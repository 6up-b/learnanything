"""Reader workbench RW7b, Codex review fixes (job 20261025-131543-oFLlrm).

* **F1** The kill switch reaches plans already built: a plan whose reading
  the path chose, with that reading not yet started, goes back to the
  predecessor's reading (the receipt's ``predecessor``) when
  ``reading_paths.plan_uses_path`` or ``reading_paths.enabled`` is turned
  off; a staged, unstarted path reading block is ended unread
  (``reading_path_off``, no minutes counted); the minutes are recomputed and
  the transition is recorded on the receipt. A started reading is kept.
* **F2** A path judged for an older learner state (a changed goal, LO status
  or role: a missing current-state judgment) is stale: the plan falls back
  to the predecessor's order for that reading, recorded, and calls no model.
* **F3** The receipt names the inputs' state key and the judgment it
  consumed separately, with the judge rows and override rows it used, so a
  later judgment or override cannot change what it says.
* **F4** ``learnloop reader report``'s reading-path block has §15's row:
  misses on LOs whose core section was skipped, after the skip (an earlier
  miss and an unrelated LO do not count).

Fakes only (``PathJudgeFake``); no network.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import timedelta

import pytest

from learnloop.daily_plan import engine as E
from learnloop.source_retrieval import reading_paths as RP
from learnloop.vault.loader import load_vault
from tests.helpers import append_config_toml
from tests.reading_path_fixtures import EXT, PathJudgeFake, call, context
from tests.test_plan_follows_path import GUIDE_OFF, OFF, _split, _vault

LABELS = {"sec_eigen": "enrichment", "sec_spectral": "prerequisite"}


def _blocks(repository):
    with repository.connection() as connection:
        blocks = [dict(row) for row in connection.execute(
            "SELECT id, action, reading_json FROM attention_blocks ORDER BY rowid")]
        events = [dict(row) for row in connection.execute(
            "SELECT block_id, kind, detail_json FROM attention_block_events ORDER BY rowid")]
    return blocks, events


def _stage_reading(ctx, session_id):
    """Skip the plan's items (prefetch only) until its reading block is the
    current, staged and unstarted block."""

    for _ in range(20):
        step = call(ctx, "next_plan_item", {"sessionId": session_id, "serve": False})["step"]
        if step["kind"] == "reading":
            return step
        assert step["kind"] == "item", step
        call(ctx, "next_plan_item", {"sessionId": session_id, "skipPracticeItemId": step["practiceItemId"],
                                     "serve": False})
    raise AssertionError("no reading step")


# -- F1: the kill switch reaches plans already built --------------------------------------------------


@pytest.mark.parametrize("switch", [OFF, GUIDE_OFF], ids=["plan_uses_path_off", "guide_off"])
def test_f1_switching_off_after_the_build_restores_the_predecessors_reading(tmp_path, monkeypatch, switch):
    paths, repository, _ = _vault(tmp_path, monkeypatch, labels=LABELS)
    call(context(paths.root), "get_daily_plan", {})
    built = _split(repository)
    assert built["reading"]["section_id"] == "sec_spectral"
    append_config_toml(paths.root, switch)
    plan = call(context(paths.root), "get_daily_plan", {})
    split = _split(repository)
    # The predecessor's reading, as a plan built with the switch off holds it.
    assert split["reading"] == built["reading_path"]["predecessor"]
    assert "path_label" not in split["reading"]
    transition = split["reading_path"]["transition"]
    assert transition["reason"] == "reading_path_off"
    assert (transition["from"]["section_id"], transition["to"]["section_id"]) == ("sec_spectral", "sec_eigen")
    # The minutes follow the section now planned (the predecessor's words).
    estimator = E._estimator(E.PlanEnv(load_vault(paths.root), repository))
    assert split["reading_full_minutes"] == round(estimator.reading_minutes(split["reading"]["words_left"]), 4)
    assert split["admitted_new_minutes"] == pytest.approx(
        built["admitted_new_minutes"] - built["reading_full_minutes"] + split["reading_full_minutes"], abs=1e-3)
    projected = [row for row in plan["plan"]["projected"] if row.get("readingTitle")]
    assert projected and projected[0]["readingTitle"] == "1 Eigenvalues"
    assert "reading path" not in projected[0]["why"]
    # Recorded once: turning the switch back on keeps the predecessor's reading.
    text = (paths.root / "learnloop.toml").read_text().replace(switch, "")
    (paths.root / "learnloop.toml").write_text(text)
    assert E.reading_path_plan_active(load_vault(paths.root))
    call(context(paths.root), "get_daily_plan", {})
    assert _split(repository) == split


def test_f1_a_staged_unstarted_path_reading_is_ended_unread_and_the_predecessors_is_served(tmp_path, monkeypatch):
    paths, repository, _ = _vault(tmp_path, monkeypatch, labels=LABELS)
    ctx = context(paths.root)
    session_id = call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    staged = _stage_reading(ctx, session_id)
    assert staged["reading"]["sectionId"] == "sec_spectral"
    append_config_toml(paths.root, OFF)
    ctx = context(paths.root)
    step = call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
    assert step["kind"] == "reading" and step["reading"]["sectionId"] == "sec_eigen"
    blocks, events = _blocks(repository)
    old = staged["blockId"]
    ended = [json.loads(e["detail_json"]) for e in events if e["block_id"] == old and e["kind"] == "block_ended"]
    assert ended == [{"outcome": "displaced", "reason": "reading_path_off", "minutes_counted": 0.0}]
    assert not any(e["block_id"] == old and e["kind"] == "block_started" for e in events)
    assert _split(repository)["reading_path"]["transition"]["displaced_block_ids"] == [old]
    # The withdrawn block counts no minutes, and the new one is the plan's reading block.
    record = E.latest_today(E.PlanEnv(load_vault(paths.root), repository))
    withdrawn = next(block for block in record.blocks if block.id == old)
    assert withdrawn.est_minutes() == 0.0 and withdrawn.withdrawn_path_reading
    assert sum(1 for block in record.blocks if block.is_reading and not block.withdrawn_path_reading) == 1


def test_f1_a_started_path_reading_is_kept(tmp_path, monkeypatch):
    paths, repository, _ = _vault(tmp_path, monkeypatch, labels=LABELS)
    ctx = context(paths.root)
    session_id = call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    _stage_reading(ctx, session_id)
    started = call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
    assert started["reading"]["sectionId"] == "sec_spectral"
    before = _split(repository)
    append_config_toml(paths.root, OFF)
    step = call(context(paths.root), "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
    # The learner is reading it: history is kept, nothing is rewritten.
    assert (step["kind"], step["reading"]["sectionId"], step["blockId"]) == ("reading", "sec_spectral",
                                                                             started["blockId"])
    assert _split(repository) == before


# -- F2: a stale path falls back to the predecessor's order -------------------------------------------


def test_f2_a_judgment_for_an_older_state_is_stale_and_the_plan_keeps_the_order(tmp_path, monkeypatch):
    from tests.test_reading_paths import _practised

    paths, repository, _ = _vault(tmp_path, monkeypatch, labels={"sec_eigen": "enrichment"})
    fresh = RP.plan_path(load_vault(paths.root), repository, EXT)
    assert fresh.status == "path" and not fresh.plannable("sec_eigen")
    # The learner state moves (an LO now has evidence): the stored judgment
    # was for another state key, and nothing re-judged it.
    _practised(repository, "lo_spectral")
    judge = PathJudgeFake({"sec_eigen": "enrichment"})
    ctx = context(paths.root, reading_path_judge_client=judge)
    call(ctx, "get_daily_plan", {})
    assert judge.calls == 0  # the plan never calls a model
    path = RP.plan_path(load_vault(paths.root), repository, EXT)
    assert (path.status, path.follows, path.fresh) == ("stale", False, False)
    split = _split(repository)
    # The predecessor's order (book order: the enrichment section first), recorded.
    assert split["reading"]["section_id"] == "sec_eigen" and "path_label" not in split["reading"]
    receipt = split["reading_path"]
    assert receipt["chosen_by"] == "order" and receipt["same_as_predecessor"] is True
    [consulted] = receipt["paths"]
    assert consulted["status"] == "stale" and consulted["judgment"] is None
    assert consulted["latest_judged_state_key"] == fresh.judged_state_key != consulted["input_state_key"]


def test_f2_a_goal_change_invalidates_an_enrichment_judgment(tmp_path, monkeypatch):
    paths, repository, _ = _vault(tmp_path, monkeypatch, labels={"sec_eigen": "enrichment"})
    vault = load_vault(paths.root)
    inputs = RP.path_inputs(vault, repository, EXT)
    before = inputs.state_key("learn_to_use_it")
    # Another goal names the path now (the key hashes the goal): the old judgment is not today's.
    monkeypatch.setattr(RP, "goal_for_source",
                        lambda _vault, _los: type("Goal", (), {"id": "goal_g2", "title": "Another goal"})())
    assert RP.path_inputs(vault, repository, EXT).state_key("learn_to_use_it") != before
    path = RP.plan_path(vault, repository, EXT)
    assert path.status == "stale" and not path.follows
    reading, receipt = E._reading_on_path(E.PlanEnv(vault, repository), extraction_ids=None, from_furthest=True,
                                          exam=None)
    assert reading.section_id == "sec_eigen" and reading.path_label is None
    assert [p["status"] for p in receipt["paths"]] == ["stale"]


# -- F3: the receipt names the judgment it consumed ---------------------------------------------------


def test_f3_the_receipt_names_the_rows_it_used_and_later_rows_do_not_change_it(tmp_path, monkeypatch):
    paths, repository, _ = _vault(tmp_path, monkeypatch, labels=LABELS, overrides=[("sec_diag", "skip")])
    call(context(paths.root), "get_daily_plan", {})
    [consulted] = _split(repository)["reading_path"]["paths"]
    assert consulted["status"] == "path" and consulted["fresh"] is True
    assert consulted["input_state_key"] == consulted["judgment"]["state_key"]
    sections = {row["section_id"]: row for row in consulted["sections"]}
    assert {sid: row["label"] for sid, row in sections.items()} == {
        "sec_eigen": "enrichment", "sec_spectral": "prerequisite", "sec_diag": "skipped", "sec_history": "core"}

    def rows(ids):
        with repository.connection() as connection:
            return {str(r["id"]): dict(r) for r in connection.execute(
                f"SELECT * FROM reader_path_sections WHERE id IN ({','.join('?' for _ in ids)})", list(ids))}

    judged = rows([row["judgment_row_id"] for row in sections.values()])
    assert {r["section_id"]: r["label"] for r in judged.values()} == {
        "sec_eigen": "enrichment", "sec_spectral": "prerequisite", "sec_diag": "core", "sec_history": "core"}
    assert {r["state_key"] for r in judged.values()} == {consulted["judgment"]["state_key"]}
    assert all(r["learner_override"] is None for r in judged.values())
    assert sections["sec_diag"]["override"] == "skip"
    [override] = rows([sections["sec_diag"]["override_row_id"]]).values()
    assert (override["section_id"], override["learner_override"]) == ("sec_diag", "skip")
    assert all(sections[s]["override_row_id"] is None for s in ("sec_eigen", "sec_spectral", "sec_history"))
    stored = _split(repository)["reading_path"]
    # A later override and a later judgment (another depth, then back) append
    # rows; the receipt's references still resolve to the rows it used.
    ctx = context(paths.root, reading_path_judge_client=PathJudgeFake({"sec_spectral": "core"}),
                  reading_path_inline=True)
    call(ctx, "reader.reading_path_override",
         {"extractionId": EXT, "depth": "learn_to_use_it", "sectionId": "sec_spectral", "choice": "skip"})
    call(ctx, "reader.reading_path_set_depth", {"extractionId": EXT, "depth": "fluency"})
    assert _split(repository)["reading_path"] == stored
    assert rows([row["judgment_row_id"] for row in sections.values()]) == judged


# -- F4: misses on LOs whose core section was skipped -------------------------------------------------


def _attempt(paths, attempt_id, lo_id, correctness, at):
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "correctness, hints_used, created_at) VALUES (?, ?, ?, 'short_answer', 'independent_attempt', ?, 0, ?)",
            (attempt_id, f"pi_{attempt_id}", lo_id, correctness, at))


def _report(paths):
    from typer.testing import CliRunner

    from learnloop.cli import app

    result = CliRunner().invoke(app, ["reader", "report", "--vault", str(paths.root), "--json"])
    assert result.exit_code == 0, result.output
    return json.loads(result.output)["reading_paths"]["skipped_core"]


def test_f4_the_report_counts_misses_after_a_core_skip_only(tmp_path, monkeypatch):
    paths, repository, _ = _vault(tmp_path, monkeypatch, labels={"sec_history": "enrichment"},
                                  overrides=[("sec_spectral", "skip"), ("sec_history", "skip")])
    with repository.connection() as connection:
        skip_at = connection.execute(
            "SELECT created_at FROM reader_path_sections WHERE section_id = 'sec_spectral' "
            "AND learner_override = 'skip'").fetchone()[0]
    from learnloop.clock import parse_utc

    at = parse_utc(skip_at)
    stamp = lambda delta: (at + delta).isoformat().replace("+00:00", "Z")  # noqa: E731
    _attempt(paths, "att_earlier", "lo_spectral", 0.0, stamp(-timedelta(days=1)))  # before the skip
    _attempt(paths, "att_unrelated", "lo_diag", 0.0, stamp(timedelta(hours=1)))  # another LO
    empty = _report(paths)
    assert (empty["skips"], empty["by_label"], empty["with_learning_objects"]) == (1, {"core": 1}, 1)
    assert (empty["assessments"], empty["misses"], empty["pending"]) == (0, 0, 1)
    _attempt(paths, "att_after", "lo_spectral", 0.0, stamp(timedelta(hours=2)))  # a subsequent miss
    _attempt(paths, "att_ok", "lo_spectral", 1.0, stamp(timedelta(hours=3)))
    report = _report(paths)
    assert (report["assessments"], report["misses"], report["with_miss"], report["pending"]) == (2, 1, 1, 0)
    assert report["learning_objects_missed"] == 1
    # Read it anyway ends the skip: a miss after that is no longer after a skipped section.
    monkeypatch._rw7b_clock.advance(hours=4)
    call(context(paths.root), "reader.reading_path_override",
         {"extractionId": EXT, "depth": "learn_to_use_it", "sectionId": "sec_spectral", "choice": "read_anyway"})
    _attempt(paths, "att_later", "lo_spectral", 0.0, stamp(timedelta(hours=5)))
    assert _report(paths)["misses"] == 1


def test_f4_the_report_without_the_adapter_and_with_the_guide_off_is_as_before(tmp_path, monkeypatch):
    from learnloop.reader.reader_report import build_reader_report

    paths, _repository, _ = _vault(tmp_path, monkeypatch, overrides=[("sec_spectral", "skip")])
    assert "skipped_core" not in build_reader_report(paths.sqlite_path)["reading_paths"]
    append_config_toml(paths.root, GUIDE_OFF)
    from typer.testing import CliRunner

    from learnloop.cli import app

    result = CliRunner().invoke(app, ["reader", "report", "--vault", str(paths.root), "--json"])
    assert "reading_paths" not in json.loads(result.output)
