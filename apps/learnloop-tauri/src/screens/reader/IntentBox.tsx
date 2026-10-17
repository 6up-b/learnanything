// The intent box (reader workbench RW1b; spec §4.2; UX §4.1, W2): a small box
// under the selection -- "what do you want to do with this?" -- with its key row,
// the routed line once an action is chosen (with "change"), the model-action
// states (W14) and, on Tab, the palette grouped by the five intentions plus Mark.
// Presentational: useIntentBox owns the behaviour. No animation, no modal, and
// focus moves only on the learner's key (W12).
import { COLOR, FONT_MONO } from "../../components/term";
import type { ReaderIntentActionDto } from "../../api/dto";
import { INTENT_COPY, routedLine } from "./intentPalette";
import { ModelActionState } from "./ModelActionState";
import type { IntentBoxController } from "./useIntentBox";
import { LearnerQuote, MeaningLabel } from "./voices";

const linkStyle = {
  border: 0,
  background: "transparent",
  color: COLOR.amberLink,
  fontFamily: FONT_MONO,
  fontSize: 11,
  padding: 0,
  cursor: "pointer",
  textDecoration: "underline",
  textUnderlineOffset: 2,
} as const;

export function IntentBox({ box }: { box: IntentBoxController }) {
  if (!box.open || !box.position) return null;
  const { position, routed, phase } = box;
  const words = box.text.trim();
  return (
    <div
      ref={box.boxRef}
      data-intent-box=""
      data-above={position.above ? "" : undefined}
      // The box sits over the text column without taking it over (U2): a
      // learner-requested element, closed by Esc or a click elsewhere.
      style={{
        position: "absolute", zIndex: 30, top: position.top, left: position.left, width: 360, boxSizing: "border-box",
        background: COLOR.bgElev, border: `1px solid ${COLOR.border}`, padding: "6px 8px", display: "flex",
        flexDirection: "column", gap: 4, fontFamily: FONT_MONO, fontSize: 12,
      }}
      onMouseUp={(event) => event.stopPropagation()}
    >
      {routed ? (
        <>
          <span style={{ color: COLOR.text }}>
            <span aria-hidden="true">› </span>
            <LearnerQuote>{words}</LearnerQuote>
          </span>
          <div role="status" aria-live="polite" style={{ display: "flex", gap: 8, alignItems: "baseline", color: COLOR.textDim }}>
            <span>→ {routedLine(routed.action)}</span>
            {routed.reason && routed.action.id === "ask" ? (
              <MeaningLabel style={{ fontSize: 10 }}>(LearnLoop's model couldn't choose, so this asks)</MeaningLabel>
            ) : null}
            <button type="button" onClick={box.change} style={{ ...linkStyle, marginLeft: "auto" }}>{INTENT_COPY.change}</button>
          </div>
        </>
      ) : (
        <>
          <input
            ref={box.inputRef}
            aria-label={INTENT_COPY.label}
            placeholder={INTENT_COPY.placeholder}
            value={box.text}
            onChange={(event) => box.setText(event.target.value)}
            disabled={phase === "pending"}
            style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: "4px 6px" }}
          />
          {phase === "pending" ? (
            <ModelActionState phase="pending" verb={INTENT_COPY.routing} onCancel={box.close} />
          ) : phase === "offline" ? (
            <ModelActionState phase="offline" verb={INTENT_COPY.routing} />
          ) : box.protectedSelection && words ? (
            <MeaningLabel style={{ fontSize: 10 }}>{INTENT_COPY.protected}</MeaningLabel>
          ) : (
            <span style={{ display: "flex", gap: 8, color: COLOR.textDim, fontSize: 10 }}>
              <span>{INTENT_COPY.keys}</span>
              <span style={{ marginLeft: "auto" }} title={INTENT_COPY.whereThisGoes}>ⓘ where this goes</span>
            </span>
          )}
        </>
      )}
      {box.paletteOpen ? <IntentPalette box={box} /> : null}
    </div>
  );
}

function IntentPalette({ box }: { box: IntentBoxController }) {
  return (
    <div role="group" aria-label={INTENT_COPY.paletteLabel} style={{ display: "flex", flexDirection: "column", gap: 4, borderTop: `1px solid ${COLOR.border}`, paddingTop: 4 }}>
      {box.groups.map((group) => (
        <div key={group.group} style={{ display: "flex", gap: 8, alignItems: "baseline" }}>
          <h3 style={{ margin: 0, minWidth: 92, fontFamily: FONT_MONO, fontSize: 9, letterSpacing: "0.12em", color: COLOR.textDim, fontWeight: 400, textTransform: "none" }}>
            {group.label}
          </h3>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "2px 10px" }}>
            {group.actions.map((action: ReaderIntentActionDto) => (
              <button key={action.id} type="button" data-intent-action={action.id} onClick={() => box.pick(action)} style={linkStyle}>
                {action.label}
              </button>
            ))}
          </div>
        </div>
      ))}
      <MeaningLabel style={{ fontSize: 10 }}>{INTENT_COPY.paletteKeys}</MeaningLabel>
    </div>
  );
}
