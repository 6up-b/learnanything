---
title: "Desktop module · src/components/askPanel.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.components.askPanel"
language: "TypeScript"
area: "TypeScript/components"
source_path: "apps/learnloop-tauri/src/components/askPanel.tsx"
source_paths:
  - "apps/learnloop-tauri/src/components/askPanel.tsx"
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

# `src/components/askPanel.tsx`

Area: [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides the reusable `askPanel` interaction surface used by one or more desktop workflows.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/components/askPanel.tsx](../../../../../../apps/learnloop-tauri/src/components/askPanel.tsx) |
| Source lines | 131 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/components/_area|TypeScript/components]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] → [[Reference/Desktop/TypeScript/components/askPanel|src/components/askPanel.tsx]]

## Public API

- `export const STYLE_ANSWER_MODE: Record<HelpStyle, AnswerMode> =` — const, line 14
- `export const ANSWER_MODE_LABEL: Record<AnswerMode, string> =` — const, line 21
- `export const ONE_QUESTION_MODES: ReadonlyArray<` — const, line 28
- `export const ASK_COPY =` — const, line 40
- `export function answerCountLabel(` — function, line 71
- `export function useStoredHelpStyle(): HelpStyle` — function, line 80
- `export function StoredHelpStyle(` — function, line 87
- `export function shortDate(iso: string): string` — function, line 127

## Internal implementation anchors

- `const STYLE_LABELS: ReadonlyArray<` — const, line 34
- `const style = useStoredHelpStyle()` — const, line 88
- `const choose = async (next: HelpStyle)` — const, line 91
- `const saved = await api.setHelpStyle(next)` — const, line 95
- `const checked = style === option.value` — const, line 109
- `const date = new Date(iso)` — const, line 128

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export: `ANSWER_MODE_LABEL`, `ASK_COPY`, `ONE_QUESTION_MODES`, `STYLE_ANSWER_MODE`, `StoredHelpStyle`, `answerCountLabel`, `shortDate`, `useStoredHelpStyle`; references `ANSWER_MODE_LABEL`, `ASK_COPY`, `ONE_QUESTION_MODES`, `STYLE_ANSWER_MODE`, `StoredHelpStyle`, `answerCountLabel`, `shortDate`, `useStoredHelpStyle`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `ASK_COPY`; references `ASK_COPY`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `STYLE_ANSWER_MODE`, `StoredHelpStyle`, `useStoredHelpStyle`; references `STYLE_ANSWER_MODE`, `StoredHelpStyle`, `useStoredHelpStyle`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AnswerMode`, `HelpStyle`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`, `setAdaptiveHelpStyle`, `storedHelpStyle`, `subscribeAlgoConfig`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/components/AskOverlay.panel.test.tsx](../../../../../../apps/learnloop-tauri/src/components/AskOverlay.panel.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/components/askPanel.tsx](../../../../../../apps/learnloop-tauri/src/components/askPanel.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
