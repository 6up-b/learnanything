"""Method-explicit items, redesigned (2026-10-14): ONE structured authority.

The item's ``required_method`` field, frozen in the assessment contract the
learner answered, is the only thing grading, regrading and replay read. No
grader parses the prompt to decide whether a method applies:

* writers make the text agree with the field: a generated prompt gets the
  ONE canonical sentence generated from it ("Use {method} in your answer."),
  and validation checks for exactly that sentence (whitespace aside);
* a source statement that must not be rewritten is judged ONCE, at import,
  by the Decider (else the LLM judge), ledgered with its probabilities, the
  argmax deciding; the owner changes the field through a proposal;
* a PF variant of a parent with a required method is judged ONCE, at
  publication: a stem that prohibits or contradicts the method is refused,
  never published with the sentence appended (review F10);
* the free-text statement reader survives only as an advisory flag.

The verify's reproductions (worked-example description, "without having to
use", LaTeX- and reference-link-wrapped instructions, a "which" clause, the
contradictory variant stem) can no longer change grading. Fakes only; no
network.
"""

from __future__ import annotations

import inspect
import json
from types import SimpleNamespace

import pytest
import yaml

from learnloop.attempts.grading_support import reference_policy, required_method_policy
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.models import PracticeItem, Rubric
from learnloop.vault.required_method import normalize_required_method, required_method_problems

from tests.helpers import create_basic_vault

STAMP = "2026-10-14T00:00:00Z"
METHOD = "cofactor expansion"
SENTENCE = "Use cofactor expansion in your answer."
FROZEN = {"name": METHOD, "criterion_ids": ["method"]}

#: The final verify's reproductions (job 20261013-235413-bgDA2U): each was read
#: wrongly by some round of the free-text statement reader.
REPRODUCTIONS = {
    "worked_example": "In the worked example, using cofactor expansion gives 13. Compute det(B).",
    "without_having_to_use": "Compute det(A) without having to use cofactor expansion.",
    "latex_wrapped": "Compute det(A) using \\(\\text{cofactor expansion}\\).",
    "reference_link": "Compute det(A) using [cofactor expansion][c].\n\n[c]: https://example.org/cofactor",
    "which_clause": "Determine which matrix is singular using cofactor expansion.",
    "contradictory_variant": "Compute det(B), but do not use the method of cofactor expansion.",
}
REPRO_IDS = list(REPRODUCTIONS)


def _item(prompt: str, required_method: dict | None = None, **extra) -> PracticeItem:
    data = {
        "id": "pi_x", "learning_object_id": "lo_svd_definition", "practice_mode": "short_answer",
        "prompt": prompt, "expected_answer": "13",
        "grading_rubric": {"criteria": [
            {"id": "method", "points": 2, "description": "Uses cofactor expansion along the first row."},
            {"id": "result", "points": 2, "description": "Establishes det(A) = 13."},
        ]},
        "created_at": STAMP, "updated_at": STAMP, **extra,
    }
    if required_method is not None:
        data["required_method"] = required_method
    return PracticeItem.model_validate(data)


# -- 1. grading reads only the frozen field -------------------------------------------------


@pytest.mark.parametrize("case", REPRO_IDS)
def test_grading_reads_only_the_frozen_field(case):
    """Whatever the statement says, the policy shows exactly the method the
    contract froze, and none when it froze none."""

    prompt = REPRODUCTIONS[case]
    item = _item(prompt, required_method=FROZEN)
    ids = ["method", "result"]
    policy = reference_policy(item, "13", route_rules="own-route-v2", rubric_criterion_ids=ids,
                              required_method=FROZEN)
    assert policy["required_method"] == FROZEN
    # The item's current field, the gold-set harness's default, likewise.
    assert reference_policy(item, "13", route_rules="own-route-v2", rubric_criterion_ids=ids)[
        "required_method"] == FROZEN
    unrequired = reference_policy(item, "13", route_rules="own-route-v2", rubric_criterion_ids=ids,
                                  required_method=None)
    assert "required_method" not in unrequired
    assert required_method_policy(item, ids, required_method=FROZEN) == FROZEN


def test_no_grading_entry_point_takes_the_prompt_to_decide():
    """The policy functions have no statement parameter left to read."""

    for function in (reference_policy, required_method_policy):
        assert "presented_prompt" not in inspect.signature(function).parameters


# -- 2. live grading, regrading and replay read the frozen field ------------------------------


def test_a_live_answer_its_regrade_and_replay_are_graded_under_the_frozen_field(tmp_path):
    """A method item whose statement wraps the method in LaTeX (the verify's
    F9 reproduction, which the reader dropped): graded live, regraded and
    replayed under the field, never under a reading of the text."""

    from learnloop.attempts.regrade import regrade_attempt
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
    from tests.split_live_helpers import ReadyRuntime, split_vault, submit
    from tests.test_required_method_grading import (
        ALTERNATIVE, CLOCK, ITEM, METHOD as SVD, VERSION, DivergentGrader, _projection, _support,
    )

    paths, _vault, repository = split_vault(tmp_path, version=VERSION)
    path = paths.practice_item_path("linear-algebra", ITEM)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["prompt"] = "Write A using \\(\\text{singular value decomposition}\\)."
    data["required_method"] = {"name": SVD, "criterion_ids": ["setup"], "statement": "source",
                               "decided_by": "owner"}
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    vault = load_vault(paths.root)
    result = submit(vault, repository, DivergentGrader(), answer=ALTERNATIVE)
    rule = _support(repository, result.attempt_id)["proof_route_check"]
    assert rule["required_method"] == {"name": SVD, "criterion_ids": ["setup"]}
    assert rule["method_route_criterion_ids"] == ["setup"]
    regrade_attempt(vault, repository, repository.fetch_practice_attempt(result.attempt_id),
                    runtime=ReadyRuntime(), client=DivergentGrader(), grading_source="ai", clock=CLOCK)
    rule = _support(repository, result.attempt_id)["proof_route_check"]
    assert rule["required_method"] == {"name": SVD, "criterion_ids": ["setup"]}
    assert rule["method_route_criterion_ids"] == ["setup"]
    before = _projection(repository)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    assert _projection(repository) == before


# -- 3. writers append the canonical sentence; validation checks exactly it ---------------------


def _targets():
    from learnloop.vault.required_method import MethodTarget

    return [MethodTarget(name="Cofactor expansion", basis="concept_type", learning_object_id="lo_cofactor",
                         concept_id="cofactor_expansion")]


@pytest.mark.parametrize("case", REPRO_IDS)
def test_a_generated_prompt_gets_the_canonical_sentence_whatever_it_says(case):
    """The writer never reads the prompt: it appends the one sentence unless
    it is already there verbatim, and keeps the field."""

    prompt = REPRODUCTIONS[case]
    payload = {"prompt": prompt, "grading_rubric": {"criteria": [{"id": "method"}, {"id": "result"}]},
               "required_method": dict(FROZEN)}
    notes = normalize_required_method(payload, _targets())
    assert notes == ["required_method:instruction_added"]
    assert payload["prompt"] == f"{prompt}\n\n{SENTENCE}"
    assert payload["required_method"]["name"] == METHOD
    again = dict(payload)
    assert normalize_required_method(again, _targets()) == [] and again["prompt"] == payload["prompt"]


def test_an_affirmative_phrasing_is_not_the_canonical_sentence():
    """Only the exact sentence (whitespace aside) states the field: "Compute
    det(A) by cofactor expansion." gets the sentence appended, and
    validation reports it until then."""

    from learnloop.vault.required_method import ensure_method_instruction, has_method_instruction

    prompt = "Compute det(A) by cofactor expansion."
    assert not has_method_instruction(prompt, METHOD)
    assert has_method_instruction("Compute det(A).\n  Use cofactor\nexpansion in   your answer.", METHOD)
    assert not has_method_instruction("Compute det(A). use cofactor expansion in your answer.", METHOD)
    assert ensure_method_instruction(prompt, METHOD) == f"{prompt}\n\n{SENTENCE}"
    rubric = Rubric.model_validate(_item(prompt).grading_rubric.model_dump(mode="json"))
    codes = [problem.code for problem in required_method_problems(_item(prompt, FROZEN), rubric)]
    assert codes == ["required_method:not_stated"]


@pytest.mark.parametrize("case", REPRO_IDS)
def test_validation_checks_the_exact_sentence_and_only_flags_the_rest(case):
    """Without the sentence every reproduction is ``not_stated``; with it none
    is an error, and the advisory heuristic only warns (judge = heuristic)
    where the statement may negate the method."""

    prompt = REPRODUCTIONS[case]
    rubric = Rubric.model_validate(_item(prompt).grading_rubric.model_dump(mode="json"))
    errors = [problem.code for problem in required_method_problems(_item(prompt, FROZEN), rubric)
              if problem.severity == "error"]
    assert errors == ["required_method:not_stated"]
    stated = _item(f"{prompt}\n\n{SENTENCE}", FROZEN)
    problems = required_method_problems(stated, rubric)
    assert [problem for problem in problems if problem.severity == "error"] == []
    advisory = [problem for problem in problems if problem.code == "required_method:statement_may_disagree"]
    assert all(problem.severity == "warning" and problem.judge == "heuristic" for problem in advisory)
    assert bool(advisory) == (case in ("without_having_to_use", "contradictory_variant"))


def test_a_source_statement_is_valid_by_its_recorded_decision_not_its_wording():
    rubric = Rubric.model_validate(_item("x").grading_rubric.model_dump(mode="json"))
    decided = {**FROZEN, "statement": "source", "decided_by": "judgment", "judgment_id": "j1"}
    assert [p.code for p in required_method_problems(_item(REPRODUCTIONS["latex_wrapped"], decided), rubric)
            if p.severity == "error"] == []
    undecided = {**FROZEN, "statement": "source"}
    assert [p.code for p in required_method_problems(_item(REPRODUCTIONS["latex_wrapped"], undecided), rubric)
            if p.severity == "error"] == ["required_method:undecided"]
    unlinked = {**FROZEN, "statement": "source", "decided_by": "judgment"}
    assert [p.code for p in required_method_problems(_item("Compute det(A).", unlinked), rubric)
            if p.severity == "error"] == ["required_method:undecided"]


# -- 4. the one-time judgment ---------------------------------------------------------------------


class StatementDecider:
    """A Decider double for the statement questions: probabilities per stem."""

    provider_name = "openrouter_decider"
    provider_type = "decider"
    model = "perplexity/pplx-decider-v1.1-27b"
    settings = SimpleNamespace(price_per_million_input=0.02)

    def __init__(self, probabilities):
        self.probabilities = probabilities
        self.calls: list[tuple[str, dict]] = []

    def decide(self, state, questions, *, purpose):
        from learnloop.ai.decisions import ChoiceAnswer, DecisionResult
        from learnloop.ai.execution import model_call, report_call_usage

        self.calls.append((state, dict(questions)))
        probabilities = self.probabilities(state) if callable(self.probabilities) else dict(self.probabilities)
        with model_call(self, purpose=purpose, prompt=state):
            report_call_usage({"input_tokens": 150, "output_tokens": 1, "cost": 0.000003})
            answers = {name: ChoiceAnswer(choice=max(probabilities, key=probabilities.get),
                                          probabilities=probabilities) for name in questions}
            return DecisionResult(answers=answers, model=self.model, input_tokens=150, output_tokens=1,
                                  cost=0.000003, response_id="r", provider="Fake")


REQUIRES = {"requires": 0.81, "allows": 0.17, "prohibits": 0.02}
ALLOWS = {"requires": 0.22, "allows": 0.71, "prohibits": 0.07}
PROHIBITS = {"requires": 0.03, "allows": 0.12, "prohibits": 0.85}


def _ledger(repository, task="required_method_statement"):
    with connect(repository.sqlite_path, read_only=True) as connection:
        connection.row_factory = __import__("sqlite3").Row
        return [dict(row) for row in connection.execute(
            "SELECT * FROM judgment_ledger WHERE task = ? ORDER BY created_at, id", (task,))]


@pytest.fixture()
def basic(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    return paths, load_vault(paths.root), Repository(paths.sqlite_path)


def test_the_judgment_is_made_once_ledgered_with_probabilities_and_the_argmax_decides(basic):
    from learnloop.content.proposals.method_statement_judge import (
        SOURCE_QUESTION_SET, TASK, resolve_statement_judge,
    )

    _paths, vault, repository = basic
    decider = StatementDecider(REQUIRES)
    judge = resolve_statement_judge(vault, clients=decider)
    assert judge.kind == "decider"
    statement = REPRODUCTIONS["latex_wrapped"]
    verdict = judge.judge(repository, question="source", subject_kind="practice_item", subject_id="pi_x",
                          statement=statement, method=METHOD, owner=("test", "run"))
    assert (verdict.verdict, verdict.judge, verdict.reused) == ("requires", "decider", False)
    [row] = _ledger(repository)
    assert (row["task"], row["left_kind"], row["left_id"], row["judge"]) == (TASK, "practice_item", "pi_x", "decider")
    assert (row["prompt_version"], row["verdict"], row["score"]) == (SOURCE_QUESTION_SET, "requires", 0.81)
    assert row["judge_model"] == decider.model and row["id"] == verdict.judgment_id
    assert json.loads(row["rationale"])["probabilities"] == REQUIRES
    # The Decider read the statement verbatim and the question named the method.
    [(state, questions)] = decider.calls
    assert statement in state and METHOD in questions["verdict"].instructions
    # Once: the same statement and method reuse the row, with no new call.
    again = judge.judge(repository, question="source", subject_kind="practice_item", subject_id="pi_x",
                        statement=statement, method=METHOD, owner=("test", "run"))
    assert again.reused and again.judgment_id == verdict.judgment_id and len(decider.calls) == 1
    # The request left a receipt owned by the caller.
    with connect(repository.sqlite_path, read_only=True) as connection:
        owners = connection.execute("SELECT owner_kind, owner_id FROM model_call_receipts").fetchall()
    assert ("test", "run") in {tuple(owner) for owner in owners}


def test_the_argmax_has_no_threshold_and_a_tie_is_conservative():
    from learnloop.content.proposals.method_statement_judge import argmax

    assert argmax("source", {"requires": 0.34, "allows": 0.33, "prohibits": 0.33}) == "requires"
    assert argmax("source", {"requires": 0.4, "allows": 0.4, "prohibits": 0.2}) == "allows"
    assert argmax("variant", {"consistent": 0.5, "contradicts": 0.5}) == "contradicts"
    assert argmax("variant", {"consistent": 0.51, "contradicts": 0.49}) == "consistent"


def test_without_a_decider_the_llm_judge_decides_and_without_either_nothing_does(basic):
    from learnloop.content.proposals.method_statement_judge import LLM_PROMPT_VERSION, resolve_statement_judge
    from tests.structured_ai import StructuredClientFake

    class LLM(StructuredClientFake):
        provider_name = "llm-fake"
        model = "llm-fake-model"

        def complete(self, request):
            return request.result_model.model_validate({"verdict": "prohibits", "rationale": "It says without."})

    _paths, vault, repository = basic
    judge = resolve_statement_judge(vault, clients={"decider": None, "llm": LLM()}, price_per_million=1.0)
    assert judge.kind == "llm"
    verdict = judge.judge(repository, question="source", subject_kind="practice_item", subject_id="pi_y",
                          statement=REPRODUCTIONS["without_having_to_use"], method=METHOD, owner=("test", "run"))
    assert verdict.verdict == "prohibits"
    [row] = _ledger(repository)
    assert (row["judge"], row["prompt_version"], row["score"]) == ("llm", LLM_PROMPT_VERSION, None)
    assert resolve_statement_judge(vault, clients={"decider": None, "llm": None}) is None


def test_a_metered_llm_judge_without_a_price_is_refused_before_sending_and_decides_nothing(basic):
    """Spend is admitted before every request: a metered LLM judge with no
    owner price is refused, nothing is sent, and the statement keeps no
    requirement (the writer check's caller hears why)."""

    from learnloop.content.proposals.method_statement_judge import resolve_statement_judge, source_judge
    from tests.structured_ai import StructuredClientFake

    class LLM(StructuredClientFake):
        provider_name = "llm-fake"
        model = "llm-fake-model"

        def __init__(self):
            self.prompts: list[str] = []

        def complete(self, request):
            self.prompts.append(request.prompt)
            return request.result_model.model_validate({"verdict": "requires", "rationale": "r"})

    _paths, vault, repository = basic
    llm = LLM()
    judge = resolve_statement_judge(vault, clients={"decider": None, "llm": llm})
    reasons: list[str] = []
    payload = {"prompt": REPRODUCTIONS["worked_example"], "required_method": dict(FROZEN),
               "grading_rubric": {"criteria": [{"id": "method"}]}}
    notes = normalize_required_method(payload, _targets(), source_statement=True,
                                      judge_source=source_judge(judge, repository, subject_id="pi_src",
                                                                owner=("test", "run"), log=reasons.append))
    assert notes == ["required_method:dropped_source_statement_unjudged"]
    assert llm.prompts == [] and _ledger(repository) == []
    assert reasons == ["the judgment failed (SpendLimitExceeded)"]


@pytest.mark.parametrize("probabilities, kept", [(REQUIRES, True), (ALLOWS, False), (PROHIBITS, False)],
                         ids=["requires", "allows", "prohibits"])
def test_a_source_statement_keeps_the_field_only_by_the_judgment(basic, probabilities, kept):
    """The writer check asks the judge once, records its id in the field
    (``statement = source``), and never rewrites the statement."""

    from learnloop.content.proposals.method_statement_judge import resolve_statement_judge, source_judge

    _paths, vault, repository = basic
    judge = resolve_statement_judge(vault, clients=StatementDecider(probabilities))
    statement = REPRODUCTIONS["worked_example"]
    payload = {"prompt": statement, "grading_rubric": {"criteria": [{"id": "method"}, {"id": "result"}]},
               "required_method": dict(FROZEN)}
    notes = normalize_required_method(
        payload, _targets(), source_statement=True,
        judge_source=source_judge(judge, repository, subject_id="pi_src", owner=("test", "run")),
    )
    assert payload["prompt"] == statement
    [row] = _ledger(repository)
    if kept:
        assert notes == ["required_method:source_statement_judged_requires"]
        assert payload["required_method"] == {
            **FROZEN, "learning_object_id": "lo_cofactor", "concept_id": "cofactor_expansion",
            "statement": "source", "decided_by": "judgment", "judgment_id": row["id"]}
    else:
        assert "required_method" not in payload
        assert notes == [f"required_method:dropped_source_statement_judged_{row['verdict']}"]


def test_a_source_statement_with_no_judge_keeps_no_requirement(basic):
    from learnloop.content.proposals.method_statement_judge import source_judge

    _paths, _vault, repository = basic
    reasons: list[str] = []
    payload = {"prompt": REPRODUCTIONS["worked_example"], "required_method": dict(FROZEN),
               "grading_rubric": {"criteria": [{"id": "method"}]}}
    notes = normalize_required_method(payload, _targets(), source_statement=True,
                                      judge_source=source_judge(None, repository, subject_id="pi_src",
                                                                owner=("test", "run"), log=reasons.append))
    assert notes == ["required_method:dropped_source_statement_unjudged"] and "required_method" not in payload
    assert reasons == ["no judge is ready"] and _ledger(repository) == []


# -- 5. the import path: decided once, by the judgment, not by the wording ------------------------

SVD = "singular value decomposition"
#: The verify's source reproductions, on the basic vault's method target
#: (``lo_svd_definition``: the singular value decomposition, a procedure).
SOURCE_REPRODUCTIONS = {
    "worked_example": "In the worked example, using singular value decomposition gives A = U S V^T. Factor B.",
    "without_having_to_use": "Factor A without having to use singular value decomposition.",
    "latex_wrapped": "Factor A using \\(\\text{singular value decomposition}\\).",
    "reference_link": "Factor A using [singular value decomposition][svd].\n\n[svd]: https://example.org/svd",
    "which_clause": "Determine which factor is orthogonal using singular value decomposition.",
}


def _setup_statement(tmp_path, text: str):
    from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
    from tests.test_source_inventory import _persist, _register_revision

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    _register_revision(repository, source_id="src1", revision_id="rev1")
    blocks = [DocumentBlock.build(span_id="s1", block_type="Text", text=text, ordinal=0, page=1,
                                  section_path=["SVD"])]
    ir = DocumentIR(
        extractor="marker", extractor_version="1",
        units=[DocumentUnit(unit_id="u1", label="SVD", ordinal=0, semantic_hash="sha256:svd", page_start=1,
                            page_end=1, span_ids=["s1"])],
        blocks=blocks, assets=[], health=ExtractionHealth(),
    )
    _persist(repository, ir, revision_id="rev1", extraction_id="ext1")
    return paths, repository


def _import(tmp_path, statement: str, **kwargs):
    from learnloop.content.authoring import exercise_authoring as EX
    from learnloop.content.authoring.ai_contracts import ExerciseAuthoring
    from learnloop.content.proposals.ai_contracts import RequiredMethodPayload
    from tests.test_exercise_authoring import FakeClient, _item as exercise_item, _write_facet_registry

    paths, repository = _setup_statement(tmp_path, statement)
    _write_facet_registry(tmp_path)
    entry = exercise_item(required_method=RequiredMethodPayload(name=SVD, criterion_ids=["factorization"]),
                          statement_md=statement)
    result = EX.import_exercises(
        tmp_path / "vault", repository, FakeClient(ExerciseAuthoring(items=[entry])), extraction_id="ext1",
        raw_selection={"nodes": [{"spanId": "s1", "quote": statement}]}, source_id="src1", **kwargs,
    )
    [summary] = result["items"]
    item = load_vault(tmp_path / "vault").practice_items[summary["practice_item_id"]]
    return item, result, repository


@pytest.mark.parametrize("case", list(SOURCE_REPRODUCTIONS))
def test_an_import_without_a_judgment_never_reads_a_requirement_into_the_wording(tmp_path, case):
    """No judge is ready in the test vault: the requirement the author
    proposed is dropped, whatever the statement's wording (the reader read
    "worked example" and "without having to use" as requirements), and the
    statement is never rewritten."""

    item, result, _repository = _import(tmp_path, SOURCE_REPRODUCTIONS[case])
    assert item.prompt == SOURCE_REPRODUCTIONS[case]
    assert item.required_method is None
    assert any("required_method:dropped_source_statement_unjudged" in warning for warning in result["warnings"])


@pytest.mark.parametrize("case", list(SOURCE_REPRODUCTIONS))
@pytest.mark.parametrize("probabilities", [REQUIRES, ALLOWS], ids=["judged_requires", "judged_allows"])
def test_an_import_keeps_the_field_exactly_when_the_one_time_judgment_says_requires(tmp_path, case, probabilities):
    from learnloop.content.proposals.method_statement_judge import resolve_statement_judge

    holder: dict = {}

    def judge():
        holder["judge"] = resolve_statement_judge(load_vault(tmp_path / "vault"),
                                                  clients=StatementDecider(probabilities))
        return holder["judge"]

    from learnloop.content.proposals.method_statement_judge import LazyStatementJudge

    item, _result, repository = _import(tmp_path, SOURCE_REPRODUCTIONS[case],
                                        method_judge=LazyStatementJudge(judge))
    assert item.prompt == SOURCE_REPRODUCTIONS[case]
    [row] = _ledger(repository)
    assert (row["left_kind"], row["left_id"], row["right_id"]) == ("practice_item", item.id, SVD)
    if probabilities is REQUIRES:
        assert item.required_method is not None
        assert (item.required_method.statement, item.required_method.decided_by) == ("source", "judgment")
        assert item.required_method.judgment_id == row["id"]
        # Grading then reads exactly this field.
        assert required_method_policy(item, ["factorization", "factors"]) == {
            "name": SVD, "criterion_ids": ["factorization"]}
    else:
        assert item.required_method is None


# -- 6. the owner's override, through the proposal/confirm path -----------------------------------


def test_the_owner_overrides_a_source_decision_and_clears_it_through_proposals(tmp_path):
    from learnloop.content.proposals.proposals import accept_items
    from learnloop.content.proposals.required_method_override import propose_required_method_override

    item, _result, repository = _import(tmp_path, SOURCE_REPRODUCTIONS["which_clause"])
    assert item.required_method is None  # unjudged at import
    root = tmp_path / "vault"
    proposed = propose_required_method_override(load_vault(root), repository, item.id, name=SVD,
                                                criterion_ids=["factorization"])
    assert proposed["statement"] == "source" and proposed["to"]["decided_by"] == "owner"
    [row] = repository.proposal_items(proposed["proposal_id"])
    assert row["decision"] == "pending" and "prompt" not in row["payload"]
    assert load_vault(root).practice_items[item.id].required_method is None  # nothing until accepted
    accept_items(root, proposed["proposal_id"])
    changed = load_vault(root).practice_items[item.id]
    assert changed.prompt == SOURCE_REPRODUCTIONS["which_clause"]
    assert (changed.required_method.name, changed.required_method.statement, changed.required_method.decided_by) == (
        SVD, "source", "owner")
    assert required_method_problems(changed, changed.grading_rubric) == [] or all(
        problem.severity == "warning" for problem in required_method_problems(changed, changed.grading_rubric))
    cleared = propose_required_method_override(load_vault(root), repository, item.id, clear=True)
    accept_items(root, cleared["proposal_id"])
    final = load_vault(root).practice_items[item.id]
    assert final.required_method is None and final.prompt == SOURCE_REPRODUCTIONS["which_clause"]


def test_the_owner_override_on_a_generated_item_moves_the_canonical_sentence(tmp_path):
    from learnloop.content.proposals.proposals import accept_items
    from learnloop.content.proposals.required_method_override import propose_required_method_override

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    vault = load_vault(paths.root)
    item = vault.practice_items["pi_svd_define_001"]
    original = item.prompt
    proposed = propose_required_method_override(vault, repository, item.id, name=SVD, criterion_ids=["correctness"])
    assert proposed["statement"] == "instruction"
    accept_items(paths.root, proposed["proposal_id"])
    changed = load_vault(paths.root).practice_items[item.id]
    assert changed.prompt == f"{original.rstrip()}\n\nUse {SVD} in your answer."
    assert changed.required_method.criterion_ids == ["correctness"]
    assert changed.required_method.statement == "instruction"
    cleared = propose_required_method_override(load_vault(paths.root), repository, item.id, clear=True)
    accept_items(paths.root, cleared["proposal_id"])
    final = load_vault(paths.root).practice_items[item.id]
    assert final.required_method is None and final.prompt == original.rstrip()


def test_the_cli_proposes_the_override_and_accept_applies_it(tmp_path):
    from typer.testing import CliRunner

    from learnloop.cli import app

    paths = create_basic_vault(tmp_path / "vault")
    result = CliRunner().invoke(app, ["grading", "required-method", "pi_svd_define_001", "--method", SVD,
                                      "--criterion", "correctness", "--vault", str(paths.root), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "proposed" and payload["to"]["name"] == SVD
    assert load_vault(paths.root).practice_items["pi_svd_define_001"].required_method is None
    accepted = CliRunner().invoke(app, ["accept", payload["proposal_id"], "--all", "--vault", str(paths.root)])
    assert accepted.exit_code == 0, accepted.output
    item = load_vault(paths.root).practice_items["pi_svd_define_001"]
    assert item.required_method.name == SVD and item.prompt.endswith(f"Use {SVD} in your answer.")
    refused = CliRunner().invoke(app, ["grading", "required-method", "pi_svd_define_001", "--method", SVD,
                                       "--criterion", "ghost", "--vault", str(paths.root)])
    assert refused.exit_code == 1 and json.loads(refused.output)["status"] == "invalid"


def test_the_override_refuses_unknown_criteria_and_a_clear_with_nothing_to_clear(tmp_path):
    from learnloop.content.proposals.required_method_override import override_payload

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    with pytest.raises(ValueError, match="no criterion 'ghost'"):
        override_payload(vault, "pi_svd_define_001", name=SVD, criterion_ids=["ghost"])
    with pytest.raises(ValueError, match="no required method to clear"):
        override_payload(vault, "pi_svd_define_001", clear=True)
    with pytest.raises(ValueError, match="--criterion"):
        override_payload(vault, "pi_svd_define_001", name=SVD)


def test_a_generated_proposal_never_changes_a_source_items_field(tmp_path):
    """Only the import's judgment or the owner decides a textbook statement's
    requirement: an AI update proposal's ``required_method`` is dropped."""

    from learnloop.clock import FrozenClock
    from learnloop.content.proposals.ai_contracts import AuthoringProposal
    from learnloop.content.proposals.proposals import persist_authoring_proposal
    from tests.helpers import NOW

    item, _result, repository = _import(tmp_path, SOURCE_REPRODUCTIONS["which_clause"])
    proposal = AuthoringProposal.model_validate({
        "summary": "update", "source_refs": [{"ref_type": "manual_context", "ref_id": "manual"}],
        "items": [{"client_item_id": "u1", "item_type": "practice_item", "operation": "update",
                   "target": {"entity_type": "practice_item", "entity_id": item.id},
                   "source_ref_ids": ["manual"], "rationale": "r", "review_route": "review_required",
                   "payload": {"required_method": {"name": SVD, "criterion_ids": ["factorization"]},
                               "hints": ["A hint."]}}],
    })
    patch_id = persist_authoring_proposal(tmp_path / "vault", proposal, provider="import", clock=FrozenClock(NOW))
    [row] = repository.proposal_items(patch_id)
    assert "required_method" not in row["payload"] and "prompt" not in row["payload"]


# -- 7. PF variants: the one-time publication judgment (review F10) --------------------------------


def _pf_parent():
    return _item(f"Compute det(A). {SENTENCE}", FROZEN)


def _pf_row(stem: str) -> dict:
    return {"payload_json": json.dumps({"stem": stem, "final_answer": "3", "solution": "2*2 - 1*1 = 3"}),
            "final_relation": "isomorph", "declared_relation": "isomorph", "difficulty": None,
            "generation_path": "ensemble", "id": "cand1", "family_id": "fam1"}


def test_a_variant_payload_is_never_built_without_its_publication_judgment():
    """The verify's F10 reproduction: the contradictory stem is refused, never
    given the sentence; so is any stem with no recorded judgment."""

    from learnloop.ops.pf_publish import (
        PublishRefused, RequiredMethodUnjudged, VariantContradictsRequiredMethod, build_item_payload,
    )

    row = _pf_row(REPRODUCTIONS["contradictory_variant"])
    with pytest.raises(RequiredMethodUnjudged) as unjudged:
        build_item_payload(None, _pf_parent(), row, item_id="pi_pf_x", now_iso=STAMP)
    assert isinstance(unjudged.value, PublishRefused)
    with pytest.raises(VariantContradictsRequiredMethod, match=METHOD):
        build_item_payload(None, _pf_parent(), row, item_id="pi_pf_x", now_iso=STAMP, method_verdict="contradicts")
    consistent = build_item_payload(None, _pf_parent(), _pf_row("Compute det(B) for B = [[2, 1], [1, 2]]."),
                                    item_id="pi_pf_y", now_iso=STAMP, method_verdict="consistent")
    assert consistent["prompt"] == f"Compute det(B) for B = [[2, 1], [1, 2]].\n\n{SENTENCE}"
    assert consistent["required_method"] == FROZEN


def _pf_method_vault(tmp_path):
    from learnloop.vault.writer import upsert_practice_item
    from tests.pf_fakes import seed_pf_vault

    _vault, repository, paths = seed_pf_vault(tmp_path / "vault")
    parent = load_vault(paths.root).practice_items["pi_linear_001"].model_dump(mode="json")
    parent["prompt"] = "Solve 2x + 4 = 10 for x. Use substitution in your answer."
    parent["required_method"] = {"name": "substitution", "criterion_ids": ["setup"]}
    upsert_practice_item(paths.root, parent)
    return repository, paths


VARIANT_CONSISTENT = {"consistent": 0.93, "contradicts": 0.07}
VARIANT_CONTRADICTS = {"consistent": 0.08, "contradicts": 0.92}


@pytest.mark.parametrize("probabilities, published", [(VARIANT_CONSISTENT, True), (VARIANT_CONTRADICTS, False)],
                         ids=["consistent", "contradicts"])
def test_pf_judges_each_selected_variant_once_and_publication_reads_the_verdict(tmp_path, probabilities, published):
    from learnloop.content.authoring.pf_sandbox import sandbox_available
    from learnloop.content.proposals.method_statement_judge import VARIANT_QUESTION_SET
    from learnloop.ops.pf_generation import publish_backlog
    from tests.pf_fakes import clients
    from tests.test_pf_generation import NEXT_DAY, ledger, rows, run

    if not sandbox_available():
        pytest.skip("bubblewrap is not installed")
    repository, paths = _pf_method_vault(tmp_path)
    decider = StatementDecider(probabilities)
    report = run(paths, publish=False, select=1, fakes=clients(required_method_judge=decider))
    [family] = report["families"]
    verdict = "consistent" if published else "contradicts"
    assert family["required_method_judgments"] == {verdict: 1}
    [selected] = rows(repository, "status='selected'")
    [judgment] = _ledger(repository)
    assert (judgment["left_kind"], judgment["left_id"], judgment["prompt_version"], judgment["verdict"]) == (
        "pf_candidate", selected["id"], VARIANT_QUESTION_SET, verdict)
    stem = json.loads(selected["payload_json"])["stem"]
    assert stem in decider.calls[0][0]
    # The backlog makes no model call: it reads the recorded verdict.
    outcome = publish_backlog(load_vault(paths.root), clock=NEXT_DAY)
    assert len(decider.calls) == 1
    [row] = rows(repository, "id=?", (selected["id"],))
    if published:
        [item_id] = outcome["published_item_ids"]
        item = load_vault(paths.root).practice_items[item_id]
        assert item.prompt == f"{stem.rstrip()}\n\nUse substitution in your answer."
        assert item.required_method.name == "substitution"
    else:
        assert outcome["published_item_ids"] == [] and outcome["refused_candidates"] == 1
        assert row["status"] == "rejected" and row["rejection_filter"] == "required_method_contradicted"
        refusals = [entry for entry in ledger(repository, "pf_publish")
                    if entry["verdict"] == "refuse_contradicts_required_method"]
        assert len(refusals) == 1 and refusals[0]["left_id"] == selected["id"]


def test_a_variant_with_no_verdict_or_an_edited_stem_is_not_published(tmp_path):
    from learnloop.content.authoring.pf_sandbox import sandbox_available
    from learnloop.db.stores import pf as store
    from learnloop.ops.pf_generation import publish_backlog
    from tests.pf_fakes import clients
    from tests.test_pf_generation import NEXT_DAY, rows, run

    if not sandbox_available():
        pytest.skip("bubblewrap is not installed")
    repository, paths = _pf_method_vault(tmp_path)
    report = run(paths, publish=False, select=1, fakes=clients(required_method_judge={"decider": None, "llm": None}))
    assert report["families"][0]["required_method_judgments"] == {"unjudged": 1}
    [selected] = rows(repository, "status='selected'")
    outcome = publish_backlog(load_vault(paths.root), clock=NEXT_DAY)
    assert outcome["published_item_ids"] == [] and outcome["unjudged_candidates"] == 1
    assert rows(repository, "id=?", (selected["id"],))[0]["status"] == "selected"
    # A verdict binds the stem it judged: a stem edited afterwards has none.
    second = _pf_method_vault(tmp_path / "second")
    repository, paths = second
    judged = run(paths, publish=False, select=1,
                 fakes=clients(required_method_judge=StatementDecider(VARIANT_CONSISTENT)))
    # The judgment is admitted under the run's own caps (its metered budget).
    charged = lambda result: result["usage"]["charged"]["metered"]["calls"]  # noqa: E731
    assert charged(judged) == charged(report) + 1
    [selected] = rows(repository, "status='selected'")
    payload = json.loads(selected["payload_json"])
    payload["stem"] = REPRODUCTIONS["contradictory_variant"]
    with repository.connection() as connection:
        store.update_candidate(connection, selected["id"], payload_json=json.dumps(payload))
    outcome = publish_backlog(load_vault(paths.root), clock=NEXT_DAY)
    assert outcome["published_item_ids"] == [] and outcome["unjudged_candidates"] == 1


# -- 8. review F13: a frozen regrade binds verification to the content it graded --------------------


@pytest.fixture
def gated_successor(tmp_path, monkeypatch):
    from learnloop.algorithm_versions import METHOD_EXPLICIT_ALGORITHM_VERSION
    from learnloop.content.authoring import pf_sandbox
    from tests.helpers import set_algorithm_version
    from tests.source_service_fakes import build_textbook_vault

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    set_algorithm_version(paths, METHOD_EXPLICIT_ALGORITHM_VERSION)
    monkeypatch.setattr(pf_sandbox, "_sandbox_bwrap_path", lambda: None)
    return paths, repository, spans


def _verified_method_import(paths, repository, spans):
    from learnloop.vault.writer import upsert_practice_item
    from tests.source_service_fakes import loaded
    from tests.test_reference_gate_imports import _verified_import

    item_id = _verified_import(paths, repository, spans)
    data = loaded(paths).practice_items[item_id].model_dump(mode="json")
    [criterion] = data["grading_rubric"]["criteria"][:1]
    data["required_method"] = {"name": "the characteristic polynomial", "criterion_ids": [criterion["id"]],
                               "statement": "source", "decided_by": "owner"}
    upsert_practice_item(paths.root, data)
    return item_id, criterion["id"]


def test_f13_a_frozen_regrade_keeps_the_status_of_the_content_it_graded(gated_successor):
    from tests.test_reference_gate_imports import _attempt, _bindings, _edit_key, _regrade, _status

    paths, repository, spans = gated_successor
    item_id, criterion = _verified_method_import(paths, repository, spans)
    attempt = _attempt(paths, repository, item_id, criterion=criterion)
    assert _status(repository, attempt.attempt_id) == "verified"
    cited = {row.assessment_contract_version_id for row in repository.fetch_grading_evidence(attempt.attempt_id)}
    assert None not in cited  # the attempt's grade cites its frozen contract
    _edit_key(paths, repository, item_id)  # the current content: unverified
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "verified"
    assert _bindings(repository, attempt.attempt_id) == []


def test_f13_a_frozen_regrade_of_the_current_content_still_binds_it(gated_successor):
    """The frozen content IS the current content and a later check disputes
    its key: the regrade binds it and lowers the status, as before."""

    from contextlib import closing

    from learnloop.db.stores.source_service import insert_key_check, reference_content_hash
    from tests.source_service_fakes import loaded
    from tests.test_reference_gate_imports import _attempt, _bindings, _regrade, _status

    paths, repository, spans = gated_successor
    item_id, criterion = _verified_method_import(paths, repository, spans)
    attempt = _attempt(paths, repository, item_id, criterion=criterion)
    item = loaded(paths).practice_items[item_id]
    with closing(connect(repository.sqlite_path)) as connection:
        with connection:
            insert_key_check(connection, id="rkc_disputed", practice_item_id=item_id,
                             content_hash=reference_content_hash(item), key_status="disputed", rung="test",
                             trigger="verify", started_at="2099-01-01T00:00:00Z", created_at="2099-01-01T00:00:00Z")
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "unverified"
    assert len(_bindings(repository, attempt.attempt_id)) == 1


def test_f13_without_a_frozen_method_a_regrade_still_binds_the_current_content(gated_successor):
    from tests.test_reference_gate_imports import _attempt, _edit_key, _regrade, _status, _verified_import

    paths, repository, spans = gated_successor
    item_id = _verified_import(paths, repository, spans)
    attempt = _attempt(paths, repository, item_id)
    _edit_key(paths, repository, item_id)
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "unverified"
