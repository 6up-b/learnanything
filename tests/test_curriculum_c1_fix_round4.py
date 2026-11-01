"""Curriculum C1, fix round 4 (scoped verify 20261101-020943-Fu1ywd). Fail-first, one group per
verbatim finding:

* **Mediums 1 and 2** (diagnosis deadlines): the memo's deadline input is placement's own rule
  (``placement.state.diagnosis_waits_run_out``: live jobs only, a payload naming no mode being
  live, run out strictly after the deadline), so the fingerprint is unchanged before and exactly at
  a deadline, changes just after it, and a shadow job before a live one never stands for it.
* **Medium 3** (the watcher's file): a database restored at the same path is watched as the new
  file (device and inode checked on every fingerprint), and a sidecar context closing or loading
  drops the memo and its watcher.
* **Medium 4** (claim owners): each job's claim carries its own token, so a Guide job finishing
  never releases a key another Guide job holds now, and the daily refresh cannot claim it.

Every model is a fake; nothing leaves the machine.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import timedelta

from learnloop.clock import FrozenClock, parse_utc, utc_now_iso
from learnloop.daily_plan import engine as E
from learnloop.daily_plan import reading_choice as RC
from learnloop.db.copies import backup_database
from learnloop.placement.rules import DIAGNOSIS_WAIT_DAYS
from learnloop.source_retrieval import deliverable_path as DP
from learnloop.vault.loader import load_vault
from tests.deliverable_fixtures import DeliverableFake
from tests.reading_path_fixtures import call, context
from tests.test_curriculum_c1_fix_round2 import _no_refresh
from tests.test_curriculum_c1_fix_round3 import JOB, _env, _raw
from tests.test_curriculum_c1_plan_follows_path import PRIMARIES, _c1


def _queued(env, after_wait_start: timedelta) -> str:
    """A job time whose wait runs out ``after_wait_start`` from now."""

    now = parse_utc(env.now_iso())
    return utc_now_iso(FrozenClock(now - timedelta(days=DIAGNOSIS_WAIT_DAYS) + after_wait_start))


def _job(c1, job_id, at, payload='{"mode": "live"}', attempt="att_x"):
    _raw(c1, "INSERT INTO post_attempt_jobs(id, attempt_id, kind, job_key, attempt_completed_at, state, "
             "payload_json, created_at, updated_at) VALUES (?, ?, 'diagnose', ?, ?, 'queued', ?, ?, ?)",
         (job_id, attempt, f"key_{job_id}", at, payload, at, at))


# -- Mediums 1 and 2: placement's own deadline rule ------------------------------------------------------


def test_m1_the_deadline_input_moves_strictly_after_the_deadline(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)  # undated: no days left move within the day
    env = _env(c1)
    _job(c1, "job_1", _queued(env, timedelta(seconds=5)))
    before = E._fresh_reading_fingerprint(env)
    c1.clock.advance(seconds=5)  # exactly at the deadline: placement still waits
    assert E._fresh_reading_fingerprint(env) == before
    from learnloop.placement.state import diagnosis_waits_run_out

    with c1.repository.connection() as connection:
        assert diagnosis_waits_run_out(connection, env.now_iso()) == 0
    c1.clock.advance(seconds=1)  # after it: placement decides the miss
    assert E._fresh_reading_fingerprint(env) != before
    with c1.repository.connection() as connection:
        assert diagnosis_waits_run_out(connection, env.now_iso()) == 1


def test_m2_a_shadow_job_before_the_live_one_never_stands_for_its_deadline(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)
    env = _env(c1)
    _job(c1, "job_shadow", _queued(env, timedelta(seconds=5)), payload='{"mode": "shadow"}')
    _job(c1, "job_live", _queued(env, timedelta(seconds=60)), payload="{}")  # no mode named: live
    before = E._fresh_reading_fingerprint(env)
    c1.clock.advance(seconds=6)  # past the shadow job's deadline only
    assert E._fresh_reading_fingerprint(env) == before
    c1.clock.advance(seconds=55)  # past the live job's
    assert E._fresh_reading_fingerprint(env) != before


def test_m2_the_count_is_placements_rule_for_the_same_rows(tmp_path, monkeypatch):
    from learnloop.placement import state as PS
    from learnloop.placement.state import diagnosis_waits_run_out

    c1 = _c1(tmp_path, monkeypatch)
    env = _env(c1)
    _job(c1, "job_a", _queued(env, timedelta(seconds=-10)), attempt="att_a")
    _job(c1, "job_b", _queued(env, timedelta(seconds=-10)), payload='{"mode": "shadow"}', attempt="att_b")
    _job(c1, "job_c", _queued(env, timedelta(seconds=30)), attempt="att_c")
    with c1.repository.connection() as connection:
        rows = PS._rows(connection, "SELECT attempt_id, payload_json, created_at FROM post_attempt_jobs")
        by_attempt: dict[str, list] = {}
        for row in rows:
            if PS._live_diagnose_job(row):
                by_attempt.setdefault(str(row["attempt_id"]), []).append(row)
        expected = sum(PS._wait_over(PS._diagnosis_wait_deadline(jobs), env.now_iso()) for jobs in by_attempt.values())
        assert diagnosis_waits_run_out(connection, env.now_iso()) == expected == 1


# -- Medium 3: the watcher follows the file -------------------------------------------------------------


def test_m3_a_database_restored_at_the_same_path_is_watched_as_the_new_file(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)
    env = _env(c1)
    saved = tmp_path / "saved.sqlite"
    backup_database(c1.paths.sqlite_path, saved)
    chosen: list[int] = []
    real = E._fresh_reading_checked
    monkeypatch.setattr(E, "_fresh_reading_checked", lambda *a, **k: chosen.append(1) or real(*a, **k))
    E._remembered_fresh_reading(env)
    before = E._fresh_reading_fingerprint(env)
    os.replace(saved, c1.paths.sqlite_path)  # a restore: another file at the same path
    restored = E._fresh_reading_fingerprint(env)
    assert restored != before and RC._ENTRY is None  # recreated, the old entry dropped
    E._remembered_fresh_reading(env)
    assert len(chosen) == 2
    # A commit to the restored file invalidates (the watcher is on the new file).
    _raw(c1, "UPDATE reader_section_progress SET spans_seen = spans_seen")
    _job(c1, "job_r", env.now_iso())
    assert E._fresh_reading_fingerprint(env) != restored


def test_m3_a_vanished_database_is_never_trusted(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)
    env = _env(c1)
    assert E._fresh_reading_fingerprint(env) is not None
    moved = tmp_path / "moved.sqlite"
    os.replace(c1.paths.sqlite_path, moved)
    assert RC.fingerprint(c1.repository, {}) is None and RC._WATCHER is None
    os.replace(moved, c1.paths.sqlite_path)


def test_m3_a_closing_context_drops_the_memo_and_its_watcher(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)
    ctx = context(c1.paths.root)
    _no_refresh(ctx)
    call(ctx, "get_daily_plan", {})
    assert RC._WATCHER is not None and RC._ENTRY is not None
    ctx.close()
    assert RC._WATCHER is None and RC._ENTRY is None
    again = context(c1.paths.root)  # a load drops it too (a switch, or the same path reopened)
    call(again, "get_daily_plan", {})
    assert RC._WATCHER is not None
    again.load(c1.paths.root)
    assert RC._WATCHER is None
    again.close()


# -- Medium 4: one token per job -------------------------------------------------------------------------


def test_m4_a_finishing_guide_job_keeps_another_jobs_claim_and_the_refresh_sends_nothing(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers import deliverables as H

    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")
    c1.clock.advance(days=1)
    fake = DeliverableFake(primaries=PRIMARIES)
    ctx = context(c1.paths.root, deliverable_path_client=fake, deliverable_inline=True)
    _no_refresh(ctx)
    work = H._work(ctx)
    depth = "learn_to_use_it"
    k0 = (c1.goal_id, depth, "k0-the-open-saw")  # A was started for K0; its prepared inputs are K1
    b_claim = {"state": "running", "by": "guide"}  # another Guide job's claim
    real_judge = DP.judge

    def a_judging(*args, **kwargs):
        # A moved its claim to K1 and released K0; meanwhile the learner switched back and
        # job B claimed K0 and started judging.
        assert k0 not in work.judging
        work.judging[k0] = dict(b_claim)
        return real_judge(*args, **kwargs)

    monkeypatch.setattr(DP, "judge", a_judging)
    vault, repository = ctx.require_vault()
    H._judge_path(ctx, vault, repository, c1.goal_id, depth, k0[2])
    assert fake.calls == 1  # A's own call
    assert work.judging.get(k0) == b_claim  # A finishing left B's claim alone
    # The daily refresh cannot claim K0 while B runs: no duplicate call.
    with H._claim_path(work, *k0) as claimed:
        assert not claimed
    assert fake.calls == 1


def test_m4_claims_carry_a_token_per_job(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers import deliverables as H

    first, second = H._token("guide"), H._token("guide")
    assert first != second and first.startswith("guide:")
    work = H._Work()
    key, other = ("g", "d", "k0"), ("g", "d", "k1")
    work.judging[key] = {"state": "running", "by": first}
    assert H._move_claim(work, key, other, first) and work.judging[other]["by"] == first and key not in work.judging
    work.judging[key] = {"state": "running", "by": second}
    H._release(work, key, first)  # not first's: kept
    assert work.judging[key]["by"] == second
