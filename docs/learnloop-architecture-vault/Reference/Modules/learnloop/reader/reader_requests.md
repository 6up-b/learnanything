---
title: "learnloop.reader.reader_requests"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/reader_requests.py"
source_paths:
  - "src/learnloop/reader/reader_requests.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.reader_requests module"
  - "src/learnloop/reader/reader_requests.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.reader_requests`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.reader_requests` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Demand-paged synthesis: reader background requests (spec §6, design B step 6).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/reader_requests.py](../../../../../../src/learnloop/reader/reader_requests.py) |
| Source lines | 786 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `normalized_instructions(text: Any) -> str` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 66) — The learner's instructions for a capture (its ``learner_text``, what the model is told to do with the passage), whitespace collapsed: part of a capture's synthesis request identity (Codex final verify of RW1b, F16).
- `class LandingDiscarded(Exception)` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 80) — A request a revert cancelled while it ran reached its landing: the result is discarded and the request resolves ``cancelled``, as a cancelled queued request never runs (Codex verify of RW1b fix round 3, F16).
- `annotation_instructions(repository: Repository, annotation_id: Any) -> str` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 86) — A capture's instructions, as the model is given them: its annotation head's ``learner_text`` ("" without an annotation).
- `class ReaderRequestError(ValueError)` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 103) — Domain error for the demand-paged synthesis service.
- `request_reader_preset_synthesis(client: StructuredTransport, context: ReaderPresetSynthesisContext) -> ReaderPresetSynthesis` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 107) — Synthesize one reader preset through the shared transport.
- `neighborhood(repository: Repository, *, extraction_id: str, span_id: str, selected_span_ids: Sequence[str]=()) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 120) — Resolve the bounded union around every selected source block (§6.3).
- `request_key(*, revision_id: str, window: Mapping[str, Any], preset: str, provider: str, model: str, config_hash: str, inventory_profile: str='semantic', instructions: str='') -> str` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 185) — Canonical idempotency key over {revision, window, preset, inventory schema + profile, synthesis/output schema, prompt+provider+model, config/policy} (§6.2).
- `enqueue_request(repository: Repository, *, source_id: str, revision_id: str, extraction_id: str, span_id: str, preset: str, provider: str='stub', model: str='stub-1', config_hash: str='', inventory_profile: str='semantic', annotation_id: str | None=None, commitment_id: str | None=None, client_idempotency_key: str | None=None, selected_text: str='', selection_edited: bool=False, selected_span_ids: Sequence[str]=(), revive_cancelled: bool=False, instructions: str='', clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 238) — Enqueue a demand-paged synthesis request (§6).
- `request_status(repository: Repository, *, request_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 364)
- `cancel_request(repository: Repository, *, request_id: str, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 379)
- `retry_request(repository: Repository, *, request_id: str, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 383)
- `rebind_completed(repository: Repository, *, request_id: str, annotation_id: str, commitment_id: str | None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 515) — Rebind a COMPLETED request to the capture that still holds it after the capture it served was reverted, and move its commitment mapping with it (Codex verify of RW1b fix round 3, F16).
- `model_synthesis(client: Any, *, source_sets: Any) -> Callable[[Repository, Mapping[str, Any], Clock | None], dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 559) — Build the real ``synthesize`` seam for :func:`drain_requests`.
- `drain_requests(repository: Repository, *, worker_id: str='reader-synth', lease_seconds: int=120, limit: int=100, synthesize: Callable[[Repository, Mapping[str, Any], Clock | None], dict[str, Any]] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 719) — Drain queued requests under a fenced lease.

### Module constants

- `PRIORITY_BAND` ([src/learnloop/reader/reader_requests.py](../../../../../../src/learnloop/reader/reader_requests.py), line 41)
- `MAX_ADJACENT_BLOCKS` ([src/learnloop/reader/reader_requests.py](../../../../../../src/learnloop/reader/reader_requests.py), line 43)
- `TOKEN_CAP` ([src/learnloop/reader/reader_requests.py](../../../../../../src/learnloop/reader/reader_requests.py), line 45)
- `INVENTORY_SCHEMA_VERSION` ([src/learnloop/reader/reader_requests.py](../../../../../../src/learnloop/reader/reader_requests.py), line 48)
- `SYNTHESIS_SCHEMA_VERSION` ([src/learnloop/reader/reader_requests.py](../../../../../../src/learnloop/reader/reader_requests.py), line 49)
- `PROMPT_VERSION` ([src/learnloop/reader/reader_requests.py](../../../../../../src/learnloop/reader/reader_requests.py), line 50)
- `_PRESET_OBJECT_TYPE` ([src/learnloop/reader/reader_requests.py](../../../../../../src/learnloop/reader/reader_requests.py), line 54)
- `REVERTED_CAPTURE_REASON` ([src/learnloop/reader/reader_requests.py](../../../../../../src/learnloop/reader/reader_requests.py), line 77)

## Internal implementation anchors

- `_revivable(row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 96) — The rows a capture's conversion revives (Codex re-review of RW1b, F15).
- `_land_proposals(repository: Repository, request: Mapping[str, Any], clock: Clock | None, *, object_type: str, exact_text: str, content: Mapping[str, Any], span_ids: list[str], model_provenance: Mapping[str, Any], usage: Mapping[str, int] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 387) — Land one synthesis result as the reviewable §6.4 artifact pair: a PROPOSED source object + canonical mapping proposal (+ commitment mapping for commit-class presets).
- `_revert_cancelled(repository: Repository, row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 492) — A running request a revert flagged for cancellation: its bound capture was reverted and no other capture holds it (a holder would have been rebound to, and a revival clears the flag).
- `_stopped(repository: Repository, commitment_id: str) -> bool` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 505) — A stopped commitment (a reverted capture's, retired) never receives a mapping (Codex final verify of RW1b, F16).
- `_deterministic_synthesis(repository: Repository, request: Mapping[str, Any], clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 679) — Deterministic, no-LLM synthesis producing a PROPOSED source object + canonical mapping proposal (the reviewable artifact, §6.4).
- `_plus_seconds(now_iso: str, seconds: int) -> str` ([source](../../../../../../src/learnloop/reader/reader_requests.py), line 783)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `module`; statically calls `drain_requests`, `model_synthesis`
- [[Reference/Modules/learnloop/reader/reader_capture|learnloop.reader.reader_capture]] — imports `module`; statically calls `annotation_instructions`, `enqueue_request`
- [[Reference/Modules/learnloop/reader/reader_intent|learnloop.reader.reader_intent]] — imports `module`; statically calls `rebind_completed`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `cancel_request`, `drain_requests`, `enqueue_request`, `request_status`, `retry_request`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `record_model_calls`; calls `record_model_calls`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `StructuredTransport`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `held_out_among`, `held_out_material`, `held_out_refusal`; calls `held_out_among`, `held_out_material`, `held_out_refusal`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `resolve_disposition`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/reader/ai_contracts|learnloop.reader.ai_contracts]] — imports `ReaderPresetSynthesis`, `ReaderPresetSynthesisContext`, `reader_preset_synthesis_prompt`; calls `ReaderPresetSynthesisContext`, `reader_preset_synthesis_prompt`
- [[Reference/Modules/learnloop/reader/source_objects|learnloop.reader.source_objects]] — imports `module`; calls `author_source_object`, `propose_mapping`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/reader/reader_capture|learnloop.reader.reader_capture]], [[Reference/Modules/learnloop/reader/reader_intent|learnloop.reader.reader_intent]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_codex_output_schema.py](../../../../../../tests/test_codex_output_schema.py) — direct import
  - `test_sdk_reader_preset_regenerates_when_app_server_rejects_hex_escape`
  - `test_sdk_reader_preset_repairs_invalid_unicode_json_once`
- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — direct import
  - `test_a_reader_preset_on_held_out_material_fails_before_any_model_call`
- [tests/test_ingest_jobs.py](../../../../../../tests/test_ingest_jobs.py) — direct import
  - `test_background_reader_drain_records_model_call_receipts`
  - `test_kick_reader_drain_leaves_requests_queued_without_provider`
  - `test_kick_reader_drain_runs_model_synthesis_foreground`
- [tests/test_reader_requests.py](../../../../../../tests/test_reader_requests.py) — direct import
  - `test_cancel_request_never_cancels_the_local_capture`
  - `test_different_selections_in_one_block_do_not_share_a_request`
  - `test_drain_lease_is_fenced_and_reruns_are_noops`
  - `test_drain_produces_reviewable_proposals_not_evidence`
  - `test_enqueue_is_idempotent_on_contract_and_versions_change_identity`
  - `test_model_synthesis_focuses_edited_latex_selection`
  - `test_model_synthesis_lands_generated_content_as_proposed_object`
  - `test_model_synthesis_receives_every_selected_span_and_its_context`
  - `test_model_synthesis_rejects_invented_spans`
  - `test_model_synthesis_without_provider_support_fails_visibly`
  - `test_neighborhood_is_bounded_to_smallest_window`
  - `test_neighborhood_merges_bounded_context_around_every_selected_span`
  - `test_token_cap_keeps_capture_and_never_expands_scope`
- [tests/test_reader_rw1b_final_verify.py](../../../../../../tests/test_reader_rw1b_final_verify.py) — direct import
  - `test_f14_revert_restore_revert_restore_converts`
  - `test_f14_revert_restore_revert_then_a_retried_conversion_enqueues_nothing`
  - `test_f16_a_key_without_instructions_is_unchanged`
  - `test_f16_a_running_revival_lands_on_the_reviving_capture`
  - `test_f16_a_same_instruction_revival_rebinds_to_the_reviving_capture`
  - `test_f16_captures_with_different_instructions_never_share_or_revive`
  - `test_f16_reverting_the_bound_capture_of_shared_work_rebinds_it`
- [tests/test_reader_rw1b_fix_round4.py](../../../../../../tests/test_reader_rw1b_fix_round4.py) — direct import
  - `test_a_revert_after_the_binding_read_still_maps_the_holder`
  - `test_a_revert_of_a_completed_request_nobody_else_holds_leaves_it`
  - `test_a_revert_of_a_completed_shared_request_moves_its_commitment_mapping`
  - `test_an_explicit_cancel_of_a_running_request_still_lands`
  - `test_b_a_revert_after_the_stopped_check_moves_the_mapping`
  - `test_c_a_revival_during_landing_ends_mapped_to_the_reviving_capture`
  - `test_d_a_compatible_no_note_revival_keeps_its_exact_key`
  - `test_d_a_no_note_capture_never_revives_a_legacy_request_asking_something_else`
  - `test_the_landing_writes_the_drains_result`
- [tests/test_reader_rw1b_rereview.py](../../../../../../tests/test_reader_rw1b_rereview.py) — direct import
  - `test_f14_a_failed_conversion_retried_after_the_revert_enqueues_nothing`
  - `test_f14_a_revert_racing_a_drain_waits_for_it_and_cancels_what_it_enqueued`
  - `test_f15_a_later_capture_revives_cancelled_work`
- [tests/test_reread_safety.py](../../../../../../tests/test_reread_safety.py) — direct import
  - `test_a_new_citation_records_its_blocks_content_hash`
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import

## Modification guidance

- Change reader requests policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/reader_requests.py](../../../../../../src/learnloop/reader/reader_requests.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
