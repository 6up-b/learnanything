---
title: "learnloop.source_retrieval.note_links"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/note_links.py"
source_paths:
  - "src/learnloop/source_retrieval/note_links.py"
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
  - "learnloop.source_retrieval.note_links module"
  - "src/learnloop/source_retrieval/note_links.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.note_links`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.note_links` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Deliverable curriculum C2: notes in the learner's voice, linked (spec_deliverable_curriculum_v1 §10, §12 C2; C2b: the vault's own notes).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py) |
| Source lines | 1317 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class NotesError(ValueError)` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 145) — A request the notes cannot answer (``code`` names it for the sidecar).
  - `__init__(self, code: str, message: str) -> None` (line 148; internal)
- `class NotesSwitchedOff(BaseException)` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 153) — The notes' authorization changed while work was under way (``notes.enabled`` off, another vault open): nothing more is sent or recorded.
- `enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 160)
- `models_off() -> bool` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 164)
- `class NotesSettings` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 169) — The notes as a run reads them: whether the vault's embeddings offer a meaning search.
- `notes_settings(vault: Any) -> NotesSettings | None` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 175) — The notes' settings, or None while the notes are off (C2b: notes are in every vault).
- `available(vault: Any) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 183)
- `class NotesGuard` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 187) — Codex review F2: the notes' authorization, read afresh from the vault as it is now (the sidecar's loaded vault, else the files), at every model request's admission (a request gate, composed with C0a's :class:`SC.CoverageGuard` when given) and before every record.
  - `__init__(self, vault: Any, *, live_vault: Callable[[], Any] | None=None) -> None` (line 201; internal)
  - `with_coverage(self, library: SC.Library, keys: Iterable[tuple[str, str]], *, notes: Sequence[str]=()) -> 'NotesGuard'` (line 213; public) — The same authorization composed with one judgment's protection check over ``keys``: both judged on one published snapshot (Codex re-review F2).
  - `_refusal_in(self, vault: Any) -> str | None` (line 232; internal) — Why ``vault`` (one published snapshot) authorizes nothing more (None: it does).
  - `_refusal(self) -> str | None` (line 255; internal)
  - `_refuse_if_changed(self, purpose: str) -> None` (line 271; internal)
  - `_adopt(self) -> None` (line 276; internal) — The composed check refused on the notes: so does every later check of this guard.
  - `check_notes(self, purpose: str='request') -> None` (line 283; public) — Raise :class:`NotesSwitchedOff` when the run may send or record nothing more.
  - `check(self, purpose: str='request') -> None` (line 292; public) — The notes (and, composed, the protection, on the same snapshot).
  - `admit(self, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> Any` (line 305; public)
  - `settle(self, admission: Any, usage: dict[str, Any]) -> None` (line 325; public)
- `opaque(note_key: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 337) — A note's id in the judgment ledger: a digest, never its path (an unrelated note leaves no trace of where it lives).
- `passage_key(extraction_id: str, section_id: str | None, span_id: str | None) -> str` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 344)
- `identity(row: Mapping[str, Any]) -> tuple[str, str]` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 348) — What one link decision is about: the note and its topic (a model proposal, or the learner's word on it), else the note and the passage (a link made by hand).
- `class Target` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 362) — One topic on a deliverable path, as the notes read it.
- `path_targets(vault: Any, repository: Repository, goal_id: str) -> list[Target]` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 378) — The deliverable's needed topics on its current path, each with its primary section (never a withheld one: the path view drops them first).
- `candidates(vault: Any, repository: Repository, target: Target, *, limit: int, corpus: Sequence[VN.VaultNote] | None=None, embedder: Any | None=None, settings: NotesSettings | None=None) -> list[VN.VaultNote]` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 406) — The vault notes search for the topic's and its sections' titles: by meaning first while the vault's embeddings are on (each query in order, the topic's first), then by exact words, each note once, at most ``limit`` (C2b).
- `state_key(target: Target, lead: str, notes: Sequence[VN.VaultNote]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 450)
- `class NoteVerdict(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 464)
- `class NoteLinkOutputV1(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 475)
- `build_prompt(target: Target, lead: str, notes: Sequence[VN.VaultNote]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 493)
- `class JudgeResult` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 507)
- `verdict_problem(output: NoteLinkOutputV1, expected: Sequence[str]) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 519) — Why an answer is unusable (Codex review F12), or None: exactly one verdict per candidate (none missing, none twice, no unknown id), and ``about`` and ``how`` for each ``discusses``.
- `judge_target(vault: Any, repository: Repository, target: Target, *, settings: NotesSettings | None=None, client: Any | None=None, clock: Clock | None=None, live_vault: Callable[[], Any] | None=None, guard: NotesGuard | None=None, corpus: Sequence[VN.VaultNote] | None=None, embedder: Any | None=None) -> JudgeResult` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 568) — Find the topic's candidate notes, and (unless this state was judged) ask once which discuss it; store the proposals with snapshots of the linked notes only, and mark the state the topic shows.
- `class LinkRun` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 748)
- `link_goal(vault: Any, repository: Repository, goal_id: str, *, client: Any | None=None, clock: Clock | None=None, live_vault: Callable[[], Any] | None=None, still_wanted: Callable[[], bool] | None=None, embedder: Any | None=None) -> LinkRun` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 756) — Link the deliverable's topics to the learner's notes (the background job's body), then refresh the snapshots of the notes the learner linked by hand.
- `refresh_learner_links(vault: Any, repository: Repository, *, clock: Clock | None=None, guard: NotesGuard | None=None) -> int` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 798) — Read again, from the vault, each note the learner linked by hand (and still keeps): a changed text is a new snapshot, or the earlier snapshot of the same text made current again (Codex re-review F13), which the link shows (its note's current snapshot).
- `effective(repository: Repository, rows: Sequence[Mapping[str, Any]], *, vault: Any, goal_id: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 861) — The links shown among ``rows``: the current state's proposals per topic and the learner's own links, minus everything the learner hid.
- `named_for_display(repository: Repository, pairs: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]]) -> list[tuple[Mapping[str, Any], Mapping[str, Any]]]` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 876) — ``pairs`` with each note named for the learner (follow-ups batch 7 (B)).
- `withhold_protected(vault: Any, repository: Repository, pairs: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]]) -> list[tuple[Mapping[str, Any], Mapping[str, Any]]]` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 891) — ``pairs`` minus every snapshot of a Reader note any of whose anchors (or their sections' headers) sits beside protected material now (C0a's predicate read now; unreadable: every Reader note is withheld, fail closed).
- `effective_rows(repository: Repository, rows: Sequence[Mapping[str, Any]], *, vault: Any, goal_id: str | None=None, withhold: bool=True) -> list[tuple[Mapping[str, Any], Mapping[str, Any]]]` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 908) — :func:`effective`'s links as (link row, the snapshot it shows), oldest first: the one rule for which links stand (curriculum C5's gap reading reads the same pairs).
- `date_label(captured_on: str | None) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 944) — "3 Oct" (the note's date), or None.
- `link_view(row: Mapping[str, Any], note: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 956)
- `for_goal(vault: Any, repository: Repository, goal_id: str, *, targets: Sequence[Target] | None=None) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 977) — The notes shown on the deliverable's path lines, by topic (``targets``: the path's topics when the caller has read them already).
- `marks(vault: Any, repository: Repository, extraction_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 1007) — The ``›`` marks of one reading: per passage (span), the notes linked beside it.
- `for_passages(vault: Any, repository: Repository, passages: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 1025) — Compare's *your take* band: the notes linked to the compared passages' sections (or their spans), each once.
- `take_text(view: Mapping[str, Any], *, limit: int) -> str` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 1049) — *use as my take*: the take RW4d keeps, quoting the note in the learner's words.
- `decide(vault: Any, repository: Repository, link_id: str, choice: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 1074) — One tap: ``hide`` (rejected: hidden now and across re-judgments) or ``keep`` (the learner's own word that it stays: undoes a hide).
- `hidden_origin_label(key: str, note: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 1122) — Where a hidden note came from, in words: a Pocket Notes page (C2's history), or a vault note's kind (a Reader note, a capture); None for a tend-era note (its title and heading name it).
- `hidden(vault: Any, repository: Repository) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 1134) — The links the learner hid and still keeps hidden, newest first (C2 ruling R5, followups-nov1c C: Settings lists them, to bring one back after the reading changed): the learner's newest row per (note, topic) or (note, passage) is a hide.
- `search(vault: Any, repository: Repository, *, query: str | None=None, extraction_id: str | None=None, span_id: str | None=None, mode: str='words', embedder: Any | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 1178) — The Reader's *link one of your notes* (C2b: the vault's own notes): with no words, the notes for the passage's section title; with the learner's words, those words.
- `link_by_hand(vault: Any, repository: Repository, *, hit: Mapping[str, Any], extraction_id: str, span_id: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 1218) — The learner links a note to a passage from the Reader (``authorship = 'learner'``, ``accepted``): the note is read again from the vault (by its key) and snapshotted.
- `report_row(repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 1267) — ``learnloop curriculum report``'s notes row: proposals, links kept by hand, hides and *use as my take*; counts only, never a note's text or where it lives.

### Module constants

- `ROUTE` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 88)
- `PROMPT_VERSION` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 90)
- `HIDE_VERSION` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 91)
- `LEDGER_TASK` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 92)
- `LEDGER_LEFT` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 93)
- `LEDGER_RIGHT` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 94)
- `SHOWN_TASK` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 96)
- `SHOWN_VERSION` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 97)
- `SHOWN_LEFT` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 98)
- `CURRENT_TASK` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 101)
- `CURRENT_VERSION` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 102)
- `CURRENT_LEFT` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 103)
- `CURRENT_RIGHT` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 104)
- `WAITING_RETRY_SECONDS` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 110)
- `NO_CANDIDATES_STATE` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 112)
- `MODELS_ENV` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 115)
- `HOWS` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 117)
- `HOW_WORDS` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 118)
- `POCKET_NOTES_LABEL` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 123)
- `VAULT_ORIGIN_LABELS` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 126)
- `BY_MODEL_LABEL` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 128)
- `BY_YOU_LABEL` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 129)
- `TAKE_PREFIX` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 132)
- `LEAD_CHARS` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 136)
- `STATEMENT_CHARS` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 138)
- `HOW_LINE_CHARS` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 140)
- `QUERY_CHARS` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 142)
- `_INSTRUCTIONS` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 479)
- `REPORT_LABEL` ([src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py), line 1264)

### Explicit exports

`__all__` declares:

- `BY_MODEL_LABEL`
- `HOWS`
- `LEDGER_TASK`
- `NotesError`
- `NotesGuard`
- `NotesSettings`
- `NotesSwitchedOff`
- `POCKET_NOTES_LABEL`
- `PROMPT_VERSION`
- `ROUTE`
- `TAKE_PREFIX`
- `Target`
- `available`
- `candidates`
- `decide`
- `effective`
- `enabled`
- `for_goal`
- `for_passages`
- `hidden`
- `judge_target`
- `link_by_hand`
- `link_goal`
- `marks`
- `notes_settings`
- `path_targets`
- `report_row`
- `search`
- `state_key`
- `verdict_problem`
- `take_text`
- `withhold_protected`

## Internal implementation anchors

- `_one_line(text: Any, limit: int) -> str` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 332)
- `_lead(vault: Any, repository: Repository, target: Target) -> str` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 436)
- `_text_hash(text: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 442)
- `_content_hash(note: VN.VaultNote) -> str` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 446)
- `_validator(expected: Sequence[str]) -> Callable[[NoteLinkOutputV1], NoteLinkOutputV1]` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 537)
- `_mark_shown(connection: Any, target: Target, state: str, now: str) -> None` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 546) — Inside the caller's transaction: the topic shows ``state`` now (Codex review F7).
- `_record_shown(repository: Repository, target: Target, state: str, guard: NotesGuard, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 561)
- `_judge_target(vault: Any, repository: Repository, target: Target, *, settings: NotesSettings | None, client: Any | None, clock: Clock | None, notes_guard: NotesGuard, corpus: Sequence[VN.VaultNote] | None, embedder: Any | None) -> JudgeResult` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 585)
- `_store_snapshot(connection: Any, note: VN.VaultNote, now: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 695) — The note's snapshot (stored once per content hash; only ever for a linked note): origin ``vault`` and its vault reference (C2b, migration 233).
- `_read_token(repository: Repository) -> str` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 709) — A read's monotonic token (C2 ruling R6), taken when the read starts, before the note is read from the vault: a ULID that sorts after every ULID this process minted before it and after the newest token any read has published (read from the database now: Codex review F2, a token p…
- `_show_read(connection: Any, note: VN.VaultNote, token: str, now: str) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 723) — Inside the caller's write transaction: a read of the note made to show it (a link by hand, a refresh) makes its text the snapshot the note shows (Codex re-review F13), a text the note had before included (that snapshot again) — but only if it started after every read published s…
- `_standing(rows: Iterable[Mapping[str, Any]]) -> dict[tuple[str, str], Mapping[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 789) — The learner's newest row per (note, topic or passage): their word that stands.
- `_shown_ai_rows(connection: Any, rows: Sequence[Mapping[str, Any]], *, goal_id: str | None=None) -> list[Mapping[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 846) — The model's rows of the candidate state each topic shows now (Codex review F7): for one deliverable (``goal_id``), its own topic's state; otherwise (a reading's marks, Compare's band) the state any deliverable's topic shows.
- `_row(repository: Repository, link_id: str) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 1066)
- `_where(vault: Any, library: SC.Library | None, row: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/note_links.py), line 1102) — Where a hidden link was: its topic's title, else its reading and section.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/curriculum|learnloop.cli.curriculum]] — imports `report_row`; statically calls `report_row`
- [[Reference/Modules/learnloop/source_retrieval/note_gaps|learnloop.source_retrieval.note_gaps]] — imports `module`; statically calls `available`, `effective_rows`
- [[Reference/Modules/learnloop/teacher/notes|learnloop.teacher.notes]] — imports `module`; statically calls `available`, `effective`, `enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/notes|learnloop_sidecar.handlers.notes]] — imports `module`; statically calls `available`, `decide`, `enabled`, `for_goal`, `for_passages`, `hidden`, `link_by_hand`, `link_goal`, `marks`, `notes_settings`, `path_targets`, `search`, `take_text`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInvalidOutput`; calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `active_request_gate`, `content_key`; calls `active_request_gate`, `content_key`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `title_from_local_uri`; calls `title_from_local_uri`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/learner_notes|learnloop.db.stores.learner_notes]] — imports `module`; calls `current_fences`, `current_notes`, `current_states`, `insert_link`, `insert_note`, `judged`, `learner_rows_for`, `link_counts`, `links`, `newest_read_token`, `notes_by_id`, `tables_present`, `takes_quoting_notes`, `topic_key`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`, `new_ulid_after`; calls `new_ulid`, `new_ulid_after`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `module`; calls `path_view`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `module`; calls `ChatRoute`, `daily_envelope`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `module`; calls `CoverageGuard`, `Library`, `peek`, `published_snapshot`, `still_published`
- [[Reference/Modules/learnloop/source_retrieval/vault_notes|learnloop.source_retrieval.vault_notes]] — imports `module`; calls `meaning_available`, `meaning_search`, `meaning_unavailable`, `notes`, `read`, `read_many`, `snapshot_protected_keys`, `source_display_titles`, `split_key`, `words_search`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `hashlib`, `json`, `os`, `pathlib`, `threading`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/curriculum|learnloop.cli.curriculum]], [[Reference/Modules/learnloop/source_retrieval/note_gaps|learnloop.source_retrieval.note_gaps]], [[Reference/Modules/learnloop/teacher/notes|learnloop.teacher.notes]], [[Reference/Modules/learnloop_sidecar/handlers/notes|learnloop_sidecar.handlers.notes]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_curriculum_c3_exam_scoping.py](../../../../../../tests/test_curriculum_c3_exam_scoping.py) — direct import
  - `test_gc1_note_link_judge_requests_carry_no_exam_material_from_sources`
- [tests/test_followups_batch7_note_titles.py](../../../../../../tests/test_followups_batch7_note_titles.py) — direct import
  - `test_a_row_stored_with_the_uri_is_shown_readable_and_stays_as_it_was`
  - `test_the_notes_content_hash_is_unchanged_so_nothing_reads_as_changed`
- [tests/test_notes_as_learner_text.py](../../../../../../tests/test_notes_as_learner_text.py) — direct import
  - `test_gc1_exam_sentinels_never_reach_the_gap_model_via_a_notes_context`
  - `test_switched_off_the_gaps_code_reads_no_note_row_and_queues_nothing`
- [tests/test_notes_c2b_review5.py](../../../../../../tests/test_notes_c2b_review5.py) — direct import
  - `test_c2b_final_verify_f1_the_notes_guard_judges_a_candidate_by_every_anchor_it_ever_had`
  - `test_c2b_r5_f1_a_linked_note_whose_anchor_became_protected_is_withheld_everywhere`
  - `test_c2b_r5_rereview_f1_a_snapshot_from_an_older_anchor_is_withheld_once_that_anchor_is_protected`
- [tests/test_notes_linked.py](../../../../../../tests/test_notes_linked.py) — direct import
  - `test_a_learner_links_a_note_by_hand_from_the_reader`
  - `test_f12_verdict_problem_names_each_defect`
  - `test_f2_notes_switched_off_refuses_the_pending_request`
  - `test_f2_switching_notes_off_during_the_request_records_nothing`
  - `test_f9_a_link_hidden_during_the_refresh_stays_hidden`
  - `test_landing_c2b_a_hidden_note_beside_material_protected_since_is_not_listed`
  - `test_landing_the_coverage_guard_composes_c1s_gate_and_c2s_also`
  - `test_legacy_tend_snapshots_stay_readable`
  - `test_on_the_contract_in_every_vault_with_the_meaning_flag`
  - `test_one_tap_hides_a_link_and_it_stays_hidden_across_rejudgments`
  - `test_r5_settings_lists_the_hidden_notes_and_show_again_unhides_through_decide`
  - `test_r6_an_unchanged_read_fences_off_an_older_refresh_in_flight`
  - `test_r6_review_f2_a_clock_correction_and_restart_never_blocks_later_refreshes`
  - `test_r6_two_concurrent_refreshes_resolve_to_the_newest_read`
  - `test_re3_f13_a_delayed_judgment_never_makes_its_snapshot_current_again`
  - `test_re_f13_a_note_linked_by_hand_changed_and_changed_back_shows_its_text_now`
  - `test_re_f14_a_waiting_run_is_not_restarted_by_every_read`
  - `test_re_f2_an_unchanged_reload_still_links`
  - `test_re_f2_the_composed_gate_admits_on_one_snapshot`
  - `test_refresh_reads_a_hand_linked_note_again_from_the_vault`
  - `test_the_path_links_the_vault_notes_that_discuss_it_and_stores_only_linked_notes`
  - `test_the_report_counts_notes_without_their_text`
- [tests/test_notes_vault_search.py](../../../../../../tests/test_notes_vault_search.py) — direct import
  - `test_c2b_f2_a_candidate_protected_before_the_request_refuses_it`
  - `test_the_link_judges_candidates_come_from_the_same_vault_search`

## Modification guidance

- Make changes here when the responsibility remains note links within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/note_links.py](../../../../../../src/learnloop/source_retrieval/note_links.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
