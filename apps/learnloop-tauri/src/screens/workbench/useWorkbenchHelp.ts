// Reader workbench RW2b: one problem's checks and help (spec §5.2-5.6; UX
// §4.0, §5.4-5.8). Every model-backed action is a job: the press answers at
// once and the hook paces the reads (350 ms rising to 1.5 s); the read that
// returns a ready check or hint SHOWS it (the server marks it shown and
// counts it), so exactly what that read returns is rendered. Nothing a
// result does moves focus, animates or opens a dialog (W12): results land
// under their steps and the record line updates.
//
// Leaving (review F7): no read is sent once the workbench has gone (the
// lifecycle is checked after every wait, before every delivering read), and
// every check or hint still pending is cancelled, so it is never shown and
// counts nothing. A read already in flight when the learner leaves may have
// delivered its result: that result counts (the server showed it) and is
// never lost, because reopening the problem restores every shown check and
// hint (workbench.help_state).
//
// Unsaved work (review F8): when the latest edits cannot be saved, neither a
// check nor a hint nor a suggestion is asked for (they would read older
// steps than the ones on screen); the learner's choice on the ladder stays.
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type {
  CheckViewDto,
  HelpStyle,
  HelpSuggestionDto,
  HintShortcut,
  LadderRungDto,
  WorkbenchHelpJobDto,
  WorkbenchHelpResultDto,
  WorkbenchHelpStateDto,
  WorkbenchHintViewDto,
  WorkbenchRecordDto,
  WorkbenchRequestHelpInput,
  WorkbenchStepLabelsDto,
} from "../../api/dto";
import { errorMessage } from "../../errors";
import { DEFAULT_RUNGS } from "./helpModel";

const FIRST_POLL_MS = 350;
export const UNSAVED_HELP = "Your latest steps aren't saved yet, so help can't read them. They're safe in this window.";
const MAX_POLL_MS = 1500;

export interface LadderState {
  open: boolean;
  /** The step Help opened below (its chain id). */
  focusedStepId: string | null;
  chosen: number;
  /** The learner moved the choice: a late suggestion no longer moves it. */
  touched: boolean;
  suggestion: HelpSuggestionDto | null;
  rungs: LadderRungDto[];
  pending: boolean;
  steps: WorkbenchStepLabelsDto | null;
  notice: string | null;
}

export interface HelpNotice {
  /** The step the notice sits under (chain id), or null for the problem. */
  stepId: string | null;
  message: string;
}

export interface BridgeState {
  status: "pending" | "ready" | "none";
  line?: string;
  spanId?: string | null;
  extractionId?: string | null;
  /** RW2c review F1: the book a picked passage is in (absent on RW2b's bridge). */
  sourceId?: string | null;
  /** RW2c: the bridge row and how many other passages its logged draw kept
   *  ("another passage"); both absent unless the draw logged options. */
  assistId?: string;
  alternatives?: number;
}

/** RW2c: a bridge's draw fields, only when its row logged options, and the
 *  book its passage is in when the server names one (fix round 2, 7: a drawn
 *  or picked passage in another book opens there, initially and on resume).
 *  The server sends neither while workbench.passage_draw_enabled is off, so
 *  a bridge's state is then RW2b's. */
function drawnFields(value: { assistId?: string | null; alternatives?: number; sourceId?: string | null } | null | undefined): Partial<BridgeState> {
  return {
    ...(value?.alternatives && value.assistId ? { assistId: value.assistId, alternatives: value.alternatives } : {}),
    ...(value?.sourceId ? { sourceId: value.sourceId } : {}),
  };
}

export interface WorkbenchHelp {
  enabled: boolean;
  hintsEnabled: boolean;
  check: CheckViewDto | null;
  checkPending: boolean;
  checkNotice: string | null;
  ladder: LadderState;
  hints: WorkbenchHintViewDto[];
  hintPending: { stepId: string | null } | null;
  notice: HelpNotice | null;
  bridges: Record<string, BridgeState>;
  helpStyle: HelpStyle | null;
  storedHelpStyle: HelpStyle;
  runCheck: () => Promise<void>;
  openHelp: (focusedStepId: string | null) => void;
  closeHelp: () => void;
  choose: (level: number) => void;
  take: (level?: number) => Promise<void>;
  reply: (hint: WorkbenchHintViewDto, reply: { shortcut?: HintShortcut; text?: string; stepId?: string | null }) => Promise<void>;
  bookWay: (hint: WorkbenchHintViewDto) => Promise<void>;
  smallerStep: (hint: WorkbenchHintViewDto) => Promise<void>;
  answerDiscriminating: (hint: WorkbenchHintViewDto, answer: string) => Promise<void>;
  cancelHint: () => Promise<void>;
  setHelpStyle: (style: HelpStyle | null) => Promise<void>;
}

const closedLadder: LadderState = {
  open: false, focusedStepId: null, chosen: 1, touched: false, suggestion: null, rungs: DEFAULT_RUNGS,
  pending: false, steps: null, notice: null,
};

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function useWorkbenchHelp(options: {
  sessionId: string;
  enabled: boolean;
  hintsEnabled: boolean;
  storedHelpStyle: HelpStyle;
  readOnly?: boolean;
  /** Save the resting edits before a check or a hint reads the steps. */
  beforeRequest: () => Promise<boolean>;
  onRecord: (record: WorkbenchRecordDto) => void;
  /** RW2c: a delivered hint started its worked-example job. */
  onExampleJob?: (hintAssistId: string, jobId: string) => void;
  /** RW2c: the restored help state (its examples), as read on resume. */
  onHelpState?: (state: WorkbenchHelpStateDto) => void;
}): WorkbenchHelp {
  const { sessionId, enabled, hintsEnabled } = options;
  const [check, setCheck] = useState<CheckViewDto | null>(null);
  const [checkPending, setCheckPending] = useState(false);
  const [checkNotice, setCheckNotice] = useState<string | null>(null);
  const [ladder, setLadder] = useState<LadderState>(closedLadder);
  const [hints, setHints] = useState<WorkbenchHintViewDto[]>([]);
  const [hintPending, setHintPending] = useState<{ stepId: string | null; jobId?: string } | null>(null);
  const [notice, setNotice] = useState<HelpNotice | null>(null);
  const [bridges, setBridges] = useState<Record<string, BridgeState>>({});
  const [helpStyle, setHelpStyleState] = useState<HelpStyle | null>(null);
  const [storedHelpStyle, setStoredHelpStyle] = useState<HelpStyle>(options.storedHelpStyle);
  const alive = useRef(true);
  const generation = useRef(0);
  const onRecordRef = useRef(options.onRecord);
  onRecordRef.current = options.onRecord;
  const beforeRef = useRef(options.beforeRequest);
  beforeRef.current = options.beforeRequest;
  const exampleJobRef = useRef(options.onExampleJob);
  exampleJobRef.current = options.onExampleJob;
  const helpStateRef = useRef(options.onHelpState);
  helpStateRef.current = options.onHelpState;
  const hintJob = useRef<string | null>(null);
  /** Checks and hints asked for and not yet read to the end (cancelled on leaving). */
  const pendingJobs = useRef<Set<string>>(new Set());

  useEffect(() => {
    alive.current = true;
    const pending = pendingJobs.current;
    return () => {
      alive.current = false;
      for (const jobId of pending) void api.workbenchCancelHelp(jobId).catch(() => undefined);
      pending.clear();
    };
  }, []);

  // A resumed problem restores its last check and its hints (§5.1).
  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    void api.workbenchHelpState({ sessionId }).then((state) => {
      if (cancelled || !alive.current) return;
      setCheck(state.check);
      setHints(state.hints);
      setHelpStyleState(state.helpStyle);
      setStoredHelpStyle(state.storedHelpStyle);
      const restored: Record<string, BridgeState> = {};
      for (const hint of state.hints) {
        if (hint.bridge) restored[hint.assistId] = { status: "ready", line: hint.bridge.line, spanId: hint.bridge.spanId, extractionId: hint.bridge.extractionId, ...drawnFields(hint.bridge) };
      }
      setBridges(restored);
      helpStateRef.current?.(state);
    }).catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [enabled, sessionId]);

  const poll = useCallback(async (started: WorkbenchHelpJobDto, counted = false): Promise<WorkbenchHelpJobDto> => {
    let job = started;
    let wait = FIRST_POLL_MS;
    const jobId = job.jobId;
    if (counted && jobId && job.state === "pending") pendingJobs.current.add(jobId);
    try {
      while (job.jobId && job.state === "pending" && alive.current) {
        await sleep(wait);
        // F7: gone while waiting: no delivering read (the unmount cancels it).
        if (!alive.current) break;
        wait = Math.min(MAX_POLL_MS, Math.round(wait * 1.5));
        job = await api.workbenchHelpJob(job.jobId);
      }
    } finally {
      if (jobId && alive.current) pendingJobs.current.delete(jobId);
    }
    return job;
  }, []);

  const followBridge = useCallback(async (hintAssistId: string, jobId: string) => {
    setBridges((current) => ({ ...current, [hintAssistId]: { status: "pending" } }));
    try {
      const job = await poll(await api.workbenchHelpJob(jobId));
      const result = job.result;
      if (!alive.current) return;
      setBridges((current) => ({
        ...current,
        [hintAssistId]: result && result.status === "ready" && result.shown
          ? { status: "ready", line: result.line, spanId: result.spanId ?? null, extractionId: result.extractionId ?? null, ...drawnFields(result) }
          : { status: "none" },
      }));
    } catch {
      if (alive.current) setBridges((current) => ({ ...current, [hintAssistId]: { status: "none" } }));
    }
  }, [poll]);

  const runCheck = useCallback(async () => {
    if (!enabled || checkPending || options.readOnly) return;
    setCheckNotice(null);
    if (!(await beforeRef.current())) {
      setCheckNotice("Your latest steps aren't saved yet, so they can't be checked. They're safe in this window.");
      return;
    }
    setCheckPending(true);
    try {
      const started = await api.workbenchCheck({ sessionId });
      if (!alive.current) {
        if (started.jobId) void api.workbenchCancelHelp(started.jobId).catch(() => undefined);
        return;
      }
      const job = await poll(started, true);
      const result: WorkbenchHelpResultDto | null = job.result;
      if (!alive.current) return;
      if (job.state === "cancelled" || !result) return;
      if (result.check) setCheck(result.check);
      if (result.record) onRecordRef.current(result.record);
      if (result.status === "unchanged") setCheckNotice("Nothing changed since the last check, so it still stands.");
      else if (result.status !== "ready" || !result.shown) setCheckNotice(result.message ?? "Couldn't check your steps just now. They're saved — try again ↵");
    } catch (error) {
      if (alive.current) setCheckNotice(`Couldn't reach LearnLoop's model. Your steps are saved — try again ↵ (${errorMessage(error)})`);
    } finally {
      if (alive.current) setCheckPending(false);
    }
  }, [enabled, checkPending, options.readOnly, poll, sessionId]);

  const openHelp = useCallback((focusedStepId: string | null) => {
    if (!enabled || !hintsEnabled || options.readOnly) return;
    const mine = ++generation.current;
    setLadder({ ...closedLadder, open: true, focusedStepId, pending: true });
    void (async () => {
      try {
        if (!(await beforeRef.current())) {
          // F8: no suggestion read from older steps; the rungs stay to choose from.
          if (alive.current && generation.current === mine) {
            setLadder((current) => ({ ...current, pending: false, notice: UNSAVED_HELP }));
          }
          return;
        }
        const job = await poll(await api.workbenchSuggestHelp({ sessionId, focusedStepId }));
        if (!alive.current || generation.current !== mine) return;
        const result = job.result;
        setLadder((current) => {
          if (!current.open) return current;
          if (!result || result.status !== "ready" || !result.suggestion) {
            return { ...current, pending: false, notice: result?.message ?? null };
          }
          const suggestion = result.suggestion;
          return {
            ...current, pending: false, suggestion, rungs: suggestion.rungs.length ? suggestion.rungs : current.rungs,
            steps: result.steps ?? null, chosen: current.touched ? current.chosen : suggestion.level,
          };
        });
      } catch {
        if (alive.current && generation.current === mine) setLadder((current) => ({ ...current, pending: false }));
      }
    })();
  }, [enabled, hintsEnabled, options.readOnly, poll, sessionId]);

  const closeHelp = useCallback(() => {
    generation.current += 1;
    setLadder(closedLadder);
  }, []);

  const choose = useCallback((level: number) => {
    setLadder((current) => ({ ...current, chosen: Math.max(1, Math.min(5, level)), touched: true }));
  }, []);

  const requestHint = useCallback(async (input: Omit<WorkbenchRequestHelpInput, "sessionId">, stepId: string | null,
    flushed = false) => {
    if (hintJob.current) return;
    setNotice(null);
    if (!flushed && !(await beforeRef.current())) {
      // F8: as a check: nothing is asked for against steps older than the screen's.
      if (alive.current) setNotice({ stepId, message: UNSAVED_HELP });
      return;
    }
    if (!alive.current) return;
    setHintPending({ stepId });
    try {
      const started = await api.workbenchRequestHelp({ sessionId, ...input });
      if (!alive.current) {
        if (started.jobId) void api.workbenchCancelHelp(started.jobId).catch(() => undefined);
        return;
      }
      hintJob.current = started.jobId;
      const job = await poll(started, true);
      hintJob.current = null;
      if (!alive.current) return;
      const result = job.result;
      if (job.state === "cancelled" || !result) return;
      if (result.status === "ready" && result.shown && result.assistId) {
        const view: WorkbenchHintViewDto = {
          assistId: result.assistId, kind: result.kind ?? "next_step", level: result.level ?? 3,
          hintMd: result.hintMd ?? "", labels: result.labels ?? {},
          aboutStepId: result.steps?.aboutStepId ?? stepId, continueFromStepId: result.steps?.continueFromStepId ?? null,
          stepLine: result.stepLine ?? "", replies: result.replies ?? [], discriminatingAnswer: null, bridge: null,
          claims: result.claims ?? [],
          // Fix round 11: the server's CURRENT symbolic switch, carried to the view.
          symbolicEnabled: result.symbolicEnabled === true,
        };
        setHints((current) => [...current, view]);
        if (result.record) onRecordRef.current(result.record);
        if (result.message) setNotice({ stepId: view.aboutStepId, message: result.message });
        if (result.bridgeJobId) void followBridge(result.assistId, result.bridgeJobId);
        if (result.exampleJobId) exampleJobRef.current?.(result.assistId, result.exampleJobId);
      } else {
        setNotice({ stepId: result.steps?.aboutStepId ?? stepId, message: result.message ?? "Couldn't write a hint. Your steps are saved — try again ↵" });
      }
    } catch (error) {
      hintJob.current = null;
      if (alive.current) setNotice({ stepId, message: `Couldn't reach LearnLoop's model. Your steps are saved — try again ↵ (${errorMessage(error)})` });
    } finally {
      if (alive.current) setHintPending(null);
    }
  }, [followBridge, poll, sessionId]);

  const take = useCallback(async (level?: number) => {
    if (hintJob.current) return;
    const chosen = level ?? ladder.chosen;
    const { suggestion, focusedStepId } = ladder;
    if (!(await beforeRef.current())) {
      // F8: the ladder stays open with the learner's choice, and says why.
      if (alive.current) setLadder((current) => ({ ...current, chosen, touched: true, notice: UNSAVED_HELP }));
      return;
    }
    closeHelp();
    await requestHint({
      request: "more", takenLevel: chosen, offeredLevel: suggestion?.level ?? null,
      suggestionId: suggestion?.suggestionId ?? null, focusedStepId,
    }, ladder.steps?.aboutStepId ?? focusedStepId, true);
  }, [closeHelp, ladder, requestHint]);

  const reply = useCallback(async (hint: WorkbenchHintViewDto, value: { shortcut?: HintShortcut; text?: string; stepId?: string | null }) => {
    await requestHint({
      request: "feedback", answeredAssistId: hint.assistId, feedbackShortcut: value.shortcut,
      feedbackText: value.text?.trim() ? value.text : undefined, feedbackStepId: value.stepId ?? hint.aboutStepId,
    }, value.shortcut === "not_where_stuck" ? value.stepId ?? hint.aboutStepId : hint.aboutStepId);
  }, [requestHint]);

  const bookWay = useCallback(async (hint: WorkbenchHintViewDto) => {
    await requestHint({ request: "book_way", answeredAssistId: hint.assistId }, hint.aboutStepId);
  }, [requestHint]);

  const smallerStep = useCallback(async (hint: WorkbenchHintViewDto) => {
    await requestHint({ request: "smaller_step", answeredAssistId: hint.assistId }, hint.aboutStepId);
  }, [requestHint]);

  const answerDiscriminating = useCallback(async (hint: WorkbenchHintViewDto, answer: string) => {
    try {
      const recorded = await api.workbenchAnswerDiscriminating({ sessionId, questionAssistId: hint.assistId, answerMd: answer });
      if (!alive.current) return;
      setHints((current) => current.map((entry) => (entry.assistId === hint.assistId
        ? { ...entry, discriminatingAnswer: { answerMd: answer, message: recorded.message ?? "" } }
        : entry)));
    } catch (error) {
      if (alive.current) setNotice({ stepId: hint.aboutStepId, message: `Your answer wasn't recorded (${errorMessage(error)}); it's still in the box.` });
    }
  }, [sessionId]);

  const cancelHint = useCallback(async () => {
    const jobId = hintJob.current;
    if (!jobId) return;
    try {
      await api.workbenchCancelHelp(jobId);
    } catch {
      // A cancel that fails leaves the hint to land; it counts only if shown.
    }
  }, []);

  const setHelpStyle = useCallback(async (style: HelpStyle | null) => {
    const previous = helpStyle;
    setHelpStyleState(style);
    try {
      const saved = await api.workbenchSetHelpStyle({ sessionId, helpStyle: style });
      if (alive.current) {
        setHelpStyleState(saved.helpStyle);
        setStoredHelpStyle(saved.storedHelpStyle);
      }
    } catch {
      if (alive.current) setHelpStyleState(previous);
    }
  }, [helpStyle, sessionId]);

  return {
    enabled, hintsEnabled, check, checkPending, checkNotice, ladder, hints, hintPending, notice, bridges,
    helpStyle, storedHelpStyle, runCheck, openHelp, closeHelp, choose, take, reply, bookWay, smallerStep,
    answerDiscriminating, cancelHint, setHelpStyle,
  };
}
