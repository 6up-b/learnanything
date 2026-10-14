"""`learnloop grading method-phrasing`: method-phrased criteria and their repairs.

Owner rule 2026-10-13: existing items' criteria phrased by method are flagged
(the Decider via its route when ready, else the LLM judge route, else the
conservative heuristic; the report says which) and repaired only through the
normal proposal/confirm path: rephrase the criterion by fact, or add the
required method and its instruction when the item's target really is that
method. Nothing is rewritten until the owner accepts. Fakes only; no network.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
import yaml
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.content.proposals.proposals import accept_items
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.content.proposals.method_phrasing import (
    LEDGER_TASK,
    PROPOSAL_PURPOSE,
    RubricPhrasingReading,
    deterministic_fact_draft,
    resolve_judge,
    run_method_phrasing,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.required_method import prompt_states_method
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault
from tests.structured_ai import StructuredClientFake, _request_context
from tests.test_required_method_items import _add_concept_and_lo

CLOCK = FrozenClock(NOW)
COFACTOR = "Uses cofactor expansion along the first row to compute det(A)."
MINORS = "Computes each 2x2 minor and its cofactor sign correctly."
RESULT = "Establishes det(A) = 13."


def _write_item(paths, item_id, lo_id, criteria, prompt="Compute det(A) for A = [[1, 2, 0], [0, 1, 3], [2, 0, 1]]."):
    write_yaml(paths.practice_item_path("linear-algebra", item_id), {
        "schema_version": 1, "id": item_id, "learning_object_id": lo_id, "practice_mode": "short_answer",
        "prompt": prompt, "expected_answer": "13",
        "grading_rubric": {"max_points": sum(points for _cid, points, _d in criteria),
                           "criteria": [{"id": cid, "points": points, "description": description,
                                         "correlation_group": "g1", "recipe_ids": ["r1"]}
                                        for cid, points, description in criteria]},
        "created_at": NOW_ISO, "updated_at": NOW_ISO,
    })


@pytest.fixture()
def vault_paths(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _add_concept_and_lo(paths, "cofactor_expansion", "procedure", "lo_cofactor")
    _add_concept_and_lo(paths, "determinant", "concept", "lo_determinant")
    # The determinant item: method-phrased criteria on a target that is not a method.
    _write_item(paths, "pi_det", "lo_determinant", [("method", 2, COFACTOR), ("minors", 1, MINORS), ("result", 1, RESULT)])
    # The cofactor item: its target IS the method, so the repair makes it the required method.
    _write_item(paths, "pi_cofactor", "lo_cofactor", [("method", 2, COFACTOR), ("result", 2, RESULT)])
    return paths


class LLMJudge(StructuredClientFake):
    """Reads ``method`` and ``minors`` criteria as method-phrased and rewrites them by fact."""

    provider_name = "llm-fake"
    model = "llm-fake-model"

    def __init__(self):
        self.prompts: list[str] = []

    def complete(self, request):
        self.prompts.append(request.prompt)
        context = _request_context(request.prompt, request.purpose)
        rows = []
        for criterion in context["criteria"]:
            if criterion["id"] == "method":
                rows.append({"criterion_id": "method", "phrased_by": "method", "method": "cofactor expansion",
                             "fact_phrasing": "Establishes the value of det(A) by a valid evaluation."})
            elif criterion["id"] == "minors":
                rows.append({"criterion_id": "minors", "phrased_by": "method", "method": "cofactor expansion",
                             "fact_phrasing": "Establishes each intermediate value its evaluation relies on."})
            else:
                rows.append({"criterion_id": criterion["id"], "phrased_by": "fact"})
        return request.result_model.model_validate({"criteria": rows})


class Decider:
    """Answers each criterion's choice question: ``method`` for the cofactor
    and minors criteria (the heuristic misses the minors one)."""

    provider_name = "openrouter_decider"
    model = "perplexity/pplx-decider-v1.1-27b"
    settings = SimpleNamespace(price_per_million_input=0.02)

    def __init__(self):
        self.calls: list[tuple[str, list[str]]] = []

    def decide(self, state, questions, *, purpose=None):
        self.calls.append((state, sorted(questions)))
        answers = {}
        for key, question in questions.items():
            method = "cofactor expansion" in question.instructions or "minor" in question.instructions
            answers[key] = SimpleNamespace(choice="method" if method else "fact",
                                           probabilities={"method": 0.9 if method else 0.1, "fact": 0.1 if method else 0.9})
        return SimpleNamespace(answers=answers)


def _ledger(paths):
    with connect(paths.sqlite_path, read_only=True) as connection:
        return [dict(zip(("judge", "left_id", "verdict", "prompt_version"), row)) for row in connection.execute(
            "SELECT judge, left_id, verdict, prompt_version FROM judgment_ledger WHERE task = ? ORDER BY rowid",
            (LEDGER_TASK,))]


def test_auto_tries_the_decider_then_the_llm_judge_then_the_heuristic(vault_paths):
    vault = load_vault(vault_paths.root, load_environment=False)
    decider, llm = Decider(), LLMJudge()
    assert resolve_judge(vault, clients={"decider": decider, "llm": llm}).kind == "decider"
    route = resolve_judge(vault, clients={"decider": None, "llm": llm})
    assert route.kind == "llm" and route.tried[0] == {"judge": "decider", "provider": "openrouter_decider", "ready": False}
    route = resolve_judge(vault, clients={"decider": None, "llm": None})
    assert route.kind == "heuristic" and route.reason == "neither the Decider nor an LLM judge is ready"
    assert resolve_judge(vault, "heuristic").kind == "heuristic"
    with pytest.raises(RuntimeError, match="not ready"):
        resolve_judge(vault, "decider", clients={"decider": None})
    with pytest.raises(ValueError):
        resolve_judge(vault, "oracle")


def test_the_heuristic_flags_explicit_method_phrasing_and_drafts_repairs(vault_paths):
    vault = load_vault(vault_paths.root, load_environment=False)
    report = run_method_phrasing(vault, judge="heuristic", clock=CLOCK)
    assert report["status"] == "complete" and report["judge"]["kind"] == "heuristic"
    assert report["judge"]["rewrites"] == "deterministic_draft"
    flagged = {(row["item_id"], row["criterion_id"]) for row in report["flagged"]}
    # Conservative: it misses the minors criterion (it names no method).
    assert flagged == {("pi_det", "method"), ("pi_cofactor", "method")}
    repairs = {plan["item_id"]: plan for plan in report["repairs"]}
    [det] = repairs["pi_det"]["actions"]
    assert det["action"] == "rephrase_by_fact" and det["rewrite"] == "deterministic_draft"
    assert det["to"] == "Computes det(A) (any valid method)."
    [cofactor] = repairs["pi_cofactor"]["actions"]
    assert cofactor["action"] == "add_required_method" and cofactor["method"] == "cofactor expansion"
    payload = repairs["pi_cofactor"]["payload"]
    assert payload["required_method"] == {"name": "cofactor expansion", "criterion_ids": ["method"],
                                          "learning_object_id": "lo_cofactor", "concept_id": "cofactor_expansion"}
    assert payload["prompt"].endswith("Use cofactor expansion in your answer.")
    assert _ledger(vault_paths) == []  # the heuristic is deterministic: nothing to record
    assert "proposal_id" not in report


def test_the_llm_judge_reads_and_rewrites_and_its_verdicts_reach_the_ledger(vault_paths):
    vault = load_vault(vault_paths.root, load_environment=False)
    llm = LLMJudge()
    report = run_method_phrasing(vault, judge="llm", clients={"llm": llm}, price_per_million=1.0, clock=CLOCK)
    assert report["judge"]["kind"] == "llm" and report["judge"]["rewrites"] == "llm"
    assert len(llm.prompts) == 3  # one call per item with its own rubric (the basic vault's item too)
    flagged = {(row["item_id"], row["criterion_id"]) for row in report["flagged"]}
    assert flagged == {("pi_det", "method"), ("pi_det", "minors"), ("pi_cofactor", "method")}
    det = {action["criterion_id"]: action for action in
           next(plan for plan in report["repairs"] if plan["item_id"] == "pi_det")["actions"]}
    assert det["minors"]["to"] == "Establishes each intermediate value its evaluation relies on."
    assert det["minors"]["rewrite"] == "llm"
    ledger = _ledger(vault_paths)
    assert {row["judge"] for row in ledger} == {"llm"} and {row["prompt_version"] for row in ledger} == {
        "rubric-phrasing-judge-v1"}
    assert {row["left_id"] for row in ledger} >= {"pi_det#method", "pi_det#minors", "pi_cofactor#result"}
    assert report["spend"]["routes"]["rubric_phrasing_judge"]["calls"] == 3


def test_the_decider_flags_and_the_llm_route_writes_the_fact_phrasings(vault_paths):
    vault = load_vault(vault_paths.root, load_environment=False)
    decider, llm = Decider(), LLMJudge()
    report = run_method_phrasing(vault, clients={"decider": decider, "llm": llm}, price_per_million=1.0, clock=CLOCK)
    assert report["judge"]["kind"] == "decider" and report["judge"]["reason"] == "the Decider is ready"
    assert len(decider.calls) == 3
    flagged = {(row["item_id"], row["criterion_id"]) for row in report["flagged"]}
    assert flagged == {("pi_det", "method"), ("pi_det", "minors"), ("pi_cofactor", "method")}
    # The LLM route wrote only the flagged items' phrasings (two items, not three).
    assert len(llm.prompts) == 2
    det = {action["criterion_id"]: action for action in
           next(plan for plan in report["repairs"] if plan["item_id"] == "pi_det")["actions"]}
    assert det["minors"]["rewrite"] == "llm"
    assert {row["judge"] for row in _ledger(vault_paths)} == {"decider"}
    # Without an LLM ready the Decider's flags get deterministic drafts.
    alone = run_method_phrasing(vault, clients={"decider": Decider(), "llm": None}, clock=CLOCK)
    det = {action["criterion_id"]: action for action in
           next(plan for plan in alone["repairs"] if plan["item_id"] == "pi_det")["actions"]}
    assert det["minors"]["rewrite"] == "deterministic_draft"
    assert alone["judge"]["rewrites"] == "deterministic_draft"


def test_repairs_are_pending_proposals_applied_only_on_accept(vault_paths):
    """No silent rewrite: the proposal is pending (an update is never
    auto-applied) and the items are unchanged until the owner accepts; a
    practised item is labelled so."""

    root = vault_paths.root
    vault = load_vault(root, load_environment=False)
    before = {path: path.read_bytes() for path in sorted(root.glob("subjects/*/practice-items/*.yaml"))}
    report = run_method_phrasing(vault, judge="llm", clients={"llm": LLMJudge()}, price_per_million=1.0,
                                 propose=True, clock=CLOCK)
    patch_id = report["proposal_id"]
    repository = Repository(vault_paths.sqlite_path)
    rows = repository.proposal_items(patch_id)
    assert {row["decision"] for row in rows} == {"pending"} and {row["operation"] for row in rows} == {"update"}
    assert {row["target_entity_id"] for row in rows} == {"pi_det", "pi_cofactor"}
    with connect(vault_paths.sqlite_path, read_only=True) as connection:
        assert connection.execute("SELECT purpose FROM proposed_patches WHERE id = ?", (patch_id,)).fetchone()[0] == (
            PROPOSAL_PURPOSE)
    assert {path: path.read_bytes() for path in before} == before
    accept_items(root, patch_id)
    after = load_vault(root)
    det, cofactor = after.practice_items["pi_det"], after.practice_items["pi_cofactor"]
    criteria = {criterion.id: criterion for criterion in det.grading_rubric.criteria}
    assert criteria["method"].description == "Establishes the value of det(A) by a valid evaluation."
    # Every other criterion field survives the repair.
    assert criteria["method"].correlation_group == "g1" and criteria["method"].recipe_ids == ["r1"]
    assert det.required_method is None
    assert cofactor.required_method is not None and cofactor.required_method.criterion_ids == ["method"]
    assert prompt_states_method(cofactor.prompt, "cofactor expansion")
    # After the repair, nothing is left to flag.
    again = run_method_phrasing(load_vault(root, load_environment=False), judge="llm", clients={"llm": LLMJudge()},
                                price_per_million=1.0, clock=CLOCK)
    # The fake LLM still reads the cofactor item's 'method' criterion as
    # method-phrased, but it is now the required method's criterion: never flagged.
    assert ("pi_cofactor", "method") not in {(row["item_id"], row["criterion_id"]) for row in again["flagged"]}
    assert all(plan["item_id"] != "pi_cofactor" for plan in again["repairs"])


def test_the_dry_run_plans_and_builds_no_client(vault_paths, monkeypatch):
    vault = load_vault(vault_paths.root, load_environment=False)
    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task",
                        lambda *a, **k: pytest.fail("a dry run builds no client"))
    report = run_method_phrasing(vault, dry_run=True)
    assert report["status"] == "dry_run" and report["items"] == 3
    assert [entry["judge"] for entry in report["judge_plan"]] == ["decider", "llm", "heuristic"]
    assert {(row["item_id"], row["criterion_id"]) for row in report["heuristic_flags"]} == {
        ("pi_det", "method"), ("pi_cofactor", "method")}


def test_the_cli_with_the_heuristic_proposes(vault_paths):
    result = CliRunner().invoke(app, [
        "grading", "method-phrasing", "--vault", str(vault_paths.root), "--judge", "heuristic", "--propose", "--json",
    ])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["judge"]["kind"] == "heuristic" and payload["proposal_id"]
    dry = CliRunner().invoke(app, ["grading", "method-phrasing", "--vault", str(vault_paths.root), "--dry-run"])
    assert dry.exit_code == 0, dry.output
    assert any(entry.startswith("pi_det#method") for entry in json.loads(dry.output)["flagged"])


@pytest.mark.parametrize("description, draft", [
    ("Uses cofactor expansion along the first row to compute det(A).", "Computes det(A) (any valid method)."),
    ("Finds the probability by the complement rule.", "Finds the probability (any valid method)."),
    ("Applies the chain rule to differentiate f.", "Differentiates f (any valid method)."),
    ("Establishes det(A) = 13.", "Establishes det(A) = 13. Any valid method that establishes this earns it."),
])
def test_the_deterministic_draft(description, draft):
    assert deterministic_fact_draft(description) == draft


def test_the_llm_contract_round_trips():
    reading = RubricPhrasingReading.model_validate({"criteria": [
        {"criterion_id": "a", "phrased_by": "method", "method": "x", "fact_phrasing": "y"}]})
    assert reading.criteria[0].phrased_by == "method"
