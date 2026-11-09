---
title: "Desktop module · src/errors.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.errors"
language: "TypeScript"
area: "TypeScript"
source_path: "apps/learnloop-tauri/src/errors.ts"
source_paths:
  - "apps/learnloop-tauri/src/errors.ts"
source_commit: "9ed381bc3787439c88ffe3ec08b319b51049fa02"
source_commit_timestamp: "2026-11-01T03:48:43-05:00"
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

# `src/errors.ts`

Area: [[Reference/Desktop/TypeScript/_area|TypeScript]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Turns unknown renderer failures into the user-facing desktop error contract.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/errors.ts](../../../../../apps/learnloop-tauri/src/errors.ts) |
| Source lines | 89 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/_area|TypeScript]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `9ed381bc3787439c88ffe3ec08b319b51049fa02` |
| Commit timestamp | `2026-11-01T03:48:43-05:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/errors|src/errors.ts]]

## Public API

- `export type MessageKind = "error" | "notice"` — type, line 8
- `export interface RetryRan` — interface, line 27
- `export const RETRY_RAN: RetryRan = Object.freeze(` — const, line 32
- `export type NoticeRetry = ()` — type, line 34
- `export function retryRan(value: unknown): value is RetryRan` — function, line 36
- `export type ErrorReport = |` — type, line 40
- `export type ReportError = (message: string, report?: ErrorReport)` — type, line 45
- `export function getCommandError(error: unknown): CommandError | null` — function, line 53
- `export const SPAN_MISMATCH_CODE = "span_extraction_mismatch"` — const, line 68
- `export const SPAN_MISMATCH_COPY = "That passage belongs to another reading` — const, line 69
- `export function isSpanMismatch(error: unknown): boolean` — function, line 72
- `export function errorMessage(error: unknown, fallback = DEFAULT_ERROR_MESSAGE): string` — function, line 77

## Internal implementation anchors

- `const DEFAULT_ERROR_MESSAGE = "Something went wrong. Please try again."` — const, line 3
- `const candidate = error as Partial<CommandError>` — const, line 55
- `const command = getCommandError(error)` — const, line 78
- `const message = (error as` — const, line 85

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/api/queryCache|src/api/queryCache.ts]] — import-or-re-export: `errorMessage`, `getCommandError`; references `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/api/useCachedQuery|src/api/useCachedQuery.ts]] — import-or-re-export: `ErrorReport`, `NoticeRetry`, `RETRY_RAN`; references `ErrorReport`, `NoticeRetry`, `RETRY_RAN`
- [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] — import-or-re-export: `ErrorReport`, `NoticeRetry`, `RETRY_RAN`, `errorMessage`, `getCommandError`; references `ErrorReport`, `NoticeRetry`, `RETRY_RAN`, `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/app/ScreenErrorBoundary|src/app/ScreenErrorBoundary.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/app/notices|src/app/notices.ts]] — import-or-re-export: `MessageKind`, `NoticeRetry`, `errorMessage`, `getCommandError`, `retryRan`; references `MessageKind`, `NoticeRetry`, `errorMessage`, `getCommandError`, `retryRan`
- [[Reference/Desktop/TypeScript/app/sessionHandoff|src/app/sessionHandoff.ts]] — import-or-re-export: `getCommandError`; references `getCommandError`
- [[Reference/Desktop/TypeScript/app/useCloseWithFlush|src/app/useCloseWithFlush.ts]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/components/AdjudicationOverlay|src/components/AdjudicationOverlay.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/components/AsPrinted|src/components/AsPrinted.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/components/CapturePhoto|src/components/CapturePhoto.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/components/ChatGPTPlanSettings|src/components/ChatGPTPlanSettings.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/components/InboxStrip|src/components/InboxStrip.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/components/NativeMediaSettings|src/components/NativeMediaSettings.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/components/NewVaultWizard|src/components/NewVaultWizard.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/components/QuickAddDialog|src/components/QuickAddDialog.tsx]] — import-or-re-export: `errorMessage`, `getCommandError`; references `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/components/askFigures|src/components/askFigures.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/components/askPanel|src/components/askPanel.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/components/goldenpath/GoldenPathSetup|src/components/goldenpath/GoldenPathSetup.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/fixtures/retryRequests|src/fixtures/retryRequests.ts]] — import-or-re-export: `RETRY_RAN`; references `RETRY_RAN`
- [[Reference/Desktop/TypeScript/screens/FeedbackScreen|src/screens/FeedbackScreen.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/GoldenPathScreen|src/screens/GoldenPathScreen.tsx]] — import-or-re-export: `errorMessage`, `getCommandError`; references `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/screens/IngestScreen|src/screens/IngestScreen.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/KnowledgeMapScreen|src/screens/KnowledgeMapScreen.tsx]] — import-or-re-export: `ReportError`; references `ReportError`
- [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] — import-or-re-export: `getCommandError`; references `getCommandError`
- [[Reference/Desktop/TypeScript/screens/LibraryScreen|src/screens/LibraryScreen.tsx]] — import-or-re-export: `ReportError`; references `ReportError`
- [[Reference/Desktop/TypeScript/screens/MaintenanceScreen|src/screens/MaintenanceScreen.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/PracticeScreen|src/screens/PracticeScreen.tsx]] — import-or-re-export: `errorMessage`, `getCommandError`; references `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/screens/ReaderScreen|src/screens/ReaderScreen.tsx]] — import-or-re-export: `SPAN_MISMATCH_COPY`, `errorMessage`; references `SPAN_MISMATCH_COPY`, `errorMessage`
- [[Reference/Desktop/TypeScript/screens/feedback/CompareMethods|src/screens/feedback/CompareMethods.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/practice/HelpStyleSettings|src/screens/practice/HelpStyleSettings.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/practice/useAdaptiveHints|src/screens/practice/useAdaptiveHints.ts]] — import-or-re-export: `errorMessage`, `getCommandError`; references `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/screens/reader/AlsoInBooks|src/screens/reader/AlsoInBooks.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/CompareKeep|src/screens/reader/CompareKeep.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/ComparePointTable|src/screens/reader/ComparePointTable.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/DeliverableScope|src/screens/reader/DeliverableScope.tsx]] — import-or-re-export: `errorMessage`, `getCommandError`; references `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/screens/reader/DeliverableSliceCard|src/screens/reader/DeliverableSliceCard.tsx]] — import-or-re-export: `errorMessage`, `getCommandError`; references `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/screens/reader/FindSection|src/screens/reader/FindSection.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/GuideRail|src/screens/reader/GuideRail.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/HiddenNotesSettings|src/screens/reader/HiddenNotesSettings.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/ModelActionState|src/screens/reader/ModelActionState.tsx]] — import-or-re-export: `getCommandError`; references `getCommandError`
- [[Reference/Desktop/TypeScript/screens/reader/NotesGapsSettings|src/screens/reader/NotesGapsSettings.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/PreparingView|src/screens/reader/PreparingView.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderCorrespondenceSettings|src/screens/reader/ReaderCorrespondenceSettings.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderCueSettings|src/screens/reader/ReaderCueSettings.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/ReaderNotes|src/screens/reader/ReaderNotes.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/ReadingPathCard|src/screens/reader/ReadingPathCard.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/ScopeFromPassage|src/screens/reader/ScopeFromPassage.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/SideBySidePane|src/screens/reader/SideBySidePane.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/WrapUpOffer|src/screens/reader/WrapUpOffer.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/figures/useFigures|src/screens/reader/figures/useFigures.ts]] — import-or-re-export: `errorMessage`, `getCommandError`; references `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/screens/reader/useActiveReading|src/screens/reader/useActiveReading.ts]] — import-or-re-export: `errorMessage`, `getCommandError`; references `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/screens/reader/useLibraryAsk|src/screens/reader/useLibraryAsk.ts]] — import-or-re-export: `errorMessage`, `getCommandError`; references `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderCues|src/screens/reader/useReaderCues.ts]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|src/screens/reader/useReaderInquiry.ts]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderRecap|src/screens/reader/useReaderRecap.ts]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderRequests|src/screens/reader/useReaderRequests.ts]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/useReaderWorkbench|src/screens/reader/useReaderWorkbench.ts]] — import-or-re-export: `SPAN_MISMATCH_COPY`, `errorMessage`; references `SPAN_MISMATCH_COPY`, `errorMessage`
- [[Reference/Desktop/TypeScript/screens/reader/useSideBySide|src/screens/reader/useSideBySide.ts]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/today/ContinueLessonCard|src/screens/today/ContinueLessonCard.tsx]] — import-or-re-export: `getCommandError`; references `getCommandError`
- [[Reference/Desktop/TypeScript/screens/today/LessonOfferBlock|src/screens/today/LessonOfferBlock.tsx]] — import-or-re-export: `getCommandError`; references `getCommandError`
- [[Reference/Desktop/TypeScript/screens/today/LessonSuggestionCard|src/screens/today/LessonSuggestionCard.tsx]] — import-or-re-export: `getCommandError`; references `getCommandError`
- [[Reference/Desktop/TypeScript/screens/today/SomethingElse|src/screens/today/SomethingElse.tsx]] — import-or-re-export: `getCommandError`; references `getCommandError`
- [[Reference/Desktop/TypeScript/screens/today/TodayPlace|src/screens/today/TodayPlace.tsx]] — import-or-re-export: `ErrorReport`, `errorMessage`; references `ErrorReport`, `errorMessage`
- [[Reference/Desktop/TypeScript/screens/underhood/tools|src/screens/underhood/tools.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/workbench/RouteExample|src/screens/workbench/RouteExample.tsx]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/workbench/Workbench|src/screens/workbench/Workbench.tsx]] — import-or-re-export: `errorMessage`, `getCommandError`; references `errorMessage`, `getCommandError`
- [[Reference/Desktop/TypeScript/screens/workbench/useWorkbenchHelp|src/screens/workbench/useWorkbenchHelp.ts]] — import-or-re-export: `errorMessage`; references `errorMessage`
- [[Reference/Desktop/TypeScript/screens/workbench/useWorkbenchSession|src/screens/workbench/useWorkbenchSession.ts]] — import-or-re-export: `errorMessage`, `getCommandError`; references `errorMessage`, `getCommandError`

## Dependencies

### Desktop source modules

- [[Reference/Desktop/TypeScript/api/dto|src/api/dto.ts]] — import-or-re-export; imports `CommandError`

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/sideBySideIntent.test.tsx](../../../../../apps/learnloop-tauri/src/screens/reader/sideBySideIntent.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/screens/ReaderScreen.workbench.test.tsx](../../../../../apps/learnloop-tauri/src/screens/ReaderScreen.workbench.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/components/NoticeHost.test.tsx](../../../../../apps/learnloop-tauri/src/components/NoticeHost.test.tsx) — vitest test: imports and executes this module under jsdom (`npm test`).
- [apps/learnloop-tauri/src/app/notices.shell.test.ts](../../../../../apps/learnloop-tauri/src/app/notices.shell.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).

## Modification guidance

- Change this source at its stated ownership boundary, then check every inbound consumer and outbound dependency listed above.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/errors.ts](../../../../../apps/learnloop-tauri/src/errors.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
