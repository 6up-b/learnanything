# Replaced learner claims kept (successor mvp-0.36)

Stage `lp-learner-report-superseded`, branch `lp/learner-report-superseded`
(worktree `learnanything-ad1`), base main `5c6a0834f`. The successor of the
Medium recorded at the rebuild-equivalence landing
(`docs/reviews/rebuild-equivalence-fix.md`; the strict xfail
`test_a_second_learner_report_on_an_lo_after_an_attempt_rebuilds_to_live`).

## The defect

A learner report on an LO (a `too_easy` retirement, a rung-variant request
easier/harder) writes an LO-scoped claim and re-anchors the LO's mastery at
once. A second report of the same source on the same LO replaced the first
through `Repository.delete_learner_claims` (the replace seam), i.e. deleted
it. Its live re-anchor had already moved mastery, so replay, which applies
claims at their own point since mvp-0.33, could not apply a claim that was
gone: rebuild != live (Δmean -0.269 on `lo_diag`, one attempt then two
`too_easy` retirements). Every upgrade rebuilds, so a vault carries the
difference from then on.

## The design (the smaller one)

One nullable column and a version gate on the seam's write; no new table.

* **Migration 225** (`225_learner_claim_superseded_by.sql`):
  `learner_claims.superseded_by TEXT CHECK (superseded_by IS NULL OR
  superseded_by <> id)`, the id of the claim that replaced this one. NULL on
  every existing row. Classified as `metadata` in
  `adaptive_difficulty/column_classes.py`; `learner_claims` stays RAW_LEDGER
  (no new table, so no table_roles change).
* **The seam** is one repository method,
  `Repository.replace_learner_claim(claim, *, keep_replaced, clock)`: with
  `keep_replaced` it inserts the new claim and marks the in-force rows of the
  same `(source, scope_type[, scope_id])` `superseded_by` it, in one
  transaction; without it, it is exactly the predecessor's delete-then-insert.
  All three seam callers use it: `item_authoring._apply_difficulty_report`
  (learner_report), `rung_variants.request_rung_variant`
  (rung_variant_request), `learner_profile.seed_global_learner_claim`
  (init_wizard, global; the sidecar's `set_learner_profile` passes the
  vault's gate, bootstrap keeps the default since a new vault has no claim to
  replace). `keep_replaced = mastery.replaced_claims_kept(vault)` = version in
  `SUPERSEDED_CLAIMS_VERSIONS`.
* **Live readers are unchanged**: `Repository.learner_claims()` returns only
  rows with no `superseded_by` (filtered in Python, so a database attached
  below 225 still reads), which is exactly the set the predecessor's delete
  left. The three raw-SQL readers filter the same way: the AD replay's claim
  events (`adaptive_difficulty/replay.py`, column-guarded), the router card's
  self-reports (`daily_plan/router_card.py`), and the field's frozen priors
  (`field/priors.py`).
* **Replay** (`substrate/replay._ClaimStream`) reads every covering claim,
  replaced ones included (`covering_claims(..., include_superseded=True)`),
  places each at its own point (its recorded `applied_after_attempts`, else
  `(created_at, id)`), and re-anchors each re-anchoring one there, as live
  did. At any point the claims in force are the claims made by then minus
  those whose replacing claim was also made by then (`mastery._in_force`):
  the seed before the first attempt, each zero-evidence re-seed, and the
  re-review F8 variance retention (each anchor reads the claims in force at
  its own point, so a replaced anchor still counts the variance it left) all
  read that. The replacing claim is applied after the claim it replaces: the
  replacement, its application position and its re-anchor are one
  transaction (`mastery.replace_claim_and_reanchor`, Codex review F1), and
  replay places it after that claim whatever its stamp and id say
  (`mastery.after_what_they_replaced`, review F2: a stamp has second
  resolution and a ULID is monotonic within one process only). Live
  (`claims_made is None`) seeds the mean from the claims in force, unchanged,
  and reads every claim on record for the retained variance (review F3).
  Codex review and fixes: `docs/reviews/lp-learner-report-superseded-codex-review.md`.

Below the tag nothing writes `superseded_by`, so replay reads exactly what it
read before at every older version (the strict xfail stays xfail there).

## Successor mvp-0.36

`SUPERSEDED_CLAIMS_ALGORITHM_VERSION = "mvp-0.36"`, appended to
`SUCCESSOR_CHAIN` after Reader CA2's mvp-0.35 (one constant; the upgrade, the
CLI and the gates read it). `SUPERSEDED_CLAIMS_VERSIONS` is the gate.
Defaults snapshot `mvp-0.36` recorded (no default changes; only the version
string moves the fingerprint). Upgrade `learnloop upgrade --to mvp-0.36` (the
bare upgrade's default now): `learnloop.superseded_claims_upgrade`, the same
journalled activation as mvp-0.33 to mvp-0.35 (one `BEGIN IMMEDIATE`,
manifest, `activate_p0_projection`, registry refresh, journal, publication
last; the chain's completion is now this module's, installed by the CLI and
the sidecar, handing earlier journals down the chain). It accepts mvp-0.35
and mvp-0.9 to mvp-0.34 through the chain.

**No kill switch** (decision for the owner's checkpoint, see open questions):
no live decision changes; a replaced row is read by replay only; switching
replay back would only restore a known rebuild/live divergence. The
playbook's kill-switch rule (mvp-0.27) is for changes to what is served or
admitted; this changes what replay can derive.

**What the activation moves: nothing.** A claim the predecessor replaced was
deleted and cannot be recovered, and no row is `superseded_by` at activation,
so the activation's rebuild derives what the predecessor's derived (tested:
only the row label differs). What changes is every later rebuild of an LO
whose claim is replaced from the tag on.

**Also recorded under this tag.** The AD guard offer-receipts fix (main
cdd0a3c4f) restored AD serving in place, without its own tag, on vaults
holding an answer picked from a published offer. It was accepted by the
orchestrator's ruling under the owner's proportionate bar; see
`docs/reviews/ad-guard-offer-receipts.md` §10.

## Tests

* `tests/test_rebuild_equivalence.py::test_a_second_learner_report_on_an_lo_after_an_attempt_rebuilds_to_live`:
  strict xfail kept at mvp-0.33, mvp-0.34 and mvp-0.35; passes at mvp-0.36
  (and the latest).
* `tests/test_learner_report_superseded.py` (new):
  * the seam: a second report keeps the first as a replaced row no live reader
    reads; below the tag (mvp-0.33, mvp-0.35) the seam still deletes; a
    rung-variant request replaces only its own source on its own LO (0/0/0);
    two rung requests on a cold LO, then an attempt (0/0/0, rebuild == live;
    each request also writes a self-report attempt, so this is not the
    attempt-free case: that one is Codex review F3's test); the field's frozen priors read the same with
    the replaced row kept as with it deleted;
  * the starting level: an LO first practised under the bootstrap level
    rebuilds to live after the level changes (replay reads the replaced
    claim);
  * **property**: 24 seeded random histories of attempts (independent, hinted,
    primed, "I don't know"), `too_easy` retirements, rung-variant requests in
    both directions and tutor gap declarations, each history with at least
    one replaced learner_report or rung-variant claim (asserted; a closing
    replacement is added when the random part has none), then a primary load:
    shadow rebuild 0/0/0, and an applied rebuild (twice) leaves mastery exactly
    as live. The same generator at mvp-0.35 fails on all 24 seeds (checked once
    by hand, not committed), so the property is not vacuous;
  * the chain: one constant after mvp-0.35 and the latest, snapshot; upgrade
    from mvp-0.9, 0.30, 0.33, 0.34, 0.35; the bare upgrade targets it; refusal
    of mvp-0.8 and of a second upgrade; the activation derives what the
    predecessor derived; a real death after the publication (forked process),
    every opener completes an interrupted activation, every attach refuses
    without a completer, the upgrade completes its own journal, a failure after
    the rename leaves the predecessor, an mvp-0.35 journal is handed down, a
    torn journal is removed.
* `tests/test_learner_claim_superseded_migration.py` (new): 225 adds the
  column and nothing else; the head fixture holds 225 in rollback mode;
  durability lane.
* Head fixture renamed `migration_head_224` -> `migration_head_225`, rebuilt
  from the tracked sanitized copy with only 225 applied (README section);
  every hard-coded path and head pin updated (tests, `scripts/`, the two DB
  reference scripts, `SCHEMA_HEAD = 225`).

## Found here, not fixed (separate class)

`test_a_global_claim_made_after_materialization_rebuilds_to_live` (strict
xfail at mvp-0.35 and mvp-0.36): a claim that never re-anchors (an
init-wizard starting level, a manual claim) made after an LO's mastery row
was materialized (every LO is materialized at the vault's first sync) leaves
the live row as it was, while replay seeds the LO from the claims in force at
its first attempt, and an attempt-free LO from the claims in force at
rebuild time. Pre-existing and independent of the replace seam (one claim,
no replacement, reproduces it). It is why the property test does not change
the starting level; the starting-level test asserts only the LO practised
before the change. Fixing it needs the materialization point (or a
re-anchor for global claims), a separate successor.

## Gate (this stage; the full suite runs once at landing)

Every pytest inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p
MemorySwapMax=1G`; no frontend or `src-tauri` change, so no npm/vitest/cargo.

* `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`.
* `uv run lint-imports --no-cache`: 36 kept, 0 broken (the new module is in
  the experiments-isolation contract's source list).
* Targeted pytest, 148 files (`-n 6`, behind `flock
  /tmp/learnloop-fullsuite.lock`): every test file added or changed, every file
  that names the changed modules or functions (learner_claims, the claim
  seeds and re-anchor, replay, retire_item, rung-variant requests, the
  learner profile, field priors, the router card, AD replay, the upgrade
  chain, activation journal), the files naming the head fixture, and the
  contract tests (architecture, CLI help snapshot, config defaults
  snapshot/config refactor, coordinated migrations, desktop RPC contract,
  mobile allowlist, public-tip guards, table_roles, tracked fixture databases,
  AD protected tables, sidecar serializer snapshot and contract, sqlite file
  copies, e0 isolation): **8535 passed, 10 failed, 17 skipped, 6 xfailed**
  (42:40). The 10: 7 chain pins that compare a version set to an explicit
  set ending in `LATEST_ALGORITHM_VERSION`, fixed after (below), and 3 in
  `tests/test_codex_lockdown_round2.py`, the known Codex CLI 0.164.0
  environment break (fail on main too; another stage fixes them).
* Rerun of the 9 files with failures (`-n 4`): 207 passed, 4 failed (the 3
  Codex lockdown + `test_recurrence_commands.py::test_successor_vocabulary`,
  fixed after), then `tests/test_recurrence_commands.py`: 47 passed.
* Durability: `-m durability` on the migration tests touched
  (`test_learner_claim_superseded_migration.py`,
  `test_learner_claim_application_migration.py`,
  `test_section_coverage_migration.py`, `test_reader_ca2_fix_orchestrator.py`,
  `test_migrations.py`): 3 passed; `--durable-sqlite
  tests/test_learner_report_superseded.py`: 50 passed, 2 xfailed.
* DB reference: `db_generate_reference.py` then `db_validate_reference.py`
  (errors: []), at `SCHEMA_HEAD = 225`.
* CLI help snapshot regenerated inside pytest (only `upgrade` changed).

No paid or live calls: every script outside pytest ran under `env -i` with
empty HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR; no owner-vault copies (none
in this stage); synthetic helpers.py vaults only.

## Landing onto main (2026-10-27)

Landed in `learnanything-ad1` on `lp/learner-report-superseded` (stage tip
`dcd1e9429`, base `5c6a0834f`) by merging `main` at `cdd0a3c4f`, which adds
the Codex CLI 0.164.0 lockdown fix (`b49ca63bb`) and the AD guard
offer-receipts fix (`cdd0a3c4f`). Main was neither fast-forwarded nor pushed.
This stage lands first and keeps migration 225 and `migration_head_225`.

### Commits and conflicts

| Commit | What |
|---|---|
| `436b3cec9` | `--no-ff` merge of `main` `cdd0a3c4f`. **No conflicts.** The AD column classes already classed `learner_claims.superseded_by` as a read column of `learner_claims` (`column_classes.py`), so main's new reachable-reads scan (`tests/test_ad_guard_reachable_reads.py`, `tests/ad_reachable_reads.py`) accepts the new column and the replay's in-force read (`WHERE superseded_by IS NULL`) as merged. In a targeted run of the reachable-reads scan, the offer-receipts tests, the migration-225 test, `test_learner_report_superseded.py` and the 0.164.0 lockdown tests: 86 passed, 2 xfailed (the stage's known strict xfails). |
| `a38bfd722` | DB/config reference regenerated (`db_generate_reference.py`, then `db_validate_reference.py`: **errors []**). The real changes are citations: `ai/providers/codex.py` line numbers moved by `b49ca63bb`, `learner/mastery.py` line numbers, and test lists that now name main's new AD guard tests. The other ~425 note changes are `source_commit` stamps. |
| `a866c0649` | The mvp-0.36 version note (the `algorithm_versions.py` comment and this record's "Successor mvp-0.36" section). It names the AD guard offer-receipts fix (main `cdd0a3c4f`): that fix restored AD serving in place, without its own tag, on vaults holding an answer picked from a published offer, and the orchestrator's ruling accepted it under the owner's proportionate bar (`docs/reviews/ad-guard-offer-receipts.md` §10). After this commit, regenerating the reference changed only `source_commit` stamps, so that churn was discarded. |

Against main, the diff adds **no tracked database or binary other than the
head fixture rename** (`git diff --numstat -M main` lists only
`fixtures/{migration_head_224 => migration_head_225}/state.sqlite`). The root
`.gitignore` is unchanged and nothing under `fixtures-local/` is tracked.

### Regeneration

- DB reference: regenerated as above; 0 validation errors.
- CLI help snapshot, sidecar serializer snapshot, desktop RPC contract,
  embedding recipe pins, and the config defaults snapshots and fingerprints
  (`test_config_refactor.py`) all pass as merged (62 passed). Main changed no
  default, CLI command or RPC, so none was regenerated. The template `.pyc`
  was cleared before the full suite.

### Gate (at `a866c0649`; `env -i` with empty `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`, `TMPDIR`; logs in `fixtures-local/landing/logs/`)

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`, 5G scope; `lint-imports --no-cache` | **36 kept**, 0 broken |
| full suite (`flock`, 10G/2G scope, `pytest -n 8 --dist worksteal --durations=50 -o faulthandler_timeout=600 --junitxml`) | **22,188 passed, 0 failed**, 89 skipped, 44 xfailed. pytest time 2,367.5 s (39:27); wall time 39 min 31 s, after a 7-minute wait for another stage's lock. No faulthandler dump and no hang. All 10 Codex lockdown tests pass with main's fix. No flake fired, so nothing needed a rerun. |
| durability (`-m durability`, same wrapper and scope) | **139 passed**, 1 skipped (57 s) |
| owner lane (`-m owner_vaults`, fresh backup-API copies of `fixtures-local/owner-copies-mvp035/{linear_algebra,probability,arxiv_v2}` in `fixtures-local/landing/owner-lane/`) | 80 passed, **9 failed**: the **6 known** (`test_doctor` pre-044, `test_migrate_fresh` 153, `test_goal_decay_projection`, `test_sidecar_contract` recent ingests, `test_activity_backfill`, `test_placement_fixture_copies[arxiv_v2]`), plus 3 on the probability copy: `test_daily_plan_kill_switch::test_plan_off_is_dl0_on_fixture_copies`, `test_field_workbench_signals::test_g41_off_is_the_predecessor_on_fixture_copies` and `test_router_r2a_serving::test_switch_off_at_the_successor_serves_the_predecessors_plan_on_fixture_copies`. **The same 9 fail on main**: main's own tree (`git archive cdd0a3c4f`), run with `PYTHONPATH` on its own fresh copies, also gave 80 passed and 9 failed. The 3 are data-dependent and come from the owner's recent use of probability, which these copies hold: 2 daily plans with 3 blocks, and a real `workbench_stuck` session. They are not from this stage. |
| frontend / Tauri | not run: the merge touches nothing under `apps/` |

### Parity (fresh backup-API copies of `fixtures-local/owner-copies-mvp035/*`, all three at mvp-0.35 on main's code; `fixtures-local/landing-lrs/`, scripts in `scripts/`)

Setup: `base/` holds the copies. Routes go to the `127.0.0.1:9` blackhole (65
tasks, none elsewhere apart from the opt-in `embedding` route, which is off
and has no key in the environment). `code_main` is `git archive cdd0a3c4f`
and `code_branch` is `git archive a866c0649`. Every run went through `env -i`
with empty dirs. `run.py`'s audit hooks refuse Codex process starts and
non-loopback sockets; no audit line was written.

- **(a) main vs branch at mvp-0.35, no upgrade** (after a primary sidecar load
  at a frozen clock; a second main copy is the noise control). Every row of
  all 358 tables is identical: 18,810 rows in linear_algebra, 10,297 in
  probability, 23,710 in arxiv_v2. The branch adds only
  `learner_claims.superseded_by` (all NULL), its table SQL, and
  `schema_migrations` +225 (common rows identical). Integrity ok; foreign
  keys 0. `rebuild --shadow` is **0/0/0** on both sides. `doctor` is
  identical: linear_algebra 57 issues / 1 error (`layout:missing_directory`),
  probability 102 / 48 (46 `criterion:unknown_dependency`, 2 `yaml:invalid`),
  arxiv_v2 76 / 47 (46 `criterion:unknown_dependency`, 1
  `layout:missing_directory`). All are the known content errors.
- **(b) `upgrade --to mvp-0.36`, then `rebuild-derived-state`** (branch code).
  The upgrade prints "Upgraded vault: mvp-0.35 -> mvp-0.36" and leaves no
  journal.
  - **Mastery and schedules: 0 LOs and 0 items moved**, both after the
    activation and after the rebuild, on all three vaults.
  - **Rows: every row kept.** On a normalized comparison, the only changes
    are the version stamps (`algorithm_version` on the DERIVED rows, plus the
    version labels inside `attempt_debug_payloads.payload_json` after the
    rebuild), the projection activation's facet-row timestamps, the
    `parameter_registry` refresh (352 rows), and the added receipts (+1
    `derived_state_rebuilds`, +1 `parameter_registry_manifests`, +225 in
    `schema_migrations`).
  - The rebuild also appends ledger backfill rows (`activity_observations`,
    `grade_interpretations`, `raw_grade_events`, `measurement_events`:
    38/38/38/152 in linear_algebra, 3/3/3/12 in probability, 2/2/2/8 in
    arxiv_v2). **Main's own `rebuild-derived-state` at mvp-0.35 appends
    exactly the same rows** (control copy). FTS content is identical.
  - Shadow right after the upgrade: facet 0, schedule 0, mastery 21 / 18 / 34
    = **the `algorithm_version` stamp only**, as at the mvp-0.35 landing.
    After the rebuild: **0/0/0**. Doctor unchanged.
  - **Live** (a primary load, then 12 self-graded attempts at a frozen clock,
    with two `too_easy` retirements on one LO after attempts 3 and 7):
    - linear_algebra, `lo_compute_with_complex_numbers`: claims on the LO
      went 2 -> 3, with 1 `superseded_by`.
    - probability, `lo_count_compound_and_ordered_outcomes`: 1 -> 2, with 1
      superseded.
    - arxiv_v2, `lo_render_a_classifier_s_decision_regions`: 2 -> 3, with 1
      superseded.
    - `rebuild --shadow` afterwards: **0/0/0 on all three**. The first try of
      this script did not run on linear_algebra and arxiv_v2: it grouped
      candidate items by practice mode, and it treated an empty
      `attempt_types_allowed` (which allows every type) as disallowed.
      Corrected, it was rerun on fresh copies of the upgraded vaults.
- **(c) an interrupted mvp-0.36 activation** (the upgrade dies with
  `os._exit(17)` after the config publication), on all three vaults. The
  vault is left with label mvp-0.36, the journal present, and mastery
  untouched.
  - `upgrade --to mvp-0.36` completes it ("completed the interrupted
    activation of mvp-0.36"); run again, it says "vault is already mvp-0.36".
  - The desktop start (`SidecarContext.load`) completes it.
  - Both equal the clean upgrade (0 LOs moved).
  - Every attach that may not complete it refuses with "The upgrade to
    mvp-0.36 did not finish ... run `learnloop upgrade --to mvp-0.36`" and
    leaves the vault as it was: `Repository`, `open_vault_repository` without
    a completer, and the secondary attach raise `InterruptedActivation`; the
    remote schema check raises `SchemaMismatch`. The upgrade then completes it.
  - Plain `doctor --json` is a read-only attach and refuses too (the journal
    stays), as recorded at the earlier landings.
- **(d) `ad report --json`: no new denials.** Before the upgrade, after it,
  and after the live run, the guard denials are linear_algebra 0/0/0,
  probability 6/6/6 and arxiv_v2 0/0/0. Probability's 6 are the historical
  lines in its `ad_guard_denials.jsonl`, unchanged in length.
- **Receipts and calls.** 0 `model_call_receipts` rows were written by any
  run. Linear_algebra and arxiv_v2 copies hold 0. Every probability copy
  holds the same 56 historical receipts as its source (the owner's use on
  Oct 25-26, latest `2026-10-26T18:30:28Z`). The empty `HOME`, `CODEX_HOME`
  and `LEARNLOOP_CONFIG_DIR` stayed empty. **Spend: $0.** Nothing under
  `~/learnloop-vaults`, `~/learnloop-retired` or `~/learnloop-books` was
  opened or listed.

### Owner notes

- Back up each vault, then close the desktop app, MCP and the phone page.
- Run `learnloop upgrade --to mvp-0.36` (the bare `upgrade` now targets
  mvp-0.36). It accepts mvp-0.35 directly and mvp-0.9 to mvp-0.34 through the
  chain.
- Nothing learner-visible moves at the activation (0 LOs, 0 schedules on all
  three copies). From the tag on, a second learner report on an LO keeps the
  replaced claim as a `superseded_by` row instead of deleting it, so replay
  agrees with live.
- If an upgrade is interrupted, rerun the same command or open the desktop
  app.

### Open items (carried from the stage)

- **Kill switch:** none ships (the stage's reasoning is that no live decision
  changes). This is the owner's checkpoint question.
- **Deleted pre-0.36 claims are unrecoverable.** Claims the predecessor
  replaced were deleted, and replay cannot apply them. An optional ledger
  reconstruction is a possible follow-up.
- **Strict xfail:**
  `test_a_global_claim_made_after_materialization_rebuilds_to_live`. A global
  claim made after an LO's materialization does not re-anchor the live row.
  This is pre-existing and needs its own successor.
- **Cross-source claim order at one point:** two re-anchoring claims from
  different sources on one LO, in the same second, at the same attempt count,
  written by two processes, replay in `(created_at, id)` order, which can
  invert. Closing it needs a transactional application-sequence successor.
- **Migration 225 clash:** phone PR-3/PR-4 (`learnanything-merge2`) also built
  a migration 225 and `migration_head_225`. This stage lands first and keeps
  225; PR-3/PR-4 must renumber theirs (226+) and rebuild their head fixture
  from this one.
