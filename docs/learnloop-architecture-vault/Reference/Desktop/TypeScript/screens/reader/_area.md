---
title: "Desktop area · TypeScript/screens/reader"
type: "desktop-area-map"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader"
source_commit: "d9e95c6025d25552c051f68259df62d893782389"
source_commit_timestamp: "2026-11-07T07:06:12-05:00"
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/moc"
  - "learnloop/desktop"
  - "learnloop/desktop/area"
---

# TypeScript/screens/reader

Parent: [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]] · Source: [apps/learnloop-tauri/src/screens/reader](../../../../../../../apps/learnloop-tauri/src/screens/reader)

## Responsibility

Reader request-state coordination extracted from the main reader screen.

> [!note] Ownership boundary
> This map inventories code organization. End-to-end behavior remains in the linked workflow and concept notes.

## Child areas

- [[Reference/Desktop/TypeScript/screens/reader/figures/_area|TypeScript/screens/reader/figures]] — Reader "show me" figures: the figure grammar and spec, inline figures, panels, predictions, and their state.

## Direct modules

| Module | Status | Purpose | Imports | Imported by |
|---|---|---|---:|---:|
| [[Reference/Desktop/TypeScript/screens/reader/ActiveReadingCard|ActiveReadingCard.tsx]] | `ACTIVE` | Implements the `ActiveReadingCard` routed desktop screen and coordinates its learner-facing workflow state. | 7 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/AlsoInBooks|AlsoInBooks.tsx]] | `ACTIVE` | Implements the `AlsoInBooks` routed desktop screen and coordinates its learner-facing workflow state. | 9 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/AskRail|AskRail.tsx]] | `ACTIVE` | Implements the `AskRail` routed desktop screen and coordinates its learner-facing workflow state. | 11 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/ComingUp|ComingUp.tsx]] | `ACTIVE` | Implements the `ComingUp` routed desktop screen and coordinates its learner-facing workflow state. | 3 | 2 |
| [[Reference/Desktop/TypeScript/screens/reader/CompareKeep|CompareKeep.tsx]] | `ACTIVE` | Implements the `CompareKeep` routed desktop screen and coordinates its learner-facing workflow state. | 8 | 5 |
| [[Reference/Desktop/TypeScript/screens/reader/ComparePointTable|ComparePointTable.tsx]] | `ACTIVE` | Implements the `ComparePointTable` routed desktop screen and coordinates its learner-facing workflow state. | 9 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/CompareScope|CompareScope.tsx]] | `ACTIVE` | Implements the `CompareScope` routed desktop screen and coordinates its learner-facing workflow state. | 7 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/DeliverableScope|DeliverableScope.tsx]] | `ACTIVE` | Implements the `DeliverableScope` routed desktop screen and coordinates its learner-facing workflow state. | 4 | 2 |
| [[Reference/Desktop/TypeScript/screens/reader/DeliverableSliceCard|DeliverableSliceCard.tsx]] | `ACTIVE` | Implements the `DeliverableSliceCard` routed desktop screen and coordinates its learner-facing workflow state. | 8 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/DetourStrip|DetourStrip.tsx]] | `ACTIVE` | Implements the `DetourStrip` routed desktop screen and coordinates its learner-facing workflow state. | 2 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/DigestNarrative|DigestNarrative.tsx]] | `ACTIVE` | Implements the `DigestNarrative` routed desktop screen and coordinates its learner-facing workflow state. | 4 | 3 |
| [[Reference/Desktop/TypeScript/screens/reader/DoseOffer|DoseOffer.tsx]] | `ACTIVE` | Implements the `DoseOffer` routed desktop screen and coordinates its learner-facing workflow state. | 4 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/ExerciseCandidates (tsx)|ExerciseCandidates.tsx]] | `ACTIVE` | Implements the `ExerciseCandidates` routed desktop screen and coordinates its learner-facing workflow state. | 5 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/FindSection|FindSection.tsx]] | `ACTIVE` | Implements the `FindSection` routed desktop screen and coordinates its learner-facing workflow state. | 8 | 2 |
| [[Reference/Desktop/TypeScript/screens/reader/GuideRail|GuideRail.tsx]] | `ACTIVE` | Implements the `GuideRail` routed desktop screen and coordinates its learner-facing workflow state. | 9 | 2 |
| [[Reference/Desktop/TypeScript/screens/reader/HiddenNotesSettings|HiddenNotesSettings.tsx]] | `ACTIVE` | Implements the `HiddenNotesSettings` routed desktop screen and coordinates its learner-facing workflow state. | 5 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/InquiryQuickCheck|InquiryQuickCheck.tsx]] | `ACTIVE` | Implements the `InquiryQuickCheck` routed desktop screen and coordinates its learner-facing workflow state. | 6 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/IntentBox|IntentBox.tsx]] | `ACTIVE` | Implements the `IntentBox` routed desktop screen and coordinates its learner-facing workflow state. | 6 | 2 |
| [[Reference/Desktop/TypeScript/screens/reader/KeptMark|KeptMark.tsx]] | `ACTIVE` | Implements the `KeptMark` routed desktop screen and coordinates its learner-facing workflow state. | 4 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/LibraryAnswer|LibraryAnswer.tsx]] | `ACTIVE` | Implements the `LibraryAnswer` routed desktop screen and coordinates its learner-facing workflow state. | 12 | 4 |
| [[Reference/Desktop/TypeScript/screens/reader/LibraryPane|LibraryPane.tsx]] | `ACTIVE` | Implements the `LibraryPane` routed desktop screen and coordinates its learner-facing workflow state. | 6 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/MarginMark|MarginMark.tsx]] | `ACTIVE` | Implements the `MarginMark` routed desktop screen and coordinates its learner-facing workflow state. | 5 | 2 |
| [[Reference/Desktop/TypeScript/screens/reader/ModelActionState|ModelActionState.tsx]] | `ACTIVE` | Implements the `ModelActionState` routed desktop screen and coordinates its learner-facing workflow state. | 3 | 15 |
| [[Reference/Desktop/TypeScript/screens/reader/NotesGapsSettings|NotesGapsSettings.tsx]] | `ACTIVE` | Implements the `NotesGapsSettings` routed desktop screen and coordinates its learner-facing workflow state. | 6 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/NotesRail|NotesRail.tsx]] | `ACTIVE` | Implements the `NotesRail` routed desktop screen and coordinates its learner-facing workflow state. | 8 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/PreparingView|PreparingView.tsx]] | `ACTIVE` | Implements the `PreparingView` routed desktop screen and coordinates its learner-facing workflow state. | 7 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/ProposalExercises|ProposalExercises.tsx]] | `ACTIVE` | Implements the `ProposalExercises` routed desktop screen and coordinates its learner-facing workflow state. | 7 | 3 |
| [[Reference/Desktop/TypeScript/screens/reader/ReaderAskBranches|ReaderAskBranches.tsx]] | `ACTIVE` | Implements the `ReaderAskBranches` routed desktop screen and coordinates its learner-facing workflow state. | 6 | 4 |
| [[Reference/Desktop/TypeScript/screens/reader/ReaderCorrespondenceSettings|ReaderCorrespondenceSettings.tsx]] | `ACTIVE` | Implements the `ReaderCorrespondenceSettings` routed desktop screen and coordinates its learner-facing workflow state. | 6 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/ReaderCueSettings|ReaderCueSettings.tsx]] | `ACTIVE` | Implements the `ReaderCueSettings` routed desktop screen and coordinates its learner-facing workflow state. | 7 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/ReaderNotes|ReaderNotes.tsx]] | `ACTIVE` | Implements the `ReaderNotes` routed desktop screen and coordinates its learner-facing workflow state. | 6 | 4 |
| [[Reference/Desktop/TypeScript/screens/reader/ReaderWorkingPosture|ReaderWorkingPosture.tsx]] | `ACTIVE` | Implements the `ReaderWorkingPosture` routed desktop screen and coordinates its learner-facing workflow state. | 8 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/ReadingPathCard|ReadingPathCard.tsx]] | `ACTIVE` | Implements the `ReadingPathCard` routed desktop screen and coordinates its learner-facing workflow state. | 6 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/RecapCard|RecapCard.tsx]] | `ACTIVE` | Implements the `RecapCard` routed desktop screen and coordinates its learner-facing workflow state. | 6 | 2 |
| [[Reference/Desktop/TypeScript/screens/reader/ReconnectLine|ReconnectLine.tsx]] | `ACTIVE` | Implements the `ReconnectLine` routed desktop screen and coordinates its learner-facing workflow state. | 3 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/ScopeFromPassage|ScopeFromPassage.tsx]] | `ACTIVE` | Implements the `ScopeFromPassage` routed desktop screen and coordinates its learner-facing workflow state. | 7 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/SideBySidePane|SideBySidePane.tsx]] | `ACTIVE` | Implements the `SideBySidePane` routed desktop screen and coordinates its learner-facing workflow state. | 10 | 3 |
| [[Reference/Desktop/TypeScript/screens/reader/TutorAnswer|TutorAnswer.tsx]] | `ACTIVE` | Implements the `TutorAnswer` routed desktop screen and coordinates its learner-facing workflow state. | 7 | 3 |
| [[Reference/Desktop/TypeScript/screens/reader/TutorOffers|TutorOffers.tsx]] | `ACTIVE` | Implements the `TutorOffers` routed desktop screen and coordinates its learner-facing workflow state. | 10 | 2 |
| [[Reference/Desktop/TypeScript/screens/reader/WrapUpOffer|WrapUpOffer.tsx]] | `ACTIVE` | Implements the `WrapUpOffer` routed desktop screen and coordinates its learner-facing workflow state. | 8 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/WrapUpPanel|WrapUpPanel.tsx]] | `ACTIVE` | Implements the `WrapUpPanel` routed desktop screen and coordinates its learner-facing workflow state. | 8 | 2 |
| [[Reference/Desktop/TypeScript/screens/reader/YouTubeWatchPanel|YouTubeWatchPanel.tsx]] | `ACTIVE` | Implements the `YouTubeWatchPanel` routed desktop screen and coordinates its learner-facing workflow state. | 6 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/activity|activity.ts]] | `ACTIVE` | Provides `setReaderActivityEnabled`, `readerActivityEnabled`, `newActivityId`, `flushReaderActivity` and related exports within the desktop's TypeScript/screens/reader ownership area. | 2 | 13 |
| [[Reference/Desktop/TypeScript/screens/reader/authoredQuestion|authoredQuestion.ts]] | `ACTIVE` | Provides `AuthoredQuestionStatus`, `authoredQuestionMessage` within the desktop's TypeScript/screens/reader ownership area. | 1 | 2 |
| [[Reference/Desktop/TypeScript/screens/reader/bareAlt|bareAlt.ts]] | `ACTIVE` | Provides `useBareAltClear` within the desktop's TypeScript/screens/reader ownership area. | 1 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/checkOffer|checkOffer.ts]] | `ACTIVE` | Provides `CheckSurface`, `ReadingPhase`, `SectionCheckOffer`, `PassageCheckOffer` and related exports within the desktop's TypeScript/screens/reader ownership area. | 0 | 2 |
| [[Reference/Desktop/TypeScript/screens/reader/compareKeepContext|compareKeepContext.ts]] | `ACTIVE` | Provides `CompareKeepContextValue`, `CompareKeepContext`, `useCompareKeep` within the desktop's TypeScript/screens/reader ownership area. | 1 | 4 |
| [[Reference/Desktop/TypeScript/screens/reader/comparePoints|comparePoints.ts]] | `ACTIVE` | Provides `RELATION_ORDER`, `CHIP_LABELS`, `RowChip`, `columnTitles` and related exports within the desktop's TypeScript/screens/reader ownership area. | 2 | 3 |
| [[Reference/Desktop/TypeScript/screens/reader/correspondenceEvents|correspondenceEvents.ts]] | `ACTIVE` | Provides `CorrespondentAct`, `CorrespondentActTarget`, `logCorrespondentAct` within the desktop's TypeScript/screens/reader ownership area. | 2 | 3 |
| [[Reference/Desktop/TypeScript/screens/reader/correspondentsRead|correspondentsRead.ts]] | `ACTIVE` | Provides `quietCorrespondents` within the desktop's TypeScript/screens/reader ownership area. | 2 | 2 |
| [[Reference/Desktop/TypeScript/screens/reader/cues|cues.ts]] | `ACTIVE` | Provides `CUE_DENSITIES`, `DENSITY_BUDGET`, `stepDown`, `CUE_COPY` and related exports within the desktop's TypeScript/screens/reader ownership area. | 1 | 6 |
| [[Reference/Desktop/TypeScript/screens/reader/deliverableSlice|deliverableSlice.ts]] | `ACTIVE` | Provides `DELIVERABLE_COPY`, `DELIVERABLE_POLL_MS`, `shouldPollSlice`, `sliceShown` and related exports within the desktop's TypeScript/screens/reader ownership area. | 1 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/exerciseCandidates (ts)|exerciseCandidates.ts]] | `ACTIVE` | Provides `EXERCISE_COPY`, `ExerciseCandidate`, `ReaderWorkbenchExercise`, `proposalKeys` and related exports within the desktop's TypeScript/screens/reader ownership area. | 1 | 7 |
| [[Reference/Desktop/TypeScript/screens/reader/guidePlan|guidePlan.ts]] | `ACTIVE` | Provides `GUIDE_DIAGNOSIS_POLL_MS`, `GUIDE_DIAGNOSIS_POLL_MAX_MS`, `guidePlanKey`, `pendingDiagnoses` and related exports within the desktop's TypeScript/screens/reader ownership area. | 5 | 3 |
| [[Reference/Desktop/TypeScript/screens/reader/intentPalette|intentPalette.ts]] | `ACTIVE` | Provides `INTENT_COPY`, `visiblePalette`, `paletteActions`, `SHOW_ME_LABEL` and related exports within the desktop's TypeScript/screens/reader ownership area. | 1 | 2 |
| [[Reference/Desktop/TypeScript/screens/reader/notesContext|notesContext.ts]] | `ACTIVE` | Provides `HiddenNote`, `NotesContextValue`, `NotesContext`, `useNotes` within the desktop's TypeScript/screens/reader ownership area. | 1 | 2 |
| [[Reference/Desktop/TypeScript/screens/reader/observerGeneration|observerGeneration.ts]] | `ACTIVE` | Provides `ObserverGeneration`, `observerGeneration` within the desktop's TypeScript/screens/reader ownership area. | 0 | 2 |
| [[Reference/Desktop/TypeScript/screens/reader/readerCache|readerCache.ts]] | `ACTIVE` | Provides `READER_CACHE_MS`, `SourceReadOptions`, `cachedSourceRead` within the desktop's TypeScript/screens/reader ownership area. | 2 | 3 |
| [[Reference/Desktop/TypeScript/screens/reader/readerKeys|readerKeys.ts]] | `ACTIVE` | Provides `ReaderKey`, `readerKeyBarKeys` within the desktop's TypeScript/screens/reader ownership area. | 0 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/readerShared|readerShared.ts]] | `ACTIVE` | Provides `ANSWER_MODE_OPTIONS`, `answerModeLabel`, `clip`, `SelectionNode` and related exports within the desktop's TypeScript/screens/reader ownership area. | 1 | 18 |
| [[Reference/Desktop/TypeScript/screens/reader/readingPath|readingPath.ts]] | `ACTIVE` | Provides `READING_PATH_COPY`, `READING_PATH_POLL_MS`, `shouldPoll`, `pathHeading` and related exports within the desktop's TypeScript/screens/reader ownership area. | 1 | 2 |
| [[Reference/Desktop/TypeScript/screens/reader/readingPosition|readingPosition.ts]] | `ACTIVE` | Provides `ReadingPosition`, `readingPositionIn`, `spanAtPosition`, `pagePositionAt` and related exports within the desktop's TypeScript/screens/reader ownership area. | 1 | 3 |
| [[Reference/Desktop/TypeScript/screens/reader/recapCopy|recapCopy.ts]] | `ACTIVE` | Provides `RECAP_COPY`, `fullDay`, `shortDay`, `aboutMinutes` and related exports within the desktop's TypeScript/screens/reader ownership area. | 1 | 5 |
| [[Reference/Desktop/TypeScript/screens/reader/returnStack|returnStack.ts]] | `ACTIVE` | Provides `DetourKind`, `RailTab`, `ReturnEntry`, `ReturnStack` and related exports within the desktop's TypeScript/screens/reader ownership area. | 2 | 6 |
| [[Reference/Desktop/TypeScript/screens/reader/roleLabel|roleLabel.ts]] | `ACTIVE` | Provides `MODEL_LABEL`, `hitRoleLabel` within the desktop's TypeScript/screens/reader ownership area. | 1 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/searchBasis|searchBasis.ts]] | `ACTIVE` | Provides `searchBasisLabel` within the desktop's TypeScript/screens/reader ownership area. | 1 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/sideBySide|sideBySide.ts]] | `ACTIVE` | Provides `SIDE_BY_SIDE_MIN_WIDTH`, `Pane`, `PaneTarget`, `targetOf` and related exports within the desktop's TypeScript/screens/reader ownership area. | 1 | 4 |
| [[Reference/Desktop/TypeScript/screens/reader/useActiveReading|useActiveReading.ts]] | `ACTIVE` | Provides `AnotherWayHit`, `ActiveReadingState`, `AnotherWayState`, `UNDONE_EARLIER` and related exports within the desktop's TypeScript/screens/reader ownership area. | 5 | 3 |
| [[Reference/Desktop/TypeScript/screens/reader/useCueDiscovery|useCueDiscovery.ts]] | `ACTIVE` | Provides `DISCOVERY_POLL_MS`, `DISCOVERY_MAX_READS`, `DISCOVERY_MAX_REASKS`, `TARGETS_PENDING_POLL_MS` and related exports within the desktop's TypeScript/screens/reader ownership area. | 3 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/useCueImpressions|useCueImpressions.ts]] | `ACTIVE` | Provides `IMPRESSION_FLUSH_MS`, `IMPRESSION_RETRY_MS`, `CUE_REFLOW_SETTLE_MS`, `passageThresholds` and related exports within the desktop's TypeScript/screens/reader ownership area. | 5 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/useIntentBox|useIntentBox.ts]] | `ACTIVE` | Provides `SHOW_AFTER_MS`, `IntentRunHow`, `IntentRunHandle`, `IntentCancel` and related exports within the desktop's TypeScript/screens/reader ownership area. | 6 | 4 |
| [[Reference/Desktop/TypeScript/screens/reader/useKeptComparisons|useKeptComparisons.ts]] | `ACTIVE` | Provides `useKeptComparisons` within the desktop's TypeScript/screens/reader ownership area. | 3 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/useLibraryAsk|useLibraryAsk.ts]] | `ACTIVE` | Provides `LIBRARY_COPY`, `SCOPE_COPY`, `CompareRequest`, `comparePayload` and related exports within the desktop's TypeScript/screens/reader ownership area. | 5 | 5 |
| [[Reference/Desktop/TypeScript/screens/reader/useLibraryExercises|useLibraryExercises.ts]] | `ACTIVE` | Provides `LibraryExercisesSettings`, `LibraryExercisesState`, `useLibraryExercises` within the desktop's TypeScript/screens/reader ownership area. | 5 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/useReaderCues|useReaderCues.ts]] | `ACTIVE` | Provides `CueCheckMeRequest`, `CueRequestOrigin`, `CueSurface`, `ReaderCuesInput` and related exports within the desktop's TypeScript/screens/reader ownership area. | 9 | 2 |
| [[Reference/Desktop/TypeScript/screens/reader/useReaderInquiry|useReaderInquiry.ts]] | `ACTIVE` | Provides `INQUIRY_CHECK_POLL_MS`, `INQUIRY_CHECK_MAX_POLLS`, `AskAnchor`, `AskOverride` and related exports within the desktop's TypeScript/screens/reader ownership area. | 16 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/useReaderRecap|useReaderRecap.ts]] | `ACTIVE` | Provides `ReaderRecapInput`, `ReaderRecapCtl`, `NARRATIVE_POLL_MS`, `useReaderRecap` within the desktop's TypeScript/screens/reader ownership area. | 6 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/useReaderRequests|useReaderRequests.ts]] | `ACTIVE` | Provides `BackgroundRequest`, `SynthesizedObject`, `useReaderRequests`, `parseRequestResult` and related exports within the desktop's TypeScript/screens/reader ownership area. | 2 | 2 |
| [[Reference/Desktop/TypeScript/screens/reader/useReaderVisit|useReaderVisit.ts]] | `ACTIVE` | Provides `ReaderVisitInput`, `ReaderVisit`, `useReaderVisit` within the desktop's TypeScript/screens/reader ownership area. | 3 | 3 |
| [[Reference/Desktop/TypeScript/screens/reader/useReaderWorkbench|useReaderWorkbench.ts]] | `ACTIVE` | Provides `ReaderWorkbenchCheck`, `ReaderWorkbenchProps`, `ReaderWorkbenchResume`, `ActiveWorkbench` and related exports within the desktop's TypeScript/screens/reader ownership area. | 7 | 4 |
| [[Reference/Desktop/TypeScript/screens/reader/useReadingProgress|useReadingProgress.ts]] | `ACTIVE` | Provides `SEEN_SETTLE_MS`, `SEEN_REPORT_MS`, `READING_MARKER`, `readingPositionKey` and related exports within the desktop's TypeScript/screens/reader ownership area. | 7 | 3 |
| [[Reference/Desktop/TypeScript/screens/reader/useSideBySide|useSideBySide.ts]] | `ACTIVE` | Provides `SidePaneDraft`, `SIDE_BY_SIDE_COPY`, `SIDE_BY_SIDE_SCROLL_KEYS`, `MainPane` and related exports within the desktop's TypeScript/screens/reader ownership area. | 7 | 2 |
| [[Reference/Desktop/TypeScript/screens/reader/useSidePane|useSidePane.ts]] | `ACTIVE` | Provides `PaneCaptureTarget`, `SidePaneInput`, `useSidePane`, `SidePane` and related exports within the desktop's TypeScript/screens/reader ownership area. | 7 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/visitClock|visitClock.ts]] | `ACTIVE` | Provides `VISIT_IDLE_MS`, `VisitClock`, `accrueVisit`, `visitSeconds` within the desktop's TypeScript/screens/reader ownership area. | 0 | 1 |
| [[Reference/Desktop/TypeScript/screens/reader/voices|voices.tsx]] | `ACTIVE` | Implements the `voices` routed desktop screen and coordinates its learner-facing workflow state. | 1 | 44 |

## Modification guidance

Follow a module note's inbound consumers and dependencies before moving ownership. Update architecture/workflow authority only when behavior—not merely file layout—changes.

## Related notes

- [[Architecture/Adapter Architecture#Request flow|Adapter request flow]]
- [[Architecture/Architecture Overview#Runtime composition|Runtime composition]]
- [[Reference/Desktop/Desktop Module Catalog|Desktop Module Catalog]]
