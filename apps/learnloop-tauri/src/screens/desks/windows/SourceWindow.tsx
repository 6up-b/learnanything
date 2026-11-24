// Book, PDF, paper, web and video windows (spec §7.1, §7.4): one Reader source pane per window, as a
// scoped instance. The Reader's hooks (selection, capture, margin cues, figures, the watch panel and
// its transcript) run unchanged inside it; what makes it one window among many is around it: its
// listeners go through the desk's router, its timers and media pause when it leaves the view, and it
// logs reading activity only while it is active or visible (desks/lifecycle.tsx).
import { useCallback, useMemo, useState, type ComponentProps } from "react";
import type { ContentRefDto, SourceLibraryCard } from "../../../api/dto";
import { ScopedSource } from "../source/ScopedSource";
import type { PenSurface, ReaderLens, ReaderWindowing, WindowInquiry } from "../source/types";
import type { WindowAsk } from "../../reader/useReaderInquiry";
import { PenLayer } from "../pen/PenLayer";
import type { VideoExtras } from "../../reader/YouTubeWatchPanel";
import type { ReadingPosition } from "../../reader/readingPosition";

export type ReaderPassThrough = Pick<ComponentProps<typeof ScopedSource>, "onCheckMe" | "onUseExercise" | "onTeachMe" | "workbench">;

export interface SourceStatus {
  title?: string;
  readingSpan?: string | null;
  progress?: number;
  where?: string | null;
  /** The reading the window's Reader shows (its book's current one): the window's reference names it. */
  reading?: string | null;
}

export function SourceWindow({
  content,
  card,
  libraryLoaded,
  startSpan,
  railHost,
  onStatus,
  onJumpReady,
  onMediaReady,
  onError,
  reader,
  lens = null,
  video = null,
  onInquiryReady,
  onAsk,
  onOpenPath,
  openNote = null,
  drainHost = null,
  onOpenBeside,
  onOpenPair,
  onSection,
  onPairKey,
  onTouched,
  onWorkOnPad,
  onSkimming,
  handoff = null,
}: {
  content: Extract<ContentRefDto, { kind: "source" | "video" }>;
  card: SourceLibraryCard | null;
  libraryLoaded: boolean;
  /** The passage to open at: the window's saved scroll anchor, or the target it was opened for. */
  startSpan: string | null;
  railHost: ReaderWindowing["railHost"];
  onStatus: (status: SourceStatus) => void;
  onJumpReady: (jump: ((spanId: string) => void) | null) => void;
  onMediaReady: (toggle: (() => void) | null) => void;
  onError: (message: string) => void;
  reader?: ReaderPassThrough;
  /** The goal lens over this reading (marks, callouts, dimming), or none. */
  lens?: ReaderLens | null;
  /** A video window's extras (RD10: chapters, ticks, the player's clock), or none. */
  video?: VideoExtras | null;
  /** The desk's way into the window's detours and reconnect (a claim peeks; a companion answer joins them). */
  onInquiryReady?: (inquiry: WindowInquiry | null) => void;
  /** The window's asks, to the desk's companion. */
  onAsk?: (ask: WindowAsk) => void;
  /** "what matters here?": the desk's path for this reading. */
  onOpenPath?: () => void;
  /** The note the window was opened for (a search result's), which opens in its margin card. */
  openNote?: string | null;
  /** While the desk's day closes: where the drain shows this reading's Wrap up. */
  drainHost?: HTMLElement | null;
  /** Another book's passage, opened in a window beside this one. */
  onOpenBeside?: (hit: { sourceId: string; extractionId: string; spanId: string }) => void;
  /** Side by side on the desks: the other book in a window paired with this one, the section in view, the pair's keys. */
  onOpenPair?: ReaderWindowing["onOpenPair"];
  onSection?: ReaderWindowing["onSection"];
  onPairKey?: ReaderWindowing["onPairKey"];
  onTouched?: ReaderWindowing["onTouched"];
  /** A problem opened in this window is worked on the desk's problem pad (spec §15.2). */
  onWorkOnPad?: ReaderWindowing["onWorkOnPad"];
  /** Whether this window's reading is skimmed now (the app holds the leave-time offer while the book read is). */
  onSkimming?: (muted: boolean) => void;
  /** The place in the original the learner was at while the book was prepared in this window's place. */
  handoff?: ReadingPosition | null;
}) {
  const onTitle = useCallback((title: string) => onStatus({ title }), [onStatus]);
  const onReaderStatus = useCallback(
    (status: { readingSpan: string | null; progress: number; where: string | null; reading?: string | null }) => onStatus(status),
    [onStatus],
  );
  // Pen mode's way onto the text (RD8a): the pen layer mounts on the surface the Reader hands over.
  const [penSurface, setPenSurface] = useState<PenSurface | null>(null);
  const windowing = useMemo<ReaderWindowing>(
    () => ({ railHost, onTitle, onJumpReady, onMediaReady, onStatus: onReaderStatus, lens, video, onPenSurface: setPenSurface, onInquiryReady, onAsk, onOpenPath, openNote, drainHost, onOpenBeside, onOpenPair, onSection, onPairKey, onTouched, onWorkOnPad }),
    [railHost, onTitle, onJumpReady, onMediaReady, onReaderStatus, lens, video, onInquiryReady, onAsk, onOpenPath, openNote, drainHost, onOpenBeside, onOpenPair, onSection, onPairKey, onTouched, onWorkOnPad],
  );
  // The Reader opens its first source once, on mount: a window opens one book for its life.
  const initialSource = useMemo(
    () => (card ? { card, spanId: startSpan, reading: startSpan ? content.extractionId : null, ...(handoff ? { handoff } : {}) } : null),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [card?.sourceId],
  );
  if (!card) {
    return (
      <div className="desk-panel desk-quiet">
        {libraryLoaded ? "This source is not in your library any more." : "◐ Opening…"}
      </div>
    );
  }
  return (
    <>
      <ScopedSource
        key={card.sourceId}
        onError={onError}
        initialSource={initialSource}
        windowed={windowing}
        {...(reader ?? {})}
        {...(onSkimming ? { onSkimmingChange: onSkimming } : {})}
      />
      <PenLayer surface={penSurface} />
    </>
  );
}
