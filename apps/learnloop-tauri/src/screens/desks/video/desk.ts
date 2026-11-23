// The desks' videos (spec §7.4, §7.5, §7.9; RD10), as an external store (useSyncExternalStore): each video window's
// clock, what each book window follows (follow-along), which books the learner unlinked (`u`), and each video's
// accepted chapters (the scrub track's ticks, the shelf row's minimap).
//
// Follow-along asks `reader.follow_along` once per transcript section the playing video enters, per book window
// that is not paused (the answer carries the section's time bounds; the clock moving inside them asks nothing). The
// book marks the passage whatever the player does, and scrolls to it only while the video plays and the passage
// changed. A paused book asks nothing; on screen again, it asks for where the video is then.
import { api } from "../../../api/client";
import type { ChaptersJobDto, CorrespondentsDto, FollowAlongDto, VideoChapterDto } from "../../../api/dto";
import { chapterRanges, chapterWords, choosePassage, type FollowChipState, type FollowedPassage } from "./model";

export interface VideoTransport {
  followAlong(input: { extractionId: string; t: number; bookExtractionId: string }): Promise<FollowAlongDto>;
  chaptersList(input: { extractionId: string }): Promise<{ extractionId: string; chapters: VideoChapterDto[]; nextCheckDue?: string | null }>;
  chaptersSuggest(input: { extractionId: string }): Promise<ChaptersJobDto>;
  chaptersJob(input: { jobId: string }): Promise<ChaptersJobDto>;
  chaptersCancel(input: { jobId: string }): Promise<ChaptersJobDto>;
  chaptersDecide(input: { chapterId: string; decision: "accept" | "dismiss" }): Promise<{ chapter: VideoChapterDto }>;
  /** Judged correspondents (carried questions beside related passages). */
  correspondents(input: { extractionId: string; sectionId: string; searchFallback: boolean }): Promise<CorrespondentsDto>;
}

export const LIVE_VIDEO_TRANSPORT: VideoTransport = {
  followAlong: (input) => api.readerFollowAlong(input),
  chaptersList: (input) => api.chaptersList(input),
  chaptersSuggest: (input) => api.chaptersSuggest(input),
  chaptersJob: (input) => api.chaptersJob(input),
  chaptersCancel: (input) => api.chaptersCancel(input),
  chaptersDecide: (input) => api.chaptersDecide(input),
  correspondents: (input) => api.readerCorrespondents(input),
};

export interface VideoClock {
  t: number;
  playing: boolean;
  spanId: string | null;
  duration: number;
}

/** The current desk's windows as follow-along reads them. */
export interface DeskVideos {
  videos: Array<{ windowId: string; extractionId: string; title: string }>;
  books: Array<{ windowId: string; extractionId: string; paused: boolean }>;
}

interface Followed {
  videoExtractionId: string;
  /** The time it was asked for (an answer whose bounds miss it is not asked again for the same second). */
  askedT: number;
  result: FollowAlongDto;
  passage: FollowedPassage | null;
}

const NO_PRIMARY = () => null;

/** An answer read before a check fell due may name what that check covers: it is not shown, and is asked again. */
export function pastCheck(result: { nextCheckDue?: string | null } | null | undefined, now = Date.now()): boolean {
  const due = result?.nextCheckDue ? Date.parse(result.nextCheckDue) : NaN;
  return !Number.isNaN(due) && now >= due;
}

export class VideoDesk {
  private clocks = new Map<string, VideoClock & { extractionId: string }>();
  private lastPlaying: string | null = null;
  private followed = new Map<string, Followed>();
  private asking = new Set<string>();
  private unlinked = new Set<string>();
  private accepted = new Map<string, VideoChapterDto[]>();
  private durations = new Map<string, number>();
  private layout: DeskVideos = { videos: [], books: [] };
  private primaryFor: (learningObjectId: string) => { extractionId: string; sectionId: string } | null = NO_PRIMARY;
  private listeners = new Set<() => void>();
  private version = 0;

  constructor(private readonly transport: VideoTransport, private readonly onFollow: (bookWindowId: string, spanId: string) => void) {}

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  getVersion = (): number => this.version;

  private emit(): void {
    this.version += 1;
    for (const listener of this.listeners) listener();
  }

  /** The current desk's videos and books (called as the desk renders; unchanged, nothing happens). */
  setLayout(layout: DeskVideos): void {
    const before = JSON.stringify(this.layout);
    if (JSON.stringify(layout) === before) return;
    this.layout = layout;
    this.refresh();
    this.emit();
  }

  /** The goal path's primary section for an LO (the desk's goal band), preferred among correspondents. */
  setPrimary(primaryFor: (learningObjectId: string) => { extractionId: string; sectionId: string } | null): void {
    this.primaryFor = primaryFor;
  }

  /** A video window's player clock. */
  clock(windowId: string, extractionId: string, clock: VideoClock): void {
    const before = this.clocks.get(windowId);
    this.clocks.set(windowId, { ...clock, extractionId });
    if (clock.playing) this.lastPlaying = windowId;
    if (clock.duration > 0 && this.durations.get(extractionId) !== clock.duration) {
      this.durations.set(extractionId, clock.duration);
      this.emit();
    }
    // The chip before any answer shows where the video is; a new play state can start a scroll.
    if (!before || before.playing !== clock.playing || Math.floor(before.t) !== Math.floor(clock.t)) this.refresh();
  }

  clockOf(windowId: string): VideoClock | null {
    return this.clocks.get(windowId) ?? null;
  }

  /** The video follow-along reads: the one that played last on this desk, else its first. */
  driver(): { windowId: string; extractionId: string; title: string } | null {
    return this.layout.videos.find((video) => video.windowId === this.lastPlaying) ?? this.layout.videos[0] ?? null;
  }

  private refresh(): void {
    const driver = this.driver();
    if (!driver) return;
    const clock = this.clocks.get(driver.windowId);
    if (!clock) return;
    for (const book of this.layout.books) {
      if (book.paused || this.unlinked.has(book.windowId) || this.asking.has(book.windowId)) continue;
      const known = this.followed.get(book.windowId);
      const section = known?.result.section;
      const inside = section ? clock.t >= section.t0 && (section.t1 === null || clock.t < section.t1) : known?.result.t !== -1;
      const fresh = known && known.videoExtractionId === driver.extractionId && !pastCheck(known.result)
        && (inside || Math.floor(known.askedT) === Math.floor(clock.t));
      if (fresh) continue;
      this.ask(book.windowId, book.extractionId, driver.extractionId, clock.t);
    }
  }

  private ask(bookWindowId: string, bookExtractionId: string, videoExtractionId: string, t: number): void {
    this.asking.add(bookWindowId);
    void Promise.resolve().then(() => this.transport.followAlong({ extractionId: videoExtractionId, t, bookExtractionId })).then(
      (result) => {
        this.asking.delete(bookWindowId);
        const before = this.followed.get(bookWindowId)?.passage ?? null;
        const passage = choosePassage(result, bookExtractionId, this.primaryFor);
        this.followed.set(bookWindowId, { videoExtractionId, askedT: t, result, passage });
        const driver = this.driver();
        const playing = driver ? this.clocks.get(driver.windowId)?.playing ?? false : false;
        if (passage && passage.spanId !== before?.spanId && playing && !this.unlinked.has(bookWindowId)) this.onFollow(bookWindowId, passage.spanId);
        this.emit();
        // The clock may have left the answered section while it was asked.
        this.refresh();
      },
      () => {
        this.asking.delete(bookWindowId);
      },
    );
  }

  /** `u`: stop following, or follow again (then the book goes to the passage at once). */
  toggle(bookWindowId: string): void {
    if (this.unlinked.delete(bookWindowId)) {
      const passage = this.followed.get(bookWindowId)?.passage;
      if (passage) this.onFollow(bookWindowId, passage.spanId);
      this.refresh();
    } else {
      this.unlinked.add(bookWindowId);
    }
    this.emit();
  }

  /** The chip a book window's head shows (none on a desk with no video). */
  chipFor(bookWindowId: string): FollowChipState | null {
    const driver = this.driver();
    if (!driver || !this.layout.books.some((book) => book.windowId === bookWindowId)) return null;
    const known = this.followed.get(bookWindowId);
    const answered = known && known.videoExtractionId === driver.extractionId ? known.result : null;
    // An answer from before a check fell due shows nothing of itself, linked or not, until it is asked again.
    const result = answered && !pastCheck(answered) ? answered : null;
    const chapter = chapterWords(result);
    if (this.unlinked.has(bookWindowId)) return { kind: "unlinked", chapter };
    if (!result) return { kind: "waiting", t: this.clocks.get(driver.windowId)?.t ?? 0 };
    if (known?.passage) return { kind: "following", chapter, t: result.t, passage: known.passage.title ?? "" };
    return { kind: "no_passage", chapter, t: result.t };
  }

  /** The passage a book window marks (cyan), while it follows. */
  followedSpan(bookWindowId: string): string | null {
    if (this.unlinked.has(bookWindowId)) return null;
    return this.followed.get(bookWindowId)?.passage?.spanId ?? null;
  }

  /** A video's chapters as its window last read them: the accepted ones tick the track and range the minimap, and
   * a chip naming a chapter reads again. */
  chapters(extractionId: string, chapters: VideoChapterDto[]): void {
    const accepted = chapters.filter((chapter) => chapter.state === "accepted");
    const before = this.accepted.get(extractionId) ?? [];
    if (JSON.stringify(before.map((c) => c.chapterId)) === JSON.stringify(accepted.map((c) => c.chapterId))) return;
    this.accepted.set(extractionId, accepted);
    // Asked again (the chapter a chip names may have changed); the passage stays, so nothing scrolls for it.
    for (const [bookWindowId, known] of this.followed) {
      if (known.videoExtractionId === extractionId) this.followed.set(bookWindowId, { ...known, askedT: -1, result: { ...known.result, section: null, t: -1 } });
    }
    this.refresh();
    this.emit();
  }

  /** A video's accepted chapters as ranges of its length (the shelf row's minimap). */
  rangesFor(extractionId: string): Array<{ start: number; end: number }> {
    return chapterRanges(this.accepted.get(extractionId) ?? [], this.durations.get(extractionId) ?? 0);
  }
}
