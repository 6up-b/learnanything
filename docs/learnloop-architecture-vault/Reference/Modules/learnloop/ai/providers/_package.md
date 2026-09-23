---
title: "learnloop.ai.providers — Package Map"
type: "package-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop/ai/providers/__init__.py"
  - "src/learnloop/ai/providers/codex.py"
  - "src/learnloop/ai/providers/codex_http.py"
  - "src/learnloop/ai/providers/openai_chat.py"
  - "src/learnloop/ai/providers/openrouter.py"
  - "src/learnloop/ai/providers/openrouter_catalog.py"
  - "src/learnloop/ai/providers/openrouter_video.py"
  - "src/learnloop/ai/providers/structured_output.py"
source_commit: "aggregate; see module notes"
source_commit_timestamp: "2026-09-23T12:25:12-04:00"
generated: true
generated_at: "2026-09-23"
package: "learnloop.ai.providers"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Process Model Output"
tags:
  - "docs/package-map"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai-providers"
---

# `learnloop.ai.providers` package map

> [!info] Generated package map
> This map is generated from live modules and their static imports. Follow module links for source-level facts and canonical concept/workflow links for system behavior.

Up: [[Module Catalog]]

## Responsibility

Concrete AI transport adapters behind the provider-neutral contract.

For system intent, use [[AI Architecture]], [[Architecture Overview]].

^package-purpose

## Module index

| Module | Purpose | Status | Direct importers | Direct test files |
|---|---|---:|---:|---:|
| [[Reference/Modules/learnloop/ai/providers/__init__|learnloop.ai.providers]] | [[Reference/Modules/learnloop/ai/providers/__init__#^module-purpose|purpose]] | `ACTIVE` | 0 | 0 |
| [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] | [[Reference/Modules/learnloop/ai/providers/codex#^module-purpose|purpose]] | `ACTIVE` | 6 | 13 |
| [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]] | [[Reference/Modules/learnloop/ai/providers/codex_http#^module-purpose|purpose]] | `ACTIVE` | 2 | 4 |
| [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]] | [[Reference/Modules/learnloop/ai/providers/openai_chat#^module-purpose|purpose]] | `ACTIVE` | 2 | 6 |
| [[Reference/Modules/learnloop/ai/providers/openrouter|learnloop.ai.providers.openrouter]] | [[Reference/Modules/learnloop/ai/providers/openrouter#^module-purpose|purpose]] | `ACTIVE` | 2 | 2 |
| [[Reference/Modules/learnloop/ai/providers/openrouter_catalog|learnloop.ai.providers.openrouter_catalog]] | [[Reference/Modules/learnloop/ai/providers/openrouter_catalog#^module-purpose|purpose]] | `ACTIVE` | 1 | 2 |
| [[Reference/Modules/learnloop/ai/providers/openrouter_video|learnloop.ai.providers.openrouter_video]] | [[Reference/Modules/learnloop/ai/providers/openrouter_video#^module-purpose|purpose]] | `ACTIVE` | 2 | 2 |
| [[Reference/Modules/learnloop/ai/providers/structured_output|learnloop.ai.providers.structured_output]] | [[Reference/Modules/learnloop/ai/providers/structured_output#^module-purpose|purpose]] | `ACTIVE` | 1 | 0 |

## Cross-package dependencies

### This package imports

- [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] — 20 static module edges
- [[Reference/Modules/learnloop/config/_package|learnloop.config]] — 6 static module edges

### Packages that import this package

- [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] — 6 static module edges
- [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] — 2 static module edges
- [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] — 1 static module edge
- [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] — 1 static module edge
- [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] — 1 static module edge

### Dependency neighborhood

This diagram compresses package-level static imports; edge labels are distinct module-to-module import counts.

```mermaid
flowchart LR
    center["learnloop.ai.providers"]
    n_learnloop_ai["learnloop.ai"]
    n_learnloop_config["learnloop.config"]
    n_learnloop_attempts["learnloop.attempts"]
    n_learnloop_content_authoring["learnloop.content.authoring"]
    n_learnloop_ops["learnloop.ops"]
    n_learnloop_sidecar_handlers["learnloop_sidecar.handlers"]
    n_learnloop_ai -->|6| center
    center -->|20| n_learnloop_ai
    center -->|6| n_learnloop_config
    n_learnloop_attempts -->|2| center
    n_learnloop_content_authoring -->|1| center
    n_learnloop_ops -->|1| center
    n_learnloop_sidecar_handlers -->|1| center
```

Interpretation: arrow direction is static import direction and the label is the number of distinct module-to-module edges. It shows coupling pressure, not runtime call frequency or ownership permission.

## Workflow entry points

- [[Process Model Output]]

## Find and filter

Use Obsidian's native search:

```query
path:"Reference/Modules/learnloop/ai/providers" tag:#docs/module
```

To change this package, start with a module's [[#Module index|purpose link]], then follow its callers, tests, and modification guidance. Re-run the generator after source changes.
