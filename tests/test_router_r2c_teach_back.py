"""Router R2c: teach-back dialogues summarized into the card's typed evidence (spec §15.1).

After the grader has graded a teach-back dialogue, the router LLM condenses
it (what was explained correctly, what was missing or wrong, the learner's
own words); the summary enters the next card as typed evidence with its
source attempt, citable by the LLM. Never on exam or reserved material; the
summarizer sees the transcript, the topic and the grade's word only; it acts
only where the mixture serves.
"""

from __future__ import annotations

from learnloop import learner_protection as protection
from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION
from learnloop.daily_plan import router_teach_back as tb
from learnloop.daily_plan.router_card import CardGatherer
from learnloop.daily_plan.types import PlanState
from learnloop.router.requests import evidence_from_card

from tests.router_mixture_helpers import mixture_env
from tests.router_model_fakes import FakeLLM, fake_runtime
from tests.test_daily_plan_build import _wide_items

TRANSCRIPT = (
    "# Teach-back transcript\n\n## Opening explanation\n\nA basis spans the space and is independent.\n\n"
    "## Follow-up 1 (criterion: c_independence)\n\n**Student asked:** Why independent?\n\n"
    "**Learner answered:** So no vector is redundant, I think.\n"
)


def _summary_llm(calls):
    def answer(request):
        calls.append(request)
        return {"explained_correctly": ["a basis spans the space"],
                "missing_or_wrong": ["why independence makes the coordinates unique"],
                "learner_words": ["no vector is redundant"]}

    return FakeLLM(answer=answer)


def _teach_back(env, attempt_id="att_tb_1", item="pi_m1a", lo="lo_m1", at="2026-10-11T09:00:00Z"):
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "correctness, hints_used, primed, latency_seconds, created_at, session_id, learner_answer_md) "
            "VALUES (?, ?, ?, 'teach_back', 'teach_back', 0.5, 0, 0, 300, ?, 's0', ?)",
            (attempt_id, item, lo, at, TRANSCRIPT),
        )
        connection.commit()
    return attempt_id


def _card(env):
    state = PlanState(plan_id="p", kind="normal", minutes_budget=25.0, minutes_left=25.0,
                      lane_minutes_left={"maintain": 10.0}, days_since_last_activity=0, streak_days=1,
                      current_block_id=None)
    from learnloop.daily_plan.engine import build_plan

    record = build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    feasible = []
    del record
    from learnloop.daily_plan.types import BlockCandidate

    feasible.append(BlockCandidate(
        candidate_id="maintain:x", lane="maintain", action="maintain", subtype=None, learning_object_ids=("lo_m1",),
        item_ids=("pi_m1a",), reading=None, est_minutes=2.0, planner_value=1.0, reason="review",
        annotations={"reason_code": "review", "topic": "Bases", "reversible": True},
    ))
    return CardGatherer(env.vault, env.repository, clock=env.clock, session_id="s1")(state, feasible)


def test_a_graded_teach_back_is_summarized_into_the_next_card(tmp_path):
    calls: list = []
    runtime = fake_runtime(llm=_summary_llm(calls))
    env = mixture_env(tmp_path, runtime, items=_wide_items())
    attempt_id = _teach_back(env)
    summary = tb.summarize(env.vault, env.repository, attempt_id, runtime=runtime)
    assert summary["missing_or_wrong"] == ["why independence makes the coordinates unique"]
    (request,) = calls
    assert "no vector is redundant" in request.prompt and "partly correct" in request.prompt
    # The learner's dialogue goes to an isolated turn, as the blind grader's does.
    assert request.isolated is True
    # Idempotent: a stored summary is never paid for twice.
    assert tb.summarize(env.vault, env.repository, attempt_id, runtime=runtime) is None and len(calls) == 1
    with env.repository.connection() as connection:
        owners = {row[0] for row in connection.execute("SELECT owner_kind FROM model_call_receipts")}
    assert owners == {"router_teach_back_summary"}
    card = _card(env)
    (entry,) = card.json["evidence_sections"]["teach_back_summaries"]
    assert entry["attempt_id"] == attempt_id and entry["source"] == "teach_back_summary"
    assert "# Teach-back summaries" in card.text and "missing or wrong: why independence" in card.text
    assert attempt_id in {ref.attempt_id for ref in evidence_from_card(card.json)}


def test_the_summarizer_never_sees_the_rubric_or_a_reference_answer(tmp_path):
    calls: list = []
    runtime = fake_runtime(llm=_summary_llm(calls))
    env = mixture_env(tmp_path, runtime, items=_wide_items())
    tb.summarize(env.vault, env.repository, _teach_back(env), runtime=runtime)
    item = env.vault.practice_items["pi_m1a"]
    secrets = [str(value) for value in (getattr(item, "reference_answer_md", None), getattr(item, "answer", None))
               if value]
    for secret in secrets:
        assert secret not in calls[0].prompt
    assert "rubric" not in calls[0].prompt.lower()


def test_exam_or_reserved_work_is_never_summarized(tmp_path, monkeypatch):
    calls: list = []
    runtime = fake_runtime(llm=_summary_llm(calls))
    env = mixture_env(tmp_path, runtime, items=_wide_items())
    # The card's protection, shared with the chat frontend (learner_protection).
    monkeypatch.setattr(protection, "withheld_items",
                        lambda vault, repository: protection.Withheld(reasons={"pi_m1a": protection.WITHHELD_EXAM}))
    assert tb.summarize(env.vault, env.repository, _teach_back(env), runtime=runtime) is None
    monkeypatch.setattr(protection, "withheld_items",
                        lambda vault, repository: protection.Withheld(available=False))
    assert tb.summarize(env.vault, env.repository, _teach_back(env, attempt_id="att_tb_2"), runtime=runtime) is None
    assert calls == []


def test_summaries_run_only_where_the_mixture_serves(tmp_path):
    calls: list = []
    runtime = fake_runtime(llm=_summary_llm(calls))
    staged = mixture_env(tmp_path / "a", runtime, items=_wide_items(), version=ROUTER_STAGED_FRAME_ALGORITHM_VERSION)
    assert tb.schedule(staged.vault, staged.repository.sqlite_path, _teach_back(staged), runtime=runtime) is None
    off = mixture_env(tmp_path / "b", runtime, items=_wide_items(), toml="[router]\nteach_back_summary = false\n")
    tb.schedule(off.vault, off.repository.sqlite_path, _teach_back(off), runtime=runtime)
    assert calls == []
    on = mixture_env(tmp_path / "c", runtime, items=_wide_items())
    tb.schedule(on.vault, on.repository.sqlite_path, _teach_back(on), runtime=runtime)
    assert len(calls) == 1
    # No LLM set up: nothing is asked.
    bare = fake_runtime()
    none = mixture_env(tmp_path / "d", bare, items=_wide_items())
    assert tb.schedule(none.vault, none.repository.sqlite_path, _teach_back(none), runtime=bare) is None


# -- Codex review F2: held grades and regrades --------------------------------------------------


def _blind_record(env, attempt_id, *, record_id, at, held):
    import json

    support = {"proof_route_check": {"held_for_review": held, "status": "checked", "version": "own-route-rule-v1"}}
    with env.repository.connection() as connection:
        connection.execute(
            "INSERT INTO blind_grade_records(id, attempt_id, agent_run_id, grading_prompt_version, "
            "output_schema_version, context_hash, record_json, supersedes_id, created_at) "
            "VALUES (?, ?, NULL, 'blind-v1', 'schema-v1', 'h', ?, NULL, ?)",
            (record_id, attempt_id, json.dumps({"grading_support": support}, separators=(",", ":")), at),
        )
        connection.commit()


def _summaries(env):
    state = PlanState(plan_id="p", kind="normal", minutes_budget=25.0, minutes_left=25.0,
                      lane_minutes_left={"maintain": 10.0}, days_since_last_activity=0, streak_days=1,
                      current_block_id=None)
    from learnloop.daily_plan.types import BlockCandidate

    feasible = [BlockCandidate(
        candidate_id="maintain:x", lane="maintain", action="maintain", subtype=None, learning_object_ids=("lo_m1",),
        item_ids=("pi_m1a",), reading=None, est_minutes=2.0, planner_value=1.0, reason="review",
        annotations={"reason_code": "review", "topic": "Bases", "reversible": True},
    )]
    card = CardGatherer(env.vault, env.repository, clock=env.clock, session_id="s1")(state, feasible)
    return card.json.get("evidence_sections", {}).get("teach_back_summaries", []), card.text


def test_a_held_teach_back_is_never_summarized(tmp_path):
    # Codex review F2: a grade held for review is no evidence anywhere, so its
    # dialogue's "explained correctly" conclusions never reach a model.
    from learnloop.held_grades import attempt_grade_held

    calls: list = []
    runtime = fake_runtime(llm=_summary_llm(calls))
    env = mixture_env(tmp_path, runtime, items=_wide_items())
    attempt_id = _teach_back(env)
    _blind_record(env, attempt_id, record_id="bgr_1", at="2026-10-11T09:01:00Z", held=True)
    assert attempt_grade_held(env.repository, attempt_id)
    assert tb.summarize(env.vault, env.repository, attempt_id, runtime=runtime) is None
    assert calls == []


def test_a_summary_leaves_the_card_once_its_grade_is_held_or_regraded(tmp_path):
    # Codex review F2: a summary is read only while its attempt's grade is not
    # held and is the one it summarized. A regrade into a hold removes it; a
    # later release (another regrade) does not bring back the stale summary.
    calls: list = []
    runtime = fake_runtime(llm=_summary_llm(calls))
    env = mixture_env(tmp_path, runtime, items=_wide_items())
    attempt_id = _teach_back(env)
    _blind_record(env, attempt_id, record_id="bgr_1", at="2026-10-11T09:01:00Z", held=False)
    assert tb.summarize(env.vault, env.repository, attempt_id, runtime=runtime) is not None
    _card(env)  # the plan the card reads
    (entry,), text = _summaries(env)
    assert entry["attempt_id"] == attempt_id and "a basis spans the space" in text
    # A regrade holds the grade for review: the summary leaves the card.
    _blind_record(env, attempt_id, record_id="bgr_2", at="2026-10-11T10:00:00Z", held=True)
    summaries, text = _summaries(env)
    assert summaries == [] and "a basis spans the space" not in text
    # A later regrade releases it: the old summary described another grade.
    _blind_record(env, attempt_id, record_id="bgr_3", at="2026-10-11T11:00:00Z", held=False)
    assert _summaries(env)[0] == []
    # Summarizing the current grade puts a fresh summary in the card.
    assert tb.summarize(env.vault, env.repository, attempt_id, runtime=runtime) is not None
    summaries = [request for request in calls if request.purpose == tb.PURPOSE]
    assert len(summaries) == 2 and [entry["attempt_id"] for entry in _summaries(env)[0]] == [attempt_id]
