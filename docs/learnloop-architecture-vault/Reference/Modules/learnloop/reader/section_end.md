---
title: "learnloop.reader.section_end"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/section_end.py"
source_paths:
  - "src/learnloop/reader/section_end.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.section_end module"
  - "src/learnloop/reader/section_end.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.section_end`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.section_end` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Whether a progress report finishes its section, and why (mvp-0.63, ``docs/reviews/algorithm-mvp-0.63.md``).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/section_end.py](../../../../../../src/learnloop/reader/section_end.py) |
| Source lines | 52 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class SectionFinish` ([source](../../../../../../src/learnloop/reader/section_end.py), line 31)
- `section_finish(config: object, completed: bool, completed_by: str | None, end_span_id: str | None) -> SectionFinish` ([source](../../../../../../src/learnloop/reader/section_end.py), line 41) — ``completed`` and ``completed_by`` as the report sent them; ``end_span_id`` the end the report's check kept (None when it named none, or none that counts).

### Module constants

- `REACHED_END` ([src/learnloop/reader/section_end.py](../../../../../../src/learnloop/reader/section_end.py), line 22)
- `LEARNER_SAID` ([src/learnloop/reader/section_end.py](../../../../../../src/learnloop/reader/section_end.py), line 24)
- `LEARNER` ([src/learnloop/reader/section_end.py](../../../../../../src/learnloop/reader/section_end.py), line 27)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `section_finish`; statically calls `section_finish`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `section_end_on`; calls `section_end_on`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/figures_show_me_helpers.py](../../../../../../tests/figures_show_me_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]]
- [tests/learner_blindness_relax_helpers.py](../../../../../../tests/learner_blindness_relax_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]]
- [tests/reader_tutor_fakes.py](../../../../../../tests/reader_tutor_fakes.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]]
- [tests/test_compare_sources_keep.py](../../../../../../tests/test_compare_sources_keep.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]]
- [tests/test_figures_rw5b_review.py](../../../../../../tests/test_figures_rw5b_review.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]]
- [tests/test_method_explicit_landing.py](../../../../../../tests/test_method_explicit_landing.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]]
- [tests/test_mobile_v4_codex_review.py](../../../../../../tests/test_mobile_v4_codex_review.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]]
- [tests/test_mobile_v4_reader.py](../../../../../../tests/test_mobile_v4_reader.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]]
- [tests/test_plan_first_transport.py](../../../../../../tests/test_plan_first_transport.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]]
- [tests/test_protection_surface_matrix.py](../../../../../../tests/test_protection_surface_matrix.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]]
- [tests/test_reader_active_reading.py](../../../../../../tests/test_reader_active_reading.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]]
- [tests/test_reader_branches.py](../../../../../../tests/test_reader_branches.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]]

## Modification guidance

- Change section end policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/section_end.py](../../../../../../src/learnloop/reader/section_end.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
