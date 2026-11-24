---
title: "Desktop module · src/screens/desks/video/model.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.video.model"
language: "TypeScript"
area: "TypeScript/screens/desks/video"
source_path: "apps/learnloop-tauri/src/screens/desks/video/model.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/video/model.ts"
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

# `src/screens/desks/video/model.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/video/_area|TypeScript/screens/desks/video]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `clockWords`, `FollowedPassage`, `choosePassage`, `chapterWords` and related exports within the desktop's TypeScript/screens/desks/video ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/video/model.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/video/model.ts) |
| Source lines | 77 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/video/_area|TypeScript/screens/desks/video]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/video/model|src/screens/desks/video/model.ts]]

## Public API

- `export function clockWords(seconds: number): string` — function, line 7
- `export interface FollowedPassage` — interface, line 15
- `export function choosePassage(result: FollowAlongDto | null, bookExtractionId: string, primaryFor: (learningObjectId: string)` — function, line 24
- `export function chapterWords(result: FollowAlongDto | null): string` — function, line 38
- `export type FollowChipState = |` — type, line 42
- `export function chipText(state: FollowChipState): string` — function, line 49
- `export function chapterTicks(chapters: readonly VideoChapterDto[]): Array<` — function, line 63
- `export function chapterRanges(chapters: readonly VideoChapterDto[], duration: number): Array<` — function, line 68
- `export function timestampLine(videoTitle: string, t: number): string` — function, line 75

## Internal implementation anchors

- `const s = Math.max(0, Math.floor(seconds))` — const, line 8
- `const h = Math.floor(s / 3600)` — const, line 9
- `const m = Math.floor((s % 3600) / 60)` — const, line 10
- `const rest = String(s % 60).padStart(2, "0")` — const, line 11
- `const candidates = result.learningObjects.flatMap((group)` — const, line 27
- `const primary = candidates.find((candidate)` — const, line 30
- `const path = primaryFor(candidate.learningObjectId)` — const, line 31

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `timestampLine`; references `timestampLine`
- [[Reference/Desktop/TypeScript/screens/desks/video/ChaptersPanel|src/screens/desks/video/ChaptersPanel.tsx]] — import-or-re-export: `clockWords`; references `clockWords`
- [[Reference/Desktop/TypeScript/screens/desks/video/FollowChip|src/screens/desks/video/FollowChip.tsx]] — import-or-re-export: `chipText`; references `chipText`
- [[Reference/Desktop/TypeScript/screens/desks/video/VideoWindow|src/screens/desks/video/VideoWindow.tsx]] — import-or-re-export: `chapterTicks`; references `chapterTicks`
- [[Reference/Desktop/TypeScript/screens/desks/video/desk|src/screens/desks/video/desk.ts]] — import-or-re-export: `FollowChipState`, `FollowedPassage`, `chapterRanges`, `chapterWords`, `choosePassage`; references `FollowChipState`, `FollowedPassage`, `chapterRanges`, `chapterWords`, `choosePassage`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `FollowAlongDto`, `VideoChapterDto`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/video/video.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/video/video.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/video/model.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/video/model.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
