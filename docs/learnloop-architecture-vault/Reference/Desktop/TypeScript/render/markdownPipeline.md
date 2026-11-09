---
title: "Desktop module · src/render/markdownPipeline.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.render.markdownPipeline"
language: "TypeScript"
area: "TypeScript/render"
source_path: "apps/learnloop-tauri/src/render/markdownPipeline.ts"
source_paths:
  - "apps/learnloop-tauri/src/render/markdownPipeline.ts"
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

# `src/render/markdownPipeline.ts`

Area: [[Reference/Desktop/TypeScript/render/_area|TypeScript/render]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Adapts `markdownPipeline` content editing or rendering into React presentation behavior.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/render/markdownPipeline.ts](../../../../../../apps/learnloop-tauri/src/render/markdownPipeline.ts) |
| Source lines | 71 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/render/_area|TypeScript/render]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] → [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] → [[Reference/Desktop/TypeScript/render/markdownPipeline|src/render/markdownPipeline.ts]]

## Public API

- `export type NormalizedText =` — type, line 15
- `export function normalizeWithPlaces(value: string): NormalizedText` — function, line 49
- `export function normalizeMathDelimiters(value: string): string` — function, line 66
- `export const REMARK_PLUGINS = [remarkGfm, remarkMath]` — const, line 71

## Internal implementation anchors

- `const CODE_SEGMENT = /(```[\s\S]*?(?:```|$)|~~~[\s\S]*?(?:~~~|$)|`[^`\n]*`)/g` — const, line 11
- `const WRITTEN = -1` — const, line 12
- `function rewrite(input: NormalizedText, pattern: RegExp, open: string, close: string): NormalizedText` — function, line 17
- `const out: NormalizedText =` — const, line 18
- `const copy = (from: number, to: number)` — const, line 19
- `const write = (text: string)` — const, line 23
- `let last = 0` — let, line 27
- `const at = match.index` — const, line 29
- `const body = match[1]` — const, line 30
- `const begin = at + 2 + (body.length - body.trimStart().length)` — const, line 31
- `function rewriteDelimiters(text: string, offset: number): NormalizedText` — function, line 42
- `const start: NormalizedText =` — const, line 43
- `const display = rewrite(start, /\\\[([\s\S]+?)\\\]/g, "\n$$\n", "\n$$\n")` — const, line 45
- `const out: NormalizedText =` — const, line 50
- `let offset = 0` — let, line 51
- `const done = rewriteDelimiters(segment, offset)` — const, line 57

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export: `REMARK_PLUGINS`, `normalizeMathDelimiters`; references `REMARK_PLUGINS`, `normalizeMathDelimiters`
- [[Reference/Desktop/TypeScript/render/pageMathSegments|src/render/pageMathSegments.ts]] — import-or-re-export: `REMARK_PLUGINS`, `normalizeWithPlaces`; references `REMARK_PLUGINS`, `normalizeWithPlaces`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

- Imported packages/crates: `remark-gfm`, `remark-math`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/figures/bookMathRender.test.ts](../../../../../../apps/learnloop-tauri/src/screens/reader/figures/bookMathRender.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/render/markdownPipeline.ts](../../../../../../apps/learnloop-tauri/src/render/markdownPipeline.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
