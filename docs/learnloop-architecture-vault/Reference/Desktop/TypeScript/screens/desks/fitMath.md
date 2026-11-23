---
title: "Desktop module · src/screens/desks/fitMath.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.fitMath"
language: "TypeScript"
area: "TypeScript/screens/desks"
source_path: "apps/learnloop-tauri/src/screens/desks/fitMath.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/fitMath.tsx"
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

# `src/screens/desks/fitMath.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/_area|TypeScript/screens/desks]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `fitMath` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/fitMath.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/fitMath.tsx) |
| Source lines | 64 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/_area|TypeScript/screens/desks]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/LessonView|src/screens/LessonView.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/fitMath|src/screens/desks/fitMath.tsx]]

## Public API

- `export const MIN_MATH_SCALE = 0.75` — const, line 8
- `export function fitDisplayMath(root: HTMLElement): Array<"fits" | "scaled" | "scrolls">` — function, line 11
- `export function FitMath(` — function, line 40

## Internal implementation anchors

- `const out: Array<"fits" | "scaled" | "scrolls"> = []` — const, line 12
- `const math = display.querySelector<HTMLElement>(":scope > .katex")` — const, line 14
- `const column = display.clientWidth` — const, line 19
- `const natural = math.scrollWidth` — const, line 20
- `const scale = column / natural` — const, line 25
- `const ref = useRef<HTMLElement | null>(null)` — const, line 41
- `const node = ref.current` — const, line 43
- `let live = true` — let, line 45
- `const fit = ()` — const, line 46
- `const fonts = typeof document !== "undefined" ? (document as Document &` — const, line 50
- `const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(fit)` — const, line 52
- `const mutations = typeof MutationObserver === "undefined" ? null : new MutationObserver(fit)` — const, line 55

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/LessonView|src/screens/LessonView.tsx]] — import-or-re-export: `FitMath`; references `FitMath`
- [[Reference/Desktop/TypeScript/screens/desks/companion/Companion|src/screens/desks/companion/Companion.tsx]] — import-or-re-export: `FitMath`; references `FitMath`
- [[Reference/Desktop/TypeScript/screens/desks/pads/PadStackWindow|src/screens/desks/pads/PadStackWindow.tsx]] — import-or-re-export: `FitMath`; references `FitMath`
- [[Reference/Desktop/TypeScript/screens/desks/pen/InkLine|src/screens/desks/pen/InkLine.tsx]] — import-or-re-export: `FitMath`; references `FitMath`
- [[Reference/Desktop/TypeScript/screens/desks/windows/ThreadWindow|src/screens/desks/windows/ThreadWindow.tsx]] — import-or-re-export: `FitMath`; references `FitMath`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/fitMath.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/fitMath.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/fitMath.tsx](../../../../../../../apps/learnloop-tauri/src/screens/desks/fitMath.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
