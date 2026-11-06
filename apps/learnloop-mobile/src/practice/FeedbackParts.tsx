// Mobile v2 V2: feedback parity on the phone (spec §2.1 J2, J3 without probes, J4). Each part is the
// server's read, shown in the phone's words; none stands between the learner and Next.
import { useEffect, useRef, useState } from "react";
import type { CommandError, FeedbackBundle, FollowupDto, HypothesisMark, HypothesisMarksDto } from "@desktop/api/dto";
import { MarkdownMath } from "@desktop/render/MarkdownMath";
import { staleRefusal } from "../api/http";
import { phone } from "../api/phone";
import { RemoteImageAsLink } from "../components/RemoteImageAsLink";
import { newUlid } from "../util/ulid";
import { useVisibleInterval } from "../util/useVisibleInterval";
import { RouterLine } from "./RouterLine";
import { useAnswerDisplay } from "./useAnswerDisplay";

/** The desktop's interval for a follow-up's read (FG1 §6, `FeedbackScreen.tsx`): a `keep` bound. */
const FOLLOWUP_POLL_MS = 2000;

/**
 * J3 without probes (FG1 §6 on the phone, V2): what the follow-up workflow says. While a question is
 * prepared the answer and the causes are held, so the answer can tell them apart; *Show anyway* releases
 * them (the answer then doesn't count as independent), *Continue without it* goes on without the question.
 * The question itself is the desktop's until V3 (D3): the phone's plan leaves it for the desktop.
 */
export function useFollowup(attemptId: string, initial: FollowupDto | null | undefined) {
  const [read, setRead] = useState<FollowupDto | null>(initial ?? null);
  useEffect(() => setRead(initial ?? null), [initial]);
  const open = read !== null && (read.state === "pending" || read.held);
  const refresh = () =>
    phone
      .followupStatus(attemptId)
      .then((status) => {
        if (status.enabled) {
          const { enabled: _enabled, ...rest } = status;
          setRead(rest as FollowupDto);
        }
      })
      .catch(() => undefined);
  useVisibleInterval(() => void refresh(), FOLLOWUP_POLL_MS, open);
  return { followup: read, refresh };
}

export function FollowupPanel({
  attemptId,
  followup,
  onReleased,
  onRefresh
}: {
  attemptId: string;
  followup: FollowupDto;
  /** The held part came out: the bundle is re-read (not another open of the screen). */
  onReleased: () => void;
  onRefresh: () => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  async function act(run: () => Promise<unknown>) {
    setBusy(true);
    try {
      await run();
      await onRefresh();
      onReleased();
    } catch {
      // The panel's own read says what is so; a failed way out leaves it as it was.
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="banner" data-testid="followup-panel">
      {followup.line ? <p>{followup.line}</p> : null}
      {followup.held ? (
        <p className="dim">The answer and the possible causes come after the question, so your answer can tell them apart.</p>
      ) : null}
      <div className="row">
        {followup.held && followup.canShowAnyway ? (
          <button className="plain" type="button" disabled={busy} onClick={() => void act(() => phone.followupShowAnyway(attemptId))}>Show anyway</button>
        ) : null}
        {followup.canContinueWithout ? (
          <button className="plain" type="button" disabled={busy} onClick={() => void act(() => phone.followupContinueWithout(attemptId))}>Continue without it</button>
        ) : null}
      </div>
      <RouterLine decision={followup.routerDecision} />
    </section>
  );
}

const MARK_LABELS: { mark: HypothesisMark; label: string }[] = [
  { mark: "my_gap", label: "This is my gap" },
  { mark: "partly", label: "Partly" },
  { mark: "not_it", label: "Not it" }
];

/** FG1c §7: the learner's optional read of what went wrong. Appended to a raw ledger; it decides nothing. */
export function HypothesisMarks({ marks }: { marks: HypothesisMarksDto }) {
  const [read, setRead] = useState(marks);
  const [text, setText] = useState(marks.noneOfTheseText ?? "");
  const [failed, setFailed] = useState(false);
  const sent = useRef(new Set<string>());
  useEffect(() => {
    setRead(marks);
    setText(marks.noneOfTheseText ?? "");
  }, [marks]);
  const ids = read.hypotheses.map((row) => row.hypothesisVersionId);
  const key = `${read.attemptId}\0${read.surface}\0${ids.join("\0")}`;
  useEffect(() => {
    // The display event, once per list on screen (router objective §4 row 6).
    if (ids.length === 0 || sent.current.has(key)) return;
    sent.current.add(key);
    void phone
      .recordHypothesisExposure({ attemptId: read.attemptId, surface: read.surface, hypothesisVersionIds: ids, shownAt: new Date().toISOString() })
      .catch(() => undefined);
    // `key` carries `ids`.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  async function save(mark: HypothesisMark | "none_of_these" | "cleared", hypothesisVersionId: string | null, freeText: string | null = null) {
    setFailed(false);
    try {
      const reply = await phone.recordHypothesisMark({ attemptId: read.attemptId, mark, hypothesisVersionId, freeText, surface: read.surface });
      if (reply.marks) setRead(reply.marks);
    } catch {
      setFailed(true);
    }
  }

  return (
    <section data-testid="hypothesis-marks">
      <h2>Possible causes</h2>
      <p className="dim">Does one of these fit what happened? This is optional, and it doesn't change your grade.</p>
      {read.hypotheses.map((row) => (
        <div key={row.hypothesisVersionId} className="criterion">
          <div className="markdown"><MarkdownMath value={row.statement} components={RemoteImageAsLink} /></div>
          <div className="row">
            {MARK_LABELS.map(({ mark, label }) => (
              <button
                key={mark}
                className="plain"
                type="button"
                aria-pressed={row.mark === mark}
                onClick={() => void save(row.mark === mark ? "cleared" : mark, row.hypothesisVersionId)}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      ))}
      <div className="row">
        <button className="plain" type="button" aria-pressed={read.noneOfThese} onClick={() => void save(read.noneOfThese ? "cleared" : "none_of_these", null)}>
          None of these
        </button>
      </div>
      {read.noneOfThese ? (
        <>
          <label htmlFor="none-of-these">What do you think it was? (optional)</label>
          <textarea id="none-of-these" rows={2} value={text} onChange={(event) => setText(event.target.value)} />
          <div className="row">
            <button className="plain" type="button" disabled={text.trim() === (read.noneOfTheseText ?? "")} onClick={() => void save("none_of_these", null, text)}>
              Save
            </button>
          </div>
        </>
      ) : null}
      {failed ? <p className="dim" role="status">That didn't save. It's optional, so carry on whenever you like.</p> : null}
    </section>
  );
}

function answerText(value: unknown): string {
  if (typeof value === "string") return value;
  if (value == null) return "";
  if (Array.isArray(value)) return value.map(answerText).join("\n");
  if (typeof value === "object") {
    return Object.entries(value as Record<string, unknown>).map(([key, entry]) => `${key.replace(/_/g, " ")}: ${answerText(entry)}`).join("\n");
  }
  return String(value);
}

/** The answer the grade stands on, when the record says which it was (never a current one in its place). */
export function fullAnswerOf(feedback: FeedbackBundle): string {
  if (feedback.answeredSource === "unrecorded") return "";
  return answerText(feedback.answeredExpectedAnswer).trim();
}

/**
 * J2's reveal recording: *A full answer* opens on a tap and shows only while a recorded display covers it
 * (`record_answer_display`, the desktop's gate). Held behind a follow-up, it is not offered at all.
 */
export function FullAnswer({ feedback, held }: { feedback: FeedbackBundle; held: boolean }) {
  const text = fullAnswerOf(feedback);
  const [asked, setAsked] = useState(false);
  const exposure = useAnswerDisplay(feedback.attemptId, asked && !held && Boolean(text));
  if (!text || held) return null;
  if (!asked) {
    return (
      <div className="row">
        <button className="plain" type="button" onClick={() => setAsked(true)}>Show the full answer</button>
      </div>
    );
  }
  return (
    <section data-testid="full-answer">
      <h2>A full answer</h2>
      {exposure.shown ? (
        <div className="markdown"><MarkdownMath value={text} components={RemoteImageAsLink} /></div>
      ) : (
        <p className="dim" role="status">{exposure.status === "unavailable" ? "The full answer can't be shown right now." : "Opening the full answer…"}</p>
      )}
    </section>
  );
}

/**
 * "I think I was right" (UX Phase 4 §7.5): one optional line, kept before the grader looks again, which
 * never sees it. One key per contest, reused on a retry, so it is recorded and queued once.
 */
export function Contest({ attemptId, onBundle }: { attemptId: string; onBundle: (bundle: FeedbackBundle) => void }) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<FeedbackBundle["contest"] | null>(null);
  const key = useRef<{ id: string; reason: string } | null>(null);
  if (done) {
    return (
      <p className="dim" role="status">
        {done.reviewRequested ? "Noted. The grade will be looked at again." : done.regraded ? "Noted. The grader looked again." : "Noted."}
      </p>
    );
  }
  if (!open) {
    return (
      <div className="row">
        <button className="link" type="button" onClick={() => setOpen(true)}>I think I was right</button>
      </div>
    );
  }
  async function send() {
    const text = reason.trim();
    // A retry of the same reason reuses its key; an edited reason is a new contest.
    if (!key.current || key.current.reason !== text) key.current = { id: newUlid(), reason: text };
    setBusy(true);
    setError(null);
    try {
      const bundle = await phone.contestGrade(attemptId, text, key.current.id);
      onBundle(bundle);
      setDone(bundle.contest ?? { recorded: true, regraded: false, reviewRequested: false });
    } catch (failure) {
      setError(staleRefusal(failure) ? null : (failure as CommandError).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section>
      <label htmlFor="contest">Why do you think you were right? (optional, one line)</label>
      <input id="contest" value={reason} disabled={busy} onChange={(event) => setReason(event.target.value)} />
      {error ? <p className="bad" role="alert">{error}</p> : null}
      {busy ? <p className="dim" role="status">Looking again…</p> : null}
      <div className="row">
        <button className="plain" type="button" disabled={busy} onClick={() => void send()}>Send</button>
        <button className="plain" type="button" disabled={busy} onClick={() => setOpen(false)}>Cancel</button>
      </div>
    </section>
  );
}
