"""Curriculum C1, fix round 3 (scoped verify 20261101-011719-nTKDJ1). Fail-first, one test group per
verbatim finding:

* **Medium 1** (intent): a prefetched, unread C1 reading whose source the learner pauses moves to
  the fresh choice (C1's invariant runs before DL2's intent ending on a C1 plan), instead of DL2
  ending it and the plan keeping the paused reading. A reading with history keeps DL2's ending.
* **Medium 2** (memo inputs): the memo's fingerprint is the whole database (``PRAGMA data_version``
  of a watcher connection, and its own changes), plus the config, the dates, the goals' days left
  and the diagnosis waits crossed: a write to ``attempt_diagnoses`` or ``post_attempt_jobs`` alone,
  or a write from another connection, invalidates; a diagnosis wait running out invalidates with
  no write; repeated reads with no write hit, and a plan read that moves nothing writes nothing.
* **Medium 3** (coalescing): the daily refresh and the Guide's worker claim the key of the inputs
  they prepared and send exactly those: K0 observed, K1 prepared, a concurrent Guide open for K1
  sends no second call (and the other way round).

Every model is a fake; nothing leaves the machine.
"""
from __future__ import annotations

import sqlite3
from datetime import timedelta

from learnloop.clock import FrozenClock, parse_utc, utc_now_iso
from learnloop.daily_plan import engine as E
from learnloop.daily_plan import reading_choice as RC
from learnloop.source_retrieval import deliverable_path as DP
from learnloop.vault.loader import load_vault
from tests.deliverable_fixtures import DeliverableFake, PlanDeliverableFake
from tests.reading_path_fixtures import call, context
from tests.test_curriculum_c1_codex_review_fixes import _ended
from tests.test_curriculum_c1_fix_round2 import _no_refresh
from tests.test_curriculum_c1_plan_follows_path import PRIMARIES, _at, _c1, _split
from tests.test_rw7b_codex_review_fixes import _stage_reading


# -- Medium 1: C1's invariant before DL2's intent ending -----------------------------------------------


def _pause_notes(ctx) -> None:
    applied = call(ctx, "set_intent", {"scopeKind": "source", "scopeId": "src_book", "choice": "pause"})
    assert applied["available"], applied


def test_m1_an_unread_c1_reading_on_a_paused_source_moves_to_the_fresh_choice(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)
    ctx = context(c1.paths.root)
    _no_refresh(ctx)
    session_id = call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    staged = _stage_reading(ctx, session_id)  # prefetched, never started
    assert staged["reading"]["sectionId"] == "ch_det"
    _pause_notes(ctx)  # Lay stays readable
    step = call(ctx, "next_plan_item", {"sessionId": session_id, "serve": False})["step"]
    # Withdrawn by C1's move (no intent ending), and the plan takes the fresh choice in Lay.
    assert _ended(c1.repository, staged["blockId"]) == [
        {"outcome": "displaced", "reason": "reading_path_off", "minutes_counted": 0.0}]
    split = _split(c1.repository)
    assert _at(split["reading"]) == ("ext_lay", "lay_char") and split["reading_path"]["chosen_by"] == "deliverable"
    assert split["reading_path"]["moves"][-1]["reason"] == "deliverable_path_moved"
    assert step["kind"] == "reading" and step["reading"]["sectionId"] == "lay_char"


def test_m1_a_paused_reading_with_history_keeps_dl2s_intent_ending(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)
    ctx = context(c1.paths.root)
    _no_refresh(ctx)
    session_id = call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    staged = _stage_reading(ctx, session_id)
    # The learner read part of it in the reader (history), then paused its book.
    call(ctx, "reader.mark_section_progress",
         {"extractionId": "ext_book", "sectionId": "ch_det", "spansSeen": 1, "spanCount": 3})
    _pause_notes(ctx)
    call(ctx, "next_plan_item", {"sessionId": session_id, "serve": False})
    assert _ended(c1.repository, staged["blockId"]) == [
        {"outcome": "displaced", "reason": "intent", "minutes_counted": 0.0}]
    split = _split(c1.repository)
    assert _at(split["reading"]) == ("ext_book", "ch_det") and "moves" not in split["reading_path"]


# -- Medium 2: the whole database ------------------------------------------------------------------------


def _env(c1):
    return E.PlanEnv(load_vault(c1.paths.root), c1.repository)


def _raw(c1, sql, params=()):
    """A write from another connection (as a background job or another process makes it)."""

    connection = sqlite3.connect(c1.paths.sqlite_path)
    try:
        connection.execute(sql, params)
        connection.commit()
    finally:
        connection.close()


JOB = ("INSERT INTO post_attempt_jobs(id, attempt_id, kind, job_key, attempt_completed_at, state, payload_json, "
       "created_at, updated_at) VALUES (?, 'att_x', 'diagnose', ?, ?, 'queued', '{\"mode\": \"live\"}', ?, ?)")


def test_m2_a_write_to_the_diagnosis_or_job_rows_alone_invalidates(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)
    env = _env(c1)
    now = env.now_iso()
    first = E._fresh_reading_fingerprint(env)
    assert first is not None and E._fresh_reading_fingerprint(env) == first
    _raw(c1, JOB, ("job_1", "key_1", now, now, now))
    queued = E._fresh_reading_fingerprint(env)
    assert queued != first
    # A job's payload changing (a hold, a re-queue) is a write too.
    _raw(c1, "UPDATE post_attempt_jobs SET payload_json = '{\"mode\": \"live\", \"split_held_at\": \"x\"}'")
    held = E._fresh_reading_fingerprint(env)
    assert held != queued
    _raw(c1, "INSERT INTO attempt_diagnoses(id, attempt_id, diagnosis_prompt_version, mode, history_mode, status, "
             "created_at) VALUES ('dg_1', 'att_x', 'v1', 'live', 'exact', 'failed', ?)", (now,))
    assert E._fresh_reading_fingerprint(env) != held


def test_m2_a_write_from_another_connection_makes_the_next_read_choose_again(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)
    env = _env(c1)
    chosen: list[int] = []
    real = E._fresh_reading_checked
    monkeypatch.setattr(E, "_fresh_reading_checked", lambda *a, **k: chosen.append(1) or real(*a, **k))
    E._remembered_fresh_reading(env)
    for _ in range(3):
        E._remembered_fresh_reading(env)
    assert len(chosen) == 1  # repeated reads with no write hit the memo
    _raw(c1, "UPDATE reader_section_progress SET spans_seen = spans_seen")  # a commit, whatever it changes
    _raw(c1, JOB, ("job_2", "key_2", env.now_iso(), env.now_iso(), env.now_iso()))
    E._remembered_fresh_reading(env)
    E._remembered_fresh_reading(env)
    assert len(chosen) == 2


def test_m2_a_diagnosis_wait_running_out_invalidates_with_no_write(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)  # undated: no days left move within the day
    env = _env(c1)
    now = parse_utc(env.now_iso())
    from learnloop.placement.rules import DIAGNOSIS_WAIT_DAYS

    queued = utc_now_iso(FrozenClock(now - timedelta(days=DIAGNOSIS_WAIT_DAYS) + timedelta(seconds=30)))
    _raw(c1, JOB, ("job_3", "key_3", queued, queued, queued))
    before = E._fresh_reading_fingerprint(env)
    c1.clock.advance(seconds=10)
    assert E._fresh_reading_fingerprint(env) == before  # nothing crossed, nothing written
    c1.clock.advance(minutes=1)  # the wait runs out (the same day)
    assert E._fresh_reading_fingerprint(env) != before


def test_m2_the_plan_read_writes_nothing_when_nothing_moves_so_the_memo_hits(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)
    ctx = context(c1.paths.root)
    _no_refresh(ctx)
    call(ctx, "get_daily_plan", {})
    chosen: list[int] = []
    real = E._fresh_reading_checked
    monkeypatch.setattr(E, "_fresh_reading_checked", lambda *a, **k: chosen.append(1) or real(*a, **k))
    call(ctx, "get_daily_plan", {})  # the memo may be cold for the sidecar's vault object
    watcher = sqlite3.connect(c1.paths.sqlite_path)
    try:
        version = watcher.execute("PRAGMA data_version").fetchone()[0]
        before = len(chosen)
        for _ in range(3):
            call(ctx, "get_daily_plan", {})
        assert watcher.execute("PRAGMA data_version").fetchone()[0] == version  # no commit by the reads
        assert len(chosen) == before  # every read hit the memo
    finally:
        watcher.close()


def test_m2_the_memo_is_one_database_and_its_watcher_is_closed_on_forget(tmp_path, monkeypatch):
    first = _c1(tmp_path, monkeypatch, "one")
    second = _c1(tmp_path, monkeypatch, "two")
    env_one, env_two = _env(first), _env(second)
    E._remembered_fresh_reading(env_one)
    E._remembered_fresh_reading(env_two)  # another database: the first one's entry goes
    assert RC.recall(first.repository, env_one.vault, E._fresh_reading_fingerprint(env_one)) is None
    RC.forget()
    assert RC._WATCHER is None and RC._ENTRY is None


# -- Medium 3: claim and send the same prepared inputs -------------------------------------------------


def test_m3_k0_observed_k1_prepared_and_a_concurrent_guide_open_for_k1_send_one_call(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")
    c1.clock.advance(days=1)  # K0 (today's state) is stale
    observed = DP.deliverable_plan_path
    moved: list[str] = []

    def k0_then_k1(vault, repository, goal, **kwargs):
        path = observed(vault, repository, goal, **kwargs)
        if not moved and path.status == "stale":
            moved.append(str(path.state_key))
            # The learner's state moves to K1 after the refresh observed K0 stale.
            c1.repository.upsert_reader_section_progress(
                extraction_id="ext_lay", section_id="lay_ortho", spans_seen=1, span_count=4)
        return path

    opened: list[dict] = []

    class RefreshFake(PlanDeliverableFake):
        def complete(self, request):
            if not opened:
                # The learner opens the Guide while the refresh's K1 judgment is in flight.
                opened.append(call(ctx, "curriculum.path", {"goalId": c1.goal_id}))
            return super().complete(request)

    monkeypatch.setattr(DP, "deliverable_plan_path", k0_then_k1)
    fake = RefreshFake(primaries=PRIMARIES)
    ctx = context(c1.paths.root, deliverable_path_client=fake, deliverable_inline=True)
    call(ctx, "get_daily_plan", {})
    k1 = DP.path_inputs(load_vault(c1.paths.root), c1.repository, c1.goal_id).state_key()
    assert moved and moved[0] != k1
    assert opened and opened[0]["status"] == "judging"  # the refresh's K1 claim, as the Guide sees it
    assert fake.calls == 1  # the refresh sent K1, claimed as K1: the Guide sent nothing
    from learnloop_sidecar.handlers.deliverables import _work

    assert _work(ctx).refresh["state_key"] == k1


def test_m3_the_guides_worker_moves_its_claim_to_the_inputs_it_prepared(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers import deliverables as H

    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")
    c1.clock.advance(days=1)
    fake = DeliverableFake(primaries=PRIMARIES)
    ctx = context(c1.paths.root, deliverable_path_client=fake, deliverable_inline=True)
    _no_refresh(ctx)
    keys: list[str] = []
    real_spawn = H._spawn

    def between_claim_and_worker(ctx_, name, run):
        if name.startswith("deliverable-path-") and not keys:
            vault = load_vault(c1.paths.root)
            keys.append(DP.path_inputs(vault, c1.repository, c1.goal_id).state_key())  # K0: claimed by the open
            # The learner's state moves to K1, and the daily refresh is judging K1 right now.
            c1.repository.upsert_reader_section_progress(
                extraction_id="ext_lay", section_id="lay_ortho", spans_seen=1, span_count=4)
            k1 = DP.path_inputs(vault, c1.repository, c1.goal_id)
            keys.append(k1.state_key())
            H._work(ctx).judging[(c1.goal_id, k1.depth, k1.state_key())] = {"state": "running", "by": "plan_refresh"}
        return real_spawn(ctx_, name, run)

    monkeypatch.setattr(H, "_spawn", between_claim_and_worker)
    call(ctx, "curriculum.path", {"goalId": c1.goal_id})
    assert len(keys) == 2 and keys[0] != keys[1]
    assert fake.calls == 0  # the worker prepared K1, found it running and sent nothing
    judging = H._work(ctx).judging
    assert (c1.goal_id, "learn_to_use_it", keys[0]) not in judging  # its K0 mark is cleared
    assert judging[(c1.goal_id, "learn_to_use_it", keys[1])]["by"] == "plan_refresh"
