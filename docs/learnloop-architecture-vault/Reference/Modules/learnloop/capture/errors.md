---
title: "learnloop.capture.errors"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/capture/errors.py"
source_paths:
  - "src/learnloop/capture/errors.py"
source_commit: "3fde02bfe8f284fbd1cf59c96d0659d9b00fb130"
source_commit_timestamp: "2026-10-11T23:13:46-04:00"
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
  - "learnloop.capture.errors module"
  - "src/learnloop/capture/errors.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-capture"
---

# `learnloop.capture.errors`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.capture.errors` exists within [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] to own the behavior summarized by its module contract: Stable domain errors shared by the HTTP, CLI and desktop adapters.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/capture/errors.py](../../../../../../src/learnloop/capture/errors.py) |
| Source lines | 10 |
| Owning package | [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `3fde02bfe8f284fbd1cf59c96d0659d9b00fb130` |
| Commit timestamp | `2026-10-11T23:13:46-04:00` |

## Public API

- `class CaptureError(ValueError)` ([source](../../../../../../src/learnloop/capture/errors.py), line 4)
  - `__init__(self, code: str, status: int, message: str)` (line 5; internal)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]] — imports `CaptureError`
- [[Reference/Modules/learnloop/capture/devices|learnloop.capture.devices]] — imports `CaptureError`; statically calls `CaptureError`
- [[Reference/Modules/learnloop/capture/inbox|learnloop.capture.inbox]] — imports `CaptureError`; statically calls `CaptureError`
- [[Reference/Modules/learnloop/capture/maintenance|learnloop.capture.maintenance]] — imports `CaptureError`; statically calls `CaptureError`
- [[Reference/Modules/learnloop/capture/routing|learnloop.capture.routing]] — imports `CaptureError`; statically calls `CaptureError`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: none imported directly
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]], [[Reference/Modules/learnloop/capture/devices|learnloop.capture.devices]], [[Reference/Modules/learnloop/capture/inbox|learnloop.capture.inbox]], [[Reference/Modules/learnloop/capture/maintenance|learnloop.capture.maintenance]], [[Reference/Modules/learnloop/capture/routing|learnloop.capture.routing]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_capture_desktop.py](../../../../../../tests/test_capture_desktop.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_capture_domain.py](../../../../../../tests/test_capture_domain.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_capture_originals_race.py](../../../../../../tests/test_capture_originals_race.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_capture_route_recovery.py](../../../../../../tests/test_capture_route_recovery.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_mobile_host_auth.py](../../../../../../tests/test_mobile_host_auth.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_mobile_host_coexistence.py](../../../../../../tests/test_mobile_host_coexistence.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_mobile_pairing.py](../../../../../../tests/test_mobile_pairing.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_reader_ca1_as_printed.py](../../../../../../tests/test_reader_ca1_as_printed.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/notes_fixtures.py](../../../../../../tests/notes_fixtures.py) — imports consumer [[Reference/Modules/learnloop/capture/inbox|learnloop.capture.inbox]]

## Modification guidance

- Make changes here when the responsibility remains errors within learnloop.capture; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/capture/errors.py](../../../../../../src/learnloop/capture/errors.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
