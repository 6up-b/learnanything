---
title: "learnloop.content.pipeline.wait_detail"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/pipeline/wait_detail.py"
source_paths:
  - "src/learnloop/content/pipeline/wait_detail.py"
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
  - "learnloop.content.pipeline.wait_detail module"
  - "src/learnloop/content/pipeline/wait_detail.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-pipeline"
---

# `learnloop.content.pipeline.wait_detail`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.pipeline.wait_detail` exists within [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] to own the behavior summarized by its module contract: What a learner waiting on a book can be told, in facts the code recorded when they happened.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/pipeline/wait_detail.py](../../../../../../../src/learnloop/content/pipeline/wait_detail.py) |
| Source lines | 218 |
| Owning package | [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `delivery(repo, job: Mapping[str, Any], progress: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/wait_detail.py), line 89) — What the job's model requests have done, this try: when the newest request still in flight was sent, when the newest reply was received, and the in-flight request's streamed output so far (its count of pieces and when the last arrived; 0 and None with none, or on a transport tha…
- `build_detail(repo, batch: Mapping[str, Any], *, measured: tuple[float, int] | None, now: datetime) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/wait_detail.py), line 124) — A build under way, in facts.
- `topic_minutes(repo, *, sample: int=5) -> tuple[float, int] | None` ([source](../../../../../../../src/learnloop/content/pipeline/wait_detail.py), line 162) — How long one topic's questions take to write in this library: the middle of the newest ``sample`` topics written (from the request for them to their questions applied), with how many it rests on; None before any topic was timed.
- `writing_detail(repo, vault, job: Mapping[str, Any], *, measured: tuple[float, int] | None, now: datetime) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/pipeline/wait_detail.py), line 184) — A section's questions being written, in facts: ``queued`` while its job waits its turn; the topic being written now (``topic``: its title, which of the job's topics and of how many; ``reading_questions`` drops the place where other jobs write too) and when its writing was asked…

### Module constants

- `BUILD_STEP_JOBS` ([src/learnloop/content/pipeline/wait_detail.py](../../../../../../../src/learnloop/content/pipeline/wait_detail.py), line 34)
- `_SYNTHESIS_STAGE` ([src/learnloop/content/pipeline/wait_detail.py](../../../../../../../src/learnloop/content/pipeline/wait_detail.py), line 37)

### Explicit exports

`__all__` declares:

- `BUILD_STEP_JOBS`
- `build_detail`
- `delivery`
- `topic_minutes`
- `writing_detail`

## Internal implementation anchors

- `_iso(value: Any) -> str | None` ([source](../../../../../../../src/learnloop/content/pipeline/wait_detail.py), line 50) — One time format for the screens ("…Z", whole seconds), whatever wrote it.
- `_when(value: Any) -> datetime | None` ([source](../../../../../../../src/learnloop/content/pipeline/wait_detail.py), line 62)
- `_int(value: Any) -> int | None` ([source](../../../../../../../src/learnloop/content/pipeline/wait_detail.py), line 69)
- `_progress(repo, job: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/pipeline/wait_detail.py), line 73) — The job's progress row, only when it is this attempt's.
- `_retry(job: Mapping[str, Any], progress: Mapping[str, Any] | None) -> bool` ([source](../../../../../../../src/learnloop/content/pipeline/wait_detail.py), line 82) — Whether this is a try after an earlier one stopped: the runner's own second try, or a later attempt (Try again, or work taken over after its worker stopped).
- `_measured(measured: tuple[float, int] | None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/content/pipeline/wait_detail.py), line 117)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `build_detail`, `module`; statically calls `build_detail`, `topic_minutes`, `writing_detail`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_build_wait_detail.py](../../../../../../../tests/test_build_wait_detail.py) — direct import
  - `test_a_queued_section_job_says_it_waits_and_nothing_else`
  - `test_a_section_being_written_names_its_topic_and_this_librarys_time_per_topic`
  - `test_a_transport_that_does_not_stream_reports_no_output`
  - `test_before_any_topic_is_timed_nothing_is_measured`
  - `test_the_reply_is_named_once_received_and_no_output_is_then_in_flight`

## Modification guidance

- Change wait detail policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/pipeline/wait_detail.py](../../../../../../../src/learnloop/content/pipeline/wait_detail.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
