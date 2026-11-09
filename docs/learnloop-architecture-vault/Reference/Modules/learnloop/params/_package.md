---
title: "learnloop.params — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/params/__init__.py"
  - "src/learnloop/params/fitted_params.py"
  - "src/learnloop/params/parameter_registry.py"
  - "src/learnloop/params/sensitivity_certificates.py"
source_commit: "aggregate; see module notes"
source_commit_timestamp: "2026-11-09T15:29:00-05:00"
generated: true
generated_at: "2026-11-02"
package: "learnloop.params"
layer: "domain"
concepts:
  - "Learning System"
  - "Configuration"
workflows:
  - "Start a Learning Cycle"
tags:
  - "docs/package-map"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-params"
---

# `learnloop.params` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

Algorithm parameter registry, fitted values, and sensitivity certificates.

For system intent, use [[Learning System]], [[Configuration]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop/params/__init__|learnloop.params]] | [[Reference/Modules/learnloop/params/__init__#^module-purpose|purpose]] | `ACTIVE` | 0 | 0 |
| [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] | [[Reference/Modules/learnloop/params/fitted_params#^module-purpose|purpose]] | `ACTIVE` | 24 | 8 |
| [[Reference/Modules/learnloop/params/parameter_registry|learnloop.params.parameter_registry]] | [[Reference/Modules/learnloop/params/parameter_registry#^module-purpose|purpose]] | `ACTIVE` | 49 | 52 |
| [[Reference/Modules/learnloop/params/sensitivity_certificates|learnloop.params.sensitivity_certificates]] | [[Reference/Modules/learnloop/params/sensitivity_certificates#^module-purpose|purpose]] | `ACTIVE` | 3 | 1 |

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/db/_package|learnloop.db]] — 3 static module edges
- [[Reference/Modules/learnloop/_package|learnloop]] — 2 static module edges
- [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] — 2 static module edges
- [[Reference/Modules/learnloop/config/_package|learnloop.config]] — 1 static module edge
- [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] — 1 static module edge
- [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] — 1 static module edge
- [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] — 1 static module edge

### Packages that import this package

- [[Reference/Modules/learnloop/_package|learnloop]] — 43 static module edges
- [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] — 7 static module edges
- [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] — 4 static module edges
- [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] — 4 static module edges
- [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] — 4 static module edges
- [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] — 2 static module edges
- [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] — 2 static module edges
- [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] — 1 static module edge
- [[Reference/Modules/learnloop/field/_package|learnloop.field]] — 1 static module edge
- [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] — 1 static module edge
- [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] — 1 static module edge
- [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] — 1 static module edge
- [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] — 1 static module edge
- [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] — 1 static module edge
- [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] — 1 static module edge
- [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] — 1 static module edge

### Dependency neighborhood

This diagram compresses package-level static imports; edge labels are distinct module-to-module import counts.

```mermaid
flowchart LR
    center["learnloop.params"]
    n_learnloop["learnloop"]
    n_learnloop_scheduling["learnloop.scheduling"]
    n_learnloop_attempts["learnloop.attempts"]
    n_learnloop_cli["learnloop.cli"]
    n_learnloop_daily_plan["learnloop.daily_plan"]
    n_learnloop_db["learnloop.db"]
    n_learnloop_substrate["learnloop.substrate"]
    n_learnloop_diagnosis["learnloop.diagnosis"]
    n_learnloop_goals["learnloop.goals"]
    n_learnloop_config["learnloop.config"]
    n_learnloop -->|43| center
    center -->|2| n_learnloop
    n_learnloop_scheduling -->|7| center
    center -->|1| n_learnloop_scheduling
    n_learnloop_attempts -->|4| center
    n_learnloop_cli -->|4| center
    n_learnloop_daily_plan -->|4| center
    center -->|3| n_learnloop_db
    n_learnloop_substrate -->|1| center
    center -->|2| n_learnloop_substrate
    n_learnloop_diagnosis -->|2| center
    n_learnloop_goals -->|2| center
    center -->|1| n_learnloop_config
```

Interpretation: arrow direction is static import direction and the label is the number of distinct module-to-module edges. It shows coupling pressure, not runtime call frequency or ownership permission.

## Workflow entry points

- [[Start a Learning Cycle]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/params" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
