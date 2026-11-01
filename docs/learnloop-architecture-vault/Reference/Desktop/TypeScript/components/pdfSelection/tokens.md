---
title: "Desktop module · src/components/pdfSelection/tokens.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.pdfSelection.tokens"
language: "TypeScript"
area: "TypeScript/components/pdfSelection"
source_path: "apps/learnloop-tauri/src/components/pdfSelection/tokens.ts"
source_paths:
  - "apps/learnloop-tauri/src/components/pdfSelection/tokens.ts"
source_commit: "b1087be0a01909d5363e9c41f140e27673801640"
source_commit_timestamp: "2026-10-15T14:19:42-04:00"
source_worktree_state: "clean"
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

# `src/components/pdfSelection/tokens.ts`

Area: [[Reference/Desktop/TypeScript/components/pdfSelection/_area|TypeScript/components/pdfSelection]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides shared `tokens` state or utility behavior for desktop components.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/pdfSelection/tokens.ts](../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/tokens.ts) |
| Source lines | 172 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/pdfSelection/_area|TypeScript/components/pdfSelection]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `b1087be0a01909d5363e9c41f140e27673801640` |
| Commit timestamp | `2026-10-15T14:19:42-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/components/pdfSelection/model|src/components/pdfSelection/model.ts]] → [[Reference/Desktop/TypeScript/components/pdfSelection/tokens|src/components/pdfSelection/tokens.ts]]

## Public API

- `export interface Token` — interface, line 12
- `export const ATOMIC_TYPES: ReadonlySet<string> = new Set([ "Equation", "Table", "TableGroup", "Figure", "FigureGroup", "Picture", "PictureGroup", "Form", "ComplexRegion", "Handwriting", ])` — const, line 28
- `export const FURNITURE_TYPES: ReadonlySet<string> = new Set(["PageHeader", "PageFooter", "TableOfContents"])` — const, line 43
- `export function isAtomicType(blockType: string | null | undefined): boolean` — function, line 48
- `export function keyOf(text: string): string` — function, line 55
- `export function tokenize(text: string): Token[]` — function, line 106
- `export function toCodepoint(text: string, index: number): number` — function, line 143
- `export function fromCodepoint(text: string, codepoint: number): number` — function, line 149
- `export function cleanText(slice: string, blockType: string | null | undefined): string` — function, line 166

## Internal implementation anchors

- `const VERBATIM_TYPES: ReadonlySet<string> = new Set(["Code"])` — const, line 46
- `const LATEX_COMMAND = /\\[a-zA-Z]+/g` — const, line 52
- `function glyphCount(text: string, math: boolean): number` — function, line 63
- `const visible = text.replace(/\*\*|__|`/g, "").replace(LATEX_COMMAND, "x")` — const, line 65
- `function mathClose(text: string, at: number): number` — function, line 70
- `const close = text.indexOf("$$", at + 2)` — const, line 72
- `const close = text.indexOf("\\)", at + 2)` — const, line 89
- `const close = text.indexOf("\\]", at + 2)` — const, line 93
- `function opensMath(text: string, at: number): boolean` — function, line 99
- `const tokens: Token[] = []` — const, line 107
- `let start = -1` — let, line 108
- `let math = false` — let, line 109
- `const close = (end: number)` — const, line 110
- `const piece = text.slice(start, end)` — const, line 112
- `let i = 0` — let, line 117
- `const ch = text[i]` — const, line 119
- `const end = mathClose(text, i)` — const, line 127
- `let index = 0` — let, line 150
- `let count = 0` — let, line 151
- `const code = text.charCodeAt(index)` — const, line 153

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/pdfSelection/geometry|src/components/pdfSelection/geometry.ts]] — import-or-re-export: `Token`, `keyOf`; references `Token`, `keyOf`
- [[Reference/Desktop/TypeScript/components/pdfSelection/model|src/components/pdfSelection/model.ts]] — import-or-re-export: `FURNITURE_TYPES`, `Token`, `cleanText`, `fromCodepoint`, `isAtomicType`, `keyOf`, `toCodepoint`, `tokenize`; references `FURNITURE_TYPES`, `Token`, `cleanText`, `fromCodepoint`, `isAtomicType`, `keyOf`, `toCodepoint`, `tokenize`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/pdfSelection/model.test.ts](../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/model.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/pdfSelection/tokens.ts](../../../../../../../apps/learnloop-tauri/src/components/pdfSelection/tokens.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
