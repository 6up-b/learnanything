// What a pad window needs from the desks (spec §10): the vault's store, ids, today's date, ways to open a
// passage, search, the companion and a lesson, and the pad RPCs. DeskShell provides it; tests provide fakes.
import { createContext, useContext } from "react";
import type {
  CarryInput,
  CarriedQuestionDto,
  PadProposalsDto,
  PadSubmitBlockDto,
  PadSubmitBlockInput,
  PassageContentDto,
  PassageUnionDto,
  PassageUnionInput,
  ProposalLabelInput,
  SessionSnapshot,
  SubmitTeachBackTurnInput,
  TeachBackTurnResult,
} from "../../../api/dto";
import type { DeskStore } from "../store";
import type { MenuObjectInput, PromotedRowDto } from "../../../api/dto";
import type { Poller } from "../../../api/poller";
import type { PromotedApi } from "../menu/ContextMenu";
import type { LessonsHost } from "../lesson/host";
import type { SearchRow } from "../search/model";
import type { NotebookMenuRequest } from "../notebook/menuBridge";

export interface PadsApi {
  padProposals(input: { padId: string }): Promise<PadProposalsDto>;
  proposalLabel(input: ProposalLabelInput): Promise<unknown>;
  padSubmitBlock(input: PadSubmitBlockInput): Promise<PadSubmitBlockDto>;
  carriedCarry(input: CarryInput): Promise<{ carried: CarriedQuestionDto; created: boolean }>;
  requestTeachBack(input: { learningObjectId?: string; practiceItemId?: string }): Promise<{ practiceItemId: string }>;
  passageUnionRange(input: PassageUnionInput): Promise<PassageUnionDto>;
  authorPracticeItem(input: { learningObjectId: string; prompt: string; expectedAnswer: string }): Promise<{ practiceItemId: string }>;
  /** A teach-back's next turn (the existing entry point), when a submitted teach-back asks a follow-up. */
  submitTeachBackTurn(input: SubmitTeachBackTurnInput): Promise<TeachBackTurnResult>;
  /** The session (its checkpoint holds a teach-back in progress). */
  getSession(sessionId: string): Promise<SessionSnapshot>;
  /** A passage as its source has it (a source piece's words, apart from its title, page and time). */
  passageContent(input: PassageUnionInput): Promise<PassageContentDto>;
  /** The open problems (a problem pad's item). */
  workbenchOpenProblems(): Promise<{ problems: Array<{ sessionId: string; practiceItemId?: string | null }> }>;
}

/** A source piece the pad menu can insert (spec §9.2): the passage in view in an open source window, the cue
 * playing now in a video. */
export interface SourcePiece {
  label: string;
  extractionId: string;
  spanId: string;
  text: string;
  t?: number;
  sourceTitle: string;
}

export interface PadsHost {
  store: DeskStore;
  deskId: string | null;
  mintId: (prefix: string) => string;
  /** Today's local date, yyyy-mm-dd (the running pad's day headings). */
  today: () => string;
  api: PadsApi;
  /** The practice session a submission is recorded in (the shell's), or null. */
  practiceSessionId: string | null;
  /** A passage beside the focus (or scrolled to where it is open); a source on no desk is reopened from the
   * stored source id (or its reading), a video at the stored time. */
  openPassage: (extractionId: string, spanId: string | null, t?: number, sourceId?: string | null) => void;
  openSearch: (query: string, insert?: (row: SearchRow) => void) => void;
  /** The companion, asking about `quote`; from a pad line, with its block and the passage it links to. */
  askAbout: (quote: string, context?: { padId: string; blockId: string | null; anchor: { extractionId: string; spanId: string } | null }) => void;
  teachMe?: (extractionId: string, spanIds: string[]) => void;
  /** Show me (spec §13.1): a figure for the line, built as the Reader's are; null when none is shown. Its job is
   * polled under `ownerWindowId`, so a paused pad window's figure waits with it. */
  showMe?: (text: string, anchor: { extractionId: string; spanId: string } | null, ownerWindowId?: string) => Promise<{ figureId: string; line: string } | null>;
  /** Figures finished for a pad window, kept until the window is live to write them. */
  figures: PendingFigures;
  toast: (text: string) => void;
  setView: (windowId: string, view: Record<string, unknown>) => void;
  sourcePieces: () => SourcePiece[];
  /** The context menu's shared parts (promoted rows and their job, What this knows), lent by the desks. */
  menu?: {
    promoted: PromotedApi;
    poller: Poller;
    /** A promoted row's action, run for the object its menu was opened on; false when it could not run. */
    onPromoted: (row: PromotedRowDto, origin: MenuObjectInput | null) => boolean;
    knows: (object: MenuObjectInput) => void;
  };
  /** A pad joins a stack window by its own desk op (add_to_stack), never through the window's view. */
  addToStack: (windowId: string, padId: string) => void;
  /** A window's keys reach its stack through this handle. */
  register: (windowId: string, handle: PadStackHandle | null) => void;
  /** Teacher lessons as tabs of a stack (spec §11.1); absent where the desks give none (a stack then shows pads only). */
  lessons?: LessonsHost;
  /** Carry a question (shared with the shelf). */
  carry: (text: string, origin: { kind: CarryInput["originKind"]; ref?: string | null; anchor?: CarryInput["anchor"] }) => Promise<void> | void;
}

/** What the desks' keys ask of a pad stack. */
export interface PadStackHandle {
  /** ctrl+tab / ctrl+shift+tab. */
  nextPad(direction: -1 | 1): void;
  /** alt+j/k: the next pad (or split pane); false past the last, so the desk moves on. */
  padOrDesk(direction: -1 | 1): boolean;
  /** alt+n. */
  newPad(title?: string): void;
  /** alt+d. */
  sketchBlock(): void;
  /** alt+a. */
  arrange(): void;
  /** `.` on the hovered line. */
  menuAtHover(): boolean;
  /** The desks' right-click on a pad line (or the pad's body, `blockId` null): its menu opens here. */
  openMenu(padId: string, blockId: string | null, at: { x: number; y: number }, selection?: string): void;
  /** Bring one of its pads into view (the shelf's running pad "open"). */
  showPad(padId: string): void;
  /** A notebook frame's right-click in this stack (a pad's cells or a lesson's notebook): the pad menu there. */
  openFrameMenu(request: NotebookMenuRequest): void;
}

/** A figure Show me finished, waiting to be written below its line. */
export interface PendingFigure {
  padId: string;
  afterBlockId: string | null;
  figureId: string;
  line: string;
}

/** Finished figures per pad window: a paused window writes nothing, so its figures wait here (kept across its
 * pause and a remount) until it is live again. */
export class PendingFigures {
  private byWindow = new Map<string, PendingFigure[]>();
  private listeners = new Set<() => void>();
  private version = 0;

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  getVersion = (): number => this.version;

  push(windowId: string, figure: PendingFigure): void {
    this.byWindow.set(windowId, [...(this.byWindow.get(windowId) ?? []), figure]);
    this.version += 1;
    for (const listener of [...this.listeners]) listener();
  }

  /** The window's waiting figures, handed over once. */
  take(windowId: string): PendingFigure[] {
    const waiting = this.byWindow.get(windowId) ?? [];
    this.byWindow.delete(windowId);
    return waiting;
  }
}

export const PadsHostContext = createContext<PadsHost | null>(null);

export function usePadsHost(): PadsHost | null {
  return useContext(PadsHostContext);
}

/** A local date as yyyy-mm-dd. */
export function localDay(date: Date = new Date()): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

/** "FRI 22 NOV", with " · TODAY" for today. */
export function dayHeading(day: string, today: string): string {
  const date = new Date(`${day}T12:00:00`);
  if (Number.isNaN(date.getTime())) return day;
  const label = date.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" }).replace(",", "").toUpperCase();
  return day === today ? `${label} · TODAY` : label;
}
