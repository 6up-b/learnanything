// A video window on the desks (spec §7.4, §7.9; RD10): the Reader's source pane for the video (SourceWindow), with the
// suggested chapters under its player, the accepted chapters' ticks on its scrub track, and its player's clock handed
// to the desk (follow-along, the timestamp key).
import { useCallback, useMemo, useSyncExternalStore, type ComponentProps } from "react";
import type { VideoChapterDto } from "../../../api/dto";
import type { Poller } from "../../../api/poller";
import type { VideoExtras } from "../../reader/YouTubeWatchPanel";
import { SourceWindow } from "../windows/SourceWindow";
import { useVideoChapters } from "./ChaptersPanel";
import type { VideoDesk, VideoTransport } from "./desk";
import { chapterTicks } from "./model";

export function VideoWindow({ windowId, desk, transport, poller, ...source }: ComponentProps<typeof SourceWindow> & {
  windowId: string;
  desk: VideoDesk;
  transport: VideoTransport;
  poller: Poller;
}) {
  const extractionId = source.content.extractionId;
  const onChapters = useCallback((chapters: VideoChapterDto[]) => desk.chapters(extractionId, chapters), [desk, extractionId]);
  const decisions = useSyncExternalStore(desk.subscribe, () => desk.decisionsOn(extractionId));
  const onDecided = useCallback(() => desk.decided(extractionId), [desk, extractionId]);
  const { chapters, side } = useVideoChapters({ extractionId, transport, poller, onChapters, onDecided, decisions });
  const ticks = useMemo(() => chapterTicks(chapters), [chapters]);
  const onClock = useCallback<NonNullable<VideoExtras["onClock"]>>((clock) => desk.clock(windowId, extractionId, clock), [desk, windowId, extractionId]);
  const video = useMemo<VideoExtras>(() => ({ ticks, side, onClock }), [ticks, side, onClock]);
  return <SourceWindow {...source} video={video} />;
}
