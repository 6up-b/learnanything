"""What other test files use from ``tests/test_learner_pick_proposal.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

import learnloop.clock as clock_module
import learnloop.scheduling.scheduler as scheduler_module
from learnloop.db.stores.practice_index import insert_proposal
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.helpers import create_daily_plan_vault


DAY1 = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _draw(monkeypatch, promoted: str | None) -> None:
    """The scheduler's seeded exploration through its own draw seam.

    This vault is at mvp-0.14, where the plan's pool keeps the scheduler's
    seeded draw (router R1's design; plan-determinism review): hashed from the
    session id, a fresh ULID per run, it moves a near-tie to the front of the
    pool in about one session in ten. ``None`` pins the greedy order (the roll
    misses); an item id pins the draw on that alternative wherever it is one.
    """

    def draws(_queue, _session, _now, alternatives):
        ids = [item.practice_item_id for item in alternatives]
        if promoted not in ids:
            return 1.0, 0.0
        return 0.0, (ids.index(promoted) + 0.5) / len(ids)

    monkeypatch.setattr(scheduler_module, "_exploration_draws", draws)


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: DAY1)
    _draw(monkeypatch, None)  # the plan these tests build is the greedy one
    paths = create_daily_plan_vault(tmp_path / "vault",
                                    learning_objects={"lo_extra": [("pi_extra_1", 2.0), ("pi_extra_2", 2.0)]})
    context = SidecarContext()
    context.load(paths.root)
    context.grading_provider_override = "manual"
    _vault, repository = context.require_vault()
    with repository.connection() as connection:
        insert_proposal(connection, id="pp_test", created_at="2026-10-12T08:59:00Z", origin="rpc",
                        query_id="q", query_text="extra practice", constraints={}, path="direct",
                        path_reason="test", signals={}, reranked=False, rerank_status="disabled",
                        rerank_model=None,
                        proposed=[{"practice_item_id": "pi_extra_1", "rank": 1, "relevance": None,
                                   "kind": "item", "rationale": "fits"}],
                        exclusions={}, manifest={}, algorithm_version="mvp-0.14",
                        caller="tutor", caller_ref="qe_1", intent="practice")
    return context, paths


def _interventions(repository):
    from learnloop.db.stores.source_service import interventions

    with repository.connection() as connection:
        return interventions(connection)
