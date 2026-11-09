---
title: "Desktop module · src/screens/workbench/Workbench.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.workbench.Workbench"
language: "TypeScript"
area: "TypeScript/screens/workbench"
source_path: "apps/learnloop-tauri/src/screens/workbench/Workbench.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/workbench/Workbench.tsx"
source_commit: "5fe3a22558905593434e76e97a9375a41bf0354f"
source_commit_timestamp: "2026-11-08T19:24:01-05:00"
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

# `src/screens/workbench/Workbench.tsx`

Area: [[Reference/Desktop/TypeScript/screens/workbench/_area|TypeScript/screens/workbench]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `Workbench` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/workbench/Workbench.tsx](../../../../../../../apps/learnloop-tauri/src/screens/workbench/Workbench.tsx) |
| Source lines | 862 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/workbench/_area|TypeScript/screens/workbench]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `5fe3a22558905593434e76e97a9375a41bf0354f` |
| Commit timestamp | `2026-11-08T19:24:01-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/workbench/Workbench|src/screens/workbench/Workbench.tsx]]

## Public API

- `export type WorkbenchLayout = "split" | "stacked" | "full"` — type, line 42
- `export interface WorkbenchProps` — interface, line 44
- `export function stepsAsWork(steps: readonly` — function, line 115
- `export function Workbench(props: WorkbenchProps)` — function, line 126

## Internal implementation anchors

- `const linkStyle: CSSProperties =` — const, line 104
- `const actionStyle: CSSProperties =` — const, line 108
- `function isTyping(target: EventTarget | null): boolean` — function, line 122
- `const wb = useWorkbenchSession(initial,` — const, line 128
- `const serverSession = props.serverSession` — const, line 130
- `const applyServer = wb.applyServer` — const, line 131
- `const regionRef = useRef<HTMLElement | null>(null)` — const, line 135
- `const first = steps[0]` — const, line 137
- `const openedAt = useRef(Date.now())` — const, line 145
- `const timer = setInterval(()` — const, line 149
- `const title = problemTitle(session.stemMd)` — const, line 153
- `const fromBook = session.origin === "reader"` — const, line 154
- `const asPrinted = useAsPrinted(props.hideProblem ? null : session.practiceItemId)` — const, line 158
- `const blocksPrint = useProblemCrops( !props.hideProblem && !session.practiceItemId && fromBook ? session.extractionId : null, session.spanIds, session.printRegion ?? null, )` — const, line 162
- `const originalPageTarget: OriginalPageTarget | null = session.practiceItemId ? (asPrinted?.kind === "page" && asPrinted.originalPage ? asPrinted.originalPage : null) : originalPageOfCrops(blocksPrint, session.sourceId)` — const, line 169
- `const bound = session.practiceItemId !== null` — const, line 173
- `const open = session.status === "open"` — const, line 174
- `const live = liveSteps(steps)` — const, line 175
- `const workMd = stepsAsWork(live)` — const, line 176
- `const onWorkChange = props.onWorkChange` — const, line 177
- `const leaving = wb.leaving` — const, line 183
- `const helpConfig = algoConfig().workbenchHelp` — const, line 187
- `const hintsConfig = algoConfig().adaptiveHints` — const, line 188
- `const rw2c = useRouteExamples(` — const, line 191
- `const help = useWorkbenchHelp(` — const, line 201
- `const helpOn = helpConfig !== null` — const, line 219
- `const canHelp = helpOn && open && !readOnly && bound && !leaving` — const, line 220
- `const focusedChain = (()` — const, line 221
- `const step = live.find((candidate)` — const, line 222
- `const stepOptions: StepOption[] = live.flatMap((step, index)` — const, line 225
- `const chain = stepChain(step)` — const, line 226
- `const check = helpOn ? withLocalEdits(help.check, live.map((step)` — const, line 231
- `const liveChains = new Set(stepOptions.map((option)` — const, line 234
- `const onAStep = (stepId: string | null)` — const, line 235
- `const ladderLoose = helpOn && help.ladder.open && !onAStep(help.ladder.focusedStepId ?? focusedChain)` — const, line 236
- `const pendingLoose = Boolean(helpOn && help.hintPending && !onAStep(help.hintPending.stepId ?? focusedChain))` — const, line 237
- `const noticeLoose = Boolean(helpOn && help.notice && !onAStep(help.notice.stepId ?? focusedChain))` — const, line 238
- `const looseHints = helpOn ? help.hints.filter((hint)` — const, line 239
- `const takeWorked = canHelp ? (level: 4 | 5)` — const, line 243
- `function openAskInline()` — function, line 244
- `const askSignal = props.askSignal ?? 0` — const, line 248
- `const askSignalSeen = useRef(askSignal)` — const, line 249
- `function runCheck()` — function, line 257
- `function openHelp()` — function, line 261
- `function smallerStep()` — function, line 265
- `const waypoint = [...help.hints].reverse().find((hint)` — const, line 266
- `function peek(spanId: string, target?: PassageTarget)` — function, line 270
- `function requestFocus(key: string)` — function, line 276
- `async function submit()` — function, line 280
- `const named = props.schedulerCandidateId !== undefined || props.planPresentationId !== undefined` — const, line 291
- `const result = await wb.submit(` — const, line 292
- `const command = getCommandError(error)` — const, line 300
- `const departing = useRef(false)` — const, line 311
- `async function depart(then: (session: WorkbenchSessionDto)` — function, line 312
- `let result:` — let, line 317
- `async function leave()` — function, line 331
- `async function abandon()` — function, line 335
- `const closed = await wb.abandon()` — const, line 338
- `function stuck()` — function, line 342
- `const key = wb.addStep(null, "stuck")` — const, line 344
- `function toggleBook()` — function, line 348
- `function moveFocus(fromKey: string | null, delta: number)` — function, line 353
- `const keys = live.map((step)` — const, line 354
- `const index = fromKey ? keys.indexOf(fromKey) : -1` — const, line 355
- `const target = keys[Math.min(keys.length - 1, Math.max(0, index + delta))]` — const, line 356
- `function onRegionKeyDown(event: ReactKeyboardEvent<HTMLElement>)` — function, line 360
- `const ctrl = event.ctrlKey || event.metaKey` — const, line 361
- `const key = event.key` — const, line 362
- `const handled = ()` — const, line 363
- `const current = steps.find((step)` — const, line 406
- `function onStepKeyDown(stepKey: string, event: ReactKeyboardEvent<HTMLTextAreaElement>, info: LiveMarkdownKeyInfo)` — function, line 411
- `const key = wb.addStep(stepKey, "step")` — const, line 414
- `const index = live.findIndex((step)` — const, line 419
- `const previous = live[index - 1]` — const, line 421
- `const header = ( <div data-testid="workbench-header" style=` — const, line 426
- `const setup = !readOnly && session.status !== "submitted" ? ( session.importStatus === "pending" && session.parts && session.parts.length > 1 ? ( <div role="group" aria-label="which part" style=` — const, line 459
- `const pickedExposure = session.exercisePick?.exposure ?? null` — const, line 495
- `const exposureNote = !readOnly && session.status !== "submitted" && pickedExposure?.exposed ? ( <div data-testid="workbench-exercise-exposure"> <MeaningLabel style=` — const, line 496
- `const problem = ( <div style=` — const, line 508
- `const bookLine = fromBook && open && !readOnly && !wb.started ? ( <div role="radiogroup" aria-label="the book while you work" style=` — const, line 547
- `const checked = session.sourceVisible === visible` — const, line 550
- `let number = 0` — let, line 570
- `const work = ( <div style=` — const, line 571
- `const label = `Step $` — const, line 591
- `const editor = readOnly ? ( <div style=` — const, line 600
- `const chain = stepChain(step)` — const, line 616
- `const verdict = helpOn && chain ? verdictFor(check, chain) : null` — const, line 617
- `const stepHints = helpOn && chain ? help.hints.filter((hint)` — const, line 618
- `const ladderHere = helpOn && help.ladder.open && chain !== null && (help.ladder.focusedStepId ?? focusedChain) === chain` — const, line 619
- `const pendingHere = helpOn && help.hintPending && chain !== null && (help.hintPending.stepId ?? focusedChain) === chain` — const, line 620
- `const noticeHere = helpOn && help.notice && chain !== null && (help.notice.stepId ?? focusedChain) === chain` — const, line 621
- `const focusedVerdict = helpOn && focusedKey ? verdictFor(check, stepChain(live.find((entry)` — const, line 623
- `const outlined = Boolean(chain && focusedVerdict?.dependsOn.includes(chain))` — const, line 624
- `const confidenceRow = helpOn && open && !readOnly && bound ? ( <div role="radiogroup" aria-label=` — const, line 745
- `const recordLine = ( <div style=` — const, line 759
- `const actions = !readOnly && open ? ( <div style=` — const, line 766
- `const reopenLine = !readOnly && session.status === "abandoned" ? ( <MeaningLabel style=` — const, line 814

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `Workbench`; references `Workbench`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderWorkingPosture|src/screens/reader/ReaderWorkingPosture.tsx]] — import-or-re-export: `Workbench`; references `Workbench`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `PassageTarget`, `WorkbenchSessionDto`, `WorkbenchSubmitDto`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `algoConfig`
- [[Reference/Desktop/TypeScript/components/AsPrinted|src/components/AsPrinted.tsx]] — import-or-re-export; imports `AS_PRINTED_COPY`, `AsPrinted`, `BlocksAsPrinted`, `OriginalPageTarget`, `originalPageOfCrops`, `useAsPrinted`, `useProblemCrops`
- [[Reference/Desktop/TypeScript/components/ItemPresentation|src/components/ItemPresentation.tsx]] — import-or-re-export; imports `ItemPresentation`
- [[Reference/Desktop/TypeScript/components/OpenInSource|src/components/OpenInSource.tsx]] — import-or-re-export; imports `OpenInSource`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `COLOR`, `FONT_MONO`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/render/LiveMarkdownEditor|src/render/LiveMarkdownEditor.tsx]] — import-or-re-export; imports `LiveMarkdownEditor`, `LiveMarkdownKeyInfo`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/screens/reader/exerciseCandidates (ts)|src/screens/reader/exerciseCandidates.ts]] — import-or-re-export; imports `EXERCISE_COPY`, `keyStatusLine`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `LearnerVoice`, `MeaningLabel`, `SourceVoice`
- [[Reference/Desktop/TypeScript/screens/workbench/CheckColumn|src/screens/workbench/CheckColumn.tsx]] — import-or-re-export; imports `CheckSummary`, `QuestionableNote`, `VerdictCell`
- [[Reference/Desktop/TypeScript/screens/workbench/HelpLadder|src/screens/workbench/HelpLadder.tsx]] — import-or-re-export; imports `HelpLadder`
- [[Reference/Desktop/TypeScript/screens/workbench/HelpStyleControl|src/screens/workbench/HelpStyleControl.tsx]] — import-or-re-export; imports `HelpStyleControl`
- [[Reference/Desktop/TypeScript/screens/workbench/RouteExample|src/screens/workbench/RouteExample.tsx]] — import-or-re-export; imports `PassageExtras`, `ShowMeExample`, `useRouteExamples`
- [[Reference/Desktop/TypeScript/screens/workbench/StepHints|src/screens/workbench/StepHints.tsx]] — import-or-re-export; imports `HintCard`, `StepOption`
- [[Reference/Desktop/TypeScript/screens/workbench/WhereThisGoes|src/screens/workbench/WhereThisGoes.tsx]] — import-or-re-export; imports `WhereThisGoes`
- [[Reference/Desktop/TypeScript/screens/workbench/helpModel|src/screens/workbench/helpModel.ts]] — import-or-re-export; imports `HELP_COPY`, `verdictFor`, `withLocalEdits`
- [[Reference/Desktop/TypeScript/screens/workbench/stepModel|src/screens/workbench/stepModel.ts]] — import-or-re-export; imports `WORKBENCH_COPY`, `liveSteps`, `problemTitle`, `savedLabel`, `stepChain`
- [[Reference/Desktop/TypeScript/screens/workbench/useWorkbenchHelp|src/screens/workbench/useWorkbenchHelp.ts]] — import-or-re-export; imports `useWorkbenchHelp`
- [[Reference/Desktop/TypeScript/screens/workbench/useWorkbenchSession|src/screens/workbench/useWorkbenchSession.ts]] — import-or-re-export; imports `useWorkbenchSession`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/workbench/rw2cFixRound2.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/workbench/rw2cFixRound2.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/workbench/reviewFixes.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/workbench/reviewFixes.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/workbench/ownerCapture1025.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/workbench/ownerCapture1025.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/workbench/asPrinted.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/workbench/asPrinted.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/workbench/Workbench.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/workbench/Workbench.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/workbench/RouteExample.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/workbench/RouteExample.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/workbench/HelpLadder.test.tsx](../../../../../../../apps/learnloop-tauri/src/screens/workbench/HelpLadder.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_owner_capture_1025.py](../../../../../../../tests/test_owner_capture_1025.py) — cross-boundary name contract: references uniquely owned exported name `Workbench`; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/workbench/Workbench.tsx](../../../../../../../apps/learnloop-tauri/src/screens/workbench/Workbench.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
