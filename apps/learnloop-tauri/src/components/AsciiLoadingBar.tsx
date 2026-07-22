import { useEffect, useState } from "react";
import { COLOR, FONT_MONO } from "./term";

export function AsciiLoadingBar({ width = 30 }: { width?: number }) {
  const [frame, setFrame] = useState(0);

  useEffect(() => {
    const id = window.setInterval(() => setFrame((value) => value + 1), 90);
    return () => window.clearInterval(id);
  }, []);

  const span = Math.max(2, width * 2 - 2);
  const offset = frame % span;
  const position = offset < width ? offset : span - offset;
  const movingRight = offset < width;
  const cells = Array.from({ length: width }, () => "·");
  cells[position] = movingRight ? ">" : "<";
  for (let distance = 1; distance <= 5; distance += 1) {
    const trail = position + (movingRight ? -distance : distance);
    if (trail >= 0 && trail < width) cells[trail] = "=";
  }

  return (
    <div
      role="progressbar"
      aria-label="Import running"
      aria-valuetext="Running"
      style={{
        color: COLOR.cyan,
        fontFamily: FONT_MONO,
        fontSize: 12,
        letterSpacing: "0.04em",
        whiteSpace: "pre",
        overflow: "hidden"
      }}
    >
      <span style={{ color: COLOR.textFaint }}>[</span>
      {cells.join("")}
      <span style={{ color: COLOR.textFaint }}>]</span>
    </div>
  );
}
