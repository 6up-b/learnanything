import { FONT_MONO } from "../../components/term";
import { CHAR_H, CHAR_W, mixRgb, readPaletteColors, rgba } from "./shared";

export const FULLSCREEN_CANVAS_STYLE = {
  position: "absolute",
  inset: 0,
  width: "100%",
  height: "100%",
  display: "block"
} as const;

type GlyphAtlasOptions = {
  glyphs: string;
  colors: string[];
  dpr: number;
  glowColor?: string;
  glowColors?: string[];
  glowBlur?: number;
};

/**
 * Resolve CSS variables and color-mix() once while constructing an atlas.
 * Canvas paint styles cannot consume var(--token) directly.
 */
export function resolveCssColor(value: string, fallback: string): string {
  const probe = document.createElement("span");
  probe.style.position = "fixed";
  probe.style.visibility = "hidden";
  probe.style.pointerEvents = "none";
  probe.style.color = fallback;
  probe.style.color = value;
  document.body.appendChild(probe);
  const resolved = getComputedStyle(probe).color || fallback;
  probe.remove();
  return resolved;
}

export function readAmberAtlasPalette(glowStrength: number): { colors: string[]; glow: string } {
  const palette = readPaletteColors();
  return {
    colors: [
      resolveCssColor("var(--amber-low)", rgba(mixRgb(palette.bg, palette.amber, 0.3), 1)),
      resolveCssColor("var(--amber-mid)", rgba(mixRgb(palette.bg, palette.amber, 0.58), 1)),
      resolveCssColor("var(--amber)", rgba(palette.amber, 1)),
      resolveCssColor("var(--amber-hi)", rgba(mixRgb(palette.amber, [255, 255, 255], 0.38), 1))
    ],
    glow: resolveCssColor(
      `color-mix(in srgb, var(--amber) ${glowStrength * 100}%, transparent)`,
      rgba(palette.amber, glowStrength)
    )
  };
}

/**
 * A tiny raster font texture. Every glyph/color combination is painted once;
 * animation frames only clear the destination canvas and copy atlas tiles.
 *
 * Cell codes are 1-based so zero can represent an empty cell:
 *   1 + colorIndex * glyphCount + glyphIndex
 */
export class MonospaceGlyphAtlas {
  readonly glyphCount: number;
  readonly colorCount: number;
  readonly cellWidth = CHAR_W;
  readonly cellHeight = CHAR_H;

  private readonly atlas: HTMLCanvasElement;
  private readonly pad: number;
  private readonly tileWidth: number;
  private readonly tileHeight: number;
  private readonly tilePixelWidth: number;
  private readonly tilePixelHeight: number;
  private readonly sourceX: Uint16Array;
  private readonly sourceY: Uint16Array;
  private readonly glyphIndices = new Map<string, number>();

  constructor({
    glyphs,
    colors,
    dpr,
    glowColor = "transparent",
    glowColors,
    glowBlur = 0
  }: GlyphAtlasOptions) {
    this.glyphCount = glyphs.length;
    this.colorCount = colors.length;
    this.pad = Math.ceil(glowBlur * 2);
    this.tileWidth = this.cellWidth + this.pad * 2;
    this.tileHeight = this.cellHeight + this.pad * 2;
    this.tilePixelWidth = Math.ceil(this.tileWidth * dpr);
    this.tilePixelHeight = Math.ceil(this.tileHeight * dpr);

    for (let i = 0; i < glyphs.length; i++) this.glyphIndices.set(glyphs[i], i);

    const tileCount = this.glyphCount * this.colorCount;
    const atlasCols = this.glyphCount;
    const atlasRows = this.colorCount;
    this.sourceX = new Uint16Array(tileCount + 1);
    this.sourceY = new Uint16Array(tileCount + 1);
    this.atlas = document.createElement("canvas");
    this.atlas.width = atlasCols * this.tilePixelWidth;
    this.atlas.height = atlasRows * this.tilePixelHeight;

    const ctx = this.atlas.getContext("2d");
    if (!ctx) throw new Error("Canvas 2D is unavailable");
    ctx.font = `${12 * dpr}px ${FONT_MONO}`;
    ctx.textAlign = "center";
    ctx.textBaseline = "alphabetic";
    ctx.shadowBlur = glowBlur * dpr;

    const metrics = ctx.measureText("Mg");
    const ascent = metrics.actualBoundingBoxAscent || 9 * dpr;
    const descent = metrics.actualBoundingBoxDescent || 3 * dpr;
    const baselineOffset = (this.cellHeight * dpr + ascent - descent) / 2;

    for (let colorIndex = 0; colorIndex < colors.length; colorIndex++) {
      ctx.fillStyle = colors[colorIndex];
      ctx.shadowColor = glowColors?.[colorIndex] ?? glowColor;
      for (let glyphIndex = 0; glyphIndex < glyphs.length; glyphIndex++) {
        const tileIndex = colorIndex * this.glyphCount + glyphIndex;
        const code = tileIndex + 1;
        const sx = glyphIndex * this.tilePixelWidth;
        const sy = colorIndex * this.tilePixelHeight;
        this.sourceX[code] = sx;
        this.sourceY[code] = sy;
        ctx.fillText(
          glyphs[glyphIndex],
          sx + this.pad * dpr + (this.cellWidth * dpr) / 2,
          sy + this.pad * dpr + baselineOffset
        );
      }
    }
  }

  glyphIndex(glyph: string): number {
    const index = this.glyphIndices.get(glyph);
    if (index === undefined) throw new Error(`Glyph ${JSON.stringify(glyph)} is not present in the atlas`);
    return index;
  }

  code(glyphIndex: number, colorIndex: number): number {
    return 1 + colorIndex * this.glyphCount + glyphIndex;
  }

  draw(ctx: CanvasRenderingContext2D, cells: Uint16Array, cols: number): void {
    const sourceX = this.sourceX;
    const sourceY = this.sourceY;
    const sourceWidth = this.tilePixelWidth;
    const sourceHeight = this.tilePixelHeight;
    const destWidth = this.tileWidth;
    const destHeight = this.tileHeight;
    const pad = this.pad;
    const cellWidth = this.cellWidth;
    const cellHeight = this.cellHeight;
    const atlas = this.atlas;

    const rows = Math.ceil(cells.length / cols);
    let index = 0;
    for (let row = 0; row < rows; row++) {
      const y = row * cellHeight - pad;
      for (let col = 0; col < cols && index < cells.length; col++, index++) {
        const code = cells[index];
        if (code === 0) continue;
        ctx.drawImage(
          atlas,
          sourceX[code],
          sourceY[code],
          sourceWidth,
          sourceHeight,
          col * cellWidth - pad,
          y,
          destWidth,
          destHeight
        );
      }
    }
  }
}
