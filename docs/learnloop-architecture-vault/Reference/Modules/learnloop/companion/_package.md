---
title: "learnloop.companion — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/companion/__init__.py"
  - "src/learnloop/companion/asks.py"
  - "src/learnloop/companion/history.py"
  - "src/learnloop/companion/search.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.companion"
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
  - "package/learnloop-companion"
---

# `learnloop.companion` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

The Reader workbench's companion: the tutor's history by day and desk, and the context each exchange was asked in. Read-only over exchanges.

For system intent, use [[Architecture Overview]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop/companion/__init__|learnloop.companion]] | [[Reference/Modules/learnloop/companion/__init__#^module-purpose|purpose]] | `ACTIVE` | 0 | 0 |
| [[Reference/Modules/learnloop/companion/asks|learnloop.companion.asks]] | [[Reference/Modules/learnloop/companion/asks#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/companion/history|learnloop.companion.history]] | [[Reference/Modules/learnloop/companion/history#^module-purpose|purpose]] | `ACTIVE` | 3 | 1 |
| [[Reference/Modules/learnloop/companion/search|learnloop.companion.search]] | [[Reference/Modules/learnloop/companion/search#^module-purpose|purpose]] | `ACTIVE` | 1 | 0 |

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] — 5 static module edges
- [[Reference/Modules/learnloop/db/_package|learnloop.db]] — 3 static module edges
- [[Reference/Modules/learnloop/_package|learnloop]] — 1 static module edge
- [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] — 1 static module edge
- [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] — 1 static module edge
- [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] — 1 static module edge

### Packages that import this package

- [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] — 4 static module edges

### Dependency neighborhood

This diagram compresses package-level static imports; edge labels are distinct module-to-module import counts.

```mermaid
flowchart LR
    center["learnloop.companion"]
    n_learnloop_db_stores["learnloop.db.stores"]
    n_learnloop_sidecar_handlers["learnloop_sidecar.handlers"]
    n_learnloop_db["learnloop.db"]
    n_learnloop["learnloop"]
    n_learnloop_content_sources["learnloop.content.sources"]
    n_learnloop_substrate["learnloop.substrate"]
    n_learnloop_tutor["learnloop.tutor"]
    center -->|5| n_learnloop_db_stores
    n_learnloop_sidecar_handlers -->|4| center
    center -->|3| n_learnloop_db
    center -->|1| n_learnloop
    center -->|1| n_learnloop_content_sources
    center -->|1| n_learnloop_substrate
    center -->|1| n_learnloop_tutor
```

Interpretation: arrow direction is static import direction and the label is the number of distinct module-to-module edges. It shows coupling pressure, not runtime call frequency or ownership permission.

## Workflow entry points

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/companion" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
