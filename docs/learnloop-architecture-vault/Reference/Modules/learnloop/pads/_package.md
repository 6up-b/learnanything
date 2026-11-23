---
title: "learnloop.pads — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/pads/__init__.py"
  - "src/learnloop/pads/blocks.py"
  - "src/learnloop/pads/carried.py"
  - "src/learnloop/pads/drain.py"
  - "src/learnloop/pads/emission.py"
  - "src/learnloop/pads/ink.py"
  - "src/learnloop/pads/ink_render.py"
  - "src/learnloop/pads/ink_transcribe.py"
  - "src/learnloop/pads/proposals.py"
  - "src/learnloop/pads/quoting.py"
  - "src/learnloop/pads/submission.py"
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
| [[Reference/Modules/learnloop/pads/blocks|learnloop.pads.blocks]] | [[Reference/Modules/learnloop/pads/blocks#^module-purpose|purpose]] | `ACTIVE` | 1 | 4 |
| [[Reference/Modules/learnloop/pads/carried|learnloop.pads.carried]] | [[Reference/Modules/learnloop/pads/carried#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/pads/drain|learnloop.pads.drain]] | [[Reference/Modules/learnloop/pads/drain#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/pads/emission|learnloop.pads.emission]] | [[Reference/Modules/learnloop/pads/emission#^module-purpose|purpose]] | `ACTIVE` | 7 | 3 |
| [[Reference/Modules/learnloop/pads/ink|learnloop.pads.ink]] | [[Reference/Modules/learnloop/pads/ink#^module-purpose|purpose]] | `ACTIVE` | 3 | 5 |
| [[Reference/Modules/learnloop/pads/ink_render|learnloop.pads.ink_render]] | [[Reference/Modules/learnloop/pads/ink_render#^module-purpose|purpose]] | `ACTIVE` | 2 | 2 |
| [[Reference/Modules/learnloop/pads/ink_transcribe|learnloop.pads.ink_transcribe]] | [[Reference/Modules/learnloop/pads/ink_transcribe#^module-purpose|purpose]] | `ACTIVE` | 1 | 3 |
| [[Reference/Modules/learnloop/pads/proposals|learnloop.pads.proposals]] | [[Reference/Modules/learnloop/pads/proposals#^module-purpose|purpose]] | `ACTIVE` | 2 | 2 |
| [[Reference/Modules/learnloop/pads/quoting|learnloop.pads.quoting]] | [[Reference/Modules/learnloop/pads/quoting#^module-purpose|purpose]] | `ACTIVE` | 2 | 1 |
| [[Reference/Modules/learnloop/pads/submission|learnloop.pads.submission]] | [[Reference/Modules/learnloop/pads/submission#^module-purpose|purpose]] | `ACTIVE` | 2 | 1 |

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] — 18 static module edges
- [[Reference/Modules/learnloop/_package|learnloop]] — 12 static module edges
- [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] — 5 static module edges
- [[Reference/Modules/learnloop/desks/_package|learnloop.desks]] — 4 static module edges
- [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] — 2 static module edges
- [[Reference/Modules/learnloop/db/_package|learnloop.db]] — 1 static module edge
- [[Reference/Modules/learnloop/passage_union/_package|learnloop.passage_union]] — 1 static module edge
- [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] — 1 static module edge
- [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] — 1 static module edge

### Packages that import this package

- [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] — 12 static module edges
- [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] — 1 static module edge

### Dependency neighborhood

This diagram compresses package-level static imports; edge labels are distinct module-to-module import counts.

```mermaid
flowchart LR
    center["learnloop.pads"]
    n_learnloop_db_stores["learnloop.db.stores"]
    n_learnloop["learnloop"]
    n_learnloop_sidecar_handlers["learnloop_sidecar.handlers"]
    n_learnloop_ai["learnloop.ai"]
    n_learnloop_desks["learnloop.desks"]
    n_learnloop_content_sources["learnloop.content.sources"]
    n_learnloop_db["learnloop.db"]
    n_learnloop_passage_union["learnloop.passage_union"]
    n_learnloop_practice_index["learnloop.practice_index"]
    n_learnloop_workbench["learnloop.workbench"]
    center -->|18| n_learnloop_db_stores
    center -->|12| n_learnloop
    n_learnloop_sidecar_handlers -->|12| center
    center -->|5| n_learnloop_ai
    center -->|4| n_learnloop_desks
    center -->|2| n_learnloop_content_sources
    center -->|1| n_learnloop_db
    center -->|1| n_learnloop_passage_union
    center -->|1| n_learnloop_practice_index
    center -->|1| n_learnloop_workbench
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
