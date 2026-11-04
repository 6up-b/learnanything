---
title: "learnloop.diagnosis.split.snapshot"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/split/snapshot.py"
source_paths:
  - "src/learnloop/diagnosis/split/snapshot.py"
source_commit: "a1ba732a86f8c704cd6e6ee1071bf7a30ad3fb1a"
source_commit_timestamp: "2026-11-04T08:47:30-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.split"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.split.snapshot module"
  - "src/learnloop/diagnosis/split/snapshot.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-split"
---

# `learnloop.diagnosis.split.snapshot`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.split.snapshot` exists within [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] to own the behavior summarized by its module contract: The ``snapshot`` history mode's as-of export (Slice 1 §5.6).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/split/snapshot.py](../../../../../../../src/learnloop/diagnosis/split/snapshot.py) |
| Source lines | 380 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `a1ba732a86f8c704cd6e6ee1071bf7a30ad3fb1a` |
| Commit timestamp | `2026-11-04T08:47:30-05:00` |

## Public API

- `class SnapshotManifest` ([source](../../../../../../../src/learnloop/diagnosis/split/snapshot.py), line 47)
  - `file_count(self) -> int` (line 59; public)
  - `as_receipt(self) -> dict[str, Any]` (line 62; public)
  - `as_context_note(self) -> dict[str, Any]` (line 71; public) — What the inline context says about the workspace (no learner text).
- `render_attempt(attempt: HistoryAttempt, title: str) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/snapshot.py), line 102)
- `export_snapshot(vault: LoadedVault, store: HistoryStore, before: AttemptRef, destination: Path) -> SnapshotManifest` ([source](../../../../../../../src/learnloop/diagnosis/split/snapshot.py), line 240) — Write the as-of export into an empty ``destination`` directory.
- `snapshot_workspace(vault: LoadedVault, store: HistoryStore, before: AttemptRef, *, parent: Path | None=None) -> Iterator[SnapshotManifest]` ([source](../../../../../../../src/learnloop/diagnosis/split/snapshot.py), line 358) — A fresh export that is always deleted, on success or failure.

### Module constants

- `SNAPSHOT_EXPORT_VERSION` ([src/learnloop/diagnosis/split/snapshot.py](../../../../../../../src/learnloop/diagnosis/split/snapshot.py), line 38)
- `_UNSAFE` ([src/learnloop/diagnosis/split/snapshot.py](../../../../../../../src/learnloop/diagnosis/split/snapshot.py), line 39)

### Explicit exports

`__all__` declares:

- `SNAPSHOT_EXPORT_VERSION`
- `SnapshotManifest`
- `export_snapshot`
- `render_attempt`
- `snapshot_workspace`

## Internal implementation anchors

- `_safe(value: str) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/snapshot.py), line 42)
- `_bullets(rows: list[tuple[str, Any]]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/snapshot.py), line 91)
- `_render_hypothesis(record: HypothesisRecord) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/snapshot.py), line 152)
- `_render_registry(record: RegistryRecord) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/snapshot.py), line 178)
- `_render_repairs(facet: str, records: list[RepairRecord]) -> str` ([source](../../../../../../../src/learnloop/diagnosis/split/snapshot.py), line 201)
- `_render_graph(vault: LoadedVault) -> tuple[str, set[str]]` ([source](../../../../../../../src/learnloop/diagnosis/split/snapshot.py), line 213)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]] — imports `snapshot_workspace`; statically calls `snapshot_workspace`
- [[Reference/Modules/learnloop/diagnosis/split/diagnoser|learnloop.diagnosis.split.diagnoser]] — imports `snapshot_workspace`; statically calls `snapshot_workspace`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/diagnosis/split/context|learnloop.diagnosis.split.context]] — imports `KnownIds`; calls `KnownIds`
- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `AttemptRef`, `HistoryAttempt`, `HistoryStore`, `HypothesisRecord`, `RegistryRecord`, `RepairRecord`
- [[Reference/Modules/learnloop/diagnosis/split/provenance|learnloop.diagnosis.split.provenance]] — imports `DiagnosisReads`, `SnapshotEntries`, `attempt_read`, `freeze_entries`, `hypothesis_read`, `registry_read`, `repair_read`, `shown_titles`; calls `DiagnosisReads`, `SnapshotEntries`, `attempt_read`, `freeze_entries`, `hypothesis_read`, `registry_read`, `repair_read`, `shown_titles`
- [[Reference/Modules/learnloop/followup_serve/marks|learnloop.followup_serve.marks]] — imports `opinion_block`; calls `opinion_block`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `learning_object_facet_union`; calls `learning_object_facet_union`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `dataclasses`, `hashlib`, `json`, `pathlib`, `re`, `shutil`, `tempfile`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]], [[Reference/Modules/learnloop/diagnosis/split/diagnoser|learnloop.diagnosis.split.diagnoser]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_chatgpt_plan_workspace.py](../../../../../../../tests/test_chatgpt_plan_workspace.py) — direct import
  - `test_served_paths_map_to_export_entries_under_input_provenance`
- [tests/test_diagnosis_history_modes.py](../../../../../../../tests/test_diagnosis_history_modes.py) — direct import
  - `test_snapshot_export_is_as_of_and_stripped`
  - `test_snapshot_workspace_is_deleted_on_success_and_on_failure`
- [tests/test_followup_fg1c_codex_review.py](../../../../../../../tests/test_followup_fg1c_codex_review.py) — direct import
  - `test_f1_the_snapshot_entry_of_a_marked_attempt_carries_the_cause`

## Modification guidance

- Change snapshot policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/split/snapshot.py](../../../../../../../src/learnloop/diagnosis/split/snapshot.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
