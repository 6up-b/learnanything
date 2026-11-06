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
