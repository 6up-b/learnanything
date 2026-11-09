---
title: "Desktop module · src/screens/reader/SideBySidePane.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.SideBySidePane"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/SideBySidePane.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/SideBySidePane.tsx"
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

# `src/screens/reader/SideBySidePane.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `SideBySidePane` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/SideBySidePane.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/SideBySidePane.tsx) |
| Source lines | 378 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/SideBySidePane|src/screens/reader/SideBySidePane.tsx]]

## Public API

- `export interface PaneSelection` — interface, line 42
- `export interface SideBySidePaneProps` — interface, line 49
- `export const SIDE_PANE_COPY =` — const, line 77
- `export const SideBySidePane = forwardRef<HTMLDivElement, SideBySidePaneProps>(function SideBySidePane(` — const, line 137

## Internal implementation anchors

- `const LINK: CSSProperties =` — const, line 36
- `function useOwnMarks(sourceId: string | null, extractionId: string | null, enabled: boolean, version = 0): [Map<string, string>, ()` — function, line 86
- `let live = true` — let, line 94
- `const next = new Map<string, string>()` — const, line 99
- `const version = (row.version as Record<string, unknown>) ??` — const, line 101
- `const spanId = String(segment.spanId ?? "")` — const, line 103
- `function selectionIn(root: HTMLElement | null): PaneSelection | null` — function, line 115
- `const sel = window.getSelection()` — const, line 116
- `const range = sel.getRangeAt(0)` — const, line 118
- `const quote = sel.toString().replace(/\s+/g, " ").trim()` — const, line 120
- `const spans: string[] = []` — const, line 122
- `const nodes: PaneSelection["nodes"] = []` — const, line 123
- `const part = document.createRange()` — const, line 127
- `const words = part.toString().replace(/\s+/g, " ").trim()` — const, line 131
- `const scrollRef = useRef<HTMLDivElement | null>(null)` — const, line 141
- `const target = ctl.target` — const, line 144
- `const section = ctl.section && target && ctl.section.sectionId === target.sectionId ? ctl.section : null` — const, line 145
- `const draftKey = section ? `$` — const, line 149
- `const selection = draft && draft.key === draftKey ? draft.selection : null` — const, line 151
- `const noting = draft && draft.key === draftKey ? draft.noting : null` — const, line 152
- `const setSelection = useCallback((picked: PaneSelection | null)` — const, line 153
- `const setNoting = useCallback((text: string | null)` — const, line 157
- `const canCapture = Boolean(onCaptured && section?.revisionId)` — const, line 161
- `const sheet = ctl.sheet` — const, line 163
- `const leads = ctl.panes && ctl.leader === "side"` — const, line 164
- `const sectionKey = section ? `$` — const, line 169
- `const node = scrollRef.current` — const, line 172
- `const capture = async (kind: "highlight" | "annotate", picked: PaneSelection, learnerText: string)` — const, line 179
- `const setRefs = useCallback((node: HTMLDivElement | null)` — const, line 201
- `const touch = ()` — const, line 208
- `const onKeyDown = (event: KeyboardEvent<HTMLDivElement>)` — const, line 209
- `const header: ReactNode = ( <div data-sbs-header="" style=` — const, line 220
- `const picked = selectionIn(scrollRef.current)` — const, line 267
- `const folded = Boolean(fold?.spans.has(block.spanId))` — const, line 286
- `const firstFolded = folded && !(index > 0 && fold?.spans.has(section.blocks[index - 1].spanId))` — const, line 287
- `const cue = folded ? null : marginFor?.(block.spanId) ?? null` — const, line 288

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `SideBySidePane`; references `SideBySidePane`
- [[Reference/Desktop/TypeScript/screens/reader/useSideBySide|src/screens/reader/useSideBySide.ts]] — import-or-re-export: `PaneSelection`; references `PaneSelection`
- [[Reference/Desktop/TypeScript/screens/reader/useSidePane|src/screens/reader/useSidePane.ts]] — import-or-re-export: `PaneSelection`; references `PaneSelection`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/reader/IntentBox|src/screens/reader/IntentBox.tsx]] — import-or-re-export; imports `IntentBox`
- [[Reference/Desktop/TypeScript/screens/reader/activity|src/screens/reader/activity.ts]] — import-or-re-export; imports `newActivityId`
- [[Reference/Desktop/TypeScript/screens/reader/readerShared|src/screens/reader/readerShared.ts]] — import-or-re-export; imports `clip`
- [[Reference/Desktop/TypeScript/screens/reader/useIntentBox|src/screens/reader/useIntentBox.ts]] — import-or-re-export; imports `IntentBoxController`
- [[Reference/Desktop/TypeScript/screens/reader/useSideBySide|src/screens/reader/useSideBySide.ts]] — import-or-re-export; imports `SIDE_BY_SIDE_COPY`, `SIDE_BY_SIDE_SCROLL_KEYS`, `SideBySide`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `MeaningLabel`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/sideBySideReader.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/sideBySideReader.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/sideBySideIntent.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/sideBySideIntent.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/SideBySidePane.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/SideBySidePane.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
