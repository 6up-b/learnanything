// The detour strip (reader workbench RW1a; UX §4.2, W3): one line between the
// header and the body, only while a detour exists. Every crumb is a button;
// the first is always the reading position from before the detour.
//   ↩ Mixtures ¶3 › why weighted by p? › conditioning on a coin flip   alt+← back
import { COLOR, FONT_MONO } from "../../components/term";
import { hasDetour, type ReturnStack } from "./returnStack";

//
// Reader CA5: a peek at another book's section from the Guide adds a last crumb
// (`› peek Axler §5.A`). It is display only, never a return-stack entry (a peek
// crumb into another book would make Alt+→ open that book); with no detour the
// strip shows for it alone, its first crumb the place the peek came from.
const CRUMB = {
  border: 0, background: "transparent", padding: 0, fontFamily: FONT_MONO, fontSize: 11, overflow: "hidden",
  textOverflow: "ellipsis", maxWidth: 260, textUnderlineOffset: 2,
} as const;

export interface DetourPeekCrumb {
  label: string;
  /** The reading position the peek came from (shown when there is no detour). */
  origin: string;
  /** Closes the peek (Esc does too, on the list). */
  onClose: () => void;
}

export function DetourStrip({ stack, onGoTo, peek = null }: {
  stack: ReturnStack;
  onGoTo: (index: number) => void;
  peek?: DetourPeekCrumb | null;
}) {
  const detour = hasDetour(stack);
  if (!detour && !peek) return null;
  return (
    <nav
      aria-label="Detour"
      style={{
        flexShrink: 0,
        minHeight: 26,
        padding: "4px 32px",
        borderBottom: `1px solid ${COLOR.border}`,
        display: "flex",
        alignItems: "center",
        gap: 6,
        fontFamily: FONT_MONO,
        fontSize: 11,
        color: COLOR.textDim,
        overflow: "hidden",
        whiteSpace: "nowrap",
      }}
    >
      <span aria-hidden="true" style={{ color: COLOR.amber }}>↩</span>
      {!detour && peek ? (
        <button type="button" onClick={peek.onClose} title="back to where I was" style={{ ...CRUMB, color: COLOR.amberLink, textDecoration: "underline", cursor: "pointer" }}>
          {peek.origin}
        </button>
      ) : null}
      {(detour ? stack.entries : []).map((entry, index) => {
        const current = index === stack.cursor;
        return (
          <span key={entry.id} style={{ display: "inline-flex", alignItems: "center", gap: 6, minWidth: 0 }}>
            {index > 0 ? <span aria-hidden="true">›</span> : null}
            <button
              type="button"
              onClick={() => onGoTo(index)}
              aria-current={current ? "location" : undefined}
              title={index === 0 ? "back to where I was" : entry.label}
              style={{
                border: 0,
                background: "transparent",
                padding: 0,
                cursor: current ? "default" : "pointer",
                fontFamily: FONT_MONO,
                fontSize: 11,
                color: current ? COLOR.text : COLOR.amberLink,
                textDecoration: current ? "none" : "underline",
                textUnderlineOffset: 2,
                overflow: "hidden",
                textOverflow: "ellipsis",
                maxWidth: 260,
              }}
            >
              {entry.label}
            </button>
          </span>
        );
      })}
      {peek ? (
        <span data-detour-peek="" style={{ display: "inline-flex", alignItems: "center", gap: 6, minWidth: 0 }}>
          <span aria-hidden="true">›</span>
          <span aria-current="location" style={{ ...CRUMB, color: COLOR.text }}>{peek.label}</span>
        </span>
      ) : null}
      {detour || !peek ? (
        <span style={{ marginLeft: "auto", flexShrink: 0, color: COLOR.textDim }}>alt+← back</span>
      ) : (
        <button type="button" onClick={peek.onClose} style={{ ...CRUMB, marginLeft: "auto", flexShrink: 0, color: COLOR.amberLink, cursor: "pointer" }}>close peek</button>
      )}
    </nav>
  );
}
