"""What other test files use from ``tests/test_hint_h2a_review_round2.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import sqlite3
from contextlib import closing

from learnloop.db.repositories import Repository
from learnloop.hints import service as S
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.hint_fakes import ITEM, WORK, ChooserFake, WriterFake, hint_vault, prefer, store_map


ARGMAX = '[hints]\nchoice_policy = "argmax"\n'
SELF_GRADE = {"criterionPoints": {"cdf": 2, "value": 0}, "confidence": 3}


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _context(paths, *, inline: bool = False) -> SidecarContext:
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    ctx.hints_inline = inline
    ctx.hint_seed = "e"
    return ctx


def _attempt(paths, attempt_id: str) -> dict:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return dict(connection.execute("SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,)).fetchone())


def _two_sidecars(tmp_path, option: str):
    """Sidecar B prepares a hint of submission ``k1`` (written, not yet
    read); sidecar A will submit ``k1``. Both on one vault."""

    paths = hint_vault(tmp_path, config=ARGMAX)
    store_map(paths)
    a, b = _context(paths), _context(paths)
    session = _call(a, "start_session", {"energy": "medium"})["sessionId"]
    b.hint_writer_client = WriterFake()
    b.hint_chooser_client = ChooserFake(prefer(option, 0.9))
    params = {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1", "answerMd": WORK}
    if option.endswith(("L4", "L5")):
        params["takenLevel"] = int(option[-1])
    job = _call(b, "practice.request_hint", params)["jobId"]
    assert b.hint_jobs.get(job).done.wait(30)
    return paths, a, b, session, job


def _setup(tmp_path, *, map_payload: dict | None = None):
    paths = hint_vault(tmp_path, config=ARGMAX)
    store_map(paths, map_payload)
    return paths, load_vault(paths.root), Repository.attach(paths.sqlite_path)


def _ask(vault, repository, option: str, answers=(), *, deliver: bool = True, **overrides):
    writer = WriterFake(list(answers))
    values = {"practice_item_id": ITEM, "session_id": "s1", "submission_id": "k1", "work_md": WORK}
    values.update(overrides)
    result = S.request_hint(vault, repository, S.HintRequestV1(**values), writer_client=writer,
                            chooser_client_factory=lambda: ChooserFake(prefer(option, 0.9)), seed="r")
    if deliver and result.status == S.READY:
        assert S.deliver(repository, str(result.assist_id)) is not None
    return result, writer
