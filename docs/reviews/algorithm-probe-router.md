# The probe router (refactor G2's behaviour step): the router decides whether a probe is asked

The algorithm record of refactor step G2's behaviour (design: [`refactor-g2-design.md`](refactor-g2-design.md); steps 1
to 5: [`refactor-g2a.md`](refactor-g2a.md), [`refactor-g2b.md`](refactor-g2b.md)). Its tag is
`PROBE_ROUTER_ALGORITHM_VERSION`, one constant in `learnloop.algorithm_versions`; it is `mvp-0.70` on the branch
(after the inline checks' `mvp-0.69`; L4-2, also being built, was promised `mvp-0.70`: whichever lands second takes the
next tag, a renumber of that one line with the goldens, pins and chain-position assertions regenerated). No kill
switch (owner rule 2026-11-16).

**Status: slice 1 of 2 built on the branch; it does not land alone.** The design's rule is that the router's authority
is transferred whole: slice 1 moves the automatic follow-up lane (FG1) to the router, and slice 2 moves the learner's
repair lane and removes the downstream worth gates for router-selected probes. Both land together.

## The owner's decisions this records

- **2026-11-20, G2 option f** ("Option 1 plus a small randomized share of probes"): an unwritten probe earns no
  information credit (design decision 1, the conservative value), a covering repair uses the cause-class slopes and an
  uncovered one is priced as practice (decision 2), no room to wait does not force a probe (decision 3); and a small,
  logged, randomized share of eligible misses still asks the probe, so the data that would teach the router to value
  probes keeps arriving.
- **2026-11-23, the share's size:** "derive it from an existing randomized arm's rate" (no new constant).
- **Applied by the orchestrator, 2026-11-23:** the share is the stop coin's rate, `router_objective.stop_coin`, read
  through one function (`router_objective.probe_coin.share`). The stop coin is the same mechanism (a coin beside the
  mix, its own uniform, an exact served distribution, an assignment row) and the same family (the `mvp-0.48` arms,
  each a declared price for information on an action the policies value below another), and at 0.05 it is small.
  **One config field now prices two arms:** changing `stop_coin` moves the probe share with it, and 0 turns both off.
  The field's own documentation says so.
  - Alternative kept: `router_objective.pick_open_share` (0.1), the closer subject (learning about a miss's causes),
    but another mechanism (it acts on a misconception pick, not a draw) and twice the learner minutes.
  - Alternative kept: `router.epsilon_min` (0.02), the mixture's per-option floor; the probe would stay in the
    support with only the floor's mass, which needs it removed from both policies' components and kept in the uniform
    branch (a change to the mix's structure and record), and it is very small.

The randomized arms in force when the choice was made (all fixed config values, none learned): the stop coin (0.05
each way), the randomized cold check (one a day, embedded), the open misconception pick (0.1), the two policies'
minimum shares (0.1 each; the weight itself is learned), the mixture's floor `router.epsilon_min` (0.02), AD's dose
arm (D21, 0.10, at most three offers a day) and its overlap share (0.10), the legacy queue's near-tie exploration
(0.1), and, as display or card ablations rather than action arms, the similar-decisions inclusion (0.5) and the
Reader cue holdout (0.1).

## What changes at the tag (slice 1: the automatic lane)

| | Below the tag (the predecessor) | At the tag |
|---|---|---|
| The mix's support after a miss with rival causes, on a plan | ask now, wait, no intervention (and a lesson when offered) | no intervention, and a lesson when offered: the unwritten probe is no option of either policy, now or after the block |
| No lesson offered | a draw over the three arms | nothing for a policy to choose: no model is asked |
| No room to wait | the probe asked now, deterministically (`no_room_to_wait`) | as any other boundary: waiting is never an option, the coin decides the probe |
| No plan, or the router switched off | the probe asked now, deterministically, no router row (`no_plan`, `router_off`) | the coin decides; the decision is logged (`probe_coin_no_plan`, `probe_coin_router_off`), plan fields null |
| The probe coin | none | `ask_probe` at `r`, `policy` at `1 − r`; its own seed (`probe_coin.seed_for`), its own uniform, its own assignment row (`g2_probe_coin:v1`) |
| The logged propensities | the mix's `μ` | the served distribution, exactly: `P(probe) = r`, `P(a) = (1 − r)·μ(a)`; the mix's `μ` is beside it (`mix_pi`) |
| Hard refusals (Not now, pending machine checks, a measured foreign episode) | first | first, unchanged |

The coin and the stop coin are independent draws: different seed functions (the stop coin's uniform comes from the
decision's mix seed, the probe coin's from its own), different stages, different experiment ids and rows. They never
meet in one decision (the stop coin applies at a block boundary with stop in the support, the probe coin after a
miss), and each decision's served distribution is exact on its own. In tests the probe coin's seed is pinned as its own
family (`tests/pinned_draws.py`).

Nothing already derived moves: replay runs no decision policy, and no recorded decision, probe, observation or episode
is reinterpreted. The upgrade row is `Link(PROBE_ROUTER_ALGORITHM_VERSION, idempotent_projection)`.

## Tests, pins and goldens (slice 1)

- `tests/test_probe_router.py` (written first; it failed on import before the code): the tag and its predicate, the
  share's one function, the exact served distribution, the coin's arms and assignment row, its own seed and experiment,
  the plan with and without a lesson, no room to wait, a zero share, the lane's logged decision and assignment, no
  plan both ways, and below the tag the predecessor's no-plan and no-room answers.
- FG1's fixtures (`tests/followup_serve_helpers.TAG`) build at the probe router's predecessor (computed from the chain,
  so a renumber needs no edit): their subject is the lane as it asked its probe (the written question, its admission,
  serving and receipts). One test built at the head by name (`test_followup_codex_review::test_f6_a_crash_after_the_
  diagnosis_ended_is_recovered_by_next`) names that tag now: its recovered decision must ask the probe.
- Identity pins: nine move by the tag alone (A1-A4, C3.boundary, C3.boundary_offer, C3b.chooser, C3b.chooser_offer,
  C3b.start_key, C3b.start_key_offer, C5, C6): regenerated with the behaviour change and without it (the chain
  appended alone), the same file. The diagnosis journey golden differs only by the tag string (every removed line
  equals an added line once `mvp-0.68`/`mvp-0.69` are normalized). The effective defaults show the tag line.
- After merging the inline checks (`mvp-0.69`) the tag is `mvp-0.70`: the same nine pins moved again by the tag
  alone, the journey golden and `tests/goldens/placement_stored_misses.json` again by the tag string only, the CLI
  surface's `upgrade --to` default, and the chain-position assertions of the successor tests the inline checks'
  landing bumped (one more step back for each named older tag, the head's literal one tag on).
- No assertion was weakened.
