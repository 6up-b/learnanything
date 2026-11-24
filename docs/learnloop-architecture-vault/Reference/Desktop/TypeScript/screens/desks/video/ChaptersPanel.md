---
title: "Desktop module · src/screens/desks/video/ChaptersPanel.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.video.ChaptersPanel"
language: "TypeScript"
area: "TypeScript/screens/desks/video"
source_path: "apps/learnloop-tauri/src/screens/desks/video/ChaptersPanel.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/video/ChaptersPanel.tsx"
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

# `src/screens/desks/video/ChaptersPanel.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/video/_area|TypeScript/screens/desks/video]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `ChaptersPanel` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/video/ChaptersPanel.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/video/ChaptersPanel.tsx) |
| Source lines | 151 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/video/_area|TypeScript/screens/desks/video]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/video/VideoWindow|src/screens/desks/video/VideoWindow.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/video/ChaptersPanel|src/screens/desks/video/ChaptersPanel.tsx]]

## Public API

- `export interface ChaptersState` — interface, line 12
- `export function useVideoChapters(` — function, line 18

## Internal implementation anchors

- `const current = useRef<VideoChapterDto[]>([])` — const, line 30
- `const whenLive = useWhenLive()` — const, line 33
- `const onChaptersRef = useRef(onChapters)` — const, line 35
- `const onDecidedRef = useRef(onDecided)` — const, line 37
- `const show = useCallback((next: VideoChapterDto[])` — const, line 39
- `let live = true` — let, line 48
- `let timer: number | undefined` — let, line 49
- `const due = out.nextCheckDue ? Date.parse(out.nextCheckDue) : NaN` — const, line 54
- `const settle = useCallback((out: ChaptersJobDto)` — const, line 62
- `const suggest = useCallback(()` — const, line 92
- `const cancel = useCallback(()` — const, line 100
- `const decide = useCallback((chapter: VideoChapterDto, decision: "accept" | "dismiss")` — const, line 105
- `const list = useMemo(()` — const, line 119
- `const side = useMemo(()` — const, line 121
- `const topic = chapter.learningObjects?.[0]` — const, line 125
- `const lo = topic ? chapter.held || topic.held ? "a topic with a cold check due" : topic.title : null` — const, line 126

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/video/VideoWindow|src/screens/desks/video/VideoWindow.tsx]] — import-or-re-export: `useVideoChapters`; references `useVideoChapters`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ChaptersJobDto`, `VideoChapterDto`
- [[Reference/Desktop/TypeScript/api/poller|src/api/poller.ts]] — import-or-re-export; imports `Poller`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `useWhenLive`, `useWindowLifecycle`
- [[Reference/Desktop/TypeScript/screens/desks/video/desk|src/screens/desks/video/desk.ts]] — import-or-re-export; imports `VideoTransport`
- [[Reference/Desktop/TypeScript/screens/desks/video/model|src/screens/desks/video/model.ts]] — import-or-re-export; imports `chapterLabel`, `clockWords`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/video/video.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/video/video.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/video/protection.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/video/protection.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/video/ChaptersPanel.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/video/ChaptersPanel.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
