---
title: "Desktop module · src/screens/reader/figures/figureGrammar.ts"
type: "desktop-module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
module: "desktop.src.screens.reader.figures.figureGrammar"
language: "TypeScript"
area: "TypeScript/screens/reader/figures"
source_path: "apps/learnloop-tauri/src/screens/reader/figures/figureGrammar.ts"
source_paths:
  - "apps/learnloop-tauri/src/screens/reader/figures/figureGrammar.ts"
source_commit: "3092f6161aaa654ac0081fad52bf7ee52020ee2c"
source_commit_timestamp: "2026-10-21T00:06:21-04:00"
source_worktree_state: "clean"
activation_kind: "entry-reachable build graph"
activation_evidence: "A static TypeScript import path reaches this file from the Vite entry src/main.tsx."
generated: true
generated_at: "2026-08-18"
tags:
  - "learnloop/docs"
  - "learnloop/reference/module"
  - "learnloop/desktop"
  - "learnloop/desktop/typescript"
  - "refactor/active"
---

# `src/screens/reader/figures/figureGrammar.ts`

Area: [[Reference/Desktop/TypeScript/screens/reader/figures/_area|TypeScript/screens/reader/figures]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

Provides `MAX_EXPR_CHARS`, `MAX_NODES`, `MAX_DEPTH`, `MAX_EXPANDED_NODES` and related exports within the desktop's TypeScript/screens/reader/figures ownership area.

The system-level behavior stays authoritative in the linked architecture, concept, and workflow notes; this note owns only source-level lookup facts.

^desktop-module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [apps/learnloop-tauri/src/screens/reader/figures/figureGrammar.ts](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/figureGrammar.ts) |
| Source lines | 660 |
| Language | `TypeScript` |
| Area | [[Reference/Desktop/TypeScript/screens/reader/figures/_area|TypeScript/screens/reader/figures]] |
| Refactor status | `ACTIVE` |
| Activation kind | `entry-reachable build graph` |
| Worktree state | `clean` |
| Source commit | `3092f6161aaa654ac0081fad52bf7ee52020ee2c` |
| Commit timestamp | `2026-10-21T00:06:21-04:00` |

## Activation and status evidence

> [!success] ACTIVE
> A static TypeScript import path reaches this file from the Vite entry src/main.tsx.
>
> Build/entry chain: [[Reference/Desktop/TypeScript/main|src/main.tsx]] → [[Reference/Desktop/TypeScript/app/App|src/app/App.tsx]] → [[Reference/Desktop/TypeScript/screens/LessonScreen|src/screens/LessonScreen.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/FigureInline|src/screens/reader/figures/FigureInline.tsx]] → [[Reference/Desktop/TypeScript/screens/reader/figures/figureSpec|src/screens/reader/figures/figureSpec.ts]] → [[Reference/Desktop/TypeScript/screens/reader/figures/figureGrammar|src/screens/reader/figures/figureGrammar.ts]]

## Public API

- `export const MAX_EXPR_CHARS = 2000` — const, line 11
- `export const MAX_NODES = 400` — const, line 12
- `export const MAX_DEPTH = 40` — const, line 13
- `export const MAX_EXPANDED_NODES = 4000` — const, line 14
- `export const MAX_NAME_CHARS = 32` — const, line 15
- `export const MAX_SUM_TERMS = 10001` — const, line 16
- `export const MAX_SAFE_INTEGER = Number.MAX_SAFE_INTEGER` — const, line 21
- `export const SIMPSON_EPS = 1e-10` — const, line 22
- `export const SIMPSON_MIN_LEVEL = 3` — const, line 23
- `export const SIMPSON_MAX_LEVEL = 24` — const, line 24
- `export const SIMPSON_NUDGE = Math.pow(2, -40)` — const, line 25
- `export const MAX_INTEGRAND_EVALS = 200000` — const, line 26
- `export const FUNCTIONS: Record<string, [number, number]> =` — const, line 28
- `export const CONSTANTS: Record<string, number> =` — const, line 34
- `export const PROTOTYPE_NAMES = new Set<string>(["constructor", "hasOwnProperty", "isPrototypeOf", "propertyIsEnumerable", "toLocaleString", "toString", "valueOf"])` — const, line 39
- `export const RESERVED = new Set<string>([...Object.keys(FUNCTIONS), ...SPECIAL_FORMS, ...Object.keys(CONSTANTS), ...KEYWORDS, ...PROTOTYPE_NAMES])` — const, line 40
- `export class FigureGrammarError extends Error` — class, line 43
- `export type NodeKind = "num" | "name" | "neg" | "bin" | "call" | "piecewise" | "integral" | "sum" | "cmp" | "and" | "or"` — type, line 45
- `export interface FigureNode` — interface, line 47
- `export function isName(text: string): boolean` — function, line 61
- `export function parseExpression(source: string): FigureNode` — function, line 305
- `export type Definitions = Map<string, FigureNode>` — type, line 323
- `export function freeNames(node: FigureNode, bound: Set<string> = new Set()): Set<string>` — function, line 325
- `export const MAX_EXPANDED_DEPTH = 700` — const, line 345
- `export function nodeCount(node: FigureNode, definitions: Definitions): number` — function, line 364
- `export function expandedDepth(node: FigureNode, definitions: Definitions): number` — function, line 370
- `export function hasBoundForm(node: FigureNode, definitions: Definitions): boolean` — function, line 376
- `export function checkNames(node: FigureNode, known: Set<string>, definitions: Definitions): void` — function, line 381
- `export function erf(x: number): number` — function, line 454
- `export function erfc(x: number): number` — function, line 467
- `export function Phi(x: number): number` — function, line 488
- `export function adaptiveSimpson(fn: (t: number)` — function, line 517
- `export function exactSum(fn: (k: number)` — function, line 557
- `export type Env = Record<string, number>` — type, line 571
- `export function canonical(value: number): number` — function, line 590
- `export function newEnv(from?: Env): Env` — function, line 595
- `export function evaluate(node: FigureNode, env: Env, defs: Definitions = new Map()): number` — function, line 602

## Internal implementation anchors

- `const SPECIAL_FORMS = ["piecewise", "integral", "sum"]` — const, line 33
- `const KEYWORDS = ["and", "or"]` — const, line 35
- `const COMPARISONS = ["<=", ">=", "==", "!=", "<", ">"]` — const, line 41
- `type Token = [kind: "number" | "name" | "op", text: string]` — type, line 55
- `const TOKEN = /[ \t\r\n]*(?:((?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)|([A-Za-z][A-Za-z0-9]*)|(<=|>=|==|!=|[-+*/^(),<>]))/y` — const, line 57
- `const BLANK = /^[ \t\r\n]*$/` — const, line 58
- `const NAME = /^[A-Za-z][A-Za-z0-9]*$/` — const, line 59
- `function tokenize(source: string): Token[]` — function, line 65
- `const tokens: Token[] = []` — const, line 68
- `let position = 0` — let, line 69
- `const match = TOKEN.exec(source)` — const, line 73
- `function mk(kind: NodeKind, values: Partial<FigureNode> =` — function, line 88
- `class Parser` — class, line 92
- `const index = this.position + offset` — const, line 102
- `const token = this.peek()` — const, line 107
- `const token = this.take()` — const, line 114
- `const token = this.peek()` — const, line 119
- `const node = this.expression(0)` — const, line 132
- `let node = this.term(depth + 1)` — let, line 139
- `const op = this.take()[1]` — const, line 141
- `let node = this.unary(depth + 1)` — let, line 148
- `const op = this.take()[1]` — const, line 150
- `const base = this.primary(depth + 1)` — const, line 166
- `const value = parseFloat(text)` — const, line 178
- `const node = this.expression(depth + 1)` — const, line 184
- `const args = [this.expression(depth + 1)]` — const, line 205
- `const args: FigureNode[] = []` — const, line 218
- `let level = 0` — let, line 234
- `const parts = [this.conjunction(depth + 1)]` — const, line 248
- `const parts = [this.comparison(depth + 1)]` — const, line 257
- `const token = this.peek()` — const, line 266
- `const left = this.expression(depth + 1)` — const, line 271
- `const token = this.peek()` — const, line 272
- `const right = this.expression(depth + 1)` — const, line 275
- `const follow = this.peek()` — const, line 276
- `const body = this.expression(depth + 1)` — const, line 283
- `const lower = this.expression(depth + 1)` — const, line 288
- `const upper = this.expression(depth + 1)` — const, line 290
- `const literal = bound.kind === "neg" ? bound.args[0] : bound` — const, line 294
- `const stack: FigureNode[] = [node]` — const, line 315
- `const current = stack.pop() as FigureNode` — const, line 317
- `const found = new Set<string>()` — const, line 326
- `const stack: Array<[FigureNode, Set<string>]> = [[node, bound]]` — const, line 327
- `const stack: Array<[FigureNode, number, string[]]> = [[node, 1, []]]` — const, line 349
- `let count = 0` — let, line 350
- `let count = 0` — let, line 365
- `let deepest = 0` — let, line 371
- `const ERX = 8.45062911510467529297e-01` — const, line 407
- `const EFX = 1.28379167095512586316e-01` — const, line 408
- `const PP = [1.28379167095512558561e-01, -3.25042107247001499370e-01, -2.84817495755985104766e-02, -5.77027029648944159157e-03, -2.37630166566501626084e-05]` — const, line 409
- `const QQ = [0, 3.97917223959155352819e-01, 6.50222499887672944485e-02, 5.08130628187576562776e-03, 1.32494738004321644526e-04, -3.96022827877536812320e-06]` — const, line 410
- `const PA = [-2.36211856075265944077e-03, 4.14856118683748331666e-01, -3.72207876035701323847e-01, 3.18346619901161753674e-01, -1.10894694282396677476e-01, 3.54783043256182359371e-02, -2.16637559486879084300e-03]` — const, line 411
- `const QA = [0, 1.06420880400844228286e-01, 5.40397917702171048937e-01, 7.18286544141962662868e-02, 1.26171219808761642112e-01, 1.36370839120290507362e-02, 1.19844998467991074170e-02]` — const, line 412
- `const RA = [-9.86494403484714822705e-03, -6.93858572707181764372e-01, -1.05586262253232909814e+01, -6.23753324503260060396e+01, -1.62396669462573470355e+02, -1.84605092906711035994e+02, -8.12874355063065934246e+01, -9.81432934416914548592e+00]` — const, line 413
- `const SA = [0, 1.96512716674392571292e+01, 1.37657754143519042600e+02, 4.34565877475229228821e+02, 6.45387271733267880336e+02, 4.29008140027567833386e+02, 1.08635005541779435134e+02, 6.57024977031928170135e+00, -6.04244152148580987438e-02]` — const, line 414
- `const RB = [-9.86494292470009928597e-03, -7.99283237680523006574e-01, -1.77579549177547519889e+01, -1.60636384855821916062e+02, -6.37566443368389627722e+02, -1.02509513161107724954e+03, -4.83519191608651397019e+02]` — const, line 415
- `const SB = [0, 3.03380607434824582924e+01, 3.25792512996573918826e+02, 1.53672958608443695994e+03, 3.19985821950859553908e+03, 2.55305040643316442583e+03, 4.74528541206955367215e+02, -2.24409524465858183362e+01]` — const, line 416
- `const scratch = new DataView(new ArrayBuffer(8))` — const, line 418
- `function truncLow(value: number): number` — function, line 419
- `function erfcTail(ax: number): number` — function, line 425
- `const s = 1 / (ax * ax)` — const, line 426
- `let r: number` — let, line 427
- `let q: number` — let, line 428
- `const z = truncLow(ax)` — const, line 436
- `function smallRatio(x: number): number` — function, line 440
- `const z = x * x` — const, line 441
- `const r = PP[0] + z * (PP[1] + z * (PP[2] + z * (PP[3] + z * PP[4])))` — const, line 442
- `const s = 1 + z * (QQ[1] + z * (QQ[2] + z * (QQ[3] + z * (QQ[4] + z * QQ[5]))))` — const, line 443
- `function midRatio(ax: number): number` — function, line 447
- `const s = ax - 1` — const, line 448
- `const p = PA[0] + s * (PA[1] + s * (PA[2] + s * (PA[3] + s * (PA[4] + s * (PA[5] + s * PA[6])))))` — const, line 449
- `const q = 1 + s * (QA[1] + s * (QA[2] + s * (QA[3] + s * (QA[4] + s * (QA[5] + s * QA[6])))))` — const, line 450
- `const ax = Math.abs(x)` — const, line 456
- `const sign = x < 0 ? -1 : 1` — const, line 457
- `const ax = Math.abs(x)` — const, line 469
- `const y = smallRatio(x)` — const, line 472
- `const ratio = midRatio(ax)` — const, line 477
- `const r = erfcTail(ax)` — const, line 482
- `function trig(fn: (value: number)` — function, line 493
- `const UNARY: Record<string, (a: number)` — const, line 497
- `function extreme(values: number[], pick: (...values: number[])` — function, line 511
- `const budget =` — const, line 520
- `const f = (t: number): number` — const, line 521
- `const nudge = (b - a) * SIMPSON_NUDGE` — const, line 525
- `const m = (a + b) / 2` — const, line 526
- `const fa = f(a + nudge)` — const, line 527
- `const fm = f(m)` — const, line 528
- `const fb = f(b - nudge)` — const, line 529
- `const whole = ((b - a) / 6) * (fa + 4 * fm + fb)` — const, line 530
- `function simpsonStep( f: (t: number)` — function, line 534
- `const m = (a + b) / 2` — const, line 538
- `const nudge = (m - a) * SIMPSON_NUDGE` — const, line 539
- `const flm = f((a + m) / 2)` — const, line 540
- `const frm = f((m + b) / 2)` — const, line 541
- `const fml = f(m - nudge)` — const, line 542
- `const fmr = f(m + nudge)` — const, line 543
- `const left = ((m - a) / 6) * (fa + 4 * flm + fml)` — const, line 544
- `const right = ((b - m) / 6) * (fmr + 4 * frm + fb)` — const, line 545
- `const delta = left + right - whole` — const, line 546
- `const low = Math.ceil(a - 1e-9)` — const, line 559
- `const high = Math.floor(b + 1e-9)` — const, line 560
- `const count = high - low + 1` — const, line 563
- `let total = 0` — let, line 565
- `function truth(node: FigureNode, env: Env, defs: Definitions): boolean` — function, line 573
- `const left = evaluate(node.args[0], env, defs)` — const, line 576
- `const right = evaluate(node.args[1], env, defs)` — const, line 577
- `const env = Object.create(null) as Env` — const, line 596
- `function evaluateNode(node: FigureNode, env: Env, defs: Definitions): number` — function, line 606
- `const name = node.text` — const, line 611
- `const definition = defs.get(name)` — const, line 613
- `const a = evaluate(node.args[0], env, defs)` — const, line 621
- `const b = evaluate(node.args[1], env, defs)` — const, line 622
- `const values = node.args.map((child)` — const, line 632
- `const args = node.args` — const, line 638
- `const a = evaluate(lower, env, defs)` — const, line 647
- `const b = evaluate(upper, env, defs)` — const, line 648
- `const variable = node.text` — const, line 649
- `const scope: Env = newEnv(env)` — const, line 650
- `const at = (t: number): number` — const, line 651

## Who imports or calls it

> [!note] Static-evidence boundary
> “Calls” here means an import/module edge plus a source reference to the imported name. React render callbacks, props, Tauri string dispatch, macro expansion, browser/Cargo entry points, and data-driven routing can add runtime consumers that static text cannot prove.

- [[Reference/Desktop/TypeScript/screens/reader/figures/figureSpec|src/screens/reader/figures/figureSpec.ts]] — import-or-re-export: `CONSTANTS`, `Definitions`, `Env`, `FigureGrammarError`, `FigureNode`, `MAX_SAFE_INTEGER`, `MAX_SUM_TERMS`, `RESERVED`, `adaptiveSimpson`, `canonical`, `checkNames`, `evaluate`, `exactSum`, `expansion`, `isName`, `newEnv`, `parseExpression`, `walk`; references `CONSTANTS`, `Definitions`, `Env`, `FigureGrammarError`, `FigureNode`, `MAX_SAFE_INTEGER`, `MAX_SUM_TERMS`, `RESERVED`, `adaptiveSimpson`, `canonical`, `checkNames`, `evaluate`, `exactSum`, `expansion`, `isName`, `newEnv`, `parseExpression`, `walk`

## Dependencies

### Desktop source modules

No local TypeScript/TSX or Rust module dependency was detected.

### Assets, platform, and third-party dependencies

No explicit asset, standard-library, package, or crate dependency was detected.

## Larger desktop and workflow participation

- [[Architecture/Adapter Architecture#Request flow|adapter request flow]] — places this module on the UI/sidecar boundary.
- [[Workflows/Reader to Practice Workflow|Reader to Practice Workflow]] — owns the end-to-end reader sequence.
- [[Concepts/Reader Tutor and Teach-Back#Reader|Reader model]] — owns reader semantics.

The workflow note owns end-to-end sequencing; this module note describes only its local participation and edges.

## Tests that define behavior

- [apps/learnloop-tauri/src/screens/reader/figures/figureGrammar.test.ts](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/figureGrammar.test.ts) — vitest test: imports and executes this module under jsdom (`npm test`).
- [tests/test_figure_grammar.py](../../../../../../../../tests/test_figure_grammar.py) — cross-boundary name contract: references uniquely owned exported names `CONSTANTS`, `FUNCTIONS`; it does **not** directly execute this source module.
- [tests/test_figures_fix_round2.py](../../../../../../../../tests/test_figures_fix_round2.py) — cross-boundary name contract: references uniquely owned exported name `MAX_SAFE_INTEGER`; it does **not** directly execute this source module.
- [tests/test_figures_fix_round4.py](../../../../../../../../tests/test_figures_fix_round4.py) — direct source contract: references the exact source path.
- [tests/test_sketch_verify.py](../../../../../../../../tests/test_sketch_verify.py) — cross-boundary name contract: references uniquely owned exported name `MAX_SUM_TERMS`; it does **not** directly execute this source module.
- [tests/test_sidecar_reader.py](../../../../../../../../tests/test_sidecar_reader.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_sidecar_reader_pdf_view.py](../../../../../../../../tests/test_sidecar_reader_pdf_view.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_render_views.py](../../../../../../../../tests/test_reader_render_views.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.
- [tests/test_reader_requests.py](../../../../../../../../tests/test_reader_requests.py) — related cross-boundary behavior contract; it does **not** directly execute this source module.

## Modification guidance

- Change rendering, local interaction state, accessibility, or screen composition here; keep learning policy in the Python owning domain.
- When a request or response shape changes, update `src/api/dto.ts`, `src/api/client.ts`, the Rust command bridge, and the matching Python sidecar handler as one contract change.
- Run `npm run typecheck`, `npm test` and `npm run frontend:build` from `apps/learnloop-tauri`; for Rust changes also run `cargo test` from `apps/learnloop-tauri/src-tauri`.
- Update the canonical concept or workflow note when system semantics change; do not copy that explanation into this generated reference.

### Regeneration checklist

1. Modify [apps/learnloop-tauri/src/screens/reader/figures/figureGrammar.ts](../../../../../../../../apps/learnloop-tauri/src/screens/reader/figures/figureGrammar.ts) and focused tests.
2. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_generate.py`.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/desktop_validate.py`.
