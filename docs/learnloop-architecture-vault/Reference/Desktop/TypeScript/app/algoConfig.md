---
title: "Desktop module · src/app/algoConfig.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.app.algoConfig"
language: "TypeScript"
area: "TypeScript/app"
source_path: "apps/learnloop-tauri/src/app/algoConfig.ts"
source_paths:
  - "apps/learnloop-tauri/src/app/algoConfig.ts"
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

# `src/app/algoConfig.ts`

Area: [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Normalizes and exposes algorithm configuration values needed by presentation code.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/algoConfig.ts](../../../../../../apps/learnloop-tauri/src/app/algoConfig.ts) |
| Source lines | 268 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]]

## Public API

- `export interface AlgoDisplayConfig` — interface, line 7
- `export interface AskPanelConfig` — interface, line 75
- `export interface WorkbenchHelpConfig` — interface, line 87
- `export type HelpStyleValue = "let_me_struggle" | "balanced" | "guide_me"` — type, line 98
- `export interface AdaptiveHintsConfig` — interface, line 100
- `export function setAlgoConfig(config: unknown): void` — function, line 133
- `export function subscribeAlgoConfig(listener: ()` — function, line 195
- `export function setAdaptiveHelpStyle(style: HelpStyleValue): void` — function, line 207
- `export function storedHelpStyle(): HelpStyleValue` — function, line 216
- `export const STUCK_PROMPT_TEXT = "Write what you can, or what's confusing you"` — const, line 222
- `export function algoConfig(): AlgoDisplayConfig` — function, line 224
- `export type MasteryBand = "strong" | "developing" | "weak"` — type, line 228
- `export function masteryBand(mastery: number): MasteryBand` — function, line 230
- `export function masteryTone<T>(mastery: number, palette:` — function, line 237
- `export function useSymbolicChecksLive(): boolean` — function, line 249
- `export function setRenderedShell(shell: "simple" | "classic" | null): void` — function, line 261
- `export function activeShell(): "simple" | "classic"` — function, line 266

## Internal implementation anchors

- `const DEFAULTS: AlgoDisplayConfig =` — const, line 107
- `let current: AlgoDisplayConfig =` — let, line 129
- `let renderedShell: "simple" | "classic" | null = null` — let, line 131
- `const root = (config ??` — const, line 134
- `const listeners = new Set<()` — const, line 191
- `function asHelpStyle(value: unknown): HelpStyleValue` — function, line 202
- `const band = masteryBand(mastery)` — const, line 238
- `function asNumber(value: unknown, fallback: number): number` — function, line 242

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `algoConfig`, `setAlgoConfig`, `setRenderedShell`; references `algoConfig`, `setAlgoConfig`, `setRenderedShell`
- [[Reference/Desktop/TypeScript/app/dailyPlan|src/app/dailyPlan.ts]] — import-or-re-export: `algoConfig`; references `algoConfig`
- [[Reference/Desktop/TypeScript/app/keyScope|src/app/keyScope.ts]] — import-or-re-export: `activeShell`; references `activeShell`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export: `activeShell`; references `activeShell`
- [[Reference/Desktop/TypeScript/app/practiceFeedback|src/app/practiceFeedback.ts]] — import-or-re-export: `algoConfig`; references `algoConfig`
- [[Reference/Desktop/TypeScript/app/shell|src/app/shell.ts]] — import-or-re-export: `algoConfig`; references `algoConfig`
- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export: `algoConfig`; references `algoConfig`
- [[Reference/Desktop/TypeScript/components/DialogueProbe|src/components/DialogueProbe.tsx]] — import-or-re-export: `STUCK_PROMPT_TEXT`, `algoConfig`; references `STUCK_PROMPT_TEXT`, `algoConfig`
- [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]] — import-or-re-export: `masteryTone`; references `masteryTone`
- [[Reference/Desktop/TypeScript/components/askFigures|src/components/askFigures.tsx]] — import-or-re-export: `algoConfig`; references `algoConfig`
- [[Reference/Desktop/TypeScript/components/askPanel|src/components/askPanel.tsx]] — import-or-re-export: `algoConfig`, `setAdaptiveHelpStyle`, `storedHelpStyle`, `subscribeAlgoConfig`; references `algoConfig`, `setAdaptiveHelpStyle`, `storedHelpStyle`, `subscribeAlgoConfig`
- [[Reference/Desktop/TypeScript/screens/ExamScreen|src/screens/ExamScreen.tsx]] — import-or-re-export: `masteryTone`; references `masteryTone`
- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export: `algoConfig`, `masteryTone`; references `algoConfig`, `masteryTone`
- [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] — import-or-re-export: `masteryTone`; references `masteryTone`
- [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] — import-or-re-export: `masteryTone`; references `masteryTone`
- [[Reference/Desktop/TypeScript/screens/KnowledgeStrataView|src/screens/KnowledgeStrataView.tsx]] — import-or-re-export: `masteryTone`; references `masteryTone`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `STUCK_PROMPT_TEXT`, `algoConfig`, `masteryTone`, `setAdaptiveHelpStyle`; references `STUCK_PROMPT_TEXT`, `algoConfig`, `masteryTone`, `setAdaptiveHelpStyle`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `algoConfig`; references `algoConfig`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export: `algoConfig`, `masteryTone`; references `algoConfig`, `masteryTone`
- [[Reference/Desktop/TypeScript/screens/practice/HelpStyleSettings|src/screens/practice/HelpStyleSettings.tsx]] — import-or-re-export: `algoConfig`, `setAdaptiveHelpStyle`; references `algoConfig`, `setAdaptiveHelpStyle`
- [[Reference/Desktop/TypeScript/screens/practice/HintPanel|src/screens/practice/HintPanel.tsx]] — import-or-re-export: `algoConfig`; references `algoConfig`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderWorkingPosture|src/screens/reader/ReaderWorkingPosture.tsx]] — import-or-re-export: `algoConfig`; references `algoConfig`
- [[Reference/Desktop/TypeScript/screens/reader/WrapUpOffer|src/screens/reader/WrapUpOffer.tsx]] — import-or-re-export: `algoConfig`; references `algoConfig`
- [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]] — import-or-re-export: `algoConfig`; references `algoConfig`
- [[Reference/Desktop/TypeScript/screens/workbench/CheckColumn|src/screens/workbench/CheckColumn.tsx]] — import-or-re-export: `useSymbolicChecksLive`; references `useSymbolicChecksLive`
- [[Reference/Desktop/TypeScript/screens/workbench/StepHints|src/screens/workbench/StepHints.tsx]] — import-or-re-export: `useSymbolicChecksLive`; references `useSymbolicChecksLive`
- [[Reference/Desktop/TypeScript/screens/workbench/Workbench|src/screens/workbench/Workbench.tsx]] — import-or-re-export: `algoConfig`; references `algoConfig`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Configure AI Providers|Configure AI Providers]] — owns provider setup.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/workbench/symbolicOff.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/workbench/symbolicOff.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/workbench/switchOff.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/workbench/switchOff.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/workbench/rw2cFixRound2.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/workbench/rw2cFixRound2.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/workbench/reviewFixes.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/workbench/reviewFixes.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/workbench/ownerCapture1025.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/workbench/ownerCapture1025.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/workbench/RouteExample.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/workbench/RouteExample.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/workbench/HelpLadder.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/workbench/HelpLadder.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/today/TodayPlace.test.tsx](../../../../../../apps/learnloop-tauri/src/screens/today/TodayPlace.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/algoConfig.ts](../../../../../../apps/learnloop-tauri/src/app/algoConfig.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
