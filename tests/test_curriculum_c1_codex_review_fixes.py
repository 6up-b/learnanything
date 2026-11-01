"""Curriculum C1, Codex review (job 20261031-225454-osGoYy): the plan's path switches and the
refresh adoption on plans already built.

* **F1.** A refresh adoption ends the staged fallback reading unread; that withdrawn block is
  no reading of the day, so turning C1 off afterwards still puts RW7b's reading back.
* **F2.** The two path switches turned off in separate reads: C1 off (RW7b's reading), then
  RW7b's switch off (the order's reading); both transitions kept.
* **F3.** Refresh adoption reads judgment identity, not wall-clock order: a judgment recorded in
  the plan's own second, or between the build's stale read and the plan's creation stamp, is
  adopted.
* **F4.** A nearer deliverable found stale while a farther one's fresh path was followed is
  adopted once it is refreshed.

Every model is a fake; nothing leaves the machine.
"""
from __future__ import annotations

import json

from learnloop.daily_plan import engine as E
from learnloop.source_retrieval import deliverable_path as DP
from learnloop.vault.loader import load_vault
from tests.deliverable_fixtures import DeliverableFake
from tests.helpers import append_config_toml
from tests.reading_path_fixtures import call, context
from tests.test_curriculum_c1_plan_follows_path import (
    C1_OFF,
    PRIMARIES,
    RW7B_OFF,
    _at,
    _c1,
    _complete,
    _deliverable,
    _judge,
    _split,
    _step,
)
from tests.test_rw7b_codex_review_fixes import _blocks, _stage_reading


def _ended(repository, block_id) -> list[dict]:
    _blocks_, events = _blocks(repository)
    return [json.loads(e["detail_json"]) for e in events if e["block_id"] == block_id and e["kind"] == "block_ended"]


# -- F1: a refresh's withdrawn block does not stop the kill switch -----------------------------------


def test_f1_after_a_refresh_withdrew_the_staged_reading_the_switch_still_restores_rw7bs(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")
    c1.clock.advance(days=1)  # the path is stale: the plan keeps RW7b's (here the order's) choice
    ctx = context(c1.paths.root)
    session_id = call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    staged = _stage_reading(ctx, session_id)
    assert staged["reading"]["sectionId"] == "ch_eigen"
    c1.clock.advance(minutes=5)
    _judge(c1)  # the daily refresh lands
    step = call(ctx, "next_plan_item", {"sessionId": session_id, "serve": False})["step"]
    assert step["kind"] == "reading" and step["reading"]["sectionId"] == "ch_det"
    assert _ended(c1.repository, staged["blockId"]) == [
        {"outcome": "displaced", "reason": "reading_path_off", "minutes_counted": 0.0}]
    assert _split(c1.repository)["reading_path"]["refreshed"]["displaced_block_ids"] == [staged["blockId"]]
    replacement = step["blockId"]
    # The learner turns C1 off before starting the replacement: RW7b's reading comes back.
    append_config_toml(c1.paths.root, C1_OFF)
    step = call(context(c1.paths.root), "next_plan_item", {"sessionId": session_id, "serve": False})["step"]
    assert step["kind"] == "reading" and step["reading"]["sectionId"] == "ch_eigen"
    after = _split(c1.repository)
    assert _at(after["reading"]) == ("ext_book", "ch_eigen")
    transition = after["reading_path"]["transition"]
    assert transition["reason"] == "deliverable_path_off" and transition["displaced_block_ids"] == [replacement]
    record = E.latest_today(E.PlanEnv(load_vault(c1.paths.root), c1.repository))
    assert sum(1 for block in record.blocks if block.is_reading and not block.withdrawn_path_reading) == 1


def test_f1_a_started_replacement_reading_is_still_kept(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")
    c1.clock.advance(days=1)
    ctx = context(c1.paths.root)
    session_id = call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    _stage_reading(ctx, session_id)
    c1.clock.advance(minutes=5)
    _judge(c1)
    call(ctx, "next_plan_item", {"sessionId": session_id, "serve": False})
    started = call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
    assert started["reading"]["sectionId"] == "ch_det"
    before = _split(c1.repository)
    append_config_toml(c1.paths.root, C1_OFF)
    step = call(context(c1.paths.root), "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
    # The learner is reading it: history is kept.
    assert (step["reading"]["sectionId"], step["blockId"]) == ("ch_det", started["blockId"])
    assert _split(c1.repository) == before


# -- F2: the two switches turned off one after the other ---------------------------------------------


def test_f2_c1_off_then_rw7b_off_in_separate_reads_ends_on_the_orders_reading(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, book_path={"ch_eigen": "enrichment"})
    call(context(c1.paths.root), "get_daily_plan", {})
    built = _split(c1.repository)
    assert _at(built["reading"]) == ("ext_book", "ch_det") and built["reading"]["path_label"] == "prerequisite"
    append_config_toml(c1.paths.root, C1_OFF)
    call(context(c1.paths.root), "get_daily_plan", {})
    first = _split(c1.repository)
    # RW7b's choice (its own path skips the enrichment chapter): the same section, RW7b's label.
    assert first["reading"] == built["reading_path"]["predecessor"] and first["reading"]["path_label"] == "core"
    assert first["reading_path"]["transition"]["reason"] == "deliverable_path_off"
    assert "transitions" not in first["reading_path"]
    append_config_toml(c1.paths.root, RW7B_OFF.replace("[reading_paths]\n", "\n[reading_paths]\n"))
    call(context(c1.paths.root), "get_daily_plan", {})
    second = _split(c1.repository)
    # Now the order's choice (RW7b's own receipt's predecessor), and both transitions are history.
    assert _at(second["reading"]) == ("ext_book", "ch_eigen") and "path_label" not in second["reading"]
    receipt = second["reading_path"]
    assert receipt["transition"]["reason"] == "reading_path_off"
    assert receipt["transition"]["from"] == first["reading"]
    assert receipt["transitions"] == [first["reading_path"]["transition"], receipt["transition"]]
    # Recorded once: reading the plan again changes nothing.
    call(context(c1.paths.root), "get_daily_plan", {})
    assert _split(c1.repository)["reading_path"] == receipt


def test_f2_c1_back_on_after_its_switch_off_does_not_undo_the_transition(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)
    call(context(c1.paths.root), "get_daily_plan", {})
    append_config_toml(c1.paths.root, C1_OFF)
    call(context(c1.paths.root), "get_daily_plan", {})
    first = _split(c1.repository)
    assert _at(first["reading"]) == ("ext_book", "ch_eigen")
    config = c1.paths.root / "learnloop.toml"
    config.write_text(config.read_text().replace("plan_uses_path = false", "plan_uses_path = true"))
    # C1 is on again (RW7b's switch never went off): a transition is not undone, nothing moves.
    assert E.deliverable_plan_active(load_vault(c1.paths.root))
    call(context(c1.paths.root), "get_daily_plan", {})
    assert _split(c1.repository) == first


# -- F3: freshness by judgment identity, not wall-clock order ----------------------------------------


def test_f3_a_judgment_in_the_plans_own_second_is_adopted(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")
    c1.clock.advance(days=1)
    ctx = context(c1.paths.root)
    call(ctx, "get_daily_plan", {})
    assert _split(c1.repository)["reading_path"]["deliverable"]["status"] == "stale"
    _judge(c1)  # the clock has not moved: the same second as the plan's creation
    call(ctx, "get_daily_plan", {})
    split = _split(c1.repository)
    assert _at(split["reading"]) == ("ext_book", "ch_det")
    assert split["reading_path"]["refreshed"]["was"]["status"] == "stale"


def test_f3_a_judgment_between_the_stale_read_and_the_plans_stamp_is_adopted(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")
    c1.clock.advance(days=1)
    original = DP.plan_deliverable
    landed: list[bool] = []

    def interleaved(*args, **kwargs):
        followed, consulted = original(*args, **kwargs)
        if not landed and any(path.status == "stale" for path in consulted):
            landed.append(True)
            # The background refresh records its judgment after the build read the path stale,
            # and the plan is stamped a second later.
            DP.judge(load_vault(c1.paths.root), c1.repository, c1.goal_id,
                     client=DeliverableFake(primaries=PRIMARIES))
            c1.clock.advance(seconds=1)
        return followed, consulted

    monkeypatch.setattr(DP, "plan_deliverable", interleaved)
    ctx = context(c1.paths.root)
    call(ctx, "get_daily_plan", {})
    assert landed
    with c1.repository.connection() as connection:
        judged_at = connection.execute(
            "SELECT MAX(created_at) FROM deliverable_path_sections WHERE learner_override IS NULL").fetchone()[0]
        created_at = connection.execute("SELECT created_at FROM daily_plans").fetchone()[0]
    assert judged_at < created_at  # the judgment predates the plan's stamp
    # The build read the path stale; the plan's first reconcile (in the same call) sees the
    # newer judgment by identity and takes the fresh step.
    split = _split(c1.repository)
    assert _at(split["reading"]) == ("ext_book", "ch_det") and split["reading_path"]["chosen_by"] == "deliverable"
    refreshed = split["reading_path"]["refreshed"]
    assert refreshed["was"]["status"] == "stale" and _at(refreshed["from"]) == ("ext_book", "ch_eigen")
    call(ctx, "get_daily_plan", {})
    assert _split(c1.repository)["reading_path"]["refreshed"] == refreshed


def test_f3_without_a_new_judgment_the_stale_plan_stays_and_reads_no_path(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")
    c1.clock.advance(days=1)
    ctx = context(c1.paths.root)
    call(ctx, "get_daily_plan", {})
    before = _split(c1.repository)
    reads = []
    monkeypatch.setattr(DP, "plan_deliverable", lambda *a, **k: reads.append(1) or (None, []))
    c1.clock.advance(minutes=5)
    call(ctx, "get_daily_plan", {})
    assert _split(c1.repository) == before and reads == []


# -- F4: a nearer deliverable refreshed while a farther one was followed -----------------------------


NEAR_PRIMARIES = {"Eigenvalues": "Chapter 5 Eigenvalues", "Determinants": "Chapter 3 Determinants"}


def test_f4_a_nearer_stale_deliverable_refreshed_is_adopted_over_the_farther_fresh_one(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)  # undated: its path's key carries no days left
    near = _deliverable(c1.paths, c1.repository, "eigenvalues for the quiz", due_at="2026-11-20")
    _complete(c1.repository, "ext_book", "ch_det")
    _judge(c1)
    DP.judge(c1.vault, c1.repository, near, client=DeliverableFake(primaries=NEAR_PRIMARIES))
    reading, receipt = _step(c1)
    assert receipt["deliverable"]["goal_id"] == near and _at(reading) == ("ext_book", "ch_eigen")
    c1.clock.advance(days=1)  # the nearer one's days left move; the undated one stays fresh
    ctx = context(c1.paths.root)
    call(ctx, "get_daily_plan", {})
    built = _split(c1.repository)
    entry = built["reading_path"]["deliverable"]
    assert entry["goal_id"] == c1.goal_id and entry["status"] == "path"
    assert [(c["goal_id"], c["status"]) for c in entry["consulted"]] == [(near, "stale"), (c1.goal_id, "path")]
    assert _at(built["reading"]) == ("ext_lay", "lay_char")
    c1.clock.advance(minutes=5)
    DP.judge(c1.vault, c1.repository, near, client=DeliverableFake(primaries=NEAR_PRIMARIES))
    call(ctx, "get_daily_plan", {})
    split = _split(c1.repository)
    assert _at(split["reading"]) == ("ext_book", "ch_eigen") and split["reading"]["path_label"] == "core"
    receipt = split["reading_path"]
    assert receipt["chosen_by"] == "deliverable" and receipt["deliverable"]["goal_id"] == near
    refreshed = receipt["refreshed"]
    assert refreshed["was"]["goal_id"] == c1.goal_id and _at(refreshed["from"]) == ("ext_lay", "lay_char")
    call(ctx, "get_daily_plan", {})
    assert _split(c1.repository)["reading_path"]["refreshed"] == refreshed


def test_f4_a_nearer_one_still_stale_leaves_the_farther_ones_step(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch)
    near = _deliverable(c1.paths, c1.repository, "eigenvalues for the quiz", due_at="2026-11-20")
    _complete(c1.repository, "ext_book", "ch_det")
    _judge(c1)
    DP.judge(c1.vault, c1.repository, near, client=DeliverableFake(primaries=NEAR_PRIMARIES))
    c1.clock.advance(days=1)
    ctx = context(c1.paths.root)
    call(ctx, "get_daily_plan", {})
    before = _split(c1.repository)
    c1.clock.advance(minutes=5)
    call(ctx, "get_daily_plan", {})
    assert _split(c1.repository) == before
