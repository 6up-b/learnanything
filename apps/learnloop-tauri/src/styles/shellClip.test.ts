// The boxes around every screen (`html`, `body`, `#root`, the frame) clip
// their overflow. A box with `overflow: hidden` can still be scrolled by a
// child's `scrollIntoView` or `focus()`, which carried the top bar and the
// place tabs out of the window in the Reader with no way back; a clipped box
// cannot be scrolled by anything. jsdom applies no stylesheet, so the rules
// are read as text; that the window honours `overflow: clip` (WebKitGTK) is
// for the real window.
import { beforeAll, expect, it } from "vitest";

let css = "";
let html = "";
beforeAll(async () => {
  const fsModule = "node:fs";
  const fs = (await import(/* @vite-ignore */ fsModule)) as { readFileSync: (path: string, encoding: string) => string };
  // Tests run from the app's folder (vitest's root).
  const cwd = (globalThis as unknown as { process: { cwd(): string } }).process.cwd();
  css = fs.readFileSync(`${cwd}/src/styles/app.css`, "utf8");
  html = fs.readFileSync(`${cwd}/index.html`, "utf8");
});

function rule(text: string, selector: RegExp): string {
  return text.match(new RegExp(`(^|\\n)\\s*${selector.source}\\s*\\{([^}]*)\\}`))?.[2] ?? "";
}

it("html, body and #root clip their overflow, in the stylesheet and in the page that loads it", () => {
  expect(rule(css, /html,\s*body,\s*#root/)).toMatch(/overflow:\s*clip/);
  expect(rule(html, /html,\s*body,\s*#root/)).toMatch(/overflow:\s*clip/);
});

it("the frame clips too, and still fits the window whatever it holds", () => {
  const frame = rule(css, /\.terminal-frame/);
  expect(frame).toMatch(/overflow:\s*clip/);
  expect(frame).toMatch(/min-width:\s*0/);
  expect(frame).toMatch(/min-height:\s*0/);
});
