// The overview's card face (spec §6.1) and its links (§6.5). A card is laid out at its overview size in
// world pixels (the camera's 0.34 brings it to the screen), so its type is three times the size it reads.
import type { ReactNode } from "react";
import type { Rect } from "../geometry";
import type { CurvedLink } from "./links";

/** World pixels per screen pixel in the overview (1 / 0.34): a 12 px line on screen is 35 px here. */
export const CARD_K = 1 / 0.34;

export interface CardFaceProps {
  glyph: string;
  kind: string;
  title: string;
  where: string | null;
  progress: number | null;
  /** A pad stack's bands, or a pair's second pane. */
  extra?: ReactNode;
  /** Where the live miniature goes; null for a window not opened yet (its desk was never visited). */
  miniatureHost: ((node: HTMLDivElement | null) => void) | null;
  paper: boolean;
}

export function CardFace({ glyph, kind, title, where, progress, extra, miniatureHost, paper }: CardFaceProps) {
  return (
    <div className="desk-card-face">
      {/* The picture first, as the mockup's cards: then the name, the minimap bar and where. */}
      <div className={`desk-card-thumb${paper ? " paper" : ""}`}>
        {miniatureHost ? <div className="desk-card-mini" ref={miniatureHost} /> : <div className="desk-card-unopened">not opened yet</div>}
      </div>
      <div className="desk-card-n"><span className="desk-card-g">{glyph}</span> {title}</div>
      <div className="desk-card-k">{kind}</div>
      {progress !== null ? (
        <div className="desk-card-bar" aria-hidden="true">
          <span className="ln" />
          <span className="rd" style={{ width: `${Math.max(0, Math.min(1, progress)) * 100}%` }} />
        </div>
      ) : null}
      {where ? <div className="desk-card-w">{where}</div> : null}
      {extra}
    </div>
  );
}

/** The links of the focused or hovered card, in world coordinates, with their labels. */
export function LinkLayer({ links, rects }: { links: CurvedLink[]; rects: Map<string, Rect> }) {
  if (links.length === 0) return null;
  return (
    <svg className="desk-links" aria-hidden="true" style={{ overflow: "visible", position: "absolute", left: 0, top: 0, width: 1, height: 1 }}>
      {links.map((link) => (
        <g key={link.to} data-link-to={link.to} data-link-weight={link.weight}>
          {/* The mockup's: 1.6 screen px at 85 % for every kind; an explicit link solid, the others dashed 8 / 6. */}
          <path d={link.d} fill="none" stroke="var(--desk-cyan)" strokeOpacity={0.85} strokeWidth={1.6 * CARD_K} strokeDasharray={link.weight === 3 ? undefined : `${8 * CARD_K} ${6 * CARD_K}`} />
          {rects.has(link.to) ? (
            <text x={link.labelAt.x} y={link.labelAt.y - 6 * CARD_K} fill="#bfeef5" stroke="#0a0a0b" strokeWidth={6} paintOrder="stroke" fontSize={11 * CARD_K} fontFamily="var(--desk-mono)" textAnchor="middle">{link.label}</text>
          ) : null}
        </g>
      ))}
    </svg>
  );
}
