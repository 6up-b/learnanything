---
title: "Desktop module · src/render/pageMathSegments.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.render.pageMathSegments"
language: "TypeScript"
area: "TypeScript/render"
source_path: "apps/learnloop-tauri/src/render/pageMathSegments.ts"
source_paths:
  - "apps/learnloop-tauri/src/render/pageMathSegments.ts"
source_commit: "677db664814feb3446ee0469b65cf4eb5c278b16"
source_commit_timestamp: "2026-11-02T23:12:42-05:00"
source_worktree_state: "clean"
activation_kind: "vitest-support"
activation_evidence: "Outside the Vite build graph: test support imported only by vitest files, directly or through other test support; it runs under `npm test` and is never in the app bundle."
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/reference/module"
  - "learnloop/desktop"
  - "learnloop/desktop/typescript"
  - "refactor/active"
---

# `src/render/pageMathSegments.ts`

Area: [[Reference/Desktop/TypeScript/render/_area|TypeScript/render]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Adapts `pageMathSegments` content editing or rendering into React presentation behavior.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/render/pageMathSegments.ts](../../../../../../apps/learnloop-tauri/src/render/pageMathSegments.ts) |
| Source lines | 82 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/render/_area|TypeScript/render]] |
| Refactor status | `ACTIVE` |
| Activation kind | `vitest-support` |
| Worktree state | `clean` |
| Source commit | `677db664814feb3446ee0469b65cf4eb5c278b16` |
| Commit timestamp | `2026-11-02T23:12:42-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> Outside the Vite build graph: test support imported only by vitest files, directly or through other test support; it runs under `npm test` and is never in the app bundle.
>
> Test-import chain (from a vitest file): [[Reference/Desktop/TypeScript/render/pageMathSegments|src/render/pageMathSegments.ts]]

## Public API

- `export type PageMathSegment =` — type, line 10
- `export function pageMathSegments(value: string): PageMathSegment[]` — function, line 46

## Internal implementation anchors

- `type Hast =` — type, line 12
- `const PROCESSOR = unified().use(remarkParse).use(REMARK_PLUGINS).use(remarkRehype,` — const, line 21
- `function classes(node: Hast): unknown[]` — function, line 23
- `const names = node.properties?.className` — const, line 24
- `function textOf(node: Hast): string` — function, line 28
- `function codePoints(text: string, place: number): number` — function, line 33
- `let count = 0` — let, line 34
- `const unit = text.charCodeAt(at)` — const, line 36
- `const next = text.charCodeAt(at + 1)` — const, line 38
- `const source = value || ""` — const, line 47
- `const tree = PROCESSOR.runSync(PROCESSOR.parse(text)) as unknown as Hast` — const, line 49
- `const found: PageMathSegment[] = []` — const, line 50
- `const visit = (node: Hast, holder: Hast | null, struck: boolean)` — const, line 51
- `const names = classes(node)` — const, line 56
- `const inline = names.includes("math-inline")` — const, line 57
- `const display = names.includes("math-display")` — const, line 58
- `const located = node.position ?? holder?.position` — const, line 61
- `const low = located?.start?.offset` — const, line 62
- `const high = located?.end?.offset` — const, line 63
- `const latex = textOf(node)` — const, line 65
- `const inside = text.indexOf(latex, low)` — const, line 66
- `let begin = from` — let, line 68
- `let end = to` — let, line 70

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

No live desktop source file directly imports this module. Do not infer dormancy: it can still be an implicit entry, worker, ambient declaration, fixture, or runtime-dispatched surface.

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/render/markdownPipeline|src/render/markdownPipeline.ts]] — import-or-re-export; imports `REMARK_PLUGINS`, `normalizeWithPlaces`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `remark-parse`, `remark-rehype`, `unified`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/figures/bookMathRender.test.ts](../../../../../../apps/learnloop-tauri/src/screens/reader/figures/bookMathRender.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/render/pageMathSegments.ts](../../../../../../apps/learnloop-tauri/src/render/pageMathSegments.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
