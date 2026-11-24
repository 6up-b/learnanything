---
title: "learnloop.intent.inline_checks"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/intent/inline_checks.py"
source_paths:
  - "src/learnloop/intent/inline_checks.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.intent"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.intent.inline_checks module"
  - "src/learnloop/intent/inline_checks.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-intent"
---

# `learnloop.intent.inline_checks`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.intent.inline_checks` exists within [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] to own the behavior summarized by its module contract: Reader workbench v2 inline checks, the reads (spec §3.4, §12.6.1): the due delayed checks with their hosts (:func:`due_checks`, for the server's own use: the goal lens, the begun card), and the desks' opaque handles (:func:`due_handles`, ``checks.due_for``'s reply, and :func:`re…

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/intent/inline_checks.py](../../../../../../src/learnloop/intent/inline_checks.py) |
| Source lines | 262 |
| Owning package | [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `serving_view(vault: Any, repository: Any, *, clock: Clock | None=None) -> Any` ([source](../../../../../../src/learnloop/intent/inline_checks.py), line 108) — The serving view the check reads below share (one build answers both).
- `next_check_due(view: Any) -> str | None` ([source](../../../../../../src/learnloop/intent/inline_checks.py), line 115) — When the next check not due yet falls due (a UTC stamp), or None: a reader of the due checks (the goal band, which hides what a due check covers) reads again then.
- `due_checks(vault: Any, repository: Any, *, goal_id: str | None=None, learning_object_ids: Iterable[str] | None=None, extraction_id: str | None=None, span_id: str | None=None, clock: Clock | None=None, view: Any | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/intent/inline_checks.py), line 124) — Every due check, one row per (check, learning object), oldest due first, filtered.
- `answered_checks(vault: Any, repository: Any, *, since: str, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/intent/inline_checks.py), line 170) — Every "Check once" answered on the learner's own since ``since`` (a UTC stamp), one row per (check, learning object): the goal band fills its ◇ once a check is answered.
- `new_handle_key() -> None` ([source](../../../../../../src/learnloop/intent/inline_checks.py), line 212) — Draw a new key, as a sidecar's start does: every handle minted before is dead (``check_unknown``).
- `handle_of(commitment_id: str, administrations: int) -> str` ([source](../../../../../../src/learnloop/intent/inline_checks.py), line 219)
- `due_handles(vault: Any, repository: Any, *, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/intent/inline_checks.py), line 224) — ``checks.due_for``'s rows: one opaque handle per due check, every due check in the vault (a filter by goal, reading or passage would itself say where it is), in the handles' own order (the due order could be recalled).
- `resolve_handle(vault: Any, repository: Any, handle: str, *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/intent/inline_checks.py), line 239) — The due check a handle names now, or None (spent, stale, from another sidecar run, or guessed).

### Module constants

- `_HANDLE_KEY` ([src/learnloop/intent/inline_checks.py](../../../../../../src/learnloop/intent/inline_checks.py), line 208)
- `HANDLE_PREFIX` ([src/learnloop/intent/inline_checks.py](../../../../../../src/learnloop/intent/inline_checks.py), line 209)

### Explicit exports

`__all__` declares:

- `answered_checks`
- `due_checks`
- `due_handles`
- `handle_of`
- `new_handle_key`
- `next_check_due`
- `resolve_handle`
- `serving_view`

## Internal implementation anchors

- `class _Sections` ([source](../../../../../../src/learnloop/intent/inline_checks.py), line 31) — Each reading's sections, loaded once per call.
- `_path_host(connection: Any, goal_id: str, lo_id: str) -> tuple[str, str] | None` ([source](../../../../../../src/learnloop/intent/inline_checks.py), line 56)
- `_primary_passage(connection: Any, lo_id: str) -> tuple[str, str] | None` ([source](../../../../../../src/learnloop/intent/inline_checks.py), line 69)
- `_host(connection: Any, sections: _Sections, lo_id: str, goal_id: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/intent/inline_checks.py), line 80)
- `_provenance(provenance: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/intent/inline_checks.py), line 96) — Who made the check, in one word: its ``via`` (or ``origin``) and nothing else.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/intent/inline_administration|learnloop.intent.inline_administration]] — imports `_Sections`, `_primary_passage`; statically calls `_Sections`, `_primary_passage`
- [[Reference/Modules/learnloop_sidecar/handlers/goal_lens|learnloop_sidecar.handlers.goal_lens]] — imports `answered_checks`, `due_checks`, `next_check_due`, `serving_view`; statically calls `answered_checks`, `due_checks`, `next_check_due`, `serving_view`
- [[Reference/Modules/learnloop_sidecar/handlers/inline_checks|learnloop_sidecar.handlers.inline_checks]] — imports `due_checks`, `due_handles`, `resolve_handle`; statically calls `due_checks`, `due_handles`, `resolve_handle`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/stores/check_administrations|learnloop.db.stores.check_administrations]] — imports `module`; calls `administration_counts`, `open_administration`, `table_present`
- [[Reference/Modules/learnloop/scheduling/intent/resolution|learnloop.scheduling.intent.resolution]] — imports `load_snapshots`; calls `load_snapshots`
- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `intent_serving`; calls `intent_serving`
- [[Reference/Modules/learnloop/section_map|learnloop.section_map]] — imports `extraction_sections`; calls `extraction_sections`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `hashlib`, `hmac`, `secrets`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/intent/inline_administration|learnloop.intent.inline_administration]], [[Reference/Modules/learnloop_sidecar/handlers/goal_lens|learnloop_sidecar.handlers.goal_lens]], [[Reference/Modules/learnloop_sidecar/handlers/inline_checks|learnloop_sidecar.handlers.inline_checks]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rd0_reads.py](../../../../../../tests/test_reader_rd0_reads.py) — direct import
  - `test_due_checks_name_their_host_and_nothing_of_the_item`
- [tests/test_reader_rd7_unlocated_marker.py](../../../../../../tests/test_reader_rd7_unlocated_marker.py) — direct import
  - `test_a_handle_dies_with_the_sidecar_and_a_new_read_recovers`
  - `test_due_for_answers_a_handle_and_nothing_of_the_check`
- [tests/test_reader_rd7a_inline_checks.py](../../../../../../tests/test_reader_rd7a_inline_checks.py) — direct import
  - `test_one_administration_at_a_time_and_today_honours_it`

## Modification guidance

- Make changes here when the responsibility remains inline checks within learnloop.intent; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/intent/inline_checks.py](../../../../../../src/learnloop/intent/inline_checks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
