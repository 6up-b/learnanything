---
title: "learnloop.source_retrieval.video_chapters"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/video_chapters.py"
source_paths:
  - "src/learnloop/source_retrieval/video_chapters.py"
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
  - "learnloop.source_retrieval.video_chapters module"
  - "src/learnloop/source_retrieval/video_chapters.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.video_chapters`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.video_chapters` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Reader workbench v2 RD10 (spec §7.9): a video's suggested chapters, judged against the vault's LOs over its transcript sections, and the learner's decision on each (``video_chapters``, migration 268).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/video_chapters.py](../../../../../../src/learnloop/source_retrieval/video_chapters.py) |
| Source lines | 400 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ChaptersError(Exception)` ([source](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 49)
  - `__init__(self, code: str, message: str) -> None` (line 50; internal)
- `class ChapterJudgment(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 56)
  - `_tolerate(cls, data: Any) -> Any` (line 69; internal)
- `class VideoChaptersOutputV1(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 80)
- `class TranscriptSection` ([source](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 109)
- `class Prompt` ([source](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 118)
- `class SuggestResult` ([source](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 127)
- `transcript_sections(repository: Repository, extraction_id: str) -> list[TranscriptSection]` ([source](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 139) — A video reading's sections with their cue times, in order (a section with no timed cue is left out).
- `section_at(sections: Sequence[TranscriptSection], t: float) -> TranscriptSection | None` ([source](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 158) — The section a time falls in (between two sections: the one before it; before the first: the first).
- `build_prompt(vault: Any, library: SC.Library, extraction_id: str, sections: Sequence[TranscriptSection], learning_object_ids: Sequence[str]) -> Prompt` ([source](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 168) — The video's sections (time range and words, each held to an equal share of ``curriculum.max_prompt_tokens``, as the coverage judge's candidates are) and the LOs it may be judged against, by title.
- `chapter_id(extraction_id: str, t0: float, t1: float, title: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 194)
- `assemble(extraction_id: str, sections: Sequence[TranscriptSection], prompt: Prompt, rows: dict[str, dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 198) — The chapters the judged sections describe: each run from a start to the next start (the first section always starts one), its sections' times, the start's title and its LO tags (listed refs only).
- `list_chapters(vault: Any, repository: Repository, extraction_id: str, *, states: Sequence[str]=('suggested', 'accepted')) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 235) — A reading's chapters in the given states, by time; each with its LOs' titles (an LO gone from the vault is left out of its tags).
- `accepted_at(repository: Repository, extraction_id: str, t: float) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 253) — The accepted chapter a time falls in, if any.
- `class NotWanted(Exception)` ([source](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 262) — The judgment's job was cancelled, or its context closed or switched vaults, before its chapters were stored.
- `store_suggestions(repository: Repository, extraction_id: str, source_id: str | None, chapters: Sequence[dict[str, Any]], *, clock: Clock | None=None, guard: SC.CoverageGuard | None=None, wanted: Callable[[], bool] | None=None) -> None` ([source](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 266) — Replace the reading's chapters still suggested by these; a decided chapter (and the same chapter suggested again) keeps its row.
- `decide(vault: Any, repository: Repository, chapter_id_: str, decision: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 289) — Accept a suggested chapter or dismiss it ("not this"), once.
- `suggest(vault: Any, repository: Repository, extraction_id: str, *, client: Any | None=None, clock: Clock | None=None, budget: SpendBudget | None=None, live_vault: Any | None=None, wanted: Callable[[], bool] | None=None) -> SuggestResult` ([source](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 312) — Judge a video's chapters and store them suggested (no call when the same request is in the ledger).

### Module constants

- `LEDGER_TASK` ([src/learnloop/source_retrieval/video_chapters.py](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 40)
- `LEDGER_LEFT` ([src/learnloop/source_retrieval/video_chapters.py](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 41)
- `LEDGER_RIGHT` ([src/learnloop/source_retrieval/video_chapters.py](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 42)
- `PROMPT_VERSION` ([src/learnloop/source_retrieval/video_chapters.py](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 43)
- `STATES` ([src/learnloop/source_retrieval/video_chapters.py](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 44)
- `DECISIONS` ([src/learnloop/source_retrieval/video_chapters.py](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 45)
- `_CUE_TIME_RE` ([src/learnloop/source_retrieval/video_chapters.py](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 46)
- `CHAPTERS_TASK` ([src/learnloop/source_retrieval/video_chapters.py](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 86)
- `_INSTRUCTIONS` ([src/learnloop/source_retrieval/video_chapters.py](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 96)

### Explicit exports

`__all__` declares:

- `CHAPTERS_TASK`
- `ChaptersError`
- `NotWanted`
- `SuggestResult`
- `TranscriptSection`
- `VideoChaptersOutputV1`
- `accepted_at`
- `assemble`
- `build_prompt`
- `decide`
- `list_chapters`
- `section_at`
- `store_suggestions`
- `suggest`
- `transcript_sections`

## Internal implementation anchors

- `_cue_times(block: Any) -> tuple[float, float] | None` ([source](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 134)
- `_view(row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 223)
- `_rows(connection: Any, sql: str, params: Sequence[Any]=()) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/video_chapters.py), line 229)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/follow_along|learnloop.source_retrieval.follow_along]] — imports `module`; statically calls `accepted_at`, `section_at`, `transcript_sections`
- [[Reference/Modules/learnloop_sidecar/handlers/video|learnloop_sidecar.handlers.video]] — imports `module`; statically calls `decide`, `list_chapters`, `suggest`, `transcript_sections`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`; calls `AIInterrupted`, `AIInvalidOutput`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `call_labels`, `content_key`, `gate_model_requests`; calls `call_labels`, `content_key`, `gate_model_requests`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `spend_envelopes`; calls `spend_envelopes`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/practice_index/listwise|learnloop.practice_index.listwise]] — imports `ListwiseTask`, `judge_listwise`, `listwise_caps`; calls `ListwiseTask`, `judge_listwise`, `listwise_caps`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `plan_route`; calls `plan_route`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `extraction_sections`; calls `extraction_sections`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `module`; calls `CoverageGuard`, `Library`, `_daily_if_inactive`, `admission_problem`, `enabled`, `source_learning_objects`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `re`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/follow_along|learnloop.source_retrieval.follow_along]], [[Reference/Modules/learnloop_sidecar/handlers/video|learnloop_sidecar.handlers.video]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/test_reader_rd10_fix_protection.py](../../../../../../tests/test_reader_rd10_fix_protection.py) — direct import
  - `test_a_judged_video_replays_from_the_ledger_with_the_budget_spent_and_an_unjudged_one_is_capped`
  - `test_the_curriculum_switched_off_while_a_suggestion_runs_stores_nothing`
- [tests/test_reader_rd10_video.py](../../../../../../tests/test_reader_rd10_video.py) — direct import
  - `test_chapters_are_judged_once_stored_suggested_and_accepting_stores`
  - `test_chapters_are_off_with_the_curriculum`
  - `test_the_chapters_are_assembled_from_the_judged_boundaries`

## Modification guidance

- Make changes here when the responsibility remains video chapters within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/video_chapters.py](../../../../../../src/learnloop/source_retrieval/video_chapters.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
