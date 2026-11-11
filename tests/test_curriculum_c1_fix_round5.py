"""Curriculum C1, fix round 5 (final verify 20261101-030938-zfScC7). Fail-first:

* **Medium 1** (metered spend): the automatic daily refresh asks only the subscription ChatGPT-plan
  route. A metered path-judge route, priced and with budget left, sends nothing (``unavailable``)
  and the plan's receipt stays ``stale``; a learner's Guide judgment on it still runs.
* **Medium 2** (a queued refresh after its gate went off): the worker rechecks C1's complete gate
  on the vault as it is now before it starts and before its claim, and the judge asks it again at
  every request and inside the write; off, nothing is sent or kept.

Every model is a fake; nothing leaves the machine.
"""
from __future__ import annotations

import pytest

from learnloop.source_retrieval import deliverable_path as DP
from tests.deliverable_fixtures import PlanDeliverableFake
from tests.helpers import append_config_toml
from tests.reading_path_fixtures import call, context
from tests.curriculum_c1_plan_follows_path_helpers import (
    C1_OFF,
    CURRICULUM_OFF,
    GUIDE_OFF,
    PRIMARIES,
    RW7B_OFF,
    _at,
    _c1,
    _split,
)
from tests.curriculum_c1_fix_round5_helpers import MeteredFake, _rows

PRICED = "\n[source_retrieval]\nllm_price_per_million = 1.0\n"


# -- Medium 1: plan route only -----------------------------------------------------------------------------


def test_m1_a_metered_route_is_never_asked_by_the_automatic_refresh(tmp_path, monkeypatch):
    from learnloop_sidecar.handlers.deliverables import _work

    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20", config=PRICED)
    c1.clock.advance(days=1)
    fake = MeteredFake(primaries=PRIMARIES)
    ctx = context(c1.paths.root, deliverable_path_client=fake, deliverable_inline=True)
    call(ctx, "get_daily_plan", {})
    assert fake.calls == 0
    assert DP.plan_refresh_route_problem(c1.vault, fake) == "not_plan_route"
    assert _work(ctx).refresh["status"] == "unavailable" and _work(ctx).refresh["reason"] == "not_plan_route"
    split = _split(c1.repository)
    assert split["reading_path"]["deliverable"]["status"] == "stale" and _at(split["reading"]) == ("ext_book", "ch_eigen")
    # A learner's Guide open on the same metered route still judges (today's behaviour).
    call(ctx, "curriculum.path", {"goalId": c1.goal_id})
    assert fake.calls == 1


def test_m1_the_plan_route_is_asked(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")
    c1.clock.advance(days=1)
    fake = PlanDeliverableFake(primaries=PRIMARIES)
    assert DP.plan_refresh_route_problem(c1.vault, fake) is None
    assert DP.refresh_for_plan(c1.vault, c1.repository, client=fake)["status"] == "ready" and fake.calls == 1


# -- Medium 2: the gate on the vault as it is now -----------------------------------------------------------


@pytest.mark.parametrize("switch", [C1_OFF, CURRICULUM_OFF, RW7B_OFF, GUIDE_OFF, "[plan]\nenabled = false\n"],
                         ids=["plan_uses_path", "curriculum", "rw7b", "guide", "plan"])
def test_m2_a_refresh_queued_before_a_switch_went_off_sends_and_writes_nothing(tmp_path, monkeypatch, switch):
    from learnloop_sidecar.handlers import deliverables as H

    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")
    c1.clock.advance(days=1)
    fake = PlanDeliverableFake(primaries=PRIMARIES)
    ctx = context(c1.paths.root, deliverable_path_client=fake)
    queued: list = []
    monkeypatch.setattr(H, "_spawn", lambda _ctx, name, run: queued.append(run) if name == "deliverable-plan-refresh"
                        else run())
    call(ctx, "get_daily_plan", {})
    assert len(queued) == 1  # queued, not run yet
    rows = _rows(c1)
    append_config_toml(c1.paths.root, "\n" + switch)
    ctx.reload()
    queued[0]()
    assert fake.calls == 0 and _rows(c1) == rows
    assert H._work(ctx).refresh["status"] == "switched_off"


def test_m2_the_gate_going_off_at_the_request_or_the_write_keeps_nothing(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")
    c1.clock.advance(days=1)
    on = {"value": True}

    class OffMidCall(PlanDeliverableFake):
        def complete(self, request):
            on["value"] = False  # the switch goes off while the judgment is in flight
            return super().complete(request)

    rows = _rows(c1)
    fake = OffMidCall(primaries=PRIMARIES)
    result = DP.refresh_for_plan(c1.vault, c1.repository, client=fake, still_wanted=lambda _vault: on["value"])
    assert fake.calls == 1 and result["status"] == "switched_off" and _rows(c1) == rows  # nothing written
    # Off before the request: nothing sent.
    on["value"] = True
    calls: list[int] = []
    checks = iter([True])  # the claim's check passes, every later one says off

    def wanted(_vault) -> bool:
        calls.append(1)
        return next(checks, False)

    second = PlanDeliverableFake(primaries=PRIMARIES)
    result = DP.refresh_for_plan(c1.vault, c1.repository, client=second, still_wanted=wanted)
    assert second.calls == 0 and result["status"] == "switched_off" and _rows(c1) == rows
