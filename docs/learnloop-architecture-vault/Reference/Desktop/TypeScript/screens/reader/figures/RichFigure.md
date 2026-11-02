---
title: "Desktop module · src/screens/reader/figures/RichFigure.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.figures.RichFigure"
language: "TypeScript"
area: "TypeScript/screens/reader/figures"
source_path: "apps/learnloop-tauri/src/screens/reader/figures/RichFigure.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/figures/RichFigure.tsx"
source_commit: "037248502b5de983d75467e41786b59dd1b6d4b3"
source_commit_timestamp: "2026-11-01T09:50:06-05:00"
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

# `src/screens/reader/figures/RichFigure.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/figures/_area|TypeScript/screens/reader/figures]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `RichFigure` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/figures/RichFigure.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/RichFigure.tsx) |
| Source lines | 235 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/figures/_area|TypeScript/screens/reader/figures]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `037248502b5de983d75467e41786b59dd1b6d4b3` |
| Commit timestamp | `2026-11-01T09:50:06-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] → [[Reference/Desktop/TypeScript/components/askFigures|src/components/askFigures.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/RichFigure|src/screens/reader/figures/RichFigure.tsx]]

## Public API

- `export const RICH_FRAME =` — const, line 25
- `export const RICH_PHASES: Readonly<Record<string, string>> = Object.freeze(` — const, line 61
- `export function manimBadge(figure: FigureViewDto): string` — function, line 67
- `export function manimCheckLine(check: FigureManimCheckDto): string` — function, line 75
- `export function ManimNotRight(` — function, line 89
- `export function ManimFigureBody(` — function, line 118
- `export function FullerLine(` — function, line 152
- `export function RichPendingLine(` — function, line 201
- `export function ManimOptInLine(` — function, line 227

## Internal implementation anchors

- `const settings = `at $` — const, line 76
- `const property = check.property === "nonnegative" ? "is never negative" : check.property === "bounded" ? `stays within ±$` — const, line 82
- `const manim = figure.manim` — const, line 120
- `const style =` — const, line 160
- `const text = line.state === "waiting_for_plan" ? RICH_FRAME.richWaiting : (RICH_PHASES[line.phase ?? "writing"] ?? RICH_PHASES.writing)` — const, line 217

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/components/askFigures|src/components/askFigures.tsx]] — import-or-re-export: `RichPendingLine`; references `RichPendingLine`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export: `FullerLine`, `ManimFigureBody`, `ManimNotRight`, `ManimOptInLine`, `RICH_FRAME`, `RichPendingLine`, `manimBadge`; references `FullerLine`, `ManimFigureBody`, `ManimNotRight`, `ManimOptInLine`, `RICH_FRAME`, `RichPendingLine`, `manimBadge`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `FigureFullerDto`, `FigureManimCheckDto`, `FigureRichPendingDto`, `FigureViewDto`
- [[Reference/Desktop/TypeScript/components/AnimationPlayer|src/components/AnimationPlayer.tsx]] — import-or-re-export; imports `AnimationPlayer`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export; imports `FIGURE_FRAME`, `linkStyle`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `MeaningLabel`, `ModelVoice`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/figures/richFigure.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/richFigure.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_figure_label_wording.py](../../../../../../../../tests/test_figure_label_wording.py) — cross-boundary name contract: references uniquely owned exported name `RICH_FRAME`; it does **not** directly execute this source module.
- [tests/test_sidecar_reader.py](../../../../../../../../tests/test_sidecar_reader.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../../../tests/test_sidecar_reader_pdf_view.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_render_views.py](../../../../../../../../tests/test_reader_render_views.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_requests.py](../../../../../../../../tests/test_reader_requests.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/reader/figures/RichFigure.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/RichFigure.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
