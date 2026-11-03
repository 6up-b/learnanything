#!/usr/bin/env node
// Bundles src/render/pageMathSegments.ts, the page's own markdown pipeline up to the math elements, into
// page-markdown.js for the book-math engine (RW5c §5.2; the sidecar runs it, learnloop.figures.katex_tree).
// The inputs are the packages package-lock.json locks, so the output is reproducible: `--check` compares and writes nothing.
//   node sketch-engine/markdown/build.mjs            write page-markdown.js, LICENSES.txt, page-markdown.lock.json
//   node sketch-engine/markdown/build.mjs --check    exit 1 if any of them would change
// A change moves page-markdown.lock.json's digest: pin it in katex_tree.MARKDOWN_SHA256, and bump CERTIFICATION_VERSION.
import { createHash } from "node:crypto";
import { existsSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { build, version as esbuildVersion } from "esbuild";

const HERE = dirname(fileURLToPath(import.meta.url));
const APP = resolve(HERE, "..", "..");
const FILES = { bundle: join(HERE, "page-markdown.js"), licenses: join(HERE, "LICENSES.txt"), lock: join(HERE, "page-markdown.lock.json") };

export const OPTIONS = {
  absWorkingDir: APP,
  entryPoints: ["src/render/pageMathSegments.ts"],
  bundle: true,
  format: "iife",
  globalName: "pageMarkdown",
  // No DOM and no node: `worker` picks the same entity decoder vitest's node lane uses, and vfile's browser path helpers.
  platform: "neutral",
  mainFields: ["module", "main"],
  conditions: ["worker"],
  target: "es2022",
  minify: true,
  charset: "ascii",
  legalComments: "none",
  metafile: true,
  write: false,
};

function authorOf(manifest) {
  return typeof manifest.author === "string" ? manifest.author : manifest.author?.name ?? "not named";
}

/** Each bundled package with bytes in the output, and its version, licence name and licence text. */
function packagesOf(metafile) {
  const inputs = Object.values(metafile.outputs)[0].inputs;
  const names = new Set();
  for (const [path, input] of Object.entries(inputs)) {
    const found = path.match(/node_modules\/((?:@[^/]+\/)?[^/]+)\//);
    if (found && input.bytesInOutput > 0) names.add(found[1]);
  }
  return [...names].sort().map((name) => {
    const root = join(APP, "node_modules", name);
    const manifest = JSON.parse(readFileSync(join(root, "package.json"), "utf8"));
    const file = readdirSync(root).find((entry) => /^licen[cs]e/i.test(entry));
    if (!["MIT", "ISC"].includes(manifest.license)) throw new Error(`${name}: licence ${manifest.license} is not on the list`);
    return { name, version: manifest.version, license: manifest.license, text: file ? readFileSync(join(root, file), "utf8").trim()
      : `The npm package names the ${manifest.license} licence and carries no licence file. Author: ${authorOf(manifest)}. Source: ${manifest.repository?.url ?? manifest.repository ?? "not named"}.` };
  });
}

export async function outputs() {
  const result = await build(OPTIONS);
  const bundle = result.outputFiles[0].text;
  const packages = packagesOf(result.metafile);
  const licenses = [
    "Third-party notices for page-markdown.js, a bundle of these packages at these versions (build.mjs):",
    "",
    ...packages.flatMap((item) => [`--- ${item.name} ${item.version} (${item.license})`, "", item.text, ""]),
  ].join("\n");
  const lock = {
    sha256: createHash("sha256").update(bundle).digest("hex"),
    bytes: Buffer.byteLength(bundle),
    esbuild: esbuildVersion,
    packages: Object.fromEntries(packages.map((item) => [item.name, item.version])),
  };
  return { bundle, licenses, lock: `${JSON.stringify(lock, null, 2)}\n` };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const made = await outputs();
  const changed = Object.keys(FILES).filter((key) => !existsSync(FILES[key]) || readFileSync(FILES[key], "utf8") !== made[key]);
  if (process.argv.includes("--check")) {
    console.log(changed.length ? `DIFFERENT: ${changed.join(", ")}` : `reproduced ${JSON.parse(made.lock).sha256}`);
    process.exit(changed.length ? 1 : 0);
  }
  for (const key of changed) writeFileSync(FILES[key], made[key]);
  console.log(JSON.parse(made.lock).sha256);
}
