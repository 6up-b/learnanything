---
title: "learnloop.content.pipeline.add_source"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/pipeline/add_source.py"
source_paths:
  - "src/learnloop/content/pipeline/add_source.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.pipeline"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.pipeline.add_source module"
  - "src/learnloop/content/pipeline/add_source.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-pipeline"
---

# `learnloop.content.pipeline.add_source`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.pipeline.add_source` exists within [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] to own the behavior summarized by its module contract: One Add for any source (UX Phase 1, docs/specs/ux_learnloop_v1.md §6).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py) |
| Source lines | 2791 |
| Owning package | [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class AddSourceOptions` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 133) — Add → More options (spec §8.2).
- `kind_noun(category: str | None) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 141)
- `source_kind_noun(repo, source_id: str, category: str | None) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 154) — What the learner calls this source: ``kind_noun``, except that a PDF whose text is ready is a paper (short, opening with an Abstract), a book (longer than a handout) or, when it is a few pages, still a PDF.
- `add_source(vault, ingest_jobs, source: str, options: AddSourceOptions | None=None, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 189) — Add one source and return the item the Library and Reader open.
- `local_display_title(path: Path, raw_bytes: bytes, category: str | None) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 279) — A readable title for a local file: the PDF's own title when it has a real one, else the file name in words (never a ``file://`` URI).
- `pdf_metadata_title(raw_bytes: bytes) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 290) — The PDF's own title when it has a real one (not "Untitled", not a file name), else ``None``.
- `learner_title(artifact: Mapping[str, Any], revision: Mapping[str, Any] | None) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 319) — The card and Reader title: display title, else a file name in words.
- `class Chapter` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 346) — A top-level unit of the outline with every unit nested under it.
- `outline_chapters(outline) -> list[Chapter]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 356)
- `readable_label(label: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 389) — A heading slug (``1-probability-and-counting``, how the Markdown extractor keys sections) back into words; real titles pass unchanged.
- `reading_order_scope(chapters: Sequence[Chapter], *, built: Iterable[str]=(), start_unit_id: str | None=None, cap_tokens: int, floor_tokens: int=FLOOR_TOKENS, ahead: int=1) -> list[Chapter]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 407) — The first build: the chapter the learner starts in, plus ``ahead`` more.
- `chapters_to_keep_ahead(chapters: Sequence[Chapter], section_unit_id: str, built: Iterable[str]) -> list[Chapter]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 444) — While reading: the chapter holding ``section_unit_id`` and the next one, minus what is already built (or nothing, outside every chapter).
- `chapter_phrase(labels: Sequence[str], *, whole: bool=False, noun: str='book') -> str` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 456) — ``Ch.
- `class AuthoringRoute` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 486)
  - `consented(self, config) -> bool` (line 496; public) — The learner's OK to send this build to the provider: recorded, or the yes on its offer.
- `consent_key(config, provider_name: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 502) — The consent identity for a provider: one OK covers its whole family.
- `consent_label(key: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 518)
- `what_leaves(label: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 522)
- `upload_consent_key(flow: str | None) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 529) — Which recorded OK covers an upload ``flow`` (jobs' guard flows).
- `file_upload_allowed(config, flow: str | None=None) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 535) — The learner's separate OK for sending a whole file out (a recording to be transcribed, a whole PDF to a model that reads PDFs, a document to z.ai for GLM-OCR, which has its own).
- `pending_upload_flow(repo, *, source_id: str | None=None, batch_id: str | None=None) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 544) — The upload a book's (or an Add's) import is waiting for the OK on, so the OK given is the one its card named.
- `authoring_route_for(vault_root: Path, config) -> AuthoringRoute` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 561) — The route that would write questions for a build, and whether it is ready, the way the build resolves it.
- `default_authoring_route(ctx) -> AuthoringRoute` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 596)
- `is_subscription_route(config, provider_name: str | None) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 637)
- `plan_tokens(totals: Mapping[str, Any]) -> int` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 647)
- `estimate_usd(config, provider_name: str, totals: Mapping[str, Any]) -> float` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 651) — A metered route's price for a build plan: input plus maximum output.
- `cost_pause_reason(config, usd: float, spent_today_usd: float) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 657) — ``over_threshold`` / ``daily_cap`` when a build should ask first (Q5).
- `metered_spend_usd(config, rows: Iterable[Mapping[str, Any]]) -> float` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 687)
- `build_spend_usd(repo, config, batch_id: str) -> float` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 710) — What one automatic build has cost so far, every attempt included.
- `spent_today_usd(repo, config, now: datetime) -> float` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 717) — Money spent today on every model call LearnLoop made (receipts), plus what automatic builds still running are allowed to spend.
- `auto_build_spend_report(vault, repo, *, days: int=7, top: int=5, now: datetime | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 736) — Automatic book preparation's actual spend, for setting caps from real use (owner, 2026-10-13: spend is observed before caps are set).
- `class CostDecision` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 867) — What an automatic build may spend, and whether it must ask first.
  - `cost_basis(self) -> str` (line 878; public)
  - `as_dict(self) -> dict[str, Any]` (line 881; public)
- `decide_cost(config, repo, provider_name: str, totals: Mapping[str, Any], *, approved: bool, now: datetime) -> CostDecision` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 893) — Price a build plan and decide: run silently, ask first (``over_threshold`` / ``daily_cap``: "Build them" passes these), or stop (``budget_used``: the daily cap is spent; "Build them" does not pass it).
- `admit_auto_build_job(ctx, *, planned_tokens: int | None=None) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 925) — Admit one paid job attempt of an automatic build, or stop it (F1-F5), and admit each of its model requests (re-review F2).
- `auto_apply_allowed(ctx) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1078) — Read immediately before an automatic build applies (F4, F5): the kill switches and the Undo generation, as they are now.
- `subject_title_from(title: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1102) — A subject name from a book title: drop the author part, editions and subtitles, keep at most eight words.
- `ensure_subject(vault_root: Path, vault, source_id: str, title: str, *, clock: Clock | None=None) -> tuple[str, bool]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1113) — The subject this source is filed under, creating a provisional one named from the book when nothing fits.
- `child_batch_id(planner_job_id: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1139) — The build batch a planning job queues: derived from the planner, so a planner that dies after queuing it finds it again (review F3) and status, coverage and Undo find it even when the planner never saved its result.
- `auto_jobs(repo, source_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1153) — This source's planning jobs, newest first: the whole history, filtered by source in SQL before anything is limited (review F10).
- `import_jobs(repo, source_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1160)
- `planner_outcome(repo, job: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1183) — What a planning job decided: its saved result, or (when it died after queuing its build) the plan its build batch carries.
- `latest_auto_outcome(repo, source_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1196)
- `current_generation(repo, source_id: str) -> int` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1204)
- `class Coverage` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1257) — Which chapters of a book automatic builds cover (review F6).
  - `covered(self) -> set[str]` (line 1269; public) — What a new build must not plan again.
- `coverage(repo, source_id: str, *, exclude_job_id: str | None=None) -> Coverage` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1275)
- `built_unit_ids(repo, source_id: str) -> set[str]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1303) — Chapters an automatic build covers or is building, and not undone.
- `class BuildPlanChoice` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1354) — What a build would cover, and its plan totals (no writes, no calls).
  - `info(self) -> dict[str, Any]` (line 1371; public)
- `exam_material_units(vault, repo, source_id: str, revision_id: str | None, extraction_id: str) -> frozenset[str] | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1422) — The book's units that are exam material, by the one exam predicate (``content.sources.exam_material``, read through ``source_retrieval.corpus.source_exam_exclusions``: exam-role members and unit overrides in every revision, outline role picks ``exam``, and every ``held_out_evalu…
- `preview_auto_build(vault_root: Path, repo, source_id: str, *, whole_book: bool=False, chapter_ids: Sequence[str] | None=None, approved: bool=False, route: AuthoringRoute | None=None, now: datetime | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1467) — The zero-call dry run of an automatic build (review F2): what it would cover, the route, tokens, money and whether it would ask first or stop.
- `run_auto_study_map(ctx) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1524) — Plan (and queue) the automatic question build for one source.
- `after_auto_build(ctx) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1676) — An automatic build's synthesis finished: act on reading progress that arrived while it ran (review F7).
- `request_auto_build(ingest_jobs, source_id: str, *, approved: bool=False, chapter_ids: Sequence[str] | None=None, start_unit_id: str | None=None, answers_revision: int | None=None) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1722) — Plan another automatic build for ``source_id`` (connect, build now, keep ahead).
- `release_waiting_builds(ingest_jobs) -> list[str]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1748) — After an AI is connected: plan again for every book waiting on it, and act on reading progress that waited (complete history, review F10).
- `reconcile_reading_builds(ingest_jobs, *, skip: Iterable[str]=()) -> list[str]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1800) — Act on every book's pending reading request: at startup, on reconnection (review F7).
- `plan_reading_advance(ingest_jobs, source_id: str, extraction_id: str, section_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1836) — Keep one chapter ahead of ``section_id`` (Q6), or say why not now.
- `act_on_reading_request(ingest_jobs, source_id: str, *, rearm: bool=False, now: datetime | None=None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1869) — Act on the book's pending reading request, exactly its current revision (finishing pass, F8 and F9).
- `books_of_batch(repo, batch_id: str) -> set[str]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1950) — The books whose automatic-build work a batch holds: an Add's or a build's planner, or a planner's build batch.
- `settle_reading_for_cancelled_batch(repo, batch_id: str) -> list[str]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1980) — A cancel answers the reading request of every book whose work the batch held (reading-hardening, part 1): each is settled at the revision it has now, so nothing re-plans the cancelled work behind the learner's back.
- `advance_reading_build(ingest_jobs, extraction_id: str, section_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2003) — The Reader reached ``section_id``: keep one chapter ahead (Q6).
- `keep_ahead_for_reader(ingest_jobs, extraction_id: str, section_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2020) — The Reader's progress RPC asks to keep one chapter ahead.
- `undo_source_questions(ingest_jobs, source_id: str, *, clock: Clock | None=None) -> int` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2087) — Take a book's automatic questions back out (one-tap undo, Q3).
- `glm_estimate_phrase(details: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2244) — " (404 pages, about $0.04)" from a z.ai OK's estimate, or "" without one.
- `text_recognition_available(*, config=None) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2274) — Whether an extractor that really recognises text can run (review F9): GLM-OCR (hosted with a z.ai key, or a self-hosted server), local Marker, or the hosted Marker runtime the owner configured.
- `build_minutes_phrase(repo, *, section_count: int, sample: int=5) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2344) — How long questions for ``section_count`` sections take, from this library's own finished automatic builds ("in about 4 min", "in under a minute"), or ``None`` when it has none to go on (usability round 2: "in about 13 min" was a made-up formula for a build that took seconds).
- `source_status_line(repo, vault, source_id: str | None, *, batch_id: str | None=None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2389) — The one quiet line a book card shows, or ``None`` when there is nothing to say.
- `pending_adds(repo, *, limit: int=30) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2632) — Adds whose link is still being fetched (no library card yet): every unfinished Add, not a window over the queue (review F10).
- `pending_title(source: str, category: str | None) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2659) — A readable name for a link still being fetched (usability round 1: the video's card was titled with its raw URL).
- `latest_add_batch(repo, source_id: str) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2677)
- `latest_planner(repo, source_id: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2682) — The planning job the card's line speaks for, and its outcome (a planner an Undo or a cancel stopped before it ran is skipped).
- `latest_build_batch(repo, source_id: str) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2694)
- `retry_build(ingest_jobs, source_id: str) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2702) — The card's Retry for a failed automatic build (§6.7, review F11): the zero-model repair and revalidation of a preserved candidate first; a fresh model run only when there is none, or repairing it already failed, and then under a new admission (a new attempt of each paid job).

### Module constants

- `AUTO_STUDY_MAP_JOB` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 62)
- `ADD_SOURCE_WORKFLOW` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 63)
- `AUTO_BUILD_WORKFLOW` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 64)
- `ADD_SOURCE_PRIORITY` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 67)
- `BUILD_PRIORITY` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 68)
- `UNSUPPORTED_MESSAGE` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 70)
- `MISSING_FILE_MESSAGE` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 73)
- `EXISTING_MESSAGE` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 74)
- `DATA_FLOW` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 75)
- `FILE_UPLOAD_CONSENT` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 78)
- `FILE_UPLOAD_DATA_FLOW` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 79)
- `GLM_OCR_UPLOAD_CONSENT` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 83)
- `AUTO_BUILD_BATCH_PREFIX` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 85)
- `UNDO_JUDGMENT_TASK` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 87)
- `TEXT_RECOGNITION_HOW_TO` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 92)
- `TEXT_RECOGNITION_UNAVAILABLE_MESSAGE` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 93)
- `FLOOR_TOKENS` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 99)
- `_KIND_NOUN` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 101)
- `_ROLE_BY_CATEGORY` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 113)
- `_CHAPTER_NUMBER` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 120)
- `_JUNK_PDF_TITLES` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 121)
- `_CONSENT_LABEL` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 124)
- `_ABSTRACT_LABEL` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 149)
- `_PAPER_MAX_PAGES` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 150)
- `_HANDOUT_MAX_PAGES` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 151)
- `_REVERTABLE_ITEM_TYPES` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1249)
- `_SCAN_DETAILS` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2173)
- `_RESTORE_READING_DETAILS` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2238)
- `_GLM_FAILED_DETAILS` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2291)
- `_GLM_NEEDS_OK_DETAILS` ([src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2294)

### Explicit exports

`__all__` declares:

- `ADD_SOURCE_PRIORITY`
- `ADD_SOURCE_WORKFLOW`
- `AUTO_BUILD_WORKFLOW`
- `AUTO_STUDY_MAP_JOB`
- `AddSourceOptions`
- `AuthoringRoute`
- `Chapter`
- `CostDecision`
- `Coverage`
- `act_on_reading_request`
- `add_source`
- `books_of_batch`
- `admit_auto_build_job`
- `advance_reading_build`
- `after_auto_build`
- `authoring_route_for`
- `auto_apply_allowed`
- `auto_build_spend_report`
- `built_unit_ids`
- `chapter_phrase`
- `child_batch_id`
- `consent_key`
- `consent_label`
- `cost_pause_reason`
- `coverage`
- `decide_cost`
- `default_authoring_route`
- `ensure_subject`
- `estimate_usd`
- `file_upload_allowed`
- `pending_upload_flow`
- `upload_consent_key`
- `keep_ahead_for_reader`
- `kind_noun`
- `source_kind_noun`
- `build_minutes_phrase`
- `pdf_metadata_title`
- `TEXT_RECOGNITION_HOW_TO`
- `latest_auto_outcome`
- `latest_planner`
- `learner_title`
- `outline_chapters`
- `pending_adds`
- `pending_title`
- `plan_reading_advance`
- `planner_outcome`
- `preview_auto_build`
- `reading_order_scope`
- `reconcile_reading_builds`
- `release_waiting_builds`
- `request_auto_build`
- `retry_build`
- `run_auto_study_map`
- `settle_reading_for_cancelled_batch`
- `source_status_line`
- `spent_today_usd`
- `text_recognition_available`
- `undo_source_questions`
- `what_leaves`

## Internal implementation anchors

- `_local_file(source: str) -> Path | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 272)
- `_display_title(artifact: Mapping[str, Any], revision: Mapping[str, Any] | None) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 307)
- `_completed_extraction(repo, source_id: str) -> tuple[str, str] | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 325)
- `_has_text_or_add_in_flight(repo, source_id: str) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 331)
- `_is_front_matter(chapter: Chapter) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 403)
- `_price_per_million(config, provider_name: str | None) -> float` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 628)
- `_receipt_usd(config, row: Mapping[str, Any]) -> float` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 674) — What one model call cost in money: the provider's reported cost, else its tokens at the route's price; nothing for a subscription call.
- `_day_start_iso(now: datetime) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 691)
- `_active_auto_build_batches(repo) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 697)
- `_batch_job_ids(repo, batch_id: str) -> list[str]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 706)
- `_receipt_tokens(row: Mapping[str, Any]) -> int` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 732)
- `_request_output_ceiling(config, job_type: str) -> int` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 998) — The output a request is reserved for when it names no ceiling of its own (epigraphs; append reconciliation names its own since K3.4): the configured per-operation output budget the pipeline holds its results to.
- `_request_gate(config, limit_usd: float | None, default_output_tokens: int, *, cancelled=None)` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1010)
- `_spend_paused(reason: str, details: Mapping[str, Any])` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1025)
- `_requests_admitted(gate, reason: str, details: Mapping[str, Any])` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1038) — Hold ``gate`` over every model request of the attempt; a request it refused stops the job as ``spend_paused`` (whatever the pipeline made of the refusal on its way out).
- `_cancel_rest_of_batch(ctx) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1062) — Stop the automatic build this job belongs to: the batch is flagged and its jobs still waiting go straight to cancelled (as a batch cancel does); the runner finishes this job as cancelled.
- `_job_source_id(job: Mapping[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1147)
- `_child_auto_info(repo, batch_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1164) — The plan an automatic build batch carries on its synthesis job.
- `_outcome_from_child(repo, batch_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1174)
- `_build_state(repo, outcome: Mapping[str, Any], *, generation: int | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1208) — What became of a ``building`` outcome's batch: its status, proposal, whether it applied, was taken back out, or left changes to look at.
- `_revertable(item: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1252)
- `_active(job_or_batch: Mapping[str, Any] | None) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1310)
- `_source_work_active(repo, source_id: str, *, ignore_batch_id: str | None=None) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1314)
- `_source_work_waiting_on(repo, source_id: str, *, ignore_batch_id: str | None=None) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1318) — Whether the book's automatic-build work is unfinished, and on whom: ``"worker"`` (some of it is queued or running), ``"learner"`` (all of it waits for the learner's input), or ``None`` (none is unfinished).
- `_source_from_dependency(ctx) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1343)
- `_choose_scope(repo, config, vault, source_id: str, resolved: tuple[str, str], *, chapter_ids: Sequence[str] | None, start_unit_id: str | None, exclude_job_id: str | None) -> BuildPlanChoice | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1377)
- `_without_units(chapters: Sequence[Chapter], withheld: frozenset[str]) -> list[Chapter]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1450) — Chapters minus their withheld units; a chapter left with none is dropped.
- `_keep_ahead_ready(repo, vault_root: Path, source_id: str) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1766) — Whether a book's questions may grow with reading now: it has an automatic build that was not undone, auto-build is on and nothing for it is running.
- `_wanted_chapters(repo, vault_root: Path, source_id: str, state: Mapping[str, Any]) -> list[str]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1785) — The chapters a pending reading request asks for (none: nothing to do).
- `_reading_retry_delay(ingest_jobs, attempts: int) -> float` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1923) — Seconds before the ``attempts``-th failed attempt is tried again: the host's delays in turn, the last one repeating (never given up).
- `_note_reading_failure(ingest_jobs, source_id: str, revision: int, attempts: int, *, now: datetime | None=None) -> None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1931) — Best effort: count a failed attempt, set its retry time and bring the sweep's next pass forward.
- `_extraction_source(repo, extraction_id: str) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 1996)
- `_record_undo_judgment(repo, source_id: str, proposal_id: str, item_ids: Sequence[str], generation: int, *, clock: Clock | None=None) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2049) — The learner's Undo is an owner verdict on automatically applied content (review F12): one ``judgment_ledger`` row per proposal, idempotent.
- `_import_waiting_for_upload_ok(repo, source_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2143) — The book's latest import, when it waits for an upload OK and its Add was not stopped.
- `_line(text: str, tone: str='quiet', action: tuple[str, str] | None=None, details: str | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2163)
- `_scan_unreadable(text: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2180)
- `_is_scan_failure(lowered: str) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2184) — An import that found no text layer at all: a scanned PDF.
- `_import_failure_line(job: Mapping[str, Any], category: str | None, *, config=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2190)
- `_reread_refused(repo, source_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2258) — A book that has a reading whose latest import (a re-read) refused because its original file changed: one plain line, no action that cannot help (re-read safety E1).
- `_health_line(repo, source_id: str, *, config=None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2300)
- `_scope_size(outcome: Mapping[str, Any]) -> int` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2338) — How many sections a build covers (its units, else its chapters).
- `_budget_used_line(details: str | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2384)
- `_study_map_questions(repo, source_id: str) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2557) — What study-map builds that read this book left (round-2 review F6): ``"applied"`` when a finished build's questions were applied and are still in, ``"pending"`` when a finished build's questions still wait for a look, else ``None``.
- `_built_phrase(repo, source_id: str, outcome: Mapping[str, Any], noun: str) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2589) — Every chapter the book's questions cover so far (``Ch.
- `_unit_tree(repo, extraction_id: str) -> Any` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2605) — Just the extraction's units (id, parent, label), enough for ``outline_chapters``' chapter list and labels: the card's line is read on every library poll and keeping a chapter ahead on every reading-progress report, and the full outline loads the book's text once per unit (usabil…
- `_category_of(source: Any) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/add_source.py), line 2625)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/ingest_batches|learnloop.cli.ingest_batches]] — imports `settle_reading_for_cancelled_batch`; statically calls `settle_reading_for_cancelled_batch`
- [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]] — imports `auto_build_spend_report`, `preview_auto_build`; statically calls `auto_build_spend_report`, `preview_auto_build`
- [[Reference/Modules/learnloop/content/pipeline/acquisition_preview|learnloop.content.pipeline.acquisition_preview]] — imports `file_upload_allowed`; statically calls `file_upload_allowed`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `ADD_SOURCE_PRIORITY`, `ADD_SOURCE_WORKFLOW`, `AUTO_BUILD_BATCH_PREFIX`, `AUTO_BUILD_WORKFLOW`, `AUTO_STUDY_MAP_JOB`, `AddSourceOptions`, `BUILD_PRIORITY`, `admit_auto_build_job`, `after_auto_build`, `auto_apply_allowed`, `file_upload_allowed`, `module`, `pdf_metadata_title`, `run_auto_study_map`; statically calls `AddSourceOptions`, `act_on_reading_request`, `admit_auto_build_job`, `after_auto_build`, `auto_apply_allowed`, `file_upload_allowed`, `pdf_metadata_title`, `run_auto_study_map`, `settle_reading_for_cancelled_batch`
- [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]] — imports `consent_key`; statically calls `consent_key`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `default_authoring_route`; statically calls `default_authoring_route`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `file_upload_allowed`; statically calls `file_upload_allowed`
- [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]] — imports `learner_title`; statically calls `learner_title`
- [[Reference/Modules/learnloop/remote/views|learnloop.remote.views]] — imports `learner_title`, `source_kind_noun`, `source_status_line`; statically calls `learner_title`, `source_kind_noun`, `source_status_line`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `reconcile_reading_builds`; statically calls `reconcile_reading_builds`
- [[Reference/Modules/learnloop_sidecar/handlers/as_printed|learnloop_sidecar.handlers.as_printed]] — imports `learner_title`; statically calls `learner_title`
- [[Reference/Modules/learnloop_sidecar/handlers/first_run|learnloop_sidecar.handlers.first_run]] — imports `module`; statically calls `AddSourceOptions`, `_completed_extraction`, `add_source`, `authoring_route_for`, `consent_label`, `file_upload_allowed`, `import_jobs`, `latest_add_batch`, `latest_planner`, `learner_title`, `outline_chapters`, `pending_upload_flow`, `release_waiting_builds`, `request_auto_build`, `retry_build`, `text_recognition_available`, `undo_source_questions`, `upload_consent_key`, `what_leaves`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `learner_title`, `module`; statically calls `latest_add_batch`, `latest_build_batch`, `latest_planner`, `learner_title`, `pending_adds`, `source_kind_noun`, `source_status_line`, `text_recognition_available`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `keep_ahead_for_reader`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `learner_title`; statically calls `learner_title`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`, `gate_model_requests`; calls `content_key`, `gate_model_requests`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `offer_profile`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `is_plan_profile`, `ready_client_for_task`; calls `is_plan_profile`, `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `MeteredRequestGate`, `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`, `is_subscription_transport`; calls `MeteredRequestGate`, `SpendBudget`, `SpendCaps`, `SpendEstimate`, `is_subscription_transport`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `FrozenClock`, `SystemClock`, `utc_now_iso`; calls `FrozenClock`, `SystemClock`, `utc_now_iso`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `CODEX_PROVIDER_NAMES`
- [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] — imports `load_config`; calls `load_config`
- [[Reference/Modules/learnloop/content/pipeline/build_plan|learnloop.content.pipeline.build_plan]] — imports `build_build_plan`; calls `build_build_plan`
- [[Reference/Modules/learnloop/content/pipeline/exam_marking|learnloop.content.pipeline.exam_marking]] — imports `module`; calls `held_back_details`, `held_back_reading`
- [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]] — imports `_default_brief`, `_resolve_extraction`; calls `_default_brief`, `_resolve_extraction`
- [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]] — imports `cost_phrase`, `module`, `unread_current_revision`; calls `carry_owed`, `cost_phrase`, `unread_current_revision`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `IngestRunnerError`, `JobCancelled`, `JobSpec`, `WaitingForInput`; calls `IngestRunnerError`, `JobCancelled`, `JobSpec`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `refuse_while_an_apply_is_outstanding`; calls `refuse_while_an_apply_is_outstanding`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `reject_items`; calls `reject_items`
- [[Reference/Modules/learnloop/content/sources/front_matter|learnloop.content.sources.front_matter]] — imports `FRONT_MATTER`
- [[Reference/Modules/learnloop/content/sources/source_library|learnloop.content.sources.source_library]] — imports `register_source_revision`; calls `register_source_revision`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `build_source_outline`, `title_from_file_name`, `title_from_local_uri`; calls `build_source_outline`, `title_from_file_name`, `title_from_local_uri`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `APPEND_INPUT_OVER_CEILING`
- [[Reference/Modules/learnloop/db/scopes|learnloop.db.scopes]] — imports `JobOwnershipLost`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `extraction_units`; calls `extraction_units`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `kebab_case`; calls `kebab_case`
- [[Reference/Modules/learnloop/ingest/extractors/__init__|learnloop.ingest.extractors]] — imports `datalab_api_key`, `marker_available`; calls `datalab_api_key`, `marker_available`
- [[Reference/Modules/learnloop/ingest/extractors/glm_ocr|learnloop.ingest.extractors.glm_ocr]] — imports `selected_backend`; calls `selected_backend`
- [[Reference/Modules/learnloop/ingest/models|learnloop.ingest.models]] — imports `UnsupportedSourceError`
- [[Reference/Modules/learnloop/ingest/resolution|learnloop.ingest.resolution]] — imports `resolve_source`; calls `resolve_source`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `source_exam_exclusions`; calls `source_exam_exclusions`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `add_subject`, `load_vault`; calls `add_subject`, `load_vault`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `upsert_source_set`; calls `upsert_source_set`
- [[Reference/Modules/learnloop/vault_lock|learnloop.vault_lock]] — imports `vault_mutation_lock`; calls `vault_mutation_lock`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `dataclasses`, `datetime`, `io`, `json`, `logging`, `os`, `pathlib`, `re`, `sqlite3`, `types`, `typing`, `urllib`, `uuid`
- Third party: `pypdf`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/ingest_batches|learnloop.cli.ingest_batches]], [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]], [[Reference/Modules/learnloop/content/pipeline/acquisition_preview|learnloop.content.pipeline.acquisition_preview]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]] and 10 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/reading_request_sweep_helpers.py](../../../../../../../tests/reading_request_sweep_helpers.py) — direct import
- [tests/reread_safety_helpers.py](../../../../../../../tests/reread_safety_helpers.py) — direct import
- [tests/test_auto_build_spend_report.py](../../../../../../../tests/test_auto_build_spend_report.py) — direct import
  - `test_a_build_still_running_is_held_back_by_the_guard`
  - `test_the_report_shows_automatic_builds_daily_spend_under_their_guard`
- [tests/test_decider_landing.py](../../../../../../../tests/test_decider_landing.py) — direct import
  - `test_inside_an_automatic_builds_request_gate_the_span_check_is_admitted_and_settled`
- [tests/test_exam_protection_landing.py](../../../../../../../tests/test_exam_protection_landing.py) — direct import
  - `test_a_book_picked_as_an_exam_in_its_outline_builds_nothing`
  - `test_the_automatic_build_scope_is_the_one_predicate`
- [tests/test_followups_batch7_note_titles.py](../../../../../../../tests/test_followups_batch7_note_titles.py) — direct import
  - `test_the_library_card_names_a_percent_encoded_file_the_same_way`
- [tests/test_glm_ocr.py](../../../../../../../tests/test_glm_ocr.py) — direct import
  - `test_a_book_carrying_the_retired_keep_local_choice_is_read_like_any_other`
  - `test_an_add_asks_once_naming_z_ai_then_reads_and_records_the_spend`
  - `test_every_glm_ocr_reading_queues_the_source_block_backfill`
  - `test_r2_f2_an_import_without_the_ok_reads_locally_and_offers_text_recognition`
  - `test_r2_f3_an_earlier_whole_file_ok_never_covers_z_ai`
  - `test_r2_f3_the_z_ai_ok_names_only_z_ai`
  - `test_r2_f5_paid_windows_are_kept_so_trying_again_pays_only_for_the_rest`
  - `test_r2_f7_a_stand_in_reading_is_stored_with_its_own_model_versions`
  - `test_r2_f9_a_scan_offers_text_recognition_or_where_to_set_it_up`
  - `test_r3_f10_a_local_repair_never_leaves_this_computer`
  - `test_r3_f10_a_local_repair_of_an_image_sends_nothing_and_says_why`
  - `test_r3_f14_the_cards_details_are_plain_words`
  - `test_r3_f7_a_double_fallback_stores_the_versions_of_what_read_it`
  - `test_read_again_with_text_recognition_uses_glm_when_it_can`
  - `test_the_daily_gate_prices_glm_receipts_and_local_runs_cost_nothing`
- [tests/test_keep_ahead_append_units.py](../../../../../../../tests/test_keep_ahead_append_units.py) — direct import
  - `test_an_append_over_its_input_ceiling_fails_once_and_the_card_says_so`
  - `test_the_second_build_appends_only_its_own_chapter`
- [tests/test_keep_local_retired.py](../../../../../../../tests/test_keep_local_retired.py) — direct import
  - `test_a_book_carrying_the_retired_choice_gets_its_questions_built`
  - `test_a_plan_that_waited_on_the_retired_choice_offers_build_them`
  - `test_add_no_longer_takes_a_keep_local_option`
  - `test_book_details_no_longer_offer_keeping_a_book_off_the_ai`
- [tests/test_plan_first_transport.py](../../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_f1_a_configured_metered_fallback_provider_is_never_used_silently_for_a_plan_route`
  - `test_f3_the_question_build_asks_and_a_grant_serves_it_priced_as_metered`
  - `test_f6_codex_is_never_a_fallback_through_the_direct_readers`
  - `test_rr_f1_the_connection_status_never_offers_and_shows_a_granted_build`
- [tests/test_plan_first_transport_offer_grants_r5.py](../../../../../../../tests/test_plan_first_transport_offer_grants_r5.py) — direct import
- [tests/test_reading_hardening_2_fixes.py](../../../../../../../tests/test_reading_hardening_2_fixes.py) — direct import
  - `test_f1_a_foreground_host_starts_no_worker_of_its_own`
  - `test_f1_the_start_and_the_sweep_leave_work_that_cannot_run_alone`
- [tests/test_reading_hardening_review_fixes.py](../../../../../../../tests/test_reading_hardening_review_fixes.py) — direct import
  - `test_f1_a_crash_between_the_cancel_and_its_settle_leaves_neither_after_a_restart`
- [tests/test_reading_hardening_verify_fixes.py](../../../../../../../tests/test_reading_hardening_verify_fixes.py) — direct import
  - `test_f1_a_cancel_committing_while_a_finished_build_plans_its_follow_on_leaves_nothing_queued`
  - `test_f1_a_planner_cancelled_while_it_plans_queues_no_build`
  - `test_f1_a_request_newer_than_the_one_acted_on_is_left_for_its_own_act`
  - `test_n2_a_retry_time_that_overflows_blocks_no_other_book`
- [tests/test_reading_request_sweep.py](../../../../../../../tests/test_reading_request_sweep.py) — direct import
  - `test_a_request_waiting_on_the_books_work_is_not_replanned_by_the_sweep`
  - `test_d_work_the_cli_finishes_leaves_the_request_due_for_the_sweep`
- [tests/test_reread_safety.py](../../../../../../../tests/test_reread_safety.py) — direct import
  - `test_e1_a_failed_import_of_new_bytes_leaves_the_previous_revision_current`
  - `test_e1_bytes_that_match_nowhere_refuse_plainly_and_register_nothing`
  - `test_e1_one_tap_repair_for_a_library_already_in_that_state`
  - `test_f7_a_carry_over_that_fails_is_finished_later_never_lost`
  - `test_redesign_marking_the_new_reading_makes_it_usable`
  - `test_the_reread_keeps_the_page_scope_and_carries_the_selection`
  - `test_the_z_ai_ok_line_names_pages_and_cost_for_a_404_page_book`
- [tests/test_ux_phase1_add_source.py](../../../../../../../tests/test_ux_phase1_add_source.py) — direct import
  - `test_add_source_opens_a_pdf_at_once_with_its_original`
  - `test_add_source_with_more_options`
  - `test_reading_progress_reaches_the_reading_order_build`
- [tests/test_ux_phase1_auto_build.py](../../../../../../../tests/test_ux_phase1_auto_build.py) — direct import
  - `test_a_cheap_metered_build_runs_silently`
  - `test_a_failed_fetch_says_so_in_one_line`
  - `test_a_past_exam_builds_nothing`
  - `test_a_quarter_of_the_daily_cap_also_pauses`
  - `test_adding_a_book_builds_questions_for_the_first_chapter_and_the_next`
  - `test_an_existing_subject_with_the_books_name_is_reused`
  - `test_an_expensive_build_pauses_once_with_one_line`
  - `test_auto_apply_off_leaves_the_build_waiting_for_a_look`
  - `test_auto_build_off_leaves_the_book_readable_only`
  - `test_jumping_ahead_builds_the_chapter_jumped_to`
  - `test_missing_consent_waits_for_one_ok`
  - `test_no_ai_waits_with_a_connect_line`
  - `test_reading_does_nothing_while_auto_build_is_off`
  - `test_reading_into_the_next_chapter_builds_one_chapter_ahead`
  - `test_reading_order_scope`
  - `test_the_subscription_never_pauses_for_cost`
  - `test_undo_takes_the_books_questions_back_out`
  - `test_while_the_next_build_is_planned_the_card_says_chapters_found`
- [tests/test_ux_phase1_connect_ai.py](../../../../../../../tests/test_ux_phase1_connect_ai.py) — direct import
  - `test_connecting_releases_books_that_were_waiting`
  - `test_quick_add_reads_the_recorded_ok_instead_of_asking_per_build`
- [tests/test_ux_phase1_finish.py](../../../../../../../tests/test_ux_phase1_finish.py) — direct import
  - `test_6_a_pdf_is_a_pdf_until_its_text_says_book_or_paper`
  - `test_f8_a_saved_report_keeps_its_ask_even_when_acting_cannot_start`
  - `test_f9_undo_invalidates_a_request_being_acted_on`
- [tests/test_ux_phase1_landing.py](../../../../../../../tests/test_ux_phase1_landing.py) — direct import
  - `test_a_book_that_is_exam_material_builds_nothing`
  - `test_an_automatic_build_never_takes_a_held_out_unit_as_teaching`
- [tests/test_ux_phase1_review_fixes.py](../../../../../../../tests/test_ux_phase1_review_fixes.py) — direct import
  - `test_f10_a_books_history_survives_lots_of_other_work`
  - `test_f10_connecting_releases_a_book_however_old_its_wait`
  - `test_f11_retry_tries_the_zero_model_repair_first_then_a_fresh_run`
  - `test_f12_undo_records_the_owners_verdict_once`
  - `test_f2_a_retry_is_admitted_against_what_the_build_already_spent`
  - `test_f2_build_them_never_passes_the_daily_cap`
  - `test_f2_each_paid_job_is_admitted_at_the_route_it_really_uses`
  - `test_f2_no_per_build_cap_by_default`
  - `test_f2_rereview_a_json_repair_is_admitted_like_any_paid_request`
  - `test_f2_rereview_append_reconciliation_calls_are_admitted_one_by_one`
  - `test_f2_the_dry_run_command`
  - `test_f2_the_dry_run_makes_no_call_and_writes_nothing`
  - `test_f2_todays_spending_is_what_model_calls_cost_not_planner_estimates`
  - `test_f3_a_planner_that_dies_after_queuing_its_build_is_never_orphaned`
  - `test_f3_rereview_a_link_planner_that_dies_after_queuing_its_build_is_found`
  - `test_f4_turning_auto_apply_off_after_planning_keeps_the_build_unapplied`
  - `test_f4_turning_auto_build_off_stops_queued_automatic_work`
  - `test_f5_undo_cancels_a_build_still_waiting_to_run`
  - `test_f5_undo_while_a_chapter_builds_keeps_it_from_putting_content_back`
  - `test_f6_failed_chapters_are_built_again_by_build_the_whole_book`
  - `test_f7_a_position_that_waited_across_a_restart_is_acted_on_when_the_library_opens`
  - `test_f7_reading_ahead_while_a_build_runs_is_built_when_it_finishes`
  - `test_f9_text_recognition_names_an_extractor_that_recognises_text`
  - `test_f9_text_recognition_without_an_extractor_that_can_do_it_says_so`
- [tests/test_ux_phase1_round2_rereview.py](../../../../../../../tests/test_ux_phase1_round2_rereview.py) — direct import
  - `test_f8_a_keep_ahead_that_failed_is_kept_for_the_next_start`
- [tests/test_ux_phase1_round2_review.py](../../../../../../../tests/test_ux_phase1_round2_review.py) — direct import
  - `test_f1_keeping_a_chapter_ahead_never_loads_the_books_text`
  - `test_f1_keeping_a_chapter_ahead_reads_the_config_not_the_whole_vault`
  - `test_f1_keeping_a_chapter_ahead_still_honours_the_switch_in_the_config`
  - `test_f1_progress_within_a_section_already_reached_plans_nothing_again`
- [tests/test_ux_phase1_usability_round1.py](../../../../../../../tests/test_ux_phase1_usability_round1.py) — direct import
  - `test_a_link_being_fetched_has_a_readable_name`
  - `test_u4_reaching_a_section_keeps_the_questions_a_chapter_ahead`
  - `test_u7_a_scan_offers_text_recognition_when_it_is_installed`
  - `test_u7_a_scan_says_plainly_when_text_recognition_is_not_installed`
  - `test_u7_reading_a_scan_with_text_recognition_also_builds_its_questions`
  - `test_u8_a_built_book_says_its_questions_come_as_you_read`
- [tests/test_ux_phase1_usability_round2.py](../../../../../../../tests/test_ux_phase1_usability_round2.py) — direct import
  - `test_a_built_books_line_reads_its_text_at_most_once`
  - `test_a_first_build_promises_no_minutes_it_cannot_know`
  - `test_a_later_build_is_estimated_from_this_librarys_own_builds`
  - `test_a_pdf_with_an_abstract_is_a_paper`
  - `test_adding_with_text_recognition_that_is_not_installed_says_how_to_get_it`
  - `test_no_finished_build_means_no_estimate`
  - `test_r4_a_card_says_whether_text_recognition_can_run_for_it`
  - `test_r4_asking_for_text_recognition_that_is_not_installed_says_how_to_get_it`
  - `test_scan_details_say_how_to_get_text_recognition_plainly`
  - `test_the_estimate_scales_with_the_sections_a_build_covers`
  - `test_the_one_time_ok_names_codex_for_a_library_set_up_with_codex`
- [tests/ux_phase1_landing_helpers.py](../../../../../../../tests/ux_phase1_landing_helpers.py) — direct import
- [tests/ux_phase1_review_fixes_helpers.py](../../../../../../../tests/ux_phase1_review_fixes_helpers.py) — direct import
- [tests/ux_phase1_support.py](../../../../../../../tests/ux_phase1_support.py) — direct import

## Modification guidance

- Change add source policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/pipeline/add_source.py](../../../../../../../src/learnloop/content/pipeline/add_source.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
