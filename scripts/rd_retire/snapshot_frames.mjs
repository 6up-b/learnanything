// Phase 2 step 2: the switch-off snapshot tests ("byte-identical with the switch off") were written with the standalone
// screen's frame (its header and key bar). Ported to the scoped source, their markup has the source bar instead. This
// checks that nothing else moved: each old snapshot without the old header and key bar equals the new one without the
// source bar, entry by entry. A record of the port, run once against the snapshots before and after `vitest -u`.
// Usage: node snapshot_frames.mjs <app dir> <old.snap> <new.snap> [...pairs]
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { join } from "node:path";
import vm from "node:vm";

const [app, ...files] = process.argv.slice(2);
const { JSDOM } = createRequire(join(app, "package.json"))("jsdom");

function entries(path) {
  const exports = {};
  vm.runInNewContext(readFileSync(path, "utf8"), { exports });
  // Each value is the markup in double quotes, its own quotes unescaped (vitest prints strings so).
  return Object.fromEntries(Object.entries(exports).map(([key, value]) => [key, value.trim().replace(/^"/, "").replace(/"$/, "")]));
}

function strip(markup, removeOld) {
  const dom = new JSDOM(`<body>${markup}</body>`);
  const body = dom.window.document.body;
  if (removeOld) {
    // The old header: the block holding the READER label and "← Library".
    for (const button of [...body.querySelectorAll("button")].filter((each) => each.textContent === "← Library")) {
      let node = button;
      while (node && !(node.getAttribute?.("style") ?? "").includes("padding: 22px 32px")) node = node.parentElement;
      node?.remove();
    }
    // The old key bar: the term KeyBar at the foot of the screen's root (another screen's key bar stays).
    const root = body.firstElementChild;
    for (const child of [...(root?.children ?? [])]) {
      if ((child.getAttribute("style") ?? "").startsWith("border-top: 1px solid var(--border); padding: 6px 14px")) child.remove();
    }
  } else {
    for (const bar of body.querySelectorAll("[data-window-source-bar]")) bar.remove();
  }
  return body.innerHTML;
}

let failures = 0;
for (let i = 0; i < files.length; i += 2) {
  const before = entries(files[i]);
  const after = entries(files[i + 1]);
  for (const key of Object.keys(after)) {
    if (!(key in before)) { console.log(`new entry ${key}`); failures += 1; continue; }
    const a = strip(before[key], true);
    const b = strip(after[key], false);
    if (a !== b) {
      failures += 1;
      let at = 0;
      while (a[at] === b[at]) at += 1;
      console.log(`DIFFERS ${key}\n  old: …${a.slice(Math.max(0, at - 80), at + 160)}\n  new: …${b.slice(Math.max(0, at - 80), at + 160)}`);
    } else console.log(`same ${key}`);
  }
}
process.exit(failures ? 1 : 0);
