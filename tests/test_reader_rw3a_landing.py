"""Reader RW3a landing onto main after router R2a (docs/reviews/reader-hook-rw3a.md).

RW3a's "check me" proposes one item on the cue's Learning Object
(``reader.cue_action``, under the Reader's caller) and the shell opens it as a
learner pick through ``plan_learner_pick`` (``app/readerCheck.ts``). At
mvp-0.23 ``plan_learner_pick`` logs the pick block's own router decision and
plan presentation (router R2a, review F4). The composition:

* the Reader's tap logs no router decision and no presentation, so the pick's
  is the only one: one decision, one presentation, one delivery naming it;
* the answer, sent with the pick step's ``presentationId`` (``readerCheckOffer``
  carries it since this landing), binds by presentation, not by R1's labelled
  session-rule fallback.
"""

from __future__ import annotations

import sqlite3

import pytest

import learnloop.clock as clock_module
import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_service import interventions
from learnloop.router.outcomes import derive_router_outcomes
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.helpers import add_followup_item, create_daily_plan_vault
from tests.test_reader_cues import _CLOCK, _active_error, _ir, _refs
from tests.test_router_r2a_serving import FROZEN
from tests.test_source_inventory import _persist, _register_revision

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


@pytest.mark.parametrize("case", sorted(CASES))
def test_check_me_goes_through_the_plan_path_and_is_logged_once(tmp_path, monkeypatch, case):
    paths, ctx = _world(tmp_path, monkeypatch)
    _session_id, check, result, before = _picked(ctx, paths, CASES[case])
    step = result["step"]
    assert step["kind"] == "item" and step["practiceItemId"] == check["practiceItemId"]
    assert step["presentationId"]
    after = _counts(paths)
    assert after["plan_presentations"] - before["plan_presentations"] == 1
    with sqlite3.connect(paths.sqlite_path) as connection:
        connection.row_factory = sqlite3.Row
        presentation = connection.execute("SELECT * FROM plan_presentations WHERE id = ?",
                                          (step["presentationId"],)).fetchone()
        decision = connection.execute("SELECT * FROM router_decisions WHERE id = ?",
                                      (presentation["router_decision_id"],)).fetchone()
        repeated = connection.execute(
            "SELECT receipt_key FROM router_decisions GROUP BY receipt_key HAVING COUNT(*) > 1"
        ).fetchall()
        [delivery] = interventions(connection)
    assert presentation["practice_item_id"] == check["practiceItemId"]
    assert repeated == []
    if case == "open_list":
        assert presentation["origin"] == "open_list" and decision is None
        assert after["router_decisions"] == before["router_decisions"]
        assert delivery["router_decision_id"] is None
        return
    assert decision["receipt_key"] == f"plan_block:{step['blockId']}"
    if case == "new_pick_block":
        # R2a review F4: the pick block's own decision, the learner's choice.
        assert presentation["origin"] == "learner_pick"
        assert (decision["learner_pick"], decision["propensity"]) == (1, None)
        assert after["router_decisions"] - before["router_decisions"] == 1
    else:
        # A planned item opened from the list is simply served by its block.
        assert decision["learner_pick"] == 0 and presentation["origin"] != "learner_pick"
    assert decision["chosen_practice_item_id"] == check["practiceItemId"]
    assert delivery["router_decision_id"] == decision["id"]
    assert result["proposalPick"]["routerDecisionId"] == decision["id"]


@pytest.mark.parametrize("case", ["new_pick_block", "planned"])
def test_the_answer_to_a_check_binds_by_the_picks_presentation(tmp_path, monkeypatch, case):
    paths, ctx = _world(tmp_path, monkeypatch)
    session_id, check, result, _before = _picked(ctx, paths, CASES[case])
    step = result["step"]
    # What the shell sends (readerCheckOffer -> planPresentationForServe).
    submitted = _call(ctx, "submit_attempt", {
        "sessionId": session_id, "practiceItemId": check["practiceItemId"], "answerMd": "My answer.",
        "attemptType": "independent_attempt", "hintsUsed": 0,
        "selfGrade": {"criterionPoints": {"correctness": 4}, "confidence": 4},
        "schedulerCandidateId": step.get("schedulerCandidateId"),
        "planPresentationId": step["presentationId"],
    })
    with connect(paths.sqlite_path, read_only=True) as connection:
        bound = connection.execute("SELECT plan_presentation_id FROM practice_attempts WHERE id = ?",
                                   (submitted["attemptId"],)).fetchone()[0]
        decision_id = connection.execute("SELECT router_decision_id FROM plan_presentations WHERE id = ?",
                                         (step["presentationId"],)).fetchone()[0]
        outcomes = {row["decision_id"]: row for row in derive_router_outcomes(connection)}
    assert bound == step["presentationId"]
    outcome = outcomes[decision_id]
    assert (outcome["action_status"], outcome["action_attempt_id"], outcome["action_binding"]) == (
        "taken", submitted["attemptId"], "presentation",
    )
