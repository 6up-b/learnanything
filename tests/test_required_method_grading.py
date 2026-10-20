"""Required methods in the grader (method-explicit successor ``mvp-0.25``).

Owner rule 2026-10-13: rubric criteria name the fact a step establishes, not
the method; an item whose target IS a method states it ("Use {method} in your
answer.") and records it as ``PracticeItem.required_method``. The own-route
rules gain the required method (``own-route-v2``):

* a criterion tied to the item's required method is graded on USE of that
  method: on a route the grader reads as divergent, its mark-down needs no
  quoted wrong step (the route is the evidence) and is never unassessed by
  PF-c's gate or the unlocated-mark-down rule (the grader's own "cannot
  verify" still unassesses it);
* every other criterion keeps mvp-0.20's rules (any valid method; a
  mark-down needs a verbatim quote).

Kill switch ``required_method.enabled``: off, new answers grade exactly as
the immediate predecessor (mvp-0.24, whose grading keeps mvp-0.20's own-route
rules). Replay reads every record as written. Fakes only; no network.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from learnloop.algorithm_versions import (
    LATEST_ALGORITHM_VERSION,
    METHOD_EXPLICIT_ALGORITHM_VERSION,
    METHOD_EXPLICIT_VERSIONS,
    ROUTER_MIXTURE_ALGORITHM_VERSION,
)
from learnloop.attempts.ai_contracts import CriterionEvidence
from learnloop.attempts.blind_grading import BlindErrorAttribution, BlindGradingProposal, blind_grading_prompt
from learnloop.attempts.grading_support import (
    METHOD_ROUTE_RULES_SUFFIX,
    REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION,
    REQUIRED_METHOD_RULES,
    ROUTE_RULES,
    ROUTE_RULES_SUFFIX,
    ROUTE_RULES_V2,
    apply_route_rule,
    apply_valid_alternative_gate,
    method_rules_active,
    route_rules_active,
)
from learnloop.attempts.regrade import regrade_attempt
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.diagnosis.split.jobs import diagnosis_status
from learnloop.substrate.canonical_projection import project_canonical_facet_state, unassessed_evidence_row
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault
from learnloop.vault.models import Rubric

from tests.split_live_helpers import ReadyRuntime, split_vault, submit
from tests.test_route_rules_in_grader import ALTERNATIVE, DivergentGrader, FullCreditGrader

VERSION = METHOD_EXPLICIT_ALGORITHM_VERSION
#: The immediate predecessor: its grading is mvp-0.20's own-route rules.
PREDECESSOR = ROUTER_MIXTURE_ALGORITHM_VERSION
ITEM = "pi_svd_compute_001"  # setup (2) + result (2); its LO's concept (SVD) is a procedure
METHOD = "singular value decomposition"
CLOCK = FrozenClock(datetime(2026, 11, 1, 12, 0, tzinfo=UTC))
KILL_SWITCH = "[required_method]\nenabled = false"


def _require_method(paths, item_id: str = ITEM, criterion_ids=("setup",)) -> None:
    """Make ``item_id`` a method item: the required method (round 3: its
    instruction is rendered from the field, the statement is unchanged)."""

    path = paths.practice_item_path("linear-algebra", item_id)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["required_method"] = {"name": METHOD, "criterion_ids": list(criterion_ids),
                               "learning_object_id": data["learning_object_id"]}
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _method_vault(tmp_path, *, version=VERSION, config="", seed=True):
    paths, _vault, repository = split_vault(tmp_path, version=version, config=config, seed=seed)
    _require_method(paths)
    return paths, load_vault(paths.root), repository


def _support(repository, attempt_id):
    return repository.latest_blind_grade_record(attempt_id)["record"]["grading_support"]


# -- the version and the switch ---------------------------------------------------------


def test_the_method_explicit_successor_is_the_latest_after_the_route_rules():
    # Regrade contracts (mvp-0.26) followed it and keep it.
    assert VERSION == "mvp-0.25"
    assert LATEST_ALGORITHM_VERSION == "mvp-0.29"
    assert PREDECESSOR == "mvp-0.24"
    assert METHOD_EXPLICIT_VERSIONS == frozenset({VERSION, "mvp-0.26", "mvp-0.27", LATEST_ALGORITHM_VERSION})


def test_active_only_at_the_successor_with_both_switches_on(tmp_path):
    _paths, vault, _repository = split_vault(tmp_path / "on", version=VERSION, seed=False)
    assert method_rules_active(vault) and route_rules_active(vault)
    _paths, older, _repository = split_vault(tmp_path / "older", version=PREDECESSOR, seed=False)
    assert route_rules_active(older) and not method_rules_active(older)
    _paths, off, _repository = split_vault(tmp_path / "off", version=VERSION, config=KILL_SWITCH, seed=False)
    assert route_rules_active(off) and not method_rules_active(off)
    # The required-method rules extend the own-route rules: off with them.
    _paths, rules_off, _repository = split_vault(
        tmp_path / "rules_off", version=VERSION, config="[proof_check]\nenabled = false", seed=False,
    )
    assert not route_rules_active(rules_off) and not method_rules_active(rules_off)


# -- the deterministic rules (pure) ------------------------------------------------------

RUBRIC = Rubric.model_validate({
    "id": "r", "max_points": 4,
    "criteria": [{"id": "method", "description": "Uses cofactor expansion", "points": 2},
                 {"id": "result", "description": "Establishes det(A) = 13", "points": 2}],
})
ANSWER = "Row reduce: R3 <- R3 - 2 R1, then the triangular product is 13. det(A) = 13"


def _proposal(points, attributions=()):
    return BlindGradingProposal(
        local_analysis_md="a", attempt_id="a1", practice_item_id="i",
        criterion_evidence=[CriterionEvidence(criterion_id=cid, points_awarded=p, evidence=f"grader on {cid}")
                            for cid, p in points.items()],
        rubric_score=int(sum(points.values())), error_attributions=list(attributions), grader_confidence=0.9,
    )


def _rule(proposal, *, final="undecidable", divergent=True, before=(), method=("method",), declared=()):
    return apply_route_rule(
        proposal, rubric=RUBRIC, learner_answer_md=ANSWER, final_answer_status=final,
        divergent_route=divergent, unverified_before=before, declared_unverified=declared,
        method_criterion_ids=method,
    )


def test_a_required_method_criterion_fails_on_another_route_without_a_quote():
    """The route is the evidence: an unquoted mark-down of the method
    criterion on a divergent route stays assessed; any other unquoted
    mark-down is still unassessed (P1)."""

    rule = _rule(_proposal({"method": 0.0, "result": 2.0}))
    assert not rule.applied and rule.unverified == () and rule.method_route == ("method",)
    assert rule.assessed_shortfall is True and rule.held_for_review is False
    both = _rule(_proposal({"method": 0.0, "result": 0.0}))
    assert both.applied and both.unlocated == ("result",) and both.method_route == ("method",)
    # Something assessed (the method criterion): no hold, a real shortfall.
    assert both.held_for_review is False and both.assessed_shortfall is True
    rows = {row.criterion_id: row for row in both.proposal.criterion_evidence}
    assert rows["result"].notes.startswith("Not assessed") and rows["method"].notes is None
    # Without the required method (mvp-0.20's rules) the same mark-down is unassessed.
    plain = _rule(_proposal({"method": 0.0, "result": 2.0}), method=())
    assert plain.applied and plain.unlocated == ("method",) and plain.method_route == ()


def test_the_graders_declared_uncertainty_still_unassesses_a_method_criterion():
    rule = _rule(_proposal({"method": 0.0, "result": 2.0}), declared=("method",))
    assert rule.applied and rule.declared == ("method",) and rule.method_route == ()
    assert rule.unverified == ("method",)


def test_a_route_read_as_the_references_leaves_the_method_criterion_to_the_ordinary_rules():
    rule = _rule(_proposal({"method": 0.0, "result": 2.0}), divergent=False)
    assert not rule.applied and rule.method_route == () and rule.assessed_shortfall is True


def test_pfc_gate_never_unassesses_a_method_criterion_on_a_divergent_route():
    """On a verified final answer PF-c unassesses unlocated mark-downs; a
    required method's criterion (passed only on a divergent route) is exempt,
    unless the grader itself declared it unverifiable."""

    policy = {"final_answer_check": {"status": "matches_reference"}}
    proposal = _proposal({"method": 0.0, "result": 0.0})
    exempt = apply_valid_alternative_gate(proposal, rubric=RUBRIC, learner_answer_md=ANSWER, policy=policy,
                                          method_criterion_ids=("method",))
    assert exempt.unverified_criterion_ids == ("result",) and exempt.assessed_shortfall is True
    plain = apply_valid_alternative_gate(proposal, rubric=RUBRIC, learner_answer_md=ANSWER, policy=policy)
    assert plain.unverified_criterion_ids == ("method", "result") and plain.assessed_shortfall is False
    declared = apply_valid_alternative_gate(proposal, rubric=RUBRIC, learner_answer_md=ANSWER, policy=policy,
                                            method_criterion_ids=("method",), declared_unverified=("method",))
    assert declared.unverified_criterion_ids == ("method", "result")


def test_a_quoted_wrong_step_in_the_method_still_counts():
    attribution = BlindErrorAttribution(
        error_type="conceptual_slip", evidence="e", target_criterion_ids=["method"],
        first_divergence={"anchor_kind": "span", "criterion_id": "method", "quote": "R3 <- R3 - 2 R1"},
        validity_scope="valid_measurement",
    )
    rule = _rule(_proposal({"method": 0.0, "result": 2.0}, [attribution]))
    # Located: an ordinary assessed mark-down, not a route-only one.
    assert rule.method_route == () and not rule.applied


# -- the prompt and its identity -----------------------------------------------------------


def _blind_plan(vault, answer=ALTERNATIVE, *, stuck=False, item_id=ITEM):
    from learnloop.attempts.attempts import _blind_grading_plan
    from learnloop.attempts.grading import build_grading_context, resolved_rubric

    item = vault.practice_items[item_id]
    context = build_grading_context(
        vault, item, attempt_id="planned", learner_answer_md=answer, rubric=resolved_rubric(vault, item),
    )
    return _blind_grading_plan(vault, item, context, stuck=stuck)


def test_the_prompt_carries_the_required_method_and_names_v2(tmp_path):
    _paths, vault, _repository = _method_vault(tmp_path / "on", seed=False)
    plan = _blind_plan(vault)
    policy = plan.context.reference_policy
    assert policy["route_rules"] == "own-route-v2"
    assert policy["required_method"] == {"name": METHOD, "criterion_ids": ["setup"]}
    prompt = blind_grading_prompt(plan.context)
    assert ROUTE_RULES_V2 in prompt and REQUIRED_METHOD_RULES in prompt and ROUTE_RULES in prompt
    assert plan.prompt_version == f"mvp-2.1-blind-reference-policy{METHOD_ROUTE_RULES_SUFFIX}"
    assert plan.calibration_prompt_version == f"{REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION}{METHOD_ROUTE_RULES_SUFFIX}"
    stuck = _blind_plan(vault, stuck=True)
    assert stuck.prompt_version == f"mvp-2.1-blind-reference-policy{METHOD_ROUTE_RULES_SUFFIX}+stuck-v1"
    # An item without a required method: the v2 rules, no required method shown.
    other = _blind_plan(vault, item_id="pi_svd_compute_002")
    assert other.context.reference_policy["route_rules"] == "own-route-v2"
    assert "required_method" not in other.context.reference_policy
    assert other.prompt_version.endswith(METHOD_ROUTE_RULES_SUFFIX)


def test_the_grader_reads_the_frozen_field_never_the_answered_statement(tmp_path):
    """Redesign 2026-10-14: the plan shows exactly the method the answer's
    contract froze, whatever the statement it answered says. A contract that
    froze none shows none (even though the statement names the method and
    the item has one now); one that froze it shows it (even though the
    answered statement lacks the sentence)."""

    from learnloop.attempts.attempts import _blind_grading_plan
    from learnloop.attempts.grading import build_grading_context, resolved_rubric

    _paths, vault, _repository = _method_vault(tmp_path, seed=False)
    item = vault.practice_items[ITEM]

    def plan(prompt, required_method):
        context = build_grading_context(
            vault, item, attempt_id="planned", learner_answer_md=ALTERNATIVE, rubric=resolved_rubric(vault, item),
            assessment_contract={"prompt": prompt, "expected_answer": item.expected_answer},
        )
        return _blind_grading_plan(vault, item, context, required_method=required_method).context.reference_policy

    unfrozen = plan(f"Write the SVD of A. Use {METHOD} in your answer.", None)
    assert unfrozen["route_rules"] == "own-route-v2" and "required_method" not in unfrozen
    frozen = plan("Write the SVD of A.", {"name": METHOD, "criterion_ids": ["setup"]})
    assert frozen["required_method"] == {"name": METHOD, "criterion_ids": ["setup"]}


@pytest.mark.parametrize("setup", ["kill_switch", "predecessor"])
def test_off_and_at_the_predecessor_the_prompt_is_the_predecessors_byte_for_byte(tmp_path, setup):
    """The kill switch (and mvp-0.24 itself) shows the own-route-v1 rules and
    no required method, even on a method item: the same prompt, context hash
    and identity as an mvp-0.24 vault (mvp-0.20's rules)."""

    if setup == "kill_switch":
        _paths, vault, _repository = _method_vault(tmp_path / "a", config=KILL_SWITCH, seed=False)
    else:
        _paths, vault, _repository = _method_vault(tmp_path / "a", version=PREDECESSOR, seed=False)
    _paths, baseline, _repository = _method_vault(tmp_path / "b", version=PREDECESSOR, seed=False)
    plan, reference = _blind_plan(vault), _blind_plan(baseline)
    assert plan.context.reference_policy["route_rules"] == "own-route-v1"
    assert "required_method" not in plan.context.reference_policy
    assert blind_grading_prompt(plan.context) == blind_grading_prompt(reference.context)
    assert REQUIRED_METHOD_RULES not in blind_grading_prompt(plan.context)
    assert (plan.prompt_version, plan.context_hash, plan.calibration_prompt_version) == (
        reference.prompt_version, reference.context_hash, reference.calibration_prompt_version)
    assert plan.prompt_version.endswith(ROUTE_RULES_SUFFIX)


# -- live grades -----------------------------------------------------------------------------


def test_live_another_route_fails_the_method_criterion_with_no_quote(tmp_path):
    """Gold-set case (a) through the real door: the method criterion
    (``setup``) is marked down on a divergent route with nothing quoted; at the
    successor it stays assessed (failed), recorded on the blind record and in
    the route verdict, and the attempt is a measured shortfall."""

    _paths, vault, repository = _method_vault(tmp_path)
    result = submit(vault, repository, DivergentGrader(), answer=ALTERNATIVE)
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    support = _support(repository, result.attempt_id)
    rule = support["proof_route_check"]
    assert rule["rules"] == "own-route-v2" and rule["divergent_route"] is True
    assert rule["required_method"] == {"name": METHOD, "criterion_ids": ["setup"]}
    assert rule["method_route_criterion_ids"] == ["setup"]
    assert rule["applied"] is False and rule["unlocated_criterion_ids"] == []
    rows = {row.criterion_id: row for row in repository.fetch_grading_evidence(result.attempt_id)}
    assert not unassessed_evidence_row(rows["setup"].attribution_json)
    assert not unassessed_evidence_row(rows["result"].attribution_json)
    assert (attempt["rubric_score"], attempt["correctness"]) == (0, 0.0)
    assert support["unverified_criterion_ids"] == []
    with connect(repository.sqlite_path, read_only=True) as connection:
        [verdict] = [json.loads(row[0]) for row in connection.execute(
            "SELECT verdict FROM judgment_ledger WHERE task = 'own_route_rule' AND left_id = ?",
            (result.attempt_id,))]
    assert verdict["method_route_criterion_ids"] == ["setup"] and verdict["rules"] == "own-route-v2"
    assert diagnosis_status(repository, result.attempt_id)["status"] != "not_needed"


def test_live_the_same_mathematics_without_a_required_method_keeps_mvp020s_rule(tmp_path):
    """Gold-set case (b): the same item and answer without a required method:
    the unquoted mark-down is unassessed (any valid method passes)."""

    _paths, vault, repository = split_vault(tmp_path, version=VERSION)
    result = submit(vault, repository, DivergentGrader(), answer=ALTERNATIVE)
    rule = _support(repository, result.attempt_id)["proof_route_check"]
    assert rule["rules"] == "own-route-v2" and "required_method" not in rule
    assert rule["unlocated_criterion_ids"] == ["setup"]
    rows = {row.criterion_id: row for row in repository.fetch_grading_evidence(result.attempt_id)}
    assert unassessed_evidence_row(rows["setup"].attribution_json)


@pytest.mark.parametrize("setup", ["kill_switch", "predecessor"])
def test_the_kill_switch_grades_exactly_as_the_predecessor(tmp_path, setup):
    """Off (and at mvp-0.24) the method item grades as mvp-0.24 does: the same
    columns, evidence rows, record, prompt and identity."""

    if setup == "kill_switch":
        _paths, vault, repository = _method_vault(tmp_path / "a", config=KILL_SWITCH)
    else:
        _paths, vault, repository = _method_vault(tmp_path / "a", version=PREDECESSOR)
    _paths, baseline, baseline_repository = _method_vault(tmp_path / "b", version=PREDECESSOR)
    grader, reference_grader = DivergentGrader(), DivergentGrader()
    result = submit(vault, repository, grader, answer=ALTERNATIVE, when=CLOCK.now())
    reference = submit(baseline, baseline_repository, reference_grader, answer=ALTERNATIVE, when=CLOCK.now())
    assert grader.calls == reference_grader.calls == ["blind_grading"]
    # The same prompt, attempt ids aside.
    assert grader.prompts[0].replace(result.attempt_id, "ATTEMPT") == reference_grader.prompts[0].replace(
        reference.attempt_id, "ATTEMPT")
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    expected = baseline_repository.fetch_practice_attempt(reference.attempt_id)
    for column in ("rubric_score", "correctness", "manual_review_reason", "error_type"):
        assert attempt[column] == expected[column], column
    rows = [(r.criterion_id, r.points_awarded, r.attribution_json) for r in repository.fetch_grading_evidence(result.attempt_id)]
    ref = [(r.criterion_id, r.points_awarded, r.attribution_json)
           for r in baseline_repository.fetch_grading_evidence(reference.attempt_id)]
    assert rows == ref
    record = repository.latest_blind_grade_record(result.attempt_id)["record"]
    ref_record = baseline_repository.latest_blind_grade_record(reference.attempt_id)["record"]
    assert record["grading_support"] == ref_record["grading_support"]
    assert record["calibration_prompt_version"] == ref_record["calibration_prompt_version"] == (
        f"{REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION}{ROUTE_RULES_SUFFIX}")
    # The predecessor's (mvp-0.20's rules) outcome: the method criterion's
    # unquoted mark-down is unassessed.
    assert record["grading_support"]["proof_route_check"]["unlocated_criterion_ids"] == ["setup"]


def test_a_regrade_at_the_successor_keeps_the_method_rule_and_a_full_credit_regrade_clears_it(tmp_path):
    _paths, vault, repository = _method_vault(tmp_path)
    result = submit(vault, repository, DivergentGrader(), answer=ALTERNATIVE)
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(result.attempt_id),
                    runtime=ReadyRuntime(), client=DivergentGrader(), grading_source="ai", clock=CLOCK)
    rule = _support(repository, result.attempt_id)["proof_route_check"]
    assert rule["method_route_criterion_ids"] == ["setup"]
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(result.attempt_id),
                    runtime=ReadyRuntime(), client=FullCreditGrader(), grading_source="ai", clock=CLOCK)
    assert repository.fetch_practice_attempt(result.attempt_id)["rubric_score"] == 4
    assert _support(repository, result.attempt_id)["proof_route_check"]["method_route_criterion_ids"] == []


def _projection(repository):
    return sorted(
        (cell.facet_id, cell.capability, round(cell.direct_positive_mass, 12),
         round(cell.direct_negative_mass, 12), round(cell.certification_credit, 12))
        for cell in repository.facet_capability_evidence_all()
    )


def test_replay_reproduces_method_grades_without_a_model(tmp_path, monkeypatch):
    _paths, vault, repository = _method_vault(tmp_path)
    submit(vault, repository, DivergentGrader(), answer=ALTERNATIVE)
    submit(vault, repository, FullCreditGrader(), answer=ALTERNATIVE + " (full)")
    project_canonical_facet_state(vault, repository)
    before = _projection(repository)
    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task",
                        lambda *a, **k: pytest.fail("replay must not build a client"))
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    first = _projection(repository)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert first == _projection(repository) == before


def test_grades_recorded_at_the_predecessor_replay_unchanged_after_the_upgrade(tmp_path):
    """Existing grades keep their meaning: an mvp-0.24 grade of a method item
    (the method criterion unassessed) replays identically after the vault is
    upgraded to the successor; nothing is regraded or rewritten."""

    from learnloop.method_explicit_upgrade import upgrade_to_method_explicit

    paths, vault, repository = _method_vault(tmp_path, version=PREDECESSOR)
    result = submit(vault, repository, DivergentGrader(), answer=ALTERNATIVE)
    project_canonical_facet_state(vault, repository)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    before = _projection(repository)
    with connect(repository.sqlite_path, read_only=True) as connection:
        tables = {table: connection.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()
                  for table in ("practice_attempts", "grading_evidence", "blind_grade_records", "judgment_ledger")}
    upgraded = upgrade_to_method_explicit(paths.root, clock=CLOCK)
    assert upgraded.upgraded, upgraded.problems
    vault = load_vault(paths.root)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert _projection(repository) == before
    with connect(repository.sqlite_path, read_only=True) as connection:
        for table, rows in tables.items():
            assert connection.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall() == rows, table
    rows = {row.criterion_id: row for row in repository.fetch_grading_evidence(result.attempt_id)}
    assert unassessed_evidence_row(rows["setup"].attribution_json)


# -- review F1: the required method is frozen with the assessment contract -------------------


def _set_required_method(paths, criterion_ids, item_id: str = ITEM, prompt: str | None = None) -> None:
    """An accepted repair: only the item's ``required_method`` (and, given, its prompt) change."""

    path = paths.practice_item_path("linear-algebra", item_id)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["required_method"] = {"name": METHOD, "criterion_ids": list(criterion_ids),
                               "learning_object_id": data["learning_object_id"]}
    if prompt is not None:
        data["prompt"] = prompt
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _present(vault, repository, item_id: str = ITEM) -> str:
    from learnloop.learner.assessment_contracts import snapshot_for_presentation

    return snapshot_for_presentation(repository, vault, vault.practice_items[item_id], clock=CLOCK)


def _submit_presented(vault, repository, client, version_id: str, answer: str = ALTERNATIVE):
    from learnloop.attempts.attempts import AttemptDraft, complete_attempt_with_ai_required

    draft = AttemptDraft(practice_item_id=ITEM, learner_answer_md=answer, attempt_type="independent_attempt",
                         assessment_contract_version_id=version_id)
    return complete_attempt_with_ai_required(vault, repository, draft, runtime=ReadyRuntime(), ai_client=client)


def test_the_contract_snapshots_the_required_method_and_its_hash_moves_with_it(tmp_path):
    from learnloop.learner.assessment_contracts import compile_assessment_contract, contract_hash

    _paths, vault, _repository = _method_vault(tmp_path, seed=False)
    item = vault.practice_items[ITEM]
    contract = compile_assessment_contract(vault, item)
    assert contract["required_method"] == {"name": METHOD, "criterion_ids": ["setup"]}
    widened = item.model_copy(update={
        "required_method": item.required_method.model_copy(update={"criterion_ids": ["setup", "result"]})})
    # Changing only the required method is a new contract.
    assert contract_hash(compile_assessment_contract(vault, widened)) != contract_hash(contract)
    # An item without one snapshots exactly as before: no key at all.
    assert "required_method" not in compile_assessment_contract(vault, vault.practice_items["pi_svd_compute_002"])


def test_a_submission_is_graded_under_the_presented_contracts_required_method(tmp_path):
    """Presented with the method on ``setup``; an accepted repair then widens it
    to ``result`` too, prompt unchanged. The answer is graded under the
    snapshot it was presented with."""

    paths, vault, repository = _method_vault(tmp_path)
    version_id = _present(vault, repository)
    _set_required_method(paths, ("setup", "result"))
    vault = load_vault(paths.root)
    result = _submit_presented(vault, repository, DivergentGrader(), version_id)
    rule = _support(repository, result.attempt_id)["proof_route_check"]
    assert rule["required_method"] == {"name": METHOD, "criterion_ids": ["setup"]}


def test_a_snapshot_without_a_required_method_never_acquires_one(tmp_path):
    """The prompt the learner answered already reads like a requirement, but
    the item had no required method when it was presented; one added later
    (prompt unchanged) never reaches that answer's grade."""

    paths, vault, repository = split_vault(tmp_path, version=VERSION)
    prompt = f"Write the SVD of A using {METHOD}."
    path = paths.practice_item_path("linear-algebra", ITEM)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["prompt"] = prompt
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    vault = load_vault(paths.root)
    version_id = _present(vault, repository)
    _set_required_method(paths, ("setup",), prompt=prompt)
    vault = load_vault(paths.root)
    assert vault.practice_items[ITEM].required_method is not None
    result = _submit_presented(vault, repository, DivergentGrader(), version_id)
    rule = _support(repository, result.attempt_id)["proof_route_check"]
    assert "required_method" not in rule and rule["unlocated_criterion_ids"] == ["setup"]


def test_a_regrade_never_acquires_a_required_method_added_after_the_answer(tmp_path):
    """An unrestricted item is answered by another route (the unquoted
    mark-down unassessed); a repair then makes it a method item (prompt and
    field). A regrade grades the answer against the contract it was graded
    under, so it is not failed for bypassing the new method."""

    paths, vault, repository = split_vault(tmp_path, version=VERSION)
    result = submit(vault, repository, DivergentGrader(), answer=ALTERNATIVE)
    assert "required_method" not in _support(repository, result.attempt_id)["proof_route_check"]
    _require_method(paths)
    vault = load_vault(paths.root)
    grader = DivergentGrader()
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(result.attempt_id),
                    runtime=ReadyRuntime(), client=grader, grading_source="ai", clock=CLOCK)
    rule = _support(repository, result.attempt_id)["proof_route_check"]
    assert "required_method" not in rule
    assert rule["unlocated_criterion_ids"] == ["setup"] and rule.get("method_route_criterion_ids") is None
    rows = {row.criterion_id: row for row in repository.fetch_grading_evidence(result.attempt_id)}
    assert unassessed_evidence_row(rows["setup"].attribution_json)
    # Re-review F1: the grader reads the statement the learner answered, never
    # the instruction added after it.
    [prompt] = grader.prompts
    assert f"Use {METHOD} in your answer." not in prompt


# -- re-review F1: a regrade grades the one contract its method was frozen with -------------


def _edit_item(paths, *, prompt: str | None = None, setup_description: str | None = None,
               item_id: str = ITEM) -> None:
    path = paths.practice_item_path("linear-algebra", item_id)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if prompt is not None:
        data["prompt"] = prompt
    if setup_description is not None:
        [setup] = [criterion for criterion in data["grading_rubric"]["criteria"] if criterion["id"] == "setup"]
        setup["description"] = setup_description
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _contract_versions(repository, attempt_id, *, since: set[str] | None = None):
    """The contract versions the attempt's evidence rows cite (``since``: only rows added after those ids)."""

    return {row.assessment_contract_version_id
            for row in repository.fetch_grading_evidence(attempt_id, include_superseded=True)
            if since is None or row.id not in since}


def _evidence_ids(repository, attempt_id) -> set[str]:
    return {row.id for row in repository.fetch_grading_evidence(attempt_id, include_superseded=True)}


def test_a_regrade_grades_the_statement_and_rubric_its_method_was_frozen_with(tmp_path):
    """Answered under "Use SVD in your answer."; the owner then makes the
    current statement require another method and edits the method criterion.
    The regrade reads the statement, the rubric and the method from the one
    assessment contract the answer was graded under: the frozen requirement
    is still enforced (the field is the one authority; no statement is read
    to decide it), the grader sees what the learner answered, and the
    regrade's rows cite that contract, so replay reads the same criteria."""

    paths, vault, repository = _method_vault(tmp_path)
    presented = vault.practice_items[ITEM].prompt
    result = submit(vault, repository, DivergentGrader(), answer=ALTERNATIVE)
    [version_id] = _contract_versions(repository, result.attempt_id)
    assert version_id is not None
    graded = _evidence_ids(repository, result.attempt_id)
    _edit_item(paths, prompt="Write the SVD of A. Use row reduction in your answer.",
               setup_description="Edited after the answer.")
    vault = load_vault(paths.root)
    grader = DivergentGrader()
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(result.attempt_id),
                    runtime=ReadyRuntime(), client=grader, grading_source="ai", clock=CLOCK)
    rule = _support(repository, result.attempt_id)["proof_route_check"]
    assert rule["required_method"] == {"name": METHOD, "criterion_ids": ["setup"]}
    assert rule["method_route_criterion_ids"] == ["setup"] and rule["unlocated_criterion_ids"] == []
    [prompt] = grader.prompts
    assert presented in prompt and "row reduction" not in prompt
    # Round 3: the grader is sent the frozen method's instruction after the statement.
    assert json.dumps(f"{presented.rstrip()}\n\nUse {METHOD} in your answer.")[1:-1] in prompt
    assert "Edited after the answer." not in prompt and "setup is right." in prompt
    rows = {row.criterion_id: row for row in repository.fetch_grading_evidence(result.attempt_id)}
    assert not unassessed_evidence_row(rows["setup"].attribution_json)
    assert _contract_versions(repository, result.attempt_id, since=graded) == {version_id}
    assert repository.fetch_practice_attempt(result.attempt_id)["rubric_score"] == 0
    # Replay reads the regrade's rows against that contract: a rebuild is stable.
    project_canonical_facet_state(vault, repository)
    before = _projection(repository)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert _projection(repository) == before


@pytest.mark.parametrize("setup", ["kill_switch", "no_method"])
def test_every_other_regrade_still_reads_the_item_as_it_is_now(tmp_path, setup):
    """Outside method-explicit items (and with the kill switch off) a regrade
    is unchanged: it reads the item as it is now (canonical sources §7.3a)
    and its rows cite no contract."""

    if setup == "kill_switch":
        paths, vault, repository = _method_vault(tmp_path, config=KILL_SWITCH)
    else:
        paths, vault, repository = split_vault(tmp_path, version=VERSION)
    result = submit(vault, repository, DivergentGrader(), answer=ALTERNATIVE)
    graded = _evidence_ids(repository, result.attempt_id)
    _edit_item(paths, prompt="Write the SVD of A, edited after the answer.")
    vault = load_vault(paths.root)
    grader = DivergentGrader()
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(result.attempt_id),
                    runtime=ReadyRuntime(), client=grader, grading_source="ai", clock=CLOCK)
    [prompt] = grader.prompts
    assert "edited after the answer" in prompt
    assert _contract_versions(repository, result.attempt_id, since=graded) == {None}
