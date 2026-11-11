---
title: "Desktop module · src/screens/practice/useAdaptiveHints.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.practice.useAdaptiveHints"
language: "TypeScript"
area: "TypeScript/screens/practice"
source_path: "apps/learnloop-tauri/src/screens/practice/useAdaptiveHints.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/practice/useAdaptiveHints.ts"
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

# `src/screens/practice/useAdaptiveHints.ts`

Area: [[Reference/Desktop/TypeScript/screens/practice/_area|TypeScript/screens/practice]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `HintEntry`, `HintNotice`, `AdaptiveHintsOptions`, `useAdaptiveHints` and related exports within the desktop's TypeScript/screens/practice ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/practice/useAdaptiveHints.ts](../../../../../../../apps/learnloop-tauri/src/screens/practice/useAdaptiveHints.ts) |
| Source lines | 523 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/practice/_area|TypeScript/screens/practice]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/practice/useAdaptiveHints|src/screens/practice/useAdaptiveHints.ts]]

## Public API

- `export interface HintEntry` — interface, line 45
- `export interface HintNotice` — interface, line 55
- `export interface AdaptiveHintsOptions` — interface, line 76
- `export function useAdaptiveHints(options: AdaptiveHintsOptions)` — function, line 97
- `export type AdaptiveHints = ReturnType<typeof useAdaptiveHints>` — type, line 523

## Internal implementation anchors

- `interface Pending` — interface, line 61
- `const POLL_DELAYS_MS = [350, 600, 900, 1200, 1500]` — const, line 68
- `function gone(error: unknown): boolean` — function, line 72
- `const opts = useRef(options)` — const, line 102
- `const pendingRef = useRef<Pending | null>(null)` — const, line 104
- `const generation = useRef(0)` — const, line 107
- `const timers = useRef<number[]>([])` — const, line 108
- `const suspended = useRef(false)` — const, line 110
- `const inflight = useRef(new Set<Promise<unknown>>())` — const, line 112
- `const pollChain = useRef(0)` — const, line 114
- `const retained = useRef(new Set<string>())` — const, line 119
- `const holdGen = useRef(0)` — const, line 123
- `const offerClaim = useRef<string | null>(null)` — const, line 125
- `const track = <T,>(work: Promise<T>): Promise<T>` — const, line 127
- `const done = ()` — const, line 129
- `const clearTimers = ()` — const, line 134
- `const settle = useCallback(()` — const, line 156
- `const handleDone = useCallback((result: HintResultDto | null)` — const, line 163
- `const poll = useCallback((jobId: string, attempt: number, mine: number, chain: number = pollChain.current)` — const, line 190
- `const delay = POLL_DELAYS_MS[Math.min(attempt, POLL_DELAYS_MS.length - 1)]` — const, line 191
- `const timer = window.setTimeout(async ()` — const, line 192
- `let job: HintJobDto` — let, line 197
- `const current = pendingRef.current?.jobId === jobId` — const, line 214
- `const request = useCallback((input: Omit<HintRequestInput, "sessionId" | "practiceItemId" | "submissionId">)` — const, line 227
- `const o = opts.current` — const, line 228
- `const send = async (input: Omit<HintRequestInput, "sessionId" | "practiceItemId" | "submissionId">)` — const, line 233
- `const o = opts.current` — const, line 234
- `const mine = generation.current` — const, line 235
- `const started: Pending =` — const, line 236
- `const job = await api.requestHint(` — const, line 245
- `const live: Pending =` — const, line 259
- `const offerTimer = window.setTimeout(()` — const, line 264
- `const clientCount = entries.filter((entry)` — const, line 278
- `const nextAuthoredIndex = useMemo(()` — const, line 279
- `const shown = new Set<number>()` — const, line 280
- `const takeAuthoredInstead = useCallback(()` — const, line 290
- `const live = pendingRef.current` — const, line 291
- `const index = nextAuthoredIndex` — const, line 292
- `const release = ()` — const, line 300
- `const revealInstead = async (live: Pending, index: number)` — const, line 309
- `const jobId = live.jobId as string` — const, line 310
- `const mine = generation.current` — const, line 311
- `let cancelled = false` — let, line 312
- `const answer = await api.cancelHint(jobId)` — const, line 314
- `const text = opts.current.authoredHints[index] ?? ""` — const, line 331
- `const key = `client-$` — const, line 332
- `const assistId = await opts.current.onAuthoredReveal(index)` — const, line 341
- `const hold = useCallback(async (): Promise<boolean>` — const, line 360
- `const mine = generation.current` — const, line 366
- `const live = pendingRef.current` — const, line 367
- `let reported = false` — let, line 372
- `const answer = await track(api.cancelHint(jobId))` — const, line 375
- `const job = await track(api.hintJob(jobId))` — const, line 382
- `const holdGeneration = useCallback(()` — const, line 402
- `const resume = useCallback((heldAt?: number)` — const, line 408
- `const mine = generation.current` — const, line 412
- `const at = holdGen.current` — const, line 413
- `const adopted: Pending =` — const, line 422
- `const press = useCallback(()` — const, line 440
- `const reply = useCallback((entry: HintEntry, reply:` — const, line 441
- `const bookWay = useCallback((entry: HintEntry)` — const, line 453
- `const smallerStep = useCallback((entry: HintEntry)` — const, line 456
- `const takeWorked = useCallback((level: 4 | 5)` — const, line 459
- `const answerDiscriminating = useCallback(async (entry: HintEntry, text: string)` — const, line 461
- `const o = opts.current` — const, line 462
- `const mine = generation.current` — const, line 464
- `let answer: HintDiscriminateAnswerDto` — let, line 465
- `const saveHelpStyle = useCallback(async (style: HelpStyle)` — const, line 481
- `const saved = await api.setHelpStyle(style)` — const, line 483
- `const picks = useMemo(()` — const, line 492
- `const found = entries[index].result.picks` — const, line 494

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `useAdaptiveHints`; references `useAdaptiveHints`
- [[Reference/Desktop/TypeScript/screens/practice/HintPanel|src/screens/practice/HintPanel.tsx]] — import-or-re-export: `AdaptiveHints`, `HintEntry`; references `AdaptiveHints`, `HintEntry`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `HelpStyle`, `HintDiscriminateAnswerDto`, `HintJobDto`, `HintRequestInput`, `HintResultDto`, `HintShortcut`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/screens/practice/hintCopy|src/screens/practice/hintCopy.ts]] — import-or-re-export; imports `HINT_COPY`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/practice/useAdaptiveHints.hold.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/practice/useAdaptiveHints.hold.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_large_practice_flow.py](../../../../../../../tests/test_large_practice_flow.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_contract.py](../../../../../../../tests/test_sidecar_contract.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_practice_information.py](../../../../../../../tests/test_practice_information.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/practice/useAdaptiveHints.ts](../../../../../../../apps/learnloop-tauri/src/screens/practice/useAdaptiveHints.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
