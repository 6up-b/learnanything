// G55: every text token pairing the Reader's voices and labels use is checked
// in the five palettes (the default and dracula, gruvbox, nord,
// catppuccin-mocha): meaning-bearing copy (--dim), the model voice's label
// (--purple-text) and body text (--text) reach WCAG's 4.5:1 on --bg, and
// --faint (which meaning-bearing copy must not use) does not.
import { expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

// vitest turns CSS imports into empty modules, so read the files themselves.
const STYLES = join(__dirname, "..", "..", "styles");
const appCss = readFileSync(join(STYLES, "app.css"), "utf8");
const paletteCss = readFileSync(join(STYLES, "palettes.css"), "utf8");

function block(css: string, selector: string): Record<string, string> {
  const start = css.indexOf(`${selector} {`);
  if (start < 0) throw new Error(`no block ${selector}`);
  const body = css.slice(css.indexOf("{", start) + 1, css.indexOf("}", start));
  const tokens: Record<string, string> = {};
  for (const match of body.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) tokens[match[1]] = match[2].trim();
  return tokens;
}

type Rgb = [number, number, number];

function hex(value: string): Rgb {
  const raw = value.replace("#", "");
  const full = raw.length === 3 ? raw.split("").map((c) => c + c).join("") : raw;
  return [0, 2, 4].map((i) => parseInt(full.slice(i, i + 2), 16)) as Rgb;
}

function resolve(tokens: Record<string, string>, value: string, depth = 0): Rgb {
  if (depth > 8) throw new Error(`cycle resolving ${value}`);
  const trimmed = value.trim();
  if (trimmed === "white") return [255, 255, 255];
  if (trimmed === "black") return [0, 0, 0];
  if (trimmed.startsWith("#")) return hex(trimmed);
  const variable = /^var\((--[\w-]+)\)$/.exec(trimmed);
  if (variable) return resolve(tokens, tokens[variable[1]], depth + 1);
  const mix = /^color-mix\(in srgb,\s*(.+?)\s+(\d+(?:\.\d+)?)%,\s*(.+)\)$/.exec(trimmed);
  if (mix) {
    const a = resolve(tokens, mix[1], depth + 1);
    const b = resolve(tokens, mix[3], depth + 1);
    const weight = Number(mix[2]) / 100;
    return a.map((channel, i) => channel * weight + b[i] * (1 - weight)) as Rgb;
  }
  throw new Error(`cannot resolve ${value}`);
}

function luminance([r, g, b]: Rgb): number {
  const linear = (c: number) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b);
}

function contrast(a: Rgb, b: Rgb): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

const base = block(appCss, ":root");
const shared = block(paletteCss, ':root[data-palette="dracula"],\n:root[data-palette="gruvbox"],\n:root[data-palette="nord"],\n:root[data-palette="catppuccin-mocha"]');
const palettes: Record<string, Record<string, string>> = {
  default: base,
  ...Object.fromEntries(["dracula", "gruvbox", "nord", "catppuccin-mocha"].map((name) => [
    name,
    { ...base, ...shared, ...block(paletteCss, `:root[data-palette="${name}"]`) },
  ])),
};

for (const [name, tokens] of Object.entries(palettes)) {
  it(`${name}: the Reader's text tokens reach 4.5:1 on the background`, () => {
    const bg = resolve(tokens, tokens["--bg"]);
    for (const token of ["--dim", "--purple-text", "--text"]) {
      expect(contrast(resolve(tokens, tokens[token]), bg), `${token} on --bg`).toBeGreaterThanOrEqual(4.5);
    }
  });
}

it("--faint is under 4.5:1 on the default background, so meaning-bearing copy uses --dim", () => {
  expect(contrast(resolve(base, base["--faint"]), resolve(base, base["--bg"]))).toBeLessThan(4.5);
});
