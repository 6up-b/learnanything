---
title: "learnloop.router_objective — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/router_objective/__init__.py"
  - "src/learnloop/router_objective/ask_availability.py"
  - "src/learnloop/router_objective/assignments.py"
  - "src/learnloop/router_objective/calibration_report.py"
  - "src/learnloop/router_objective/checks.py"
  - "src/learnloop/router_objective/cold_timing.py"
  - "src/learnloop/router_objective/combiner_data.py"
  - "src/learnloop/router_objective/decision_state.py"
  - "src/learnloop/router_objective/exposure.py"
  - "src/learnloop/router_objective/forecast_resolve.py"
  - "src/learnloop/router_objective/goal_lifecycle.py"
  - "src/learnloop/router_objective/goal_read.py"
  - "src/learnloop/router_objective/learned_tail.py"
  - "src/learnloop/router_objective/memory.py"
  - "src/learnloop/router_objective/miss_cause.py"
  - "src/learnloop/router_objective/miss_cause_report.py"
  - "src/learnloop/router_objective/mix.py"
  - "src/learnloop/router_objective/objective_report.py"
  - "src/learnloop/router_objective/offer_report.py"
  - "src/learnloop/router_objective/picks.py"
  - "src/learnloop/router_objective/preference_report.py"
  - "src/learnloop/router_objective/preferences.py"
  - "src/learnloop/router_objective/price.py"
  - "src/learnloop/router_objective/question_state.py"
  - "src/learnloop/router_objective/report.py"
  - "src/learnloop/router_objective/scores.py"
  - "src/learnloop/router_objective/sessions.py"
  - "src/learnloop/router_objective/stop_coin.py"
  - "src/learnloop/router_objective/tail_data.py"
  - "src/learnloop/router_objective/tail_report.py"
  - "src/learnloop/router_objective/tail_serve.py"
  - "src/learnloop/router_objective/trace.py"
  - "src/learnloop/router_objective/trajectory.py"
  - "src/learnloop/router_objective/value.py"
  - "src/learnloop/router_objective/weight.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router_objective"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
tags:
  - "docs/package-map"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router_objective"
---

# `learnloop.router_objective` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

The router objective's logging (spec_router_objective_v1 §4, RO0): additive receipts at every version behind [router_objective] receipts, read by nothing serving, scheduling or certification.

For system intent, use [[Architecture Overview]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop/router_objective/__init__|learnloop.router_objective]] | [[Reference/Modules/learnloop/router_objective/__init__#^module-purpose|purpose]] | `ACTIVE` | 0 | 0 |
| [[Reference/Modules/learnloop/router_objective/ask_availability|learnloop.router_objective.ask_availability]] | [[Reference/Modules/learnloop/router_objective/ask_availability#^module-purpose|purpose]] | `ACTIVE` | 2 | 2 |
| [[Reference/Modules/learnloop/router_objective/assignments|learnloop.router_objective.assignments]] | [[Reference/Modules/learnloop/router_objective/assignments#^module-purpose|purpose]] | `ACTIVE` | 6 | 8 |
| [[Reference/Modules/learnloop/router_objective/calibration_report|learnloop.router_objective.calibration_report]] | [[Reference/Modules/learnloop/router_objective/calibration_report#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/router_objective/checks|learnloop.router_objective.checks]] | [[Reference/Modules/learnloop/router_objective/checks#^module-purpose|purpose]] | `ACTIVE` | 9 | 13 |
| [[Reference/Modules/learnloop/router_objective/cold_timing|learnloop.router_objective.cold_timing]] | [[Reference/Modules/learnloop/router_objective/cold_timing#^module-purpose|purpose]] | `ACTIVE` | 1 | 2 |
| [[Reference/Modules/learnloop/router_objective/combiner_data|learnloop.router_objective.combiner_data]] | [[Reference/Modules/learnloop/router_objective/combiner_data#^module-purpose|purpose]] | `ACTIVE` | 1 | 2 |
| [[Reference/Modules/learnloop/router_objective/decision_state|learnloop.router_objective.decision_state]] | [[Reference/Modules/learnloop/router_objective/decision_state#^module-purpose|purpose]] | `ACTIVE` | 5 | 4 |
| [[Reference/Modules/learnloop/router_objective/exposure|learnloop.router_objective.exposure]] | [[Reference/Modules/learnloop/router_objective/exposure#^module-purpose|purpose]] | `ACTIVE` | 12 | 2 |
| [[Reference/Modules/learnloop/router_objective/forecast_resolve|learnloop.router_objective.forecast_resolve]] | [[Reference/Modules/learnloop/router_objective/forecast_resolve#^module-purpose|purpose]] | `ACTIVE` | 2 | 2 |
| [[Reference/Modules/learnloop/router_objective/goal_lifecycle|learnloop.router_objective.goal_lifecycle]] | [[Reference/Modules/learnloop/router_objective/goal_lifecycle#^module-purpose|purpose]] | `ACTIVE` | 1 | 3 |
| [[Reference/Modules/learnloop/router_objective/goal_read|learnloop.router_objective.goal_read]] | [[Reference/Modules/learnloop/router_objective/goal_read#^module-purpose|purpose]] | `ACTIVE` | 1 | 3 |
| [[Reference/Modules/learnloop/router_objective/learned_tail|learnloop.router_objective.learned_tail]] | [[Reference/Modules/learnloop/router_objective/learned_tail#^module-purpose|purpose]] | `ACTIVE` | 4 | 10 |
| [[Reference/Modules/learnloop/router_objective/memory|learnloop.router_objective.memory]] | [[Reference/Modules/learnloop/router_objective/memory#^module-purpose|purpose]] | `ACTIVE` | 3 | 13 |
| [[Reference/Modules/learnloop/router_objective/miss_cause|learnloop.router_objective.miss_cause]] | [[Reference/Modules/learnloop/router_objective/miss_cause#^module-purpose|purpose]] | `ACTIVE` | 5 | 1 |
| [[Reference/Modules/learnloop/router_objective/miss_cause_report|learnloop.router_objective.miss_cause_report]] | [[Reference/Modules/learnloop/router_objective/miss_cause_report#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/router_objective/mix|learnloop.router_objective.mix]] | [[Reference/Modules/learnloop/router_objective/mix#^module-purpose|purpose]] | `ACTIVE` | 2 | 16 |
| [[Reference/Modules/learnloop/router_objective/objective_report|learnloop.router_objective.objective_report]] | [[Reference/Modules/learnloop/router_objective/objective_report#^module-purpose|purpose]] | `ACTIVE` | 1 | 3 |
| [[Reference/Modules/learnloop/router_objective/offer_report|learnloop.router_objective.offer_report]] | [[Reference/Modules/learnloop/router_objective/offer_report#^module-purpose|purpose]] | `ACTIVE` | 2 | 1 |
| [[Reference/Modules/learnloop/router_objective/picks|learnloop.router_objective.picks]] | [[Reference/Modules/learnloop/router_objective/picks#^module-purpose|purpose]] | `ACTIVE` | 4 | 1 |
| [[Reference/Modules/learnloop/router_objective/preference_report|learnloop.router_objective.preference_report]] | [[Reference/Modules/learnloop/router_objective/preference_report#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/router_objective/preferences|learnloop.router_objective.preferences]] | [[Reference/Modules/learnloop/router_objective/preferences#^module-purpose|purpose]] | `ACTIVE` | 4 | 2 |
| [[Reference/Modules/learnloop/router_objective/price|learnloop.router_objective.price]] | [[Reference/Modules/learnloop/router_objective/price#^module-purpose|purpose]] | `ACTIVE` | 5 | 5 |
| [[Reference/Modules/learnloop/router_objective/question_state|learnloop.router_objective.question_state]] | [[Reference/Modules/learnloop/router_objective/question_state#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/router_objective/report|learnloop.router_objective.report]] | [[Reference/Modules/learnloop/router_objective/report#^module-purpose|purpose]] | `ACTIVE` | 1 | 0 |
| [[Reference/Modules/learnloop/router_objective/scores|learnloop.router_objective.scores]] | [[Reference/Modules/learnloop/router_objective/scores#^module-purpose|purpose]] | `ACTIVE` | 5 | 8 |
| [[Reference/Modules/learnloop/router_objective/sessions|learnloop.router_objective.sessions]] | [[Reference/Modules/learnloop/router_objective/sessions#^module-purpose|purpose]] | `ACTIVE` | 2 | 3 |
| [[Reference/Modules/learnloop/router_objective/stop_coin|learnloop.router_objective.stop_coin]] | [[Reference/Modules/learnloop/router_objective/stop_coin#^module-purpose|purpose]] | `ACTIVE` | 6 | 11 |
| [[Reference/Modules/learnloop/router_objective/tail_data|learnloop.router_objective.tail_data]] | [[Reference/Modules/learnloop/router_objective/tail_data#^module-purpose|purpose]] | `ACTIVE` | 4 | 14 |
| [[Reference/Modules/learnloop/router_objective/tail_report|learnloop.router_objective.tail_report]] | [[Reference/Modules/learnloop/router_objective/tail_report#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/router_objective/tail_serve|learnloop.router_objective.tail_serve]] | [[Reference/Modules/learnloop/router_objective/tail_serve#^module-purpose|purpose]] | `ACTIVE` | 1 | 6 |
| [[Reference/Modules/learnloop/router_objective/trace|learnloop.router_objective.trace]] | [[Reference/Modules/learnloop/router_objective/trace#^module-purpose|purpose]] | `ACTIVE` | 5 | 4 |
| [[Reference/Modules/learnloop/router_objective/trajectory|learnloop.router_objective.trajectory]] | [[Reference/Modules/learnloop/router_objective/trajectory#^module-purpose|purpose]] | `ACTIVE` | 2 | 2 |
| [[Reference/Modules/learnloop/router_objective/value|learnloop.router_objective.value]] | [[Reference/Modules/learnloop/router_objective/value#^module-purpose|purpose]] | `ACTIVE` | 2 | 25 |
| [[Reference/Modules/learnloop/router_objective/weight|learnloop.router_objective.weight]] | [[Reference/Modules/learnloop/router_objective/weight#^module-purpose|purpose]] | `ACTIVE` | 3 | 4 |

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/_package|learnloop]] — 25 static module edges
- [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] — 17 static module edges
- [[Reference/Modules/learnloop/data_capture/_package|learnloop.data_capture]] — 6 static module edges
- [[Reference/Modules/learnloop/router/_package|learnloop.router]] — 5 static module edges
- [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] — 2 static module edges
- [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] — 1 static module edge
- [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] — 1 static module edge
- [[Reference/Modules/learnloop/params/_package|learnloop.params]] — 1 static module edge

### Packages that import this package

- [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] — 29 static module edges
- [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] — 13 static module edges
- [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] — 6 static module edges
- [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] — 4 static module edges
- [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] — 2 static module edges
- [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] — 2 static module edges
- [[Reference/Modules/learnloop/why/_package|learnloop.why]] — 2 static module edges
- [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] — 1 static module edge
- [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] — 1 static module edge
- [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] — 1 static module edge
- [[Reference/Modules/learnloop/recognition/_package|learnloop.recognition]] — 1 static module edge
- [[Reference/Modules/learnloop/remote/_package|learnloop.remote]] — 1 static module edge
- [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] — 1 static module edge
- [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] — 1 static module edge

### Dependency neighborhood

This diagram compresses package-level static imports; edge labels are distinct module-to-module import counts.

```mermaid
flowchart LR
    center["learnloop.router_objective"]
    n_learnloop_daily_plan["learnloop.daily_plan"]
    n_learnloop["learnloop"]
    n_learnloop_db_stores["learnloop.db.stores"]
    n_learnloop_sidecar_handlers["learnloop_sidecar.handlers"]
    n_learnloop_cli["learnloop.cli"]
    n_learnloop_data_capture["learnloop.data_capture"]
    n_learnloop_router["learnloop.router"]
    n_learnloop_ops["learnloop.ops"]
    n_learnloop_followup_run["learnloop.followup_run"]
    n_learnloop_learner["learnloop.learner"]
    n_learnloop_daily_plan -->|29| center
    center -->|25| n_learnloop
    center -->|17| n_learnloop_db_stores
    n_learnloop_sidecar_handlers -->|13| center
    n_learnloop_cli -->|6| center
    center -->|6| n_learnloop_data_capture
    center -->|5| n_learnloop_router
    n_learnloop_ops -->|4| center
    n_learnloop_followup_run -->|2| center
    center -->|2| n_learnloop_learner
```

Interpretation: arrow direction is static import direction and the label is the number of distinct module-to-module edges. It shows coupling pressure, not runtime call frequency or ownership permission.

## Workflow entry points

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/router_objective" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
