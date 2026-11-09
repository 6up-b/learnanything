---
title: "learnloop.capture.jobs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/capture/jobs.py"
source_paths:
  - "src/learnloop/capture/jobs.py"
source_commit: "38ccfa65f8d3889cdb161cd5db0cea3a5d0582f0"
source_commit_timestamp: "2026-11-09T06:12:48-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.capture"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.capture.jobs module"
  - "src/learnloop/capture/jobs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-capture"
---

# `learnloop.capture.jobs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.capture.jobs` exists within [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] to own the behavior summarized by its module contract: Accepted jobs for the phone's long mutations (mobile spec §6.3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/capture/jobs.py](../../../../../../src/learnloop/capture/jobs.py) |
| Source lines | 251 |
| Owning package | [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `38ccfa65f8d3889cdb161cd5db0cea3a5d0582f0` |
| Commit timestamp | `2026-11-09T06:12:48-05:00` |

## Public API

- `recorded_error(attempt: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/capture/jobs.py), line 44) — What a recorded submit says, in ``CommandError``'s four fields.
- `get_job(repo: Repository, job_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/capture/jobs.py), line 54)
- `job_for_request(repo: Repository, request_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/capture/jobs.py), line 60) — The newest job for a request id, whichever device made it (reads are unrestricted, §6.5).
- `accept_job(repo: Repository, *, device_id: str, request_id: str, method: str, params: dict[str, Any], params_sha256: str, boot_id: str, check_new: Callable[[], None] | None=None, now: datetime | None=None) -> tuple[dict[str, Any], bool]` ([source](../../../../../../src/learnloop/capture/jobs.py), line 71) — ``(job, enqueue)``, committed before the host answers (§6.3).
- `submission_in_flight(repo: Repository, practice_item_id: str) -> bool` ([source](../../../../../../src/learnloop/capture/jobs.py), line 128) — A phone's answer to ``practice_item_id`` accepted and not yet finished (mobile v2 V3; Codex review of V3, F2).
- `start_job(repo: Repository, job_id: str, *, now: datetime | None=None) -> None` ([source](../../../../../../src/learnloop/capture/jobs.py), line 147)
- `finish_job(repo: Repository, job_id: str, *, result: Any=None, error: dict[str, Any] | None=None, state: str | None=None, now: datetime | None=None) -> None` ([source](../../../../../../src/learnloop/capture/jobs.py), line 155) — ``state`` is only for :data:`RECORDED`, which carries an error and is no failure.
- `job_receipt(connection: Any, job_id: str) -> Any` ([source](../../../../../../src/learnloop/capture/jobs.py), line 175) — Mobile v2 V4 (Codex review F5): the result an open job's handler already committed, or None.
- `write_job_receipt(connection: Any, job_id: str, result: Any) -> None` ([source](../../../../../../src/learnloop/capture/jobs.py), line 189) — The handler's result on its open job's row, in the handler's transaction (see :func:`job_receipt`).
- `recover_jobs(repo: Repository, boot_id: str, *, now: datetime | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/capture/jobs.py), line 199) — What a starting host owes (§6.3): the jobs another run left open, to run again.

### Module constants

- `RECORDED` ([src/learnloop/capture/jobs.py](../../../../../../src/learnloop/capture/jobs.py), line 25)
- `OPEN_STATES` ([src/learnloop/capture/jobs.py](../../../../../../src/learnloop/capture/jobs.py), line 26)
- `SUBMIT_METHODS` ([src/learnloop/capture/jobs.py](../../../../../../src/learnloop/capture/jobs.py), line 27)
- `SUBMISSION_COMMITTED` ([src/learnloop/capture/jobs.py](../../../../../../src/learnloop/capture/jobs.py), line 29)
- `MAX_BOOTS` ([src/learnloop/capture/jobs.py](../../../../../../src/learnloop/capture/jobs.py), line 31)
- `HOST_RESTART_EXHAUSTED` ([src/learnloop/capture/jobs.py](../../../../../../src/learnloop/capture/jobs.py), line 32)

## Internal implementation anchors

- `_row(row: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/capture/jobs.py), line 35)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]] — imports `ACCEPTED`, `COMPLETED`, `FAILED`, `MAX_BOOTS`, `RECORDED`, `RUNNING`, `SUBMISSION_COMMITTED`, `SUBMIT_METHODS`, `accept_job`, `finish_job`, `get_job`, `job_for_request`, `recorded_error`, `recover_jobs`, `start_job`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `submission_in_flight`; statically calls `submission_in_flight`
- [[Reference/Modules/learnloop_sidecar/phone_reader|learnloop_sidecar.phone_reader]] — imports `job_receipt`, `write_job_receipt`; statically calls `job_receipt`, `write_job_receipt`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/capture/devices|learnloop.capture.devices]] — imports `_now`; calls `_now`
- [[Reference/Modules/learnloop/capture/errors|learnloop.capture.errors]] — imports `CaptureError`; calls `CaptureError`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]], [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]], [[Reference/Modules/learnloop_sidecar/phone_reader|learnloop_sidecar.phone_reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_re0_capture.py](../../../../../../tests/test_re0_capture.py) — direct import
  - `test_an_unchanged_retry_accepted_before_re0_is_not_a_conflict`

## Modification guidance

- Make changes here when the responsibility remains jobs within learnloop.capture; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/capture/jobs.py](../../../../../../src/learnloop/capture/jobs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
