---
title: "Desktop area · TypeScript/screens/desks"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/desks"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/screens/desks

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/desks](../../../../../../../apps/learnloop-tauri/src/screens/desks)

## Responsibility

The Reader workbench's desks: the shell, the window lifecycle contract, the shelf, reading-view geometry and the desk outbox.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

- [[Reference/Desktop/TypeScript/screens/desks/companion/_area|TypeScript/screens/desks/companion]] — The app-wide companion: its docks, summon, dissolve, hand-off and pill (geometry and state machine), its questions as polled companion.ask jobs, the panel with the desk's thread and the history, and previewed diffs.
- [[Reference/Desktop/TypeScript/screens/desks/goal/_area|TypeScript/screens/desks/goal]] — The goal lens on the desks: the goal band under the top bar, criticality marks with their why card, dimming, section callouts, a pad stack's goal line and the path view, all read from goal.band and goal.lens.
- [[Reference/Desktop/TypeScript/screens/desks/keys/_area|TypeScript/screens/desks/keys]] — The desks' key router (the scope and precedence matrix, the bare-Alt hold rule) and the one listener router for every window.
- [[Reference/Desktop/TypeScript/screens/desks/menu/_area|TypeScript/screens/desks/menu]] — The context-aware right-click: one menu and one listener for passages, cues, highlights, margin notes, window headers and pad lines, its promoted rows (passage.promoted and the judged job on the poller, labelled per row), the verbs wired to their server entries, and What this knows.
- [[Reference/Desktop/TypeScript/screens/desks/model/_area|TypeScript/screens/desks/model]] — The client workspace model: desks, windows, slots and pairs, mirroring desk.apply op for op.
- [[Reference/Desktop/TypeScript/screens/desks/overview/_area|TypeScript/screens/desks/overview]] — The desks' overview: the zoom engine (layout, camera, frame function, spring, wheel), its one frame writer, cards, curved links, gather and live miniatures.
- [[Reference/Desktop/TypeScript/screens/desks/pads/_area|TypeScript/screens/desks/pads]] — The scratchpads: pad stack windows (sticky tabs, the running pad, the live editor writing through pad.apply), provenance, gutter marks and hover cards, the pad menu, arrange and split, sketch blocks, submitting a block, passage marks for links and carried questions, and the desk drain.
- [[Reference/Desktop/TypeScript/screens/desks/pen/_area|TypeScript/screens/desks/pen]] — Pen and ink on sources: pen input (pressure, tilt, the barrel eraser, palm rejection), the recognizer (underline, bracket, margin note, lasso, strike), the ink layer inside a source window's scroller, the annotations each mark becomes, ink saved in the one write sequence, the margin note's transcription, and ink pads (lined or dotted paper, ink lines and their readings through the central poller, the learner's corrections).
- [[Reference/Desktop/TypeScript/screens/desks/search/_area|TypeScript/screens/desks/search]] — Search in context: the groups of search.everything with the client's open-on-this-desk group, the meaning job, insert mode and the panel.
- [[Reference/Desktop/TypeScript/screens/desks/windows/_area|TypeScript/screens/desks/windows]] — Desk windows: the Reader's source pane as a scoped source or video window, thread windows, and the panel windows hosting v1 Reader surfaces.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/desks/DeskShell|DeskShell.tsx]] | `ACTIVE` | Implements the `DeskShell` routed desktop screen and coordinates its learner-facing workflow state. | 43 | 2 |
| [[Reference/Desktop/TypeScript/screens/desks/Shelf|Shelf.tsx]] | `ACTIVE` | Implements the `Shelf` routed desktop screen and coordinates its learner-facing workflow state. | 1 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/fitMath|fitMath.tsx]] | `ACTIVE` | Implements the `fitMath` routed desktop screen and coordinates its learner-facing workflow state. | 0 | 4 |
| [[Reference/Desktop/TypeScript/screens/desks/geometry|geometry.ts]] | `ACTIVE` | Provides `DESK_SIZES`, `Rect`, `Stage`, `slotWidth` and related exports within the desktop's TypeScript/screens/desks ownership area. | 0 | 8 |
| [[Reference/Desktop/TypeScript/screens/desks/lifecycle|lifecycle.tsx]] | `ACTIVE` | Implements the `lifecycle` routed desktop screen and coordinates its learner-facing workflow state. | 0 | 41 |
| [[Reference/Desktop/TypeScript/screens/desks/outbox|outbox.ts]] | `ACTIVE` | Provides `InkSaveBody`, `InkEraseBody`, `Batch`, `BatchBody` and related exports within the desktop's TypeScript/screens/desks ownership area. | 1 | 3 |
| [[Reference/Desktop/TypeScript/screens/desks/selection|selection.ts]] | `ACTIVE` | Provides `WindowSelection`, `quoteOf`, `clipQuote`, `readWindowSelection` within the desktop's TypeScript/screens/desks ownership area. | 3 | 1 |
| [[Reference/Desktop/TypeScript/screens/desks/store|store.ts]] | `ACTIVE` | Provides `DeskStoreTransport`, `DeskNotice`, `FLUSH_IDLE_MS`, `DeskStore` and related exports within the desktop's TypeScript/screens/desks ownership area. | 5 | 3 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]
