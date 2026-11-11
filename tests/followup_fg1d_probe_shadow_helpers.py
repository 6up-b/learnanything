"""What other test files use from ``tests/test_followup_fg1d_probe_shadow.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from learnloop.algorithm_versions import FOLLOWUP_SERVE_ALGORITHM_VERSION, INTERVAL_FACTOR_ALGORITHM_VERSION
from learnloop.clock import SystemClock
from learnloop.substrate.replay import rebuild_derived_state
from learnloop.substrate.shadow_rebuild import shadow_rebuild
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext

from tests.followup_serve_helpers import BlindRivalClient, live_shape_vault
from tests.followup_rival_factor_helpers import _Ready, _call


ZERO = {"mastery": 0, "facet": 0, "schedule": 0}
INSTANT = datetime(2026, 11, 4, 15, 0, 0, tzinfo=UTC)


def _summary(result):
    assert result.live_database_unchanged
    return result.learner_state_diff["summary"]


@pytest.fixture(params=[FOLLOWUP_SERVE_ALGORITHM_VERSION, INTERVAL_FACTOR_ALGORITHM_VERSION])
def desk(tmp_path, monkeypatch, request):
    # FG1's tag and RO1's successor: neither changes the fold, so the answer holds at both.
    monkeypatch.setattr(SystemClock, "now", lambda self: INSTANT)
    paths, vault, repository = live_shape_vault(tmp_path, version=request.param)
    # The seeded vault predates the tag: rebuild it, as the owner does after an upgrade, so the
    # shadow starts at 0/0/0 and whatever it reads afterwards is the journey's.
    rebuild_derived_state(vault, repository)
    assert _summary(shadow_rebuild(load_vault(paths.root))) == ZERO
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.post_attempt_worker.autostart = False
    client = BlindRivalClient()
    monkeypatch.setattr("learnloop_sidecar.handlers.practice.ready_grading_provider",
                        lambda *_a, **_k: ("fake", _Ready(), client))
    session = _call(ctx, "start_session", {"available_minutes": 30})
    return SimpleNamespace(ctx=ctx, client=client, session=session.get("sessionId") or session["session_id"], paths=paths)
