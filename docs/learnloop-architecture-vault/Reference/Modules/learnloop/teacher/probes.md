---
title: "learnloop.teacher.probes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/probes.py"
source_paths:
  - "src/learnloop/teacher/probes.py"
source_commit: "6cad8141ecef068e53fce83d54802d5a726e0b95"
source_commit_timestamp: "2026-11-06T08:54:29-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.teacher"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.teacher.probes module"
  - "src/learnloop/teacher/probes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-teacher"
---

# `learnloop.teacher.probes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.probes` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: Teacher TE2: probes inside a lesson (spec_teacher_v1 rev 5 §11.3, §9 ``serve_probe``, §9.1, §11.9, §18.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/probes.py](../../../../../../src/learnloop/teacher/probes.py) |
| Source lines | 501 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `6cad8141ecef068e53fce83d54802d5a726e0b95` |
| Commit timestamp | `2026-11-06T08:54:29-05:00` |

## Public API

- `class Probe` ([source](../../../../../../src/learnloop/teacher/probes.py), line 58) — One probe of a lesson, read back from its ledger.
  - `unanswered(self) -> bool` (line 75; public)
- `probes(turns: Sequence[Mapping[str, Any]]) -> list[Probe]` ([source](../../../../../../src/learnloop/teacher/probes.py), line 79) — Every probe of a lesson, in request order, with its current status.
- `unanswered(turns: Sequence[Mapping[str, Any]]) -> Probe | None` ([source](../../../../../../src/learnloop/teacher/probes.py), line 109)
- `open_probe(turns: Sequence[Mapping[str, Any]]) -> Probe | None` ([source](../../../../../../src/learnloop/teacher/probes.py), line 113) — The probe being answered (served, no answer yet): the teacher is silent until its grade is back.
- `contract_problem(vault: Any, state: Any, turn_obj: Any, index: int, request: Any) -> str | None` ([source](../../../../../../src/learnloop/teacher/probes.py), line 124) — A correctable problem with a ``serve_probe`` request, named by location (never by text), or None.
- `logged_fields(turn_obj: Any) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/teacher/probes.py), line 149) — ``(location, text)`` of a TE2 request's words a ledger entry or a row keeps: a probe's readings and node, a gap's words and ref.
- `request(vault: Any, repository: Any, state: Any, turn_obj: Any, req: Any, *, append: Callable[..., Any], effect_refs: Mapping[str, Any] | None, family: str, prompt: str, doctrine: str, model: str | None, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/probes.py), line 166) — The probe's request: the ledger entry, the forecast receipt (before any serve), the generation job and the episode row, in the caller's transaction.
- `pending_request(repository: Any, lesson_id: str, node_id: str) -> tuple[dict[str, Any] | None, Probe | None]` ([source](../../../../../../src/learnloop/teacher/probes.py), line 226) — The lesson and its probe on ``node_id`` (the worker's read), or Nones.
- `record_ready(vault: Any, repository: Any, *, lesson_id: str, node_id: str, item_id: str, receipt: Mapping[str, Any], clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/teacher/probes.py), line 233) — The generated question is admitted: its ``probe_ready`` entry with the admission receipt.
- `record_refused(vault: Any, repository: Any, *, lesson_id: str, node_id: str, reason: str, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/teacher/probes.py), line 254) — No question passed: the ``probe_refused`` entry and its episode closed ``refused`` with the reason.
- `serve(vault: Any, repository: Any, lesson: Mapping[str, Any], turns: Sequence[Mapping[str, Any]], *, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/teacher/probes.py), line 293) — The question the screen may show now: a served probe again (the same administration), or a ready one served now (FG1's atomic first-serve claim, surface ``lesson``, and its ``probe_served`` entry, before any text leaves).
- `retire(vault: Any, repository: Any, lesson: Mapping[str, Any], turns: Sequence[Mapping[str, Any]], probe: Probe, *, reason: str, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/teacher/probes.py), line 333) — Retire an unanswered probe unused ("Teach it anyway", the lesson's close, an unservable item): its queued job is skipped, a generated item retired (FG1's ledger: no door opens it again), a ``probe_retired`` entry, and its episode closed ``retired``.
- `record_answer(vault: Any, repository: Any, lesson: Mapping[str, Any], probe: Probe, *, answer: str | None, tap: int | None, grading_client: Any, grading_source: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/probes.py), line 372) — The learner's answer to the open probe: blind-graded (the answer only), one ``diagnostic_probe`` attempt at full evidence through the attempts path, its independence from the reveal ledger's topic-wide check (carried into the attempt's activity class), the item retired (never se…
- `finish_recorded(vault: Any, repository: Any, lesson: Mapping[str, Any], turns: Sequence[Mapping[str, Any]], *, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/teacher/probes.py), line 452) — The view's recovery (no model call): a served probe whose attempt is already recorded but whose result is not (an interrupted write before Codex review F3's one transaction) is finished from the stored attempt, so its result reaches the feed and the teacher (``probe_result`` is…
- `transcript_entry(entry: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/teacher/probes.py), line 469) — A probe step as the teacher reads it (TE2 lessons only), or None: never the question's key or rubric.

### Module constants

- `REQUEST` ([src/learnloop/teacher/probes.py](../../../../../../src/learnloop/teacher/probes.py), line 39)
- `READY` ([src/learnloop/teacher/probes.py](../../../../../../src/learnloop/teacher/probes.py), line 40)
- `REFUSED` ([src/learnloop/teacher/probes.py](../../../../../../src/learnloop/teacher/probes.py), line 41)
- `SERVED` ([src/learnloop/teacher/probes.py](../../../../../../src/learnloop/teacher/probes.py), line 42)
- `ANSWER` ([src/learnloop/teacher/probes.py](../../../../../../src/learnloop/teacher/probes.py), line 43)
- `RESULT` ([src/learnloop/teacher/probes.py](../../../../../../src/learnloop/teacher/probes.py), line 44)
- `RETIRED` ([src/learnloop/teacher/probes.py](../../../../../../src/learnloop/teacher/probes.py), line 45)
- `REFUSAL_REASONS` ([src/learnloop/teacher/probes.py](../../../../../../src/learnloop/teacher/probes.py), line 47)
- `ATTEMPT_TYPE` ([src/learnloop/teacher/probes.py](../../../../../../src/learnloop/teacher/probes.py), line 49)
- `ENTRY_SURFACE` ([src/learnloop/teacher/probes.py](../../../../../../src/learnloop/teacher/probes.py), line 50)
- `EVIDENCE_ORIGIN` ([src/learnloop/teacher/probes.py](../../../../../../src/learnloop/teacher/probes.py), line 51)
- `PREPARING` ([src/learnloop/teacher/probes.py](../../../../../../src/learnloop/teacher/probes.py), line 53)
- `NOT_PREPARED` ([src/learnloop/teacher/probes.py](../../../../../../src/learnloop/teacher/probes.py), line 54)

### Explicit exports

`__all__` declares:

- `ANSWER`
- `ATTEMPT_TYPE`
- `NOT_PREPARED`
- `PREPARING`
- `Probe`
- `READY`
- `REFUSAL_REASONS`
- `REFUSED`
- `REQUEST`
- `RESULT`
- `RETIRED`
- `SERVED`
- `contract_problem`
- `finish_recorded`
- `logged_fields`
- `open_probe`
- `pending_request`
- `probes`
- `record_answer`
- `record_ready`
- `record_refused`
- `request`
- `retire`
- `serve`
- `transcript_entry`
- `unanswered`

## Internal implementation anchors

- `_probe_of(connection: Any, lesson_id: str, node_id: str) -> tuple[dict[str, Any] | None, Probe | None]` ([source](../../../../../../src/learnloop/teacher/probes.py), line 218)
- `_close_episode(repository: Any, lesson_id: str, probe: Probe, *, closed_at: str, reason: str, outcome: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/teacher/probes.py), line 276) — Close the probe's own episode row (opened by its request), once.
- `_current(connection: Any, lesson_id: str, ref: str) -> Probe | None` ([source](../../../../../../src/learnloop/teacher/probes.py), line 357)
- `_stored_feedback(repository: Any, attempt_id: str) -> str | None` ([source](../../../../../../src/learnloop/teacher/probes.py), line 361) — The grader's feedback an already-recorded attempt was shown with (its saved completion), or None.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/followup_run/lesson_probe|learnloop.followup_run.lesson_probe]] — imports `module`; statically calls `pending_request`, `record_ready`, `record_refused`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `module`; statically calls `contract_problem`, `finish_recorded`, `logged_fields`, `open_probe`, `probes`, `record_answer`, `request`, `retire`, `serve`, `transcript_entry`, `unanswered`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `ApplyAttemptInput`, `AttemptDraft`, `apply_attempt`; calls `ApplyAttemptInput`, `AttemptDraft`, `apply_attempt`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `vault_grading_calibration_identity`; calls `vault_grading_calibration_identity`
- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `production_admissibility`; calls `production_admissibility`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/stores/lessons|learnloop.db.stores.lessons]] — imports `module`; calls `append_turn`, `lesson`, `turns`
- [[Reference/Modules/learnloop/followup_serve/identity|learnloop.followup_serve.identity]] — imports `module`; calls `claim_serve`, `retire`
- [[Reference/Modules/learnloop/followup_serve/queue|learnloop.followup_serve.queue]] — imports `module`; calls `enqueue_lesson`, `skip_lesson_job`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/scheduling/forecast_receipts|learnloop.scheduling.forecast_receipts]] — imports `ForecastReceipt`, `LESSON_PROBE_ATTEMPT`, `LESSON_PROBE_CORRECT`, `record_receipts`; calls `ForecastReceipt`, `record_receipts`
- [[Reference/Modules/learnloop/teacher/checks|learnloop.teacher.checks]] — imports `module`; calls `grade_answer`
- [[Reference/Modules/learnloop/teacher/episodes|learnloop.teacher.episodes]] — imports `module`; calls `close_one`, `node_known`, `node_lo`, `on`, `open_episode`
- [[Reference/Modules/learnloop/teacher/exposure|learnloop.teacher.exposure]] — imports `EXPOSURE_KEY`, `exposed_identities`; calls `exposed_identities`
- [[Reference/Modules/learnloop/teacher/te2|learnloop.teacher.te2]] — imports `LESSON_SURFACE`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/followup_run/lesson_probe|learnloop.followup_run.lesson_probe]], [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_te3a_lesson_opportunity.py](../../../../../../tests/test_te3a_lesson_opportunity.py) — direct import
  - `test_landing_r1_a_probe_lesson_freezes_every_display_and_its_receipt_is_judged_not_failed_closed`
- [tests/test_teacher_te2_probes.py](../../../../../../tests/test_teacher_te2_probes.py) — direct import
  - `test_a_late_question_is_retired_as_it_lands`
  - `test_a_probe_is_generated_once_served_cold_and_never_again`
  - `test_a_reserved_question_match_gives_no_probe`
- [tests/test_teacher_te2_review_fixes.py](../../../../../../tests/test_teacher_te2_review_fixes.py) — direct import
  - `test_f3_a_fault_after_the_attempt_rolls_everything_back_and_the_answer_can_be_sent_again`
  - `test_f3_a_second_submit_of_an_answered_probe_returns_its_result`

## Modification guidance

- Make changes here when the responsibility remains probes within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/probes.py](../../../../../../src/learnloop/teacher/probes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
