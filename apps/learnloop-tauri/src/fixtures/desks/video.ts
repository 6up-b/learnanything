// The synthetic workspace's follow-along and suggested chapters (spec §7.5, §7.9; RD10): the fixture video's captions
// fall into six transcript sections, each judged (here, by hand: a fixture, never a model) to treat one of the book's
// sections; follow-along answers as `reader.follow_along` does, and the chapters judge as a polled job that finishes
// on its first poll. On the harness's `?video=1` page three chapters are already suggested and the second accepted,
// as the reference shows them. Every call is recorded. Project-authored text only.
import type { ChaptersJobDto, CorrespondentsDto, FollowAlongDto, VideoChapterDto } from "../../api/dto";
import { FIXTURE_SOURCES } from "./sources";

const { book, paper, video } = FIXTURE_SOURCES;
const CUE_S = 6;

/** The video's transcript sections: [first cue, last cue] (1-based, 6 s each), and the book section each treats. */
const SECTIONS: Array<{ id: string; cues: [number, number]; lo: string; loTitle: string; book: string | null; paper: string | null }> = [
  { id: "v1", cues: [1, 4], lo: "fx_lo_weights", loTitle: "Turn scores into probabilities", book: "s1", paper: null },
  { id: "v2", cues: [5, 9], lo: "fx_lo_gaps", loTitle: "Only score gaps matter", book: "s2", paper: null },
  { id: "v3", cues: [10, 13], lo: "fx_lo_temperature", loTitle: "Interpret sampling temperature", book: "s3", paper: "s2" },
  { id: "v4", cues: [14, 17], lo: "fx_lo_xent", loTitle: "Cross-entropy as minus a log", book: "s4", paper: null },
  { id: "v5", cues: [18, 24], lo: "fx_lo_grad", loTitle: "The gradient of softmax and cross-entropy", book: "s5", paper: null },
  { id: "v6", cues: [25, 32], lo: "fx_lo_stable", loTitle: "Compute softmax without overflow", book: "s6", paper: null },
];
const BOOK_TITLES: Record<string, string> = { s1: "1 Scores into weights", s2: "2 Why the exponential", s3: "3 Temperature", s4: "4 Cross-entropy", s5: "5 The gradient", s6: "6 Computing it safely" };
const PAPER_TITLES: Record<string, string> = { s2: "2 Why divide by the square root" };

function clock(seconds: number): string {
  return `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, "0")}`;
}

function bounds(index: number): { t0: number; t1: number | null } {
  const section = SECTIONS[index];
  return { t0: index === 0 ? 0 : (section.cues[0] - 1) * CUE_S, t1: index + 1 < SECTIONS.length ? (SECTIONS[index + 1].cues[0] - 1) * CUE_S : null };
}

function sectionTitle(index: number): string {
  const section = SECTIONS[index];
  return `${clock((section.cues[0] - 1) * CUE_S)}–${clock(section.cues[1] * CUE_S)}`;
}

function chapter(index: number, title: string, state: VideoChapterDto["state"]): VideoChapterDto {
  const section = SECTIONS[index];
  return {
    chapterId: `fx_ch_${section.id}`, extractionId: video.extractionId, t0: (section.cues[0] - 1) * CUE_S, t1: section.cues[1] * CUE_S, title,
    learningObjectIds: [section.lo], learningObjects: [{ learningObjectId: section.lo, title: section.loTitle }], state,
    suggestedAt: "2026-11-23T09:00:00Z", decidedAt: state === "suggested" ? null : "2026-11-23T09:05:00Z",
  };
}

const SUGGESTED: Array<[number, string]> = [[0, "weights from scores"], [1, "a shift changes nothing"], [2, "temperature"]];

export class FixtureVideo {
  readonly calls: Array<{ command: string; input: unknown }> = [];
  private chapters: VideoChapterDto[];

  constructor(suggested: boolean) {
    this.chapters = suggested ? SUGGESTED.map(([index, title]) => chapter(index, title, index === 1 ? "accepted" : "suggested")) : [];
  }

  follow(input: { extractionId: string; t: number; bookExtractionId: string }): FollowAlongDto {
    this.calls.push({ command: "reader_follow_along", input });
    const out: FollowAlongDto = { videoExtractionId: input.extractionId, bookExtractionId: input.bookExtractionId, t: input.t, status: "no_section", section: null, chapter: null, learningObjects: [] };
    if (input.extractionId !== video.extractionId) return out;
    let index = SECTIONS.findIndex((_section, i) => input.t >= bounds(i).t0 && (bounds(i).t1 === null || input.t < (bounds(i).t1 as number)));
    if (index < 0) index = 0;
    const section = SECTIONS[index];
    out.section = { sectionId: section.id, title: sectionTitle(index), ...bounds(index) };
    const accepted = this.chapters.find((each) => each.state === "accepted" && each.t0 <= input.t && each.t1 >= input.t);
    out.chapter = accepted ? { chapterId: accepted.chapterId, title: accepted.title, t0: accepted.t0, t1: accepted.t1 } : null;
    const target = input.bookExtractionId === book.extractionId ? section.book : input.bookExtractionId === paper.extractionId ? section.paper : null;
    if (!target) {
      out.status = "no_passage";
      return out;
    }
    const titles = input.bookExtractionId === book.extractionId ? BOOK_TITLES : PAPER_TITLES;
    out.status = "following";
    out.learningObjects = [{ learningObjectId: section.lo, title: section.loTitle,
      sections: [{ sectionId: target, title: titles[target], jumpSpanId: `${input.bookExtractionId}_${target}_1` }] }];
    return out;
  }

  list(input: { extractionId: string }): { extractionId: string; chapters: VideoChapterDto[] } {
    this.calls.push({ command: "chapters_list", input });
    return { extractionId: input.extractionId, chapters: input.extractionId === video.extractionId ? this.chapters.filter((each) => each.state !== "dismissed") : [] };
  }

  suggest(input: { extractionId: string }): ChaptersJobDto {
    this.calls.push({ command: "chapters_suggest", input });
    return { jobId: "fx_vch_1", status: "running", done: false, result: null, error: null };
  }

  job(input: { jobId: string }): ChaptersJobDto {
    this.calls.push({ command: "chapters_job", input });
    const decided = new Map(this.chapters.map((each) => [each.chapterId, each]));
    this.chapters = SUGGESTED.map(([index, title]) => decided.get(`fx_ch_${SECTIONS[index].id}`) ?? chapter(index, title, "suggested"));
    return { jobId: input.jobId, status: "done", done: true, error: null, result: { status: "ready", reason: null, message: null, chapters: this.chapters } };
  }

  cancel(input: { jobId: string }): ChaptersJobDto {
    this.calls.push({ command: "chapters_cancel", input });
    return { jobId: input.jobId, status: "cancelled", done: true, result: null, error: null };
  }

  decide(input: { chapterId: string; decision: "accept" | "dismiss" }): { chapter: VideoChapterDto } {
    this.calls.push({ command: "chapters_decide", input });
    const found = this.chapters.find((each) => each.chapterId === input.chapterId);
    if (!found) throw { code: "chapter_not_found", message: `No chapter ${input.chapterId}.` };
    if (found.state === "suggested") Object.assign(found, { state: input.decision === "accept" ? "accepted" : "dismissed", decidedAt: "2026-11-23T10:00:00Z" });
    return { chapter: { ...found } };
  }

  /** Judged correspondents (a carried question beside related passages): a book section's video section. */
  correspondents(input: { extractionId: string; sectionId: string }): CorrespondentsDto {
    this.calls.push({ command: "reader_correspondents", input });
    const index = input.extractionId === book.extractionId ? SECTIONS.findIndex((section) => section.book === input.sectionId) : -1;
    if (index < 0) return { extractionId: input.extractionId, sectionId: input.sectionId, status: "none", learningObjects: [], search: null, checkableLearningObjectIds: [] };
    const section = SECTIONS[index];
    const spanId = `${video.extractionId}_c${section.cues[0]}`;
    return {
      extractionId: input.extractionId, sectionId: input.sectionId, status: "judged", search: null, checkableLearningObjectIds: [],
      learningObjects: [{ learningObjectId: section.lo, title: section.loTitle, sources: [{ sourceId: video.sourceId, sourceTitle: "Softmax by hand (synthetic captions)", sections: [{
        extractionId: video.extractionId, sectionId: section.id, title: sectionTitle(index), sourceId: video.sourceId, sourceTitle: "Softmax by hand (synthetic captions)",
        read: false, jump: { extractionId: video.extractionId, sectionId: section.id, spanId }, treatment: "develops", by: "judge" }] }] }],
    } as CorrespondentsDto;
  }
}
