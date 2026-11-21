---
title: "learnloop.reader.seen_passages"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/seen_passages.py"
source_paths:
  - "src/learnloop/reader/seen_passages.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.seen_passages module"
  - "src/learnloop/reader/seen_passages.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.seen_passages`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.seen_passages` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Which passages the learner's own reading observed, and where it reached a section's end (migration 256).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/seen_passages.py](../../../../../../src/learnloop/reader/seen_passages.py) |
| Source lines | 130 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class CheckedReport` ([source](../../../../../../src/learnloop/reader/seen_passages.py), line 33) — A report's passages, kept: those that are readable passages of its section, in reading order, once each; the section's end when its last passage is seen; and how many named ids were left out.
- `check_report(repository: Any, *, extraction_id: str, section_id: str, seen_span_ids: list[str] | None, reached_end: bool) -> CheckedReport` ([source](../../../../../../src/learnloop/reader/seen_passages.py), line 42) — Keep the passages a report names that are readable passages of its section on its reading.
- `class SeenPassage` ([source](../../../../../../src/learnloop/reader/seen_passages.py), line 78) — One passage of a reading with exact seen evidence: where it was observed (``observed_on``: the reading and span the report named), when first and by which device.
- `seen_on(repository: Any, extraction_id: str) -> dict[str, SeenPassage]` ([source](../../../../../../src/learnloop/reader/seen_passages.py), line 88) — Every passage of ``extraction_id`` with exact seen evidence, by span id.
- `class SectionEnd` ([source](../../../../../../src/learnloop/reader/seen_passages.py), line 116) — A section of a reading whose last readable passage (``span_id``) the learner's own reading reached.
- `section_ends_on(repository: Any, extraction_id: str) -> list[SectionEnd]` ([source](../../../../../../src/learnloop/reader/seen_passages.py), line 125) — The sections of ``extraction_id`` whose end was reached, on that reading only (another reading's sections are other sections).

### Module constants

- `ORIGINS` ([src/learnloop/reader/seen_passages.py](../../../../../../src/learnloop/reader/seen_passages.py), line 26)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `check_report`; statically calls `check_report`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/span_aliases|learnloop.content.sources.span_aliases]] — imports `SpanTranslator`, `other_readings`; calls `SpanTranslator`, `other_readings`
- [[Reference/Modules/learnloop/section_map|learnloop.section_map]] — imports `extraction_sections`; calls `extraction_sections`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_seen_passages.py](../../../../../../tests/test_reader_seen_passages.py) — direct import
  - `test_an_exact_alias_carries_a_seen_passage_to_a_reread_and_a_changed_one_does_not`
  - `test_section_ends_are_read_on_their_own_reading_only`

## Modification guidance

- Change seen passages policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/seen_passages.py](../../../../../../src/learnloop/reader/seen_passages.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
