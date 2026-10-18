// Reader workbench RW2b: the help style in the workbench header (UX §5.11,
// W5; spec D31): let me struggle · balanced · guide me, for this problem
// only; the stored preference is the default and Settings changes it. It
// changes only which rung is suggested; every rung stays available.
import type { HelpStyle } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { HELP_COPY, STYLE_OPTIONS } from "./helpModel";

export function HelpStyleControl({
  value,
  stored,
  disabled,
  onChange,
}: {
  /** This problem's style, or null to follow the stored preference. */
  value: HelpStyle | null;
  stored: HelpStyle;
  disabled?: boolean;
  onChange: (style: HelpStyle | null) => void;
}) {
  const effective = value ?? stored;
  return (
    <span role="radiogroup" aria-label="help style for this problem" data-testid="workbench-help-style"
      style={{ display: "inline-flex", gap: 4, alignItems: "baseline", fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
      <span>{HELP_COPY.styleLabel}</span>
      {STYLE_OPTIONS.map((option, index) => {
        const checked = effective === option.value;
        return (
          <span key={option.value}>
            {index > 0 ? <span aria-hidden="true"> · </span> : null}
            <button
              type="button"
              role="radio"
              aria-checked={checked}
              aria-disabled={disabled}
              title={option.line}
              onClick={() => {
                if (disabled || checked) return;
                // The stored preference again means "follow it" (no override).
                onChange(option.value === stored ? null : option.value);
              }}
              style={{ border: 0, background: "transparent", padding: 0, cursor: "pointer", fontFamily: FONT_MONO, fontSize: 11,
                color: checked ? COLOR.text : COLOR.textDim }}
            >
              {checked ? `[${option.label}]` : option.label}
            </button>
          </span>
        );
      })}
    </span>
  );
}
