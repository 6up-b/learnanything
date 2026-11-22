"""What other test files use from ``tests/test_ux_phase1_add_source.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY: a file run alone found it empty
from learnloop_sidecar.context import SidecarContext
import learnloop_sidecar.handlers  # noqa: F401 -- register methods before registry reads
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.ux_phase1_support import CLOCK, fake_services


def call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _held_ctx(root):
    """A sidecar whose queue only records: nothing drains, so the state right
    after Add (registered, not yet extracted) can be observed."""

    ctx = SidecarContext()
    ctx.load(root)
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=CLOCK, services=fake_services())
    ctx.ingest_jobs._ensure_worker = lambda: None  # type: ignore[method-assign]
    return ctx


def _draining_ctx(root):
    ctx = SidecarContext()
    ctx.load(root)
    ctx.ingest_jobs.bind(ctx.repository, root, background=False, clock=CLOCK, services=fake_services())
    return ctx
