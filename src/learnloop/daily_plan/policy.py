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


def objective_active(vault: Any) -> bool:
    """Router objective RO4 (spec §8): the objective chooses Today's blocks: the mixture serves and the vault is at
    RO4's tag with ``[router_objective] enabled``. Below the tag, or off, the predecessor's mixture and frame."""

    from learnloop.router_objective_switches import objective_on

    return mixture_active(vault) and objective_on(vault.config)


def policy_for(
    vault: Any,
    repository: Any,
    *,
    session_id: str | None = None,
    clock: Any = None,
    runtime: Any = None,
    serve: bool = False,
    start_only: bool = False,
) -> PlanPolicy:
    """Today's source/chooser pair for one plan env (one RPC). ``start_only``: the prefetch's
    (:func:`learnloop.daily_plan.engine.prefetch_boundary`): its objective chooser starts the job and decides nothing."""

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
        )
    from learnloop.daily_plan.router_chooser import RestraintGate, RouterChooser
    from learnloop.daily_plan.router_runtime import default_runtime

    runtime = runtime if runtime is not None else default_runtime()
    if objective_active(vault):
        # Router objective RO4 (spec §8.2-§8.3): the soft-budget frame and the two policies' learned mix.
        from learnloop.daily_plan.objective_chooser import ObjectiveChooser, ObjectiveRestraintGate

        objective_restraint = None
        if bool(getattr(vault.config.router, "restraint", False)):
            objective_restraint = ObjectiveRestraintGate(
                vault, repository, runtime, frame=frame, card_builder=cards, session_id=session_id, clock=clock,
                may_defer=not serve,
            )
        return PlanPolicy(
            source_name=SOURCE_NAME,
            chooser=ObjectiveChooser(
                vault, repository, runtime, card_builder=cards, session_id=session_id, clock=clock, may_defer=not serve,
                start_only=start_only,
            ),
            make_source=StagedFrameFactory(frame),
            projection_chooser=LaneQuotaChooser(),
            restraint=objective_restraint,
            soft_budget=True,
            lesson_offer=_lesson_offer_builder(vault, repository),
        )
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
    )


def prefetch_can_start(vault: Any, *, runtime: Any = None) -> bool:
    """Spec_instruct_handoff_v1 §3a: a boundary's objective job has something to ask: the objective chooses Today and
    a model is set up. Read before the prefetch builds anything."""

    if not objective_active(vault):
        return False
    from learnloop.daily_plan.router_runtime import default_runtime

    readiness = (runtime if runtime is not None else default_runtime()).readiness(vault)
    return any(reason is None for reason in readiness.values())


def _lesson_offer_builder(vault: Any, repository: Any) -> Any:
    """Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): the boundary's lesson offer, at TE3b's tag with its switch on
    (``router_objective_switches.lesson_offers_on``); None (the predecessor's boundary exactly) otherwise. Each
    boundary first records ``ignored`` on a drawn offer whose boundary passed with no answer."""

    from learnloop.router_objective_switches import lesson_offers_on

    if not lesson_offers_on(vault.config):
        return None

    def build(*, env: Any, record: Any, forced: bool, read_only: bool = False) -> Any:
        from learnloop.daily_plan import lesson_offer as LO
        from learnloop.db.stores import router_suggestions as suggestions

        today, now_iso = env.today(), env.now_iso()
        if read_only:
            with repository.connection() as connection:
                if suggestions.tables_present(connection) and LO.sweep_due(connection, today=today):
                    return LO.Offer(None, needs_write=True)
        else:
            with repository.atomic(), repository.connection() as connection:
                if suggestions.tables_present(connection):
                    LO.sweep_ignored(connection, today=today, now_iso=now_iso)
        if getattr(env, "device", None) is not None:
            from learnloop.router_objective_switches import lessons_compete_with_followups_on

            if lessons_compete_with_followups_on(vault.config):
                # IH2 (spec_instruct_handoff_v1 §5): the phone serves no lesson until V6, so an offer in its support would
                # give a share of its decision to something it can only hold: no offers at all; the desktop draws them.
                return LO.Offer(None, {"version": LO.OFFER_VERSION, "status": "none:device_serves_no_lesson"})
        local = env.now().astimezone()
        minutes_left = float(record.minutes_left()) if record is not None and record.is_open else None
        return LO.build(vault, repository, today=today, now_iso=now_iso, local_hour=local.hour + local.minute / 60.0,
                        minutes_left=minutes_left, reentry=bool(env.gap().due), forced=forced)

    return build


__all__ = ["bridge_active", "mixture_active", "objective_active", "policy_for", "prefetch_can_start", "router_active"]
