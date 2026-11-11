---
title: "learnloop.adaptive_difficulty.denial_log"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/denial_log.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/denial_log.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.adaptive_difficulty.denial_log module"
  - "src/learnloop/adaptive_difficulty/denial_log.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.denial_log`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.denial_log` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: The AD guard's denial log (``ad_guard_denials.jsonl`` beside the vault database).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/denial_log.py](../../../../../../src/learnloop/adaptive_difficulty/denial_log.py) |
| Source lines | 306 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `denial_log_path(sqlite_path: Any) -> Path` ([source](../../../../../../src/learnloop/adaptive_difficulty/denial_log.py), line 74) — The guard's denial log, beside the vault database.
- `append_denials(sqlite_path: Any, denials: Iterable[Mapping[str, Any]], *, epoch: Any, entry: str | None) -> None` ([source](../../../../../../src/learnloop/adaptive_difficulty/denial_log.py), line 98) — Append one line per denial, with the operation's epoch and entry point.
- `denial_count(sqlite_path: Any) -> int` ([source](../../../../../../src/learnloop/adaptive_difficulty/denial_log.py), line 129) — The live log's lines (denials since the last upgrade began); 0 without a log.
- `archived_logs(sqlite_path: Any) -> list[Path]` ([source](../../../../../../src/learnloop/adaptive_difficulty/denial_log.py), line 146) — The archives earlier upgrades left beside the database, oldest name first.
- `summary(sqlite_path: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/denial_log.py), line 163) — ``ad report``'s guard block: the live log's count and its count by entry point, and the archives' counts (file names and line counts only; a line's content is never shown).
- `class Cutover` ([source](../../../../../../src/learnloop/adaptive_difficulty/denial_log.py), line 184) — The live log as an upgrade command found it: its identity and length (``None``/0: no log).
- `cutover_mark(sqlite_path: Any) -> Cutover` ([source](../../../../../../src/learnloop/adaptive_difficulty/denial_log.py), line 191) — Mark the live log at an upgrade command's start (under the log lock, so the length ends at a whole append).
- `archive_denial_log(sqlite_path: Any, *, from_version: str, to_version: str, mark: Cutover | None, now: datetime | None=None) -> Path | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/denial_log.py), line 243) — Move the lines the live log held at ``mark`` to a dated archive beside it; None when the mark found no log, or the log there now is a later one (another archival moved the marked lines).

### Module constants

- `LOG_NAME` ([src/learnloop/adaptive_difficulty/denial_log.py](../../../../../../src/learnloop/adaptive_difficulty/denial_log.py), line 64)
- `LOCK_NAME` ([src/learnloop/adaptive_difficulty/denial_log.py](../../../../../../src/learnloop/adaptive_difficulty/denial_log.py), line 65)
- `_ARCHIVE_PREFIX` ([src/learnloop/adaptive_difficulty/denial_log.py](../../../../../../src/learnloop/adaptive_difficulty/denial_log.py), line 66)
- `UNRECORDED` ([src/learnloop/adaptive_difficulty/denial_log.py](../../../../../../src/learnloop/adaptive_difficulty/denial_log.py), line 69)
- `UNREADABLE` ([src/learnloop/adaptive_difficulty/denial_log.py](../../../../../../src/learnloop/adaptive_difficulty/denial_log.py), line 71)

### Explicit exports

`__all__` declares:

- `LOCK_NAME`
- `LOG_NAME`
- `UNREADABLE`
- `UNRECORDED`
- `Cutover`
- `append_denials`
- `archive_denial_log`
- `archived_logs`
- `cutover_mark`
- `denial_count`
- `denial_log_path`
- `summary`

## Internal implementation anchors

- `_log_lock(sqlite_path: Any) -> Iterator[None]` ([source](../../../../../../src/learnloop/adaptive_difficulty/denial_log.py), line 81) — The log's leaf lock (see the module docstring).
- `_ends_with_newline(path: Path) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/denial_log.py), line 116)
- `_lines(path: Path) -> list[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/denial_log.py), line 122)
- `_entry_of(line: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/denial_log.py), line 135)
- `_snapshot(sqlite_path: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/denial_log.py), line 156)
- `_stamp(now: datetime | None) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/denial_log.py), line 203)
- `_safe(version: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/denial_log.py), line 208)
- `_remove(path: Path) -> None` ([source](../../../../../../src/learnloop/adaptive_difficulty/denial_log.py), line 212)
- `_fsync_write(path: Path, data: bytes, *, exclusive: bool) -> None` ([source](../../../../../../src/learnloop/adaptive_difficulty/denial_log.py), line 219) — Write every byte of ``data`` to ``path`` and fsync it, or raise (Codex verify 2: ``os.write`` may write a prefix and return its length).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `append_denials`, `denial_count`; statically calls `append_denials`
- [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]] — imports `module`; statically calls `summary`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `archive_denial_log`, `cutover_mark`; statically calls `archive_denial_log`, `cutover_mark`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `datetime`, `errno`, `fcntl`, `json`, `os`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]], [[Reference/Modules/learnloop/adaptive_difficulty/report|learnloop.adaptive_difficulty.report]], [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad_denial_log_helpers.py](../../../../../../tests/ad_denial_log_helpers.py) — direct import
- [tests/test_ad_denial_log.py](../../../../../../tests/test_ad_denial_log.py) — direct import
  - `test_a_new_denial_line_names_the_refused_operation`
  - `test_a_second_upgrade_never_overwrites_the_first_archive`
  - `test_a_successful_upgrade_archives_the_log_and_the_report_counts_from_zero`
  - `test_an_archive_name_already_taken_gets_a_counter`
  - `test_an_upgrade_without_a_log_archives_nothing`
  - `test_append_writes_the_entry_beside_the_refusal`
  - `test_f1_a_denial_after_the_upgrade_returned_stays_live`
  - `test_f1_an_append_in_flight_never_writes_into_the_archive`
  - `test_f1_lines_appended_after_the_mark_stay_live_and_the_marked_ones_are_archived`
  - `test_f1_the_archival_waits_for_an_append_holding_the_log_lock`
  - `test_f2_a_report_never_counts_a_line_live_and_archived`
  - `test_old_format_lines_stay_readable_and_are_grouped_as_unrecorded`
  - `test_v2_a_failed_archival_never_touches_an_existing_archive`
  - `test_v2_a_failed_write_keeps_the_live_log_and_removes_what_it_created`
  - `test_v2_a_short_write_that_resumes_completes_every_byte`
  - `test_v2_f1_an_unmarked_upgrade_leaves_the_log_live`
  - `test_v2_f2_a_report_without_the_lock_does_not_count_archives`
  - `test_v3_a_replace_that_fails_without_effect_still_cleans_up`
  - `test_v3_an_interrupt_after_the_replace_keeps_the_archive`
- [tests/test_forced_withdrawal_records.py](../../../../../../tests/test_forced_withdrawal_records.py) — direct import
  - `test_a_guard_denial_is_recorded_beside_the_jsonl_log_the_report_still_reads`
- [tests/test_pr4_superseded_claims_landing.py](../../../../../../tests/test_pr4_superseded_claims_landing.py) — direct import
  - `test_landing_iii_upgrade_to_mvp037_archives_the_denial_log_exactly_once`

## Modification guidance

- Make changes here when the responsibility remains denial log within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/denial_log.py](../../../../../../src/learnloop/adaptive_difficulty/denial_log.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
