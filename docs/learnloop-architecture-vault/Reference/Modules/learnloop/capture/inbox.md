---
title: "learnloop.capture.inbox"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/capture/inbox.py"
source_paths:
  - "src/learnloop/capture/inbox.py"
source_commit: "fd203b85eab9c4a925589c804f6300d11c7dd1ed"
source_commit_timestamp: "2026-10-25T16:07:25-04:00"
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
  - "learnloop.capture.inbox module"
  - "src/learnloop/capture/inbox.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-capture"
---

# `learnloop.capture.inbox`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.capture.inbox` exists within [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] to own the behavior summarized by its module contract: Durable reference-only capture, with no ingestion or practice side effects.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/capture/inbox.py](../../../../../../src/learnloop/capture/inbox.py) |
| Source lines | 396 |
| Owning package | [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `fd203b85eab9c4a925589c804f6300d11c7dd1ed` |
| Commit timestamp | `2026-10-25T16:07:25-04:00` |

## Public API

- `validate_url(value: str) -> None` ([source](../../../../../../src/learnloop/capture/inbox.py), line 34) — Accept references, never local source paths; this function fetches nothing.
- `sanitize_image(raw: bytes) -> tuple[bytes, str]` ([source](../../../../../../src/learnloop/capture/inbox.py), line 53) — Decode before trusting MIME; orientation survives, ancillary data does not.
- `create_capture(repo: Repository, *, client_capture_id: str, kind: str, text: str | None=None, url: str | None=None, note: str | None=None, source_app: str | None=None, captured_at: str | None=None, media: bytes | None=None, device_id: str | None=None, root: Path | None=None) -> dict` ([source](../../../../../../src/learnloop/capture/inbox.py), line 102)
- `get_capture(repo: Repository, capture_id: str) -> dict` ([source](../../../../../../src/learnloop/capture/inbox.py), line 185)
- `list_captures(repo: Repository, *, status: str | None=None, limit: int=100, offset: int=0) -> list[dict]` ([source](../../../../../../src/learnloop/capture/inbox.py), line 193)
- `get_inbox_summary(repo: Repository) -> dict` ([source](../../../../../../src/learnloop/capture/inbox.py), line 214) — New captures plus every capture whose media deletion is still pending.
- `route_capture(repo: Repository, capture_id: str, *, route: str, result_refs) -> dict` ([source](../../../../../../src/learnloop/capture/inbox.py), line 233)
- `photo_for_practice_item(repo: Repository, practice_item_id: str) -> dict | None` ([source](../../../../../../src/learnloop/capture/inbox.py), line 254) — The phone photo a card was written from (Reader CA1, *your photo*): the reverse of a routed capture's link, read from its ``result_refs_json``.
- `dismiss_capture(repo: Repository, capture_id: str) -> dict` ([source](../../../../../../src/learnloop/capture/inbox.py), line 279)
- `purge_capture(repo: Repository, capture_id: str, *, root: Path | None=None) -> dict` ([source](../../../../../../src/learnloop/capture/inbox.py), line 297) — Erase capture payload but preserve its fingerprint tombstone and provenance.
- `capture_media_preview(repo: Repository, capture_id: str, *, root: Path | None=None, max_side: int=PREVIEW_MAX_SIDE) -> dict` ([source](../../../../../../src/learnloop/capture/inbox.py), line 339) — Desktop-only, read-only bounded preview of a photo capture.
- `report_orphan_originals(repo: Repository, *, root: Path | None=None) -> list[str]` ([source](../../../../../../src/learnloop/capture/inbox.py), line 387) — Read-only reporting: never remove unknown files from the shared store.

### Module constants

- `_ULID` ([src/learnloop/capture/inbox.py](../../../../../../src/learnloop/capture/inbox.py), line 24)
- `_DIGEST` ([src/learnloop/capture/inbox.py](../../../../../../src/learnloop/capture/inbox.py), line 25)
- `PREVIEW_MAX_SIDE` ([src/learnloop/capture/inbox.py](../../../../../../src/learnloop/capture/inbox.py), line 26)
- `_ARXIV` ([src/learnloop/capture/inbox.py](../../../../../../src/learnloop/capture/inbox.py), line 27)
- `_SELECT` ([src/learnloop/capture/inbox.py](../../../../../../src/learnloop/capture/inbox.py), line 28)

## Internal implementation anchors

- `_json(value) -> str` ([source](../../../../../../src/learnloop/capture/inbox.py), line 81)
- `_decode(row) -> dict` ([source](../../../../../../src/learnloop/capture/inbox.py), line 85)
- `_referenced(conn, digest: str) -> bool` ([source](../../../../../../src/learnloop/capture/inbox.py), line 289)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]] — imports `capture_media_preview`, `create_capture`, `dismiss_capture`, `get_capture`, `get_inbox_summary`, `list_captures`, `photo_for_practice_item`, `purge_capture`, `report_orphan_originals`, `route_capture`, `sanitize_image`, `validate_url`
- [[Reference/Modules/learnloop/capture/routing|learnloop.capture.routing]] — imports `get_capture`; statically calls `get_capture`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/capture/devices|learnloop.capture.devices]] — imports `_now`; calls `_now`
- [[Reference/Modules/learnloop/capture/errors|learnloop.capture.errors]] — imports `CaptureError`; calls `CaptureError`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ingest/originals|learnloop.ingest.originals]] — imports `canonical_source_raw_path`, `store_original_bytes`; calls `canonical_source_raw_path`, `store_original_bytes`

### Platform and third-party dependencies

- Standard library: `__future__`, `base64`, `datetime`, `hashlib`, `io`, `json`, `pathlib`, `re`, `urllib`, `warnings`
- Third party: `PIL`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/capture/__init__|learnloop.capture]], [[Reference/Modules/learnloop/capture/routing|learnloop.capture.routing]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/notes_fixtures.py](../../../../../../tests/notes_fixtures.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains inbox within learnloop.capture; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/capture/inbox.py](../../../../../../src/learnloop/capture/inbox.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
