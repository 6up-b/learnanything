// The Reader workbench's desks (spec §3.1, §5): the top bar's desk tabs, the stage of windows in
// slots, the shelf, the footer, and the single key router for the workbench.
//
// The workspace model (model/workspace.ts) is the truth on screen; every change the learner makes is
// applied there at once and queued as `desk.apply` ops in the outbox (outbox.ts), which sends them in
// order. A conflict takes the server's state: the shell reads `desk.state` again.
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, useSyncExternalStore, type ComponentProps, type CSSProperties, type ReactNode } from "react";
import { flushSync } from "react-dom";
import { api } from "../../api/client";
import { useCachedQuery } from "../../api/useCachedQuery";
import { TAG } from "../../api/queryTags";
import { TUTOR_COPY } from "../reader/TutorAnswer";
import { cachedSourceRead } from "../reader/readerCache";
import { poller as appPoller, type Poller } from "../../api/poller";
import type { CarriedQuestionDto, CompanionDock, CompanionHistoryDto, ContentRefDto, PadDrainDto, DeskApplyDto, DeskApplyInput, DeskStateDto, SourceLibraryCard, TutorCitationDto } from "../../api/dto";
import {
  closeWindow,
  createDesk,
  deskById,
  focusAlong,
  focusPane,
  focusedSlot,
  focusedWindowId,
  moveFocused,
  moveToDesk,
  moveToDeskAt,
  openStackBeside,
  addToStack,
  ensureRunningPad,
  hasRunningPad,
  type Step,
  moveWindowTo,
  openBeside,
  openPaired,
  pairFocused,
  renameDesk,
  reorderSlots,
  setFocus,
  setCompanionDock,
  setCompanionShown,
  setGoal,
  setView,
  slotIndexOf,
  swapInView,
  undoClose,
  unpairFocused,
  type DeskWindow,
  type Workspace,
} from "./model/workspace";
import {
  DESK_SIZES,
  FOCUS_MEASURE,
  ensureVisible,
  paneRects,
  rowTop,
  sliverSlots,
  slotRects,
  slotVisibility,
  slotWidth,
  softCropMask,
  stepZoom,
  type Rect,
  type Stage,
} from "./geometry";
import {
  IDENTITY,
  OVERVIEW,
  classifyWheel,
  dragProgress,
  dropTarget,
  enteringCamera,
  followSelection,
  moveSelection,
  newZoomGesture,
  normalizedDelta,
  overviewLayout,
  zoomWheel,
  type Camera,
  type ZoomGesture,
  type ZoomSource,
} from "./overview/engine";
import { ANIMATION_FRAMES, ZoomController, cameraTransform, type FrameClock, type SlotElements, type ZoomPlan } from "./overview/controller";
import { CardFace, LinkLayer } from "./overview/Card";
import { DRAWN_RELATIONS, curvedLinks, gatherOrder, relationsOf, type Relation } from "./overview/links";
import { MiniatureBook, cloneForMiniature } from "./overview/miniature";
import {
  BareAltTracker,
  DESK_BINDINGS,
  ModifierTracker,
  REAL_TIMERS,
  isTypingTarget,
  resolveKey,
  type DeskAction,
  type Timers,
} from "./keys/router";
import { DeskListenerRouter, WINDOW_ATTRIBUTE, windowOfTarget } from "./keys/listeners";
import { WindowScope, isPaused, windowState, type ClaimedScope, type ListenerHub, type ScopeClaims, type WindowLifecycle } from "./lifecycle";
import { clientIdFor, type OutboxTransport } from "./outbox";
import { deskStoreFor } from "./store";
import { CarriedList, Shelf, type ShelfRow } from "./Shelf";
import { SourceWindow, type ReaderPassThrough, type SourceStatus } from "./windows/SourceWindow";
import { DeskPairs, keptPairsFor } from "./sideBySide/pairs";
import type { PaneTarget } from "../reader/sideBySide";
import { logReaderAction } from "../reader/activity";
import type { WindowInquiry } from "../ReaderScreen";
import type { WindowAsk, WindowExchange } from "../reader/useReaderInquiry";
import { ThreadWindow } from "./windows/ThreadWindow";
import { PadStackWindow } from "./pads/PadStackWindow";
import { ContextMenu, useSheetFocus, type PromotedApi } from "./menu/ContextMenu";
import { KnowsPanel } from "./menu/KnowsPanel";
import { ExerciseSheet } from "./menu/ExerciseSheet";
import { captureNodes, hasPassage, headerLine, objectAt, objectInput, passageIds, type MenuObject } from "./menu/model";
import { promotedRef, runVerb, sourceMenuRows, type MenuApi, type MenuContext } from "./menu/verbs";
import { DrainPanel } from "./pads/DrainPanel";
import { PassageMarks, visibleSpanRange, type PadLink } from "./pads/PassageMarks";
import { keyAfter, padName } from "./pads/model";
import { PenHostContext, type PenApi, type PenHost } from "./pen/host";
import { LIVE_PEN_API } from "./pen/live";
import { InkCache } from "./pen/inkCache";
import { PadsHostContext, PendingFigures, localDay, type PadStackHandle, type PadsApi, type PadsHost, type SourcePiece } from "./pads/host";
import type { ProposedDiff } from "./companion/DiffProposal";
import { Companion, type CompanionHandle } from "./companion/Companion";
import { NotebookBridgeContext, type NotebookBridgeHost } from "./notebook/NotebookFrame";
import type { BridgeMessage } from "./notebook/bridge";
import { notebookMenuRequest, openNotebookMenu, setNotebookMenuOpener } from "./notebook/menuBridge";
import { lessonNotebookFrame } from "./notebook/LessonNotebook";
import { handOver, problemPadId, type ProblemHandoff } from "./problem/problemPads";
import { CompanionFigures, showInCompanion, useCompanionFigures, type CompanionFigureHost } from "./companion/companionFigures";
import type { ProblemHost } from "./problem/ProblemPad";
import { problemTitle } from "../workbench/stepModel";
import type { NotebookOwner } from "../../api/dto";
import { CompanionAsks, companionAsksFor, forgetCompanionAsks, type CompanionApi, type CompanionExchange } from "./companion/asks";
import { HIDDEN, avoidOffset, companionStep, type CompanionEvent, type CompanionState } from "./companion/model";
import { SearchPanel, type SearchApi } from "./search/SearchPanel";
import type { SearchRow } from "./search/model";
import { clipQuote, readWindowSelection, type WindowSelection } from "./selection";
import { LibraryPanel, PANEL_TITLES, PathPanel, RailHostPanel } from "./windows/PanelWindow";
import { ScreenErrorBoundary } from "../../app/ScreenErrorBoundary";
import { useGoalDesk, type GoalReading } from "./goal/GoalLayer";
import { LIVE_GOAL_TRANSPORT, type GoalTransport } from "./goal/controller";
import { LessonDesk, LIVE_LESSONS_TRANSPORT, type LessonsHost, type LessonsTransport, type Opening } from "./lesson/host";
import { addLessonToStack, findLesson, lessonKey, lessonStack, lessonTabTitle, stackWindowOf } from "./lesson/model";
import { PathLessonRow } from "./lesson/PathLessonRow";
import { LIVE_VIDEO_TRANSPORT, VideoDesk, type VideoTransport } from "./video/desk";
import { VideoWindow } from "./video/VideoWindow";
import { FollowChip } from "./video/FollowChip";
import { FollowLenses } from "./video/followLens";
import { timestampLine } from "./video/model";
import { CarriedRelated, allCarried } from "./carried/related";
import type { LessonEntry } from "../LessonView";
import type { LessonViewDto } from "../../api/dto";
import "../../styles/goal.css";
import "../../styles/lesson.css";
import "../../styles/video.css";
import "../../styles/checks.css";
import { CheckDesk, LIVE_CHECK_TRANSPORT, type CheckTransport } from "./checks/controller";
import { CheckCardOverlay, CheckLenses } from "./checks/CheckCard";
import { VeilLayer } from "./checks/VeilLayer";
import { visibleNow } from "./checks/model";
import "../../styles/desk.css";
// The desks' five fonts ship with the app (SIL OFL 1.1, Fontsource packages pinned in package.json): Vite
// bundles their files, so nothing is fetched from a font service.
import "@fontsource-variable/literata";
import "@fontsource-variable/literata/wght-italic.css";
import "@fontsource-variable/source-serif-4";
import "@fontsource-variable/source-serif-4/wght-italic.css";
import "@fontsource-variable/jetbrains-mono";
import "@fontsource-variable/caveat";

export interface DeskTransport extends OutboxTransport {
  state(): Promise<DeskStateDto>;
  padGet?(input: { padId: string }): Promise<import("../../api/dto").PadViewDto>;
  library(): Promise<SourceLibraryCard[]>;
  /** A source's current reading, which a window names (its content reference carries both). */
  resolveExtraction(sourceId: string): Promise<string>;
  /** The source a reading belongs to (a passage named by its reading alone: a history anchor, a citation). */
  sourceOfExtraction?(extractionId: string): Promise<string>;
}

export const LIVE_DESK_TRANSPORT: DeskTransport = {
  state: () => api.deskState(),
  apply: (input: DeskApplyInput): Promise<DeskApplyDto> => api.deskApply(input),
  applyPad: (input) => api.padApply(input),
  applyInk: (input) => api.inkSave(input),
  applyInkErase: (input) => api.inkErase(input),
  padGet: (input) => api.padGet(input),
  library: async () => (await api.getSourceLibrary()).sources,
  // The Reader's own cached read: the window that opens next reads it from the cache.
  resolveExtraction: async (sourceId) => (await cachedSourceRead(sourceId, ["reader_render_view", sourceId], () =>
    api.readerRenderView({ extractionId: sourceId }))).extractionId,
  // The same read by the reading's id: its render names the source.
  sourceOfExtraction: async (extractionId) => (await api.readerRenderView({ extractionId })).sourceId,
};

/** The companion's hand-off waits this long after an anchored summon before a scroll counts (spec §8.3). */
const COMPANION_SIZES_HANDOFF_MS = 250;

/** What a companion question is grounded in, or why there is nothing to ground it in. */
interface Grounding {
  reason: string | null;
  extractionId?: string;
  spanId?: string;
  windowId?: string;
  /** Asked about a pad line: its block (recorded with the exchange; its words go with the question). */
  padBlockId?: string;
  /** The window whose top passage stands in when no reading place is known (the book beside a pad line). */
  spanWindowId?: string;
}

/** A pad line asked about ("Ask about this" in the pad menu or a card): its block and the passage it links to. */
export interface PadAskContext {
  blockIds?: string[];
  padId: string;
  blockId: string | null;
  anchor: { extractionId: string; spanId: string } | null;
}

/** What the chip asks about: a selection in a window, or a pad line. */
export interface AskChip {
  extractionId?: string;
  quote?: string;
  spanIds: string[];
  windowId: string;
  pad?: PadAskContext;
}

export function groundingFor(ws: Workspace, chip: AskChip | null, focus: DeskWindow | undefined, status: Record<string, SourceStatus>): Grounding {
  if (chip?.pad) {
    const padBlockId = chip.pad.blockId ?? undefined;
    // A linked line is asked about its passage.
    if (chip.pad.anchor) return { reason: null, extractionId: chip.pad.anchor.extractionId, spanId: chip.pad.anchor.spanId, windowId: chip.windowId, padBlockId };
    // An unlinked line is asked beside the desk's book or video, where the learner reads (its reading place).
    const deskId = ws.windows[chip.windowId]?.deskId ?? focus?.deskId;
    const desk = deskId ? ws.desks.find((each) => each.deskId === deskId) : undefined;
    for (const id of desk?.slots.flat() ?? Object.keys(ws.windows)) {
      const window = ws.windows[id];
      const content = window?.content;
      if (!window || !content || (content.kind !== "source" && content.kind !== "video")) continue;
      const span = status[id]?.readingSpan ?? (typeof window.view?.spanId === "string" ? (window.view.spanId as string) : undefined);
      // Asked from the pad (its window owns the question's poll), about the book where the learner reads.
      return { reason: null, extractionId: content.extractionId, spanId: span, windowId: chip.windowId, spanWindowId: id, padBlockId };
    }
    return { reason: "Open a book or video on this desk before asking about this line." };
  }
  if (chip && chip.spanIds.length) {
    const content = ws.windows[chip.windowId]?.content;
    if (content && (content.kind === "source" || content.kind === "video")) {
      return { reason: null, extractionId: chip.extractionId ?? content.extractionId, spanId: chip.spanIds[0], windowId: chip.windowId };
    }
    return { reason: "reopen the selected passage to ask about it" };
  }
  const content = focus?.content;
  if (focus && content && (content.kind === "source" || content.kind === "video")) {
    // Where the learner is in it: its reported reading place, else its saved one; else the passage at the top
    // of the window when the question is asked.
    const span = status[focus.windowId]?.readingSpan ?? (typeof focus.view?.spanId === "string" ? (focus.view.spanId as string) : undefined);
    return { reason: null, extractionId: content.extractionId, spanId: span ?? undefined, windowId: focus.windowId };
  }
  return { reason: "Open a book or video, or select a passage, then press C to ask." };
}

/** A Compare window's passage anchor, kept in its view by the menu's Compare (null when it was opened bare). */
function compareAnchorOf(view: Record<string, unknown> | undefined): { extractionId: string; spanIds: string[]; sourceId: string; revisionId: string | null } | null {
  const anchor = view?.compareAnchor as Record<string, unknown> | undefined;
  if (!anchor || typeof anchor.extractionId !== "string" || typeof anchor.sourceId !== "string" || !Array.isArray(anchor.spanIds)) return null;
  return { extractionId: anchor.extractionId, sourceId: anchor.sourceId, spanIds: anchor.spanIds.filter((id): id is string => typeof id === "string"),
    revisionId: typeof anchor.revisionId === "string" ? anchor.revisionId : null };
}

/** The first passage showing at the top of a window (its reading place when none was reported yet). */
function firstVisibleSpan(windowId: string | null): string | null {
  if (!windowId) return null;
  const host = document.querySelector(`[${WINDOW_ATTRIBUTE}="${windowId}"]`);
  if (!host) return null;
  const top = host.getBoundingClientRect().top;
  const spans = [...host.querySelectorAll<HTMLElement>("[data-span-id], [data-transcript-span]")];
  const visible = spans.find((element) => element.getBoundingClientRect().bottom > top + 40) ?? spans[0];
  return visible ? visible.getAttribute("data-span-id") ?? visible.getAttribute("data-transcript-span") : null;
}

const PENDING_FIGURES = new WeakMap<object, PendingFigures>();

function pendingFiguresFor(store: object): PendingFigures {
  let figures = PENDING_FIGURES.get(store);
  if (!figures) {
    figures = new PendingFigures();
    PENDING_FIGURES.set(store, figures);
  }
  return figures;
}

function errorText(error: unknown): string {
  return error && typeof error === "object" && "message" in error ? String((error as { message: unknown }).message) : String(error);
}

/** The menu's small sheets: a margin note's words, or a review before something joins the queue. */
function MenuSheet({ sheet, onDone }: { sheet: { kind: "note" | "confirm"; title: string; detail: string; mine?: boolean }; onDone: (value: string | boolean | null) => void }) {
  const [text, setText] = useState("");
  const node = useRef<HTMLDivElement | null>(null);
  useSheetFocus(node, () => onDone(sheet.kind === "note" ? null : false));
  return (
    <div ref={node} tabIndex={-1} className="desk-sheet" role="dialog" aria-label={sheet.title}>
      <div className="head">{sheet.title} · {sheet.detail}</div>
      {sheet.kind === "note" ? <label>your note<textarea aria-label="your note" value={text} onChange={(event) => setText(event.target.value)} /></label> : null}
      <div className="acts">
        <button type="button" disabled={sheet.kind === "note" && !text.trim()} onClick={() => onDone(sheet.kind === "note" ? text.trim() : true)}>{sheet.kind === "note" ? "keep it" : "yes"}</button>
        {sheet.kind === "confirm" && sheet.mine ? <button type="button" data-sheet-choice="mine" onClick={() => onDone("mine")}>write it myself</button> : null}
        <button type="button" onClick={() => onDone(sheet.kind === "note" ? null : false)}>not now</button>
      </div>
    </div>
  );
}

/** A position key after a pad's last block. */
function keyAfterLast(blocks: Array<{ blockId: string; positionKey: string }>): string {
  return keyAfter(blocks as never, blocks[blocks.length - 1]?.blockId ?? null);
}

function threadTitle(thread: CompanionExchange[]): string {
  const last = thread[thread.length - 1];
  if (!last) return "nothing asked yet";
  return last.question.length > 40 ? `${last.question.slice(0, 39)}…` : last.question;
}

/** The pads' calls beyond `pad.get` / `pad.apply` (spec §10; RD4a), and the carried questions'. */
export interface PadsTransport extends PadsApi {
  padDrain(input: { deskId: string }): Promise<PadDrainDto>;
  figureRequest(input: import("../../api/dto").FigureRequestV1Input): Promise<import("../../api/dto").LibraryJobDto<import("../../api/dto").FigureBuildResultDto>>;
  readerFigureJob(input: { jobId: string }): Promise<import("../../api/dto").LibraryJobDto<import("../../api/dto").FigureBuildResultDto>>;
  carriedList(input: { which?: "open" | "closed" | "all"; deskId?: string; cursor?: string }): Promise<{ carried: CarriedQuestionDto[]; shelfLimit: number; cursor?: string | null }>;
  carriedMark(input: import("../../api/dto").CarriedMarkInput): Promise<unknown>;
}

export const LIVE_PADS_TRANSPORT: PadsTransport = {
  padProposals: (input) => api.padProposals(input),
  proposalLabel: (input) => api.proposalLabel(input),
  padSubmitBlock: (input) => api.padSubmitBlock(input),
  carriedCarry: (input) => api.carriedCarry(input),
  requestTeachBack: (input) => api.requestTeachBack(input),
  passageUnionRange: (input) => api.passageUnionRange(input),
  authorPracticeItem: (input) => api.authorPracticeItem(input),
  submitTeachBackTurn: (input) => api.submitTeachBackTurn(input),
  getSession: (sessionId) => api.getSession(sessionId),
  passageContent: (input) => api.passageContent(input),
  workbenchOpenProblems: async () => (await api.workbenchOpenProblems()) as unknown as { problems: Array<{ sessionId: string; practiceItemId?: string | null }> },
  padDrain: (input) => api.padDrain(input),
  figureRequest: (input) => api.figureRequest(input),
  readerFigureJob: (input) => api.readerFigureJob(input),
  carriedList: (input) => api.carriedList(input),
  carriedMark: (input) => api.carriedMark(input),
};

/** The context menu's calls (spec §9.1; RD5a): its promoted rows and their job, labels, What this knows, and the
 * verbs' server entries. */
export interface MenuTransport extends MenuApi {
  passagePromoted: PromotedApi["passagePromoted"];
  passagePromotedJob: PromotedApi["passagePromotedJob"];
  passagePromotedCancel: PromotedApi["passagePromotedCancel"];
  proposalLabel(input: import("../../api/dto").ProposalLabelInput): Promise<unknown>;
  readerExerciseImportStatus(input: { batchId: string }): Promise<import("../../api/dto").ReaderExerciseImportStatusDto>;
}

export const LIVE_MENU_TRANSPORT: MenuTransport = {
  passagePromoted: (input) => api.passagePromoted(input),
  passagePromotedJob: (input) => api.passagePromotedJob(input),
  passagePromotedCancel: (input) => api.passagePromotedCancel(input),
  proposalLabel: (input) => api.proposalLabel(input),
  passageKnows: (input) => api.passageKnows(input),
  readerCorrespondents: (input) => api.readerCorrespondents(input),
  // The reading's identity for a capture, from the Reader's cached render read.
  readingIdentity: async (extractionId) => {
    const view = await cachedSourceRead(extractionId, ["reader_render_view", extractionId], () => api.readerRenderView({ extractionId }));
    return { sourceId: view.sourceId, revisionId: view.revisionId, renderViewId: view.renderViewId ?? null };
  },
  readerCapture: (input) => api.readerCapture(input),
  readerImportExercise: (input) => api.readerImportExercise(input),
  readerAuthorSectionQuestion: (input) => api.readerAuthorSectionQuestion(input),
  readerExerciseImportStatus: (input) => api.readerExerciseImportStatus(input),
};

/** The companion's and search's calls (spec §3.4; RD3a's jobs). */
export interface CompanionTransport extends CompanionApi, SearchApi {
  companionHistory(input: { query?: string; deskId?: string; cursor?: string }): Promise<CompanionHistoryDto>;
}

export const LIVE_COMPANION_TRANSPORT: CompanionTransport = {
  companionAsk: (input) => api.companionAsk(input),
  companionAskJob: (input) => api.companionAskJob(input),
  companionAskCancel: (input) => api.companionAskCancel(input),
  companionHistory: (input) => api.companionHistory(input),
  searchEverything: (input) => api.searchEverything(input),
  searchJob: (input) => api.searchJob(input),
};

/** What a pane needs to render its content; tests and the harness may render panes their own way. */
export interface PaneRenderInput {
  window: DeskWindow;
  lifecycle: WindowLifecycle;
  card: SourceLibraryCard | null;
}

/** Undo close stays on the shelf this long (spec §5.2). */
const UNDO_CLOSE_MS = 9_000;
/** A toast stays 2.2 s (spec §4.3). */
const TOAST_MS = 2_200;
/** A window's reading place is saved once the learner settles on it. */
const VIEW_SAVE_IDLE_MS = 2_000;
/** A gather to a new desk leaves a placeholder sliver this long (spec §6.6). */
const MOVED_NOTICE_MS = 6_000;

/** What the visual harness may drive directly: the zoom's progress, for the commit-identity check. */
export interface DeskDebugHandle {
  /** From the overview: toward `to` (else where it was entered from), in focus mode when `focusAfter`. */
  beginZoom(to?: { deskId: string; windowId: string | null } | null, focusAfter?: boolean): boolean;
  setZoomProgress(p: number): void;
  finishZoom(goal: 0 | 1): void;
  zoomFrameTimes(): number[];
  overview(): boolean;
}

/** The camera the world shows now (mid CSS transition), read from its computed transform. */
function displayedCamera(world: HTMLElement): Camera | null {
  const shown = typeof getComputedStyle === "function" ? getComputedStyle(world).transform : "";
  const match = /^matrix\(([^)]+)\)$/.exec(shown ?? "");
  if (!match) return null;
  const [a, , , , e, f] = match[1].split(",").map((part) => Number(part.trim()));
  return [a, e, f].every(Number.isFinite) && a > 0 ? { x: e, y: f, s: a } : null;
}

function prefersReducedMotion(): boolean {
  try {
    return typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch {
    return false;
  }
}

/** A slot's key: its desk and the windows in it. */
function slotKey(deskId: string, slot: string[]): string {
  return `${deskId}:${slot.join("+")}`;
}

function intersects(rect: Rect, stage: Stage): boolean {
  return rect.x + rect.w > 0 && rect.x < stage.width && rect.y + rect.h > 0 && rect.y < stage.height;
}

export const KIND_GLYPH: Record<string, string> = {
  source: "§",
  video: "▶",
  pad: "›",
  pad_stack: "›",
  lesson: "◇",
  thread: "?",
  compare: "⇄",
  panel: "◇",
  figure_notebook: "◇",
};

const KIND_WORD: Record<string, string> = {
  source: "book",
  video: "video",
  pad: "notes",
  pad_stack: "notes",
  lesson: "lesson",
  thread: "thread",
  compare: "compare",
  panel: "panel",
  figure_notebook: "figure",
};

function defaultMintId(prefix: string): string {
  try {
    return `${prefix}_${crypto.randomUUID()}`;
  } catch {
    return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2)}`;
  }
}

function shortName(title: string): string {
  const words = title.split(/\s+/).filter(Boolean);
  return words.slice(0, 3).join(" ");
}

function readStored(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStored(key: string, value: string): void {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    /* a per-machine convenience */
  }
}

export interface DeskShellProps {
  vaultKey: string;
  onError: (message: string) => void;
  /** Back to the old Reader (it stays reachable until the parity matrix passes, spec §21.1). */
  onLeave?: () => void;
  /** First run: the book the learner read last, for the first desk (spec §5.1). */
  firstSourceId?: string | null;
  transport?: DeskTransport;
  reader?: ReaderPassThrough;
  /** Renders a pane's content; absent, the real windows (source, video, panels). */
  renderPane?: (input: PaneRenderInput) => ReactNode;
  /** The viewport before it is measured (tests; jsdom lays nothing out). */
  initialViewport?: Stage;
  mintId?: (prefix: string) => string;
  timers?: Timers;
  /** The zoom's frames (tests drive them by hand). */
  frameClock?: FrameClock;
  /** Reduced motion; absent, the system's setting. */
  reducedMotion?: boolean;
  /** The harness's handle on the zoom. */
  onDebugHandle?: (handle: DeskDebugHandle) => void;
  /** The companion's and search's calls; absent, the sidecar's. */
  companion?: CompanionTransport;
  /** The job poller (tests pass one they tick by hand); absent, the app's one poller. */
  poller?: Poller;
  /** The pads' and carried questions' calls; absent, the sidecar's. */
  padsTransport?: PadsTransport;
  /** The context menu's calls; absent, the sidecar's. */
  menuTransport?: MenuTransport;
  /** The goal lens's calls (goal.band, goal.lens, the learner's choices); absent, the sidecar's. */
  goalTransport?: GoalTransport;
  /** The pen layer's calls (RD8a); absent, the sidecar's. */
  penApi?: PenApi;
  /** Teacher lessons as windows (spec §11.1), when lessons are on: what a lesson window hands back to the app, and
   *  a lesson the app asks to open while the desks are its current place (`seq` makes each ask one open). */
  lessons?: {
    /** A lesson the app asks for, in the vault it was asked in (another vault's is dropped, never opened here). */
    request?: { seq: number; entry: LessonEntry; vault?: string } | null;
    /** The request was taken (opened or dropped): the app forgets it, so a remount or a vault switch replays nothing. */
    onConsumed?: (seq: number) => void;
    /** A lesson's quick question on the full lesson screen (never in a desk window); settled when it closes. */
    onProbe?: (lessonId: string) => Promise<void>;
    onQuickCheck?: (learningObjectIds: string[]) => void;
    onLookInLibrary?: (phrase: string) => void;
    /** RD9b's notebook frame for a notebook lesson. */
    notebookFrame?: (lessonId: string, view: LessonViewDto) => ReactNode;
  };
  /** The lessons' summaries (lesson.list); absent, the sidecar's. */
  lessonsTransport?: LessonsTransport;
  /** Follow-along and the suggested chapters' calls (RD10); absent, the sidecar's. */
  videoTransport?: VideoTransport;
  /** The app's "Ask the tutor about this" while the desks are the Reader: each new count summons the companion on
   *  what is in view (it never dismisses it). */
  askRequest?: number;
  /** Whether the book being read is skimmed (the focused book window, else the book window focused last): the app
   *  offers nothing where the learner lands after leaving the desks while skimming, as after the old Reader. */
  onSkimmingChange?: (muted: boolean) => void;
  /** The app's way into the Reader while the desks are the Reader (the shelf, Today's threads and citations, a return
   *  from feedback, a lesson's "Look in my library"): a book (and passage) to open or focus on the desk in view, or
   *  words to search for. Each request is done once, by its sequence number, however often the desks mount again. */
  openRequest?: DeskOpenRequest | null;
  /** The inline checks' calls (RD7, spec §12.6); absent, the sidecar's. */
  checkTransport?: CheckTransport;
}

export interface DeskOpenRequest {
  seq: number;
  sourceId: string | null;
  spanId: string | null;
  /** The reading `spanId` was found on (absent or null: the book's current one). */
  reading?: string | null;
  /** Search the desks for these words (with no book). */
  phrase?: string;
}

/** The app's open requests already done, per vault: the desks unmount with the Reader place and mount again. */
const doneOpenRequests = new Map<string, number>();


export function DeskShell({
  vaultKey,
  onError,
  onLeave,
  firstSourceId = null,
  transport = LIVE_DESK_TRANSPORT,
  reader: readerProp,
  renderPane,
  initialViewport,
  mintId = defaultMintId,
  timers = REAL_TIMERS,
  frameClock = ANIMATION_FRAMES,
  reducedMotion,
  onDebugHandle,
  companion: companionTransport = LIVE_COMPANION_TRANSPORT,
  poller = appPoller,
  padsTransport = LIVE_PADS_TRANSPORT,
  menuTransport = LIVE_MENU_TRANSPORT,
  goalTransport = LIVE_GOAL_TRANSPORT,
  penApi = LIVE_PEN_API,
  lessons,
  lessonsTransport = LIVE_LESSONS_TRANSPORT,
  videoTransport = LIVE_VIDEO_TRANSPORT,
  askRequest = 0,
  onSkimmingChange,
  openRequest = null,
  checkTransport = LIVE_CHECK_TRANSPORT,
}: DeskShellProps) {
  // The vault's one desk store (store.ts): it outlives this shell, so leaving and coming back never makes a
  // second outbox for the same client.
  const store = useMemo(
    () => deskStoreFor(vaultKey, transport, timers, () => clientIdFor(vaultKey, typeof window === "undefined" ? null : window.localStorage, () => mintId("client"))),
    [vaultKey, transport, timers, mintId],
  );
  const storeWs = useSyncExternalStore(store.subscribe, store.getSnapshot);
  // Teacher lessons on the desks (spec §11.1): their summaries and the openings in flight. The shell stores an
  // opened lesson in its stack (add_to_stack) when the opening's turn returns its id.
  const lessonOpened = useRef<(opening: Opening, lessonId: string) => void>(() => undefined);
  const lessonDesk = useMemo(() => new LessonDesk(lessonsTransport, (opening, lessonId) => lessonOpened.current(opening, lessonId)), [lessonsTransport]);
  // A lesson window's title and the path view's rows follow the summaries as they land.
  useSyncExternalStore(lessonDesk.subscribe, lessonDesk.getVersion);
  // The desks' videos (RD10): each player's clock, what each book follows, each video's accepted chapters. A book
  // following a new passage scrolls to it through its window's jump (set below, once the jumps exist).
  const videoFollowed = useRef<(bookWindowId: string, spanId: string) => void>(() => undefined);
  const videoDesk = useMemo(() => new VideoDesk(videoTransport, (windowId, spanId) => videoFollowed.current(windowId, spanId)), [videoTransport]);
  useSyncExternalStore(videoDesk.subscribe, videoDesk.getVersion);
  const followLenses = useMemo(() => new FollowLenses(), []);
  // Inline cold checks (RD7, spec §12.6): the due checks' closed markers, the one open administration and its veils.
  const checkDesk = useMemo(() => new CheckDesk(checkTransport, mintId), [checkTransport, mintId]);
  useSyncExternalStore(checkDesk.subscribe, checkDesk.getVersion);
  const checkLenses = useMemo(() => new CheckLenses(), []);
  // `u` and `alt+;` reach the latest render's handlers (set below).
  const videoKeys = useRef<{ follow: () => boolean; timestamp: () => boolean }>({ follow: () => false, timestamp: () => false });
  // Pad changes re-render the shell too (the passages' ✎ links, the companion's pad proposals).
  useSyncExternalStore(store.subscribe, store.getPadVersion);
  const [storeReady, setStoreReady] = useState(store.loaded);
  const ws: Workspace | null = storeReady ? storeWs : null;
  const wsRef = useMemo(() => ({ get current(): Workspace { return store.ws; } }), [store]);
  const [library, setLibrary] = useState<SourceLibraryCard[] | null>(null);
  const deskKey = `learnloop.desks.current.${vaultKey}`;
  const [currentDeskId, setCurrentDeskIdState] = useState<string | null>(() => readStored(deskKey));
  const [camX, setCamX] = useState<Record<string, number>>({});
  const [visited, setVisited] = useState<Set<string>>(() => new Set());
  const [focusMode, setFocusMode] = useState(false);
  const [whichKey, setWhichKey] = useState(false);
  const [toast, setToast] = useState<{ text: string; key: number } | null>(null);
  const [undo, setUndo] = useState<{ deskId: string; windowId: string; title: string; until: number } | null>(null);
  const [status, setStatus] = useState<Record<string, SourceStatus>>({});
  const [entering, setEntering] = useState<Set<string>>(() => new Set());
  const [renaming, setRenaming] = useState<string | null>(null);
  const [opener, setOpener] = useState(false);
  const [badge, setBadge] = useState<number | null>(null);
  const [railHosts, setRailHosts] = useState<Record<string, HTMLElement | null>>({});
  const [railClaims, setRailClaims] = useState<Record<string, string>>({});
  const stageRef = useRef<HTMLElement | null>(null);
  const [stage, setStage] = useState<Stage>(() => {
    const viewport = initialViewport ?? { width: window.innerWidth, height: window.innerHeight };
    const shelf = viewport.width < DESK_SIZES.shelfFoldBelow ? DESK_SIZES.shelfRail : DESK_SIZES.shelf;
    return { width: viewport.width - shelf, height: viewport.height - DESK_SIZES.topBar - DESK_SIZES.footer };
  });
  const [viewportWidth, setViewportWidth] = useState(() => (initialViewport ?? { width: window.innerWidth }).width);
  // The companion's docks fold on the laptop by the window's width, as the mockup's (§4.3).
  const companionStage = useMemo(() => ({ ...stage, viewport: viewportWidth }), [stage, viewportWidth]);
  // The overview (spec §6): the committed view, its camera and selection, and what a zoom needs.
  const [overview, setOverview] = useState(false);
  const [ovCam, setOvCam] = useState<Camera>({ x: 24, y: 70, s: OVERVIEW.scale });
  const [selection, setSelection] = useState<{ deskId: string; windowId: string } | null>(null);
  const [zooming, setZooming] = useState(false);
  // While a zoom leaves the overview: the desk it lands on and its camera, so the soft crop and the
  // slivers it will show are already there on its last frame (the commit then changes nothing).
  // While a zoom leaves the overview: the desk it lands on, its camera, and the window it opens in focus
  // mode (alt+↵), whose full-screen geometry is laid out before the zoom so its last frame is the commit.
  const [leaveTarget, setLeaveTarget] = useState<{ deskId: string; cams: Record<string, number>; focusWindowId?: string | null } | null>(null);
  const [showRelations, setShowRelations] = useState(true);
  const [gatherPreview, setGatherPreview] = useState(false);
  const [panEase, setPanEase] = useState(false);
  const [hud, setHud] = useState("");
  // The companion (spec §8): its state, the dock it shows at, the selection it asks about, and how far it
  // slides aside; search in context (§9.3) while open.
  const [companionState, setCompanionState] = useState<CompanionState>(HIDDEN);
  const [companionDock, setCompanionDockShown] = useState<CompanionDock>("br");
  const [chip, setChip] = useState<(AskChip & { quote: string }) | null>(null);
  const [avoid, setAvoid] = useState(0);
  const [search, setSearchState] = useState<{ query: string; selection?: { extractionId: string; spanIds: string[] }; blockIds?: string[]; insert?: ((row: SearchRow) => void) | null } | null>(null);
  // Pads (spec §10): the stacks' key handles, the carried questions, and the desk drain while it is open.
  const padHandles = useRef(new Map<string, PadStackHandle>());
  const [carried, setCarried] = useState<{ list: CarriedQuestionDto[]; limit: number; more: boolean }>({ list: [], limit: 3, more: false });
  const [carriedOpen, setCarriedOpen] = useState(false);
  // The pad stack whose "where your words go" is open (its ⓘ sits in the window's title bar).
  const [emissionOpen, setEmissionOpen] = useState<string | null>(null);
  const [draining, setDraining] = useState(false);
  // While the desk's day closes, its readings show their Wrap up in the drain, under the pads (spec §21.1).
  const [drainWrapHost, setDrainWrapHost] = useState<HTMLDivElement | null>(null);
  // The context menu (spec §9.1) on a source object, What this knows, and the small sheets its verbs ask with.
  const [menu, setMenu] = useState<MenuObject | null>(null);
  const [knows, setKnows] = useState<import("../../api/dto").MenuObjectInput | null>(null);
  const [menuSheet, setMenuSheet] = useState<{ kind: "note" | "confirm"; title: string; detail: string; mine?: boolean; resolve: (value: string | boolean | null) => void } | null>(null);
  // Make it practice on an exercise: the sheet that shows its words, imports it and lists what it made.
  const [exerciseSheet, setExerciseSheet] = useState<{ object: MenuObject; anchor: { extractionId: string; spanId: string }; key: string } | null>(null);
  const menuOpenRef = useRef(false);
  menuOpenRef.current = menu !== null || knows !== null || menuSheet !== null || exerciseSheet !== null;
  // Pen mode (spec §10.10): alt+p, the ✎ chip, or a pen's first touch; "simulate pen" lets the mouse draw.
  const [penOn, setPenOn] = useState(false);
  const [simulatePen, setSimulatePen] = useState(false);
  const penOnRef = useRef(penOn);
  penOnRef.current = penOn;
  const drainingRef = useRef(false);
  drainingRef.current = draining;
  const companionRef = useRef<CompanionHandle | null>(null);
  const [ungather, setUngather] = useState<{ deskId: string; order: string[][] } | null>(null);
  const [movedNotice, setMovedNotice] = useState<{ deskId: string; title: string; until: number } | null>(null);
  const preOverview = useRef<{ deskId: string; focusId: string | null } | null>(null);
  const worldRef = useRef<HTMLDivElement | null>(null);
  // Each slot's three elements, by slot key. Kept apart because React attaches a parent's ref after its
  // children's, so one record per slot would lose the children on every render.
  const boxEls = useRef(new Map<string, HTMLElement>());
  const innerEls = useRef(new Map<string, HTMLElement>());
  const cardEls = useRef(new Map<string, HTMLElement>());
  const ringEls = useRef(new Map<string, HTMLElement>());
  const slotElements = useCallback((): Map<string, SlotElements> => {
    const out = new Map<string, SlotElements>();
    for (const [key, box] of boxEls.current) out.set(key, { box, inner: innerEls.current.get(key) ?? null, card: cardEls.current.get(key) ?? null });
    return out;
  }, []);
  const lateEls = useRef(new Map<string, HTMLElement>());
  const sliverEls = useRef(new Map<string, HTMLElement>());
  const miniatures = useMemo(() => new MiniatureBook(), []);
  const miniHosts = useRef(new Map<string, HTMLDivElement>());
  const onEndRef = useRef<(goal: 0 | 1, base: 0 | 1) => void>(() => undefined);
  const controller = useMemo(() => new ZoomController(frameClock, (goal, base) => onEndRef.current(goal, base)), [frameClock]);
  const jumps = useRef(new Map<string, (spanId: string) => void>());
  // Each source window's inquiry (its detours and reconnect): a claim of its reading peeks there, and a companion
  // answer about it joins its detours (spec §21.1).
  const inquiries = useRef(new Map<string, WindowInquiry>());
  const media = useRef(new Map<string, () => void>());
  const pendingJump = useRef(new Map<string, string>());

  const toastNow = useCallback((text: string) => setToast({ text, key: Date.now() }), []);
  // While an inline check is open, search waits: its results would show what the veils hold (spec §12.6.4).
  const setSearch = useCallback((next: { query: string; selection?: { extractionId: string; spanIds: string[] }; blockIds?: string[]; insert?: ((row: SearchRow) => void) | null } | null) => {
    const held = next ? checkDesk.heldReason() : null;
    if (held) {
      toastNow(`search waits · ${held}`);
      return;
    }
    setSearchState(next);
  }, [checkDesk, toastNow]);
  useEffect(() => {
    if (!toast) return;
    const handle = timers.set(() => setToast(null), TOAST_MS);
    return () => timers.clear(handle);
  }, [toast, timers]);

  // -- loading and persisting ----------------------------------------------------------------------

  const setCurrentDeskId = useCallback((deskId: string | null) => {
    setCurrentDeskIdState(deskId);
    if (deskId) writeStored(deskKey, deskId);
  }, [deskKey]);

  const commit = useCallback((step: Step) => {
    store.commit(step);
    if (step.notice) toastNow(step.notice);
  }, [store, toastNow]);

  // What the store could not save, said in one line.
  useEffect(() => store.onNotice((notice) => {
    if (notice.kind === "rejected") toastNow("That change couldn’t be saved. Check the desk before trying again.");
    else if (notice.kind === "conflict") {
      const total = notice.dropped + notice.lost;
      if (total > 0) toastNow(`the desk changed elsewhere · ${total} change${total === 1 ? "" : "s"} couldn’t be saved. Check the desk before trying again.`);
    } else if (notice.kind === "kept-both") {
      toastNow(`Your edit overlaps with a newer one. Look for your edit in ${notice.count === 1 ? "a separate line" : "separate lines"} marked “written over an older version”.`);
    } else if (notice.kind === "offline") toastNow("Still waiting to save your desk changes. Keep LearnLoop open.");
    else onError(notice.message);
  }), [store, toastNow, onError]);

  const chain = useCallback((first: Step, next: (ws: Workspace) => Step): Step => {
    const second = next(first.ws);
    return { ws: second.ws, ops: [...first.ops, ...second.ops], notice: second.notice ?? first.notice };
  }, []);

  const firstRun = useCallback(async (base: Workspace, cards: SourceLibraryCard[] | null): Promise<Step> => {
    const card = firstSourceId ? cards?.find((entry) => entry.sourceId === firstSourceId) ?? null : null;
    const deskId = mintId("desk");
    const created = createDesk(base, deskId, card ? `new desk · ${shortName(card.title)}` : "new desk");
    if (!card || card.readiness !== "ready") return created;
    const extractionId = await transport.resolveExtraction(card.sourceId).catch(() => null);
    if (!extractionId) return created;
    return chain(created, (next) => openBeside(next, deskId, contentForCard(card, extractionId), () => mintId("win")));
  }, [chain, firstSourceId, mintId, transport]);

  useEffect(() => {
    let live = true;
    void (async () => {
      try {
        const [state, cards] = await Promise.all([store.load(), transport.library().catch(() => null)]);
        if (!live) return;
        setLibrary(cards);
        if (state && store.ws.desks.length === 0) store.commit(await firstRun(store.ws, cards));
        if (live) setStoreReady(true);
      } catch {
        if (live) onError("Couldn’t open your desks. Switch away from Reader, then open it again.");
      }
    })();
    // A load that lands after this shell unmounted changes nothing here.
    return () => {
      live = false;
    };
    // Loaded once per store; a conflict reconciles inside the store.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [store]);

  // -- the current desk, focus and camera ------------------------------------------------------------

  const desk = ws ? deskById(ws, currentDeskId) ?? ws.desks[0] ?? null : null;
  const deskId = desk?.deskId ?? null;
  const focusId = ws && desk ? focusedWindowId(ws, desk) : null;
  const focusSlotIndex = ws && desk ? focusedSlot(ws, desk) : -1;
  useEffect(() => {
    if (deskId && deskId !== currentDeskId) setCurrentDeskId(deskId);
  }, [deskId, currentDeskId, setCurrentDeskId]);
  useEffect(() => {
    if (deskId) setVisited((seen) => (seen.has(deskId) ? seen : new Set([...seen, deskId])));
  }, [deskId]);

  const slotCount = desk?.slots.length ?? 0;
  const keepPrevious = useRef(false);
  useLayoutEffect(() => {
    if (!deskId) return;
    setCamX((cams) => {
      const next = ensureVisible(cams[deskId] ?? 0, focusSlotIndex, slotCount, stage, keepPrevious.current);
      keepPrevious.current = false;
      return cams[deskId] === next ? cams : { ...cams, [deskId]: next };
    });
  }, [deskId, focusSlotIndex, slotCount, stage]);

  // The stage's size: the window's, less the chrome (or all of it, in focus mode).
  useEffect(() => {
    const node = stageRef.current;
    const measure = () => {
      if (node && node.clientWidth > 0 && node.clientHeight > 0) {
        const next = { width: node.clientWidth, height: node.clientHeight };
        const now = stageNow.current;
        // A zoom's plan holds the rects of the stage it began on: a new size settles it first, so the new
        // layout is laid out at rest and never under transforms computed for the old one.
        if (controller.active && (next.width !== now.width || next.height !== now.height)) controller.settle();
        setStage(next);
      }
      // The shelf folds by the desks' own width (the Reader place), not the window's.
      const shell = node?.closest(".desk-shell") as HTMLElement | null;
      if (shell && shell.clientWidth > 0) setViewportWidth(shell.clientWidth);
    };
    measure();
    const observer = typeof ResizeObserver === "undefined" || !node ? null : new ResizeObserver(measure);
    if (observer && node) observer.observe(node);
    window.addEventListener("resize", measure);
    return () => {
      observer?.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, [ws === null]);

  const cam = deskId ? camX[deskId] ?? 0 : 0;
  const visibility = useMemo(() => slotVisibility(cam, slotCount, stage), [cam, slotCount, stage]);
  const deskIndex = ws && desk ? ws.desks.indexOf(desk) : 0;

  // -- the lifecycle of every window ---------------------------------------------------------------

  const lifecycles = useMemo(() => {
    const out: Record<string, WindowLifecycle> = {};
    if (!ws) return out;
    for (const each of ws.desks) {
      const onCurrent = each.deskId === deskId;
      each.slots.forEach((slot, index) => {
        for (const id of slot) {
          out[id] = {
            windowId: id,
            // In the overview every window is a card (a preview): paused, and it logs no reading.
            state: windowState({ onCurrentDesk: onCurrent, inView: onCurrent && Boolean(visibility[index]?.inView), focused: onCurrent && id === focusId, focusMode, preview: overview }),
          };
        }
      });
    }
    return out;
  }, [ws, deskId, visibility, focusId, focusMode, overview]);
  // The DOM focus follows the activation: when another window becomes the active one (a key, a click,
  // another desk), focus held inside a window that is no longer active moves to the new active window,
  // so typing never edits a hidden desk's field or reaches an inactive window's iframe.
  const activeWindowId = Object.values(lifecycles).find((each) => each.state === "active")?.windowId ?? null;
  useEffect(() => {
    const held = document.activeElement;
    const owner = held && held !== document.body ? windowOfTarget(held) : null;
    if (owner === activeWindowId && owner !== null) return;
    const target = activeWindowId ? document.querySelector<HTMLElement>(`[${WINDOW_ATTRIBUTE}="${activeWindowId}"]`) : null;
    // Focus elsewhere in the shell (the top bar, the shelf's filter) stays where the learner put it.
    if (owner === null && held && held !== document.body && !(held instanceof HTMLIFrameElement)) return;
    if (target) target.focus({ preventScroll: true });
    else if (held instanceof HTMLElement && owner !== null) held.blur();
  }, [activeWindowId]);
  const lifecyclesRef = useRef(lifecycles);
  lifecyclesRef.current = lifecycles;
  const focusIdRef = useRef(focusId);
  focusIdRef.current = focusId;
  // Skimming, per book window (each window's own way of reading): the app hears the book being read, the focused book
  // window, else the book window focused last.
  const skimming = useRef(new Map<string, boolean>());
  const lastBookFocus = useRef<string | null>(null);
  const skimmingReported = useRef<boolean | null>(null);
  const onSkimmingRef = useRef(onSkimmingChange);
  onSkimmingRef.current = onSkimmingChange;
  const reportSkimming = useCallback(() => {
    const focused = focusIdRef.current;
    const content = focused ? wsRef.current.windows[focused]?.content : undefined;
    if (focused && content && (content.kind === "source" || content.kind === "video")) lastBookFocus.current = focused;
    const muted = Boolean(lastBookFocus.current && skimming.current.get(lastBookFocus.current));
    if (skimmingReported.current === muted) return;
    skimmingReported.current = muted;
    onSkimmingRef.current?.(muted);
  }, [wsRef]);
  const skimmingHandlers = useMemo(() => new Map<string, (muted: boolean) => void>(), []);
  const skimmingFor = useCallback((windowId: string) => {
    let handler = skimmingHandlers.get(windowId);
    if (!handler) {
      handler = (muted: boolean) => {
        skimming.current.set(windowId, muted);
        reportSkimming();
      };
      skimmingHandlers.set(windowId, handler);
    }
    return handler;
  }, [skimmingHandlers, reportSkimming]);
  useEffect(() => reportSkimming(), [focusId, reportSkimming]);
  // Poll owners follow the windows: a paused window's polls wait; a window that closed (gone from the
  // lifecycles) pauses its polls too, and when the shell detaches every owner it knew pauses.
  const knownOwners = useRef(new Set<string>());
  useEffect(() => {
    for (const [id, lifecycle] of Object.entries(lifecycles)) poller.setOwnerPaused(id, isPaused(lifecycle.state));
    for (const id of knownOwners.current) if (!(id in lifecycles)) poller.setOwnerPaused(id, true);
    for (const id of Object.keys(lifecycles)) knownOwners.current.add(id);
  }, [lifecycles, poller]);
  useEffect(() => () => {
    for (const id of knownOwners.current) poller.setOwnerPaused(id, true);
  }, [poller]);

  // -- actions -------------------------------------------------------------------------------------

  const focusModeRef = useRef(focusMode);
  focusModeRef.current = focusMode;

  const switchDesk = useCallback((direction: -1 | 1): boolean => {
    const current = wsRef.current;
    const index = current.desks.findIndex((each) => each.deskId === deskIdRef.current);
    const next = current.desks[index + direction];
    if (!next) return false;
    setCurrentDeskId(next.deskId);
    return true;
  }, [setCurrentDeskId]);
  const deskIdRef = useRef(deskId);
  deskIdRef.current = deskId;

  const titleOf = useCallback((window: DeskWindow | undefined): string => {
    if (!window) return "";
    const known = status[window.windowId]?.title;
    if (known) return known;
    const content = window.content;
    // A stack of pads is the learner's scratchpads (the title bar adds ⓘ and "yours").
    if (window.kind === "pad_stack") return "Pads";
    if (!content) return "notes";
    if (content.kind === "source" || content.kind === "video") return library?.find((card) => card.sourceId === content.sourceId)?.title ?? "source";
    if (content.kind === "panel") return PANEL_TITLES[content.panel];
    if (content.kind === "compare") return content.query ? `compare · ${content.query}` : "compare";
    if (content.kind === "lesson") return lessonTabTitle(lessonDesk.summary(content.lessonId)?.title);
    return KIND_WORD[content.kind] ?? content.kind;
  }, [status, library, lessonDesk]);

  // -- the overview: its layout, a zoom's plan and its commit (spec §6.2, §6.3) -----------------------

  const ovLayout = useMemo(() => (ws ? overviewLayout(ws.desks.map((each) => each.slots.length), slotWidth(stage), stage) : null), [ws, stage]);
  const ovLayoutRef = useRef(ovLayout);
  ovLayoutRef.current = ovLayout;
  const stageNow = useRef(stage);
  stageNow.current = stage;
  const camXRef = useRef(camX);
  camXRef.current = camX;
  const overviewRef = useRef(overview);
  overviewRef.current = overview;
  const ovCamRef = useRef(ovCam);
  ovCamRef.current = ovCam;
  const selectionRef = useRef(selection);
  selectionRef.current = selection;
  const visitedRef = useRef(visited);
  visitedRef.current = visited;
  const showRelationsRef = useRef(showRelations);
  showRelationsRef.current = showRelations;
  const reduced = reducedMotion ?? prefersReducedMotion();
  // Each transition (a zoom or a crossfade) takes the next number; a callback scheduled by one acts only
  // while it is still the latest.
  const transitionGen = useRef(0);
  const panEaseRef = useRef(panEase);
  panEaseRef.current = panEase;
  const pendingLeave = useRef<{ deskId: string; windowId: string | null; cams: Record<string, number>; focusMode: boolean } | null>(null);

  /** Where a window's card is in the overview's world. */
  const cardOf = useCallback((windowId: string | null | undefined): Rect | null => {
    const layout = ovLayoutRef.current;
    const current = wsRef.current;
    if (!layout || !windowId) return null;
    for (const [row, each] of current.desks.entries()) {
      const index = slotIndexOf(each, windowId);
      if (index >= 0) return layout.cards[row]?.[index] ?? null;
    }
    return null;
  }, []);

  /** A slot's reading rect in world coordinates, with `readingDeskId`'s row in view and `cams` each desk's
   * camera: where the reading view lays it out. */
  const readingRectOf = useCallback((current: Workspace, row: number, index: number, readingRow: number, cams: Record<string, number>, st: Stage): Rect => {
    const each = current.desks[row];
    const rect = slotRects(each.slots.length, st)[index];
    return { x: rect.x - (cams[each.deskId] ?? 0), y: rect.y + rowTop(row, st) - rowTop(readingRow, st), w: rect.w, h: rect.h };
  }, []);

  const relatedTo = useCallback((windowId: string | null | undefined): Relation[] => (windowId ? relationsOf(wsRef.current, windowId).slice(0, DRAWN_RELATIONS) : []), []);

  /** Whether a slot recedes in the overview: the selection has relations, and this slot is neither it nor one. */
  const recedes = useCallback((slot: string[], selected: string | null, related: Relation[], relationsOn: boolean): boolean => {
    if (!relationsOn || !selected || related.length === 0) return false;
    return !slot.includes(selected) && !slot.some((id) => related.some((relation) => relation.windowId === id));
  }, []);

  const planZoom = useCallback((base: 0 | 1, readingDeskId: string, cams: Record<string, number>, selected: string | null, B: Camera, fullWindowId: string | null = null): ZoomPlan | null => {
    const current = wsRef.current;
    const layout = ovLayoutRef.current;
    const st = stageNow.current;
    if (!layout) return null;
    const readingRow = Math.max(0, current.desks.findIndex((each) => each.deskId === readingDeskId));
    const related = relatedTo(selected);
    const items: ZoomPlan["items"] = [];
    const rings: ZoomPlan["rings"] = [];
    current.desks.forEach((each, row) => each.slots.forEach((slot, index) => {
      const a = readingRectOf(current, row, index, readingRow, cams, st);
      const b = layout.cards[row][index];
      const readingPanes = paneRects(a, slot.length);
      const cardPanes = paneRects(b, slot.length);
      const live = visitedRef.current.has(each.deskId) && each.deskId === readingDeskId && intersects(a, st);
      const recede = recedes(slot, selected, related, showRelationsRef.current);
      const focus = selected !== null && slot.includes(selected);
      const isRelated = showRelationsRef.current && slot.some((id) => related.some((relation) => relation.windowId === id));
      slot.forEach((id, pane) => {
        // A window opened in focus mode lands on the whole stage.
        const pa = id === fullWindowId && each.deskId === readingDeskId ? { x: 0, y: 0, w: st.width, h: st.height } : readingPanes[pane];
        const pb = cardPanes[pane];
        items.push({ key: id, a: pa, b: pb, base: base === 0 ? pa : pb, live, recede, focus: focus && id === selected });
      });
      if (focus || isRelated) rings.push({ key: slotKey(each.deskId, slot), a, b });
    }));
    return { base, A: IDENTITY, B, items, rings };
  }, [readingRectOf, relatedTo, recedes]);

  const zoomTargets = useCallback(() => ({
    world: worldRef.current as HTMLElement,
    slots: slotElements(),
    rings: new Map(ringEls.current),
    late: [...lateEls.current.values()],
    slivers: [...sliverEls.current.values()],
    followers: [(q: number | null) => companionRef.current?.zoomFrame(q)],
  }), [slotElements]);

  /** Reduced motion (spec §6.3): no zoom, the view swaps at once under a short crossfade. Every way into a
   * transition (a key, the button, the wheel, a drag) comes through `beginEnter` or `beginLeave`, which
   * take this path instead of starting a zoom. */
  const crossfade = useCallback((enter: boolean, to: { deskId: string; windowId: string | null } | null, focusAfter: boolean) => {
    transitionGen.current += 1;
    const world = worldRef.current;
    world?.classList.remove("desk-fadeswap");
    void world?.offsetWidth;
    world?.classList.add("desk-fadeswap");
    setPanEase(false);
    if (enter) {
      const id = deskIdRef.current;
      if (!id) return;
      if (focusModeRef.current) setFocusMode(false);
      preOverview.current = { deskId: id, focusId: focusIdRef.current };
      setSelection(focusIdRef.current ? { deskId: id, windowId: focusIdRef.current } : null);
      setOvCam(enteringCamera(cardOf(focusIdRef.current), stageNow.current));
      setOverview(true);
      return;
    }
    const target = to ?? (preOverview.current ? { deskId: preOverview.current.deskId, windowId: preOverview.current.focusId } : null);
    setOverview(false);
    if (target) {
      setCurrentDeskId(target.deskId);
      if (target.windowId) commit(setFocus(wsRef.current, target.deskId, target.windowId));
    }
    if (focusAfter) setFocusMode(true);
  }, [cardOf, setCurrentDeskId, commit]);

  /** Start a zoom from the reading view (into the overview); returns false when one cannot start (or when
   * reduced motion swapped the view at once instead). */
  const beginEnter = useCallback((): boolean => {
    if (controller.active || overviewRef.current || !worldRef.current) return false;
    const id = deskIdRef.current;
    if (!id) return false;
    if (reduced) {
      crossfade(true, null, false);
      return false;
    }
    transitionGen.current += 1;
    if (focusModeRef.current) flushSync(() => setFocusMode(false));
    const selected = focusIdRef.current;
    preOverview.current = { deskId: id, focusId: selected };
    const B = enteringCamera(cardOf(selected), stageNow.current);
    flushSync(() => {
      setZooming(true);
      setSelection(selected ? { deskId: id, windowId: selected } : null);
    });
    const plan = planZoom(0, id, camXRef.current, selected, B);
    if (!plan) return false;
    controller.begin(plan, zoomTargets());
    return true;
  }, [controller, cardOf, planZoom, zoomTargets, reduced, crossfade]);

  /** Start a zoom from the overview back into a desk: the selected card's, or where the overview was
   * entered from. */
  const beginLeave = useCallback((to: { deskId: string; windowId: string | null } | null, focusAfter = false): boolean => {
    if (controller.active || !overviewRef.current || !worldRef.current) return false;
    if (reduced) {
      crossfade(false, to, focusAfter);
      return false;
    }
    transitionGen.current += 1;
    // The world's camera has one animator: a keyboard pan still easing under the CSS transition is taken
    // where it shows now, and the transition goes before the zoom writes the camera.
    if (panEaseRef.current) {
      const shown = displayedCamera(worldRef.current) ?? ovCamRef.current;
      flushSync(() => {
        setPanEase(false);
        setOvCam(shown);
      });
    }
    const target = to ?? preOverview.current ?? (selectionRef.current ? { deskId: selectionRef.current.deskId, focusId: selectionRef.current.windowId } : null);
    if (!target) return false;
    const deskIdTo = target.deskId;
    const windowTo = "windowId" in target ? target.windowId : target.focusId;
    const current = wsRef.current;
    const each = deskById(current, deskIdTo);
    if (!each) return false;
    const fullWindowId = focusAfter && windowTo ? windowTo : null;
    // Before planning, the destination is laid out as the commit will show it, so the zoom's last frame is
    // the commit: its desk's content mounted (paused) if it was never opened, the selection on the window
    // it opens, and for focus mode the full-screen shell and the window's full-screen layout.
    flushSync(() => {
      setVisited((seen) => (seen.has(deskIdTo) ? seen : new Set([...seen, deskIdTo])));
      if (windowTo) setSelection({ deskId: deskIdTo, windowId: windowTo });
      setLeaveTarget({ deskId: deskIdTo, cams: camXRef.current, focusWindowId: fullWindowId });
    });
    const node = stageRef.current;
    if (node && node.clientWidth > 0 && node.clientHeight > 0 && (node.clientWidth !== stageNow.current.width || node.clientHeight !== stageNow.current.height)) {
      flushSync(() => setStage({ width: node.clientWidth, height: node.clientHeight }));
    }
    const cams = { ...camXRef.current };
    const index = windowTo ? slotIndexOf(each, windowTo) : -1;
    cams[deskIdTo] = ensureVisible(cams[deskIdTo] ?? 0, index >= 0 ? index : focusedSlot(current, each), each.slots.length, stageNow.current);
    const plan = planZoom(1, deskIdTo, cams, windowTo, ovCamRef.current, fullWindowId);
    if (!plan) {
      flushSync(() => setLeaveTarget(null));
      return false;
    }
    pendingLeave.current = { deskId: deskIdTo, windowId: windowTo, cams, focusMode: focusAfter };
    flushSync(() => {
      setZooming(true);
      setLeaveTarget({ deskId: deskIdTo, cams, focusWindowId: fullWindowId });
    });
    controller.begin(plan, zoomTargets());
    return true;
  }, [controller, planZoom, zoomTargets, reduced, crossfade]);

  /** The zoom ended: the one commit, whose layout is the zoom's last frame. */
  onEndRef.current = (goal, base) => {
    const plan = controller.plan;
    controller.clean();
    if (goal === base) {
      flushSync(() => {
        setZooming(false);
        setLeaveTarget(null);
      });
      pendingLeave.current = null;
      return;
    }
    if (goal === 1) {
      flushSync(() => {
        setOverview(true);
        if (plan) setOvCam(plan.B);
        setZooming(false);
      });
      return;
    }
    const leave = pendingLeave.current;
    pendingLeave.current = null;
    flushSync(() => {
      setOverview(false);
      // `zooming` stays one more frame: the windows' left/top transitions must not animate the commit's
      // layout from the cards back to the slots it already shows.
      if (leave) {
        setCamX(leave.cams);
        setCurrentDeskId(leave.deskId);
        if (leave.windowId) commit(setFocus(wsRef.current, leave.deskId, leave.windowId));
        if (leave.focusMode) setFocusMode(true);
      }
    });
    // Only this transition's own cleanup: a zoom started since (o pressed during the exit) keeps its state.
    const generation = transitionGen.current;
    frameClock.request(() => frameClock.request(() => {
      if (transitionGen.current !== generation) return;
      setZooming(false);
      setLeaveTarget(null);
    }));
  };

  /** alt+o, o, the button, esc, ↵: the fast eased zoom (a crossfade with reduced motion). */
  const toggleOverview = useCallback((to: { deskId: string; windowId: string | null } | null = null, focusAfter = false) => {
    if (controller.active) {
      controller.go(overviewRef.current ? 1 : 0);
      return;
    }
    if (overviewRef.current) {
      if (beginLeave(to, focusAfter)) controller.go(0);
    } else if (beginEnter()) {
      controller.go(1);
    }
  }, [controller, beginEnter, beginLeave]);

  // The overview's selection is always a card on show: a selection that names no window there (none on
  // entering, a window closed or moved by a reload) becomes the reading focus's card, else the first card.
  useEffect(() => {
    if (!overview || !ws) return;
    if (selection && ws.windows[selection.windowId]?.deskId === selection.deskId) return;
    const focusWindow = focusId ? ws.windows[focusId] : null;
    if (focusWindow) {
      setSelection({ deskId: focusWindow.deskId, windowId: focusWindow.windowId });
      return;
    }
    const first = ws.desks.find((each) => each.slots.length > 0);
    const windowId = first ? first.slots[0].find((id) => ws.windows[id]?.active) ?? first.slots[0][0] : null;
    setSelection(first && windowId ? { deskId: first.deskId, windowId } : null);
  }, [overview, ws, selection, focusId]);
  // After a card is moved (alt+[ ], alt+shift+j/k) the camera follows it to its new place.
  const followMoved = useRef(false);
  useEffect(() => {
    if (!followMoved.current || !overview || !selection) return;
    followMoved.current = false;
    const rect = cardOf(selection.windowId);
    if (!rect) return;
    setPanEase(true);
    setOvCam((cam) => followSelection(cam, rect, stageNow.current));
  }, [overview, ovLayout, selection, cardOf]);

  /** Move the overview's selection; the camera follows over .2 s, keeping it 48 px inside. */
  const moveOverviewSelection = useCallback((direction: "left" | "right" | "up" | "down") => {
    const layout = ovLayoutRef.current;
    const current = wsRef.current;
    const sel = selectionRef.current;
    if (!layout) return;
    let row = sel ? current.desks.findIndex((each) => each.deskId === sel.deskId) : 0;
    let slot = sel ? slotIndexOf(current.desks[row] ?? current.desks[0], sel.windowId) : 0;
    if (row < 0 || slot < 0) {
      row = 0;
      slot = 0;
    }
    const next = moveSelection(layout, { row, slot }, direction);
    const each = current.desks[next.row];
    const windowId = each?.slots[next.slot]?.find((id) => current.windows[id]?.active) ?? each?.slots[next.slot]?.[0];
    if (!each || !windowId) return;
    setSelection({ deskId: each.deskId, windowId });
    setPanEase(true);
    setOvCam((cam) => followSelection(cam, layout.cards[next.row][next.slot], stageNow.current));
  }, []);

  /** Gather around the focus (spec §6.6): linked windows to its right, or to a new desk. */
  const gather = useCallback((toNewDesk: boolean) => {
    const current = wsRef.current;
    const id = deskIdRef.current;
    const focus = focusIdRef.current;
    const each = id ? deskById(current, id) : null;
    if (!id || !focus || !each) return;
    if (!toNewDesk && ungather && ungather.deskId === id) {
      commit(reorderSlots(current, id, ungather.order));
      setUngather(null);
      return;
    }
    const related = relationsOf(current, focus).filter((relation) => current.windows[relation.windowId]?.deskId === id);
    if (related.length === 0) {
      toastNow("nothing on this desk is linked to this window yet");
      return;
    }
    const { order, stayed } = gatherOrder(each.slots, focus, related);
    if (!toNewDesk) {
      setUngather({ deskId: id, order: each.slots.map((slot) => [...slot]) });
      commit(reorderSlots(current, id, order));
      if (stayed > 0) toastNow(`gathered · and ${stayed} more stayed (four move along at most)`);
      return;
    }
    // To a new desk: the focus and its linked windows (four at most), the focus first.
    const moving = [focus, ...related.slice(0, DRAWN_RELATIONS).map((relation) => relation.windowId)];
    const newDeskId = mintId("desk");
    const title = `gathered · ${shortName(titleOf(current.windows[focus]))}`;
    let step = createDesk(current, newDeskId, title);
    let after: string | null = null;
    for (const windowId of moving) {
      const next = moveToDesk(step.ws, id, windowId, newDeskId, after);
      step = { ws: next.ws, ops: [...step.ops, ...next.ops] };
      after = windowId;
    }
    const focused = setFocus(step.ws, newDeskId, focus);
    step = { ws: focused.ws, ops: [...step.ops, ...focused.ops] };
    commit(step);
    setMovedNotice({ deskId: id, title, until: timers.now() + MOVED_NOTICE_MS });
    if (related.length > DRAWN_RELATIONS) toastNow(`moved to “${title}” · and ${related.length - DRAWN_RELATIONS} more stayed`);
    setCurrentDeskId(newDeskId);
  }, [commit, mintId, setCurrentDeskId, timers, titleOf, toastNow, ungather]);

  /** The window menu's ⊞ New desk from these (spec §5.1, §9.2): the window moves to a new desk with its linked
   * thread windows (none needed), titled from it; not gather, which moves what is related and refuses alone. */
  const newDeskFrom = useCallback((windowId: string) => {
    const current = wsRef.current;
    const id = deskIdRef.current;
    if (!id || current.windows[windowId]?.deskId !== id) return;
    const threads = relationsOf(current, windowId)
      .filter((relation) => current.windows[relation.windowId]?.deskId === id && current.windows[relation.windowId]?.content?.kind === "thread")
      .map((relation) => relation.windowId);
    const newDeskId = mintId("desk");
    const window = current.windows[windowId];
    // A comparison's window title can contain the passage used as its query.
    const title = `new desk · ${window.content?.kind === "compare" ? "comparison" : shortName(titleOf(window))}`;
    let step = createDesk(current, newDeskId, title);
    let after: string | null = null;
    for (const moving of [windowId, ...threads]) {
      const next = moveToDesk(step.ws, id, moving, newDeskId, after);
      step = { ws: next.ws, ops: [...step.ops, ...next.ops] };
      after = moving;
    }
    const focused = setFocus(step.ws, newDeskId, windowId);
    commit({ ws: focused.ws, ops: [...step.ops, ...focused.ops] });
    setMovedNotice({ deskId: id, title, until: timers.now() + MOVED_NOTICE_MS });
    setCurrentDeskId(newDeskId);
  }, [commit, mintId, setCurrentDeskId, timers, titleOf]);

  const run = useCallback((action: DeskAction): boolean => {
    const current = wsRef.current;
    const id = deskIdRef.current;
    if (!id) return false;
    const focus = focusIdRef.current;
    switch (action.kind) {
      case "focusAlong":
        commit(focusAlong(current, id, action.direction));
        return true;
      case "paneOrDesk": {
        // In a pad stack, alt+j/k goes to the next pad (or split pane) first, then on to the next desk.
        const stack = focusedStackRef.current();
        if (stack && stack.padOrDesk(action.direction)) return true;
        const step = focusPane(current, id, action.direction);
        if (step) commit(step);
        else switchDesk(action.direction);
        return true;
      }
      case "moveWindow": {
        const sel = overviewRef.current ? selectionRef.current : null;
        if (sel) {
          const each = deskById(current, sel.deskId);
          const index = each ? slotIndexOf(each, sel.windowId) : -1;
          if (each && index >= 0) {
            followMoved.current = true;
            commit(moveWindowTo(current, sel.deskId, sel.windowId, index + action.direction));
          }
          return true;
        }
        commit(moveFocused(current, id, action.direction));
        return true;
      }
      case "moveToDesk": {
        const sel = selectionRef.current;
        if (!overviewRef.current || !sel) return true;
        const row = current.desks.findIndex((each) => each.deskId === sel.deskId);
        const to = current.desks[row + action.direction];
        const from = current.desks[row];
        if (!to || !from) return true;
        const index = slotIndexOf(from, sel.windowId);
        followMoved.current = true;
        commit(moveToDeskAt(current, sel.deskId, sel.windowId, to.deskId, index));
        setSelection({ deskId: to.deskId, windowId: sel.windowId });
        return true;
      }
      case "overview":
        toggleOverview();
        return true;
      case "overviewMove":
        moveOverviewSelection(action.direction);
        return true;
      case "overviewOpen": {
        const sel = selectionRef.current;
        toggleOverview(sel ? { deskId: sel.deskId, windowId: sel.windowId } : null, action.focusMode);
        return true;
      }
      case "leaveOverview":
        toggleOverview(null);
        return true;
      case "closeStrip":
        setStripOpen(false);
        return true;
      case "toggleRelations":
        setShowRelations((on) => !on);
        return true;
      case "gatherPreview":
        setGatherPreview(true);
        return true;
      case "gather":
        gather(action.toNewDesk);
        return true;
      case "pair":
        commit(pairFocused(current, id));
        return true;
      case "unpair":
        commit(unpairFocused(current, id));
        return true;
      case "closeWindow": {
        if (!focus) return true;
        const title = titleOf(current.windows[focus]);
        commit(closeWindow(current, id, focus));
        setUndo({ deskId: id, windowId: focus, title, until: timers.now() + UNDO_CLOSE_MS });
        return true;
      }
      case "toggleFocusMode":
        if (!focus) return true;
        setFocusMode((on) => !on);
        setBadge(timers.now());
        return true;
      case "leaveFocusMode":
        setFocusMode(false);
        return true;
      case "docZoom": {
        if (!focus) return true;
        const window = current.windows[focus];
        const zoom = typeof window?.view?.zoom === "number" ? (window.view.zoom as number) : 1;
        const next = stepZoom(zoom, action.direction);
        commit(setView(current, id, focus, { ...(window?.view ?? {}), zoom: next }));
        setBadge(timers.now());
        return true;
      }
      case "swap": {
        const desk = deskById(current, id);
        if (!desk || !focus) return true;
        const index = slotIndexOf(desk, focus);
        const shown = visibilityRef.current.filter((slot) => slot.inView).map((slot) => slot.index);
        const other = shown.find((slot) => slot !== index);
        if (other !== undefined) commit(swapInView(current, id, other));
        return true;
      }
      case "playPause": {
        const toggle = focus ? media.current.get(focus) : undefined;
        if (!toggle) return false;
        toggle();
        return true;
      }
      case "newPad": {
        const stack = focusedStackRef.current();
        if (stack) stack.newPad(focusIdRef.current ? readWindowSelection(focusIdRef.current, stageRef.current)?.quote : undefined);
        else newPadBesideRef.current();
        return true;
      }
      case "sketchBlock": {
        const stack = focusedStackRef.current();
        if (!stack) return false;
        stack.sketchBlock();
        return true;
      }
      case "arrangePads": {
        const stack = focusedStackRef.current();
        if (!stack) return false;
        stack.arrange();
        return true;
      }
      case "nextPad": {
        const stack = focusedStackRef.current();
        if (!stack) return false;
        stack.nextPad(action.direction);
        return true;
      }
      case "menu": {
        // `.` or the ContextMenu key: the pad menu on the hovered line; else the menu on the hovered object, or on
        // the focused window's first object.
        // A focused stack with no hovered line falls through to the hovered object (a passage beside it).
        const stack = focusedStackRef.current();
        if (stack?.menuAtHover()) return true;
        return openMenuByKeyRef.current();
      }
      case "marginNote":
        return hoveredKeyRef.current("note");
      case "promoted":
        return hoveredKeyRef.current("promoted");
      case "drain":
        setDraining(true);
        return true;
      case "companion":
        companionKeyRef.current(action.atDock);
        return true;
      case "search":
        setSearch({ query: "" });
        return true;
      case "path":
        // The goal's path view; with no goal, the focused book's own path in its window.
        if (goalPathRef.current.toggle()) return true;
        return focusIdRef.current ? inquiries.current.get(focusIdRef.current)?.showPath("toggle") ?? false : false;
      case "follow":
        return videoKeys.current.follow();
      case "timestamp":
        return videoKeys.current.timestamp();
      case "pen":
        setPenOn((on) => !on);
        return true;
      default:
        return false;
    }
  }, [commit, switchDesk, timers, titleOf, toggleOverview, moveOverviewSelection, gather]);
  const visibilityRef = useRef(visibility);
  visibilityRef.current = visibility;
  const runRef = useRef(run);
  runRef.current = run;

  // -- the key router: one capture listener, the matrix, the bare-Alt rule --------------------------

  const modifiers = useMemo(() => new ModifierTracker(), []);
  const altTracker = useMemo(
    () => new BareAltTracker(timers, () => setWhichKey(true), () => setWhichKey(false)),
    [timers],
  );
  const router = useMemo(() => new DeskListenerRouter({
    // In the overview every window is a card: none owns input (the reading focus is only remembered).
    activeWindowId: () => (overviewRef.current ? null : focusIdRef.current),
    isPaused: (windowId) => isPaused(lifecyclesRef.current[windowId]?.state ?? "hidden"),
    onPointerWindow: (windowId) => {
      const current = wsRef.current;
      const id = deskIdRef.current;
      if (!id || focusIdRef.current === windowId) return;
      const owner = current.windows[windowId];
      if (!owner || owner.deskId !== id) return;
      focusIdRef.current = windowId;
      commit(setFocus(current, id, windowId));
    },
    intercept: (type, phase, event) => {
      if (phase !== "capture") return false;
      if (type === "blur") {
        // The window itself losing focus (not an element blurring as a press moves the focus).
        if (!(event.target instanceof Node)) cancelDragRef.current();
        modifiers.blur();
        altTracker.cancel();
        altTracker.reset();
        return false;
      }
      if (type === "mousedown") {
        altTracker.cancel();
        // A pointer press during a zoom settles it at once (spec §6.3).
        if (controller.active) controller.settle();
        return false;
      }
      if (!(event instanceof KeyboardEvent)) return false;
      if (type === "keyup") {
        modifiers.keyup(event);
        if (event.key === "g" || event.key === "G") setGatherPreview(false);
        // The shell's tracker is the one that saw every key while Alt was down (a chord it took never reaches
        // a window): only a confirmed tap's release goes on to a window's capture-clearing gesture. A hold
        // (which-key) or a chord keeps it.
        const outcome = altTracker.release(event);
        return outcome !== null && outcome !== "tap";
      }
      if (type !== "keydown") return false;
      modifiers.keydown(event);
      altTracker.keydown(event);
      if (event.key === "Alt" || event.key === "Control" || event.key === "Shift" || event.key === "Meta") return false;
      // A key press during a zoom settles it first (spec §6.3); a repeat does not.
      if (controller.active && !event.repeat) controller.settle();
      const open = claimed.current.get(focusIdRef.current ?? "");
      const has = (scope: ClaimedScope) => (open?.get(scope)?.size ?? 0) > 0;
      const resolution = resolveKey(event, {
        typing: isTypingTarget(event.target),
        // A claim with the focus on the page (the Reader's intent box): the selection's shortcuts still pass.
        typingClaim: has("typing"),
        // Search in context or the drain is open: its keys are its own (as an open menu owns them).
        menu: has("menu") || searchOpenRef.current || drainingRef.current || menuOpenRef.current || goalPathRef.current.open,
        check: has("check"),
        focus: focusModeRef.current,
        pen: penOnRef.current,
        overview: overviewRef.current,
        strip: stripOpenRef.current,
      }, modifiers.read(event));
      if (!resolution || resolution.binding.later) return false;
      if (!runRef.current(resolution.binding.action)) return false;
      event.preventDefault();
      event.stopPropagation();
      return true;
    },
  }), [modifiers, altTracker, commit, controller]);
  useEffect(() => {
    router.ensure("window", "keydown");
    router.ensure("window", "keyup");
    router.ensure("window", "mousedown");
    router.ensure("window", "blur");
    return () => router.dispose();
  }, [router]);
  // The scopes each window's content has open (a Reader's menu, its intent box): the router reads the
  // active window's before the desk's own bindings.
  const claimed = useRef(new Map<string, Map<ClaimedScope, Set<string>>>());
  const claimsByWindow = useRef(new Map<string, ScopeClaims>());
  const claimsFor = useCallback((windowId: string): ScopeClaims => {
    let claims = claimsByWindow.current.get(windowId);
    if (!claims) {
      claims = {
        claim: (scope, owner, open) => {
          const byScope = claimed.current.get(windowId) ?? new Map<ClaimedScope, Set<string>>();
          const owners = byScope.get(scope) ?? new Set<string>();
          if (open) owners.add(owner);
          else owners.delete(owner);
          byScope.set(scope, owners);
          claimed.current.set(windowId, byScope);
        },
      };
      claimsByWindow.current.set(windowId, claims);
    }
    return claims;
  }, []);
  const hubs = useRef(new Map<string, ListenerHub>());
  const hubFor = useCallback((windowId: string): ListenerHub => {
    let hub = hubs.current.get(windowId);
    if (!hub) {
      hub = router.hubFor(windowId);
      hubs.current.set(windowId, hub);
    }
    return hub;
  }, [router]);

  // -- the world's camera at rest, the wheel router, ctrl+drag, the overview's drags (spec §5.5, §6.2) -------

  // At rest the world's transform is the committed view's camera; a zoom writes it itself.
  useLayoutEffect(() => {
    const world = worldRef.current;
    if (!world || controller.active) return;
    world.style.transform = overview ? cameraTransform(ovCam) : "";
  });

  const mainRef = useRef<HTMLElement | null>(null);
  const gesture = useRef<{ kind: "pan" | "zoom" | "scroll" | "ovpan"; source?: ZoomSource; zoom?: ZoomGesture; timer: unknown; panned: boolean } | null>(null);
  const endGesture = useCallback(() => {
    const g = gesture.current;
    gesture.current = null;
    setHud("");
    if (!g) return;
    if (g.kind === "zoom" && g.zoom && !g.zoom.latch && controller.active) {
      // The fingers lifted mid-zoom: complete past 40 % of the way, else spring back.
      controller.release();
    }
    if (g.kind === "pan" && g.panned) {
      // Snap to the nearest window's left edge and focus it.
      const current = wsRef.current;
      const id = deskIdRef.current;
      const each = id ? deskById(current, id) : null;
      if (!id || !each || each.slots.length === 0) return;
      const st = stageNow.current;
      const rects = slotRects(each.slots.length, st);
      const cam = camXRef.current[id] ?? 0;
      let best = 0;
      rects.forEach((rect, index) => {
        if (Math.abs(rect.x - DESK_SIZES.side - cam) < Math.abs(rects[best].x - DESK_SIZES.side - cam)) best = index;
      });
      const snapped = ensureVisible(rects[best].x - DESK_SIZES.side, best, each.slots.length, st);
      setCamX((cams) => ({ ...cams, [id]: snapped }));
      const target = each.slots[best].find((windowId) => current.windows[windowId]?.active) ?? each.slots[best][0];
      commit(setFocus(current, id, target));
    }
  }, [controller, commit]);

  useEffect(() => {
    const main = mainRef.current;
    if (!main) return;
    const onWheel = (event: WheelEvent) => {
      const target = event.target as Element | null;
      if (!target || !target.closest("[data-desk-stage], .desk-shelf, .desk-shelf-rail")) return;
      // Alt used with the wheel is a gesture, not a bare-Alt tap: its release clears no capture and the
      // which-key panel does not show.
      if (event.altKey || modifiers.read().alt) altTracker.cancel();
      const st = stageNow.current;
      const now = performance.now();
      let g = gesture.current;
      if (!g) {
        // The tracked keys only: classifyWheel reads the event's own flags itself (a pinch is ctrl+wheel
        // with no Ctrl key held).
        const kind = classifyWheel(event, modifiers.read(), st.height);
        // In the overview a plain wheel pans its camera; alt or ctrl zooms back in.
        const ovPlain = overviewRef.current && kind.kind !== "zoom";
        g = gesture.current = {
          kind: ovPlain ? "ovpan" : kind.kind,
          source: kind.source,
          zoom: kind.kind === "zoom" && kind.source ? newZoomGesture(kind.source, now) : undefined,
          timer: null,
          panned: false,
        };
      }
      if (g.kind === "scroll") {
        // A plain scroll is the window's own (it never pans the strip).
        timers.clear(g.timer);
        g.timer = timers.set(endGesture, OVERVIEW.gestureIdleMs);
        return;
      }
      event.preventDefault();
      const { dx, dy } = normalizedDelta(event, st.height);
      if (g.kind === "ovpan") {
        setPanEase(false);
        setOvCam((cam) => ({ ...cam, x: cam.x - (event.shiftKey ? dy : dx), y: cam.y - (event.shiftKey ? 0 : dy) }));
        timers.clear(g.timer);
        g.timer = timers.set(endGesture, OVERVIEW.gestureIdleMs);
        return;
      }
      if (g.kind === "pan") {
        if (overviewRef.current || focusModeRef.current) return;
        const id = deskIdRef.current;
        const each = id ? deskById(wsRef.current, id) : null;
        if (!id || !each) return;
        const travel = Math.abs(dx) > Math.abs(dy) ? dx : dy;
        const max = Math.max(0, slotRects(each.slots.length, st).reduce((end, rect) => Math.max(end, rect.x + rect.w), 0) + DESK_SIZES.side - st.width);
        setCamX((cams) => ({ ...cams, [id]: Math.max(0, Math.min(max, (cams[id] ?? 0) + travel)) }));
        g.panned = true;
        setHud("Alt + swipe to move between windows. Lift your fingers to stop.");
        timers.clear(g.timer);
        g.timer = timers.set(endGesture, OVERVIEW.panSnapMs);
        return;
      }
      // The zoom: alt + vertical, ctrl + scroll, or a pinch.
      if (!g.zoom) return;
      const result = zoomWheel(g.zoom, dy, now, { active: controller.active, inOverview: overviewRef.current, target: controller.target });
      g.zoom = result.gesture;
      const stepped = result.step;
      if (stepped.kind === "begin-and-target") {
        const began = overviewRef.current ? beginLeave(selectionRef.current ? { deskId: selectionRef.current.deskId, windowId: selectionRef.current.windowId } : null) : beginEnter();
        if (began) controller.setTarget(stepped.target);
      } else if (stepped.kind === "target") {
        controller.setTarget(stepped.target);
      } else if (stepped.kind === "goal") {
        if (!controller.active) {
          const began = stepped.goal === 1 ? beginEnter() : beginLeave(selectionRef.current ? { deskId: selectionRef.current.deskId, windowId: selectionRef.current.windowId } : null);
          if (!began) return;
        }
        controller.go(stepped.goal);
      }
      if (stepped.kind === "target" || stepped.kind === "begin-and-target") {
        const how = g.source === "pinch" ? "pinch" : modifiers.read(event).alt ? "alt + scroll" : "ctrl + scroll";
        setHud(`${how} · zooming ${dy > 0 ? "out" : "in"} · lift your fingers to stop`);
      } else {
        setHud("");
      }
      timers.clear(g.timer);
      g.timer = timers.set(endGesture, stepped.armMs);
    };
    main.addEventListener("wheel", onWheel, { passive: false, capture: true });
    return () => main.removeEventListener("wheel", onWheel, { capture: true });
  }, [ws === null, modifiers, altTracker, timers, controller, beginEnter, beginLeave, endGesture]);

  // Ctrl+drag on the stage background scrubs the zoom (320 px is the whole zoom); in the overview a drag
  // on the background pans, and a card dragged farther than 8 px moves.
  const drag = useRef<{ kind: "scrub" | "pan" | "card"; x: number; y: number; base: 0 | 1; cam: Camera; key?: string; windowId?: string; deskId?: string; moved: boolean } | null>(null);
  const onStagePointerDown = useCallback((event: React.PointerEvent<HTMLElement>) => {
    const target = event.target as Element;
    const onCard = target.closest("[data-desk-slot]");
    // A sliver is background (spec §5.5): a ctrl+drag from it scrubs, and its click still navigates.
    const onSliver = target.closest(".desk-sliver") !== null;
    const inContent = !onSliver && target.closest(".desk-slot-inner, button, input, textarea") !== null;
    if (overviewRef.current) {
      if (onCard) {
        const key = onCard.getAttribute("data-desk-slot-key") ?? undefined;
        const windowId = onCard.getAttribute("data-desk-slot-window") ?? undefined;
        const deskOf = onCard.getAttribute("data-desk-slot-desk") ?? undefined;
        drag.current = { kind: "card", x: event.clientX, y: event.clientY, base: 1, cam: ovCamRef.current, key, windowId, deskId: deskOf, moved: false };
      } else {
        drag.current = { kind: "pan", x: event.clientX, y: event.clientY, base: 1, cam: ovCamRef.current, moved: false };
      }
      (event.currentTarget as HTMLElement).setPointerCapture?.(event.pointerId);
      return;
    }
    if ((event.ctrlKey || modifiers.read().ctrl) && !inContent && !focusModeRef.current) {
      drag.current = { kind: "scrub", x: event.clientX, y: event.clientY, base: 0, cam: IDENTITY, moved: false };
      (event.currentTarget as HTMLElement).setPointerCapture?.(event.pointerId);
      event.preventDefault();
    }
  }, [modifiers]);
  const onStagePointerMove = useCallback((event: React.PointerEvent<HTMLElement>) => {
    const d = drag.current;
    if (!d) return;
    const dx = event.clientX - d.x;
    const dy = event.clientY - d.y;
    if (d.kind === "scrub") {
      if (!controller.active && !beginEnter()) {
        drag.current = null;
        return;
      }
      d.moved = true;
      controller.setTarget(dragProgress(d.base, dy));
      setHud("Ctrl + drag to zoom. Let go to stop.");
      return;
    }
    if (d.kind === "pan") {
      d.moved = d.moved || Math.hypot(dx, dy) > 3;
      setPanEase(false);
      setOvCam({ ...d.cam, x: d.cam.x + dx, y: d.cam.y + dy });
      return;
    }
    if (!d.moved && Math.hypot(dx, dy) <= OVERVIEW.cardDragPx) return;
    d.moved = true;
    const element = d.windowId ? boxEls.current.get(d.windowId) : null;
    if (element) {
      element.style.transform = `translate(${dx / d.cam.s}px, ${dy / d.cam.s}px)`;
      element.style.zIndex = "30";
    }
  }, [controller, beginEnter]);
  /** A gesture the system took away (pointercancel, a lost capture, the window losing focus): the card
   * goes back to its place and a scrub settles; nothing moves until the next press. */
  const cancelDrag = useCallback(() => {
    const d = drag.current;
    drag.current = null;
    if (!d) return;
    if (d.kind === "scrub") {
      setHud("");
      if (controller.active) controller.settle();
      return;
    }
    const element = d.windowId ? boxEls.current.get(d.windowId) : null;
    if (element) {
      element.style.transform = "";
      element.style.zIndex = "";
    }
  }, [controller]);
  const cancelDragRef = useRef(cancelDrag);
  cancelDragRef.current = cancelDrag;
  // A click that ends a scrub started on a sliver is the scrub's, not the sliver's.
  const scrubbedClick = useRef(false);
  const onStagePointerUp = useCallback((event: React.PointerEvent<HTMLElement>) => {
    const d = drag.current;
    drag.current = null;
    if (!d) return;
    if (d.kind === "scrub") {
      setHud("");
      if (d.moved) scrubbedClick.current = true;
      if (controller.active) controller.release();
      return;
    }
    if (d.kind !== "card" || !d.windowId || !d.deskId) return;
    const element = d.windowId ? boxEls.current.get(d.windowId) : null;
    if (element) {
      element.style.transform = "";
      element.style.zIndex = "";
    }
    if (!d.moved) {
      // A click on a card opens it.
      setSelection({ deskId: d.deskId, windowId: d.windowId });
      toggleOverview({ deskId: d.deskId, windowId: d.windowId });
      return;
    }
    const layout = ovLayoutRef.current;
    const stageBox = (event.currentTarget as HTMLElement).getBoundingClientRect();
    if (!layout) return;
    const point = { x: (event.clientX - stageBox.left - d.cam.x) / d.cam.s, y: (event.clientY - stageBox.top - d.cam.y) / d.cam.s };
    const drop = dropTarget(layout, point);
    const current = wsRef.current;
    const to = drop ? current.desks[drop.row] : null;
    if (!drop || !to) return;
    if (to.deskId === d.deskId) {
      const from = slotIndexOf(to, d.windowId);
      commit(moveWindowTo(current, d.deskId, d.windowId, Math.min(drop.slot > from ? drop.slot - 1 : drop.slot, to.slots.length - 1)));
    } else {
      commit(moveToDeskAt(current, d.deskId, d.windowId, to.deskId, drop.slot));
      setSelection({ deskId: to.deskId, windowId: d.windowId });
    }
  }, [controller, toggleOverview, commit]);

  // A window's picture goes stale when its content changes (a note, a panel's list, a page turned), not
  // only when its status does: any change inside a window's content marks its picture for a rebuild.
  useEffect(() => {
    const world = worldRef.current;
    if (!world || typeof MutationObserver === "undefined") return;
    const observer = new MutationObserver((records) => {
      for (const record of records) {
        const node = record.target instanceof Element ? record.target : record.target.parentElement;
        const windowId = windowOfTarget(node);
        if (windowId) miniatures.invalidate(windowId);
      }
    });
    observer.observe(world, { subtree: true, childList: true, characterData: true });
    return () => observer.disconnect();
  }, [ws === null, miniatures]);

  // Miniatures: once the overview is committed and no zoom runs, each opened window's picture is
  // (re)built if it changed, or put back in a card host that lost it. A build never lands during a zoom:
  // a zoom starting cancels it, and the commit after the zoom schedules it again.
  useEffect(() => {
    if (!overview || zooming) return;
    const handle = timers.set(() => {
      if (controller.active) return;
      for (const [windowId, host] of miniHosts.current) {
        const body = [...document.querySelectorAll<HTMLElement>("[data-desk-window]")].find((pane) => pane.getAttribute("data-desk-window") === windowId) ?? null;
        if (!body) continue;
        if (miniatures.needs(windowId)) {
          const { node, restoreScroll } = cloneForMiniature(body);
          node.style.width = `${body.offsetWidth}px`;
          node.style.height = `${body.offsetHeight}px`;
          miniatures.store(windowId, node);
          host.replaceChildren(node);
          restoreScroll();
        } else if (!host.firstChild) {
          const node = miniatures.get(windowId);
          if (node) host.replaceChildren(node);
        }
        const node = host.firstElementChild as HTMLElement | null;
        if (node && body.offsetWidth > 0) node.style.transform = `scale(${host.clientWidth / body.offsetWidth})`;
      }
    }, 120);
    return () => timers.clear(handle);
  }, [overview, zooming, ws, timers, miniatures, controller]);

  // The harness's handle on the zoom (the commit-identity check drives p itself).
  useEffect(() => {
    onDebugHandle?.({
      beginZoom: (to, focusAfter) => (overviewRef.current ? beginLeave(to ?? null, focusAfter ?? false) : beginEnter()),
      setZoomProgress: (p) => controller.setProgress(p),
      finishZoom: (goal) => onEndRef.current(goal, controller.plan?.base ?? (goal === 1 ? 0 : 1)),
      zoomFrameTimes: () => [...controller.frameTimes],
      overview: () => overviewRef.current,
    });
  }, [onDebugHandle, controller, beginEnter, beginLeave]);

  // -- opening windows -------------------------------------------------------------------------------

  // -- Teacher lessons as windows (spec §11.1) -------------------------------------------------------

  /** The desk's stack, where a lesson lands: its first stack window, or the one ensuring its running pad makes. */
  const stackForLessons = useCallback((id: string): string | null => {
    const existing = stackWindowOf(wsRef.current, id);
    if (existing) return existing;
    const before = new Set(wsRef.current.runningPadIds ?? []);
    const step = ensureRunningPad(wsRef.current, id, () => mintId("pad"), () => mintId("win"));
    commit(step);
    for (const padId of step.ws.runningPadIds ?? []) if (!before.has(padId)) store.noteCreatedPad(padId, "running", "running", id);
    return stackWindowOf(wsRef.current, id);
  }, [wsRef, commit, mintId, store]);

  /** A stored lesson on the current desk: focused where it already is (its own window, or a stack's tab), else added
   * to the desk's stack and scrolled to. */
  const placeLesson = useCallback((lessonId: string) => {
    const id = deskIdRef.current;
    if (!id) return;
    const found = findLesson(wsRef.current, id, lessonId);
    if (found) {
      commit(setFocus(wsRef.current, id, found.windowId));
      if (found.inStack) lessonDesk.reveal(found.windowId, lessonKey(lessonId));
      return;
    }
    const stackId = stackForLessons(id);
    if (!stackId) return;
    commit(addLessonToStack(wsRef.current, id, stackId, lessonId));
    lessonDesk.reveal(stackId, lessonKey(lessonId));
  }, [wsRef, commit, lessonDesk, stackForLessons]);

  /** Every lesson entry on the desks opens a window on the current desk instead of switching screens (spec §11.1):
   * a stored lesson by its id, a new one as an opening tab in the desk's stack, stored once its turn returns. */
  const openLesson = useCallback((entry: LessonEntry) => {
    // While an inline check is open, a new lesson waits: it would teach what the veils hold (spec §12.6.4).
    const held = entry.kind === "resume" ? null : checkDesk.heldReason();
    if (held) {
      toastNow(`a lesson waits · ${held}`);
      return;
    }
    if (entry.kind === "resume") {
      placeLesson(entry.lessonId);
      return;
    }
    const id = deskIdRef.current;
    if (!id) return;
    const stackId = stackForLessons(id);
    if (!stackId) return;
    commit(setFocus(wsRef.current, id, stackId));
    lessonDesk.open(stackId, entry);
  }, [wsRef, commit, lessonDesk, placeLesson, stackForLessons, checkDesk, toastNow]);
  // An opening's lesson joins the stack it was opened in (the focus is left where the learner has it now: the
  // opening turn can take a minute).
  lessonOpened.current = (opening, lessonId) => {
    const window = wsRef.current.windows[opening.windowId];
    if (window) commit(addLessonToStack(wsRef.current, window.deskId, opening.windowId, lessonId, { focus: false }));
  };

  // A lesson the app asked for while the desks are its place (a Teach me from the inspector, a hand-off).
  const lessonRequestSeq = useRef<number | null>(null);
  const lessonRequest = lessons?.request ?? null;
  useEffect(() => {
    if (!lessonRequest || !ws || !deskId || lessonRequest.seq === lessonRequestSeq.current) return;
    lessonRequestSeq.current = lessonRequest.seq;
    if (lessonRequest.vault === undefined || lessonRequest.vault === vaultKey) openLesson(lessonRequest.entry);
    lessons?.onConsumed?.(lessonRequest.seq);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lessonRequest, ws, deskId, openLesson, vaultKey]);

  // The Reader's "Teach me this" (a source window's selection, a pad line) opens the lesson here, not as a screen.
  const reader = useMemo<ReaderPassThrough | undefined>(() => (readerProp?.onTeachMe
    ? { ...readerProp, onTeachMe: (request: { extractionId: string; spanIds: string[] }) => openLesson({ kind: "open", entry: "reader_selection", selection: request }) }
    : readerProp), [readerProp, openLesson]);

  const lessonsHost = useMemo<LessonsHost>(() => ({
    desk: lessonDesk,
    onError,
    openLesson,
    ...(lessons?.onQuickCheck ? { onQuickCheck: lessons.onQuickCheck } : {}),
    ...(lessons?.onLookInLibrary ? { onLookInLibrary: lessons.onLookInLibrary } : {}),
    ...(lessons?.onProbe ? { openProbeScreen: lessons.onProbe } : {}),
    // A notebook lesson's frame (spec §11.2); a caller may stand in its own.
    notebookFrame: lessons?.notebookFrame ?? lessonNotebookFrame,
  }), [lessonDesk, onError, openLesson, lessons?.onQuickCheck, lessons?.onLookInLibrary, lessons?.notebookFrame, lessons?.onProbe]);

  const openContent = useCallback((content: ContentRefDto, options: { spanId?: string | null; view?: Record<string, unknown>; peek?: boolean } = {}) => {
    const current = wsRef.current;
    const id = deskIdRef.current;
    if (!id) return;
    if (content.kind === "lesson") {
      // A lesson lands in the desk's stack (spec §11.1), or is focused where it already is.
      placeLesson(content.lessonId);
      setOpener(false);
      return;
    }
    const step = openBeside(current, id, content, () => mintId("win"), {
      spanId: options.spanId ?? null,
      view: { ...(options.view ?? {}), ...(options.spanId ? { spanId: options.spanId } : {}) },
    });
    keepPrevious.current = !step.existed;
    commit(step);
    if (step.existed && options.view?.compareAnchor) {
      const shown = wsRef.current.windows[step.windowId];
      commit(setView(wsRef.current, id, step.windowId, { ...shown.view, compareAnchor: options.view.compareAnchor }));
    }
    if (step.existed && options.spanId) {
      // A claim in a window already open is a peek there (its strip shows the way back); else a jump.
      const inquiry = options.peek ? inquiries.current.get(step.windowId) : undefined;
      const jump = jumps.current.get(step.windowId);
      if (inquiry) inquiry.peek(options.spanId);
      else if (jump) jump(options.spanId);
      else pendingJump.current.set(step.windowId, options.spanId);
    }
    if (!step.existed) {
      setEntering((now) => new Set([...now, step.windowId]));
      const handle = timers.set(() => {
        shellTimers.current.delete(handle);
        setEntering((now) => {
          const next = new Set(now);
          next.delete(step.windowId);
          return next;
        });
      }, 450);
      shellTimers.current.add(handle);
    }
    setOpener(false);
  }, [commit, mintId, timers, placeLesson]);

  /** The passage a window opens at for the app's open request still to be done: the book's window on the desk in view
   *  that the request would focus (the one `openBeside` finds), on the request's reading. */
  const openingAt = (windowId: string, windowDeskId: string, content: { kind: string; sourceId?: string; extractionId?: string }): string | null => {
    if (!openRequest?.spanId || !openRequest.sourceId || !ws || !deskId || windowDeskId !== deskId) return null;
    if ((doneOpenRequests.get(vaultKey) ?? -1) >= openRequest.seq) return null;
    if (content.kind !== "source" || content.sourceId !== openRequest.sourceId) return null;
    if (openRequest.reading && openRequest.reading !== content.extractionId) return null;
    const desk = deskById(ws, deskId);
    if (!desk) return null;
    const first = desk.slots.flat().find((id) => {
      const other = ws.windows[id]?.content;
      return other?.kind === "source" && other.sourceId === openRequest.sourceId;
    });
    return first === windowId ? openRequest.spanId : null;
  };

  // The app's open request: done once the desks, the library and the desk in view are there.
  useEffect(() => {
    if (!openRequest || !storeReady || !deskId || library === null) return;
    if ((doneOpenRequests.get(vaultKey) ?? -1) >= openRequest.seq) return;
    doneOpenRequests.set(vaultKey, openRequest.seq);
    if (!openRequest.sourceId) {
      if (openRequest.phrase !== undefined) setSearch({ query: openRequest.phrase });
      return;
    }
    const card = library.find((entry) => entry.sourceId === openRequest.sourceId);
    if (!card) {
      toastNow("that book isn't in your library any more");
      return;
    }
    if (card.readiness !== "ready") {
      toastNow(`“${shortName(card.title)}” is still being prepared · open it from the Library to read the original meanwhile`);
      return;
    }
    void transport.resolveExtraction(card.sourceId).then((extractionId) => {
      // A passage found on an earlier reading of the book is not a passage of the reading it has now: the book opens.
      const sameReading = !openRequest.reading || openRequest.reading === extractionId;
      openContent(contentForCard(card, extractionId), { spanId: sameReading ? openRequest.spanId : null });
      if (!sameReading && openRequest.spanId) toastNow("that passage was on an earlier reading of this book · it opened at your place in it");
    }, () => toastNow("couldn't open that book just now"));
  }, [openRequest, storeReady, deskId, library, vaultKey, transport, openContent, toastNow]);

  const openHit = useCallback((hit: { sourceId: string | null; extractionId: string; spanId: string }) => {
    if (!hit.sourceId) return;
    const card = library?.find((entry) => entry.sourceId === hit.sourceId);
    const kind = card && isVideoCard(card) ? "video" : "source";
    openContent({ kind, sourceId: hit.sourceId, extractionId: hit.extractionId } as ContentRefDto, { spanId: hit.spanId });
  }, [library, openContent]);

  // -- the companion and search in context (spec §8, §9.3) ----------------------------------------------

  // The vault's companion threads: each question a polled job, kept per desk across the shell's mounts.
  const asks = useMemo(
    () => companionAsksFor(vaultKey, companionTransport, () => new CompanionAsks(companionTransport, poller, () => mintId("req"))),
    [vaultKey, companionTransport, poller, mintId],
  );
  useSyncExternalStore(asks.subscribe, asks.getVersion);
  // The threads are followed while this shell shows them; another vault's store is gone for good.
  useEffect(() => {
    asks.resume();
    return () => asks.suspend();
  }, [asks]);
  const shownVault = useRef<{ vaultKey: string; transport: object } | null>(null);
  useEffect(() => {
    const before = shownVault.current;
    if (before && (before.vaultKey !== vaultKey || before.transport !== companionTransport)) forgetCompanionAsks(before.vaultKey, before.transport);
    shownVault.current = { vaultKey, transport: companionTransport };
  }, [vaultKey, companionTransport]);
  const statusRef = useRef(status);
  statusRef.current = status;
  const companionStateRef = useRef(companionState);
  companionStateRef.current = companionState;
  const chipRef = useRef(chip);
  chipRef.current = chip;
  const searchOpenRef = useRef(false);
  searchOpenRef.current = search !== null;
  // The laptop's strip, open over the rail: the shelf shows it, the key router closes it with esc.
  const [stripOpen, setStripOpen] = useState(false);
  const stripOpenRef = useRef(false);
  stripOpenRef.current = stripOpen && viewportWidth < DESK_SIZES.shelfFoldBelow;
  // The goal lens's path view: `p` toggles it, and while it is open its keys are its own (a menu scope).
  const goalPathRef = useRef<{ open: boolean; toggle: () => boolean }>({ open: false, toggle: () => false });
  /** The lens's goal while its band shows (set where the goal desk is read, below; asked under by the companion). */
  const goalIdRef = useRef<string | null>(null);
  const anchoredAt = useRef(0);
  const groundingRef = useRef<Grounding>({ reason: "" });

  /** One step of the companion's state machine; whether it shows is remembered on the desk. */
  const stepCompanion = useCallback((event: CompanionEvent) => {
    const before = companionStateRef.current;
    const next = companionStep(before, event);
    if (next === before) return;
    companionStateRef.current = next;
    setCompanionState(next);
    if (next.mode === "anchored") anchoredAt.current = timers.now();
    const id = deskIdRef.current;
    if (id && (before.mode === "hidden") !== (next.mode === "hidden")) commit(setCompanionShown(wsRef.current, id, next.mode !== "hidden"));
  }, [commit, timers]);

  // The last pointer position over the stage: `c` with no selection anchors there.
  const lastPointer = useRef<{ x: number; y: number } | null>(null);
  useEffect(() => {
    const stageNode = stageRef.current;
    if (!stageNode) return;
    const onMove = (event: PointerEvent) => {
      const box = stageNode.getBoundingClientRect();
      lastPointer.current = { x: event.clientX - box.left, y: event.clientY - box.top };
    };
    stageNode.addEventListener("pointermove", onMove, { passive: true });
    return () => stageNode.removeEventListener("pointermove", onMove);
  }, [ws === null]);

  /** `c` (alt+c while typing) and `shift+c` (spec §8.3): summon at the selection or the cursor, dissolve when
   * anchored, back to the drawer when docked; shift+c to the dock. */
  const companionKey = (atDock: boolean) => {
    const id = focusIdRef.current;
    if (atDock) {
      // A selection is the question's context whichever key opens the companion (§8.6): shift+c takes it too.
      const selected: WindowSelection | null = id ? readWindowSelection(id, stageRef.current) : null;
      if (selected) setChip({ quote: clipQuote(selected.quote, 400), spanIds: selected.spanIds, windowId: selected.windowId });
      stepCompanion({ kind: "dock" });
      return;
    }
    let anchor: Rect | null = null;
    if (companionStateRef.current.mode === "hidden") {
      const selected: WindowSelection | null = id ? readWindowSelection(id, stageRef.current) : null;
      if (selected) {
        setChip({ quote: clipQuote(selected.quote, 400), spanIds: selected.spanIds, windowId: selected.windowId });
        anchor = selected.bounds;
      } else if (lastPointer.current) {
        anchor = { x: lastPointer.current.x, y: lastPointer.current.y, w: 1, h: 1 };
      }
    }
    // The window's width decides the narrow summon, as the mockup's (§4.3).
    const viewport = (stageRef.current?.closest(".desk-shell") as HTMLElement | null)?.clientWidth;
    stepCompanion({ kind: "c", anchor, stage: { ...stageNow.current, viewport } });
  };
  const companionKeyRef = useRef(companionKey);
  companionKeyRef.current = companionKey;
  // The palette's Ask: the companion on the focused window's reading (its selection as the chip), or left shown.
  const askRequestSeen = useRef(askRequest);
  useEffect(() => {
    if (askRequest === askRequestSeen.current) return;
    askRequestSeen.current = askRequest;
    if (companionStateRef.current.mode === "hidden") companionKeyRef.current(false);
  }, [askRequest]);

  /** A notebook frame's bridge (spec §11.3): `c` summons the companion at the frame's selection with its text as
   * the chip (untrusted notebook text, quoted), `shift` docks it, escape dissolves an anchored companion, and a
   * right-click opens the pad menu labelled for the notebook's owner. The
   * frame has already checked the message's source, origin and shape, and placed its geometry on the page. */
  const notebookMessage = (message: BridgeMessage, owner: NotebookOwner) => {
    if (message.ll === "menu") {
      // The pad menu, labelled for the notebook's owner, once the menu registers its opener (notebook/menuBridge).
      const request = notebookMenuRequest(message, owner);
      if (request) openNotebookMenu(request);
      return;
    }
    if (message.ll === "escape") {
      if (companionStateRef.current.mode === "anchored") stepCompanion({ kind: "c", anchor: null, stage: stageNow.current });
      return;
    }
    if (message.ll !== "companion") return;
    if (message.shift) {
      stepCompanion({ kind: "dock" });
      return;
    }
    const box = stageRef.current?.getBoundingClientRect();
    const anchor = message.rect && box ? { x: message.rect.x - box.left, y: message.rect.y - box.top, w: message.rect.width, h: message.rect.height } : null;
    if (message.text && companionStateRef.current.mode === "hidden") {
      setChip({ quote: clipQuote(message.text, 400), spanIds: [], windowId: focusIdRef.current ?? "" });
    }
    stepCompanion({ kind: "c", anchor, stage: stageNow.current });
  };
  const notebookMessageRef = useRef(notebookMessage);
  notebookMessageRef.current = notebookMessage;
  const notebookBridge = useMemo<NotebookBridgeHost>(() => ({ onMessage: (message, _frame, owner) => notebookMessageRef.current(message, owner) }), []);

  // The dock and whether it shows come from the desk the desks open on; after that the companion is
  // app-wide and stays where it is when the learner switches desks (a docked companion never moves).
  const companionInit = useRef(false);
  useEffect(() => {
    if (companionInit.current || !ws || !deskId) return;
    const opening = deskById(ws, deskId);
    if (!opening) return;
    companionInit.current = true;
    setCompanionDockShown(opening.companion.dock);
    if (opening.companion.shown) {
      const shown: CompanionState = { mode: "docked", origin: "drawer", anchored: null, last: "none" };
      companionStateRef.current = shown;
      setCompanionState(shown);
    }
  }, [ws, deskId]);

  const snapCompanion = useCallback((dock: CompanionDock) => {
    setCompanionDockShown(dock);
    const id = deskIdRef.current;
    if (id) commit(setCompanionDock(wsRef.current, id, dock));
    const before = companionStateRef.current;
    const next: CompanionState = { mode: "docked", origin: before.origin, anchored: null, last: "snap" };
    companionStateRef.current = next;
    setCompanionState(next);
    if (id && before.mode === "hidden") commit(setCompanionShown(wsRef.current, id, true));
  }, [commit]);

  // Hand-off (spec §8.3): an anchored companion moves to its dock when the view moves (the strip pans, the
  // desk changes, focus mode, the overview opens).
  const viewKey = `${deskId}|${deskId ? camX[deskId] ?? 0 : 0}|${focusMode}|${overview}|${zooming}`;
  const lastViewKey = useRef(viewKey);
  useEffect(() => {
    if (lastViewKey.current === viewKey) return;
    lastViewKey.current = viewKey;
    if (companionStateRef.current.mode === "anchored") stepCompanion({ kind: "hand-off" });
  }, [viewKey, stepCompanion]);
  // …and when the text it is anchored at scrolls away, after its first 250 ms (the companion's own scrolling
  // and the search panel's are not the text's).
  useEffect(() => {
    const stageNode = stageRef.current;
    if (!stageNode) return;
    const onScroll = (event: Event) => {
      if (companionStateRef.current.mode !== "anchored") return;
      if (timers.now() - anchoredAt.current <= COMPANION_SIZES_HANDOFF_MS) return;
      const target = event.target instanceof Element ? event.target : null;
      if (target?.closest(".desk-companion, .desk-search-backdrop")) return;
      stepCompanion({ kind: "hand-off" });
    };
    stageNode.addEventListener("scroll", onScroll, { capture: true, passive: true });
    return () => stageNode.removeEventListener("scroll", onScroll, { capture: true });
  }, [ws === null, timers, stepCompanion]);

  // Avoid (spec §8.2): when the selection lies under a docked companion, it slides sideways once.
  useEffect(() => {
    const onSelection = () => {
      const id = focusIdRef.current;
      const panel = companionRef.current?.rect() ?? null;
      if (!id || !panel || companionStateRef.current.mode !== "docked") {
        setAvoid(0);
        return;
      }
      const selected = readWindowSelection(id, stageRef.current);
      setAvoid((now) => (selected ? (now !== 0 ? now : avoidOffset(panel, selected.rects, stageNow.current)) : 0));
    };
    document.addEventListener("selectionchange", onSelection);
    return () => document.removeEventListener("selectionchange", onSelection);
  }, []);

  // The tutor that looks things up (RW1c), as the Reader's contract offers it: its personalized chip is sent with
  // every ask while it is on (at the vault's default until the learner switches it), and an answer that looked
  // things up can be asked again "another way" or as "that didn't help".
  const promptContract = useCachedQuery(["reader_prompt_contract"], () => Promise.resolve().then(() => api.readerPromptContract()), {
    tags: [TAG.reader, TAG.settings],
    staleAfterMs: Infinity,
  });
  const readerTutor = promptContract.data?.readerTutor ?? null;
  const [personalizedChoice, setPersonalizedChoice] = useState<boolean | null>(null);
  const personalizedOn = personalizedChoice ?? readerTutor?.personalizedDefault ?? true;
  const personalizedRef = useRef<boolean | null>(null);
  personalizedRef.current = readerTutor?.retrieval ? personalizedOn : null;
  const personalizedInput = () => (personalizedRef.current !== null ? { personalized: personalizedRef.current } : {});

  const askCompanion = useCallback((question: string) => {
    const grounding = groundingRef.current;
    if (grounding.reason !== null || !grounding.extractionId) return;
    const spanId = grounding.spanId ?? firstVisibleSpan(grounding.spanWindowId ?? grounding.windowId ?? null);
    if (!spanId) {
      toastNow("select a passage to ask about it");
      return;
    }
    // A preview or a paused window asks nothing (the overview shows only the pill).
    const lifecycle = lifecyclesRef.current[grounding.windowId ?? ""];
    if (overviewRef.current || (lifecycle && isPaused(lifecycle.state))) return;
    const selected = chipRef.current;
    // A pad line is the learner's own text, which the tutor may read (§14): it goes with the question, never as
    // the passage's words; the block is recorded with the exchange.
    const padLine = selected?.pad ? selected.quote : null;
    asks.ask({
      deskId: deskIdRef.current,
      windowId: grounding.windowId ?? null,
      surface: "desk",
      question: padLine ? `${question}\n\n(about this line of my pad: “${padLine}”)` : question,
      extractionId: grounding.extractionId,
      spanId,
      selectionSpanIds: padLine ? undefined : selected?.spanIds,
      quote: padLine ? null : selected?.quote ?? null,
      ...(grounding.padBlockId ? { padBlockIds: selected?.pad?.blockIds ?? [grounding.padBlockId] } : {}),
      ...personalizedInput(),
      // The goal in view (the lens's), so the tutor's answer can aim at it.
      ...(goalIdRef.current ? { goalId: goalIdRef.current } : {}),
    // The sidecar records the desk's focus and windows with the question: the writes queued so far land first.
    }, store.settled());
    setChip(null);
  }, [asks, store, toastNow]);

  /** "another way" or "that didn't help…" under an answer: a branch of it, on the same reading and passage. */
  const askAgain = (exchange: CompanionExchange, question: string, retrievalIntent: "alternative" | "remediate") => {
    const parent = exchange.answer ? exchange.answer.readerAnswerEventId || exchange.answer.eventId : null;
    if (!parent) return;
    asks.ask({
      deskId: deskIdRef.current, windowId: exchange.windowId, surface: exchange.request.surface, question,
      extractionId: exchange.extractionId, spanId: exchange.spanId,
      ...(exchange.request.selectionSpanIds?.length ? { selectionSpanIds: exchange.request.selectionSpanIds } : {}),
      quote: exchange.request.selectionQuote ?? null, parentExchangeId: parent, retrievalIntent, ...personalizedInput(),
    }, store.settled());
  };

  const loadHistory = useCallback((query: string, cursor?: string) => companionTransport.companionHistory({ ...(query ? { query } : {}), ...(cursor ? { cursor } : {}) }), [companionTransport]);

  const deskTitle = useCallback((id: string | null) => (id ? deskById(wsRef.current, id)?.title ?? "an archived desk" : "no desk"), []);

  /** A claim (or a history anchor) opens its passage beside the focus, or scrolls to it where it is open. */
  /** A passage named by its reading (a claim, a history anchor, a pad's back-link) opens beside the focus, or is
   * scrolled to where it is open; with no window of its source open, the source is read from the reading (or
   * the stored source id) and opened, a video at the stored time. */
  const openClaim = useCallback((citation: Pick<TutorCitationDto, "extractionId" | "spanId"> & { sourceId?: string | null; t?: number }) => {
    let sourceId = citation.sourceId ?? null;
    let kind: "source" | "video" = "source";
    for (const window of Object.values(wsRef.current.windows)) {
      const content = window.content;
      if (content && (content.kind === "source" || content.kind === "video") && content.extractionId === citation.extractionId) {
        sourceId = content.sourceId;
        kind = content.kind;
        break;
      }
    }
    const open = (found: string, known: "source" | "video") => {
      const card = library?.find((entry) => entry.sourceId === found);
      const shown = card && isVideoCard(card) ? "video" : known;
      const ref = { kind: shown, sourceId: found, extractionId: citation.extractionId, ...(shown === "video" && citation.t !== undefined ? { t: citation.t } : {}) } as ContentRefDto;
      openContent(ref, { spanId: citation.spanId, peek: true });
    };
    if (sourceId) {
      open(sourceId, kind);
      return;
    }
    // Its book is on no desk: the reading names its source (a backend read), and it opens beside.
    if (!transport.sourceOfExtraction) {
      toastNow("that passage's source isn't on a desk · find it with /");
      return;
    }
    void transport.sourceOfExtraction(citation.extractionId).then(
      (found) => open(found, "source"),
      () => toastNow("couldn't find that passage's source · find it with /"),
    );
  }, [library, openContent, toastNow, transport]);

  const openThread = useCallback((exchange: CompanionExchange) => {
    const root = exchange.answer?.readerAnswerEventId || exchange.answer?.eventId;
    if (!root) return;
    openContent({ kind: "thread", rootExchangeId: root }, { view: { extractionId: exchange.extractionId } });
  }, [openContent]);

  /** A search result opens beside the focus (a source at its passage, a video at its moment, a thread, a pad),
   * or, already open, is scrolled to; a window on this desk takes the focus. */
  const openSearchRow = useCallback((row: SearchRow) => {
    const id = deskIdRef.current;
    if (row.kind === "open") {
      if (id) commit(setFocus(wsRef.current, id, row.windowId));
      return;
    }
    const ref = row.ref;
    if (!ref) {
      toastNow("Can’t open this result here. Search for its source by title.");
      return;
    }
    // A note opens by its identity: a Reader note or highlight in its book at its passage (the window's view
    // names the note); an inbox note has no desk window yet, so it is said where it lives, not opened as an
    // unbound Notes panel.
    const note = row.raw as { noteKind?: string; noteRefKind?: string | null; snippet?: string; title?: string };
    if (note.noteKind === "note") {
      const target = row.target ?? {};
      if (note.noteRefKind === "capture" || ref.kind === "panel") {
        toastNow(`“${(note.title || note.snippet || "this note").slice(0, 60)}” is an inbox note. Open Today, then Inbox.`);
        return;
      }
      openContent(ref, { spanId: target.spanId ?? null, view: { ...(target.noteKey ? { noteKey: target.noteKey } : {}), ...(target.annotationId ? { annotationId: target.annotationId } : {}) } });
      return;
    }
    if (ref.kind === "thread") {
      const passage = (row.raw as { passage?: ContentRefDto | null }).passage;
      const extractionId = passage && (passage.kind === "source" || passage.kind === "video") ? passage.extractionId : null;
      openContent(ref, { view: extractionId ? { extractionId } : {} });
      return;
    }
    openContent(ref, { spanId: row.target?.spanId ?? null });
  }, [commit, openContent, toastNow]);

  // -- pads (spec §10): the host the pad windows use, the carried questions, the drain ----------------------

  // Every desk has its running pad in a stack (spec §10.5): ensured, idempotently, the first time the desks show
  // a desk with windows whose stacks hold none (a new desk, or one from before running pads); never during a zoom,
  // so no layout changes under a transition. An empty desk keeps saying how to open a book.
  const ensuredDesks = useRef(new Set<string>());
  useEffect(() => {
    const desk = ws && deskId ? deskById(ws, deskId) : undefined;
    if (!ws || !deskId || !desk || overview || zooming || desk.slots.length === 0 || ensuredDesks.current.has(deskId)) return;
    ensuredDesks.current.add(deskId);
    if (hasRunningPad(ws, deskId)) return;
    const before = new Set(ws.runningPadIds ?? []);
    const step = ensureRunningPad(ws, deskId, () => mintId("pad"), () => mintId("win"));
    commit(step);
    for (const padId of step.ws.runningPadIds ?? []) if (!before.has(padId)) store.noteCreatedPad(padId, "running", "running", deskId);
  }, [ws, deskId, overview, zooming, commit, mintId, store]);

  // Every stack's pads are read once when the desks open (one pad.get each, never polled), so a desk visited for
  // the first time shows its pads as it arrives instead of "reading the pad…" after the zoom.
  const prefetched = useRef(new Set<string>());
  useEffect(() => {
    if (!ws) return;
    for (const window of Object.values(ws.windows)) {
      for (const entry of window.stack ?? []) {
        if (entry.kind !== "pad" || prefetched.current.has(entry.padId)) continue;
        prefetched.current.add(entry.padId);
        void store.loadPad(entry.padId);
      }
    }
  }, [ws, store]);

  // Pads an earlier build kept in a stack window's view join its stack by their own op, once.
  const migratedStacks = useRef(new Set<string>());
  useEffect(() => {
    if (!ws) return;
    let next = ws;
    const ops: Step["ops"] = [];
    for (const window of Object.values(ws.windows)) {
      if (window.kind !== "pad_stack" || migratedStacks.current.has(window.windowId)) continue;
      migratedStacks.current.add(window.windowId);
      const legacy = Array.isArray(window.view?.addedPads) ? (window.view.addedPads as unknown[]).filter((id): id is string => typeof id === "string") : [];
      for (const padId of legacy) {
        const step = addToStack(next, window.deskId, window.windowId, padId);
        next = step.ws;
        ops.push(...step.ops);
      }
    }
    if (ops.length) commit({ ws: next, ops });
  }, [ws, commit]);

  // The questions a successful mark closed this session (fruitful, let it go): taken out of both lists at once, and
  // never restored by a refresh read before the mark or one that failed part-way.
  const closedCarried = useRef(new Set<string>());
  const openOnly = useCallback((list: CarriedQuestionDto[]) => list.filter((question) => !closedCarried.current.has(question.carriedId)), []);
  const refreshCarried = useCallback(() => {
    // Through a promise, so a call that throws (a sidecar without carried questions) is a quiet failure too.
    void Promise.resolve().then(() => padsTransport.carriedList({ which: "open" })).then((out) => setCarried({ list: openOnly(out.carried), limit: out.shelfLimit, more: Boolean(out.cursor) }), () => undefined);
  }, [padsTransport, openOnly]);
  useEffect(() => {
    if (ws) refreshCarried();
    // Read once when the desks open; carrying refreshes it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ws === null]);
  // Every still-carried question, through the list's pages, read again whenever the shelf's list is (RD10): a
  // question past the first page comes back beside its passages too.
  const [carriedAll, setCarriedAll] = useState<CarriedQuestionDto[] | null>(null);
  useEffect(() => {
    let live = true;
    void allCarried((cursor) => Promise.resolve().then(() => padsTransport.carriedList({ which: "open", ...(cursor ? { cursor } : {}) })))
      .then((all) => { if (live) setCarriedAll(openOnly(all)); }, () => undefined);
    return () => { live = false; };
  }, [carried, padsTransport, openOnly]);
  const markedCarried = useCallback((carriedId: string, event: string) => {
    if (event === "fruitful" || event === "let_go") {
      closedCarried.current.add(carriedId);
      setCarried((now) => ({ ...now, list: openOnly(now.list) }));
      setCarriedAll((now) => (now ? openOnly(now) : now));
    }
    refreshCarried();
  }, [openOnly, refreshCarried]);
  // And beside the related passages of the other open readings (spec §10.12).
  const carriedRelated = useMemo(() => new CarriedRelated({
    passageUnionRange: (input) => padsTransport.passageUnionRange(input),
    correspondents: (input) => videoTransport.correspondents(input),
  }), [padsTransport, videoTransport]);
  useSyncExternalStore(carriedRelated.subscribe, carriedRelated.getVersion);
  // The carried questions the margin marks place: beside their own passages, and beside related ones in the other
  // open readings (one list, kept while nothing it reads changes, so the marks are not placed again every render).
  const relatedVersion = carriedRelated.getVersion();
  const openReadings = (desk?.slots.flat() ?? []).flatMap((id) => {
    const content = ws?.windows[id]?.content;
    return content && (content.kind === "source" || content.kind === "video") ? [content.extractionId] : [];
  }).join("\u0000");
  const marksCarried = useMemo(() => {
    const all = carriedAll ?? carried.list;
    return [...all, ...carriedRelated.beside(all, openReadings ? openReadings.split("\u0000") : [])];
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [carriedAll, carried.list, openReadings, relatedVersion, carriedRelated]);


  /** Carry a question; settles when the sidecar has it (rejecting, with its reason, when it does not). */
  const carryQuestion = useCallback((text: string, origin: { blockIds?: string[]; kind: CarriedQuestionDto["originKind"]; ref?: string | null; anchor?: { extractionId: string; spanId: string } | null }): Promise<void> => {
    const carried = Promise.resolve().then(() => padsTransport.carriedCarry({ carriedId: mintId("carried"), text, originKind: origin.kind, ...(origin.blockIds ? { blockIds: origin.blockIds } : {}), originRef: origin.ref ?? null, anchor: origin.anchor ?? null, deskId: deskIdRef.current }));
    void carried.then(() => {
      toastNow("Question saved for later. It may appear beside a related passage.");
      refreshCarried();
    }, (error: unknown) => toastNow(`couldn't save it for later · ${errorText(error)}`));
    return carried.then(() => undefined);
  }, [padsTransport, mintId, toastNow, refreshCarried]);

  /** A passage beside the focus (a quote's back-link, a hover card's "open it beside"), at its time for a video. */
  const openPassage = useCallback((extractionId: string, spanId: string | null, t?: number, sourceId?: string | null) => {
    // Through the claims' path: a source on no desk is reopened at the stored passage, a video at its time.
    openClaim({ extractionId, spanId: spanId ?? "", sourceId: sourceId ?? null, ...(t !== undefined ? { t } : {}) });
  }, [openClaim]);

  /** The passage at the top of each open source window, and the cue at the top of each video (the pad menu's
   * source pieces). */
  const sourcePieces = useCallback((): SourcePiece[] => {
    const current = wsRef.current;
    const id = deskIdRef.current;
    const each = id ? deskById(current, id) : null;
    if (!each) return [];
    const out: SourcePiece[] = [];
    for (const windowId of each.slots.flat()) {
      const window = current.windows[windowId];
      const content = window?.content;
      if (!window || !content || (content.kind !== "source" && content.kind !== "video")) continue;
      const spanId = statusRef.current[windowId]?.readingSpan ?? firstVisibleSpan(windowId);
      if (!spanId) continue;
      const element = document.querySelector(`[${WINDOW_ATTRIBUTE}="${windowId}"] [data-span-id="${spanId}"], [${WINDOW_ATTRIBUTE}="${windowId}"] [data-transcript-span="${spanId}"]`);
      const text = (element?.textContent ?? "").replace(/\s+/g, " ").trim().slice(0, 600);
      if (!text) continue;
      const title = titleOf(window);
      out.push({ label: `${content.kind === "video" ? "the current caption" : "the passage in view"} · ${shortName(title)}`, extractionId: content.extractionId, spanId, text, sourceTitle: title });
    }
    return out;
  }, [titleOf]);

  // The vault's finished figures waiting for their pad windows (kept across the shell's mounts with the store).
  const pendingFigures = useMemo(() => pendingFiguresFor(store), [store]);
  // The promoted rows' calls, shared by the source menu and the pad menu; labels are kept per row (option C's data).
  const menuPromoted = useMemo<PromotedApi>(() => ({
    passagePromoted: (input) => menuTransport.passagePromoted(input),
    passagePromotedJob: (input) => menuTransport.passagePromotedJob(input),
    passagePromotedCancel: (input) => menuTransport.passagePromotedCancel(input),
    label: (rowId, label) => {
      // A label keeps its id until it is stored (labels are idempotent by id): a failed send is retried on the one
      // poller with its backoff; one the sidecar refuses outright says so (the row may come back next time).
      const input = { labelId: mintId("lbl"), proposalKind: "promoted_row" as const, proposalId: rowId, label };
      const refused = (error: unknown) => Boolean(error && typeof error === "object" && (error as { retryable?: unknown }).retryable === false);
      const giveUp = () => toastNow(label === "opened" ? "couldn't note that you opened it" : "couldn't keep that you set it aside · it may come back");
      void menuTransport.proposalLabel(input).catch((error: unknown) => {
        if (refused(error)) {
          giveUp();
          return;
        }
        const stop = poller.register<unknown>({
          key: `promoted-label:${input.labelId}`,
          owner: null,
          request: () => menuTransport.proposalLabel(input),
          onResult: () => ({ done: true }),
          onError: (again) => {
            if (!refused(again)) return;
            stop();
            giveUp();
          },
        });
      });
    },
  }), [menuTransport, mintId, poller, toastNow]);
  const onPromotedRef = useRef<(row: import("../../api/dto").PromotedRowDto, origin: import("../../api/dto").MenuObjectInput | null) => boolean>(() => false);
  const openMenuByKeyRef = useRef<() => boolean>(() => false);
  const hoveredKeyRef = useRef<(what: "note" | "promoted") => boolean>(() => false);
  /** A figure as a `figure` block in the running pad of the desk Show me was asked on (captured when asked), not the
   * desk shown when it is ready: Show me's interim landing, and the companion figure's "move to scratchpad". */
  const landFigureBlock = useCallback(async (anchor: { extractionId: string | null; spanId: string | null; spanIds?: string[] }, figure: { figureId: string; line: string }, padId: string | null) => {
    if (padId) await store.loadPad(padId);
    const pad = padId ? store.pads[padId] : null;
    if (!padId || !pad) {
      toastNow("the figure is ready, but that desk has no running pad to put it in");
      throw new Error("no running pad");
    }
    store.commitPad(padId, [{ op: "insert_block", blockId: mintId("blk"), versionId: mintId("ver"), kind: "figure", provenance: "learnloop", positionKey: keyAfterLast(pad.blocks), day: localDay(),
      bodyMd: figure.line, payload: { figure_id: figure.figureId, extraction_id: anchor.extractionId, span_id: anchor.spanId, ...(anchor.spanIds ? { span_ids: anchor.spanIds } : {}) } }]);
    toastNow("◇ the figure was added to your running pad");
  }, [store, toastNow, mintId]);
  const companionFigureHost = useMemo<CompanionFigureHost>(() => ({
    moveToPad: (entry) => landFigureBlock(entry.anchor, { figureId: entry.figure.figureId, line: entry.figure.demonstrates || entry.figure.goalText || "a figure" }, entry.destination),
    openSource: (extractionId, spanId) => openClaim({ extractionId, spanId }),
  }), [landFigureBlock, openClaim]);
  const shownFigures = useCompanionFigures(vaultKey);

  // RW2 on a desk (spec §15.2): a problem a source window opens is worked on a problem pad in the desk's stack (the
  // pad of its workbench session when one is loaded, else a new one), brought into view; the window keeps reading.
  const workOnPad = useCallback(async (handoff: ProblemHandoff) => {
    handOver(handoff);
    const id = deskIdRef.current;
    if (!id) return;
    const sessionId = handoff.session.sessionId;
    // One pad per problem: its id is the session's, so the pad of a session made earlier (in another view of the
    // desks, not loaded now) is read from the server before any is made. The pads store has no read by session
    // (pad.list neither filters nor indexes by it), so the id carries the binding.
    const padId = problemPadId(sessionId);
    if (!store.pads[padId]) await store.loadPad(padId);
    if (!store.pads[padId]) {
      const title = problemTitle(handoff.session.stemMd);
      const refused = store.commitPad(padId, [{ op: "create_pad", kind: "problem", title: title === "this problem" ? "a problem" : title, homeDeskId: id, workbenchSessionId: sessionId }]);
      if (refused) {
        toastNow(`couldn't make the problem's pad · ${refused.message}`);
        return;
      }
    }
    // The pad lives where it is: a stack already holding it (on this desk or another) is where it is shown, that
    // desk becoming the current one; else it joins this desk's stack.
    const holding = Object.values(wsRef.current.windows).find((window) => window.kind === "pad_stack" && (window.stack ?? []).some((entry) => entry.kind === "pad" && entry.padId === padId));
    if (holding && holding.deskId !== id) {
      setCurrentDeskId(holding.deskId);
      const desk = wsRef.current.desks.find((each) => each.deskId === holding.deskId);
      toastNow(`✎ this problem is on the desk “${desk?.title ?? "another desk"}” · shown there`);
    }
    const deskOf = holding?.deskId ?? id;
    const stackWindow = holding ?? Object.values(wsRef.current.windows).find((window) => window.deskId === id && window.kind === "pad_stack");
    if (!stackWindow) {
      commit(openStackBeside(wsRef.current, id, [padId], () => mintId("win")));
      return;
    }
    if (!holding) commit(addToStack(wsRef.current, deskOf, stackWindow.windowId, padId));
    commit(setFocus(wsRef.current, deskOf, stackWindow.windowId));
    requestAnimationFrame(() => padHandles.current.get(stackWindow.windowId)?.showPad(padId));
  }, [store, mintId, toastNow, commit, setCurrentDeskId]);
  const problemHost = useMemo<ProblemHost>(() => ({
    practiceSessionId: reader?.workbench?.practiceSessionId ?? null,
    ...(reader?.workbench?.onSubmitted ? { onSubmitted: reader.workbench.onSubmitted } : {}),
    showInBook: (session) => {
      if (session.extractionId) openPassage(session.extractionId, session.spanIds[0] ?? null, undefined, session.sourceId ?? null);
    },
    cardFor: (sourceId) => (sourceId ? library?.find((card) => card.sourceId === sourceId) ?? null : null),
    onError,
  }), [reader, openPassage, library, onError]);

  const padsHost = useMemo<PadsHost>(() => ({
    store,
    deskId,
    mintId,
    today: () => localDay(),
    api: padsTransport,
    practiceSessionId: reader?.workbench?.practiceSessionId ?? null,
    openPassage,
    openSearch: (query, insert, blockIds) => setSearch({ query, insert: insert ?? null, blockIds }),
    askAbout: (quote, context) => {
      setChip({ quote: clipQuote(quote, 400), spanIds: [], windowId: focusIdRef.current ?? "", ...(context ? { pad: context } : {}) });
      stepCompanion({ kind: "dock" });
    },
    showMe: async (text: string, anchor: { extractionId: string; spanId: string; spanIds?: string[] } | null, ownerWindowId?: string, blockIds?: string[]) => {
      // While an inline check is open, Show me waits: a figure would explain what the veils hold (spec §12.6.4).
      const held = checkDesk.heldReason();
      if (held) {
        toastNow(`Show me waits · ${held}`);
        return null;
      }
      // The Reader's figure build (RW5d), read through the one poller under the pad window that asked: a paused
      // window's poll waits with it. A figure that is not shown lands nowhere.
      const first = await padsTransport.figureRequest({ goalText: text, origin: "show_me", ...(blockIds ? { blockIds } : {}), anchor: anchor ? { extractionId: anchor.extractionId, spanIds: anchor.spanIds ?? [anchor.spanId] } : null });
      const job = first.state !== "pending" ? first : await new Promise<typeof first>((resolve, reject) => {
        // The poll ends on every terminal path: a result, a job the sidecar no longer knows, or the window that asked
        // being closed (its paused polls would otherwise wait for ever).
        let stop: () => void = () => undefined;
        const gone = { code: "owner_gone", message: "the window that asked is closed" };
        stop = poller.register<typeof first>({
          key: `figure-job:${first.jobId}`,
          owner: ownerWindowId ?? null,
          request: () => (ownerWindowId && !wsRef.current.windows[ownerWindowId] ? Promise.reject(gone) : padsTransport.readerFigureJob({ jobId: first.jobId })),
          onResult: (read) => {
            if (read.state === "pending") return { done: false };
            resolve(read);
            return { done: true };
          },
          onError: (error) => {
            const code = error && typeof error === "object" ? (error as { code?: unknown }).code : null;
            if (code === "job_not_found" || code === "owner_gone") {
              stop();
              reject(error);
            }
          },
        });
      });
      const figure = job.result?.figure;
      if (!figure || !figure.shown) return null;
      return { figureId: figure.figureId, line: figure.demonstrates || figure.goalText || text, figure };
    },
    figures: pendingFigures,
    menu: {
      promoted: menuPromoted,
      poller,
      onPromoted: (row, origin) => onPromotedRef.current(row, origin),
      knows: (object) => setKnows(object),
    },
    // A pad line's Teach me opens a lesson tab in the desk's stack, as the source menu's does (one path).
    teachMe: (extractionId: string, spanIds: string[], blockIds?: string[]) => openLesson({ kind: "open", entry: "reader_selection", selection: { extractionId, spanIds, ...(blockIds ? { blockIds } : {}) } }),
    toast: toastNow,
    setView: (windowId, view) => {
      const window = wsRef.current.windows[windowId];
      if (window) commit(setView(wsRef.current, window.deskId, windowId, view));
    },
    sourcePieces,
    addToStack: (windowId, padId) => {
      const window = wsRef.current.windows[windowId];
      if (window) commit(addToStack(wsRef.current, window.deskId, windowId, padId));
    },
    register: (windowId, handle) => {
      if (handle) padHandles.current.set(windowId, handle);
      else padHandles.current.delete(windowId);
    },
    carry: carryQuestion,
    lessons: lessonsHost,
    problems: problemHost,
  }), [store, deskId, mintId, padsTransport, reader, openPassage, toastNow, commit, sourcePieces, carryQuestion, stepCompanion, poller, pendingFigures, menuPromoted, lessonsHost, openLesson, problemHost]);
  // Pen and ink (RD8a): what a source window's pen layer and a pad's ink lines reach through.
  const inkCache = useMemo(() => new InkCache({ api: penApi, poller, settled: () => store.settled(), refreshPad: (padId) => store.refreshPad(padId),
    held: () => checkDesk.heldReason() }), [penApi, poller, store, checkDesk]);
  const penHost = useMemo<PenHost>(() => ({
    on: penOn,
    simulate: simulatePen,
    setOn: setPenOn,
    saveInk: (ink) => store.commitInk(ink),
    eraseInk: (erase) => store.commitInkErase(erase),
    settled: () => store.settled(),
    mintId,
    api: penApi,
    poller,
    askCompanion: () => companionKeyRef.current(false),
    ink: inkCache,
  }), [penOn, simulatePen, store, mintId, penApi, poller, inkCache]);

  /** The pad stack the keys act on: the focused window when it is one. */
  const focusedStack = (): PadStackHandle | null => (focusIdRef.current ? padHandles.current.get(focusIdRef.current) ?? null : null);
  const focusedStackRef = useRef(focusedStack);
  focusedStackRef.current = focusedStack;

  /** alt+n away from a stack: a new pad in a new stack window beside, titled from the selection. */
  const newPadBeside = useCallback(() => {
    const id = deskIdRef.current;
    if (!id) return;
    const padId = mintId("pad");
    const title = "Pad · new notes";
    const refused = store.commitPad(padId, [{ op: "create_pad", kind: "named", title, homeDeskId: id }]);
    if (refused) {
      toastNow("Couldn’t make a pad. Reopen this desk and try again.");
      return;
    }
    commit(openStackBeside(wsRef.current, id, [padId], () => mintId("win")));
  }, [commit, mintId, store, toastNow]);
  const newPadBesideRef = useRef(newPadBeside);
  newPadBesideRef.current = newPadBeside;

  /** The pads in a desk's stack windows (a desk's running pad is among them). */
  const deskPadIds = useCallback((id: string | null): string[] => {
    if (!id) return [];
    return Object.values(wsRef.current.windows).filter((window) => window.deskId === id).flatMap((window) => (window.stack ?? []).flatMap((entry) => (entry.kind === "pad" ? [entry.padId] : [])));
  }, []);

  /** The desk's running pad among the pads read, if one is. */
  const runningPadOf = useCallback((id: string | null): string | null => {
    if (!id) return null;
    return Object.values(store.pads).find((pad) => pad.pad.kind === "running" && pad.pad.homeDeskId === id)?.pad.padId ?? null;
  }, [store]);

  /** The companion's answers propose a previewed diff into the desk's running pad (spec §8.4). A desk whose
   * stacks are not read yet (its pad window paused) reads them when the learner accepts. */
  const answerProposals = useCallback((exchange: CompanionExchange): ProposedDiff[] => {
    const answer = exchange.answer;
    const known = runningPadOf(exchange.deskId);
    if (!answer || (!known && deskPadIds(exchange.deskId).length === 0)) return [];
    const lines = answer.answerMd.split("\n").map((line) => line.trim()).filter(Boolean).slice(0, 6);
    return [{
      id: `${exchange.requestId}:running`,
      target: known ? padName(store.pads[known]?.pad) : "running pad",
      // "the reply": the preview line says it shows only the first lines, and the header holds two lines at the
      // companion's laptop width with the pad's whole name ("running pad").
      label: "Copy the reply",
      lines,
      onAccept: async () => {
        if (!runningPadOf(exchange.deskId)) await Promise.all(deskPadIds(exchange.deskId).map((padId) => store.loadPad(padId)));
        const padId = runningPadOf(exchange.deskId);
        const now = padId ? store.pads[padId] : null;
        if (!padId || !now) throw new Error("this desk has no running pad");
        const refused = store.commitPad(padId, [{
          op: "insert_block", blockId: mintId("blk"), versionId: mintId("ver"), kind: "tutor_quote", provenance: "tutor",
          positionKey: keyAfterLast(now.blocks), day: localDay(), bodyMd: answer.answerMd, payload: { asked_on: localDay(), question_md: exchange.question },
        }]);
        if (refused) throw refused;
      },
    }];
  }, [deskPadIds, mintId, runningPadOf, store]);

  /** Keep or leave a pad from the drain: the pad is read first when no window has (its stack paused). */
  /** Keep or leave a pad from the drain; settles once the server has it (rejecting with why when it does not). */
  const drainWrite = useCallback(async (padId: string, op: "keep" | "unkeep", version: number): Promise<void> => {
    await store.loadPad(padId);
    if (!store.pads[padId]) throw new Error(store.padFailure(padId) ?? "the pad could not be read");
    const refused = store.commitPad(padId, [{ op, expectedVersion: store.pads[padId]?.pad.version ?? version }]);
    if (refused) throw refused;
    if ((await store.settled()) !== "saved") throw new Error("it could not be saved just now");
  }, [store]);

  // The passages' ✎ links come from the passage union of what each source window shows (links on another reading
  // resolved through aliases, whether or not any pad is loaded), read again when the view moves or a pad changes.
  // A paused window reads nothing.
  const [unionLinks, setUnionLinks] = useState<Record<string, PadLink[]>>({});
  const unionKey = useRef<Record<string, string>>({});
  const padVersionNow = store.getPadVersion();
  useEffect(() => {
    const stage = stageRef.current;
    if (!stage || !ws || !deskId || overview) return;
    let live = true;
    const read = () => {
      const desk = deskById(wsRef.current, deskId);
      for (const id of desk?.slots.flat() ?? []) {
        const content = wsRef.current.windows[id]?.content;
        const lifecycle = lifecyclesRef.current[id];
        if (!content || (content.kind !== "source" && content.kind !== "video") || (lifecycle && isPaused(lifecycle.state))) continue;
        const range = visibleSpanRange(stage, id);
        if (!range) continue;
        const key = `${content.extractionId}|${range.from}|${range.to}|${store.getPadVersion()}`;
        if (unionKey.current[id] === key) continue;
        unionKey.current[id] = key;
        const extractionId = content.extractionId;
        void Promise.resolve().then(() => padsTransport.passageUnionRange({ extractionId, fromSpanId: range.from, toSpanId: range.to })).then((union) => {
          if (!live) return;
          const links = union.spans.flatMap((span) => span.padBlocks.map((block) => ({ padId: block.padId, blockId: block.blockId, extractionId, spanId: span.spanId, alias: block.alias })));
          setUnionLinks((now) => ({ ...now, [id]: links }));
        }, () => undefined);
      }
    };
    read();
    let frame: ReturnType<typeof setTimeout> | null = null;
    const onScroll = () => {
      if (frame) clearTimeout(frame);
      frame = setTimeout(read, 400);
    };
    stage.addEventListener("scroll", onScroll, { capture: true, passive: true });
    // The Reader renders its passages after this does: look again shortly.
    const settle = setTimeout(read, 800);
    return () => {
      live = false;
      stage.removeEventListener("scroll", onScroll, { capture: true });
      if (frame) clearTimeout(frame);
      clearTimeout(settle);
    };
    // The windows' identity is in ws; a pad change is padVersionNow.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ws, deskId, overview, padVersionNow, padsTransport, lifecycles]);
  const padLinks = useMemo<PadLink[]>(() => {
    const seen = new Set<string>();
    const out: PadLink[] = [];
    for (const links of Object.values(unionLinks)) {
      for (const link of links) {
        const key = `${link.extractionId}|${link.spanId}|${link.blockId}`;
        if (seen.has(key)) continue;
        seen.add(key);
        out.push(link);
      }
    }
    return out;
  }, [unionLinks]);
  // -- the goal lens (spec §12): the band, each reading's marks, the path view ----------------------------
  // A pad stack's goal line reads its own pads' anchors (loaded pads), whatever is on screen; a pad no unpaused
  // window shows asks the lens for nothing (paused, as a paused reading).
  const goalPadAnchors = useMemo(() => {
    const live = new Set<string>();
    for (const window of Object.values(ws?.windows ?? {})) {
      if (isPaused(lifecycles[window.windowId]?.state ?? "hidden")) continue;
      if (window.content?.kind === "pad") live.add(window.content.padId);
      for (const entry of window.stack ?? []) if (entry.kind === "pad") live.add(entry.padId);
    }
    return Object.values(store.pads).flatMap((pad) => pad.anchors.map((anchor) => ({ padId: pad.pad.padId, extractionId: anchor.extractionId,
      spanId: anchor.spanId, paused: !live.has(pad.pad.padId) })));
  },
    // store.pads changes identity on every pad change (padVersionNow re-renders this shell).
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [store.pads, padVersionNow, ws, lifecycles]);
  const goalReadings = useMemo<GoalReading[]>(() => {
    if (!ws) return [];
    const out: GoalReading[] = [];
    for (const window of Object.values(ws.windows)) {
      const content = window.content;
      if (!content || (content.kind !== "source" && content.kind !== "video")) continue;
      const card = library?.find((each) => each.sourceId === content.sourceId);
      out.push({ windowId: window.windowId, extractionId: content.extractionId, book: titleOf(window),
        paused: isPaused(lifecycles[window.windowId]?.state ?? "hidden"), paper: card?.kindNoun === "paper" });
    }
    return out;
  }, [ws, lifecycles, titleOf, library]);
  const goalFocused = useMemo(() => {
    const window = focusId && ws ? ws.windows[focusId] : null;
    if (!window) return null;
    const content = window.content;
    const extractionId = content && (content.kind === "source" || content.kind === "video") ? content.extractionId : null;
    return { windowId: window.windowId, extractionId, readingSpan: status[window.windowId]?.readingSpan ?? null,
      where: status[window.windowId]?.where ?? (extractionId ? titleOf(window) : null) };
  }, [focusId, ws, status, titleOf]);
  const openGoalSection = useCallback((section: { extractionId: string; sourceId?: string; startSpanId: string | null }) => {
    const onDesk = Object.values(wsRef.current.windows).some((window) => window.content && (window.content.kind === "source" || window.content.kind === "video") && window.content.extractionId === section.extractionId);
    if (onDesk || !section.sourceId) openPassage(section.extractionId, section.startSpanId);
    else openContent({ kind: "source", sourceId: section.sourceId, extractionId: section.extractionId, view: "render" }, { spanId: section.startSpanId });
  }, [openPassage, openContent]);
  // -- inline cold checks (RD7, spec §12.6) -------------------------------------------------------------------------
  // After a restart the open administration comes back with its veils; the readings on this desk show their markers.
  useEffect(() => {
    if (ws) checkDesk.restart();
    // Once, when the desks open.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ws === null, checkDesk]);
  const checkReadings = (desk?.slots.flat() ?? []).flatMap((id) => {
    const content = ws?.windows[id]?.content;
    return content?.kind === "source" ? [content.extractionId] : [];
  }).join("\u0000");
  useEffect(() => {
    if (checkReadings) checkDesk.readings(checkReadings.split("\u0000"));
  }, [checkReadings, checkDesk]);
  /** What is on screen, as the server classifies it: every desk's windows, the companion, the overview's cards. */
  const visibleForCheck = useCallback(() => {
    const windows = Object.values(wsRef.current.windows).map((window) => ({ windowId: window.windowId, kind: window.kind,
      content: window.content as { kind: string; extractionId?: string } | null }));
    const exchanges = asks.thread(deskIdRef.current).flatMap((exchange) => (exchange.answer?.eventId ? [exchange.answer.eventId] : []));
    return visibleNow(typeof document === "undefined" ? null : document, windows, {
      companionOpen: companionStateRef.current.mode !== "hidden", companionExchangeIds: exchanges,
      previewWindowIds: overviewRef.current ? windows.map((window) => window.windowId) : [],
    });
  }, [asks, wsRef]);
  /** "check now" on a closed marker: the server opens the administration and names the veils before the prompt. */
  const checkNow = useCallback((commitmentId: string) => {
    // Search closes first: its rows could show what the check asks, and it stays closed until the answer.
    setSearchState(null);
    void checkDesk.begin(commitmentId, reader?.workbench?.practiceSessionId ?? null, visibleForCheck()).then((opened) => {
      if (checkDesk.notice) toastNow(checkDesk.notice);
      // The app adopts the session the answer will be recorded on, as after a workbench submit.
      const session = opened ? checkDesk.open()?.card.practiceSession : null;
      if (session) reader?.workbench?.onPracticeSession?.(session);
    });
  }, [checkDesk, reader, visibleForCheck, toastNow]);
  // New windows or passages in view while a check is open: the server veils what it must (check.protect_more; a view
  // unchanged since the last call sends nothing).
  const protectCheckView = useCallback(() => {
    if (checkDesk.holding()) void checkDesk.protectMore(visibleForCheck());
  }, [checkDesk, visibleForCheck]);
  const checkHolding = checkDesk.holding();
  useEffect(() => {
    if (!checkHolding) return;
    const handle = requestAnimationFrame(() => void checkDesk.protectMore(visibleForCheck()));
    return () => cancelAnimationFrame(handle);
  }, [checkHolding, checkDesk, visibleForCheck, ws, currentDeskId, overview, companionState.mode, status, lifecycles]);
  const openCheck = checkDesk.open();
  const checkInline = Boolean(openCheck?.host && (desk?.slots.flat() ?? []).some((id) => {
    const content = ws?.windows[id]?.content;
    return content?.kind === "source" && content.extractionId === openCheck.host?.extractionId && !isPaused(lifecycles[id]?.state ?? "hidden");
  }));

  const goalDesk = useGoalDesk({
    transport: goalTransport,
    deskGoalId: desk?.goalId,
    offKey: deskId ? `learnloop.desks.goalOff.${vaultKey}.${deskId}` : null,
    onSetGoal: (goalId) => { if (deskIdRef.current) commit(setGoal(wsRef.current, deskIdRef.current, goalId)); },
    readings: goalReadings,
    focused: goalFocused,
    padAnchors: goalPadAnchors,
    hubFor,
    timers,
    mintId,
    onError,
    onOpen: openGoalSection,
    // The path view's Teacher lesson row (spec §12.5): the newest lesson on the LO, opening its window.
    lessonRow: (learningObjectId, closePath) => (
      <PathLessonRow desk={lessonDesk} learningObjectId={learningObjectId} onOpen={(lessonId) => { closePath(); placeLesson(lessonId); }} />
    ),
  });
  goalPathRef.current = { open: goalDesk.pathOpen, toggle: goalDesk.togglePath };
  goalIdRef.current = goalDesk.goalId;

  // -- videos (RD10): follow-along, the timestamp key ----------------------------------------------------

  // A book following a new passage scrolls there through its window's jump (a programmatic move: no reading activity).
  videoFollowed.current = (bookWindowId, spanId) => jumps.current.get(bookWindowId)?.(spanId);
  videoDesk.setPrimary(goalDesk.primaryFor);
  // The current desk's videos and books, as follow-along reads them (a paused book asks nothing).
  useEffect(() => {
    const ids = desk?.slots.flat() ?? [];
    const videos: Array<{ windowId: string; extractionId: string; title: string }> = [];
    const books: Array<{ windowId: string; extractionId: string; paused: boolean }> = [];
    for (const id of ids) {
      const content = ws?.windows[id]?.content;
      if (content?.kind === "video") videos.push({ windowId: id, extractionId: content.extractionId, title: titleOf(ws?.windows[id]) });
      else if (content?.kind === "source") books.push({ windowId: id, extractionId: content.extractionId, paused: isPaused(lifecycles[id]?.state ?? "hidden") });
    }
    videoDesk.setLayout({ videos, books });
  });
  videoKeys.current = {
    // `u`: the focused book stops or starts following; with another window focused, every book on the desk does.
    follow: () => {
      const focus = focusIdRef.current;
      if (focus && videoDesk.chipFor(focus)) {
        videoDesk.toggle(focus);
        return true;
      }
      const books = (deskById(wsRef.current, deskIdRef.current)?.slots.flat() ?? []).filter((id) => videoDesk.chipFor(id));
      if (!books.length) {
        toastNow("Open a video on this desk to follow it.");
        return true;
      }
      for (const id of books) videoDesk.toggle(id);
      return true;
    },
    // `alt+;`: "▶ <video> at m:ss" into the current desk's running pad, a quote anchored to the cue span, from the
    // focused video's clock (else the video this desk played last).
    timestamp: () => {
      const id = deskIdRef.current;
      if (!id) return false;
      const focus = focusIdRef.current;
      const focused = focus ? wsRef.current.windows[focus] : null;
      const driver = videoDesk.driver();
      const windowId = focused?.content?.kind === "video" ? focused.windowId : driver?.windowId ?? null;
      const content = windowId ? wsRef.current.windows[windowId]?.content : null;
      if (!windowId || content?.kind !== "video") {
        toastNow("no video on this desk · alt+; stamps a video's time into the running pad");
        return true;
      }
      const clock = videoDesk.clockOf(windowId);
      if (!clock?.spanId) {
        toastNow("Play the video until a caption appears, then press Alt+; again.");
        return true;
      }
      const title = titleOf(wsRef.current.windows[windowId]);
      const line = timestampLine(title, clock.t);
      void (async () => {
        let padId = runningPadOf(id);
        if (!padId) {
          await Promise.all(deskPadIds(id).map((pad) => store.loadPad(pad)));
          padId = runningPadOf(id);
        }
        if (!padId) {
          const before = new Set(wsRef.current.runningPadIds ?? []);
          const step = ensureRunningPad(wsRef.current, id, () => mintId("pad"), () => mintId("win"));
          commit(step);
          for (const created of step.ws.runningPadIds ?? []) if (!before.has(created)) store.noteCreatedPad(created, "running", "running", id);
          padId = runningPadOf(id);
        }
        const pad = padId ? store.pads[padId] : null;
        if (!padId || !pad) {
          toastNow("Couldn’t find this desk’s running pad. Open it and try again.");
          return;
        }
        const blockId = mintId("blk");
        const refused = store.commitPad(padId, [
          { op: "insert_block", blockId, versionId: mintId("ver"), kind: "source_quote", provenance: "source", positionKey: keyAfterLast(pad.blocks),
            day: localDay(), bodyMd: line, payload: { source_title: title, t: Math.floor(clock.t), extraction_id: content.extractionId, span_id: clock.spanId } },
          { op: "link_anchor", blockId, extractionId: content.extractionId, spanId: clock.spanId as string, eventId: mintId("lnk"), expectedAnchorHead: null },
        ]);
        toastNow(refused ? "Couldn’t add the video time. Open the running pad and try again." : `${line} · adding to the running pad…`);
      })();
      return true;
    },
  };
  // Each path opening reads the lessons again (one may have been taught since).
  useEffect(() => {
    if (!goalDesk.pathOpen) lessonDesk.forgetAll();
  }, [goalDesk.pathOpen, lessonDesk]);

  const surfacedCarried = useRef(new Set<string>());
  const onCarriedSurfaced = useCallback((question: CarriedQuestionDto) => {
    if (surfacedCarried.current.has(question.carriedId)) return;
    surfacedCarried.current.add(question.carriedId);
    void padsTransport.carriedMark({ eventId: mintId("cev"), carriedId: question.carriedId, event: "surfaced" }).catch(() => undefined);
  }, [padsTransport, mintId]);

  // -- the context menu (spec §0 item 7, §9.1): one listener, one menu, every verb wired --------------------

  // The pad Append writes to, remembered per desk (a per-viewer convenience: the running pad when none is).
  const [appendTargets, setAppendTargets] = useState<Record<string, string>>(() => {
    try {
      return JSON.parse(localStorage.getItem("learnloop.desks.appendTargets") ?? "{}") as Record<string, string>;
    } catch {
      return {};
    }
  });
  const rememberAppendTarget = useCallback((id: string, padId: string) => {
    setAppendTargets((now) => {
      const next = { ...now, [id]: padId };
      try {
        localStorage.setItem("learnloop.desks.appendTargets", JSON.stringify(next));
      } catch {
        // A private window keeps it for the session only.
      }
      return next;
    });
  }, []);
  /** The desk's pads (its stacks' entries), with the titles the learner reads. */
  const deskPads = useCallback((id: string | null): Array<{ padId: string; title: string }> => {
    if (!id) return [];
    const desk = deskById(wsRef.current, id);
    const ids = (desk?.slots.flat() ?? []).flatMap((windowId) => (wsRef.current.windows[windowId]?.stack ?? []).flatMap((entry) => (entry.kind === "pad" ? [entry.padId] : [])));
    return [...new Set(ids)].map((padId) => {
      const state = store.pads[padId];
      return { padId, title: state?.pad.kind === "running" && (!state.pad.title || state.pad.title === "running") ? `running pad · ${localDay()}` : padName(state?.pad) };
    });
  }, [store]);
  const appendTargetOf = useCallback((id: string | null): string | null => {
    if (!id) return null;
    const pads = deskPads(id);
    const remembered = appendTargets[id];
    if (remembered && pads.some((pad) => pad.padId === remembered)) return remembered;
    return runningPadOf(id) ?? pads[0]?.padId ?? null;
  }, [appendTargets, deskPads, runningPadOf]);

  /** Append (§9.1): the passage (or the selection over it) as a source_quote block in the chosen pad, linked both
   * ways (a highlight on the passage, the block's link naming it). "+" makes a new pad in the desk's stack first. */
  const appendTo = useCallback(async (object: MenuObject, choice: string | "+" | null) => {
    const id = deskIdRef.current;
    if (!id || !object.extractionId || !object.spanId) return;
    let target = choice === null ? appendTargetOf(id) : choice;
    if (target === "+") {
      const padId = mintId("pad");
      const title = "Pad";
      const refused = store.commitPad(padId, [{ op: "create_pad", kind: "named", title, homeDeskId: id }]);
      if (refused) {
        toastNow(`couldn't make a pad · ${refused.message}`);
        return;
      }
      const stackWindow = Object.values(wsRef.current.windows).find((window) => window.deskId === id && window.kind === "pad_stack");
      commit(stackWindow ? addToStack(wsRef.current, id, stackWindow.windowId, padId) : openStackBeside(wsRef.current, id, [padId], () => mintId("win")));
      target = padId;
    }
    if (!target) {
      toastNow("this desk has no pad to append to · alt+n makes one");
      return;
    }
    rememberAppendTarget(id, target);
    await store.loadPad(target);
    const pad = store.pads[target];
    if (!pad) {
      toastNow("couldn't read that pad just now");
      return;
    }
    // The passage's highlight, so the two ends link (§10.7); a passage already highlighted keeps its own.
    let annotationId = object.annotationId ?? null;
    if (!annotationId) {
      try {
        const who = await menuTransport.readingIdentity(object.extractionId);
        const receipt = await menuTransport.readerCapture({
          sourceId: who.sourceId, revisionId: who.revisionId, extractionId: object.extractionId, renderViewId: who.renderViewId,
          action: "highlight", clientIdempotencyKey: mintId("hl"),
          rawSelection: { extractionId: object.extractionId, spanId: object.spanId, spanIds: passageIds(object), nodes: captureNodes(object) },
        });
        // A highlight that could not be placed is not linked from the block (the block still links its passages).
        if (receipt.anchorStatus === "needs_reanchor") toastNow("couldn’t place the highlight · the pad line still links to the passage");
        else annotationId = receipt.annotationId;
      } catch (error) {
        toastNow(`couldn't capture that passage · ${errorText(error)}`);
        return;
      }
    }
    const words = (object.selection || object.text).replace(/\s+/g, " ").trim();
    const body = words.length > 600 ? `${words.slice(0, 600)}…` : words;
    const window = object.windowId ? wsRef.current.windows[object.windowId] : undefined;
    const blockId = mintId("blk");
    const refused = store.commitPad(target, [
      { op: "insert_block", blockId, versionId: mintId("ver"), kind: "source_quote", provenance: "source", positionKey: keyAfterLast(pad.blocks),
        day: pad.pad.kind === "running" ? localDay() : null, bodyMd: body,
        payload: { source_id: object.sourceId ?? null, source_title: titleOf(window), extraction_id: object.extractionId, span_id: object.spanId, span_ids: passageIds(object), ...(object.t !== undefined ? { t: object.t } : {}) } },
      // Every passage the selection touches links back to the line (each with its own ✎ mark).
      ...captureNodes(object).map((node) => ({ op: "link_anchor" as const, blockId, extractionId: object.extractionId as string, spanId: node.spanId, eventId: mintId("lnk"), expectedAnchorHead: null, annotationId })),
    ]);
    if (refused) toastNow(`couldn’t add it · ${refused.message}`);
    else toastNow(`adding to “${padName(pad.pad)}”…`);
  }, [appendTargetOf, commit, menuTransport, mintId, rememberAppendTarget, store, titleOf, toastNow]);

  // The rows the open source menu shows (Open beside takes its correspondent from them): told by that menu only
  // while it is open on its object, so a closed menu's late answer never lands here.
  const menuPromotedRows = useRef<import("../../api/dto").PromotedRowDto[]>([]);
  const liveMenu = useRef<MenuObject | null>(null);
  const closeSourceMenu = () => {
    liveMenu.current = null;
    menuWithheldAnswer.current.resolve(null);
    setMenu(null);
  };
  const [menuWithheld, setMenuWithheld] = useState<boolean | null>(null);
  const menuOpening = useRef(0);
  const menuWithheldAnswer = useRef<{ promise: Promise<boolean | null>; resolve: (withheld: boolean | null) => void }>({ promise: Promise.resolve(null), resolve: () => undefined });
  const menuContext = useMemo<MenuContext>(() => ({
    deskId,
    // A capture from the menu (a margin note, an append's highlight) is read again by the windows showing its
    // reading, so its mark shows there at once.
    api: { ...menuTransport, readerCapture: async (input) => {
      const receipt = await menuTransport.readerCapture(input);
      for (const [windowId, inquiry] of inquiries.current) {
        const content = wsRef.current.windows[windowId]?.content;
        if (content && (content.kind === "source" || content.kind === "video") && content.extractionId === input.extractionId) inquiry.annotationsChanged();
      }
      return receipt;
    } },
    mintId,
    toast: toastNow,
    // While an inline check is open, the verbs that would reveal or send veiled material wait (spec §12.6.4).
    heldReason: () => checkDesk.heldReason(),
    ask: (object) => {
      const quote = clipQuote(object.selection || object.text, 400);
      if (object.windowId) setChip({ quote, extractionId: object.extractionId, spanIds: passageIds(object), windowId: object.windowId });
      const box = stageRef.current?.getBoundingClientRect();
      const anchor = box ? { x: object.at.x - box.left, y: object.at.y - box.top, w: 1, h: 1 } : null;
      if (companionStateRef.current.mode === "hidden") stepCompanion({ kind: "c", anchor, stage: stageNow.current });
    },
    openSearch: (query, selection) => setSearch({ query, selection }),
    openContent: (ref, options) => openContent(ref, options ?? {}),
    carry: (text, origin) => carryQuestion(text, origin),
    append: (object, choice) => void appendTo(object, choice),
    askNote: () => new Promise<string | null>((resolve) => setMenuSheet({ kind: "note", title: "› note in margin", detail: "your words beside this passage", resolve: (value) => resolve(typeof value === "string" ? value : null) })),
    confirm: (title, detail, options) => new Promise<boolean | "mine">((resolve) => setMenuSheet({ kind: "confirm", title, detail, mine: options?.mine,
      resolve: (value) => resolve(value === "mine" ? "mine" : value === true) })),
    // The window showing the passage opens the Reader's own question card there (one opens beside if none shows it).
    writeOwnQuestion: (object, anchor) => {
      const windowId = object.windowId && inquiries.current.has(object.windowId) ? object.windowId : null;
      const inquiry = windowId ? inquiries.current.get(windowId) : undefined;
      if (inquiry) inquiry.writeOwnQuestion(anchor.spanId, (object.selection || object.text).trim());
      else toastNow("open the passage's book on this desk to write your own question there");
    },
    showMe: (text, anchor, owner) => padsHost.showMe ? padsHost.showMe(text, anchor, owner ?? undefined) : Promise.resolve(null),
    figureDestination: () => runningPadOf(deskIdRef.current),
    showFigure: (object, figure, destination) => {
      showInCompanion(vaultKey, {
        key: mintId("cfig"), figure, destination, anchor: { extractionId: object.extractionId ?? null, spanId: object.spanId ?? null },
        sourceTitle: object.windowId ? titleOf(wsRef.current.windows[object.windowId]) : null,
      });
      // The figure is in the companion's answer: it is summoned (docked) if it was hidden.
      if (companionStateRef.current.mode === "hidden") stepCompanion({ kind: "dock" });
    },
    landFigure: (object, figure, padId) => landFigureBlock({ extractionId: object.extractionId ?? null, spanId: object.spanId ?? null, spanIds: passageIds(object) }, figure, padId).catch(() => undefined),
    windowMove: (kind, windowId) => {
      const id = deskIdRef.current;
      if (!id) return;
      if (kind === "new_desk") {
        newDeskFrom(windowId);
        return;
      }
      commit(setFocus(wsRef.current, id, windowId));
      if (kind === "gather") runRef.current({ kind: "gather", toNewDesk: false });
      else if (kind === "share_slot") runRef.current({ kind: "pair" });
      else runRef.current({ kind: "unpair" });
    },
    showKnows: (object) => setKnows(objectInput(object, deskIdRef.current)),
    teachMe: (entry) => openLesson(entry),
    // One import key per sheet: a resent import of the same exercise is the same import.
    reviewExercise: (object, anchor) => setExerciseSheet({ object, anchor, key: mintId("import") }),
    promotedRows: () => menuPromotedRows.current,
    withheld: () => menuWithheldAnswer.current.promise,
  }), [deskId, menuTransport, mintId, toastNow, stepCompanion, openContent, carryQuestion, appendTo, padsHost, runningPadOf, store, commit, openLesson, newDeskFrom, vaultKey, titleOf, landFigureBlock]);

  // A right-click inside a notebook frame (spec §11.3) opens the pad menu in the stack window that shows the
  // notebook's owner: a pad's cells ("your pad") or a lesson's notebook ("the lesson", inserting under the lesson).
  // Registered once; the request's text is the frame's selection, untrusted, and only ever shown quoted.
  useEffect(() => {
    setNotebookMenuOpener((request) => {
      const id = deskIdRef.current;
      const shows = (window: DeskWindow) => {
        if (request.lessonId) {
          const lessonId = request.lessonId;
          return (window.stack ?? []).some((entry) => entry.kind === "lesson" && entry.lessonId === lessonId)
            || (window.content?.kind === "lesson" && window.content.lessonId === lessonId)
            || lessonDesk.openingsFor(window.windowId).includes(lessonKey(lessonId));
        }
        return (window.stack ?? []).some((entry) => entry.kind === "pad" && entry.padId === request.padId)
          || (window.content?.kind === "pad" && window.content.padId === request.padId);
      };
      const target = Object.values(wsRef.current.windows).find((window) => window.deskId === id && shows(window) && padHandles.current.has(window.windowId));
      if (!id || !target) return;
      // A press inside a frame never reaches the desks, so its window takes the focus here first (the pad menu
      // belongs to the active window and closes when the focus leaves it); the menu opens once it has it.
      if (focusIdRef.current !== target.windowId) commit(setFocus(wsRef.current, id, target.windowId));
      timers.set(() => padHandles.current.get(target.windowId)?.openFrameMenu(request), 0);
    });
    return () => setNotebookMenuOpener(null);
  }, [lessonDesk, commit, timers]);

  /** A pad line in view: its stack window takes the focus (opened beside when no stack shows the pad) and the line
   * flashes (the ✎ marks' way back to a pad). */
  const openPadBlock = (padId: string, blockId: string | null) => {
    const id = deskIdRef.current;
    if (!id) return;
    const stackWindow = Object.values(wsRef.current.windows).find((window) => window.deskId === id && (window.stack ?? []).some((entry) => entry.kind === "pad" && entry.padId === padId));
    if (stackWindow) {
      commit(setFocus(wsRef.current, id, stackWindow.windowId));
      padHandles.current.get(stackWindow.windowId)?.showPad(padId);
    } else {
      openContent({ kind: "pad", padId });
    }
    if (blockId) timers.set(() => window.dispatchEvent(new CustomEvent("learnloop:pad-flash", { detail: { blockId } })), 0);
  };

  /** A promoted row's action, for the object its menu was opened on (a source object or a pad line): open its place
   * (a pad at its line), What this knows of that object, the carried list, a margin note's or a figure's passage
   * (the Reader shows the passage's notes and figures there). False when the row names nothing that can open. */
  onPromotedRef.current = (row, origin) => {
    const place = promotedRef(row);
    if (place) {
      if (place.ref.kind === "pad") openPadBlock(place.ref.padId, row.action.target?.blockId ?? null);
      else openContent(place.ref, { spanId: place.spanId });
      return true;
    }
    switch (row.action.verb) {
      case "knows":
        if (!origin) return false;
        setKnows(origin);
        return true;
      case "carried":
        setCarriedOpen(true);
        return true;
      case "annotation":
      case "figure": {
        // The row's own passage when it names one, else the passage the menu was opened on.
        const named = row.action as { extractionId?: string; target?: { spanId?: string } };
        const extractionId = named.extractionId ?? origin?.extractionId;
        const spanId = named.target?.spanId ?? origin?.spanId;
        if (!extractionId || !spanId) {
          toastNow("couldn't find the passage this belongs to");
          return false;
        }
        openPassage(extractionId, spanId);
        return true;
      }
      default:
        return false;
    }
  };

  /** The one right-click listener (spec §4.4: the menu opens once): on a passage, a cue, a highlight or note, a
   * window header or a pad line, the menu for that object; anywhere else, nothing of ours. */
  const onStageContextMenu = (event: React.MouseEvent) => {
    if (overviewRef.current) return;
    const target = event.target as Element;
    const object = objectAt(target, (windowId) => wsRef.current.windows[windowId]?.content?.kind ?? null, (windowId) => {
      const content = wsRef.current.windows[windowId]?.content;
      return content && (content.kind === "source" || content.kind === "video") ? { sourceId: content.sourceId, extractionId: content.extractionId } : null;
    }, { x: event.clientX, y: event.clientY }, firstVisibleSpan);
    if (!object) return;
    event.preventDefault();
    event.stopPropagation();
    openMenuOn(object);
  };
  const openMenuOn = (object: MenuObject) => {
    if (object.kind === "pad_line") {
      closeSourceMenu();
      const handle = object.windowId ? padHandles.current.get(object.windowId) : undefined;
      if (handle && object.padId) handle.openMenu(object.padId, object.blockId ?? null, object.at, object.selection, object.blockIds);
      return;
    }
    liveMenu.current = object;
    menuPromotedRows.current = [];
    // The object's protection is known from its first answer; a verb that would send its words waits for it.
    menuOpening.current++;
    menuWithheldAnswer.current.resolve(null);
    setMenuWithheld(null);
    let resolve: (withheld: boolean | null) => void = () => undefined;
    menuWithheldAnswer.current = { promise: new Promise<boolean | null>((done) => { resolve = done; }), resolve: (withheld) => resolve(withheld) };
    if (!hasPassage(object)) menuWithheldAnswer.current.resolve(object.kind !== "window");
    setMenu(object);
  };

  const openMenuContext: MenuContext = { ...menuContext, begin: () => {
    if (!menu || liveMenu.current !== menu) return false;
    closeSourceMenu();
    return true;
  } };

  // The object under the pointer, for `.` and the ContextMenu key (else the focused window's first object).
  const hoverTarget = useRef<Element | null>(null);
  /** `n` (a margin note on the hovered passage) and `b` (the hovered object's first promoted action, labelled
   * opened once it ran); false when the pointer is over nothing they apply to. */
  hoveredKeyRef.current = (what) => {
    const hovered = hoverTarget.current;
    if (!hovered || !stageRef.current?.contains(hovered)) return false;
    const object = objectAt(hovered, (windowId) => wsRef.current.windows[windowId]?.content?.kind ?? null, (windowId) => {
      const content = wsRef.current.windows[windowId]?.content;
      return content && (content.kind === "source" || content.kind === "video") ? { sourceId: content.sourceId, extractionId: content.extractionId } : null;
    }, (() => {
      const box = hovered.getBoundingClientRect();
      return { x: box.left + 30, y: box.bottom + 2 };
    })(), firstVisibleSpan);
    if (!object || !hasPassage(object)) return false;
    if (what === "note" && object.kind !== "passage" && object.kind !== "cue") return false;
    const input = objectInput(object, deskIdRef.current);
    void menuPromoted.passagePromoted(input).then((found) => {
      if (found.pendingJob) void menuPromoted.passagePromotedCancel({ jobId: found.pendingJob.jobId }).catch(() => undefined);
      if (what === "note") {
        void runVerb("note", object, { ...menuContext, withheld: async () => found.withheld !== false });
        return;
      }
      const first = found.rows[0];
      if (!first) {
        toastNow("nothing to open from here yet");
        return;
      }
      if (onPromotedRef.current(first, input)) menuPromoted.label(first.rowId, "opened");
    }, () => toastNow("couldn't read what this passage holds just now"));
    return true;
  };
  openMenuByKeyRef.current = () => {
    const stage = stageRef.current;
    const focusWindow = focusIdRef.current;
    const kindOf = (windowId: string) => wsRef.current.windows[windowId]?.content?.kind ?? null;
    const sourceOf = (windowId: string) => {
      const content = wsRef.current.windows[windowId]?.content;
      return content && (content.kind === "source" || content.kind === "video") ? { sourceId: content.sourceId, extractionId: content.extractionId } : null;
    };
    const atOf = (element: Element) => {
      const box = element.getBoundingClientRect();
      return { x: box.left + 30, y: box.bottom + 2 };
    };
    const hovered = hoverTarget.current;
    if (hovered && stage?.contains(hovered)) {
      const object = objectAt(hovered, kindOf, sourceOf, atOf(hovered), firstVisibleSpan);
      if (object) {
        openMenuOn(object);
        return true;
      }
    }
    if (!focusWindow || !stage) return false;
    const spanId = firstVisibleSpan(focusWindow);
    const host = stage.querySelector(`[${WINDOW_ATTRIBUTE}="${focusWindow}"]`);
    const first = spanId ? host?.querySelector(`[data-span-id="${spanId}"], [data-transcript-span="${spanId}"]`) : host?.querySelector(".desk-pane-head");
    if (!first) return false;
    const object = objectAt(first, kindOf, sourceOf, atOf(first), firstVisibleSpan);
    if (!object) return false;
    openMenuOn(object);
    return true;
  };

  // The shelf's TODAY · RUNNING PAD (spec §5.6): the last three blocks of today, marked by where each came from.
  const shelfToday = (() => {
    const padId = runningPadOf(deskId);
    const pad = padId ? store.pads[padId] : null;
    if (!padId || !pad) return null;
    const today = localDay();
    const lines = pad.blocks.filter((block) => block.day === today && block.kind !== "lifted").slice(-3).map((block) => {
      const words = block.bodyMd.replace(/\s+/g, " ").trim();
      return {
        blockId: block.blockId,
        mark: block.kind === "figure" ? "◇ fig" : block.provenance === "source" ? "§" : block.provenance === "tutor" || block.provenance === "learnloop" ? "◇" : "›",
        text: words.length > 60 ? `${words.slice(0, 60)}…` : words || "…",
      };
    });
    return {
      lines,
      onOpen: () => {
        const id = deskIdRef.current;
        const stackWindow = Object.values(wsRef.current.windows).find((window) => window.deskId === id && (window.stack ?? []).some((entry) => entry.kind === "pad" && entry.padId === padId));
        if (!id || !stackWindow) return;
        commit(setFocus(wsRef.current, id, stackWindow.windowId));
        padHandles.current.get(stackWindow.windowId)?.showPad(padId);
      },
    };
  })();

  // -- window status from inside (title, reading place, rail hosts, media) ------------------------

  const viewTimers = useRef(new Map<string, { handle: unknown; save: () => void }>());
  const shellTimers = useRef(new Set<unknown>());
  // The shell's own timers (an entering fade) end with it. A reading place still waiting for its idle save
  // is handed to the vault's store at once, which outlives the shell and sends it.
  useEffect(() => () => {
    for (const pending of viewTimers.current.values()) {
      timers.clear(pending.handle);
      pending.save();
    }
    viewTimers.current.clear();
    for (const handle of shellTimers.current) timers.clear(handle);
    shellTimers.current.clear();
  }, [timers]);
  const statusFor = useMemo(() => new Map<string, (next: SourceStatus) => void>(), []);
  const onStatusFor = useCallback((windowId: string) => {
    let handler = statusFor.get(windowId);
    if (!handler) {
      handler = (next: SourceStatus) => {
        setStatus((all) => ({ ...all, [windowId]: { ...all[windowId], ...next } }));
        // The window changed: its card's picture is rebuilt the next time the overview shows it.
        miniatures.invalidate(windowId);
        // The reading place, saved as the window's scroll anchor by passage once the learner settles
        // (spec §3.5: span-based, never pixels), and only for the window the learner is reading.
        if (next.readingSpan && focusIdRef.current === windowId) {
          const previous = viewTimers.current.get(windowId);
          if (previous !== undefined) timers.clear(previous.handle);
          const save = () => {
            const current = store.ws;
            const window = current.windows[windowId];
            if (!window || window.view?.spanId === next.readingSpan) return;
            store.commit(setView(current, window.deskId, windowId, { ...window.view, spanId: next.readingSpan }));
          };
          viewTimers.current.set(windowId, {
            save,
            handle: timers.set(() => {
              viewTimers.current.delete(windowId);
              save();
            }, VIEW_SAVE_IDLE_MS),
          });
        }
      };
      statusFor.set(windowId, handler);
    }
    return handler;
  }, [statusFor, timers, store, miniatures]);

  const jumpReadyFor = useMemo(() => new Map<string, (jump: ((spanId: string) => void) | null) => void>(), []);
  const onJumpReadyFor = useCallback((windowId: string) => {
    let handler = jumpReadyFor.get(windowId);
    if (!handler) {
      handler = (jump) => {
        if (!jump) {
          jumps.current.delete(windowId);
          return;
        }
        jumps.current.set(windowId, jump);
        const pending = pendingJump.current.get(windowId);
        if (pending) {
          pendingJump.current.delete(windowId);
          jump(pending);
        }
      };
      jumpReadyFor.set(windowId, handler);
    }
    return handler;
  }, [jumpReadyFor]);

  const inquiryReadyFor = useMemo(() => new Map<string, (inquiry: WindowInquiry | null) => void>(), []);
  const onInquiryReadyFor = useCallback((windowId: string) => {
    let handler = inquiryReadyFor.get(windowId);
    if (!handler) {
      handler = (inquiry) => {
        if (inquiry) inquiries.current.set(windowId, inquiry);
        else inquiries.current.delete(windowId);
      };
      inquiryReadyFor.set(windowId, handler);
    }
    return handler;
  }, [inquiryReadyFor]);

  // A source window's ask goes to the companion (its rail is not on the desk): with words it is asked now, on the
  // window's reading and passage (a named parent makes it a branch of that question); without, the companion opens
  // on the passage with its words as the chip, for the learner to ask.
  const windowAsk = (windowId: string, ask: WindowAsk) => {
    const content = wsRef.current.windows[windowId]?.content;
    if (!content || (content.kind !== "source" && content.kind !== "video")) return;
    if (ask.question.trim()) {
      asks.ask({
        deskId: deskIdRef.current, windowId, surface: "desk", question: ask.question.trim(), extractionId: content.extractionId,
        spanId: ask.spanId, selectionSpanIds: ask.selectionSpanIds, quote: ask.quote,
        ...(ask.parentExchangeId !== undefined ? { parentExchangeId: ask.parentExchangeId } : {}),
        ...(ask.answerMode ? { answerMode: ask.answerMode } : {}),
        ...personalizedInput(),
      }, store.settled());
    } else if (ask.quote) {
      setChip({ quote: clipQuote(ask.quote, 400), spanIds: ask.selectionSpanIds, windowId });
    }
    if (companionStateRef.current.mode === "hidden") stepCompanion({ kind: "c", anchor: null, stage: stageNow.current });
  };
  const windowAskRef = useRef(windowAsk);
  windowAskRef.current = windowAsk;
  const askFor = useMemo(() => new Map<string, (ask: WindowAsk) => void>(), []);
  const onAskFor = useCallback((windowId: string) => {
    let handler = askFor.get(windowId);
    if (!handler) {
      handler = (ask) => windowAskRef.current(windowId, ask);
      askFor.set(windowId, handler);
    }
    return handler;
  }, [askFor]);

  // "what matters here?" in a window: the goal's path view when the desk has a goal band, else the reading's own path
  // in that window.
  const windowOpenPath = (windowId: string) => {
    const content = wsRef.current.windows[windowId]?.content;
    if (!content || (content.kind !== "source" && content.kind !== "video")) return;
    if (goalPathRef.current.open) return;
    if (goalPathRef.current.toggle()) return;
    if (inquiries.current.get(windowId)?.showPath("open")) return;
    openContent({ kind: "panel", panel: "path", extractionId: content.extractionId } as ContentRefDto);
  };
  const windowOpenPathRef = useRef(windowOpenPath);
  windowOpenPathRef.current = windowOpenPath;
  const openPathFor = useMemo(() => new Map<string, () => void>(), []);
  const onOpenPathFor = useCallback((windowId: string) => {
    let handler = openPathFor.get(windowId);
    if (!handler) {
      handler = () => windowOpenPathRef.current(windowId);
      openPathFor.set(windowId, handler);
    }
    return handler;
  }, [openPathFor]);

  // Side by side (the v1 Reader's second pane as two windows, spec §21.1): Ctrl+\ or a list's "side by side" in a
  // book window opens the other book in a window paired with it; following, F6 and the way back live in DeskPairs.
  const pairs = useMemo(() => new DeskPairs({
    loaded: () => store.loaded,
    windowOf: (id) => {
      const content = wsRef.current.windows[id]?.content;
      return content && content.kind === "source" ? { sourceId: content.sourceId, extractionId: content.extractionId } : null;
    },
    correspondents: (input) => api.readerCorrespondents(input),
    jump: (id, spanId) => {
      const jump = jumps.current.get(id);
      if (jump) jump(spanId);
      else pendingJump.current.set(id, spanId);
    },
    notice: (text) => toastNow(text),
    record: (event, payload) => logReaderAction(event, payload),
    // The vault's pairs outlive this mount: back from a check or its feedback, a pair is still one.
  }, keptPairsFor(vaultKey)), [toastNow, store, vaultKey]);
  const windowOpenPair = (windowId: string, target: PaneTarget) => {
    const id = deskIdRef.current;
    const current = wsRef.current;
    if (!id || !current.windows[windowId]) return;
    const card = library?.find((entry) => entry.sourceId === target.sourceId);
    const kind = card && isVideoCard(card) ? "video" : "source";
    const step = openPaired(current, id, windowId, { kind, sourceId: target.sourceId, extractionId: target.extractionId } as ContentRefDto,
      () => mintId("win"), { spanId: target.spanId, view: target.spanId ? { spanId: target.spanId } : {} });
    commit(step);
    if (step.windowId !== windowId) pairs.pair(windowId, step.windowId);
    if (step.existed && target.spanId) {
      const jump = jumps.current.get(step.windowId);
      if (jump) jump(target.spanId);
      else pendingJump.current.set(step.windowId, target.spanId);
    }
  };
  const windowOpenPairRef = useRef(windowOpenPair);
  windowOpenPairRef.current = windowOpenPair;
  const pairHandlers = useMemo(() => new Map<string, { open: (target: PaneTarget) => void; section: (section: { extractionId: string; sectionId: string } | null) => void; key: (key: "follow" | "other") => void; touched: () => void }>(), []);
  const pairHandlersFor = useCallback((windowId: string) => {
    let handlers = pairHandlers.get(windowId);
    if (!handlers) {
      handlers = {
        open: (target) => windowOpenPairRef.current(windowId, target),
        section: (section) => void pairs.crossed(windowId, section),
        touched: () => pairs.touched(windowId),
        key: (key) => {
          if (key === "follow") {
            pairs.toggleFollow(windowId);
            return;
          }
          const partner = pairs.partnerOf(windowId);
          const id = deskIdRef.current;
          if (partner && id) commit(setFocus(wsRef.current, id, partner));
        },
      };
      pairHandlers.set(windowId, handlers);
    }
    return handlers;
  }, [pairHandlers, pairs, commit]);

  // A companion answer that lands while the desks are shown is told to the window it was asked from (else the first
  // window on the desk showing its reading): a follow-up joins that window's detours with its parent, so walking back
  // to where the learner was asks "does this make sense now?" there. Answers already in the thread when the desks
  // open were told before, or belong to a visit that has ended.
  const toldAnswers = useRef<Set<string> | null>(null);
  const companionVersion = asks.getVersion();
  useEffect(() => {
    const answerId = (exchange: CompanionExchange) => (exchange.answer ? exchange.answer.readerAnswerEventId || exchange.answer.eventId : null);
    const thread = asks.thread(deskId);
    if (toldAnswers.current === null) {
      toldAnswers.current = new Set(thread.map(answerId).filter((id): id is string => Boolean(id)));
      return;
    }
    const told = toldAnswers.current;
    const asExchange = (exchange: CompanionExchange, id: string): WindowExchange => ({
      id, parentExchangeId: exchange.answer?.parentExchangeId ?? exchange.request.parentExchangeId ?? null,
      extractionId: exchange.extractionId, spanId: exchange.spanId, question: exchange.question, answerMd: exchange.answer?.answerMd ?? "",
    });
    for (const exchange of thread) {
      const id = answerId(exchange);
      if (exchange.status !== "answered" || !id || told.has(id)) continue;
      told.add(id);
      const current = wsRef.current;
      const shows = (windowId: string | null) => {
        const content = windowId ? current.windows[windowId]?.content : null;
        return Boolean(content && (content.kind === "source" || content.kind === "video") && content.extractionId === exchange.extractionId);
      };
      const desk = deskId ? deskById(current, deskId) : null;
      const windowId = shows(exchange.windowId) ? exchange.windowId : (desk?.slots.flat().find((each) => shows(each)) ?? null);
      const inquiry = windowId ? inquiries.current.get(windowId) : undefined;
      if (!inquiry) continue;
      const me = asExchange(exchange, id);
      const parent = me.parentExchangeId ? thread.find((each) => answerId(each) === me.parentExchangeId) : undefined;
      inquiry.noteAnswer(me, parent ? asExchange(parent, me.parentExchangeId as string) : null);
    }
  }, [asks, deskId, companionVersion]);

  const mediaReadyFor = useMemo(() => new Map<string, (toggle: (() => void) | null) => void>(), []);
  const onMediaReadyFor = useCallback((windowId: string) => {
    let handler = mediaReadyFor.get(windowId);
    if (!handler) {
      handler = (toggle) => {
        if (toggle) media.current.set(windowId, toggle);
        else media.current.delete(windowId);
      };
      mediaReadyFor.set(windowId, handler);
    }
    return handler;
  }, [mediaReadyFor]);

  const railNodeFor = useMemo(() => new Map<string, (node: HTMLElement | null) => void>(), []);
  const onRailNode = useCallback((windowId: string) => {
    let handler = railNodeFor.get(windowId);
    if (!handler) {
      handler = (node) => setRailHosts((hosts) => (hosts[windowId] === node ? hosts : { ...hosts, [windowId]: node }));
      railNodeFor.set(windowId, handler);
    }
    return handler;
  }, [railNodeFor]);

  /** Per desk and book, the panel window that shows the book's rail: the claimed one, else the first. */
  const railPanelOf = useCallback((deskOf: string, extractionId: string): string | null => {
    if (!ws) return null;
    const desk = deskById(ws, deskOf);
    if (!desk) return null;
    const panels = desk.slots.flat().filter((id) => {
      const content = ws.windows[id]?.content;
      return content?.kind === "panel" && (content.panel === "guide" || content.panel === "notes") && content.extractionId === extractionId;
    });
    const claimed = railClaims[`${deskOf}:${extractionId}`];
    return claimed && panels.includes(claimed) ? claimed : panels[0] ?? null;
  }, [ws, railClaims]);

  const sourceWindowOf = useCallback((deskOf: string, extractionId: string): string | null => {
    if (!ws) return null;
    const desk = deskById(ws, deskOf);
    if (!desk) return null;
    return desk.slots.flat().find((id) => {
      const content = ws.windows[id]?.content;
      return (content?.kind === "source" || content?.kind === "video") && content.extractionId === extractionId;
    }) ?? null;
  }, [ws]);

  // -- rendering ------------------------------------------------------------------------------------

  // An undo offer holds only while the window is still closed (a close the server refused is no close).
  const undoShown = undo && undo.deskId === deskId && undo.until > timers.now()
    && (ws?.closed[undo.deskId] ?? []).some((entry) => entry.window.windowId === undo.windowId) ? undo : null;
  useEffect(() => {
    if (!undo) return;
    const handle = timers.set(() => setUndo(null), Math.max(0, undo.until - timers.now()));
    return () => timers.clear(handle);
  }, [undo, timers]);

  if (!ws) {
    return (
      <div className="desk-shell" data-desk-shell="">
        <header className="desk-top"><span className="desk-brand">◇ LearnLoop</span></header>
        <main className="desk-main"><aside className="desk-shelf" /><section className="desk-stage" ref={stageRef} /></main>
        <footer className="desk-keys"><span className="note">◐ Opening your desks…</span></footer>
      </div>
    );
  }

  const paneBody = (window: DeskWindow, lifecycle: WindowLifecycle): ReactNode => {
    const content = window.content;
    const card = content && (content.kind === "source" || content.kind === "video") ? library?.find((entry) => entry.sourceId === content.sourceId) ?? null : null;
    if (renderPane) return renderPane({ window, lifecycle, card });
    if (window.kind === "pad_stack" || content?.kind === "pad" || content?.kind === "lesson") {
      // A pad or a lesson in a slot of its own is a stack of one.
      const stack = window.stack ?? (content?.kind === "pad" ? [{ kind: "pad" as const, padId: content.padId }] : content?.kind === "lesson" ? lessonStack(content) : []);
      return <PadStackWindow windowId={window.windowId} stack={stack} view={window.view ?? {}} info={emissionOpen === window.windowId} onInfo={(open) => setEmissionOpen(open ? window.windowId : null)} />;
    }
    if (!content) return <div className="desk-panel desk-quiet">This window can’t open here. Close it and reopen the source from your library.</div>;
    switch (content.kind) {
      case "source":
      case "video": {
        const railPanel = railPanelOf(window.deskId, content.extractionId);
        const railNode = railPanel ? railHosts[railPanel] ?? null : null;
        const railContent = railPanel ? ws.windows[railPanel]?.content : null;
        const railTab = railContent?.kind === "panel" && railContent.panel === "notes" ? "notes" : "guide";
        const props: ComponentProps<typeof SourceWindow> = {
          content,
          card,
          libraryLoaded: library !== null,
          // The app's way back to this book (a check's or a problem's return, the plan's reading) not done yet: the window
          // opens at that passage. Its Reader places itself once it opens, asynchronously (a saved place, its reading
          // history), so a jump made before that would be undone; a window that opens at the passage is not.
          startSpan: openingAt(window.windowId, window.deskId, content)
            ?? (typeof window.view?.spanId === "string" ? (window.view.spanId as string) : null),
          railHost: railNode && railPanel ? { node: railNode, tab: railTab, lifecycle: lifecycles[railPanel] ?? { windowId: railPanel, state: "hidden" }, hub: hubFor(railPanel), claims: claimsFor(railPanel) } : null,
          onStatus: onStatusFor(window.windowId),
          onJumpReady: onJumpReadyFor(window.windowId),
          onMediaReady: onMediaReadyFor(window.windowId),
          onInquiryReady: onInquiryReadyFor(window.windowId),
          onAsk: onAskFor(window.windowId),
          onOpenPath: onOpenPathFor(window.windowId),
          // A note a search result opened the window for (its identity in the window's view).
          openNote: typeof window.view?.annotationId === "string" ? (window.view.annotationId as string) : null,
          drainHost: draining && window.deskId === deskId ? drainWrapHost : null,
          onOpenBeside: openHit,
          onOpenPair: pairHandlersFor(window.windowId).open,
          onSection: pairHandlersFor(window.windowId).section,
          onPairKey: pairHandlersFor(window.windowId).key,
          onTouched: pairHandlersFor(window.windowId).touched,
          onWorkOnPad: (handoff) => void workOnPad(handoff),
          onSkimming: skimmingFor(window.windowId),
          onError,
          ...(reader ? { reader } : {}),
          // A book following a video marks its passage over the goal lens (RD10); a due check's closed marker (or its
          // open card) sits before its host passage (RD7).
          lens: checkLenses.lensFor(window.windowId, content.extractionId, content.kind === "source"
            ? followLenses.lensFor(window.windowId, goalDesk.lensFor(window.windowId, content.extractionId), videoDesk.followedSpan(window.windowId))
            : goalDesk.lensFor(window.windowId, content.extractionId), checkDesk, checkNow),
        };
        if (content.kind === "video") {
          return <VideoWindow {...props} windowId={window.windowId} desk={videoDesk} transport={videoTransport} poller={poller} />;
        }
        return <SourceWindow {...props} />;
      }
      case "panel": {
        if (content.panel === "guide" || content.panel === "notes") {
          const extractionId = content.extractionId ?? "";
          const owner = railPanelOf(window.deskId, extractionId);
          return (
            <RailHostPanel
              panel={content.panel}
              bound={Boolean(extractionId && sourceWindowOf(window.deskId, extractionId))}
              claimed={owner !== null && owner !== window.windowId}
              onNode={onRailNode(window.windowId)}
              onClaim={() => setRailClaims((claims) => ({ ...claims, [`${window.deskId}:${extractionId}`]: window.windowId }))}
            />
          );
        }
        if (content.panel === "path") {
          return (
            <PathPanel
              extractionId={content.extractionId ?? null}
              onError={onError}
              onJump={(spanId) => {
                const target = content.extractionId ? sourceWindowOf(window.deskId, content.extractionId) : null;
                if (!target) return;
                commit(setFocus(wsRef.current, window.deskId, target));
                const jump = jumps.current.get(target);
                if (jump) jump(spanId);
              }}
            />
          );
        }
        return <LibraryPanel query={null} onOpenHit={openHit} onClose={() => run({ kind: "closeWindow" })} onError={onError} library={library ?? null} reader={reader ?? null} />;
      }
      case "compare":
        return <LibraryPanel query={content.query ?? null} anchor={compareAnchorOf(window.view)} onOpenHit={openHit} onClose={() => run({ kind: "closeWindow" })} onError={onError} library={library ?? null} reader={reader ?? null} />;
      case "thread":
        return (
          <ThreadWindow
            rootExchangeId={content.rootExchangeId}
            extractionId={typeof window.view?.extractionId === "string" ? (window.view.extractionId as string) : null}
            onOpenClaim={openClaim}
          />
        );
      default:
        return <div className="desk-panel desk-quiet">This window can’t open here. Close it and reopen the source from your library.</div>;
    }
  };

  // The overview's relations, links and gather ghosts for the selection (or, entering, the focus).
  const linkedFrom = overview || zooming ? selection?.windowId ?? focusId : null;
  const selectedRelations = relatedTo(linkedFrom);
  const linkRects = new Map<string, Rect>();
  ws.desks.forEach((each, row) => each.slots.forEach((slot, index) => {
    const rect = ovLayout?.cards[row]?.[index];
    if (rect) for (const id of slot) linkRects.set(id, rect);
  }));
  const fromCard = linkedFrom ? linkRects.get(linkedFrom) ?? null : null;
  const links = fromCard
    ? curvedLinks(fromCard, selectedRelations.filter((relation) => linkRects.has(relation.windowId)).map((relation) => ({ rect: linkRects.get(relation.windowId) as Rect, relation })))
    : [];
  const ghosts: Array<{ key: string; rect: Rect }> = [];
  if (overview && gatherPreview && selection && ovLayout) {
    const row = ws.desks.findIndex((each) => each.deskId === selection.deskId);
    const each = ws.desks[row];
    if (each) {
      const sameDesk = selectedRelations.filter((relation) => ws.windows[relation.windowId]?.deskId === each.deskId);
      const { order } = gatherOrder(each.slots, selection.windowId, sameDesk);
      order.forEach((slot, index) => {
        // Only the linked cards: where each would go.
        const linked = slot.some((id) => sameDesk.some((relation) => relation.windowId === id));
        if (linked && each.slots[index]?.[0] !== slot[0] && ovLayout.cards[row][index]) ghosts.push({ key: slot.join("+"), rect: ovLayout.cards[row][index] });
      });
    }
  }
  const movedShown = movedNotice && movedNotice.deskId === deskId && movedNotice.until > timers.now() ? movedNotice : null;
  const focusWindow = focusId ? ws.windows[focusId] : undefined;
  // What a question is asked about: the selection's passages, else the focused source's reading place.
  const thread = asks.thread(deskId);
  const grounding: Grounding = groundingFor(ws, chip, focusWindow, status);
  groundingRef.current = grounding;
  const focusZoom = typeof focusWindow?.view?.zoom === "number" ? (focusWindow.view.zoom as number) : 1;
  // Every window's place: its slot, its pane, its reading rect and its card rect. Rendered in window-id
  // order, so reordering slots moves no element in the DOM (a moved iframe would reload its player).
  const windowPlaces = ws.desks.flatMap((each, rowIndex) => {
    const eachCam = camX[each.deskId] ?? 0;
    const rects = slotRects(each.slots.length, stage);
    const top = rowTop(rowIndex, stage) - rowTop(deskIndex, stage);
    return each.slots.flatMap((slot, index) => {
      const slotReading = { x: rects[index].x - eachCam, y: top + rects[index].y, w: rects[index].w, h: rects[index].h };
      const slotCard = ovLayout?.cards[rowIndex]?.[index] ?? slotReading;
      const readingPanes = paneRects(slotReading, slot.length);
      const cardPanes = paneRects(slotCard, slot.length);
      return slot.flatMap((id, pane) => {
        const window = ws.windows[id];
        return window ? [{ window, each, rowIndex, index, pane, slot, reading: readingPanes[pane], card: cardPanes[pane] }] : [];
      });
    });
  }).sort((a, b) => (a.window.windowId < b.window.windowId ? -1 : a.window.windowId > b.window.windowId ? 1 : 0));

  // The slivers: the current desk's; while a zoom leaves the overview, the desk it lands on.
  const sliverDesk = leaveTarget ? deskById(ws, leaveTarget.deskId) : desk;
  const sliverCam = leaveTarget && sliverDesk ? leaveTarget.cams[sliverDesk.deskId] ?? 0 : cam;
  const slivers = sliverDesk && !focusMode ? sliverSlots(sliverCam, sliverDesk.slots.length, stage) : { left: null, right: null };
  const shelfRows: ShelfRow[] = desk
    ? desk.slots.flatMap((slot, index) => slot.map((id) => {
      const window = ws.windows[id];
      const kind = window?.kind ?? "source";
      return {
        windowId: id,
        slot: index,
        glyph: KIND_GLYPH[kind] ?? "§",
        kind: KIND_WORD[kind] ?? kind,
        title: titleOf(window),
        state: id === focusId ? "focus" as const : visibility[index]?.inView ? "in view" as const : null,
        progress: typeof status[id]?.progress === "number" ? status[id].progress as number : null,
        where: status[id]?.where ?? null,
        goal: goalDesk.rowGoal(window?.content && (window.content.kind === "source" || window.content.kind === "video") ? window.content.extractionId : null,
          (window?.stack ?? []).flatMap((entry) => (entry.kind === "pad" ? [entry.padId] : []))),
        // A video's accepted chapters on its minimap (RD10).
        ...(window?.content?.kind === "video" ? { chapters: videoDesk.rangesFor(window.content.extractionId) } : {}),
      };
    }))
    : [];

  const hints = overview
    ? [["h j k l", "select"], ["↵ / click", "open"], ["alt+↵", "open in focus"], ["alt+[ ]", "move"], ["alt+shift+j/k", "to a desk"], ["drag", "move a card"], ["b", "relations"], ["g", "hold: gather"], ["o / esc", "back"]]
    : focusMode
    ? [["alt+↵ / esc", "leave focus"], ["= − 0", "zoom"], ["alt+h/l", "next window"]]
    : [["alt+h/l", "window"], ["alt+j/k", "window · desk"], ["alt+[ ]", "move"], ["alt+, .", "stack · unstack"], ["alt+↵", "focus"], ["alt+w", "close"], ["c", "companion here"], ["shift+c", "dock it"], ["/", "find"]];

  return (
    <PadsHostContext.Provider value={padsHost}>
    <PenHostContext.Provider value={penHost}>
      <NotebookBridgeContext.Provider value={notebookBridge}>
    <div className={`desk-shell${penOn ? " pen-mode" : ""}${focusMode || leaveTarget?.focusWindowId ? " focus-mode" : ""}${overview ? " overview" : ""}${zooming ? " zooming" : ""}${goalDesk.hasBand ? " has-goal" : ""}`} data-desk-shell="" data-focus-mode={focusMode ? "on" : "off"} data-overview={overview ? "on" : "off"}>
      <header className="desk-top">
        <span className="desk-brand">◇ LearnLoop</span>
        <nav className="desk-tabs" aria-label="desks">
          {ws.desks.map((each) => (
            renaming === each.deskId ? (
              <input
                key={each.deskId}
                aria-label="desk name"
                defaultValue={each.title}
                autoFocus
                onBlur={() => setRenaming(null)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    const title = (event.target as HTMLInputElement).value.trim();
                    if (title && title !== each.title) commit(renameDesk(wsRef.current, each.deskId, title));
                    setRenaming(null);
                  } else if (event.key === "Escape") {
                    setRenaming(null);
                  }
                }}
              />
            ) : (
              <button
                key={each.deskId}
                type="button"
                aria-current={each.deskId === deskId ? "true" : "false"}
                title="double-click to rename"
                onClick={() => setCurrentDeskId(each.deskId)}
                onDoubleClick={() => setRenaming(each.deskId)}
              >
                {each.title}
              </button>
            )
          ))}
          <button
            type="button"
            aria-label="new desk"
            title="a new desk"
            onClick={() => {
              const id = mintId("desk");
              commit(createDesk(wsRef.current, id, "new desk"));
              setCurrentDeskId(id);
            }}
          >
            +
          </button>
        </nav>
        {goalDesk.topChip}
        <span className="grow" />
        <button type="button" className="tb penchip" aria-pressed={penOn} title="alt+p · pen mode" onClick={() => setPenOn((on) => !on)}>✎ pen <span>{penOn ? "on" : "off"}</span></button>
        {viewportWidth >= DESK_SIZES.shelfFoldBelow ? (
          <button type="button" className="tb simpen" aria-pressed={simulatePen} title="draw with the mouse as if it were a pen" onClick={() => setSimulatePen((on) => { if (!on) setPenOn(true); return !on; })}>simulate pen: <span>{simulatePen ? "on" : "off"}</span></button>
        ) : null}
        <button type="button" className="tb" aria-pressed={overview} title="alt+o" onClick={() => toggleOverview()}>o overview</button>
        <button type="button" className="tb" aria-expanded={opener} onClick={() => setOpener((open) => !open)}>+ open beside</button>
        {onLeave ? <button type="button" className="tb" onClick={onLeave}>old Reader</button> : null}
      </header>
      {goalDesk.band}
      <main className={`desk-main${viewportWidth < DESK_SIZES.shelfFoldBelow ? " rail" : ""}`} ref={mainRef}>
        <Shelf
          rows={shelfRows}
          folded={viewportWidth < DESK_SIZES.shelfFoldBelow}
          open={stripOpen}
          onOpenChange={setStripOpen}
          undo={undoShown ? { title: undoShown.title, onUndo: () => { commit(undoClose(wsRef.current, undoShown.deskId)); setUndo(null); } } : null}
          onFocus={(id) => {
            if (!deskId) return;
            // In the overview a row's click opens its window (and leaves the overview).
            if (overviewRef.current) toggleOverview({ deskId, windowId: id });
            else commit(setFocus(wsRef.current, deskId, id));
          }}
          onReorder={(id, toSlot) => {
            if (!deskId) return;
            commit(moveWindowTo(wsRef.current, deskId, id, toSlot));
          }}
          onSearch={() => setSearch({ query: "" })}
          carried={carried.list.slice(0, carried.limit).map((question) => ({ carriedId: question.carriedId, text: question.text, since: question.since }))}
          carriedMore={Math.max(0, carried.list.length - carried.limit)}
          onCarriedList={carried.list.length > carried.limit || carried.more ? () => setCarriedOpen(true) : undefined}
          today={shelfToday}
        />
        <section
          className="desk-stage"
          ref={stageRef}
          data-desk-stage=""
          onContextMenuCapture={onStageContextMenu}
          onMouseOverCapture={(event) => {
            hoverTarget.current = event.target as Element;
          }}
          onPointerDown={onStagePointerDown}
          onPointerMove={onStagePointerMove}
          onPointerUp={onStagePointerUp}
          onPointerCancel={cancelDrag}
          onLostPointerCapture={(event) => {
            // pointerup releases the capture too (after it has run): only a capture lost mid-gesture cancels.
            if (drag.current && event.pointerId !== undefined) cancelDrag();
          }}
          onClickCapture={(event) => {
            if (!scrubbedClick.current) return;
            scrubbedClick.current = false;
            event.stopPropagation();
            event.preventDefault();
          }}
        >
          <div className={`desk-world${panEase && overview && !zooming ? " pan-ease" : ""}`} ref={worldRef} data-desk-world="">
            {/* One element per window, keyed by the window: pairing, unpairing and focus mode change its
                style, never its place in the tree, so the Reader inside is never remounted (its drafts,
                selection and scroll stay). */}
            {windowPlaces.map((place) => {
              const { window, each, rowIndex, index, pane, slot } = place;
              const id = window.windowId;
              const onCurrent = each.deskId === deskId;
              const opened = visited.has(each.deskId) || onCurrent;
              const full = (!overview && onCurrent && focusMode && id === focusId) || (leaveTarget?.focusWindowId === id && leaveTarget.deskId === each.deskId);
              const hiddenInFocus = !overview && onCurrent && focusMode && !full;
              const reading = full ? { x: 0, y: 0, w: stage.width, h: stage.height } : place.reading;
              const card = place.card;
              const box = overview ? card : reading;
              const leavingTo = leaveTarget?.deskId === each.deskId;
              const slotCut = leavingTo
                ? slotVisibility(leaveTarget.cams[each.deskId] ?? 0, each.slots.length, stage)[index]
                : onCurrent ? visibility[index] : null;
              const mask = full || focusMode || !slotCut ? null : leavingTo || (!overview && !zooming && onCurrent) ? softCropMask(slotCut, reading.w) : null;
              const lifecycle = lifecycles[id] ?? { windowId: id, state: "hidden" as const };
              const paused = isPaused(lifecycle.state);
              const paired = slot.length > 1;
              const selected = overview && selection !== null && slot.includes(selection.windowId);
              const receding = overview && recedes(slot, selection?.windowId ?? null, selectedRelations, showRelations);
              const measure = FOCUS_MEASURE[window.kind] ?? FOCUS_MEASURE.source;
              return (
                <div
                  key={id}
                  ref={(node) => {
                    if (node) boxEls.current.set(id, node);
                    else boxEls.current.delete(id);
                  }}
                  data-desk-slot={`${each.deskId}:${index}:${pane}`}
                  data-desk-slot-key={slotKey(each.deskId, slot)}
                  data-desk-slot-desk={each.deskId}
                  data-desk-slot-window={id}
                  className={`desk-window${!overview && onCurrent && id === focusId ? " focus" : ""}${full ? " focused-full" : ""}${paired && !full ? (pane === 0 ? " pair-top" : " pair-bottom") : ""}${paused ? " paused" : ""}${entering.has(id) ? " entering" : ""}${selected ? " ov-selected" : ""}${receding ? " ov-recede" : ""}`}
                  style={{
                    left: box.x,
                    top: box.y,
                    width: box.w,
                    height: box.h,
                    ...(mask ? { WebkitMaskImage: mask, maskImage: mask } : {}),
                    ...(hiddenInFocus ? { visibility: "hidden" as const } : {}),
                  }}
                >
                  {opened ? (
                    <div
                      className="desk-slot-inner"
                      ref={(node) => {
                        if (node) innerEls.current.set(id, node);
                        else innerEls.current.delete(id);
                      }}
                      style={{ width: reading.w, height: reading.h }}
                    >
                      <div
                        {...{ [WINDOW_ATTRIBUTE]: id }}
                        // A paused window (another desk, out of view, a card in the overview) takes no DOM input:
                        // no focus, no typing, no tab stop, no clicks into its controls or its iframes.
                        {...(paused ? { inert: "" } : {})}
                        tabIndex={-1}
                        data-window-state={lifecycle.state}
                        data-window-kind={window.kind}
                        className={`desk-pane${paired && window.active ? " active-pane" : ""}`}
                      >
                        <div className="desk-pane-head">
                          <span className="g" title={window.kind === "pad_stack" || window.kind === "pad" ? "Pad" : KIND_WORD[window.kind] ?? "Window"}>{KIND_GLYPH[window.kind] ?? "§"}</span>
                          <span className="t">{titleOf(window)}</span>
                          {window.kind === "pad_stack" ? (
                            <button type="button" className="emi pinfo" aria-label="where your words go" title="where your words go" aria-expanded={emissionOpen === id}
                              onClick={() => setEmissionOpen((now) => (now === id ? null : id))}>ⓘ</button>
                          ) : null}
                          {window.kind === "pad_stack" ? <span className="loc">yours</span> : status[id]?.where ? <span className="loc">{status[id]?.where}</span> : null}
                          {window.content?.kind === "source" ? <FollowChip desk={videoDesk} windowId={id} /> : null}
                          {paired ? <span className="hint">{window.active ? "Alt+. gives this window its own space" : "click or alt+j/k"}</span> : null}
                          <button
                            type="button"
                            className="x"
                            aria-label={`close ${titleOf(window)}`}
                            title="close (alt+w)"
                            style={paired ? undefined : { marginLeft: "auto" }}
                            onClick={(event) => {
                              event.stopPropagation();
                              const title = titleOf(window);
                              commit(closeWindow(wsRef.current, each.deskId, id));
                              setUndo({ deskId: each.deskId, windowId: id, title, until: timers.now() + UNDO_CLOSE_MS });
                            }}
                          >
                            ✕
                          </button>
                        </div>
                        {window.kind === "pad_stack" ? goalDesk.padLine((window.stack ?? []).flatMap((entry) => (entry.kind === "pad" ? [entry.padId] : []))) : null}
                        <div className="desk-pane-body" data-desk-pane-body="">
                          {/* A window that fails to render fails alone: the desk and its other windows stay. */}
                          <ScreenErrorBoundary resetKey={id}>
                          <WindowScope lifecycle={lifecycle} hub={hubFor(id)} claims={claimsFor(id)}>
                            {/* The measure wrapper is always there (focus mode only restyles it), so entering
                                focus mode never remounts the content. */}
                            <div
                              className="desk-measure"
                              style={{
                                ...(full ? { ["--desk-measure" as string]: `${measure}px`, zoom: focusZoom } : {}),
                                display: "flex",
                                flexDirection: "column",
                                minHeight: 0,
                                height: "100%",
                              } as CSSProperties}
                            >
                              {paneBody(window, lifecycle)}
                            </div>
                          </WindowScope>
                          </ScreenErrorBoundary>
                        </div>
                      </div>
                    </div>
                  ) : null}
                  {/* The card face: laid out at its overview size, scaled to the box it sits in (static per
                      layout; the zoom scales the box). */}
                  <div
                    className="desk-card"
                    data-desk-card={id}
                    ref={(node) => {
                      if (node) cardEls.current.set(id, node);
                      else cardEls.current.delete(id);
                    }}
                    style={{ width: card.w, height: card.h, transform: `scale(${box.w / card.w}, ${box.h / card.h})` }}
                  >
                    <CardFace
                      glyph={KIND_GLYPH[window.kind] ?? "§"}
                      kind={KIND_WORD[window.kind] ?? window.kind}
                      title={titleOf(window)}
                      where={status[id]?.where ?? null}
                      progress={typeof status[id]?.progress === "number" ? status[id].progress as number : null}
                      paper={window.kind === "source" || window.kind === "video"}
                      extra={window.stack ? <div className="desk-card-bands">{window.stack.map((entry, band) => <span key={band}>› {entry.kind === "pad" ? "pad" : "lesson"} {band + 1}</span>)}</div> : undefined}
                      miniatureHost={opened ? (node) => {
                        if (node) miniHosts.current.set(id, node);
                        else miniHosts.current.delete(id);
                      } : null}
                    />
                  </div>
                </div>
              );
            })}
            {overview || zooming ? (
              <>
                {ws.desks.map((each, rowIndex) => (
                  <div
                    key={`label-${each.deskId}`}
                    className="desk-ov-label"
                    ref={(node) => {
                      if (node) lateEls.current.set(`label-${each.deskId}`, node);
                      else lateEls.current.delete(`label-${each.deskId}`);
                    }}
                    style={{ left: ovLayout?.labels[rowIndex]?.x ?? 0, top: (ovLayout?.labels[rowIndex]?.y ?? 0) - 34 }}
                  >
                    {each.title}
                  </div>
                ))}
                {showRelations && links.length > 0 ? (
                  <div className="desk-ov-links" ref={(node) => { if (node) lateEls.current.set("links", node); else lateEls.current.delete("links"); }}>
                    <LinkLayer links={links} rects={linkRects} />
                  </div>
                ) : null}
                {/* Rings around the selection (amber) and its related cards (cyan, the top four): siblings laid
                    out at the cards' rects, so a zoom's last frame draws them exactly as the overview does. */}
                {ws.desks.flatMap((each, rowIndex) => each.slots.map((slot, index) => {
                  const ringId = linkedFrom;
                  const isSel = ringId !== null && slot.includes(ringId);
                  const isRel = !isSel && showRelations && slot.some((id) => selectedRelations.some((relation) => relation.windowId === id));
                  const rect = ovLayout?.cards[rowIndex]?.[index];
                  if ((!isSel && !isRel) || !rect) return null;
                  const key = slotKey(each.deskId, slot);
                  return (
                    <div
                      key={`ring-${key}`}
                      className={`desk-ov-ring ${isSel ? "sel" : "rel"}`}
                      ref={(node) => {
                        if (node) ringEls.current.set(key, node);
                        else ringEls.current.delete(key);
                      }}
                      style={{ left: rect.x, top: rect.y, width: rect.w, height: rect.h }}
                    />
                  );
                }))}
                {overview && gatherPreview ? ghosts.map((ghost) => (
                  <div key={ghost.key} className="desk-ov-ghost" style={{ left: ghost.rect.x, top: ghost.rect.y, width: ghost.rect.w, height: ghost.rect.h }} />
                )) : null}
              </>
            ) : null}
          </div>
          {sliverDesk && slivers.left !== null && (!overview || leaveTarget) ? (
            <Sliver side="l" title={titleOf(ws.windows[sliverDesk.slots[slivers.left][0]])} kind={ws.windows[sliverDesk.slots[slivers.left][0]]?.kind ?? "source"}
              register={(node) => { if (node) sliverEls.current.set("l", node); else sliverEls.current.delete("l"); }}
              onClick={() => commit(setFocus(wsRef.current, sliverDesk.deskId, sliverDesk.slots[slivers.left as number][0]))} />
          ) : null}
          {sliverDesk && slivers.right !== null && (!overview || leaveTarget) ? (
            <Sliver side="r" title={titleOf(ws.windows[sliverDesk.slots[slivers.right][0]])} kind={ws.windows[sliverDesk.slots[slivers.right][0]]?.kind ?? "source"}
              register={(node) => { if (node) sliverEls.current.set("r", node); else sliverEls.current.delete("r"); }}
              onClick={() => commit(setFocus(wsRef.current, sliverDesk.deskId, sliverDesk.slots[slivers.right as number][0]))} />
          ) : null}
          {movedShown && !overview ? (
            <div className="desk-sliver r desk-moved" role="status"><span className="sg">→</span><span className="st">moved to “{movedShown.title}”</span></div>
          ) : null}
          {desk && desk.slots.length === 0 && !overview ? (
            <div className="desk-panel desk-quiet" style={{ position: "absolute", left: DESK_SIZES.side, top: DESK_SIZES.inset }}>
              This desk is empty. <button type="button" onClick={() => setOpener(true)}>open a source beside</button>
            </div>
          ) : null}
          {/* Marks follow their passages by left/top: none while a zoom's frames run (they write transforms only). */}
          {!overview && !zooming ? (
            <PassageMarks
              stage={stageRef.current}
              windows={(desk?.slots.flat() ?? []).flatMap((id) => {
                const content = ws.windows[id]?.content;
                return content && (content.kind === "source" || content.kind === "video") ? [{ windowId: id, extractionId: content.extractionId }] : [];
              })}
              links={padLinks}
              carried={marksCarried}
              onOpenLink={(link) => {
                const stackWindow = Object.values(wsRef.current.windows).find((window) => window.deskId === deskId && (window.stack ?? []).some((entry) => entry.kind === "pad" && entry.padId === link.padId));
                if (stackWindow && deskId) commit(setFocus(wsRef.current, deskId, stackWindow.windowId));
                window.dispatchEvent(new CustomEvent("learnloop:pad-flash", { detail: { blockId: link.blockId } }));
              }}
              onSurfaced={onCarriedSurfaced}
              onMarkCarried={(question, event) => {
                void padsTransport.carriedMark({ eventId: mintId("cev"), carriedId: question.carriedId, event, expectedVersion: question.version }).then(() => markedCarried(question.carriedId, event), () => undefined);
              }}
            />
          ) : null}
          {hud ? <div className="desk-hud" role="status">{hud}</div> : null}
          {openCheck && !checkInline ? <CheckCardOverlay desk={checkDesk} /> : null}
          <VeilLayer desk={checkDesk} root={typeof document === "undefined" ? null : document} onChange={protectCheckView} />
          <Companion
            ref={companionRef}
            state={companionState}
            dock={companionDock}
            stage={companionStage}
            overview={overview}
            reducedMotion={reduced}
            timers={timers}
            context={{
              following: focusWindow ? { glyph: KIND_GLYPH[focusWindow.kind] ?? "§", title: titleOf(focusWindow) } : null,
              goalInContext: goalDesk.hasBand,
            }}
            threadTitle={threadTitle(thread)}
            thread={thread}
            proposals={answerProposals}
            chip={chip ? { quote: chip.quote } : null}
            cannotAsk={checkDesk.heldReason() ? `the companion waits · ${checkDesk.heldReason()}` : grounding.reason}
            avoid={avoid}
            loadHistory={loadHistory}
            deskTitle={deskTitle}
            onAsk={askCompanion}
            onCancel={(requestId) => asks.cancel(requestId)}
            onRetry={(requestId) => asks.retry(requestId)}
            onClearChip={() => setChip(null)}
            onOpenClaim={openClaim}
            onOpenAnchor={(anchor) => openClaim({ extractionId: anchor.extractionId, spanId: anchor.spanId })}
            onOpenThread={openThread}
            figures={shownFigures.length ? <CompanionFigures scope={vaultKey} host={companionFigureHost} /> : null}
            tutor={readerTutor?.retrieval ? {
              personalized: { on: personalizedOn, onToggle: setPersonalizedChoice },
              anotherWay: readerTutor.anotherWay,
              onAnotherWay: (exchange) => askAgain(exchange, TUTOR_COPY.anotherWayQuestion, "alternative"),
              onDidntHelp: (exchange, text) => askAgain(exchange, text || TUTOR_COPY.didntHelpDefault, "remediate"),
              onOpenPassage: (passage) => openClaim(passage),
            } : null}
            onHide={() => stepCompanion({ kind: "hide" })}
            onDock={() => stepCompanion({ kind: "dock" })}
            onSnap={snapCompanion}
            onPill={() => {
              stepCompanion({ kind: "dock" });
              toggleOverview(null);
            }}
          />
          {search ? (
            <SearchPanel
              api={companionTransport}
              poller={poller}
              timers={timers}
              deskId={deskId}
              open={(desk?.slots.flat() ?? []).map((id) => ({ windowId: id, title: titleOf(ws.windows[id]) }))}
              deskTitle={deskTitle}
              initialQuery={search.query}
              selection={search.selection}
              blockIds={search.blockIds}
              insert={search.insert ?? null}
              reducedMotion={reduced}
              onOpenRow={openSearchRow}
              onClose={() => setSearch(null)}
            />
          ) : null}
        </section>
      </main>
      {goalDesk.overlays}
      <footer className="desk-keys">
        {goalDesk.hasBand && !overview ? <span className="gk"><kbd title="Press P to open Path">p</kbd> your path</span> : null}
        {penOn && !overview ? (
          <>
            <span className="penk"><kbd>✎</kbd> pen: underline · bracket · circle · scribble · strike</span>
            <span><kbd>Pen side button</kbd> = eraser · menu stays on <kbd title="Press Period for passage options">.</kbd> · touch only scrolls</span>
          </>
        ) : null}
        {hints.map(([keys, label]) => <span key={keys}><kbd title={keys.replace(/↵/g, "Enter").replace("= − 0", "Equals, Minus, Zero")}>{keys}</kbd> {label}</span>)}
        {ungather && ungather.deskId === deskId && !overview ? (
          <button type="button" style={{ color: "var(--desk-cyan)" }} onClick={() => gather(false)}>↺ Undo grouping</button>
        ) : null}
        {undoShown && viewportWidth < DESK_SIZES.shelfFoldBelow ? (
          // With the shelf folded to its rail, its undo line moves here.
          <button type="button" style={{ color: "var(--desk-amber)" }} onClick={() => { commit(undoClose(wsRef.current, undoShown.deskId)); setUndo(null); }}>
            ↺ undo close {undoShown.title}
          </button>
        ) : null}
        <span className="desk-dots" aria-label="windows on this desk">
          {desk?.slots.flatMap((slot, index) => slot.map((id) => (
            <button
              key={id}
              type="button"
              aria-label={titleOf(ws.windows[id])}
              title={titleOf(ws.windows[id])}
              className={id === focusId ? "f" : visibility[index]?.inView ? "in" : ""}
              style={focusMode ? (id === focusId ? { width: 46, height: 5 } : { opacity: 0.45 }) : undefined}
              onClick={() => commit(setFocus(wsRef.current, desk.deskId, id))}
            />
          )))}
        </span>
        <span className="note">hold <kbd>alt</kbd> for shortcuts</span>
      </footer>
      {opener ? (
        <OpenBeside
          library={library}
          focus={focusWindow ?? null}
          focusTitle={titleOf(focusWindow)}
          onOpen={openContent}
          onOpenCard={(card) => {
            void transport.resolveExtraction(card.sourceId)
              .then((extractionId) => openContent(contentForCard(card, extractionId)))
              .catch(() => toastNow("Couldn’t open this source. Find it in your library and try again."));
          }}
          onClose={() => setOpener(false)}
        />
      ) : null}
      {whichKey ? <WhichKey /> : null}
      {toast ? <div key={toast.key} className="desk-toast" role="status">{toast.text}</div> : null}
      {focusMode && badge !== null ? (
        <div key={badge} className="desk-zoom-badge fade" role="status">
          {Math.round(focusZoom * 100)}% · alt+↵ or esc to leave · = − to zoom
        </div>
      ) : null}
      {menu ? (
        <ContextMenu
          key={menuOpening.current}
          header={headerLine(menu, menuWithheld)}
          neutralHeader={headerLine(menu)}
          rows={sourceMenuRows(menu, openMenuContext, (() => {
            const target = appendTargetOf(deskId);
            return deskPads(deskId).find((pad) => pad.padId === target)?.title ?? "a new pad";
          })(), menuWithheld === true)}
          at={menu.at}
          object={hasPassage(menu) ? objectInput(menu, deskId) : null}
          promoted={menuPromoted}
          onPromoted={(row, origin) => onPromotedRef.current(row, origin)}
          onRows={(rows) => {
            menuPromotedRows.current = rows;
          }}
          onWithheld={(withheld, failed) => {
            if (liveMenu.current !== menu) return;
            const verdict = failed ? null : withheld;
            menuWithheldAnswer.current.resolve(verdict);
            menuWithheldAnswer.current.promise = Promise.resolve(verdict);
            setMenuWithheld(withheld);
          }}
          poller={poller}
          owner={menu.windowId}
          append={menuWithheld !== true && (menu.kind === "passage" || menu.kind === "cue" || menu.kind === "highlight") ? {
            pads: deskPads(deskId),
            current: appendTargetOf(deskId),
            onPick: (padId) => void runVerb("append", menu, openMenuContext, padId),
          } : null}
          onClose={closeSourceMenu}
        />
      ) : null}
      {knows ? (
        <KnowsPanel
          object={knows}
          load={(object) => menuTransport.passageKnows(object)}
          actions={{
            openThread: (questionEventId) => openContent({ kind: "thread", rootExchangeId: questionEventId }),
            openPadBlock: (padId) => {
              const stackWindow = Object.values(wsRef.current.windows).find((window) => (window.stack ?? []).some((entry) => entry.kind === "pad" && entry.padId === padId));
              if (stackWindow) commit(setFocus(wsRef.current, stackWindow.deskId, stackWindow.windowId));
            },
            openPassage: (extractionId, spanId) => openPassage(extractionId, spanId),
          }}
          onClose={() => setKnows(null)}
        />
      ) : null}
      {exerciseSheet ? (
        <ExerciseSheet
          readWords={() => {
            const ids = captureNodes(exerciseSheet.object).map((node) => node.spanId);
            return padsTransport.passageContent({ extractionId: exerciseSheet.anchor.extractionId, fromSpanId: ids[0] ?? exerciseSheet.anchor.spanId, toSpanId: ids[ids.length - 1] ?? exerciseSheet.anchor.spanId });
          }}
          startImport={async () => {
            const { object, anchor, key } = exerciseSheet;
            const who = await menuTransport.readingIdentity(anchor.extractionId);
            return menuTransport.readerImportExercise({
              sourceId: who.sourceId, revisionId: who.revisionId, extractionId: anchor.extractionId, renderViewId: who.renderViewId, clientIdempotencyKey: key,
              rawSelection: { extractionId: anchor.extractionId, spanId: anchor.spanId, spanIds: passageIds(object), nodes: captureNodes(object) },
            });
          }}
          readStatus={(batchId) => menuTransport.readerExerciseImportStatus({ batchId })}
          poller={poller}
          owner={exerciseSheet.object.windowId}
          onClose={() => setExerciseSheet(null)}
          onError={toastNow}
        />
      ) : null}
      {menuSheet ? <MenuSheet sheet={menuSheet} onDone={(value) => {
        menuSheet.resolve(value);
        setMenuSheet(null);
      }} /> : null}
      {carriedOpen ? (
        <CarriedList
          load={(cursor) => padsTransport.carriedList({ which: "open", ...(cursor ? { cursor } : {}) })}
          mark={(question, event) => padsTransport.carriedMark({ eventId: mintId("cev"), carriedId: question.carriedId, event, expectedVersion: question.version }).then((out) => {
            markedCarried(question.carriedId, event);
            return out;
          })}
          onClose={() => setCarriedOpen(false)}
        />
      ) : null}
      {draining && deskId ? (
        <DrainPanel
          deskTitle={desk?.title ?? "this desk"}
          load={() => padsTransport.padDrain({ deskId })}
          actions={{
            keep: (padId, version) => drainWrite(padId, "keep", version),
            leave: (padId, version) => drainWrite(padId, "unkeep", version),
            carry: (text, padId) => carryQuestion(text, { kind: "drain", ref: padId }),
          }}
          onClose={() => setDraining(false)}
          wrapUpHost={setDrainWrapHost}
        />
      ) : null}
    </div>
      </NotebookBridgeContext.Provider>
    </PenHostContext.Provider>
    </PadsHostContext.Provider>
  );
}

export function isVideoCard(card: SourceLibraryCard): boolean {
  return card.kindNoun === "video" || /youtube\.com|youtu\.be/.test(card.canonicalUri ?? "");
}

export function contentForCard(card: SourceLibraryCard, extractionId: string): ContentRefDto {
  return isVideoCard(card)
    ? { kind: "video", sourceId: card.sourceId, extractionId }
    : { kind: "source", sourceId: card.sourceId, extractionId, view: "render" };
}

function Sliver({ side, title, kind, onClick, register }: { side: "l" | "r"; title: string; kind: string; onClick: () => void; register?: (node: HTMLButtonElement | null) => void }) {
  return (
    <button type="button" ref={register} className={`desk-sliver ${side}`} aria-label={`${side === "l" ? "previous" : "next"} window: ${title}`} title={`${side === "l" ? "Previous" : "Next"} window: ${title}`} onClick={onClick}>
      <span className="sg">{side === "l" ? "‹" : "›"}</span>
      <span className="sgl" title={kind === "pad_stack" || kind === "pad" ? "Pad" : KIND_WORD[kind] ?? "Window"}>{KIND_GLYPH[kind] ?? "§"}</span>
      <span className="st">{title}</span>
    </button>
  );
}

function WhichKey() {
  const groups: Array<{ id: NonNullable<(typeof DESK_BINDINGS)[number]["group"]>; title: string }> = [
    { id: "move", title: "move" },
    { id: "windows", title: "windows" },
    { id: "pads", title: "pads" },
    { id: "media", title: "media" },
  ];
  return (
    <div className="desk-whichkey" role="dialog" aria-label="alt keys">
      <div className="wkh">alt +</div>
      <div className="wkg">
        {groups.map((group) => {
          const rows = DESK_BINDINGS.filter((binding) => binding.group === group.id && !binding.later);
          if (rows.length === 0) return null;
          return (
            <div key={group.id}>
              <div className="wkt">{group.title}</div>
              {rows.map((binding) => (
                <div key={binding.id} className="wkr"><kbd>{binding.keys.replace(/^alt\+/, "")}</kbd><span>{binding.label}</span></div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/** "+ open beside": a source from the library, or a panel for the focused book. Until search lands
 * (spec §9.3) this list is how a window is opened on a desk. */
function OpenBeside({
  library,
  focus,
  focusTitle,
  onOpen,
  onOpenCard,
  onClose,
}: {
  library: SourceLibraryCard[] | null;
  focus: DeskWindow | null;
  focusTitle: string;
  onOpen: (content: ContentRefDto) => void;
  onOpenCard: (card: SourceLibraryCard) => void;
  onClose: () => void;
}) {
  const [filter, setFilter] = useState("");
  const words = filter.trim().toLowerCase();
  const sources = (library ?? []).filter((card) => card.readerEnabled !== false && (!words || card.title.toLowerCase().includes(words)));
  const book = focus?.content && (focus.content.kind === "source" || focus.content.kind === "video") ? focus.content : null;
  return (
    <div
      role="dialog"
      aria-label="open beside"
      data-desk-typing=""
      className="desk-whichkey"
      style={{ top: 48, bottom: "auto", width: 460 }}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          event.stopPropagation();
          onClose();
        }
      }}
    >
      <div className="wkh">open beside</div>
      <input
        autoFocus
        aria-label="find a source"
        placeholder="a source by its title…"
        value={filter}
        onChange={(event) => setFilter(event.target.value)}
        style={{ width: "100%", boxSizing: "border-box", font: "12px var(--desk-mono)", background: "#1d1d21", color: "var(--desk-t)", border: "1px solid var(--desk-line2)", borderRadius: 4, padding: "4px 8px", marginBottom: 8 }}
      />
      <div style={{ maxHeight: 280, overflowY: "auto" }}>
        {book ? (
          <div style={{ marginBottom: 8 }}>
            <div className="wkt">for {focusTitle}</div>
            {(["guide", "notes", "path"] as const).map((panel) => (
              <div key={panel} className="wkr">
                <span />
                <button type="button" style={{ textAlign: "left" }} onClick={() => onOpen({ kind: "panel", panel, extractionId: book.extractionId })}>
                  ◇ {PANEL_TITLES[panel]}
                </button>
              </div>
            ))}
          </div>
        ) : null}
        <div className="wkt">the library</div>
        <div className="wkr"><span /><button type="button" style={{ textAlign: "left" }} onClick={() => onOpen({ kind: "panel", panel: "library" })}>◇ ask across the library</button></div>
        <div className="wkr"><span /><button type="button" style={{ textAlign: "left" }} onClick={() => onOpen(filter.trim() ? { kind: "compare", query: filter.trim() } : { kind: "panel", panel: "library" })}>⇄ compare{filter.trim() ? ` “${filter.trim()}”` : ""}</button></div>
        <div className="wkt" style={{ marginTop: 8 }}>sources</div>
        {library === null ? <div className="desk-quiet">◐ reading the library…</div> : null}
        {sources.map((card) => (
          <div key={card.sourceId} className="wkr">
            <span title={isVideoCard(card) ? "Video" : "Book"}>{isVideoCard(card) ? "▶" : "§"}</span>
            <button type="button" style={{ textAlign: "left" }} onClick={() => onOpenCard(card)}>{card.title}</button>
          </div>
        ))}
      </div>
    </div>
  );
}
