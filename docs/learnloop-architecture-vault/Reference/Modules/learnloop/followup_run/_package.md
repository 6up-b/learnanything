---
title: "learnloop.followup_run — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/followup_run/__init__.py"
  - "src/learnloop/followup_run/admission.py"
  - "src/learnloop/followup_run/authoring.py"
  - "src/learnloop/followup_run/decision_view.py"
  - "src/learnloop/followup_run/jobs.py"
  - "src/learnloop/followup_run/lanes.py"
  - "src/learnloop/followup_run/marks.py"
  - "src/learnloop/followup_run/router.py"
  - "src/learnloop/followup_run/serving.py"
source_commit: "aggregate; see module notes"
source_commit_timestamp: "2026-11-04T09:10:39-05:00"
generated: true
generated_at: "2026-11-02"
package: "learnloop.followup_run"
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
  - "package/learnloop-followup_run"
---

# `learnloop.followup_run` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

FG1's composition, imported only by the sidecar: lanes, the frontier authoring operation, machine admission, the router's itemless decision, what the feedback screen and Next read, and the generation worker.

For system intent, use [[Architecture Overview]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop/followup_run/__init__|learnloop.followup_run]] | [[Reference/Modules/learnloop/followup_run/__init__#^module-purpose|purpose]] | `ACTIVE` | 0 | 0 |
| [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]] | [[Reference/Modules/learnloop/followup_run/admission#^module-purpose|purpose]] | `ACTIVE` | 1 | 2 |
| [[Reference/Modules/learnloop/followup_run/authoring|learnloop.followup_run.authoring]] | [[Reference/Modules/learnloop/followup_run/authoring#^module-purpose|purpose]] | `ACTIVE` | 2 | 4 |
| [[Reference/Modules/learnloop/followup_run/decision_view|learnloop.followup_run.decision_view]] | [[Reference/Modules/learnloop/followup_run/decision_view#^module-purpose|purpose]] | `ACTIVE` | 2 | 2 |
| [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] | [[Reference/Modules/learnloop/followup_run/jobs#^module-purpose|purpose]] | `ACTIVE` | 3 | 5 |
| [[Reference/Modules/learnloop/followup_run/lanes|learnloop.followup_run.lanes]] | [[Reference/Modules/learnloop/followup_run/lanes#^module-purpose|purpose]] | `ACTIVE` | 3 | 3 |
| [[Reference/Modules/learnloop/followup_run/marks|learnloop.followup_run.marks]] | [[Reference/Modules/learnloop/followup_run/marks#^module-purpose|purpose]] | `ACTIVE` | 2 | 2 |
| [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] | [[Reference/Modules/learnloop/followup_run/router#^module-purpose|purpose]] | `ACTIVE` | 2 | 6 |
| [[Reference/Modules/learnloop/followup_run/serving|learnloop.followup_run.serving]] | [[Reference/Modules/learnloop/followup_run/serving#^module-purpose|purpose]] | `ACTIVE` | 6 | 2 |

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] — 17 static module edges
- [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] — 14 static module edges
- [[Reference/Modules/learnloop/db/_package|learnloop.db]] — 8 static module edges
- [[Reference/Modules/learnloop/_package|learnloop]] — 7 static module edges
- [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] — 6 static module edges
- [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] — 5 static module edges
- [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] — 3 static module edges
- [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] — 3 static module edges
- [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] — 3 static module edges
- [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] — 2 static module edges
- [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] — 1 static module edge
- [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] — 1 static module edge
- [[Reference/Modules/learnloop/data_capture/_package|learnloop.data_capture]] — 1 static module edge
- [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] — 1 static module edge
- [[Reference/Modules/learnloop/router/_package|learnloop.router]] — 1 static module edge

### Packages that import this package

- [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] — 8 static module edges
- [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] — 2 static module edges

### Dependency neighborhood

This diagram compresses package-level static imports; edge labels are distinct module-to-module import counts.

```mermaid
flowchart LR
    center["learnloop.followup_run"]
    n_learnloop_diagnosis["learnloop.diagnosis"]
    n_learnloop_followup_serve["learnloop.followup_serve"]
    n_learnloop_db["learnloop.db"]
    n_learnloop_sidecar_handlers["learnloop_sidecar.handlers"]
    n_learnloop["learnloop"]
    n_learnloop_daily_plan["learnloop.daily_plan"]
    n_learnloop_db_stores["learnloop.db.stores"]
    n_learnloop_ai["learnloop.ai"]
    n_learnloop_content_authoring["learnloop.content.authoring"]
    n_learnloop_diagnosis_split["learnloop.diagnosis.split"]
    center -->|17| n_learnloop_diagnosis
    center -->|14| n_learnloop_followup_serve
    center -->|8| n_learnloop_db
    n_learnloop_sidecar_handlers -->|8| center
    center -->|7| n_learnloop
    center -->|6| n_learnloop_daily_plan
    center -->|5| n_learnloop_db_stores
    center -->|3| n_learnloop_ai
    center -->|3| n_learnloop_content_authoring
    center -->|3| n_learnloop_diagnosis_split
```

Interpretation: arrow direction is static import direction and the label is the number of distinct module-to-module edges. It shows coupling pressure, not runtime call frequency or ownership permission.

## Workflow entry points

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/followup_run" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
