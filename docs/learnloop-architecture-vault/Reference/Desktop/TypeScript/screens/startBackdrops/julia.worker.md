---
title: "Desktop module · src/screens/startBackdrops/julia.worker.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.startBackdrops.julia.worker"
language: "TypeScript"
area: "TypeScript/screens/startBackdrops"
source_path: "apps/learnloop-tauri/src/screens/startBackdrops/julia.worker.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/startBackdrops/julia.worker.ts"
source_commit: "971d7c274e09873d726d43578cd080e4d8865571"
source_commit_timestamp: "2026-07-27T06:01:19-04:00"
source_worktree_state: "clean"
activation_kind: "entry-reachable build graph"
activation_evidence: "Imported through StartScreen's supported optional backdrop paths reachable from src/main.tsx."
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/reference/module"
  - "learnloop/desktop"
  - "learnloop/desktop/typescript"
  - "refactor/active"
---

# `src/screens/startBackdrops/julia.worker.ts`

Area: [[Reference/Desktop/TypeScript/screens/startBackdrops/_area|TypeScript/screens/startBackdrops]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `julia.worker` start-screen visualization or its rendering support.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/startBackdrops/julia.worker.ts](../../../../../../../apps/learnloop-tauri/src/screens/startBackdrops/julia.worker.ts) |
| Source lines | 93 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/startBackdrops/_area|TypeScript/screens/startBackdrops]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `971d7c274e09873d726d43578cd080e4d8865571` |
| Commit timestamp | `2026-07-27T06:01:19-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> Imported through StartScreen's supported optional backdrop paths reachable from src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/startBackdrops/JuliaBackdrop|src/screens/startBackdrops/JuliaBackdrop.tsx]] → [[Reference/Desktop/TypeScript/screens/startBackdrops/julia.worker|src/screens/startBackdrops/julia.worker.ts]]

## Public API

No exported declaration was detected; this is an entry, side-effect, fixture, or file-local module.

## Internal implementation anchors

- `const MAX_IT = 28` — const, line 1
- `type JuliaFrameRequest =` — type, line 3
- `type JuliaFrameResponse =` — type, line 13
- `let cachedCols = 0` — let, line 20
- `let cachedRows = 0` — let, line 21
- `let cachedReSpan = 0` — let, line 22
- `let cachedImSpan = 0` — let, line 23
- `let realCoordinates = new Float64Array(0)` — let, line 24
- `let imaginaryCoordinates = new Float64Array(0)` — let, line 25
- `function prepareCoordinates(cols: number, rows: number, reSpan: number, imSpan: number): void` — function, line 27
- `const realStep = reSpan / Math.max(1, cols - 1)` — const, line 44
- `const imaginaryStep = imSpan / Math.max(1, rows - 1)` — const, line 45
- `let value = -reSpan * 0.5` — let, line 46
- `function computeFrame(request: JuliaFrameRequest): Uint8Array` — function, line 52
- `const result = new Uint8Array(cols * rows)` — const, line 55
- `let offset = 0` — let, line 56
- `const initialZi = imaginaryCoordinates[y]` — const, line 59
- `let zr = realCoordinates[x]` — let, line 61
- `let zi = initialZi` — let, line 62
- `let zr2 = zr * zr` — let, line 63
- `let zi2 = zi * zi` — let, line 64
- `let iteration = 0` — let, line 65
- `const request = event.data` — const, line 82
- `const iterations = computeFrame(request)` — const, line 83
- `const response: JuliaFrameResponse =` — const, line 84

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/startBackdrops/JuliaBackdrop|src/screens/startBackdrops/JuliaBackdrop.tsx]] — import-or-re-export: `JuliaWorker`; references `JuliaWorker`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/startBackdrops/julia.worker.ts](../../../../../../../apps/learnloop-tauri/src/screens/startBackdrops/julia.worker.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
