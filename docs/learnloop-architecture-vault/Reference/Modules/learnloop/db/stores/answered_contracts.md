---
title: "learnloop.db.stores.answered_contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/answered_contracts.py"
source_paths:
  - "src/learnloop/db/stores/answered_contracts.py"
source_commit: "2d7c4948399efdc96c3c60d7379da37bc90a9e3d"
source_commit_timestamp: "2026-10-14T20:18:37-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.stores.answered_contracts module"
  - "src/learnloop/db/stores/answered_contracts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.answered_contracts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.answered_contracts` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: The question each answer was graded under (method-explicit-3 review F3).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/answered_contracts.py](../../../../../../../src/learnloop/db/stores/answered_contracts.py) |
| Source lines | 74 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `2d7c4948399efdc96c3c60d7379da37bc90a9e3d` |
| Commit timestamp | `2026-10-14T20:18:37-04:00` |

## Public API

- `answered_contracts(connection: sqlite3.Connection, attempt_ids: Iterable[str] | None=None) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/answered_contracts.py), line 28) — ``{attempt id: {"prompt": ..., "required_method": ...}}`` for each attempt (every attempt when ``attempt_ids`` is None) whose evidence cites an assessment contract: the frozen statement, and the frozen required method (``{"name", "criterion_ids"}``) or None.

### Module constants

- `_CHUNK` ([src/learnloop/db/stores/answered_contracts.py](../../../../../../../src/learnloop/db/stores/answered_contracts.py), line 19)

### Explicit exports

`__all__` declares:

- `answered_contracts`

## Internal implementation anchors

- `_table(connection: sqlite3.Connection, name: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/answered_contracts.py), line 22)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `answered_contracts`; statically calls `answered_contracts`
- [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]] — imports `answered_contracts`; statically calls `answered_contracts`
- [[Reference/Modules/learnloop/reader/reader_cues|learnloop.reader.reader_cues]] — imports `answered_contracts`; statically calls `answered_contracts`
- [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]] — imports `answered_contracts`; statically calls `answered_contracts`
- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `answered_contracts`; statically calls `answered_contracts`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]], [[Reference/Modules/learnloop/diagnosis/split/live|learnloop.diagnosis.split.live]], [[Reference/Modules/learnloop/reader/reader_cues|learnloop.reader.reader_cues]], [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]], [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_chatgpt_plan_workspace.py](../../../../../../../tests/test_chatgpt_plan_workspace.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]]
- [tests/test_codex_lockdown_round3.py](../../../../../../../tests/test_codex_lockdown_round3.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]]
- [tests/test_diagnosis_context.py](../../../../../../../tests/test_diagnosis_context.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]]
- [tests/test_diagnosis_contract.py](../../../../../../../tests/test_diagnosis_contract.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]]
- [tests/test_diagnosis_history_modes.py](../../../../../../../tests/test_diagnosis_history_modes.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]]
- [tests/test_diagnosis_input_provenance.py](../../../../../../../tests/test_diagnosis_input_provenance.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]]
- [tests/test_learner_blindness_relax.py](../../../../../../../tests/test_learner_blindness_relax.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]]
- [tests/test_learner_text_gaps.py](../../../../../../../tests/test_learner_text_gaps.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]]
- [tests/test_pfc_unassessed_readers.py](../../../../../../../tests/test_pfc_unassessed_readers.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]]
- [tests/test_required_method_round3_review.py](../../../../../../../tests/test_required_method_round3_review.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]]
- [tests/test_ro1_availability_reads.py](../../../../../../../tests/test_ro1_availability_reads.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]]
- [tests/test_ro1_projection.py](../../../../../../../tests/test_ro1_projection.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/answered_contracts.py](../../../../../../../src/learnloop/db/stores/answered_contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
