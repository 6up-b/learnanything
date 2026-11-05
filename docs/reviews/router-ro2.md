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
  tokens; real tokens are roughly a quarter to a third of that), plus about 1,000 bytes of instructions and the schema, in.
  Out (corrected by the Codex review's F5; the earlier "1,200" was a constant the send never used): each call reserves the
  route's own output budget, `ai.route_output_tokens.ad_forecast_llm`, else the serving profile's `max_tokens`, else
  `ai.output_tokens` (16,384 by default), and one retry at most double; the answer itself is four probabilities and at
  most three sentences (a few hundred tokens). A learner with little history sends a few kilobytes. H0 is the smallest
  (about `llm_v3`'s card). So per presentation at most about 2 x (14k in + 16k reserved out), plus one retry each at
  worst; typically far less in, and a few hundred out.
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

## Landing onto main: stopped at the smoke, not landed

Main was at `79a1ce32a9` (RO1: mvp-0.46, migration 244, `migration_head_244`; FG1d: no migration). Steps 0 to 4 ran.
Step 5's smoke hit one of the brief's stop conditions: **with the forecaster on, AD's serve rows differ from main's on
all three owner copies**. So RO2 does not land at this tip; the branch carries steps 0 to 3 and this record.

### Rulings (verbatim)

- R1: "F9 is fixed by failing closed: an inquiry whose ancestry reaches a parent that a capped read left unread gets an unknown root and status and open false, and the card records inquiry_ancestry among the reads that hit their limit. Codex's 60-thread reproduction is the test."
- R2: "F7's remainder is Low under the proportionate bar and not fixed here: an older inquiry placed on the scope only by its anchor's current mapping, behind 100 newer unrelated inquiries, is missing from a forecaster's card. It is model input, not evidence, and nothing a learner sees changes. The card must say so: when the recent-inquiries read hits its limit, the card lists it among the reads that hit their limit."
- R3: "H2's inquiry reads have had three rounds, so there's no further Codex round on them. A further finding there is Low unless it puts protected or post-serve material into a card."
- R4: "The forecaster stays on by default, as the spec says (§6.4: it runs until the owner turns it off). The orchestrator tells the owner before landing what it sends per presentation and how to turn it off. The smoke measures real card sizes on the owner's copies so that number is real."
- R5: "Open questions stand as recorded and go to the follow-up batch: hedges and held grades stay off the card while AD's guard denies those tables; inquiry status set through paths that write no log reads unknown; workbench sessions and steps are unclassified for AD; forecast-audit only sees presentations within router.payload_retention_days."

### Step 0: F9 and F7's card note (`44b78d6158`)

Recorded in `docs/reviews/router-ro2-codex-review.md` ("Final verify ... and the landing fixes"). F9: a parent that a
capped ancestry read left unread is unresolved (root and status `unknown`, `open` false, `inquiry_ancestry` listed);
Codex's 60-thread reproduction failed on the pre-fix source (`q_20_2` rooted at `q_20_1`, open) and passes after it.
F7's remainder: no code change; `recent_inquiries` was already listed when it hit its limit, and Codex's scenario is
now a test that pins it. Spec §6.6 amended.

### Step 1: the merge (`5cbf9a8519`)

Conflicts only in the generated references (477 notes; RO2's side kept, then regenerated). Main's non-generated changes
(FG1d: `attempts.py`, `followup_run/marks.py`, `handlers/feedback.py`, two tests, records) touch nothing RO2 touches,
and main added no migration, config key or successor since RO2's base. Main's `migration_head_244/state.sqlite` is the
same blob RO2's head was built from (`929b55ae0e`). A rebuild from it (backup-API copy outside the checkout,
`apply_migrations` under the scratch-copy allowance) applied `[245]` only, and its `iterdump` matches the tracked
`migration_head_245` line for line except the `schema_migrations` row's `applied_at`. So the head stands (README noted).
The defaults snapshots, fingerprints, registry, `table_roles.py` and AD guard registrations needed no change.

### Step 2: early checks (`81fb9bb2dc`)

- `lint-imports --no-cache`: 43 kept, 0 broken (frozen cycles kept).
- 24 files, `-n 6`, 5G scope: 457 passed, 1 skipped, 0 failed. They were:
  - `test_measurement_state_labels.py`, `test_cli_help_snapshot.py`, `test_codex_lockdown_round3.py` (process-launch
    allowlist);
  - `test_ro1_availability_reads.py`, `test_ro1_availability.py`, `test_ro1_successor.py`;
  - every `test_ro2_*` (4 files);
  - FG1d's two;
  - `test_table_roles.py`, the four AD guard files, `test_registry_audit.py`, `test_coordinated_migrations.py`,
    `test_tracked_fixture_databases.py`, the serializer and RPC snapshots, `test_architecture.py`,
    `test_config_refactor.py`, `test_codex_tool_lockdown.py`.
- **The structural availability test now covers RO2's reads.** The history card reads attempts through
  `MaterialView.rows(connection, "practice_attempts", where, ...)`, with no `FROM practice_attempts` for the SQL scan to
  see. So `test_ro1_availability_reads.py` gained:
  - the card's `attempts` among the decision-time readers that must ask the predicate;
  - a second scan, of calls that name `practice_attempts` as a table argument beside a WHERE literal with an upper
    bound on `created_at`. Each must ask the predicate or be allowlisted. Only the card's read matches, and it asks.

### Step 3: references (`81fb9bb2dc`)

`db_generate_reference.py` + `db_validate_reference.py`: errors `[]` at head 245, 1140 leaves. `desktop_validate`
passed; `module_validate` PASS; `validate_vault.py` passed (2195 notes). The fingerprints carried over unchanged (main
changed no config).

### Step 4: gate (at `81fb9bb2dc`)

| Lane | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | done |
| `lint-imports --no-cache` | 43 kept, 0 broken |
| Full suite (`-n 8 --dist worksteal`, 10G scope, under the full-suite lock) | **26354 passed, 91 skipped, 47 xfailed, 0 failed** (57:17); FG1d's landing had 26316 |
| Durability lane (`-m durability`) | 402 passed, 1 skipped |
| Owner lane (fresh backup-API copies of `owner-copies-mvp035` in `fixtures-local/landing-ro2/`) | 83 passed, 4 skipped, and the same 2 known failures as at FG1d's landing (`test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events`, `test_placement_fixture_copies[arxiv_v2]`) |
| Desktop: typecheck, vitest (`--maxWorkers=4`, 5G), frontend build | ok; 2751 passed; ok |
| `cargo check` | ok |
| Mobile: typecheck, build | ok; ok |

No unexpected failure, so nothing was rerun.

### Step 5: smoke, and the blocker

Setup:

- Copies: fresh backup-API copies of `~/learnloop-backups/mvp043-20261103-copy/{arxiv_v2,linear_algebra,probability}`
  in `fixtures-local/landing-ro2-smoke/`, every AI route at `127.0.0.1:9`. Each was upgraded on main code to mvp-0.45,
  then to mvp-0.46, then `rebuild-derived-state` (head 244).
- Code: `git archive 79a1ce32a9` (main) and `git archive 81fb9bb2dc` (branch), both with `migrations/`.
- Driver: RO1's landing driver, adapted. Today, the plan, Next with serve (the plan's steps answered), a real
  `submit_attempt` through the tests' grader and diagnoser fake with its diagnosis drained, the router card, the 4 to 25
  feedback bundles, and every row written. Frozen clock and module-stream ids. AD's own background scheduling was off on
  both sides, so the forecaster's job ran separately, with an in-process fake.

**The blocker.** On branch code with `llm_history_v1` on (the default), every Next serve on every copy logged:

```
AD guard denied read of source_document_units (a protected table read outside the rules) by learnloop.section_map:
AD is unavailable for the rest of learnloop.adaptive_difficulty.serve.record_plan_serve
AD1 serve receipts for presentation ... not recorded (ViewDenied)
```

The path is `serve.record_plan_serve` → `history_forecast.freeze_history_inputs` → `history_card.build_sections` →
`_inquiries` → `_inquiry_los` → `VaultReadingMap.los_for_span` → `reader_progression.learning_objects_for_span` →
`section_map.section_id_for_span` → `repository.load_document_ir`. That is a raw `source_document_units` read outside
the reading chokepoint (`MaterialView.document_ir`, `Scope.DERIVE`). AD's guard refuses it and poisons the operation.
The serve's savepoint then rolls back every AD write of that serve:

- AD1's serve receipts;
- `llm_v1`/`llm_v3`'s frozen inputs;
- the reading sweep's rows;
- RO2's own draw and cards.

Any Reader or library question anchored to a block span (`span:<extraction>/<span>`) triggers it. Since F7, the
`recent_inquiries` read brings in the newest 100 such questions on any LO, so one such question anywhere in the vault
is enough. All three copies have them: arxiv_v2 1, linear_algebra 5, probability 3. Each one, mapped inside an AD
operation, poisons it, whether or not its reading is withheld.

The tests missed it because no RO2 test vault holds a span-anchored Reader question with a document IR. The plan vault
has no Reader spans, and F7's anchor test supplies the mapping with a test double. A reproduction
(`test_a_span_anchored_reader_question_does_not_poison_the_card_build`: the textbook fake, one Reader question on
`span:ext_text/<span>`, `build_sections` in an AD operation) fails at this tip with the same denial. It is kept outside
the tree, in the orchestrator's scratch directory (`ro2-landing/repro/`).

What differs from main, journey by journey (the ids, the times and RO2's own rows aside):

| Copy | Forecaster off (removed from `outside_forecasters`) | Forecaster on (default) |
|---|---|---|
| arxiv_v2 | IDENTICAL; no RO2 row, no call | `forecast_receipts` 5 → 1 (AD1's 4 serve receipts lost), `item_forecast_payloads` 2 → 0; no RO2 row |
| linear_algebra | IDENTICAL; no RO2 row, no call | `ad_reading_opportunities` 81 → 0, `forecast_receipts` 9 → 1, `item_forecast_payloads` 4 → 0; and so AD's prediction the router reads moved: the router card's `p_band_next` 0.0416 → 0.0241 for one cell, and `router_decision_payloads`/`decision_state_receipts` differ the same way; no RO2 row |
| probability | IDENTICAL; no RO2 row, no call | `forecast_receipts` 3 → 1, `item_forecast_payloads` 1 → 0; no RO2 row |

On every copy, Today, the plan, Next's items and their order, the submit, its feedback and every bundle stayed
identical. What changed is AD's recorded state, and on linear_algebra the router's input. That is the stop condition
"serving differs with the forecaster on". It also means the forecaster sends nothing on these vaults.

**Fix direction (not applied; for the orchestrator).** `_inquiry_los` has to map a span through the reading
chokepoint, or not at all. Two things to know:

- `VaultReadingMap.los_for_span` and `los_for_section` are refused inside any AD operation. The probe on these copies:
  `MaterialView.document_ir` itself is allowed, but `learning_objects_for_section` loads the IR again, raw.
- The same calls sit in AD3's reading sweep (`reading_sources.py` lines 123, 144, 205, 232) and `dose.py:159`. On these
  copies the sweep never reached them on main (0 denials), but the latent issue is AD3's as well as RO2's.

A fix needs an IR-taking section-to-LO mapping behind `document_ir`, with the sweep's withheld check first. Its test is
the reproduction above.

**Everything else, with a smoke-only stand-in for that fix.** `los_for_span` was patched, on both sides, to return the
incumbent's mapping computed outside any AD operation. Then:

- **Serving**: main vs branch on, IDENTICAL on all three copies (Today, plan, Next, submit, feedback, every bundle and
  every row), plus RO2's rows:

  | Copy | Draws | Frozen cards |
  |---|---|---|
  | arxiv_v2 | 2 | 4 |
  | linear_algebra | 4 | 8 |
  | probability | 1 | 2 |

  No AD warning on either side.
- **The job** (in-process fake, `ForecastLLM`): every rung was sent exactly as frozen (the prompts equal
  `prompt_for(frozen state)`), H3 plus the drawn rung, 2 calls per presentation. Per presentation it wrote:
  - 8 receipts (2 `item_unassisted_success` bound to the presentation, 6 `lo_cold_success` bound `lo_cold_after_block`);
  - a request and a response payload per rung;
  - 8 judgments.

  arxiv_v2: 2 presentations, 16 receipts. linear_algebra: 4, 32. probability: 1, 8.
- **Protection on real data.** Every frozen card (14) was scanned for:
  - every item's reference answer and rubric text;
  - the stem of any item not attempted by the serve, other than the served item;
  - exam answers;
  - any attempt, question or help id dated after the serve.

  One hit, a false positive: linear_algebra's H3 `other_topics` lists an item attempted 105 days before. Its stem is a
  multiple choice whose option A reads exactly as the item's reference answer ("A. It is linearly dependent because
  ..."). The stem is the attempted item's own, which the learner saw, and the card does not say which option is
  correct.

  Held out after the serve: on arxiv_v2 and probability, the unit holding the served item's source span was marked
  `held_out_evaluation` (the rest of the selection kept). Each send was then refused (`protected`): nothing sent, no
  receipt. linear_algebra's served items have no source reference, so there was nothing to hold out.
- **Skips**: the fake raised a plan pause on one presentation and the spend cap on the next. Each wrote censored
  receipts with `binding_kind = none` and no `p`: `skipped:plan_paused` (`failed`) and `skipped:spend_cap`
  (`refused_spend`). No judgment.
- `learnloop ad report` ran on each copy (exit 0). The `history_forecaster` block lists the new forecasts' cold outcomes
  as pending: arxiv_v2 4, linear_algebra 8, probability 2. Nothing has resolved yet (no later attempt).
- `learnloop ad forecast-audit --mode permuted` (dry run) on linear_algebra says it would send `calls: 3`,
  `estimated_tokens: 155824`, `estimated_tokens_with_retries: 360800`, `output_tokens_per_call: 16384`,
  `retries_per_call: 1`, `model_calls: 0`, `writes: 0`, with `estimated_usd: null`. The route there is the neutralized
  `blackhole` (metered).
- **Rebuild.** RO2's rows (draws, payloads, receipts, judgments) were the same before and after a state sync, a full
  rebuild and a second sync: arxiv_v2 (2, 12, 16, 16) and probability (1, 6, 8, 8).
  - `rebuild --shadow` after the journeys: probability 0/0/0 on every side; arxiv_v2 facet 0, mastery 1, schedule 1, the
    same on main code.
  - The driver writes its later plan steps' answers straight into `practice_attempts`, so the shadow counts them. On
    linear_algebra one of them (`independent_attempt` on an item that does not allow it) stops the replay, on main code
    too.
- **The serve's added cost** (one run each, during the gate, so noisy):

  | Copy | `freeze_history_inputs` inside the serve | `record_plan_serve` total, main / branch |
  |---|---|---|
  | arxiv_v2 | 2.9 to 5.3 ms | 30 to 71 / 32 to 76 ms |
  | linear_algebra | 9.0 to 11.0 ms | 92 to 330 / 96 to 321 ms |
  | probability | 11.2 ms | 201 / 135 ms |

  The interleaved Today, Next and submit timing was not run; it belongs to the rerun after the fix.
- **No real model.** `model_call_receipts` added only the fakes' rows (`fake` and `fake_llm`). probability's 56
  `chatgpt`, `chatgpt_low` and `openrouter_decider` rows are in the backup itself. No non-loopback connect, no name
  resolution and no Codex process appear in the watch log; its only subprocesses are `git` and `powerprofilesctl`.

### R4: what the forecaster sends, on the owner's copies

Measured with the stand-in above, at every point each copy's history would have served:

- each recorded plan presentation: arxiv_v2 0, linear_algebra 0, probability 1;
- each non-self-report attempt's item, one second before the answer: arxiv_v2 0, linear_algebra 62, probability 3;
- every item now, at 2026-11-04T15:00Z: arxiv_v2 32, linear_algebra 84 (15 protected items skipped), probability 77.

Sizes are UTF-8 bytes of the frozen card and of the whole prompt. Tokens are estimated as bytes/4.

| Copy (points) | Rung | Prompt bytes, min / median / max | About tokens, median (max) |
|---|---|---|---|
| arxiv_v2 (now, 32) | H0 / H1 / H2 / H3 | 1,702 / 1,890 / 2,126; 1,767 / 1,955 / 2,191; 1,833 / 2,021 / 2,257; 1,910 / 2,098 / 2,334 | 472 / 488 / 505 / 524 (583) |
| linear_algebra (attempts, 62) | H0 / H1 / H2 / H3 | 1,567 / 3,078 / 7,802; 1,634 / 4,667 / 17,197; 1,700 / 5,187 / 17,263; 3,943 / 13,648 / 34,197 | 769 / 1,166 / 1,296 / 3,412 (8,549) |
| linear_algebra (now, 84) | H0 / H1 / H2 / H3 | 1,668 / 5,559 / 8,663; 1,733 / 10,270 / 18,713; 1,799 / 10,471 / 18,779; 22,131 / 29,965 / 35,817 | 1,389 / 2,567 / 2,617 / 7,491 (8,954) |
| probability (attempts, 3) | H0 / H1 / H2 / H3 | 1,764 / 2,567 / 3,372; 2,833 / 5,655 / 8,621; 3,877 / 6,889 / 9,860; 3,954 / 6,966 / 9,937 | 641 / 1,413 / 1,722 / 1,741 (2,484) |
| probability (now, 77) | H0 / H1 / H2 / H3 | 1,632 / 1,860 / 5,425; 1,697 / 1,925 / 15,575; 1,940 / 6,537 / 16,814; 3,391 / 7,988 / 18,058 | 465 / 481 / 1,634 / 1,997 (4,514) |

- Per presentation, H3 plus the expected drawn rung:
  - linear_algebra now: 38,821 bytes median (about 9,700 tokens), 51,202 max (about 12,800);
  - probability now: 11,501 bytes (about 2,900), max 30,662 (about 7,700);
  - arxiv_v2: about 1,000 tokens.
- No card reached the 48,000-byte budget, nothing was trimmed, and no read hit its row limit on any copy.
- Output: each answer is four probabilities and at most three sentences (a few hundred tokens). Each call reserves
  `ai.output_tokens` (16,384), and at most one retry.
- A typical day, from each copy's own history of non-self-report attempts (the proxy for presentations: the plan served
  almost nothing):

  | Copy | Active days | Presentations per day, median / mean / max | Calls per day, median | Input tokens per day, median |
  |---|---|---|---|---|
  | linear_algebra | 6 | 8 / 10.3 / 25 | 16 | about 78,000 (at today's sizes) |
  | probability | 2 | 2 / 2 / 2 | 4 | about 6,000 |
  | arxiv_v2 | none (only self-reports) | | | |

  A 25-presentation day on linear_algebra is 50 calls, about 240,000 input tokens. On the ChatGPT plan route it counts
  $0 against `adaptive_difficulty.daily_spend_cap_usd`.

### How to turn the forecaster off

In the vault's `learnloop.toml`:

```toml
[adaptive_difficulty]
outside_forecasters = ["llm_v1:item", "llm_v3:llm", "llm_v3:decider"]
```

That is the default list without `llm_history_v1`. `forecast_receipts = false` or `enabled = false` turns off AD's
forecasts altogether. With it off, the smoke was identical to main on all three copies, with no RO2 row and no call.

### What the owner must run

Nothing: RO2 is not landed. After a fix and a clean rerun of this smoke, the owner would update each vault to migration
245 by opening it (the desktop app, or `learnloop doctor --fix-state --vault <vault>`). There is no successor tag and
no rebuild. Then the owner would rebuild the desktop app and restart the phone host, as for earlier stages.

### Open items

- **The blocker above** (span mapping inside AD's operation). It needs a fix with its reproduction, then this smoke
  rerun: the interleaved timing, the full journeys without the stand-in, and the shadow on journeys without raw
  attempt inserts.
- R5's items stand as ruled: hedges and held grades, unlogged status paths, workbench classification, and the audit's
  retention window.
- AD3's reading sweep and `dose.py` make the same `los_for_span` and `los_for_section` calls inside AD operations
  (latent on main; not reached on these copies).

### Rules not followed

- During the merge investigation, one `uv run --no-sync learnloop --help` ran outside the `env -i` wrapper (grepped
  for "sync"; it printed nothing). No vault, config, network or model was touched.

## Landing onto main, second pass

The orchestrator ruled on the stopped record, and the fix and a full rerun followed. Main is still `79a1ce32a9`.

### Rulings (verbatim)

- R6: "The AD guard denial on span-anchored inquiries is a real defect and blocks landing. The fix is structural: every span-to-section and section-to-LO mapping reached inside AD's operation takes the document IR from MaterialView.document_ir, after the sweep's withheld rule is checked. An IR-taking section_id_for_span and learning_objects_for_section, with the raw-loading versions as thin wrappers for callers outside AD. The same fix applies to main's latent call sites (reading_sources.py at the four lines you found, and dose.py:159), since it is the same helper and the same class: an AD serve rolled back by a guard denial."
- R7: "A test scans the code reached from AD's operation (the history card's reads, the reading sweep, dose) and fails on any call to repository.load_document_ir or another raw document loader. Your reproduction (a span-anchored Reader question on a textbook fake) is a test at mvp-0.45 and mvp-0.46 and passes after the fix; with it, a test shows a guard denial on any AD read leaves the learner's serve unchanged, as it does now."
- R8: "No further Codex round on R6: the reproduction is the test, and the smoke rerun without the stand-in is the check. Landing needs, on all three copies with the forecaster on: no AD guard warning, AD1's serve receipts, the frozen inputs and the reading-sweep rows identical to main (linear_algebra's 81 included), and the router card's AD prediction identical to main. A further finding on this class is Low unless it rolls back an AD serve write or puts protected or post-serve material into a card."

### R6: the fix (`c170f020f0`)

- **`section_map.py`** gains three functions that take the IR from their caller: `section_id_in_ir`,
  `learning_objects_for_span_in_ir` and `learning_objects_for_section_in_ir`.
  - `section_id_for_span`, `learning_objects_for_span` and `learning_objects_for_section` keep their signatures. They are
    now thin wrappers that load the IR and call the IR-taking versions, for callers outside AD (the Reader, data capture,
    the router's reading reads, the gap sources).
  - `learning_objects_for_span` loads the IR once now. Before, it loaded it twice: once in `section_id_for_span` and again
    in `learning_objects_for_section`.
- **`VaultReadingMap`** (`adaptive_difficulty/reading.py`) is the one map that the history card, the reading sweep's sources
  and dose use.
  - `los_for_span` and `los_for_section` first apply the sweep's withheld rule (`withheld(extraction, span)`). Then they
    take the IR from `MaterialView.document_ir`, cached per map, and call the IR-taking versions.
  - The helpers get the operation's projected repository (`project_repository`). So the span translator's re-read
    aliases also load each reading through the view, whichever repository the map was built with.
  - This covers all of the sweep's calls: `reading_sources.py` lines 112, 123, 144, 205, 229 and 232, and `dose.py` 159
    and 272.
- **A correction to the stopped record.** The sweep and dose are `@entry` points, and those receive `op.repository`, a
  `ProjectedRepository` whose `load_document_ir` already is the view's. So on main their calls did not poison; my first
  probe built the map with the raw repository. RO2's card built its map from `reads.view.repository`, which is raw, and
  so did RO2's resolver (`history_resolve`). After R6 the map no longer depends on the repository it is handed.
- **The reproduction** is `tests/test_ro2_ad_document_ir.py`, at mvp-0.45 and mvp-0.46. It uses the textbook fake, an LO
  citing a span of `ext_text`, and a Reader question on `span:ext_text/<span>`. Three tests run at each version:
  - the card builds inside an AD operation with the inquiry on H2;
  - the map gives inside the operation the LOs the incumbent gives outside it, for the span and its section
    (`["lo_matrices"]`);
  - `record_plan_serve` writes AD1's receipts, the frozen inputs and RO2's draw, and H3 carries the inquiry.

  All 6 failed on the pre-fix source (the guard denial) and pass after the fix.

### R7: the structural guard (`a6ff74ba9d`)

`tests/test_ro2_ad_raw_document_reads.py`:

- **A static walk** starts from every function of `history_card.py`, `reading.py`, `reading_sources.py` and `dose.py`. It
  follows calls to module functions, imported names, `self` methods and classes, across all of `src/learnloop`.
  - It fails on any call to `load_document_ir`, `document_blocks` or `document_blocks_on_pages`, except inside
    `MaterialView.document_ir`.
  - One entry is named with its reason: `span_aliases._computed`. AD reaches it only through the map's projected
    repository, and the run-time test below checks that.
  - It asserts that the walk does reach `VaultReadingMap.los_for_span`/`los_for_section` and
    `learning_objects_for_section_in_ir`, and that the named entry is not stale.
- **A test of the wrappers.** The raw-loading versions call the IR-taking ones, and the IR-taking ones never load an IR.
- **A run-time check** on the span-anchored fake. During the map's span and section mapping, the card build and a whole
  `record_plan_serve` (its sweep included), every `Repository.load_document_ir` call happens inside
  `MaterialView.document_ir`.
- **A guard denial in AD's serve leaves the learner's serve unchanged.** The denial is forced by a read of
  `grading_evidence` inside `freeze_history_inputs`. The step and the presentation row stay the same as an undenied
  serve's. The denied serve writes no `forecast_receipts`, `item_serve_inputs` or draw row; the undenied one writes all
  three.

On the pre-fix source, the walk, the wrapper test and the run-time check fail; the denial test passes, as R7 asks.

### The audit's estimate, reconciled (`219f7e7887`)

`forecast-audit --mode permuted` on linear_algebra estimates 155,824 tokens for 3 calls. That splits into:

- 103,525 prompt bytes (three permuted H3 cards of about 34.5 KB, counted one byte per token);
- about 3,150 for the answer schema and the framing;
- 49,152 reserved output (3 × 16,384).

That is the charge the spend caps reserve, an upper bound. Expected use is about 26,000 input tokens (bytes/4) plus a few
hundred output tokens per call. That is about 9,000 tokens per call, in line with the measured cards (H3 now: about 7,500
tokens median on linear_algebra).

The output did not say any of this, so the dry run now adds:

- `prompt_bytes`;
- `reserved_output_tokens`;
- `estimate_counts`: "an upper bound the spend caps reserve, not expected usage: each call's prompt as UTF-8 bytes
  (real tokens are about a quarter to a third of that), the answer schema and framing, and the whole reserved output
  budget (output_tokens_per_call), of which an answer uses a few hundred tokens; _with_retries adds one retry per call at
  double that budget".

No charge changed. The dry-run test pins the new fields.

### Targeted checks (step a)

- `lint-imports --no-cache`: 43 kept, 0 broken (frozen cycles kept).
- 38 files, `-n 6`, 5G scope: **1384 passed, 0 failed**. They were:
  - every `test_ro2_*` (6 files with the two new);
  - the four AD guard files;
  - every test naming `reading_sources`, `section_map`, `reader_progression`, dose, `VaultReadingMap`, the span mapping
    functions or `span_aliases` (26 files);
  - `test_ad3_reading.py`, `test_ro1_availability*.py`, `test_table_roles.py`, `test_architecture.py`;
  - the early checks: `test_measurement_state_labels.py`, `test_cli_help_snapshot.py`, `test_codex_lockdown_round3.py`.
- The audit-wording change: `test_ro2_history_resolve.py` and the CLI help snapshot, 16 passed.
- `--durable-sqlite` on the two new files, `test_ro2_history_protection.py`, `test_ro2_history_resolve.py` and
  `test_ad3_reading.py`: 48 passed.
- References (`d88d56ab82`): `db_validate_reference` errors `[]` at head 245 (nothing to regenerate); module catalog
  regenerated, `module_validate` PASS; `desktop_validate` and `validate_vault` pass.

### Gate (step b, at `d88d56ab82`)

| Lane | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | done |
| `lint-imports --no-cache` | 43 kept, 0 broken |
| Full suite (`-n 8 --dist worksteal`, 10G scope, under the full-suite lock) | **26365 passed, 90 skipped, 47 xfailed, 0 failed** (54:43). The first pass had 26354 |
| Durability lane (`-m durability`) | 402 passed, 1 skipped |
| Owner lane (FRESH backup-API copies of `owner-copies-mvp035` in `fixtures-local/landing-ro2/`) | 83 passed, 4 skipped; the same 2 known failures as at FG1d's landing and the first pass (`test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events`, `test_placement_fixture_copies[arxiv_v2]`) |
| Desktop typecheck, vitest, build; `cargo check`; mobile typecheck, build | carried over from `81fb9bb2dc` (ok; 2751 passed; ok; ok; ok, ok): the second pass changes nothing under `apps/` or `src-tauri` |

No unexpected failure, so nothing was rerun.

### Smoke, second pass (step c)

Fresh backup-API copies of the three `mvp043-20261103-copy` vaults were made as in the first pass (main code, mvp-0.45,
mvp-0.46, `rebuild-derived-state`, head 244). The code was `git archive 79a1ce32a9` (main) and `git archive 219f7e7887`
(branch: every code change of the second pass), both with `migrations/`. **No stand-in.** The same driver ran with
warnings logged.

**R8, per copy** (the full journey: Today, plan, Next steps, submit, feedback, the bundles, the router card, every row):

| Copy | Off vs main | On vs main | AD guard warnings, main / on | AD1 serve receipts, main / on | Frozen inputs (`llm_v1`/`llm_v3`), main / on | Reading-sweep rows, main / on | Router card AD prediction | RO2 rows on: draws / cards |
|---|---|---|---|---|---|---|---|---|
| arxiv_v2 | IDENTICAL, no RO2 row | IDENTICAL plus RO2's rows | 0 / 0 | 4 / 4 | 2 / 2 | 0 / 0 | identical | 2 / 4 |
| linear_algebra | IDENTICAL, no RO2 row | IDENTICAL plus RO2's rows | 0 / 0 | 8 / 8 | 4 / 4 | **81 / 81** | identical (`p_band_next` 0.0416 on both) | 4 / 8 |
| probability | IDENTICAL, no RO2 row | IDENTICAL plus RO2's rows | 0 / 0 | 2 / 2 | 1 / 1 | 0 / 0 | identical | 1 / 2 |

A second, submit-only journey (the real `submit_attempt` only, no raw attempt inserts) gave the same result on every
copy. On it, linear_algebra again had 81 / 81 sweep rows, and its router card's AD prediction was 0.1974 on both sides.

Every check of R8 holds. linear_algebra's frozen H2/H3 cards now carry its span-anchored inquiries (3 on three of its
four presentations).

**Everything else, without the stand-in.** The results are those of the first pass:

- **The job** sent every rung exactly as frozen. Receipts, payloads and judgments per copy:

  | Copy | Presentations | Receipts | Judgments |
  |---|---|---|---|
  | arxiv_v2 | 2 | 16 | 16 |
  | linear_algebra | 4 | 32 | 32 |
  | probability | 1 | 8 | 8 |

  Each presentation has 2 `item_unassisted_success` receipts bound to it and 6 `lo_cold_success` receipts bound
  `lo_cold_after_block`.
- **Protection scan** of all 14 frozen cards: no problem. The one hit is the same false positive as in the first pass: a
  multiple-choice stem the learner answered, whose option A is its reference answer.
- **Held out after the serve:** on arxiv_v2 and probability the send is refused (`protected`), with nothing sent and no
  receipt. linear_algebra's served items have no source reference.
- **Skips:** `skipped:plan_paused` (`failed`) and `skipped:spend_cap` (`refused_spend`) are censored receipts with no
  `p`, binding `none` and no judgment. A paused call's one retry resends the same prompt.
- **`learnloop ad report`:** exit 0 on each copy, with cold outcomes pending: arxiv_v2 4, linear_algebra 8, probability 2.
- **Audit dry run:** as reconciled above.
- **Shadow** after the submit-only journeys: 0/0/0 on every copy, on main code and on branch code. It is still 0/0/0
  after the job ran there.
  - The full journeys' shadow is not 0/0/0: arxiv_v2 shows mastery 1 and schedule 1, and linear_algebra's replay stops
    on the driver's raw `independent_attempt` insert.
  - Both are the same on main code, and both come from the driver.
- **RO2's rows survive a state sync, a rebuild and a second sync** (draws, payloads, receipts, judgments, before and
  after):

  | Copy | Full journey | Submit-only journey |
  |---|---|---|
  | arxiv_v2 | (2, 12, 16, 16) | (1, 6, 8, 8) |
  | linear_algebra | not run (the driver's insert stops the rebuild) | (1, 6, 8, 8) |
  | probability | (1, 6, 8, 8) | (1, 6, 8, 8) |
- **Isolation:**
  - The watch log for this pass holds only `git` and `powerprofilesctl` subprocesses: no connect, no non-loopback
    connect, no name resolution, no Codex process.
  - `model_call_receipts` gained only the fakes' rows (`fake`, `fake_llm`). probability's 56 older rows come from the
    backup.

**R4 again.** The card sizes did not move. The same 32, 146 and 81 serve points were measured without the stand-in, and
every rung's card size is byte-identical to the first pass. So the first pass's R4 tables stand: the fixed mapping gives
exactly the incumbent's LOs. No read hit its limit, nothing was trimmed, and no operation was poisoned.

**Timing.** Medians in ms. Each copy ran 4 interleaved rounds of main, branch off and branch on, each on a fresh copy,
after the gate with nothing else running. Today was called 5 times per run.

| Copy | Side | Today | Next | Submit | `record_plan_serve` | `freeze_history_inputs` (max) |
|---|---|---|---|---|---|---|
| arxiv_v2 | main | 147.2 | 431.1 | 384.8 | 47.0 | |
| arxiv_v2 | off | 149.3 | 430.2 | 393.4 | 44.8 | 0.0 |
| arxiv_v2 | on | 148.1 | 417.5 | 395.2 | 52.4 | 5.9 (7.5) |
| linear_algebra | main | 205.5 | 556.1 | 401.4 | 132.2 | |
| linear_algebra | off | 203.4 | 534.2 | 394.9 | 104.8 | 0.0 |
| linear_algebra | on | 202.7 | 511.4 | 403.7 | 123.8 | 19.4 (21.8) |
| probability | main | 153.8 | 526.2 | 632.5 | 108.5 | |
| probability | off | 160.7 | 578.0 | 672.5 | 174.1 | 0.0 |
| probability | on | 153.4 | 555.5 | 671.5 | 186.6 | 16.6 (17.6) |

Sample sizes: Today 20 per cell; Next 12, 20 and 8 per copy; submit 4.

- **The cost inside the serve** is `freeze_history_inputs`: 5.9 ms on arxiv_v2, 19.4 ms on linear_algebra and 16.6 ms on
  probability (medians).
  - That is more than with the first pass's stand-in (3 to 11 ms). The span and section mapping now builds through
    the view's IR, once per map.
  - It is well inside Next's run-to-run spread: Next on linear_algebra was 511 to 556 ms across the three sides.
- **Today and submit** are unchanged within their spread.
- **On probability, both branch sides read above main** for `record_plan_serve` (174 and 187 against 109) and for
  submit (about 672 against 633). It is the same with the forecaster off, where `freeze_history_inputs` costs 0.0 ms,
  so it is not the forecaster's call. Each of those cells has only 4 samples, and I did not look further. It is listed
  under open items.

### What the forecaster sends, for the owner (R4, unchanged)

- 2 calls per eligible plan presentation: H3, plus one drawn rung from H0, H1 and H2.
- Each answer is a few hundred tokens; each call reserves 16,384 output tokens and allows one retry.
- At today's card sizes, per presentation:

  | Copy | Input tokens per presentation, median (max) |
  |---|---|
  | linear_algebra | about 9,700 (12,800) |
  | probability | about 2,900 (7,700) |
  | arxiv_v2 | about 1,000 |

- A typical day (from the copies' own history): linear_algebra about 8 presentations, 16 calls and 78,000 input tokens;
  its busiest day was 25 presentations, 50 calls and about 240,000.
- It goes on the ChatGPT plan route (`ai.routing.ad_forecast_llm`), at $0 against `adaptive_difficulty.daily_spend_cap_usd`.
- To turn it off: in the vault's `learnloop.toml`, under `[adaptive_difficulty]`, set
  `outside_forecasters = ["llm_v1:item", "llm_v3:llm", "llm_v3:decider"]`. With it off, the smoke is identical to main
  on all three copies.

### What the owner must run after the fast-forward

1. Open each vault with the new code to apply migration 245. That is the desktop app, or
   `learnloop doctor --fix-state --vault <vault>` (it adds one empty table). There is no successor tag, no
   `learnloop upgrade` and no rebuild. If a vault is still below mvp-0.46, run the earlier stages' upgrades first, as
   their records say (`learnloop upgrade --to mvp-0.45`, then `--to mvp-0.46`).
2. Rebuild the desktop app, and restart the phone host so it serves the new code.
3. Optional, free: `learnloop ad forecast-audit --vault <a backup copy> --mode permuted` shows what the audit would send.
   It is a dry run unless `--run` is given.

### Open items

- R5's items stand as ruled: hedges and held grades stay off the card, inquiry status set through unlogged paths reads
  unknown, workbench sessions and steps are unclassified for AD, and forecast-audit sees only presentations within
  `router.payload_retention_days`.
- The smoke driver writes its later plan steps' answers straight into `practice_attempts`, which the shadow then counts
  (on main code too). The submit-only journey gives 0/0/0. That is a smoke-driver issue, not a product one.
- probability's `record_plan_serve` and submit read above main on both branch sides, with only 4 samples per cell (see
  Timing). It is unexplained but not the forecaster's call; a longer interleaved run would settle it.
- `adaptive_difficulty/data_check.py` (the `learnloop ad data-check` report) calls the raw-loading
  `learning_objects_for_span`. It is not an AD operation, so the guard does not apply; it is listed here because it
  shares the helper.
