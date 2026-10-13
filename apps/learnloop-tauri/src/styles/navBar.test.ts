// The ten-tab bar until Phase 2 (usability round 2): at the desktop window's
// 1380px the library switcher was squeezed to "Le…"/"li…" and "[Alt+S]" was
// clipped at the right edge. jsdom has no layout, so this pins the rules that
// make room: tabs give back padding on narrower windows, the switcher keeps
// enough width for a library's name, and the settings chip never wraps or
// clips (its key hint steps aside below 1300px; the tooltip still names it).
import { beforeAll, expect, it } from "vitest";

// The stylesheet's own text (Vite hands tests an empty string for CSS imports,
// and the app's types carry no Node module declarations).
let css = "";
beforeAll(async () => {
  const fsModule = "node:fs";
  const fs = (await import(/* @vite-ignore */ fsModule)) as { readFileSync: (path: string, encoding: string) => string };
  // Tests run from the app's folder (vitest's root).
  const cwd = (globalThis as unknown as { process: { cwd(): string } }).process.cwd();
  css = fs.readFileSync(`${cwd}/src/styles/app.css`, "utf8");
});

function rule(selector: string): string {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = css.match(new RegExp(`(^|\\n)${escaped}\\s*\\{([^}]*)\\}`));
  return match ? match[2] : "";
}

it("tabs give back horizontal padding on narrower windows", () => {
  expect(rule(".top-nav button")).toMatch(/padding:\s*11px\s+clamp\(/);
});

it("the library switcher keeps room for a library's name", () => {
  const minWidth = rule(".vault-menu-wrap").match(/min-width:\s*(\d+)ch/);
  expect(minWidth).not.toBeNull();
  expect(Number(minWidth![1])).toBeGreaterThanOrEqual(12);
});

it("the settings chip never shrinks or wraps, and its key hint steps aside when space is short", () => {
  const chip = rule(".nav-settings");
  expect(chip).toMatch(/flex-shrink:\s*0/);
  expect(chip).toMatch(/white-space:\s*nowrap/);
  expect(css).toMatch(/@media \(max-width: 1300px\)\s*\{[^}]*\.nav-settings-key\s*\{\s*display:\s*none;?\s*\}/);
});
