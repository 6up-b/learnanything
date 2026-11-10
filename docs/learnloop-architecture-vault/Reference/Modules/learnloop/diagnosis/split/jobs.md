---
title: "learnloop.diagnosis.split.jobs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/split/jobs.py"
source_paths:
  - "src/learnloop/diagnosis/split/jobs.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.split"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.split.jobs module"
  - "src/learnloop/diagnosis/split/jobs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-split"
---

# `learnloop.diagnosis.split.jobs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.split.jobs` exists within [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] to own the behavior summarized by its module contract: The asynchronous post-attempt jobs of the live split (Slice 1 §5.1, §7, §11).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/split/jobs.py](../../../../../../../src/learnloop/diagnosis/split/jobs.py) |
| Source lines | 1721 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class JobOutcome` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 93)
- `enqueue_diagnosis(vault: LoadedVault, repository: Repository, *, attempt_id: str, rediagnose: bool=False, clock: Clock | None=None) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 110) — Queue the attempt's diagnosis when §5.1 says it runs; returns the job id.
- `enqueue_embed_job(repository: Repository, *, attempt_id: str, diagnosis_id: str | None, include_divergence: bool, clock: Clock | None=None) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 164)
- `diagnosis_status(repository: Repository, attempt_id: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 185) — §11 UI status: pending | not_needed | done | failed (live diagnoses only).
- `session_diagnosis_availability(repository: Repository, session_id: str) -> tuple[list[str], list[str]]` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 213) — E7 at one serve: (attempts whose live diagnosis is required, those without it).
- `pending_diagnosis_attempts(repository: Repository, attempt_ids: list[str]) -> list[str]` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 237)
- `default_diagnosis_client(vault: LoadedVault) -> Any | None` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 263) — The ``ai.routing.diagnosis`` client (unset: the resolved grading route).
- `default_embedding_client(vault: LoadedVault) -> Any | None` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 278)
- `process_next_job(vault: LoadedVault, repository: Repository, *, kind: str, owner: str, client_factory: ClientFactory | None=None, embedding_factory: ClientFactory | None=None, judge_factory: ClientFactory | None=None, attempt_id: str | None=None, session_id: str | None=None, spend: ReviewSpend | None=None, cancelled: Cancelled | None=None, clock: Clock | None=None) -> JobOutcome | None` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 287) — Lease and run the next runnable job of ``kind``; None when none is.
- `record_diagnosis_reads(repository: Repository, *, diagnosis_id: str, proposal: Mapping[str, Any] | None, record: Any=None, reads: Any=None, clock: Clock | None=None) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 446) — Record what a diagnosis read (its write-time provenance), on the repository's current connection: inside the transaction that writes the diagnosis.
- `register_retrieval_route(spend: ReviewSpend, client: Any=None, *, vault: LoadedVault | None=None) -> Any` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 521) — Classify the retrieval embedding route on a command budget.
- `run_diagnose_job(vault: LoadedVault, repository: Repository, job: Mapping[str, Any], *, client_factory: ClientFactory, embedding_factory: ClientFactory | None=None, judge_factory: ClientFactory | None=None, session_id: str | None=None, spend: ReviewSpend | None=None, scope_attempt_id: str | None=None, cancelled: Cancelled | None=None, clock: Clock | None=None) -> JobOutcome` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 682)
- `apply_diagnosis(vault: LoadedVault, repository: Repository, *, attempt: Mapping[str, Any], diagnosis: Mapping[str, Any], session_id: str | None=None, clock: Clock | None=None, judge_factory: ClientFactory | None=None, embedding_factory: ClientFactory | None=None, writer_factory: ClientFactory | None=None, spend: ReviewSpend | None=None, scope_attempt_id: str | None=None, cancelled: Cancelled | None=None, heartbeat: Callable[[], bool] | None=None) -> None` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 1051) — The diagnosis-dependent pipeline steps (§7.2 worker half).
- `record_pattern_verdicts(repository: Repository, *, diagnosis: Mapping[str, Any], attempt_id: str) -> int` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 1149) — Append one ``same_cause`` verdict per validated citation (idempotent).
- `run_embed_job(vault: LoadedVault, repository: Repository, job: Mapping[str, Any], *, embedding_factory: ClientFactory, clock: Clock | None=None) -> JobOutcome` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 1195) — Embed-on-write (S1.4a/b), then the would-merge log.
- `drain(vault: LoadedVault, repository: Repository, *, owner: str='cli', kinds: tuple[str, ...]=(DIAGNOSE_KIND, EMBED_KIND), attempt_id: str | None=None, client_factory: ClientFactory | None=None, embedding_factory: ClientFactory | None=None, judge_factory: ClientFactory | None=None, max_jobs: int=1000, spend: ReviewSpend | None=None, cancelled: Cancelled | None=None, clock: Clock | None=None) -> list[JobOutcome]` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 1255) — Run runnable jobs until none is left (``learnloop diagnose --drain``).
- `command_spend(vault: LoadedVault, caps: SpendCaps, *, price_per_million: float | None=None, cancelled: Cancelled | None=None) -> ReviewSpend` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 1306) — A command's shared budget; its routes are classified from config.
- `plan_diagnosis_jobs(vault: LoadedVault, repository: Repository, *, spend: ReviewSpend, attempt_id: str | None=None, max_jobs: int=1000, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 1489) — What ``drain`` would run now, and its admission estimate (no call, no write).
- `plan_unqueued_diagnosis(vault: LoadedVault, repository: Repository, *, attempt_id: str, spend: ReviewSpend) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 1611) — The one diagnosis call ``retry`` would queue for an attempt not in the queue.
- `plan_embed_jobs(vault: LoadedVault, repository: Repository, *, attempt_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 1652) — Pending embed-on-write work (each job runs under its own embedding caps).

### Module constants

- `LOG` ([src/learnloop/diagnosis/split/jobs.py](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 52)
- `DIAGNOSE_KIND` ([src/learnloop/diagnosis/split/jobs.py](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 54)
- `EMBED_KIND` ([src/learnloop/diagnosis/split/jobs.py](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 55)
- `DIAGNOSE_LEASE_SECONDS` ([src/learnloop/diagnosis/split/jobs.py](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 57)
- `EMBED_LEASE_SECONDS` ([src/learnloop/diagnosis/split/jobs.py](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 58)
- `BACKOFF_BASE_SECONDS` ([src/learnloop/diagnosis/split/jobs.py](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 59)
- `BACKOFF_MAX_SECONDS` ([src/learnloop/diagnosis/split/jobs.py](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 60)
- `NOT_READY_RECHECK_SECONDS` ([src/learnloop/diagnosis/split/jobs.py](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 62)
- `SPLIT_OFF_RECHECK_SECONDS` ([src/learnloop/diagnosis/split/jobs.py](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 63)
- `MODEL_CALL_OWNER_KIND` ([src/learnloop/diagnosis/split/jobs.py](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 64)
- `DIAGNOSIS_ROUTE` ([src/learnloop/diagnosis/split/jobs.py](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 68)
- `LIVE_DIAGNOSIS_CAPS` ([src/learnloop/diagnosis/split/jobs.py](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 79)
- `RETRIEVAL_CAPS` ([src/learnloop/diagnosis/split/jobs.py](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 497)
- `RETRIEVAL_ROUTE` ([src/learnloop/diagnosis/split/jobs.py](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 507)
- `_RETRIEVAL_NOTE` ([src/learnloop/diagnosis/split/jobs.py](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 1483)

### Explicit exports

`__all__` declares:

- `DIAGNOSE_KIND`
- `DIAGNOSIS_ROUTE`
- `LIVE_DIAGNOSIS_CAPS`
- `command_spend`
- `plan_diagnosis_jobs`
- `plan_embed_jobs`
- `plan_unqueued_diagnosis`
- `DONE`
- `EMBED_KIND`
- `FAILED`
- `JobOutcome`
- `NOT_NEEDED`
- `PENDING`
- `apply_diagnosis`
- `record_diagnosis_reads`
- `default_diagnosis_client`
- `default_embedding_client`
- `diagnosis_status`
- `drain`
- `enqueue_diagnosis`
- `enqueue_embed_job`
- `pending_diagnosis_attempts`
- `process_next_job`
- `record_pattern_verdicts`
- `run_diagnose_job`
- `run_embed_job`

## Internal implementation anchors

- `class _LeaseLost(RuntimeError)` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 104) — The job was re-claimed by another worker; publish nothing.
- `_backoff(attempt_count: int, clock: Clock | None) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 248)
- `_later(seconds: float, clock: Clock | None) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 253)
- `_day_start(clock: Clock | None) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 258)
- `_default_judge_factory(vault: LoadedVault) -> ClientFactory` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 346) — The same-cause judge client, resolved only when a pair needs judging.
- `_existing_diagnosis(repository: Repository, job: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 354) — A COMPLETED diagnosis this job already wrote before a crash.
- `_finish(repository: Repository, job: Mapping[str, Any], state: str, *, error: str | None=None, payload: Mapping[str, Any] | None=None, clock: Clock | None=None) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 380)
- `_lease_heartbeat(repository: Repository, job: Mapping[str, Any], clock: Clock | None) -> Callable[[], bool]` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 388) — Renew this worker's diagnose lease for another full term; False once lost.
- `_release(repository: Repository, job: Mapping[str, Any], *, not_before: str, error: str | None, refund: bool, clock: Clock | None) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 405)
- `_persist(repository: Repository, job: Mapping[str, Any], *, diagnosis_id: str, values: dict[str, Any], clock: Clock | None, record: Any=None, forecasts: Callable[[], Any] | None=None) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 413) — Write the diagnosis + receipt only while this worker still owns the job.
- `_receipt_for_storage(outcome: DiagnosisOutcome) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 471)
- `class _NoRegistryIndex` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 510) — Embeddings are on but no client is ready: the exact registry set, recorded (S6).
- `_sum_estimates(*estimates: SpendEstimate) -> SpendEstimate` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 552)
- `_diagnosis_reserve(spend: ReviewSpend, count: int) -> SpendEstimate` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 562) — What ``count`` diagnosis calls need at least: a call each plus its output limit.
- `_remaining_diagnoses_reserve(spend: ReviewSpend, repository: Repository, *, scope_attempt_id: str | None=None) -> Callable[[], SpendEstimate]` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 570) — What a command must keep for the diagnoses still queued after this one.
- `_command_retrieval_guard(spend: ReviewSpend, repository: Repository, *, scope_attempt_id: str | None=None) -> Callable[[str, int], Any]` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 590) — Admit each retrieval embedding request on the command's budget (review F12).
- `_hybrid_retriever(vault: LoadedVault, repository: Repository, embedding_factory: ClientFactory | None, *, spend: ReviewSpend | None=None, scope_attempt_id: str | None=None) -> Any | None` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 617) — The live kNN retriever (S1.4b hybrid index, S1.4a registry shortlist), or None (then hybrid degrades to exact and the registry block is the exact set, S6).
- `_workflow_diagnosis_ended(vault: LoadedVault, repository: Repository, attempt_id: str, mode: str, clock: Clock | None) -> None` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 670) — FG1: a live diagnosis ended, or stays released for a readiness reason: the follow-up workflow that owns the attempt moves on, on its own slot (never in this ordered one).
- `_diagnose(vault: LoadedVault, repository: Repository, job: Mapping[str, Any], attempt: Mapping[str, Any], *, client: Any, mode: str, payload: Mapping[str, Any], embedding_factory: ClientFactory | None, clock: Clock | None, outcome: JobOutcome, spend: ReviewSpend | None=None, scope_attempt_id: str | None=None, cancelled: Cancelled | None=None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 807) — One model call; returns the persisted diagnosis row, or None when released.
- `_superseded(repository: Repository, attempt_id: str, mode: str, payload: Mapping[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 1044)
- `_plan_current(vault: LoadedVault, repository: Repository, attempt: Mapping[str, Any]) -> Any | None` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 1338)
- `_estimated_prompt_tokens(vault: LoadedVault, current: Any, *, store: Any) -> int` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 1344) — The diagnosis prompt's token estimate, assembled offline (no call).
- `_estimated_retrieval(vault: LoadedVault, repository: Repository, current: Any, *, store: Any, seen: set[tuple[str, str, str]]) -> tuple[int, int]` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 1358) — One diagnosis's retrieval embedding requests and input tokens (an upper bound).
- `_retrieval_plan(spend: ReviewSpend, diagnosis_estimate: SpendEstimate, *, calls: int, input_tokens: int) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 1379) — The retrieval half of a plan: its estimate and whether it fits beside the diagnoses.
- `_recurrence_plan(vault: LoadedVault, spend: ReviewSpend, diagnosis_estimate: SpendEstimate, *, jobs: int) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/split/jobs.py), line 1407) — Slice 2 T1's work inside the planned diagnose jobs, on the same caps.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `DIAGNOSE_KIND`, `LIVE_DIAGNOSIS_CAPS`, `NOT_NEEDED`, `diagnosis_status`, `drain`; statically calls `diagnosis_status`, `drain`
- [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]] — imports `DIAGNOSE_KIND`, `EMBED_KIND`, `command_spend`, `diagnosis_status`, `drain`, `enqueue_diagnosis`, `plan_diagnosis_jobs`, `plan_embed_jobs`, `plan_unqueued_diagnosis`; statically calls `command_spend`, `diagnosis_status`, `drain`, `enqueue_diagnosis`, `plan_diagnosis_jobs`, `plan_embed_jobs`, `plan_unqueued_diagnosis`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `enqueue_diagnosis`; statically calls `enqueue_diagnosis`
- [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]] — imports `enqueue_diagnosis`; statically calls `enqueue_diagnosis`
- [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]] — imports `default_embedding_client`; statically calls `default_embedding_client`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `register_retrieval_route`; statically calls `register_retrieval_route`
- [[Reference/Modules/learnloop/diagnosis/split/card|learnloop.diagnosis.split.card]] — imports `DONE`, `diagnosis_status`; statically calls `diagnosis_status`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] — imports `register_retrieval_route`; statically calls `register_retrieval_route`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]] — imports `default_embedding_client`; statically calls `default_embedding_client`
- [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] — imports `DONE`, `PENDING`, `diagnosis_status`; statically calls `diagnosis_status`
- [[Reference/Modules/learnloop/followup_run/marks|learnloop.followup_run.marks]] — imports `diagnosis_status`; statically calls `diagnosis_status`
- [[Reference/Modules/learnloop/followup_run/serving|learnloop.followup_run.serving]] — imports `PENDING`, `diagnosis_status`; statically calls `diagnosis_status`
- [[Reference/Modules/learnloop/learner_context|learnloop.learner_context]] — imports `DONE`, `diagnosis_status`; statically calls `diagnosis_status`
- [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]] — imports `DIAGNOSE_KIND`, `DONE`, `NOT_NEEDED`, `diagnosis_status`, `drain`; statically calls `diagnosis_status`, `drain`
- [[Reference/Modules/learnloop_sidecar/handlers/diagnosis_card|learnloop_sidecar.handlers.diagnosis_card]] — imports `DONE`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `NOT_NEEDED`, `diagnosis_status`; statically calls `diagnosis_status`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `session_diagnosis_availability`; statically calls `session_diagnosis_availability`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `NOT_NEEDED`, `diagnosis_status`; statically calls `diagnosis_status`
- [[Reference/Modules/learnloop_sidecar/post_attempt_worker|learnloop_sidecar.post_attempt_worker]] — imports `process_next_job`; statically calls `process_next_job`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`, `record_model_calls`; calls `content_key`, `record_model_calls`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/runs|learnloop.ai.runs]] — imports `finish_agent_run`; calls `finish_agent_run`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; calls `SpendBudget`, `SpendCaps`, `SpendEstimate`
- [[Reference/Modules/learnloop/attempts/blind_grading|learnloop.attempts.blind_grading]] — imports `split_grading_active`; calls `split_grading_active`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `resolved_rubric`; calls `resolved_rubric`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`, `utc_now_iso`; calls `SystemClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/write_provenance|learnloop.db.stores.write_provenance]] — imports `WriteRecord`, `record_text_write`; calls `record_text_write`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `run_post_diagnosis_hooks`; calls `run_post_diagnosis_hooks`
- [[Reference/Modules/learnloop/diagnosis/forecast_receipts|learnloop.diagnosis.forecast_receipts]] — imports `record_diagnosis_forecasts`; calls `record_diagnosis_forecasts`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `normalize_and_resolve_attempt`; calls `normalize_and_resolve_attempt`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `route_profiles`; calls `route_profiles`
- [[Reference/Modules/learnloop/diagnosis/offline_review/spend|learnloop.diagnosis.offline_review.spend]] — imports `KNOWN_PRICES_PER_MILLION`, `ReviewSpend`, `RouteInfo`; calls `ReviewSpend`, `RouteInfo`
- [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]] — imports `route_profile`; calls `route_profile`
- [[Reference/Modules/learnloop/diagnosis/recurrence/escalation|learnloop.diagnosis.recurrence.escalation]] — imports `ESCALATION_REPAIR_PROMPT_TOKENS`, `ESCALATION_REPAIR_ROUTE`
- [[Reference/Modules/learnloop/diagnosis/recurrence/kind|learnloop.diagnosis.recurrence.kind]] — imports `SAME_CAUSE_ROUTE`
- [[Reference/Modules/learnloop/diagnosis/recurrence/live|learnloop.diagnosis.recurrence.live]] — imports `PLANNED_EMBED_TOKENS_PER_JOB`, `PLANNED_JUDGE_PROMPT_TOKENS`, `default_live_judge_factory`, `record_escalation`, `recurrence_step`; calls `default_live_judge_factory`, `record_escalation`, `recurrence_step`
- [[Reference/Modules/learnloop/diagnosis/split/context|learnloop.diagnosis.split.context]] — imports `RegistryShortlist`, `assemble_diagnosis_context`; calls `RegistryShortlist`, `assemble_diagnosis_context`
- [[Reference/Modules/learnloop/diagnosis/split/contract|learnloop.diagnosis.split.contract]] — imports `diagnosis_prompt`; calls `diagnosis_prompt`
- [[Reference/Modules/learnloop/diagnosis/split/diagnoser|learnloop.diagnosis.split.diagnoser]] — imports `DiagnosisOutcome`, `run_diagnosis`; calls `DiagnosisOutcome`, `run_diagnosis`
- [[Reference/Modules/learnloop/diagnosis/split/embeddings|learnloop.diagnosis.split.embeddings]] — imports `LIVE_CAPS`, `PRICES_PER_MILLION`, `divergence_records`, `embed_records`, `hypothesis_records`, `misconception_records`, `pending_records`, `record_would_merge`; calls `divergence_records`, `embed_records`, `hypothesis_records`, `misconception_records`, `pending_records`, `record_would_merge`
- [[Reference/Modules/learnloop/diagnosis/split/figure_trace|learnloop.diagnosis.split.figure_trace]] — imports `SUFFIX`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `build_causal_view`, `current_attempt_for`, `joint_grade_record`, `live_history_store`, `needs_diagnosis`, `sampled_correct_answer`, `settings_from_config`; calls `build_causal_view`, `current_attempt_for`, `joint_grade_record`, `live_history_store`, `needs_diagnosis`, `sampled_correct_answer`, `settings_from_config`
- [[Reference/Modules/learnloop/diagnosis/split/prior_analysis|learnloop.diagnosis.split.prior_analysis]] — imports `module`; calls `for_attempt`
- [[Reference/Modules/learnloop/diagnosis/split/provenance|learnloop.diagnosis.split.provenance]] — imports `NOT_FROZEN`, `diagnosis_record`; calls `diagnosis_record`
- [[Reference/Modules/learnloop/diagnosis/split/retrieval|learnloop.diagnosis.split.retrieval]] — imports `EmbeddingHistoryRetriever`, `planned_retrieval_requests`; calls `EmbeddingHistoryRetriever`, `planned_retrieval_requests`
- [[Reference/Modules/learnloop/diagnosis/split/settings|learnloop.diagnosis.split.settings]] — imports `DIAGNOSIS_PROMPT_VERSION`
- [[Reference/Modules/learnloop/diagnosis/split/workbench_trace|learnloop.diagnosis.split.workbench_trace]] — imports `SUFFIX`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `enqueue_after_diagnosis`; calls `enqueue_after_diagnosis`
- [[Reference/Modules/learnloop/followup_serve/workflow|learnloop.followup_serve.workflow]] — imports `diagnosis_ended`; calls `diagnosis_ended`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `project_canonical_facet_state`; calls `project_canonical_facet_state`
- [[Reference/Modules/learnloop/substrate/recurrence_groups|learnloop.substrate.recurrence_groups]] — imports `claim_for_citation`, `recurrence_active`; calls `claim_for_citation`, `recurrence_active`
- [[Reference/Modules/learnloop/symbolic_view|learnloop.symbolic_view]] — imports `switch_now`, `trace_view`; calls `switch_now`, `trace_view`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `dataclasses`, `datetime`, `logging`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]], [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]], [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]], [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]] and 14 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/split_live_helpers.py](../../../../../../../tests/split_live_helpers.py) — direct import
- [tests/test_active_errors_overlay.py](../../../../../../../tests/test_active_errors_overlay.py) — direct import
  - `test_overlaid_read_carries_the_diagnosers_statement_and_verdict`
  - `test_tui_error_attributions_are_not_rerendered_when_no_diagnosis_is_needed`
  - `test_tui_error_attributions_show_the_diagnosers_statement_once_diagnosed`
- [tests/test_chatgpt_plan_landing.py](../../../../../../../tests/test_chatgpt_plan_landing.py) — direct import
  - `test_a_snapshot_diagnosis_on_the_plan_records_what_it_served_with_its_row_and_forecasts`
- [tests/test_diagnosis_input_provenance.py](../../../../../../../tests/test_diagnosis_input_provenance.py) — direct import
  - `test_old_rows_stay_held_back_and_a_re_diagnosis_writes_recorded_ones`
  - `test_rereview_f3_a_regrade_after_the_job_captured_its_gradings_is_unaccountable`
- [tests/test_diagnosis_input_provenance_landing.py](../../../../../../../tests/test_diagnosis_input_provenance_landing.py) — direct import
- [tests/test_diagnosis_pipeline.py](../../../../../../../tests/test_diagnosis_pipeline.py) — direct import
  - `test_a_joint_attempt_regraded_in_a_split_vault_is_graded_blind_and_isolated`
  - `test_a_self_graded_fallback_is_regraded_blind_and_queues_its_diagnosis`
  - `test_blind_grade_carries_no_causal_fields_and_queues_a_diagnosis`
  - `test_blind_regrade_supersedes_the_record_and_rediagnoses`
  - `test_correct_answer_needs_no_diagnosis`
  - `test_correct_answers_are_sampled_in_shadow_only`
  - `test_diagnosis_materializes_hypotheses_from_the_diagnosis`
  - `test_failed_diagnosis_backs_off_then_fails_and_leaves_the_grade`
  - `test_kill_switch_holds_queued_live_diagnoses`
  - `test_regrade_to_full_marks_retires_the_diagnosis`
  - `test_resume_after_a_crash_between_diagnosis_and_settle_makes_no_second_call`
  - `test_shadow_diagnosis_on_a_joint_vault_changes_nothing_live`
  - `test_the_accessor_and_the_overlays_agree_on_the_diagnosis_in_force`
- [tests/test_diagnosis_reports.py](../../../../../../../tests/test_diagnosis_reports.py) — direct import
  - `test_a_cancelled_job_is_released_unspent`
- [tests/test_followup_fg1d_probe_shadow.py](../../../../../../../tests/test_followup_fg1d_probe_shadow.py) — direct import
  - `test_the_diagnosis_job_after_the_answer_changes_nothing_further`
- [tests/test_followup_next_matrix.py](../../../../../../../tests/test_followup_next_matrix.py) — direct import
- [tests/test_followup_rival_factor.py](../../../../../../../tests/test_followup_rival_factor.py) — direct import
- [tests/test_forecast_receipts.py](../../../../../../../tests/test_forecast_receipts.py) — direct import
  - `test_a_completed_diagnosis_writes_its_forecast_in_its_own_transaction`
  - `test_replay_neither_reads_nor_writes_forecast_receipts`
- [tests/test_forecast_receipts_landing.py](../../../../../../../tests/test_forecast_receipts_landing.py) — direct import
  - `test_the_provenance_record_the_diagnosis_and_its_forecasts_commit_as_one_transaction`
- [tests/test_held_grade_composition.py](../../../../../../../tests/test_held_grade_composition.py) — direct import
  - `test_a_held_attempt_queues_no_gap_reading_as_a_failure`
- [tests/test_held_grade_evidence.py](../../../../../../../tests/test_held_grade_evidence.py) — direct import
  - `test_f1_live_a_blank_criterion_id_keeps_no_shortfall_and_queues_no_diagnosis`
  - `test_f2_a_regrade_that_validates_nothing_keeps_the_hold`
- [tests/test_mobile_v3_codex_review.py](../../../../../../../tests/test_mobile_v3_codex_review.py) — direct import
- [tests/test_mobile_v3_probes.py](../../../../../../../tests/test_mobile_v3_probes.py) — direct import
- [tests/test_pfc_unverified_unassessed.py](../../../../../../../tests/test_pfc_unverified_unassessed.py) — direct import
  - `test_a_complement_route_is_graded_on_its_assessed_criteria_only`
  - `test_a_regrade_applies_the_same_rule`
  - `test_an_attempt_with_no_assessed_criterion_schedules_as_correct_and_is_no_evidence`
- [tests/test_placement_diagnosis_decides.py](../../../../../../../tests/test_placement_diagnosis_decides.py) — direct import
  - `test_a_decided_miss_is_not_reopened_by_a_retry`
  - `test_a_miss_decided_before_the_hold_keeps_its_diagnosis`
- [tests/test_post_attempt_worker.py](../../../../../../../tests/test_post_attempt_worker.py) — direct import
  - `test_a_submission_committed_while_the_worker_projects_is_never_overwritten`
  - `test_an_older_job_queued_during_a_live_lease_is_never_leased_concurrently`
  - `test_provider_not_ready_keeps_the_job_queued_without_spending_an_attempt`
  - `test_worker_thread_drains_in_order_and_records_receipts`
- [tests/test_reader_cues.py](../../../../../../../tests/test_reader_cues.py) — direct import
  - `test_a_split_cue_names_the_diagnosers_statement_as_the_rail_does`
- [tests/test_reader_guidance.py](../../../../../../../tests/test_reader_guidance.py) — direct import
  - `test_split_guide_falls_back_to_the_error_type_when_the_diagnosis_failed`
  - `test_split_guide_falls_back_to_the_error_type_while_the_diagnosis_is_pending`
  - `test_split_guide_plan_names_the_pending_diagnosis_until_it_lands`
  - `test_split_guide_plan_waits_on_nothing_once_the_diagnosis_failed`
  - `test_split_guide_plan_waits_only_on_diagnoses_behind_its_passages`
  - `test_split_guide_reason_names_the_diagnosers_statement`
- [tests/test_reader_rw2b_fix15.py](../../../../../../../tests/test_reader_rw2b_fix15.py) — direct import
  - `test_item2_a_switch_off_during_context_assembly_masks_the_rendered_trace`
- [tests/test_recurrence_live.py](../../../../../../../tests/test_recurrence_live.py) — direct import
  - `test_a_cancelled_command_stops_the_judge`
  - `test_a_hidden_escalation_card_plans_no_escalated_repair`
  - `test_a_lost_lease_stops_the_t1_calls_of_the_old_worker`
  - `test_an_exhausted_command_budget_stops_the_judge`
  - `test_slow_judging_renews_the_lease_so_no_second_worker_repeats_the_paid_repair`
  - `test_the_dry_run_plans_the_recurrence_work_on_the_same_caps`
  - `test_the_judge_runs_on_the_commands_budget_and_shows_in_its_summary`
- [tests/test_recurrence_merge_composition.py](../../../../../../../tests/test_recurrence_merge_composition.py) — direct import
  - `test_an_unassessed_only_answer_is_never_a_recurrence`
- [tests/test_required_method_grading.py](../../../../../../../tests/test_required_method_grading.py) — direct import
  - `test_live_another_route_fails_the_method_criterion_with_no_quote`
- [tests/test_route_rules_in_grader.py](../../../../../../../tests/test_route_rules_in_grader.py) — direct import
  - `test_f1_live_an_incomplete_grade_with_nothing_located_is_held`
  - `test_live_nothing_located_and_nothing_validated_is_held`
- [tests/test_stuck_prompt.py](../../../../../../../tests/test_stuck_prompt.py) — direct import
  - `test_a_partial_stuck_answer_is_graded_blind_at_standard_mass_and_diagnosed`
  - `test_an_empty_stuck_answer_scores_zero_without_a_model_call`

## Modification guidance

- Change jobs policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/split/jobs.py](../../../../../../../src/learnloop/diagnosis/split/jobs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
