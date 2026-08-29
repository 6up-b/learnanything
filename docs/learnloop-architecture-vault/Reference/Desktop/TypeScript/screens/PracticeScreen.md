---
title: "Desktop module · src/screens/PracticeScreen.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.PracticeScreen"
language: "TypeScript"
area: "TypeScript/screens"
source_path: "apps/learnloop-tauri/src/screens/PracticeScreen.tsx"
source_paths:
  - "apps/learnloop-tauri/src/screens/PracticeScreen.tsx"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
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

# `src/screens/PracticeScreen.tsx`

Area: [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Implements the `PracticeScreen` routed desktop screen and coordinates its learner-facing workflow state.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/PracticeScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/PracticeScreen.tsx) |
| Source lines | 1562 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/_area|TypeScript/screens]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]]

## Public API

- `export function PracticeScreen(` — function, line 91

## Internal implementation anchors

- `type CommittedAttemptRecovery =` — type, line 29
- `type PracticeCheckpointIdentity =` — type, line 35
- `function committedAttemptRecovery(error: unknown): CommittedAttemptRecovery | null` — function, line 40
- `const command = getCommandError(error)` — const, line 41
- `const details = command.details as` — const, line 45
- `const attemptId = details.attempt_id ?? details.attemptId` — const, line 51
- `const attemptType = details.attempt_type ?? details.attemptType` — const, line 53
- `function activeProbeContract(contract: ProbeContractDto): ProbeContractDto | null` — function, line 64
- `const restrictions = contract.restrictions` — const, line 74
- `const mountedRef = useRef(true)` — const, line 187
- `const submissionId = useRef(restoredSubmissionId?.trim() || crypto.randomUUID())` — const, line 188
- `const latestDraft = useRef(` — const, line 189
- `const suppressDraftFlush = useRef(false)` — const, line 196
- `const isTeachBack = item?.practiceMode === "teach_back"` — const, line 197
- `const teachBackRef = useRef(true)` — const, line 202
- `const teachBackActive = item ? item.practiceMode === "teach_back" : Boolean(restoredTeachBack)` — const, line 207
- `const openedAtMs = useRef(Date.now())` — const, line 214
- `const elapsedSeconds = ()` — const, line 223
- `const openAsk = (options?:` — const, line 234
- `const editorSlotRef = useRef<HTMLDivElement>(null)` — const, line 248
- `const belowRef = useRef<HTMLDivElement>(null)` — const, line 249
- `const recomputeEditorMax = useCallback(()` — const, line 252
- `const slot = editorSlotRef.current` — const, line 253
- `const top = slot.getBoundingClientRect().top` — const, line 255
- `const below = belowRef.current?.offsetHeight ?? 0` — const, line 256
- `const keybar = (document.querySelector(".keybar") as HTMLElement | null)?.offsetHeight ?? 36` — const, line 257
- `const next = Math.max(140, Math.floor(window.innerHeight - top - below - keybar - 28))` — const, line 258
- `const flushDraft = useCallback(async ()` — const, line 273
- `let cancelled = false` — let, line 289
- `const recoverOrLoad = async ()` — const, line 298
- `const retryKey = restoredSubmissionId?.trim()` — const, line 299
- `const recovery = await api.recoverPracticeSubmission(` — const, line 302
- `const recoveredItem = await api.getPracticeItem(practiceItemId).catch(()` — const, line 312
- `const routed = await routeAfterAttempt( recovery.result, recoveredItem, ()` — const, line 317
- `const recovery = committedAttemptRecovery(error)` — const, line 334
- `const timer = setTimeout(()` — const, line 377
- `const appWindow = getCurrentWindow()` — const, line 396
- `let unlisten: (()` — let, line 397
- `let closing = false` — let, line 398
- `const practiceReady = item !== null && probeLoadState === "ready"` — const, line 416
- `const probeActive = Boolean(probe?.active && probe.presentationId)` — const, line 417
- `const interactionReady = practiceReady && committedRecovery === null` — const, line 418
- `const onKey = (event: KeyboardEvent)` — const, line 426
- `const ctrl = event.ctrlKey || event.metaKey` — const, line 442
- `const onResize = ()` — const, line 485
- `const observer = new ResizeObserver(()` — const, line 487
- `const scorePreview = useMemo(()` — const, line 495
- `let score = Math.round(Object.values(selfGrade.criterionPoints).reduce((sum, value)` — let, line 497
- `const fatal = item.rubric.fatalErrors.find((candidate)` — const, line 500
- `function revealHint()` — function, line 506
- `async function stopDiagnosing()` — function, line 516
- `async function routeAfterAttempt( result: AttemptResultDto, recoveredItem: PracticeItemDetail | null = item, cancelled: ()` — function, line 529
- `const learningObjectId = recoveredItem?.learningObjectId ?? result.learningObjectId` — const, line 535
- `const learningObjectTitle = recoveredItem?.learningObjectTitle ?? result.learningObjectId` — const, line 536
- `const next = await api.getNextProbeItem(learningObjectId)` — const, line 548
- `async function submit()` — function, line 567
- `const submittedItemId = item.id` — const, line 569
- `const submittedKey = submissionId.current` — const, line 570
- `const validation = validateSelfGrade(item, selfGrade, fallbackRequired)` — const, line 577
- `const result = await api.submitAttempt(` — const, line 587
- `const routed = await routeAfterAttempt(result, item, ()` — const, line 620
- `const recovery = committedAttemptRecovery(error)` — const, line 623
- `const command = getCommandError(error)` — const, line 632
- `async function dontKnow()` — function, line 645
- `const submittedItemId = item.id` — const, line 647
- `const submittedKey = submissionId.current` — const, line 648
- `const result = await api.submitDontKnow(` — const, line 653
- `const routed = await routeAfterAttempt(result, item, ()` — const, line 665
- `const recovery = committedAttemptRecovery(error)` — const, line 668
- `async function skip()` — function, line 679
- `const skippedIdentity =` — const, line 681
- `async function acknowledgeCheckpoint(practiceItemId: string, expectedSubmissionId: string): Promise<boolean>` — function, line 695
- `const result = await api.acknowledgePracticeSubmission(` — const, line 697
- `const loadError = itemLoadError ?? probeLoadError` — const, line 711
- `const diagnostic = committedRecovery.attemptType === "diagnostic_probe" || probeActive` — const, line 713
- `const on = answerConfidence === level` — const, line 1000
- `const locked = submitting || selfGradeVisible` — const, line 1001
- `function TeachBackConversation(` — function, line 1112
- `const startedRef = useRef(false)` — const, line 1137
- `const transcriptRef = useRef<HTMLDivElement | null>(null)` — const, line 1138
- `const lastRole = turns.length > 0 ? turns[turns.length - 1].role : null` — const, line 1140
- `const needsText = turns.length === 0 || lastRole === "ai"` — const, line 1144
- `const start = useCallback(()` — const, line 1146
- `const node = transcriptRef.current` — const, line 1176
- `async function send(finish = false)` — function, line 1180
- `const text = input.trim()` — const, line 1182
- `const result = await api.submitTeachBackTurn(` — const, line 1188
- `const onKey = (event: KeyboardEvent)` — const, line 1213
- `const submitLabel = turns.length === 0 ? "Start teaching" : lastRole === "learner" ? "Continue" : "Send answer"` — const, line 1223
- `const questionsAnswered = asked > 0 && lastRole === "learner"` — const, line 1225
- `function SelfGradePanel(` — function, line 1340
- `const awarded = value.criterionPoints[criterion.id] ?? 0` — const, line 1361
- `const docked = awarded < criterion.points` — const, line 1362
- `const points = Number(event.target.value)` — const, line 1375
- `const stillDocked = points < criterion.points` — const, line 1376
- `function CriterionErrorPicker(` — function, line 1440
- `const selected = new Set( (value.errorAttributions ?? []).filter((a)` — const, line 1451
- `const toggle = (errorType: string)` — const, line 1454
- `const list = value.errorAttributions ?? []` — const, line 1455
- `const exists = list.some((a)` — const, line 1456
- `const relevant = candidates.filter((c)` — const, line 1464
- `const others = candidates.filter((c)` — const, line 1465
- `const chip = (c: CandidateErrorTypeDto)` — const, line 1466
- `function prunedAttributions(item: PracticeItemDetail, grade: SelfGradeInputDto): SelfGradeErrorAttributionDto[]` — function, line 1503
- `const docked = new Set( (item.rubric?.criteria ?? []) .filter((criterion)` — const, line 1504
- `const NON_RECORDING_ATTEMPT_TYPES: ReadonlySet<AttemptType> = new Set(["guided_walkthrough", "skip"])` — const, line 1515
- `function defaultAttemptType(allowed: readonly AttemptType[]): AttemptType` — function, line 1517
- `function composeRedoAnswer(prefix: string, redoText: string): string` — function, line 1530
- `const suffix = redoText.replace(/^[ \t]+/, "")` — const, line 1531
- `function chooseAttemptType(allowed: readonly AttemptType[], hintsUsed: number): AttemptType` — function, line 1539
- `const allows = (type: AttemptType)` — const, line 1540
- `function validateSelfGrade( item: PracticeItemDetail, value: SelfGradeInputDto, required: boolean ): Record<string, string>` — function, line 1545
- `const errors: Record<string, string> =` — const, line 1551
- `const points = value.criterionPoints[criterion.id]` — const, line 1553

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `PracticeScreen`; references `PracticeScreen`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AttemptResultDto`, `AttemptType`, `CandidateErrorTypeDto`, `GuidedRedoDto`, `PracticeItemDetail`, `ProbeBlockEndDto`, `ProbeContractDto`, `RubricCriterionDto`, `SelfGradeErrorAttributionDto`, `SelfGradeInputDto`, `SessionSnapshot`, `TeachBackStateDto`, `TeachBackTurnDto`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `masteryTone`
- [[Reference/Desktop/TypeScript/app/keyboard|src/app/keyboard.ts]] — import-or-re-export; imports `isTypingTarget`
- [[Reference/Desktop/TypeScript/components/CardControls|src/components/CardControls.tsx]] — import-or-re-export; imports `CardControls`
- [[Reference/Desktop/TypeScript/components/ItemPresentation|src/components/ItemPresentation.tsx]] — import-or-re-export; imports `ItemPresentation`
- [[Reference/Desktop/TypeScript/components/term|src/components/term.tsx]] — import-or-re-export; imports `BlockBar`, `COLOR`, `FONT_MONO`, `Faint`, `TermSelect`, `modePillColor`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `Card`, `EntityLink`, `KeyBar`, `Pill`, `SectionHeader`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/render/MarkdownMath|src/render/MarkdownMath.tsx]] — import-or-re-export; imports `MarkdownMath`
- [[Reference/Desktop/TypeScript/render/MathLiveEditor|src/render/MathLiveEditor.tsx]] — import-or-re-export; imports `MathLiveEditor`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `@tauri-apps/api/window`, `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Start a Learning Cycle#Desktop|desktop learning cycle]] — shows the user-facing session path.
- [[Concepts/Learning System#One attempt|one-attempt model]] — owns learning semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [tests/test_e2e_tui.py](../../../../../../tests/test_e2e_tui.py) — cross-boundary name contract: references uniquely owned exported name `PracticeScreen`; it does **not** directly execute this source module.
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — cross-boundary name contract: references uniquely owned exported name `PracticeScreen`; it does **not** directly execute this source module.
- [tests/test_tui_practice.py](../../../../../../tests/test_tui_practice.py) — cross-boundary name contract: references uniquely owned exported name `PracticeScreen`; it does **not** directly execute this source module.
- [tests/test_tui_today.py](../../../../../../tests/test_tui_today.py) — cross-boundary name contract: references uniquely owned exported name `PracticeScreen`; it does **not** directly execute this source module.
- [tests/test_large_practice_flow.py](../../../../../../tests/test_large_practice_flow.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_practice_information.py](../../../../../../tests/test_practice_information.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_diagnostic.py](../../../../../../tests/test_sidecar_diagnostic.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/PracticeScreen.tsx](../../../../../../apps/learnloop-tauri/src/screens/PracticeScreen.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
