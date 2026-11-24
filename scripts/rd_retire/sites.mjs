// The standalone-only sites of the old ReaderScreen function, found by shape (not line numbers).
import { ts, walk } from "./common.mjs";

export function mainFunction(sf, name) {
  let found = null;
  ts.forEachChild(sf, (node) => {
    if (ts.isFunctionDeclaration(node) && node.name?.text === name) found = node;
  });
  if (!found) throw new Error(`no function ${name}`);
  return found;
}

const text = (node) => node.getText().replace(/\s+/g, " ").trim();

/** { unopened: [stmt, stmt], header: expr, collapsedRail: expr, keyBar: expr } in the old function. */
export function sites(fn) {
  const body = fn.body.statements;
  const i = body.findIndex((s) => ts.isIfStatement(s) && text(s.expression) === "!render && opening && openingTitle");
  if (i < 0 || !(ts.isIfStatement(body[i + 1]) && text(body[i + 1].expression) === "!render")) throw new Error("unopened branches not found");
  const ret = body[body.length - 1];
  if (!ts.isReturnStatement(ret)) throw new Error("no final return");
  let header = null, collapsedRail = null, keyBar = null;
  walk(ret, (node) => {
    if (!ts.isJsxExpression(node) || !node.expression || !ts.isConditionalExpression(node.expression)) return;
    const c = node.expression;
    const cond = text(c.condition);
    if (cond === "windowed" && text(c.whenTrue) === "null" && /^<KeyBar\b/.test(text(c.whenFalse))) keyBar = c;
    else if (cond === "windowed" && !header && text(c.whenFalse).includes(">READER<")) header = c.whenFalse;
    else if (cond.startsWith("!windowed && ((inquiry && railCollapsed) || sbsPanes)")) collapsedRail = c;
  });
  if (!header || !collapsedRail || !keyBar) throw new Error(`sites missing: ${[header, collapsedRail, keyBar].map(Boolean)}`);
  return { unopened: [body[i], body[i + 1]], header, collapsedRail, keyBar };
}
