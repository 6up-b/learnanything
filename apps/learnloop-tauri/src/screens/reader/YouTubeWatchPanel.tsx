// The Reader's YouTube watch mode (owner request 2026-07-20), moved out of
// ReaderScreen by the RW3a hook extraction (a move, no behaviour change).
import { Fragment, forwardRef, useCallback, useEffect, useImperativeHandle, useMemo, useRef, useState, type ReactNode } from "react";
import type { ReaderRenderBlockDto, ReaderWatchPlanDto } from "../../api/dto";
import { COLOR, Card, Faint, FONT_MONO, Meta, Pill } from "../../components/term";
import { SecondaryButton } from "../../components/goldenpath/shared";
import type { TagMenuRequest } from "../../components/PdfReaderPane";
import { SEEN_SETTLE_MS } from "./useReadingProgress";

// The playing cue is the one with the latest start at most this far ahead of
// the player's time.
const CUE_LOOKAHEAD_S = 0.15;
// A seek the watch panel makes has landed when the player reports a time from
// just before its cue (the lookahead) to a moment of playing on after it.
// Until then the player's reports are from before the seek. A seek whose
// landing is never reported (the learner moved the player with YouTube's own
// controls) stops waiting after a while: the next report is where the player
// is, a placement too (reading-hardening Codex review 2, F2).
const SEEK_LANDING_EARLY_S = CUE_LOOKAHEAD_S;
const SEEK_LANDING_LATE_S = 2.5;
const SEEK_LANDING_WAIT_MS = 10_000;

// ── YouTube watch mode (owner request 2026-07-20) ───────────────────────────
// Embedded privacy-enhanced player (CSP already allows youtube-nocookie.com;
// controlled via the widget postMessage protocol — no external script). Playback
// drives the transcript position; the learner may pause and ask at any moment.
// Reviewed section checks remain in the stable Guide rail and never interrupt
// playback on their own.

const YT_ORIGIN = "https://www.youtube-nocookie.com";

function parseTimeLocator(value?: string | null): [number, number] | null {
  if (!value) return null;
  const match = /^t=(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)$/.exec(value.trim());
  return match ? [parseFloat(match[1]), parseFloat(match[2])] : null;
}

function formatClock(seconds: number): string {
  const total = Math.max(0, Math.floor(seconds));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const sec = total % 60;
  return h ? `${h}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}` : `${m}:${String(sec).padStart(2, "0")}`;
}

interface TranscriptCue {
  block: ReaderRenderBlockDto;
  start: number;
  end: number;
}

// The cue playing at ``time``. Auto-generated captions commonly overlap:
// stopping at the first cue whose end still covered the time left an older
// phrase highlighted while a newer one was being spoken, so it is the cue
// with the latest start at/before playback.
function cueAt(cues: TranscriptCue[], time: number): TranscriptCue | null {
  let active: TranscriptCue | null = null;
  for (const cue of cues) {
    if (cue.start > time + CUE_LOOKAHEAD_S) break;
    active = cue;
  }
  return active;
}

interface TranscriptSection {
  cues: TranscriptCue[];
  start: number;
  end: number;
  characters: number;
}

// Raw YouTube captions are often only a few words long. Keep their individual
// spans for timing, seeking, and annotation, but render adjacent cues together
// as readable transcript paragraphs.
function groupTranscriptCues(cues: TranscriptCue[]): TranscriptSection[] {
  const sections: TranscriptSection[] = [];
  for (const cue of cues) {
    const textLength = cue.block.markdown.trim().length;
    const current = sections[sections.length - 1];
    if (!current) {
      sections.push({ cues: [cue], start: cue.start, end: cue.end, characters: textLength });
      continue;
    }

    const previous = current.cues[current.cues.length - 1];
    const gap = cue.start - previous.end;
    const projectedDuration = Math.max(current.end, cue.end) - current.start;
    const previousEndsSentence = /[.!?]["')\]]?$/.test(previous.block.markdown.trim());
    const shouldStartSection =
      gap >= 3 ||
      projectedDuration > 18 ||
      current.characters + textLength + 1 > 260 ||
      (previous.end - current.start >= 10 && previousEndsSentence);

    if (shouldStartSection) {
      sections.push({ cues: [cue], start: cue.start, end: cue.end, characters: textLength });
      continue;
    }
    current.cues.push(cue);
    current.end = Math.max(current.end, cue.end);
    current.characters += textLength + 1;
  }
  return sections;
}

export interface WatchPanelHandle {
  /** Seek the video (and transcript) to the cue backing a span id. */
  seekToSpan: (spanId: string) => boolean;
}

export const YouTubeWatchPanel = forwardRef<WatchPanelHandle, {
  plan: ReaderWatchPlanDto;
  blocks: ReaderRenderBlockDto[];
  annotatedSpans: Set<string>;
  guidanceSpans: Set<string>;
  resumeSpan: string | null;
  findShortcutEnabled: boolean;
  /** The cue playback is at; ``advancing`` is false for a seek's landing
   *  and while the player is paused (only playing on is watching). Nothing
   *  is reported while a seek is on its way (its landing not yet reported). */
  onPlaybackSpan: (spanId: string | null, advancing: boolean) => void;
  /** Every seek this panel makes (a resume, a transcript cue, a jump), told
   *  before the player moves: a seek is a placement, not watching. */
  onSeek: (spanId: string | null) => void;
  onAskSpan: (spanId: string | null) => void;
  onTagMenu: (request: TagMenuRequest) => void;
  /** RW1a: the reconnect line under the transcript passage holding this cue. */
  inlineNote?: { spanId: string; node: ReactNode } | null;
}>(function YouTubeWatchPanel({
  plan,
  blocks,
  annotatedSpans,
  guidanceSpans,
  resumeSpan,
  findShortcutEnabled,
  onPlaybackSpan,
  onSeek,
  onAskSpan,
  onTagMenu,
  inlineNote = null,
}, ref) {
  const iframeRef = useRef<HTMLIFrameElement | null>(null);
  const transcriptRef = useRef<HTMLDivElement | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [followTranscript, setFollowTranscript] = useState(true);
  const [playerReady, setPlayerReady] = useState(false);
  const resumeSpanRef = useRef(resumeSpan);
  // Whether the player is playing (YouTube's playerState 1), once it says;
  // and until when a seek's landing (and the late reports around it) is not
  // playback.
  const playingRef = useRef<boolean | null>(null);
  const seekUntilRef = useRef(0);
  // The seek this panel made last (reading-hardening Codex review 2, F2):
  // where it goes, when, and the time the player reported on landing. Until it
  // lands, a report is from before it (a message sent before the seek can
  // arrive after it) and reaches neither the transcript nor the Reader.
  const seekRef = useRef<{ target: number; at: number; landing: number | null } | null>(null);
  // The cue a seek landed on, until the Reader is told: a placement, never
  // watching, however late the landing came.
  const placementRef = useRef<string | null | undefined>(undefined);
  const cuesRef = useRef<TranscriptCue[]>([]);
  const noteSeek = useCallback((spanId: string | null, target: number) => {
    const now = Date.now();
    seekUntilRef.current = now + SEEN_SETTLE_MS;
    seekRef.current = { target, at: now, landing: null };
    placementRef.current = undefined;
    onSeek(spanId);
  }, [onSeek]);
  // Whether a time the player reported is where it is now, as opposed to a
  // report sent before the panel's last seek.
  const acceptPlayerTime = useCallback((time: number): boolean => {
    const seek = seekRef.current;
    if (!seek) return true;
    const now = Date.now();
    if (seek.landing === null) {
      const landed = time >= seek.target - SEEK_LANDING_EARLY_S && time <= seek.target + SEEK_LANDING_LATE_S;
      if (!landed && now - seek.at < SEEK_LANDING_WAIT_MS) return false;
      seek.landing = time;
      placementRef.current = cueAt(cuesRef.current, time)?.block.spanId ?? null;
      return true;
    }
    if (now >= seek.at + SEEN_SETTLE_MS) {
      seekRef.current = null;
      return true;
    }
    // Just after the landing, only playing on from it is the player now; a
    // report from before the seek can still arrive.
    return time >= seek.landing - SEEK_LANDING_EARLY_S && time <= seek.landing + SEEK_LANDING_LATE_S + (now - seek.at) / 1000;
  }, []);
  // ctrl/cmd+F transcript find (mirrors the PDF pane's find conventions).
  const [findOpen, setFindOpen] = useState(false);
  const [findQuery, setFindQuery] = useState("");
  const [matchIdx, setMatchIdx] = useState(0);
  const findInputRef = useRef<HTMLInputElement | null>(null);

  const transcriptCues = useMemo<TranscriptCue[]>(() => {
    const cues: TranscriptCue[] = [];
    for (const block of blocks) {
      const range = parseTimeLocator(block.extractorBlockId);
      if (!range || !block.spanId) continue;
      cues.push({ block, start: range[0], end: range[1] });
    }
    return cues.sort((a, b) => a.start - b.start || a.end - b.end);
  }, [blocks]);
  cuesRef.current = transcriptCues;

  const transcriptSections = useMemo(() => groupTranscriptCues(transcriptCues), [transcriptCues]);

  const activeCue = useMemo(() => cueAt(transcriptCues, currentTime), [transcriptCues, currentTime]);

  const post = useCallback((func: string, args: unknown[] = []) => {
    iframeRef.current?.contentWindow?.postMessage(JSON.stringify({ event: "command", func, args }), YT_ORIGIN);
  }, []);

  // Widget handshake: subscribing makes the iframe stream infoDelivery
  // (currentTime / playerState) back to this window.
  const handshake = useCallback(() => {
    iframeRef.current?.contentWindow?.postMessage(JSON.stringify({ event: "listening", id: "llwatch", channel: "widget" }), YT_ORIGIN);
    const resumeCue = transcriptCues.find((cue) => cue.block.spanId === resumeSpanRef.current);
    if (resumeCue && resumeCue.start > 0) {
      noteSeek(resumeCue.block.spanId ?? null, resumeCue.start);
      post("seekTo", [resumeCue.start, true]);
      setCurrentTime(resumeCue.start);
    }
    setPlayerReady(true);
  }, [post, transcriptCues, noteSeek]);

  useEffect(() => {
    const onMessage = (event: MessageEvent) => {
      if (event.origin !== YT_ORIGIN) return;
      let data: { event?: string; info?: number | { currentTime?: number; playerState?: number } };
      try {
        data = typeof event.data === "string" ? JSON.parse(event.data) : event.data;
      } catch {
        return;
      }
      // The widget reports only what changed: the player's state when it
      // changes (also as onStateChange), the time as it moves.
      if (data?.event === "onStateChange" && typeof data.info === "number") {
        playingRef.current = data.info === 1;
      }
      if (data?.event === "infoDelivery" && typeof data.info === "object" && data.info !== null) {
        if (typeof data.info.playerState === "number") playingRef.current = data.info.playerState === 1;
        if (typeof data.info.currentTime === "number" && acceptPlayerTime(data.info.currentTime)) {
          setCurrentTime(data.info.currentTime);
        }
      }
    };
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, [acceptPlayerTime]);

  // Keep playback anchored in a dedicated transcript scroller, rather than
  // scrolling the whole Reader and pushing the video out of view. A learner who
  // wheels/touches the transcript pauses follow-mode until they explicitly
  // resume it.
  useEffect(() => {
    if (!playerReady) return;
    const spanId = activeCue?.block.spanId ?? null;
    const seek = seekRef.current;
    // A seek still on its way tells the Reader nothing: it already knows the
    // place (onSeek). The cue it lands on is a placement, never watching;
    // only playing on from there is (reading-hardening Codex review 2, F2).
    if (!seek || seek.landing !== null) {
      const placement = placementRef.current;
      placementRef.current = undefined;
      const placing = placement !== undefined && placement === spanId;
      onPlaybackSpan(spanId, !placing && playingRef.current !== false && Date.now() >= seekUntilRef.current);
    }
    if (!spanId || !followTranscript) return;
    const scroller = transcriptRef.current;
    const cue = scroller?.querySelector(`[data-transcript-span="${spanId}"]`);
    if (!(scroller instanceof HTMLElement) || !(cue instanceof HTMLElement)) return;
    // offsetTop is measured from the cue's offset parent, which is not
    // necessarily this scroller. Mixing that document-relative value with the
    // scroller's height can jump past the active caption into later ones. Use
    // viewport-relative rectangles to derive the cue's position inside the
    // scroller, then place its center at the scroller's midpoint.
    const scrollerRect = scroller.getBoundingClientRect();
    const cueRect = cue.getBoundingClientRect();
    const top = scroller.scrollTop + cueRect.top - scrollerRect.top - (scroller.clientHeight - cueRect.height) / 2;
    scroller.scrollTo({ top: Math.max(0, top), behavior: "smooth" });
  }, [activeCue, followTranscript, onPlaybackSpan, playerReady]);

  // Map playback time → the caption span whose cue window contains it (cue
  // t= locators stamped by captions_to_ir v2 / transcript_to_ir).
  const pauseAndAsk = useCallback(() => {
    post("pauseVideo");
    let best: string | null = null;
    for (const block of blocks) {
      const range = parseTimeLocator(block.extractorBlockId);
      if (!range || !block.spanId) continue;
      if (range[0] <= currentTime) best = block.spanId;
      else break;
    }
    onAskSpan(best ?? blocks.find((b) => b.spanId)?.spanId ?? null);
  }, [blocks, currentTime, onAskSpan, post]);

  const seekToCue = useCallback((cue: TranscriptCue) => {
    const selection = window.getSelection();
    if (selection && !selection.isCollapsed) return;
    noteSeek(cue.block.spanId ?? null, cue.start);
    post("seekTo", [cue.start, true]);
    post("playVideo");
    setFollowTranscript(true);
    onAskSpan(cue.block.spanId);
  }, [onAskSpan, post, noteSeek]);

  // ── transcript find ──
  const findNeedle = findQuery.trim().toLowerCase();
  const findMatches = useMemo(() => {
    if (!findOpen || findNeedle.length < 2) return [];
    return transcriptCues.filter((cue) =>
      (cue.block.markdown ?? "").toLowerCase().includes(findNeedle),
    );
  }, [transcriptCues, findOpen, findNeedle]);

  useEffect(() => {
    setMatchIdx(0);
  }, [findNeedle]);

  const scrollToFindMatch = useCallback((index: number) => {
    const cue = findMatches[index];
    const scroller = transcriptRef.current;
    if (!cue || !scroller) return;
    // Searching is scanning, not watching: stop follow so the scroller stays
    // on the hit. Clicking a hit cue still seeks the video as usual.
    setFollowTranscript(false);
    const el = scroller.querySelector(`[data-transcript-span="${cue.block.spanId}"]`);
    if (!(el instanceof HTMLElement)) return;
    const scrollerRect = scroller.getBoundingClientRect();
    const rect = el.getBoundingClientRect();
    const top = scroller.scrollTop + rect.top - scrollerRect.top - (scroller.clientHeight - rect.height) / 2;
    scroller.scrollTo({ top: Math.max(0, top), behavior: "smooth" });
  }, [findMatches]);

  const gotoFindMatch = useCallback((delta: number) => {
    if (!findMatches.length) return;
    setMatchIdx((i) => (i + delta + findMatches.length) % findMatches.length);
  }, [findMatches]);

  useEffect(() => {
    if (findOpen && findMatches.length) scrollToFindMatch(matchIdx);
  }, [findOpen, findMatches, matchIdx, scrollToFindMatch]);

  const openFind = useCallback(() => {
    setFindOpen(true);
    window.setTimeout(() => findInputRef.current?.focus(), 0);
  }, []);

  const closeFind = useCallback(() => {
    setFindOpen(false);
    setFindQuery("");
  }, []);

  useEffect(() => {
    if (!findShortcutEnabled) return;
    const handler = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "f") {
        event.preventDefault();
        openFind();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [findShortcutEnabled, openFind]);

  // Imperative jump for the guide rail (contents outline, quick-check "show me
  // the passage", suggested passages): seek the video to the cue's start
  // without forcing playback, and resume transcript follow so the scroller
  // lands on it. Returns false when the span is not a transcript cue.
  useImperativeHandle(ref, () => ({
    seekToSpan: (spanId: string) => {
      const cue = transcriptCues.find((c) => c.block.spanId === spanId);
      if (!cue) return false;
      noteSeek(spanId, cue.start);
      post("seekTo", [cue.start, true]);
      setCurrentTime(cue.start);
      setFollowTranscript(true);
      return true;
    },
  }), [transcriptCues, post, noteSeek]);

  return (
    <Card style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 14 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        <Pill color="cyan">watch mode</Pill>
        <Meta>{plan.videoId}</Meta>
        <Faint style={{ fontSize: 11 }}>{formatClock(currentTime)}</Faint>
        <span style={{ marginLeft: "auto" }}>
          <SecondaryButton onClick={pauseAndAsk}>pause &amp; ask about this moment</SecondaryButton>
        </span>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: 10, alignItems: "start" }}>
        <iframe
          ref={iframeRef}
          src={plan.embedUrl}
          title={`watch ${plan.videoId}`}
          style={{ width: "100%", aspectRatio: "16 / 9", border: 0, background: "#000" }}
          allow="encrypted-media; picture-in-picture"
          onLoad={handshake}
        />
        <div style={{ border: `1px solid ${COLOR.border}`, background: COLOR.bgInput }}>
        <div style={{ height: 30, padding: "0 10px", display: "flex", alignItems: "center", gap: 8, borderBottom: `1px solid ${COLOR.border}` }}>
          <Faint style={{ fontSize: 10, letterSpacing: "0.12em" }}>TRANSCRIPT</Faint>
          <Faint style={{ fontSize: 10 }}>{transcriptSections.length} passages</Faint>
          {findOpen ? (
            <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 6 }}>
              <input
                ref={findInputRef}
                value={findQuery}
                onChange={(event) => setFindQuery(event.target.value)}
                placeholder="find in transcript…"
                onKeyDown={(event) => {
                  if (event.key === "Enter") gotoFindMatch(event.shiftKey ? -1 : 1);
                  if (event.key === "Escape") {
                    event.stopPropagation();
                    closeFind();
                  }
                }}
                style={{ fontFamily: FONT_MONO, fontSize: 11, width: 150, background: COLOR.bg, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: "2px 6px" }}
              />
              <Faint style={{ fontSize: 10 }}>{findMatches.length ? `${matchIdx + 1}/${findMatches.length}` : "0/0"}</Faint>
              {([["↑", () => gotoFindMatch(-1)], ["↓", () => gotoFindMatch(1)], ["✕", closeFind]] as Array<[string, () => void]>).map(([label, onClick]) => (
                <button
                  key={label}
                  type="button"
                  onClick={onClick}
                  style={{ width: 20, height: 18, border: `1px solid ${COLOR.border}`, background: "transparent", color: COLOR.textDim, fontFamily: FONT_MONO, fontSize: 10, cursor: "pointer", padding: 0 }}
                >
                  {label}
                </button>
              ))}
            </div>
          ) : (
            <button
              type="button"
              onClick={openFind}
              title="find in transcript (ctrl+f)"
              style={{ marginLeft: "auto", width: 20, height: 18, border: `1px solid ${COLOR.border}`, background: "transparent", color: COLOR.textDim, fontFamily: FONT_MONO, fontSize: 11, cursor: "pointer", padding: 0 }}
            >
              ⌕
            </button>
          )}
          <button
            type="button"
            onClick={() => setFollowTranscript((value) => !value)}
            aria-pressed={followTranscript}
            style={{ marginLeft: findOpen ? 0 : 8, border: 0, background: "transparent", color: followTranscript ? COLOR.green : COLOR.textFaint, fontFamily: FONT_MONO, fontSize: 10, cursor: "pointer", padding: 0 }}
          >
            {followTranscript ? "● following video" : "○ resume follow"}
          </button>
        </div>
        <div
          ref={transcriptRef}
          className="ll-scroll"
          tabIndex={0}
          onWheel={() => setFollowTranscript(false)}
          onTouchStart={() => setFollowTranscript(false)}
          onMouseDown={() => setFollowTranscript(false)}
          onKeyDown={(event) => {
            if (["ArrowUp", "ArrowDown", "PageUp", "PageDown", "Home", "End"].includes(event.key)) setFollowTranscript(false);
          }}
          style={{ maxHeight: 230, overflowY: "auto", scrollBehavior: "smooth", padding: "8px 0" }}
          aria-live="off"
        >
          {transcriptCues.length === 0 ? (
            <Faint style={{ display: "block", padding: "10px 12px", fontSize: 11 }}>No timestamped transcript was extracted for this video.</Faint>
          ) : transcriptSections.map((section) => {
            const activeSpanId = activeCue?.block.spanId;
            const active = section.cues.some((cue) => cue.block.spanId === activeSpanId);
            const annotated = section.cues.some((cue) => annotatedSpans.has(cue.block.spanId ?? ""));
            const guided = section.cues.some((cue) => guidanceSpans.has(cue.block.spanId ?? ""));
            const sectionKey = section.cues[0].block.spanId ?? `t-${section.start}`;
            return (
              <div
                key={sectionKey}
                aria-label={`Transcript from ${formatClock(section.start)} to ${formatClock(section.end)}`}
                style={{ display: "grid", gridTemplateColumns: "48px minmax(0, 1fr)", gap: 8, padding: "8px 10px", borderLeft: `3px solid ${active ? COLOR.amber : annotated ? COLOR.greenSoft : guided ? COLOR.purplePill : "transparent"}`, background: guided && !active ? COLOR.washPurple : "transparent", color: COLOR.textDim, fontFamily: FONT_MONO, fontSize: 11, lineHeight: 1.65 }}
              >
                <span style={{ color: active ? COLOR.amberLink : COLOR.textFaint }}>{formatClock(section.start)}</span>
                <span>
                  {section.cues.map((cue, index) => {
                    const spanId = cue.block.spanId ?? "";
                    const cueActive = activeSpanId === spanId;
                    const cueAnnotated = annotatedSpans.has(spanId);
                    const cueGuided = guidanceSpans.has(spanId);
                    const cueFindHit = findOpen && findNeedle.length >= 2
                      && (cue.block.markdown ?? "").toLowerCase().includes(findNeedle);
                    const cueCurrentFind = cueFindHit && findMatches[matchIdx]?.block.spanId === spanId;
                    return (
                      <Fragment key={spanId}>
                        <span
                          data-span-id={spanId}
                          data-transcript-span={spanId}
                          onClick={() => seekToCue(cue)}
                          onContextMenu={(event) => {
                            event.preventDefault();
                            const sel = window.getSelection();
                            const quote = sel && !sel.isCollapsed ? sel.toString().replace(/\s+/g, " ").trim() : "";
                            onTagMenu({ x: event.clientX, y: event.clientY, spanId, quote: quote || null });
                          }}
                          role="button"
                          tabIndex={0}
                          onKeyDown={(event) => {
                            if (event.key === "Enter" || event.key === " ") {
                              event.preventDefault();
                              seekToCue(cue);
                            }
                          }}
                          style={{ cursor: "pointer", padding: "1px 2px", background: cueFindHit ? "rgba(255, 213, 79, 0.18)" : cueActive ? COLOR.washAmber : cueGuided ? COLOR.washPurple : "transparent", outline: cueCurrentFind ? `1px solid ${COLOR.amber}` : undefined, color: cueActive || cueFindHit ? COLOR.text : COLOR.textDim, borderBottom: cueAnnotated ? `1px solid ${COLOR.greenSoft}` : "1px solid transparent", boxDecorationBreak: "clone", WebkitBoxDecorationBreak: "clone" }}
                        >
                          {cue.block.markdown}
                        </span>
                        {index < section.cues.length - 1 ? " " : null}
                      </Fragment>
                    );
                  })}
                </span>
                {inlineNote && section.cues.some((cue) => cue.block.spanId === inlineNote.spanId) ? (
                  <div style={{ gridColumn: "2 / span 1" }}>{inlineNote.node}</div>
                ) : null}
              </div>
            );
          })}
        </div>
        </div>
      </div>
    </Card>
  );
});
