"""The follow-up generation worker (spec §5 item 1, §8).

Its own slot, apart from the strictly ordered diagnosis worker, so later diagnoses are
never delayed. One job per deduplicated key: a workflow, an entered episode, a recorded
need. That is the structural bound on physical generation on a subscription route, where
dollar reservations bound nothing; retries are admitted by the workflow, up to
:data:`MAX_GENERATION_ATTEMPTS`.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.daily_plan.router_runtime import FOLLOWUP_GENERATION_OWNER
from learnloop.db.repositories import Repository
from learnloop.db.stores import followup_serve as store
from learnloop.followup_serve import identity
from learnloop.followup_serve import workflow as wf
from learnloop.followup_serve import queue
from learnloop.followup_serve.gates import generate_and_serve_on

LOG = logging.getLogger(__name__)

#: The model-call receipts of one generation job: calls and cost per probe are read from these,
#: and the router's daily guard counts them, so several jobs can't pass its cap between them.
RECEIPT_OWNER = FOLLOWUP_GENERATION_OWNER

#: A job's lease: a generation is one structured model call with its checks.
LEASE_SECONDS = 900.0
#: One generation per workflow or need, and at most this many physical runs of it:
#: the first, and one retry after a transient failure. A structural bound (spec §8).
MAX_GENERATION_ATTEMPTS = 2
#: The pause before that retry: long enough for a transient provider failure to pass,
#: short against the learner's wait.
RETRY_BACKOFF_SECONDS = 20.0
#: A failed lane's need is tried again later, not now: what just failed would fail again.
NEED_RETRY_DELAY_SECONDS = 3_600.0


class GenerationDeferred(RuntimeError):
    """The route is not ready: nothing was spent, and the job may run again."""


@dataclass
class JobOutcome:
    job_id: str
    kind: str
    state: str
    error: str | None = None
    workflow_id: str | None = None


def _iso_after(clock: Clock | None, seconds: float) -> str:
    now = parse_utc(utc_now_iso(clock))
    return (now + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def process_next_job(
    vault: Any,
    repository: Repository,
    *,
    owner: str,
    clients: Any = None,
    cancelled: Callable[[], bool] | None = None,
    clock: Clock | None = None,
) -> JobOutcome | None:
    """Lease and run the next runnable job; None when none is."""

    if cancelled is not None and cancelled():
        return None
    now = utc_now_iso(clock)
    with repository.atomic(), repository.connection() as connection:
        job = store.lease_next_generation_job(
            connection, owner=owner, now=now, lease_expires_at=_iso_after(clock, LEASE_SECONDS),
        )
    if job is None:
        return None
    outcome = JobOutcome(job_id=str(job["id"]), kind=str(job["kind"]), state="done",
                         workflow_id=job.get("workflow_id"))
    try:
        if not generate_and_serve_on(vault.config):
            _finish(repository, job, "skipped", "switch_off", clock)
            outcome.state, outcome.error = "skipped", "switch_off"
            return outcome
        _run(vault, repository, job, clients=clients, clock=clock)
        _finish(repository, job, "done", None, clock)
        return outcome
    except GenerationDeferred as deferred:
        return _retry_or_fail(vault, repository, job, outcome, str(deferred), clock)
    except Exception as exc:  # noqa: BLE001 - a job's failure is a typed outcome, never the worker's
        LOG.warning("follow-up generation job %s failed", job["id"], exc_info=True)
        return _retry_or_fail(vault, repository, job, outcome, type(exc).__name__, clock)


def _finish(repository: Repository, job: Mapping[str, Any], state: str, error: str | None, clock: Clock | None,
            *, not_before: str | None = None) -> bool:
    with repository.atomic(), repository.connection() as connection:
        return store.finish_generation_job(
            connection, job, state=state, at=utc_now_iso(clock), error=error, not_before=not_before,
        )


def _retry_or_fail(vault: Any, repository: Repository, job: Mapping[str, Any], outcome: JobOutcome, error: str,
                   clock: Clock | None) -> JobOutcome:
    outcome.error = error
    if int(job.get("attempt_count") or 0) < MAX_GENERATION_ATTEMPTS:
        _finish(repository, job, "queued", error, clock, not_before=_iso_after(clock, RETRY_BACKOFF_SECONDS))
        outcome.state = "retry"
        return outcome
    _finish(repository, job, "failed", error, clock)
    outcome.state = "failed"
    if job.get("workflow_id"):
        fail_workflow(vault, repository, str(job["workflow_id"]), reason=error, clock=clock)
    return outcome


def fail_workflow(vault: Any, repository: Repository, workflow_id: str, *, reason: str, clock: Clock | None) -> None:
    """§6.2: nothing passed. Next continues the plan, feedback is released, and the need
    stays open for background generation, deduplicated, cancelled if the hypotheses close."""

    row = wf.get(repository, workflow_id)
    if row is None:
        return
    with repository.atomic():
        # What its last run left closes with it, or it would block the need's own question
        # (``duplicate_instrument_class``).
        if not wf.finish(repository, workflow_id, to_state=wf.FAILED, reason=reason,
                         release=wf.RELEASE_GENERATION_FAILED, clock=clock):
            return
        if row.get("factor_id"):
            queue.enqueue_factor(repository, str(row["factor_id"]), workflow_id=workflow_id,
                                 not_before=_iso_after(clock, NEED_RETRY_DELAY_SECONDS), clock=clock)


def recover_workflow(vault: Any, repository: Repository, row: Mapping[str, Any], *, clock: Clock | None = None) -> bool:
    """§6.2's "Next never strands": a pending workflow whose diagnosis ended and whose job a
    crash lost gets that job; one whose job ended with the workflow still pending fails, with
    its failure line. Idempotent, and nothing happens while the diagnosis is still out."""

    from learnloop.diagnosis.split.jobs import PENDING, diagnosis_status

    if row["state"] != wf.PENDING:
        return False
    attempt_id = str(row["source_attempt_id"])
    if (repository.latest_blind_grade_record(attempt_id) is not None
            and diagnosis_status(repository, attempt_id)["status"] == PENDING):
        return False
    workflow_id = str(row["id"])
    with repository.connection() as connection:
        job = store.generation_job(connection, f"workflow:{workflow_id}")
    if job is None:
        return queue.enqueue_workflow(repository, workflow_id, clock=clock) is not None
    if job["state"] in {"done", "failed", "skipped"}:
        fail_workflow(vault, repository, workflow_id, reason="generation_job_ended", clock=clock)
        return True
    return False


def recover_pending_workflows(vault: Any, repository: Repository, *, clock: Clock | None = None) -> int:
    """At startup: what a previous process committed and never handed off."""

    if not generate_and_serve_on(vault.config):
        return 0
    with repository.connection() as connection:
        rows = store.open_workflows(connection, states=(wf.PENDING,)) if store.present(connection) else []
    return sum(1 for row in rows if recover_workflow(vault, repository, row, clock=clock))


def _run(vault: Any, repository: Repository, job: Mapping[str, Any], *, clients: Any, clock: Clock | None) -> None:
    from learnloop.daily_plan.router_runtime import default_runtime

    kind = str(job["kind"])
    # Every physical call of this job, retries and optional review included, is admitted
    # and recorded through the existing envelope: subscription requests are recorded and
    # never refused, a metered one needs the budget (spec §8).
    runtime = getattr(clients, "runtime", None) or default_runtime()
    with runtime.spend.metered(repository, vault.config, owner_kind=RECEIPT_OWNER, owner_id=str(job["id"])):
        if kind == "workflow":
            _run_workflow(vault, repository, str(job["workflow_id"]), clients=clients, clock=clock)
        elif kind == "entry_episode":
            _run_entry(vault, repository, str(job["probe_episode_id"]), clients=clients, clock=clock)
        elif job.get("need_id"):
            _run_need(vault, repository, str(job["need_id"]), clients=clients, clock=clock)
        else:
            _run_factor_need(vault, repository, str(job["dedupe_key"]).split(":", 1)[1], clients=clients, clock=clock)


def _run_entry(vault: Any, repository: Repository, episode_id: str, *, clients: Any, clock: Clock | None) -> None:
    """§4.3: the worker chooses the contract. With concrete rival causes it is §4.1;
    otherwise the family's question pattern, written by the model. Single use either way."""

    from learnloop.diagnosis.probe_instance_generation import mint_single_use_probe_surface
    from learnloop.followup_run.lanes import concrete_rivals

    episode = repository.probe_episode(episode_id)
    if episode is None or episode.status != "pending_items":
        return
    factor_id = _causal_factor_of(episode)
    factor = repository.unresolved_cause_factor(factor_id) if factor_id else None
    if factor is not None and factor.get("status") == "open" and len(concrete_rivals(repository, factor)) >= 2:
        _author_for_factor(vault, repository, factor_id=str(factor_id), learning_object_id=episode.learning_object_id,
                           attempt_id=str(factor.get("attempt_id") or ""), episode_id=episode_id, clients=clients,
                           clock=clock)
        return
    client = _author_client(vault, clients)
    if client is None:
        raise GenerationDeferred("author_route_not_ready")
    if mint_single_use_probe_surface(repository, vault, episode_id, ai_client=client, clock=clock) is None:
        raise GenerationDeferred("no_surface_passed")


def _causal_factor_of(episode: Any) -> str | None:
    from learnloop.diagnosis.causal_orchestrator import causal_origin_factor

    return causal_origin_factor(str(episode.origin or ""))


def _author_for_factor(vault: Any, repository: Repository, *, factor_id: str, learning_object_id: str, attempt_id: str,
                       episode_id: str | None, clients: Any, clock: Clock | None) -> str | None:
    """§4.1's contract with no workflow: an active candidate on the factor, unreserved."""

    from learnloop.followup_run import admission

    client = _author_client(vault, clients)
    if client is None:
        raise GenerationDeferred("author_route_not_ready")
    row = {"id": None, "learning_object_id": learning_object_id, "source_attempt_id": attempt_id}
    probe, template, card = admission.author_probe(
        vault, repository, workflow=row, factor_id=factor_id, decision={"chosen": "background", "timing": "later"},
        client=client,
    )
    item_id = admission.persist_item(vault, repository, probe, template=template, card=card, workflow_id=None,
                                     episode_id=episode_id, source="entry", client=client, clock=clock)
    admission.commission_only(reloaded(vault), repository, probe, factor_id=factor_id, practice_item_id=item_id,
                              client=client, clock=clock)
    return item_id


def _run_factor_need(vault: Any, repository: Repository, factor_id: str, *, clients: Any, clock: Clock | None) -> None:
    """§6.2: a failed probe lane's need, deduplicated by factor and cancelled if it closed."""

    factor = repository.unresolved_cause_factor(factor_id)
    if factor is None or factor.get("status") != "open":
        return
    attempt = repository.fetch_practice_attempt(str(factor.get("attempt_id") or "")) or {}
    _author_for_factor(vault, repository, factor_id=factor_id,
                       learning_object_id=str(attempt.get("learning_object_id") or ""),
                       attempt_id=str(factor.get("attempt_id") or ""), episode_id=None, clients=clients, clock=clock)


def _run_need(vault: Any, repository: Repository, need_id: str, *, clients: Any, clock: Clock | None) -> None:
    """§4: a recorded need fills in the background, S2b's order kept: an existing item was
    the chooser's, then a textbook exercise, then a generated practice item."""

    from learnloop.ai.routing import ready_client_for_task
    from learnloop.content.authoring.practice_generation import generate_diagnostic_practice_proposal
    from learnloop.content.proposals.proposals import accept_items
    from learnloop.instructional.needs import fulfil_need_from_sources, pending_causal_decision

    need = next((row for row in repository.pending_intervention_needs(None) if str(row["id"]) == need_id), None)
    if need is None:
        return
    outcome = fulfil_need_from_sources(
        vault, repository, need, path="background",
        pending_decision=pending_causal_decision(vault, repository, need), clock=clock,
    )
    if outcome.get("outcome") != "generate":
        return
    injected = getattr(clients, "authoring", None)
    if injected is not None:
        client = injected
    else:
        resolved = ready_client_for_task(vault.root, vault.config, "authoring")
        client = resolved.client if resolved.ready else None
    if client is None:
        raise GenerationDeferred("authoring_route_not_ready")
    result = generate_diagnostic_practice_proposal(
        vault.root, client, learning_object_id=str(need["learning_object_id"]), max_needs=1,
    )
    # Practice items, not probes: filled without a click or a CLI command (§4).
    accept_items(vault.root, result.patch_id)


def _run_workflow(vault: Any, repository: Repository, workflow_id: str, *, clients: Any, clock: Clock | None) -> None:
    from learnloop.diagnosis.split.jobs import DONE, diagnosis_status
    from learnloop.followup_run.lanes import open_rival_factor, select_lane, settle_practice_lane
    row = wf.get(repository, workflow_id)
    if row is None or row["state"] != wf.PENDING:
        return
    if wf.superseded(repository, row):
        wf.finish(repository, workflow_id, to_state=wf.SKIPPED, reason="newer_grade", release=wf.RELEASE_FALLBACK,
                  clock=clock)
        return
    attempt_id = str(row["source_attempt_id"])
    blind = repository.latest_blind_grade_record(attempt_id) is not None
    if blind and diagnosis_status(repository, attempt_id)["status"] != DONE:
        # §6.2: failed, skipped or released for readiness: one fallback, from the grade alone.
        settle_practice_lane(vault, repository, row, reason="diagnosis_unavailable", release=wf.RELEASE_FALLBACK,
                                clock=clock)
        return
    open_rival_factor(vault, repository, row, clock=clock)
    choice = select_lane(repository, row)
    if choice.lane != wf.LANE_PROBE:
        settle_practice_lane(vault, repository, row, reason=choice.reason, clock=clock)
        return
    # §4.1, §8: a cause reproducing a reserved question sends its words to neither the router
    # nor the author, so this miss takes the practice lane. Before anything is spent.
    from learnloop.followup_run import authoring

    try:
        matched = authoring.causes_match_reserved(vault, repository, choice.hypothesis_ids)
    except authoring.AuthoringRejected as rejected:
        fail_workflow(vault, repository, workflow_id, reason=str(rejected), clock=clock)
        return
    if matched:
        settle_practice_lane(vault, repository, row, reason=authoring.CAUSE_MATCHES_RESERVED, clock=clock)
        return
    wf.set_fields(repository, workflow_id, lane=wf.LANE_PROBE, factor_id=choice.factor_id, clock=clock)
    row = wf.get(repository, workflow_id) or row
    _run_probe_lane(vault, repository, row, choice=choice, clients=clients, clock=clock)


def _author_client(vault: Any, clients: Any) -> Any:
    """The test seam's client, else the route's; never the Decider."""

    from learnloop.followup_run.authoring import resolve_author_client

    injected = getattr(clients, "author", None)
    return injected if injected is not None else resolve_author_client(vault)


def _run_probe_lane(vault: Any, repository: Repository, row: Mapping[str, Any], *, choice: Any, clients: Any,
                    clock: Clock | None) -> None:
    """§5: the decision first and the item after it. One physical authoring call, on a plan route."""

    from learnloop.followup_run import admission, router

    workflow_id = str(row["id"])
    factor_id = str(choice.factor_id)
    # §4.2: what an interrupted run published and never bound is never served, whatever this run decides.
    identity.retire_unbound(repository, workflow_id, clock=clock)
    # Retry and lease recovery run under the decision already drawn, never a fresh draw.
    decision = router.decide_once(vault, repository, row, choice=choice, clients=clients, clock=clock)
    if decision.refused:
        with repository.atomic():
            wf.finish(repository, workflow_id, to_state=wf.REFUSED, reason=decision.reason, release=wf.RELEASE_REFUSED,
                      clock=clock)
            router.record_outcome(repository, row, decision, outcome="refused", clock=clock)
        return
    if decision.no_intervention:
        # §5 item 4: nothing is generated, the screen shows the decision, and what was held is released.
        with repository.atomic():
            wf.finish(repository, workflow_id, to_state=wf.SETTLED, reason="no_intervention",
                      release=wf.RELEASE_NO_INTERVENTION, lane=wf.LANE_PROBE, clock=clock)
            router.record_outcome(repository, row, decision, outcome="no_intervention", clock=clock)
        return
    if decision.wait:
        # §6.0: released now, and the later probe is labelled exposed, so it can't resolve the cause.
        wf.release_feedback(repository, workflow_id, reason=wf.RELEASE_WAIT, exposed=True, clock=clock)
    client = _author_client(vault, clients)
    if client is None:
        raise GenerationDeferred("author_route_not_ready")
    item_id: str | None = None
    fresh = vault
    try:
        probe, template, card = admission.author_probe(
            vault, repository, workflow=row, factor_id=factor_id, decision=decision.for_author(), client=client,
        )
        # The learner may have said "Not now" while the model wrote; nothing further was paid for.
        refusal = router.hard_refusal(vault, repository, row, factor_id=factor_id)
        if refusal is not None:
            raise admission.OfferRefused(refusal)
        item_id = admission.persist_item(vault, repository, probe, template=template, card=card, workflow_id=workflow_id,
                                         client=client, clock=clock)
        fresh = reloaded(vault)
        admitted = admission.commission_and_pin(
            fresh, repository, probe, workflow=row, factor_id=factor_id, decision_id=decision.decision_id,
            practice_item_id=item_id, client=client, clock=clock,
        )
    except admission.OfferRefused as refused:
        with repository.atomic():
            _withdraw(repository, item_id, reason=refused.reason, workflow_id=workflow_id, clock=clock)
            wf.finish(repository, workflow_id, to_state=wf.REFUSED, reason=refused.reason, release=wf.RELEASE_REFUSED,
                      clock=clock)
            router.record_outcome(repository, row, decision, outcome="refused", clock=clock)
        return
    except admission.AdmissionFailed as failed:
        from learnloop.followup_run.authoring import RESERVED_MATCHES
        from learnloop.followup_run.lanes import settle_practice_lane

        if failed.reason in RESERVED_MATCHES:
            # §8, the owner's ruling: the miss takes the practice lane, and nothing was served.
            with repository.atomic():
                _withdraw(repository, item_id, reason=failed.reason, workflow_id=workflow_id, clock=clock)
                settle_practice_lane(vault, repository, row, reason=failed.reason, clock=clock)
                router.record_outcome(repository, row, decision, outcome="refused", clock=clock)
            return
        with repository.atomic():
            _withdraw(repository, item_id, reason=failed.reason, workflow_id=workflow_id, clock=clock)
            fail_workflow(vault, repository, workflow_id, reason=failed.reason, clock=clock)
            router.record_outcome(repository, row, decision, outcome="generation_failed", clock=clock)
        return
    with repository.atomic():
        moved = wf.move(
            repository, workflow_id, to_state=wf.WAITING if decision.wait else wf.READY, reason=decision.chosen_ref,
            from_states=(wf.PENDING,),
            practice_item_id=admitted.practice_item_id, probe_candidate_id=admitted.candidate_id,
            hypothesis_set_id=admitted.hypothesis_set_id, probe_episode_id=admitted.episode_id,
            presentation_id=admitted.presentation_id, clock=clock,
        )
        if moved:
            router.bind_item(repository, row, decision, admitted, clock=clock)
        else:
            # A late generator: the skip or fallback already settled it, and this adds nothing.
            wf.close_probe(repository, {**row, "practice_item_id": admitted.practice_item_id,
                                        "presentation_id": admitted.presentation_id,
                                        "probe_episode_id": admitted.episode_id},
                           reason="workflow_settled", clock=clock)


def reloaded(vault: Any) -> Any:
    """The vault with the item just written; its config stays the run's."""

    from learnloop.vault.loader import load_vault

    fresh = load_vault(vault.root)
    fresh.config = vault.config
    return fresh


def _withdraw(repository: Repository, item_id: str | None, *, reason: str, workflow_id: str, clock: Clock | None) -> None:
    if item_id is not None:
        identity.withdraw(repository, item_id, reason=reason, workflow_id=workflow_id, clock=clock)


__all__ = [
    "GenerationDeferred", "JobOutcome", "LEASE_SECONDS", "MAX_GENERATION_ATTEMPTS", "NEED_RETRY_DELAY_SECONDS",
    "RETRY_BACKOFF_SECONDS",
    "fail_workflow", "process_next_job", "recover_pending_workflows", "recover_workflow", "reloaded",
]
