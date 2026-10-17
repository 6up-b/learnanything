// Reader workbench RW2a in the Reader: the working posture (spec §5.1; UX §3.1,
// §5.1, S1/S2/S6/S7/S13).
//
// The problems worked on this source (open or set aside, never submitted)
// show as ✎ marks beside their passages and as lines in the rail; RW6a's
// recap reads the same list (`workbench.for_source`). "Work through this" on
// a selection opens a session at once with the verbatim selection as the
// stem, while the exercise import binds it in the background; on an imported
// exercise it opens bound. The workbench takes half the window (resizable,
// remembered on this device, at least 480 px), or the whole screen below the
// 1,040 px breakpoint with the book in a sheet. Leave, Submit and Abandon
// collapse back into reading at the problem's passage.
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type {
  ReaderImportExerciseInput,
  SourceLibraryCard,
  WorkbenchSessionDto,
  WorkbenchSubmitDto,
  WorkbenchSummaryDto,
} from "../../api/dto";
import { errorMessage } from "../../errors";
import {
  SPLIT_STEP,
  clampSplitWidth,
  defaultSplitWidth,
  isNarrow,
  readSplitWidth,
  writeSplitWidth,
} from "../workbench/splitWidth";

export interface ReaderWorkbenchProps {
  /** The app's open practice session, when there is one (the submit uses it). */
  practiceSessionId?: string | null;
  /** A submit hands its attempt to the shell, with the way back to its passage. */
  onSubmitted?: (result: WorkbenchSubmitDto, at: { card: SourceLibraryCard; spanId: string }) => void;
  /** Back from feedback: open this attempt's problem read-only (UX S6). */
  initialAttemptId?: string | null;
  /** The read-only problem was shown (the shell forgets the attempt). */
  onInitialAttemptShown?: () => void;
}

export interface ActiveWorkbench {
  session: WorkbenchSessionDto;
  readOnly: boolean;
  /** Opened by the learner just now: step 1 takes the caret. */
  autoFocus: boolean;
}

export interface ReaderWorkbench {
  enabled: boolean;
  sessions: WorkbenchSummaryDto[];
  active: ActiveWorkbench | null;
  /** The receipt after Abandon: "abandoned · your steps are kept · reopen". */
  abandoned: WorkbenchSessionDto | null;
  width: number;
  narrow: boolean;
  sheetOpen: boolean;
  setSheetOpen: (open: boolean) => void;
  resizeBy: (delta: number) => void;
  setWidth: (width: number) => void;
  openSelection: (input: { stemMd: string; spanIds: string[]; importRequest: ReaderImportExerciseInput }) => Promise<void>;
  openItem: (input: { practiceItemId: string; stemMd: string; spanIds: string[] }) => Promise<void>;
  resume: (sessionId: string) => Promise<void>;
  reopenAbandoned: () => Promise<void>;
  /** The session changed inside the workbench (the book, the binding). */
  update: (session: WorkbenchSessionDto) => void;
  /** Collapse back into reading; returns the passage to return to. */
  close: (session: WorkbenchSessionDto | null, options?: { abandoned?: boolean }) => string | null;
  submitted: (result: WorkbenchSubmitDto) => void;
}

function newKey(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `k${Date.now()}${Math.random()}`;
}

export function useReaderWorkbench(input: {
  enabled: boolean;
  extractionId: string | null;
  card: SourceLibraryCard | null;
  props?: ReaderWorkbenchProps;
  onError: (message: string) => void;
}): ReaderWorkbench {
  const { enabled, extractionId, card, onError } = input;
  const props = input.props;
  const [sessions, setSessions] = useState<WorkbenchSummaryDto[]>([]);
  const [active, setActive] = useState<ActiveWorkbench | null>(null);
  const [abandoned, setAbandoned] = useState<WorkbenchSessionDto | null>(null);
  const [windowWidth, setWindowWidth] = useState(() => (typeof window === "undefined" ? 1600 : window.innerWidth));
  const [width, setWidthState] = useState(() => clampSplitWidth(readSplitWidth() ?? defaultSplitWidth(windowWidth), windowWidth));
  const [sheetOpen, setSheetOpen] = useState(false);
  const extractionRef = useRef(extractionId);
  extractionRef.current = extractionId;

  const refresh = useCallback(async () => {
    const current = extractionRef.current;
    if (!enabled || !current) return;
    try {
      const result = await api.workbenchForSource({ extractionId: current });
      if (extractionRef.current === current) setSessions(result.sessions);
    } catch {
      // The marks are a convenience: without them the source still reads.
    }
  }, [enabled]);

  useEffect(() => {
    setSessions([]);
    setActive(null);
    setAbandoned(null);
    void refresh();
  }, [extractionId, refresh]);

  // Back from feedback (UX S6): the submitted problem, read-only.
  // It opens once the source it belongs to is open, and only once.
  const initialAttemptId = props?.initialAttemptId ?? null;
  const openedAttemptRef = useRef<string | null>(null);
  useEffect(() => {
    if (!enabled || !initialAttemptId || !extractionId || openedAttemptRef.current === initialAttemptId) return;
    openedAttemptRef.current = initialAttemptId;
    void api.workbenchSessionForAttempt({ attemptId: initialAttemptId })
      .then((result) => {
        const session = result.session;
        if (session && extractionRef.current === extractionId && session.extractionId === extractionId) {
          setActive({ session, readOnly: true, autoFocus: false });
          props?.onInitialAttemptShown?.();
        }
      })
      .catch(() => undefined);
  }, [enabled, initialAttemptId, extractionId]);

  useEffect(() => {
    if (!enabled) return undefined;
    const onResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [enabled]);

  const setWidth = useCallback((next: number) => {
    const clamped = clampSplitWidth(next, window.innerWidth);
    setWidthState(clamped);
    writeSplitWidth(clamped);
  }, []);
  const resizeBy = useCallback((delta: number) => {
    setWidthState((current) => {
      const clamped = clampSplitWidth(current + delta, window.innerWidth);
      writeSplitWidth(clamped);
      return clamped;
    });
  }, []);

  const begin = useCallback((session: WorkbenchSessionDto, readOnly = false) => {
    setAbandoned(null);
    setSheetOpen(false);
    setActive({ session, readOnly, autoFocus: !readOnly });
  }, []);

  const openSelection = useCallback(async (request: { stemMd: string; spanIds: string[]; importRequest: ReaderImportExerciseInput }) => {
    if (!enabled || !extractionId) return;
    try {
      const result = await api.workbenchOpen({
        origin: "reader", entry: "work_through", stemMd: request.stemMd, extractionId,
        spanIds: request.spanIds, importRequest: request.importRequest, clientIdempotencyKey: newKey(),
      });
      begin(result.session);
    } catch (error) {
      onError(errorMessage(error, "Couldn't open the workbench."));
    }
  }, [begin, enabled, extractionId, onError]);

  const openItem = useCallback(async (request: { practiceItemId: string; stemMd: string; spanIds: string[] }) => {
    if (!enabled || !extractionId) return;
    try {
      const result = await api.workbenchOpen({
        origin: "reader", entry: "work_through", practiceItemId: request.practiceItemId, stemMd: request.stemMd,
        extractionId, spanIds: request.spanIds, clientIdempotencyKey: newKey(),
      });
      begin(result.session);
    } catch (error) {
      onError(errorMessage(error, "Couldn't open the workbench."));
    }
  }, [begin, enabled, extractionId, onError]);

  const resume = useCallback(async (sessionId: string) => {
    try {
      const read = await api.workbenchGet({ sessionId });
      const session = read.session.status === "abandoned" ? (await api.workbenchReopen({ sessionId })).session : read.session;
      begin(session);
    } catch (error) {
      onError(errorMessage(error, "Couldn't reopen this problem."));
    }
  }, [begin, onError]);

  const reopenAbandoned = useCallback(async () => {
    if (!abandoned) return;
    await resume(abandoned.sessionId);
  }, [abandoned, resume]);

  const update = useCallback((session: WorkbenchSessionDto) => {
    setActive((current) => (current && current.session.sessionId === session.sessionId ? { ...current, session } : current));
  }, []);

  const close = useCallback((session: WorkbenchSessionDto | null, options?: { abandoned?: boolean }) => {
    const target = session ?? active?.session ?? null;
    setActive(null);
    setSheetOpen(false);
    setAbandoned(options?.abandoned && target ? target : null);
    void refresh();
    return target?.spanIds[0] ?? null;
  }, [active, refresh]);

  const submitted = useCallback((result: WorkbenchSubmitDto) => {
    const spanId = result.session.spanIds[0] ?? active?.session.spanIds[0] ?? "";
    setActive(null);
    void refresh();
    if (card && props?.onSubmitted) props.onSubmitted(result, { card, spanId });
  }, [active, card, props, refresh]);

  return {
    enabled,
    sessions,
    active,
    abandoned,
    width: clampSplitWidth(width, windowWidth),
    narrow: isNarrow(windowWidth),
    sheetOpen,
    setSheetOpen,
    resizeBy,
    setWidth,
    openSelection,
    openItem,
    resume,
    reopenAbandoned,
    update,
    close,
    submitted,
  };
}

export { SPLIT_STEP };
