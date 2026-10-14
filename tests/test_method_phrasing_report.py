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
    writer_names,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.required_method import has_method_instruction
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
    # The required method takes the target's own name (its concept's title).
    assert cofactor["action"] == "add_required_method" and cofactor["method"] == "Cofactor Expansion"
    payload = repairs["pi_cofactor"]["payload"]
    assert payload["required_method"] == {"name": "Cofactor Expansion", "criterion_ids": ["method"],
                                          "learning_object_id": "lo_cofactor", "concept_id": "cofactor_expansion"}
    assert payload["prompt"].endswith("Use Cofactor Expansion in your answer.")
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
    # Both judges' verdicts reach the ledger (review F6): the writer's too.
    assert {row["judge"] for row in _ledger(vault_paths)} == {"decider", "llm"}
    # The writer agreed on every flag here; a writer that reads a flagged
    # criterion as a fact is recorded as a disagreement on its draft.
    assert not any(action.get("judges_disagree") for action in det.values())

    class FactWriter(LLMJudge):
        def complete(self, request):
            result = super().complete(request)
            return result.model_copy(update={"criteria": [
                row.model_copy(update={"phrased_by": "fact", "fact_phrasing": None, "method": None})
                if row.criterion_id == "minors" else row for row in result.criteria]})

    split = run_method_phrasing(vault, clients={"decider": Decider(), "llm": FactWriter()}, price_per_million=1.0,
                                clock=CLOCK)
    det = {action["criterion_id"]: action for action in
           next(plan for plan in split["repairs"] if plan["item_id"] == "pi_det")["actions"]}
    assert det["minors"]["judges_disagree"] is True and det["minors"]["rewrite"] == "deterministic_draft"
    flagged_minors = next(row for row in split["flagged"] if row["criterion_id"] == "minors")
    assert flagged_minors["writer_reading"] == "fact"
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
    # The canonical sentence generated from the field (the target's own name).
    assert has_method_instruction(cofactor.prompt, cofactor.required_method.name)
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


def test_a_repair_never_rewrites_a_source_statement_or_gives_a_teach_back_a_method(vault_paths):
    """A textbook exercise keeps its verbatim stem and never gains a required
    method from a repair, whatever its wording (redesign 2026-10-14: its
    requirement is the import's one-time judgment, or the owner's); a
    teach-back item never gains one; and a method that merely resembles the
    target (a shared word) is no match."""

    from learnloop.content.proposals.method_phrasing import CriterionReading, repair_plan

    vault = load_vault(vault_paths.root, load_environment=False)
    item = vault.practice_items["pi_cofactor"]

    def reading(method):
        return CriterionReading("pi_cofactor", "method", COFACTOR, "method", "llm", method=method,
                                fact_phrasing="Establishes the value of det(A).", rewrite="llm")

    source = item.model_copy(update={"provenance": item.provenance.model_copy(update={"origin": "canonical_extract"})})
    for prompt in (source.prompt, "Compute det(A) by cofactor expansion."):
        plan = repair_plan(vault, source.model_copy(update={"prompt": prompt}), [reading("cofactor expansion")])
        [action] = plan["actions"]
        assert action["action"] == "rephrase_by_fact" and action["source_statement"]
        assert "prompt" not in plan["payload"] and "required_method" not in plan["payload"]
    teach_back = item.model_copy(update={"practice_mode": "teach_back"})
    assert repair_plan(vault, teach_back, [reading("cofactor expansion")])["actions"][0]["action"] == "rephrase_by_fact"
    resembling = repair_plan(vault, item, [reading("expansion of the product along a row")])
    assert resembling["actions"][0]["action"] == "rephrase_by_fact"


def test_a_repair_adds_the_canonical_sentence_and_only_flags_a_statement_that_may_disagree(vault_paths):
    """On a generated item whose target is the method, the repair adds the
    required method with the canonical sentence; a prompt that may negate it
    is labelled for the owner (advisory), never decided by its wording."""

    from learnloop.content.proposals.method_phrasing import CriterionReading, repair_plan

    vault = load_vault(vault_paths.root, load_environment=False)
    item = vault.practice_items["pi_cofactor"]
    reading = CriterionReading("pi_cofactor", "method", COFACTOR, "method", "llm", method="cofactor expansion")
    plain = repair_plan(vault, item, [reading])
    [action] = plain["actions"]
    assert action["action"] == "add_required_method" and "statement_may_disagree" not in action
    assert plain["payload"]["prompt"] == f"{item.prompt.rstrip()}\n\nUse Cofactor Expansion in your answer."
    negating = item.model_copy(update={"prompt": "Compute det(A) without cofactor expansion."})
    flagged = repair_plan(vault, negating, [reading])
    [action] = flagged["actions"]
    assert action["action"] == "add_required_method" and action["statement_may_disagree"] == "negated"


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


# -- review fixes ---------------------------------------------------------------------------


def _ledger_rows(paths):
    with connect(paths.sqlite_path, read_only=True) as connection:
        return [dict(zip(("id", "judge", "judge_model", "left_id", "verdict", "prompt_version", "input_hash"), row))
                for row in connection.execute(
                    "SELECT id, judge, judge_model, left_id, verdict, prompt_version, input_hash FROM judgment_ledger "
                    "WHERE task = ? ORDER BY rowid", (LEDGER_TASK,))]


def _actions(report, item_id):
    return {action["criterion_id"]: action
            for action in next(plan for plan in report["repairs"] if plan["item_id"] == item_id)["actions"]}


def test_f3_a_repair_refuses_a_rubric_edited_before_acceptance(vault_paths):
    """The proposal carries the item's content hash; an edit after the report
    (a criterion's weight) makes acceptance refuse, so the stale rubric is
    never restored."""

    from learnloop.content.proposals.patches import PatchApplicationError, compute_target_hash

    root = vault_paths.root
    vault = load_vault(root, load_environment=False)
    report = run_method_phrasing(vault, judge="heuristic", propose=True, clock=CLOCK)
    rows = {row["target_entity_id"]: row for row in Repository(vault_paths.sqlite_path).proposal_items(
        report["proposal_id"])}
    assert rows["pi_det"]["payload"]["expected_target_hash"] == compute_target_hash(vault, "practice_item", "pi_det")
    path = vault_paths.practice_item_path("linear-algebra", "pi_det")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["grading_rubric"]["criteria"][2]["points"] = 2
    data["grading_rubric"]["max_points"] = 5
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    with pytest.raises(PatchApplicationError, match="target changed"):
        accept_items(root, report["proposal_id"])
    after = load_vault(root).practice_items["pi_det"]
    criteria = {criterion.id: criterion for criterion in after.grading_rubric.criteria}
    assert criteria["result"].points == 2 and criteria["method"].description == COFACTOR


def test_f3_an_accepted_repair_writes_no_proposal_only_key(vault_paths):
    root = vault_paths.root
    report = run_method_phrasing(load_vault(root, load_environment=False), judge="heuristic", propose=True,
                                 clock=CLOCK)
    accept_items(root, report["proposal_id"])
    for item_id in ("pi_det", "pi_cofactor"):
        text = vault_paths.practice_item_path("linear-algebra", item_id).read_text(encoding="utf-8")
        assert "expected_target_hash" not in text


@pytest.fixture()
def routed(monkeypatch):
    """Real route resolution: Codex reads as ready, an offline OpenRouter key."""

    monkeypatch.setattr("learnloop.ai.runtime.check_codex_runtime", lambda *a, **k: SimpleNamespace(
        status="ready", actual_revision=None, message="ok"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)


def test_f4_a_decider_on_the_route_is_never_the_writer(vault_paths, routed):
    vault = load_vault(vault_paths.root, load_environment=False)
    vault.config.ai.routing.rubric_phrasing_judge = "openrouter_decider"
    route = resolve_judge(vault)
    assert route.kind == "decider" and route.client.provider_type == "decider"
    # The writer is the serving chat profile (ai.active_provider), never the Decider.
    assert route.writer is not None and getattr(route.writer, "provider_type", None) != "decider"
    assert route.as_dict()["writer"] == "codex" and route.as_dict()["rewrites"] == "llm"
    # Forcing the LLM judge on a Decider-routed vault reads with the chat profile too.
    llm = resolve_judge(vault, "llm")
    assert llm.kind == "llm" and getattr(llm.client, "provider_type", None) != "decider"
    # A serving chat provider that is not ready: the fallback provider writes.
    vault.config.ai.active_provider = "deepseek_pro"
    vault.config.ai.fallback_provider = "codex"
    fallback = resolve_judge(vault)
    assert fallback.kind == "decider" and fallback.as_dict()["writer"] == "codex"
    # A route naming a chat profile: that profile judges and writes.
    vault.config.ai.routing.rubric_phrasing_judge = "codex_low"
    named = resolve_judge(vault, "llm")
    assert named.kind == "llm" and named.provider == "codex_low"


def test_f4_a_failed_rewrite_keeps_the_deciders_paid_flags_with_labelled_drafts(vault_paths):
    class BrokenWriter(LLMJudge):
        def complete(self, request):
            raise RuntimeError("the writer broke")

    vault = load_vault(vault_paths.root, load_environment=False)
    report = run_method_phrasing(vault, clients={"decider": Decider(), "llm": BrokenWriter()}, price_per_million=1.0,
                                 clock=CLOCK)
    assert report["judge"]["kind"] == "decider" and "failed_items" not in report
    assert {(row["item_id"], row["criterion_id"]) for row in report["flagged"]} == {
        ("pi_det", "method"), ("pi_det", "minors"), ("pi_cofactor", "method")}
    assert report["writer_failures"] == {"RuntimeError": 2}
    det = _actions(report, "pi_det")
    assert det["minors"]["rewrite"] == "deterministic_draft" and det["minors"]["writer_error"] == "RuntimeError"
    assert {row["judge"] for row in _ledger_rows(vault_paths)} == {"decider"}


class _Mangled(LLMJudge):
    """The LLM judge's reading with its criterion rows mangled."""

    def __init__(self, mangle):
        super().__init__()
        self.mangle = mangle

    def complete(self, request):
        result = super().complete(request)
        rows = [row.model_dump(mode="json") for row in result.criteria]
        return request.result_model.model_validate({"criteria": self.mangle(rows)})


@pytest.mark.parametrize("mangle", [
    lambda rows: [],
    lambda rows: [row for row in rows if row["criterion_id"] != "result"],
    lambda rows: rows + rows[:1],
    lambda rows: rows + [{"criterion_id": "ghost", "phrased_by": "fact"}],
], ids=["empty", "missing", "duplicate", "unknown"])
def test_f5_an_incomplete_reading_is_a_failed_item_never_a_fact_verdict(vault_paths, mangle):
    vault = load_vault(vault_paths.root, load_environment=False)
    report = run_method_phrasing(vault, judge="llm", clients={"llm": _Mangled(mangle)}, price_per_million=1.0,
                                 clock=CLOCK)
    failed = {row["item_id"]: row["error"] for row in report.get("failed_items", [])}
    assert failed.get("pi_det") == "IncompleteJudgment" and failed.get("pi_cofactor") == "IncompleteJudgment"
    assert not any(row["item_id"] in failed for row in report["flagged"])
    assert not any(plan["item_id"] in failed for plan in report["repairs"])
    # Nothing recorded for an item whose reading was incomplete.
    ledgered = {row["left_id"].split("#")[0] for row in _ledger_rows(vault_paths)}
    assert not ledgered & set(failed)


def test_f5_the_required_methods_own_criteria_are_never_ledgered_as_verdicts(vault_paths):
    """A required method's criterion is fact by design, not judged: neither
    judge's ledger records a verdict for it."""

    root = vault_paths.root
    report = run_method_phrasing(load_vault(root, load_environment=False), judge="llm", clients={"llm": LLMJudge()},
                                 price_per_million=1.0, propose=True, clock=CLOCK)
    accept_items(root, report["proposal_id"])
    vault = load_vault(root, load_environment=False)
    before = {row["id"] for row in _ledger_rows(vault_paths)}
    for clients in ({"llm": LLMJudge()}, {"decider": Decider(), "llm": LLMJudge()}):
        run_method_phrasing(vault, judge="llm" if "decider" not in clients else "auto", clients=clients,
                            price_per_million=1.0, clock=CLOCK)
    new = [row for row in _ledger_rows(vault_paths) if row["id"] not in before]
    assert new and "pi_cofactor#method" not in {row["left_id"] for row in new}


def test_f6_the_writers_verdicts_reach_the_ledger_linked_to_the_repair(vault_paths):
    vault = load_vault(vault_paths.root, load_environment=False)
    report = run_method_phrasing(vault, clients={"decider": Decider(), "llm": LLMJudge()}, price_per_million=1.0,
                                 propose=True, clock=CLOCK)
    rows = _ledger_rows(vault_paths)
    writer = [row for row in rows if row["judge"] == "llm"]
    assert {row["left_id"] for row in writer} == {"pi_det#method", "pi_det#minors", "pi_cofactor#method"}
    assert {(row["judge_model"], row["prompt_version"]) for row in writer} == {
        ("llm-fake-model", "rubric-phrasing-judge-v1")}
    decider_hashes = {row["input_hash"] for row in rows if row["judge"] == "decider"}
    assert not decider_hashes & {row["input_hash"] for row in writer}
    by_id = {row["id"]: row for row in rows}
    det = _actions(report, "pi_det")
    for criterion_id in ("method", "minors"):
        ids = det[criterion_id]["judgment_ids"]
        assert [by_id[value]["judge"] for value in ids] == ["decider", "llm"]
        assert {by_id[value]["left_id"] for value in ids} == {f"pi_det#{criterion_id}"}
    # The proposal row links the repair to both verdicts.
    [row] = [row for row in Repository(vault_paths.sqlite_path).proposal_items(report["proposal_id"])
             if row["target_entity_id"] == "pi_det"]
    linked = row["audit"]["rubric_phrasing"]["judgment_ids"]
    assert set(det["minors"]["judgment_ids"]) <= set(linked)

    class FactWriter(LLMJudge):
        def complete(self, request):
            result = super().complete(request)
            return result.model_copy(update={"criteria": [
                row.model_copy(update={"phrased_by": "fact", "fact_phrasing": None, "method": None})
                if row.criterion_id == "minors" else row for row in result.criteria]})

    before = {row["id"] for row in rows}
    split = run_method_phrasing(vault, clients={"decider": Decider(), "llm": FactWriter()}, price_per_million=1.0,
                                clock=CLOCK)
    disagreement = [row for row in _ledger_rows(vault_paths) if row["id"] not in before
                    and row["judge"] == "llm" and row["left_id"] == "pi_det#minors"]
    assert [json.loads(row["verdict"])["phrased_by"] for row in disagreement] == ["fact"]
    assert _actions(split, "pi_det")["minors"]["judges_disagree"] is True


def test_f7_the_dry_run_plans_rewrites_and_their_cost(vault_paths, monkeypatch):
    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task",
                        lambda *a, **k: pytest.fail("a dry run builds no client"))
    vault = load_vault(vault_paths.root, load_environment=False)
    report = run_method_phrasing(vault, judge="decider", dry_run=True)
    [decider, heuristic] = report["judge_plan"]
    assert decider["judge"] == "decider" and heuristic == {"judge": "heuristic", "requests": 0}
    classify, rewrite = decider["steps"]
    assert (classify["step"], classify["provider"], classify["billing"]) == ("classify", "openrouter_decider", "metered")
    assert classify["requests"] == 3 and classify["estimated_usd"] > 0
    # The writer (ai.active_provider: Codex on the subscription) may rewrite every item.
    assert (rewrite["step"], rewrite["provider"], rewrite["billing"]) == ("rewrite", "codex", "subscription")
    assert rewrite["requests_at_most"] == 3 and rewrite["cost_basis"] == "estimated_only"
    assert rewrite["marginal_usd"] == 0.0 and "subscription" in rewrite["note"]
    assert report["status"] == "dry_run" and report["estimate"]["estimated_usd_upper_bound"] == pytest.approx(
        classify["estimated_usd"])
    # A metered writer without a price: refused, never rendered as zero.
    vault.config.ai.active_provider = "openrouter_haiku"
    refused = run_method_phrasing(vault, judge="decider", dry_run=True)
    rewrite = refused["judge_plan"][0]["steps"][1]
    assert refused["status"] == "refused" and rewrite["estimated_usd"] is None
    assert "unknown price" in rewrite["refused"] and any("unknown price" in reason
                                                         for reason in refused["estimate"]["refused"])
    priced = run_method_phrasing(vault, judge="decider", dry_run=True, price_per_million=1.0)
    rewrite = priced["judge_plan"][0]["steps"][1]
    assert priced["status"] == "dry_run" and rewrite["estimated_usd"] == pytest.approx(
        (rewrite["input_tokens"] + rewrite["output_tokens"]) / 1_000_000)
    # A Decider named on the route: the writer is still the chat profile.
    vault.config.ai.routing.rubric_phrasing_judge = "openrouter_decider"
    routed = run_method_phrasing(vault, judge="decider", dry_run=True, price_per_million=1.0)
    assert routed["judge_plan"][0]["steps"][1]["provider"] == "openrouter_haiku"
    cli = CliRunner().invoke(app, ["grading", "method-phrasing", "--vault", str(vault_paths.root), "--dry-run",
                                   "--judge", "decider", "--json"])
    assert cli.exit_code == 0, cli.output


# -- re-review F11: the dry run prices every writer the run may select ------------------------


@pytest.mark.parametrize("route", ["unset", "decider"])
def test_f11_the_dry_run_prices_the_configured_fallback_writer(vault_paths, monkeypatch, route):
    """A subscription primary writer (Codex) and a metered fallback (Haiku on
    OpenRouter): when Codex is unavailable the run writes with the fallback,
    so the dry run plans it too. Without a price it is refused; with one its
    cost is inside the advertised upper bound."""

    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    vault = load_vault(vault_paths.root, load_environment=False)
    if route == "decider":
        vault.config.ai.routing.rubric_phrasing_judge = "openrouter_decider"
    vault.config.ai.fallback_provider = "openrouter_haiku"
    with monkeypatch.context() as patched:
        patched.setattr("learnloop.ai.routing.ready_client_for_task",
                        lambda *a, **k: pytest.fail("a dry run builds no client"))
        refused = run_method_phrasing(vault, judge="auto", dry_run=True)
        priced = run_method_phrasing(vault, judge="auto", dry_run=True, price_per_million=1.0)
    assert refused["status"] == "refused"
    decider, llm, _heuristic = refused["judge_plan"]
    _classify, rewrite, fallback = decider["steps"]
    assert (rewrite["provider"], rewrite["billing"]) == ("codex", "subscription")
    assert (fallback["step"], fallback["provider"], fallback["billing"], fallback["fallback_for"]) == (
        "rewrite", "openrouter_haiku", "metered", "codex")
    assert fallback["estimated_usd"] is None and "unknown price" in fallback["refused"]
    assert decider["estimated_usd"] is None and refused["estimate"]["estimated_usd_upper_bound"] is None
    assert [step["provider"] for step in llm["steps"]] == ["codex", "openrouter_haiku"]
    assert any("openrouter_haiku" in reason for reason in refused["estimate"]["refused"])

    assert priced["status"] == "dry_run"
    decider, llm, _heuristic = priced["judge_plan"]
    classify, rewrite, fallback = decider["steps"]
    assert fallback["requests_at_most"] == rewrite["requests_at_most"] == 3
    assert fallback["estimated_usd"] == pytest.approx((fallback["input_tokens"] + fallback["output_tokens"]) / 1_000_000)
    assert decider["estimated_usd"] == pytest.approx(classify["estimated_usd"] + fallback["estimated_usd"])
    judge, judge_fallback = llm["steps"]
    assert llm["estimated_usd"] == pytest.approx(max(judge["estimated_usd"], judge_fallback["estimated_usd"]))
    assert priced["estimate"]["estimated_usd_upper_bound"] == pytest.approx(
        max(decider["estimated_usd"], llm["estimated_usd"]))
    assert priced["estimate"]["estimated_usd_upper_bound"] >= fallback["estimated_usd"] > 0

    # The run really does select it: Codex unavailable, the fallback writes.
    monkeypatch.setattr("learnloop.ai.runtime.check_codex_runtime", lambda *a, **k: SimpleNamespace(
        status="missing", actual_revision=None, message="not installed"))
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    executed = resolve_judge(vault)
    assert executed.kind == "decider" and executed.as_dict()["writer"] == "openrouter_haiku"


def test_f11_an_explicit_chat_route_or_an_env_override_has_no_fallback_writer(vault_paths, monkeypatch):
    monkeypatch.setattr("learnloop.ai.routing.ready_client_for_task",
                        lambda *a, **k: pytest.fail("a dry run builds no client"))
    vault = load_vault(vault_paths.root, load_environment=False)
    vault.config.ai.fallback_provider = "openrouter_haiku"
    vault.config.ai.routing.rubric_phrasing_judge = "codex_low"
    named = run_method_phrasing(vault, judge="llm", dry_run=True)
    assert [step["provider"] for step in named["judge_plan"][0]["steps"]] == ["codex_low"]
    vault.config.ai.routing.rubric_phrasing_judge = None
    monkeypatch.setenv("LEARNLOOP_AI_PROVIDER", "codex")
    overridden = run_method_phrasing(vault, judge="llm", dry_run=True)
    assert [step["provider"] for step in overridden["judge_plan"][0]["steps"]] == ["codex"]


def test_f11_an_unset_route_without_a_serving_provider_reaches_no_fallback(vault_paths, monkeypatch):
    """The task route resolves an empty or manual serving provider to the
    manual path before any fallback, so the dry run never plans the fallback."""

    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    vault = load_vault(vault_paths.root, load_environment=False)
    vault.config.ai.fallback_provider = "openrouter_haiku"
    for serving in ("", "manual"):
        vault.config.ai.active_provider = serving
        assert "openrouter_haiku" not in writer_names(vault)
