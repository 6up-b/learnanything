---
title: "Desktop module · src/components/highlight.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.highlight"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/highlight.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/highlight.tsx"
source_commit: "4a28c9635f24945d78366fa26212db7488d82545"
source_commit_timestamp: "2026-05-28T11:36:12-04:00"
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

# `src/components/highlight.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `highlight` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/highlight.tsx](../../../../../../apps/learnloop-tauri/src/components/highlight.tsx) |
| Source lines | 273 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `4a28c9635f24945d78366fa26212db7488d82545` |
| Commit timestamp | `2026-05-28T11:36:12-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LibraryScreen|src/screens/LibraryScreen.tsx]] → [[Reference/Desktop/TypeScript/components/highlight|src/components/highlight.tsx]]

## Public API

- `export function highlightYaml(src: string): ReactNode[]` — function, line 35
- `export function highlightMarkdown(src: string): ReactNode[]` — function, line 198
- `export function highlightFor(kind: string | undefined, body: string): ReactNode[]` — function, line 268

## Internal implementation anchors

- `const PROSE_KEYS = new Set([ "description", "expected_answer", "prompt", "quote", "summary", "title" ])` — const, line 8
- `const ID_KEYS = new Set([ "concept", "id", "learning_object_id", "path", "practice_mode", "ref_id", "ref_type", "status" ])` — const, line 17
- `const DATE_KEYS = new Set(["created_at", "updated_at"])` — const, line 28
- `type YamlContinuation =` — type, line 30
- `let continuation: YamlContinuation | null = null` — let, line 36
- `const key = `y$` — const, line 39
- `const indent = line.match(/^(\s*)/)?.[0] ?? ""` — const, line 40
- `const indentWidth = indent.length` — const, line 41
- `const rest = line.slice(indent.length)` — const, line 42
- `const listKeyMatch = rest.match(/^- ([A-Za-z0-9_-]+):\s?(.*)$/)` — const, line 63
- `const value = rest.slice(2)` — const, line 78
- `const match = rest.match(/^([A-Za-z0-9_-]+):\s?(.*)$/)` — const, line 90
- `function renderYamlPair(field: string, value: string): ReactNode` — function, line 124
- `function renderYamlScalar(field: string, value: string): ReactNode` — function, line 139
- `const block = value.match(/^([|>])([+-])?$/)` — const, line 140
- `const color = scalarColor(value, field)` — const, line 145
- `const commentIndex = value.indexOf(" #")` — const, line 146
- `function renderIndent(indent: string): ReactNode` — function, line 159
- `function nextContinuation(indent: number, field: string, value: string): YamlContinuation | null` — function, line 163
- `function isCompactScalar(value: string): boolean` — function, line 171
- `const trimmed = value.trim()` — const, line 172
- `function scalarColor(value: string, field?: string): string` — function, line 184
- `const trimmed = value.trim()` — const, line 185
- `const key = `m$` — const, line 200
- `const parts = line.split(/(`[^`]+`|\*\*[^*]+\*\*)/)` — const, line 242

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/LibraryScreen|src/screens/LibraryScreen.tsx]] — import-or-re-export: `highlightFor`; references `highlightFor`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_sidecar_reader.py](../../../../../../tests/test_sidecar_reader.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../tests/test_sidecar_reader_pdf_view.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_render_views.py](../../../../../../tests/test_reader_render_views.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_requests.py](../../../../../../tests/test_reader_requests.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/highlight.tsx](../../../../../../apps/learnloop-tauri/src/components/highlight.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
