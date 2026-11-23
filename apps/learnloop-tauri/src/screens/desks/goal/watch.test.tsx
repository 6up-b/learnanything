// The goal lens over a video window (spec §12.3 point 5, §12.4): the transcript's passage groups take the lens's
// classes and marks, the head sits at the top of the transcript, the path's ranges are segments on a track under the
// player, and an annotated cue keeps full colour inside a dimmed passage. Without a lens the panel is as before.
import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import type { ReaderRenderBlockDto } from "../../../api/dto";
import { FixtureGoal } from "../../../fixtures/desks/goal";
import { FIXTURE_SOURCES, FIXTURE_VIEWS, FIXTURE_WATCH } from "../../../fixtures/desks/sources";
import { DIRECT_HUB, WindowScope } from "../lifecycle";
import { YouTubeWatchPanel, type WatchLens } from "../../reader/YouTubeWatchPanel";
import { readerLens } from "./marks";
import { indexLens } from "./model";

afterEach(cleanup);
const VIDEO = FIXTURE_SOURCES.video;
const blocks = FIXTURE_VIEWS[VIDEO.sourceId].blocks as ReaderRenderBlockDto[];

function panel(lens: WatchLens | null, annotated: string[] = []) {
  return render(
    <WindowScope lifecycle={{ windowId: "v", state: "active" }} hub={DIRECT_HUB}>
      <YouTubeWatchPanel plan={FIXTURE_WATCH[VIDEO.sourceId]} blocks={blocks} annotatedSpans={new Set(annotated)} guidanceSpans={new Set()}
        resumeSpan={null} findShortcutEnabled={false} onPlaybackSpan={() => undefined} onSeek={() => undefined}
        onAskSpan={() => undefined} onTagMenu={() => undefined} lens={lens} />
    </WindowScope>,
  );
}

describe("the goal lens on a transcript", () => {
  const lens = readerLens({ index: indexLens(new FixtureGoal().lens(VIDEO.extractionId)), dimOn: true, windowId: "v",
    handlers: { hover: () => undefined, tap: () => undefined } })!.watch!;

  it("marks each passage group, draws the path's segments on the track and heads the transcript", () => {
    panel(lens);
    const groups = [...document.querySelectorAll(".tp")];
    expect(groups.length).toBeGreaterThan(0);
    expect(groups[0].className).toBe("tp g-skip gl-dim");
    expect(groups.some((group) => group.className === "tp g-sup" && group.querySelector(".tx > .gm.gl-tx"))).toBe(true);
    expect(document.querySelectorAll(".tp.gl-dim").length).toBeGreaterThan(0);
    const segments = [...document.querySelectorAll("[data-goal-track] .gseg")] as HTMLElement[];
    // Three ranges on the path, over a 180 s transcript (30 cues of 6 s).
    expect(segments.map((segment) => `${segment.style.left} ${segment.style.width}`)).toEqual(["10% 26.67%", "36.67% 13.33%", "50% 33.33%"]);
    expect(document.querySelector("[data-goal-head]")!.textContent).toContain("on your path · 0:18–1:06");
  });

  it("keeps an annotated cue at full colour inside a dimmed passage", () => {
    panel(lens, [`${VIDEO.extractionId}_c2`]);
    expect(document.querySelector(`[data-transcript-span='${VIDEO.extractionId}_c2']`)!.className).toBe("gl-keep");
    expect(document.querySelector(`[data-transcript-span='${VIDEO.extractionId}_c1']`)!.className).toBe("");
  });

  it("without a lens draws no group class, mark, track or head", () => {
    panel(null);
    expect(document.querySelector(".tp, .gm, [data-goal-track], [data-goal-head], .gl-keep")).toBeNull();
  });
});
