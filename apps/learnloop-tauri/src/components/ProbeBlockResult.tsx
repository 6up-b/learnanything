import { useEffect, useState } from "react";
import { api } from "../api/client";
import type {
  ProbeBlockEndDto,
  UnresolvedCauseSelfReportResponse,
} from "../api/dto";
import { MarkdownMath } from "../render/MarkdownMath";
import { COLOR, FONT_MONO, Faint } from "./term";
import { Pill } from "./ui";
import { CausalFeedbackPanel } from "./CausalAttribution";

// Shared §5.7 block-end review: status/route banner + the withheld feedback
// released for every attempt in the block. Extracted from DialogueProbe's
// "done" phase so the ordinary Diagnostic Check review (DiagnosticReviewScreen)
// renders in the exact same visual language.

const ROUTE_LABEL: Record<string, string> = {
  tutoring: "next: tutoring on the diagnosed gap",
  next_block: "next: another short diagnostic block",
  ordinary_practice: "next: ordinary practice"
};

export function ProbeBlockResult({
  status,
  completionReason,
  route,
  releasedFeedback,
  labelForIndex,
  onError,
}: {
  status: string;
  completionReason: string | null;
  route: ProbeBlockEndDto["route"];
  releasedFeedback: ProbeBlockEndDto["releasedFeedback"];
  /** Per-entry caption (defaults to "observation N"); dialogue turns label by kind. */
  labelForIndex?: (index: number) => string;
  onError?: (message: string) => void;
}) {
  const [entries, setEntries] = useState(releasedFeedback);
  const [reportingAttemptId, setReportingAttemptId] = useState<string | null>(null);

  useEffect(() => {
    setEntries(releasedFeedback);
  }, [releasedFeedback]);

  const reportContest = async (
    attemptId: string,
    factorId: string | null,
    reason: UnresolvedCauseSelfReportResponse,
  ) => {
    if (reportingAttemptId) return;
    setReportingAttemptId(attemptId);
    try {
      if (factorId) {
        await api.reportUnresolvedCause({ factorId, response: reason });
      } else {
        await api.contestCausalDiagnosis(
          attemptId,
          reason as Exclude<UnresolvedCauseSelfReportResponse, "believed_candidate">,
        );
      }
      const refreshed = await api.getFeedback(attemptId);
      setEntries((current) =>
        current.map((entry) =>
          entry.attemptId === attemptId
            ? { ...entry, causalFeedback: refreshed.causalFeedback }
            : entry,
        ),
      );
    } catch (error) {
      onError?.((error as Error).message);
    } finally {
      setReportingAttemptId(null);
    }
  };

  return (
    <>
      <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        <Pill tone={status === "complete" ? "cyan" : "slate"}>{status}</Pill>
        {completionReason ? <Faint>{completionReason}</Faint> : null}
        {route ? (
          <span style={{ fontFamily: FONT_MONO, fontSize: 12, color: COLOR.amber }}>
            {ROUTE_LABEL[route] ?? route}
          </span>
        ) : null}
      </div>
      {entries.length > 0 ? (
        <div style={{ marginTop: 12, display: "grid", gap: 10 }}>
          <Faint>Feedback withheld during the block, released now:</Faint>
          {entries.map((feedback, index) => (
            <div
              key={feedback.attemptId}
              style={{ borderTop: `1px solid ${COLOR.border}`, paddingTop: 8, fontSize: 13 }}
            >
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <Pill tone={(feedback.rubricScore ?? 0) >= 3 ? "green" : "amber"}>
                  {feedback.rubricScore ?? "—"}/4
                </Pill>
                <Faint>{labelForIndex ? labelForIndex(index) : `observation ${index + 1}`}</Faint>
                {feedback.fatalErrors.length > 0 ? (
                  <span style={{ color: COLOR.red, fontFamily: FONT_MONO, fontSize: 11 }}>
                    {feedback.fatalErrors.join(", ")}
                  </span>
                ) : null}
              </div>
              {feedback.causalFeedback ? (
                <div style={{ marginTop: 8 }}>
                  <CausalFeedbackPanel
                    feedback={feedback.causalFeedback}
                    contestPending={reportingAttemptId === feedback.attemptId}
                    onContest={(reason, factorId) => {
                      void reportContest(feedback.attemptId, factorId, reason);
                    }}
                  />
                </div>
              ) : feedback.feedbackMd ? (
                <div className="markdown" style={{ marginTop: 4, fontSize: 12, lineHeight: 1.5 }}>
                  <MarkdownMath value={feedback.feedbackMd} />
                </div>
              ) : null}
            </div>
          ))}
        </div>
      ) : (
        <div style={{ marginTop: 10 }}>
          <Faint>No feedback to release for this block.</Faint>
        </div>
      )}
    </>
  );
}
