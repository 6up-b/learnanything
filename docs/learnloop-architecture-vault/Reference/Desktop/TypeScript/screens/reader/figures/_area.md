---
title: "Desktop area · TypeScript/screens/reader/figures"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/figures"
source_commit: "20c6c3ad3806f7951982f4768478fe77272f4c3a"
source_commit_timestamp: "2026-11-01T23:26:02-05:00"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/screens/reader/figures

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/reader/figures](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures)

## Responsibility

Reader "show me" figures: the figure grammar and spec, inline figures, panels, predictions, and their state.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

- [[Reference/Desktop/TypeScript/screens/reader/figures/sketch/_area|TypeScript/screens/reader/figures/sketch]] — The sandboxed sketch tier: the pinned engine host, its Worker protocol and runner, and the scene renderer.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/reader/figures/AdvancedPanels|AdvancedPanels.tsx]] | `ACTIVE` | Implements the `AdvancedPanels` routed desktop screen and coordinates its learner-facing workflow state. | 3 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|FigureInline.tsx]] | `ACTIVE` | Implements the `FigureInline` routed desktop screen and coordinates its learner-facing workflow state. | 12 | 5 |
| [[Reference/Desktop/TypeScript/screens/reader/figures/FigurePanels|FigurePanels.tsx]] | `ACTIVE` | Implements the `FigurePanels` routed desktop screen and coordinates its learner-facing workflow state. | 3 | 3 |
| [[Reference/Desktop/TypeScript/screens/reader/figures/RichFigure|RichFigure.tsx]] | `ACTIVE` | Implements the `RichFigure` routed desktop screen and coordinates its learner-facing workflow state. | 5 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/figures/figureGrammar|figureGrammar.ts]] | `ACTIVE` | Provides `MAX_EXPR_CHARS`, `MAX_NODES`, `MAX_DEPTH`, `MAX_EXPANDED_NODES` and related exports within the desktop's TypeScript/screens/reader/figures ownership area. | 0 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/figures/figureSpec|figureSpec.ts]] | `ACTIVE` | Provides `SPEC_VERSION`, `SAMPLES`, `DIRECTIONS`, `SAME_TOLERANCE` and related exports within the desktop's TypeScript/screens/reader/figures ownership area. | 1 | 3 |
| [[Reference/Desktop/TypeScript/screens/reader/figures/showMe|showMe.ts]] | `ACTIVE` | Provides `SHOW_ME_COPY`, `ShowMeLine`, `passageChip`, `showMeSourceLine` and related exports within the desktop's TypeScript/screens/reader/figures ownership area. | 1 | 2 |
| [[Reference/Desktop/TypeScript/screens/reader/figures/useFigures|useFigures.ts]] | `ACTIVE` | Provides `FIGURE_POLL_MS`, `RICH_POLL_MS`, `FigureRequestInput`, `FigureRequestOutcome` and related exports within the desktop's TypeScript/screens/reader/figures ownership area. | 5 | 4 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]
