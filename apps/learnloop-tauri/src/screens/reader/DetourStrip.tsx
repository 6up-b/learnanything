// The detour strip (reader workbench RW1a; UX §4.2, W3): one line between the
// header and the body, only while a detour exists. Every crumb is a button;
// the first is always the reading position from before the detour.
//   ↩ Mixtures ¶3 › why weighted by p? › conditioning on a coin flip   alt+← back
import { COLOR, FONT_MONO } from "../../components/term";
import { hasDetour, type ReturnStack } from "./returnStack";

export function DetourStrip({ stack, onGoTo }: { stack: ReturnStack; onGoTo: (index: number) => void }) {
  if (!hasDetour(stack)) return null;
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
      {stack.entries.map((entry, index) => {
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
      <span style={{ marginLeft: "auto", flexShrink: 0, color: COLOR.textDim }}>alt+← back</span>
    </nav>
  );
}
