// "◇ suggested chapters" under a video window's player (spec §7.9; RD10): each chapter's time range, title and LO tag,
// with accept (stored; its tick joins the scrub track and its range the minimap) and not this (dismissed, logged).
// The chapters are judged on the learner's ask ("suggest from the transcript"): a polled job, polled only while the
// window is live, cancellable while it runs. A suggestion is a proposal: it never changes coverage. Accepting one
// does (owner decision 2026-11-23): its range then counts as a place its topics are taught, once; the panel says so
// before the learner accepts.
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import type { ChaptersJobDto, VideoChapterDto } from "../../../api/dto";
import type { Poller } from "../../../api/poller";
import { useWhenLive, useWindowLifecycle } from "../lifecycle";
import type { VideoTransport } from "./desk";
import { chapterLabel, clockWords } from "./model";

/** What accepting does, said before the learner accepts (a decision is final; a section's "not about this"
 *  corrects it). */
export const ACCEPT_LINE = "accepting counts this stretch as teaching its topic for your goal · it stays; if part of it isn't, mark that part not about this";

export interface ChaptersState {
  chapters: VideoChapterDto[];
  side: ReactNode;
}

/** A video window's chapters: read once the window is live, suggested on the learner's ask, decided once. */
export function useVideoChapters({ extractionId, transport, poller, onChapters, onDecided, decisions = 0 }: {
  extractionId: string;
  transport: VideoTransport;
  poller: Poller;
  onChapters: (chapters: VideoChapterDto[]) => void;
  /** A decision stored here: every window showing this video reads its chapters again. */
  onDecided?: () => void;
  /** How many decisions the desk has seen on this video: a new one (here or in another window) reads again. */
  decisions?: number;
}): ChaptersState {
  const [chapters, setChapters] = useState<VideoChapterDto[] | null>(null);
  // The chapters as shown now: a decision's reply merges into these, never into the list it was asked from.
  const current = useRef<VideoChapterDto[]>([]);
  const [job, setJob] = useState<{ jobId: string } | null>(null);
  const [line, setLine] = useState<string | null>(null);
  const whenLive = useWhenLive();
  const { windowId } = useWindowLifecycle();
  const onChaptersRef = useRef(onChapters);
  onChaptersRef.current = onChapters;
  const onDecidedRef = useRef(onDecided);
  onDecidedRef.current = onDecided;
  const show = useCallback((next: VideoChapterDto[]) => {
    current.current = next;
    setChapters(next);
    onChaptersRef.current(next);
  }, []);

  // Read again when the next check falls due: from then the titles of what it covers are neutral.
  const [readAgain, setReadAgain] = useState(0);
  useEffect(() => {
    let live = true;
    let timer: number | undefined;
    void whenLive().then(() => transport.chaptersList({ extractionId })).then(
      (out) => {
        if (!live) return;
        show(out.chapters);
        const due = out.nextCheckDue ? Date.parse(out.nextCheckDue) : NaN;
        if (!Number.isNaN(due)) timer = window.setTimeout(() => setReadAgain((value) => value + 1), Math.min(Math.max(0, due - Date.now()) + 1, 2 ** 31 - 1));
      },
      () => { if (live) setChapters([]); },
    );
    return () => { live = false; if (timer !== undefined) window.clearTimeout(timer); };
  }, [extractionId, transport, whenLive, show, readAgain, decisions]);

  const settle = useCallback((out: ChaptersJobDto) => {
    if (!out.done) return false;
    setJob(null);
    if (out.status === "done" && out.result) {
      if (out.result.status === "ready") {
        show(out.result.chapters.filter((chapter) => chapter.state !== "dismissed"));
        setLine(out.result.chapters.some((chapter) => chapter.state === "suggested") ? null : "No new chapters were suggested.");
      } else {
        const { status, reason, message } = out.result;
        setLine(status === "capped" ? "Chapter suggestions reached their limit. You can still use existing chapters."
          : status === "no_sections" || (status === "unavailable" && reason === "curriculum_disabled") ? message
          : "Couldn’t suggest chapters. Try again or continue watching.");
      }
    } else if (out.status === "cancelled") setLine("Chapter suggestion stopped.");
    else setLine(out.error?.message ?? "Couldn’t suggest chapters. Try again or continue watching.");
    return true;
  }, [show]);

  // The job is polled through the app's one poller, under this window: a paused window's poll waits.
  useEffect(() => {
    if (!job) return;
    return poller.register<ChaptersJobDto>({
      key: `chapters:${job.jobId}`,
      request: () => transport.chaptersJob({ jobId: job.jobId }),
      onResult: (out) => (settle(out) ? { done: true } : undefined),
      onError: () => { setJob(null); setLine("Couldn’t load the suggestion. Select Suggest from the transcript to try again."); },
      owner: windowId,
    });
  }, [job, poller, transport, settle, windowId]);

  const suggest = useCallback(() => {
    setLine(null);
    void transport.chaptersSuggest({ extractionId }).then(
      (out) => { if (!settle(out) && out.jobId) setJob({ jobId: out.jobId }); },
      (error: unknown) => setLine((error as { message?: string })?.message ?? "Couldn’t suggest chapters. Try again or continue watching."),
    );
  }, [extractionId, transport, settle]);

  const cancel = useCallback(() => {
    if (!job) return;
    void transport.chaptersCancel({ jobId: job.jobId }).then((out) => settle(out), () => undefined);
  }, [job, transport, settle]);

  const decide = useCallback((chapter: VideoChapterDto, decision: "accept" | "dismiss") => {
    void transport.chaptersDecide({ chapterId: chapter.chapterId, decision }).then(
      (out) => {
        show(current.current.flatMap((each) => (each.chapterId !== chapter.chapterId ? [each] : out.chapter.state === "dismissed" ? [] : [out.chapter])));
        onDecidedRef.current?.();
      },
      (error: unknown) => {
        setLine((error as { message?: string })?.message ?? "Couldn’t update this chapter. Reopen the video and try again.");
        // Decided otherwise elsewhere (another window, another device): read what is stored.
        setReadAgain((value) => value + 1);
      },
    );
  }, [transport, show]);

  const list = useMemo(() => chapters ?? [], [chapters]);
  // Made again only when what it shows changes: the window's Reader re-renders with it.
  const side = useMemo(() => (
    <div className="vside desk-chapters" data-chapters="">
      <div className="hd">◇ suggested chapters</div>
      {list.some((chapter) => chapter.state === "suggested") ? <div className="cline quiet" data-chapters-accept-line="">{ACCEPT_LINE}</div> : null}
      {list.map((chapter) => {
        const topic = chapter.learningObjects?.[0];
        const lo = topic ? chapter.held || topic.held ? "a topic with a cold check due" : topic.title : null;
        return (
          <div key={chapter.chapterId} className={`chap${chapter.state === "accepted" ? " accepted" : ""}`} data-chapter={chapter.chapterId}>
            <span className="tr">{clockWords(chapter.t0)}–{clockWords(chapter.t1)}</span>
            <span><span className="ti">{chapterLabel(chapter)}</span>{lo ? <span className="lo"> ◇ {lo}</span> : null}</span>
            <span className="acts">
              {chapter.state === "suggested" ? (
                <>
                  <button type="button" className="btn" title={ACCEPT_LINE} onClick={() => decide(chapter, "accept")}>accept</button>
                  <button type="button" className="btn" onClick={() => decide(chapter, "dismiss")}>not this</button>
                </>
              ) : <span className="kept">✓ accepted</span>}
            </span>
          </div>
        );
      })}
      {job ? (
        <div className="cline" role="status">◐ Looking for chapters in the transcript… <button type="button" className="lnk" onClick={cancel}>cancel</button></div>
      ) : chapters !== null && !list.some((chapter) => chapter.state === "suggested") ? (
        <div className="cline">{list.length ? "every chapter decided · " : "No chapters to show. Reopen the video if chapters are missing · "}<button type="button" className="lnk" onClick={suggest}>suggest from the transcript</button></div>
      ) : null}
      {line ? <div className="cline quiet">{line}</div> : null}
    </div>
  ), [list, chapters, job, line, decide, cancel, suggest]);
  return { chapters: list, side };
}
