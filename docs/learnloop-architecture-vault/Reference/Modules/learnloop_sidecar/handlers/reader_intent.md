---
title: "learnloop_sidecar.handlers.reader_intent"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/reader_intent.py"
source_paths:
  - "src/learnloop_sidecar/handlers/reader_intent.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop_sidecar.handlers.reader_intent module"
  - "src/learnloop_sidecar/handlers/reader_intent.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.reader_intent`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.reader_intent` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Reader workbench RW1b: the intent box and active reading (spec_reader_workbench_v1 §4.2-§4.5).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/reader_intent.py](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py) |
| Source lines | 632 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `intent_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 78) — The intent box is on: its switch and RW1a's inquiry (its rail and shared parts).
- `active_reading_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 84)
- `prompt_contract_fields(vault: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 88) — What the Reader's prompt contract adds for RW1b (absent while off, so the wire is unchanged).
- `class IntentRoutings` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 192) — Routings in flight and just made, kept for reading back (in memory).
  - `__init__(self) -> None` (line 195; internal)
  - `start(self, ctx: SidecarContext, vault: Any, repository: Any, *, text: str, quote: str, extraction_id: str, span_ids: list[str], speculative: bool, notes: bool=False) -> _Running` (line 199; public)
  - `get(self, routing_id: str) -> _Running | None` (line 258; public)
- `class ReaderRouteIntentInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 282)
- `reader_route_intent(ctx: SidecarContext, params: ReaderRouteIntentInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 296) — Start routing the intent box's text (never on the request path).
- `class ReaderIntentRoutingInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 321)
- `reader_intent_routing(ctx: SidecarContext, params: ReaderIntentRoutingInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 327) — A routing's state; waits up to ``wait_ms`` (at most a second) for it.
- `class ReaderIntentOutcomeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 340)
- `reader_intent_outcome(ctx: SidecarContext, params: ReaderIntentOutcomeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 349) — ``used`` (Enter took it), ``discarded`` (the text changed, the box closed), ``corrected`` ("change", with the action picked instead, or none) or ``reverted`` ("change" after a routed capture ran: its annotation, commitment and synthesis are undone).
- `class ReaderActiveQuestionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 449)
- `reader_active_question(ctx: SidecarContext, params: ReaderActiveQuestionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 459) — The selection's question in one style: reused, or queued for the producer (written off the request path).
- `class ReaderActiveQuestionStatusInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 515)
- `reader_active_question_status(ctx: SidecarContext, params: ReaderActiveQuestionStatusInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 523) — The question once written (a cheap local read), and its job's state.
- `class ReaderActiveQuestionActionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 536)
- `reader_active_question_action(ctx: SidecarContext, params: ReaderActiveQuestionActionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 544) — Answer (an empty answer is "show me"), self-check or dismiss.
- `class ReaderReconstructInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 570)
- `reader_reconstruct(ctx: SidecarContext, params: ReaderReconstructInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 576) — "Reconstruct this later": the escalated item and its ``test_me_later`` commitment (idempotent).
- `class ReaderReconstructUndoInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 609)
- `reader_reconstruct_undo(ctx: SidecarContext, params: ReaderReconstructUndoInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 614) — Undo "reconstruct this later": its commitment and its item are retired.

### Module constants

- `MAX_KEPT_ROUTINGS` ([src/learnloop_sidecar/handlers/reader_intent.py](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 62)
- `MAX_WAIT_MS` ([src/learnloop_sidecar/handlers/reader_intent.py](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 64)
- `RW1B_RPCS` ([src/learnloop_sidecar/handlers/reader_intent.py](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 66)

## Internal implementation anchors

- `_require_reader(ctx: SidecarContext)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 108)
- `_require_intent(ctx: SidecarContext)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 115)
- `_require_active(ctx: SidecarContext)` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 124)
- `_extraction(repository, extraction_id: str) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 135)
- `_refuse_held_out(vault, repository, extraction_id: str, span_ids: list[str]) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 142)
- `_event(repository, kind: str, payload: dict[str, Any], *, subject_id: str | None) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 148)
- `class _Running` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 161)
- `_record_fate(repository, running: _Running, fate: str) -> str | None` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 177) — One fate (``used`` or ``discarded``) and its funnel event.
- `_routings(ctx: SidecarContext) -> IntentRoutings` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 263)
- `_routing_payload(running: _Running) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 271)
- `_question_payload(vault, repository, row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 400)
- `_reconstruct_state(repository, row: dict[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 420)
- `_job_state(repository, batch_id: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py), line 430)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `prompt_contract_fields`; statically calls `prompt_contract_fields`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `priced_by`
- [[Reference/Modules/learnloop/attempts/salience_firewall|learnloop.attempts.salience_firewall]] — imports `salience_payload`; calls `salience_payload`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `resolve_disposition`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/reader/active_reading|learnloop.reader.active_reading]] — imports `module`; calls `_commitment_for`, `reconstruct_commit`, `reconstruct_undo`, `record_action`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; calls `inquiry_enabled`, `reader_enabled`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `module`; calls `reading_protection`
- [[Reference/Modules/learnloop/reader/reader_intent|learnloop.reader.reader_intent]] — imports `module`; calls `Routing`, `palette`, `record_correction`, `record_fate`, `revert_capture`, `route`, `speculation_room`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `learning_objects_for_span`; calls `learning_objects_for_span`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `module`; calls `is_missed`, `selection_question`, `selection_view`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `log_interaction_event`; calls `log_interaction_event`
- [[Reference/Modules/learnloop_sidecar/background_jobs|learnloop_sidecar.background_jobs]] — imports `background_jobs`; calls `background_jobs`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `ready_canonical_ingest_provider`; calls `ready_canonical_ingest_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `_authored_question_payload`; calls `_authored_question_payload`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`
- [[Reference/Modules/learnloop_sidecar/source_identity|learnloop_sidecar.source_identity]] — imports `require_identity`; calls `require_identity`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `threading`, `time`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_rw1b_rpcs_are_all_of_them`
- [tests/test_reader_intent.py](../../../../../../tests/test_reader_intent.py) — direct import
  - `test_the_sidecar_never_sends_a_held_out_passage`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/reader_intent.py](../../../../../../src/learnloop_sidecar/handlers/reader_intent.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
