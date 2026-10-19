// Reader workbench RW2b: the help ladder (UX §5.5, W6; spec §5.2, §5.5, G37,
// G62, G63). It opens inline below the focused step (never modal, never over
// the learner's work) with all five rungs at once; the suggested rung gets
// ▸ and *suggested (why?)* when the chooser returns, naming its form in plain
// words. Choosing and taking are separate: digits and arrows choose, ↵ takes,
// so a stray key never reveals a worked step, and there is no "are you
// sure?". Every rung states its consequence before it is taken.
import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { COLOR, FONT_MONO } from "../../components/term";
import { quietLink } from "../../components/PlainParts";
import { MeaningLabel } from "../reader/voices";
import { HELP_COPY, chooseKey, suggestedLine } from "./helpModel";
import type { LadderState } from "./useWorkbenchHelp";

export function HelpLadder({
  ladder,
  onChoose,
  onTake,
  onClose,
}: {
  ladder: LadderState;
  onChoose: (level: number) => void;
  onTake: (level: number) => void;
  onClose: () => void;
}) {
  const [whyOpen, setWhyOpen] = useState(false);
  const listRef = useRef<HTMLDivElement | null>(null);
  // Opening the ladder is the learner's own press (Ctrl+H): it takes focus
  // once so the digits and arrows reach it. A suggestion that lands later
  // never moves focus (W12).
  useEffect(() => {
    listRef.current?.focus();
  }, []);
  const suggestion = ladder.suggestion;
  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const next = chooseKey({ chosen: ladder.chosen }, event.key);
    if (next === null) return;
    event.preventDefault();
    event.stopPropagation();
    if (next === "take") onTake(ladder.chosen);
    else if (next === "close") onClose();
    else onChoose(next.chosen);
  };
  return (
    <div
      ref={listRef}
      role="listbox"
      aria-label="help ladder"
      aria-activedescendant={`ladder-rung-${ladder.chosen}`}
      tabIndex={0}
      data-testid="help-ladder"
      onKeyDown={onKeyDown}
      style={{ border: `1px solid ${COLOR.border}`, padding: "6px 8px", display: "flex", flexDirection: "column", gap: 3,
        fontFamily: FONT_MONO, fontSize: 11, outline: "none", marginTop: 4 }}
    >
      <div style={{ display: "flex", gap: 8, alignItems: "baseline", flexWrap: "wrap" }}>
        <span style={{ color: COLOR.textFaint, letterSpacing: "0.1em" }}>{HELP_COPY.ladderTitle}</span>
        {suggestion ? (
          <span data-testid="ladder-suggested">
            <MeaningLabel>{`▸ ${suggestedLine(suggestion)}`}</MeaningLabel>{" "}
            <button type="button" style={{ ...quietLink, fontSize: 10 }} aria-expanded={whyOpen} onClick={() => setWhyOpen((open) => !open)}>
              ({HELP_COPY.why})
            </button>
          </span>
        ) : ladder.pending ? null : null}
      </div>
      {whyOpen && suggestion ? (
        <div data-testid="ladder-why">
          <MeaningLabel>{suggestion.why}</MeaningLabel>
          {suggestion.split ? <div><MeaningLabel>{suggestion.split}</MeaningLabel></div> : null}
        </div>
      ) : null}
      {ladder.rungs.map((rung) => {
        const chosen = ladder.chosen === rung.level;
        const suggested = suggestion?.level === rung.level;
        return (
          <div
            key={rung.level}
            id={`ladder-rung-${rung.level}`}
            role="option"
            aria-selected={chosen}
            data-testid={`ladder-rung-${rung.level}`}
            data-suggested={suggested ? "true" : undefined}
            onClick={() => onChoose(rung.level)}
            onDoubleClick={() => onTake(rung.level)}
            style={{ display: "flex", gap: 8, alignItems: "baseline", cursor: "pointer",
              color: chosen ? COLOR.text : COLOR.textDim, background: chosen ? COLOR.washAmber : "transparent", padding: "1px 2px" }}
          >
            <span aria-hidden="true" style={{ width: 10 }}>{suggested ? "▸" : ""}</span>
            <span>{rung.level}</span>
            <span style={{ flex: 1 }}>
              {rung.label}
              {rung.discriminating ? <span> · {HELP_COPY.notGraded}</span> : null}
            </span>
            <MeaningLabel>{rung.consequence}</MeaningLabel>
          </div>
        );
      })}
      {ladder.notice ? <MeaningLabel>{ladder.notice}</MeaningLabel> : null}
      <div style={{ display: "flex", gap: 8, alignItems: "baseline" }}>
        <MeaningLabel>{HELP_COPY.chooseTake}</MeaningLabel>
        <button type="button" style={{ ...quietLink, fontSize: 10, marginLeft: "auto" }} onClick={() => onTake(ladder.chosen)}>
          take {ladder.chosen} ↵
        </button>
      </div>
    </div>
  );
}
