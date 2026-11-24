// Phase 2 step 1: move ReaderScreen's scoped source into screens/desks/source/ (a text move driven by the AST).
// Usage: APP_DIR=<app> node generate.mjs <original ReaderScreen.tsx copy>
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { ts, program, identifiers, symbolOf, within, isLocalDecl } from "./common.mjs";
import { mainFunction, sites } from "./sites.mjs";

const APP = process.env.APP_DIR;
const SCREENS = join(APP, "src/screens");
const OLD = join(SCREENS, "ReaderScreen.tsx");
const SOURCE_DIR = join(SCREENS, "desks/source");
const MOVED_TYPES = ["ReaderOpenSource", "ReaderWindowing", "WindowInquiry", "ReaderLens", "PenSurface", "ReaderCheckMeRequest", "ReaderExerciseRequest"];
const SLOTS = { unopened: "StandaloneUnopened", header: "StandaloneHeader", collapsedRail: "StandaloneCollapsedRail", keyBar: "StandaloneKeyBar" };
const REACT_HOOKS = new Set(["useState", "useCallback", "useMemo", "useRef", "useEffect", "useLayoutEffect", "useReducer", "useContext", "useId", "useSyncExternalStore", "useTransition", "useDeferredValue"]);

const prog = program([OLD]);
const checker = prog.getTypeChecker();
const sf = prog.getSourceFile(OLD);
const src = sf.getFullText();
const fn = mainFunction(sf, "ReaderScreen");
const site = sites(fn);

// ── the original imports: local name → { spec, typeOnly, imported } ──
const imports = new Map();
const importStatements = [];
for (const stmt of sf.statements) {
  if (!ts.isImportDeclaration(stmt)) continue;
  importStatements.push(stmt);
  const spec = stmt.moduleSpecifier.text;
  const clause = stmt.importClause;
  if (!clause) continue;
  if (clause.name) imports.set(clause.name.text, { spec, typeOnly: clause.isTypeOnly, imported: "default" });
  const nb = clause.namedBindings;
  if (nb && ts.isNamedImports(nb)) {
    for (const el of nb.elements) imports.set(el.name.text, { spec, typeOnly: clause.isTypeOnly || el.isTypeOnly, imported: (el.propertyName ?? el.name).text });
  } else if (nb && ts.isNamespaceImport(nb)) imports.set(nb.name.text, { spec, typeOnly: clause.isTypeOnly, imported: "*" });
}
const rebase = (spec, fromDir) => {
  if (!spec.startsWith(".")) return spec;
  let r = relative(fromDir, resolve(SCREENS, spec)).replaceAll("\\", "/");
  return r.startsWith(".") ? r : `./${r}`;
};

/** Import statements for the names a text uses, from the original imports, rebased to a directory. */
function importsFor(names, fromDir, { typeOnlyAll = false } = {}) {
  const bySpec = new Map();
  for (const name of [...names].sort()) {
    const imp = imports.get(name);
    if (!imp) continue;
    const spec = rebase(imp.spec, fromDir);
    if (!bySpec.has(spec)) bySpec.set(spec, []);
    bySpec.get(spec).push({ name, ...imp });
  }
  const lines = [];
  // In the original file's order (a module's evaluation order follows its imports').
  const order = (spec) => importStatements.findIndex((st) => rebase(st.moduleSpecifier.text, fromDir) === spec);
  for (const [spec, list] of [...bySpec].sort((a, b) => order(a[0]) - order(b[0]))) {
    const star = list.find((x) => x.imported === "*");
    if (star) { lines.push(`import ${star.typeOnly || typeOnlyAll ? "type " : ""}* as ${star.name} from "${spec}";`); continue; }
    const def = list.find((x) => x.imported === "default");
    const named = list.filter((x) => x.imported !== "default").map((x) => {
      const as = x.imported === x.name ? x.name : `${x.imported} as ${x.name}`;
      return (x.typeOnly || typeOnlyAll) ? `type ${as}` : as;
    });
    if (!def && named.length && named.every((n) => n.startsWith("type "))) {
      lines.push(`import type { ${named.map((n) => n.slice(5)).join(", ")} } from "${spec}";`);
      continue;
    }
    const parts = [def ? def.name : null, named.length ? `{ ${named.join(", ")} }` : null].filter(Boolean).join(", ");
    lines.push(`import ${parts} from "${spec}";`);
  }
  return lines;
}

/** Names a node's identifiers resolve to through the file's imports. */
function importedNamesIn(nodes) {
  const out = new Set();
  for (const node of nodes) for (const id of identifiers(node)) {
    const sym = symbolOf(checker, id);
    const decl = sym?.declarations?.[0];
    if (decl && (ts.isImportSpecifier(decl) || ts.isImportClause(decl) || ts.isNamespaceImport(decl)) && decl.getSourceFile() === sf) out.add(id.text);
  }
  return out;
}
/** Module-level declarations of the file a node uses (not imports). */
function moduleNamesIn(nodes) {
  const out = new Set();
  for (const node of nodes) for (const id of identifiers(node)) {
    const sym = symbolOf(checker, id);
    const decl = sym?.declarations?.[0];
    if (decl && decl.getSourceFile() === sf && !within(decl, fn) && decl.parent && (decl.parent === sf || decl.parent.parent?.parent === sf || ts.isSourceFile(decl.parent))) out.add(id.text);
  }
  return out;
}

// ── each slot's free locals, in first-use order, with a type ──
const printedImports = new Set();
function typeFor(name, sym, id) {
  const decl = sym.declarations[0];
  if (ts.isVariableDeclaration(decl) && decl.initializer && ts.isCallExpression(decl.initializer) && ts.isIdentifier(decl.initializer.expression)) {
    const callee = decl.initializer.expression.text;
    if (!REACT_HOOKS.has(callee) && imports.has(callee)) { printedImports.add(callee); return `ReturnType<typeof ${callee}>`; }
  }
  let text = checker.typeToString(checker.getTypeOfSymbolAtLocation(sym, id), fn, ts.TypeFormatFlags.NoTruncation);
  text = text.replace(/import\("([^"]+)"\)\.(\w+)/g, (_, path, member) => {
    if (path.includes("@types/react")) { printedImports.add(`react:${member}`); return member; }
    printedImports.add(member);
    return member;
  });
  // A module-private alias of the source spelled out (types.ts cannot name it).
  text = text.replace(/\bOpenOutcome\b/g, '"opened" | "preparing" | "not_opened"');
  for (const word of text.match(/\b[A-Z]\w*\b/g) ?? []) printedImports.add(word);
  return text;
}
const slotNodes = { unopened: site.unopened, header: [site.header], collapsedRail: [site.collapsedRail], keyBar: [site.keyBar] };
const slotNames = {};
for (const [slot, nodes] of Object.entries(slotNodes)) {
  const names = new Map();
  for (const node of nodes) for (const id of identifiers(node)) {
    const sym = symbolOf(checker, id);
    const decl = sym?.declarations?.[0];
    if (!decl || !isLocalDecl(decl) || decl.getSourceFile() !== sf) continue;
    if (!within(decl, fn) || nodes.some((n) => within(decl, n))) continue;
    if (!names.has(id.text)) names.set(id.text, typeFor(id.text, sym, id));
  }
  slotNames[slot] = names;
}

// ── types.ts ──
const movedTypeStmts = sf.statements.filter((s) => (ts.isInterfaceDeclaration(s) || ts.isTypeAliasDeclaration(s)) && MOVED_TYPES.includes(s.name.text));
if (movedTypeStmts.length !== MOVED_TYPES.length) throw new Error("moved types missing");
const typeNames = new Set([...importedNamesIn(movedTypeStmts)]);
for (const n of printedImports) if (!n.startsWith("react:") && imports.has(n)) typeNames.add(n);
const reactTypes = new Set(["ReactNode", ...[...printedImports].filter((n) => n.startsWith("react:")).map((n) => n.slice(6))]);
for (const n of reactTypes) typeNames.delete(n);
const unknown = [...printedImports].filter((n) => !n.startsWith("react:") && !imports.has(n) && !MOVED_TYPES.includes(n)
  && !["ReturnType", "Promise", "Record", "Pick", "Omit", "Array", "Partial", "ReadonlyMap", "Map", "Set", "HTMLElement", "Range", "KeyboardEvent", "Element", "Event", "MouseEvent", "Exclude", "Readonly", "ReadonlyArray", "ReactNode"].includes(n));
if (unknown.length) console.error("types printed with names not imported:", unknown.join(", "));
const typesHeader = `// The scoped source's contracts: what a source window (and, until step 2 of the Reader's retirement, the standalone
// Reader screen) hands the source and gets back. Moved whole from screens/ReaderScreen.tsx; the Standalone* contexts
// are what the standalone screen's own branches read from the source (the names they read, nothing more).
`;
const typesImports = [
  `import type { ${[...reactTypes].sort().join(", ")} } from "react";`,
  ...importsFor(typeNames, SOURCE_DIR, { typeOnlyAll: true }).filter((l) => !/from "react";$/.test(l)),
];
const ctxInterfaces = Object.entries(SLOTS).map(([slot, typeName]) => {
  const fields = [...slotNames[slot]].map(([n, t]) => `  ${n}: ${t};`).join("\n");
  return `export interface ${typeName} {\n${fields}\n}`;
});
const shell = `/** The standalone screen's own branches, as functions of the source's state (absent in a source window). */
export interface StandaloneShell {
${Object.entries(SLOTS).map(([slot, t]) => `  ${slot}: (ctx: ${t}) => ReactNode;`).join("\n")}
}`;
const typesText = [typesHeader, typesImports.join("\n"), "", ...movedTypeStmts.map((s) => s.getFullText(sf).replace(/^\n+/, "")), "",
  ...ctxInterfaces.flatMap((t) => [t, ""]), shell, ""].join("\n");

// ── ScopedSource.tsx ──
const callFor = (slot) => `standalone ? standalone.${slot}({ ${[...slotNames[slot].keys()].join(", ")} }) : null`;
const edits = [
  { start: site.unopened[0].getStart(sf), end: site.unopened[1].getEnd(), text: `if (!render) return ${callFor("unopened")};` },
  { start: site.header.getStart(sf), end: site.header.getEnd(), text: `(${callFor("header")})` },
  { start: site.collapsedRail.getStart(sf), end: site.collapsedRail.getEnd(), text: callFor("collapsedRail") },
  { start: site.keyBar.getStart(sf), end: site.keyBar.getEnd(), text: callFor("keyBar") },
];
// The props: one more, the standalone shell.
const param = fn.parameters[0];
const binding = param.name;
const literal = param.type;
edits.push({ start: binding.elements[binding.elements.length - 1].getEnd(), end: binding.elements[binding.elements.length - 1].getEnd(),
  text: ",\n  standalone = null" });
edits.push({ start: literal.members[0].getFullStart(), end: literal.members[0].getFullStart(),
  text: "\n  /** The standalone Reader screen's own branches (its list, header, collapsed rail and key bar); absent in a source window. */\n  standalone?: StandaloneShell | null;" });
edits.push({ start: fn.name.getStart(sf), end: fn.name.getEnd(), text: "ScopedSource" });
let fnText = src.slice(fn.getFullStart(), fn.getEnd());
for (const e of [...edits].sort((a, b) => b.start - a.start)) {
  fnText = fnText.slice(0, e.start - fn.getFullStart()) + e.text + fnText.slice(e.end - fn.getFullStart());
}
const keptModuleStmts = sf.statements.filter((s) => !ts.isImportDeclaration(s) && s !== fn && !movedTypeStmts.includes(s));
const excluded = [...site.unopened, site.header, site.collapsedRail, site.keyBar];
// The names the moved code still uses through imports (the slots' own names leave with them).
const usedBySource = new Set();
for (const node of [...keptModuleStmts, fn]) for (const id of identifiers(node, excluded)) {
  const sym = symbolOf(checker, id);
  const decl = sym?.declarations?.[0];
  if (decl && (ts.isImportSpecifier(decl) || ts.isImportClause(decl) || ts.isNamespaceImport(decl)) && decl.getSourceFile() === sf) usedBySource.add(id.text);
}
for (const t of MOVED_TYPES) usedBySource.delete(t);
const leadingComment = src.slice(0, importStatements[0].getStart(sf));
const sourceImports = [
  ...importsFor(usedBySource, SOURCE_DIR),
  `import type { ${[...MOVED_TYPES.filter((t) => new RegExp(`\\b${t}\\b`).test(fnText + keptModuleStmts.map((s) => s.getText(sf)).join("\n"))), "StandaloneShell"].sort().join(", ")} } from "./types";`,
];
// Module-level names the standalone branches read are exported from the source (the only change to a moved statement).
const slotModuleNames = moduleNamesIn(excluded);
const exportIfRead = (stmt) => {
  const text = stmt.getFullText(sf).replace(/^\n+/, "");
  const declared = ts.isVariableStatement(stmt) ? stmt.declarationList.declarations.map((d) => d.name.getText(sf)) : [stmt.name?.text];
  return declared.some((n) => slotModuleNames.has(n)) && !/^export /.test(stmt.getText(sf)) ? text.replace(stmt.getText(sf), `export ${stmt.getText(sf)}`) : text;
};
const sourceText = [leadingComment.trimEnd(), "", sourceImports.join("\n"), "",
  keptModuleStmts.map(exportIfRead).join("\n"), "", fnText.replace(/^\n+/, ""), ""].join("\n");

// ── the new ReaderScreen.tsx ──
const slotFns = Object.entries(SLOTS).map(([slot, typeName]) => {
  const names = [...slotNames[slot].keys()].join(", ");
  if (slot === "unopened") {
    const body = src.slice(site.unopened[0].getStart(sf), site.unopened[1].getEnd());
    return `function unopened({ ${names} }: ${typeName}): ReactNode {\n  ${body}\n  return null;\n}`;
  }
  const node = site[slot];
  return `function ${slot}({ ${names} }: ${typeName}): ReactNode {\n  return ${src.slice(node.getStart(sf), node.getEnd())};\n}`;
});
const shellImports = importedNamesIn(excluded);
const moduleUsed = moduleNamesIn(excluded);
const readerText = [
  `// The standalone Reader screen: the scoped source (screens/desks/source/ScopedSource.tsx) with the branches only this
// screen has (the list of books, the old header, the collapsed rail's handle and the key bar), as functions of the
// source's state. A source window mounts the same source without them. Step 2 of the Reader's retirement deletes this
// file with its standalone-only state.`,
  `import type { ComponentProps, ReactNode } from "react";`,
  ...importsFor(shellImports, SCREENS).filter((l) => !/from "react";$/.test(l)),
  `import { ${["ScopedSource", ...moduleUsed].sort().join(", ")} } from "./desks/source/ScopedSource";`,
  `import type { ${["StandaloneShell", ...Object.values(SLOTS)].sort().join(", ")} } from "./desks/source/types";`,
  "",
  `export function ReaderScreen(props: Omit<ComponentProps<typeof ScopedSource>, "standalone">) {
  return <ScopedSource {...props} standalone={STANDALONE} />;
}`,
  "",
  ...slotFns.flatMap((f) => [f, ""]),
  `const STANDALONE: StandaloneShell = { ${Object.keys(SLOTS).join(", ")} };`,
  "",
].join("\n");

mkdirSync(SOURCE_DIR, { recursive: true });
writeFileSync(join(SOURCE_DIR, "types.ts"), typesText);
writeFileSync(join(SOURCE_DIR, "ScopedSource.tsx"), sourceText);
writeFileSync(OLD, readerText);
writeFileSync(join(dirname(process.argv[1]), "slots.json"), JSON.stringify(Object.fromEntries(Object.entries(slotNames).map(([k, v]) => [k, [...v.keys()]])), null, 1));
console.log("written; slot names:", Object.fromEntries(Object.entries(slotNames).map(([k, v]) => [k, v.size])));
