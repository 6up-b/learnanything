---
title: "learnloop_sidecar.section_questions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/section_questions.py"
source_paths:
  - "src/learnloop_sidecar/section_questions.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar"
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
  - "learnloop_sidecar.section_questions module"
  - "src/learnloop_sidecar/section_questions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar"
---

# `learnloop_sidecar.section_questions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.section_questions` exists within [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] to own the behavior summarized by its module contract: A finished section's questions, started from the desktop app (the primary).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/section_questions.py](../../../../../src/learnloop_sidecar/section_questions.py) |
| Source lines | 66 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `start_section_questions(ctx: Any, vault: Any, repository: Any, extraction_id: str, section_id: str, *, from_stamp: str | None=None, completed_at: str | None=None) -> str | None` ([source](../../../../../src/learnloop_sidecar/section_questions.py), line 19) — A finished section's question writing, queued on this app's queue, once; the batch id, or None.
- `drain_owed_section_questions(ctx: Any, vault: Any, repository: Any, *, extraction_id: str | None=None) -> int` ([source](../../../../../src/learnloop_sidecar/section_questions.py), line 42) — Start the writing every finished section still owes: one the phone finished, one that waited for its book's build, one an older version settled as needing nothing before its topics were in.

### Module constants

- `_LOGGER` ([src/learnloop_sidecar/section_questions.py](../../../../../src/learnloop_sidecar/section_questions.py), line 16)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `drain_owed_section_questions`; statically calls `drain_owed_section_questions`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `drain_owed_section_questions`; statically calls `drain_owed_section_questions`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `drain_owed_section_questions`, `start_section_questions`; statically calls `drain_owed_section_questions`, `start_section_questions`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `quiet`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `section_topics_settled`; calls `section_topics_settled`
- [[Reference/Modules/learnloop/reader/section_generation|learnloop.reader.section_generation]] — imports `OWED`, `module`; calls `start_section_questions`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

### Platform and third-party dependencies

- Standard library: `__future__`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/ad1_attempt_columns_helpers.py](../../../../../tests/ad1_attempt_columns_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/capture_desktop_helpers.py](../../../../../tests/capture_desktop_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/daily_plan_kill_switch_helpers.py](../../../../../tests/daily_plan_kill_switch_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/device_eligibility_helpers.py](../../../../../tests/device_eligibility_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/facet_reword_paths_helpers.py](../../../../../tests/facet_reword_paths_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/figures_help_helpers.py](../../../../../tests/figures_help_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/followup_fg1d_probe_shadow_helpers.py](../../../../../tests/followup_fg1d_probe_shadow_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/followup_journey_helpers.py](../../../../../tests/followup_journey_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/graph_editor_reads_helpers.py](../../../../../tests/graph_editor_reads_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/hint_h2a_review_helpers.py](../../../../../tests/hint_h2a_review_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/hint_h2a_review_round2_helpers.py](../../../../../tests/hint_h2a_review_round2_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/hint_h2b_review_helpers.py](../../../../../tests/hint_h2b_review_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/section_questions.py](../../../../../src/learnloop_sidecar/section_questions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
