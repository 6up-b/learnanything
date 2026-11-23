// Video and carried polish (spec §7.4, §7.5, §7.9, §10.12; RD10): the chip's words and which passage a book follows
// (the goal path's primary section first); the desk's follow-along (one ask per section, none from a paused book, a
// scroll only while playing and for a new passage, `u`); the suggested chapters (read once live, judged on the
// learner's ask as a polled job, accept and not this, cancel); the watch panel's ticks, side panel and clock; and a
// carried question beside related passages. No model is called: every transport is a fake.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { ChaptersJobDto, CorrespondentsDto, FollowAlongDto, ReaderRenderBlockDto, VideoChapterDto } from "../../../api/dto";
import { Poller } from "../../../api/poller";
import { YouTubeWatchPanel } from "../../reader/YouTubeWatchPanel";
import { DIRECT_HUB, WindowScope, type WindowState } from "../lifecycle";
import { CarriedRelated, allCarried } from "../carried/related";
import { useVideoChapters } from "./ChaptersPanel";
import { VideoDesk, type VideoTransport } from "./desk";
import { chapterRanges, chapterTicks, chipText, choosePassage, clockWords, timestampLine } from "./model";

vi.mock("../../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

function follow(over: Partial<FollowAlongDto> = {}): FollowAlongDto {
  return {
    videoExtractionId: "ext_vid", bookExtractionId: "ext_book", t: 25, status: "following",
    section: { sectionId: "v_eigen", title: "1:00–2:00", t0: 20, t1: 40 }, chapter: null,
    learningObjects: [
      { learningObjectId: "lo_a", title: "A", sections: [{ sectionId: "sec_a", title: "2 Eigen", jumpSpanId: "s_a" }] },
      { learningObjectId: "lo_b", title: "B", sections: [{ sectionId: "sec_b", title: "3 Spectra", jumpSpanId: "s_b" }] },
    ],
    ...over,
  };
}

function chapter(id: string, state: VideoChapterDto["state"], t0: number, t1: number, title = id): VideoChapterDto {
  return { chapterId: id, extractionId: "ext_vid", t0, t1, title, learningObjectIds: ["lo_a"], learningObjects: [{ learningObjectId: "lo_a", title: "Eigenvalues" }],
    state, suggestedAt: "2026-11-23T10:00:00Z", decidedAt: state === "suggested" ? null : "2026-11-23T10:05:00Z" };
}

describe("the follow-along words", () => {
  it("reads the chip, prefers the goal path's primary section and says no passage where there is none", () => {
    expect(clockWords(83)).toBe("1:23");
    expect(clockWords(3725)).toBe("1:02:05");
    expect(choosePassage(follow(), "ext_book", () => null)?.spanId).toBe("s_a");
    expect(choosePassage(follow(), "ext_book", (lo) => (lo === "lo_b" ? { extractionId: "ext_book", sectionId: "sec_b" } : null))?.spanId).toBe("s_b");
    // A primary section in another book is not this book's.
    expect(choosePassage(follow(), "ext_book", () => ({ extractionId: "ext_other", sectionId: "sec_b" }))?.spanId).toBe("s_a");
    expect(choosePassage(follow({ status: "no_passage", learningObjects: [] }), "ext_book", () => null)).toBeNull();
    expect(chipText({ kind: "following", chapter: "softmax", t: 83, passage: "2 Eigen" })).toBe("following ▶ softmax 1:23 · 2 Eigen");
    expect(chipText({ kind: "no_passage", chapter: "softmax", t: 83 })).toBe("following ▶ softmax 1:23 · no passage here");
    expect(chipText({ kind: "unlinked", chapter: "softmax" })).toBe("unlinked · u to follow ▶ softmax");
    expect(timestampLine("Softmax by hand", 72)).toBe("▶ Softmax by hand at 1:12");
  });

  it("ticks and ranges only accepted chapters", () => {
    const list = [chapter("c1", "accepted", 20, 40, "eigen"), chapter("c2", "suggested", 40, 60)];
    expect(chapterTicks(list)).toEqual([{ t: 20, title: "eigen" }]);
    expect(chapterRanges(list, 80)).toEqual([{ start: 0.25, end: 0.5 }]);
    expect(chapterRanges(list, 0)).toEqual([]);
  });
});

function videoTransport(answer: (input: { t: number; bookExtractionId: string }) => FollowAlongDto = () => follow()) {
  const asked: Array<{ t: number; bookExtractionId: string }> = [];
  const transport = {
    followAlong: vi.fn(async (input: { extractionId: string; t: number; bookExtractionId: string }) => { asked.push(input); return answer(input); }),
  } as unknown as VideoTransport;
  return { transport, asked };
}

const flush = () => act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)); });
const LAYOUT = { videos: [{ windowId: "w_vid", extractionId: "ext_vid", title: "Matrices" }], books: [{ windowId: "w_book", extractionId: "ext_book", paused: false }] };

describe("the desk's follow-along", () => {
  it("asks once per section, scrolls the book only while playing and for a new passage, and u unlinks it", async () => {
    const { transport, asked } = videoTransport((input) => (input.t < 40 ? follow({ t: input.t }) : follow({ t: input.t, section: { sectionId: "v_det", title: "2:00–3:00", t0: 40, t1: 60 },
      learningObjects: [{ learningObjectId: "lo_b", title: "B", sections: [{ sectionId: "sec_b", title: "3 Spectra", jumpSpanId: "s_b" }] }] })));
    const followed: Array<[string, string]> = [];
    const desk = new VideoDesk(transport, (windowId, spanId) => followed.push([windowId, spanId]));
    desk.setLayout(LAYOUT);
    // Before the player has said anything: where the video is.
    expect(chipText(desk.chipFor("w_book")!)).toBe("following ▶ 0:00");
    desk.clock("w_vid", "ext_vid", { t: 21, playing: false, spanId: "c3", duration: 60 });
    await flush();
    expect(asked.map((input) => input.t)).toEqual([21]);
    // Marked, not scrolled: the video is not playing.
    expect(desk.followedSpan("w_book")).toBe("s_a");
    expect(followed).toEqual([]);
    expect(chipText(desk.chipFor("w_book")!)).toBe("following ▶ 1:00–2:00 0:21 · 2 Eigen");
    // Inside the section nothing is asked again; playing on into the next one asks once and scrolls there.
    desk.clock("w_vid", "ext_vid", { t: 30, playing: true, spanId: "c3", duration: 60 });
    desk.clock("w_vid", "ext_vid", { t: 39, playing: true, spanId: "c4", duration: 60 });
    await flush();
    expect(asked.map((input) => input.t)).toEqual([21]);
    desk.clock("w_vid", "ext_vid", { t: 41, playing: true, spanId: "c5", duration: 60 });
    await flush();
    expect(asked.map((input) => input.t)).toEqual([21, 41]);
    expect(followed).toEqual([["w_book", "s_b"]]);
    // u: unlinked, no mark, the chip says how to follow again; u again goes back to the passage at once.
    desk.toggle("w_book");
    expect(desk.followedSpan("w_book")).toBeNull();
    expect(chipText(desk.chipFor("w_book")!)).toBe("unlinked · u to follow ▶ 2:00–3:00");
    desk.toggle("w_book");
    expect(followed).toEqual([["w_book", "s_b"], ["w_book", "s_b"]]);
  });

  it("a paused book asks nothing; a desk with no video shows no chip; no passage scrolls nothing", async () => {
    const { transport, asked } = videoTransport(() => follow({ status: "no_passage", learningObjects: [] }));
    const followed: string[] = [];
    const desk = new VideoDesk(transport, (_windowId, spanId) => followed.push(spanId));
    desk.setLayout({ ...LAYOUT, books: [{ windowId: "w_book", extractionId: "ext_book", paused: true }] });
    desk.clock("w_vid", "ext_vid", { t: 25, playing: true, spanId: "c3", duration: 60 });
    await flush();
    expect(asked).toEqual([]);
    desk.setLayout(LAYOUT);
    await flush();
    expect(asked.map((input) => input.t)).toEqual([25]);
    expect(chipText(desk.chipFor("w_book")!)).toBe("following ▶ 1:00–2:00 0:25 · no passage here");
    expect(followed).toEqual([]);
    desk.setLayout({ videos: [], books: LAYOUT.books });
    expect(desk.chipFor("w_book")).toBeNull();
  });

  it("an accepted chapter ranges the minimap and is named by the chip once asked again", async () => {
    const { transport, asked } = videoTransport((input) => follow({ t: input.t, chapter: asked.length > 1 ? { chapterId: "c1", title: "eigen", t0: 20, t1: 40 } : null }));
    const desk = new VideoDesk(transport, () => undefined);
    desk.setLayout(LAYOUT);
    desk.clock("w_vid", "ext_vid", { t: 25, playing: false, spanId: "c3", duration: 80 });
    await flush();
    desk.chapters("ext_vid", [chapter("c1", "accepted", 20, 40, "eigen")]);
    await flush();
    expect(desk.rangesFor("ext_vid")).toEqual([{ start: 0.25, end: 0.5 }]);
    expect(asked.length).toBe(2);
    expect(chipText(desk.chipFor("w_book")!)).toBe("following ▶ eigen 0:25 · 2 Eigen");
  });
});

function chaptersTransport(stored: VideoChapterDto[] = []) {
  const jobs: ChaptersJobDto[] = [];
  const transport = {
    chaptersList: vi.fn(async () => ({ extractionId: "ext_vid", chapters: stored })),
    chaptersSuggest: vi.fn(async () => ({ jobId: "vch_1", status: "running", done: false, result: null, error: null }) as ChaptersJobDto),
    chaptersJob: vi.fn(async () => jobs.shift() ?? ({ jobId: "vch_1", status: "running", done: false, result: null, error: null } as ChaptersJobDto)),
    chaptersCancel: vi.fn(async () => ({ jobId: "vch_1", status: "cancelled", done: true, result: null, error: null }) as ChaptersJobDto),
    chaptersDecide: vi.fn(async (input: { chapterId: string; decision: "accept" | "dismiss" }) => ({
      chapter: { ...chapter(input.chapterId, input.decision === "accept" ? "accepted" : "dismissed", 0, 20) } })),
  } as unknown as VideoTransport;
  return { transport, jobs };
}

function Chapters({ transport, poller, onChapters }: { transport: VideoTransport; poller: Poller; onChapters: (list: VideoChapterDto[]) => void }) {
  const { side } = useVideoChapters({ extractionId: "ext_vid", transport, poller, onChapters });
  return <>{side}</>;
}

function mountChapters(state: WindowState, transport: VideoTransport) {
  const poller = new Poller({ tickMs: 10 });
  const seen: VideoChapterDto[][] = [];
  const ui = (now: WindowState) => (
    <WindowScope lifecycle={{ windowId: "w_vid", state: now }} hub={DIRECT_HUB}>
      <Chapters transport={transport} poller={poller} onChapters={(list) => seen.push(list)} />
    </WindowScope>
  );
  const view = render(ui(state));
  return { poller, seen, rerender: (now: WindowState) => view.rerender(ui(now)) };
}

describe("the suggested chapters", () => {
  it("are read once the window is live; judged on the learner's ask as a polled job; accept and not this decide once", async () => {
    const { transport, jobs } = chaptersTransport();
    const { seen, rerender } = mountChapters("hidden", transport);
    await flush();
    expect(transport.chaptersList).not.toHaveBeenCalled();
    rerender("active");
    await screen.findByText("suggest from the transcript");
    expect(transport.chaptersSuggest).not.toHaveBeenCalled();
    jobs.push({ jobId: "vch_1", status: "done", done: true, error: null,
      result: { status: "ready", reason: null, message: null, chapters: [chapter("c1", "suggested", 0, 20, "intro"), chapter("c2", "suggested", 20, 40, "eigenvalues")] } });
    fireEvent.click(screen.getByText("suggest from the transcript"));
    await screen.findByText(/judging the transcript/);
    await screen.findByText("eigenvalues");
    expect(screen.getByText("0:20–0:40")).toBeTruthy();
    expect(screen.getAllByText("◇ Eigenvalues", { exact: false }).length).toBe(2);
    const row = document.querySelector('[data-chapter="c2"]') as HTMLElement;
    fireEvent.click(within(row).getByText("accept"));
    await waitFor(() => expect(document.querySelector('[data-chapter="c2"]')?.textContent).toContain("✓ accepted"));
    expect(transport.chaptersDecide).toHaveBeenCalledWith({ chapterId: "c2", decision: "accept" });
    expect(seen[seen.length - 1].find((each) => each.chapterId === "c2")?.state).toBe("accepted");
    fireEvent.click(within(document.querySelector('[data-chapter="c1"]') as HTMLElement).getByText("not this"));
    await waitFor(() => expect(document.querySelector('[data-chapter="c1"]')).toBeNull());
  });

  it("a running suggestion can be cancelled, and nothing is kept", async () => {
    const { transport } = chaptersTransport([chapter("c9", "accepted", 0, 20, "kept")]);
    mountChapters("active", transport);
    fireEvent.click(await screen.findByText("suggest from the transcript"));
    fireEvent.click(await screen.findByText("cancel"));
    await screen.findByText("cancelled · nothing was kept");
    expect(transport.chaptersCancel).toHaveBeenCalledWith({ jobId: "vch_1" });
    expect(screen.getByText("kept")).toBeTruthy();
  });
});

describe("the watch panel's video extras", () => {
  function cue(id: string, start: number, end: number): ReaderRenderBlockDto {
    return { displayNodeId: `node-${id}`, spanId: id, blockType: "Text", extractorBlockId: `t=${start}-${end}`, markdown: `cue ${id}`,
      sanitized: false, katexNodes: [], assets: [], health: { status: "ok", recommendedView: "derived", reasonFlags: [] } } as ReaderRenderBlockDto;
  }

  it("draws accepted chapters' ticks, the side panel, and hands the clock with its cue to the desk", () => {
    const clocks: Array<{ t: number; playing: boolean; spanId: string | null; duration: number }> = [];
    render(
      <WindowScope lifecycle={{ windowId: "w_vid", state: "active" }} hub={DIRECT_HUB}>
        <YouTubeWatchPanel plan={{ sourceId: "src", videoId: "v", embedUrl: "https://www.youtube-nocookie.com/embed/v?enablejsapi=1", pausePoints: [] }}
          blocks={[cue("c1", 0, 30), cue("c2", 30, 120)]} annotatedSpans={new Set()} guidanceSpans={new Set()} resumeSpan={null}
          findShortcutEnabled={false} onPlaybackSpan={() => undefined} onSeek={() => undefined} onAskSpan={() => undefined} onTagMenu={() => undefined}
          video={{ ticks: [{ t: 30, title: "eigen" }], side: <div data-testid="side">chapters here</div>, onClock: (clock) => clocks.push(clock) }} />
      </WindowScope>,
    );
    const tick = document.querySelector("[data-chapter-tick='30']") as HTMLElement;
    expect(tick.style.left).toBe("25%");
    expect(screen.getByTestId("side").closest(".watch-side")).toBeTruthy();
    // Nothing before the player says where it is; then its time, whether it plays and the cue there.
    expect(clocks).toEqual([]);
    const frame = screen.getByTitle("watch v") as HTMLIFrameElement;
    act(() => {
      window.dispatchEvent(new MessageEvent("message", { origin: "https://www.youtube-nocookie.com", source: frame.contentWindow,
        data: JSON.stringify({ event: "infoDelivery", info: { currentTime: 40, playerState: 1 } }) }));
    });
    expect(clocks[clocks.length - 1]).toEqual({ t: 40, playing: true, spanId: "c2", duration: 120 });
  });
});

describe("a carried question beside related passages", () => {
  const question = { carriedId: "cq1", text: "why e?", originKind: "selection", originRef: null, anchor: { extraction_id: "ext_book", span_id: "b3" },
    deskId: null, since: "2026-11-21T10:00:00Z", state: "carried", carried: true, version: 1, updatedAt: "2026-11-21T10:00:00Z" } as never;

  it("comes back at the judged correspondents' passages in the other open readings, read once", async () => {
    const correspondents = vi.fn(async () => ({ extractionId: "ext_book", sectionId: "sec_b", status: "judged", search: null, checkableLearningObjectIds: [],
      learningObjects: [{ learningObjectId: "lo_a", title: "A", sources: [{ sourceId: "src_vid", sourceTitle: "V", sections: [
        { extractionId: "ext_vid", sectionId: "v_eigen", title: "1:00–2:00", sourceId: "src_vid", sourceTitle: "V", read: false, jump: { extractionId: "ext_vid", sectionId: "v_eigen", spanId: "c3" }, treatment: "develops", by: "judge" }] }] }] }) as unknown as CorrespondentsDto);
    const passageUnionRange = vi.fn(async () => ({ version: 1, extractionId: "ext_book", spans: [{ spanId: "b3", sectionId: "sec_b" }], sections: [] }) as never);
    const related = new CarriedRelated({ passageUnionRange, correspondents });
    expect(related.beside([question], ["ext_book"])).toEqual([]);
    expect(passageUnionRange).not.toHaveBeenCalled();
    expect(related.beside([question], ["ext_book", "ext_vid"])).toEqual([]);
    await flush();
    const beside = related.beside([question], ["ext_book", "ext_vid"]);
    expect(beside.map((each) => each.anchor)).toEqual([{ extraction_id: "ext_vid", span_id: "c3", related: true }]);
    expect(correspondents).toHaveBeenCalledWith({ extractionId: "ext_book", sectionId: "sec_b", searchFallback: false });
    related.beside([question], ["ext_book", "ext_vid"]);
    expect(passageUnionRange).toHaveBeenCalledTimes(1);
    // A question let go comes back nowhere.
    expect(related.beside([{ ...(question as object), carried: false } as never], ["ext_book", "ext_vid"])).toEqual([]);
  });

  it("reads every page of the carried questions", async () => {
    const pages: Record<string, { carried: never[]; cursor: string | null }> = {
      "": { carried: [question], cursor: "p2" }, p2: { carried: [{ ...(question as object), carriedId: "cq2" } as never], cursor: null } };
    const all = await allCarried(async (cursor) => pages[cursor ?? ""]);
    expect(all.map((each) => each.carriedId)).toEqual(["cq1", "cq2"]);
  });
});
