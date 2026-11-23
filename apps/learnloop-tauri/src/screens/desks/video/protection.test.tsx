// A due check's protection on the video desks (spec §12.6.1, decision D15): follow-along and the chapters RPCs mask what
// a due check covers on the server (curriculum.goal_lens). This checks the client adds nothing back: the chip (linked or
// unlinked) and the chapters panel render no text, title or attribute naming the masked LO; and an answer read before a
// check fell due shows nothing of itself and is asked again.
import { act, cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { FollowAlongDto, VideoChapterDto } from "../../../api/dto";
import { Poller } from "../../../api/poller";
import { DIRECT_HUB, WindowScope } from "../lifecycle";
import { useVideoChapters } from "./ChaptersPanel";
import { VideoDesk, type VideoTransport } from "./desk";
import { FollowChip } from "./FollowChip";
import { chapterTicks } from "./model";

vi.mock("../../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));
afterEach(() => { cleanup(); vi.useRealTimers(); });

const NAME = "Eigenvalues";
const NEUTRAL_LO = "a topic with a cold check due";
const NEUTRAL_SECTION = "a section held until its cold check";
const LAYOUT = { videos: [{ windowId: "w_vid", extractionId: "ext_vid", title: "Matrices, a video" }], books: [{ windowId: "w_book", extractionId: "ext_book", paused: false }] };
const flush = () => act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)); });

/** As reader.follow_along answers while lo_eigen's check is due. */
function masked(over: Partial<FollowAlongDto> = {}): FollowAlongDto {
  return {
    videoExtractionId: "ext_vid", bookExtractionId: "ext_book", t: 25, status: "following",
    section: { sectionId: "v_eigen", title: NEUTRAL_SECTION, t0: 20, t1: 40, held: true },
    chapter: { chapterId: "c1", title: NEUTRAL_SECTION, t0: 20, t1: 40, learningObjectIds: ["lo_eigen"], held: true },
    learningObjects: [{ learningObjectId: "lo_eigen", title: NEUTRAL_LO, held: true,
      sections: [{ sectionId: "ch_eigen", title: NEUTRAL_SECTION, jumpSpanId: "s1", held: true }] }],
    nextCheckDue: null, ...over,
  };
}

function maskedChapters(): VideoChapterDto[] {
  return [{ chapterId: "c1", extractionId: "ext_vid", t0: 20, t1: 40, title: NEUTRAL_SECTION, held: true, learningObjectIds: ["lo_eigen"],
    learningObjects: [{ learningObjectId: "lo_eigen", title: NEUTRAL_LO, held: true }], state: "accepted", suggestedAt: "2026-11-23T10:00:00Z", decidedAt: "2026-11-23T10:05:00Z" }];
}

function leaks(name: string): string[] {
  const wanted = name.toLowerCase();
  const found: string[] = [];
  if ((document.body.textContent ?? "").toLowerCase().includes(wanted)) found.push("text");
  for (const element of [document.body, ...document.body.querySelectorAll("*")]) {
    for (const attribute of [...element.attributes]) if (attribute.value.toLowerCase().includes(wanted)) found.push(`${element.tagName}[${attribute.name}]`);
  }
  return found;
}

function Chapters({ transport }: { transport: VideoTransport }) {
  const { side, chapters } = useVideoChapters({ extractionId: "ext_vid", transport, poller: new Poller({ tickMs: 10 }), onChapters: () => undefined });
  return <>{side}<span>{chapterTicks(chapters).map((tick) => <i key={tick.t} title={tick.title} />)}</span></>;
}

describe("a masked LO on the video desks", () => {
  it("is named nowhere in the chip, linked or unlinked, or in the chapters panel and its ticks", async () => {
    const transport = {
      followAlong: vi.fn(async () => masked()),
      chaptersList: vi.fn(async () => ({ extractionId: "ext_vid", chapters: maskedChapters(), nextCheckDue: null })),
    } as unknown as VideoTransport;
    const desk = new VideoDesk(transport, () => undefined);
    desk.setLayout(LAYOUT);
    desk.clock("w_vid", "ext_vid", { t: 25, playing: true, spanId: "c3", duration: 60 });
    await flush();
    render(<div><FollowChip desk={desk} windowId="w_book" /><WindowScope lifecycle={{ windowId: "w_vid", state: "active" }} hub={DIRECT_HUB}><Chapters transport={transport} /></WindowScope></div>);
    await flush();
    expect(document.querySelector("[data-follow='following']")!.textContent).toContain(NEUTRAL_SECTION);
    expect(leaks(NAME)).toEqual([]);
    act(() => desk.toggle("w_book"));
    expect(document.querySelector("[data-follow='unlinked']")).toBeTruthy();
    expect(leaks(NAME)).toEqual([]);
  });

  it("shows nothing of an answer read before a check fell due, unlinked included, and asks again", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const due = new Date(Date.now() + 60_000).toISOString();
    let calls = 0;
    const transport = {
      followAlong: vi.fn(async () => { calls += 1; return calls === 1
        ? masked({ section: { sectionId: "v_eigen", title: "eigenvalues by hand", t0: 20, t1: 40 },
          chapter: { chapterId: "c1", title: "the spectrum", t0: 20, t1: 40 }, nextCheckDue: due })
        : masked(); }),
    } as unknown as VideoTransport;
    const desk = new VideoDesk(transport, () => undefined);
    desk.setLayout(LAYOUT);
    desk.clock("w_vid", "ext_vid", { t: 25, playing: true, spanId: "c3", duration: 60 });
    await flush();
    expect(desk.chipFor("w_book")).toMatchObject({ chapter: "the spectrum" });
    act(() => desk.toggle("w_book"));
    vi.setSystemTime(Date.now() + 61_000);
    // Unlinked, nothing is asked; the old chapter is not shown.
    expect(desk.chipFor("w_book")).toEqual({ kind: "unlinked", chapter: "" });
    act(() => desk.toggle("w_book"));
    desk.clock("w_vid", "ext_vid", { t: 26, playing: true, spanId: "c3", duration: 60 });
    await flush();
    expect(calls).toBe(2);
    expect(desk.chipFor("w_book")).toMatchObject({ chapter: NEUTRAL_SECTION });
  });
});
