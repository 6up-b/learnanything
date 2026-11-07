# Router speed, Nov 6 (`router/ro-speed`)

Base: main `516db1d862` (the follow-up batch landed at mvp-0.50, head 247).

**No algorithm successor and no migration.** At a fixed number of draws every value the objective computes is the
landing code's: bit for bit, proven by tests that put the landing code back (copied into the test files) and compare.
Nothing moved onto the serving path.

**Corrected after the Codex review (docs/reviews/router-speed-codex-review.md).** Fixed-draw equality is not serving
equality: serving refines until the LLM answers or the deadline runs out, so the faster link completes more draws and
can change `Q̄` and the choice (F1). Item 1 is therefore a serving change behind its own kill switch,
`[router_objective] held_ad_link` (default on, at mvp-0.50), which is in RO6's generator payload, the trace's
`versions.serving_switches` and the prefetch key. Item 2's shared fit is revalidated by the database's commit version,
so a regrade or hold committed between the card's build and the numeric policy's reaches the numeric policy (F2). The
statements below that say "no switch" or "one read per decision" are superseded by that file.

The owner's measurement (docs/reviews/router-followups-nov5.md, "Landing onto main") was:
- the numeric policy was 1.6 to 3.4 times slower than mvp-0.49;
- linear_algebra's Next at a boundary right after feedback went from 2.0 to 3.3 s;
- its follow-up gate went from 302 to 1120 ms.

The causes were R9's quadrature (about half of every evaluation) and item 2's trace join (0.4 to 1.4 s a call, about
2.4 calls a decision).

Fakes only. There was no paid call and no model request. No owner vault or tracked working vault was opened. Every
measurement is on a synthetic vault under the worktree's `fixtures-local/rospeed/`, run under `env -i` with an empty
`HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

## For the owner

- **Nothing to upgrade.** No version moves. Restart the phone host and rebuild the desktop app to pick up the faster
  code. One new switch, `[router_objective] held_ad_link` (on by default; off restores the batch's landing code). The
  traces now record it, so RO6's generator changes once at the upgrade (one change point).
- **Paid routes: none added.** No model request, no learner minutes.
- **Speed**: see "The target" below.

## Commits

| Commit | Item |
|---|---|
| `41e5569b2d` | 1: R9's AD link evaluated once per array (one quadrature for F, F' and logit F; values held per role and recomputed only where the state's bits changed) |
| `139500ed92` | 2: the combiner's join read once per decision; the trace side parsed once per trace content; RO2's resolver indexed by presentation and LO |
| `c85c9c438e` | 4: the two intermittent tests made deterministic (test-only) |
| (this record) | the review file, the regenerated references |

Item 3 was not built (see below).

## Item by item

### 1. R9's link (`value.AdLink`), once per array

**Before.** Each graded attempt computed four quadratures of 32 sigmoids, through four separate calls:
- `F` at the draws' `η`;
- `F` at the belief;
- `logit F` and its slope at the belief;
- `logit F` and its slope at `η`.

Every `P(perform)` read also recomputed `logit F` over every draw and topic, though a tail session changes only a few
cells.

**Now.**
- `AdLink.quadrature` evaluates the sigmoids once and returns `F` and `F'`. The constants (the node shifts, the weights,
  `1 − λ`) are built once.
- `logit_and_slope_from` and `logit_p_from` finish from those values.
- `p`, `slope`, `logit_and_slope` and `logit_p` keep their signatures and their bits.
- `_Model._linked_logit` holds, per role (the draws' `η`, the belief's), the last array and its `F`, `F'` and
  `logit F`. On each call it compares the new state with the held one bit for bit and recomputes only the cells that
  changed.
- A graded attempt and a probe's observation (`_link_cells`) read the held values for the cells they touch. A merged
  session practises the cells its ranking just read, so it computes no quadrature at all.

**Why it is exact.** Every function involved is elementwise. Each element's bits are the same in any array it is
evaluated in: stacked, sliced or a subset. The test checks this property directly.

**Its scope.** The cache belongs to one model, so it is never shared across threads or decisions. The arrays it hands
out are read-only.

**Tests:** `tests/test_rospeed_ad_link.py`. The landing's four `AdLink` methods and the model's four readers
(`performance`, `_graded`, `_graded_linked`, `_observe`) are copied into the test verbatim. The test then compares,
bit for bit, every candidate's `Q` per draw, every term and every branch record (`repr`). It covers:
- every case and option at 8 draws, and the two copy-relevant shapes at 64 draws (24 cases);
- the arxiv_v2-, linear_algebra- and probability-shaped decisions with every switch of the batch on;
- the per-block loop's fallbacks (topics repeating within a session, a dated use inside the horizon);
- the link's log-space tail (`η` near −760);
- every action kind: stop, offer, probe with repair, reading, lesson and sequence;
- `baselines` and `gain`;
- the quadrature against each old call over a grid running from −900 to 745;
- the held values after in-place and one-ulp changes, and on another state.

**Timings.** `value.evaluate`, 64 draws, every switch on, median of three:

| Shape (topics, items per block) | Landing code | Now | mvp-0.49's options (no link, linear combiner, per-block loop, AD's draw) |
|---|---:|---:|---:|
| arxiv_v2-shaped (22, 3) | 1468 ms | 855 ms | 736 ms |
| linear_algebra-shaped (40, 3) | 1863 ms | 958 ms | 798 ms |
| probability-shaped (12, 2) | 1024 ms | 704 ms | 630 ms |

These come from the scratch benchmark `bench_value.py`, run on the same machine with no other load.

**Profile, linear_algebra-shaped.**
- Before: 2.60 s in all. The quadrature took about 2.0 s: `logit_p` 1.46 s and `p` 1.56 s cumulative, mostly
  sigmoids.
- After: 1.12 s in all. The quadrature took 0.22 s, and the held-value bookkeeping 0.04 s.

**What remains above mvp-0.49** (+12% to +20% here) belongs to the batch's own model, not to the link:
- R1's consistent draw computes FSRS's retrievability and a logit on each graded attempt;
- the link still computes one quadrature for each cell a session changes, for each of the two roles.

### 2. The combiner's join, once per decision and incremental

- **Once per decision.** `objective_inputs.decision_reads()` is a context scope, and the prefetch job
  (`_objective_job`) runs inside it.
  - Inside the scope, every `build` of the decision reads the combiner's fit once, keyed by database, `now` and
    vault. These builds are the card's (for the LLM policy's reference row), then the numeric policy's.
  - Before, the join ran once per build, about 2.4 times a decision.
  - The fit is the decision's as of its first read, just as `now` is. So the card's reference row and the numeric
    policy's `Q` now value one fit, where before a write landing between the two reads could give them two.
  - Nothing outlives the scope. The next decision reads afresh, so a regrade, a hold, a late-received outcome or late
    activity enters it. A test shows exactly this.
- **Incremental on the trace side.**
  - `combiner_data._untouched` parses each plan-block trace's untouched topics and sensors once per trace content. It
    is keyed by a blake2b digest of the drawn option and the trace's whole JSON text, so a trace rewritten in any byte
    is parsed again. Traces are immutable in the schema anyway (`router_objective_traces_no_update`).
  - Each decision's first presentation served by `now` is one read, not one query per trace.
  - The outcome side is read at every call: presentations, RO2's resolution, received time, regrades and holds.
  - The bound `_PARSED_LIMIT` (4096) is a keep bound, classified in the parameter registry. The resolver's
    `_FLAT_CURVE` is classified too, now that the module is in the inventory.
- **RO2's resolver, linear in an LO's rows.** `_resolve_groups` indexes the attempts by presentation and by LO, and the
  reveals and readings by LO, once per call. Each list keeps the rows' own order. Before, every group scanned every
  attempt twice and every reveal and reading once, so the join grew with the square of the log.

**Not built as written: caching the joined rows of closed traces by trace id with a data fingerprint.**
- Why: a closed row depends on LO-wide data:
  - every attempt on the LO before its outcome (`first_seen` and the first qualifying answer);
  - each one's grading and hold (AD's events through the material view);
  - every reveal and reading on the LO (late activity can censor it);
  - the block's own attempts.
- Only the vault-wide loads deliver that data, through the material view's filters for holds and protection. They
  are presentations, attempts, `replay.load_events`, reveals, and the readings (`listed_events`, which maps every
  completed section to its LOs).
- A sound fingerprint must read all of it, so it would cost what the row costs, and every answer moves some LO's
  fingerprint.
- What was built instead is the smallest exact alternative: one read per decision, the parse incremental on the
  trace side (the part that is immutable), and the resolution made linear.
- **What remains**: the loads themselves. The owner's linear_algebra profile put the readings at about 0.4 s of a
  0.47 s call: `_opportunities` 2.78 of 3.28 s over 7 calls, and `learning_objects_for_section_in_ir` 1.8 s, which
  reloads the textbook's IR from `source_document_blocks` at every call.
- **The smallest finish**: hold the section→LO map across calls.
  - Key it by the extraction id, the vault object and a fingerprint of the content rows the map reads: the
    extraction run, the revision, the artifact and the span-alias rows.
  - Evaluate the withheld rule (`VaultReadingMap.withheld`, the material view's holds) fresh at every call before the
    map is read, as it is now.
  - This sits in AD's reading code (`adaptive_difficulty/reading.py`, `section_map.py`). It needs a reviewer of AD's
    protection layer, so it is not built here.

**Tests:** `tests/test_rospeed_join.py` (70). The landing's `combiner_data.groups` and
`history_resolve._resolve_groups` are copied in verbatim. The tests cover:
- **The resolver's loop**: 60 randomized logs through a fake view. Each log has blocks with several presentations,
  attempts with and without presentations or LOs, ineligible and ungraded events, reveals, readings, groups with
  missing presentations, and ties. Each one's rows equal the landing code's, as objects and as sorted JSON.
- **The groups**: five moments on a trace table. It has several presentations per decision (a tie on `served_at`),
  a block served after the moment, a stop, an interrupt, a trace after the moment, an option whose topics are all
  its own, `llm_forecast` and `ad_eta: None`. The tests also cover a rewritten trace (parsed again), a caller editing
  a group (the held parse is untouched) and the bound.
- **The fit on a real journey.** The journey is at the tag, with both policies on fakes. Four cold outcomes are
  answered through the real self-grading pipeline. The fit (its coefficients' bits, sources and counts) equals the
  landing code's at each step:
  - answered: 4 joined rows;
  - a regrade (`insert_regrade_evidence`): 3;
  - a hold (a regrade into a held blind record, `test_held_grade_evidence._hold_by_regrade`): 2;
  - a late-received outcome (`received_at` after the moment): 1;
  - late activity (a reveal stamped between the block and the outcome, recorded afterwards): 0.

  Each step changes the fit, so no read was stale.
- **One read per decision.** Inside `decision_reads` three reads give one object and one resolver call. Another
  moment is its own read. Outside the scope every read is a read. A regrade between two scopes enters the second.
- **On the journey's prefetch jobs**: one combiner read per decision's `now`, and fewer reads than builds.

**Timings** (synthetic vaults, `OI._combiner` as of the log's end, median of five after the first):

| Vault | Traces, attempts | Landing code | Now |
|---|---|---:|---:|
| 6 topics x 5 items, 15 days | 67, 129 | 62 ms | 57 ms |
| 16 topics x 8 items, 15 days | 71, 177 | 72 ms | 63 ms |

The synthetic journeys have no Reader sources and only 13-71 traces, so a call is small here. The saving that carries
to the copies is the reads per decision: 2 to 1 per prefetch job (the test's count). On the owner's linear_algebra copy
that is 0.4 to 0.9 s a decision.

### 3. RO6's closed transitions and RO5's closed-window scores: not built

Measured as of the 16-topic vault's end (69 transitions, 11 scored windows):
- `tail_data.transitions` takes 15.5 ms;
- `tail_data.fits` 17.1 ms;
- `scores.scores` 14.6 ms;
- `current_weight` 23.2 ms.

That is about 30 ms a decision at two weeks of log, against hundreds of ms in items 1 and 2. A data-fingerprint cache
here must invalidate on every input a closed transition or window reads:
- the window's activity (late activity);
- each check's outcome (a regrade or a hold);
- the completion rate and prices as of the window's end;
- exam results known by `at`.

Each of those is a SQL read of the same size as the computation. Not built, as "if time allows" permits.

**The smallest finish**: key each closed transition's reward by its two decision ids, plus a digest of:
- the session rows in `(start, end]`;
- the resolved checks planned in the window, with their outcome, status and received time;
- the price rows as of `end`;
- the dated uses' import rows.

Recompute open and censored ones every call. Test it as item 2's fit test does.

### 4. The intermittent tests (test-only)

- **`tests/test_ro5_landing.py`, the r8 test.** It now pins `block_drawing_seed()` (RO6's landing ruling R14), as the
  R5 (1) test beside it does. Unpinned, the plan's first draw was a stop about one run in six, so the fixture's first
  advance found no block (`'done' == 'item'` at line 412).
  - Reproduced: 1 of 12, then 1 of 9, runs alone before the fix.
  - After: 0 failures in 22 runs alone.
- **`tests/test_rofu_carried.py`, the early-publication test.** The serve's `Prefetch.wait` now runs out right after
  the numeric job's early publication, by events (the publication or the job's completion), instead of a real 3 s wait
  against a publication of about 2.2 s. On a loaded machine the publication took more than 3 s, so the serve found
  nothing published. A prefetch with no numeric component, and every serve once the LLM is released, waits as the
  runtime does. 8 of 8 runs passed.

## The target: Next at a boundary right after feedback, and the follow-up gate

**How it was measured.** The scratch harness `bench_e2e.py` runs RO6's journey on a synthetic vault created for the
run:
- a seeded ~70% learner, with one day a week off;
- both policies answering through inline fakes, with a pinned block-drawing seed;
- Next run right after each answer (dwell 0);
- the follow-up gate (`ObjectiveFollowupGate.decide_followup`, as FG1 calls it after a miss) asked after every other
  answer.

Only the last six days are timed. Three runs per shape: the landing code (`git archive 516db1d862`) at mvp-0.49, the
landing code at mvp-0.50, and this branch at mvp-0.50, one after another on an otherwise quiet machine.

| Shape | Side | Traces at end | Next at a boundary, ms (median, n) | Follow-up gate, ms (median, n) | Numeric per decision, ms | Combiner reads per boundary (ms each) |
|---|---|---:|---:|---:|---:|---|
| linear_algebra-shaped: 16 topics x 8 items, 14 + 6 days | landing code, mvp-0.49 | 111 | 3158 (26) | 939 (34) | 872 | 2 (9; no join below the tag) |
| | landing code, mvp-0.50 | 110 | 2868 (25) | 795 (37) | 739 | 2 (91) |
| | **this branch, mvp-0.50** | 105 | **2568 (27)** | **705 (35)** | 601 | **1** (74) |
| arxiv_v2-shaped: 22 topics x 4 items, 8 + 6 days | landing code, mvp-0.49 | 95 | 3246 (37) | 942 (58) | 955 | 2 (8) |
| | landing code, mvp-0.50 | 94 | 3425 (37) | 929 (58) | 893 | 2 (97) |
| | **this branch, mvp-0.50** | 95 | **2943 (38)** | **799 (59)** | 697 | **1** (79) |

**The target is met on both shapes.**
- linear_algebra-shaped, against mvp-0.49: Next at a boundary 19% faster, the gate 25% faster.
- arxiv_v2-shaped, against mvp-0.49: Next 9% faster, the gate 15% faster.
- Against the landing code at mvp-0.50, Next is 10-14% faster and the gate 11-14% faster.

The journeys differ in their draws, and so in their logs: each boundary key names the run's plan ids, which seed the
rollouts. Their values are compared in the equality tests, not here.

**These synthetic journeys do not reproduce the landing's regression**, because the regime differs from the owner's
copies in three ways:
- the inline fakes answer at once, so the numeric policy stops at its first 8 draws;
- the journeys have no Reader sources, so the join has no readings to map;
- the logs are short.

Two measurements show what remains in the owner's regime:
- **The numeric policy at the refinement's ceiling (64 draws)**, item 1's table: the linear_algebra-shaped decision
  takes 958 ms against 798 ms with mvp-0.49's options (+20%). The arxiv_v2-shaped one takes 855 ms against 736 ms
  (+16%), and the probability-shaped one 704 ms against 630 ms (+12%).
  - What remains is R1's and R9's own work: one quadrature per changed cell per role, and the consistent draw's
    retrievability.
  - That is down from +133%, +99% and +63% at the landing.
- **The join's readings** on a copy: about 0.4 s a call by the landing's profile (item 2's smallest finish).
  - The per-decision read already halves the prefetch's share of it.
  - The follow-up gate makes a single build, so its one read is still a full join.
  - So on the owner's linear_algebra copy the gate's remaining excess over mvp-0.49 is expected to be about that one
    join (0.4-0.9 s), less item 1's saving in its three-sequence evaluation. It must be measured at the landing gate's
    smoke.

## The gate (this step)

The full suite, the whole durability lane and the whole vitest run belong to the landing gate.
- No frontend or `src-tauri` file changed, so no npm, vitest or cargo step applies.
- No schema change and no DB or connection code changed, so no durability-marked test applies.

| Step | What ran | Result |
|---|---|---|
| Setup | `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | ok |
| Import contracts | `uv run lint-imports --no-cache` (under `env -i`) | 43 kept, 0 broken |
| Iterating | `tests/test_rospeed_ad_link.py` with the value and link files (`test_rofu_ad_link`, `test_rofu_ad_latent`, `test_rofu_ad_stable`, `test_rofu_speed`, `test_rofu_review_draw`, `test_rofu_monotone`, `test_ro4_value`), `-n 6` | 110 passed |
| | `tests/test_rospeed_join.py`, `test_rofu_learning`, `test_ro2_history_resolve`, `test_ro4_codex_review`, `test_registry_audit`, `test_field_workbench_signals`, `test_salience_firewall`, `-n 6` | 5682 passed, 3 skipped |
| | the r8 test alone, 22 times; the early-publication test alone, 8 times | 22/22, 8/8 passed |
| Targeted set, after every commit | 112 files, `-n 6`, behind `flock /tmp/learnloop-fullsuite.lock`. They are: every file naming a changed module (`objective_inputs`, `objective_chooser`, `combiner_data`, `history_resolve`, `router_objective.value`, `parameter_registry`, `AdLink`); every `test_ro4_*`, `test_ro5_*`, `test_ro6_*` and `test_rofu_*` but the weeks; both `test_rospeed_*`; and the contract and audit set. The contract and audit set is `test_config_refactor` (the defaults snapshot), `test_cli_help_snapshot`, `test_sidecar_serializer_snapshot`, `test_desktop_rpc_contract`, `test_mobile_allowlist`, `test_architecture` (the frozen cycles, the SQL-owner rule), `test_table_roles`, `test_coordinated_migrations`, `test_tracked_fixture_databases`, `test_registry_audit`, `test_module_catalog_inventory`, `test_public_tip_guards` and `test_sqlite_file_copies`, plus the display-label audit (`test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`, `test_rw5c_labels`) and the process-launch allowlist (`test_codex_lockdown_round3`, `test_ai_tool_isolation`, `test_e0_isolation`, `test_codex_tool_lockdown`) | **7772 passed, 13 skipped, 1 xfailed** (51 min on a shared machine) |
| References | `module_generate.py` / `module_validate.py` (PASS); `db_generate_reference.py` / `db_validate_reference.py` (errors []: head 247, no schema or configuration change, so stamps only); `desktop_generate.py` / `desktop_validate.py` (passed); `validate_vault.py` (passed) | ok |

- Every test ran inside `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, at most `-n 6`, one run at a
  time.
- Every script outside pytest ran under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, and
  `TMPDIR` outside the worktree. That covers the benchmarks, the synthetic journeys, lint-imports and the reference
  scripts.
- The landing code for the "before" timings was a `git archive` of `516db1d862` in the scratch directory, run on this
  worktree's venv.

## Files added or changed (for the landing gate)

- Added: `tests/test_rospeed_ad_link.py`, `tests/test_rospeed_join.py`.
- Changed tests: `tests/test_ro5_landing.py`, `tests/test_rofu_carried.py`.
- Changed source:
  - `src/learnloop/router_objective/value.py`;
  - `src/learnloop/router_objective/combiner_data.py`;
  - `src/learnloop/adaptive_difficulty/history_resolve.py`;
  - `src/learnloop/daily_plan/objective_inputs.py`;
  - `src/learnloop/daily_plan/objective_chooser.py`;
  - `src/learnloop/params/parameter_registry.py`.

Old item difficulty scalar (owner, Nov 5): `git diff 516db1d862 -- src migrations` adds no reader or writer of the
difficulty columns, `mastery.irt.difficulty_from_prior` or surprise's `b`.

## Open items

- **AD's section→LO map held across the join's calls**: the dominant cost left on the copies (item 2's smallest
  finish).
- **Item 3's caches** (smallest finish above).
- **The copies' own numbers.** The copy-shaped timings above are on synthetic vaults with no Reader sources. The
  landing gate's smoke on the owner's copies is where the join's readings show. Rerun its "Time" table there.

## Landing onto main

Prepared on `router/ro-speed` for the orchestrator's fast-forward. Main was merged three times:
- `b1c67e1f52`: main `64f7d1dc86` (TE2 as mvp-0.51, migration 248; the teacher exam-question guard);
- `1ccf60fe9a`: main `8b0738499d` (TE3a as mvp-0.52, migration 249). TE3a's lesson-window reset now also runs on the
  held link's path, with a test;
- `7514676e5c` and `b1693676a8`: main `1c12763372` (the phone frontend v2 spec and the owner's phone follow-ups) and
  `23ce859c16` (phone V1). These are phone app, host and docs only: no router change, no successor, no migration. The
  module reference's provenance conflicts were taken from main and regenerated (`ae87b5fd8d`).

**Still no successor and no migration.** The tip runs at main's mvp-0.52, head 249. `held_ad_link` stays on by
default.

### Time (ruling R5): the journey pinned on all three codes

**How it was measured.**
- Copies: fresh backup-API copies of `~/learnloop-backups/mvp043-20261103-copy`, two sets:
  - mvp-0.49 copies, upgraded on `e7a7d7734f`'s code;
  - mvp-0.52 copies, upgraded on main `8b0738499d`'s code.
- Network: every AI route points at 127.0.0.1:9. The router LLM and the Decider are in-process fakes, and the follow-up
  probe is written by the tests' AuthorFake.
- Pinning: `SMOKE_PIN_SEED=1` and `SMOKE_PIN_KEY=1` on all three codes. The rollout seed is the decision id, and the
  boundary key's version string and switch snapshot are dropped.
- Codes: git archives (with `migrations/`) of mvp-0.49's `e7a7d7734f`, main `8b0738499d` and the branch `1ccf60fe9a`.
  - Main's later commits (`1c12763372`, `23ce859c16`) change no router file.
  - Since `1ccf60fe9a`, the branch changes only `src/learnloop/capture/` and `src/learnloop_mobile/` (both from main).
- Each day run: one simulated day per copy. The second served item is answered wrong (FG1's follow-up), and the first
  offered stop is declined. Next is pressed at once ("dwell 0") or after a 3 s sleep. Fresh copies for every run.
- The week: linear_algebra, 7 days, day 3 skipped, a seeded learner who is about 70% correct, offered stops kept or
  accepted at random (seeded), Next at once.
- Conditions: every run held `/tmp/learnloop-fullsuite.lock`, one run at a time (load average 1-3). The driver records
  every span with its thread and attributes each Next to the spans that overlapped it.

**The served journeys.**
- Main and the branch serve the same items in the same order in every run, the week included (106 items).
- mvp-0.49 matches them on probability only.
  - On arxiv_v2 and linear_algebra it diverges after the second item. Its policy is a different algorithm, so the
    pinned seed fixes the draws, not the choices.
  - Its week serves 125 items.
- So mvp-0.49's column is the same journey shape on the same copy, not item for item.

**"Next after feedback"** is a block-boundary Next that serves an item and immediately follows an answered item: its
feedback, then the app's prefetch call, then the dwell. These are excluded:
- the first Next of a day;
- the probe opened by `followup_next`;
- a Next right after a declined stop (reported separately below).

The Next column gives median / p90 (nearest rank) / the count above 2 s, in ms. The day runs have only 1-3 such Nexts
per cell; the week is the distribution to read.

| Copy | Code | Numeric policy per decision, ms: median (p90, n) | Next after feedback, dwell 0 | Next after a 3 s dwell | Follow-up gate, ms, median (n): objective-decided / no room to wait |
|---|---|---|---|---|---|
| arxiv_v2 | mvp-0.49 (`e7a7d7734f`) | 1324 (1462, 12) | 2310 / 2310 / 1 of 1 | 568 / 568 / 0 of 1 | 763 (2) / - |
| | main (`8b0738499d`) | 2221 (2285, 10) | 3399 / 3469 / 2 of 3 | 677 / 708 / 0 of 3 | - / 206 (2) |
| | **branch** | **1932** (2009, 10) | **2892** / 3112 / 2 of 3 | 530 / 546 / 0 of 3 | - / 198 (2) |
| linear_algebra | mvp-0.49 | 673 (995, 10) | 1975 / 2401 / 1 of 3 | 673 / 697 / 0 of 3 | - / 195 (2) |
| | main | 1509 (2183, 10) | 2422 / 3564 / 2 of 3 | 615 / 688 / 0 of 3 | - / 201 (2) |
| | **branch** | **1369** (1941, 10) | **2359** / 3394 / 2 of 3 | 674 / 704 / 0 of 3 | - / 199 (2) |
| probability | mvp-0.49 | 181 (209, 10) | 1179 / 1204 / 0 of 3 | 662 / 699 / 0 of 3 | - / 205 (2) |
| | main | 615 (624, 10) | 2026 / 2045 / 2 of 3 | 669 / 702 / 0 of 3 | - / 177 (2) |
| | **branch** | **600** (664, 10) | **2035** / 2061 / 2 of 3 | 731 / 782 / 0 of 3 | - / 176 (2) |
| linear_algebra, a week | mvp-0.49 | 741 (994, 60) | 2221 / 2724 / 25 of 30 | - | 796 (9) / 228 (19) |
| | main | 1434 (2042, 60) | 3404 / 4008 / 26 of 27 | - | 1314 (11) / 233 (13) |
| | **branch** | **1348** (1922, 60) | **3403** / 3815 / 26 of 27 | - | 1298 (11) / 236 (13) |

**Next right after a declined stop.** There is no prefetch and no dwell before it. Pooled over every run of a code
(n 8): mvp-0.49 1832 / 2208 / 3 of 8; main 2922 / 3918 / 6 of 8; the branch 2757 / 3525 / 6 of 8.

**What the table says.**
- **Branch against main.** The numeric policy is 2-13% faster per decision (arxiv_v2 -13%, linear_algebra -9%,
  probability -2%, the week -6%).
  - Next after feedback is 15% faster on arxiv_v2. It is unchanged on linear_algebra and probability: the week's
    median is 3403 against 3404 ms, and its p90 3815 against 4008 ms.
  - The objective-decided gate is unchanged (1298 against 1314 ms).
- **Branch against mvp-0.49.** The branch is still slower everywhere.
  - Numeric per decision: +46% on arxiv_v2, +103% on linear_algebra, +230% on probability, +82% on the week.
  - Next after feedback in the week: +53% (3403 against 2221 ms).
  - The objective-decided gate: +63% (1298 against 796 ms). The no-room path is unchanged at about 230 ms.
- **The owner's regression is mostly not closed by this branch** on the Reader-heavy copies. Why is next.

**Why Next is bimodal** (from the per-Next span overlap and the profile below):
- After feedback, the app's prefetch call starts the next decision's objective job on a router thread. A boundary Next
  that comes before the job is done waits for it.
- With dwell 0, every boundary Next after feedback waited on that job (began before Next, overlapping it), so Next is
  the job's remaining time.
  - The week's job takes 3302 ms median on the branch (p90 4237), 3391 ms on main and 2053 ms on mvp-0.49.
  - 26 of 27 such Nexts are above 2 s.
  - The one fast Next per week (1.6 s) is the one whose job found the combiner's join already current (26 ms
    instead of about 1.1 s).
- With a 3 s dwell, the job is done when Next is pressed, so Next is the serve alone: 0.5-0.8 s on every copy and
  code.
- So the two modes are "the job finished" (about 0.6 s) and "Next waits for the job" (the job's length). Which
  component puts a waiting Next above 2 s depends on the copy.
  - **linear_algebra and probability: the combiner's join**, inside the input build. In the branch's week, over the
    26 slow Nexts (median overlaps, nested):
    - input build 1510 ms, of which the join is 1145 ms;
    - inside the join, RO2's `resolve_curves` 1128 ms, its `_opportunities` 954 ms, and AD's section-to-LO map
      912 ms;
    - the numeric policy 1348 ms, of which the rollouts are 1214 ms;
    - the decision card about 400 ms, running alongside.
    - AD's section map was called 3,794 times in the pinned week (11 ms median, main and branch alike). The unpinned
      held-on week below called it 5,004 times. mvp-0.49 called it 1,899 times at 1 ms (no join).
    - On probability's day runs, the two slow Nexts spend 1.1 s in the join (0.95 s of it AD's section map) and only
      0.63 s in the numeric policy.
  - **arxiv_v2: the rollouts.** The numeric policy is about 2.0 s per decision (rollouts 1.85-2.3 s), and the join is
    only about 0.16 s.
- The join runs about twice per decision: 109 joins over 49 jobs in the week, and in the profile 98 builds and 98
  joins over 49 jobs. That matches the decision scope's commit-version check (F2, accepted in R2) dropping the shared
  fit when a receipt commits between the card's build and the numeric policy's. Every decision here makes a router
  LLM request, which writes a receipt. So item 2's per-job saving is mostly lost on these copies, as R2 foresaw. The
  cause was not traced call by call.

**Profile: the branch, linear_algebra, the pinned week.** This is a separate run under cProfile (49 objective jobs,
4.25 s median per job under the profiler, against 3.30 s without), merged over every job. Cumulative per job:
- `objective_inputs.build` (2 calls) 1.69 s:
  - `_combiner` 1.40 s;
  - `_combiner_with_traces` (the join) 1.18 s;
  - `history_resolve.resolve_curves` 1.18 s, with `_opportunities` 0.96 s;
  - `adaptive_difficulty.reading.los_for_section` (AD's section map; 56 calls a job) 1.25 s;
  - `reading_sources.listed_events` 0.88 s.
- `objective_chooser.run_numeric` 1.71 s:
  - `value._session` 2.14 s, a sum across threads that includes calls outside `run_numeric`;
  - `run_tail` 1.07 s;
  - `evaluate` 1.01 s;
  - `_practice_batch` 1.32 s, of which `_graded_linked` is 0.54 s and the AD link's `quadrature` 0.12 s.
- SQLite: `execute` 1.16 s of internal time a job. Connection open and close: 462 `connect` calls a job, 0.82 s
  cumulative, of which `close` alone is 0.32 s. They come through `Repository.connection` (683 calls a job). The
  profile kept no caller table, so which readers open them is not measured; AD's `material_view` reader and
  `operation.scoped` are the largest cumulative entries around them.

What remains, in order:
1. The join's AD section map and RO2's opportunity resolve: R3's follow-up, about 0.9-1.2 s a job here, larger than
   R3's 0.4 s.
2. The rollouts: R1/R9's own work, about 1.2-1.4 s.
3. Connection churn: about 0.8 s.
4. The second join a decision (see above).

**Unpinned runs (context only).** The earlier unpinned runs (the scratch directory's `out/unpinned/`, a less quiet
machine) served a different journey per code (on linear_algebra, 11 numeric decisions on main against 4 on the branch). Their medians mix
journey and speed. For example, linear_algebra's numeric policy ran 1403 ms on the branch against 1305 ms on main, but
arxiv_v2's 1729 against 2384. They are not compared here.

### Orchestrator rulings (verbatim)

- R1: "F1 is versioned by the held_ad_link switch in the generator payload, trace and prefetch key, as the follow-up
  batch's merged_sessions was; no separate tag. With it off the landing code's quadratures run element for element and
  a deadline-bound decision is the landing code's draw for draw (the test stays)."
- R2: "F2's database commit-version check is accepted, including losing most of item 2's per-job saving when an LLM
  request's receipt commits between the builds. The watcher is a read-only connection that never writes; confirm under
  the durability lane that it leaves no -wal frames, no journal header change and no lock that blocks a writer (a test:
  a writer commits while the watcher is open)."
- R3: "The remaining join cost on Reader-heavy vaults (AD's section-to-LO map rebuilt per call, about 0.4 s) goes to
  the follow-up batch, with a reviewer of AD's protection layer; this landing measures it on the copies."
- R4: "The watcher finding is accepted: a writer that commits and closes while the read-only watcher is open leaves
  its own frames in the -wal until the next read-write connection closes, which is generic SQLite behaviour shared by
  the app's existing read-only watchers (reading_choice, canonical_projection_rollout); no frame comes from the watcher,
  nothing is lost, and the stop condition 'the watcher leaves WAL frames' is not met. The test documents it."
- R5: "The time table is measured with the journey pinned (SMOKE_PIN_SEED=1 and SMOKE_PIN_KEY=1 on all three codes:
  mvp-0.49's e7a7d7734f, main 8b0738499d and the branch), so all three serve the same items in the same order; report,
  per copy, the numeric policy per decision, Next at a block boundary right after feedback and after a 3 s dwell (as
  distributions: median, p90, and the share above 2 s, since Next is bimodal), and the follow-up gate. Explain the
  bimodality from the profile (which component puts a Next above 2 s: the prefetch not done, the join, AD's section
  map at about 4,400-5,000 calls a week, the rollouts). The unpinned runs are reported only as context. Run the timing
  when no full suite holds the lock, so the machine is as quiet as the queue allows."

R5's premise that all three serve the same items holds for main and the branch, and for mvp-0.49 on probability only
(see "The served journeys").

### Identity: held_ad_link = false against main

Main `8b0738499d` against the branch with `[router_objective] held_ad_link = false`, both at mvp-0.52 on fresh copies
of the mvp-0.52 set. One day per copy: the second served item missed (FG1's follow-up, AuthorFake's probe), the first
stop declined, `SMOKE_PIN_SEED=1` and `SMOKE_PIN_KEY=1` on both sides.

**IDENTICAL on all three copies** (arxiv_v2, linear_algebra, probability):
- LLM requests (5 each), Decider requests (5 each) and the follow-up gate (1 each);
- the 5 traces each, every prompt, and every written and removed row;
- every trace at 8 draws.

Set aside, on both sides alike:
- `held_ad_link` wherever it is recorded: a receipt's config record, and the trace's `versions.serving_switches`;
- RO6's `generator` key, which names the version and the switch record;
- the boundary key's version string and `objective.followup_switches` (`SMOKE_PIN_KEY`);
- ids (ULIDs and hex digests), wall-clock stamps, latencies, and a compressed receipt's `stored_bytes`;
- version strings, normalized.

`receipts_real` counts the copies' own older receipts (42 on probability, equal on both sides). Every new receipt on
both sides is a fake (below).

### Watcher (R2, R4)

`tests/test_rospeed_watcher.py` runs under the durability lane (WAL, `synchronous=FULL`, a freshly initialised
vault):
- A writer commits (`BEGIN IMMEDIATE` and `BEGIN EXCLUSIVE`, no busy wait) and a `TRUNCATE` checkpoint completes while
  the decision scope's watcher is open. The watcher never writes, leaves no -wal frames of its own and no journal
  header change.
- A writer that closes before the watcher leaves only its own frames (R4).
- A rollback-header database is watched without blocking a writer.

It passed in the targeted sets and in the durability lane (below).

### Gate

| Lane | On | Result |
|---|---|---|
| Setup | `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | ok |
| Import contracts | `lint-imports --no-cache` | 43 kept, 0 broken |
| Full suite | `1ccf60fe9a`, `-n 8 --dist worksteal`, behind `flock /tmp/learnloop-fullsuite.lock`, 10G scope | **29955 passed, 91 skipped, 47 xfailed, 1 failed** (57 min 47 s) |
| | the failure alone, 3 times | 3 of 3 passed |
| Durability lane | `1ccf60fe9a`, `-m durability`, `-n 6` | 407 passed, 1 skipped |
| Owner lane | `1ccf60fe9a`, fresh backup-API copies of `owner-copies-mvp035` in `fixtures-local/landing-rospeed/`, `-m owner_vaults` | 83 passed, 4 skipped, 2 failed: the two known (`test_activity_backfill`, `test_placement_fixture_copies[arxiv_v2]`) |
| Targeted set, after the `1c12763372` merge | `7514676e5c`: step 1's 142 files plus `test_mobile_allowlist`, `test_mobile_rpc`, `test_mobile_shortcuts`, `test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot` (147 files), `-n 6` | 2882 passed, 12 skipped, 3 xfailed |
| Targeted set, after the `23ce859c16` merge | `ae87b5fd8d`: the same plus every `test_mobile_*` (159 files), `-n 6` | 3109 passed, 12 skipped, 3 xfailed |
| References | `db_generate_reference` / `db_validate_reference` (errors []), `desktop_generate` / `desktop_validate`, `module_generate` / `module_validate`, `validate_vault` | all pass; provenance and the test inventory only |

The full-suite failure was `tests/test_ro0_rows9_13_decision_state.py::test_receipts_hold_ids_and_numbers`. It asserts
that a learning object's title (`M2`) is absent from a receipt's serialized state, and a random ULID in that state
contained `M2` (`...S6NMV11D83M2VGNAKBXANP`). This is a test flake, unrelated to this branch.

What did not rerun:
- No full suite after the two phone merges (`1c12763372` and `23ce859c16`), as the orchestrator ruled: they change no
  router file.
- No vitest or cargo: the branch changes no frontend or `src-tauri` file. The phone app's files come from main as
  they are.

### Smoke

**held_ad_link on (the default, unpinned, as served).** The branch ran on fresh copies of the mvp-0.52 set: one day
on each copy (a generated follow-up, the first stop declined) and the linear_algebra week. Then, on each run:

| Run | Decisions | RO6 trace terms recomputed | RO5 logged probabilities | Generated probes served, then refused | rebuild --shadow | Survival |
|---|---|---|---|---|---|---|
| arxiv_v2 day | 8 | v_residual 35, v_tilde 35, calibration 8: 0 problems | 8 coins, 1 check day: 0 problems | 1, refused (`generated_probe_closed`) | 26 mastery rows, stamp only; live unchanged | assignments and traces identical across `rebuild-derived-state` and a state sync |
| linear_algebra day | 4 | 24, 24, 4: 0 problems | 4 coins: 0 problems | 1, refused | 18 rows, stamp only | identical |
| probability day | 5 | 19, 19, 5: 0 problems | 5 coins: 0 problems | 1, refused | 16 rows, stamp only | identical |
| linear_algebra week | 50 | 259, 259, 50: 0 problems | 50 coins, 6 check days: 0 problems | 30, each refused | 14 rows, stamp only | identical |

- "Stamp only" means `algorithm_version` from mvp-0.47 to mvp-0.52 on rows with no evidence, the known case. No
  facet or schedule changes.
- The protection scan of both cards showed nothing protected shown. The objective report as of each run's end exited
  0.

**Network and processes.**
- New `model_call_receipts`: the four held-on runs wrote 29, 17, 20 and 440, all fakes (`fake_llm`/`fake-router-llm`,
  `fake_decider`, `fake`/`fake-model`, `fake`/`fake-frontier`). Zero from a real model.
- The socket and subprocess watch (`sitecustomize` on every smoke run) logged no connect, no non-loopback address
  and no name resolution.
- The only subprocesses were `powerprofilesctl get` and `git rev-parse HEAD` on the archived trees' `data_capture`
  directory. No Codex process.

**Stop conditions: none met.**
- Serving with `held_ad_link` off is main's.
- Every trace term recomputes.
- The watcher neither writes nor locks a writer out, and leaves no frames of its own (R4).
- No work moved onto the serving path.
- The shadow shows stamps only.
- No real model call.
- The one failure passed 3 times alone.

### What the owner does

- **Nothing beyond restarting the desktop app and the phone host** after the fast-forward. No version moves, no
  migration, nothing to upgrade or rebuild.
- **To turn the held link off**, set `held_ad_link = false` under `[router_objective]` in the vault's
  `learnloop.toml`, then restart the app and the phone host. Serving is then the follow-up batch's landing code, draw
  for draw (R1). The traces and the prefetch key record the switch.

### Open items

- **The speed target is not met on the Reader-heavy copies.**
  - linear_algebra's Next after feedback is unchanged against main (3.4 s median in the week) and still 53% slower
    than mvp-0.49.
  - Its objective-decided gate is still 63% slower than mvp-0.49.
  - The cost is the join, as R3 expects, but larger than R3's 0.4 s:
    - AD's section map is about 0.9 s a decision;
    - RO2's opportunity resolve is about 1.0 s;
    - the join runs twice a decision, consistent with F2's check.
  - R3's follow-up should take the section map and the opportunity resolve together. It should also look at the
    462 connection opens a job in AD's readers.
- **The rollouts** are still +82% per decision against mvp-0.49 in the week. They are R1/R9's own work, the larger
  share on arxiv_v2.
- **Test flake**: `test_ro0_rows9_13_decision_state::test_receipts_hold_ids_and_numbers` checks a two-character title
  (`M2`) as a substring of a state that holds random ULIDs. The assertion should match whole tokens, or the title
  should not be a valid ULID substring.
