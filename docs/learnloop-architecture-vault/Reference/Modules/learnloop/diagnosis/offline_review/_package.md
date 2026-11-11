---
title: "learnloop.diagnosis.offline_review — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/diagnosis/offline_review/__init__.py"
  - "src/learnloop/diagnosis/offline_review/decider_links.py"
  - "src/learnloop/diagnosis/offline_review/judge.py"
  - "src/learnloop/diagnosis/offline_review/links.py"
  - "src/learnloop/diagnosis/offline_review/planted.py"
  - "src/learnloop/diagnosis/offline_review/probes.py"
  - "src/learnloop/diagnosis/offline_review/report.py"
  - "src/learnloop/diagnosis/offline_review/runner.py"
  - "src/learnloop/diagnosis/offline_review/spend.py"
  - "src/learnloop/diagnosis/offline_review/spot_check.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.offline_review"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Process Model Output"
tags:
  - "docs/package-map"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-offline_review"
---

# `learnloop.diagnosis.offline_review` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

The offline review of blind grading and history-aware diagnosis, run on backup copies with synthetic learners; never changes a live vault.

For system intent, use [[Learning System]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop/diagnosis/offline_review/__init__|learnloop.diagnosis.offline_review]] | [[Reference/Modules/learnloop/diagnosis/offline_review/__init__#^module-purpose|purpose]] | `ACTIVE` | 0 | 0 |
| [[Reference/Modules/learnloop/diagnosis/offline_review/decider_links|learnloop.diagnosis.offline_review.decider_links]] | [[Reference/Modules/learnloop/diagnosis/offline_review/decider_links#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/diagnosis/offline_review/judge|learnloop.diagnosis.offline_review.judge]] | [[Reference/Modules/learnloop/diagnosis/offline_review/judge#^module-purpose|purpose]] | `ACTIVE` | 5 | 4 |
| [[Reference/Modules/learnloop/diagnosis/offline_review/links|learnloop.diagnosis.offline_review.links]] | [[Reference/Modules/learnloop/diagnosis/offline_review/links#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/diagnosis/offline_review/planted|learnloop.diagnosis.offline_review.planted]] | [[Reference/Modules/learnloop/diagnosis/offline_review/planted#^module-purpose|purpose]] | `ACTIVE` | 1 | 2 |
| [[Reference/Modules/learnloop/diagnosis/offline_review/probes|learnloop.diagnosis.offline_review.probes]] | [[Reference/Modules/learnloop/diagnosis/offline_review/probes#^module-purpose|purpose]] | `ACTIVE` | 2 | 2 |
| [[Reference/Modules/learnloop/diagnosis/offline_review/report|learnloop.diagnosis.offline_review.report]] | [[Reference/Modules/learnloop/diagnosis/offline_review/report#^module-purpose|purpose]] | `ACTIVE` | 5 | 1 |
| [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] | [[Reference/Modules/learnloop/diagnosis/offline_review/runner#^module-purpose|purpose]] | `ACTIVE` | 6 | 6 |
| [[Reference/Modules/learnloop/diagnosis/offline_review/spend|learnloop.diagnosis.offline_review.spend]] | [[Reference/Modules/learnloop/diagnosis/offline_review/spend#^module-purpose|purpose]] | `ACTIVE` | 14 | 6 |
| [[Reference/Modules/learnloop/diagnosis/offline_review/spot_check|learnloop.diagnosis.offline_review.spot_check]] | [[Reference/Modules/learnloop/diagnosis/offline_review/spot_check#^module-purpose|purpose]] | `ACTIVE` | 2 | 1 |

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] — 14 static module edges
- [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] — 12 static module edges
- [[Reference/Modules/learnloop/db/_package|learnloop.db]] — 9 static module edges
- [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] — 9 static module edges
- [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] — 7 static module edges
- [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] — 6 static module edges
- [[Reference/Modules/learnloop/_package|learnloop]] — 5 static module edges
- [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] — 2 static module edges
- [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] — 1 static module edge
- [[Reference/Modules/learnloop/config/_package|learnloop.config]] — 1 static module edge
- [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] — 1 static module edge

### Packages that import this package

- [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] — 7 static module edges
- [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] — 7 static module edges
- [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] — 6 static module edges
- [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] — 2 static module edges
- [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] — 1 static module edge

### Dependency neighborhood

This diagram compresses package-level static imports; edge labels are distinct module-to-module import counts.

```mermaid
flowchart LR
    center["learnloop.diagnosis.offline_review"]
    n_learnloop_diagnosis_split["learnloop.diagnosis.split"]
    n_learnloop_ai["learnloop.ai"]
    n_learnloop_db["learnloop.db"]
    n_learnloop_vault["learnloop.vault"]
    n_learnloop_attempts["learnloop.attempts"]
    n_learnloop_cli["learnloop.cli"]
    n_learnloop_diagnosis_recurrence["learnloop.diagnosis.recurrence"]
    n_learnloop_db_stores["learnloop.db.stores"]
    n_learnloop["learnloop"]
    n_learnloop_content_proposals["learnloop.content.proposals"]
    n_learnloop_diagnosis_split -->|6| center
    center -->|12| n_learnloop_diagnosis_split
    center -->|14| n_learnloop_ai
    center -->|9| n_learnloop_db
    center -->|9| n_learnloop_vault
    center -->|7| n_learnloop_attempts
    n_learnloop_cli -->|7| center
    n_learnloop_diagnosis_recurrence -->|7| center
    center -->|6| n_learnloop_db_stores
    center -->|5| n_learnloop
    n_learnloop_content_proposals -->|2| center
```

Interpretation: arrow direction is static import direction and the label is the number of distinct module-to-module edges. It shows coupling pressure, not runtime call frequency or ownership permission.

## Workflow entry points

- [[Start a Learning Cycle]]
- [[Process Model Output]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/diagnosis/offline_review" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
