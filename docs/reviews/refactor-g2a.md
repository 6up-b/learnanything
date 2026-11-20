# G2a. The router decides: steps 1 to 3 (characterize, the pure post-miss choice, the proposal's reads)

Branch `refactor/g2-router-decides`, base main `0f309a8687` plus the design commit `6be52f0476`
([`refactor-g2-design.md`](refactor-g2-design.md)). Steps 1, 2 and 3 of the design's §4: characterization and
structure only. No served decision, draw, seed, trace, stored value or prompt byte changes; the behaviour change
(step 6, `mvp-0.62`) is not started. [Strategy §2.10, G2](../specs/refactor_strategy_v3.md#210-arc-g-one-decider-one-record-of-each-fact-one-belief-one-protection)

## Commits

| Commit | Step | What |
|---|---|---|
| `ff9ac1307f` | 1 | `tests/test_probe_router_authority.py` (28 tests), `tests/probe_router_authority_helpers.py`, three new cases in the diagnosis journey golden |
| `050471fb7a` | 2, proof first | `tests/test_post_miss_choice.py`: `ObjectiveRestraintGate._mixed` over a grid, its golden written by the unchanged code |
| `59b672061d` | 2, proof first | the grid reaches three more parse conditions (10,260 cases), golden rewritten by the unchanged code |
| `d88ec36952` | 1 | structure golden `golden_json_lines` 230,733 → 235,023 for step 1's journey cases (their 4,290 lines) |
| `815bbc86ff` | 2, proof first | the grid golden packed one line per shape (same digests); `golden_json_lines` → 235,085 |
| `a903b8580d` | 2 | `router_objective.choose.post_miss_choice`; `_mixed` calls it |
| `51da03ba32` | 3 | `causal_orchestrator.gather_probe_reads` → `probe_facts.ProbeProposalReads`; `_status_for_factor` reads it |

The structure ratchet rose with step 1's and step 2's first commits and was raised two commits later, so
`ff9ac1307f`, `050471fb7a` and `59b672061d` each fail `tests/test_structure_ratchets.py` on their own; each step lands
as its series (step 1 with `d88ec36952`; step 2 from `050471fb7a` to `a903b8580d`).

## Step 1: every door, characterized

`tests/test_probe_router_authority.py` pins today's answer at each site of the design's inventory (§1), at the head
tag, and the rows it leaves. No production code changed. The sites and their tests:

| Site | Surface | Cases pinned |
|---|---|---|
| A, lane existence | automatic | two concrete rivals → probe lane; the open arm, a vanished hypothesis and a repeat are not rivals; one rival, no factor, no concrete cause → practice; the first factor with two rivals wins. The practice lane settles the workflow (`settled`, `practice_lane` release, no arm, no decision) and hands the miss to G (`insertion_only`, diagnosis hooks deferred), once |
| B, causal gate | learner | a status read offers the quick check (`probe_now`, three actions) and **each read writes a new receipt** (a remount is a second verdict), with no router row and no episode; "Not now" withdraws the offer (`defer_learner_preference`, teach-now only) while the divergence stands; no instrument → `skip_no_discrimination` on the pinned 0.0 gain, `blocked_pending_review`/`no_discriminating_instrument`, with the gain's `heuristic_default` provenance and `likelihood_completeness = {complete: false, reason: no_instrument}` on the receipt; one repair for both causes → `skip_common_repair`, `safe_common_repair_available`, an episode |
| B, an existing pin | learner | accepting twice returns the same presentation (`probe_already_pinned`) and writes no receipt; acceptance reads neither the receipt's verdict nor "Not now": a stale request after "Not now" still pins |
| C, repair entry | learner (manual request) | a repair request on a divergent factor raises `RemediationBlocked(needs_disambiguation)`; over the sidecar it is a result with `episode: null`, one receipt per request, no episode; "Teach me now" starts the repair with no probe (`defer_learner_preference`, `learner_requested_teaching_without_probe`) and the repair entry then returns that episode under a fresh receipt |
| D, hard refusals | automatic | "Not now" before the job: refused, no question written, feedback released, a **planless router row** (`staged_v1`, propensity 1, `refused` detail) with an `outcome: refused` binding and a `followup_gate` record (`learner_decline`, logged); a pending repair-mapping machine check refuses the same way; the order is preference, machine checks, then the shared episode check (which is not asked once an earlier one refuses); "Not now" while the question is written: decided (ask now), paid for, then refused with nothing bound |
| D, retry | automatic | a recorded arm is kept (`recorded`, no gate record, no draw); a refusal that holds at the retry is its outcome (`decline`), the row keeps the first draw and only the gate record says `retry: true`; a recorded no-intervention or lesson arm is returned as recorded whatever refuses |
| E, logged class verdict | automatic | divergent classes → `decide_probe_absent: no_instrument_before_authoring`; one class → `skip_action_equivalent`; unreadable → `{}` |
| F, no plan | automatic | ask now, no draw, **no router row, no binding**, gate record `no_plan` (not logged), feedback held, no causal receipt (the automatic lane never asks B) |
| F, existing presentation | automatic | the serving door never asks the value rule for the router's committed presentation (a spy on `probe_value_block_reason` sees no call) and serves it; no `probe_value` record |
| F, on a plan | automatic | one draw over `insert_now, continue_current, no_intervention` and the lesson at the same boundary; wait releases at once and marks the question exposed; the trace, decision-state receipt, frozen objective (`arm: wait`) and logged gate record; a lesson win releases (`lesson_offer_won`), generates nothing, binds `outcome: lesson_offer`; no intervention settles and releases |
| F, no room to wait | automatic | ask now deterministically (`staged_v1`, `no_room_to_wait`, propensity 1, support `[insert_now]`, no mixture), unless a lesson contests it: then a real draw over exactly `insert_now` and the lesson |
| F, restraint (need path) | automatic | mid-block, no room → `no_room_to_wait`; room → a draw over the two arms |
| F, retry on a plan | automatic | the workflow's logged decision is reused: no second draw or row |
| G, value suppression | automatic (practice lane) | value does not pay → suppressed (`voi_value_below_minutes_cost`), a `followup_value_decisions` row (`stop`); the learner's request overrides it (`manual_override`, logged as would-suppress); value pays → queued |
| H, scheduler | both | value does not pay → every probe's `probe_eig` zeroed and `voi_stop`, one `stop` decision; pays → probes scored, `continue` |
| I, serving door | both | value does not pay → `value_below_minutes_cost`; the sidecar refuses the new presentation and writes a `probe_value` record |
| J, block continuation | both | FG1's one-question block closes whatever value says; an ordinary three-question block closes after its first answer only when the next observation does not pay |
| K, completion | both | value completes the episode (`value_of_information_stop`); with the value switch off the count does (`observation_budget_exhausted`) |

The journey golden (`tests/diagnosis_journey_helpers.py`, design §4 row 1) gains three cases that record every
table stage by stage: `fg1_refused_before_authoring`, `fg1_refused_while_authoring` and
`causal_reread_and_request` (two status reads, a held repair request, the quick check accepted twice). The 18
existing cases are byte-identical in content; the file diff is large only because the new keys sort among them.

**Stop rule.** Every site the design lists has a caller demonstrated by a test above. Two pieces of a site were not
reached and are listed under "not verified": the Textual screen's copy of I, and H's `probe_gate` zero-EIG rejection.

## Step 2: the pure post-miss choice

**What moved.** `ObjectiveRestraintGate._mixed`'s policy-status, failure, weight, component and draw assembly
(base `objective_chooser.py:1188-1207`, 20 lines) is `router_objective.choose.post_miss_choice(PostMissInputs) ->
PostMissChoice`. It reads the LLM policy's answer from whichever request was sent (per option: a parse that is the
policy's own, names exactly the support and gives every option mass; yes/no: strictly between 0 and 1), fails the
numeric policy outside the support, applies the failure rule, builds the components and draws once from the seed. The
shell keeps the reads in their order (the weight, the failure rule, then `new_ulid` and the seed that depends on
it), the trace, the record, the why and the offer's guarded why. `mix.draw` is still called through its module, so the
fixtures that replace it reach the served draw.

**Order.** The pure parse, failure, weight and component computations now run after the weight read and the id mint
instead of before them. They read nothing and cannot raise on the inputs that reach them (`w` from `current_weight`
is in [0, 1]; `insert_now` is in every support `_mixed` gets), so no read, id or draw moved relative to another; this
is the same observation E2 made for `choose`.

**Proof (written before the move).** `tests/test_post_miss_choice.py` calls the real `_mixed` (only `run_numeric`,
`current_weight` and `new_ulid` replaced by fixed answers, the models by fixed results) over a grid: 6 support shapes
(the restraint's two arms; the restraint with a lesson, with and without room; FG1's three arms; FG1 with a lesson,
with and without room) × every readiness (none, Decider, LLM, both) × each model answer (Decider answered or failed;
LLM per option: shown rationale, unknown evidence, no rationale, a missing arm, a zero arm, a parse of the wrong type,
a parsed answer under a failed status, invalid, timeout; yes/no: 0.3, 1.0, 0.0, no probability, failed, timeout) ×
5 numeric answers (first arm, last arm, outside the support, timeout, failed) × the failure rule both ways × w 0.35
and 1.0 × 3 seeds (two pinned, one derived from the boundary key and the decision id). 10,260 cases. Each case's whole
outcome (served arm, propensity, the full record with its trace and mixture, why, wait-feasibility and the numeric
policy's call: support, candidates, sequences, seed, deadline) is serialized and hashed. The golden was written by
`59b672061d` (the predecessor's code); `a903b8580d` reproduces all 10,260 digests and the served histogram (every
arm of every shape is served, and every component, `llm`, `numeric`, `staged` and `uniform`, draws in every shape). Two runs of a case are byte-equal.
Fail-first: three mutations of the core each fail it (yes/no `<= 1.0`: 180 cases; a per-option rationale kept without
its parse: 900; the zero-mass check dropped: 900). Six literal tests of the core (no vault) cover the statuses, the
failure rule and the seed.

P-draw: the harness E2 and G1 rebuilt runs no mid-block or post-miss decision (no `plan_interrupt` row in its
scenarios), so it cannot see this change and was not rerun; `ObjectiveChooser` and `choose()` are untouched. The
journey-level tests that reach `_mixed` (step 1's F tests, IH2, RO5, the follow-up router) pass unchanged.

## Step 3: the diagnostic proposal's reads

**What moved.** The 116 lines of `_status_for_factor` after its mapping checks and before `decide_probe` (the
classes' need and cover, the diagnosis receipt's cover, pending machine checks, the episode conflict, the ordered
candidates and the chosen one, its separability, the locked set's prior basis, the likelihood coverage, the burden,
the avoided minutes, the preference, the recent probe count) moved **verbatim**, comments included, into
`causal_orchestrator.gather_probe_reads`, which returns `probe_facts.ProbeProposalReads` (plain values; `probe_facts`
still imports nothing of LearnLoop). Two locals only the old call used (`expected_information_gain`, `action_change`)
were dropped. `_status_for_factor` calls `decide_probe` with the same arguments, read from the value, and builds the
same receipt inputs. The reads keep their order and their conditions (machine checks only when the cause set is
probe-worthy), so no query moves, the lock read (`fetch_hypothesis_set` of the chosen candidate's set) is the same
row, and no prior is normalized. `ProbeProposalReads.facts()` gives `ProbeFacts` through `probe_facts` (reused).
`channel_status` (`no_instrument`, `no_separability_record`, `separability_computed`; pure `channel_status()`) keeps a
missing instrument and an unreadable record apart from the 0.0 the verdict is given for both; it enters no receipt.
Today's only "channel" is pairwise separability of blind bundles, never `P(result | h)`.

**Proof.** G1's recording plugin (its `g1_record.py`, plus the `RepairStatus` each `_status_for_factor` returns) over
G1's 42 files and step 1's file (834 tests), at the base (`a903b8580d`) twice and at the tip: 125 receipts in 84 tests
(inputs, parameter manifests, provenance), 113 `decide_probe` calls (kwargs and results) in 76 tests, 117 repair
statuses in 78 tests, 407 hypothesis sets, 152 FG1 observations: **equal test by test** after normalizing ids and wall
stamps. Without wall normalization the tip differs from the base in the same 13 receipt tests and 5 status tests as a
second base run does (wall-clock `created_at`). G1's synthetic `decide_probe` grid (40,569 cases) gives G1's sha256
`1ebf13c7af32...` at the tip. `tests/test_probe_proposal_reads.py` (constructor-only, no new live receipt): the facts
equal `probe_facts` on literals; the three channel states; gathering writes no row of any registered table; the
verdict on the gathered facts is the status's verdict, with and without an instrument.

## Net lines

| Step | Production | Tests |
|---|---|---|
| 1 | 0 | +784 (+71 journey helpers, +97 helper, +616 tests), journey golden +4,290 lines |
| 2 | +84 (`choose.py` +86, `objective_chooser.py` −2) | +355 (grid and literal tests), golden 62 lines |
| 3 | +137 (`causal_orchestrator.py` +63, `probe_facts.py` +74) | +96 |

**The cost rule.** Steps 2 and 3 each add more production lines than they remove, and no existing test got simpler
(the new cores are tested with literals, but those tests are new). They continue because the design's later steps use
them: step 6 puts the probe candidate's support and values into the post-miss choice, and builds its diagnostic
proposal from the gathered reads (design §2a, `gather_probe_proposal`).

## Where the code differed from the design

1. **A planless refusal is logged.** The design (§1 F, §2d) says no-plan has a gate record and no router row. That
   holds for no-plan's ask-now only: a hard refusal with no plan goes through `record_decision`'s logging path and
   writes a `plan_interrupt` row with null plan and block, `staged_v1`, propensity 1, and an `outcome: refused`
   binding; its gate record says `logged: true`.
2. **E and B disagree on one shape.** For two causes that need the same repair, FG1's logged verdict is
   `skip_action_equivalent` while the causal gate decides `skip_common_repair`: the gate treats a cause set that is not
   probe-worthy as covered (`causal_orchestrator.py`, `common_repair_covers = ... or not targeting.probe_worthy`), FG1's
   `_observe` does not. E decides nothing, so no learner sees it; G2 removes the verdict. No ledger row.
3. **I's bypass is two-fold.** For FG1's own item `probe_value_block_reason` also returns `(None, None)` (the item is not
   among the episode's eligible instruments), and the door never asks it for a committed presentation. The test pins
   the second.
4. **Acceptance asks nothing.** `accept_probe_offer` reads neither the receipt it is handed nor the learner's
   preference: a stale "Take the quick check" after "Not now" pins the probe.
5. **Line citations** checked in §1 (lanes, router, objective chooser, jobs, remediation, sidecar handlers, scheduler
   `:3219`/`:3307`, presentations `:391`/`:428`/`:463`, blocks `:87`/`:146`, completion `:69`/`:617`/`:645`,
   `voi_stopping.py:2167`) match the code at the base.
6. **`_mixed`'s P-draw.** The design asks for existing P-draw identical; no P-draw scenario reaches `_mixed` (above).

## The design's §8 questions these tests answer

- **Planless doors** (one no-plan repair/status/retry journey): partly. The builder already persists a planless row
  for a refusal (`test_d_not_now_refuses_before_the_router_and_no_question_is_written`, journey case
  `fg1_refused_before_authoring`); no-plan's ask-now persists none (`test_f_with_no_plan_...`); a learner-lane status
  read persists a receipt per read and no router row. Idempotency and a crash between decision and binding are not
  tested.
- **A selected candidate and the downstream worth gates**: for today's FG1 probe, partly. The serving door does not
  re-value its committed presentation, and its block ends at one question whatever value says (I, J tests). The
  scheduler and the Textual screen were not tested for it.

## What was run

Every pytest command ran from a script file under the scratch directory at `-n 1` inside a 3 GB scope, one at a
time; none was killed. At the tip `51da03ba32`:

| What | Result |
|---|---|
| `scripts/affected_tests.py --files` over the four changed source files: 214 files, more than 150, so filtered by name (`router\|objective\|followup\|causal\|probe\|choose\|diagnos\|remediation\|ih[0-9]\|ih_\|ro[0-9]\|rofu\|rospeed\|repair\|voi\|interrupt\|restraint\|lesson\|mixture\|identity_pins\|structure\|journey\|refusal\|te3b\|sg_\|pinned_draws\|plan_determinism\|daily_plan\|data_capture\|mobile_v4_plan\|decision_records\|withdrawal\|post_attempt\|post_miss`) to 146, in 4 chunks of at most 40, `-m "not arc_close"` | 2,643 passed, 9 skipped, 1 xfailed, 0 failed |
| The added and edited test files with `test_identity_pins`, `test_structure_ratchets`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies` | 442 passed |
| `tests/test_test_layout.py` alone | 3 passed |
| `tests/test_architecture.py` alone | 18 passed |
| `ruff check` | all checks passed |
| `lint-imports --no-cache` | 43 kept, 0 broken |
| `scripts/check_gate_partition.py` | 31,622 collected: landing 31,557 + arc_close 65 |
| Step 2's earlier run (19 router, objective, IH, RO and gate files) | 791 passed; the one failure was the structure ratchet, fixed by `d88ec36952` and `815bbc86ff` |
| Step 3's recordings (G1's 42 files and step 1's, with the plugin), base twice and tip twice | 834 passed each |

Identity pins pass with nothing written; no pin moved. The journey golden's 18 existing cases pass unchanged; the
structure golden moved only in `golden_json_lines` (230,733 → 235,085, the two commits above).

## Not verified

- The Textual practice screen's copy of I (it returns on a value refusal, design §1 I).
- H's `probe_gate` rejection of a nonpositive EIG.
- E2's P-draw harness (it does not reach `_mixed`); P-shadow (the orchestrator's; neither step touches replay:
  `objective_chooser`, `choose`, `causal_orchestrator` and `probe_facts` write no derived state).
- The whole suite, durability, `--fresh-connections` and `arc_close`.
- That `815bbc86ff`'s packed golden passes at the predecessor's code: its digests were checked equal to the ones
  `59b672061d` wrote there, and the packing is read back by the test at the tip.

## What steps 4 to 6 need that is not here

- `ProbeProposalReads` carries no locked hypothesis ids or order, no effective posterior, no `P(result | h)` rows,
  no repair per hypothesis (`repair_class_by_hypothesis` is computed in the shell and passed in, not kept), no
  durations; `channel_status` only says whether separability was readable.
- `gather_probe_reads` runs only after `_status_for_factor`'s legacy and incomplete-mapping arms and after
  `close_satisfied_backfills` writes; a router-side gather has to keep those arms (one of them writes an obligation).
- FG1 decides before authoring, so its proposal is `no_instrument` by construction (design owner decision 1).
- `post_miss_choice` takes the numeric policy's choice only; step 6 adds the probe candidate to `run_numeric`'s
  support and sequences, and the no-room arm set (owner decision 3) is still `_no_room`'s deterministic ask-now.
- `post_miss_choice` repeats `choose()`'s six mixing lines; a shared helper would join them, which touches the block
  chooser and its proofs, so it was left.
- The two stop orders (FG1 asks preference first, the gate machine checks first) still differ (G1 §9).

Implementer: one Opus session, no subagents; token use not available to the implementer.
