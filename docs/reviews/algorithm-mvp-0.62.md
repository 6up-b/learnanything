# mvp-0.62: the committed-check credit (TV2-1, steps 6 and 7; with TV2-2 and TV2-3)

Branch `algo/check-credit-activate`, from main `5b510c8f51`. The owner sees what it changes on their own vaults before
it lands (the last sections: what the orchestrator runs on copies). Everything below was measured on synthetic inputs
and vaults. No migration, no kill switch, no config key, no prompt change: the tag is the switch. The design is the
orchestrator's build sheet (sections 2, 3, rows 6 and 7 of 4, 5, 6); steps 1 to 5 are
[algorithm-check-credit-steps-1-4.md](algorithm-check-credit-steps-1-4.md) and
[algorithm-check-credit-step-5.md](algorithm-check-credit-step-5.md).

## The rule

From mvp-0.62 a new decision values a lesson offer's committed delayed check as `docs/specs/spec_teacher_v2.md` §7.4
states it: the check is delivered with its cold-completion probability (the as-of receipt counts with the one-trial
seed: `alpha = e + S`, `beta = (1 − e) + F`, `e` whether a question exists now; a point mass at an endpoint), happens
only on a simulated return on or after its date and inside the window, takes the plan's minutes for one check on that
session's clock (so it can displace tail practice and is charged the attention price), and draws its delivery and
outcome from streams of its own. An undelivered check is no event: no dose, no information, no minutes. Below the tag
a decision is valued exactly as before (the check a free full practice attempt at its due day).

## The tag

- One constant, `COMMITTED_CHECK_DELIVERY_ALGORITHM_VERSION = "mvp-0.62"`, appended to `SUCCESSOR_CHAIN`, with
  `COMMITTED_CHECK_DELIVERY_VERSIONS = successors_from(it)` and one predicate, `committed_check_delivery_on(config)`,
  which both readers use (the offer builder and the chooser), so they cannot disagree.
- One upgrade row, `Link(COMMITTED_CHECK_DELIVERY_ALGORITHM_VERSION, idempotent_projection)`: only new decisions move;
  nothing already derived is reinterpreted (design §3).
- One test row in `tests/test_upgrades.py`'s `EXPECTED_ACTIVATIONS`.
- Commits: the delivery reader's move `36c0cddd09`; the finding and the report's options `0840d840e0`; the tag
  `54786dbae4`; the activation `d0f81c792c`; the tests that read the latest tag's evaluation `d13912d769`; this record, the G2 renumbering and the ledger in the commit after it.

## Read first: the owner-copy finding, explained

The step-5 report, run by the orchestrator on a backup copy of the owner's vault, rated lessons *higher* once the
phantom check was gone: on the 5 offers it could compare (lesson against stopping), proposed minus old `q` was +0.018
at 8 draws and +0.065 at 64, on values near 9.4; at 64 draws the old accepted branch (9.349) was below the old declined
one (9.410); no offered topic had an eligible question and delivery so far was 0 of 19, so the proposed path credits
no check at all. The phantom practice event was counting *against* lessons. Two mechanisms produce that direction,
each reproduced on one synthetic topic with no return in a 30-day window, the combiner linear at fixed `(a0, aA, aR) =
(0, 1, 0.5)` (a practised topic reads `σ(0.5·η + 0.5·logit R)`, an unpractised one `σ(η)`), `γ = 0.2` fixed, a
15-minute lesson at mass 0.5, a check 3 days after it, 8 draws (`tests/test_check_credit_characterization.py`, the
"owner-copy finding" tests). The terms are the accepted branch's ledger, new minus old:

| Term | A: unpractised, `η = 2` (either review draw) | B: practised, stability 30, `η = −2`, the mvp-0.49 draw | B under the served draw |
|---|---:|---:|---:|
| crossed-date reward | 0 | 0 | 0 |
| undated reward during the action | 0 | 0 | 0 |
| κ integral (the lesson's minutes) | 0 | 0 | 0 |
| tail reward (to `C`) | **+1.178857** | **+3.913109** | −0.366634 |
| tail cost | 0 | 0 | 0 |
| terminal reward (`C` to `C + H`) | **+2.738082** | **+4.250329** | +0.202508 |
| terminal cost | 0 | 0 | 0 |
| `q` | **+3.916939** | **+8.163438** | −0.164126 |

(The report's branch terms group these: `after = tail_reward − tail_cost + terminal`, `terminal = terminal_reward −
terminal_cost`. Here all of the move is in `after`, split as above.)

**Which term moves, and why.** In both mechanisms the phantom event moves only the undated reward after the action
(`tail_reward` and `terminal_reward`), never the action's own terms, the costs or a crossed date: it acts on the topic's
memory state at the day-4 boundary, and every later day's undated use reads that state.

- **A: a first graded attempt switches an unpractised topic onto forgetting** (ledger **TV2-2**, a second defect, in the
  memory model, not in the check credit). The router's combiner reads an unpractised topic as AD's predictive alone,
  constant in time (`memory.perform`: the retrievability term is multiplied by `practiced`), and a practised one with
  FSRS's `R`. The phantom check is the topic's first graded attempt: it adds `γ` to `η` but sets `practiced` and a
  first-review stability (2.31 days on a success, 0.21 on a lapse), so from day 4 the topic reads
  `σ(0.5·η + 0.5·logit R)` with `R` decaying over the 60 days to `C + H`, below the `σ(η)` it would have kept, which
  never forgets. The same holds under either review draw (a first attempt reads AD's predictive both ways). In a
  scratch run closer to the report's inputs (the real input builder's `Inputs` from a synthetic vault: AD's link, the
  monotone combiner prior, the lesson curve; the lesson topic unpractised with `η = 2`, eight practised topics beside
  it, a 30-day return gap, 64 draws) the accepted branch is worth +0.046 more without the phantom under the mvp-0.49
  draw and +0.128 under the served draw, and the old accepted branch is below the declined one (12.329 against 12.503
  under the mvp-0.49 draw), as on the owner's copy. **The new path still has it for a delivered check** (and every first practice in the rollouts has
  it: a tail session's, a new-practice block's, a repair's); an undelivered check no longer triggers it, which is all
  this tag changes about it. Its fix is a memory-model successor (how a first attempt starts forgetting), the owner's
  call; not in this tag.
- **B: under the mvp-0.49 review draw a phantom lapse collapses a practised topic's memory** (ledger **TV2-3**, a defect
  in the step-5 report, fixed here). The report's current-copy scenario evaluated both pricings with no rollout options,
  so it ran the per-block tail and the review draw from AD's predictive alone, not the memory model's own `P(perform)`
  every decision has served since mvp-0.50. With `σ(η) ≈ 0.12` the phantom review is mostly a lapse even though FSRS's
  `R ≈ 0.99`, and FSRS's lapse update cuts stability 30 to a few days, so the topic's long-run `R` and performance fall
  (+8.163 without the phantom). Under the served draw the same check is mostly a success and the phantom inflates the
  branch (−0.164 without it): the "free practice inflates lesson offers" reading. The owner's numbers (+0.018, +0.065)
  were computed under the mvp-0.49 draw; the report now runs under the copy's served options
  (`objective_chooser.rollout_options`) and records them, and the orchestrator reruns it.

The orchestrator's untraced guess (the phantom event resets or displaces the lesson's own gain) is not the cause: the
lesson's gain on `η` is untouched (the check adds `γ` on top), and the lesson window it resets is read only by a later
lesson, which no tail runs. Which mechanism dominates on the owner's copy is a measurement for the rerun: if the sign
stays positive under the served draw, it is A (unpractised offered topics with a high AD prediction); if it turns
negative, it was B.

**Decision to activate.** The direction is reproduced and explained (A is the rollouts' existing treatment of a first
practice, B was the report's), the new path prices an undelivered check as no event exactly, and neither mechanism is a
reason to keep crediting a check that never happens. So the tag activates.

## What activates at mvp-0.62

All together, for decisions made at the tag:

- **The offer record** (`daily_plan.lesson_offer.build`, `_with_sensors`; `daily_plan.check_inputs.check_sensors`): each
  committed check gains `key` (`<lo>:<purpose>:<ordinal>`), `group` (`legacy_vault_item:<purpose>`), `delivery` (the
  posterior's record: policy and priors versions, basis, purpose, regime, `eligible_now`, `S`, `F`, censored by reason,
  `alpha`, `beta`, predictive mean, evidence digest, `seed_trials`), `minutes` (the plan estimator's four-decimal minutes,
  basis, provenance item, estimator version) and the rollout path's `rollout_policy` and `stream_layout`. The receipts
  are classified once per offer, as of the decision. The decision's clock is left out of the record on purpose: the
  record is in the boundary's identity, which must not move between a prefetch and its serve unless the evidence did.
  Receipts that cannot be read credit nothing (the point mass at zero, `status: unavailable`), never a guessed rate.
- **The action** (`lesson_offer.typed_checks`, `objective_inputs.action_for`): a record with sensors gives
  `Action.checks` (typed), none untyped; a record without them gives the untyped pairs as before.
- **Every evaluation of the decision** (`objective_chooser._evaluator`): the first evaluation with its refinement, the
  LLM-corrected one and both carried valuations run `check_value.evaluate` at the tag, the rollouts below it. Actions
  without typed checks are valued exactly as by the rollouts on that path (step 4's byte tests). `baselines` and the
  day's `gain` curve value no action (the tail from the decision's state), so no check exists for them to price; they
  are unchanged. The belief's world (`_Model._belief_model`) is now built with the model's own class, so a
  check-credit model's probe branches run on a check-credit model. The diagnostic evaluator (G2's, unserved) builds
  the check-credit model when its action carries typed checks: its offer branch prices them through the new path.
- **The identity**: the record's sensors are in the candidate's `log_row`, so the boundary key and the numeric seed move
  when the availability, the receipts (the digest) or the minutes move, and only then
  (`test_the_offers_identity_moves_with_its_delivery_evidence_and_only_with_it`). The objective and terminal formula
  versions do not change; RO6's generator key moves with the tag string.
- **The trace**: the offer section's `action` lists the typed checks (only when there are any), and the decision's
  trace holds `check_credit_replay` (`router_objective.check_replay`): version `check_credit_replay_v1`, a canonical JSON
  string and its SHA-256. The string holds the frozen `Inputs`, every candidate with its branches as valued (`proposed`)
  and with each typed check turned back into the old pair (`old`), the numeric seed, the final, first and ceiling draw
  counts, the rollout options (with RO6's `unmeasured` topics), the clock the inputs were read at, the versions and each
  check's sensors as its offer recorded them. No question, answer or title. A payload holding a NaN or an infinity is
  not written (the decision is then not replayable, and says nothing else). The string survives the trace's six-decimal
  rounding.
- **The report** (`scripts/check_credit_report.py`) reads that payload as the EXACT class: it accepts it only when it is
  this decision's (the chosen offer, the decision's feasible support), was read no later than the decision, names the
  policies this checkout prices, and recomputes the value the trace recorded (within the trace's six decimals); it then
  values both pricings on it.

## What does not move on upgrade

The upgrade is the idempotent projection: no whole-vault rebuild, no migration. Recorded router decisions (a raw ledger),
objective traces and forecast receipts (receipts), plans and their workflows, accepted-offer contracts, lesson receipts
and canonical commitments are not recomputed or rewritten; a decided workflow consumes its recorded decision. Mastery,
facet and scheduling projections do not depend on the tag. Only decisions made after the upgrade use the new rule; a
later plan rebuild that makes a new decision makes it at mvp-0.62 and records it as new. No G2 behaviour is activated.

## Both tags

| Test | mvp-0.61 | mvp-0.62 |
|---|---|---|
| `test_check_credit_characterization.py::test_both_tags_an_offer_with_no_eligible_question` (was the strict xfail) | untyped `(lo, 3.0)`; the decision's evaluator is the rollouts; accepted 0.600000000 against the lesson's 0.500000000 | typed, delivery `(0, 1)`; the evaluator is `check_value.evaluate`; accepted equals the lesson alone, draw for draw |
| `test_check_credit_activation.py::test_both_tags_the_offer_record_and_its_action` | the record's check has exactly `lo, purpose, days, basis`; untyped action | plus the sensors; delivery `(1, 0)` (a question, no receipts); typed action |
| `test_check_credit_activation.py::test_both_tags_the_decisions_numeric_answer_and_its_trace` (`run_numeric` end to end, then `decision_trace`) | untyped, no payload, no `checks` in the trace's action | typed; the payload decodes to the answer's inputs and actions, its sensors are the record's, and recomputing gives every row's draws exactly |

Fail-first: with `committed_check_delivery_on` forced false, five tests fail (`test_the_tag`, both `[mvp-0.62]` arms
above, the identity test, the characterization `[mvp-0.62]` arm); the `[mvp-0.61]` arms and the pure tests pass.

## Pins and goldens that moved

- **The tag commit, by the tag string alone** (as at mvp-0.61): `tests/goldens/identities.toml` six pins
  (`A1-A4.manifest_hash.init`, `C3.boundary.init`, `C3b.chooser`, `C3b.start_key`, `C5.init`, `C6.init`), regenerated
  with `tests/test_identity_pins.py --write`; `tests/goldens/effective_defaults.toml` (the `algorithms.algorithm_version`
  line); `tests/cli_surface.json` (`upgrade --to`'s default, that line edited by hand: the writer would also have
  rewritten unrelated drift); `tests/goldens/placement_stored_misses.json` (the manifest's tag);
  `tests/fixtures/diagnosis_journey_golden.json` (311 tag strings and its two decision states' config and snapshot
  hashes, nothing else; its repeated recording is deterministic: 21 passed); latest-tag and chain-position pins in 38
  earlier successors' test files (mechanical).
- **The activation commit**: no existing pin moved (`test_identity_pins` 348 passed before the new pins were written).
  New pins: `C3.boundary_offer.init` (the hand-written boundary with a lesson offer whose check carries its sensors),
  `C3b.chooser_offer` and `C3b.start_key_offer` (the chooser's own identity and start key with that offer beside the two
  blocks), `C7.streams` (the committed checks' named streams: the posterior group's propensity draw, and delivery and
  outcome for commitments 1, 8 and 9 and a second on one topic). Step 4's stream tests (`tests/test_check_value.py`)
  hold their independence, stable prefixes under `K → 2K`, insertion and reordering invariance. C3m (the mix's seed) and
  C4 (objective settings, switch snapshot) did not move.
- The diagnosis journey golden did not move with the activation: its journeys build no lesson offer, so no lesson-offer
  behaviour is exercised there; all of its diff is the tag commit's.
- Router objective goldens: none moved. `tests/test_te3b_value.py` and `tests/test_ro4_value.py` value their cases on the
  rollouts directly, which keep the old pricing for untyped commitments, as the explicit old-tag cases they are.
- Pinned draws: no test node id changed.
- Assertions changed: `tests/test_check_value.py`'s G2 refusal of typed checks became the G2 evaluator pricing them
  through the new path (the activation's adapter); the three AST scans that pinned the path, the reader and the
  adapters as unreachable from `src` were deleted with their premise; `test_today_an_offer_is_built_with_a_check…` is
  pinned to mvp-0.61 and renamed `test_below_the_tag_…`; the report's real-builder test asserts the scenario's options.

## Judgment calls

1. **The delivery reader moved to `daily_plan`** (`daily_plan/check_delivery.py`, from `teacher/`). The offer builder
   reading it from `teacher` closed a `daily_plan → teacher` package cycle that the frozen-cycles contract refuses; in
   `router_objective` it closed one through `scheduling` (step 4's reason for `teacher`). The plan already reads
   `scheduling`, `serve_eligibility` and the grade holds. A pure move in its own commit.
2. **The evaluator is chosen by the tag, the action by the record.** At the tag every evaluation runs the check-credit
   path; the record's sensors decide typed or untyped. A record built below the tag reaching an evaluation at the tag
   (none should: the boundary key holds the tag) is refused by the new path and the numeric policy falls back to the
   staged rule, loudly, rather than credited the old way.
3. **The clock is not in the record.** The posterior's and the minutes' `as_of` are dropped from the offer record
   (they would move the boundary key at every boundary and break the prefetch lookup); the payload holds the clock.
4. **The payload's clock is the input build's**, which can precede the decision's own `created_at` (a prefetch); the
   report accepts a payload read no later than the decision and binds it by the recorded value instead of an equal
   timestamp. The step-5 prototype format keeps its rule.
5. **Baselines and the gain curve stay on the rollouts.** They value no action, so they hold no check; running them
   through the subclass would change nothing and add an import.
6. **TV2-2 is recorded, not fixed.** It is the memory model's (every first practice), the fix changes persisted meaning
   on its own, and the brief bounds this tag to the check credit.
7. **The payload's digest is integrity, not identity.** It is a SHA-256 over whole dataclass dumps, but nothing compares
   it as a key; `tests/test_identity_pins.py`'s dump scan does not see it (no `asdict`), and no pin is registered for it.

## Playbook gates (synthetic; the owner copies are the orchestrator's)

All through the scratch wrapper, `-n 1`, in a 3G scope, one command at a time, at the activation's tree unless
noted.

| Gate | Command | Result |
|---|---|---|
| Effective defaults (step 4) | `tests/test_effective_defaults_golden.py --write`, then the test | the algorithm line only; passed |
| Identity review (step 4) | `tests/test_identity_pins.py --write` at the tag commit, then at the activation | six tag pins at the tag; four new pins, none moved, at the activation; 352 passed |
| Upgrade path, recovery, idempotent re-run (step 8) | `tests/test_upgrades.py` (every row, a death at each point, a re-run) | passed (in the 638 below) |
| Replay completeness and rebuild equivalence (step 6) | `tests/test_rebuild_equivalence_review.py` and the upgrade and rebuild files in the name filter | passed (in the chunks below); no table, projection or replayer changed |
| Shadow rebuild on a copy, foreign keys, doctor, live hash, second rebuild (steps 7, 8) | the orchestrator's, on owner copies (below) | not run here |
| The new and edited check-credit files, pins, ratchets, defaults, CLI snapshot, kill switches, SQLite copies, public-tip guards, upgrades | 14 files | 638 passed |
| The brief's name filter (check_credit, check_delivery, check_inputs, check_value, ro2_, ro4_, ro5_, ro6_, te3b, te2_, lesson_suggest, upgrades, algorithm_version, effective_defaults, diagnosis_journey, due_queue, rollout: 57 files), `-m "not arc_close"`, two chunks | | 403 passed; 253 passed, 1 failed (`test_te3b_offers`, the served offer's trace, fixed: see below), then the file 10 passed |
| `scripts/affected_tests.py --files` the 14 changed source files lists 1,333 files; beyond the name filter, the 66 among them naming objective, offer, trace, te3, rospeed, ro1_, rofu, ih, sg_, te1b, probe_router, diagnostic_probe_value or action_kinds, `-m "not arc_close"`, two chunks | | 639 passed, 4 failed; 409 passed, 2 failed (the refinement, carried-valuation and slip-or-gap twin tests, ported: see below), then those three files 44 passed |
| The router objective's arc-close tests (`test_ro6_tail_data`, `test_rofu_weeks`, `test_ro5_calibration`), `-m arc_close`, once | | 3 passed |
| The diagnosis journey golden (repeated recording) | at the tag and at the activation | 21 passed each |
| `tests/test_test_layout.py` alone; `tests/test_architecture.py` alone | | 3 passed; 18 passed |
| `ruff check`; `lint-imports --no-cache`; `scripts/check_gate_partition.py`; `git diff --check` | | All checks passed; 45 kept, 0 broken; 32534 collected: landing 32468 + arc_close 66; clean |

**Tests that followed the activation** (`d13912d769`): `tests/test_te3b_offers.py` asserted the served offer's trace
action held the untyped pair; at the latest tag it holds the typed check and the trace the replay payload, so it now
asserts those (the one exercised lesson-offer behaviour in a served journey). `tests/test_objective_refinement.py` and
`tests/test_rofu_carried.py` spied on `rollouts.evaluate` to hold and count batches at the latest tag; the chooser's
evaluator there is `check_value.evaluate`, so they spy on it (a public name, no private patch added).
`tests/test_sg_slip_vs_gap.py`'s twin journeys pair two runs boundary by boundary at pinned draws; at the latest tag the
check credit's offer values part them at another boundary (six traces against five), so the twins run at mvp-0.61.

## What the orchestrator must run on owner copies

On idle backup-API copies of `arxiv_v2`, `linear_algebra` and `probability` (each at mvp-0.61), with this branch:

1. The report before: `python scripts/check_credit_report.py --vault "$COPY" --json --out "$BEFORE"` (now under the
   copy's served rollout options; compare with the step-5 numbers: the sign of the current-copy difference tells
   mechanism A from B above), with `--draws 8` and `--draws 64`.
2. Record the live vault's database SHA-256.
3. `learnloop upgrade --vault "$COPY" --to mvp-0.62`: expect `completed the activation of mvp-0.62 (its projection
   activation)`.
4. `learnloop rebuild --shadow --json --vault "$COPY"`: zero mastery, facet and scheduling deltas.
5. `learnloop doctor --vault "$COPY"` and `PRAGMA foreign_key_check` on the copy: clean.
6. A second idempotent rebuild: every dumped table byte-equal to the first (write stamps and surrogate ids excepted as
   the playbook allows); raw ledgers, receipts, plans and forecast contracts unchanged.
7. The live database's SHA-256 unchanged.
8. The report after, on the upgraded copy: the populations and delivery statistics as before; EXACT still 0 (no
   decision was made at the tag on a copy).
9. Optional, if a no-model plan build is available on a copy: one boundary with a lesson offer at mvp-0.62, then the
   report: EXACT 1 for it, and its trace's `check_credit_replay` decodes.

## The owner-copy lane, as run (2026-11-21; aggregates only)

Backup-API copies of the owner's three vaults in a gitignored directory, with this branch; the copies were
deleted afterwards. The live databases' SHA-256 were equal before the copy, after it and at the end.

| | arxiv_v2 | linear_algebra | probability |
|---|---|---|---|
| Tag before | mvp-0.61 | mvp-0.58 | mvp-0.58 |
| `learnloop upgrade --to mvp-0.62` | upgraded | upgraded (through .59, .60, .61) | upgraded (through .59, .60, .61) |
| Shadow rebuild: mastery rows whose values differ | 0 of 37 | 0 of 21 | 0 of 18 |
| Shadow rebuild: facet rows whose values differ | 0 of 60 | 0 of 80 | 0 of 3 |
| Shadow rebuild: schedule rows changed | 0 of 81 | 0 of 99 | 0 of 77 |
| Rows that differ only in their `algorithm_version` stamp | 37 mastery, 12 facet | 21 mastery, 4 facet | 18 mastery, 1 facet |
| A second shadow rebuild | identical to the first | identical | identical |
| `PRAGMA foreign_key_check`; `integrity_check` | 0 rows; ok | 0 rows; ok | 0 rows; ok |
| Doctor errors (content findings that predate this tag) | 46 `criterion:unknown_dependency` | none | 46 `criterion:unknown_dependency`, 2 `yaml:invalid` |

The stamp-only rows are what a projection activation leaves: it re-runs the canonical facet projection and
records the activation, and does not rewrite the mastery or facet-uncertainty rows, which keep the tag they
were last written under (`mvp-0.61`) until their topic is next written; a full replay stamps `mvp-0.62`. No
value differs.

**The report on the arxiv copy, under the rollout options decisions are served with** (the step-5 run used
the `mvp-0.49` review draw: ledger TV2-3): 5 of 6 offers computable in the present-day lesson-versus-stop
scenario; expected completed checks 0; exact historical values 0 of 6 before and after the upgrade (no stored
decision has the lossless payload yet).

| Draws | proposed minus old q | old accepted / declined | proposed accepted / declined | numeric choice changed | ranking changed |
|---|---|---|---|---|---|
| 8 | -0.061 | 8.439 / 8.280 | 8.377 / 8.280 | 1 of 5 | 1 of 5 |
| 64 | -0.034 | 11.515 / 11.678 | 11.476 / 11.678 | 0 of 5 | 1 of 5 |

So under the served draw the fix LOWERS the lesson's value on this vault, as the defect's description
predicts, and the positive difference reported on 2026-11-20 was explanation B above (the report's draw), not
A. The report's numbers before and after the upgrade are identical.

## Remaining limitations

- TV2-2 stays: a delivered check, and every first practice, still switches an unpractised topic onto forgetting.
- The payload records the numeric inputs, not the mixing inputs, so the report's EXACT class computes values and the
  numeric choice, not the changed mixing probability.
- The resolved-outcome estimator stays optimistic under persistent censoring (design §5); the report shows the censored
  counts.
- The delivery reader classifies every receipt at each offer build; fine at today's few dozen entries, to revisit if
  receipts grow by orders of magnitude.
- A check whose minutes cannot be estimated is recorded at 0 minutes with basis `unavailable` (it is still delivered
  with its probability).

## Not verified

- The owner's vaults and the comparison on copies (the orchestrator's); the landing gate and the whole suite.
- Durability (`--durable-sqlite`) on the new tests.
- A real served boundary through the sidecar with a lesson offer at the tag (the numeric policy and the trace were run
  through `run_numeric` and `decision_trace` directly).
- The vault references are not regenerated (the landing does).
