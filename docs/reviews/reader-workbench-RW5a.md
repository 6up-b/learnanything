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

## 1. What was built

### 1.1 The grammar and its two evaluators (`learnloop.figures.grammar`, `figureGrammar.ts`)

- A hand-written tokenizer (ASCII only: a Unicode digit or a no-break space is outside the grammar),
  recursive-descent parser and tree-walking evaluator, line for line in Python and TypeScript. The
  grammar is §8.2's: numbers, names, `+ - * / ^` (right-associative power), unary minus, the thirteen
  functions (`Phi` is the standard normal CDF, `min`/`max` take 2-8 arguments), `piecewise((cond,
  expr)…, else)` with `< <= > >= == !=` joined by `and`/`or` (chained comparisons refused), `pi`, `e`,
  `integral(expr, var, a, b)` and `sum(expr, k, a, b)`. Caps: 2,000 characters, 400 nodes, depth 40,
  4,000 nodes once definitions are expanded, 10,001 sum terms, 200,000 integrand evaluations; no
  integral or sum inside an integral or sum (definitions count). An unbound name is NaN.
- Arithmetic is IEEE doubles as JavaScript computes them (the Python twin emulates `1/0`, `log(0)`,
  `0^-1`, `1^NaN`, `NaN` in `min`/`max`, …). `erf`/`erfc` in TypeScript are Sun's fdlibm (checked to
  2e-16 / 2e-15 of the C library over 25,000 points); Python calls `math.erf`/`math.erfc`; `Phi` is
  `erfc(-x/√2)/2` in both (no cancellation in the left tail).
- **The integration rule** (deviation, see §2): adaptive Simpson with Richardson's correction,
  tolerance 1e-10 halving per level, levels 3 to 24, with **one-sided endpoint values**: every
  interval reads its endpoints 2^-40 of its width inside itself, so a `piecewise` jump at an endpoint
  or a bisection point is integrated from the correct side. Without it the flagship's
  `integral(f, x, -40, 0)` read `f(0)` from the right branch and missed `p` by up to 4e-5.
- `to_sympy` translates a parsed expression (definitions expanded, decimals as exact `Rational`s) for
  the verifier's sandboxed check.

### 1.2 The spec (`learnloop.figures.spec`, `figureSpec.ts`)

`InteractiveFigureSpecV1` (pydantic, unknown keys refused): §8.2's fields with `function_plot`
(series, markers, `shade` under a named series between two bound expressions), `pmf_bars` (series over
whole-number `k`, at most 200 bars, `highlight`), `linear_map_2d` (2×2 matrix of expressions, the unit
square's image and the determinant), `readout` (`format` number | percent); invariants `finite`,
`bounded`, `nonnegative`, `integrates_to_one`, `sums_to_one`, `monotone_nondecreasing` (each over
`var` from..to) and `equals_source` (names the definition that is the book's equation); predictions
`{prompt, change, observe: {kind: direction | area, expr}}`; annotations. At most 4 parameters (the
3^4 = 81 grid). The compiler resolves every name (definitions may name only earlier ones; panel
expressions only the parameters and the panel's variable). `evaluate_figure` / `evaluateFigure` give
every panel's data at a parameter set (121 samples per plot, the shaded areas' and highlights' values),
and `prediction_outcome` decides a prediction by code: direction = rises / falls / same (1e-6
relative) of the observed expression before and after the change; area = the one shaded area whose
value equals the observed one.

### 1.3 Verification (`learnloop.figures.verify`)

Step 1 (every shown value finite at every grid point), step 2 (each invariant at every grid point;
`integrates_to_one` within 1e-3 by the shared Simpson rule, `sums_to_one` within 1e-9; every shaded
area's readout within 1e-6 of an independent 10-point Gauss-Legendre integration on 200 panels per
piece, split at the series' piecewise breakpoints), step 3 for `kind = reconstructed` only: the
claims' quotes must be verbatim (whitespace collapsed) in the span they name; the verifier (one call)
returns the quoted equation in sympy and `check(reference, answer)`; the PF-b sandbox
(`run_equivalence_checks`, bubblewrap, never in-process) runs it on the spec's definition and on our
two negative controls (×8/7 and ÷2) plus the sandbox's standard ones (`degenerate`). Verified only
when the definition is accepted and every control refused. Anything that keeps step 3 from running
(no quote, no `equals_source`, the verifier unrouted/capped/failing, a transcription of a quote the
spec never claimed, no sandbox) is a reason: the figure is `illustrative` with its label, never
verified. Steps 1-2 failing: `failed`, stored, never shown. Undecidable predictions are dropped
(listed in the report), not failed. One `judgment_ledger` row per build (task `figure_verified`,
judge `verifier`, verdict the outcome).

### 1.4 Routes, caps and spend (`learnloop.figures.routes`)

`figure_author` and `figure_verifier` are `AITask`s with `ai.routing.*` keys (unset: the active
provider; Codex allowed, `estimated_only`). Per request at most **two author attempts** (the second is
told the first's problems) and **one verifier call**, each one physical request (`max_retries = 0`).
A metered route is held to `figures.max_daily_cost_usd` (1.00) at `figures.price_per_million` by a
`SharedDailyEnvelope` named `figures.max_daily_cost_usd` (the transactional reservation ledger every
paid role shares); unpriced is refused before sending, a spent envelope is `capped`.
`LEARNLOOP_FIGURE_MODELS=off` (set in `tests/conftest.py`) resolves no real client. The author's
prompt carries a per-request id, so "try again" after a failure asks afresh instead of recovering the
failed answer from its receipt. The figure author is in `ai.disclosures.JUDGE_ROUTES` (Settings): it
receives a learner's "not right?" note.

**Image input** (new, small): `StructuredRequest.images` and the `image_input` capability;
`execute_structured_operation` refuses images to a transport that does not declare it, before any
request; `openai_chat` / OpenRouter declare it when the profile lists `image` in `input_modalities`
and send `image_url` parts; `PaidCalls.call(images=…)` passes them through (the prompt names the
image's digest, so a checkpoint never answers another image).

### 1.5 The service (`learnloop.figures.service`)

`check_request` (the switches, then exam and held-out material refused through
`exam_material(vault, repo)`'s `covers`/`withheld` on the selection, the region's block and, for a
revision, the base figure: before any job or call) → `build_figure`: the source context (the selected
blocks, two blocks each side unless held out), the crop (`build_block_region`, a region's box clipped
to its figure block, or the figure block's crop when the route reads images; a region with a
text-only route is refused `no_image_input`), `input_hash` (spec, prompt and verifier versions, the
request, the passage and context text, the image digest, the revision note), reuse of the newest
shown or unsupported row with that hash (a failed row is never reused), the author attempts, the
verification, one row and its ledger verdict in one transaction. `list_figures` shows per version
chain the newest shown version (else the newest failed or unsupported one), current spec version
only, never one whose passage is held out now. `record_prediction` (code decides `matched`;
idempotent per figure and prediction) and `record_explanation` (once).

### 1.6 Data: migration 216, table roles, head fixture

`migrations/216_interactive_figures.sql`: `interactive_figures` (WORKFLOW; §8.5's columns, CHECKs on
origin, verification, kind and that a verified figure is a reconstruction with a spec; three indexes)
and `figure_predictions` (RAW_LEDGER; plus `extraction_id` for RW6a's read; unique per figure and
prediction; the no-delete trigger and the explanation-once trigger). Classified in
`db/table_roles.py`; no DERIVED table, so no replayer. `fixtures/migration_head_213` →
`fixtures/migration_head_216` (git rename; backup-API copy, only 216 applied under
`UPGRADE_SCRATCH_COPY`, `wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE`, header bytes
1/1, `integrity_check` ok, `foreign_key_check` empty, no companion files; README paragraph); every
path naming it (33 files: 31 tests, both reference scripts with `SCHEMA_HEAD = 216`,
`docs/decider-tier1-migration.md`); the head pins at 216; AD1's, H1's, H0's and RW4a's "nothing else
changed" diffs subtract `RW5A_ADDED_OBJECTS` (`tests/test_figures_migration.py`), and AD1's
`_upgrade` now expects 213 first (216 follows on the way to head).

### 1.7 Formative records (W1 tier 2)

A missed prediction is a `reader_formative` learner text through the existing adapter: figure
prediction ids are prefixed `fpr_`; `text_gaps.sources.formative_row` / `reader_formative_text`,
`provenance.formative_record` and `missed_formative_ids` (the backlog sweep) dispatch on the prefix
(by SQL; `learnloop.diagnosis` never imports the figure package). The text is the learner's answer in
words and, when written, "What changed, in my words: …"; the context is the prediction's question,
the figure's own passage and what the figure showed (computed by code, labelled as not the book's
words). `jobs.enqueue_figure_prediction` queues it on RW1b's rule (`learner_text_gaps.enabled` and
`reader_formative.enabled`), at the prediction; a "what changed?" written while that job is still
queued is read with it, and one written after its reading started is its own later text
(`<prediction id>:explained`, `jobs.enqueue_figure_explanation`; Codex review F5,
docs/reviews/reader-rw5a-codex-review.md). A matched
prediction queues nothing. RW6a's `prediction_observations` now finds missed predictions (its read
was already written for this table).

### 1.8 Sidecar (`learnloop_sidecar/handlers/figures.py`), events, contract, intent

Seven desktop-only RPCs (`FIGURE_RPCS`, pinned in `tests/test_mobile_allowlist.py`; Tauri
passthroughs in `commands.rs`/`main.rs`; `api/client.ts`): `reader.figure_request`,
`reader.figure_revise` (each refused at once or answering with a job on RW4a's `LibraryJobs` runner,
`ctx.figure_jobs`, delivery re-checking held-out material), `reader.figure_job`,
`reader.figure_job_cancel`, `reader.figures`, `reader.figure_predict`, `reader.figure_explain`.
`reader.prompt_contract` gains `figures: {predictions, region, revisions}` only while on. The intent
catalogue gains `make_explorable` ("make this explorable", Understand, effect `{kind: "figure"}`) only
while on (`Availability.figures`). Events: server-owned `figure_requested`,
`figure_region_selected`, `figure_revision_requested`, `figure_predicted`, `figure_explained`
(`reader_inquiry.RW5A_SERVER_EVENTS`; ids and status only, never the learner's words), client
`figure_opened` and `figure_animated` (`CLIENT_ACTION_EVENTS`; `figure_id` and `parameter` added to
the kept activity fields); all salience-only. The reader report gains a `figures` block (built by
verification, unsupported requests by kind, revisions, regions, predictions, missed, "what changed").

### 1.9 The Reader (frontend)

- `screens/reader/figures/useFigures.ts`: loads `reader.figures` for the open source, runs builds as
  paced jobs (1.5 s) with cancel and try again, keeps the one expanded figure, lands a new version in
  place of the one it supersedes (a "not right?" version that did not verify leaves the earlier one
  and says why). Inert with no `figures` in the contract.
- `FigureInline.tsx`: the pending line (*◐ building an interactive version — keep reading* · cancel),
  the failed line (its reason · try again), the unsupported line (*can't draw this yet — needs … ·
  noted*), and the collapsed line *▸ interactive version · {label}* that expands in place, one at a
  time. Open: what it shows (◇, AI-written) and what it assumes (quoted § where verified), the
  prediction before the first change (sliders locked until answered or skipped; "A prediction is for
  you: it is never graded"), the readout before → after (*30.0% → 30.0%*) and "what changed?
  (optional)" with its "where this goes", sliders with numeric fields, `▶ play` on an `animate`
  parameter (40 steps through the same `evaluateFigure`; nothing moves until pressed; `◂ step` /
  `step ▸` under `prefers-reduced-motion`), the values table (`t`, or the button), annotations,
  "not right?" with its "where this goes".
- `FigurePanels.tsx`: SVG function plots (series by line style as well as colour, shaded areas by wash
  and hatch, markers), PMF bars (the highlighted range filled), the unit square and its image, readouts;
  a data table per panel.
- `ReaderScreen.tsx` (narrow): the `figure` intent effect (selection spans, or the PDF region), the
  slot under each passage in the text view, and on the PDF the pane's new `inlineNotes` slots and
  `regionSelection`. `usePdfSelection`: with `regionAt` (only while `figures.region_enabled`), one
  Ctrl+drag box whose centre lies in a Figure/Picture block is a region of it (the selection carries
  `region: {spanId, page, bbox}`); otherwise today's word marquee, unchanged.

### 1.10 Config

`[figures]` (`FiguresConfig`): `enabled`, `predictions_enabled`, `region_enabled`,
`revisions_enabled` (true), `max_daily_cost_usd` (1.00), `price_per_million` (unset); routes
`ai.routing.figure_author`, `ai.routing.figure_verifier`. Every `figures.*` key is classified in
`params/parameter_registry.py` (structural / operational). The 20 `DEFAULTS_SNAPSHOT_BY_ALGORITHM`
entries were recomputed (template `.pyc` cleared; 0 mismatches) with the usual note (no serving
change, no successor). `db_generate_reference.py` gained the section's description and places the two
tables in the reader family with their own purpose lines.

## 2. Deviations (each with its reason)

1. **One-sided endpoint values in the Simpson rule** (§1.1). The spec says "the same fixed adaptive
   Simpson rule (same depth and tolerance)"; it still is one rule, identical in both evaluators, but a
   plain Simpson rule cannot meet G45's 1e-6 when a density jumps at an endpoint. Max level 24 (not a
   lower number) so a jump strictly inside an interval converges to about 1e-6 of the jump.
2. **At most 4 parameters**, so §8.3's grid is exactly {min, default, max}^n ≤ 81.
3. **Predictions are `direction` or `area`, decided by code** (no free-word answers): the learner
   answers "in a word, a choice or a click on an area" — the choices are the words. No model judges a
   prediction.
4. **`figure_predictions.extraction_id`** beyond §8.5's columns: RW6a's recap already reads it.
5. **`interactive_figures.kind`** is the spec's kind as written; a downgraded reconstruction is
   `kind = reconstructed`, `verification = illustrative`.
6. **The ◇▸ margin mark** of a built figure is not drawn (the collapsed line carries the figure under
   its passage instead); RW3a's margin gutter allows one LearnLoop mark per screenful, and a second
   kind of mark there needs its own density rule. Open question 3.
7. **"about N s"** is never shown: the reader report does not yet measure figure builds (W14 says
   only once measured).
8. **On the original-page (PDF) view** the figure is drawn as an overlay just below its passage's box
   (the pane's inline-note mechanism, now a list), covering the page below it while expanded; the
   extracted-text view reflows it inline. The PDF page cannot reflow.
9. **Codex reads no images here**: the Codex SDK transport does not declare `image_input` (it runs
   with `view_image` off), so a region needs an OpenRouter/OpenAI-compatible profile with `image` in
   `input_modalities` on `ai.routing.figure_author`; a region with a text-only route is refused before
   any call. A figure block selected with a text-only route is sent as its text (caption and
   neighbours).
10. **No CLI.** The app is the only entry; there is nothing batch-like to dry-run.

## 3. Tests

New: `tests/test_figure_grammar.py` (152: the corpus, coverage of every construct and panel kind,
rejected inputs, the fuzz, the G21 AST lint, G45, the jump rule, the caps, `to_sympy`),
`tests/test_figure_verification.py` (18: invariants, structure, independent shading, quotes, the
sandboxed source match with its negative controls (real bubblewrap), never in-process, G23 labels,
downgrades, the half-density control never shown, the second attempt, unsupported, undecidable
predictions, no answer sent early), `tests/test_figures_rpc.py` (17: contract and intent with the
switch, switch-off refusals with no call, held-out refusal before any call, held out later is not
shown, context privacy, reuse by `input_hash`, failed not reused, the two caps, unpriced and capped
metered spend, the capped verifier downgrades, no learning-state writes, salience events, client
events, cancel, validation), `tests/test_figure_region.py` (9: only the crop is sent, clipping, no
crop no call, no image route refused before any call, figure-block crop only with image input, the
switch, the transport refusal, `image_url` parts), `tests/test_figure_predictions.py` (10: G24 table
diff, the formative queue, matched queues nothing, the switches, once and validated, "what changed?"
read with it, the append-only triggers, the backlog sweep, RW6a, the report),
`tests/test_figure_revisions.py` (6), `tests/test_figures_migration.py` (6, one `durability`),
`tests/test_figures_switch_off.py` (2: the golden recorded on an export of `e14b4e4ff`),
`FigureInline.test.tsx` (13), `readerFigures.test.tsx` (2), `figureGrammar.test.ts` (147, the same
corpus). Changed pins: the intent catalogue (`test_reader_intentions.py`, `test_reader_intent.py`'s
base-contract parity turns figures off), RW1c's switch-off golden (pops RW5a's key and action, as the
RW4b landing did), `test_judge_routes.py` (the figure author's disclosure), the mobile allowlist,
`test_architecture.py` (the store's SQL), the head-fixture files, the TS intent fixture, RW4a's
switch-off snapshot helper (strips RW5a's action), the attention lint (covers the figure components).

## 4. Owner-run commands

None needed. To try it on a backup copy (never the tracked vaults): set `ai.routing.figure_author` to
an image-capable profile if you want regions (OpenRouter vision model with
`input_modalities = ["text", "image"]`), select an equation in the Reader → *make this explorable*.
Switch off with `[figures] enabled = false` (or the sub-switches).

## 5. Open questions (with the defaults in force)

1. **Grid size.** Default: at most 4 parameters (81 grid points). Allow more with a sampled grid?
2. **Image route.** Default: the active provider (often Codex, text only); regions need an
   image-capable `figure_author`. Recommend an OpenRouter vision profile for `figure_author`?
3. **The ◇▸ margin mark** (deviation 6). Default: none; the collapsed line is the mark.
4. **One prediction per figure.** Default: the first only; later ones in the spec are not asked.
5. **"Try again" after a failed build** makes a new paid request (inside the caps). Default: yes.

## 6. Friction notes for RW5b and RW6b

- RW5b: add panels to `spec.py`/`figureSpec.ts` and their data to `evaluate_figure` with corpus cases
  (the corpus test fails until both evaluators agree); RK4 must be written in the same operation order
  in both. Offers (`origin = library | tutor`) already have their column values; `FigureRequest.origin`
  accepts them, the RPC does not yet take one.
- RW5b: verification is O(grid × samples × integrand); the normal-CDF corpus figure (an integral per
  sample) takes about 10 s in Python. Heavier panels want a coarser verification sample.
- RW6b: missed predictions are `reader_formative` texts with ids `fpr_…` and RW6a's
  `prediction_observations` returns them; the recap's "worth a second look" already has copy for them.
- The `LibraryJobs` runner records receipts under the sidecar's own owner (`sidecar_rpc`); the figure
  envelope counts its reservations, which is what admission reads.

## 7. Gate (implement step; owner rule 2026-10-17: targeted only)

Run on the tip with `TMPDIR=fixtures-local/tmp`, the full-suite lock free:

- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: done.
- `uv run lint-imports --no-cache`: **29 kept, 0 broken** (the new `evidence-never-reads-figures`
  contract included).
- `uv run pytest -n auto <209 files>`: **4,429 passed, 2 xfailed** (9 min 26 s). The files: every
  test file added or changed here and every one that exercises a changed module or pins what was
  touched (transport, `openai_chat`, `PaidCalls`, `span_view`, learner-text gaps, reader inquiry and
  intent, disclosures, the parameter registry, table roles, the defaults snapshots, reader
  observations, the head fixture, the prompt contract, routing, effective config, the salience
  firewall), plus the contract pins (CLI help, sqlite file copies, tracked fixture databases,
  coordinated migrations, desktop RPC contract, mobile allowlist, architecture, table roles,
  serializer snapshot, registry audit, grading CLI, p0 cutover, settings, AI config):

  `test_ad1_codex_rereview_fixes.py test_ad1_codex_review_fixes.py test_ad1_fix_round5.py test_ad1_migration.py test_ad1_reading_opportunities.py test_adaptive_difficulty_ad1.py test_agent_run_tokens.py test_ai_compare.py test_ai_config.py test_ai_single_request.py test_ai_tool_isolation.py test_approach_map_replay.py test_approach_maps.py test_approach_maps_schema.py test_architecture.py test_chatgpt_plan_cli.py test_chatgpt_plan_provider.py test_chatgpt_plan_workspace.py test_cli_help_snapshot.py test_codex_isolation_mcp_check.py test_coldness_receipt.py test_config_refactor.py test_constraint_engine.py test_coordinated_migrations.py test_daily_plan_replay.py test_decider_landing.py test_desktop_rpc_contract.py test_diagnose_review_spend.py test_diagnosis_context.py test_diagnosis_history_modes.py test_diagnosis_input_provenance_landing.py test_diagnosis_input_provenance.py test_diagnosis_isolation.py test_diagnosis_replay.py test_embedding_backfill.py test_embedding_store.py test_exam_protection.py test_exam_protection_review.py test_facet_identity_actions.py test_facet_identity_composition.py test_field_config.py test_figure_grammar.py test_figure_predictions.py test_figure_region.py test_figure_revisions.py test_figures_migration.py test_figures_rpc.py test_figures_switch_off.py test_figure_verification.py test_forecast_receipts_landing.py test_forecast_receipts.py test_glm_ocr.py test_grading_cli.py test_graph_nomination_ingest.py test_held_grade_composition.py test_help_assists_schema.py test_hint_feedback_texts.py test_hint_feedback_widening.py test_hint_h2b_review.py test_hint_outcome.py test_hint_telemetry.py test_hypothesis_reference_contract.py test_ingestion_checkpoints.py test_ingest_jobs.py test_ingest_ownership.py test_ingest_runner.py test_intent_codex_rereview.py test_intent_orchestrator_rulings.py test_item_fingerprints.py test_judge_routes.py test_kinship_feature.py test_learner_text_gaps_composition.py test_learner_text_gaps_flow.py test_learner_text_gaps.py test_learner_text_gaps_rereview.py test_learner_text_gaps_review.py test_learner_text_source_widening.py test_library_ask.py test_library_ask_review.py test_library_asks_migration.py test_library_exercises.py test_lo_general.py test_marker_pdfium_worker.py test_mcp_c1a_landing.py test_mcp_c1a_narrow.py test_mcp_c1a_review.py test_mcp_tools.py test_method_explicit_landing.py test_method_explicit_upgrade.py test_migrations.py test_mobile_allowlist.py test_model_call_receipt_owners.py test_model_usage_report.py test_multimodal_client.py test_mvp010_upgrade.py test_mvp011_upgrade.py test_mvp013_upgrade.py test_mvp014_upgrade.py test_mvp015_upgrade.py test_mvp016_upgrade.py test_mvp017_route_check_replay.py test_mvp017_upgrade.py test_mvp018_upgrade.py test_mvp020_upgrade.py test_mvp021_upgrade.py test_mvp022_upgrade.py test_mvp023_upgrade.py test_mvp024_upgrade.py test_openai_chat_client.py test_openai_embedding_client.py test_openrouter_video_client.py test_open_world_gate.py test_output_budget.py test_p0_cutover_mvp08.py test_p3_journeys.py test_pfc_unverified_unassessed.py test_pf_verify_extraction_parity.py test_plan_determinism.py test_practice_index_adapters.py test_practice_index_dossiers.py test_practice_index_find.py test_practice_index_paid.py test_practice_proposal_caller_columns.py test_prescription_passages.py test_probability_cli.py test_probability_prep.py test_project_atomicity.py test_project_blindness.py test_project_cli.py test_project_experiment_store.py test_project_probes.py test_project_report.py test_provider_resolution_parity.py test_reader_active_reading.py test_reader_activity.py test_reader_authoring.py test_reader_branches.py test_reader_cues.py test_reader_dialogue.py test_reader_find_sources_callers.py test_reader_formative_texts.py test_reader_inquiry_kill_switch.py test_reader_inquiry_status.py test_reader_intentions.py test_reader_intent.py test_reader_observation_records.py test_reader_passage_check.py test_reader_recap_review.py test_reader_reconnect.py test_reader_reconstruct.py test_reader_render_views.py test_reader_report.py test_reader_restoration.py test_reader_rw1b_final_verify.py test_reader_rw1b_fix_round4.py test_reader_rw1b_rereview.py test_reader_rw1b_review.py test_reader_rw2b_review.py test_reader_tutor_offers.py test_reader_tutor_retrieval.py test_reader_tutor_switch_off.py test_reader_workbench_rw2a.py test_reading_hardening_review_fixes.py test_reading_step_switch.py test_rebuild_orchestrator.py test_recurrence_benchmarks.py test_recurrence_commands.py test_recurrence_live.py test_registry_audit.py test_regrade_contract_successor.py test_regrade_contract_upgrade.py test_required_method_round3_review.py test_retrieval_interventions_write_points.py test_router_r2b_serving.py test_route_rules_in_grader.py test_rw4_kill_switches.py test_salience_firewall.py test_sensitivity_certificates.py test_serve_eligibility_review.py test_settings_sidecar.py test_shadow_rebuild.py test_sidecar_append.py test_sidecar_reader.py test_sidecar_serializer_snapshot.py test_sidecar_span_view.py test_source_block_fts.py test_source_outcome_analytics.py test_source_retrieval_codex_unavailable.py test_source_service_spend_accounting.py test_sources_merge_composition.py test_span_view.py test_spend_controls.py test_sqlite_file_copies.py test_structured_transport_parity.py test_stuck_prompt_replay.py test_success_head_cli.py test_t6_followup_composition.py test_t6_followup_review.py test_table_roles.py test_tier1_decider.py test_tracked_fixture_databases.py test_tutor_delivery_fixes.py test_ux_phase1_landing.py test_ux_phase1_review_fixes.py test_ux_phase4_landing.py test_workbench_chooser.py test_workbench_hint_service.py test_workbench_in_session_gaps.py test_workbench_text_gaps.py`
- `uv run pytest -n auto -m durability` on `test_figures_migration.py`, `test_ad1_migration.py`,
  `test_help_assists_schema.py`, `test_library_asks_migration.py`, `test_approach_maps_schema.py`,
  `test_learner_text_source_widening.py`, `test_tracked_fixture_databases.py`, `test_migrations.py`:
  **6 passed**.
- Frontend (`apps/learnloop-tauri`): `npm install`; `npm run typecheck` clean; `npx vitest run
  src/screens/reader src/screens/ReaderScreen src/components/pdfSelection src/components/PdfReaderPane
  src/screens/attentionBudget.test.tsx`: **70 files, 680 passed** (the figure files: 162 of them);
  `npm run frontend:build`: built.
- `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml`: finished (the seven
  passthroughs).
- References: `db_generate_reference.py` then `db_validate_reference.py`: **0 errors** (schema head
  216, 335 table notes, 937 configuration leaves in 67 sections).
- Defaults snapshots: 20 of 20 recomputed, 0 mismatches against `defaults_fingerprint_for_version`.
- No model was called: every test uses fakes; no CLI or app run touched a vault (the only run outside
  pytest recorded the switch-off golden on an export of `e14b4e4ff` under `env -i` with empty HOME,
  CODEX_HOME and LEARNLOOP_CONFIG_DIR, and the head fixture, references and snapshots the same way).
  The tracked working vaults are untouched.

## 8. Owner scope decision and redesign (2026-10-21)

After five fix rounds, the round-5 verify reopened both recurring classes. An Opus scope review
(the orchestrator's scratchpad, `rw5a-scope-proposal.md`) diagnosed the two classes:

- **Class A**, the "checked" claim: a figure-wide claim over an open, model-written document,
  guarded by hand-enumerated deny-lists.
- **Class B**, admission: the configuration was captured at job start and checked only at named
  call sites.

The owner decided to ship RW5a without "checked". This section records what that changes in §§1-5
above. The review's own record is `docs/reviews/reader-rw5a-codex-review.md`, "Owner scope
decision and redesign".

### 8.1 What is built now (replacing parts of §1.3, §1.4, §1.5 and §1.10)

- **Verification is spec §8.3 steps 1-2 only** (`learnloop.figures.verify`: structure, invariants,
  shaded areas). Step 3 is removed:
  - the verifier route and its prompt and output model;
  - the SymPy translation (`grammar.to_sympy`, `sympy_problem`);
  - the sandboxed source match;
  - rounds 2-5's binding, literal, branch and display-agreement rules and the certification
    version.

  A reconstruction is stored and shown as an illustration, with the reason "the book check comes
  in a later version". Nothing produces `verified`. A `verified` row stored earlier is shown as an
  illustration (`service.shown_row`). Migration 216's CHECK still allows `verified`, for RW5c.
- **One admission gate** (`learnloop.figure_admission.FiguresGate`, installed with
  `gate_model_requests`). It admits every physical request of a build, and of a figure prediction's
  learner-text reading. Before each request, retries included, it reads the configuration as it is
  now and compares it with the start:
  - **a build:** the vault, `figures.enabled`, the author route, `max_daily_cost_usd` and
    `price_per_million`;
  - **a reading:** the vault and the switch.

  Any change refuses that request and every later one. A build then raises `FigureRefused`
  (`figures_changed`) and stores nothing; it also checks again before the row is stored. A reading
  is released with its checkpoint, its attempt refunded. The sidecar's build reads
  `ctx.loaded_vault`; anything else reloads the vault from disk. The refusal (`FiguresChanged`) is
  a `BaseException`, so the learner-text pipeline's broad `except Exception` handlers cannot turn
  it into a "failed" reading and carry on. `pipeline.py` is unchanged.
- **One switch predicate with one default:** `figure_admission.figures_enabled`, off when there is
  no `figures` section. `service.enabled` and `text_gaps.sources.figures_enabled` both delegate to
  it.
- **Switched off, a queued figure text takes main's path.** Round 4's deferral state and its two
  drain exemptions are deleted, and `post_attempt_worker.py` is back to main's text. A figure
  text queued while figures are off reads as "nothing to read" and is skipped (dropped), as main
  does for a disabled source. `learnloop gaps run --backlog --dry-run --json` and
  `learnloop gaps run --json` on a vault with a queued `fpr_` job therefore equal main's output by
  construction (a golden recorded on an `e14b4e4ff` export).
- **Config:** `ai.routing.figure_verifier` is deleted (schema, routing, template note), and the 20
  defaults snapshots are recomputed. `[figures]` is unchanged.
- **Kept:** round 2's shared PF sandbox change (the harness reports a check's answer as given:
  inconclusive is not passing). It is recorded as its own PF item. Also kept: both corpora (golden
  and property) byte for byte, their Python/TypeScript parity, the grammar narrowing, the bounds
  and depth caps, F1, F5, F7 and migration 216.

### 8.2 Deviations (added to §2)

11. **Spec §8.3 step 3 and the `verified` outcome: deferred to RW5c.** Spec §8.1's first label,
    UX §4.7's first label, Moment 9's and W11's "(checked)" line, and §8.5's `figure_verifier`
    route are marked "deferred to RW5c" in both documents. Every RW5a figure carries the
    illustration label.
12. **G23** ("matches the source's equation" only after step 3 passed) **holds vacuously** in RW5a.
    G21, G22, G24 and G45 pass unchanged.
13. **A build stops when its switch, route, cap or price changes**, rather than being held to a live
    envelope (orchestrator decision): "try again" admits it under the new configuration.
14. **A figure text queued while figures are off is dropped** (owner decision): main's skip path,
    with no deferral state.

### 8.3 Open questions (with the defaults in force)

6. **RW5c's label scope.** Default: lenient. Code labels the checked series; model labels that do
   not reuse the source's identifiers are kept, and the claim is scoped to that element. The strict
   alternative code-labels every numeric element.
7. **Re-queue figure texts dropped while off** when the switch comes back on (about 15 lines).
   Default: no; they stay dropped.
8. **The flagship's "P(X ≤ 0)" readout** is a clipped integral (−40 to 0). It is correct within
   1e-6 for λ ≥ 0.5, but the label states an unclipped probability. It is not a source label, so
   the default is to leave it for RW5c's code labels.

### 8.4 RW5c (follow-up stage)

"Matches the book's equation (checked)" comes back as its own stage, designed before it is coded.
The design is a short spec amendment covering:

- the element-scoped claim: one `equals_source` definition, carried only by a plot or PMF series
  that is the bare reference to it, with a code-written label;
- a schema-walk token rule over every `Label` and `Text` field;
- an allow-list of constructs with an exact translation;
- an exact literal count from the decimal tuple;
- the standing float ruling now written into spec §8.3: "checked" never certifies float values at
  points the check did not sample.

Codex reviews the design adversarially ("find a displayed element or number this rule lets carry
the claim") before any code. The deleted machinery is in branch history at `865a3b38f`, as a
starting point.

## 9. Landing onto main

Landed in the `learnanything-merge2` worktree on branch `merge/rw5a-onto-main`, cut from main at `c80c54cbb` (the
RW7a landing record: migration head 217 with `migration_head_217`, which held 215 and 217; 20 defaults snapshots; 945
configuration leaves in 68 sections). The stage tip is `c29c1be2d` (base `e14b4e4ff`), unchanged. The orchestrator's
verifies: `20261021-090616-ZI8wj6` on `a559e35ea` (the whole stage) and `20261021-095546-vEb5ES` on `c29c1be2d` (the
final round; one High ruled out of scope, below). Main was neither fast-forwarded nor pushed here.

### Commits and conflicts

- `87c9b9a4a`: the `--no-ff` merge of `reader/rw5a` onto `c80c54cbb`. Main had gained RW3b (215), RW4d, RW4e and RW7a
  (217) since the stage's base, so 528 paths conflicted. Every conflict was composed so both sides survive:
  - **Generated references** (`Reference/Configuration/**`, `Reference/Database/**`): main's side, then regenerated.
  - **Head fixture**: main renamed 213 → 215 → 217 and the stage 213 → 216. `migration_head_217` keeps main's
    content (rebuilt with 216 in the next commit); the stage's `migration_head_216` and the old 213 paths are gone.
  - **Fixture paths**: 26 test files and `docs/decider-tier1-migration.md` differed only in `migration_head_216` vs
    `_217`; HEAD's side. Both reference scripts keep `SCHEMA_HEAD = 217` and `migration_head_217`.
  - **`config/template.py`**: in each of the 20 snapshot hunks, main's RW3b/RW4d/RW4e/RW7a comments, then RW5a's,
    then a hash recomputed in the next commit.
  - **Both kept, side by side**: `ai/routing.py` (tasks and route keys), `ai/disclosures.py` (the registry and the
    "when" texts; one closing parenthesis restored between `reading_paths` and `figures`), `config/schema.py` (routes),
    `params/parameter_registry.py`, `reader/reader_report.py` (both switches: `reading_paths_enabled` defaults to
    True, `figures_enabled` to False, as each stage left it), `cli/reader.py` (passes both), the sidecar's
    `reader.prompt_contract` (RW4d's, RW7a's and RW5a's fields), `tests/conftest.py` (all four model switches),
    `test_mobile_allowlist.py` (RW4d's, RW7a's and RW5a's pins), `test_judge_routes.py`, `test_reader_intent.py` and
    `test_reader_intentions.py` (both actions), `test_reader_tutor_switch_off.py` (pops RW4d's and RW5a's keys).
  - **Frontend and Tauri**: `ReaderScreen.tsx` (the `reading_path` and `figure` intent cases), `dto.ts` (both effect
    kinds), the intent fixture's header (both actions were already merged in its body),
    `libraryAskSwitchOff.test.tsx` (strips both later actions), `commands.rs` / `main.rs` (RW4d's, RW7a's and RW5a's
    passthroughs).
  - **Exact version sets** now say 215, 216 and 217 present, 214 absent: `test_ad1_migration` (`[213, 215, 216, 217]`),
    `test_reader_rw3b_migration` (`[215, 216, 217]`), `test_reader_rw7a_migration` (`[216, 217]` from 215, and the head
    fixture holds 215-217 with no 214), and the "nothing else changed" diffs of AD1, H0, H1, RW4a, RW3b and RW7a
    subtract `RW5A_ADDED_OBJECTS`.
- `c02d65aaf`: the regeneration (below).
- `229a5f782`: the composed switch-off pins and the interaction test (below). **This is the gate head.**
- This record (docs only).

**pf_sandbox callers.** On main the PF-b harness is used by `ops/pf_generation.py`, `ops/pf_verify.py`,
`ops/embedding_compare.py`, `content/authoring/pf_contracts.py` (protocol names), `source_exercise_import.py` (limits)
and `workbench/symbolic.py` (its own harness). None of them changed on main since `e14b4e4ff`; RW4e's labeller and
RW7a do not use it. Parity (d) covers the change.

### Regeneration (`c02d65aaf`)

- **Head fixture.** Main's `fixtures/migration_head_217/state.sqlite` blob was placed with the backup API and only 216
  applied under `UPGRADE_SCRATCH_COPY`; `wal_checkpoint(TRUNCATE)` (0, 0, 0), then `journal_mode=DELETE`; then backed up
  into place. Against main's fixture: **exactly RW5a's 12 objects** added (1,438 → 1,450), none removed or changed,
  every row of all 342 existing tables identical (apart from `schema_migrations` gaining `(216, interactive_figures)`),
  both new tables empty, header bytes 1/1, `integrity_check` ok, `foreign_key_check` empty, no `-wal` / `-shm`. The
  directory keeps its name (217 is still the highest version); its README says it now holds 215, 216 and 217 and no 214.
- **References.** `db_generate_reference.py`, then `db_validate_reference.py`: **0 errors**, schema head 217, **339**
  table notes, **952** configuration leaves in **69** sections (RW5a's `[figures]` and `ai.routing.figure_author`). The
  two prose counts (`Configuration.md`, `Database.md`) were updated from 945 / 68 / 337.
- **Defaults snapshots.** Template `.pyc` cleared, run with `-B`: all **20** entries moved (both sides add keys) and
  were rewritten from `defaults_fingerprint_for_version`; the re-check gives **0 mismatches**.
- **CLI help snapshot, RPC pins, mobile allowlist, serializer snapshot, table roles, architecture**: unchanged; a pin
  run of 92 files (every test naming the prompt contract, the reader report or a switch-off, plus the contract pins)
  gave 1,740 passed and one failure, RW4d's switch-off golden (next section).
- **`validate_vault.py`**: passes (1,142 notes, 1,140/1,140 reachable).
- **Figure corpora**: `python -m tests.figure_corpus` and `python -m tests.figure_property_corpus` under `env -i`
  regenerate both files **byte-identical** (golden: 84 expressions, 5 figures, 51 rejected inputs, 8 rejected figures,
  4 fuzz seeds; property: 3,152 cases).
- **Known failures from before this stage, not fixed:** `desktop_validate.py` still stops on
  `components/pdfSelection/testing/syntheticBook.ts`; `module_validate.py` reports **987** issues (968 at the RW7a
  landing; RW5a's new modules have no module notes).

### Composition fixes (`229a5f782`)

Each stage's switch-off golden was recorded before the others landed. The pins now remove what the other stages add,
and still compare everything else byte for byte:
- `test_compare_keep_switch_off.py` (RW4d): also sets `figures.enabled = false` (the failure of the pin run).
- `test_reading_paths.py` (RW7a): `_without_rw5a` pops `figures` and the `figure` action from the contract, and the CLI
  report drops RW5a's `figures` block.
- `test_figures_switch_off.py` (RW5a): strips main's later keys (`compareKeep`, `readingPaths` and "what matters
  here?") from the contract and the `comparisons`, `roles` and `reading_paths` blocks from the report.

**Interaction test** (`screens/reader/figuresWithReadingPath.test.tsx`, new; 2 tests): with `figures` and
`readingPaths` both in the contract, a figure stays inline under its passage in a section the Guide's path labels core,
under the code-owned frame; the palette carries both actions, "what matters here?" builds no figure and "make this
explorable" re-reads no path. **RW4e's role labels** are independent of figures: they are source-object proposals
shown in the library's grouping and used in retrieval and cue shortlists, never drawn under a passage or read by the
figure service, so no Reader test combines them.

### Gate

Setup: Python 3.12.14; `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2` (5.14.0); `TMPDIR` was
merge2's `fixtures-local/tmp`; every later command `uv run --no-sync`. Both suite lanes ran on `229a5f782` under
`flock /tmp/learnloop-fullsuite.lock`. The AD2+AD3 (`learnanything-ad1`) and E0 (`learnanything-e0`) worktrees and their
processes were not touched (AD2+AD3's own test run shared the machine). Every test uses fakes.

**This is the first full run over RW5a's code**: the stage, its five fix rounds, the redesign and the final round ran
targeted tests only.

| Check | Result |
|---|---|
| `lint-imports --no-cache` | **29 kept**, 0 broken (RW7a's landing: 28; RW5a adds `evidence-never-reads-figures`) |
| full suite `pytest -n auto` | **15,424 passed, 1 failed, 1 skipped, 2 xfailed** (19 min 27 s; `fixtures-local/rw5a-landing/fullsuite.log`). The failure is a cross-test leak (finding 1): rerun alone 3 times, **5 passed** each time. RW7a's landing ran 15,114 |
| `pytest -m durability` | **119 passed**, 15,309 deselected (4 min 53 s); RW7a's landing had 118 |
| `npm install`, `npm run typecheck` | ok; clean |
| `npm test` (the whole vitest run) | **169 files, 1,469 tests passed**, no unhandled error (RW7a's landing: 165 / 1,292) |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | ok (RW5a's seven passthroughs) |
| tracked fixtures, worktree | `git status` clean after both lanes and the frontend runs; no `-wal` / `-shm` beside a fixture |

No real failure, so no landing fix.

### Parity (backup-API copies; no model call completed)

**Setup.** Scripts in `fixtures-local/landing-rw5a/scripts/`, adapted from the RW7a landing's; new: `ab_rw5a.sh`,
`c_rw5a.sh`, `fig_run.py`, `fcmp.py`, `pf_parity.py`, `dcmp.py`, `head_build.py`, `civ.py`.
- **Copies.** `fixtures/linear_algebra` and `fixtures/probability` were copied once with `copy_tree_with_databases`
  from the main checkout into `fixtures-local/landing-rw5a/orig/`; every other copy came from `orig/` or its upgraded
  copies through the same helper. `arxiv_v2` was not opened. Both start at schema 165, label `mvp-0.8`, 0 receipts.
- **Code.** Main's is `git archive c80c54cbb`; the merge's `git archive 229a5f782`.
- **Environment.** `env -i` with only `PATH`, `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`, `TMPDIR` and `LANG`; the
  three directories empty, and empty afterwards.
- **Routes.** `neutralize3.py` under each code: every route field to `127.0.0.1:9` (58 on main, 59 on the merge, where
  `figure_author` is the new one), the active provider to that loopback profile with no fallback, query rewrite /
  rerank / dense / embeddings / learner-text gaps off, `build_on_serve` and outcome placement off. `routes.py` resolved
  61 `AITask`s on main and 62 on the merge; nothing outside the loopback profiles except the disabled, keyless
  `embedding`; `figure_author` → `blackhole` (`openai_chat`, `http://127.0.0.1:9/v1`).

**(a) Migration 216**

| Check | linear_algebra | probability |
|---|---|---|
| open (migrate), main / merge | 165 → 217, 50 applied (no 214, no 216) / 165 → 217, **51** applied (216 included, no 214) | the same |
| schema, main vs merge | merge-only objects are exactly RW5a's **12** (`interactive_figures`, `figure_predictions`, 5 named indexes, 3 autoindexes, the no-delete and explanation-once triggers); none main-only; no shared object's SQL differs (1,439 → 1,451) | the same 12 (1,438 → 1,450) |
| rows of every existing table (342), all columns | **identical** (16,541 rows); `schema_migrations` gains 216, common rows differ only in `applied_at`; both new tables empty | **identical** (7,639 rows; the same) |
| `foreign_key_check` / `integrity_check` | 0 / ok, both | the same |
| `rebuild --shadow --json` | **0 differences** after normalisation (facet 0, mastery 2, schedule 8 on both); live database unchanged on both | **0 differences** (0 / 1 / 1) |
| `doctor --json` | **0 differences** after normalisation (57 issues, 1 error) | **0 differences** (101 issues, 48 errors) |

**(b) Nothing served changes.** The merge ran at its defaults (figures **on**), frozen clock 2026-10-19 09:00 UTC:
certification with recipe gaps and curves; the Today queue (no session, session, greedy); the daily plan (read, served
twice, read again).

| Check | linear_algebra | probability |
|---|---|---|
| at `mvp-0.8` | cert (132,860 bytes), Today (504,488), plan (546): **byte-identical** | cert (17,494), Today (709,910), plan (546): **byte-identical** |
| upgraded by main's code to `mvp-0.27` (`--to mvp-0.9`, `--to mvp-0.27`, `rebuild-derived-state` twice; rc 0), opened by each code | cert (129,651) and Today (528,665) **byte-identical** | cert (17,495) and Today (741,269) **byte-identical** |
| then to `mvp-0.29` (`--to mvp-0.29`, `rebuild-derived-state` twice; rc 0) | cert and Today **byte-identical** | the same |
| the daily plan at mvp-0.27 and mvp-0.29 | identical except `router_decisions.card_hash`, `snapshot_hash` and the card hash inside `detail_json`; a second run of main's code on a fresh copy differs from the first in exactly these three and equals the merge's (`plan_repeat.sh`), as at the earlier landings | the same |

**(c) The real sidecar** over stdio, `SystemClock` frozen at 2026-10-19 09:00 UTC (`sidecar_clock.py`), on copies of
main's mvp-0.29 vaults; driver `fig_run.py`, compared by `fcmp.py` with run ids normalised. Runs: (i) `cm` main's code;
(ii) `coff` the merge with `[figures] enabled = false`; (iii) `cdef` the merge at defaults; (iv) `civ` (probability only)
(iii) plus `figures.price_per_million = 1.0` and a dummy key in the loopback profile's variable, so the metered author
really sends to `127.0.0.1:9`. Calls: `initialize`; `reader.prompt_contract`; `reader.figures`; `reader.figure_request`
on an equation block (probability `ext_01KYMSJJNJQ0W9QHZ9ZMFD88NY` `s38`; linear_algebra `ext_01KY2YGNVCCVEQCGCE4RH3BWHQ`
`s52`), polled with `reader.figure_job`; `reader.figures`; the same request again (*try again*), polled;
`reader.figure_job_cancel` on an unknown job; `reader.figures`; on probability a manual-graded attempt on
`pi_prob_derive_complement`; `shutdown`. Then `learnloop reader report --json` and
`learnloop gaps run --backlog --dry-run --json` on the same copy.

| Step | (i) main vs (ii) switch off | (iii) defaults: every difference from (i) |
|---|---|---|
| `initialize` | **the seven RW5a RPCs register while off** (method list); `migrationsApplied` 202 vs 203; the vault path | the same |
| `reader.prompt_contract` | **identical** | gains `figures {predictions, region, revisions: true}`; Understand's palette gains "make this explorable" (10 actions, was 9) |
| `reader.figures` (3 reads) | (i) `method_not_found`; (ii) refused `figures_disabled` ("Explorable figures are switched off (figures.enabled).") | the source's figures: none |
| `reader.figure_request` (twice) | the same two refusals | a job (`pending`), then **failed, `unpriced`** ("A metered figure route needs figures.price_per_million."): refused before any request; nothing stored |
| `reader.figure_job_cancel` (unknown) | the same two refusals | `not_found` |
| the attempt (probability) | every call **identical**; its rows in 23 tables identical across (i)-(iv) | identical (ids normalised) |
| `reader report --json` | identical apart from `window.until` (the CLI's clock) | gains `figures` (all zero: built `{}`) |
| `gaps run --backlog --dry-run --json` | **byte-identical** | **byte-identical** |
| rows beyond the attempt | none | `interaction_events` 2 (`figure_requested`, salience only); no figure, ledger, spend or receipt row |

So (i) and (ii) are identical call by call apart from the method registry (and so the off refusal code), the vault
path and the applied-migration count.

**(iv) The route actually tried** (probability): 2 builds × 2 author attempts = **4** requests; **8**
`model_call_receipts`, every one **`failed`** (4 `figure_author` `AIProviderUnavailable`, 4 transport children
`APIConnectionError`, all to `http://127.0.0.1:9/v1`); 2 `interactive_figures` rows `verification = failed` (no spec,
never shown; the view's reason "the figure model failed: AIProviderUnavailable") with 2 `figure_verified` ledger rows
(`failed`); 4 `source_service_spend` rows under `figures.max_daily_cost_usd`, each **settled at its ~$0.0216 estimate**
(finding 2); the report counts `built {failed: 2}`. No row is `verified` on any copy.

**(d) The PF stricter-inconclusive change** (`pf_parity.py`, on a backup copy of probability with its `[pf]` sandbox
limits: 20 s CPU, 2,048 MB, 60 s wall; real bubblewrap). Eleven check programs ran through each code's own
`run_generator_tests`, `check_generator_answers`, `run_equivalence_checks` and `equivalence_confirmations`, and each
code's own generation rule:

| Check answers | main → merge |
|---|---|
| Python `True`/`False`; `numpy.bool_`; `sympy.true`/`false`; an evaluated `sympy.Eq`; `1 == 1`; a raise on a wrong answer; an always-`True` (degenerate) check | **identical** (every harness field except the new `negative_controls_inconclusive`; gate pass / pass, the degenerate one fail on controls both sides; confirmations unchanged) |
| `1`/`0` | pass → **fail** (self-check not `True`); confirmations `[True, False]` → `[None, None]` |
| `True` / `None` on a wrong answer | pass → **fail** (controls inconclusive); `[True, False]` → `[None, None]` |
| `'yes'` / `''` | pass → **fail**; `[True, False]` → `[None, None]` |
| an unevaluated `sympy.Eq(x, 1)` | fail (error: `bool()` raises) → fail (self-check not `True`) |

Only non-boolean answers changed: PF generation and PF verification are slightly stricter on main.

**`model_call_receipts`.** 39 learner databases under `landing-rw5a/` carry the table. **No row completed** in any of
them; the only rows are (iv)'s 8 failed ones.

### New findings

1. **A cross-test thread leak in the full suite (Low, from before this stage).**
   `test_learner_read_model_pinning.py::test_read_model_opens_one_connection_per_call[build_learner_review_feed]` counted
   3 connections instead of 1: the two extra were to another test's vault (`test_a_tutor_keep_takes_a_take...`, RW4d's
   `test_compare_sources_keep.py`) on the same xdist worker, a background thread of that test still running while this
   one patched `repositories.connect`. Alone, 3 runs × 5 passed. **Follow-up:** RW4d's tutor-keep test should join its
   background work before returning.
2. **A transport failure is charged its estimate against the figure cap (Low).** As at the RW7a landing (its finding
   2): each refused connection settled its full estimate (~$0.0216) in `figures.max_daily_cost_usd`; a failed build
   and one *try again* used $0.087 of the $1.00 a day. This is the shared `PaidCalls` / `SharedDailyEnvelope`
   accounting, and the cap still bounds repeated *try again*. On Codex (the default) the route is `estimated_only`.
3. **The figure RPCs register while off.** Off, every one refuses `figures_disabled` and nothing is called or written;
   only `initialize`'s method list (and so the refusal code) differs from main. The same holds for RW7a's.
4. **Composition was all in tests.** No source file needed a landing fix beyond keeping both sides; the switch-off pins
   of RW4d, RW5a and RW7a needed each other's keys removed.

### For the owner

- **Migration 216 applies on the next open** of a vault by the merged code, through the coordinator. **Close the app,
  the MCP server and the mobile host, and back up first.** It adds two empty tables (`interactive_figures`, WORKFLOW;
  `figure_predictions`, append-only RAW_LEDGER). No existing row changes and nothing served moves (parity (a), (b)).
  Your algorithm version is unchanged; there is no successor.
- **What you see.** Select an equation or passage in the Reader → *make this explorable* (Understand). It builds in the
  background (*◐ building an interactive version — keep reading*, with cancel) and lands as a collapsed line under its
  passage; open it for sliders with numeric fields, function plots with shading, PMF bars, 2-D linear maps, readouts,
  play-only animation (step buttons under reduced motion) and a values table (`t`). **Every figure is an illustration**:
  the badge is written by the Reader's code, "AI-built illustration of an interpretation · not checked against the
  book" (or "couldn't build a reliable version of this" / "can't draw this yet · noted"); nothing says "checked" (RW5c).
  What is checked are the figure's **property checks** (finite values, the invariants it declares, shaded areas against
  an independent integration), named in the frame's words. Before your first change it may ask a **prediction** (never
  graded; code decides whether it matched), then "what changed? (optional)": a missed prediction and its "what changed?"
  become `reader_formative` learner text only while learner-text gaps and `reader_formative` are on. *Not right?* asks
  for a new version with your note; the earlier one is kept. A request with the same input reuses the stored figure.
- **Routes.** `figure_author` follows the active provider (Codex by default, `estimated_only`). Regions (Ctrl+drag a box
  in a Figure/Picture block on the PDF page) need an **image-capable** `figure_author` profile (OpenRouter or an
  OpenAI-compatible profile with `image` in `input_modalities`); with a text-only route a region is refused before any
  call, and a figure block is sent as its caption and neighbours.
- **Caps and switches.** `[figures] enabled`, `predictions_enabled`, `region_enabled`, `revisions_enabled` (all true);
  `max_daily_cost_usd = 1.00` and `price_per_million` (unset: a metered route is refused before sending, as parity (c)
  showed). Per request at most two author attempts, one physical request each. One `FiguresGate` re-reads the switch,
  route, cap and price before every request and stops the build if any changed. `enabled = false` restores main's
  Reader: no contract key, no palette action, no report block, every figure RPC refuses, and a figure text queued while
  off is dropped (main's skip path).
- **The PF stricter-inconclusive change (its own PF item).** The shared PF-b sandbox now reports a check's answer as
  given: only a real boolean (Python's, numpy's, sympy's) counts. A generator check answering `1`, `None` or a string,
  or a check answering a wrong answer with something not `False`, now fails PF generation and confirms nothing in PF
  verification and the embedding comparison. Boolean checks behave exactly as before (parity (d)).

### Open questions (defaults in force)

1. *Grid size?* At most 4 parameters (81 grid points).
2. *Image route?* The active provider (often Codex, text only); regions need an image-capable `figure_author`.
3. *The ◇▸ margin mark?* None; the collapsed line under the passage is the mark.
4. *One prediction per figure?* The first only.
5. *"Try again" after a failed build makes a new paid request (inside the caps)?* Yes.
6. *RW5c's label scope?* Lenient (element-scoped claim on the checked series).
7. *Re-queue figure texts dropped while off when the switch comes back on?* No; they stay dropped.
8. *The flagship's "P(X ≤ 0)" readout (a clipped integral)?* Left for RW5c's code labels.

### Open items

- **Codex isolated turns (High, ruled out of scope at the final round).** Codex isolated turns keep utility tools and
  sub-agents, so `figure_author` (like every other source-only Reader route on main that uses the same isolation
  layer) is isolated and workspace-free but not strictly tool-free, and the per-turn `FiguresGate` admission does not
  see internal continuations. Queued follow-up: "Codex isolated turns: prove or enforce no utility-tool/sub-agent file
  or network access and gate internal continuations, for every isolated route".
- **Lows ruled across rounds:** float rendering resolution; model label text inside the code-owned frame; the gap
  pipeline's mid-reading cap/price/route behaviour (queued as "live admission for learner-text-gap readings"); a
  provider `base_url` change in the middle of one build; a reading whose last request completed before a switch flip.
- **RW5c** ("matches the book's equation (checked)"): its own stage, designed (§8.4) and Codex-reviewed before code.
- **Findings 1-2** above (Low).
- **From before this stage:** `desktop_validate.py` (`syntheticBook.ts`) and `module_validate.py` (987 issues).

**Process note (landing).** Every Python and CLI run outside pytest went through `env -i` with an empty HOME,
CODEX_HOME and LEARNLOOP_CONFIG_DIR, with two exceptions that read nothing: a `python3 -` with an empty here-document
(no code executed) while composing the head-fixture README, and `.venv/bin/python --version` after `uv sync`. Neither
opened a vault, made a network call or touched a credential. No stash was used, no fixture vault was opened except
through `learnloop.db.copies`, and no git command ran in the main checkout.
