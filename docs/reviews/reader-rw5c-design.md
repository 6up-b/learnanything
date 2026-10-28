# Reader RW5c design: "matches the book's equation (checked)" (stage record)

- **Stage:** `reader-rw5c-design`. Design only: no `src/`, `tests/` or `apps/` change.
- **Branch:** `reader/rw5c-design` in `learnanything-ad1`, base `dbc1559e7` (migrations through 226, `mvp-0.37`).
- **Spec:** `docs/specs/spec_reader_rw5c_checked_labels_v1.md` (new), for owner review before any code.
- **Pointers added:** `spec_reader_workbench_v1.md` (§8.3 an "RW5c design" paragraph after the RW5a amendment, §8.5 routes note, G23 row, and an RW5c row in the §13 rollout table); `spec_reader_show_me_figures_v1.md` (N-a); `ux_reader_workbench_v1.md` (§4.7, "Labels follow verification"). Each pointer says the design is pending owner review and that the RW5a amendment governs until RW5c lands, so no existing statement is contradicted.
- **Live calls:** none. No model call, no paid command, no vault opened, no git command in the main checkout, no stash.

## What the design decides (recommended defaults; the owner may override)

- **Source equation:** read by code from the LaTeX of the figure's own input spans, through a closed construct table that translates into the figure grammar's `Node`s (spec §5). The author's quote is a pointer and a stated claim, never a check input.
- **Check:** code only. A fixed harness in the PF-b sandbox gets JSON ASTs (no text parsing in the sandbox) and runs sympy exact equality, piecewise by intervals, under sign assumptions taken from the slider ranges. It has structural negative controls, an interval-arithmetic proof of difference, and display agreement to the digits `formatValue` shows (spec §6). There is no `figure_verifier` route and no new cap, price or constant.
- **Labels:** element-scoped. Roles are `book`, `derived` (B only) and `ai`, found by a generic walk over the schema's `Label` and `Text` types. Delivered labels are rewritten by element id, with `shade.series` and `annotation.target` rebound (spec §7).
- **Owner choice pending (Q1):** A (code labels only on the checked element, plus a token rule) or B (strict: every label on a checked figure code-owned). The orchestrator recommends B (spec §8).
- **G23** becomes G23a–G23h (spec §9; G23i, every check is a verdict, was added by the Codex review, `reader-rw5c-design-codex-review.md`). The kill switch is `figures.checked_labels_enabled` (default on). Migration 227 adds `figure_source_checks`, an append-only RAW_LEDGER, with the no-migration alternative as Q6. There is no successor (spec §10).
- **Open questions:** Q1–Q18 in spec §17.

## Feasibility probes (offline)

These were run with the worktree's `.venv` Python (sympy 1.14.0) under `env -i HOME=<scratch>/home CODEX_HOME=<scratch>/codex LEARNLOOP_CONFIG_DIR=<scratch>/cfg PATH=/usr/bin:/bin`, with `python -I`. The scripts were in the session scratchpad. No vault, network or credential was touched.

1. **sympy's lark LaTeX parser** (`parse_latex(..., backend="lark")`):
   - `p \lambda e^{\lambda x}` gives `e**(lambda*x)*lambda*p`, with `e` as a free symbol;
   - `f(x) = p \lambda e^{\lambda x}` gives `Tree('_ambig', …)`;
   - each of these fails (`UnexpectedCharacters`): `\begin{cases}…\end{cases}`, `\frac{1}{\sqrt{2\pi}\sigma} e^{…}`, `\binom{n}{k} p^k (1-p)^{n-k}`, `\frac{\lambda^k e^{-\lambda}}{k!}`, `\frac{1}{\sigma \sqrt{2 \pi}} \exp\left(…\right)`, `\Phi(x)`, `\operatorname{erf}(x)` and `\mathrm{e}^{x}`;
   - each of these parses: `\frac{\lambda^{k} \cdot e^{-\lambda}}{k!}`, `\binom{n}{k} \cdot p^{k} \cdot (1-p)^{n-k}`, `\exp(x)` and `\sum_{k=0}^{n} \binom{n}{k}`;
   - `0.3 x` gives a `Float`.

   This is why spec §5.3 uses RW5c's own closed reader rather than lark.
2. **The exact check on the flagship density:** each branch's `simplify(book − figure) == 0` is True, and so is the breakpoint value. The three controls (`+1`, `×2`, `λ → λ + 1`) are each not equal. `sqrt(λ²) − λ` simplifies to 0 under `positive`. `Fraction(t) == Fraction(float(t))` holds for `0.5` and fails for `0.3`, `10000000000000001` and `1e-3`. An `mpmath.iv` proof that a value and its half are disjoint succeeds. Total: 0.1 s.

## Gate

- **Internal consistency.** I read the spec in full twice against the parent's §8.1–8.6, G23, the standing scope note, RW5d's SM2, N-a and Q4, and the RW5a review's §8.3–8.4. These contradictions were found and fixed before the final commit:
  - G45's ½ density is refused at step 2 by `integrates_to_one`, so it cannot reach step 3 as written. It is now the `differs` case only with that invariant removed (§9, §14).
  - The reserved-name rule contradicted the `\pi` row. `\pi` and `e` are now read only by their own rows (§5.3).
  - `checked` required display agreement for the whole definition, but agreement is per element. Now each element gets `book` only when its own agreement holds (§6.6).
  - The source of the `differs` "not shown" state was unclear. It now comes from the ledger row, and `verification` keeps steps 1–2's result (§6.6, §10.2).
  - The audit command was given as a `--recheck` run. It is now a listing without `--recheck` (§12).
  - `math_text.GREEK` was cited as the map for LaTeX commands. Commands canonicalize to their own name, and `GREEK` maps Unicode letters (§2, §5.3).
- **Citations.** I re-checked all 76 `file:line` citations in the new spec (38 distinct file:range citations, plus the continuation `:N` forms) in the worktree at `dbc1559e7`, or with `git show 865a3b38f:<path>` for the four deleted-step-3 citations. Corrected ranges: `verify.py:365-380`, `block_health.py:66-134` and `:137-146`, `symbolic.py:1-66` and `:1013-1058`, `protected_tables.py:320-331`, `config/schema.py:2590` (`max_daily_cost_usd`), `spec.py:50` (`SAMPLES`), `211_approach_maps.sql:58-68`. The pointer edits in the three existing specs add no code citation.
- **`git diff --check`:** clean.
- **Tests:** none run. It is a doc stage, and no code, test or fixture changed.

## Next

1. The owner reviews the spec and answers Q1 (A or B). The other Q2–Q18 defaults stand unless overridden.
2. Codex reviews the design adversarially ("find a displayed element or number these rules let carry the claim") before any code.
3. P1, in its own stage. Migration 227 if it is still free; renumber at landing.
