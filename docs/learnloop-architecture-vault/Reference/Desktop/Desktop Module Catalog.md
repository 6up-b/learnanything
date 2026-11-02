---
title: "Desktop Module Catalog"
type: "map-of-content"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src"
  - "apps/learnloop-tauri/src-tauri/src"
source_commit: "20c6c3ad3806f7951982f4768478fe77272f4c3a"
source_commit_timestamp: "2026-11-01T23:26:02-05:00"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/module-catalog"
---

# Desktop Module Catalog

> [!abstract] Exact coverage
> One generated note exists for each of the **305 live TypeScript/TSX modules** under `apps/learnloop-tauri/src` and **6 authored Rust crate modules** under `src-tauri/src`. Cargo `target/` output and `build.rs` are not runtime crate modules and are intentionally excluded.

^desktop-catalog-coverage

## Runtime bridge

```mermaid
flowchart LR
  UI[React screens and components] --> DTO[api/dto.ts contracts]
  DTO --> CLIENT[api/client.ts invoke facade]
  CLIENT --> COMMANDS[Rust commands.rs]
  COMMANDS --> MANAGER[Rust SidecarManager]
  MANAGER --> PY[Python learnloop_sidecar registry]
  WATCH[Rust VaultWatcher] --> MANAGER
  PY --> DOMAIN[Python domain owners and SQLite]
```

The diagram makes the cross-language request boundary explicit: TypeScript presents and adapts, Rust owns native transport/process concerns, and Python remains the learning and persistent-state authority. See [[Architecture/Adapter Architecture#Request flow|request flow]].

## Area maps

| Area | Direct modules | Responsibility |
|---|---:|---|
| [[Reference/Desktop/Rust/_area|Rust]] | 6 | The native Tauri shell, command bridge, sidecar process manager, error contract, and vault watcher. |
| [[Reference/Desktop/TypeScript/_area|TypeScript]] | 5 | The React renderer entry point and cross-cutting frontend modules. |
| [[Reference/Desktop/TypeScript/api/_area|TypeScript/api]] | 6 | Typed DTOs and the renderer-to-Tauri invocation facade. |
| [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] | 24 | Desktop shell orchestration, keyboard policy, configuration helpers, and recent-vault state. |
| [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] | 77 | Reusable learner-facing controls and composite interaction surfaces. |
| [[Reference/Desktop/TypeScript/components/goldenpath/_area|TypeScript/components/goldenpath]] | 3 | Golden-path setup and triage components used by the staged learning journey. |
| [[Reference/Desktop/TypeScript/components/graphedit/_area|TypeScript/components/graphedit]] | 5 | Study-map editing widgets, pending edits, and geometry previews. |
| [[Reference/Desktop/TypeScript/components/pdfSelection/_area|TypeScript/components/pdfSelection]] | 6 | The PDF text-layer selection model: tokens, geometry, highlights, and the selection layer over a rendered page. |
| [[Reference/Desktop/TypeScript/components/pdfSelection/testing/_area|TypeScript/components/pdfSelection/testing]] | 2 | Synthetic PDFs and books built in memory for the PDF selection vitest files (test support, outside the Vite build). |
| [[Reference/Desktop/TypeScript/components/recipeedit/_area|TypeScript/components/recipeedit]] | 1 | Recipe-tree editing for structured learning plans. |
| [[Reference/Desktop/TypeScript/copy/_area|TypeScript/copy]] | 2 | Learner-facing copy policy: the jargon deny-list the vitest lints apply, and plain-language ingest error wording. |
| [[Reference/Desktop/TypeScript/fixtures/_area|TypeScript/fixtures]] | 3 | Deterministic renderer fixtures used to demonstrate or restore known states. |
| [[Reference/Desktop/TypeScript/fixtures/goldenpath/_area|TypeScript/fixtures/goldenpath]] | 1 | A barrel over checked-in golden-path JSON scenario fixtures. |
| [[Reference/Desktop/TypeScript/render/_area|TypeScript/render]] | 3 | Markdown, mathematics, and live-editor rendering adapters. |
| [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] | 28 | Top-level routed workflow screens in the desktop shell. |
| [[Reference/Desktop/TypeScript/screens/feedback/_area|TypeScript/screens/feedback]] | 3 | The post-answer feedback surface: answer exposure, method comparison, and its exposure contract. |
| [[Reference/Desktop/TypeScript/screens/practice/_area|TypeScript/screens/practice]] | 7 | Practice-screen help: hints, the hint panel, help-style settings, difficulty taps, and why an item was chosen. |
| [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] | 84 | Reader request-state coordination extracted from the main reader screen. |
| [[Reference/Desktop/TypeScript/screens/reader/figures/_area|TypeScript/screens/reader/figures]] | 8 | Reader "show me" figures: the figure grammar and spec, inline figures, panels, predictions, and their state. |
| [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/_area|TypeScript/screens/reader/figures/sketch]] | 13 | The sandboxed sketch tier: the pinned engine host, its Worker protocol and runner, and the scene renderer. |
| [[Reference/Desktop/TypeScript/screens/startBackdrops/_area|TypeScript/screens/startBackdrops]] | 8 | Canvas/SVG simulations and workers used as the start-screen visual backdrop. |
| [[Reference/Desktop/TypeScript/screens/today/_area|TypeScript/screens/today]] | 3 | The Today place: the daily plan view and re-entry after time away. |
| [[Reference/Desktop/TypeScript/screens/underhood/_area|TypeScript/screens/underhood]] | 1 | Under the hood's thin tool entry points (SQLite browser, inspector, calibration, mistake history, AI routes). |
| [[Reference/Desktop/TypeScript/screens/workbench/_area|TypeScript/screens/workbench]] | 12 | The Reader workbench: steps, Check my work, the help ladder, step hints, and the session state behind them. |

## Status and evidence

| Refactor status | Modules | Positive evidence required |
|---|---:|---|
| `ACTIVE` | 311 | Current entry/build reachability, an explicit compiler inclusion, or (test support) an import from a vitest file. |
| `DORMANT` | 0 | An owned retained seam plus evidence that no primary workflow uses it. |
| `COMPAT` | 0 | An explicitly frozen compatibility contract. |
| `EVALUATION` | 0 | A simulation/audit surface that measures rather than serves the learner. |

The audit proves **295 TypeScript/TSX files** are reachable through static imports from `src/main.tsx`, **2 ambient declarations** are included by `tsconfig.json`, **6 test-support files** are imported only by vitest files (they run under `npm test`, never in the app bundle), and **6 Rust modules** are reachable by `mod`/`crate` edges from native `main.rs`.

The reachability set includes all **2 app fixture modules** through current Reader/GoldenPath screens (the other 2 fixture modules are vitest support) and all **8 backdrop/worker modules** through StartScreen's supported optional presentation paths. Entry files are active roots. Therefore all 311 files are `ACTIVE`; none has positive evidence for `DORMANT`, `COMPAT`, or `EVALUATION`.

> [!warning] Static graph limits
> Import and symbol-reference edges are reproducible build evidence, not runtime tracing. The generator refuses an unclassified file instead of treating a missing caller as proof of dormancy; a new implicit entry requires an explicit audit rule.

## Find a desktop module

```query
path:"Reference/Desktop" tag:#learnloop/desktop/typescript
```

```query
path:"Reference/Desktop" section:("Modification guidance") "RPC"
```

> [!tip] Optional Dataview index
> The vault works without Dataview; when enabled, this produces a sortable source table.

```dataview
TABLE language AS Language, area AS Area, source_path AS Source, source_commit_timestamp AS Commit
FROM "Reference/Desktop"
WHERE type = "desktop-module-reference"
SORT source_path ASC
```

## How to change the desktop safely

1. Locate a module through its area map and inspect inbound consumers and outbound dependencies.
2. Follow the canonical workflow/concept links for semantics; do not derive learning policy from UI wording.
3. For an RPC shape change, keep TypeScript DTO/client, Rust command registration/bridge, and Python handler/registry synchronized.
4. Run the focused cross-boundary tests, frontend typecheck/build, and Rust tests named in the module note.
5. Regenerate and validate this reference.

## Maintenance

```bash
.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py
.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py
```

Use `desktop_generate.py --check` in CI to verify byte-for-byte reproducibility without writing files.
