// The proof of phase 2 step 1: every moved definition is the same AST, and every name in it resolves to the same thing.
// Usage: APP_DIR=<app> node check.mjs <original ReaderScreen.tsx (a copy)>
// The original is placed beside its old path for the check (so its relative imports resolve as they did) and removed.
import { copyFileSync, rmSync } from "node:fs";
import { join, relative } from "node:path";
import { ts, program, identifiers, symbolOf, within, walk } from "./common.mjs";
import { mainFunction, sites } from "./sites.mjs";

const APP = process.env.APP_DIR;
const SCREENS = join(APP, "src/screens");
const ORIG = join(SCREENS, "__orig_ReaderScreen.tsx");
const NEW_SOURCE = join(SCREENS, "desks/source/ScopedSource.tsx");
const NEW_TYPES = join(SCREENS, "desks/source/types.ts");
const NEW_SCREEN = join(SCREENS, "ReaderScreen.tsx");
copyFileSync(process.argv[2], ORIG);
let failures = 0;
const fail = (msg) => { failures += 1; console.log(`FAIL ${msg}`); };
const ok = (msg) => console.log(`ok   ${msg}`);
try {
  const prog = program([ORIG, NEW_SOURCE, NEW_TYPES, NEW_SCREEN]);
  const checker = prog.getTypeChecker();
  const oldSf = prog.getSourceFile(ORIG), srcSf = prog.getSourceFile(NEW_SOURCE), typesSf = prog.getSourceFile(NEW_TYPES), screenSf = prog.getSourceFile(NEW_SCREEN);
  const MOVED = new Set([oldSf, srcSf, typesSf, screenSf].map((f) => f.fileName));
  const oldFn = mainFunction(oldSf, "ReaderScreen");
  const newFn = mainFunction(srcSf, "ScopedSource");
  const site = sites(oldFn);
  const SLOT_NAMES = ["unopened", "header", "collapsedRail", "keyBar"];
  const oldSlotNodes = { unopened: site.unopened, header: [site.header], collapsedRail: [site.collapsedRail], keyBar: [site.keyBar] };
  const oldExcluded = Object.values(oldSlotNodes).flat();

  // The new function's slot calls (`standalone ? standalone.X({...}) : null`) and the added prop.
  const newCalls = {};
  walk(newFn, (node) => {
    if (ts.isConditionalExpression(node) && ts.isIdentifier(node.condition) && node.condition.text === "standalone"
      && ts.isCallExpression(node.whenTrue) && ts.isPropertyAccessExpression(node.whenTrue.expression)) newCalls[node.whenTrue.expression.name.text] = node;
  });
  const unopenedStmt = newFn.body.statements.find((s) => ts.isIfStatement(s) && s.getText(srcSf).includes("standalone.unopened("));
  const standaloneBinding = newFn.parameters[0].name.elements.find((e) => e.name.text === "standalone");
  const standaloneMember = newFn.parameters[0].type.members.find((m) => m.name?.text === "standalone");
  if (!unopenedStmt || SLOT_NAMES.some((n) => !newCalls[n]) || !standaloneBinding || !standaloneMember) fail("the new function's slot calls or standalone prop not found");
  const newExcluded = [unopenedStmt, newCalls.header, newCalls.collapsedRail, newCalls.keyBar, standaloneBinding, standaloneMember];

  // ── keys: what a name resolves to, independent of where the text sits ──
  const DECL_KINDS = new Set([ts.SyntaxKind.VariableDeclaration, ts.SyntaxKind.BindingElement, ts.SyntaxKind.Parameter, ts.SyntaxKind.FunctionDeclaration,
    ts.SyntaxKind.PropertySignature, ts.SyntaxKind.PropertyAssignment, ts.SyntaxKind.ShorthandPropertyAssignment, ts.SyntaxKind.MethodDeclaration,
    ts.SyntaxKind.InterfaceDeclaration, ts.SyntaxKind.TypeAliasDeclaration, ts.SyntaxKind.TypeParameter, ts.SyntaxKind.PropertyDeclaration,
    ts.SyntaxKind.EnumMember, ts.SyntaxKind.MethodSignature, ts.SyntaxKind.JsxAttribute, ts.SyntaxKind.FunctionExpression, ts.SyntaxKind.ClassDeclaration]);
  function ordinals(roots, excluded) {
    const out = new Map(), seen = new Map();
    for (const root of roots) walk(root, (node) => {
      if (!DECL_KINDS.has(node.kind) || !node.name || !ts.isIdentifier(node.name)) return;
      if (excluded.some((ex) => within(node, ex))) return;
      const k = `${node.name.text}:${node.kind}`;
      seen.set(k, (seen.get(k) ?? 0) + 1);
      out.set(node, `${k}:${seen.get(k)}`);
    });
    return out;
  }
  const regions = [
    { name: "fn", roots: [oldFn], excluded: oldExcluded },
    { name: "fn", roots: [newFn], excluded: newExcluded },
    ...SLOT_NAMES.map((n) => ({ name: `slot`, roots: oldSlotNodes[n], excluded: [] })),
  ];
  const slotFns = Object.fromEntries(SLOT_NAMES.map((n) => [n, mainFunction(screenSf, n)]));
  for (const n of SLOT_NAMES) regions.push({ name: "slot", roots: [slotFns[n].body], excluded: [], ctxOf: slotFns[n] });
  for (const r of regions) r.ord = ordinals(r.roots, r.excluded);
  function keyOf(id, slotRoots = null) {
    let sym = symbolOf(checker, id);
    if (!sym) return "none";
    if (sym.flags & ts.SymbolFlags.Alias) sym = checker.getAliasedSymbol(sym);
    const decl = sym.declarations?.[0];
    if (!decl) return `sym:${sym.name}`;
    const file = decl.getSourceFile().fileName;
    if (!MOVED.has(file)) return `ext:${relative(APP, file)}:${sym.name}:${decl.kind}:${decl.pos}`;
    for (const sf of [screenSf]) for (const n of SLOT_NAMES) {
      const f = slotFns[n];
      if (decl.getSourceFile() === sf && within(decl, f.parameters[0])) return `ctx:${sym.name}`;
    }
    // A local of the old function read by a standalone branch: what the slot's context carries under its name.
    if (slotRoots && within(decl, oldFn) && !slotRoots.some((x) => within(decl, x))) return `ctx:${sym.name}`;
    for (const r of regions) if (r.ord.has(decl)) return `${r.name}:${r.ord.get(decl)}`;
    // A local of the old function read by a slot: what the slot's context carries under its name.
    if (within(decl, oldFn)) return `ctx:${sym.name}`;
    return `mod:${sym.name}:${decl.kind}`;
  }
  function stream(roots, excluded = [], slotRoots = null) {
    return roots.flatMap((r) => identifiers(r, excluded)).map((id) => `${id.text}=${keyOf(id, slotRoots)}`);
  }
  function sameStreams(label, a, b) {
    if (a.length !== b.length) return fail(`${label}: ${a.length} names before, ${b.length} after`);
    const at = a.findIndex((x, i) => x !== b[i]);
    if (at >= 0) return fail(`${label}: name ${at} resolves differently: ${a[at]} vs ${b[at]}`);
    ok(`${label}: ${a.length} names resolve as before`);
  }
  // ── printed text (comments and layout ignored), with the replaced parts standing as one placeholder each ──
  const printer = ts.createPrinter({ removeComments: true });
  function printWith(node, sf, replace) {
    const result = ts.transform(node, [(ctx) => {
      const visit = (n) => {
        const r = replace(n);
        if (r) return r;
        return ts.visitEachChild(n, visit, ctx);
      };
      return (root) => ts.visitNode(root, visit);
    }]);
    const text = printer.printNode(ts.EmitHint.Unspecified, result.transformed[0], sf);
    result.dispose();
    return text;
  }
  const placeholder = (name) => ts.factory.createIdentifier(`__${name}__`);
  const stmtPlaceholder = (name) => ts.factory.createExpressionStatement(placeholder(name));

  // 1. Module-level statements: each old one is in the source or the contracts, the same.
  for (const stmt of oldSf.statements) {
    if (ts.isImportDeclaration(stmt) || stmt === oldFn) continue;
    const names = ts.isVariableStatement(stmt) ? stmt.declarationList.declarations.map((d) => d.name.getText(oldSf)) : [stmt.name?.text];
    const target = [srcSf, typesSf].flatMap((f) => f.statements).find((s) => {
      const n = ts.isVariableStatement(s) ? s.declarationList.declarations.map((d) => d.name.getText(s.getSourceFile())) : [s.name?.text];
      return n.join() === names.join();
    });
    if (!target) { fail(`${names} not found after the move`); continue; }
    const strip = (n) => (n.kind === ts.SyntaxKind.ExportKeyword ? ts.factory.createIdentifier("") : undefined);
    const before = printWith(stmt, oldSf, () => undefined).replace(/^export /, "");
    const after = printWith(target, target.getSourceFile(), () => undefined).replace(/^export /, "");
    void strip;
    if (before !== after) fail(`${names}: changed`);
    sameStreams(`${names.join(",")} (${relative(SCREENS, target.getSourceFile().fileName)})`, stream([stmt]), stream([target]));
  }

  // 2. The function: the same, but for its name, the one added prop and the four places the standalone branches were.
  const oldPrinted = printWith(oldFn, oldSf, (n) => {
    if (n === site.unopened[0]) return stmtPlaceholder("unopened");
    if (n === site.unopened[1]) return ts.factory.createEmptyStatement();
    if (n === site.header) return placeholder("header");
    if (n === site.collapsedRail) return placeholder("collapsedRail");
    if (n === site.keyBar) return placeholder("keyBar");
    if (n === oldFn.name) return ts.factory.createIdentifier("Fn");
    return undefined;
  }).replace(/\n\s*;\n/g, "\n");
  const newPrinted = printWith(newFn, srcSf, (n) => {
    if (n === unopenedStmt) return stmtPlaceholder("unopened");
    if (n === newCalls.header) return placeholder("header");
    if (n === newCalls.collapsedRail) return placeholder("collapsedRail");
    if (n === newCalls.keyBar) return placeholder("keyBar");
    if (n === newFn.name) return ts.factory.createIdentifier("Fn");
    return undefined;
  }).replace(/,\s*standalone = null/, "").replace(/\n\s*standalone\?: StandaloneShell \| null;/, "").replace(/\(__header__\)/, "__header__");
  if (oldPrinted !== newPrinted) {
    const a = oldPrinted.split("\n"), b = newPrinted.split("\n");
    const at = a.findIndex((x, i) => x !== b[i]);
    fail(`ScopedSource differs from ReaderScreen at printed line ${at}:\n  before: ${a[at]}\n  after:  ${b[at]}`);
  } else ok(`ScopedSource is ReaderScreen's function (${oldPrinted.split("\n").length} printed lines) but for its name, the standalone prop and the four slot calls`);
  // The function's own name is the one rename.
  sameStreams("ScopedSource's names", stream([oldFn], [...oldExcluded, oldFn.name]), stream([newFn], [...newExcluded, newFn.name]));

  // 3. The slots: each standalone branch is the same text in the new ReaderScreen, reading the same locals from its context.
  for (const n of SLOT_NAMES) {
    const f = slotFns[n];
    const body = f.body.statements;
    const newNodes = n === "unopened" ? body.slice(0, 2) : [body[0].expression];
    const before = oldSlotNodes[n].map((x) => printWith(x, oldSf, () => undefined)).join("\n");
    const after = newNodes.map((x) => printWith(x, screenSf, () => undefined)).join("\n");
    if (before !== after) fail(`slot ${n}: its text changed`);
    else ok(`slot ${n}: the same text`);
    sameStreams(`slot ${n}`, stream(oldSlotNodes[n], [], oldSlotNodes[n]), stream(newNodes));
    if (n === "unopened" && !(body.length === 3 && body[2].getText(screenSf) === "return null;")) fail("unopened: more than its two branches and `return null;`");
    // The call passes exactly the names the slot reads, each the same local as before.
    const ctxNames = f.parameters[0].name.elements.map((e) => e.name.text);
    const call = newCalls[n].whenTrue;
    const passed = call.arguments[0].properties;
    if (passed.map((p) => p.name.text).join() !== ctxNames.join() || !passed.every(ts.isShorthandPropertyAssignment)) fail(`slot ${n}: the call passes other names than the slot reads`);
    const oldLocal = new Map();
    for (const id of oldSlotNodes[n].flatMap((x) => identifiers(x))) {
      const sym = symbolOf(checker, id);
      const decl = sym?.declarations?.[0];
      if (decl && within(decl, oldFn) && !oldSlotNodes[n].some((x) => within(decl, x))) {
        for (const r of regions.slice(0, 1)) if (r.ord.has(decl)) oldLocal.set(id.text, `fn:${r.ord.get(decl)}`);
      }
    }
    const mism = passed.filter((p) => keyOf(p.name) !== oldLocal.get(p.name.text));
    if (mism.length || oldLocal.size !== passed.length) fail(`slot ${n}: passed names resolve elsewhere: ${mism.map((p) => p.name.text)} (${oldLocal.size} read, ${passed.length} passed)`);
    else ok(`slot ${n}: the call passes its ${passed.length} names, each the local it read before`);
  }
} finally {
  rmSync(ORIG, { force: true });
}
console.log(failures ? `${failures} failure(s)` : "the move is the same code with the same names");
process.exit(failures ? 1 : 0);
