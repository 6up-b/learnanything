---
title: "learnloop.diagnosis.repair_splice"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/repair_splice.py"
source_paths:
  - "src/learnloop/diagnosis/repair_splice.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.repair_splice module"
  - "src/learnloop/diagnosis/repair_splice.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.repair_splice`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.repair_splice` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Deterministic composition of a repaired trace from its stored parts.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/repair_splice.py](../../../../../../src/learnloop/diagnosis/repair_splice.py) |
| Source lines | 279 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class PreservedPrefix` ([source](../../../../../../src/learnloop/diagnosis/repair_splice.py), line 89) — The server's answer to "how much of this answer is the learner's?".
- `class SplicedAnswer` ([source](../../../../../../src/learnloop/diagnosis/repair_splice.py), line 101)
- `clause_boundaries(answer: str) -> list[int]` ([source](../../../../../../src/learnloop/diagnosis/repair_splice.py), line 109) — Offsets in ``answer`` that a preserved prefix may legitimately end at.
- `snap_prefix_end(answer: str, end: int) -> int` ([source](../../../../../../src/learnloop/diagnosis/repair_splice.py), line 135) — Snap ``end`` OUTWARD to the next clause/sentence boundary.
- `preserved_prefix_from_refs(answer: str, preserve_refs: list[Any] | None, *, before_offset: int | None=None) -> PreservedPrefix | None` ([source](../../../../../../src/learnloop/diagnosis/repair_splice.py), line 182) — Derive the preserved prefix from a suggestion's ``preserve_refs``.
- `is_end_append(repaired_trace: dict[str, Any]) -> bool` ([source](../../../../../../src/learnloop/diagnosis/repair_splice.py), line 231) — Whether the repair appends after the learner's work rather than into it.
- `splice_repaired_answer(prefix: str, regenerated: str, *, end_append: bool) -> SplicedAnswer` ([source](../../../../../../src/learnloop/diagnosis/repair_splice.py), line 259) — Compose the repaired answer, guarding the end-append junction.

### Module constants

- `PREFIX_BASES` ([src/learnloop/diagnosis/repair_splice.py](../../../../../../src/learnloop/diagnosis/repair_splice.py), line 37)
- `SPLICE_JOINS` ([src/learnloop/diagnosis/repair_splice.py](../../../../../../src/learnloop/diagnosis/repair_splice.py), line 43)
- `_SENTENCE_END` ([src/learnloop/diagnosis/repair_splice.py](../../../../../../src/learnloop/diagnosis/repair_splice.py), line 50)
- `_CLAUSE_WORDS` ([src/learnloop/diagnosis/repair_splice.py](../../../../../../src/learnloop/diagnosis/repair_splice.py), line 54)
- `_CONJUNCTION` ([src/learnloop/diagnosis/repair_splice.py](../../../../../../src/learnloop/diagnosis/repair_splice.py), line 73)
- `_PUNCT_BREAK` ([src/learnloop/diagnosis/repair_splice.py](../../../../../../src/learnloop/diagnosis/repair_splice.py), line 78)
- `_LINE_END` ([src/learnloop/diagnosis/repair_splice.py](../../../../../../src/learnloop/diagnosis/repair_splice.py), line 80)
- `_PARAGRAPH_BREAK_AT_END` ([src/learnloop/diagnosis/repair_splice.py](../../../../../../src/learnloop/diagnosis/repair_splice.py), line 82)
- `_PARAGRAPH_BREAK_AT_START` ([src/learnloop/diagnosis/repair_splice.py](../../../../../../src/learnloop/diagnosis/repair_splice.py), line 83)
- `_NEWLINE_AT_END` ([src/learnloop/diagnosis/repair_splice.py](../../../../../../src/learnloop/diagnosis/repair_splice.py), line 84)
- `_NEWLINE_AT_START` ([src/learnloop/diagnosis/repair_splice.py](../../../../../../src/learnloop/diagnosis/repair_splice.py), line 85)

## Internal implementation anchors

- `_resolved_span_end(answer: str, ref: dict[str, Any]) -> int | None` ([source](../../../../../../src/learnloop/diagnosis/repair_splice.py), line 155) — End offset of one ``answer_span`` preserve ref, quote-authoritative.
- `_has_paragraph_break(prefix: str, regenerated: str) -> bool` ([source](../../../../../../src/learnloop/diagnosis/repair_splice.py), line 249)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `is_end_append`, `preserved_prefix_from_refs`, `splice_repaired_answer`; statically calls `is_end_append`, `preserved_prefix_from_refs`, `splice_repaired_answer`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `resolve_quote_anchor`; calls `resolve_quote_anchor`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_repair_splice.py](../../../../../../tests/test_repair_splice.py) — direct import
  - `test_boundaries_never_fall_inside_a_token`
  - `test_end_append_detection_requires_an_explicit_insertion_point`
  - `test_existing_paragraph_break_is_not_doubled`
  - `test_later_preserve_ref_cannot_move_prefix_past_repair_anchor`
  - `test_non_answer_span_preserve_refs_derive_nothing`
  - `test_preserve_span_snaps_to_the_clause_not_the_whole_answer`
  - `test_quote_only_preserve_ref_is_anchored_server_side`
  - `test_snap_falls_back_to_end_of_text_when_no_boundary_follows`
  - `test_span_ending_mid_clause_snaps_outward_to_the_clause_end`

## Modification guidance

- Change repair splice policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/repair_splice.py](../../../../../../src/learnloop/diagnosis/repair_splice.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
