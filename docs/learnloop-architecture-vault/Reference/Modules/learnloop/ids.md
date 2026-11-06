---
title: "learnloop.ids"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ids.py"
source_paths:
  - "src/learnloop/ids.py"
source_commit: "13c0b95b2512ad934c98f996cf692668b2e74d1b"
source_commit_timestamp: "2026-11-01T19:58:55-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "primitive"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.ids module"
  - "src/learnloop/ids.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/primitive"
  - "package/learnloop"
---

# `learnloop.ids`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps ids behavior inside its owning package, [[Reference/Modules/learnloop/_package|learnloop]]. Its public surface centers on `new_ulid`, `new_ulid_after`, `kebab_case`, `snake_case`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ids.py](../../../../../src/learnloop/ids.py) |
| Source lines | 109 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `primitive` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `13c0b95b2512ad934c98f996cf692668b2e74d1b` |
| Commit timestamp | `2026-11-01T19:58:55-05:00` |

## Public API

- `new_ulid() -> str` ([source](../../../../../src/learnloop/ids.py), line 35) — Generate a ULID that sorts after every ULID this process generated before it.
- `new_ulid_after(floor: str | None) -> str` ([source](../../../../../src/learnloop/ids.py), line 78) — A ULID that sorts after every ULID this process generated before it and after ``floor``, a ULID read from storage (Codex review F2 of followups-nov1c): process-local monotonicity cannot order an id against one a process with a clock running ahead persisted before a restart, so a…
- `kebab_case(value: str) -> str` ([source](../../../../../src/learnloop/ids.py), line 95)
- `snake_case(value: str) -> str` ([source](../../../../../src/learnloop/ids.py), line 108)

### Module constants

- `_CROCKFORD` ([src/learnloop/ids.py](../../../../../src/learnloop/ids.py), line 7)
- `_TIMESTAMP_MASK` ([src/learnloop/ids.py](../../../../../src/learnloop/ids.py), line 18)
- `_RANDOMNESS_BITS` ([src/learnloop/ids.py](../../../../../src/learnloop/ids.py), line 19)
- `_RANDOMNESS_MAX` ([src/learnloop/ids.py](../../../../../src/learnloop/ids.py), line 20)
- `_FLOOR_JITTER_BITS` ([src/learnloop/ids.py](../../../../../src/learnloop/ids.py), line 75)

## Internal implementation anchors

- `_encode_crockford(value: int, length: int) -> str` ([source](../../../../../src/learnloop/ids.py), line 10)
- `_wall_clock_ms() -> int` ([source](../../../../../src/learnloop/ids.py), line 31)
- `_decode_ulid(value: str) -> tuple[int, int] | None` ([source](../../../../../src/learnloop/ids.py), line 58) — A ULID's (timestamp ms, randomness), or None for anything that is not one.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/attempts/calibration_streams|learnloop.attempts.calibration_streams]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/attempts/clarification|learnloop.attempts.clarification]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/attempts/measurement_corrections|learnloop.attempts.measurement_corrections]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/bootstrap|learnloop.bootstrap]] — imports `kebab_case`; statically calls `kebab_case`
- [[Reference/Modules/learnloop/capture/devices|learnloop.capture.devices]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/capture/inbox|learnloop.capture.inbox]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/capture/jobs|learnloop.capture.jobs]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/capture/routing|learnloop.capture.routing]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/cli/gaps|learnloop.cli.gaps]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/cli/project|learnloop.cli.project]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/cli/receipts|learnloop.cli.receipts]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `new_ulid`
- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `new_ulid`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/content/facet_identity/dedupe|learnloop.content.facet_identity.dedupe]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `kebab_case`; statically calls `kebab_case`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/content/pipeline/revision_refresh|learnloop.content.pipeline.revision_refresh]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `kebab_case`, `new_ulid`, `snake_case`; statically calls `kebab_case`, `new_ulid`, `snake_case`
- [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/content/proposals/method_phrasing|learnloop.content.proposals.method_phrasing]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `new_ulid`, `snake_case`; statically calls `new_ulid`, `snake_case`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `new_ulid`, `snake_case`; statically calls `new_ulid`, `snake_case`
- [[Reference/Modules/learnloop/content/proposals/required_method_override|learnloop.content.proposals.required_method_override]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/content/sources/source_library|learnloop.content.sources.source_library]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/content/synthesis/facet_candidates|learnloop.content.synthesis.facet_candidates]] — imports `snake_case`; statically calls `snake_case`
- [[Reference/Modules/learnloop/content/synthesis/graph_nomination|learnloop.content.synthesis.graph_nomination]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `new_ulid`, `snake_case`; statically calls `new_ulid`, `snake_case`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/curriculum/concepts|learnloop.curriculum.concepts]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/curriculum/depth_edge_authoring|learnloop.curriculum.depth_edge_authoring]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/curriculum/depth_transition|learnloop.curriculum.depth_transition]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/curriculum/graph_edit_proposals|learnloop.curriculum.graph_edit_proposals]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/curriculum/subject_registry|learnloop.curriculum.subject_registry]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/data_capture/prefilter|learnloop.data_capture.prefilter]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/db/stores/ad_receipts|learnloop.db.stores.ad_receipts]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/db/stores/ad_serving|learnloop.db.stores.ad_serving]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/db/stores/collection|learnloop.db.stores.collection]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/db/stores/data_capture|learnloop.db.stores.data_capture]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/db/stores/diagnoses|learnloop.db.stores.diagnoses]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/db/stores/followup_serve|learnloop.db.stores.followup_serve]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/db/stores/followup_value|learnloop.db.stores.followup_value]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/db/stores/forecast_receipts|learnloop.db.stores.forecast_receipts]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/db/stores/hypothesis_marks|learnloop.db.stores.hypothesis_marks]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/db/stores/learner_gaps|learnloop.db.stores.learner_gaps]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/db/stores/lessons|learnloop.db.stores.lessons]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/db/stores/recurrence|learnloop.db.stores.recurrence]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/db/stores/router|learnloop.db.stores.router]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/db/stores/router_suggestions|learnloop.db.stores.router_suggestions]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/db/stores/session_ownership|learnloop.db.stores.session_ownership]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/db/stores/voi_forecasts|learnloop.db.stores.voi_forecasts]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/db/stores/write_provenance|learnloop.db.stores.write_provenance]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/diagnosis/error_taxonomy|learnloop.diagnosis.error_taxonomy]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/diagnosis/grading_hardcases|learnloop.diagnosis.grading_hardcases]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/diagnosis/offline_review/planted|learnloop.diagnosis.offline_review.planted]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/diagnosis/probe_remint|learnloop.diagnosis.probe_remint]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/diagnosis/split/pfc_report|learnloop.diagnosis.split.pfc_report]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/goals/exam_seeding|learnloop.goals.exam_seeding]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/goals/exam_session|learnloop.goals.exam_session]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/goals/forecast_ledger|learnloop.goals.forecast_ledger]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/hints/telemetry|learnloop.hints.telemetry]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/intent/control|learnloop.intent.control]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/ops/contamination/report|learnloop.ops.contamination.report]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/ops/embedding_compare|learnloop.ops.embedding_compare]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/ops/family_proposals|learnloop.ops.family_proposals]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/ops/pf_reports|learnloop.ops.pf_reports]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/placement/field_receipts|learnloop.placement.field_receipts]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/practice_index/dossiers|learnloop.practice_index.dossiers]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/projects/capture|learnloop.projects.capture]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/projects/experiment_store|learnloop.projects.experiment_store]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/projects/probes|learnloop.projects.probes]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/reader/reader_intent|learnloop.reader.reader_intent]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/reader/workbench|learnloop.reader.workbench]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/router/decisions|learnloop.router.decisions]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/router/plan_log|learnloop.router.plan_log]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/router_objective/ask_availability|learnloop.router_objective.ask_availability]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/router_objective/assignments|learnloop.router_objective.assignments]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/router_objective/decision_state|learnloop.router_objective.decision_state]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/router_objective/goal_lifecycle|learnloop.router_objective.goal_lifecycle]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/router_objective/sessions|learnloop.router_objective.sessions]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/router_objective/trace|learnloop.router_objective.trace]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/scheduling/controller_ownership|learnloop.scheduling.controller_ownership]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/scheduling/controller_store|learnloop.scheduling.controller_store]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/scheduling/kinship_feature|learnloop.scheduling.kinship_feature]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/scheduling/prequential|learnloop.scheduling.prequential]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/scheduling/shadow_components|learnloop.scheduling.shadow_components]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/sim/diagnostic_validation|learnloop.sim.diagnostic_validation]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/source_retrieval/compare_scope|learnloop.source_retrieval.compare_scope]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/source_retrieval/feedback|learnloop.source_retrieval.feedback]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/source_retrieval/kept_comparisons|learnloop.source_retrieval.kept_comparisons]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/source_retrieval/note_links|learnloop.source_retrieval.note_links]] — imports `new_ulid`, `new_ulid_after`; statically calls `new_ulid`, `new_ulid_after`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/source_retrieval/tutor|learnloop.source_retrieval.tutor]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/teacher/checks|learnloop.teacher.checks]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/teacher/episodes|learnloop.teacher.episodes]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/teacher/probes|learnloop.teacher.probes]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/tui/state|learnloop.tui.state]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `kebab_case`, `snake_case`; statically calls `kebab_case`, `snake_case`
- [[Reference/Modules/learnloop/workbench/bridge|learnloop.workbench.bridge]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/workbench/check|learnloop.workbench.check]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/workbench/compare_methods|learnloop.workbench.compare_methods]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/workbench/passage_draw|learnloop.workbench.passage_draw]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop/workbench/route_example|learnloop.workbench.route_example]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop_sidecar/handlers/chatgpt_plan|learnloop_sidecar.handlers.chatgpt_plan]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop_sidecar/handlers/compare_scope|learnloop_sidecar.handlers.compare_scope]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_cue_discovery|learnloop_sidecar.handlers.reader_cue_discovery]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop_sidecar/handlers/source_service|learnloop_sidecar.handlers.source_service]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop_sidecar/post_attempt_worker|learnloop_sidecar.post_attempt_worker]] — imports `new_ulid`; statically calls `new_ulid`
- [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] — imports `new_ulid`; statically calls `new_ulid`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `secrets`, `threading`, `time`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/calibration_streams|learnloop.attempts.calibration_streams]], [[Reference/Modules/learnloop/attempts/clarification|learnloop.attempts.clarification]], [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]], [[Reference/Modules/learnloop/attempts/measurement_corrections|learnloop.attempts.measurement_corrections]] and 163 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/notes_fixtures.py](../../../../../tests/notes_fixtures.py) — direct import
- [tests/test_ad23_contract.py](../../../../../tests/test_ad23_contract.py) — direct import
  - `test_an_empty_support_draw_of_a_protected_slot_leaves_the_report_cohort`
- [tests/test_capture_desktop.py](../../../../../tests/test_capture_desktop.py) — direct import
  - `test_desktop_photo_preview_rpc_reads_only_the_capture_original`
  - `test_image_capture_kind_matches_desktop_dto`
- [tests/test_capture_domain.py](../../../../../tests/test_capture_domain.py) — direct import
  - `test_capture_concurrent_idempotency`
  - `test_global_idempotency_and_reference_only`
  - `test_image_sanitization_and_raw_fingerprint`
  - `test_inbox_route_atomic_failure_and_orphan_reporting`
  - `test_interrupted_purge_keeps_durable_deletion_intent`
  - `test_old_handled_capture_is_reachable_past_100_newer_and_tombstones`
  - `test_photo_preview_is_resolved_from_the_stored_hash_only`
  - `test_photo_preview_refuses_tampered_hashes_missing_files_and_purge`
  - `test_purge_file_failure_is_visible_and_retryable`
  - `test_purge_retains_canonical_source_original`
  - `test_purge_shared_original_and_retry_never_resurrects`
  - `test_routes_dismiss_and_readonly_status`
- [tests/test_capture_originals_race.py](../../../../../tests/test_capture_originals_race.py) — direct import
  - `test_source_publication_and_capture_purge_share_writer_reservation`
- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../tests/test_causal_repair_sidecar_rpcs.py) — direct import
  - `test_an_open_episode_with_observations_refuses_the_offer_with_a_typed_reason`
- [tests/test_characterization_probe_regrade.py](../../../../../tests/test_characterization_probe_regrade.py) — direct import
  - `test_deferred_regrade_rewrites_summary_but_posterior_does_not_follow`
- [tests/test_characterization_probe_replay.py](../../../../../tests/test_characterization_probe_replay.py) — direct import
- [tests/test_daily_loop_reader_authored_practice.py](../../../../../tests/test_daily_loop_reader_authored_practice.py) — direct import
  - `test_written_question_keeps_returning_after_it_is_answered`
- [tests/test_daily_loop_reentry_break.py](../../../../../tests/test_daily_loop_reentry_break.py) — direct import
- [tests/test_discriminating_search.py](../../../../../tests/test_discriminating_search.py) — direct import
  - `test_an_unverified_import_is_excluded_from_value_intents_but_not_practice`
- [tests/test_evsi_router_composition.py](../../../../../tests/test_evsi_router_composition.py) — direct import
- [tests/test_exam_protection.py](../../../../../tests/test_exam_protection.py) — direct import
  - `test_a_revealed_item_is_never_the_cold_retry`
  - `test_an_exposed_import_never_becomes_an_exam_item`
- [tests/test_exam_protection_review.py](../../../../../tests/test_exam_protection_review.py) — direct import
- [tests/test_figure_offers.py](../../../../../tests/test_figure_offers.py) — direct import
- [tests/test_figures_rw5b_fix_round2.py](../../../../../tests/test_figures_rw5b_fix_round2.py) — direct import
  - `test_a_forked_ask_offers_and_builds_on_the_fork`
- [tests/test_goal_contracts.py](../../../../../tests/test_goal_contracts.py) — direct import
- [tests/test_hint_telemetry.py](../../../../../tests/test_hint_telemetry.py) — direct import
- [tests/test_ids.py](../../../../../tests/test_ids.py) — direct import
  - `test_a_new_millisecond_restarts_from_fresh_randomness`
  - `test_new_ulid_after_ignores_a_floor_that_is_not_a_ulid_or_is_behind`
  - `test_new_ulid_after_sorts_after_a_floor_persisted_by_a_process_whose_clock_ran_ahead`
  - `test_ulid_moves_to_the_next_millisecond_when_randomness_is_exhausted`
  - `test_ulids_minted_in_one_millisecond_sort_in_creation_order`
  - `test_ulids_stay_ordered_when_the_wall_clock_steps_backwards`
- [tests/test_learner_blindness_relax_codex_review.py](../../../../../tests/test_learner_blindness_relax_codex_review.py) — direct import
- [tests/test_lp_claim_fixes_rereview.py](../../../../../tests/test_lp_claim_fixes_rereview.py) — direct import
  - `test_f7_an_attempt_reserved_before_a_gap_and_graded_after_it_replays_after_it`
  - `test_f7_the_claim_records_how_many_of_its_los_attempts_it_was_applied_after`
- [tests/test_misconception_registry.py](../../../../../tests/test_misconception_registry.py) — direct import
  - `test_discriminating_item_has_higher_eig`
- [tests/test_mobile_capture.py](../../../../../tests/test_mobile_capture.py) — direct import
- [tests/test_mobile_host_auth.py](../../../../../tests/test_mobile_host_auth.py) — direct import
  - `test_offline_backlog_flushes_without_per_device_throttle`
- [tests/test_mobile_jobs.py](../../../../../tests/test_mobile_jobs.py) — direct import
  - `test_a_job_of_this_run_is_never_recovered_by_itself`
- [tests/test_mobile_phone_contract.py](../../../../../tests/test_mobile_phone_contract.py) — direct import
- [tests/test_model_grade_lane.py](../../../../../tests/test_model_grade_lane.py) — direct import
- [tests/test_notes_linked.py](../../../../../tests/test_notes_linked.py) — direct import
  - `test_r6_review_f2_a_clock_correction_and_restart_never_blocks_later_refreshes`
- [tests/test_p2_acceptance.py](../../../../../tests/test_p2_acceptance.py) — direct import
- [tests/test_p2_leakage_suite.py](../../../../../tests/test_p2_leakage_suite.py) — direct import
- [tests/test_pfc_unassessed_readers.py](../../../../../tests/test_pfc_unassessed_readers.py) — direct import
- [tests/test_probe_audit.py](../../../../../tests/test_probe_audit.py) — direct import
- [tests/test_probe_block_end.py](../../../../../tests/test_probe_block_end.py) — direct import
  - `test_ordinary_attempt_outside_block_still_normalizes`
- [tests/test_probe_dialogue.py](../../../../../tests/test_probe_dialogue.py) — direct import
- [tests/test_probe_episodes.py](../../../../../tests/test_probe_episodes.py) — direct import
  - `test_presentation_activity_disqualification_precedes_live_projection`
  - `test_stop_and_teach_ends_measurement_and_segments_evidence`
- [tests/test_probe_longform_families.py](../../../../../tests/test_probe_longform_families.py) — direct import
  - `test_longform_observation_records_trace_and_bounded_mass`
- [tests/test_probe_orchestration_remainder.py](../../../../../tests/test_probe_orchestration_remainder.py) — direct import
  - `test_answer_confidence_out_of_range_is_rejected`
- [tests/test_probe_policy.py](../../../../../tests/test_probe_policy.py) — direct import
- [tests/test_probe_robust_cutover.py](../../../../../tests/test_probe_robust_cutover.py) — direct import
- [tests/test_project_blindness.py](../../../../../tests/test_project_blindness.py) — direct import
  - `test_rendered_prompts_carry_no_provenance_declaration_or_closed_book_origin`
- [tests/test_project_report.py](../../../../../tests/test_project_report.py) — direct import
- [tests/test_reader_ca1_as_printed.py](../../../../../tests/test_reader_ca1_as_printed.py) — direct import
- [tests/test_reader_recap_review_r2.py](../../../../../tests/test_reader_recap_review_r2.py) — direct import
- [tests/test_reader_tutor_retrieval.py](../../../../../tests/test_reader_tutor_retrieval.py) — direct import
- [tests/test_reread_safety.py](../../../../../tests/test_reread_safety.py) — direct import
- [tests/test_ro1_availability.py](../../../../../tests/test_ro1_availability.py) — direct import
  - `test_the_backfill_reads_an_imported_exam_rows_ulid_time_and_leaves_bad_ids_null`
- [tests/test_router_r2a_landing.py](../../../../../tests/test_router_r2a_landing.py) — direct import
- [tests/test_sidecar_trace_and_clarification.py](../../../../../tests/test_sidecar_trace_and_clarification.py) — direct import
- [tests/test_source_first_needs.py](../../../../../tests/test_source_first_needs.py) — direct import
  - `test_the_follow_up_rechecks_independence_before_serving_a_need_import`
- [tests/test_teacher_te2_landing_r1.py](../../../../../tests/test_teacher_te2_landing_r1.py) — direct import
  - `test_fg1s_presentation_path_stamps_the_submissions_identity_and_its_regrade_the_replacements`
- [tests/test_voi_merge_composition.py](../../../../../tests/test_voi_merge_composition.py) — direct import
  - `test_the_report_scores_a_project_probe_through_r1s_plan_block`
- [tests/test_voi_stopping.py](../../../../../tests/test_voi_stopping.py) — direct import
- [tests/voi_restore_scenarios.py](../../../../../tests/voi_restore_scenarios.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains ids within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ids.py](../../../../../src/learnloop/ids.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
