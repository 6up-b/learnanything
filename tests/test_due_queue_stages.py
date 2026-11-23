"""The due queue's ranking is a pure stage (``scheduler.rank_due``): it reaches no repository, and its composition
(which the offer trace and the head probe's propensity re-run) reads nothing either."""

from __future__ import annotations

import pytest

from learnloop.scheduling import scheduler
from learnloop.scheduling.device_eligibility import PHONE, DeviceFilter
from learnloop.scheduling.scheduler import OfferTrace, SchedulerSession, read_due_queue, serve_due_queue

from tests.due_queue_helpers import (
    CLOCK,
    LEFT_FOR_DESKTOP,
    SESSION,
    build_figure_vault,
    build_gate_vault,
    build_generated_followup_vault,
    build_intent_targets_vault,
    build_rich_vault,
)


def _no_reads(*_args, **_kwargs):
    raise AssertionError("the ranking read the repository")


@pytest.mark.parametrize(
    ("vault_builder", "serving", "phone"),
    [
        (build_rich_vault, True, False),
        (build_rich_vault, False, False),
        (build_gate_vault, True, False),
        (build_intent_targets_vault, True, False),
        (build_generated_followup_vault, True, False),
        (build_figure_vault, True, True),
    ],
    ids=["rich-serving", "rich-read", "gates", "intent-targets", "generated-followup", "phone"],
)
def test_the_ranking_reads_nothing(tmp_path, monkeypatch, vault_builder, serving, phone):
    vault, repository = vault_builder(tmp_path / "vault")
    real = scheduler.rank_due
    ranked_runs: list[int] = []

    def guarded(vault_, admission, inputs):
        with monkeypatch.context() as patch:
            patch.setattr(repository, "connection", _no_reads)
            ranked = real(vault_, admission, inputs)
            for outcome in (ranked.greedy_queue, ranked.considered_queue):
                ranked.compose(list(outcome), record=False)
        ranked_runs.append(len(ranked.queue))
        return ranked

    monkeypatch.setattr(scheduler, "rank_due", guarded)
    build = serve_due_queue if serving else read_due_queue
    device = DeviceFilter(vault, PHONE, left_for_desktop=frozenset({LEFT_FOR_DESKTOP})) if phone else None
    queue = build(vault, repository, clock=CLOCK, session=SchedulerSession(session_id=SESSION),
                  offer_trace=OfferTrace(), device_filter=device)
    assert ranked_runs == [len(queue)] and queue, "the build ranked through the pure stage"
    if phone:
        assert device.deferred, "the phone's deferred items come back from the stage"
