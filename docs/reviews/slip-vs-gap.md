# Slip or gap (SG1 + SG2): build review

Branch `sg/slip-vs-gap`, built on `55abc68feb` (the spec commit on `instruct/handoff` `910f079bda`). Spec:
`docs/specs/spec_slip_vs_gap_v1.md` (its §10 is the as-built note this review checks). Built and reviewed here; the
orchestrator lands it.

## Owner decisions (Nov 9, verbatim)

- On §6's default (`γ_slip`'s seeded prior centred at 0 with `γ`'s variance): "While the numeric prior might not value a
  lesson after a slip, the LLM can still decide". Kept: the numeric policy's prior for `γ_slip` is centred at 0; the LLM's
  share of the mix reads SG1's sensor on its card, never this prior, and stays free to choose a lesson after a slip.
- "Build now, beside the placement and RE0 landings; land right after RE0, before refactor arc A."

## As built

- **Successor.** `SLIP_GAP_ALGORITHM_VERSION = "mvp-0.57"`, one constant, appended after `mvp-0.55`;
  `learnloop.slip_gap_upgrade` (the journalled link; no migration: everything is computed from existing ledgers). The CLI,
  the CLI's and the sidecar's openers, the activation journal's docstring and the import contract's module list name it.
  **For the landing:** the placement fix's `mvp-0.56` goes into `SUCCESSOR_CHAIN` before this tag; then
  `slip_gap_upgrade` imports `UNEVIDENCED_RETURN_ALGORITHM_VERSION` and its upgrade as `PREDECESSOR` (two lines), the
  defaults snapshots are recomputed again, and the earlier links' pins move again (`SUCCESSOR_CHAIN[-N]` shifts, version
  sets gain `mvp-0.56`; this branch's own `tests/test_sg_successor.py` names `mvp-0.55` as the predecessor in three places).
- **Switches.** `[router_objective] miss_cause_sensor` (SG1) and `miss_cause_in_value` (SG2, needs SG1), default true,
  structural/operational kill switches in the parameter registry. Wired as IH's: gates in `router_objective_switches`,
  named in the prefetch key from the tag (`objective_settings`), excluded from the numeric seed
  (`COMMON_DRAW_OBJECTIVE_KEYS`; with the sensor's identity mark and the sensor on an offer's card record), every
  defaults snapshot recomputed, `drop_sg_keys` in the frozen-digest helpers. SG2 is in RO6's generator payload at the tag
  (it changes logged values: the follow-up batch's ruling R8); SG1 is not.
- **Why the seed excludes SG2 too.** The existing seed-neutral keys are those that move no value at a fixed draw count.
  SG2 does move values, but only through its inputs. Keeping it out of the seed gives common random numbers across the
  switch: with SG2 on, a decision whose topics have no diagnosed miss is `mvp-0.55`'s bit for bit at the same seed, and
  one that has differs by the split alone (plus `γ_slip`'s own draw stream, which only a diagnosed topic reads). That is what made the copies' comparison below exact. A flip still starts a new job (the
  key names it) and is a change point for RO6 (the generator payload names it).
- **SG1, SG2:** spec §10.

## Evidence

### Tests (targeted; no full suite, no durability lane)

| Set | Result |
|---|---|
| `tests/test_sg_slip_vs_gap.py`, `tests/test_sg_successor.py` (new; after the Codex fixes) | 46 passed |
| The successor and pin set: 47 earlier links' successor/upgrade tests, `test_ih5_successor`, `test_curriculum_c1_landing`, `test_followup_successor`, `test_cli_help_snapshot`, `test_cli_json`, `test_architecture`, `test_registry_audit` | 1041 passed, 12 skipped, 3 xfailed |
| Router and IH files touching the changed modules (57 files: `test_ih*`, `test_ro4*`-`test_ro6*`, `test_rofu*`, `test_rospeed*`, `test_te3a*`, `test_te3b*`, `test_data_capture*`, `test_hypothesis_marks_context`, `test_instruct_handoff_ih0/1`) plus the new files, after the Codex fixes | 1003 passed, 1 failed: `test_ro5_stop_coin.py::test_serving_records_each_coin_with_its_exact_probability_and_availability` (the trace's 6-digit rounding of a fresh random propensity against a 1e-6 relative tolerance; pre-existing, nothing here touches the mix or the trace's rounding; 5 of 5 passes alone) |
| `lint-imports --no-cache` | 43 kept, 0 broken |

Every pytest ran in a 5G memory scope, at most `-n 6`, with explicit paths and an empty `HOME`, `CODEX_HOME` and
`LEARNLOOP_CONFIG_DIR`. The successor and pin set ran before the Codex fixes, which change no version, pin, snapshot or
config key; `lint-imports` ran again after them.

### Copies

Fresh backup-API copies (`learnloop.db.copies.copy_tree_with_databases`) of `~/learnloop-backups/20261109-copy`
(mvp-0.54, migration 250; arxiv_v2, linear_algebra, probability) under the gitignored `fixtures-local/sg/`. Each run took
its own fresh copy: **base** (the branch base's code from `git archive 55abc68feb`, upgraded to mvp-0.55), and on this
branch's code (upgraded to mvp-0.57) **off** (`miss_cause_sensor = false`), **SG1** (`miss_cause_in_value = false`) and
**SG1+SG2** (defaults). No model call, no network: the probes call the numeric policy directly.

**What a probe is.** For each lesson candidate topic on the copy (`lesson_suggestion.build_candidates` at a fixed moment,
the same rows on both codes), one support: the topic's lesson offer (fixed duration, mass and acceptance), a repair block
on one of its items, a review of another topic, and stop, valued by `objective_chooser.run_numeric` at a fixed seed and
the default draw count. This exercises the real inputs (AD's posteriors, the diagnoses, the surprise, the probe
posteriors) and the real value estimator; it is not a replay of the copies' logged plan decisions (the plan's support,
the mix and the LLM are not run). The decision flow itself (trace, card, offer record, mix, `μ` replay) is covered by the
twin tests in `tests/test_sg_slip_vs_gap.py` on a synthetic vault.

| | arxiv_v2 | linear_algebra | probability |
|---|---|---|---|
| Off against base: every `Q̄`, choice and draw count | identical, every probe | identical, every probe | identical, every probe |
| SG1 against base | identical, every probe; the sensor on every probe | identical; sensor on every probe | identical; sensor on every probe |
| SG1+SG2: probes whose values moved | the diagnosed topics' lesson and repair only | none (no miss on those topics has a live diagnosis: status `none`) | the diagnosed topic's lesson and repair only |
| SG1+SG2: numeric choice changed | none | none | none |
| `β` | moved off 0 on very few self-selected rows (its posterior variance still large) | prior (no diagnosed miss) | prior (no row) |
| `γ_gap`, `γ_slip` | priors (no lesson from an SG offer) | priors | priors |

Counts per vault, the per-topic statuses and probabilities and every value delta are in
`fixtures-local/sg/evidence/<vault>.compare.json` (private; not tracked).

**Why values move, and their direction.** On every diagnosed topic the lesson and the repair learn
`(p_gap·γ_gap + p_slip·γ_slip)·m` instead of `γ·m`; at the seeded priors that is `p_slip·γ̄·m` less. Lesson offers fell on
the slip-heavy topics; at the default eight draws some repairs on mostly-gap diagnoses were valued slightly higher
with the split. At 64 draws (arxiv_v2 and probability) every repair and every slip-heavy lesson fell; the mostly-gap
lessons moved by under 1e-3, in either direction. `Q̄` is not monotone in an action's immediate learning gain: the adaptive tail practises a topic it believes weaker
sooner, and at eight draws its allocation's discrete changes are of the size of these deltas.

**rebuild --shadow** on fresh copies upgraded to mvp-0.57: exit 0 and the live database's hash unchanged on all three.
The only differences are mastery rows' `algorithm_version` stamps on linear_algebra and probability, and on arxiv_v2 also
some mastery rows' `logit_mean`/`logit_variance` and some schedule rows' `due_at`. The same shadow on the base code
(mvp-0.55) gives exactly those arxiv_v2 differences: they predate this branch (SG changes no projection).

## Identifiability (spec §4)

- `γ_gap` and `γ_slip` learn only from lessons that ran from offers that froze a diagnosed sensor. None exist on any copy,
  so SG2's effect at launch is the priors'.
- `β` is fitted on natural follow-ups (self-selected: often the diagnosis's own probe) and is labelled so; it never enters
  the mix weight's scoring. On arxiv_v2 very few rows move it; a handful of self-selected rows is weak evidence, and the posterior variance
  says so.
- The diagnosis's prior weights are the diagnoser's judgement, not frequencies. On linear_algebra no recent miss has a live
  diagnosis, so SG2 does nothing there today.

## Codex review (read-only, `gpt-6.1-sol`, high; job `20261109-152925-yHiRej`)

One review of the whole diff (`55abc68feb..4be77a51f6`). Ten findings; rulings and fixes (the fix commit follows the
implementation commit on the branch):

| # | Severity | Finding | Ruling |
|---|---|---|---|
| F1 | High | The prefetch key named only the candidate topics' sensors, but `β` (and the slopes) read every topic's misses, diagnoses and lessons: a diagnosis landing elsewhere left a stale job serving old SG2 values | **Fixed.** With SG2 on, the identity's mark also names the fits' ledgers (`miss_cause.ledger_mark`: live diagnoses, lessons' opens and closes, stored surprises, each a count and the latest write); still out of the seed. A new attempt was already named by `as_of` |
| F2 | Medium | Off does not preserve the predecessor's draws: the identity keeps `version`, so mvp-0.55 and mvp-0.57 seed differently; SG2's generator field is present (false) when off | **Declined, claim narrowed.** Every successor's identity and RO6 generator name the algorithm version, so every tag starts new draws and a change point (IH5's off did the same against mvp-0.54). The kill switch restores the predecessor's policy, and at the same seed its values bit for bit: the twin tests and the copies' probes compare at a pinned seed. Making the seed version-blind would change every earlier link's behaviour; out of scope. This review and spec §10 say "at the same seed" |
| F3 | Medium | The slopes' first outcome after a lesson used occurrence time only, admitting an outcome received after the decision | **Fixed.** The first qualifying outcome must be known at the decision (THE availability predicate); until it is, the lesson is unresolved |
| F4 | Medium | As-of leaks: today's job state, future lesson closes, a marked hypothesis's class from a later version, surprise rows written later | **Fixed** for lesson closes (a close after the decision counts as still open), marks (the marked version's class, else the latest version known then) and surprises (written by the decision). **Declined** for the job state: `post_attempt_jobs` keeps no history, and the sensor is computed at serving time, where "queued now" is the state known at the decision; a historical recompute would need a job ledger. Stated under "unverified" |
| F5 | Medium | `β`'s undamped Newton step can cycle and report the prior | **Fixed.** Damped Newton (a step halves until the concave log posterior does not fall), a `converged` flag, the curvature at the returned mode. Codex's case is a test |
| F6 | Medium | A pure gap by rounding (`p_gap` = 1 − 1 ulp, no other mass) divides by zero in the calibration; nine equal gaps can sum above 1 | **Fixed.** Probabilities renormalized per record; the calibration leaves a record with no mass on the other side unchanged. Tested |
| F7 | Medium | Both slopes were drawn on one normal (correlation +1), discarding the learned covariance and doubling a mixed diagnosis's variance at the independent priors | **Fixed.** The joint posterior is drawn: `γ_gap` on `γ`'s stream (a pure gap stays the predecessor's draws), `γ_slip` as its regression on it plus its residual on a stream of its own (`CauseSplit.cov`). At the seeded priors they are independent. Tested (correlation, variance) |
| F8 | Medium | Decision-path cost: the reference moments recomputed per row; the fits run with nothing diagnosed | **Fixed.** Moments once per decision; no fit when no candidate topic is diagnosed (the record says `fitted: false`). The per-miss queries in `β`'s rows remain (a full-history read on each SG2 decision with a diagnosed topic): noted, not optimized |
| F9 | Low | Interrupt lines: statements and causes each got the whole budget; the heading was not counted | **Fixed.** The causes get what the statements left, and the heading and note count. Tested |
| F10 | Medium | §8 claims under-tested: whole-card bytes, probes and sequences skipped, observation posteriors, budgets, fake-LLM interrupts | **Fixed in part.** Added: the whole card off and below byte-identical and on differing by the section alone; a probe's repair branch and a sequence's repair step split; an open episode's observation posterior; the lines' budget. **Not added:** a live `plan_interrupt` through a fake LLM (listed as unverified) |

Codex also reported, as checked correct: the latest miss is never read past a newer undiagnosed one; no record carries a
hypothesis statement, `analysis_md` or an expected answer; `β` reads prior weights, never a probe posterior, and drops
rows with an attempt or a lesson in between; the belief's world reads the slopes' means; TE3a's shift stays additive; the
tail keeps `γ`; no new action threshold; the successor wiring and the report's labels are consistent.

## References

Regenerated on the final tree (`db_generate_reference`, `module_generate`, `desktop_generate`); `db_validate_reference`
(after the two prose leaf counts moved from 1192 to 1194), `module_validate`, `desktop_validate` and `validate_vault` pass.

## What is unverified

- No full suite and no durability lane (the orchestrator gates at landing).
- The copies' evidence is decision probes on the numeric policy, not a replay of logged plan decisions with the mix and a
  model; the twin tests cover the decision flow on a synthetic vault only.
- The plan_interrupt lines (`miss_cause_lines`) are tested for off and below the tag, not through a live restraint
  decision with a fake LLM.
- `cause_slopes` is tested on one synthetic lesson; no real lesson from an SG offer exists.
- Performance on a large history: `beta_rows` reads every missed cold check, with a few queries each, on each SG2
  decision that has a diagnosed candidate topic.
- The sensor's `pending` status reads the diagnose job's state now, not as of an earlier moment (Codex F4, declined):
  exact at serving time, not for a historical recompute.
- The kill switches restore mvp-0.55's values at the same seed; across the tag the seed itself differs, as at every
  successor (Codex F2, declined).
