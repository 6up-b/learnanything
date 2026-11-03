---
title: "learnloop.capture.devices"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/capture/devices.py"
source_paths:
  - "src/learnloop/capture/devices.py"
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
  - "learnloop.capture.devices module"
  - "src/learnloop/capture/devices.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-capture"
---

# `learnloop.capture.devices`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.capture.devices` exists within [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] to own the behavior summarized by its module contract: Hashed credentials and durable, serialized pairing admission.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/capture/devices.py](../../../../../../src/learnloop/capture/devices.py) |
| Source lines | 187 |
| Owning package | [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `3fde02bfe8f284fbd1cf59c96d0659d9b00fb130` |
| Commit timestamp | `2026-10-11T23:13:46-04:00` |

## Public API

- `create_pairing(repo: Repository, *, label: str='Phone', scope: str='capture', now: datetime | None=None) -> dict` ([source](../../../../../../src/learnloop/capture/devices.py), line 38)
- `exchange_pairing(repo: Repository, *, secret: str | None=None, code: str | None=None, device_label: str | None=None, tailscale_login: str | None=None, now: datetime | None=None) -> dict` ([source](../../../../../../src/learnloop/capture/devices.py), line 65)
- `authenticate_device(repo: Repository, token: str, *, scope: str='capture', now: datetime | None=None) -> dict` ([source](../../../../../../src/learnloop/capture/devices.py), line 133)
- `touch_device(repo: Repository, device_id: str, *, now: datetime | None=None) -> None` ([source](../../../../../../src/learnloop/capture/devices.py), line 152) — Persist admitted use at most once per minute, never during credential checks.
- `list_devices(repo: Repository, *, now: datetime | None=None) -> list[dict]` ([source](../../../../../../src/learnloop/capture/devices.py), line 167)
- `revoke_device(repo: Repository, device_id: str, *, now: datetime | None=None) -> dict` ([source](../../../../../../src/learnloop/capture/devices.py), line 181)

### Module constants

- `_ALPHABET` ([src/learnloop/capture/devices.py](../../../../../../src/learnloop/capture/devices.py), line 18)

## Internal implementation anchors

- `_now(now: datetime | None=None) -> datetime` ([source](../../../../../../src/learnloop/capture/devices.py), line 21)
- `_hash(value: str) -> str` ([source](../../../../../../src/learnloop/capture/devices.py), line 28)
- `_label(value: str) -> str` ([source](../../../../../../src/learnloop/capture/devices.py), line 32)
- `_expire_unclaimed(conn, at: datetime) -> None` ([source](../../../../../../src/learnloop/capture/devices.py), line 125)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]] — imports `authenticate_device`, `create_pairing`, `exchange_pairing`, `list_devices`, `revoke_device`, `touch_device`
- [[Reference/Modules/learnloop/capture/inbox|learnloop.capture.inbox]] — imports `_now`; statically calls `_now`
- [[Reference/Modules/learnloop/capture/jobs|learnloop.capture.jobs]] — imports `_now`; statically calls `_now`
- [[Reference/Modules/learnloop/capture/maintenance|learnloop.capture.maintenance]] — imports `_now`; statically calls `_now`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/capture/errors|learnloop.capture.errors]] — imports `CaptureError`; calls `CaptureError`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `hashlib`, `secrets`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]], [[Reference/Modules/learnloop/capture/inbox|learnloop.capture.inbox]], [[Reference/Modules/learnloop/capture/jobs|learnloop.capture.jobs]], [[Reference/Modules/learnloop/capture/maintenance|learnloop.capture.maintenance]].

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
- [tests/test_mobile_https.py](../../../../../../tests/test_mobile_https.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_mobile_jobs.py](../../../../../../tests/test_mobile_jobs.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_mobile_pairing.py](../../../../../../tests/test_mobile_pairing.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]
- [tests/test_reader_ca1_as_printed.py](../../../../../../tests/test_reader_ca1_as_printed.py) — imports consumer [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]]

## Modification guidance

- Make changes here when the responsibility remains devices within learnloop.capture; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/capture/devices.py](../../../../../../src/learnloop/capture/devices.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
