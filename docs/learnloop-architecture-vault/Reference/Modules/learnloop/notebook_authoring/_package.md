---
title: "learnloop.notebook_authoring — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/notebook_authoring/__init__.py"
  - "src/learnloop/notebook_authoring/check.py"
  - "src/learnloop/notebook_authoring/marimo_adapter.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.notebook_authoring"
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
  - "package/learnloop-notebook_authoring"
---

# `learnloop.notebook_authoring` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

The owner-side notebook harness, imported by no serving package: a parser adapter over marimo's non-executing loader and the structural check behind `learnloop notebook check`.

For system intent, use [[Architecture Overview]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop/notebook_authoring/__init__|learnloop.notebook_authoring]] | [[Reference/Modules/learnloop/notebook_authoring/__init__#^module-purpose|purpose]] | `ACTIVE` | 0 | 0 |
| [[Reference/Modules/learnloop/notebook_authoring/check|learnloop.notebook_authoring.check]] | [[Reference/Modules/learnloop/notebook_authoring/check#^module-purpose|purpose]] | `ACTIVE` | 1 | 0 |
| [[Reference/Modules/learnloop/notebook_authoring/marimo_adapter|learnloop.notebook_authoring.marimo_adapter]] | [[Reference/Modules/learnloop/notebook_authoring/marimo_adapter#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |

## Cross-package dependencies

- No cross-package imports were found.

### Packages that import this package

- [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] — 1 static module edge

## Workflow entry points

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/notebook_authoring" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
