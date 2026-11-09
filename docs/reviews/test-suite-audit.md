# Test-suite audit and speed (`tests/audit-speed`)

Owner, Nov 9: "Have opus in parallel fix the test suite." Base: main `a525dbcef4`. This file is the running record. Goals, in order: speed, flakes and known failures, usefulness.

## 1. Baseline

**Source:** per-test times from the Nov 7 gate (`pytest -n 8 --dist worksteal`, 10 GB scope, under the full-suite lock) and new profiling on this machine. No fresh full run was taken before changing anything, because the owner's rule allows one full run per stage, at its end. The Nov 7 and Nov 8 gates stand in as the "before" figure.

| Measure | Value |
|---|---:|
| Wall clock at `-n 8` | 3,562 s (59:22), and 57:32 on the merged tree |
| Test seconds | 27,650 s |
| Tests | 30,327: 30,189 passed, 91 skipped, 47 xfailed |
| Skipped | 77 owner lane, 8 torch, 6 others |
| Tests under 20 ms | 14,905, costing 6 s in total |
| Tests from 0.2 s to 5 s | 12,018, costing 13,760 s |

### Where the time went

A random sample of 120 tests of 0.2 to 8 s, serial, under cProfile: 191 s.

| Cost | Seconds of the sample | Share | Note |
|---|---:|---:|---|
| Opening connections (`connect`, nearly all of it the schema parse at the first statement) | 81 | 42% | 23,799 opens, 198 per test, about 3 ms each at 396 tables |
| Closing connections (freeing that schema) | 14 | 7% | |
| YAML dump and read-back (`vault/yaml_io._dumped`) | 12 | 6% | 10 ms per write, in pure Python |
| Vault template copy (`backup_database`) | 9 | 5% | Owner's prior: 90 ms each on btrfs, 3 ms without synchronous writes |
| Fresh schema (`_apply_fresh`) | 8 | 4% | 0.8 s each |
| Explicit `os.fsync` | 3.4 | 2% | |

One chain walk, `test_upgrade_to_mvp042_works_from_supported_versions[mvp-0.9]`, alone: 138 s. **133.6 s of that is `parameter_registry.refresh`,** called 64 times at 2.09 s each. It reads and upserts about 400 specs, each on a new connection: 34,935 opens in one test. That's why these tests grow with every tag.

Other measurements:

| Measure | Value |
|---|---:|
| `import learnloop.cli` | 1.4 s |
| Conftest import | 0.7 s |
| Session template build (`basic_vault_template`) | 0.76 s per worker, about 6 s of 27,650 s across 8 workers |
| Template copy, tmpfs against btrfs | 7 ms against 80-120 ms |
| Worker balance | Sum / 8 = 3,456 s against 3,562 s wall: workers aren't idle, so balance isn't the constraint |

## 2. Speed: what changed

Each row is one change. Seconds were measured alone on this machine, so read them as relative: the machine was loaded by other stages. Before and after times are in §8.

| Change | Measured | What still proves the behaviour |
|---|---|---|
| **Connection reuse in the fast lane** (`tests/connection_reuse.py`): a test's `connect()` calls share idle connections through production's own pool seam, `db.connection._REUSED` | 120-test sample: 189.5 s to 95.9 s. One chain walk: 138 s to 6.9 s. 8,923 tests from three targeted runs: 14,650 to 3,775 test seconds | The durability lane, the owner lane, `--fresh-connections` and the `fresh_connections` marker run production's open path. `tests/test_connection_reuse.py` pins each difference between an idle connection and a fresh one |
| **Copy targets skip fsync** (the owner's prior) | About 90 ms to 3 ms per vault copy on btrfs, 10 s of the sample | The durability lane keeps the production copy path, pinned |
| **`os.fsync` is a no-op in the fast lane** (bad descriptors still raise) | 3.7 s of the sample | Tests that spy on or fail `os.fsync` replace it as before. Real in the durability lane, pinned |
| **Fresh schema copied after the process's first real build** | 0.8 s per fresh vault, 8 s of the sample | The first build in each process is real. A test compares a copy to a real build. The durability lane always builds, pinned |
| **`yaml_io._dumped` and `model_json_schema` remember exact results** | 120-test sample 65.7 s to 49.1 s, against 189.5 s before any of this. About 75% of YAML writes hit | Pure functions: the real one runs on every new input. YAML is keyed by repr and only for plain data, because a round-trip mapping has comments its repr hides. Pinned: order, types, comments, a long key's read-back, callers can't change a schema |
| **Template built only if a selected file mentions a vault** | 0.8 s per process, about 7 s of 27,650 s | A wrong guess is only slower: with no template, `create_basic_vault` builds the real vault |
| **One BLAS thread** | AD sim CPU 6.24 s to 5.04 s | Same results: matrices this small don't use BLAS threads |
| **CLI help no longer hashed** (§5) | Fast lane 60 s to under 1 s | §5 |
| **Follow-ups journey cut to one arm** (§5) | 467 test seconds in the baseline; 204 s alone | §6 |
| **`slow` marker**: `-m "not slow"` while iterating; everything still runs in the gate. `test_ad23_sim`, the journeys, the CLI render and 13 others | No gate saving, by design | The marked tests are unchanged |

### The owner's priors

| Prior | Verdict |
|---|---|
| `backup_database()` keeps synchronous writes in the fast lane, because the connect patch misses its target | **Right.** 90 ms against 3 ms. Fixed. It's still small next to the schema parse |
| `basic_vault_template` builds for tests that need no vault | **True but cheap:** once per process, 0.8 s, not per test. Made conditional. Truly lazy building would be wrong: the first test's monkeypatches would reach every later copy |
| Sim tests: smaller horizons in the fast lane, full runs in a slow lane | **Done for AD2+AD3** (`test_ad23_sim`, with `test_ad23_sim_smoke`). Its gates are pre-registered, so their size wasn't changed |
| Migration application per test | **Partly.** Upgrade tests' `_migrate` stays. The real cost was fresh schemas, now copied |
| Subprocess-heavy tests | **Small.** `test_evsi_multisim`'s CLI test (170 s) is CPU in the model fits, not process startup |
| xdist balance | **Not the constraint.** Sum / 8 is 97% of the wall clock |
| Upgrade and successor tests: why they grow, and whether a shared chain helps | **The cause wasn't the chain.** `parameter_registry.refresh` opens about 816 connections per call, 64 calls per walk, which is 96% of the time. Connection reuse takes a walk from 138 s to 6.9 s, so a shared chain (which would weaken what each proves) isn't needed. Each new tag now adds about 0.2 s, not 3 s |

The same `refresh` cost is real in production: about 2 s per tag on an upgrade. A one-line `with repository.pinned():` would fix it. It's listed in §7 rather than changed here, because the brief allows no such source change.

## 3. Flakes and known failures

| Failure | Cause | Fix | How it was checked |
|---|---|---|---|
| **RO0 ULID** (`test_receipts_hold_ids_and_numbers`) | Checked a two-character title, `M2`, as a substring of a state full of random ULIDs | A whole-word match. A clause that never applied was dropped, so the check is stricter | Passes; the cause is deterministic to read. Not run enough times to show the old rate |
| **MCP `8841`** (`test_mcp_c1a_review`, `test_mcp_c1a_narrow`, `test_diagnosis_input_provenance`) | The same bug: four digits as a substring of random ids and hashes | `names_planted_key`, a whole-word match. It still catches a leak in a title or slug, and now also checks each output leaf in the schema test | Passes, and the leak tests still fail on a planted title |
| **Phone contract row order** | The journey took `rows[0]` of the queue, then revealed a hint on it. A hintless item sorting first gave a 422 | The journey picks an item with an authored hint | Recorded cause in `phone-v2-codex-review.md` |
| **Phone contract under load** (RE0's agent, -n 4) | **Likely, not confirmed from its log:** a method past the host's 15 s wait answers 202, and `Phone.rpc` requires 200 | The shared helper sets a long wait for all 16 host test files; `test_mobile_jobs` keeps its own short one | Mechanism read from `host.py:591`. Not reproduced |
| **Grader time of day** | Already fixed on Nov 1 (`fix-grader-date-nov1.md`): a test mixed wall-clock writes with a frozen clock that had fallen into the past | No further change. Swept again with the clock moved: 157 test files naming a date from 2026-11 on, at 2027-03-01 | 3,403 passed. The only 2 failures are the next two rows: neither is a date bomb. Other dates and times of day were tried on those 2 tests only |
| **Dont_know mass** (new; `test_stuck_prompt`, and very likely the failure seen in `test_stuck_prompt_replay`) | The builtin schema's id is a random ULID, which enters the calibration hash, which seeds the certainty bound. 1 hash in 600 gives a bound below certainty, so a dont_know reads 0.690, not 0.7 | In tests, only the id production mints is fixed, per slug; the real insert runs (§9, F1) | Simulated over 600 hashes: min bound 0.649, 1 below certainty. The failing value itself wasn't captured, so the link is by magnitude and mechanism |
| **`test_mobile_two_process` under time travel** | An artefact: the sweep's plugin warps only the main process, so the other process's day differs. It fails at every warped date and passes normally | None | Not a product or test bug |
| **Thread leaks** | The guard (`tests/thread_guard.py`) reported none in the Nov 7 gate, the targeted runs or the final gate, so `test_capture_route_recovery`'s listed leak is already gone | None | A leak fails its test's teardown: 0 errors in the final gate |
| **Three races connection reuse exposed** (`test_batch3_landing`, `test_approach_map_replay`, `test_compare_sources_keep`) | Each read state while background work it had started was still writing. A slow main thread used to hide this | Each stops or waits for the work first | Batch 3 and the map fixture failed every run before the fix. Repeated runs pass |
| **`test_reader_rw6b_p2_landing::test_i_the_narrative_lands...`** (the final gate's one failure; 3 of 3 alone) | A Today build holds AD's read snapshot while its background job commits the narrative. In WAL that's fine. In the fast lane's rollback journal the commit waits 5 s, then fails with "database is locked". With fresh connections the two rarely overlapped | The test runs in the durability lane, so it exercises production's concurrency. Rollback production is tested separately (§9, F3) | Found by listing the lock's holders at the failure. Passes 3 of 3 in that lane, and in the coordinator's gate at `1af4372fd0` |
| **`test_voi_v2`** (2 tests, older gates called it a load flake) | Its golden seeds every ULID, schema ids included. The fixed schema ids changed its decisions, failing every run until `seed_ids` restored production's | Fixed in `voi_restore_scenarios` | 3 of 3 passes. The golden is unchanged. It may also explain the older flake, if the id stream was disturbed; not shown |

**Load flakes in older gates** (`test_reading_hardening_2_fixes::test_f1_...`, `test_reading_request_sweep`, `test_voi_v2`, `test_apply_write_ahead`): none failed in the Nov 7 gate or here. No cause was established, so they aren't claimed as fixed. Halving the suite's CPU should help, since each waited on a worker under load.

### The two owner-lane failures waved through at every landing

**`test_backfill_logs_attempt_duration_interaction_events`: the test was out of date.** It looked in the copy for an attempt with no observation, and none is left since practice began writing them, so its setup crashed on `None` and the backfill never ran. It now makes one legacy on its private copy, with the same assertions, and the code passes.

**`test_placement_ignores_unanswered_opening_episodes_on_fixture_copies[arxiv_v2]`: the test found a real gap, and it needs the owner.**

- `pi_a_preprocessing_pipeline` is the only item of `lo_prepare_and_inspect_aligned_coordinate_tensors`. Its only answer is a `self_report` from Jul 21, with no evidence.
- So it has `last_attempt_at`, no `due_at`, and an opening episode that placement ignores. It isn't new material (not never-attempted) and it isn't routinely due.
- **Under placement that LO never comes back,** at every tag from mvp-0.11 to mvp-0.54, on this mvp-0.35 copy. Below placement it's served.
- A fix changes what the scheduler serves, so per the brief it stops here: no source change. The original expectations hold on every copy except this named LO on `arxiv_v2`. A separate test at the latest tag fails on a setup problem, on a newly stranded LO and on a fix, and xfails only for this LO (§9, F2).
- `linear_algebra` has one similar item, which is still served. `probability` has none.

## 4. Critical behaviour: seeded bugs

A name search can't show that a behaviour is tested, so I seeded one bug at a time in the source, ran the tests that name the subject (`-m "not slow"`, with `--maxfail=3`), and reverted it. The durability seeds ran the whole durability lane. **Survived** means no test noticed.

| Area | Seeded bug | First result | Now |
|---|---|---|---|
| Propensity | The mix's draw logs probability 1 | Killed | |
| Propensity | The stop coin's served probability is wrong | Killed | |
| Propensity | `μ` loses its floor | Killed | |
| Propensity | The chooser's trace logs the mix's probability under a coin | **Survived** 245 tests | Killed: `test_ro5_stop_coin` |
| Propensity | AD's `Draw.propensity` returns 1 | **Survived** 210 tests | Killed: `test_ad2_serving` |
| Propensity | A plan block logs probability 1 | Killed | |
| Propensity | The pick experiment logs the wrong share | Killed | |
| Propensity | A check slot logs probability 1, which the estimator divides by | **Survived** 145 tests | Killed: `test_ro5_checks` |
| Propensity | `DoseDecision`'s returned distribution is wrong | Survived 414 tests | **Left open:** nothing reads the returned value, and the persisted row is checked |
| Grading contract | The blind prompt carries `diagnostic_history` | Killed only by an unrelated flake (§3) | Killed: `test_blind_grading_contract` |
| Grading contract | The contract hash is constant | Killed | |
| Grading contract | `pinned_contracts` accepts another item's contract | Survived: **an equivalent bug,** because `pinned_contract_ids` checks too | See next row |
| Grading contract | `pinned_contract_ids` accepts another item's contract | **Survived** 869 tests | Killed: `test_learner_protection_predicates` |
| Grading contract | A route hold isn't honoured | Killed | |
| Protection | A held grade shows as a score | Killed | |
| Protection | Cold items aren't withheld | Killed | |
| Protection | An ordinary item presented as a probe isn't withheld | **Survived** 3,844 tests | Killed: `test_learner_protection_predicates` |
| Protection | Exam attempts aren't protected | Killed | |
| Protection | A failed predicate fails open | Killed | |
| Replay parity | Replay reads only the first evidence row | Killed | |
| Replay parity | The shadow rebuild's snapshot is empty, so it sees no diff | Killed | |
| Replay parity | The shadow rebuild ignores a live database that changed | **Survived** 503 tests | Killed: `test_shadow_rebuild` |
| Migrations | The head migration loses an index | Killed | |
| Migrations | A derived table is reclassified | Killed | |
| Durability | Production stays in rollback mode | Killed by the durability lane | |
| Durability | Production uses `synchronous=NORMAL` | Killed by the durability lane | |

Of 26 distinct seeds, 6 survived and now fail a new assertion, 1 was equivalent, 1 has no reader, and 1 had been killed only by accident. This is a sample of 26 chosen by hand, not a coverage measure. Each area's other behaviours are unchecked.

### Critical gaps still open

These are known-failing behaviours, pinned by strict xfails. Each goes red when fixed, so none is forgotten by the test suite, but none has an owner. They need a successor or a design, so nothing changed here.

| Pinned by | Gap | Status |
|---|---|---|
| `test_rebuild_closed_row_answer` (3) | An item retired outside the attempt ledger has no time replay can apply it at, so replay sees it active | Needs closures as ledger events |
| `test_rebuild_equivalence_review` (1) | Two grades of one LO committed in one second in reverse id order replay in id order | Needs a persisted commit sequence |
| `test_learner_report_superseded` (2) | A claim that never re-anchors, made after materialization, differs between live and replay | Open |
| `test_diagnosis_input_provenance_landing` (2) | Two reopened provenance gaps (F2, F3) | Waits on the one-capture-point follow-up |
| `test_placement_fixture_copies` (1, new; owner lane; a scoped `pytest.xfail`, not a strict marker) | An answered LO with no due time never returns under placement | §3, the owner's call |
| `test_rebuild_equivalence` (3) | Below mvp-0.36 only: fixed from that tag on | Goes with old tags (D3) |

Other things never run in the gate:

- 8 trainer tests skip because torch is absent (the `pdf` extra).
- `test_the_real_sdk_has_the_seams_the_lockdown_replaces` skips because `openai_codex` isn't installed. **The seam it checks is a security boundary,** so it should run somewhere.
- Node's `test_the_vendored_file_is_byte_for_byte...`, the GPU smoke test and the real-scope sandbox test skip by environment.
- The 24 AD grid xfails and 8 other AD gate xfails are monitors by the owner's Oct 19 decision. They're kept, in the slow lane.

## 5. Usefulness

**A smaller problem than the brief feared, by these scans:**

- **Mocking is light.** Only 4 of 1,382 test files use `MagicMock` or `mock.patch`. The suite drives real SQLite and real code with fake model clients.
- **No test file is a literal duplicate.** The AST scan found 15 groups of identical test bodies (40 tests), but they call module-local helpers with different meanings, so they aren't duplicates. The real overlap is the per-tag successor families, which go with the upgrade modules (D3).
- **Tests with no assertion:** the scan listed 40, and the ones read call a local `_refused`-style assertion helper. Not all 40 were read.
- **Self-equal assertions** (`once() == once()`, 7 of them) are determinism checks, which is what they claim.

**Findings acted on:**

| Test | Problem | Action | What still proves it |
|---|---|---|---|
| `test_recursive_cli_help_matches_snapshot` | A hash of each help text, re-recorded in 211 commits, so a failure only meant "regenerate": reward-hackable | **Rewritten** into 3 tests | Parameter contracts pinned in `tests/cli_surface.json` (§9, F5): an incompatible change fails, a compatible addition needs no edit. Every help still renders (slow). Dropped: exact prose. Fail-first: a renamed flag fails, an added flag passes |
| `test_router_reader_activity::test_it_is_a_pure_read` | Compared `total_changes` across two new connections: always 0 == 0 | **Rewritten** to compare the file's bytes | Fail-first: a seeded no-op write fails it |
| `test_ad2_serving::test_propensity_recomputes_from_logged_row` | Compared a property with itself | **Strengthened** | §4 |
| `test_ro0...test_receipts_hold_ids_and_numbers` | An `or` clause that never applied | **Rewritten** as a whole-word check | §3 |
| `test_rofu_weeks` | 2 two-week journeys, 467 test seconds in the baseline, only asserting `transitions >= 0`, which can't fail. Its numbers were for a review written on Nov 5 | **Rewritten:** one two-week journey at the tag it was for, with real assertions, in the slow lane. The mvp-0.49 arm is deleted | Removed arm: the comparison is recorded in `router-followups-nov5.md`, and `test_ro6_tail_data`'s journey runs at its own tag |

**Reported, not changed:**

- **`test_router_staged_p2:109`** asserts `counts.get("controller_ownership", 0) >= 0`, which can't fail. It sits in the P4 controller area on the deprecated inventory, so it goes with that code.
- **About 20 other `>= 0` assertions** are mostly shape checks beside real ones. They're weak but harmless.
- **158 test files read source text or parse an AST.** Many pin real boundaries, such as what code AD's operation may reach, but they name paths. The refactor will break them. Keep the ones that enforce a boundary, and delete the ones that only pin where a thing lives.
- **Test files named for their review rounds** (`*_codex_review`, `*_fix_round3`, `test_reader_rw2b_fix4` to `fix15`). This hides what each proves. The refactor's removal steps will touch many of them; renaming by behaviour is cheap then.

**Goldens:** besides the CLI hash, all are low-churn (1 to 3 commits each) and prove "switched off equals the predecessor", which is real parity. Kept.

## 6. Deletions, rewrites and additions

Nothing on the map's deprecated inventory was deleted. `test_ad23_sim` and `sim/ad_gates` aren't deprecated (strategy, Appendix A), so they were treated as live.

| Test | What it proved | What proves that now, or why it was worthless |
|---|---|---|
| `test_recursive_cli_help_matches_snapshot` and `tests/cli_help_snapshot.json` (removed) | Every help exits 0, and each help's exact bytes | Exit 0: `test_every_command_prints_its_help`. Contracts: `test_no_command_or_parameter_changed_incompatibly`. Exact prose: worthless, it was re-recorded in 211 commits |
| `test_two_weeks_before_and_after_the_batch[mvp-0.49]` (removed) | A two-week journey runs at mvp-0.49. It asserted nothing else, and `>= 0` can't fail | `test_ro6_tail_data::test_a_few_weeks...`: the same journey at the same tag, with real assertions. The comparison is in `router-followups-nov5.md` |

**Counts** (before the fix round in §9, which added the tests it names):

- **Removed:** 2 test cases (the CLI hash test, and the journey's mvp-0.49 arm).
- **Merged:** 0. No real duplicates were found (§5).
- **Rewritten:** 4 (CLI surface, into 3 tests; pure read; RO0 receipts; the follow-ups journey).
- **Corrected or strengthened in place:** 12 (AD's row, RO5's trace and check, backfill's setup, placement's property, phone contract's item choice and wait, 3 background-work orderings, the narrative test's lane, the VOI golden's ids, the planted-key checks across 3 files).
- **Added:** 33 test functions, 51 cases: `test_connection_reuse` 23 functions, `test_learner_protection_predicates` 4, `test_ad23_sim_smoke` 1 (15 cases), and one each in `test_shadow_rebuild`, `test_blind_grading_contract`, `test_ad2_serving`, `test_mcp_c1a_narrow` and `test_placement_fixture_copies`.

## 7. Plumbing list for the refactor

None of this was changed here. Counts are from this branch's tests; they use the strategy's Appendix A where it corrected the map.

| Item | Today | What I'd do |
|---|---|---|
| **Frozen version sets** | 36 assertions of the form `X_VERSIONS == frozenset({"mvp-0.24", ..., "mvp-0.54"})` in test files, each edited by every new tag; 46 test files name a recent tag literally | Assert the rule once per set: `X_VERSIONS == set(SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(first):])`. One parametrized table of `(set, first tag, last tag or None)` in one test file, which also finds the sets that end early |
| **"Latest" pins** | `SUCCESSOR_CHAIN[-1] == LATEST == "mvp-0.54"` in each successor's test | One test on the chain's shape. A successor's own test names its neighbours by index from its own tag, never the latest |
| **Frozen defaults digests** | 48 test files read `DEFAULTS_SNAPSHOT_BY_ALGORITHM` or `defaults_fingerprint_for_version`, each with a growing preamble that undoes later defaults. Nothing in `src` reads the snapshot | Delete the per-tag digests and their tests. Keep one test: a change to a default that replay reads must name its successor or say why not. That is what the digest was standing in for |
| **Head fixture path** | `migration_head_250` named in 68 test files, plus 3 scripts | A `tests/head_fixture.py` that finds the one `fixtures/migration_head_*`. The rename then touches no test |
| **Generated notes** | Regenerated by hand in every stage: 593 of router speed 2's 615 files | Generate at landing only, in one commit, with the gate checking they're current. Merge conflicts in them resolve by regenerating |
| **`--pass-through` of the guard** | Chain tests `_pass_guard` through `mvp-0.12` on vaults at mvp-0.10 | Goes with the upgrade modules (D3) |

**Speed-ups that depend on the default vault's tag (mvp-0.6; the strategy's D2a and D2b move it), left alone:**

- Every test that starts below the tag it tests walks the chain to reach it. Moving the default tag removes those walks where they aren't the test's subject. They now cost about 0.2 s per tag rather than 3 s, so this matters less than it did.
- Tests pinned to `set_algorithm_version(paths, "mvp-0.6")` semantics can drop their old-tag branches once those gates go (D4 to D6).

**Source changes I'd make, outside this brief:**

| Where | Change | Why |
|---|---|---|
| `params/parameter_registry.py:3292` `refresh` | Run its loop inside `repository.pinned()` | It opens about 816 connections per call: about 2 s per tag on the owner's real upgrades, more with fsync. `pinned()` is documented as purely a performance measure |
| `db/repositories.py:1094` `Repository.connection` | Reuse across a request or job, as `reused_connections` does for an objective job | Each connection costs about 3 ms of schema parsing and 1 ms to close, and an ordinary test opens about 200. The same cost applies per request in production |
| `db/connection.py` | Decide whether a test-only DML-keeping pool should be production's rule too (R4 closes after any write) | Reads and writes alternate, so production's pool rarely reuses across a write |
| `outcome_schemas` | Give the builtin schemas a content-derived id | The random id seeds the certainty bound, so two vaults with identical histories get different masses (§4) |

## 8. Before and after

| Command | Before | After | Note |
|---|---:|---:|---|
| **Full suite, `-n 8 --dist worksteal`, 10 GB scope, under the lock** | **59:22** (Nov 7 gate, 3,562 s); 57:32 on Nov 8's merged tree | **14:52** (892.8 s) | The after run had a nearly idle machine (load average under 1 when it ended); the before runs' load isn't recorded, so the wall-clock ratio may flatter this |
| Test seconds, same run | 27,650 s | **6,701 s** | The fairer comparison: -76%. On the 30,322 tests in both: 27,130 s to 6,511 s |
| **Serial, full suite** | **7:02:47** (25,367 s, a525dbcef4, the owner-approved overnight baseline) | **Not run.** About 1:50 if the test seconds carry over, **an estimate** | The owner's rule allows one full run per stage, and it was the `-n 8` one |
| **Durability lane, serial** | **6:24** (384.6 s, 410 tests: 409 passed, 1 skipped) | **6:54** (414 s, 411 tests) | No speed-up, by design: it still runs production's pragmas, WAL and fresh vaults. The small rise includes 2 new tests and other load |
| Durability lane, `-n 4` | not measured | 2:22 | |
| `-m "not slow"`, `-n 8` | no such lane | **Not run.** About 11 min (5,299 test seconds / 8), **an estimate** | 72 slow cases cost 1,401 test seconds |
| Owner lane, `-n 4` on fresh copies | 83 passed, 4 skipped, **2 failed** (last landings) | **85 passed, 4 skipped, 1 xfailed, 0 failed** (92 s) | The xfail is the new pin in §3 |
| One chain walk, alone | 138 s | 6.9 s | |

**By family, test seconds in the gate (the map's overlapping filename families):** successor and upgrade 4,364 to 186; Reader 2,589 to 498; router 2,142 to 982; AD 1,953 to 1,151; sim 1,316 to 938. What's left is mostly real computation: the AD gates, the EVSI fits and the router's rollouts.

**Worker balance after:** 6,701 s / 8 is 94% of the wall clock.

**My gate (`983035eb0e`):** 30,322 passed, 1 failed, 91 skipped, 47 xfailed. The failure is in §3. **The coordinator's gate at `1af4372fd0`, as reported to me:** fast lane 30,322 passed, 92 skipped, 47 xfailed, 0 failed in 14:43; durability 412 passed, 1 skipped in 6:31. The fix round in §9 came after both, and only targeted runs back it: the coordinator runs the final gate on its tip.

**Not verified:**

- I ran no full `--fresh-connections` run. The coordinator is running one in a separate checkout, and its result isn't in this record.
- The serial and `-m "not slow"` after-times, as noted.
- The dont_know flake's link to the fixed schema id is by mechanism and magnitude. The failing value was never captured with its hash.
- The phone contract's load failure from RE0 was never reproduced. Its cause is read from the code.
- The seeded bugs are a hand-picked sample of 26.
- The AD gates' figures weren't re-examined: they're unchanged apart from a BLAS thread limit, and strict xfails would have gone red.

## 9. Codex review of `1af4372fd0`: findings, rulings, fixes

The verdict was "land after fixes". Each row is one commit, reproduced first where testable. No source, app or migration changed.

| # | Finding | Coordinator's ruling | Fix and evidence |
|---|---|---|---|
| F1 | The lane pre-inserted and committed the schema row, so production's insert branch never ran in a new-schema test | Patch only the minted id; keep a test of the real random id, and one of the bound's limits over seeds | `ensure_outcome_schema` runs unchanged, and only `new_ulid` inside it returns the slug's id. `tests/test_outcome_schema_ids.py`: real random id; the insert branch mints exactly once (fails on the old pre-insert); the bound over 1,500 seeds stays above 0 and at or below the mean's certainty, so mass stays within (0, the type's mass]. `seed_ids` and `test_voi_v2`'s golden are unchanged and pass |
| F2 | Placement subtracted a computed set from both expectations everywhere, and a strict xfail covered a whole test, so a setup failure passed as expected | Name the fixture and LO; restore both expectations elsewhere; scope the xfail to the predicate | `KNOWN_STRANDED` names one LO on `arxiv_v2`. On fresh owner copies: 8 passed, 1 xfailed. Emptying the known set fails both tests on `arxiv_v2`. A newly stranded LO or a fix fails |
| F3 | Moving the narrative test to the durability lane hid what production's rollback mode does | Keep it there; record which versions stay in rollback; test a real rollback open with controlled overlap; xfail and report if the narrative is lost | See below: **a delay, not a loss.** 4 tests in `tests/test_narrative_rollback_overlap.py`, no xfail |
| F4 | A kept connection could leak state through a raw handle, and the DML-keeping limit wasn't stated | Don't discard after DML. Proxy `cursor.connection`; let no untracked cursor or raw-registered function survive release; guard `src`; state the limit | Each reproduced first (9 tests failed). Every cursor is recorded on the raw connection, including those sqlite3's `execute` makes in C. Raw state calls, and blobs, mark the connection for good. Guard and docstring added. 1,537 passed on half the connection-sensitive files |
| F5 | The surface pinned names only, so a changed type or default, or a reordered positional, passed | Record contracts; compatible additions pass; only incompatible changes fail; no prose | `cli_surface.json` records order, type, default, nargs, required, choices. 6 compatible and 11 incompatible cases are unit-tested. Seeded on the real CLI: a renamed flag fails, an added flag passes |
| F6 | The YAML memo gave a repeated container the plain copy's text | Bypass on repeated identities, cycles included | Reproduced: `{"a": shared, "b": shared}` and `{"a": [1], "b": [1]}` share a repr and differ in YAML, and a cycle raised `RecursionError`. Any repeated container now takes the real dump |
| F7 | The JSON-schema memo returned stale results after a rebuild or a config change | Key on them, or remove the patch | Kept. Reproduced on a forced rebuild, a changed `model_config` and a nested model's. The key now holds the core schema's identity and every reachable model's config; all 3 fail on the old key. In the sample, 50 of 754 calls regenerate |
| F8 | Cutting the journey to 8 days wasn't justified | Back to 15 days, slow; removing the mvp-0.49 arm stands | Done: 204 s alone, 120 s more than at 8 days |
| F9 | `--fresh-connections` failed its own harness tests | Build pools explicitly; honor the selected mode | Reproduced: 21 of 42 in `test_connection_reuse` failed in that mode, and none does now. An autouse fixture builds each test's pool in either mode, and one test asserts the mode itself. An unfiltered run's result is the coordinator's |

**The 120-test sample,** same command under cProfile: 57.1 s before this round, 60.0 s after it. Both ran beside the coordinator's full run (load average 12 to 14), so the 3 s difference isn't a precise cost. Earlier figures in §2 came from a quieter machine.

### F3: rollback in production

`switch_to_wal` keeps a database in rollback mode only when `wal_unavailable_reason` says the linked SQLite has the WAL-reset bug:

- **Stays in rollback:** below 3.44.6, 3.45.0 through 3.50.6, and 3.51.0 through 3.51.2.
- **Moves to WAL:** 3.44.6 or a later 3.44, 3.50.7 or a later 3.50, 3.51.3 and later.
- **The owner:** this worktree's uv-managed Python 3.12.14 links SQLite 3.53.1 (`wal_unavailable_reason()` is `None`), and the 3 permitted copies' headers are WAL. **I didn't open the live vaults,** and I checked no other machine. A system Python on an older SQLite would stay in rollback.

On a real production rollback open (`synchronous=FULL`, journal `delete`, busy timeout shortened from 5 s for the past-timeout cases):

| Overlap | What happens |
|---|---|
| No reader | The narrative lands |
| A reader ending inside the busy timeout | A wait, then it lands |
| A reader past the timeout, held before the job's claim | The job raises `database is locked`, no model is asked, and the next build lands it |
| A reader arriving after the claim (the sidecar's real order) | Renewal and release both fail, so the claim stays. Builds get `claimed` until the lease lapses, no model is asked twice, and the first build after the lease lands it |

**Production finding, not fixed:** on a rollback vault, a read longer than the 5 s busy timeout can delay a narrative by the claim's lease (5 minutes in this test's route). It isn't lost, and WAL vaults, like the owner's copies, aren't affected.

### F4: corrections to the review's premise

Checked in `src`, and consistent with the ruling:

- `.lastrowid` is read in `learnloop_sidecar/handlers/sqlite_admin.py` (2 sites), on the cursor just used and on that module's own `sqlite3.connect`, never a pooled connection. The guard names it as the one exception and checks it still opens its own connection.
- `total_changes` is also read at `db/repositories.py:20557`, as a delta within one checkout. That's safe on a kept connection, though it isn't a watcher's read.

### Added in this round

`test_outcome_schema_ids` 4 tests; `test_narrative_rollback_overlap` 4; `test_connection_reuse` 16 more cases (net of 1 moved to the new file); `test_cli_help_snapshot` 18 more cases; 1 more owner-lane parametrized test in place of the strict xfail.


## 10. Landing onto main

Gate on `0439d1ad06` (the orchestrator's, under the lock; test-only change, so no vitest, cargo or smoke):

| Lane | Time | Result |
|---|---:|---|
| Full suite, `-n 8` | 16:36 | 30,363 passed, **1 failed**, 94 skipped, 47 xfailed |
| Durability, serial | 7:08 | 416 passed, 1 skipped |
| Owner lane, `-n 4`, fresh backup-API copies | 1:25 | 87 passed, 4 skipped, 1 xfailed |
| Import contracts | | 43 kept |

The one failure, `test_source_space_resolver::test_a_challenger_learns_its_way_up_from_resolver_receipts`: `learned_weights` returned None after a history drawn from seeds keyed by random receipt ids. This branch doesn't touch the test. It passed 3 of 3 alone and then no failure showed in 256 more runs (4 of them ended on a warning line rather than a pass line, so they count as no failure seen, not as passes). The link to the random receipt is inferred from the code and was not reproduced. The final commit runs the draws' seeds in call order in that test: 20 of 20 passed, and its file passed whole (17). The tip therefore has no full-suite pass of its own beyond this one test's change.

One full `--fresh-connections` run at `1af4372fd0`, in a clean checkout: 52:33, 30,309 passed, 13 failed, 92 skipped, 47 xfailed. All 13 failures are in `tests/test_connection_reuse.py`, the F9 harness problem fixed in `e264fbfc69`; every other test had the fast lane's outcome (14:43, 30,322 passed, 0 failed, at the same commit). Not repeated on the fixed tip.

Ruling recorded for the refactor: one full `--fresh-connections` run at each arc's close.

Open for the owner: the placement gap (needs a successor), owners for the seven other strict xfails, and whether `openai_codex` joins the gate so `test_the_real_sdk_has_the_seams_the_lockdown_replaces` runs. A narrative delay on rollback-journal SQLite versions is recorded in §9; nothing shows the owner on those versions.

The owner has nothing to run for this landing: no source, schema or config changed.
