""""check now" before the app has a practice session (spec §12.6.2; RD7's frontend half): the desks can be open
with no Today session yet, so `check.begin_inline` takes the session as a workbench submit does (the app's open one,
else the most recent open one, else a new one) and returns it for the app to adopt; a check that cannot open starts no
session. The grader is a fake; no model is called."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta

import pytest

from learnloop.curriculum import commitments as C
from learnloop.db.repositories import Repository
from learnloop_sidecar.context import SidecarContext
from tests.approach_map_fakes import ITEM
from tests.hint_fakes import hint_vault
from tests.workbench_help_fakes import call


@pytest.fixture(autouse=True)
def grader(monkeypatch):
    import learnloop_sidecar.handlers.practice as practice
    from tests.split_live_helpers import ReadyRuntime
    from tests.stuck_prompt_helpers import StuckFake

    monkeypatch.setattr(practice, "ready_grading_provider", lambda vault, override=None: ("fake", ReadyRuntime(), StuckFake()))


def _vault(tmp_path):
    paths = hint_vault(tmp_path)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.post_attempt_worker.autostart = False
    repository = Repository.attach(paths.sqlite_path)
    yesterday = (datetime.now(UTC) - timedelta(days=1)).date().isoformat()
    commitment = C.create_commitment(
        repository, action="test_me_later", intent_text="check later",
        targets=[{"target_kind": "legacy_practice_item", "target_ref": ITEM, "role": "required"}],
        depth_preset="keep_in_touch", client_idempotency_key="rd7b-session", due_hint=yesterday).id
    return paths, ctx, commitment


def _sessions(paths) -> list[str]:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        return [row[0] for row in connection.execute("SELECT id FROM sessions ORDER BY started_at")]


def test_with_no_session_the_check_opens_in_a_new_one_and_returns_it(tmp_path):
    paths, ctx, commitment = _vault(tmp_path)
    assert _sessions(paths) == []
    card = call(ctx, "check.begin_inline", {"requestId": "r1", "commitmentId": commitment, "visible": {}})
    [session] = _sessions(paths)
    assert card["practiceSession"]["sessionId"] == session
    assert card["administrationToken"]


def test_without_one_named_the_most_recent_open_session_is_used(tmp_path):
    paths, ctx, commitment = _vault(tmp_path)
    open_session = call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    card = call(ctx, "check.begin_inline", {"requestId": "r1", "commitmentId": commitment, "visible": {}})
    assert card["practiceSession"]["sessionId"] == open_session
    assert _sessions(paths) == [open_session]


def test_a_check_that_cannot_open_starts_no_session(tmp_path):
    paths, ctx, commitment = _vault(tmp_path)
    call(ctx, "check.begin_inline", {"requestId": "r1", "commitmentId": commitment, "visible": {}})
    before = _sessions(paths)
    with pytest.raises(Exception) as refused:
        call(ctx, "check.begin_inline", {"requestId": "r2", "commitmentId": "cm_other", "visible": {}})
    assert getattr(refused.value, "code", None) == "administration_open"
    assert _sessions(paths) == before
