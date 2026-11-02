---
title: "Desktop area · TypeScript/screens/practice"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/practice"
source_commit: "4066ab56bccaee0859f87dc6db5d2de2853a8252"
source_commit_timestamp: "2026-10-25T20:20:20-04:00"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/screens/practice

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/practice](../../../../../../../apps/learnloop-tauri/src/screens/practice)

## Responsibility

Practice-screen help: hints, the hint panel, help-style settings, difficulty taps, and why an item was chosen.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/practice/DifficultyRatingTap|DifficultyRatingTap.tsx]] | `ACTIVE` | Implements the `DifficultyRatingTap` routed desktop screen and coordinates its learner-facing workflow state. | 2 | 1 |
| [[Reference/Desktop/TypeScript/screens/practice/HelpStyleSettings|HelpStyleSettings.tsx]] | `ACTIVE` | Implements the `HelpStyleSettings` routed desktop screen and coordinates its learner-facing workflow state. | 7 | 1 |
| [[Reference/Desktop/TypeScript/screens/practice/HintPanel|HintPanel.tsx]] | `ACTIVE` | Implements the `HintPanel` routed desktop screen and coordinates its learner-facing workflow state. | 9 | 1 |
| [[Reference/Desktop/TypeScript/screens/practice/WhyThisItem|WhyThisItem.tsx]] | `ACTIVE` | Implements the `WhyThisItem` routed desktop screen and coordinates its learner-facing workflow state. | 2 | 1 |
| [[Reference/Desktop/TypeScript/screens/practice/hintCopy|hintCopy.ts]] | `ACTIVE` | Provides `HINT_COPY`, `SHORTCUT_COPY`, `HELP_STYLE_COPY`, `FORBIDDEN_WORDING` within the desktop's TypeScript/screens/practice ownership area. | 1 | 3 |
| [[Reference/Desktop/TypeScript/screens/practice/useAdaptiveHints|useAdaptiveHints.ts]] | `ACTIVE` | Provides `HintEntry`, `HintNotice`, `AdaptiveHintsOptions`, `useAdaptiveHints` and related exports within the desktop's TypeScript/screens/practice ownership area. | 4 | 2 |
| [[Reference/Desktop/TypeScript/screens/practice/useFirstHintProgress|useFirstHintProgress.ts]] | `ACTIVE` | Provides `FirstHintProgressMarker`, `useFirstHintProgress` within the desktop's TypeScript/screens/practice ownership area. | 1 | 1 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]
