"""Curriculum C1, fix round 2 (scoped verify 20261101-003504-qjtNva): one invariant.

*While the plan's reading block has no reading history, it is whatever a fresh build would
choose right now* (``engine._reading_follows_fresh_choice``). Each verbatim finding, fail-first:

* **Medium 1** (auto-completion): C1's reading staged, C1 off (RW7b offers none), the practice
  exhausted (the plan completes), then RW7b off: the plan reopens with the order's reading. The
  withdrawn C1 block is no reading of the plan.
* **Medium 2** (refresh order): nearer A and farther B both stale; B refreshed first (the plan
  takes B's step), then A: the plan ends on A's step, the nearest fresh path.
* **Medium 3** (K0 to K1): the build reads the inputs at state K0; a coverage-side change moves
  the state to K1 and K1's judgment commits before the build looks its rows up. The fresh
  choice's fingerprint is taken before any input, so the next read takes K1's step.
* **Medium 4** (Library reading): a prefetched, unstarted block the learner read part of in the
  reader (``note_reading_progress``), or a staged section read through the Library before its
  block exists, is reading history: a refresh never moves it, and its minutes count.
* **Medium 5** (one judgment): the Guide's judgment in flight and the day's first plan read (and
  the other way round) send exactly one model call: one coalescing set.
* **Low 6** (cost): a path judged but stale again ("stale after refresh") is not chosen afresh on
  every read: the choice is memoized on its inputs' fingerprint (a spy counts it), and a read
  that moves nothing writes nothing.

Every model is a fake; nothing leaves the machine.
"""
from __future__ import annotations

import json

from learnloop.algorithm_versions import DELIVERABLE_PLAN_ALGORITHM_VERSION
from learnloop.daily_plan import engine as E
from learnloop.source_retrieval import deliverable_path as DP
from learnloop.vault.loader import load_vault
from tests.deliverable_fixtures import DeliverableFake, PlanDeliverableFake
from tests.helpers import append_config_toml
from tests.reading_path_fixtures import call, context
from tests.curriculum_c1_codex_review_fixes_helpers import NEAR_PRIMARIES, _ended
from tests.curriculum_c1_plan_follows_path_helpers import (
    C1_OFF,
    PRIMARIES,
    RW7B_OFF,
    _at,
    _c1,
    _complete,
    _deliverable,
    _judge,
    _split,
)
from tests.rw7b_codex_review_fixes_helpers import _blocks, _stage_reading
from tests.rw7b_fix_round2_helpers import _plan_row, _skip_to_done
from tests.curriculum_c1_fix_round2_helpers import _no_refresh


def _record(c1):
    return E.latest_today(E.PlanEnv(load_vault(c1.paths.root), c1.repository))


# -- Medium 1: auto-completion, then RW7b's switch off -------------------------------------------------


EVERY_ENRICHMENT = {"ch_eigen": "enrichment", "ch_det": "enrichment", "ch_orth": "enrichment"}


def test_m1_auto_completed_after_c1_off_then_rw7b_off_reopens_with_the_orders_reading(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, book_path=EVERY_ENRICHMENT)
    ctx = context(c1.paths.root)
    session_id = call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    staged = _stage_reading(ctx, session_id)
    assert staged["reading"]["sectionId"] == "ch_det"  # C1's step; RW7b's path leaves the notes nothing
    built = _split(c1.repository)
    assert built["reading_path"]["predecessor"] is None
    assert _at(built["reading_path"]["rw7b"]["predecessor"]) == ("ext_book", "ch_eigen")
    # C1 off: the fresh choice is RW7b's, which is no reading; the staged block is withdrawn.
    append_config_toml(c1.paths.root, C1_OFF)
    ctx = context(c1.paths.root)
    assert _skip_to_done(ctx, session_id)["kind"] == "done"
    assert _ended(c1.repository, staged["blockId"]) == [
        {"outcome": "displaced", "reason": "reading_path_off", "minutes_counted": 0.0}]
    closed = _plan_row(c1.repository)
    assert closed["status"] == "complete" and closed["stop_reason"] != "learner_stopped"
    assert _split(c1.repository)["reading"] is None
    # RW7b's path off too: the order offers a reading, so the plan reopens with it.
    append_config_toml(c1.paths.root, RW7B_OFF.replace("[reading_paths]\n", "\n[reading_paths]\n"))
    step = call(context(c1.paths.root), "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
    assert step["kind"] == "reading" and step["reading"]["sectionId"] == "ch_eigen"
    assert _plan_row(c1.repository) == {"status": "open", "stop_reason": None, "completed_at": None}
    receipt = _split(c1.repository)["reading_path"]
    latest = receipt["moves"][-1]
    assert latest["reason"] == "reading_path_off" and latest["from"] is None
    assert latest["reopened"] == {"status": "complete", "stop_reason": closed["stop_reason"],
                                  "completed_at": closed["completed_at"]}
    assert receipt["move_count"] == 2


def test_m1_a_plan_the_learner_ended_stays_ended(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, book_path=EVERY_ENRICHMENT)
    ctx = context(c1.paths.root)
    session_id = call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    _stage_reading(ctx, session_id)
    call(ctx, "plan_keep_going", {"sessionId": session_id, "stop": True})
    ended, before = _plan_row(c1.repository), _split(c1.repository)
    assert ended["stop_reason"] == "learner_stopped"
    append_config_toml(c1.paths.root, C1_OFF + RW7B_OFF.replace("[reading_paths]\n", "\n[reading_paths]\n"))
    step = call(context(c1.paths.root), "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
    assert step["kind"] == "done"
    assert _plan_row(c1.repository) == ended and _split(c1.repository) == before


# -- Medium 2: the farther deliverable refreshed first, then the nearer ---------------------------------


def test_m2_farther_refreshed_first_then_nearer_ends_on_the_nearer_step(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")  # B: the farther deliverable
    near = _deliverable(c1.paths, c1.repository, "eigenvalues for the quiz", due_at="2026-11-20")  # A
    _complete(c1.repository, "ext_book", "ch_det")
    _judge(c1)
    DP.judge(c1.vault, c1.repository, near, client=DeliverableFake(primaries=NEAR_PRIMARIES))
    c1.clock.advance(days=1)  # both dated: both stale
    ctx = context(c1.paths.root)
    _no_refresh(ctx)
    call(ctx, "get_daily_plan", {})
    built = _split(c1.repository)
    assert [(c["goal_id"], c["status"]) for c in built["reading_path"]["deliverable"]["consulted"]] == [
        (near, "stale"), (c1.goal_id, "stale")]
    fallback = _at(built["reading"])
    # B's judgment lands first: B is the nearest fresh path, its step is taken.
    c1.clock.advance(minutes=5)
    _judge(c1)
    call(ctx, "get_daily_plan", {})
    first = _split(c1.repository)
    assert _at(first["reading"]) == ("ext_lay", "lay_char") and first["reading_path"]["deliverable"]["goal_id"] == c1.goal_id
    # Then A's: the nearer fresh path wins, while the reading is unread.
    c1.clock.advance(minutes=5)
    DP.judge(load_vault(c1.paths.root), c1.repository, near, client=DeliverableFake(primaries=NEAR_PRIMARIES))
    call(ctx, "get_daily_plan", {})
    second = _split(c1.repository)
    assert _at(second["reading"]) == ("ext_book", "ch_eigen") and second["reading"]["path_label"] == "core"
    receipt = second["reading_path"]
    assert receipt["deliverable"]["goal_id"] == near and receipt["chosen_by"] == "deliverable"
    assert [(_at(m["from"]), _at(m["to"])) for m in receipt["moves"]] == [
        (fallback, ("ext_lay", "lay_char")), (("ext_lay", "lay_char"), ("ext_book", "ch_eigen"))]
    assert receipt["move_count"] == 2


# -- Medium 3: K0 read, K1 judged before the lookup ----------------------------------------------------


def test_m3_a_k1_judgment_committed_between_the_builds_inputs_and_its_lookup_is_taken(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")
    c1.clock.advance(days=1)  # K0 (today's state) is not judged
    original = DP.path_inputs
    landed: list[str] = []

    def interleaved(vault, repository, goal_id, **kwargs):
        inputs = original(vault, repository, goal_id, **kwargs)
        if not landed:
            landed.append(inputs.state_key())
            # Background work moves the learner's state (a book started: learner context),
            # then the refresh for that state K1 commits, all before the build's lookup.
            c1.repository.upsert_reader_section_progress(
                extraction_id="ext_lay", section_id="lay_ortho", spans_seen=1, span_count=4)
            DP.judge(load_vault(c1.paths.root), c1.repository, c1.goal_id,
                     client=DeliverableFake(primaries=PRIMARIES))
        return inputs

    monkeypatch.setattr(DP, "path_inputs", interleaved)
    ctx = context(c1.paths.root)
    _no_refresh(ctx)
    call(ctx, "get_daily_plan", {})
    k1 = original(load_vault(c1.paths.root), c1.repository, c1.goal_id).state_key()
    assert landed and landed[0] != k1  # the build read K0; K1 was judged meanwhile
    split = _split(c1.repository)
    # The build found K0 stale; its first reconcile (the same call) sees the inputs changed
    # and takes K1's fresh step.
    assert _at(split["reading"]) == ("ext_book", "ch_det") and split["reading_path"]["chosen_by"] == "deliverable"
    assert split["reading_path"]["deliverable"]["input_state_key"] == k1
    assert split["reading_path"]["moves"][0]["reason"] == "deliverable_path_moved"
    call(ctx, "get_daily_plan", {})
    assert _split(c1.repository) == split


# -- Medium 4: reading progress is reading history ------------------------------------------------------


def test_m4_a_prefetched_block_read_in_the_reader_is_never_moved_and_its_minutes_count(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20", version=DELIVERABLE_PLAN_ALGORITHM_VERSION)
    c1.clock.advance(days=1)
    ctx = context(c1.paths.root)
    _no_refresh(ctx)
    session_id = call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    staged = _stage_reading(ctx, session_id)  # prefetched: current, never started
    assert staged["reading"]["sectionId"] == "ch_eigen"
    # The learner opens that section through the Library and reads part of it.
    call(ctx, "reader.mark_section_progress",
         {"extractionId": "ext_book", "sectionId": "ch_eigen", "spansSeen": 1, "spanCount": 3})
    record = _record(c1)
    block = next(b for b in record.blocks if b.id == staged["blockId"])
    assert block.started_at is None and block.reading_progress == (1, 3)
    c1.clock.advance(minutes=5)
    _judge(c1)  # the refresh lands: a fresh build would now choose Determinants
    step = call(ctx, "next_plan_item", {"sessionId": session_id, "serve": False})["step"]
    assert step["kind"] == "reading" and step["blockId"] == staged["blockId"]
    assert step["reading"]["sectionId"] == "ch_eigen"
    assert _ended(c1.repository, staged["blockId"]) == []
    assert "moves" not in _split(c1.repository)["reading_path"]
    # The learner finishes it: the block ends completed and its minutes count.
    call(ctx, "reader.mark_section_progress",
         {"extractionId": "ext_book", "sectionId": "ch_eigen", "spansSeen": 3, "spanCount": 3, "completed": True})
    [ended] = _ended(c1.repository, staged["blockId"])
    assert ended["outcome"] == "section_completed" and ended["minutes_counted"] > 0


def test_m4_a_staged_section_read_through_the_library_before_its_block_exists_is_kept(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")
    c1.clock.advance(days=1)
    ctx = context(c1.paths.root)
    _no_refresh(ctx)
    call(ctx, "get_daily_plan", {})
    built = _split(c1.repository)
    assert _at(built["reading"]) == ("ext_book", "ch_eigen")
    assert not [b for b in _record(c1).blocks if b.is_reading]
    # Read in the Library while the plan serves practice: no block takes it, the row does.
    call(ctx, "reader.mark_section_progress",
         {"extractionId": "ext_book", "sectionId": "ch_eigen", "spansSeen": 1, "spanCount": 3})
    c1.clock.advance(minutes=5)
    _judge(c1)
    call(ctx, "get_daily_plan", {})
    assert _split(c1.repository) == built


# -- Medium 5: one judgment for the Guide and the daily refresh -----------------------------------------


def test_m5_a_plan_read_while_the_guides_judgment_runs_sends_no_second_call(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers.deliverables import _work

    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")
    c1.clock.advance(days=1)
    nested: list[dict] = []

    class GuideFake(PlanDeliverableFake):
        def complete(self, request):
            if not nested:
                # The day's first plan read arrives while the Guide's judgment is in flight.
                nested.append(call(ctx, "get_daily_plan", {}))
            return super().complete(request)

    fake = GuideFake(primaries=PRIMARIES)
    ctx = context(c1.paths.root, deliverable_path_client=fake, deliverable_inline=True)
    call(ctx, "curriculum.path", {"goalId": c1.goal_id})
    assert nested and fake.calls == 1
    assert _work(ctx).refresh["status"] == "coalesced"
    # The plan built meanwhile took the fresh step on its next read.
    call(ctx, "get_daily_plan", {})
    assert _at(_split(c1.repository)["reading"]) == ("ext_book", "ch_det") and fake.calls == 1


def test_m5_a_guide_open_while_the_daily_refresh_runs_sends_no_second_call(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")
    c1.clock.advance(days=1)
    opened: list[dict] = []

    class RefreshFake(PlanDeliverableFake):
        def complete(self, request):
            if not opened:
                # The learner opens the Guide while the quiet daily refresh is in flight.
                opened.append(call(ctx, "curriculum.path", {"goalId": c1.goal_id}))
            return super().complete(request)

    fake = RefreshFake(primaries=PRIMARIES)
    ctx = context(c1.paths.root, deliverable_path_client=fake, deliverable_inline=True)
    call(ctx, "get_daily_plan", {})
    assert opened and fake.calls == 1
    assert opened[0]["status"] == "judging"  # the Guide shows the refresh's judgment running
    assert _at(_split(c1.repository)["reading"]) == ("ext_book", "ch_det")


# -- Low 6: the fresh choice is memoized on its inputs ---------------------------------------------------


def test_l6_a_path_stale_after_its_refresh_is_not_chosen_afresh_on_every_read(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")
    c1.clock.advance(days=1)
    ctx = context(c1.paths.root)
    _no_refresh(ctx)
    call(ctx, "get_daily_plan", {})
    # A refresh judged it, then the learner's state moved (a book started): stale again, with a
    # newer judgment than the build saw.
    _judge(c1)
    c1.repository.upsert_reader_section_progress(
        extraction_id="ext_lay", section_id="lay_ortho", spans_seen=1, span_count=4)
    choices: list[int] = []
    real = E._deliverable_choice
    monkeypatch.setattr(E, "_deliverable_choice", lambda *a, **k: choices.append(1) or real(*a, **k))
    call(ctx, "get_daily_plan", {})
    after = _split(c1.repository)
    assert after["reading_path"]["deliverable"]["status"] == "stale" and "moves" not in after["reading_path"]
    assert len(choices) == 1  # the inputs changed once: one full choice
    with c1.repository.connection() as connection:
        stamp = connection.execute("SELECT updated_at FROM daily_plans").fetchone()[0]
    for _ in range(4):
        c1.clock.advance(minutes=1)
        call(ctx, "get_daily_plan", {})
    assert len(choices) == 1  # nothing changed: no full choice, and nothing written
    with c1.repository.connection() as connection:
        assert connection.execute("SELECT updated_at FROM daily_plans").fetchone()[0] == stamp
    assert _split(c1.repository) == after
    # An input changing (another section read) recomputes it once.
    c1.repository.upsert_reader_section_progress(
        extraction_id="ext_lay", section_id="lay_ortho", spans_seen=2, span_count=4)
    call(ctx, "get_daily_plan", {})
    call(ctx, "get_daily_plan", {})
    assert len(choices) == 2


def test_l6_the_fingerprint_moves_with_a_judgment_a_switch_and_the_date(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")
    vault = load_vault(c1.paths.root)
    env = E.PlanEnv(vault, c1.repository)
    first = E._fresh_reading_fingerprint(env)
    assert E._fresh_reading_fingerprint(env) == first  # reading it writes and changes nothing
    c1.clock.advance(days=1)
    dated = E._fresh_reading_fingerprint(env)
    assert dated != first
    _judge(c1)  # stale after the day: a new judgment row
    assert E._fresh_reading_fingerprint(env) != dated
    append_config_toml(c1.paths.root, C1_OFF)
    off = E.PlanEnv(load_vault(c1.paths.root), c1.repository)
    assert E._fresh_reading_fingerprint(off) != E._fresh_reading_fingerprint(env)


def test_l6_a_memo_hit_returns_exactly_what_the_choice_computed(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)
    env = E.PlanEnv(load_vault(c1.paths.root), c1.repository)
    reading, receipt = E._remembered_fresh_reading(env)
    computed = E._fresh_reading(env, E.intent_view(env))
    assert (reading, receipt) == computed
    receipt["chosen_by"] = "tampered"  # a caller's change never reaches the memo
    again = E._remembered_fresh_reading(env)
    assert again == computed and json.dumps(again[1]) == json.dumps(computed[1])


def test_a_move_withdraws_the_staged_block_and_it_counts_no_minutes(tmp_path, monkeypatch):
    """The withdrawn block of a move counts no minutes and is no reading of the day."""

    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20", version=DELIVERABLE_PLAN_ALGORITHM_VERSION)
    c1.clock.advance(days=1)
    ctx = context(c1.paths.root)
    _no_refresh(ctx)
    session_id = call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    staged = _stage_reading(ctx, session_id)
    c1.clock.advance(minutes=5)
    _judge(c1)
    step = call(ctx, "next_plan_item", {"sessionId": session_id, "serve": False})["step"]
    assert step["reading"]["sectionId"] == "ch_det" and step["blockId"] != staged["blockId"]
    record = _record(c1)
    withdrawn = next(b for b in record.blocks if b.id == staged["blockId"])
    assert withdrawn.withdrawn_path_reading and withdrawn.est_minutes() == 0.0
    blocks, _events = _blocks(c1.repository)
    assert sum(1 for b in record.blocks if b.is_reading and not b.withdrawn_path_reading) == 1 and blocks


def test_l6_a_choice_made_while_a_read_failed_is_never_kept(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)
    env = E.PlanEnv(load_vault(c1.paths.root), c1.repository)
    computed = E._fresh_reading(env, E.intent_view(env))
    assert _at(computed[0]) == ("ext_book", "ch_det")
    real = E._exam_material
    monkeypatch.setattr(E, "_exam_material", lambda *a, **k: None)
    assert E._remembered_fresh_reading(env) == (None, None)  # protection unreadable: no step
    monkeypatch.setattr(E, "_exam_material", real)
    assert E._remembered_fresh_reading(env) == computed  # asked again, not the failure kept

    def boom(*_args, **_kwargs):
        raise RuntimeError("boom")

    lines = DP.effective_lines
    monkeypatch.setattr(DP, "effective_lines", boom)
    reloaded = E.PlanEnv(load_vault(c1.paths.root), c1.repository)  # another vault object: a miss
    _reading, receipt = E._remembered_fresh_reading(reloaded)
    assert receipt["deliverable"]["status"] == "unreadable"  # a path that cannot be read: RW7b's
    monkeypatch.setattr(DP, "effective_lines", lines)
    assert E._remembered_fresh_reading(reloaded)[1]["deliverable"]["status"] == "path"
