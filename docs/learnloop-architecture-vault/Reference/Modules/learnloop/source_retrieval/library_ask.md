---
title: "learnloop.source_retrieval.library_ask"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/library_ask.py"
source_paths:
  - "src/learnloop/source_retrieval/library_ask.py"
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
  - "learnloop.source_retrieval.library_ask module"
  - "src/learnloop/source_retrieval/library_ask.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.library_ask`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.library_ask` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Ask your library (reader workbench RW4a; spec_reader_workbench_v1 §7.2, §7.3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py) |
| Source lines | 1500 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class LibraryAskError(ValueError)` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 157)
  - `__init__(self, code: str, message: str) -> None` (line 158; internal)
- `library_ask_enabled(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 167) — The library answer exists: its own switch, the sources service it composes, and RW1a's inquiry (its states, voices and return stack).
- `compare_enabled(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 176)
- `class OrganizerNote(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 185)
- `class OrganizerResult(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 198)
- `class OrganizerRoleNote(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 214)
  - `_tolerate_roles(cls, data: Any) -> Any` (line 231; internal)
- `class OrganizerRolesResult(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 235)
- `class OrganizerExplorableNote(OrganizerNote)` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 271)
  - `_tolerate(cls, data: Any) -> Any` (line 278; internal)
- `class OrganizerExplorableResult(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 282)
- `class OrganizerRoleExplorableNote(OrganizerRoleNote)` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 287)
  - `_tolerate(cls, data: Any) -> Any` (line 292; internal)
- `class OrganizerRolesExplorableResult(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 296)
- `ledger_explorable(ledger: Mapping[str, Any] | None) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 308) — Whether a ``library_contribution`` ledger row records the organizer's ``explorable: yes`` (rows of any other request record none: no).
- `explorable_task(task: ListwiseTask) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 328)
- `base_task(task: ListwiseTask) -> ListwiseTask` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 332)
- `organizer_task(vault: LoadedVault) -> ListwiseTask` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 344) — RW4a's organizer request, or RW4e's while ``roles.on_demand_enabled`` is on; either with RW5b's ``explorable`` while ``figures.offers_enabled`` is on.
- `offerable_kind(passage: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 354) — ``equation`` | ``figure`` for a block an offer may name (code decides), else None.
- `shown_organizer(vault: LoadedVault, organizer: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 360) — The organizer's output as it may be shown now: with offers off, no note carries ``explorable`` (a stored one from while they were on included), so the output is RW4a's/RW4e's, key for key.
- `anchor_learning_objects(vault: LoadedVault, repository: Repository, *, extraction_id: str | None, span_ids: Sequence[str], learning_object_ids: Sequence[str]=()) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 412) — The question's LOs: given ones, else the anchor passage's provenance-linked LOs.
- `open_questions(vault: LoadedVault, repository: Repository, lo_ids: Sequence[str]) -> list[dict[str, str]]` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 444) — The learner's open questions on these LOs, as the personalized organizer sees them: active misconceptions (the diagnoser's statements) and named learner-text gaps not undone.
- `group_hits(hits: Sequence[Mapping[str, Any]], *, order: Sequence[str]=GROUP_ORDER) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 497) — Main passages by source (in the order a source first appears) and then by role; expansion passages under their own subheads (UX W9).
- `label_proposed_roles(vault: LoadedVault, repository: Repository, hits: Sequence[dict[str, Any]]) -> None` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 524) — RW4e (``roles.positive_filter_enabled``): a main passage whose ingest role is ordinary prose and that has a visible role proposal is grouped by the proposed role and carries it as ``proposed_role`` (the model's label, UX §4.5).
- `ask_library(vault: LoadedVault, repository: Repository, query: str, *, find: Callable[..., Any], caller: Mapping[str, Any], record_shown: Callable[[Sequence[str], str], Sequence[str]] | None=None, entry: str='reader', extraction_id: str | None=None, anchor_span_ids: Sequence[str]=(), learning_object_ids: Sequence[str]=(), personalized: bool | None=None, expand: Sequence[str] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 564) — Passages for ``query`` from the learner's library, sources first.
- `ask_row(repository: Repository, ask_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 714)
- `organizer_envelope(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> SharedDailyEnvelope` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 744) — ``library_ask.max_daily_cost_usd`` as a durable, atomic daily cap (Codex review F5).
- `organizer_spent_today(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> float` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 762) — The organizer's metered spend since UTC midnight, as its cap counts it.
- `organizer_prompt(query: str, candidates: Sequence[Mapping[str, Any]], questions: Sequence[Mapping[str, str]], *, personalized: bool, task: ListwiseTask=ORGANIZER_TASK) -> str` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 820)
- `organize(vault: LoadedVault, repository: Repository, ask_id: str, *, client: Any | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 860) — The organizer's notes for a library answer: one listwise call, cached.
- `open_comparison(vault: LoadedVault, repository: Repository, *, question: str, caller: Mapping[str, Any], door: str, extraction_id: str | None=None, anchor_span_ids: Sequence[str]=(), entry: str='reader', tool_call_id: str | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 1059) — Reader CA3: the ask row a comparison from a door without a library answer (a selection, the ask box's comparison, the tutor's offer) is bound by.
- `compare_table(comparison: Mapping[str, Any], *, first_source_id: str | None=None, by_point: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 1116) — The Reader's table over a ``compare_sources`` result (UX W10).
- `point_rows(comparison: Mapping[str, Any], refs: Mapping[Any, Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 1184) — Reader CA4 (§5.1, K13): a v2 comparison's points as the grid shows them.
- `compare(vault: LoadedVault, repository: Repository, ask_id: str, *, pinned_keys: Sequence[str], compare_sources: Callable[..., Any], record_shown: Callable[[Sequence[str], str], Sequence[str]] | None=None, open_source_id: str | None=None, requested_perspectives: Sequence[str]=(), scope: Mapping[str, Any] | None=None, bind: Callable[[Callable[[], None], Sequence[str], str | None], Mapping[str, Any]] | None=None, by_point: bool=False, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 1222) — Compare the pinned passages through the service's ``compare_sources``.
- `class OnlyPinned` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 1335) — The pinned-span provider, without the numbered blocks a pinned passage cites ("by Theorem 3.2"): "answers only from these N passages" holds for the citation allowlist too (G17).
  - `__call__(self, vault: LoadedVault, repository: Repository, **kwargs: Any)` (line 1350; internal)
- `compared_passage_keys(payload: Mapping[str, Any], table: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 1364) — Every passage a comparison read, as ``extraction:span`` keys, the anchor first: the service's own record (``counterpart_keys``, what a stored comparison keeps too), else the table's rows (each row's passage, every block of an anchor of several).
- `comparison_passage_keys(repository: Repository, ask_id: str, comparison_id: str) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 1380) — Reader CA3 (Codex re-review F10): every passage the ask's comparison read, from the stored comparison itself (each compared book's passage and every block of an anchor of several), as ``extraction:span`` keys, the anchor first.
- `ask_tutor(vault: LoadedVault, repository: Repository, ask_id: str, *, pinned_keys: Sequence[str], question_md: str | None, ask: Callable[..., Mapping[str, Any]], clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 1406) — "Ask the tutor about these": a ``reader``-context question (a ``question_events`` row, so it joins the question queue, the field's question signals and learner-text gaps), grounded in the pinned passages and citing only them.

### Module constants

- `PROMPT_VERSION` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 109)
- `ORGANIZER_TASK_NAME` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 110)
- `ENTRIES` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 112)
- `ENTRY_EXPANSIONS` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 117)
- `EXPANSION_LABELS` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 124)
- `MAIN_LIMIT` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 128)
- `EXPANSION_LIMIT` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 129)
- `EXPANSION_POOL` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 131)
- `ORGANIZER_PASSAGE_CHARS` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 132)
- `QUESTION_CHARS` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 133)
- `ROLES` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 136)
- `ROLES_PROMPT_VERSION` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 139)
- `VERDICTS` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 140)
- `ROLE_GROUPS` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 142)
- `GROUP_ORDER` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 148)
- `ROLE_GROUP_ORDER` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 150)
- `EVENTS` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 154)
- `ORGANIZER_TASK` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 203)
- `ORGANIZER_ROLES_TASK` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 242)
- `EXPLORABLE_SUFFIX` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 258)
- `ORGANIZER_EXPLORABLE_TASK` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 321)
- `ORGANIZER_ROLES_EXPLORABLE_TASK` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 322)
- `_BASE_OF` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 324)
- `_EXPLORABLE_SENTENCE` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 336)
- `_INSTRUCTIONS` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 373)
- `_ROLES_V1` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 384)
- `_ROLES_V2` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 385)
- `_PERSONAL` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 388)
- `ORGANIZER_ENVELOPE` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 741)
- `DOORS` ([src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 1056)

### Explicit exports

`__all__` declares:

- `ENTRIES`
- `ENTRY_EXPANSIONS`
- `EVENTS`
- `EXPANSION_LABELS`
- `LibraryAskError`
- `ORGANIZER_ENVELOPE`
- `ORGANIZER_TASK`
- `DOORS`
- `OnlyPinned`
- `OrganizerResult`
- `ROLES`
- `anchor_learning_objects`
- `ask_library`
- `ask_row`
- `ask_tutor`
- `compare`
- `compare_enabled`
- `compare_table`
- `point_rows`
- `compared_passage_keys`
- `comparison_passage_keys`
- `group_hits`
- `open_comparison`
- `ledger_explorable`
- `library_ask_enabled`
- `open_questions`
- `organize`
- `organizer_envelope`
- `organizer_prompt`
- `organizer_spent_today`

## Internal implementation anchors

- `_tolerate_explorable(data: Any) -> Any` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 261) — A missing or unknown ``explorable`` reads as no (old outputs included).
- `_explorable_twin(task: ListwiseTask, result_model: type[WireModel]) -> ListwiseTask` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 301)
- `_key(hit: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 399)
- `_keys(values: Sequence[str]) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 403)
- `_linked_keys(vault: LoadedVault, repository: Repository, lo_id: str) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 427) — The passages an LO is linked to by provenance (its teaching links).
- `_demonstrated(vault: LoadedVault, repository: Repository, lo_id: str) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 434)
- `_group_of(hit: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 482)
- `_shown_hit(hit: Mapping[str, Any], *, expansion: str | None, learning_object_ids: Sequence[str]=()) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 486)
- `_basis(manifest: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 543) — How the passages were found, in the learner's words.
- `_status(result: Any) -> str` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 552)
- `_event(repository: Repository, event: str, payload: Mapping[str, Any], *, subject_id: str | None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 556)
- `_record_ask_citations(vault: LoadedVault, repository: Repository, row: Mapping[str, Any], citations: Sequence[Mapping[str, Any]]) -> int` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 695) — Local contextual retrieval P1 (spec §9.2, Codex review F11): the pinned tutor answer's validated citations are relevance signals on the passages the ask's own searches delivered (joined by their receipts).
- `_update(repository: Repository, ask_id: str, **columns: Any) -> None` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 722)
- `_shown_keys(row: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 728)
- `class _OrganizerAdmission` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 774) — Each metered organizer attempt's admission under the daily cap, through ``judge_listwise``'s ``admit`` hook (after the ledger and the checkpoints were found not to answer it, before anything is sent).
- `_passages(vault: LoadedVault, repository: Repository, keys: Sequence[str], *, with_kinds: bool=False) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 795) — The passages' text and page; ``with_kinds`` (RW5b's offers): their block type too, so code can tell an equation or a figure.
- `_earlier_notes(repository: Repository, ledger_ids: Sequence[str]) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 813) — The validated notes an earlier ask stored for these ledger rows.
- `_recovered_answer(repository: Repository, route: Any, prompt: str, validate: Callable[[Any], Any], task: ListwiseTask=ORGANIZER_TASK) -> Any | None` ([source](../../../../../../src/learnloop/source_retrieval/library_ask.py), line 837) — The organizer's validated answer for ``prompt`` from what the paid call left behind: its checkpoint, else its completed receipt (Codex review F8: the ledger committed and the process died before the notes were stored, so the ledger answers "cached" and no earlier notes exist).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/kept_comparisons|learnloop.source_retrieval.kept_comparisons]] — imports `LibraryAskError`, `anchor_learning_objects`, `compare_enabled`, `compare_table`; statically calls `LibraryAskError`, `anchor_learning_objects`, `compare_enabled`, `compare_table`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `ROLES`
- [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] — imports `anchor_learning_objects`, `open_questions`; statically calls `anchor_learning_objects`, `open_questions`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `module`; statically calls `ask_row`, `ledger_explorable`
- [[Reference/Modules/learnloop_sidecar/handlers/kept_comparisons|learnloop_sidecar.handlers.kept_comparisons]] — imports `module`; statically calls `ask_row`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `module`; statically calls `OnlyPinned`, `ask_library`, `ask_row`, `ask_tutor`, `compare`, `compare_enabled`, `comparison_passage_keys`, `library_ask_enabled`, `open_comparison`, `organize`
- [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]] — imports `module`; statically calls `library_ask_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_tutor|learnloop_sidecar.handlers.reader_tutor]] — imports `open_questions`; statically calls `open_questions`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInvalidOutput`; calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendEstimate`, `SpendLimitExceeded`; calls `SpendLimitExceeded`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/attempts/salience_firewall|learnloop.attempts.salience_firewall]] — imports `salience_payload`; calls `salience_payload`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] — imports `build_cross_source_spans`; calls `build_cross_source_spans`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `module`; calls `exam_material`, `held_out_among`, `held_out_material`, `held_out_refusal`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/learner_gaps|learnloop.db.stores.learner_gaps]] — imports `module`; calls `gaps`, `reversals`
- [[Reference/Modules/learnloop/db/stores/library_asks|learnloop.db.stores.library_asks]] — imports `module`; calls `ask_row`, `insert_ask`, `notes_for_ledger_ids`, `update_ask`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `blocks_by_key`; calls `blocks_by_key`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `comparison_row`; calls `comparison_row`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `EXPLORABLE`, `explorable_yes`, `offer_kind`, `offers_enabled`; calls `explorable_yes`, `offer_kind`, `offers_enabled`
- [[Reference/Modules/learnloop/goals/goal_certification|learnloop.goals.goal_certification]] — imports `lo_certification`; calls `lo_certification`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/practice_index/listwise|learnloop.practice_index.listwise]] — imports `ListwiseTask`, `judge_listwise`, `listwise_caps`, `task_output_tokens`; calls `ListwiseTask`, `judge_listwise`, `listwise_caps`, `task_output_tokens`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `checkpoint_key`, `plan_route`, `receipt_answer`; calls `checkpoint_key`, `plan_route`, `receipt_answer`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `learning_objects_for_span`; calls `learning_objects_for_span`
- [[Reference/Modules/learnloop/reader/source_roles|learnloop.reader.source_roles]] — imports `module`; calls `best_roles`, `claims_from_judgments`, `clean_roles`, `on_demand_enabled`, `positive_filter_enabled`, `propose_roles`, `tolerate_roles`
- [[Reference/Modules/learnloop/source_retrieval/feedback|learnloop.source_retrieval.feedback]] — imports `record_receipt_citations`; calls `record_receipt_citations`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `EXPANSIONS`, `expanded_learning_objects`; calls `expanded_learning_objects`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `SharedDailyEnvelope`, `midnight`; calls `SharedDailyEnvelope`, `midnight`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `log_interaction_event`; calls `log_interaction_event`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `decimal`, `json`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/kept_comparisons|learnloop.source_retrieval.kept_comparisons]], [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]], [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]], [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]], [[Reference/Modules/learnloop_sidecar/handlers/kept_comparisons|learnloop_sidecar.handlers.kept_comparisons]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/library_ask_fixtures.py](../../../../../../tests/library_ask_fixtures.py) — direct import
- [tests/test_compare_sources_keep.py](../../../../../../tests/test_compare_sources_keep.py) — direct import
  - `test_a_tutor_keep_checks_its_question_passage_before_any_write`
- [tests/test_figure_offers.py](../../../../../../tests/test_figure_offers.py) — direct import
  - `test_a_block_the_judgment_did_not_offer_is_refused_before_any_call`
  - `test_a_stored_answer_with_offers_is_shown_without_them_once_offers_are_off`
  - `test_an_old_output_without_the_field_reads_as_no`
  - `test_offers_off_the_contract_has_none_and_the_press_is_refused`
  - `test_offers_off_the_organizer_is_its_own_version_and_shows_no_explorable`
  - `test_pressing_a_library_offer_builds_through_rw5a_with_origin_library`
  - `test_the_organizer_judges_explorable_in_its_one_call_on_equation_and_figure_blocks`
  - `test_the_roles_request_composes_with_explorable`
- [tests/test_figures_rw5b_fix_round2.py](../../../../../../tests/test_figures_rw5b_fix_round2.py) — direct import
  - `test_a_forked_ask_offers_and_builds_on_the_fork`
  - `test_a_library_note_pointing_at_another_tasks_yes_row_is_refused`
  - `test_the_same_question_asked_twice_offers_and_builds_on_the_second_ask`
- [tests/test_figures_rw5b_review.py](../../../../../../tests/test_figures_rw5b_review.py) — direct import
  - `test_a_library_note_edited_to_offer_without_its_ledger_yes_is_refused`
- [tests/test_library_ask.py](../../../../../../tests/test_library_ask.py) — direct import
  - `test_an_ask_returns_passages_first_and_no_essay`
  - `test_every_rw4a_event_is_salience_only_refused_as_evidence_and_never_client_recorded`
- [tests/test_library_ask_expand.py](../../../../../../tests/test_library_ask_expand.py) — direct import
  - `test_a_similar_passage_never_becomes_an_expansion`
  - `test_no_anchor_los_means_no_expansion`
  - `test_the_organizer_judges_the_union_once`
  - `test_the_rpc_reads_the_anchor_passages_los`
- [tests/test_library_ask_review.py](../../../../../../tests/test_library_ask_review.py) — direct import
  - `test_a_crash_after_the_ledger_commit_keeps_the_notes_recoverable`
  - `test_pinned_passages_are_held_to_the_tutors_context_budget`
  - `test_two_organizer_requests_in_flight_cannot_both_pass_the_cap`
  - `test_with_no_paid_answer_left_a_cached_line_stays_out_and_is_retried`
- [tests/test_passage_links.py](../../../../../../tests/test_passage_links.py) — direct import
  - `test_the_judges_role_vocabulary_is_rw4es`
- [tests/test_reader_compare_table.py](../../../../../../tests/test_reader_compare_table.py) — direct import
  - `test_compare_needs_two_pins_and_its_switch`
- [tests/test_roles_judges.py](../../../../../../tests/test_roles_judges.py) — direct import
  - `test_library_answers_group_a_proposed_role_labelled_as_the_models`
  - `test_the_judges_result_schemas_are_the_base_trees`
  - `test_the_organizer_asks_rw4es_request_and_its_roles_become_proposals`
  - `test_with_on_demand_off_the_organizer_asks_rw4as_request_and_writes_nothing`
- [tests/test_source_space_resolver.py](../../../../../../tests/test_source_space_resolver.py) — direct import
  - `test_ordinary_use_completes_the_loop_opens_ask_citations_and_the_background_refit`

## Modification guidance

- Make changes here when the responsibility remains library ask within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/library_ask.py](../../../../../../src/learnloop/source_retrieval/library_ask.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
