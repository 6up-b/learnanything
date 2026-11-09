---
title: "learnloop.reader.source_roles"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/source_roles.py"
source_paths:
  - "src/learnloop/reader/source_roles.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.source_roles module"
  - "src/learnloop/reader/source_roles.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.source_roles`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.source_roles` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Instructional roles as source-object proposals (reader workbench RW4e; spec_reader_workbench_v1 §7.9).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/source_roles.py](../../../../../../src/learnloop/reader/source_roles.py) |
| Source lines | 515 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class RoleProposal(WireModel)` ([source](../../../../../../src/learnloop/reader/source_roles.py), line 105)
- `clean_roles(value: Any) -> list[dict[str, str]]` ([source](../../../../../../src/learnloop/reader/source_roles.py), line 114) — A judge's ``roles`` read tolerantly: each well-formed ``{role, confidence}`` from the vocabulary, once, in order; anything else (a missing field, a string, an unknown role or confidence) is dropped, so a malformed roles field never fails the judge's main output.
- `tolerate_roles(data: Any) -> Any` ([source](../../../../../../src/learnloop/reader/source_roles.py), line 135) — A ``mode="before"`` model validator's body: the judgment's ``roles`` replaced by :func:`clean_roles` of it (``[]`` when missing).
- `tolerate_malformed_roles(data: Any) -> Any` ([source](../../../../../../src/learnloop/reader/source_roles.py), line 151) — The cue judge's ``mode="before"`` validator (fix round 4): a ``roles`` array RW3b's schema (``list[RoleProposal]``) accepts passes unchanged, duplicates and order kept, so a valid answer is returned and stored as the base returned and stored it; only a missing or malformed field…
- `class TolerantRoles(WireModel)` ([source](../../../../../../src/learnloop/reader/source_roles.py), line 172) — A judgment whose ``roles`` field is read with :func:`tolerate_roles`.
  - `_tolerate_roles(cls, data: Any) -> Any` (line 177; internal)
- `on_demand_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/reader/source_roles.py), line 189) — The judges' role proposals are written (``roles.on_demand_enabled``).
- `positive_filter_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/reader/source_roles.py), line 195) — Proposals are read by filters and groupings (``roles.positive_filter_enabled``).
- `batch_max_cost_usd(vault: Any) -> float` ([source](../../../../../../src/learnloop/reader/source_roles.py), line 201)
- `object_type_for(role: str) -> str` ([source](../../../../../../src/learnloop/reader/source_roles.py), line 205)
- `propose_roles(vault: Any, repository: Repository, claims: Sequence[Mapping[str, Any]], *, judge: str, prompt_version: str, model: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/source_roles.py), line 249) — Write each ``{extraction_id, span_id, role, confidence, ledger_id}`` as a proposal (one object per passage and role; a second judge's agreement a version).
- `claims_from_judgments(refs: Mapping[str, Key], judgments: Mapping[str, Any], ledger_ids: Mapping[Key, str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/source_roles.py), line 330) — The role claims of a listwise judge's judgments (``ref -> judgment``, each with a ``roles`` field), in the pool's order.
- `class RoleLabel` ([source](../../../../../../src/learnloop/reader/source_roles.py), line 351) — One visible role proposal on one passage of a current reading.
  - `low(self) -> bool` (line 365; public)
  - `as_dict(self) -> dict[str, Any]` (line 368; public)
- `role_proposals(vault: Any, repository: Repository, *, extraction_ids: Iterable[str] | None=None, roles: Iterable[str] | None=None) -> list[RoleLabel]` ([source](../../../../../../src/learnloop/reader/source_roles.py), line 381) — The visible RW4e role proposals (one per object and citation), oldest first: head versions ``proposed`` or ``reviewed`` with an ``authorial_role``, on the reading each citation resolves to now (the one alias authority), without any object ``hidden_source_objects`` hides.
- `role_keys(vault: Any, repository: Repository, extraction_ids: Iterable[str], roles: Iterable[str]) -> tuple[set[Key], set[Key]]` ([source](../../../../../../src/learnloop/reader/source_roles.py), line 454) — Passages a visible proposal gives one of ``roles``: ``(confident, low)``, a passage with any confident proposal never in ``low``.
- `best_roles(vault: Any, repository: Repository, keys: Iterable[Key]) -> dict[Key, RoleLabel]` ([source](../../../../../../src/learnloop/reader/source_roles.py), line 466) — Each passage's best visible proposal: the best confidence (``low`` only when nothing better exists), then the most judges, then the vocabulary's order.

### Module constants

- `ROLES` ([src/learnloop/reader/source_roles.py](../../../../../../src/learnloop/reader/source_roles.py), line 64)
- `CONFIDENCES` ([src/learnloop/reader/source_roles.py](../../../../../../src/learnloop/reader/source_roles.py), line 68)
- `JUDGE_ORGANIZER` ([src/learnloop/reader/source_roles.py](../../../../../../src/learnloop/reader/source_roles.py), line 70)
- `JUDGE_CUE` ([src/learnloop/reader/source_roles.py](../../../../../../src/learnloop/reader/source_roles.py), line 71)
- `JUDGE_LABELLER` ([src/learnloop/reader/source_roles.py](../../../../../../src/learnloop/reader/source_roles.py), line 72)
- `JUDGE_COVERAGE` ([src/learnloop/reader/source_roles.py](../../../../../../src/learnloop/reader/source_roles.py), line 76)
- `JUDGES` ([src/learnloop/reader/source_roles.py](../../../../../../src/learnloop/reader/source_roles.py), line 77)
- `PROPOSAL_KIND` ([src/learnloop/reader/source_roles.py](../../../../../../src/learnloop/reader/source_roles.py), line 79)
- `PROPOSAL_KIND_SQL` ([src/learnloop/reader/source_roles.py](../../../../../../src/learnloop/reader/source_roles.py), line 81)
- `OBJECT_TYPE_FOR_ROLE` ([src/learnloop/reader/source_roles.py](../../../../../../src/learnloop/reader/source_roles.py), line 84)
- `MODEL_LABEL` ([src/learnloop/reader/source_roles.py](../../../../../../src/learnloop/reader/source_roles.py), line 88)
- `ROLE_GROUPS` ([src/learnloop/reader/source_roles.py](../../../../../../src/learnloop/reader/source_roles.py), line 91)
- `_CONFIDENCE_RANK` ([src/learnloop/reader/source_roles.py](../../../../../../src/learnloop/reader/source_roles.py), line 100)
- `_BASE_ROLES` ([src/learnloop/reader/source_roles.py](../../../../../../src/learnloop/reader/source_roles.py), line 147)
- `_MISSING` ([src/learnloop/reader/source_roles.py](../../../../../../src/learnloop/reader/source_roles.py), line 148)

### Explicit exports

`__all__` declares:

- `CONFIDENCES`
- `JUDGES`
- `JUDGE_COVERAGE`
- `JUDGE_CUE`
- `JUDGE_LABELLER`
- `JUDGE_ORGANIZER`
- `MODEL_LABEL`
- `OBJECT_TYPE_FOR_ROLE`
- `PROPOSAL_KIND`
- `PROPOSAL_KIND_SQL`
- `ROLES`
- `ROLE_GROUPS`
- `RoleLabel`
- `RoleProposal`
- `TolerantRoles`
- `batch_max_cost_usd`
- `best_roles`
- `claims_from_judgments`
- `clean_roles`
- `object_type_for`
- `on_demand_enabled`
- `positive_filter_enabled`
- `propose_roles`
- `role_keys`
- `role_proposals`
- `tolerate_malformed_roles`
- `tolerate_roles`

## Internal implementation anchors

- `_settings(vault: Any) -> Any` ([source](../../../../../../src/learnloop/reader/source_roles.py), line 185)
- `_existing(repository: Repository, revision_ids: Iterable[str]) -> dict[tuple[Any, ...], dict[str, Any]]` ([source](../../../../../../src/learnloop/reader/source_roles.py), line 213) — Role proposals already on these revisions, keyed ``(revision, span, block hash, role)``: each head's object id, status and judges.
- `_content(text: Any) -> Mapping[str, Any]` ([source](../../../../../../src/learnloop/reader/source_roles.py), line 373)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `PROPOSAL_KIND_SQL`, `role_keys`; statically calls `role_keys`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `PROPOSAL_KIND_SQL`, `positive_filter_enabled`, `role_proposals`; statically calls `positive_filter_enabled`, `role_proposals`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `module`; statically calls `best_roles`, `claims_from_judgments`, `clean_roles`, `on_demand_enabled`, `positive_filter_enabled`, `propose_roles`, `tolerate_roles`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `RoleProposal`, `module`, `tolerate_malformed_roles`; statically calls `tolerate_malformed_roles`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `module`; statically calls `best_roles`
- [[Reference/Modules/learnloop/source_retrieval/role_labeller|learnloop.source_retrieval.role_labeller]] — imports `module`; statically calls `batch_max_cost_usd`, `claims_from_judgments`, `clean_roles`, `propose_roles`, `tolerate_roles`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `positive_filter_enabled`; statically calls `positive_filter_enabled`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `module`; statically calls `best_roles`, `clean_roles`, `on_demand_enabled`, `propose_roles`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `module`; calls `exam_material`
- [[Reference/Modules/learnloop/content/sources/span_aliases|learnloop.content.sources.span_aliases]] — imports `CITATION_MADE_AT_SQL`, `CitationResolver`; calls `CitationResolver`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `block_content_hashes`, `existing_spans`, `extraction_source_ids`; calls `block_content_hashes`, `existing_spans`, `extraction_source_ids`
- [[Reference/Modules/learnloop/reader/source_objects|learnloop.reader.source_objects]] — imports `module`; calls `append_proposal_version`, `author_source_object`, `hidden_source_objects`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `json`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]], [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]], [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]], [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]], [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reading_paths.py](../../../../../../tests/test_reading_paths.py) — direct import
  - `test_f5_a_role_proposal_the_role_switch_and_title_edits_rejudge_a_cached_path`
  - `test_section_roles_combine_role_hint_and_visible_rw4e_proposals`
- [tests/test_roles_concurrency.py](../../../../../../tests/test_roles_concurrency.py) — direct import
  - `test_a_review_between_a_judges_read_and_its_write_stands`
  - `test_a_review_that_won_the_lock_first_takes_no_further_proposal`
  - `test_two_judges_at_once_make_one_object_with_their_agreement`
- [tests/test_roles_judges.py](../../../../../../tests/test_roles_judges.py) — direct import
  - `test_library_answers_group_a_proposed_role_labelled_as_the_models`
  - `test_rw3b_contrast_list_a_confident_contrast_the_judge_may_not_be_shown_never_blocks_the_low_one`
  - `test_rw3b_contrast_list_takes_a_low_confidence_proposal_only_when_none_better_is_on_target`
  - `test_rw3b_prefers_contrast_and_counterexample_passages_for_distinction_cues`
  - `test_two_judges_agreeing_on_a_passages_role_make_one_proposal_with_two_versions`
- [tests/test_roles_switch_off.py](../../../../../../tests/test_roles_switch_off.py) — direct import
- [tests/test_section_coverage_review.py](../../../../../../tests/test_section_coverage_review.py) — direct import
  - `test_f5_a_crash_before_the_proposals_is_recovered_without_a_call`
- [tests/test_source_roles.py](../../../../../../tests/test_source_roles.py) — direct import
  - `test_a_failing_protection_read_returns_no_proposal`
  - `test_a_proposal_carries_confidence_judge_ledger_id_revision_and_one_citation`
  - `test_a_proposal_held_out_later_is_never_returned`
  - `test_a_reviewed_or_rejected_proposal_takes_no_further_version`
  - `test_a_second_judge_adds_a_version_and_the_same_judge_writes_nothing`
  - `test_an_unreadable_exam_predicate_proposes_nothing`
  - `test_clean_roles_reads_a_roles_field_tolerantly`
  - `test_roles_filters_match_ingest_hints_and_proposals_with_the_low_confidence_rule`
  - `test_the_object_type_is_mapped_by_section_3_4_item_14`
  - `test_the_reader_report_counts_proposals_by_role_judge_and_agreement`

## Modification guidance

- Change source roles policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/source_roles.py](../../../../../../src/learnloop/reader/source_roles.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
