// Shared plumbing for the start-screen backdrops: palette snapshot for canvas
// renderers, rgb math, glyph metrics, and the reduced-motion check.
//
// ASCII backdrops stay palette-aware through CSS (`bd-c-*` classes / var()
// inline styles) and never need this reader. Canvas 2D cannot resolve var()
// in fillStyle, so canvas backdrops snapshot the BASE palette tokens at mount
// via getComputedStyle. Base tokens are plain hex in app.css :root AND every
// palettes.css block (documented invariant there); derived tokens are
// color-mix() strings JS can't parse, so shades are derived here with mixRgb.
// StartScreen fully unmounts on tab switch and the palette can only change on
// the Settings tab, so a mount-time snapshot is always fresh.

export const CHAR_W = 7;
export const CHAR_H = 12;

export type Rgb = [number, number, number];

export type BackdropPalette = {
  bg: Rgb;
  text: Rgb;
  dim: Rgb;
  faint: Rgb;
  amber: Rgb;
  green: Rgb;
  cyan: Rgb;
  red: Rgb;
  pink: Rgb;
  yellow: Rgb;
};

// Default-palette fallbacks (app.css :root literals) for parse failures.
const FALLBACK: BackdropPalette = {
  bg: [14, 14, 14],
  text: [216, 216, 224],
  dim: [144, 144, 160],
  faint: [102, 103, 120],
  amber: [227, 160, 99],
  green: [127, 210, 143],
  cyan: [106, 208, 224],
  red: [224, 126, 126],
  pink: [220, 127, 184],
  yellow: [220, 205, 90]
};

function parseHex(raw: string, fallback: Rgb): Rgb {
  const hex = raw.trim().replace(/^#/, "");
  if (/^[0-9a-fA-F]{3}$/.test(hex)) {
    return [
      parseInt(hex[0] + hex[0], 16),
      parseInt(hex[1] + hex[1], 16),
      parseInt(hex[2] + hex[2], 16)
    ];
  }
  if (/^[0-9a-fA-F]{6}$/.test(hex)) {
    return [
      parseInt(hex.slice(0, 2), 16),
      parseInt(hex.slice(2, 4), 16),
      parseInt(hex.slice(4, 6), 16)
    ];
  }
  return fallback;
}

export function readPaletteColors(): BackdropPalette {
  const style = getComputedStyle(document.documentElement);
  const read = (token: string, fallback: Rgb): Rgb =>
    parseHex(style.getPropertyValue(token), fallback);
  return {
    bg: read("--bg", FALLBACK.bg),
    text: read("--text", FALLBACK.text),
    dim: read("--dim", FALLBACK.dim),
    faint: read("--faint", FALLBACK.faint),
    amber: read("--amber", FALLBACK.amber),
    green: read("--green", FALLBACK.green),
    cyan: read("--cyan", FALLBACK.cyan),
    red: read("--red", FALLBACK.red),
    pink: read("--pink", FALLBACK.pink),
    yellow: read("--yellow", FALLBACK.yellow)
  };
}

export const BLACK: Rgb = [0, 0, 0];

export function rgba(c: Rgb, a: number): string {
  return `rgba(${c[0]}, ${c[1]}, ${c[2]}, ${a})`;
}

// Linear interpolation a→b — the JS twin of CSS color-mix(in srgb, b t%, a).
export function mixRgb(a: Rgb, b: Rgb, t: number): Rgb {
  return [
    Math.round(a[0] + (b[0] - a[0]) * t),
    Math.round(a[1] + (b[1] - a[1]) * t),
    Math.round(a[2] + (b[2] - a[2]) * t)
  ];
}

// Read once at mount (SessionFinishHud precedent): animation preference rarely
// changes mid-session, and StartScreen remounts on every tab return anyway.
export function prefersReducedMotion(): boolean {
  return window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
}

// Class ramps for palette-aware ASCII rendering (resolved in app.css to
// var(--amber-low/-mid/…)). Monotonic dark→bright.
export const AMBER_CLASS_RAMP = ["bd-c-amber-low", "bd-c-amber-mid", "bd-c-amber", "bd-c-amber-hi"];
