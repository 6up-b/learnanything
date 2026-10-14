"""Which source/chooser pair serves Today (router R2a, plan_router_r2_v1 §3.2).

``spec_daily_loop_v1.md`` §6.8's switch table, from the router's side:

* below ``mvp-0.23`` (``ROUTER_STAGED_FRAME_VERSIONS``), or with
  ``router.enabled = false``: DL1's pair exactly (``legacy_lanes_v1`` +
  ``lane_quota_v1``, :data:`learnloop.daily_plan.engine.DEFAULT_POLICY`; G8);
* at ``mvp-0.23`` with the router on (``router.mode = "staged"``): the staged
  frame (``staged_frame_v1``) with its chooser (``staged_v1``). The projection
  chooser stays ``lane_quota_v1`` (DL1 F3: projections never call a live or
  sampled chooser);
* with ``plan.enabled = false`` there is no plan to fill (the open queue serves).

Every entry point that builds a :class:`~learnloop.daily_plan.engine.PlanEnv`
that makes block decisions goes through :func:`policy_for` (the sidecar's plan
RPCs). The P2 bridge's switch is :func:`bridge_active`: it needs no plan.
"""

from __future__ import annotations

from typing import Any

from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_VERSIONS
from learnloop.daily_plan.chooser import LaneQuotaChooser
from learnloop.daily_plan.engine import DEFAULT_POLICY, PlanPolicy, plan_active


def bridge_active(vault: Any) -> bool:
    """``golden_path.advance`` goes through the P2 bridge (D13): the R2a
    successor or later with the router's kill switch on."""

    config = vault.config
    return (
        config.algorithms.algorithm_version in ROUTER_STAGED_FRAME_VERSIONS
        and bool(getattr(config.router, "enabled", False))
    )


def router_active(vault: Any) -> bool:
    """The router composes Today: the plan serves and the bridge's switch holds."""

    return plan_active(vault) and bridge_active(vault)


def policy_for(vault: Any, repository: Any, *, session_id: str | None = None, clock: Any = None) -> PlanPolicy:
    """Today's source/chooser pair for one plan env (one RPC)."""

    if not router_active(vault):
        return DEFAULT_POLICY
    from learnloop.daily_plan.router_card import CardGatherer
    from learnloop.daily_plan.staged_frame import (
        SOURCE_NAME,
        StagedChooser,
        StagedFrame,
        StagedFrameFactory,
    )

    mode = getattr(vault.config.router, "mode", "staged")
    if mode != "staged":  # pragma: no cover - the schema admits only "staged" until R2b
        raise ValueError(f"router.mode {mode!r} is not served at this version")
    frame = StagedFrame(vault, repository, clock=clock)
    return PlanPolicy(
        source_name=SOURCE_NAME,
        chooser=StagedChooser(card_builder=CardGatherer(vault, repository, clock=clock, session_id=session_id)),
        make_source=StagedFrameFactory(frame),
        projection_chooser=LaneQuotaChooser(),
    )


__all__ = ["bridge_active", "policy_for", "router_active"]
