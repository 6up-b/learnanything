---
title: "learnloop.matching — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/matching/__init__.py"
  - "src/learnloop/matching/judge.py"
  - "src/learnloop/matching/kinds.py"
  - "src/learnloop/matching/shortlist.py"
  - "src/learnloop/matching/union.py"
source_commit: "aggregate; see module notes"
source_commit_timestamp: "2026-11-01T18:48:17-05:00"
generated: true
generated_at: "2026-11-02"
package: "learnloop.matching"
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
  - "package/learnloop-matching"
---

# `learnloop.matching` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

The one 'same or different?' step: registered match kinds, embedding shortlists and LLM judges, recorded in the judgment ledger.

For system intent, use [[Architecture Overview]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop/matching/__init__|learnloop.matching]] | [[Reference/Modules/learnloop/matching/__init__#^module-purpose|purpose]] | `ACTIVE` | 0 | 1 |
| [[Reference/Modules/learnloop/matching/judge|learnloop.matching.judge]] | [[Reference/Modules/learnloop/matching/judge#^module-purpose|purpose]] | `ACTIVE` | 8 | 5 |
| [[Reference/Modules/learnloop/matching/kinds|learnloop.matching.kinds]] | [[Reference/Modules/learnloop/matching/kinds#^module-purpose|purpose]] | `ACTIVE` | 9 | 3 |
| [[Reference/Modules/learnloop/matching/shortlist|learnloop.matching.shortlist]] | [[Reference/Modules/learnloop/matching/shortlist#^module-purpose|purpose]] | `ACTIVE` | 6 | 3 |
| [[Reference/Modules/learnloop/matching/union|learnloop.matching.union]] | [[Reference/Modules/learnloop/matching/union#^module-purpose|purpose]] | `ACTIVE` | 4 | 2 |

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] — 5 static module edges
- [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] — 3 static module edges
- [[Reference/Modules/learnloop/_package|learnloop]] — 1 static module edge

### Packages that import this package

- [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] — 10 static module edges
- [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] — 7 static module edges
- [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] — 2 static module edges
- [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] — 1 static module edge

### Dependency neighborhood

This diagram compresses package-level static imports; edge labels are distinct module-to-module import counts.

```mermaid
flowchart LR
    center["learnloop.matching"]
    n_learnloop_diagnosis_recurrence["learnloop.diagnosis.recurrence"]
    n_learnloop_diagnosis_text_gaps["learnloop.diagnosis.text_gaps"]
    n_learnloop_ai["learnloop.ai"]
    n_learnloop_db_stores["learnloop.db.stores"]
    n_learnloop_content_facet_identity["learnloop.content.facet_identity"]
    n_learnloop["learnloop"]
    n_learnloop_substrate["learnloop.substrate"]
    n_learnloop_diagnosis_recurrence -->|10| center
    n_learnloop_diagnosis_text_gaps -->|7| center
    center -->|5| n_learnloop_ai
    center -->|3| n_learnloop_db_stores
    n_learnloop_content_facet_identity -->|2| center
    center -->|1| n_learnloop
    n_learnloop_substrate -->|1| center
```

Interpretation: arrow direction is static import direction and the label is the number of distinct module-to-module edges. It shows coupling pressure, not runtime call frequency or ownership permission.

## Workflow entry points

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/matching" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
