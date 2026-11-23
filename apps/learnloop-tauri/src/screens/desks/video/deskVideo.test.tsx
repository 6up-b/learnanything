// RD10 on the desks (spec §7.4, §7.5; its acceptance: the following chip and scroll on a fixture with coverage): a book
// beside a playing video shows "following ▶ …" in its head, marks the passage and scrolls to it; `u` unlinks it; and
// `alt+;` stamps "▶ <video> at m:ss" into the current desk's running pad as a quote anchored to the cue. jsdom lays
// nothing out; the harness shows the real webview.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { FollowAlongDto, PadOpDto } from "../../../api/dto";
import { FixtureDeskServer } from "../../../fixtures/desks/workspace";
import { FIXTURE_LIBRARY, FIXTURE_SOURCES } from "../../../fixtures/desks/sources";
import { DeskShell, type CompanionTransport, type DeskTransport, type PadsTransport } from "../DeskShell";
import type { GoalTransport } from "../goal/controller";
import type { VideoTransport } from "./desk";

const jumped: Array<[string, string]> = [];
vi.mock("../../../api/client", () => ({ api: {} }));
// A source window stands in as its title and the props the desks hand it: a video's clock is told through a button,
// and a book's jump is recorded.
vi.mock("../windows/SourceWindow", async () => {
  const { useEffect } = await import("react");
  return {
    SourceWindow: (props: { content: { kind: string; extractionId: string }; lens?: { className?: (span: string, state: object) => string | undefined } | null;
      onJumpReady: (jump: ((spanId: string) => void) | null) => void;
      video?: { onClock?: (clock: { t: number; playing: boolean; spanId: string | null; duration: number }) => void } | null }) => {
      useEffect(() => {
        props.onJumpReady((spanId) => jumped.push([props.content.extractionId, spanId]));
        return () => props.onJumpReady(null);
        // eslint-disable-next-line react-hooks/exhaustive-deps
      }, []);
      return (
        <div data-testid={`src-${props.content.extractionId}`} data-followed={props.lens?.className?.("fx_ext_softmax_s2_1", { annotated: false, active: false }) ?? ""}>
          {props.video ? (
            <>
              <button type="button" onClick={() => props.video?.onClock?.({ t: 25, playing: true, spanId: "fx_ext_video_c3", duration: 120 })}>play to 0:25</button>
              <button type="button" onClick={() => props.video?.onClock?.({ t: 72, playing: false, spanId: "fx_ext_video_c4", duration: 120 })}>pause at 1:12</button>
            </>
          ) : null}
        </div>
      );
    },
  };
});
vi.mock("../windows/PanelWindow", () => ({ PANEL_TITLES: { guide: "Guide", notes: "Notes", path: "Reading path", library: "Library" }, LibraryPanel: () => null, PathPanel: () => null, RailHostPanel: () => null }));

function deskTransport(server: FixtureDeskServer): DeskTransport {
  return {
    state: async () => server.state(),
    apply: async (input) => server.apply(input),
    applyPad: async (input) => server.applyPad(input),
    padGet: async ({ padId }) => server.padGet(padId),
    library: async () => FIXTURE_LIBRARY,
    resolveExtraction: async (sourceId: string) => Object.values(FIXTURE_SOURCES).find((source) => source.sourceId === sourceId)?.extractionId ?? sourceId,
  } as DeskTransport;
}

const quietGoal = { goals: async () => ({ version: 1, goals: [] }) } as unknown as GoalTransport;
const quietCompanion = { companionHistory: async () => ({ version: 1, days: [], cursor: null }) } as unknown as CompanionTransport;
const quietPads = {
  padProposals: async (input: { padId: string }) => ({ version: 1, padId: input.padId, proposals: [] }),
  padDrain: async () => ({ version: 1, pads: [] }),
  carriedList: async () => ({ carried: [], shelfLimit: 3 }),
  carriedMark: async () => ({}),
  passageUnionRange: async () => ({ version: 1, extractionId: "", spans: [], sections: [] }),
} as unknown as PadsTransport;

const { book, video } = FIXTURE_SOURCES;

function followAnswer(input: { extractionId: string; t: number; bookExtractionId: string }): FollowAlongDto {
  const covered = input.bookExtractionId === book.extractionId;
  return {
    videoExtractionId: input.extractionId, bookExtractionId: input.bookExtractionId, t: input.t, status: covered ? "following" : "no_passage",
    section: input.t < 40 ? { sectionId: "v2", title: "0:20–0:40", t0: 20, t1: 40 } : { sectionId: "v3", title: "0:40–2:00", t0: 40, t1: null }, chapter: null,
    learningObjects: covered ? [{ learningObjectId: "lo_softmax", title: "Softmax", sections: [{ sectionId: "s2", title: "2 Why the exponential", jumpSpanId: "fx_ext_softmax_s2_1" }] }] : [],
  };
}

let mintCount = 0;
const mint = (prefix: string) => `${prefix}_${++mintCount}`;

function mount() {
  const server = new FixtureDeskServer();
  const videoTransport = {
    followAlong: vi.fn(async (input: { extractionId: string; t: number; bookExtractionId: string }) => followAnswer(input)),
    chaptersList: vi.fn(async () => ({ extractionId: video.extractionId, chapters: [] })),
    correspondents: vi.fn(async () => ({ status: "none", learningObjects: [] })),
  } as unknown as VideoTransport;
  render(
    <DeskShell vaultKey={`vault-video-${Math.random()}`} onError={vi.fn()} transport={deskTransport(server)} initialViewport={{ width: 1600, height: 960 }}
      mintId={mint} goalTransport={quietGoal} companion={quietCompanion} padsTransport={quietPads} videoTransport={videoTransport} />,
  );
  return { server, videoTransport };
}

async function flushDesks() {
  for (let i = 0; i < 4; i += 1) {
    await act(async () => {
      vi.advanceTimersByTime(1000);
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
  }
}

const headOf = (windowId: string) => document.querySelector(`[data-desk-window="${windowId}"] .desk-pane-head`) as HTMLElement;

beforeEach(() => {
  jumped.length = 0;
  vi.useFakeTimers({ shouldAdvanceTime: true });
  const values = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => void values.set(key, value),
    removeItem: (key: string) => void values.delete(key),
    clear: () => values.clear(),
  });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("follow-along on the desks", () => {
  it("a book beside a playing video shows the following chip, marks its passage and scrolls to it; u unlinks it", async () => {
    const { videoTransport } = mount();
    fireEvent.click(await screen.findByRole("button", { name: "play to 0:25" }));
    await waitFor(() => expect(headOf("fx_w_book").querySelector(".fchip")?.textContent).toBe("following ▶ 0:20–0:40 0:25 · 2 Why the exponential"));
    expect(videoTransport.followAlong).toHaveBeenCalledWith({ extractionId: video.extractionId, t: 25, bookExtractionId: book.extractionId });
    expect(jumped).toContainEqual([book.extractionId, "fx_ext_softmax_s2_1"]);
    await waitFor(() => expect(screen.getByTestId(`src-${book.extractionId}`).getAttribute("data-followed")).toContain("followed"));
    // A video's own head has no chip.
    expect(headOf("fx_w_video").querySelector(".fchip")).toBeNull();
    // u with the book focused: unlinked, the mark gone.
    fireEvent.click(headOf("fx_w_book"));
    fireEvent.keyDown(window, { key: "u", code: "KeyU" });
    await waitFor(() => expect(headOf("fx_w_book").querySelector(".fchip")?.textContent).toBe("unlinked · u to follow ▶ 0:20–0:40"));
    expect(screen.getByTestId(`src-${book.extractionId}`).getAttribute("data-followed") ?? "").not.toContain("followed");
  });
});

describe("the timestamp key", () => {
  it("alt+; stamps the focused video's time into the current desk's running pad, a quote anchored to the cue", async () => {
    const { server } = mount();
    fireEvent.click(await screen.findByRole("button", { name: "pause at 1:12" }));
    fireEvent.click(headOf("fx_w_video"));
    fireEvent.keyDown(window, { key: ";", code: "Semicolon", altKey: true });
    await flushDesks();
    await waitFor(() => expect(server.padBatches.length).toBeGreaterThan(0));
    const ops = server.padBatches.filter((batch) => batch.padId === "fx_pad_running").flatMap((batch) => batch.ops as PadOpDto[]);
    const insert = ops.find((op) => op.op === "insert_block") as Extract<PadOpDto, { op: "insert_block" }>;
    expect(insert).toMatchObject({ kind: "source_quote", provenance: "source", payload: { t: 72, extraction_id: video.extractionId, span_id: "fx_ext_video_c4" } });
    expect(insert.bodyMd).toMatch(/^▶ .+ at 1:12$/);
    expect(ops.find((op) => op.op === "link_anchor")).toMatchObject({ extractionId: video.extractionId, spanId: "fx_ext_video_c4" });
  });
});
