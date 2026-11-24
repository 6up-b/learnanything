---
title: "learnloop.content.pipeline.practice_publication"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/pipeline/practice_publication.py"
source_paths:
  - "src/learnloop/content/pipeline/practice_publication.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.pipeline"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.pipeline.practice_publication module"
  - "src/learnloop/content/pipeline/practice_publication.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-pipeline"
---

# `learnloop.content.pipeline.practice_publication`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.pipeline.practice_publication` exists within [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] to own the behavior summarized by its module contract: Publish practice written by an ingest job, including on lease recovery.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/pipeline/practice_publication.py](../../../../../../../src/learnloop/content/pipeline/practice_publication.py) |
| Source lines | 57 |
| Owning package | [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `practice_snapshot(root)` ([source](../../../../../../../src/learnloop/content/pipeline/practice_publication.py), line 10)
- `begin_practice_write(repo, root, job, owner)` ([source](../../../../../../../src/learnloop/content/pipeline/practice_publication.py), line 21)
- `publish_practice(repo, root, job_id, clock)` ([source](../../../../../../../src/learnloop/content/pipeline/practice_publication.py), line 35) — Called inside the terminal transition's transaction.
- `publish_watched_practice(repo, root)` ([source](../../../../../../../src/learnloop/content/pipeline/practice_publication.py), line 52)

### Module constants

- `PRACTICE_WRITERS` ([src/learnloop/content/pipeline/practice_publication.py](../../../../../../../src/learnloop/content/pipeline/practice_publication.py), line 7)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `PRACTICE_WRITERS`, `begin_practice_write`, `publish_practice`; statically calls `begin_practice_write`, `publish_practice`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `publish_watched_practice`; statically calls `publish_watched_practice`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `hashlib`, `json`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]], [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/ad23_contract_helpers.py](../../../../../../../tests/ad23_contract_helpers.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]]
- [tests/figure_rich_job_helpers.py](../../../../../../../tests/figure_rich_job_helpers.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]]
- [tests/figure_rich_rpc_helpers.py](../../../../../../../tests/figure_rich_rpc_helpers.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]]
- [tests/glm_ocr_helpers.py](../../../../../../../tests/glm_ocr_helpers.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]]
- [tests/ingest_runner_helpers.py](../../../../../../../tests/ingest_runner_helpers.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]]
- [tests/learner_data_relax_2_helpers.py](../../../../../../../tests/learner_data_relax_2_helpers.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]]
- [tests/plan_first_transport_offer_grants_helpers.py](../../../../../../../tests/plan_first_transport_offer_grants_helpers.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]]
- [tests/protection_matrix_helpers.py](../../../../../../../tests/protection_matrix_helpers.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]]
- [tests/reread_safety_helpers.py](../../../../../../../tests/reread_safety_helpers.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]]
- [tests/section_question_parts_helpers.py](../../../../../../../tests/section_question_parts_helpers.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]]
- [tests/source_vector_backfill_helpers.py](../../../../../../../tests/source_vector_backfill_helpers.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]]
- [tests/test_ad23_fix_r5.py](../../../../../../../tests/test_ad23_fix_r5.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]]

## Modification guidance

- Change practice publication policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/pipeline/practice_publication.py](../../../../../../../src/learnloop/content/pipeline/practice_publication.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
