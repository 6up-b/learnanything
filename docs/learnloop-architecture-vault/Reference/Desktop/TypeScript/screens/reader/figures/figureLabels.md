---
title: "Desktop module · src/screens/reader/figures/figureLabels.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.figures.figureLabels"
language: "TypeScript"
area: "TypeScript/screens/reader/figures"
source_path: "apps/learnloop-tauri/src/screens/reader/figures/figureLabels.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/figures/figureLabels.tsx"
source_commit: "9e12d91330e6fa42d51fd7c7319294c7015e803f"
source_commit_timestamp: "2026-11-02T20:08:53-05:00"
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

# `src/screens/reader/figures/figureLabels.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/figures/_area|TypeScript/screens/reader/figures]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `figureLabels` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/figures/figureLabels.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/figureLabels.tsx) |
| Source lines | 217 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/figures/_area|TypeScript/screens/reader/figures]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `9e12d91330e6fa42d51fd7c7319294c7015e803f` |
| Commit timestamp | `2026-11-02T20:08:53-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/figureLabels|src/screens/reader/figures/figureLabels.tsx]]

## Public API

- `export interface FigureLabels` — interface, line 22
- `export function useFigureLabels(): FigureLabels | null` — function, line 31
- `export function labelElements(figure: FigureViewDto): FigureElementDto[]` — function, line 36
- `export function Tex(` — function, line 41
- `export function derivedWords(element: FigureElementDto, bounds: DerivedBounds | null):` — function, line 47
- `export function FigureLabelsProvider(` — function, line 80
- `export function LabelText(` — function, line 111
- `export function LabelSuffix(` — function, line 141
- `export function CheckedBadge(` — function, line 164
- `export function CheckedLines(` — function, line 178
- `export function FigureSourceInfo(` — function, line 193

## Internal implementation anchors

- `const LEGEND_CHARS = 48` — const, line 20
- `const FigureLabelsContext = createContext<FigureLabels | null>(null)` — const, line 29
- `const elements = figure.elements ?? []` — const, line 37
- `const html = useMemo(()` — const, line 42
- `const template = element.template` — const, line 48
- `const low = bounds.integers ? String(bounds.integers[0]) : String(bounds.from)` — const, line 54
- `const high = bounds.integers ? String(bounds.integers[1]) : String(bounds.to)` — const, line 55
- `const limited = bounds.clipped ? ` · $` — const, line 56
- `const symbol = variableTex(variable)` — const, line 61
- `const GREEK = new Set(["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota", "kappa", "lambda", "mu", "nu", "xi", "rho", "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega"])` — const, line 68
- `function variableTex(name: string): string` — function, line 71
- `const head = name.replace(/[0-9]+$/, "")` — const, line 74
- `const tail = name.slice(head.length)` — const, line 75
- `const value = useMemo<FigureLabels | null>(()` — const, line 81
- `const list = labelElements(figure)` — const, line 82
- `const elements = new Map(list.map((element)` — const, line 84
- `const bounds = (element: FigureElementDto)` — const, line 85
- `const template = element.template` — const, line 86
- `const element = elements.get(id)` — const, line 98
- `const GLYPH: CSSProperties =` — const, line 107
- `const labels = useFigureLabels()` — const, line 112
- `const element = labels.elements.get(id)` — const, line 114
- `const words = element.template ? derivedWords(element, labels.bounds(element)) :` — const, line 116
- `const compact = element.role === "ai" && legendIndex !== undefined && words.plain.length > LEGEND_CHARS` — const, line 128
- `const glyph = element.voice === "model" ? <span aria-hidden="true" style=` — const, line 129
- `const labels = useFigureLabels()` — const, line 142
- `const element = labels?.elements.get(id)` — const, line 143
- `const words = derivedWords(element, labels.bounds(element))` — const, line 145
- `function distinctBook(figure: FigureViewDto): FigureElementDto[]` — function, line 154
- `const seen = new Set<string>()` — const, line 155
- `const rest = labelElements(figure).some((element)` — const, line 165
- `const book = distinctBook(figure)` — const, line 195
- `const reasons = sourceCheckReasons(figure.sourceCheck?.reasons)` — const, line 196

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/figures/AdvancedPanels|src/screens/reader/figures/AdvancedPanels.tsx]] — import-or-re-export: `LabelText`, `useFigureLabels`; references `LabelText`, `useFigureLabels`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export: `CheckedBadge`, `CheckedLines`, `FigureLabelsProvider`, `FigureSourceInfo`, `LabelText`, `labelElements`, `useFigureLabels`; references `CheckedBadge`, `CheckedLines`, `FigureLabelsProvider`, `FigureSourceInfo`, `LabelText`, `labelElements`, `useFigureLabels`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigurePanels|src/screens/reader/figures/FigurePanels.tsx]] — import-or-re-export: `LabelSuffix`, `LabelText`, `useFigureLabels`; references `LabelSuffix`, `LabelText`, `useFigureLabels`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `FigureElementDto`, `FigureViewDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export; imports `FIGURE_FRAME`, `linkStyle`, `sourceCheckReasons`
- [[Reference/Desktop/TypeScript/screens/reader/figures/figureSpec|src/screens/reader/figures/figureSpec.ts]] — import-or-re-export; imports `CompiledFigure`, `DerivedBounds`, `defaults`, `derivedBounds`
- [[Reference/Desktop/TypeScript/screens/reader/figures/useFigures|src/screens/reader/figures/useFigures.ts]] — import-or-re-export; imports `FiguresCtl`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `MeaningLabel`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `katex`, `katex/dist/katex.min.css`, `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/figures/figureLabels.test.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/figureLabels.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/figures/figureLabels.tsx](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/figureLabels.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
