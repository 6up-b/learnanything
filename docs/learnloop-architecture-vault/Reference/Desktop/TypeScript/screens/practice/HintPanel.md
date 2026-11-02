---
title: "Desktop module · src/screens/practice/HintPanel.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.practice.HintPanel"
language: "TypeScript"
area: "TypeScript/screens/practice"
source_path: "apps/learnloop-tauri/src/screens/practice/HintPanel.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/practice/HintPanel.tsx"
source_commit: "afb17672c627b4f4422c149ac63dd2addef98a9b"
source_commit_timestamp: "2026-11-01T20:23:43-05:00"
source_worktree_state: "clean"
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

# `src/screens/practice/HintPanel.tsx`

Area: [[Reference/Desktop/TypeScript/screens/practice/_area|TypeScript/screens/practice]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `HintPanel` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/practice/HintPanel.tsx](../../../../../../../apps/learnloop-tauri/src/screens/practice/HintPanel.tsx) |
| Source lines | 349 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/practice/_area|TypeScript/screens/practice]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `afb17672c627b4f4422c149ac63dd2addef98a9b` |
| Commit timestamp | `2026-11-01T20:23:43-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/practice/HintPanel|src/screens/practice/HintPanel.tsx]]

## Public API

- `export function hintLabelLine(entry: HintEntry): string` — function, line 33
- `export function HintPanel(` — function, line 256

## Internal implementation anchors

- `const chip = (on: boolean)` — const, line 21
- `const labels = entry.result.labels ??` — const, line 34
- `const parts: string[] = []` — const, line 35
- `function draftLines(answer: string): string[]` — function, line 44
- `function FeedbackBox(` — function, line 48
- `const lines = draftLines(answer)` — const, line 60
- `const send = ()` — const, line 61
- `const selection = shortcut === "not_where_stuck" ? picked.sort((a, b)` — const, line 62
- `const onKey = (event: KeyboardEvent<HTMLInputElement>)` — const, line 66
- `function DiscriminatingBox(` — function, line 122
- `function ExploreFigure(` — function, line 165
- `const figures = usePanelFigures(target,` — const, line 168
- `const offer = entry.result.figure` — const, line 169
- `const opened = figures.lines.find((line)` — const, line 171
- `function HintCard(` — function, line 187
- `const replies = entry.result.replies ?? []` — const, line 192
- `const asking = entry.result.kind === "discriminating" && Boolean(entry.result.discriminating?.answerBox)` — const, line 193

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `HintPanel`; references `HintPanel`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `HelpStyle`, `HintShortcut`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`
- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export; imports `AskTarget`
- [[Reference/Desktop/TypeScript/components/PlainParts|src/components/PlainParts.tsx]] — import-or-re-export; imports `quietLine`, `quietLink`
- [[Reference/Desktop/TypeScript/components/askFigures|src/components/askFigures.tsx]] — import-or-re-export; imports `PANEL_FIGURE_COPY`, `PanelFigureEvent`, `PanelFigureThreadLine`, `usePanelFigures`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/practice/hintCopy|src/screens/practice/hintCopy.ts]] — import-or-re-export; imports `HELP_STYLE_COPY`, `HINT_COPY`, `SHORTCUT_COPY`
- [[Reference/Desktop/TypeScript/screens/practice/useAdaptiveHints|src/screens/practice/useAdaptiveHints.ts]] — import-or-re-export; imports `AdaptiveHints`, `HintEntry`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_large_practice_flow.py](../../../../../../../tests/test_large_practice_flow.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_contract.py](../../../../../../../tests/test_sidecar_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_practice_information.py](../../../../../../../tests/test_practice_information.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_diagnostic.py](../../../../../../../tests/test_sidecar_diagnostic.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/practice/HintPanel.tsx](../../../../../../../apps/learnloop-tauri/src/screens/practice/HintPanel.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
