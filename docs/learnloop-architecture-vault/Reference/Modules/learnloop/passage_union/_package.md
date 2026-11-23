---
title: "learnloop.passage_union — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/passage_union/__init__.py"
  - "src/learnloop/passage_union/content.py"
  - "src/learnloop/passage_union/union.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.passage_union"
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
  - "package/learnloop-passage_union"
---

# `learnloop.passage_union` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

The Reader workbench's per-span union read over a visible range: a read-only projection of what LearnLoop holds for each passage.

For system intent, use [[Architecture Overview]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop/passage_union/__init__|learnloop.passage_union]] | [[Reference/Modules/learnloop/passage_union/__init__#^module-purpose|purpose]] | `ACTIVE` | 0 | 0 |
| [[Reference/Modules/learnloop/passage_union/content|learnloop.passage_union.content]] | [[Reference/Modules/learnloop/passage_union/content#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/passage_union/union|learnloop.passage_union.union]] | [[Reference/Modules/learnloop/passage_union/union#^module-purpose|purpose]] | `ACTIVE` | 2 | 3 |

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] — 4 static module edges
- [[Reference/Modules/learnloop/_package|learnloop]] — 2 static module edges
- [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] — 2 static module edges
- [[Reference/Modules/learnloop/db/_package|learnloop.db]] — 1 static module edge
- [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] — 1 static module edge
- [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] — 1 static module edge

### Packages that import this package

- [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] — 2 static module edges

### Dependency neighborhood

This diagram compresses package-level static imports; edge labels are distinct module-to-module import counts.

```mermaid
flowchart LR
    center["learnloop.passage_union"]
    n_learnloop_content_sources["learnloop.content.sources"]
    n_learnloop["learnloop"]
    n_learnloop_db_stores["learnloop.db.stores"]
    n_learnloop_sidecar_handlers["learnloop_sidecar.handlers"]
    n_learnloop_db["learnloop.db"]
    n_learnloop_intent["learnloop.intent"]
    n_learnloop_reader["learnloop.reader"]
    center -->|4| n_learnloop_content_sources
    center -->|2| n_learnloop
    center -->|2| n_learnloop_db_stores
    n_learnloop_sidecar_handlers -->|2| center
    center -->|1| n_learnloop_db
    center -->|1| n_learnloop_intent
    center -->|1| n_learnloop_reader
```

Interpretation: arrow direction is static import direction and the label is the number of distinct module-to-module edges. It shows coupling pressure, not runtime call frequency or ownership permission.

## Workflow entry points

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/passage_union" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
