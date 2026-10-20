# Reader workbench RW5a: explorable figures (stage `reader-rw5a`)

Branch `reader/rw5a` (worktree `learnanything-dl2`), base `main` at
`e14b4e4ff` (migration head 213; AD1, RW2b + H3, RW1c, RW4b and DL2 on main;
AD2+AD3 hold 214 and RW3b 215 in parallel). Spec:
`docs/specs/spec_reader_workbench_v1.md` §1's RW5a line and §8 in full (§8.1
what the learner sees, §8.2 the spec and the grammar, §8.3 verification, §8.4
predictions, §8.5 data, routes, spend and privacy, §8.6 switches), §11's two
tables, §12's `[figures]` keys and routes, §14 G21-G24, G45 and the RW5a test
lists. UX: `docs/specs/ux_reader_workbench_v1.md` §4.7, Moment 9, W11, §7.2-7.3
(values table, reduced motion), S9 (inline under the passage), D39 (play only).

## 0. Plan (written before the code)

### 0.1 What exists on `e14b4e4ff`

- No figure code. RW6a already reads `figure_predictions` (`reader_observations.prediction_observations`:
  `id`, `extraction_id`, `matched`, `created_at`), and its recap copy names "a figure prediction that turned
  out differently"; both read nothing until this migration.
- The intent catalogue (`reader/reader_intent.py`) says RW5a's action is absent until it lands (U13).
- `span_view.build_block_region` crops one block's PDF region (a pure read); the PDF pane's Ctrl+drag draws
  boxes in the block-bbox coordinate space.
- The PF-b sandbox (`content/authoring/pf_sandbox.py`: bubblewrap, no network, rlimits, fail closed) runs
  LLM-written sympy `check(reference, answer)` programs with negative controls (`run_equivalence_checks`).
- Paid calls: `practice_index/paid.py` (`plan_route`, `resolve_client`, `PaidCalls`) under a
  `SharedDailyEnvelope` (the workbench check's pattern). No structured transport takes an image today.
- Learner text: `reader_formative` is a source kind of learner-text gaps (RW1b), read from
  `reader_authored_questions` only.
- Exam protection: `content/sources/exam_material.exam_material(vault, repo)` (`covers`, `withheld`) and
  `held_out_refusal`.

### 0.2 What RW5a builds

1. **`learnloop.figures`** (new package, no evidence writer imports; an import-linter contract forbids every
   evidence/replay/serving package from importing it, as for the workbench):
   - `grammar.py`: the hand-written tokenizer, parser and evaluator (no `eval`, `exec` or `compile`):
     numbers, names, `+ - * / ^`, unary minus, `exp log sqrt abs sin cos tan atan erf Phi min max floor`,
     `piecewise((cond, expr)…, else)` with comparisons joined by `and`/`or`, `pi`, `e`,
     `integral(expr, var, a, b)` (one fixed adaptive Simpson rule) and `sum(expr, k, a, b)` (exact over
     integers). Caps: 2,000 characters, 400 nodes, depth 40 per expression; no integral or sum inside an
     integral or sum (after definitions are expanded); at most 10,001 sum terms; definitions may name only
     earlier definitions. `to_sympy` translates a parsed expression to sympy syntax (fixed code, for the
     verifier's sandboxed check).
   - `spec.py`: `InteractiveFigureSpecV1` (`spec_version "ifs-v1"`, strict, unknown fields refused) with the
     §8.2 fields and panels `function_plot` (series, markers, shade), `pmf_bars` (series, highlight),
     `linear_map_2d`, `readout` (with an optional `format`), invariants, predictions (`direction` or
     `area`, both decided by code) and annotations; at most 4 parameters (3^4 = 81 grid points).
     `evaluate_figure(spec, params)` produces the panels' data (the same shape the TypeScript renderer
     draws), the parity unit of the golden corpus.
   - `verify.py`: §8.3 steps 1-3. Structural (parse, names defined, finite on the parameter grid of
     {min, default, max}); invariants on the grid (`finite`, `bounded`, `nonnegative`, `integrates_to_one`
     within 1e-3 by the shared Simpson rule, `sums_to_one` within 1e-9, `monotone_nondecreasing`); every
     shaded area's readout against an independent Gauss-Legendre integration split at the piecewise
     breakpoints (within 1e-6); source match for `kind = reconstructed` only: the verifier's sympy
     `check(reference, answer)` run in the PF-b sandbox on (the quoted source equation as the verifier
     transcribed it, the spec's definition as `to_sympy` writes it), with two negative controls of our own
     (the definition scaled by 8/7 and halved) plus the sandbox's standard ones; any accepted negative, a
     sandbox that cannot run, or a quote that is not verbatim in the source downgrades the figure to
     `illustrative`. Steps 1 or 2 failing: `failed`, never shown.
   - `routes.py`: routes `figure_author` and `figure_verifier` (chat; unset is the active provider, Codex
     allowed by the owner's 2026-10-12 decision, `estimated_only`). Per request: at most two author attempts
     (the second sees the first's problems) and one verifier call. Every metered call is held to
     `figures.max_daily_cost_usd` (1.00) at `figures.price_per_million` through a `SharedDailyEnvelope`
     (refused before sending when unpriced or spent). `LEARNLOOP_FIGURE_MODELS=off` (set by the test suite)
     resolves no real client.
   - `service.py`: build (refuse exam/held-out material before any model call; reuse by `input_hash`; author;
     verify; store), revise ("not right?" → a new version with `supersedes_id` and `revision_note`, the
     earlier kept), list (the newest shown version per chain, current `spec_version` only, held-out sources
     dropped at read time), predict (code decides `matched` from the observed before/after readout) and
     explain ("what changed?").
2. **Image input.** `StructuredRequest.images` and the `image_input` capability (openai_chat / OpenRouter
   profiles that list `image` in `input_modalities`); `execute_structured_operation` refuses an image request
   to a transport that does not declare it, before any request. A region request needs an image-capable
   author route and is refused otherwise; a figure block sends its crop only when the route can read it.
3. **Migration 216** (`216_interactive_figures.sql`): `interactive_figures` (WORKFLOW) and
   `figure_predictions` (RAW_LEDGER, append-only by trigger except the one-time `explanation_text`), with
   `extraction_id` on predictions for RW6a's read. Classified in `db/table_roles.py`; head fixture
   `fixtures/migration_head_216` (git rename of 213's, 216 applied through the backup API, rollback mode)
   and every path naming the old one; references regenerated.
4. **Formative records.** A missed prediction is a `reader_formative` learner text (its answer and its
   "what changed?" text) through the existing adapter (`text_gaps.sources` / `provenance` / `jobs`, figure
   prediction ids prefixed `fpr_`), only while `learner_text_gaps.enabled` and `reader_formative.enabled`.
   Matched predictions write nothing there. No attempt, evidence, mastery, certification, scheduling, FSRS,
   AD or field write anywhere.
5. **Sidecar** (`learnloop_sidecar/handlers/figures.py`, desktop only): `reader.figure_request`,
   `reader.figure_revise`, `reader.figure_job`, `reader.figure_job_cancel`, `reader.figures`,
   `reader.figure_predict`, `reader.figure_explain`; builds run off the request path (RW4a's job runner);
   `reader.prompt_contract` gains `figures` only while on; the intent catalogue gains "make this
   explorable" (`figure` effect) only while on. Server events `figure_requested`, `figure_region_selected`,
   `figure_revision_requested`, `figure_predicted`; client events `figure_opened`, `figure_animated`.
6. **Frontend**: `screens/reader/figures/figureGrammar.ts` (the TypeScript twin, same rule and corpus),
   `FigureInline.tsx` (collapsed line with its verification label, one expanded at a time, sliders with
   numeric fields, function plots with shading, PMF bars, 2-D linear maps, readouts, play-only animation
   calling the same evaluator as the slider, step buttons under reduced motion, the values table on `t`,
   the prediction before the first change, "what changed? (optional)", what it demonstrates and assumes,
   "not right?"), `useFigures.ts`; narrow `ReaderScreen.tsx` edits (the intent effect, the slot under each
   passage, the region on the PDF selection).
7. **Config** `[figures]`: `enabled`, `predictions_enabled`, `region_enabled`, `revisions_enabled` (true),
   `max_daily_cost_usd` (1.00), `price_per_million` (unset); routes `ai.routing.figure_author` and
   `ai.routing.figure_verifier`. Every key classified in the parameter registry; defaults snapshots
   recomputed (no serving change, no successor).

### 0.3 What RW5a does not do

No RW5b panels or offers; no generated code anywhere; no CLI (the app is the only entry; nothing to dry-run);
no edits to `adaptive_difficulty/`, the scheduler, the plan, `PracticeScreen.tsx`, RW3b's or RW4d's files.

### 0.4 Tests planned

`tests/test_figure_grammar.py` and `figureGrammar.test.ts` on one golden corpus
(`apps/learnloop-tauri/src/screens/reader/figures/figureGoldenCorpus.json`: every construct, `integral`,
`sum`, shading, PMF bars, linear maps, the two-sided exponential and the ½ negative control, plus the
rejected inputs and a seeded fuzz); `tests/test_figure_verification.py` (invariants, source match with the
sandbox and with fakes, downgrade, refusal, unsupported, G23, G45); `tests/test_figure_region.py`;
`tests/test_figure_predictions.py` (G24, the formative adapter); `tests/test_figure_revisions.py`;
`tests/test_figures_rpc.py` (caps with fakes, held-out refusal before any call, reuse by `input_hash`,
switch-off pins, events); `tests/test_figures_migration.py` (table roles, triggers, durability);
`FigureInline.test.tsx`; the mobile allowlist, parameter registry, config, CLI and RPC pins.
