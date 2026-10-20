// RW4d (spec §7.8; UX §3.4): ⇄ in the margin beside a passage with a
// comparison the learner kept. The learner's own mark (like ? and ✎): it is
// outside the cue budget and never counted by the density setting. Pressing
// it reopens the kept table under the passage (no model call); Esc or
// *close* folds it again. Nothing opens, moves focus or animates unasked.
import { useState } from "react";
import type { KeptMarkDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { KeptComparisonView, shortDate } from "./CompareKeep";
import { CompareTable } from "./LibraryAnswer";

export function KeptMark({ mark }: { mark: KeptMarkDto }) {
  const [open, setOpen] = useState(false);
  const others = mark.otherSources.join(", ") || "another source";
  const when = shortDate(mark.keptAt);
  return (
    <>
      <button
        type="button"
        data-kept-mark={mark.spanId}
        aria-expanded={open}
        aria-label={`a comparison you kept with ${others}${when ? ` on ${when}` : ""}: ${open ? "close it" : "reopen it"}`}
        title={`a comparison you kept · ${others}`}
        onClick={(event) => {
          event.stopPropagation();
          setOpen((value) => !value);
        }}
        style={{ position: "absolute", left: -22, top: 18, border: 0, background: "transparent", color: COLOR.amber, fontFamily: FONT_MONO, fontSize: 12, padding: 0, cursor: "pointer" }}
      >
        ⇄
      </button>
      {open ? (
        <div onClick={(event) => event.stopPropagation()}>
          <KeptComparisonView askId={mark.askIds[0]} onClose={() => setOpen(false)} Table={CompareTable} />
        </div>
      ) : null}
    </>
  );
}
