---
title: "learnloop.source_retrieval.kept_comparisons"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/kept_comparisons.py"
source_paths:
  - "src/learnloop/source_retrieval/kept_comparisons.py"
source_commit: "0105c383a8986a3532f28326aaea4ea09a3695e6"
source_commit_timestamp: "2026-10-27T20:54:11-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.source_retrieval.kept_comparisons module"
  - "src/learnloop/source_retrieval/kept_comparisons.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.kept_comparisons`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.kept_comparisons` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Keep this comparison (reader workbench RW4d; spec_reader_workbench_v1 §7.8).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/kept_comparisons.py](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py) |
| Source lines | 1590 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `0105c383a8986a3532f28326aaea4ea09a3695e6` |
| Commit timestamp | `2026-10-27T20:54:11-04:00` |

## Public API

- `keep_enabled(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 139) — Keep is on: its own switch and everything RW4a's compare needs.
- `tutor_keep_enabled(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 145) — Keep on the tutor's comparison (RW1c's offer): the keep switch, the Reader's compare switch and the service's comparison, without requiring the library answer (the tutor's offer does not go through it).
- `coarse_relation(fine: str, left_type: str, right_type: str) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 156) — §3.4 item 15's mapping; None for a label it does not know (not kept).
- `max_perspectives(vault: LoadedVault) -> int` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 164) — The most views a comparison asks for and keeps (``reader_compare.max_perspectives``).
- `by_point_enabled(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 170) — Reader CA4 is on: its switch and the comparison it builds on.
- `clean_perspectives(values: Sequence[str] | None, *, limit: int) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 176) — The requested perspectives as typed: trimmed, distinct, at most ``limit``.
- `held_out_now(vault: LoadedVault, repository: Repository, keys: Sequence[tuple[str, str]]) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 232) — Whether any of ``keys`` is exam or held-out material now.
- `is_by_point(stored: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 361) — A stored comparison by point (``source_compare.v2``, with its points).
- `cell_key(passage_key: str, point_id: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 372) — A kept cell's key: its passage and its row (a passage holds one cell per row).
- `take_key(keys: Sequence[str], text: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 531) — A take's idempotency key: its passages (in order) and its words, as kept.
- `kept_state(kept: Mapping[str, Any] | None, *, kept_at: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 840) — What the Reader shows of a keep: ids, types and fine labels, the takes (no quotes).
- `kept_ask(repository: Repository, ask_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 997) — An ask's caller, comparison and keep state (``not_found`` when unknown).
- `live_keep_of(repository: Repository, comparison_id: str | None, *, prefer: str | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 1029) — The row that keeps ``comparison_id`` now, whichever ask holds it: the ask named by ``prefer`` when it does, else the earliest live keep of that comparison (any caller).
- `keep(vault: LoadedVault, repository: Repository, ask_id: str, *, comparison_id: str | None=None, takes: Sequence[Mapping[str, Any]]=(), clock: Clock | None=None, guard: RowGuard | None=None, hidden_points: Sequence[str] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 1050) — Keep a library ask's comparison (the learner pressed *keep comparison*), or add a take to it once kept.
- `compare_kept_state(vault: LoadedVault, repository: Repository, ask_id: str, comparison_id: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 1108) — Whether the comparison just shown is the one this ask keeps (for the table).
- `tutor_comparison(repository: Repository, tool_call_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 1121) — The tutor's comparison request and its latest successful run (what was shown).
- `keep_tutor(vault: LoadedVault, repository: Repository, tool_call_id: str, *, extraction_id: str | None=None, takes: Sequence[Mapping[str, Any]]=(), clock: Clock | None=None, guard: RowGuard | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 1137) — Keep the tutor's comparison (RW1c's *how do your books treat this?*, pressed and shown).
- `remove(vault: LoadedVault, repository: Repository, ask_id: str, *, comparison_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 1193) — *Remove*: the keep's proposals are superseded (append-only), never deleted.
- `relation_lineage(repository: Repository) -> dict[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 1237) — Each superseded successor relation id -> the relation id it supersedes (RW4d's removals and CA4's hidden rows are the only writers of relation successors).
- `relation_head(repository: Repository, relation_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 1254) — The current head of a relation's lineage (itself while nothing supersedes it).
- `kept_marks(vault: LoadedVault, repository: Repository, extraction_id: str, *, available: Callable[[Mapping[str, Any]], bool] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 1270) — The ``⇄`` marks for one reading: each span with a live kept comparison (the learner's own mark, outside the cue budget).
- `reopen(vault: LoadedVault, repository: Repository, ask_id: str, *, open_source_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 1322) — The table of a kept comparison, rebuilt from the stored row (no model call), showing only what was kept; refused while any of it is held out.
- `compared_on(vault: LoadedVault, repository: Repository, keys: Sequence[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 1448) — For a later library ask: the kept comparisons sharing its passages ("you compared these on 3 Oct"), newest first; none withheld whole.
- `kept_comparisons_for_card(vault: LoadedVault, repository: Repository, *, learning_object_ids: Sequence[str], as_of: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 1494) — Kept comparisons on these LOs (for RW6b's ``reader_activity_for_card``, spec §9.4): a pure, deterministic read of ``library_asks.kept_json``, typed, with no prose and no quotes.

### Module constants

- `RELATION_MAP` ([src/learnloop/source_retrieval/kept_comparisons.py](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 112)
- `TAKE_RELATION` ([src/learnloop/source_retrieval/kept_comparisons.py](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 121)
- `MAX_TAKE_CHARS` ([src/learnloop/source_retrieval/kept_comparisons.py](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 123)
- `MAX_TAKES` ([src/learnloop/source_retrieval/kept_comparisons.py](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 124)
- `MAX_PERSPECTIVE_CHARS` ([src/learnloop/source_retrieval/kept_comparisons.py](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 128)
- `BY_POINT_LAYOUT` ([src/learnloop/source_retrieval/kept_comparisons.py](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 130)
- `KEPT_VERSION` ([src/learnloop/source_retrieval/kept_comparisons.py](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 131)
- `EVENTS` ([src/learnloop/source_retrieval/kept_comparisons.py](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 133)
- `_SNAPSHOT_FIELDS` ([src/learnloop/source_retrieval/kept_comparisons.py](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 1187)
- `_POINT_SNAPSHOT_FIELDS` ([src/learnloop/source_retrieval/kept_comparisons.py](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 1190)

### Explicit exports

`__all__` declares:

- `EVENTS`
- `BY_POINT_LAYOUT`
- `by_point_enabled`
- `cell_key`
- `is_by_point`
- `max_perspectives`
- `RELATION_MAP`
- `RowGuard`
- `TAKE_RELATION`
- `clean_perspectives`
- `coarse_relation`
- `compare_kept_state`
- `compared_on`
- `held_out_now`
- `keep`
- `keep_enabled`
- `keep_tutor`
- `kept_ask`
- `kept_comparisons_for_card`
- `live_keep_of`
- `kept_marks`
- `kept_state`
- `relation_head`
- `relation_lineage`
- `remove`
- `reopen`
- `take_key`
- `tutor_comparison`
- `tutor_keep_enabled`

## Internal implementation anchors

- `_withheld_rows(vault: LoadedVault, repository: Repository, rows: Sequence[Mapping[str, Any]]) -> frozenset[str]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 187) — The ids of ``rows`` whose comparison is withheld whole: any passage that contributed to it is held out now, or its provenance cannot be resolved (``reader.source_objects.withheld_comparisons``, failing closed).
- `_key(entry: Mapping[str, Any]) -> tuple[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 199)
- `_entry_keys(entry: Mapping[str, Any]) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 203) — Every block of a compared passage: one, or (Reader CA3, Codex review F4) an anchor's blocks in the learner's order, its first naming it.
- `_holder(claim: Mapping[str, Any], quote: str) -> tuple[str, str] | None` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 214) — The block of a claim's passage that holds ``quote`` (first in order).
- `_key_str(key: tuple[str, str]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 220)
- `_event(repository: Repository, event: str, payload: Mapping[str, Any], *, subject_id: str | None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 224)
- `_comparison_withheld() -> LibraryAskError` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 246)
- `_refuse_comparison(vault: LoadedVault, repository: Repository, comparison_id: str | None, *, ask_id: str | None=None, question_event_id: str | None=None, keys: Sequence[tuple[str, str]]=(), ask_ids: Sequence[str]=(), question_event_ids: Sequence[str]=()) -> None` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 253) — Refuse (``comparison_withheld``) unless every passage that contributed to the comparison is readable now: its sources, counterparts, unverified sources and dropped pins, the ask's anchor and binding, the tutor question's passages (``reader.source_objects.comparison_passages``) a…
- `_stored(repository: Repository, comparison_id: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 277)
- `_sources(stored: Mapping[str, Any], shown: Sequence[str] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 287) — The stored comparison's compared sources (only those shown, when named).
- `_relations(stored: Mapping[str, Any], refs: set[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 297)
- `_plan(vault: LoadedVault, repository: Repository, stored: Mapping[str, Any], sources: Sequence[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 302) — What a keep would write, checked against the books as they are now (no writes).
- `_points(stored: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 368)
- `_plan_by_point(vault: LoadedVault, repository: Repository, stored: Mapping[str, Any], sources: Sequence[Mapping[str, Any]], *, hidden: set[str], only: set[str] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 378) — Reader CA4: what a keep by point would write (no writes), one claim per quoted cell of every row not hidden (``only``: just those rows), each quote rechecked against the block of its passage as it is now, and each row's verified relations between that row's two kept claims.
- `_write_cells(repository: Repository, *, ask: Mapping[str, Any], stored: Mapping[str, Any], plan: Mapping[str, Any], provenance: Mapping[str, Any], clock: Clock | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 446) — Reader CA4: the proposals of a keep by point (one claim per cell, the row's label in ``content_json``; each row's relations between its claims).
- `_passage_keys(objects: Sequence[Mapping[str, Any]]) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 494)
- `_quote_of(claim: Mapping[str, Any], relations: Sequence[Mapping[str, Any]]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 498)
- `_take_parts(take: Mapping[str, Any]) -> tuple[list[str], str]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 509)
- `_take_target(take: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 514) — Reader CA4: what a take by point is about: ``point:<id>`` (a row) or ``comparison`` (the whole table); None for a take on passages (v1).
- `_point_take_key(take: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 525)
- `_kept_take_key(take: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 539)
- `_resolve_point_take(take: Mapping[str, Any], objects: Sequence[Mapping[str, Any]]) -> tuple[str, str | None, str, list[str]]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 543) — A take by point: the row's first two kept claims (by column), or for the whole comparison its first two claims from different books; one alone when that is all there is.
- `_check_point_takes(takes: Sequence[Mapping[str, Any]], objects: Sequence[Mapping[str, Any]], *, kept_takes: Sequence[Mapping[str, Any]]=()) -> list[Mapping[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 579) — ``_check_takes`` for a keep by point: every take names a kept row (or the whole comparison); the ones not kept yet, within the limit.
- `_resolve_take(take: Mapping[str, Any], objects: Mapping[str, Mapping[str, Any]]) -> tuple[str, str | None, str]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 598)
- `_check_takes(takes: Sequence[Mapping[str, Any]], keys: Sequence[str], *, kept_takes: Sequence[Mapping[str, Any]]=()) -> list[Mapping[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 609) — Every take is valid against the claims that will be kept (before any write); returns the ones not kept yet (a replayed take is not new, so a replay at the limit succeeds), refusing when those would pass the limit.
- `_add_takes(repository: Repository, kept: dict[str, Any], takes: Sequence[Mapping[str, Any]], *, clock: Clock | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 630)
- `_add_point_takes(repository: Repository, kept: dict[str, Any], takes: Sequence[Mapping[str, Any]], *, clock: Clock | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 651)
- `_learning_objects_of(vault: LoadedVault, repository: Repository, objects: Sequence[Mapping[str, Any]], learning_object_ids: Sequence[str]) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 670) — The LOs the card reads a keep under: the question's own (its anchor, or the tutor request's), then each kept passage's provenance-linked LOs.
- `_write_by_point(vault: LoadedVault, repository: Repository, *, ask: Mapping[str, Any], stored: Mapping[str, Any], plan: Mapping[str, Any], caller: str, clock: Clock | None, hidden: Sequence[str], learning_object_ids: Sequence[str]=()) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 684) — Reader CA4: write a keep by point and return its kept_json.
- `_set_hidden(vault: LoadedVault, repository: Repository, ask: Mapping[str, Any], kept: dict[str, Any], hidden: Sequence[str], *, clock: Clock | None) -> dict[str, int]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 704) — Reader CA4 (§5.2): hide or show rows of a keep by point.
- `_take_object_ids(repository: Repository, take: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 766)
- `_write(vault: LoadedVault, repository: Repository, *, ask: Mapping[str, Any], stored: Mapping[str, Any], plan: Mapping[str, Any], caller: str, clock: Clock | None, learning_object_ids: Sequence[str]=()) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 773) — Write the proposals (through reader.source_objects) and return kept_json.
- `_save(repository: Repository, ask_id: str, kept: Mapping[str, Any] | None, *, kept_at: str | None) -> None` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 833)
- `_contributors(repository: Repository, kept: Mapping[str, Any], *, ask_id: str, acting_ask_id: str | None, question_event_id: str | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 866) — The keep's recorded contributors with those of this moment added: the ask acting now (when another ask owns the keep), the tutor question acting now, and the question each contributing ask holds **now** (the owner's, the acting ask's, every recorded ask's).
- `_keep(vault: LoadedVault, repository: Repository, ask: Mapping[str, Any], *, shown: Sequence[str] | None, takes: Sequence[Mapping[str, Any]], caller: str, clock: Clock | None, question_event_id: str | None=None, acting_ask_id: str | None=None, hidden_points: Sequence[str] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 895)
- `_question_learning_objects(repository: Repository, ask: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 978)
- `_row(repository: Repository, ask_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 987)
- `_stale() -> LibraryAskError` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 1003)
- `_fork_for(repository: Repository, row: Mapping[str, Any], comparison_id: str, *, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 1009) — The row that keeps ``comparison_id`` for this question, forked when none does.
- `_with_keeps(repository: Repository) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 1230) — Every ask that has kept a comparison, live or removed since.
- `_live(repository: Repository) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 1265)
- `_relation_signature(rel: Mapping[str, Any], fine: Any) -> tuple[Any, ...]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 1317)
- `_reopen_by_point(stored: Mapping[str, Any], kept: Mapping[str, Any], *, open_source_id: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 1352) — Reader CA4: a keep by point reopened by point.
- `_reopen_by_book(stored: Mapping[str, Any], kept: Mapping[str, Any], *, open_source_id: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 1399) — A keep reopened by book (RW4d's table): its claims with their kept lines and its kept relations.
- `_episodes(row: Mapping[str, Any]) -> list[tuple[dict[str, Any], str, str | None]]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 1465) — Each keep of an ask: (the keep, kept_at, removed_at or None while live).
- `_episode_keys(kept: Mapping[str, Any]) -> set[tuple[str, str]]` ([source](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py), line 1478) — Every passage a keep holds: its keys and each kept object's span.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/router_reader|learnloop.daily_plan.router_reader]] — imports `kept_comparisons_for_card`; statically calls `kept_comparisons_for_card`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `kept_comparisons_for_card`; statically calls `kept_comparisons_for_card`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `module`; statically calls `keep_enabled`, `kept_comparisons_for_card`
- [[Reference/Modules/learnloop_sidecar/handlers/kept_comparisons|learnloop_sidecar.handlers.kept_comparisons]] — imports `module`; statically calls `by_point_enabled`, `keep`, `keep_enabled`, `keep_tutor`, `kept_ask`, `kept_marks`, `max_perspectives`, `remove`, `reopen`, `tutor_comparison`, `tutor_keep_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `module`; statically calls `by_point_enabled`, `clean_perspectives`, `compare_kept_state`, `compared_on`, `keep_enabled`, `max_perspectives`
- [[Reference/Modules/learnloop_sidecar/handlers/notes|learnloop_sidecar.handlers.notes]] — imports `MAX_TAKE_CHARS`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/salience_firewall|learnloop.attempts.salience_firewall]] — imports `salience_payload`; calls `salience_payload`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `module`; calls `exam_withheld`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/library_asks|learnloop.db.stores.library_asks]] — imports `module`; calls `ask_row`, `asks_for_comparison`, `asks_with_keeps`, `fork_ask`, `insert_ask`, `kept_asks`, `kept_row`, `update_ask`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `block_content_hashes`, `blocks_by_key`; calls `block_content_hashes`, `blocks_by_key`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `comparison_row`, `tool_call`, `tool_call_runs`; calls `comparison_row`, `tool_call`, `tool_call_runs`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/reader/source_objects|learnloop.reader.source_objects]] — imports `module`; calls `author_source_object`, `comparison_passages`, `link_relation`, `review_source_object`, `supersede_relation`, `withheld_comparisons`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `COMPARE_PROMPT_VERSION`, `COMPARE_PROMPT_VERSION_V2`, `_quote_in`; calls `_quote_in`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `block_roles`; calls `block_roles`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `LibraryAskError`, `anchor_learning_objects`, `compare_enabled`, `compare_table`; calls `LibraryAskError`, `anchor_learning_objects`, `compare_enabled`, `compare_table`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `log_interaction_event`; calls `log_interaction_event`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/router_reader|learnloop.daily_plan.router_reader]], [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]], [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]], [[Reference/Modules/learnloop_sidecar/handlers/kept_comparisons|learnloop_sidecar.handlers.kept_comparisons]], [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_compare_sources_keep.py](../../../../../../tests/test_compare_sources_keep.py) — direct import
  - `test_a_keep_interrupted_after_its_proposals_writes_nothing_and_a_retry_keeps_once`
  - `test_a_tutor_keep_checks_its_question_passage_before_any_write`
  - `test_a_tutor_keep_keeps_only_the_sources_its_run_showed`
  - `test_a_tutor_take_on_a_learner_keep_is_hidden_once_its_question_is_held_out`
  - `test_an_interrupted_remove_leaves_the_keep_whole`
  - `test_concurrent_keeps_of_one_comparison_write_one_set`
  - `test_equivalent_definitions_are_alternate_definitions`
  - `test_every_fine_label_round_trips_through_kept_json`
  - `test_every_rw4d_event_is_salience_only`
  - `test_relation_successors_record_what_they_supersede`
  - `test_replaying_a_take_does_not_duplicate_it_even_at_the_limit`
  - `test_the_card_omits_a_comparison_held_out_now_at_every_as_of`
  - `test_the_card_reads_keeps_takes_and_removals_as_of`
  - `test_the_held_out_predicate_fails_closed`
  - `test_the_relation_mapping_table`
  - `test_the_router_cards_read_is_typed_and_pure`
  - `test_the_tutor_shown_a_comparison_the_learner_keeps_modifies_that_keep`
- [tests/test_reader_ca4_table_by_point.py](../../../../../../tests/test_reader_ca4_table_by_point.py) — direct import
  - `test_hiding_a_kept_row_supersedes_its_proposals_and_showing_it_proposes_it_again`
  - `test_keep_maps_each_quoted_cell_to_one_claim_with_its_rows_label`
  - `test_max_perspectives_is_a_keep_config_key`

## Modification guidance

- Make changes here when the responsibility remains kept comparisons within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/kept_comparisons.py](../../../../../../src/learnloop/source_retrieval/kept_comparisons.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
