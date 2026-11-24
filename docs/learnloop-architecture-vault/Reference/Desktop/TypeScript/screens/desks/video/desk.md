---
title: "Desktop module · src/screens/desks/video/desk.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.desks.video.desk"
language: "TypeScript"
area: "TypeScript/screens/desks/video"
source_path: "apps/learnloop-tauri/src/screens/desks/video/desk.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/video/desk.ts"
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

# `src/screens/desks/video/desk.ts`

Area: [[Reference/Desktop/TypeScript/screens/desks/video/_area|TypeScript/screens/desks/video]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `VideoTransport`, `LIVE_VIDEO_TRANSPORT`, `VideoClock`, `DeskVideos` and related exports within the desktop's TypeScript/screens/desks/video ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/desks/video/desk.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/video/desk.ts) |
| Source lines | 243 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/desks/video/_area|TypeScript/screens/desks/video]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] → [[Reference/Desktop/TypeScript/screens/desks/video/desk|src/screens/desks/video/desk.ts]]

## Public API

- `export interface VideoTransport` — interface, line 13
- `export const LIVE_VIDEO_TRANSPORT: VideoTransport =` — const, line 24
- `export interface VideoClock` — interface, line 34
- `export interface DeskVideos` — interface, line 42
- `export function pastCheck(result:` — function, line 58
- `export class VideoDesk` — class, line 63

## Internal implementation anchors

- `interface Followed` — interface, line 47
- `const NO_PRIMARY = ()` — const, line 55
- `const due = result?.nextCheckDue ? Date.parse(result.nextCheckDue) : NaN` — const, line 59
- `const before = JSON.stringify(this.layout)` — const, line 96
- `const before = this.clocks.get(windowId)` — const, line 110
- `let best:` — let, line 127
- `let at = 0` — let, line 128
- `const seq = this.played.get(video.windowId) ?? 0` — const, line 130
- `const driver = this.driver()` — const, line 137
- `const clock = this.clocks.get(driver.windowId)` — const, line 139
- `const known = this.followed.get(book.windowId)` — const, line 143
- `const section = known?.result.section` — const, line 144
- `const inside = section ? clock.t >= section.t0 && (section.t1 === null || clock.t < section.t1) : known?.result.t !== -1` — const, line 145
- `const fresh = known && known.videoExtractionId === driver.extractionId && !pastCheck(known.result) && (inside || Math.floor(known.askedT) === Math.floor(clock.t))` — const, line 146
- `const book = this.layout.books.find((each)` — const, line 160
- `const before = this.followed.get(bookWindowId)?.passage ?? null` — const, line 165
- `const passage = choosePassage(result, bookExtractionId, this.primaryFor)` — const, line 166
- `const driver = this.driver()` — const, line 168
- `const playing = driver ? this.clocks.get(driver.windowId)?.playing ?? false : false` — const, line 169
- `const passage = this.followed.get(bookWindowId)?.passage` — const, line 184
- `const driver = this.driver()` — const, line 195
- `const known = this.followed.get(bookWindowId)` — const, line 197
- `const answered = known && known.videoExtractionId === driver.extractionId ? known.result : null` — const, line 198
- `const result = answered && !pastCheck(answered) ? answered : null` — const, line 200
- `const chapter = chapterWords(result)` — const, line 201
- `const accepted = chapters.filter((chapter)` — const, line 217
- `const before = this.accepted.get(extractionId) ?? []` — const, line 218

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/desks/DeskShell|src/screens/desks/DeskShell.tsx]] — import-or-re-export: `LIVE_VIDEO_TRANSPORT`, `VideoDesk`, `VideoTransport`; references `LIVE_VIDEO_TRANSPORT`, `VideoDesk`, `VideoTransport`
- [[Reference/Desktop/TypeScript/screens/desks/video/ChaptersPanel|src/screens/desks/video/ChaptersPanel.tsx]] — import-or-re-export: `VideoTransport`; references `VideoTransport`
- [[Reference/Desktop/TypeScript/screens/desks/video/FollowChip|src/screens/desks/video/FollowChip.tsx]] — import-or-re-export: `VideoDesk`; references `VideoDesk`
- [[Reference/Desktop/TypeScript/screens/desks/video/VideoWindow|src/screens/desks/video/VideoWindow.tsx]] — import-or-re-export: `VideoDesk`, `VideoTransport`; references `VideoDesk`, `VideoTransport`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ChaptersJobDto`, `CorrespondentsDto`, `FollowAlongDto`, `VideoChapterDto`
- [[Reference/Desktop/TypeScript/screens/desks/video/model|src/screens/desks/video/model.ts]] — import-or-re-export; imports `FollowChipState`, `FollowedPassage`, `chapterRanges`, `chapterWords`, `choosePassage`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/desks/video/video.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/video/video.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/video/protection.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/video/protection.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/desks/video/deskVideo.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/desks/video/deskVideo.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/desks/video/desk.ts](../../../../../../../../apps/learnloop-tauri/src/screens/desks/video/desk.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
