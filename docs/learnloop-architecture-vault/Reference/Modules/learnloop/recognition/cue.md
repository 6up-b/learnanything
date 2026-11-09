---
title: "learnloop.recognition.cue"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/recognition/cue.py"
source_paths:
  - "src/learnloop/recognition/cue.py"
source_commit: "workspace/uncommitted @ HEAD cd6759fcb9e7c6a3877c0dd019a9c37b7305f90d"
source_commit_timestamp: "2026-11-09T01:34:53-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop.recognition"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.recognition.cue module"
  - "src/learnloop/recognition/cue.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-recognition"
---

# `learnloop.recognition.cue`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/recognition/_package|learnloop.recognition]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.recognition.cue` exists within [[Reference/Modules/learnloop/recognition/_package|learnloop.recognition]] to own the behavior summarized by its module contract: RE0 §4.2: the cue label, ``attempt_cue_v1(attempt, ledger)``.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/recognition/cue.py](../../../../../../src/learnloop/recognition/cue.py) |
| Source lines | 199 |
| Owning package | [[Reference/Modules/learnloop/recognition/_package|learnloop.recognition]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD cd6759fcb9e7c6a3877c0dd019a9c37b7305f90d` |
| Commit timestamp | `2026-11-09T01:34:53-05:00` |

## Public API

- `parse(stamp: str) -> datetime` ([source](../../../../../../src/learnloop/recognition/cue.py), line 54)
- `class Exposure` ([source](../../../../../../src/learnloop/recognition/cue.py), line 59) — One exposure to a learning object: a Reader exposure or a reveal (``reading``), or a lesson's end (``lesson``).
- `class CueLedger` ([source](../../../../../../src/learnloop/recognition/cue.py), line 70) — What the label reads, as plain records.
  - `__post_init__(self) -> None` (line 89; internal)
  - `previous(self, attempt: Mapping[str, object]) -> Mapping[str, object] | None` (line 108; public) — The previous practice attempt in the attempt's session, or None.
  - `exposures_of(self, learning_object_id: str) -> tuple[Exposure, ...]` (line 124; public)
- `class AttemptCue` ([source](../../../../../../src/learnloop/recognition/cue.py), line 129) — The label: the seven fields, the fields the records could not speak to, and the cue version.
  - `present(self) -> tuple[str, ...]` (line 145; public)
  - `label(self) -> str` (line 149; public)
- `attempt_cue_v1(attempt: Mapping[str, object], ledger: CueLedger) -> AttemptCue` ([source](../../../../../../src/learnloop/recognition/cue.py), line 161) — The cues present on ``attempt`` (module docstring).
- `cues(attempts: Iterable[Mapping[str, object]], ledger: CueLedger) -> dict[str, AttemptCue]` ([source](../../../../../../src/learnloop/recognition/cue.py), line 196) — The label of each attempt, by id.

### Module constants

- `CUE_VERSION` ([src/learnloop/recognition/cue.py](../../../../../../src/learnloop/recognition/cue.py), line 40)
- `FIELDS` ([src/learnloop/recognition/cue.py](../../../../../../src/learnloop/recognition/cue.py), line 41)
- `NOT_PRACTICE` ([src/learnloop/recognition/cue.py](../../../../../../src/learnloop/recognition/cue.py), line 48)
- `IMPORTED` ([src/learnloop/recognition/cue.py](../../../../../../src/learnloop/recognition/cue.py), line 49)

## Internal implementation anchors

- `_began(attempt: Mapping[str, object]) -> datetime` ([source](../../../../../../src/learnloop/recognition/cue.py), line 155)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/recognition/ledger|learnloop.recognition.ledger]] — imports `CueLedger`, `Exposure`, `LESSON`, `READING`; statically calls `CueLedger`, `Exposure`
- [[Reference/Modules/learnloop/recognition/report|learnloop.recognition.report]] — imports `module`; statically calls `cues`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `bisect`, `collections`, `dataclasses`, `datetime`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/recognition/ledger|learnloop.recognition.ledger]], [[Reference/Modules/learnloop/recognition/report|learnloop.recognition.report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_re0_capture.py](../../../../../../tests/test_re0_capture.py) — direct import
  - `test_a_synthetic_trace_with_no_cues_present_is_uncued`
  - `test_an_unreadable_field_is_listed_and_an_imported_answer_is_unlabelled_not_uncued`
  - `test_each_cue_alone_makes_an_attempt_cued`
  - `test_the_cue_window_counts_what_happened_before_the_attempt_began_and_not_help_during_it`
  - `test_the_previous_attempt_is_the_sessions_and_a_session_less_one_reads_the_routers_gap`
  - `test_the_same_ledger_gives_the_same_label`

## Modification guidance

- Make changes here when the responsibility remains cue within learnloop.recognition; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/recognition/cue.py](../../../../../../src/learnloop/recognition/cue.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
