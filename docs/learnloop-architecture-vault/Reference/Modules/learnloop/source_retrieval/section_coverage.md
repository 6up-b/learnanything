---
title: "learnloop.source_retrieval.section_coverage"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/section_coverage.py"
source_paths:
  - "src/learnloop/source_retrieval/section_coverage.py"
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
  - "learnloop.source_retrieval.section_coverage module"
  - "src/learnloop/source_retrieval/section_coverage.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.section_coverage`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.section_coverage` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Deliverable curriculum C0a: section coverage, the correspondence backbone (spec_deliverable_curriculum_v1 §6, §9, §12; ux_reader_compare_ask_v1 §6, §12.3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py) |
| Source lines | 2318 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class CoverageError(ValueError)` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 172) — A request coverage cannot answer (``code`` names it for the sidecar).
  - `__init__(self, code: str, message: str) -> None` (line 175; internal)
- `enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 180)
- `models_off() -> bool` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 185)
- `lo_hash(learning_object: Any) -> str` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 189) — What the judge read of the LO: its title and statement.
- `class Section` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 205)
  - `key(self) -> tuple[str, str]` (line 220; public)
- `class Reading` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 225)
- `class Protection` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 239) — What no model may read, as the vault says now: the one exam predicate (held-out units included), the teaching exclusions and the readings held back until protection is marked on them (rule 4).
  - `key(self) -> str` (line 253; public) — A digest of everything withheld: equal keys withhold exactly the same.
  - `reading_out(self, extraction_id: str) -> bool` (line 265; public)
  - `span_out(self, extraction_id: str, span_id: str) -> bool` (line 269; public)
- `read_protection(vault: Any, repository: Repository, *, readable_roles: frozenset[str]=frozenset()) -> Protection` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 273) — The predicate read afresh; unreadable, ``CoverageError("withheld")`` (fail closed).
- `class Library` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 307) — Every current, reader-enabled reading with teaching authority, read lazily, with exam and held-out material taken out before anything is returned.
  - `__init__(self, vault: Any, repository: Repository, *, protection: Protection | None=None, scope: Scope | None=None) -> None` (line 314; internal)
  - `refreshed(self, vault: Any | None=None, *, protection: Protection | None=None) -> Library` (line 333; public) — This library if protection (and the vault object) are unchanged, else a new one read under today's protection (nothing cached is reused).
  - `sendable_under(self, protection: Protection, keys: Iterable[tuple[str, str]]) -> bool` (line 346; public) — Whether every one of these sections may still be read under ``protection``: its reading is not withheld whole and none of its spans is withheld.
  - `reading(self, extraction_id: str) -> Reading | None` (line 363; public)
  - `_load(self, extraction_id: str) -> Reading | None` (line 370; internal)
  - `section(self, extraction_id: str, section_id: str) -> Section | None` (line 413; public)
  - `section_of(self, extraction_id: str, span_id: str) -> str | None` (line 417; public) — The sendable section a passage belongs to (None: withheld, dropped or unknown).
  - `by_source(self) -> dict[str, list[str]]` (line 423; public)
  - `search_scope(self, extraction_ids: Sequence[str]) -> Scope` (line 429; public) — One source's search scope: its readings, every withheld or excluded span out.
  - `_provenance_index(self) -> dict[str, list[tuple[str, str]]]` (line 440; internal)
  - `provenance(self, learning_object_id: str) -> list[tuple[str, str]]` (line 458; public) — The sections the LO's (and its facets') provenance cites, in library order.
  - `section_learning_objects(self, extraction_id: str, section_id: str) -> tuple[str, ...]` (line 463; public) — The active LOs whose provenance cites this section (one reading's map, loaded once).
- `scope_signature(scope: Scope) -> str` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 478) — A digest of the readings a library is read from (ids, books, titles, reader switch): an import, a re-extraction or a book switched off changes it.
- `class LibraryCache` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 486) — Reader CA5's per-vault library for the Guide's reads (CA5a open item 7).
  - `__init__(self) -> None` (line 501; internal)
  - `get(self, vault: Any, repository: Repository) -> Library` (line 506; public)
  - `clear(self) -> None` (line 520; public)
- `class Candidate` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 535)
  - `key(self) -> tuple[str, str]` (line 544; public)
- `lo_query(learning_object: Any) -> str` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 548)
- `search_sections(vault: Any, repository: Repository, library: Library, query: str, *, sources: Iterable[str] | None=None, deep: bool=True, embedder: Any | None=None, owner_id: str='', consumer: str=SEARCH_CONSUMER, read_only: bool=False) -> dict[str, list[tuple[str, str, list[str]]]]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 566) — One ``search_spans`` per source (a shared query vector), hits grouped to sendable sections, at most :data:`SECTIONS_PER_SOURCE` each: ``source_id -> [(extraction_id, section_id, hit spans)]`` in rank order.
- `candidates_for(vault: Any, repository: Repository, library: Library, learning_object_id: str, *, deep: bool=True, embedder: Any | None=None, owner_id: str='') -> list[Candidate]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 624) — The LO's candidate sections across the library (§6.2 step 1), each once, provenance first, then the learner's, then retrieval's, each in rank order.
- `state_key(learning_object: Any, library: Library, candidates: Sequence[Candidate]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 663) — The judgment's cache key: the prompt version, the LO's statement and every candidate with its block hashes (§6.1).
- `class PassageRoles(RS.TolerantRoles)` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 678)
- `class CoverageJudgment(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 683)
  - `_tolerate(cls, data: Any) -> Any` (line 699; internal)
- `class SectionCoverageOutputV1(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 714)
- `class Prompt` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 749)
- `related_topics(vault: Any, library: Library, learning_object: Any, candidates: Sequence[Candidate]) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 759) — The LOs a section may be said to assume: the LO's prerequisites and the candidates' provenance-linked LOs (active, the LO itself left out).
- `build_prompt(vault: Any, library: Library, learning_object: Any, candidates: Sequence[Candidate]) -> Prompt` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 769) — The LO and per candidate its title, roles and lead passages (then its hits), verbatim, each section held to an equal share of ``curriculum.max_prompt_tokens``.
- `class JudgeResult` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 829)
  - `as_dict(self) -> dict[str, Any]` (line 841; public)
  - `usage_tokens(self) -> int` (line 846; public) — The tokens its requests reported (or were estimated at), summed.
- `daily_envelope(vault: Any, repository: Repository, *, clock: Clock | None=None) -> SharedDailyEnvelope` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 858)
- `capped_message(vault: Any) -> str` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 873)
- `admission_problem(vault: Any, repository: Repository, *, client: Any | None=None, clock: Clock | None=None) -> tuple[str, str] | None` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 878) — Why a judgment would be refused now, before any call: ``(reason, message)`` or None.
- `class ProtectionChanged(BaseException)` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 899) — A coverage request or record refused: a section it reads is protected now, the predicate cannot be read, or another vault is open.
- `class GateClosed(ProtectionChanged)` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 911) — The caller's gate (``CoverageGuard(gate=...)``) is closed on the snapshot being admitted: nothing more is sent or recorded (curriculum C1's automatic refresh, its switches turned off; Reader follow-ups Nov 1).
- `vault_on_disk(root: Path | str) -> Any` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 928) — The vault as its files say now, for a caller with no loaded-vault provider (the CLI: the desktop may change a source's role meanwhile; re-review F1).
- `published_snapshot(live_vault: Callable[[], Any] | None, root: Path | str) -> tuple[Any | None, Any]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 947) — ``(the vault now, its reload generation or None)``, read as one snapshot: the provider's ``snapshot()`` when it has one (the sidecar's), else the provider and its ``generation()``; with no provider, the files loaded again (:func:`vault_on_disk`).
- `still_published(live_vault: Callable[[], Any] | None, generation: Any) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 962) — Whether the snapshot of ``generation`` is still the published one (compared under the provider's publication lock when it has ``admit``).
- `protection_on_disk(vault: Any, repository: Repository) -> Protection` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 974) — :func:`read_protection` of the vault's files now (:func:`vault_on_disk`).
- `class CoverageGuard` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 980) — One judgment's protection check, before every physical request it makes (the context's request gate, so a retry or a provider's own follow-up is checked again) and before each record it writes.
  - `__init__(self, library: Library, keys: Iterable[tuple[str, str]], *, live_vault: Callable[[], Any] | None=None, gate: Callable[[Any], bool] | None=None, also: Callable[[Any], str | None] | None=None, also_refusal: type[BaseException]=ProtectionChanged) -> None` (line 1016; internal)
  - `_snapshot(self) -> tuple[Any | None, Any]` (line 1036; internal) — ``(the vault now, its reload generation or None)``, read as one snapshot.
  - `_still_published(self, generation: Any) -> bool` (line 1041; internal)
  - `_refusal(self) -> tuple[str, type[BaseException]] | None` (line 1044; internal) — Why the judgment may send or record nothing more now, and what that raises (None: it may).
  - `check(self, purpose: str='request') -> None` (line 1088; public) — Raise :class:`ProtectionChanged` (:class:`GateClosed` when the gate is closed, or ``also_refusal``) when the judgment may send or record nothing more.
  - `admit(self, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> Any` (line 1100; public)
  - `settle(self, admission: Any, usage: dict[str, Any]) -> None` (line 1113; public)
- `judge(vault: Any, repository: Repository, learning_object_id: str, *, library: Library | None=None, client: Any | None=None, embedder: Any | None=None, clock: Clock | None=None, budget: SpendBudget | None=None, candidates: Sequence[Candidate] | None=None, before_call: Callable[[int], str | None] | None=None, live_vault: Callable[[], Any] | None=None) -> JudgeResult` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1197) — Judge one LO's coverage across the library: no call when its current state is stored; otherwise one listwise call, then its RW4e proposals and its rows in one transaction (they mark the state done; a run that stopped before the commit is answered from the ledger next time, under…
- `cover(vault: Any, repository: Repository, learning_object_ids: Sequence[str], *, client: Any | None=None, embedder: Any | None=None, clock: Clock | None=None, cancelled: Callable[[], bool]=lambda: False) -> list[JudgeResult]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1323) — Judge each LO in turn; protection is read again before each (a library that is unchanged is reused).
- `on_extract_reason(config: Any) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1354) — Why a completed extraction queues no coverage job (None: it does).
- `covered_learning_objects(repository: Repository) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1365) — Every LO some judgment has covered (the on-extract job's work list).
- `rejudge_on_extract(vault: Any, repository: Repository, extraction_id: str, *, client: Any | None=None, embedder: Any | None=None, clock: Clock | None=None, cancelled: Callable[[], bool]=lambda: False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1376) — The on-extract job: judge every covered LO again, so the new (or re-read) reading's candidate sections join its next judgment (§6.3).
- `source_learning_objects(vault: Any, repository: Repository, library: Library, extraction_id: str) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1436) — The LOs a book's sections are judged against: the ones its sections' provenance cites, the ones coverage already names on it, then every active LO of the subjects it belongs to (a source set naming the book, or the subjects of the LOs it is cited for); with no subject known, eve…
- `query_embedding_plan(vault: Any, repository: Repository, query: str, *, embedder: Any | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1464) — What a real run's Qwen query embedding for this LO would cost (a dry run's estimate; no call, no write).
- `cover_source(vault: Any, repository: Repository, extraction_id: str, *, dry_run: bool=False, client: Any | None=None, embedder: Any | None=None, clock: Clock | None=None, cancelled: Callable[[], bool]=lambda: False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1515) — Judge a book's sections against the LOs their candidates suggest (§6.2, owner-run; never on a hot path).
- `class Standing` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1667)
  - `about(self) -> bool` (line 1683; public)
- `standing(vault: Any, repository: Repository, library: Library, learning_object_ids: Iterable[str]) -> dict[str, dict[tuple[str, str], Standing]]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1687) — Per LO, its standing row per section: the rows of its current judgment that still describe the section and the LO as they are now (a changed section or statement drops them), with the newest learner correction per section standing over them.
- `section_learning_objects(vault: Any, repository: Repository, library: Library, extraction_id: str, section_id: str) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1762) — The LOs a pressed check judges for a section: its provenance-linked LOs and every LO a coverage row (judge or learner) names for it.
- `correct(vault: Any, repository: Repository, extraction_id: str, section_id: str, learning_object_id: str, choice: str, *, text: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1778) — *Not about this* / *also about…* (or ``none``, clearing one): one ``learner_card`` ledger verdict and one ``learner`` row, nothing else.
- `dismiss(vault: Any, repository: Repository, origin: tuple[str, str], target: tuple[str, str], *, operation_id: str, undo_of: str | None=None, learning_object_ids: Sequence[str] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1878) — *Not about this* on an unchecked hit (``undo_of``: undo that operation), in one transaction.
- `peek(vault: Any, repository: Repository, extraction_id: str, section_id: str, *, cache: LibraryCache | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1985) — A section's first blocks, from its jump locator, for CA5a's peek.
- `section_text(vault: Any, repository: Repository, extraction_id: str, section_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 2023) — A whole section's blocks, from its jump locator, for side by side's second pane.
- `correspondents(vault: Any, repository: Repository, extraction_id: str, section_id: str, *, search_fallback: bool=True, embedder: Any | None=None, cache: LibraryCache | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 2148) — From one section, the other books' sections that treat the same LOs (judged coverage), or, with none and ``search_fallback``, the live search hits per book labelled *found by search, not checked*.

### Module constants

- `TREATMENTS` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 119)
- `ABOUT` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 120)
- `TREATMENT_WORDS` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 122)
- `ORIGINS` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 126)
- `OVERRIDES` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 128)
- `ROUTE_TASK` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 130)
- `LEDGER_TASK` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 131)
- `LEDGER_LEFT` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 132)
- `LEDGER_RIGHT` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 133)
- `PROMPT_VERSION` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 134)
- `CORRECTION_VERSION` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 135)
- `ENVELOPE` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 136)
- `CURRICULUM_OWNER_KINDS` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 140)
- `COVER_CAP_SETTING` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 142)
- `SEARCH_CONSUMER` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 144)
- `FALLBACK_CONSUMER` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 145)
- `MODELS_ENV` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 148)
- `UNCHECKED_LABEL` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 149)
- `NOTATION_LABEL` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 150)
- `SECTIONS_PER_SOURCE` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 156)
- `HITS_PER_SOURCE` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 159)
- `PASSAGE_CHARS` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 161)
- `STATEMENT_CHARS` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 162)
- `NOTE_CHARS` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 163)
- `MAX_TEXT_CHARS` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 165)
- `_CHARS_PER_TOKEN` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 167)
- `_OVERHEAD_CHARS` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 169)
- `COVERAGE_TASK` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 720)
- `_INSTRUCTIONS` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 733)
- `STOPPING` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 853)
- `STALE_MESSAGE` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 854)
- `GATE_CLOSED` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 918)
- `RELOAD_RETRIES` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 925)
- `ON_EXTRACT_JOB` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1351)
- `PAIR_TASK` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1844)
- `PAIR_KIND` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1845)
- `PAIR_VERSION` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1846)
- `_OPERATION_ID` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1847)
- `PEEK_BLOCKS` ([src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1982)

### Explicit exports

`__all__` declares:

- `ON_EXTRACT_JOB`
- `covered_learning_objects`
- `on_extract_reason`
- `rejudge_on_extract`
- `ABOUT`
- `COVERAGE_TASK`
- `STALE_MESSAGE`
- `STOPPING`
- `LEDGER_TASK`
- `MODELS_ENV`
- `ORIGINS`
- `OVERRIDES`
- `PAIR_TASK`
- `PEEK_BLOCKS`
- `PROMPT_VERSION`
- `ROUTE_TASK`
- `SECTIONS_PER_SOURCE`
- `TREATMENTS`
- `TREATMENT_WORDS`
- `UNCHECKED_LABEL`
- `Candidate`
- `CoverageError`
- `CoverageGuard`
- `GATE_CLOSED`
- `GateClosed`
- `JudgeResult`
- `Library`
- `LibraryCache`
- `Protection`
- `ProtectionChanged`
- `Section`
- `SectionCoverageOutputV1`
- `Standing`
- `admission_problem`
- `build_prompt`
- `candidates_for`
- `correct`
- `correspondents`
- `cover`
- `cover_source`
- `dismiss`
- `enabled`
- `judge`
- `lo_hash`
- `lo_query`
- `models_off`
- `peek`
- `query_embedding_plan`
- `read_protection`
- `scope_signature`
- `search_sections`
- `section_learning_objects`
- `section_text`
- `source_learning_objects`
- `standing`
- `state_key`

## Internal implementation anchors

- `_one_line(text: Any, limit: int=NOTE_CHARS) -> str` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 195)
- `_active(vault: Any, lo_id: str) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 525)
- `_query_vectors(vault: Any, repository: Repository, query: str, *, deep: bool, embedder: Any | None, owner_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 552) — The LO's Qwen query vector, embedded once for every source's search.
- `_kept_keys(vault: Any, repository: Repository, learning_object_ids: Sequence[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 611) — RW4d's kept comparisons on these LOs (held-out ones left out, fail closed), while keep is on.
- `_clean_roles(values: Any) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 820)
- `_daily_if_inactive(vault: Any, repository: Repository, clock: Clock | None) -> SharedDailyEnvelope | None` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 865) — The daily envelope, unless a caller (the owner-run batch) has it active already.
- `_write_rows(repository: Repository, library: Library, learning_object: Any, candidates: Sequence[Candidate], prompt: Prompt, key: str, rows: Mapping[tuple[str, str], Mapping[str, Any]], model: str, clock: Clock | None, guard: CoverageGuard | None=None, *, vault: Any | None=None, claims: Sequence[Mapping[str, Any]]=()) -> None` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1122) — The judgment's RW4e role proposals (``claims``) and its rows, in one transaction (re-review F10): a proposal changes the sections' roles, so the rebuilt prompt, and with it the ledger lookup a stopped run is resumed by.
- `_proposal_claims(prompt: Prompt, rows: Mapping[tuple[str, str], Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1171) — The RW4e role claims the ledger records for this prompt's passages (each section's ``passages``), so a judgment answered from the ledger (a run that stopped before applying them) yields the same claims as the paid answer did (Codex review F5).
- `_judge(vault: Any, repository: Repository, learning_object: Any, *, library: Library, client: Any | None, embedder: Any | None, clock: Clock | None, budget: SpendBudget | None, candidates: Sequence[Candidate] | None, before_call: Callable[[int], str | None] | None, live_vault: Callable[[], Any] | None) -> JudgeResult` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1232)
- `_run_usage(results: Sequence[JudgeResult], budget: SpendBudget, command: SpendEnvelope, route: Any, *, subscription: bool, price: float | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1494) — The run's usage (Codex review F9, as ``role_labeller._usage``): the judge's tokens and dollars estimated from each call's reported usage (``estimated_only`` on a subscription; unknown with no price), and apart, the metered dollars the run's envelope was charged (a metered judge'…
- `_order(entry: Standing) -> tuple[int, int, str, str]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1757)
- `_write_correction(connection: sqlite3.Connection, vault: Any, section: Section, learning_object_id: str, choice: str, words: str | None, now: str, *, operation_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1802) — One learner correction in the caller's transaction: its ``learner_card`` verdict and its ``learner`` row (CA5a's dismissal names its operation).
- `_pair_id(operation_id: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1850)
- `_section_ref(extraction_id: str, section_id: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1854)
- `_readable_section(library: Library, extraction_id: str, section_id: str) -> Section` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1858)
- `_operation_view(row: Mapping[str, Any], *, replayed: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1868)
- `_pair_dismissed(repository: Repository, origin: Section) -> set[str]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 1965) — The hits the learner said are not about this section (the newest pair verdict per hit).
- `_done(progress: Mapping[str, Mapping[str, Any]], section_id: str) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 2074)
- `class _Progress` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 2084)
- `_section_view(section: Section, *, read: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 2099)
- `_kept_between(vault: Any, repository: Repository, library: Library, origin: Section, learning_object_ids: Sequence[str]) -> dict[tuple[str, str], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 2106) — Per other section, what the learner kept comparing it with the origin (RW4d; held-out keeps left out): when, and the fine labels of the kept relations whose two ends are the origin and that section (Codex review F6: a comparison of three sections never lends one pair's relation…
- `_withheld_view(extraction_id: str, section_id: str, message: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 2143)
- `_fallback(vault: Any, repository: Repository, library: Library, origin: Section, learning_object_ids: Sequence[str], rows: Mapping[str, Mapping[tuple[str, str], Standing]], progress: _Progress, *, embedder: Any | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/section_coverage.py), line 2222) — The live search hits per other book for a section with no judged correspondent: its title, its LOs' titles and its lead passage as the query, by keyword only: no model call, no query embedding, no write (Codex review F7).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/curriculum|learnloop.cli.curriculum]] — imports `CoverageError`, `cover_source`, `enabled`; statically calls `cover_source`, `enabled`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `ON_EXTRACT_JOB`, `covered_learning_objects`, `module`, `on_extract_reason`; statically calls `covered_learning_objects`, `on_extract_reason`, `rejudge_on_extract`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `CoverageError`, `read_protection`; statically calls `read_protection`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `module`; statically calls `CoverageGuard`, `Library`, `_active`, `lo_hash`, `standing`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `module`; statically calls `CoverageGuard`, `Library`, `correct`, `enabled`, `read_protection`
- [[Reference/Modules/learnloop/source_retrieval/note_gaps|learnloop.source_retrieval.note_gaps]] — imports `module`; statically calls `Library`, `peek`
- [[Reference/Modules/learnloop/source_retrieval/note_links|learnloop.source_retrieval.note_links]] — imports `module`; statically calls `CoverageGuard`, `Library`, `peek`, `published_snapshot`, `still_published`
- [[Reference/Modules/learnloop/source_retrieval/vault_notes|learnloop.source_retrieval.vault_notes]] — imports `module`; statically calls `read_protection`
- [[Reference/Modules/learnloop/teacher/actions|learnloop.teacher.actions]] — imports `Library`; statically calls `Library`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `CoverageError`, `Library`, `read_protection`; statically calls `Library`, `read_protection`
- [[Reference/Modules/learnloop/teacher/diagnosed_sources|learnloop.teacher.diagnosed_sources]] — imports `module`; statically calls `search_sections`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `CoverageError`, `Library`; statically calls `Library`
- [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]] — imports `module`; statically calls `LibraryCache`, `correct`, `correspondents`, `dismiss`, `enabled`, `peek`
- [[Reference/Modules/learnloop_sidecar/handlers/deliverables|learnloop_sidecar.handlers.deliverables]] — imports `module`; statically calls `Library`, `admission_problem`, `judge`
- [[Reference/Modules/learnloop_sidecar/handlers/side_by_side|learnloop_sidecar.handlers.side_by_side]] — imports `module`; statically calls `enabled`, `section_text`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`; calls `AIInterrupted`, `AIInvalidOutput`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `active_request_gate`, `call_labels`, `content_key`, `gate_model_requests`; calls `active_request_gate`, `call_labels`, `content_key`, `gate_model_requests`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `quiet`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendEnvelope`, `active_envelopes`, `spend_envelopes`; calls `SpendBudget`, `SpendCaps`, `SpendEnvelope`, `active_envelopes`, `spend_envelopes`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `module`; calls `exam_material`, `source_marks`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/section_coverage|learnloop.db.stores.section_coverage]] — imports `module`; calls `corrections`, `insert`, `judged`, `judged_states`, `learning_objects_named`, `table_present`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `protection_issues`; calls `protection_issues`
- [[Reference/Modules/learnloop/practice_index/listwise|learnloop.practice_index.listwise]] — imports `ListwiseTask`, `judge_listwise`, `listwise_caps`, `route_skip`, `task_output_tokens`; calls `ListwiseTask`, `judge_listwise`, `listwise_caps`, `route_skip`, `task_output_tokens`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `PaidCalls`, `estimated_call_tokens`, `plan_route`; calls `PaidCalls`, `estimated_call_tokens`, `plan_route`
- [[Reference/Modules/learnloop/practice_index/query_vectors|learnloop.practice_index.query_vectors]] — imports `cached_query_vectors`, `estimated_tokens`, `normalize_query`, `query_embedding_price`; calls `cached_query_vectors`, `estimated_tokens`, `normalize_query`, `query_embedding_price`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `extraction_sections`; calls `extraction_sections`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `learning_objects_by_section`; calls `learning_objects_by_section`
- [[Reference/Modules/learnloop/reader/source_render_views|learnloop.reader.source_render_views]] — imports `sanitize_source_text`; calls `sanitize_source_text`
- [[Reference/Modules/learnloop/reader/source_roles|learnloop.reader.source_roles]] — imports `module`; calls `best_roles`, `clean_roles`, `on_demand_enabled`, `propose_roles`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `Scope`, `SourceExtraction`, `exercise_and_solution_spans`, `library_scope`, `teaching_exclusions`; calls `Scope`, `exercise_and_solution_spans`, `library_scope`, `teaching_exclusions`
- [[Reference/Modules/learnloop/source_retrieval/feedback|learnloop.source_retrieval.feedback]] — imports `deliver`; calls `deliver`
- [[Reference/Modules/learnloop/source_retrieval/kept_comparisons|learnloop.source_retrieval.kept_comparisons]] — imports `module`; calls `keep_enabled`, `kept_comparisons_for_card`
- [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]] — imports `MAX_QUERY_CHARS`, `QUERY_RECORD_KIND`, `embed_query_texts`, `query_id`; calls `embed_query_texts`, `query_id`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `search_spans`; calls `search_spans`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `SharedDailyEnvelope`, `midnight`; calls `SharedDailyEnvelope`, `midnight`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `settled_load_vault`; calls `settled_load_vault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `os`, `pathlib`, `re`, `sqlite3`, `threading`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/curriculum|learnloop.cli.curriculum]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]], [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]], [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] and 10 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/deliverable_fixtures.py](../../../../../../tests/deliverable_fixtures.py) — direct import
- [tests/section_coverage_fixtures.py](../../../../../../tests/section_coverage_fixtures.py) — direct import
- [tests/test_coverage_on_extract.py](../../../../../../tests/test_coverage_on_extract.py) — direct import
  - `test_an_extraction_queues_the_job_only_while_both_switches_are_on`
  - `test_one_live_job_at_a_time`
  - `test_the_handler_is_registered_and_known`
  - `test_the_job_rejudges_covered_los_a_new_book_joins_and_a_fresh_state_pays_nothing`
  - `test_the_job_runs_quiet_and_never_offers_openrouter`
- [tests/test_curriculum_c0b_landing.py](../../../../../../tests/test_curriculum_c0b_landing.py) — direct import
  - `test_i_a_dismissal_and_an_also_about_on_one_section_coexist_through_path_rejudgments`
- [tests/test_curriculum_c1_plan_follows_path.py](../../../../../../tests/test_curriculum_c1_plan_follows_path.py) — direct import
  - `test_a_withheld_path_plans_nothing`
- [tests/test_curriculum_c3_exam_scoping.py](../../../../../../tests/test_curriculum_c3_exam_scoping.py) — direct import
  - `test_a_syllabus_never_teaches_and_is_never_a_coverage_candidate`
  - `test_gc1_no_request_correspondent_path_row_or_slice_names_exam_material`
  - `test_gc1_note_link_judge_requests_carry_no_exam_material_from_sources`
- [tests/test_deliverable_codex_review.py](../../../../../../tests/test_deliverable_codex_review.py) — direct import
  - `test_f3_a_switch_turned_off_after_queueing_stops_the_job`
  - `test_f3_a_switch_turned_off_between_los_stops_the_rest`
  - `test_f3_judge_itself_refuses_with_the_curriculum_off`
  - `test_f7_a_running_job_does_not_swallow_a_new_extraction`
- [tests/test_deliverable_rpcs.py](../../../../../../tests/test_deliverable_rpcs.py) — direct import
  - `test_an_lo_with_no_candidate_is_searched_once_per_session_not_on_every_read`
- [tests/test_deliverable_scope.py](../../../../../../tests/test_deliverable_scope.py) — direct import
  - `test_scope_view_lists_topics_unmatched_and_the_receipt`
- [tests/test_ih7_lesson_sources_follow_diagnosis.py](../../../../../../tests/test_ih7_lesson_sources_follow_diagnosis.py) — direct import
  - `test_a_section_held_out_after_the_fact_is_revoked_for_the_lesson`
  - `test_the_query_is_the_diagnosed_statement_never_an_expected_answer_a_rubric_or_the_analysis`
- [tests/test_notes_as_learner_text.py](../../../../../../tests/test_notes_as_learner_text.py) — direct import
  - `test_gc1_exam_sentinels_never_reach_the_gap_model_via_a_notes_context`
- [tests/test_notes_c2b_review5.py](../../../../../../tests/test_notes_c2b_review5.py) — direct import
  - `test_c2b_final_verify_f1_the_notes_guard_judges_a_candidate_by_every_anchor_it_ever_had`
  - `test_c2b_r5_f2_a_notes_reading_records_its_anchor_heading_and_every_section_span`
- [tests/test_notes_linked.py](../../../../../../tests/test_notes_linked.py) — direct import
  - `test_landing_the_coverage_guard_composes_c1s_gate_and_c2s_also`
  - `test_re_f2_the_composed_gate_admits_on_one_snapshot`
- [tests/test_notes_vault_search.py](../../../../../../tests/test_notes_vault_search.py) — direct import
  - `test_an_unreadable_protection_predicate_keeps_every_annotation_out`
- [tests/test_reader_ca5_also_in_books.py](../../../../../../tests/test_reader_ca5_also_in_books.py) — direct import
  - `test_an_unreadable_protection_predicate_shows_nothing_through_the_cache`
  - `test_crossing_sections_reuses_one_library_and_parses_each_reading_once`
  - `test_the_judged_list_is_by_lo_with_treatments_notation_and_read_marks_and_no_model_call`
- [tests/test_reader_ca5a_find_section.py](../../../../../../tests/test_reader_ca5a_find_section.py) — direct import
  - `test_f1_a_peek_is_bounded_to_the_first_blocks`
  - `test_f3_a_failure_inside_the_operation_leaves_nothing`
  - `test_f6_an_unmapped_section_can_say_not_about_this_and_undo_it`
  - `test_the_hits_are_grouped_by_book_unchecked_and_write_nothing`
- [tests/test_reader_ca6_side_by_side.py](../../../../../../tests/test_reader_ca6_side_by_side.py) — direct import
  - `test_a_side_by_side_read_holds_a_follow_up_on_a_shown_span_and_only_there`
- [tests/test_section_coverage.py](../../../../../../tests/test_section_coverage.py) — direct import
  - `test_a_big_book_never_crowds_out_a_small_one`
  - `test_a_changed_section_drops_its_row`
  - `test_a_changed_statement_makes_old_rows_stale_until_rejudged`
  - `test_a_correction_on_protected_material_is_refused`
  - `test_a_failed_judgment_writes_nothing`
  - `test_a_protected_section_has_no_correspondents`
  - `test_an_answer_that_skips_a_section_is_never_stored`
  - `test_candidates_are_provenance_then_retrieval_per_source`
  - `test_corrections_stand_over_the_judge_across_rejudgments`
  - `test_correspondents_join_on_the_lo_and_are_symmetric`
  - `test_models_off_and_an_unrouted_judge_make_no_call`
  - `test_no_exam_or_held_out_text_reaches_the_judge`
  - `test_one_listwise_judgment_writes_one_row_per_candidate_and_caches`
  - `test_rw4e_proposals_are_written_by_the_coverage_judge`
  - `test_the_library_leaves_out_exam_and_held_out_material`
  - `test_the_search_fallback_is_labelled_unchecked_and_writes_nothing`
  - `test_the_table_is_append_only`
- [tests/test_section_coverage_review.py](../../../../../../tests/test_section_coverage_review.py) — direct import
  - `test_f1_a_batch_reads_protection_again_before_each_lo`
  - `test_f1_a_retry_after_protection_changed_is_never_sent`
  - `test_f1_protection_marked_during_the_call_keeps_nothing`
  - `test_f2_query_embeddings_are_held_to_the_curriculum_caps`
  - `test_f2_the_dry_run_estimates_the_query_embeddings`
  - `test_f3_a_failed_qwen_query_still_searches_deep`
  - `test_f4_returning_to_a_judged_state_reads_its_rows_again`
  - `test_f5_a_crash_before_the_proposals_is_recovered_without_a_call`
  - `test_f6_kept_relations_join_only_their_own_endpoints`
  - `test_f7_the_search_fallback_embeds_and_logs_nothing`
  - `test_f9_a_subscription_run_reports_tokens_and_estimated_dollars`
  - `test_landing_f1_a_reload_with_invalid_source_sets_is_never_admitted`
  - `test_landing_f1_admission_refuses_a_vault_whose_source_sets_did_not_load`
  - `test_landing_f1_cover_refuses_when_source_sets_turn_invalid_mid_batch`
  - `test_landing_f1_source_sets_turning_invalid_during_a_cli_judgment_keep_nothing`
  - `test_landing_f1_the_cli_batch_refuses_when_source_sets_turn_invalid_mid_batch`
  - `test_rr_f10_a_crash_after_the_proposals_is_recovered_from_the_ledger`
  - `test_rr_f1_a_reload_published_during_the_protection_read_is_never_admitted`
  - `test_rr_f1_a_retry_after_a_role_changed_on_disk_is_never_sent`
  - `test_rr_f1_a_role_changed_on_disk_during_a_cli_judgment_keeps_nothing`
  - `test_rr_f1_the_cli_batch_reads_source_sets_from_disk_before_each_lo`
- [tests/test_section_coverage_rpcs.py](../../../../../../tests/test_section_coverage_rpcs.py) — direct import
  - `test_cover_source_judges_and_caps_a_metered_run`
  - `test_cover_source_refuses_a_withheld_reading`

## Modification guidance

- Make changes here when the responsibility remains section coverage within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/section_coverage.py](../../../../../../src/learnloop/source_retrieval/section_coverage.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
