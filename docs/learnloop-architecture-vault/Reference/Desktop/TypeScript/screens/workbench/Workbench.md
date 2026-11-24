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
| Source lines | 927 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/workbench/_area|TypeScript/screens/workbench]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/workbench/Workbench|src/screens/workbench/Workbench.tsx]]

## Public API

- `export type WorkbenchLayout = "split" | "stacked" | "full"` — type, line 44
- `export interface WorkbenchProps` — interface, line 46
- `export interface HandwrittenWork` — interface, line 113
- `export function stepsAsWork(steps: readonly` — function, line 135
- `export function Workbench(props: WorkbenchProps)` — function, line 146

## Internal implementation anchors

- `const linkStyle: CSSProperties =` — const, line 124
- `const actionStyle: CSSProperties =` — const, line 128
- `function isTyping(target: EventTarget | null): boolean` — function, line 142
- `const wb = useWorkbenchSession(initial,` — const, line 148
- `const handwritten = props.handwritten` — const, line 151
- `const linesKey = JSON.stringify(handwritten?.lines ?? [])` — const, line 152
- `const bindLine = wb.bindLine` — const, line 153
- `const lineOfStep = new Map<string, string>()` — const, line 159
- `const taken = new Set(lineOfStep.values())` — const, line 162
- `const line = handwritten.lines.find((each)` — const, line 165
- `const serverSession = props.serverSession` — const, line 172
- `const applyServer = wb.applyServer` — const, line 173
- `const regionRef = useRef<HTMLElement | null>(null)` — const, line 177
- `const first = steps[0]` — const, line 179
- `const openedAt = useRef(Date.now())` — const, line 187
- `const activeClock = useAttemptClock()` — const, line 190
- `const hostClock = props.activeSeconds` — const, line 191
- `const paused = useWindowPaused()` — const, line 197
- `const timer = setInterval(()` — const, line 202
- `const title = problemTitle(session.stemMd)` — const, line 206
- `const fromBook = session.origin === "reader"` — const, line 207
- `const asPrinted = useAsPrinted(props.hideProblem ? null : session.practiceItemId)` — const, line 211
- `const blocksPrint = useProblemCrops( !props.hideProblem && !session.practiceItemId && fromBook ? session.extractionId : null, session.spanIds, session.printRegion ?? null, )` — const, line 215
- `const originalPageTarget: OriginalPageTarget | null = session.practiceItemId ? (asPrinted?.kind === "page" && asPrinted.originalPage ? asPrinted.originalPage : null) : originalPageOfCrops(blocksPrint, session.sourceId)` — const, line 222
- `const bound = session.practiceItemId !== null` — const, line 226
- `const open = session.status === "open"` — const, line 227
- `const live = liveSteps(steps)` — const, line 228
- `const workMd = stepsAsWork(live)` — const, line 229
- `const onWorkChange = props.onWorkChange` — const, line 230
- `const leaving = wb.leaving` — const, line 236
- `const helpConfig = algoConfig().workbenchHelp` — const, line 240
- `const hintsConfig = algoConfig().adaptiveHints` — const, line 241
- `const rw2c = useRouteExamples(` — const, line 244
- `const help = useWorkbenchHelp(` — const, line 254
- `const helpOn = helpConfig !== null` — const, line 272
- `const canHelp = helpOn && open && !readOnly && bound && !leaving` — const, line 273
- `const focusedChain = (()` — const, line 274
- `const step = live.find((candidate)` — const, line 275
- `const stepOptions: StepOption[] = live.flatMap((step, index)` — const, line 278
- `const chain = stepChain(step)` — const, line 279
- `const check = helpOn ? withLocalEdits(help.check, live.map((step)` — const, line 284
- `const liveChains = new Set(stepOptions.map((option)` — const, line 287
- `const onAStep = (stepId: string | null)` — const, line 288
- `const ladderLoose = helpOn && help.ladder.open && !onAStep(help.ladder.focusedStepId ?? focusedChain)` — const, line 289
- `const pendingLoose = Boolean(helpOn && help.hintPending && !onAStep(help.hintPending.stepId ?? focusedChain))` — const, line 290
- `const noticeLoose = Boolean(helpOn && help.notice && !onAStep(help.notice.stepId ?? focusedChain))` — const, line 291
- `const looseHints = helpOn ? help.hints.filter((hint)` — const, line 292
- `const takeWorked = canHelp ? (level: 4 | 5)` — const, line 296
- `function openAskInline()` — function, line 297
- `const askSignal = props.askSignal ?? 0` — const, line 301
- `const askSignalSeen = useRef(askSignal)` — const, line 302
- `function runCheck()` — function, line 310
- `function openHelp()` — function, line 314
- `function smallerStep()` — function, line 318
- `const waypoint = [...help.hints].reverse().find((hint)` — const, line 319
- `function peek(spanId: string, target?: PassageTarget)` — function, line 323
- `function requestFocus(key: string)` — function, line 329
- `async function submit()` — function, line 333
- `const named = props.schedulerCandidateId !== undefined || props.planPresentationId !== undefined` — const, line 344
- `const result = await wb.submit(` — const, line 345
- `const command = getCommandError(error)` — const, line 355
- `const departing = useRef(false)` — const, line 366
- `async function depart(then: (session: WorkbenchSessionDto)` — function, line 367
- `let result:` — let, line 372
- `async function leave()` — function, line 386
- `async function abandon()` — function, line 390
- `const closed = await wb.abandon()` — const, line 393
- `function stuck()` — function, line 397
- `const key = wb.addStep(null, "stuck")` — const, line 399
- `function toggleBook()` — function, line 403
- `function moveFocus(fromKey: string | null, delta: number)` — function, line 408
- `const keys = live.map((step)` — const, line 409
- `const index = fromKey ? keys.indexOf(fromKey) : -1` — const, line 410
- `const target = keys[Math.min(keys.length - 1, Math.max(0, index + delta))]` — const, line 411
- `function onRegionKeyDown(event: ReactKeyboardEvent<HTMLElement>)` — function, line 415
- `const ctrl = event.ctrlKey || event.metaKey` — const, line 416
- `const key = event.key` — const, line 417
- `const handled = ()` — const, line 418
- `const current = steps.find((step)` — const, line 461
- `function onStepKeyDown(stepKey: string, event: ReactKeyboardEvent<HTMLTextAreaElement>, info: LiveMarkdownKeyInfo)` — function, line 466
- `const key = wb.addStep(stepKey, "step")` — const, line 469
- `const index = live.findIndex((step)` — const, line 474
- `const previous = live[index - 1]` — const, line 476
- `const header = ( <div data-testid="workbench-header" style=` — const, line 481
- `const setup = !readOnly && session.status !== "submitted" ? ( session.importStatus === "pending" && session.parts && session.parts.length > 1 ? ( <div role="group" aria-label="which part" style=` — const, line 514
- `const pickedExposure = session.exercisePick?.exposure ?? null` — const, line 550
- `const exposureNote = !readOnly && session.status !== "submitted" && pickedExposure?.exposed ? ( <div data-testid="workbench-exercise-exposure"> <MeaningLabel style=` — const, line 551
- `const problem = ( <div style=` — const, line 563
- `const bookLine = fromBook && open && !readOnly && !wb.started ? ( <div role="radiogroup" aria-label="the book while you work" style=` — const, line 602
- `const checked = session.sourceVisible === visible` — const, line 605
- `let number = 0` — let, line 625
- `const work = ( <div style=` — const, line 626
- `const label = `Step $` — const, line 646
- `const inkLine = handwritten ? lineOfStep.get(step.key) : undefined` — const, line 655
- `const editor = inkLine !== undefined ? ( <div data-ink-step=` — const, line 656
- `const chain = stepChain(step)` — const, line 674
- `const verdict = helpOn && chain ? verdictFor(check, chain) : null` — const, line 675
- `const stepHints = helpOn && chain ? help.hints.filter((hint)` — const, line 676
- `const ladderHere = helpOn && help.ladder.open && chain !== null && (help.ladder.focusedStepId ?? focusedChain) === chain` — const, line 677
- `const pendingHere = helpOn && help.hintPending && chain !== null && (help.hintPending.stepId ?? focusedChain) === chain` — const, line 678
- `const noticeHere = helpOn && help.notice && chain !== null && (help.notice.stepId ?? focusedChain) === chain` — const, line 679
- `const focusedVerdict = helpOn && focusedKey ? verdictFor(check, stepChain(live.find((entry)` — const, line 681
- `const outlined = Boolean(chain && focusedVerdict?.dependsOn.includes(chain))` — const, line 682
- `const confidenceRow = helpOn && open && !readOnly && bound ? ( <div role="radiogroup" aria-label=` — const, line 810
- `const recordLine = ( <div style=` — const, line 824
- `const actions = !readOnly && open ? ( <div style=` — const, line 831
- `const reopenLine = !readOnly && session.status === "abandoned" ? ( <MeaningLabel style=` — const, line 879

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `Workbench`; references `Workbench`
- [[Reference/Desktop/TypeScript/screens/desks/problem/ProblemPad|src/screens/desks/problem/ProblemPad.tsx]] — import-or-re-export: `HandwrittenWork`, `Workbench`; references `HandwrittenWork`, `Workbench`
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
- [[Reference/Desktop/TypeScript/screens/desks/lifecycle|src/screens/desks/lifecycle.tsx]] — import-or-re-export; imports `useWindowPaused`
- [[Reference/Desktop/TypeScript/screens/reader/exerciseCandidates (ts)|src/screens/reader/exerciseCandidates.ts]] — import-or-re-export; imports `EXERCISE_COPY`, `keyStatusLine`
- [[Reference/Desktop/TypeScript/screens/reader/voices|src/screens/reader/voices.tsx]] — import-or-re-export; imports `LearnerVoice`, `MeaningLabel`, `SourceVoice`
- [[Reference/Desktop/TypeScript/screens/useAttemptClock|src/screens/useAttemptClock.ts]] — import-or-re-export; imports `useAttemptClock`
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
