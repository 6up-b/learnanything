# The placement hole: an answered LO with no due time never came back (successor mvp-0.56)

Owner decision, 2026-11-09: "Fix the placement bug with a successor." The finding is
`docs/reviews/test-suite-audit.md` §3 ("The two owner-lane failures"). This note covers the cause, the rule, the
successor, the evidence, the Codex review and what is left untested. Counts and LO lists from the owner's newer
backup stay in the gitignored `fixtures-local/placement/`; this note names only what main already makes public.

## The cause

Under placement (`PLACEMENT_VERSIONS`, `placement.enabled`, opening probes ignored) two gates in
`scheduling/scheduler.py` decide whether an LO with no evidence is served at all:

- `_BuildAdmission.placement` makes an item **new material** only when it was never attempted
  (`state.last_attempt_at is None`), on an LO with no servable episode and no goal frontier.
- `_BuildAdmission.cold_start_gate` refuses (`cold_start_unattempted`) any item whose LO has no evidence
  (`mastery.last_evidence_at is None`), no servable open episode and no frontier entry, unless the first gate made
  it new material or an assumed check.

An item with an answer but **no due time**, on an LO with **no evidence**, passes neither. The answer sets
`last_attempt_at`, so it is not new material; the LO has no evidence, so the cold-start gate refuses it; and with
no `due_at` its forgetting risk is zero, so nothing else brings it back. Below placement the LO's opening episode
(`trigger = 'initial'`, `pending_items`) kept it served through the cold-start floor. Placement ignores an
unanswered opening episode (owner decision 2026-10-12), so the LO lost its only door. If the LO has no other item,
it never returns.

Answers that leave this shape are those the attempt path records without an FSRS review and without advancing the
LO's evidence:

- a `self_report` (a rung re-request's belief write) whose grade replay held as `grade_contract_unrecorded`, so it
  wrote neither a review nor evidence. This is the audit's case, `pi_a_preprocessing_pipeline` on arxiv_v2;
- a **primed** answer (help shown before answering). The causal policy classes it as a repair activity, which skips
  the FSRS review, and mastery keeps `last_evidence_at` on the last unprimed answer (`learner/mastery.py`). A test
  reproduces this shape on a synthetic vault.

These cases look like the hole but aren't:

- **linear_algebra's similar item** is a spent `diagnostic_probe`. A probe is single use, so its state is
  deactivated on its one answer, and the routine gate (`inactive_state`, `diagnostic_probe_administered`) refuses
  it for good, as intended. Its LO has evidence and other items, which keep it served. Nothing is lost.
- An answered item with no due time whose LO **has** evidence belongs to the routine queue, as at every tag. The
  cold-start gate does not apply to it.
- An answered item on an LO with a servable episode or on a goal frontier is served by the cold-start floor or the
  frontier, as before.
- An answered item on an assumed or maintained LO keeps placement's own routing (its check, or maintenance).

## The rule

> Under placement, an active answered item with no due time, on an LO with no evidence, **starts as learning**: it
> is new material, as a never-attempted item would be.

This follows how scheduling already treats unevidenced work. An answer that set no review and gave the LO no
evidence demonstrated nothing, so the LO is where it was before the answer, which is learning. Nothing counts as
demonstrated: `last_evidence_at` stays empty, and mastery, facets and FSRS state are untouched.

Two holds keep the return from undoing what made the answer unevidenced. Like placement's own first-review check,
the item is picked outside the routine timing, so it takes the exclusions any selector outside the scheduler's
timing takes (`serving_exclusions.out_of_timing_serving_exclusions`):

- it waits while an open cold follow-up holds it;
- it waits for the cold retrieval delay (`COLD_RETRIEVAL_DELAY`) after its answer was last shown, so a primed
  answer's item does not come back in the session that showed the answer.

Both holds are existing rules. The change adds no weight, margin, threshold or constant.

The daily plan follows the scheduler. A returned item (one with the `unevidenced_return` component) takes the
plan's "new" lane ("back as learning") and is admitted and counted as new material (`PoolItem.counts_as_new`),
under the same load ceiling and daily cap. Without that, the plan would put it in "later" and Today would never plan
it. An open diagnosed problem on its LO still sends it to the repair lane first, as for any attempted item.

The rule acts only where `placement.state.unevidenced_return_active` is true: at the tag, with the switch on, and
only where opening episodes are ignored, so `placement.initial_probes = true` still gives the predecessor's serving.

## The successor

- **Tag** `mvp-0.56` (`UNEVIDENCED_RETURN_ALGORITHM_VERSION`, ONE constant), the next link after instruct/handoff's
  mvp-0.55 in `SUCCESSOR_CHAIN` since the landing merge (built on a base where mvp-0.54 was the latest; nothing was
  renamed, only pins moved: see "Landing onto main").
- **Kill switch** `[placement] unevidenced_return` (default true; registry: structural/operational). Off, below the
  tag, with placement off or with opening probes back on, every path is the predecessor's (mvp-0.55 since the landing): the gate returns false, the
  return set is empty, no component is written, and the plan's branch reads only that component.
- **Upgrade** `learnloop.unevidenced_return_upgrade`, the chain's journalled link (from mvp-0.55 since the landing, or
  from mvp-0.9 onwards through the chain). The CLI and sidecar openers install it, and `learnloop upgrade` targets it by default.
- **No migration.** The change is serving only: nothing recorded changes meaning, and no replayer, projection or
  receipt reads the rule.
- **Defaults**: every snapshot is recomputed, because the switch is a key of every effective config. Dropping the
  key reproduces every snapshot recorded on main, and mvp-0.56's snapshot differs from its predecessor's by the tag alone.
- **Receipt**: the returned item carries `components.unevidenced_return = 1.0` and the reason "back as learning: an
  earlier answer set no review and gave no evidence" in place of new material's.
- **Logged propensities** stay exact. The build computes them over the queue as it stands, so a returned item is one
  more candidate with its own propensity, and no other candidate's formula changes.

## Evidence

All runs used fresh backup-API copies (`learnloop.db.copies.copy_tree_with_databases`) in gitignored
`fixtures-local/placement/`. The per-copy counts and the names of every LO that changes are there (`evidence.json`,
`probe_hole.json`, `order_diff.json`, `shadow-*.json`, `shadow-compare.json`).

**The Nov 9 backup** (migration 250, mvp-0.54; arxiv_v2, linear_algebra, probability). Each copy was upgraded on
this branch, and queues were built with no limit at the backup's noon and again three days later, past the cold
delay.

- **Only arxiv_v2 changes.** Every LO that changes is in the hole, and the audit's LO is one of them. At the
  backup's noon nothing changes, because the answers involved were shown within the cold delay. Three days later
  they return as new material, and nothing leaves the queue. On linear_algebra and probability the queues are
  identical at both moments.
- **The switched-off successor equals the predecessor exactly** on all three copies at both moments: every queue
  row (priority, components, plain English), the plan's classified pool, and the logged slate (propensities and
  kinds) of a persisting build.
- **Knock-on changes on arxiv_v2.** Nothing else leaves the queue or changes lane. Two kinds of change follow from
  the existing new-material ordering applied to more LOs:
  1. new material is re-ordered among the slots it already holds, and a returned item takes its place by the
     existing rule;
  2. LOs that name a returned LO's concept as a prerequisite move one prerequisite layer later
     (`placement_layer` + 1), because their prerequisite is now new material.

  In the plan's pool, a returned item whose LO has an open diagnosed problem takes the repair lane; the others are
  new-material candidates.
- **The upgrade changes nothing recorded.** The upgraded database's item states equal the predecessor's.

**Shadow rebuild.** `learnloop rebuild --shadow --json` ran on a fresh upgraded copy of each vault and on a fresh
copy left at mvp-0.54. Every run exited 0 with the live hash unchanged. With the version label normalized, the
learner-state diff and the schedule effects are identical at both tags on all three copies. Where the successor's
diff lists more mastery rows, they differ only in their `algorithm_version` label. The few content changes and
earlier due dates that appear are the same at both tags: existing replay gaps, not this change.

**Owner lane.** `LEARNLOOP_OWNER_VAULTS` pointed at fresh copies of the mvp-0.35 copies in
`learnanything-ad1/fixtures-local/owner-copies-mvp035`. `test_placement_fixture_copies.py`: 12 passed.

- The test at the latest tag lost its exception: no `KNOWN_STRANDED`, no xfail.
- The audit's LO is pinned as stranded at mvp-0.54 and with the switch off. That switched-off queue equals
  mvp-0.54's row for row.
- Switching back on takes in that LO and nothing else.

## Tests

- `tests/test_placement_unevidenced_return.py`, on synthetic vaults with fakes only:
  - the chain, the defaults and the gate;
  - the shapes: a primed first answer on an only item (lost below the tag, served at it), the replay-held
    self_report state, the never-attempted sibling's own label, an answer that set a review, evidence ending the
    return, the reveal hold and its end, a cold follow-up's hold, a spent probe;
  - the switch-off path: the switch and the old tag equal mvp-0.54 row for row, and the switch on adds only the
    hole;
  - the plan: its lane, candidates and admission, and the repair lane's precedence;
  - replay: whole-vault rebuild state at both tags, and a shadow rebuild;
  - the upgrade: publishing, chaining, refusals, the openers and the CLI.
- `tests/test_placement_fixture_copies.py` (owner lane), as above.
- Version pins moved in the earlier links' tests (sets, negative chain indexes, the openers' link, the frozen
  digests that drop later keys through `drop_unevidenced_return_keys`), and in `tests/cli_surface.json`
  (`upgrade --to` default).

## Codex review

There was one read-only review (`gpt-6.1-sol`, high effort) of the whole diff against main, job
`20261109-114746-jQmVUO`. It was asked whether the change reaches beyond the hole, whether the switch-off path is
exactly the predecessor, and whether replay agrees. Codex found the switch-off paths, replay readers, the upgrade
link, the version gates and the extra exclusions read correct by inspection, with no new constant and no wrong pin.

- **F1 (medium): the change is not item-local.** A returned LO joins the shared new-material ordering and the
  plan's admission. Its dependents move a prerequisite layer later, and a returned item takes a share of the daily
  new-material cap.
  **Ruling: accepted as intended, now tested.** "Starts as learning" means new material under the existing rules.
  Keeping the predecessor's order for every other item would need a second ordering rule beside the one that
  exists. The evidence above shows the effect on the owner's copy is exactly this. New test:
  `test_a_returned_prerequisite_moves_its_dependents_one_layer_later`.
- **F2 (medium): a returned item whose LO has an open diagnosed problem goes to repair, and lost the flag.** It took
  the repair lane without `unevidenced_return`, so the staged frame would read it as acquired.
  **Ruling: fixed in part.** The plan's `PoolItem` now carries the flag whatever lane it takes, so `target_acquired`
  stays false and the plan payload shows it. Repair precedence stays: an open diagnosed problem's repair comes
  first for any attempted item, and the LO is served either way, so the hole is closed.
- **F3 (low): other candidates' exploration probabilities can change.** Adding a near-tie candidate splits the
  exploration share among more alternatives.
  **Ruling: documented, no code change.** The logged probabilities stay exact: they are the true design
  probabilities of the queue as built. Freezing the old values would make them wrong. On the owner's copies every
  slate row is a composed offer with no scheduler propensity (`unavailable_composed_offer`), and the switched-off
  slate equals the predecessor's.
- **F4 (low): the regression test compared component keys, not values, and the plan test used a handmade item.**
  **Ruling: fixed.** With the switch on, every row other than the returned item now equals the predecessor's value
  for value. The plan test now runs real scheduler output through `_classified_pool` and checks that the
  switched-off pool and candidates equal the predecessor's.

While fixing F4 I found a pre-existing test-isolation bug. Under xdist the value-for-value comparison failed
intermittently: `scheduling/selection_rewards._SHAPE_CACHE` is keyed on `id(vault)`, so a vault object built later
in a worker can reuse a freed vault's id and read another vault's item shapes. The comparison tests clear that cache
before each build. The cache itself is left for its own change.

## What is untested

- **Adaptive difficulty choosing a returned item.** AD's slot candidates must be members of the plan's admitted new
  material, which now includes returned items, but no test drives AD's draw onto one. AD's own fresh-item receipts
  read "never attempted" from attempts, so they do not treat a returned item as fresh.
- **The phone (a device filter) serving a returned item.** The device gate is unchanged and applies after placement.
- **The router's staged frame and the LLM policy seeing a returned item.** Only `target_acquired` changes (false for
  a returned item, as for new material). No test drives the router over one.
- **Long-run behaviour.** After the returned item's next unprimed answer, it gets a review and its LO gets evidence,
  and the rule stops applying. This is tested on a synthetic vault only.

## Landing onto main

Landed onto main `0a6e8bda4e` (instruct/handoff's mvp-0.55, Decider v1.2, the test-suite audit, the refactor docs)
by merge `a121b50fc6`, references regenerated in `f60df0bb89`.

**The merge.** The chain is now mvp-0.54 -> mvp-0.55 (IH5's failure share) -> mvp-0.56. The upgrade link's
predecessor is `failure_share_upgrade`; every gate stays "mvp-0.56 or later" (`UNEVIDENCED_RETURN_VERSIONS`), so with
the switch off or below the tag serving is mvp-0.55's. All 47 defaults snapshots were recomputed from the merged tree
(`defaults_fingerprint_for_version`). The frozen-digest tests keep every normalization from both sides
(`drop_ih5_keys`, the 40 s router wait reset to 8.0, `undo_decider_v12`, `drop_unevidenced_return_keys`). Version pins
moved so the latest tag is mvp-0.56; the pin conflicts and slice indexes were resolved by script (exact patterns), the
rest with the editor. `tests/cli_surface.json`'s `upgrade --to` default is mvp-0.56. The new module joins the
experiments-isolation import contract beside IH's. The references were regenerated, not hand-merged; two prose leaf
counts (1192 -> 1193) were fixed by hand.

### Gate

| Step | Result |
|---|---|
| Targeted tests (204 files: placement, plan, every successor/upgrade, frozen-digest and defaults files, the IH tests, CLI surface and JSON, architecture, registry audit, public-tip guards) | first run 15 pin failures (merge slices and sets), fixed; the 15 files again: 329 passed, 6 skipped, 1 xfailed |
| `lint-imports --no-cache` | 43 kept, 0 broken |
| `db_generate_reference` / `db_validate_reference` | regenerated; errors `[]` (1193 configuration leaves) |
| `module_generate` / `module_validate` | 1261 module notes; PASS |
| `desktop_generate` / `desktop_validate` | 328 TS/TSX + 6 Rust; passed, reproducible |
| `validate_vault.py` | passed (2260 notes) |
| Config fingerprints | all 47 snapshots recomputed; the recomputation is idempotent |
| `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | ok |
| Full pytest (`-n 8 --dist worksteal`) | 30803 passed, 97 skipped, 47 xfailed, **2 failed, both reproduced on main `0a6e8bda4e` itself** (below) |
| Durability lane (`-m durability -n 4`) | 417 passed, 1 skipped |
| Owner lane on fresh backup-API copies of `owner-copies-mvp035` | 91 passed, 4 skipped, 0 xfailed (main: 87 passed, 4 skipped, 1 xfailed; this change removes that xfail) |
| Desktop / phone | no file under `apps/` changed: not run |

The two full-suite failures, each rerun alone 3 times on this branch and 3 times on a clean export of main:

- `test_codex_lockdown_round3.py::test_every_process_launch_site_is_approved`: fails 3/3 here and 3/3 on main. The
  unreviewed launch sites are `scripts/refactor_measures.py` (`main`, `subprocess.run`), which main added (S0/Z2,
  `db2c92aeda`) and this branch does not touch. It needs a launch-site review on main. It is not approved here.
- `test_ro5_stop_coin.py::test_serving_records_each_coin_with_its_exact_probability_and_availability`: flaky, 1/3
  fails here and 1/3 on main (a recorded probability rounded to 6 places against the exact one). It is not this
  change.

### Smoke

In-process, on fresh backup-API copies of the Nov 9 backup (migration 250, mvp-0.54) in gitignored
`fixtures-local/landing-placement-smoke/`. Each copy was opened (migration 251) and upgraded: with main's code to
mvp-0.55 (`m55`), and with this branch to mvp-0.56 (`u56`; `off` is `u56` with `[placement] unevidenced_return =
false`). Every AI route of each tree points at 127.0.0.1:9; the router LLM, the Decider, grading and diagnosis, the
FG1 author and the lesson writer are the tests' in-process fakes. A socket guard logs every connection and refuses
any that is not loopback. The drivers reuse the IH landing's (read-only copies).

1. **Identity first: the switch off at mvp-0.56 equals main at mvp-0.55.** Set aside, on both sides alike: the
   version label (mvp-0.55 / mvp-0.56) and the switch key `unevidenced_return` wherever a config record carries it.
   The numeric policy's seed key drops its version field on both sides, as at earlier landings.
   - Scheduler queue (no limit) and the plan's classified pool and new-material candidates, at the backup's noon and
     three days later: equal on all three vaults at both moments.
   - A served day at 2026-11-12 15:00 (the second item missed, FG1's follow-up authored, the first stop declined,
     the mixture seed pinned): Today, the plan, every step, every submit and feedback, the router LLM and Decider
     requests, the gates, the traces, and every written row are identical on arxiv_v2 (16 served), linear_algebra
     (7) and probability (4).
2. **The change.** On arxiv_v2, at the backup's noon nothing changes (the answers were shown within the cold
   delay). Three days later the two stranded LOs' items return (`unevidenced_return = 1.0`): one takes the plan's
   "new" lane and joins the new-material candidates, the other (an LO with an open diagnosed problem) takes the
   repair lane. Nothing leaves the queue and no lane changes. The only other movement is the recorded knock-on: 12
   new-material rows move one prerequisite layer later (`placement_layer` + 1), with equal priorities. The served day
   at mvp-0.56 serves the returned repair item. linear_algebra and probability are unchanged at both moments, and
   their served days at mvp-0.56 equal main's.
3. **IH on a returned LO's topic** (arxiv_v2, 2026-11-12 15:00). The returned item was missed at mvp-0.56, and main
   at mvp-0.55 missed a never-returned item at the same position. Both behave the same way. `plan_interrupt` holds
   `insert_now` beside the lesson offer in one logged draw, with the same support and propensity (0.1181) for the
   offer. The offer is the step right after feedback, `offer_shown` is written, and Start opens the lesson with
   `sources_follow` recorded. With `insert_now` drawn, FG1 writes the follow-up on the returned LO's topic and opens
   it. The boundary `followup_contest` decision was not reached by either tree in these scenarios (the follow-up
   opens at once), so it was neither exercised nor changed.
4. **Protection.** Both returned items were exam-reserved (an unreleased `exam_pool_items` row; learner protection
   reads "exam or held-out material") on one copy, and held by a pending cold check ("a check waiting in the app") on
   another. Then neither is in the queue, the plan's pool or the candidates, and neither is served in a 90-minute day
   (12 and 13 items served).
5. **`rebuild --shadow`** on fresh copies of m55, u56 and u56 after its served day, for all three vaults: exit 0 and
   live unchanged every time. linear_algebra and probability show stamp-only mastery rows. arxiv_v2 shows
   stamp-only mastery rows plus the pre-existing rows the IH landing noted: two mastery rows
   (`lo_render_a_classifier_s_decision_regions`, `lo_trace_recursive_relu_folding`) and nine `pi_lesson_*` due dates.
   They are the same at mvp-0.55 on main and at mvp-0.56 here. Nothing beyond them.
6. **No real model call, no network.** Every receipt written by every smoke run is a fake's (`fake_decider`,
   `fake_llm`, `fake`), so 0 are from a real model. The socket log shows no non-loopback connection and no name
   lookup.

### Owner steps

1. Restart the desktop app and the phone host.
2. Upgrade each vault to mvp-0.56: `learnloop upgrade --vault <path>` (the default target; from mvp-0.55, or from
   mvp-0.9 onwards through the chain).
3. To turn it off: `[placement] unevidenced_return = false` (serves mvp-0.55 exactly).

### Open items

- The `selection_rewards._SHAPE_CACHE` `id(vault)` bug stays a separate item.
- Main's `scripts/refactor_measures.py` launch sites need a lockdown review (the persistent full-suite failure above).
- `test_ro5_stop_coin`'s rounding flake, on main as here.
