// A book window's follow-along chip in its head (spec §7.5; RD10): "following ▶ <chapter> <time> · <passage label>",
// "… · no passage here", or "unlinked · u to follow ▶ <chapter>". Shown only on a desk with a video. A click is `u`.
import { useSyncExternalStore } from "react";
import type { VideoDesk } from "./desk";
import { chipText } from "./model";

export function FollowChip({ desk, windowId }: { desk: VideoDesk; windowId: string }) {
  useSyncExternalStore(desk.subscribe, desk.getVersion);
  const state = desk.chipFor(windowId);
  if (!state) return null;
  const text = chipText(state);
  return (
    <button type="button" className={`chip fchip${state.kind === "unlinked" ? " off" : ""}`} data-follow={state.kind} title={text}
      onClick={(event) => { event.stopPropagation(); desk.toggle(windowId); }}>
      {text}
    </button>
  );
}
