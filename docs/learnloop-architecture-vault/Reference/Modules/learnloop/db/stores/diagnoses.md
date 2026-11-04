---
title: "learnloop.db.stores.diagnoses"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/diagnoses.py"
source_paths:
  - "src/learnloop/db/stores/diagnoses.py"
source_commit: "8e529218954fcf26cc284a07612cf76f2f430d67"
source_commit_timestamp: "2026-10-16T10:17:46-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.stores.diagnoses module"
  - "src/learnloop/db/stores/diagnoses.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.diagnoses`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.diagnoses` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Slice 1 M2 persistence: blind grades, diagnoses, card taps and the job queue.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/diagnoses.py](../../../../../../../src/learnloop/db/stores/diagnoses.py) |
| Source lines | 988 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `8e529218954fcf26cc284a07612cf76f2f430d67` |
| Commit timestamp | `2026-10-16T10:17:46-04:00` |

## Public API

- `merge_causal_view_into_events(events: Sequence[Mapping[str, Any]], view: Mapping[str, Any] | None, *, diagnosis_id: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/diagnoses.py), line 46) — Error events with a diagnosis's causal fields laid over them.
- `merge_causal_view_into_feedback(metadata: Mapping[str, Any] | None, view: Mapping[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/diagnoses.py), line 77) — Feedback metadata whose repair suggestions come from the diagnosis.
- `class DiagnosisStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/diagnoses.py), line 95) — Repository mixin; every method opens (or joins) one connection scope.
  - `insert_blind_grade_record(self, *, attempt_id: str, agent_run_id: str | None, grading_prompt_version: str, output_schema_version: str, context_hash: str, record: Mapping[str, Any], supersedes_id: str | None=None, queue_diagnosis: bool | None=None, clock: Clock | None=None) -> str` (line 100; public) — Append a blind grade; a regrade's record also queues the diagnosis.
  - `_decode_blind_record(row: Any) -> dict[str, Any]` (line 160; internal)
  - `latest_blind_grade_record(self, attempt_id: str) -> dict[str, Any] | None` (line 165; public)
  - `blind_record_max_points(self, attempt_id: str, agent_run_ids: Iterable[str]) -> int | None` (line 178; public) — The maximum a grading recorded WITH its grade: the ``max_points`` of the attempt's latest blind record written by one of ``agent_run_ids`` (the runs of one grading epoch), or None.
  - `blind_graded_attempt_ids(self) -> set[str]` (line 205; public)
  - `latest_blind_grade_records(self) -> dict[str, dict[str, Any]]` (line 214; public) — attempt id -> its latest blind record (one ordered scan).
  - `insert_attempt_diagnosis(self, *, attempt_id: str, diagnosis_prompt_version: str, mode: str, history_mode: str, status: str, proposal: Mapping[str, Any] | None, causal_view: Mapping[str, Any] | None, validation_report: Mapping[str, Any] | None, receipt: Mapping[str, Any] | None, blind_grade_record_id: str | None=None, agent_run_id: str | None=None, provider: str | None=None, model: str | None=None, error: str | None=None, latency_seconds: float | None=None, supersedes_id: str | None=None, diagnosis_id: str | None=None, clock: Clock | None=None) -> str` (line 222; public) — Append one diagnosis and (when given) its context receipt together.
  - `_decode_diagnosis(row: Any) -> dict[str, Any]` (line 295; internal)
  - `attempt_diagnoses_for_attempt(self, attempt_id: str) -> list[dict[str, Any]]` (line 302; public)
  - `attempt_diagnosis(self, diagnosis_id: str) -> dict[str, Any] | None` (line 312; public)
  - `latest_attempt_diagnosis(self, attempt_id: str, *, mode: str='live', statuses: Iterable[str] | None=None) -> dict[str, Any] | None` (line 319; public)
  - `_diagnosis_in_force(status: Any, record_id: Any, current_record_id: str | None) -> bool` (line 336; internal) — THE eligibility rule for a live diagnosis (one rule for every reader).
  - `_diagnosis_concerns_grade(record_id: Any, current_record_id: str | None) -> bool` (line 351; internal) — Whether a diagnosis row read the blind grade ``current_record_id`` (the half of :meth:`_diagnosis_in_force` that does not look at status).
  - `current_live_diagnosis(self, attempt_id: str) -> dict[str, Any] | None` (line 359; public) — The live diagnosis in force for an attempt, decoded, or None.
  - `_live_views(self, connection: Any, attempt_ids: Sequence[str] | None) -> dict[str, tuple[str, dict[str, Any]]]` (line 388; internal) — The causal view in force per attempt (:meth:`_diagnosis_in_force`).
  - `live_causal_view(self, attempt_id: str) -> tuple[str, dict[str, Any]] | None` (line 423; public) — (diagnosis id, causal view) of the latest completed live diagnosis.
  - `live_causal_views(self, attempt_ids: Iterable[str] | None=None) -> dict[str, tuple[str, dict[str, Any]]]` (line 431; public) — (diagnosis id, causal view) in force per attempt: for every attempt, or only for ``attempt_ids`` (batched: one diagnoses read and one blind-grade read for the whole batch, not one pair per attempt).
  - `pending_live_diagnoses_for_active_errors(self, learning_object_ids: Iterable[str]) -> list[str]` (line 446; public) — Attempts behind these LOs' active error events whose live diagnosis is pending.
  - `diagnosis_context_receipt(self, diagnosis_id: str) -> dict[str, Any] | None` (line 477; public)
  - `diagnosis_calls_since(self, since_iso: str) -> int` (line 499; public) — Diagnoser calls ADMITTED since ``since_iso``, failures included.
  - `all_attempt_diagnoses(self) -> list[dict[str, Any]]` (line 518; public)
  - `insert_diagnosis_feedback(self, *, diagnosis_id: str, attempt_id: str, response: str, cited_attempt_id: str | None=None, forwarded_factor_id: str | None=None, shown_at: str | None=None, clock: Clock | None=None) -> str` (line 527; public)
  - `diagnosis_feedback_rows(self, diagnosis_id: str | None=None) -> list[dict[str, Any]]` (line 553; public)
  - `insert_would_merge(self, *, diagnosis_id: str | None, hypothesis_id: str, model_id: str, exact_key: str, exact_group_ids: Sequence[str], neighbors: Sequence[Mapping[str, Any]], clock: Clock | None=None) -> str | None` (line 568; public)
  - `would_merge_rows(self) -> list[dict[str, Any]]` (line 595; public)
  - `insert_diagnosis_wait_receipt(self, *, session_id: str | None, pending_attempt_ids: Sequence[str], waited_seconds: float, served_without_diagnosis: bool, clock: Clock | None=None) -> str` (line 608; public)
  - `diagnosis_wait_receipts(self) -> list[dict[str, Any]]` (line 633; public)
  - `_decode_job(row: Any) -> dict[str, Any]` (line 649; internal)
  - `enqueue_post_attempt_job(self, *, attempt_id: str, kind: str, job_key: str, attempt_completed_at: str, payload: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str | None` (line 654; public) — Insert a queued job once per ``(kind, job_key)``; returns its id when new.
  - `post_attempt_job(self, job_id: str) -> dict[str, Any] | None` (line 682; public)
  - `post_attempt_jobs(self, *, attempt_id: str | None=None, kind: str | None=None, states: Iterable[str] | None=None) -> list[dict[str, Any]]` (line 689; public)
  - `lease_next_post_attempt_job(self, *, kind: str, owner: str, lease_seconds: float, clock: Clock | None=None, attempt_id: str | None=None) -> dict[str, Any] | None` (line 719; public) — Claim the next runnable job, or None.
  - `renew_post_attempt_lease(self, job_id: str, *, epoch: int, lease_seconds: float, clock: Clock | None=None) -> bool` (line 793; public)
  - `owns_post_attempt_job(self, job_id: str, *, epoch: int) -> bool` (line 807; public)
  - `finish_post_attempt_job(self, job_id: str, *, epoch: int, state: str, last_error: str | None=None, payload: Mapping[str, Any] | None=None, clock: Clock | None=None) -> bool` (line 815; public) — Settle a leased job; a superseded lease writes nothing (fencing).
  - `release_post_attempt_job(self, job_id: str, *, epoch: int, not_before: str | None, last_error: str | None=None, refund_attempt: bool=False, clock: Clock | None=None) -> bool` (line 844; public) — Return a leased job to the queue (backoff, or provider not ready).
  - `hold_queued_live_diagnoses(self, *, clock: Clock | None=None) -> int` (line 868; public) — Stamp each queued LIVE diagnose job ``payload.split_held_at = now``.
  - `requeue_post_attempt_job(self, job_id: str, *, clock: Clock | None=None) -> bool` (line 902; public) — Owner retry: a settled job runs again with a fresh attempt count.
  - `pending_live_diagnoses_for_session(self, session_id: str) -> list[str]` (line 917; public) — Attempts of this session whose LIVE diagnosis is queued or running.
  - `live_diagnosis_jobs_for_session(self, session_id: str) -> list[dict[str, Any]]` (line 934; public) — Every LIVE diagnose job of this session's attempts, any state (E7 population).
  - `post_attempt_job_counts(self) -> dict[str, dict[str, int]]` (line 950; public)
- `latest_blind_grade_rows(connection: Any) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/diagnoses.py), line 968) — attempt id -> its latest blind record, on the caller's connection (one ordered scan; a caller can read it in the same snapshot as other rows).

### Module constants

- `_EVENT_VIEW_KEYS` ([src/learnloop/db/stores/diagnoses.py](../../../../../../../src/learnloop/db/stores/diagnoses.py), line 22)

### Explicit exports

`__all__` declares:

- `DiagnosisStoreMixin`
- `latest_blind_grade_rows`
- `merge_causal_view_into_events`
- `merge_causal_view_into_feedback`

## Internal implementation anchors

- `_dumps(value: Any) -> str` ([source](../../../../../../../src/learnloop/db/stores/diagnoses.py), line 31)
- `_loads(value: Any, default: Any) -> Any` ([source](../../../../../../../src/learnloop/db/stores/diagnoses.py), line 35)
- `_has_table(connection: Any, name: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/diagnoses.py), line 962)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `DiagnosisStoreMixin`, `merge_causal_view_into_events`, `merge_causal_view_into_feedback`; statically calls `merge_causal_view_into_events`, `merge_causal_view_into_feedback`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `latest_blind_grade_rows`; statically calls `latest_blind_grade_rows`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/ad23_fakes.py](../../../../../../../tests/ad23_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/ad_ingest_fakes.py](../../../../../../../tests/ad_ingest_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/approach_map_fakes.py](../../../../../../../tests/approach_map_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/daily_plan_fakes.py](../../../../../../../tests/daily_plan_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/deliverable_fixtures.py](../../../../../../../tests/deliverable_fixtures.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/diagnosis_split_helpers.py](../../../../../../../tests/diagnosis_split_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/e0_fakes.py](../../../../../../../tests/e0_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/exam_scope_fixtures.py](../../../../../../../tests/exam_scope_fixtures.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/followup_serve_helpers.py](../../../../../../../tests/followup_serve_helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/helpers.py](../../../../../../../tests/helpers.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/hint_fakes.py](../../../../../../../tests/hint_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]
- [tests/intent_fakes.py](../../../../../../../tests/intent_fakes.py) — imports consumer [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/diagnoses.py](../../../../../../../src/learnloop/db/stores/diagnoses.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
