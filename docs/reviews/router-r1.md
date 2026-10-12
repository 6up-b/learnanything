# Router R1: decision logging on today's paths

Branch `router/r1`, worktree `learnanything-router-r1`, base `5a9a9e3d` (main
with router R0 and Slice A Phase 6 merged). Specs:
`spec_action_router_v1.md` §2, §9 and §11's R1 row;
`spec_p4_controller_and_scale.md` §3.3 and §9.3; `spec_learner_field_v1.md`
§3. Owner decisions of 2026-10-12 in force (defaults accepted, frictionless
defaults: honest labels, generous defaults, live changes behind kill
switches). No model calls in R1.

## Plan (written before coding)

### Code truth checked first

- **Today's queue** is `scheduler.build_due_queue`: a greedy sort on
  `selection_reward`, then Phase 6's new-material reorder, then the seeded
  ε-exploration (`_apply_seeded_exploration`), then a deterministic
  composition (teach-back cap, goal quota, requested floor, same-day
  rotation, forced follow-ups, contrast-pair order, the committed probe
  presentation pin), then `limit`. The sidecar then drops unready teach-back
  items, finalizes the offer (`finalize_scheduler_offer`) and groups it into
  sections; Today focuses, and "Next" opens, the first item of the first
  non-empty section. That head is what the system serves.
- **Propensities today.** Slate candidates record
  `propensity_kind = unavailable_composed_offer` because composition runs
  after the draw. The exploration's probe exclusion now sits in
  `_selection_propensities` and `_apply_seeded_exploration` (the spec's line
  numbers 1544-1551 predate later edits): a PROBE-intent best is never
  displaced and PROBE-intent items are never alternatives. PROBE intent covers
  in-episode diagnostic probes and teach-back items.
- **Offers** are finalized in two places: `get_today_queue` and
  `skip_practice_item`. Learner picks bind a submission to an offered
  candidate in `bind_submission_offer` (practice drafts and submits,
  teach-back).
- **The staged P2 path** (`controller_cutover.staged_next_action` /
  `advance_live`) is the only live staged decision. It has no production
  caller: the desktop's `golden_path.advance` calls `GPR.advance` directly.
  R1 logs where the bridge decides, so the rows appear as soon as it is wired;
  wiring it is a serving change and is not done here (open question).

### Files to add

- `migrations/176_router_decisions.sql`: `router_decisions` (RAW_LEDGER,
  append-only triggers) and `router_outcomes` (DERIVED).
- `src/learnloop/db/stores/router.py`: the only SQL writer for both tables
  (decision insert, learner-pick insert inside the bind transaction, outcome
  replace).
- `src/learnloop/router/` (a leaf package: it imports only `clock`, `ids`,
  `outcome_contract` and `db`, so the rebuild orchestrator can own its
  replayer without a package cycle):
  - `decisions.py`: row builders for Today offers, staged P2 decisions and
    learner picks; the exact head distribution over the exploration's
    outcomes;
  - `outcomes.py`: `R_next`, `R_cold` and `S` per decision, right-censored,
    and the replayer body.
- `src/learnloop/cli/router.py`: `learnloop router log` (read-only listing of
  recent decisions with their derived outcomes) for the owner and this review.
- Tests (all fakes, no model calls): offer logging and exact propensities,
  probe-tie successor and kill switch, staged P2 logging, learner picks,
  outcomes and the replayer, the `mvp-0.12` upgrade.

### Files to change

- `scheduling/scheduler.py`: an optional `offer_trace` out-parameter on
  `build_due_queue` (exclusion reasons, the exploration's support, the
  composed order under every exploration outcome); the composition chain
  moved into one helper used by the live path and the counterfactuals; the
  probe-tie admission behind the successor gate. Nothing else in the queue.
- `scheduling/controller_cutover.py`: log each staged P2 decision.
- Sidecar `queue.py`, `practice.py` (skip), `teach_back.py` (a readiness
  helper the head rule reuses): build the offer row and finalize it with the
  offer receipt in one transaction.
- `db/stores/collection.py`: learner picks recorded in the bind transaction.
- `algorithm_versions.py`, `config/schema.py` (`[router]`), `config/template.py`
  (fingerprints), `ops/vault_upgrade.py` (`upgrade_to_mvp012`), `cli/app.py`.
- `db/table_roles.py`, `substrate/rebuild_orchestrator.py` (the
  `router_outcomes` replayer), `pyproject.toml` (import contracts),
  `tests/test_architecture.py` (SQL owner).

### Migrations

One, the next free number: 176 (main is at 175; T1 takes 176 and the stuck
prompt 177-178 at merge, so expect renumbering). Head fixture
`migration_head_175` upgraded and renamed `migration_head_176` in rollback
mode; README and the hard-coded paths updated; DB and config references
regenerated.

### Algorithm successor and kill switch

`mvp-0.12` (`PROBE_TIE_ALGORITHM_VERSION`; the next free label on this base,
to be relabelled at landing since DL1 and T1 also claim it): `mvp-0.11` plus
the probe-tie admission. Gate set `PROBE_TIE_VERSIONS`; the split, placement
and P0-successor sets gain it (linear chain). Kill switch
`router.probe_tie_admission` (default on). Decision logging is not a serving
change: it runs at every version behind `router.log_decisions` (default on).
`upgrade_to_mvp012` accepts `mvp-0.11` and chains from `mvp-0.9`/`mvp-0.10`.
The projection is unchanged, so the upgrade is a tag plus the idempotent
rebuild, prepared before the atomic config rename.

### Spend caps and model routes

None. R1 makes no model or embedding call; replay makes none (tested with the
model constructors forbidden).

### `judgment_ledger` writes

None: no LLM, verifier or owner verdict is produced.

### Tests

Listed under files to add. The exactness test recomposes every exploration
outcome and checks the realized one reproduces the live queue; the
probe-tie tests check the predecessor is byte-identical and the kill switch
restores it.

---

## What was built

### The decision ledger (migration 176)

- **`router_decisions`** (RAW_LEDGER, append-only: triggers refuse UPDATE and
  DELETE; idempotent on `receipt_key`). One row per decision with the §9
  columns: id, kind (`today_offer` | `staged_p2` | `learner_pick`), surface,
  mode (`legacy_queue` | `staged`), policy, algorithm version, session,
  parent decision (a learner pick names the offer it overrode), slate or
  controller decision link, `snapshot_hash` (content hash of the decision's
  inputs), design and seed, `candidates_json`, `exclusions_json`, the chosen
  candidate (`chosen_ref`, item, LO, scheduler candidate), `propensity` and
  `propensity_kind`, `learner_pick`, and the R2 columns left NULL while no
  model chooses (fallback, mixture weights, model distributions, sensor
  answers, question-set version, model ids, card hash, similar decisions,
  latency, cost). CHECKs: `exact` means 0 < p < 1, `deterministic` means
  p = 1, `none` means NULL, and `none` exactly when `learner_pick = 1`.
- **`router_outcomes`** (DERIVED, one replayer `router_outcomes` in
  `substrate/rebuild_orchestrator.py`): R_next, R_cold and S per decision.
- `db/stores/router.py` is the only SQL writer for both (registered SQL owner).
  `router_decisions_payloads` (§9's WORKFLOW table for model responses) is not
  created: R1 has no model payload; R2 adds it.

### Today offers (`today_offer`)

- `build_due_queue` takes an optional `offer_trace` out-parameter. When a
  caller passes one, the build records:
  - a reason code for every candidate the loop withholds (`withheld(...)` at
    each `continue`): retired, inactive, reserved exam, rung-variant hold,
    staged-owned, microprobe, administered probe, unservable stimulus, no LO,
    put away, diagnostic freshness reserve, **placement assumed / maintained
    withheld**, cold-start, diagnostic reserved, zero priority;
  - the exploration's whole support: for the greedy order and for every
    near-tie the seeded draw could move to the front, the offer the build
    would have composed. The composition steps (teach-back cap, goal quota,
    requested floor, same-day rotation, forced follow-ups, contrast-pair
    order) moved into one local `compose()` used by the live build and by the
    counterfactuals (`record=False` skips the contrast-pair audit row), then
    the committed-presentation pin.
- The sidecar (`queue.publish_offer`, used by `get_today_queue` and
  `skip_practice_item`) builds the row and `finalize_scheduler_offer` writes it
  in the offer receipt's own transaction. The **chosen candidate** is the item
  Today focuses first and "Next" opens: the head of the first non-empty
  section (due/follow-up, then probe, then later). `_OfferHeadRule` applies
  exactly the steps between the build and that head (`limit`, the teach-back
  readiness filter, a skip's removal, the sections, one pinned `now`), so the
  head probability of every candidate is a sum over the exploration's
  support: the **true propensity**. If recomposing the realized draw does not
  reproduce the served head, the row is refused (`OfferHeadMismatch`, logged
  as a warning) rather than written with a wrong number.
- Candidates: every item any outcome composes (planner values: priority,
  selection reward, legacy priority, intent, non-zero signals including
  `new_material`, `assumed_check`, `taught_first`, `placement_layer`,
  `placement_predicted_success`, follow-up lanes; section; considered and
  offered ranks; the pre-composition exploration probability; the head
  probability; the slate candidate id), plus `continue_current` when an item
  is in progress and `stop_for_today` always. Exclusions are `{named: {reason:
  ids}, counts: {reason: n}}`; bulk reasons (retired, nothing due, ...) are
  counts. Phase 6's placement exclusions are named.
- **"Continue"**: a committed probe presentation (the pin) or a saved,
  unsubmitted draft (`session_checkpoints`). A pinned presentation that heads
  the offer is logged as `chosen_ref = continue_current`, deterministic.
- An empty offer (nothing to serve) is a `stop_for_today` decision, written
  directly (no receipt is published for it).
- An offer without a session records no slate, so nothing can be served from
  it under an offer id; it is not logged.

### Learner picks (`learner_pick`)

The first bind of a submission (or a teach-back conversation) to an offered
candidate other than the logged offer's head writes a `learner_pick` row in the
bind's transaction (`collection.bind_submission_offer` →
`router.record_learner_pick`): parent offer, the picked candidate, no
propensity, and in `detail_json` the offer policy's probability of the pick.
Taking the head writes nothing: that is the logged decision being served.

### Staged P2 decisions (`staged_p2`)

`controller_cutover.staged_next_action` logs each live staged decision for a
staged-owned run: `continue_current` (the run's canonical successor), the ten
§4.2 ladder rungs with `staged_eligible`, `fired` (the ladder's first eligible
rung) and `reversible` (§7.1: terminal assessment, depth edge and model
expansion are not), the within-block feasible items with their rank and the
legacy comparator's priority, and `stop_for_today`; exclusions grouped by
constraint key (ownership refusals counted). The served choice is
`continue_current` when the canonical successor stands, `stop_for_today` on a
staged veto, the block for a short-circuited explicit choice (logged as a
learner pick). Nothing on this path is drawn, so the propensity is
`deterministic`, unless a within-block EVSI tie-break was randomized, whose
assignment propensity is then logged (`epsilon_tiebreak`).
`staged_policy.ladder_eligibility` reports the rungs; it changes no decision.

### The serving change: probe near-ties (`mvp-0.12`)

`_exploration_support` is now the one gate for both the logged design
probability and the draw. Below `mvp-0.12`, or with
`router.probe_tie_admission = false`, it keeps the predecessor's probe
exclusion exactly. At `mvp-0.12` with the switch on, PROBE-intent candidates
(in-episode diagnostic probes **and teach-back items**, which share that
intent in `_intent_for_item`) are ordinary near-ties: a PROBE-intent best can
be displaced with probability `rate`, and PROBE-intent items within the reward
window share it as alternatives. Nothing else in the queue changed.

### Outcomes (`router_outcomes`)

`learnloop.router.outcomes.derive_router_outcomes`, from the ledgers only:

- **Action.** An offer's head is taken when an attempt is bound to its
  scheduler candidate; a learner pick's when an attempt is bound to the
  picked candidate; a staged decision's when its item is attempted at or after
  the decision in its session. Untaken: `overridden` (a learner pick of the
  same offer), `superseded` (a later decision in the session), else `open`.
- **R_next**: the first later attempt on the decision's LO that is fresh (a
  different item), unassisted (no hints, not primed), independent
  (independent / don't-know / diagnostic probe / open text / exam attempt;
  human origin), with a scorable resolved grade (PF-c nothing-assessed
  excluded): the outcome contract's `retention_exclusions` minus its delay
  rules.
- **R_cold**: the first later attempt on the LO at least one day after the
  last exposure to it, where an exposure is any attempt on it or any reveal on
  the item or the LO (`reveal_events`), in a different session from that last
  attempt, and unassisted as above.
- **S** = 0.75 R_cold + 0.25 R_next when both are observed (`final`); one
  observed is `provisional` (R_next while R_cold is pending); none is
  `pending`. A pending outcome is right-censored at `observed_through` (the
  newest attempt in the ledger), never a failure. Skip reasons are counted in
  `detail_json`.

### Configuration, upgrade, CLI

- `[router]`: `log_decisions = true` (logging, every version, not a serving
  change) and `probe_tie_admission = true` (the `mvp-0.12` kill switch).
  Modelled defaults, not in the 80-line decision-only template.
- `upgrade_to_mvp012` accepts `mvp-0.11` and chains from `mvp-0.9`/`mvp-0.10`
  through `upgrade_to_mvp011`; it freezes the `mvp-0.11` manifest, rebuilds the
  unchanged projection and renames the config atomically. `learnloop upgrade`
  now targets `mvp-0.12` by default. New vaults stay at `mvp-0.9`.
- `learnloop router log --vault <v> [--limit N] [--candidates] [--json]`:
  read-only listing of the newest decisions with outcomes derived on the fly.

## Deviations and decisions

1. **The spec's line numbers.** `scheduler.py:1544-1551` predate later edits;
   the exclusion lived in `_selection_propensities` and
   `_apply_seeded_exploration` (two copies). Both now read one
   `_exploration_support`.
2. **PROBE intent includes teach-backs.** Closing the exclusion as written
   admits every PROBE-intent candidate, which includes teach-back items. On
   the `linear_algebra` copy that is the only effect (open question 1).
3. **"epsilon_tiebreak" is the Today queue's own seeded exploration**, logged
   under that design name with its mechanism in `detail_json.exploration`. It
   is not rerouted through `randomization_layer.epsilon_tiebreak`: that design
   (uniform over a 5 % relative tie set) would change non-probe serving too.
   The draw is a deterministic hash of (session, UTC date, candidate ids), so
   logging it with the offer rather than before it changes nothing; note that
   repeated offers with the same candidates in one session-day share a draw.
4. **The chosen candidate is Today's head, not `queue[0]`.** Today groups the
   offer into sections, so a probe or "later" item at the front of the queue
   does not head the offer while a due item exists. The propensity is of the
   served head; `exploration_propensity` keeps the pre-composition draw.
   Consequence: the probe-tie admission changes the served head only where
   PROBE-intent items compete inside the section that heads the offer (two
   in-episode probes with nothing due, or a due teach-back explored past the
   teach-back cap). It also changes which probe, if any, is committed as a
   presentation (`queue[0]`).
5. **Contrast-pair order is context, not draw.** Its coin is seeded per
   (session, pair), fixed before the decision; the propensity conditions on
   it. Recorded in the review, not enumerated.
6. **The staged P2 bridge has no production caller.** The desktop's
   `golden_path.advance` calls `GPR.advance` directly. R1 logs where the
   bridge decides (tests, cutover gates), so rows appear once it is wired;
   wiring it is a serving change and was not made (open question 2).
7. **Learner picks are binds.** Opening an item from the list does not reach
   the sidecar until a draft is saved or an answer submitted; the first bind
   is the pick. A teach-back reopened from a refreshed list rebinds its new
   candidate, which is logged as a pick from that offer.
8. **Staged eligibility on Today** is `not_evaluated_on_legacy_queue`: the
   staged policy does not run on Today's queue (it is shadow there).
9. **Candidate-set size.** On the `linear_algebra` copy an offer's
   `candidates_json` is 22.7 kB for 43 candidates; the same build's slate
   candidate rows hold 262 kB. Bulk exclusions are counts; nulls are omitted;
   head probabilities are rounded to 12 decimals in the list (the row keeps
   the chosen one at full precision).
10. **Teach-back readiness in the head rule** is probed once per offer, only
    when an outcome's offer contains a teach-back.

## Paid calls and spend

None. No model, decider or embedding call; no route; $0.00. Replay makes zero
model calls (`test_the_replayer_rebuilds_router_outcomes_deterministically_with_no_model_call`
forbids the client constructors and the Decider client).

## `judgment_ledger`

No writes: no LLM, verifier or owner verdict exists in R1.

## Migrations

`176_router_decisions.sql` (`router_decisions` RAW_LEDGER, `router_outcomes`
DERIVED), classified in `db/table_roles.py`; the replayer is registered and
validated. Head fixture `migration_head_175` → `migration_head_176` (only 176
applied, `wal_checkpoint(TRUNCATE)`, `journal_mode=DELETE`, integrity ok,
FK-clean); README and the hard-coded paths (7 tests, 2 scripts, `SCHEMA_HEAD`)
updated. References regenerated: schema 176, 293 table notes, 632 config
leaves in 37 sections, 0 errors; `validate_vault.py` passes. Expect
renumbering at merge (T1 takes 176; the stuck prompt 177-178; DL1 also
claims a number).

## Manual runs (backup-API copies under `fixtures-local/`)

Copies `r1-linear_algebra`, `r1-probability`, `r1-arxiv_v2` of the worktree's
tracked fixtures (`copy_tree_with_databases`; the tracked vaults stay clean in
`git status`). Each: `doctor --fix-state` (pre-existing issues only),
`upgrade --to mvp-0.9`, `upgrade --to mvp-0.11`, two `rebuild-derived-state`.

**Shadow rebuilds** (mastery / facet / schedule rows changed, semantic
changes in brackets; live database hash unchanged in every run):

| Run | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| Same version (`mvp-0.11`) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| Candidate `mvp-0.12` | 21 / 79 / 0 [0] | 18 / 2 / 0 [0] | 34 / 6 / 0 [0] |
| Candidate `mvp-0.12`, switch off | 21 / 79 / 0 [0] | 18 / 2 / 0 [0] | 34 / 6 / 0 [0] |
| After `learnloop upgrade` (default target) then `rebuild-derived-state`, same version | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

The candidate rows differ only in their `algorithm_version` tag: the
projection is unchanged. Right after the upgrade (before the rebuild) the
same-version shadow reports the per-LO mastery tags (21/18/34), as Phase 6
recorded for its upgrade.

**Queue comparison** (the shadow rebuild compares projections, not serving,
so serving is compared directly): 60 seeded sessions, one fixed clock,
`persist_explanations=False`, items, priorities and every component:

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| Considered candidates | 41 | 67 | 32 |
| Exploration outcomes per offer | 22 | 1 | 3 |
| Sessions with a PROBE-intent candidate in the tie set | 60 | 0 | 0 |
| Sessions where `mvp-0.12` serves differently from `mvp-0.11` | 5 | 0 | 0 |
| Sessions where `mvp-0.12` with the switch off differs | 0 | 0 | 0 |

Every difference has a PROBE-intent candidate in the tie set (asserted). On
`linear_algebra` the PROBE-intent candidates are teach-backs: the served head
gains one teach-back alternative (probability 0.48 % per offer when the
teach-back provider is ready; 0 when it is not). The offer trace costs about
0.2 ms per build (5.4 vs 5.6 ms untraced/traced on `linear_algebra`).

### A sample logged decision

`fixtures-local/r1-linear_algebra` at `mvp-0.12`, one offer through the
sidecar's own `publish_offer` (no SidecarContext, so no startup maintenance,
no post-attempt worker; model clients forbidden; the teach-back provider
treated as unavailable), then a draft bound to the second item. Columns
(NULL R2 columns omitted):

```json
{
 "id": "01M4S39R7KK7X9646A82T80J4J",
 "receipt_key": "today_offer:01M4S39R62RCY61RCQAZS5BTZP",
 "decision_kind": "today_offer",
 "surface": "desktop_queue",
 "mode": "legacy_queue",
 "policy": "composed_offer_v2",
 "algorithm_version": "mvp-0.12",
 "log_version": "router_decisions_v1",
 "session_id": "01M4S39QXMT6W43N7FAYA8929S",
 "scheduler_slate_id": "01M4S39R62RCY61RCQAZS5BTZP",
 "snapshot_hash": "7a1fa512132f6396b91454f113c83ce0f02674c2e112e2cc6277787085d40b09",
 "design": "epsilon_tiebreak",
 "seed": "8d92dd319b053aff38e1e77e17f96fda",
 "candidate_count": 43,
 "chosen_ref": "pi_what_makes_function_axiom_strategy",
 "chosen_practice_item_id": "pi_what_makes_function_axiom_strategy",
 "chosen_learning_object_id": "lo_what_makes_a_vector_space",
 "chosen_scheduler_candidate_id": "01M4S39R638MBWBSYCHBFYHD39",
 "propensity": 0.957142857142857,
 "propensity_kind": "exact",
 "learner_pick": 0,
 "cost_usd": 0.0,
 "created_at": "2026-10-12T22:21:28Z"
}
```

The head's propensity is 0.957, not the draw's 0.9: of the 21 near-ties the
draw can move to the front, 12 are "later" items or teach-backs that cannot
head an offer with a due item first, so those draws still serve the head
(0.9 + 12 × 0.1/21); the other 9 each head with 0.1/21.
Five of the 43 candidates (`candidates_json`):

```json
[
 {"ref": "pi_what_makes_function_axiom_strategy", "kind": "item", "learning_object_id": "lo_what_makes_a_vector_space",
  "practice_mode": "constructed_response", "feasible": true, "section": "due", "considered_rank": 1, "offered_rank": 1,
  "planner": {"intent": "repair", "priority": 0.418705, "legacy_priority": 0.418705, "selection_reward": 0.423444,
              "signals": {"boundary_target": 0.069775, "forgetting_risk": 0.418699,
                          "predicted_correctness": 0.675622, "recent_error": 1.2e-05}},
  "exploration_propensity": 0.9, "propensity": 0.957142857143, "scheduler_candidate_id": "01M4S39R638MBWBSYCHBFYHD39"},
 {"ref": "pi_what_makes_structure_interpret_01", "kind": "item", "section": "due", "considered_rank": 2, "offered_rank": 2,
  "planner": {"intent": "repair", "priority": 0.300649, "selection_reward": 0.423444, "...": "..."},
  "exploration_propensity": 0.004762, "propensity": 0.004761904762, "scheduler_candidate_id": "01M4S39R638MBWBSYCHBFYHD3B"},
 {"ref": "pi_what_makes_test_strategy_01", "kind": "item", "section": "later", "considered_rank": 3, "offered_rank": 3,
  "planner": {"intent": "repair", "priority": 0.069775, "selection_reward": 0.423444, "...": "..."},
  "exploration_propensity": 0.004762, "propensity": 0.0},
 {"ref": "pi_coordinates_require_a_basis_teach_back_1xwm7p", "kind": "item", "practice_mode": "teach_back",
  "section": "due", "planner": {"intent": "probe", "priority": 0.306267, "selection_reward": 0.328846, "...": "..."},
  "exploration_propensity": 0.004762, "propensity": 0.0},
 {"ref": "stop_for_today", "kind": "stop", "feasible": true, "propensity": 0.0}
]
```

The teach-back has no ranks: the session cap drops it in the realized offer;
it is a candidate because exploring it (admitted at `mvp-0.12`) would keep it
past the cap. Its head probability is 0 here only because the sample treats
the teach-back provider as down. `exclusions_json`:

```json
{"counts": {"inactive_state": 1, "retired": 40},
 "named": {"reserved_exam": ["pi_axiom_commutative_recall_02", "pi_axiom_sequence_audit_plan", "... 13 more"],
           "teach_back_provider_unready": ["pi_compute_with_complex_numbers_teach_back_ya8r73"],
           "teach_back_session_cap": ["pi_coordinates_require_a_basis_teach_back_1xwm7p",
                                      "pi_orient_to_the_vector_space_idea_teach_back_phcbsn"]}}
```

`detail_json` (lists shortened):

```json
{"built_at": "2026-10-12T22:21:28Z",
 "exploration": {"mechanism": "scheduler.seeded_exploration", "rate": 0.1, "reward_window": 0.15,
                 "probe_ties_admitted": true, "best_item_id": "pi_what_makes_function_axiom_strategy",
                 "alternative_item_ids": ["pi_what_makes_structure_interpret_01", "pi_what_makes_test_strategy_01", "... 19 more"],
                 "roll": 0.6340393619682549, "choice": 0.3740564570916089, "realized_item_id": null,
                 "seed": "8d92dd319b053aff38e1e77e17f96fda"},
 "head_distribution": {"pi_what_makes_function_axiom_strategy": 0.957142857142857,
                       "pi_axiom_addition_integer_difference": 0.004761904761904762, "...": "10 heads in all"},
 "outcome_count": 22, "offered_count": 40, "limit": null, "pinned_item_id": null, "in_progress": null,
 "probe_block_reason": null, "placement_active": true,
 "staged_eligibility": "not_evaluated_on_legacy_queue"}
```

The learner pick it produced:

```json
{"decision_kind": "learner_pick", "surface": "desktop_practice", "policy": "learner",
 "parent_decision_id": "01M4S39R7KK7X9646A82T80J4J", "scheduler_slate_id": "01M4S39R62RCY61RCQAZS5BTZP",
 "chosen_ref": "pi_what_makes_structure_interpret_01", "chosen_scheduler_candidate_id": "01M4S39R638MBWBSYCHBFYHD3B",
 "propensity": null, "propensity_kind": "none", "learner_pick": 1,
 "detail_json": {"offer_probability_of_pick": 0.004761904762, "overrode_ref": "pi_what_makes_function_axiom_strategy",
                 "overrode_scheduler_candidate_id": "01M4S39R638MBWBSYCHBFYHD39",
                 "submission_id": "r1-sample-01M4S39QXMT6W43N7FAYA8929S"}}
```

`learnloop router log` shows the offer as `overridden` and the pick as
`open` with every outcome `pending` (no attempt yet; censored at the copy's
newest attempt, 2026-07-28).

## Where DL1's plan decisions should log

DL1 (`daily-loop/dl1`) builds its pool with `build_due_queue` but publishes
no offer from it (its review F5), so R1's `today_offer` rows never describe a
plan block, and the full list Today still shows (L3 picks) keeps logging
through `get_today_queue`. The plan's own decisions should log at:

- `daily_plan/engine.py::_boundary`, after `decide()` and inside
  `_persist_block`'s transaction: one row per block boundary with a new
  `decision_kind` (say `plan_block`; the CHECK needs the value at merge),
  `mode = staged`/`plan`, candidates = `decide()`'s feasible block candidates
  (candidate id, lane, minutes, item ids) plus `continue_current` and
  `stop_for_today`, the chooser's `BlockChoice` as the chosen candidate with
  its `propensity` (`lane_quota_v1` is deterministic, so 1), `chosen_by =
  learner` as `learner_pick`, and `Decision.fallback_from` in `fallback`;
- the plan's `item_served` path (`_item_step`), which serves within a block:
  within-block selection is P4 §4.4's transparent selector, so only the block
  boundary is a router decision; item serves join outcomes through their
  `scheduler_candidate_id`.

`router.decisions.record_decision` and the store's insert are reusable as is.

## Tests

| File | Covers |
|---|---|
| `tests/test_router_offer_log.py` (15) | Offer row: candidates, served head, exact propensity summing to 1 with stop, design and seed, slate link, one row per published offer, append-only triggers; no session, no row; switch off writes nothing and serves the same; a logging failure never fails the offer; an empty offer is a deterministic stop; skip requeue; learner pick (no propensity, parent, offer probability) and taking the head is not a pick; a draft is the continue candidate; placement exclusions and components; **exactness**: forcing each outcome of the draw rebuilds exactly that outcome's composed offer, and the goal quota undoing an explored non-goal item is inside the propensity; a draw composition always undoes is deterministic; a committed presentation is the continue choice; a recomposition mismatch is refused |
| `tests/test_router_probe_ties.py` (10) | The gate needs the successor and the switch; predecessor and switch-off keep the exclusion exactly; both directions admitted at `mvp-0.12`; the draw displaces a probe only at the successor; end to end, two in-episode probes: deterministic at `mvp-0.11`, 0.8/0.2 with a logged exact propensity at `mvp-0.12`; switch-off serves the predecessor's probe offer exactly; without PROBE-intent candidates `mvp-0.12` (on or off) serves exactly as `mvp-0.11` |
| `tests/test_router_staged_p2.py` (9) | Live staged decision: continue chosen, ten rungs with eligibility and the ladder's pick, irreversible rungs, deterministic; a retried bridge call logs once; a veto is the stop it served; legacy authority and the switch write nothing; a logging failure never changes the decision; explicit choice is a learner pick and continuation is continue; a randomized within-block choice logs its assignment propensity |
| `tests/test_router_outcomes.py` (9) | R_next fresh/unassisted with skip reasons; R_cold needs a day since the last exposure including a reveal; final S; same session, primed, non-independent and simulator answers are never cold; PF-c nothing-assessed is never an outcome; pending is right-censored; open / superseded / overridden / not applicable; a learner pick's outcome; a staged decision's action; the replayer is deterministic over two rebuilds with model constructors forbidden; durability lane under production pragmas |
| `tests/test_mvp012_upgrade.py` (8) | Version sets; each version activates exactly its features; upgrade from `mvp-0.11` and chained from `mvp-0.9`; refusals and idempotence; CLI default; defaults fingerprint; head-fixture path (upgrade, FK, doctor, idempotent rebuild including `router_outcomes`) |

Changed existing tests: `test_mvp011_upgrade.py` (LATEST and the version sets
now include `mvp-0.12`; the CLI-default test reaches `mvp-0.11` explicitly),
`test_mvp09_upgrade.py` (comment), `test_rebuild_orchestrator.py` (a stale
`router_outcomes` row is cleared), `test_architecture.py` (SQL owner),
`test_mobile_allowlist.py` (R1's extended RPCs pinned desktop-only:
`get_today_queue`, `skip_practice_item`, `save_practice_draft`,
`submit_attempt`, `submit_dont_know`, `start_teach_back`; R1 adds no RPC), the
head-fixture paths, and the CLI help snapshot.

## Files touched

- Added: `migrations/176_router_decisions.sql`, `src/learnloop/router/`
  (`__init__.py`, `decisions.py`, `outcomes.py`),
  `src/learnloop/db/stores/router.py`, `src/learnloop/cli/router.py`, the five
  test files above, this review.
- Changed: `algorithm_versions.py`, `config/schema.py`, `config/template.py`,
  `ops/vault_upgrade.py`, `cli/app.py`, `cli/__init__.py`,
  `db/table_roles.py`, `db/stores/collection.py`,
  `scheduling/scheduler.py`, `scheduling/staged_policy.py`,
  `scheduling/controller_cutover.py`, `substrate/rebuild_orchestrator.py`,
  sidecar `handlers/queue.py`, `handlers/practice.py`,
  `handlers/serializers.py`, `handlers/teach_back.py`, `pyproject.toml`
  (contract `router-log-is-a-leaf`; `learnloop.router` added to the
  infrastructure and G7 contracts), the head fixture, the reference scripts and
  generated references, the Version Registry and the algorithm-versions note.
- No frontend change.

## Owner-run commands

Run on a backup-API copy first, then on the live vault when satisfied (never
on the tracked fixtures from an agent):

```bash
# Upgrade to the probe-tie successor (from mvp-0.11, or chained from mvp-0.9/0.10),
# then optionally retag the per-LO mastery rows:
uv run learnloop upgrade --vault "$VAULT"
uv run learnloop rebuild-derived-state --vault "$VAULT"

# Check the successor changes nothing in the projection (expect 0/0/0):
uv run learnloop rebuild --shadow --json --vault "$VAULT"

# After some practice: the newest logged decisions and their outcomes (read-only):
uv run learnloop router log --vault "$VAULT" --limit 20
uv run learnloop router log --vault "$VAULT" --limit 1 --candidates --json

# Kill switches (add to the vault's learnloop.toml):
#   [router]
#   probe_tie_admission = false   # serve exactly as mvp-0.11
#   log_decisions = false         # stop writing router decisions (no serving effect)
```

## Open questions

1. **Teach-backs in the tie-break.** Closing the PROBE-intent exclusion
   admits teach-backs as well as in-episode diagnostic probes; on
   `linear_algebra` that is the only effect (one due teach-back alternative,
   about 0.5 % of offers). Narrowing it to diagnostic probes is a one-line
   gate (`practice_mode != "teach_back"`).
2. **Wire the staged P2 bridge?** `golden_path.advance` bypasses
   `advance_live`, so the staged P2 path makes no live decision today. Routing
   the desktop through the bridge is a serving change (the staged policy could
   veto a transition); it belongs with R2's cutover unless wanted sooner.
3. **Field serving propensity.** `facet_outcome_observations.serving_propensity`
   is still NULL ("no verified kind exists yet"). R1's offer rows are that
   verified kind; joining them (the attempt's candidate → its offer's head
   probability) is a DERIVED change for the field owner.
4. **R_cold definition.** R_cold here is a delayed retrieval under the reveal
   ledger (a day since any exposure to the LO), not a certified cold
   measurement from `coldness_receipts` (those exist only for the repair and
   certification lanes). Confirm before R3 reads S.
5. **Repeated offers share a draw.** The seeded exploration is a hash of
   (session, date, candidates), so refreshes with the same candidates in one
   session-day repeat the outcome; R3's variance estimates should cluster by
   session-day.
