---
title: "learnloop.content.sources.front_matter"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/sources/front_matter.py"
source_paths:
  - "src/learnloop/content/sources/front_matter.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.sources"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.sources.front_matter module"
  - "src/learnloop/content/sources/front_matter.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-sources"
---

# `learnloop.content.sources.front_matter`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.sources.front_matter` exists within [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] to own the behavior summarized by its module contract: Front and back matter by heading: contents, preface, index, references...

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/sources/front_matter.py](../../../../../../../src/learnloop/content/sources/front_matter.py) |
| Source lines | 30 |
| Owning package | [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `is_front_matter_label(label: str | None) -> bool` ([source](../../../../../../../src/learnloop/content/sources/front_matter.py), line 20) — Whether a section heading names front or back matter.

### Module constants

- `FRONT_MATTER` ([src/learnloop/content/sources/front_matter.py](../../../../../../../src/learnloop/content/sources/front_matter.py), line 12)

### Explicit exports

`__all__` declares:

- `FRONT_MATTER`
- `is_front_matter_label`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `FRONT_MATTER`
- [[Reference/Modules/learnloop/daily_plan/reading|learnloop.daily_plan.reading]] — imports `is_front_matter_label`; statically calls `is_front_matter_label`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `re`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]], [[Reference/Modules/learnloop/daily_plan/reading|learnloop.daily_plan.reading]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/reading_request_sweep_helpers.py](../../../../../../../tests/reading_request_sweep_helpers.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]]
- [tests/reread_safety_helpers.py](../../../../../../../tests/reread_safety_helpers.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]]
- [tests/test_auto_build_spend_report.py](../../../../../../../tests/test_auto_build_spend_report.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]]
- [tests/test_decider_landing.py](../../../../../../../tests/test_decider_landing.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]]
- [tests/test_exam_protection_landing.py](../../../../../../../tests/test_exam_protection_landing.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]]
- [tests/test_followups_batch7_note_titles.py](../../../../../../../tests/test_followups_batch7_note_titles.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]]
- [tests/test_glm_ocr.py](../../../../../../../tests/test_glm_ocr.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]]
- [tests/test_keep_local_retired.py](../../../../../../../tests/test_keep_local_retired.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]]
- [tests/test_plan_first_transport.py](../../../../../../../tests/test_plan_first_transport.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]]
- [tests/test_plan_first_transport_offer_grants_r5.py](../../../../../../../tests/test_plan_first_transport_offer_grants_r5.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]]
- [tests/test_reading_hardening_2_fixes.py](../../../../../../../tests/test_reading_hardening_2_fixes.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]]
- [tests/test_reading_hardening_review_fixes.py](../../../../../../../tests/test_reading_hardening_review_fixes.py) — imports consumer [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]]

## Modification guidance

- Change front matter policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/sources/front_matter.py](../../../../../../../src/learnloop/content/sources/front_matter.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
