"""Opening the veil on a margin note (a source annotation on an open source) is exposure sized by what the note says
(spec §12.6.4, the owner's overlap rule): the desks name a margin note by its annotation id, so its current words are
what is measured against the answer key. The grader is a fake; no other model is called."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta

import pytest

from learnloop.curriculum import commitments as C
from learnloop.db.repositories import Repository
from learnloop_sidecar.context import SidecarContext
from tests.approach_map_fakes import EXPECTED, ITEM
from tests.hint_fakes import hint_vault
from tests.workbench_help_fakes import call


@pytest.fixture(autouse=True)
def grader(monkeypatch):
    import learnloop_sidecar.handlers.practice as practice
    from tests.split_live_helpers import ReadyRuntime
    from tests.stuck_prompt_helpers import StuckFake

    monkeypatch.setattr(practice, "ready_grading_provider", lambda vault, override=None: ("fake", ReadyRuntime(), StuckFake()))


def test_opening_a_margin_notes_veil_debits_what_the_note_says(tmp_path):
    paths = hint_vault(tmp_path)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.post_attempt_worker.autostart = False
    session = call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    repository = Repository.attach(paths.sqlite_path)
    yesterday = (datetime.now(UTC) - timedelta(days=1)).date().isoformat()
    commitment = C.create_commitment(
        repository, action="test_me_later", intent_text="check later",
        targets=[{"target_kind": "legacy_practice_item", "target_ref": ITEM, "role": "required"}],
        depth_preset="keep_in_touch", client_idempotency_key="rd7b", due_hint=yesterday).id
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute("INSERT INTO source_annotations (id, source_id, created_at) VALUES ('ann_1', 'src_x', 't')")
        connection.execute("INSERT INTO source_annotation_versions (id, annotation_id, version_ordinal, annotation_type, "
                           "learner_text, created_at) VALUES ('anv_1', 'ann_1', 1, 'interpretation', ?, 't')", (EXPECTED,))
        connection.commit()
    token = call(ctx, "check.begin_inline", {"requestId": "r1", "commitmentId": commitment, "sessionId": session,
                                            "visible": {}})["administrationToken"]
    status = call(ctx, "check.expose", {"administrationToken": token, "ref": {"kind": "note", "note_id": "ann_1"},
                                        "kind": "opened_veil"})["protectionStatus"]
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        amounts = [row[0] for row in connection.execute("SELECT amount FROM reveal_events WHERE basis = 'check_inline:opened_veil'")]
    assert amounts and amounts[0] > 0
    assert status["coldNow"] is False
