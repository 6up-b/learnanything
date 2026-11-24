---
title: "learnloop.db.stores — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/db/stores/__init__.py"
  - "src/learnloop/db/stores/activity.py"
  - "src/learnloop/db/stores/ad_receipts.py"
  - "src/learnloop/db/stores/ad_serving.py"
  - "src/learnloop/db/stores/answered_contracts.py"
  - "src/learnloop/db/stores/approach_maps.py"
  - "src/learnloop/db/stores/attempts.py"
  - "src/learnloop/db/stores/causal.py"
  - "src/learnloop/db/stores/check_administrations.py"
  - "src/learnloop/db/stores/collection.py"
  - "src/learnloop/db/stores/completion.py"
  - "src/learnloop/db/stores/content.py"
  - "src/learnloop/db/stores/daily_plans.py"
  - "src/learnloop/db/stores/data_capture.py"
  - "src/learnloop/db/stores/deliverables.py"
  - "src/learnloop/db/stores/desks.py"
  - "src/learnloop/db/stores/diagnoses.py"
  - "src/learnloop/db/stores/diagnosis_review.py"
  - "src/learnloop/db/stores/embedding_vectors.py"
  - "src/learnloop/db/stores/facet_identity.py"
  - "src/learnloop/db/stores/facet_projection.py"
  - "src/learnloop/db/stores/families.py"
  - "src/learnloop/db/stores/field.py"
  - "src/learnloop/db/stores/field_signal_receipts.py"
  - "src/learnloop/db/stores/figure_prefetch.py"
  - "src/learnloop/db/stores/figures.py"
  - "src/learnloop/db/stores/followup_serve.py"
  - "src/learnloop/db/stores/followup_value.py"
  - "src/learnloop/db/stores/forecast_receipts.py"
  - "src/learnloop/db/stores/goals.py"
  - "src/learnloop/db/stores/grading.py"
  - "src/learnloop/db/stores/held_out_signals.py"
  - "src/learnloop/db/stores/help_assists.py"
  - "src/learnloop/db/stores/hypothesis_marks.py"
  - "src/learnloop/db/stores/ingest_queue.py"
  - "src/learnloop/db/stores/ink_strokes.py"
  - "src/learnloop/db/stores/intent_reads.py"
  - "src/learnloop/db/stores/judgment_claims.py"
  - "src/learnloop/db/stores/judgments.py"
  - "src/learnloop/db/stores/learner_gaps.py"
  - "src/learnloop/db/stores/learner_model.py"
  - "src/learnloop/db/stores/learner_notes.py"
  - "src/learnloop/db/stores/lessons.py"
  - "src/learnloop/db/stores/library_asks.py"
  - "src/learnloop/db/stores/maintenance.py"
  - "src/learnloop/db/stores/model_calls.py"
  - "src/learnloop/db/stores/observation_ledger.py"
  - "src/learnloop/db/stores/pad_ledgers.py"
  - "src/learnloop/db/stores/pad_reads.py"
  - "src/learnloop/db/stores/pads.py"
  - "src/learnloop/db/stores/passage_link_reads.py"
  - "src/learnloop/db/stores/pf.py"
  - "src/learnloop/db/stores/placement.py"
  - "src/learnloop/db/stores/plan_presentations.py"
  - "src/learnloop/db/stores/practice_index.py"
  - "src/learnloop/db/stores/practice_state.py"
  - "src/learnloop/db/stores/probes.py"
  - "src/learnloop/db/stores/provenance.py"
  - "src/learnloop/db/stores/questions.py"
  - "src/learnloop/db/stores/reader.py"
  - "src/learnloop/db/stores/reader_cue_links.py"
  - "src/learnloop/db/stores/reader_digests.py"
  - "src/learnloop/db/stores/reading_paths.py"
  - "src/learnloop/db/stores/reading_requests.py"
  - "src/learnloop/db/stores/recurrence.py"
  - "src/learnloop/db/stores/remediation.py"
  - "src/learnloop/db/stores/retrieval_spaces.py"
  - "src/learnloop/db/stores/router.py"
  - "src/learnloop/db/stores/router_objective.py"
  - "src/learnloop/db/stores/router_suggestions.py"
  - "src/learnloop/db/stores/section_coverage.py"
  - "src/learnloop/db/stores/session_ownership.py"
  - "src/learnloop/db/stores/source_block_fts.py"
  - "src/learnloop/db/stores/source_documents.py"
  - "src/learnloop/db/stores/source_service.py"
  - "src/learnloop/db/stores/span_projection_reads.py"
  - "src/learnloop/db/stores/span_projections.py"
  - "src/learnloop/db/stores/task_blueprints.py"
  - "src/learnloop/db/stores/voi_forecasts.py"
  - "src/learnloop/db/stores/workbench.py"
  - "src/learnloop/db/stores/workspace_batches.py"
  - "src/learnloop/db/stores/write_provenance.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Inspect Persistent State"
tags:
  - "docs/package-map"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

Table-family persistence owners extracted from the repository facade.

For system intent, use [[State and Persistence]], [[Architecture Overview]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop/db/stores/__init__|learnloop.db.stores]] | [[Reference/Modules/learnloop/db/stores/__init__#^module-purpose|purpose]] | `ACTIVE` | 0 | 0 |
| [[Reference/Modules/learnloop/db/stores/activity|learnloop.db.stores.activity]] | [[Reference/Modules/learnloop/db/stores/activity#^module-purpose|purpose]] | `ACTIVE` | 1 | 0 |
| [[Reference/Modules/learnloop/db/stores/ad_receipts|learnloop.db.stores.ad_receipts]] | [[Reference/Modules/learnloop/db/stores/ad_receipts#^module-purpose|purpose]] | `ACTIVE` | 12 | 8 |
| [[Reference/Modules/learnloop/db/stores/ad_serving|learnloop.db.stores.ad_serving]] | [[Reference/Modules/learnloop/db/stores/ad_serving#^module-purpose|purpose]] | `ACTIVE` | 12 | 12 |
| [[Reference/Modules/learnloop/db/stores/answered_contracts|learnloop.db.stores.answered_contracts]] | [[Reference/Modules/learnloop/db/stores/answered_contracts#^module-purpose|purpose]] | `ACTIVE` | 5 | 0 |
| [[Reference/Modules/learnloop/db/stores/approach_maps|learnloop.db.stores.approach_maps]] | [[Reference/Modules/learnloop/db/stores/approach_maps#^module-purpose|purpose]] | `ACTIVE` | 4 | 2 |
| [[Reference/Modules/learnloop/db/stores/attempts|learnloop.db.stores.attempts]] | [[Reference/Modules/learnloop/db/stores/attempts#^module-purpose|purpose]] | `ACTIVE` | 5 | 4 |
| [[Reference/Modules/learnloop/db/stores/causal|learnloop.db.stores.causal]] | [[Reference/Modules/learnloop/db/stores/causal#^module-purpose|purpose]] | `ACTIVE` | 2 | 0 |
| [[Reference/Modules/learnloop/db/stores/check_administrations|learnloop.db.stores.check_administrations]] | [[Reference/Modules/learnloop/db/stores/check_administrations#^module-purpose|purpose]] | `ACTIVE` | 2 | 1 |
| [[Reference/Modules/learnloop/db/stores/collection|learnloop.db.stores.collection]] | [[Reference/Modules/learnloop/db/stores/collection#^module-purpose|purpose]] | `ACTIVE` | 1 | 3 |
| [[Reference/Modules/learnloop/db/stores/completion|learnloop.db.stores.completion]] | [[Reference/Modules/learnloop/db/stores/completion#^module-purpose|purpose]] | `ACTIVE` | 1 | 0 |
| [[Reference/Modules/learnloop/db/stores/content|learnloop.db.stores.content]] | [[Reference/Modules/learnloop/db/stores/content#^module-purpose|purpose]] | `ACTIVE` | 1 | 0 |
| [[Reference/Modules/learnloop/db/stores/daily_plans|learnloop.db.stores.daily_plans]] | [[Reference/Modules/learnloop/db/stores/daily_plans#^module-purpose|purpose]] | `ACTIVE` | 9 | 4 |
| [[Reference/Modules/learnloop/db/stores/data_capture|learnloop.db.stores.data_capture]] | [[Reference/Modules/learnloop/db/stores/data_capture#^module-purpose|purpose]] | `ACTIVE` | 5 | 8 |
| [[Reference/Modules/learnloop/db/stores/deliverables|learnloop.db.stores.deliverables]] | [[Reference/Modules/learnloop/db/stores/deliverables#^module-purpose|purpose]] | `ACTIVE` | 3 | 5 |
| [[Reference/Modules/learnloop/db/stores/desks|learnloop.db.stores.desks]] | [[Reference/Modules/learnloop/db/stores/desks#^module-purpose|purpose]] | `ACTIVE` | 3 | 0 |
| [[Reference/Modules/learnloop/db/stores/diagnoses|learnloop.db.stores.diagnoses]] | [[Reference/Modules/learnloop/db/stores/diagnoses#^module-purpose|purpose]] | `ACTIVE` | 5 | 0 |
| [[Reference/Modules/learnloop/db/stores/diagnosis_review|learnloop.db.stores.diagnosis_review]] | [[Reference/Modules/learnloop/db/stores/diagnosis_review#^module-purpose|purpose]] | `ACTIVE` | 5 | 1 |
| [[Reference/Modules/learnloop/db/stores/embedding_vectors|learnloop.db.stores.embedding_vectors]] | [[Reference/Modules/learnloop/db/stores/embedding_vectors#^module-purpose|purpose]] | `ACTIVE` | 19 | 11 |
| [[Reference/Modules/learnloop/db/stores/facet_identity|learnloop.db.stores.facet_identity]] | [[Reference/Modules/learnloop/db/stores/facet_identity#^module-purpose|purpose]] | `ACTIVE` | 4 | 1 |
| [[Reference/Modules/learnloop/db/stores/facet_projection|learnloop.db.stores.facet_projection]] | [[Reference/Modules/learnloop/db/stores/facet_projection#^module-purpose|purpose]] | `ACTIVE` | 6 | 0 |
| [[Reference/Modules/learnloop/db/stores/families|learnloop.db.stores.families]] | [[Reference/Modules/learnloop/db/stores/families#^module-purpose|purpose]] | `ACTIVE` | 4 | 1 |
| [[Reference/Modules/learnloop/db/stores/field|learnloop.db.stores.field]] | [[Reference/Modules/learnloop/db/stores/field#^module-purpose|purpose]] | `ACTIVE` | 2 | 0 |
| [[Reference/Modules/learnloop/db/stores/field_signal_receipts|learnloop.db.stores.field_signal_receipts]] | [[Reference/Modules/learnloop/db/stores/field_signal_receipts#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/db/stores/figure_prefetch|learnloop.db.stores.figure_prefetch]] | [[Reference/Modules/learnloop/db/stores/figure_prefetch#^module-purpose|purpose]] | `ACTIVE` | 1 | 0 |
| [[Reference/Modules/learnloop/db/stores/figures|learnloop.db.stores.figures]] | [[Reference/Modules/learnloop/db/stores/figures#^module-purpose|purpose]] | `ACTIVE` | 15 | 14 |
| [[Reference/Modules/learnloop/db/stores/followup_serve|learnloop.db.stores.followup_serve]] | [[Reference/Modules/learnloop/db/stores/followup_serve#^module-purpose|purpose]] | `ACTIVE` | 8 | 15 |
| [[Reference/Modules/learnloop/db/stores/followup_value|learnloop.db.stores.followup_value]] | [[Reference/Modules/learnloop/db/stores/followup_value#^module-purpose|purpose]] | `ACTIVE` | 1 | 0 |
| [[Reference/Modules/learnloop/db/stores/forecast_receipts|learnloop.db.stores.forecast_receipts]] | [[Reference/Modules/learnloop/db/stores/forecast_receipts#^module-purpose|purpose]] | `ACTIVE` | 3 | 7 |
| [[Reference/Modules/learnloop/db/stores/goals|learnloop.db.stores.goals]] | [[Reference/Modules/learnloop/db/stores/goals#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/db/stores/grading|learnloop.db.stores.grading]] | [[Reference/Modules/learnloop/db/stores/grading#^module-purpose|purpose]] | `ACTIVE` | 2 | 0 |
| [[Reference/Modules/learnloop/db/stores/held_out_signals|learnloop.db.stores.held_out_signals]] | [[Reference/Modules/learnloop/db/stores/held_out_signals#^module-purpose|purpose]] | `ACTIVE` | 3 | 1 |
| [[Reference/Modules/learnloop/db/stores/help_assists|learnloop.db.stores.help_assists]] | [[Reference/Modules/learnloop/db/stores/help_assists#^module-purpose|purpose]] | `ACTIVE` | 19 | 12 |
| [[Reference/Modules/learnloop/db/stores/hypothesis_marks|learnloop.db.stores.hypothesis_marks]] | [[Reference/Modules/learnloop/db/stores/hypothesis_marks#^module-purpose|purpose]] | `ACTIVE` | 8 | 5 |
| [[Reference/Modules/learnloop/db/stores/ingest_queue|learnloop.db.stores.ingest_queue]] | [[Reference/Modules/learnloop/db/stores/ingest_queue#^module-purpose|purpose]] | `ACTIVE` | 4 | 2 |
| [[Reference/Modules/learnloop/db/stores/ink_strokes|learnloop.db.stores.ink_strokes]] | [[Reference/Modules/learnloop/db/stores/ink_strokes#^module-purpose|purpose]] | `ACTIVE` | 2 | 0 |
| [[Reference/Modules/learnloop/db/stores/intent_reads|learnloop.db.stores.intent_reads]] | [[Reference/Modules/learnloop/db/stores/intent_reads#^module-purpose|purpose]] | `ACTIVE` | 5 | 0 |
| [[Reference/Modules/learnloop/db/stores/judgment_claims|learnloop.db.stores.judgment_claims]] | [[Reference/Modules/learnloop/db/stores/judgment_claims#^module-purpose|purpose]] | `ACTIVE` | 7 | 5 |
| [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] | [[Reference/Modules/learnloop/db/stores/judgments#^module-purpose|purpose]] | `ACTIVE` | 70 | 21 |
| [[Reference/Modules/learnloop/db/stores/learner_gaps|learnloop.db.stores.learner_gaps]] | [[Reference/Modules/learnloop/db/stores/learner_gaps#^module-purpose|purpose]] | `ACTIVE` | 15 | 13 |
| [[Reference/Modules/learnloop/db/stores/learner_model|learnloop.db.stores.learner_model]] | [[Reference/Modules/learnloop/db/stores/learner_model#^module-purpose|purpose]] | `ACTIVE` | 10 | 5 |
| [[Reference/Modules/learnloop/db/stores/learner_notes|learnloop.db.stores.learner_notes]] | [[Reference/Modules/learnloop/db/stores/learner_notes#^module-purpose|purpose]] | `ACTIVE` | 3 | 3 |
| [[Reference/Modules/learnloop/db/stores/lessons|learnloop.db.stores.lessons]] | [[Reference/Modules/learnloop/db/stores/lessons#^module-purpose|purpose]] | `ACTIVE` | 11 | 9 |
| [[Reference/Modules/learnloop/db/stores/library_asks|learnloop.db.stores.library_asks]] | [[Reference/Modules/learnloop/db/stores/library_asks#^module-purpose|purpose]] | `ACTIVE` | 3 | 0 |
| [[Reference/Modules/learnloop/db/stores/maintenance|learnloop.db.stores.maintenance]] | [[Reference/Modules/learnloop/db/stores/maintenance#^module-purpose|purpose]] | `ACTIVE` | 1 | 0 |
| [[Reference/Modules/learnloop/db/stores/model_calls|learnloop.db.stores.model_calls]] | [[Reference/Modules/learnloop/db/stores/model_calls#^module-purpose|purpose]] | `ACTIVE` | 4 | 4 |
| [[Reference/Modules/learnloop/db/stores/observation_ledger|learnloop.db.stores.observation_ledger]] | [[Reference/Modules/learnloop/db/stores/observation_ledger#^module-purpose|purpose]] | `ACTIVE` | 4 | 5 |
| [[Reference/Modules/learnloop/db/stores/pad_ledgers|learnloop.db.stores.pad_ledgers]] | [[Reference/Modules/learnloop/db/stores/pad_ledgers#^module-purpose|purpose]] | `ACTIVE` | 3 | 0 |
| [[Reference/Modules/learnloop/db/stores/pad_reads|learnloop.db.stores.pad_reads]] | [[Reference/Modules/learnloop/db/stores/pad_reads#^module-purpose|purpose]] | `ACTIVE` | 17 | 4 |
| [[Reference/Modules/learnloop/db/stores/pads|learnloop.db.stores.pads]] | [[Reference/Modules/learnloop/db/stores/pads#^module-purpose|purpose]] | `ACTIVE` | 3 | 2 |
| [[Reference/Modules/learnloop/db/stores/passage_link_reads|learnloop.db.stores.passage_link_reads]] | [[Reference/Modules/learnloop/db/stores/passage_link_reads#^module-purpose|purpose]] | `ACTIVE` | 1 | 0 |
| [[Reference/Modules/learnloop/db/stores/pf|learnloop.db.stores.pf]] | [[Reference/Modules/learnloop/db/stores/pf#^module-purpose|purpose]] | `ACTIVE` | 6 | 7 |
| [[Reference/Modules/learnloop/db/stores/placement|learnloop.db.stores.placement]] | [[Reference/Modules/learnloop/db/stores/placement#^module-purpose|purpose]] | `ACTIVE` | 2 | 2 |
| [[Reference/Modules/learnloop/db/stores/plan_presentations|learnloop.db.stores.plan_presentations]] | [[Reference/Modules/learnloop/db/stores/plan_presentations#^module-purpose|purpose]] | `ACTIVE` | 4 | 4 |
| [[Reference/Modules/learnloop/db/stores/practice_index|learnloop.db.stores.practice_index]] | [[Reference/Modules/learnloop/db/stores/practice_index#^module-purpose|purpose]] | `ACTIVE` | 17 | 10 |
| [[Reference/Modules/learnloop/db/stores/practice_state|learnloop.db.stores.practice_state]] | [[Reference/Modules/learnloop/db/stores/practice_state#^module-purpose|purpose]] | `ACTIVE` | 6 | 0 |
| [[Reference/Modules/learnloop/db/stores/probes|learnloop.db.stores.probes]] | [[Reference/Modules/learnloop/db/stores/probes#^module-purpose|purpose]] | `ACTIVE` | 9 | 0 |
| [[Reference/Modules/learnloop/db/stores/provenance|learnloop.db.stores.provenance]] | [[Reference/Modules/learnloop/db/stores/provenance#^module-purpose|purpose]] | `ACTIVE` | 24 | 7 |
| [[Reference/Modules/learnloop/db/stores/questions|learnloop.db.stores.questions]] | [[Reference/Modules/learnloop/db/stores/questions#^module-purpose|purpose]] | `ACTIVE` | 1 | 0 |
| [[Reference/Modules/learnloop/db/stores/reader|learnloop.db.stores.reader]] | [[Reference/Modules/learnloop/db/stores/reader#^module-purpose|purpose]] | `ACTIVE` | 6 | 0 |
| [[Reference/Modules/learnloop/db/stores/reader_cue_links|learnloop.db.stores.reader_cue_links]] | [[Reference/Modules/learnloop/db/stores/reader_cue_links#^module-purpose|purpose]] | `ACTIVE` | 2 | 11 |
| [[Reference/Modules/learnloop/db/stores/reader_digests|learnloop.db.stores.reader_digests]] | [[Reference/Modules/learnloop/db/stores/reader_digests#^module-purpose|purpose]] | `ACTIVE` | 4 | 13 |
| [[Reference/Modules/learnloop/db/stores/reading_paths|learnloop.db.stores.reading_paths]] | [[Reference/Modules/learnloop/db/stores/reading_paths#^module-purpose|purpose]] | `ACTIVE` | 1 | 0 |
| [[Reference/Modules/learnloop/db/stores/reading_requests|learnloop.db.stores.reading_requests]] | [[Reference/Modules/learnloop/db/stores/reading_requests#^module-purpose|purpose]] | `ACTIVE` | 1 | 0 |
| [[Reference/Modules/learnloop/db/stores/recurrence|learnloop.db.stores.recurrence]] | [[Reference/Modules/learnloop/db/stores/recurrence#^module-purpose|purpose]] | `ACTIVE` | 4 | 0 |
| [[Reference/Modules/learnloop/db/stores/remediation|learnloop.db.stores.remediation]] | [[Reference/Modules/learnloop/db/stores/remediation#^module-purpose|purpose]] | `ACTIVE` | 1 | 0 |
| [[Reference/Modules/learnloop/db/stores/retrieval_spaces|learnloop.db.stores.retrieval_spaces]] | [[Reference/Modules/learnloop/db/stores/retrieval_spaces#^module-purpose|purpose]] | `ACTIVE` | 8 | 5 |
| [[Reference/Modules/learnloop/db/stores/router|learnloop.db.stores.router]] | [[Reference/Modules/learnloop/db/stores/router#^module-purpose|purpose]] | `ACTIVE` | 12 | 15 |
| [[Reference/Modules/learnloop/db/stores/router_objective|learnloop.db.stores.router_objective]] | [[Reference/Modules/learnloop/db/stores/router_objective#^module-purpose|purpose]] | `ACTIVE` | 19 | 26 |
| [[Reference/Modules/learnloop/db/stores/router_suggestions|learnloop.db.stores.router_suggestions]] | [[Reference/Modules/learnloop/db/stores/router_suggestions#^module-purpose|purpose]] | `ACTIVE` | 8 | 13 |
| [[Reference/Modules/learnloop/db/stores/section_coverage|learnloop.db.stores.section_coverage]] | [[Reference/Modules/learnloop/db/stores/section_coverage#^module-purpose|purpose]] | `ACTIVE` | 4 | 2 |
| [[Reference/Modules/learnloop/db/stores/session_ownership|learnloop.db.stores.session_ownership]] | [[Reference/Modules/learnloop/db/stores/session_ownership#^module-purpose|purpose]] | `ACTIVE` | 2 | 1 |
| [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] | [[Reference/Modules/learnloop/db/stores/source_block_fts#^module-purpose|purpose]] | `ACTIVE` | 39 | 10 |
| [[Reference/Modules/learnloop/db/stores/source_documents|learnloop.db.stores.source_documents]] | [[Reference/Modules/learnloop/db/stores/source_documents#^module-purpose|purpose]] | `ACTIVE` | 1 | 0 |
| [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] | [[Reference/Modules/learnloop/db/stores/source_service#^module-purpose|purpose]] | `ACTIVE` | 34 | 53 |
| [[Reference/Modules/learnloop/db/stores/span_projection_reads|learnloop.db.stores.span_projection_reads]] | [[Reference/Modules/learnloop/db/stores/span_projection_reads#^module-purpose|purpose]] | `ACTIVE` | 3 | 1 |
| [[Reference/Modules/learnloop/db/stores/span_projections|learnloop.db.stores.span_projections]] | [[Reference/Modules/learnloop/db/stores/span_projections#^module-purpose|purpose]] | `ACTIVE` | 2 | 0 |
| [[Reference/Modules/learnloop/db/stores/task_blueprints|learnloop.db.stores.task_blueprints]] | [[Reference/Modules/learnloop/db/stores/task_blueprints#^module-purpose|purpose]] | `ACTIVE` | 1 | 0 |
| [[Reference/Modules/learnloop/db/stores/voi_forecasts|learnloop.db.stores.voi_forecasts]] | [[Reference/Modules/learnloop/db/stores/voi_forecasts#^module-purpose|purpose]] | `ACTIVE` | 4 | 4 |
| [[Reference/Modules/learnloop/db/stores/workbench|learnloop.db.stores.workbench]] | [[Reference/Modules/learnloop/db/stores/workbench#^module-purpose|purpose]] | `ACTIVE` | 5 | 1 |
| [[Reference/Modules/learnloop/db/stores/workspace_batches|learnloop.db.stores.workspace_batches]] | [[Reference/Modules/learnloop/db/stores/workspace_batches#^module-purpose|purpose]] | `ACTIVE` | 4 | 0 |
| [[Reference/Modules/learnloop/db/stores/write_provenance|learnloop.db.stores.write_provenance]] | [[Reference/Modules/learnloop/db/stores/write_provenance#^module-purpose|purpose]] | `ACTIVE` | 22 | 10 |

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/_package|learnloop]] — 72 static module edges
- [[Reference/Modules/learnloop/db/_package|learnloop.db]] — 38 static module edges
- [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] — 2 static module edges
- [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] — 1 static module edge

### Packages that import this package

- [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] — 56 static module edges
- [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] — 30 static module edges
- [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] — 28 static module edges
- [[Reference/Modules/learnloop/db/_package|learnloop.db]] — 27 static module edges
- [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] — 25 static module edges
- [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] — 23 static module edges
- [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] — 23 static module edges
- [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] — 20 static module edges
- [[Reference/Modules/learnloop/pads/_package|learnloop.pads]] — 19 static module edges
- [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] — 18 static module edges
- [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] — 17 static module edges
- [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] — 16 static module edges
- [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] — 16 static module edges
- [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] — 16 static module edges
- [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] — 14 static module edges
- [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] — 14 static module edges
- [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] — 14 static module edges
- [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] — 12 static module edges
- [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] — 11 static module edges
- [[Reference/Modules/learnloop/_package|learnloop]] — 9 static module edges
- [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] — 9 static module edges
- [[Reference/Modules/learnloop/field/_package|learnloop.field]] — 9 static module edges
- [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] — 9 static module edges
- [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] — 8 static module edges
- [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] — 8 static module edges
- [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] — 7 static module edges
- [[Reference/Modules/learnloop/router/_package|learnloop.router]] — 7 static module edges
- [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] — 6 static module edges
- [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] — 6 static module edges
- [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] — 6 static module edges
- [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] — 6 static module edges
- [[Reference/Modules/learnloop/companion/_package|learnloop.companion]] — 5 static module edges
- [[Reference/Modules/learnloop/desks/_package|learnloop.desks]] — 5 static module edges
- [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] — 5 static module edges
- [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] — 5 static module edges
- [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] — 5 static module edges
- [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] — 4 static module edges
- [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] — 4 static module edges
- [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] — 4 static module edges
- [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] — 4 static module edges
- [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] — 4 static module edges
- [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] — 3 static module edges
- [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] — 3 static module edges
- [[Reference/Modules/learnloop/data_capture/_package|learnloop.data_capture]] — 3 static module edges
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] — 3 static module edges
- [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] — 3 static module edges
- [[Reference/Modules/learnloop/matching/_package|learnloop.matching]] — 3 static module edges
- [[Reference/Modules/learnloop/ops/contamination/_package|learnloop.ops.contamination]] — 3 static module edges
- [[Reference/Modules/learnloop/passage_union/_package|learnloop.passage_union]] — 3 static module edges
- [[Reference/Modules/learnloop/why/_package|learnloop.why]] — 3 static module edges
- [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] — 2 static module edges
- [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] — 1 static module edge
- [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] — 1 static module edge
- [[Reference/Modules/learnloop/recognition/_package|learnloop.recognition]] — 1 static module edge
- [[Reference/Modules/learnloop/remote/_package|learnloop.remote]] — 1 static module edge
- [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] — 1 static module edge

### Dependency neighborhood

This diagram compresses package-level static imports; edge labels are distinct module-to-module import counts.

```mermaid
flowchart LR
    center["learnloop.db.stores"]
    n_learnloop["learnloop"]
    n_learnloop_db["learnloop.db"]
    n_learnloop_source_retrieval["learnloop.source_retrieval"]
    n_learnloop_sidecar_handlers["learnloop_sidecar.handlers"]
    n_learnloop_adaptive_difficulty["learnloop.adaptive_difficulty"]
    n_learnloop_daily_plan["learnloop.daily_plan"]
    n_learnloop_figures["learnloop.figures"]
    n_learnloop_instructional["learnloop.instructional"]
    n_learnloop_diagnosis["learnloop.diagnosis"]
    n_learnloop_pads["learnloop.pads"]
    n_learnloop -->|9| center
    center -->|72| n_learnloop
    n_learnloop_db -->|27| center
    center -->|38| n_learnloop_db
    n_learnloop_source_retrieval -->|56| center
    n_learnloop_sidecar_handlers -->|30| center
    n_learnloop_adaptive_difficulty -->|28| center
    n_learnloop_daily_plan -->|25| center
    n_learnloop_figures -->|23| center
    n_learnloop_instructional -->|23| center
    n_learnloop_diagnosis -->|20| center
    n_learnloop_pads -->|19| center
```

Interpretation: arrow direction is static import direction and the label is the number of distinct module-to-module edges. It shows coupling pressure, not runtime call frequency or ownership permission.

## Workflow entry points

- [[Initialize a Vault]]
- [[Inspect Persistent State]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/db/stores" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
