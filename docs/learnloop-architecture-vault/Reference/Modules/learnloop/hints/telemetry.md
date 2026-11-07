---
title: "learnloop.hints.telemetry"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/hints/telemetry.py"
source_paths:
  - "src/learnloop/hints/telemetry.py"
source_commit: "3e98c165d53a3ded31844c9970bb462d0c71404e"
source_commit_timestamp: "2026-11-06T23:32:44-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.hints"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.hints.telemetry module"
  - "src/learnloop/hints/telemetry.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-hints"
---

# `learnloop.hints.telemetry`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.hints.telemetry` exists within [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] to own the behavior summarized by its module contract: Adaptive hints H0: authored-hint reveals as ``help_assists`` rows.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/hints/telemetry.py](../../../../../../src/learnloop/hints/telemetry.py) |
| Source lines | 202 |
| Owning package | [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `3e98c165d53a3ded31844c9970bb462d0c71404e` |
| Commit timestamp | `2026-11-06T23:32:44-05:00` |

## Public API

- `class RevealRecord` ([source](../../../../../../src/learnloop/hints/telemetry.py), line 39)
  - `as_dict(self) -> dict[str, Any]` (line 44; public)
- `telemetry_enabled(config: Any) -> bool` ([source](../../../../../../src/learnloop/hints/telemetry.py), line 48)
- `work_digest(work_md: str) -> tuple[str, int]` ([source](../../../../../../src/learnloop/hints/telemetry.py), line 52) — The draft's sha256 and length: the row keeps these, never the text.
- `reveal_instant(client_value: str | None, *, now: datetime) -> str` ([source](../../../../../../src/learnloop/hints/telemetry.py), line 62) — When the hint was shown: the client's press time (the sidecar answers one request at a time, so a reveal sent while another call runs would be stamped late), unless it is missing, malformed or ahead of the sidecar's clock; then the sidecar's own time.
- `record_authored_reveal(repository: Any, *, item: Any, session_id: str, submission_id: str, authored_index: int, work_md: str, revealed_at: str | None=None, now: datetime | None=None, surface: str='practice') -> RevealRecord` ([source](../../../../../../src/learnloop/hints/telemetry.py), line 78) — One ``help_assists`` row for an authored hint the practice screen showed.
- `stamp_submission(repository: Any, *, submission_id: str, practice_item_id: str, latency_seconds: float | None=None, now: datetime | None=None) -> str` ([source](../../../../../../src/learnloop/hints/telemetry.py), line 125) — When the submission reached the sidecar, before any grading (the end of "hint shown -> submit"; ``practice_attempts.created_at`` is stamped after the grader), with the open-to-submit latency the same submission sent.
- `stamp_window_submission(repository: Any, *, practice_item_id: str, session_id: str, since: str | None, submitted_at: str) -> int` ([source](../../../../../../src/learnloop/hints/telemetry.py), line 149) — The same submit time on the answer box's rows a workbench submission folds by the window (H2b re-review F9, fix round 3 ruling R1; :func:`store.stamp_window_submitted`: first stamp kept, no latency, as the problem's latency is not on their basis).
- `attach_reveals_to_attempt(repository: Any, *, submission_id: str, practice_item_id: str, attempt_id: str, submitted_at: str | None=None, latency_seconds: float | None=None) -> int` ([source](../../../../../../src/learnloop/hints/telemetry.py), line 169) — Fill ``attempt_id`` on the rows recorded under the submission key (and the submit time with its latency where the stamp was not made).

### Module constants

- `AUTHORED_LEVEL` ([src/learnloop/hints/telemetry.py](../../../../../../src/learnloop/hints/telemetry.py), line 32)
- `_CLIENT_CLOCK_AHEAD` ([src/learnloop/hints/telemetry.py](../../../../../../src/learnloop/hints/telemetry.py), line 35)

### Explicit exports

`__all__` declares:

- `AUTHORED_LEVEL`
- `RevealRecord`
- `attach_reveals_to_attempt`
- `record_authored_reveal`
- `reveal_instant`
- `stamp_submission`
- `stamp_window_submission`
- `telemetry_enabled`
- `work_digest`

## Internal implementation anchors

- `_iso_ms(instant: datetime) -> str` ([source](../../../../../../src/learnloop/hints/telemetry.py), line 58)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `attach_reveals_to_attempt`, `record_authored_reveal`, `stamp_submission`, `stamp_window_submission`, `telemetry_enabled`; statically calls `attach_reveals_to_attempt`, `record_authored_reveal`, `stamp_submission`, `stamp_window_submission`, `telemetry_enabled`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `SystemClock`, `parse_utc`; calls `SystemClock`, `parse_utc`
- [[Reference/Modules/learnloop/db/stores/help_assists|learnloop.db.stores.help_assists]] — imports `module`; calls `attach_submission`, `insert_assist`, `kept_draft`, `stamp_submitted`, `stamp_window_submitted`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `practice_item_hash`; calls `practice_item_hash`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `hashlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_help_assist_work_md_migration.py](../../../../../../tests/test_help_assist_work_md_migration.py) — direct import
  - `test_an_authored_reveal_keeps_the_draft`
- [tests/test_hint_service.py](../../../../../../tests/test_hint_service.py) — direct import
  - `test_authored_hints_the_client_revealed_are_not_served_again`
- [tests/test_hint_telemetry.py](../../../../../../tests/test_hint_telemetry.py) — direct import
  - `test_work_digest_keeps_only_a_hash_and_a_length`

## Modification guidance

- Make changes here when the responsibility remains telemetry within learnloop.hints; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/hints/telemetry.py](../../../../../../src/learnloop/hints/telemetry.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
