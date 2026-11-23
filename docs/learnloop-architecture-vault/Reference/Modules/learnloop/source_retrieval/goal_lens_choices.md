---
title: "learnloop.source_retrieval.goal_lens_choices"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/goal_lens_choices.py"
source_paths:
  - "src/learnloop/source_retrieval/goal_lens_choices.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.source_retrieval.goal_lens_choices module"
  - "src/learnloop/source_retrieval/goal_lens_choices.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.goal_lens_choices`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.goal_lens_choices` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: The learner's choices on a section for one goal (Reader workbench v2 §12.5): *read it anyway* on a section the goal lens dims (skippable, or needed only deeper), or ``none``, clearing it.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/goal_lens_choices.py](../../../../../../src/learnloop/source_retrieval/goal_lens_choices.py) |
| Source lines | 98 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ChoiceError(ValueError)` ([source](../../../../../../src/learnloop/source_retrieval/goal_lens_choices.py), line 32)
  - `__init__(self, code: str, message: str) -> None` (line 33; internal)
- `choose(repository: Repository, goal_id: str, extraction_id: str, section_id: str, choice: str, *, operation_id: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/goal_lens_choices.py), line 52) — One choice on a section of a reading, for one goal.
- `section_choices(repository: Repository, goal_id: str) -> dict[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/goal_lens_choices.py), line 87) — Section ref -> the learner's standing choice for this goal (a cleared one is absent).

### Module constants

- `TASK` ([src/learnloop/source_retrieval/goal_lens_choices.py](../../../../../../src/learnloop/source_retrieval/goal_lens_choices.py), line 24)
- `LEFT_KIND` ([src/learnloop/source_retrieval/goal_lens_choices.py](../../../../../../src/learnloop/source_retrieval/goal_lens_choices.py), line 25)
- `RIGHT_KIND` ([src/learnloop/source_retrieval/goal_lens_choices.py](../../../../../../src/learnloop/source_retrieval/goal_lens_choices.py), line 26)
- `VERSION` ([src/learnloop/source_retrieval/goal_lens_choices.py](../../../../../../src/learnloop/source_retrieval/goal_lens_choices.py), line 27)
- `CHOICES` ([src/learnloop/source_retrieval/goal_lens_choices.py](../../../../../../src/learnloop/source_retrieval/goal_lens_choices.py), line 28)
- `_OPERATION_ID` ([src/learnloop/source_retrieval/goal_lens_choices.py](../../../../../../src/learnloop/source_retrieval/goal_lens_choices.py), line 29)

### Explicit exports

`__all__` declares:

- `CHOICES`
- `ChoiceError`
- `choose`
- `section_choices`

## Internal implementation anchors

- `_ledger_id(operation_id: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/goal_lens_choices.py), line 38)
- `_view(row: Mapping[str, Any], *, replayed: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/goal_lens_choices.py), line 42)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/goal_lens_reads|learnloop.source_retrieval.goal_lens_reads]] — imports `module`; statically calls `section_choices`
- [[Reference/Modules/learnloop_sidecar/handlers/goal_lens|learnloop_sidecar.handlers.goal_lens]] — imports `module`; statically calls `choose`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/section_map|learnloop.section_map]] — imports `extraction_sections`; calls `extraction_sections`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/goal_lens_reads|learnloop.source_retrieval.goal_lens_reads]], [[Reference/Modules/learnloop_sidecar/handlers/goal_lens|learnloop_sidecar.handlers.goal_lens]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/goal_lens|learnloop_sidecar.handlers.goal_lens]]
- [tests/test_reader_rd6a_goal_lens.py](../../../../../../tests/test_reader_rd6a_goal_lens.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/goal_lens|learnloop_sidecar.handlers.goal_lens]]

## Modification guidance

- Make changes here when the responsibility remains goal lens choices within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/goal_lens_choices.py](../../../../../../src/learnloop/source_retrieval/goal_lens_choices.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
