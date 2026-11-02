---
title: "learnloop.teacher — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/teacher/__init__.py"
  - "src/learnloop/teacher/actions.py"
  - "src/learnloop/teacher/brief.py"
  - "src/learnloop/teacher/checks.py"
  - "src/learnloop/teacher/contracts.py"
  - "src/learnloop/teacher/delayed.py"
  - "src/learnloop/teacher/doctrines.py"
  - "src/learnloop/teacher/guards.py"
  - "src/learnloop/teacher/notes.py"
  - "src/learnloop/teacher/report.py"
  - "src/learnloop/teacher/service.py"
  - "src/learnloop/teacher/visuals.py"
source_commit: "aggregate; see module notes"
source_commit_timestamp: "2026-11-02T10:46:11-05:00"
generated: true
generated_at: "2026-11-02"
package: "learnloop.teacher"
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
  - "package/learnloop-teacher"
---

# `learnloop.teacher` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

Lessons on the latent learner state: the brief, the teacher's turn contract and actions, guards, checks, delayed checks and receipts.

For system intent, use [[Architecture Overview]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop/teacher/__init__|learnloop.teacher]] | [[Reference/Modules/learnloop/teacher/__init__#^module-purpose|purpose]] | `ACTIVE` | 0 | 1 |
| [[Reference/Modules/learnloop/teacher/actions|learnloop.teacher.actions]] | [[Reference/Modules/learnloop/teacher/actions#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] | [[Reference/Modules/learnloop/teacher/brief#^module-purpose|purpose]] | `ACTIVE` | 6 | 2 |
| [[Reference/Modules/learnloop/teacher/checks|learnloop.teacher.checks]] | [[Reference/Modules/learnloop/teacher/checks#^module-purpose|purpose]] | `ACTIVE` | 1 | 0 |
| [[Reference/Modules/learnloop/teacher/contracts|learnloop.teacher.contracts]] | [[Reference/Modules/learnloop/teacher/contracts#^module-purpose|purpose]] | `ACTIVE` | 5 | 2 |
| [[Reference/Modules/learnloop/teacher/delayed|learnloop.teacher.delayed]] | [[Reference/Modules/learnloop/teacher/delayed#^module-purpose|purpose]] | `ACTIVE` | 2 | 1 |
| [[Reference/Modules/learnloop/teacher/doctrines|learnloop.teacher.doctrines]] | [[Reference/Modules/learnloop/teacher/doctrines#^module-purpose|purpose]] | `ACTIVE` | 2 | 1 |
| [[Reference/Modules/learnloop/teacher/guards|learnloop.teacher.guards]] | [[Reference/Modules/learnloop/teacher/guards#^module-purpose|purpose]] | `ACTIVE` | 1 | 0 |
| [[Reference/Modules/learnloop/teacher/notes|learnloop.teacher.notes]] | [[Reference/Modules/learnloop/teacher/notes#^module-purpose|purpose]] | `ACTIVE` | 2 | 1 |
| [[Reference/Modules/learnloop/teacher/report|learnloop.teacher.report]] | [[Reference/Modules/learnloop/teacher/report#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] | [[Reference/Modules/learnloop/teacher/service#^module-purpose|purpose]] | `ACTIVE` | 2 | 11 |
| [[Reference/Modules/learnloop/teacher/visuals|learnloop.teacher.visuals]] | [[Reference/Modules/learnloop/teacher/visuals#^module-purpose|purpose]] | `ACTIVE` | 1 | 3 |

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/_package|learnloop]] — 15 static module edges
- [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] — 9 static module edges
- [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] — 9 static module edges
- [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] — 7 static module edges
- [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] — 6 static module edges
- [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] — 6 static module edges
- [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] — 5 static module edges
- [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] — 3 static module edges
- [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] — 2 static module edges
- [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] — 2 static module edges
- [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] — 1 static module edge
- [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] — 1 static module edge
- [[Reference/Modules/learnloop/db/_package|learnloop.db]] — 1 static module edge
- [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] — 1 static module edge
- [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] — 1 static module edge

### Packages that import this package

- [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] — 1 static module edge
- [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] — 1 static module edge
- [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] — 1 static module edge

### Dependency neighborhood

This diagram compresses package-level static imports; edge labels are distinct module-to-module import counts.

```mermaid
flowchart LR
    center["learnloop.teacher"]
    n_learnloop["learnloop"]
    n_learnloop_ai["learnloop.ai"]
    n_learnloop_source_retrieval["learnloop.source_retrieval"]
    n_learnloop_db_stores["learnloop.db.stores"]
    n_learnloop_attempts["learnloop.attempts"]
    n_learnloop_learner["learnloop.learner"]
    n_learnloop_vault["learnloop.vault"]
    n_learnloop_tutor["learnloop.tutor"]
    n_learnloop_figures["learnloop.figures"]
    n_learnloop_scheduling["learnloop.scheduling"]
    center -->|15| n_learnloop
    center -->|9| n_learnloop_ai
    center -->|9| n_learnloop_source_retrieval
    center -->|7| n_learnloop_db_stores
    center -->|6| n_learnloop_attempts
    center -->|6| n_learnloop_learner
    center -->|5| n_learnloop_vault
    center -->|3| n_learnloop_tutor
    center -->|2| n_learnloop_figures
    center -->|2| n_learnloop_scheduling
```

Interpretation: arrow direction is static import direction and the label is the number of distinct module-to-module edges. It shows coupling pressure, not runtime call frequency or ownership permission.

## Workflow entry points

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/teacher" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
