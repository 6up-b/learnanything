# Router objective RO2: the frontier LLM full-history forecaster (`router/ro2-forecaster`)

Spec: `docs/specs/spec_router_objective_v1.md` §6 (as built: §6.6). Base `248421272c` (RO1's landing branch: mvp-0.46,
migration 244). No successor tag (as AD1). Migration **245** (`245_history_forecaster.sql`, rechecked at landing).
Fakes only: no paid call was made in this stage, and no real forecast was sent.

## What exists

| Part | Where |
|---|---|
| Switch `llm_history_v1` in `adaptive_difficulty.outside_forecasters` (default on) | `adaptive_difficulty/switches.py`, `config/schema.py` |
| The draw and the frozen rungs, in the serve transaction (AD's serve savepoint) | `adaptive_difficulty/history_forecast.freeze_history_inputs`, called from `serve.record_plan_serve` |
| The background job (after `llm_v3`'s pair, same job, own claim `claims.history_key`) | `history_forecast.forecast_history_presentation`, `background.schedule_presentation_forecasts` |
| Card `ad-forecast-state-v3`, rungs H0-H3, bounded reads, budget trimming | `adaptive_difficulty/history_card.py` |
| Kind `lo_cold_success`, binding `lo_cold_after_block` (code only; no CHECK on either column) | `scheduling/forecast_receipts.py` |
| The draw table `ad_history_forecast_draws` (RECEIPT, append-only) | migration 245, `db/stores/ad_receipts.insert_history_draw`, `table_roles.py` |
| AD guard registrations: `help_assists`, `learner_text_gaps`, `reader_session_digests`, the draw table (PROTECTED; help's own rule; digests a READING table; `tutor_question` entity kind) | `protected_tables.py`, `column_classes.py`, `material_view._self_withheld` |
| Bounded `MaterialView.rows(limit=)` | `material_view.py` |
| Versioned resolver `ad-history-resolver-v1` (per protocol, intention to treat) | `adaptive_difficulty/history_resolve.py` |
| Comparisons, ladder, delayed cold, missing pairs, hierarchical calibration slopes | `scoring.history_report`; `learnloop ad report` block `history_forecaster` (`report.py`) |
| `learnloop ad forecast-audit --mode permuted|prior-sweep [--run]` | `adaptive_difficulty/history_audit.py`, `cli/ad.py` |
| Registry: `adaptive_difficulty.history_card_token_budget` (keep), every new module constant | `params/parameter_registry.py` |

## For the owner before landing: what it costs and how it is enabled

- **Enabled by default.** `"llm_history_v1"` joins the default `outside_forecasters` list (as AD1's three are on by default;
  owner rule of frictionless defaults with kill switches). A vault whose `learnloop.toml` lists `outside_forecasters`
  explicitly does not get it until the name is added; `outside_forecasters = true` includes it. Off: remove the name (or set
  `forecast_receipts`/`enabled` false). Nothing stops automatically.
- **Calls per eligible presentation: 2** (H3, plus the one drawn rung of H0, H1, H2, each with probability 1/3). Eligible:
  every plan presentation AD records whose item is not protected (the same set `llm_v3` freezes).
- **Tokens per call:** the frozen card, at most `history_card_token_budget` = 48,000 UTF-8 bytes (an upper bound on its
  tokens; real tokens are roughly a quarter to a third of that), plus about 1,000 bytes of instructions and the schema, in;
  at most 1,200 tokens out. A learner with little history sends a few kilobytes. H0 is the smallest (about `llm_v3`'s card).
  So at most about 2 x (14k in + 1.2k out) tokens per presentation; typically far less.
- **Route and money:** `ai.routing.ad_forecast_llm` (the ChatGPT plan by default: `estimated_only`, counted at $0 against
  `adaptive_difficulty.daily_spend_cap_usd`). A metered route is refused unless `adaptive_difficulty.price_per_million` is
  set, and then counts against the same daily cap. A plan usage pause, the cap, an unavailable route or an invalid answer
  each write a censored receipt (`skipped:<reason>`), never a number.
- **The audit** is owner-run: `learnloop ad forecast-audit --vault <copy> --mode permuted` is a free dry run (calls, estimated
  tokens, the route's billing and cost); `--run` sends one call per frozen H3 card that has a donor. `--mode prior-sweep` is
  free either way.

## Choices where the spec was open, or the code had moved

Each with why and the smallest alternative.

1. **Where it sits.** §6.1 says "in `outside.py`". The forecaster runs on `outside.py`'s machinery (`Clients`, the route
   resolution, `_record_admission`, `_store_payloads`, `source_identity`, `history_card`, `SendGuard`, the claims, the
   spend envelope) from two sibling modules, so `outside.py` (785 lines) changes only by H0's two parameters and
   `llm_v3`'s request is byte-identical. Alternative: move the two modules' bodies into `outside.py`.
2. **One table added.** Skips per rung are receipts (`forecast_receipts.status` allows `ok | failed | refused_spend`, so a
   plan pause is `failed` with `censor_reason` `skipped:plan_paused`), but the paired comparison needs its denominator
   whatever was written, including a refusal that writes nothing: `ad_history_forecast_draws`. Alternative: widen
   `forecast_receipts.status` (a table rebuild of an append-only table) and drop the draw table.
3. **One call per rung** answers `p_now` and the three cold lags; receipts are one per probability (four per call).
4. **Hedges** (§6.3 H1 "confidence taps and hedges"): the taps are on the card; the grader's hedge reads live in
   `grading_evidence`, the incumbent's derived state, which AD's guard denies. Alternative: a named carve-out for
   `confidence_events`' hedge read.
5. **Tutor answers** are not quoted (a tutor's answer can carry an item's worked solution: "no reference solution");
   the learner's question, its type, the disclosure state at the ask and whether it was answered are. Alternative: quote
   answers to questions on attempted items only.
6. **`learner_protection`.** `withheld_items` reads tables AD's guard refuses (follow-up tasks, remediation episodes, probe
   presentations), which would poison the serve's AD operation. The card applies its pure `attempt_protection` over a
   `Withheld` built from the view's withheld set and the vault's probe modes: exam work keeps its result only, a probe
   shows no question and no answer, an item the vault no longer holds no text. Held grades (THE predicate reads denied
   tables) are not marked "held for review"; grades show as AD's view and `llm_v3`'s card show them.
7. **Availability.** For `practice_attempts` the card asks RO1's predicate (`attempt_time_sql`) **and** `coalesce(received_at,
   created_at)` at every version, so a backdated import is out until it arrived even below the RO1 tag or with
   `available_at_reads` off (RO2's card has no predecessor to keep byte-identical). `help_assists` has no `created_at`:
   `coalesce(shown_at, requested_at)`. A reading receipt: its source's write time.
8. **Personal notes** are not read by any rung (the spec allows them only if linked and allowlisted; no allowlist exists).
9. **H2's Reader rows** are reached through AD's reading receipts on the LO (`ad_reading_opportunities`, revalidated by the
   view), their source rows (inquiries in `question_events`, self-checks in `reader_authored_questions`, exposures in
   `source_exposure_events`), and the digests of the readings those name. A Reader question's text shows only once the
   learner answered it (no unattempted stem), never its key.
10. **The resolver.** The block ends at the latest attempt answering any presentation of its block (the serve when none).
    "Unseen item" is an item of the LO never attempted before. Exposures are visible attempts, reveals (a lesson's teaching
    text reaches the ledger as reveal rows: the "intervening lesson" case) and reading receipts on the LO. AD's outcome
    categories decide the label (help, a reveal during it or a stuck answer: 0; a primed answer: censored); an ungraded
    attempt is passed over and recorded. Below one day the 1-day forecast stands.
11. **Delayed cold comparisons** are among the rungs only: `mastery_ekf`, `lo_general+composite` and `llm_v3` make no cold
    forecast. Alternative: score the arms' `p_now` as a cold proxy (not the same event).
12. **Intervals** are AD's anytime-valid confidence sequences on the paired log-loss difference
    (`monitoring.confidence_sequence`, AD §8.3), on whatever has resolved.
13. **Slopes** per model and prompt version: a MAP logistic recalibration under a seeded prior (a calibrated forecaster,
    `scoring.SLOPE_PRIOR`), each version's prior centred on the pooled posterior (the hierarchical prior; a new version
    starts there, never at an older version's slope). The prior-strength sweep refits under 0.25x to 4x the prior's spread;
    it needs no model call, so it is free (the spec groups it with the paid permuted run).
14. **Permuted history:** the donor is the nearest frozen H3 card by the incumbent's forecast (`mastery_ekf`'s `p`, "a
    similar level") of another item served no later, so a permuted card carries no event after its own serve. Frozen inputs
    are payloads, pruned after `router.payload_retention_days`: the audit sees only what is retained, at the current
    protection epoch.
15. **The serve's added cost** (§6.5) on a synthetic vault (300 earlier attempts with answers, 40 help rows, 40 questions):
    about 22 ms inside a 145 ms serve (`test_the_serve_transactions_added_cost_is_measured`). The first build measured
    about 200 ms, nearly all re-serializing the card once per trimmed entry; trimming now subtracts each entry's own size
    and serializes once per pass.

## Tests written for this stage (reproduce-first: each fails before RO2)

- `tests/test_ro2_history_forecaster.py`: the serve freezes the draw and two rungs; the forecaster off gives no row and
  no call; each rung sent exactly as frozen, its receipts and judgments; skips censored with their reason (plan pause,
  spend cap, retried later); invalid probabilities censored.
- `tests/test_ro2_history_protection.py`: held-out material on no rung (H0-H3), including a help row citing a held-out
  span, exam work result-only, no reference solution or tutor answer; content held out after the serve never sent or
  recorded; the leak test (a backdated exam import and help, questions and reveals after the serve reach no card, at the
  RO1 tag and below it; after the import it shows, dated when it happened); the budget trims oldest first within each
  rung and says so.
- `tests/test_ro2_history_resolve.py`: log-time interpolation; both bindings on an unexposed outcome with both clocks; an
  intervening lesson (a reveal) censors per protocol and is recorded under intention to treat; beyond the measured lag
  and pending; a seen item is no cold check; the report on the same presentations with the missing pairs; slopes shrink a
  new version to the population; the audit's dry run (and the CLI) calls and writes nothing; the permuted run sends
  another presentation's history; the serve's added cost measured.
- `tests/test_ro2_history_migration.py`: 245 is the head, its table a RECEIPT AD classifies; the head fixture holds it in
  rollback mode; 245 adds exactly its objects, append-only; the durability lane.

Existing tests changed, each for what RO2 changes: the head pins and `RO2_ADDED_OBJECTS` in the earlier migrations'
diffs (31 and 16 files, mechanical); `test_help_assist_figures_migration.py`, `test_help_assist_work_md_migration.py`
and `test_learner_note_source_kind_migration.py` (RO2 registers `help_assists` and `learner_text_gaps` for AD's reads);
the four snapshot-pin tests (`test_data_capture_successor.py`, `test_ro1_successor.py`, `test_teacher_te1_successor.py`,
`test_teacher_te1b_suggestions.py`) drop RO2's two config changes before their frozen digests; the salience firewall's
reader allowlist (`test_salience_firewall.py`) names the card and the resolver, which read a reading receipt's kind,
LO and time, never a dose into the state. `tests/ad_fakes.ForecastLLM` answers `HistoryForecastV1`.

## Gate (this step; the full suite runs once at landing)

All commands inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, pytest at `-n 6`.

| What | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | done |
| `uv run lint-imports --no-cache` (frozen cycles included) | 43 kept, 0 broken |
| Batch 1: every test file naming the head fixture, the migrations or `RO2_ADDED_OBJECTS` (108 files) | 1460 passed, 7 skipped, 21 failed: 18 defaults-fingerprint pins read while the snapshots were being recomputed mid-run, 3 registry pins (fixed); the 21 files rerun: all passing in batch 2 |
| Batch 2: every test file touching `adaptive_difficulty`, `outside_forecasters`, the receipts and payloads, the fakes, `learner_protection`, `help_assists`, `table_roles`, the registry, the snapshots or the config schema, plus the RO2 files and the contract tests (CLI help snapshot, serializer snapshot, desktop RPC contract, mobile allowlist, architecture, tracked fixture databases, display labels, the Codex lockdown and process-launch allowlist, SQLite copies, RO1's availability reads, the AD guard and its registry, config refactor) and batch 1's failures (235 files) | 10614 passed, 13 skipped, 41 xfailed, 5 failed (four frozen-digest pins and the firewall allowlist, fixed) |
| The 5 fixed files rerun | 5594 passed |
| `pytest -m durability tests/test_ro2_history_migration.py tests/test_ro1_availability.py` | 2 passed |
| `pytest --durable-sqlite` on the four RO2 test files | 24 passed |
| `db_generate_reference.py`, `db_validate_reference.py` (DB and config reference at head 245, 1140 leaves) | `errors: []` |
| `module_generate.py`, `module_validate.py` | PASS |

No frontend, desktop or Rust file changed (no npm, vitest or cargo run). None of the owner's uncommitted phone paths,
`.gitignore` or `README.md` was touched. The list of test files run is `docs/reviews/router-ro2.targeted-tests.txt` (322).

## Paid calls

None. No paid command was run (the audit was exercised with fakes); no vault copy was made.

## Open questions

- Should `llm_history_v1` stay on by default (2 calls per eligible presentation on the plan, $0 on the subscription), or
  start off until the owner flips it?
- The hedge reads (`grading_evidence`) and held grades need a named carve-out in AD's guard to reach the card; worth it?
