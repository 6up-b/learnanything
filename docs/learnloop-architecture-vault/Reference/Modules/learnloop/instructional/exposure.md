---
title: "learnloop.instructional.exposure"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/instructional/exposure.py"
source_paths:
  - "src/learnloop/instructional/exposure.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.instructional"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.instructional.exposure module"
  - "src/learnloop/instructional/exposure.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-instructional"
---

# `learnloop.instructional.exposure`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.instructional.exposure` exists within [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] to own the behavior summarized by its module contract: Independent-check eligibility: the exposure rule (spec_source_practice_and_probes_v1 §5.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/instructional/exposure.py](../../../../../../src/learnloop/instructional/exposure.py) |
| Source lines | 389 |
| Owning package | [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class EquivalenceJudgment(WireModel)` ([source](../../../../../../src/learnloop/instructional/exposure.py), line 61)
- `class EquivalenceVerdicts(WireModel)` ([source](../../../../../../src/learnloop/instructional/exposure.py), line 67)
- `studied_worked_examples(repository: Repository, extraction_ids: Sequence[str], *, since: str) -> list[tuple[str, str, str, str]]` ([source](../../../../../../src/learnloop/instructional/exposure.py), line 94) — Worked-example blocks shown to the learner, or in sections they read, since ``since``: ``(extraction_id, span_id, text, studied_at)``, where ``studied_at`` is the latest exposure or reading-progress stamp (S5's time since the related exposure, router §15.2's covariate).
- `independent_check_eligibility(vault: LoadedVault, repository: Repository, candidate: Mapping[str, Any], *, intent: str, at: Any | None=None, picked_proposal_id: str | None=None, judge_client: Any | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/exposure.py), line 132) — Whether ``candidate`` may stand as an independent check now, and why not.
- `practice_label(reasons: Sequence[str]) -> str` ([source](../../../../../../src/learnloop/instructional/exposure.py), line 237) — The label for a candidate served as practice, not as an independent check.
- `apply_dominance(entries: list[dict[str, Any]], eligibility: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/instructional/exposure.py), line 357) — A ``related``-labelled candidate never goes ahead of an unlabelled one whose robust value interval overlaps its own (a documented tie-break, decision-value §6.4).

### Module constants

- `EXPOSURE_RULE_VERSION` ([src/learnloop/instructional/exposure.py](../../../../../../src/learnloop/instructional/exposure.py), line 47)
- `INDEPENDENT_INTENTS` ([src/learnloop/instructional/exposure.py](../../../../../../src/learnloop/instructional/exposure.py), line 48)
- `EQUIVALENCE_PROMPT_VERSION` ([src/learnloop/instructional/exposure.py](../../../../../../src/learnloop/instructional/exposure.py), line 49)
- `SHORTLIST` ([src/learnloop/instructional/exposure.py](../../../../../../src/learnloop/instructional/exposure.py), line 51)
- `_EQUIVALENCE_INSTRUCTIONS` ([src/learnloop/instructional/exposure.py](../../../../../../src/learnloop/instructional/exposure.py), line 52)
- `EQUIVALENCE_TASK` ([src/learnloop/instructional/exposure.py](../../../../../../src/learnloop/instructional/exposure.py), line 72)
- `_PRACTICE_LABELS` ([src/learnloop/instructional/exposure.py](../../../../../../src/learnloop/instructional/exposure.py), line 229)
- `SEEN_SINCE_LABEL` ([src/learnloop/instructional/exposure.py](../../../../../../src/learnloop/instructional/exposure.py), line 234)

### Explicit exports

`__all__` declares:

- `EQUIVALENCE_TASK`
- `EXPOSURE_RULE_VERSION`
- `EquivalenceVerdicts`
- `INDEPENDENT_INTENTS`
- `apply_dominance`
- `independent_check_eligibility`
- `practice_label`
- `SEEN_SINCE_LABEL`
- `studied_worked_examples`

## Internal implementation anchors

- `_iso(moment: Any) -> str` ([source](../../../../../../src/learnloop/instructional/exposure.py), line 83)
- `_family_items(vault: LoadedVault, item_id: str) -> set[str]` ([source](../../../../../../src/learnloop/instructional/exposure.py), line 87)
- `_seconds_since(now: Any, created_at: str) -> float | None` ([source](../../../../../../src/learnloop/instructional/exposure.py), line 249)
- `_solution_spans(connection: Any, extraction_id: str, span_ids: Sequence[str], candidate: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/instructional/exposure.py), line 256) — The exercise's own book solution, when the import found one.
- `_candidate_text(vault: LoadedVault, repository: Repository, candidate: Mapping[str, Any], item: Any) -> str` ([source](../../../../../../src/learnloop/instructional/exposure.py), line 274)
- `_worked_example_rule(vault: LoadedVault, repository: Repository, candidate: Mapping[str, Any], item: Any, extraction_id: str | None, *, since: str, judge_client: Any | None, now: Any | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/exposure.py), line 280)
- `_judge_equivalence(vault, repository, prompt, refs, candidate, text, judge_client, validate)` ([source](../../../../../../src/learnloop/instructional/exposure.py), line 330)
- `_equivalence_result(refs, outcome) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/exposure.py), line 345)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/instructional/discriminating|learnloop.instructional.discriminating]] — imports `apply_dominance`, `independent_check_eligibility`; statically calls `apply_dominance`, `independent_check_eligibility`
- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `independent_check_eligibility`; statically calls `independent_check_eligibility`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `module`; statically calls `independent_check_eligibility`
- [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]] — imports `EXPOSURE_RULE_VERSION`, `independent_check_eligibility`; statically calls `independent_check_eligibility`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInvalidOutput`; calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`; calls `SystemClock`, `parse_utc`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `blocks_by_key`, `extraction_units`, `search_blocks`; calls `blocks_by_key`, `extraction_units`, `search_blocks`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `impressions_of_item`, `impressions_of_spans`; calls `impressions_of_item`, `impressions_of_spans`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `COLD_RETRIEVAL_DELAY`
- [[Reference/Modules/learnloop/practice_index/listwise|learnloop.practice_index.listwise]] — imports `ListwiseTask`, `judge_listwise`, `listwise_caps`; calls `ListwiseTask`, `judge_listwise`, `listwise_caps`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `plan_route`; calls `plan_route`
- [[Reference/Modules/learnloop/reveal_coverage|learnloop.reveal_coverage]] — imports `routine_coverage_sql`, `routine_window_start`; calls `routine_coverage_sql`, `routine_window_start`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `role_keys`, `teaching_scope`; calls `role_keys`, `teaching_scope`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `service_spend`; calls `service_spend`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/instructional/discriminating|learnloop.instructional.discriminating]], [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]], [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]], [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/source_service_fakes.py](../../../../../../tests/source_service_fakes.py) — direct import
- [tests/test_discriminating_search.py](../../../../../../tests/test_discriminating_search.py) — direct import
  - `test_an_earlier_impression_and_a_source_exposure_exclude`
  - `test_an_unjudged_studied_worked_example_excludes_every_independent_intent`
  - `test_dominance_never_puts_a_labelled_candidate_first_when_values_overlap`
  - `test_equivalent_worked_example_excludes_both_independent_intents`
- [tests/test_mcp_tools.py](../../../../../../tests/test_mcp_tools.py) — direct import
  - `test_shown_passages_are_exposure_for_the_items_built_on_them`
- [tests/test_reader_followups_review.py](../../../../../../tests/test_reader_followups_review.py) — direct import
  - `test_f5_an_unjudged_worked_example_is_refreshed_in_the_background_under_both_envelopes`
- [tests/test_retrieval_interventions_write_points.py](../../../../../../tests/test_retrieval_interventions_write_points.py) — direct import
  - `test_an_opened_offer_records_exposure_that_independence_reads`
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f1i_an_independent_check_is_not_offered_inside_a_display_s_coverage`
- [tests/test_valuation_calibration_fields.py](../../../../../../tests/test_valuation_calibration_fields.py) — direct import
  - `test_a_studied_worked_example_records_the_seconds_since_exposure`
  - `test_exposure_age_is_measured_at_delivery_not_at_valuation`

## Modification guidance

- Make changes here when the responsibility remains exposure within learnloop.instructional; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/instructional/exposure.py](../../../../../../src/learnloop/instructional/exposure.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
