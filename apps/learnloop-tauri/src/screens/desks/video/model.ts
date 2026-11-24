// Video and carried polish (spec §7.4, §7.5, §7.9; RD10), the pure part: the follow chip's words, which correspondent
// passage a book follows (the goal path's primary section first), the scrub track's chapter ticks and the minimap's
// ranges, and the timestamp line.
import type { FollowAlongDto, VideoChapterDto } from "../../../api/dto";

/** m:ss (h:mm:ss past the hour), as the player's own line reads. */
export function clockWords(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const rest = String(s % 60).padStart(2, "0");
  return h ? `${h}:${String(m).padStart(2, "0")}:${rest}` : `${m}:${rest}`;
}

export interface FollowedPassage {
  learningObjectId: string;
  sectionId: string;
  title: string | null;
  spanId: string;
}

/** The passage a book follows for the playing cue's section: among its LOs' correspondent sections in the book, the
 * goal path's primary section where one is (spec §7.5 step 3), else the first judged one. None without a landing. */
export function choosePassage(result: FollowAlongDto | null, bookExtractionId: string,
                              primaryFor: (learningObjectId: string) => { extractionId: string; sectionId: string } | null): FollowedPassage | null {
  if (!result || result.status !== "following") return null;
  const candidates = result.learningObjects.flatMap((group) => group.sections
    .filter((section) => section.jumpSpanId)
    .map((section) => ({ learningObjectId: group.learningObjectId, sectionId: section.sectionId, title: section.title, spanId: section.jumpSpanId as string })));
  const primary = candidates.find((candidate) => {
    const path = primaryFor(candidate.learningObjectId);
    return path !== null && path.extractionId === bookExtractionId && path.sectionId === candidate.sectionId;
  });
  return primary ?? candidates[0] ?? null;
}

export function chapterLabel(chapter: { title: string; t0: number; held?: boolean }): string {
  return chapter.held ? `Chapter at ${clockWords(chapter.t0)}` : chapter.title;
}

/** The chapter a chip names: the accepted chapter the time falls in, else the transcript section's label. */
export function chapterWords(result: FollowAlongDto | null): string {
  return result?.chapter ? chapterLabel(result.chapter) : result?.section?.title ?? "";
}

export type FollowChipState =
  | { kind: "following"; chapter: string; t: number; passage: string }
  | { kind: "no_passage"; chapter: string; t: number }
  | { kind: "unlinked"; chapter: string }
  | { kind: "waiting"; t: number };

/** "following ▶ <chapter> <time> · <passage label>", "… · no passage here", "unlinked · u to follow ▶ <chapter>". */
export function chipText(state: FollowChipState): string {
  switch (state.kind) {
    case "following":
      return `following ▶ ${state.chapter ? `${state.chapter} ` : ""}${clockWords(state.t)} · ${state.passage}`;
    case "no_passage":
      return `following ▶ ${state.chapter ? `${state.chapter} ` : ""}${clockWords(state.t)} · no passage here`;
    case "unlinked":
      return `unlinked · u to follow ▶${state.chapter ? ` ${state.chapter}` : ""}`;
    case "waiting":
      return `Looking for a passage at ▶ ${clockWords(state.t)}…`;
  }
}

/** Accepted chapters' ticks on the scrub track (their starts). */
export function chapterTicks(chapters: readonly VideoChapterDto[]): Array<{ t: number; title: string }> {
  return chapters.filter((chapter) => chapter.state === "accepted").map((chapter) => ({ t: chapter.t0, title: chapterLabel(chapter) }));
}

/** Accepted chapters' ranges on the shelf row's minimap, as fractions of the video's length. */
export function chapterRanges(chapters: readonly VideoChapterDto[], duration: number): Array<{ start: number; end: number }> {
  if (!(duration > 0)) return [];
  return chapters.filter((chapter) => chapter.state === "accepted")
    .map((chapter) => ({ start: Math.max(0, chapter.t0 / duration), end: Math.min(1, chapter.t1 / duration) }));
}

/** The timestamp key's line (spec §7.4): "▶ <video> at m:ss". */
export function timestampLine(videoTitle: string, t: number): string {
  return `▶ ${videoTitle} at ${clockWords(t)}`;
}
