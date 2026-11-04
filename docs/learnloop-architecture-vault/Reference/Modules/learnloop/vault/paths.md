---
title: "learnloop.vault.paths"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/vault/paths.py"
source_paths:
  - "src/learnloop/vault/paths.py"
source_commit: "9044bfd1d4383b8eaa28de7590e93037d35791bb"
source_commit_timestamp: "2026-10-11T23:30:14-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.vault"
layer: "infrastructure"
concepts:
  - "State and Persistence"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.vault.paths module"
  - "src/learnloop/vault/paths.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-vault"
---

# `learnloop.vault.paths`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps paths behavior inside its owning package, [[Reference/Modules/learnloop/vault/_package|learnloop.vault]]. Its public surface centers on `VaultPaths`, `animation_video_path`, `find_vault_root`.

The authoritative system-level explanation remains in [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/vault/paths.py](../../../../../../src/learnloop/vault/paths.py) |
| Source lines | 126 |
| Owning package | [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `9044bfd1d4383b8eaa28de7590e93037d35791bb` |
| Commit timestamp | `2026-10-11T23:30:14-04:00` |

## Public API

- `class VaultPaths` ([source](../../../../../../src/learnloop/vault/paths.py), line 11)
  - `config_path(self) -> Path` (line 16; public)
  - `sqlite_path(self) -> Path` (line 20; public)
  - `concepts_path(self) -> Path` (line 24; public)
  - `relations_path(self) -> Path` (line 28; public)
  - `goals_path(self) -> Path` (line 32; public)
  - `learner_path(self) -> Path` (line 36; public)
  - `error_types_path(self) -> Path` (line 40; public)
  - `facets_path(self) -> Path` (line 44; public)
  - `subject_dir(self, subject_id: str) -> Path` (line 47; public)
  - `subject_markdown_path(self, subject_id: str) -> Path` (line 50; public)
  - `subject_graph_path(self, subject_id: str) -> Path` (line 53; public)
  - `learning_object_path(self, subject_id: str, learning_object_id: str) -> Path` (line 56; public)
  - `practice_item_path(self, subject_id: str, practice_item_id: str) -> Path` (line 59; public)
  - `activity_family_path(self, subject_id: str, family_id: str) -> Path` (line 62; public)
  - `note_path(self, subject_id: str, note_id: str) -> Path` (line 65; public)
  - `sources_dir(self) -> Path` (line 73; public)
  - `source_sets_path(self) -> Path` (line 77; public)
  - `source_dir(self, source_id: str) -> Path` (line 82; public)
  - `source_markdown_path(self, source_id: str) -> Path` (line 85; public)
  - `source_revision_path(self, source_id: str, revision_id: str) -> Path` (line 89; public)
  - `canonical_source_raw_path(self, asset_hash: str) -> Path` (line 93; public)
  - `source_extraction_cache_dir(self, extraction_id: str) -> Path` (line 97; public)
  - `animations_dir(self) -> Path` (line 102; public)
- `animation_video_path(root: Path, video_hash: str) -> Path` ([source](../../../../../../src/learnloop/vault/paths.py), line 107) — Content-addressed animation mp4 path; config-free like the raw store.
- `find_vault_root(start: Path) -> Path` ([source](../../../../../../src/learnloop/vault/paths.py), line 119)

## Internal implementation anchors

- `_sanitize_hash(asset_hash: str) -> str` ([source](../../../../../../src/learnloop/vault/paths.py), line 113)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ad_successor_upgrade|learnloop.ad_successor_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/attempt_content_state_upgrade|learnloop.attempt_content_state_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/bootstrap|learnloop.bootstrap]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/claim_fixes_upgrade|learnloop.claim_fixes_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/ad|learnloop.cli.ad]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/ai_compare|learnloop.cli.ai_compare]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/curriculum|learnloop.cli.curriculum]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/data|learnloop.cli.data]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/data_capture|learnloop.cli.data_capture]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/decider|learnloop.cli.decider]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/diagnose|learnloop.cli.diagnose]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/facets|learnloop.cli.facets]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/families|learnloop.cli.families]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/field_classification|learnloop.cli.field_classification]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/gaps|learnloop.cli.gaps]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/hints|learnloop.cli.hints]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/mcp|learnloop.cli.mcp]] — imports `find_vault_root`; statically calls `find_vault_root`
- [[Reference/Modules/learnloop/cli/placement|learnloop.cli.placement]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/plan|learnloop.cli.plan]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/practice_index|learnloop.cli.practice_index]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/project|learnloop.cli.project]] — imports `find_vault_root`; statically calls `find_vault_root`
- [[Reference/Modules/learnloop/cli/reader|learnloop.cli.reader]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/receipts|learnloop.cli.receipts]] — imports `VaultPaths`, `find_vault_root`; statically calls `VaultPaths`, `find_vault_root`
- [[Reference/Modules/learnloop/cli/recurrence|learnloop.cli.recurrence]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `VaultPaths`, `find_vault_root`; statically calls `VaultPaths`, `find_vault_root`
- [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/success_head|learnloop.cli.success_head]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cli/teacher|learnloop.cli.teacher]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/cold_retry_reschedule_upgrade|learnloop.cold_retry_reschedule_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]] — imports `VaultPaths`, `animation_video_path`; statically calls `VaultPaths`, `animation_video_path`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]] — imports `VaultPaths`
- [[Reference/Modules/learnloop/content/facet_identity/dedupe|learnloop.content.facet_identity.dedupe]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/content/pipeline/revision_refresh|learnloop.content.pipeline.revision_refresh]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]] — imports `VaultPaths`
- [[Reference/Modules/learnloop/content/proposals/method_phrasing|learnloop.content.proposals.method_phrasing]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/content/sources/source_deletion|learnloop.content.sources.source_deletion]] — imports `canonical_source_raw_path`; statically calls `canonical_source_raw_path`
- [[Reference/Modules/learnloop/content/synthesis/graph_nomination|learnloop.content.synthesis.graph_nomination]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/curriculum/concepts|learnloop.curriculum.concepts]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/curriculum/golden_path_fixture|learnloop.curriculum.golden_path_fixture]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/curriculum/graph_edit_proposals|learnloop.curriculum.graph_edit_proposals]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/curriculum/integration_backfill|learnloop.curriculum.integration_backfill]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/daily_plan_upgrade|learnloop.daily_plan_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/data_capture_upgrade|learnloop.data_capture_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/decider_upgrade|learnloop.decider_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/deliverable_plan_upgrade|learnloop.deliverable_plan_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/diagnosis/grading_hardcases|learnloop.diagnosis.grading_hardcases]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/diagnosis/recurrence/upgrade|learnloop.diagnosis.recurrence.upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/diagnosis/split/embeddings|learnloop.diagnosis.split.embeddings]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/eligibility_decision_upgrade|learnloop.eligibility_decision_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/evsi_calibration/forecast_report|learnloop.evsi_calibration.forecast_report]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/evsi_calibration/live_report|learnloop.evsi_calibration.live_report]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/records|learnloop.experiments.contextual_embeddings.records]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/followup_serve_upgrade|learnloop.followup_serve_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/goals/goal_contracts|learnloop.goals.goal_contracts]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/help_fold_attach_upgrade|learnloop.help_fold_attach_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/intent/deadline|learnloop.intent.deadline]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/intent_upgrade|learnloop.intent_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/learner/learner_profile|learnloop.learner.learner_profile]] — imports `VaultPaths`
- [[Reference/Modules/learnloop/learner/recall_calibration|learnloop.learner.recall_calibration]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/learner_text_gap_upgrade|learnloop.learner_text_gap_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/lesson_suggestions_upgrade|learnloop.lesson_suggestions_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/method_explicit_upgrade|learnloop.method_explicit_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/one_ask_upgrade|learnloop.one_ask_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/ops/contamination/recipes|learnloop.ops.contamination.recipes]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/ops/contamination/report|learnloop.ops.contamination.report]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/ops/debug_time|learnloop.ops.debug_time]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/ops/embedding_compare|learnloop.ops.embedding_compare]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/ops/family_proposals|learnloop.ops.family_proposals]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/ops/graph_nomination_report|learnloop.ops.graph_nomination_report]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/ops/pf_reports|learnloop.ops.pf_reports]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/ops/vault_upgrade|learnloop.ops.vault_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/practice_index/dossiers|learnloop.practice_index.dossiers]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `VaultPaths`
- [[Reference/Modules/learnloop/probe_tie_upgrade|learnloop.probe_tie_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/proof_check_upgrade|learnloop.proof_check_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/reader_followups_upgrade|learnloop.reader_followups_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/reading_path_plan_upgrade|learnloop.reading_path_plan_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/regrade_contract_upgrade|learnloop.regrade_contract_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/remote/runtime|learnloop.remote.runtime]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/replay_ledger_upgrade|learnloop.replay_ledger_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/route_rules_upgrade|learnloop.route_rules_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/router_mixture_upgrade|learnloop.router_mixture_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/router_staged_upgrade|learnloop.router_staged_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/sim/diagnostic_validation|learnloop.sim.diagnostic_validation]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/source_retrieval/bench|learnloop.source_retrieval.bench]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/source_retrieval/recipes|learnloop.source_retrieval.recipes]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/source_retrieval/source_vectors|learnloop.source_retrieval.source_vectors]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/sources_upgrade|learnloop.sources_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/stuck_prompt_upgrade|learnloop.stuck_prompt_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/substrate/families|learnloop.substrate.families]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/substrate/shadow_rebuild|learnloop.substrate.shadow_rebuild]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/superseded_claims_upgrade|learnloop.superseded_claims_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/teacher_upgrade|learnloop.teacher_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/tui/state|learnloop.tui.state]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/embedding_recipes|learnloop.vault.embedding_recipes]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `VaultPaths`, `find_vault_root`; statically calls `VaultPaths`, `find_vault_root`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `VaultPaths`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/voi_stopping_upgrade|learnloop.voi_stopping_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop/workbench_field_signals_upgrade|learnloop.workbench_field_signals_upgrade]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop_sidecar/handlers/library|learnloop_sidecar.handlers.library]] — imports `VaultPaths`; statically calls `VaultPaths`
- [[Reference/Modules/learnloop_sidecar/handlers/vault|learnloop_sidecar.handlers.vault]] — imports `VaultPaths`; statically calls `VaultPaths`

### Repository tooling consumers

- [scripts/benchmark_sqlite_concurrency.py](../../../../../../scripts/benchmark_sqlite_concurrency.py); calls `VaultPaths`
- [scripts/gen_goldenpath_fixtures.py](../../../../../../scripts/gen_goldenpath_fixtures.py); calls `VaultPaths`
- [scripts/voi_cap_report.py](../../../../../../scripts/voi_cap_report.py); calls `VaultPaths`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/ingest/originals|learnloop.ingest.originals]] — imports `canonical_source_raw_path`; calls `canonical_source_raw_path`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `pathlib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/ad_successor_upgrade|learnloop.ad_successor_upgrade]], [[Reference/Modules/learnloop/attempt_content_state_upgrade|learnloop.attempt_content_state_upgrade]], [[Reference/Modules/learnloop/bootstrap|learnloop.bootstrap]], [[Reference/Modules/learnloop/claim_fixes_upgrade|learnloop.claim_fixes_upgrade]], [[Reference/Modules/learnloop/cli/ad|learnloop.cli.ad]] and 125 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/daily_plan_fakes.py](../../../../../../tests/daily_plan_fakes.py) — direct import
- [tests/deliverable_fixtures.py](../../../../../../tests/deliverable_fixtures.py) — direct import
- [tests/diagnosis_split_helpers.py](../../../../../../tests/diagnosis_split_helpers.py) — direct import
- [tests/e0_fakes.py](../../../../../../tests/e0_fakes.py) — direct import
- [tests/exam_scope_fixtures.py](../../../../../../tests/exam_scope_fixtures.py) — direct import
- [tests/helpers.py](../../../../../../tests/helpers.py) — direct import
- [tests/intent_fakes.py](../../../../../../tests/intent_fakes.py) — direct import
- [tests/mcp_world.py](../../../../../../tests/mcp_world.py) — direct import
- [tests/practice_index_fakes.py](../../../../../../tests/practice_index_fakes.py) — direct import
- [tests/reading_path_fixtures.py](../../../../../../tests/reading_path_fixtures.py) — direct import
- [tests/rw5c_golden_source.py](../../../../../../tests/rw5c_golden_source.py) — direct import
- [tests/section_coverage_fixtures.py](../../../../../../tests/section_coverage_fixtures.py) — direct import
- [tests/source_retrieval_fakes.py](../../../../../../tests/source_retrieval_fakes.py) — direct import
- [tests/source_service_fakes.py](../../../../../../tests/source_service_fakes.py) — direct import
- [tests/teacher_fakes.py](../../../../../../tests/teacher_fakes.py) — direct import
- [tests/test_ad1_fix_round4.py](../../../../../../tests/test_ad1_fix_round4.py) — direct import
- [tests/test_ad23_t1_routes.py](../../../../../../tests/test_ad23_t1_routes.py) — direct import
  - `test_inside_an_ad_operation_no_route_asks_and_no_grant_serves`
- [tests/test_ai_compare.py](../../../../../../tests/test_ai_compare.py) — direct import
  - `test_a_draft_the_tutor_would_reject_is_invalid`
  - `test_a_dry_run_may_make_the_copy_and_copy_from_needs_a_new_directory`
  - `test_a_json_repair_carries_the_budget_of_the_request_it_repairs`
  - `test_a_live_vault_moved_out_of_git_is_still_refused_and_its_copy_is_compared`
  - `test_a_run_on_a_copy_reports_agreement_validity_latency_tokens_and_allowance`
  - `test_a_vault_whose_database_lies_outside_it_is_refused`
  - `test_a_working_vault_is_refused`
  - `test_copy_from_backs_up_a_wal_database_not_named_sqlite`
  - `test_copy_from_backs_up_the_database_a_symlinked_path_opens`
  - `test_copy_from_relocates_a_database_configured_outside_the_vault`
  - `test_each_request_carries_the_output_budget_its_estimate_reports`
- [tests/test_apply_write_ahead.py](../../../../../../tests/test_apply_write_ahead.py) — direct import
- [tests/test_attempt_completion.py](../../../../../../tests/test_attempt_completion.py) — direct import
  - `test_block_closing_diagnostic_answer_keeps_grader_provenance`
- [tests/test_batch3_landing.py](../../../../../../tests/test_batch3_landing.py) — direct import
  - `test_iii_a_figure_grant_never_meters_an_ask_and_an_ask_grant_meters_it_under_the_cap`
- [tests/test_chatgpt_plan_provider.py](../../../../../../tests/test_chatgpt_plan_provider.py) — direct import
  - `test_t6_rewrite_runs_on_the_plan_with_receipts`
- [tests/test_cli_attempt.py](../../../../../../tests/test_cli_attempt.py) — direct import
  - `test_cli_show_attempt_includes_evidence_and_surprise`
- [tests/test_cli_json.py](../../../../../../tests/test_cli_json.py) — direct import
  - `test_proposals_json_contract`
- [tests/test_concept_animation_service.py](../../../../../../tests/test_concept_animation_service.py) — direct import
- [tests/test_concept_animation_store.py](../../../../../../tests/test_concept_animation_store.py) — direct import
  - `test_animation_video_path_is_content_addressed`
- [tests/test_daily_loop_golden_path_lifecycle.py](../../../../../../tests/test_daily_loop_golden_path_lifecycle.py) — direct import
  - `test_assess_open_refuses_a_parked_lo_without_burning_the_surface`
- [tests/test_daily_loop_lo_lifecycle_serving.py](../../../../../../tests/test_daily_loop_lo_lifecycle_serving.py) — direct import
- [tests/test_daily_loop_reader_authored_practice.py](../../../../../../tests/test_daily_loop_reader_authored_practice.py) — direct import
- [tests/test_daily_plan_review_regressions.py](../../../../../../tests/test_daily_plan_review_regressions.py) — direct import
- [tests/test_diagnostic_generation.py](../../../../../../tests/test_diagnostic_generation.py) — direct import
- [tests/test_diagnostic_pack.py](../../../../../../tests/test_diagnostic_pack.py) — direct import
- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — direct import
- [tests/test_exam_protection_review.py](../../../../../../tests/test_exam_protection_review.py) — direct import
- [tests/test_facet_authority.py](../../../../../../tests/test_facet_authority.py) — direct import
  - `test_an_ingest_consolidation_keeps_exam_only_meaning_out_and_its_undo_cannot_mint_it`
  - `test_the_registry_writer_refuses_exam_only_meaning_whatever_the_caller_declares`
- [tests/test_facet_authority_review.py](../../../../../../tests/test_facet_authority_review.py) — direct import
  - `test_recovery_settles_an_undo_intent_the_authority_rule_refuses`
- [tests/test_facet_identity.py](../../../../../../tests/test_facet_identity.py) — direct import
- [tests/test_facet_identity_composition.py](../../../../../../tests/test_facet_identity_composition.py) — direct import
- [tests/test_facet_identity_ingest.py](../../../../../../tests/test_facet_identity_ingest.py) — direct import
  - `test_a_candidate_matching_a_registered_facet_becomes_its_alias`
  - `test_a_duplicate_candidate_is_merged_before_the_gates_and_undo_re_mints_it`
- [tests/test_facet_mint_gate.py](../../../../../../tests/test_facet_mint_gate.py) — direct import
  - `test_ingest_aliases_a_collapsing_candidate_into_a_registered_facet`
- [tests/test_facet_registry_v2.py](../../../../../../tests/test_facet_registry_v2.py) — direct import
- [tests/test_facet_reword_paths.py](../../../../../../tests/test_facet_reword_paths.py) — direct import
  - `test_an_append_facet_restructure_applies_as_a_facet_version_with_undo`
- [tests/test_failure_triage.py](../../../../../../tests/test_failure_triage.py) — direct import
  - `test_high_confidence_signature_takes_intended_route`
- [tests/test_failure_triage_causal_gate.py](../../../../../../tests/test_failure_triage_causal_gate.py) — direct import
  - `test_triage_records_tier_one_basis_on_the_result_and_the_event`
- [tests/test_figure_rich_job.py](../../../../../../tests/test_figure_rich_job.py) — direct import
  - `test_the_quick_figure_shows_first_and_the_fuller_one_lands_under_it`
- [tests/test_forecast_receipts.py](../../../../../../tests/test_forecast_receipts.py) — direct import
  - `test_f3_a_cold_success_whose_grade_is_now_held_is_not_measured`
- [tests/test_goal_scope_material.py](../../../../../../tests/test_goal_scope_material.py) — direct import
- [tests/test_golden_path_fixture.py](../../../../../../tests/test_golden_path_fixture.py) — direct import
  - `test_fixture_blueprint_is_active_after_confirmation`
  - `test_fixture_bootstrap_confirms_a_certifying_run`
- [tests/test_grading_hardcases.py](../../../../../../tests/test_grading_hardcases.py) — direct import
- [tests/test_held_grade_evidence.py](../../../../../../tests/test_held_grade_evidence.py) — direct import
  - `test_review_f3_diagnostic_observations_held_by_a_regrade_qualify_nothing`
- [tests/test_hypothesis_marks.py](../../../../../../tests/test_hypothesis_marks.py) — direct import
- [tests/test_hypothesis_marks_context.py](../../../../../../tests/test_hypothesis_marks_context.py) — direct import
  - `test_the_whole_report_carries_the_section_in_json_and_in_words`
- [tests/test_import_split_parity.py](../../../../../../tests/test_import_split_parity.py) — direct import
  - `test_author_then_write_writes_what_import_exercises_writes`
- [tests/test_intent_codex_review.py](../../../../../../tests/test_intent_codex_review.py) — direct import
  - `test_f9_concurrent_writers_publish_one_goal_and_one_link`
- [tests/test_intent_fix_round4.py](../../../../../../tests/test_intent_fix_round4.py) — direct import
- [tests/test_intent_fix_round5.py](../../../../../../tests/test_intent_fix_round5.py) — direct import
- [tests/test_intent_fix_round6.py](../../../../../../tests/test_intent_fix_round6.py) — direct import
- [tests/test_intent_fix_round7.py](../../../../../../tests/test_intent_fix_round7.py) — direct import
- [tests/test_intent_plan.py](../../../../../../tests/test_intent_plan.py) — direct import
- [tests/test_intent_planner.py](../../../../../../tests/test_intent_planner.py) — direct import
- [tests/test_km5_sim_gates.py](../../../../../../tests/test_km5_sim_gates.py) — direct import
  - `test_shadow_intent_logs_practice_integration_at_the_right_moment`
- [tests/test_learner_read_model_pinning.py](../../../../../../tests/test_learner_read_model_pinning.py) — direct import
- [tests/test_learner_report_superseded.py](../../../../../../tests/test_learner_report_superseded.py) — direct import
- [tests/test_lp_claim_fixes_rereview.py](../../../../../../tests/test_lp_claim_fixes_rereview.py) — direct import
- [tests/test_originals_store.py](../../../../../../tests/test_originals_store.py) — direct import
  - `test_failed_original_write_leaves_no_temporary_file`
  - `test_resolve_prefers_store_then_original_uri`
- [tests/test_p2_acceptance.py](../../../../../../tests/test_p2_acceptance.py) — direct import
- [tests/test_p2_leakage_suite.py](../../../../../../tests/test_p2_leakage_suite.py) — direct import
- [tests/test_pattern_ladder.py](../../../../../../tests/test_pattern_ladder.py) — direct import
- [tests/test_persona_gate.py](../../../../../../tests/test_persona_gate.py) — direct import
  - `test_gate_precision_reports_no_data_before_any_prediction`
- [tests/test_plan_first_transport_grant_scope.py](../../../../../../tests/test_plan_first_transport_grant_scope.py) — direct import
- [tests/test_plan_first_transport_offer_grants.py](../../../../../../tests/test_plan_first_transport_offer_grants.py) — direct import
- [tests/test_planted_misgrade.py](../../../../../../tests/test_planted_misgrade.py) — direct import
- [tests/test_practice_information.py](../../../../../../tests/test_practice_information.py) — direct import
- [tests/test_probe_orchestration_remainder.py](../../../../../../tests/test_probe_orchestration_remainder.py) — direct import
- [tests/test_quick_add.py](../../../../../../tests/test_quick_add.py) — direct import
- [tests/test_rbeq_pr2_landing.py](../../../../../../tests/test_rbeq_pr2_landing.py) — direct import
- [tests/test_reader_dialogue.py](../../../../../../tests/test_reader_dialogue.py) — direct import
  - `test_golden_path_completes_with_reader_never_invoked`
- [tests/test_reader_progression.py](../../../../../../tests/test_reader_progression.py) — direct import
  - `test_reader_source_refs_preserve_bounded_span_context`
- [tests/test_reader_recap_review_r2.py](../../../../../../tests/test_reader_recap_review_r2.py) — direct import
- [tests/test_reader_recap_review_r3.py](../../../../../../tests/test_reader_recap_review_r3.py) — direct import
- [tests/test_reader_reconnect.py](../../../../../../tests/test_reader_reconnect.py) — direct import
  - `test_a_landed_inquiry_check_names_its_model_and_prompt_version`
  - `test_inquiry_question_action_rpc_records_the_self_check`
  - `test_the_quick_check_read_reports_its_durable_jobs_state`
- [tests/test_reader_report.py](../../../../../../tests/test_reader_report.py) — direct import
  - `test_the_passage_quick_check_is_a_model_backed_action_in_the_funnel`
- [tests/test_reading_request_sweep.py](../../../../../../tests/test_reading_request_sweep.py) — direct import
- [tests/test_recall_coverage_interventions.py](../../../../../../tests/test_recall_coverage_interventions.py) — direct import
- [tests/test_router_r2a_landing.py](../../../../../../tests/test_router_r2a_landing.py) — direct import
- [tests/test_router_r2bc_landing.py](../../../../../../tests/test_router_r2bc_landing.py) — direct import
  - `test_router_embeddings_and_the_source_backfill_each_answer_to_their_own_guard`
- [tests/test_scheduler.py](../../../../../../tests/test_scheduler.py) — direct import
  - `test_scheduler_scores_due_goal_item`
- [tests/test_secondary_attach.py](../../../../../../tests/test_secondary_attach.py) — direct import
  - `test_load_secondary_writes_nothing_where_load_writes`
- [tests/test_sidecar_append.py](../../../../../../tests/test_sidecar_append.py) — direct import
  - `test_list_source_conflicts_enriches_extraction_ids`
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_sidecar_get_facet_mastery_shape_on_fixture_vault`
- [tests/test_sidecar_reader.py](../../../../../../tests/test_sidecar_reader.py) — direct import
  - `test_reader_ask_history_rpc_returns_durable_exchanges`
- [tests/test_sim_teach_back.py](../../../../../../tests/test_sim_teach_back.py) — direct import
  - `test_runner_completes_session_with_teach_back_item`
- [tests/test_simulation.py](../../../../../../tests/test_simulation.py) — direct import
- [tests/test_source_append.py](../../../../../../tests/test_source_append.py) — direct import
- [tests/test_source_deletion.py](../../../../../../tests/test_source_deletion.py) — direct import
  - `test_delete_keeps_stored_bytes_another_source_still_shares`
- [tests/test_source_set_synthesis.py](../../../../../../tests/test_source_set_synthesis.py) — direct import
  - `test_a_vault_whose_facets_used_to_be_locked_still_bootstraps`
- [tests/test_sqlite_wal_lifecycle.py](../../../../../../tests/test_sqlite_wal_lifecycle.py) — direct import
  - `test_wal_stays_bounded_across_twenty_queue_builds_on_a_fixture_copy`
- [tests/test_subject_registry.py](../../../../../../tests/test_subject_registry.py) — direct import
- [tests/test_surface_pool.py](../../../../../../tests/test_surface_pool.py) — direct import
- [tests/test_synthesis_criterion_dependencies.py](../../../../../../tests/test_synthesis_criterion_dependencies.py) — direct import
  - `test_fix_content_skips_unparseable_items_and_reports_them`
- [tests/test_t6_followup_composition.py](../../../../../../tests/test_t6_followup_composition.py) — direct import
  - `test_pf_caller_prices_a_truncation_retry_at_its_doubled_output_budget`
- [tests/test_teacher_te1_review_fixes.py](../../../../../../tests/test_teacher_te1_review_fixes.py) — direct import
  - `test_r3_f4_unreadable_protection_ends_the_lesson`
- [tests/test_today_surfaces.py](../../../../../../tests/test_today_surfaces.py) — direct import
  - `test_overconfidence_probe_origin_survives_target_selection`
  - `test_overconfidence_probe_records_origin`
  - `test_probe_episode_without_origin_is_null`
- [tests/test_ux_phase1_finish.py](../../../../../../tests/test_ux_phase1_finish.py) — direct import
- [tests/test_ux_phase1_usability_round1.py](../../../../../../tests/test_ux_phase1_usability_round1.py) — direct import
- [tests/test_voi_forecasts.py](../../../../../../tests/test_voi_forecasts.py) — direct import
  - `test_followup_outcome_needs_the_frozen_facet_map`
- [tests/ux_phase1_support.py](../../../../../../tests/ux_phase1_support.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains paths within learnloop.vault; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/vault/paths.py](../../../../../../src/learnloop/vault/paths.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
