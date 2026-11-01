// Reader RW5d P2: the display-list renderer (spec_reader_show_me_figures_v1 §9.1).
//
// Draws a validated Scene (sketchScene.ts) as SVG primitives: polylines,
// polygons, points, segments, arrows, circles, rects, heat cells and text,
// each from its fields only (text is a text node, never markup; colours come
// from a closed palette; no element can carry a URL, an image or a style
// string). A handle is a draggable point bound to one or two parameters:
// dragging sets those parameters, within their ranges, through the host's
// own controls; the program never sees a pointer event.
import { useRef, type CSSProperties, type PointerEvent } from "react";
import { COLOR, FONT_MONO } from "../../../../components/term";
import type { Scene, SketchColor, SketchElement, SketchStyle } from "./sketchScene";

export const SCENE_W = 600;
export const SCENE_H = 300;
const PAD = { left: 40, right: 12, top: 10, bottom: 28 };

const PALETTE: Record<SketchColor, string> = {
  series0: COLOR.cyan,
  series1: COLOR.amber,
  series2: COLOR.green,
  series3: COLOR.pink,
  muted: COLOR.textDim,
  accent: COLOR.purpleText,
};

export type Scale = { x: (value: number) => number; y: (value: number) => number; invert: (px: number, py: number) => [number, number] };

export function sceneScale(scene: Scene): Scale {
  const [x0, x1] = scene.viewport.x;
  const [y0, y1] = scene.viewport.y;
  const width = SCENE_W - PAD.left - PAD.right;
  const height = SCENE_H - PAD.top - PAD.bottom;
  return {
    x: (value) => PAD.left + ((value - x0) / (x1 - x0)) * width,
    y: (value) => PAD.top + (1 - (value - y0) / (y1 - y0)) * height,
    invert: (px, py) => [x0 + ((px - PAD.left) / width) * (x1 - x0), y0 + (1 - (py - PAD.top) / height) * (y1 - y0)],
  };
}

function stroke(style: SketchStyle | undefined, fallback: SketchColor = "series0") {
  const color = PALETTE[style?.color ?? fallback] ?? PALETTE[fallback];
  return {
    stroke: color,
    strokeWidth: Math.min(3, Math.max(0.5, style?.width ?? 1.5)),
    strokeDasharray: style?.dash ? "6 4" : undefined,
    opacity: style?.opacity ?? 1,
  };
}

function cellColor(value: number, low: number, high: number): string {
  const share = high > low ? (value - low) / (high - low) : 0.5;
  const percent = Math.round(Math.min(1, Math.max(0, share)) * 100);
  return `color-mix(in srgb, ${COLOR.cyan} ${percent}%, ${COLOR.bgElev})`;
}

function Element({ element, scale, index }: { element: SketchElement; scale: Scale; index: number }) {
  const key = element.type === "handle" ? element.id : `${element.type}-${index}`;
  switch (element.type) {
    case "polyline":
    case "polygon": {
      const points = element.x.map((x, i) => `${scale.x(x)},${scale.y(element.y[i])}`).join(" ");
      const paint = stroke(element.style);
      if (element.type === "polygon") {
        return <polygon key={key} data-sketch-element={element.id ?? element.type} points={points} {...paint}
          fill={element.style?.fill ? paint.stroke : "none"} fillOpacity={element.style?.fill ? 0.25 : undefined} />;
      }
      return <polyline key={key} data-sketch-element={element.id ?? element.type} points={points} fill="none" {...paint} />;
    }
    case "points": {
      const paint = stroke(element.style);
      const r = element.r ?? 2;
      return (
        <g key={key} data-sketch-element={element.id ?? element.type} fill={paint.stroke} opacity={paint.opacity}>
          {element.x.map((x, i) => <circle key={i} cx={scale.x(x)} cy={scale.y(element.y[i])} r={r} />)}
        </g>
      );
    }
    case "segment":
    case "arrow":
      return <line key={key} data-sketch-element={element.id ?? element.type} x1={scale.x(element.x1)} y1={scale.y(element.y1)}
        x2={scale.x(element.x2)} y2={scale.y(element.y2)} {...stroke(element.style)}
        markerEnd={element.type === "arrow" ? "url(#sketch-arrow)" : undefined} />;
    case "circle": {
      const rx = Math.abs(scale.x(element.cx + element.r) - scale.x(element.cx));
      const ry = Math.abs(scale.y(element.cy + element.r) - scale.y(element.cy));
      const paint = stroke(element.style);
      return <ellipse key={key} data-sketch-element={element.id ?? element.type} cx={scale.x(element.cx)} cy={scale.y(element.cy)}
        rx={rx} ry={ry} {...paint} fill={element.style?.fill ? paint.stroke : "none"} fillOpacity={element.style?.fill ? 0.25 : undefined} />;
    }
    case "rect": {
      const left = scale.x(element.x);
      const right = scale.x(element.x + element.w);
      const top = scale.y(element.y + element.h);
      const bottom = scale.y(element.y);
      const paint = stroke(element.style, "muted");
      return <rect key={key} data-sketch-element={element.id ?? element.type} x={Math.min(left, right)} y={Math.min(top, bottom)}
        width={Math.abs(right - left)} height={Math.abs(bottom - top)} {...paint}
        fill={element.style?.fill ? paint.stroke : "none"} fillOpacity={element.style?.fill ? 0.25 : undefined} />;
    }
    case "text":
      // The model's words, drawn as a text node in the model's voice (italic), inside the frame.
      return <text key={key} data-sketch-element={element.id ?? element.type} data-sketch-text="" x={scale.x(element.x)} y={scale.y(element.y)}
        fill={PALETTE[element.style?.color ?? "muted"]} fontFamily={FONT_MONO} fontSize={10} fontStyle="italic">{element.text}</text>;
    case "heat_cells": {
      const low = Math.min(...element.values);
      const high = Math.max(...element.values);
      const cw = (element.x[1] - element.x[0]) / element.cols;
      const ch = (element.y[1] - element.y[0]) / element.rows;
      return (
        <g key={key} data-sketch-element={element.id ?? element.type}>
          {element.values.map((value, i) => {
            const col = i % element.cols;
            const row = Math.floor(i / element.cols);
            const x = element.x[0] + col * cw;
            const y = element.y[1] - (row + 1) * ch;
            const left = scale.x(x);
            const top = scale.y(y + ch);
            return <rect key={i} x={left} y={top} width={Math.abs(scale.x(x + cw) - left)} height={Math.abs(scale.y(y) - top)}
              fill={cellColor(value, low, high)} />;
          })}
        </g>
      );
    }
    default:
      return null;
  }
}

export function SketchSceneView({
  scene,
  onHandle,
  label,
}: {
  scene: Scene;
  /** A handle dragged to data coordinates (x, y): the host sets its bound parameters. */
  onHandle?: (id: string, x: number, y: number) => void;
  label?: string;
}) {
  const scale = sceneScale(scene);
  const svg = useRef<SVGSVGElement | null>(null);
  const dragging = useRef<string | null>(null);
  const toData = (event: PointerEvent<SVGElement>): [number, number] | null => {
    const node = svg.current;
    if (!node) return null;
    const box = node.getBoundingClientRect();
    const px = box.width ? ((event.clientX - box.left) / box.width) * SCENE_W : event.clientX;
    const py = box.height ? ((event.clientY - box.top) / box.height) * SCENE_H : event.clientY;
    return scale.invert(px, py);
  };
  const svgStyle: CSSProperties = { width: "100%", maxWidth: SCENE_W, height: "auto", background: COLOR.bg, touchAction: "none" };
  const handles = scene.elements.filter((element): element is Extract<SketchElement, { type: "handle" }> => element.type === "handle");
  return (
    <svg ref={svg} viewBox={`0 0 ${SCENE_W} ${SCENE_H}`} style={svgStyle} role="img" aria-label={label ?? "simulation"} data-sketch-scene=""
      onPointerMove={(event) => {
        if (!dragging.current || !onHandle) return;
        const point = toData(event);
        if (point) onHandle(dragging.current, point[0], point[1]);
      }}
      onPointerUp={() => { dragging.current = null; }}
      onPointerLeave={() => { dragging.current = null; }}>
      <defs>
        <marker id="sketch-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill={COLOR.textDim} />
        </marker>
      </defs>
      <rect x={PAD.left} y={PAD.top} width={SCENE_W - PAD.left - PAD.right} height={SCENE_H - PAD.top - PAD.bottom}
        fill="none" stroke={COLOR.border} />
      {scene.elements.map((element, index) => (element.type === "handle" ? null : <Element key={index} element={element} scale={scale} index={index} />))}
      {handles.map((handle) => (
        <circle key={handle.id} data-sketch-handle={handle.id} cx={scale.x(handle.x)} cy={scale.y(handle.y)} r={7}
          fill={COLOR.bgElev} stroke={COLOR.amber} strokeWidth={2} style={{ cursor: "grab" }} tabIndex={0}
          aria-label={`drag to set ${Object.values(handle.binds).join(" and ")}`}
          onPointerDown={(event) => {
            dragging.current = handle.id;
            (event.target as Element & { setPointerCapture?: (id: number) => void }).setPointerCapture?.(event.pointerId);
          }} />
      ))}
      {scene.axes?.x_label ? (
        <text x={SCENE_W / 2} y={SCENE_H - 6} textAnchor="middle" fill={COLOR.textDim} fontFamily={FONT_MONO} fontSize={10}>{scene.axes.x_label}</text>
      ) : null}
      {scene.axes?.y_label ? (
        <text x={10} y={SCENE_H / 2} textAnchor="middle" fill={COLOR.textDim} fontFamily={FONT_MONO} fontSize={10}
          transform={`rotate(-90 10 ${SCENE_H / 2})`}>{scene.axes.y_label}</text>
      ) : null}
    </svg>
  );
}
