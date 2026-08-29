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
| Source lines | 1122 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/app/_area|TypeScript/app]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]]

## Public API

- `export function App()` — function, line 63

## Internal implementation anchors

- `type OpenSourceTarget =` — type, line 42
- `type TodayStage = "queue" | "practice" | "feedback" | "blockReview"` — type, line 50
- `type VaultFilesChangedEvent =` — type, line 52
- `const onPracticeDraft = useCallback( (draft:` — const, line 144
- `const startupStartedRef = useRef(false)` — const, line 163
- `const teachBackActiveRef = useRef(false)` — const, line 167
- `const practiceAskAllowedRef = useRef(false)` — const, line 171
- `const onTeachBackActive = useCallback((active: boolean)` — const, line 172
- `const onPracticeAskAllowed = useCallback((allowed: boolean)` — const, line 175
- `const onError = useCallback((message: string)` — const, line 179
- `const onPaletteEntities = useCallback((ids:` — const, line 180
- `const loadInitialVault = useCallback(async ()` — const, line 185
- `const appSnapshot = await api.loadVault()` — const, line 188
- `const checkpoint = appSnapshot.activeSession.checkpoint` — const, line 193
- `let disposed = false` — let, line 212
- `let unlisten: (()` — let, line 213
- `const next = payload.refresh.snapshot` — const, line 221
- `const practiceItemCount = payload.refresh.practiceItemCount` — const, line 231
- `const vaultRoot = snapshot?.vault?.root ?? null` — const, line 265
- `let disposed = false` — let, line 271
- `const refresh = ()` — const, line 272
- `const unsubscribe = subscribeQueueChanged(refresh)` — const, line 283
- `const navBadges = useMemo<NavBadgeCounts>( ()` — const, line 290
- `const root = snapshot?.vault?.root` — const, line 306
- `const onKey = (event: KeyboardEvent)` — const, line 311
- `const textTarget = isTypingTarget(event.target)` — const, line 312
- `const next = navTabs.find((candidate)` — const, line 330
- `const restored = useMemo(()` — const, line 341
- `const checkpoint = session?.checkpoint` — const, line 350
- `const subjectOptions = useMemo( ()` — const, line 361
- `const manualGrading = snapshot?.health.ai?.manualGrading ?? false` — const, line 365
- `const gradingReady = (snapshot?.health.ai?.ready ?? snapshot?.health.codex.ready ?? false) && !manualGrading` — const, line 368
- `const gradingProvider = snapshot?.health.ai?.activeProvider ?? "codex"` — const, line 369
- `const settingsHealthy = manualGrading || (snapshot?.health.ai?.settingsReady ?? snapshot?.health.ai?.ready ?? snapshot?.health.codex.ready ?? false)` — const, line 374
- `const applyHealth = useCallback((health: RuntimeHealth)` — const, line 381
- `const changeGradingProvider = useCallback( async (provider: string)` — const, line 385
- `const result = await api.setGradingProvider(provider)` — const, line 388
- `function beginSession(next: SessionSnapshot)` — function, line 414
- `function openPractice(id: string)` — function, line 440
- `function openPrimedRetry(id: string)` — function, line 454
- `function openGuidedRedo(redo: GuidedRedoDto)` — function, line 470
- `function openFeedback(id: string)` — function, line 487
- `function openBlockReview(blockEnd: ProbeBlockEndDto, learningObjectId: string, learningObjectTitle: string)` — function, line 494
- `function openLibraryFile(path: string)` — function, line 500
- `function clearLocalCheckpoint(identity?:` — function, line 505
- `const checkpoint = current.checkpoint` — const, line 509
- `function endSession(summary: SessionEndSummary)` — function, line 528
- `function gotoTab(next: TopTab)` — function, line 545
- `function openRepair(misconceptionId: string)` — function, line 567
- `function openExam(goalId: string)` — function, line 572
- `function exitExam()` — function, line 577
- `function openCalibration(id: string)` — function, line 584
- `function exitCalibration()` — function, line 591
- `const askCurrentContext = useCallback((): boolean` — const, line 600
- `function gotoLibraryProposal(patchId: string, itemId: string)` — function, line 630
- `function gotoProposalBatch(patchId: string)` — function, line 635
- `const changeVault = useCallback( async (path: string)` — const, line 640
- `let selected = false` — let, line 642
- `const next = await api.loadVault()` — const, line 664
- `const message = errorMessage(error, "Could not open that vault.")` — const, line 684
- `function renderBody()` — function, line 702
- `const practicing = tab === "today" && (todayStage === "practice" || todayStage === "feedback")` — const, line 742
- `function unique(values: Array<string | null>): string[]` — function, line 1120

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/main|src/main.tsx]] — import-or-re-export: `App`; references `App`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/client|src/api/client.ts]] — import-or-re-export; imports `api`
- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `AppSnapshot`, `GuidedRedoDto`, `ProbeBlockEndDto`, `ReviewCountsDto`, `RuntimeHealth`, `SessionEndSummary`, `SessionSnapshot`, `TriageResultDto`
- [[Reference/Desktop/TypeScript/app/algoConfig|src/app/algoConfig.ts]] — import-or-re-export; imports `setAlgoConfig`
- [[Reference/Desktop/TypeScript/app/keyboard|src/app/keyboard.ts]] — import-or-re-export; imports `isTypingTarget`
- [[Reference/Desktop/TypeScript/app/recentVaults|src/app/recentVaults.ts]] — import-or-re-export; imports `recordRecentVault`, `removeRecentVault`
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
- [[Reference/Desktop/TypeScript/components/ui|src/components/ui.tsx]] — import-or-re-export; imports `EmptyPlaceholder`, `NavBadgeCounts`, `SHOW_GOLDEN_PATH`, `TerminalFrame`, `TopTab`, `navTabs`
- [[Reference/Desktop/TypeScript/errors|src/errors.ts]] — import-or-re-export; imports `errorMessage`
- [[Reference/Desktop/TypeScript/queueEvents|src/queueEvents.ts]] — import-or-re-export; imports `notifyQueueChanged`, `subscribeQueueChanged`
- [[Reference/Desktop/TypeScript/screens/CalibrationScreen|src/screens/CalibrationScreen.tsx]] — import-or-re-export; imports `CalibrationScreen`
- [[Reference/Desktop/TypeScript/screens/DiagnosticReviewScreen|src/screens/DiagnosticReviewScreen.tsx]] — import-or-re-export; imports `DiagnosticReviewScreen`
- [[Reference/Desktop/TypeScript/screens/ExamScreen|src/screens/ExamScreen.tsx]] — import-or-re-export; imports `ExamScreen`
- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export; imports `FeedbackScreen`
- [[Reference/Desktop/TypeScript/screens/GoldenPathScreen|src/screens/GoldenPathScreen.tsx]] — import-or-re-export; imports `GoldenPathScreen`
- [[Reference/Desktop/TypeScript/screens/GraphScreen|src/screens/GraphScreen.tsx]] — import-or-re-export; imports `GraphScreen`
- [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] — import-or-re-export; imports `IngestScreen`
- [[Reference/Desktop/TypeScript/screens/LibraryScreen|src/screens/LibraryScreen.tsx]] — import-or-re-export; imports `LibraryScreen`
- [[Reference/Desktop/TypeScript/screens/MaintenanceScreen|src/screens/MaintenanceScreen.tsx]] — import-or-re-export; imports `MaintenanceScreen`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export; imports `PracticeScreen`
- [[Reference/Desktop/TypeScript/screens/ProposalsScreen|src/screens/ProposalsScreen.tsx]] — import-or-re-export; imports `ProposalsScreen`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export; imports `ReaderScreen`
- [[Reference/Desktop/TypeScript/screens/RegistryReviewScreen|src/screens/RegistryReviewScreen.tsx]] — import-or-re-export; imports `RegistryReviewScreen`
- [[Reference/Desktop/TypeScript/screens/RepairScreen|src/screens/RepairScreen.tsx]] — import-or-re-export; imports `RepairScreen`
- [[Reference/Desktop/TypeScript/screens/ReviewScreen|src/screens/ReviewScreen.tsx]] — import-or-re-export; imports `ReviewScreen`
- [[Reference/Desktop/TypeScript/screens/SettingsScreen|src/screens/SettingsScreen.tsx]] — import-or-re-export; imports `SettingsOverlay`
- [[Reference/Desktop/TypeScript/screens/StartScreen|src/screens/StartScreen.tsx]] — import-or-re-export; imports `StartScreen`
- [[Reference/Desktop/TypeScript/screens/TodayScreen|src/screens/TodayScreen.tsx]] — import-or-re-export; imports `TodayScreen`

### Assets, platform, and third-party dependencies

- Imported packages/crates: `@tauri-apps/api/event`, `react`

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Architecture/Architecture Overview#Runtime composition|runtime composition]] — shows this entry point in the whole process graph.
- [[Workflows/Initialize a Vault|Initialize a Vault]] — owns first-run behavior.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- No repository test directly names this source path or a uniquely owned export. `npm run typecheck` and `npm run frontend:build` are the executable frontend gates; add a focused test when changing behavior.

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/app/App.tsx](../../../../../../apps/learnloop-tauri/src/app/App.tsx) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
