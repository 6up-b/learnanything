// The companion (spec §8): the tutor behind one floating panel. It sits at a dock, hides to a tab, opens
// anchored at the selection, dissolves in place, hands off to its dock by a FLIP move, slides aside once
// when it would cover what the learner is looking at, and becomes the overview's pill in step with the zoom.
// Its body is the desk's thread (each question a `companion.ask` job, asks.ts) or the history by day and
// desk (`companion.history`). Answers' claims open beside; a thread opens as a window; previewed diffs
// wait for pads.
//
// A docked or hidden companion is placed in the stage's own coordinates and never moves when the learner
// scrolls, pans, reorders, gathers, pairs or switches desks; an anchored one leaves its anchor only by a
// hand-off or a dissolve. Every move is a transform and opacity (filter for the blur), never a jump.
import { forwardRef, useEffect, useImperativeHandle, useLayoutEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";
import type { CompanionDock, CompanionExchangeDto, CompanionHistoryDto, TutorCitationDto } from "../../../api/dto";
import { MarkdownMath } from "../../../render/MarkdownMath";
import { FitMath } from "../fitMath";
import type { Rect, Stage } from "../geometry";
import type { Timers } from "../keys/router";
import type { CompanionExchange } from "./asks";
import { DiffProposal, type ProposedDiff } from "./DiffProposal";
import { dockRect, nearestDock, pillRect, type CompanionState } from "./model";

/** Transition lengths (spec §4.3). */
export const COMPANION_MS = { move: 280, dissolve: 260, reduced: 200 } as const;

export interface CompanionContext {
  /** "following <glyph> <title>", or null when no window is focused. */
  following: { glyph: string; title: string } | null;
  goalInContext: boolean;
}

export interface CompanionChip {
  quote: string;
}

export interface CompanionHandle {
  /** The zoom's progress toward the overview (0 reading, 1 overview), null when no zoom runs. */
  zoomFrame(q: number | null): void;
  /** Where the panel shows now, in stage coordinates (for hand-off FLIPs and tests). */
  rect(): Rect | null;
}

export interface CompanionProps {
  state: CompanionState;
  dock: CompanionDock;
  stage: Stage;
  overview: boolean;
  reducedMotion: boolean;
  timers: Timers;
  context: CompanionContext;
  threadTitle: string;
  thread: CompanionExchange[];
  chip: CompanionChip | null;
  /** Why a question cannot be asked here now (no passage to ground it), or null when it can. */
  cannotAsk: string | null;
  /** The sideways shift that clears what it would cover (0 when nothing). */
  avoid: number;
  /** A page of the history: the first without a cursor, then each older page by the cursor the last gave. */
  loadHistory: (query: string, cursor?: string) => Promise<CompanionHistoryDto>;
  deskTitle: (deskId: string | null) => string;
  proposals?: (exchange: CompanionExchange) => ProposedDiff[];
  onAsk: (question: string) => void;
  onCancel: (requestId: string) => void;
  onRetry: (requestId: string) => void;
  onClearChip: () => void;
  onOpenClaim: (citation: TutorCitationDto) => void;
  onOpenAnchor: (anchor: NonNullable<CompanionExchangeDto["anchor"]>) => void;
  onOpenThread: (exchange: CompanionExchange) => void;
  onHide: () => void;
  onDock: () => void;
  onSnap: (dock: CompanionDock) => void;
  onPill: () => void;
  /** Typing in its input, for the latency trace (a keystroke's render time). */
  onEdit?: () => void;
}

function timeOf(ms: number): string {
  return new Date(ms).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
}

function dayLabel(date: string): string {
  const day = new Date(`${date}T12:00:00`);
  const today = new Date();
  if (day.toDateString() === today.toDateString()) return "today";
  return Number.isNaN(day.getTime()) ? date : day.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

function rectStyle(rect: Rect): CSSProperties {
  return { left: rect.x, top: rect.y, width: rect.w, height: rect.h };
}

export const Companion = forwardRef<CompanionHandle, CompanionProps>(function Companion(props, ref) {
  const { state, dock, stage, overview, reducedMotion, timers } = props;
  const [tab, setTab] = useState<"tutor" | "history">("tutor");
  const [draft, setDraft] = useState("");
  const [history, setHistory] = useState<CompanionHistoryDto | null>(null);
  const [historyFailed, setHistoryFailed] = useState<string | null>(null);
  const [historyQuery, setHistoryQuery] = useState("");
  const panelRef = useRef<HTMLDivElement | null>(null);
  const pillRef = useRef<HTMLButtonElement | null>(null);
  const tabRef = useRef<HTMLButtonElement | null>(null);
  const bodyRef = useRef<HTMLDivElement | null>(null);

  // What the panel shows: it stays mounted while it animates out (a dissolve or a hide), then goes.
  const showing = state.mode !== "hidden";
  const [leaving, setLeaving] = useState<"dissolve" | "hide" | null>(null);
  const [mounted, setMounted] = useState(showing);
  const restRect = state.mode === "anchored" && state.anchored ? state.anchored : dockRect(dock, stage);
  const [shownRect, setShownRect] = useState<Rect>(restRect);
  const lastShown = useRef<Rect | null>(null);

  useLayoutEffect(() => {
    if (showing) {
      setLeaving(null);
      setMounted(true);
      setShownRect(restRect);
      return;
    }
    if (!mounted) return;
    // Leaving: a dissolve stays where it is; a hide eases down out of its dock. Neither passes the dock.
    const kind = state.last === "dissolve" ? "dissolve" : "hide";
    setLeaving(kind);
    const handle = timers.set(() => {
      setMounted(false);
      setLeaving(null);
    }, reducedMotion ? COMPANION_MS.reduced : kind === "dissolve" ? COMPANION_MS.dissolve : COMPANION_MS.move);
    return () => timers.clear(handle);
    // restRect is derived from the props listed.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showing, state.mode, state.anchored, dock, stage.width, stage.height]);

  // FLIP: a hand-off or a snap moves from where the panel showed to its new rest rect by a transform.
  useLayoutEffect(() => {
    const panel = panelRef.current;
    const previous = lastShown.current;
    lastShown.current = shownRect;
    if (!panel || !previous || reducedMotion) return;
    if (state.last !== "hand-off" && state.last !== "snap") return;
    if (previous.x === shownRect.x && previous.y === shownRect.y && previous.w === shownRect.w && previous.h === shownRect.h) return;
    const dx = previous.x - shownRect.x;
    const dy = previous.y - shownRect.y;
    const sx = previous.w / Math.max(1, shownRect.w);
    const sy = previous.h / Math.max(1, shownRect.h);
    panel.style.transition = "none";
    panel.style.transformOrigin = "0 0";
    panel.style.transform = `translate(${dx}px, ${dy}px) scale(${sx}, ${sy})`;
    void panel.offsetWidth;
    panel.style.transition = "";
    panel.style.transform = "";
  }, [shownRect, state.last, reducedMotion]);

  useImperativeHandle(ref, () => ({
    zoomFrame(q) {
      const panel = panelRef.current;
      const pill = pillRef.current;
      const tabEl = tabRef.current;
      if (q === null) {
        if (panel) {
          panel.style.opacity = "";
          panel.style.transform = "";
          panel.style.transition = "";
        }
        for (const element of [pill, tabEl]) {
          if (!element) continue;
          element.style.opacity = "";
          element.style.transition = "";
        }
        return;
      }
      // The drawer's tab fades out as the pill fades in.
      if (tabEl) {
        tabEl.style.transition = "none";
        tabEl.style.opacity = String(1 - q);
      }
      // In step with the zoom: the panel shrinks toward the pill's corner and fades as the pill fades in.
      if (panel) {
        const target = pillRect(stage);
        const from = shownRect;
        const k = q;
        panel.style.transition = "none";
        panel.style.transformOrigin = "100% 100%";
        const tx = (target.x + target.w - (from.x + from.w)) * k;
        const ty = (target.y + target.h - (from.y + from.h)) * k;
        const s = 1 - (1 - target.w / Math.max(1, from.w)) * k;
        panel.style.transform = `translate(${tx}px, ${ty}px) scale(${s})`;
        panel.style.opacity = String(1 - k);
      }
      if (pill) {
        pill.style.transition = "none";
        pill.style.opacity = String(q);
      }
    },
    rect() {
      return mounted ? shownRect : null;
    },
  }), [mounted, shownRect, stage]);

  // History: loaded when its tab opens (and on a query), newest first, by day and then desk; older pages are
  // read by the cursor and appended.
  const historyGeneration = useRef(0);
  const [olderLoading, setOlderLoading] = useState(false);
  const loadOlder = () => {
    const cursor = history?.cursor;
    if (!cursor || olderLoading) return;
    const generation = historyGeneration.current;
    setOlderLoading(true);
    props.loadHistory(historyQuery.trim(), cursor).then(
      (page) => {
        if (generation !== historyGeneration.current) return;
        setHistory((now) => (now ? appendHistory(now, page) : page));
        setOlderLoading(false);
      },
      (error: unknown) => {
        if (generation !== historyGeneration.current) return;
        setOlderLoading(false);
        setHistoryFailed(error && typeof error === "object" && "message" in error ? String((error as { message: unknown }).message) : String(error));
      },
    );
  };
  useEffect(() => {
    if (tab !== "history" || !showing) return;
    let live = true;
    const generation = ++historyGeneration.current;
    setOlderLoading(false);
    const handle = timers.set(() => {
      props.loadHistory(historyQuery.trim()).then(
        (found) => {
          if (!live || generation !== historyGeneration.current) return;
          setHistory(found);
          setHistoryFailed(null);
        },
        (error: unknown) => {
          if (live) setHistoryFailed(error && typeof error === "object" && "message" in error ? String((error as { message: unknown }).message) : String(error));
        },
      );
    }, historyQuery ? 160 : 0);
    return () => {
      live = false;
      timers.clear(handle);
    };
    // loadHistory is a stable callback from the shell.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, showing, historyQuery, timers]);

  // The latest exchange stays in view as it arrives or changes.
  const lastStatus = props.thread.length ? `${props.thread.length}:${props.thread[props.thread.length - 1].status}` : "";
  useEffect(() => {
    const body = bodyRef.current;
    if (body && tab === "tutor") body.scrollTop = body.scrollHeight;
  }, [lastStatus, tab]);

  // The "earlier" dates come from the history's days (read once when the panel opens).
  const [earlier, setEarlier] = useState<string[]>([]);
  useEffect(() => {
    if (!showing) return;
    let live = true;
    props.loadHistory("").then((found) => {
      if (live) setEarlier(found.days.map((day) => day.date).filter((date) => dayLabel(date) !== "today").slice(0, 3));
    }, () => undefined);
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showing]);

  // Dragging the handle: the panel follows the pointer, and on drop snaps to the nearest dock.
  const drag = useRef<{ x: number; y: number; id: number } | null>(null);
  const onGrabDown = (event: React.PointerEvent<HTMLDivElement>) => {
    drag.current = { x: event.clientX, y: event.clientY, id: event.pointerId };
    (event.currentTarget as HTMLElement).setPointerCapture?.(event.pointerId);
    event.preventDefault();
  };
  const onGrabMove = (event: React.PointerEvent<HTMLDivElement>) => {
    const d = drag.current;
    const panel = panelRef.current;
    if (!d || !panel) return;
    panel.style.transition = "none";
    panel.style.transform = `translate(${event.clientX - d.x}px, ${event.clientY - d.y}px)`;
  };
  const onGrabUp = (event: React.PointerEvent<HTMLDivElement>) => {
    const d = drag.current;
    drag.current = null;
    const panel = panelRef.current;
    if (!d || !panel) return;
    const dx = event.clientX - d.x;
    const dy = event.clientY - d.y;
    const dropped = { x: shownRect.x + dx, y: shownRect.y + dy, w: shownRect.w, h: shownRect.h };
    panel.style.transform = "";
    panel.style.transition = "";
    if (Math.hypot(dx, dy) < 4) return;
    // The panel is now drawn where it was dropped, so the FLIP starts from there.
    lastShown.current = dropped;
    props.onSnap(nearestDock({ x: dropped.x + dropped.w / 2, y: dropped.y + dropped.h / 2 }, stage));
  };

  // Away (the overview) the panel and its tab are inert: Tab cannot reach the hidden input, and the focus moves
  // out of it (to the pill, the overview's way back); back from the overview it returns where it was.
  const returnFocus = useRef<HTMLElement | null>(null);
  useLayoutEffect(() => {
    const panel = panelRef.current;
    for (const element of [panel, tabRef.current]) {
      if (!element) continue;
      if (overview) {
        element.setAttribute("inert", "");
        element.setAttribute("aria-hidden", "true");
      } else {
        element.removeAttribute("inert");
        element.removeAttribute("aria-hidden");
      }
    }
    if (overview) {
      const active = document.activeElement;
      if (panel && active instanceof HTMLElement && panel.contains(active)) {
        returnFocus.current = active;
        active.blur();
        pillRef.current?.focus({ preventScroll: true });
      }
    } else if (returnFocus.current) {
      const back = returnFocus.current;
      returnFocus.current = null;
      if (back.isConnected && (document.activeElement === document.body || document.activeElement === pillRef.current || document.activeElement === null)) back.focus({ preventScroll: true });
    }
  }, [overview, mounted]);

  const motionClass = reducedMotion ? " still" : "";
  const enter = state.last === "summon" ? " summon" : state.last === "show" ? " show" : "";
  const anchorOrigin = state.mode === "anchored" && state.anchored ? `${Math.round(state.anchored.w / 2)}px 0px` : "50% 100%";

  const tabRect = dockRect(dock, stage);
  const tabLabel = `◇ tutor · ${props.threadTitle} c`;

  return (
    <>
      {/* The panel, the tab and the pill stay mounted through the overview (only faded), so a zoom in or out
          moves them in step with its frames and its commit changes nothing on screen. */}
      {mounted ? (
        <div
          ref={panelRef}
          className={`desk-companion${leaving ? ` leaving-${leaving}` : enter}${motionClass}${overview ? " away" : ""}`}
          data-desk-companion=""
          data-companion-mode={state.mode}
          data-companion-dock={dock}
          role="complementary"
          aria-label="the companion"
          style={{
            ...rectStyle(shownRect),
            ["--companion-avoid" as string]: `${props.avoid}px`,
            ["--companion-drop" as string]: `${shownRect.h + 40}px`,
            transformOrigin: anchorOrigin,
          } as CSSProperties}
        >
          <div className="grab" onPointerDown={onGrabDown} onPointerMove={onGrabMove} onPointerUp={onGrabUp} onPointerCancel={() => {
            drag.current = null;
            if (panelRef.current) panelRef.current.style.transform = "";
          }} aria-hidden="true" />
          <div className="ctabs" role="tablist">
            <button type="button" role="tab" aria-selected={tab === "tutor"} className={tab === "tutor" ? "on" : ""} onClick={() => setTab("tutor")}>◇ tutor</button>
            <button type="button" role="tab" aria-selected={tab === "history"} className={tab === "history" ? "on" : ""} onClick={() => setTab("history")}>history</button>
            <span className="grow" />
            <button type="button" onClick={props.onHide}>c hide</button>
          </div>
          <div className="ctx">
            <span>{props.context.following ? `following ${props.context.following.glyph} ${props.context.following.title}` : "following nothing yet"}</span>
            {/* The goal in view goes with each question to the tutor (its sentence and depth). */}
            {props.context.goalInContext ? <span className="goal gctx" title="your goal's lens is on this desk">◎ goal in view</span> : null}
            <span className="grow" />
            {earlier.length && tab === "tutor" ? (
              <button type="button" className="earlier" onClick={() => setTab("history")}>earlier · {earlier.map(dayLabel).join(" · ")} ›</button>
            ) : null}
          </div>
          <div className="body" ref={bodyRef}>
            {tab === "tutor" ? (
              props.thread.length === 0 ? (
                <div className="empty">◇ nothing asked on this desk yet · select a passage and press c</div>
              ) : (
                props.thread.map((exchange) => (
                  <ExchangeView
                    key={exchange.requestId}
                    exchange={exchange}
                    proposals={props.proposals?.(exchange) ?? []}
                    onCancel={props.onCancel}
                    onRetry={props.onRetry}
                    onOpenClaim={props.onOpenClaim}
                    onOpenThread={props.onOpenThread}
                  />
                ))
              )
            ) : (
              <HistoryView
                history={history}
                olderLoading={olderLoading}
                onOlder={loadOlder}
                failed={historyFailed}
                query={historyQuery}
                onQuery={setHistoryQuery}
                deskTitle={props.deskTitle}
                onOpenAnchor={props.onOpenAnchor}
              />
            )}
          </div>
          {props.chip ? (
            <div className="chip">
              <span className="g">§</span> <span className="lab">asking about</span> <span className="q">“{props.chip.quote.length > 120 ? `${props.chip.quote.slice(0, 119)}…` : props.chip.quote}”</span>
              <button type="button" aria-label="stop asking about the selection" onClick={props.onClearChip}>✕</button>
            </div>
          ) : null}
          <div className="cin">
            {props.cannotAsk ? <div className="cannot">{props.cannotAsk}</div> : null}
            <input
              className="input"
              value={draft}
              placeholder="› ask about this…"
              aria-label="ask about this"
              disabled={props.cannotAsk !== null}
              onChange={(event) => {
                setDraft(event.target.value);
                props.onEdit?.();
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  const question = draft.trim();
                  if (!question || props.cannotAsk) return;
                  props.onAsk(question);
                  setDraft("");
                  setTab("tutor");
                } else if (event.key === "Escape") {
                  event.preventDefault();
                  (event.currentTarget as HTMLInputElement).blur();
                }
              }}
            />
          </div>
        </div>
      ) : null}
      {!mounted ? (
        <button
          ref={tabRef}
          type="button"
          className={`desk-companion-tab${motionClass}${overview ? " away" : ""}`}
          data-desk-companion-tab=""
          style={{ left: tabRect.x + tabRect.w - 230, top: tabRect.y + tabRect.h - 26 }}
          onClick={props.onDock}
        >
          {tabLabel}
        </button>
      ) : null}
      {(
        <button
          ref={pillRef}
          type="button"
          className={`desk-companion-pill${overview ? " on" : ""}`}
          data-desk-companion-pill=""
          style={rectStyle(pillRect(stage))}
          onClick={props.onPill}
          tabIndex={overview ? 0 : -1}
          aria-hidden={overview ? undefined : true}
        >
          <span className="g">◇</span>
          <span className="t">{props.threadTitle}</span>
          <span className="k">› <kbd>c</kbd></span>
        </button>
      )}
    </>
  );
});

function ExchangeView({ exchange, proposals, onCancel, onRetry, onOpenClaim, onOpenThread }: {
  exchange: CompanionExchange;
  proposals: ProposedDiff[];
  onCancel: (requestId: string) => void;
  onRetry: (requestId: string) => void;
  onOpenClaim: (citation: TutorCitationDto) => void;
  onOpenThread: (exchange: CompanionExchange) => void;
}) {
  let answer: ReactNode;
  switch (exchange.status) {
    case "waiting":
      answer = (
        <div className="bub ai asking" data-exchange-status="waiting">
          <span className="who">◇ LearnLoop · saving your desk first</span>
          <p className="thinking">◐ it is asked about the desk as you left it, once that is saved</p>
        </div>
      );
      break;
    case "asking":
      answer = exchange.stopping ? (
        <div className="bub ai asking" data-exchange-status="stopping">
          <span className="who">◇ LearnLoop · stopping…</span>
          <p className="thinking">◐ waiting to hear how it ended</p>
        </div>
      ) : (
        <div className="bub ai asking" data-exchange-status="asking">
          <span className="who">◇ LearnLoop · {exchange.jobStatus === "queued" || exchange.jobStatus === null ? "asked" : "answering"}{exchange.streamedPieces > 0 ? ` · ${exchange.streamedPieces} pieces so far` : ""}</span>
          <p className="thinking">◐ writing the answer…</p>
          <button type="button" className="act" onClick={() => onCancel(exchange.requestId)}>stop</button>
        </div>
      );
      break;
    case "answered":
      answer = (
        <div className="bub ai" data-exchange-status="answered">
          <span className="who">◇ LearnLoop{exchange.answer?.citations.length ? " · claims link to the passage" : ""}</span>
          <FitMath className="md"><MarkdownMath value={exchange.answer?.answerMd ?? ""} /></FitMath>
          {exchange.answer?.citations.length ? (
            <div className="claims">
              {exchange.answer.citations.map((citation, index) => (
                <button key={`${citation.extractionId}:${citation.spanId}:${index}`} type="button" className="claim" onClick={() => onOpenClaim(citation)}>
                  § {citation.label ?? "the passage"} ↗
                </button>
              ))}
            </div>
          ) : null}
          {proposals.map((proposal) => <DiffProposal key={proposal.id} proposal={proposal} />)}
          <button type="button" className="act" onClick={() => onOpenThread(exchange)}>open the thread as a window ↗</button>
        </div>
      );
      break;
    case "failed":
      answer = (
        <div className="bub ai failed" data-exchange-status="failed">
          <span className="who">◇ couldn't answer</span>
          <p>{exchange.error?.message ?? "Something went wrong."}</p>
          {exchange.error?.retryable ? <button type="button" className="act" onClick={() => onRetry(exchange.requestId)}>try again</button> : null}
        </div>
      );
      break;
    case "cancelled":
      answer = (
        <div className="bub ai stopped" data-exchange-status="cancelled">
          <span className="who">◇ stopped</span>
          <p>{exchange.kept
            ? "The question was already sent; its answer is kept in your history, not shown here."
            : exchange.sent
              ? "The question was sent before it stopped; no answer is shown."
              : "Stopped before it was sent."}</p>
        </div>
      );
      break;
    case "interrupted":
      answer = (
        <div className="bub ai interrupted" data-exchange-status="interrupted">
          <span className="who">◇ interrupted</span>
          <p>{exchange.error?.message ?? "This was interrupted."}</p>
          <button type="button" className="act" onClick={() => onRetry(exchange.requestId)}>ask again</button>
        </div>
      );
      break;
  }
  return (
    <div className="exchange" data-exchange={exchange.requestId}>
      <div className="bub you">
        <span className="who">› you{exchange.quote ? ` · on “${exchange.quote.slice(0, 60)}${exchange.quote.length > 60 ? "…" : ""}”` : ""} · {timeOf(exchange.askedAt)}</span>
        <p>{exchange.question}</p>
      </div>
      {answer}
    </div>
  );
}

/** An older page of the history appended to the pages read: a day (and a desk in it) split across pages joins. */
export function appendHistory(now: CompanionHistoryDto, page: CompanionHistoryDto): CompanionHistoryDto {
  const days = now.days.map((day) => ({ ...day, desks: day.desks.map((desk) => ({ ...desk, exchanges: [...desk.exchanges] })) }));
  const seen = new Set(days.flatMap((day) => day.desks.flatMap((desk) => desk.exchanges.map((exchange) => exchange.questionEventId))));
  for (const day of page.days) {
    let into = days.find((each) => each.date === day.date);
    if (!into) {
      into = { ...day, desks: [] };
      days.push(into);
    }
    for (const desk of day.desks) {
      let deskInto = into.desks.find((each) => each.deskId === desk.deskId);
      if (!deskInto) {
        deskInto = { ...desk, exchanges: [] };
        into.desks.push(deskInto);
      }
      for (const exchange of desk.exchanges) {
        if (seen.has(exchange.questionEventId)) continue;
        seen.add(exchange.questionEventId);
        deskInto.exchanges.push(exchange);
      }
    }
  }
  return { ...page, days, cursor: page.cursor };
}

function HistoryView({ history, olderLoading, onOlder, failed, query, onQuery, deskTitle, onOpenAnchor }: {
  history: CompanionHistoryDto | null;
  olderLoading: boolean;
  onOlder: () => void;
  failed: string | null;
  query: string;
  onQuery: (query: string) => void;
  deskTitle: (deskId: string | null) => string;
  onOpenAnchor: (anchor: NonNullable<CompanionExchangeDto["anchor"]>) => void;
}) {
  return (
    <div className="history" data-companion-history="">
      <div className="hnote">every exchange stays here, by day and by desk, with the passage it was about · also in / search</div>
      <input className="hsearch" value={query} placeholder="search your exchanges" aria-label="search your exchanges" onChange={(event) => onQuery(event.target.value)} />
      {failed ? <div className="hitem dim">couldn't read your history just now · {failed}</div> : null}
      {history && history.days.length === 0 ? <div className="hitem dim">{query ? `nothing matches “${query}”` : "nothing asked yet"}</div> : null}
      {history?.days.map((day) => (
        <div key={day.date} className="hdayblock">
          <div className="hday">{dayLabel(day.date)}</div>
          {day.desks.map((desk) => (
            <div key={desk.deskId ?? "none"}>
              <div className="hdesk">{desk.deskId ? deskTitle(desk.deskId) : desk.exchanges.some((exchange) => exchange.origin === "backfill") ? "before desks" : "no desk"}</div>
              {desk.exchanges.map((exchange) => (
                <div key={exchange.questionEventId} className="hitem">
                  <div className="hq">› {exchange.questionMd}</div>
                  {exchange.answerFirstSentence ? <div className="ha">◇ {exchange.answerFirstSentence}</div> : null}
                  <div className="hm">
                    <span className="dim">{exchange.where}</span>
                    {exchange.anchor ? (
                      <button type="button" className="anchor" onClick={() => onOpenAnchor(exchange.anchor!)}>§ the passage ↗</button>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      ))}
      {history?.cursor ? (
        <button type="button" className="older" disabled={olderLoading} onClick={onOlder}>{olderLoading ? "◐ reading older exchanges…" : "older exchanges ›"}</button>
      ) : null}
    </div>
  );
}
