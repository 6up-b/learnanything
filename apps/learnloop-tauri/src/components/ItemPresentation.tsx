import type { CSSProperties } from "react";
import type { ItemPresentationDto, PresentationBlockDto } from "../api/dto";
import { COLOR, FONT_MONO, Faint } from "./term";
import { MarkdownMath } from "../render/MarkdownMath";

// Meas §3.A2/§3.A3 — the one renderer for "what must the learner SEE to answer
// this item". Practice and exams both mount THIS, rather than each reaching into
// the item for the fields it happens to know about. That habit is what shipped
// two whole instrument classes with no stimulus: an error hunt whose prompt said
// "repair the worked solution below" with nothing below it, and a laddered-stem
// part asking about a setup the learner was never shown. Neither failed loudly —
// the grader receives the material through its own path, so it marked every
// planted error missed and the projection banked negative facet mass for a
// repair nobody had the material to make.
//
// The rule that keeps it closed: render every block, in order, whatever its
// kind. `kind` selects a caption and a frame; it never decides whether a block
// is shown. A block kind this build does not recognise is a stimulus added after
// it was compiled, and hiding it would recreate the defect exactly.
//
// THE LADDERED STEM IS SHOWN ON EVERY PART, NOT ONCE PER RUN. §3.A2 describes
// presenting the shared setup once and amortizing the context load across the
// parts that climb it, and that is the instrument's cost argument — but it is an
// argument about AUTHORING cost, not about what a serve renders. Parts are
// separate `PracticeItem`s (each files credit at its own capability), they are
// independently scheduled, and nothing in this app sequences a "ladder run" or
// holds session-level stimulus state: part 3 can arrive days after part 1, in a
// different session, with parts 1-2 never served. Showing the stimulus once
// would therefore mean showing it on whichever part happened to come first and
// serving the rest unanswerable — the same silent failure, moved. Repetition is
// the correct behaviour here and must not be "optimized away" without a real
// ladder-run construct to hang it on.

const FRAMED_KINDS = new Set(["error_hunt_worked_solution", "laddered_stem_stimulus"]);

export function ItemPresentation({
  presentation,
  style
}: {
  presentation: ItemPresentationDto;
  style?: CSSProperties;
}) {
  return (
    <div style={style}>
      {presentation.blocks.map((block, index) => (
        <PresentationBlock key={`${block.kind}:${index}`} block={block} />
      ))}
    </div>
  );
}

function PresentationBlock({ block }: { block: PresentationBlockDto }) {
  // The prompt is the item's own voice and gets no chrome — a caption over it
  // would read as an aside about the question rather than as the question.
  if (!FRAMED_KINDS.has(block.kind)) {
    return (
      <div className="markdown" style={{ marginTop: 10 }}>
        <MarkdownMath value={block.markdown} />
      </div>
    );
  }
  return (
    <div
      style={{
        marginTop: 12,
        borderLeft: `2px solid ${COLOR.border}`,
        paddingLeft: 12
      }}
    >
      {block.label ? (
        <Faint
          style={{
            display: "block",
            fontFamily: FONT_MONO,
            fontSize: 10,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            marginBottom: 4
          }}
        >
          {block.label}
        </Faint>
      ) : null}
      <div className="markdown">
        <MarkdownMath value={block.markdown} />
      </div>
    </div>
  );
}
