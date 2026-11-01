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
source_commit: "ae8339e6a36086fbd02e406b50925dd747ad3d6e"
source_commit_timestamp: "2026-10-20T12:30:38-04:00"
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
| Source lines | 651 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/workbench/_area|TypeScript/screens/workbench]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `ae8339e6a36086fbd02e406b50925dd747ad3d6e` |
| Commit timestamp | `2026-10-20T12:30:38-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/workbench/Workbench|src/screens/workbench/Workbench.tsx]] → [[Reference/Desktop/TypeScript/screens/workbench/useWorkbenchSession|src/screens/workbench/useWorkbenchSession.ts]]

## Public API

- `export const EDIT_DEBOUNCE_MS = 600` — const, line 56
- `export function leaveHeldNote(reason: string | null): string` — function, line 77
- `export function leftUnsavedNote(reason: string | null): string` — function, line 82
- `export function notSavedError(reason: string | null, action: string):` — function, line 89
- `export interface WorkbenchSessionControls` — interface, line 98
- `export function useWorkbenchSession( initial: WorkbenchSessionDto, options:` — function, line 138

## Internal implementation anchors

- `type LocalStep, type SaveStatus, } from "./stepModel"` — type, line 51
- `type SaveStatus, } from "./stepModel"` — type, line 52
- `const RETRY_DELAYS_MS = [1000, 2000, 4000, 8000]` — const, line 57
- `const RETRIES_AFTER_CLOSE = 5` — const, line 59
- `const PERMANENT = new Set(["validation_error", "not_found", "not_open", "already_submitted", "workbench_disabled", "no_book"])` — const, line 61
- `const BOOK_KEY = "\u0000book"` — const, line 63
- `type StepOpKind = "add" | "edit" | "delete" | "restore"` — type, line 65
- `type StepOp =` — type, line 66
- `type BookOp =` — type, line 67
- `type Op = StepOp | BookOp` — type, line 68
- `function newKey(): string` — function, line 70
- `const readOnly = options.readOnly ?? false` — const, line 142
- `const local = fromServer(initial.steps.filter((step)` — const, line 146
- `const sessionRef = useRef(session)` — const, line 155
- `const stepsRef = useRef(steps)` — const, line 156
- `const queue = useRef<Op[]>([])` — const, line 157
- `const running = useRef(false)` — const, line 158
- `const retryTimer = useRef<ReturnType<typeof setTimeout> | null>(null)` — const, line 159
- `const failures = useRef(0)` — const, line 160
- `const closed = useRef(false)` — const, line 161
- `const lifeSeq = useRef(0)` — const, line 166
- `const live = useRef<number | null>(null)` — const, line 167
- `const liveNow = ()` — const, line 169
- `const stillLive = (sentIn: number | null)` — const, line 171
- `const frozenRef = useRef(false)` — const, line 172
- `const leavingRef = useRef(false)` — const, line 174
- `const paused = ()` — const, line 176
- `const rejected = useRef(new Map<string, string>())` — const, line 178
- `const editTimers = useRef(new Map<string, ReturnType<typeof setTimeout>>())` — const, line 179
- `const waiters = useRef<Array<(ok: boolean)` — const, line 180
- `const onSessionRef = useRef(options.onSession)` — const, line 181
- `const onErrorRef = useRef(options.onError)` — const, line 183
- `const commitSteps = useCallback((next: LocalStep[])` — const, line 186
- `const commitSession = useCallback((next: WorkbenchSessionDto, notify = true)` — const, line 190
- `const firstRejection = useCallback(()` — const, line 197
- `const settleWaiters = useCallback((ok: boolean)` — const, line 199
- `const pending = waiters.current` — const, line 200
- `const settleIdle = useCallback(()` — const, line 206
- `const reason = firstRejection()` — const, line 207
- `const stepInput = useCallback((op: StepOp): WorkbenchSaveStepInput | null` — const, line 214
- `const list = stepsRef.current` — const, line 215
- `const index = list.findIndex((step)` — const, line 216
- `const step = list[index]` — const, line 217
- `const sessionId = sessionRef.current.sessionId` — const, line 219
- `const before = list.slice(0, index).reverse().find((candidate)` — const, line 221
- `const hasUnsentWrite = useCallback((key: string)` — const, line 229
- `const nextOp = useCallback((): Op | undefined` — const, line 235
- `const stepRefused = [...rejected.current.keys()].some((key)` — const, line 236
- `const firstBook = queue.current.find((queued)` — const, line 237
- `const holdBook = stepRefused && firstBook !== undefined && !firstBook.payload && !firstBook.visible` — const, line 238
- `const dequeue = useCallback((op: Op)` — const, line 241
- `const pump = useCallback(async ()` — const, line 245
- `const op = nextOp()` — const, line 247
- `const input = stepInput(op)` — const, line 259
- `const result = await api.workbenchSetBook(op.payload!)` — const, line 271
- `const result = await api.workbenchSaveStep(op.payload!)` — const, line 282
- `const local = stepsRef.current.find((step)` — const, line 289
- `const code = getCommandError(error)?.code ?? ""` — const, line 299
- `const delay = RETRY_DELAYS_MS[Math.min(failures.current, RETRY_DELAYS_MS.length - 1)]` — const, line 312
- `const enqueue = useCallback((op: Op)` — const, line 321
- `const queueEdit = useCallback((key: string)` — const, line 328
- `const step = stepsRef.current.find((candidate)` — const, line 329
- `const addQueued = queue.current.some((queued)` — const, line 331
- `const flushEdits = useCallback(()` — const, line 336
- `const setBody = useCallback((key: string, body: string)` — const, line 344
- `const timers = editTimers.current` — const, line 348
- `const existing = timers.get(key)` — const, line 349
- `const addStep = useCallback((afterKey: string | null, kind: WorkbenchStepKind = "step")` — const, line 357
- `const key = newKey()` — const, line 358
- `let list = stepsRef.current` — let, line 360
- `const unwritten = (step: LocalStep)` — const, line 363
- `const deleteStep = useCallback((key: string)` — const, line 377
- `const step = stepsRef.current.find((candidate)` — const, line 379
- `const timer = editTimers.current.get(key)` — const, line 381
- `const saved = step.serverId !== null || queue.current.some((queued)` — const, line 386
- `const undoDelete = useCallback((key: string)` — const, line 399
- `const drained = useCallback(()` — const, line 405
- `const persist = useCallback(async (action: string)` — const, line 413
- `const setBook = useCallback(async (visible: boolean)` — const, line 418
- `const leaveHeld = useRef(false)` — const, line 437
- `const departure = useRef<Promise<` — const, line 438
- `const leave = useCallback(()` — const, line 439
- `const startPause = ()` — const, line 442
- `const endPause = ()` — const, line 446
- `const check = async (): Promise<` — const, line 452
- `const reason = firstRejection()` — const, line 455
- `const run = async ()` — const, line 463
- `const first = await check()` — const, line 473
- `const last = first.note === null ? await check() : first` — const, line 484
- `const pending = run().finally(()` — const, line 492
- `const abandon = useCallback(async ()` — const, line 499
- `const sentIn = liveNow()` — const, line 503
- `const result = await api.workbenchAbandon(` — const, line 504
- `const reopen = useCallback(async ()` — const, line 513
- `const sentIn = liveNow()` — const, line 515
- `const result = await api.workbenchReopen(` — const, line 516
- `const retryImport = useCallback(async ()` — const, line 523
- `const sentIn = liveNow()` — const, line 525
- `const result = await api.workbenchRetryImport(` — const, line 526
- `const bind = useCallback(async (practiceItemId: string)` — const, line 533
- `const sentIn = liveNow()` — const, line 535
- `const result = await api.workbenchBind(` — const, line 536
- `const submit = useCallback(async (input: Omit<WorkbenchSubmitInput, "sessionId">)` — const, line 543
- `const sentIn = liveNow()` — const, line 545
- `const result = await api.workbenchSubmit(` — const, line 546
- `const flushForTransition = useCallback(async ()` — const, line 554
- `const flushForClose = useCallback(async ()` — const, line 574
- `const reportError = useCallback((message: string)` — const, line 578
- `const waiting = !readOnly && session.status !== "submitted" && session.importStatus === "pending" && !session.parts` — const, line 582
- `const timer = setInterval(()` — const, line 585
- `const sentIn = liveNow()` — const, line 586
- `const next = result.session` — const, line 593
- `const current = sessionRef.current` — const, line 594
- `const applyRecord = useCallback((next: WorkbenchRecordDto)` — const, line 631
- `const applyServer = useCallback((next: WorkbenchSessionDto)` — const, line 633
- `const current = sessionRef.current` — const, line 634

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/workbench/Workbench|src/screens/workbench/Workbench.tsx]] — import-or-re-export: `useWorkbenchSession`; references `useWorkbenchSession`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `WorkbenchRecordDto`, `WorkbenchSaveStepInput`, `WorkbenchSessionDto`, `WorkbenchStepKind`, `WorkbenchSubmitDto`, `WorkbenchSubmitInput`
- [[Reference/Desktop/TypeScript/app/useCloseWithFlush|src/app/useCloseWithFlush.ts]] — import-or-re-export; imports `useCloseWithFlush`
- [[Reference/Desktop/TypeScript/app/vaultTransition|src/app/vaultTransition.ts]] — import-or-re-export; imports `registerVaultDraft`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/screens/reader/ModelActionState|src/screens/reader/ModelActionState.tsx]] — import-or-re-export; imports `phaseForError`
- [[Reference/Desktop/TypeScript/screens/workbench/stepModel|src/screens/workbench/stepModel.ts]] — import-or-re-export; imports `LocalStep`, `SaveStatus`, `deleteLocal`, `fromServer`, `insertAfter`, `restoreLocal`, `updateLocal`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

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
