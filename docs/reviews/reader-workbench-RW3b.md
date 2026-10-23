# Reader workbench RW3b: discovered cues (stage `reader-rw3b`)

Branch `reader/rw3b` (worktree `learnanything-merge4`), base `main` at
`c9ad9cce1` (RW1c landed; migration head 213). Spec:
`docs/specs/spec_reader_workbench_v1.md` §1's RW3b line, §6 in full (§6.1
kinds and restraint, §6.2 "RW3b: discovered links" items 1-6, §6.3 data,
§6.4 routes, §6.5 switches), §5.2's in-session updates, §7.9 (roles: positive
use only, G44), §11, §13, G13-G16, G42, G44, the §14 RW3b test lists and the
§15 cue metrics. Presentation: `docs/specs/ux_reader_workbench_v1.md` §3.4
(the legend: `◌┆`, `●┆`, `▹┆`), §4.3 (the next-step fold `▹┆` opens), §4.4.
Friction notes read: RW3a (notes 3, 5, 7), RW1b §9 item 4, RW1c §8 item 2,
RW2a note 6, RW4a §9 item 4.

## 0. Plan (written before the code)

**What exists.** RW3a draws the Guide's own `recent_misunderstanding`
passages as `◌┆` marks (`reader/reader_cues.py`, `screens/reader/cues.ts`,
`useReaderCues.ts`, `MarginMark.tsx`), within the learner's density budget,
one per screenful, never on the restored passage or while skimming. Taps are
salience-only events and `learner_card` verdicts on ledger task
`passage_cue`. T6's `search_spans` takes `extra_lists`; the shared
`judge_listwise` gives request identity, the ledger-served cache, one capped
call plus a retry; `corpus.role_proposal_keys` already reads RW4e role
proposals; `corpus.model_reader_withheld` and `exam_material.held_out_material`
are the protection helpers every model context uses.

**Scope (RW3b only).**

1. **Migration 215** (AD2+AD3 holds 214; the runner has no contiguity check,
   so the 213 -> 215 gap is tried first and recorded): `passage_links`
   (WORKFLOW: paid outputs, never re-run on rebuild) and
   `reader_cue_impressions` (RECEIPT, with `suppressed_reason`; append-only
   but for one write-once response, enforced by trigger). Head fixture
   rebuilt to `migration_head_215` with the backup API (rollback mode), its
   README and every hard-coded path updated; references regenerated.
2. **Targets** (`source_retrieval/passage_cues.py`, a pure read of existing
   state, each rendered as its LLM-written statement): durable misconceptions
   on the open source's learning objects (lifecycle active), open probe-episode
   hypotheses (their posterior), named learner-text gaps not undone, and
   demonstrated facets (for "a new application"). Each target has a
   `state_key` (its statement and status); a new or resolved target
   recomputes only its own links.
3. **Shortlist.** `search_spans` over the open source's extraction with the
   target's statement as the query, plus two `extra_lists`: passages with a
   `contrast` or `counterexample` role (RW4e proposals through
   `role_proposal_keys`, and roles RW3b's own judge proposed) on the target's
   learning objects or their `confusables`, and the misconception's
   `correction_source_span_ids`. **Every shortlisted passage passes T6's
   exclusions and held-out filtering before the judge sees it:** the scope
   excludes `teaching_exclusions` and the held-out partition, and the pool is
   filtered again by `model_reader_withheld` (solutions, assessment lanes)
   and `held_out_material` (one shared helper each, no second leak check).
4. **Judge.** One listwise call per target through `judge_listwise` (route
   `passage_cue_judge`, ledger task `passage_cue`, left kind `cue_target`):
   every passage judged `clarifies_distinction` | `new_application` |
   `prerequisite_for` | `try_first` | `none`, at most two picks, each with a
   quote verified in code against the block (`text_canon.canonical`), and
   per passage the instructional `roles` RW4e reads (kept on the link,
   used only positively, G44). `try_first` is kept only on a worked example
   or derivation (`reader_tutor.NEXT_STEP_ROLES`) for an open target; a pick
   whose quote does not verify is dropped, never repaired. Background work:
   Codex by default (`ai.active_provider`, `estimated_only`), caps
   `cues.max_calls_per_source_open` (12) and `cues.max_daily_cost_usd`
   ($0.50 metered, the shared daily envelope as RW4a's organizer).
5. **Value order** (`cues.value_order_enabled`): within a section, Guide and
   discovered cues by `p_open` (read from existing state: the episode
   posterior, the misconception's lifecycle, the gap's status, the active
   predictor's P(failure) on the passage's LO for "new application" and
   "try first"), then the judge's pick rank, Guide first on ties; a target
   already shown this visit ranks after every target not yet shown; then the
   density budget. Off: RW3a's order with discovered cues after the Guide's.
6. **Holdout** (`cues.holdout_rate`, 0.1): an eligible discovered cue is
   withheld by a seeded draw (seed derived from the link id, reproducible),
   its propensity logged; Guide cues are never held out; density, spacing
   and restored-line suppressions are recorded with their reason and are not
   holdouts.
7. **Impressions** (`reader_cue_impressions`): one row per (visit, cue): shown
   (when in view), held out, or suppressed with its reason; `p_open` and its
   source, the density, the seed and propensity come from the server's own
   computation, never the client's; the learner's response (`opened`,
   `check_me`, `try_first`, `not_relevant`, `fewer`) is written once.
8. **Kinds and copy** (fixed templates, G16): discovered distinctions `◌┆`
   ("Connects to something you worked on: …"), a new application `●┆` ("A new
   use of something you've shown: …"), try this step first `▹┆` ("Try the
   next step before reading it?"); the "because" line says "found by
   LearnLoop's model, not by a test". "Try this step first" opens RW1b's
   *let me try the next step* at that line (a learner pick, never a gate).
9. **RPCs** (desktop only): `reader.cue_discovery` (starts the background
   job for the open source, answers at once), `reader.cue_discovery_job`,
   `reader.cue_impressions`, `reader.discovered_cue_action`. The guide plan
   merges discovered cues only when `cues.discovery_enabled`; a tap is
   resolved by link id without rebuilding the plan (RW3a friction note 5).
   In-session updates: the Reader asks for discovery again when the plan's
   target fingerprint changes (a new hypothesis or gap), so only the new
   target's links are computed, in the background.
10. **Owner-run** `learnloop reader cues discover --vault --source [--dry-run]`
    (dry run: targets and shortlists, no model call) and the cue funnel in
    `learnloop reader report` (impressions shown vs held out with
    propensities, response rates).

**Switches.** `cues.enabled` (RW3a's), `cues.discovery_enabled`,
`cues.try_first_enabled`, `cues.value_order_enabled`, `cues.one_per_viewport`
(RW3a's), `cues.holdout_rate`. With every RW3b switch off the RW3a cues are
byte-identical to `c9ad9cce1` (pinned in pytest and vitest before any change).

**Never.** Nothing RW3b writes enters evidence, mastery, serving or grading;
"Check me" and "Try this step first" are learner picks. No edit to
`adaptive_difficulty/`, scheduling intent, `daily_plan` or RW4b's exercise
files; `ReaderScreen.tsx` changes are a few wiring lines, the behaviour lives
in `screens/reader/`. No live model call anywhere in this stage.

## 1. What was built

Commits on `reader/rw3b` (base `c9ad9cce1`): `8ee16cbd1` (this plan and the
switch-off pins, written and generated on the unchanged base), `e8ecf17dd`
(backend), `e086fc460` (frontend), then the references and this record.

**Migration 215** (`migrations/215_reader_discovered_cues.sql`). The runner
has no contiguity rule and no test rejects the 213 -> 215 gap, so it is
numbered **215** as the orchestrator asked (AD2+AD3 keeps 214); nothing needs
renumbering at the landing unless 214 lands with a conflicting object name
(it does not: its tables are `ad_*` and `item_forecast_scores`).
- `passage_links` (WORKFLOW, append-only by trigger): §6.3's columns plus
  `pick_rank`, `ranks_json` (the passage's rank in each retrieval list, the
  contrast and correction lists among them) and `roles_json` (the judge's role
  proposals with confidence). `ledger_id` references `judgment_ledger(id)`;
  one row per (extraction, target, state key, span).
- `reader_cue_impressions` (RECEIPT): §6.3's columns plus `cue_id`, `kind`,
  `extraction_id`, `span_id` and `learning_object_id` (the holdout estimate
  reads the next attempt on it). CHECKs: shown iff no reason; a holdout names
  a link; a response has its time. Append-only but for the first response,
  written once (trigger). One row per (visit, cue).
- `table_roles` classifies both; `fixtures/migration_head_213` was renamed
  `migration_head_215` and its `state.sqlite` rebuilt: a backup-API copy of
  the base's 213 head with only 215 applied (`UPGRADE_SCRATCH_COPY`,
  `wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE`, header 1/1,
  `integrity_check` ok, `foreign_key_check` empty, no companions), placed with
  the backup API. README updated; every hard-coded path (30 test files and
  the two reference scripts, `SCHEMA_HEAD = 215`) moved.

**Backend.**
- `src/learnloop/source_retrieval/passage_cues.py` (the Reader package sits
  below `source_retrieval`, so the retrieval-and-judge code lives here, as
  RW4a's and RW1c's do):
  - **Targets** (`cue_targets`): the LOs the open source teaches (section
    provenance, RW6a's reading, plus teaching links into this extraction);
    on them, the concrete hypotheses of an open probe episode that name a
    misconception (`p_open` = the episode posterior's mass), durable
    misconceptions not in an episode (`p_open` 1.0 from the lifecycle), named
    learner-text gaps not undone and not naming a targeted misconception
    (`p_open` 1.0 from the gap's status), and facets with a demonstrated
    capability (`demonstrated_capabilities_for_facet`, for "a new
    application"). `state_key` = statement + status.
  - **Protection before the judge** (`protection`, `shortlist`): the scope
    excludes `teaching_exclusions` (exam and held-out material, roles without
    teaching authority, exercise and assessment links) and a reading held out
    whole is never searched; the pool is filtered again by
    `model_reader_withheld` (solutions, assessment lanes) and
    `held_out_material`. No new leak predicate.
  - **Shortlist**: `search_spans` (statement as the query, no rewrite, RRF
    pool, twice the shortlist read so withheld passages never shrink it) with
    `extra_lists`: `contrast` (RW4e proposals through the sources spec's
    `source_object_lists(…, "remediate", …)` plus this judge's own
    contrast/counterexample proposals, kept only on the target's LOs or their
    confusables) and the misconception's `correction_lists` (facets, sources).
    The manifest names every list and its size (G42).
  - **Judge** (`judge_target`): `judge_listwise` with `CUE_JUDGE_TASK` (route
    `passage_cue_judge`, ledger task `passage_cue`, left kind `cue_target`,
    right kind `reader_span`, picks at most two, `none` never picked), the full
    answer captured through `validate` (as RW4a's organizer), recovered from
    the checkpoint or receipt when the ledger answers "cached" but the links
    were never written. A pick is dropped, never repaired, when its quote is
    not the passage's words (`text_canon.canonical`, 12 characters at least)
    or a `try_first` is not on a worked example or derivation
    (`reader_tutor.NEXT_STEP_ROLES`) for an open target. Spend: Codex
    (`ai.active_provider`, empty route) is `estimated_only` and never refused
    by the metered cap; a metered route without a price is skipped and
    labelled; with one it reserves under the shared daily envelope
    `cues.max_daily_cost_usd` (RW4a's `SharedDailyEnvelope`).
  - **Discovery** (`discover`): targets not yet settled (judged at this state,
    links written), highest `p_open` first, at most
    `cues.max_calls_per_source_open` paid calls; `dry_run` reads keyword lists
    only and calls and writes nothing. `LEARNLOOP_CUE_JUDGE_MODELS=off` (set by
    `tests/conftest.py`) resolves no real client.
  - **Merge** (`merged_cues`): RW3a's candidates and the discovered ones; a
    Guide-marked passage keeps the Guide's mark; one discovered mark per
    passage; not relevant and books off honoured; the seeded holdout
    (`holdout_draw`: seed = sha256 of salt and link id, draw = seed/2^64,
    propensity = the drawn arm's probability); value order; the density budget;
    RW3a's spacing rank. The payload is RW3a's plus `discovery` (`targets_key`,
    the switches, `held_out`, `suppressed`).
- `src/learnloop/reader/reader_cues.py`: `DISCOVERED_TAP_ACTIONS` (adds
  `try_first` -> `cue_try_first`, `same`), `RW3B_SERVER_CUE_EVENTS`,
  `current_verdicts`, and `record_cue_tap(actions=…, right_kind=…)` with
  RW3a's defaults (RW3a's calls unchanged).
- `src/learnloop_sidecar/handlers/reader_cue_discovery.py`: the four RPCs
  (§0 item 9); `reader.guide_plan` merges discovered cues only while
  `cues.discovery_enabled`, else calls `RCU.guide_cues` exactly as before.
  Taps and impressions resolve a cue from the plan's merged cues kept per
  source in the context (RW3a friction note 5), rebuilt on a miss.
  *Superseded for impressions (fix round 4, F17):* each plan carries a
  `discovery.plan_id`, impressions name it, and they are resolved against
  that plan as it was served. An unknown or expired plan is refused.
  *Fix round 4, F16:* discovery requests carry a `source_open_id`, and one
  call budget is kept per open. *Fix round 5:* a source's judge calls are
  capped by `cues.max_calls_per_source_per_day` (36), counted from the
  durable receipts (a rolling 24 hours in UTC since round 6). Taps carry the `plan_id` the cue was first seen on,
  and a missing impression is created only from that kept plan.
- Config `[cues]`: `discovery_enabled`, `try_first_enabled`,
  `value_order_enabled` (true), `holdout_rate` (0.1), `max_calls_per_source_open`
  (12), `max_daily_cost_usd` (0.5); route `ai.routing.passage_cue_judge`
  (`AITask`, `ROUTE_FOR_OPERATION`, a privacy disclosure in Settings). Every
  new key is classified in `params/parameter_registry.py` (structural,
  operational). All 19 `DEFAULTS_SNAPSHOT_BY_ALGORITHM` fingerprints were
  recomputed from the composed defaults (template `.pyc` cleared). No
  algorithm successor: display only.
- `learnloop reader cues discover --vault --source [--dry-run] [--json]`;
  `learnloop reader report` gains `cues.discovered` only once impressions
  exist (reasons, kinds, responses, the share of `●` marks, and the holdout
  estimate: the next attempt's `correctness` on the cue's LO, each arm
  weighted by 1/propensity, self-normalized, with a normal 95% interval and
  the sample sizes; density, spacing and restored-line suppressions left out;
  an arm with fewer than two outcomes gets counts only).

**Frontend.** `api/dto.ts`, `api/client.ts` (four calls), Tauri passthroughs
(`commands.rs`, `main.rs`); `screens/reader/cues.ts` (`DISCOVERED_COPY`,
`markClass`), `MarginMark.tsx` (kind class and `data-cue-kind` only on a
discovered mark; open shows the passage's own words and the statement in the
model's voice; *try the next step first* as the first action; the legend's
discovered marks), `styles/app.css` (static `●┆`, `▹┆` glyphs),
`useCueDiscovery.ts` (the background search once per `targetsKey`, read back
without waiting, the plan re-read when it found something),
`useCueImpressions.ts` (receipts once per visit: a drawn mark in view; a
held-out, density-cut, spaced or restored-line cue when its passage is in
view), `useReaderCues.ts` (taps through `reader.cue_tap` with the visit while
discovery is on; `tryFirst`, `fewerOn`). `ReaderScreen.tsx`: 11 lines (the
try-first callback through a ref to RW1b's `activeCtl.start("next_step", …)`,
the mark's two props, the footer's legend prop); none of RW4b's hunks.

## 2. Deviations and decisions within the spec

*Fix round 1 (`docs/reviews/reader-rw3b-codex-review.md`) supersedes items 3
(now the learner's impressions this reader session, F10), 4 (recurrence
groups and holding-pen candidates are targets, F9), 5 (claims needing an
independent check are try-first-only targets, F9) and 6 (both arms measured
by their passage; neither recorded on the PDF, F5).*

1. **Extra columns** (recorded in the migration): `pick_rank`, `ranks_json`,
   `roles_json` on links; `cue_id`, `kind`, `extraction_id`, `span_id`,
   `learning_object_id` on impressions. The spec's columns are all there.
2. **Role proposals are kept on the link, not written to `source_objects`.**
   RW4e owns the proposal rows (§7.9); it reads `passage_links.roles_json`
   (with the judge, ledger id and prompt version on the same row) as it reads
   RW4a's organizer roles. They already widen RW3b's own contrast list
   (positive only, G44).
3. **"A target already shown during this visit"** is read within the plan:
   a target given a mark in an earlier section ranks after every target not
   yet given one. Re-ranking on what was seen mid-visit would move marks while
   the learner reads (RW3a's "nothing appears or disappears while scrolling").
4. **Recurrence-group targets are reserved** (the CHECK admits them): v1 reads
   the misconceptions and open hypotheses they group. A group target needs the
   group's own statement and openness, which T1's projection does not store.
5. **"Unchecked claim"** for try-first is read as an open target (a
   misconception, hypothesis or named gap); RW6a's claims needing an
   independent check are per session and not a cue input yet.
6. **A held-out cue's impression is logged when its passage is in view**, as a
   shown mark's is (symmetric arms for the estimate). The original PDF draws
   no element per passage, so on the PDF surface only drawn marks are logged.
7. **The holdout is per link** (a link is shown or withheld for its life at a
   given rate), so a learner's arm does not flip between visits.
8. **In-session updates** are client-driven: the Reader asks for discovery
   again whenever a plan read shows a new `targetsKey` (a tap, a diagnosis
   landing, reopening). No hook was added inside the learner-text gap or
   diagnosis pipelines (other stages own them).
9. **Opening a vault may open a probe episode** for an active misconception;
   its target is then the hypothesis (with the episode's posterior, often
   small, so it ranks below the Guide's cues). That is the spec's reading of
   `p_open`; the owner may want the lifecycle's 1.0 instead (Q2).

## 3. Tests (all fakes; no model call)

New: `test_passage_links.py` (16: targets, protected shortlist, contrast and
correction lists in the manifest, G15 judge stubbed to none, ledger verdict
and verified quote, dropped quotes, state-key recompute and ledger cache,
recovery without paying again, per-open cap, metered skip and cap, Codex not
refused, dry run, switch off, G44 roles), `test_reader_cue_holdout.py` (8:
seed reproduces the draw, propensity equals the draw probability, rate,
Guide never held out, rate 0, impressions recorded by the server's decision,
once per visit and cue, fewer, RPCs refuse while off),
`test_reader_cue_value.py` (6 functions, 9 cases: p_open then pick rank,
Guide first on ties, monotone rescaling keeps the order, density changes only
how many, seen targets rank after, value order off, predictor P(failure) for
a new application), `test_reader_try_first.py` (5, G42),
`test_reader_rw3b_protection.py` (6: held-out sentinel over the judge
prompt, stored quotes and rendered cues; a link made before its passage was
held out never shown or tapped; a whole held-out reading never searched; G13
display only; not-relevant text is never learner text; G16 lint),
`test_reader_cues_cli_report.py` (5), `test_reader_rw3b_migration.py` (4,
one durability), `test_reader_rw3b_switch_off.py` (2, pinned on the base).
Changed: `test_salience_firewall.py` (+2: `cue_try_first` salience-only and
not client-recordable; no belief, scheduling, grading or plan module reads
the RW3b tables), `test_mobile_allowlist.py` (RW3b's four RPCs desktop only),
`test_judge_routes.py`, `test_architecture.py` (the store is a registered SQL
owner), the four earlier migration tests (215's objects on the way to head),
the 30 head-path files. Vitest: `ReaderScreen.cuesSwitchOff.test.tsx`
(snapshots written on the base), `ReaderScreen.discoveredCues.test.tsx` (8).

## 4. Owner-run commands (dry run first; no paid call was made in this stage)

On a backup-API copy only:
`uv run python -c "from pathlib import Path; from learnloop.db.copies import copy_tree_with_databases as c; c(Path('fixtures/probability'), Path('fixtures-local/rw3b-prob'))"`,
`uv run learnloop doctor --fix-state --vault fixtures-local/rw3b-prob`
(applies 215), then
`uv run learnloop reader cues discover --vault fixtures-local/rw3b-prob --source <source id> --dry-run --json`
(targets and keyword shortlists; nothing called or written), then without
`--dry-run` (one Codex call per target, at most 12, `estimated_only`). In the
app: open the book; marks arrive in the background. `uv run learnloop reader
report --json --vault <copy>` shows `cues.discovered` once impressions exist.
Switches in the copy's `learnloop.toml` `[cues]`: `discovery_enabled = false`
(RW3a's cues, byte for byte), `try_first_enabled`, `value_order_enabled`,
`holdout_rate = 0`, `max_calls_per_source_open`, `max_daily_cost_usd`.

## 5. Open questions (defaults applied)

- **Q1.** Holdout rate 0.1 on every discovered cue from day one (spec default).
  Default: kept.
- **Q2.** A misconception inside an open probe episode is ordered by the
  episode's posterior mass (often well below 1), so its cues rank after the
  Guide's at every density. Default: the spec's reading (posterior); the
  alternative is the lifecycle's 1.0.
- **Q3.** Discovery runs on every source open with discovery on (Codex, up to
  12 calls per open for unsettled targets; settled targets cost nothing).
  Default: on (generous defaults).
- **Q4.** Recurrence groups as their own targets (deviation 4). Default:
  deferred.

## 6. Friction notes

- **RW4d** (kept comparisons): `⇄` is the learner's mark, outside the
  budget; the discovered marks share RW3a's gutter slot, so a passage with a
  cue and a kept comparison needs RW2a's offset (its friction note 6).
- **RW4e** (roles): the cue judge already proposes roles per judged passage;
  only picked passages are stored (`passage_links.roles_json`, with judge,
  ledger id, prompt version). Persist them as `source_objects` proposals
  there; `contrast_list` reads both RW4e's proposals and these.
- **RW2c** (worked example in your route): `passage_cues.shortlist` is a
  reusable protected T6 shortlist for one target statement; a try-first link
  marks worked examples worth offering.
- **RW6b** (follow-ups): `reader_cue_impressions` (shown vs held out with
  propensities) and the `passage_cue` learner-card verdicts are the cue's
  outcome inputs; the report's `cues.discovered.holdout` is the first
  estimate. `targets_key` is a cheap "did the open questions change" signal.

## 7. Gate (this step; targeted per the owner rule of 2026-10-17)

Run in the worktree with `TMPDIR=fixtures-local/tmp`. `/tmp/learnloop-fullsuite.lock`
was not taken; no full suite, whole durability lane or whole vitest run.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | **28 kept, 0 broken** |
| targeted `pytest -n 8` over 105 files (`fixtures-local/rw3b-scripts/affected.txt`: every new and changed test file, every file naming the head fixture, and every file that greps for the touched modules: `reader_cues`, `guide_plan`, `reader_report`, routing, disclosures, the parameter registry, `table_roles`, the defaults snapshots, the CLI help, `search_spans`, `judge_listwise`, plus `test_mobile_allowlist`, `test_architecture`, `test_table_roles`, `test_tracked_fixture_databases`, `test_coordinated_migrations`, `test_registry_audit`, `test_config_refactor`, `test_sidecar_reader`, `test_cli_help_snapshot`) | first run **2,074 passed, 40 failed**: all 40 were the defaults-snapshot pins reading a stale template `.pyc`; with it cleared, the 21 files holding them: **408 passed** |
| `pytest tests/test_desktop_rpc_contract.py` | **4 passed** |
| `pytest -m durability` on the migration and fixture files (`test_reader_rw3b_migration`, `test_ad1_migration`, `test_library_asks_migration`, `test_approach_maps_schema`, `test_help_assists_schema`, `test_migrations`, `test_coordinated_migrations`, `test_tracked_fixture_databases`) | **7 passed** |
| `pytest --durable-sqlite` on the eight RW3b behaviour files | **51 passed** |
| `npm run typecheck` | clean |
| `npx vitest run` over `src/screens/ReaderScreen*`, `src/screens/reader/`, `PdfReaderPane.marks.test.tsx`, `readerCheck.test.ts` (57 files) | **416 passed** (the switch-off snapshots unchanged) |
| `npm run frontend:build` | built (the usual chunk-size notice) |
| `cargo check` | finished |
| `db_generate_reference.py`, `db_validate_reference.py`, `validate_vault.py` | head 215, 335 table notes, 926 leaves; errors []; passed (1,132 notes, all reachable) |
| CLI help snapshot | rewritten (`learnloop reader cues discover`) |

**Model calls in this stage: none** (no paid or live call, no smoke run on a
vault copy; every judge is `tests/passage_cue_fakes.CueJudgeFake`).
**Safety:** the tracked working vaults were not opened; no credential file
was read. One stray helper left in `fixtures-local/tmp` by an earlier stage
(`copy.py`) was imported by accident when a script ran from that directory;
its guard found its backup-API copy already present (dated 2026-10-18), so it
copied nothing. Later scripts ran isolated (`python -I`) from
`fixtures-local/rw3b-scripts/`.

## 8. Landing onto main

Landed in the `learnanything-merge2` worktree on branch `merge/rw3b-onto-main`, cut from main at `e14b4e4ff` (the
DL2 landing record; main has RW4b and DL2, successor mvp-0.29 with 20 defaults snapshots, migration head 213). The
stage tip is `837208ad2` (base `c9ad9cce1`), unchanged. The orchestrator's last verify (Codex job
`20261020-171319-9xYYRQ` on `837208ad2`) is clean: no High, no Medium. Main was neither fast-forwarded nor pushed
here.

### Commits and conflicts

- `8e50f38e5`: a `--no-ff` merge of `reader/rw3b` onto `e14b4e4ff`. Three source conflicts, each composed so that
  both sides survive:
  - `config/template.py`: RW4b's, DL2's and RW3b's notes kept on every defaults snapshot (RW3b's `[cues]` note under
    mvp-0.9's, a one-line pointer on the others, mvp-0.29 included), and all **20** snapshots (mvp-0.9 … mvp-0.27,
    mvp-0.29) recomputed from the composed defaults with the template `.pyc` cleared.
  - `params/parameter_registry.py`: RW4b's `[library_exercises]` rule and RW3b's two `[cues]` rules both kept.
  - `tests/test_mobile_allowlist.py`: the desktop-only parametrization lists both `READER_RW3B_RPCS` and
    `READER_RW4B_RPCS`.
  - 400 generated reference notes took main's side and were regenerated afterwards.
  - `docs/decider-tier1-migration.md`: the head-fixture path moves to `migration_head_215` (the stage had missed
    this one prose path).
  - Auto-merged without conflict, then checked by the gate: `ReaderScreen.tsx` (RW3b's 11 wiring lines beside RW4b's
    hunks), the reader handlers and the handler registry, `config/schema.py`, `dto.ts` / `client.ts`, `commands.rs` /
    `main.rs`, the CLI help snapshot, the RPC pins and the 35 head-fixture paths.
- `2f669764f`: the references regenerated on the merged tree (the gate head).
- This record.

**Migration numbering.** 215 lands with a gap: main's head is 213 and AD2+AD3 holds 214. `db/migrate.py` `_migrate`
applies every migration not yet applied, so a vault at 213 takes 215 now and 214 later. Every test, script and
reference generator accepts the gap: the full suite and the durability lane pass with `migration_head_215`,
`db_generate_reference.py` / `db_validate_reference.py` run with `SCHEMA_HEAD = 215` and 0 errors, and parity (a)
opens real vault copies from 165 straight to 215 (49 migrations, no 214).

### Regeneration

- **References.** `db_generate_reference.py`, then `db_validate_reference.py`: **0 errors**, `schema_head` 215,
  **335** table notes, **937** configuration leaves in **66** sections (RW3b's eight new leaves, seven `[cues]` keys
  and `ai.routing.passage_cue_judge`, on DL2's 929). The two prose counts in `Configuration.md` and `Database.md`
  were moved by hand; the rest is commit labels, RW3b's tests in the table notes and the field notes (405 files).
- **Defaults snapshots.** With the template's `.pyc` cleared, all **20** `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries
  match `defaults_fingerprint_for_version` (recomputed in the merge commit; 0 mismatches after).
- **CLI help snapshot and RPC pins** (serializer snapshot, desktop RPC contract, mobile allowlist, sidecar
  registry): a pin run of 773 tests (those files plus every test naming the snapshots, `test_table_roles`,
  `test_tracked_fixture_databases`, `test_coordinated_migrations`, `test_migrations`, `test_rebuild_orchestrator`,
  `test_architecture`, `test_registry_audit`, `test_config_refactor`, `test_sqlite_file_copies`) passed; no file
  needed rewriting. RW3b's four RPCs stay desktop-only.
- **Head fixture 215.** Main changed neither `migration_head_213` nor `migrations/` since `c9ad9cce1`, so the
  stage's fixture stands. Checked: a backup-API copy of main's `migration_head_213` with 215 applied under
  `UPGRADE_SCRATCH_COPY` (`wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE`) is identical to the tracked
  `fixtures/migration_head_215/state.sqlite` in schema (1,427 objects) and in every row of all 340 tables (apart
  from `schema_migrations.applied_at`); both have header bytes 1/1, `integrity_check` ok, empty
  `foreign_key_check`, and no `-wal` or `-shm`. Not rebuilt.
- **`validate_vault.py`**: passes (1,135 notes, 1,133/1,133 reachable).
- **Known failures from before this stage, not fixed:** `desktop_validate.py` still stops on
  `components/pdfSelection/testing/syntheticBook.ts`; `module_validate.py` reports **954** issues (948 at the DL2
  landing: RW3b adds modules without module notes, such as `source_retrieval/passage_cues.py` and
  `db/stores/reader_cue_links.py`).

### Gate

Python 3.12.14. `TMPDIR` was merge2's `fixtures-local/tmp`; every command after the install ran as `uv run
--no-sync`. Both suite lanes ran under `flock /tmp/learnloop-fullsuite.lock` on `2f669764f` (the gate head; this
record changes docs only). The AD2+AD3 (`learnanything-ad1`) and RW4d (`learnanything-rw4b`) worktrees and their
processes were not touched. Every test uses fakes. **This is the first full run over RW3b's code**: the stage and
its 11 fix rounds ran targeted tests only.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `lint-imports --no-cache` | **28 kept**, 0 broken |
| full suite `pytest -n auto` | **14,889 passed, 2 xfailed, 0 failed** (24 min 53 s; `fixtures-local/rw3b-landing-fullsuite.log`). The DL2 landing ran 14,783 |
| `pytest -m durability` | **114 passed**, 14,777 deselected (3 min 14 s; `fixtures-local/rw3b-landing-durability.log`). DL2's was 113; RW3b adds one |
| `npm install`, `npm run typecheck` | up to date (lockfile unchanged); clean |
| `npm test` (the whole vitest run) | **158 files, 1,254 tests passed** on the first run (DL2's landing: 154 / 1,206) |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | ok (RW3b's four passthroughs in `commands.rs` / `main.rs`) |
| thread, lock and timing tests | all passed on the first run, so none was rerun |
| tracked fixtures, worktree | `git status` clean after both lanes and the frontend run; no non-empty `-wal` beside a fixture |

No failure, so no landing fix.

### Parity (backup-API copies; no model call completed)

**Setup** (scripts in `fixtures-local/landing-rw3b/scripts/`, adapted from the DL2 landing's):
- **Copies.** `fixtures/linear_algebra` and `fixtures/probability` were copied once, with `copy_tree_with_databases`,
  from the main checkout into `fixtures-local/landing-rw3b/orig/`; every other copy came from `orig/` or its
  upgraded copies through the same helper. `arxiv_v2` was not opened. Both vaults start at schema 165, label
  `mvp-0.8`.
- **Code.** Main's code is `git archive e14b4e4ff`; the merge's is `git archive 2f669764f`.
- **Environment.** Every run went through `env -i` with only `PATH`, `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`,
  `TMPDIR` and `LANG` (empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`).
- **Routes.** `neutralize3.py`, under each code, sent every route field to `127.0.0.1:9` (55 on main, 56 on the
  merge: `passage_cue_judge` is the new one; the reader, tutor, sources, hint, workbench, AD and Decider routes
  included), the active provider to that loopback profile with no fallback; `query_rewrite`,
  `tutor_query_rewrite`, `tutor_rerank`, `dense`, `[embedding]` and `[learner_text_gaps]` off; `build_on_serve` and
  outcome placement off. `routes.py` resolved all 58 `AITask`s on main and 59 on the merge (`passage_cue_judge` to
  `blackhole` at `127.0.0.1:9`): nothing outside the loopback profiles except `embedding`, disabled and keyless.

**(a) Migration 215**

| Check | linear_algebra | probability |
|---|---|---|
| open (migrate), main's code / the merge's | 165 → 213 (48 applied) / 165 → **215** (49 applied, no 214) | the same |
| schema, main@213 vs merge@215 | merge-only objects are exactly **14**: `passage_links`, `reader_cue_impressions`, their 4 named indexes, 4 `sqlite_autoindex` (UNIQUE) indexes and 4 triggers (`*_no_update`, `*_no_delete`, `reader_cue_impressions_response_once`); none main-only; no shared object's SQL differs (1,414 → 1,428) | the same 14 (1,413 → 1,427) |
| rows of every existing table (338), all columns | **identical** (16,539 rows); `schema_migrations` + 215, the common rows differ only in `applied_at`; both new tables empty | **identical** (7,637 rows; the same) |
| `foreign_key_check` / `integrity_check` | 0 / ok, both sides | the same |
| `rebuild --shadow --json`, main@213 vs merge@215 | **0 differences** after normalisation (facet 0, mastery 2, schedule 8 on both); live database unchanged on both | **0 differences** (0 / 1 / 1) |
| `doctor --json`, main@213 vs merge@215 | **0 differences** after normalisation (57 issues, 1 error) | **0 differences** (101 issues, 48 errors) |

**(b) Nothing served changes** (frozen clock 2026-10-19 09:00 UTC; certification with recipe gaps and curves, the
Today queue with no session / a session / greedy, the daily plan read, served twice and read again)

| Check | linear_algebra | probability |
|---|---|---|
| at `mvp-0.8` (the copies' label) | cert **byte-identical** (132,860 bytes), Today **byte-identical** (504,488), plan byte-identical (off below mvp-0.14) | cert (17,494), Today (709,910), plan: all **byte-identical** |
| upgraded by main's code to `mvp-0.27` (`--to mvp-0.9`, `--to mvp-0.27`, `rebuild-derived-state` twice; all rc 0), opened by each code | cert **byte-identical** (129,651), Today **byte-identical** (528,665) | cert (17,495), Today (741,269): **byte-identical** |
| then by main's code to `mvp-0.29` (`--to mvp-0.29`, `rebuild-derived-state` twice; all rc 0), opened by each code | cert and Today **byte-identical** (the same sizes) | the same |
| the daily plan at mvp-0.27 and at mvp-0.29 | identical except `router_decisions.card_hash`, `snapshot_hash` and the card hash inside `detail_json`; a second run of main's code on a fresh copy differs from the first in exactly these three | the same |

**(c) The real sidecar** (stdio, `SystemClock` frozen at 2026-10-19 09:00 UTC through `sidecar_clock.py`;
`cue_run.py`) on copies of main's mvp-0.29 vaults: (i) `cm`, main's code; (ii) `coff`, the merge with `[cues]`
`discovery_enabled`, `try_first_enabled`, `value_order_enabled` = false and `holdout_rate` = 0; (iii) `cdef`, the
merge at its defaults. Each: `reader.prompt_contract`; `reader.guide_plan` on a source (probability
`ext_01KYMSJJNJQ0W9QHZ9ZMFD88NY`, linear_algebra `ext_01KY2YGNVCCVEQCGCE4RH3BWHQ`); `reader.cue_discovery` with a
`source_open_id`, polled through `reader.cue_discovery_job`; the guide plan again; on probability a manual-graded
attempt on `pi_prob_derive_complement`; `shutdown`.

| Step | (i) main vs (ii) switches off | (iii) defaults |
|---|---|---|
| `reader.prompt_contract` | **byte-identical** (both vaults) | byte-identical to (i) |
| `reader.guide_plan`, both reads (RW3a's Guide cues) | **byte-identical** (both vaults, both reads): probability 2 marks, linear_algebra 8 | the same marks, the same cue ids in the same order. Differences, all additive: every Guide mark gains `foundBy` "guide", `pOpen` 1.0 and `pOpenSource` "error_lifecycle"; `cues.withheld` gains `holdout` 0; `cues.discovery` is present (`planId`, `holdoutRate` 0.1, `tryFirst`, `valueOrder`, `targets` (probability 0, linear_algebra 3), `targetsKey`, `targetsPending` false, `heldOut` [], `suppressed`: the Guide cues the density budget cut, with reason `density`, probability 1 and linear_algebra 3) |
| `reader.cue_discovery` | (i) `method_not_found`; (ii) refused, `cues_disabled` ("Discovered margin cues are switched off …") | started at once (`pending`), done within 1 s, **0 calls**: probability `unavailable` with no target; linear_algebra 3 targets (two hypotheses, one demonstrated facet), each `skipped: metered cue judge route without source_retrieval.llm_price_per_million` |
| the attempt (probability) | the rows it added in 24 tables are **identical** across (i), (ii) and (iii) with ids normalised; `attempt_debug_payloads` differs only in the attempt id and the diagnosis receipt id | identical, as left |
| RW3b's tables, receipts | (ii): `passage_links` 0, `reader_cue_impressions` 0; `passage_cue` ledger 0; `model_call_receipts` 0 | the same: 0 / 0 / 0 / 0 |

A fourth run, **(iv) the route actually tried**: linear_algebra at the defaults with
`source_retrieval.llm_price_per_million = 1.0` and a dummy key in the loopback profile's variable, so the metered
judge sends its requests to `127.0.0.1:9`. The job ran **12** requests (the per-open cap) and stopped: the first target
`capped` ("calls exceeds max_calls"), the other two `capped` (`cues.max_calls_per_source_open`). 24
`model_call_receipts`, every one `failed` (12 judge requests, `AIProviderUnavailable`, each with its transport child,
`APIConnectionError`); no link, no ledger row, the guide plan unchanged.

**(d) The dry-run CLI.** `learnloop reader cues discover --vault <copy> --source <source> --dry-run --json` on
merge-migrated copies of both mvp-0.29 vaults: rc 0, `calls` 0, `judged` 0, `dry_run` true; the spend plan names the
caps (`max_calls_per_source_open` 12, `max_calls_per_source_per_day` 36 with window "rolling 24 hours (UTC)",
`source_calls_last_24h` 0, `max_daily_cost_usd` 0.5, `remaining_today_usd` 0.5) and the judge's estimate
(linear_algebra 3 calls, 69,686 tokens; probability 0). The database file is byte-identical before and after (its
logical dump too): `model_call_receipts`, `passage_links` and the `passage_cue` ledger stay 0. The run leaves an
empty `-wal` and a `-shm` beside the copy's database (finding 3).

**`model_call_receipts`**: 40 learner databases under `landing-rw3b/` carry the table; **no row is `completed`** in
any of them. The only rows are run (iv)'s 24, all `failed`.

### New findings

1. **No composition failure.** RW3b's three conflicts were bookkeeping (snapshots, registry rules, the RPC pin
   list); RW4b's and DL2's code paths compose with RW3b's without a change.
2. **Against an unreachable metered route, the first target spends the whole per-open allowance on retries**
   (`judge_listwise(..., max_retries=cap, max_calls=cap)`): 12 failed requests on one target, the other targets
   capped. That is the designed count (F3: every request and retry counts) and the caps hold (12 per open, 36 per
   source per rolling 24 hours), so it stays at most three such opens a day per source. Low; not changed.
3. **The dry run leaves an empty `-wal` and a `-shm`** beside a WAL-mode database it only read. The database file
   and its contents are unchanged. Harmless (the CLAUDE.md note on empty companions); Low.
4. **With discovery on, every Guide mark carries `foundBy`, `pOpen` and `pOpenSource`**, and the plan a
   `discovery` block, even when nothing was discovered. Display payload only; the client renders the same marks.

### For the owner

- **Migration 215 applies on the next open.** Back up the vault, close the app, the MCP server and the mobile host
  first. It adds two empty tables (`passage_links`, `reader_cue_impressions`) with their indexes and triggers and
  changes no existing row (parity (a)). No successor: your algorithm version is unchanged, and nothing served moves
  (parity (b)). AD2+AD3's 214 will apply later on top; the gap is expected.
- **What you see in the Reader.**
  - New margin marks beside the Guide's `◌┆`: a discovered distinction `◌┆` ("Connects to something you worked
    on: …"), a new application `●┆` ("A new use of something you've shown: …") and a try-first `▹┆`. Each one's
    "because" line says it was found by LearnLoop's model, not by a test; opening it shows the passage's own words and
    what you worked on.
  - **"Try this step first"**: on a worked example or derivation, it opens the Reader's *let me try the next step* at
    that line. It is your pick, never a gate.
  - **The density control** (off, fewer, normal, more, plus "fewer" on a mark) decides how many marks a section
    shows, one per screenful. About one eligible discovered cue in ten is held back at random (logged, so the report
    can tell whether the marks help).
- **Discovery** runs in the background when you open a source, on Codex by default (`ai.active_provider`; counted as
  an estimate, not billed per call). At most **12 calls per open** and **36 per source per rolling 24 hours**, inside
  the cue spend cap (`cues.max_daily_cost_usd` 0.50 for metered routes). Targets already judged in their current
  state cost nothing. Try it on a copy first: `uv run learnloop reader cues discover --vault <copy> --source <id>
  --dry-run --json` (no call), then without `--dry-run`.
- **The switches** (`[cues]` in `learnloop.toml`): `discovery_enabled = false` gives RW3a's cues byte for byte
  (parity (c)); `try_first_enabled`, `value_order_enabled`, `holdout_rate = 0`, `max_calls_per_source_open`,
  `max_calls_per_source_per_day`, `max_daily_cost_usd`; `enabled = false` turns every cue off. The judge's route is
  `ai.routing.passage_cue_judge` (empty = the active provider).

### Open questions (defaults in force)

1. **Q1.** Holdout rate 0.1 on every discovered cue from day one: **kept**.
2. **Q2.** A misconception inside an open probe episode is ordered by the episode's posterior mass (so often after the
   Guide's cues): **the posterior** (the alternative is the lifecycle's 1.0).
3. **Q3.** Discovery on every source open (Codex, up to 12 calls per open, 36 per source per day): **on**.
4. **Q5.** "Check me" on a discovered cue asks for practice on the cue's whole learning object: **unchanged** (not
   narrowed to the target's facets or to `intent="discriminate"` for rival hypotheses).
5. **Q6.** An unchecked-claim target reads RW6a's claims from the current and previous reader sessions only:
   **those two**.

(Q4, recurrence groups as targets, was settled by fix round 1's F9: they are targets.)

### Open items

- **Accepted Lows:**
  - the per-source daily cap is exact within one process, so a CLI run at the same instant as the sidecar can pass
    the check concurrently;
  - the retention bounds: 4,096 opens, 256 plans for 12 h;
  - the holdout interval is withheld when outcomes are shared across arms.
- **Findings 2 and 3** above (Low).
- **Friction notes for RW4d, RW4e, RW2c and RW6b** stand as written in §6.
- **From before this stage:** `desktop_validate.py` (`syntheticBook.ts`) and `module_validate.py` (954 issues).
