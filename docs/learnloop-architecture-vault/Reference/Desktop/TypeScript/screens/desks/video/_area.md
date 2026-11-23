---
title: "Desktop area · TypeScript/screens/desks/video"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks/video"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/screens/desks/video

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/desks/video](../../../../../../../../apps/learnloop-tauri/src/screens/desks/video)

## Responsibility

Video windows on the desks: follow-along (a book's chip, its followed passage and the scroll, from reader.follow_along), the suggested chapters under a player (a polled judged job; accept and not this), the accepted chapters' ticks and minimap ranges, and the players' clocks for the timestamp key.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/desks/video/ChaptersPanel|ChaptersPanel.tsx]] | `ACTIVE` | Implements the `ChaptersPanel` routed desktop screen and coordinates its learner-facing workflow state. | 5 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/video/FollowChip|FollowChip.tsx]] | `ACTIVE` | Implements the `FollowChip` routed desktop screen and coordinates its learner-facing workflow state. | 2 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/video/VideoWindow|VideoWindow.tsx]] | `ACTIVE` | Implements the `VideoWindow` routed desktop screen and coordinates its learner-facing workflow state. | 7 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/video/desk|desk.ts]] | `ACTIVE` | Provides `VideoTransport`, `LIVE_VIDEO_TRANSPORT`, `VideoClock`, `DeskVideos` and related exports within the desktop's TypeScript/screens/desks/video ownership area. | 3 | 4 |
| [[Reference/Desktop/TypeScript/screens/desks/video/followLens|followLens.ts]] | `ACTIVE` | Provides `FollowLenses` within the desktop's TypeScript/screens/desks/video ownership area. | 1 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/video/model|model.ts]] | `ACTIVE` | Provides `clockWords`, `FollowedPassage`, `choosePassage`, `chapterWords` and related exports within the desktop's TypeScript/screens/desks/video ownership area. | 1 | 5 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]
