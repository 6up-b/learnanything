---
title: "Desktop module · src/screens/reader/DeliverableScope.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.DeliverableScope"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/DeliverableScope.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/DeliverableScope.tsx"
source_commit: "1bd537ae4527bb8d6bd5360ec8560b6947c7827c"
source_commit_timestamp: "2026-10-31T16:21:48-04:00"
source_worktree_state: "staged-or-mixed"
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

# `src/screens/reader/DeliverableScope.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `DeliverableScope` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/DeliverableScope.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/DeliverableScope.tsx) |
| Source lines | 372 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `staged-or-mixed` |
| Source commit | `1bd537ae4527bb8d6bd5360ec8560b6947c7827c` |
| Commit timestamp | `2026-10-31T16:21:48-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/DeliverableSliceCard|src/screens/reader/DeliverableSliceCard.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/DeliverableScope|src/screens/reader/DeliverableScope.tsx]]

## Public API

- `export const SCOPE_DEPTHS: Array<` — const, line 31
- `export const SCOPE_COPY =` — const, line 37
- `export function scopeSummary(scope: DeliverableScopeDto): string` — function, line 76
- `export function scopeNotice(result:` — function, line 81
- `export interface DeliverableScopePanelProps` — interface, line 85
- `export function DeliverableScopePanel(` — function, line 91
- `export interface DeliverableEntryProps` — interface, line 263
- `export function DeliverableEntry(` — function, line 270

## Internal implementation anchors

- `const LINK =` — const, line 21
- `const INPUT =` — const, line 25
- `const syllabi = scope.syllabi ?? []` — const, line 104
- `const subjects = scope.subjects ?? []` — const, line 105
- `const choosing = (scope.subjectId == null || askSubject) && subjects.length > 0 && scope.unmatched.some((entry)` — const, line 106
- `const send = async (kind: "correction" | "text", text: string, clear: ()` — const, line 109
- `const out = await api.curriculumSetScope(` — const, line 112
- `const attachSyllabus = async (extractionId: string)` — const, line 123
- `const out = await api.curriculumSetScope(` — const, line 126
- `const decide = async (phrase: string, decision: "create" | "decline")` — const, line 137
- `const chosen = decision === "create" && choosing && subjectId ?` — const, line 140
- `const out = await api.curriculumScopeDecide(` — const, line 141
- `const setDepth = async (depth: ReadingPathDepth)` — const, line 152
- `function TextBox(` — function, line 247
- `const load = useCallback(async ()` — const, line 280
- `const out = await api.curriculumDeliverables()` — const, line 282
- `const replace = (scope: DeliverableScopeDto)` — const, line 291
- `const others = current.filter((entry)` — const, line 293
- `const make = async ()` — const, line 299
- `const created = await api.curriculumCreateDeliverable(` — const, line 302
- `let scope = created.scope` — let, line 303
- `let message = scopeNotice(created)` — let, line 304
- `const listed = await api.curriculumSetScope(` — const, line 306

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/DeliverableSliceCard|src/screens/reader/DeliverableSliceCard.tsx]] — import-or-re-export: `DeliverableEntry`, `DeliverableScopePanel`, `scopeNotice`; references `DeliverableEntry`, `DeliverableScopePanel`, `scopeNotice`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `DeliverableScopeDto`, `ReadingPathDepth`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Card`, `FONT_MONO`, `Faint`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`, `getCommandError`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/DeliverableSliceCard.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/DeliverableSliceCard.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/DeliverableScope.syllabus.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/DeliverableScope.syllabus.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/syllabusRole.test.tsx](../../../../../../../apps/learnloop-tauri/src/components/syllabusRole.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_reader.py](../../../../../../../tests/test_sidecar_reader.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../../tests/test_sidecar_reader_pdf_view.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_render_views.py](../../../../../../../tests/test_reader_render_views.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_requests.py](../../../../../../../tests/test_reader_requests.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/reader/DeliverableScope.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/DeliverableScope.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
