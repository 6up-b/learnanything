---
title: "learnloop_sidecar.handlers.learner_gaps"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/learner_gaps.py"
source_paths:
  - "src/learnloop_sidecar/handlers/learner_gaps.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.handlers.learner_gaps module"
  - "src/learnloop_sidecar/handlers/learner_gaps.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.learner_gaps`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.learner_gaps` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Learner-text gap RPCs: what a question was read as, and its one-tap undo.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/learner_gaps.py](../../../../../../src/learnloop_sidecar/handlers/learner_gaps.py) |
| Source lines | 186 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class GetLearnerTextGapInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/learner_gaps.py), line 26)
- `class ReverseLearnerTextGapInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/learner_gaps.py), line 31)
- `gap_view(vault: Any, gap: dict[str, Any], reversals: list[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/learner_gaps.py), line 36) — The learner-facing reading: honest labels, only what happened.
- `queue_tutor_question_gap(ctx: SidecarContext, vault: Any, repository: Any, event_id: str, reading: dict[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/learner_gaps.py), line 130) — Queue an answered question's gap reading and wake the worker.
- `get_learner_text_gap(ctx: SidecarContext, params: GetLearnerTextGapInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/learner_gaps.py), line 153)
- `reverse_learner_text_gap(ctx: SidecarContext, params: ReverseLearnerTextGapInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/learner_gaps.py), line 170)

### Explicit exports

`__all__` declares:

- `gap_view`
- `get_learner_text_gap`
- `queue_tutor_question_gap`
- `reverse_learner_text_gap`

## Internal implementation anchors

- `_changed_vault(vault: Any, gap: dict[str, Any], reversals: list[str]) -> bool` ([source](../../../../../../src/learnloop_sidecar/handlers/learner_gaps.py), line 91) — Does the loaded vault predate what this reading (or its undo) wrote?
- `_reconcile(ctx: SidecarContext, vault: Any, repository: Any, gap: dict[str, Any], reversals: list[str]) -> tuple[Any, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/learner_gaps.py), line 107) — Reload once per reading state when the loaded vault looks older than it.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `queue_tutor_question_gap`; statically calls `queue_tutor_question_gap`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `queue_tutor_question_gap`; statically calls `queue_tutor_question_gap`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `queue_tutor_question_gap`; statically calls `queue_tutor_question_gap`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/learner_gaps|learnloop.db.stores.learner_gaps]] — imports `module`; calls `gap`, `gap_for_source`, `job_for_source`, `reversals`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]] — imports `UndoError`, `reverse_gap`; calls `reverse_gap`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `enqueue_tutor_question`; calls `enqueue_tutor_question`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]], [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followups_nov2_note_gap_unlinked.py](../../../../../../tests/test_followups_nov2_note_gap_unlinked.py) — direct import
  - `test_hiding_a_read_notes_link_sets_its_gaps_aside_and_only_its_own`
- [tests/test_learner_text_gaps_flow.py](../../../../../../tests/test_learner_text_gaps_flow.py) — direct import
  - `test_the_sidecar_queues_the_reading_and_the_overlay_shows_it_with_undo`
- [tests/test_learner_text_gaps_review.py](../../../../../../tests/test_learner_text_gaps_review.py) — direct import
  - `test_f16_a_removed_edge_reloads_once_and_bumps_nothing`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/learner_gaps.py](../../../../../../src/learnloop_sidecar/handlers/learner_gaps.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
