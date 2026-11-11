"""What other test files use from ``tests/test_hint_h2b_review.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from learnloop.hints.report import build_hints_report, item_caps
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.hint_fakes import ITEM, WORK, ChooserFake, WriterFake, hint_vault, prefer, store_map
from tests.split_live_helpers import ReadyRuntime
from tests.stuck_prompt_helpers import StuckFake


PARTIAL = {"criterionPoints": {"cdf": 2, "value": 0}, "confidence": 3}


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _rows(paths, sql, params=()):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(sql, params)]


def _attempt(paths, attempt_id):
    [row] = _rows(paths, "SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,))
    return row


def _sidecar(tmp_path, config: str = "", *, map_: bool = True):
    paths = hint_vault(tmp_path, config='[hints]\nchoice_policy = "argmax"\n' + config)
    if map_:
        store_map(paths)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    ctx.hints_inline = True
    ctx.hint_seed = "e"
    ctx.hint_writer_client = WriterFake()
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    return paths, ctx, session


@pytest.fixture
def grader(monkeypatch):
    """A blind grader fake behind the sidecar's grading provider (the
    workbench submit has no self-grade)."""

    import learnloop.attempts.attempts as attempts_module
    import learnloop_sidecar.handlers.practice as practice

    monkeypatch.setattr(attempts_module, "AUTO_PRIME_REVEAL_THRESHOLD", 10.0)
    client = StuckFake()
    monkeypatch.setattr(practice, "ready_grading_provider",
                        lambda vault, override=None: ("fake", ReadyRuntime(), client))
    return client


def _hint(ctx, session, key, option="next_step@L3", **params):
    ctx.hint_chooser_client = ChooserFake(prefer(option, 0.9))
    return _call(ctx, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM, "submissionId": key,
                                                "answerMd": WORK, **params})["result"]


def _into_steps(ctx, session, key, *, carried: int = 0):
    # The screen names no submission (ruling R1): the server's window needs none.
    payload = {"origin": "practice", "entry": "practice_screen", "practiceItemId": ITEM, "stemMd": "Find P.",
               "carriedHints": carried}
    view = _call(ctx, "workbench.open", payload)["session"]
    _call(ctx, "workbench.save_step", {"sessionId": view["sessionId"], "clientIdempotencyKey": "s1", "op": "add",
                                       "bodyMd": WORK})
    return view


def _wb_submit(ctx, wb_session, session):
    return _call(ctx, "workbench.submit", {"sessionId": wb_session, "practiceSessionId": session})["attempt"]


def _hinted_wrong_attempt(ctx, session, key="k1"):
    _hint(ctx, session, key)
    return _call(ctx, "submit_attempt", {
        "sessionId": session, "practiceItemId": ITEM, "answerMd": WORK, "attemptType": "independent_attempt",
        "hintsUsed": 0, "selfGrade": PARTIAL, "submissionId": key})["attemptId"]


def _report(paths, **kwargs):
    vault = load_vault(paths.root)
    return build_hints_report(paths.sqlite_path, item_caps=item_caps(vault.practice_items.values()), **kwargs)
