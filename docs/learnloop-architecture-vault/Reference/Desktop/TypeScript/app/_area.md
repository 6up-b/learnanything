---
title: "Desktop area · TypeScript/app"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/app"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/app

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/app](../../../../../../apps/learnloop-tauri/src/app)

## Responsibility

Desktop shell orchestration, keyboard policy, configuration helpers, and recent-vault state.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

No nested ownership area.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/app/App|App.tsx]] | `ACTIVE` | Owns desktop navigation and cross-screen state, connecting startup, sessions, overlays, vault refresh, and route handoffs. | 80 | 1 |
| [[Reference/Desktop/TypeScript/app/ScreenErrorBoundary|ScreenErrorBoundary.tsx]] | `ACTIVE` | Provides `ScreenErrorBoundary` within the desktop's TypeScript/app ownership area. | 1 | 1 |
| [[Reference/Desktop/TypeScript/app/ShellChromeRoot|ShellChromeRoot.tsx]] | `ACTIVE` | Provides `SHELL_CHROME_ATTRIBUTE`, `inShellChrome`, `ShellChromeRoot` within the desktop's TypeScript/app ownership area. | 1 | 1 |
| [[Reference/Desktop/TypeScript/app/algoConfig|algoConfig.ts]] | `ACTIVE` | Normalizes and exposes algorithm configuration values needed by presentation code. | 0 | 28 |
| [[Reference/Desktop/TypeScript/app/autoAdvance|autoAdvance.ts]] | `ACTIVE` | Provides `todayQueueInput`, `todayQueueKey`, `queueHead`, `NextQueueItem` and related exports within the desktop's TypeScript/app ownership area. | 5 | 4 |
| [[Reference/Desktop/TypeScript/app/dailyPlan|dailyPlan.ts]] | `ACTIVE` | Provides `aboutMinutes`, `minutesPerDay`, `wholeMinutes`, `dailyPlanKey` and related exports within the desktop's TypeScript/app ownership area. | 6 | 11 |
| [[Reference/Desktop/TypeScript/app/intentCheck|intentCheck.ts]] | `ACTIVE` | Provides `readerTargetForRestoration` within the desktop's TypeScript/app ownership area. | 1 | 1 |
| [[Reference/Desktop/TypeScript/app/keyScope|keyScope.ts]] | `ACTIVE` | Provides `keyScope` within the desktop's TypeScript/app ownership area. | 1 | 3 |
| [[Reference/Desktop/TypeScript/app/keyboard|keyboard.ts]] | `ACTIVE` | Centralizes keyboard-target and shortcut guards shared by desktop interactions. | 0 | 4 |
| [[Reference/Desktop/TypeScript/app/keymap|keymap.ts]] | `ACTIVE` | Provides `KeyAction`, `KeyBinding`, `ADD_FILES_CHORD`, `shellBindings` and related exports within the desktop's TypeScript/app ownership area. | 3 | 46 |
| [[Reference/Desktop/TypeScript/app/notices|notices.ts]] | `ACTIVE` | Provides `NEEDS_SESSION`, `noticeAfterSessionBegins`, `NoticeCondition`, `ShellNotice` and related exports within the desktop's TypeScript/app ownership area. | 1 | 2 |
| [[Reference/Desktop/TypeScript/app/planFallback|planFallback.ts]] | `ACTIVE` | Provides `PlanFallbackOffer`, `extractFallbackOffer`, `noteFallbackOffer`, `currentFallbackOffer` and related exports within the desktop's TypeScript/app ownership area. | 0 | 2 |
| [[Reference/Desktop/TypeScript/app/practiceDraft|practiceDraft.ts]] | `ACTIVE` | Provides `PracticeDraftMirror`, `RestoredPracticeDraft`, `restoredPracticeDraft` within the desktop's TypeScript/app ownership area. | 1 | 1 |
| [[Reference/Desktop/TypeScript/app/practiceFeedback|practiceFeedback.ts]] | `ACTIVE` | Provides `simplePracticeFeedback`, `Verdict`, `VERDICT_TEXT`, `verdictOf` and related exports within the desktop's TypeScript/app ownership area. | 1 | 8 |
| [[Reference/Desktop/TypeScript/app/practiceOffer|practiceOffer.ts]] | `ACTIVE` | Provides `ProposalOrigin`, `PracticeOffer`, `schedulerCandidateForServe`, `planPresentationForServe` and related exports within the desktop's TypeScript/app ownership area. | 0 | 3 |
| [[Reference/Desktop/TypeScript/app/readerCheck|readerCheck.ts]] | `ACTIVE` | Provides `ReaderReturn`, `returnsToReader`, `keepReaderReturn`, `readerCheckOffer` within the desktop's TypeScript/app ownership area. | 3 | 2 |
| [[Reference/Desktop/TypeScript/app/readerWorkbench|readerWorkbench.ts]] | `ACTIVE` | Provides `ReaderWorkbenchOrigin`, `workbenchReturn`, `readerTargetBack`, `sessionAfterWorkbenchSubmit` and related exports within the desktop's TypeScript/app ownership area. | 5 | 1 |
| [[Reference/Desktop/TypeScript/app/recentVaults|recentVaults.ts]] | `ACTIVE` | Persists and normalizes the renderer's recent-vault list. | 0 | 3 |
| [[Reference/Desktop/TypeScript/app/sessionHandoff|sessionHandoff.ts]] | `ACTIVE` | Provides `ElsewhereChoice`, `ElsewhereQuestion`, `useElsewhereQuestion`, `adoptMovedSession` and related exports within the desktop's TypeScript/app ownership area. | 4 | 4 |
| [[Reference/Desktop/TypeScript/app/sessionMoved|sessionMoved.ts]] | `ACTIVE` | Provides `SessionMoved`, `sessionMovedFrom`, `setSessionMoved`, `useSessionMoved` and related exports within the desktop's TypeScript/app ownership area. | 1 | 5 |
| [[Reference/Desktop/TypeScript/app/shell|shell.ts]] | `ACTIVE` | Provides `ShellMode`, `shellMode`, `simpleShell`, `Place` and related exports within the desktop's TypeScript/app ownership area. | 2 | 11 |
| [[Reference/Desktop/TypeScript/app/todayPlan|todayPlan.ts]] | `ACTIVE` | Provides `dayPhrase`, `TodayRow`, `onYourOwnItem`, `todayRows` and related exports within the desktop's TypeScript/app ownership area. | 3 | 2 |
| [[Reference/Desktop/TypeScript/app/useCloseWithFlush|useCloseWithFlush.ts]] | `ACTIVE` | Provides `CLOSE_HELD_NOTE`, `useCloseWithFlush` within the desktop's TypeScript/app ownership area. | 1 | 2 |
| [[Reference/Desktop/TypeScript/app/useGlobalAdd|useGlobalAdd.ts]] | `ACTIVE` | Provides `looksLikeSource`, `useGlobalAdd` within the desktop's TypeScript/app ownership area. | 2 | 1 |
| [[Reference/Desktop/TypeScript/app/useQueueRevisionPoll|useQueueRevisionPoll.ts]] | `ACTIVE` | Provides `REVISION_POLL_MS`, `RevisionPollView`, `revisionPollHeld`, `QueueRevisionPollOptions` and related exports within the desktop's TypeScript/app ownership area. | 4 | 1 |
| [[Reference/Desktop/TypeScript/app/vaultTransition|vaultTransition.ts]] | `ACTIVE` | Provides `registerVaultDraft`, `selectWithDraftFlush` within the desktop's TypeScript/app ownership area. | 0 | 3 |
| [[Reference/Desktop/TypeScript/app/wrapUpOffer|wrapUpOffer.ts]] | `ACTIVE` | Provides `WrapUpLanding`, `wrapUpOfferArmed` within the desktop's TypeScript/app ownership area. | 0 | 1 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]
