# The probe router (refactor G2's behaviour step): the router decides whether a probe is asked

Branch `refactor/g2-router-probes`, on main with the inline checks merged (latest tag on main `mvp-0.69`). The design is
[`refactor-g2-design.md`](refactor-g2-design.md) (its §1 lettered sites A to K, its §2c table of what goes, its §2d
learner-lane shape); steps 1 to 5 are [`refactor-g2a.md`](refactor-g2a.md) and [`refactor-g2b.md`](refactor-g2b.md).
Its tag is `PROBE_ROUTER_ALGORITHM_VERSION`, one constant in `learnloop.algorithm_versions`: `mvp-0.70` on the branch.
L4-2, also being built, was promised `mvp-0.70`; whichever lands second takes the next tag, a renumber of that one
line with the goldens, pins and chain-position assertions regenerated. No kill switch (owner rule 2026-11-16), no
migration, no config key, no prompt change and no model call of its own.

**Status: both slices built on the branch; they land together.** The design's rule is that the router's authority is
transferred whole. Slice 1 moved the automatic follow-up lane (FG1) to the router. Slice 2 moves the learner's repair
lane to the router and removes the downstream worth gates for router-selected probes.

| Commit | Slice | What |
|---|---|---|
| `3df902ef83` | 1, tests first | `tests/test_probe_router.py`; fails on import |
| `63d18eb791` | 1 | The tag: one constant, the chain entry, its set and predicate, one upgrade row, one test row; the nine pins and the effective defaults by the tag string |
| `adf1fa4479` | 1 | The automatic lane: an unwritten probe is no option of either policy; the probe coin asks it at the stop coin's rate |
| `73cf2cde0d` | 1 | FG1's tests build at the predecessor; slice 1's record; `stop_coin`'s doc says it prices two arms |
| `fb760d5d93`, `4252ef9af8` | 1 | Merge of main (the inline checks, `mvp-0.69`); the renumber to `mvp-0.70` |
| `ef20a2f136` | 1 | Comments name decisions, not rulings |
| `e6c31f4553` | 2, tests first | `tests/test_probe_router_learner_lane.py`; fails on import |
| `1b2bed5d2c` | 2 | The learner lane: the repair status reads facts; the router's one decision per factor |
| `6de6a45841` | 2, tests first | `tests/test_probe_router_worth_gates.py` (the sentinel journey) and `diagnosis/probe_authority.py`; fails at the block's continuation by value |
| `bcec1da1f3` | 2 | The worth gates H to K step aside for a router-selected probe, by origin, at the tag |
| `d32f299ccc` | 2 | The feedback surface's DTO carries the router's disposition |
| `d0a683ead1` | 2 | `tests/test_probe_router_replay.py`: the same history rebuilds to the same rows at both tags |
| `d7e6c0d66c` | 2 | `scripts/probe_router_copy_counts.py` and its test |
| `e435d5ec32` | 2 | This record (amended in the last commits) |
| `c7c57caec0` | 2 | No new import cycle: the payload builder moves to `daily_plan.learner_probe`, the episode predicate to `probe_episodes`; the scheduler's line ratchet raised |
| `d9c82ccb3c` | 2 | The scheduler reads the router's episodes through its module-level `probe_episodes` import |

## The owner's decisions this records

- **2026-11-20, G2 option f** ("Option 1 plus a small randomized share of probes"):
  - an unwritten probe earns no information credit (design decision 1, the conservative value);
  - a covering repair uses the cause-class slopes and an uncovered one is priced as practice (decision 2);
  - no room to wait does not force a probe (decision 3);
  - a small, logged, randomized share of eligible misses still asks the probe, so the data that would teach the
    router to value probes keeps arriving.
- **2026-11-23, the share's size:** "derive it from an existing randomized arm's rate" (no new constant).
- **Applied by the orchestrator, 2026-11-23:** the share is the stop coin's rate, `router_objective.stop_coin`, read
  through one function (`router_objective.probe_coin.share`).
  - The stop coin is the same mechanism: a coin beside the mix, its own uniform, an exact served distribution, an
    assignment row.
  - It is the same family: the `mvp-0.48` arms, each a declared price for information on an action the policies value
    below another. At 0.05 it is small.
  - **One config field now prices two arms:** changing `stop_coin` moves the probe share with it, and 0 turns both
    off. The field's own documentation says so.
  - Alternative kept: `router_objective.pick_open_share` (0.1). The closer subject (learning about a miss's causes),
    but another mechanism (it acts on a misconception pick, not a draw) and twice the learner minutes.
  - Alternative kept: `router.epsilon_min` (0.02), the mixture's per-option floor. The probe would stay in the support
    with only the floor's mass, which needs it removed from both policies' components and kept in the uniform branch
    (a change to the mix's structure and record), and it is very small.
- **Decisions 1 to 3 as the evaluator reads them:** the learner lane values with
  `daily_plan.learner_probe.OWNER_DECISIONS`, the design's recommendations marked "decided by the owner 2026-11-20
  (option f)" in every valuation record.

The randomized arms in force when the choice was made (all fixed config values, none learned):

- the stop coin (0.05 each way);
- the randomized cold check (one a day, embedded);
- the open misconception pick (0.1);
- the two policies' minimum shares (0.1 each; the weight itself is learned);
- the mixture's floor `router.epsilon_min` (0.02);
- AD's dose arm (D21, 0.10, at most three offers a day) and its overlap share (0.10);
- the legacy queue's near-tie exploration (0.1);
- as display or card ablations rather than action arms: the similar-decisions inclusion (0.5) and the Reader cue
  holdout (0.1).

## What changes at the tag

### The automatic lane (slice 1)

| | Below the tag (the predecessor) | At the tag |
|---|---|---|
| The mix's support after a miss with rival causes, on a plan | ask now, wait, no intervention (and a lesson when offered) | no intervention, and a lesson when offered: the unwritten probe is no option of either policy, now or after the block |
| No lesson offered | a draw over the three arms | nothing for a policy to choose: no model is asked |
| No room to wait | the probe asked now, deterministically (`no_room_to_wait`) | as any other boundary: waiting is never an option, the coin decides the probe |
| No plan, or the router switched off | the probe asked now, deterministically, no router row (`no_plan`, `router_off`) | the coin decides; the decision is logged (`probe_coin_no_plan`, `probe_coin_router_off`), plan fields null |
| The probe coin | none | `ask_probe` at `r`, `policy` at `1 − r`; its own seed (`probe_coin.seed_for`), its own uniform, its own assignment row (`g2_probe_coin:v1`) |
| The logged propensities | the mix's `μ` | the served distribution, exactly: `P(probe) = r`, `P(a) = (1 − r)·μ(a)`; the mix's `μ` is beside it (`mix_pi`) |
| Hard refusals (Not now, pending machine checks, a measured foreign episode) | first | first, unchanged |

The coin and the stop coin are independent draws:

- different seed functions (the stop coin's uniform comes from the decision's mix seed, the probe coin's from its own);
- different stages, experiment ids and rows.

They never meet in one decision: the stop coin applies at a block boundary with stop in the support, the probe coin
after a miss. Each decision's served distribution is exact on its own. In tests the probe coin's seed is pinned as its
own family (`tests/pinned_draws.py`).

### The learner's lane (slice 2)

Below the tag the feedback screen's status read (`causal_repair_status`) runs the causal gate (`decide_probe`):
thresholds on separability and action change, avoided minutes against the burden plus a margin, a recent-diagnostic
count and a session budget. Each read writes a new receipt, so a remounted panel is a second verdict.

At the tag:

- **The status read is a read of facts** (`causal_orchestrator._routed`). It forms no worth verdict. A reread of the
  same facts writes no new receipt (`insert_causal_probe_decision_receipt(once=True)`: the factor's latest receipt is
  returned when its fingerprint is the same). The receipt's decision is `router_decides`. The predecessor's
  recent-burden and session-budget defers and its value thresholds are gone; their inputs stay on the receipt as facts.
- **The facts settle what they settle**, each as the predecessor's status, with `router_state: unavailable` and
  `hard_stop_reasons`:
  - one repair covers the causes, or every cause needs the same repair (`common_repair_covers`, `same_repair_class`);
  - pending machine checks;
  - the learner's "Not now" (the offer withdrawn, Teach me now left) or "Teach me now" (the repair starts);
  - no reviewed executable instrument (`blocked_pending_review`, as before);
  - another episode on the learning object has already measured.
- **Otherwise the router decides, once per factor** (`daily_plan.learner_probe`):
  - The row is a `plan_interrupt` on the `causal_repair` surface, receipt key `plan_interrupt:learner_probe:<factor>`.
    Every later read, the repair entry and the offer read it back. Nothing is redrawn.
  - The probe is priced by `diagnostic_value.evaluate_probe` with the existing instrument's channel
    (`learner_probe.diagnostic_payload`). The channel is the instrument's composed `P(outcome | hypothesis)`
    through the slot mapping the episode's own valuation reads. Every locked hypothesis keeps its row, the open arm
    included; a hypothesis without a row makes the channel missing.
  - The valuation reads the vault's frozen objective inputs (`objective_inputs.build`) with no plan, and the day's
    price (`day_price`, read-only).
  - **Learned** (information value above zero at the learned slopes): the probe is an option of the mix. The numeric
    policy's choice goes in. The LLM policy is not asked on this lane (no card exists for it, and no prompt changes);
    its share goes where a failed policy's goes. The exploration floor stays. The served option and its exact `μ` are
    logged.
  - **Unlearned** (no information, a missing channel, or no valuation): the mix has one option (no probe). The same
    probe coin as the automatic lane's offers the probe on its share, with its own seed (`learner_probe:<factor>`
    boundary), its own assignment row, and the served distribution logged exactly.
- **The status after the decision:**
  - `selected`: `needs_disambiguation` with the three actions (Take the quick check, Teach me now, Not now);
  - `not_selected`: `started` (the repair goes on without the check);
  - `pending` (no decision yet, for a caller with no router): the offer withheld, Teach me now left.
- **The payload** gains `router_state`, `router_decision_id` and `hard_stop_reasons`, present only at the tag.
- **The sidecar decides first.** `causal_repair_status` and `start_remediation` make the router's decision before
  reading the status, so the repair entry holds only on the router's selection. A diagnosis-only caller with no router
  (`guided_redo`'s repair start) is never held on a decision nobody made: the repair starts.
- **The offer.** `causal_probe_offer_action` accepts only the router's selection (`probe_offer.accept_routed_probe_offer`),
  with the learner's hard stops read again at acceptance. Anything else is `accepted: false` with
  `reason: router_decision_required` (or `learner_preference`) and the router's disposition. A request never makes a
  decision. The pin names the router's decision (`causal_probe.router_decision_id`).
- **The frontend.** `CausalRepairStatusDto` gains the three fields and the offer result its disposition. The panel is
  unchanged (its actions are the backend's), and the two refusals have a line each.

### The worth gates downstream (slice 2)

At the tag a probe whose presentation pins a router decision (`diagnosis/probe_authority.py`) is the router's whole
decision. This covers the automatic lane's asked probe and the learner lane's selected offer.

| Site | Below the tag, and for any other origin | A router-selected probe at the tag |
|---|---|---|
| G, the general follow-up's value suppression | values and suppresses | never meets it: the sentinel journey asks `_intervention_value` and it stays silent |
| H, the scheduler's admission | `probe_episode_decision` admits or withholds (`voi_stop`) | no value admission (`AdmissionReads.router_owned_episodes`); EIG still ranks |
| I, the serving door | vetoes a new presentation by value | no value veto for the episode's next instrument |
| J, a block's continuation | closes when the next observation does not pay | one question closes the block, as FG1's |
| K, completion | action equivalence, the robust gate and the value stop; value lifts the count | evidence and the count alone (budget, decision stable with breadth, the strong-claim fast path, the empty pool's park); the count binds |

## Playbook ruling and activation

The change alters persisted meaning: which probes are asked, offered and continued, and what the router's ledger
records for them. So a tag: `mvp-0.70`, the immediate successor of `mvp-0.69`, with no kill switch.

- `PROBE_ROUTER_ALGORITHM_VERSION`, `PROBE_ROUTER_VERSIONS`, the one predicate `probe_router_on(config)`.
- **`Link(mvp-0.70, idempotent_projection)`.** Only decisions made after the upgrade behave differently. Replay runs no
  decision policy, and no recorded decision, probe, observation, lock or episode is reinterpreted.
  `tests/test_probe_router_replay.py` settles it:
  - two histories recorded below the tag: an episode ended by its value stop, and a probe pinned with a router
    decision, answered, its block closed;
  - copies rebuilt whole at `mvp-0.69` and at `mvp-0.70` compare equal in every table once surrogate ids, timestamps
    and the tag string are set aside;
  - a second rebuild at the tag repeats the first;
  - `learnloop upgrade` activates with no derived row changed.
- `tests/test_upgrades.py`'s `EXPECTED_ACTIVATIONS` gained the row (slice 1).
- **A vault upgraded mid-episode** (corrected in the fix round, G2-R1): a probe pinned by a decision made below the
  tag keeps its predecessor gates after the upgrade. Authority is the pinned decision row's own: its
  `algorithm_version`, frozen when it was drawn, and a probe arm.

## Tests, pins and goldens

**Slice 1:**

- `tests/test_probe_router.py`, written first (it failed on import before the code). It covers:
  - the tag and its predicate, and the share's one function;
  - the exact served distribution, the coin's arms and assignment row, its own seed and experiment;
  - the plan with and without a lesson, no room to wait, a zero share;
  - the lane's logged decision and assignment, and no plan both ways;
  - below the tag, the predecessor's no-plan and no-room answers.
- FG1's fixtures (`tests/followup_serve_helpers.TAG`) build at the probe router's predecessor, computed from the
  chain, so a renumber needs no edit. Their subject is the lane as it asked its probe (the written question, its
  admission, serving and receipts). One test built at the head by name
  (`test_followup_codex_review::test_f6_a_crash_after_the_diagnosis_ended_is_recovered_by_next`) names that tag now:
  its recovered decision must ask the probe.
- Identity pins: nine move by the tag alone (A1-A4, C3.boundary, C3.boundary_offer, C3b.chooser, C3b.chooser_offer,
  C3b.start_key, C3b.start_key_offer, C5, C6). They were regenerated with the behaviour change and without it (the
  chain appended alone), giving the same file.
- After merging the inline checks (`mvp-0.69`) the tag is `mvp-0.70`:
  - the same nine pins moved again by the tag alone;
  - the journey golden and `tests/goldens/placement_stored_misses.json` moved by the tag string only;
  - the CLI surface's `upgrade --to` default;
  - the chain-position assertions of the successor tests the inline checks' landing bumped (one more step back for
    each named older tag, the head's literal one tag on).
- `tests/test_ih2_lessons_compete.py`'s switch-off case now builds at the predecessor, a new node id. The case pins
  its arm with the `draw` fixture (`draw.prefer = (INSERT_NOW,)` serves the probe whatever the uniforms), and its
  assertions read the decision's support and candidates, never the drawn arm. So the pinned seeds its node id now
  gets change nothing it checks (it passes).

**Slice 2:**

- `tests/test_probe_router_learner_lane.py` (16, written first; failed on import):
  - the facts read and the one decision (a reread draws nothing and writes no receipt);
  - an unlearned probe offered only by the coin, with its exact propensity and assignment row;
  - the valuation on the existing instrument's channel (`channel_use: channel`, information 0 at the seeded slopes);
  - a learned probe in the mix with no coin flipped;
  - a zero share;
  - the typed refusal of a stale offer (before any decision, and after a decision not to ask);
  - the selected probe accepted once with its pin naming the decision;
  - Not now after the selection; Teach me now;
  - the repair entry held only on the selection, and with no router behind it;
  - no executable instrument; one repair for both causes;
  - below the tag, the verdict and no router keys.
- `tests/test_probe_router_worth_gates.py` (4). The sentinel journey makes every legacy worth function raise (the
  causal verdict, the follow-up's value suppression, the episode value decision, the block's continuation by value,
  action equivalence, the robust gate, the value stop), then:
  - serves the router-selected probe through the sidecar;
  - answers it, and its block closes;
  - its episode stays in progress with the second instrument;
  - the scheduler builds with no value decision on it;
  - the serving door commits the second instrument.

  With the dispatch disabled it fails at the first gate it meets: the block's continuation by value
  (`_next_observation_does_not_pay`). The count binds and value decides nothing for a router-selected episode, another
  origin keeps its gates, and below the tag a pinned router decision dispatches nothing.
- `tests/test_probe_router_replay.py` (3) and `tests/test_probe_router_copy_counts.py` (2).
- **A guard this step changes, as the design says:** `tests/test_diagnostic_probe_value.py`'s
  `test_no_served_module_imports_the_evaluator` kept the successor evaluator unserved through steps 4 and 5 ("until the
  behaviour step wires it"; design §4, step 4 unserved, step 6 wires "the new evaluator"). It is now
  `test_only_the_routers_learner_lane_imports_the_evaluator`: exactly one served module, `daily_plan/learner_probe.py`,
  imports it, and every other module under `src` stays off it. The automatic lane needs no import (its unwritten probe
  is never valued). `diagnostic_value`'s docstring says so.
- **The attempt-facts census:** K9.13 (merged before the landing gate) moved the hinted-evidence weight's read of
  `hints_used` from `probe_episodes.episode_posterior` into `_gather_episode_evidence`; the census row names it.
- **Fixtures moved to the predecessor** (their subject is the causal gate's verdict, which the router replaces at the
  tag), with no assertion changed:
  - `tests/causal_orchestrator_helpers._vault` (a `version` parameter, the predecessor by default; it serves
    `test_causal_orchestrator.py`, `test_causal_repair_sidecar_rpcs.py`, the journeys' causal cases and four other
    files);
  - `tests/probe_router_authority_helpers.divergent_factor` (a `version` parameter);
  - `test_causal_p2_acceptance::test_causal_disambiguation_end_to_end_acceptance`.
- **The diagnosis journey golden:**
  - `causal_reread_and_request` differs only by the tag string (`mvp-0.70` to `mvp-0.69`, five lines); every other
    existing case is byte-identical;
  - two successor journeys at the tag, `router_learner_offered` and `router_learner_not_selected` (the status read,
    the reread, the repair entry, the offer accepted or refused), add 4,581 lines. That raises the `golden_json_lines`
    structure ratchet by the same number (`tests/goldens/structure.toml`).
  - The journeys' `_wall` sets aside the valuation's wall-clock keys (`ms`, `ms_act_now`, `ms_probe`).
- **Identity pins:** none moved in slice 2, and none was added. The learner lane's decision is a new row kind, not a
  hash, seed or manifest an existing pin covers. Its seeds go through `objective_seeds.numeric_seed`,
  `router_objective.mix.seed_for` and `probe_coin.seed_for`, each already a pinned family.
- **Effective defaults and the CLI surface:** unchanged in slice 2.
- **Structure ratchets:** `golden_json_lines` +4,581 (the two successor journeys, above);
  `src/learnloop/scheduling/scheduler.py` 4,428 to 4,442 (+14: which probing episodes the router owns, site H). The
  dispatch commit (`bcec1da1f3`) alone added an import edge from scheduling into diagnosis that the frozen-cycles
  contract refuses, and put the payload builder in a diagnosis import cycle; `c7c57caec0` removes both.

## What the orchestrator must run on owner copies

On backup-API copies (never a live vault), each at `mvp-0.69`, from the landed tip, with the scratch wrapper's
isolation. `scripts/probe_router_copy_counts.py` reads a copy read-only and prints counts only: no id, text or path.

1. `uv run python scripts/probe_router_copy_counts.py counts "$COPY" > before.json`. Expected:
   - `probe_router_on: false`;
   - no learner decisions;
   - no probe coin assignments;
   - the causal receipts by the predecessor's verbs;
   - `presentations_pinning_a_router_decision` as the automatic lane left them.
2. `learnloop rebuild --shadow --json --vault "$COPY"` at `mvp-0.69` (the baseline).
3. `learnloop upgrade --vault "$COPY" --to mvp-0.70`, then:
   - `learnloop doctor --vault "$COPY"`;
   - `PRAGMA integrity_check`;
   - `PRAGMA foreign_key_check`.
4. `... counts "$COPY" > after.json`, then `... compare before.json after.json`. Expected: only `algorithm_version`
   and `probe_router_on` move. The upgrade decides nothing and rewrites no receipt, decision or episode.
5. `learnloop rebuild --shadow --json` at `mvp-0.70`: 0, 0, 0 and no due date moved, apart from the rows'
   algorithm-tag stamp (an idempotent projection keeps live rows' stamp while the shadow stamps the new tag).
6. Verify the live databases' SHA-256 unchanged.

What the copies cannot show: a learner-lane decision is made only when a status is read, so a copy shows none until
the app reads one. The decision's latency on a real vault's inputs is the one number a copy could add. It needs a
status read on a copy with an open divergent factor and a reviewed instrument, through the sidecar, with the copy's
own config. Measured on the synthetic journey only (below).

## Judgment calls, to read first

1. **The repair classes still settle the learner lane's status** (one repair for every cause, or every cause needing
   the same repair). They read as the lane's existence fact, as the rival count (site A) is on the automatic lane:
   with no repair choice for an answer to change, the router has nothing to decide, and the common-repair card's
   receipts stay as they were. **The automatic lane is not symmetric:** its coin applies to every miss with two rivals,
   whatever their repair classes (slice 1, design site E: the class verdict is observational there). The owner may
   want one rule for both lanes.
2. **No executable instrument still holds the repair** (`blocked_pending_review`, as the predecessor). It is an
   executable-contract state, not a worth verdict, and Teach me now stays available. A measuring foreign episode holds
   it the same way.
3. **One decision per factor, forever.** A `not_selected` factor is never offered the quick check again on the learner
   lane (Not now, Teach me now and new facts change its status, not the decision). A later miss makes a new factor and
   a new decision. "A router no-intervention result is a decision for this boundary" (design §2d).
4. **The LLM policy is not asked on the learner lane.** The brief allows no prompt change, and no card exists for this
   lane. In the learned branch its share goes where a failed policy's goes (logged `not_asked_on_this_lane`), so a
   learned probe's `μ` is the numeric policy's one-hot plus the floor.
5. **The valuation runs synchronously in the status read.** On the journey's vault it valued 3 hypotheses, 6 results
   and 2 repairs in 15 rollouts. The day's price computes its gain curve when no plan decision has carried it today.
   Latency on a real vault is not measured (above).
6. **The learner lane's probe is priced unexposed.** Its instrument is not the missed item, and acceptance refuses an
   instrument whose answer was shown. The miss's own released feedback is not modelled as exposing the instrument.
7. **Continuation after a router-selected probe:**
   - its block is the one question;
   - its episode completes on evidence and its count (the count binds, since value no longer decides);
   - while instruments remain and no evidence rule ends it, the scheduler may serve the next one, ranked by EIG with
     no value admission.

   The design's "one continuation router decision" is **not built**: continuation within the count is the scheduler's
   ranking. Building it is a router decision per continuation, priced as the first; the owner should decide whether
   that is a follow-up.
8. **G needs no dispatch.** The general follow-up's value suppression never meets a router-selected probe: the probe
   is a committed presentation, and inside its block the follow-up hooks are deferred. The sentinel journey proves it
   by making `_intervention_value` raise.
9. **A durable misconception's status read still writes its `start_durable_repair` receipt per read** (unchanged at
   the tag). It is not a probe decision; the common-repair card reads it.
10. **The learner-lane facts are read twice on the first read** (the status before the decision, then after). The
    second writes nothing (the same facts, the same receipt).

## Limitations

- The learned branch is covered with a stand-in valuation (information 0.5, the probe chosen); no real vault has a
  learned `γ_gap` above `γ` (`refactor-g2b.md` judgment call 2), so every real learner-lane decision today is unlearned
  and asked only by the coin.
- A selected probe whose instrument becomes unservable after the decision (its answer shown, its surface used) is still
  `selected`; acceptance refuses it with the predecessor's typed reason, and the status keeps offering it.
- An offer request names a factor; with two divergent factors on one miss each has its own decision.

## Fix round (the adversarial review of 2026-11-24)

Codex's review of the landed `1293ec6f96` found 4 blockers, 15 majors and 1 minor. Every finding was checked against
the code first. Each fixed one has a fail-first test in `tests/test_probe_router_decision_integrity.py` (shown failing
against main's files before the fix) and a ledger row G2-R1 to G2-R20 (`refactor-bug-ledger.md`).

**The tag.** The fixes ride on `mvp-0.70`; no successor is needed. The playbook mints a tag for a change to persisted
meaning so that a vault's history stays interpretable. No vault holds an `mvp-0.70` decision yet: the owner-copy run
showed the upgrade decides nothing, and no owner vault is upgraded. The precedent is the recorded `mvp-0.59`
amendments, made while every live vault was below the tag. A decision recorded at `mvp-0.70` before these fixes
exists only in test vaults. **If an owner vault is upgraded to `mvp-0.70` before this lands, these fixes become
`mvp-0.71` instead**, a renumber with an upgrade row (`idempotent_projection`; the replay test still holds).
No migration is needed.

| Finding | Disposition |
|---|---|
| 1 blocker: an upgrade changed an old pin's meaning | Fixed. `probe_authority.decision_owns` reads the pinned decision's row: its algorithm_version must be the probe router's and its arm a probe. The "vault upgraded mid-episode" paragraph above is corrected. |
| 2 blocker: the trace said lesson, the ledger said probe | Fixed. The follow-up gate's objective trace is written after the coin, with the served arm and its exact probability; the mix's draw (`drawn_chosen`) and `mu` sit beside them. |
| 3 blocker: another instrument under the original propensity | Fixed. The selected status and the acceptance use the decision's own candidate. A selection that can no longer be served is `void`, with no substitute. |
| 4 blocker: a probe served without its decision or assignment | Fixed on both lanes. Decision, assignment and binding commit together. On failure the automatic lane serves no intervention, never the probe and never in place of a drawn lesson. |
| 5: the old gate with the objective off | Fixed. The tag dispatches first, to the probe coin's logged fallback. |
| 6: a stale click past a hard stop | Fixed at acceptance (the whole status is read again). **Open:** retiring a pin whose learner refused after pinning, at the first display door. |
| 7: an abandoned pin's authority | Fixed for ownership (only a pin that still stands). **Open:** reserving an accepted learner pin against a scheduler refresh. |
| 8, 9: zero-EIG admission and the missing continuation decision | **Open, one fix:** one router decision per next observation (stop among its options), consumed by block release, scheduler and item-open and pinned on the next presentation; eligibility carried apart from EIG in admission and precommit. Until then, a router-owned episode's continuation is the scheduler's EIG ranking within the count (judgment call 7). |
| 10: completion lost its stops | Fixed (ownership read once from the episode). The second part, a stable breadth-short episode returning with an empty pool, is the predecessor's own path for every origin, so not a G2 defect. |
| 11: two opportunities on one factor | **Open:** the learner lane should read the automatic lane's decision on the same factor and reuse it. Common repair is still decided per lane (judgment call 1). |
| 12: the feedback screen sends no factor | **Open:** carry the factor through status, decision and Teach me now (frontend and RPC). |
| 13: an unservable candidate drawn over | Fixed. `candidate_unservable` (the item is in the vault, its surface was never answered) is checked before any draw and again on reread. An answer shown on a routine display stays the acceptance's own refusal. |
| 14: exposure always false | **Open:** compute known exposure at the decision with the answer admission's own scope. |
| 15: the valuation could not be replayed | Fixed. The chooser's rollout options are used, and the unrounded inputs, payload, seed, draws and options are frozen on the decision. A replay from the record alone is not yet tested. |
| 16: one fallback duration for every repair | Fixed. Each class uses its own estimate, with its source. |
| 17: an outcome credited to a declined offer | Fixed in part: a learner row names no item until an acceptance's pin binds one. A common outcome target for both arms is open. |
| 18: one stored decision, two draws | Fixed. Seeds come from the factor. A receipt is reused only for the same status and candidate. The router's read before it decides records no receipt. |
| 19: valuation on the serial request loop | **Open:** a resumable per-factor job, with the status pending while it runs. |
| 20 minor: a tiny share logged as deterministic | Fixed. |

Assertions changed (each by a fix):

- The learner lane's coin seed is the factor's (R18).
- A selected row's `chosen_practice_item_id` is None (R17).
- The sentinel tests' predicates take the repository and a real decision id (R1).

The diagnosis journey golden moved for the two `router_learner_*` journeys only. The reasons are the frozen inputs,
the repairs' minutes and sources, the seeds, the `started` receipt of a not-selected read, and no item on the row.
That raises `golden_json_lines` by 944.

## Fix round 2

Branch `refactor/g2-fix-2`, cut from the first fix round's tip (`41ab8e5977`). It takes the findings the first round
left open. Each was checked against the code first and has a fail-first test in
`tests/test_probe_router_decision_integrity.py`, shown failing against the base's `src` before its fix (R3's test
against the base with the acceptance's named candidate removed, since round 1 had already fixed it).

**The tag.** As in round 1, the fixes ride on `mvp-0.70`: no stored shape changed and no vault holds a decision made at
`mvp-0.70`. Every new datum is a value in an existing column or a row in an existing table:

- the learner-lane decision's `detail_json` gains its exposure and a replay payload;
- its facts receipt's `inputs_json` gains the session the read was made in;
- the decision writes a `decision_objectives` row, and the measurement that row arranges, as the automatic lane's
  decisions already do;
- a retired pin ends `abandoned`, an existing end reason.

No migration. The one fix that needs one is R8 and R9's stop arm, and it is not built (below).

| Commit | Finding | What |
|---|---|---|
| `40446b6146` | R11, R12 | One probe decision per factor across lanes; the status, the decision and Teach me now are the shown factor's |
| `dca80ee8cb` | R14 | The probe priced exposed when the answer admission would refuse its answer |
| `e0500bfbd3` | R17 | Both arms freeze one outcome target and are measured on it |
| `b3c851f9c6` | R15 | A decision revalues from its stored row alone |
| `7d1c3ae713` | R3 | The missing test: a candidate ranking ahead at acceptance is never served |
| `e4e46b1039` | R6 | A pin refused after pinning is retired at its first display |
| `b9e749fa24` | R7 | An accepted learner-lane pin holds its episode |
| `975b4a3f8c` | R19, R12 | The valuation in a resumable job; the frontend carries the factor and reads a pending status again |
| `f6d6952848` | | The journey golden, the golden lines ratchet; comments name decisions, not review numbers |

| Finding | Disposition |
|---|---|
| 3 (its test) | Added. Candidate B, made to rank ahead of A after the decision, is never offered or pinned: the status keeps A, and acceptance pins A's item. |
| 6 (the display door) | Fixed. `probe_presentations.serve_presentation` is the one path to `served`. It retires an unshown learner-lane pin (`learner_refused_pin`: it names a router decision and no workflow) when the learner's current preference on its factor refuses ("Not now", "Teach me now", no more diagnostics; the status's scope). The pin ends `abandoned`, and the sidecar answers `learner_refused_probe`. Acceptance found no refusal, so one found here came after the pin. The repair entry now carries the session too. |
| 7 (the reservation) | Fixed. `eligible_instruments` reserves an episode for any standing router pin, not only a workflow's. No routine selection, dialogue or scheduler commit can supersede an accepted learner pin before it is answered, refused at its door, or ended. |
| 8, 9 | Planned here, then built with migration 273 once the orchestrator assigned it ("The continuation decision", below). |
| 11 | Fixed. `plan_log.automatic_probe_decision` reads the automatic lane's committed decision on the factor (its probe-lane workflow's decision; a hard refusal is no draw). The learner lane reuses it and flips no coin. Its status is `not_selected`, with `router_asked_on_automatic_lane` or `router_did_not_select_probe_on_automatic_lane`, and the automatic decision's id. The offer refuses a click, and the decision job checks again before it draws. |
| 12 | Fixed. `causal_repair_status` takes `factor_id` (validated: one of the cause's open factors, and on `attempt_id` when that is given too; otherwise refused) or `attempt_id` (the open factor on that attempt). With neither, or no factor on that attempt, it reads the oldest, as before. The status read, the router's decision, the offer's reread, Teach me now and the repair entry each pass the factor. Frontend: the feedback screen's first read names its attempt, and later reads and the actions name the status's factor. Teach me now's hand-off opens the repair for that factor (`openRepair`, `RepairScreen`, and the `start_remediation` command with optional `factor_id` and `session_id`). |
| 14 | Fixed. `probe_episodes.known_exposure` reads the answer admission's reveal window (`production_admissibility` over the item and its learning object, at the decision's instant; none below `mvp-0.61`, as the admission). The payload carries `exposed`, and the valuation record freezes `exposure` (its reason, scope and instant). An exposed probe earns no information (`channel_use: exposed`). |
| 15 (its test) | Fixed. The valuation freezes a lossless replay payload (`frozen.replay`, the `check_replay` format, which now encodes the diagnostic payload's dataclasses and a repair's frozen coverage; payloads without them are written as before). `learner_probe.revalue` values it again from the stored row alone, with no vault, repository or config. The test compares the values, choice, results and decisions with the stored evaluation. |
| 17 (the common target) | Fixed. The decision freezes one objective for both arms, the factor's learning object (`measurement.freeze_followup`, support the arms with mass), in its own transaction, as the automatic lane's decision does. The outcome adapter measures a learner-lane decision on that objective for both arms, intention to treat (`router.outcomes`: by the row's surface). An answer to the offered item outside the offer is never the decision's action. |
| 19 | Fixed. The sidecar's status read decides nothing. A factor with no decision reads `pending` (offer withheld, Teach me now left), and the worker is asked to run its new `probe_router` slot (`learner_probe.run_pending`). That slot reads the status again (so a refusal made meanwhile is honoured), values, decides and records, off the request loop. The queue needs no table: `learner_probe.requested` lists each open factor whose latest receipt is the router's pending read and that has no decision of either lane. The receipt carries the read's session, and the next start resumes the queue (`resume_post_attempt_jobs`). The slot runs only when a read or a start asks, never on idle polls, so a decision that failed to record is tried at the next read. The repair entry holds while pending. Frontend: `useRouterDecisionPoll` reads a pending status again (feedback) or asks the entry again (repair), backing off from 500 ms over six tries, and stops once decided. |

### R8 and R9: the plan (as it stood before the build)

The fix is one router decision per next observation of a router-owned episode, with stop among its options. Block
release, the scheduler and item-open consume it, and it is pinned on the next presentation. It is larger than the rest
of this round together, and its stop arm cannot be recorded without a migration. So it stops here, unwired.

1. **The decision.** A new module beside `learner_probe` (`daily_plan/probe_continuation.py`) generalizes the learner
   lane's decision. It applies at a router-owned episode's boundary: an answer recorded, K continuing, and no
   presentation active.
   - Options: `next` (the episode's top eligible instrument, eligibility from `eligible_instruments` with no EIG floor)
     and `stop`.
   - Pricing: `evaluate_probe` on the episode's effective posterior, that instrument's channel (`learner_probe._channel`)
     and its known exposure.
   - Learned, the mix draws. Unlearned, the probe coin does (`P(next) = r`, exact).
   - Record: a `plan_interrupt` row with receipt key `plan_interrupt:probe_continuation:<episode>:<qualifying count>`,
     its replay payload, assignment and objective, as the learner lane's.
2. **The job.** The same `probe_router` slot. Its queue is derived the same way: router-owned episodes in progress with
   no active presentation and no continuation decision for their current count.
3. **The consumers.**
   - Block release (J): unchanged. One question closes the block, and the next presentation's pin names the
     continuation decision, so its answer is router-owned too. That removes R9's legacy `_next_observation_does_not_pay`
     on the second answer.
   - The scheduler (H, R8): a router-owned episode's one probe candidate is the decided instrument. `probe_gate` admits
     it by the decision whatever its EIG (EIG only ranks), and precommit binds it with the decision's pin. With no
     decision, or a stop, it offers nothing, under its own reason, not `diagnostic_reserved`.
   - Item-open (I, R9): commits only the decided instrument, pinned. Another item of the episode is ordinary practice.
     A pending decision is inactive (`router_decision_pending`).
4. **The stop arm needs a decision.** `probe_episodes.completion_reason` has a CHECK (migration 200) with no router
   reason. Three ways out:
   - a `router_stop` reason by migration (the next free number is 273 or 274; the orchestrator assigns it);
   - an owner call to record the stop under an existing reason. `value_of_information_stop` would conflate it with the
     legacy value stop, and `manual_stop` misdescribes it;
   - leaving a stopped episode in progress, which keeps its learning object's one open episode. Not recommended.

   Recommended: the migration.
5. **Fail-first tests.**
   - A flat (zero-EIG) router-owned instrument decided `next`: it is included in the queue and precommitted with its pin.
   - The sentinel journey extended through the second answer: J closes the block by the pin, and K reads no legacy worth.
   - A stop ends the episode.
   - A pending decision serves nothing at either door.

The orchestrator chose the migration (273); the build is the next section.

### Judgment calls (round 2)

1. **R11, an automatic probe asked:** the learner lane's status reads `not_selected` with
   `router_asked_on_automatic_lane`, since the factor's one probe was the automatic lane's. The reverse order, the
   automatic lane deciding after a learner-lane decision, is not checked. The automatic lane decides before the feedback
   is released, and its later redraw after losing to a lesson is IH2's own boundary by design. Common repair is still
   decided per lane (round 1, judgment call 1).
2. **R12, several factors:** a read that names neither a factor nor an attempt with one still reads the oldest. A cause
   matched from an earlier miss keeps working that way. Returning every actionable factor's disposition at once is not
   built.
3. **R14 may price most real learner-lane probes exposed.** The answer admission counts any reveal on the learning object
   inside its coverage, including a full-answer display of the miss's own feedback. Such an answer would also be refused
   as evidence by the episode reading (`mvp-0.61`) when it is given. The router now prices what the answer will be worth.
   Every real decision was already unlearned (Limitations), so the served draw does not change, only its record. The owner
   may want to look at the interaction itself.
4. **R17 measures intention to treat.** The probe arm is measured whether or not the offer was taken. Both arms arrange
   the objective's measurement (a "Check once" question later), as the automatic lane's decisions already do.
5. **R19's poll** is UI timing (half a second, doubling, six tries), not a weight or threshold of any decision. A pending
   status keeps the panel's pending copy and Teach me now.
6. **R6's retired pin** ends `abandoned` (no new end reason, so no migration), and the item it pinned is ordinary
   practice if opened, as with an answer shown on a routine display.
7. **R19, the read's one write.** The status read writes no decision, valuation, assignment or objective. It still
   records its facts receipt, once per fingerprint, as every status read has since the tag (round 1). That receipt is
   also the job's durable request, which is why no queue table (and no migration) was needed. A read that wrote nothing
   at all would need a request row elsewhere.

### Proof (round 2)

- `tests/test_probe_router*.py` and the decision-integrity file pass (round 2 adds 19 tests there).
- The import-based affected set (`scripts/affected_tests.py --base 41ab8e5977`: 1,114 files) passes, run in 28 chunks of
  40 with `-n 1 -m "not arc_close"` (three chunks at a time, each in its own 3 GB scope). One chunk failed on the idle
  thread inventory, which now counts the new slot (below), and that file was rerun and passes.
- `tests/test_identity_pins.py` passes, with no pin moved: the replay payload's digest is a record of the row, not a
  compared identity.
- `test_structure_ratchets.py` passes with `golden_json_lines` raised by 398 (below). `test_architecture.py`,
  `test_test_layout.py`, `ruff check` and `lint-imports` (55 kept) pass.
- `npm run typecheck` passes, and so do the touched vitest files: `CausalAttribution.test.tsx` (3 new tests), the
  `FeedbackScreen*`, `RepairScreen.phase4`, `RepairOverFeedback.phase4` and `denyList.phase4` tests.

Assertions changed:

- `test_probe_router_learner_lane.py::test_a_status_read_decides_once_and_a_reread_draws_nothing_and_writes_no_receipt`
  now finds two receipts: the pending read's, then the decided status's (it found one). A remount still adds none.
- `test_probe_router_learner_lane.py::test_the_repair_entry_holds_only_on_the_routers_selection`: the entry first holds
  on `pending`. The job is run, then the entry holds on the selection or starts the repair, as before.
- `test_sidecar_idle_threads.py` (two tests) counts six background threads, not five: the new
  `learnloop-post-attempt-probe_router` slot. Its idle-CPU check passes unchanged.
- The learner-lane tests' status helpers (`read_status` in `tests/probe_router_authority_helpers.py`) wait for the
  decision job when a read is pending. No other assertion changed.

**The diagnosis journey golden** moved for the two `router_learner_*` journeys only; every other case is byte-identical.
What they now record:

- the decision's frozen exposure and replay payload;
- the session on its facts receipt;
- the decision objective and the measurement check it arranges (`commitments` and their versions, events and targets,
  the depth policy rows);
- surrogate ids renumbered by those rows.

`golden_json_lines` rose by 398 (`tests/goldens/structure.toml`). Those journeys call the library's synchronous
`learner_probe.decide`, which the job runs, so they show no `pending` stage.

**Not verified:**

- `cargo check`: the `start_remediation` Tauri command gained two optional arguments and was not compiled.
- The decision job's latency, or the app driven end to end.
- The owner-copy run. Nothing here changes an upgrade: no row is rewritten and no decision is made by one.

## The continuation decision (R8, R9): migration 273

After round 2 was accepted (at `0a1f8247b8`) the orchestrator assigned migration 273 and asked for the build. The
branch first merged `origin/main` (`c6bef417bd`: the inline checks' fix round, 271, and the Reader's retirement, 272),
so 273 sits on 272.

| Commit | What |
|---|---|
| `45110c257f` | Merge `origin/main` |
| `cff2bd743e` | Migration 273 (`probe_episodes.completion_reason` gains `router_stop`), the migration-head fixture upgraded in place, its test |
| `f49a3f43dc` | The continuation decision, its doors and tests |
| `89be3a4726` | The stop option renamed (`CONTINUATION_STOP_REF`); 273 in the earlier migrations' upgrade diffs |
| `ad538f8469` | Merge `origin/main` again (`1966a33cbf`: the unlocated due-check marker, the inline-check server fixes, round 1 of this fix landed; head still 272). The conflicts were generated reference notes only, regenerated after |
| `0b3daa34da` | A router decision's measurement never takes a probe instrument as its check |

**The decision** (`daily_plan.probe_continuation`). An episode is router-owned when a probe the router selected at its
tag was administered in it (`probe_authority`). Such an episode can be left in progress with no presentation standing
after an answer: its block is the one question, and its completion reads only evidence and the count. Then the router
decides its next observation.

- **Options:** `probe`, the episode's top eligible instrument, and `stop`.
  - Eligibility comes from `eligible_instruments`; EIG only ranks.
  - So a flat, zero-EIG instrument can be asked.
- **Pricing:** the learner lane's valuation (`learner_probe.value`) on:
  - the episode's posterior (the payload's `prior`);
  - the instrument's channel;
  - the factor's repair classes (`causal_orchestrator.repair_classes_for_factor`);
  - the probe's minutes (`causal_reads.probe_burden_minutes`) and its known exposure.
- **The draw** is the learner lane's, now one function (`learner_probe.draw`): the mix when learned, the probe coin
  when not. Its seed is the boundary's (`mix.seed_for` / `probe_coin.seed_for` of the boundary key, unit
  `probe_continuation`).
- **The row:** `plan_log.log_probe_continuation_decision`.
  - Surface `probe_episode`, options `probe` and `stop`.
  - The logged propensities are exactly `served_pi`; the coin's assignment row and the objective commit with it (the
    episode's learning object; arm `insert` or `stop`).
  - The replay payload is frozen, and `learner_probe.revalue` reproduces its values from the row alone.
  - The receipt key is `plan_interrupt:probe_continuation:<episode>:<observations>:<redraw>`, one decision per next
    observation. `redraw` counts the earlier decisions at that count whose pin ended unanswered (expired, invalidated):
    each such end opens a new boundary.
- **In the same transaction:**
  - a `probe` commits the next presentation, pinned with the decision (`causal_probe.router_decision_id`,
    `continuation_of_episode`);
  - a `stop` completes the episode with `router_stop` and names the decision in `completion_detail_json`
    (`probe_blocks.stop_on_router_decision`, which also writes a diagnosed gap's typed transition and tutoring segment,
    as a completing block end does).
  - Anything that fails rolls the whole decision back, and the episode stays waiting.
- **The job:** the worker's `probe_router` slot, after the learner lane's. Its queue is derived
  (`probe_continuation.requested`), so a restart's `resume_post_attempt_jobs` finds a waiting episode. Every
  submission already calls that resume, so an answer that leaves an episode waiting asks the job.

**The doors consume the pin.** Eligibility is carried apart from EIG:

- **The scheduler (H, R8).** A router-owned episode's one candidate is the item its standing pin names
  (`probe_episodes.router_pinned_item`; the automatic lane's workflow pin keeps its own serving path).
  - The probe gate admits that item whatever its EIG (`router_pinned_items`), and the queue puts it first, as a
    session's presentation.
  - No other instrument of a router-owned episode is a probe candidate, and nothing is precommitted for it.
- **Item-open (I, R9).** A router-owned episode serves only its standing pin (the existing committed-presentation path).
  With none standing, the door answers `router_decision_pending` and asks the job.
  - `commit_item_presentation` itself refuses a router-owned episode, so the TUI's door is closed too.
- **Block release (J).** The pin makes the continuation's answer router-owned, so its block is the one question and
  `_next_observation_does_not_pay` is never asked. The sentinel journey proves it through the second answer.
- **Completion (K).** Unchanged: evidence and the count. The router's stop is the decision's, written by the job.

**Persisted meaning and the tag.** The fix rides on `mvp-0.70`, now with a migration:

- **The migration is schema, not meaning.** It widens one CHECK and rewrites no row. Every vault applies it on its next
  open, whatever its tag, and a vault below the tag never writes `router_stop`.
- **Where the new behaviour lives.** It is only in decisions made at `mvp-0.70`: a continuation needs a router-owned
  episode, which needs a router decision stamped with the tag (`decision_owns`). No vault holds one yet; the owner's
  vaults are at migration 255, far below.
- **Replay** derives nothing from these decisions. `probe_episodes` is a workflow table, read as stored.
  `tests/test_probe_router_continuation.py` rebuilds a vault after a router stop twice: the derived rows and the
  episode are equal, and the only ledger row added is the rebuild's own receipt.
- **Below the tag** no episode is router-owned, so `requested` is empty, no door changes and the scheduler reads
  nothing new.

**Judgment calls:**

1. **While the router decides,** a router-owned episode's instruments are not probes. One that is not a diagnostic
   surface is ordinary practice if opened, as any item outside a probe. A diagnostic surface stays reserved. The job is
   asked at the submission that leaves the episode waiting, so the window is the job's run.
2. **The learner's refusal at the display door** (round 2's R6) does not retire a continuation pin. The offer's "Not
   now" is about the offer. Retiring the pin would open a new boundary each time, and the episode would loop.
3. **The next instrument is the top eligible one.** The router decides whether, not which. The valuation prices that
   one instrument.
4. **A decision's measurement never takes a probe instrument** (`0b3daa34da`). The proof after the second merge found
   the objective a learner-lane or continuation decision freezes arranging its "Check once" on a probe's instrument
   (the journey golden had taken `pi_causal_probe_001` itself). The check then held the router's next instrument back
   (`intent_check_waiting`), and would have served it as an ordinary question. Both lanes now exclude the learning
   object's instrument items from the arrangement (`learner_probe.instrument_items`: card-bound items, diagnostic
   surfaces, the factor's candidates).
   - Fail-first test: `test_no_router_decisions_measurement_takes_a_probe_instrument_as_its_check`.
   - The journey golden's two `router_learner_*` journeys now check `pi_svd_define_001` (20 lines fewer).
   - Not covered: a *replacement* check (after a check answered warm) is picked later without these exclusions, as the
     automatic lane's are. Also, the automatic lane's own objective still passes no exclusions; its generated probe is
     reserved by its workflow.

**Proof (this part):**

- `tests/test_probe_router_continuation.py` (11 tests):
  - the decision's exact served distribution, assignment, objective, receipt key and pin, decided once;
  - a flat instrument (EIG 0) the router asks, admitted and served first by the scheduler, then served at the door;
  - the continuation's answer closing its block with every legacy worth function raising;
  - a stop completing the episode with `router_stop`;
  - no door committing anything while the router decides;
  - a pin that ended unanswered opening a new boundary;
  - a restart resuming the queue;
  - below the tag nothing waiting;
  - the rebuild after a stop;
  - a revaluation from the stored row for both arms.
- `tests/test_probe_router_stop_migration.py` (2): the head fixture holds 273 in rollback mode; a downgraded copy
  upgrades with every row and index kept and nothing else changed.
- The worth-gates sentinel journey now asks its second instrument through the decision. It was shown failing on the
  base: the door committed the instrument with no decision. The continuation file failed on import.
- `tests/test_migrations.py`, `test_tracked_fixture_databases.py` and `test_public_tip_guards.py` pass, and so do the
  `tests/test_probe_router*.py` files.
- `test_architecture.py` passes (the burden read is a public name now). `test_structure_ratchets.py` passes with
  `scheduler.py` raised from 4442 to 4468 lines (reason in `tests/goldens/structure.toml`). `ruff` and `lint-imports`
  (55 kept) pass.
- `cargo check` of `apps/learnloop-tauri/src-tauri` passes, covering round 2's `start_remediation` command.
- Assertions changed: `test_probe_router_worth_gates.py`'s journey. Its door is first asked for the second instrument
  and refuses (`router_decision_pending`); the job runs; then the door serves the router's pin, and the test checks
  that pin is router-owned. It asserted that the door committed the instrument directly. The four tests' shared setup
  moved to `tests/probe_router_owned_helpers.py`, unchanged.
- The database and module reference notes were regenerated after the commits (`db_generate_reference.py` and
  `db_validate_reference.py`, `module_generate.py` and `module_validate.py`, the last a PASS).
- **The whole suite** (every `tests/test_*.py`, `-m "not arc_close"`) ran, because the migration and the head fixture
  make every test depend on the change. It ran in 42 chunks of 40 at `-n 1`, three chunks at a time, each in its own
  3 GB scope. It found two things, both fixed and the failing files rerun green:
  - **A bug of this build.** The continuation's stop option was first named `STOP_REF` in `plan_log`, which rebound
    the plan block decisions' `stop_for_today`. That broke the plan's stop and the stop coin, the offer and objective
    tests and the plan-refs leaf test (36 tests). It is now `plan_log.CONTINUATION_STOP_REF`.
  - **The earlier migrations' "nothing else changed" upgrade diffs** (16 test files) now set aside
    `ROUTER_STOP_ALTERED_TABLES` (`tests/probe_router_stop_migration_helpers.py`: `probe_episodes`, rebuilt by 273),
    as they set aside every earlier rebuild. These are assertion changes by the migration, the established way.
  - Every other file passed. The module catalog test passes after the regeneration.
- **After the second merge** (`ad538f8469`, then `0b3daa34da`), the import-based affected set (`affected_tests.py
  --base ad538f8469`: 517 files) passes, in 13 chunks of 40, `-n 1 -m "not arc_close"`. So do the proof files:
  - `tests/test_probe_router*.py`, the migration, fixture, upgrades, table roles and replay files;
  - the identity pins, the structure ratchets, architecture and test layout;
  - the journey golden; `ruff` and `lint-imports` (55 kept);
  - `npm run typecheck`, the touched vitest files (146 tests) and `cargo check`.
  - All three reference generators ran on the committed tree (`63378c44bc`).

## Owner copies (run by the orchestrator)

Run on 2026-11-24 on backup-API copies of the three floor-set vaults (never a live vault), each upgraded to `mvp-0.69`
first, with the isolation above. Counts only; the copies were deleted afterwards.

- Counts before against counts after the upgrade to `mvp-0.70`: on every copy only `algorithm_version` and
  `probe_router_on` moved. The upgrade decided nothing and rewrote no receipt, decision or episode.
- `integrity_check` ok and `foreign_key_check` empty on every copy.
- The shadow rebuild's difference counters are the same at `mvp-0.69` and at `mvp-0.70` on every copy (mastery rows
  differing: 34, 21 and 18; facet rows: 3, 4 and 1; no schedule row), so this tag adds none. Each rebuild added one
  row to a ledger, its own rebuild receipt.
- `doctor` exits non-zero on these copies before and after alike, on content findings this step does not touch
  (rubric criteria whose `depends_on` names a facet, and study-map warnings).

## Fix round 3 (the re-review of 2026-11-26)

Branch `refactor/g2-fix-round-3`, cut from main `a534c9e529` (head tag `mvp-0.76`, migration head 276). Each fix names
the class of defect it removes (its generator), not only the instance. Every finding was checked against the code
first; each fixed one has a fail-first test (shown failing against the base's `src` before its fix) and a ledger row
G2-R21 to G2-R36 in the review's table order. **No tag and no migration in this round:** every fix below is
protection or an integrity rule over rows that already exist (no stored decision's meaning, propensity or replay
changes); the findings that need `mvp-0.77` are listed under "Not done in this round".

| Finding | Class (generator) | Disposition |
|---|---|---|
| 1 (R21) | A door that shows an item in the session without the session serve's verdict | Fixed. `exam_material.serve_refusals` is the one verdict (the `session_serve` row); `probe_episodes.item_refusals` reads it in selection, the learner lane's offer, reread and acceptance; `serve_presentation` ends a protected pin unshown before anything is marked served. A past exam that is not held out stays servable, as in the session serve (matrix 6.1/6.2, SS = S). |
| 2 (R22) | A derived copy that drops its source's locators | Fixed. A kept copy carries the canonical exercise and source refs (`vault.copy_locators`); a protected probe is not kept; older copies: `learnloop doctor` names them (`remint:missing_source_locators`, an error when the source is protected now) and `--fix-state` repairs them. |
| 3 (R23) | A unit of work whose only fenced write comes last | Fixed. `writer_fence.require_current` (the triggers' rule as a statement) opens the continuation's transaction (both arms) and the offer's (entry and pin now one transaction). No table joins the fence; no migration. |
| 4 (R24) | A decision validated against a snapshot read before its valuation | Fixed. The continuation rereads the episode inside its transaction; "Stop diagnosing and teach me" is one transaction. |
| 7 (R27) | A door that supersedes or relocks without asking who owns the episode | Fixed. `probe_presentations.ownership_refusal` in the payload builder every presentation passes; `episode_conflict_reason` refuses a relock under a standing owned pin. |
| 8 (R28) | A liveness rule gated on answer quality | Fixed. A router-owned episode reads its supply after any observation and parks (`park_without_supply`, one transaction with its generation need); the continuation parks through it too. The continuation test's parking assertion is exact. |
| 10 (R30) | Two eligibility reads for one instrument | Fixed with R21's `item_refusals` (offer, reread, acceptance and selection share it). |
| 12 (R32) | A cross-lane check made before the write instead of in it | Fixed. Each lane claims the factor's initial decision inside its own transaction; the automatic lane logs `factor_decided_on_learner_lane`. IH2's redraw keeps its boundary. |
| 15 (R35) | A learner action written before its request is validated | Fixed. `validate_shown_factor` and the consent in one transaction. |
| 5, 6, 9, 11, 13, 14, 16 | | Not done in this round (below). |

**Assertions changed:**

- `test_probe_router_continuation.py::test_the_continuation_answer_closes_its_block_by_its_pin_and_no_legacy_worth_gate_is_asked`:
  the episode's status after its last instrument is exactly `pending_items` and nothing waits (it accepted
  `in_progress`). Tightened, not loosened.
- `test_k1_serve_door_reservation.py`: the switch patch moved to where the switch is now read
  (`exam_material.held_out_selection_active`); the assertion is unchanged.
- 18 test files pass the vault to `serve_presentation` (a required argument now); no assertion changed.
- `test_probe_router_decision_integrity.py`'s two lane setups moved, unchanged, to `tests/probe_router_lanes_helpers.py`.

**Observed, not fixed (outside this step):** `remint_probe_as_practice_item`'s `probe_reminted` interaction event
fails the table's `kind` CHECK and is logged and skipped (best-effort), so a remint leaves no interaction event.

### Not done in this round

- **5 (propensity of a forced head) and 14 (the learned chooser's rounding):** both change a logged propensity, so both
  belong under `mvp-0.77`. 14's generator is `router.mixture.Draw.deterministic` (a 1e-12 tolerance) read as
  `1.0 if drawn.deterministic else drawn.propensity` at five sites; the fix is a `Draw` property that logs 1 only when
  no other option has mass, gated by the tag where the sites have the config. 5 needs router-pin promotion moved into
  the composition the probability calculation shares, and a failing `OfferHeadMismatch` path made to refuse the offer.
- **6 (Continue opens the router's question):** one resolver (pending, the exact standing presentation, or the
  completed transition) for the desktop and the terminal client, plus the frontend.
- **9 ("Check once" takes the next probe instrument):** carry the instrument exclusions through sharing and
  replacement in `daily_plan.measurement`.
- **11 (the same prior for offer and episode):** bind the episode to the valued lock (its hypothesis versions and
  prior) at entry and retarget.
- **13 (the 0.6 family-repeat multiplier):** a design choice; options in the round's report.
- **16 (the live-to-rebuild proof):** a live snapshot before the first rebuild, compared row by row.

### Fix round 3, second part (the findings left above)

Same branch, merged with main first. The findings that change a logged propensity, a stored decision's meaning or
what an episode administers sit under the successor tag **mvp-0.77** (`docs/reviews/algorithm-mvp-0.77.md`, one
constant, one upgrade row: an idempotent projection; both sides of the tag tested); the others are fixed without it.

| Finding | Class (generator) | Disposition |
|---|---|---|
| 5 (R25) | A live step the probability calculation does not recompose | Fixed under mvp-0.77: the router pin's promotion runs inside `compose`; a head mismatch refuses the offer. |
| 6 (R26) | Two clients each deciding what continues a router-owned episode | Fixed: `probe_controls.router_next`, read by the sidecar and the terminal client; the desktop waits for the router's question. |
| 9 (R29) | An exclusion consulted on one path of a decision's measurement | Fixed: sharing and replacement carry the probe decision's instrument exclusions. |
| 11 (R31) | A second derivation of a value the decision fixed | Fixed under mvp-0.77: entry and retarget bind the valued lock. |
| 13 (R33) | A made-up constant in a ranking | Fixed under mvp-0.77 (owner decision, option (a)): expected information over the observed posterior; the field retired. |
| 14 (R34) | A propensity read through a tolerance instead of the support | Fixed under mvp-0.77: `Draw.logged_propensity`. |
| 16 (R36) | A proof that compares a rebuild with a rebuild | Fixed: live snapshot before the first rebuild, row by row; a real predecessor decision answered after activation. |
| R18 residue | A lookup and an insert in two transactions | Fixed: one write transaction. |

**Stopped:** the remint's `probe_reminted` interaction event (and, same class, `rung_variant_requested` from the rung
variants) fails `interaction_events.kind`'s CHECK (migration 203's vocabulary) and is swallowed by a best-effort
`except Exception`. Making it recordable needs a migration widening the CHECK; the orchestrator decides (277).
