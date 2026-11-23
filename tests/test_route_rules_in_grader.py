"""Route rules in the grader (successor mvp-0.20; built as mvp-0.18, a placeholder
tag, and relabelled at its merge after the sources track's mvp-0.18/0.19).

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
from datetime import timedelta
from pathlib import Path

import pytest

from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    PROOF_ROUTE_CHECK_ALGORITHM_VERSION,
    SOURCE_FIRST_NEEDS_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.attempts.attempts import AttemptValidationError
from learnloop.attempts.grading import GradingValidationError
from learnloop.attempts.blind_grading import BlindErrorAttribution
from learnloop.attempts.grading_support import (
    HELD_REVIEW_REASON,
    REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION,
    METHOD_ROUTE_RULES_SUFFIX,
    ROUTE_RULES,
    UNVERIFIED_REVIEW_REASON,
    apply_route_rule,
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
from tests.split_live_helpers import ReadyRuntime, append_config, split_vault, submit
from tests.helpers import MIGRATION_HEAD_FIXTURE
from tests.route_rules_in_grader_helpers import (
    ALTERNATIVE,
    ANSWER,
    CLOCK,
    DivergentGrader,
    DivergentUnlocatedGrader,
    FullCreditGrader,
    ITEM,
    RUBRIC,
    VERSION,
    _first_scheduled_attempt,
    _projection,
    _proposal,
    _schedule,
    _support,
)
from tests.helpers import allow_below_floor

#: When a test that regrades at ``CLOCK`` submits its attempt. ``submit`` with
#: no ``when`` stamps the attempt with the wall clock, and the latest grade is
#: the latest by ``created_at``: once the wall clock passed ``CLOCK`` (12:00 UTC on
#: 2026-11-01) such a regrade sorted before the grade it replaced.
SUBMITTED = CLOCK.now() - timedelta(hours=1)
#: Grading without the own-route rules: PF-c's reference policy off (the rules live in it), the one way left once
#: their own kill switch went.
NO_POLICY = "[diagnosis]\ngrading_support = false"


# -- the version and the switch ---------------------------------------------------------


def test_the_route_rules_follow_the_route_check_and_value_of_information_stopping_follows_them():
    assert SUCCESSOR_CHAIN[11] == VERSION == "mvp-0.20"
    # Value-of-information stopping (mvp-0.21), Tier 1's Decider judgments
    # (mvp-0.22) and router R2a's staged frame (mvp-0.23, the latest)
    # followed the rules and keep them.
    assert SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION == "mvp-0.67"
    # Canonical sources' mvp-0.18 and mvp-0.19 sit between the check and the rules.
    assert SUCCESSOR_CHAIN[10] == SOURCE_FIRST_NEEDS_ALGORITHM_VERSION == "mvp-0.19"
    assert SUCCESSOR_CHAIN[8] == PROOF_ROUTE_CHECK_ALGORITHM_VERSION == "mvp-0.17"


# -- the deterministic rule (pure) --------------------------------------------------------


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


def _rule(proposal, *, final="undecidable", divergent=True, before=(), rubric=RUBRIC, **extra):
    """The rule on ``ANSWER``; ``declared`` (the grader's own unverified
    criteria) and ``clarification`` (the learner's clarification reply) pass
    through when given."""

    if "declared" in extra:
        extra["declared_unverified"] = extra.pop("declared")
    if "clarification" in extra:
        extra["clarification_answer_md"] = extra.pop("clarification")
    return apply_route_rule(
        proposal, rubric=rubric, learner_answer_md=ANSWER, final_answer_status=final,
        divergent_route=divergent, unverified_before=before, **extra,
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


def test_the_prompt_carries_the_rules_and_names_them(tmp_path):
    from learnloop.attempts.blind_grading import blind_grading_prompt

    _paths, vault, _repository = split_vault(tmp_path / "on", seed=False)
    plan = _blind_plan(vault)
    assert plan.context.reference_policy["route_rules"] == "own-route-v2"
    assert ROUTE_RULES in blind_grading_prompt(plan.context)
    assert plan.prompt_version == f"mvp-2.1-blind-reference-policy{METHOD_ROUTE_RULES_SUFFIX}"
    assert plan.calibration_prompt_version == f"{REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION}{METHOD_ROUTE_RULES_SUFFIX}"
    stuck = _blind_plan(vault, stuck=True)
    assert stuck.prompt_version == f"mvp-2.1-blind-reference-policy{METHOD_ROUTE_RULES_SUFFIX}+stuck-v1"


# -- live grades -----------------------------------------------------------------------------


def test_a_proof_item_is_graded_in_exactly_one_model_call(tmp_path, monkeypatch):
    """No item reading and no re-derivation: the grader's one call, admitted
    once, and no other client is ever built."""

    from contextlib import nullcontext

    from learnloop.attempts.grading_admission import grading_admission

    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task",
                        lambda *a, **k: pytest.fail("grading builds no second client"))
    _paths, vault, repository = split_vault(tmp_path)
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
    _paths, vault, repository = split_vault(tmp_path)
    result = submit(vault, repository, DivergentGrader(), answer=ALTERNATIVE)
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    support = _support(repository, result.attempt_id)
    rule = support["proof_route_check"]
    assert rule["version"] == "route-rules-in-grader-v1" and rule["rules"] == "own-route-v2"
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

    _paths, vault, repository = split_vault(tmp_path)
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
    _paths, vault, repository = split_vault(tmp_path)
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

    _paths, vault, repository = split_vault(tmp_path)
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

    _paths, vault, repository = split_vault(tmp_path, config=config)
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


def _identity(repository, attempt_id):
    record = repository.latest_blind_grade_record(attempt_id)["record"]
    return record["calibration_prompt_version"], repository.latest_raw_grade_identity(attempt_id)[0]


def test_a_ruled_grade_is_calibrated_under_the_rules_identity_and_so_is_its_regrade(tmp_path):
    from learnloop.attempts.attempts import replay_grader_identity

    expected = f"{REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION}{METHOD_ROUTE_RULES_SUFFIX}"
    _paths, vault, repository = split_vault(tmp_path)
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

    _paths, vault, repository = split_vault(tmp_path)
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

    paths, _vault, _repository = split_vault(tmp_path, seed=False)
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

    _paths, vault, _repository = split_vault(tmp_path)
    grader = DivergentGrader()
    monkeypatch.setattr(cli_module, "_ready_provider_for_task", lambda *_a, **_k: ("fake", ReadyRuntime(), grader))
    result = CliRunner().invoke(app, [
        "attempt", ITEM, "--answer", ALTERNATIVE, "--criterion-points", "setup=0,result=0", "--json",
        "--no-diagnose", "--dry-run", "--vault", str(vault.root),
    ])
    assert result.exit_code == 0, result.output
    grading = json.loads(result.output)["grading"]
    assert grading["calls"] == 1 and grading["admissible"] is True
    assert grading["prompt_version"].endswith(METHOD_ROUTE_RULES_SUFFIX)
    assert "proof_check" not in grading and grader.calls == []


def test_migration_186_keeps_its_trigger_which_nothing_writes_now(tmp_path):
    """Migration 186 stays (append-only, harmless): the trigger CHECK still
    admits ``route_check_disagreement`` so mvp-0.17's rows stay valid."""

    from learnloop.db.copies import copy_tree_with_databases

    head = MIGRATION_HEAD_FIXTURE
    root = tmp_path / "head"
    copy_tree_with_databases(head, root)
    allow_below_floor(root)
    with connect(root / "state.sqlite") as connection:
        sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE name = 'grading_clarifications'").fetchone()[0]
        assert "'route_check_disagreement'" in sql
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


# -- Codex review of route-check-in-grader (F1-F4) -----------------------------------------


class OmittingGrader(DivergentGrader):
    """F1: only ``setup`` (0 points) on a divergent route, locating nothing;
    ``result`` is omitted from the criterion evidence."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        evidence = [row for row in result.criterion_evidence if row.criterion_id == "setup"]
        return result.model_copy(update={
            "criterion_evidence": evidence, "error_attributions": [], "rubric_score": 0,
        })


class EmptyGrader(DivergentGrader):
    """F1: no criterion evidence at all on a divergent route."""

    def _blind_grading(self, request, context):
        return super()._blind_grading(request, context).model_copy(update={
            "criterion_evidence": [], "error_attributions": [], "rubric_score": 0,
        })


#: A step of ``ALTERNATIVE``, quoted verbatim.
ALTERNATIVE_STEP = "Take the eigenvectors of A^T A for V"


class UncertainQuotingGrader(DivergentGrader):
    """F2: the grader cannot verify ``setup`` on a divergent route. It says so
    (``unverified_criterion_ids``), quotes the step it cannot verify, and still
    marks it down; ``result`` gets full points."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        evidence = [
            row.model_copy(update={
                "points_awarded": 0.0 if row.criterion_id == "setup" else 2.0,
                "evidence": "I cannot verify this step of the learner's route." if row.criterion_id == "setup"
                else "graded",
            })
            for row in result.criterion_evidence
        ]
        attribution = BlindErrorAttribution(
            error_type="conceptual_slip", evidence="I cannot verify this step.",
            target_criterion_ids=["setup"], validity_scope="valid_measurement",
            first_divergence={"anchor_kind": "span", "criterion_id": "setup", "quote": ALTERNATIVE_STEP},
        )
        return result.model_copy(update={
            "criterion_evidence": evidence, "error_attributions": [attribution],
            "unverified_criterion_ids": ["setup"], "rubric_score": 2,
        })


#: A false claim the learner makes only in a clarification reply.
CLARIFIED_ERROR = "All continuous functions are differentiable."


class ClarifiedErrorGrader(DivergentGrader):
    """F3: on a clarification regrade, ``setup`` is marked down by quoting the
    learner's reply (an error the reply newly reveals); ``result`` full."""

    def __init__(self, quote: str = CLARIFIED_ERROR, **kwargs):
        super().__init__(**kwargs)
        self.quote = quote

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        evidence = [
            row.model_copy(update={"points_awarded": 0.0 if row.criterion_id == "setup" else 2.0})
            for row in result.criterion_evidence
        ]
        attribution = BlindErrorAttribution(
            error_type="conceptual_slip", evidence="The reply states a false claim.",
            target_criterion_ids=["setup"], validity_scope="valid_measurement",
            first_divergence={"anchor_kind": "span", "criterion_id": "setup", "quote": self.quote},
        )
        return result.model_copy(update={
            "criterion_evidence": evidence, "error_attributions": [attribution], "rubric_score": 2,
        })


def _exchange(answer=CLARIFIED_ERROR, question="Why is f differentiable on the interval?"):
    return {"question_md": question, "answer_md": answer, "criterion_id": "setup", "reason": "method_ambiguity"}


def test_f1_an_omitted_criterion_is_unlocated_and_with_nothing_assessed_holds():
    rule = _rule(_proposal({"setup": 0.0}))
    assert rule.applied and rule.unlocated == ("setup", "result")
    assert rule.unverified == ("result", "setup")
    assert rule.held_for_review is True and rule.assessed_shortfall is False
    # Empty output: every criterion omitted.
    empty = _rule(_proposal({}))
    assert empty.unlocated == ("setup", "result") and empty.held_for_review is True
    # An omitted criterion beside one at full points: unassessed, no hold.
    partial = _rule(_proposal({"setup": 2.0}))
    assert partial.unlocated == ("result",) and partial.held_for_review is False
    assert partial.assessed_shortfall is False
    # A located attribution cannot supply a missing criterion grade.
    located = _rule(_proposal({"setup": 0.0}, [_attribution("result", "x squared is positive")]))
    assert located.unlocated == ("setup", "result") and located.held_for_review is True
    assert located.assessed_shortfall is False
    # Off a divergent route the rule does not read the grade at all.
    assert not _rule(_proposal({"setup": 0.0}), divergent=False).applied


@pytest.mark.parametrize("grader", [OmittingGrader, EmptyGrader], ids=["missing_row", "empty_output"])
def test_f1_live_an_incomplete_grade_is_refused(tmp_path, grader):
    _paths, vault, repository = split_vault(tmp_path)
    _first_scheduled_attempt(vault, repository)
    before = _schedule(repository)
    attempts = len(repository.list_all_attempts())
    with pytest.raises(AttemptValidationError, match="criterion evidence"):
        submit(vault, repository, grader(), answer=ALTERNATIVE + " (again)",
               when=CLOCK.now() + timedelta(days=3))
    assert _schedule(repository) == before
    assert len(repository.list_all_attempts()) == attempts


def test_f1_live_an_incomplete_regrade_keeps_an_existing_hold(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    _first_scheduled_attempt(vault, repository)
    before = _schedule(repository)
    held = submit(vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE + " (again)",
                  when=CLOCK.now() + timedelta(days=3))
    for index, grader in enumerate((OmittingGrader(), EmptyGrader())):
        kwargs = dict(runtime=ReadyRuntime(), client=grader, grading_source="ai",
                      clock=FrozenClock(CLOCK.now() + timedelta(days=4 + index)))
        attempt = repository.fetch_practice_attempt(held.attempt_id)
        evidence = repository.fetch_grading_evidence(held.attempt_id, include_superseded=True)
        with pytest.raises(GradingValidationError, match="criterion evidence"):
            regrade_attempt(vault, repository, attempt, **kwargs)
        assert repository.fetch_grading_evidence(held.attempt_id, include_superseded=True) == evidence
        rule = _support(repository, held.attempt_id)["proof_route_check"]
        assert rule["held_for_review"] is True, type(grader).__name__
        attempt = repository.fetch_practice_attempt(held.attempt_id)
        assert attempt["manual_review_reason"] == HELD_REVIEW_REASON
        assert _schedule(repository) == before


# -- a criterion worth no points (adversarial review of arc E, finding 1) ---------------------

#: The review's rubric: ``form`` is worth nothing beside ``setup`` and ``result``.
WEIGHTLESS_RUBRIC = Rubric.model_validate({
    "id": "r", "max_points": 4,
    "criteria": [{"id": "form", "description": "Writes it up", "points": 0},
                 {"id": "setup", "description": "Sets up", "points": 2},
                 {"id": "result", "description": "Concludes", "points": 2}],
})


def _weightless_vault(tmp_path):
    """The split vault with ``form`` (0 points) added to ``ITEM``'s rubric."""

    from learnloop.vault.yaml_io import read_yaml, write_yaml

    paths, _vault, repository = split_vault(tmp_path, seed=False)
    path = paths.practice_item_path("linear-algebra", ITEM)
    item = read_yaml(path)
    criteria = item["grading_rubric"]["criteria"]
    criteria.insert(0, {**criteria[0], "id": "form", "points": 0, "description": "form is right."})
    write_yaml(path, item)
    return load_vault(paths.root), repository


class WeightlessOmittingGrader(DivergentUnlocatedGrader):
    """0 for ``form`` and ``setup`` on a divergent route, ``result`` left out."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        evidence = [row for row in result.criterion_evidence if row.criterion_id != "result"]
        return result.model_copy(update={"criterion_evidence": evidence, "rubric_score": 0})


class WeightedFullCreditGrader(DivergentGrader):
    """Every criterion at its own maximum on a divergent route."""

    def _blind_grading(self, request, context):
        result = super()._blind_grading(request, context)
        maxima = {criterion["id"]: float(criterion["points"]) for criterion in context["rubric"]["criteria"]}
        evidence = [row.model_copy(update={"points_awarded": maxima[row.criterion_id]})
                    for row in result.criterion_evidence]
        return result.model_copy(update={"criterion_evidence": evidence, "rubric_score": 4, "error_attributions": []})


def test_er1_a_grade_that_leaves_out_a_criterion_is_refused(tmp_path):
    vault, repository = _weightless_vault(tmp_path)
    before = repository.practice_item_state(ITEM)
    with pytest.raises(AttemptValidationError, match="criterion evidence"):
        submit(vault, repository, WeightlessOmittingGrader(), answer=ALTERNATIVE, when=SUBMITTED)
    assert repository.list_all_attempts() == []
    assert repository.practice_item_state(ITEM) == before


@pytest.mark.parametrize("door", ["live", "regrade"])
def test_er1_nothing_with_points_assessed_is_held_not_full_marks(tmp_path, door):
    from learnloop.held_grades import attempt_grade_held

    vault, repository = _weightless_vault(tmp_path)
    if door == "live":
        result = submit(vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE, when=SUBMITTED)
    else:
        result = submit(vault, repository, WeightedFullCreditGrader(), answer=ALTERNATIVE, when=SUBMITTED)
        assert repository.fetch_practice_attempt(result.attempt_id)["rubric_score"] == 4
        regrade_attempt(vault, repository, repository.fetch_practice_attempt(result.attempt_id),
                        runtime=ReadyRuntime(), client=DivergentUnlocatedGrader(), grading_source="ai", clock=CLOCK)
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    support = _support(repository, result.attempt_id)
    rule = support["proof_route_check"]
    # ``setup`` and ``result`` were marked down with nothing located; the only
    # criterion left assessed is worth nothing, so nothing was assessed.
    assert rule["held_for_review"] is True
    assert attempt["rubric_score"] == 0 and attempt_grade_held(repository, result.attempt_id)
    rows = repository.fetch_grading_evidence(result.attempt_id)
    marked = {row.criterion_id for row in rows if unassessed_evidence_row(row.attribution_json)}
    # Only the rule's own unverified criteria are shown as not assessed.
    assert marked == set(support["unverified_criterion_ids"]) == set(rule["unverified_criterion_ids"])
    assert {row.criterion_id for row in rows} == {"form", "setup", "result"}


def test_er1_the_rules_treat_a_weightless_remainder_as_nothing_assessed():
    from learnloop.attempts.attempts import assessed_rubric_score
    from learnloop.attempts.grading_support import apply_valid_alternative_gate

    zeros = _proposal({"form": 0.0, "setup": 0.0, "result": 0.0})
    rule = _rule(zeros, rubric=WEIGHTLESS_RUBRIC)
    assert rule.unverified == ("form", "result", "setup") and rule.held_for_review is True
    # A verified final answer: PF-c's nothing-assessed grade (correct for
    # scheduling, no evidence), never an assessed zero-point criterion.
    gate = apply_valid_alternative_gate(
        zeros, rubric=WEIGHTLESS_RUBRIC, learner_answer_md=ANSWER,
        policy={"final_answer_check": {"status": "matches_reference"}},
    )
    assert gate.unverified_criterion_ids == ("form", "result", "setup")
    # A criterion with points still assessed keeps the zero-point one assessed.
    kept = _rule(_proposal({"form": 0.0, "setup": 0.0, "result": 2.0}), rubric=WEIGHTLESS_RUBRIC)
    assert kept.unverified == ("setup",) and kept.held_for_review is False
    points = {"form": 0.0, "setup": 0.0, "result": 0.0}
    # The score over the assessed criteria never divides by zero weight: with
    # nothing validated it is the grader's own, with a verified answer PF-c's.
    for unassessed in (("setup", "result"), ("form", "setup", "result")):
        assert assessed_rubric_score(WEIGHTLESS_RUBRIC, points, [], unassessed_criterion_ids=unassessed,
                                     answer_validated=False) == 0
        assert assessed_rubric_score(WEIGHTLESS_RUBRIC, points, [], unassessed_criterion_ids=unassessed,
                                     answer_validated=True) == 4


def test_f2_a_criterion_the_grader_declares_unverified_is_unassessed_on_a_divergent_route():
    """The grader's own "I cannot verify this" outranks its quote: PF-c reads
    it only on a verified final answer, so the rule reads it on a divergent
    route, quoted or not."""

    quoted = _rule(_proposal({"setup": 0.0, "result": 2.0}, [_attribution("setup", "Let x be fixed")]),
                   declared=("setup",))
    assert quoted.applied and quoted.declared == ("setup",) and quoted.unlocated == ()
    assert quoted.unverified == ("setup",) and quoted.assessed_shortfall is False
    assert [row.validity_scope for row in quoted.proposal.error_attributions] == ["grader_interpretation"]
    setup = {row.criterion_id: row for row in quoted.proposal.criterion_evidence}["setup"]
    assert setup.notes.startswith("Not assessed")
    unquoted = _rule(_proposal({"setup": 0.0, "result": 2.0}), declared=("setup",))
    assert unquoted.unverified == ("setup",) and unquoted.assessed_shortfall is False
    # Declared everywhere and nothing validated: held.
    everything = _rule(_proposal({"setup": 0.0, "result": 0.0}, [_attribution("setup", "Let x be fixed"),
                                                              _attribution("result", "So the claim holds")]),
                       declared=("setup", "result"))
    assert everything.held_for_review is True
    # The documented exceptions stand: a differing conclusion, a fatal error,
    # a criterion at full points, an unknown id, a route that is not divergent.
    differs = _rule(_proposal({"setup": 0.0, "result": 2.0}), final="differs_from_reference", declared=("setup",))
    assert not differs.applied and differs.unverified == ()
    rubric = Rubric.model_validate({
        **RUBRIC.model_dump(mode="json"),
        "fatal_errors": [{"id": "wrong_statement", "description": "proves the wrong claim", "max_grade": 0}],
    })
    fatal = _rule(_proposal({"setup": 0.0, "result": 0.0}, fatal=["wrong_statement"]), rubric=rubric,
                  declared=("setup",))
    assert not fatal.applied and fatal.unverified == ()
    full = _rule(_proposal({"setup": 2.0, "result": 2.0}), declared=("setup", "nope"))
    assert not full.applied and full.unverified == ()
    straight = _rule(_proposal({"setup": 0.0, "result": 2.0}, [_attribution("setup", "Let x be fixed")]),
                     divergent=False, declared=("setup",))
    assert not straight.applied and straight.unverified == ()


def test_f2_live_declared_uncertainty_on_a_quoted_step_is_unassessed(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    result = submit(vault, repository, UncertainQuotingGrader(), answer=ALTERNATIVE)
    support = _support(repository, result.attempt_id)
    rule = support["proof_route_check"]
    assert support["grader_unverified_criterion_ids"] == ["setup"]
    assert rule["applied"] is True and rule["declared_unverified_criterion_ids"] == ["setup"]
    assert support["unverified_criterion_ids"] == ["setup"]
    rows = {row.criterion_id: row for row in repository.fetch_grading_evidence(result.attempt_id)}
    assert unassessed_evidence_row(rows["setup"].attribution_json)
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    # Only ``result`` is assessed, at full points.
    assert (attempt["rubric_score"], attempt["correctness"]) == (4, 1.0)
    assert support["assessed_shortfall"] is False


def test_f3_a_quote_from_the_learners_clarification_reply_locates_an_error():
    """The learner's reply is the learner's words; the machine's question is not."""

    proposal = _proposal({"setup": 0.0, "result": 2.0}, [_attribution("setup", CLARIFIED_ERROR)])
    replied = _rule(proposal, clarification=CLARIFIED_ERROR)
    assert not replied.applied and replied.unverified == () and replied.assessed_shortfall is True
    assert replied.clarification_located == ("setup",)
    assert replied.proposal.error_attributions[0].validity_scope == "valid_measurement"
    # Without the reply the same quote is fabricated.
    assert _rule(proposal).unlocated == ("setup",)
    # A quote of the question locates nothing.
    question = "Is every continuous function differentiable?"
    asked = _rule(_proposal({"setup": 0.0, "result": 2.0}, [_attribution("setup", question)]),
                  clarification=CLARIFIED_ERROR)
    assert asked.unlocated == ("setup",) and asked.clarification_located == ()


def test_f3_live_a_clarification_regrade_keeps_an_error_the_reply_reveals(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    result = submit(vault, repository, FullCreditGrader(), answer=ALTERNATIVE, when=SUBMITTED)
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(result.attempt_id),
                    runtime=ReadyRuntime(), client=ClarifiedErrorGrader(), grading_source="ai",
                    clock=CLOCK, clarification_exchange=_exchange())
    support = _support(repository, result.attempt_id)
    rule = support["proof_route_check"]
    assert rule["applied"] is False and rule["clarification_located_criterion_ids"] == ["setup"]
    assert support["unverified_criterion_ids"] == []
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    assert attempt["rubric_score"] == 2
    rows = {row.criterion_id: row for row in repository.fetch_grading_evidence(result.attempt_id)}
    assert not unassessed_evidence_row(rows["setup"].attribution_json)
    # The machine's question is not learner evidence.
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(result.attempt_id),
                    runtime=ReadyRuntime(), client=ClarifiedErrorGrader(quote="Why is f differentiable"),
                    grading_source="ai", clock=FrozenClock(CLOCK.now() + timedelta(days=1)),
                    clarification_exchange=_exchange())
    rule = _support(repository, result.attempt_id)["proof_route_check"]
    assert rule["unlocated_criterion_ids"] == ["setup"]


def _route_judgments(repository, attempt_id):
    with connect(repository.sqlite_path, read_only=True) as connection:
        return [
            dict(zip(("id", "supersedes_id", "judge", "judge_model", "prompt_version", "input_hash", "verdict"), row, strict=True))
            for row in connection.execute(
                "SELECT id, supersedes_id, judge, judge_model, prompt_version, input_hash, verdict "
                "FROM judgment_ledger WHERE task = 'own_route_rule' AND left_kind = 'attempt' "
                "AND left_id = ? ORDER BY created_at, rowid", (attempt_id,),
            )
        ]


def test_f4_the_graders_route_verdict_reaches_the_judgment_ledger_and_regrades_supersede_it(tmp_path):
    _paths, vault, repository = split_vault(tmp_path)
    result = submit(vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE, when=SUBMITTED)
    blind = repository.latest_blind_grade_record(result.attempt_id)
    [first] = _route_judgments(repository, result.attempt_id)
    assert first["judge"] == "llm" and first["judge_model"] == "fake-model"
    assert first["prompt_version"] == blind["grading_prompt_version"]
    assert first["prompt_version"].endswith(METHOD_ROUTE_RULES_SUFFIX)
    assert first["input_hash"] == blind["context_hash"] and first["supersedes_id"] is None
    verdict = json.loads(first["verdict"])
    assert verdict["divergent_route"] is True and verdict["held_for_review"] is True
    assert sorted(verdict["unlocated_criterion_ids"]) == ["result", "setup"]
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(result.attempt_id),
                    runtime=ReadyRuntime(), client=FullCreditGrader(), grading_source="ai", clock=CLOCK)
    first_again, second = _route_judgments(repository, result.attempt_id)
    assert first_again == first and second["supersedes_id"] == first["id"]
    assert json.loads(second["verdict"])["held_for_review"] is False
    # Replay writes no verdict.
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert len(_route_judgments(repository, result.attempt_id)) == 2


def test_f4_no_route_verdict_without_the_rules(tmp_path):
    _paths, vault, repository = split_vault(tmp_path, config=NO_POLICY)
    result = submit(vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE)
    assert _route_judgments(repository, result.attempt_id) == []


# -- review F5: a regrade the rule did not run over supersedes the verdict ---------------


def _judgments(repository, attempt_id, task):
    with connect(repository.sqlite_path, read_only=True) as connection:
        return [
            dict(zip(("id", "supersedes_id", "judge", "judge_model", "prompt_version", "input_hash", "verdict"), row, strict=True))
            for row in connection.execute(
                "SELECT id, supersedes_id, judge, judge_model, prompt_version, input_hash, verdict "
                "FROM judgment_ledger WHERE task = ? AND left_kind = 'attempt' "
                "AND left_id = ? ORDER BY rowid", (task, attempt_id),
            )
        ]


def _current(rows):
    superseded = {row["supersedes_id"] for row in rows}
    return [row for row in rows if row["id"] not in superseded]


def _latest_regrade_run(repository):
    with connect(repository.sqlite_path, read_only=True) as connection:
        return connection.execute(
            "SELECT prompt_version, input_context_hash FROM agent_runs WHERE purpose = 'grading_regrade' "
            "ORDER BY started_at DESC, id DESC LIMIT 1"
        ).fetchone()


def test_f5_a_regrade_without_the_rules_supersedes_the_held_verdict(tmp_path):
    paths, vault, repository = split_vault(tmp_path)
    held = submit(vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE, when=SUBMITTED)
    [first] = _route_judgments(repository, held.attempt_id)
    assert json.loads(first["verdict"])["held_for_review"] is True
    append_config(paths.root, NO_POLICY)
    vault = load_vault(paths.root)
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(held.attempt_id),
                    runtime=ReadyRuntime(), client=FullCreditGrader(), grading_source="ai",
                    clock=FrozenClock(CLOCK.now() + timedelta(days=1)))
    blind = repository.latest_blind_grade_record(held.attempt_id)
    assert "proof_route_check" not in blind["record"]["grading_support"]
    first_again, second = _route_judgments(repository, held.attempt_id)
    assert first_again == first and second["supersedes_id"] == first["id"]
    # The current verdict describes the grade that replaced the held one.
    assert json.loads(second["verdict"]) == {"status": "not_checked"}
    assert (second["judge"], second["judge_model"]) == ("llm", "fake-model")
    assert second["prompt_version"] == blind["grading_prompt_version"]
    assert second["input_hash"] == blind["context_hash"]
    assert _current(_route_judgments(repository, held.attempt_id)) == [second]
    # Each later grade restates it, so the current verdict carries the
    # identity of the current grade.
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(held.attempt_id),
                    runtime=ReadyRuntime(), client=FullCreditGrader(), grading_source="ai",
                    clock=FrozenClock(CLOCK.now() + timedelta(days=2)))
    rows = _route_judgments(repository, held.attempt_id)
    assert len(rows) == 3 and rows[2]["supersedes_id"] == second["id"]
    assert json.loads(rows[2]["verdict"]) == {"status": "not_checked"}
    assert rows[2]["input_hash"] == repository.latest_blind_grade_record(held.attempt_id)["context_hash"]
    # Replay writes none.
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert len(_route_judgments(repository, held.attempt_id)) == 3


MVP017_FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mvp017_route_check_replay"


def test_f5_a_regrade_supersedes_an_mvp017_route_check_verdict(tmp_path):
    """mvp-0.17's check wrote the attempt's route verdict under task
    ``proof_route_check`` and superseded it on each checked regrade. Nothing
    writes that task now, so any regrade of such an attempt supersedes it as
    not checked, and writes the rules' own verdict beside it."""
    from learnloop.db.copies import copy_tree_with_databases
    from learnloop.ops.upgrades import rewrite_algorithm_version
    from learnloop.vault.repository import open_vault_repository

    expected = json.loads((MVP017_FIXTURE / "expected.json").read_text(encoding="utf-8"))["attempts"]
    root = tmp_path / "vault"
    copy_tree_with_databases(MVP017_FIXTURE, root)
    allow_below_floor(root)
    vault, repository = load_vault(root), open_vault_repository(root, root / "state.sqlite")
    held, restored = expected["held"]["attempt_id"], expected["restored_both"]["attempt_id"]
    later = FrozenClock(CLOCK.now() + timedelta(days=60))  # after every fixture grade
    [legacy] = _judgments(repository, held, "proof_route_check")
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(held),
                    runtime=ReadyRuntime(), client=FullCreditGrader(), grading_source="ai", clock=later)
    legacy_again, superseding = _judgments(repository, held, "proof_route_check")
    assert legacy_again == legacy and superseding["supersedes_id"] == legacy["id"]
    assert json.loads(superseding["verdict"]) == {"status": "not_checked"}
    assert superseding["input_hash"] == repository.latest_blind_grade_record(held)["context_hash"]
    # The rules run on every vault that opens (the fixture's own tag included).
    [ruled_held] = _route_judgments(repository, held)
    assert json.loads(ruled_held["verdict"])["status"] == "checked" and ruled_held["supersedes_id"] is None
    # At the successor the regrade's own verdict is written, and the old one superseded.
    rewrite_algorithm_version(root / "learnloop.toml", "mvp-0.17", "mvp-0.20")
    vault = load_vault(root)
    [legacy] = _judgments(repository, restored, "proof_route_check")
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(restored),
                    runtime=ReadyRuntime(), client=FullCreditGrader(), grading_source="ai", clock=later)
    assert [row["supersedes_id"] for row in _judgments(repository, restored, "proof_route_check")] == [
        None, legacy["id"]
    ]
    [ruled] = _route_judgments(repository, restored)
    assert json.loads(ruled["verdict"])["status"] == "checked" and ruled["supersedes_id"] is None
