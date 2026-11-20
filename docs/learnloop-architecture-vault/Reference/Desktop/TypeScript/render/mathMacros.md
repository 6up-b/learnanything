---
title: "Desktop module · src/render/mathMacros.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.render.mathMacros"
language: "TypeScript"
area: "TypeScript/render"
source_path: "apps/learnloop-tauri/src/render/mathMacros.tsx"
source_paths:
  - "apps/learnloop-tauri/src/render/mathMacros.tsx"
activation_kind: "entry-reachable build graph"
activation_evidence: "A static TypeScript import path reaches this file from the Vite entry src/main.tsx."
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/reference/module"
  - "learnloop/desktop"
  - "learnloop/desktop/typescript"
  - "refactor/active"
---

# `src/render/mathMacros.tsx`

Area: [[Reference/Desktop/TypeScript/render/_area|TypeScript/render]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Adapts `mathMacros` content editing or rendering into React presentation behavior.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/render/mathMacros.tsx](../../../../../../apps/learnloop-tauri/src/render/mathMacros.tsx) |
| Source lines | 25 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/render/_area|TypeScript/render]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/render/mathMacros|src/render/mathMacros.tsx]]

## Public API

- `export type MathMacros = Readonly<Record<string, string>>` — type, line 13
- `export function MathMacrosProvider(` — function, line 17
- `export function useMathMacros(): MathMacros | null` — function, line 23

## Internal implementation anchors

- `const MathMacrosContext = createContext<MathMacros | null>(null)` — const, line 15
- `const table = macros && Object.keys(macros).length > 0 ? macros : null` — const, line 18

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export: `useMathMacros`; references `useMathMacros`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `MathMacrosProvider`; references `MathMacrosProvider`
- [[Reference/Desktop/TypeScript/screens/reader/SideBySidePane|src/screens/reader/SideBySidePane.tsx]] — import-or-re-export: `MathMacrosProvider`; references `MathMacrosProvider`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/render/sourceMacros.test.tsx](../../../../../../apps/learnloop-tauri/src/render/sourceMacros.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/render/mathMacros.tsx](../../../../../../apps/learnloop-tauri/src/render/mathMacros.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
