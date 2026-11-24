---
title: "Desktop module · src/screens/desks/video/VideoWindow.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.video.VideoWindow"
language: "TypeScript"
area: "TypeScript/screens/desks/video"
source_path: "apps/learnloop-tauri/src/screens/desks/video/VideoWindow.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/video/VideoWindow.tsx"
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

# `src/screens/desks/video/VideoWindow.tsx`

Area: [[Reference/Desktop/TypeScript/screens/desks/video/_area|TypeScript/screens/desks/video]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `VideoWindow` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/video/VideoWindow.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/video/VideoWindow.tsx) |
| Source lines | 28 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/video/_area|TypeScript/screens/desks/video]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/video/VideoWindow|src/screens/desks/video/VideoWindow.tsx]]

## Public API

- `export function VideoWindow(` — function, line 13

## Internal implementation anchors

- `const extractionId = source.content.extractionId` — const, line 19
- `const onChapters = useCallback((chapters: VideoChapterDto[])` — const, line 20
- `const decisions = useSyncExternalStore(desk.subscribe, ()` — const, line 21
- `const onDecided = useCallback(()` — const, line 22
- `const ticks = useMemo(()` — const, line 24
- `const onClock = useCallback<NonNullable<VideoExtras["onClock"]>>((clock)` — const, line 25
- `const video = useMemo<VideoExtras>(()` — const, line 26

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `VideoWindow`; references `VideoWindow`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `VideoChapterDto`
- [[Reference/Desktop/TypeScript/api/poller|src/api/poller.ts]] — import-or-re-export; imports `Poller`
- [[Reference/Desktop/TypeScript/screens/desks/video/ChaptersPanel|src/screens/desks/video/ChaptersPanel.tsx]] — import-or-re-export; imports `useVideoChapters`
- [[Reference/Desktop/TypeScript/screens/desks/video/desk|src/screens/desks/video/desk.ts]] — import-or-re-export; imports `VideoDesk`, `VideoTransport`
- [[Reference/Desktop/TypeScript/screens/desks/video/model|src/screens/desks/video/model.ts]] — import-or-re-export; imports `chapterTicks`
- [[Reference/Desktop/TypeScript/screens/desks/windows/SourceWindow|src/screens/desks/windows/SourceWindow.tsx]] — import-or-re-export; imports `SourceWindow`
- [[Reference/Desktop/TypeScript/screens/reader/YouTubeWatchPanel|src/screens/reader/YouTubeWatchPanel.tsx]] — import-or-re-export; imports `VideoExtras`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck`, `npm test` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/video/VideoWindow.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/video/VideoWindow.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
