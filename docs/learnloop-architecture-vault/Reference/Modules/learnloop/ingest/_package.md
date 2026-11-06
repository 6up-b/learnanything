---
title: "learnloop.ingest — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/ingest/__init__.py"
  - "src/learnloop/ingest/block_roles.py"
  - "src/learnloop/ingest/detect.py"
  - "src/learnloop/ingest/fetchers.py"
  - "src/learnloop/ingest/hashing.py"
  - "src/learnloop/ingest/ir.py"
  - "src/learnloop/ingest/locators.py"
  - "src/learnloop/ingest/models.py"
  - "src/learnloop/ingest/originals.py"
  - "src/learnloop/ingest/reanchor.py"
  - "src/learnloop/ingest/resolution.py"
  - "src/learnloop/ingest/transcription.py"
  - "src/learnloop/ingest/transcripts.py"
source_commit: "aggregate; see module notes"
source_commit_timestamp: "2026-10-27T05:54:16-04:00"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ingest"
layer: "infrastructure"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
tags:
  - "docs/package-map"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest"
---

# `learnloop.ingest` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

Acquisition intermediate representation, locators, fetchers, originals, and ingestion orchestration.

For system intent, use [[Architecture Overview]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop/ingest/__init__|learnloop.ingest]] | [[Reference/Modules/learnloop/ingest/__init__#^module-purpose|purpose]] | `ACTIVE` | 0 | 0 |
| [[Reference/Modules/learnloop/ingest/block_roles|learnloop.ingest.block_roles]] | [[Reference/Modules/learnloop/ingest/block_roles#^module-purpose|purpose]] | `ACTIVE` | 12 | 6 |
| [[Reference/Modules/learnloop/ingest/detect|learnloop.ingest.detect]] | [[Reference/Modules/learnloop/ingest/detect#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/ingest/fetchers|learnloop.ingest.fetchers]] | [[Reference/Modules/learnloop/ingest/fetchers#^module-purpose|purpose]] | `ACTIVE` | 3 | 2 |
| [[Reference/Modules/learnloop/ingest/hashing|learnloop.ingest.hashing]] | [[Reference/Modules/learnloop/ingest/hashing#^module-purpose|purpose]] | `ACTIVE` | 12 | 20 |
| [[Reference/Modules/learnloop/ingest/ir|learnloop.ingest.ir]] | [[Reference/Modules/learnloop/ingest/ir#^module-purpose|purpose]] | `ACTIVE` | 18 | 67 |
| [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] | [[Reference/Modules/learnloop/ingest/locators#^module-purpose|purpose]] | `ACTIVE` | 28 | 12 |
| [[Reference/Modules/learnloop/ingest/models|learnloop.ingest.models]] | [[Reference/Modules/learnloop/ingest/models#^module-purpose|purpose]] | `ACTIVE` | 8 | 2 |
| [[Reference/Modules/learnloop/ingest/originals|learnloop.ingest.originals]] | [[Reference/Modules/learnloop/ingest/originals#^module-purpose|purpose]] | `ACTIVE` | 10 | 16 |
| [[Reference/Modules/learnloop/ingest/reanchor|learnloop.ingest.reanchor]] | [[Reference/Modules/learnloop/ingest/reanchor#^module-purpose|purpose]] | `ACTIVE` | 6 | 1 |
| [[Reference/Modules/learnloop/ingest/resolution|learnloop.ingest.resolution]] | [[Reference/Modules/learnloop/ingest/resolution#^module-purpose|purpose]] | `ACTIVE` | 7 | 6 |
| [[Reference/Modules/learnloop/ingest/transcription|learnloop.ingest.transcription]] | [[Reference/Modules/learnloop/ingest/transcription#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/ingest/transcripts|learnloop.ingest.transcripts]] | [[Reference/Modules/learnloop/ingest/transcripts#^module-purpose|purpose]] | `ACTIVE` | 2 | 1 |

## Child package maps

- [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] — Format-specific extraction adapters for canonical sources.

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/config/_package|learnloop.config]] — 1 static module edge

### Packages that import this package

- [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] — 18 static module edges
- [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] — 13 static module edges
- [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] — 10 static module edges
- [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] — 10 static module edges
- [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] — 8 static module edges
- [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] — 6 static module edges
- [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] — 5 static module edges
- [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] — 4 static module edges
- [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] — 3 static module edges
- [[Reference/Modules/learnloop/db/_package|learnloop.db]] — 2 static module edges
- [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] — 2 static module edges
- [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] — 2 static module edges
- [[Reference/Modules/learnloop/_package|learnloop]] — 1 static module edge
- [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] — 1 static module edge
- [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] — 1 static module edge
- [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] — 1 static module edge
- [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] — 1 static module edge
- [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] — 1 static module edge
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] — 1 static module edge
- [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] — 1 static module edge
- [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] — 1 static module edge
- [[Reference/Modules/learnloop/remote/_package|learnloop.remote]] — 1 static module edge
- [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] — 1 static module edge
- [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] — 1 static module edge
- [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] — 1 static module edge
- [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] — 1 static module edge

### Dependency neighborhood

This diagram compresses package-level static imports; edge labels are distinct module-to-module import counts.

```mermaid
flowchart LR
    center["learnloop.ingest"]
    n_learnloop_content_pipeline["learnloop.content.pipeline"]
    n_learnloop_ingest_extractors["learnloop.ingest.extractors"]
    n_learnloop_content_sources["learnloop.content.sources"]
    n_learnloop_reader["learnloop.reader"]
    n_learnloop_source_retrieval["learnloop.source_retrieval"]
    n_learnloop_sidecar_handlers["learnloop_sidecar.handlers"]
    n_learnloop_content_synthesis["learnloop.content.synthesis"]
    n_learnloop_content_authoring["learnloop.content.authoring"]
    n_learnloop_adaptive_difficulty["learnloop.adaptive_difficulty"]
    n_learnloop_db["learnloop.db"]
    n_learnloop_content_pipeline -->|18| center
    n_learnloop_ingest_extractors -->|13| center
    n_learnloop_content_sources -->|10| center
    n_learnloop_reader -->|10| center
    n_learnloop_source_retrieval -->|8| center
    n_learnloop_sidecar_handlers -->|6| center
    n_learnloop_content_synthesis -->|5| center
    n_learnloop_content_authoring -->|4| center
    n_learnloop_adaptive_difficulty -->|3| center
    n_learnloop_db -->|2| center
```

Interpretation: arrow direction is static import direction and the label is the number of distinct module-to-module edges. It shows coupling pressure, not runtime call frequency or ownership permission.

## Workflow entry points

- [[Import Canonical Sources]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/ingest" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
