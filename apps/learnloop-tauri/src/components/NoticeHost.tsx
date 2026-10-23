// The simple shell's notices at the bottom edge (UX Phase 2,
// docs/specs/ux_learnloop_v1.md §7.9, §10 2.3). The list itself and its rules
// are app/notices.ts; this draws it and keeps its clock: a notice's few
// seconds run while it is on screen, so a notice held while the Reader has a
// book open (raised there, or shown before and held since) arrives whole at
// the next destination.
import { useEffect, useMemo, useState, type Dispatch, type SetStateAction } from "react";
import {
  NOTICE_TTL_MS,
  dismissNotice,
  expireNotices,
  markShown,
  restartHidden,
  runNoticeRetry,
  visibleNotices,
  type ShellNotice
} from "../app/notices";

export function NoticeHost({
  notices,
  holding,
  onChange
}: {
  notices: ShellNotice[];
  /** The Reader has a book open: hold notices (errors still show). */
  holding: boolean;
  onChange: Dispatch<SetStateAction<ShellNotice[]>>;
}) {
  const visible = useMemo(() => visibleNotices(notices, holding), [notices, holding]);
  const unstamped = visible.filter((notice) => notice.shownAt === null).map((notice) => notice.id).join(" ");
  const visibleIds = visible.map((notice) => notice.id).join(" ");
  const offScreenStamped = notices.some(
    (notice) => notice.kind !== "error" && notice.shownAt !== null && !visible.includes(notice)
  );

  // A notice that left the screen unexpired (held while reading, or pushed
  // off by an error) gets its whole time again when it is back (F7).
  useEffect(() => {
    if (!offScreenStamped) return;
    const ids = visibleIds ? visibleIds.split(" ") : [];
    onChange((list) => restartHidden(list, ids));
  }, [offScreenStamped, visibleIds, onChange]);

  // Stamp what has just come on screen.
  useEffect(() => {
    if (!unstamped) return;
    const ids = unstamped.split(" ");
    onChange((list) => markShown(list, ids, Date.now()));
  }, [unstamped, onChange]);

  // Let the next notice go when its time is up.
  const nextExpiry = visible.reduce<number | null>((soonest, notice) => {
    if (notice.kind !== "notice" || notice.shownAt === null) return soonest;
    const at = notice.shownAt + NOTICE_TTL_MS;
    return soonest === null || at < soonest ? at : soonest;
  }, null);
  useEffect(() => {
    if (nextExpiry === null) return;
    const timer = window.setTimeout(() => onChange((list) => expireNotices(list, Date.now())), Math.max(0, nextExpiry - Date.now()));
    return () => window.clearTimeout(timer);
  }, [nextExpiry, onChange]);

  if (visible.length === 0) return null;
  return (
    <div className="shell-notices" data-shell-chrome="">
      {visible.map((notice) => (
        <NoticeRow
          key={notice.id}
          notice={notice}
          onDismiss={() => onChange((list) => dismissNotice(list, notice.id))}
          onRetry={() => runNoticeRetry(notice, onChange)}
        />
      ))}
    </div>
  );
}

function NoticeRow({ notice, onDismiss, onRetry }: { notice: ShellNotice; onDismiss: () => void; onRetry: () => void }) {
  const [details, setDetails] = useState(false);
  const error = notice.kind === "error";
  return (
    <div
      className={`shell-notice shell-notice-${notice.kind}`}
      role={error ? "alert" : "status"}
      aria-live={error ? "assertive" : "polite"}
    >
      <span className="shell-notice-text">{notice.text}</span>
      {error && notice.retry ? (
        // The shell runs the retry and keeps this error until it settles
        // (fix round 2): it is gone on success, replaced on a new failure.
        <button type="button" className="shell-notice-action" disabled={notice.retrying === true} onClick={onRetry}>
          {notice.retrying ? "Trying again…" : "Try again"}
        </button>
      ) : null}
      {error && notice.code ? (
        <button type="button" className="shell-notice-details" aria-expanded={details} onClick={() => setDetails((open) => !open)}>
          {details ? "details ▾" : "details ▸"}
        </button>
      ) : null}
      <button type="button" className="shell-notice-dismiss" aria-label="Dismiss" onClick={onDismiss}>
        ×
      </button>
      {details && notice.code ? <span className="shell-notice-code">{notice.code}</span> : null}
    </div>
  );
}
