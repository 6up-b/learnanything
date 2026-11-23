---
title: "learnloop.companion.search"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/companion/search.py"
source_paths:
  - "src/learnloop/companion/search.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.companion"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.companion.search module"
  - "src/learnloop/companion/search.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-companion"
---

# `learnloop.companion.search`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/companion/_package|learnloop.companion]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.companion.search` exists within [[Reference/Modules/learnloop/companion/_package|learnloop.companion]] to own the behavior summarized by its module contract: Search in context (spec §9.3): the groups found by the learner's words, at once.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/companion/search.py](../../../../../../src/learnloop/companion/search.py) |
| Source lines | 345 |
| Owning package | [[Reference/Modules/learnloop/companion/_package|learnloop.companion]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `words_of(query: str | None) -> str` ([source](../../../../../../src/learnloop/companion/search.py), line 54)
- `snippet(text: str | None, words: str) -> str` ([source](../../../../../../src/learnloop/companion/search.py), line 62)
- `group(name: str, rows: list[dict[str, Any]], *, more: bool, basis: str='words') -> dict[str, Any]` ([source](../../../../../../src/learnloop/companion/search.py), line 77)
- `off_group(name: str, reason: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/companion/search.py), line 81) — A group that could not be searched, said so (never shown as "nothing found").
- `class SourceIds` ([source](../../../../../../src/learnloop/companion/search.py), line 88) — A reading's source, looked up once per search.
  - `__init__(self, repository: Any) -> None` (line 91; internal)
  - `__call__(self, extraction_id: str) -> str | None` (line 95; internal)
- `source_ref(source_id: str | None, extraction_id: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/companion/search.py), line 103)
- `sources_group(repository: Any, connection: Any, words: str, desk_id: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/companion/search.py), line 132) — Library sources whose title holds the words, with the desks each is open on.
- `pads_group(connection: Any, words: str, desk_id: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/companion/search.py), line 158) — Standing pad blocks whose text holds the words (removed blocks and archived pads excluded).
- `threads_group(connection: Any, words: str, source_ids: SourceIds) -> dict[str, Any]` ([source](../../../../../../src/learnloop/companion/search.py), line 214) — Reader exchanges whose question or answer holds the words, each with its thread (§7.8).
- `exchanges_group(repository: Any, words: str, source_ids: SourceIds) -> dict[str, Any]` ([source](../../../../../../src/learnloop/companion/search.py), line 239) — Every past exchange whose question or answer holds the words (the history's query), newest first.
- `gap_rows(connection: Any, words: str, source_ids: SourceIds) -> tuple[list[dict[str, Any]], bool]` ([source](../../../../../../src/learnloop/companion/search.py), line 259) — The learner's own words LearnLoop read for a gap (stuck answers, workbench text, lesson turns and the like), whose words no other group shows.
- `cue_starts(repository: Any, keys: Iterable[tuple[str, str]]) -> dict[tuple[str, str], float]` ([source](../../../../../../src/learnloop/companion/search.py), line 288) — The start time of each passage that is a transcript cue (its block is ``t=<start>-<end>``), so a video result opens at its moment; a book passage has none.
- `passage_row(hit: dict[str, Any], cue_start: float | None, *, basis: str='words') -> dict[str, Any]` ([source](../../../../../../src/learnloop/companion/search.py), line 309) — A library search hit as a result row: a video opens at its cue, a book at its passage.
- `word_groups(repository: Any, words: str, *, desk_id: str | None, scopes: Iterable[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/companion/search.py), line 324) — The groups this module searches, by name, for the scopes asked (``gaps`` is the notes group's part).

### Module constants

- `GROUP_ROWS` ([src/learnloop/companion/search.py](../../../../../../src/learnloop/companion/search.py), line 30)
- `MIN_QUERY_CHARS` ([src/learnloop/companion/search.py](../../../../../../src/learnloop/companion/search.py), line 32)
- `MAX_QUERY_CHARS` ([src/learnloop/companion/search.py](../../../../../../src/learnloop/companion/search.py), line 34)
- `MAX_THREAD_DEPTH` ([src/learnloop/companion/search.py](../../../../../../src/learnloop/companion/search.py), line 36)
- `_SNIPPET_RADIUS` ([src/learnloop/companion/search.py](../../../../../../src/learnloop/companion/search.py), line 37)
- `_CUE_TIME` ([src/learnloop/companion/search.py](../../../../../../src/learnloop/companion/search.py), line 38)
- `_GAP_KINDS_ELSEWHERE` ([src/learnloop/companion/search.py](../../../../../../src/learnloop/companion/search.py), line 41)
- `_ANCHOR_RANK` ([src/learnloop/companion/search.py](../../../../../../src/learnloop/companion/search.py), line 42)
- `LABELS` ([src/learnloop/companion/search.py](../../../../../../src/learnloop/companion/search.py), line 44)

### Explicit exports

`__all__` declares:

- `GROUP_ROWS`
- `LABELS`
- `MAX_QUERY_CHARS`
- `MIN_QUERY_CHARS`
- `SourceIds`
- `cue_starts`
- `group`
- `off_group`
- `passage_row`
- `snippet`
- `source_ref`
- `word_groups`
- `words_of`

## Internal implementation anchors

- `_like(words: str) -> str` ([source](../../../../../../src/learnloop/companion/search.py), line 58)
- `_rows(connection: Any, sql: str, params: Iterable[Any]=()) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/companion/search.py), line 71)
- `_open_windows(connection: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/companion/search.py), line 109) — The content of every open window on an open desk, with its desk.
- `_source_title(repository: Any, artifact: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/companion/search.py), line 126)
- `_thread_roots(connection: Any, question_event_ids: list[str]) -> dict[str, tuple[str, str]]` ([source](../../../../../../src/learnloop/companion/search.py), line 178) — Each Reader exchange's answer event and the root of the branch it is on, by question event id.
- `_parent(payload_json: Any) -> str | None` ([source](../../../../../../src/learnloop/companion/search.py), line 205)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/search|learnloop_sidecar.handlers.search]] — imports `module`; statically calls `SourceIds`, `cue_starts`, `group`, `off_group`, `passage_row`, `source_ref`, `word_groups`, `words_of`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/companion/history|learnloop.companion.history]] — imports `companion_history`; calls `companion_history`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/span_projection_reads|learnloop.db.stores.span_projection_reads]] — imports `module`; calls `rows_for`
- [[Reference/Modules/learnloop/substrate/passage_spans|learnloop.substrate.passage_spans]] — imports `READER_ANSWER_QUESTION_KEY`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `json`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/search|learnloop_sidecar.handlers.search]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/search|learnloop_sidecar.handlers.search]]
- [tests/test_reader_rd3a_search.py](../../../../../../tests/test_reader_rd3a_search.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/search|learnloop_sidecar.handlers.search]]

## Modification guidance

- Make changes here when the responsibility remains search within learnloop.companion; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/companion/search.py](../../../../../../src/learnloop/companion/search.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
