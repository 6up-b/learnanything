"""The probe router's continuation: one router decision per next observation of a router-owned episode.

An episode is router-owned when a probe the router selected at its tag was administered in it (``probe_authority``:
the automatic lane's asked probe, the learner lane's accepted offer, or an earlier continuation). Its blocks are one
question each, and its completion reads only evidence and its count, so no worth gate decides whether it goes on. This
module does: after an answer, when the completion policy leaves the episode in progress with no presentation standing,
the router decides between asking the episode's next instrument (``probe``) and stopping (``stop``).

**The decision** is the learner lane's (``learner_probe.draw``): the next instrument, the episode's top eligible one
(eligibility from ``eligible_instruments``; its EIG ranks it and nothing else, so a flat instrument can be asked), is
priced by ``diagnostic_value.evaluate_probe`` on the episode's posterior, the instrument's channel, the factor's repair
classes and the probe's known exposure. Learned, the mix draws; unlearned, the probe coin does. The row
(``plan_log.log_probe_continuation_decision``) logs the served distribution exactly, with its assignment row, the
objective both arms are measured on (the episode's learning object), and a replay payload. In the same transaction a
``probe`` commits the next presentation pinned with the decision (``causal_probe.router_decision_id``), which every
door then consumes as it stands: the scheduler admits and places it whatever its EIG, item-open serves it, its answer
closes its one-question block; a ``stop`` completes the episode (``router_stop``).

**The job.** Decisions are made in the sidecar worker's ``probe_router`` slot (:func:`run_pending`), never on a request
loop. The queue is derived from rows (:func:`requested`): an episode is waiting while it is router-owned, in progress,
with no presentation standing and no decision at its boundary (its observation count, and the number of earlier
decisions there whose pin ended unanswered). A process that ends before deciding finds it again at the next start.
Below the probe router's tag no episode is router-owned, so nothing here runs.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import logging
from types import SimpleNamespace
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.ids import new_ulid

LOG = logging.getLogger(__name__)

#: The record's policy name for continuation decisions.
POLICY = "probe_router_continuation_v1"
#: The seed unit of a continuation's draw (the boundary key names the episode and its count).
UNIT = "probe_continuation"


@dataclass(frozen=True)
class ContinuationProposal:
    """What the valuation reads about one episode's next observation (``learner_probe.value``'s proposal shape)."""

    episode_id: str
    factor_id: str
    learning_object_id: str
    attempt_id: str | None
    repair_class_by_hypothesis: Mapping[str, str]
    repair_minutes: float
    #: The episode's posterior: the payload's hypothesis masses (``learner_probe.diagnostic_payload``).
    prior: Mapping[str, float]
    reads: Any
    chosen: Mapping[str, Any] = field(default_factory=dict)
    misconception_id: str | None = None
    session_id: str | None = None

    @property
    def practice_item_id(self) -> str | None:
        value = self.chosen.get("practice_item_id")
        return str(value) if value else None

    def facts(self) -> dict[str, Any]:
        return {"probe_episode_id": self.episode_id, "next_item": self.practice_item_id,
                "probe_burden_minutes": self.reads.probe_burden_minutes,
                "probe_burden_provenance": self.reads.probe_burden_provenance}


def _observations(repository: Any, episode_id: str) -> int:
    return len(repository.probe_observations_for_episode(episode_id))


def _pins_of(repository: Any, episode_id: str) -> dict[str, Any]:
    """The episode's presentations by the router decision their pin names."""

    out: dict[str, Any] = {}
    for presentation in repository.probe_presentations_for_episode(episode_id):
        pin = (presentation.selection_components or {}).get("causal_probe")
        if isinstance(pin, Mapping) and pin.get("router_decision_id"):
            out[str(pin["router_decision_id"])] = presentation
    return out


def boundary(repository: Any, episode: Any) -> tuple[int, int] | None:
    """The episode's decision boundary ``(observations, redraw)`` when a decision is due there, else None: none
    yet at this count, or the last one asked a probe whose pin ended unanswered (expired, refused, invalidated)."""

    from learnloop.router.plan_log import PROBE_REF, probe_continuation_decisions

    count = _observations(repository, str(episode.id))
    with repository.connection() as connection:
        decided = probe_continuation_decisions(connection, str(episode.id), count)
    if not decided:
        return count, 0
    last = decided[-1]
    if str(last["chosen_ref"]) != PROBE_REF:
        return None
    pinned = _pins_of(repository, str(episode.id)).get(str(last["id"]))
    if pinned is not None and pinned.status == "ended":
        return count, len(decided)
    return None


def requested(vault: Any, repository: Any) -> list[dict[str, Any]]:
    """The router-owned episodes waiting on a continuation decision, oldest first."""

    from learnloop.algorithm_versions import probe_router_on
    from learnloop.diagnosis.probe_episodes import router_selected_episode

    if not probe_router_on(vault.config):
        return []
    waiting = []
    for episode in repository.list_probe_episodes(statuses=("in_progress",)):
        if episode.hypothesis_set_id is None or repository.active_probe_presentation(episode.id) is not None:
            continue
        if _observations(repository, str(episode.id)) < 1 or not router_selected_episode(vault, repository, episode):
            continue
        at = boundary(repository, episode)
        if at is not None:
            waiting.append({"episode_id": str(episode.id), "observations": at[0], "redraw": at[1],
                            "at": str(episode.updated_at or "")})
    return sorted(waiting, key=lambda value: (value["at"], value["episode_id"]))


def proposal(vault: Any, repository: Any, episode: Any) -> tuple[ContinuationProposal | None, Any, str | None]:
    """``(proposal, the next eligible instrument, why none)`` for the episode's next observation: its top eligible
    instrument, on its posterior. None with a reason when no instrument is left (the completion policy parks such an
    episode) or the episode cannot be read."""

    from learnloop.diagnosis.causal_orchestrator import repair_classes_for_factor, resolve_orchestrator_parameters
    from learnloop.diagnosis.causal_reads import probe_burden_minutes
    from learnloop.diagnosis.probe_episodes import eligible_instruments, episode_posterior
    from learnloop.diagnosis.probe_hard_stops import causal_origin_factor

    posterior = episode_posterior(vault, repository, episode)
    if posterior is None:
        return None, None, "no_posterior"
    candidates = eligible_instruments(vault, repository, episode, posterior=posterior.posterior)
    if not candidates:
        return None, None, "no_instrument_left"
    instrument = candidates[0]
    factor_id = causal_origin_factor(str(episode.origin or "")) or ""
    factor = repository.unresolved_cause_factor(factor_id) if factor_id else None
    parameters = resolve_orchestrator_parameters(repository)
    burden, burden_source = probe_burden_minutes(repository, instrument.item.id,
                                                  parameters["probe_burden_minutes_default"])
    reads = SimpleNamespace(probe_burden_minutes=float(burden), probe_burden_provenance=burden_source,
                            prior_basis="episode_posterior")
    return ContinuationProposal(
        episode_id=str(episode.id), factor_id=factor_id, learning_object_id=str(episode.learning_object_id),
        attempt_id=str((factor or {}).get("attempt_id") or "") or None,
        repair_class_by_hypothesis=repair_classes_for_factor(repository, factor_id) if factor_id else {},
        repair_minutes=float(parameters["repair_class_expected_minutes_default"]),
        prior=dict(posterior.posterior), reads=reads,
        chosen={"id": f"instrument:{instrument.item.id}", "practice_item_id": instrument.item.id,
                "hypothesis_set_id": episode.hypothesis_set_id},
    ), instrument, None


def decide(vault: Any, repository: Any, request: Mapping[str, Any], *, clock: Clock | None = None) -> str | None:
    """Decide one waiting episode's next observation and record it with what it serves (the pinned next presentation,
    or the episode's stop), all in one transaction. Returns the decision's id, or None when nothing was recorded (no
    instrument left, a boundary no longer waiting, or a write that failed: the episode stays waiting)."""

    from learnloop.daily_plan import learner_probe as LP
    from learnloop.daily_plan import measurement as objectives
    from learnloop.diagnosis.probe_blocks import stop_on_router_decision
    from learnloop.diagnosis.probe_presentations import commit_presentation
    from learnloop.router.plan_log import PROBE_REF, CONTINUATION_STOP_REF, log_probe_continuation_decision, \
        probe_continuation_receipt_key

    episode = repository.probe_episode(str(request["episode_id"]))
    if episode is None or episode.status != "in_progress" or repository.active_probe_presentation(episode.id):
        return None
    at = boundary(repository, episode)
    if at is None:
        return None
    built, instrument, why_not = proposal(vault, repository, episode)
    if built is None:
        LOG.info("probe router: no continuation for episode %s (%s)", episode.id, why_not)
        return None
    config = vault.config
    now_iso = utc_now_iso(clock)
    receipt_key = probe_continuation_receipt_key(str(episode.id), at[0], at[1])
    key = receipt_key.split(":", 1)[1]
    identity = {"kind": UNIT, "episode": str(episode.id), "observations": at[0], "redraw": at[1],
                "item": built.practice_item_id, "version": config.algorithms.algorithm_version}
    try:
        valuation, value_record = LP.value(vault, repository, built, now_iso=now_iso, seed_identity=identity)
    except Exception as exc:  # a probe the router could not value is unlearned
        LOG.warning("probe router: the continuation's valuation failed for episode %s", episode.id, exc_info=True)
        valuation, value_record = None, {"status": "failed", "error": type(exc).__name__}
    gained = LP.information(valuation)
    served, propensity, served_pi, drawn, pending = LP.draw(
        vault, repository, key=key, unit=UNIT, valuation=valuation, now_iso=now_iso, probe_ref=PROBE_REF,
        other_ref=CONTINUATION_STOP_REF)
    decision_id = new_ulid()
    detail: dict[str, Any] = {
        "probe_episode_id": str(episode.id), "factor_id": built.factor_id, "observations": at[0], "redraw": at[1],
        "candidate_id": built.chosen["id"], "next_item": built.practice_item_id,
        "learning_object_id": built.learning_object_id, "policy": POLICY, "learned": gained > 0.0,
        "information": gained, "valuation": value_record, "facts": built.facts(), "support": [CONTINUATION_STOP_REF, PROBE_REF],
        "eligibility": {"next_item_eig": float(instrument.expected_information_gain), "ranked_by": "eig",
                        "eligible_by": "eligible_instruments"},
        **drawn, "served_pi": served_pi,
    }
    if valuation is not None:
        detail["evaluation"] = {name: valuation.record.get(name) for name in
                                ("version", "decisions", "given", "values", "choice", "results", "prior_choice",
                                 "policy_changes_with_result", "channel_use", "excluded", "cost")}
        detail["evaluation"]["numeric_choice"] = valuation.choice
    try:
        with repository.atomic(), repository.connection() as connection:
            # One owner of the episode's state: the decision commits only against the episode as it stands inside this
            # transaction, under its lock. A stale process is refused here, whichever arm it drew (the fence's rule;
            # the stop writes no fenced table of its own), and a learner's completed action ("Stop diagnosing and
            # teach me"), another door's presentation or a new answer since the valuation wins: nothing is recorded,
            # and the next run decides at the boundary as it then is.
            from learnloop.db.writer_fence import require_current

            require_current(connection)
            standing = _still_waiting(repository, episode, at)
            if standing is None:
                return None
            episode = standing
            recorded = log_probe_continuation_decision(connection, {
                "decision_id": decision_id, "factor_id": built.factor_id or str(episode.id),
                "probe_episode_id": str(episode.id), "receipt_key": receipt_key, "chosen_ref": served,
                "propensity": propensity, "served_pi": served_pi, "learning_object_id": built.learning_object_id,
                "session_id": None, "policy": POLICY, "mode": "probe_router", "detail": detail,
                "decided_at": now_iso, "config": config,
            })
            if recorded != decision_id:
                return recorded  # a concurrent run decided this boundary first
            if pending:
                from learnloop.router_objective import assignments as ro5_assignments

                written = ro5_assignments.record_pending(connection, pending, unit_id=decision_id, at=now_iso)
                if len(written) != len(pending):
                    raise RuntimeError("the probe coin's assignment was not written")
            support = [ref for ref in (CONTINUATION_STOP_REF, PROBE_REF) if float(served_pi.get(ref, 0.0)) > 0.0]
            objectives.record(vault, repository, connection, decision_id=decision_id, decision_kind="plan_interrupt",
                              frozen=objectives.freeze_followup(built.learning_object_id, support=support),
                              arm=objectives.ARM_INSERT if served == PROBE_REF else objectives.ARM_STOP,
                              clock=clock, exclude=LP.instrument_items(vault, repository, built.learning_object_id,
                                                                       built.factor_id or None))
            if served == PROBE_REF:
                # The decision's own instrument, pinned: the doors serve this presentation and nothing else.
                commit_presentation(vault, repository, episode, instrument, extra_selection_components={
                    "causal_probe": {
                        "causal_factor_id": built.factor_id or None,
                        "hypothesis_set_id": str(episode.hypothesis_set_id),
                        "router_decision_id": decision_id,
                        "continuation_of_episode": str(episode.id),
                        "session_id": None,
                    }}, clock=clock)
            else:
                stop_on_router_decision(vault, repository, episode, router_decision_id=decision_id, clock=clock)
    except Exception:  # noqa: BLE001 - nothing unrecorded is served: the episode stays waiting
        LOG.warning("probe router: the continuation decision was not recorded for episode %s", episode.id,
                    exc_info=True)
        return None
    return decision_id


def _still_waiting(repository: Any, valued: Any, at: tuple[int, int]) -> Any:
    """The episode as it stands now when it is still the boundary that was valued (in progress, the same state segment,
    no presentation standing, the same observation count and redraw), else None."""

    fresh = repository.probe_episode(str(valued.id))
    if fresh is None or fresh.status != "in_progress":
        return None
    if fresh.active_state_segment_id != valued.active_state_segment_id:
        return None
    if repository.active_probe_presentation(fresh.id) is not None or boundary(repository, fresh) != at:
        return None
    return fresh


def run_pending(vault: Any, repository: Any, *, clock: Clock | None = None, max_jobs: int = 100) -> list[str]:
    """The continuation job: decide each waiting episode once. Returns the episodes it decided."""

    ran: list[str] = []
    for request in requested(vault, repository)[:max_jobs]:
        try:
            if decide(vault, repository, request, clock=clock) is not None:
                ran.append(request["episode_id"])
        except Exception:  # noqa: BLE001 - a job never dies on one episode
            LOG.warning("probe router: the continuation job failed for episode %s", request["episode_id"],
                        exc_info=True)
    return ran


__all__ = ["POLICY", "UNIT", "ContinuationProposal", "boundary", "decide", "proposal", "requested", "run_pending"]
