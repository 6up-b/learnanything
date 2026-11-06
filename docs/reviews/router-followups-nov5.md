# Router objective follow-up batch, Nov 5 (`router/ro-followups`)

Spec: `docs/specs/spec_router_objective_v1.md` (§8.11, §9.1, §10.1 as built; §11). Items from the landing records of
RO1, RO2, RO4, RO5, RO6 and FG1d (open items and rulings). Base `e7a7d7734f` (RO6 landed: mvp-0.49, head 246).
Successor **mvp-0.50** (`ROUTER_FOLLOWUPS_ALGORITHM_VERSION`) <- mvp-0.49, rechecked at landing. **No migration.**
Fakes only: no paid call, no real request, no owner vault opened, no tracked working vault touched, no manual run on
a copy (every measurement below is on a synthetic vault, in a test or a scratch script under `env -i`).

## For the owner before landing

- **Enabled at the tag by default**, where RO4's objective serves. `learnloop upgrade` (default target) moves a vault
  from mvp-0.49; nothing recorded changes (a projection activation, journalled like its predecessors).
- **Each part that changes serving has its own switch** under `[router_objective]`, default true; any off, or below
  the tag, that part is mvp-0.49's exactly:

  | Switch | Item | Off |
  |---|---|---|
  | `combiner_trace_outcomes` | 2: the combiner also fitted on the traces' joined outcomes | RO5's checks-only fit |
  | `merged_sessions` | 3: the tail's sessions merged (faster, so a deadline admits more draws; Codex review F2) | the per-block loop |
  | `consistent_review_draw` | 7 (landing ruling R1): a practised topic's practice outcome in the rollouts drawn from the memory model's own `P(perform)` | AD's predictive alone |
  | `monotone_combiner` | landing ruling R6: the combiner monotone in ability by construction (η's slopes log-normal in its prior and fit) | RO4's linear combiner |
  | `ad_predictive_link` | landing ruling R9: the rollouts read AD's own predicted success `F(η)`, with its lapse term, on AD's latent | `σ(η)` on `logit p̄` |
  | `carried_in_prefetch` | 4: the carried valuation deferred to the next prefetch, recorded in a later trace | RO6's R12/R3 (censored) |
  | `scope_extension` | 5: a growing retention scope is not an objective change | RO6's R11 (a change point) |

  Under landing ruling R8 every switch above except `carried_in_prefetch` is part of RO6's generator version, so
  flipping one is a change point for the learned tail's fit. Step 4's every-switch-off identity covers seven
  switches: the brief's five, plus `monotone_combiner` and `ad_predictive_link`.

- **Paid routes: the batch adds no model request.** No call per day.
- **Learner minutes: none.** No arm is added.
- **Latency**: see the table under item 3 (the numeric policy is faster) and item 2 (the combiner's join adds a read
  of the traces and one call to RO2's resolver per decision, in the numeric job).

## Commits

| Commit | What |
|---|---|
| `93b36220c7` | mvp-0.50: constant, upgrade, openers, CLI, the three switches classified, every defaults snapshot recomputed, version pins moved in 45 test files |
| `23b3b5d948` | Items 1, 2: the report and the trace say what the rollouts read; the combiner fitted on the traces' joined outcomes |
| `a574409cc1` | Item 3: the tail's sessions vectorized over every block's cells |
| `cc31c0ed4b` | Items 4, 5: carried valuations in the next prefetch; scope extensions |
| `8974d41869` | Item 8: `\cdots` has plain words (certification 6 -> 7) |
| (this record) | The join's per-protocol counts, the weeks test, the review file, the spec's as-built, the regenerated references |

Items 1 and 2 share `daily_plan/objective_inputs.py`; items 4 and 5 share `router_objective/tail_data.py` and
`daily_plan/objective_chooser.py`. With no interactive staging here each pair is one commit; each item has its own
tests, written against its interface first (`tests/test_rofu_*.py`).

## Item by item

### 1. RO4's R3: the rollouts on AD's posterior learning parameters

**Found built.** RO5 (§9.1 item 7, `fitted_models`, default true at mvp-0.48) already reads AD's subject-view posterior
moments of `γ` and the reading curve (`gbar:1`, `gbar:2`) through AD's read-only entry point
`adaptive_difficulty.readiness.decision_state_fields(learning_moments=True)`, each parameter falling back to its prior
where AD has none; the reading map is RO4's R6 path (`adaptive_difficulty.reading.section_learning_objects`), and
`tests/test_ro2_ad_raw_document_reads.py` already walks from `objective_inputs`, `objective_chooser` and `readiness`.
**Availability**: the posterior is AD's snapshot of the live database at the decision; a live read can't see a row
before it is written (RO1's ruling R2), so every attempt it holds was known by then. Reads at a past cutoff (item 2's
join, RO6's rebuilt features) go through `known_at`.

What was left, and built:

- At the tag the trace holds the numbers the rollouts drew from (`inputs_sources.learning`: `gamma`, `gbar`,
  `dose_scales`, the source and which AD parameters were read). Below it the trace is byte-identical (a test).
- `learnloop router objective-report` gains `memory_model`: per decision, whether the rollouts read AD's posterior or
  its priors, and the combiner's version, source and fit size; the words read "the rollouts read AD's posterior
  learning parameters on N of N decisions (its priors on 0)". The landing record's "the rollouts use priors" no
  longer describes any version from mvp-0.48 with `fitted_models` on.

Tests: `tests/test_rofu_learning.py` (item 1's four).

### 2. RO4's item 6: the combiner fed resolved cold outcomes

`router_objective/combiner_data.py` (`combiner_trace_join_v1`) and `objective_inputs._combiner_with_traces`, at the tag
with `combiner_trace_outcomes`:

- **The join**: each traced `plan_block` decision that served a block (its first plan presentation names it; a drawn
  stop serves none and joins nothing); every topic it froze sensors for **except the drawn option's own topics** (the
  block acted on those, so their outcome measures the action's effect, which `γ` and the effect slopes own, not the
  memory forecast the combiner calibrates); RO2's resolver (`history_resolve.resolve_curves`) **per protocol** (no
  exposure between the block and the outcome; RO2's label, so help is a failure and an ungraded answer is passed
  over); the row `(η, R at the realized lag, y)`, `R` from the frozen stability and days since the last review plus
  the days to the outcome, none for an unpractised topic.
- **One outcome once**: an answer that is the first qualifying outcome after several decisions joins the latest of
  them (the freshest sensors); an answer that is also a randomized check's stays the check's row.
- **As of the decision**: a trace written by then, its block served by then, an outcome known by then through the
  availability predicate (`known_at`: received time at RO1's tag), so a backdated import is out until it arrived.
- The fit is RO5's Laplace fit with its labelled prior on the union of the checks' rows and the joined rows; the
  trace's `versions.memory_model` names `fit_version` (`combiner_fit_v2:checks+trace_outcomes`), `n`, and the rows per
  source with the join's counts (groups, scored, not known by then, check answers, duplicates).
- Natural outcomes are selected, so these rows are conditional on observation: a forecast's calibration may use them
  (§8.4), `w` never does (§8.7); nothing here enters a comparison score.

Limit, recorded: RO2's resolver reads exposures by occurrence time, so at a past cutoff an exposure imported later
with an earlier occurrence could censor a row the decision would have kept (per protocol). It can only remove rows,
never add a later-known outcome.

Measured on the copy-shaped synthetic vault after two weeks (57 traced decisions, `tests/test_rofu_weeks.py`): the
combiner's fit takes **56 ms with the join, 7 ms without** (median of three). The join reloads RO2's resolver inputs
(AD's events) at every decision, so it grows with the log; in the model branch it runs inside the prefetch job, twice
(the LLM policy's card build and the numeric policy both build the inputs), and on the no-model branch on the
serving thread. Smallest finish if it shows on the owner's copies: cache the joined rows per database keyed by the
traces' count and the attempts' greatest rowid, and build the inputs once per job.

What it fed on that journey: 110 groups, **0 rows** (every per-protocol row `pending:no_qualifying_outcome`): the
fake grader writes no AD evidence, so RO2's resolver passes every later answer over as ungraded, and the checks took
the unseen items. The join's logic is tested with planted resolver rows; its first real rows will come from a vault
with AD-graded answers on unseen items of topics the drawn block did not touch. The trace's join record now counts
every per-protocol row by status and reason, so the owner's report shows why rows are few.

Tests: `tests/test_rofu_learning.py` (item 2's four: the join's topics, one outcome once and only when known, the fit
and its trace record at the tag with the switch's predecessor record exactly, no read below the tag).

### 3. Speed

**The memory model's per-review update, vectorized over topics.** RO5's profile put 6.0 of 17 s per decision in
`memory.review` (177k calls) on arxiv_v2. The calls come from the tail's sessions, one per block per session per
day of the horizon. A session ranks its topics once and takes its slots cyclically, so when its slots are fewer
than its topics no topic repeats; and `before_block` scores something only when a dated use falls inside the
session. In that case (`merged_sessions`; at the tag with `[router_objective] merged_sessions` since Codex review F2:
`docs/reviews/router-followups-codex-review.md`) the session is now one vectorized step over every block's cells,
each at its own block's end: the same cells, in the same order, through the same elementwise formulas. Otherwise
the per-block loop runs as before (the reference path). `Fsrs.review`/`retrievability` also drop `np.clip` (the same
values, `np.minimum(np.maximum(...))`, without its per-call overhead).

| Copy-shaped decision (arxiv_v2's 22 topics, 5 candidates incl. a probe, 8 draws) | Per-block loop | Merged |
|---|---|---|
| `value.evaluate`, median of 5 | 423 ms (435 ms at the base) | 232 ms |
| `memory.review` calls per evaluation | 6,483 | 2,197 |
| Largest difference of any `Q` draw | | 0.0 (bitwise equal here; the test holds 1e-12) |

Tests: `tests/test_rofu_speed.py` (equality to 1e-12 on the copy shape, with fewer topics than slots, and with dated
uses inside the horizon; the call count; the update against the scheduler's scalar FSRS).

**Not built: RO6's R5 transition-reward cache and RO5's closed-window score cache.** "Exact equality with the
uncached fit" needs every input a closed reward or score reads to be unchanged since it was cached, and they are not
immutable: a regrade or a hold changes a closed check's label as the grade stands now (RO5's ruling R1 names it as
intended), and the realized cost reads activity on occurrence time through the window's end (R10), so a late-arriving
row with an earlier occurrence moves it. A cache keyed by decision ids alone would serve stale values. Smallest way to
finish: key each cached reward or score by its decision ids **and** a fingerprint of what can move it (the count and
greatest rowid of `held_grades` and the grading epochs, wholesale; the count of activity rows with occurrence at or
before the latest closure); recompute all on a change. On the copies RO6 measured the refit at 20-22 ms at 36-75
decisions, so this is not yet where the time goes.

### 4. RO6's R12 and R3: carried valuations in the next prefetch (`carried_in_prefetch`)

- A decision's job no longer runs its own second valuation after the answer: every answer that can serve carries
  its own (`NumericPolicy.carried`, frozen to that answer's inputs: the final answer and, since Codex review F3, an
  early uncorrected publication), and the serve registers the one it took (process memory, per database, at most
  `CARRY_LIMIT` = 32, `keep`). The reading side asks the same switch (Codex review F1).
- The **next boundary's prefetch** runs every registered one after its own answer is out, at its own deadline. The
  no-model branch has no prefetch: its decision's valuation runs on a thread of its own started after the serve.
  Neither is the serving thread (tests block every evaluation at a carried cutoff: the chooser's wait returns, and
  none runs on the serving thread).
- A later decision's trace records each valued one (`carried_for`: the decision's id, its `previous` record with `q`
  and `features`): a separate, immutable record keyed by the decision, read as of the carrying trace's own time (the
  traces known at the reading moment). The earliest carrier stands; a record naming another earlier decision is
  ignored; a valuation that found no value is dropped. A record stays waiting until a trace holding it is known to be
  written (a choice computed and never logged writes nothing).
- `tail_data.logged` then gives the decision its carried values (`carried_source = "later_prefetch"`), so the
  transition into it is valued at `previous_cutoff`, the same backup as a decision valued in time (a test), instead
  of censored `cutoff_unmatched`. Its own record says where the value went (`previous.deferred_to`).

Choice recorded: the brief's "a separate, append-only record keyed by the decision's trace id" is the later trace's
`carried_for` section rather than a new table: a table would need migration 247, and renaming the head fixture
touches the 65 test files that name `migration_head_246`. The record is keyed by decision id (one trace per decision,
`decision_id` unique). Smallest alternative if the owner wants its own table: migration 247 with one RECEIPT table
(`decision_id`, `trace_id`, `previous_decision_id`, `record_json`, `received_at`), written by the draining job, and
`tail_data._with_late_carried` reading it instead.

Tests: `tests/test_rofu_carried.py`.

### 5. RO6's R11: a growing retention scope (`scope_extension`)

§3.3's undated uses run "from enrollment on": a topic the learner starts practising enters the retention scope at the
density every retention topic has, which is a change of **state** (the transition caused the enrollment), not of the
objective. At the tag the objective's definition (`ro6_objective_definition_v3_scope_extension`) keeps the goals, the
horizon and the goals' topics with their densities as before, and reads the retention topics (those in no goal's
scope) by their **set of densities** alone. A new retention topic at the scope's density leaves the hash, and so the
generator version, as it was; the earlier decision's value never depended on the topic (it never valued it, or valued
it at that density as a candidate). The backup across it is exactly the no-growth backup (a test). A retention density
that changes (Codex's 0.1 -> 0.9 reproduction stays censored `objective_changed`), a new topic at another density, a
goal, a weight, a date or the horizon still changes it. The serving side hashes the same way (the trace's residual
names the definition's version).

Limit, recorded: the very first retention topic (an empty retention scope becoming one) is still a change point,
since an empty scope has no density to compare with.

Tests: `tests/test_rofu_scope.py`.

### 6. RO6's R5: the mix's floor draws as randomized contrasts for `ŵ` — not built

The floor's draw is randomized with a logged probability (`μ = (1 − kε)·mix + ε`), but its contrast is not the coin's:
under the floor, stop has probability `1/k` and each block `1/k`, not `p` both ways, so `learned_tail.coin_contrast`'s
`±1/p` weight, the predicted contrast at the mix's shares and RO6's R1/R7/R10 bounds all need a second form
(`w = 1[stop]·k − 1[block]·k/(k−1)` conditional on the floor component, the blocks' predicted contrast at uniform
shares, intent-to-treat by the drawn component). Smallest way to finish: a `FloorDraw` beside `CoinDraw` in
`learned_tail` with its own weight and predicted contrast, `tail_data.contrasts` building both cohorts (a decision
whose coin forced an arm is the coin's only), `coin_contrasts`' bounds unchanged; a planted-slope recovery test and
Codex's R1 reproductions rerun with floor draws in the cohort. A switch `floor_contrasts`.

### 7. RO5's open items — recorded, not built

- **Availability as a covariate in κ0's likelihood**: logged with every observation; not fitted. Smallest finish: one
  more grid axis (a slope on the log ratio of minutes offered to `m̄`, prior `N(0, s²)`), labelled.
- **The goal-date read inside `V`**: reported only (RO5's choice 10). Smallest finish as recorded there.
- **linear_algebra's zero-price long sessions, found**: the seed falls to the tail's average, and that is 0 when
  `G(m̄) ≤ G(0)`. On a synthetic decision (8 practised topics, `m̄` 30, blocks of 10 minutes and 3 items, 64 draws)
  the **marginal gain at `m̄` is negative in every case** (−0.0002 to −0.0022 per minute, η from −0.5 to 1.5, `S`
  2 or 40) and the average is at most +0.0003, negative at η 0.5, `S` 40. The mechanism: the rollouts draw a review's
  outcome from AD's predictive (η) but apply it through FSRS, whose lapse branch resets a strong item's stability, and
  a session with more slots than topics re-practises the same topic minutes later, where a success adds almost
  nothing (`R ≈ 1`) and a failure costs most of `S`. So more practice today lowers the forecast and the seed has no
  positive value to keep. This is a model defect, not the design: §8.6's floor keeps the last positive value, and
  there has never been one. A labelled prior on `κ0` from the goal contract's minutes is not what §8.6 says (it seeds
  from the forecast gain), so it is not the fix. Smallest fix, a serving change for the owner's ruling: draw a
  practised topic's review outcome from the memory model's own `P(perform)` at that moment (the combiner over `η` and
  `R`), so a review FSRS calls a lapse is one the model expects, behind its own switch; then rerun the probe and the
  smoke's linear_algebra day. **Built at landing (ruling R1, `[router_objective] consistent_review_draw`)**: the probe
  before and after, and what still makes the marginal negative, are in `docs/reviews/router-followups-codex-review.md`
  ("Landing ruling R1").
- **The closed-window score cache**: see item 3.

### 8. Small items

- **`\cdots` plain words**: built. KaTeX writes it `\@cdots` (family `inner`), now beside `\ldots` in
  `book_math._PLAIN_ATOMS`; `source_check.CERTIFICATION_VERSION` 6 -> 7, so a label stored under 6 is read again by
  code at no paid cost. Test `tests/test_rw5c_plain_words.py::test_cdots_has_plain_words_as_ldots_does`.
- **FG1d's `get_feedback` whole-handler pin and the one-fold probe interpretation**: not built. Both reorder writes in
  the feedback and probe-episode paths (the open and reveal debits; the probe's grade interpretation before the
  attempt's first projection), outside the router objective; smallest finish as FG1d's record says, with its own
  byte-identity check.
- **RO1's R3 (admission's review load from `last_attempt_at` with no intent view)**: not built. It changes admission,
  so it needs its own successor entry in the playbook and a switch (RO1's ruling); smallest finish: read the review
  anchor RO1's recall targets use (FSRS-eligible, not held) in `daily_plan/admission.py`'s fallback.
- **Stamp-only mastery rows after an upgrade**: not built. The playbook (step 6) ignores "only explicitly documented
  surrogate IDs and write timestamps", and an `algorithm_version` stamp is neither, so the shadow is right to show
  them; the smaller fix is the upgrade's: restamp the projection's untouched rows in the activation transaction
  (an UPDATE of `algorithm_version` alone on the derived mastery rows), with a rebuild-equivalence test.
- **RO2's probability-copy serve latency**: not investigated (it needs the owner's copy; this batch opened none).

## A few simulated weeks (copy-shaped synthetic vault), before and after

`tests/test_rofu_weeks.py`: RO6's few-weeks journey (six practised topics, four unseen items each, the default arms,
day 4 and 11 without a session, a seeded ~70% learner, both policies answering through fakes), 15 days at mvp-0.49
and at mvp-0.50. The fake runtime runs each prefetch job inline (the serve waits for it), so neither side censors
`cutoff_unmatched` here; the timing case is `tests/test_rofu_carried.py`'s, with every carried evaluation blocked.

| | mvp-0.49 | mvp-0.50 |
|---|---|---|
| Traced block decisions | 51 | 87 (57 in a second run: the journey's decision ids are fresh ULIDs, so the seeds differ run to run) |
| Transitions / censored | 50 / `no_later_decision` 1 | 86 / `no_later_decision` 1 |
| Generator versions | 1 | 1 (the synthetic population does not grow; item 5's case is `tests/test_rofu_scope.py`'s) |
| `carried_for` records written | 0 | 85 |
| Numeric policy per decision, median / max (ms) | 1097 / 1642 | 1174 / 1711 (1087 / 1562 in the second run) |
| Combiner | 12 checks, `laplace_fit on resolved randomized checks` | 12 checks + 0 joined rows (see item 2) |
| The rollouts' learning parameters | AD's posterior (RO5) | AD's posterior, numbers in the trace |

The numeric policy's time here is mostly the AD reads and the inline jobs, not the rollouts (6 topics); the
rollouts' saving is item 3's table. Under blocked carried evaluations (`tests/test_rofu_carried.py`): at mvp-0.49 the
no-model branch censors every transition `cutoff_unmatched` (R3's test); at mvp-0.50 the valuations run off the
serving thread, the serve's wait returns, and the fits read `previous_cutoff` transitions from later traces' records.

## The gate (this step)

The full suite, the whole durability lane and the whole vitest run are the landing gate's. No frontend or `src-tauri`
file changed, so no npm, vitest or cargo step applies. No schema change and no DB or connection code changed, so no
durability-marked test applies and the DB reference was regenerated only for the configuration leaves (1170 to 1173)
and validated.

| Step | What ran | Result |
|---|---|---|
| Setup | `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | ok |
| Import contracts | `uv run lint-imports --no-cache` (under `env -i`) | 43 kept, 0 broken |
| Version pins | the 69 test files naming mvp-0.49, the chain's tail, the latest version or RO6's opener, with `test_config_refactor` and the CLI help snapshot, `-n 6` | 120 failed (pins and snapshots) before the fixes, in 42 files |
| RO regression, contract and pin set | every `tests/test_rofu_*.py` (but the weeks), `test_ro4_*`, `test_ro5_*`, `test_ro6_*`, `test_ro1_availability_reads`, `test_ro2_ad_raw_document_reads`, `test_registry_audit`, `test_architecture` (frozen cycles, the SQL-owner rule), `test_table_roles`, `test_config_refactor`, `test_cli_help_snapshot`, `test_ro0_gate`, `test_data_capture_successor` and the 42 pin files, `-n 6` | 1114 passed, 9 skipped, 3 xfailed, 5 failed (four sets ending in `LATEST_ALGORITHM_VERSION`, the CLI help snapshot); fixed, those five with the six `test_rw5c_*` files rerun: 415 passed, 7 skipped, 1 xfailed |
| Contract and audit set | the display-label audit (`test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`, `test_rw5c_labels`), the process-launch allowlist (`test_codex_lockdown_round3`, `test_ai_tool_isolation`, `test_e0_isolation`, `test_codex_tool_lockdown`), `test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`, `test_sidecar_registry`, `test_mobile_allowlist`, `test_coordinated_migrations`, `test_tracked_fixture_databases`, `test_module_catalog_inventory`, `test_public_tip_guards`, `test_sqlite_file_copies`, `test_ro1_availability`, `test_ro1_interval_factor`, `test_ro1_projection`, `test_ro1_self_report`, `test_ro0_rows9_13_decision_state`, every `test_rofu_*` but the weeks, `test_config_refactor`, `test_registry_audit`, `test_architecture`, `test_cli_help_snapshot`, `-n 6` | 949 passed, 1 skipped, 1 failed: the module catalog's two new notes not yet tracked (committed with this record; rerun below) |
| The weeks | `tests/test_rofu_weeks.py`, serial with `-s` | 2 passed (and its mvp-0.50 case with `test_rofu_learning.py` after the join's counts: 9 passed) |
| References | `db_generate_reference.py` / `db_validate_reference.py` (head 246, 1173 leaves: errors []), `module_generate.py` / `module_validate.py` (PASS), `validate_vault.py` (passed) | ok |

Every test ran inside `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, at most `-n 6`, one run at a
time. Every script outside pytest (the fingerprints, the CLI help snapshot's `--write`, lint-imports, the reference
scripts, the benchmarks and the κ0 probe) ran under `env -i` with empty `HOME`, `CODEX_HOME` and
`LEARNLOOP_CONFIG_DIR`. Old item difficulty scalar (owner, Nov 5): `git diff e7a7d7734f -- src migrations` adds no
reader or writer of the difficulty columns, `mastery.irt.difficulty_from_prior` or surprise's `b`.

## Files the batch added or changed tests in (for the landing gate)

Added: `tests/test_rofu_successor.py`, `test_rofu_learning.py`, `test_rofu_speed.py`, `test_rofu_carried.py`,
`test_rofu_scope.py`, `test_rofu_weeks.py`. Changed: `test_rw5c_plain_words.py`, `test_rw5c_katex_tree.py`,
`test_rw5c_block_policy.py` (item 8); `cli_help_snapshot.json`; pins moved in `test_curriculum_c1_landing.py`,
`test_curriculum_c1_plan_follows_path.py`, `test_data_capture_successor.py`, `test_field_workbench_signals.py`,
`test_followup_successor.py`, `test_help_fold_attach_successor.py`, `test_intent_codex_rereview.py`,
`test_learner_report_superseded.py`, `test_lp_claim_fixes.py`, `test_method_explicit_upgrade.py`,
`test_mvp011_upgrade.py`, `test_mvp013_upgrade.py` to `test_mvp018_upgrade.py`, `test_mvp020_upgrade.py` to
`test_mvp024_upgrade.py`, `test_plan_follows_path.py`, `test_pr4_superseded_claims_landing.py`,
`test_reader_ca2_one_ask.py`, `test_reader_followups_successor.py`, `test_reading_step_switch.py`,
`test_rebuild_equivalence_review.py`, `test_recurrence_commands.py`, `test_regrade_contract_successor.py`,
`test_required_method_grading.py`, `test_ro1_successor.py`, `test_ro4_successor.py`, `test_ro5_successor.py`,
`test_ro6_successor.py`, `test_route_rules_in_grader.py`, `test_serve_eligibility_review.py`,
`test_teacher_te1_successor.py`, `test_teacher_te1b_suggestions.py`.

## Open questions (for the orchestrator)

1. Item 7's finding: the rollouts' review outcome is drawn from AD's predictive while its effect goes through FSRS's
   lapse branch, which makes more practice today lower the forecast (negative marginal gain at `m̄` on every synthetic
   case), so κ0's seed has no positive value to keep. The smallest fix (draw a practised topic's outcome from the
   memory model's own `P(perform)`) changes every valuation: build it next with its own switch, or rule otherwise.
2. Item 4's record is a section of a later trace rather than its own table (no migration, no 65-file fixture rename);
   accept, or ask for migration 247's RECEIPT table.
3. Items 6 and 7 (the floor contrasts; κ0's availability covariate, the goal-date read in `V`) and RO6's/RO5's caches
   are recorded with the smallest way to finish each; which go next.
4. Item 2's join found no row on the synthetic journey (no AD-graded answers there); its first real numbers come
   from `objective-report`'s `memory_model` after the owner upgrades.

## Landing onto main

What was built for each ruling is in `docs/reviews/router-followups-codex-review.md`, under the sections for R1, R6,
R7, R8, R9 and "Scoped verify and landing rulings R10-R12". The commits:

| Ruling | Commits |
|---|---|
| R1 | `3d018ebf50` |
| R6 | `58b727566e`, with its switch in `0ad1ebe661` |
| R7 | `f7a21cf602` (a record only) |
| R8 | `0767b917bd` |
| R9 | `8a19c2698b` |
| R10 | `f1129754c8` |
| R11 | `0c448efaa7`, `a63fc11ba0` |
| R12 | `f707b88555` |

Main was merged twice: `c2e810f940` in `2db795f6d7`, and `5565bede25` (TE2-log, migration 247) in `1fd90d95da`. In
the second merge every defaults snapshot was recomputed, and the successor test's frozen mvp-0.49 digest moved to
main's own (`8031015473`).

### Orchestrator rulings (verbatim)

- R1: "Item 7's finding is a model defect and is fixed in this batch: a practised topic's review outcome in the rollouts is drawn from the memory model's own P(perform) at that moment (the combiner over AD's predictive and FSRS's R, as §8.4 defines it), so a review FSRS calls a lapse is one the model expects. Behind its own switch [router_objective] consistent_review_draw (default true, classified as a structural kill switch), at the mvp-0.50 tag only; below the tag and with the switch off the rollouts are mvp-0.49's draw for draw. Reproduce first: the synthetic probe from the record (8 practised topics, m-bar 30, blocks of 10 minutes and 3 items, 64 draws, eta from -0.5 to 1.5, S 2 or 40) shows the negative marginal gain at m-bar on the pre-fix source; after the fix, report the marginal gain per case and whether kappa0's seed gets a positive value to keep. No sign is asserted as a law; the test pins the probe's numbers and the switch-off identity."
- R2: "Item 4's carried-valuation record as a section of a later trace (carried_for, append-only, keyed by the decision's trace id, read as of its own received time) instead of its own RECEIPT table is accepted. Pending carried work held in process memory is lost on restart, and that transition stays censored as in mvp-0.49: accepted and recorded."
- R3: "Not built here and queued for the next follow-up batch, each as recorded with its smallest finish: item 6 (floor draws as contrasts), kappa0's availability covariate and the goal-date read inside V, the RO6 transition-reward and RO5 closed-score caches with data fingerprints, FG1d's get_feedback pin and one-fold probe, RO1 R3's admission anchor (its own playbook entry), the upgrade restamping mastery rows, RO2's probability-copy latency (measured on the smoke's copies here)."
- R4: "Item 2's join cost (about 50 ms per decision at 57 traces, growing with the log, twice per model-branch prefetch) is measured on the copies at the smoke against the log's length, before any cache."
- R5: "Owner, Nov 5: the old item difficulty scalar is to be retired in the refactor. This batch adds no new reader or writer of it; the landing checks this with a grep of the diff against main for the difficulty columns, mastery.irt.difficulty_from_prior and surprise's b, and records the result."
- On R1's decisions: "Your decisions 1 and 2 are accepted (the belief observes under the same combiner likelihood; unpractised topics and probes stay on sigma(eta))."
- R6: "The memory model's combiner is monotone in ability by construction: P(perform) cannot fall as eta rises. The slope on eta (aA - aR in memory.perform's form) gets a positive-support labelled prior (log-normal, moment-matched to the current N(0.5, 0.5^2) mean and spread), so no coefficient draw has a negative slope; the combiner's fit (fit_combiner, including RO-followups item 2's trace-fed fit) uses the same parametrization. This is structural, not a tuned constant: higher ability never lowers predicted performance. Behind the mvp-0.50 tag only; below it mvp-0.49's draws are unchanged. Test: no draw of the prior or a fitted posterior has a negative slope; the probe's per-case marginals before and after at 64 and 512 draws are pinned (no sign asserted)."
- R7: "The rollouts apply practice's learning increment exactly as AD's own learning model does. Check AD's model (adaptive_difficulty: how gamma moves eta per practice and whether it saturates) against value._Model: if the rollouts' growth differs from AD's form (for example, AD saturates or is bounded and the rollouts are linear without a ceiling), align the rollouts to AD's form at the tag, reproduce-first. If AD's own form is unbounded too, do NOT invent a ceiling here: record it in the review file as an AD-level finding, with the probe's eta trajectory (it reached about 41 on the logit scale over 180 days), for the owner and the next AD stage."
- R8: "Every serving switch that changes the logger's values is part of RO6's generator payload, so flipping it is a change point and never changes Q under the same generator version: merged_sessions, consistent_review_draw, combiner_trace_outcomes and scope_extension (and any other switch of this batch that changes a decision's V or mu). carried_in_prefetch changes only which transitions are valued, not the logger, so it stays out; say if you find another that belongs. A test flips each and sees a new generator version; with every switch at its default the payload at mvp-0.50 is stable across decisions."
- On R6, answer 1: "Yes, add the kill switch: [router_objective] monotone_combiner (default true, structural kill switch, at the tag only), with the defaults snapshots recomputed, and include it in RO6's generator payload per R8. Step 4's every-switch-off identity then covers six switches."
- On R6, answer 2: "Keep the moment-matched variance 0.5 (my ruling misquoted the prior; moment-matching to the actual marginals is what it meant). Record the correction." Correction: R6's quoted "N(0.5, 0.5^2)" is my own misstatement of the linear prior. The prior on aA − aR is N(0.5, 0.5), variance 0.5 and sd 0.71, and the monotone prior is moment-matched to that.
- R9: "Where the rollouts read AD's predicted success (unpractised topics, probes, and the eta input to the combiner's prediction where AD's own predictive is meant), they use AD's own F(eta) with its lapse term, not sigma(eta), at the tag behind monotone_combiner's tag gate (or its own switch if you judge they should be separable; say which). The belief-variance drift and coupled-facet transfer stay recorded as AD-level findings, not built here." Built behind its own switch, `[router_objective] ad_predictive_link`. It is separable from `monotone_combiner`: one is the link to AD's predictive, the other the combiner's coefficient sign. With its own switch, step 4's identity covers seven switches.
- R10 (Codex N1): "The rollouts start from AD's actual latent posterior moments (mean and variance of eta as AD holds them, read through AD's read-only entry point with availability), not a point inverse of the variance-integrated p-bar with the variance added again. Where only p-bar and a variance exist, invert the variance-integrated predictive. Codex's two reproductions (latent mean 2 and -2, variance 4) must give an initial rollout predictive equal to AD's p-bar to quadrature precision; zero variance stays equal."
- R11 (Codex N2): "Unpractised Bernoulli draws and probe observations use F directly; the combiner gets a numerically stable probability-logit of its own, with a derivative that matches the transformation actually applied; FSRS's retrievability clipping stays FSRS's. Codex's eta -14, u 5e-5 case must give the same outcome on the graded, observe and performance paths, all at F(-14)."
- R12 (Codex N3): "The tag-gated switch snapshot is part of the prefetch boundary key, and each numeric answer freezes the switch settings it was computed under; the trace records those, never the current config's. Codex's reproduction is a test: flipping each of the six generator switches between prefetch and serve starts a new job, and a served cached answer's trace names the generator that produced it."
- After R10-R12: "rerun the probe at 64 and 512 draws, then CONTINUE with steps 1-6 without stopping. No further Codex round; I'll read the R10-R12 diffs before landing, so keep each in its own commit. In step 4's smoke, report the numeric policy's time per decision and Next at a boundary against mvp-0.49 per copy, so the cost of R9's quadrature is measured (if Next regresses noticeably, say by how much; don't optimize in this landing)."
- On main moving to 5565bede25: "merge main before step 5's record and step 6's checks (and rerun the targeted set after the merge ...)". The full gate below ran on the merged tree, so it covers the targeted set and `test_tracked_fixture_databases`, `test_coordinated_migrations` and `test_migrations`.

### Step 1: early checks (on the merged tree)

- **Command:** `-n 6` over 69 files: every `test_ro[0-9]*` and `test_rofu_*`, plus `test_measurement_state_labels`,
  `test_cli_help_snapshot`, `test_codex_lockdown_round3` (the process-launch allowlist), `test_ro1_availability_reads`,
  `test_tracked_fixture_databases`, `test_coordinated_migrations` and `test_migrations`.
- **Result:** 788 passed, 2 failed.
  - `test_rofu_successor`'s frozen mvp-0.49 digest, which the merge moved. It is fixed test-only in `8031015473`.
  - `test_rofu_carried.py::test_an_early_publication_served_keeps_its_carried_valuation`, the timing-sensitive test
    (see the review file). Alone it passed 2 of 3; it passed in the full suite.
- **Import contracts:** `lint-imports --no-cache` kept 43 contracts, 0 broken.
- **Also intermittent, before the merge:** `test_ro5_landing.py::test_r8_each_arm_can_be_drawn_with_its_logged_probability_and_no_intervention_serves_no_probe`
  failed in the targeted set after R10-R12, and 4 of 22 times alone in the worktree.
  - It failed 0 of 12 on a full archive of the same commit, and 0 of 24 on `5919b5a08c` and `591fd37f13`.
  - It runs below the batch's tag (mvp-0.48), where the batch changes nothing. Its first boundary's decision seed is
    unpinned, the class RO6's R8 and R14 pinned elsewhere.
  - It passed in the full suite. A seed pin (test-only) is left for a ruling.

### Step 2: references (`de22e2e670`)

- `db_generate_reference` (395 table notes) and `db_validate_reference` (errors []). The prose counts in
  `Database.md` and `Configuration.md` were updated to 1178 effective leaves.
- `desktop_generate` and `desktop_validate`: 320/320 TS/TSX and 6/6 Rust modules.
- `module_generate` (1239 module notes, 67 package maps) and `module_validate` (PASS).
- `validate_vault.py`: passed, 2229 notes.
- The defaults snapshots match the composed defaults: 41 of 41.

### Step 3: the gate (at `8031015473`, the merged tree)

| Lane | Result |
|---|---|
| Setup | `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0`: ok |
| Import contracts | 43 kept, 0 broken |
| Full suite (`-n 8`, 10G scope, under the shared lock) | 26845 passed, 91 skipped, 47 xfailed, 0 failed, in 67.0 min |
| Durability lane (`-m durability`) | 403 passed, 1 skipped |
| Owner lane (fresh backup-API copies of `owner-copies-mvp035` in `fixtures-local/landing-rofu/`, since deleted) | 83 passed, 4 skipped, and the 2 known failures: `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events` and `test_placement_fixture_copies[arxiv_v2]` |
| Desktop | typecheck ok; whole vitest at `--maxWorkers=4`: 2763 passed; `frontend:build` ok (`npm ci --offline` from the user's npm cache) |
| Rust | `cargo check`: ok |
| Mobile | typecheck ok, build ok (no phone file changed) |

### Step 4: the smoke

**Setup.**
- **Copies.** Fresh backup-API copies of `~/learnloop-backups/mvp043-20261103-copy` (arxiv_v2, linear_algebra,
  probability), neutralized, under `fixtures-local/landing-rofu-smoke/` (since deleted).
- **Upgrades.** On main code (`c2e810f940`): mvp-0.45, rebuild, mvp-0.46, mvp-0.47, rebuild, then the default to
  mvp-0.49. Then on branch code, the default upgrade to mvp-0.50. Head 246 throughout.
- **Code.** The branch code was `fdcc287c1e`, before the second merge. That merge is teacher-only (TE2-log); the
  gate above covers the merged tree. Main and branch were each `git archive`d with `migrations/`.
- **Models.** Every AI route was pointed at 127.0.0.1:9. The router LLM and the Decider were in-process fakes;
  grading and diagnosis were the tests' `BlindRivalClient`; probe authoring was `AuthorFake`.
- **Driver.** RO6's driver, adapted. It runs through the real sidecar handlers and threads.

**Identity.** The seed is pinned to the decision id on both sides, and ids and wall times are set aside. Each pair
compares Today, the plan, every step, every written row (traces included, with their JSON read), every router LLM
and Decider request, and the generated follow-up's gate.

| Copy | Below the tag: main vs branch at mvp-0.49 | At the tag, all seven switches off, vs main at mvp-0.49 | Both with `[router_objective] enabled = false` |
|---|---|---|---|
| arxiv_v2 | identical (5 LLM, 5 Decider requests, 1 gate, 5 traces) | identical (6, 6, 1 gate, 5 traces) | identical (7, 7, 1 gate) |
| linear_algebra | identical (5, 5, 1 gate, 5 traces) | identical (5, 5, 1 gate, 5 traces) | identical (8, 8, 1 gate) |
| probability | identical (5, 5, 1 gate, 5 traces) | identical in two reruns (5, 5, 1 gate, 5 traces); see below | identical (4, 4, 1 gate) |

- **Set aside for the at-the-tag pair only:**
  - the boundary key's version string, and at mvp-0.50 its switch snapshot (R12), on both sides, because they seed
    the rollouts' noise, as RO5's and RO6's landings did;
  - the trace's generator key, which names the version;
  - `versions.serving_switches` (all false);
  - item 1's `inputs_sources.learning` (trace metadata with no switch).

  Below the tag, only latencies (`fit_ms`) were set aside.
- **probability's first at-the-tag run** differed in one trace's values only: 16 completed draws against 8, with the
  same choices and rows. That is the deadline-bound refinement under load (Steam's shader compiles held the CPU),
  the F2 phenomenon. Two reruns gave 8 draws on both sides and were identical.

**Two simulated weeks per copy at the tag, every switch on** (RO6's journey):
- RO5's arms were on.
- A seeded ~70% learner answered the copy's real items.
- Offered stops were kept going or accepted at random.
- Days 3 and 10 had no session.
- Next ran either right after feedback (dwell 0) or after a 3 s dwell.

linear_algebra first (dwell 0, per day as of the day's end):

| Day | Decisions | Longest session minutes (plan 30) | κ0 (source) | Transitions (censored) | Carried valuations recovered | Combiner fit n (joined rows) | Numeric ms median (max) |
|---|---:|---:|---|---|---|---|---|
| 11-05 | 1 | 1.5 | 0.007269 (day seed) | 0 (`no_later_decision` 1) | 0/1 | 1 (0) | 722 |
| 11-06 | 9 | 31.5 | 0.001746 (day seed, carried) | 7 (`cutoff_unmatched` 2, 1) | 7/10 | 3 (1) | 1408 (1934) |
| 11-07 | 7 | 33.0 | 0.003355 (posterior from stop offers) | 15 (1, 1) | 15/17 | 4 (1) | 1873 (2127) |
| 11-09 | 5 | 10.5 | 0.004139 (posterior) | 19 (2, 1) | 19/22 | 6 (2) | 1715 (2174) |
| 11-10 | 8 | 25.5 | 0.004127 (posterior) | 28 (1, 1) | 28/30 | 8 (3) | 1571 (2213) |
| 11-11 | 3 | 13.5 | 0.004127 | 30 (2, 1) | 30/33 | 10 (4) | 1982 (2708) |
| 11-12 | 3 | 12.0 | 0.004127 | 33 (2, 1) | 33/36 | 13 (6) | 2036 (2495) |
| 11-13 | 8 | 31.5 | 0.005308 (posterior) | 41 (2, 1) | 41/44 | 14 (6) | 1925 (2723) |
| 11-14 | 12 | 55.5 | 0.005797 (posterior) | 53 (2, 1) | 53/56 | 14 (6) | 1955 (3371) |
| 11-16 | 2 | 0.0 | 0.005797 | 55 (2, 1) | 55/58 | 14 (6) | 3377 (4051) |
| 11-17 | 3 | 13.5 | 0.008008 (posterior) | 58 (2, 1) | 58/61 | 15 (7) | 1871 (3163) |
| 11-18 | 4 | 15.0 | 0.008008 | 62 (2, 1) | 62/65 | 15 (7) | 1847 (2459) |

What the linear_algebra weeks show:
- κ0 had a positive value every day. It started from the day's seed and was handed to RO5's posterior once a
  randomized stop offer had a response (day 3).
- Sessions stayed near the plan's 30 minutes, with one 55.5-minute day. RO6's landing recorded zero-price long
  sessions here.

All copies at the weeks' end:

| Copy, dwell | Traced decisions | Transitions | Censored | Generator versions | Carried recovered | Combiner n (joined rows) | Numeric ms median (max) | Combiner join ms, first third / last third of the log (calls) |
|---|---:|---:|---|---:|---|---|---|---|
| linear_algebra, 0 s | 65 | 62 | `cutoff_unmatched` 2, `no_later_decision` 1 | 1 | 62/65 | 15 (7) | 1868 (4051) | 646 / 913 (157) |
| linear_algebra, 3 s | 65 | 63 | 1, 1 | 1 | 63/65 | 15 (7) | 1877 (4863) | 426 / 551 (157) |
| arxiv_v2, 0 s | 33 | 31 | 1, 1 | 1 | 31/33 | 15 (15) | 999 (3723) | 129 / 159 (77) |
| arxiv_v2, 3 s | 33 | 31 | 1, 1 | 1 | 31/33 | 15 (15) | 852 (4541) | 98 / 96 (77) |
| probability, 0 s | 59 | 56 | 2, 1 | 1 | 56/59 | 16 (11) | 1196 (3247) | 617 / 1417 (149) |
| probability, 3 s | 59 | 57 | 1, 1 | 1 | 57/59 | 16 (11) | 1099 (2323) | 736 / 503 (149) |

- **Censoring.** `cutoff_unmatched` is now rare at both dwells: 1-2 per copy. At RO6's landing it was 11 of 36, 68
  of 75 and 35 of 68.
- **Carried valuations.** Almost every one was recovered from the next prefetch and recorded in a later trace's
  `carried_for`.
- **Generator versions.** One per copy in two weeks. arxiv_v2 had 22 at RO6's landing; item 5's scope extension
  removes that churn, and no `objective_changed` remains.
- **`ŵ`.** 0 bound and 0 unbounded every day. No evaluation window closed within the two weeks, so no randomized
  contrast formed (as at RO6's landing).
- **R4, the join's cost.** It grows with the log, and it runs inside the prefetch job about 2.4 times per decision:
  - per call, 0.4-0.9 s on linear_algebra and up to 1.4 s on probability at the end of the log;
  - the dwell-0 runs overlapped the full suite, the dwell-3 runs a quieter machine.

  The trace-fed combiner now has real joined rows: 7, 15 and 11, against 0 in the batch's synthetic journey.
- **Trace terms.** Recomputed for every decision: 318 / 118 / 255 candidate `V_residual` and `Ṽ`, plus the
  calibration summary as of each trace (65 / 33 / 59). Problems: 0.
- **Assignments.** RO5's analysis recomputed each logged probability (coins 60 / 26 / 53, checks over 12 days).
  Problems: 0. Every generated probe was served at most once, and every follow-up workflow settled.
- **Trace bytes per decision.** 22-24 KB, 13-31 KB and 12-24 KB.

**Protection on the cards.** 168 / 84 / 164 router LLM cards and every Decider state were scanned.
- No protected or invisible stem, and no attempt cited after its decision. linear_algebra's 15 protected items were
  never shown.
- Every reference-solution hit (1431 / 37 / 872) sits in the learner's own answer, either under an `answer` or
  `answer_excerpt` key or right after an `answer:` label. That is the synthetic learner typing the expected answer.
- probability's 17 unattempted-stem hits are RO6's known false positive: `pi_method_reusable_access_code` shares its
  first 60 characters with an attempted sibling.

**Time.** One day with a generated follow-up; main at mvp-0.49 against branch at mvp-0.50.

| Copy | Next after | Numeric per decision ms (main / branch, median) | Next at a boundary ms (main / branch) | Follow-up gate ms (main / branch) | Today ms | Submit ms |
|---|---|---|---|---|---|---|
| arxiv_v2 | 0 s | 1248 / 2315 | 2005 / 2103 | 191 / 210 | 163 / 175 | 202 / 264 |
| arxiv_v2 | 3 s | 1207 / 2301 | 594 / 523 | 208 / 206 | 165 / 177 | 219 / 217 |
| linear_algebra | 0 s | 743 / 1207 | **2003 / 3260** | **302 / 1120** | 870 / 884 | 230 / 242 |
| linear_algebra | 3 s | 740 / 1242 | 798 / 776 | **217 / 1126** | 888 / 841 | 246 / 241 |
| probability | 0 s | 224 / 490 | 1052 / 952 | 189 / 189 | 701 / 695 | 206 / 228 |
| probability | 3 s | 182 / 619 | 875 / 858 | 189 / 196 | 744 / 731 | 253 / 237 |

- **The numeric policy is 1.6 to 3.4 times slower.** This is in the prefetch job.
- **Next at a boundary regresses noticeably on linear_algebra with Next right after feedback:** +1.26 s (+63%,
  2.0 to 3.3 s). With a 3 s dwell, and on arxiv_v2 and probability, it is unchanged.
- **linear_algebra's follow-up gate is about 0.8 s slower.**
- **Profiles on arxiv_v2 and linear_algebra** (`SMOKE_PROFILE`, one day):
  - R9's link inside the practice draws (`_graded_linked`, the quadrature's `logit_and_slope` twice per call) is
    about half of every evaluation: 4.8 of 9.2 s on arxiv_v2, 4.1 of 9.7 s on linear_algebra.
  - Item 2's join (`resolve_curves`) is 3.7 of 16.3 s on linear_algebra.
- **RO2's probability-copy serve latency (R3):** Next at a boundary is 952-1052 ms and Today is 695-744 ms on both
  codes. No regression.

Not optimized here, as ruled. The smallest finishes:
- compute `logit_and_slope` once for `η` and once for the belief per batch rather than per call;
- the join cache keyed by the traces' count and the attempts' greatest rowid, built once per job (recorded under
  item 2).

**Reports, rebuild, sync.**
- **`learnloop router objective-report`** was run as of the weeks' end, with RO6's `report_at.py` (the frozen clock
  is in the real one's future).
  - `memory_model`: "the rollouts read AD's posterior learning parameters on 65 of 65 decisions (its priors on 0);
    the combiner fsrs_ad_logistic_v1 is laplace_fit on resolved randomized checks and the traces' sensors joined to
    resolved cold outcomes, fitted on 15 outcomes". The same on 33 of 33 for arxiv_v2 (15 outcomes) and 59 of 59 for
    probability (16 outcomes).
  - `learned_tail`: "w^ 0.0000 (slope +0.0000 sd 1.0000, rank None, P(rank > 0) 0.500, 0 randomized contrasts, 0
    forced ...); transitions 62 of 65 decisions; censored {'cutoff_unmatched': 2, 'no_later_decision': 1}; change
    points 0; version ad66c63f1f7e1bdf (mvp-0.50, 65 decisions ...): fit n 62, fqe_fixed_point_with_prior". For
    arxiv_v2: 31 of 33, fit n 31. For probability: 56 of 59, fit n 56.
- **`rebuild --shadow`** on each copy: facet 0, schedule 0. Mastery differs only in the known stamp-only
  `algorithm_version` rows (4 / 14 / 7).
- **Survival.** Assignments and traces survive `rebuild-derived-state` and a state sync on each copy (byte-equal
  before and after).

**R5's grep.** `git diff 5565bede25 -- src migrations` adds no reader or writer of the difficulty columns,
`mastery.irt.difficulty_from_prior` or surprise's `b`. Its added lines that name "difficulty" are imports and
docstrings of the `adaptive_difficulty` package (R9's and R10's reads). The rollouts' `Topic.difficulty` is FSRS's
D, which was already there.

**Model calls and processes.**
- No model receipt came from a real model. Real-model receipts stay at each copy's own pre-existing count (probability
  42, the others 0), and every new receipt is a fake's.
- The net watch saw no non-loopback connect and no resolve.
- The only subprocesses were `git` and `powerprofilesctl`. No Codex process ran.

### For the owner

- **Upgrade.** Each vault goes from mvp-0.49 to mvp-0.50 with `learnloop upgrade --vault ~/learnloop-vaults/<name>`
  (the default target). Then restart the phone host and rebuild the desktop app.
  - Nothing recorded changes; this is a projection activation.
  - The vaults still at mvp-0.43 go through RO5's and RO6's steps first: `learnloop upgrade --to mvp-0.45`, then
    `learnloop rebuild-derived-state`, `--to mvp-0.46`, `--to mvp-0.47`, `rebuild-derived-state` again, then the
    default upgrade.
  - Opening a vault applies TE2-log's migration 247.
- **Switches.** Each one is a kill switch under `[router_objective]` in the vault's `learnloop.toml` and defaults to
  true; setting it to `false` serves that part as mvp-0.49 did:
  - `combiner_trace_outcomes`
  - `merged_sessions`
  - `consistent_review_draw`
  - `monotone_combiner`
  - `ad_predictive_link`
  - `carried_in_prefetch`
  - `scope_extension`

  `enabled = false` turns the whole objective off. Under R8 every switch but `carried_in_prefetch` is a change point
  for the learned tail's fit.
- **Paid routes.** None added. No model request, no paid call.

### Open items

- **Speed.** R9's quadrature and item 2's join, as measured above. linear_algebra's Next at a boundary is +1.26 s
  with Next right after feedback, and its follow-up gate is +0.8 s.
- **R7's AD-level findings.** AD's learning increment is unbounded, the belief's variance does not drift, and
  coupled-facet transfer is not simulated.
- **Intermittent tests.** `test_ro5_landing`'s r8 test (an unpinned seed below the tag) and
  `test_rofu_carried`'s early-publication test (a 3 s serve wait against a 2.2 s first publication).
- **R3's queue, unchanged:**
  - item 6's floor contrasts;
  - κ0's availability covariate and the goal-date read in `V`;
  - the RO6 and RO5 caches;
  - FG1d's `get_feedback` pin and one-fold probe;
  - RO1 R3's admission anchor;
  - the upgrade's mastery restamping.
