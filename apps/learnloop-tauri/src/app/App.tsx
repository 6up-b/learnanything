import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import type { AppSnapshot, SessionEndSummary, SessionSnapshot } from "../api/dto";
import { CommandPalette } from "../components/CommandPalette";
import { InspectorOverlay } from "../components/InspectorOverlay";
import { SessionFinishHud } from "../components/SessionFinishHud";
import { EmptyPlaceholder, TerminalFrame, type TopTab, navTabs } from "../components/ui";
import { FeedbackScreen } from "../screens/FeedbackScreen";
import { GraphScreen } from "../screens/GraphScreen";
import { LibraryScreen } from "../screens/LibraryScreen";
import { PracticeScreen } from "../screens/PracticeScreen";
import { ProposalsScreen } from "../screens/ProposalsScreen";
import { StartScreen } from "../screens/StartScreen";
import { TodayScreen } from "../screens/TodayScreen";

type TodayStage = "queue" | "practice" | "feedback";

export function App() {
  const [snapshot, setSnapshot] = useState<AppSnapshot | null>(null);
  const [session, setSession] = useState<SessionSnapshot | null>(null);
  const [tab, setTab] = useState<TopTab>("start");
  const [todayStage, setTodayStage] = useState<TodayStage>("queue");
  const [practiceItemId, setPracticeItemId] = useState<string | null>(null);
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [inspectorId, setInspectorId] = useState<string | null>(null);
  const [libraryFocus, setLibraryFocus] = useState<{ patchId: string; itemId: string } | null>(null);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [paletteEntityIds, setPaletteEntityIds] = useState<string[]>([]);
  const [palettePracticeItemIds, setPalettePracticeItemIds] = useState<string[]>([]);
  const [toast, setToast] = useState<string | null>(null);
  const [finishSummary, setFinishSummary] = useState<SessionEndSummary | null>(null);
  const startupStartedRef = useRef(false);

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
    const checkpoint = session?.checkpoint;
    if (!checkpoint || checkpoint.currentPracticeItemId !== practiceItemId) return { answer: "", hints: 0 };
    return { answer: checkpoint.currentAnswer ?? "", hints: checkpoint.hintsUsed };
  }, [session, practiceItemId]);
  const gradingReady = snapshot?.health.ai?.ready ?? snapshot?.health.codex.ready ?? false;
  const gradingProvider = snapshot?.health.ai?.activeProvider ?? "codex";

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
    setPracticeItemId(id);
    setTab("today");
    setTodayStage("practice");
  }

  function openFeedback(id: string) {
    setAttemptId(id);
    setTodayStage("feedback");
  }

  function clearLocalCheckpoint() {
    setSession((current) => current ? { ...current, checkpoint: null } : current);
  }

  function endSession(summary: SessionEndSummary) {
    setSession(null);
    setPracticeItemId(null);
    setAttemptId(null);
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
        setSnapshot(next);
        setSession(next.activeSession ?? null);
        setPracticeItemId(null);
        setAttemptId(null);
        setInspectorId(null);
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
    if (tab === "start") {
      return <StartScreen onBegin={beginSession} onError={onError} vault={snapshot.vault} streak={snapshot.streak} />;
    }
    if (tab === "today") {
      if (todayStage === "practice" && session && practiceItemId) {
        return (
          <PracticeScreen
            session={session}
            practiceItemId={practiceItemId}
            gradingReady={gradingReady}
            gradingProvider={gradingProvider}
            restoredAnswer={restored.answer}
            restoredHints={restored.hints}
            onFeedback={openFeedback}
            onBack={() => setTodayStage("queue")}
            onCheckpointCleared={clearLocalCheckpoint}
            onInspect={setInspectorId}
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
            onInspect={setInspectorId}
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
          onError={onError}
        />
      );
    }
    if (tab === "graph") {
      return <GraphScreen onInspect={setInspectorId} onError={onError} />;
    }
    if (tab === "library") {
      return <LibraryScreen onError={onError} focus={libraryFocus} onFocusConsumed={() => setLibraryFocus(null)} />;
    }
    if (tab === "proposals") {
      return (
        <ProposalsScreen
          authoringReady={snapshot.health.ai.ready}
          authoringProvider={snapshot.health.ai.activeProvider}
          onInspect={setInspectorId}
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
        onInspect={setInspectorId}
        onError={onError}
      />
    </>
  );
}

function unique(values: Array<string | null>): string[] {
  return Array.from(new Set(values.filter((value): value is string => Boolean(value))));
}
