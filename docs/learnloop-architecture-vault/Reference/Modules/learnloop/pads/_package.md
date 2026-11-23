---
title: "learnloop.pads — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/pads/__init__.py"
  - "src/learnloop/pads/blocks.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.pads"
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
  - "package/learnloop-pads"
---

# `learnloop.pads` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

The Reader workbench's scratchpads: pads, their append-only block versions and anchors. The learner's own writing, never evidence; its exits to learner-text gaps and attempts are explicit.

For system intent, use [[Architecture Overview]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop/pads/__init__|learnloop.pads]] | [[Reference/Modules/learnloop/pads/__init__#^module-purpose|purpose]] | `ACTIVE` | 0 | 0 |
| [[Reference/Modules/learnloop/pads/blocks|learnloop.pads.blocks]] | [[Reference/Modules/learnloop/pads/blocks#^module-purpose|purpose]] | `ACTIVE` | 1 | 2 |

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] — 2 static module edges
- [[Reference/Modules/learnloop/desks/_package|learnloop.desks]] — 2 static module edges
- [[Reference/Modules/learnloop/_package|learnloop]] — 1 static module edge

### Packages that import this package

- [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] — 1 static module edge

### Dependency neighborhood

This diagram compresses package-level static imports; edge labels are distinct module-to-module import counts.

```mermaid
flowchart LR
    center["learnloop.pads"]
    n_learnloop_db_stores["learnloop.db.stores"]
    n_learnloop_desks["learnloop.desks"]
    n_learnloop["learnloop"]
    n_learnloop_sidecar_handlers["learnloop_sidecar.handlers"]
    center -->|2| n_learnloop_db_stores
    center -->|2| n_learnloop_desks
    center -->|1| n_learnloop
    n_learnloop_sidecar_handlers -->|1| center
```

Interpretation: arrow direction is static import direction and the label is the number of distinct module-to-module edges. It shows coupling pressure, not runtime call frequency or ownership permission.

## Workflow entry points

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/pads" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
