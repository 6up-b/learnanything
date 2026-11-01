---
title: "Desktop module · src/screens/feedback/answerExposure.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.feedback.answerExposure"
language: "TypeScript"
area: "TypeScript/screens/feedback"
source_path: "apps/learnloop-tauri/src/screens/feedback/answerExposure.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/feedback/answerExposure.ts"
source_commit: "03edeb4044c1bd439743f200a3b5804f657ff5a3"
source_commit_timestamp: "2026-10-16T04:55:59-04:00"
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

# `src/screens/feedback/answerExposure.ts`

Area: [[Reference/Desktop/TypeScript/screens/feedback/_area|TypeScript/screens/feedback]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `EXPOSURE`, `DisplayReceipt`, `RecordDisplay`, `ExposureStatus` and related exports within the desktop's TypeScript/screens/feedback ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/feedback/answerExposure.ts](../../../../../../../apps/learnloop-tauri/src/screens/feedback/answerExposure.ts) |
| Source lines | 397 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/feedback/_area|TypeScript/screens/feedback]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `03edeb4044c1bd439743f200a3b5804f657ff5a3` |
| Commit timestamp | `2026-10-16T04:55:59-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/feedback/answerExposure|src/screens/feedback/answerExposure.ts]]

## Public API

- `export const EXPOSURE = contract as` — const, line 48
- `export interface DisplayReceipt` — interface, line 57
- `export type RecordDisplay = (displayId: string)` — type, line 62
- `export type ExposureStatus = "shown" | "waiting" | "away" | "unavailable"` — type, line 64
- `export class AnswerExposureGate` — class, line 98
- `export function useAnswerExposure( key: string, onScreen: boolean, record: RecordDisplay | undefined ):` — function, line 228

## Internal implementation anchors

- `interface Row` — interface, line 66
- `interface Pending` — interface, line 79
- `function newDisplayId(): string` — function, line 88
- `const random = globalThis.crypto?.randomUUID?.()` — const, line 89
- `function refused(error: unknown): boolean` — function, line 93
- `const latest = this.latest` — const, line 118
- `const at = this.now()` — const, line 146
- `const covered = this.covered(at)` — const, line 156
- `const due = !covered || at - (this.latest?.sentMs ?? Number.NEGATIVE_INFINITY) >= EXPOSURE.renewAfterMs` — const, line 157
- `const pending = this.pending ??` — const, line 171
- `let call: Promise<unknown>` — let, line 177
- `const stampMs = this.stampOf(receipt, pending.firstSentMs)` — const, line 185
- `const at = receipt && typeof receipt === "object" ? (receipt as DisplayReceipt).recordedAt : null` — const, line 208
- `const parsed = typeof at === "string" ? Date.parse(at) : Number.NaN` — const, line 209
- `function documentVisible(): boolean` — function, line 214
- `const PRESENCE_EVENTS = ["pointerdown", "pointermove", "keydown", "wheel", "touchstart"] as const` — const, line 218
- `const SHELL_SETTLE_MS = 300` — const, line 222
- `const recordRef = useRef(record)` — const, line 233
- `const bump = useCallback(()` — const, line 236
- `const gates = useRef<` — const, line 237
- `const gate = gates.current.gate` — const, line 248
- `const shellHeldRef = useRef(shellHeld)` — const, line 255
- `const wanted = onScreen && visible && !shellHeld && record !== undefined` — const, line 257
- `const wantedRef = useRef(wanted)` — const, line 258
- `let requery: (()` — let, line 265
- `const hide = ()` — const, line 269
- `const onVisibility = ()` — const, line 274
- `const isVisible = documentVisible()` — const, line 275
- `const back = ()` — const, line 285
- `const present = ()` — const, line 290
- `let disposed = false` — let, line 315
- `let generation = 0` — let, line 316
- `const unlisten: (()` — const, line 317
- `const keep = (listener: Promise<()` — const, line 318
- `let settle: number | undefined` — let, line 323
- `const appWindow = getCurrentWindow()` — const, line 325
- `const ask = ()` — const, line 328
- `const asked = generation` — const, line 330
- `const shellEvent = ()` — const, line 343
- `const timer = window.setInterval(()` — const, line 361
- `const show = useCallback(()` — const, line 390

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `RecordDisplay`, `useAnswerExposure`; references `RecordDisplay`, `useAnswerExposure`
- [[Reference/Desktop/TypeScript/screens/feedback/FeedbackSurface|src/screens/feedback/FeedbackSurface.tsx]] — import-or-re-export: `ExposureStatus`, `useAnswerExposure`; references `ExposureStatus`, `useAnswerExposure`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

- Local asset: [apps/learnloop-tauri/src/screens/feedback/exposureContract.json](../../../../../../../apps/learnloop-tauri/src/screens/feedback/exposureContract.json)
- Imported packages/crates: `@tauri-apps/api/window`, `react`, `react-dom`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/feedback/answerExposure.test.ts](../../../../../../../apps/learnloop-tauri/src/screens/feedback/answerExposure.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/feedback/answerExposure.shell.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/feedback/answerExposure.shell.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_review_log.py](../../../../../../../tests/test_review_log.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_learner_review_system_entries.py](../../../../../../../tests/test_learner_review_system_entries.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_forecast_ledger.py](../../../../../../../tests/test_forecast_ledger.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/feedback/answerExposure.ts](../../../../../../../apps/learnloop-tauri/src/screens/feedback/answerExposure.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
