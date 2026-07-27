"""Meas §3.A3 error-hunt items (implementation plan item 6.4).

The two §10 lines these tests exist for:

    An error-hunt item whose planted error is found by the misconception-persona
    is rejected.

    A clean-solution error-hunt on which the learner reports an error writes a
    misconception candidate, not a facet failure.

The first is §3.A3's non-triviality criterion and it inverts the ordinary §3.0
question: on an error hunt a belief-holder FAILS by not seeing the plant, so the
gate has to test invisibility rather than divergence. The second is the rotation
that makes the instrument worth having — "a learner who 'finds' an error in a
correct solution has just handed you a misconception directly" — and it is the
one place in the codebase where a wrong answer must NOT become negative facet
evidence.
"""

from __future__ import annotations

import json

import pytest

from learnloop.clock import FrozenClock
from learnloop.codex.schemas import (
    CriterionEvidence,
    ErrorAttribution,
    ErrorHuntReport,
    GradingProposal,
    ReportedError,
)
from learnloop.db.repositories import Repository
from learnloop.services.attempts import AttemptDraft, complete_codex_graded_attempt
from learnloop.services.error_hunt import (
    AGREEMENT_FLOOR,
    MIN_PAIRED_FACETS,
    PROOFREADING_SIGNAL_METRIC,
    PlantOutcome,
    error_hunt_outcome_summary,
    proofreading_signal,
    validate_error_hunt_report,
)
from learnloop.services.persona_gate import (
    GateDecision,
    GateTier,
    InstrumentClass,
    PersonaGate,
    PersonaGateReason,
    classify_instrument,
    declares_error_count,
)
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault, set_algorithm_version, write_facets

CLOCK = FrozenClock(NOW)
ITEM = "pi_hunt_001"
FACET = "f_chain_rule"
MISCONCEPTION = "mc_forgets_inner_derivative"
BELIEF_SIGNATURE = "d/dx sin(3x) = cos(3x)"
CORRECT_STEP = "d/dx sin(3x) = 3 cos(3x)"

FACETS = [
    {
        "id": FACET,
        "kind": "procedure_contract",
        "claim": "Differentiating a composite multiplies by the inner derivative.",
        "error_signatures": [BELIEF_SIGNATURE],
        "instructional_repairs": ["work the chain rule outward-in"],
    }
]


def _plant(**overrides) -> dict:
    payload = {
        "id": "pe_inner",
        "step_ref": "step 2",
        "source": "misconception_registry",
        "error_signature": BELIEF_SIGNATURE,
        "required_repair": CORRECT_STEP,
        "misconception_id": MISCONCEPTION,
        "facet_id": FACET,
    }
    payload.update(overrides)
    return payload


def _hunt_payload(*, plants=None, prompt="Correct the worked solution below.", **overrides) -> dict:
    payload = {
        "id": ITEM,
        "learning_object_id": "lo_svd_definition",
        "practice_mode": "constructed_response",
        "prompt": prompt,
        "expected_answer": "The corrected derivation.",
        "surface_family": "worked_repair",
        "evidence_facets": [FACET],
        "evidence_weights": {FACET: 1.0},
        "error_hunt": {
            "worked_solution_md": f"step 1: let u = 3x\nstep 2: {BELIEF_SIGNATURE}\nstep 3: done",
            "planted_errors": [_plant()] if plants is None else plants,
        },
        "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "c1", "points": 4, "description": "repairs the solution"}],
            "fatal_errors": [],
        },
    }
    payload.update(overrides)
    return payload


def _row(payload, client_item_id="c_0") -> dict:
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


def _registry(repository) -> None:
    repository.insert_misconception(
        id=MISCONCEPTION,
        learning_object_id="lo_svd_definition",
        statement="forgets the inner derivative in the chain rule",
        signature=BELIEF_SIGNATURE,
        facet_ids=[FACET],
        severity=0.8,
        status="active",
    )


def _vault(tmp_path, *, plants=None, prompt="Correct the worked solution below."):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    write_facets(paths, FACETS)
    write_yaml(
        paths.practice_item_path("linear-algebra", ITEM),
        {
            "schema_version": 1,
            **_hunt_payload(plants=plants, prompt=prompt),
            "attempt_types_allowed": ["independent_attempt"],
            "capability": "procedure_execution",
            "difficulty": 0.5,
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    _registry(repository)
    sync_vault_state(vault, repository, clock=CLOCK)
    return paths, vault, repository


def _gate(tmp_path) -> tuple[PersonaGate, Repository]:
    paths = create_basic_vault(tmp_path / "vault")
    write_facets(paths, FACETS)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    _registry(repository)
    return PersonaGate(vault, repository), repository


# ---------------------------------------------------------------------------
# The §3.0 gate, inverted for A3
# ---------------------------------------------------------------------------


def test_carrying_an_error_hunt_contract_is_what_makes_it_an_error_hunt():
    assert classify_instrument(_hunt_payload()) is InstrumentClass.ERROR_HUNT
    assert classify_instrument(_hunt_payload(error_hunt=None)) is InstrumentClass.PLAIN_PRACTICE


def test_a_plant_invisible_to_the_belief_holder_passes(tmp_path):
    """The positive control: the plant IS what the belief-holder would write."""

    gate, _repo = _gate(tmp_path)
    rows = [_row(_hunt_payload())]

    gate(rows)

    outcome = gate.outcomes[0]
    assert outcome.instrument_class is InstrumentClass.ERROR_HUNT
    assert outcome.tier is GateTier.HARD
    assert outcome.decision is GateDecision.PASS
    assert outcome.reason is PersonaGateReason.ERROR_HUNT_PLANTS_INVISIBLE
    assert rows[0]["validation_status"] == "valid"


def test_a_plant_the_belief_holder_would_catch_is_rejected(tmp_path):
    """§10's line. The item measures carefulness, which is not a facet anyone wants.

    The plant is a DIFFERENT wrong step from the one this belief produces, so a
    holder of the belief reads it and sees an error — exactly the proofreading
    exercise §3.A3's revert criterion exists to detect, caught here at authoring
    time instead of after twenty attempts.
    """

    gate, _repo = _gate(tmp_path)
    visible = _plant(error_signature="d/dx sin(3x) = 3 sin(3x)")
    rows = [_row(_hunt_payload(plants=[visible]))]

    gate(rows)

    outcome = gate.outcomes[0]
    assert outcome.decision is GateDecision.BLOCK
    assert outcome.reason is PersonaGateReason.ERROR_HUNT_PLANT_VISIBLE_TO_BELIEF_HOLDER
    assert rows[0]["validation_status"] == "invalid"


def test_a_plant_the_registry_cannot_corroborate_is_rejected(tmp_path):
    """"Plant from the registry, never freehand ... a freehand error is an
    untyped instrument."

    The plant declares a registry source, but neither the named misconception nor
    any facet error signature in this vault contains its text — so there is no
    belief-holder to test invisibility against, and the plant is untyped whatever
    its `source` field says.
    """

    gate, _repo = _gate(tmp_path)
    freehand = _plant(
        misconception_id="mc_invented",
        facet_id=None,
        error_signature="d/dx sin(3x) = sin(3x)",
    )
    rows = [_row(_hunt_payload(plants=[freehand]))]

    gate(rows)

    assert gate.outcomes[0].decision is GateDecision.BLOCK
    assert gate.outcomes[0].reason is PersonaGateReason.ERROR_HUNT_PLANT_NOT_FROM_REGISTRY


def test_a_facet_error_signature_corroborates_a_plant_with_no_registry_belief(tmp_path):
    """The second admissible provenance: the ingest-emitted `error_signatures`.

    §3.0/D2's "one mechanism, three uses" — the field the mint gate and the
    persona gate already plant from is enough on its own, so an error hunt does
    not require a promoted misconception to exist first.
    """

    gate, _repo = _gate(tmp_path)
    rows = [
        _row(
            _hunt_payload(
                plants=[_plant(source="facet_error_signature", misconception_id=None)]
            )
        )
    ]

    gate(rows)

    assert gate.outcomes[0].decision is GateDecision.PASS
    assert gate.outcomes[0].reason is PersonaGateReason.ERROR_HUNT_PLANTS_INVISIBLE


def test_a_plant_with_no_required_repair_is_rejected(tmp_path):
    """"Flagging is recognition; repairing is construction." §11 forbids the first."""

    gate, _repo = _gate(tmp_path)
    rows = [_row(_hunt_payload(plants=[_plant(required_repair="  ")]))]

    gate(rows)

    assert gate.outcomes[0].decision is GateDecision.BLOCK
    assert gate.outcomes[0].reason is PersonaGateReason.ERROR_HUNT_NO_REPAIR_REQUIRED


def test_a_plant_identical_to_its_own_repair_is_rejected(tmp_path):
    """Nothing was planted. Distinct from visibility: the remedy is different."""

    gate, _repo = _gate(tmp_path)
    rows = [_row(_hunt_payload(plants=[_plant(required_repair=BELIEF_SIGNATURE)]))]

    gate(rows)

    assert gate.outcomes[0].decision is GateDecision.BLOCK
    assert gate.outcomes[0].reason is PersonaGateReason.ERROR_HUNT_PLANT_MATCHES_REPAIR


def test_a_prompt_that_states_the_error_count_is_rejected(tmp_path):
    """"A prompt saying 'find the 2 errors' is a scavenger hunt.\""""

    assert declares_error_count("Find the 2 errors below.")
    assert declares_error_count("There are three mistakes in this derivation.")
    assert declares_error_count("Exactly one step is wrong.")
    # The rule is about the COUNT, not about plurality.
    assert not declares_error_count("Correct whatever is wrong with the work below.")

    gate, _repo = _gate(tmp_path)
    rows = [_row(_hunt_payload(prompt="Find the 2 errors in the solution below."))]

    gate(rows)

    assert gate.outcomes[0].decision is GateDecision.BLOCK
    assert gate.outcomes[0].reason is PersonaGateReason.ERROR_HUNT_DECLARES_ERROR_COUNT


def test_the_clean_rotation_passes_with_its_own_typed_reason(tmp_path):
    """An item that plants nothing is SUPPOSED to discriminate nothing.

    Blocking it would remove the rotation that kills the "there is always an
    error" strategy, so the clean control gets a typed pass rather than falling
    through to the unplantable-instrument block.
    """

    gate, _repo = _gate(tmp_path)
    rows = [_row(_hunt_payload(plants=[]))]

    gate(rows)

    assert gate.outcomes[0].decision is GateDecision.PASS
    assert gate.outcomes[0].reason is PersonaGateReason.ERROR_HUNT_CLEAN_CONTROL
    assert rows[0]["validation_status"] == "valid"


# ---------------------------------------------------------------------------
# Grading: repaired, found-but-not-repaired, missed
# ---------------------------------------------------------------------------


def _report(*reports) -> ErrorHuntReport:
    return ErrorHuntReport(reported_errors=list(reports))


def _proposal(report, **overrides) -> GradingProposal:
    payload = {
        "attempt_id": "att_hunt",
        "practice_item_id": ITEM,
        "rubric_score": 2,
        "criterion_evidence": [
            CriterionEvidence(criterion_id="c1", points_awarded=2, evidence="partial")
        ],
        "grader_confidence": 0.9,
        "error_hunt_report": report,
    }
    payload.update(overrides)
    return GradingProposal(**payload)


def test_the_repair_is_required_not_the_flag(tmp_path):
    """Three arms, and the middle one is the whole point of having three."""

    _paths, vault, _repo = _vault(tmp_path)
    item = vault.practice_items[ITEM]

    repaired = validate_error_hunt_report(
        item,
        _proposal(
            _report(
                ReportedError(
                    location="step 2",
                    claim_md="the inner derivative is missing",
                    repair_md=CORRECT_STEP,
                )
            )
        ),
    )
    assert repaired.plants[0].outcome is PlantOutcome.REPAIRED

    flagged = validate_error_hunt_report(
        item,
        _proposal(
            _report(
                ReportedError(location="step 2", claim_md="something is wrong here", repair_md="")
            )
        ),
    )
    assert flagged.plants[0].outcome is PlantOutcome.FOUND_NOT_REPAIRED

    missed = validate_error_hunt_report(item, _proposal(_report()))
    assert missed.plants[0].outcome is PlantOutcome.MISSED
    assert missed.false_positives == ()


def test_a_wrong_repair_is_not_credited_as_a_repair(tmp_path):
    """Locating the error without correcting it is the recognition half."""

    _paths, vault, _repo = _vault(tmp_path)
    item = vault.practice_items[ITEM]

    resolved = validate_error_hunt_report(
        item,
        _proposal(
            _report(
                ReportedError(
                    location="step 2",
                    claim_md="wrong",
                    repair_md="d/dx sin(3x) = 3 sin(3x)",
                )
            )
        ),
    )

    assert resolved.plants[0].outcome is PlantOutcome.FOUND_NOT_REPAIRED


def test_an_item_that_is_not_an_error_hunt_produces_no_outcome(tmp_path):
    """`None`, not an empty result: an empty one would write a row per attempt."""

    _paths, vault, _repo = _vault(tmp_path)

    assert validate_error_hunt_report(
        vault.practice_items["pi_svd_define_001"], _proposal(_report())
    ) is None


# ---------------------------------------------------------------------------
# §10: the clean-solution false positive
# ---------------------------------------------------------------------------


def _graded(vault, repository, attempt_id: str, *, report, attributions=()):
    return complete_codex_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=ITEM,
            learner_answer_md="Step 2 looks wrong to me; it should be cos(3x).",
            attempt_type="independent_attempt",
        ),
        GradingProposal(
            attempt_id=attempt_id,
            practice_item_id=ITEM,
            rubric_score=1,
            # The prose-first contract still applies: a named facet must be
            # anchored in `diagnosis_md` (causal §5.1), error hunt or not.
            diagnosis_md=(
                f"The learner disputed a step the chain rule ({FACET}) makes correct."
            ),
            criterion_evidence=[
                CriterionEvidence(criterion_id="c1", points_awarded=1, evidence="reported a non-error")
            ],
            error_attributions=list(attributions),
            grader_confidence=0.9,
            error_hunt_report=report,
        ),
        agent_run_id=None,
        clock=CLOCK,
    )


def test_clean_solution_false_positive_writes_a_candidate_not_a_facet_failure(tmp_path):
    """§10's line, end to end, in both halves.

    The learner is shown CORRECT work and says step 2 is wrong. The grader does
    what it always does — attributes the failure to the item's facet. What must
    come out the other side is a misconception CANDIDATE and no facet negative:
    the learner was reading, not deriving, so nothing was observed about their
    ability to do the work, while their disagreement with correct work says
    exactly what they believe.
    """

    _paths, vault, repository = _vault(tmp_path, plants=[])

    _graded(
        vault,
        repository,
        "att_clean_fp",
        report=_report(
            ReportedError(
                location="step 2",
                claim_md="the derivative of sin(3x) should be cos(3x)",
                repair_md="d/dx sin(3x) = cos(3x)",
            )
        ),
        attributions=[
            ErrorAttribution(
                error_type="conceptual_slip",
                severity=0.6,
                evidence="disputes a correct step",
                target_evidence_families=[FACET],
            )
        ],
    )

    outcome = repository.error_hunt_outcome("att_clean_fp")
    assert outcome is not None
    assert outcome["clean_solution"] == 1
    assert outcome["false_positive_reports"] == 1
    # Half one: a candidate was minted, in the EXISTING store the review and
    # promotion machinery already reads.
    candidate_id = outcome["misconception_candidate_id"]
    assert candidate_id
    candidate = repository.misconception_candidate_by_id(candidate_id)
    assert candidate["learning_object_id"] == "lo_svd_definition"
    assert "believes correct work is wrong" in candidate["statement"]
    assert candidate["mechanism"] == "clean_solution_false_positive"
    # Half two: no facet took a negative, and the suppression is recorded rather
    # than merely true.
    assert outcome["facet_failure_suppressed"] == 1
    debug = repository.attempt_debug_payload("att_clean_fp") or {}
    kinds = {event["kind"] for event in (debug.get("causal_attribution") or {}).get("firewall_events", [])}
    assert "clean_solution_false_positive_facet_write_blocked" in kinds

    # Half three, and the one that actually holds §10's line: the LEDGER. An
    # emptied target list is indistinguishable from a list the grader never
    # filled, so without a typed block reason on the observation the projection's
    # single-target fallback attributes the whole failure to the criterion's own
    # target — and the facet failure this guard exists to prevent gets banked
    # anyway. Asserting only the attribution channel above missed exactly that.
    evidence = repository.fetch_grading_evidence("att_clean_fp")
    assert evidence, "the attempt must carry grading evidence to test the stamp"
    blocked = {
        json.loads(row.attribution_json or "{}").get("negative_evidence_blocked")
        for row in evidence
    }
    assert blocked == {"clean_solution_false_positive"}

    from learnloop.services.canonical_projection import project_canonical_facet_state

    project_canonical_facet_state(vault, repository, clock=CLOCK)
    for cell in repository.facet_capability_evidence_all():
        assert cell.direct_negative_mass == pytest.approx(0.0), (
            f"{cell.facet_id}@{cell.capability} took negative mass from a "
            "clean-solution false positive"
        )
        assert cell.embedded_negative_mass == pytest.approx(0.0)


def test_a_seeded_error_hunt_still_writes_ordinary_facet_evidence(tmp_path):
    """The suppression is narrow. A miss on a SEEDED hunt localizes to the plant's
    own facet, which is real evidence and the instrument's entire cost argument."""

    _paths, vault, repository = _vault(tmp_path)

    _graded(
        vault,
        repository,
        "att_seeded",
        report=_report(),
        attributions=[
            ErrorAttribution(
                error_type="conceptual_slip",
                severity=0.6,
                evidence="did not find the planted error",
                target_evidence_families=[FACET],
            )
        ],
    )

    outcome = repository.error_hunt_outcome("att_seeded")
    assert outcome["clean_solution"] == 0
    assert outcome["planted_missed"] == 1
    assert outcome["misconception_candidate_id"] is None
    assert outcome["facet_failure_suppressed"] == 0


def test_a_clean_solution_the_learner_leaves_alone_mints_nothing(tmp_path):
    """The other clean arm: agreeing with correct work is not a misconception."""

    _paths, vault, repository = _vault(tmp_path, plants=[])

    _graded(vault, repository, "att_clean_ok", report=_report())

    outcome = repository.error_hunt_outcome("att_clean_ok")
    assert outcome["false_positive_reports"] == 0
    assert outcome["misconception_candidate_id"] is None
    assert outcome["facet_failure_suppressed"] == 0


def test_a_repeated_false_positive_increments_the_same_candidate(tmp_path):
    """One belief, not one per report. The normalization key is what merges them."""

    _paths, vault, repository = _vault(tmp_path, plants=[])
    report = _report(
        ReportedError(location="step 2", claim_md="should be cos(3x)", repair_md="cos(3x)")
    )

    _graded(vault, vault and repository, "att_fp_1", report=report)
    _graded(vault, repository, "att_fp_2", report=report)

    first = repository.error_hunt_outcome("att_fp_1")["misconception_candidate_id"]
    second = repository.error_hunt_outcome("att_fp_2")["misconception_candidate_id"]
    assert first == second
    assert repository.misconception_candidate_by_id(first)["occurrence_count"] == 2


def test_repeats_on_one_solution_stay_one_observation_and_do_not_promote(tmp_path):
    """Occurrence count is not independence.

    The candidate's count rises on every repeat, but three false positives on
    the SAME worked solution are one observation — the item resolves to one
    `surface_group_id`. §5.6 arm (b) needs a fingerprint-DISTINCT group, so
    nothing durable may be minted here however many times it recurs.
    """

    _paths, vault, repository = _vault(tmp_path, plants=[])
    report = _report(
        ReportedError(location="step 2", claim_md="should be cos(3x)", repair_md="cos(3x)")
    )

    _graded(vault, repository, "att_same_1", report=report)
    _graded(vault, repository, "att_same_2", report=report)
    _graded(vault, repository, "att_same_3", report=report)

    candidate_id = repository.error_hunt_outcome("att_same_3")["misconception_candidate_id"]
    candidate = repository.misconception_candidate_by_id(candidate_id)
    assert candidate["occurrence_count"] == 3
    assert candidate["status"] == "candidate"
    assert candidate["promoted_misconception_id"] is None


def test_the_outcome_store_is_append_only(tmp_path):
    _paths, vault, repository = _vault(tmp_path, plants=[])
    _graded(vault, repository, "att_immutable", report=_report())

    with pytest.raises(Exception):
        with repository.connection() as connection:
            connection.execute("UPDATE error_hunt_outcomes SET planted_missed = 9")


# ---------------------------------------------------------------------------
# The revert criterion
# ---------------------------------------------------------------------------


def test_proofreading_signal_abstains_without_both_populations(tmp_path):
    """"Error-hunt outcomes uncorrelated with the same learner's
    constructed-response outcomes on the same facet" needs both populations."""

    _paths, vault, repository = _vault(tmp_path)

    metric = proofreading_signal(vault, repository)

    assert metric.name == PROOFREADING_SIGNAL_METRIC
    assert metric.availability == "no_data"
    assert metric.value is None
    assert metric.detail["verdict"] == "insufficient_paired_facets"
    assert metric.detail["min_paired_facets"] == MIN_PAIRED_FACETS
    assert metric.detail["error_hunt_items"] == 1


def test_outcome_summary_reports_the_clean_rotation_share(tmp_path):
    """The one number an author can act on: the rotation stopping is invisible
    otherwise, and "there is always an error" starts working again."""

    _paths, vault, repository = _vault(tmp_path, plants=[])
    _graded(vault, repository, "att_summary", report=_report())

    summary = error_hunt_outcome_summary(repository)

    assert summary["attempts"] == 1
    assert summary["clean_solution_attempts"] == 1
    assert summary["clean_rotation_share"] == 1.0
    assert AGREEMENT_FLOOR == 0.5


# ---------------------------------------------------------------------------
# The doctor: the same rules, checked on what actually shipped
# ---------------------------------------------------------------------------


def test_the_doctor_catches_a_hand_authored_error_hunt_the_gates_never_saw(tmp_path):
    """The gates run on generated proposals; a hand-edited YAML item skips both.

    So the doctor asserts the same three structural rules against the vault —
    a plant with no repair, a plant identical to its repair, and a plant the
    vault cannot source.
    """

    from learnloop.services.doctor import _check_blueprints_and_criteria

    _paths, vault, _repo = _vault(
        tmp_path,
        plants=[
            _plant(id="pe_no_repair", required_repair=""),
            _plant(id="pe_is_repair", required_repair=BELIEF_SIGNATURE),
            _plant(id="pe_unsourced", misconception_id=None, facet_id=None),
        ],
        prompt="Find the 2 errors below.",
    )

    issues: list = []
    _check_blueprints_and_criteria(vault, issues)
    codes = {issue.code for issue in issues}

    assert "error_hunt:no_required_repair" in codes
    assert "error_hunt:plant_matches_repair" in codes
    assert "error_hunt:unsourced_plant" in codes
    assert "error_hunt:declares_error_count" in codes


def test_the_doctor_is_silent_on_a_well_formed_error_hunt(tmp_path):
    _paths, vault, _repo = _vault(tmp_path)

    from learnloop.services.doctor import _check_blueprints_and_criteria

    issues: list = []
    _check_blueprints_and_criteria(vault, issues)

    assert not any(issue.code.startswith("error_hunt:") for issue in issues)
