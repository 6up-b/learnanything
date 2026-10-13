"""Route rules in the grader (successor mvp-0.18, a placeholder tag).

route-check-in-grader (owner decision 2026-10-13) folded mvp-0.17's separate
route check (an item-kind reading, an independent re-derivation call and a
deterministic gate) into the blind grader's prompt. The protective core is
kept:

* the grader grades each criterion on the learner's own route, marks down
  only by quoting the failing step verbatim and says so rather than marking
  down a route it cannot verify; it keeps reporting
  ``route_check.divergent_route``;
* one deterministic rule reads only the grader's output: a mark-down on a
  divergent route with no verbatim quote that occurs in the answer is
  unverified, so unassessed (P1). With nothing then assessed and nothing
  validated the grade is held for review through the held-grade predicate. A
  conclusion that ``differs_from_reference`` is never unassessed, and fatal
  errors keep their mark-downs.

One grading call; no second model. Fakes only; no network.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    PROOF_ROUTE_CHECK_ALGORITHM_VERSION,
    ROUTE_RULES_ALGORITHM_VERSION,
    ROUTE_RULES_VERSIONS,
    SUCCESSOR_CHAIN,
)
from learnloop.attempts.ai_contracts import CriterionEvidence
from learnloop.attempts.blind_grading import BlindErrorAttribution, BlindGradingProposal
from learnloop.attempts.grading_support import (
    HELD_REVIEW_REASON,
    REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION,
    ROUTE_RULES,
    ROUTE_RULES_SUFFIX,
    UNVERIFIED_REVIEW_REASON,
    RouteCheck,
    apply_route_rule,
    route_rules_active,
)
from learnloop.attempts.regrade import regrade_attempt
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.diagnosis.split.jobs import diagnosis_status
from learnloop.outcome_contract import GRADE_HELD_FOR_REVIEW
from learnloop.substrate.canonical_projection import project_canonical_facet_state, unassessed_evidence_row
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault
from learnloop.vault.models import Rubric

from tests.diagnosis_fakes import ReviewFakeClient
from tests.split_live_helpers import ReadyRuntime, split_vault, submit

VERSION = ROUTE_RULES_ALGORITHM_VERSION
ITEM = "pi_svd_compute_001"  # setup (2) + result (2)
#: A route the default fake grades 0/4: ``setup`` with no located error,
#: ``result`` with the located quote "Take the eigenvectors".
ALTERNATIVE = "Take the eigenvectors of A^T A for V, then U = A V Sigma^{-1}."
CLOCK = FrozenClock(datetime(2026, 11, 1, 12, 0, tzinfo=UTC))


class DivergentGrader(ReviewFakeClient):
    """The default fake's grade on a route it reads as divergent
    (``route_check.divergent_route``): ``setup`` marked down with nothing
    located, ``result`` marked down with a quote from the answer (naming no
    facet, so the grade carries no review concern of its own)."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        attributions = [
            row.model_copy(update={"target_evidence_families": [], "target_criterion_ids": ["result"]})
            for row in result.error_attributions
        ]
        update = {"error_attributions": attributions}
        if hasattr(result, "route_check"):
            update["route_check"] = RouteCheck(divergent_route=True, rederivation_md="re-derived")
        return result.model_copy(update=update)


class DivergentUnlocatedGrader(DivergentGrader):
    """0 on every criterion on a divergent route, locating no error."""

    def _blind_grading(self, request, context):
        return super()._blind_grading(request, context).model_copy(update={"error_attributions": []})


class FullCreditGrader(DivergentGrader):
    """Every criterion at full points on a divergent route (validates it)."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        evidence = [row.model_copy(update={"points_awarded": 2.0}) for row in result.criterion_evidence]
        return result.model_copy(update={
            "criterion_evidence": evidence, "rubric_score": 4, "error_attributions": [],
        })


def _support(repository, attempt_id):
    return repository.latest_blind_grade_record(attempt_id)["record"]["grading_support"]


def _schedule(repository):
    state = repository.practice_item_state(ITEM)
    return (state.difficulty, state.stability, state.due_at)


def _first_scheduled_attempt(vault, repository):
    """A validated attempt (full credit: 4/4) that schedules the item, rebuilt
    once so the baseline schedule is replay's (a rebuild of the seeded vault
    alone moves this item's due date by minutes)."""

    first = submit(vault, repository, FullCreditGrader(), answer=ALTERNATIVE, when=CLOCK.now())
    assert repository.fetch_practice_attempt(first.attempt_id)["rubric_score"] == 4
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    return first


def _projection(repository):
    return sorted(
        (cell.facet_id, cell.capability, round(cell.direct_positive_mass, 12),
         round(cell.direct_negative_mass, 12), round(cell.certification_credit, 12))
        for cell in repository.facet_capability_evidence_all()
    )


# -- the version and the switch ---------------------------------------------------------


def test_the_route_rules_are_the_latest_successor_after_the_route_check():
    assert SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == VERSION == "mvp-0.18"
    assert SUCCESSOR_CHAIN[-2] == PROOF_ROUTE_CHECK_ALGORITHM_VERSION == "mvp-0.17"
    assert ROUTE_RULES_VERSIONS == frozenset({VERSION})


def test_active_only_at_the_successor_with_the_switch_on(tmp_path):
    _paths, vault, _repository = split_vault(tmp_path / "on", version=VERSION, seed=False)
    assert route_rules_active(vault)
    _paths, older, _repository = split_vault(tmp_path / "old", version="mvp-0.17", seed=False)
    assert not route_rules_active(older)
    _paths, off, _repository = split_vault(
        tmp_path / "off", version=VERSION, config="[proof_check]\nenabled = false", seed=False,
    )
    assert not route_rules_active(off)


# -- the deterministic rule (pure) --------------------------------------------------------


RUBRIC = Rubric.model_validate({
    "id": "r", "max_points": 4,
    "criteria": [{"id": "setup", "description": "Sets up", "points": 2},
                 {"id": "result", "description": "Concludes", "points": 2}],
})
ANSWER = "Let x be fixed. Then x squared is positive. So the claim holds."


def _proposal(points, attributions=(), fatal=()):
    return BlindGradingProposal(
        local_analysis_md="a", attempt_id="a1", practice_item_id="i",
        criterion_evidence=[CriterionEvidence(criterion_id=cid, points_awarded=p, evidence=f"grader on {cid}")
                            for cid, p in points.items()],
        rubric_score=int(sum(points.values())), fatal_errors=list(fatal),
        error_attributions=list(attributions), grader_confidence=0.9,
    )


def _attribution(criterion, quote, scope="valid_measurement"):
    return BlindErrorAttribution(
        error_type="conceptual_slip", evidence="e", target_criterion_ids=[criterion],
        first_divergence={"anchor_kind": "span", "criterion_id": criterion, "quote": quote},
        validity_scope=scope,
    )


def _whole_answer(quote=None):
    """An attribution naming no criterion (a whole-answer finding)."""

    return BlindErrorAttribution(
        error_type="conceptual_slip", evidence="the route does not prove the claim",
        target_evidence_families=["svd"], validity_scope="valid_measurement",
        first_divergence=(
            {"anchor_kind": "whole_answer", "criterion_id": "", "quote": quote} if quote else None
        ),
    )


def _rule(proposal, *, final="undecidable", divergent=True, before=(), rubric=RUBRIC):
    return apply_route_rule(
        proposal, rubric=rubric, learner_answer_md=ANSWER, final_answer_status=final,
        divergent_route=divergent, unverified_before=before,
    )


def test_an_unlocated_mark_down_on_a_divergent_route_is_unassessed():
    rule = _rule(_proposal({"setup": 0.0, "result": 2.0}))
    assert rule.applied and rule.unlocated == ("setup",) and rule.unverified == ("setup",)
    assert rule.assessed_shortfall is False and rule.held_for_review is False
    rows = {row.criterion_id: row for row in rule.proposal.criterion_evidence}
    # Unassessed, never restored: the grader's points stay, out of the grade.
    assert rows["setup"].points_awarded == 0.0 and rows["result"].points_awarded == 2.0
    assert rows["setup"].notes.startswith("Not assessed") and "Held" not in rows["setup"].notes
    assert rule.proposal.manual_review_recommended is True


def test_nothing_assessed_and_nothing_validated_is_held_for_review():
    rule = _rule(_proposal({"setup": 0.0, "result": 0.0}), final="no_conclusion")
    assert rule.unlocated == ("setup", "result") and rule.held_for_review is True
    assert all("Held for review" in row.notes for row in rule.proposal.criterion_evidence)
    # Something still assessed (a criterion at full points) is no hold.
    partial = _rule(_proposal({"setup": 0.0, "result": 2.0}), final="no_conclusion")
    assert partial.applied and partial.held_for_review is False
    # A verified final answer validates the answer: PF-c already unassessed
    # its unlocated mark-downs, so nothing is left for this rule and no hold.
    verified = _rule(_proposal({"setup": 0.0, "result": 0.0}), final="matches_reference",
                     before=("result", "setup"))
    assert not verified.applied and verified.held_for_review is False
    assert verified.unverified == ("result", "setup")


@pytest.mark.parametrize("attribution", [
    _attribution("setup", "a step the learner never wrote"),
    _attribution("setup", "Let x be fixed", scope="grader_interpretation"),
], ids=["fabricated_quote", "interpretation_only"])
def test_a_quote_that_is_not_in_the_answer_locates_nothing(attribution):
    rule = _rule(_proposal({"setup": 0.0, "result": 2.0}, [attribution]))
    assert rule.unlocated == ("setup",) and rule.assessed_shortfall is False
    [rescoped] = rule.proposal.error_attributions
    assert rescoped.validity_scope == "grader_interpretation"


def test_a_verbatim_quote_keeps_the_mark_down():
    # Whitespace and case aside, the quote occurs in the answer: a located error.
    rule = _rule(_proposal({"setup": 0.0, "result": 2.0}, [_attribution("setup", "let X  be FIXED")]))
    assert not rule.applied and rule.unverified == () and rule.assessed_shortfall is True
    assert rule.proposal.error_attributions[0].validity_scope == "valid_measurement"


def test_a_conclusion_that_differs_from_the_reference_outranks_the_rule():
    rule = _rule(_proposal({"setup": 0.0, "result": 0.0}), final="differs_from_reference")
    assert not rule.applied and rule.unverified == () and rule.held_for_review is False
    assert rule.assessed_shortfall is True
    assert [row.points_awarded for row in rule.proposal.criterion_evidence] == [0.0, 0.0]


def test_fatal_errors_keep_their_mark_downs():
    rubric = Rubric.model_validate({
        **RUBRIC.model_dump(mode="json"),
        "fatal_errors": [{"id": "wrong_statement", "description": "proves the wrong claim", "max_grade": 0}],
    })
    rule = _rule(_proposal({"setup": 0.0, "result": 0.0}, fatal=["wrong_statement"]), rubric=rubric)
    assert not rule.applied and rule.unverified == () and rule.assessed_shortfall is True


def test_the_rule_reads_only_a_divergent_route():
    rule = _rule(_proposal({"setup": 0.0, "result": 2.0}), divergent=False)
    assert not rule.applied and rule.unverified == () and rule.assessed_shortfall is True


def test_pfc_unverified_criteria_are_not_this_rules():
    rule = _rule(_proposal({"setup": 2.0, "result": 0.0}), final="matches_reference", before=("result",))
    assert not rule.applied and rule.unverified == ("result",)


def test_an_unlocated_whole_answer_attribution_is_the_graders_interpretation():
    """An attribution that names no criterion and locates no step never keeps
    a measured failure on its own once the rule unassesses the mark-downs
    (PF-c rescopes it the same way); one that quotes the answer still counts."""

    rule = _rule(_proposal({"setup": 0.0, "result": 0.0}, [_whole_answer()]))
    assert rule.unverified == ("result", "setup") and rule.assessed_shortfall is False
    assert [row.validity_scope for row in rule.proposal.error_attributions] == ["grader_interpretation"]
    located = _rule(_proposal({"setup": 0.0, "result": 0.0}, [_whole_answer("x squared is positive")]))
    assert [row.validity_scope for row in located.proposal.error_attributions] == ["valid_measurement"]
    assert located.assessed_shortfall is True
    untouched = _rule(_proposal({"setup": 0.0, "result": 2.0}, [_whole_answer()]), divergent=False)
    assert [row.validity_scope for row in untouched.proposal.error_attributions] == ["valid_measurement"]


# -- the prompt and its identity -------------------------------------------------------------


def _blind_plan(vault, answer=ALTERNATIVE, *, stuck=False):
    from learnloop.attempts.attempts import _blind_grading_plan
    from learnloop.attempts.grading import build_grading_context, resolved_rubric

    item = vault.practice_items[ITEM]
    context = build_grading_context(
        vault, item, attempt_id="planned", learner_answer_md=answer, rubric=resolved_rubric(vault, item),
    )
    return _blind_grading_plan(vault, item, context, stuck=stuck)


def test_the_prompt_carries_the_rules_and_names_them_only_at_the_successor(tmp_path):
    from learnloop.attempts.blind_grading import blind_grading_prompt

    _paths, vault, _repository = split_vault(tmp_path / "on", version=VERSION, seed=False)
    plan = _blind_plan(vault)
    assert plan.context.reference_policy["route_rules"] == "own-route-v1"
    assert ROUTE_RULES in blind_grading_prompt(plan.context)
    assert plan.prompt_version == f"mvp-2.1-blind-reference-policy{ROUTE_RULES_SUFFIX}"
    assert plan.calibration_prompt_version == f"{REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION}{ROUTE_RULES_SUFFIX}"
    stuck = _blind_plan(vault, stuck=True)
    assert stuck.prompt_version == f"mvp-2.1-blind-reference-policy{ROUTE_RULES_SUFFIX}+stuck-v1"
    for name, kwargs in (("predecessor", {"version": "mvp-0.17"}),
                         ("kill_switch", {"version": VERSION, "config": "[proof_check]\nenabled = false"})):
        _paths, other, _repository = split_vault(tmp_path / name, seed=False, **kwargs)
        plain = _blind_plan(other)
        assert "route_rules" not in plain.context.reference_policy, name
        assert ROUTE_RULES not in blind_grading_prompt(plain.context), name
        assert plain.prompt_version == "mvp-2.1-blind-reference-policy", name
        assert plain.calibration_prompt_version == REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION, name


# -- live grades -----------------------------------------------------------------------------


def test_a_proof_item_is_graded_in_exactly_one_model_call(tmp_path, monkeypatch):
    """No item reading and no re-derivation: the grader's one call, admitted
    once, and no other client is ever built."""

    from contextlib import nullcontext

    from learnloop.attempts.grading_admission import grading_admission

    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task",
                        lambda *a, **k: pytest.fail("grading builds no second client"))
    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    grader = DivergentGrader()
    admitted: list[str] = []

    def guard(purpose, prompt):
        admitted.append(purpose)
        return nullcontext()

    with grading_admission(guard):
        result = submit(vault, repository, grader, answer=ALTERNATIVE, pipeline=False)
    assert grader.calls == ["blind_grading"] and admitted == ["blind_grading"]
    assert _support(repository, result.attempt_id)["proof_route_check"]["status"] == "checked"
    with connect(repository.sqlite_path, read_only=True) as connection:
        tasks = {row[0] for row in connection.execute("SELECT DISTINCT task FROM judgment_ledger")}
    assert not tasks & {"proof_like_item", "proof_route_check"}


def test_live_an_unlocated_mark_down_on_a_divergent_route_is_unassessed(tmp_path):
    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    result = submit(vault, repository, DivergentGrader(), answer=ALTERNATIVE)
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    support = _support(repository, result.attempt_id)
    rule = support["proof_route_check"]
    assert rule["version"] == "route-rules-in-grader-v1" and rule["rules"] == "own-route-v1"
    assert rule["divergent_route"] is True and rule["final_answer_status"] == "undecidable"
    assert rule["applied"] is True and rule["unlocated_criterion_ids"] == ["setup"]
    assert rule["held_for_review"] is False
    rows = {row.criterion_id: row for row in repository.fetch_grading_evidence(result.attempt_id)}
    # setup is out of the grade; result keeps its located mark-down: 0/2 assessed.
    assert unassessed_evidence_row(rows["setup"].attribution_json)
    assert not unassessed_evidence_row(rows["result"].attribution_json)
    assert (attempt["rubric_score"], attempt["correctness"]) == (0, 0.0)
    assert support["unverified_criterion_ids"] == ["setup"]
    assert support["valid_alternative_gate"] == {"final_answer": False, "proof_route": True}
    assert support["assessed_shortfall"] is True  # the located error is a real shortfall
    assert attempt["manual_review_reason"] == UNVERIFIED_REVIEW_REASON


def test_live_nothing_located_and_nothing_validated_is_held(tmp_path):
    """Nothing assessed and nothing validated: the grader's own 0/4, held for
    review. No FSRS review, no prediction error, no follow-up, no diagnosis;
    replay reproduces the hold from the record, without a model."""

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    _first_scheduled_attempt(vault, repository)
    before = _schedule(repository)
    held = submit(vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE + " (again)",
                  when=CLOCK.now() + timedelta(days=3))
    attempt = repository.fetch_practice_attempt(held.attempt_id)
    rule = _support(repository, held.attempt_id)["proof_route_check"]
    assert rule["held_for_review"] is True and sorted(rule["unlocated_criterion_ids"]) == ["result", "setup"]
    assert (attempt["rubric_score"], attempt["correctness"]) == (0, 0.0)
    assert attempt["manual_review_reason"] == HELD_REVIEW_REASON == GRADE_HELD_FOR_REVIEW
    assert attempt["manual_review"]
    assert _schedule(repository) == before
    assert held.surprise_direction == "none"
    surprise = repository.latest_attempt_surprise(held.attempt_id)
    assert any(action.endswith(":grade_held_for_review") for action in surprise["suppressed_actions"])
    rows = repository.fetch_grading_evidence(held.attempt_id)
    assert rows and all(unassessed_evidence_row(row.attribution_json) for row in rows)
    assert diagnosis_status(repository, held.attempt_id)["status"] == "not_needed"
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert _schedule(repository) == before
    assert repository.fetch_practice_attempt(held.attempt_id)["rubric_score"] == 0


def test_live_a_regrade_keeps_a_hold_until_the_grader_validates_the_route(tmp_path):
    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    _first_scheduled_attempt(vault, repository)
    before = _schedule(repository)
    held = submit(vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE + " (again)",
                  when=CLOCK.now() + timedelta(days=3))
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(held.attempt_id),
                    runtime=ReadyRuntime(), client=DivergentUnlocatedGrader(), grading_source="ai",
                    clock=FrozenClock(CLOCK.now() + timedelta(days=4)))
    assert repository.fetch_practice_attempt(held.attempt_id)["rubric_score"] == 0
    assert _support(repository, held.attempt_id)["proof_route_check"]["held_for_review"] is True
    assert _schedule(repository) == before
    # A regrade that validates the route releases it: credited and reviewed.
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(held.attempt_id),
                    runtime=ReadyRuntime(), client=FullCreditGrader(), grading_source="ai",
                    clock=FrozenClock(CLOCK.now() + timedelta(days=5)))
    assert repository.fetch_practice_attempt(held.attempt_id)["rubric_score"] == 4
    assert _support(repository, held.attempt_id)["proof_route_check"]["held_for_review"] is False
    assert _schedule(repository) != before


def test_live_an_adjudication_releases_a_hold_on_replay(tmp_path):
    from learnloop.attempts.grade_resolution import append_adjudication_evidence_revision

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    _first_scheduled_attempt(vault, repository)
    before = _schedule(repository)
    held = submit(vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE + " (again)",
                  when=CLOCK.now() + timedelta(days=3))
    revision = append_adjudication_evidence_revision(
        repository, attempt_id=held.attempt_id, resolved_fraction=1.0, adjudication_id="adj-rules",
        adjudicator_source="human_owner", rationale="the route is valid", vault=vault,
        clock=FrozenClock(CLOCK.now() + timedelta(days=4)),
    )
    assert revision["status"] == "revised"
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert repository.fetch_practice_attempt(held.attempt_id)["rubric_score"] == 4
    assert _schedule(repository) != before


@pytest.mark.parametrize("config", ["", "[diagnosis]\ngrading_support = false"])
def test_live_a_wrong_final_answer_is_never_unassessed(tmp_path, config):
    """"Name a prime." expects 2; the answer concludes 4 and the grader marks
    it down on a divergent route without a quote: the deterministic check
    outranks the rule. Without PF-c's policy the rules are not in the prompt
    and nothing is unassessed either."""

    class Unlocated(DivergentGrader):
        def _blind_grading(self, request, context):
            return super()._blind_grading(request, context).model_copy(update={"error_attributions": []})

    _paths, vault, repository = split_vault(tmp_path, version=VERSION, config=config)
    result = submit(vault, repository, Unlocated(), item_id="pi_unrelated_001",
                    answer="Four is the smallest even square, so the answer is 4.")
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    assert (attempt["rubric_score"], attempt["correctness"]) == (0, 0.0)
    rows = repository.fetch_grading_evidence(result.attempt_id)
    assert [row.points_awarded for row in rows] == [0.0]
    assert not unassessed_evidence_row(rows[0].attribution_json)
    support = _support(repository, result.attempt_id)
    if config:
        assert "proof_route_check" not in support
    else:
        rule = support["proof_route_check"]
        assert rule["final_answer_status"] == "differs_from_reference" and rule["applied"] is False


@pytest.mark.parametrize("setup", ["kill_switch", "predecessor"])
def test_the_kill_switch_and_mvp017_grade_exactly_as_mvp016(tmp_path, setup):
    """Off (or at mvp-0.17, whose separate check is gone) one call and the
    grade is mvp-0.16's: no rules, no record, the base identity."""

    if setup == "kill_switch":
        _paths, vault, repository = split_vault(tmp_path / "a", version=VERSION,
                                                config="[proof_check]\nenabled = false")
    else:
        _paths, vault, repository = split_vault(tmp_path / "a", version="mvp-0.17")
    _paths, baseline, baseline_repository = split_vault(tmp_path / "b", version="mvp-0.16")
    grader, reference_grader = DivergentGrader(), DivergentGrader()
    result = submit(vault, repository, grader, answer=ALTERNATIVE, when=CLOCK.now())
    reference = submit(baseline, baseline_repository, reference_grader, answer=ALTERNATIVE, when=CLOCK.now())
    assert grader.calls == reference_grader.calls == ["blind_grading"]
    assert ROUTE_RULES not in grader.prompts[0]
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    expected = baseline_repository.fetch_practice_attempt(reference.attempt_id)
    for column in ("rubric_score", "correctness", "manual_review_reason", "error_type"):
        assert attempt[column] == expected[column], column
    assert "proof_route_check" not in _support(repository, result.attempt_id)
    rows = [(r.criterion_id, r.points_awarded, r.attribution_json) for r in repository.fetch_grading_evidence(result.attempt_id)]
    ref = [(r.criterion_id, r.points_awarded, r.attribution_json)
           for r in baseline_repository.fetch_grading_evidence(reference.attempt_id)]
    assert rows == ref
    record = repository.latest_blind_grade_record(result.attempt_id)["record"]
    assert record["calibration_prompt_version"] == REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION


def _identity(repository, attempt_id):
    record = repository.latest_blind_grade_record(attempt_id)["record"]
    return record["calibration_prompt_version"], repository.latest_raw_grade_identity(attempt_id)[0]


def test_a_ruled_grade_is_calibrated_under_the_rules_identity_and_so_is_its_regrade(tmp_path):
    from learnloop.attempts.attempts import replay_grader_identity

    expected = f"{REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION}{ROUTE_RULES_SUFFIX}"
    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    # The identity names the prompt's rules, never a checker: it is the same
    # whatever the rule did to the grade.
    for grader, answer in ((DivergentGrader(), ALTERNATIVE), (ReviewFakeClient(), ALTERNATIVE + " (2)")):
        result = submit(vault, repository, grader, answer=answer)
        assert _identity(repository, result.attempt_id) == (expected, expected)
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(result.attempt_id),
                    runtime=ReadyRuntime(), client=DivergentGrader(), grading_source="ai", clock=CLOCK)
    assert _identity(repository, result.attempt_id) == (expected, expected)
    blind = repository.latest_blind_grade_record(result.attempt_id)
    assert replay_grader_identity(repository, result.attempt_id, blind)[0] == expected


def test_replay_reproduces_ruled_grades_without_a_model(tmp_path, monkeypatch):
    """Same-version rebuild equivalence (playbook item 6): replay reads the
    records as written and never calls a model."""

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    submit(vault, repository, DivergentGrader(), answer=ALTERNATIVE)
    submit(vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE + " (held)")
    submit(vault, repository, FullCreditGrader(), answer=ALTERNATIVE + " (full)")
    project_canonical_facet_state(vault, repository)
    before = _projection(repository)
    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task",
                        lambda *a, **k: pytest.fail("replay must not build a client"))
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    first = _projection(repository)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert first == _projection(repository) == before


# -- config, the CLI plan and the migration ------------------------------------------------


def test_a_retired_proof_check_route_is_ignored_and_reported(tmp_path):
    from learnloop.ops.doctor import run_doctor

    paths, _vault, _repository = split_vault(tmp_path, version=VERSION, seed=False)
    config = paths.root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    assert text.count("[ai.routing]\n") == 1
    text = text.replace("[ai.routing]\n", '[ai.routing]\nproof_check = "codex_low"\n', 1)
    config.write_text(text + "\n[ai.route_output_tokens]\nproof_check = 4096\n", encoding="utf-8")
    loaded = load_vault(paths.root)
    assert not hasattr(loaded.config.ai.routing, "proof_check")
    assert any(issue.code == "config:retired_route" for issue in run_doctor(paths.root).issues)


def test_cli_dry_run_plans_one_grading_call(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    import learnloop.cli as cli_module
    from learnloop.cli.app import app

    _paths, vault, _repository = split_vault(tmp_path, version=VERSION)
    grader = DivergentGrader()
    monkeypatch.setattr(cli_module, "_ready_provider_for_task", lambda *_a, **_k: ("fake", ReadyRuntime(), grader))
    result = CliRunner().invoke(app, [
        "attempt", ITEM, "--answer", ALTERNATIVE, "--criterion-points", "setup=0,result=0", "--json",
        "--no-diagnose", "--dry-run", "--vault", str(vault.root),
    ])
    assert result.exit_code == 0, result.output
    grading = json.loads(result.output)["grading"]
    assert grading["calls"] == 1 and grading["admissible"] is True
    assert grading["prompt_version"].endswith(ROUTE_RULES_SUFFIX)
    assert "proof_check" not in grading and grader.calls == []


def test_migration_186_keeps_its_trigger_which_nothing_writes_now(tmp_path):
    """Migration 186 stays (append-only, harmless): the trigger CHECK still
    admits ``route_check_disagreement`` so mvp-0.17's rows stay valid."""

    from learnloop.db.copies import copy_tree_with_databases
    from learnloop.db.migrate import discover_migrations

    head = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_186"
    root = tmp_path / "head"
    copy_tree_with_databases(head, root)
    assert max(m.version for m in discover_migrations()) == 186
    with connect(root / "state.sqlite") as connection:
        sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE name = 'grading_clarifications'").fetchone()[0]
        assert "'route_check_disagreement'" in sql
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
