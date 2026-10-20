// The figure grammar's TypeScript twin (reader workbench RW5a; spec §8.2, G21, G22).
//
// A hand-written tokenizer, recursive-descent parser and tree-walking
// evaluator, line for line the Python twin in src/learnloop/figures/grammar.py.
// No generated code runs: nothing here builds or executes code from text (a
// vitest scan pins it). Arithmetic is IEEE doubles; the integral is the same
// fixed adaptive Simpson rule (one-sided endpoint values, the same tolerance,
// levels and evaluation budget) and the sum is exact over the integers. One
// golden corpus (figureGoldenCorpus.json) is run by both test suites.

export const MAX_EXPR_CHARS = 2000;
export const MAX_NODES = 400;
export const MAX_DEPTH = 40;
export const MAX_EXPANDED_NODES = 4000;
export const MAX_NAME_CHARS = 32;
export const MAX_SUM_TERMS = 10001;
export const SIMPSON_EPS = 1e-10;
export const SIMPSON_MIN_LEVEL = 3;
export const SIMPSON_MAX_LEVEL = 24;
export const SIMPSON_NUDGE = Math.pow(2, -40);
export const MAX_INTEGRAND_EVALS = 200000;

export const FUNCTIONS: Record<string, [number, number]> = {
  exp: [1, 1], log: [1, 1], sqrt: [1, 1], abs: [1, 1], sin: [1, 1], cos: [1, 1],
  tan: [1, 1], atan: [1, 1], erf: [1, 1], Phi: [1, 1], floor: [1, 1],
  min: [2, 8], max: [2, 8],
};
const SPECIAL_FORMS = ["piecewise", "integral", "sum"];
export const CONSTANTS: Record<string, number> = { pi: Math.PI, e: Math.E };
const KEYWORDS = ["and", "or"];
export const RESERVED = new Set<string>([...Object.keys(FUNCTIONS), ...SPECIAL_FORMS, ...Object.keys(CONSTANTS), ...KEYWORDS]);
const COMPARISONS = ["<=", ">=", "==", "!=", "<", ">"];

export class FigureGrammarError extends Error {}

export type NodeKind = "num" | "name" | "neg" | "bin" | "call" | "piecewise" | "integral" | "sum" | "cmp" | "and" | "or";

export interface FigureNode {
  kind: NodeKind;
  text: string;
  op: string;
  value: number;
  args: FigureNode[];
}

type Token = [kind: "number" | "name" | "op", text: string];

const TOKEN = /[ \t\r\n]*(?:((?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)|([A-Za-z_][A-Za-z0-9_]*)|(<=|>=|==|!=|[-+*/^(),<>]))/y;
const BLANK = /^[ \t\r\n]*$/;
const NAME = /^[A-Za-z_][A-Za-z0-9_]*$/;

export function isName(text: string): boolean {
  return NAME.test(text ?? "") && text.length <= MAX_NAME_CHARS;
}

function tokenize(source: string): Token[] {
  if (typeof source !== "string") throw new FigureGrammarError("an expression must be text");
  if (source.length > MAX_EXPR_CHARS) throw new FigureGrammarError(`expression longer than ${MAX_EXPR_CHARS} characters`);
  const tokens: Token[] = [];
  let position = 0;
  while (position < source.length) {
    if (BLANK.test(source.slice(position))) break;
    TOKEN.lastIndex = position;
    const match = TOKEN.exec(source);
    if (!match || match.index !== position || TOKEN.lastIndex === position) {
      throw new FigureGrammarError(`unexpected character ${JSON.stringify(source.slice(position).trimStart().slice(0, 1))}`);
    }
    if (match[1] !== undefined) tokens.push(["number", match[1]]);
    else if (match[2] !== undefined) {
      if (match[2].length > MAX_NAME_CHARS) throw new FigureGrammarError(`name longer than ${MAX_NAME_CHARS} characters`);
      tokens.push(["name", match[2]]);
    } else tokens.push(["op", match[3] as string]);
    position = TOKEN.lastIndex;
  }
  return tokens;
}

function mk(kind: NodeKind, values: Partial<FigureNode> = {}): FigureNode {
  return { kind, text: values.text ?? "", op: values.op ?? "", value: values.value ?? 0, args: values.args ?? [] };
}

class Parser {
  private tokens: Token[];
  private position = 0;
  private nodes = 0;

  constructor(source: string) {
    this.tokens = tokenize(source);
  }

  private peek(offset = 0): Token | null {
    const index = this.position + offset;
    return index < this.tokens.length ? this.tokens[index] : null;
  }

  private take(): Token {
    const token = this.peek();
    if (!token) throw new FigureGrammarError("unexpected end of expression");
    this.position += 1;
    return token;
  }

  private expect(text: string): void {
    const token = this.take();
    if (token[1] !== text || token[0] === "name") throw new FigureGrammarError(`expected ${JSON.stringify(text)}, found ${JSON.stringify(token[1])}`);
  }

  private at(text: string): boolean {
    const token = this.peek();
    return token !== null && token[0] === "op" && token[1] === text;
  }

  private node(kind: NodeKind, depth: number, values: Partial<FigureNode> = {}): FigureNode {
    this.nodes += 1;
    if (this.nodes > MAX_NODES) throw new FigureGrammarError(`expression has more than ${MAX_NODES} nodes`);
    if (depth > MAX_DEPTH) throw new FigureGrammarError(`expression nested deeper than ${MAX_DEPTH}`);
    return mk(kind, values);
  }

  parse(): FigureNode {
    if (!this.tokens.length) throw new FigureGrammarError("empty expression");
    const node = this.expression(0);
    if (this.position !== this.tokens.length) throw new FigureGrammarError(`unexpected ${JSON.stringify(this.tokens[this.position][1])}`);
    return node;
  }

  expression(depth: number): FigureNode {
    if (depth > MAX_DEPTH) throw new FigureGrammarError(`expression nested deeper than ${MAX_DEPTH}`);
    let node = this.term(depth + 1);
    while (this.at("+") || this.at("-")) {
      const op = this.take()[1];
      node = this.node("bin", depth, { op, args: [node, this.term(depth + 1)] });
    }
    return node;
  }

  term(depth: number): FigureNode {
    let node = this.unary(depth + 1);
    while (this.at("*") || this.at("/")) {
      const op = this.take()[1];
      node = this.node("bin", depth, { op, args: [node, this.unary(depth + 1)] });
    }
    return node;
  }

  unary(depth: number): FigureNode {
    if (depth > MAX_DEPTH) throw new FigureGrammarError(`expression nested deeper than ${MAX_DEPTH}`);
    if (this.at("-")) {
      this.take();
      return this.node("neg", depth, { args: [this.unary(depth + 1)] });
    }
    return this.power(depth + 1);
  }

  power(depth: number): FigureNode {
    const base = this.primary(depth + 1);
    if (this.at("^")) {
      this.take();
      return this.node("bin", depth, { op: "^", args: [base, this.unary(depth + 1)] });
    }
    return base;
  }

  primary(depth: number): FigureNode {
    if (depth > MAX_DEPTH) throw new FigureGrammarError(`expression nested deeper than ${MAX_DEPTH}`);
    const [kind, text] = this.take();
    if (kind === "number") {
      const value = parseFloat(text);
      if (!Number.isFinite(value)) throw new FigureGrammarError(`number ${JSON.stringify(text)} is not finite`);
      return this.node("num", depth, { text, value });
    }
    if (kind === "op") {
      if (text === "(") {
        const node = this.expression(depth + 1);
        this.expect(")");
        return node;
      }
      throw new FigureGrammarError(`unexpected ${JSON.stringify(text)}`);
    }
    if (KEYWORDS.includes(text)) throw new FigureGrammarError(`${JSON.stringify(text)} belongs only in a piecewise condition`);
    if (this.at("(")) {
      if (Object.prototype.hasOwnProperty.call(FUNCTIONS, text)) return this.call(text, depth);
      if (text === "piecewise") return this.piecewise(depth);
      if (text === "integral" || text === "sum") return this.boundForm(text, depth);
      throw new FigureGrammarError(`unknown function ${JSON.stringify(text)}`);
    }
    if (Object.prototype.hasOwnProperty.call(FUNCTIONS, text) || SPECIAL_FORMS.includes(text)) {
      throw new FigureGrammarError(`${JSON.stringify(text)} must be called`);
    }
    return this.node("name", depth, { text });
  }

  call(name: string, depth: number): FigureNode {
    this.expect("(");
    const args = [this.expression(depth + 1)];
    while (this.at(",")) {
      this.take();
      args.push(this.expression(depth + 1));
    }
    this.expect(")");
    const [low, high] = FUNCTIONS[name];
    if (args.length < low || args.length > high) throw new FigureGrammarError(`${name} takes ${low} argument(s) or more`);
    return this.node("call", depth, { text: name, args });
  }

  piecewise(depth: number): FigureNode {
    this.expect("(");
    const args: FigureNode[] = [];
    while (this.at("(") && this.isBranch()) {
      this.take();
      args.push(this.condition(depth + 1));
      this.expect(",");
      args.push(this.expression(depth + 1));
      this.expect(")");
      this.expect(",");
    }
    if (!args.length) throw new FigureGrammarError("piecewise needs at least one (condition, value) branch");
    args.push(this.expression(depth + 1));
    this.expect(")");
    return this.node("piecewise", depth, { args });
  }

  private isBranch(): boolean {
    let level = 0;
    for (let index = this.position; index < this.tokens.length; index += 1) {
      const [kind, text] = this.tokens[index];
      if (kind === "op" && text === "(") level += 1;
      else if (kind === "op" && text === ")") {
        level -= 1;
        if (level === 0) return false;
      } else if (level === 1 && kind === "op" && text === ",") return false;
      else if (level === 1 && ((kind === "op" && COMPARISONS.includes(text)) || (kind === "name" && KEYWORDS.includes(text)))) return true;
    }
    return false;
  }

  condition(depth: number): FigureNode {
    const parts = [this.conjunction(depth + 1)];
    while (this.peekIs("name", "or")) {
      this.take();
      parts.push(this.conjunction(depth + 1));
    }
    return parts.length === 1 ? parts[0] : this.node("or", depth, { args: parts });
  }

  conjunction(depth: number): FigureNode {
    const parts = [this.comparison(depth + 1)];
    while (this.peekIs("name", "and")) {
      this.take();
      parts.push(this.comparison(depth + 1));
    }
    return parts.length === 1 ? parts[0] : this.node("and", depth, { args: parts });
  }

  private peekIs(kind: string, text: string): boolean {
    const token = this.peek();
    return token !== null && token[0] === kind && token[1] === text;
  }

  comparison(depth: number): FigureNode {
    const left = this.expression(depth + 1);
    const token = this.peek();
    if (!token || token[0] !== "op" || !COMPARISONS.includes(token[1])) throw new FigureGrammarError("a piecewise condition must be a comparison");
    this.take();
    const right = this.expression(depth + 1);
    const follow = this.peek();
    if (follow && follow[0] === "op" && COMPARISONS.includes(follow[1])) throw new FigureGrammarError("chain comparisons with 'and'");
    return this.node("cmp", depth, { op: token[1], args: [left, right] });
  }

  boundForm(name: "integral" | "sum", depth: number): FigureNode {
    this.expect("(");
    const body = this.expression(depth + 1);
    this.expect(",");
    const [kind, variable] = this.take();
    if (kind !== "name" || RESERVED.has(variable)) throw new FigureGrammarError(`${name}'s second argument must be a variable name`);
    this.expect(",");
    const lower = this.expression(depth + 1);
    this.expect(",");
    const upper = this.expression(depth + 1);
    this.expect(")");
    return this.node(name, depth, { text: variable, args: [body, lower, upper] });
  }
}

/** Parse one expression, or throw FigureGrammarError (nothing is evaluated). */
export function parseExpression(source: string): FigureNode {
  return new Parser(source).parse();
}

// ---------------------------------------------------------------------------
// Static checks over a figure's names
// ---------------------------------------------------------------------------

export function* walk(node: FigureNode): Generator<FigureNode> {
  yield node;
  for (const child of node.args) yield* walk(child);
}

export type Definitions = Map<string, FigureNode>;

export function freeNames(node: FigureNode, bound: Set<string> = new Set()): Set<string> {
  if (node.kind === "name") return bound.has(node.text) || node.text in CONSTANTS ? new Set() : new Set([node.text]);
  if (node.kind === "integral" || node.kind === "sum") {
    const [body, lower, upper] = node.args;
    return new Set([...freeNames(body, new Set([...bound, node.text])), ...freeNames(lower, bound), ...freeNames(upper, bound)]);
  }
  const found = new Set<string>();
  for (const child of node.args) for (const name of freeNames(child, bound)) found.add(name);
  return found;
}

export function nodeCount(node: FigureNode, definitions: Definitions, seen: string[] = []): number {
  if (node.kind === "name" && definitions.has(node.text) && !seen.includes(node.text)) {
    return nodeCount(definitions.get(node.text) as FigureNode, definitions, [...seen, node.text]);
  }
  return 1 + node.args.reduce((total, child) => total + nodeCount(child, definitions, seen), 0);
}

export function hasBoundForm(node: FigureNode, definitions: Definitions, seen: string[] = []): boolean {
  if (node.kind === "integral" || node.kind === "sum") return true;
  if (node.kind === "name" && definitions.has(node.text) && !seen.includes(node.text)) {
    return hasBoundForm(definitions.get(node.text) as FigureNode, definitions, [...seen, node.text]);
  }
  return node.args.some((child) => hasBoundForm(child, definitions, seen));
}

export function checkNames(node: FigureNode, known: Set<string>, definitions: Definitions): void {
  for (const name of [...freeNames(node)].sort()) {
    if (!known.has(name) && !definitions.has(name)) throw new FigureGrammarError(`unknown name ${JSON.stringify(name)}`);
  }
  for (const child of walk(node)) {
    if (child.kind === "integral" || child.kind === "sum") {
      if (definitions.has(child.text)) throw new FigureGrammarError(`${child.kind} variable ${JSON.stringify(child.text)} is a definition's name`);
      if (hasBoundForm(child.args[0], definitions)) throw new FigureGrammarError("no integral or sum inside an integral or sum");
      for (const bound of child.args.slice(1)) {
        if (hasBoundForm(bound, definitions)) throw new FigureGrammarError("no integral or sum inside an integral's or sum's bounds");
      }
    }
  }
  if (nodeCount(node, definitions) > MAX_EXPANDED_NODES) throw new FigureGrammarError(`expression expands to more than ${MAX_EXPANDED_NODES} nodes`);
}

// ---------------------------------------------------------------------------
// Evaluation (IEEE doubles)
// ---------------------------------------------------------------------------

// erf and erfc: Sun's fdlibm (s_erf.c), as JavaScript has none; within a few
// ulps of the C library's, which the Python twin calls.
const ERX = 8.45062911510467529297e-01;
const EFX = 1.28379167095512586316e-01;
const PP = [1.28379167095512558561e-01, -3.25042107247001499370e-01, -2.84817495755985104766e-02, -5.77027029648944159157e-03, -2.37630166566501626084e-05];
const QQ = [0, 3.97917223959155352819e-01, 6.50222499887672944485e-02, 5.08130628187576562776e-03, 1.32494738004321644526e-04, -3.96022827877536812320e-06];
const PA = [-2.36211856075265944077e-03, 4.14856118683748331666e-01, -3.72207876035701323847e-01, 3.18346619901161753674e-01, -1.10894694282396677476e-01, 3.54783043256182359371e-02, -2.16637559486879084300e-03];
const QA = [0, 1.06420880400844228286e-01, 5.40397917702171048937e-01, 7.18286544141962662868e-02, 1.26171219808761642112e-01, 1.36370839120290507362e-02, 1.19844998467991074170e-02];
const RA = [-9.86494403484714822705e-03, -6.93858572707181764372e-01, -1.05586262253232909814e+01, -6.23753324503260060396e+01, -1.62396669462573470355e+02, -1.84605092906711035994e+02, -8.12874355063065934246e+01, -9.81432934416914548592e+00];
const SA = [0, 1.96512716674392571292e+01, 1.37657754143519042600e+02, 4.34565877475229228821e+02, 6.45387271733267880336e+02, 4.29008140027567833386e+02, 1.08635005541779435134e+02, 6.57024977031928170135e+00, -6.04244152148580987438e-02];
const RB = [-9.86494292470009928597e-03, -7.99283237680523006574e-01, -1.77579549177547519889e+01, -1.60636384855821916062e+02, -6.37566443368389627722e+02, -1.02509513161107724954e+03, -4.83519191608651397019e+02];
const SB = [0, 3.03380607434824582924e+01, 3.25792512996573918826e+02, 1.53672958608443695994e+03, 3.19985821950859553908e+03, 2.55305040643316442583e+03, 4.74528541206955367215e+02, -2.24409524465858183362e+01];

const scratch = new DataView(new ArrayBuffer(8));
function truncLow(value: number): number {
  scratch.setFloat64(0, value);
  scratch.setUint32(4, 0);
  return scratch.getFloat64(0);
}

function erfcTail(ax: number): number {
  const s = 1 / (ax * ax);
  let r: number;
  let q: number;
  if (ax < 1 / 0.35) {
    r = RA[0] + s * (RA[1] + s * (RA[2] + s * (RA[3] + s * (RA[4] + s * (RA[5] + s * (RA[6] + s * RA[7]))))));
    q = 1 + s * (SA[1] + s * (SA[2] + s * (SA[3] + s * (SA[4] + s * (SA[5] + s * (SA[6] + s * (SA[7] + s * SA[8])))))));
  } else {
    r = RB[0] + s * (RB[1] + s * (RB[2] + s * (RB[3] + s * (RB[4] + s * (RB[5] + s * RB[6])))));
    q = 1 + s * (SB[1] + s * (SB[2] + s * (SB[3] + s * (SB[4] + s * (SB[5] + s * (SB[6] + s * SB[7]))))));
  }
  const z = truncLow(ax);
  return (Math.exp(-z * z - 0.5625) * Math.exp((z - ax) * (z + ax) + r / q)) / ax;
}

function smallRatio(x: number): number {
  const z = x * x;
  const r = PP[0] + z * (PP[1] + z * (PP[2] + z * (PP[3] + z * PP[4])));
  const s = 1 + z * (QQ[1] + z * (QQ[2] + z * (QQ[3] + z * (QQ[4] + z * QQ[5]))));
  return r / s;
}

function midRatio(ax: number): number {
  const s = ax - 1;
  const p = PA[0] + s * (PA[1] + s * (PA[2] + s * (PA[3] + s * (PA[4] + s * (PA[5] + s * PA[6])))));
  const q = 1 + s * (QA[1] + s * (QA[2] + s * (QA[3] + s * (QA[4] + s * (QA[5] + s * QA[6])))));
  return p / q;
}

export function erf(x: number): number {
  if (Number.isNaN(x)) return NaN;
  const ax = Math.abs(x);
  const sign = x < 0 ? -1 : 1;
  if (ax < 0.84375) {
    if (ax < Math.pow(2, -28)) return x + EFX * x;
    return x + x * smallRatio(x);
  }
  if (ax < 1.25) return sign * (ERX + midRatio(ax));
  if (ax >= 6) return sign;
  return sign * (1 - erfcTail(ax));
}

export function erfc(x: number): number {
  if (Number.isNaN(x)) return NaN;
  const ax = Math.abs(x);
  if (ax < 0.84375) {
    if (ax < Math.pow(2, -56)) return 1 - x;
    const y = smallRatio(x);
    if (x < 0.25) return 1 - (x + x * y);
    return 0.5 - (x - 0.5 + x * y);
  }
  if (ax < 1.25) {
    const ratio = midRatio(ax);
    return x >= 0 ? 1 - ERX - ratio : 1 + ERX + ratio;
  }
  if (ax < 28) {
    if (x < -6) return 2;
    const r = erfcTail(ax);
    return x > 0 ? r : 2 - r;
  }
  return x > 0 ? 0 : 2;
}

export function Phi(x: number): number {
  if (Number.isNaN(x)) return NaN;
  return 0.5 * erfc(-x / Math.SQRT2);
}

function trig(fn: (value: number) => number, a: number): number {
  return Number.isFinite(a) ? fn(a) : NaN;
}

const UNARY: Record<string, (a: number) => number> = {
  exp: (a) => Math.exp(a),
  log: (a) => Math.log(a),
  sqrt: (a) => Math.sqrt(a),
  abs: (a) => Math.abs(a),
  sin: (a) => trig(Math.sin, a),
  cos: (a) => trig(Math.cos, a),
  tan: (a) => trig(Math.tan, a),
  atan: (a) => Math.atan(a),
  erf,
  Phi,
  floor: (a) => (Number.isFinite(a) ? Math.floor(a) : a),
};

function extreme(values: number[], pick: (...values: number[]) => number): number {
  if (values.some((value) => Number.isNaN(value))) return NaN;
  return pick(...values);
}

/** The one integration rule (the Python twin's adaptive_simpson). */
export function adaptiveSimpson(fn: (t: number) => number, a: number, b: number): number {
  if (!(Number.isFinite(a) && Number.isFinite(b))) return NaN;
  if (a === b) return 0;
  const budget = { evals: 0 };
  const f = (t: number): number => {
    budget.evals += 1;
    return fn(t);
  };
  const nudge = (b - a) * SIMPSON_NUDGE;
  const m = (a + b) / 2;
  const fa = f(a + nudge);
  const fm = f(m);
  const fb = f(b - nudge);
  const whole = ((b - a) / 6) * (fa + 4 * fm + fb);
  return simpsonStep(f, a, b, fa, fm, fb, whole, SIMPSON_EPS, 0, budget);
}

function simpsonStep(
  f: (t: number) => number, a: number, b: number, fa: number, fm: number, fb: number,
  whole: number, eps: number, level: number, budget: { evals: number },
): number {
  const m = (a + b) / 2;
  const nudge = (m - a) * SIMPSON_NUDGE;
  const flm = f((a + m) / 2);
  const frm = f((m + b) / 2);
  const fml = f(m - nudge);
  const fmr = f(m + nudge);
  const left = ((m - a) / 6) * (fa + 4 * flm + fml);
  const right = ((b - m) / 6) * (fmr + 4 * frm + fb);
  const delta = left + right - whole;
  if (!Number.isFinite(delta)) return NaN;
  if (level >= SIMPSON_MAX_LEVEL || (level >= SIMPSON_MIN_LEVEL && Math.abs(delta) <= 15 * eps)) return left + right + delta / 15;
  if (budget.evals > MAX_INTEGRAND_EVALS) return NaN;
  return (
    simpsonStep(f, a, m, fa, flm, fml, left, eps / 2, level + 1, budget)
    + simpsonStep(f, m, b, fmr, frm, fb, right, eps / 2, level + 1, budget)
  );
}

/** fn(k) summed in order over the integers ceil(a) .. floor(b) (the Python twin's exact_sum). */
export function exactSum(fn: (k: number) => number, a: number, b: number): number {
  if (!(Number.isFinite(a) && Number.isFinite(b))) return NaN;
  const low = Math.ceil(a - 1e-9);
  const high = Math.floor(b + 1e-9);
  if (high < low) return 0;
  if (high - low + 1 > MAX_SUM_TERMS) return NaN;
  let total = 0;
  for (let k = low; k <= high; k += 1) total += fn(k);
  return total;
}

export type Env = Record<string, number>;

function truth(node: FigureNode, env: Env, defs: Definitions): boolean {
  if (node.kind === "and") return node.args.every((child) => truth(child, env, defs));
  if (node.kind === "or") return node.args.some((child) => truth(child, env, defs));
  const left = evaluate(node.args[0], env, defs);
  const right = evaluate(node.args[1], env, defs);
  if (Number.isNaN(left) || Number.isNaN(right)) return node.op === "!=";
  switch (node.op) {
    case "<": return left < right;
    case "<=": return left <= right;
    case ">": return left > right;
    case ">=": return left >= right;
    case "==": return left === right;
    default: return left !== right;
  }
}

/** The value of node with env (variables, parameters) and definitions; an unbound name is NaN. */
export function evaluate(node: FigureNode, env: Env, defs: Definitions = new Map()): number {
  switch (node.kind) {
    case "num":
      return node.value;
    case "name": {
      const name = node.text;
      if (Object.prototype.hasOwnProperty.call(env, name)) return env[name];
      const definition = defs.get(name);
      if (definition) return evaluate(definition, env, defs);
      if (Object.prototype.hasOwnProperty.call(CONSTANTS, name)) return CONSTANTS[name];
      return NaN;
    }
    case "neg":
      return -evaluate(node.args[0], env, defs);
    case "bin": {
      const a = evaluate(node.args[0], env, defs);
      const b = evaluate(node.args[1], env, defs);
      switch (node.op) {
        case "+": return a + b;
        case "-": return a - b;
        case "*": return a * b;
        case "/": return a / b;
        default: return Math.pow(a, b);
      }
    }
    case "call": {
      const values = node.args.map((child) => evaluate(child, env, defs));
      if (node.text === "min") return extreme(values, Math.min);
      if (node.text === "max") return extreme(values, Math.max);
      return UNARY[node.text](values[0]);
    }
    case "piecewise": {
      const args = node.args;
      for (let index = 0; index < args.length - 1; index += 2) {
        if (truth(args[index], env, defs)) return evaluate(args[index + 1], env, defs);
      }
      return evaluate(args[args.length - 1], env, defs);
    }
    case "integral":
    case "sum": {
      const [body, lower, upper] = node.args;
      const a = evaluate(lower, env, defs);
      const b = evaluate(upper, env, defs);
      const variable = node.text;
      const scope: Env = { ...env };
      const at = (t: number): number => {
        scope[variable] = t;
        return evaluate(body, scope, defs);
      };
      return node.kind === "integral" ? adaptiveSimpson(at, a, b) : exactSum(at, a, b);
    }
    default:
      throw new FigureGrammarError(`cannot evaluate a ${node.kind} node`);
  }
}
