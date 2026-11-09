# Slip or gap (SG): the router weighs what a miss was, not only its grade

**Status:** built Nov 9 2026 on `sg/slip-vs-gap` as `mvp-0.57` (§10, as built; `docs/reviews/slip-vs-gap.md`). The owner kept §6's default and placed the landing right after RE0 (§1).

**Depends on:** IH landed (`spec_instruct_handoff_v1.md`, tag `mvp-0.55`), and in particular §7d.

## 1. The owner's decisions

Verbatim, Nov 9 2026:

> cold_failing can be from 1 severe bayesian surprise cold retrieval failure or 2 mild surprise cold retrieval failures, or none since the failures in the cold retrieval were insignificant/trivial arithmetic. This is something for the action router/diagnosis/teacher ensemble to decide through the learnloop algorithm.

> yes write up the slip-vs-gap follow-up spec and hand it off to the main orchestrator to implement

Standing rules that bind this spec: no rule mapping a score, count, severity or error type to an action or a candidacy (`spec_instruct_handoff_v1.md` §1). Weights, margins and thresholds are learned, and priors are seeded (owner, Oct 24). Only the grader is blind (owner, Nov 1).

Verbatim, Nov 9 2026, before the build:

- On §6's default (`γ_slip`'s seeded prior centred at 0 with `γ`'s variance): "While the numeric prior might not value a lesson after a slip, the LLM can still decide". The default stands: the numeric policy's prior for `γ_slip` is centred at 0, and the LLM's share of the mix stays free to choose a lesson after a slip.
- "Build now, beside the placement and RE0 landings; land right after RE0, before refactor arc A."

## 2. The problem

IH removed the `cold_failing` count, so any cold miss since a topic's last lesson makes it a lesson candidate (IH §7d). The router is meant to weigh the miss. IH §7d records what it can weigh today:

- **The lesson offer's own value is the same for a slip and a gap at the same grade.** The numeric policy values a lesson from adaptive difficulty's posterior. AD reads each grade as a category (success at 0.8 and up, partial from 0.4, fail below: `adaptive_difficulty/priors.py:47-48`). So a slip graded 0.85 counts as a success, and a slip and a conceptual error both graded 0.75 are identical. The lesson's effect (`router_objective/value.py`, `γ` at the lesson's mass) is the same whatever the cause.
- **The offer picked among candidates** is TE1b's staged value, `log P(accept) + log(1 − p)`. `P(accept)` reads the reason, the context and past declines; `p` is the mastery model's prediction. No cause enters.
- **The options a lesson competes against do depend on the diagnosis.** Only a `learner_state` diagnosis (or an open unresolved-cause factor) puts the topic in the repair lane, giving a repair candidate valued `V.REPAIR` (`db/stores/daily_plans.py:333`).
- **The LLM card** shows result buckets, labels 0.8 and up "correct", and shows only the result for probe and exam attempts. It never shows the diagnosis's cause class, the surprise or the error type.

The evidence exists and isn't read:
- **The diagnosis** classifies each candidate cause with `cause_scope` in `learner_state`, `transient_execution` or `unknown` (`diagnosis/split/validation.py:201`), with prior weights. Probe episodes update a posterior over those hypotheses.
- **The learner** marks hypotheses `my_gap` (`hypothesis_marks`).
- **The surprise** is stored per attempt: `attempt_surprise.bayesian_surprise`, `predictive_surprise` and `surprise_direction` (`migrations/001_initial.sql:186`).
- `diagnosis/forecast_receipts.py` already uses `TRANSIENT`.

## 3. Design

Two stages under one new successor tag, each with its own kill switch in `[router_objective]`, default on. Off, or below the tag, every value and every card matches `mvp-0.55` exactly.

### SG1: the evidence, frozen and shown (no change to what numeric values)

1. **A per-topic sensor, `miss_cause`,** for every candidate topic with a cold miss since its last lesson (IH §7d's definition), computed from the ledger with no model call.
   - **Which miss:** the latest diagnosed cold miss, read through the availability predicate.
   - **`p_gap`, `p_slip`, `p_unknown`:**
     - If a probe episode on that miss's factor has a posterior, use it.
     - Otherwise use the diagnosis's normalized prior weights by `cause_scope`.
     - A hypothesis the learner marked `my_gap` is recorded as a learner statement beside it. It is not folded into the probabilities, which keeps IH4's line between statements and evidence.
   - **`surprise`:** the attempt's `bayesian_surprise`, `predictive_surprise` and `surprise_direction`, as stored.
   - **`status`:** `diagnosed`, `pending`, `failed`, `none` or `not_applicable`, so an absent diagnosis is visible and never read as "slip".
   - **Provenance:** the attempt, the diagnosis and the episode.
2. **Freeze it in the decision trace** for `plan_block` and `plan_interrupt` decisions (beside RO's per-topic sensors, `objective_chooser.py:1144`), and in the lesson offer's card record.
3. **The LLM card shows it** for the offer's topic and for repair candidates: the cause probabilities, the surprise in words and the status.
   - This applies to probe attempts too, which today show only their result.
   - It is the cause class and probability only, never the hypothesis statements, which can restate the expected answer.
   - Bump the card version, and respect `llm_card_token_budget`.
4. **Report:** a `learnloop data-capture report` section with cause-class counts among offers, how often lessons win by class, and later cold results by class. The cold results are labelled observational.

### SG2: the numeric policy weighs the cause

1. **The lesson's effect splits by cause.** In the lesson interface (`router_objective/value.py`), the expected gain on a topic becomes a mixture over the miss's cause: `p_gap · γ_gap + p_slip · γ_slip + p_unknown · γ`.
   - `γ_gap`, `γ_slip` and the existing `γ` are effect slopes in RO's existing machinery (`effect_slope_v1`), learned from cold outcomes after lessons, each with a seeded prior (§6).
   - A topic with no diagnosed miss uses `γ` exactly as today.
2. **Repair gets the same split** (`V.REPAIR`), so a lesson and a repair are compared on the same footing.
3. **The surprise calibrates `p_gap`.** It doesn't act on its own.
   - `p_gap` passes through a calibration `logit p̃_gap = logit p_gap + β · s`, where `s` is the standardized `bayesian_surprise`.
   - `β` is a learned coefficient with a prior centred at 0, fitted on whether the topic's next cold check after the miss succeeded, with no lesson or repair in between.
   - At `β = 0` the sensor is the diagnosis's alone.
   - This is how "one severe surprise" can count for more than "two mild ones", through data rather than a cut-off.
4. **No threshold anywhere:** no probability cut-off, no surprise cut-off and no rule for slips. A slip-attributed miss stays a candidate and can lose the draw.
5. **Replay:** older decisions replay to their logged `μ`, because the switch is off below the tag and the sensor isn't read there.

### What stays

- Candidacy stays IH §7d's structural rule.
- The acceptance model is unchanged.
- The staged policy reads nothing new, by owner decision (IH §8 row 2).
- AD's posterior update is unchanged; see §5.

## 4. Data and identifiability (state this plainly in the as-built notes)

- **`γ_gap` and `γ_slip`** are learned from lessons that ran, which today number 0 in `arxiv_v2`. Until lessons accumulate, they stay near their priors, so SG2's effect at launch comes from the priors (§6).
- **The calibration `β`** is fitted on natural follow-ups, which are self-selected. Label it as such, and keep it out of `w`'s scoring, following IH4's rule.
- **The diagnosis's prior weights** are the diagnoser's judgement, not frequencies. Their calibration is what `β` and the report check.

## 5. Alternative considered, not chosen

**A mixture likelihood in AD**, where a miss moves AD's posterior less in proportion to `p_slip`. This is principled, and it would change every reader of AD: practice selection, readiness, forecasts and replay. It is a change to persisted meaning for a much larger surface. Revisit it once SG's report shows how the cause classes predict later results.

## 6. Owner decision with a default

| Decision | Default | Why | Alternative |
|---|---|---|---|
| The seeded prior for `γ_slip` | Centred at 0, with the same variance as `γ` | It encodes the belief that a lesson teaches little after a pure slip, so a trivial slip weighs less from day one. The variance lets data overturn it | Centred at `γ`. Nothing changes at launch, and data must move it, which may take months, given lessons are rare |

`γ_gap`'s prior is `γ`'s current prior. The build uses the default unless the owner says otherwise before it starts.

**Decided Nov 9: the default.** The owner: "While the numeric prior might not value a lesson after a slip, the LLM can still decide". So `γ_slip`'s seeded prior is centred at 0 with `γ`'s variance in the numeric policy, and the LLM's share of the mix, which reads SG1's sensor on its card and never this prior, stays free to choose a lesson after a slip.

## 7. Versioning and switches

- A new successor after `mvp-0.55` (expected `mvp-0.56`, one constant, renumbered at landing if needed).
- Switches: `[router_objective] miss_cause_sensor` (SG1) and `miss_cause_in_value` (SG2). SG2 needs SG1's switch on.
- Wire them as IH's switches are wired: gate, parameter registry, prefetch key, the `SEED_NEUTRAL_SWITCHES` judgement, frozen-digest helpers and recomputed defaults snapshots.
- No migration is expected (computed from existing ledgers, as RO6's fits are). If one is needed, take the next free number after RE0's.

## 8. Tests

- **The sensor:**
  - A slip (`transient_execution`), a gap (`learner_state`) and an unknown give the expected `p_*`.
  - A probe posterior overrides prior weights.
  - `pending`, `failed` and no diagnosis are explicit statuses, never a slip.
  - Nothing protected or answer-restating reaches the card.
  - Probe attempts gain the cause class.
- **SG1:** with the switch on, the trace and card change and the numeric values are bit-identical to `mvp-0.55`.
- **SG2:**
  - With the Nov 7 shape (a 0.75 miss), a slip-attributed miss gives a lower lesson value than a gap-attributed one, by the prior's difference only.
  - At `β = 0` the sensor is the diagnosis's.
  - `β`'s fit excludes rows with a lesson or repair between the miss and the check.
  - Nothing adds a threshold: a static check over the new code for comparisons against fixed numbers.
- **Switches:** off, and below the tag, everything matches `mvp-0.55`. Older decisions replay to their logged `μ`.
- **The report:** its labels are present.

## 9. Not in this spec

- AD's likelihood (§5).
- Error-type taxonomy work.
- Phone lessons (V6).
- Any change to which topics are candidates.

## 10. As built (Nov 9, `sg/slip-vs-gap`, `mvp-0.57`)

**Version.** `SLIP_GAP_ALGORITHM_VERSION = "mvp-0.57"`, one constant, the chain's next link after `mvp-0.55` (`learnloop.slip_gap_upgrade`, journalled like its predecessors; no migration). Built beside the placement fix: at the landing its `mvp-0.56` goes in the chain before this tag and becomes `slip_gap_upgrade.PREDECESSOR` (one import, one assignment), and the earlier links' pins move again.

**Switches.** `[router_objective] miss_cause_sensor` (SG1) and `miss_cause_in_value` (SG2), default true, structural/operational kill switches in the parameter registry. Gates `router_objective_switches.miss_cause_sensor_on` (the tag, the objective serving, the switch) and `miss_cause_in_value_on` (SG1's gate and its own switch). Both are named in the prefetch key from the tag (`objective_settings`), with the sensor's mark beside them (`miss_cause.mark`: each candidate topic's status, attempt, diagnosis, episode and posterior time), so a flip or a diagnosis landing starts a new job; with SG2 on the mark also names the fits' ledgers (`miss_cause.ledger_mark`: live diagnoses, lessons, stored surprises), since `β` reads every topic (Codex F1). None of these, nor the sensor on an offer's card record, enters the numeric policy's seed (`router_objective_switches.COMMON_DRAW_OBJECTIVE_KEYS`, `objective_chooser._without_miss_cause`): a decision is valued on the same draws whatever they are. SG1 moves no value; SG2 moves values only through its inputs, so with SG2 on a decision whose topics have no diagnosed miss is `mvp-0.55`'s bit for bit at the same seed (the identity, like every successor's, names the version, so across the tag the seed itself differs: Codex F2, declined). SG2 is in RO6's generator payload (`followup_generator_switches`, at the tag only), so a flip is a change point; SG1 is not. Every defaults snapshot is recomputed; `tests/test_sg_successor.drop_sg_keys` drops the keys from the earlier links' frozen digests.

**SG1** (`router_objective/miss_cause.py`).
- The miss: the latest cold attempt not fully right since the topic's last lesson ended, read through the availability predicate, not classified `lesson_probe_exposed` (IH §7d's rows; a test pins it to `lesson_suggestion.missed_since`). No older miss is read past it.
- The status, as known at the decision: `pending` (a live diagnose job queued or leased), `failed` (the latest live diagnosis is not in force: failed, skipped or for a superseded grade), `none` (nothing queued or written), `not_applicable` (it ran and found nothing to explain, or named no cause), `diagnosed`.
- `p_*`: a probe episode on the miss's factor (`probe_episodes.origin = causal_factor:<factor>`), its latest posterior known at the decision (the completion posterior or the latest observation's `posterior_after_json`), each hypothesis's mass by its `cause_scope`, the open-set mass and any key naming no causal hypothesis to `unknown`. Otherwise the diagnosis's verbalized `prior_weight`s, normalized per error event as `forecast_receipts` does and averaged over the attempt's events. Statements and `analysis_md` are never read into the record.
- `my_gap` marks: the hypothesis keys and classes beside the probabilities, never folded in.
- The trace: `candidates[ref].sensors[lo].miss_cause` (with `reached_qbar`) and the whole record at `miss_cause` (with SG2, `in_value`: `β`'s fit, each topic's `s` and calibrated split, the slopes). The offer's card record carries `miss_cause` for its topic (None with no miss), on `plan_block` and `plan_interrupt` decisions.
- The card: `history.miss_causes` for the offer's topic and each repair candidate's (`objective_card.miss_cause_entries`; `CARD_VERSION_MISS_CAUSES`, `router-policy-card-v4`, named only on a card that holds an entry), first in the section order so the budget trims it last. The cause probabilities, the status, the surprise in words (the surprise module's direction and the miss's rank among the learner's recorded misses, never a cut-off), and the learner's marks by class. `plan_interrupt` requests get the same entries as lines for the LLM alone (`miss_cause_lines`), under `llm_card_token_budget`.
- The report: `learnloop data-capture report`'s `miss_causes` section (`router_objective/miss_cause_report.py`): statuses among offers, expected offers per class (sums of probabilities), how often the lesson was drawn by class, later cold grades by class (labelled observational), and where `β` and the slopes stand.

**SG2.**
- `value.CauseSplit` on `Learning.causes`: on a diagnosed topic a lesson's and a repair's slope is `p_gap·γ_gap + p_slip·γ_slip + p_unknown·γ` at the same mass, the slopes drawn from their joint posterior (Codex F7): `γ_gap` along `γ`'s own stream (common random numbers), `γ_slip` as its regression on that draw plus its residual on a stream of its own (independent at the seeded priors); the belief's world reads the means. TE3a's learned lesson-curve shift adds after it, unchanged. Where `γ_gap`'s posterior is `γ`'s, a pure gap is the predecessor's value draw for draw; at the seeded priors the believed gains of a slip and a gap differ by the priors' means only. Every other kind, and the tail, keep `γ`. With no candidate topic diagnosed, no fit runs (`in_value.fitted` false).
- `β` (`miss_cause.beta_fit`): `P(next cold check missed) = σ(logit p_gap + β·s)`, prior `N(0, 1)` on the standardized surprise (`BETA_PRIOR`), a Laplace posterior by damped Newton (Codex F5), with a `converged` flag and the curvature at the mode. Rows: diagnosed missed cold checks whose topic's next attempt was a cold check, with no other attempt (a repair, a primed or hinted try) and no lesson opened in between. `p_gap` from the diagnosis's prior weights only, never a probe posterior (the next check is often the episode's own probe). Rows with `p_gap` 0 or 1 carry no information and are counted apart. `s` is standardized over the learner's own missed cold checks on record. The record is labelled self-selected; nothing here enters `w`'s scoring.
- The calibration: `logit p̃_gap = logit p_gap + β̂·s`; the remaining mass keeps the diagnosis's split between slip and unknown. At `β = 0`, the diagnosis's own numbers.
- `γ_gap`, `γ_slip` (`miss_cause.cause_slopes`): seeded `N(γ̄, v)` and `N(0, v)` from the `γ` the decision reads (the owner's default), each lesson that ran from an offer whose card froze a diagnosed sensor one extended-Kalman step on its first later qualifying cold outcome (`lesson_weight.qualifying_outcomes`, counted once it is known at the decision: Codex F3) under `σ(logit p₀ + m·(p_gap·γ_gap + p_slip·γ_slip + p_unknown·γ̄))`, `p₀` the mastery prediction and `m` the mass the offer froze. None yet: no offer has frozen a sensor before this tag.

**Identifiability, as it stands.** `γ_gap` and `γ_slip` learn only from lessons that ran from SG offers: none exist, so at launch SG2's effect is the priors' (a slip-attributed lesson or repair learns `p_slip·γ̄` less per unit mass). `β` is fitted on natural follow-ups, which are self-selected and few; on one copy it moved off 0 on very few rows (`docs/reviews/slip-vs-gap.md`). The diagnosis's prior weights are the diagnoser's judgement, not frequencies; `β` and the report are what check them. `Q̄` is not monotone in the immediate learning gain (the adaptive tail practises a topic it believes weaker sooner), so at the default eight draws some repairs on mostly-gap diagnoses were valued slightly higher with the split; at 64 draws every repair and every slip-heavy lesson fell, and mostly-gap lessons moved by under 1e-3.
