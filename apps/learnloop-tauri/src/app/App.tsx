import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import type { AppSnapshot, SessionEndSummary, SessionSnapshot } from "../api/dto";
import { AskOverlay, type AskTarget } from "../components/AskOverlay";
import { CommandPalette } from "../components/CommandPalette";
import { InspectorOverlay } from "../components/InspectorOverlay";
import { SessionFinishHud } from "../components/SessionFinishHud";
import { EmptyPlaceholder, TerminalFrame, type TopTab, navTabs } from "../components/ui";
import { CalibrationScreen } from "../screens/CalibrationScreen";
import { ExamScreen } from "../screens/ExamScreen";
import { FeedbackScreen } from "../screens/FeedbackScreen";
import { GraphScreen } from "../screens/GraphScreen";
import { IngestScreen } from "../screens/IngestScreen";
import { LibraryScreen } from "../screens/LibraryScreen";
import { PracticeScreen } from "../screens/PracticeScreen";
import { ProposalsScreen } from "../screens/ProposalsScreen";
import { StartScreen } from "../screens/StartScreen";
import { TodayScreen } from "../screens/TodayScreen";
import { setAlgoConfig } from "./algoConfig";

type TodayStage = "queue" | "practice" | "feedback";

export function App() {
  const [snapshot, setSnapshot] = useState<AppSnapshot | null>(null);
  const [session, setSession] = useState<SessionSnapshot | null>(null);
  const [tab, setTab] = useState<TopTab>("start");
  const [todayStage, setTodayStage] = useState<TodayStage>("queue");
  const [practiceItemId, setPracticeItemId] = useState<string | null>(null);
  // The current practice item is a primed retry (opened from the feedback
  // screen's source panel); the submit carries primed=true to the backend.
  const [primedRetry, setPrimedRetry] = useState(false);
  const [attemptId, setAttemptId] = useState<string | null>(null);
  // The practice-exam overlay: when set, ExamScreen takes over the body (entered
  // only from the goal banner, exited back to the today tab). Not a nav tab.
  const [examGoalId, setExamGoalId] = useState<string | null>(null);
  // The active §5.9 calibration session: when set, CalibrationScreen pre-empts
  // the tab body (like the exam overlay) except while a practice/feedback round
  // for its next target is in flight — coming back from that round remounts the
  // screen, which refreshes progress. Entered from the command palette.
  const [calibrationSessionId, setCalibrationSessionId] = useState<string | null>(null);
  const [inspectorId, setInspectorId] = useState<string | null>(null);
  const [libraryFocus, setLibraryFocus] = useState<{ patchId: string; itemId: string } | null>(null);
  const [libraryFilePath, setLibraryFilePath] = useState<string | null>(null);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [paletteEntityIds, setPaletteEntityIds] = useState<string[]>([]);
  const [palettePracticeItemIds, setPalettePracticeItemIds] = useState<string[]>([]);
  const [toast, setToast] = useState<string | null>(null);
  const [finishSummary, setFinishSummary] = useState<SessionEndSummary | null>(null);
  const [askTarget, setAskTarget] = useState<AskTarget | null>(null);
  // In-memory mirror of the practice draft, reported by PracticeScreen when it
  // unmounts. The backend checkpoint is also updated, but `session.checkpoint`
  // is only loaded at startup — without this mirror, esc-ing to Today and
  // re-opening the same question mid-session would show an empty editor.
  const [localDraft, setLocalDraft] = useState<{
    practiceItemId: string;
    answerMd: string;
    hintsUsed: number;
  } | null>(null);
  const onPracticeDraft = useCallback(
    (draft: { practiceItemId: string; answerMd: string; hintsUsed: number }) => setLocalDraft(draft),
    []
  );
  const [libraryNoteId, setLibraryNoteId] = useState<string | null>(null);
  const startupStartedRef = useRef(false);
  // Whether the practice screen is currently a teach-back conversation. Only
  // PracticeScreen knows the item's mode; it reports it up so the
  // command-palette ask path can refuse to open the tutor mid-transcript.
  const teachBackActiveRef = useRef(false);
  const onTeachBackActive = useCallback((active: boolean) => {
    teachBackActiveRef.current = active;
  }, []);

  const onError = useCallback((message: string) => setToast(message), []);
  const onPaletteEntities = useCallback((ids: { inspectIds: string[]; practiceItemIds: string[] }) => {
    setPaletteEntityIds(ids.inspectIds);
    setPalettePracticeItemIds(ids.practiceItemIds);
  }, []);

  useEffect(() => {
    if (startupStartedRef.current) return;
    startupStartedRef.current = true;

    api.loadVault()
      .then((appSnapshot) => {
        setAlgoConfig(appSnapshot.config);
        setSnapshot(appSnapshot);
        if (appSnapshot.activeSession) {
          setSession(appSnapshot.activeSession);
          const checkpoint = appSnapshot.activeSession.checkpoint;
          if (checkpoint?.currentPracticeItemId) {
            setPracticeItemId(checkpoint.currentPracticeItemId);
            setTab("today");
            setTodayStage("practice");
          }
        }
      })
      .catch((error) => onError(error.message));
  }, [onError]);

  useEffect(() => {
    localStorage.setItem("learnloop.tab", tab);
  }, [tab]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const tag = (event.target as HTMLElement | null)?.tagName?.toLowerCase();
      const textTarget = tag === "input" || tag === "textarea";
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "p") {
        event.preventDefault();
        setPaletteOpen(true);
        return;
      }
      if (!textTarget && event.key === ":") {
        event.preventDefault();
        setPaletteOpen(true);
        return;
      }
      if (textTarget) return;
      if (event.altKey && /^[1-8]$/.test(event.key)) {
        const next = navTabs[Number(event.key) - 1];
        if (next) {
          gotoTab(next.id);
          event.preventDefault();
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const restored = useMemo(() => {
    if (localDraft && localDraft.practiceItemId === practiceItemId) {
      return { answer: localDraft.answerMd, hints: localDraft.hintsUsed, teachBack: null };
    }
    const checkpoint = session?.checkpoint;
    if (!checkpoint || checkpoint.currentPracticeItemId !== practiceItemId) {
      return { answer: "", hints: 0, teachBack: null };
    }
    return {
      answer: checkpoint.currentAnswer ?? "",
      hints: checkpoint.hintsUsed,
      teachBack: checkpoint.teachBack ?? null
    };
  }, [session, practiceItemId, localDraft]);
  const manualGrading = snapshot?.health.ai?.manualGrading ?? false;
  // In manual mode the sidecar reports ready=true (it's an intentional choice,
  // not an outage) — but practice screens must still start in self-grade mode.
  const gradingReady = (snapshot?.health.ai?.ready ?? snapshot?.health.codex.ready ?? false) && !manualGrading;
  const gradingProvider = snapshot?.health.ai?.activeProvider ?? "codex";
  const availableProviders = snapshot?.health.ai?.availableGradingProviders ?? [];

  const changeGradingProvider = useCallback(
    async (provider: string) => {
      try {
        const result = await api.setGradingProvider(provider);
        setSnapshot((current) =>
          current
            ? {
                ...current,
                health: {
                  ...current.health,
                  ai: {
                    ...current.health.ai,
                    activeProvider: result.activeProvider,
                    ready: result.ready,
                    manualGrading: result.manualGrading,
                    availableGradingProviders: result.availableProviders
                  }
                }
              }
            : current
        );
        setToast(`grading → ${result.manualGrading ? "manual (self-grade)" : result.activeProvider}`);
      } catch (error) {
        onError((error as Error).message);
      }
    },
    [onError]
  );

  function beginSession(next: SessionSnapshot) {
    setSession(next);
    setTab("today");
    setTodayStage("queue");
  }

  function openPractice(id: string) {
    if (!session) {
      setTab("start");
      setToast("Start a session before opening practice.");
      return;
    }
    setPrimedRetry(false);
    setPracticeItemId(id);
    setTab("today");
    setTodayStage("practice");
  }

  function openPrimedRetry(id: string) {
    if (!session) {
      setTab("start");
      setToast("Start a session before opening practice.");
      return;
    }
    setPrimedRetry(true);
    setPracticeItemId(id);
    setTab("today");
    setTodayStage("practice");
  }

  function openFeedback(id: string) {
    setPrimedRetry(false);
    setAttemptId(id);
    setTodayStage("feedback");
  }

  // "View in Library" from the feedback source panel: open that vault file.
  function openLibraryFile(path: string) {
    setLibraryFilePath(path);
    setTab("library");
  }

  function clearLocalCheckpoint() {
    setSession((current) => current ? { ...current, checkpoint: null } : current);
    setLocalDraft(null);
  }

  function endSession(summary: SessionEndSummary) {
    setSession(null);
    setLocalDraft(null);
    setPracticeItemId(null);
    setAttemptId(null);
    // Calibration attaches to the practice session — drop the overlay with it.
    setCalibrationSessionId(null);
    setTodayStage("queue");
    setTab("start");
    // The finish HUD replaces the plain toast: it overlays the (now reset)
    // Start screen, reads out the summary, and holds until the learner dismisses.
    setFinishSummary(summary);
  }

  function gotoTab(next: TopTab) {
    setTab(next);
    if (next !== "today") setTodayStage("queue");
  }

  // Enter the practice-exam overlay from the goal banner.
  function openExam(goalId: string) {
    setExamGoalId(goalId);
  }

  // Exit the exam back to the today tab.
  function exitExam() {
    setExamGoalId(null);
    setTab("today");
    setTodayStage("queue");
  }

  // Enter the calibration overlay (command palette "calibrate").
  function openCalibration(id: string) {
    setCalibrationSessionId(id);
    setTab("today");
    setTodayStage("queue");
  }

  // Exit calibration back to the today tab.
  function exitCalibration() {
    setCalibrationSessionId(null);
    setTab("today");
    setTodayStage("queue");
  }

  // Open the ask overlay for the current context if one is determinable
  // (command palette entry). Screens with richer context (practice timer)
  // call setAskTarget directly via onAsk.
  const askCurrentContext = useCallback((): boolean => {
    if (tab === "today" && todayStage === "practice" && practiceItemId && session) {
      if (teachBackActiveRef.current) {
        // The tutor could leak answers into the graded transcript.
        setToast("ask-tutor is disabled during a teach-back conversation.");
        return false;
      }
      setAskTarget({
        context: "practice",
        practiceItemId,
        sessionId: session.sessionId
      });
      return true;
    }
    if (tab === "today" && todayStage === "feedback" && attemptId) {
      setAskTarget({ context: "feedback", attemptId, sessionId: session?.sessionId });
      return true;
    }
    if (tab === "library" && libraryNoteId) {
      setAskTarget({ context: "library", noteId: libraryNoteId });
      return true;
    }
    return false;
  }, [tab, todayStage, practiceItemId, attemptId, session, libraryNoteId]);

  // Handoff from the Proposals screen: open the proposal's payload in the Library editor.
  function gotoLibraryProposal(patchId: string, itemId: string) {
    setLibraryFocus({ patchId, itemId });
    setTab("library");
  }

  const changeVault = useCallback(
    async (path: string) => {
      try {
        await api.selectVault(path);
        const next = await api.loadVault();
        setAlgoConfig(next.config);
        setSnapshot(next);
        setSession(next.activeSession ?? null);
        setPracticeItemId(null);
        setAttemptId(null);
        setInspectorId(null);
        setCalibrationSessionId(null);
        setTodayStage("queue");
        setTab("start");
      } catch (error) {
        onError((error as Error).message);
      }
    },
    [onError]
  );

  function renderBody() {
    if (!snapshot) {
      return <EmptyPlaceholder title="Loading LearnLoop vault" />;
    }
    // The exam overlay pre-empts the tab body — it's entered only from the goal
    // banner and returns to the today tab on exit.
    if (examGoalId) {
      return <ExamScreen goalId={examGoalId} onExit={exitExam} onError={onError} />;
    }
    // The calibration overlay also pre-empts the tab body, but yields to the
    // practice/feedback stages so its "Practice next target" handoff runs the
    // ordinary practice loop — returning to the queue remounts (→ refreshes) it.
    const practicing = tab === "today" && (todayStage === "practice" || todayStage === "feedback");
    if (calibrationSessionId && !practicing) {
      return (
        <CalibrationScreen
          calibrationSessionId={calibrationSessionId}
          onPractice={openPractice}
          onExit={exitCalibration}
          onError={onError}
        />
      );
    }
    if (tab === "start") {
      return <StartScreen onBegin={beginSession} onError={onError} vault={snapshot.vault} streak={snapshot.streak} />;
    }
    if (tab === "today") {
      if (todayStage === "practice" && session && practiceItemId) {
        return (
          <PracticeScreen
            session={session}
            practiceItemId={practiceItemId}
            primed={primedRetry}
            gradingReady={gradingReady}
            gradingProvider={gradingProvider}
            restoredAnswer={restored.answer}
            restoredHints={restored.hints}
            restoredTeachBack={restored.teachBack}
            onFeedback={openFeedback}
            onBack={() => setTodayStage("queue")}
            onCheckpointCleared={clearLocalCheckpoint}
            onDraftSaved={onPracticeDraft}
            onTeachBackActive={onTeachBackActive}
            onInspect={setInspectorId}
            onAsk={setAskTarget}
            onError={onError}
          />
        );
      }
      if (todayStage === "feedback" && attemptId) {
        return (
          <FeedbackScreen
            attemptId={attemptId}
            onNext={() => setTodayStage("queue")}
            onBack={() => setTodayStage("queue")}
            onOpenNotes={() => gotoTab("library")}
            onPrimedRetry={openPrimedRetry}
            onOpenLibraryFile={openLibraryFile}
            onInspect={setInspectorId}
            onPaletteEntities={onPaletteEntities}
            onAsk={setAskTarget}
            onError={onError}
          />
        );
      }
      return (
        <TodayScreen
          session={session}
          gradingReady={gradingReady}
          gradingProvider={gradingProvider}
          algorithmVersion={snapshot.vault?.algorithmVersion ?? "unknown"}
          onOpenPractice={openPractice}
          onPaletteEntities={onPaletteEntities}
          onEndSession={endSession}
          onInspect={setInspectorId}
          onTakeExam={openExam}
          onError={onError}
        />
      );
    }
    if (tab === "graph") {
      return <GraphScreen onInspect={setInspectorId} onError={onError} />;
    }
    if (tab === "ingest") {
      return <IngestScreen onProceedToPropose={() => gotoTab("proposals")} />;
    }
    if (tab === "library") {
      return (
        <LibraryScreen
          onError={onError}
          focus={libraryFocus}
          onFocusConsumed={() => setLibraryFocus(null)}
          focusFilePath={libraryFilePath}
          onFileFocusConsumed={() => setLibraryFilePath(null)}
          onAsk={setAskTarget}
          onNoteSelected={setLibraryNoteId}
        />
      );
    }
    if (tab === "proposals") {
      return (
        <ProposalsScreen
          authoringReady={snapshot.health.ai.ready}
          authoringProvider={snapshot.health.ai.activeProvider}
          onInspect={setInspectorId}
          onPaletteEntities={onPaletteEntities}
          onError={onError}
          onHandoff={gotoLibraryProposal}
        />
      );
    }
    return <EmptyPlaceholder title={tab} />;
  }

  return (
    <>
      <TerminalFrame
        active={tab}
        onTab={gotoTab}
        aiReady={gradingReady}
        aiLabel={gradingProvider}
        aiManual={manualGrading}
        aiProviders={availableProviders}
        onSelectAiProvider={changeGradingProvider}
        vaultRoot={snapshot?.vault?.root}
        onSelectVault={changeVault}
      >
        {toast ? <div className="toast" onClick={() => setToast(null)}>{toast}</div> : null}
        {renderBody()}
      </TerminalFrame>
      <InspectorOverlay
        entityId={inspectorId}
        onClose={() => setInspectorId(null)}
        onInspect={setInspectorId}
        onError={onError}
      />
      <AskOverlay target={askTarget} onClose={() => setAskTarget(null)} onToast={setToast} />
      <SessionFinishHud summary={finishSummary} onDismiss={() => setFinishSummary(null)} />
      <CommandPalette
        open={paletteOpen}
        session={session}
        entityIds={unique([practiceItemId, attemptId, ...paletteEntityIds])}
        practiceItemIds={unique([practiceItemId, ...palettePracticeItemIds])}
        subjects={snapshot?.vault?.subjects ?? []}
        onClose={() => setPaletteOpen(false)}
        onGoto={gotoTab}
        onOpenPractice={openPractice}
        onOpenCalibration={openCalibration}
        onInspect={setInspectorId}
        onAsk={askCurrentContext}
        onError={onError}
      />
    </>
  );
}

function unique(values: Array<string | null>): string[] {
  return Array.from(new Set(values.filter((value): value is string => Boolean(value))));
}
