import { useEffect } from "react";
import type { QueueSnapshot, ScheduledItemDto, SessionEndSummary, SessionSnapshot } from "@desktop/api/dto";
import { useCachedQuery } from "@desktop/api/useCachedQuery";
import { TAG } from "@desktop/api/queryTags";
import { phone } from "../api/phone";

/** The phone's Today is the allowlisted queue, never the shared stored plan (M2a open item 2). A
 *  `keep` bound on the rows it asks for: every row it is given it shows, so the offer's receipt is
 *  what the phone showed (open item 3), and a phone session does not need a longer list. */
export const PHONE_QUEUE_LIMIT = 20;
/** The chips Start offers (the desktop's `MINUTE_PRESETS`, the three a phone session fits). */
const MINUTES = [10, 15, 25];

export function queueKey(sessionId: string): readonly [string, string] {
  return ["get_today_queue", sessionId];
}

export function queueRows(queue: QueueSnapshot | undefined, held: ReadonlySet<string>): ScheduledItemDto[] {
  const rows = queue?.sections.flatMap((section) => section.items) ?? [];
  return rows.filter((row) => !held.has(row.practiceItemId));
}

function waitingLine(count: number): string | null {
  if (count <= 0) return null;
  return `${count} ${count === 1 ? "item" : "items"} waiting for the desktop`;
}

export function TodayScreen({
  session,
  held,
  finished,
  busy,
  onBegin,
  onOpen,
  onEnd,
  onError
}: {
  session: SessionSnapshot | null;
  held: ReadonlySet<string>;
  finished: SessionEndSummary | null;
  busy: boolean;
  onBegin: (minutes: number) => void;
  onOpen: (row: ScheduledItemDto) => void;
  onEnd: () => void;
  onError: (error: unknown) => void;
}) {
  const sessionId = session?.sessionId ?? null;
  const query = useCachedQuery<QueueSnapshot>(
    sessionId ? queueKey(sessionId) : null,
    () => phone.getTodayQueue(sessionId as string, PHONE_QUEUE_LIMIT),
    { tags: [TAG.queue] }
  );
  useEffect(() => {
    if (query.error) onError(query.error);
    // Reported once per failure.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query.error]);

  if (!session) {
    return (
      <div className="main">
        <h1>Today</h1>
        {finished ? (
          <p className="banner" role="status">
            Session finished: {finished.attemptsRecorded} {finished.attemptsRecorded === 1 ? "answer" : "answers"}.
          </p>
        ) : null}
        <p className="dim">How long have you got?</p>
        <div className="row">
          {MINUTES.map((minutes) => (
            <button key={minutes} className="primary" type="button" disabled={busy} onClick={() => onBegin(minutes)}>
              {minutes} min
            </button>
          ))}
        </div>
      </div>
    );
  }

  const rows = queueRows(query.data, held);
  const [head, ...rest] = rows;
  const waiting = waitingLine((query.data?.deviceDeferredCount ?? 0) + held.size);
  return (
    <div className="main">
      <h1>Today</h1>
      {query.loading ? <p className="dim">Reading today's list…</p> : null}
      {head ? (
        <>
          <div className="row">
            <button className="primary" type="button" onClick={() => onOpen(head)}>Next: {head.learningObjectTitle}</button>
          </div>
          <ul className="list" aria-label="Today's items">
            {rest.map((row) => (
              <li key={row.practiceItemId}>
                <button type="button" onClick={() => onOpen(row)}>{row.learningObjectTitle}</button>
              </li>
            ))}
          </ul>
        </>
      ) : query.loading ? null : (
        <p className="dim">Nothing more for now.</p>
      )}
      {waiting ? <p className="dim" role="status">{waiting}</p> : null}
      <div className="row">
        <button className="plain" type="button" disabled={busy} onClick={onEnd}>End session</button>
      </div>
    </div>
  );
}
