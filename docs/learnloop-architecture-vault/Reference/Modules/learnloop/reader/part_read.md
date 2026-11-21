---
title: "learnloop.reader.part_read"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/part_read.py"
source_paths:
  - "src/learnloop/reader/part_read.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.part_read module"
  - "src/learnloop/reader/part_read.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.part_read`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.part_read` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: A first set of questions from the part of a section the learner has read.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/part_read.py](../../../../../../src/learnloop/reader/part_read.py) |
| Source lines | 459 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class TopicCoverage` ([source](../../../../../../src/learnloop/reader/part_read.py), line 80) — What one topic's grounding cites and how much of it the learner's reading has seen.
  - `qualifies(self) -> bool` (line 96; public)
  - `reason(self) -> str` (line 100; public) — Why it qualifies or not, the first exclusion that applies: ``unresolved``, ``no_citation``, ``held_out``, ``unseen`` or ``seen``.
- `topic_coverage(vault: LoadedVault, repository: Any, extraction_id: str, lo_ids: list[str]) -> dict[str, TopicCoverage]` ([source](../../../../../../src/learnloop/reader/part_read.py), line 262) — Each active topic of ``lo_ids``'s coverage, read against ``extraction_id`` (the reading being read).
- `seen_grounding(vault: LoadedVault, repository: Any, extraction_id: str, coverage: TopicCoverage, library: _Library | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/part_read.py), line 275) — A qualifying topic's citation bundles: its cited passages (at most four, its own references' first, as the finished section's bundles choose them), each widened by up to five neighbours on either side inside its section, only while they are seen.
- `class SectionPartRead` ([source](../../../../../../src/learnloop/reader/part_read.py), line 326) — One unfinished section with seen passages: whether its chapter's topics are in, the topics citing it that need questions and nobody owns (``candidates``), those of them that qualify, with their grounding.
  - `qualifying(self) -> tuple[str, ...]` (line 337; public)
  - `state(self) -> str` (line 341; public)
- `assess(vault: LoadedVault, repository: Any, extraction_id: str, *, topics_settled: Callable[[str], tuple[bool, str | None]], remember: bool=True) -> dict[str, SectionPartRead]` ([source](../../../../../../src/learnloop/reader/part_read.py), line 363) — Every unfinished section of ``extraction_id`` the learner has seen passages of, by section id.
- `read_readings(repository: Any) -> list[str]` ([source](../../../../../../src/learnloop/reader/part_read.py), line 406) — The current reading of every book the learner has seen passages of (on it, or on an earlier reading whose passages carry over by exact alias).
- `reconcile_part_read(vault: LoadedVault, repository: Any, *, extraction_id: str, enqueue: TopicEnqueue, topics_settled: Callable[[str], tuple[bool, str | None]], claim_repository: Any=None, remember: bool=True) -> list[str]` ([source](../../../../../../src/learnloop/reader/part_read.py), line 419) — Claim the topics of ``extraction_id``'s unfinished sections that newly qualify, and queue their first sets.

### Module constants

- `PART_READ` ([src/learnloop/reader/part_read.py](../../../../../../src/learnloop/reader/part_read.py), line 64)
- `BEFORE_BUILD` ([src/learnloop/reader/part_read.py](../../../../../../src/learnloop/reader/part_read.py), line 67)
- `OWED` ([src/learnloop/reader/part_read.py](../../../../../../src/learnloop/reader/part_read.py), line 68)
- `READ_FURTHER` ([src/learnloop/reader/part_read.py](../../../../../../src/learnloop/reader/part_read.py), line 69)
- `NOTHING` ([src/learnloop/reader/part_read.py](../../../../../../src/learnloop/reader/part_read.py), line 70)
- `_PASSAGE_REFS` ([src/learnloop/reader/part_read.py](../../../../../../src/learnloop/reader/part_read.py), line 75)
- `_TIME_LOCATOR_RE` ([src/learnloop/reader/part_read.py](../../../../../../src/learnloop/reader/part_read.py), line 76)
- `_MEMO` ([src/learnloop/reader/part_read.py](../../../../../../src/learnloop/reader/part_read.py), line 349)
- `_MEMO_LOCK` ([src/learnloop/reader/part_read.py](../../../../../../src/learnloop/reader/part_read.py), line 350)

### Explicit exports

`__all__` declares:

- `BEFORE_BUILD`
- `NOTHING`
- `OWED`
- `READ_FURTHER`
- `PART_READ`
- `SectionPartRead`
- `TopicCoverage`
- `assess`
- `read_readings`
- `reconcile_part_read`
- `seen_grounding`
- `topic_coverage`

## Internal implementation anchors

- `class _Reading` ([source](../../../../../../src/learnloop/reader/part_read.py), line 113) — One reading's readable passages, in order, with their sections and blocks, its book, and what of it was seen.
- `_raw_path(vault: LoadedVault, revision: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/reader/part_read.py), line 136)
- `class _Library` ([source](../../../../../../src/learnloop/reader/part_read.py), line 141) — The readings a set of topics cites, loaded once each: the reading being read, and any other book's current one.
- `_timed(ref: SourceRef, reading: _Reading) -> list[str] | None` ([source](../../../../../../src/learnloop/reader/part_read.py), line 176) — Every transcript cue a timed reference's range overlaps, or None when the reference is not timed.
- `_resolve(ref: SourceRef, reading: _Reading) -> list[str] | None` ([source](../../../../../../src/learnloop/reader/part_read.py), line 196) — The readable passages of ``reading`` a reference cites, each exactly; None when any of it cannot be resolved exactly (an explicit span that is not the same text here, or a locator or quote that names no passage, or only a moved one).
- `_coverage(library: _Library, learning_object: Any) -> TopicCoverage` ([source](../../../../../../src/learnloop/reader/part_read.py), line 226)
- `_fingerprint(vault: LoadedVault, repository: Any, progress: list[dict[str, Any]]) -> tuple[Any, ...]` ([source](../../../../../../src/learnloop/reader/part_read.py), line 353)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `module`; statically calls `assess`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `module`; statically calls `read_readings`, `reconcile_part_read`
- [[Reference/Modules/learnloop_sidecar/handlers/proposals|learnloop_sidecar.handlers.proposals]] — imports `read_readings`; statically calls `read_readings`
- [[Reference/Modules/learnloop_sidecar/section_questions|learnloop_sidecar.section_questions]] — imports `read_readings`, `reconcile_part_read`; statically calls `read_readings`, `reconcile_part_read`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `surface_material`; calls `surface_material`
- [[Reference/Modules/learnloop/content/sources/span_aliases|learnloop.content.sources.span_aliases]] — imports `SpanTranslator`, `current_reading`, `reading_source`; calls `SpanTranslator`, `current_reading`, `reading_source`
- [[Reference/Modules/learnloop/db/stores/reader|learnloop.db.stores.reader]] — imports `READER_FIRST_SET`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `_MAX_SOURCE_BUNDLES_PER_LO`, `_SOURCE_BUNDLE_RADIUS`, `citation_bundle`; calls `citation_bundle`
- [[Reference/Modules/learnloop/reader/section_generation|learnloop.reader.section_generation]] — imports `TOPIC_MANAGED`, `TopicEnqueue`, `claim_section_topics`, `section_generation_candidates`, `section_topic_requests`; calls `claim_section_topics`, `section_generation_candidates`, `section_topic_requests`
- [[Reference/Modules/learnloop/reader/seen_passages|learnloop.reader.seen_passages]] — imports `seen_marker`, `seen_on`, `seen_readings`; calls `seen_marker`, `seen_on`, `seen_readings`
- [[Reference/Modules/learnloop/section_map|learnloop.section_map]] — imports `ANCHOR_CURRENT`, `anchor_for_ref`, `canonical_note_ids`, `extraction_sections`; calls `anchor_for_ref`, `canonical_note_ids`, `extraction_sections`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `SourceRef`, `learning_object_facet_union`; calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `re`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop_sidecar/handlers/proposals|learnloop_sidecar.handlers.proposals]], [[Reference/Modules/learnloop_sidecar/section_questions|learnloop_sidecar.section_questions]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_first_questions_today.py](../../../../../../tests/test_first_questions_today.py) — direct import
  - `test_a_section_read_in_part_says_what_its_reading_can_give`
- [tests/test_part_read_first_set.py](../../../../../../tests/test_part_read_first_set.py) — direct import
  - `test_a_topic_with_no_citation_never_qualifies`

## Modification guidance

- Change part read policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/part_read.py](../../../../../../src/learnloop/reader/part_read.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
