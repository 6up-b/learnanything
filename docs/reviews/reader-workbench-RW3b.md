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
