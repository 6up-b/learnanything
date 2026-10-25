"""Reader workbench RW7b, fix round 2 (scoped Codex verify 20261025-143353-i8EshF).

* **Medium (F1 for auto-completed plans)** When the path excluded every
  remaining reading and no practice was left, the plan closed by itself
  (``complete``). Turning ``reading_paths.plan_uses_path`` or
  ``reading_paths.enabled`` off must reopen it and put the predecessor's
  reading back (G47 for existing plans), recorded on the receipt's
  transition. A plan the learner ended ("Done for today") or one with a
  reading started or ended stays as it is.
* **Low (the projection)** A path reading the switch withdrew
  (``reading_path_off``) is no reading of the day in ``simulate_blocks``
  either, so the projected readings show the predecessor's section that live
  selection now chooses.

Fakes only (``PathJudgeFake``); no network.
"""
from __future__ import annotations

import pytest

from learnloop.daily_plan import engine as E
from learnloop.vault.loader import load_vault
from tests.helpers import append_config_toml
from tests.reading_path_fixtures import call, context
from tests.test_plan_follows_path import GUIDE_OFF, OFF, _split, _vault
from tests.test_rw7b_codex_review_fixes import LABELS, _stage_reading

EVERY_ENRICHMENT = {section: "enrichment" for section in ("sec_eigen", "sec_spectral", "sec_diag", "sec_history")}


def _plan_row(repository) -> dict:
    with repository.connection() as connection:
        [row] = connection.execute(
            "SELECT status, stop_reason, completed_at FROM daily_plans ORDER BY created_at, id").fetchall()
    return dict(row)


def _skip_to_done(ctx, session_id) -> dict:
    """Skip every practice item the plan serves until it has nothing left."""

    for _ in range(40):
        step = call(ctx, "next_plan_item", {"sessionId": session_id, "serve": False})["step"]
        if step["kind"] == "done":
            return step
        assert step["kind"] == "item", step
        call(ctx, "next_plan_item", {"sessionId": session_id, "skipPracticeItemId": step["practiceItemId"],
                                     "serve": False})
    raise AssertionError("the plan never finished")



# -- Medium: a plan auto-completed because the path excluded every reading -----------------------------


@pytest.mark.parametrize("switch", [OFF, GUIDE_OFF], ids=["plan_uses_path_off", "guide_off"])
def test_an_auto_completed_plan_whose_path_left_no_reading_is_reopened_to_the_predecessors_reading(
        tmp_path, monkeypatch, switch):
    paths, repository, _ = _vault(tmp_path, monkeypatch, labels=EVERY_ENRICHMENT)
    ctx = context(paths.root)
    session_id = call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    assert _skip_to_done(ctx, session_id)["kind"] == "done"
    closed = _plan_row(repository)
    assert closed["status"] == "complete" and closed["stop_reason"] != "learner_stopped"
    built = _split(repository)
    assert built["reading"] is None and built["reading_path"]["predecessor"]["section_id"] == "sec_eigen"

    append_config_toml(paths.root, switch)
    ctx = context(paths.root)
    # The plan boundary: reconcile reopens it, and serving reaches the predecessor's reading.
    step = call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
    assert step["kind"] == "reading" and step["reading"]["sectionId"] == "sec_eigen"
    reopened = _plan_row(repository)
    assert reopened == {"status": "open", "stop_reason": None, "completed_at": None}
    split = _split(repository)
    assert split["reading"] == built["reading_path"]["predecessor"]
    transition = split["reading_path"]["transition"]
    assert transition["reason"] == "reading_path_off" and transition["from"] is None
    assert transition["to"]["section_id"] == "sec_eigen"
    assert transition["reopened"] == {"status": "complete", "stop_reason": closed["stop_reason"],
                                      "completed_at": closed["completed_at"]}
    # Recorded once: the next boundary does not rewrite it.
    call(context(paths.root), "get_daily_plan", {})
    assert _split(repository)["reading_path"]["transition"] == transition


def test_a_plan_the_learner_ended_stays_ended_when_the_switch_turns_off(tmp_path, monkeypatch):
    paths, repository, _ = _vault(tmp_path, monkeypatch, labels=EVERY_ENRICHMENT)
    ctx = context(paths.root)
    session_id = call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    step = call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
    assert step["kind"] == "item"
    call(ctx, "plan_keep_going", {"sessionId": session_id, "stop": True})
    ended, before = _plan_row(repository), _split(repository)
    assert (ended["status"], ended["stop_reason"]) == ("stopped", "learner_stopped")
    append_config_toml(paths.root, OFF)
    step = call(context(paths.root), "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
    assert step["kind"] == "done"
    assert _plan_row(repository) == ended and _split(repository) == before


def test_an_auto_completed_plan_with_a_reading_ended_stays_complete(tmp_path, monkeypatch):
    paths, repository, _ = _vault(tmp_path, monkeypatch, labels=LABELS)
    ctx = context(paths.root)
    session_id = call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    _stage_reading(ctx, session_id)
    started = call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
    assert started["reading"]["sectionId"] == "sec_spectral"
    call(ctx, "plan_reading_ended", {"outcome": "skipped", "sessionId": session_id})
    assert _skip_to_done(ctx, session_id)["kind"] == "done"
    closed, before = _plan_row(repository), _split(repository)
    assert closed["status"] == "complete"
    append_config_toml(paths.root, OFF)
    step = call(context(paths.root), "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
    assert step["kind"] == "done"
    assert _plan_row(repository) == closed and _split(repository) == before


# -- Low: the withdrawn block is no reading of the projection ------------------------------------------


def test_a_withdrawn_path_reading_leaves_the_predecessors_reading_in_the_projection(tmp_path, monkeypatch):
    from learnloop.daily_plan.view import project_blocks

    paths, repository, _ = _vault(tmp_path, monkeypatch, labels=LABELS)
    ctx = context(paths.root)
    session_id = call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    staged = _stage_reading(ctx, session_id)
    assert staged["reading"]["sectionId"] == "sec_spectral"
    append_config_toml(paths.root, OFF)
    env = E.PlanEnv(load_vault(paths.root), repository)
    # Reconcile withdraws the staged block (no boundary crossed yet) ...
    record = E.reconcile(env, E.latest_today(env))
    assert next(block for block in record.blocks if block.id == staged["blockId"]).withdrawn_path_reading
    assert record.current_block() is None
    # ... and the projection from that record names the predecessor's reading,
    projection_context, _built = E._live_context(env, record)
    projected = [row["reading_title"] for row in project_blocks(record, projection_context, env.policy)
                 if row["reading_title"]]
    assert projected == ["1 Eigenvalues"]
    # which is what the next boundary (advance) chooses live.
    _record, step = E.advance(env, serve=True)
    assert step["kind"] == "reading" and step["reading"]["section_id"] == "sec_eigen"
