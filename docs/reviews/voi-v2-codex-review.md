# voi-v2: Codex review and fixes

Stage `voi-v2`, branch `serving/voi-stopping`, worktree `learnanything-voi`.
Codex reviewed the stage at `6f24d6a4` (job `20261013-143656-ElFzMu`,
verdict "changes required") and found four defects: one High (F13) and three
Medium (F10, F14, F15). All four reproduced at `6f24d6a4` and are fixed in
`c5b832ff`. F13's surface group moved onto the eligible instrument in
`73dff7ba`. None was rejected. The references were regenerated at each code
commit (`ddf4cc79`, then `dc509c9b`).

Owner decisions in force (2026-10-12/13): the recommended defaults in each
spec are accepted; frictionless defaults (honest labels, generous defaults,
live changes behind kill switches, no shadow stage). The study's §12
questions are being collected separately, so this stage builds to the
recommended defaults: ranks 1 to 3 ship behind their switches and Part C
stays off. The successor label (`mvp-0.17`) and migration numbers (187/188)
are still placeholders, renumbered at the merge onto main. No paid call was
made.

## 1. Reproduction at `6f24d6a4`

Each finding was reproduced first with the regression test that now guards
it (in `tests/test_voi_v2.py`, section "Codex review of voi-v2"). The tests
were run against the unfixed source (`git stash` of `src/`), and all 7
failed for the reviewer's reasons:

| Id | What the reproduction did | Observed at `6f24d6a4` |
|---|---|---|
| F13 | The real probe vault (pinned channel, 129 members, 0.02-minute checks, belief 0.9 on one hypothesis), with all seven eligible items rewritten as fresh variants of one stimulus (`evidence_fingerprint.shared_stimulus_id`) | Every eligible item was in surface group `stim_one`, yet `lookahead.paid` was `True`: the batch was bought. After one answer the episode has no eligible instrument left, so the second observation never happens |
| F13 | The same vault with two stimuli (`stim_a`: items 001-004, `stim_b`: 005-007) | The first batch tried was `[pi_svd_define_007, pi_svd_define_006]`, both `stim_b` (robust 0.10271 min against 0.04), and it paid |
| F13 | Pure: two weak checks (accuracy 0.7, 0.1 min) on one surface | `Candidate` carried no surface identity (`TypeError: unexpected keyword argument 'surface_group'`) |
| F15 | The reviewer's pair (prior 0.75/0.25, accuracy 0.7, 0.1 min each) at `SITE_FOLLOWUP`, defaults | `continue`, method `robust_evsi_lookahead_2` |
| F10 | A 30-minute plan with overlapping project probes A (12 min) and B (5 min); the build plans A, and B is worth 0 given A. The learner skips A | The refresh valued B at 18 minutes with `chosen_before = ['pi_a']`: A was admitted again, B stopped, and the plan closed (`nothing more worth doing today fits`) |
| F10 | A build whose universe holds B (worth nothing then) but not C. On refresh, C is due and overlaps B | B's lane was `None`: C was admitted first and B suppressed; `_context` then drops C, so neither can be planned |
| F14 | A 20-minute plan, one request allowed, pool `[A requested project probe 12 min, R requested item 15 min]` | `split.requested = ['pi_req']`; A got 5 minutes and `does_not_fit_plan_minutes` |

## 2. Findings

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F13 | High | Lookahead buys a batch that cannot be administered | fixed | `c5b832ff`, `73dff7ba` | `test_a_lookahead_batch_never_holds_two_checks_on_one_surface`, `test_a_lookahead_batch_is_built_from_distinct_surfaces`, `test_a_batch_skips_a_check_that_shares_a_surface_with_a_better_ranked_one` |
| F10 | Medium | Skipped probes still suppress usable alternatives | fixed | `c5b832ff` | `test_a_skipped_probe_does_not_suppress_its_alternative_on_refresh`, `test_a_probe_outside_the_plans_universe_does_not_suppress_one_inside` |
| F14 | Medium | Request reservations can exclude the request that should come first | fixed | `c5b832ff` | `test_requested_probes_and_requests_share_one_request_rule` |
| F15 | Medium | Follow-up lookahead ships despite the explicit wait recommendation | fixed | `c5b832ff` | `test_the_lookahead_acts_at_probe_episodes_only` |

### F13: a batch holds one check per canonical surface group

`voi_stopping.Candidate` gains `surface_group`. `eligible_instruments`
already computes `surface_group_id(item)` for its exposure rule (once one
item of a group is answered, the rest of the group is excluded). It now
records that key on `EligibleInstrument.surface_group`, which is not logged
and not compared, and `probe_episode_decision` passes it to each candidate.
In `c5b832ff` the decision imported the substrate inside the function
instead. The first gate run caught that:
`test_function_local_domain_imports_match_the_frozen_edge_inventory`
forbids a new function-local cross-domain edge, so `73dff7ba` moved the key
onto the instrument. `_lookahead` then walks `rank_feasible`'s ranking and keeps only the
best-ranked feasible check of each group before it forms any batch. The top
`k` of that list are always administrable together. A dropped check is listed
in the lookahead body (`skipped_same_surface`), and a paid batch records each
member's group (`surface_groups`). A candidate with no group (the pure
scenarios, the greedy admission) counts as its own surface, so the restore
golden and the earlier lookahead tests are unchanged.

When all eligible checks share one stimulus, no batch of two can be formed:
`tried` is empty, nothing pays, and the episode stops on its single-check
values. With two stimuli, every batch tried has distinct groups, and the
paid pair is one `stim_a` and one `stim_b` check.

### F15: the lookahead acts at probe episodes only

`voi_stopping.LOOKAHEAD_SITES = frozenset({SITE_PROBE_EPISODE})` restricts it
to the only site the study simulated (§7.1). §6.2 defers the follow-up and
teach-back sites until live calibration. `value_candidates` runs `_lookahead`
only at a site in that set. `heuristic_parameters` lists
`lookahead_max_checks` only where it can act, so a follow-up receipt no
longer names a parameter that did not apply. `lookahead_max_checks = 1`
still turns the lookahead off in probe episodes.

This is a module constant, not a new config key. A later follow-up rollout
needs its own site control and the calibration §6.2 prescribes, and neither
belongs in this stage. The schema docstring and the registry description of
`lookahead_max_checks` now say "probe episode" and "one check per surface
group". This answers the voi-v2 report's open question 2.

### F10: a refresh values only probes the plan can still take

On a refresh, `_classified_pool` gives the admission
`_plan_availability(record, held)`. It names why a due probe cannot join the
plan, using the same set that `_context` keeps: `skipped_in_this_plan`,
`answered_in_this_plan`, or `outside_plan_universe`. The held probes are
excluded from that test: planned and unanswered (`already_planned`), or a
request that a crash left unplaced (`learner_request`). They are still
conditioned on, as before. An unavailable probe is filtered out before
valuation, so it is never valued and never conditioned on. Its receipt is
`voi_stopping.not_in_plan_receipt` (decision `stop`, reason
`not_available_to_this_plan`, plus `availability`), and its lane label reads
"a due project probe this plan no longer takes (skipped, answered, or new
since it was built)".

The skip test runs through the real `advance`. The build plans A. The
learner skips A, and the new-lane item N leaves the list (answered from the
full list), so the new lane releases its six minutes to maintain. The
refresh values B with `chosen_before = []` (`none_chosen`) against the 18
minutes left, and B is planned as the next block. A's receipt says
`skipped_in_this_plan`. The universe test checks the refresh's context: C is
out of the pool, and B is in maintain with a `continue` receipt, valued
without C.

### F14: one request rule for requested probes and ordinary requests

On a build, `_classified_pool` selects the requests once, before any probe
is valued. It runs `_select_requests` (same limit, budget and pool order) over
`classify(None)`, where `_request_candidate` gives a requested project probe
the maintain lane whenever the plan allows maintain. L3 says the learner's
explicit choice is always honoured and that lane eligibility never blocks a
request. So a requested probe is a request regardless of its value or the
former daily count.

The chosen requests are recorded in `_Pool.request_ids`, and
`_prepare_plan` uses exactly those. It does not recompute them from the
value-reordered pool. Each request is charged once, before the split. A
requested probe chosen as a request is preselected in the probes' admission
with reason `learner_request`: the other probes are conditioned on it, and it
is not valued or charged again. The former cap's counterfactual counts it,
and the step context lists it under `learner_requests` rather than
`already_planned`. Below the successor, or with the site off,
`request_ids = None`, and the split selects requests exactly as before.

In the reviewer's scenario, A (first in pool order) is the request and is
placed first. R's 15 minutes do not fit the 8 that remain, so R waits.
mvp-0.16 makes the same request.

### The claims that did not hold

* "Conditioned only on what was actually planned": a refresh now admits only
  probes the plan can take (F10). Skipped, answered and out-of-universe probes
  are neither admitted nor conditioned on.
* "Requests do not depend on the probes' value": requests are now selected
  before any probe is valued, and requested probes are included (F14).
* "§6.2 waits for the lookahead at the follow-up site": this now holds in
  the code (F15).
* "Feasible candidates only": a batch now also requires distinct canonical
  surface groups (F13).

`docs/reviews/voi-v2.md` is annotated where these fixes revise it: the F10
rule, the lookahead's reach, and open question 2.

## 3. Open questions for the owner

1. **Should the refresh bound probes by minutes left or by lane minutes?** A
   refresh admits probes against the plan's minutes left, as the voi-v2 F10
   rule says and this review accepted. But the §6.2 lane ledger keeps a
   skipped item's minutes as spent, and minutes the split never allotted are
   not lane minutes. So a probe admitted on a refresh is planned only when
   some lane releases minutes to maintain, as in the skip test. Bounding
   admission by the ledger's releasable minutes (the allowed lanes'
   `lane_left`) would be tighter. It is not changed here because it alters
   the voi-v2 rule beyond these findings.
2. **Should a requested probe always be honoured?** F14 makes a requested
   project probe a request whatever its value, as L3 reads. Alternatively, a
   requested probe could be honoured only when its value pays.
3. **Pre-existing, outside this stage: the vault writer cannot change
   `evidence_fingerprint`.** `vault.writer.upsert_practice_item` cannot change
   an existing item's `evidence_fingerprint`. The field is not in
   `PRACTICE_ITEM_ORDER`, so the existing value wins the merge. The F13 tests
   write the item YAML directly.

## 4. Paid calls

None. Every test uses fakes or local arithmetic: no model route, no network,
$0.00. No manual run was needed. The fixes change only probe-episode
batches, the plan's admission inputs and the request rule, all covered by
tests on temporary vaults.

## 5. Gate

The gate ran at `dc509c9b`, whose code is that of `73dff7ba`. `TMPDIR` was
the worktree's `fixtures-local/tmp`. Both suites ran under
`flock /tmp/learnloop-fullsuite.lock`, and each waited for another stage to
release the lock.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 15 kept, 0 broken |
| `flock … uv run pytest -n auto` | **9,067 passed**, 0 failed (333 s) |
| `flock … uv run pytest -m durability` | **95 passed**, 8,972 deselected (93 s) |
| DB and config references (`db_generate_reference.py`, `db_validate_reference.py`) | regenerated at schema head 188 (759 effective leaves, 308 table notes); validator `errors: []` |
| Frontend (`apps/learnloop-tauri`), `cargo check` | not run: nothing under `apps/` changed |

An earlier full run at `ddf4cc79` had **9,066 passed, 1 failed**. The failure
was `test_architecture.py::test_function_local_domain_imports_match_the_frozen_edge_inventory`:
the new function-local import of `surface_group_id` in `voi_stopping`. It was
fixed in `73dff7ba` (see F13) before the run above. That earlier log was
written to a scratch file shared with another stage's run, so its counts
were read from the summary line of this stage's own process.

Stage tests: `tests/test_voi_v2.py` has **39 cases**, the 32 from voi-v2 plus
7 for this review: F13 3, F15 1, F10 2, F14 1. Together with
`test_voi_stopping.py` and `test_mvp017_upgrade.py` that makes 121 passing.
The 7 new tests failed at `6f24d6a4` for the reasons in §1. The restore
golden (`test_at_their_restore_values_the_switches_reproduce_the_branchs_decisions_exactly`)
and every earlier lookahead test pass unchanged: restore scenarios carry no
surface group and run at the probe-episode site.
