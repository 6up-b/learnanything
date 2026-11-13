---
title: "learnloop.diagnosis — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/diagnosis/__init__.py"
  - "src/learnloop/diagnosis/ai_contracts.py"
  - "src/learnloop/diagnosis/calibration_sessions.py"
  - "src/learnloop/diagnosis/causal_activity_policy.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/causal_diagnostic_selector.py"
  - "src/learnloop/diagnosis/causal_factor_deferral.py"
  - "src/learnloop/diagnosis/causal_health.py"
  - "src/learnloop/diagnosis/causal_orchestrator.py"
  - "src/learnloop/diagnosis/causal_probe_coherence.py"
  - "src/learnloop/diagnosis/causal_probe_commissioning.py"
  - "src/learnloop/diagnosis/causal_selection_audit.py"
  - "src/learnloop/diagnosis/chain_records.py"
  - "src/learnloop/diagnosis/contrast_pairs.py"
  - "src/learnloop/diagnosis/diagnosis_adjudication.py"
  - "src/learnloop/diagnosis/diagnostic_augmentation.py"
  - "src/learnloop/diagnosis/diagnostic_gate.py"
  - "src/learnloop/diagnosis/diagnostic_pack.py"
  - "src/learnloop/diagnosis/diagnostic_surface_supply.py"
  - "src/learnloop/diagnosis/discrimination_profiles.py"
  - "src/learnloop/diagnosis/error_hunt.py"
  - "src/learnloop/diagnosis/error_taxonomy.py"
  - "src/learnloop/diagnosis/error_taxonomy_map.py"
  - "src/learnloop/diagnosis/failure_triage.py"
  - "src/learnloop/diagnosis/followups.py"
  - "src/learnloop/diagnosis/forecast_receipts.py"
  - "src/learnloop/diagnosis/gate_fit.py"
  - "src/learnloop/diagnosis/gate_score.py"
  - "src/learnloop/diagnosis/grading_hardcases.py"
  - "src/learnloop/diagnosis/guided_redo.py"
  - "src/learnloop/diagnosis/longform_trace.py"
  - "src/learnloop/diagnosis/misconceptions.py"
  - "src/learnloop/diagnosis/missing_vocabulary.py"
  - "src/learnloop/diagnosis/predictive_eig.py"
  - "src/learnloop/diagnosis/probe_audit.py"
  - "src/learnloop/diagnosis/probe_blocks.py"
  - "src/learnloop/diagnosis/probe_coverage.py"
  - "src/learnloop/diagnosis/probe_dialogue.py"
  - "src/learnloop/diagnosis/probe_episodes.py"
  - "src/learnloop/diagnosis/probe_families.py"
  - "src/learnloop/diagnosis/probe_hypotheses.py"
  - "src/learnloop/diagnosis/probe_instance_generation.py"
  - "src/learnloop/diagnosis/probe_lifecycle.py"
  - "src/learnloop/diagnosis/probe_outcome_mapping.py"
  - "src/learnloop/diagnosis/probe_remint.py"
  - "src/learnloop/diagnosis/probe_robust.py"
  - "src/learnloop/diagnosis/probe_targeting.py"
  - "src/learnloop/diagnosis/probes.py"
  - "src/learnloop/diagnosis/quick_check.py"
  - "src/learnloop/diagnosis/remediation.py"
  - "src/learnloop/diagnosis/repair_splice.py"
  - "src/learnloop/diagnosis/robust_composition.py"
  - "src/learnloop/diagnosis/scoreboard.py"
  - "src/learnloop/diagnosis/signal_quantiles.py"
  - "src/learnloop/diagnosis/taxonomy_regrade.py"
  - "src/learnloop/diagnosis/voi_forecasting.py"
  - "src/learnloop/diagnosis/voi_stopping.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Process Model Output"
tags:
  - "docs/package-map"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

Diagnostic probes, causal attribution, error classification, and remediation decisions.

For system intent, use [[Learning System]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop/diagnosis/__init__|learnloop.diagnosis]] | [[Reference/Modules/learnloop/diagnosis/__init__#^module-purpose|purpose]] | `ACTIVE` | 0 | 0 |
| [[Reference/Modules/learnloop/diagnosis/ai_contracts|learnloop.diagnosis.ai_contracts]] | [[Reference/Modules/learnloop/diagnosis/ai_contracts#^module-purpose|purpose]] | `ACTIVE` | 7 | 14 |
| [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]] | [[Reference/Modules/learnloop/diagnosis/calibration_sessions#^module-purpose|purpose]] | `ACTIVE` | 6 | 9 |
| [[Reference/Modules/learnloop/diagnosis/causal_activity_policy|learnloop.diagnosis.causal_activity_policy]] | [[Reference/Modules/learnloop/diagnosis/causal_activity_policy#^module-purpose|purpose]] | `ACTIVE` | 10 | 9 |
| [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] | [[Reference/Modules/learnloop/diagnosis/causal_attribution#^module-purpose|purpose]] | `ACTIVE` | 27 | 19 |
| [[Reference/Modules/learnloop/diagnosis/causal_diagnostic_selector|learnloop.diagnosis.causal_diagnostic_selector]] | [[Reference/Modules/learnloop/diagnosis/causal_diagnostic_selector#^module-purpose|purpose]] | `EVALUATION` | 3 | 2 |
| [[Reference/Modules/learnloop/diagnosis/causal_factor_deferral|learnloop.diagnosis.causal_factor_deferral]] | [[Reference/Modules/learnloop/diagnosis/causal_factor_deferral#^module-purpose|purpose]] | `ACTIVE` | 4 | 3 |
| [[Reference/Modules/learnloop/diagnosis/causal_health|learnloop.diagnosis.causal_health]] | [[Reference/Modules/learnloop/diagnosis/causal_health#^module-purpose|purpose]] | `ACTIVE` | 2 | 1 |
| [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] | [[Reference/Modules/learnloop/diagnosis/causal_orchestrator#^module-purpose|purpose]] | `ACTIVE` | 9 | 24 |
| [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] | [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence#^module-purpose|purpose]] | `ACTIVE` | 15 | 17 |
| [[Reference/Modules/learnloop/diagnosis/causal_probe_commissioning|learnloop.diagnosis.causal_probe_commissioning]] | [[Reference/Modules/learnloop/diagnosis/causal_probe_commissioning#^module-purpose|purpose]] | `ACTIVE` | 2 | 4 |
| [[Reference/Modules/learnloop/diagnosis/causal_selection_audit|learnloop.diagnosis.causal_selection_audit]] | [[Reference/Modules/learnloop/diagnosis/causal_selection_audit#^module-purpose|purpose]] | `EVALUATION` | 2 | 1 |
| [[Reference/Modules/learnloop/diagnosis/chain_records|learnloop.diagnosis.chain_records]] | [[Reference/Modules/learnloop/diagnosis/chain_records#^module-purpose|purpose]] | `ACTIVE` | 5 | 2 |
| [[Reference/Modules/learnloop/diagnosis/contrast_pairs|learnloop.diagnosis.contrast_pairs]] | [[Reference/Modules/learnloop/diagnosis/contrast_pairs#^module-purpose|purpose]] | `ACTIVE` | 5 | 4 |
| [[Reference/Modules/learnloop/diagnosis/diagnosis_adjudication|learnloop.diagnosis.diagnosis_adjudication]] | [[Reference/Modules/learnloop/diagnosis/diagnosis_adjudication#^module-purpose|purpose]] | `ACTIVE` | 5 | 5 |
| [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]] | [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation#^module-purpose|purpose]] | `ACTIVE` | 6 | 2 |
| [[Reference/Modules/learnloop/diagnosis/diagnostic_gate|learnloop.diagnosis.diagnostic_gate]] | [[Reference/Modules/learnloop/diagnosis/diagnostic_gate#^module-purpose|purpose]] | `ACTIVE` | 9 | 4 |
| [[Reference/Modules/learnloop/diagnosis/diagnostic_pack|learnloop.diagnosis.diagnostic_pack]] | [[Reference/Modules/learnloop/diagnosis/diagnostic_pack#^module-purpose|purpose]] | `ACTIVE` | 2 | 5 |
| [[Reference/Modules/learnloop/diagnosis/diagnostic_surface_supply|learnloop.diagnosis.diagnostic_surface_supply]] | [[Reference/Modules/learnloop/diagnosis/diagnostic_surface_supply#^module-purpose|purpose]] | `ACTIVE` | 2 | 5 |
| [[Reference/Modules/learnloop/diagnosis/discrimination_profiles|learnloop.diagnosis.discrimination_profiles]] | [[Reference/Modules/learnloop/diagnosis/discrimination_profiles#^module-purpose|purpose]] | `ACTIVE` | 6 | 1 |
| [[Reference/Modules/learnloop/diagnosis/error_hunt|learnloop.diagnosis.error_hunt]] | [[Reference/Modules/learnloop/diagnosis/error_hunt#^module-purpose|purpose]] | `ACTIVE` | 4 | 1 |
| [[Reference/Modules/learnloop/diagnosis/error_taxonomy|learnloop.diagnosis.error_taxonomy]] | [[Reference/Modules/learnloop/diagnosis/error_taxonomy#^module-purpose|purpose]] | `ACTIVE` | 2 | 1 |
| [[Reference/Modules/learnloop/diagnosis/error_taxonomy_map|learnloop.diagnosis.error_taxonomy_map]] | [[Reference/Modules/learnloop/diagnosis/error_taxonomy_map#^module-purpose|purpose]] | `ACTIVE` | 8 | 4 |
| [[Reference/Modules/learnloop/diagnosis/failure_triage|learnloop.diagnosis.failure_triage]] | [[Reference/Modules/learnloop/diagnosis/failure_triage#^module-purpose|purpose]] | `ACTIVE` | 0 | 5 |
| [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] | [[Reference/Modules/learnloop/diagnosis/followups#^module-purpose|purpose]] | `ACTIVE` | 10 | 26 |
| [[Reference/Modules/learnloop/diagnosis/forecast_receipts|learnloop.diagnosis.forecast_receipts]] | [[Reference/Modules/learnloop/diagnosis/forecast_receipts#^module-purpose|purpose]] | `ACTIVE` | 3 | 1 |
| [[Reference/Modules/learnloop/diagnosis/gate_fit|learnloop.diagnosis.gate_fit]] | [[Reference/Modules/learnloop/diagnosis/gate_fit#^module-purpose|purpose]] | `ACTIVE` | 1 | 2 |
| [[Reference/Modules/learnloop/diagnosis/gate_score|learnloop.diagnosis.gate_score]] | [[Reference/Modules/learnloop/diagnosis/gate_score#^module-purpose|purpose]] | `ACTIVE` | 3 | 3 |
| [[Reference/Modules/learnloop/diagnosis/grading_hardcases|learnloop.diagnosis.grading_hardcases]] | [[Reference/Modules/learnloop/diagnosis/grading_hardcases#^module-purpose|purpose]] | `ACTIVE` | 1 | 2 |
| [[Reference/Modules/learnloop/diagnosis/guided_redo|learnloop.diagnosis.guided_redo]] | [[Reference/Modules/learnloop/diagnosis/guided_redo#^module-purpose|purpose]] | `ACTIVE` | 5 | 1 |
| [[Reference/Modules/learnloop/diagnosis/longform_trace|learnloop.diagnosis.longform_trace]] | [[Reference/Modules/learnloop/diagnosis/longform_trace#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] | [[Reference/Modules/learnloop/diagnosis/misconceptions#^module-purpose|purpose]] | `ACTIVE` | 10 | 9 |
| [[Reference/Modules/learnloop/diagnosis/missing_vocabulary|learnloop.diagnosis.missing_vocabulary]] | [[Reference/Modules/learnloop/diagnosis/missing_vocabulary#^module-purpose|purpose]] | `ACTIVE` | 4 | 1 |
| [[Reference/Modules/learnloop/diagnosis/predictive_eig|learnloop.diagnosis.predictive_eig]] | [[Reference/Modules/learnloop/diagnosis/predictive_eig#^module-purpose|purpose]] | `ACTIVE` | 1 | 2 |
| [[Reference/Modules/learnloop/diagnosis/probe_audit|learnloop.diagnosis.probe_audit]] | [[Reference/Modules/learnloop/diagnosis/probe_audit#^module-purpose|purpose]] | `ACTIVE` | 3 | 5 |
| [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]] | [[Reference/Modules/learnloop/diagnosis/probe_blocks#^module-purpose|purpose]] | `ACTIVE` | 3 | 1 |
| [[Reference/Modules/learnloop/diagnosis/probe_coverage|learnloop.diagnosis.probe_coverage]] | [[Reference/Modules/learnloop/diagnosis/probe_coverage#^module-purpose|purpose]] | `ACTIVE` | 1 | 2 |
| [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]] | [[Reference/Modules/learnloop/diagnosis/probe_dialogue#^module-purpose|purpose]] | `ACTIVE` | 1 | 3 |
| [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] | [[Reference/Modules/learnloop/diagnosis/probe_episodes#^module-purpose|purpose]] | `ACTIVE` | 21 | 60 |
| [[Reference/Modules/learnloop/diagnosis/probe_families|learnloop.diagnosis.probe_families]] | [[Reference/Modules/learnloop/diagnosis/probe_families#^module-purpose|purpose]] | `ACTIVE` | 17 | 23 |
| [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] | [[Reference/Modules/learnloop/diagnosis/probe_hypotheses#^module-purpose|purpose]] | `ACTIVE` | 14 | 10 |
| [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] | [[Reference/Modules/learnloop/diagnosis/probe_instance_generation#^module-purpose|purpose]] | `ACTIVE` | 11 | 9 |
| [[Reference/Modules/learnloop/diagnosis/probe_lifecycle|learnloop.diagnosis.probe_lifecycle]] | [[Reference/Modules/learnloop/diagnosis/probe_lifecycle#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/diagnosis/probe_outcome_mapping|learnloop.diagnosis.probe_outcome_mapping]] | [[Reference/Modules/learnloop/diagnosis/probe_outcome_mapping#^module-purpose|purpose]] | `ACTIVE` | 2 | 1 |
| [[Reference/Modules/learnloop/diagnosis/probe_remint|learnloop.diagnosis.probe_remint]] | [[Reference/Modules/learnloop/diagnosis/probe_remint#^module-purpose|purpose]] | `ACTIVE` | 1 | 3 |
| [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]] | [[Reference/Modules/learnloop/diagnosis/probe_robust#^module-purpose|purpose]] | `ACTIVE` | 5 | 5 |
| [[Reference/Modules/learnloop/diagnosis/probe_targeting|learnloop.diagnosis.probe_targeting]] | [[Reference/Modules/learnloop/diagnosis/probe_targeting#^module-purpose|purpose]] | `ACTIVE` | 2 | 3 |
| [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] | [[Reference/Modules/learnloop/diagnosis/probes#^module-purpose|purpose]] | `ACTIVE` | 16 | 15 |
| [[Reference/Modules/learnloop/diagnosis/quick_check|learnloop.diagnosis.quick_check]] | [[Reference/Modules/learnloop/diagnosis/quick_check#^module-purpose|purpose]] | `ACTIVE` | 2 | 3 |
| [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] | [[Reference/Modules/learnloop/diagnosis/remediation#^module-purpose|purpose]] | `ACTIVE` | 15 | 28 |
| [[Reference/Modules/learnloop/diagnosis/repair_splice|learnloop.diagnosis.repair_splice]] | [[Reference/Modules/learnloop/diagnosis/repair_splice#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/diagnosis/robust_composition|learnloop.diagnosis.robust_composition]] | [[Reference/Modules/learnloop/diagnosis/robust_composition#^module-purpose|purpose]] | `ACTIVE` | 14 | 12 |
| [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] | [[Reference/Modules/learnloop/diagnosis/scoreboard#^module-purpose|purpose]] | `ACTIVE` | 7 | 5 |
| [[Reference/Modules/learnloop/diagnosis/signal_quantiles|learnloop.diagnosis.signal_quantiles]] | [[Reference/Modules/learnloop/diagnosis/signal_quantiles#^module-purpose|purpose]] | `ACTIVE` | 2 | 2 |
| [[Reference/Modules/learnloop/diagnosis/taxonomy_regrade|learnloop.diagnosis.taxonomy_regrade]] | [[Reference/Modules/learnloop/diagnosis/taxonomy_regrade#^module-purpose|purpose]] | `ACTIVE` | 1 | 2 |
| [[Reference/Modules/learnloop/diagnosis/voi_forecasting|learnloop.diagnosis.voi_forecasting]] | [[Reference/Modules/learnloop/diagnosis/voi_forecasting#^module-purpose|purpose]] | `ACTIVE` | 4 | 2 |
| [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]] | [[Reference/Modules/learnloop/diagnosis/voi_stopping#^module-purpose|purpose]] | `ACTIVE` | 8 | 8 |

## Child package maps

- [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] — The offline review of blind grading and history-aware diagnosis, run on backup copies with synthetic learners; never changes a live vault.
- [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] — Recurrence with authority: the same_cause match kind over causal hypotheses, its shortlist and judge, the live step and the backlog.
- [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] — History-aware diagnosis split from the learner-blind grader: history modes, the diagnoser's inputs, jobs and traces.
- [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] — Learner-text gaps: what a learner's own words show they lack or hold, read in tiers, judged in pairs, acted on with undo, and reported.

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/_package|learnloop]] — 79 static module edges
- [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] — 52 static module edges
- [[Reference/Modules/learnloop/db/_package|learnloop.db]] — 48 static module edges
- [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] — 26 static module edges
- [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] — 22 static module edges
- [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] — 20 static module edges
- [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] — 17 static module edges
- [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] — 12 static module edges
- [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] — 11 static module edges
- [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] — 8 static module edges
- [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] — 7 static module edges
- [[Reference/Modules/learnloop/config/_package|learnloop.config]] — 6 static module edges
- [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] — 5 static module edges
- [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] — 3 static module edges
- [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] — 3 static module edges
- [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] — 2 static module edges
- [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] — 2 static module edges
- [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] — 2 static module edges
- [[Reference/Modules/learnloop/data_capture/_package|learnloop.data_capture]] — 2 static module edges
- [[Reference/Modules/learnloop/params/_package|learnloop.params]] — 2 static module edges
- [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] — 1 static module edge
- [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] — 1 static module edge
- [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] — 1 static module edge
- [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] — 1 static module edge
- [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] — 1 static module edge
- [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] — 1 static module edge
- [[Reference/Modules/learnloop/router/_package|learnloop.router]] — 1 static module edge
- [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] — 1 static module edge

### Packages that import this package

- [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] — 29 static module edges
- [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] — 25 static module edges
- [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] — 20 static module edges
- [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] — 19 static module edges
- [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] — 12 static module edges
- [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] — 12 static module edges
- [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] — 9 static module edges
- [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] — 9 static module edges
- [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] — 8 static module edges
- [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] — 6 static module edges
- [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] — 5 static module edges
- [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] — 5 static module edges
- [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] — 5 static module edges
- [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] — 4 static module edges
- [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] — 3 static module edges
- [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] — 3 static module edges
- [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] — 3 static module edges
- [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] — 3 static module edges
- [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] — 2 static module edges
- [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] — 2 static module edges
- [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] — 2 static module edges
- [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] — 2 static module edges
- [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] — 2 static module edges
- [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] — 2 static module edges
- [[Reference/Modules/learnloop/field/_package|learnloop.field]] — 1 static module edge
- [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] — 1 static module edge
- [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] — 1 static module edge
- [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] — 1 static module edge
- [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] — 1 static module edge

### Dependency neighborhood

This diagram compresses package-level static imports; edge labels are distinct module-to-module import counts.

```mermaid
flowchart LR
    center["learnloop.diagnosis"]
    n_learnloop["learnloop"]
    n_learnloop_vault["learnloop.vault"]
    n_learnloop_db["learnloop.db"]
    n_learnloop_attempts["learnloop.attempts"]
    n_learnloop_sidecar_handlers["learnloop_sidecar.handlers"]
    n_learnloop_substrate["learnloop.substrate"]
    n_learnloop_cli["learnloop.cli"]
    n_learnloop_learner["learnloop.learner"]
    n_learnloop_scheduling["learnloop.scheduling"]
    n_learnloop_followup_run["learnloop.followup_run"]
    center -->|79| n_learnloop
    center -->|52| n_learnloop_vault
    center -->|48| n_learnloop_db
    n_learnloop_attempts -->|20| center
    center -->|26| n_learnloop_attempts
    n_learnloop_sidecar_handlers -->|29| center
    n_learnloop_substrate -->|5| center
    center -->|22| n_learnloop_substrate
    n_learnloop_cli -->|25| center
    n_learnloop_learner -->|5| center
    center -->|20| n_learnloop_learner
    n_learnloop_scheduling -->|9| center
    center -->|12| n_learnloop_scheduling
    n_learnloop_followup_run -->|19| center
```

Interpretation: arrow direction is static import direction and the label is the number of distinct module-to-module edges. It shows coupling pressure, not runtime call frequency or ownership permission.

## Workflow entry points

- [[Start a Learning Cycle]]
- [[Process Model Output]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/diagnosis" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
