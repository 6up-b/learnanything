// Phase 2 step 1: copy a standalone screen test to mount the scoped source (the copy in screens/desks/source/, its
// relative paths rebased, ReaderScreen read as ScopedSource). The original stays until step 2 deletes the screen.
// Usage: node port_tests.mjs <app dir> <topic>...   (screens/ReaderScreen.<topic>.test.tsx → ScopedSource.<topic>.test.tsx)
import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, relative, resolve } from "node:path";

const [app, ...topics] = process.argv.slice(2);
const ts = createRequire(join(app, "package.json"))("typescript");
// The cases that reach the source only through the standalone screen's own branches (its list, header or key bar):
// left out of the copies, kept in the originals, ported to the window's own controls in step 2.
const OMIT = JSON.parse(readFileSync(join(dirname(new URL(import.meta.url).pathname), "standalone_only_cases.json"), "utf8"));

/** The text without the it()/test() cases named (each a whole statement). */
function withoutCases(text, names) {
  const sf = ts.createSourceFile("t.tsx", text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const spans = [];
  const visit = (node) => {
    if (ts.isExpressionStatement(node) && ts.isCallExpression(node.expression) && ts.isIdentifier(node.expression.expression)
      && ["it", "test"].includes(node.expression.expression.text)) {
      const title = node.expression.arguments[0];
      if (title && (ts.isStringLiteral(title) || ts.isNoSubstitutionTemplateLiteral(title)) && names.includes(title.text)) spans.push([node.getFullStart(), node.getEnd()]);
      return;
    }
    ts.forEachChild(node, visit);
  };
  visit(sf);
  if (spans.length !== names.length) throw new Error(`omitted ${spans.length} of ${names.length} cases`);
  for (const [a, b] of spans.sort((x, y) => y[0] - x[0])) text = text.slice(0, a) + text.slice(b);
  return text;
}
const SCREENS = join(app, "src/screens");
const TARGET = join(SCREENS, "desks/source");
const rebase = (spec) => {
  if (!spec.startsWith(".")) return spec;
  const r = relative(TARGET, resolve(SCREENS, spec)).replaceAll("\\", "/");
  return r.startsWith(".") ? r : `./${r}`;
};
for (const topic of topics) {
  const from = join(SCREENS, `ReaderScreen.${topic}.test.tsx`);
  let text = readFileSync(from, "utf8");
  text = text.replace(/import \{ ReaderScreen \} from "\.\/ReaderScreen";/, 'import { ScopedSource } from "./desks/source/ScopedSource";');
  // Every relative module path (imports, vi.mock, vi.importActual, dynamic imports) is rebased.
  text = text.replace(/(from\s+|vi\.mock\(\s*|vi\.doMock\(\s*|importActual(?:<[^>]*>)?\(\s*|import\(\s*)(["'])(\.{1,2}\/[^"']*)\2/g,
    (_, lead, q, spec) => `${lead}${q}${rebase(spec)}${q}`);
  // The component only (its JSX and its type), never a test's name: a snapshot's keys stay the original's.
  text = text.replace(/(<\/?)ReaderScreen\b/g, "$1ScopedSource").replace(/typeof ReaderScreen\b/g, "typeof ScopedSource");
  // A file a test reads beside it (\`\${__dirname}/../styles/...\`) is read from the same place.
  text = text.replace(/\$\{__dirname\}\/\.\.\//g, "${__dirname}/../../../");
  const omitted = OMIT[topic] ?? [];
  if (omitted.length) text = withoutCases(text, omitted.map((c) => c.name));
  const omittedNote = omitted.length
    ? "// Left out (kept in the original until step 2 ports them to a source window's own controls):\n"
      + omitted.map((c) => `//   - "${c.name}": ${c.why}.`).join("\n") + "\n"
    : "";
  const header = `// Ported from screens/ReaderScreen.${topic}.test.tsx (the Reader's retirement, phase 2 step 1): the same cases,
// mounting the scoped source a source window mounts, without the standalone screen's own branches.
`;
  mkdirSync(TARGET, { recursive: true });
  writeFileSync(join(TARGET, `ScopedSource.${topic}.test.tsx`), header + omittedNote + text);
  const snap = join(SCREENS, "__snapshots__", `ReaderScreen.${topic}.test.tsx.snap`);
  if (existsSync(snap)) {
    mkdirSync(join(TARGET, "__snapshots__"), { recursive: true });
    copyFileSync(snap, join(TARGET, "__snapshots__", `ScopedSource.${topic}.test.tsx.snap`));
  }
  console.log(`ported ${topic}`);
}
void dirname;
