"""Every door that answers a served plan presentation keeps its link under mvp-0.74's session rule (H3-R7, H3-R29).

A presentation is taken by an answer from its own session, from an answer that names no session, or once its session
has ended (starting a session ends every other one, so no answer of that session can still come). Only a presentation
still open in another session is left for that session's answer. One test per door that names a presentation; the
doors that never name one (exam sittings, lesson checks, lesson probes, inline checks, pads, teach-back, the CLI, the
TUI, imports, the MCP tools, the simulator) are pinned by the inventory test at the end. Fakes only; no network.
"""

from __future__ import annotations

import ast
import sqlite3
from pathlib import Path

import pytest

import learnloop.clock as clock_module
import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext

from tests.difficulty_replay_helpers import _iso
from tests.helpers import NOW, create_daily_plan_vault, create_placement_vault
from tests.router_r2a_serving_helpers import FROZEN, _call
from tests.reader_workbench_rw2a_helpers import ITEM, _context, _open, _step, _vault, grader  # noqa: F401


def _bound(sqlite_path, attempt_id):
    with sqlite3.connect(sqlite_path) as connection:
        return connection.execute("SELECT plan_presentation_id FROM practice_attempts WHERE id = ?",
                                  (attempt_id,)).fetchone()[0]


def _desktop(tmp_path, monkeypatch):
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: FROZEN)
    paths = create_daily_plan_vault(tmp_path / "vault", version=LATEST_ALGORITHM_VERSION,
                                    learning_objects={"lo_extra": [("pi_extra_1", 2.0), ("pi_extra_2", 2.0)]})
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    return paths, ctx


def _submit(ctx, session_id, item_id, presentation_id, **extra):
    return _call(ctx, "submit_attempt", {
        "sessionId": session_id, "practiceItemId": item_id, "answerMd": "My answer.",
        "attemptType": "independent_attempt", "hintsUsed": 0,
        "selfGrade": {"criterionPoints": {"correctness": 4}, "confidence": 4},
        "planPresentationId": presentation_id, **extra,
    })


def test_desktop_submit_in_the_serving_session_binds(tmp_path, monkeypatch):
    paths, ctx = _desktop(tmp_path, monkeypatch)
    session = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    served = _call(ctx, "next_plan_item", {"sessionId": session, "serve": True})["step"]
    result = _submit(ctx, session, served["practiceItemId"], served["presentationId"])
    assert _bound(paths.sqlite_path, result["attemptId"]) == served["presentationId"]


def test_desktop_submit_after_a_new_session_binds_the_ended_sessions_presentation(tmp_path, monkeypatch):
    """The app restarts and starts a new session (ending the serving one); the restored draft names the
    presentation it was opened under. Failed before: the link was refused as another session's."""

    paths, ctx = _desktop(tmp_path, monkeypatch)
    first = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    served = _call(ctx, "next_plan_item", {"sessionId": first, "serve": True})["step"]
    second = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    assert second != first and Repository(paths.sqlite_path).fetch_session(first)["ended_at"] is not None
    result = _submit(ctx, second, served["practiceItemId"], served["presentationId"])
    assert _bound(paths.sqlite_path, result["attemptId"]) == served["presentationId"]


def test_outbox_retry_binds_once_and_an_ended_sessions_retry_is_refused_by_the_door(tmp_path, monkeypatch):
    """A queued submit retried under its retry key returns the attempt its first write bound. A retry carrying a
    session that has ended never reaches the attempt: the submit door refuses it (``session ended``)."""

    from learnloop_sidecar.errors import SidecarError

    paths, ctx = _desktop(tmp_path, monkeypatch)
    first = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
    served = _call(ctx, "next_plan_item", {"sessionId": first, "serve": True})["step"]
    result = _submit(ctx, first, served["practiceItemId"], served["presentationId"], submissionId="outbox-1")
    assert _bound(paths.sqlite_path, result["attemptId"]) == served["presentationId"]
    again = _submit(ctx, first, served["practiceItemId"], served["presentationId"], submissionId="outbox-1")
    assert again["attemptId"] == result["attemptId"]
    _call(ctx, "start_session", {"availableMinutes": 25})
    with pytest.raises(SidecarError, match="ended"):
        _submit(ctx, first, served["practiceItemId"], served["presentationId"], submissionId="outbox-2")


def test_phone_submit_in_the_adopted_session_binds(tmp_path, monkeypatch):
    """The phone adopts the desktop's open session (its id kept) and answers the step the desktop served."""

    pytest.importorskip("starlette")
    from tests.mobile_v3_probes_helpers import PHONE, _adopt, _world
    from tests.mobile_v3_probes_helpers import _call as _call_as

    world = _world(tmp_path, monkeypatch, version=LATEST_ALGORITHM_VERSION, owner=None)
    served = _call(world.ctx, "next_plan_item", {"sessionId": world.session, "serve": True})["step"]
    assert served["kind"] == "item" and served["presentationId"]
    _adopt(world, PHONE)
    result = _call_as(world.ctx, "submit_attempt", {
        "sessionId": world.session, "practiceItemId": served["practiceItemId"], "answerMd": "An answer.",
        "attemptType": "independent_attempt", "latencySeconds": 60, "planPresentationId": served["presentationId"],
    }, PHONE)
    assert _bound(world.paths.sqlite_path, result["attemptId"]) == served["presentationId"]


def test_workbench_submit_after_its_admission_session_ended_binds(tmp_path, grader):
    """A workbench problem keeps the presentation it was opened under; its admission's practice session ends before
    the submit, which then runs in the open session (``_practice_session``). Failed before: refused as another
    session's."""

    paths, repository = _vault(tmp_path)
    ctx = _context(paths.root)
    first = _call(ctx, "start_session", {})["sessionId"]
    with repository.connection() as connection:
        connection.execute("INSERT INTO attention_blocks(id, action, budget_minutes, content_hash, created_at) "
                           "VALUES ('blk_wb', 'practice', 10, 'h', ?)", (_iso(NOW),))
        connection.execute("INSERT INTO plan_presentations(id, block_id, practice_item_id, position, origin, served_at, "
                           "session_id) VALUES ('pres_wb', 'blk_wb', ?, 1, 'chooser', ?, ?)", (ITEM, _iso(NOW), first))
        connection.commit()
    problem = _open(ctx, entry="check_me", planPresentationId="pres_wb")
    _step(ctx, problem["sessionId"], "a", bodyMd="A = U Sigma V^T")
    second = _call(ctx, "start_session", {})["sessionId"]
    payload = _call(ctx, "workbench.submit", {"sessionId": problem["sessionId"], "practiceSessionId": second})
    assert _bound(paths.sqlite_path, payload["attempt"]["attemptId"]) == "pres_wb"


def _served_in(tmp_path, *, ended: bool):
    paths = create_placement_vault(tmp_path / "vault", version=LATEST_ALGORITHM_VERSION)
    vault, repo = load_vault(paths.root), Repository(paths.sqlite_path)
    sync_vault_state(vault, repo, clock=FrozenClock(NOW))
    owner = repo.create_session()
    with repo.connection() as connection:
        connection.execute("INSERT INTO attention_blocks(id, action, budget_minutes, content_hash, created_at) "
                           "VALUES ('block', 'practice', 10, 'hash', ?)", (_iso(NOW),))
        connection.execute("INSERT INTO plan_presentations(id, block_id, practice_item_id, origin, served_at, session_id) "
                           "VALUES ('served', 'block', 'pi_eig_mid', 'chooser', ?, ?)", (_iso(NOW), owner))
        connection.commit()
    if ended:
        repo.end_session(owner, clock=FrozenClock(NOW))
    return vault, repo


def test_a_draft_naming_no_session_binds_an_unused_presentation(tmp_path):
    vault, repo = _served_in(tmp_path, ended=False)
    result = complete_self_graded_attempt(vault, repo, AttemptDraft("pi_eig_mid", "answer", plan_presentation_id="served"),
                                          SelfGradeInput({"correctness": 3}, 3), clock=FrozenClock(NOW))
    assert _bound(repo.sqlite_path, result.attempt_id) == "served"


@pytest.mark.parametrize("ended", [False, True])
def test_another_sessions_presentation_binds_only_once_that_session_has_ended(tmp_path, ended):
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    from tests.surprise_reads_ad_forecast_helpers import _surprise

    vault, repo = _served_in(tmp_path, ended=ended)
    stranger = repo.create_session()
    result = complete_self_graded_attempt(vault, repo, AttemptDraft("pi_eig_mid", "answer", session_id=stranger,
                                                                    plan_presentation_id="served"),
                                          SelfGradeInput({"correctness": 3}, 3), clock=FrozenClock(NOW))
    assert _bound(repo.sqlite_path, result.attempt_id) == ("served" if ended else None)
    live = _surprise(repo)
    rebuild_all_derived_state(vault, repo)
    assert _surprise(repo) == live


def test_only_the_practice_and_workbench_submits_name_a_plan_presentation():
    """The door inventory: every production draft that names a plan presentation is built by the sidecar's practice
    submit (desktop and phone, the outbox's retries, the workbench's submit through it) or is the replay's draft. A
    new door naming one joins this file with its own test."""

    root = Path(__file__).resolve().parents[1] / "src"
    found = set()
    for path in root.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
                if name in ("AttemptDraft", "SubmitAttemptInput", "DontKnowInput") and any(
                        keyword.arg == "plan_presentation_id" for keyword in node.keywords):
                    found.add(path.relative_to(root).as_posix())
    assert found == {"learnloop/attempts/attempts.py", "learnloop_sidecar/handlers/practice.py",
                     "learnloop_sidecar/handlers/workbench.py"}
