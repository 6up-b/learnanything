"""§3.0's planted-persona gate on the LIVE generation path (plan item 5.3).

The audit these tests were written against: "exists but its only ship/no-ship
caller is test-only; the live `generate-diagnostics` route never touches it." So
the load-bearing tests here go through
``practice_generation.generate_diagnostic_practice_proposal`` — the function the
`learnloop generate-diagnostics` CLI calls — and assert on the *persisted* row, so
they fail if the `row_transform` wiring is removed.
"""

from __future__ import annotations

from pathlib import Path

from learnloop.codex.schemas import AuthoringProposal
from learnloop.db.repositories import Repository
from learnloop.services.persona_gate import (
    CONTRAST_PAIR_TAG_PREFIX,
    GATE_PRECISION_METRIC,
    GateDecision,
    GateTier,
    InstrumentClass,
    PersonaGate,
    PersonaGateReason,
    classify_instrument,
    gate_precision,
    tier_for,
)
from learnloop.services.practice_generation import generate_diagnostic_practice_proposal
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW_ISO, create_basic_vault


class _FakeClient:
    provider_name = "codex"
    provider_type = "test"
    model = "test-model"

    def __init__(self, proposal: AuthoringProposal):
        self._proposal = proposal
        self.contexts: list = []

    def run_authoring_proposal(self, context):
        self.contexts.append(context)
        return self._proposal


class _FiresEverything:
    """A provider whose semantic grader marks every answer wrong.

    The only way to reach ``FACET_HOLDER_FAILS``: the deterministic grader can
    never fire on the expected answer (it is compared with itself), so the
    asymmetric arm is reachable exactly through the provider seam.
    """

    def grade_diagnostic_fire(self, *, answer, expected, **_kw):  # noqa: ARG002
        return True


def _item_payload(**overrides):
    payload = {
        "id": "pi_probe_001",
        "learning_object_id": "lo_svd_definition",
        "practice_mode": "short_answer",
        "prompt": "Which of Qx / Q^T x is the coordinate vector?",
        "expected_answer": "Qx is the coordinate vector",
        "surface_family": "computation",
        "evidence_facets": ["recall"],
        "evidence_weights": {"recall": 1.0},
        "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "c1", "points": 4, "description": "correct"}],
            "fatal_errors": [],
        },
    }
    payload.update(overrides)
    return payload


def _proposal(*payloads):
    return AuthoringProposal.model_validate(
        {
            "summary": "diagnostic",
            "source_refs": [],
            "items": [
                {
                    "client_item_id": f"c_{index}",
                    "item_type": "practice_item",
                    "operation": "create",
                    "proposed_entity_id": payload["id"],
                    "rationale": "Probe the belief on a concrete instance.",
                    "review_route": "review_required",
                    "payload": payload,
                }
                for index, payload in enumerate(payloads)
            ],
        }
    )


def _keyed_rubric(misconception_id="mc_reverse_q"):
    return {
        "max_points": 4,
        "criteria": [{"id": "c1", "points": 4, "description": "correct"}],
        "fatal_errors": [
            {
                "id": "fe_reversed",
                "description": "reverses Q/Q^T",
                "misconception_id": misconception_id,
                "max_grade": 1,
            }
        ],
    }


def _setup(root: Path, *, with_facet_registry: bool = False) -> tuple[Repository, str]:
    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    if with_facet_registry:
        # A registry facet whose error signature IS the item's expected answer:
        # the belief-holder answers the item correctly, so the item is blind to a
        # misconception the registry already knows about.
        write_yaml(
            paths.facets_path,
            {
                "schema_version": 2,
                "facets": [
                    {
                        "id": "recall",
                        "claim": "Qx is the coordinate vector of x in the Q basis.",
                        "error_signatures": ["Qx is the coordinate vector"],
                        "instructional_repairs": ["contrast Q and Q^T"],
                        "status": "reviewed",
                    }
                ],
            },
        )
    repository = Repository(paths.sqlite_path)
    repository.insert_misconception(
        id="mc_reverse_q",
        learning_object_id="lo_svd_definition",
        statement="reverses Q / Q^T",
        signature="Q^T x is the coordinate vector",
        facet_ids=["recall"],
        severity=0.9,
        status="active",
    )
    need_id = repository.upsert_intervention_need(
        {
            "attempt_id": "att_diag",
            "learning_object_id": "lo_svd_definition",
            "practice_item_id": "pi_svd_define_001",
            "desired_intent": "repair",
            "trigger_reason": "severe_error_event",
            "target_facets": ["recall"],
            "error_types": [],
            "priority": 0.9,
            "status": "pending",
            "blocked_reason": "no_suitable_item",
            "candidate_requirements": {},
            "diagnostic_focus": {"misconception_ids": ["mc_reverse_q"]},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        }
    )
    return repository, need_id


# --- tiering is structural --------------------------------------------------


def test_tier_is_read_off_the_payload_not_the_route():
    """A diagnostic instrument is hard-gated with no option passed anywhere."""

    assert classify_instrument(_item_payload()) is InstrumentClass.PLAIN_PRACTICE
    assert tier_for(InstrumentClass.PLAIN_PRACTICE) is GateTier.ADVISORY
    # A discrimination CLAIM promotes the item, whichever route authored it.
    claimed = _item_payload(misconception_consistent_answer="Q^T x is the coordinate vector")
    assert classify_instrument(claimed) is InstrumentClass.MISCONCEPTION_DIAGNOSTIC
    assert tier_for(InstrumentClass.MISCONCEPTION_DIAGNOSTIC) is GateTier.HARD
    keyed = _item_payload(grading_rubric=_keyed_rubric())
    assert classify_instrument(keyed) is InstrumentClass.MISCONCEPTION_DIAGNOSTIC
    # A3/A4/A5 arms, by mode and by tag.
    assert classify_instrument(_item_payload(practice_mode="error_hunt")) is InstrumentClass.ERROR_HUNT
    assert (
        classify_instrument(_item_payload(tags=["contrast_pair"])) is InstrumentClass.CONTRAST_PAIR
    )
    assert (
        classify_instrument(_item_payload(practice_mode="discrimination_profile"))
        is InstrumentClass.DISCRIMINATION_PROFILE
    )
    for arm in (
        InstrumentClass.ERROR_HUNT,
        InstrumentClass.CONTRAST_PAIR,
        InstrumentClass.DISCRIMINATION_PROFILE,
    ):
        assert tier_for(arm) is GateTier.HARD
    # `practice_mode: diagnostic_probe` alone is NOT a discrimination claim: the
    # plan forbids throttling authoring throughput on an unvalidated simulator.
    assert (
        classify_instrument(_item_payload(practice_mode="diagnostic_probe"))
        is InstrumentClass.PLAIN_PRACTICE
    )


# --- the live path is gated -------------------------------------------------


def test_live_generate_diagnostics_blocks_an_undiscriminating_diagnostic(tmp_path):
    """THE wiring test: a paraphrase diagnostic is blocked on the live route.

    Fails outright if `PersonaGate` is unchained from
    `generate_diagnostic_practice_proposal` — the audit record disappears, the row
    stays `valid`, and the need is consumed.
    """

    root = create_basic_vault(tmp_path / "vault").root
    repository, need_id = _setup(root)
    # The regression case: the planted belief-holder answers correctly.
    client = _FakeClient(
        _proposal(
            _item_payload(
                misconception_consistent_answer="Qx is the coordinate vector",
                grading_rubric=_keyed_rubric(),
            )
        )
    )

    result = generate_diagnostic_practice_proposal(root, client)

    items = repository.proposal_items(result.patch_id)
    assert len(items) == 1
    audit = items[0]["audit"]["persona_gate"]
    assert audit["decision"] == str(GateDecision.BLOCK)
    assert audit["reason"] == str(PersonaGateReason.BELIEF_HOLDER_PASSES)
    assert audit["instrument_class"] == str(InstrumentClass.MISCONCEPTION_DIAGNOSTIC)
    assert audit["tier"] == str(GateTier.HARD)
    # A pre-B2 verdict is stamped as provisional, per §3.0.
    assert audit["persona_realism_validated"] is False
    # Blocked = un-acceptable, not merely noted.
    assert items[0]["validation_status"] == "invalid"
    assert any(error.startswith("persona_gate:") for error in items[0]["validation_errors"])
    # The need is NOT consumed by an instrument that cannot discriminate.
    assert result.fulfilled_need_ids == []
    need = repository.intervention_need(need_id)
    assert need["status"] == "pending"
    assert need["blocked_reason"].startswith(f"diagnostic_proposal_rejected:{result.patch_id}")
    assert result.persona_gate["decisions"][str(GateDecision.BLOCK)] == 1
    assert result.persona_gate_violations


def test_live_generate_diagnostics_ships_a_discriminating_diagnostic(tmp_path):
    """The positive control: the gate is not simply blocking everything."""

    root = create_basic_vault(tmp_path / "vault").root
    repository, need_id = _setup(root)
    client = _FakeClient(
        _proposal(
            _item_payload(
                misconception_consistent_answer="Q^T x is the coordinate vector",
                grading_rubric=_keyed_rubric(),
            )
        )
    )

    result = generate_diagnostic_practice_proposal(root, client)

    items = repository.proposal_items(result.patch_id)
    audit = items[0]["audit"]["persona_gate"]
    assert audit["decision"] == str(GateDecision.PASS)
    assert audit["reason"] == str(PersonaGateReason.PERSONAS_SEPARATE)
    assert items[0]["validation_status"] != "invalid"
    assert result.fulfilled_need_ids == [need_id]
    assert repository.intervention_need(need_id)["status"] == "fulfilled"


def test_live_plain_practice_item_is_flagged_but_shipped(tmp_path):
    """Advisory tier on the same live route: flagged, never blocked (plan §7.3)."""

    root = create_basic_vault(tmp_path / "vault").root
    repository, need_id = _setup(root, with_facet_registry=True)
    # No discrimination claim -> plain practice; the target facet's registry error
    # signature equals this item's expected answer, so the personas cannot separate.
    client = _FakeClient(_proposal(_item_payload()))

    result = generate_diagnostic_practice_proposal(root, client)

    items = repository.proposal_items(result.patch_id)
    audit = items[0]["audit"]["persona_gate"]
    assert audit["decision"] == str(GateDecision.FLAG_FOR_REVIEW)
    assert audit["reason"] == str(PersonaGateReason.BELIEF_HOLDER_PASSES)
    assert audit["tier"] == str(GateTier.ADVISORY)
    # Shipped: reviewable, not invalid, and it still closes its need.
    assert items[0]["validation_status"] == "warning"
    assert any(
        error.startswith("persona_gate_review:") for error in items[0]["validation_errors"]
    )
    assert result.fulfilled_need_ids == [need_id]
    assert result.persona_gate_warnings and not result.persona_gate_violations


def test_b2_license_promotes_plain_practice_advisory_failure_to_hard(tmp_path):
    root = create_basic_vault(tmp_path / "vault").root
    repository, need_id = _setup(root, with_facet_registry=True)
    repository.insert_persona_realism_run(
        {
            "matcher_version": "test",
            "corpus_hash": "b" * 64,
            "persona_source": "authored_signature",
            "persona_count": 8,
            "real_count": 8,
            "folds": 16,
            "matcher_correct": 8,
            "matcher_total": 16,
            "balanced_accuracy": 0.5,
            "separation_threshold": 0.7,
            "verdict": "indistinguishable",
            "feature_manifest": {},
        }
    )

    result = generate_diagnostic_practice_proposal(
        root, _FakeClient(_proposal(_item_payload()))
    )

    item = repository.proposal_items(result.patch_id)[0]
    audit = item["audit"]["persona_gate"]
    assert audit["persona_realism_validated"] is True
    assert audit["tier"] == str(GateTier.HARD)
    assert audit["decision"] == str(GateDecision.BLOCK)
    assert item["validation_status"] == "invalid"
    assert repository.intervention_need(need_id)["status"] == "pending"


def test_live_route_abstains_when_there_is_nothing_to_plant(tmp_path):
    """No persona material -> UNTESTED, recorded, and no route change.

    The legacy vault has no facet registry, so a plain item's targets carry no
    ``error_signatures``. Flagging every such item would make the flag meaningless
    and would throttle exactly the throughput the plan protects.
    """

    root = create_basic_vault(tmp_path / "vault").root
    repository, need_id = _setup(root)
    client = _FakeClient(_proposal(_item_payload()))

    result = generate_diagnostic_practice_proposal(root, client)

    items = repository.proposal_items(result.patch_id)
    audit = items[0]["audit"]["persona_gate"]
    assert audit["decision"] == str(GateDecision.UNTESTED)
    assert audit["reason"] == str(PersonaGateReason.INSUFFICIENT_PERSONA_PAYLOAD)
    assert items[0]["validation_status"] != "invalid"
    assert result.fulfilled_need_ids == [need_id]


# --- every typed reason is reachable ---------------------------------------


def _gate(root: Path, *, grading_client=None) -> PersonaGate:
    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    return PersonaGate(vault, repository, grading_client=grading_client)


def _row(payload, client_item_id="c_0"):
    return {
        "client_item_id": client_item_id,
        "item_type": "practice_item",
        "operation": "create",
        "payload": payload,
        "audit": None,
        "validation_status": "valid",
        "validation_errors": [],
        "_auto_apply": True,
    }


def test_reason_no_keyed_detector(tmp_path):
    """A diagnostic must ATTRIBUTE a failure, not merely mark it wrong."""

    root = create_basic_vault(tmp_path / "vault").root
    gate = _gate(root)
    rows = [_row(_item_payload(misconception_consistent_answer="Q^T x is the vector"))]

    gate(rows)

    assert gate.outcomes[0].reason is PersonaGateReason.NO_KEYED_DETECTOR
    assert gate.outcomes[0].decision is GateDecision.BLOCK
    assert rows[0]["validation_status"] == "invalid"


def test_reason_facet_holder_fails_via_semantic_grader(tmp_path):
    root = create_basic_vault(tmp_path / "vault").root
    gate = _gate(root, grading_client=_FiresEverything())
    rows = [
        _row(
            _item_payload(
                misconception_consistent_answer="Q^T x is the coordinate vector",
                grading_rubric=_keyed_rubric(),
            )
        )
    ]

    gate(rows)

    assert gate.outcomes[0].reason is PersonaGateReason.FACET_HOLDER_FAILS
    assert gate.outcomes[0].decision is GateDecision.BLOCK


def test_reason_not_an_instrument_abstains(tmp_path):
    """Nothing a persona could answer: abstain, do not blame the personas."""

    root = create_basic_vault(tmp_path / "vault").root
    gate = _gate(root)
    rows = [
        _row(_item_payload(prompt="", expected_answer="")),
        # A row that is not a created practice item never reaches classification.
        {**_row(_item_payload(), client_item_id="c_concept"), "item_type": "concept"},
    ]

    gate(rows)

    assert len(gate.outcomes) == 1
    assert gate.outcomes[0].instrument_class is InstrumentClass.NOT_AN_INSTRUMENT
    assert gate.outcomes[0].tier is GateTier.NONE
    assert gate.outcomes[0].decision is GateDecision.UNTESTED
    assert gate.outcomes[0].reason is PersonaGateReason.NOT_AN_INSTRUMENT
    assert rows[0]["validation_status"] == "valid"  # abstention changes no route
    assert rows[1]["audit"] is None


def test_reason_insufficient_persona_payload_blocks_an_unplantable_error_hunt(tmp_path):
    """A3: 'a freehand error is an untyped instrument.'"""

    root = create_basic_vault(tmp_path / "vault").root
    gate = _gate(root)
    rows = [_row(_item_payload(practice_mode="error_hunt"))]

    gate(rows)

    assert gate.outcomes[0].reason is PersonaGateReason.INSUFFICIENT_PERSONA_PAYLOAD
    assert gate.outcomes[0].decision is GateDecision.BLOCK


def _pair_rows(*, expected_a, expected_b, belief):
    tag = f"{CONTRAST_PAIR_TAG_PREFIX}qqt"
    return [
        _row(
            _item_payload(
                id="pi_pair_a",
                tags=[tag],
                expected_answer=expected_a,
                misconception_consistent_answer=belief,
                grading_rubric=_keyed_rubric(),
            ),
            client_item_id="c_a",
        ),
        _row(
            _item_payload(
                id="pi_pair_b", tags=[tag], expected_answer=expected_b, grading_rubric=_keyed_rubric()
            ),
            client_item_id="c_b",
        ),
    ]


def test_contrast_pair_must_fail_exactly_one_member(tmp_path):
    """§3.0's A4 clause, in all three arms."""

    root = create_basic_vault(tmp_path / "vault").root

    separates = _pair_rows(
        expected_a="Qx is the coordinate vector",
        expected_b="Q^T x is the coordinate vector",
        belief="Q^T x is the coordinate vector",
    )
    gate = _gate(root)
    gate(separates)
    assert {o.reason for o in gate.outcomes} == {PersonaGateReason.CONTRAST_PAIR_SEPARATES}
    assert {o.decision for o in gate.outcomes} == {GateDecision.PASS}

    # "Fails both" is only a VERDICT when a semantic oracle judged it. The
    # deterministic fallback compares one authored signature against each
    # member's expected answer, and a signature written as what a believer would
    # actually produce differs from both — so without an oracle this arm would
    # block every honestly-authored pair, enforcing "the signature is a verbatim
    # copy of one expected answer" rather than anything about the instrument.
    both = _pair_rows(
        expected_a="Qx is the coordinate vector",
        expected_b="Qx is also the coordinate vector",
        belief="Q^T x is the coordinate vector",
    )

    class _SemanticOracle:
        """Judges every member as failed — the real 'fails both' case."""

        @staticmethod
        def grade_diagnostic_fire(**_kwargs) -> bool:
            return True

    gate = _gate(root, grading_client=_SemanticOracle())
    gate(both)
    assert {o.reason for o in gate.outcomes} == {PersonaGateReason.CONTRAST_PAIR_FAILS_BOTH}
    assert {o.decision for o in gate.outcomes} == {GateDecision.BLOCK}

    # Same pair, no oracle: an abstention that ships to review, not a block.
    gate = _gate(root)
    gate(both)
    assert {o.reason for o in gate.outcomes} == {PersonaGateReason.CONTRAST_PAIR_UNJUDGED}
    assert {o.decision for o in gate.outcomes} == {GateDecision.FLAG_FOR_REVIEW}

    neither = _pair_rows(
        expected_a="Q^T x is the coordinate vector",
        expected_b="Q^T x is the coordinate vector",
        belief="Q^T x is the coordinate vector",
    )
    gate = _gate(root)
    gate(neither)
    assert {o.reason for o in gate.outcomes} == {PersonaGateReason.CONTRAST_PAIR_FAILS_NEITHER}
    assert {o.decision for o in gate.outcomes} == {GateDecision.BLOCK}


def test_every_typed_reason_is_reachable_is_asserted_by_this_module():
    """Guard: a new reason arm must arrive with a test that reaches it.

    Split across two modules since Meas §3.A3 landed (plan item 6.4). The A3 arms
    invert the question this gate normally asks — a belief-holder passes an error
    hunt by *not* seeing the plant — so their coverage lives beside the rest of
    A3 in ``tests/test_error_hunt_items``, and the guard names them here rather
    than losing the completeness check.
    """

    covered = {
        PersonaGateReason.PERSONAS_SEPARATE,
        PersonaGateReason.CONTRAST_PAIR_SEPARATES,
        PersonaGateReason.BELIEF_HOLDER_PASSES,
        PersonaGateReason.FACET_HOLDER_FAILS,
        PersonaGateReason.CONTRAST_PAIR_FAILS_BOTH,
        PersonaGateReason.CONTRAST_PAIR_UNJUDGED,
        PersonaGateReason.CONTRAST_PAIR_FAILS_NEITHER,
        PersonaGateReason.NO_KEYED_DETECTOR,
        PersonaGateReason.INSUFFICIENT_PERSONA_PAYLOAD,
        PersonaGateReason.NOT_AN_INSTRUMENT,
        PersonaGateReason.PERSONA_REALISM_SEPARABLE,
    }
    #: Reached in `tests/test_error_hunt_items.py`, one test per arm.
    covered_by_error_hunt_tests = {
        PersonaGateReason.ERROR_HUNT_PLANTS_INVISIBLE,
        PersonaGateReason.ERROR_HUNT_CLEAN_CONTROL,
        PersonaGateReason.ERROR_HUNT_PLANT_VISIBLE_TO_BELIEF_HOLDER,
        PersonaGateReason.ERROR_HUNT_PLANT_NOT_FROM_REGISTRY,
        PersonaGateReason.ERROR_HUNT_NO_REPAIR_REQUIRED,
        PersonaGateReason.ERROR_HUNT_DECLARES_ERROR_COUNT,
        PersonaGateReason.ERROR_HUNT_PLANT_MATCHES_REPAIR,
    }
    assert covered | covered_by_error_hunt_tests == set(PersonaGateReason)


def test_b2_separable_corpus_invalidates_an_otherwise_passing_hard_gate(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    repository.insert_persona_realism_run(
        {
            "matcher_version": "test",
            "corpus_hash": "a" * 64,
            "persona_source": "authored_signature",
            "generator_family": "test:generator",
            "persona_count": 8,
            "real_count": 8,
            "folds": 16,
            "matcher_correct": 16,
            "matcher_total": 16,
            "balanced_accuracy": 1.0,
            "separation_threshold": 0.7,
            "verdict": "separable",
            "feature_manifest": {},
        }
    )
    payload = _item_payload(
        misconception_consistent_answer="V transpose is unnecessary",
        grading_rubric={
            "max_points": 4,
            "criteria": [{"id": "c1", "points": 4, "description": "correct"}],
            "fatal_errors": [
                {
                    "id": "fatal_vt",
                    "description": "omits V transpose",
                    "max_grade": 1,
                    "misconception_id": "mc_vt",
                }
            ],
        },
    )
    row = {
        "client_item_id": "candidate",
        "item_type": "practice_item",
        "operation": "create",
        "validation_status": "valid",
        "payload": payload,
    }
    gate = PersonaGate(vault, repository)
    gate([row])

    assert gate.outcomes[0].decision is GateDecision.BLOCK
    assert (
        gate.outcomes[0].reason
        is PersonaGateReason.PERSONA_REALISM_SEPARABLE
    )
    assert row["audit"]["persona_gate"]["persona_realism_validated"] is False


# --- gate precision --------------------------------------------------------


def test_gate_precision_reports_no_data_before_any_prediction(tmp_path):
    root = create_basic_vault(tmp_path / "vault").root
    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)

    metric = gate_precision(repository)

    assert metric.name == GATE_PRECISION_METRIC
    assert metric.availability == "no_data"
    # The whole point: a rate over zero gated items is never 0.0 and never 1.0.
    assert metric.value is None
    assert metric.denominator == 0


def test_gate_precision_reports_no_producer_without_blinded_ground_truth(tmp_path):
    root = create_basic_vault(tmp_path / "vault").root
    repository, _need_id = _setup(root)
    client = _FakeClient(
        _proposal(
            _item_payload(
                misconception_consistent_answer="Qx is the coordinate vector",
                grading_rubric=_keyed_rubric(),
            )
        )
    )
    generate_diagnostic_practice_proposal(root, client)

    metric = gate_precision(repository)

    # A real prediction exists and is counted, but "genuinely bad" needs a blinded
    # label (B2's matcher / B1's planted side); reviewer decisions are confounded.
    assert metric.availability == "no_producer"
    assert metric.value is None
    assert metric.denominator == 1
    assert metric.detail["decisions"][str(GateDecision.BLOCK)] == 1
    assert metric.detail["reasons"][str(PersonaGateReason.BELIEF_HOLDER_PASSES)] == 1
    # Reviewer decisions are captured from day one, descriptively only.
    assert metric.detail["reviewer_decisions"] == {"pending": 1}
    assert metric.detail["label_source"] is None


def test_gate_precision_becomes_available_once_labels_are_supplied(tmp_path):
    root = create_basic_vault(tmp_path / "vault").root
    repository, _need_id = _setup(root)
    client = _FakeClient(
        _proposal(
            _item_payload(
                misconception_consistent_answer="Qx is the coordinate vector",
                grading_rubric=_keyed_rubric(),
            )
        )
    )
    result = generate_diagnostic_practice_proposal(root, client)
    item_id = repository.proposal_items(result.patch_id)[0]["id"]

    metric = gate_precision(repository, blinded_labels={item_id: True})

    assert metric.availability == "available"
    assert metric.value == 1.0
    assert metric.numerator == 1.0 and metric.denominator == 1.0
    assert metric.detail["label_source"] == "blinded_labels"
