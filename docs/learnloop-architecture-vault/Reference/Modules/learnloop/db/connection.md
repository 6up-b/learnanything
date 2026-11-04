---
title: "learnloop.db.connection"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/connection.py"
source_paths:
  - "src/learnloop/db/connection.py"
source_commit: "07ac808ab30e8970f57c1905e3d2364ed2ccb404"
source_commit_timestamp: "2026-10-20T20:49:36-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.connection module"
  - "src/learnloop/db/connection.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db"
---

# `learnloop.db.connection`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/_package|learnloop.db]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps connection behavior inside its owning package, [[Reference/Modules/learnloop/db/_package|learnloop.db]]. Its public surface centers on `UnsupportedSQLiteVersion`, `require_supported_sqlite`, `linked_sqlite_version`, `wal_reset_bug_fixed`, `wal_unavailable_reason`, `connect`.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/connection.py](../../../../../../src/learnloop/db/connection.py) |
| Source lines | 148 |
| Owning package | [[Reference/Modules/learnloop/db/_package|learnloop.db]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `07ac808ab30e8970f57c1905e3d2364ed2ccb404` |
| Commit timestamp | `2026-10-20T20:49:36-04:00` |

## Public API

- `class UnsupportedSQLiteVersion(RuntimeError)` ([source](../../../../../../src/learnloop/db/connection.py), line 33) — The SQLite library linked into Python is too old for WAL vaults.
- `require_supported_sqlite() -> None` ([source](../../../../../../src/learnloop/db/connection.py), line 38) — Fail once, clearly, when the runtime SQLite cannot open WAL vaults.
- `linked_sqlite_version() -> tuple[int, int, int]` ([source](../../../../../../src/learnloop/db/connection.py), line 49)
- `wal_reset_bug_fixed(version: tuple[int, int, int] | None=None) -> bool` ([source](../../../../../../src/learnloop/db/connection.py), line 53) — Whether ``version`` (default: the linked SQLite) has the WAL-reset fix.
- `wal_unavailable_reason(version: tuple[int, int, int] | None=None) -> str | None` ([source](../../../../../../src/learnloop/db/connection.py), line 66) — Why WAL must not be enabled with ``version``, or ``None`` when it may be.
- `connect(sqlite_path: Path, *, read_only: bool=False) -> sqlite3.Connection` ([source](../../../../../../src/learnloop/db/connection.py), line 82) — Open a configured SQLite connection.

### Module constants

- `MINIMUM_SQLITE_VERSION` ([src/learnloop/db/connection.py](../../../../../../src/learnloop/db/connection.py), line 11)
- `BUSY_TIMEOUT_MS` ([src/learnloop/db/connection.py](../../../../../../src/learnloop/db/connection.py), line 12)
- `WAL_RESET_FIX_RELEASES` ([src/learnloop/db/connection.py](../../../../../../src/learnloop/db/connection.py), line 20)
- `WAL_RESET_FIXED_VERSIONS_TEXT` ([src/learnloop/db/connection.py](../../../../../../src/learnloop/db/connection.py), line 25)
- `WAL_RESET_ADVISORY_URL` ([src/learnloop/db/connection.py](../../../../../../src/learnloop/db/connection.py), line 26)
- `_READ_ONLY_OPEN_FAILURES` ([src/learnloop/db/connection.py](../../../../../../src/learnloop/db/connection.py), line 30)

## Internal implementation anchors

- `_configure(connection: sqlite3.Connection) -> None` ([source](../../../../../../src/learnloop/db/connection.py), line 113)
- `_open_read_only(sqlite_path: Path) -> sqlite3.Connection` ([source](../../../../../../src/learnloop/db/connection.py), line 119) — Open with ``mode=ro`` and surface a WAL open failure here.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/adaptive_difficulty/background|learnloop.adaptive_difficulty.background]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/adaptive_difficulty/data_check|learnloop.adaptive_difficulty.data_check]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/adaptive_difficulty/reading|learnloop.adaptive_difficulty.reading]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness|learnloop.adaptive_difficulty.relatedness]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness_jobs|learnloop.adaptive_difficulty.relatedness_jobs]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/adaptive_difficulty/serve_inputs|learnloop.adaptive_difficulty.serve_inputs]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/cli/ad|learnloop.cli.ad]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/cli/data_capture|learnloop.cli.data_capture]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/cli/decider|learnloop.cli.decider]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/cli/gaps|learnloop.cli.gaps]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/cli/placement|learnloop.cli.placement]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/cli/plan|learnloop.cli.plan]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/cli/practice_index|learnloop.cli.practice_index]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/cli/success_head|learnloop.cli.success_head]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/content/proposals/method_phrasing|learnloop.content.proposals.method_phrasing]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/content/proposals/method_statement_judge|learnloop.content.proposals.method_statement_judge]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/content/sources/exercise_statements|learnloop.content.sources.exercise_statements]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/content/sources/span_aliases|learnloop.content.sources.span_aliases]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/content/synthesis/graph_nomination|learnloop.content.synthesis.graph_nomination]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/daily_plan/router_retrieval|learnloop.daily_plan.router_retrieval]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/db/checkpoint|learnloop.db.checkpoint]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/db/copies|learnloop.db.copies]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/db/migrate|learnloop.db.migrate]] — imports `connect`, `wal_unavailable_reason`; statically calls `connect`, `wal_unavailable_reason`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/db/scopes|learnloop.db.scopes]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/db/stores/embedding_vectors|learnloop.db.stores.embedding_vectors]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/db/stores/model_calls|learnloop.db.stores.model_calls]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/diagnosis/offline_review/links|learnloop.diagnosis.offline_review.links]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/diagnosis/offline_review/report|learnloop.diagnosis.offline_review.report]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/diagnosis/offline_review/spot_check|learnloop.diagnosis.offline_review.spot_check]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/diagnosis/recurrence/backlog|learnloop.diagnosis.recurrence.backlog]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/diagnosis/split/embeddings|learnloop.diagnosis.split.embeddings]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/diagnosis/split/figure_trace|learnloop.diagnosis.split.figure_trace]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/diagnosis/split/prior_analysis|learnloop.diagnosis.split.prior_analysis]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/diagnosis/split/retrieval|learnloop.diagnosis.split.retrieval]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/diagnosis/split/workbench_trace|learnloop.diagnosis.split.workbench_trace]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/candidates|learnloop.diagnosis.text_gaps.candidates]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/report|learnloop.diagnosis.text_gaps.report]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/sources|learnloop.diagnosis.text_gaps.sources]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/tier1|learnloop.diagnosis.text_gaps.tier1]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/evsi_calibration/forecast_report|learnloop.evsi_calibration.forecast_report]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/evsi_calibration/live_report|learnloop.evsi_calibration.live_report]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/bank|learnloop.experiments.contextual_embeddings.bank]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/runner|learnloop.experiments.contextual_embeddings.runner]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/figures/help|learnloop.figures.help]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/figures/learner_state|learnloop.figures.learner_state]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/figures/prefetch_ledger|learnloop.figures.prefetch_ledger]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/figures/rich|learnloop.figures.rich]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/figures/source_check|learnloop.figures.source_check]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/hints/discriminating|learnloop.hints.discriminating]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/hints/map_report|learnloop.hints.map_report]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/hints/map_seeds|learnloop.hints.map_seeds]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/hints/outcome|learnloop.hints.outcome]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/hints/report|learnloop.hints.report]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/hints/report_workbench|learnloop.hints.report_workbench]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/hints/state|learnloop.hints.state]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/instructional/discriminating|learnloop.instructional.discriminating]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/instructional/exercises|learnloop.instructional.exercises]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/instructional/exposure|learnloop.instructional.exposure]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/instructional/policy|learnloop.instructional.policy]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/instructional/screen|learnloop.instructional.screen]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/instructional/valuation|learnloop.instructional.valuation]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/local_embeddings/cache|learnloop.local_embeddings.cache]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/migration_coordinator|learnloop.migration_coordinator]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/ops/contamination/detectors|learnloop.ops.contamination.detectors]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/ops/contamination/judge|learnloop.ops.contamination.judge]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `WAL_RESET_ADVISORY_URL`, `WAL_RESET_FIXED_VERSIONS_TEXT`, `linked_sqlite_version`, `wal_unavailable_reason`; statically calls `linked_sqlite_version`, `wal_unavailable_reason`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/ops/family_proposals|learnloop.ops.family_proposals]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/ops/graph_nomination_report|learnloop.ops.graph_nomination_report]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/practice_index/dossiers|learnloop.practice_index.dossiers]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/practice_index/listwise|learnloop.practice_index.listwise]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/practice_index/query_vectors|learnloop.practice_index.query_vectors]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/practice_index/usage|learnloop.practice_index.usage]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/projects/experiment_store|learnloop.projects.experiment_store]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/reader/reader_report|learnloop.reader.reader_report]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/reader/source_roles|learnloop.reader.source_roles]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/reader_learner_state|learnloop.reader_learner_state]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/scheduling/intent/followup_gate|learnloop.scheduling.intent.followup_gate]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/scheduling/serving_exclusions|learnloop.scheduling.serving_exclusions]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/b4|learnloop.source_retrieval.b4]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/bench|learnloop.source_retrieval.bench]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/dense|learnloop.source_retrieval.dense]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/feedback|learnloop.source_retrieval.feedback]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/recipes|learnloop.source_retrieval.recipes]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/role_labeller|learnloop.source_retrieval.role_labeller]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/spaces|learnloop.source_retrieval.spaces]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/student_encoder|learnloop.source_retrieval.student_encoder]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/suggest|learnloop.source_retrieval.suggest]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/timing|learnloop.source_retrieval.timing]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/tutor|learnloop.source_retrieval.tutor]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/vault_notes|learnloop.source_retrieval.vault_notes]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/source_retrieval/windows|learnloop.source_retrieval.windows]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/substrate/data_quality|learnloop.substrate.data_quality]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/substrate/dataset|learnloop.substrate.dataset]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/substrate/model_usage|learnloop.substrate.model_usage]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/teacher/visuals|learnloop.teacher.visuals]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/tutor/context_delivery|learnloop.tutor.context_delivery]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/vault/embedding_recipes|learnloop.vault.embedding_recipes]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/workbench/bridge|learnloop.workbench.bridge]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/workbench/check|learnloop.workbench.check]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/workbench/compare_methods|learnloop.workbench.compare_methods]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/workbench/help_outcomes|learnloop.workbench.help_outcomes]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/workbench/ladder|learnloop.workbench.ladder]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop/workbench/route_example|learnloop.workbench.route_example]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop_sidecar/handlers/adaptive_difficulty|learnloop_sidecar.handlers.adaptive_difficulty]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop_sidecar/handlers/figures|learnloop_sidecar.handlers.figures]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop_sidecar/handlers/item_text_neighbors|learnloop_sidecar.handlers.item_text_neighbors]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop_sidecar/handlers/learner_gaps|learnloop_sidecar.handlers.learner_gaps]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop_sidecar/handlers/library_exercises|learnloop_sidecar.handlers.library_exercises]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop_sidecar/handlers/source_service|learnloop_sidecar.handlers.source_service]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench|learnloop_sidecar.handlers.workbench]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `connect`; statically calls `connect`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]] — imports `connect`; statically calls `connect`

### Repository tooling consumers

- [scripts/benchmark_sqlite_concurrency.py](../../../../../../scripts/benchmark_sqlite_concurrency.py); calls `connect`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/scopes|learnloop.db.scopes]] — imports `apply_connection_hook`, `guarded_connection`; calls `apply_connection_hook`, `guarded_connection`

### Platform and third-party dependencies

- Standard library: `__future__`, `functools`, `pathlib`, `sqlite3`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]], [[Reference/Modules/learnloop/adaptive_difficulty/background|learnloop.adaptive_difficulty.background]], [[Reference/Modules/learnloop/adaptive_difficulty/data_check|learnloop.adaptive_difficulty.data_check]], [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]], [[Reference/Modules/learnloop/adaptive_difficulty/generation|learnloop.adaptive_difficulty.generation]] and 170 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad_ingest_fakes.py](../../../../../../tests/ad_ingest_fakes.py) — direct import
- [tests/approach_map_fakes.py](../../../../../../tests/approach_map_fakes.py) — direct import
- [tests/conftest.py](../../../../../../tests/conftest.py) — direct import
- [tests/helpers.py](../../../../../../tests/helpers.py) — direct import
- [tests/hint_fakes.py](../../../../../../tests/hint_fakes.py) — direct import
- [tests/query_student_fakes.py](../../../../../../tests/query_student_fakes.py) — direct import
- [tests/test_activity_backfill.py](../../../../../../tests/test_activity_backfill.py) — direct import
  - `test_backfill_logs_attempt_duration_interaction_events`
  - `test_backfill_marks_unverifiable_for_missing_item`
  - `test_backfill_populates_substrate_from_fixture`
  - `test_backfill_render_once_per_shared_surface`
  - `test_diagnostic_probe_attempts_reuse_shared_surface_hash`
- [tests/test_activity_substrate.py](../../../../../../tests/test_activity_substrate.py) — direct import
  - `test_ensure_activity_family_and_card_are_race_safe`
  - `test_feedback_before_response_yields_no_terminal_credit`
  - `test_migration_created_substrate_tables_and_partial_indices`
  - `test_retire_with_reason_records_and_preserves_evidence`
- [tests/test_ad1_migration.py](../../../../../../tests/test_ad1_migration.py) — direct import
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — direct import
  - `test_a_dose_draw_at_a_protected_origin_is_a_draw_never_made`
  - `test_a_late_uptake_callback_writes_nothing_when_ad_cannot_record_it`
  - `test_a_protected_receipt_occupies_no_daily_cap_slot`
  - `test_a_run_whose_quoted_revision_was_replaced_then_protected_is_not_used`
  - `test_a_saved_run_proposed_before_its_subject_was_protected_is_not_used`
  - `test_a_stale_run_never_answers_for_a_re_proposal`
  - `test_a_tutor_exchange_on_a_protected_canonical_note_enters_no_prediction`
  - `test_a_tutor_exchange_whose_recorded_context_quotes_a_protected_span_enters_no_prediction`
  - `test_an_empty_support_draw_of_a_protected_slot_leaves_the_report_cohort`
  - `test_feedback_dwell_skips_a_serve_withheld_with_its_presentation`
  - `test_the_sidecar_uptake_callback_answers_a_no_op_with_ad_off`
  - `test_with_no_protection_a_frozen_dose_on_an_absent_facet_stands`
  - `test_withheld_dose_offers_neither_spend_the_budget_nor_count_as_taken`
- [tests/test_ad23_fix_r5.py](../../../../../../tests/test_ad23_fix_r5.py) — direct import
  - `test_a_generation_jobs_commission_expires_seven_days_after_the_job_finished`
  - `test_an_item_that_lands_after_expiry_gets_a_marked_receipt_and_a_later_draw_owns_later_items`
  - `test_the_report_forecasts_with_the_configured_coupling`
- [tests/test_ad23_fix_r6.py](../../../../../../tests/test_ad23_fix_r6.py) — direct import
  - `test_draws_of_one_second_are_ordered_by_insertion`
  - `test_one_owner_at_equal_timestamps_and_the_first_attribution_is_final`
- [tests/test_ad23_fix_r7.py](../../../../../../tests/test_ad23_fix_r7.py) — direct import
  - `test_features_match_reads_the_audited_features_the_receipt_records`
- [tests/test_ad23_fix_r8.py](../../../../../../tests/test_ad23_fix_r8.py) — direct import
  - `test_a_reading_receipt_whose_source_is_held_out_now_is_not_replayed`
  - `test_practice_minutes_come_from_the_visible_practice_cohort`
  - `test_report_sensitivity_never_re_forecasts_a_withheld_item`
  - `test_the_dose_arm_never_offers_or_returns_a_held_out_question`
  - `test_the_dose_moderator_window_closes_only_at_a_visible_graded_attempt`
  - `test_with_the_predicate_unavailable_the_report_discloses_zero_observations`
- [tests/test_ad23_fix_r9.py](../../../../../../tests/test_ad23_fix_r9.py) — direct import
  - `test_an_attempt_on_a_held_out_answered_revision_is_filtered_at_the_source`
- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — direct import
  - `test_a_commission_queued_before_models_go_off_waits_and_resumes`
  - `test_a_historical_regrade_reads_its_current_epoch_not_a_surviving_obsolete_criterion`
  - `test_density_lowerings_join_offers_to_their_visits`
  - `test_repeated_reports_fire_the_readiness_flag_through_build`
- [tests/test_ad23_migration.py](../../../../../../tests/test_ad23_migration.py) — direct import
- [tests/test_ad23_owner_decisions.py](../../../../../../tests/test_ad23_owner_decisions.py) — direct import
  - `test_a_commission_whose_item_is_in_review_stays_open_until_the_decision`
  - `test_ad_reads_history_through_its_own_fallback_and_field_keeps_its_own`
- [tests/test_ad2_model.py](../../../../../../tests/test_ad2_model.py) — direct import
  - `test_pre_exposed_presentation_excluded_from_update_and_scoring`
  - `test_self_report_and_held_grades_excluded`
  - `test_warmth_uses_only_pre_serve_exposures`
- [tests/test_ad2_serving.py](../../../../../../tests/test_ad2_serving.py) — direct import
  - `test_commission_result_appended_never_mutates_selection`
  - `test_why_this_item_names_the_draw_that_chose_it`
- [tests/test_ad3_dose_arm.py](../../../../../../tests/test_ad3_dose_arm.py) — direct import
  - `test_uptake_appends_rows_and_never_changes_the_draw`
- [tests/test_ad3_monitoring.py](../../../../../../tests/test_ad3_monitoring.py) — direct import
  - `test_monitoring_applies_field_rule_as_monitor_never_gate`
  - `test_no_flag_edits_the_vault_config`
- [tests/test_ad3_reading.py](../../../../../../tests/test_ad3_reading.py) — direct import
  - `test_a_question_counts_once_and_no_verdict_reaches_evidence`
  - `test_reading_raises_prediction_never_evidence`
  - `test_reading_self_check_switch_restores_d20_and_is_moot_without_reading`
- [tests/test_ad3_relatedness.py](../../../../../../tests/test_ad3_relatedness.py) — direct import
  - `test_each_loading_and_coupling_is_one_ledger_row_and_invalid_outputs_drop`
  - `test_unchanged_input_makes_no_call_and_a_change_reproposes_only_what_it_touches`
- [tests/test_ad3_subject_view.py](../../../../../../tests/test_ad3_subject_view.py) — direct import
  - `test_coupling_is_prediction_only`
- [tests/test_ad_epoch.py](../../../../../../tests/test_ad_epoch.py) — direct import
  - `test_a_commission_drawn_under_other_protection_is_not_open`
  - `test_a_protected_pending_proposal_never_holds_a_commission_open`
  - `test_a_reading_receipt_recorded_under_other_protection_is_mapped_again`
  - `test_frozen_serve_signals_trained_on_a_newly_protected_answer_are_not_replayed`
- [tests/test_ad_guard.py](../../../../../../tests/test_ad_guard.py) — direct import
  - `test_a_denied_dose_response_rolls_the_draw_back`
  - `test_an_exam_reserved_items_contract_is_read_only_through_the_rules`
- [tests/test_ad_guard_offer_receipts.py](../../../../../../tests/test_ad_guard_offer_receipts.py) — direct import
  - `test_the_serving_snapshot_and_the_report_run_with_zero_denials`
  - `test_the_view_labels_the_pick_as_field_does_outside_ad`
- [tests/test_ad_guard_reachable_reads.py](../../../../../../tests/test_ad_guard_reachable_reads.py) — direct import
  - `test_every_serving_branch_runs_with_zero_denials_and_fields_labels`
- [tests/test_ad_projection.py](../../../../../../tests/test_ad_projection.py) — direct import
  - `test_every_protected_table_reads_as_in_the_absent_copy`
- [tests/test_ad_protected_readings.py](../../../../../../tests/test_ad_protected_readings.py) — direct import
  - `test_a_clean_reading_is_read_as_the_reader_and_the_incumbent_read_it`
  - `test_a_practice_interaction_event_is_not_a_reading_event`
  - `test_a_reader_question_anchored_by_note_on_a_mixed_reading_is_withheld`
  - `test_attempt_evidence_from_a_visible_span_of_a_mixed_reading_is_unchanged`
  - `test_marking_and_release_flip_the_epoch_and_the_reading_with_it`
  - `test_probe_candidates_are_taken_in_reading_order_not_span_id_order`
- [tests/test_ad_protected_tables.py](../../../../../../tests/test_ad_protected_tables.py) — direct import
  - `test_every_column_of_every_readable_table_is_metadata_or_content`
- [tests/test_agent_run_tokens.py](../../../../../../tests/test_agent_run_tokens.py) — direct import
  - `test_agent_run_token_columns_exist_and_default_to_zero`
- [tests/test_answer_signal_arms.py](../../../../../../tests/test_answer_signal_arms.py) — direct import
  - `test_the_loader_reads_the_tap_and_the_graders_tone_reading`
- [tests/test_approach_map_boundaries.py](../../../../../../tests/test_approach_map_boundaries.py) — direct import
  - `test_grading_prompts_never_carry_or_read_a_stored_map`
- [tests/test_approach_map_replay.py](../../../../../../tests/test_approach_map_replay.py) — direct import
  - `test_the_read_refusal_would_catch_a_replay_that_read_maps`
- [tests/test_approach_maps.py](../../../../../../tests/test_approach_maps.py) — direct import
  - `test_a_metered_build_under_the_cap_reserves_and_settles_its_spend`
  - `test_a_revised_item_or_changed_seeds_gets_a_new_row_never_an_update`
  - `test_f3_the_durable_claim_keeps_a_second_worker_from_paying`
  - `test_f4_a_seeded_but_unrouted_attempt_is_merged_later`
  - `test_f5_an_inherited_rubric_change_is_a_new_revision`
  - `test_help_assists_map_id_is_a_soft_reference_checked_in_code`
- [tests/test_approach_maps_schema.py](../../../../../../tests/test_approach_maps_schema.py) — direct import
  - `test_the_store_refuses_unknown_columns`
- [tests/test_assessment_contracts.py](../../../../../../tests/test_assessment_contracts.py) — direct import
  - `test_observation_id_attaches_once`
- [tests/test_assessment_enforcement.py](../../../../../../tests/test_assessment_enforcement.py) — direct import
  - `test_failed_with_feedback_appends_practice_successor_proposal`
  - `test_render_marks_unrepresentative_when_head_support_moved`
- [tests/test_assumed_known.py](../../../../../../tests/test_assumed_known.py) — direct import
- [tests/test_attempt_content_state_race.py](../../../../../../tests/test_attempt_content_state_race.py) — direct import
  - `test_an_attempt_on_an_item_with_no_row_inserts_the_whole_row`
- [tests/test_chatgpt_plan_landing.py](../../../../../../tests/test_chatgpt_plan_landing.py) — direct import
  - `test_a_snapshot_diagnosis_on_the_plan_records_what_it_served_with_its_row_and_forecasts`
- [tests/test_collection_dataset.py](../../../../../../tests/test_collection_dataset.py) — direct import
  - `test_export_gives_up_on_a_source_locked_after_its_probe_and_removes_the_export`
  - `test_production_lane_and_live_backup_preserve_committed_state`
  - `test_scored_item_text_is_snapshotted_once_per_revision_and_exported`
  - `test_selection_decision_features_reference_the_item_and_stay_compact`
- [tests/test_compare_methods.py](../../../../../../tests/test_compare_methods.py) — direct import
- [tests/test_compare_sources_keep.py](../../../../../../tests/test_compare_sources_keep.py) — direct import
  - `test_a_comparison_holding_exam_material_is_refused`
- [tests/test_coordinated_migrations.py](../../../../../../tests/test_coordinated_migrations.py) — direct import
- [tests/test_daily_plan_owner_decisions.py](../../../../../../tests/test_daily_plan_owner_decisions.py) — direct import
  - `test_migration_180_widens_the_field_serving_origins_and_keeps_its_rows`
- [tests/test_data_capture_landing_review.py](../../../../../../tests/test_data_capture_landing_review.py) — direct import
  - `test_f1_the_read_is_read_only_under_a_read_only_repository`
- [tests/test_data_capture_phone.py](../../../../../../tests/test_data_capture_phone.py) — direct import
  - `test_answered_on_the_phone_a_check_measures_its_objective`
- [tests/test_diagnosis_input_provenance.py](../../../../../../tests/test_diagnosis_input_provenance.py) — direct import
  - `test_f5_replay_never_reads_the_switch_or_the_records`
- [tests/test_diagnosis_input_provenance_landing.py](../../../../../../tests/test_diagnosis_input_provenance_landing.py) — direct import
  - `test_q14_on_a_vault_the_coordinator_upgrades_the_receipt_commits_with_the_grade`
- [tests/test_diagnosis_replay.py](../../../../../../tests/test_diagnosis_replay.py) — direct import
  - `test_joint_reads_are_untouched_by_the_overlay`
- [tests/test_dl2_rw4b_keyed_pick_check.py](../../../../../../tests/test_dl2_rw4b_keyed_pick_check.py) — direct import
- [tests/test_e0_corpus.py](../../../../../../tests/test_e0_corpus.py) — direct import
  - `test_prepare_copies_uses_the_backup_api_under_fixtures_local_only`
- [tests/test_e0_relabel_round.py](../../../../../../tests/test_e0_relabel_round.py) — direct import
- [tests/test_e0_review_round1.py](../../../../../../tests/test_e0_review_round1.py) — direct import
  - `test_f1_service_copy_preparation_never_sends_protected_text`
- [tests/test_embedding_store.py](../../../../../../tests/test_embedding_store.py) — direct import
- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — direct import
  - `test_a_pick_of_an_item_reserved_since_its_proposal_is_refused_before_anything_is_recorded`
  - `test_a_reader_question_about_held_out_material_is_refused_before_anything_is_sent`
  - `test_the_daily_envelope_stamps_its_rows_with_the_injected_clock`
- [tests/test_exam_protection_landing.py](../../../../../../tests/test_exam_protection_landing.py) — direct import
  - `test_the_reading_step_never_offers_a_held_out_section_of_a_book_in_no_source_set`
- [tests/test_exam_protection_review.py](../../../../../../tests/test_exam_protection_review.py) — direct import
  - `test_an_exam_item_exposed_after_its_reservation_is_withdrawn_before_the_exam_starts`
  - `test_replay_never_reads_the_switch`
- [tests/test_exam_seeding.py](../../../../../../tests/test_exam_seeding.py) — direct import
  - `test_migration_018_allows_exam_evidence_on_existing_db`
- [tests/test_exercise_arm.py](../../../../../../tests/test_exercise_arm.py) — direct import
  - `test_an_exercise_keeps_its_setup_and_its_unnumbered_lines`
  - `test_page_furniture_and_empty_blocks_never_form_an_exercise`
- [tests/test_facet_rewords_migration.py](../../../../../../tests/test_facet_rewords_migration.py) — direct import
  - `test_migration_196_upgrades_a_195_vault_keeping_actions_and_the_forecast_log`
- [tests/test_field_workbench_signals.py](../../../../../../tests/test_field_workbench_signals.py) — direct import
  - `test_an_attempts_rows_and_hint_outcome_are_unchanged_by_its_workbench_rows`
  - `test_rereview_f3_the_subject_is_the_one_frozen_with_the_contract`
  - `test_review_f1_a_worked_example_after_real_work_is_not_early_help`
  - `test_the_rebuild_never_reads_the_workbench_tables`
- [tests/test_followup_fg1c_codex_review.py](../../../../../../tests/test_followup_fg1c_codex_review.py) — direct import
  - `test_f4_a_later_success_disagrees_with_a_named_gap_and_the_plain_report_says_what_came_after`
- [tests/test_followups_nov2_help_fold.py](../../../../../../tests/test_followups_nov2_help_fold.py) — direct import
  - `test_every_help_kind_the_keyed_fold_counts_is_exactly_what_the_attempt_attaches`
  - `test_the_keyless_window_still_reads_its_own_session_only`
- [tests/test_forecast_receipts.py](../../../../../../tests/test_forecast_receipts.py) — direct import
  - `test_a_completed_diagnosis_writes_its_forecast_in_its_own_transaction`
  - `test_a_scheduled_cold_check_records_its_repair_forecast_and_resolves_on_its_task`
  - `test_receipts_are_append_only`
  - `test_replay_neither_reads_nor_writes_forecast_receipts`
  - `test_the_report_reads_a_vault_without_receipts_as_empty`
- [tests/test_forecast_receipts_landing.py](../../../../../../tests/test_forecast_receipts_landing.py) — direct import
  - `test_a_failed_forecast_receipt_keeps_the_diagnosis_and_its_provenance_record`
  - `test_the_provenance_record_the_diagnosis_and_its_forecasts_commit_as_one_transaction`
- [tests/test_goal_contracts.py](../../../../../../tests/test_goal_contracts.py) — direct import
- [tests/test_grade_resolution_pipeline.py](../../../../../../tests/test_grade_resolution_pipeline.py) — direct import
  - `test_backfill_converts_probe_presentations_idempotently`
  - `test_insert_calibration_model_is_content_addressed_no_duplicate`
  - `test_migration_066_created_tables_and_indices`
  - `test_probe_dual_write_helper_records_diagnostic_grade`
- [tests/test_grading_cli.py](../../../../../../tests/test_grading_cli.py) — direct import
  - `test_retire_surface_from_cli_preserves_evidence_and_logs_reason`
- [tests/test_grading_hardcases.py](../../../../../../tests/test_grading_hardcases.py) — direct import
- [tests/test_graph_nomination.py](../../../../../../tests/test_graph_nomination.py) — direct import
  - `test_backfill_reuses_a_vector_paid_at_ingest_under_another_id`
  - `test_ranking_matches_phase_1_retrieval`
- [tests/test_held_grade_evidence.py](../../../../../../tests/test_held_grade_evidence.py) — direct import
  - `test_f6_the_dataset_exports_no_held_score_as_observed`
  - `test_review_f1_a_regrade_into_a_hold_supersedes_the_assessed_grade_it_replaces`
- [tests/test_help_assists_schema.py](../../../../../../tests/test_help_assists_schema.py) — direct import
  - `test_the_ledger_keeps_rows_and_an_attached_attempt`
  - `test_the_store_attach_matches_the_submission_key_only`
  - `test_the_store_refuses_unknown_columns`
  - `test_the_workbench_lifecycle_binds_each_deferred_column_once`
- [tests/test_help_outcomes.py](../../../../../../tests/test_help_outcomes.py) — direct import
  - `test_f10_an_s5_record_naming_a_passage_is_its_outcome_and_is_not_counted_again`
  - `test_f3_hints_the_learner_picked_stay_in_the_history_passage_picks_do_not_count_twice`
  - `test_f5_a_comparison_gets_no_credit_for_an_attempt_before_it_was_opened`
  - `test_f6_a_hold_released_after_as_of_still_held_then`
  - `test_s5_absent_reads_as_absent`
- [tests/test_hint_feedback_widening.py](../../../../../../tests/test_hint_feedback_widening.py) — direct import
- [tests/test_hint_h2a_review_round3.py](../../../../../../tests/test_hint_h2a_review_round3.py) — direct import
  - `test_w1_the_fence_and_the_keyless_fold_share_one_window`
- [tests/test_hint_h2b_rereview.py](../../../../../../tests/test_hint_h2b_rereview.py) — direct import
  - `test_f9_the_first_submit_time_stays`
- [tests/test_hint_telemetry.py](../../../../../../tests/test_hint_telemetry.py) — direct import
  - `test_a_problem_opened_on_another_item_leaves_the_attempt_reached`
  - `test_a_workbench_problem_holding_a_hint_is_workbench_state_unknown`
  - `test_hiding_the_book_after_the_submit_never_flips_the_attempt`
  - `test_submit_never_attaches_another_sessions_or_items_rows`
  - `test_the_report_summarises_any_number_of_rows`
- [tests/test_hypothesis_marks_context.py](../../../../../../tests/test_hypothesis_marks_context.py) — direct import
  - `test_the_whole_report_carries_the_section_in_json_and_in_words`
- [tests/test_intent_plan.py](../../../../../../tests/test_intent_plan.py) — direct import
  - `test_plan_report_counts_the_recall_target_fallbacks`
- [tests/test_judge_routes.py](../../../../../../tests/test_judge_routes.py) — direct import
  - `test_judgment_ledger_accepts_the_decider_with_provenance`
  - `test_migration_175_preserves_every_judgment_and_its_references`
  - `test_receipts_store_labels_and_unlabelled_calls_work_below_175`
- [tests/test_judgment_ledger.py](../../../../../../tests/test_judgment_ledger.py) — direct import
- [tests/test_knowledge_map_text_neighbors.py](../../../../../../tests/test_knowledge_map_text_neighbors.py) — direct import
  - `test_item_text_ranks_like_the_store_and_leaves_the_map_geometry_alone`
  - `test_render_never_calls_a_model_or_writes`
- [tests/test_learner_blindness_relax.py](../../../../../../tests/test_learner_blindness_relax.py) — direct import
- [tests/test_learner_gap_unlinked_migration.py](../../../../../../tests/test_learner_gap_unlinked_migration.py) — direct import
- [tests/test_learner_note_source_kind_migration.py](../../../../../../tests/test_learner_note_source_kind_migration.py) — direct import
- [tests/test_learner_notes_vault_origin_migration.py](../../../../../../tests/test_learner_notes_vault_origin_migration.py) — direct import
- [tests/test_learner_text_gaps.py](../../../../../../tests/test_learner_text_gaps.py) — direct import
  - `test_a_matched_target_is_the_questions_weak_signal_with_its_subject`
  - `test_a_missing_prerequisite_is_drafted_created_live_seeded_and_committed`
  - `test_named_gaps_reach_the_learner_state_card`
  - `test_the_cli_dry_runs_send_and_write_nothing`
  - `test_the_vault_wide_shortlist_ranks_stored_vectors_and_judges_decide`
  - `test_undo_creation_puts_the_lo_away_and_removes_its_edge_and_commitment`
  - `test_without_a_reading_nothing_is_targeted_and_the_grounded_rule_stays`
- [tests/test_learner_text_gaps_composition.py](../../../../../../tests/test_learner_text_gaps_composition.py) — direct import
  - `test_a_stuck_answer_keeps_its_confusion_signal_and_adds_one_gap_observation`
  - `test_a_stuck_answer_with_text_is_queued_at_recording_and_read`
  - `test_stuck_answer_reads_one_attempt_exactly_as_stuck_answers_does`
  - `test_the_gap_signal_changes_serving_only_at_mvp016_with_its_switch`
- [tests/test_learner_text_gaps_flow.py](../../../../../../tests/test_learner_text_gaps_flow.py) — direct import
  - `test_a_gap_brings_an_assumed_los_check_forward_and_the_switch_restores_the_predecessor`
  - `test_a_gap_on_a_maintenance_lo_brings_its_next_review_forward_until_answered`
  - `test_a_job_that_keeps_failing_is_logged_as_failed_without_a_target`
  - `test_stuck_text_is_read_through_the_source_interface`
  - `test_the_queue_runs_a_text_once_retries_failures_and_respects_the_switch`
  - `test_the_switch_off_queue_equals_the_predecessor_version`
- [tests/test_learner_text_gaps_rereview.py](../../../../../../tests/test_learner_text_gaps_rereview.py) — direct import
  - `test_rr_f5_a_commands_calls_do_not_count_toward_the_live_daily_cap`
  - `test_rr_f6_only_a_tap_on_a_belief_answer_is_counted`
- [tests/test_learner_text_gaps_review.py](../../../../../../tests/test_learner_text_gaps_review.py) — direct import
  - `test_f5_a_match_on_the_items_own_lo_is_no_prerequisite_target`
  - `test_f5_several_same_verdicts_are_ambiguous_and_target_nothing`
  - `test_f6_a_question_retargeted_by_a_later_reading_is_observed_at_the_reading`
  - `test_f8_the_adapter_reads_the_marker_before_scanning`
- [tests/test_learner_text_source_widening.py](../../../../../../tests/test_learner_text_source_widening.py) — direct import
- [tests/test_library_asks_migration.py](../../../../../../tests/test_library_asks_migration.py) — direct import
- [tests/test_library_exercises.py](../../../../../../tests/test_library_exercises.py) — direct import
  - `test_a_long_exercise_opens_on_its_complete_statement_not_the_cards_preview`
  - `test_r2_contract_no_workbench_or_reader_exercise_rpc_returns_a_held_out_statement`
  - `test_r2_verify_f2_submit_with_no_practice_session_admits_the_owed_pick_first`
  - `test_r4_verify_f7_an_exercise_held_out_after_its_card_was_shown_is_never_read_or_opened`
  - `test_the_fallback_finds_exercise_regions_of_the_teaching_scope_only_and_records_what_it_showed`
  - `test_use_this_one_opens_at_once_on_the_verbatim_stem_while_the_import_runs`
- [tests/test_local_index.py](../../../../../../tests/test_local_index.py) — direct import
  - `test_a_moved_canary_stores_nothing_and_marks_epoch_drift`
  - `test_a_worker_on_another_software_epoch_stores_nothing`
  - `test_the_index_job_caches_both_variants_and_registers_the_spaces`
- [tests/test_matching.py](../../../../../../tests/test_matching.py) — direct import
  - `test_a_partially_backfilled_replacement_model_never_ranks`
  - `test_an_asymmetric_kind_shortlists_an_ephemeral_query_against_a_pool_of_another_record_kind`
  - `test_shortlist_takes_top_k_skips_settled_and_applies_only_a_given_cutoff`
- [tests/test_mcp_runtime.py](../../../../../../tests/test_mcp_runtime.py) — direct import
  - `test_a_second_process_serves_the_vault_beside_the_desktop_sidecar`
  - `test_secondary_attach_refuses_a_schema_it_does_not_match`
- [tests/test_method_explicit_upgrade.py](../../../../../../tests/test_method_explicit_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_method_phrasing_report.py](../../../../../../tests/test_method_phrasing_report.py) — direct import
  - `test_repairs_are_pending_proposals_applied_only_on_accept`
- [tests/test_migrate_fresh.py](../../../../../../tests/test_migrate_fresh.py) — direct import
  - `test_fk_toggle_migration_is_atomic_and_restores_enforcement`
  - `test_incremental_migration_and_ledger_receipt_roll_back_together`
  - `test_incremental_statement_parser_preserves_trigger_bodies`
  - `test_real_fk_rebuild_153_rolls_back_on_interruption`
- [tests/test_migration_coordinator.py](../../../../../../tests/test_migration_coordinator.py) — direct import
  - `test_process_death_mid_migration_leaves_body_and_receipt_fully_absent`
- [tests/test_migrations.py](../../../../../../tests/test_migrations.py) — direct import
  - `test_agent_runs_have_generic_provider_metadata`
  - `test_attempt_feedback_metadata_allows_ai_source`
  - `test_controller_decision_action_and_shadow_authority_checks`
  - `test_controller_snapshot_migration_applies_on_pre_096_db`
  - `test_controller_snapshot_schema_is_available`
  - `test_durable_ingest_jobs_migration_applies_on_pre_033_db`
  - `test_durable_ingest_jobs_schema_is_available`
  - `test_entity_source_links_relation_and_status_checks`
  - `test_every_fixture_upgrades_with_clean_foreign_keys`
  - `test_facet_diagnostic_schema_is_available`
  - `test_first_error_cleanup_is_semantically_demoted_not_learned`
  - `test_fresh_db_applies_all_migrations`
  - `test_head_163_database_upgrades_to_snapshots_and_fk_free_adjudications`
  - `test_misconception_migration_applies_on_pre_025_db`
  - `test_misconception_registry_schema_is_available`
  - `test_open_text_migration_preserves_existing_attempts_and_foreign_keys`
  - `test_opening_the_vault_applies_pending_migrations_a_bare_repository_refuses`
  - `test_practice_attempts_allow_open_text_after_fresh_migration`
  - `test_practice_attempts_schema_matches_supported_attempt_types`
  - `test_provenance_manifests_apply_intents_schema_is_available`
  - `test_provenance_migration_applies_on_pre_044_db`
  - `test_question_promotion_request_migration_backfills_legacy_ledger`
  - `test_real_migration_chain_applies_incrementally_after_initial_schema`
  - `test_repair_opportunity_bridge_applies_after_opportunity_substrate`
  - `test_scheduler_training_log_schema_is_available`
  - `test_source_exposure_index_backfill_is_idempotent_on_092_only_vault`
  - `test_source_exposure_indexes_present_on_fresh_vault`
  - `test_source_layer_migration_applies_on_pre_032_db`
  - `test_source_layer_schema_is_available`
  - `test_source_unit_selections_migration_applies_on_pre_040_db`
  - `test_source_unit_selections_schema_is_available`
  - `test_variable_rubric_scale_migration_allows_scores_above_four`
- [tests/test_mobile_doctor.py](../../../../../../tests/test_mobile_doctor.py) — direct import
  - `test_doctor_checks_fake_deployment_without_mutating_vault`
- [tests/test_mobile_host_coexistence.py](../../../../../../tests/test_mobile_host_coexistence.py) — direct import
  - `test_capture_host_coexists_without_primary_startup_work`
- [tests/test_model_call_receipt_owners.py](../../../../../../tests/test_model_call_receipt_owners.py) — direct import
  - `test_a_database_below_the_receipt_schema_lets_the_model_call_run_unrecorded`
- [tests/test_mvp010_upgrade.py](../../../../../../tests/test_mvp010_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
  - `test_upgrade_flips_rebuilds_and_preserves_raw_history`
- [tests/test_mvp011_upgrade.py](../../../../../../tests/test_mvp011_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp013_upgrade.py](../../../../../../tests/test_mvp013_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
  - `test_upgrade_from_mvp012_flips_rebuilds_and_preserves_raw_history`
- [tests/test_mvp014_upgrade.py](../../../../../../tests/test_mvp014_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp015_upgrade.py](../../../../../../tests/test_mvp015_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp016_upgrade.py](../../../../../../tests/test_mvp016_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp017_route_check_replay.py](../../../../../../tests/test_mvp017_route_check_replay.py) — direct import
- [tests/test_mvp017_upgrade.py](../../../../../../tests/test_mvp017_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp018_upgrade.py](../../../../../../tests/test_mvp018_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp020_upgrade.py](../../../../../../tests/test_mvp020_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp021_upgrade.py](../../../../../../tests/test_mvp021_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
  - `test_the_successor_rebuild_equals_mvp020s_projection`
- [tests/test_mvp022_upgrade.py](../../../../../../tests/test_mvp022_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp023_upgrade.py](../../../../../../tests/test_mvp023_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_mvp09_upgrade.py](../../../../../../tests/test_mvp09_upgrade.py) — direct import
  - `test_upgrade_to_mvp09_flips_rebuilds_and_preserves_raw_history`
- [tests/test_notes_vault_search.py](../../../../../../tests/test_notes_vault_search.py) — direct import
  - `test_c2b_f1_a_note_under_a_protected_section_header_is_no_note`
- [tests/test_openai_embedding_client.py](../../../../../../tests/test_openai_embedding_client.py) — direct import
  - `test_batched_openrouter_request_mrl_order_and_receipt`
- [tests/test_output_budget.py](../../../../../../tests/test_output_budget.py) — direct import
- [tests/test_p0_cutover_mvp08.py](../../../../../../tests/test_p0_cutover_mvp08.py) — direct import
  - `test_upgrade_does_not_rewrite_raw_history`
- [tests/test_p0_projection_cutover.py](../../../../../../tests/test_p0_projection_cutover.py) — direct import
  - `test_adjudication_reverses_projection_and_preserves_history`
  - `test_ruling_a_superseded_rows_inert_nonsuperseded_rows_authoritative`
- [tests/test_persistence_open.py](../../../../../../tests/test_persistence_open.py) — direct import
  - `test_connection_centralizes_busy_timeout`
  - `test_read_only_connect_does_not_create_a_missing_database_or_parent`
  - `test_repository_attach_can_open_a_writable_scratch_copy`
- [tests/test_pfc_unverified_unassessed.py](../../../../../../tests/test_pfc_unverified_unassessed.py) — direct import
  - `test_joint_fixture_replays_through_the_unchanged_path`
- [tests/test_placement_report.py](../../../../../../tests/test_placement_report.py) — direct import
- [tests/test_plan_determinism.py](../../../../../../tests/test_plan_determinism.py) — direct import
  - `test_replay_never_reads_the_switch`
- [tests/test_plan_follows_path.py](../../../../../../tests/test_plan_follows_path.py) — direct import
  - `test_g47_a_rebuild_shows_zero_projection_deltas_and_never_reads_a_path`
- [tests/test_practice_index_adapters.py](../../../../../../tests/test_practice_index_adapters.py) — direct import
- [tests/test_probability_prep.py](../../../../../../tests/test_probability_prep.py) — direct import
  - `test_a_queued_intent_never_moves_the_cutoff_past_the_presentation`
  - `test_an_early_offer_moves_the_window_and_the_incumbent_back`
  - `test_decider_end_to_end_through_the_fake_endpoint`
  - `test_grading_time_never_moves_the_cutoff_and_an_unknown_start_withholds_history`
  - `test_llm_judge_metered_route_is_isolated_bounded_and_ledgered`
  - `test_resume_recovers_a_committed_verdict_instead_of_paying_again`
  - `test_rich_state_carries_hypothesis_evidence_and_help_timing_to_both_judges`
  - `test_subscription_llm_estimates_cost_ledgers_invalid_verdicts_and_resumes`
  - `test_the_offer_sets_the_cutoff_and_questions_during_the_attempt_never_show`
- [tests/test_project_experiment_store.py](../../../../../../tests/test_project_experiment_store.py) — direct import
  - `test_store_runs_in_wal_with_full_sync_in_production`
- [tests/test_proposal_dependencies.py](../../../../../../tests/test_proposal_dependencies.py) — direct import
- [tests/test_query_student.py](../../../../../../tests/test_query_student.py) — direct import
- [tests/test_question_promotions.py](../../../../../../tests/test_question_promotions.py) — direct import
  - `test_027_rebuild_preserves_existing_rows`
  - `test_attempt_before_promotion_does_not_consume_practice_again_request`
  - `test_learner_claims_accepts_tutor_gap_declaration_source`
  - `test_question_promotions_schema_available_on_fresh_db`
  - `test_requested_practice_item_ids_orders_oldest_first_and_excludes_attempted`
- [tests/test_reader_ca4_table_by_point.py](../../../../../../tests/test_reader_ca4_table_by_point.py) — direct import
  - `test_a_cell_names_the_anchor_block_that_holds_its_quote`
  - `test_a_quote_across_two_anchor_blocks_is_not_shown_as_one_blocks_words`
- [tests/test_reader_rw1b_review.py](../../../../../../tests/test_reader_rw1b_review.py) — direct import
  - `test_f1_a_formative_gap_brings_no_check_forward`
  - `test_f1_a_formative_gap_is_not_a_weak_prerequisite_signal`
- [tests/test_reader_rw1c_review.py](../../../../../../tests/test_reader_rw1c_review.py) — direct import
  - `test_a_bound_question_precedes_the_next_attempt_in_the_field`
  - `test_a_mapped_lo_does_not_suppress_the_attribution`
- [tests/test_reader_rw3a_landing.py](../../../../../../tests/test_reader_rw3a_landing.py) — direct import
  - `test_the_answer_to_a_check_binds_by_the_picks_presentation`
- [tests/test_reader_rw3b_migration.py](../../../../../../tests/test_reader_rw3b_migration.py) — direct import
- [tests/test_reader_rw4b_admission_idempotency.py](../../../../../../tests/test_reader_rw4b_admission_idempotency.py) — direct import
  - `test_r1_a_retry_after_a_locked_final_write_makes_no_second_pick`
- [tests/test_reader_rw4b_fix6.py](../../../../../../tests/test_reader_rw4b_fix6.py) — direct import
  - `test_f2_verify_sequence_planned_pick_locked_picked_write_retry_under_a_later_plan`
  - `test_r7_a_failed_presentation_write_rolls_the_whole_keyed_pick_back`
- [tests/test_reader_rw7a_migration.py](../../../../../../tests/test_reader_rw7a_migration.py) — direct import
- [tests/test_reader_workbench_rw2a.py](../../../../../../tests/test_reader_workbench_rw2a.py) — direct import
  - `test_an_abandoned_session_writes_no_attempt_and_a_rebuild_leaves_the_workbench_alone`
  - `test_migration_207_creates_both_tables_with_every_check_value`
- [tests/test_reading_step_switch.py](../../../../../../tests/test_reading_step_switch.py) — direct import
  - `test_replay_never_reads_the_switch`
- [tests/test_rebuild_equivalence_review.py](../../../../../../tests/test_rebuild_equivalence_review.py) — direct import
- [tests/test_rebuild_orchestrator.py](../../../../../../tests/test_rebuild_orchestrator.py) — direct import
  - `test_content_recalibration_replay_cannot_lose_its_ingest_lease_midway`
  - `test_golden_projection_survives_one_umbrella_rebuild_exactly_and_stale_rows_clear`
  - `test_umbrella_accounts_for_every_raw_attempt_and_records_one_receipt`
- [tests/test_recurrence_commands.py](../../../../../../tests/test_recurrence_commands.py) — direct import
  - `test_rebuild_makes_no_model_call_and_is_a_fixed_point`
  - `test_the_head_fixture_predecessor_to_successor_path`
- [tests/test_recurrence_live.py](../../../../../../tests/test_recurrence_live.py) — direct import
  - `test_a_verdict_after_a_promotion_moves_only_the_group_projection_and_rebuild_matches_live`
- [tests/test_reference_gate_imports.py](../../../../../../tests/test_reference_gate_imports.py) — direct import
  - `test_a_historical_reader_import_resolves_to_model_answer`
  - `test_a_reader_import_row_counts_as_an_import`
  - `test_a_regrade_against_an_edited_unverified_key_never_certifies`
  - `test_a_regrade_never_raises_an_attempts_status`
  - `test_attempts_record_the_key_status_and_unverified_ones_never_certify`
- [tests/test_regrade_contract_upgrade.py](../../../../../../tests/test_regrade_contract_upgrade.py) — direct import
  - `test_after_the_upgrade_a_rebuild_settles_and_stays`
  - `test_head_fixture_predecessor_to_successor_path`
- [tests/test_repository_scopes.py](../../../../../../tests/test_repository_scopes.py) — direct import
  - `test_atomic_scope_rolls_back_nested_commits_and_serializes_writers`
- [tests/test_required_method_authority.py](../../../../../../tests/test_required_method_authority.py) — direct import
  - `test_f13_a_frozen_regrade_of_the_current_content_still_binds_it`
  - `test_the_judgment_is_made_once_ledgered_with_probabilities_and_the_argmax_decides`
- [tests/test_required_method_grading.py](../../../../../../tests/test_required_method_grading.py) — direct import
  - `test_grades_recorded_at_the_predecessor_replay_unchanged_after_the_upgrade`
  - `test_live_another_route_fails_the_method_criterion_with_no_quote`
- [tests/test_required_method_reopened.py](../../../../../../tests/test_required_method_reopened.py) — direct import
- [tests/test_required_method_rereview.py](../../../../../../tests/test_required_method_rereview.py) — direct import
- [tests/test_required_method_round3.py](../../../../../../tests/test_required_method_round3.py) — direct import
  - `test_f22_a_partial_selection_left_by_an_earlier_run_is_finished_first`
- [tests/test_required_method_round3_final_verify.py](../../../../../../tests/test_required_method_round3_final_verify.py) — direct import
  - `test_a_contract_without_a_recorded_hash_leaves_the_cleared_question_needing_a_fresh_check`
- [tests/test_required_method_round3_rereview.py](../../../../../../tests/test_required_method_round3_rereview.py) — direct import
  - `test_f1_a_cleared_method_is_never_verified_by_a_check_of_the_method_question`
  - `test_f1_a_ladder_result_committed_later_keeps_the_identity_it_was_computed_under`
  - `test_f1_checks_record_their_identity_and_an_item_without_a_method_keeps_its_checks`
  - `test_f9_the_resume_budgets_the_largest_judgment_estimates_not_the_longest_stems`
- [tests/test_required_method_round3_review.py](../../../../../../tests/test_required_method_round3_review.py) — direct import
  - `test_f1_changing_only_the_required_method_needs_a_fresh_check`
  - `test_f3_exam_review_shows_the_question_the_answer_was_given`
  - `test_f7_a_selection_to_finish_is_estimated_from_its_survivors`
  - `test_f8_the_attempt_time_revision_settles_it`
- [tests/test_reread_safety.py](../../../../../../tests/test_reread_safety.py) — direct import
- [tests/test_retrieval_spaces_migration.py](../../../../../../tests/test_retrieval_spaces_migration.py) — direct import
  - `test_220_on_the_durability_lane`
- [tests/test_reveal_ledger.py](../../../../../../tests/test_reveal_ledger.py) — direct import
  - `test_migration_154_adds_the_ledger_and_the_question_event_columns`
- [tests/test_route_rules_in_grader.py](../../../../../../tests/test_route_rules_in_grader.py) — direct import
  - `test_a_proof_item_is_graded_in_exactly_one_model_call`
  - `test_f5_a_joint_regrade_supersedes_a_route_verdict`
  - `test_migration_186_keeps_its_trigger_which_nothing_writes_now`
- [tests/test_router_g4_restraint.py](../../../../../../tests/test_router_g4_restraint.py) — direct import
  - `test_an_inserted_follow_up_is_bound_to_its_own_decision_by_its_presentation`
- [tests/test_router_presentations.py](../../../../../../tests/test_router_presentations.py) — direct import
- [tests/test_router_r2b_agreement.py](../../../../../../tests/test_router_r2b_agreement.py) — direct import
  - `test_a_failed_decider_is_a_fallback_in_the_report`
  - `test_the_router_decisions_feed_the_agreement_report`
- [tests/test_router_r2bc_landing.py](../../../../../../tests/test_router_r2bc_landing.py) — direct import
  - `test_check_me_under_the_mixture_is_logged_once_and_binds_to_its_presentation`
- [tests/test_router_r2c_retrieval.py](../../../../../../tests/test_router_r2c_retrieval.py) — direct import
  - `test_only_matured_decisions_from_another_session_and_plan_are_similar`
  - `test_replay_never_needs_a_vector`
- [tests/test_rw2c_fix_round2.py](../../../../../../tests/test_rw2c_fix_round2.py) — direct import
  - `test_fr2_5_a_later_regrade_never_changes_s5s_outcome_at_as_of_linked_or_standalone`
  - `test_fr2_5_an_s5_record_read_before_its_censoring_horizon_is_pending_not_expired`
  - `test_fr2_5_the_s5_historical_read_leaves_current_behaviour_alone`
- [tests/test_rw2c_fix_round3.py](../../../../../../tests/test_rw2c_fix_round3.py) — direct import
  - `test_l6_the_compare_rpcs_refuse_a_problem_whose_exercise_is_withheld_now`
- [tests/test_rw4d_rw3b_composition.py](../../../../../../tests/test_rw4d_rw3b_composition.py) — direct import
  - `test_every_passage_rw4ds_predicate_withholds_is_one_the_cues_never_surface`
- [tests/test_rw5c_recheck.py](../../../../../../tests/test_rw5c_recheck.py) — direct import
- [tests/test_secondary_attach.py](../../../../../../tests/test_secondary_attach.py) — direct import
  - `test_second_process_attaches_beside_a_writing_primary_on_wal`
  - `test_secondary_refuses_a_schema_it_would_have_to_migrate`
- [tests/test_section_coverage_migration.py](../../../../../../tests/test_section_coverage_migration.py) — direct import
  - `test_222_on_the_durability_lane`
- [tests/test_shadow_rebuild.py](../../../../../../tests/test_shadow_rebuild.py) — direct import
- [tests/test_sidecar_close_cancels_jobs.py](../../../../../../tests/test_sidecar_close_cancels_jobs.py) — direct import
  - `test_shutting_down_the_gaps_slot_inside_a_request_sends_no_further_request`
- [tests/test_source_block_fts.py](../../../../../../tests/test_source_block_fts.py) — direct import
  - `test_a_delete_never_removes_another_blocks_index_row`
  - `test_migration_177_indexes_a_176_vaults_existing_blocks`
  - `test_queries_are_sanitized_stemmed_scoped_and_ranked`
  - `test_replacing_a_runs_blocks_replaces_its_index_rows`
  - `test_triggers_index_every_written_block_except_page_furniture`
- [tests/test_source_retrieval_cli.py](../../../../../../tests/test_source_retrieval_cli.py) — direct import
  - `test_deep_search_has_a_dry_run_and_caps`
- [tests/test_source_retrieval_codex_unavailable.py](../../../../../../tests/test_source_retrieval_codex_unavailable.py) — direct import
- [tests/test_source_retrieval_followup.py](../../../../../../tests/test_source_retrieval_followup.py) — direct import
  - `test_the_report_runs_the_production_verification_by_query_type`
- [tests/test_source_retrieval_guards.py](../../../../../../tests/test_source_retrieval_guards.py) — direct import
  - `test_a_cited_span_overlapping_the_expected_answer_is_debited_as_a_reveal`
  - `test_linked_spans_without_retrieval_are_not_debited`
- [tests/test_source_retrieval_rereview.py](../../../../../../tests/test_source_retrieval_rereview.py) — direct import
- [tests/test_source_retrieval_search.py](../../../../../../tests/test_source_retrieval_search.py) — direct import
  - `test_dense_ranking_is_the_phase_1_mean_centred_cosine`
- [tests/test_source_retrieval_suites.py](../../../../../../tests/test_source_retrieval_suites.py) — direct import
  - `test_b4_compares_page_images_with_text_chunks_and_decides_conservatively`
- [tests/test_source_retrieval_tutor.py](../../../../../../tests/test_source_retrieval_tutor.py) — direct import
  - `test_tutor_spans_are_retrieved_for_the_question_then_verified`
- [tests/test_source_service_spend_accounting.py](../../../../../../tests/test_source_service_spend_accounting.py) — direct import
  - `test_a_receipt_without_a_cost_is_priced_at_its_requests_recorded_rate`
  - `test_a_released_reservation_cannot_start_its_request`
  - `test_a_request_reserved_yesterday_counts_on_yesterdays_cap`
  - `test_an_upgrade_counts_every_request_and_reports_the_unprovable_overlap`
  - `test_separate_processes_race_for_the_shared_cap`
  - `test_spend_since_counts_a_reported_cost_alongside_tokens`
  - `test_subscription_requests_are_never_refused_by_the_shared_daily_cap`
- [tests/test_source_service_spend_envelopes.py](../../../../../../tests/test_source_service_spend_envelopes.py) — direct import
  - `test_spend_since_counts_a_request_in_the_first_second_of_a_run`
  - `test_spend_since_estimates_subscription_tokens_and_prices_unreported_metered_cost`
- [tests/test_source_vector_backfill.py](../../../../../../tests/test_source_vector_backfill.py) — direct import
- [tests/test_sources_merge_composition.py](../../../../../../tests/test_sources_merge_composition.py) — direct import
  - `test_a_decision_mode_valuation_records_its_forecast_when_logging_is_on`
- [tests/test_sqlite_test_mode.py](../../../../../../tests/test_sqlite_test_mode.py) — direct import
- [tests/test_sqlite_wal.py](../../../../../../tests/test_sqlite_wal.py) — direct import
  - `test_a_long_read_transaction_delays_checkpoints_only_until_it_ends`
  - `test_connect_sets_production_pragmas_and_never_changes_the_journal_mode`
  - `test_fresh_creation_discards_an_orphaned_wal_from_a_deleted_database`
  - `test_read_only_open_in_a_read_only_directory_reads_commits_still_in_the_wal`
  - `test_read_only_open_without_a_shm_in_a_read_only_directory_fails_with_what_to_do`
  - `test_read_only_reports_work_in_a_read_only_vault_whose_wal_files_exist`
  - `test_runtime_sqlite_below_the_minimum_fails_with_a_clear_message`
  - `test_switch_fails_clearly_and_leaves_the_mode_unchanged_while_a_reader_is_open`
  - `test_wal_reset_fix_matches_the_advisory`
- [tests/test_sqlite_wal_lifecycle.py](../../../../../../tests/test_sqlite_wal_lifecycle.py) — direct import
  - `test_backup_gives_up_on_a_source_locked_after_its_probe_and_removes_the_copy`
  - `test_doctor_reports_wal_size_and_warns_when_it_is_large`
  - `test_finished_ingest_batch_truncates_the_wal`
  - `test_live_rebuild_truncates_the_wal_it_grew`
  - `test_sim_run_vault_keeps_commits_still_in_the_source_wal`
  - `test_wal_stays_bounded_across_twenty_queue_builds_on_a_fixture_copy`
- [tests/test_state_sync_scheduling_race.py](../../../../../../tests/test_state_sync_scheduling_race.py) — direct import
  - `test_a_probe_attempt_after_the_fallback_read_stays_retired`
  - `test_content_change_sync_keeps_an_attempt_committed_after_its_snapshot`
  - `test_creating_sync_keeps_a_row_an_attempt_inserted_after_its_snapshot`
  - `test_incremental_watch_refresh_keeps_an_attempt_committed_after_its_read`
  - `test_review_parking_after_the_lifecycle_reads_keeps_the_item_inactive`
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — direct import
  - `test_a_joint_regrade_rereads_the_stuck_answer_and_supersedes`
  - `test_a_regrade_appends_a_superseding_stuck_judgment`
  - `test_a_stuck_attempt_without_confusion_writes_no_signal`
  - `test_an_empty_stuck_answer_scores_zero_without_a_model_call`
  - `test_cli_subscription_grading_counts_calls_without_a_token_bound`
  - `test_confusion_is_read_and_signalled_in_both_grading_modes`
  - `test_confusion_text_is_marked_and_becomes_a_fast_track_blocking_signal`
  - `test_migration_179_widens_the_reveal_kinds_and_keeps_the_ledger`
  - `test_sidecar_dont_know_records_an_empty_stuck_answer_in_an_active_vault`
  - `test_the_owner_summary_counts_text_share_confusion_and_grading_runs`
  - `test_the_stuck_reading_appends_a_judgment_with_the_blind_record`
- [tests/test_stuck_prompt_composition.py](../../../../../../tests/test_stuck_prompt_composition.py) — direct import
  - `test_a_stuck_answers_pfc_unverified_criteria_are_unassessed`
- [tests/test_stuck_prompt_replay.py](../../../../../../tests/test_stuck_prompt_replay.py) — direct import
  - `test_a_stuck_vault_rebuilds_to_a_fixed_point_with_no_model_call`
  - `test_historical_dont_know_rows_replay_unchanged_under_the_successor`
- [tests/test_success_head_cli.py](../../../../../../tests/test_success_head_cli.py) — direct import
  - `test_loader_clears_ambiguous_identities_and_reads_skeletons_for_current_text`
  - `test_loader_reads_phase_5a_skeletons_keyed_by_item_id`
  - `test_loader_uses_the_seen_text_and_never_substitutes_current_vectors`
  - `test_seen_stem_records_follow_the_seen_revision_and_scored_rows`
- [tests/test_t6_followup_review.py](../../../../../../tests/test_t6_followup_review.py) — direct import
  - `test_paid_calls_reserve_and_record_the_real_increased_limit`
- [tests/test_table_roles.py](../../../../../../tests/test_table_roles.py) — direct import
  - `test_migration_head_user_tables_match_role_registry_exactly`
  - `test_synthetic_unclassified_table_fails_registry_check`
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
  - `test_migration_020_allows_teach_back_on_existing_db`
  - `test_regrade_teach_back_attempt_without_evidence_falls_back_to_core`
- [tests/test_teacher_te0_confidence_events.py](../../../../../../tests/test_teacher_te0_confidence_events.py) — direct import
- [tests/test_teacher_te0_fix_round2.py](../../../../../../tests/test_teacher_te0_fix_round2.py) — direct import
  - `test_a_held_review_grade_reads_held_for_review_in_a_later_targets_history`
  - `test_the_live_history_keeps_the_ledgers_hold`
- [tests/test_teacher_te0_review_fixes.py](../../../../../../tests/test_teacher_te0_review_fixes.py) — direct import
  - `test_the_offline_runner_renders_the_confidence_block_into_each_arms_prompt`
- [tests/test_tutor_delivery_fixes.py](../../../../../../tests/test_tutor_delivery_fixes.py) — direct import
  - `test_the_complete_passages_kill_switch_restores_the_judges_900_characters`
- [tests/test_ux_phase2_error_type_proposals.py](../../../../../../tests/test_ux_phase2_error_type_proposals.py) — direct import
  - `test_a_grading_that_waits_on_another_writer_sees_its_proposal`
  - `test_a_rejected_proposal_does_not_absorb_a_later_grading`
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
- [tests/test_vault_epigraphs.py](../../../../../../tests/test_vault_epigraphs.py) — direct import
  - `test_vault_epigraphs_rows_are_immutable`
- [tests/test_voi_merge_composition.py](../../../../../../tests/test_voi_merge_composition.py) — direct import
- [tests/test_voi_stopping.py](../../../../../../tests/test_voi_stopping.py) — direct import
  - `test_the_decision_features_receipt_reads_the_overlay_and_says_so`
- [tests/test_whole_comparison_provenance_surfaces.py](../../../../../../tests/test_whole_comparison_provenance_surfaces.py) — direct import
- [tests/test_whole_comparison_reuse_provenance.py](../../../../../../tests/test_whole_comparison_reuse_provenance.py) — direct import

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/connection.py](../../../../../../src/learnloop/db/connection.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
