// FG1c (docs/specs/spec_followup_generate_serve_v1.md §7): the learner's optional read of what went
// wrong. Everything here is the server's list, in the order it gives (shuffled, with a logged seed);
// a mark is appended to a raw ledger and changes nothing that decides. It never stands between the
// learner and Next: no queue write, nothing required, and a failed save says so quietly.
import { useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type { HypothesisMark, HypothesisMarksDto } from "../../api/dto";
import { COLOR } from "../../components/term";
import { quietLine, quietLink } from "../../components/PlainParts";
import { MarkdownMath } from "../../render/MarkdownMath";

const MARK_LABELS: { mark: HypothesisMark; label: string }[] = [
  { mark: "my_gap", label: "This is my gap" },
  { mark: "partly", label: "Partly" },
  { mark: "not_it", label: "Not it" },
];

/**
 * Spec_router_objective_v1 §4 row 6: the client's display event for one list, sent once per list while it is
 * on screen, in the order shown. A refused receipt is the server's to warn about: this never fails a screen.
 */
export function useHypothesisListExposure(attemptId: string, surface: string, ids: string[], onScreen: boolean): void {
  const sent = useRef(new Set<string>());
  const key = `${attemptId}\0${surface}\0${ids.join("\0")}`;
  useEffect(() => {
    if (!onScreen || ids.length === 0 || sent.current.has(key)) return;
    sent.current.add(key);
    api
      .recordHypothesisExposure({ attemptId, surface, hypothesisVersionIds: ids, shownAt: new Date().toISOString() })
      .catch(() => undefined);
    // `key` carries `ids`.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, onScreen]);
}

const pressed = (on: boolean) => ({
  ...quietLink,
  color: on ? COLOR.text : COLOR.textDim,
  fontWeight: on ? 600 : 400,
  textDecoration: on ? "none" : quietLink.textDecoration,
});

export function HypothesisMarksPanel({ marks }: { marks: HypothesisMarksDto }) {
  const [read, setRead] = useState(marks);
  const [text, setText] = useState(marks.noneOfTheseText ?? "");
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    setRead(marks);
    setText(marks.noneOfTheseText ?? "");
    setFailed(false);
  }, [marks]);
  useHypothesisListExposure(read.attemptId, read.surface, read.hypotheses.map((row) => row.hypothesisVersionId), true);

  const save = async (mark: HypothesisMark | "none_of_these" | "cleared", hypothesisVersionId: string | null, freeText: string | null = null) => {
    setFailed(false);
    try {
      const reply = await api.recordHypothesisMark({
        attemptId: read.attemptId, mark, hypothesisVersionId, freeText, surface: read.surface,
      });
      if (reply.marks) setRead(reply.marks);
    } catch {
      setFailed(true);
    }
  };

  return (
    <div
      data-testid="hypothesis-marks"
      style={{ marginTop: 16, maxWidth: 900 }}
      // Enter and Space belong to the button in focus here, not to the screen's Next.
      onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") event.stopPropagation(); }}
    >
      <div style={{ fontSize: 14, color: COLOR.text }}>Possible causes</div>
      <div style={{ ...quietLine, marginTop: 2 }}>
        Does one of these fit what happened? This is optional, and it doesn't change your grade.
      </div>
      <div style={{ display: "grid", gap: 8, marginTop: 8 }}>
        {read.hypotheses.map((row) => (
          <div key={row.hypothesisVersionId} data-testid="hypothesis-mark-row">
            <div style={{ color: COLOR.text, fontSize: 14 }}><MarkdownMath value={row.statement} /></div>
            <div style={{ display: "flex", gap: 14, flexWrap: "wrap", marginTop: 2 }}>
              {MARK_LABELS.map(({ mark, label }) => (
                <button
                  key={mark}
                  type="button"
                  aria-pressed={row.mark === mark}
                  style={pressed(row.mark === mark)}
                  onClick={() => void save(row.mark === mark ? "cleared" : mark, row.hypothesisVersionId)}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 10 }}>
        <button
          type="button"
          aria-pressed={read.noneOfThese}
          style={pressed(read.noneOfThese)}
          onClick={() => void save(read.noneOfThese ? "cleared" : "none_of_these", null)}
        >
          None of these
        </button>
      </div>
      {read.noneOfThese ? (
        <div style={{ marginTop: 6 }}>
          <textarea
            aria-label="What do you think it was? (optional)"
            placeholder="What do you think it was? (optional)"
            rows={2}
            value={text}
            onChange={(event) => setText(event.target.value)}
            style={{ width: "100%", maxWidth: 640, fontFamily: "inherit", fontSize: 13 }}
          />
          <div>
            <button
              type="button"
              style={quietLink}
              disabled={text.trim() === (read.noneOfTheseText ?? "")}
              onClick={() => void save("none_of_these", null, text)}
            >
              Save
            </button>
          </div>
        </div>
      ) : null}
      {failed ? (
        <div data-testid="hypothesis-marks-failed" style={{ ...quietLine, marginTop: 6 }}>
          That didn't save. It's optional, so carry on whenever you like.
        </div>
      ) : null}
    </div>
  );
}
