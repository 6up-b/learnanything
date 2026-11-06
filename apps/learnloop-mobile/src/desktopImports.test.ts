// Mobile v2 §5.3 and §7.1: the phone shares the desktop's types, query cache and pure render
// modules through `@desktop`, never its Tauri bindings. This walks the module graph from every
// phone source file, through each `@desktop/…` import and everything it imports in turn, and
// fails if any path reaches `@tauri-apps/*`. It keeps the share honest as the desktop changes.
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const PHONE_SRC = dirname(fileURLToPath(import.meta.url));
const DESKTOP_SRC = resolve(PHONE_SRC, "..", "..", "learnloop-tauri", "src");
const CODE = /\.(ts|tsx)$/;
const SPECIFIERS = /(?:^|[^\w.])(?:import|export)\s+(?:type\s+)?(?:[\w*{}\s,]+?\s+from\s+)?["']([^"']+)["']|import\(\s*["']([^"']+)["']\s*\)/g;

function isTest(path: string): boolean {
  return /\.test\.(ts|tsx)$/.test(path) || path.split("/").includes("test");
}

function phoneFiles(dir = PHONE_SRC): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return phoneFiles(path);
    return CODE.test(name) && !name.endsWith(".d.ts") && !isTest(path) ? [path] : [];
  });
}

export function specifiersOf(source: string): string[] {
  return [...source.matchAll(SPECIFIERS)].map((match) => match[1] ?? match[2]);
}

function resolveFile(base: string): string | null {
  for (const candidate of [base, `${base}.ts`, `${base}.tsx`, join(base, "index.ts"), join(base, "index.tsx")]) {
    if (existsSync(candidate) && statSync(candidate).isFile()) return candidate;
  }
  return null;
}

/** The module a specifier names, or null for a package (other than Tauri) or a non-code asset. */
function target(from: string, specifier: string): string | null {
  if (specifier.startsWith("@desktop/")) return resolveFile(join(DESKTOP_SRC, specifier.slice("@desktop/".length)));
  if (specifier.startsWith(".")) {
    const file = resolveFile(resolve(dirname(from), specifier.replace(/\?raw$/, "")));
    return file && CODE.test(file) ? file : null;
  }
  return null;
}

/** Every path from `roots` to a `@tauri-apps/*` import, as readable chains. */
export function tauriPaths(roots: readonly string[]): { reached: Set<string>; violations: string[] } {
  const reached = new Set<string>();
  const violations: string[] = [];
  const queue: Array<{ file: string; chain: string[] }> = roots.map((file) => ({ file, chain: [file] }));
  while (queue.length) {
    const { file, chain } = queue.shift() as { file: string; chain: string[] };
    if (reached.has(file)) continue;
    reached.add(file);
    for (const specifier of specifiersOf(readFileSync(file, "utf8"))) {
      if (specifier.startsWith("@tauri-apps/")) {
        violations.push([...chain, specifier].map((step) => (step.startsWith("/") ? relative(resolve(PHONE_SRC, ".."), step) : step)).join(" -> "));
        continue;
      }
      const next = target(file, specifier);
      if (next && !reached.has(next)) queue.push({ file: next, chain: [...chain, next] });
    }
  }
  return { reached, violations };
}

describe("the @desktop import walk", () => {
  it("no phone module reaches @tauri-apps, however deep", () => {
    const { reached, violations } = tauriPaths(phoneFiles());
    expect(violations).toEqual([]);
    // Not vacuous: the shared modules §5.3 names are in the walk.
    const shared = [...reached].filter((file) => file.startsWith(DESKTOP_SRC)).map((file) => relative(DESKTOP_SRC, file));
    expect(shared).toEqual(expect.arrayContaining(["api/dto.ts", "api/queryCache.ts", "api/useCachedQuery.ts", "api/queryTags.ts", "render/MarkdownMath.tsx", "render/MathLiveEditor.tsx"]));
  });

  it("would catch the desktop's own client, which is Tauri's", () => {
    const { violations } = tauriPaths([join(DESKTOP_SRC, "api", "client.ts")]);
    expect(violations.some((chain) => chain.endsWith("@tauri-apps/api/core"))).toBe(true);
  });

  it("reads every import form", () => {
    expect(specifiersOf([
      'import a from "x1";', 'import { b, c } from "x2";', 'import type { D } from "x3";', 'import "x4";',
      'export { e } from "x5";', 'export * from "x6";', 'const f = await import("x7");', 'import * as g from "x8";'
    ].join("\n"))).toEqual(["x1", "x2", "x3", "x4", "x5", "x6", "x7", "x8"]);
  });
});
