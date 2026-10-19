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
   **Owner decision 2026-10-18: outside forecasters (llm_v1:item, llm_v3:llm, llm_v3:decider) and
   the feature audit stay on by default (AD2 is next).**
2. **The feature audit on by default**: one Decider request (five questions) per new item
   revision of the plan's pool, LLM fallback on Codex. [On, as the spec states.] **Decided with
   question 1 (owner decision 2026-10-18): stays on.**
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

## Landing onto main

Landed in the `learnanything-merge2` worktree on branch `merge/ad1-onto-main`, cut from main at
`7d4c5f4ce` (the H2b landing). The stage tip is `9f2b3d4a1`, unchanged; its base was `16a0071f2`
(an H2b stage tip), so main's H2b fix rounds 3 and 4 came in with the merge. The last
orchestrator verify (Codex job `20261018-192812-YPRSS9`, after fix round 9) is clean, with one
Low open (below). Main was neither fast-forwarded nor pushed here. No gate fix was needed.

**Commits:**
- `e1bd8231b`: a `--no-ff` merge of `adaptive-difficulty/ad1` onto `7d4c5f4ce`.
- `00d6dc62e`: the references regenerated on the merged tree (commit labels only).
- This record, with the owner decision of 2026-10-18 (§7, questions 1 and 2).

### Merge

- **Conflicts: only the generated reference pages** (393 notes under
  `docs/learnloop-architecture-vault/Reference/`, all `source_commit` lines). Main's side was
  taken and the pages regenerated in the next commit.
- **Code merged without conflict.** `PracticeScreen.tsx` and `handlers/practice.py` were changed on
  both sides and merged automatically:
  - main's H2b behaviour is kept whole: the serialized answer box -> steps transitions (token,
    `stepsShown`, `handOffFailed(token, heldAt)`), `useAdaptiveHints`' `holdGeneration` /
    `resume(heldAt)`, and the fold's admission time (`_dataclass_replace(hint_fold,
    submitted_at=...)`, then `server_hint_fold` on the draft);
  - AD1's call sites sit beside them: the draft fields, the two submit payloads, the tap state, and
    the AD fields on `AttemptDraft` (set before the `replace`, which keeps them).
  - `hint_fold.py`, `outcome.py`, `help_assists.py` and `useAdaptiveHints.ts` are main's exactly
    (AD1 does not touch them).
- **The marker still sees H2b's deliveries.** `useFirstHintProgress` is marked by the effect on
  `adaptiveHints.entries.length`. Main's final `useAdaptiveHints` still returns `entries` (it
  added `holdGeneration` only), and the authored offer and reveals still go through
  `revealAuthoredHint` / `revealAuthoredAt`, which mark it. Vitest
  `PracticeScreen.adaptiveDifficulty.test.tsx` passes on the merged tree, inside the whole run.
- **`migration_head_212` is gone.** `fixtures/migration_head_213` is in rollback mode: header
  bytes 18-19 are 1/1, `journal_mode` is `delete`, the last `schema_migrations` row is 213, and
  there is no `-wal` or `-shm`. Nothing in `tests/`, `scripts/`, `src/`, `apps/` or the reference
  scripts names `migration_head_212`, including main's later H2b tests (`test_hint_h2b_fix3`/`fix4`
  do not name a head fixture). The name survives only in history text: this review, the Codex
  review, `adaptive-hints-H2b.md` and the head fixture's README chain. The Catalog's line is
  regenerated.
- **`apps/` changed** (13 files), **`src-tauri` did not**, so no `cargo check`.
- **No algorithm successor.** The vaults keep their label.

### Regenerated

- **References.** `db_generate_reference.py`, then `db_validate_reference.py`: **0 errors**,
  `schema_head` 213, 333 table notes. Against the stage tip, only `source_commit` lines differ
  (397 notes).
- **Defaults snapshots.** Deleted the template `.pyc` and touched `template.py`. All 19
  `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries equal `defaults_fingerprint_for_version`: **0
  mismatches**.
- **CLI help snapshot.** `python tests/test_cli_help_snapshot.py --write`: no change.
- **RPC pins and the parameter registry.** `test_sidecar_serializer_snapshot.py`,
  `test_desktop_rpc_contract.py`, `test_mobile_allowlist.py`, `test_cli_help_snapshot.py`,
  `test_registry_audit.py`, `test_grading_cli.py` and `test_p0_cutover_mvp08.py`: **237 passed**,
  no file rewritten. AD1 adds no RPC. The new config keys are classified (`daily_spend_cap_usd`
  structural/operational).
- **`validate_vault.py`**: passes (1,129 notes; 1,127 of 1,127 reachable).
- **Known failures, from before this stage, not fixed:**
  - `desktop_validate.py` stops on `apps/learnloop-tauri/src/components/pdfSelection/testing/syntheticBook.ts`
    (an unclassified desktop source), as at the H2b landing;
  - `module_validate.py` reports **879** issues (844 at the H2b landing; the rise is AD1's new
    modules without module notes, e.g. `Reference/Modules/learnloop/adaptive_difficulty/*`).

### Gate

Python 3.12.14. `TMPDIR` was merge2's `fixtures-local/tmp`, and every command after the install ran
as `uv run --no-sync`. Both suite lanes ran under `flock /tmp/learnloop-fullsuite.lock`; the
RW2b+H3 worktree and its processes were not touched. Every test uses fakes. **This is the first
full run over the stage's code**: every stage step and fix rounds 1-9 ran targeted tests only
(owner rule 2026-10-17).

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `lint-imports --no-cache` | **27 kept**, 0 broken |
| full suite `pytest -n auto` on `00d6dc62e` | **13,738 passed, 2 xfailed, 0 failed** (15 min 18 s; `fixtures-local/ad1-landing-fullsuite.log`). The H2b landing ran 13,630 |
| `pytest -m durability` | **113 passed**, 13,627 deselected (3 min 35 s; `fixtures-local/ad1-landing-durability.log`) |
| `npm install`, `npm run typecheck` | ok, clean |
| `npm test` (the whole vitest run) | **134 files, 1,068 tests passed** on the first run (the `FeedbackScreen` load flake did not fire) |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check` | not needed (`src-tauri` unchanged) |
| thread, lock and timing tests | all passed on the first run, so no reruns were needed. The `"8841"` MCP flake did not fire |
| tracked fixtures, worktree | `git status` clean after both lanes and the frontend run, apart from this record |

### Parity (backup-API copies; no model call finished)

**Setup:**
- **Copies.** The owner's `fixtures/linear_algebra` and `fixtures/probability` (probability with
  its `.learnloop/state.sqlite`) were copied once with `copy_tree_with_databases` from the main
  checkout into `fixtures-local/landing-ad1/orig/`. Every other copy came from `orig/`, or from
  its upgraded copy `u27/`, through the same helper. `arxiv_v2` was not opened. Both vaults start
  at schema 165, label `mvp-0.8`, with **0** `model_call_receipts`.
- **Code.** Main's code is `git archive 7d4c5f4ce` and the merge's is `git archive 00d6dc62e`
  (`src`, `migrations`, `pyproject.toml`), each first on `sys.path`.
- **Environment.** Every run went through `env -i` with only `PATH`, `HOME`, `CODEX_HOME`,
  `LEARNLOOP_CONFIG_DIR`, `TMPDIR` and `LANG`. `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`
  were empty directories and still are. No `*_API_KEY`, `OPENROUTER*`, `OPENAI*`, `ANTHROPIC*` or
  `LEARNLOOP_AI_PROVIDER` variable was set.
- **Model routes, set before anything ran.** H2b's `neutralize3.py`, run under each code (54 tasks
  on main, 57 on the merge), sent every field of that code's `AIRoutingConfig` to `127.0.0.1:9`:
  - chat routes to `blackhole` (`openai_chat` at `http://127.0.0.1:9/v1`), including
    `ad_forecast_llm`, `ad_feature_audit`, `hint_writer`, `approach_map`, `hint_outcome` and the
    workbench routes;
  - decider-only routes to `blackhole_decider` (`127.0.0.1:9`), including `ad_forecast_decider`,
    `tier1_decider` (the audit's Decider) and `hint_chooser`;
  - `ai.active_provider` to `blackhole`, the fallback cleared;
  - `query_rewrite`, `tutor_query_rewrite`, `tutor_rerank`, `dense` and `[embedding]` off;
  - `[learner_text_gaps] enabled = false`;
  - `[hints.maps] build_on_serve = false` and `[hints] outcome_placement_enabled = false` on every
    copy.
  - A copy upgraded by main's code got the three AD routes added before the merge's code opened
    it.
  - A resolver check over every `AITask` found nothing outside those two profiles except
    `embedding` (disabled, keyless).
- **The profiles' key variable.** It is `LL_LANDING_NO_KEY`. It is unset in every run except
  `cik`/`ciik`/`ciiik` and `fk`. There it is set to the dummy `landing-dummy`, so that AD's
  requests reach the loopback instead of stopping at "no client". The endpoint is still
  `127.0.0.1:9`, where nothing listens.
- `LEARNLOOP_AD_MODELS` was unset everywhere except the in-process daily-plan dumps of (b). There
  it was `off`, so that no background thread outlives the dump.

**(a) Migration 213, and (b) nothing served changes**

| Check | linear_algebra | probability |
|---|---|---|
| **(a)** open (migrate): main's code / the merge's | 165 → 212 (47) / 165 → 213 (48) | the same |
| schema, main@212 vs merge@213 | **19 objects only on the merge, exactly the stage's**: tables `item_serve_inputs`, `ad_reading_opportunities`, `item_forecast_payloads`; indexes `idx_item_serve_inputs_item`, `_plan`, `idx_ad_reading_opportunities_lo`, `_written`, `idx_item_forecast_payloads_created`, plus 7 autoindexes; triggers `item_serve_inputs_no_update`/`_no_delete`, `ad_reading_opportunities_no_update`/`_no_delete`. **Two tables' SQL differs**: `practice_attempts` gains `difficulty_rating TEXT CHECK (… IN ('easy','about_right','hard'))` and `first_hint_progress TEXT CHECK (… IN ('no_draft','draft_started'))`; `question_events` gains `answered_at TEXT` and `answer_mode TEXT CHECK (… IN ('answer_directly','help_me_reason','ask_me_first'))`. Nothing only on main | the same (1,394 → 1,413 objects; LA 1,395 → 1,414) |
| rows of every pre-existing table (335), on main's columns | **identical** (16,538 rows); the four new columns NULL on every row; the three new tables empty. `schema_migrations`: the merge has 213 extra; the common rows differ only in `applied_at` (the open's time) | **identical** (7,636 rows; the same) |
| `foreign_key_check` / `integrity_check`, both sides | 0 / ok | 0 / ok |
| `rebuild --shadow --json`, main@212 vs merge@213 | **0 differences** after normalisation (raw: the marker id and the database hashes); facet 0, mastery 2, schedule 8; live database unchanged on both | **0 differences** (facet 0, mastery 1, schedule 1) |
| `doctor --json`, main vs merge | **0 differences** (raw: the copy paths); 57 issues, 1 error | **0 differences**; 101 issues, 48 errors |
| **(b)** at `mvp-0.8`: certification, recipe gaps and curves (`cert_dump`); the Today queue at a frozen clock (2026-10-18 09:00 UTC; no session, a session, greedy) | **byte-identical** (39 facets, 84 points, 2 corrections; 21 LOs, 1 certified; queue 41) | **byte-identical** (29 facets, 2 points; 18 LOs; queue 67) |
| the daily plan at `mvp-0.8` (in process, the sidecar's handlers, frozen clock, a fixed session: read, serve, serve again, read; then the plan tables, `plan_presentations` and the `plan_block` decisions, ULIDs mapped to their order) | **byte-identical** (the plan is off below `mvp-0.14`) | **byte-identical** |
| upgraded by main's code to `mvp-0.27` (`--to mvp-0.9`, `--to mvp-0.27`, `rebuild-derived-state` twice), then opened by each code (main: nothing; merge: 213, AD at its defaults) | certification and curves **byte-identical** (82 points, 7 corrections); Today queue **byte-identical** (43) | **byte-identical** (queue 67) |
| the daily plan at `mvp-0.27` | the read, both serves, the second read, `daily_plans`, the blocks, `plan_presentations` (1, `pi_orient_operations_omission_rewrite`) and the decision rows are **identical**, except `router_decisions.card_hash` / `snapshot_hash` and the card hash in `detail_json`. **These hash the card, which carries the plan's ULID**: a second run of main's code differs from the first in exactly these three, and nothing else differs once they are set aside. The stored cards differ only in `session.plan_id` | the same (`pi_three_independent_birthd`) |

The merge's serve at `mvp-0.27` wrote AD's rows and nothing that is served:
- the two in-process receipts (`mastery_ekf`, `lo_general+composite`, `presentation`, ok);
- one frozen `llm_v3` state payload;
- the first serve's history sweep (deviation 9): 81 reading opportunities on LA and 182 on
  probability;
- **no `item_serve_inputs` row**: the item served on each vault has earlier attempts (1 and 2), and
  the row is written only for a never-attempted item (§1.3).

**(c) Practice through the real sidecar** (stdio). The copies are of probability at `mvp-0.27`
(`u27/`), so that the daily plan serves. The sequence:
- `initialize`, `get_config`, `set_grading_provider manual`, `start_session`;
- **the daily-plan serve**: `get_daily_plan`, then `next_plan_item` with `serve` true (it serves
  `pi_three_independent_birthd`), then a 12 s wait for AD's background jobs;
- H2b's sequence on `pi_prob_derive_complement`: `get_practice_item`, `get_probe_contract`,
  `practice.record_hint_reveal` (authored hint 0), `save_practice_draft`, `submit_attempt` (with
  self-grade and the `submissionId`), `acknowledge_practice_submission`;
- `submit_dont_know` on `pi_incl_derive_intersections` (another LO), then acknowledge;
- a hint-free workbench open, get and submit on `pi_story_binomial_translation` (a third LO);
- `get_session`, `shutdown`.

The runs:
- (i) main;
- (ii) the merge with the four switches false (`forecast_receipts = false`,
  `outside_forecasters = []`, `rating_tap = false`, `feature_audit = false`);
- (iii) the merge at the defaults.

Each ran twice: once with the key variable unset (`ci`/`cii`/`ciii`, plus `ci2`, a second main
run as the baseline), and once with it set (`cik`/`ciik`/`ciiik`).

| Check | Result |
|---|---|
| every response (21 calls), (i) vs (ii) vs (iii), both sets | **identical** after H2b's normalisation: ULIDs, timestamps, the copy path, and `initialize`'s two schema-head fields (212 against 213). There is **one difference, in (iii) only**: `get_config` carries `adaptiveDifficulty: {firstHintProgress: true, ratingTap: true}`, the app snapshot's key. In (ii), `get_config` is raw-identical to main's |
| the database delta on main's columns | (ii) differs from (i) in exactly the tables where `ci2` (main again) differs from `ci`: `attention_block_events` (the router card hash, as in (b)) and `attempt_debug_payloads` / `scheduler_explanations` / `scheduler_slate_candidates` (wall-clock floats such as `forgetting_risk` in the 7th decimal). (iii) adds AD's tables only (below) |
| (ii): the new tables and columns | the three new tables **empty**; `difficulty_rating`, `first_hint_progress`, `answered_at` and `answer_mode` **NULL on every row**; 0 AD forecast receipts, 0 `ad_feature_audit` ledger rows, 0 claims, 0 receipts |
| the attempts, all seven runs | **identical** evidence fields. The `open_text` attempt has `hints_used` 1, `primed` 0, correctness 1.0. The `dont_know` is recorded as stuck (`open_text`, `declared_stuck` 1, scored 0, as at `mvp-0.13`+), with `hints_used` 0. The workbench attempt (`desktop_practice_workbench`) has `hints_used` 0, `primed` 0. There are 0 `reveal_events` rows. One `help_assists` row (the client-counted authored reveal, level 3, attached to the first attempt). The AD columns are NULL (nothing was tapped) |

**(iii): every AD row written** (`ciiik`, the key variable set):
- `ad_reading_opportunities` **182**, all from the serve's sweep (history):
  - `worked_example:in_completed_section` 107;
  - `in_passage_question:recall` 25;
  - `reading:section_read` 25;
  - `reader_tutor_exchange` 15;
  - `reading:passage_viewed` 10.
- `item_serve_inputs` **0** (the served item has 2 earlier attempts).
- `forecast_receipts` of kind `item_unassisted_success`, **5**:
  - `mastery_ekf` ok (p 0.381);
  - `lo_general+composite` ok (0.550);
  - `llm_v3:llm` **refused_spend** (unpriced: a metered route with no
    `adaptive_difficulty.price_per_million`, refused before sending);
  - `llm_v3:decider` **failed** (`AIProviderUnavailable`, the loopback refused the connection);
  - `llm_v1:item` **refused_spend** (unpriced).
- `item_forecast_payloads` **4**: the frozen `llm_v3` state, and the requests of `llm_v3:llm`,
  `llm_v3:decider` and `llm_v1:item`.
- `judgment_ledger` **5** rows, task `ad_feature_audit`, judge `decider`, one per dimension
  (complexity, transfer, scaffolding, span, response), verdict **`unavailable`**. There is no
  `llm` row: the LLM fallback was refused (unpriced).
- `judgment_work_claims` 3, all released (the audit, `llm_v1`, the presentation).
- `model_call_receipts` 2: the audit's Decider request and `llm_v3:decider`, both **`failed`**
  (`AIProviderUnavailable`), **0 completed**.
- `practice_item_snapshots` 67 (main writes the same 67 at the plan read).

With the key variable unset (`ciii`), every outside request stops before the transport, with no
client (`unavailable`): no outside receipts, 0 `model_call_receipts`, the 5 audit rows
`unavailable`. The in-process receipts, the sweep and the frozen state are as above.

**(d) The rating tap** (merge, through the sidecar input). On `pi_prob_derive_complement`: an
authored reveal, `save_practice_draft` with `firstHintProgress: draft_started`, then
`submit_attempt` with `difficultyRating: "hard"` and `firstHintProgress: "draft_started"`. Then
`submit_dont_know` on `pi_incl_derive_intersections`, with nothing sent.

| Run | tapped attempt | untapped attempt |
|---|---|---|
| defaults | `difficulty_rating` **hard**, `first_hint_progress` **draft_started** (`hints_used` 1) | **NULL**, NULL |
| the four switches false | **NULL**, NULL (client-sent, not stored with `rating_tap` / `forecast_receipts` off) | NULL, NULL |

**(e) Owner commands** on the merge's copies at 213 (`mvp-0.27`): `learnloop ad data-check
--json`, then `learnloop ad backfill --audit --llm-v1 --reading --dry-run --json`. Both made
**0 calls**, the database dump was **unchanged**, and there are 0 receipts.

| | linear_algebra | probability |
|---|---|---|
| items; by `difficulty_source` | 99; `llm_estimate` 97, `author` 2 | 77; `llm_estimate` 46, none 31 |
| items with task features | 96 | 46 |
| graded attempts; items attempted once / twice or more | 62; 47 / 7 | 2; 0 / 1 |
| full-credit share | 74.2% | 0% |
| first unassisted unprimed attempt vs the label | **n 54, rho -0.566** (interval -0.72 to -0.35); within capability -0.348 (-0.56 to -0.09) | n 0 |
| AD1 receipts | all 0 | all 0 |
| backfill plan: audit | 44 revisions (15 protected skipped), 44 Decider requests, est. **$0.0032**; the LLM fallback "every call would be refused before sending" (unpriced) | 77 revisions, 77 requests, est. **$0.0061**; the same |
| backfill plan: `llm_v1:item` | 20 items (refused: unpriced) | 76 items (refused: unpriced) |
| backfill plan: reading | planned, 0 model calls | planned, 0 model calls |
| spend | cap $0.50, remaining $0.50 | the same |

**(f) Reload: the preparation queue** (merge at the defaults, the key variable set, copy of
probability). The run:
- `initialize`; a first open schedules nothing;
- **25 active item files edited** on the copy (`tags: []` → `[landing_ad1]`), so they are new
  revisions;
- `reload_vault`, then a 20 s wait;
- `reload_vault` again, then 20 s;
- `shutdown`.

A trace in the launcher, observation only, wrapped `background._prepare` to log each run's thread
and batch.

| Check | Result |
|---|---|
| workers | **one at a time**: each run was the single `learnloop-ad-prepare` thread alive |
| run 1 (first reload) | took **20** of the 25. Every one ended audit **failed** (the Decider at the loopback) and `llm_v1` **refused_spend** (unpriced), so none settled |
| run 2 (second reload, nothing new) | took **20**: the 5 left waiting, then 15 unsettled retries from the back. 19 visited; `shutdown` fenced the 20th mid-audit, leaving its claim `leased` until its lease lapses (by design) |
| recorded | `judgment_ledger` 199 `ad_feature_audit` rows over 24 revisions, verdict `unavailable`; `forecast_receipts` 39 `llm_v1:item` `refused_spend` over 24 items; `item_forecast_payloads` 39 requests; `judgment_work_claims` 47 released and 1 leased; 24 snapshots |
| model calls | `model_call_receipts` **40, all `failed`** (`AIProviderUnavailable`), **0 completed** |
| AD spend ledger | 40 `adaptive_difficulty.daily_spend_cap_usd` reservations settled, **$0.00337** charged in total (see new findings) |

**`model_call_receipts` across all 44 databases** under `landing-ad1/` (copies and their base
backups): 42 rows, **all `failed`**: 2 in `ciiik` and 40 in `fk`, all `blackhole_decider` at
`127.0.0.1:9`. There are **0** `completed` and **0** `started`, so **no call finished**.
`approach_maps` is empty on every copy.

### New findings

- **Low, shared spend framework, not fixed.** A Decider request that fails at the transport
  (connection refused, nothing billed) is still settled at its reservation in the daily envelope.
  In (f), 40 failed audit requests charged $0.00337 against the $0.50 cap, and in (c)(iii) 2
  failed requests charged $0.00013. This is `ai.spend`'s "reserved before each request,
  reconciled upward; never a refund", shared with RW4a and H1, so it is conservative (the cap can
  only be reached early). During a long Decider outage, retries on every reload or plan read would
  use up the cap with failures. A successor could release a reservation whose request never
  connected.
- **Behaviour to know, not a defect.** An unsettled revision (an outage, or an unpriced metered
  route) is retried by every later reload or plan read, at most 20 a run. Every retry writes
  another set of `unavailable` audit rows (5 a revision) and another `refused_spend` receipt.
  With the Decider down for a day of reloads, `judgment_ledger` and `forecast_receipts` grow by
  about 5 + 1 rows per revision per run. No call completes, and nothing reads them yet.

### For the owner

- **Migration 213 applies on the next open.** It adds the two attempt columns, the two
  `question_events` columns, and the three AD tables. It changes no existing row (parity (a)).
  Close the app, the MCP server and the mobile host, and **back up first**. There is no
  algorithm successor and no `--to` command.
- **What is new to see.** An optional **"Felt: easy · about right · hard"** tap beside Submit on
  the practice card (both layouts):
  - unselected; a second tap retracts it;
  - locked once Submit is pressed;
  - hidden for the session after one tap;
  - logged only: it never changes grading, scheduling or certification.

  Nothing else on screen changes; the plan, queue, certification and curves are byte-identical
  (parity (b)).
- **The background calls now made** (on by default, owner decision 2026-10-18):
  - On **Codex** (subscription, `estimated_only`; nothing counts against the cap):
    - `llm_v1:item`, once per new item revision;
    - `llm_v3:llm`, once per served plan item;
    - the feature audit's LLM fallback, for dimensions the Decider leaves unanswered.
  - On the **Decider through OpenRouter**, at its listed input price ($0.02 per million):
    - the feature audit, one request (five questions) per new item revision, about $0.00008 a
      request (the backfill estimates $0.0032 for LA's 44 revisions and $0.0061 for
      probability's 77);
    - `llm_v3:decider`, once per served plan item, about $0.00005 a request.
  - All inside **`adaptive_difficulty.daily_spend_cap_usd = 0.50`**. A metered LLM route also needs
    `adaptive_difficulty.price_per_million`, or it is refused before sending.
  - A reload or plan read prepares at most 20 revisions a run, one worker at a time.
  - `llm_v3` sends the learner's recent results on the topic (result, hints, the question), never
    answer text.
- **Turning things off** (`learnloop.toml`):

  ```toml
  [adaptive_difficulty]
  outside_forecasters = []    # no llm_v1 / llm_v3 calls
  feature_audit = false       # no audit requests (Decider or LLM)
  forecast_receipts = false   # no serve-time receipts, sweep, frozen inputs or marker (also stops the outside forecasters)
  rating_tap = false          # no tap, and a client-sent rating is not stored
  ```

  All four false is parity (c)(ii): the responses are main's, and the new tables and columns stay
  empty.
- **Owner-run commands** (on a backup copy first; dry-run first; §6):

  ```bash
  uv run python -c "from pathlib import Path; from learnloop.db.copies import copy_tree_with_databases as c; c(Path('fixtures/linear_algebra'), Path('fixtures-local/la_ad1'))"
  uv run learnloop ad data-check --vault fixtures-local/la_ad1 --json
  uv run learnloop ad backfill --vault fixtures-local/la_ad1 --audit --llm-v1 --reading --dry-run --json
  uv run learnloop ad backfill --vault fixtures-local/la_ad1 --reading
  uv run learnloop ad backfill --vault fixtures-local/la_ad1 --audit --limit 20
  uv run learnloop ad backfill --vault fixtures-local/la_ad1 --llm-v1 --limit 20
  ```

- **Open questions (defaults taken), from §7:**
  - 1: outside forecasters on by default. **Decided by the owner 2026-10-18: they stay on (AD2
    is next).**
  - 2: the feature audit on by default. **Decided with 1: it stays on.**
  - 3: serve-time receipts at plan presentations only (not probes or Today-queue serves);
  - 4: the minimal `llm_v3` card;
  - 5: item preparation from the plan pool, plus the reload of new revisions;
  - 6: workbench submits send neither the tap nor the marker;
  - 7: the rating shown on diagnostic checks;
  - 8: D22's first verdict across a rewritten answer.
- **Open items carried:**
  - the last verify's **Low**: unanswered dimensions are misreported on a retry;
  - the two new findings above;
  - `desktop_validate.py` (`syntheticBook.ts`) and `module_validate.py` (879 issues), both from
    before this stage.
