---
title: "learnloop.notebook_runtime — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/notebook_runtime/__init__.py"
  - "src/learnloop/notebook_runtime/adapter.py"
  - "src/learnloop/notebook_runtime/proxy.py"
  - "src/learnloop/notebook_runtime/runtime.py"
  - "src/learnloop/notebook_runtime/sandbox.py"
  - "src/learnloop/notebook_runtime/settings.py"
  - "src/learnloop/notebook_runtime/supervisor.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.notebook_runtime"
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
  - "package/learnloop-notebook_runtime"
---

# `learnloop.notebook_runtime` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

The notebook runtime: one supervised, sandboxed marimo server per pad or lesson, the frame proxy in front of it, and the one adapter that holds marimo's private interfaces. Serving code; the authoring harness never imports it and it never imports the harness.

For system intent, use [[Architecture Overview]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop/notebook_runtime/__init__|learnloop.notebook_runtime]] | [[Reference/Modules/learnloop/notebook_runtime/__init__#^module-purpose|purpose]] | `ACTIVE` | 0 | 0 |
| [[Reference/Modules/learnloop/notebook_runtime/adapter|learnloop.notebook_runtime.adapter]] | [[Reference/Modules/learnloop/notebook_runtime/adapter#^module-purpose|purpose]] | `ACTIVE` | 4 | 2 |
| [[Reference/Modules/learnloop/notebook_runtime/proxy|learnloop.notebook_runtime.proxy]] | [[Reference/Modules/learnloop/notebook_runtime/proxy#^module-purpose|purpose]] | `ACTIVE` | 1 | 1 |
| [[Reference/Modules/learnloop/notebook_runtime/runtime|learnloop.notebook_runtime.runtime]] | [[Reference/Modules/learnloop/notebook_runtime/runtime#^module-purpose|purpose]] | `ACTIVE` | 1 | 3 |
| [[Reference/Modules/learnloop/notebook_runtime/sandbox|learnloop.notebook_runtime.sandbox]] | [[Reference/Modules/learnloop/notebook_runtime/sandbox#^module-purpose|purpose]] | `ACTIVE` | 3 | 4 |
| [[Reference/Modules/learnloop/notebook_runtime/settings|learnloop.notebook_runtime.settings]] | [[Reference/Modules/learnloop/notebook_runtime/settings#^module-purpose|purpose]] | `ACTIVE` | 5 | 1 |
| [[Reference/Modules/learnloop/notebook_runtime/supervisor|learnloop.notebook_runtime.supervisor]] | [[Reference/Modules/learnloop/notebook_runtime/supervisor#^module-purpose|purpose]] | `ACTIVE` | 2 | 2 |

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/_package|learnloop]] — 1 static module edge

### Packages that import this package

- [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] — 3 static module edges

## Workflow entry points

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/notebook_runtime" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
