---
title: "Desktop module · src/screens/feedback/answerExposureGate.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.feedback.answerExposureGate"
language: "TypeScript"
area: "TypeScript/screens/feedback"
source_path: "apps/learnloop-tauri/src/screens/feedback/answerExposureGate.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/feedback/answerExposureGate.ts"
source_commit: "30213eb58031832c7ea2ce41e29ae27866751e9c"
source_commit_timestamp: "2026-11-06T16:40:48-05:00"
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

# `src/screens/feedback/answerExposureGate.ts`

Area: [[Reference/Desktop/TypeScript/screens/feedback/_area|TypeScript/screens/feedback]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `EXPOSURE`, `DisplayReceipt`, `RecordDisplay`, `ExposureStatus` and related exports within the desktop's TypeScript/screens/feedback ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/feedback/answerExposureGate.ts](../../../../../../../apps/learnloop-tauri/src/screens/feedback/answerExposureGate.ts) |
| Source lines | 171 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/feedback/_area|TypeScript/screens/feedback]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `30213eb58031832c7ea2ce41e29ae27866751e9c` |
| Commit timestamp | `2026-11-06T16:40:48-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/feedback/answerExposure|src/screens/feedback/answerExposure.ts]] → [[Reference/Desktop/TypeScript/screens/feedback/answerExposureGate|src/screens/feedback/answerExposureGate.ts]]

## Public API

- `export const EXPOSURE = contract as` — const, line 7
- `export interface DisplayReceipt` — interface, line 16
- `export type RecordDisplay = (displayId: string)` — type, line 21
- `export type ExposureStatus = "shown" | "waiting" | "away" | "unavailable"` — type, line 23
- `export class AnswerExposureGate` — class, line 57

## Internal implementation anchors

- `interface Row` — interface, line 25
- `interface Pending` — interface, line 38
- `function newDisplayId(): string` — function, line 47
- `const random = globalThis.crypto?.randomUUID?.()` — const, line 48
- `function refused(error: unknown): boolean` — function, line 52
- `const latest = this.latest` — const, line 77
- `const at = this.now()` — const, line 105
- `const covered = this.covered(at)` — const, line 115
- `const due = !covered || at - (this.latest?.sentMs ?? Number.NEGATIVE_INFINITY) >= EXPOSURE.renewAfterMs` — const, line 116
- `const pending = this.pending ??` — const, line 130
- `let call: Promise<unknown>` — let, line 136
- `const stampMs = this.stampOf(receipt, pending.firstSentMs)` — const, line 144
- `const at = receipt && typeof receipt === "object" ? (receipt as DisplayReceipt).recordedAt : null` — const, line 167
- `const parsed = typeof at === "string" ? Date.parse(at) : Number.NaN` — const, line 168

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/feedback/answerExposure|src/screens/feedback/answerExposure.ts]] — import-or-re-export: `AnswerExposureGate`, `EXPOSURE`, `ExposureStatus`, `RecordDisplay`; references `AnswerExposureGate`, `EXPOSURE`, `ExposureStatus`, `RecordDisplay`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

- Local asset: [apps/learnloop-tauri/src/screens/feedback/exposureContract.json](../../../../../../../apps/learnloop-tauri/src/screens/feedback/exposureContract.json)

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_review_log.py](../../../../../../../tests/test_review_log.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_learner_review_system_entries.py](../../../../../../../tests/test_learner_review_system_entries.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_forecast_ledger.py](../../../../../../../tests/test_forecast_ledger.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/feedback/answerExposureGate.ts](../../../../../../../apps/learnloop-tauri/src/screens/feedback/answerExposureGate.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
