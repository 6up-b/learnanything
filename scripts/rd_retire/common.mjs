// Shared helpers for the extraction and its proof (TypeScript compiler API).
import { createRequire } from "node:module";
import { join } from "node:path";

export const APP = process.env.APP_DIR;
const require = createRequire(join(APP, "package.json"));
export const ts = require("typescript");

export function program(files) {
  const config = ts.readConfigFile(join(APP, "tsconfig.json"), ts.sys.readFile);
  const parsed = ts.parseJsonConfigFileContent(config.config, ts.sys, APP);
  return ts.createProgram({ rootNames: files, options: { ...parsed.options, noEmit: true } });
}

export function walk(node, visit) {
  visit(node);
  ts.forEachChild(node, (child) => walk(child, visit));
}

export function within(inner, outer) {
  return inner.getStart() >= outer.getStart() && inner.getEnd() <= outer.getEnd();
}

/** The symbol an identifier names (a shorthand property's value, not the property). */
export function symbolOf(checker, id) {
  if (id.parent && ts.isShorthandPropertyAssignment(id.parent) && id.parent.name === id) {
    return checker.getShorthandAssignmentValueSymbol(id.parent);
  }
  return checker.getSymbolAtLocation(id);
}

export function isLocalDecl(decl) {
  return ts.isVariableDeclaration(decl) || ts.isBindingElement(decl) || ts.isParameter(decl) || ts.isFunctionDeclaration(decl)
    || ts.isClassDeclaration(decl);
}

/** Every identifier under a node, in order, skipping those under any of the excluded nodes. */
export function identifiers(root, excluded = []) {
  const out = [];
  walk(root, (node) => {
    if (ts.isIdentifier(node) && !excluded.some((ex) => within(node, ex))) out.push(node);
  });
  return out;
}

/** Tokens of a text, trivia (spaces, comments) skipped. */
export function tokens(text) {
  const scanner = ts.createScanner(ts.ScriptTarget.Latest, true, ts.LanguageVariant.JSX, text);
  const out = [];
  let kind = scanner.scan();
  while (kind !== ts.SyntaxKind.EndOfFileToken) {
    out.push(scanner.getTokenText());
    kind = kind === ts.SyntaxKind.GreaterThanToken ? scanner.reScanGreaterToken() : kind;
    kind = scanner.scan();
  }
  return out;
}
