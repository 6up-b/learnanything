---
title: "learnloop.db — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/db/__init__.py"
  - "src/learnloop/db/checkpoint.py"
  - "src/learnloop/db/connection.py"
  - "src/learnloop/db/copies.py"
  - "src/learnloop/db/migrate.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/db/scopes.py"
  - "src/learnloop/db/storage.py"
  - "src/learnloop/db/table_roles.py"
source_commit: "aggregate; see module notes"
source_commit_timestamp: "2026-09-23T20:44:21-04:00"
generated: true
generated_at: "2026-09-23"
package: "learnloop.db"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Inspect Persistent State"
tags:
  - "docs/package-map"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db"
---

# `learnloop.db` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

SQLite connections, migrations, repository compatibility, table roles, rebuilds, and persistence infrastructure.

For system intent, use [[State and Persistence]], [[Architecture Overview]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop/db/__init__|learnloop.db]] | [[Reference/Modules/learnloop/db/__init__#^module-purpose|purpose]] | `ACTIVE` | 0 | 0 |
| [[Reference/Modules/learnloop/db/checkpoint|learnloop.db.checkpoint]] | [[Reference/Modules/learnloop/db/checkpoint#^module-purpose|purpose]] | `ACTIVE` | 3 | 2 |
| [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] | [[Reference/Modules/learnloop/db/connection#^module-purpose|purpose]] | `ACTIVE` | 10 | 32 |
| [[Reference/Modules/learnloop/db/copies|learnloop.db.copies]] | [[Reference/Modules/learnloop/db/copies#^module-purpose|purpose]] | `ACTIVE` | 4 | 4 |
| [[Reference/Modules/learnloop/db/migrate|learnloop.db.migrate]] | [[Reference/Modules/learnloop/db/migrate#^module-purpose|purpose]] | `ACTIVE` | 5 | 29 |
| [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] | [[Reference/Modules/learnloop/db/repositories#^module-purpose|purpose]] | `ACTIVE` | 217 | 326 |
| [[Reference/Modules/learnloop/db/scopes|learnloop.db.scopes]] | [[Reference/Modules/learnloop/db/scopes#^module-purpose|purpose]] | `ACTIVE` | 12 | 3 |
| [[Reference/Modules/learnloop/db/storage|learnloop.db.storage]] | [[Reference/Modules/learnloop/db/storage#^module-purpose|purpose]] | `ACTIVE` | 1 | 5 |
| [[Reference/Modules/learnloop/db/table_roles|learnloop.db.table_roles]] | [[Reference/Modules/learnloop/db/table_roles#^module-purpose|purpose]] | `ACTIVE` | 6 | 2 |

## Child package maps

- [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] — Table-family persistence owners extracted from the repository facade.

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/_package|learnloop]] — 8 static module edges
- [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] — 6 static module edges
- [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] — 2 static module edges
- [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] — 1 static module edge

### Packages that import this package

- [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] — 45 static module edges
- [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] — 24 static module edges
- [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] — 20 static module edges
- [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] — 20 static module edges
- [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] — 20 static module edges
- [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] — 15 static module edges
- [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] — 14 static module edges
- [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] — 13 static module edges
- [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] — 10 static module edges
- [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] — 10 static module edges
- [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] — 9 static module edges
- [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] — 8 static module edges
- [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] — 6 static module edges
- [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] — 5 static module edges
- [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] — 5 static module edges
- [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] — 5 static module edges
- [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] — 3 static module edges
- [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] — 3 static module edges
- [[Reference/Modules/learnloop/params/_package|learnloop.params]] — 3 static module edges
- [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] — 3 static module edges
- [[Reference/Modules/learnloop/substrate/compat/_package|learnloop.substrate.compat]] — 2 static module edges
- [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] — 2 static module edges
- [[Reference/Modules/learnloop/_package|learnloop]] — 1 static module edge
- [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] — 1 static module edge
- [[Reference/Modules/learnloop/tui/_package|learnloop.tui]] — 1 static module edge
- [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] — 1 static module edge

### Dependency neighborhood

This diagram compresses package-level static imports; edge labels are distinct module-to-module import counts.

```mermaid
flowchart LR
    center["learnloop.db"]
    n_learnloop_diagnosis["learnloop.diagnosis"]
    n_learnloop_scheduling["learnloop.scheduling"]
    n_learnloop_curriculum["learnloop.curriculum"]
    n_learnloop_learner["learnloop.learner"]
    n_learnloop_substrate["learnloop.substrate"]
    n_learnloop_attempts["learnloop.attempts"]
    n_learnloop_goals["learnloop.goals"]
    n_learnloop_reader["learnloop.reader"]
    n_learnloop_content_authoring["learnloop.content.authoring"]
    n_learnloop_content_synthesis["learnloop.content.synthesis"]
    n_learnloop_diagnosis -->|45| center
    n_learnloop_scheduling -->|24| center
    n_learnloop_curriculum -->|20| center
    n_learnloop_learner -->|20| center
    n_learnloop_substrate -->|20| center
    n_learnloop_attempts -->|15| center
    n_learnloop_goals -->|14| center
    n_learnloop_reader -->|13| center
    n_learnloop_content_authoring -->|10| center
    n_learnloop_content_synthesis -->|10| center
```

Interpretation: arrow direction is static import direction and the label is the number of distinct module-to-module edges. It shows coupling pressure, not runtime call frequency or ownership permission.

## Workflow entry points

- [[Initialize a Vault]]
- [[Inspect Persistent State]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/db" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
