---
title: "learnloop.reader.reader_capture"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/reader_capture.py"
source_paths:
  - "src/learnloop/reader/reader_capture.py"
generated: true
generated_at: "2026-11-02"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.reader_capture` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Local-first capture spine + outbox drain (spec §5.3, §13.3, §15.2; design B step 4).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/reader_capture.py](../../../../../../src/learnloop/reader/reader_capture.py) |
| Source lines | 464 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class CaptureError(ValueError)` ([source](../../../../../../src/learnloop/reader/reader_capture.py), line 90) — Domain error for the capture spine.
- `capture(repository: Repository, *, source_id: str, revision_id: str, extraction_id: str, action: str, client_idempotency_key: str, raw_selection: Mapping[str, Any] | None=None, render_view_id: str | None=None, learner_text: str='', what_i_think_is_going_on: str | None=None, privacy_locality: str='local_private', session_id: str | None=None, commitment_id: str | None=None, enqueue_synth: bool=False, preset: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_capture.py), line 132) — One local-first capture.
- `invoke_preset(repository: Repository, *, preset: str, source_id: str, revision_id: str, extraction_id: str, client_idempotency_key: str, raw_selection: Mapping[str, Any] | None=None, render_view_id: str | None=None, learner_text: str='', what_i_think_is_going_on: str | None=None, session_id: str | None=None, subject_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_capture.py), line 245) — The three-action / nine-preset palette (§5.2).
- `drain_outbox(repository: Repository, *, limit: int=100, convert: Callable[[Repository, Mapping[str, Any]], str | None]=_default_convert, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_capture.py), line 425) — Drain pending outbox rows idempotently.
- `outbox_status(repository: Repository, *, client_idempotency_key: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/reader/reader_capture.py), line 451)

### Module constants

- `_ACTION_MAP` ([src/learnloop/reader/reader_capture.py](../../../../../../src/learnloop/reader/reader_capture.py), line 34)
- `PRESETS` ([src/learnloop/reader/reader_capture.py](../../../../../../src/learnloop/reader/reader_capture.py), line 74)
- `REVERTED_CAPTURE_REASON` ([src/learnloop/reader/reader_capture.py](../../../../../../src/learnloop/reader/reader_capture.py), line 357)

## Internal implementation anchors

- `class _Preset(NamedTuple)` ([source](../../../../../../src/learnloop/reader/reader_capture.py), line 56) — A palette preset (§5.2): the local-capture action + its commit/synthesis wiring.
- `_selection_surface(raw_selection: Mapping[str, Any] | None) -> tuple[str, bool]` ([source](../../../../../../src/learnloop/reader/reader_capture.py), line 94) — Return the learner-visible selection while retaining source-owned anchors.
- `_anchor_from_translation(*, source_id: str, revision_id: str, extraction_id: str, render_view_id: str | None, translation: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_capture.py), line 114)
- `_default_convert(repository: Repository, row: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/reader/reader_capture.py), line 360) — Idempotent outbox conversion (§5.3 step 6 seam).
- `_enqueue_for(repository: Repository, row: Mapping[str, Any], payload: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/reader/reader_capture.py), line 386)
- `_loads(value: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_capture.py), line 413)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/reader/reader_intent|learnloop.reader.reader_intent]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `capture`, `drain_outbox`, `invoke_preset`, `outbox_status`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/salience_firewall|learnloop.attempts.salience_firewall]] — imports `salience_payload`; calls `salience_payload`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/curriculum/commitment_arcs|learnloop.curriculum.commitment_arcs]] — imports `module`; calls `create_arc`, `preview_for_capture`, `project_arc`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `create_commitment`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/reader/annotations|learnloop.reader.annotations]] — imports `module`; calls `translate_selection`
- [[Reference/Modules/learnloop/reader/reader_requests|learnloop.reader.reader_requests]] — imports `module`; calls `annotation_instructions`, `enqueue_request`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/reader/reader_intent|learnloop.reader.reader_intent]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

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
- [tests/test_reader_intentions.py](../../../../../../tests/test_reader_intentions.py) — direct import
  - `test_grouping_changes_no_presets_effect`
- [tests/test_reader_rw1b_final_verify.py](../../../../../../tests/test_reader_rw1b_final_verify.py) — direct import
  - `test_f14_a_revert_after_an_undone_revert_converts_to_no_work`
  - `test_f14_revert_restore_revert_restore_converts`
  - `test_f14_revert_restore_revert_then_a_retried_conversion_enqueues_nothing`
  - `test_f16_a_running_revival_lands_on_the_reviving_capture`
  - `test_f16_a_same_instruction_revival_rebinds_to_the_reviving_capture`
  - `test_f16_captures_with_different_instructions_never_share_or_revive`
  - `test_f16_reverting_the_bound_capture_of_shared_work_rebinds_it`
- [tests/test_reader_rw1b_fix_round4.py](../../../../../../tests/test_reader_rw1b_fix_round4.py) — direct import
  - `test_a_revert_of_a_completed_request_nobody_else_holds_leaves_it`
  - `test_c_a_revival_during_landing_ends_mapped_to_the_reviving_capture`
  - `test_d_a_compatible_no_note_revival_keeps_its_exact_key`
  - `test_d_a_legacy_rekey_that_collides_takes_a_key_no_enqueue_computes`
  - `test_d_a_no_note_capture_never_revives_a_legacy_request_asking_something_else`
- [tests/test_reader_rw1b_rereview.py](../../../../../../tests/test_reader_rw1b_rereview.py) — direct import
  - `test_f14_a_capture_reverted_before_its_drain_enqueues_nothing`
  - `test_f14_a_failed_conversion_retried_after_the_revert_enqueues_nothing`
  - `test_f14_a_revert_racing_a_drain_waits_for_it_and_cancels_what_it_enqueued`
  - `test_f15_a_later_capture_keeps_running_work_its_revert_flagged`
  - `test_f15_a_later_capture_revives_cancelled_work`
- [tests/test_reader_rw1b_review.py](../../../../../../tests/test_reader_rw1b_review.py) — direct import
  - `test_f4_change_reverts_the_routed_capture_its_commitment_and_its_request`

## Modification guidance

- Change reader capture policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/reader_capture.py](../../../../../../src/learnloop/reader/reader_capture.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
