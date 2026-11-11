"""What other test files use from ``tests/test_reader_workbench_rw2a.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import pytest

from tests.split_live_helpers import ReadyRuntime, split_vault
from tests.stuck_prompt_helpers import StuckFake


ITEM = "pi_svd_compute_001"
OTHER_ITEM = "pi_transpose_001"
STEM = "Exercise 5.14: write the SVD of A."
EXTRACTION = "ext_wb"


def _call(ctx, name: str, params: dict):
    import learnloop_sidecar.handlers  # noqa: F401 - register methods
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _context(root):
    from learnloop_sidecar.context import SidecarContext

    ctx = SidecarContext()
    ctx.load(root)
    return ctx


def _vault(tmp_path, *, config: str = ""):
    from tests.source_retrieval_fakes import seed_source

    paths, _vault, repository = split_vault(tmp_path, version="mvp-0.27", config=config)
    # Reader CA6b fix round 5: the problem's reading exists, with the passages
    # the problems name (s5, s6, s9): the sidecar checks a problem's passages
    # against its reading and refuses another reading's (or none).
    seed_source(repository, source_id="src_wb", revision_id="rev_wb", extraction_id=EXTRACTION, title="Workbench book",
                units={"u_wb": ("Probability", [(f"Line {index}", 1) for index in range(12)])}, furniture=False)
    return paths, repository


@pytest.fixture
def grader(monkeypatch):
    """A blind grader fake behind the sidecar's grading provider."""

    import learnloop_sidecar.handlers.practice as practice

    client = StuckFake()
    monkeypatch.setattr(
        practice, "ready_grading_provider", lambda vault, override=None: ("fake", ReadyRuntime(), client)
    )
    return client


def _open(ctx, **params):
    payload = {"origin": "reader", "entry": "work_through", "practiceItemId": ITEM, "stemMd": STEM,
               "extractionId": EXTRACTION, "spanIds": ["s5"], **params}
    return _call(ctx, "workbench.open", payload)["session"]


def _step(ctx, session_id: str, key: str, op: str = "add", **params):
    return _call(ctx, "workbench.save_step", {"sessionId": session_id, "clientIdempotencyKey": key, "op": op, **params})


def _submit(ctx, session_id: str, **params):
    return _call(ctx, "workbench.submit", {"sessionId": session_id, **params})
