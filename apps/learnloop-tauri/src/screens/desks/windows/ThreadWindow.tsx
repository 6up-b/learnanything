// A thread window (spec §7.8): one Reader thread, its root question and every follow-up under it, read from
// the source's ask history. A thread names only its root exchange; the window's view carries the reading it
// was asked in (set when it is opened from the companion or a search), without which it says where to find it.
import { useEffect, useState } from "react";
import { api } from "../../../api/client";
import type { ReaderAskHistoryExchangeDto, TutorCitationDto } from "../../../api/dto";
import { MarkdownMath } from "../../../render/MarkdownMath";
import { useWindowPaused } from "../lifecycle";

/** The exchanges of the thread `rootExchangeId` belongs to, in the order they were asked. */
export function threadExchanges(exchanges: ReaderAskHistoryExchangeDto[], rootExchangeId: string): ReaderAskHistoryExchangeDto[] {
  const byId = new Map(exchanges.map((exchange) => [exchange.eventId, exchange]));
  const rootOf = (exchange: ReaderAskHistoryExchangeDto): string => {
    let current = exchange;
    for (let step = 0; step < 64 && current.parentExchangeId && byId.has(current.parentExchangeId); step += 1) {
      current = byId.get(current.parentExchangeId) as ReaderAskHistoryExchangeDto;
    }
    return current.eventId;
  };
  // The ref may name any exchange of the thread (a follow-up opened from the companion): its root is the thread's.
  const named = byId.get(rootExchangeId);
  const root = named ? rootOf(named) : rootExchangeId;
  return exchanges.filter((exchange) => rootOf(exchange) === root);
}

export function ThreadWindow({ rootExchangeId, extractionId, onOpenClaim }: {
  rootExchangeId: string;
  extractionId: string | null;
  onOpenClaim: (citation: TutorCitationDto) => void;
}) {
  const paused = useWindowPaused();
  const [exchanges, setExchanges] = useState<ReaderAskHistoryExchangeDto[] | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  useEffect(() => {
    // A preview or a hidden window reads nothing; it reads once it is shown.
    if (!extractionId || paused || exchanges !== null) return;
    let live = true;
    api.readerAskHistory(extractionId).then(
      (found) => {
        if (live) setExchanges(threadExchanges(found.exchanges, rootExchangeId));
      },
      (error: unknown) => {
        if (live) setFailure(error && typeof error === "object" && "message" in error ? String((error as { message: unknown }).message) : String(error));
      },
    );
    return () => {
      live = false;
    };
  }, [extractionId, rootExchangeId, paused, exchanges]);

  if (!extractionId) {
    return <div className="desk-panel desk-quiet">This thread's reading isn't known on this desk. It is in the companion's history.</div>;
  }
  if (failure) return <div className="desk-panel desk-quiet">couldn't read this thread just now · {failure}</div>;
  if (exchanges === null) return <div className="desk-panel desk-quiet">◐ reading the thread…</div>;
  if (exchanges.length === 0) return <div className="desk-panel desk-quiet">This thread has no answered exchange in this reading.</div>;
  return (
    <div className="desk-thread" data-thread-window={rootExchangeId}>
      {exchanges.map((exchange) => (
        <div key={exchange.eventId} className="exchange">
          <div className="bub you"><span className="who">› you{exchange.createdAt ? ` · ${new Date(exchange.createdAt).toLocaleDateString("en-GB", { day: "numeric", month: "short" })}` : ""}</span><p>{exchange.questionMd}</p></div>
          <div className="bub ai">
            <span className="who">◇ LearnLoop</span>
            <div className="md"><MarkdownMath value={exchange.answerMd} /></div>
            {exchange.citations.length ? (
              <div className="claims">
                {exchange.citations.map((citation, index) => (
                  <button key={index} type="button" className="claim" onClick={() => onOpenClaim(citation)}>§ {citation.label ?? "the passage"} ↗</button>
                ))}
              </div>
            ) : null}
          </div>
        </div>
      ))}
    </div>
  );
}
