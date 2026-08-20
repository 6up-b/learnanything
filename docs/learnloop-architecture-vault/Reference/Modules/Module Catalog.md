---
title: "Module Catalog"
type: "map-of-content"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "src/learnloop"
  - "src/learnloop_sidecar"
  - "apps/learnloop-tauri"
source_commit: "aggregate; see module notes"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
generated: true
generated_at: "2026-08-18"
tags:
  - "docs/moc"
  - "docs/module-catalog"
  - "architecture/reference"
---

# Module Catalog

> [!abstract] Lookup contract
> This catalog maps all **452 Python source modules** under `src/learnloop` and `src/learnloop_sidecar` to one generated reference note apiece—including explicit active, compatibility, dormant, and evaluation statuses—and links the **107 TypeScript/TSX/Rust modules** in [[Desktop Module Catalog]]. It also provides **33 Python package maps**. Concepts belong in [[Architecture Overview]], [[Learning System]], [[AI Architecture]], [[State and Persistence]], and [[Configuration]]; workflows belong in their dedicated notes.

## Coverage and status

| Refactor status | Modules | Meaning |
|---|---:|---|
| `ACTIVE` | 431 | Live ownership after the refactor. |
| `COMPAT` | 4 | Live but frozen old-vault compatibility machinery. |
| `DORMANT` | 2 | Explicitly disabled/descoped modules with no live workflow authority. |
| `EVALUATION` | 15 | Shadow, audit, or offline evaluation code whose outputs are decision-inert. |

> [!note] Generated evidence
> Importers and direct calls are static AST evidence. Dynamic RPC registration, entry points, reflection, and string-based dispatch are called out where known but cannot be proven exhaustively without runtime tracing.

^catalog-coverage

## Package maps

| Package | Layer | Status | Direct modules | Responsibility |
|---|---|---|---:|---|
| [[Reference/Modules/learnloop/_package|learnloop]] | `coordination` | `ACTIVE` | 12 | Application-level coordinators and dependency-neutral authorities shared across LearnLoop. |
| [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] | `infrastructure` | `ACTIVE` | 11 | Provider-neutral structured transport, routing, provider composition, capability checks, and usage accounting. |
| [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] | `infrastructure` | `ACTIVE` | 6 | Concrete AI transport adapters behind the provider-neutral contract. |
| [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] | `domain` | `ACTIVE` | 23 | Attempt acceptance, grading, interaction evidence, feedback, and post-attempt processing. |
| [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] | `adapter` | `ACTIVE` | 23 | Typer command adapters, rendering, argument contracts, and command registration. |
| [[Reference/Modules/learnloop/config/_package|learnloop.config]] | `infrastructure` | `ACTIVE` | 5 | Typed configuration schema, compatibility normalization, loading, and template emission. |
| [[Reference/Modules/learnloop/content/_package|learnloop.content]] | `domain` | `ACTIVE` | 0 | Source-derived content, authoring, synthesis, proposal, and canonical pipeline ownership. |
| [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] | `domain` | `ACTIVE` | 14 | Practice-content authoring gates, generation contracts, and authored artifacts. |
| [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] | `domain` | `ACTIVE` | 9 | Canonical content extraction and transformation stages. |
| [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] | `domain` | `ACTIVE` | 6 | Reviewable content and graph change proposals and their lifecycle. |
| [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] | `domain` | `ACTIVE` | 12 | Canonical source-library identity, manifests, and source-set behavior. |
| [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] | `domain` | `ACTIVE` | 18 | Synthesis of source material into learning structures and AI-owned contracts. |
| [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] | `domain` | `ACTIVE` | 22 | Commitments, blueprints, depth structures, concept relationships, and golden paths. |
| [[Reference/Modules/learnloop/db/_package|learnloop.db]] | `infrastructure` | `ACTIVE` | 5 | SQLite connections, migrations, repository compatibility, table roles, rebuilds, and persistence infrastructure. |
| [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] | `infrastructure` | `ACTIVE` | 3 | Table-family persistence owners extracted from the repository facade. |
| [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] | `domain` | `ACTIVE` | 53 | Diagnostic probes, causal attribution, error classification, and remediation decisions. |
| [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] | `domain` | `ACTIVE` | 17 | Learning goals, forecasts, certification, readiness, and exam workflows. |
| [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] | `infrastructure` | `ACTIVE` | 13 | Acquisition intermediate representation, locators, fetchers, originals, and ingestion orchestration. |
| [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] | `infrastructure` | `ACTIVE` | 6 | Format-specific extraction adapters for canonical sources. |
| [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] | `domain` | `ACTIVE` | 26 | Mastery, recall, evidence, claims, ability transitions, and learner-state views. |
| [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] | `domain` | `ACTIVE` | 9 | Vault diagnostics, locks, settings, startup, upgrades, and operator-facing maintenance. |
| [[Reference/Modules/learnloop/params/_package|learnloop.params]] | `domain` | `ACTIVE` | 4 | Algorithm parameter registry, fitted values, and sensitivity certificates. |
| [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] | `domain` | `ACTIVE` | 16 | Reader-mode source exploration, annotations, quick checks, and authoring handoffs. |
| [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] | `domain` | `ACTIVE` | 32 | Selection, review timing, progression, controller decisions, and scheduling projections. |
| [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] | `simulation` | `EVALUATION` | 11 | Offline simulation, benchmark, sweep, synthetic-student, and algorithm evaluation tools. |
| [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] | `domain` | `ACTIVE` | 15 | Activity, card, surface, and identity substrate plus canonical projections. |
| [[Reference/Modules/learnloop/substrate/compat/_package|learnloop.substrate.compat]] | `domain` | `COMPAT` | 4 | Frozen compatibility machinery retained for old vaults. |
| [[Reference/Modules/learnloop/tui/_package|learnloop.tui]] | `adapter` | `ACTIVE` | 5 | Textual UI adapter, screens, widgets, state, and presentation behavior. |
| [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] | `adapter` | `ACTIVE` | 5 | Individual Textual user-interface screens. |
| [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] | `domain` | `ACTIVE` | 8 | Tutoring, hints, teach-back, and tutor question-and-answer workflows. |
| [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] | `infrastructure` | `ACTIVE` | 9 | Filesystem layout, Markdown/YAML I/O, hashes, models, loading, and writing. |
| [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] | `adapter` | `ACTIVE` | 9 | Desktop sidecar process, RPC registry, transport context, DTOs, and server lifecycle. |
| [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] | `adapter` | `ACTIVE` | 41 | RPC adapters that validate requests and delegate to domain and infrastructure APIs. |

## Desktop client modules

The Tauri desktop application has **107 source modules** with one-to-one reference notes in [[Desktop Module Catalog]]. Read [[Desktop Architecture]] first for the React-to-Rust-to-sidecar boundary, then use that catalog for per-file callers, dependencies, tests, and modification guidance.

> [!tip] Choose the catalog by source tree
> Use this catalog for Python under `src/`; use [[Desktop Module Catalog]] for TypeScript, TSX, and Rust under `apps/learnloop-tauri/`. Both link back to the same concepts and end-to-end workflows.

## Find a module

Obsidian's native search operators work without plugins:

- `path:` restricts search to this catalog.
- `tag:` filters by refactor status, layer, or package.
- `section:` searches a generated heading such as `Modification guidance`.
- `file:` finds a module by source/module filename.
- `line:` finds facts on one generated line.

```query
path:"Reference/Modules" tag:#docs/module
```

```query
path:"Reference/Modules" tag:#refactor/compat
```

```query
path:"Reference/Modules" section:("Modification guidance") "Schema changes"
```

> [!tip] Optional Dataview index
> If the Dataview community plugin is enabled, the query below creates a sortable live table. The vault does not require the plugin.

```dataview
TABLE refactor_status AS Status, layer AS Layer, source_path AS Source, source_commit_timestamp AS Commit
FROM "Reference/Modules"
WHERE type = "module-reference"
SORT file.name ASC
```

## How to read a module note

1. Use [[#Package maps|the package map]] to locate the ownership boundary.
2. Open the module's purpose block, then inspect its public API and internal anchors.
3. Follow inbound importers to learn who depends on it and outbound dependencies to learn what it assumes.
4. Use test anchors as behavior evidence and the change guide for safe extension points.
5. Follow canonical concept/workflow links for system semantics rather than expecting them to be duplicated in reference notes.

## Maintenance

```bash
.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py
.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py
```

The current generation discovered 431 Python test files. Each module note lists direct importing tests or, when absent, one-hop consumer tests.
