---
title: "Desktop module · src/screens/feedback/CompareMethods.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.feedback.CompareMethods"
language: "TypeScript"
area: "TypeScript/screens/feedback"
source_path: "apps/learnloop-tauri/src/screens/feedback/CompareMethods.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/feedback/CompareMethods.tsx"
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

# `src/screens/feedback/CompareMethods.tsx`

Area: [[Reference/Desktop/TypeScript/screens/feedback/_area|TypeScript/screens/feedback]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `CompareMethods` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/feedback/CompareMethods.tsx](../../../../../../../apps/learnloop-tauri/src/screens/feedback/CompareMethods.tsx) |
| Source lines | 173 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/feedback/_area|TypeScript/screens/feedback]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/feedback/CompareMethods|src/screens/feedback/CompareMethods.tsx]]

## Public API

- `export const COMPARE_COPY =` — const, line 27
- `export function CompareMethods(` — function, line 43

## Internal implementation anchors

- `const CORRECT = 0.999` — const, line 35
- `const FIRST_POLL_MS = 350` — const, line 36
- `const MAX_POLL_MS = 1500` — const, line 37
- `function sleep(ms: number): Promise<void>` — function, line 39
- `const alive = useRef(true)` — const, line 54
- `const correct = !held && typeof correctness === "number" && correctness >= CORRECT` — const, line 55
- `let cancelled = false` — let, line 70
- `async function open()` — function, line 79
- `const opened = await api.workbenchCompareMethods(` — const, line 84
- `async function follow(jobId: string)` — function, line 96
- `let job = await api.workbenchHelpJob(jobId)` — let, line 99
- `let wait = FIRST_POLL_MS` — let, line 100
- `const result = job.result as unknown as WorkbenchCompareJobResultDto | null` — const, line 108

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export: `CompareMethods`; references `CompareMethods`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `WorkbenchCompareJobResultDto`, `WorkbenchCompareLinesDto`, `WorkbenchComparisonDto`
- [[Reference/Desktop/TypeScript/components/AsPrinted|src/components/AsPrinted.tsx]] — import-or-re-export; imports `AS_PRINTED_COPY`, `BlocksAsPrinted`
- [[Reference/Desktop/TypeScript/components/PlainParts|src/components/PlainParts.tsx]] — import-or-re-export; imports `quietLine`, `quietLink`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `LearnerVoice`, `MeaningLabel`, `ModelVoice`, `SourceVoice`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/feedback/CompareMethods.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/feedback/CompareMethods.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_review_log.py](../../../../../../../tests/test_review_log.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_learner_review_system_entries.py](../../../../../../../tests/test_learner_review_system_entries.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_forecast_ledger.py](../../../../../../../tests/test_forecast_ledger.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/feedback/CompareMethods.tsx](../../../../../../../apps/learnloop-tauri/src/screens/feedback/CompareMethods.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
