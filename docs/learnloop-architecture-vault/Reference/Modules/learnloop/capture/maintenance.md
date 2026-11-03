---
title: "learnloop.capture.maintenance"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/capture/maintenance.py"
source_paths:
  - "src/learnloop/capture/maintenance.py"
source_commit: "cdd578ba62529223b963e848b1ee6c8f98799ae9"
source_commit_timestamp: "2026-11-03T12:14:06-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.capture"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.capture.maintenance module"
  - "src/learnloop/capture/maintenance.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-capture"
---

# `learnloop.capture.maintenance`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.capture.maintenance` exists within [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] to own the behavior summarized by its module contract: Small capture-host maintenance operations; never sidecar startup work.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/capture/maintenance.py](../../../../../../src/learnloop/capture/maintenance.py) |
| Source lines | 60 |
| Owning package | [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `cdd578ba62529223b963e848b1ee6c8f98799ae9` |
| Commit timestamp | `2026-11-03T12:14:06-05:00` |

## Public API

- `log_request(repo: Repository, *, endpoint: str, status: int, duration_ms: float, device_id: str | None=None, now: datetime | None=None) -> None` ([source](../../../../../../src/learnloop/capture/maintenance.py), line 22)
- `prune_request_log(repo: Repository, *, now: datetime | None=None) -> int` ([source](../../../../../../src/learnloop/capture/maintenance.py), line 39)
- `pinned_vault_info(config_path: Path, current_root: Path) -> dict` ([source](../../../../../../src/learnloop/capture/maintenance.py), line 45) — Read machine routing information without importing a host entry point.

### Module constants

- `_LOG_ENDPOINTS` ([src/learnloop/capture/maintenance.py](../../../../../../src/learnloop/capture/maintenance.py), line 16)
- `_RPC_METHOD` ([src/learnloop/capture/maintenance.py](../../../../../../src/learnloop/capture/maintenance.py), line 19)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]] — imports `log_request`, `pinned_vault_info`, `prune_request_log`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/capture/devices|learnloop.capture.devices]] — imports `_now`; calls `_now`
- [[Reference/Modules/learnloop/capture/errors|learnloop.capture.errors]] — imports `CaptureError`; calls `CaptureError`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `pathlib`, `re`, `tomllib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/mobile_host_helpers.py](../../../../../../tests/mobile_host_helpers.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_capture_desktop.py](../../../../../../tests/test_capture_desktop.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_capture_domain.py](../../../../../../tests/test_capture_domain.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_capture_originals_race.py](../../../../../../tests/test_capture_originals_race.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_capture_route_recovery.py](../../../../../../tests/test_capture_route_recovery.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_mobile_handoff.py](../../../../../../tests/test_mobile_handoff.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_mobile_host_auth.py](../../../../../../tests/test_mobile_host_auth.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_mobile_host_coexistence.py](../../../../../../tests/test_mobile_host_coexistence.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_mobile_jobs.py](../../../../../../tests/test_mobile_jobs.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_mobile_pairing.py](../../../../../../tests/test_mobile_pairing.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_reader_ca1_as_printed.py](../../../../../../tests/test_reader_ca1_as_printed.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]

## Modification guidance

- Make changes here when the responsibility remains maintenance within learnloop.capture; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/capture/maintenance.py](../../../../../../src/learnloop/capture/maintenance.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
