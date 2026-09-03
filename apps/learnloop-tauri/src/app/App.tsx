import { listen } from "@tauri-apps/api/event";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import type { AppSnapshot, GuidedRedoDto, ProbeBlockEndDto, ReviewCountsDto, RuntimeHealth, SessionEndSummary, SessionSnapshot } from "../api/dto";
import { AskOverlay, type AskTarget } from "../components/AskOverlay";
import { CommandPalette } from "../components/CommandPalette";
import { InspectorOverlay } from "../components/InspectorOverlay";
import { SessionFinishHud } from "../components/SessionFinishHud";
import { EmptyPlaceholder, SHOW_GOLDEN_PATH, TerminalFrame, type NavBadgeCounts, type TopTab, navTabs } from "../components/ui";
import { CalibrationScreen } from "../screens/CalibrationScreen";
import { DiagnosticReviewScreen } from "../screens/DiagnosticReviewScreen";
import { ExamScreen } from "../screens/ExamScreen";
import { FeedbackScreen } from "../screens/FeedbackScreen";
import { GraphScreen } from "../screens/GraphScreen";
import { IngestScreen } from "../screens/IngestScreen";
import { LibraryScreen } from "../screens/LibraryScreen";
import { MaintenanceScreen } from "../screens/MaintenanceScreen";
import { SettingsOverlay } from "../screens/SettingsScreen";
import { PracticeScreen } from "../screens/PracticeScreen";
import { ProposalsScreen } from "../screens/ProposalsScreen";
import { RegistryReviewScreen } from "../screens/RegistryReviewScreen";
import { RepairScreen } from "../screens/RepairScreen";
import { ReviewScreen } from "../screens/ReviewScreen";
import { StartScreen } from "../screens/StartScreen";
import { TodayScreen } from "../screens/TodayScreen";
import { OpenInSource } from "../components/OpenInSource";
import { QuickAddDialog } from "../components/QuickAddDialog";
import { NewVaultWizard } from "../components/NewVaultWizard";
import { GoldenPathScreen } from "../screens/GoldenPathScreen";
import { GoldenPathSetup } from "../components/goldenpath/GoldenPathSetup";
import { ReaderScreen } from "../screens/ReaderScreen";
import { ExemplarConfirmDialog } from "../components/ExemplarConfirmDialog";
import { WhyDiagnosisOverlay } from "../components/WhyDiagnosisOverlay";
import { AdjudicationOverlay } from "../components/AdjudicationOverlay";
import type { TriageResultDto } from "../api/dto";
import { setAlgoConfig } from "./algoConfig";
import { isTypingTarget } from "./keyboard";
import { notifyQueueChanged, subscribeQueueChanged } from "../queueEvents";
import { clear as clearQueryCache, invalidateAll as invalidateAllQueries } from "../api/queryCache";
import { recordRecentVault, removeRecentVault } from "./recentVaults";
import { errorMessage } from "../errors";

type OpenSourceTarget = {
  extractionId: string;
  spanId: string;
  context?: string;
  entityType?: string | null;
  entityId?: string | null;
};

type TodayStage = "queue" | "practice" | "feedback" | "blockReview";

type VaultFilesChangedEvent = {
  root: string;
  changedPaths: string[];
  refresh: {
    mode?: "noop" | "stale" | "incremental" | "full";
    practiceItemCount?: number;
    snapshot?: AppSnapshot;
    error?: { code: string; message: string };
  };
};

export function App() {
  const [snapshot, setSnapshot] = useState<AppSnapshot | null>(null);
  const [startupError, setStartupError] = useState<string | null>(null);
  const [reviewCounts, setReviewCounts] = useState<ReviewCountsDto | null>(null);
  const [session, setSession] = useState<SessionSnapshot | null>(null);
  const [tab, setTab] = useState<TopTab>("start");
  // Registry review (§5.7) + Open-in-source (§9.2) + Quick add (§1) surfaces.
  const [registrySubjectId, setRegistrySubjectId] = useState<string | null>(null);
  const [openSource, setOpenSource] = useState<OpenSourceTarget | null>(null);
  const [quickAddOpen, setQuickAddOpen] = useState(false);
  const [quickAddGuided, setQuickAddGuided] = useState(false);
  const [quickAddDefaultSubjectId, setQuickAddDefaultSubjectId] = useState<string | null>(null);
  const [ingestGuideActive, setIngestGuideActive] = useState(false);
  const [newVaultOpen, setNewVaultOpen] = useState(false);
  const [todayStage, setTodayStage] = useState<TodayStage>("queue");
  const [practiceItemId, setPracticeItemId] = useState<string | null>(null);
  // The current practice item is a primed retry (opened from the feedback
  // screen's source panel); the submit carries primed=true to the backend.
  const [primedRetry, setPrimedRetry] = useState(false);
  // Fix 3 guided partial redo: when set, PracticeScreen renders the preserved
  // learner work read-only and the learner rewrites only the failed portion;
  // the composed answer is submitted primed on the SAME item.
  const [redoContext, setRedoContext] = useState<GuidedRedoDto | null>(null);
  const [attemptId, setAttemptId] = useState<string | null>(null);
  // §5.7: the unified Diagnostic Check review, shown instead of single-attempt
  // feedback when a probe block just closed (releasedFeedback covers every
  // attempt in the block).
  const [blockReview, setBlockReview] = useState<{
    blockEnd: ProbeBlockEndDto;
    learningObjectId: string;
    learningObjectTitle: string;
  } | null>(null);
  // The practice-exam overlay: when set, ExamScreen takes over the body (entered
  // only from the goal banner, exited back to the today tab). Not a nav tab.
  const [examGoalId, setExamGoalId] = useState<string | null>(null);
  // P2 golden path: the active run (body-pre-emption, exam precedent), the atomic
  // confirmation dialog, and the why-this-diagnosis overlay.
  const [goldenRunId, setGoldenRunId] = useState<string | null>(null);
  // Golden tab: false → the real discovery/confirm setup; true → offline fixture demo.
  const [goldenDemo, setGoldenDemo] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [whyTriage, setWhyTriage] = useState<TriageResultDto | null>(null);
  // The active §5.9 calibration session: when set, CalibrationScreen pre-empts
  // the tab body (like the exam overlay) except while a practice/feedback round
  // for its next target is in flight — coming back from that round remounts the
  // screen, which refreshes progress. Entered from the command palette.
  const [calibrationSessionId, setCalibrationSessionId] = useState<string | null>(null);
  const [inspectorId, setInspectorId] = useState<string | null>(null);
  // Review is a command overlay (`learnloop diff`), not a body-replacing tab.
  // Keep the current screen mounted beneath it just as `learnloop show` does.
  const [reviewOpen, setReviewOpen] = useState(false);
  // Settings is also a command-style overlay. In particular, opening it while
  // practicing or reading must not unmount the active screen beneath it.
  const [settingsOpen, setSettingsOpen] = useState(false);
  // Diagnosis adjudication (§2 A4) is a command overlay too: the supply step for
  // the eval store, opened over whatever screen is mounted.
  const [adjudicateOpen, setAdjudicateOpen] = useState(false);
  const [libraryFocus, setLibraryFocus] = useState<{ patchId: string; itemId: string } | null>(null);
  const [proposalFocusPatchId, setProposalFocusPatchId] = useState<string | null>(null);
  const [ingestJobId, setIngestJobId] = useState<string | null>(null);
  const [libraryFilePath, setLibraryFilePath] = useState<string | null>(null);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [paletteEntityIds, setPaletteEntityIds] = useState<string[]>([]);
  const [palettePracticeItemIds, setPalettePracticeItemIds] = useState<string[]>([]);
  const [toast, setToast] = useState<string | null>(null);
  const [finishSummary, setFinishSummary] = useState<SessionEndSummary | null>(null);
  const [askTarget, setAskTarget] = useState<AskTarget | null>(null);
  // Today unmounts when navigating to another tab. Keep this dismissal at the
  // app/session level so the no-goal decay banner stays dismissed when the
  // learner returns during the same practice session.
  const [todayNoGoalBannerDismissed, setTodayNoGoalBannerDismissed] = useState(false);
  // In-memory mirror of the practice draft, reported by PracticeScreen when it
  // unmounts. The backend checkpoint is also updated, but `session.checkpoint`
  // is only loaded at startup — without this mirror, esc-ing to Today and
  // re-opening the same question mid-session would show an empty editor.
  const [localDraft, setLocalDraft] = useState<{
    practiceItemId: string;
    answerMd: string;
    hintsUsed: number;
    submissionId: string;
  } | null>(null);
  const onPracticeDraft = useCallback(
    (draft: { practiceItemId: string; answerMd: string; hintsUsed: number; submissionId: string }) => setLocalDraft(draft),
    []
  );
  const [libraryNoteId, setLibraryNoteId] = useState<string | null>(null);
  // F6 Repair (§4.10): a detail overlay launched with a misconception id. Not a
  // tab. openRepair is the App-level entry point — wire it to Feedback's "repair
  // this" and Today cards as well (pass onRepair={openRepair}).
  const [repairMisconceptionId, setRepairMisconceptionId] = useState<string | null>(null);
  // A primed item handed off from the repair overlay while NO session was open.
  // Practice needs a session, but discarding the id here stranded the repair
  // episode in `treatment` forever (it is never reused). Stash it, route the
  // learner to session start, and resume the primed retry when a session begins.
  const [pendingPrimedItemId, setPendingPrimedItemId] = useState<string | null>(null);
  // Same stash-and-resume for a guided redo begun with NO session open:
  // start_guided_redo has already committed the repair episode to treatment on
  // the redo item, so dropping the DTO here would strand that episode exactly
  // like a discarded primed handoff. Stash it, route to session start, resume.
  const [pendingRedo, setPendingRedo] = useState<GuidedRedoDto | null>(null);
  const startupStartedRef = useRef(false);
  // Whether the practice screen is currently a teach-back conversation. Only
  // PracticeScreen knows the item's mode; it reports it up so the
  // command-palette ask path can refuse to open the tutor mid-transcript.
  const teachBackActiveRef = useRef(false);
  // Practice reports whether its diagnostic contract has been verified and
  // permits tutor assistance. Default closed so command-palette Ask cannot
  // race the mount-time contract RPC.
  const practiceAskAllowedRef = useRef(false);
  const onTeachBackActive = useCallback((active: boolean) => {
    teachBackActiveRef.current = active;
  }, []);
  const onPracticeAskAllowed = useCallback((allowed: boolean) => {
    practiceAskAllowedRef.current = allowed;
  }, []);

  const onError = useCallback((message: string) => setToast(message), []);
  const onPaletteEntities = useCallback((ids: { inspectIds: string[]; practiceItemIds: string[] }) => {
    setPaletteEntityIds(ids.inspectIds);
    setPalettePracticeItemIds(ids.practiceItemIds);
  }, []);

  const loadInitialVault = useCallback(async () => {
    setStartupError(null);
    try {
      const appSnapshot = await api.loadVault();
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
    } catch (error) {
      setStartupError(errorMessage(error, "Could not load the LearnLoop vault."));
    }
  }, []);

  useEffect(() => {
    if (startupStartedRef.current) return;
    startupStartedRef.current = true;
    void loadInitialVault();
  }, [loadInitialVault]);

  useEffect(() => {
    let disposed = false;
    let unlisten: (() => void) | undefined;
    listen<VaultFilesChangedEvent>("learnloop://vault-files-changed", ({ payload }) => {
      // Files changed on disk: every cached read may be stale. Data is kept so
      // mounted screens repaint from it while they revalidate.
      if (payload.refresh.mode !== "noop") invalidateAllQueries();
      notifyQueueChanged();
      if (payload.refresh.error) {
        onError(`Vault refresh failed: ${payload.refresh.error.message}`);
        return;
      }
      if (payload.refresh.mode === "full") {
        const next = payload.refresh.snapshot;
        if (next) {
          setAlgoConfig(next.config);
          setSnapshot(next);
        } else {
          onError("Vault refreshed, but the watcher returned no application snapshot.");
        }
        return;
      }
      if (typeof payload.refresh.practiceItemCount === "number") {
        const practiceItemCount = payload.refresh.practiceItemCount;
        setSnapshot((current) =>
          current?.vault
            ? {
                ...current,
                vault: {
                  ...current.vault,
                  counts: {
                    ...current.vault.counts,
                    practiceItems: practiceItemCount
                  }
                }
              }
            : current
        );
      }
    })
      .then((stop) => {
        if (disposed) stop();
        else unlisten = stop;
      })
      .catch((error) => onError(errorMessage(error, "Could not watch this vault for changes.")));
    return () => {
      disposed = true;
      unlisten?.();
    };
  }, [onError]);

  // Nav badge counts. Event-driven, never polled: it refreshes when a vault is
  // opened or switched, when the learner moves between tabs (so acting on a
  // queue updates its badge on the way out), and on the same `queue-changed`
  // signal the file watcher and the review surfaces already broadcast. The RPC
  // is a handful of indexed COUNTs, which is what makes hanging it off tab
  // changes affordable.
  const vaultRoot = snapshot?.vault?.root ?? null;
  useEffect(() => {
    if (!vaultRoot) {
      setReviewCounts(null);
      return;
    }
    let disposed = false;
    const refresh = () => {
      api.getReviewCounts()
        .then((counts) => {
          if (!disposed) setReviewCounts(counts);
        })
        // Badges are decoration. A count that fails to load leaves the previous
        // number in place and stays quiet — it must never raise a toast over a
        // screen the learner is working in.
        .catch(() => undefined);
    };
    refresh();
    const unsubscribe = subscribeQueueChanged(refresh);
    return () => {
      disposed = true;
      unsubscribe();
    };
  }, [vaultRoot, tab]);

  const navBadges = useMemo<NavBadgeCounts>(
    () =>
      reviewCounts
        ? { proposals: reviewCounts.proposalsBadge, maintain: reviewCounts.maintainBadge }
        : {},
    [reviewCounts]
  );

  useEffect(() => {
    localStorage.setItem("learnloop.tab", tab);
  }, [tab]);

  // Record every activated vault (startup load, chip switches, NewVaultWizard —
  // all update snapshot.vault.root) into the nav chip's recents dropdown. Uses
  // the canonical root the backend returned, not the raw picked string.
  useEffect(() => {
    const root = snapshot?.vault?.root;
    if (root) recordRecentVault(root);
  }, [snapshot?.vault?.root]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const textTarget = isTypingTarget(event.target);
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "p") {
        event.preventDefault();
        setPaletteOpen(true);
        return;
      }
      if (event.altKey && event.key.toLowerCase() === "s") {
        event.preventDefault();
        setSettingsOpen(true);
        return;
      }
      if (!textTarget && event.key === ":") {
        event.preventDefault();
        setPaletteOpen(true);
        return;
      }
      if (textTarget) return;
      if (event.altKey && /^[0-9]$/.test(event.key)) {
        const next = navTabs.find((candidate) => candidate.key === event.key);
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
      return {
        answer: localDraft.answerMd,
        hints: localDraft.hintsUsed,
        submissionId: localDraft.submissionId,
        teachBack: null
      };
    }
    const checkpoint = session?.checkpoint;
    if (!checkpoint || checkpoint.currentPracticeItemId !== practiceItemId) {
      return { answer: "", hints: 0, submissionId: null, teachBack: null };
    }
    return {
      answer: checkpoint.currentAnswer ?? "",
      hints: checkpoint.hintsUsed,
      submissionId: checkpoint.submissionId ?? null,
      teachBack: checkpoint.teachBack ?? null
    };
  }, [session, practiceItemId, localDraft]);
  const subjectOptions = useMemo(
    () => (snapshot?.vault?.subjects ?? []).map((id) => ({ id, title: id })),
    [snapshot?.vault?.subjects]
  );
  const manualGrading = snapshot?.health.ai?.manualGrading ?? false;
  // In manual mode the sidecar reports ready=true (it's an intentional choice,
  // not an outage) — but practice screens must still start in self-grade mode.
  const gradingReady = (snapshot?.health.ai?.ready ?? snapshot?.health.codex.ready ?? false) && !manualGrading;
  const gradingProvider = snapshot?.health.ai?.activeProvider ?? "codex";
  // The settings chip is green when the configured backend has no errors/missing
  // fields — every routed provider is ready (settingsReady), or grading is
  // intentionally manual — rather than tracking grading-only readiness. Falls
  // back to active-provider readiness on older sidecars without settingsReady.
  const settingsHealthy =
    manualGrading ||
    (snapshot?.health.ai?.settingsReady ??
      snapshot?.health.ai?.ready ??
      snapshot?.health.codex.ready ??
      false);

  const applyHealth = useCallback((health: RuntimeHealth) => {
    setSnapshot((current) => (current ? { ...current, health } : current));
  }, []);

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
        onError(errorMessage(error, "Could not change the grading provider."));
      }
    },
    [onError]
  );

  function beginSession(next: SessionSnapshot) {
    setTodayNoGoalBannerDismissed(false);
    setSession(next);
    setTab("today");
    if (pendingRedo) {
      // Resume the guided redo that was waiting on a session: its episode is
      // already committed to this item as the primed surface.
      setPrimedRetry(true);
      setRedoContext(pendingRedo);
      setPracticeItemId(pendingRedo.practiceItemId);
      setPendingRedo(null);
      setTodayStage("practice");
      return;
    }
    if (pendingPrimedItemId) {
      // Resume the repair handoff that was waiting on a session: open the
      // stashed primed retry directly instead of the queue.
      setPrimedRetry(true);
      setPracticeItemId(pendingPrimedItemId);
      setPendingPrimedItemId(null);
      setTodayStage("practice");
      return;
    }
    setTodayStage("queue");
  }

  function openPractice(id: string) {
    if (!session) {
      setTab("start");
      setToast("Start a session before opening practice.");
      return;
    }
    setPrimedRetry(false);
    setRedoContext(null);
    setAskTarget(null);
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
    setRedoContext(null);
    setAskTarget(null);
    setPracticeItemId(id);
    setTab("today");
    setTodayStage("practice");
  }

  // Fix 3: reuse the primed-retry plumbing, but carry the redo context so
  // PracticeScreen locks the preserved prefix and submits the composed answer.
  function openGuidedRedo(redo: GuidedRedoDto) {
    if (!session) {
      // The redo's episode is already committed server-side; stash the context
      // and resume it when a session begins (mirrors pendingPrimedItemId).
      setPendingRedo(redo);
      setTab("start");
      setToast("Start a session to begin the redo.");
      return;
    }
    setPrimedRetry(true);
    setRedoContext(redo);
    setAskTarget(null);
    setPracticeItemId(redo.practiceItemId);
    setTab("today");
    setTodayStage("practice");
  }

  function openFeedback(id: string) {
    setPrimedRetry(false);
    setRedoContext(null);
    setAttemptId(id);
    setTodayStage("feedback");
  }

  function openBlockReview(blockEnd: ProbeBlockEndDto, learningObjectId: string, learningObjectTitle: string) {
    setBlockReview({ blockEnd, learningObjectId, learningObjectTitle });
    setTodayStage("blockReview");
  }

  // "View in Library" from the feedback source panel: open that vault file.
  function openLibraryFile(path: string) {
    setLibraryFilePath(path);
    setTab("library");
  }

  function clearLocalCheckpoint(identity?: { practiceItemId: string; submissionId: string }) {
    setSession((current) => {
      if (!current) return current;
      if (!identity) return { ...current, checkpoint: null };
      const checkpoint = current.checkpoint;
      // The in-memory SessionSnapshot is only refreshed at startup and can
      // predate this item's generated retry key. The sidecar has already
      // compared both item + key atomically; matching the snapshot's item is
      // therefore sufficient, while a newer different item remains intact.
      if (checkpoint?.currentPracticeItemId === identity.practiceItemId) {
        return { ...current, checkpoint: null };
      }
      return current;
    });
    setLocalDraft((current) => {
      if (!identity) return null;
      return current?.practiceItemId === identity.practiceItemId
        && current.submissionId === identity.submissionId
        ? null
        : current;
    });
  }

  function endSession(summary: SessionEndSummary) {
    setTodayNoGoalBannerDismissed(false);
    setSession(null);
    setLocalDraft(null);
    setPracticeItemId(null);
    setRedoContext(null);
    setAttemptId(null);
    setBlockReview(null);
    // Calibration attaches to the practice session — drop the overlay with it.
    setCalibrationSessionId(null);
    setTodayStage("queue");
    setTab("start");
    // The finish HUD replaces the plain toast: it overlays the (now reset)
    // Start screen, reads out the summary, and holds until the learner dismisses.
    setFinishSummary(summary);
  }

  function gotoTab(next: TopTab) {
    // Golden Path is gated off (see SHOW_GOLDEN_PATH); refuse the target rather
    // than land on a tab with no button back. Overlay targets still dispatch.
    if (next === "golden" && !SHOW_GOLDEN_PATH) return;
    if (next === "errors") {
      setSettingsOpen(false);
      setReviewOpen(true);
      return;
    }
    if (next === "settings") {
      setReviewOpen(false);
      setSettingsOpen(true);
      return;
    }
    setSettingsOpen(false);
    setReviewOpen(false);
    setTab(next);
    if (next !== "today") setTodayStage("queue");
  }

  // Launch the F6 Repair flow (§4.10) for a misconception. Shared entry point
  // for Review's working hypotheses and (once wired) Feedback / Today.
  function openRepair(misconceptionId: string) {
    setRepairMisconceptionId(misconceptionId);
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
      if (!practiceAskAllowedRef.current) {
        setToast("ask-tutor is unavailable until diagnostic safeguards are verified, and stays disabled during diagnostic checks.");
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

  function gotoProposalBatch(patchId: string) {
    setProposalFocusPatchId(patchId);
    setTab("proposals");
  }

  const changeVault = useCallback(
    async (path: string) => {
      let selected = false;
      try {
        await api.selectVault(path);
        selected = true;
        // Cached reads belong to the previous vault; drop them before any
        // screen can read through the cache for the new one.
        clearQueryCache();
        // From this point onward every command targets the new vault. Do not
        // leave the previous vault's snapshot or overlays interactive while the
        // replacement snapshot is loading (or if that second read fails).
        setSnapshot(null);
        setSession(null);
        setStartupError(null);
        setSettingsOpen(false);
        setReviewOpen(false);
        setInspectorId(null);
        setAskTarget(null);
        setOpenSource(null);
        setQuickAddOpen(false);
        setRepairMisconceptionId(null);
        setConfirmOpen(false);
        setWhyTriage(null);
        setAdjudicateOpen(false);
        setPaletteOpen(false);
        setFinishSummary(null);
        const next = await api.loadVault();
        setAlgoConfig(next.config);
        setSnapshot(next);
        setStartupError(null);
        setSession(next.activeSession ?? null);
        setTodayNoGoalBannerDismissed(false);
        setPracticeItemId(null);
        setRedoContext(null);
        setAttemptId(null);
        setBlockReview(null);
        setInspectorId(null);
        setSettingsOpen(false);
        setCalibrationSessionId(null);
        setRepairMisconceptionId(null);
        setPendingPrimedItemId(null);
        setIngestJobId(null);
        setProposalFocusPatchId(null);
        setTodayStage("queue");
        setTab("start");
      } catch (error) {
        const message = errorMessage(error, "Could not open that vault.");
        if (selected) {
          // Selection committed in the backend, so restoring the old snapshot
          // would create a cross-vault UI/data mismatch. Keep the app blocked
          // on a retryable load surface for the newly selected vault instead.
          setStartupError(message);
        } else {
          // A path that could not be selected (deleted/renamed directory, bad
          // vault) drops out of recents; the still-active old snapshot is safe.
          removeRecentVault(path);
        }
        onError(message);
        throw error;
      }
    },
    [onError]
  );

  function renderBody() {
    if (!snapshot) {
      if (startupError) {
        return (
          <div className="placeholder-screen" role="alert">
            <div className="toast" style={{ maxWidth: 620 }}>
              <div>{startupError}</div>
              <button type="button" className="queue-row" style={{ marginTop: 10 }} onClick={() => void loadInitialVault()}>
                retry vault load
              </button>
            </div>
          </div>
        );
      }
      return <EmptyPlaceholder title="Loading LearnLoop vault" />;
    }
    // The exam overlay pre-empts the tab body — it's entered only from the goal
    // banner and returns to the today tab on exit.
    if (examGoalId) {
      return <ExamScreen goalId={examGoalId} onExit={exitExam} onError={onError} />;
    }
    // The golden-path run pre-empts the body (exam/calibration precedent) while a
    // run is active. Selecting the Golden Path tab with no active run renders the
    // offline fixture surface.
    if (goldenRunId && SHOW_GOLDEN_PATH) {
      return (
        <GoldenPathScreen
          runId={goldenRunId}
          onExit={() => {
            setGoldenRunId(null);
            gotoTab("today");
          }}
          onWhy={setWhyTriage}
          onError={onError}
        />
      );
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
          onOpenRepair={openRepair}
          onGuidedRedo={openGuidedRedo}
          onExit={exitCalibration}
          onError={onError}
        />
      );
    }
    if (tab === "start") {
      return (
        <StartScreen
          onBegin={beginSession}
          onError={onError}
          vault={snapshot.vault}
          streak={snapshot.streak}
          onNewVault={() => setNewVaultOpen(true)}
        />
      );
    }
    if (tab === "today") {
      if (todayStage === "practice" && session && practiceItemId) {
        return (
          <PracticeScreen
            key={`${session.sessionId}:${practiceItemId}`}
            session={session}
            practiceItemId={practiceItemId}
            primed={primedRetry}
            redo={redoContext && redoContext.practiceItemId === practiceItemId ? redoContext : null}
            gradingReady={gradingReady}
            gradingProvider={gradingProvider}
            restoredAnswer={restored.answer}
            restoredHints={restored.hints}
            restoredSubmissionId={restored.submissionId}
            restoredTeachBack={restored.teachBack}
            onFeedback={openFeedback}
            onBlockEnd={openBlockReview}
            onContinueDiagnostic={openPractice}
            onBack={() => setTodayStage("queue")}
            onCheckpointCleared={clearLocalCheckpoint}
            onDraftSaved={onPracticeDraft}
            onTeachBackActive={onTeachBackActive}
            onAskAvailabilityChange={onPracticeAskAllowed}
            onInspect={setInspectorId}
            onAsk={setAskTarget}
            onError={onError}
          />
        );
      }
      if (todayStage === "blockReview" && session && blockReview) {
        return (
          <DiagnosticReviewScreen
            blockEnd={blockReview.blockEnd}
            learningObjectId={blockReview.learningObjectId}
            learningObjectTitle={blockReview.learningObjectTitle}
            sessionId={session.sessionId}
            onContinueDiagnostic={openPractice}
            onAsk={setAskTarget}
            onOpenRepair={openRepair}
            onGuidedRedo={openGuidedRedo}
            onBack={() => {
              setBlockReview(null);
              setTodayStage("queue");
            }}
            onError={onError}
          />
        );
      }
      if (todayStage === "feedback" && attemptId) {
        return (
          <FeedbackScreen
            attemptId={attemptId}
            sessionId={session?.sessionId ?? null}
            onOpenRepair={openRepair}
            onNext={() => setTodayStage("queue")}
            onBack={() => setTodayStage("queue")}
            onOpenNotes={() => gotoTab("library")}
            onPrimedRetry={openPrimedRetry}
            onGuidedRedo={openGuidedRedo}
            onOpenPractice={openPractice}
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
          onOpenPrimedPractice={openPrimedRetry}
          onAsk={setAskTarget}
          onPaletteEntities={onPaletteEntities}
          onEndSession={endSession}
          onInspect={setInspectorId}
          onTakeExam={openExam}
          noGoalBannerDismissed={todayNoGoalBannerDismissed}
          onDismissNoGoalBanner={() => setTodayNoGoalBannerDismissed(true)}
          onGotoReader={() => setTab("reader")}
          readerSeedingActive={
            (snapshot.vault?.counts.learningObjects ?? 0) > 0 &&
            (snapshot.vault?.counts.practiceItems ?? 0) === 0
          }
          onError={onError}
        />
      );
    }
    if (tab === "graph") {
      return <GraphScreen onInspect={setInspectorId} onError={onError} />;
    }
    if (tab === "ingest") {
      return (
        <IngestScreen
          jobId={ingestJobId}
          onJobIdChange={setIngestJobId}
          onProceedToPropose={gotoProposalBatch}
          onCreateStudyMap={() => {
            setQuickAddGuided(false);
            setQuickAddDefaultSubjectId(null);
            setQuickAddOpen(true);
          }}
          guideActive={ingestGuideActive}
          onDismissGuide={() => setIngestGuideActive(false)}
        />
      );
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
          onInspect={setInspectorId}
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
          focusPatchId={proposalFocusPatchId}
          onFocusConsumed={() => setProposalFocusPatchId(null)}
        />
      );
    }
    if (tab === "registry") {
      return (
        <RegistryReviewScreen
          subjectId={registrySubjectId}
          subjects={subjectOptions}
          onSelectSubject={setRegistrySubjectId}
          onOpenSource={(extractionId, spanId, entityType, entityId) =>
            // ING M8 (§11): opens originate from the entity provenance panel embedded
            // in the registry cards, so tag exposure with the provenance_panel context.
            setOpenSource({ extractionId, spanId, context: "provenance_panel", entityType, entityId })
          }
        />
      );
    }
    if (tab === "golden") {
      // The real front door: discovery → compose → review → confirm. The
      // offline fixture demo stays reachable behind an explicit toggle.
      if (goldenDemo) {
        return (
          <GoldenPathScreen
            runId={null}
            onExit={() => setGoldenDemo(false)}
            onWhy={setWhyTriage}
            onOpenConfirm={() => setConfirmOpen(true)}
            onError={onError}
          />
        );
      }
      return (
        <GoldenPathSetup
          onRunStarted={(runId) => setGoldenRunId(runId)}
          onOpenDemo={() => setGoldenDemo(true)}
          onError={onError}
        />
      );
    }
    if (tab === "reader") {
      return <ReaderScreen onError={onError} />;
    }
    if (tab === "maintain") {
      return (
        <MaintenanceScreen
          subjects={subjectOptions}
          onError={onError}
          onInspect={setInspectorId}
          onOpenAdjudication={() => setAdjudicateOpen(true)}
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
        aiReady={settingsHealthy}
        aiManual={manualGrading}
        vaultRoot={snapshot?.vault?.root}
        onSelectVault={(path) => void changeVault(path).catch(() => undefined)}
        settingsOpen={settingsOpen}
        badges={navBadges}
      >
        {toast && !settingsOpen ? (
          <div className="toast" role="status" aria-live="polite" aria-atomic="true" onClick={() => setToast(null)}>
            {toast}
          </div>
        ) : null}
        {renderBody()}
      </TerminalFrame>
      {settingsOpen ? (
        <SettingsOverlay
          manualGrading={manualGrading}
          onSelectGradingProvider={changeGradingProvider}
          onHealthChanged={applyHealth}
          onToast={setToast}
          onError={onError}
          onClose={() => {
            setSettingsOpen(false);
            setToast(null);
          }}
          notification={toast}
          onDismissNotification={() => setToast(null)}
        />
      ) : null}
      {reviewOpen ? (
        <ReviewScreen
          onClose={() => setReviewOpen(false)}
          onError={onError}
          onRepair={(misconceptionId) => {
            setReviewOpen(false);
            openRepair(misconceptionId);
          }}
          onInspect={setInspectorId}
          inspectorOpen={Boolean(inspectorId)}
        />
      ) : null}
      <InspectorOverlay
        entityId={inspectorId}
        onClose={() => setInspectorId(null)}
        onInspect={setInspectorId}
        onError={onError}
      />
      <AskOverlay target={askTarget} onClose={() => setAskTarget(null)} onToast={setToast} />
      {openSource ? (
        <OpenInSource
          extractionId={openSource.extractionId}
          spanId={openSource.spanId}
          context={openSource.context}
          entityType={openSource.entityType}
          entityId={openSource.entityId}
          onClose={() => setOpenSource(null)}
        />
      ) : null}
      {quickAddOpen ? (
        <QuickAddDialog
          subjects={subjectOptions}
          defaultSubjectId={quickAddDefaultSubjectId ?? registrySubjectId ?? subjectOptions[0]?.id ?? null}
          guided={quickAddGuided}
          onClose={() => {
            setQuickAddOpen(false);
            setQuickAddGuided(false);
            setQuickAddDefaultSubjectId(null);
          }}
          onEnqueued={() => {
            setQuickAddOpen(false);
            setQuickAddGuided(false);
            setQuickAddDefaultSubjectId(null);
            setIngestGuideActive(true);
            setIngestJobId(null);
            setTab("ingest");
            setToast("Study map building — track it in Ingest");
          }}
        />
      ) : null}
      {newVaultOpen ? (
        <NewVaultWizard
          onClose={() => setNewVaultOpen(false)}
          onActivateVault={changeVault}
          onContinueInIngest={(subjectId) => {
            setQuickAddDefaultSubjectId(subjectId);
            setQuickAddGuided(true);
            setIngestGuideActive(true);
            setTab("ingest");
            setQuickAddOpen(true);
          }}
          onGotoTab={gotoTab}
          onToast={setToast}
          onError={onError}
        />
      ) : null}
      {repairMisconceptionId ? (
        <RepairScreen
          misconceptionId={repairMisconceptionId}
          sessionId={session?.sessionId ?? null}
          onClose={() => setRepairMisconceptionId(null)}
          onPractice={(practiceItemId) => {
            // Check the session BEFORE unmounting the overlay: openPrimedRetry
            // bails without a session, and losing the primed item id here used
            // to strand the freshly committed episode in `treatment`.
            if (!session) {
              setPendingPrimedItemId(practiceItemId);
              setRepairMisconceptionId(null);
              setTab("start");
              setToast("Start a session to practice the primed item — it will open automatically.");
              return;
            }
            setRepairMisconceptionId(null);
            openPrimedRetry(practiceItemId);
          }}
          onProbe={(practiceItemId) => {
            // A causal disambiguation probe is a measurement, not a primed
            // retry: it opens cold so the attempt carries no repair context.
            setRepairMisconceptionId(null);
            openPractice(practiceItemId);
          }}
          onError={onError}
        />
      ) : null}
      {confirmOpen ? (
        <ExemplarConfirmDialog
          onConfirmed={(runId) => {
            setConfirmOpen(false);
            setGoldenRunId(runId);
            setTab("golden");
          }}
          onClose={() => setConfirmOpen(false)}
          onError={onError}
        />
      ) : null}
      {whyTriage ? <WhyDiagnosisOverlay triage={whyTriage} onClose={() => setWhyTriage(null)} /> : null}
      {adjudicateOpen ? (
        <AdjudicationOverlay onClose={() => setAdjudicateOpen(false)} onError={onError} />
      ) : null}
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
        onOpenAdjudication={() => setAdjudicateOpen(true)}
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
