import type { ReactNode } from "react";
import type { RepairedTraceDto } from "../api/dto";
import { COLOR, FONT_MONO } from "./term";
import { MarkdownMath } from "../render/MarkdownMath";

// ── Annotated repair diff ────────────────────────────────────────────────────
// A repaired trace is stored as two separately-authored parts: the learner's
// preserved work and the regenerated continuation. Rendering the fused
// `repairedAnswerMd` as one paragraph loses exactly the distinction the trace
// exists to make — the learner cannot see where their own reasoning stopped and
// the repair began, and a splice that lands mid-sentence reads as something
// they wrote. So the parts render as labeled blocks and the flat string stays
// what it always was: the derived value for consumers that need one string.

function Label({ children, tone }: { children: string; tone: string }) {
  return (
    <div
      style={{
        color: tone,
        fontFamily: FONT_MONO,
        fontSize: 10,
        letterSpacing: "0.04em",
        marginBottom: 4,
        textTransform: "uppercase"
      }}
    >
      {children}
    </div>
  );
}

function Block({
  children,
  accent
}: {
  children: ReactNode;
  accent: string;
}) {
  return (
    <div
      className="md-tight"
      style={{
        border: `1px solid ${COLOR.border}`,
        borderLeft: `2px solid ${accent}`,
        padding: "5px 9px",
        // Quoted answer text sitting two panels deep. At the inherited 13px it
        // matched the body prose of the surfaces that embed it — the inspector
        // receipt and the learner feedback panel are both 13 — so the quote read
        // as the page rather than as material being shown.
        fontSize: 12,
        lineHeight: 1.5,
        // pre-line, not pre-wrap: line breaks are meaningful in a learner's
        // work, runs of leading spaces are not — under pre-wrap they stacked on
        // top of markdown's own indentation.
        whiteSpace: "pre-line",
        overflowWrap: "anywhere"
      }}
    >
      {children}
    </div>
  );
}

/** The regenerated half, whether or not the model stored it separately. */
export function regeneratedPart(trace: RepairedTraceDto): string {
  const regenerated = (trace.regeneratedWork ?? "").trim();
  if (regenerated) return regenerated;
  const full = trace.repairedAnswerMd ?? "";
  const prefix = trace.learnerWorkPrefix ?? "";
  // Server-side the two are composed, so this slice is normally exact; it is a
  // fallback for legacy rows stored before the splice was made deterministic.
  if (prefix && full.startsWith(prefix)) return full.slice(prefix.length).trim();
  return full.trim();
}

export function RepairTraceBlocks({
  trace,
  preservedLabel = "your work",
  repairLabel = "the repair"
}: {
  trace: RepairedTraceDto;
  preservedLabel?: string;
  repairLabel?: string;
}) {
  const preserved = (trace.learnerWorkPrefix ?? "").trim();
  const repaired = regeneratedPart(trace);
  if (!preserved && !repaired && !trace.minimalEdit) return null;
  return (
    <div style={{ marginTop: 10, display: "grid", gap: 9 }}>
      {trace.minimalEdit ? (
        <div style={{ fontSize: 12, color: COLOR.textDim, lineHeight: 1.55 }}>
          <span style={{ color: COLOR.green }}>minimal edit · </span>
          {trace.minimalEdit}
        </div>
      ) : null}
      {preserved ? (
        <div>
          <Label tone={COLOR.textFaint}>{preservedLabel}</Label>
          <Block accent={COLOR.borderStrong}>
            <MarkdownMath value={preserved} />
          </Block>
        </div>
      ) : null}
      {repaired ? (
        <div>
          <Label tone={COLOR.green}>{repairLabel}</Label>
          <Block accent={COLOR.green}>
            <MarkdownMath value={repaired} />
          </Block>
        </div>
      ) : null}
    </div>
  );
}
