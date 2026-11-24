---
title: "Desktop module · src/screens/workbench/useWorkbenchSession.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.workbench.useWorkbenchSession"
language: "TypeScript"
area: "TypeScript/screens/workbench"
source_path: "apps/learnloop-tauri/src/screens/workbench/useWorkbenchSession.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/workbench/useWorkbenchSession.ts"
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

# `src/screens/workbench/useWorkbenchSession.ts`

Area: [[Reference/Desktop/TypeScript/screens/workbench/_area|TypeScript/screens/workbench]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `EDIT_DEBOUNCE_MS`, `leaveHeldNote`, `leftUnsavedNote`, `notSavedError` and related exports within the desktop's TypeScript/screens/workbench ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/workbench/useWorkbenchSession.ts](../../../../../../../apps/learnloop-tauri/src/screens/workbench/useWorkbenchSession.ts) |
| Source lines | 698 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/workbench/_area|TypeScript/screens/workbench]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/workbench/Workbench|src/screens/workbench/Workbench.tsx]] → [[Reference/Desktop/TypeScript/screens/workbench/useWorkbenchSession|src/screens/workbench/useWorkbenchSession.ts]]

## Public API

- `export const EDIT_DEBOUNCE_MS = 600` — const, line 58
- `export function leaveHeldNote(reason: string | null): string` — function, line 79
- `export function leftUnsavedNote(reason: string | null): string` — function, line 84
- `export function notSavedError(reason: string | null, action: string):` — function, line 91
- `export interface WorkbenchSessionControls` — interface, line 100
- `export function useWorkbenchSession( initial: WorkbenchSessionDto, options:` — function, line 146

## Internal implementation anchors

- `type LocalStep, type SaveStatus, } from "./stepModel"` — type, line 53
- `type SaveStatus, } from "./stepModel"` — type, line 54
- `const RETRY_DELAYS_MS = [1000, 2000, 4000, 8000]` — const, line 59
- `const RETRIES_AFTER_CLOSE = 5` — const, line 61
- `const PERMANENT = new Set(["validation_error", "not_found", "not_open", "already_submitted", "workbench_disabled", "no_book"])` — const, line 63
- `const BOOK_KEY = "\u0000book"` — const, line 65
- `type StepOpKind = "add" | "edit" | "delete" | "restore"` — type, line 67
- `type StepOp =` — type, line 68
- `type BookOp =` — type, line 69
- `type Op = StepOp | BookOp` — type, line 70
- `function newKey(): string` — function, line 72
- `const readOnly = options.readOnly ?? false` — const, line 150
- `const local = fromServer(initial.steps.filter((step)` — const, line 154
- `const sessionRef = useRef(session)` — const, line 163
- `const stepsRef = useRef(steps)` — const, line 164
- `const queue = useRef<Op[]>([])` — const, line 165
- `const running = useRef(false)` — const, line 166
- `const retryTimer = useRef<ReturnType<typeof setTimeout> | null>(null)` — const, line 167
- `const failures = useRef(0)` — const, line 168
- `const closed = useRef(false)` — const, line 169
- `const lifeSeq = useRef(0)` — const, line 174
- `const live = useRef<number | null>(null)` — const, line 175
- `const liveNow = ()` — const, line 177
- `const stillLive = (sentIn: number | null)` — const, line 179
- `const frozenRef = useRef(false)` — const, line 180
- `const leavingRef = useRef(false)` — const, line 182
- `const paused = ()` — const, line 184
- `const rejected = useRef(new Map<string, string>())` — const, line 186
- `const editTimers = useRef(new Map<string, ReturnType<typeof setTimeout>>())` — const, line 187
- `const waiters = useRef<Array<(ok: boolean)` — const, line 188
- `const onSessionRef = useRef(options.onSession)` — const, line 189
- `const onErrorRef = useRef(options.onError)` — const, line 191
- `const commitSteps = useCallback((next: LocalStep[])` — const, line 194
- `const commitSession = useCallback((next: WorkbenchSessionDto, notify = true)` — const, line 198
- `const firstRejection = useCallback(()` — const, line 205
- `const settleWaiters = useCallback((ok: boolean)` — const, line 207
- `const pending = waiters.current` — const, line 208
- `const settleIdle = useCallback(()` — const, line 214
- `const reason = firstRejection()` — const, line 215
- `const stepInput = useCallback((op: StepOp): WorkbenchSaveStepInput | null` — const, line 222
- `const list = stepsRef.current` — const, line 223
- `const index = list.findIndex((step)` — const, line 224
- `const step = list[index]` — const, line 225
- `const sessionId = sessionRef.current.sessionId` — const, line 227
- `const before = list.slice(0, index).reverse().find((candidate)` — const, line 229
- `const hasUnsentWrite = useCallback((key: string)` — const, line 237
- `const nextOp = useCallback((): Op | undefined` — const, line 243
- `const stepRefused = [...rejected.current.keys()].some((key)` — const, line 244
- `const firstBook = queue.current.find((queued)` — const, line 245
- `const holdBook = stepRefused && firstBook !== undefined && !firstBook.payload && !firstBook.visible` — const, line 246
- `const dequeue = useCallback((op: Op)` — const, line 249
- `const pump = useCallback(async ()` — const, line 253
- `const op = nextOp()` — const, line 255
- `const input = stepInput(op)` — const, line 267
- `const result = await api.workbenchSetBook(op.payload!)` — const, line 279
- `const result = await api.workbenchSaveStep(op.payload!)` — const, line 290
- `const listed = op.kind === "add" ? stepsRef.current.find((step)` — const, line 296
- `const line = listed ? [...boundRef.current].find(([, key])` — const, line 297
- `const body = stepsRef.current.find((step)` — const, line 299
- `const local = stepsRef.current.find((step)` — const, line 308
- `const code = getCommandError(error)?.code ?? ""` — const, line 318
- `const delay = RETRY_DELAYS_MS[Math.min(failures.current, RETRY_DELAYS_MS.length - 1)]` — const, line 331
- `const enqueue = useCallback((op: Op)` — const, line 340
- `const queueEdit = useCallback((key: string)` — const, line 347
- `const step = stepsRef.current.find((candidate)` — const, line 348
- `const addQueued = queue.current.some((queued)` — const, line 350
- `const flushEdits = useCallback(()` — const, line 355
- `const setBody = useCallback((key: string, body: string)` — const, line 363
- `const timers = editTimers.current` — const, line 367
- `const existing = timers.get(key)` — const, line 368
- `const addStep = useCallback((afterKey: string | null, kind: WorkbenchStepKind = "step")` — const, line 376
- `const key = newKey()` — const, line 377
- `let list = stepsRef.current` — let, line 379
- `const unwritten = (step: LocalStep)` — const, line 382
- `const boundRef = useRef<ReadonlyMap<string, string>>(new Map())` — const, line 396
- `const bindLine = useCallback((lineId: string, body: string)` — const, line 398
- `const key = boundRef.current.get(lineId)` — const, line 400
- `const step = stepsRef.current.find((candidate)` — const, line 402
- `const added = newKey()` — const, line 406
- `let list = stepsRef.current` — let, line 408
- `const unwritten = (step: LocalStep)` — const, line 409
- `const deleteStep = useCallback((key: string)` — const, line 420
- `const step = stepsRef.current.find((candidate)` — const, line 422
- `const timer = editTimers.current.get(key)` — const, line 424
- `const saved = step.serverId !== null || queue.current.some((queued)` — const, line 429
- `const undoDelete = useCallback((key: string)` — const, line 442
- `const drained = useCallback(()` — const, line 448
- `const persist = useCallback(async (action: string)` — const, line 456
- `const setBook = useCallback(async (visible: boolean)` — const, line 461
- `const leaveHeld = useRef(false)` — const, line 480
- `const departure = useRef<Promise<` — const, line 481
- `const leave = useCallback(()` — const, line 482
- `const startPause = ()` — const, line 485
- `const endPause = ()` — const, line 489
- `const check = async (): Promise<` — const, line 495
- `const reason = firstRejection()` — const, line 498
- `const run = async ()` — const, line 506
- `const first = await check()` — const, line 516
- `const last = first.note === null ? await check() : first` — const, line 527
- `const pending = run().finally(()` — const, line 535
- `const abandon = useCallback(async ()` — const, line 542
- `const sentIn = liveNow()` — const, line 546
- `const result = await api.workbenchAbandon(` — const, line 547
- `const reopen = useCallback(async ()` — const, line 557
- `const sentIn = liveNow()` — const, line 559
- `const result = await api.workbenchReopen(` — const, line 560
- `const retryImport = useCallback(async ()` — const, line 567
- `const sentIn = liveNow()` — const, line 569
- `const result = await api.workbenchRetryImport(` — const, line 570
- `const bind = useCallback(async (practiceItemId: string)` — const, line 577
- `const sentIn = liveNow()` — const, line 579
- `const result = await api.workbenchBind(` — const, line 580
- `const submit = useCallback(async (input: Omit<WorkbenchSubmitInput, "sessionId">)` — const, line 587
- `const sentIn = liveNow()` — const, line 589
- `const result = await api.workbenchSubmit(` — const, line 590
- `const flushForTransition = useCallback(async ()` — const, line 598
- `const flushForClose = useCallback(async ()` — const, line 618
- `const reportError = useCallback((message: string)` — const, line 622
- `const waiting = !readOnly && session.status !== "submitted" && session.importStatus === "pending" && !session.parts` — const, line 626
- `const windowPaused = useWindowPaused()` — const, line 628
- `const timer = setInterval(()` — const, line 631
- `const sentIn = liveNow()` — const, line 632
- `const next = result.session` — const, line 639
- `const current = sessionRef.current` — const, line 640
- `const applyRecord = useCallback((next: WorkbenchRecordDto)` — const, line 677
- `const applyServer = useCallback((next: WorkbenchSessionDto)` — const, line 679
- `const current = sessionRef.current` — const, line 680

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/workbench/Workbench|src/screens/workbench/Workbench.tsx]] — import-or-re-export: `useWorkbenchSession`; references `useWorkbenchSession`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `WorkbenchRecordDto`, `WorkbenchSaveStepInput`, `WorkbenchSessionDto`, `WorkbenchStepKind`, `WorkbenchSubmitDto`, `WorkbenchSubmitInput`
- [[Reference/Desktop/TypeScript/app/dailyPlan|src/app/dailyPlan.ts]] — import-or-re-export; imports `rereadPlanAfterWorkbenchClosed`
- [[Reference/Desktop/TypeScript/app/useCloseWithFlush|src/app/useCloseWithFlush.ts]] — import-or-re-export; imports `useCloseWithFlush`
- [[Reference/Desktop/TypeScript/app/vaultTransition|src/app/vaultTransition.ts]] — import-or-re-export; imports `registerVaultDraft`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `useWindowPaused`
- [[Reference/Desktop/TypeScript/screens/reader/ModelActionState|src/screens/reader/ModelActionState.tsx]] — import-or-re-export; imports `phaseForError`
- [[Reference/Desktop/TypeScript/screens/workbench/stepModel|src/screens/workbench/stepModel.ts]] — import-or-re-export; imports `LocalStep`, `SaveStatus`, `deleteLocal`, `fromServer`, `insertAfter`, `restoreLocal`, `updateLocal`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/workbench/handwritten.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/workbench/handwritten.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/workbench/Workbench.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/workbench/Workbench.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/workbench/useWorkbenchSession.ts](../../../../../../../apps/learnloop-tauri/src/screens/workbench/useWorkbenchSession.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
