// What a pad window needs from the desks (spec §10): the vault's store, ids, today's date, ways to open a
// passage, search, the companion and a lesson, and the pad RPCs. DeskShell provides it; tests provide fakes.
import { createContext, useContext } from "react";
import type {
  CarryInput,
  CarriedQuestionDto,
  PadProposalsDto,
  PadSubmitBlockDto,
  PadSubmitBlockInput,
  PassageUnionDto,
  PassageUnionInput,
  ProposalLabelInput,
} from "../../../api/dto";
import type { DeskStore } from "../store";
import type { SearchRow } from "../search/model";

export interface PadsApi {
  padProposals(input: { padId: string }): Promise<PadProposalsDto>;
  proposalLabel(input: ProposalLabelInput): Promise<unknown>;
  padSubmitBlock(input: PadSubmitBlockInput): Promise<PadSubmitBlockDto>;
  carriedCarry(input: CarryInput): Promise<{ carried: CarriedQuestionDto; created: boolean }>;
  requestTeachBack(input: { learningObjectId?: string; practiceItemId?: string }): Promise<{ practiceItemId: string }>;
  passageUnionRange(input: PassageUnionInput): Promise<PassageUnionDto>;
  authorPracticeItem(input: { learningObjectId: string; prompt: string; expectedAnswer: string }): Promise<{ practiceItemId: string }>;
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
  openPassage: (extractionId: string, spanId: string | null, t?: number) => void;
  openSearch: (query: string, insert?: (row: SearchRow) => void) => void;
  askAbout: (quote: string) => void;
  teachMe?: (extractionId: string, spanIds: string[]) => void;
  /** Show me (spec §13.1): a figure for the line, built as the Reader's are; null when none is shown. */
  showMe?: (text: string, anchor: { extractionId: string; spanId: string } | null) => Promise<{ figureId: string; line: string } | null>;
  toast: (text: string) => void;
  setView: (windowId: string, view: Record<string, unknown>) => void;
  sourcePieces: () => SourcePiece[];
  /** A window's keys reach its stack through this handle. */
  register: (windowId: string, handle: PadStackHandle | null) => void;
  /** Carry a question (shared with the shelf). */
  carry: (text: string, origin: { kind: CarryInput["originKind"]; ref?: string | null; anchor?: CarryInput["anchor"] }) => void;
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
