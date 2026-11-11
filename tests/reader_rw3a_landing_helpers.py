"""What other test files use from ``tests/test_reader_rw3a_landing.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import sqlite3

import learnloop.clock as clock_module
from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.helpers import add_followup_item, create_daily_plan_vault
from tests.reader_cues_helpers import _CLOCK, _active_error, _ir, _refs
from tests.router_r2a_serving_helpers import FROZEN
from tests.source_inventory_helpers import _persist, _register_revision


A = ROUTER_STAGED_FRAME_ALGORITHM_VERSION


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


#: How the pick lands in today's plan (``engine.learner_pick``), by the
#: session's budget: a new one-item pick block with its own decision (review
#: F4), the item already planned (its block's decision), or a plan with
#: nothing left open (an open-list pick: a presentation with no decision).
CASES = {"new_pick_block": 3, "planned": 25, "open_list": 1}


def _world(tmp_path, monkeypatch, *, version: str = A):
    """An mvp-0.23 daily-plan vault with the router on, whose Guide carries a
    margin cue (an active error on lo_svd_definition, whose item cites ext1),
    a second item on that LO for "check me" to propose, and two one-minute
    items elsewhere that fill a small plan. ``version`` sets a later successor
    (router R2b + R2c's landing runs the same check under the mixture)."""

    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: FROZEN)
    paths = create_daily_plan_vault(
        tmp_path / "vault", version=version,
        learning_objects={"lo_extra": [("pi_extra_1", 1.0), ("pi_extra_2", 1.0)]},
    )
    repository = Repository(paths.sqlite_path)
    _register_revision(repository, source_id="src1", revision_id="rev1")
    _persist(repository, _ir(), revision_id="rev1", extraction_id="ext1")
    vault = load_vault(paths.root)
    item = vault.practice_items["pi_svd_define_001"]
    item.provenance.source_refs = _refs(("s1", "s2", "s3", "s5"))
    upsert_practice_item(paths.root, item, clock=_CLOCK)
    add_followup_item(paths.root)
    _active_error(repository)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    return paths, ctx


def _counts(paths) -> dict[str, int]:
    with sqlite3.connect(paths.sqlite_path) as connection:
        return {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("router_decisions", "plan_presentations", "practice_attempts")
        }


def _check_me(ctx) -> dict:
    marks = _call(ctx, "reader.guide_plan", {"extractionId": "ext1"})["cues"]["marks"]
    assert marks, "the Guide's misunderstanding passages carry margin cues"
    result = _call(ctx, "reader.cue_action", {"extractionId": "ext1", "cueId": marks[0]["cueId"], "action": "check_me"})
    check = result["check"]
    assert check["status"] == "found" and check["proposalId"]
    return check


def _picked(ctx, paths, minutes: int):
    session_id = _call(ctx, "start_session", {"availableMinutes": minutes})["sessionId"]
    _call(ctx, "get_daily_plan", {"sessionId": session_id})
    before = _counts(paths)
    check = _check_me(ctx)
    # The Reader's tap proposes only: no router decision, no presentation.
    assert _counts(paths) == before
    # The shell's learner pick (App.pickCheckMe: no scheduler candidate, the proposal).
    result = _call(ctx, "plan_learner_pick", {"practiceItemId": check["practiceItemId"], "sessionId": session_id,
                                              "proposalId": check["proposalId"]})
    return session_id, check, result, before
