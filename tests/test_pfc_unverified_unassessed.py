"""PF-c unverified criteria are unassessed everywhere (owner decision 2026-10-12).

The valid-alternative gate fires when the deterministic final-answer check
verifies the answer but the blind grader marked a criterion down without
locating an error in the learner's words. Such a criterion was never exercised
by the learner's route, so it is neither credit nor failure, consistently:

* the attempt's grade is over the assessed criteria only, and the FSRS rating
  reads that grade (no separate path);
* with nothing assessed the verified answer schedules as correct and the
  attempt is no evidence at all;
* the canonical projection, the evidence timeline and the learner field write
  no facet evidence for it, live, on a regrade and on replay;
* joint vaults never carry the block, so they replay exactly as before.

Fakes only; no network.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from learnloop.algorithm_versions import DIAGNOSIS_SPLIT_VERSIONS
from learnloop.attempts.attempts import fsrs_rating_for_attempt
from learnloop.attempts.grading_support import (
    UNASSESSED_CRITERION_LABEL,
    UNVERIFIED_REVIEW_REASON,
)
from learnloop.attempts.regrade import regrade_attempt
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.diagnosis.split.jobs import diagnosis_status
from learnloop.diagnosis.split.live import needs_diagnosis
from learnloop.field.outcomes import data_check, load_attempt_rows, load_facet_rows
from learnloop.substrate.canonical_projection import (
    UNVERIFIED_CRITERION_BLOCK,
    project_canonical_facet_state,
    unassessed_evidence_row,
)
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault

from tests.diagnosis_fakes import ReviewFakeClient
from tests.split_live_helpers import ReadyRuntime, append_config, drain_jobs, split_vault, submit
from tests.test_field_split_outcomes import _ZeroEverythingWithoutAttribution

#: The reference's final answer, reached by a different route: PF-c's
#: final-answer check verifies it.
VERIFYING_ANSWER = "A different route.\nFinal answer: U Sigma V^T"
ITEM = "pi_svd_compute_001"  # setup (2, measures compute) + result (2, measures recall)
LO = "lo_svd_compute"
CLOCK = FrozenClock(datetime(2026, 11, 1, 12, 0, tzinfo=UTC))
HEAD_FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_216"
#: Every split version grades blind, so the rule holds at each of them, never
#: at mvp-0.10 alone (mvp-0.11 = the mvp-0.10 split plus placement).
SPLIT_VERSIONS = sorted(DIAGNOSIS_SPLIT_VERSIONS)
at_every_split_version = pytest.mark.parametrize("version", SPLIT_VERSIONS)


class _PartialWithoutAttribution(ReviewFakeClient):
    """Gives ``result`` half its points on any answer, naming no error.

    On a verifying answer the gate records ``result`` unverified while the
    grader's own sum is 3/4: the kept point is what must no longer count."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        evidence = [
            row.model_copy(update={"points_awarded": 1.0}) if row.criterion_id == "result" else row
            for row in result.criterion_evidence
        ]
        return result.model_copy(
            update={
                "criterion_evidence": evidence,
                "rubric_score": int(sum(row.points_awarded for row in evidence)),
                "error_attributions": [],
            }
        )


def _mapped_split_vault(tmp_path, version: str = "mvp-0.10"):
    """The split vault with its SVD items' criteria authored onto their facets
    (``setup`` -> compute, ``result`` -> recall), so the attempt step and the
    learner field use the same criterion -> facet map the projection compiles
    from the criteria's targets."""

    from learnloop.vault.yaml_io import read_yaml, write_yaml

    paths, _vault, repository = split_vault(tmp_path, version=version)
    for item_id in (ITEM, "pi_svd_compute_002"):
        item_path = paths.practice_item_path("linear-algebra", item_id)
        item = read_yaml(item_path)
        item["criterion_facet_weights"] = {"setup": {"compute": 1.0}, "result": {"recall": 1.0}}
        write_yaml(item_path, item)
    return paths, load_vault(paths.root), repository


def _mass(repository, facet: str) -> tuple[float, float]:
    """(positive, negative) projected mass on ``facet``, over capabilities."""

    cells = [cell for cell in repository.facet_capability_evidence_all() if cell.facet_id == facet]
    positive = sum(cell.direct_positive_mass + cell.embedded_positive_mass for cell in cells)
    negative = sum(cell.direct_negative_mass + cell.embedded_negative_mass for cell in cells)
    return positive, negative


def _cells(repository) -> dict[tuple[str, str], tuple[float, ...]]:
    return {
        (cell.facet_id, cell.capability): (
            round(cell.direct_positive_mass, 12),
            round(cell.embedded_positive_mass, 12),
            round(cell.direct_negative_mass, 12),
            round(cell.embedded_negative_mass, 12),
            round(cell.certification_credit, 12),
        )
        for cell in repository.facet_capability_evidence_all()
    }


def _timeline_endpoint(vault, repository, facet: str) -> float:
    from learnloop.learner.facet_evidence_timeline import facet_evidence_timelines

    series = facet_evidence_timelines(vault, repository, [facet]).get(facet, [])
    return series[-1].demonstrated if series else 0.0


def _banked(repository, facet: str) -> float:
    return sum(
        cell.certification_credit
        for cell in repository.facet_capability_evidence_all()
        if cell.facet_id == facet
    )


def _support(repository, attempt_id: str) -> dict:
    return repository.latest_blind_grade_record(attempt_id)["record"]["grading_support"]


def _mastery(repository) -> tuple[float, float, int]:
    state = repository.mastery_state(LO)
    return (state.logit_mean, state.logit_variance, state.evidence_count)


# -- the gate on a complement-route answer --------------------------------------


@at_every_split_version
def test_a_complement_route_is_graded_on_its_assessed_criteria_only(tmp_path, version):
    """``result`` is unverified with one kept point (grader sum 3/4). The
    grade is over ``setup`` alone (2/2, so 4/4), the FSRS rating reads that
    grade, and ``result``'s facet gets neither the kept point nor a failure."""

    _paths, vault, repository = _mapped_split_vault(tmp_path, version)
    project_canonical_facet_state(vault, repository)
    recall_before, compute_before = _mass(repository, "recall"), _mass(repository, "compute")

    result = submit(vault, repository, _PartialWithoutAttribution(), answer=VERIFYING_ANSWER)

    attempt = repository.fetch_practice_attempt(result.attempt_id)
    assert (attempt["rubric_score"], attempt["correctness"]) == (4, 1.0)
    assert (result.rubric_score, result.correctness) == (4, 1.0)
    item = vault.practice_items[ITEM]
    assert result.fsrs_rating == fsrs_rating_for_attempt(item, attempt["rubric_score"], 4, 0).name.lower()
    assert result.fsrs_rating == "easy"
    support = _support(repository, result.attempt_id)
    assert support["unverified_criterion_ids"] == ["result"]
    assert support["assessed_shortfall"] is False
    # The grader's own measurement stays in its ledger untouched.
    assert repository.latest_blind_grade_record(result.attempt_id)["record"]["rubric_score"] == 3
    # No facet evidence for the unverified criterion, either way.
    assert _mass(repository, "recall") == pytest.approx(recall_before)
    assert _mass(repository, "compute")[0] > compute_before[0]
    debug = repository.attempt_debug_payload(result.attempt_id)
    assert debug["unassessed_criteria"] == ["result"]
    assert "recall" not in debug["facet_outcomes"] and debug["facet_outcomes"]
    # The review flag is a log only: recorded, and nothing waits on it.
    assert attempt["manual_review_reason"] == UNVERIFIED_REVIEW_REASON
    assert diagnosis_status(repository, result.attempt_id)["status"] == "not_needed"
    rows = {row.criterion_id: row for row in repository.fetch_grading_evidence(result.attempt_id)}
    assert rows["result"].points_awarded == 1.0
    assert unassessed_evidence_row(rows["result"].attribution_json)


@at_every_split_version
def test_an_attempt_with_no_assessed_criterion_schedules_as_correct_and_is_no_evidence(tmp_path, version):
    """Every criterion zeroed with no error named: nothing is assessed. The
    deterministic check verified the answer, so it schedules as correct; no
    facet, and not the learning object's belief, takes any evidence."""

    _paths, vault, repository = split_vault(tmp_path, version=version)
    project_canonical_facet_state(vault, repository)
    cells_before = _cells(repository)
    mastery_before = _mastery(repository)

    result = submit(vault, repository, _ZeroEverythingWithoutAttribution(), answer=VERIFYING_ANSWER)

    attempt = repository.fetch_practice_attempt(result.attempt_id)
    assert (attempt["rubric_score"], attempt["correctness"]) == (4, 1.0)
    assert result.fsrs_rating == "easy"
    support = _support(repository, result.attempt_id)
    assert sorted(support["unverified_criterion_ids"]) == ["result", "setup"]
    assert support["assessed_shortfall"] is False
    state = repository.practice_item_state(ITEM)
    assert state.due_at == result.due_at and state.stability is not None
    assert _cells(repository) == cells_before
    assert _mastery(repository) == pytest.approx(mastery_before)
    debug = repository.attempt_debug_payload(result.attempt_id)
    assert debug["covered_facets"] == {} and debug["facet_outcomes"] == {}
    assert debug["unassessed_criteria"] == ["result", "setup"]
    assert diagnosis_status(repository, result.attempt_id)["status"] == "not_needed"


def test_a_located_error_beside_an_unverified_criterion_still_counts(tmp_path):
    """The gate leaves a located failure in force: it is assessed, it lowers
    the grade over the assessed criteria, and the attempt is diagnosed."""

    from learnloop.attempts.blind_grading import BlindGradingProposal
    from learnloop.attempts.grading import resolved_rubric
    from learnloop.attempts.grading_support import apply_valid_alternative_gate, reference_policy

    paths, vault, _repository = split_vault(tmp_path, seed=False)
    item = vault.practice_items[ITEM]
    rubric = resolved_rubric(vault, item)
    answer = "I first wrote U Sigma V, then fixed it.\nFinal answer: U Sigma V^T"
    proposal = BlindGradingProposal.model_validate(
        {
            "local_analysis_md": "reading",
            "attempt_id": "att",
            "practice_item_id": ITEM,
            "criterion_evidence": [
                {"criterion_id": "setup", "points_awarded": 1, "evidence": "e"},
                {"criterion_id": "result", "points_awarded": 0, "evidence": "e"},
            ],
            "rubric_score": 1,
            "error_attributions": [
                {
                    "error_type": "conceptual_slip",
                    "evidence": "x",
                    "first_divergence": {"anchor_kind": "span", "criterion_id": "setup", "quote": "U Sigma V,"},
                    "target_criterion_ids": ["setup"],
                    "validity_scope": "valid_measurement",
                    "resolution_status": "resolved",
                }
            ],
            "grader_confidence": 0.8,
        }
    )
    gate = apply_valid_alternative_gate(
        proposal, rubric=rubric, learner_answer_md=answer, policy=reference_policy(item, answer)
    )
    assert gate.applied and gate.unverified_criterion_ids == ("result",)
    assert gate.assessed_shortfall is True

    from learnloop.attempts.attempts import assessed_rubric_score

    # setup 1/2 over the assessed criterion only: 0.5 of the 4-point scale.
    assert assessed_rubric_score(rubric, {"setup": 1, "result": 0}, [], unassessed_criterion_ids=["result"]) == 2
    # Nothing unassessed: the validator's derived score exactly.
    assert assessed_rubric_score(rubric, {"setup": 1, "result": 1}, [], unassessed_criterion_ids=[]) == 2
    # Nothing assessed: the verified answer is correct.
    assert assessed_rubric_score(rubric, {"setup": 0, "result": 0}, [], unassessed_criterion_ids=["setup", "result"]) == 4

    record = {
        "rubric_score": 1,
        "max_points": 4,
        "error_attributions": [{"validity_scope": "grader_interpretation"}],
        "grading_support": {"valid_alternative_gate_applied": True, "assessed_shortfall": False},
    }
    assert needs_diagnosis(record) is False
    assert needs_diagnosis({**record, "fatal_errors": ["f"]}) is True
    assert needs_diagnosis({**record, "grading_support": {**record["grading_support"], "assessed_shortfall": True}})
    # A record written before the rule keeps the old reading.
    assert needs_diagnosis({**record, "grading_support": {"valid_alternative_gate_applied": True}}) is True


# -- a regrade ----------------------------------------------------------------------


@at_every_split_version
def test_a_regrade_applies_the_same_rule(tmp_path, version):
    """A full-credit grade is regraded to an unverified ``result``: the
    regrade's grade is over ``setup`` alone, the full grade's credit on
    ``result``'s facet is withdrawn, and no partial credit replaces it."""

    _paths, vault, repository = _mapped_split_vault(tmp_path, version)
    project_canonical_facet_state(vault, repository)
    recall_before = _mass(repository, "recall")
    result = submit(vault, repository, ReviewFakeClient(), answer=VERIFYING_ANSWER)
    assert repository.fetch_practice_attempt(result.attempt_id)["rubric_score"] == 4
    recall_full = _mass(repository, "recall")
    assert recall_full[0] > recall_before[0]

    attempt = repository.fetch_practice_attempt(result.attempt_id)
    regrade_attempt(
        vault, repository, attempt, runtime=ReadyRuntime(), client=_PartialWithoutAttribution(),
        grading_source="ai", clock=None,
    )

    attempt = repository.fetch_practice_attempt(result.attempt_id)
    assert (attempt["rubric_score"], attempt["correctness"]) == (4, 1.0)
    assert attempt["manual_review_reason"] == UNVERIFIED_REVIEW_REASON
    rows = {row.criterion_id: row for row in repository.fetch_grading_evidence(result.attempt_id)}
    assert rows["result"].points_awarded == 1.0 and unassessed_evidence_row(rows["result"].attribution_json)
    assert _mass(repository, "recall") == pytest.approx(recall_before)
    debug = repository.attempt_debug_payload(result.attempt_id)
    assert debug["unassessed_criteria"] == ["result"]
    assert "recall" not in debug["facet_outcomes"]
    # The regrade queues a re-diagnosis; the job finds nothing assessed to explain.
    drain_jobs(vault, repository, ReviewFakeClient())
    assert diagnosis_status(repository, result.attempt_id)["status"] == "not_needed"


# -- replay and rebuild parity --------------------------------------------------------


def _live_view(repository, attempt_ids) -> dict:
    view = {}
    for attempt_id in attempt_ids:
        attempt = repository.fetch_practice_attempt(attempt_id)
        debug = repository.attempt_debug_payload(attempt_id)
        view[attempt_id] = {
            "score": (attempt["rubric_score"], attempt["correctness"], attempt["manual_review_reason"]),
            "unassessed": debug.get("unassessed_criteria"),
            "covered": debug["covered_facets"],
            "outcomes": debug["facet_outcomes"],
        }
    return view


@at_every_split_version
def test_split_vault_replay_and_rebuild_keep_unverified_criteria_unassessed(tmp_path, version):
    _paths, vault, repository = _mapped_split_vault(tmp_path, version)
    partial = submit(vault, repository, _PartialWithoutAttribution(), answer=VERIFYING_ANSWER)
    nothing = submit(
        vault, repository, _ZeroEverythingWithoutAttribution(), item_id="pi_svd_compute_002",
        answer="Another route.\nFinal answer: U Sigma V^T",
    )
    attempts = (partial.attempt_id, nothing.attempt_id)
    live = _live_view(repository, attempts)
    live_recall = _mass(repository, "recall")
    assert live[partial.attempt_id]["score"][:2] == (4, 1.0)
    assert live[nothing.attempt_id]["covered"] == {}

    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    first = (_live_view(repository, attempts), _cells(repository), _mastery(repository))
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    second = (_live_view(repository, attempts), _cells(repository), _mastery(repository))

    assert second == first
    assert first[0] == live
    assert _mass(repository, "recall") == pytest.approx(live_recall)


def test_joint_grades_replay_untouched_beside_blind_unverified_ones(tmp_path):
    """Kill switch off after a blind unverified grade: the joint grade that
    follows (on a wrong answer, a real failure) replays exactly as graded,
    while the blind one keeps its assessed grade."""

    paths, vault, repository = split_vault(tmp_path)
    blind = submit(vault, repository, _PartialWithoutAttribution(), answer=VERIFYING_ANSWER)
    append_config(paths.root, "[diagnosis]\nsplit_enabled = false")
    vault = load_vault(paths.root)
    joint = submit(vault, repository, ReviewFakeClient(), item_id="pi_svd_compute_002", answer="B = U Sigma V nope")
    assert repository.latest_blind_grade_record(joint.attempt_id) is None
    joint_rows = [
        (row.criterion_id, row.points_awarded, row.attribution_json)
        for row in repository.fetch_grading_evidence(joint.attempt_id)
    ]
    assert not any(unassessed_evidence_row(raw) for _cid, _points, raw in joint_rows)
    live = _live_view(repository, (blind.attempt_id, joint.attempt_id))
    assert live[joint.attempt_id]["unassessed"] is None
    assert live[joint.attempt_id]["score"][:2] == (0, 0.0)

    rebuild_all_derived_state(vault, repository, clock=CLOCK)

    assert _live_view(repository, (blind.attempt_id, joint.attempt_id)) == live
    assert live[blind.attempt_id]["score"][:2] == (4, 1.0)


@pytest.mark.durability
def test_joint_fixture_replays_through_the_unchanged_path(tmp_path, monkeypatch):
    """Joint vaults never carry the block, so every replayed attempt passes an
    empty unassessed set and a same-version rebuild is a fixed point."""

    from learnloop.attempts import attempts as attempts_module

    root = tmp_path / "head"
    copy_tree_with_databases(HEAD_FIXTURE, root)
    vault = load_vault(root)
    repository = Repository(root / "state.sqlite")
    with connect(repository.sqlite_path, read_only=True) as connection:
        raws = [row[0] for row in connection.execute("SELECT attribution_json FROM grading_evidence")]
    assert raws and not any(unassessed_evidence_row(raw) for raw in raws)

    seen: list[tuple[str, ...]] = []
    original = attempts_module._compute_resolved_grade_application

    def spy(*args, **kwargs):
        seen.append(tuple(kwargs["unassessed_criterion_ids"]))
        return original(*args, **kwargs)

    monkeypatch.setattr(attempts_module, "_compute_resolved_grade_application", spy)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    first = _cells(repository)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)

    assert seen and set(seen) == {()}
    assert _cells(repository) == first


# -- field and projection agreement ------------------------------------------------------


@pytest.mark.parametrize("mapped", [True, False], ids=["authored_map", "targets_only"])
def test_field_projection_and_timeline_read_unverified_criteria_the_same_way(tmp_path, mapped):
    """With the authored criterion -> facet map and without it (the ordinary
    item: only the criteria's targets name the facets; review F1)."""

    _paths, vault, repository = (_mapped_split_vault if mapped else split_vault)(tmp_path)
    project_canonical_facet_state(vault, repository)
    recall_before = _mass(repository, "recall")
    partial = submit(vault, repository, _PartialWithoutAttribution(), answer=VERIFYING_ANSWER)
    nothing = submit(
        vault, repository, _ZeroEverythingWithoutAttribution(), item_id="pi_svd_compute_002",
        answer="Another route.\nFinal answer: U Sigma V^T",
    )

    with repository.connection() as connection:
        attempts = {
            row.attempt_id: row
            for row in load_attempt_rows(connection, vault, legacy_fallback="current_content")
        }
        facets = {}
        for row in load_facet_rows(connection, vault, legacy_fallback="current_content"):
            facets.setdefault(row.attempt_id, {})[row.facet_id] = row.outcome
        report = data_check(connection, vault, legacy_fallback="current_content")

    # The field: the partial attempt is measured on setup alone; the empty one is not a row.
    assert attempts[partial.attempt_id].outcome == 1.0
    assert facets[partial.attempt_id] == {"compute": 1.0}
    assert nothing.attempt_id not in attempts and nothing.attempt_id not in facets
    assert report["pf_c_unverified_attempts"] == 2
    assert report["attempts_without_outcome_row"][UNVERIFIED_CRITERION_BLOCK] == 1
    # The projection agrees: no recall evidence from either attempt...
    assert _mass(repository, "recall") == pytest.approx(recall_before)
    # ...and the live debug outcome now matches the field's row where both exist.
    debug = repository.attempt_debug_payload(partial.attempt_id)
    assert debug["facet_outcomes"] == pytest.approx(facets[partial.attempt_id])
    # The learner-facing timeline plots exactly what the projection banked.
    for facet in ("recall", "compute"):
        assert _timeline_endpoint(vault, repository, facet) == pytest.approx(
            _banked(repository, facet), abs=1e-9
        )


# -- learner-facing feedback -----------------------------------------------------------------


def test_feedback_shows_an_unverified_criterion_as_not_assessed(tmp_path):
    from learnloop.attempts.grading import resolved_rubric
    from learnloop.tui.screens.feedback import FeedbackScreen
    from learnloop_sidecar.handlers.serializers import feedback_bundle

    _paths, vault, repository = split_vault(tmp_path)
    result = submit(vault, repository, _PartialWithoutAttribution(), answer=VERIFYING_ANSWER)

    bundle = feedback_bundle(vault, repository, result.attempt_id)
    rows = {row["criterionId"]: row for row in bundle["criterionEvidence"]}
    assert rows["result"]["assessed"] is False
    assert rows["result"]["notAssessedLabel"] == UNASSESSED_CRITERION_LABEL
    assert rows["setup"]["assessed"] is True and rows["setup"]["notAssessedLabel"] is None
    assert (bundle["rubricScore"], bundle["maxPoints"], bundle["fsrsRating"]) == (4, 4, "easy")
    assert "diagnosisStatus" not in bundle  # nothing assessed fell short: no diagnosis card

    screen = SimpleNamespace(
        rubric=resolved_rubric(vault, vault.practice_items[ITEM]),
        state=SimpleNamespace(repository=repository),
        criterion_points={},
        _criterion_mark=lambda awarded, points: FeedbackScreen._criterion_mark(None, awarded, points),
    )
    text = FeedbackScreen._rubric_evidence_content(screen, result).plain
    assert f"result  {UNASSESSED_CRITERION_LABEL}" in text
    assert "setup  2.0/2" in text
    assert "1.0/2" not in text


def test_the_stamped_block_is_read_from_text_or_mapping():
    from learnloop.attempts.attempts import unverified_attribution_json
    from learnloop.outcome_contract import PFC_REVIEW_REASON
    from learnloop.substrate.canonical_projection import unverified_evidence_row

    block = unverified_attribution_json()
    assert json.loads(block)["unverified_interpretation"] == "unassessed"
    assert unassessed_evidence_row(block) and unassessed_evidence_row(json.loads(block))
    assert unverified_evidence_row(block)
    # A block written before the unassessed rule (no interpretation mark) is
    # still an unverified row, read the M2 way: not an unassessed one.
    before = json.dumps({"targets": [], "negative_evidence_blocked": UNVERIFIED_CRITERION_BLOCK})
    assert unverified_evidence_row(before) and unverified_evidence_row(json.loads(before))
    assert not unassessed_evidence_row(before)
    for other in (None, "not json", json.dumps({"targets": [], "negative_evidence_blocked": "machine_review_scope"})):
        assert not unassessed_evidence_row(other) and not unverified_evidence_row(other)
    # The dependency-free label contract names the same review reason.
    assert PFC_REVIEW_REASON == UNVERIFIED_REVIEW_REASON
