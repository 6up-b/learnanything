// The scoped source's contracts: what a source window hands the source and gets back. Moved whole from the retired
// standalone Reader screen (the Reader's retirement, phase 2).

import type { ReactNode } from "react";
import type { SourceLibraryCard } from "../../../api/dto";
import type { ReadingPosition } from "../../reader/readingPosition";
import type { ListenerHub, ScopeClaims, WindowLifecycle } from "../lifecycle";
import type { WindowAsk, WindowExchange } from "../../reader/useReaderInquiry";
import type { VideoExtras, WatchLens } from "../../reader/YouTubeWatchPanel";
import type { CueCheckMeRequest } from "../../reader/useReaderCues";
import type { ReturnStack } from "../../reader/returnStack";
import type { ReaderWorkbenchExercise } from "../../reader/exerciseCandidates";
import type { ProblemHandoff } from "../problem/problemPads";
import type { SideBySideVia } from "../../reader/useSideBySide";
import type { PaneTarget } from "../../reader/sideBySide";

export interface ReaderOpenSource {
  card: SourceLibraryCard;
  spanId: string | null;
  /** The reading `spanId` was found on (UX Phase 3 fix round 1, F3: Today's
   *  threads): a span of another reading is translated, never opened as one
   *  of the reading the book opens on. Absent: the span is the open one's. */
  reading?: string | null;
  /** Reader CA6b (Codex re-review F8): the return stack to open with, so a
   *  check or a work through started from side by side's second pane keeps
   *  its way back there (Alt+← reopens side by side) across the shell's
   *  practice and feedback screens. Absent: the Reader opens as before. */
  besideTrail?: ReturnStack | null;
  /** Where the learner was in the original while the book was being prepared (its window's hand-over): the reading
   *  opens there. Absent: the saved place, as before. */
  handoff?: ReadingPosition | null;
}
/** Reader workbench v2 (spec §7.1, §21.1): this Reader is one source window on a desk. It shows the
 *  source pane only; the window's frame carries the title, and the rail (Guide, Ask, Notes) shows in a
 *  panel window bound to this book when the desk has one (`railHost`), else nowhere. */
export interface ReaderWindowing {
  /** The panel window's body to show the rail in, the tab it opens on, and that panel's own lifecycle,
   *  listener hub and scope claims: the rail is shown in the panel, so its keys, timers and exposure go
   *  by the panel, not by this source window. */
  railHost?: { node: HTMLElement; tab: "guide" | "notes"; lifecycle: WindowLifecycle; hub: ListenerHub; claims?: ScopeClaims } | null;
  /** The book's title once known, for the window's frame and the shelf. */
  onTitle?: (title: string) => void;
  /** The desk's way into this window: jump to a passage (a path row, a shelf row). */
  onJumpReady?: (jump: ((spanId: string) => void) | null) => void;
  /** Where the learner is, for the shelf's row: the passage under the marker, how far through the book,
   *  and the section's words. */
  onStatus?: (status: { readingSpan: string | null; progress: number; where: string | null }) => void;
  /** A video source's play/pause, for the desk's `space` (null when this source has no player). */
  onMediaReady?: (toggle: (() => void) | null) => void;
  /** The goal lens over this reading (the desks' RD6): what to draw before a passage, in its gutter, and
   *  the classes it takes. Absent, passages render as they always have. */
  lens?: ReaderLens | null;
  /** The desks' video window (RD10): chapter ticks, the suggested chapters under the player, the player's clock. */
  video?: VideoExtras | null;
  /** Pen mode's way onto this source (RD8a): the text surface, the open reading's identity and the selection
   * model for a range the pen marked (null while no text reading is shown). */
  onPenSurface?: (surface: PenSurface | null) => void;
  /** The desk's way into this window's inquiry (spec §21.1: the companion holds the thread; the detour strip and
   *  alt+← stay in the window): a claim of this reading peeks, and a companion answer joins its detours. */
  onInquiryReady?: (inquiry: WindowInquiry | null) => void;
  /** Asks go to the desk's companion (a routed ask, a reconnect's "still unclear"), not to a rail the desk hides. */
  onAsk?: (ask: WindowAsk) => void;
  /** "what matters here?": the desk's path for this reading (the goal's path view, else the reading's path). */
  onOpenPath?: () => void;
  /** A note the window was opened for (a search result names it): its card opens, being edited, once it is listed. */
  openNote?: string | null;
  /** While the desk's day closes (the drain): where this reading's Wrap up is shown. */
  drainHost?: HTMLElement | null;
  /** Another book's passage (a library hit, a textbook exercise in another book) opens in a window beside this one,
   *  never in place of this window's book (a window opens one book for its life). */
  onOpenBeside?: (hit: { sourceId: string; extractionId: string; spanId: string }) => void;
  /** Side by side on the desks: the other book opens in a window paired with this one (its first correspondent from
   *  Ctrl+\, or a list's "side by side"); the desk hosts following, focus and the way back between the two. */
  onOpenPair?: (target: PaneTarget, via: SideBySideVia) => void;
  /** The section in view moved (the desk's follow along between paired windows reads it). */
  onSection?: (section: { extractionId: string; sectionId: string } | null) => void;
  /** Side by side's keys on the desks, for the pair this window is in: Ctrl+Shift+L follow along, F6 the other one. */
  onPairKey?: (key: "follow" | "other") => void;
  /** The learner's hand on this window (a scroll, a click, a touch), for the pair it is in. */
  onTouched?: () => void;
  /** RW2 on a desk (spec §15.2): a problem this window opens (work through this, an exercise, a check, a resume) is
   *  worked on the desk's problem pad instead of a working posture over the book. */
  onWorkOnPad?: (handoff: ProblemHandoff) => void;
}
/** What a desk does in a source window's inquiry. */
export interface WindowInquiry {
  /** A claim of this reading opened from outside: a peek, so the strip shows the way back and alt+← walks it. */
  peek: (spanId: string) => void;
  /** A companion answer about this reading landed (a follow-up, with its parent). */
  noteAnswer: (exchange: WindowExchange, parent: WindowExchange | null) => void;
  /** The desk wrote an annotation on this reading (a margin note, an append): its marks are read again. */
  annotationsChanged: () => void;
  /** The reading's own path (RW7a) in the window, for a desk with no goal: toggled, or opened; false when this
   *  reading has no path to show (reading paths off). */
  showPath: (how: "toggle" | "open") => boolean;
  /** "write it myself" from the menu's Make it practice: the Reader's own question card on this passage, in the window. */
  writeOwnQuestion: (spanId: string, quote: string) => void;
}
/** The desks' goal lens, laid over a reading's passages by span id (the text itself is never changed). */
export interface ReaderLens {
  /** A callout before the passage (a section start on the goal's path). */
  before?: (spanId: string) => ReactNode;
  /** A mark in the passage's left gutter; the passage becomes its offset parent. */
  mark?: (spanId: string) => ReactNode;
  /** Classes for the passage (dimmed for the goal); `state` says what the Reader marks on it (the learner's
   *  annotation, the active passage, the passage scrolled to and being read), which stays at full colour. */
  className?: (spanId: string, state: { annotated: boolean; active: boolean; reading?: boolean }) => string | undefined;
  /** The same lens over a video's transcript. */
  watch?: WatchLens | null;
}
/** What the desk's pen layer needs of a source window's text (spec §10.10). */
export interface PenSurface {
  /** The scrolling text surface: the ink layer lives inside it, so ink scrolls with the text. */
  body: HTMLElement;
  identity: { sourceId: string; revisionId: string; extractionId: string; renderViewId: string | null };
  /** A range's passages, one node per covered block, as a selection's (the same anchoring as a highlight). */
  nodesFor: (range: Range) => Array<{ spanId: string; quote: string; start?: number; end?: number }>;
}
/** RW3a "check me" on a margin cue: the item to open as an ordinary attempt on
 *  your own, and the passage to come back to after its feedback. */
export interface ReaderCheckMeRequest extends CueCheckMeRequest {
  card: SourceLibraryCard;
  /** RW4b: the sources service's import that wrote the item (an exercise's pick). */
  importId?: string | null;
  /** RW4b: an admitted exercise resumes its own problem ("practice_this"). */
  entry?: "check_me" | "practice_this";
  /** Reader CA6b (Codex re-review F8): the way back to side by side, when the
   *  check came from its second pane (the shell hands it back to the Reader). */
  besideTrail?: ReturnStack | null;
}
/** RW4b "use this one" on a textbook exercise: the problem to open at once
 *  on its verbatim statement, in the source it comes from. */
export type ReaderExerciseRequest = ReaderWorkbenchExercise & { card: SourceLibraryCard };
