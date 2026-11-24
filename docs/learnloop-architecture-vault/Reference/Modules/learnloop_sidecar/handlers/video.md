---
title: "learnloop_sidecar.handlers.video"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/video.py"
source_paths:
  - "src/learnloop_sidecar/handlers/video.py"
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
  - "learnloop_sidecar.handlers.video module"
  - "src/learnloop_sidecar/handlers/video.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.video`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.video` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Reader workbench v2 RD10 RPCs: follow-along and suggested video chapters (spec §7.5, §7.9).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/video.py](../../../../../../src/learnloop_sidecar/handlers/video.py) |
| Source lines | 239 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class FollowAlongInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/video.py), line 46)
- `class ChaptersInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/video.py), line 54)
- `class ChaptersJobInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/video.py), line 58)
- `class ChaptersDecideInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/video.py), line 62)
- `reader_follow_along(ctx: SidecarContext, params: FollowAlongInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/video.py), line 111) — What the book follows at the video's time (no model call, no write).
- `chapters_list(ctx: SidecarContext, params: ChaptersInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/video.py), line 125) — A video reading's chapters, suggested and accepted, by time.
- `chapters_suggest(ctx: SidecarContext, params: ChaptersInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/video.py), line 165) — Judge the video's chapters: ``{job_id, status, done, result, error}`` at once.
- `chapters_job(ctx: SidecarContext, params: ChaptersJobInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/video.py), line 213) — The suggestion's state, at once (never a wait on the request path).
- `chapters_cancel(ctx: SidecarContext, params: ChaptersJobInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/video.py), line 220) — Cancel the suggestion: its next model request is refused; a finished one keeps its outcome.
- `chapters_decide(ctx: SidecarContext, params: ChaptersDecideInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/video.py), line 227) — Accept a suggested chapter or dismiss it ("not this"), once; the chapter as it now stands.

### Module constants

- `VIDEO_RPCS` ([src/learnloop_sidecar/handlers/video.py](../../../../../../src/learnloop_sidecar/handlers/video.py), line 38)
- `KIND` ([src/learnloop_sidecar/handlers/video.py](../../../../../../src/learnloop_sidecar/handlers/video.py), line 40)
- `NOT_FOUND_MESSAGE` ([src/learnloop_sidecar/handlers/video.py](../../../../../../src/learnloop_sidecar/handlers/video.py), line 41)
- `_REGISTRY` ([src/learnloop_sidecar/handlers/video.py](../../../../../../src/learnloop_sidecar/handlers/video.py), line 42)
- `_JOBS_LOCK` ([src/learnloop_sidecar/handlers/video.py](../../../../../../src/learnloop_sidecar/handlers/video.py), line 43)

### Explicit exports

`__all__` declares:

- `VIDEO_RPCS`

## Internal implementation anchors

- `_sections(repository: Any, extraction_id: str) -> list[tuple[str, float, float | None]]` ([source](../../../../../../src/learnloop_sidecar/handlers/video.py), line 67)
- `_protected_chapters(vault: Any, repository: Any, extraction_id: str, chapters: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str | None]` ([source](../../../../../../src/learnloop_sidecar/handlers/video.py), line 71) — Chapters as a reply may carry them while checks are due (masked at every read, a poll included, so a check falling due since the judgment still hides what it covers), and when the next check falls due.
- `_exam_masked(vault: Any, repository: Any, extraction_id: str, chapters: list[dict[str, Any]], sections: list[Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/video.py), line 82) — A chapter over exam or held-out material keeps its times and ids, its title and tags neutral.
- `_chapters_error(exc: VC.ChaptersError | SC.CoverageError) -> SidecarError` ([source](../../../../../../src/learnloop_sidecar/handlers/video.py), line 106)
- `_jobs(ctx: SidecarContext) -> PJ.PolledJobs` ([source](../../../../../../src/learnloop_sidecar/handlers/video.py), line 133)
- `_error(error: SidecarError | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/video.py), line 137)
- `_payload(job_id: str | None, status: str, *, finished: bool, result: dict[str, Any] | None, error: SidecarError | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/video.py), line 143)
- `_job_payload(ctx: SidecarContext, job: PJ.PolledJob) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/video.py), line 148)
- `_find(ctx: SidecarContext, job_id: str, *, cancel: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/video.py), line 198)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `relay_job_offer`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `exam_withheld`; calls `exam_withheld`
- [[Reference/Modules/learnloop/curriculum/goal_lens|learnloop.curriculum.goal_lens]] — imports `module`; calls `protect_chapters`, `protect_follow`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/source_retrieval/follow_along|learnloop.source_retrieval.follow_along]] — imports `module`; calls `follow`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `module`
- [[Reference/Modules/learnloop/source_retrieval/video_chapters|learnloop.source_retrieval.video_chapters]] — imports `module`; calls `decide`, `list_chapters`, `suggest`, `transcript_sections`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]] — imports `_library_cache`, `_require`; calls `_library_cache`, `_require`
- [[Reference/Modules/learnloop_sidecar/handlers/goal_lens|learnloop_sidecar.handlers.goal_lens]] — imports `protection_now`; calls `protection_now`
- [[Reference/Modules/learnloop_sidecar/polled_jobs|learnloop_sidecar.polled_jobs]] — imports `module`; calls `registry`, `vault_key`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `threading`, `typing`
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
  - `test_the_pinned_rd10_rpcs_are_all_of_them`
- [tests/test_reader_rd10_video.py](../../../../../../tests/test_reader_rd10_video.py) — direct import
  - `test_the_rpcs_are_registered_desktop_only_and_refuse_extra_fields`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/video.py](../../../../../../src/learnloop_sidecar/handlers/video.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
