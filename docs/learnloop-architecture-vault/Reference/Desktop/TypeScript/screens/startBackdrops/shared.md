---
title: "Desktop module · src/screens/startBackdrops/shared.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.startBackdrops.shared"
language: "TypeScript"
area: "TypeScript/screens/startBackdrops"
source_path: "apps/learnloop-tauri/src/screens/startBackdrops/shared.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/startBackdrops/shared.ts"
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

# `src/screens/startBackdrops/shared.ts`

Area: [[Reference/Desktop/TypeScript/screens/startBackdrops/_area|TypeScript/screens/startBackdrops]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `shared` start-screen visualization or its rendering support.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/startBackdrops/shared.ts](../../../../../../../apps/learnloop-tauri/src/screens/startBackdrops/shared.ts) |
| Source lines | 99 |
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
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/startBackdrops/shared|src/screens/startBackdrops/shared.ts]]

## Public API

- `export const CHAR_W = 7` — const, line 11
- `export const CHAR_H = 12` — const, line 12
- `export type Rgb = [number, number, number]` — type, line 14
- `export type BackdropPalette =` — type, line 16
- `export function readPaletteColors(): BackdropPalette` — function, line 62
- `export const BLACK: Rgb = [0, 0, 0]` — const, line 80
- `export function rgba(c: Rgb, a: number): string` — function, line 82
- `export function mixRgb(a: Rgb, b: Rgb, t: number): Rgb` — function, line 87
- `export function prefersReducedMotion(): boolean` — function, line 97

## Internal implementation anchors

- `const FALLBACK: BackdropPalette =` — const, line 30
- `function parseHex(raw: string, fallback: Rgb): Rgb` — function, line 43
- `const hex = raw.trim().replace(/^#/, "")` — const, line 44
- `const style = getComputedStyle(document.documentElement)` — const, line 63
- `const read = (token: string, fallback: Rgb): Rgb` — const, line 64

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] — import-or-re-export: `BLACK`, `mixRgb`, `prefersReducedMotion`, `readPaletteColors`, `rgba`; references `BLACK`, `mixRgb`, `prefersReducedMotion`, `readPaletteColors`, `rgba`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/CliffordBackdrop|src/screens/startBackdrops/CliffordBackdrop.tsx]] — import-or-re-export: `BLACK`, `mixRgb`, `prefersReducedMotion`, `readPaletteColors`, `rgba`; references `BLACK`, `mixRgb`, `prefersReducedMotion`, `readPaletteColors`, `rgba`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/JuliaBackdrop|src/screens/startBackdrops/JuliaBackdrop.tsx]] — import-or-re-export: `CHAR_H`, `CHAR_W`, `prefersReducedMotion`; references `CHAR_H`, `CHAR_W`, `prefersReducedMotion`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/LifeBackdrop|src/screens/startBackdrops/LifeBackdrop.tsx]] — import-or-re-export: `CHAR_H`, `CHAR_W`, `prefersReducedMotion`; references `CHAR_H`, `CHAR_W`, `prefersReducedMotion`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/PendulumBackdrop|src/screens/startBackdrops/PendulumBackdrop.tsx]] — import-or-re-export: `BLACK`, `Rgb`, `mixRgb`, `prefersReducedMotion`, `readPaletteColors`, `rgba`; references `BLACK`, `Rgb`, `mixRgb`, `prefersReducedMotion`, `readPaletteColors`, `rgba`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/ThreeBodyBackdrop|src/screens/startBackdrops/ThreeBodyBackdrop.tsx]] — import-or-re-export: `BLACK`, `Rgb`, `mixRgb`, `prefersReducedMotion`, `readPaletteColors`, `rgba`; references `BLACK`, `Rgb`, `mixRgb`, `prefersReducedMotion`, `readPaletteColors`, `rgba`
- [[Reference/Desktop/TypeScript/screens/startBackdrops/glyphAtlas|src/screens/startBackdrops/glyphAtlas.ts]] — import-or-re-export: `CHAR_H`, `CHAR_W`, `mixRgb`, `readPaletteColors`, `rgba`; references `CHAR_H`, `CHAR_W`, `mixRgb`, `readPaletteColors`, `rgba`

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

1. Modify [apps/learnloop-tauri/src/screens/startBackdrops/shared.ts](../../../../../../../apps/learnloop-tauri/src/screens/startBackdrops/shared.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
