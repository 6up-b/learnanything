---
title: "learnloop.ingest.extractors — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/ingest/extractors/__init__.py"
  - "src/learnloop/ingest/extractors/base.py"
  - "src/learnloop/ingest/extractors/datalab.py"
  - "src/learnloop/ingest/extractors/marker.py"
  - "src/learnloop/ingest/extractors/normalizers.py"
  - "src/learnloop/ingest/extractors/pypdf.py"
source_commit: "aggregate; see module notes"
source_commit_timestamp: "2026-07-22T21:17:05-04:00"
generated: true
generated_at: "2026-08-18"
package: "learnloop.ingest.extractors"
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
  - "package/learnloop-ingest-extractors"
---

# `learnloop.ingest.extractors` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

Format-specific extraction adapters for canonical sources.

For system intent, use [[Architecture Overview]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop/ingest/extractors/__init__|learnloop.ingest.extractors]] | [[Reference/Modules/learnloop/ingest/extractors/__init__#^module-purpose|purpose]] | `ACTIVE` | 2 | 1 |
| [[Reference/Modules/learnloop/ingest/extractors/base|learnloop.ingest.extractors.base]] | [[Reference/Modules/learnloop/ingest/extractors/base#^module-purpose|purpose]] | `ACTIVE` | 5 | 1 |
| [[Reference/Modules/learnloop/ingest/extractors/datalab|learnloop.ingest.extractors.datalab]] | [[Reference/Modules/learnloop/ingest/extractors/datalab#^module-purpose|purpose]] | `ACTIVE` | 1 | 0 |
| [[Reference/Modules/learnloop/ingest/extractors/marker|learnloop.ingest.extractors.marker]] | [[Reference/Modules/learnloop/ingest/extractors/marker#^module-purpose|purpose]] | `ACTIVE` | 2 | 2 |
| [[Reference/Modules/learnloop/ingest/extractors/normalizers|learnloop.ingest.extractors.normalizers]] | [[Reference/Modules/learnloop/ingest/extractors/normalizers#^module-purpose|purpose]] | `ACTIVE` | 1 | 8 |
| [[Reference/Modules/learnloop/ingest/extractors/pypdf|learnloop.ingest.extractors.pypdf]] | [[Reference/Modules/learnloop/ingest/extractors/pypdf#^module-purpose|purpose]] | `ACTIVE` | 3 | 1 |

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] — 10 static module edges

### Packages that import this package

- [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] — 3 static module edges

## Workflow entry points

- [[Import Canonical Sources]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/ingest/extractors" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
