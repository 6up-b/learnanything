---
title: "learnloop.db.stores.session_ownership"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/session_ownership.py"
source_paths:
  - "src/learnloop/db/stores/session_ownership.py"
source_commit: "0048ada3be44b48136e2f7be0ce1d4eb666912be"
source_commit_timestamp: "2026-10-27T15:49:04-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.db.stores.session_ownership module"
  - "src/learnloop/db/stores/session_ownership.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.session_ownership`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.session_ownership` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Mobile PR-4: atomic session operations and ownership (migration 226).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/session_ownership.py](../../../../../../../src/learnloop/db/stores/session_ownership.py) |
| Source lines | 363 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `0048ada3be44b48136e2f7be0ce1d4eb666912be` |
| Commit timestamp | `2026-10-27T15:49:04-04:00` |

## Public API

- `class SessionOwnershipError(Exception)` ([source](../../../../../../../src/learnloop/db/stores/session_ownership.py), line 42) — A session operation refused by its owner or its state.
  - `__init__(self, code: str, message: str, details: Mapping[str, Any] | None=None) -> None` (line 52; internal)
- `class SessionOwnershipStoreMixin` ([source](../../../../../../../src/learnloop/db/stores/session_ownership.py), line 70) — Repository methods for session ownership; every write is one transaction.
  - `device_label(self, device_id: str | None) -> str` (line 75; public) — The label the learner gave a device; ``desktop`` for NULL.
  - `session_owner_snapshot(self, session: Mapping[str, Any]) -> dict[str, Any]` (line 84; public) — What a client shows about a session another device holds (§6.5): its owner, its current item, and whether a draft exists, with the draft's first line.
  - `session_handoffs(self, session_id: str) -> list[dict[str, Any]]` (line 104; public)
  - `require_session_owner(self, session_id: str, device_id: str | None, *, require_open: bool=True, expected_generation: int | None=None) -> dict[str, Any]` (line 119; public) — The session row, if ``device_id`` owns it; ``session_moved`` otherwise.
  - `start_session_exclusive(self, fields: Mapping[str, Any], owner_device_id: str | None, replace: str | None=None, *, settle_checkpoint: Callable[[dict[str, Any]], None] | None=None, clock: Clock | None=None) -> str` (line 160; public) — Start the one open session for ``owner_device_id`` (§6.5, PR-4).
  - `adopt_session(self, session_id: str, owner_device_id: str | None, expected_generation: int, *, current_item_ineligible: Callable[[str], bool] | None=None, clock: Clock | None=None) -> dict[str, Any]` (line 245; public) — Move an open session to ``owner_device_id`` (§6.5, PR-4).
  - `end_session_owned(self, session_id: str, device_id: str | None, *, clear: Callable[[str], Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` (line 317; public) — End a session its owner ends, in one transaction (§6.5, PR-4).
  - `_record_handoff(self, *, session_id: str, kind: str, from_device_id: str | None, to_device_id: str | None, generation: int, checkpoint: Mapping[str, Any] | None, at: str) -> str` (line 341; internal)

### Module constants

- `DESKTOP_LABEL` ([src/learnloop/db/stores/session_ownership.py](../../../../../../../src/learnloop/db/stores/session_ownership.py), line 37)
- `DRAFT_PREVIEW_CHARS` ([src/learnloop/db/stores/session_ownership.py](../../../../../../../src/learnloop/db/stores/session_ownership.py), line 39)

## Internal implementation anchors

- `_same_owner(left: str | None, right: str | None) -> bool` ([source](../../../../../../../src/learnloop/db/stores/session_ownership.py), line 59)
- `_draft_text(checkpoint: Mapping[str, Any] | None) -> str` ([source](../../../../../../../src/learnloop/db/stores/session_ownership.py), line 63)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `SessionOwnershipStoreMixin`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `SessionOwnershipError`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]], [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_session_ownership.py](../../../../../../../tests/test_session_ownership.py) — direct import
  - `test_a_retried_replacement_never_ends_the_session_it_created`
  - `test_a_start_from_another_device_never_ends_the_open_session_silently`
  - `test_adopt_is_a_compare_and_swap_that_carries_the_session_and_its_checkpoint`
  - `test_adopting_never_loses_a_draft_on_an_item_the_device_cannot_answer`
  - `test_two_devices_adopting_at_once_leave_one_owner`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/session_ownership.py](../../../../../../../src/learnloop/db/stores/session_ownership.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
