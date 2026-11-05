---
title: "learnloop_sidecar — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop_sidecar/__init__.py"
  - "src/learnloop_sidecar/__main__.py"
  - "src/learnloop_sidecar/background_jobs.py"
  - "src/learnloop_sidecar/context.py"
  - "src/learnloop_sidecar/dto.py"
  - "src/learnloop_sidecar/errors.py"
  - "src/learnloop_sidecar/exam_grading.py"
  - "src/learnloop_sidecar/logging.py"
  - "src/learnloop_sidecar/post_attempt_worker.py"
  - "src/learnloop_sidecar/prefetch_runtime.py"
  - "src/learnloop_sidecar/registry.py"
  - "src/learnloop_sidecar/request_origin.py"
  - "src/learnloop_sidecar/server.py"
  - "src/learnloop_sidecar/serving.py"
  - "src/learnloop_sidecar/source_identity.py"
source_commit: "aggregate; see module notes"
source_commit_timestamp: "2026-11-05T12:03:53-05:00"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
tags:
  - "docs/package-map"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop_sidecar"
---

# `learnloop_sidecar` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

Desktop sidecar process, RPC registry, transport context, DTOs, and server lifecycle.

For system intent, use [[Architecture Overview]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop_sidecar/__init__|learnloop_sidecar]] | [[Reference/Modules/learnloop_sidecar/__init__#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop_sidecar/__main__|learnloop_sidecar.__main__]] | [[Reference/Modules/learnloop_sidecar/__main__#^module-purpose|purpose]] | `ACTIVE` | 0 | 0 |
| [[Reference/Modules/learnloop_sidecar/background_jobs|learnloop_sidecar.background_jobs]] | [[Reference/Modules/learnloop_sidecar/background_jobs#^module-purpose|purpose]] | `ACTIVE` | 10 | 4 |
| [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] | [[Reference/Modules/learnloop_sidecar/context#^module-purpose|purpose]] | `ACTIVE` | 76 | 187 |
| [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] | [[Reference/Modules/learnloop_sidecar/dto#^module-purpose|purpose]] | `ACTIVE` | 78 | 12 |
| [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] | [[Reference/Modules/learnloop_sidecar/errors#^module-purpose|purpose]] | `ACTIVE` | 76 | 120 |
| [[Reference/Modules/learnloop_sidecar/exam_grading|learnloop_sidecar.exam_grading]] | [[Reference/Modules/learnloop_sidecar/exam_grading#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop_sidecar/logging|learnloop_sidecar.logging]] | [[Reference/Modules/learnloop_sidecar/logging#^module-purpose|purpose]] | `ACTIVE` | 10 | 0 |
| [[Reference/Modules/learnloop_sidecar/post_attempt_worker|learnloop_sidecar.post_attempt_worker]] | [[Reference/Modules/learnloop_sidecar/post_attempt_worker#^module-purpose|purpose]] | `ACTIVE` | 1 | 7 |
| [[Reference/Modules/learnloop_sidecar/prefetch_runtime|learnloop_sidecar.prefetch_runtime]] | [[Reference/Modules/learnloop_sidecar/prefetch_runtime#^module-purpose|purpose]] | `ACTIVE` | 6 | 5 |
| [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] | [[Reference/Modules/learnloop_sidecar/registry#^module-purpose|purpose]] | `ACTIVE` | 75 | 128 |
| [[Reference/Modules/learnloop_sidecar/request_origin|learnloop_sidecar.request_origin]] | [[Reference/Modules/learnloop_sidecar/request_origin#^module-purpose|purpose]] | `ACTIVE` | 6 | 4 |
| [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] | [[Reference/Modules/learnloop_sidecar/server#^module-purpose|purpose]] | `ACTIVE` | 1 | 45 |
| [[Reference/Modules/learnloop_sidecar/serving|learnloop_sidecar.serving]] | [[Reference/Modules/learnloop_sidecar/serving#^module-purpose|purpose]] | `ACTIVE` | 5 | 0 |
| [[Reference/Modules/learnloop_sidecar/source_identity|learnloop_sidecar.source_identity]] | [[Reference/Modules/learnloop_sidecar/source_identity#^module-purpose|purpose]] | `ACTIVE` | 5 | 0 |

## Child package maps

- [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] — RPC adapters that validate requests and delegate to domain and infrastructure APIs.

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/_package|learnloop]] — 7 static module edges
- [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] — 7 static module edges
- [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] — 7 static module edges
- [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] — 5 static module edges
- [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] — 4 static module edges
- [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] — 4 static module edges
- [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] — 4 static module edges
- [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] — 3 static module edges
- [[Reference/Modules/learnloop/db/_package|learnloop.db]] — 3 static module edges
- [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] — 2 static module edges
- [[Reference/Modules/learnloop/config/_package|learnloop.config]] — 2 static module edges
- [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] — 2 static module edges
- [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] — 2 static module edges
- [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] — 2 static module edges
- [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] — 2 static module edges
- [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] — 2 static module edges
- [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] — 2 static module edges
- [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] — 2 static module edges
- [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] — 2 static module edges
- [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] — 1 static module edge
- [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] — 1 static module edge
- [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] — 1 static module edge
- [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] — 1 static module edge
- [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] — 1 static module edge
- [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] — 1 static module edge
- [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] — 1 static module edge
- [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] — 1 static module edge
- [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] — 1 static module edge

### Packages that import this package

- [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] — 332 static module edges

### Dependency neighborhood

This diagram compresses package-level static imports; edge labels are distinct module-to-module import counts.

```mermaid
flowchart LR
    center["learnloop_sidecar"]
    n_learnloop_sidecar_handlers["learnloop_sidecar.handlers"]
    n_learnloop["learnloop"]
    n_learnloop_ai["learnloop.ai"]
    n_learnloop_vault["learnloop.vault"]
    n_learnloop_followup_serve["learnloop.followup_serve"]
    n_learnloop_daily_plan["learnloop.daily_plan"]
    n_learnloop_figures["learnloop.figures"]
    n_learnloop_adaptive_difficulty["learnloop.adaptive_difficulty"]
    n_learnloop_db["learnloop.db"]
    n_learnloop_attempts["learnloop.attempts"]
    n_learnloop_sidecar_handlers -->|332| center
    center -->|4| n_learnloop_sidecar_handlers
    center -->|7| n_learnloop
    center -->|7| n_learnloop_ai
    center -->|7| n_learnloop_vault
    center -->|5| n_learnloop_followup_serve
    center -->|4| n_learnloop_daily_plan
    center -->|4| n_learnloop_figures
    center -->|3| n_learnloop_adaptive_difficulty
    center -->|3| n_learnloop_db
    center -->|2| n_learnloop_attempts
```

Interpretation: arrow direction is static import direction and the label is the number of distinct module-to-module edges. It shows coupling pressure, not runtime call frequency or ownership permission.

## Workflow entry points

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop_sidecar" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
