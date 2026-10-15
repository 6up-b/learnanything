"""The chat frontend's C1a landed onto main: one protection, two text rules (Q16).

C1a's read model (``learner_context``) and router R2a's ``LearnerStateCardV1``
(``daily_plan.router_card``) both put the learner's past work in front of a
model. At the landing they read every predicate and protection from one
module, ``learnloop.learner_protection``: the withheld items (exam and
held-out material, reservations, cold checks and repair cold retries,
probes, items the vault cannot read; fail closed), each attempt's own
protection, held grades, the pinned revision with the required method its
contract froze, and the leakage rule for a statement written from protected
work. Each keeps its own text rule, a parameter: the card's G5
(``router_card.CardText``; its reader is the router model) and the chat's
``TextGuard``.

The method-explicit merge note is applied: the chat renders the pinned
question with the frozen method's instruction whole, exactly as the card does.
"""

from __future__ import annotations

import ast
import inspect
import json
from datetime import UTC, datetime

from learnloop import learner_protection as protection
from learnloop.daily_plan.policy import policy_for
from learnloop.daily_plan.router_card import CardGatherer
from learnloop.daily_plan.types import BlockCandidate, PlanState
from learnloop.learner_context import HELD_BACK, learning_context
from learnloop.router.card import STEM_LIMIT

from tests.daily_plan_fakes import MovableClock, iso, make_env, scheduled, seed_due
from tests.helpers import create_daily_plan_vault
from tests.test_method_explicit_landing import LONG, METHOD, SENTENCE, _graded_under_method
from tests.test_router_card import A, LAST, OWN_ANSWER, PAST, _attempt, _item

NOW = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
NOW_ISO = iso(NOW)
CAUSE = "CAUSE_STATEMENT_A_DIAGNOSER_WROTE_5120"
EXAM_CAUSE = "CAUSE_REVISED_FROM_AN_EXAM_ANSWER_7781"
GAP_WORDS = "LEARNER_WORDS_ABOUT_THE_EXAM_QUESTION_3307"


def _world(tmp_path, monkeypatch):
    """Two topics: lo_m1 (pi_a) and lo_m2 (pi_b, and pi_cold, held by an open cold retry)."""

    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects={"lo_m1": [], "lo_m2": []}, version=A)
    _item(paths, "pi_a", "lo_m1", prompt="Compute the determinant of A.", expected="kept")
    _item(paths, "pi_b", "lo_m2", prompt="Name a basis of R^2.", expected="e1, e2")
    _item(paths, "pi_cold", "lo_m2", prompt="Is this set a basis?", expected="no")
    clock = MovableClock()
    env = make_env(paths.root, [scheduled("pi_a", "lo_m1", forgetting_risk=0.6),
                                scheduled("pi_b", "lo_m2", forgetting_risk=0.6)], clock=clock, session_id="s1")
    for item in ("pi_a", "pi_b"):
        seed_due(env.repository, item, due=PAST, last=LAST)
    from learnloop.content.sources import exam_material as EM

    monkeypatch.setattr(EM, "exam_material",
                        lambda _vault, _repo: EM.ExamMaterial(material=EM.Material(), held_out=EM.Material()))
    env.policy = policy_for(env.vault, env.repository, session_id="s1", clock=clock)
    return env


def _cold_retry(env, item_id: str) -> None:
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO followup_tasks(id, kind, case_kind, case_ref, not_before, status, selected_item_id, "
            "learning_object_id, created_at, updated_at) VALUES ('fu_cold', 'cold_retry', 'diagnosis', 'case_1', ?, "
            "'pending', ?, 'lo_m2', ?, ?)",
            (iso(LAST), item_id, iso(LAST), iso(LAST)),
        )
        connection.commit()


def _version(env, hypothesis_id: str, episode: str, version: int, attempt_id: str, statement: str, at: str) -> None:
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO causal_hypotheses(id, episode_key, version, attempt_id, learning_object_id, cause_scope, "
            "statement, statement_normalized, status, evidence_json, created_at) "
            "VALUES (?, ?, ?, ?, 'lo_m1', 'learner_state', ?, ?, 'candidate', '{}', ?)",
            (hypothesis_id, episode, version, attempt_id, statement, statement.lower(), at),
        )
        connection.commit()


def _gap(env, gap_id: str, attempt_id: str, item_id: str, words: str) -> None:
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO learner_text_gaps(id, source_kind, source_id, attempt_id, practice_item_id, "
            "anchor_learning_object_id, learner_text, chooser, context_judge, kind, action, algorithm_version, "
            "pipeline_version, created_at) VALUES (?, 'tutor_question', ?, ?, ?, 'lo_m1', ?, 'context_model', 'tutor', "
            "'misconception', 'unplaced', ?, 'v1', ?)",
            (gap_id, f"q_{gap_id}", attempt_id, item_id, words, A, iso(LAST)),
        )
        connection.commit()


def _card_inputs(env):
    state = PlanState(plan_id="p", kind="normal", minutes_budget=25.0, minutes_left=25.0,
                      lane_minutes_left={"maintain": 10.0}, days_since_last_activity=0, streak_days=1,
                      current_block_id=None)
    feasible = [BlockCandidate(
        candidate_id="maintain:x", lane="maintain", action="maintain", subtype=None,
        learning_object_ids=("lo_m1", "lo_m2"), item_ids=("pi_a", "pi_b"), reading=None, est_minutes=4.0,
        planner_value=1.0, reason="review", annotations={"reason_code": "review", "reversible": True},
    )]
    return CardGatherer(env.vault, env.repository, clock=env.clock, session_id="s1").inputs(
        state, feasible, now_iso=NOW_ISO)


def _chat(env) -> dict:
    return learning_context(env.vault, env.repository, learning_object_ids=["lo_m1", "lo_m2"], now=NOW)


def _protected_world(tmp_path, monkeypatch):
    env = _world(tmp_path, monkeypatch)
    _attempt(env, "att_ok", "pi_a", "lo_m1", "2026-09-20T09:00:00Z", answer=OWN_ANSWER, correctness=1.0)
    _graded_under_method(env, "att_ok", "pi_a", prompt="Compute the determinant of A.", method=None)
    _attempt(env, "att_exam", "pi_a", "lo_m1", "2026-09-20T10:00:00Z", answer="EXAM_ANSWER_1", correctness=0.0,
             attempt_type="exam_attempt")
    _cold_retry(env, "pi_cold")
    _attempt(env, "att_cold", "pi_cold", "lo_m2", "2026-09-20T11:00:00Z", answer="COLD_ANSWER_2", correctness=0.0)
    _attempt(env, "att_gone", "pi_gone", "lo_m1", "2026-09-20T12:00:00Z", answer="GONE_ANSWER_3", correctness=1.0)
    return env


def test_the_card_and_the_chat_withhold_the_same_past_work_for_the_same_reasons(tmp_path, monkeypatch):
    """One authority: exam work, an item a cold retry holds and an item the
    vault no longer has keep their results and show no question and no
    answer in both readers, naming the same reason; ordinary work shows."""

    env = _protected_world(tmp_path, monkeypatch)
    card = {entry["attempt_id"]: entry for entry in _card_inputs(env).recent_work}
    chat = {entry["attempt_id"]: entry for entry in _chat(env)["recent_answer_traces"]}
    expected = {"att_ok": None, "att_exam": protection.WITHHELD_EXAM, "att_cold": protection.WITHHELD_COLD,
                "att_gone": protection.WITHHELD_UNKNOWN_ITEM}
    assert {attempt: card[attempt]["withheld"] for attempt in expected} == expected
    assert {attempt: chat[attempt]["withheld"] for attempt in expected} == expected
    for attempt in ("att_exam", "att_cold", "att_gone"):
        for entry in (card[attempt], chat[attempt]):
            assert entry["stem"] is None and entry["answer"] is None, (attempt, entry)
        assert card[attempt]["result"] == chat[attempt]["result"]
    assert card["att_ok"]["answer"] == chat["att_ok"]["answer"] == OWN_ANSWER
    assert card["att_ok"]["stem"] == chat["att_ok"]["stem"] == "Compute the determinant of A."
    text = json.dumps([card[attempt] for attempt in card])
    for planted in ("EXAM_ANSWER_1", "COLD_ANSWER_2", "GONE_ANSWER_3"):
        assert planted not in text


def test_both_readers_render_the_pinned_question_with_its_frozen_method(tmp_path, monkeypatch):
    """The method-explicit merge note: the chat's pinned question reads the
    contract's frozen ``required_method`` beside ``$.prompt`` and keeps its
    instruction whole within the stem limit, exactly as the card does. A
    contract that froze no method shows none."""

    env = _world(tmp_path, monkeypatch)
    _attempt(env, "att_method", "pi_a", "lo_m1", iso(LAST), answer=OWN_ANSWER, correctness=1.0)
    _graded_under_method(env, "att_method", "pi_a", prompt=LONG, method=METHOD)
    _attempt(env, "att_short", "pi_b", "lo_m2", "2026-09-21T09:00:00Z", answer="e1, e2", correctness=1.0)
    _graded_under_method(env, "att_short", "pi_b", prompt="Name a basis.", method=METHOD)
    _attempt(env, "att_plain", "pi_b", "lo_m2", "2026-09-22T09:00:00Z", answer="e2, e1", correctness=1.0)
    _graded_under_method(env, "att_plain", "pi_b", prompt="Name another basis.", method=None)
    card = {entry["attempt_id"]: entry for entry in _card_inputs(env).recent_work}
    chat = {entry["attempt_id"]: entry for entry in _chat(env)["recent_answer_traces"]}
    stem = chat["att_method"]["stem"]
    assert stem.endswith(" " + SENTENCE) and len(stem) <= STEM_LIMIT and stem.startswith("Let A be the 2 by 2")
    assert stem == card["att_method"]["stem"]
    assert chat["att_short"]["stem"] == card["att_short"]["stem"] == f"Name a basis. {SENTENCE}"
    assert chat["att_plain"]["stem"] == card["att_plain"]["stem"] == "Name another basis."


def test_a_statement_written_from_protected_work_is_withheld_by_both(tmp_path, monkeypatch):
    """The shared leakage rule. A cause whose episode was revised from an exam
    answer (its open head rests on ordinary work) and a learner's words about
    an exam answer keep their entries, never their words, in both readers."""

    env = _protected_world(tmp_path, monkeypatch)
    _version(env, "hyp_v1", "ep_mixed", 1, "att_exam", "first draft", "2026-09-20T10:05:00Z")
    _version(env, "hyp_v2", "ep_mixed", 2, "att_ok", EXAM_CAUSE, "2026-09-20T10:06:00Z")
    _gap(env, "gap_exam", "att_exam", "pi_a", GAP_WORDS)
    inputs = _card_inputs(env)
    card = {entry.get("hypothesis_id") or entry["kind"]: entry for entry in inputs.open_hypotheses}
    assert card["hyp_v2"]["statement"] is None and card["hyp_v2"]["withheld"] == protection.WITHHELD_EXAM
    [gap] = [entry for entry in inputs.open_hypotheses if entry["kind"] == "learner_named_misconception"]
    assert gap["statement"] is None and gap["withheld"] == protection.WITHHELD_EXAM
    context = _chat(env)
    [cause] = [entry for entry in context["open_hypotheses"] if entry.get("hypothesis_id") == "hyp_v2"]
    assert cause["statement"] is None and cause["statement_note"] == f"withheld: {protection.WITHHELD_EXAM}"
    [chat_gap] = [entry for entry in context["open_learner_text_gaps"] if entry["gap_id"] == "gap_exam"]
    assert chat_gap["learner_text"] is None
    assert chat_gap["learner_text_note"] == f"withheld: {protection.WITHHELD_EXAM}"
    for planted in (EXAM_CAUSE, GAP_WORDS):
        assert planted not in json.dumps(list(inputs.open_hypotheses)) and planted not in json.dumps(context)


def test_the_text_rule_is_each_readers_own(tmp_path, monkeypatch):
    """Same protection, different readers. The router model reads a cause a
    diagnoser wrote and an unpinned answer (G5); the chat holds the cause back
    until a write-time record says what it was written from, and an answer
    whose revision is not recorded."""

    env = _world(tmp_path, monkeypatch)
    _attempt(env, "att_a", "pi_a", "lo_m1", iso(LAST), answer="UNPINNED_ANSWER_4402", correctness=0.0)
    _version(env, "hyp_open", "ep_open", 1, "att_a", CAUSE, iso(LAST))
    inputs = _card_inputs(env)
    [cause] = [entry for entry in inputs.open_hypotheses if entry.get("hypothesis_id") == "hyp_open"]
    [work] = [entry for entry in inputs.recent_work if entry["attempt_id"] == "att_a"]
    assert cause["statement"] == CAUSE and cause["withheld"] is None
    assert work["answer"] == "UNPINNED_ANSWER_4402" and work["stem"] is None
    assert work["stem_note"] == protection.STEM_UNRECORDED
    context = _chat(env)
    [chat_cause] = [entry for entry in context["open_hypotheses"] if entry.get("hypothesis_id") == "hyp_open"]
    [trace] = [entry for entry in context["recent_answer_traces"] if entry["attempt_id"] == "att_a"]
    assert chat_cause["statement"] is None and chat_cause["statement_note"] == HELD_BACK
    assert trace["answer"] is None and trace["stem"] is None and trace["withheld"] is None
    assert trace["stem_note"] == protection.STEM_UNRECORDED


def test_a_teach_back_on_an_item_a_cold_check_holds_is_never_summarized(tmp_path):
    """R2c's summaries read the same protection: a teach-back whose item an
    open cold retry holds is not summarized (nothing is sent)."""

    from learnloop.daily_plan import router_teach_back as tb

    from tests.router_mixture_helpers import mixture_env
    from tests.router_model_fakes import fake_runtime
    from tests.test_daily_plan_build import _wide_items
    from tests.test_router_r2c_teach_back import _summary_llm, _teach_back

    calls: list = []
    runtime = fake_runtime(llm=_summary_llm(calls))
    env = mixture_env(tmp_path, runtime, items=_wide_items())
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO followup_tasks(id, kind, case_kind, case_ref, not_before, status, selected_item_id, "
            "learning_object_id, created_at, updated_at) VALUES ('fu_tb', 'cold_retry', 'diagnosis', 'case_tb', "
            "'2026-10-01T00:00:00Z', 'pending', 'pi_m1a', 'lo_m1', '2026-10-01T00:00:00Z', '2026-10-01T00:00:00Z')"
        )
        connection.commit()
    assert tb.summarize(env.vault, env.repository, _teach_back(env), runtime=runtime) is None
    assert calls == []


def _code(module) -> tuple[set[str], list[str]]:
    """The names a module's code uses and its string constants, docstrings aside."""

    tree = ast.parse(inspect.getsource(module))
    docstrings = {id(node.body[0].value) for node in ast.walk(tree)
                  if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                  and node.body and isinstance(node.body[0], ast.Expr)
                  and isinstance(node.body[0].value, ast.Constant)}
    names: set[str] = set()
    strings: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.alias):
            names.add(node.name.rsplit(".", 1)[-1])
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            strings.append(node.value)
    return names, strings


def test_no_reader_keeps_a_protection_of_its_own():
    """One authority. The chat's read model re-exports the shared predicates
    (the same objects); neither reader nor R2c's summaries define or query a
    protection of their own (no exam predicate, reservation, cold-check,
    probe, held-grade or pinned-contract read outside ``learner_protection``)."""

    import learnloop.daily_plan.router_card as card_module
    import learnloop.daily_plan.router_teach_back as teach_back_module
    import learnloop.learner_context as chat_module

    for name in ("Withheld", "withheld_items", "protection_issues", "WITHHELD_EXAM", "WITHHELD_UNREADABLE",
                 "SNAPSHOT_UNSETTLED", "PROTECTION_UNKNOWN", "STEM_UNRECORDED"):
        assert getattr(chat_module, name) is getattr(protection, name), name
    owned_names = {"item_exam_status", "exam_material", "held_out_items", "reserved_exam_pool_item_ids",
                   "reserved_assessment_surfaces", "open_followup_tasks_of_kind"}
    # The protection's reads (the chat still reads remediation episodes for
    # the repairs tried, not for a cold item; R2c reads live grading evidence
    # for a grade's revision, not for its pinned contract).
    owned_sql = ("probe_presentations", "assessment_contract_version_id", "followup_tasks", "cold_item_id")
    for module in (card_module, chat_module, teach_back_module):
        names, strings = _code(module)
        assert not names & owned_names, (module.__name__, names & owned_names)
        assert not [needle for needle in owned_sql if any(needle in value for value in strings)], module.__name__
    # Held grades: both readers ask the shared reader (``PastWork.held``), which
    # asks THE predicate (``held_grades``, itself the one authority R2c reads).
    for module in (card_module, chat_module):
        assert "held_for_review_attempts" not in _code(module)[0], module.__name__
    assert "_withheld_items" not in _code(teach_back_module)[0]
    defined = {node.name for module in (card_module, chat_module)
               for node in ast.walk(ast.parse(inspect.getsource(module)))
               if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    assert not defined & {"_result", "_pins", "_pinned_stems", "_exam_or_withheld", "_withheld_reason",
                          "_frozen_method", "_evidence_attempts", "attempt_reason_of", "withheld_items",
                          "protection_issues", "Withheld"}
    assert "learner_protection" in inspect.getsource(teach_back_module)
