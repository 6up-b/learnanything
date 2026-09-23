---
title: "Desktop module · src/app/App.tsx"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.app.App"
language: "TypeScript"
area: "TypeScript/app"
source_path: "apps/learnloop-tauri/src/app/App.tsx"
source_paths:
  - "apps/learnloop-tauri/src/app/App.tsx"
source_commit: "4ba2554f476133243a7ab95ac094a46fbd3c970c"
source_commit_timestamp: "2026-09-23T12:06:06-04:00"
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

# `src/app/App.tsx`

Area: [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Owns desktop navigation and cross-screen state, connecting startup, sessions, overlays, vault refresh, and route handoffs.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/app/App.tsx](../../../../../../apps/learnloop-tauri/src/app/App.tsx) |
| Source lines | 1184 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `4ba2554f476133243a7ab95ac094a46fbd3c970c` |
| Commit timestamp | `2026-09-23T12:06:06-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]]

## Public API

- `export function App()` — function, line 71

## Internal implementation anchors

- `type OpenSourceTarget =` — type, line 41
- `const ReaderScreen = lazy(()` — const, line 49
- `const GraphScreen = lazy(()` — const, line 50
- `const IngestScreen = lazy(()` — const, line 51
- `const ExamScreen = lazy(()` — const, line 52
- `const LibraryScreen = lazy(()` — const, line 53
- `const ProposalsScreen = lazy(()` — const, line 54
- `const RegistryReviewScreen = lazy(()` — const, line 55
- `const GoldenPathScreen = lazy(()` — const, line 56
- `type TodayStage = "queue" | "practice" | "feedback" | "blockReview"` — type, line 58
- `type VaultFilesChangedEvent =` — type, line 60
- `const onPracticeDraft = useCallback( (draft:` — const, line 156
- `const startupStartedRef = useRef(false)` — const, line 175
- `const teachBackActiveRef = useRef(false)` — const, line 179
- `const practiceAskAllowedRef = useRef(false)` — const, line 183
- `const onTeachBackActive = useCallback((active: boolean)` — const, line 184
- `const onPracticeAskAllowed = useCallback((allowed: boolean)` — const, line 187
- `const onError = useCallback((message: string)` — const, line 191
- `const onPaletteEntities = useCallback((ids:` — const, line 192
- `const loadInitialVault = useCallback(async ()` — const, line 197
- `const appSnapshot = await api.loadVault()` — const, line 200
- `const checkpoint = appSnapshot.activeSession.checkpoint` — const, line 205
- `let disposed = false` — let, line 224
- `let unlisten: (()` — let, line 225
- `let invalidateTimer: number | null = null` — let, line 230
- `const scheduleInvalidateAll = ()` — const, line 231
- `const next = payload.refresh.snapshot` — const, line 248
- `const practiceItemCount = payload.refresh.practiceItemCount` — const, line 258
- `const vaultRoot = snapshot?.vault?.root ?? null` — const, line 293
- `let disposed = false` — let, line 299
- `const refresh = ()` — const, line 300
- `const unsubscribe = subscribeQueueChanged(refresh)` — const, line 311
- `const navBadges = useMemo<NavBadgeCounts>( ()` — const, line 318
- `const root = snapshot?.vault?.root` — const, line 334
- `const onKey = (event: KeyboardEvent)` — const, line 339
- `const textTarget = isTypingTarget(event.target)` — const, line 340
- `const next = navTabs.find((candidate)` — const, line 358
- `const restored = useMemo(()` — const, line 369
- `const checkpoint = session?.checkpoint` — const, line 378
- `const subjectOptions = useMemo( ()` — const, line 389
- `const manualGrading = snapshot?.health.ai?.manualGrading ?? false` — const, line 393
- `const gradingReady = (snapshot?.health.ai?.ready ?? snapshot?.health.codex.ready ?? false) && !manualGrading` — const, line 396
- `const gradingProvider = snapshot?.health.ai?.activeProvider ?? "codex"` — const, line 397
- `const settingsHealthy = manualGrading || (snapshot?.health.ai?.settingsReady ?? snapshot?.health.ai?.ready ?? snapshot?.health.codex.ready ?? false)` — const, line 402
- `const applyHealth = useCallback((health: RuntimeHealth)` — const, line 409
- `const changeGradingProvider = useCallback( async (provider: string)` — const, line 413
- `const result = await api.setGradingProvider(provider)` — const, line 416
- `function beginSession(next: SessionSnapshot)` — function, line 442
- `function openPractice(id: string, schedulerCandidateId?: string | null)` — function, line 468
- `function openPrimedRetry(id: string)` — function, line 483
- `function openGuidedRedo(redo: GuidedRedoDto)` — function, line 500
- `function openFeedback(id: string)` — function, line 517
- `function openBlockReview(blockEnd: ProbeBlockEndDto, learningObjectId: string, learningObjectTitle: string)` — function, line 524
- `function openLibraryFile(path: string)` — function, line 530
- `function clearLocalCheckpoint(identity?:` — function, line 535
- `const checkpoint = current.checkpoint` — const, line 539
- `function endSession(summary: SessionEndSummary)` — function, line 558
- `function gotoTab(next: TopTab)` — function, line 576
- `function openRepair(misconceptionId: string)` — function, line 598
- `function openExam(goalId: string)` — function, line 603
- `function exitExam()` — function, line 608
- `function openCalibration(id: string)` — function, line 615
- `function exitCalibration()` — function, line 622
- `const askCurrentContext = useCallback((): boolean` — const, line 631
- `function gotoLibraryProposal(patchId: string, itemId: string)` — function, line 661
- `function gotoProposalBatch(patchId: string)` — function, line 666
- `function resetShellForVault()` — function, line 672
- `const changeVault = useCallback( async (path: string)` — const, line 705
- `let selected = false` — let, line 707
- `let selectionAttempted = false` — let, line 708
- `const next = await api.loadVault()` — const, line 731
- `const message = errorMessage(error, "Could not open that vault.")` — const, line 737
- `function renderBody()` — function, line 755
- `const practicing = tab === "today" && (todayStage === "practice" || todayStage === "feedback")` — const, line 795
- `function unique(values: Array<string | null>): string[]` — function, line 1182

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/main|src/main.tsx]] — import-or-re-export: `App`; references `App`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AppSnapshot`, `GuidedRedoDto`, `ProbeBlockEndDto`, `ReviewCountsDto`, `RuntimeHealth`, `SessionEndSummary`, `SessionSnapshot`, `TriageResultDto`
- [[Reference/Desktop/TypeScript/api/queryCache|src/api/queryCache.ts]] — import-or-re-export; imports `clearQueryCache`, `invalidateAllQueries`
- [[Reference/Desktop/TypeScript/app/ScreenErrorBoundary|src/app/ScreenErrorBoundary.tsx]] — import-or-re-export; imports `ScreenErrorBoundary`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `setAlgoConfig`
- [[Reference/Desktop/TypeScript/app/keyboard|src/app/keyboard.ts]] — import-or-re-export; imports `isTypingTarget`
- [[Reference/Desktop/TypeScript/app/practiceOffer|src/app/practiceOffer.ts]] — import-or-re-export; imports `PracticeOffer`, `schedulerCandidateForServe`
- [[Reference/Desktop/TypeScript/app/recentVaults|src/app/recentVaults.ts]] — import-or-re-export; imports `recordRecentVault`, `removeRecentVault`
- [[Reference/Desktop/TypeScript/app/vaultTransition|src/app/vaultTransition.ts]] — import-or-re-export; imports `selectWithDraftFlush`
- [[Reference/Desktop/TypeScript/components/AdjudicationOverlay|src/components/AdjudicationOverlay.tsx]] — import-or-re-export; imports `AdjudicationOverlay`
- [[Reference/Desktop/TypeScript/components/AskOverlay|src/components/AskOverlay.tsx]] — import-or-re-export; imports `AskOverlay`, `AskTarget`
- [[Reference/Desktop/TypeScript/components/CommandPalette|src/components/CommandPalette.tsx]] — import-or-re-export; imports `CommandPalette`
- [[Reference/Desktop/TypeScript/components/ExemplarConfirmDialog|src/components/ExemplarConfirmDialog.tsx]] — import-or-re-export; imports `ExemplarConfirmDialog`
- [[Reference/Desktop/TypeScript/components/InspectorOverlay|src/components/InspectorOverlay.tsx]] — import-or-re-export; imports `InspectorOverlay`
- [[Reference/Desktop/TypeScript/components/NewVaultWizard|src/components/NewVaultWizard.tsx]] — import-or-re-export; imports `NewVaultWizard`
- [[Reference/Desktop/TypeScript/components/OpenInSource|src/components/OpenInSource.tsx]] — import-or-re-export; imports `OpenInSource`
- [[Reference/Desktop/TypeScript/components/QuickAddDialog|src/components/QuickAddDialog.tsx]] — import-or-re-export; imports `QuickAddDialog`
- [[Reference/Desktop/TypeScript/components/SessionFinishHud|src/components/SessionFinishHud.tsx]] — import-or-re-export; imports `SessionFinishHud`
- [[Reference/Desktop/TypeScript/components/WhyDiagnosisOverlay|src/components/WhyDiagnosisOverlay.tsx]] — import-or-re-export; imports `WhyDiagnosisOverlay`
- [[Reference/Desktop/TypeScript/components/goldenpath/GoldenPathSetup|src/components/goldenpath/GoldenPathSetup.tsx]] — import-or-re-export; imports `GoldenPathSetup`
- [[Reference/Desktop/TypeScript/components/pdfDocumentCache|src/components/pdfDocumentCache.ts]] — import-or-re-export; imports `clearPdfDocuments`
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `EmptyPlaceholder`, `NavBadgeCounts`, `SHOW_GOLDEN_PATH`, `TerminalFrame`, `TopTab`, `navTabs`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/queueEvents|src/queueEvents.ts]] — import-or-re-export; imports `notifyQueueChanged`, `subscribeQueueChanged`
- [[Reference/Desktop/TypeScript/screens/CalibrationScreen|src/screens/CalibrationScreen.tsx]] — import-or-re-export; imports `CalibrationScreen`
- [[Reference/Desktop/TypeScript/screens/DiagnosticReviewScreen|src/screens/DiagnosticReviewScreen.tsx]] — import-or-re-export; imports `DiagnosticReviewScreen`
- [[Reference/Desktop/TypeScript/screens/ExamScreen|src/screens/ExamScreen.tsx]] — dynamic import
- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export; imports `FeedbackScreen`
- [[Reference/Desktop/TypeScript/screens/GoldenPathScreen|src/screens/GoldenPathScreen.tsx]] — dynamic import
- [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] — dynamic import
- [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] — dynamic import
- [[Reference/Desktop/TypeScript/screens/LibraryScreen|src/screens/LibraryScreen.tsx]] — dynamic import
- [[Reference/Desktop/TypeScript/screens/MaintenanceScreen|src/screens/MaintenanceScreen.tsx]] — import-or-re-export; imports `MaintenanceScreen`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export; imports `PracticeScreen`
- [[Reference/Desktop/TypeScript/screens/ProposalsScreen|src/screens/ProposalsScreen.tsx]] — dynamic import
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — dynamic import; imports `ReaderOpenSource`
- [[Reference/Desktop/TypeScript/screens/RegistryReviewScreen|src/screens/RegistryReviewScreen.tsx]] — dynamic import
- [[Reference/Desktop/TypeScript/screens/RepairScreen|src/screens/RepairScreen.tsx]] — import-or-re-export; imports `RepairScreen`
- [[Reference/Desktop/TypeScript/screens/ReviewScreen|src/screens/ReviewScreen.tsx]] — import-or-re-export; imports `ReviewScreen`
- [[Reference/Desktop/TypeScript/screens/SettingsScreen|src/screens/SettingsScreen.tsx]] — import-or-re-export; imports `SettingsOverlay`
- [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] — import-or-re-export; imports `StartScreen`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export; imports `TodayScreen`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `@tauri-apps/api/event`, `react`, `react-dom`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Architecture/Architecture Overview#Runtime composition|runtime composition]] — shows this entry point in the whole process graph.
- [[Workflows/Initialize a Vault|Initialize a Vault]] — owns first-run behavior.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck`, `npm test` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/App.tsx](../../../../../../apps/learnloop-tauri/src/app/App.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
