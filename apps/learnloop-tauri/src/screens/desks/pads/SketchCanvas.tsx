// A sketch block (spec §10.8): the learner's SVG canvas on a 20 px grid, "sketch · yours". Every tool works:
// pen (smoothed paths, with pressure from a pen), line, arrow, box, text and eraser; drawing within 16 px of
// the bottom grows the canvas by 60 px. Stored as typed shapes in the block's payload; LearnLoop never draws
// here and never reads a sketch for grading.
import { useRef, useState } from "react";

export type SketchTool = "pen" | "line" | "arrow" | "box" | "text" | "eraser";

export type SketchItem =
  | { type: "path"; d: string; w: number }
  | { type: "line" | "arrow"; x1: number; y1: number; x2: number; y2: number }
  | { type: "box"; x: number; y: number; w: number; h: number }
  | { type: "text"; x: number; y: number; text: string };

export interface SketchPayload {
  width: number;
  height: number;
  items: SketchItem[];
}

export const SKETCH_SIZES = { grid: 20, growWithin: 16, growBy: 60, minHeight: 160 } as const;

export const SKETCH_TOOLS: Array<{ tool: SketchTool; label: string }> = [
  { tool: "pen", label: "✎ pen" },
  { tool: "line", label: "／ line" },
  { tool: "arrow", label: "→ arrow" },
  { tool: "box", label: "▭ box" },
  { tool: "text", label: "T text" },
  { tool: "eraser", label: "⌫ eraser" },
];

export function readSketch(payload: Record<string, unknown>): SketchPayload {
  const items = Array.isArray(payload.items) ? (payload.items as SketchItem[]) : [];
  return {
    width: typeof payload.width === "number" ? payload.width : 480,
    height: typeof payload.height === "number" ? Math.max(SKETCH_SIZES.minHeight, payload.height) : SKETCH_SIZES.minHeight,
    items,
  };
}

/** Points smoothed into a path: quadratic curves through the midpoints of successive points. */
export function smoothPath(points: Array<{ x: number; y: number }>): string {
  if (points.length === 0) return "";
  if (points.length < 3) return `M${points.map((p) => `${round(p.x)} ${round(p.y)}`).join(" L")}`;
  let d = `M${round(points[0].x)} ${round(points[0].y)}`;
  for (let i = 1; i < points.length - 1; i += 1) {
    const mid = { x: (points[i].x + points[i + 1].x) / 2, y: (points[i].y + points[i + 1].y) / 2 };
    d += ` Q${round(points[i].x)} ${round(points[i].y)} ${round(mid.x)} ${round(mid.y)}`;
  }
  const last = points[points.length - 1];
  return `${d} L${round(last.x)} ${round(last.y)}`;
}

function round(value: number): number {
  return Math.round(value * 10) / 10;
}

/** Whether an item lies under a point (the eraser's hit test). */
export function hits(item: SketchItem, x: number, y: number, within = 8): boolean {
  switch (item.type) {
    case "box":
      return x >= item.x - within && x <= item.x + item.w + within && y >= item.y - within && y <= item.y + item.h + within;
    case "text":
      return x >= item.x - within && x <= item.x + item.text.length * 8 + within && y >= item.y - 16 && y <= item.y + within;
    case "line":
    case "arrow": {
      const dx = item.x2 - item.x1;
      const dy = item.y2 - item.y1;
      const length = dx * dx + dy * dy || 1;
      const t = Math.max(0, Math.min(1, ((x - item.x1) * dx + (y - item.y1) * dy) / length));
      return Math.hypot(item.x1 + t * dx - x, item.y1 + t * dy - y) <= within;
    }
    case "path": {
      const numbers = item.d.match(/-?\d+(\.\d+)?/g)?.map(Number) ?? [];
      for (let i = 0; i + 1 < numbers.length; i += 2) if (Math.hypot(numbers[i] - x, numbers[i + 1] - y) <= within + item.w) return true;
      return false;
    }
  }
}

export function SketchCanvas({ payload, editable, onCommit, onTextPrompt }: {
  payload: Record<string, unknown>;
  editable: boolean;
  onCommit: (next: SketchPayload) => void;
  /** Asks for a text label (a prompt in the app; tests answer it directly). */
  onTextPrompt?: () => string | null;
}) {
  const sketch = readSketch(payload);
  const [tool, setTool] = useState<SketchTool>("pen");
  const [draft, setDraft] = useState<SketchItem | null>(null);
  const [height, setHeight] = useState(sketch.height);
  const points = useRef<Array<{ x: number; y: number }>>([]);
  const start = useRef<{ x: number; y: number } | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const pressure = useRef(1);

  const at = (event: React.PointerEvent): { x: number; y: number } => {
    const box = svgRef.current?.getBoundingClientRect();
    return { x: event.clientX - (box?.left ?? 0), y: event.clientY - (box?.top ?? 0) };
  };
  const grow = (y: number) => {
    if (y >= height - SKETCH_SIZES.growWithin) setHeight((now) => now + SKETCH_SIZES.growBy);
  };
  const commit = (items: SketchItem[], nextHeight = height) => onCommit({ width: sketch.width, height: nextHeight, items });

  const onDown = (event: React.PointerEvent<SVGSVGElement>) => {
    if (!editable) return;
    const p = at(event);
    event.currentTarget.setPointerCapture?.(event.pointerId);
    pressure.current = event.pointerType === "pen" && event.pressure > 0 ? event.pressure : 0.5;
    if (tool === "eraser") {
      const kept = sketch.items.filter((item) => !hits(item, p.x, p.y));
      if (kept.length !== sketch.items.length) commit(kept);
      return;
    }
    if (tool === "text") {
      const text = onTextPrompt ? onTextPrompt() : typeof window !== "undefined" ? window.prompt("text") : null;
      if (text) commit([...sketch.items, { type: "text", x: p.x, y: p.y, text }]);
      return;
    }
    start.current = p;
    points.current = [p];
  };
  const onMove = (event: React.PointerEvent<SVGSVGElement>) => {
    const s = start.current;
    if (!s) return;
    const p = at(event);
    grow(p.y);
    if (tool === "pen") {
      points.current.push(p);
      setDraft({ type: "path", d: smoothPath(points.current), w: 1.2 + 2 * pressure.current });
    } else if (tool === "line" || tool === "arrow") {
      setDraft({ type: tool, x1: s.x, y1: s.y, x2: p.x, y2: p.y });
    } else if (tool === "box") {
      setDraft({ type: "box", x: Math.min(s.x, p.x), y: Math.min(s.y, p.y), w: Math.abs(p.x - s.x), h: Math.abs(p.y - s.y) });
    }
  };
  const onUp = () => {
    start.current = null;
    if (draft) commit([...sketch.items, draft]);
    setDraft(null);
    points.current = [];
  };

  const drawn = draft ? [...sketch.items, draft] : sketch.items;
  return (
    <div className="desk-sketch" data-sketch="">
      <div className="bar">
        <span className="who">sketch · yours</span>
        {editable ? SKETCH_TOOLS.map((each) => (
          <button key={each.tool} type="button" className={tool === each.tool ? "on" : ""} aria-pressed={tool === each.tool} onClick={() => setTool(each.tool)}>{each.label}</button>
        )) : null}
      </div>
      <svg
        ref={svgRef}
        width="100%"
        height={height}
        viewBox={`0 0 ${sketch.width} ${height}`}
        preserveAspectRatio="xMinYMin meet"
        className={`canvas tool-${tool}`}
        role="img"
        aria-label="your sketch"
        onPointerDown={onDown}
        onPointerMove={onMove}
        onPointerUp={onUp}
        onPointerCancel={onUp}
      >
        <defs>
          <pattern id="desk-sketch-grid" width={SKETCH_SIZES.grid} height={SKETCH_SIZES.grid} patternUnits="userSpaceOnUse">
            <path d={`M ${SKETCH_SIZES.grid} 0 L 0 0 0 ${SKETCH_SIZES.grid}`} fill="none" stroke="#ece8df" strokeWidth="1" />
          </pattern>
          <marker id="desk-sketch-arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
            <path d="M0 0 L10 4 L0 8 z" fill="#2b4fa8" />
          </marker>
        </defs>
        <rect width="100%" height="100%" fill="url(#desk-sketch-grid)" />
        {drawn.map((item, index) => {
          switch (item.type) {
            case "path":
              return <path key={index} d={item.d} fill="none" stroke="#2b4fa8" strokeWidth={item.w} strokeLinecap="round" strokeLinejoin="round" />;
            case "line":
            case "arrow":
              return <line key={index} x1={item.x1} y1={item.y1} x2={item.x2} y2={item.y2} stroke="#2b4fa8" strokeWidth="2" markerEnd={item.type === "arrow" ? "url(#desk-sketch-arrow)" : undefined} />;
            case "box":
              return <rect key={index} x={item.x} y={item.y} width={item.w} height={item.h} fill="none" stroke="#2b4fa8" strokeWidth="2" rx="2" />;
            case "text":
              return <text key={index} x={item.x} y={item.y} fill="#2b4fa8" fontFamily="Caveat Variable, Caveat, cursive" fontSize="18">{item.text}</text>;
          }
          return null;
        })}
      </svg>
    </div>
  );
}
