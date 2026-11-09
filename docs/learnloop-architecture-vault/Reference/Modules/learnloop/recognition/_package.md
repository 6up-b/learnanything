---
title: "learnloop.recognition — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/recognition/__init__.py"
  - "src/learnloop/recognition/cue.py"
  - "src/learnloop/recognition/ledger.py"
  - "src/learnloop/recognition/report.py"
source_commit: "aggregate; see module notes"
source_commit_timestamp: "2026-11-09T16:01:49-05:00"
generated: true
generated_at: "2026-11-02"
package: "learnloop.recognition"
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
  - "package/learnloop-recognition"
---

# `learnloop.recognition` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

Recognition and effort RE0: the derived cue label of an attempt and the report section that splits results by it; capture only, read by reports and nothing else.

For system intent, use [[Architecture Overview]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop/recognition/__init__|learnloop.recognition]] | [[Reference/Modules/learnloop/recognition/__init__#^module-purpose|purpose]] | `ACTIVE` | 0 | 0 |
| [[Reference/Modules/learnloop/recognition/cue|learnloop.recognition.cue]] | [[Reference/Modules/learnloop/recognition/cue#^module-purpose|purpose]] | `ACTIVE` | 2 | 1 |
| [[Reference/Modules/learnloop/recognition/ledger|learnloop.recognition.ledger]] | [[Reference/Modules/learnloop/recognition/ledger#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/recognition/report|learnloop.recognition.report]] | [[Reference/Modules/learnloop/recognition/report#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/_package|learnloop]] — 1 static module edge
- [[Reference/Modules/learnloop/data_capture/_package|learnloop.data_capture]] — 1 static module edge
- [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] — 1 static module edge
- [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] — 1 static module edge
- [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] — 1 static module edge

### Packages that import this package

- [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] — 1 static module edge

### Dependency neighborhood

This diagram compresses package-level static imports; edge labels are distinct module-to-module import counts.

```mermaid
flowchart LR
    center["learnloop.recognition"]
    n_learnloop["learnloop"]
    n_learnloop_data_capture["learnloop.data_capture"]
    n_learnloop_db_stores["learnloop.db.stores"]
    n_learnloop_learner["learnloop.learner"]
    n_learnloop_ops["learnloop.ops"]
    n_learnloop_router_objective["learnloop.router_objective"]
    center -->|1| n_learnloop
    center -->|1| n_learnloop_data_capture
    center -->|1| n_learnloop_db_stores
    center -->|1| n_learnloop_learner
    n_learnloop_ops -->|1| center
    center -->|1| n_learnloop_router_objective
```

Interpretation: arrow direction is static import direction and the label is the number of distinct module-to-module edges. It shows coupling pressure, not runtime call frequency or ownership permission.

## Workflow entry points

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/recognition" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
