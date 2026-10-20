"""Which source/chooser pair serves Today (router R2a, plan_router_r2_v1 §3.2).

``spec_daily_loop_v1.md`` §6.8's switch table, from the router's side:

* below ``mvp-0.23`` (``ROUTER_STAGED_FRAME_VERSIONS``), or with
  ``router.enabled = false``: DL1's pair exactly (``legacy_lanes_v1`` +
  ``lane_quota_v1``, :data:`learnloop.daily_plan.engine.DEFAULT_POLICY`; G8);
* at ``mvp-0.23`` with the router on, or later with ``router.mode =
  "staged"``: the staged frame (``staged_frame_v1``) with its chooser
  (``staged_v1``), exactly R2a. The projection chooser stays
  ``lane_quota_v1`` (DL1 F3: projections never call a live or sampled
  chooser);
* at the R2b + R2c successor (``ROUTER_MIXTURE_VERSIONS``) with ``router.mode =
  "mixture"`` (its default): the staged frame with the logged model mixture
  (``router_mixture_v1``, :mod:`learnloop.daily_plan.router_chooser`), and,
  with ``router.restraint`` on, the restraint gate on mid-block follow-ups
  (``plan_interrupt``). ``serve`` says whether the call serves a step (it
  then waits for the models, up to ``router.timeout_seconds``) or only reads
  (a decision whose models are still out is left open);
* with ``plan.enabled = false`` there is no plan to fill (the open queue serves).

Every entry point that builds a :class:`~learnloop.daily_plan.engine.PlanEnv`
that makes block decisions goes through :func:`policy_for` (the sidecar's plan
RPCs). The P2 bridge's switch is :func:`bridge_active`: it needs no plan.
"""

from __future__ import annotations

from typing import Any

from learnloop.algorithm_versions import ROUTER_MIXTURE_VERSIONS, ROUTER_STAGED_FRAME_VERSIONS
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


def mixture_active(vault: Any) -> bool:
    """The model mixture chooses Today's blocks: the router composes Today, the
    vault is at the R2b + R2c successor or later, and ``router.mode`` is
    ``mixture``. Below the successor the mixture is dormant (``mixture`` serves
    as ``staged``)."""

    config = vault.config
    return (
        router_active(vault)
        and config.algorithms.algorithm_version in ROUTER_MIXTURE_VERSIONS
        and getattr(config.router, "mode", "staged") == "mixture"
    )


def policy_for(
    vault: Any,
    repository: Any,
    *,
    session_id: str | None = None,
    clock: Any = None,
    runtime: Any = None,
    serve: bool = False,
) -> PlanPolicy:
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

    frame = StagedFrame(vault, repository, clock=clock)
    cards = CardGatherer(vault, repository, clock=clock, session_id=session_id)
    if not mixture_active(vault):
        return PlanPolicy(
            source_name=SOURCE_NAME,
            chooser=StagedChooser(card_builder=cards),
            make_source=StagedFrameFactory(frame),
            projection_chooser=LaneQuotaChooser(),
            mandatory_refusals=frame.refusals_for,
        )
    from learnloop.daily_plan.router_chooser import RestraintGate, RouterChooser
    from learnloop.daily_plan.router_runtime import default_runtime

    runtime = runtime if runtime is not None else default_runtime()
    restraint = None
    if bool(getattr(vault.config.router, "restraint", False)):
        restraint = RestraintGate(
            vault, repository, runtime, frame=frame, card_builder=cards, session_id=session_id, clock=clock,
            may_defer=not serve,
        )
    return PlanPolicy(
        source_name=SOURCE_NAME,
        chooser=RouterChooser(
            vault, repository, runtime, card_builder=cards, session_id=session_id, clock=clock, may_defer=not serve,
        ),
        make_source=StagedFrameFactory(frame),
        projection_chooser=LaneQuotaChooser(),
        restraint=restraint,
        mandatory_refusals=frame.refusals_for,
    )


__all__ = ["bridge_active", "mixture_active", "policy_for", "router_active"]
