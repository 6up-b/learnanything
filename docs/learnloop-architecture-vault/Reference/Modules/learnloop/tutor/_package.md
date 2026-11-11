---
title: "learnloop.tutor — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/tutor/__init__.py"
  - "src/learnloop/tutor/ai_contracts.py"
  - "src/learnloop/tutor/context_delivery.py"
  - "src/learnloop/tutor/durable_promotion.py"
  - "src/learnloop/tutor/promotions.py"
  - "src/learnloop/tutor/question_queue.py"
  - "src/learnloop/tutor/question_signal.py"
  - "src/learnloop/tutor/reader_modes.py"
  - "src/learnloop/tutor/teach_back.py"
  - "src/learnloop/tutor/tutor_qa.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.tutor"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Start a Learning Cycle"
  - "Process Model Output"
tags:
  - "docs/package-map"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-tutor"
---

# `learnloop.tutor` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

Tutoring, hints, teach-back, and tutor question-and-answer workflows.

For system intent, use [[Learning System]], [[AI Architecture]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop/tutor/__init__|learnloop.tutor]] | [[Reference/Modules/learnloop/tutor/__init__#^module-purpose|purpose]] | `ACTIVE` | 0 | 0 |
| [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]] | [[Reference/Modules/learnloop/tutor/ai_contracts#^module-purpose|purpose]] | `ACTIVE` | 9 | 62 |
| [[Reference/Modules/learnloop/tutor/context_delivery|learnloop.tutor.context_delivery]] | [[Reference/Modules/learnloop/tutor/context_delivery#^module-purpose|purpose]] | `ACTIVE` | 7 | 4 |
| [[Reference/Modules/learnloop/tutor/durable_promotion|learnloop.tutor.durable_promotion]] | [[Reference/Modules/learnloop/tutor/durable_promotion#^module-purpose|purpose]] | `ACTIVE` | 5 | 1 |
| [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] | [[Reference/Modules/learnloop/tutor/promotions#^module-purpose|purpose]] | `ACTIVE` | 5 | 6 |
| [[Reference/Modules/learnloop/tutor/question_queue|learnloop.tutor.question_queue]] | [[Reference/Modules/learnloop/tutor/question_queue#^module-purpose|purpose]] | `ACTIVE` | 4 | 1 |
| [[Reference/Modules/learnloop/tutor/question_signal|learnloop.tutor.question_signal]] | [[Reference/Modules/learnloop/tutor/question_signal#^module-purpose|purpose]] | `ACTIVE` | 1 | 4 |
| [[Reference/Modules/learnloop/tutor/reader_modes|learnloop.tutor.reader_modes]] | [[Reference/Modules/learnloop/tutor/reader_modes#^module-purpose|purpose]] | `ACTIVE` | 3 | 4 |
| [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] | [[Reference/Modules/learnloop/tutor/teach_back#^module-purpose|purpose]] | `ACTIVE` | 6 | 4 |
| [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] | [[Reference/Modules/learnloop/tutor/tutor_qa#^module-purpose|purpose]] | `ACTIVE` | 26 | 58 |

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/_package|learnloop]] — 14 static module edges
- [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] — 14 static module edges
- [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] — 11 static module edges
- [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] — 8 static module edges
- [[Reference/Modules/learnloop/db/_package|learnloop.db]] — 7 static module edges
- [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] — 4 static module edges
- [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] — 4 static module edges
- [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] — 4 static module edges
- [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] — 3 static module edges
- [[Reference/Modules/learnloop/config/_package|learnloop.config]] — 3 static module edges
- [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] — 2 static module edges
- [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] — 2 static module edges
- [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] — 2 static module edges
- [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] — 1 static module edge
- [[Reference/Modules/learnloop/data_capture/_package|learnloop.data_capture]] — 1 static module edge
- [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] — 1 static module edge
- [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] — 1 static module edge
- [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] — 1 static module edge
- [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] — 1 static module edge

### Packages that import this package

- [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] — 14 static module edges
- [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] — 6 static module edges
- [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] — 4 static module edges
- [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] — 3 static module edges
- [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] — 3 static module edges
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] — 3 static module edges
- [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] — 3 static module edges
- [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] — 3 static module edges
- [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] — 3 static module edges
- [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] — 3 static module edges
- [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] — 2 static module edges
- [[Reference/Modules/learnloop/_package|learnloop]] — 1 static module edge
- [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] — 1 static module edge
- [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] — 1 static module edge
- [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] — 1 static module edge
- [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] — 1 static module edge
- [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] — 1 static module edge
- [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] — 1 static module edge
- [[Reference/Modules/learnloop/ops/contamination/_package|learnloop.ops.contamination]] — 1 static module edge

### Dependency neighborhood

This diagram compresses package-level static imports; edge labels are distinct module-to-module import counts.

```mermaid
flowchart LR
    center["learnloop.tutor"]
    n_learnloop["learnloop"]
    n_learnloop_vault["learnloop.vault"]
    n_learnloop_sidecar_handlers["learnloop_sidecar.handlers"]
    n_learnloop_ai["learnloop.ai"]
    n_learnloop_learner["learnloop.learner"]
    n_learnloop_db["learnloop.db"]
    n_learnloop_diagnosis["learnloop.diagnosis"]
    n_learnloop_source_retrieval["learnloop.source_retrieval"]
    n_learnloop_content_authoring["learnloop.content.authoring"]
    n_learnloop_reader["learnloop.reader"]
    n_learnloop -->|1| center
    center -->|14| n_learnloop
    center -->|14| n_learnloop_vault
    n_learnloop_sidecar_handlers -->|14| center
    center -->|11| n_learnloop_ai
    n_learnloop_learner -->|1| center
    center -->|8| n_learnloop_learner
    center -->|7| n_learnloop_db
    n_learnloop_diagnosis -->|3| center
    center -->|4| n_learnloop_diagnosis
    n_learnloop_source_retrieval -->|6| center
    n_learnloop_content_authoring -->|1| center
    center -->|4| n_learnloop_content_authoring
    n_learnloop_reader -->|3| center
    center -->|2| n_learnloop_reader
```

Interpretation: arrow direction is static import direction and the label is the number of distinct module-to-module edges. It shows coupling pressure, not runtime call frequency or ownership permission.

## Workflow entry points

- [[Start a Learning Cycle]]
- [[Process Model Output]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/tutor" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
