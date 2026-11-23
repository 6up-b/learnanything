// Reader workbench v2 (spec §3.6): media identity is per instance. Two players on one desk each hear
// only their own iframe: a message is taken when `event.source` is that player's frame, not merely
// when it comes from YouTube's origin (which every player shares).
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { ReaderRenderBlockDto, ReaderWatchPlanDto } from "../../api/dto";
import { WindowScope, type ListenerHub, DIRECT_HUB } from "../desks/lifecycle";
import { YouTubeWatchPanel } from "./YouTubeWatchPanel";

const YT = "https://www.youtube-nocookie.com";

function plan(videoId: string): ReaderWatchPlanDto {
  return { sourceId: `src_${videoId}`, videoId, embedUrl: `${YT}/embed/${videoId}?enablejsapi=1`, pausePoints: [] };
}

function cue(id: string, start: number, end: number): ReaderRenderBlockDto {
  return {
    displayNodeId: `node-${id}`, spanId: id, blockType: "Text", extractorBlockId: `t=${start}-${end}`,
    markdown: `cue ${id}`, sanitized: false, katexNodes: [], assets: [],
    health: { status: "ok", recommendedView: "derived", reasonFlags: [] },
  } as ReaderRenderBlockDto;
}

function Player({ videoId, hub = DIRECT_HUB, state = "active" as const }: { videoId: string; hub?: ListenerHub; state?: "active" | "visible" | "offscreen" }) {
  return (
    <div data-testid={`player-${videoId}`}>
      <WindowScope lifecycle={{ windowId: videoId, state }} hub={hub}>
        <YouTubeWatchPanel
          plan={plan(videoId)}
          blocks={[cue(`${videoId}1`, 0, 30), cue(`${videoId}2`, 30, 120)]}
          annotatedSpans={new Set()}
          guidanceSpans={new Set()}
          resumeSpan={null}
          findShortcutEnabled={false}
          onPlaybackSpan={() => undefined}
          onSeek={() => undefined}
          onAskSpan={() => undefined}
          onTagMenu={() => undefined}
        />
      </WindowScope>
    </div>
  );
}

function frameOf(videoId: string): HTMLIFrameElement {
  return within(screen.getByTestId(`player-${videoId}`)).getByTitle(`watch ${videoId}`) as HTMLIFrameElement;
}

function deliver(source: Window | null, currentTime: number) {
  act(() => {
    window.dispatchEvent(new MessageEvent("message", {
      origin: YT,
      source,
      data: JSON.stringify({ event: "infoDelivery", info: { currentTime, playerState: 1 } }),
    }));
  });
}

function clockOf(videoId: string): string {
  // The panel's header line: the video id, then its clock.
  const header = within(screen.getByTestId(`player-${videoId}`)).getByText(videoId).parentElement as HTMLElement;
  return header.textContent ?? "";
}

afterEach(cleanup);

describe("two players on one desk", () => {
  it("each takes only its own frame's time messages", () => {
    render(<><Player videoId="aaaa" /><Player videoId="bbbb" /></>);
    const a = frameOf("aaaa").contentWindow;
    const b = frameOf("bbbb").contentWindow;
    expect(a).toBeTruthy();
    expect(b).toBeTruthy();
    deliver(a, 75);
    expect(clockOf("aaaa")).toContain("1:15");
    expect(clockOf("bbbb")).toContain("0:00");
    deliver(b, 42);
    expect(clockOf("bbbb")).toContain("0:42");
    expect(clockOf("aaaa")).toContain("1:15");
  });

  it("ignores a message from YouTube's origin that no player's frame sent", () => {
    render(<Player videoId="cccc" />);
    deliver(window, 90);
    deliver(null, 91);
    expect(clockOf("cccc")).toContain("0:00");
  });
});

describe("a player whose window leaves the view", () => {
  it("is paused when its window goes offscreen, and not before", () => {
    // jsdom has no smooth scrolling; the transcript follows playback with it.
    Element.prototype.scrollTo = vi.fn();
    const { rerender } = render(<Player videoId="dddd" state="active" />);
    const frame = frameOf("dddd");
    const post = vi.spyOn(frame.contentWindow as Window, "postMessage");
    act(() => {
      fireEvent.load(frame);
    });
    const commands = () => post.mock.calls.map(([message]) => JSON.parse(String(message)).func).filter(Boolean);
    expect(commands()).not.toContain("pauseVideo");
    rerender(<Player videoId="dddd" state="offscreen" />);
    expect(commands()).toContain("pauseVideo");
  });
});
