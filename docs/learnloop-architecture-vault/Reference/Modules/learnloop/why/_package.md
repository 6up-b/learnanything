---
title: "learnloop.why — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/why/__init__.py"
  - "src/learnloop/why/outcomes_now.py"
  - "src/learnloop/why/reader.py"
  - "src/learnloop/why/reconstructed.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.why"
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
  - "package/learnloop-why"
---

# `learnloop.why` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

Why x and not y: the one reader over decision records, and the labelled reconstruction of decisions older than them (ADR-017).

For system intent, use [[Architecture Overview]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop/why/__init__|learnloop.why]] | [[Reference/Modules/learnloop/why/__init__#^module-purpose|purpose]] | `ACTIVE` | 0 | 0 |
| [[Reference/Modules/learnloop/why/outcomes_now|learnloop.why.outcomes_now]] | [[Reference/Modules/learnloop/why/outcomes_now#^module-purpose|purpose]] | `ACTIVE` | 2 | 0 |
| [[Reference/Modules/learnloop/why/reader|learnloop.why.reader]] | [[Reference/Modules/learnloop/why/reader#^module-purpose|purpose]] | `ACTIVE` | 3 | 2 |
| [[Reference/Modules/learnloop/why/reconstructed|learnloop.why.reconstructed]] | [[Reference/Modules/learnloop/why/reconstructed#^module-purpose|purpose]] | `ACTIVE` | 1 | 2 |

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] — 3 static module edges
- [[Reference/Modules/learnloop/_package|learnloop]] — 2 static module edges
- [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] — 2 static module edges
- [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] — 2 static module edges
- [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] — 1 static module edge
- [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] — 1 static module edge
- [[Reference/Modules/learnloop/data_capture/_package|learnloop.data_capture]] — 1 static module edge
- [[Reference/Modules/learnloop/db/_package|learnloop.db]] — 1 static module edge
- [[Reference/Modules/learnloop/router/_package|learnloop.router]] — 1 static module edge
- [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] — 1 static module edge

### Packages that import this package

- [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] — 3 static module edges
- [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] — 1 static module edge

### Dependency neighborhood

This diagram compresses package-level static imports; edge labels are distinct module-to-module import counts.

```mermaid
flowchart LR
    center["learnloop.why"]
    n_learnloop_cli["learnloop.cli"]
    n_learnloop_db_stores["learnloop.db.stores"]
    n_learnloop["learnloop"]
    n_learnloop_router_objective["learnloop.router_objective"]
    n_learnloop_scheduling["learnloop.scheduling"]
    n_learnloop_ai["learnloop.ai"]
    n_learnloop_attempts["learnloop.attempts"]
    n_learnloop_data_capture["learnloop.data_capture"]
    n_learnloop_db["learnloop.db"]
    n_learnloop_router["learnloop.router"]
    n_learnloop_cli -->|3| center
    center -->|3| n_learnloop_db_stores
    center -->|2| n_learnloop
    center -->|2| n_learnloop_router_objective
    center -->|2| n_learnloop_scheduling
    center -->|1| n_learnloop_ai
    center -->|1| n_learnloop_attempts
    center -->|1| n_learnloop_data_capture
    center -->|1| n_learnloop_db
    center -->|1| n_learnloop_router
```

Interpretation: arrow direction is static import direction and the label is the number of distinct module-to-module edges. It shows coupling pressure, not runtime call frequency or ownership permission.

## Workflow entry points

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/why" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
