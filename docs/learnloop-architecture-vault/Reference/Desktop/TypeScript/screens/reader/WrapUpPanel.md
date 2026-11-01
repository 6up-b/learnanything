---
title: "Desktop module · src/screens/reader/WrapUpPanel.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.WrapUpPanel"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/WrapUpPanel.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/WrapUpPanel.tsx"
source_commit: "aca248456eeb018af0f9703f284541298697d35f"
source_commit_timestamp: "2026-11-01T01:19:43-05:00"
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

# `src/screens/reader/WrapUpPanel.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `WrapUpPanel` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/WrapUpPanel.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/WrapUpPanel.tsx) |
| Source lines | 125 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `aca248456eeb018af0f9703f284541298697d35f` |
| Commit timestamp | `2026-11-01T01:19:43-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/WrapUpPanel|src/screens/reader/WrapUpPanel.tsx]]

## Public API

- `export interface WrapUpPanelProps` — interface, line 17
- `export function WrapUpPanel(` — function, line 47

## Internal implementation anchors

- `const ACTION_LABELS: Record<ReaderWrapUpActionDto["action"], string> =` — const, line 30
- `const headingStyle: CSSProperties =` — const, line 37
- `const listStyle: CSSProperties =` — const, line 38
- `const lineStyle: CSSProperties =` — const, line 39
- `function reinforceLine(line: ReaderWrapUpReinforceLineDto): string` — function, line 41
- `const onKey = (event: KeyboardEvent)` — const, line 50
- `const actionsFor = (line: ReaderWrapUpInquiryLineDto)` — const, line 58
- `const withHelp = wrapUp.worthReinforcing.filter((line)` — const, line 61
- `const reinforce = wrapUp.worthReinforcing.filter((line)` — const, line 62
- `const empty = wrapUp.resolved.length === 0 && wrapUp.stillOpen.length === 0 && reinforce.length === 0` — const, line 63
- `const renderInquiry = (line: ReaderWrapUpInquiryLineDto, glyph: string)` — const, line 65

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `WrapUpPanel`; references `WrapUpPanel`
- [[Reference/Desktop/TypeScript/screens/reader/WrapUpOffer|src/screens/reader/WrapUpOffer.tsx]] — import-or-re-export: `WrapUpPanel`; references `WrapUpPanel`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `ReaderWrapUpActionDto`, `ReaderWrapUpDto`, `ReaderWrapUpInquiryLineDto`, `ReaderWrapUpReinforceLineDto`
- [[Reference/Desktop/TypeScript/app/keymap|src/app/keymap.ts]] — import-or-re-export; imports `screenLeavesKey`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/screens/reader/ComingUp|src/screens/reader/ComingUp.tsx]] — import-or-re-export; imports `ComingUp`, `ComingUpProps`
- [[Reference/Desktop/TypeScript/screens/reader/DigestNarrative|src/screens/reader/DigestNarrative.tsx]] — import-or-re-export; imports `DigestNarrative`
- [[Reference/Desktop/TypeScript/screens/reader/RecapCard|src/screens/reader/RecapCard.tsx]] — import-or-re-export; imports `Quoted`, `RecapLink`
- [[Reference/Desktop/TypeScript/screens/reader/recapCopy|src/screens/reader/recapCopy.ts]] — import-or-re-export; imports `RECAP_COPY`, `observationLine`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `MeaningLabel`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/WrapUp.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/WrapUp.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/DigestNarrative.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/DigestNarrative.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/WrapUpPanel.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/WrapUpPanel.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
