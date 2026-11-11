---
title: "learnloop.db.stores.judgments"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/judgments.py"
source_paths:
  - "src/learnloop/db/stores/judgments.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.stores.judgments module"
  - "src/learnloop/db/stores/judgments.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.judgments`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.judgments` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Append-only verdict inputs.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/judgments.py](../../../../../../../src/learnloop/db/stores/judgments.py) |
| Source lines | 42 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `append_judgment(connection: sqlite3.Connection, *, task: str, left_kind: str, left_id: str, judge: str, input_hash: str, verdict: str, right_kind: str | None=None, right_id: str | None=None, judge_model: str | None=None, prompt_version: str | None=None, score: float | None=None, rationale: str='', supersedes_id: str | None=None, id: str | None=None, created_at: str | None=None) -> str` ([source](../../../../../../../src/learnloop/db/stores/judgments.py), line 14) — Append within the caller's transaction; SQL enforces supersession identity.

### Module constants

- `MODEL_JUDGES` ([src/learnloop/db/stores/judgments.py](../../../../../../../src/learnloop/db/stores/judgments.py), line 11)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/attempts/stuck|learnloop.attempts.stuck]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/content/facet_identity/judge|learnloop.content.facet_identity.judge]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/content/facet_identity/span_support|learnloop.content.facet_identity.span_support]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/content/pipeline/exam_marking|learnloop.content.pipeline.exam_marking]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/content/proposals/method_phrasing|learnloop.content.proposals.method_phrasing]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/content/proposals/method_statement_judge|learnloop.content.proposals.method_statement_judge]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/content/proposals/required_method_override|learnloop.content.proposals.required_method_override]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/curriculum/subject_registry|learnloop.curriculum.subject_registry]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/diagnosis/offline_review/links|learnloop.diagnosis.offline_review.links]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/diagnosis/split/card|learnloop.diagnosis.split.card]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/diagnosis/split/pfc_report|learnloop.diagnosis.split.pfc_report]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/records|learnloop.experiments.contextual_embeddings.records]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/field/classification|learnloop.field.classification]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/field/probability_prep|learnloop.field.probability_prep]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/hints/chooser|learnloop.hints.chooser]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/hints/outcome|learnloop.hints.outcome]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/instructional/reader_digest|learnloop.instructional.reader_digest]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/instructional/screen|learnloop.instructional.screen]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/matching/judge|learnloop.matching.judge]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/ops/contamination/judge|learnloop.ops.contamination.judge]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/ops/contamination/report|learnloop.ops.contamination.report]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/ops/family_proposals|learnloop.ops.family_proposals]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/ops/pf_calls|learnloop.ops.pf_calls]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/ops/pf_publish|learnloop.ops.pf_publish]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/practice_index/listwise|learnloop.practice_index.listwise]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/practice_index/usage|learnloop.practice_index.usage]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/reader/reader_cues|learnloop.reader.reader_cues]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/reader/reader_intent|learnloop.reader.reader_intent]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/source_retrieval/compare_scope|learnloop.source_retrieval.compare_scope]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/source_retrieval/note_links|learnloop.source_retrieval.note_links]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/substrate/families|learnloop.substrate.families]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/workbench/check|learnloop.workbench.check]] — imports `append_judgment`; statically calls `append_judgment`
- [[Reference/Modules/learnloop/workbench/compare_methods|learnloop.workbench.compare_methods]] — imports `append_judgment`; statically calls `append_judgment`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `math`, `sqlite3`, `uuid`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]], [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]], [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]], [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]], [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]] and 63 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad23_contract_helpers.py](../../../../../../../tests/ad23_contract_helpers.py) — direct import
- [tests/help_outcomes_helpers.py](../../../../../../../tests/help_outcomes_helpers.py) — direct import
- [tests/recurrence_fakes.py](../../../../../../../tests/recurrence_fakes.py) — direct import
- [tests/test_activity_families.py](../../../../../../../tests/test_activity_families.py) — direct import
  - `test_verifier_rejects_unbound_acceptance`
- [tests/test_ad2_model.py](../../../../../../../tests/test_ad2_model.py) — direct import
- [tests/test_contamination_report.py](../../../../../../../tests/test_contamination_report.py) — direct import
  - `test_owner_verdict_outranks_the_judge`
  - `test_the_report_carries_a_repeated_judgment_noise_floor_and_owner_audits`
- [tests/test_decider_agreement.py](../../../../../../../tests/test_decider_agreement.py) — direct import
  - `test_agreement_cli_is_read_only_and_reads_review_runs`
  - `test_agreement_counts_each_ledger_row_once_across_a_review_runs_vault_copy`
  - `test_agreement_reports_real_pairs_fallbacks_and_labels`
  - `test_span_support_labels_never_leak_to_another_rewords_check`
- [tests/test_decider_landing.py](../../../../../../../tests/test_decider_landing.py) — direct import
  - `test_a_link_recorded_at_main_mvp020_or_mvp021_has_no_decider_authority`
- [tests/test_embedding_store.py](../../../../../../../tests/test_embedding_store.py) — direct import
  - `test_replay_preserves_paid_inputs_without_models`
- [tests/test_figures_help.py](../../../../../../../tests/test_figures_help.py) — direct import
  - `test_a_figure_built_from_the_items_own_blocks_never_qualifies`
- [tests/test_graph_nomination_ingest.py](../../../../../../../tests/test_graph_nomination_ingest.py) — direct import
  - `test_registry_merge_is_declined_when_its_verdict_cannot_be_ledgered`
- [tests/test_graph_nomination_report.py](../../../../../../../tests/test_graph_nomination_report.py) — direct import
  - `test_ledger_same_verdicts_join_the_ground_truth`
- [tests/test_help_outcomes.py](../../../../../../../tests/test_help_outcomes.py) — direct import
  - `test_f3_hints_the_learner_picked_stay_in_the_history_passage_picks_do_not_count_twice`
- [tests/test_judge_routes.py](../../../../../../../tests/test_judge_routes.py) — direct import
  - `test_judgment_ledger_accepts_the_decider_with_provenance`
  - `test_migration_175_preserves_every_judgment_and_its_references`
- [tests/test_judgment_ledger.py](../../../../../../../tests/test_judgment_ledger.py) — direct import
  - `test_append_and_validated_supersession`
  - `test_database_protects_history`
  - `test_model_judges_accept_complete_provenance`
  - `test_model_judges_require_provenance_in_api_and_sql`
  - `test_other_judges_keep_optional_provenance`
  - `test_unary_verdict_and_validation`
- [tests/test_learner_text_gaps_composition.py](../../../../../../../tests/test_learner_text_gaps_composition.py) — direct import
- [tests/test_learner_text_gaps_rereview.py](../../../../../../../tests/test_learner_text_gaps_rereview.py) — direct import
  - `test_rr_f6_only_a_tap_on_a_belief_answer_is_counted`
- [tests/test_recurrence_groups.py](../../../../../../../tests/test_recurrence_groups.py) — direct import
  - `test_supersession_is_how_a_judges_different_is_replaced`
- [tests/test_recurrence_merge_composition.py](../../../../../../../tests/test_recurrence_merge_composition.py) — direct import
  - `test_a_decider_same_cause_verdict_is_logged_but_joins_no_group`
- [tests/test_route_rules_in_grader.py](../../../../../../../tests/test_route_rules_in_grader.py) — direct import
  - `test_f5_a_joint_regrade_supersedes_a_route_verdict`
- [tests/test_tier1_decider.py](../../../../../../../tests/test_tier1_decider.py) — direct import
  - `test_only_new_authoritative_decider_links_reach_recurrence`
  - `test_the_gaps_report_skips_decider_failure_rows`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/judgments.py](../../../../../../../src/learnloop/db/stores/judgments.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
