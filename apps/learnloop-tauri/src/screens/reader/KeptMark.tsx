// RW4d (spec §7.8; UX §3.4): ⇄ in the margin beside a passage with a
// comparison the learner kept. The learner's own mark (like ? and ✎): it is
// outside the cue budget and never counted by the density setting. Pressing
// it reopens the kept table under the passage (no model call); Esc or
// *close* folds it again. Nothing opens, moves focus or animates unasked.
//
// A passage in more than one kept comparison lists them all, each by its
// question and its date, and opens the one picked (Codex review F9). On the
// original PDF the mark sits in the page's overlay gutter (below a cue mark
// when the passage has one) and the table opens beside it (Codex review F10).
import { useState } from "react";
import type { KeptMarkDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { KeptComparisonView, shortDate } from "./CompareKeep";
import { CompareTable } from "./LibraryAnswer";

type KeptEntry = NonNullable<KeptMarkDto["comparisons"]>[number];

function entriesOf(mark: KeptMarkDto): KeptEntry[] {
  if (mark.comparisons?.length) return mark.comparisons;
  return mark.askIds.map((askId) => ({ askId, keptAt: mark.keptAt, query: null, otherSources: mark.otherSources }));
}

export function KeptMark({ mark, surface = "text", below = false }: { mark: KeptMarkDto; surface?: "text" | "pdf"; below?: boolean }) {
  const [open, setOpen] = useState(false);
  const entries = entriesOf(mark);
  const many = entries.length > 1;
  const [chosen, setChosen] = useState<string | null>(null);
  const current = many ? (entries.some((entry) => entry.askId === chosen) ? chosen : null) : (entries[0]?.askId ?? null);
  const others = mark.otherSources.join(", ") || "another source";
  const when = shortDate(mark.keptAt);
  const onPage = surface === "pdf";
  const label = many
    ? `${entries.length} comparisons you kept on this passage: ${open ? "close them" : "choose one"}`
    : `a comparison you kept with ${others}${when ? ` on ${when}` : ""}: ${open ? "close it" : "reopen it"}`;
  const body = open ? (
    <div
      data-kept-mark-panel={mark.spanId}
      onClick={(event) => event.stopPropagation()}
      style={onPage
        ? { position: "absolute", left: 24, top: 0, width: 520, maxHeight: "70vh", overflowY: "auto", zIndex: 30, background: COLOR.bg, border: `1px solid ${COLOR.border}`, padding: "4px 8px" }
        : undefined}
    >
      {many ? (
        <div data-kept-choices="" style={{ display: "flex", flexDirection: "column", gap: 2, padding: "4px 0" }}>
          {entries.map((entry) => {
            const date = shortDate(entry.keptAt);
            const withWhom = entry.otherSources.join(", ") || "another source";
            return (
              <button
                key={entry.askId}
                type="button"
                aria-pressed={current === entry.askId}
                onClick={() => setChosen(current === entry.askId ? null : entry.askId)}
                style={{ border: 0, background: "transparent", textAlign: "left", color: current === entry.askId ? COLOR.amber : COLOR.amberLink, fontFamily: FONT_MONO, fontSize: 11, padding: 0, cursor: "pointer" }}
              >
                {entry.query ? `“${entry.query}”` : "a comparison"} · with {withWhom}{date ? ` · ${date}` : ""}
              </button>
            );
          })}
        </div>
      ) : null}
      {current ? <KeptComparisonView key={current} askId={current} onClose={() => setOpen(false)} Table={CompareTable} /> : null}
    </div>
  ) : null;
  const button = (
    <button
      type="button"
      data-kept-mark={mark.spanId}
      aria-expanded={open}
      aria-label={label}
      title={many ? `${entries.length} comparisons you kept` : `a comparison you kept · ${others}`}
      onClick={(event) => {
        event.stopPropagation();
        setOpen((value) => !value);
      }}
      onKeyDown={(event) => {
        if (event.key === "Escape" && open) {
          event.stopPropagation();
          setOpen(false);
        }
      }}
      style={onPage
        ? { width: 20, height: 20, padding: 0, border: `1px solid ${COLOR.border}`, background: COLOR.bg, color: COLOR.amber, fontFamily: FONT_MONO, fontSize: 12, lineHeight: "18px", cursor: "pointer" }
        : { position: "absolute", left: -22, top: 18, border: 0, background: "transparent", color: COLOR.amber, fontFamily: FONT_MONO, fontSize: 12, padding: 0, cursor: "pointer" }}
    >
      ⇄
    </button>
  );
  if (onPage) {
    // The overlay gutter places the slot; a cue mark, when there is one, sits above.
    return (
      <span
        data-kept-slot={mark.spanId}
        style={{ position: "absolute", left: 0, top: below ? 22 : 0, zIndex: open ? 30 : 4 }}
        onMouseDown={(event) => event.stopPropagation()}
        onMouseUp={(event) => event.stopPropagation()}
      >
        {button}
        {body}
      </span>
    );
  }
  return (
    <>
      {button}
      {body}
    </>
  );
}
