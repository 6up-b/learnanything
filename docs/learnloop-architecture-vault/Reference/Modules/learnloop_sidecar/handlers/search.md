---
title: "learnloop_sidecar.handlers.search"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/search.py"
source_paths:
  - "src/learnloop_sidecar/handlers/search.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.handlers.search module"
  - "src/learnloop_sidecar/handlers/search.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.search`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.search` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Reader workbench v2 RPCs: ``search.everything`` and ``search.job`` (spec §3.4, §9.3): search in context, by words at once and by meaning through a job.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/search.py](../../../../../../src/learnloop_sidecar/handlers/search.py) |
| Source lines | 369 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class SearchEverythingInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/search.py), line 58)
- `class SearchJobInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/search.py), line 67)
- `search_everything(ctx: SidecarContext, params: SearchEverythingInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/search.py), line 244) — ``{query, groups, meaning}``: the groups by words now, and the search by meaning's job or why none.
- `search_job(ctx: SidecarContext, params: SearchJobInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/search.py), line 351) — The search by meaning's state, at once (never a wait on the request path).

### Module constants

- `SEARCH_RPCS` ([src/learnloop_sidecar/handlers/search.py](../../../../../../src/learnloop_sidecar/handlers/search.py), line 44)
- `KIND` ([src/learnloop_sidecar/handlers/search.py](../../../../../../src/learnloop_sidecar/handlers/search.py), line 45)
- `_REGISTRY` ([src/learnloop_sidecar/handlers/search.py](../../../../../../src/learnloop_sidecar/handlers/search.py), line 46)
- `SCOPES` ([src/learnloop_sidecar/handlers/search.py](../../../../../../src/learnloop_sidecar/handlers/search.py), line 47)
- `NO_MEANING_INDEX` ([src/learnloop_sidecar/handlers/search.py](../../../../../../src/learnloop_sidecar/handlers/search.py), line 50)
- `_MEANING_LISTS` ([src/learnloop_sidecar/handlers/search.py](../../../../../../src/learnloop_sidecar/handlers/search.py), line 55)
- `MAX_RUNNING_SEARCHES` ([src/learnloop_sidecar/handlers/search.py](../../../../../../src/learnloop_sidecar/handlers/search.py), line 72)

### Explicit exports

`__all__` declares:

- `SCOPES`
- `SEARCH_RPCS`
- `SearchEverythingInput`

## Internal implementation anchors

- `_jobs(ctx: SidecarContext) -> PJ.PolledJobs` ([source](../../../../../../src/learnloop_sidecar/handlers/search.py), line 75)
- `_require_desk(repository: Any, desk_id: str) -> None` ([source](../../../../../../src/learnloop_sidecar/handlers/search.py), line 80)
- `_passages_state(vault: Any) -> tuple[bool, str | None]` ([source](../../../../../../src/learnloop_sidecar/handlers/search.py), line 92) — Whether the library's passages can be searched at all (the Reader and its retrieval on).
- `_passages_meaning(vault: Any, repository: Any) -> tuple[bool, str | None, str | None]` ([source](../../../../../../src/learnloop_sidecar/handlers/search.py), line 102) — (searchable by meaning, why not, coverage label): the library's stored passage vectors.
- `_passage_rows(repository: Any, hits: list[dict[str, Any]], *, basis: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/search.py), line 118)
- `_note_row(hit: dict[str, Any], source_ids: CS.SourceIds, *, basis: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/search.py), line 124) — A vault note as a result row that opens it: a Reader note or highlight at its passage in its book (``ref`` the source, ``target`` the passage and the note), a capture-inbox note in the notes panel (``target`` the note).
- `_word_groups(ctx: SidecarContext, vault: Any, repository: Any, words: str, desk_id: str | None, scopes: list[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/search.py), line 145)
- `_seen_keys(groups: list[dict[str, Any]]) -> dict[str, set[str]]` ([source](../../../../../../src/learnloop_sidecar/handlers/search.py), line 178) — What the words found, by group, so a meaning result repeats none of it.
- `_meaning_group(name: str, rows: list[dict[str, Any]], *, more: bool, status: str='ok', reason: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/search.py), line 191) — A group found by meaning; ``status`` ``unavailable`` or ``failed`` says why it holds nothing, so an unrun search is never shown as "nothing found".
- `_passages_by_meaning(vault: Any, repository: Any, words: str, seen: set[str], coverage: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/search.py), line 203)
- `_notes_by_meaning(ctx: SidecarContext, vault: Any, repository: Any, words: str, seen: set[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/search.py), line 224)
- `_job_payload(job: PJ.PolledJob) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/search.py), line 328)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/model_use|learnloop.ai.model_use]] — imports `module`; calls `waiting`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `relay_job_offer`
- [[Reference/Modules/learnloop/companion/search|learnloop.companion.search]] — imports `module`; calls `SourceIds`, `cue_starts`, `group`, `off_group`, `passage_row`, `source_ref`, `word_groups`, `words_of`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/desks|learnloop.db.stores.desks]] — imports `module`; calls `desk`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; calls `reader_enabled`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `library_scope`; calls `library_scope`
- [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]] — imports `meaning_search_state`, `search_library`; calls `meaning_search_state`, `search_library`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/notes|learnloop_sidecar.handlers.notes]] — imports `notes_search_state`, `search_vault_notes`; calls `notes_search_state`, `search_vault_notes`
- [[Reference/Modules/learnloop_sidecar/polled_jobs|learnloop_sidecar.polled_jobs]] — imports `module`; calls `as_job_error`, `registry`, `vault_key`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`
- [[Reference/Modules/learnloop_sidecar/workbench_protection|learnloop_sidecar.workbench_protection]] — imports `PassageSelection`, `block_places`, `reading_places`, `refuse_protected`; calls `block_places`, `reading_places`, `refuse_protected`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mobile_allowlist.py](../../../../../../tests/test_mobile_allowlist.py) — direct import
  - `test_the_pinned_rd3a_rpcs_are_all_of_them`
- [tests/test_reader_rd3a_search.py](../../../../../../tests/test_reader_rd3a_search.py) — direct import
  - `test_the_rpcs_are_registered_desktop_only_and_refuse_extra_fields`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/search.py](../../../../../../src/learnloop_sidecar/handlers/search.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
