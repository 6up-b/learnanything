---
title: "learnloop.scheduling — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/scheduling/__init__.py"
  - "src/learnloop/scheduling/action_loss.py"
  - "src/learnloop/scheduling/constraint_engine.py"
  - "src/learnloop/scheduling/controller_actions.py"
  - "src/learnloop/scheduling/controller_ownership.py"
  - "src/learnloop/scheduling/controller_snapshot.py"
  - "src/learnloop/scheduling/controller_store.py"
  - "src/learnloop/scheduling/decay_pressure.py"
  - "src/learnloop/scheduling/device_eligibility.py"
  - "src/learnloop/scheduling/dispersion.py"
  - "src/learnloop/scheduling/evaluation.py"
  - "src/learnloop/scheduling/evsi.py"
  - "src/learnloop/scheduling/family_memory_model.py"
  - "src/learnloop/scheduling/forecast_receipts.py"
  - "src/learnloop/scheduling/frame_constraints.py"
  - "src/learnloop/scheduling/fsrs.py"
  - "src/learnloop/scheduling/fsrs_fitting.py"
  - "src/learnloop/scheduling/intent_planner.py"
  - "src/learnloop/scheduling/interleaving.py"
  - "src/learnloop/scheduling/kinship_feature.py"
  - "src/learnloop/scheduling/open_world_gate.py"
  - "src/learnloop/scheduling/randomization_layer.py"
  - "src/learnloop/scheduling/reentry_summary.py"
  - "src/learnloop/scheduling/review_log.py"
  - "src/learnloop/scheduling/scheduler.py"
  - "src/learnloop/scheduling/selection_rewards.py"
  - "src/learnloop/scheduling/serving_exclusions.py"
  - "src/learnloop/scheduling/session_minutes.py"
  - "src/learnloop/scheduling/shadow_components.py"
  - "src/learnloop/scheduling/slate_record.py"
  - "src/learnloop/scheduling/staged_policy.py"
  - "src/learnloop/scheduling/unresolved_cost.py"
  - "src/learnloop/scheduling/voi_forecasts.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
tags:
  - "docs/package-map"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

Selection, review timing, progression, controller decisions, and scheduling projections.

For system intent, use [[Learning System]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop/scheduling/__init__|learnloop.scheduling]] | [[Reference/Modules/learnloop/scheduling/__init__#^module-purpose|purpose]] | `ACTIVE` | 0 | 0 |
| [[Reference/Modules/learnloop/scheduling/action_loss|learnloop.scheduling.action_loss]] | [[Reference/Modules/learnloop/scheduling/action_loss#^module-purpose|purpose]] | `ACTIVE` | 9 | 10 |
| [[Reference/Modules/learnloop/scheduling/constraint_engine|learnloop.scheduling.constraint_engine]] | [[Reference/Modules/learnloop/scheduling/constraint_engine#^module-purpose|purpose]] | `ACTIVE` | 3 | 7 |
| [[Reference/Modules/learnloop/scheduling/controller_actions|learnloop.scheduling.controller_actions]] | [[Reference/Modules/learnloop/scheduling/controller_actions#^module-purpose|purpose]] | `ACTIVE` | 3 | 3 |
| [[Reference/Modules/learnloop/scheduling/controller_ownership|learnloop.scheduling.controller_ownership]] | [[Reference/Modules/learnloop/scheduling/controller_ownership#^module-purpose|purpose]] | `ACTIVE` | 3 | 4 |
| [[Reference/Modules/learnloop/scheduling/controller_snapshot|learnloop.scheduling.controller_snapshot]] | [[Reference/Modules/learnloop/scheduling/controller_snapshot#^module-purpose|purpose]] | `ACTIVE` | 5 | 15 |
| [[Reference/Modules/learnloop/scheduling/controller_store|learnloop.scheduling.controller_store]] | [[Reference/Modules/learnloop/scheduling/controller_store#^module-purpose|purpose]] | `ACTIVE` | 4 | 4 |
| [[Reference/Modules/learnloop/scheduling/decay_pressure|learnloop.scheduling.decay_pressure]] | [[Reference/Modules/learnloop/scheduling/decay_pressure#^module-purpose|purpose]] | `ACTIVE` | 2 | 1 |
| [[Reference/Modules/learnloop/scheduling/device_eligibility|learnloop.scheduling.device_eligibility]] | [[Reference/Modules/learnloop/scheduling/device_eligibility#^module-purpose|purpose]] | `ACTIVE` | 6 | 12 |
| [[Reference/Modules/learnloop/scheduling/dispersion|learnloop.scheduling.dispersion]] | [[Reference/Modules/learnloop/scheduling/dispersion#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/scheduling/evaluation|learnloop.scheduling.evaluation]] | [[Reference/Modules/learnloop/scheduling/evaluation#^module-purpose|purpose]] | `ACTIVE` | 1 | 3 |
| [[Reference/Modules/learnloop/scheduling/evsi|learnloop.scheduling.evsi]] | [[Reference/Modules/learnloop/scheduling/evsi#^module-purpose|purpose]] | `ACTIVE` | 9 | 4 |
| [[Reference/Modules/learnloop/scheduling/family_memory_model|learnloop.scheduling.family_memory_model]] | [[Reference/Modules/learnloop/scheduling/family_memory_model#^module-purpose|purpose]] | `ACTIVE` | 3 | 1 |
| [[Reference/Modules/learnloop/scheduling/forecast_receipts|learnloop.scheduling.forecast_receipts]] | [[Reference/Modules/learnloop/scheduling/forecast_receipts#^module-purpose|purpose]] | `ACTIVE` | 13 | 8 |
| [[Reference/Modules/learnloop/scheduling/frame_constraints|learnloop.scheduling.frame_constraints]] | [[Reference/Modules/learnloop/scheduling/frame_constraints#^module-purpose|purpose]] | `ACTIVE` | 2 | 3 |
| [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] | [[Reference/Modules/learnloop/scheduling/fsrs#^module-purpose|purpose]] | `ACTIVE` | 26 | 29 |
| [[Reference/Modules/learnloop/scheduling/fsrs_fitting|learnloop.scheduling.fsrs_fitting]] | [[Reference/Modules/learnloop/scheduling/fsrs_fitting#^module-purpose|purpose]] | `ACTIVE` | 1 | 2 |
| [[Reference/Modules/learnloop/scheduling/intent_planner|learnloop.scheduling.intent_planner]] | [[Reference/Modules/learnloop/scheduling/intent_planner#^module-purpose|purpose]] | `EVALUATION` | 1 | 1 |
| [[Reference/Modules/learnloop/scheduling/interleaving|learnloop.scheduling.interleaving]] | [[Reference/Modules/learnloop/scheduling/interleaving#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/scheduling/kinship_feature|learnloop.scheduling.kinship_feature]] | [[Reference/Modules/learnloop/scheduling/kinship_feature#^module-purpose|purpose]] | `DORMANT` | 1 | 2 |
| [[Reference/Modules/learnloop/scheduling/open_world_gate|learnloop.scheduling.open_world_gate]] | [[Reference/Modules/learnloop/scheduling/open_world_gate#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/scheduling/randomization_layer|learnloop.scheduling.randomization_layer]] | [[Reference/Modules/learnloop/scheduling/randomization_layer#^module-purpose|purpose]] | `ACTIVE` | 5 | 4 |
| [[Reference/Modules/learnloop/scheduling/reentry_summary|learnloop.scheduling.reentry_summary]] | [[Reference/Modules/learnloop/scheduling/reentry_summary#^module-purpose|purpose]] | `ACTIVE` | 4 | 3 |
| [[Reference/Modules/learnloop/scheduling/review_log|learnloop.scheduling.review_log]] | [[Reference/Modules/learnloop/scheduling/review_log#^module-purpose|purpose]] | `ACTIVE` | 3 | 3 |
| [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] | [[Reference/Modules/learnloop/scheduling/scheduler#^module-purpose|purpose]] | `ACTIVE` | 20 | 96 |
| [[Reference/Modules/learnloop/scheduling/selection_rewards|learnloop.scheduling.selection_rewards]] | [[Reference/Modules/learnloop/scheduling/selection_rewards#^module-purpose|purpose]] | `ACTIVE` | 5 | 8 |
| [[Reference/Modules/learnloop/scheduling/serving_exclusions|learnloop.scheduling.serving_exclusions]] | [[Reference/Modules/learnloop/scheduling/serving_exclusions#^module-purpose|purpose]] | `ACTIVE` | 5 | 16 |
| [[Reference/Modules/learnloop/scheduling/session_minutes|learnloop.scheduling.session_minutes]] | [[Reference/Modules/learnloop/scheduling/session_minutes#^module-purpose|purpose]] | `ACTIVE` | 3 | 1 |
| [[Reference/Modules/learnloop/scheduling/shadow_components|learnloop.scheduling.shadow_components]] | [[Reference/Modules/learnloop/scheduling/shadow_components#^module-purpose|purpose]] | `EVALUATION` | 1 | 1 |
| [[Reference/Modules/learnloop/scheduling/slate_record|learnloop.scheduling.slate_record]] | [[Reference/Modules/learnloop/scheduling/slate_record#^module-purpose|purpose]] | `ACTIVE` | 2 | 3 |
| [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]] | [[Reference/Modules/learnloop/scheduling/staged_policy#^module-purpose|purpose]] | `ACTIVE` | 5 | 11 |
| [[Reference/Modules/learnloop/scheduling/unresolved_cost|learnloop.scheduling.unresolved_cost]] | [[Reference/Modules/learnloop/scheduling/unresolved_cost#^module-purpose|purpose]] | `ACTIVE` | 3 | 2 |
| [[Reference/Modules/learnloop/scheduling/voi_forecasts|learnloop.scheduling.voi_forecasts]] | [[Reference/Modules/learnloop/scheduling/voi_forecasts#^module-purpose|purpose]] | `ACTIVE` | 8 | 2 |

## Child package maps

- [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] — Intent at serving time: the vocabulary, the most-recent-choice resolution, per-intent recall targets and the per-build view.

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/_package|learnloop]] — 37 static module edges
- [[Reference/Modules/learnloop/db/_package|learnloop.db]] — 22 static module edges
- [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] — 15 static module edges
- [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] — 12 static module edges
- [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] — 9 static module edges
- [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] — 9 static module edges
- [[Reference/Modules/learnloop/params/_package|learnloop.params]] — 7 static module edges
- [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] — 6 static module edges
- [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] — 5 static module edges
- [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] — 4 static module edges
- [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] — 4 static module edges
- [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] — 3 static module edges
- [[Reference/Modules/learnloop/config/_package|learnloop.config]] — 2 static module edges
- [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] — 2 static module edges
- [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] — 1 static module edge
- [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] — 1 static module edge
- [[Reference/Modules/learnloop/router/_package|learnloop.router]] — 1 static module edge
- [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] — 1 static module edge
- [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] — 1 static module edge

### Packages that import this package

- [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] — 15 static module edges
- [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] — 13 static module edges
- [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] — 12 static module edges
- [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] — 11 static module edges
- [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] — 10 static module edges
- [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] — 9 static module edges
- [[Reference/Modules/learnloop/field/_package|learnloop.field]] — 5 static module edges
- [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] — 5 static module edges
- [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] — 4 static module edges
- [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] — 4 static module edges
- [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] — 4 static module edges
- [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] — 3 static module edges
- [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] — 3 static module edges
- [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] — 3 static module edges
- [[Reference/Modules/learnloop/_package|learnloop]] — 2 static module edges
- [[Reference/Modules/learnloop/tui/_package|learnloop.tui]] — 2 static module edges
- [[Reference/Modules/learnloop/why/_package|learnloop.why]] — 2 static module edges
- [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] — 2 static module edges
- [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] — 1 static module edge
- [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] — 1 static module edge
- [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] — 1 static module edge
- [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] — 1 static module edge
- [[Reference/Modules/learnloop/params/_package|learnloop.params]] — 1 static module edge
- [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] — 1 static module edge
- [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] — 1 static module edge
- [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] — 1 static module edge

### Dependency neighborhood

This diagram compresses package-level static imports; edge labels are distinct module-to-module import counts.

```mermaid
flowchart LR
    center["learnloop.scheduling"]
    n_learnloop["learnloop"]
    n_learnloop_db["learnloop.db"]
    n_learnloop_diagnosis["learnloop.diagnosis"]
    n_learnloop_substrate["learnloop.substrate"]
    n_learnloop_sidecar_handlers["learnloop_sidecar.handlers"]
    n_learnloop_daily_plan["learnloop.daily_plan"]
    n_learnloop_vault["learnloop.vault"]
    n_learnloop_adaptive_difficulty["learnloop.adaptive_difficulty"]
    n_learnloop_evsi_calibration["learnloop.evsi_calibration"]
    n_learnloop_learner["learnloop.learner"]
    n_learnloop -->|2| center
    center -->|37| n_learnloop
    center -->|22| n_learnloop_db
    n_learnloop_diagnosis -->|12| center
    center -->|9| n_learnloop_diagnosis
    n_learnloop_substrate -->|4| center
    center -->|15| n_learnloop_substrate
    n_learnloop_sidecar_handlers -->|15| center
    n_learnloop_daily_plan -->|13| center
    center -->|12| n_learnloop_vault
    n_learnloop_adaptive_difficulty -->|11| center
    n_learnloop_evsi_calibration -->|10| center
    n_learnloop_learner -->|1| center
    center -->|9| n_learnloop_learner
```

Interpretation: arrow direction is static import direction and the label is the number of distinct module-to-module edges. It shows coupling pressure, not runtime call frequency or ownership permission.

## Workflow entry points

- [[Start a Learning Cycle]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/scheduling" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
