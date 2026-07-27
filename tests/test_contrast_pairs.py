"""Meas §3.A4 contrast pairs (implementation plan item 6.4).

The §10 line these tests exist for:

    A contrast pair whose members fall in different difficulty bands is rejected.

Around it sit the other three things §3.A4 asks for as *gates rather than
guidance* — the manipulation must change the structure of the correct answer, the
differing component must be declared and symmetric, and the two must not be
served adjacent unless their surfaces differ — plus the revert criterion, which
is unmeasurable unless the serving order is randomized AND that randomization is
auditable. Those two ship together here for that reason.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.contrast_pairs import (
    MAX_WITHIN_PAIR_DIFFICULTY_GAP,
    MIN_COMPLETED_PAIRS,
    ORDER_DOMINANCE_CEILING,
    ORDER_EFFECT_METRIC,
    AdjacencyBasis,
    ContrastPairDisposition,
    ContrastPairGate,
    PairGateReason,
    answer_skeleton,
    apply_serving_decisions,
    commission_contrast_pairs,
    contrast_pair_order_effect,
    judge_pair,
    pair_key,
    plan_contrast_pair_serving,
    randomization_draw,
    record_contrast_pair_servings,
)
from learnloop.services.persona_gate import InstrumentClass, classify_instrument, contrast_pair_key
from learnloop.services.scheduler import build_due_queue, SchedulerSession
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault, set_algorithm_version, write_facets

CLOCK = FrozenClock(NOW)
FIRST = "pi_pair_applicable"
SECOND = "pi_pair_inapplicable"
FACET = "f_applicability"

FACETS = [
    {
        "id": FACET,
        "kind": "applicability_condition",
        "claim": "The spectral theorem applies only to symmetric matrices.",
    }
]

BAND = (0.45, 0.60)


def _member(
    item_id: str,
    counterpart: str,
    *,
    expected: str,
    difficulty: float = 0.5,
    surface_family: str = "matrix_symbolic",
    differing: dict | None = ...,
) -> dict:
    payload = {
        "id": item_id,
        "learning_object_id": "lo_svd_definition",
        "practice_mode": "constructed_response",
        "prompt": f"Diagonalize the matrix in {item_id}.",
        "expected_answer": expected,
        "surface_family": surface_family,
        "difficulty": difficulty,
        "evidence_facets": [FACET],
        "evidence_weights": {FACET: 1.0},
        "contrast_of": counterpart,
        "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "c1", "points": 4, "description": "correct"}],
            "fatal_errors": [],
        },
    }
    payload["differing_component"] = (
        {
            "facet": FACET,
            "capability": "method_selection",
            "structural_change": "the symmetry precondition holds in one member and not the other",
        }
        if differing is ...
        else differing
    )
    return payload


def _row(payload, client_item_id) -> dict:
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


def _pair_rows(**overrides):
    first = _member(FIRST, SECOND, expected="Q Lambda Q^T with Lambda = diag(2, 5)", **overrides.get("first", {}))
    second = _member(
        SECOND,
        FIRST,
        expected="not orthogonally diagonalizable; the matrix is not symmetric",
        surface_family="matrix_verbal",
        **overrides.get("second", {}),
    )
    return [_row(first, "c_a"), _row(second, "c_b")]


# ---------------------------------------------------------------------------
# Identity and classification
# ---------------------------------------------------------------------------


def test_a_pair_key_is_derived_not_authored():
    """Both members compute the same key without either naming the pair.

    An authored key can disagree with `contrast_of` and silently split a pair
    into two single-member groups, each of which then passes the joint §3.0 rule
    on its own — the exact check the rule exists to make.
    """

    assert pair_key(FIRST, SECOND) == pair_key(SECOND, FIRST)
    assert contrast_pair_key(_member(FIRST, SECOND, expected="x")) == pair_key(FIRST, SECOND)
    assert contrast_pair_key(_member(SECOND, FIRST, expected="y")) == pair_key(FIRST, SECOND)


def test_carrying_the_pair_fields_is_what_makes_it_a_contrast_pair():
    assert (
        classify_instrument(_member(FIRST, SECOND, expected="x"))
        is InstrumentClass.CONTRAST_PAIR
    )


# ---------------------------------------------------------------------------
# §10: both members must sit in the target band
# ---------------------------------------------------------------------------


def test_a_pair_whose_members_fall_in_different_bands_is_rejected(tmp_path):
    """§10's line, through the live `row_transform` seam.

    §3.A4: "Both members must independently sit in the target difficulty band.
    Not 'one hard, one easy'." A trivial member measures nothing on that member
    and wastes the contrast.
    """

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    gate = ContrastPairGate(vault, difficulty_band_by_lo={"lo_svd_definition": BAND})
    rows = _pair_rows(first={"difficulty": 0.5}, second={"difficulty": 0.05})

    gate(rows)

    verdict = rows[0]["audit"]["contrast_pair_gate"]
    assert verdict["separates"] is False
    assert verdict["reason"] == str(PairGateReason.MEMBER_OUTSIDE_DIFFICULTY_BAND)
    # BOTH members are refused: a pair with one member is not an instrument, it
    # is one item with a dangling reference.
    assert rows[0]["validation_status"] == "invalid"
    assert rows[1]["validation_status"] == "invalid"
    assert len(gate.violations) == 2


def test_members_far_apart_inside_one_wide_band_are_also_rejected(tmp_path):
    """The band check alone does not catch opposite edges of a wide band."""

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    gate = ContrastPairGate(vault, difficulty_band_by_lo={"lo_svd_definition": (0.2, 0.8)})
    rows = _pair_rows(first={"difficulty": 0.22}, second={"difficulty": 0.78})

    gate(rows)

    verdict = rows[0]["audit"]["contrast_pair_gate"]
    assert verdict["reason"] == str(PairGateReason.MEMBERS_DIFFER_IN_DIFFICULTY)
    assert verdict["detail"]["difficulty_gap"] > MAX_WITHIN_PAIR_DIFFICULTY_GAP


def test_a_pair_in_band_with_a_structural_manipulation_passes(tmp_path):
    """The positive control."""

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    gate = ContrastPairGate(vault, difficulty_band_by_lo={"lo_svd_definition": BAND})
    rows = _pair_rows(first={"difficulty": 0.5}, second={"difficulty": 0.55})

    gate(rows)

    assert rows[0]["audit"]["contrast_pair_gate"]["separates"] is True
    assert rows[0]["validation_status"] == "valid"
    assert gate.violations == []


# ---------------------------------------------------------------------------
# The manipulation must change the STRUCTURE of the answer
# ---------------------------------------------------------------------------


def test_the_answer_skeleton_masks_values_and_keeps_structure():
    assert answer_skeleton("x = 3") == answer_skeleton("x = 47")
    assert answer_skeleton("x = 3") != answer_skeleton("no solution exists")


def test_a_pair_differing_only_in_its_numbers_is_rejected(tmp_path):
    """"Different numbers is a clone, and kinship will correctly refuse to count
    it twice anyway.\""""

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    gate = ContrastPairGate(vault, difficulty_band_by_lo={"lo_svd_definition": BAND})
    rows = [
        _row(_member(FIRST, SECOND, expected="Q Lambda Q^T with Lambda = diag(2, 5)"), "c_a"),
        _row(_member(SECOND, FIRST, expected="Q Lambda Q^T with Lambda = diag(7, 9)"), "c_b"),
    ]

    gate(rows)

    verdict = rows[0]["audit"]["contrast_pair_gate"]
    assert verdict["reason"] == str(PairGateReason.MANIPULATION_CHANGES_ONLY_VALUES)
    assert verdict["detail"]["answer_skeletons_differ"] is False


def test_a_pair_must_declare_one_symmetric_differing_component(tmp_path):
    """Authored so the analysis is structural rather than inferred (§3.A4)."""

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)

    missing = judge_pair(
        _member(FIRST, SECOND, expected="a", differing=None),
        _member(SECOND, FIRST, expected="b"),
        difficulty_band=None,
    )
    assert missing.reason is PairGateReason.DIFFERING_COMPONENT_MISSING_OR_ASYMMETRIC

    asymmetric = judge_pair(
        _member(FIRST, SECOND, expected="a"),
        _member(
            SECOND,
            FIRST,
            expected="b",
            differing={"facet": "f_other", "capability": "retrieval"},
        ),
        difficulty_band=None,
    )
    assert asymmetric.reason is PairGateReason.DIFFERING_COMPONENT_MISSING_OR_ASYMMETRIC


def test_a_member_whose_counterpart_does_not_exist_is_refused(tmp_path):
    """A dangling `contrast_of` is one item wearing a pair's clothes."""

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    gate = ContrastPairGate(vault)
    rows = [_row(_member(FIRST, "pi_does_not_exist", expected="a"), "c_a")]

    gate(rows)

    verdict = rows[0]["audit"]["contrast_pair_gate"]
    assert verdict["reason"] == str(PairGateReason.COUNTERPART_UNRESOLVED)
    assert rows[0]["validation_status"] == "invalid"


def test_a_member_can_pair_with_an_item_already_in_the_vault(tmp_path):
    """A commissioned pair may complete across two authoring batches."""

    paths, vault, _repo = _pair_vault(tmp_path)
    gate = ContrastPairGate(vault, difficulty_band_by_lo={"lo_svd_definition": BAND})
    rows = [
        _row(
            _member(
                "pi_pair_new",
                FIRST,
                expected="not orthogonally diagonalizable; the matrix is not symmetric",
                difficulty=0.52,
            ),
            "c_new",
        )
    ]

    gate(rows)

    assert rows[0]["audit"]["contrast_pair_gate"]["separates"] is True


# ---------------------------------------------------------------------------
# Commissioning
# ---------------------------------------------------------------------------


def test_commissioning_turns_identifiability_findings_into_requests(tmp_path):
    """§3.A4: "those findings become contrast-pair authoring requests."

    Driven off a synthetic view rather than a vault so the finding shapes are
    explicit: what is under test is the DISPOSITION per finding class, not
    whether a particular fixture happens to trip a particular check.
    """

    from learnloop.services.identifiability import IdentifiabilityFinding

    from learnloop.services import contrast_pairs as CP

    findings = [
        IdentifiabilityFinding(
            kind="generate_discriminator",
            facet_ids=("f_a", "f_b"),
            capability="",
            target_key="f_a|f_b",
            message="always co-occur",
            suggested_action="generate a discriminator",
            detail="duplicate_signature",
            check=1,
        ),
        IdentifiabilityFinding(
            kind="coarsen_distinction",
            facet_ids=("f_c", "f_d"),
            capability="",
            target_key="f_c|f_d",
            message="identical repairs",
            suggested_action="coarsen",
            detail="duplicate_signature_identical_repairs",
            check=1,
        ),
        IdentifiabilityFinding(
            kind="generate_discriminator",
            facet_ids=("f_e",),
            capability="retrieval,coordination",
            target_key="f_e#capability_confound",
            message="capabilities confounded",
            suggested_action="isolate",
            detail="capability_confounding",
            check=4,
        ),
        IdentifiabilityFinding(
            kind="generate_discriminator",
            facet_ids=("f_f",),
            capability="procedure_execution",
            target_key="f_f#procedure_execution",
            message="no anchor",
            suggested_action="generate",
            detail="missing_anchor",
            check=2,
        ),
        IdentifiabilityFinding(
            kind="generate_discriminator",
            facet_ids=("f_g", "f_h"),
            capability="",
            target_key="planted#a|b",
            message="equivalent planted profiles",
            suggested_action="contrast probe",
            detail="equivalent_planted_profiles",
            check=3,
        ),
    ]

    dispositions = [CP._disposition_for(finding) for finding in findings]

    assert dispositions == [
        ContrastPairDisposition.COMMISSION,
        # D1 has proposed retiring this distinction; commissioning an instrument
        # to preserve it would spend measurement on vocabulary debt.
        ContrastPairDisposition.DEFER_COARSENING,
        # A rung problem: the remedy is an item at the isolated capability.
        ContrastPairDisposition.DEFER_RUNG_COMMISSIONING,
        # Nothing to contrast against until one instrument exists.
        ContrastPairDisposition.DEFER_MISSING_ANCHOR,
        ContrastPairDisposition.COMMISSION,
    ]


def test_the_commissioning_queue_keeps_its_deferrals_with_a_reason(tmp_path):
    """A queue that silently omits uncommissionable rows hides its own backlog."""

    paths, vault, repository = _pair_vault(tmp_path)

    plan = commission_contrast_pairs(vault, repository)

    payload = plan.as_dict()
    assert payload["summary"]["queue_length"] == len(plan.requests)
    assert payload["summary"]["commissioned"] + payload["summary"]["deferred"] == len(
        plan.requests
    )
    for request in plan.deferred:
        assert request.reason  # every deferral says why
    for request in plan.commissioned:
        assert "differ in exactly one requirement" in request.as_dict()["request"]


# ---------------------------------------------------------------------------
# Serving: randomize, separate, record
# ---------------------------------------------------------------------------


def _write_member(paths, item_id, counterpart, *, expected, surface_family, difficulty=0.5):
    write_yaml(
        paths.practice_item_path("linear-algebra", item_id),
        {
            "schema_version": 1,
            **_member(
                item_id,
                counterpart,
                expected=expected,
                surface_family=surface_family,
                difficulty=difficulty,
            ),
            "attempt_types_allowed": ["independent_attempt"],
            "capability": "method_selection",
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )


def _pair_vault(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    write_facets(paths, FACETS)
    _write_member(
        paths,
        FIRST,
        SECOND,
        expected="Q Lambda Q^T with Lambda = diag(2, 5)",
        surface_family="matrix_symbolic",
    )
    _write_member(
        paths,
        SECOND,
        FIRST,
        expected="not orthogonally diagonalizable; the matrix is not symmetric",
        surface_family="matrix_verbal",
        difficulty=0.55,
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=CLOCK)
    return paths, vault, repository


def test_the_draw_is_deterministic_per_session_and_varies_across_them():
    """Reproducible slates, accumulating balance. Both are required.

    `build_due_queue` is called repeatedly for one session and must produce the
    same order; the balance the control depends on accumulates ACROSS sessions.
    """

    key = pair_key(FIRST, SECOND)
    assert randomization_draw(f"s1|{key}") == randomization_draw(f"s1|{key}")
    draws = {randomization_draw(f"s{i}|{key}") < 0.5 for i in range(40)}
    assert draws == {True, False}


def test_serving_randomizes_which_member_goes_first_and_records_the_seed(tmp_path):
    _paths, vault, repository = _pair_vault(tmp_path)
    queue = [FIRST, "pi_svd_define_001", SECOND]

    decisions = plan_contrast_pair_serving(vault, queue, session_id="sess_1")

    assert len(decisions) == 1
    decision = decisions[0]
    assert {decision.first_item_id, decision.second_item_id} == {FIRST, SECOND}
    assert decision.seed == f"sess_1|{pair_key(FIRST, SECOND)}"
    assert 0.0 <= decision.value < 1.0
    # One item sits between them, so they are separated by interleaving.
    assert decision.separated is True
    assert decision.adjacency_basis is AdjacencyBasis.SEPARATED_BY_INTERLEAVING

    written = record_contrast_pair_servings(
        repository, decisions, session_id="sess_1", clock=CLOCK
    )
    assert written == 2
    rows = {row["practice_item_id"]: row for row in repository.contrast_pair_serving_rows()}
    assert rows[decision.first_item_id]["serve_position"] == 0
    assert rows[decision.second_item_id]["serve_position"] == 1
    assert rows[decision.first_item_id]["randomization_seed"] == decision.seed
    # Re-planning the same session writes nothing new: the order the learner saw
    # is the one the first plan chose.
    assert record_contrast_pair_servings(
        repository, decisions, session_id="sess_1", clock=CLOCK
    ) == 0


def test_adjacent_members_are_admitted_only_when_the_surfaces_differ(tmp_path):
    """§3.A4's own exception, read off `surface_family` rather than re-judged."""

    _paths, vault, _repo = _pair_vault(tmp_path)

    differing = plan_contrast_pair_serving(vault, [FIRST, SECOND], session_id="s")[0]
    assert differing.separated is True
    assert differing.adjacency_basis is AdjacencyBasis.SURFACES_DIFFER_SUFFICIENTLY

    # Same surface family, and nothing else in the queue to interleave with.
    vault.practice_items[SECOND].surface_family = "matrix_symbolic"
    same = plan_contrast_pair_serving(vault, [FIRST, SECOND], session_id="s")[0]
    assert same.separated is False
    assert same.adjacency_basis is AdjacencyBasis.QUEUE_TOO_SHORT_TO_SEPARATE


def test_applying_a_decision_swaps_slots_and_moves_nothing_else(tmp_path):
    """A control that reshuffled the queue would confound what it removes."""

    _paths, vault, _repo = _pair_vault(tmp_path)
    queue = ["pi_svd_define_001", SECOND, "pi_other", FIRST]
    decisions = plan_contrast_pair_serving(vault, queue, session_id="sess_swap")

    reordered = apply_serving_decisions(queue, decisions)

    assert reordered[0] == "pi_svd_define_001"
    assert reordered[2] == "pi_other"
    assert set(reordered) == set(queue)
    assert reordered.index(decisions[0].first_item_id) < reordered.index(
        decisions[0].second_item_id
    )


def test_the_scheduler_records_a_serving_for_a_real_session(tmp_path):
    """The wiring test: unhook `_apply_contrast_pair_order` and this fails."""

    _paths, vault, repository = _pair_vault(tmp_path)

    build_due_queue(
        vault,
        repository,
        session=SchedulerSession(session_id="sess_live"),
        clock=CLOCK,
    )

    rows = repository.contrast_pair_serving_rows()
    assert {row["practice_item_id"] for row in rows} == {FIRST, SECOND}
    assert {row["serve_position"] for row in rows} == {0, 1}


# ---------------------------------------------------------------------------
# The revert criterion
# ---------------------------------------------------------------------------


def test_order_effect_abstains_before_enough_completed_pairs(tmp_path):
    _paths, vault, repository = _pair_vault(tmp_path)

    metric = contrast_pair_order_effect(vault, repository)

    assert metric.name == ORDER_EFFECT_METRIC
    assert metric.availability == "no_data"
    assert metric.value is None
    assert metric.detail["verdict"] == "insufficient_completed_pairs"
    assert metric.detail["min_completed_pairs"] == MIN_COMPLETED_PAIRS


def _synthetic_pair(repository, index: int, *, second_worse: bool):
    """One served pair plus the two attempts that complete it."""

    first, second = f"pi_p{index}_a", f"pi_p{index}_b"
    key = pair_key(first, second)
    for position, (item_id, counterpart) in enumerate(((first, second), (second, first))):
        repository.insert_contrast_pair_serving(
            pair_key=key,
            practice_item_id=item_id,
            counterpart_item_id=counterpart,
            serve_position=position,
            randomization_seed=f"seed|{key}",
            randomization_value=0.25 if index % 2 else 0.75,
            separated=True,
            adjacency_basis=str(AdjacencyBasis.SEPARATED_BY_INTERLEAVING),
            session_id=f"sess_{index}",
        )
    for offset, (item_id, correct) in enumerate(
        ((first, True), (second, not second_worse))
    ):
        repository.insert_practice_attempt(
            {
                "id": f"att_{item_id}",
                "practice_item_id": item_id,
                "learning_object_id": "lo_svd_definition",
                "subject": "linear-algebra",
                "concept": "singular_value_decomposition",
                "practice_mode": "constructed_response",
                "attempt_type": "independent_attempt",
                "learner_answer_md": "x",
                "evidence_facets": [FACET],
                "evidence_weights": {FACET: 1.0},
                "rubric_score": 4 if correct else 0,
                "correctness": 1.0 if correct else 0.0,
                "confidence": None,
                "latency_seconds": None,
                "hints_used": 0,
                "error_type": None,
                "grader_confidence": 1.0,
                "manual_review": 0,
                "manual_review_reason": None,
                "created_at": f"2026-07-2{index}T0{offset}:00:00+00:00",
            }
        )


def test_order_effects_dominating_is_named_as_the_revert_verdict(tmp_path):
    """§3.A4's revert direction: the later-served member always fares worse."""

    _paths, vault, repository = _pair_vault(tmp_path)
    for index in range(6):
        _synthetic_pair(repository, index, second_worse=True)

    metric = contrast_pair_order_effect(vault, repository)

    assert metric.availability == "available"
    assert metric.value == 1.0
    assert metric.value > ORDER_DOMINANCE_CEILING
    assert metric.detail["verdict"] == "order_effects_dominate"


def test_the_randomization_balance_is_reported_beside_the_effect(tmp_path):
    """The effect number is meaningless if the draw was not actually random.

    A reader must be able to see that without running a second command, so the
    realized balance travels in the same metric.
    """

    _paths, vault, repository = _pair_vault(tmp_path)
    for index in range(6):
        _synthetic_pair(repository, index, second_worse=index % 2 == 0)

    metric = contrast_pair_order_effect(vault, repository)

    assert metric.detail["randomization_balance"] == 1.0  # every pair served a-first
    assert metric.detail["completed_pairs"] == 6
    assert metric.detail["adjacency"][str(AdjacencyBasis.SEPARATED_BY_INTERLEAVING)] == 12
    assert metric.detail["verdict"] == "within_band"


def test_the_serving_store_is_append_only(tmp_path):
    _paths, _vault, repository = _pair_vault(tmp_path)
    _synthetic_pair(repository, 0, second_worse=True)

    with pytest.raises(Exception):
        with repository.connection() as connection:
            connection.execute("UPDATE contrast_pair_servings SET serve_position = 5")


# ---------------------------------------------------------------------------
# The doctor: the same rules, checked on what actually shipped
# ---------------------------------------------------------------------------


def read_pair_member(paths, item_id: str) -> dict:
    from learnloop.vault.yaml_io import read_yaml

    return read_yaml(paths.practice_item_path("linear-algebra", item_id))


def test_the_doctor_catches_a_one_sided_pair_binding(tmp_path):
    """The gates run on generated proposals; a hand-edited item skips them.

    A one-directional `contrast_of` is one item with a reference, and §3.0's
    joint rule ("the belief-holder must fail exactly one member") cannot even be
    asked of it.
    """

    from learnloop.services.doctor import _check_blueprints_and_criteria

    paths, vault, _repo = _pair_vault(tmp_path)
    write_yaml(
        paths.practice_item_path("linear-algebra", SECOND),
        {
            **read_pair_member(paths, SECOND),
            "contrast_of": None,
            "differing_component": None,
        },
    )
    vault = load_vault(paths.root)

    issues: list = []
    _check_blueprints_and_criteria(vault, issues)
    codes = {issue.code for issue in issues}

    assert "contrast_pair:asymmetric_binding" in codes


def test_the_doctor_is_silent_on_a_well_formed_pair(tmp_path):
    from learnloop.services.doctor import _check_blueprints_and_criteria

    _paths, vault, _repo = _pair_vault(tmp_path)

    issues: list = []
    _check_blueprints_and_criteria(vault, issues)

    assert not any(issue.code.startswith("contrast_pair:") for issue in issues)


# ---------------------------------------------------------------------------
# The two gates compose: §3.0's persona clause and A4's own three
# ---------------------------------------------------------------------------


def test_a_pair_must_satisfy_both_the_persona_gate_and_the_pair_gate(tmp_path):
    """§3.0 owns "the belief-holder fails exactly one member"; A4 owns the rest.

    They are separate gates on purpose — one asks a question about beliefs, the
    other about two payloads — but a shipping pair has to pass both, and this is
    the test that says so. It also pins the authoring consequence the prompt
    warns about: the pair carries a discrimination profile, because §3.0 has to
    be able to PLANT the learner the pair is meant to catch.
    """

    from learnloop.services.persona_gate import GateDecision, PersonaGate, PersonaGateReason

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    rows = _pair_rows(first={"difficulty": 0.5}, second={"difficulty": 0.55})
    # The learner this pair exists to catch: someone who thinks the spectral
    # theorem applies unconditionally, so they write the SECOND member's answer
    # on both prompts. They fail exactly one member — which is the clause.
    rows[0]["payload"]["discrimination_profiles"] = [
        {
            "id": "dp_ignores_symmetry",
            "hypothesis": "believes every square matrix is orthogonally diagonalizable",
            "observable_signature": "Q Lambda Q^T with Lambda = diag(2, 5)",
            "facet_id": FACET,
        }
    ]

    persona_gate = PersonaGate(vault, repository)
    pair_gate = ContrastPairGate(vault, difficulty_band_by_lo={"lo_svd_definition": BAND})
    persona_gate(rows)
    pair_gate(rows)

    assert {outcome.reason for outcome in persona_gate.outcomes} == {
        PersonaGateReason.CONTRAST_PAIR_SEPARATES
    }
    assert {outcome.decision for outcome in persona_gate.outcomes} == {GateDecision.PASS}
    assert rows[0]["audit"]["contrast_pair_gate"]["separates"] is True
    assert rows[0]["validation_status"] == "valid"
    assert rows[1]["validation_status"] == "valid"


def test_a_pair_the_persona_gate_cannot_plant_does_not_ship(tmp_path):
    """§3.0's A4 clause is unanswerable without a belief to plant.

    Recorded here rather than left implicit: it is the one authoring constraint
    A4 inherits from the shared gate, and the reason the authoring rule tells the
    model to give the pair a profile.
    """

    from learnloop.services.persona_gate import GateDecision, PersonaGate, PersonaGateReason

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    # No profile, no declared belief answer, and a legacy vault whose facets carry
    # no `error_signatures`: there is nothing to plant.
    rows = _pair_rows(first={"difficulty": 0.5}, second={"difficulty": 0.55})

    gate = PersonaGate(vault, repository)
    gate(rows)

    assert {outcome.decision for outcome in gate.outcomes} == {GateDecision.BLOCK}
    assert {outcome.reason for outcome in gate.outcomes} == {
        PersonaGateReason.INSUFFICIENT_PERSONA_PAYLOAD
    }
    assert rows[0]["validation_status"] == "invalid"
    assert any(
        error.startswith("persona_gate:") for error in rows[0]["validation_errors"]
    )


def test_three_rows_claiming_one_pair_key_are_refused_together(tmp_path):
    """§3.A4 is "two prompts differing in exactly one requirement".

    A third row makes "the difference" undefined. The gate used to judge
    ``members[0]`` against ``members[1]`` and record that verdict against every
    row in the group — so a third item was admitted or refused on evidence about
    two other items. Refusing the whole group with its own reason is the honest
    answer: the authoring error is the group, not any one member.
    """

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    gate = ContrastPairGate(vault, difficulty_band_by_lo={"lo_svd_definition": BAND})
    rows = _pair_rows()
    # The realistic shape: one batch emits the same member twice (same id, same
    # counterpart), so all three rows derive the same pair key.
    third = {
        **rows[1],
        "client_item_id": "c_c",
        "payload": {**rows[1]["payload"], "expected_answer": "a third answer"},
    }
    everyone = [*rows, third]

    gate(everyone)

    reasons = {row["audit"]["contrast_pair_gate"]["reason"] for row in everyone}
    assert reasons == {str(PairGateReason.PAIR_OVERSUBSCRIBED)}
    assert all(
        row["audit"]["contrast_pair_gate"]["separates"] is False for row in everyone
    )
