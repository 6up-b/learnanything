// Reader workbench RW2c: "Compare with the book's method" after a correct
// Submit (spec §5.10, §5.4, G40; UX §5.9). An optional line on the feedback
// screen of a workbench problem answered correctly: *compare methods ▸*
// opens the learner's route (their steps, in their voice) beside the
// reference (the item's key, or for an imported exercise whose key is the
// book's solution, that passage, labelled by source), with one AI-written
// line per difference, labelled, and a valid different route named valid.
//
// The reference is read by id on the server, never retrieved; opening it
// writes a reveal on the ITEM (answer_display, or source_review for the
// book's passage) before the reference comes back, so the reveal-aware cold
// lane treats the family as revealed. Nothing here touches the attempt.
//
// Rendered only while workbench.compare_methods_enabled is on (the app
// config carries `compareMethods` only then), so off the feedback screen is
// exactly as before and makes no call. Nothing here moves focus, animates or
// opens a dialog.
import { useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type { WorkbenchCompareJobResultDto, WorkbenchCompareLinesDto, WorkbenchComparisonDto } from "../../api/dto";
import { quietLine, quietLink } from "../../components/PlainParts";
import { MarkdownMath } from "../../render/MarkdownMath";
import { LearnerVoice, MeaningLabel, ModelVoice, SourceVoice } from "../reader/voices";
import { errorMessage } from "../../errors";

export const COMPARE_COPY = {
  offer: "compare methods ▸",
  opening: "opening the comparison…",
  comparing: "comparing the two routes…",
  offerTitle: "Compare with the book's method: your steps beside the reference. Opening it counts as seeing the answer for this question's family.",
} as const;

/** A correct Submit (the server's own rule; it checks again). */
const CORRECT = 0.999;
const FIRST_POLL_MS = 350;
const MAX_POLL_MS = 1500;

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function CompareMethods({ attemptId, correctness, held }: {
  attemptId: string;
  correctness: number | null | undefined;
  held: boolean;
}) {
  const [offered, setOffered] = useState(false);
  const [opening, setOpening] = useState(false);
  const [comparison, setComparison] = useState<WorkbenchComparisonDto | null>(null);
  const [lines, setLines] = useState<WorkbenchCompareLinesDto | null>(null);
  const [linesPending, setLinesPending] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const alive = useRef(true);
  const correct = !held && typeof correctness === "number" && correctness >= CORRECT;

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);

  useEffect(() => {
    setOffered(false);
    setComparison(null);
    setLines(null);
    setNotice(null);
    if (!correct) return;
    let cancelled = false;
    void api.workbenchCompareOffer({ attemptId }).then((offer) => {
      if (!cancelled && alive.current) setOffered(offer.available === true);
    }).catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [attemptId, correct]);

  async function open() {
    if (opening || comparison) return;
    setOpening(true);
    setNotice(null);
    try {
      const opened = await api.workbenchCompareMethods({ attemptId });
      if (!alive.current) return;
      setComparison(opened.comparison);
      setLines(opened.comparison.lines);
      if (opened.linesJobId && !opened.comparison.lines) void follow(opened.linesJobId);
    } catch (error) {
      if (alive.current) setNotice(`Couldn't open the comparison just now (${errorMessage(error)}).`);
    } finally {
      if (alive.current) setOpening(false);
    }
  }

  async function follow(jobId: string) {
    setLinesPending(true);
    try {
      let job = await api.workbenchHelpJob(jobId);
      let wait = FIRST_POLL_MS;
      while (job.jobId && job.state === "pending" && alive.current) {
        await sleep(wait);
        if (!alive.current) return;
        wait = Math.min(MAX_POLL_MS, Math.round(wait * 1.5));
        job = await api.workbenchHelpJob(jobId);
      }
      if (!alive.current) return;
      const result = job.result as unknown as WorkbenchCompareJobResultDto | null;
      if (result?.status === "ready" && result.lines) setLines(result.lines);
      else setNotice(result?.message ?? "Couldn't compare the methods just now; the reference is shown.");
    } catch (error) {
      if (alive.current) setNotice(`Couldn't compare the methods just now (${errorMessage(error)}); the reference is shown.`);
    } finally {
      if (alive.current) setLinesPending(false);
    }
  }

  if (!offered) return null;
  return (
    <div data-testid="feedback-compare-methods" style={{ marginTop: 14, maxWidth: 900, display: "flex", flexDirection: "column", gap: 6 }}>
      {!comparison ? (
        <div style={{ ...quietLine, fontSize: 12 }}>
          <button type="button" style={quietLink} title={COMPARE_COPY.offerTitle} aria-disabled={opening} onClick={() => void open()}>
            {opening ? COMPARE_COPY.opening : COMPARE_COPY.offer}
          </button>
        </div>
      ) : (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 12 }}>
            <LearnerVoice label={`you · ${comparison.learner.label.toLowerCase()}`}>
              <ol style={{ margin: 0, paddingLeft: 18 }}>
                {comparison.learner.steps.map((step) => (
                  <li key={step.number}><MarkdownMath value={step.bodyMd} /></li>
                ))}
              </ol>
            </LearnerVoice>
            {comparison.reference.kind === "book_solution" ? (
              <SourceVoice source={comparison.reference.label}><MarkdownMath value={comparison.reference.text} /></SourceVoice>
            ) : (
              <div data-voice="item" style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                <MeaningLabel style={{ fontSize: 10 }}>{comparison.reference.label}</MeaningLabel>
                <MarkdownMath value={comparison.reference.text} />
              </div>
            )}
          </div>
          {linesPending ? <MeaningLabel style={{ fontSize: 11 }}><span aria-hidden="true">◐</span> {COMPARE_COPY.comparing}</MeaningLabel> : null}
          {lines ? (
            <ModelVoice note={lines.label}>
              {lines.routeLine ? <div data-testid="compare-route-line">{lines.routeLine}</div> : null}
              {lines.differences.length ? (
                <ul style={{ margin: 0, paddingLeft: 18 }}>
                  {lines.differences.map((entry, index) => (
                    <li key={index} data-difference-kind={entry.kind}>
                      {entry.learnerStep ? `step ${entry.learnerStep} · ` : ""}{entry.line}
                    </li>
                  ))}
                </ul>
              ) : null}
            </ModelVoice>
          ) : null}
        </>
      )}
      {notice ? <div role="status" aria-live="polite"><MeaningLabel style={{ fontSize: 11 }}>{notice}</MeaningLabel></div> : null}
    </div>
  );
}
