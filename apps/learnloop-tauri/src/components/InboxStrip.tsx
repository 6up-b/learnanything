import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { CaptureDto, InboxSummary } from "../api/capture";
import type { AskTarget } from "./AskOverlay";
import { WriteCardDialog } from "./WriteCardDialog";
import { QuickAddDialog } from "./QuickAddDialog";
import { CapturePhoto } from "./CapturePhoto";
import { COLOR, FONT_MONO } from "./term";
import { errorMessage } from "../errors";

const PENDING_LABEL: Record<NonNullable<CaptureDto["pendingRoute"]>, string> = {
  make_card: "card", quick_add: "source", ask_tutor: "tutor question",
};

const PAGE = 100;

function label(capture: CaptureDto): string {
  if (capture.status === "purged") return "Purged capture";
  return (capture.text || capture.url || capture.note || (capture.kind === "image" ? "Photo capture" : "Capture")).slice(0, 240);
}

/** References only: no queue mutation or practice navigation on receipt or save. */
export function InboxStrip({ subjects, onAsk }: {
  subjects: { id: string; title: string }[];
  onAsk: (target: AskTarget) => void;
}) {
  const [summary, setSummary] = useState<InboxSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<{ capture: CaptureDto; route: "card" | "source" } | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [purging, setPurging] = useState<string | null>(null);
  const [subjectId, setSubjectId] = useState(subjects[0]?.id ?? "");
  const [showAll, setShowAll] = useState(false);
  const [history, setHistory] = useState<CaptureDto[]>([]);
  const [pages, setPages] = useState(1);
  const [hasOlder, setHasOlder] = useState(false);
  const [purgeResult, setPurgeResult] = useState<CaptureDto | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [viewing, setViewing] = useState<string | null>(null);
  const alive = useRef(false);
  const request = useRef(0);
  const refresh = useCallback(async () => {
    const revision = ++request.current;
    try {
      const next = await api.getInboxSummary();
      // Re-read every loaded page so polling never drops older handled entries.
      let listed: CaptureDto[] | null = null;
      let older = false;
      if (showAll) {
        listed = [];
        for (let page = 0; page < pages; page++) {
          const { captures } = await api.listCaptureInbox({ status: null, limit: PAGE, offset: page * PAGE });
          listed.push(...captures);
          older = captures.length === PAGE;
          if (!older) break;
        }
      }
      if (alive.current && revision === request.current) {
        setSummary(next);
        if (listed) {
          const seen = new Set<string>();
          setHistory(listed.filter((row) => !seen.has(row.captureId) && seen.add(row.captureId)));
          setHasOlder(older);
        }
        setError(null);
      }
    } catch (err) {
      if (alive.current && revision === request.current) setError(errorMessage(err, "Could not load the inbox."));
    }
  }, [showAll, pages]);

  useEffect(() => {
    alive.current = true;
    void refresh();
    const timer = window.setInterval(() => void refresh(), 30_000);
    const focus = () => void refresh();
    window.addEventListener("focus", focus);
    return () => {
      alive.current = false;
      ++request.current;
      window.clearInterval(timer);
      window.removeEventListener("focus", focus);
    };
  }, [refresh]);

  async function remove(captureId: string, purge: boolean) {
    setBusy(captureId);
    try {
      if (purge) {
        const result = await api.purgeCapture(captureId);
        setPurgeResult(result.capture);
      }
      else await api.dismissCapture(captureId);
      setPurging(null);
      await refresh();
    } catch (err) {
      setError(errorMessage(err, "Could not update the capture."));
    } finally {
      setBusy(null);
    }
  }

  async function resume(captureId: string) {
    setBusy(captureId);
    setNotice(null);
    try {
      await api.resumeCaptureRoute(captureId);
      setNotice("Finished the earlier save.");
      await refresh();
    } catch (err) {
      setError(errorMessage(err, "Could not finish the earlier save."));
    } finally {
      setBusy(null);
    }
  }

  const pendingDeletes = summary?.deletePending ?? [];
  const pendingIds = new Set(pendingDeletes.map((capture) => capture.captureId));

  return (
    <section aria-label="Capture inbox" style={{ padding: "12px 20px", borderBottom: `1px solid ${COLOR.border}`, fontFamily: FONT_MONO, fontSize: 12 }}>
      {summary?.vaultMismatch ? (
        <p role="status">Phone captures are pinned to {summary.pinnedVault}, not this vault. Open that vault to see them.</p>
      ) : null}
      <strong>Inbox · {summary?.newCount ?? "…"}</strong>
      <button onClick={() => { setShowAll((value) => !value); setPages(1); setHasOlder(false); }}>{showAll ? "Show new" : "Include handled"}</button>
      <span style={{ color: COLOR.textFaint }}> · saved references, no practice started</span>
      {subjects.length ? (
        <label> · Tutor subject <select aria-label="Tutor subject" value={subjectId} onChange={(event) => setSubjectId(event.target.value)}>
          {subjects.map((subject) => <option key={subject.id} value={subject.id}>{subject.title}</option>)}
        </select></label>
      ) : null}
      {error ? <p role="alert">{error} <button onClick={() => void refresh()}>Retry</button></p> : null}
      {notice ? <p role="status">{notice}</p> : null}
      {!showAll && purgeResult?.mediaDeletePending && !pendingIds.has(purgeResult.captureId) ? (
        <p role="alert">Captured content was cleared, but original media deletion is pending. <button disabled={busy !== null} onClick={() => void remove(purgeResult.captureId, true)}>Retry delete</button></p>
      ) : null}
      {pendingDeletes.length ? (
        <div role="alert">
          Original media deletion is pending for {summary?.deletePendingCount ?? pendingDeletes.length} purged
          {(summary?.deletePendingCount ?? pendingDeletes.length) === 1 ? " capture" : " captures"}.
          {pendingDeletes.map((capture) => (
            <span key={capture.captureId}> {label(capture)} · received {capture.receivedAt.slice(0, 10)} <button disabled={busy !== null} onClick={() => void remove(capture.captureId, true)}>Retry delete</button></span>
          ))}
        </div>
      ) : null}
      {!showAll && purgeResult?.mediaRetainedShared ? (
        <p role="status">Original media is retained because another source or capture still references these bytes.</p>
      ) : null}
      {(showAll ? history : summary?.captures ?? []).map((capture) => (
        <div key={capture.captureId} style={{ paddingTop: 8, display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <span style={{ flex: 1, minWidth: 160, whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>
            {label(capture)}
          </span>
          {capture.status !== "new" ? <span>{capture.status}</span> : capture.kind === "url" ? (
            <button onClick={() => setSelected({ capture, route: "source" })}>Quick Add source</button>
          ) : (
            <button onClick={() => setSelected({ capture, route: "card" })}>Make a card</button>
          )}
          {capture.status === "new" && capture.pendingRoute ? (
            <span>An earlier save did not finish. <button disabled={busy !== null} onClick={() => void resume(capture.captureId)}>
              Finish saving {PENDING_LABEL[capture.pendingRoute]}
            </button></span>
          ) : null}
          {capture.kind === "text" && capture.status === "new" ? (
            <button disabled={!subjectId} title={!subjectId ? "Create a subject before asking the tutor" : undefined} onClick={() => onAsk({ context: "library", initialQuestion: capture.text ?? "", captureId: capture.captureId, subjectId })}>Ask tutor</button>
          ) : null}
          {capture.kind === "image" && capture.status !== "purged" ? (
            <button onClick={() => setViewing(viewing === capture.captureId ? null : capture.captureId)}>
              {viewing === capture.captureId ? "Hide photo" : "View photo"}
            </button>
          ) : null}
          {capture.kind === "image" ? <span>Photo → card (manual); capture kept as provenance.</span> : null}
          {capture.mediaDeletePending && !pendingIds.has(capture.captureId) ? <span role="alert">Original media deletion is pending. <button disabled={busy !== null} onClick={() => void remove(capture.captureId, true)}>Retry delete</button></span> : null}
          {capture.mediaRetainedShared ? <span>Original media is retained because another source or capture still references these bytes.</span> : null}
          {capture.status === "new" ? <button disabled={busy !== null} onClick={() => void remove(capture.captureId, false)}>Dismiss</button> : null}
          {purging === capture.captureId ? (
            <span>Delete captured content permanently? Notes/cards already created are kept. <button disabled={busy !== null} onClick={() => void remove(capture.captureId, true)}>Confirm purge</button> <button onClick={() => setPurging(null)}>Cancel</button></span>
          ) : capture.status !== "purged" ? <button disabled={busy !== null} onClick={() => setPurging(capture.captureId)}>Purge</button> : null}
          {viewing === capture.captureId && capture.kind === "image" && capture.status !== "purged" ? (
            <div style={{ flexBasis: "100%" }}><CapturePhoto captureId={capture.captureId} /></div>
          ) : null}
        </div>
      ))}
      {showAll && hasOlder ? <button onClick={() => setPages((value) => value + 1)}>Load older</button> : null}
      {selected?.route === "card" ? (
        <WriteCardDialog
          captureId={selected.capture.captureId}
          initialPrompt={selected.capture.text ?? selected.capture.note ?? ""}
          photoCaptureId={selected.capture.kind === "image" ? selected.capture.captureId : undefined}
          onClose={() => setSelected(null)}
          onCreated={() => void refresh()}
        />
      ) : null}
      {selected?.route === "source" ? (
        <QuickAddDialog
          subjects={subjects}
          captureId={selected.capture.captureId}
          defaultSource={selected.capture.url}
          onClose={() => setSelected(null)}
          onEnqueued={() => void refresh()}
        />
      ) : null}
    </section>
  );
}
