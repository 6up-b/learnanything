"""The asynchronous post-attempt jobs of the live split (Slice 1 §5.1, §7, §11).

``diagnose`` jobs run strictly in attempt-completion order (materialization,
factors and registry promotion depend on earlier diagnoses); ``embed`` jobs are
unordered and best effort. Every job is lease-fenced (``post_attempt_jobs``):
a crash mid-job leaves it reclaimable when the lease expires, and a worker
whose lease was re-claimed writes nothing. The diagnosis row and its context
receipt are written in one transaction that first checks the lease, so each
diagnosis job appends at most one diagnosis (C5).

The worker (sidecar thread, ``learnloop diagnose drain``, the CLI/TUI inline
path) calls :func:`process_next_job`; everything else here is shared with them.
Replay never calls this module (S7).
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Callable, Iterator, Mapping

from learnloop.ai.errors import AIInterrupted, AIProviderUnavailable
from learnloop.ai.execution import record_model_calls
from learnloop.ai.runs import finish_agent_run
from learnloop.ai.spend import SpendCaps, SpendEstimate, SpendLimitExceeded
from learnloop.attempts.blind_grading import split_grading_active
from learnloop.attempts.grading import resolved_rubric
from learnloop.clock import Clock, SystemClock, parse_utc, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.diagnosis.split.diagnoser import DiagnosisOutcome, run_diagnosis
from learnloop.diagnosis.split.live import (
    build_causal_view,
    current_attempt_for,
    joint_grade_record,
    live_history_store,
    needs_diagnosis,
    sampled_correct_answer,
    settings_from_config,
)
from learnloop.diagnosis.offline_review.spend import ReviewSpend
from learnloop.diagnosis.split.settings import DIAGNOSIS_PROMPT_VERSION
from learnloop.ids import new_ulid
from learnloop.substrate.canonical_projection import project_canonical_facet_state
from learnloop.substrate.recurrence_groups import claim_for_citation, recurrence_active
from learnloop.vault.models import LoadedVault

LOG = logging.getLogger(__name__)

DIAGNOSE_KIND = "diagnose"
EMBED_KIND = "embed"
#: A diagnosis runs one model turn; a lease outlives the request timeout.
DIAGNOSE_LEASE_SECONDS = 1_200
EMBED_LEASE_SECONDS = 300
BACKOFF_BASE_SECONDS = 30
BACKOFF_MAX_SECONDS = 3_600
#: Provider not ready / kill switch off: look again later, no attempt spent.
NOT_READY_RECHECK_SECONDS = 60
SPLIT_OFF_RECHECK_SECONDS = 3_600
MODEL_CALL_OWNER_KIND = "attempt_diagnosis"
#: ``diagnosis_status`` values (§11 UI).
PENDING, NOT_NEEDED, DONE, FAILED = "pending", "not_needed", "done", "failed"
#: The spend route every diagnosis request is admitted on.
DIAGNOSIS_ROUTE = "diagnosis"
#: Per-job caps of a live diagnosis (sidecar worker, CLI/TUI inline path), in
#: the shared spend framework (``ReviewSpend`` over ``SpendBudget``). A
#: subscription route (Codex on the owner's ChatGPT plan, Slice A §5 rule 6)
#: counts its one logical call and has no physical-request, token or dollar
#: bound; its cost is estimated from reported usage. A metered route admits
#: every physical request (transport retries, JSON repairs) against these
#: caps before it is sent, and an unknown price fails closed (the job is
#: skipped as ``budget``; ``learnloop diagnose retry --price-per-million``
#: supplies one). ``diagnosis.max_calls_per_day`` caps logical calls across
#: jobs, counted at admission.
LIVE_DIAGNOSIS_CAPS = SpendCaps(
    max_candidates=1,
    max_pairs=0,
    max_retries=4,
    max_calls=5,
    max_total_tokens=750_000,
    max_estimated_usd=2.0,
)

ClientFactory = Callable[[], Any]
Cancelled = Callable[[], bool]


@dataclass
class JobOutcome:
    job_id: str
    attempt_id: str
    kind: str
    state: str  # done | failed | skipped | released | lease_lost
    diagnosis_id: str | None = None
    status: str | None = None
    error: str | None = None
    notes: list[str] = field(default_factory=list)


class _LeaseLost(RuntimeError):
    """The job was re-claimed by another worker; publish nothing."""


# -- enqueue ---------------------------------------------------------------------

def enqueue_diagnosis(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    rediagnose: bool = False,
    clock: Clock | None = None,
) -> str | None:
    """Queue the attempt's diagnosis when §5.1 says it runs; returns the job id.

    Live: a blind grade with a non-pass criterion, a fatal error or an
    attribution. Correct blind answers are sampled at
    ``correct_answer_sample_rate`` as SHADOW diagnoses (never routed).
    Shadow on a joint vault (``diagnosis.shadow``): the same trigger over the
    stored joint grade. Self-graded and deterministic attempts have neither a
    blind record nor a model grade and are never diagnosed.
    ``rediagnose`` (a regrade, or ``learnloop diagnose retry``) keys the job on
    the current blind record so it runs again and supersedes.
    """

    attempt = repository.fetch_practice_attempt(attempt_id)
    if attempt is None:
        return None
    config = getattr(vault.config, "diagnosis", None)
    row = repository.latest_blind_grade_record(attempt_id)
    if row is not None:
        record = dict(row.get("record") or {})
        mode = "live"
        if not needs_diagnosis(record):
            rate = float(getattr(config, "correct_answer_sample_rate", 0.0) or 0.0)
            if not sampled_correct_answer(attempt_id, rate):
                return None
            mode = "shadow"
        record_id = str(row["id"])
    else:
        if not bool(getattr(config, "shadow", False)):
            return None
        metadata = repository.raw_attempt_feedback_metadata(attempt_id) or {}
        if str(metadata.get("grading_source") or "") not in {"ai", "codex"}:
            return None
        if not needs_diagnosis(joint_grade_record(vault, repository, attempt)):
            return None
        mode, record_id = "shadow", None
    job_key = attempt_id if not rediagnose else f"{attempt_id}:{record_id or 'joint'}:{new_ulid()}"
    return repository.enqueue_post_attempt_job(
        attempt_id=attempt_id,
        kind=DIAGNOSE_KIND,
        job_key=job_key,
        attempt_completed_at=str(attempt.get("created_at") or utc_now_iso(clock)),
        payload={"mode": mode, "blind_grade_record_id": record_id, "rediagnose": rediagnose},
        clock=clock,
    )


def enqueue_embed_job(
    repository: Repository,
    *,
    attempt_id: str,
    diagnosis_id: str | None,
    include_divergence: bool,
    clock: Clock | None = None,
) -> str | None:
    attempt = repository.fetch_practice_attempt(attempt_id) or {}
    return repository.enqueue_post_attempt_job(
        attempt_id=attempt_id,
        kind=EMBED_KIND,
        job_key=f"{attempt_id}:{diagnosis_id or 'grade'}",
        attempt_completed_at=str(attempt.get("created_at") or utc_now_iso(clock)),
        payload={"diagnosis_id": diagnosis_id, "include_divergence": include_divergence},
        clock=clock,
    )


# -- status --------------------------------------------------------------------------

def diagnosis_status(repository: Repository, attempt_id: str) -> dict[str, Any]:
    """§11 UI status: pending | not_needed | done | failed (live diagnoses only)."""

    jobs = [
        job
        for job in repository.post_attempt_jobs(attempt_id=attempt_id, kind=DIAGNOSE_KIND)
        if (job.get("payload") or {}).get("mode", "live") == "live"
    ]
    latest = repository.latest_attempt_diagnosis(attempt_id, mode="live")
    open_jobs = [job for job in jobs if job["state"] in ("queued", "leased")]
    if open_jobs:
        return {"status": PENDING, "diagnosis_id": None, "job_state": open_jobs[-1]["state"]}
    if latest is not None and latest["status"] == "skipped" and latest.get("error") == "not_needed":
        return {"status": NOT_NEEDED, "diagnosis_id": None, "job_state": jobs[-1]["state"] if jobs else None}
    in_force = repository.current_live_diagnosis(attempt_id)
    if in_force is not None:
        return {"status": DONE, "diagnosis_id": in_force["id"], "job_state": jobs[-1]["state"] if jobs else None}
    if jobs or latest is not None:
        error = (latest or {}).get("error") or (jobs[-1].get("last_error") if jobs else None)
        return {
            "status": FAILED,
            "diagnosis_id": (latest or {}).get("id"),
            "job_state": jobs[-1]["state"] if jobs else None,
            "error": error,
        }
    return {"status": NOT_NEEDED, "diagnosis_id": None, "job_state": None}


def session_diagnosis_availability(repository: Repository, session_id: str) -> tuple[list[str], list[str]]:
    """E7 at one serve: (attempts whose live diagnosis is required, those without it).

    Availability is the attempt's :func:`diagnosis_status`, which reads the
    diagnosis in force, never a job state alone (review F13): ``done`` is
    available; ``pending`` (queued or running) and ``failed`` (failed,
    budget-skipped, rejected, or written for a superseded grade) are not. A
    ``not_needed`` attempt (a regrade left nothing to explain) requires no
    diagnosis and is outside the population.
    """

    jobs = repository.live_diagnosis_jobs_for_session(session_id)
    required: list[str] = []
    unavailable: list[str] = []
    for attempt_id in dict.fromkeys(job["attempt_id"] for job in jobs):
        status = diagnosis_status(repository, attempt_id)["status"]
        if status == NOT_NEEDED:
            continue
        required.append(attempt_id)
        if status != DONE:
            unavailable.append(attempt_id)
    return required, unavailable


def pending_diagnosis_attempts(repository: Repository, attempt_ids: list[str]) -> list[str]:
    wanted = set(attempt_ids)
    return [
        job["attempt_id"]
        for job in repository.post_attempt_jobs(kind=DIAGNOSE_KIND, states=("queued", "leased"))
        if job["attempt_id"] in wanted
    ]


# -- processing --------------------------------------------------------------------------

def _backoff(attempt_count: int, clock: Clock | None) -> str:
    seconds = min(BACKOFF_MAX_SECONDS, BACKOFF_BASE_SECONDS * (2 ** max(0, attempt_count - 1)))
    return _later(seconds, clock)


def _later(seconds: float, clock: Clock | None) -> str:
    now = parse_utc(utc_now_iso(clock))
    return (now + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def _day_start(clock: Clock | None) -> str:
    now = (clock or SystemClock()).now()
    return now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat().replace("+00:00", "Z")


def default_diagnosis_client(vault: LoadedVault) -> Any | None:
    """The ``ai.routing.diagnosis`` client (unset: the resolved grading route)."""

    from learnloop.ai.routing import ready_client_for_task

    config = getattr(vault.config, "diagnosis", None)
    resolved = ready_client_for_task(
        vault.root, vault.config, "diagnosis",
        # Codex turns take the async diagnoser's own deadline (other provider
        # types keep their profile timeout).
        timeout_seconds=int(getattr(config, "timeout_seconds", 300)),
    )
    return resolved.client if resolved.ready else None


def default_embedding_client(vault: LoadedVault) -> Any | None:
    from learnloop.ai.routing import ready_client_for_task

    if not vault.config.embedding.enabled:
        return None
    resolved = ready_client_for_task(vault.root, vault.config, "embedding")
    return resolved.client if resolved.ready else None


def process_next_job(
    vault: LoadedVault,
    repository: Repository,
    *,
    kind: str,
    owner: str,
    client_factory: ClientFactory | None = None,
    embedding_factory: ClientFactory | None = None,
    judge_factory: ClientFactory | None = None,
    attempt_id: str | None = None,
    session_id: str | None = None,
    spend: ReviewSpend | None = None,
    cancelled: Cancelled | None = None,
    clock: Clock | None = None,
) -> JobOutcome | None:
    """Lease and run the next runnable job of ``kind``; None when none is.

    ``spend`` is a command's shared budget (``learnloop diagnose drain`` /
    ``retry``); without one each diagnosis runs under
    :data:`LIVE_DIAGNOSIS_CAPS`. ``cancelled`` is checked before the claim and
    again before the paid request; a cancelled job is released unspent.
    """

    if cancelled is not None and cancelled():
        return None
    if kind == DIAGNOSE_KIND and not split_grading_active(vault):
        # The switch is off: record that every queued live diagnosis is held,
        # including those behind the head of the line that will not be leased
        # (write-once; placement decides a held miss there).
        repository.hold_queued_live_diagnoses(clock=clock)
    lease = DIAGNOSE_LEASE_SECONDS if kind == DIAGNOSE_KIND else EMBED_LEASE_SECONDS
    job = repository.lease_next_post_attempt_job(
        kind=kind, owner=owner, lease_seconds=lease, clock=clock, attempt_id=attempt_id
    )
    if job is None:
        return None
    if kind == DIAGNOSE_KIND:
        return run_diagnose_job(
            vault,
            repository,
            job,
            client_factory=client_factory or (lambda: default_diagnosis_client(vault)),
            session_id=session_id,
            embedding_factory=embedding_factory or (lambda: default_embedding_client(vault)),
            judge_factory=judge_factory or _default_judge_factory(vault),
            spend=spend,
            scope_attempt_id=attempt_id,
            cancelled=cancelled,
            clock=clock,
        )
    return run_embed_job(
        vault,
        repository,
        job,
        embedding_factory=embedding_factory or (lambda: default_embedding_client(vault)),
        clock=clock,
    )


def _default_judge_factory(vault: LoadedVault) -> ClientFactory:
    """The same-cause judge client, resolved only when a pair needs judging."""

    from learnloop.diagnosis.recurrence.live import default_live_judge_factory

    return default_live_judge_factory(vault)


def _existing_diagnosis(repository: Repository, job: Mapping[str, Any]) -> dict[str, Any] | None:
    """A COMPLETED diagnosis this job already wrote before a crash.

    That is the resume case (the row committed, the post-diagnosis steps or
    the settle did not): no second model call, the idempotent steps rerun. A
    failed or skipped row is never reused, so an owner retry runs fresh.
    """

    payload = job.get("payload") or {}
    if payload.get("diagnosis_id"):
        row = repository.attempt_diagnosis(str(payload["diagnosis_id"]))
        return row if row is not None and row.get("status") == "completed" else None
    for row in reversed(repository.attempt_diagnoses_for_attempt(str(job["attempt_id"]))):
        # Only rows minted after this job (ULIDs order creation; the timestamp
        # alone ties within a second).
        if str(row.get("created_at") or "") < str(job.get("created_at") or "") or str(row["id"]) < str(job["id"]):
            break
        if (
            row.get("status") == "completed"
            and row.get("mode") == payload.get("mode", "live")
            and row.get("blind_grade_record_id") == payload.get("blind_grade_record_id")
        ):
            return row
    return None


def _finish(repository: Repository, job: Mapping[str, Any], state: str, *, error: str | None = None,
            payload: Mapping[str, Any] | None = None, clock: Clock | None = None) -> bool:
    return repository.finish_post_attempt_job(
        str(job["id"]), epoch=int(job["lease_epoch"]), state=state, last_error=error,
        payload=payload, clock=clock,
    )


def _lease_heartbeat(repository: Repository, job: Mapping[str, Any], clock: Clock | None) -> Callable[[], bool]:
    """Renew this worker's diagnose lease for another full term; False once lost.

    Slice 2 T1's work after the diagnosis (embedding requests, up to
    ``judge_max_pairs_per_attempt`` judge calls, the escalated repair) can
    outlast one lease; each paid request renews it first, so no other worker
    re-leases the job and repeats paid work meanwhile (second review F7).
    """

    def heartbeat() -> bool:
        return repository.renew_post_attempt_lease(
            str(job["id"]), epoch=int(job["lease_epoch"]), lease_seconds=DIAGNOSE_LEASE_SECONDS, clock=clock,
        )

    return heartbeat


def _release(repository: Repository, job: Mapping[str, Any], *, not_before: str, error: str | None,
             refund: bool, clock: Clock | None) -> bool:
    return repository.release_post_attempt_job(
        str(job["id"]), epoch=int(job["lease_epoch"]), not_before=not_before,
        last_error=error, refund_attempt=refund, clock=clock,
    )


def _persist(
    repository: Repository,
    job: Mapping[str, Any],
    *,
    diagnosis_id: str,
    values: dict[str, Any],
    clock: Clock | None,
) -> str:
    """Write the diagnosis + receipt only while this worker still owns the job."""

    with repository.atomic():
        if not repository.owns_post_attempt_job(str(job["id"]), epoch=int(job["lease_epoch"])):
            raise _LeaseLost(str(job["id"]))
        return repository.insert_attempt_diagnosis(diagnosis_id=diagnosis_id, clock=clock, **values)


def _receipt_for_storage(outcome: DiagnosisOutcome) -> dict[str, Any]:
    receipt = dict(outcome.receipt or {})
    history = receipt.get("history_attempt_ids") or []
    return {
        "context_hash": outcome.context_hash,
        "context_as_of_attempt_id": receipt.get("context_as_of_attempt_id"),
        "lagged_attempts": receipt.get("lagged_attempts"),
        "failure_attempt_ids": list(receipt.get("failure_attempt_ids") or []) or list(history),
        "success_attempt_ids": list(receipt.get("success_attempt_ids") or []),
        "hypothesis_ids": list(receipt.get("hypothesis_ids") or []),
        "registry_candidate_ids": list(receipt.get("registry_candidate_ids") or []),
        "prerequisite_refs": list(receipt.get("prerequisite_refs") or []),
        "retrieval": {
            key: value
            for key, value in receipt.items()
            if key not in {"validated_citations", "anchoring_suspect"}
        },
        "anchoring_suspect": outcome.anchoring_suspect,
        "validated_citations": list(outcome.validated_citations or []),
    }


#: One diagnosis's embedding retrieval (the hybrid attempt index, the
#: registry shortlist, any embed-on-demand they need): metered and priced.
#: The per-job budget of a diagnosis run without a command budget (the
#: sidecar worker, the CLI/TUI inline path).
RETRIEVAL_CAPS = SpendCaps(
    max_candidates=400,
    max_pairs=0,
    max_retries=1,
    max_calls=8,
    max_total_tokens=400_000,
    max_estimated_usd=0.05,
)
#: The spend route retrieval embeddings are admitted on in a command budget
#: (``OUTPUT_ALLOWANCE["embedding"]`` is 0: an embedding generates nothing).
RETRIEVAL_ROUTE = "embedding"


class _NoRegistryIndex:
    """Embeddings are on but no client is ready: the exact registry set, recorded (S6)."""

    model_id = None

    def registry_knn(self, current: Any, records: Any, *, limit: int) -> Any:
        from learnloop.diagnosis.split.context import RegistryShortlist

        return RegistryShortlist(method="exact_fallback", error="no_embedding_client")


def register_retrieval_route(spend: ReviewSpend, client: Any = None, *, vault: LoadedVault | None = None) -> Any:
    """Classify the retrieval embedding route on a command budget.

    From the client a run builds, or (``vault``, a dry run) from config. A
    published price wins over the command's ``--price-per-million``, which
    exists for a route whose price is unknown; an unknown price still fails
    closed (the request is refused and retrieval falls back, S6).
    """

    from learnloop.diagnosis.offline_review.spend import KNOWN_PRICES_PER_MILLION, RouteInfo

    if client is not None:
        info = spend.register(RETRIEVAL_ROUTE, client, model_id=getattr(client, "model_id", None))
    else:
        from learnloop.diagnosis.offline_review.runner import route_profiles

        profile = route_profiles(vault)[RETRIEVAL_ROUTE]
        info = spend.register_profile(
            RETRIEVAL_ROUTE,
            provider=profile["provider"],
            model=profile["model"],
            subscription=bool(profile["subscription"]),
            max_tokens=profile["max_tokens"],
        )
    known = KNOWN_PRICES_PER_MILLION.get(str(info.model or ""))
    if info.billing == "metered" and info.price_source == "owner_override" and known is not None:
        info = RouteInfo(info.route, info.provider, info.model, info.billing, known, "known", info.output_limit)
        spend.routes[RETRIEVAL_ROUTE] = info
    return info


def _sum_estimates(*estimates: SpendEstimate) -> SpendEstimate:
    usd = [estimate.estimated_usd for estimate in estimates]
    return SpendEstimate(
        candidates=sum(estimate.candidates for estimate in estimates),
        calls=sum(estimate.calls for estimate in estimates),
        total_tokens=sum(estimate.total_tokens for estimate in estimates),
        estimated_usd=None if any(value is None for value in usd) else sum(usd),
    )


def _diagnosis_reserve(spend: ReviewSpend, count: int) -> SpendEstimate:
    """What ``count`` diagnosis calls need at least: a call each plus its output limit."""

    return spend.estimate(
        DIAGNOSIS_ROUTE, calls=count, input_tokens=0, output_tokens=count * spend.output_limit(DIAGNOSIS_ROUTE)
    )


def _remaining_diagnoses_reserve(
    spend: ReviewSpend, repository: Repository, *, scope_attempt_id: str | None = None
) -> Callable[[], SpendEstimate]:
    """What a command must keep for the diagnoses still queued after this one.

    Slice 2 T1's judge calls, embedding requests and escalated repair are
    optional work inside a diagnose job: each is admitted on the command's
    budget only while every OTHER queued diagnosis (the current one is done)
    still fits after it (a call and its output limit each).
    """

    def reserve() -> SpendEstimate:
        queued = len(
            repository.post_attempt_jobs(kind=DIAGNOSE_KIND, states=("queued", "leased"), attempt_id=scope_attempt_id)
        )
        return _diagnosis_reserve(spend, max(queued - 1, 0))

    return reserve


def _command_retrieval_guard(
    spend: ReviewSpend, repository: Repository, *, scope_attempt_id: str | None = None
) -> Callable[[str, int], Any]:
    """Admit each retrieval embedding request on the command's budget (review F12).

    Retrieval is optional (S6) and the diagnoses are the command's work: a
    request is admitted only while every queued diagnosis still fits the caps
    after it (a call and its output limit each). A refusal raises
    ``SpendLimitExceeded`` inside the retriever, which falls back to the
    exact set; nothing is sent.
    """

    @contextmanager
    def guard(purpose: str, tokens: int) -> Iterator[Any]:
        # The diagnoses this command can still run: every queued one, or
        # only its attempt's when the command is scoped to one.
        queued = len(
            repository.post_attempt_jobs(kind=DIAGNOSE_KIND, states=("queued", "leased"), attempt_id=scope_attempt_id)
        )
        request = spend.estimate(RETRIEVAL_ROUTE, calls=1, input_tokens=tokens, output_tokens=0)
        spend.check(_sum_estimates(request, _diagnosis_reserve(spend, max(queued, 1))))
        with spend.request(RETRIEVAL_ROUTE, purpose, input_tokens=tokens, output_tokens=0) as call:
            yield call

    return guard


def _hybrid_retriever(
    vault: LoadedVault,
    repository: Repository,
    embedding_factory: ClientFactory | None,
    *,
    spend: ReviewSpend | None = None,
    scope_attempt_id: str | None = None,
) -> Any | None:
    """The live kNN retriever (S1.4b hybrid index, S1.4a registry shortlist),
    or None (then hybrid degrades to exact and the registry block is the
    exact set, S6).

    With a command budget (``spend``) every embedding request is admitted
    and charged there (review F12); without one, a per-job
    :data:`RETRIEVAL_CAPS` budget admits them.
    """

    if embedding_factory is None:
        return None
    try:
        client = embedding_factory()
    except Exception:  # noqa: BLE001 - S6: retrieval never fails a diagnosis
        return None
    if client is None:
        return None
    from learnloop.diagnosis.split.retrieval import EmbeddingHistoryRetriever

    if spend is not None:
        register_retrieval_route(spend, client)
        return EmbeddingHistoryRetriever(
            client=client,
            sqlite_path=repository.sqlite_path,
            guard=_command_retrieval_guard(spend, repository, scope_attempt_id=scope_attempt_id),
        )

    from learnloop.ai.spend import SpendBudget
    from learnloop.diagnosis.split.embeddings import PRICES_PER_MILLION

    budget = SpendBudget(RETRIEVAL_CAPS)
    price = PRICES_PER_MILLION.get(getattr(client, "model_id", ""))

    def guard(_purpose: str, tokens: int):
        return budget.request(
            SpendEstimate(
                calls=1,
                total_tokens=tokens,
                estimated_usd=(tokens * price / 1_000_000) if price is not None else None,
            )
        )

    return EmbeddingHistoryRetriever(client=client, sqlite_path=repository.sqlite_path, guard=guard)


def run_diagnose_job(
    vault: LoadedVault,
    repository: Repository,
    job: Mapping[str, Any],
    *,
    client_factory: ClientFactory,
    embedding_factory: ClientFactory | None = None,
    judge_factory: ClientFactory | None = None,
    session_id: str | None = None,
    spend: ReviewSpend | None = None,
    scope_attempt_id: str | None = None,
    cancelled: Cancelled | None = None,
    clock: Clock | None = None,
) -> JobOutcome:
    attempt_id = str(job["attempt_id"])
    payload = dict(job.get("payload") or {})
    mode = str(payload.get("mode") or "live")
    outcome = JobOutcome(job_id=str(job["id"]), attempt_id=attempt_id, kind=DIAGNOSE_KIND, state="done")
    config = getattr(vault.config, "diagnosis", None)
    attempt = repository.fetch_practice_attempt(attempt_id)
    if attempt is None:
        _finish(repository, job, "skipped", error="attempt_missing", clock=clock)
        outcome.state, outcome.error = "skipped", "attempt_missing"
        return outcome
    try:
        existing = _existing_diagnosis(repository, job)
        if existing is None:
            if mode == "live" and not split_grading_active(vault):
                # Kill switch off (or the vault no longer splits): the diagnoser
                # does not run; the job waits rather than failing.
                _release(repository, job, not_before=_later(SPLIT_OFF_RECHECK_SECONDS, clock),
                         error="split_disabled", refund=True, clock=clock)
                # Queued again: stamp it held (a no-op once it was stamped).
                repository.hold_queued_live_diagnoses(clock=clock)
                outcome.state, outcome.error = "released", "split_disabled"
                return outcome
            record_row = repository.latest_blind_grade_record(attempt_id) if mode == "live" else None
            if record_row is not None and not needs_diagnosis(record_row.get("record") or {}):
                # A regrade left nothing to explain (§5.1): record that, so the
                # previous explanation stops being shown for the new grade.
                diagnosis_id = _persist(repository, job, diagnosis_id=new_ulid(), values={
                    "attempt_id": attempt_id, "diagnosis_prompt_version": DIAGNOSIS_PROMPT_VERSION,
                    "mode": mode, "history_mode": settings_from_config(vault).history_mode,
                    "status": "skipped", "proposal": None, "causal_view": None,
                    "validation_report": {"skip_reason": "not_needed"}, "receipt": None,
                    "blind_grade_record_id": str(record_row["id"]), "error": "not_needed",
                    "supersedes_id": _superseded(repository, attempt_id, mode, payload),
                }, clock=clock)
                _finish(repository, job, "skipped", error="not_needed", clock=clock)
                outcome.state, outcome.error, outcome.diagnosis_id = "skipped", "not_needed", diagnosis_id
                return outcome
            if cancelled is not None and cancelled():
                _release(repository, job, not_before=utc_now_iso(clock), error="cancelled",
                         refund=True, clock=clock)
                outcome.state, outcome.error = "released", "cancelled"
                return outcome
            limit = int(getattr(config, "max_calls_per_day", 500))
            # Counted at admission: every diagnosis request that was sent
            # today, failed ones included (review F5).
            if repository.diagnosis_calls_since(_day_start(clock)) >= limit:
                diagnosis_id = _persist(repository, job, diagnosis_id=new_ulid(), values={
                    "attempt_id": attempt_id, "diagnosis_prompt_version": DIAGNOSIS_PROMPT_VERSION,
                    "mode": mode, "history_mode": settings_from_config(vault).history_mode,
                    "status": "skipped", "proposal": None, "causal_view": None,
                    "validation_report": {"skip_reason": "budget", "max_calls_per_day": limit},
                    "receipt": None, "blind_grade_record_id": payload.get("blind_grade_record_id"),
                    "error": "budget",
                }, clock=clock)
                _finish(repository, job, "skipped", error="budget", clock=clock)
                outcome.state, outcome.error, outcome.diagnosis_id = "skipped", "budget", diagnosis_id
                return outcome
            client = client_factory()
            if client is None:
                _release(repository, job, not_before=_later(NOT_READY_RECHECK_SECONDS, clock),
                         error="provider_not_ready", refund=True, clock=clock)
                outcome.state, outcome.error = "released", "provider_not_ready"
                return outcome
            existing = _diagnose(
                vault, repository, job, attempt, client=client, mode=mode, payload=payload,
                embedding_factory=embedding_factory, clock=clock, outcome=outcome,
                spend=spend, scope_attempt_id=scope_attempt_id, cancelled=cancelled,
            )
            if existing is None:
                return outcome
        outcome.diagnosis_id = str(existing["id"])
        outcome.status = str(existing["status"])
        if existing["status"] == "completed" and existing["mode"] == "live":
            apply_diagnosis(
                vault, repository, attempt=attempt, diagnosis=existing, session_id=session_id, clock=clock,
                judge_factory=judge_factory, embedding_factory=embedding_factory, writer_factory=client_factory,
                spend=spend, scope_attempt_id=scope_attempt_id, cancelled=cancelled,
                heartbeat=_lease_heartbeat(repository, job, clock),
            )
            if vault.config.embedding.enabled:
                enqueue_embed_job(
                    repository,
                    attempt_id=attempt_id,
                    diagnosis_id=str(existing["id"]),
                    include_divergence=settings_from_config(vault).history_mode == "hybrid",
                    clock=clock,
                )
        final_state = {
            "completed": "done",
            "skipped": "skipped",
        }.get(str(existing["status"]), "failed")
        if not _finish(repository, job, final_state, error=existing.get("error"),
                       payload={**payload, "diagnosis_id": existing["id"]}, clock=clock):
            # Another worker re-leased the job meanwhile: it settles it.
            outcome.state, outcome.error = "lease_lost", "lease_lost"
            return outcome
        outcome.state = final_state
        outcome.error = outcome.error or existing.get("error")
        return outcome
    except _LeaseLost:
        outcome.state, outcome.error = "lease_lost", "lease_lost"
        return outcome


def _diagnose(
    vault: LoadedVault,
    repository: Repository,
    job: Mapping[str, Any],
    attempt: Mapping[str, Any],
    *,
    client: Any,
    mode: str,
    payload: Mapping[str, Any],
    embedding_factory: ClientFactory | None,
    clock: Clock | None,
    outcome: JobOutcome,
    spend: ReviewSpend | None = None,
    scope_attempt_id: str | None = None,
    cancelled: Cancelled | None = None,
) -> dict[str, Any] | None:
    """One model call; returns the persisted diagnosis row, or None when released.

    The request is admitted through the shared spend framework (the command's
    ``spend``, else a per-job :data:`LIVE_DIAGNOSIS_CAPS` budget) before it is
    sent; model-call receipts are written through the same observer.
    """

    attempt_id = str(attempt["id"])
    settings = settings_from_config(vault)
    config = getattr(vault.config, "diagnosis", None)
    item = vault.practice_items.get(str(attempt.get("practice_item_id") or ""))
    record_row = repository.latest_blind_grade_record(attempt_id)
    if record_row is not None:
        record = dict(record_row.get("record") or {})
    else:
        record = joint_grade_record(vault, repository, attempt)
    current = current_attempt_for(vault, attempt, record) if item is not None else None
    base_values: dict[str, Any] = {
        "attempt_id": attempt_id,
        "diagnosis_prompt_version": DIAGNOSIS_PROMPT_VERSION,
        "mode": mode,
        "history_mode": settings.history_mode,
        "blind_grade_record_id": payload.get("blind_grade_record_id"),
        "supersedes_id": _superseded(repository, attempt_id, mode, payload),
    }
    if item is None or current is None:
        row_id = _persist(repository, job, diagnosis_id=new_ulid(), values={
            **base_values, "status": "failed", "proposal": None, "causal_view": None,
            "validation_report": {}, "receipt": None, "error": "item_missing",
        }, clock=clock)
        return repository.attempt_diagnosis(row_id)
    rubric = resolved_rubric(vault, item)
    store = live_history_store(vault, repository)
    job_spend = spend if spend is not None else ReviewSpend(LIVE_DIAGNOSIS_CAPS, cancelled=cancelled)
    # Billed as the client actually built (a provider override included).
    job_spend.register(DIAGNOSIS_ROUTE, client)
    job_spend.collector.sink = lambda action, event: repository.record_model_event(
        action, event, owner_kind=MODEL_CALL_OWNER_KIND, owner_id=attempt_id
    )
    # One embedding retriever per diagnosis: the hybrid attempt index (S1.4b,
    # hybrid mode only) and the whole-vault registry shortlist (S1.4a, every
    # mode once embeddings are on). A command's retrieval is admitted and
    # charged on the command's budget (review F12).
    embedder = (
        _hybrid_retriever(vault, repository, embedding_factory, spend=spend, scope_attempt_id=scope_attempt_id)
        if settings.history_mode == "hybrid" or vault.config.embedding.enabled
        else None
    )
    retriever = embedder if settings.history_mode == "hybrid" else None
    registry_retriever = (
        (embedder if embedder is not None else _NoRegistryIndex())
        if vault.config.embedding.enabled
        else None
    )
    if retriever is not None:
        try:
            # Centre over every prior failure of this model (embed-on-demand for
            # any the embed jobs have not reached yet); failures degrade (S6).
            # Observed like the diagnosis: metered and receipted.
            with job_spend.collector.observing():
                retriever.prepare([a for a in store.attempts_before(current.ref(), None) if a.non_pass])
        except Exception:  # noqa: BLE001 - S6
            retriever = None
    agent_run_id = repository.insert_agent_run(
        {
            "id": new_ulid(),
            "purpose": "diagnosis",
            "provider": getattr(client, "provider_name", None) or "unknown",
            "provider_type": getattr(client, "provider_type", None),
            "model": getattr(client, "model", None),
            "prompt_template": "diagnosis",
            "prompt_version": DIAGNOSIS_PROMPT_VERSION,
            "output_schema": "DiagnosisProposal",
            "started_at": utc_now_iso(clock),
            "status": "running",
        }
    )
    admitted = {"requests": 0}

    @contextmanager
    def guard(purpose: str, tokens: int) -> Iterator[Any]:
        with job_spend.request(DIAGNOSIS_ROUTE, purpose, input_tokens=tokens) as call:
            admitted["requests"] += 1
            yield call

    started = time.monotonic()
    try:
        with job_spend.collector.observing():
            result = run_diagnosis(
                client,
                vault=vault,
                item=item,
                rubric=rubric,
                store=store,
                current=current,
                settings=settings,
                retriever=retriever,
                guard=guard,
                registry_retriever=registry_retriever,
            )
    except AIInterrupted as exc:  # includes SpendCancelled
        reason = "cancelled" if not admitted["requests"] else "interrupted"
        # Nothing sent: the run is cancelled and does not count toward the
        # daily cap; an interrupted request was sent and does.
        finish_agent_run(
            repository, agent_run_id, client,
            status="cancelled" if not admitted["requests"] else "failed",
            error_message=reason if reason == "interrupted" else f"cancelled: {exc}",
            clock=clock,
        )
        _release(repository, job, not_before=utc_now_iso(clock), error=reason, refund=True, clock=clock)
        outcome.state, outcome.error = "released", reason
        return None
    except SpendLimitExceeded as exc:
        finish_agent_run(
            repository, agent_run_id, client,
            status="cancelled" if not admitted["requests"] else "failed",
            error_message=f"spend_refused: {exc}",
            clock=clock,
        )
        if spend is not None:
            # A COMMAND's caps are spent: the job is not at fault. Put it back
            # unspent; the command stops (``drain`` stops on a release).
            _release(repository, job, not_before=utc_now_iso(clock), error="over_budget", refund=True, clock=clock)
            outcome.state, outcome.error = "released", "over_budget"
            return None
        row_id = _persist(repository, job, diagnosis_id=new_ulid(), values={
            **base_values, "agent_run_id": agent_run_id, "status": "skipped", "proposal": None,
            "causal_view": None, "receipt": None, "error": "budget",
            "validation_report": {"skip_reason": "budget", "spend_refused": str(exc),
                                  "caps": LIVE_DIAGNOSIS_CAPS.as_dict()},
        }, clock=clock)
        return repository.attempt_diagnosis(row_id)
    except Exception as exc:  # noqa: BLE001 - a diagnosis failure never touches the grade
        result = DiagnosisOutcome(attempt_id=attempt_id, mode=settings.history_mode, status="failed")
        result.error = type(exc).__name__
        LOG.warning("diagnosis failed for attempt %s", attempt_id, exc_info=True)
    finish_agent_run(
        repository, agent_run_id, client,
        status="completed" if result.status in ("completed", "validation_rejected") else "failed",
        error_message=result.error, clock=clock,
    )
    max_attempts = int(getattr(config, "max_attempts", 5))
    if result.status == "failed" and int(job.get("attempt_count") or 1) < max_attempts:
        _release(repository, job, not_before=_backoff(int(job.get("attempt_count") or 1), clock),
                 error=result.error, refund=False, clock=clock)
        outcome.state, outcome.error = "released", result.error
        return None
    diagnosis_id = new_ulid()
    causal_view = None
    if result.status == "completed" and mode == "live" and result.proposal is not None:
        causal_view = build_causal_view(
            diagnosis_id=diagnosis_id,
            proposal=result.proposal,
            record=record,
            error_events=repository.raw_error_events_for_attempt(attempt_id),
            agent_run_id=agent_run_id,
        )
    row_id = _persist(repository, job, diagnosis_id=diagnosis_id, values={
        **base_values,
        "agent_run_id": agent_run_id,
        "provider": result.provider,
        "model": result.model,
        "history_mode": result.mode,
        "status": result.status,
        "proposal": result.proposal,
        "causal_view": causal_view,
        "validation_report": result.validation_report,
        "receipt": _receipt_for_storage(result) if result.receipt else None,
        "error": result.error,
        "latency_seconds": round(time.monotonic() - started, 3),
    }, clock=clock)
    return repository.attempt_diagnosis(row_id)


def _superseded(repository: Repository, attempt_id: str, mode: str, payload: Mapping[str, Any]) -> str | None:
    if not payload.get("rediagnose"):
        return None
    prior = repository.latest_attempt_diagnosis(attempt_id, mode=mode)
    return str(prior["id"]) if prior is not None else None


def apply_diagnosis(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt: Mapping[str, Any],
    diagnosis: Mapping[str, Any],
    session_id: str | None = None,
    clock: Clock | None = None,
    judge_factory: ClientFactory | None = None,
    embedding_factory: ClientFactory | None = None,
    writer_factory: ClientFactory | None = None,
    spend: ReviewSpend | None = None,
    scope_attempt_id: str | None = None,
    cancelled: Cancelled | None = None,
    heartbeat: Callable[[], bool] | None = None,
) -> None:
    """The diagnosis-dependent pipeline steps (§7.2 worker half). Idempotent.

    ``heartbeat`` (inside a leased diagnose job) renews the job's lease before
    each of T1's paid requests and stops them once another worker holds it.

    ``spend``: the enclosing command's budget (``drain``/``retry``). Its caps,
    cancellation and spend summary then cover T1's judge calls, embedding
    requests and escalated-repair request too, each admitted only while the
    command's remaining diagnoses still fit; without one they run under
    per-job budgets.

    1. The attempt's still-open factor takes the candidate set the projection
       now derives from the diagnosis (what a rebuild would open it with).
    2. Slice 2 T1 (``mvp-0.12``): materialize, refresh the recurrence groups
       (this diagnosis's validated citations now count) and, with the judge
       and embeddings on, judge this attempt's shortlisted same-cause pairs,
       so step 3's promotion and K=3 count see the merges.
    3. Materialization from the diagnosis + misconception normalization with
       ``registry_match`` (no ``misconception_match`` call), via the shared
       normalizer, which materializes first in canonical vaults.
    4. The machine-check sweep and the common-repair consultation.
    5. Validated pattern claims become ``same_cause`` verdicts (judge
       ``diagnoser``); T1's group builder reads them from the receipts.
    6. Slice 2 T1: the escalation receipt when the cause recurred K times.
    """

    from learnloop.diagnosis.recurrence.live import record_escalation, recurrence_step

    from learnloop.diagnosis.followups import run_post_diagnosis_hooks
    from learnloop.diagnosis.misconceptions import normalize_and_resolve_attempt

    attempt_id = str(attempt["id"])
    learning_object_id = str(attempt.get("learning_object_id") or "")
    # The projection reads the whole observation ledger, computes, and
    # REPLACES the cache. Concurrent submissions publish their own projection
    # inside their attempt transaction, so the worker's read-compute-replace
    # takes the write lock first (BEGIN IMMEDIATE): no attempt can commit
    # between its snapshot and its publication (review F3).
    with repository.atomic():
        project_canonical_facet_state(
            vault, repository, clock=clock, refresh_factor_candidates_for={attempt_id}
        )
    reserve = _remaining_diagnoses_reserve(spend, repository, scope_attempt_id=scope_attempt_id) if spend is not None else None
    recurrence_step(
        vault, repository, attempt_id=attempt_id, judge_factory=judge_factory,
        embedding_factory=embedding_factory, spend=spend, reserve=reserve, cancelled=cancelled, clock=clock,
        heartbeat=heartbeat,
    )
    normalize_and_resolve_attempt(
        vault,
        repository,
        attempt_id=attempt_id,
        learning_object_id=learning_object_id,
        ai_client=None,
        clock=clock,
    )
    run_post_diagnosis_hooks(
        vault,
        repository,
        attempt_id=attempt_id,
        learning_object_id=learning_object_id,
        session_id=session_id,
        clock=clock,
    )
    record_pattern_verdicts(repository, diagnosis=diagnosis, attempt_id=attempt_id)
    try:
        record_escalation(
            vault, repository, attempt_id=attempt_id, diagnosis=diagnosis, writer_factory=writer_factory,
            spend=spend, reserve=reserve, cancelled=cancelled, clock=clock, heartbeat=heartbeat,
        )
    except Exception:  # noqa: BLE001 - the escalation display never fails the diagnosis
        LOG.warning("escalation receipt failed for attempt %s", attempt_id, exc_info=True)


def record_pattern_verdicts(repository: Repository, *, diagnosis: Mapping[str, Any], attempt_id: str) -> int:
    """Append one ``same_cause`` verdict per validated citation (idempotent)."""

    from learnloop.ai.execution import content_key
    from learnloop.db.stores.judgments import append_judgment

    receipt = repository.diagnosis_context_receipt(str(diagnosis["id"])) or {}
    proposal = diagnosis.get("proposal") or {}
    written = 0
    with repository.atomic():
        connection = repository.connection()
        for citation in receipt.get("validated_citations") or []:
            index = int(citation.get("claim_index", -1))
            # The stored proposal keeps only claims that survived validation,
            # so ``claim_index`` (a pre-validation position) can point past a
            # dropped claim; find the claim that cites this attempt instead.
            claim = claim_for_citation(proposal, citation) or {}
            relation = str(claim.get("relation") or "same_mechanism")
            cited = str(citation.get("attempt_id") or "")
            if not cited:
                continue
            input_hash = content_key({"diagnosis_id": diagnosis["id"], "claim": index, "cited": cited})
            exists = connection.execute(
                "SELECT 1 FROM judgment_ledger WHERE task = 'same_cause' AND input_hash = ? LIMIT 1",
                (input_hash,),
            ).fetchone()
            if exists is not None:
                continue
            append_judgment(
                connection,
                task="same_cause",
                left_kind="attempt",
                left_id=attempt_id,
                right_kind="attempt",
                right_id=cited,
                judge="diagnoser",
                judge_model=str(diagnosis.get("model") or "unknown"),
                prompt_version=str(diagnosis.get("diagnosis_prompt_version") or DIAGNOSIS_PROMPT_VERSION),
                input_hash=input_hash,
                verdict="different" if relation == "disconfirming" else "same",
                rationale=f"validated citation ({relation}); shadow, no authority",
            )
            written += 1
    return written


def run_embed_job(
    vault: LoadedVault,
    repository: Repository,
    job: Mapping[str, Any],
    *,
    embedding_factory: ClientFactory,
    clock: Clock | None = None,
) -> JobOutcome:
    """Embed-on-write (S1.4a/b), then the would-merge log. Best effort."""

    from learnloop.diagnosis.split.embeddings import (
        divergence_records,
        embed_records,
        hypothesis_records,
        misconception_records,
        record_would_merge,
    )

    attempt_id = str(job["attempt_id"])
    payload = dict(job.get("payload") or {})
    outcome = JobOutcome(job_id=str(job["id"]), attempt_id=attempt_id, kind=EMBED_KIND, state="done")
    try:
        client = embedding_factory()
    except Exception:  # noqa: BLE001
        client = None
    if client is None:
        _release(repository, job, not_before=_later(NOT_READY_RECHECK_SECONDS * 10, clock),
                 error="embedding_unavailable", refund=True, clock=clock)
        outcome.state, outcome.error = "released", "embedding_unavailable"
        return outcome
    records = [*hypothesis_records(repository, attempt_ids=[attempt_id]), *misconception_records(repository)]
    if payload.get("include_divergence"):
        records.extend(divergence_records(vault, repository, attempt_ids=[attempt_id]))
    # Embed-on-write calls belong to the attempt, like its diagnosis's.
    with record_model_calls(repository, owner_kind=MODEL_CALL_OWNER_KIND, owner_id=attempt_id):
        result = embed_records(client, repository, records)
    if result.status != "complete":
        max_attempts = int(getattr(getattr(vault.config, "diagnosis", None), "max_attempts", 5))
        if int(job.get("attempt_count") or 1) < max_attempts:
            _release(repository, job, not_before=_backoff(int(job.get("attempt_count") or 1), clock),
                     error=result.error, refund=False, clock=clock)
            outcome.state, outcome.error = "released", result.error
            return outcome
        _finish(repository, job, "failed", error=result.error, clock=clock)
        outcome.state, outcome.error = "failed", result.error
        return outcome
    try:
        written = record_would_merge(
            repository,
            diagnosis_id=payload.get("diagnosis_id"),
            attempt_id=attempt_id,
            model_id=client.model_id,
        )
        outcome.notes.append(f"would_merge_rows={written}")
    except Exception:  # noqa: BLE001 - the shadow log never fails the job
        LOG.warning("would-merge log failed for attempt %s", attempt_id, exc_info=True)
    _finish(repository, job, "done", payload={**payload, "embedded": result.embedded}, clock=clock)
    return outcome


def drain(
    vault: LoadedVault,
    repository: Repository,
    *,
    owner: str = "cli",
    kinds: tuple[str, ...] = (DIAGNOSE_KIND, EMBED_KIND),
    attempt_id: str | None = None,
    client_factory: ClientFactory | None = None,
    embedding_factory: ClientFactory | None = None,
    judge_factory: ClientFactory | None = None,
    max_jobs: int = 1_000,
    spend: ReviewSpend | None = None,
    cancelled: Cancelled | None = None,
    clock: Clock | None = None,
) -> list[JobOutcome]:
    """Run runnable jobs until none is left (``learnloop diagnose --drain``).

    Stops before the next job once ``cancelled()`` is true (SIGINT/SIGTERM in
    the CLI), and after a release (provider not ready, cancelled, a
    command's spend caps reached).
    """

    outcomes: list[JobOutcome] = []
    for kind in kinds:
        while len(outcomes) < max_jobs:
            if cancelled is not None and cancelled():
                return outcomes
            result = process_next_job(
                vault,
                repository,
                kind=kind,
                owner=owner,
                client_factory=client_factory,
                embedding_factory=embedding_factory,
                judge_factory=judge_factory,
                attempt_id=attempt_id if kind == DIAGNOSE_KIND else None,
                spend=spend if kind == DIAGNOSE_KIND else None,
                cancelled=cancelled,
                clock=clock,
            )
            if result is None:
                break
            outcomes.append(result)
            if result.state in ("released", "lease_lost"):
                break
    return outcomes


# -- dry-run planning (``learnloop diagnose drain|retry --dry-run``) ------------------


def command_spend(
    vault: LoadedVault,
    caps: SpendCaps,
    *,
    price_per_million: float | None = None,
    cancelled: Cancelled | None = None,
) -> ReviewSpend:
    """A command's shared budget; its routes are classified from config.

    The diagnosis route always; the retrieval embedding route when
    ``embedding.enabled`` (review F12: retrieval is admitted and charged on
    the same budget). A run re-registers each route with the client it
    actually builds, so a provider override is billed as what it is.
    """

    from learnloop.diagnosis.offline_review.runner import route_profiles

    spend = ReviewSpend(caps, cancelled=cancelled, price_per_million=price_per_million)
    profiles = route_profiles(vault)
    profile = profiles[DIAGNOSIS_ROUTE]
    spend.register_profile(
        DIAGNOSIS_ROUTE,
        provider=profile["provider"],
        model=profile["model"],
        subscription=bool(profile["subscription"]),
        max_tokens=profile["max_tokens"],
    )
    if profiles[RETRIEVAL_ROUTE]["enabled"]:
        register_retrieval_route(spend, vault=vault)
    return spend


def _plan_current(vault: LoadedVault, repository: Repository, attempt: Mapping[str, Any]) -> Any | None:
    record_row = repository.latest_blind_grade_record(str(attempt["id"]))
    record = dict(record_row.get("record") or {}) if record_row is not None else joint_grade_record(vault, repository, attempt)
    return current_attempt_for(vault, attempt, record)


def _estimated_prompt_tokens(vault: LoadedVault, current: Any, *, store: Any) -> int:
    """The diagnosis prompt's token estimate, assembled offline (no call).

    ``hybrid`` is estimated without its kNN additions (a dry run makes no
    embedding call); every other mode assembles exactly what would be sent.
    """

    from learnloop.diagnosis.split.context import assemble_diagnosis_context
    from learnloop.diagnosis.split.contract import diagnosis_prompt

    assembled = assemble_diagnosis_context(vault, store, current, settings_from_config(vault))
    return (len(diagnosis_prompt(assembled).encode("utf-8")) + 3) // 4


def _estimated_retrieval(
    vault: LoadedVault, repository: Repository, current: Any, *, store: Any, seen: set[tuple[str, str, str]]
) -> tuple[int, int]:
    """One diagnosis's retrieval embedding requests and input tokens (an upper bound)."""

    if not vault.config.embedding.enabled or not vault.config.embedding.model:
        return 0, 0
    from learnloop.diagnosis.split.retrieval import planned_retrieval_requests

    before = current.ref()
    hybrid = settings_from_config(vault).history_mode == "hybrid"
    return planned_retrieval_requests(
        repository.sqlite_path,
        str(vault.config.embedding.model),
        current,
        registry=list(store.registry_before(before, None)),
        failures=list(store.attempts_before(before, None)) if hybrid else (),
        seen=seen,
    )


def _retrieval_plan(
    spend: ReviewSpend, diagnosis_estimate: SpendEstimate, *, calls: int, input_tokens: int
) -> dict[str, Any] | None:
    """The retrieval half of a plan: its estimate and whether it fits beside the diagnoses."""

    info = spend.routes.get(RETRIEVAL_ROUTE)
    if info is None:
        return None
    estimate = spend.estimate(RETRIEVAL_ROUTE, calls=calls, input_tokens=input_tokens, output_tokens=0)
    try:
        spend.check(_sum_estimates(diagnosis_estimate, estimate))
        fits, reason = True, None
    except SpendLimitExceeded as exc:
        fits, reason = False, str(exc)
    return {
        "calls": calls,
        "estimated_input_tokens": input_tokens,
        "estimate": {
            "calls": estimate.calls,
            "metered_total_tokens": estimate.total_tokens,
            "estimated_usd": estimate.estimated_usd,
        },
        "route": info.as_dict(),
        "fits": fits,
        "reason": reason,
    }


def _recurrence_plan(
    vault: LoadedVault, spend: ReviewSpend, diagnosis_estimate: SpendEstimate, *, jobs: int
) -> dict[str, Any] | None:
    """Slice 2 T1's work inside the planned diagnose jobs, on the same caps.

    An upper bound per job: ``recurrence.judge_max_pairs_per_attempt`` judge
    calls, one embedding request for the attempt's own hypotheses and, at a
    recurrence group's K-th answer, one escalated-repair request. Like
    retrieval it is optional: at run time each request is admitted only while
    the remaining diagnoses still fit, and a refused one sends nothing.
    """

    from learnloop.diagnosis.recurrence.backlog import route_profile
    from learnloop.diagnosis.recurrence.escalation import (
        ESCALATION_REPAIR_PROMPT_TOKENS,
        ESCALATION_REPAIR_ROUTE,
    )
    from learnloop.diagnosis.recurrence.kind import SAME_CAUSE_ROUTE
    from learnloop.diagnosis.recurrence.live import PLANNED_EMBED_TOKENS_PER_JOB, PLANNED_JUDGE_PROMPT_TOKENS

    if jobs <= 0 or not recurrence_active(vault):
        return None
    config = vault.config.recurrence
    judging = bool(config.judge_enabled) and bool(vault.config.embedding.enabled) and int(config.judge_max_pairs_per_attempt) > 0
    judge_calls = jobs * int(config.judge_max_pairs_per_attempt) if judging else 0
    embed_calls = jobs if judging and RETRIEVAL_ROUTE in spend.routes else 0
    # No repair is requested for a card nobody sees (second review F9).
    repair_calls = (
        jobs if bool(getattr(config, "escalation_repair_enabled", True))
        and bool(getattr(config, "escalation_card_enabled", True)) else 0
    )
    for route, source in ((SAME_CAUSE_ROUTE, SAME_CAUSE_ROUTE), (ESCALATION_REPAIR_ROUTE, DIAGNOSIS_ROUTE)):
        if route not in spend.routes:
            profile = route_profile(vault, source)
            spend.register_profile(route, provider=profile["provider"], model=profile["model"],
                                   subscription=bool(profile["subscription"]), max_tokens=profile["max_tokens"])
    parts = {
        "judge": spend.estimate(SAME_CAUSE_ROUTE, calls=judge_calls, input_tokens=judge_calls * PLANNED_JUDGE_PROMPT_TOKENS,
                                output_tokens=judge_calls * spend.output_limit(SAME_CAUSE_ROUTE)),
        "escalation_repair": spend.estimate(
            ESCALATION_REPAIR_ROUTE, calls=repair_calls, input_tokens=repair_calls * ESCALATION_REPAIR_PROMPT_TOKENS,
            output_tokens=repair_calls * spend.output_limit(ESCALATION_REPAIR_ROUTE),
        ),
    }
    if embed_calls:
        parts["embedding"] = spend.estimate(RETRIEVAL_ROUTE, calls=embed_calls,
                                            input_tokens=embed_calls * PLANNED_EMBED_TOKENS_PER_JOB, output_tokens=0)
    total = _sum_estimates(*parts.values())
    try:
        spend.check(_sum_estimates(diagnosis_estimate, total))
        fits, reason = True, None
    except SpendLimitExceeded as exc:
        fits, reason = False, str(exc)
    return {
        "max_calls": total.calls,
        "by_part": {
            name: {"calls": value.calls, "metered_total_tokens": value.total_tokens, "estimated_usd": value.estimated_usd}
            for name, value in parts.items()
        },
        "estimate": {"calls": total.calls, "metered_total_tokens": total.total_tokens, "estimated_usd": total.estimated_usd},
        "routes": {
            name: spend.routes[route].as_dict()
            for name, route in (("judge", SAME_CAUSE_ROUTE), ("escalation_repair", ESCALATION_REPAIR_ROUTE),
                                ("embedding", RETRIEVAL_ROUTE))
            if route in spend.routes
        },
        "fits": fits,
        "reason": reason,
        "note": (
            "Slice 2 T1 inside each diagnose job, an upper bound: judge calls, one embedding request and at most "
            "one escalated-repair request per job; each is admitted on these caps only while the queued diagnoses "
            "still fit, and a refused one sends nothing (its pairs wait for the backlog)"
        ),
    }


_RETRIEVAL_NOTE = (
    "retrieval embeddings are admitted on these caps one request at a time, only while every queued "
    "diagnosis still fits after them; a refused request sends nothing and that diagnosis uses the exact set (S6)"
)


def plan_diagnosis_jobs(
    vault: LoadedVault,
    repository: Repository,
    *,
    spend: ReviewSpend,
    attempt_id: str | None = None,
    max_jobs: int = 1_000,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """What ``drain`` would run now, and its admission estimate (no call, no write).

    Follows the queue exactly: one diagnosis at a time in attempt order, a
    live lease or a backing-off head blocks the line, ``attempt_id`` runs
    only while that attempt's job is the head. Each planned call is
    estimated from its offline-assembled prompt plus the route's admitted
    output limit, and checked against the command's caps; the vault's daily
    cap turns calls past it into ``budget`` skips.
    """

    now = parse_utc(utc_now_iso(clock))
    config = getattr(vault.config, "diagnosis", None)
    open_jobs = repository.post_attempt_jobs(kind=DIAGNOSE_KIND, states=("queued", "leased"))
    blocked: str | None = None
    if any(
        job["state"] == "leased" and job.get("lease_expires_at") and parse_utc(job["lease_expires_at"]) > now
        for job in open_jobs
    ):
        blocked = "another worker holds a live diagnosis lease"
    planned: list[dict[str, Any]] = []
    store = live_history_store(vault, repository)
    limit = int(getattr(config, "max_calls_per_day", 500))
    used_today = repository.diagnosis_calls_since(_day_start(clock))
    calls = 0
    input_tokens = 0
    retrieval_calls = 0
    retrieval_tokens = 0
    embedded: set[tuple[str, str, str]] = set()
    for job in [] if blocked else open_jobs:
        if len(planned) >= max_jobs:
            break
        not_before = parse_utc(job["not_before"]) if job.get("not_before") else None
        expires = parse_utc(job["lease_expires_at"]) if job.get("lease_expires_at") else None
        runnable = (job["state"] == "queued" and (not_before is None or not_before <= now)) or (
            job["state"] == "leased" and (expires is None or expires <= now)
        )
        if not runnable:
            blocked = f"job {job['id']} is backing off until {job.get('not_before')}"
            break
        if attempt_id is not None and job["attempt_id"] != attempt_id:
            blocked = None if planned else f"an earlier attempt's diagnosis ({job['attempt_id']}) runs first"
            break
        mode = str((job.get("payload") or {}).get("mode") or "live")
        entry: dict[str, Any] = {"job_id": job["id"], "attempt_id": job["attempt_id"], "mode": mode}
        attempt = repository.fetch_practice_attempt(str(job["attempt_id"]))
        record_row = repository.latest_blind_grade_record(str(job["attempt_id"])) if mode == "live" else None
        if attempt is None:
            entry["action"] = "skip:attempt_missing"
        elif _existing_diagnosis(repository, job) is not None:
            entry["action"] = "resume:no_call"
        elif mode == "live" and not split_grading_active(vault):
            entry["action"] = "hold:split_disabled"
            planned.append(entry)
            break
        elif record_row is not None and not needs_diagnosis(record_row.get("record") or {}):
            entry["action"] = "skip:not_needed"
        elif used_today + calls >= limit:
            entry["action"] = "skip:budget"
            entry["max_calls_per_day"] = limit
        else:
            current = _plan_current(vault, repository, attempt)
            if current is None:
                entry["action"] = "fail:item_missing"
            else:
                tokens = _estimated_prompt_tokens(vault, current, store=store)
                entry["action"] = "diagnose"
                entry["estimated_input_tokens"] = tokens
                calls += 1
                input_tokens += tokens
                requests, embed_tokens = _estimated_retrieval(vault, repository, current, store=store, seen=embedded)
                if requests:
                    entry["retrieval_requests"] = requests
                retrieval_calls += requests
                retrieval_tokens += embed_tokens
        planned.append(entry)
    output_tokens = calls * spend.output_limit(DIAGNOSIS_ROUTE)
    estimate = spend.estimate(DIAGNOSIS_ROUTE, calls=calls, input_tokens=input_tokens, output_tokens=output_tokens)
    try:
        spend.check(estimate)
        admissible, reason = True, None
    except SpendLimitExceeded as exc:
        admissible, reason = False, str(exc)
    info = spend.routes[DIAGNOSIS_ROUTE]
    retrieval = _retrieval_plan(spend, estimate, calls=retrieval_calls, input_tokens=retrieval_tokens)
    applying = sum(1 for entry in planned if entry.get("action") in ("diagnose", "resume:no_call"))
    recurrence = _recurrence_plan(vault, spend, estimate, jobs=applying)
    return {
        "jobs": planned,
        "recurrence": recurrence,
        "blocked": blocked,
        "calls": calls,
        "estimated_input_tokens": input_tokens,
        "admitted_output_tokens": output_tokens,
        "estimate": {
            "calls": estimate.calls,
            "metered_total_tokens": estimate.total_tokens,
            "estimated_usd": estimate.estimated_usd,
        },
        "route": info.as_dict(),
        "daily_cap": {"max_calls_per_day": limit, "admitted_today": used_today},
        "admissible": admissible,
        "reason": reason,
        "retrieval": retrieval,
        "notes": (
            ["subscription route: one logical call each counts against max_calls; tokens and dollars are estimated from usage, not capped"]
            if info.billing == "subscription"
            else ["metered route: every physical request (retries, JSON repairs) is admitted against the caps before it is sent"]
        )
        + (["hybrid history mode is estimated without its kNN additions"] if settings_from_config(vault).history_mode == "hybrid" else [])
        + ([_RETRIEVAL_NOTE] if retrieval is not None else []),
    }


def plan_unqueued_diagnosis(
    vault: LoadedVault, repository: Repository, *, attempt_id: str, spend: ReviewSpend
) -> dict[str, Any]:
    """The one diagnosis call ``retry`` would queue for an attempt not in the queue."""

    attempt = repository.fetch_practice_attempt(attempt_id)
    store = live_history_store(vault, repository)
    current = _plan_current(vault, repository, attempt) if attempt is not None else None
    tokens = _estimated_prompt_tokens(vault, current, store=store) if current is not None else None
    requests, embed_tokens = (
        _estimated_retrieval(vault, repository, current, store=store, seen=set()) if current is not None else (0, 0)
    )
    output_tokens = spend.output_limit(DIAGNOSIS_ROUTE)
    estimate = spend.estimate(DIAGNOSIS_ROUTE, calls=1, input_tokens=tokens or 0, output_tokens=output_tokens)
    try:
        spend.check(estimate)
        admissible, reason = True, None
    except SpendLimitExceeded as exc:
        admissible, reason = False, str(exc)
    retrieval = _retrieval_plan(spend, estimate, calls=requests, input_tokens=embed_tokens)
    recurrence = _recurrence_plan(vault, spend, estimate, jobs=1)
    return {
        "jobs": [{"attempt_id": attempt_id, "action": "diagnose", "estimated_input_tokens": tokens}],
        "recurrence": recurrence,
        "blocked": None,
        "calls": 1,
        "estimated_input_tokens": tokens,
        "admitted_output_tokens": output_tokens,
        "estimate": {
            "calls": estimate.calls,
            "metered_total_tokens": estimate.total_tokens,
            "estimated_usd": estimate.estimated_usd,
        },
        "route": spend.routes[DIAGNOSIS_ROUTE].as_dict(),
        "admissible": admissible,
        "reason": reason,
        "retrieval": retrieval,
        "notes": [_RETRIEVAL_NOTE] if retrieval is not None else [],
    }


def plan_embed_jobs(vault: LoadedVault, repository: Repository, *, attempt_id: str | None = None) -> dict[str, Any]:
    """Pending embed-on-write work (each job runs under its own embedding caps)."""

    from learnloop.diagnosis.split.embeddings import (
        LIVE_CAPS,
        PRICES_PER_MILLION,
        divergence_records,
        hypothesis_records,
        misconception_records,
        pending_records,
    )

    jobs = [
        job
        for job in repository.post_attempt_jobs(kind=EMBED_KIND, states=("queued", "leased"))
        if attempt_id is None or job["attempt_id"] == attempt_id
    ]
    model = vault.config.embedding.model if vault.config.embedding.enabled else None
    if not jobs or model is None:
        return {"jobs": len(jobs), "model": model, "records_pending": 0, "estimated_tokens": 0, "estimated_usd": 0.0}
    records: dict[tuple[str, str, str], Any] = {}
    for job in jobs:
        payload = job.get("payload") or {}
        for record in (
            *hypothesis_records(repository, attempt_ids=[job["attempt_id"]]),
            *misconception_records(repository),
            *(divergence_records(vault, repository, attempt_ids=[job["attempt_id"]]) if payload.get("include_divergence") else ()),
        ):
            records[(record.record_kind, record.record_id, record.content_hash)] = record
    pending = pending_records(repository, list(records.values()), model)
    tokens = sum(len(record.text.encode("utf-8")) + 128 for record in pending)
    price = PRICES_PER_MILLION.get(model)
    return {
        "jobs": len(jobs),
        "model": model,
        "records_pending": len(pending),
        "estimated_tokens": tokens,
        "estimated_usd": (tokens * price / 1_000_000) if price is not None else None,
        "caps_per_job": LIVE_CAPS.as_dict(),
    }


__all__ = [
    "DIAGNOSE_KIND",
    "DIAGNOSIS_ROUTE",
    "LIVE_DIAGNOSIS_CAPS",
    "command_spend",
    "plan_diagnosis_jobs",
    "plan_embed_jobs",
    "plan_unqueued_diagnosis",
    "DONE",
    "EMBED_KIND",
    "FAILED",
    "JobOutcome",
    "NOT_NEEDED",
    "PENDING",
    "apply_diagnosis",
    "default_diagnosis_client",
    "default_embedding_client",
    "diagnosis_status",
    "drain",
    "enqueue_diagnosis",
    "enqueue_embed_job",
    "pending_diagnosis_attempts",
    "process_next_job",
    "record_pattern_verdicts",
    "run_diagnose_job",
    "run_embed_job",
]
