// Reader workbench RW6a in the Reader: "Last time here" and Wrap up
// (spec §9.1; UX §3.1 "returning", §4.8). Kept out of ReaderScreen.
//
// * The card loads when a source opens (a pure read); recap_shown is
//   recorded once per visit when it is on screen; the learner's first scroll
//   or "continue" folds it to "last time ▸", which reopens it; dismiss hides
//   it for this source until the next session (recap_dismissed).
// * Wrap up: the rail footer's offer appears once the session has activity
//   (re-read when an Ask lands or a problem changes); `w` outside a text field
//   opens it in the rail and records wrap_up_opened.
// Off (the sidecar sends no `recap` key) nothing here asks the sidecar
// anything. Nothing takes focus, animates or opens a modal.
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type { ReaderRecapCardDto, ReaderRecapEvent, ReaderWrapUpDto } from "../../api/dto";
import { errorMessage } from "../../errors";

export interface ReaderRecapInput {
  /** recap.enabled, with a real source open. */
  enabled: boolean;
  /** recap.wrap_up_enabled, with a real source open. */
  wrapUpEnabled: boolean;
  extractionId: string | null;
  /** The Reader's current visit (RW1a's envelope). */
  visitId: () => string | null;
  /** The learner moved the page themselves (the first scroll folds the card). */
  readingMoved: boolean;
  /** Changes when something that may count as activity happened. */
  activityKey: string;
  onError: (message: string) => void;
}

export interface ReaderRecapCtl {
  recap: ReaderRecapCardDto | null;
  collapsed: boolean;
  expand: () => void;
  continueReading: () => void;
  dismiss: () => Promise<void>;
  /** The card is on screen: record recap_shown, once per visit. */
  noteShown: () => void;
  /** Re-read the card and Wrap up after an action changed them. */
  reload: () => void;
  wrapUpAvailable: boolean;
  wrapUpOpen: ReaderWrapUpDto | null;
  openWrapUp: () => Promise<void>;
  closeWrapUp: () => void;
}

export function useReaderRecap({
  enabled, wrapUpEnabled, extractionId, visitId, readingMoved, activityKey, onError,
}: ReaderRecapInput): ReaderRecapCtl {
  const [recap, setRecap] = useState<ReaderRecapCardDto | null>(null);
  const [collapsed, setCollapsed] = useState(false);
  const [wrapUpAvailable, setWrapUpAvailable] = useState(false);
  const [wrapUpOpen, setWrapUpOpen] = useState<ReaderWrapUpDto | null>(null);
  const [reloads, setReloads] = useState(0);
  const autoFoldedRef = useRef(false);
  const shownRef = useRef<string | null>(null);
  const extractionRef = useRef<string | null>(extractionId);
  extractionRef.current = extractionId;
  const visitIdRef = useRef(visitId);
  visitIdRef.current = visitId;

  const record = useCallback((event: ReaderRecapEvent) => {
    const extraction = extractionRef.current;
    if (!extraction) return Promise.resolve();
    return Promise.resolve(api.readerRecapEvent({ extractionId: extraction, visitId: visitIdRef.current(), event }))
      .then(() => undefined);
  }, []);

  // The card: read once per opened source (and again after an action).
  useEffect(() => {
    if (!enabled || !extractionId) {
      setRecap(null);
      return;
    }
    let cancelled = false;
    void Promise.resolve(api.readerRecap({ extractionId, visitId: visitIdRef.current() }))
      .then((result) => {
        if (cancelled || extractionRef.current !== extractionId) return;
        setRecap(result?.recap ?? null);
      })
      .catch(() => {
        /* The card is a convenience: the Reader reads on without it. */
      });
    return () => {
      cancelled = true;
    };
  }, [enabled, extractionId, reloads]);

  // A new source starts unfolded, with its own recap_shown.
  useEffect(() => {
    setCollapsed(false);
    autoFoldedRef.current = false;
    shownRef.current = null;
    setWrapUpOpen(null);
  }, [extractionId]);

  // The learner's first scroll folds the card; later scrolling leaves it as
  // they set it.
  useEffect(() => {
    if (!recap || !readingMoved || autoFoldedRef.current) return;
    autoFoldedRef.current = true;
    setCollapsed(true);
  }, [recap, readingMoved]);

  // Wrap up's availability (the activity rule is the sidecar's).
  useEffect(() => {
    if (!wrapUpEnabled || !extractionId) {
      setWrapUpAvailable(false);
      return;
    }
    let cancelled = false;
    void Promise.resolve(api.readerWrapUp({ extractionId, visitId: visitIdRef.current() }))
      .then((result) => {
        if (cancelled || extractionRef.current !== extractionId) return;
        setWrapUpAvailable(Boolean(result?.available));
      })
      .catch(() => {
        /* No offer when the read fails; reading goes on. */
      });
    return () => {
      cancelled = true;
    };
  }, [wrapUpEnabled, extractionId, activityKey, reloads]);

  const noteShown = useCallback(() => {
    const extraction = extractionRef.current;
    if (!extraction || !recap) return;
    const key = `${extraction}:${visitIdRef.current() ?? ""}`;
    if (shownRef.current === key) return;
    shownRef.current = key;
    void record("recap_shown").catch(() => undefined);
  }, [recap, record]);

  const expand = useCallback(() => setCollapsed(false), []);
  const continueReading = useCallback(() => {
    autoFoldedRef.current = true;
    setCollapsed(true);
  }, []);
  const dismiss = useCallback(async () => {
    setRecap(null);
    try {
      await record("recap_dismissed");
    } catch (error) {
      onError(errorMessage(error));
    }
  }, [record, onError]);
  const reload = useCallback(() => setReloads((count) => count + 1), []);

  const openWrapUp = useCallback(async () => {
    const extraction = extractionRef.current;
    if (!wrapUpEnabled || !extraction) return;
    try {
      const [result] = await Promise.all([
        api.readerWrapUp({ extractionId: extraction, visitId: visitIdRef.current() }),
        record("wrap_up_opened"),
      ]);
      if (extractionRef.current === extraction) setWrapUpOpen(result);
    } catch (error) {
      onError(errorMessage(error));
    }
  }, [wrapUpEnabled, record, onError]);
  const closeWrapUp = useCallback(() => setWrapUpOpen(null), []);

  // `w` (UX §3.5): outside text fields, without modifiers, once there is
  // something to wrap up.
  useEffect(() => {
    if (!wrapUpEnabled || !wrapUpAvailable || !extractionId) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "w" || event.altKey || event.ctrlKey || event.metaKey) return;
      const target = event.target;
      if (target instanceof HTMLElement && (target.isContentEditable || target.closest("input, textarea, select"))) return;
      event.preventDefault();
      void openWrapUp();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [wrapUpEnabled, wrapUpAvailable, extractionId, openWrapUp]);

  // Re-read an open Wrap up after an action, so its lines follow the chips.
  useEffect(() => {
    if (reloads === 0 || !wrapUpOpen || !extractionId) return;
    let cancelled = false;
    void Promise.resolve(api.readerWrapUp({ extractionId, visitId: visitIdRef.current() }))
      .then((result) => {
        if (!cancelled && extractionRef.current === extractionId) setWrapUpOpen(result);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
    // Only on an explicit reload.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reloads]);

  return {
    recap, collapsed, expand, continueReading, dismiss, noteShown, reload,
    wrapUpAvailable, wrapUpOpen, openWrapUp, closeWrapUp,
  };
}
