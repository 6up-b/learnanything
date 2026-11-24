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
