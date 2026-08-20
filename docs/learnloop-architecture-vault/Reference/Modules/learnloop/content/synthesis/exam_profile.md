---
title: "learnloop.content.synthesis.exam_profile"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/exam_profile.py"
source_paths:
  - "src/learnloop/content/synthesis/exam_profile.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.synthesis"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.content.synthesis.exam_profile module"
  - "src/learnloop/content/synthesis/exam_profile.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.exam_profile`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.exam_profile` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Deterministic exam profile aggregation (spec_source_ingestion_v2 §7, §4.2).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/exam_profile.py](../../../../../../../src/learnloop/content/synthesis/exam_profile.py) |
| Source lines | 187 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `exam_family_key(metadata: Mapping[str, Any] | None) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/exam_profile.py), line 35) — Deterministic same-syllabus-family key (§4.2 near-duplicate collapse).
- `class ExamProfile` ([source](../../../../../../../src/learnloop/content/synthesis/exam_profile.py), line 58)
  - `as_dict(self) -> dict[str, Any]` (line 69; public)
- `class ExamUnitEntry` ([source](../../../../../../../src/learnloop/content/synthesis/exam_profile.py), line 84) — One selected exam unit: its inventory plus its paper metadata.
- `aggregate_exam_profile(entries: Sequence[ExamUnitEntry]) -> ExamProfile` ([source](../../../../../../../src/learnloop/content/synthesis/exam_profile.py), line 92) — Aggregate exam-unit inventories into a deterministic profile (§7).
- `profile_hash(profile: ExamProfile) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/exam_profile.py), line 181) — Deterministic hash of the profile content for cache identity.

### Module constants

- `_WS` ([src/learnloop/content/synthesis/exam_profile.py](../../../../../../../src/learnloop/content/synthesis/exam_profile.py), line 23)
- `_UNKEYED_FAMILY` ([src/learnloop/content/synthesis/exam_profile.py](../../../../../../../src/learnloop/content/synthesis/exam_profile.py), line 28)

## Internal implementation anchors

- `_norm(text: Any) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/exam_profile.py), line 31)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/synthesis/source_coverage|learnloop.content.synthesis.source_coverage]] — imports `ExamUnitEntry`, `aggregate_exam_profile`; statically calls `ExamUnitEntry`, `aggregate_exam_profile`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `ExamUnitEntry`, `aggregate_exam_profile`; statically calls `ExamUnitEntry`, `aggregate_exam_profile`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/synthesis/source_coverage|learnloop.content.synthesis.source_coverage]], [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_source_inventory.py](../../../../../../../tests/test_source_inventory.py) — direct import
  - `test_exam_family_key_ignores_year`
  - `test_same_family_exam_papers_collapse_to_one_vote`

## Modification guidance

- Change exam profile policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/exam_profile.py](../../../../../../../src/learnloop/content/synthesis/exam_profile.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
