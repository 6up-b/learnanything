---
title: "learnloop.diagnosis.probe_remint"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/probe_remint.py"
source_paths:
  - "src/learnloop/diagnosis/probe_remint.py"
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
  - "learnloop.diagnosis.probe_remint module"
  - "src/learnloop/diagnosis/probe_remint.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.probe_remint`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.probe_remint` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Learner-initiated remint: keep an administered diagnostic probe as practice.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probe_remint.py](../../../../../../src/learnloop/diagnosis/probe_remint.py) |
| Source lines | 318 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ProbeRemintError(ValueError)` ([source](../../../../../../src/learnloop/diagnosis/probe_remint.py), line 78) — Invalid remint request, with a stable code for the sidecar boundary.
  - `__init__(self, code: str, message: str, *, details: dict[str, Any] | None=None)` (line 81; internal)
- `remint_practice_mode(item: PracticeItem) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_remint.py), line 87) — Deterministic ordinary mode from the probe's shape.
- `remint_attempt_types(item: PracticeItem) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/probe_remint.py), line 106) — The ordinary attempt-type set: the probe's own set minus the diagnostic administration type, with a real answering type guaranteed.
- `existing_remint(vault: LoadedVault, source_practice_item_id: str) -> PracticeItem | None` ([source](../../../../../../src/learnloop/diagnosis/probe_remint.py), line 121) — The already-minted remint of this probe, if any (provenance query).
- `remint_probe_as_practice_item(root: Path, vault: LoadedVault, repository: Repository, *, attempt_id: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_remint.py), line 225) — Mint the ordinary practice-item copy of one administered probe.

### Module constants

- `_LOGGER` ([src/learnloop/diagnosis/probe_remint.py](../../../../../../src/learnloop/diagnosis/probe_remint.py), line 62)
- `REMINT_ORIGIN` ([src/learnloop/diagnosis/probe_remint.py](../../../../../../src/learnloop/diagnosis/probe_remint.py), line 65)
- `REMINT_TAG` ([src/learnloop/diagnosis/probe_remint.py](../../../../../../src/learnloop/diagnosis/probe_remint.py), line 68)
- `DIAGNOSTIC_ONLY_TAGS` ([src/learnloop/diagnosis/probe_remint.py](../../../../../../src/learnloop/diagnosis/probe_remint.py), line 71)
- `_NON_ANSWERING_ATTEMPT_TYPES` ([src/learnloop/diagnosis/probe_remint.py](../../../../../../src/learnloop/diagnosis/probe_remint.py), line 75)

## Internal implementation anchors

- `_remint_payload(source: PracticeItem, *, new_id: str, attempt_id: str, now_iso: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_remint.py), line 140) — Mechanical copy of the probe's content + measurement contract.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]] — imports `ProbeRemintError`, `remint_probe_as_practice_item`; statically calls `remint_probe_as_practice_item`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `practice_item_hash`; calls `practice_item_hash`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `upsert_practice_item`; calls `upsert_practice_item`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `logging`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_probe_remint.py](../../../../../../tests/test_probe_remint.py) — direct import
  - `test_remint_guards`
  - `test_remint_is_idempotent_and_points_at_the_existing_remint`

## Modification guidance

- Change probe remint policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/probe_remint.py](../../../../../../src/learnloop/diagnosis/probe_remint.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
