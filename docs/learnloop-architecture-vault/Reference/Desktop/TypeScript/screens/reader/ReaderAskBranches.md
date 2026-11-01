---
title: "Desktop module · src/screens/reader/ReaderAskBranches.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.ReaderAskBranches"
language: "TypeScript"
area: "TypeScript/screens/reader"
source_path: "apps/learnloop-tauri/src/screens/reader/ReaderAskBranches.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/ReaderAskBranches.tsx"
source_commit: "015e0270653ead506e571b2c26fd88b8254ac1ce"
source_commit_timestamp: "2026-10-19T03:10:43-04:00"
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

# `src/screens/reader/ReaderAskBranches.tsx`

Area: [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `ReaderAskBranches` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/ReaderAskBranches.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/ReaderAskBranches.tsx) |
| Source lines | 257 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/_area|TypeScript/screens/reader]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `015e0270653ead506e571b2c26fd88b8254ac1ce` |
| Commit timestamp | `2026-10-19T03:10:43-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/ReaderAskBranches|src/screens/reader/ReaderAskBranches.tsx]]

## Public API

- `export interface ReaderExchange` — interface, line 20
- `export type InquiryCommitment = "test_me_later" | "help_me_remember"` — type, line 44
- `export function ReaderAskBranches(` — function, line 69

## Internal implementation anchors

- `interface Props` — interface, line 46
- `const STATUS_WORDS: Record<InquiryResolution, string> =` — const, line 67
- `const byId = new Map(exchanges.map((exchange)` — const, line 84
- `const children = new Map<string | null, ReaderExchange[]>()` — const, line 85
- `const parents = new Map<string, string | null>()` — const, line 86
- `let parent = exchange.parentExchangeId` — let, line 90
- `const seen = new Set([exchange.id])` — const, line 91
- `let cursor = parent` — let, line 92
- `const ancestor = byId.get(cursor)` — const, line 94
- `const search = query.trim().toLowerCase()` — const, line 105
- `const visible = new Set<string>()` — const, line 106
- `let id: string | null = exchange.id` — let, line 109
- `const buttonStyle =` — const, line 116
- `const onHeaderKey = (event: KeyboardEvent<HTMLButtonElement>, exchange: ReaderExchange, isRoot: boolean)` — const, line 118
- `const resolution = exchange.resolution ?? "open"` — const, line 120
- `const scope = event.currentTarget.closest("[data-ask-threads]") ?? document` — const, line 122
- `const headers = Array.from(scope.querySelectorAll<HTMLButtonElement>("[data-exchange-header]"))` — const, line 123
- `const next = headers[headers.indexOf(event.currentTarget) + (event.key === "ArrowDown" ? 1 : -1)]` — const, line 124
- `function statusChips(root: ReaderExchange)` — function, line 145
- `const resolution = root.resolution ?? "open"` — const, line 147
- `const done = committed?.(root) ?? new Set<InquiryCommitment>()` — const, line 148
- `function branch(exchange: ReaderExchange, depth: number)` — function, line 174
- `const expanded = Boolean(search) || !collapsedIds.has(exchange.id)` — const, line 176
- `const replies = children.get(exchange.id) ?? []` — const, line 177
- `const isRoot = depth === 0` — const, line 178
- `const resolution = exchange.resolution ?? "open"` — const, line 179

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `ReaderExchange`; references `ReaderExchange`
- [[Reference/Desktop/TypeScript/screens/reader/AskRail|src/screens/reader/AskRail.tsx]] — import-or-re-export: `InquiryCommitment`, `ReaderAskBranches`, `ReaderExchange`; references `InquiryCommitment`, `ReaderAskBranches`, `ReaderExchange`
- [[Reference/Desktop/TypeScript/screens/reader/TutorAnswer|src/screens/reader/TutorAnswer.tsx]] — import-or-re-export: `ReaderExchange`; references `ReaderExchange`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]] — import-or-re-export: `InquiryCommitment`, `ReaderExchange`; references `InquiryCommitment`, `ReaderExchange`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `InquiryResolution`, `ReaderAnswerMode`, `ReaderTutorViewDto`, `TutorCitationDto`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `Card`, `FONT_MONO`, `Faint`, `Pill`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/reader/TutorAnswer|src/screens/reader/TutorAnswer.tsx]] — import-or-re-export; imports `ExchangeOffers`, `TutorAnswer`, `TutorRailProps`
- [[Reference/Desktop/TypeScript/screens/reader/readerShared|src/screens/reader/readerShared.ts]] — import-or-re-export; imports `answerModeLabel`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `LearnerVoice`, `MeaningLabel`, `SourceVoice`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/tutorReview.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/tutorReview.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/inquiryComponents.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/inquiryComponents.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/TutorAnswer.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/TutorAnswer.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/reader/ReaderAskBranches.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/ReaderAskBranches.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
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

1. Modify [apps/learnloop-tauri/src/screens/reader/ReaderAskBranches.tsx](../../../../../../../apps/learnloop-tauri/src/screens/reader/ReaderAskBranches.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
