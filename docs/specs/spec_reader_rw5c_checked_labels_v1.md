# Reader RW5c: "matches the book's equation (checked)", with code-owned, element-scoped labels (v1, design for owner review)

**Status:** design only, for owner review **before any code** (2026-10-27). It is the follow-up stage that `docs/reviews/reader-workbench-RW5a.md` §8.4 names, and it is linked from `spec_reader_workbench_v1.md` §8.3, G23 and §13. Until RW5c lands, the RW5a amendment in that §8.3 governs: every figure is an illustration and G23 holds vacuously. **One owner choice is pending** (§8: option A or option B; the orchestrator recommends B). Every other choice has a recommended default, and all of them are listed in §17. After the owner's review, Codex reviews this design adversarially ("find a displayed element or number that these rules let carry the claim") before any code is written.

**Base.** Code citations were checked in the worktree on branch `reader/rw5c-design` at `dbc1559e7` (migrations through 226, latest algorithm `mvp-0.37`). The deleted RW5a step-3 code is cited from commit `865a3b38f` (`git show 865a3b38f:<path>`). Python paths are relative to `src/`, frontend paths to `apps/learnloop-tauri/src/`, migrations to the repo root. Codex's adversarial review of this design (F1–F7) is folded in: `docs/reviews/reader-rw5c-design-codex-review.md`.

---

## 0. Summary

RW5a shipped every figure as an illustration. Its step 3 failed review five times in a row because it put one figure-wide claim on an open, model-written document and guarded it with lists of forbidden cases (class A). RW5c brings the claim back, changed in three ways:

1. **Code reads the book's equation itself.** It reads the equation from the LaTeX in the book's extracted text, through a closed table of constructs that each have an exact translation (§5). The model never writes the source equation, the check program or its translation. The figure author's quote can only *point* at an equation.
2. **The check is code only.** A fixed harness compares the figure's definition with the book's equation exactly, with sympy inside the PF-b bubblewrap sandbox. It runs negative controls and checks the displayed values against the equation to the digits shown (§6). There is no `figure_verifier` route and no model call. The only spend it can add is one retry by the figure author, inside the existing two-attempt cap and spend cap.
3. **The claim belongs to an element, not to the figure.** Only an element that draws the checked definition *by bare reference* can carry "matches the book's equation (checked)". Its label is the book's own left-hand side, quoted. Code assigns every other element a code-written voice (§7). The owner's open choice (§8) is how far code-owned labelling goes: **A**, code labels only the checked element; or **B**, strict, every label on a checked figure is code-written, so no model label sits next to the claim.

## 1. Why the first attempt failed, and what this design changes

| RW5a step 3 (rounds 1–5, deleted at the owner's decision of 2026-10-21) | RW5c |
|---|---|
| The verifier (a model, route `figure_verifier`) wrote the quoted source equation in sympy and wrote `check(reference, answer)` | Code reads the book's LaTeX through a closed construct table (§5.3). No model writes any part of the check |
| One figure-wide `verified` status, and a binding rule that listed which elements may name the source (round 2). Codex found a `highlight` labelled `f(k)` that the list missed (round-5 High 1) | Labels belong to elements. Each element has a code-assigned role (`book`, `derived`, `ai`), found by one walk over every `Label`-typed field of the schema. The walk is generic, not a list of element kinds (§7.1, G23d) |
| Literals: at most 1e6 and at most 9 significant digits by `Decimal` (round 4). Context rounding let forbidden literals through (round-5 High 2), and both numbers were made up | Literals: every literal in the checked definition must be exactly a binary64 value, decided with `Fraction(text) == Fraction(float(text))`. This needs no constant and no `Decimal` context (§6.1) |
| Display agreement within relative or absolute 1e-9, at 50 digits (round 4) | Display agreement **to the digits the figure shows** (`formatValue`), decided with interval arithmetic. The only tolerance is G22's existing parity bound between the two evaluators (§6.4) |
| A certification version inside `verification_report_json`, and a reuse-key miss (so a paid rebuild) when it changed (round-5 R5-4) | A certification version on an append-only check ledger (§10.2). Rechecks are code only and never call a model |
| "Checked" or "illustration" for the whole figure | Per element: *matches the book's equation (checked)*, *computed by LearnLoop from it*, or *AI-built, not checked* |

The class B fix from RW5a (one `FiguresGate` for every figure-derived model request, re-read before each request, `figure_admission.py`) stays, with one addition: the build's gate key gains RW5c's switch, so a switch change stops the `differs` retry and every later write (§6.7). RW5c adds no new kind of model request.

## 2. Code truth (checked at `dbc1559e7`)

| What | Where | What it means for RW5c |
|---|---|---|
| Steps 1–2 and their outcomes | `figures/verify.py:48-53` (`ILLUSTRATIVE`, `FAILED`, `UNSUPPORTED`; nothing produces `verified`); `:96` parameter grid; `:365-380` invariants, with `equals_source` skipped at `:370` | Step 3 goes after steps 1–2 and changes no part of them |
| Quote check | `figures/verify.py:391-401` (`quote_in`: verbatim after collapsing whitespace; `check_claims`) | Kept. A quote is still the author's pointer (§5.1) |
| The spec | `figures/spec.py:114-115` (`Text`, `Label` types), `:119` `SourceClaim`, `:135` `Parameter`, `:277-294` `Invariant` with `equals_source` naming a definition, `:313` `InteractiveFigureSpecV1`; `:652-654` (the compiler checks the `equals_source` name) | Unchanged: `ifs-v1` stays. The label walk keys on the `Label` and `Text` types (§7.1) |
| Grammar | `figures/grammar.py:105-117` (`Node`: a `num` keeps its source `text`), `:120` names `^[A-Za-z][A-Za-z0-9]*$`, `:48-55` caps | The book's equation is translated into this same grammar's `Node`s (§5.3). Grammar identifiers are ASCII, so comparing names is exact |
| Stored status | `db/stores/figures.py:32-43` (`VERIFIED_RW5C`, and `shown_verification` shows a stored `verified` as `illustrative`); `migrations/224_figure_requests.sql` (the current `interactive_figures`: `verification` CHECK includes `verified`, which needs `kind = 'reconstructed'`; `checks_json` is reserved for RW5d P2/P2b) | RW5c keeps both rules. Its result goes in a new ledger (§10.2), not in `verification` |
| The view | `figures/service.py:649-658` `shown_row`; `:664-704` closed `PROPERTY_CHECKS`; `:731` `figure_view`; `:821-846` `request_hash` (the prompt version is part of the reuse key) | The view gains a closed element map and a source-check block (§7.4). RW5c changes no prompt, so reuse keys do not change (§6.7) |
| Build admission, reuse and revisions | `figures/service.py:233-244` `build_key` (the gate's key: vault, `figures.enabled`, author route, cap, price, advanced panels); `:836-846` `request_hash` (it includes `supersedes_id` and `revision_note`; RW5d's show-me fields are added only when set, `:843-846`); `:850` `_reusable`; `:967-995` `_author_context` (`learner_note`, `problems_with_the_last_attempt`); `:1186-1226` the two-attempt loop; `:1267-1278` the store check, the row and its `figure_verified` judgment in one transaction; `:1319` `revision_request` ("not right?"); `migrations/224_figure_requests.sql:149-150` the unique reuse index (among shown rows) | The `differs` retry runs inside the loop (§6.6); the switch joins `build_key` (§6.7); *rebuild* is a revision with its own identity (§6.6) |
| Clipped and integer bounds | `figures/spec.py:825-845` `shade_value` (each bound clamped to the plot's x range), `:848-864` `highlight_value` (clamped to the k axis); `figures/grammar.py:618-639` `exact_sum` (integers `ceil(a − 1e-9)` to `floor(b + 1e-9)`); `:33-37` IEEE arithmetic (`1/0` is `Infinity`, `sqrt(-1)` is `NaN`) | Derived labels state the bounds the evaluator used (§7.2); domains come from the unsimplified expressions (§6.3) |
| Judgments | `db/stores/judgments.py:14-42` `append_judgment` (in the caller's transaction); `migrations/175_decider_judgments_and_receipt_labels.sql:36` (judge vocabulary, `verifier` among it), `:70-85` (supersession must name the same question) | Each check row has its judgment (§10.2) |
| The code-owned frame | `screens/reader/figures/FigureInline.tsx:28-46` (`FIGURE_FRAME`, `PROPERTY_CHECK_COPY`), `:49-54` `frameBadge` | RW5c adds constants to this frame (§7.3) |
| Label sites in the renderer | `screens/reader/figures/FigurePanels.tsx:22-31` `formatValue` (5 significant digits; exponent form outside [1e-3, 1e5); percent to 0.1); `:91` a shade finds its series **by label**; legends, SVG text, table headers and `aria-label`s at `:108-161`, `:183-203`, `:224-252` | Display agreement uses `formatValue`'s precision. Rewriting a label must keep `shade.series` and `annotation.target` bound (§7.4) |
| Precedent: symbolic checks of LaTeX | `workbench/symbolic.py:1-66` (RW2b: "checked" comes only from text parsed by code; names are never resolved; fixed harness in the PF-b sandbox; controls must behave), `:203-210` (sympy's lark LaTeX parser), `:1013-1058` `run_checks` (limits `cpu_seconds=20, wall_seconds=30` at `:1033`, `per_check_seconds` 5 at `:1039`) | Same principles. The reader is RW5c's own (§5.3, where the probe shows why it is not lark) |
| The sandbox | `content/authoring/pf_sandbox.py:80` `sandbox_available`, `:120` `run_sandboxed_python` (bubblewrap, no network, rlimits) | It runs RW5c's harness. Without bubblewrap nothing is checked |
| Block health | `content/sources/block_health.py:66-134` `analyze_block_health` (flags such as `equation_low_confidence`, `ocr_character_anomaly`; status `ok`, `suspect` or `failed`), `:137-146` `recommended_view`; computed on demand at `learnloop_sidecar/handlers/reader.py:666-681` | Gates which source blocks may be read (§5.2) |
| Greek names | `content/sources/math_text.py:34-36` (LaTeX commands canonicalize to their own name; `GREEK` gives Unicode letters the same names) | Maps a book symbol to its canonical name (§5.3) |
| Import contract and AD | `figures/__init__.py:21-23`; `pyproject.toml:672` (`evidence-never-reads-figures`); `adaptive_difficulty/protected_tables.py:105`, `:320-331`, `:509-511`, `:543`; `adaptive_difficulty/column_classes.py:294-300` | The new table needs the same classification (§10.2, §11.3) |
| The deleted step 3, as a starting point | `865a3b38f`: `figures/verify.py:475` `literal_problem`, `:533` `condition_problem`, `:693` `display_agreement`, `:795` `_names_source`; `figures/grammar.py:747` `to_sympy`, `:809` `sympy_problem` | Reused where §6 says so. The binding (`_names_source`, a label test) is **not** reused (§7) |

**Parser probe** (offline, `env -i` with an empty `HOME`, `.venv` Python with sympy 1.14.0; recorded in `docs/reviews/reader-rw5c-design.md`). sympy's lark LaTeX parser reads `e` as a free symbol, not Euler's number (`p \lambda e^{\lambda x}` → `e**(lambda*x)*lambda*p`). It returns `_ambig` for `f(x) = …`. It rejects `\begin{cases}`, `\Phi(x)`, `\operatorname{erf}(x)` and `\mathrm{e}^{x}`, and it fails on common spacing such as `\lambda^k e^{-\lambda}` and `\sigma \sqrt{2 \pi}`. Its *coverage* is therefore unknown until it is measured on the owner's books, and its *meaning* (`e`, ambiguity) would need patching. For both reasons §5.3 uses a closed reader of RW5c's own. A probe of the exact check (§6.3) on the flagship confirmed equality on both branches and at the breakpoint, rejection of all three controls, and an interval-arithmetic proof that the ½ density differs, all in about 0.1 s.

## 3. What "checked" certifies, and what it never certifies

**The standing scope note** (`spec_reader_workbench_v1.md` §8.3, owner-ruled 2026-10-21, binding here): "checked" certifies that the figure's **definition** equals the source equation, symbolically and exactly, and that the displayed, source-labelled content **is** that definition. It never certifies float values at points the check did not sample (rendering resolution, rounding at a reachable value off the sample). Such divergences are Low.

Made precise for RW5c, an element labelled *matches the book's equation (checked)* certifies all of the following:

1. **The equation is the book's, as the Reader shows it.** Code read it from the LaTeX of one source block of the figure's own input spans. That block is not withheld and its health status is `ok` (§5.2). The provenance names the extraction, the span and the page.
2. **The definition equals it, exactly, on the same domain.** sympy proves `definition − book_rhs = 0` for every real value of the plotted variable where they are defined, and for every parameter value under the sign assumptions implied by the sliders' ranges (§6.3). Proving it under weaker assumptions is a stronger statement, so it covers the whole range. Code also proves that the two are defined at the same points, read from the unsimplified expressions before anything cancels (§6.3 step 3), so `(x² − c²)/(x − c)` is never checked against `x + c`.
3. **What is drawn is that definition.** The element's expression is a bare reference to the definition: the same grammar `Node`, which the parity-tested evaluators compute (G22). Its literals are exact binary64 values and its branch conditions are exact (§6.1).
4. **What is shown matches it to the digits shown, on the parameter grid.** At every displayed sample of every grid point (§6.4), the value as displayed equals the exact value of the book's equation as displayed.
5. **The check worked.** Every negative control was refused (§6.5).

**It never certifies:**

- that the extraction read the printed page correctly. The claim is about the book's equation *as LearnLoop read it*. The ⓘ shows that reading next to a link to the page, and the health gate (§5.2) narrows this risk but cannot remove it;
- values between plotted samples, or at slider positions off the grid (rendering resolution and floating-point evaluation, Low by the scope note);
- any number computed *from* the checked definition (areas, sums, readouts of other expressions). Those are *computed by LearnLoop* (§7.2, role `derived`) and are cross-checked only by steps 1–2 (`verify.py:313` independent integration);
- that the figure teaches the right idea, that its ranges, predictions, "what it shows", assumptions or annotations are right, or that the passage means what the figure suggests. Those stay AI-written, in the model's voice;
- anything about the learner. "Checked" is a property of the figure's content. It is never evidence, mastery, certification or help weight (§11.2).

## 4. The pipeline: step 3, after steps 1–2

```text
author → spec → steps 1–2 (unchanged) → shown? ──no──→ failed (unchanged)
                                         │yes
                     figures.checked_labels_enabled? ──no──→ illustration (RW5a/RW5d exactly)
                                         │yes
 3a candidates: readable book equations in the figure's own input spans   (§5)
 3b binding:    which definitions are drawn by bare reference; names; literals; conditions   (§6.1)
 3c exact check in the sandbox, per (definition, candidate) pair; controls; display agreement   (§6.3–6.5)
 3d outcome per definition: checked | differs | undecided | not_checkable   (§6.6)
 3e element roles and labels from the outcomes   (§7, option A or B §8)
 3f one row in figure_source_checks and its judgment_ledger verdict, in one transaction   (§10.2)
```

Steps 3a–3f are deterministic functions of the stored spec, the source text, the block-health analyzer version, the reader version and the harness digest. So the same code rechecks a stored figure with no model call (§10.4).

## 5. Getting the book's equation (3a)

### 5.1 Where it comes from: the two options, and the recommended one

- **(i) Quoted source claims.** The author's `source_claims` quote (verbatim, `quote_in`) names the equation, and an `equals_source` invariant names the definition. Code reads only the quote. Coverage depends on the author quoting well, and a figure with no quote is never checked.
- **(ii) Extracted by code from the book's math, with provenance** (**recommended**). The candidates are every *readable* equation (§5.3) in the figure's own recorded input spans (`span_ids_json`, `input_span_ids_json` and RW5d's `input_span_keys_json`). These are the spans that were sent to the author and that are already rechecked for held-out material on every delivery (RW5a F1). Code tries every definition drawn by bare reference against every candidate (3c). The author's quote and `equals_source` become the author's **stated claim**: they put that candidate first, and they are the only way a figure can be found to *differ* from the book (§6.6). They are not required for a check.

Why (ii): a match is a true, exact equality with an equation the book states, whoever pointed at it. With (ii), coverage does not depend on the author's quoting, and the model's text can never widen what is certified. Trying several candidates cannot produce a false "checked", because each pair is checked exactly. When two candidates equal the same definition, the first in reading order is named, and its provenance says which it is.

A figure with grounding `none` (RW5d: "not from your books") has no candidates and is never checked. A `retrieved` figure's candidates are the passages it lists.

### 5.2 Which blocks may be read

A candidate block qualifies only when all of these hold:

- it is in the figure's input spans and is not withheld (`exam_material(...).withheld`, the same predicate as `service.check_request`, `figures/service.py:925`), at check time and on every delivery (unchanged RW5a F1 behaviour);
- its health, computed by the same `analyze_block_health` as `reader.block_health` (stored when it is computed, as that RPC does), has status `ok`. `suspect` (for example `equation_low_confidence`) and `failed` are `not_checkable`, with reason `block_health`. Health `unknown` is never treated as `ok` (`block_health.py`'s docstring, `spec_p3_reader_integration.md` §16), so code computes it at check time;
- its text holds the equation as LaTeX (`$…$`, `$$…$$`, `\[…\]`, or an `equation`/`math` block). Unicode math from a pdf.js text layer or pypdf (`𝜆`) is unreadable. `math_text.unicode_math_to_latex` is a lossy fallback and is never used to produce a candidate.

### 5.3 The book-math reader: a closed construct table

`figures/book_math.py` (new, pure, no I/O) parses one math segment into one relation and translates its right-hand side into the figure grammar's `Node`s. It is a hand-written tokenizer with an iterative parser, held to the grammar's caps (`MAX_EXPR_CHARS`, `MAX_NODES`, `MAX_DEPTH`, the expanded caps). It is not sympy's lark parser (§2 probe). It does not evaluate anything, so it runs in-process. Every construct outside the table makes the candidate `not_checkable`, with a closed reason key that the report counts (§12).

| Book LaTeX | Grammar | Rule |
|---|---|---|
| Integers and decimals (`2`, `0.5`) | `num`, with `text` kept | Read exactly as `Fraction(text)` (§6.1) |
| A Latin letter; a Greek command (`\lambda` → `lambda`: the command's own name, the canonical names `math_text` uses, `math_text.py:34-36`); one subscript letter or digit (`\mu_1`, `x_{0}` → `mu1`, `x0`) | `name` | Canonical name. Two book symbols that share one canonical name (`\epsilon`, `\varepsilon`) are unreadable (`name_collision`), and so is a symbol whose canonical name the grammar reserves for something else (a function name such as `Phi`, or `and`, `or`; `grammar.py:74-84`). `\pi` and `e` are read only as their own rows say |
| `+`, `-`, unary minus, `\cdot`, `\times`, juxtaposition | `bin` `+ - *`, `neg` | — |
| `\frac{a}{b}`, `a/b` | `bin /` | — |
| `a^{b}`, `a^b` with a one-token exponent | `bin ^` | — |
| `e^{u}`, `\mathrm{e}^{u}`, `\exp(u)`, `\exp\left(u\right)` | `call exp` | `e` is Euler's number **only** as the base of a power or as `\mathrm{e}`. A bare `e` anywhere else in the same equation makes it unreadable (`ambiguous_e`) |
| `\sqrt{u}` | `call sqrt` | An n-th root is unreadable (RW2b's rule, `symbolic.py`) |
| `\ln(u)` | `call log` | `\log` is unreadable in P1 (`log_base`: the base convention differs between books; Q12) |
| `\sin \cos \tan \arctan`, `\operatorname{erf}`, `\mathrm{erf}` | `sin cos tan atan erf` | — |
| `\lvert u\rvert`, `\left| u \right|`, `|u|` | `call abs` | — |
| `\min`, `\max` | `min`, `max` | — |
| `\pi` | `pi` | — |
| `( ) [ ] \{ \}`, `\left`/`\right`, `\, \; \! \quad` | grouping, or ignored | — |
| `\begin{cases} u & c \\ … \end{cases}` | `piecewise` | Each condition sets one symbol against a literal that is exactly binary64 (`x < 0`, `x \ge 0`, chained `0 \le x < 1`). The words allowed in the condition column are `\text{otherwise}`, `\text{if }`, `\text{for }`, and `,` and `.` at the end of a row. With no "otherwise" row, code requires the conditions to cover the real line, found by the interval method of §6.3; otherwise the equation is unreadable (`cases_cover`) |
| A symbol directly before `(` | product | Only when the same symbol also appears elsewhere in this equation without a `(` after it, or is an argument of the left-hand side. Otherwise unreadable (`application`), because code cannot tell `\lambda(1-p)` from a function applied to `1-p`. Names are never resolved (RW2b's rule) |

**Unreadable in P1** (each has its own reason key): `\Phi` (it could be the normal CDF or a symbol), `\binom`, `!`, `\Gamma`, `\int`, `\sum`, `\prod`, `\lim`, derivatives, matrices, indicator notation, sets, `\log`, other `\text{…}`, Unicode math, an inequality or `\approx`/`\propto` as the relation, more than one top-level `=`, a quote that spans two blocks, and a function applied to any name other than the table's functions. Additions come only as P2 rows, each with an exact translation and corpus cases (§13), in the order the report's reasons show (§12).

**The relation.** A segment must hold exactly one top-level `=` (or `:=`). The **left-hand side** is kept as the book's own LaTeX substring, bounded by `MAX_EXPR_CHARS`. It becomes the element's label (§7.2). When the left-hand side has the form `name(args)` or `name_{sub}(args)` with comma-separated symbol arguments, the arguments are recorded for the binding (§6.1). Any other left-hand side (`P(X = k)`, `E[X]`) is kept as a label with no arguments.

## 6. The exact check (3b–3d)

### 6.1 Binding prerequisites (code, in-process, before the sandbox)

For each definition `d` of the spec:

- **Drawn by bare reference.** `d` is a top-level definition, and some element's expression is exactly `Node(kind="name", text=d)`. That element is a `function_plot` or `pmf_bars` series whose axis variable is `d`'s only free variable that is not a parameter, a `readout` when `d` has no such variable, or a `heatmap_2d` expression in P2. A copy of `d`'s expression written inline is *not* a bare reference: it gets role `ai` (§7.2), which round 2's binding also ruled. A definition drawn by no bare reference is not checked.
- **Names are identical, with no renaming map.** The set of `d`'s free names after expansion (its parameters and its variable) equals the book right-hand side's set of canonical symbol names exactly. If the left-hand side has arguments, they equal `{the axis variable}`. A model-supplied renaming would let the author swap the roles of `p` and `λ` behind an exact match, so no renaming is accepted.
- **Literals are exact.** Every `num` in `d`'s expansion satisfies `Fraction(text) == Fraction(float(text))`, with no `Decimal` context. The renderer then evaluates exactly the literal that is checked. Book literals are read exactly as `Fraction(text)`. A figure literal `0.3` therefore never equals a book `0.3`, because the double 0.3 is not 3/10: the reason is `inexact_literal`, and the cost is a rare false negative (Q10). `pi` and `e` are constants, evaluated in floating point like any operation (the scope note), and display agreement covers them at the grid (§6.4).
- **Conditions are exact.** Every `piecewise` comparison in `d` sets a bare variable or parameter against an exactly binary64 literal, or against another bare variable or parameter. Comparing two doubles that were not computed is exact. This is round 5's R5-1b rule (`865a3b38f:figures/verify.py:533`), with one extension: name against name (Q11). A computed operand (`p*10 < 3`) is `not_checkable`.
- **No construct sympy cannot reproduce exactly.** No `integral` (the renderer's rule is Simpson), no `floor`, no `==` or `!=` (round 3's `sympy_problem` list, `865a3b38f:figures/grammar.py:809`), and in P1 no `sum`.

A definition that fails a prerequisite is `not_checkable`, with its reason (`not_bare`, `names`, `inexact_literal`, `inexact_condition` or `inexact_construct`), and the sandbox is not asked about it.

### 6.2 The harness and the sandbox

- **One fixed harness** (`figures/source_check.py`, a module constant like `symbolic.HARNESS`). Its sha256 is recorded on every check row. It runs through `pf_sandbox.run_sandboxed_python`: bubblewrap, no network, rlimits and a wall clock. sympy evaluates what it is given (`2^{10^{100}}`), so it never runs in-process.
- **The payload is ASTs, not text.** Code sends both sides, and every control, as JSON grammar `Node`s from a closed set of kinds. The harness builds sympy objects node by node through an exact table (`num` → `Rational(Fraction(text))`; `exp` → `sympy.exp`; `Phi` → `(1 + erf(x/√2))/2`; …), restored from `865a3b38f:figures/grammar.py:747` with the literal rule above. Nothing in the sandbox parses text.
- **Limits:** RW2b's existing bounds (`symbolic.py:1033`, `:1039`): 20 CPU seconds and 30 wall-clock seconds per run, 5 seconds per check. All pairs of one figure go in one run. A timeout means `undecided` for the pairs that did not finish. These are runtime bounds, not judgments (§15).
- **No bubblewrap** (macOS, Windows, or a Linux without `bwrap`): nothing is checked, and every figure stays an illustration with reason `sandbox_unavailable`. This fails closed, as RW2b does.

### 6.3 Deciding equality

For each pair (`d`, candidate):

1. **Symbols and assumptions.** The variable is `real`. A parameter is `positive` when its slider's `min > 0`, `nonnegative` when `min ≥ 0`, and `real` otherwise. These are sign assumptions only, so a proof under them holds across the slider range.
2. **Piecewise by intervals.** The breakpoints of both sides (all exact literals, §6.1) split the real line into open intervals and the breakpoints themselves. On each open interval, each side's branch is chosen by evaluating its conditions at an exact rational interior point; the conditions are constant there. The two branches must satisfy `simplify(a − b) == 0` as an identity, which is stronger than holding on the interval, and their domains must agree on the interval (step 3). At each breakpoint, both sides are substituted exactly and must both be defined with equal values, or both be undefined. A comparison against a parameter (name against name) makes the breakpoints depend on the parameters. P1 marks such pairs `undecided` (reason `parametric_breakpoint`), and P2 designs them (§13).
3. **Domains agree, read before anything simplifies** (Codex review F1). `simplify` cancels common factors, so a zero difference says nothing about where each side is defined: the source `(x² − 1/16384)/(x − 1/128)` and the figure's `x + 0.0078125` simplify to the same expression, yet the source has no value at `x = 1/128`, which is not one of the 121 samples. So, from each side's **unsimplified** grammar AST (after definition expansion, for the branch that holds on the interval), code collects its **definedness conditions**: `a / b` gives `b ≠ 0`; `sqrt(u)` gives `u ≥ 0`; `log(u)` gives `u > 0`; `tan(u)` gives `cos(u) ≠ 0`; `a ^ b` gives `a ≠ 0` when `b` is a negative integer literal, nothing when `b` is a non-negative integer literal, `a ≥ 0` when `b` is any other positive literal, and `a > 0` otherwise. These are the points where the expression has no real value; the evaluators' IEEE arithmetic gives no finite value there when the point is reachable, and steps 1–2 refuse a figure that reaches one on its grid (`grammar.py:33-37`). A condition that sympy proves true under the sign assumptions (`σ ≠ 0` for a `positive` σ, `x² + 1 > 0`) is dropped. The domains **agree** when the two sides' remaining conditions are the same set after canonical ordering, or when the conditions mention only the variable and the two **excluded sets** (the union of `solveset` of each negated condition over the interval) are proved equal. They **differ** when those excluded sets are proved unequal: an exact point of the symmetric difference (here `x = 1/128`) is a proof of difference, because one side has a value there and the other has none. Anything else (a remaining condition that depends on a parameter and differs between the sides, or a set that `solveset` cannot compare, such as a `ConditionSet`) makes the pair `undecided`, with reason `domain`. Parametric domains are designed in P2 (§13), with parametric breakpoints.
4. **Structural equality first.** Two `Node` trees that are identical after the same canonical ordering of `+` and `*` are equal without calling sympy (identical trees have identical domains).
5. **Proof of difference.** When the proof fails, the harness evaluates both sides with interval arithmetic (`mpmath.iv`) at exact rational points: the parameter grid of `verify.py:96`, with each double converted exactly, crossed with the variable's displayed samples. Precision grows until the intervals are disjoint, or until the time bound runs out. Two disjoint intervals **prove** that the definition differs from the equation, and so does a domain point from step 3.

The result of a pair is **equal** (proved, domains included), **different** (proved), or **undecided** (neither, within the bounds).

### 6.4 Display agreement (the "to the digits shown" check)

For each element that will carry `book` (§7.2), at every point of the parameter grid and every sample the renderer displays (a plot's 121 samples, a PMF's bars, a readout's value), the harness computes:

- the value the figure shows: the Python evaluator's double, formatted by a Python twin of `formatValue` (`FigurePanels.tsx:22-31`; the twin joins the G22 golden corpus, §14);
- the exact value of the book's equation at that sample: interval arithmetic until its interval formats to one string, within the time bound.

The two strings must be equal. At a sample outside the common domain (§6.3 step 3), the figure must show no value (`spec.py:803` `_num` gives `None` for a value that is not finite). The TypeScript renderer agrees with the Python evaluator only to G22's existing bound, 1e-9 relative. So a sample whose exact value lies within that bound of a display rounding boundary is *rounding decides*, and it fails closed. Any failure makes that element `ai`, not `book`, with reason `display_disagrees`. This is where catastrophic floating point (`(1 − cos x)/x²` near 0, `sin(10^15 π x)`) is caught. It also gives the scope note's phrase "points the check did not sample" its meaning: on the grid, what is shown is certified to the digits shown; off the grid it is not.

### 6.5 Negative controls

Code builds the controls from the definition, as exact `Node` transformations: `d + 1`, `2·d`, and `d` with each free symbol `s` replaced by `s + 1`. Each must come back **not equal**: different or undecided, never equal. Any control proved equal means the check is broken for this pair (a degenerate definition such as `0`, a symbol that cancels out, or a harness fault), and the pair is `undecided` with reason `control_accepted`. Following the PF item kept from RW5a (`pf_sandbox`: only a real boolean counts), an answer that is not one of the harness's three closed results is `undecided`. The controls are structural and tune nothing: any non-zero offset or scale other than 1 would serve, and these are the smallest.

### 6.6 Outcomes per definition, and what each does

**The stated claim, bound to concrete pairs** (Codex review F4). `ifs-v1` does not pair an `equals_source` invariant with a quote: invariants name definitions (`spec.py:294`), and `source_claims` is a separate list of `(span_id, quote)` (`spec.py:119-121`). So code binds them itself. A definition `d` **has a stated claim** when an `equals_source` invariant names it. Its **stated candidates** are the readable candidates (§5.3) whose segment any of the figure's quotes overlaps, for the quotes that `quote_in` verifies. Every other candidate is **unstated**. Each pair (`d`, candidate) has its own result from §6.3 (equal, different or undecided), or is not asked because a prerequisite failed.

**Precedence.** `d`'s outcome is the first row of this list that holds, in this order:

1. `checked`, through a stated candidate: some stated pair is equal and its controls are refused (§6.5). The first such candidate in reading order is named.
2. `differs`: `d` has a stated claim, no stated pair is equal, and **at least one stated pair is proved different**. This holds even when an unstated candidate is equal: the author's own claim about the book is false, and Q4 governs that, whatever else the definition happens to match. Example: one block holds `f(x)=x` and `g(x)=2x`, the author defines `d = 2*x`, names `d` in `equals_source` and quotes `f(x)=x`. `d` equals `g`, but the stated pair is proved different, so `d` is `differs` and the second attempt is told so.
3. `checked`, through an unstated candidate: some unstated pair is equal and its controls are refused. The first such candidate in reading order is named.
4. `undecided`: some pair was asked and none of the above holds.
5. `not_checkable`: no pair was asked (a prerequisite failed, §6.1; no readable candidate, §5.3; an unhealthy block, §5.2; or no sandbox).

| Outcome | What the learner sees |
|---|---|
| `checked` | Each bare-reference element whose display agreement holds (§6.4) gets role `book` (§7). One whose display disagrees stays `ai` |
| `differs` | Treated as a failed stated claim, as RW5d Q4 rules for sketches. At build, the check runs inside the two-attempt loop (`service.py:1186-1226`), after steps 1–2 pass, and a `differs` is one more problem for the second attempt ("your definition `f` differs from the quoted equation at x = −1, λ = 0.5, p = 0", or "… has a value at x = 1/128, where the quoted equation has none"), inside the existing cap of two attempts. If the second attempt also differs, the figure is **not shown**: *couldn't build a reliable version of this*, with the reason in the frame's words. The view takes this state from the ledger row (§10.2), and `verification` keeps steps 1–2's result. A recheck of a stored figure gives the same state, with *rebuild* (Q4, below). With the switch off, nothing reads the ledger, so the figure is RW5a's illustration (G23g) |
| `undecided` | `d`'s elements stay `ai`. If nothing on the figure is `book`, the badge is RW5a's illustration badge, with a closed reason in the ⓘ |
| `not_checkable` | As `undecided` |

**The figure's outcome** (the ledger row's `outcome`, §10.2) is, in order: `differs` if any definition differs; else `checked` if any definition is checked; else `undecided` if any is; else `not_checkable`. A figure has a checked element only when its outcome is `checked`, so a `differs` definition withholds every `book` role on the figure. RW5a's F3 (a second source equation is never left unchecked) is kept in element-scoped form: every definition is decided separately, and an element is `book` only for its own definition's check.

**Rebuild** (Codex review F3). The rejected figure's row stays `illustrative` with an unchanged `input_hash`, so pressing *rebuild* with the same request would return that same row from `_reusable` (`service.py:850`), and a second row with that hash would hit the unique reuse index (`224_figure_requests.sql:149-150`). *Rebuild* is therefore a **new version** through the existing revision path: `revision_request(repository, rejected_row, "")` (`service.py:1319`), so `supersedes_id` is the rejected figure's id and its `input_hash` differs (`request_hash` includes `supersedes_id`, `service.py:841`). The learner wrote no note, so `learner_note` is empty; the difference is code text and goes in as the first attempt's `problems_with_the_last_attempt` (`service.py:994`), built from the rejected figure's newest check row. That row's id joins the request's identity as `source_check_id`, added to `request_hash` only when set, as RW5d's show-me fields are (`service.py:843-846`), so every other hash is unchanged and a rebuild after a certification-version bump asks afresh. The rejected figure and its check rows are never changed. The rebuilt figure is checked at build like any other (two attempts). *Rebuild* is a revision, so `check_request`'s revision rules apply, and it is offered only while `figures.revisions_enabled` is on; when that switch is off, the failed state shows without the action.

**`kind`.** In P1 an element of a figure the author marked `illustrative` can also be `book`: an exact equality with the book is true, whatever the author called the figure. `kind = reconstructed` matters only because a reconstruction with a stated claim can *differ* (Q13).

### 6.7 Model routes, cost and admission

- **No model route.** RW5c does not re-add `figure_verifier`. A model fallback that "transcribes the book's equation" when code cannot read it would bring class A back: the check would then compare the figure with a model's text. An unreadable equation stays unreadable, and coverage grows by adding rows to the table (§13).
- **Cost.** The check makes no model call. Its only spend is the second author attempt after a proved `differs`, inside the existing per-request cap of two attempts and the `figures.max_daily_cost_usd` envelope, admitted by the existing `FiguresGate`. RW5c adds no cap and no price. CPU: one sandbox run per build or recheck.
- **Latency.** At build, the check runs inside the attempt loop, before the row is stored, because a `differs` must reach the second attempt (§6.6). It adds at most the sandbox's wall-clock bound (§6.2) to a build that is already a background job waiting on the author. A stored figure shows as an illustration while its recheck runs (§10.4), and the row upgrades it in place. Latency is measured in the report (§12).
- **Admission follows the switch** (Codex review F5). `build_key` (`service.py:233-244`) gains `figures.checked_labels_enabled`, as it holds `advanced_panels_enabled`, so `offer_build_key` inherits it. `FiguresGate` compares the key before every physical request, transport retries included, and at `gate.check("store")` (`service.py:1267`). So a switch change between the sandbox's result and the `differs` retry refuses that retry and every transport retry of it with `FiguresChanged`, and nothing is stored; the paid first answer keeps its checkpoint, as for any other switch change. The key is admission only: it is not part of `request_hash`, so reuse keys do not change (G23g). A recheck (§10.4) makes no model request, but it runs under a `FiguresGate` with the key `(vault, figures.enabled, figures.checked_labels_enabled)`, checked before the sandbox run and again just before the transaction that writes the check row and its judgment (§10.2). A unit that sees the switch off writes nothing. A row committed in the instant between that check and a switch-off is never shown while the switch is off, because the view reads the switch each time (§10.1).
- **No prompt change in P1.** The author prompt already asks a reconstruction to quote its equation and to name it in `equals_source` (`figures/routes.py:81-104`). Reuse keys (`service.py:821`) therefore stay the same, and figures already stored are rechecked by code (§10.4). Whether a prompt addition would raise coverage ("use the book's symbol names; draw the definition by bare reference") is decided after P1 from the report's reasons (P1b, §13). Such a prompt change takes a version suffix only while the switch is on, following RW5b's pattern, so hashes stay the same when it is off.

## 7. Code-owned, element-scoped labels (3e)

### 7.1 The elements

An **element** is anything the figure draws or names. It is found by one generic walk of `InteractiveFigureSpecV1`'s pydantic model: every field whose annotation is `Label` or `Text`, and every `Expr` beside them, at any depth, for every panel kind. The walk is not a list of kinds, so a new panel kind or field joins it by construction (G23d). In today's schema (`spec.py`), the elements are:

- drawn with a label: `function_plot.series[i]`, `.markers[j]`, `.shade[k]`; `pmf_bars.series[i]`, `.highlight`; `readout`; `linear_map_2d`; `heatmap_2d` (and its contours); `vector_field_2d` and its `heatmap`; `trajectory_2d`; `iterate_2d`; `parameters[i]` (the slider);
- free text outside the panels: `demonstrates`, `assumptions[i].text`, `annotations[i]` (`target` is a `Label`; `text`), `predictions[i].prompt`.

The same element ids name every place an element's label is drawn: legend, SVG text, values-table header, `aria-label`, readout line and slider label (`FigurePanels.tsx`, `FigureInline.tsx`).

### 7.2 Roles, and how code derives each label

| Role | Which elements | Label, derived by code | Voice |
|---|---|---|---|
| `book` | a bare reference to a `checked` definition (§6.1), with display agreement (§6.4) | the book's left-hand side, as the LaTeX substring of the source block (source text, never model text), rendered by KaTeX; then the frame's words *matches the book's equation (checked)*; ⓘ: the book's equation as LearnLoop read it, with the page, *open the page*, and what was checked (§3) | source (`§`) for the left-hand side, frame for the words |
| `derived` (**option B only**) | an element computed from a `book` element by a closed template: a shade under a `book` series; a highlight on a `book` PMF series; a readout `integral(d, v, a, b)` or `sum(d, k, a, b)` whose body is the bare reference `d` and whose variable is the book's variable | a code template over the **bounds the evaluator actually used**, never the author's bound expressions (Codex review F2): *area under* [LHS] *from* [lo] *to* [hi]; `\int_{lo}^{hi}` [LHS] `\,d`v; `\sum_{k=lo}^{hi}` [LHS]; then *computed by LearnLoop from it*. For a shade, lo and hi are `shade_value`'s clamped bounds (`spec.py:825-845`), which `evaluate_panel` already sends as the shade's `from` and `to`; when the clamp moved a bound, the frame adds *limited to the plotted range*. For a PMF highlight and for a `sum` readout, they are the integers the sum runs over: the highlight's bounds clamped to the k axis (`spec.py:848-864`), then `exact_sum`'s `ceil(a − 1e-9)` and `floor(b + 1e-9)` (`grammar.py:618-639`); a highlight whose clamp moved a bound also gets *limited to the plotted range*, and an empty range reads *no terms in this range*. For an `integral` readout, which is not clamped, they are its evaluated bounds, which the view sends beside the value. The numbers are formatted by `formatValue` and recomputed from the same evaluation at every slider change, so the label always names the operation whose value is shown | frame |
| `ai` | everything else | **A:** the model's label, behind the model glyph `◇`, unless the token rule replaces it (§8.1). **B:** code's own TeX rendering of the element's expression (§8.2) | model (`◇`) |

How code renders a parameter's slider, and the free text, is part of each option (§8).

**How an unverified element on the same figure stays an illustration.** Every element that is not `book` is drawn in the model's voice or the frame's, never the source's. On a figure with any `book` element, the collapsed line reads, all of it code-written with the left-hand side in source voice:

> ▸ interactive version · AI-built · `§ f(x)` matches the book's equation (checked) · the rest is an illustration

The final clause appears whenever any `ai` element is drawn. The badge slot (`frameBadge`) stays code-only. The open frame's *checked by LearnLoop:* line gains one closed entry, *the curve § f(x) equals the book's equation on p. 87, symbolically, for every x and every value the sliders reach*, beside the property checks that are already there.

### 7.3 The frame's new constants

`FIGURE_FRAME` gains `bookChecked` (*matches the book's equation (checked)*), `restIllustration` (*the rest is an illustration*), `derivedFrom` (*computed by LearnLoop from it*, B only), `limitedToPlot` (*limited to the plotted range*, B only), `noTerms` (*no terms in this range*, B only) and `aiElement` (*AI-built · not checked against the book*). A new closed table, `SOURCE_CHECK_COPY`, gives one phrase per reason key (*LearnLoop couldn't read the book's equation exactly: it uses Φ*; *the page this equation is on may be misread*; *checks need the sandbox, which this computer doesn't have*; …). An unknown key is dropped, as `PROPERTY_CHECK_COPY` drops one.

### 7.4 What the view sends, and the label rewrite

`figure_view` gains two blocks:

- `elements`: a list of `{id, path, role, tex, voice, definition?, source?: {extractionId, spanId, page}}`. `role` and `voice` are closed values. `tex` is either a substring of the verified source block (`book`) or code-rendered TeX (`derived`, and `ai` under B).
- `sourceCheck`: `{status: checked | none, certificationVersion, reasons: [closed keys]}`.

**The label rewrite, by construction.** Before the view is sent, every `Label` that code owns is replaced in the delivered `spec_json` by its element id: all of them under B, a subset under A. References between labels are rewritten with the same map (`shade.series`, `annotation.target`), so the renderer's binding by label (`FigurePanels.tsx:91`) still resolves. The renderer draws every label slot from `elements` by id. So a model string can reach a label slot only where the chosen option leaves one. The stored `spec_json` is never changed.

## 8. THE PENDING OWNER CHOICE: option A or option B

> **Question for the owner.** On a figure with a checked element, should code own **only the checked element's label** (A), or **every label and every number in a label slot** (B)? The orchestrator recommends **B**.

Both options share §§3–7: the same check, the same `book` role, the same collapsed line and the same frame constants. They differ in what happens to all the other labels on a figure that has a `book` element. A figure with no `book` element is drawn exactly as today under both options.

### 8.1 Option A: code labels only the checked element

- **`book` elements:** the book's left-hand side, as in §7.2. The model's label for that element is rewritten.
- **Every other element** keeps the model's label, drawn behind the model glyph `◇`. The legend carries the frame's note *◇ labels are AI-written*. There is no `derived` role: a shade under the book's curve keeps the model's label, for example the flagship's *◇ P(X ≤ 0)* (whose clipped-integral question, RW5a open question 8, stays open under A).
- **The token rule** (defence in depth). The walk of §7.1 tokenizes every model `Label` on a non-`book` element, through NFKC and the canonical token stream of `math_text` (LaTeX and Unicode to the same names). If the label *names the book's equation*, it is rewritten to code's TeX rendering of the element's own expression. A label names the equation when its first token is the left-hand side's head (`f` of `f(x)`, `fX` of `f_X(x)`) or when it contains the left-hand side's whole canonical token sequence. This is round 2's binding, applied by the generic walk instead of a list of element kinds, so the round-5 `highlight` case is covered.
- **Numbers:** every value is computed and formatted by code, as today. Model label text may still contain numbers (*◇ P(X ≤ 0) = 30%*), in the model's voice.
- **Slider labels:** the model's label behind `◇`. A parameter that is a symbol of a `checked` definition also shows the book's token in source voice: *§ λ · ◇ rate*.
- **Residual, by its nature:** the token rule is a deny-list over free text. A homoglyph (`ƒ`, U+0192, survives NFKC) or a paraphrase (*◇ the textbook's density*) escapes it. The mitigation is that such a label still appears in the model's voice, behind `◇`, on an element marked *AI-built · not checked against the book*. RW5a's final round ruled model text inside the code-owned frame Low. Under A, Codex's adversarial question ("find a label that impersonates the claim") has answers by construction, and each would be ruled under that Low.
- **Cost:** smaller: no `derived` templates and no rewrite of labels that do not name the book. It still needs the grammar-to-TeX renderer, because the token rule's replacement is code's TeX rendering of the element's expression. The figure keeps the model's pedagogical names (*P(X ≤ 0)*, *CDF*).

### 8.2 Option B (strict, recommended): every label on a checked figure is code-owned

- **`book` elements:** as in §7.2.
- **`derived` elements:** the closed templates of §7.2.
- **`ai` elements:** code's TeX rendering of the element's own expression. A reference to a definition that is not checked renders as its grammar name behind `◇` with the tag *AI-defined* (*◇ F(x) · AI-defined*), so it can never be read as the book's `F`. Grammar names are ASCII and come from a closed alphabet (`grammar.py:120`), so this needs no token rule. When a rendering is too long for its legend line, the legend shows *◇ curve 2* and the full rendering is in the values-table header. That is a layout fallback, not a threshold.
- **Slider labels:** the parameter's symbol. A symbol of a `checked` definition renders as the book's own token (`§ λ`, the token's LaTeX from the source block). Any other symbol renders as its grammar name rendered as a symbol, behind `◇`. The model's parameter `label` is not drawn.
- **Numbers:** every number in a label slot or inside the panels is formatted by code from a value that code computed or that the learner set (readouts, areas, slider fields, table cells, tick labels). The slider ranges are the author's *settings* and are shown as settings, never inside a label.
- **Free text** (`demonstrates`, assumptions, annotations, prediction prompts) stays where RW5a puts it: in the model's voice, **outside** the panels, labelled AI-written. It may contain numbers and symbols. Stripping them would be a deny-list, and RW5a's final round ruled this placement Low. An annotation's target renders as the target's code label (§7.4).
- **What it closes:** no model string reaches any label slot of a figure that carries the claim, so the question "find a displayed element that impersonates the claim" has no label answer by construction. Only the free-text blocks remain, outside the panels and in the model's voice. The flagship's readout becomes *∫ from −40 to 0 of § f(x) dx = 30.0% · computed by LearnLoop from it*, with the bounds the evaluator used (§7.2), which settles RW5a's open question 8 honestly.
- **Cost:** larger. It needs a grammar-to-TeX renderer (Python), the derived templates and the rewrite of every label. The figure also loses the model's names on a checked figure (its *P(X ≤ 0)* moves into *what it shows*, in the model's voice).

### 8.3 Side by side

| | A | B |
|---|---|---|
| A model label next to the checked element | yes, behind `◇` | never |
| Recurring-class risk (class A) | a deny-list remains (the token rule) | closed by construction for labels |
| The flagship's "P(X ≤ 0)" (a clipped integral) | the model's label, open question 8 stays | the code template states the clip |
| What the model's labels contribute on a checked figure | kept | moved into model-voice free text |
| Build size of P1 | M (the renderer, for the token rule only) | M–L (the renderer for every label, and the templates) |
| Tests that differ | the token-rule corpus (homoglyphs and paraphrases are documented residuals) | every label slot is drawn from `elements`, and no model string is in any slot (G23e) |

**Why the orchestrator recommends B:** RW5a lost five rounds to exactly the class that A keeps (a claim guarded by a list). The owner's own rules favour B: honest labels, and the proportionate bar (block on realistic learner-visible harm). A model label that impersonates the book next to a real "checked" is that kind of harm. B's cost is build effort and some lost model wording, not learner harm.

## 9. Gates: G23 made non-vacuous

`spec_reader_workbench_v1.md` G23 ("matches the source's equation" appears only after step 3 passed) becomes the following when RW5c lands:

| Gate | Statement |
|---|---|
| **G23a Only after the check.** | *matches the book's equation (checked)* appears only on an element of role `book`, and only when the switch is on and the newest `figure_source_checks` row for the figure carries the current certification version with outcome `checked` for that element's definition |
| **G23b Code reads the book.** | The equation comes from §5.3's table, applied to a healthy (§5.2), non-withheld block of the figure's own input spans. No model output is a check input: a fake author that returns a correct sympy string, a wrong quote or a "verified" field changes nothing |
| **G23c Exact or nothing.** | Equality is proved, on the same domain (§6.3). A stated claim proved different is `differs`, whatever else matches (§6.6). The controls are refused (§6.5). The literal and condition rules hold (§6.1). Display agreement holds (§6.4). The planted-wrong corpus (§14) is never `checked` |
| **G23d The walk is generic.** | A test enumerates every `Label`- and `Text`-typed field of `InteractiveFigureSpecV1` by type introspection and fails when the element walk misses one, so a new panel kind cannot bypass roles |
| **G23e Labels are code-owned.** | The badge slot, the frame lines and the roles are code constants or closed keys. Under B, no model `Label` string reaches any label slot of a checked figure (legend, SVG text, table header, `aria-label`, readout, slider). Under A, a model label is drawn only behind `◇` on a non-`book` element, and the token rule's corpus passes |
| **G23f Fails closed.** | No sandbox, a timeout, a broken control, an unreadable construct or an unhealthy block each give the RW5a illustration and a closed reason, never `checked` |
| **G23g Off is RW5a/RW5d exactly.** | With `figures.checked_labels_enabled` off: the views, the reader report, the CLI outputs and the reuse keys equal goldens recorded on an export of main (RW5a's R3-2 and R4-2 pattern). Nothing reads `figure_source_checks`. A switch change during a build or recheck stops it: no further author request (the `differs` retry and its transport retries included) and no check row or judgment (§6.7) |
| **G23h Never evidence.** | Nothing in attempts, evidence, hints, help outcomes, AD, scheduling or projection reads `figure_source_checks`, `sourceCheck` or the `figure_source_check` judgments (the import contract, plus a test over `protected_tables`) |
| **G23i Every check is a verdict.** | Each `figure_source_checks` row is committed in one transaction with its `judgment_ledger` row (task `figure_source_check`, judge `verifier`), at build and at recheck; a recheck's judgment supersedes the previous one for the same figure (§10.2) |

G21, G22 (extended with the `formatValue` twin), G24 and G45 stay. G45's ½ density is still refused at step 2 by its `integrates_to_one` invariant. With that invariant removed, so that steps 1–2 pass, it is RW5c's `differs` case (§14).

## 10. Switch, data, migration, successor

### 10.1 Kill switch

`figures.checked_labels_enabled` (boolean, default **true**: a live change behind a kill switch, per the owner's frictionless defaults; Q2). It sits in the existing `[figures]` section next to `predictions_enabled` and its siblings (`config/schema.py:2583-2591`). This is the key the stage brief calls "e.g. `reader.figures.checked_labels`", renamed to the section's convention. Off: steps 3a–3f do not run, no check row is written, and every view equals RW5a/RW5d's (G23g). Existing rows are kept but not read, so turning the switch back on shows them again if their certification version is current. The view reads the switch each time, so a row written just before a switch-off is never shown while the switch is off. Builds and rechecks are admitted against the switch as it is now, before every request and every write (§6.7). The key is classified in the parameter registry, and every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry it moves is recomputed (`config/template.py:842`; 28 entries at `dbc1559e7`, all of which a new default moves, as RW5d's `show_me_enabled` moved every entry then recorded), with a "no scoring, scheduling, projection or serving change" note.

### 10.2 Migration 227 (recommended): `figure_source_checks`

The number is 227 if it is still free when the stage is implemented. The runner is set-based, so renumber at landing if needed: CA3 and the cold-retry landing run in parallel.

| Column | Contents |
|---|---|
| `id` | TEXT primary key |
| `figure_id` | `interactive_figures(id)` |
| `certification_version` | INTEGER: the rules this check ran under (the reader's table, the harness, the display format); version 1 is RW5c P1 |
| `trigger` | `build` \| `recheck` |
| `outcome` | `checked` \| `differs` \| `undecided` \| `not_checkable` (figure level, §6.6) |
| `definitions_json` | per definition: outcome, reason key, the candidate's provenance (`extraction_id`, `span_id`, page, the LaTeX segment, the left-hand side, block health `{analyzer_version, status}`), the controls' answers, display agreement `{samples, agreed}` |
| `elements_json` | the element map of §7.4 (roles and code `tex`; no model text) |
| `harness_sha256`, `reader_version`, `sympy_version` | what produced it |
| `judgment_id` | the `judgment_ledger` row published with it (below) |
| `created_at` | — |

- **Role:** `RAW_LEDGER`, append-only: `_no_update` and `_no_delete` triggers, the pattern of `approach_maps` in `migrations/211_approach_maps.sql:58-68`. A recheck appends a row and never changes one. The shown state is the newest row at the current certification version. Classification: `db/table_roles.py`, `adaptive_difficulty/protected_tables.py` (PROTECTED and unread, with the reason "a code check of a figure's content; AD reads no figure") and `column_classes.py`. `interactive_figures` itself is unchanged.
- **Its judgment** (Codex review F6; implementation-handoffs §0 rule 6, parent §8.3). Every check row is a verifier verdict, so it is published with one `judgment_ledger` row through `append_judgment` (`db/stores/judgments.py:14`), **in the same transaction**: at build, the transaction that inserts the figure and its `figure_verified` judgment (`service.py:1267-1278`), after `gate.check("store")`; at recheck, one transaction holding just the check row and its judgment, after the recheck gate's last check (§6.7). Either both commit or neither does. The row:
  - `task` `figure_source_check` (beside steps 1–2's `figure_verified`, which is unchanged and keeps recording `illustrative`);
  - `left_kind` `interactive_figure`, `left_id` the figure's id, and no right side, so the question is one per figure;
  - `judge` `verifier` (code; in the existing vocabulary, `175_decider_judgments_and_receipt_labels.sql:36`), with no `judge_model` or `prompt_version`;
  - `verdict` the figure's outcome: `checked`, `differs`, `undecided` or `not_checkable` (§6.6);
  - `input_hash` the check's input digest: the sha256 of the canonical `spec_json`, the candidates' LaTeX segments with their `extraction_id`, `span_id` and block-health status, the certification version, `harness_sha256`, `reader_version` and `sympy_version`;
  - `rationale` code text only, within the existing 400 characters: per definition, its name, outcome and closed reason key, and for `differs` the witness point; never model text;
  - `supersedes_id`: none for the figure's first check; a later check (a recheck, a certification bump) supersedes the newest earlier `figure_source_check` judgment of the same figure, which the ledger's trigger requires to be the same question (`175_…sql:70-85`);
  - the check row records the judgment's id (column `judgment_id`), so either can be found from the other.

  Nothing outside `learnloop.figures` and the reader report reads task `figure_source_check` (G23h).
- **`interactive_figures.verification` stays as it is.** It records steps 1–2 (`illustrative` | `failed` | `unsupported`). RW5c never writes `verified`, so the value reserved in 216 and 224 stays unused (`VERIFIED_RW5C`'s comment is updated), and `shown_verification` keeps showing any legacy `verified` row from the RW5a development rounds as an illustration. One source of truth: the ledger.
- **Head fixture:** `migration_head_227`, with its README and the 5 hard-coded paths (CLAUDE.md), and both reference scripts rerun.
- **The alternative, with no migration** (Q6): write the result into `verification_report_json` and set `verification = 'verified'` in place on recheck (the judgment above is written either way). It is smaller, but a recheck mutates a WORKFLOW row (no figure row is updated anywhere today), the result and its history share one column, and the switch-off golden depends on in-place state. The recommendation is the ledger.

### 10.3 Successor

**None.** By `docs/algorithm-change-playbook.md` step 1, RW5c changes no scoring, scheduling, projection or admissibility meaning: figures are content and formative (parent §8.6). The check is a deterministic function of content and is not replayed on rebuild (a RAW_LEDGER table needs no replayer).

### 10.4 Stored figures

When a figure is opened with the switch on, and its tier is `grammar` with no check row at the current certification version, code queues a code-only recheck (a sidecar background job, the build worker's pattern, no model client), admitted against the switch before its sandbox run and before its write, and published with its judgment (§6.7, §10.2). The figure shows as an illustration until the row lands. `learnloop reader figure-checks --recheck [--dry-run] --json --vault <path>` does the same in bulk. With `--dry-run` it reports and writes nothing, and it is the n=1 coverage instrument (§12). A certification-version bump triggers rechecks the same way, at no paid cost.

## 11. Fit with the rest of LearnLoop

### 11.1 RW5d (show me, tiers, help)

- **Tiers.** Only `grammar`-tier figures are checked. Sketch, `js_animation` and `manim` figures keep RW5d's *not checked against the book* on every figure (RW5d SM2, N-a). Their declared claims are grammar expressions, so a later phase could check a claim's expression against the book. Even then, *the drawing itself is not checked* would stay, so the label would read *the curve is drawn from f, which matches the book's equation*. That is deferred and designed first (P3, §13; Q14).
- **Grounding.** `none` is never checked. For `retrieved`, the candidates are the listed passages (§5.1).
- **Progressive delivery and prebuilt figures (RW5d P2b, P5).** Each built figure is checked when it is stored, so a prebuilt figure arrives already checked. Nothing changes in the prefetch model, which reads only tier-1 engagement.
- **RW5d's per-element *checked by LearnLoop:* lines** (property checks) are a different claim, and their wording stays. RW5c adds one line of its own (§7.2).

### 11.2 Help is never certification

A checked figure is help exactly as an illustration is. Opened during an attempt, it counts as help (RW5d §11.4). Its *checked* changes no help weight, chooser feature, propensity or outcome, and makes no evidence. Nothing in `hints/`, `workbench/help_outcomes.py` or the evidence path reads `sourceCheck` (G23h). Whether "checked" should become a feature of the hint chooser is a later question, to be decided from the chooser's own logged outcomes, not now (Q15). The wording is always about the figure ("this curve matches the book's equation"), never about the learner.

### 11.3 AD and exam protection

- **Held-out material.** The candidates are a subset of the figure's input spans, which `exam_material` already refuses at request time and rechecks on every delivery (RW5a F1). A block that is held out later withholds the figure as it does today, and the check row is never delivered on its own.
- **Cold attempts.** No change: RW5d SM4 builds or shows nothing during a check on your own unless the learner takes it as help.
- **Blind grading.** No change: SM5, the grader never sees a figure.
- **AD.** The new table is PROTECTED and unread (§10.2). No AD operation reads figures (`protected_tables.py:509-511`, `:543`), and the import contract `evidence-never-reads-figures` (`pyproject.toml:672`) covers the new modules, which live in `learnloop.figures`.

### 11.4 Hosts

The desktop Reader is the only host in P1. The phone page and MCP show no figures in v1 (RW5d §6.7 and §10.5), so they are unchanged.

## 12. n=1 evaluation

Everything here is descriptive. Nothing applies a made-up threshold.

1. **Coverage on the owner's own books (before landing, code only).** `learnloop reader figure-checks --recheck --dry-run --json` runs on backup-API copies under `fixtures-local/`, with no model client and no writes. It reports how many stored grammar-tier figures would be `checked`, broken down by reason key (unreadable construct, health, names, literals, conditions, domains, display, controls, sandbox). This answers whether RW5c is vacuous on the owner's material, and which rows of the construct table to add next.
2. **The owner's audit of every checked element.** `learnloop reader figure-checks --json` without `--recheck` (and a `source_checks` sub-block of the reader report, only while the switch is on) lists each `checked` element: the book's equation as read (rendered), the page link, and the figure's definition (rendered). With n=1, the owner can read every one. A wrong "checked" is the incident this design exists to prevent. If one happens: switch off, write a reproducing test, and run a Codex review. If the class recurs, escalate to an Opus scope review as RW5a did, not to another fix round.
3. **The planted-wrong corpus** (tests, §14): every case must be not `checked`.
4. **Descriptive use:** opens and *not right?* notes for figures with a `book` element compared with figures that have none, and the check's latency (median and maximum). None of these feeds a decision rule.

## 13. Phases

| Phase | Builds | Needs | Size |
|---|---|---|---|
| **P0** (this document) | The design; the owner's review and the A/B choice; Codex's adversarial review of the design | — | — |
| **P1** | `book_math.py` (§5.3 table); the binding (§6.1); the harness, controls and display agreement in the sandbox (§6.2–6.5); outcomes and the `differs` retry (§6.6); roles and labels for `function_plot`/`pmf_bars` series and `readout`, plus B's `derived` templates if B is chosen (§7, §8); the frame constants; migration 227; recheck and the CLI (§10.4); the report block; the switch; the `formatValue` twin in G22 | RW5a, RW5b, RW5d P1 (all on main) | **M** (A) / **M–L** (B) |
| **P1b** (decided from the measurement) | An author-prompt addition, if the P1 report shows reasons the prompt could remove (`names`, `not_bare`). The owner decides after reading the report. There is no threshold | P1 report | **S** |
| **P2** | More constructs in the order the report's reasons show (`\binom` and `!` with `factorial`/`binomial` added to the grammar in both evaluators and corpora; `\log` per Q12; parametric breakpoints, §6.3); `heatmap_2d` with two-variable equations | P1 | **M** |
| **P3** (deferred, designed first) | RW5d tier claims against the book; matrices (`linear_map_2d` from `pmatrix`); vector fields | P2; RW5d P2/P2b | — |

## 14. Tests to write (P1)

All model calls are fakes (`LEARNLOOP_FIGURE_MODELS=off` already resolves no real client). Tests that need the real sandbox are skipped without bubblewrap, and a fake-sandbox twin tests the fail-closed path. Every test runs in the memory-capped scope.

- **`tests/test_rw5c_book_math.py`:** every row of §5.3 translates exactly, with a corpus of book-style LaTeX and the `Node` each should become; each unreadable construct gives its reason key; the `e` rule (`e^{x}` reads, a bare `e` refuses); the product rule (`\lambda(1-p)` with `\lambda` elsewhere reads; `g(1-p)` refuses); `cases` coverage with and without "otherwise"; chained conditions; non-dyadic condition literals refuse; caps and a seeded fuzz (bounded, never raises outside `GrammarError`); Unicode math refuses.
- **`tests/test_rw5c_source_check.py`:**
  - the flagship density (G45) is `checked`, with display agreement over its grid;
  - G45's ½ density, with its `integrates_to_one` invariant removed so that steps 1–2 pass, and with a stated claim, is `differs`, and the second attempt is told where (with the invariant it is still refused at step 2);
  - the controls: the definition `0`, and a symbol that cancels, give `control_accepted`;
  - each prerequisite fails on its own: a renamed parameter; an inline copy (role `ai`); `2*f` drawn under a label `f(x)` (role `ai`, rewritten under both options); round 5's highlight labelled `f(k)`; `sin(10000000000000001)` and `0.3` literals; round 5's 31-digit literal; `p*10 < 3`; `x < 0.5` (passes); name against name (P1: `undecided`);
  - `integral`, `floor` and `==` in the definition give `not_checkable`;
  - a block with status `suspect`, a withheld span, a block that is held out later (the figure withheld), and a quote across two blocks;
  - no bubblewrap, a timeout, and an inconclusive control (`None`, `0`, `""`) each give no `checked`;
  - `(1 − cos x)/x²` sampled near 0 gives `display_disagrees`;
  - two definitions with one `checked` and one `undecided` give per-element roles;
  - **domains (F1, planted-wrong corpus):** the source `\frac{x^2 - \frac{1}{16384}}{x - \frac{1}{128}}` against the figure's `x + 0.0078125` on `[0, 1]` (steps 1–2 pass, `1/128` is not a sample, `simplify` gives 0) is never `checked`, and with a stated claim it is `differs` with the witness `x = 1/128`; the reverse (the figure keeps the factor, the book has cancelled it) likewise; `sqrt(x)^2` against `x`; a parameter-dependent condition that differs between the sides gives `undecided` (`domain`); `σ` in a denominator with a `positive` slider passes;
  - **mixed candidates (F4):** one block with `f(x)=x` and `g(x)=2x`, the definition `d = 2*x` named in `equals_source` and the quote `f(x)=x`, gives `differs` (not `checked` through `g`) and the second attempt is told so; with the quote `g(x)=2x` it is `checked`, naming `g`; with no `equals_source` it is `checked` through the unstated `g`; the figure's outcome is `differs` whenever one definition differs, and then no element is `book`;
  - **admission (F5):** with a fake author and a fake sandbox, the switch turned off between the sandbox's `differs` and the second attempt refuses that attempt (`FiguresChanged`), no author request is sent, a fake transport's retry of it is refused too, and no figure, check row or judgment is stored; a recheck whose switch turns off before its write writes nothing;
  - `kind = illustrative` with an exact match gives `book`; grounding `none` is never checked; a sketch tier is never checked;
  - a fake author that returns sympy text, a "verified" field or a check program changes nothing (G23b).
- **`tests/test_rw5c_labels.py`:** G23d (the type-introspection walk covers every `Label`/`Text` field, and a synthetic new panel with a `Label` fails until it is mapped); the label rewrite keeps `shade.series` and `annotation.target` bound (evaluated in Python and through the TS compile in vitest); under B, the delivered spec of a checked figure holds no model `Label` string; under A, the token-rule corpus (the head token, the whole left-hand side, Unicode-to-LaTeX equivalents) holds, and the homoglyph and paraphrase residuals are recorded as documented passes behind `◇`.
- **`tests/test_rw5c_switch_off.py`:** G23g goldens (`figure_view`, `build_reader_report`, the CLIs, `request_hash`) recorded on an export of main; nothing reads the table while the switch is off.
- **`tests/test_rw5c_migration.py`:** append-only triggers, table roles, AD classification, and the head fixture (under `--durable-sqlite` too).
- **`tests/test_rw5c_judgments.py` (F6):** each check row commits with exactly one `figure_source_check` judgment, at build and at recheck (judge `verifier`, verdict the figure's outcome, `judgment_id` linking them); a failure injected between the two inserts leaves neither; a recheck's judgment supersedes the previous one for the same figure; the build's `figure_verified` judgment is unchanged.
- **`tests/test_rw5c_recheck.py`:** a stored reconstruction is rechecked with no model client; a certification bump rechecks; `differs` at recheck gives the failed state with *rebuild*; **pressing *rebuild* (F3)** calls the fake author (not a reuse of the rejected row), stores a new figure whose `supersedes_id` is the rejected one and whose `input_hash` differs, sends the difference as `problems_with_the_last_attempt` with an empty `learner_note`, can deliver the replacement as `checked`, and leaves the rejected row and its check rows unchanged; *rebuild* is not offered with `figures.revisions_enabled` off; `request_hash` is unchanged for every request without `source_check_id`; `--dry-run` writes nothing.
- **`tests/test_rw5c_never_evidence.py`:** G23h, over imports and `protected_tables`.
- **vitest** (`FigureInline.test.tsx`, `readerFigures.test.tsx`): the badge slot and frame lines are only code constants; every label site (legend, SVG text, table header, `aria-label`, readout, slider) reads from `elements`; a model label "matches the book's equation (checked)" in every model field never reaches a label slot (B) or appears only behind `◇` (A); the left-hand side renders through KaTeX in source voice; the ⓘ provenance; the collapsed line's *the rest is an illustration*.
- **Derived bounds (F2, under B):** a `book` curve `x + 0.25` plotted over `[0, 1]` with a shade requested from `−1` to `2` is labelled *area under f(x) from 0 to 1 · limited to the plotted range* with the value 0.75, never *from −1 to 2*; a slider that moves a bound updates the label; a highlight from 1.5 to 4.2 on a k axis 0..3 reads *from 2 to 3 · limited to the plotted range*; an empty highlight range reads *no terms in this range*; an `integral` readout shows its evaluated bounds.
- **G22 extension:** the `formatValue` twin's cases in the golden corpus, in both pytest and vitest.
- **`uv run lint-imports --no-cache`:** every contract kept, with the new modules inside `learnloop.figures`.

## 15. Every number

RW5c introduces **no new numeric threshold, weight or margin**. Every number it uses already exists:

| Number | Source |
|---|---|
| Sandbox limits: 20 CPU s, 30 wall-clock s, 5 s per check | RW2b, `workbench/symbolic.py:1033`, `:1039` (runtime bounds, not judgments) |
| Parameter grid: 3 points per parameter, at most 4 parameters | `verify.py:96`, `spec.py:51` |
| Displayed samples (121 per plot) and display precision (5 significant digits; exponent form; percent to 0.1) | `spec.py:50` (`SAMPLES`); `FigurePanels.tsx:22-31` |
| Python/TypeScript parity, 1e-9 relative | G22 (`spec_reader_workbench_v1.md`) |
| Grammar caps | `grammar.py:48-67`, `:391` |
| Two author attempts; `figures.max_daily_cost_usd` | RW5a (`config/schema.py:2590`) |
| The controls' `+1`, `×2` and `s + 1` | structural and exact (§6.5), tuning nothing |

The literal rule (exact binary64) and the display rule (to the digits shown) replace round 4's made-up `1e6`, 9 digits, `1e-9` and 50 digits (`865a3b38f:figures/verify.py:467-472`).

## 16. Risks and residuals

| Risk | Mitigation | Residual |
|---|---|---|
| The extraction misread the page, so the figure "matches" a misread | The health gate (§5.2); the ⓘ *as LearnLoop read it from p. N* with *open the page*; the owner's audit (§12) | A misread that health does not flag. The label is honest about whose reading it is |
| A sympy bug proves a false identity, or a cancellation hides a domain difference | Structural equality first; domain agreement from the unsimplified expressions (§6.3); controls; display agreement at the grid | A bug that also passes every control and every display sample: unlikely, recorded |
| Coverage turns out vacuous on real books | Measured before landing (§12 item 1); P2 grows the construct table from the reasons | It may take P2 before most of the owner's equations are readable |
| Under A, a model label impersonates the claim | The token rule; `◇` and *AI-built* on every non-`book` element | Homoglyphs and paraphrases (Low by RW5a's final ruling); none under B |
| A check makes the figure slower to appear | A stored figure shows as an illustration first and its recheck upgrades it in place; at build, the check is bounded by the sandbox's wall clock (§6.7) | At build, up to that bound added to a background build; measured (§12) |
| Platform | Without bubblewrap nothing is checked (§6.2) | macOS and Windows never show "checked" in P1 |

## 17. Open questions for the owner (each with a recommended default)

| # | Question | Recommended default |
|---|---|---|
| **Q1** | **Option A (code labels only on the checked element) or option B (strict: every label and every number in a label slot on a checked figure is code-owned)?** (§8) | **B** (orchestrator's recommendation) |
| Q2 | Default of `figures.checked_labels_enabled`? | **On** (a live change behind the kill switch) |
| Q3 | Where the book's equation comes from: (i) the author's quote only, or (ii) code reads every readable equation in the figure's own input spans, with the quote as a pointer and stated claim? (§5.1) | **(ii)** |
| Q4 | A stated claim proved to differ from its quoted equation, after the second attempt: not shown (as RW5d Q4 rules), or shown as an illustration labelled *differs from the book's equation it quotes*? (§6.6) | **Not shown** (*couldn't build a reliable version of this*); a stored figure becomes the same state, with *rebuild* (a new version through `supersedes_id`, §6.6, while `figures.revisions_enabled` is on) |
| Q5 | Which source blocks may be read: health `ok` only, or `suspect` too with a warning? (§5.2) | **`ok` only** |
| Q6 | Migration 227 `figure_source_checks` (append-only ledger), or no migration (in-place `verified` plus the report JSON)? (§10.2) | **Migration 227** |
| Q7 | Recheck stored figures by code on first open (and through the CLI)? (§10.4) | **Yes** |
| Q8 | Keep display agreement (to the digits shown, on the grid), or certify the definition only? (§6.4) | **Keep it** |
| Q9 | Under B, free model text (prediction prompts, annotations, "what it shows") keeps its numbers and symbols, in the model's voice outside the panels? (§8.2) | **Yes** (stripping would be a deny-list) |
| Q10 | Figure literals must be exact binary64, so a book's non-dyadic decimal (`0.3`) is never checked: accept that, or bring back round 4's magnitude/digit bounds (made-up constants)? (§6.1) | **Exact binary64** |
| Q11 | Allow a condition that compares two bare names (`x < theta`), an extension of round 5's rule? (§6.1; parametric breakpoints are `undecided` until P2) | **Yes**, decided in P2 |
| Q12 | `\log`: unreadable in P1, or read as the natural log? (§5.3) | **Unreadable in P1**; the report decides P2 |
| Q13 | Can an element of a figure the author marked `illustrative` be `book` when it matches exactly? (§6.6) | **Yes** |
| Q14 | RW5d tiers' claims against the book (the curve's function checked, the drawing not): design later? (§11.1) | **Yes, P3, designed first** |
| Q15 | Should "checked" become a hint-chooser feature? (§11.2) | **Not now**; only through the chooser's own logged outcomes later |
| Q16 | macOS and Windows (no bubblewrap) never show "checked" in P1: acceptable? (§6.2) | **Yes** (fails closed, as RW2b does) |
| Q17 | P1b's author-prompt addition: decided by the owner from the P1 report, rather than shipped with P1? (§6.7) | **Yes** |
| Q18 | Label wording: *matches the book's equation (checked)*, with the ⓘ *as LearnLoop read it from p. N*? Or put *as read* in the line itself? (§3) | **The short line, with the ⓘ** |

## 18. Agent prompt template (P1)

Fill in `<base branch>` and the owner's answer to Q1 (`<A or B>`). Give it to a fresh agent in the repo. The review and fix steps follow `implementation_goal.md` §2. P1b and P2 get their own prompt, written from the P1 report.

```text
Implement LearnLoop Reader RW5c P1 ("matches the book's equation (checked)"), as
specified in docs/specs/spec_reader_rw5c_checked_labels_v1.md (§13 row P1, plus every
section it cites), with option <A or B> of §8 (the owner's answer to Q1). Every other
open question takes its recommended default in §17 unless the owner's review says
otherwise; record each answer used in the review file.

Before coding, read: CLAUDE.md; docs/specs/implementation_handoffs.md §0 (standard rules
and invariants; rule 6: every verifier verdict appends to judgment_ledger);
spec_reader_rw5c_checked_labels_v1.md in full; spec_reader_workbench_v1.md §8.1-§8.6,
G21-G24 and G45; spec_reader_show_me_figures_v1.md SM2, N-a, Q4 and §11.4;
docs/reviews/reader-workbench-RW5a.md §8; docs/reviews/reader-rw5c-design-codex-review.md;
docs/specs/daily_loop_frictionless_defaults.md; db/table_roles.py;
docs/algorithm-change-playbook.md. Then write a short plan (files, migration, kill
switch, spend caps and model routes, judgment_ledger writes, tests) to
docs/reviews/reader-rw5c-p1.md and proceed.

Work in your own worktree on a new branch reader/rw5c-p1, created from <base branch>.
Follow §0 of the handoffs and the spec, especially these resolved contracts:
- the book's equation comes only from §5.3's closed reader over healthy (§5.2),
  non-withheld blocks of the figure's own input spans; no model output is a check input;
- equality is §6.3's, including domain agreement from the unsimplified ASTs (F1);
  §6.4's display agreement; §6.5's controls; nothing in the sandbox parses text;
- outcomes follow §6.6's precedence: a stated claim proved different is `differs` even
  when an unstated candidate is equal (F4); the figure's outcome is `differs` if any
  definition differs; at build the check runs inside the two-attempt loop;
- *rebuild* is a revision (`revision_request`, `supersedes_id`, `source_check_id` in
  request_hash only when set), never a reuse of the rejected row (F3);
- derived labels (option B) state the bounds the evaluator used: the shade's clamp,
  the highlight's clamp and exact_sum's integers (§7.2, F2);
- `figures.checked_labels_enabled` joins build_key; rechecks run under their own
  FiguresGate; nothing is requested or written after a switch change (§6.7, F5);
- every figure_source_checks row commits with its judgment_ledger row (task
  figure_source_check, judge verifier) in one transaction, and a recheck's judgment
  supersedes the previous one (§10.2, F6);
- labels: the generic schema walk (§7.1, G23d) and the label rewrite by element id
  (§7.4); under B no model Label reaches a label slot of a checked figure (G23e);
- migration 227 (or the next free number) for figure_source_checks, RAW_LEDGER,
  append-only, classified in db/table_roles.py, protected_tables.py and
  column_classes.py; head fixture and reference scripts per CLAUDE.md;
- no new model route, cap, price or constant (§6.7, §15); no algorithm successor
  (§10.3); recompute every DEFAULTS_SNAPSHOT_BY_ALGORITHM entry the new key moves, with
  a "no scoring, scheduling, projection or serving change" note;
- "checked" is never evidence, mastery, certification or help weight (§11.2, G23h);
- with the switch off, views, report, CLIs and reuse keys equal goldens from main (G23g);
- no live or paid AI calls in tests (fakes only); sandbox tests skip without bubblewrap
  and have a fake-sandbox twin; the coverage run (§12 item 1) is code only, on
  learnloop.db.copies backups under fixtures-local/, never on the tracked vaults;
- if the spec contradicts the code, record it in the review file, take the
  conservative option (no `checked`, switch off) if work can continue, else stop.

Done means: G23a-G23i and G22's extension pass; the §14 tests exist and pass;
uv run lint-imports --no-cache, uv run pytest -n auto and uv run pytest -m durability
pass; npm run typecheck && npm test pass; the DB reference scripts pass. The review file
lists what was built, deviations, test results with pass counts, files touched, the
migration, the §12 coverage report (by reason key), owner-run commands (dry-run first)
and open questions. Commit with clear messages; do not merge or push.
```
