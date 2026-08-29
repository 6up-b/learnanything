---
title: "learnloop.content — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/content/"
source_commit: "aggregate; see module notes"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Process Model Output"
tags:
  - "docs/package-map"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content"
---

# `learnloop.content` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

Source-derived content, authoring, synthesis, proposal, and canonical pipeline ownership.

For system intent, use [[Learning System]], [[AI Architecture]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| _Namespace package; use child package maps below._ | — | `ACTIVE` | — | — |

## Child package maps

- [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] — Practice-content authoring gates, generation contracts, and authored artifacts.
- [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] — Canonical content extraction and transformation stages.
- [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] — Reviewable content and graph change proposals and their lifecycle.
- [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] — Canonical source-library identity, manifests, and source-set behavior.
- [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] — Synthesis of source material into learning structures and AI-owned contracts.

## Cross-package dependencies

- No cross-package imports were found.

## Workflow entry points

- [[Import Canonical Sources]]
- [[Process Model Output]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/content" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
