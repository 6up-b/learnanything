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

Each row is one change. Seconds were measured alone on this machine, so read them as relative: the machine was loaded by other stages. Final before and after times are in §8.

| Change | Measured | What still proves the behaviour |
|---|---|---|
| **Connection reuse in the fast lane** (`tests/connection_reuse.py`): a test's `connect()` calls share idle connections through production's own pool seam, `db.connection._REUSED` | 120-test sample: 189.5 s to 95.9 s. One chain walk: 138 s to 6.9 s. 8,923 tests from three targeted runs: 14,650 to 3,775 test seconds | The durability lane, the owner lane, `--fresh-connections` and the `fresh_connections` marker run production's open path. `tests/test_connection_reuse.py` pins each difference between an idle connection and a fresh one |
| **Copy targets skip fsync** (the owner's prior) | About 90 ms to 3 ms per vault copy on btrfs, 10 s of the sample | The durability lane keeps the production copy path, pinned |
| **`os.fsync` is a no-op in the fast lane** (bad descriptors still raise) | 3.7 s of the sample | Tests that spy on or fail `os.fsync` replace it as before. Real in the durability lane, pinned |
| **Fresh schema copied after the process's first real build** | 0.8 s per fresh vault, 8 s of the sample | The first build in each process is real. A test compares a copy to a real build. The durability lane always builds, pinned |
| **Template built only if a selected file mentions a vault** | 0.8 s per process, about 7 s of 27,650 s | A wrong guess is only slower: with no template, `create_basic_vault` builds the real vault |
| **One BLAS thread** | AD sim CPU 6.24 s to 5.04 s | Same results: matrices this small don't use BLAS threads |
| **CLI help no longer hashed** (§5) | Fast lane 60 s to under 1 s | §5 |
| **`slow` marker**: `-m "not slow"` while iterating; everything still runs in the gate | No gate saving, by design | The marked tests are unchanged |

### The owner's priors

| Prior | Verdict |
|---|---|
| `backup_database()` keeps synchronous writes in the fast lane, because the connect patch misses its target | **Right.** 90 ms against 3 ms. Fixed. It's still small next to the schema parse |
| `basic_vault_template` builds for tests that need no vault | **True but cheap:** once per process, 0.8 s, not per test. Made conditional. Truly lazy building would be wrong: the first test's monkeypatches would reach every later copy |
| Sim tests: smaller horizons in the fast lane, full runs in a slow lane | **Done for AD2+AD3** (`test_ad23_sim`, with `test_ad23_sim_smoke`). Its gates are pre-registered, so their size wasn't changed |
| Migration application per test | **Partly.** Upgrade tests' `_migrate` stays. The real cost was fresh schemas, now copied |
| Subprocess-heavy tests | **Small.** `test_evsi_multisim`'s CLI test (170 s) is CPU in the model fits, not process startup |
| xdist balance | **Not the constraint.** Sum / 8 is 97% of the wall clock |
| Upgrade and successor tests: why they grow, and whether a shared chain helps | **The cause wasn't the chain.** `parameter_registry.refresh` opens about 816 connections per call, 64 calls per walk, which is 96% of the time. Connection reuse takes a walk from 138 s to 6.9 s, so a shared chain (which would weaken what each proves) isn't needed. Each new tag now adds about 0.15 s, not 3 s |

The same `refresh` cost is real in production: about 2 s per tag on an upgrade. A one-line `with repository.pinned():` would fix it. It's listed in §7 rather than changed here, because the brief allows no such source change.

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

