import type { CSSProperties } from "react";
import { COLOR, Faint, FONT_MONO } from "./term";

export function pageSelectionError(value: string): string | null {
  const text = value.trim();
  if (!text) return null;
  for (const rawSegment of text.split(",")) {
    const segment = rawSegment.trim();
    if (!segment) return "Remove the empty page segment.";
    const match = /^(\d+)(?:\s*-\s*(\d+))?$/.exec(segment);
    if (!match) return `“${segment}” must be a page or range such as 36 or 3-27.`;
    const start = Number(match[1]);
    const end = Number(match[2] ?? match[1]);
    if (start < 1 || end < 1) return "Pages must be positive whole numbers.";
    if (start > end) return `Range ${start}-${end} runs backwards.`;
  }
  return null;
}

export function PageRangeSelector({
  value,
  onChange,
  disabled = false,
  compact = false
}: {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  compact?: boolean;
}) {
  const error = pageSelectionError(value);
  const field: CSSProperties = {
    width: compact ? 190 : 280,
    padding: compact ? "5px 8px" : "7px 9px",
    border: `1px solid ${error ? COLOR.red : COLOR.border}`,
    background: COLOR.bgInput,
    color: COLOR.text,
    outline: "none",
    fontFamily: FONT_MONO,
    fontSize: 12,
    opacity: disabled ? 0.55 : 1
  };
  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        <Faint style={{ fontSize: 12 }}>PDF pages</Faint>
        <input
          type="text"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={(event) => event.stopPropagation()}
          placeholder="3-27, 29-33, 36"
          aria-label="PDF page selection"
          disabled={disabled}
          style={field}
        />
        <Faint style={{ fontSize: 11 }}>optional · inclusive · commas skip pages</Faint>
      </div>
      {error ? <div style={{ color: COLOR.red, fontSize: 11, marginTop: 4 }}>{error}</div> : null}
    </div>
  );
}
