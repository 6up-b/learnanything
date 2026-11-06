# Router speed: the Codex review and its fixes (`router/ro-speed`)

Codex reviewed the stage at `d9ef66456a` (gpt-6.1-sol; job `20261106-092017-FZcZWr`). It raised two Medium findings,
F1 and F2, and four claims that don't hold. Both findings reproduced here first, with failing tests, and both are
fixed. Fakes only: there was no paid call and no model request. No owner vault or tracked working vault was opened.
Every script outside pytest ran under `env -i` with an empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

## Findings

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Faster refinement changes the served choice without a successor or kill switch | **fixed** (the kill switch, generator payload and prefetch key); the algorithm-version part is **rejected**, reason below | `e66f62e6f1` | `tests/test_rospeed_ad_link.py`: `test_the_switch_off_is_the_landing_code_under_a_deadline`, `test_the_switch_off_costs_the_landing_codes_work_on_every_shape`, `test_the_switch_reaches_every_rollout_from_the_config`; the generator and prefetch-key tests parametrized over the switch list (`test_rofu_generator_switches`, `test_rofu_switch_key`) and `test_rofu_successor` now cover `held_ad_link` |
| F2 | Medium | The decision cache retains outcomes after a regrade or hold | **fixed** | `d3fb6f19f6` | `tests/test_rospeed_join.py`: `test_a_regrade_or_hold_inside_one_decisions_scope_is_read[regrade, hold]`, `test_a_regrade_or_hold_between_the_jobs_card_and_numeric_builds_reaches_the_numeric_policy[regrade, hold]` (all four fail on the previous code), `test_the_prefetch_job_reads_the_fit_again_only_after_a_commit` |

No finding was High.

### F1: the held link is a serving change, so it has a switch

**Reproduced.** This is Codex's case: the arxiv_v2-shaped 22-topic decision, seed `"speed"`, merged sessions and the
consistent draw. It runs on a deterministic clock charged one unit per sigmoid element (in the link's quadratures, the
combiner, and the landing code's copies), with one shared deadline. The deadline is 2.5 times the landing code's
cost for its first 8-draw batch.

| Code | Completed draws | Numeric choice |
|---|---:|---|
| The landing code (`516db1d862`'s link and readers, put back) | 8 | `stop_for_today` |
| This branch, `held_ad_link` off | 8 | `stop_for_today` (the same `Q` per draw, bit for bit) |
| This branch, `held_ad_link` on (the code Codex reviewed) | 32 | `a` (the review) |

This matches Codex's table (8 draws and stop; 32 draws and review a). Fixed-draw equality does not establish serving
equality, because serving refines until the LLM answers or the deadline runs out. The follow-up batch had already
ruled this way for `merged_sessions` (its Codex review F2).

**Fixed** (`e66f62e6f1`).
- **The switch.** `[router_objective] held_ad_link` defaults to true. It sits at the follow-up batch's tag (mvp-0.50)
  through `followup_on`, as every switch of the batch does.
  - On: item 1's held link.
  - Off: the batch's landing code, a quadrature per read. `_Model.performance`, `_graded_linked` and `_observe` run
    the landing's calls in the landing's order, so the work is the same, sigmoid element for sigmoid element. A test
    checks this on four shapes (arxiv_v2- and linear_algebra-shaped, a dated use inside the horizon, the log-space
    tail) with each of the batch's rollout options. Below the tag it is off.
- **One place.** `value.evaluate`, `baselines`, `gain` and `_Model` take `held_ad_link` (False there means the landing
  code). `objective_chooser._rollout_options` passes it to every rollout of a decision: the evaluation and its
  refinement, the correction, the carried valuation, the baselines and the day's gain curve.
- **Versioned as a serving change.** The switch is in `FOLLOWUP_GENERATOR_SWITCHES`, so it reaches:
  - RO6's generator payload and the trace's `versions.serving_switches` (landing ruling R8): flipping it is a change
    point, never a change of `Q` under one generator version;
  - the prefetch boundary key (`FOLLOWUP_SWITCHES`, ruling R12): a flip between a prefetch and its serve starts a new
    job.
- **Classified** in the parameter registry as a structural kill switch. Every defaults snapshot was recomputed (41
  entries; the switch is a modelled default, inert below the tag). The spec's §8 paragraph on R8 names it.

**Rejected: a new `algorithm_version`.** The switch, the generator payload and the prefetch key are the versioning the
follow-up batch uses for a serving change at its tag (R8 and R12): `merged_sessions`, the same kind of change, has no
tag of its own. The owner's decisions in force are "live changes behind kill switches" and frictionless defaults; a
tag would add an upgrade step and no information the trace and the generator do not already record. mvp-0.51 is
TE2's (landed on main), and TE3a is building the next one, so a tag here would collide with both at the landing.

**What the owner sees.** Decisions logged under the batch's landing code have no `held_ad_link` in
`serving_switches`, and new ones do. So RO6's generator changes once, when the new code first serves: one change
point, which censors the transition that spans it.

**Timings** (`value.evaluate`, 64 draws, every switch of the batch on, median of three, `bench_f1.py` in the stage's
scratch directory):

| Shape (topics, items per block) | `held_ad_link` off (the landing code) | on |
|---|---:|---:|
| arxiv_v2-shaped (22, 3) | 1670 ms | 873 ms |
| linear_algebra-shaped (40, 3) | 1939 ms | 980 ms |
| probability-shaped (12, 2) | 1052 ms | 724 ms |

These agree with item 1's table in `router-speed-nov6.md` (landing 1468 / 1863 / 1024 ms, now 855 / 958 / 704 ms; the
machine was busier this time). Default on keeps item 1's speed.

### F2: the shared fit is revalidated by the database's commit version

**Reproduced.** The fixture is the RO6-shaped journey at the tag, with two cold outcomes answered through the real
self-grading pipeline. It uses the real check resolver and fitter.
- Inside one `decision_reads()` scope, a regrade (or a hold) committed after the first read left the second read on
  the first fit; a fresh read differed.
- In the prefetch job, a regrade (or a hold) is committed between the card's build and the numeric build (through
  `decision_card`, which runs between them). The numeric policy got the card's fit (n = 2) while a fresh read at that
  moment gave n = 1.

All four tests fail on the previous code.

**Fixed** (`d3fb6f19f6`).
- **The watcher.** `decision_reads()` holds a read-only watcher connection per database, the pattern of
  `reading_choice.fingerprint`. Each read records the watcher's `PRAGMA data_version`, file identity and
  `total_changes`, taken **before** the read.
- **When a read is shared.** A build shares the held fit only while that version is unchanged. Any commit by any
  connection, whatever it wrote, makes the next build read again, so there is no list of tables to miss.
- **When the database cannot be watched,** it is read every time. The watcher closes with the scope, and nothing
  outlives the scope.
- **The tests.**
  - A regrade and a hold inside one scope reach the next read.
  - A regrade and a hold between the job's card build and numeric build reach the numeric policy's fit (equal to a
    fresh read at that moment).
  - A decision's fit is read again only after a commit, never twice on one version.

**What this costs.** A model request's start receipt (`model_call_receipts`, written by the router's spend guard) is
a commit. When the LLM policy's request starts between the two builds, which is the usual case once the card is sent,
the numeric build reads again, so the job makes two joins as the landing code did. On the inline-fake journey this is
2 builds and 2 reads per job.
- **Gone:** item 2's "2 to 1 read per prefetch job" saving, in that case.
- **Kept:** the rest of item 2. The trace side is still parsed once per content and RO2's resolver is still linear.

The watcher itself is cheap (`bench_f2.py`, synthetic vaults, medians):

| Vault | A full read (the join) | A shared build | The watcher's version check |
|---|---:|---:|---:|
| 6 topics x 5 items (`la`) | 60.4 ms | 0.013 ms | 0.013 ms |
| 16 topics x 8 items (`la16`) | 73.8 ms | 0.013 ms | 0.013 ms |

**The smallest way to get the saving back:** revalidate on the fit's own inputs instead of the whole database.
- A sound version needs every table the fit reads:
  - attempts and their `received_at`;
  - grade evidence and supersessions;
  - blind records (holds);
  - reveals, readings and presentations;
  - traces and checks.
- SQLite has no per-table version. The cheapest sound form is an in-process write epoch per table, counted in
  `db.scopes.guarded_connection` for this process's writers. It would also need `data_version` for other processes'
  commits, and those would still invalidate.
- That is DB-layer work, so it is left to the owner's call. The alternative is the AD reading-map cache already
  listed in `router-speed-nov6.md` (item 2's smallest finish), which removes most of a join's cost on the copies
  whatever the read count.

## Claims that don't hold

- **"Every value is the landing code's" and "no trace records anything different."** Corrected in
  `router-speed-nov6.md`. The values are the landing code's at a fixed number of draws. Under the serving deadline
  the held link completes more draws (F1). The traces now record `held_ad_link` in `serving_switches`.
- **"No successor, no switch."** Corrected: the switch exists and is versioned through the generator payload and the
  prefetch key. There is no algorithm-version successor, for the reason given under F1.
- **"One read per decision."** Corrected: one read while nothing is committed in between (F2).
- **The Reader-heavy regime is unverified.** Agreed, and already recorded as open in `router-speed-nov6.md` ("The
  copies' own numbers"). The synthetic journeys have no Reader sources, so the landing gate's smoke on the owner's
  copies has to measure the join's readings there. Nothing in this fix step changes that.

## Spec conformance after the fixes

| Requirement | Now |
|---|---|
| §8.4, R9–R11: AD predictive semantics | Unchanged, at fixed draws and (switch off) under the deadline |
| §8.11/R12, §10.1: version serving and generator changes | `held_ad_link` is in the generator payload, the trace's `serving_switches` and the prefetch key |
| §9.1: corrected grades and holds govern resolved outcomes | A committed regrade or hold reaches the next build of the same decision |
| Storage, replay, durability | No migration, persistent cache, replayer or durability change. The watcher is a read-only connection that lives for one decision |
| Spend, privacy, grading, evidence | No new request, network surface, grading-context change, verdict or evidence writer. No reader or writer of the retired difficulty scalar (`git diff 516db1d862 -- src migrations`) |

## The gate (this fix step)

The full suite, the whole durability lane and the whole vitest run belong to the landing gate.
- No frontend or `src-tauri` file changed, so no npm, vitest or cargo step applies.
- No schema, migration, DB-layer or connection code changed, so no durability-marked test applies. The scope's
  watcher is a read-only connection in `daily_plan`, and its tests are in the targeted set.

| Step | What ran | Result |
|---|---|---|
| Setup | `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | ok |
| Import contracts | `uv run lint-imports --no-cache` (under `env -i`) | 43 kept, 0 broken |
| Reproduction | The four F2 tests on the previous `objective_inputs.py` | 4 failed (reproduced) |
| | The F1 deadline test (`-s`) | landing 8 draws `stop_for_today`, off 8 `stop_for_today`, on 32 `a` |
| Iterating | `tests/test_rospeed_join.py`, `-n 6` | 74 passed |
| | `test_rospeed_ad_link`, `test_rofu_successor`, `test_rofu_generator_switches`, `test_rofu_switch_key`, `test_config_refactor`, `test_registry_audit`, `test_rofu_speed`, `test_rofu_ad_link`, `-n 6` | 174 passed |
| Targeted set | 131 files, `-n 6`, behind `flock /tmp/learnloop-fullsuite.lock`; listed below | **8188 passed, 1 failed, 13 skipped, 3 xfailed** (47 min, on a machine shared with other stages' landing runs) |
| The one failure | `tests/test_regrade_contract_upgrade.py::test_an_upgrade_interrupted_after_publication_is_resumed` (an mvp-0.25 mastery snapshot after a resumed regrade-contract upgrade; no module this step touches is on its path). Reruns: alone 3 times, then the whole file twice at `-n 6` | 3/3 passed; 17 passed, 17 passed. Intermittent under load, and it passed in this stage's previous targeted run |
| References | `module_generate.py` / `module_validate.py` | PASS |
| | `db_generate_reference.py` / `db_validate_reference.py` | errors []: head 247, 1179 effective configuration leaves; the two prose counts updated by hand |
| | `desktop_generate.py` / `desktop_validate.py` | passed |
| | `validate_vault.py` | passed |

**How each run was made.**
- Every test ran inside `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, at most `-n 6`, one run
  at a time.
- Every script outside pytest ran under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. That
  covers the benchmarks, lint-imports, the snapshot computation and the reference scripts.

**What the targeted set contains.** It is the stage's earlier 112 files plus every test file naming a module this step
changed: `router_objective_switches`, `DEFAULTS_SNAPSHOT_BY_ALGORITHM`, `defaults_fingerprint_for_version`,
`objective_inputs`, `objective_chooser`, `router_objective.value`, `parameter_registry`, `RouterObjectiveConfig`,
`FOLLOWUP_GENERATOR_SWITCHES`. It includes:
- **the contract and audit set:** `test_config_refactor` (the defaults snapshot), `test_cli_help_snapshot`,
  `test_sidecar_serializer_snapshot`, `test_desktop_rpc_contract`, `test_mobile_allowlist`, `test_architecture` (the
  frozen cycles, the SQL-owner rule), `test_table_roles`, `test_coordinated_migrations`,
  `test_tracked_fixture_databases`, `test_registry_audit`, `test_module_catalog_inventory`, `test_public_tip_guards`,
  `test_sqlite_file_copies`;
- **the display-label audit:** `test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`,
  `test_rw5c_labels`;
- **the process-launch allowlist:** `test_codex_lockdown_round3`, `test_ai_tool_isolation`, `test_e0_isolation`,
  `test_codex_tool_lockdown`;
- **the stage's and the batch's own tests:** every `test_ro4_*`, `test_ro5_*`, `test_ro6_*` and `test_rofu_*` but the
  weeks, both `test_rospeed_*`, and the successor tests that pin the defaults snapshots.

The 19 files added to the earlier list are:
- `test_batch3_landing`, `test_data_capture_successor`, `test_diagnosis_input_provenance`, `test_followup_successor`;
- `test_intent_codex_rereview`, `test_learner_report_superseded`, `test_mvp010_upgrade`, `test_plan_determinism`;
- `test_reading_step_switch`, `test_regrade_contract_successor`, `test_ro0_row4_exposure_initiator`;
- `test_ro1_availability`, `test_ro1_availability_reads`, `test_ro1_interval_factor`, `test_ro1_projection`,
  `test_ro1_self_report`;
- `test_serve_eligibility_review`, `test_teacher_te1b_suggestions`, `test_teacher_te1_successor`.

## Files added or changed in this step (for the landing gate)

- **Source:**
  - `src/learnloop/router_objective/value.py`;
  - `src/learnloop/daily_plan/objective_chooser.py`;
  - `src/learnloop/daily_plan/objective_inputs.py`;
  - `src/learnloop/router_objective_switches.py`;
  - `src/learnloop/config/schema.py`;
  - `src/learnloop/config/template.py` (every defaults snapshot);
  - `src/learnloop/params/parameter_registry.py`.
- **Tests:** `tests/test_rospeed_ad_link.py`, `tests/test_rospeed_join.py`, `tests/test_rofu_successor.py`.
- **Docs:**
  - `docs/specs/spec_router_objective_v1.md` (§8, R8's paragraph);
  - `docs/reviews/router-speed-nov6.md` (the corrected claims);
  - this file;
  - the regenerated references (module, DB and configuration, desktop catalogs; 1179 effective configuration leaves).

## For the landing

- **The defaults snapshots.** Every entry of `DEFAULTS_SNAPSHOT_BY_ALGORITHM` moved here, and TE2 moved them on main
  too. Recompute them on the merged tree (`defaults_fingerprint_for_version`), not by picking either side.
- **The merge with TE3a.** TE3a changes `value.py`'s LESSON branch. This step touches `_Model.__init__`,
  `performance`, `_graded_linked`, `_observe`, `_belief_model`, and the signatures of `evaluate`, `baselines` and
  `gain`. None of these is the LESSON branch.
