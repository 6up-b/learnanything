---
title: "Desktop module · src/screens/reader/MarginMark.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.MarginMark"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/MarginMark.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/MarginMark.tsx"
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

# `src/screens/reader/MarginMark.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `MarginMark` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/MarginMark.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/MarginMark.tsx) |
| Source lines | 484 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/MarginMark|src/screens/reader/MarginMark.tsx]]

## Public API

- `export type CueCheckPhase = "idle" | "finding" | "none" | "failed"` — type, line 23
- `export interface MarginMarkProps` — interface, line 25
- `export function MarginMark(` — function, line 74
- `export interface CueReceipt` — interface, line 400
- `export function CueFooter(` — function, line 412

## Internal implementation anchors

- `const SEEN_THRESHOLD = 0.5` — const, line 55
- `function yourWords(kind: string | null | undefined): string` — function, line 58
- `const labels: Record<string, string> = DISCOVERED_COPY.yourWords` — const, line 59
- `const ACTION_STYLE =` — const, line 63
- `const markRef = useRef<HTMLButtonElement | null>(null)` — const, line 91
- `const firstActionRef = useRef<HTMLButtonElement | null>(null)` — const, line 92
- `const onSeenRef = useRef(onSeen)` — const, line 97
- `const planRef = useRef(planId)` — const, line 99
- `const seen = ()` — const, line 101
- `const node = markRef.current` — const, line 107
- `const observer = new IntersectionObserver( (entries)` — const, line 112
- `const planForGeneration = planId` — const, line 128
- `const notify = onSeen` — const, line 129
- `const generation = observerGeneration()` — const, line 130
- `const close = ()` — const, line 150
- `const earlier = cue.earlier` — const, line 154
- `const discovered = cue.foundBy === "model"` — const, line 156
- `const tryFirst = discovered && cue.kind === "try_first" && onTryFirst ? onTryFirst : null` — const, line 157
- `const onPage = surface === "pdf"` — const, line 158
- `const slot = surface === "text" ?` — const, line 161

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `CueFooter`, `MarginMark`; references `CueFooter`, `MarginMark`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderCues|src/screens/reader/useReaderCues.ts]] — import-or-re-export: `CueCheckPhase`, `CueReceipt`; references `CueCheckPhase`, `CueReceipt`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CueDensity`, `ReaderCueDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/screens/reader/cues|src/screens/reader/cues.ts]] — import-or-re-export; imports `CUE_COPY`, `CUE_DENSITIES`, `DISCOVERED_COPY`, `markClass`
- [[Reference/Desktop/TypeScript/screens/reader/observerGeneration|src/screens/reader/observerGeneration.ts]] — import-or-re-export; imports `observerGeneration`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `LearnerVoice`, `MeaningLabel`, `ModelVoice`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/rw3bReview.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/rw3bReview.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_sidecar_reader.py](../../../../../../../tests/test_sidecar_reader.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../../tests/test_sidecar_reader_pdf_view.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_render_views.py](../../../../../../../tests/test_reader_render_views.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_requests.py](../../../../../../../tests/test_reader_requests.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/reader/MarginMark.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/MarginMark.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
