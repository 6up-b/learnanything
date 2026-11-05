---
title: "learnloop.vault — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/vault/__init__.py"
  - "src/learnloop/vault/embedding_recipes.py"
  - "src/learnloop/vault/facet_fingerprint.py"
  - "src/learnloop/vault/hashes.py"
  - "src/learnloop/vault/lifecycle.py"
  - "src/learnloop/vault/loader.py"
  - "src/learnloop/vault/models.py"
  - "src/learnloop/vault/paths.py"
  - "src/learnloop/vault/repository.py"
  - "src/learnloop/vault/required_method.py"
  - "src/learnloop/vault/scope_seal.py"
  - "src/learnloop/vault/working_vault.py"
  - "src/learnloop/vault/writer.py"
  - "src/learnloop/vault/yaml_io.py"
source_commit: "aggregate; see module notes"
source_commit_timestamp: "2026-11-01T18:59:57-05:00"
generated: true
generated_at: "2026-11-02"
package: "learnloop.vault"
layer: "infrastructure"
concepts:
  - "State and Persistence"
workflows:
  - "Initialize a Vault"
  - "Inspect Persistent State"
tags:
  - "docs/package-map"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-vault"
---

# `learnloop.vault` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

Filesystem layout, Markdown/YAML I/O, hashes, models, loading, and writing.

For system intent, use [[State and Persistence]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop/vault/__init__|learnloop.vault]] | [[Reference/Modules/learnloop/vault/__init__#^module-purpose|purpose]] | `ACTIVE` | 0 | 0 |
| [[Reference/Modules/learnloop/vault/embedding_recipes|learnloop.vault.embedding_recipes]] | [[Reference/Modules/learnloop/vault/embedding_recipes#^module-purpose|purpose]] | `ACTIVE` | 16 | 11 |
| [[Reference/Modules/learnloop/vault/facet_fingerprint|learnloop.vault.facet_fingerprint]] | [[Reference/Modules/learnloop/vault/facet_fingerprint#^module-purpose|purpose]] | `ACTIVE` | 4 | 1 |
| [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] | [[Reference/Modules/learnloop/vault/hashes#^module-purpose|purpose]] | `ACTIVE` | 21 | 18 |
| [[Reference/Modules/learnloop/vault/lifecycle|learnloop.vault.lifecycle]] | [[Reference/Modules/learnloop/vault/lifecycle#^module-purpose|purpose]] | `ACTIVE` | 17 | 3 |
| [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] | [[Reference/Modules/learnloop/vault/loader#^module-purpose|purpose]] | `ACTIVE` | 130 | 761 |
| [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] | [[Reference/Modules/learnloop/vault/models#^module-purpose|purpose]] | `ACTIVE` | 296 | 75 |
| [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] | [[Reference/Modules/learnloop/vault/paths#^module-purpose|purpose]] | `ACTIVE` | 134 | 113 |
| [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] | [[Reference/Modules/learnloop/vault/repository#^module-purpose|purpose]] | `ACTIVE` | 83 | 31 |
| [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] | [[Reference/Modules/learnloop/vault/required_method#^module-purpose|purpose]] | `ACTIVE` | 50 | 10 |
| [[Reference/Modules/learnloop/vault/scope_seal|learnloop.vault.scope_seal]] | [[Reference/Modules/learnloop/vault/scope_seal#^module-purpose|purpose]] | `ACTIVE` | 3 | 0 |
| [[Reference/Modules/learnloop/vault/working_vault|learnloop.vault.working_vault]] | [[Reference/Modules/learnloop/vault/working_vault#^module-purpose|purpose]] | `ACTIVE` | 1 | 2 |
| [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] | [[Reference/Modules/learnloop/vault/writer#^module-purpose|purpose]] | `ACTIVE` | 23 | 143 |
| [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] | [[Reference/Modules/learnloop/vault/yaml_io#^module-purpose|purpose]] | `ACTIVE` | 25 | 188 |

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/_package|learnloop]] — 10 static module edges
- [[Reference/Modules/learnloop/config/_package|learnloop.config]] — 4 static module edges
- [[Reference/Modules/learnloop/db/_package|learnloop.db]] — 4 static module edges
- [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] — 4 static module edges
- [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] — 1 static module edge

### Packages that import this package

- [[Reference/Modules/learnloop/_package|learnloop]] — 111 static module edges
- [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] — 80 static module edges
- [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] — 52 static module edges
- [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] — 44 static module edges
- [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] — 41 static module edges
- [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] — 30 static module edges
- [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] — 26 static module edges
- [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] — 25 static module edges
- [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] — 24 static module edges
- [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] — 23 static module edges
- [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] — 21 static module edges
- [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] — 20 static module edges
- [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] — 19 static module edges
- [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] — 19 static module edges
- [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] — 19 static module edges
- [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] — 17 static module edges
- [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] — 17 static module edges
- [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] — 15 static module edges
- [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] — 14 static module edges
- [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] — 14 static module edges
- [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] — 13 static module edges
- [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] — 12 static module edges
- [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] — 12 static module edges
- [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] — 12 static module edges
- [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] — 11 static module edges
- [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] — 10 static module edges
- [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] — 9 static module edges
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] — 8 static module edges
- [[Reference/Modules/learnloop/ops/contamination/_package|learnloop.ops.contamination]] — 8 static module edges
- [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] — 7 static module edges
- [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] — 6 static module edges
- [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] — 5 static module edges
- [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] — 4 static module edges
- [[Reference/Modules/learnloop/field/_package|learnloop.field]] — 4 static module edges
- [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] — 4 static module edges
- [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] — 4 static module edges
- [[Reference/Modules/learnloop/tui/_package|learnloop.tui]] — 4 static module edges
- [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] — 4 static module edges
- [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] — 3 static module edges
- [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] — 3 static module edges
- [[Reference/Modules/learnloop/remote/_package|learnloop.remote]] — 3 static module edges
- [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] — 2 static module edges
- [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] — 2 static module edges
- [[Reference/Modules/learnloop/data_capture/_package|learnloop.data_capture]] — 1 static module edge
- [[Reference/Modules/learnloop/params/_package|learnloop.params]] — 1 static module edge
- [[Reference/Modules/learnloop/router/_package|learnloop.router]] — 1 static module edge
- [[Reference/Modules/learnloop/substrate/compat/_package|learnloop.substrate.compat]] — 1 static module edge

### Dependency neighborhood

This diagram compresses package-level static imports; edge labels are distinct module-to-module import counts.

```mermaid
flowchart LR
    center["learnloop.vault"]
    n_learnloop["learnloop"]
    n_learnloop_cli["learnloop.cli"]
    n_learnloop_diagnosis["learnloop.diagnosis"]
    n_learnloop_source_retrieval["learnloop.source_retrieval"]
    n_learnloop_ops["learnloop.ops"]
    n_learnloop_content_authoring["learnloop.content.authoring"]
    n_learnloop_content_synthesis["learnloop.content.synthesis"]
    n_learnloop_learner["learnloop.learner"]
    n_learnloop_curriculum["learnloop.curriculum"]
    n_learnloop_content_proposals["learnloop.content.proposals"]
    n_learnloop -->|111| center
    center -->|10| n_learnloop
    n_learnloop_cli -->|80| center
    n_learnloop_diagnosis -->|52| center
    n_learnloop_source_retrieval -->|44| center
    n_learnloop_ops -->|41| center
    n_learnloop_content_authoring -->|30| center
    n_learnloop_content_synthesis -->|26| center
    n_learnloop_learner -->|25| center
    n_learnloop_curriculum -->|24| center
    n_learnloop_content_proposals -->|23| center
```

Interpretation: arrow direction is static import direction and the label is the number of distinct module-to-module edges. It shows coupling pressure, not runtime call frequency or ownership permission.

## Workflow entry points

- [[Initialize a Vault]]
- [[Inspect Persistent State]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/vault" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
