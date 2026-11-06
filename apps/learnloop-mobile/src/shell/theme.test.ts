// Mobile v2 §4.6 and §4.7: two themes on the existing CSS variables, both WCAG AA for text, and a
// choice that follows the system unless the learner picks one. Read from styles.css itself
// (vitest turns CSS imports into empty modules), so the test checks the colours that ship.
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { applyTheme, readThemeChoice, saveThemeChoice } from "./theme";

const CSS = readFileSync(join(dirname(fileURLToPath(import.meta.url)), "..", "styles.css"), "utf8");

function block(name: string): Record<string, string> {
  const match = CSS.match(new RegExp(`/\\* theme:${name} \\*/([\\s\\S]*?)/\\* end \\*/`));
  if (!match) throw new Error(`styles.css has no theme:${name} block`);
  return Object.fromEntries([...match[1].matchAll(/--([a-z-]+):\s*(#[0-9a-f]{6})\s*;/gi)].map((one) => [one[1], one[2].toLowerCase()]));
}

function luminance(hex: string): number {
  const channel = (offset: number) => {
    const value = parseInt(hex.slice(offset, offset + 2), 16) / 255;
    return value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * channel(1) + 0.7152 * channel(3) + 0.0722 * channel(5);
}

function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

/** Every pair of text colour on the surface it is drawn on. */
const TEXT_PAIRS: ReadonlyArray<[string, string]> = [
  ["text", "bg"], ["text", "panel"], ["dim", "bg"], ["dim", "panel"], ["accent", "bg"], ["accent", "panel"],
  ["on-accent", "accent"], ["bad", "bg"], ["bad", "panel"]
];

describe.each(["dark", "light"])("the %s theme", (name) => {
  const tokens = block(name);

  it.each(TEXT_PAIRS)("%s on %s is at least 4.5:1 (AA)", (fore, back) => {
    expect(tokens[fore], fore).toBeDefined();
    expect(tokens[back], back).toBeDefined();
    expect(contrast(tokens[fore], tokens[back])).toBeGreaterThanOrEqual(4.5);
  });
});

it("dark is today's palette (§4.6)", () => {
  expect(block("dark")).toMatchObject({ bg: "#14161a", panel: "#1c1f25", text: "#e8e6e1", accent: "#e0a458" });
});

it("the light theme the system picks is the one the learner picks", () => {
  expect(block("light-system")).toEqual(block("light"));
});

it("the contrast formula is WCAG's", () => {
  expect(contrast("#000000", "#ffffff")).toBeCloseTo(21, 5);
  expect(contrast("#777777", "#ffffff")).toBeCloseTo(4.48, 2);
});

describe("the choice", () => {
  it("follows the system until one is picked, and says so on the root", () => {
    expect(readThemeChoice()).toBe("system");
    saveThemeChoice("light");
    expect(readThemeChoice()).toBe("light");
    expect(document.documentElement.dataset.theme).toBe("light");
    saveThemeChoice("system");
    expect(readThemeChoice()).toBe("system");
    expect(document.documentElement.dataset.theme).toBeUndefined();
  });

  it("applies to any root it is given", () => {
    const root = document.createElement("div");
    applyTheme("dark", root);
    expect(root.dataset.theme).toBe("dark");
    applyTheme("system", root);
    expect(root.dataset.theme).toBeUndefined();
  });
});
