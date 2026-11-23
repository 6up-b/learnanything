// What lesson windows need from the desks (spec §11.1): the lessons' summaries (their tabs and the path view's rows),
// the openings in flight, where a stack should scroll to, and the shell's ways to open a lesson. DeskShell provides
// it through the pads host (a lesson is a tab of a pad stack); tests provide fakes.
import type { ReactNode } from "react";
import { api } from "../../../api/client";
import type { LessonSummaryDto, LessonViewDto } from "../../../api/dto";
import type { LessonEntry } from "../../LessonView";
import { OPENING_KEY, lessonKey, lessonOfKey } from "./model";

export interface LessonsTransport {
  list(input: { lessonIds?: string[]; learningObjectIds?: string[] }): Promise<{ lessons: LessonSummaryDto[] }>;
}

export const LIVE_LESSONS_TRANSPORT: LessonsTransport = {
  list: (input) => api.lessonList(input),
};

/** A lesson being opened into a stack: its opening turn has not returned the lesson's id yet. */
export interface Opening {
  key: string;
  windowId: string;
  entry: LessonEntry;
  lessonId: string | null;
}

/** The desks' lessons, as an external store (useSyncExternalStore): summaries read once per lesson (a batch per
 * tick), openings, aliases and reveals. No lesson is ever opened from here: a window's LessonView does that. */
export class LessonDesk {
  private summaries = new Map<string, LessonSummaryDto>();
  private asked = new Set<string>();
  private queued = new Set<string>();
  private openings: Opening[] = [];
  private openingCount = 0;
  /** An opened lesson keeps its opening's React key and entry, so the window that opened it is not remounted (its
   * waiting line, a retry after an outage and its words in flight stay where they are). */
  private aliases = new Map<string, Opening>();
  private reveals = new Map<string, string>();
  private additions = new Map<string, string>();
  private all: LessonSummaryDto[] | null = null;
  private allAsked = false;
  private listeners = new Set<() => void>();
  private version = 0;

  constructor(private readonly transport: LessonsTransport, private readonly onOpened: (opening: Opening, lessonId: string) => void) {}

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  getVersion = (): number => this.version;

  private emit(): void {
    this.version += 1;
    for (const listener of this.listeners) listener();
  }

  /** A lesson's summary, read on first ask (null until it lands, or when lessons are off). */
  summary(lessonId: string): LessonSummaryDto | null {
    const known = this.summaries.get(lessonId);
    if (known) return known;
    if (!this.asked.has(lessonId)) this.request([lessonId]);
    return null;
  }

  /** Read these lessons' summaries again (a lesson just closed: its tab and modes change). */
  refresh(lessonId: string): void {
    this.asked.delete(lessonId);
    this.all = null;
    this.allAsked = false;
    this.request([lessonId]);
  }

  private request(lessonIds: string[]): void {
    const fresh = lessonIds.filter((id) => !this.asked.has(id));
    if (!fresh.length) return;
    for (const id of fresh) {
      this.asked.add(id);
      this.queued.add(id);
    }
    // One read for every tab that asked in this tick.
    queueMicrotask(() => {
      const wanted = [...this.queued];
      this.queued.clear();
      if (!wanted.length) return;
      // A transport that throws instead of rejecting (no sidecar) is a failed read too.
      void Promise.resolve().then(() => this.transport.list({ lessonIds: wanted })).then(
        (result) => this.learn(result.lessons),
        () => undefined,
      );
    });
  }

  private learn(lessons: LessonSummaryDto[]): void {
    for (const lesson of lessons) {
      this.summaries.set(lesson.lessonId, lesson);
      if (lesson.additionsPadId && !this.additions.has(lesson.lessonId)) this.additions.set(lesson.lessonId, lesson.additionsPadId);
    }
    this.emit();
  }

  /** Every lesson (the path view's Teacher lesson rows), read once per path opening; null until it lands. */
  allLessons(): LessonSummaryDto[] | null {
    if (!this.allAsked) {
      this.allAsked = true;
      void Promise.resolve().then(() => this.transport.list({})).then(
        (result) => {
          this.all = result.lessons;
          this.learn(result.lessons);
        },
        () => undefined,
      );
    }
    return this.all;
  }

  /** Forget the list of every lesson, so the next path opening reads it again. */
  forgetAll(): void {
    this.all = null;
    this.allAsked = false;
  }

  /** A lesson's newest summary, preferring what its window just showed (a view is fresher than the list). */
  noteView(lessonId: string, view: LessonViewDto): void {
    const known = this.summaries.get(lessonId);
    if (known && known.closed !== view.closed) this.refresh(lessonId);
  }

  // -- openings ------------------------------------------------------------------------------------

  /** A lesson to open into a stack window: shown there at once, stored once its opening returns an id. */
  open(windowId: string, entry: LessonEntry): string {
    this.openingCount += 1;
    const key = `${OPENING_KEY}${this.openingCount}`;
    this.openings = [...this.openings, { key, windowId, entry, lessonId: null }];
    this.reveals.set(windowId, key);
    this.emit();
    return key;
  }

  /** The items a stack window shows for its openings: an opening's key until its turn returns, then its lesson's
   * (so the tab never drops out while the shell's add_to_stack is on its way; the stack's own entry dedups it). */
  openingsFor(windowId: string): string[] {
    return this.openings.filter((opening) => opening.windowId === windowId).map((opening) => (opening.lessonId ? lessonKey(opening.lessonId) : opening.key));
  }

  /** The stack now holds these lessons itself: their openings are done. */
  landed(windowId: string, lessonIds: readonly string[]): void {
    const before = this.openings.length;
    this.openings = this.openings.filter((opening) => opening.windowId !== windowId || !opening.lessonId || !lessonIds.includes(opening.lessonId));
    if (this.openings.length !== before) this.emit();
  }

  /** The opening's turn returned its lesson: the shell stores it in the stack (add_to_stack), and its tab keeps its
   * React key. A second view of the same opening changes nothing. */
  opened(key: string, lessonId: string): void {
    const opening = this.openings.find((each) => each.key === key);
    if (!opening || opening.lessonId !== null) return;
    opening.lessonId = lessonId;
    this.aliases.set(lessonId, opening);
    if (this.reveals.get(opening.windowId) === key) this.reveals.set(opening.windowId, lessonKey(lessonId));
    this.onOpened(opening, lessonId);
    this.emit();
  }

  /** An opening the learner gave up on (its window closed, or the opening failed before saving anything). */
  dropOpening(key: string): void {
    const before = this.openings.length;
    this.openings = this.openings.filter((opening) => opening.key !== key);
    if (this.openings.length !== before) this.emit();
  }

  /** The entry a stack item's lesson is shown with: an opening's until its lesson exists, then a resume of the
   * stored lesson. The window that opened it goes on (its entry was read once, at mount); any later mount of the tab
   * (another desk visited, the shell back) reads the lesson, and never opens it a second time. */
  entryFor(key: string): LessonEntry | null {
    const lessonId = lessonOfKey(key);
    if (lessonId) return { kind: "resume", lessonId };
    return this.openings.find((opening) => opening.key === key)?.entry ?? null;
  }

  /** The React key a stack item renders under (an opened lesson keeps its opening's). */
  reactKey(key: string): string {
    const lessonId = lessonOfKey(key);
    return (lessonId && this.aliases.get(lessonId)?.key) || key;
  }

  /** The title an opening's tab shows before its lesson exists. */
  openingTitle(key: string): string | null {
    const entry = this.openings.find((opening) => opening.key === key)?.entry;
    if (!entry || entry.kind !== "open") return null;
    return entry.title ?? (entry.entry === "reader_selection" ? "your selection" : null);
  }

  // -- reveals and additions ------------------------------------------------------------------------

  /** Scroll a stack to one of its items once it shows it. */
  reveal(windowId: string, key: string): void {
    this.reveals.set(windowId, key);
    this.emit();
  }

  /** The item a stack should scroll to, taken once it is there. */
  takeReveal(windowId: string, keys: readonly string[]): string | null {
    const key = this.reveals.get(windowId);
    if (!key || !keys.includes(key)) return null;
    this.reveals.delete(windowId);
    return key;
  }

  /** A lesson's additions pad (the one the list named, or the one created here). */
  additionsFor(lessonId: string): string | null {
    return this.additions.get(lessonId) ?? null;
  }

  noteAdditions(lessonId: string, padId: string): void {
    if (this.additions.get(lessonId) === padId) return;
    this.additions.set(lessonId, padId);
    this.emit();
  }
}

/** What a stack's lesson tabs and the path view ask of the desks. */
export interface LessonsHost {
  desk: LessonDesk;
  onError: (message: string) => void;
  /** The existing quick check over a lesson's topics. */
  onQuickCheck?: (learningObjectIds: string[]) => void;
  /** A typed goal's "Look in my library". */
  onLookInLibrary?: (phrase: string) => void;
  /** Open a lesson in a window on the current desk (a fresh lesson after a protection change, the path view's row). */
  openLesson: (entry: LessonEntry) => void;
  /** RD9b's notebook frame for a lesson whose medium is a notebook; absent until it is built. */
  notebookFrame?: (lessonId: string, view: LessonViewDto) => ReactNode;
}
