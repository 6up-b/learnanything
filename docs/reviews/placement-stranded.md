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

- **Tag** `mvp-0.56` (`UNEVIDENCED_RETURN_ALGORITHM_VERSION`, ONE constant), the next link after mvp-0.54 in
  `SUCCESSOR_CHAIN`. Instruct/handoff claims mvp-0.55 and lands first. The chain has skipped a label before
  (mvp-0.28). When IH lands, its merge puts mvp-0.55 between the two links; nothing here is renamed, only pins move.
- **Kill switch** `[placement] unevidenced_return` (default true; registry: structural/operational). Off, below the
  tag, with placement off or with opening probes back on, every path is mvp-0.54's: the gate returns false, the
  return set is empty, no component is written, and the plan's branch reads only that component.
- **Upgrade** `learnloop.unevidenced_return_upgrade`, the chain's journalled link (from mvp-0.54, or from mvp-0.9
  onwards through the chain). The CLI and sidecar openers install it, and `learnloop upgrade` targets it by default.
- **No migration.** The change is serving only: nothing recorded changes meaning, and no replayer, projection or
  receipt reads the rule.
- **Defaults**: every snapshot is recomputed, because the switch is a key of every effective config. Dropping the
  key reproduces every snapshot recorded on main, and mvp-0.56's snapshot differs from mvp-0.54's by the tag alone.
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
