# Adaptive difficulty AD1: measure and log

Stage `adaptive-difficulty-ad1` of `docs/specs/spec_adaptive_difficulty_v1.md` (§14 AD1, no
successor), branch `adaptive-difficulty/ad1`, worktree `learnanything-ad1`, base `16a0071f2`
(the hints H2b stage tip, migration head 212). Owner go-ahead 2026-10-18, running in parallel
with the hints track; H2b lands on main first and AD1 merges main before its own landing.
Prerequisite D18 (diagnosis input provenance, migration 205) is on the base.

## 0. Plan (written before the code)

**What AD1 is.** Logging that changes nothing served: receipts (forecasts, frozen serve inputs,
reading opportunities), two nullable attempt columns (rating, first-hint progress) and feature
audit judgments. No algorithm successor, no new persisted meaning, no read of any of it by
serving, scoring, scheduling, evidence, FSRS or certification (A2, A12). Live behind four
switches under `[adaptive_difficulty]`, plus the master `enabled`.

**Files** (planned, then built as listed in §5): migration 213; `db/table_roles.py`;
`db/stores/ad_receipts.py`; the new package `learnloop/adaptive_difficulty/`; the receipt
family's vocabulary in `scheduling/forecast_receipts.py`; config, routes and the Decider switch;
the two attempt columns; one call in the plan serve; the sidecar's submit, draft and snapshot;
`learnloop ad`; the practice screen's tap and marker in new small components.

**Successor and switches.** None (AD1 is not a successor). `forecast_receipts`,
`outside_forecasters`, `rating_tap`, `feature_audit` (Decider switch `ad_feature_audit`), and the
master `enabled`. All false: no new rows, prompts byte-identical, no extra calls (G-AD1-5).

**Spend caps and model routes.** Feature audit on `ai.routing.tier1_decider` with its LLM
fallback; the outside forecasters on their own routes; all through the spend framework
(`--dry-run` on the backfill) inside `adaptive_difficulty.daily_spend_cap_usd`. Fakes only in
tests; no live call in this stage.

**`judgment_ledger` writes.** Task `ad_feature_audit`, version `ad-feature-audit-v1`.

**Tests.** G-AD1-1..11 written first (each run failing on the base, §3), plus the migration,
durability lane, FK check, table roles, head fixture, config snapshots, parameter registry, CLI
help, the switch-off byte-identity pins, and vitest for the tap and the marker.

## 1. What was built

### 1.1 Migration 213 (`migrations/213_adaptive_difficulty_receipts.sql`)

- `practice_attempts.difficulty_rating` (`easy` / `about_right` / `hard`) and
  `practice_attempts.first_hint_progress` (`no_draft` / `draft_started`): nullable, CHECKed,
  written only when set (`repositories._insert_practice_attempt`), so every earlier row and a
  database below 213 reads null.
- `item_serve_inputs` (RECEIPT, append-only by trigger): §7.5's frozen serve inputs, one row per
  presentation of a never-attempted item, keyed `plan_presentation:<id>` (CHECK: the row names its
  presentation).
- `ad_reading_opportunities` (RECEIPT, append-only by trigger): §5.11's receipt, one row per
  (opportunity, LO), `opportunity_key` UNIQUE (the cap slot) and (kind, subkind, source table,
  source id, LO) UNIQUE; `authority_class` CHECKed to `salience_only`; no magnitude column.
- `item_forecast_payloads` (WORKFLOW): raw requests and responses of the paid forecasters and the
  audit's LLM judge; pruned after `router.payload_retention_days` at each write.
- **No `item_forecasts` table.** Item forecasts are rows of kind `item_unassisted_success` in
  migration 206's `forecast_receipts` (orchestrator note 1; §2 deviation 1).
- `db/table_roles.py`: two RECEIPT tables and one WORKFLOW table (no DERIVED table, so no
  replayer). `fixtures/migration_head_212` → `migration_head_213` (git rename; a backup-API copy
  of the base's head with only 213 applied under `UPGRADE_SCRATCH_COPY`,
  `wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE`, header bytes 1/1,
  `integrity_check` ok, `foreign_key_check` empty, no companion files, copied into place with the
  backup API; README paragraph and chain) and every path naming it (29 test files, both reference
  scripts with `SCHEMA_HEAD = 213`, `docs/decider-tier1-migration.md`, the Database Catalog).
  The three earlier migrations' "nothing else changed" diffs on the way to head
  (`test_approach_maps_schema.py`, `test_help_assists_schema.py`,
  `test_library_asks_migration.py`) read `AD1_ADDED_OBJECTS` / `AD1_ALTERED_TABLES` from
  `tests/test_ad1_migration.py`; the head-number pins (4) moved to 213.

### 1.2 The receipt family (`scheduling/forecast_receipts.py`)

`ITEM_UNASSISTED_SUCCESS` joins `FORECAST_KINDS`; decision kinds `serve` and `item_prepare`;
binding `first_presentation` (an item-scoped forecast is scored against its revision's first
bound presentation); `valid_for_serve(receipt, served_at)` is §8.1's validity rule
(`inputs_as_of <= served_at`, whenever the receipt arrived). AD's receipts are written through
the family's own `record_receipts` (a savepoint of the caller's transaction, never raising),
gated by `adaptive_difficulty.forecast_receipts`, not by `diagnosis.forecast_receipts`.

### 1.3 The serve hook (`adaptive_difficulty/serve.py`; one call in `daily_plan/engine._serve`)

In the transaction that writes the `plan_presentations` row, right after it, one savepoint:
(1) the reading sweep up to the serve; (2) for a never-attempted item, its `item_serve_inputs`
row (`serve_inputs.py`): the served revision's hash (the `practice_item_snapshots` serialization,
written INSERT OR IGNORE), the stamped `p1_launch@1` tuple, per audited dimension the canonical
audit answered before the serve (id, value, judge) or null, the resolved tuple, the signal
vector `z_llm` / `z_panel` / `z_v1` / `z_origin` with value, availability, receipt id and receipt
time (`z_v1` only from an `llm_v1:item` receipt that existed when the serve wrote the row,
recalibrated by the logit-intercept MAP fit on past items only, `z_v1_logit_intercept_map_n01_v1`),
`pre_exposed` (the serve-eligibility reveal sum before the serve reaching the auto-prime
threshold) and `ad_feature_resolution_v1`; (3) the in-process forecasts (`forecasters.py`):
`mastery_ekf` (placement's live incumbent over the persisted per-LO posterior) and
`lo_general+composite` (field's pure EKF with every extension, fitted on the attempt rows
completed no later than the serve), as presentation-scoped receipts with `inputs_as_of` = the
serve. A failure rolls back AD's writes alone, logged; the serve proceeds. A reopened step writes
nothing new. A protected item (held-out material or an exam reservation, `protection.py`) gets
neither inputs nor forecasts.

### 1.4 Reading opportunities (`adaptive_difficulty/reading.py`)

`SOURCES` is the one allowlist (the AD2+AD3 stage moves it into the firewall module): a section
completed (`section_read`), a span view in a learner-facing context unless the span is a worked
example (`passage_viewed`), an answered reader or library tutor question, a worked example
shown or in a completed section, an answered quick check of style `recall` / `next_step` /
`why_step` / `assumptions`, an owner-placed reading question's `reader_answer_submitted`, and
D22's first self-check verdict (`self_check:matched` / `self_check:missed`). Caps: a section
once per section and LO, passage views one per LO per day, tutor exchanges three per LO per day,
a worked example once, a question once. Doses: a named facet dose 1; otherwise dose 1 spread
over the LO's facets (blueprint union, else its active items' facets). Each query selects ids,
keys and write times only. Source times are normalized (`…ssssssZ`) so replay orders by them.
The LO mapping is the Reader's (`learning_objects_for_section` / `_span`); worked examples by
role (`source_retrieval.corpus.role_keys`); held-out material is withheld (fail closed). A serve's
sweep reads from one hour before the newest recorded source time and never re-maps a recorded
source; the backfill reads the whole history. Nothing reads the receipt (A12; the firewall
module is unchanged).

### 1.5 The feature audit (`adaptive_difficulty/feature_audit.py`)

One Decider request (`tier1_decider`, `decider_judgments.ask_decider`) with one typed choice per
audited dimension (`complexity` 0-4, `transfer`, `scaffolding`, `span`, `response`), reading
the stem and reference answer only; argmax, a tie is no answer; one `judgment_ledger` row per
dimension (task `ad_feature_audit`, version `ad-feature-audit-v1`, left
`practice_item_revision` / the revision hash, right `dimension` / its name, the distribution in
the rationale). A dimension the Decider leaves unanswered (tied, unavailable, refused, failed)
goes to the LLM judge on `ai.routing.ad_feature_audit` (one structured call for the remaining
dimensions), ledgered as judge `llm` with the Decider's verdict and row id. `[decider_routes]
ad_feature_audit = false` audits with the LLM only. The canonical audit is the earliest
answered row per dimension; a later run asks only unanswered dimensions. The audited revision is
written to `practice_item_snapshots`.

### 1.6 Outside forecasters and background jobs (`outside.py`, `background.py`, `spend.py`)

`llm_v1:item` (item stem, topic and skill names, capability, practice mode; never the reference
answer, rubric, hints or the `difficulty` label), once per item revision, scope `item`.
`llm_v3:llm` (structured `p_correct`) and `llm_v3:decider` (`noul` "will_pass"), per plan
presentation, on the V1 view plus a card of the learner's graded attempts on the LO and its
prerequisites completed before the serve (result category, hints, answer shown, the question,
days before; never answer text; protected items never shown) and the incumbent's numbers frozen
at the serve. Each receipt is written once when the answer arrives (`created_at` = issued,
`received_at` = arrived, `inputs_as_of` = the serve for `llm_v3`, the preparation time for
`llm_v1`; `status` ok / failed / refused_spend; a failure or refusal gets a suffixed key, so a
later run can still succeed). Raw request and response to `item_forecast_payloads`.
Routes `ai.routing.ad_forecast_llm` (empty: the active provider, Codex `estimated_only`) and
`ai.routing.ad_forecast_decider` (decider-only). Spend: `PaidCalls` / `ask_decider` inside the
`adaptive_difficulty.daily_spend_cap_usd` shared daily envelope (owner kinds
`ad_item_forecast`, `ad_feature_audit`); a metered LLM route needs
`adaptive_difficulty.price_per_million` or is refused before sending.
Background: after `next_plan_item` (serve) and `plan_learner_pick`, the presentation's `llm_v3`
forecasts; after a plan read or serve, the plan's unresolved items are prepared for the pool
(audit, then `llm_v1:item`, at most 20 a job, a revision prepared to the end is not scheduled
again in the process). Jobs run in the sidecar's `BackgroundBuilds` registry (`ctx.map_builds`),
check their fence before each write step, never on a request path. `LEARNLOOP_AD_MODELS=off`
(set in `tests/conftest.py`) starts nothing without an injected client.

### 1.7 The rating tap and the first-hint marker

Sidecar: `submit_attempt` / `submit_dont_know` accept `difficultyRating` and
`firstHintProgress` (Literal vocabularies); `AttemptDraft` carries them; `attempts.py` stores the
rating only with `rating_tap` on and the marker only with `forecast_receipts` on and a hint used
(read from config: the attempt path imports nothing of AD's). `save_practice_draft` keeps the
marker in the checkpoint's practice envelope under the draft's retry key (a save without it
keeps it, another retry key never inherits it, nothing kept with `forecast_receipts` off), and
`checkpoint_dto` returns it only for its own retry key. `config_dto` gains
`adaptive_difficulty: {rating_tap, first_hint_progress}` only while one is on.
Frontend (new small files): `screens/practice/DifficultyRatingTap.tsx` ("Felt: easy · about
right · hard" beside Submit in both card layouts, unselected, a second tap retracts, locked once
Submit is pressed, hidden for the session with one tap in browser storage, try/catch) and
`screens/practice/useFirstHintProgress.ts` (set once at the first hint seen: an authored reveal,
the H2b panel's authored offer, or a hint the panel delivered); narrow call sites in
`PracticeScreen.tsx` (state, two submit payloads, the draft mirror and save, the reveal
functions, one effect on the panel's delivered count, the two render sites), `App.tsx` (one
prop), `practiceDraft.ts`, `algoConfig.ts`, the DTOs and client. `screens/practice/
useAdaptiveHints.ts`, `HintPanel.tsx`, `learnloop/hints/`, `attempts/hint_fold.py`,
`help_assists` and the workbench handlers are untouched.

### 1.8 Owner commands (`learnloop ad`)

`learnloop ad data-check --vault <copy>`: read-only (no migration, no model): the §3.3 tables
(items by `difficulty_source`, items with features, graded attempts, attempted once / twice,
full-credit share, the first unassisted unprimed attempt against the label with Spearman's rho
and a Fisher-z interval overall, within capability and per capability), first-surface attempts
per (facet, capability) cell, coverage of latency, confidence, hints, priming, the rating and the
marker, exam-material assessment items with and without a facet mapping (held-out apart, Q3),
historical attempts by revision status, and the AD1 receipt counts.
`learnloop ad backfill --vault <copy> [--audit] [--llm-v1] [--reading] [--limit N] --dry-run`:
the plan and estimate, nothing written; without `--dry-run` the audit of every active item's
revision and every other revision held in `practice_item_snapshots`, the one-time `llm_v1:item`
of never-attempted items, and the reading history sweep.

### 1.9 Config, disclosures, references

`[adaptive_difficulty]` (`enabled`, `forecast_receipts`, `outside_forecasters` (a list; true /
false accepted), `rating_tap`, `feature_audit` all on; `daily_spend_cap_usd = 0.50`;
`price_per_million` unset), `[decider_routes] ad_feature_audit = true`, routes
`ad_forecast_llm`, `ad_forecast_decider` (decider task), `ad_feature_audit`. All 19
`DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries recomputed (each moves only because the effective config
gains the keys; the template `.pyc` cleared). `parameter_registry`: `daily_spend_cap_usd`
structural / operational (`price_per_million` defaults unset and is not an audited leaf, as
`hints.price_per_million`). `ai/disclosures.py`: the three routes with their consumers
(`adaptive_difficulty`, `ad_feature_audit`) and the Tier-1 text naming the audit;
`decider_judgments.connection_note` names the two new things the Decider is asked (how earlier
answers on a topic went; how a practice question is built) while on. `cli/probability_arms`
reports the consumers' status. Import-linter: new contract
`adaptive-difficulty-never-writes-evidence` (27 contracts). DB references regenerated and
validated (head 213, 333 table notes, 908 config leaves, 0 errors; vault validation passed).

## 2. Deviations (each recorded)

1. **Item forecasts are `forecast_receipts` rows**, not an `item_forecasts` table (orchestrator
   note 1); the spec's §8.1, §11.2 and §14 AD1 builds bullet are amended to say so.
2. **Serve-time receipts at plan presentations only.** The daily plan is the serving path (it is
   live from `mvp-0.14`); probe presentations and Today-queue serves bound only by a scheduler
   candidate get no `item_serve_inputs` or in-process receipts in AD1, and resolve as historical
   attempts (§7.5). [Open question 3.]
3. **AD1's own forecaster states**, not field's `StateRenderer`: the field renderer is keyed to a
   completed attempt's cutoff; a serve-time forecast has no attempt yet. State version
   `ad-forecast-state-v1`; the V3 card is smaller than field's (no answer excerpts, hypotheses or
   tutor questions).
4. **Separate routes** for the outside forecasters (`ad_forecast_llm`, `ad_forecast_decider`)
   instead of `llm_probability_*`, so their disclosure and consumer are AD's (the field routes
   stay offline-only) and the owner can route them alone; and a new chat route
   `ad_feature_audit` for the audit's LLM judge (the spec names "the existing LLM fallback"; no
   audit LLM existed).
5. **Outside forecasters need `forecast_receipts` on** (they write receipts).
6. **The marker is stored only when the attempt used a hint** (`hints_used > 0`).
7. **D22's verdict row is the question's first verdict whatever its response** (the ledger keys a
   rewritten answer as a new question; the spec says a question counts once).
8. **An owner-placed reading question's LO is its practice item's LO** (it is administered from an
   item; the spec names the question's section or anchor span, which the administration lacks).
9. **The first serve's sweep with an empty receipt covers the whole history** (no watermark yet);
   the backfill is then a no-op. A serve's overlap window is one hour.
10. **Held-out material is withheld from the reading sweep** (A8; not in the spec's G-AD1-11 list,
    added as the conservative option).

## 3. Fail-first

The 25 server-side gate tests (`tests/test_adaptive_difficulty_ad1.py` 13,
`test_ad1_attempt_columns.py` 6, `test_ad1_reading_opportunities.py` 6) were run against the base
tree (`git archive 16a0071f2` with the new test files, in its own rootdir): **25 failed**, each
for its stated reason: `No module named 'learnloop.adaptive_difficulty'` (19),
`cannot import name 'valid_for_serve'` (3), `SubmitAttemptInput` / `PracticeDraftCheckpoint`
refusing the new fields (`extra_forbidden`, 3), `AttemptDraft` has no `difficulty_rating`,
no `difficulty_rating` column, no `adaptiveDifficulty` snapshot key, no `item_serve_inputs` table.

## 4. Gate (this step; owner rule 2026-10-17: no full suite here)

- `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2`; TMPDIR = `fixtures-local/tmp`.
- `uv run lint-imports --no-cache`: **27 kept, 0 broken** (26 + the new AD contract).
- Targeted pytest, `-n auto`, file lists in `fixtures-local/tmp/` (see §8 for the files): the
  AD1 files (38 tests: gate 25, migration 5, spend/background/CLI 8), then the files that
  exercise a changed module or pin what changed: 2118 passed (plan serves, drafts, receipts,
  config DTO, Decider, judge routes; 65 files) and 1041 passed (daily plan, attempts, sidecar,
  sessions, routing, config, registry, field, placement, router, hints, mobile, CLI, settings;
  123 files); the head-fixture files and contracts (554 tests) were green after the sibling
  updates; final union run after the last change: **3657 passed** (§9).
- Durability lane: `-m durability` on `test_ad1_migration.py` and the three sibling migration
  files: 4 passed.
- Frontend: `npm install`; `npm run typecheck` clean; vitest
  `src/screens/practice/DifficultyRatingTap.test.tsx` (4), `src/screens/PracticeScreen.adaptiveDifficulty.test.tsx` (8),
  `src/screens/PracticeScreen*` and `src/screens/practice/*` (13 files, 122 tests), `src/app` and
  `src/copy` (15 files, 120 tests, incl. `practiceDraft.test.ts` 6): all passed;
  `npm run frontend:build` ok. No `src-tauri` change (no cargo check needed).
- References: `db_generate_reference.py` then `db_validate_reference.py`: 0 errors;
  `validate_vault.py` passed. (`desktop_validate.py` fails on the pre-existing
  `components/pdfSelection/testing/syntheticBook.ts`, not AD1's; AD1's new frontend files are
  reachable from `main.tsx`.)
- `git diff --check` clean.
- **Model calls: 0.** Every model-backed path is tested with fakes.

## 5. Files

New: `migrations/213_adaptive_difficulty_receipts.sql`; `src/learnloop/adaptive_difficulty/`
(`__init__`, `switches`, `protection`, `spend`, `feature_audit`, `serve_inputs`, `forecasters`,
`serve`, `reading`, `outside`, `background`, `backfill`, `data_check`);
`src/learnloop/db/stores/ad_receipts.py`; `src/learnloop/cli/ad.py`;
`apps/learnloop-tauri/src/screens/practice/DifficultyRatingTap.tsx`, `useFirstHintProgress.ts`;
tests `tests/ad_fakes.py`, `test_adaptive_difficulty_ad1.py`, `test_ad1_attempt_columns.py`,
`test_ad1_reading_opportunities.py`, `test_ad1_migration.py`, `test_ad1_outside_and_cli.py`;
vitest `DifficultyRatingTap.test.tsx`, `PracticeScreen.adaptiveDifficulty.test.tsx`; the
reference notes for the three tables and the config section.
Changed: `config/schema.py`, `config/template.py`, `ai/routing.py`, `ai/disclosures.py`,
`decider_judgments.py`, `scheduling/forecast_receipts.py`, `attempts/attempts.py`,
`db/repositories.py`, `db/table_roles.py`, `daily_plan/engine.py`,
`params/parameter_registry.py`, `cli/__init__.py`, `cli/probability_arms.py`,
`learnloop_sidecar/context.py`, `handlers/practice.py`, `handlers/sessions.py`,
`handlers/daily_plan.py`; frontend `PracticeScreen.tsx`, `App.tsx`, `algoConfig.ts`,
`practiceDraft.ts` (+ test), `api/dto.ts`, `api/client.ts`; `pyproject.toml` (contract);
`tests/conftest.py`, `test_architecture.py`, `test_judge_routes.py`, `test_decider_landing.py`,
the three sibling migration tests and `test_route_rules_in_grader.py`,
`cli_help_snapshot.json`; the head fixture rename and its paths; the spec (§8.1, §11.2, §14);
the regenerated references.

## 6. Owner-run commands (on a backup copy; dry-run first; never on the working vaults)

```bash
# 1. a backup-API copy of the vault
uv run python -c "from pathlib import Path; from learnloop.db.copies import copy_tree_with_databases as c; c(Path('fixtures/linear_algebra'), Path('fixtures-local/la_ad1'))"
# 2. the data check (read-only, no model; answers Q1 and Q3 on current data)
uv run learnloop ad data-check --vault fixtures-local/la_ad1
# 3. the backfills: plan first, then run (Decider on OpenRouter for the audit; Codex for llm_v1)
uv run learnloop ad backfill --vault fixtures-local/la_ad1 --audit --llm-v1 --reading --dry-run
uv run learnloop ad backfill --vault fixtures-local/la_ad1 --reading
uv run learnloop ad backfill --vault fixtures-local/la_ad1 --audit --limit 20
uv run learnloop ad backfill --vault fixtures-local/la_ad1 --llm-v1 --limit 20
```

Run on the live vaults only when the owner decides; the daily cap
(`adaptive_difficulty.daily_spend_cap_usd`, $0.50) bounds metered spend; Codex is
`estimated_only`.

Smoke run in this stage (no model call): a backup-API copy of the worktree's tracked
`fixtures/linear_algebra` (the committed snapshot) in `fixtures-local/`, every model route off,
API-key variables unset, empty HOME / CODEX_HOME / LEARNLOOP_CONFIG_DIR, `LEARNLOOP_AD_MODELS=off`:
upgraded to 213 by the coordinator; five synthetic plan presentations recorded in 0.24 s (the
first, sweeping 81 reading opportunities from the history), then 0.07, 0.08, 0.07 and 0.03 s
(a protected item: nothing written); `data-check` reproduces §3.3 on that snapshot (n = 54,
rho = -0.566, interval -0.72 to -0.35; within capability -0.35; 74.2% full credit). Copy removed.

## 7. Open questions (default taken in brackets)

1. **Outside forecasters on by default (§11.4, D4)** means live background calls once AD1 lands:
   `llm_v1:item` once per new item revision and `llm_v3:llm` once per served plan item on Codex
   (subscription, `estimated_only`), and `llm_v3:decider` once per served plan item on the
   Decider through OpenRouter (about $0.0004 a call, inside the $0.50 day cap), sending the
   learner's recent results on the topic (never answer text). [On, as the spec states; set
   `outside_forecasters = []` to stop them.]
2. **The feature audit on by default**: one Decider request (five questions) per new item
   revision of the plan's pool, LLM fallback on Codex. [On, as the spec states.]
3. **Probe presentations and Today-queue serves** have no serve-time receipts in AD1. [Plan
   presentations only; AD2 adds them where it draws.]
4. **The `llm_v3` card** is minimal (results, hints, the question; no answer text, hypotheses or
   tutor questions). [Minimal: less learner text leaves; field V3's richer card is the harness's.]
5. **Item preparation trigger**: the plan's unresolved items at each plan read or serve, not the
   authoring and import paths. [Plan pool; the backfill covers the rest.]
6. **Workbench submits** send neither the tap nor the marker. [Null, read as unknown.]
7. **The rating on diagnostic checks**: shown (optional, logged only). [Shown.]
8. **D22's verdict across a rewritten answer**: the first verdict of the question. [First.]

## 8. Friction notes for AD2+AD3 and AD4

- AD2's replayer reads `item_serve_inputs` (the frozen tuple and `z_i`) and `forecast_receipts`
  kind `item_unassisted_success`; `valid_for_serve` is the validity rule; an item-scoped receipt
  has binding `first_presentation` and `item_content_hash`.
- `reading.SOURCES` is the carve-out's allowlist to move into `attempts/salience_firewall.py`
  (G-AD3-13); `reading.ad_reading_opportunities` rows order by `source_written_at` (normalized).
- Audit values are strings (`complexity` "0"-"4"); `serve_inputs.feature_inputs` converts
  `complexity` to an int in the resolved tuple.
- `feature_audit.item_revision` mirrors the scheduler's snapshot serialization (pinned equal by
  `test_a_served_revision_hashes_as_the_scheduler_snapshots_it`).
- `lo_general+composite` re-fits the whole history at each serve (about 70 ms on a 70-attempt
  vault); AD2's own replayer should cache its state across serves.
- AD4 reads the canonical audit (`canonical_audits(connection, hash)`) and the snapshot rows the
  audit and the serve write.

## 9. Final targeted run

After the last code change: the union of every file above, **3657 passed** (`-n auto`,
10 min 16 s), and the durability lane on the four migration files, **4 passed**. The 222 files
(the AD1 files, every file that greps for a changed module, function or table, and the contract
files):

```text
tests/test_ad1_attempt_columns.py
tests/test_ad1_migration.py
tests/test_ad1_outside_and_cli.py
tests/test_ad1_reading_opportunities.py
tests/test_adaptive_difficulty_ad1.py
tests/test_ai_config.py
tests/test_answer_calibration_duel.py
tests/test_approach_maps_schema.py
tests/test_architecture.py
tests/test_attempt_ai_flow.py
tests/test_attempt_completion.py
tests/test_attempts.py
tests/test_attempt_write_order.py
tests/test_chatgpt_plan_landing.py
tests/test_chatgpt_plan_workspace.py
tests/test_cli_attempt.py
tests/test_cli_commands.py
tests/test_cli_entrypoint.py
tests/test_cli_fit.py
tests/test_cli_generate_practice.py
tests/test_cli_help_snapshot.py
tests/test_cli_ingest.py
tests/test_cli_json.py
tests/test_cli_observations.py
tests/test_cli_propose.py
tests/test_collection_dataset.py
tests/test_config_refactor.py
tests/test_coordinated_migrations.py
tests/test_daily_plan_admission.py
tests/test_daily_plan_build.py
tests/test_daily_plan_composition.py
tests/test_daily_plan_kill_switch.py
tests/test_daily_plan_owner_decisions.py
tests/test_daily_plan_reading.py
tests/test_daily_plan_reentry.py
tests/test_daily_plan_replay.py
tests/test_daily_plan_review_regressions.py
tests/test_daily_plan_rpc.py
tests/test_daily_plan_split.py
tests/test_decider_agreement.py
tests/test_decider_client.py
tests/test_decider_landing.py
tests/test_desktop_rpc_contract.py
tests/test_diagnosis_replay.py
tests/test_evidence_config.py
tests/test_evsi_staged_binding.py
tests/test_exam_protection_review.py
tests/test_facet_identity_composition.py
tests/test_facet_outcome_view.py
tests/test_facet_reword_confirm.py
tests/test_facet_span_support.py
tests/test_field_boundaries.py
tests/test_field_cli.py
tests/test_field_config.py
tests/test_field_priors.py
tests/test_field_signal_production_paths.py
tests/test_field_split_outcomes.py
tests/test_forecast_ledger.py
tests/test_forecast_receipts_landing.py
tests/test_forecast_receipts.py
tests/test_help_assists_schema.py
tests/test_hint_authored_reveal_ruling.py
tests/test_hint_blind.py
tests/test_hint_contracts.py
tests/test_hint_discriminating.py
tests/test_hint_evidence.py
tests/test_hint_feedback_texts.py
tests/test_hint_feedback_widening.py
tests/test_hint_h2a_review.py
tests/test_hint_h2a_review_round2.py
tests/test_hint_h2a_review_round3.py
tests/test_hint_h2a_review_round4.py
tests/test_hint_h2b_fix3.py
tests/test_hint_h2b_rereview.py
tests/test_hint_h2b_review.py
tests/test_hint_kill_switch.py
tests/test_hint_outcome.py
tests/test_hint_replies.py
tests/test_hint_report.py
tests/test_hint_service.py
tests/test_hint_telemetry.py
tests/test_judge_routes.py
tests/test_learner_pick_proposal.py
tests/test_library_asks_migration.py
tests/test_method_explicit_landing.py
tests/test_method_explicit_upgrade.py
tests/test_migrations.py
tests/test_mobile_allowlist.py
tests/test_mobile_capture.py
tests/test_mobile_doctor.py
tests/test_mobile_host_auth.py
tests/test_mobile_host_coexistence.py
tests/test_mobile_pairing.py
tests/test_mobile_shortcuts.py
tests/test_mvp010_upgrade.py
tests/test_mvp011_upgrade.py
tests/test_mvp013_upgrade.py
tests/test_mvp014_upgrade.py
tests/test_mvp015_upgrade.py
tests/test_mvp016_upgrade.py
tests/test_mvp017_upgrade.py
tests/test_mvp018_upgrade.py
tests/test_mvp020_upgrade.py
tests/test_mvp021_upgrade.py
tests/test_mvp022_upgrade.py
tests/test_mvp023_upgrade.py
tests/test_mvp024_upgrade.py
tests/test_pfc_unverified_unassessed.py
tests/test_placement_diagnosis_decides.py
tests/test_placement_fixture_copies.py
tests/test_placement_opening_probes.py
tests/test_placement_report.py
tests/test_placement_sidecar.py
tests/test_placement_signals.py
tests/test_placement_split_grades.py
tests/test_plan_determinism_landing.py
tests/test_plan_determinism.py
tests/test_practice_availability.py
tests/test_practice_index_adapters.py
tests/test_practice_index_admission.py
tests/test_practice_index_dossiers.py
tests/test_practice_index_evaluation.py
tests/test_practice_index_find.py
tests/test_practice_index_paid.py
tests/test_practice_index_text.py
tests/test_practice_information.py
tests/test_practice_item_quality_gates.py
tests/test_practice_leakage.py
tests/test_practice_proposal_caller_columns.py
tests/test_probability_prep.py
tests/test_reader_dialogue.py
tests/test_reader_intent.py
tests/test_reader_progression.py
tests/test_reader_quick_check.py
tests/test_reader_recap.py
tests/test_reader_recap_review.py
tests/test_reader_rw3a_landing.py
tests/test_reader_workbench_rw2a.py
tests/test_reader_wrap_up.py
tests/test_reading_step_switch.py
tests/test_rebuild_orchestrator.py
tests/test_recurrence_commands.py
tests/test_registry_audit.py
tests/test_regrade_contract_upgrade.py
tests/test_required_method_round3_final_verify.py
tests/test_required_method_round3.py
tests/test_required_method_round3_review.py
tests/test_router_card.py
tests/test_router_coldness_covariates.py
tests/test_router_g1_feasibility.py
tests/test_router_g3_propensity.py
tests/test_router_g4_restraint.py
tests/test_router_g7_fallback.py
tests/test_router_ladder_parity.py
tests/test_router_offer_log.py
tests/test_router_outcomes.py
tests/test_router_p2_bridge.py
tests/test_router_presentations.py
tests/test_router_probe_ties.py
tests/test_router_r1_composition.py
tests/test_router_r2a_landing.py
tests/test_router_r2a_serving.py
tests/test_router_r2b_agreement.py
tests/test_router_r2bc_landing.py
tests/test_router_r2b_requests.py
tests/test_router_r2b_serving.py
tests/test_router_r2c_retrieval.py
tests/test_router_r2c_teach_back.py
tests/test_router_staged_p2.py
tests/test_route_rules_in_grader.py
tests/test_router_why_copy.py
tests/test_salience_firewall.py
tests/test_serve_eligibility.py
tests/test_serve_eligibility_review.py
tests/test_session_attempt_attribution.py
tests/test_settings_sidecar.py
tests/test_settings_store.py
tests/test_shadow_rebuild.py
tests/test_sidecar_adjudication.py
tests/test_sidecar_animation.py
tests/test_sidecar_append.py
tests/test_sidecar_blueprint_picker.py
tests/test_sidecar_contract.py
tests/test_sidecar_diagnostic.py
tests/test_sidecar_epigraphs.py
tests/test_sidecar_exams.py
tests/test_sidecar_goals.py
tests/test_sidecar_golden_path_assessment.py
tests/test_sidecar_golden_path.py
tests/test_sidecar_ingest_m3.py
tests/test_sidecar_item_authoring.py
tests/test_sidecar_item_presentation.py
tests/test_sidecar_knowledge_model.py
tests/test_sidecar_ladder.py
tests/test_sidecar_measurement.py
tests/test_sidecar_probe.py
tests/test_sidecar_queue_serialization.py
tests/test_sidecar_quick_add.py
tests/test_sidecar_reader_p3.py
tests/test_sidecar_reader_p3_slice2.py
tests/test_sidecar_reader_p3_slice3.py
tests/test_sidecar_reader_pdf_view.py
tests/test_sidecar_reader.py
tests/test_sidecar_registry.py
tests/test_sidecar_remediation_surfaces.py
tests/test_sidecar_serializer_snapshot.py
tests/test_sidecar_source_retrieval.py
tests/test_sidecar_span_view.py
tests/test_sidecar_synthesis.py
tests/test_sidecar_teach_back.py
tests/test_sidecar_trace_and_clarification.py
tests/test_sidecar_transport.py
tests/test_sidecar_tutor_qa.py
tests/test_sqlite_file_copies.py
tests/test_stuck_prompt.py
tests/test_success_head_cli.py
tests/test_table_roles.py
tests/test_tier1_decider.py
tests/test_tracked_fixture_databases.py
tests/test_ux_phase1_connect_ai.py
tests/test_ux_phase4_feedback.py
tests/test_ux_phase4_landing.py
```
