---
title: "learnloop.reader.reader_capture"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/reader_capture.py"
source_paths:
  - "src/learnloop/reader/reader_capture.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.reader_capture module"
  - "src/learnloop/reader/reader_capture.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.reader_capture`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.reader_capture` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Local-first capture spine + outbox drain (spec §5.3, §13.3, §15.2; design B step 4).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/reader_capture.py](../../../../../../src/learnloop/reader/reader_capture.py) |
| Source lines | 435 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class CaptureError(ValueError)` ([source](../../../../../../src/learnloop/reader/reader_capture.py), line 90) — Domain error for the capture spine.
- `capture(repository: Repository, *, source_id: str, revision_id: str, extraction_id: str, action: str, client_idempotency_key: str, raw_selection: Mapping[str, Any] | None=None, render_view_id: str | None=None, learner_text: str='', what_i_think_is_going_on: str | None=None, privacy_locality: str='local_private', session_id: str | None=None, commitment_id: str | None=None, enqueue_synth: bool=False, preset: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_capture.py), line 132) — One local-first capture.
- `invoke_preset(repository: Repository, *, preset: str, source_id: str, revision_id: str, extraction_id: str, client_idempotency_key: str, raw_selection: Mapping[str, Any] | None=None, render_view_id: str | None=None, learner_text: str='', what_i_think_is_going_on: str | None=None, session_id: str | None=None, subject_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_capture.py), line 245) — The three-action / nine-preset palette (§5.2).
- `drain_outbox(repository: Repository, *, limit: int=100, convert: Callable[[Repository, Mapping[str, Any]], str | None]=_default_convert, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_capture.py), line 396) — Drain pending outbox rows idempotently.
- `outbox_status(repository: Repository, *, client_idempotency_key: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/reader/reader_capture.py), line 422)
- `retry_outbox(repository: Repository, *, outbox_id: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_capture.py), line 427) — Reset a failed row to pending for the next drain (capture already durable).

### Module constants

- `_ACTION_MAP` ([src/learnloop/reader/reader_capture.py](../../../../../../src/learnloop/reader/reader_capture.py), line 34)
- `PRESETS` ([src/learnloop/reader/reader_capture.py](../../../../../../src/learnloop/reader/reader_capture.py), line 74)

## Internal implementation anchors

- `class _Preset(NamedTuple)` ([source](../../../../../../src/learnloop/reader/reader_capture.py), line 56) — A palette preset (§5.2): the local-capture action + its commit/synthesis wiring.
- `_selection_surface(raw_selection: Mapping[str, Any] | None) -> tuple[str, bool]` ([source](../../../../../../src/learnloop/reader/reader_capture.py), line 94) — Return the learner-visible selection while retaining source-owned anchors.
- `_anchor_from_translation(*, source_id: str, revision_id: str, extraction_id: str, render_view_id: str | None, translation: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_capture.py), line 114)
- `_default_convert(repository: Repository, row: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/reader/reader_capture.py), line 353) — Idempotent outbox conversion (§5.3 step 6 seam).
- `_loads(value: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_capture.py), line 384)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `capture`, `drain_outbox`, `invoke_preset`, `outbox_status`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/salience_firewall|learnloop.attempts.salience_firewall]] — imports `salience_payload`; calls `salience_payload`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/curriculum/commitment_arcs|learnloop.curriculum.commitment_arcs]] — imports `module`; calls `create_arc`, `preview_for_capture`, `project_arc`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `create_commitment`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/reader/annotations|learnloop.reader.annotations]] — imports `module`; calls `translate_selection`
- [[Reference/Modules/learnloop/reader/reader_requests|learnloop.reader.reader_requests]] — imports `module`; calls `enqueue_request`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_p3_journeys.py](../../../../../../tests/test_p3_journeys.py) — direct import
  - `test_annotation_survival_across_reextraction`
  - `test_arc_and_salience_heads_rebuild_deterministically`
  - `test_journey1_reading_first_session`
  - `test_journey2_quick_insight_capture`
- [tests/test_reader_capture.py](../../../../../../tests/test_reader_capture.py) — direct import
  - `test_ask_and_mark_presets_never_create_commitments`
  - `test_background_request_preserves_all_captured_spans_through_outbox`
  - `test_commit_preset_captures_commitment_and_enqueues_one_synth_request`
  - `test_crash_after_capture_before_drain_survives_and_resumes_once`
  - `test_crash_mid_drain_recovers_without_duplication`
  - `test_drain_is_idempotent`
  - `test_preset_crash_between_arc_and_capture_resumes_exactly_once`
  - `test_preset_crash_between_drain_and_synth_enqueues_once`
  - `test_worked_example_preserves_edited_latex_selection_through_outbox`

## Modification guidance

- Change reader capture policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/reader_capture.py](../../../../../../src/learnloop/reader/reader_capture.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
