---
title: "learnloop.tui — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/tui/__init__.py"
  - "src/learnloop/tui/app.py"
  - "src/learnloop/tui/state.py"
  - "src/learnloop/tui/theme.py"
  - "src/learnloop/tui/widgets.py"
source_commit: "aggregate; see module notes"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
generated: true
generated_at: "2026-08-18"
package: "learnloop.tui"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Start a Learning Cycle"
  - "Inspect Persistent State"
tags:
  - "docs/package-map"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-tui"
---

# `learnloop.tui` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

Textual UI adapter, screens, widgets, state, and presentation behavior.

For system intent, use [[Architecture Overview]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop/tui/__init__|learnloop.tui]] | [[Reference/Modules/learnloop/tui/__init__#^module-purpose|purpose]] | `ACTIVE` | 0 | 0 |
| [[Reference/Modules/learnloop/tui/app|learnloop.tui.app]] | [[Reference/Modules/learnloop/tui/app#^module-purpose|purpose]] | `ACTIVE` | 1 | 6 |
| [[Reference/Modules/learnloop/tui/state|learnloop.tui.state]] | [[Reference/Modules/learnloop/tui/state#^module-purpose|purpose]] | `ACTIVE` | 5 | 0 |
| [[Reference/Modules/learnloop/tui/theme|learnloop.tui.theme]] | [[Reference/Modules/learnloop/tui/theme#^module-purpose|purpose]] | `ACTIVE` | 1 | 0 |
| [[Reference/Modules/learnloop/tui/widgets|learnloop.tui.widgets]] | [[Reference/Modules/learnloop/tui/widgets#^module-purpose|purpose]] | `ACTIVE` | 5 | 2 |

## Child package maps

- [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] — Individual Textual user-interface screens.

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] — 4 static module edges
- [[Reference/Modules/learnloop/db/_package|learnloop.db]] — 1 static module edge
- [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] — 1 static module edge
- [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] — 1 static module edge
- [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] — 1 static module edge
- [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] — 1 static module edge

### Packages that import this package

- [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] — 8 static module edges
- [[Reference/Modules/learnloop/_package|learnloop]] — 1 static module edge

### Dependency neighborhood

This diagram compresses package-level static imports; edge labels are distinct module-to-module import counts.

```mermaid
flowchart LR
    center["learnloop.tui"]
    n_learnloop_tui_screens["learnloop.tui.screens"]
    n_learnloop_vault["learnloop.vault"]
    n_learnloop["learnloop"]
    n_learnloop_db["learnloop.db"]
    n_learnloop_ops["learnloop.ops"]
    n_learnloop_scheduling["learnloop.scheduling"]
    n_learnloop_substrate["learnloop.substrate"]
    n_learnloop_tui_screens -->|8| center
    center -->|1| n_learnloop_tui_screens
    center -->|4| n_learnloop_vault
    n_learnloop -->|1| center
    center -->|1| n_learnloop_db
    center -->|1| n_learnloop_ops
    center -->|1| n_learnloop_scheduling
    center -->|1| n_learnloop_substrate
```

Interpretation: arrow direction is static import direction and the label is the number of distinct module-to-module edges. It shows coupling pressure, not runtime call frequency or ownership permission.

## Workflow entry points

- [[Start a Learning Cycle]]
- [[Inspect Persistent State]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/tui" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
