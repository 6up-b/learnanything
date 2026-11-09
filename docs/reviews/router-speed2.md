# Router speed, stage 2 (`router/ro-speed2`)

Base: main `e9ceaf8d44` (TE3b at mvp-0.53, migration head 249).

**No successor and no migration.** At a fixed number of draws every served value, logged probability and trace
field is main's for the same inputs: nothing here changes what is computed, only how often it is computed and how
its reads are opened. The equality tests put main's code back beside the new one (copied verbatim, or the same call
made with the new mechanism switched off) and compare bit for bit. Nothing moved onto the serving path. **Corrected
by the Codex review (F2, `router-speed2-codex-review.md`):** serving refines until the LLM answers or the deadline
runs out, so faster input builds complete more draws by the same deadline and can change a deadline-bound choice.
Both items are therefore serving changes behind their own kill switches, `[router_objective] held_reading_map` and
`pooled_connections` (default on at the follow-up batch's tag, in RO6's generator payload, the trace's
`versions.serving_switches` and the prefetch key, as router speed's `held_ad_link`); off serves main's code exactly.

**Superseded at the landing (rulings R1-R4, "Landing onto main" below):** item 1's map is no longer held across
calls. It is held only within one objective job, as a snapshot as of the job's first read, and nothing digests stored
rows any more (R1). The numeric seed excludes both switches (R2). A pooled connection on which anything but reads ran
is closed at release (R4). The sections below describe the stage as built before those rulings.

Fakes only. No paid call, no model request. No owner vault or tracked working vault was opened. Every measurement is
on a synthetic vault under the worktree's `fixtures-local/rospeed2/`, run under `env -i` with an empty `HOME`,
`CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

## For the owner

- **Nothing to upgrade.** No version moves, no migration. Two new kill switches (Codex review F2), both on by
  default: `[router_objective] held_reading_map` and `pooled_connections`; RO6's generator changes once when the new
  code first serves (a change point). Restart the desktop app and the phone host to pick up the faster code.
- **Paid routes: none added.** No model request, no learner minutes.
- **Speed**: see "The target". The landing's pinned linear_algebra week should be timed again on the copies at the
  landing gate's smoke (the synthetic vaults reproduce the regime, not the copies' exact sizes).
- **A reviewer of AD's protection layer is asked for** (item 1 adds a reader to `MaterialView` and holds AD's reading
  map across operations): see "For the reviewer of AD's protection layer".

## Commits

| Commit | Item |
|---|---|
| `e5c7bc7386` | 1: AD's section → LO map (and the span → section map, and the view's section spans) held across calls |
| `8685acc889` | 4: SQLite connections reused within one objective job |
| `283405f0a5`, `6dc3a82c6e` and this record | the review file and a follow-up to item 1 (held maps made read-only proxies); the regenerated references |

Items 2 and 3 were not built as written (why, and what stands in for them, below). Item 5 was not built.

## How the vaults mirror the copies

`mkvault.py` (scratch) builds RO6's journey vault (`create_daily_plan_vault`, the seeded ~70% learner of
`test_ro5_calibration._grade_answers`, one day a week off, both policies answering through the inline fakes with
the pinned block-drawing seed) and adds what the stage-1 journeys lacked and the copies have: **Reader sources**,
seeded through the tests' own IR persistence (`source_service_fakes.seed_textbook`), every LO citing spans of them
in its provenance (span locators and one quote each, the Reader's two ways of citing), and, before every session,
completed sections (`reader_section_progress`) and span views (`source_exposure_events`, context `reader`).

| Shape | Topics x items | Sources | Days | Reading a day | At the end |
|---|---|---|---|---|---|
| linear_algebra-shaped (`la`) | 16 x 8 (stage 1's) | one textbook, 80 sections x 20 blocks (1,680 blocks) | 14 | 3 sections, 8 span views | 79 traces, 217 attempts, 36 completed sections, 96 views, 114 reading receipts |
| arxiv_v2-shaped (`ax`) | 22 x 4 (stage 1's) | eight papers, 12 sections x 15 blocks each | 8 | 2 sections, 4 views | 54 traces, 143 attempts, 14 sections, 28 views |

Before this stage the `la` vault reproduces the owner's regime and exceeds it: the join runs twice a job (a fake
receipt commits between the builds, as a real one does), AD's section map dominates the join, and a job opens about
900 connections (the copy's profile: 462).

`measure.py` (scratch) copies a template with the backup API, runs three more days (reading first), and times every
objective job (dwell 0: what a Next at a block boundary right after feedback waits for): the job, the moment the
numeric answer is ready (the serve's wait ends there), the input builds, the join, AD's section map, RO2's resolve,
the decision card, AD's decision state and the SQLite opens. The same script ran on `git archive`s of main and of
each commit, one after another, behind `/tmp/learnloop-fullsuite.lock` on an otherwise quiet machine.

## The time table (before and after each item)

Per objective job, median over every job of three journey days (`la`: 19 jobs, `ax`: 27), in ms. "Numeric ready"
is when the job's numeric answer is published (the serve's wait for it ends there; the rest of the job is the carried
valuations RO6 defers until after it). "Builds" is both input builds (the card's and the numeric policy's), "join"
both joins, "numeric" the numeric policy including its own build. Load average 0.7-1.2 throughout.

| Shape | Code | Job (p90) | Numeric ready | Builds | Join (alone, as of the end) | RO2 resolve (of it: opportunities) | Numeric | Card | AD state | SQLite opens a job |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `la` | main `e9ceaf8d44` | 4775 (5059) | 4567 | 3719 | 3362 (1703) | 3267 (3181) | 2422 | 215 | 185 | 908 |
| | item 1 `e5c7bc7386` | 1717 (1905) | 1463 | 584 | 225 (113) | 145 (68) | 894 | 216 | 184 | 94 |
| | **item 4 `8685acc889`** | **1396** (1542) | **1125** | 320 | 156 (115) | 129 (51) | 739 | 204 | 148 | **5** |
| `ax` | main | 2764 (2896) | 2521 | 1796 | 1399 (713) | 1324 (1249) | 1459 | 107 | 185 | 436 |
| | item 1 | 1751 (1890) | 1478 | 731 | 326 (165) | 248 (193) | 944 | 111 | 192 | 142 |
| | **item 4** | **1247** (1312) | **999** | 303 | 134 (169) | 110 (56) | 690 | 101 | 150 | **5** |

- **linear_algebra-shaped**: the job is 71% shorter (4775 to 1396 ms), the numeric answer ready 75% sooner (4567 to
  1125 ms). AD's section map: 84 section and 192 span calls a job, 3.1 s before, 12 ms now.
- **arxiv_v2-shaped**: the job is 55% shorter (2764 to 1247 ms), the answer ready 60% sooner.
- The journeys are pinned (block-drawing seed) but their rollout seeds name the run's decision ids, so the three
  codes serve comparable, not identical, journeys; their values are compared in the equality tests, not here.

## The target

The landing measured Next at a boundary right after feedback on the owner's linear_algebra copy at 3.3 s median (the
job's length: Next waits for it) against mvp-0.49's 2.2 s; the target is about 2.4 s.

- On the synthetic `la` vault, which before this stage was heavier than the copy in the join (4.8 s a job against
  the copy's 3.3 s), the job is now 1.4 s and the answer ready at 1.1 s.
- **On the copy, by its own profile** (per job: builds 1.69 s, of which the join 1.18 s, with AD's section map about
  0.9-1.25 s and RO2's resolve about 1.0 s cumulative; 462 opens costing 0.82 s; the numeric policy 1.71 s, its
  rollouts about 1.2 s): item 1 takes the section map and most of the resolve out of both joins, item 4 the opens.
  The synthetic vault kept about 4% of its join and 9% of its builds. Applied to the copy, the builds fall from 1.69
  s to about 0.3 s and the opens from 0.82 s to nearly nothing, so the job falls from 3.3 s to about **1.6-1.9 s**:
  within the target, below mvp-0.49's 2.2 s. **This is an estimate**; the landing gate's smoke should time the
  pinned week on the copies (R5's table) to confirm it.
- What a job is made of now (`la`, the profile below): the rollouts (about 0.6 s, item 5), the carried valuations
  after the answer (about 0.3 s, off the serve's wait), the two builds (0.3 s: the join, AD's decision state and its
  replay, about half each), the decision card (0.2 s).

## Item by item

### 1. AD's section → LO map, held across calls (`adaptive_difficulty/reading_cache.py`)

**Before.** `VaultReadingMap` was built afresh at every call of RO2's opportunity resolve (twice a job), of the
sweep and of the rollouts' reading action (once per reading candidate per build). Every section it mapped re-read the
reading's run, revision and source (three connections), walked every LO's references over the section's blocks
(quote matching normalizes every block's text), and every viewed span recomputed its section's mapping from scratch
(`learning_objects_for_span_in_ir` per span, not per section). Each map loaded the IR once more through the
chokepoint, and each operation's view loaded it again for its section spans.

**Now.**
- A section's LOs, a reading's span → section map, and the view's section → spans map are held process-wide, keyed
  by:
  - the database (resolved path) and **the vault object** (the raw vault an operation projects; held weakly, and a
    reloaded vault is another object);
  - the operation's **protection epoch** (`MaterialView.epoch`: equal epochs mean equal projections, so an exam
    reservation, a held-out span or a withheld reading is a new key);
  - a **digest of the vault content the mapping reads** (each LO's id, status, references, its blueprints' facets
    with their canonical ids and references, each note's canonical source), so an in-place edit is a new key too;
  - a **digest of every stored row the mapping reads** (`MaterialView.reading_structure_digest`, new): every
    reading's, revision's and source's metadata, the stored structure (units, blocks, assets) of every reading of
    the same source that the withheld material does not touch, and the aliases recorded onto the reading. Read in
    one read transaction, in the rules' derivation scope (where `document_ir` reads the structure), never a
    withheld reading's rows. Every cell is encoded injectively (TEXT by the hex of all its bytes since Codex review
    F3, reals to 17 digits, anything else by `quote`).
  - the reading and the section.
- **The withheld rule is never held.** `los_for_section` and `los_for_span` ask the map's own operation view at every
  call, before any held value is read, exactly as before; a withheld reading has no digest, so nothing of it is held
  or read.
- **A value is held only if its key is still current after its computation**: the whole key is read again after the
  reading's first mapping in a map (the IR is loaded once per map, between the two reads), the metadata and aliases
  again after each further one. A source write landing mid-map is therefore never held under the earlier key (two
  tests, with a negative control). A failed mapping (no IR, an unreadable extraction, a guard refusal) is never held.
- **A lookup re-reads the metadata first** (Codex review F1): main reads a reading's run, revision, source and aliases
  at every mapping, so before every section or span the landing code would compute, the map reads the metadata and
  aliases part of the key again; once it changed, that reading is mapped by the landing code's own calls (over the
  IR the map loads once) for the rest of the map, and nothing more of it is held.
- `los_for_span` now maps the span's section through the held span → section map and the same section mapping:
  `learning_objects_for_span_in_ir`'s two steps, unchanged.
- Bound: `_HELD_LIMIT` (4096), a keep bound in the parameter registry (module `ad_reading_cache`).

**AD's guard and the walk.** Every IR load that still happens is inside `MaterialView.document_ir` (a hit loads
none); `tests/test_ro2_ad_raw_document_reads.py` passes unchanged (the walk sees `VaultReadingMap.los_for_section`,
`learning_objects_for_section_in_ir` and the new methods, none calling a raw loader). The digest's reads are the
rules' (a `MaterialView` method, derivation scope, rules marker), on a hooked connection: the item 1 tests run every
state in the guard's deny mode with zero denials.

**Tests** (`tests/test_rospeed2_section_map.py`, 6): main's `los_for_section` / `los_for_span` copied verbatim run
beside the held map in a real read-only AD operation, every section and span of a textbook and a re-read of it
(LOs citing by locator on both readings, so the alias authority runs, and by quote), compared at:
- nothing withheld (the second held pass computes no mapping and loads no IR);
- a held-out span (the reading withheld), released again (the earlier values, from what was held);
- a withheld re-read; an exam reservation;
- a block's text edited in place (the IR rewritten); a new reading of the book; a manual alias onto it;
- an LO's references edited and the vault reloaded; the same kind of edit made in place on the loaded vault.
Plus: a failed mapping is not held; a source write committed mid-map (the IR before the map loads it; an alias during
its third mapping), then undone so the earlier key is current again, never serves a value computed from the written
rows (both fail with the check switched off); RO2's opportunity resolve over completed sections, span views and an
anchored question gives main's rows, also after a protection change.

### 2. RO2's opportunity resolve: not built as written

After item 1 the opportunity resolve's mapping is held, and what is left of `_opportunities` is the uncapped
collectors' reads through the view (about 25 ms a call on the `la` vault, from about 1.7 s).

- **Why not cached per decision.** "The same invalidation discipline" is the decision scope's commit version, which
  the receipt committing between the job's two builds moves (item 3), so a per-decision hold would serve only builds
  that no commit separates: none, in a job that asks a model.
- **Why not cached by a fingerprint.** An exact fingerprint must cover every row the collectors and the view's
  filters read (the six source tables, the receipts, the administrations, and whatever the registry's rules resolve
  for each row). The guard records those tables per operation, but a fingerprint of them reads the same rows the
  resolve reads, so it would cost about what it saves.
- **What stands in.** Stage 1's indexing of `_resolve_groups` stays; item 1 removes the mapping; item 4 removes the
  connection opens inside it.
- **The smallest finish**, if it is ever worth it: hold `_opportunities`' rows under the key of item 1 plus a digest
  of the rows of the reading-event tables and receipts (read in one transaction), verified after computing as item 1
  verifies, and keep the view's per-row rules outside the hold (run them on the held rows at every call).

### 3. The shared fit's invalidation narrowed to the join's tables: not built as written

- **Why.** SQLite exposes no per-table change counter across connections: `PRAGMA data_version` is database-wide and
  counts no commits (it only changes), and `total_changes`, the update hook and the session extension see one
  connection's own writes. So "which tables changed" is knowable in three ways only:
  - **triggers** writing a per-table epoch: a migration (a new table classified in `table_roles`, the AD guard
    admitting the trigger's writes inside operations, every migration-head fixture and reference updated) on a stage
    that expects none, while phone V3 adds its own migration in parallel; it needs a ruling;
  - **the writers** bumping an epoch: every writer in every process (the phone host and the desktop write the same
    database), with no way to tell another process's commit from the receipt's (a commit's version cannot be
    attributed: the watcher sees only that something changed);
  - **a content digest** of every table the join reads (attempts, presentations, AD's ledger and replay inputs,
    reveals, the reading tables, traces, checks...): about as costly as the join now is after item 1 (a full digest
    of the `la` database takes 69 ms; the join's share would be most of it on a copy).
- **What stands in.** Items 1 and 4 make the second join cheap: on the `la` vault a join went from about 1.86 s to
  about 0.1 s, so the second one per job costs about that. The fit is still read again after any commit, exactly as
  main (Codex review F2's guarantee is untouched).
- **The smallest finish**: a migration adding `table_write_epochs(name, epoch)` with insert/update/delete triggers on
  the join's tables (the set pinned by a test that records the join's reads through the AD guard's `reads` and a
  recording authorizer on the job's own connections), classified NEUTRAL/AD-writable for the triggers, and the
  decision scope comparing those epochs instead of `data_version`. It needs the owner's ruling (a schema change for
  speed alone).

### 4. Connection reuse within one objective job (`db.connection.reused_connections`)

**Before.** Every repository call and every AD reader opened its own connection; SQLite parses the whole schema (400
tables) at a connection's first statement, about 2 ms each, and a job opened 94 of them after item 1 (899 before; the
copy's profile: 462, 0.82 s).

**Now.** `_objective_job` opens `reused_connections()` around the job. Inside, every `connect()` made **on the thread
that opened it** is served by the scope's pool, one connection per database and mode:
- other threads (the model calls, which copy the job's context) open their own: no connection crosses a thread;
- a connection in use is never handed out again (a nested user gets its own);
- given back (`close()`, or the end of a repository `with` block, which closes it), it is reset as a fresh one: its
  cursors closed (no read snapshot outlives its user: a later reader sees every commit), any transaction its user
  left open rolled back (as closing discards it: no write lock is ever kept), the AD guard's authorizer and trace
  hook removed (the next operation installs its own through the connection hook, which expires every statement
  prepared before, so nothing prepared outside an operation runs unchecked inside one), its settings restored;
- an ingest job's guarded connections are never pooled; the decision scope's watcher is not pooled (R2's watcher is
  unchanged);
- the scope's end closes every idle connection.

**Tests** (`tests/test_rospeed2_connections.py`, 6): one connection per database and mode on the scope's thread,
another thread opening its own, nesting; the reset (closed cursors, settings, authorizer, an uncommitted write
discarded); a pooled connection inside an AD operation carries its guard (a DENIED read is refused) and nothing
after it; under the durability lane (WAL) a writer commits with no busy wait after a user left a write uncommitted,
and a pooled reader sees every commit since its previous user, even one whose user left a cursor mid-read; on a
journey's prefetch jobs, every input build, decision card and combiner fit recomputed with the pool switched off is
equal bit for bit; a job opens at most a handful of connections.

### 5. The arxiv_v2 rollouts: not built

On the `ax` vault after items 1 and 4 the numeric policy's rollouts are the largest share of a job
(the numeric policy 690 ms of a 1247 ms job, its own build about 150 ms of it). The profile's hot spots are stage 1's: `value._session` (about 4,300 calls a job), its
`_practice_batch`, `performance` → `_linked_logit`, and `memory.review` / `retrievability`, each a few microseconds
of numpy dispatch on small arrays. The smallest exact finish is to run each tail session's blocks for every
candidate's draws in one array (the candidates share the tail's structure and their draws are independent), which
keeps every elementwise operation and so every bit; it needs its own equality harness (stage 1's
`test_rospeed_ad_link.py` pattern) and is a stage of its own.

## The profile after (`la`, this branch, two journey days under cProfile, 14 jobs)

Cumulative per job (cProfile inflates every number; 2.04 s a job under it against 1.4 s without):

| Function | Per job | Note |
|---|---:|---|
| `objective_chooser._objective_job` | 2.04 s | |
| `run_numeric` | 1.11 s | its build included |
| `value.evaluate` / `run_tail` | 0.97 s | the rollouts, the carried valuations' included; `_session` 61k calls, `_practice_batch` 0.38 s |
| `objective_inputs.build` (2) | 0.64 s | |
| `_combiner_read` (2) | 0.33 s | the join; RO2's `_resolve_groups` 0.28 s, its `_opportunities` 0.10 s |
| `_ad` (2) / `readiness.decision_state_fields` | 0.29 s | AD's replay snapshot |
| `replay.load_events` (4) | 0.27 s | twice in the resolve, twice in AD's snapshot |
| `_drain_carry` | 0.30 s | after the answer is published |
| `objective_card.decision_card` | 0.26 s | |
| `db.connection.connect` (104 calls, pooled) | 0.02 s | before: 0.82 s on the copy |

Before (main, the same profile run in the session's first measurement): the job 6.3 s under cProfile, the builds
2.4 s each, `learning_objects_for_section_in_ir` 1,848 calls at 13 ms, 889 connection opens.

## For the reviewer of AD's protection layer

What item 1 adds to the protection layer, for review:
- `MaterialView.reading_structure_digest` (a new view reader) reads `source_extraction_runs`, `source_revisions`,
  `source_artifacts`, `source_span_reanchors` (rows onto the reading) and, for readings the withheld material does
  not touch, `source_document_units/blocks/assets`, in the derivation scope, in one read transaction. It returns a
  digest only; nothing it reads reaches a value.
- `MaterialView.section_spans` holds its section → spans map under that digest (no vault, no projection: the IR's
  alone), still none for a withheld reading.
- `VaultReadingMap` holds its section and span maps under the vault, the epoch and both digests; the withheld rule
  runs at every call before the hold is read.
- Questions for the reviewer: is the epoch a sufficient key for the projected vault (the epoch's contract: "equal
  epochs mean equal projections"; the vault digest is taken over the projected vault as well)? Is a digest over the
  same source's untouched readings and the aliases onto the reading the full set of stored rows the mapping can
  read (the alias authority computes aliases only between readings of one source; `span_aliases`' own memo, per
  epoch, is main's and unchanged)?

## The gate (this step)

The full suite, the whole durability lane and the whole vitest run belong to the landing gate. No frontend or
`src-tauri` file changed (no npm, vitest or cargo step), and no schema changed. DB/connection code changed
(`db/connection.py`), so its durability-marked tests ran.

| Step | What ran | Result |
|---|---|---|
| Setup | `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | ok |
| Import contracts | `lint-imports --no-cache` (under `env -i`), after each item | 43 kept, 0 broken |
| Item 1, iterating | the 32 test files naming the reading map, the reading sources or the material view, plus `test_rospeed2_section_map` and `test_ad_guard_reachable_reads`, `-n 6` | 9022 passed, 3 skipped |
| Item 4, iterating | `test_repository_scopes`, `test_sqlite_test_mode`, `test_sqlite_wal_lifecycle`, `test_sqlite_wal`, `test_sqlite_file_copies`, `test_rospeed_watcher`, `test_rospeed_join`, `test_ad_guard` | 181 passed, 1 skipped |
| Durability (`-m durability`) | `test_repository_scopes`, `test_sqlite_test_mode`, `test_sqlite_wal_lifecycle`, `test_sqlite_wal`, `test_rospeed_watcher`, `test_rospeed2_connections` (on the final tree) | 47 passed, 1 skipped |
| Targeted set | 102 files, `-n 6`, behind `flock /tmp/learnloop-fullsuite.lock` (list below) | **10486 passed, 5 skipped, 1 failed**: `test_module_catalog_inventory` (the new module's note not yet tracked, before the references were regenerated) |
| After the references | `test_module_catalog_inventory`, `test_public_tip_guards`, `test_rospeed2_section_map`, `test_rospeed2_connections` | all passed |
| References | `module_generate` / `module_validate` (PASS), `db_generate_reference` / `db_validate_reference` (errors []), `desktop_generate` / `desktop_validate` (passed), `validate_vault` (passed) | ok |

The targeted set: every test file naming a changed module or function (`VaultReadingMap`, `adaptive_difficulty.
reading`, `section_learning_objects`, `los_for_section`/`los_for_span`, `reading_sources`, `MaterialView`/
`material_view`, `reading_cache`, `reused_connections`, `objective_chooser`, `objective_inputs`, `_objective_job`,
`decision_reads`, `section_spans`); every `test_ro4_*`, `test_ro5_*`, `test_ro6_*`, `test_rofu_*` (but the weeks) and
`test_rospeed*`; the contract and audit set (`test_config_refactor`, `test_cli_help_snapshot`,
`test_sidecar_serializer_snapshot`, `test_desktop_rpc_contract`, `test_mobile_allowlist`, `test_architecture` with the
frozen cycles, `test_table_roles`, `test_coordinated_migrations`, `test_tracked_fixture_databases`,
`test_registry_audit`, `test_module_catalog_inventory`, `test_public_tip_guards`, `test_sqlite_file_copies`); the
display-label audit (`test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`,
`test_rw5c_labels`); the process-launch allowlist (`test_codex_lockdown_round3`, `test_ai_tool_isolation`,
`test_e0_isolation`, `test_codex_tool_lockdown`); the connection tests above; `test_ro2_ad_raw_document_reads`.

- Every test ran inside `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, at most `-n 6`, one run at
  a time. Every script outside pytest (the vault builder, the measurements, lint-imports, the reference scripts) ran
  under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, `TMPDIR` outside the worktree.
- The "before" timings ran `git archive`s of main `e9ceaf8d44` and of each commit in the scratch directory, on this
  worktree's venv.

## Files added or changed (for the landing gate)

- Added: `src/learnloop/adaptive_difficulty/reading_cache.py`, `tests/test_rospeed2_section_map.py`,
  `tests/test_rospeed2_connections.py`, this file.
- Changed source: `src/learnloop/adaptive_difficulty/reading.py`, `src/learnloop/adaptive_difficulty/material_view.py`,
  `src/learnloop/db/connection.py`, `src/learnloop/daily_plan/objective_chooser.py`,
  `src/learnloop/params/parameter_registry.py`.
- References regenerated (below).

Old item difficulty scalar (owner, Nov 5): `git diff e9ceaf8d44 -- src migrations` adds no reader or writer of it.

## Open items

- Items 2 and 3 (smallest finishes above); item 3's needs a ruling on a migration.
- Item 5, the rollouts (smallest finish above).
- What remains in a job besides the rollouts, each read at both builds: AD's decision state (`readiness.
  decision_state_fields`, its replay snapshot), the goals' scope (`facet_diagnostics.required_facets` reads the whole
  item-state table about 40 times a job on the `la` vault, now on one pooled connection), and the decision card.
- The copies' own numbers: rerun the landing's pinned linear_algebra week (R5's table) at the landing gate's smoke.

## Landing onto main

Landed by the continuation of the landing agent (the first was stopped by a usage limit on Nov 7). Merges: main
`ccb6573987` (phone V3) at the start, then main `5fe3a22558` (owner capture fixes: feedback screen and Reader open,
causal attribution and repositories for follow-up answers, the workbench help ladder and hints options; one frontend
change, `BookPassage.tsx`), then main `214c206ff1` (the owner's figure author fix: a figure author's bad prediction
costs that prediction, not the figure; both figure prompt versions bumped). The branch carries those owner commits to
origin, so this gate is theirs too.

### The time table

Pinned (`SMOKE_PIN_SEED`, `SMOKE_PIN_KEY`), one run at a time with the full-suite lock held, on fresh backup-API copies
of the mvp-0.43 backup upgraded to each code's tag. **These numbers come from the earlier tree (the branch at
`5a9dae936f`, main `ccb6573987`, both switches on);** the later merges (owner captures, figure author) touch neither
the router, the reading map nor the connection layer, so they were not re-measured. "Next after feedback" is Next at
a block boundary right after a feedback (dwell 0); the 3 s column is after a 3 s dwell.

| Copy | Code | Numeric policy per decision ms: median (p90, n) | Next after feedback, dwell 0: median / p90 / above 2 s | Next after a 3 s dwell: median / p90 / above 2 s | Follow-up gate ms, median (n): objective-decided / no room to wait |
|---|---|---|---|---|---|
| arxiv_v2 | mvp-0.49 (e7a7d7734f) | 1318 (1386, 12) | 2207 / 2207 / 1/1 | 577 / 577 / 0/1 | 750 (2) / None (0) |
| arxiv_v2 | main (ccb6573987) | 2386 (2563, 10) | 3394 / 3430 / 2/3 | 864 / 890 / 0/3 | None (0) / 194 (2) |
| arxiv_v2 | branch (both switches on) | 2366 (2494, 10) | 2954 / 3016 / 2/3 | 780 / 873 / 0/3 | None (0) / 195 (2) |
| linear_algebra | mvp-0.49 (e7a7d7734f) | 674 (997, 10) | 1988 / 2400 / 1/3 | 671 / 682 / 0/3 | None (0) / 194 (2) |
| linear_algebra | main (ccb6573987) | 1896 (2224, 10) | 2853 / 3948 / 2/3 | 731 / 856 / 0/3 | None (0) / 231 (2) |
| linear_algebra | branch (both switches on) | 1657 (1899, 10) | 1636 / 2864 / 1/3 | 743 / 799 / 0/3 | None (0) / 199 (2) |
| probability | mvp-0.49 (e7a7d7734f) | 200 (217, 10) | 1125 / 1146 / 0/3 | 728 / 758 / 0/3 | None (0) / 173 (2) |
| probability | main (ccb6573987) | 612 (684, 10) | 2154 / 2265 / 2/3 | 792 / 804 / 0/3 | None (0) / 177 (2) |
| probability | branch (both switches on) | 202 (323, 11) | 1021 / 1021 / 0/1 | 821 / 871 / 0/3 | 872 (1) / 177 (1) |
| linear_algebra, a week | mvp-0.49 (e7a7d7734f) | 744 (1075, 60) | 2250 / 2689 / 25/30 | - | 751 (9) / 229 (19) |
| linear_algebra, a week | main (ccb6573987) | 1632 (2089, 41) | 3685 / 4558 / 20/21 | - | 1192 (7) / 219 (8) |
| linear_algebra, a week | branch (both switches on) | 1343 (1772, 41) | 2676 / 3040 / 16/21 | - | 1210 (7) / 222 (8) |

Next right after a declined stop (keep going; no prefetch or dwell before it), all runs of a code pooled:
  mvp-0.49 (e7a7d7734f): median / p90 / above 2 s = 1817 / 2160 / 2/8
  main (ccb6573987): median / p90 / above 2 s = 2774 / 4283 / 4/6
  branch (both switches on): median / p90 / above 2 s = 2572 / 2900 / 4/6

Reading it: the numeric policy is the largest remaining cost on every copy, at main's level or a little under it
(linear_algebra 1896 -> 1657 ms, week 1632 -> 1343 ms); the section map and the join are what the two switches took
out (a week's `combiner_join` median 704 -> 134 ms, `ad_section_map` 11 -> 1 ms, objective job median 3807 -> 2366 ms,
p90 4749 -> 3245 ms). Next right after feedback is still above 2 s on the large copies (week: 16 of 21 against main's
20 of 21 and mvp-0.49's 25 of 30): the target of stage 1 (no worse than mvp-0.49) is **not** met by this stage either;
the remainder is `rollouts_evaluate`/`run_numeric`, which no switch here touches. After a 3 s dwell no Next is above
2 s on any copy. The served sequences equal main's in 6 of 7 runs with the switches on; on probability dwell 0 the
branch served a different 7th item (gate `objective` against main's `no_room_to_wait`), a prefetch-timing difference
of the kind recorded under identity below, not a value difference.

Profile of the branch's linear_algebra job (week, cProfile, about 34 jobs): what remains is the numeric policy's per-draw
arithmetic (about 468k calls of the draw evaluators, tens of seconds of the profiled 110 s, numpy broadcasting), then
SQLite reads (`execute` about 13 s cumulative of 110 s, 394k calls), none of it the reading map or connection setup.
(Full output: `smoke/out6/prof_branch_linear_algebra.json` in the landing scratch.)

### Smoke (earlier tree; fresh copies; every AI route at 127.0.0.1:9 except the router LLM and the Decider, answered by in-process fakes)

- **Identity, both switches off against main, draw for draw** (arxiv_v2, linear_algebra, probability; mvp-0.54 copies,
  mixture seed pinned to the decision id): LLM requests, Decider requests, gates, prompts and every table identical on
  arxiv_v2 and linear_algebra; eight draws per trace on all three. Set aside, as stage 1's landing set aside
  `held_ad_link`: ids, wall times, latencies, hex digests and the boundary key, plus the two new keys
  `held_reading_map` and `pooled_connections` wherever recorded (and RO6's generator key). The numeric seed excludes the
  switches (R2), so the draws are main's. One difference, on probability: `router_objective_traces` differ in
  `carried_for` (which earlier decision's prefetch was carried into a later one). Main differs from main the same way
  between runs (three runs of main on probability gave two different carried sets, one of them the switches-off run's), so it is
  prefetch-timing nondeterminism present on main, not the branch.
- **Trace terms recompute / logged probabilities recompute (switches on):** `v_residual`, `v_tilde` and the calibration
  recompute with problems 0 on all four runs (arxiv_v2 38+38+8, linear_algebra 49+49+7, a week 172+172+26).
- **Generated probes served at most once:** every run, at most once (the week serves one of its 14 generated probes).
- **Protection (R1):** `prot_r1.py` on fresh copies of linear_algebra and probability (arxiv_v2 has no completed
  sections: skipped): the job's held map equals the landing map and computes nothing within the job; a held-out span
  added between two jobs changes the next job's map (the reading maps to nothing; the next job computes afresh); an exam
  reservation committed between two jobs moves the epoch and the next job computes every mapping afresh; a reading
  withheld mid-job returns nothing from any memo while the others keep theirs. All ok.
- **Unattempted-stem scan:** 0 not shown on every run.
- **rebuild --shadow:** on all four copies, the only differences are the 14 to 27 mastery rows per copy whose
  `algorithm_version` stamp moves (mvp-0.47 to mvp-0.54); no other field differs. Assignments and traces survive a
  rebuild and a state sync.
- **Real model:** 0 new model_call_receipts from a real model in all 32 runs; no non-loopback socket (the net watch
  recorded only `powerprofilesctl` and `git` subprocesses); no Codex process of the landing's.

### Gate (merged tree, tip recorded in the report)

On the merged tree (main `214c206ff1` merged; the full run started at `d06faf8a52`, before the golden commit below):

- `lint-imports --no-cache`: 43 contracts kept, 0 broken.
- Full pytest (`-n 8`, 10G scope, lock held): 30220 passed, 90 skipped, 47 xfailed, **1 failed**:
  `tests/test_rw5c_switch_off.py::test_the_views_report_clis_reuse_keys_and_prompt_equal_mains`. Cause: the owner's
  figure author fix (`214c206ff1`) bumped both figure prompt versions and did not re-record the golden's
  `author_prompt_sha256` and `request_hash` values; main's own tip fails it. Fixed in its own commit (the golden
  re-recorded; the only differing keys were those four hashes); that file and `test_figure_author_predictions.py` pass
  (22 passed) on two further runs alone. The rest of the suite was not rerun after that fixture-only commit.
- Durability lane (`-m durability`): 409 passed, 1 skipped.
- Owner lane (fresh backup-API copies of owner-copies-mvp035, `LEARNLOOP_OWNER_VAULTS`): 83 passed, 4 skipped, 2 failed,
  the two known (`test_activity_backfill.py::test_backfill_logs_attempt_duration_interaction_events`,
  `test_placement_fixture_copies.py::...[arxiv_v2]`).
- Desktop (a frontend change came in with the merge): `npm run typecheck` clean; vitest `--maxWorkers=4` 276 files,
  2787 tests passed; `frontend:build` built.
- References regenerated after each merge: `db_validate_reference` errors `[]`, `desktop_validate` PASS (the review
  gates in `desktop_validate.py` moved for `BookPassage.tsx`: 324 files, 313 entry-reachable, ACTIVE 330),
  `module_validate` PASS, `validate_vault.py` passed; provenance-only churn left out.

### Rulings (verbatim)

- R1: "F1 and the protection qualification go structural: the held reading map (section->LO, span->section, section_spans) is held only within ONE objective job's decision_reads scope, as a snapshot as of that job's first read, and discarded when the job ends; nothing is held across jobs or walks of different jobs, so a vault or database edit is always seen by the next decision. Within the job, every memo return (cross-call and the existing local section/span and section_spans memos alike) is preceded by the withheld/protection check run fresh, and a protection change within the job invalidates the job's held values. A vault edit landing in the middle of one ~1 s job is read as of the job's snapshot, which is accepted (the decision is as of its inputs). Codex's reproductions are tests: the cross-walk contamination after edit and undo must be gone; the mid-job IR rewrite gives the snapshot's mapping consistently across held hits and misses; a reading withheld mid-job returns nothing from any memo. Measure what this costs against the cross-call cache on the copy-shaped vaults and at the smoke."
- R2: "F2: the two speed switches stay in RO6's generator payload, serving_switches and the prefetch key, but the numeric policy's random seed is derived from an identity that excludes them (they change no value at a fixed draw count), so with both off the draws are main's exactly; Codex's eight-draw reproduction (main a, branch b with both off) is a test and must give main's choice."
- R3: "F3: REAL values are encoded bit-exactly (typed binary packing), so -0.0 and 0.0 differ; a test."
- R4: "N1: a pooled connection on which any PRAGMA with an argument (or any statement other than reads and the pool's own resets) ran during a checkout is closed at release, never returned to the pool; detect it with the authorizer's SQLITE_PRAGMA action (and the statement kind), not a list of pragmas to restore. Codex's query_only / reverse_unordered_selects reproduction is a test."
- R5: "Item 3's exact per-table invalidation (triggers in a migration) is not built; the second join is cheap now. Recorded for the owner as a possible later migration, not queued."
- R6: "No further Codex round; I read the R1-R4 diffs before landing, so keep each in its own commit."

R3 was superseded by R1 (nothing digests stored rows any more), as recorded in `router-speed2-codex-review.md`.

### What the owner does

Nothing beyond restarting the app and the phone host. No migration, no successor. To turn a switch off, in the vault's
`learnloop.toml` under `[router_objective]` set `held_reading_map = false` and/or `pooled_connections = false`; off
serves main's code and main's draws exactly (identity above).

### Open items

- The stage's target (Next right after feedback no worse than mvp-0.49) is still not met on the large copies; the
  remainder is the numeric policy (`rollouts_evaluate`, `run_numeric`), not the read path.
- Exact per-table invalidation of the shared fit (triggers in a migration) is possible later (R5); not queued.
- Main's own prefetch-timing nondeterminism in `carried_for` (identity, above) is worth knowing when comparing traces.
