// Ink in pads (spec §10.10, "Freewrite pads"): each ink line is an `ink` block holding its strokes and its
// transcription. The line's surface takes the pen (its own strokes, the barrel erasing them); a new line starts on
// the pad's last row; the transcription shows under the line as "read as …", labelled as what it is: LearnLoop's
// reading, which may be wrong, until the learner fixes it (a new version, "you corrected the transcription").
//
// Today's default route reads no images: the line then says plainly that handwriting can't be read yet, keeps the
// ink, and lets the learner type what they wrote.
import { useEffect, useMemo, useRef, useState, useSyncExternalStore, type ReactNode } from "react";
import type { InkStrokeDto, PadBlockDto, PadOpDto } from "../../../api/dto";
import { MarkdownMath } from "../../../render/MarkdownMath";
import { FitMath } from "../fitMath";
import { usePenHost, type PenHost } from "./host";
import { PenInput, type PointerLike, type Sample } from "./input";
import { distanceToPolyline } from "./geometry";

/** The pad's ruled line (spec §10.10: lined paper, 52 px rules); a line's surface is a whole number of them. */
export const RULE_PX = 52;
/** The spec's pen width (§4.2): the stroke drawn, the eraser's reach. */
const PEN_WIDTH = 2.2;

type Point6 = [number, number, number, number, number, number];

function round(value: number): number {
  return Math.round(value * 100) / 100;
}

function pathOf(points: ReadonlyArray<readonly number[]>): string {
  return points.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(" ");
}

/** How tall a line's surface is: enough whole rules to hold its strokes. */
export function surfaceHeight(strokes: ReadonlyArray<{ points: ReadonlyArray<readonly number[]> }>): number {
  const bottom = Math.max(0, ...strokes.flatMap((stroke) => stroke.points.map((p) => p[1] + PEN_WIDTH)));
  return Math.max(1, Math.ceil(bottom / RULE_PX)) * RULE_PX;
}

interface SurfaceProps {
  host: PenHost;
  strokes: ReadonlyArray<InkStrokeDto>;
  paused: boolean;
  /** A stroke finished on this surface (its points in the surface's own pixels). */
  onStroke: (stroke: InkStrokeDto, pointerType: "pen" | "mouse") => void;
  /** The barrel erased the strokes it passed over. */
  onErase?: (strokeIds: string[]) => void;
  label: string;
  children?: ReactNode;
}

/** A pen surface: draws the strokes it holds and takes new ones (touch never draws; a paused window draws nothing). */
function InkSurface({ host, strokes, paused, onStroke, onErase, label, children }: SurfaceProps) {
  const hostRef = useRef(host);
  hostRef.current = host;
  const input = useMemo(() => new PenInput(() => hostRef.current.simulate), []);
  const ref = useRef<HTMLDivElement | null>(null);
  const [live, setLive] = useState<Point6[] | null>(null);
  // A stroke's click is the pen's, not the row's (a pad's last row also starts a typed line on a click).
  const drew = useRef(false);
  // The strokes this barrel gesture already erased: the eraser passes over a stroke again before the line redraws
  // without it, and a second erase of it would be refused (the stroke no longer stands), taking the whole op.
  const erased = useRef(new Set<string>());
  const local = (samples: Sample[]): Point6[] => {
    const box = ref.current?.getBoundingClientRect() ?? { left: 0, top: 0 };
    return samples.map((s) => [round(s.x - box.left), round(s.y - box.top), round(s.t), s.pressure, s.tiltX, s.tiltY]);
  };
  // Paused mid-stroke: the stroke ends there, so samples drawn before the pause are never saved by a pointer-up
  // that comes after the window resumes.
  useEffect(() => {
    if (!paused) return;
    input.cancel();
    setLive(null);
  }, [paused, input]);
  const height = surfaceHeight([...strokes, ...(live ? [{ points: live }] : [])]);
  return (
    <div
      ref={ref}
      className="desk-ink-surface"
      aria-label={label}
      data-ink-surface=""
      style={{ height }}
      onPointerDown={(event) => {
        if (paused) return;
        const outcome = input.down(event.nativeEvent as unknown as PointerLike, hostRef.current.on);
        if (outcome.kind === "pass") return;
        if (outcome.turnOn) hostRef.current.setOn(true);
        drew.current = true;
        erased.current.clear();
        event.preventDefault();
        event.stopPropagation();
        try {
          event.currentTarget.setPointerCapture?.(event.pointerId);
        } catch {
          // A pointer the platform no longer tracks: its pointerup still ends the stroke.
        }
        if (outcome.kind === "draw") setLive(local([{ x: event.clientX, y: event.clientY, t: 0, pressure: 0.5, tiltX: 0, tiltY: 0 }]));
      }}
      onPointerMove={(event) => {
        if (paused) {
          input.cancel();
          setLive(null);
          return;
        }
        const samples = input.move(event.nativeEvent as unknown as PointerLike);
        if (!samples.length) return;
        if (input.erasing) {
          const hit = new Set<string>();
          for (const at of local(samples)) {
            for (const stroke of strokes) {
              if (erased.current.has(stroke.strokeId)) continue;
              if (distanceToPolyline({ x: at[0], y: at[1] }, stroke.points.map((p) => ({ x: p[0], y: p[1] }))) <= PEN_WIDTH) hit.add(stroke.strokeId);
            }
          }
          for (const strokeId of hit) erased.current.add(strokeId);
          if (hit.size) onErase?.([...hit]);
          return;
        }
        setLive((now) => (now ? [...now, ...local(samples)] : now));
      }}
      onPointerUp={(event) => {
        const stroke = input.up(event.nativeEvent as unknown as PointerLike);
        setLive(null);
        if (!stroke || paused || stroke.samples.length < 2) return;
        onStroke({ strokeId: hostRef.current.mintId("stroke"), points: local(stroke.samples) }, stroke.pointerType);
      }}
      onPointerCancel={() => {
        input.cancel();
        setLive(null);
      }}
      onClick={(event) => {
        if (!drew.current) return;
        drew.current = false;
        event.stopPropagation();
      }}
    >
      <svg className="desk-ink-strokes" width="100%" height={height} aria-hidden="true">
        {strokes.map((stroke) => <path key={stroke.strokeId} className="stroke" data-ink-stroke={stroke.strokeId} d={pathOf(stroke.points)} />)}
        {live ? <path className="stroke" data-ink-stroke="live" d={pathOf(live)} /> : null}
      </svg>
      {children}
    </div>
  );
}

function pointerMeta(pointerType: "pen" | "mouse") {
  return { pointerType, devicePixelRatio: (typeof window !== "undefined" && window.devicePixelRatio) || 1 };
}

export interface InkBlockProps {
  padId: string;
  block: PadBlockDto;
  windowId: string;
  paused: boolean;
  showTranscription: boolean;
  /** Write ops on the pad through the vault's store (false when refused or paused). */
  write: (ops: PadOpDto[]) => boolean;
}

/** One ink line: its strokes, and its transcription under it. */
export function InkBlock({ padId, block, windowId, paused, showTranscription, write }: InkBlockProps) {
  const host = usePenHost();
  if (!host) return <div className="desk-ink-none">ink needs the desks</div>;
  return <InkBlockOn host={host} padId={padId} block={block} windowId={windowId} paused={paused} showTranscription={showTranscription} write={write} />;
}

function InkBlockOn({ host, padId, block, windowId, paused, showTranscription, write }: InkBlockProps & { host: PenHost }) {
  const cache = host.ink;
  useSyncExternalStore(cache.subscribe, cache.getVersion);
  const pad = cache.pad(padId);
  const line = pad.lines[block.blockId];
  const reading = pad.readings[block.blockId];
  const [fixing, setFixing] = useState<string | null>(null);
  const strokes = line?.strokes ?? [];
  const words = block.bodyMd.trim();
  const corrected = block.provenance === "learner_correction";

  const keep = (text: string) => {
    setFixing(null);
    if (text.trim() === words) return;
    // The learner's words: a new version of the block (the server makes it a learner_correction).
    write([{ op: "edit_block", blockId: block.blockId, expectedHead: block.headVersionId, versionId: host.mintId("ver"), bodyMd: text.trim() }]);
  };

  let status: ReactNode = null;
  if (reading?.status === "reading") {
    status = <span className="ocrs">reading your handwriting… <button type="button" onClick={() => cache.cancel(padId, block.blockId)}>cancel</button></span>;
  } else if (reading?.status === "cannot") {
    status = <span className="ocrs" data-ink-refused="">handwriting can't be read yet · your ink is kept · <button type="button" onClick={() => setFixing(words)}>type what you wrote</button></span>;
  } else if (reading?.status === "failed") {
    status = <span className="ocrs">not read ({reading.message}) · your ink is kept · <button type="button" onClick={() => void cache.read(padId, block.blockId, windowId)}>read it again</button></span>;
  } else if (reading?.status === "kept_yours" && reading.result) {
    const offered = reading.result.latexMd;
    status = (
      <span className="ocrs" data-ink-kept-yours="">your words stand · LearnLoop now reads: <span className="ocrtex"><MarkdownMath value={offered} /></span> (may be wrong) · <button type="button" onClick={() => keep(offered)}>use it</button></span>
    );
  } else if (reading?.status === "nothing") {
    status = <span className="ocrs">nothing read · <button type="button" onClick={() => setFixing("")}>write it here</button></span>;
  } else if (line?.unread && strokes.length) {
    status = <span className="ocrs"><button type="button" onClick={() => void cache.read(padId, block.blockId, windowId)}>read it</button></span>;
  }

  return (
    <div className="desk-ink" data-ink-block={block.blockId}>
      <InkSurface
        host={host}
        strokes={strokes}
        paused={paused}
        label="an ink line"
        onStroke={(stroke, pointerType) => {
          const inkId = host.mintId("ink");
          host.saveInk({ owner: { blockId: block.blockId }, inkId, strokes: [stroke], pointerMeta: pointerMeta(pointerType) });
          cache.addStrokes(padId, block.blockId, inkId, [stroke]);
          cache.wrote(padId, block.blockId, windowId);
        }}
        onErase={(strokeIds) => {
          // Every stroke erased: LearnLoop's reading of them goes too (the server writes the same blank version).
          // Read from the cache, not this render: one barrel gesture erases stroke after stroke before a redraw.
          const all = (cache.pad(padId).lines[block.blockId]?.strokes ?? []).every((stroke) => strokeIds.includes(stroke.strokeId));
          const read = block.provenance === "ink_transcription" && (words !== "" || "ink_transcription" in block.payload);
          const op: PadOpDto = { op: "erase_ink", blockId: block.blockId, strokeIds, eraseId: host.mintId("erase"), ...(all && read ? { versionId: host.mintId("ver") } : {}) };
          if (!write([op])) return;
          cache.erase(padId, block.blockId, strokeIds);
          // Read the line's ink again once the erase is answered: an erase the server refused (a stroke already
          // erased elsewhere) shows the strokes it still holds.
          void cache.reconcile(padId);
        }}
      />
      {showTranscription ? (
        <div className="ocrl2" data-ink-transcription={corrected ? "yours" : words ? "reading" : "none"}>
          {fixing !== null ? (
            <textarea
              className="ocrfix"
              aria-label="what this line says"
              data-desk-typing=""
              autoFocus
              rows={1}
              defaultValue={fixing}
              onBlur={(event) => keep(event.currentTarget.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  event.currentTarget.blur();
                } else if (event.key === "Escape") {
                  event.preventDefault();
                  event.stopPropagation();
                  setFixing(null);
                }
              }}
            />
          ) : words ? (
            <>
              <span className="ocrt">{corrected ? "yours" : "read as"}</span>
              <span className="ocrtex"><FitMath><MarkdownMath value={words} /></FitMath></span>
              <span className="ocrl">{corrected ? "you corrected the transcription" : "may be wrong"} · <button type="button" onClick={() => setFixing(words)}>fix it</button></span>
            </>
          ) : null}
          {fixing === null ? status : null}
        </div>
      ) : null}
    </div>
  );
}

/** A pad's last row with the pen: a stroke here starts a new ink line (an `ink` block inserted, then its ink). */
export function InkJot({ padId, windowId, paused, newLine, hint }: {
  padId: string;
  windowId: string;
  paused: boolean;
  /** Insert a new ink block at the pad's end; its id, or null when refused. */
  newLine: () => string | null;
  hint: ReactNode;
}) {
  const host = usePenHost();
  if (!host) return null;
  return (
    <InkSurface
      host={host}
      strokes={[]}
      paused={paused}
      label="write a new line with the pen"
      onStroke={(stroke, pointerType) => {
        const blockId = newLine();
        if (!blockId) return;
        const inkId = host.mintId("ink");
        host.saveInk({ owner: { blockId }, inkId, strokes: [stroke], pointerMeta: pointerMeta(pointerType) });
        host.ink.addStrokes(padId, blockId, inkId, [stroke]);
        host.ink.wrote(padId, blockId, windowId);
      }}
    >
      <span className="hint2">{hint}</span>
    </InkSurface>
  );
}
