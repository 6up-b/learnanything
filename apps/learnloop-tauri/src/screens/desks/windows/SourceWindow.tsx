// Book, PDF, paper, web and video windows (spec §7.1, §7.4): one Reader source pane per window, as a
// scoped instance. The Reader's hooks (selection, capture, margin cues, figures, the watch panel and
// its transcript) run unchanged inside it; what makes it one window among many is around it: its
// listeners go through the desk's router, its timers and media pause when it leaves the view, and it
// logs reading activity only while it is active or visible (desks/lifecycle.tsx).
import { useCallback, useMemo, useState, type ComponentProps } from "react";
import type { ContentRefDto, SourceLibraryCard } from "../../../api/dto";
import { ReaderScreen, type PenSurface, type ReaderLens, type ReaderWindowing, type WindowInquiry } from "../../ReaderScreen";
import type { WindowAsk } from "../../reader/useReaderInquiry";
import { PenLayer } from "../pen/PenLayer";
import type { VideoExtras } from "../../reader/YouTubeWatchPanel";

export type ReaderPassThrough = Pick<ComponentProps<typeof ReaderScreen>, "onCheckMe" | "onUseExercise" | "onTeachMe" | "workbench">;

export interface SourceStatus {
  title?: string;
  readingSpan?: string | null;
  progress?: number;
  where?: string | null;
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
}) {
  const onTitle = useCallback((title: string) => onStatus({ title }), [onStatus]);
  const onReaderStatus = useCallback(
    (status: { readingSpan: string | null; progress: number; where: string | null }) => onStatus(status),
    [onStatus],
  );
  // Pen mode's way onto the text (RD8a): the pen layer mounts on the surface the Reader hands over.
  const [penSurface, setPenSurface] = useState<PenSurface | null>(null);
  const windowing = useMemo<ReaderWindowing>(
    () => ({ railHost, onTitle, onJumpReady, onMediaReady, onStatus: onReaderStatus, lens, video, onPenSurface: setPenSurface, onInquiryReady, onAsk }),
    [railHost, onTitle, onJumpReady, onMediaReady, onReaderStatus, lens, video, onInquiryReady, onAsk],
  );
  // The Reader opens its first source once, on mount: a window opens one book for its life.
  const initialSource = useMemo(
    () => (card ? { card, spanId: startSpan, reading: startSpan ? content.extractionId : null } : null),
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
      <ReaderScreen
        key={card.sourceId}
        onError={onError}
        initialSource={initialSource}
        windowed={windowing}
        {...(reader ?? {})}
      />
      <PenLayer surface={penSurface} />
    </>
  );
}
