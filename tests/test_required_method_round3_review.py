"""Method-explicit items, the round-3 review (stage method-explicit-3, Codex
job 20261014-193301-X2dw9X): eight findings on ``e96075e94..5392d7c3c``.

* F1: the answer key's identity (``reference_content_hash``) ignored the
  required method once round 3 stopped storing the instruction in the
  statement, so changing only the method kept a check of a different
  question (and a dispute of the new method reached the old contract);
* F2: the tutor's practice tool withheld a listed item on its stored stem
  only, then rendered the instruction, which can carry the protected answer;
* F3: exam review, adjudication and the diagnoser (its history and the
  attempt diagnosed) rendered today's item, not the question the answer was
  given;
* F4: prompt-only readers (the offline review harness and its spot check,
  the Inspector, the practice-index JSON, the source tutor's verifier,
  teach-back authoring, judges and model contexts) showed the bare stem;
* F5: a long stem clipped together with its instruction cut the instruction;
* F6: resuming a job whose every verdict was ledgered still needed a judge;
* F7: a resume estimated its unfinished work from the parent's stem;
* F8: an unrelated later revision that inherited a default rubric
  unverified a historical contract that reconstructs exactly.

Fakes only; no network.
"""

from __future__ import annotations

import hashlib
import json
from contextlib import closing
from types import SimpleNamespace

import pytest
import yaml

from learnloop.ai.spend import SpendCaps
from learnloop.db.connection import connect
from learnloop.vault.loader import load_vault

from tests.helpers import create_basic_vault

ITEM = "pi_svd_define_001"
METHOD = "cofactor expansion"
SENTENCE = "Use cofactor expansion in your answer."
#: A statement well past every model context's character budget (400 to 700).
LONG_STEM = "Let A be the 4x4 matrix with entries a_ij = i + 2j. " * 30 + "Compute det(A)."


def _upsert(paths, item_id: str, **fields) -> None:
    from learnloop.vault.writer import upsert_practice_item

    data = load_vault(paths.root).practice_items[item_id].model_dump(mode="json")
    data.update(fields)
    upsert_practice_item(paths.root, data)


# -- F1: the answer key names the required method ------------------------------------------------


def test_f1_the_reference_key_identity_carries_the_required_method(tmp_path):
    """The method's name and graded criteria are part of the key; who decided
    it and the target it links are not; an item without one keeps its hash."""

    from learnloop.db.stores.source_service import _plain, reference_content_hash
    from learnloop.vault.models import RequiredMethod

    item = load_vault(create_basic_vault(tmp_path / "vault").root).practice_items[ITEM]
    unchanged = hashlib.sha256(json.dumps(_plain({
        "prompt": item.prompt, "expected_answer": item.expected_answer, "grading_rubric": item.grading_rubric,
    }), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
    assert reference_content_hash(item) == unchanged

    def requiring(**fields):
        return item.model_copy(update={"required_method": RequiredMethod(**fields)})

    induction = requiring(name="mathematical induction", criterion_ids=["correctness"])
    generating = requiring(name="generating functions", criterion_ids=["correctness"])
    ungraded = requiring(name="mathematical induction", criterion_ids=[])
    decided = requiring(name="mathematical  induction", criterion_ids=["correctness"], statement="source",
                        decided_by="owner", learning_object_id=item.learning_object_id)
    hashes = [reference_content_hash(value) for value in (item, induction, generating, ungraded)]
    assert len(set(hashes)) == 4
    assert reference_content_hash(decided) == reference_content_hash(induction)


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


def _method_import(paths, repository, spans, name: str) -> tuple[str, str]:
    """A verified textbook exercise whose (owner-decided) required method is
    ``name``, its key checked for exactly that question."""

    from learnloop.db.stores.source_service import reference_content_hash
    from tests.source_service_fakes import loaded
    from tests.test_reference_gate_imports import _verified_import
    from tests.test_required_method_rereview import _check

    item_id = _verified_import(paths, repository, spans)
    item = loaded(paths).practice_items[item_id]
    criterion = loaded(paths).rubric_for_item(item).criteria[0].id
    _upsert(paths, item_id, required_method={"name": name, "criterion_ids": [criterion], "statement": "source",
                                             "decided_by": "owner"})
    _check(repository, item_id, reference_content_hash(loaded(paths).practice_items[item_id]), "book_solution",
           "rkc_method_checked", "2026-01-01T00:00:00Z")
    return item_id, criterion


def _override(paths, repository, item_id: str, name: str, criterion: str) -> None:
    from learnloop.content.proposals.proposals import accept_items
    from learnloop.content.proposals.required_method_override import propose_required_method_override

    proposed = propose_required_method_override(load_vault(paths.root), repository, item_id, name=name,
                                                criterion_ids=[criterion])
    accept_items(paths.root, proposed["proposal_id"])


def test_f1_changing_only_the_required_method_needs_a_fresh_check(gated_successor):
    """The verify's scenario: a verified exercise requiring induction is
    changed to require generating functions, its statement, key and rubric
    untouched. The induction question's check never verifies the new one."""

    from learnloop.db.stores.source_service import effective_key_status, reference_status_for_item
    from tests.source_service_fakes import loaded

    paths, repository, spans = gated_successor
    item_id, criterion = _method_import(paths, repository, spans, "mathematical induction")
    before = loaded(paths).practice_items[item_id]
    with closing(connect(repository.sqlite_path)) as connection:
        assert reference_status_for_item(connection, before) == "verified"
    _override(paths, repository, item_id, "generating functions", criterion)
    after = loaded(paths).practice_items[item_id]
    assert after.required_method.name == "generating functions"
    assert (after.prompt, after.expected_answer, after.grading_rubric) == (
        before.prompt, before.expected_answer, before.grading_rubric)
    with closing(connect(repository.sqlite_path)) as connection:
        assert effective_key_status(connection, after) == "changed_since_check"
        assert reference_status_for_item(connection, after) == "unverified"


def test_f1_a_dispute_of_the_new_method_never_reaches_the_contract_frozen_under_the_old(gated_successor):
    """The converse: an answer graded under induction (its contract recorded
    the key it presented) stays verified when the generating-functions
    revision's key is disputed later."""

    from learnloop.db.stores.source_service import reference_content_hash
    from tests.source_service_fakes import loaded
    from tests.test_reference_gate_imports import _attempt, _bindings, _regrade, _status
    from tests.test_required_method_rereview import _check

    paths, repository, spans = gated_successor
    item_id, criterion = _method_import(paths, repository, spans, "mathematical induction")
    attempt = _attempt(paths, repository, item_id, criterion=criterion)
    assert _status(repository, attempt.attempt_id) == "verified"
    # (A proposal is refused once the learning object has attempts: the field is written directly.)
    _upsert(paths, item_id, required_method={"name": "generating functions", "criterion_ids": [criterion],
                                             "statement": "source", "decided_by": "owner"})
    _check(repository, item_id, reference_content_hash(loaded(paths).practice_items[item_id]), "disputed",
           "rkc_new_method_disputed", "2099-01-01T00:00:00Z")
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "verified"
    assert _bindings(repository, attempt.attempt_id) == []


# -- F2: withholding reads the rendered question --------------------------------------------------


def test_f2_an_answer_carried_only_by_the_required_method_is_withheld(tmp_path):
    """The bound question's expected answer is "cofactor expansion"; the
    listed item's stem is "Compute det(A)." and it requires cofactor
    expansion. The stem alone leaks nothing; the question as rendered does."""

    from learnloop.instructional.tools import _practice_view, _Withhold
    from learnloop.vault.models import RequiredMethod

    vault = load_vault(create_basic_vault(tmp_path / "vault").root)
    item = vault.practice_items[ITEM]
    item.prompt, item.expected_answer = "Compute det(A).", METHOD
    listed = {"items": [{"practice_item_id": ITEM}]}
    withhold = _Withhold(vault, SimpleNamespace(item_id=ITEM))
    assert len(_practice_view(vault, listed, withhold)["items"]) == 1 and withhold.withheld == 0
    item.required_method = RequiredMethod(name=METHOD, criterion_ids=["correctness"])
    withhold = _Withhold(vault, SimpleNamespace(item_id=ITEM))
    view = _practice_view(vault, listed, withhold)
    assert view["items"] == [] and withhold.withheld == 1
    assert SENTENCE not in json.dumps(view)


# -- F3: readers of a recorded answer render the question it was given ----------------------------

#: (method when answered, method now): cleared since, renamed since, added since.
HISTORY_CASES = {
    "clear": (METHOD, None),
    "rename": (METHOD, "row reduction"),
    "add": (None, METHOD),
}


@pytest.fixture(params=sorted(HISTORY_CASES))
def answered(request, tmp_path):
    """A real graded attempt (``apply_attempt``, its contract frozen) on the
    item, its required method changed after the answer."""

    import learnloop_sidecar.handlers  # noqa: F401 - register methods
    from learnloop_sidecar.context import SidecarContext
    from tests.test_durable_promotion_arms import _failure
    from tests.test_km2_write_path import build_mvp07_vault

    then, now = HISTORY_CASES[request.param]
    paths = build_mvp07_vault(tmp_path / "vault")
    stem = load_vault(paths.root).practice_items[ITEM].prompt
    if then is not None:
        _upsert(paths, ITEM, required_method={"name": then, "criterion_ids": ["correctness"]})
    ctx = SidecarContext()
    ctx.load(paths.root)
    _failure(ctx.vault, ctx.repository, attempt_id="att_answered")
    _upsert(paths, ITEM, required_method={"name": now, "criterion_ids": ["correctness"]} if now else None)
    ctx.reload()
    given = f"{stem}\n\nUse {then} in your answer." if then else stem
    yield SimpleNamespace(ctx=ctx, given=given, now=now, stem=stem)
    ctx.exam_grading.shutdown()
    ctx.ingest_jobs.shutdown()


def test_f3_adjudication_shows_the_question_the_answer_was_given(answered):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY["adjudication.queue"]
    result = spec.handler(answered.ctx, spec.params_model.model_validate({}))
    [case] = [case for case in result["cases"] if case["attemptId"] == "att_answered"]
    assert case["prompt"] == answered.given


def test_f3_the_diagnosers_history_and_current_attempt_read_the_question_given(answered):
    from learnloop.diagnosis.split.history import VaultHistoryStore
    from learnloop.diagnosis.split.live import current_attempt_for

    vault, repository = answered.ctx.require_vault()
    history = VaultHistoryStore(vault, repository).attempt("att_answered")
    assert history is not None and history.item_prompt == answered.given
    attempt = repository.fetch_practice_attempt("att_answered")
    current = current_attempt_for(vault, attempt, {}, repository)
    assert current is not None and current.item_prompt == answered.given


def test_f3_exam_review_shows_the_question_the_answer_was_given(answered):
    from learnloop_sidecar.handlers.exams import _report_dto

    vault, repository = answered.ctx.require_vault()
    with closing(connect(repository.sqlite_path)) as connection:
        with connection:
            connection.execute("INSERT INTO exam_sessions (id, goal_id, status, item_order_json, started_at, "
                               "updated_at) VALUES ('exs_1', 'goal_linear_algebra_ml', 'completed', ?, "
                               "'2026-10-14T00:00:00Z', '2026-10-14T00:00:00Z')", (json.dumps([ITEM]),))
            connection.execute("INSERT INTO exam_answers (id, session_id, practice_item_id, answer_md, rubric_score, "
                               "attempt_id, answered_at, updated_at) VALUES ('exa_1', 'exs_1', ?, 'x', 0, "
                               "'att_answered', '2026-10-14T00:00:00Z', '2026-10-14T00:00:00Z')", (ITEM,))
    report = _report_dto(vault, repository, {"session_id": "exs_1", "items": [{"practice_item_id": ITEM}]})
    [outcome] = report["item_outcomes"]
    assert outcome["prompt"] == answered.given
    blocks = (outcome["presentation"] or {}).get("blocks") or []
    rendered = [block["markdown"] for block in blocks if block["kind"] in ("prompt", "required_method_instruction")]
    assert "\n\n".join(rendered) == answered.given


# -- F4: prompt-only readers render the instruction -----------------------------------------------


def test_f4_model_readers_and_review_exports_render_the_instruction(tmp_path):
    """The offline review harness's judge and planted-error writer, the
    practice-index result, teach-back authoring and the gap judge: the
    statement, then the instruction; an item without a method exactly as
    before."""

    from learnloop.diagnosis.offline_review.planted import _item_payload
    from learnloop.diagnosis.text_gaps.judges import needed_context
    from learnloop.vault.models import RequiredMethod

    vault = load_vault(create_basic_vault(tmp_path / "vault").root)
    item = vault.practice_items[ITEM]
    lo = vault.learning_objects[item.learning_object_id]
    assert _item_payload(vault, item)["prompt"] == item.prompt
    assert needed_context(vault, item, lo)["item"]["prompt"] == item.prompt
    item.required_method = RequiredMethod(name=METHOD, criterion_ids=["correctness"])
    presented = f"{item.prompt}\n\n{SENTENCE}"
    assert _item_payload(vault, item)["prompt"] == presented
    assert needed_context(vault, item, lo)["item"]["prompt"] == presented


def test_f4_the_teach_back_author_reads_the_task_as_it_was_set(tmp_path):
    from learnloop.tutor.teach_back import _fallback_teach_back_authoring
    from learnloop.vault.models import RequiredMethod

    vault = load_vault(create_basic_vault(tmp_path / "vault").root)
    item = vault.practice_items[ITEM]
    criteria = [{"id": "correctness", "description": "Correct.", "points": 4.0}]
    assert SENTENCE not in _fallback_teach_back_authoring(item, criteria, quest_sentence=None).prompt_md
    item.required_method = RequiredMethod(name=METHOD, criterion_ids=["correctness"])
    authored = _fallback_teach_back_authoring(item, criteria, quest_sentence=None)
    assert f"{item.prompt}\n\n{SENTENCE}" in authored.prompt_md


def test_f4_the_practice_index_result_presents_the_question(tmp_path):
    from learnloop.practice_index import retrieval
    from learnloop.vault.models import RequiredMethod

    vault = load_vault(create_basic_vault(tmp_path / "vault").root)
    item = vault.practice_items[ITEM]
    item.required_method = RequiredMethod(name=METHOD, criterion_ids=["correctness"])
    item.prompt = LONG_STEM
    [candidate] = retrieval._candidate_context(vault, [ITEM])
    assert candidate["prompt"].endswith(SENTENCE) and len(candidate["prompt"]) <= retrieval.CANDIDATE_PROMPT_CHARS


# -- F5: a long stem keeps the whole instruction --------------------------------------------------


def test_f5_the_practice_tool_keeps_the_instruction_of_a_long_stem(tmp_path):
    from learnloop.instructional.tools import PROMPT_CHARS, _practice_view, _Withhold
    from learnloop.vault.models import RequiredMethod

    vault = load_vault(create_basic_vault(tmp_path / "vault").root)
    item = vault.practice_items[ITEM]
    item.prompt = LONG_STEM
    listed = {"items": [{"practice_item_id": ITEM}]}
    plain = _practice_view(vault, listed, _Withhold(vault, SimpleNamespace(item_id=None)))["items"][0]["prompt"]
    assert len(plain) == PROMPT_CHARS and plain.endswith("…")
    item.required_method = RequiredMethod(name=METHOD, criterion_ids=["correctness"])
    shown = _practice_view(vault, listed, _Withhold(vault, SimpleNamespace(item_id=None)))["items"][0]["prompt"]
    assert shown.endswith(f"… {SENTENCE}") and len(shown) <= PROMPT_CHARS
    assert shown.startswith(plain[:100])


def test_f5_the_source_tutors_verifier_reads_the_whole_instruction(tmp_path):
    """The item-bound tutor's verification prompt: the question as presented
    (it was the bare stem), the statement shortened, never the instruction."""

    from tests.source_retrieval_fakes import loaded
    from tests.test_source_retrieval_tutor import CitingTutor, ask, provider, setup

    paths, repository = setup(tmp_path)
    item = loaded(paths).practice_items["pi_eigen_1"]
    criterion = loaded(paths).rubric_for_item(item).criteria[0].id
    _upsert(paths, "pi_eigen_1", prompt=LONG_STEM,
            required_method={"name": METHOD, "criterion_ids": [criterion]})
    span_provider, llm = provider()
    ask(paths, repository, CitingTutor(), span_provider=span_provider)
    [context] = [context for purpose, context in llm.calls if purpose == "source_rerank"]
    assert context["practice_question"].endswith(SENTENCE)
    assert len(context["practice_question"]) <= 700


def test_f5_find_sources_keeps_the_instruction_of_a_long_stem(tmp_path):
    from learnloop.source_retrieval.find_sources import find_sources
    from tests.pf_fakes import prompt_context
    from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, loaded

    class Recording(FakeServiceLLM):
        def __init__(self):
            super().__init__()
            self.contexts = []

        def complete(self, request):
            self.contexts.append(prompt_context(request.prompt))
            return super().complete(request)

    paths, repository, _spans = build_textbook_vault(tmp_path / "vault")
    item = loaded(paths).practice_items["pi_eigen_1"]
    criterion = loaded(paths).rubric_for_item(item).criteria[0].id
    _upsert(paths, "pi_eigen_1", prompt=LONG_STEM, required_method={"name": METHOD, "criterion_ids": [criterion]})
    llm = Recording()
    find_sources(loaded(paths), repository, "eigenvalues characteristic polynomial", policy="assisted_practice",
                 item=loaded(paths).practice_items["pi_eigen_1"], scope="teaching", verify=True,
                 rerank_client=llm)
    questions = [context.get("practice_question") for context in llm.contexts if context.get("practice_question")]
    assert questions and all(question.endswith(SENTENCE) and len(question) <= 700 for question in questions)


# -- F6/F7: resume needs no judge for recorded verdicts, and is estimated from what is persisted -----


def _needs_bwrap():
    from learnloop.content.authoring.pf_sandbox import sandbox_available

    if not sandbox_available():
        pytest.skip("bubblewrap is not installed")


def test_f6_a_job_whose_every_verdict_is_recorded_publishes_without_a_judge(tmp_path, monkeypatch):
    """The run stops after the last verdict is ledgered, before publication.
    The rerun plans no judgment and publishes from the ledger, even with no
    judge available: none is resolved."""

    from learnloop.ai.errors import AIInterrupted
    from learnloop.ops import pf_generation
    from tests.pf_fakes import clients, enable_pf
    from tests.test_pf_generation import rows, run
    from tests.test_required_method_authority import VARIANT_CONSISTENT, StatementDecider, _pf_method_vault
    from tests.test_required_method_reopened import _mint_status

    _needs_bwrap()
    repository, paths = _pf_method_vault(tmp_path)
    enable_pf(paths.root, max_published_per_day=5)
    original = pf_generation.publish_selected

    def stopped(*args, **kwargs):
        raise AIInterrupted("stopped after the last verdict, before publication")

    monkeypatch.setattr(pf_generation, "publish_selected", stopped)
    judge = StatementDecider(VARIANT_CONSISTENT)
    first = run(paths, publish=True, select=2, fakes=clients(required_method_judge=judge))
    assert first["status"] == "cancelled" and len(judge.calls) == 2
    monkeypatch.setattr(pf_generation, "publish_selected", original)
    resolved = []

    def unavailable(*args, **kwargs):
        resolved.append(True)
        return None

    monkeypatch.setattr(pf_generation, "resolve_statement_judge", unavailable)
    dry = run(paths, publish=True, select=2, dry_run=True, fakes=clients())
    [plan] = dry["plan"]
    assert plan["resume"] == {**plan["resume"], "stage": "judgment", "missing_judgments": 0}
    assert "required_method_judgment" not in plan
    second = run(paths, publish=True, select=2, fakes=clients())
    assert second["status"] == "complete", second.get("reason")
    [family] = second["families"]
    assert family["status"] == "complete", family
    assert len(family.get("published_item_ids", [])) == 2
    assert resolved == []
    assert _mint_status(repository) == ["admitted"]
    assert len(rows(repository, "status='published'")) == 2


def _stretch_stem(repository, candidate_id: str, stem: str) -> None:
    with closing(connect(repository.sqlite_path)) as connection:
        with connection:
            payload = json.loads(connection.execute("SELECT payload_json FROM pf_candidates WHERE id=?",
                                                    (candidate_id,)).fetchone()[0])
            payload["stem"] = stem
            connection.execute("UPDATE pf_candidates SET payload_json=? WHERE id=?",
                               (json.dumps(payload, sort_keys=True), candidate_id))


def test_f7_a_resume_is_estimated_from_the_persisted_unfinished_stem(tmp_path):
    """A selected variant much longer than its parent waits for its
    judgment. Its estimate is the variant's, and a token cap between the
    parent-based and the variant-based estimate refuses the plan."""

    from learnloop.ai.errors import AIProviderUnavailable
    from learnloop.content.proposals.method_statement_judge import planned_tokens
    from tests.pf_fakes import clients, enable_pf
    from tests.test_pf_generation import rows, run
    from tests.test_required_method_authority import VARIANT_CONSISTENT, StatementDecider, _pf_method_vault
    from tests.test_required_method_rereview import FailingOnceDecider

    _needs_bwrap()
    repository, paths = _pf_method_vault(tmp_path)
    enable_pf(paths.root, max_published_per_day=5)
    first = run(paths, publish=True, select=2, fakes=clients(
        required_method_judge=FailingOnceDecider(VARIANT_CONSISTENT, AIProviderUnavailable("timed out"))))
    [family] = first["families"]
    assert family["status"] == "judgment_incomplete"
    [waiting] = rows(repository, "status='selected'")
    long_stem = "Solve for x, showing each substitution step: " + "3x + 5 = 20 and 2y - x = 1; " * 100
    _stretch_stem(repository, waiting["id"], long_stem)
    parent = load_vault(paths.root).practice_items["pi_linear_001"]
    by_parent = planned_tokens("variant", parent.prompt, "substitution")
    by_variant = planned_tokens("variant", long_stem, "substitution")
    assert by_variant > by_parent + 1000
    fakes = clients(required_method_judge=StatementDecider(VARIANT_CONSISTENT))
    roomy = run(paths, publish=True, select=2, dry_run=True, fakes=fakes)
    [plan] = roomy["plan"]
    assert plan["required_method_judgment"]["calls"] == 1
    assert plan["required_method_judgment"]["tokens"] == by_variant
    between = SpendCaps(max_candidates=100, max_pairs=2000, max_calls=10, max_total_tokens=(by_parent + by_variant) // 2,
                        max_estimated_usd=10_000)
    capped = run(paths, publish=True, select=2, dry_run=True, caps=between, fakes=fakes)
    assert capped["status"] == "over_budget", capped.get("reason")


def test_f7_a_selection_to_finish_is_estimated_from_its_survivors(tmp_path):
    """A selection persisted without its marker: the selection judge's
    request is estimated from the persisted survivors, not copies of the
    parent's stem."""

    from learnloop.ai.errors import AIProviderUnavailable
    from tests.pf_fakes import clients, enable_pf
    from tests.test_pf_generation import run
    from tests.test_required_method_authority import VARIANT_CONSISTENT, StatementDecider, _pf_method_vault
    from tests.test_required_method_reopened import FailingDecider
    from tests.test_required_method_round3 import _family_rows

    _needs_bwrap()
    repository, paths = _pf_method_vault(tmp_path)
    enable_pf(paths.root, max_published_per_day=5)
    run(paths, publish=True, select=2, fakes=clients(required_method_judge=FailingDecider(
        AIProviderUnavailable("timed out"))))
    fakes = clients(required_method_judge=StatementDecider(VARIANT_CONSISTENT))
    survivors = [row for row in _family_rows(repository) if row["status"] in ("selected", "not_selected")]
    [first, *rest] = survivors
    # The partial state F22 resumes: one selection written without its marker.
    with closing(connect(repository.sqlite_path)) as connection:
        with connection:
            selection = json.loads(first["selection_json"])
            for marker in ("selected_order", "selection_complete"):
                selection.pop(marker, None)
            connection.execute("UPDATE pf_candidates SET selection_json=? WHERE id=?",
                               (json.dumps(selection, sort_keys=True), first["id"]))
            for row in rest:
                connection.execute("UPDATE pf_candidates SET status='survivor', selection_json=NULL WHERE id=?",
                                   (row["id"],))
    short = run(paths, publish=True, select=2, dry_run=True, fakes=fakes)
    [short_plan] = short["plan"]
    assert short_plan["resume"]["stage"] == "selection"
    for row in survivors:
        _stretch_stem(repository, row["id"], "Solve for x by substitution: " + "x + 1 = 2; " * 120)
    long = run(paths, publish=True, select=2, dry_run=True, fakes=fakes)
    [long_plan] = long["plan"]
    grown = long_plan["roles"]["selection"]["per_call_tokens"] - short_plan["roles"]["selection"]["per_call_tokens"]
    assert grown >= len(survivors) * 1000 // 4


# -- F8: only a revision of the graded question can establish an inherited default ----------------


def _write_default(paths, mode: str, rubric: dict) -> None:
    changed = json.loads(json.dumps(rubric))
    for criterion in changed["criteria"]:
        criterion["description"] = "Changed default: " + criterion["description"]
    (paths.root / "rubrics").mkdir(exist_ok=True)
    (paths.root / "rubrics" / f"{mode}.yaml").write_text(yaml.safe_dump({
        "schema_version": 1, "id": f"default_{mode}", "applies_to": {"practice_mode": mode}, "rubric": changed,
    }, sort_keys=False), encoding="utf-8")


def _snapshot(repository, data: dict, created_at: str) -> str:
    item_json = json.dumps(data, sort_keys=True)
    digest = hashlib.sha256(item_json.encode("utf-8")).hexdigest()
    with closing(connect(repository.sqlite_path)) as connection:
        with connection:
            connection.execute("INSERT OR IGNORE INTO practice_item_snapshots(content_hash, practice_item_id, "
                               "item_json, created_at) VALUES (?, ?, ?, ?)",
                               (digest, data["id"], item_json, created_at))
    return digest


def _historical_inline_attempt(gated_successor):
    from tests.source_service_fakes import loaded
    from tests.test_reference_gate_imports import _attempt, _status
    from tests.test_required_method_rereview import _make_historical

    paths, repository, spans = gated_successor
    item_id, criterion = _method_import(paths, repository, spans, "mathematical induction")
    item = loaded(paths).practice_items[item_id]
    assert item.grading_rubric is not None
    attempt = _attempt(paths, repository, item_id, criterion=criterion)
    assert _status(repository, attempt.attempt_id) == "verified"
    _make_historical(repository, attempt.attempt_id)
    _write_default(paths, item.practice_mode, item.grading_rubric.model_dump(mode="json"))
    return paths, repository, item, attempt


def test_f8_an_unrelated_later_revision_never_unverifies_a_historical_inline_contract(gated_successor):
    """The verify's reproduction: a later snapshot of the same item with a
    completely different question and an inherited rubric."""

    from tests.test_reference_gate_imports import _bindings, _regrade, _status

    paths, repository, item, attempt = _historical_inline_attempt(gated_successor)
    unrelated = {**item.model_dump(mode="json"), "prompt": "A different question entirely.",
                 "expected_answer": "Something else.", "grading_rubric": None}
    _snapshot(repository, unrelated, "2099-01-01T00:00:00Z")
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "verified"
    assert _bindings(repository, attempt.attempt_id) == []


def test_f8_a_revision_of_the_graded_question_that_inherited_still_fails_closed(gated_successor):
    """Control: a recorded revision of the SAME question with no rubric of its
    own may be the one graded, under a default nobody can recover."""

    from tests.test_reference_gate_imports import _bindings, _regrade, _status

    paths, repository, item, attempt = _historical_inline_attempt(gated_successor)
    _snapshot(repository, {**item.model_dump(mode="json"), "grading_rubric": None}, "2099-01-01T00:00:00Z")
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "unverified"
    [binding] = _bindings(repository, attempt.attempt_id)
    assert "graded_revision=ambiguous_default" in binding["rationale"]


def test_f8_the_attempt_time_revision_settles_it(gated_successor):
    """With the attempt's selection receipt (its candidate's snapshot, at or
    before the attempt) pinning the inline revision, a same-question
    revision that inherited later never unverifies it."""

    from tests.test_reference_gate_imports import _bindings, _regrade, _status

    paths, repository, item, attempt = _historical_inline_attempt(gated_successor)
    pinned = _snapshot(repository, item.model_dump(mode="json"), "2000-01-01T00:00:00Z")
    _snapshot(repository, {**item.model_dump(mode="json"), "grading_rubric": None}, "2099-01-01T00:00:00Z")
    with closing(connect(repository.sqlite_path)) as connection:
        with connection:
            connection.execute("UPDATE practice_attempts SET scheduler_candidate_id='cand_pinned' WHERE id=?",
                               (attempt.attempt_id,))
            connection.execute(
                "INSERT INTO decision_features (id, decision_id, decision_type, ability_vector_json, "
                "item_demand_vector_json, context_json, algorithm_version, created_at) VALUES "
                "('df_pinned', 'cand_pinned', 'selection', '{}', ?, '{}', 'test', '2000-01-01T00:00:00Z')",
                (json.dumps({"content_hash": pinned}),))
    _regrade(paths, repository, attempt.attempt_id)
    assert _status(repository, attempt.attempt_id) == "verified"
    assert _bindings(repository, attempt.attempt_id) == []
