---
title: "learnloop.diagnosis.missing_vocabulary"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/missing_vocabulary.py"
source_paths:
  - "src/learnloop/diagnosis/missing_vocabulary.py"
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
  - "learnloop.diagnosis.missing_vocabulary module"
  - "src/learnloop/diagnosis/missing_vocabulary.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.missing_vocabulary`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.missing_vocabulary` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Missing-vocabulary notes: the system's record of what it could not name.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/missing_vocabulary.py](../../../../../../src/learnloop/diagnosis/missing_vocabulary.py) |
| Source lines | 465 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `record_missing_vocabulary_notes(repository: Repository, notes: Sequence[Mapping[str, Any]], *, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/diagnosis/missing_vocabulary.py), line 133) — Append notes, skipping ones already recorded.
- `diagnostic_abstention_notes(repository: Repository, *, attempt_id: str, selected_repair_class_id: str | None=None, repair_equivalence_id: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/missing_vocabulary.py), line 162) — Build one note per abstaining attribution on an attempt.
- `record_diagnostic_abstention_notes(repository: Repository, *, attempt_id: str, selected_repair_class_id: str | None=None, repair_equivalence_id: str | None=None, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/diagnosis/missing_vocabulary.py), line 243)
- `authoring_facet_abstention_notes(payload: Mapping[str, Any], *, practice_item_id: str | None=None, detail: Mapping[str, Any] | None=None, version_stamps: Mapping[str, Any] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/missing_vocabulary.py), line 268) — Notes for the criteria of one authored item that named no canonical facet.
- `record_authoring_facet_abstention_notes(repository: Repository, items: Sequence[Mapping[str, Any]], *, patch_id: str | None=None, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/diagnosis/missing_vocabulary.py), line 338) — Capture facet abstentions from accepted proposal items (§5.8 rule 4).
- `missing_vocabulary_report(repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/missing_vocabulary.py), line 414) — Note counts by source and reason, plus the diagnostic abstention RATE.

### Module constants

- `MISSING_VOCABULARY_NOTE_VERSION` ([src/learnloop/diagnosis/missing_vocabulary.py](../../../../../../src/learnloop/diagnosis/missing_vocabulary.py), line 41)
- `NOTE_SOURCES` ([src/learnloop/diagnosis/missing_vocabulary.py](../../../../../../src/learnloop/diagnosis/missing_vocabulary.py), line 43)
- `FACET_ABSTAINING_STATUSES` ([src/learnloop/diagnosis/missing_vocabulary.py](../../../../../../src/learnloop/diagnosis/missing_vocabulary.py), line 51)

## Internal implementation anchors

- `_content_id(value: Any) -> str` ([source](../../../../../../src/learnloop/diagnosis/missing_vocabulary.py), line 54)
- `_version_stamps(repository: Repository, attempt_id: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/missing_vocabulary.py), line 61) — The A4 version set, read from durable rows plus in-force constants.
- `_note_id(note: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/diagnosis/missing_vocabulary.py), line 102) — Content-address a note over what makes it the same refusal.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `missing_vocabulary_report`; statically calls `missing_vocabulary_report`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `record_authoring_facet_abstention_notes`; statically calls `record_authoring_facet_abstention_notes`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `record_diagnostic_abstention_notes`; statically calls `record_diagnostic_abstention_notes`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `missing_vocabulary_report`; statically calls `missing_vocabulary_report`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/ai_contracts|learnloop.attempts.ai_contracts]] — imports `GRADING_PROMPT_VERSION`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/content/proposals/ai_contracts|learnloop.content.proposals.ai_contracts]] — imports `AUTHORING_PROMPT_VERSION`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `CAUSAL_DECISION_POLICY_VERSION`, `REPAIR_POLICY_VERSION`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]], [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]], [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_missing_vocabulary_notes.py](../../../../../../tests/test_missing_vocabulary_notes.py) — direct import
  - `test_authoring_facet_abstention_notes_read_the_criteria`
  - `test_authoring_note_carries_the_proposal_run_version_set`
  - `test_diagnostic_abstention_writes_a_note`
  - `test_notes_are_append_only_and_reject_untyped_refusals`
  - `test_report_surfaces_the_abstention_rate`

## Modification guidance

- Change missing vocabulary policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/missing_vocabulary.py](../../../../../../src/learnloop/diagnosis/missing_vocabulary.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
