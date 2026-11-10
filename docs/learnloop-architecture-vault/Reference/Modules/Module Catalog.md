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
generated: true
generated_at: "2026-11-02"
tags:
  - "docs/moc"
  - "docs/module-catalog"
  - "architecture/reference"
---

# Module Catalog

> [!abstract] Lookup contract
> This catalog maps all **1277 Python source modules** under `src/learnloop` and `src/learnloop_sidecar` to one generated reference note apiece—including explicit active, compatibility, dormant, and evaluation statuses—and links the **617 TypeScript/TSX/Rust modules** in [[Desktop Module Catalog]]. It also provides **68 Python package maps**. Concepts belong in [[Architecture Overview]], [[Learning System]], [[AI Architecture]], [[State and Persistence]], and [[Configuration]]; workflows belong in their dedicated notes.

## Coverage and status

| Refactor status | Modules | Meaning |
|---|---:|---|
| `ACTIVE` | 1254 | Live ownership after the refactor. |
| `COMPAT` | 4 | Live but frozen old-vault compatibility machinery. |
| `DORMANT` | 2 | Explicitly disabled/descoped modules with no live workflow authority. |
| `EVALUATION` | 17 | Shadow, audit, or offline evaluation code whose outputs are decision-inert. |

> [!note] Generated evidence
> Importers and direct calls are static AST evidence. Dynamic RPC registration, entry points, reflection, and string-based dispatch are called out where known but cannot be proven exhaustively without runtime tracing.

^catalog-coverage

## Package maps

| Package | Layer | Status | Direct modules | Responsibility |
|---|---|---|---:|---|
| [[Reference/Modules/learnloop/_package|learnloop]] | `coordination` | `ACTIVE` | 79 | Application-level coordinators and dependency-neutral authorities shared across LearnLoop. |
| [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] | `domain` | `ACTIVE` | 47 | Adaptive difficulty: logged reading opportunities and outside forecasters, the readiness model, guarded selection near the target band, and its receipts. |
| [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] | `infrastructure` | `ACTIVE` | 24 | Provider-neutral structured transport, routing, provider composition, capability checks, and usage accounting. |
| [[Reference/Modules/learnloop/ai/chatgpt_plan/_package|learnloop.ai.chatgpt_plan]] | `infrastructure` | `ACTIVE` | 7 | Sign in with ChatGPT for the chatgpt_plan provider: the machine-local sign-in store, the PKCE flow, access tokens and plan-usage state, and its requests. |
| [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] | `infrastructure` | `ACTIVE` | 13 | Concrete AI transport adapters behind the provider-neutral contract. |
| [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] | `domain` | `ACTIVE` | 31 | Attempt acceptance, grading, interaction evidence, feedback, and post-attempt processing. |
| [[Reference/Modules/learnloop/capture/_package|learnloop.capture]] | `domain` | `ACTIVE` | 8 | The shared capture domain (the capture inbox); importing it never attaches or migrates. |
| [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] | `adapter` | `ACTIVE` | 57 | Typer command adapters, rendering, argument contracts, and command registration. |
| [[Reference/Modules/learnloop/config/_package|learnloop.config]] | `infrastructure` | `ACTIVE` | 5 | Typed configuration schema, compatibility normalization, loading, and template emission. |
| [[Reference/Modules/learnloop/content/_package|learnloop.content]] | `domain` | `ACTIVE` | 0 | Source-derived content, authoring, synthesis, proposal, and canonical pipeline ownership. |
| [[Reference/Modules/learnloop/content/authoring/_package|learnloop.content.authoring]] | `domain` | `ACTIVE` | 19 | Practice-content authoring gates, generation contracts, and authored artifacts. |
| [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] | `domain` | `ACTIVE` | 9 | Facet identity at mint time and the dedupe command: embedding shortlists, a judge over each neighbourhood, live merges with exact undo. |
| [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] | `domain` | `ACTIVE` | 12 | Canonical content extraction and transformation stages. |
| [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] | `domain` | `ACTIVE` | 9 | Reviewable content and graph change proposals and their lifecycle. |
| [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] | `domain` | `ACTIVE` | 16 | Canonical source-library identity, manifests, and source-set behavior. |
| [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] | `domain` | `ACTIVE` | 20 | Synthesis of source material into learning structures and AI-owned contracts. |
| [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] | `domain` | `ACTIVE` | 23 | Commitments, blueprints, depth structures, concept relationships, and golden paths. |
| [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] | `domain` | `ACTIVE` | 37 | The finite daily plan: remembered minutes split across repair, maintain, new and push, chosen block by block, and the router card. |
| [[Reference/Modules/learnloop/data_capture/_package|learnloop.data_capture]] | `domain` | `ACTIVE` | 4 | What later evaluation needs, recorded now: its switches, prefilter receipts, and the one read of Reader exposures with the sweep that freezes them. |
| [[Reference/Modules/learnloop/db/_package|learnloop.db]] | `infrastructure` | `ACTIVE` | 9 | SQLite connections, migrations, repository compatibility, table roles, rebuilds, and persistence infrastructure. |
| [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] | `infrastructure` | `ACTIVE` | 55 | Table-family persistence owners extracted from the repository facade. |
| [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] | `domain` | `ACTIVE` | 59 | Diagnostic probes, causal attribution, error classification, and remediation decisions. |
| [[Reference/Modules/learnloop/diagnosis/offline_review/_package|learnloop.diagnosis.offline_review]] | `domain` | `ACTIVE` | 10 | The offline review of blind grading and history-aware diagnosis, run on backup copies with synthetic learners; never changes a live vault. |
| [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] | `domain` | `ACTIVE` | 11 | Recurrence with authority: the same_cause match kind over causal hypotheses, its shortlist and judge, the live step and the backlog. |
| [[Reference/Modules/learnloop/diagnosis/split/_package|learnloop.diagnosis.split]] | `domain` | `ACTIVE` | 20 | History-aware diagnosis split from the learner-blind grader: history modes, the diagnoser's inputs, jobs and traces. |
| [[Reference/Modules/learnloop/diagnosis/text_gaps/_package|learnloop.diagnosis.text_gaps]] | `domain` | `ACTIVE` | 12 | Learner-text gaps: what a learner's own words show they lack or hold, read in tiers, judged in pairs, acted on with undo, and reported. |
| [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] | `domain` | `ACTIVE` | 17 | EVSI/EIG calibration: read-only measurement of the numbers value-of-information runs on, labelled honestly where they cannot be measured. |
| [[Reference/Modules/learnloop/experiments/_package|learnloop.experiments]] | `domain` | `ACTIVE` | 1 | Research experiments on backup copies of vaults; never part of production serving (no production package imports it). |
| [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] | `domain` | `ACTIVE` | 23 | Experiment E0: hosted contextual source embeddings, its bank, labels, arms and report. |
| [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] | `domain` | `ACTIVE` | 12 | Experiment E1: the local pplx v2-context-9b batch pilot over E0's bank and finalists. |
| [[Reference/Modules/learnloop/field/_package|learnloop.field]] | `domain` | `ACTIVE` | 18 | Replay-only learner-field contracts (the LearnerPredictor contract, signals, outcomes); no serving policy or evidence writes. |
| [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] | `domain` | `ACTIVE` | 26 | Explorable figures: declarative specs and sketches, their authoring routes, verification, labels, help records and the figure service. |
| [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] | `domain` | `ACTIVE` | 10 | FG1's composition, imported only by the sidecar: lanes, the frontier authoring operation, machine admission, the router's itemless decision, what the feedback screen and Next read, and the generation worker. |
| [[Reference/Modules/learnloop/followup_serve/_package|learnloop.followup_serve]] | `domain` | `ACTIVE` | 6 | FG1's leaf: the kill switch, the durable workflow's record, the generation queue's writes and the generated probe's single-use identity, read by the domain packages. |
| [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] | `domain` | `ACTIVE` | 19 | Learning goals, forecasts, certification, readiness, and exam workflows. |
| [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] | `domain` | `ACTIVE` | 19 | Adaptive hints: telemetry and report, approach maps, the hint service and its outcomes. |
| [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] | `infrastructure` | `ACTIVE` | 13 | Acquisition intermediate representation, locators, fetchers, originals, and ingestion orchestration. |
| [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] | `infrastructure` | `ACTIVE` | 9 | Format-specific extraction adapters for canonical sources. |
| [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] | `domain` | `ACTIVE` | 18 | Canonical sources as a shared instructional service: a composition layer for the tutor's offers, source exercises, exposure and the tools. |
| [[Reference/Modules/learnloop/intent/_package|learnloop.intent]] | `domain` | `ACTIVE` | 5 | The single intent control: commitments carrying intent, optional deadlines and settled checks. |
| [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] | `domain` | `ACTIVE` | 27 | Mastery, recall, evidence, claims, ability transitions, and learner-state views. |
| [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] | `domain` | `ACTIVE` | 13 | Local contextual source retrieval: the local document space's pins, capped batch worker, GPU meter, locks and owner-run commands. |
| [[Reference/Modules/learnloop/matching/_package|learnloop.matching]] | `domain` | `ACTIVE` | 5 | The one 'same or different?' step: registered match kinds, embedding shortlists and LLM judges, recorded in the judgment ledger. |
| [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] | `domain` | `ACTIVE` | 23 | Vault diagnostics, locks, settings, startup, upgrades, and operator-facing maintenance. |
| [[Reference/Modules/learnloop/ops/contamination/_package|learnloop.ops.contamination]] | `domain` | `ACTIVE` | 7 | Contamination detectors as shadow flags, run offline on the owner's command beside the live lexical floor. |
| [[Reference/Modules/learnloop/params/_package|learnloop.params]] | `domain` | `ACTIVE` | 4 | Algorithm parameter registry, fitted values, and sensitivity certificates. |
| [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] | `domain` | `ACTIVE` | 9 | Placement for new material through the LearnerPredictor contract; writes only its own receipts, never evidence. |
| [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] | `domain` | `ACTIVE` | 14 | The practice index: facet dossiers and find_practice (recall by search, an LLM decides, the scheduler admits). |
| [[Reference/Modules/learnloop/projects/_package|learnloop.projects]] | `domain` | `ACTIVE` | 10 | Project understanding: captured agent-written diffs and delayed comprehension probes on them. |
| [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] | `domain` | `ACTIVE` | 29 | Reader-mode source exploration, annotations, quick checks, and authoring handoffs. |
| [[Reference/Modules/learnloop/recognition/_package|learnloop.recognition]] | `domain` | `ACTIVE` | 4 | Recognition and effort RE0: the derived cue label of an attempt and the report section that splits results by it; capture only, read by reports and nothing else. |
| [[Reference/Modules/learnloop/remote/_package|learnloop.remote]] | `domain` | `ACTIVE` | 7 | Application services for frontends outside the desktop (the MCP chat adapter's only door); no learning policy of its own. |
| [[Reference/Modules/learnloop/router/_package|learnloop.router]] | `domain` | `ACTIVE` | 12 | The action router: decisions logged on today's serving paths and their derived outcomes; a leaf that chooses nothing yet. |
| [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] | `domain` | `ACTIVE` | 35 | The router objective's logging (spec_router_objective_v1 §4, RO0): additive receipts at every version behind [router_objective] receipts, read by nothing serving, scheduling or certification. |
| [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] | `domain` | `ACTIVE` | 41 | Selection, review timing, progression, controller decisions, and scheduling projections. |
| [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] | `domain` | `ACTIVE` | 7 | Intent at serving time: the vocabulary, the most-recent-choice resolution, per-intent recall targets and the per-build view. |
| [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] | `simulation` | `EVALUATION` | 13 | Offline simulation, benchmark, sweep, synthetic-student, and algorithm evaluation tools. |
| [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] | `domain` | `ACTIVE` | 42 | Source retrieval and the Reader's sources side: keyword and dense search, section coverage, deliverables and paths, and the learner's notes. |
| [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] | `domain` | `ACTIVE` | 23 | Activity, card, surface, and identity substrate plus canonical projections. |
| [[Reference/Modules/learnloop/substrate/compat/_package|learnloop.substrate.compat]] | `domain` | `COMPAT` | 4 | Frozen compatibility machinery retained for old vaults. |
| [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] | `domain` | `ACTIVE` | 18 | Lessons on the latent learner state: the brief, the teacher's turn contract and actions, guards, checks, delayed checks and receipts. |
| [[Reference/Modules/learnloop/tui/_package|learnloop.tui]] | `adapter` | `ACTIVE` | 6 | Textual UI adapter, screens, widgets, state, and presentation behavior. |
| [[Reference/Modules/learnloop/tui/screens/_package|learnloop.tui.screens]] | `adapter` | `ACTIVE` | 5 | Individual Textual user-interface screens. |
| [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] | `domain` | `ACTIVE` | 10 | Tutoring, hints, teach-back, and tutor question-and-answer workflows. |
| [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] | `infrastructure` | `ACTIVE` | 14 | Filesystem layout, Markdown/YAML I/O, hashes, models, loading, and writing. |
| [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] | `domain` | `ACTIVE` | 9 | The Reader workbench's checks and the help ladder's Reader side: Check my work, declared symbolic checks and the ladder. |
| [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] | `adapter` | `ACTIVE` | 16 | Desktop sidecar process, RPC registry, transport context, DTOs, and server lifecycle. |
| [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] | `adapter` | `ACTIVE` | 78 | RPC adapters that validate requests and delegate to domain and infrastructure APIs. |

## Desktop client modules

The Tauri desktop application has **617 source modules** with one-to-one reference notes in [[Desktop Module Catalog]]. Read [[Desktop Architecture]] first for the React-to-Rust-to-sidecar boundary, then use that catalog for per-file callers, dependencies, tests, and modification guidance.

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
TABLE refactor_status AS Status, layer AS Layer, source_path AS Source
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

The current generation discovered 1491 Python test files. Each module note lists direct importing tests or, when absent, one-hop consumer tests.

Notes carry no commit of their own: the commit they were generated from is `module_generate.py`'s row in [[Reference/_generated|Generated Reference Provenance]], so a regeneration rewrites only the notes whose facts changed.
