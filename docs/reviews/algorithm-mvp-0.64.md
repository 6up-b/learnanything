# mvp-0.64: an untaken repair episode ends (refactor step K9.4)

Branch `refactor/k9.4-untaken-episode`, from origin/main `ef403d953d` (latest tag `mvp-0.63`). Ledger row R1-2: a
remediation episode whose primed attempt is never taken had no end (no task, no expiry, nothing wrote `abandoned`),
so the routine queue withheld its reserved cold item only while a cold retry stood open, and the item's protection
rested on another record. The owner decided on 2026-11-20 (K9-Q1, option b) that such an episode ends when the
item's next ordinary review comes due. The design is the K9 strategy's K9.4 entry
(`docs/reviews/k9-diagnosis-strategy-2026-11-14.md`, Q1 row, findings row 4, §9 item 1). Everything below was
measured on synthetic vaults; the owner's vaults are the orchestrator's (the last sections).

| Commit | What |
|---|---|
| `d0bdb1b531` | Characterization: below the coming tag an untaken episode never ends, and the routine queue serves its cold item |
| `38867c61b9` | The tag: one constant, the chain entry, its set and predicate, one upgrade row, one test row; the mechanical moves by the tag string |
| `7bb977b804` | No behaviour change: `IntentServing.effective`'s computation becomes `recall_targets.item_effective_due`, and `recall_targets.ordinary_due_reader` reads it outside the queue build |
| `6c4bb1b3ee` | The behaviour: the sweep ends an untaken episode at its item's review; the routine exclusions read the episode's state; tests; the structure ratchet's one raised line |
| (this record) | This record, the G2 design renumbered to `mvp-0.65`, ledger row R1-2 |

No migration (`abandoned` is in the CHECK since migration 058), no config key, no kill switch, no prompt change. No
change to cold retries, their expiry or withdrawal, to the primed binding, or to any other serving rule.

## The rule

At `mvp-0.64` or later, the per-attempt sweep (`sweep_machine_checks`, `diagnosis/machine_checks.py:236`, beside
`sweep_expired_cold_retries` at `:228`, in its own guarded block) calls `end_untaken_episodes`
(`diagnosis/remediation.py`, beside `withdraw_cold_measurement`). For every episode in `prescribed` or `treatment` with `primed_attempt_id IS NULL`
(`Repository.untaken_remediation_episodes`), it resolves the episode's item and ends the episode when that item's
next ordinary review has come due.

- **The item** is the practice item of the miss the episode repairs: for a `diagnosis` case its hypothesis's
  `attempt_id`; for a `misconception` case the newest attempt whose error events fed it
  (`attempt_ids_for_misconception`, with the misconception's `source_error_event_ids`); in both, only an attempt
  made at or before the episode's `created_at` (a later miss is a later diagnosis).
- **Due** is the read the plan and the queue use, `IntentServing.effective(item, state).due`
  (`scheduling/intent/serving.py:322`): the stored `due_at` at the 0.90 recall target, else §5.3's scaled due,
  compared with the sweep's clock (`due <= now`). This is the due gate `build_due_queue` applies through
  `effective_due_or_none` and `_forgetting_risk`, and the effective due `review_population` reads for the plan. No
  constant and no grace period. The sweep cannot build an `IntentServing` view (it imports the queue build, which
  would pull the scheduler into diagnosis's import cycle), so the computation `IntentServing.effective` ran is now
  one function, `recall_targets.item_effective_due`, which `IntentServing.effective` calls unchanged in behaviour
  (same 0.90 shortcut, same lazy anchor read, the same fallbacks counted), and `recall_targets.ordinary_due_reader`
  feeds it the same inputs (the covering commitments' recall target through `Resolution`, `resolve_fsrs_weights`,
  `load_anchors`). It leaves out only the build's fold of answered "Check once" commitments to `satisfied`, which
  changes a commitment's disposition and never the recall target an item resolves to (`Resolution._resolve` takes
  the target from the decider's or an active `help_me_remember` control's depth preset).
- **Or the review already happened**: the item has an attempt after the episode's `created_at` that wrote its FSRS
  state (`fsrs_eligible`, not held for review: the plan's anchor definition, `intent_reads.attempts_since` +
  `held_for_review_attempts`). The sweep runs only after attempts; without this arm, a learner whose first attempt
  after the item fell due is that item's own review moves the due date before the sweep looks, and the episode
  would live on to the review after (test `test_an_ordinary_review_taken_the_moment_it_fell_due_ends_the_episode`).
  A primed answer on the item writes no FSRS state and ends nothing.
- **Ending** is one guarded UPDATE (`Repository.abandon_untaken_remediation_episode`): `state = 'abandoned'`,
  `updated_at = now`, `WHERE state IN ('prescribed','treatment') AND primed_attempt_id IS NULL AND NOT EXISTS (open
  cold_retry task)`. That is the state and timestamp the release of a withdrawn retry writes
  (`_release_cold_reservation`, reached from `withdraw_cold_measurement`, `diagnosis/remediation.py:1473`), and it
  frees the cold item in every reservation reader, which all read the episode's state. `completed_at` and
  `cold_item_id` are left as they are (as the release leaves them). The event is recorded the way the episode's other
  transitions are: the row's state and `updated_at`, plus an info log line naming the episode, the item, the prior
  state and the cold item.
- **Untouched**: an episode whose primed attempt was taken (it is `cold_scheduled`, or `treatment` after a
  schedule refusal), and an episode in `diagnosis`, `cold_scheduled`, `completed` or `abandoned`. A primed attempt
  that binds between the read and the UPDATE keeps the episode (the guard is re-read in the UPDATE).
- **Idempotent**: a second sweep finds the episode `abandoned` and writes nothing (the test compares the whole row).
- **Stays open**: an episode whose item cannot be resolved (no hypothesis or misconception, no diagnosing attempt at
  or before it opened), or whose item has no review date and no review since it opened. There is no date to end it
  by; the owner-copy count below says how many there are.
- **Below the tag** nothing changes: `end_untaken_episodes` returns at once, and the routine queue keeps the
  narrower set.

### Why the item is the missed item (judgment call)

"The item" in the decision is not named further. Three readings exist: the missed item, the primed item and the
cold item. The cold and primed items fail for many episodes: a `prescribed` episode has chosen neither, and the
ranking that picks them prefers never-attempted items (`_rank_items`: last attempt `""` sorts first), which have no
review date at all, so such episodes would still never end, and with the wider routine set their cold item would be
withheld from Today's queue for good, a regression on today. The missed item exists for every episode the rule
covers, its miss gave it a review date the scheduler holds, and it is the item the guided redo primes. If the owner
meant the cold item, the change is `episode_item_id` alone (and episodes whose cold item has no date need a rule).

## The serving exclusion, before and after

| | Below `mvp-0.64` (unchanged) | At `mvp-0.64` |
|---|---|---|
| `routine_serving_exclusions` (`scheduling/serving_exclusions.py:121`; read by `build_due_queue`, the plan engine, the phone and desktop queues, `explain_practice_item`/`why`, intent feasibility) | `pending_remediation_cold_item_ids()`: a live episode's cold item only while a cold retry is `pending` or `served` | `open_remediation_cold_item_ids()`: also while the episode waits for its primed attempt (from the moment it chooses the cold item until the sweep ends it, the primed attempt is taken, or the episode otherwise finishes) |
| `out_of_timing_serving_exclusions` (`find_practice`, quick check, practice admission, AD's slot check) | the wider set | the wider set (unchanged); it now releases at the sweep's end too |
| After the episode is `abandoned` | served as an ordinary item | served as an ordinary item |

The routine gate's reason code stays `cold_check_reserved`. Both sets are the one query
`_remediation_cold_item_ids`; the tag picks which reader.

## Playbook ruling

The playbook's test (step 1): "Decide whether the change alters persisted meaning." It does: the sweep writes a new
terminal state on episodes that previously stayed open, and which items routine serving admits changes. The recorded
rule of 2026-10-17 applies directly: "a change to which items are served as measurements, or to which new attempts
are primed, is a successor ... even when replay is unchanged". So a tag: `mvp-0.64`, the immediate successor of
`mvp-0.63`, by the playbook (step 3) and without a kill switch (the 2026-11-16 rule).

- `UNTAKEN_EPISODE_END_ALGORITHM_VERSION = "mvp-0.64"`, appended to `SUCCESSOR_CHAIN`;
  `UNTAKEN_EPISODE_END_VERSIONS = successors_from(...)`; the one predicate `untaken_episode_end_on(config)`, read by
  the sweep and by `routine_serving_exclusions`.
- `Link(UNTAKEN_EPISODE_END_ALGORITHM_VERSION, idempotent_projection)` in `UPGRADES`: only sweeps after the upgrade
  behave differently. `remediation_episodes` and `followup_tasks` are `WORKFLOW` tables (`db/table_roles.py`), never
  rebuilt, so no replay touches the new writes, and nothing derived from history moves.
- One test row in `tests/test_upgrades.py`'s `EXPECTED_ACTIVATIONS`.
- Future events only: an episode open when a vault upgrades is ended by the first sweep after the upgrade, dated by
  that sweep, never back-dated to the review date that passed below the tag
  (`test_an_episode_open_at_the_upgrade_is_ended_by_the_first_sweep_after_it`).

## Pins and goldens that moved

- **The tag commit, by the tag string alone** (as at mvp-0.62 and mvp-0.63): `tests/goldens/identities.toml` nine
  pins (`A1-A4.manifest_hash.init`, `C3.boundary.init`, `C3.boundary_offer.init`, `C3b.chooser`,
  `C3b.chooser_offer`, `C3b.start_key`, `C3b.start_key_offer`, `C5.init`, `C6.init`: the same nine mvp-0.63 moved),
  regenerated with `tests/test_identity_pins.py --write`; `tests/goldens/effective_defaults.toml` (the algorithm line,
  `--write`); `tests/cli_surface.json` (`upgrade --to`'s default, edited by hand); `tests/goldens/placement_stored_misses.json`
  (its manifest's tag); `tests/fixtures/diagnosis_journey_golden.json` (311 tag strings and its two decision states'
  `config` and `snapshot_hash`, nothing else; `DIAGNOSIS_JOURNEY_WRITE_GOLDEN=1`); latest-tag and chain-position pins in
  40 earlier successors' test files: every negative `SUCCESSOR_CHAIN[-n]` index one further (`grep -n
  "SUCCESSOR_CHAIN\[-" tests/`, `tests/test_curriculum_c1_landing.py`'s `[-27:-24]` among them), `mvp-0.64` appended to
  tails and to the version sets that include every later tag (`COMMITTED_CHECK_DELIVERY_VERSIONS`,
  `SECTION_END_VERSIONS`, `FACET_BELIEF_FIX_VERSIONS`, `FIGURE_WAIT_VERSIONS`, `FAILURE_SHARE_VERSIONS`), the fresh-vault
  tag in `test_ad23_successor`, `test_serve_eligibility_review` and `test_intent_codex_rereview`.
- **The behaviour commits**: no identity pin moved and none was added (an episode's state is no compared identity).
  One structure number rose: `modules_in_an_import_cycle` 220 to 221, edited by hand in `tests/goldens/structure.toml`
  (with a comment; `--write` would have rewritten unrelated drifted lines). The new member is
  `learnloop.scheduling.intent.recall_targets`: it already imports `diagnosis.causal_activity_policy`, a member of
  the repair lane's 20-module cycle, and `diagnosis.remediation` (a member too) now imports it for the due read.
  Any module the sweep reads the plan's due from joins that cycle; a first build with the rule in two new modules
  added two members and merged the repair cycle into the scheduler's (largest component 84 to 143), which is why
  the code sits in `remediation.py` and `recall_targets.py`. No other golden moved.
- **Assertions changed**:
  - `tests/test_k1_remediation_cold_reservation.py::test_the_routine_due_queue_withholds_a_cold_item_only_while_its_check_is_pending`
    pinned the narrower routine set at the head tag; it is now pinned at `mvp-0.63` and renamed
    `test_below_mvp_0_64_the_routine_due_queue_withholds_a_cold_item_only_while_its_check_is_pending` (its assertions
    are unchanged; the at-tag behaviour is in the new file).
  - `tests/test_protection_surface_matrix.py`: the `6.remediation` row's `RT` cell (routine serving of a `treatment`
    episode's cold item before its primed attempt) moves `S` to `W`, now equal to its `OT` cell, which is the change
    the ledger row asked for.
  - `tests/test_section_end.py::test_the_tag` and `tests/test_check_credit_activation.py::test_the_tag`: their tag is
    now `SUCCESSOR_CHAIN[-2]`/`[-3]` and their version sets include `mvp-0.64` (the tag commit's mechanical moves).

## Tests, with fail-first evidence

`tests/test_untaken_repair_episode.py` (new, 18 tests):

| Test | Below the tag | At the tag |
|---|---|---|
| `test_below_the_tag_an_untaken_episode_stays_open_past_its_items_review[prescribed, treatment]` | open after sweeps a minute and sixty days past the item's review | (below-tag arm) |
| `test_below_the_tag_the_routine_queue_serves_an_untaken_episodes_cold_item` | queued at opening and after the review date; the wider set holds it | (below-tag arm) |
| `test_the_tag` | predicate off at mvp-0.63 and with no config | on at mvp-0.64 |
| `test_at_the_tag_an_untaken_episode_ends_once_its_items_review_is_due[prescribed, treatment]` | | open a minute before the review; `abandoned` a minute after, `updated_at` = the sweep, `completed_at` NULL, cold item kept; a later sweep leaves the row byte-equal |
| `test_at_the_tag_the_routine_queue_withholds_the_cold_item_while_the_episode_is_open` | | withheld (`cold_check_reserved`) until the review; queued after the sweep ends the episode |
| `test_an_ordinary_review_taken_the_moment_it_fell_due_ends_the_episode` | | the review moved the due date; the sweep still ends the episode |
| `test_a_primed_answer_on_the_item_is_no_ordinary_review` | | a primed answer moves no due date and ends nothing |
| `test_an_episode_whose_primed_attempt_was_taken_is_untouched` | | `cold_scheduled` row byte-equal after a sweep past due |
| `test_an_episode_in_any_other_state_is_untouched[diagnosis, cold_scheduled, completed]` | | byte-equal |
| `test_a_diagnosis_case_ends_at_its_hypothesis_attempts_item` | | ends at the hypothesis attempt's item's review |
| `test_an_episode_whose_item_cannot_be_resolved_stays_open` | | open sixty days on |
| `test_an_episode_open_at_the_upgrade_is_ended_by_the_first_sweep_after_it` | open past due at mvp-0.63 | ended by the first sweep at mvp-0.64, dated by it |
| `test_the_sweeps_due_read_is_the_plans[0.9, 0.8]` | | `ordinary_due_reader` equals `IntentServing.effective(...).due` for every item, at the stored target and at a scaled one (where it differs from the stored date) |

Fail-first: the characterization commit's three tests passed at the base (3 passed). The whole file run on the tip
with the four behaviour files (`db/stores/remediation.py`, `diagnosis/machine_checks.py`, `diagnosis/remediation.py`,
`scheduling/serving_exclusions.py`) checked out from `7bb977b804` and restored afterwards: 6 failed, 12 passed. The six
are the two ending arms, the routine-queue arm, the review-taken arm, the diagnosis-case arm and the upgrade arm
(`assert 'prescribed' == 'abandoned'`, `assert 'treatment' == 'abandoned'`, `assert not True`); the twelve that pass
are the three below-tag arms, `test_the_tag`, the five that assert nothing changes, the unresolvable episode and the
two due-read equivalence cases. With the behaviour: 18 passed. (A first draft's "a hinted answer is no review" test
was wrong: a hinted answer writes FSRS state at this tip, so it is a review; the test now uses a primed answer.)

## Commands and results

Every pytest run went through a script file with explicit targets, `-q -n 1 -p no:cacheprovider`, in a 3G memory
scope under the scratch wrapper (`env -i`, empty `HOME`/`CODEX_HOME`, isolated config dir).

| Run | Result |
|---|---|
| Characterization at the base (`tests/test_untaken_repair_episode.py`, 3 tests) | 3 passed |
| Tag commit's own files (47: the moved successor files, identity pins, effective defaults, CLI snapshot, placement, journey golden, upgrades, the c1 landing pin), `-m "not arc_close"` | 1266 passed, 12 skipped, 3 xfailed |
| Fail-first (behaviour files from `7bb977b804`) | 6 failed, 12 passed |
| `tests/test_untaken_repair_episode.py` at the tip | 18 passed |
| The brief's name filter over `scripts/affected_tests.py`'s 1,374 files (remediation, cold_retry, serving_exclusion, causal, sweep, intent_exclusion, due_queue, diagnosis_journey, upgrades, successor, algorithm_version, effective_defaults), united with the files naming `remediation_episode`, `start_remediation_treatment`, `routine_serving_exclusions`, `exclusion_now`, `cold_check_reserved`, `pending_remediation_cold_item_ids`, `open_remediation_cold_item_ids`, `sweep_machine_checks`, `cold_item_id`, `recall_target`, `effective_due`, `intent_serving`, `IntentServing`, plus the matrix and the ratchets: 103 files, three chunks, `-m "not arc_close"` | 869 passed, 5 skipped; 749 passed, 3 skipped; 496 passed (2 failed: the new equivalence test's config lacked the other recall-target keys, fixed: 18 passed alone) |
| Every test file naming `SUCCESSOR_CHAIN` or `LATEST_ALGORITHM_VERSION` not in the filter, with identity pins, ratchets, effective defaults, CLI snapshot, kill switches, sqlite copies, public tip guards, retired config identities, journey golden: 110 files, three chunks, `-m "not arc_close"` | 1264 passed, 18 skipped, 2 xfailed; 616 passed, 4 skipped, 1 xfailed; 573 passed |
| `test_identity_pins`, `test_structure_ratchets`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies`, `test_public_tip_guards`, `test_upgrades`, `test_untaken_repair_episode`, `test_k1_remediation_cold_reservation`, `test_protection_surface_matrix`, `test_retired_config_identities`, `test_diagnosis_journey_golden` | 877 passed |
| `tests/test_test_layout.py` alone | 3 passed |
| `tests/test_architecture.py` alone | 18 passed |
| `uv run ruff check` | All checks passed! |
| `uv run lint-imports --no-cache` | Contracts: 45 kept, 0 broken. |
| `uv run python scripts/check_gate_partition.py` | collected 32880: landing 32814 + arc_close 66 |
| The owner-copy counts script and the one-sweep command, on a fresh `learnloop init` vault | `{"algorithm_version": "mvp-0.64", "untaken": 0}`; `0` |

The structure ratchet failed once on the first build of the rule (two new modules: largest import component 84 to
143, modules in a cycle +2); the rule was moved into `remediation.py` and `recall_targets.py` (above).

## What the orchestrator must run on owner copies

On backup-API copies (never a live vault), before and after `learnloop upgrade --to mvp-0.64` (each copy at
`mvp-0.63` after mvp-0.63's landing). The counts script (counts only, read-only: attaches the database read-only,
writes nothing, calls no model) is below; run it with the scratch wrapper's isolation (`env -i`, empty `HOME` and
`CODEX_HOME`) as `uv run python <script> <copy root> [<ISO instant>]` from the landed tip:

```python
import json, sys
from collections import Counter
from pathlib import Path
from learnloop.clock import SystemClock, parse_utc
from learnloop.db.repositories import Repository
from learnloop.diagnosis.remediation import episode_item_id, review_came_due
from learnloop.scheduling.intent.recall_targets import ordinary_due_reader
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

vault = load_vault(Path(sys.argv[1]))
now = parse_utc(sys.argv[2]) if len(sys.argv) > 2 else SystemClock().now()
repository = Repository.attach(VaultPaths(vault.root, vault.config).sqlite_path, read_only=True)
episodes = repository.untaken_remediation_episodes()
due_read = ordinary_due_reader(vault, repository)
counts = Counter()
for episode in episodes:
    state = str(episode["state"])
    counts[f"untaken_{state}"] += 1
    counts["with_cold_item" if episode.get("cold_item_id") else "without_cold_item"] += 1
    item_id = episode_item_id(repository, episode)
    if item_id is None:
        counts["item_unresolved_stays_open"] += 1
    elif review_came_due(repository, item_id, opened=str(episode["created_at"]), now=now, due_read=due_read):
        counts[f"first_sweep_ends_{state}"] += 1
    else:
        counts[f"stays_open_until_due_{state}"] += 1
print(json.dumps({"algorithm_version": vault.config.algorithms.algorithm_version, "untaken": len(episodes),
                  **dict(sorted(counts.items()))}))
```

1. Per copy, the counts: open untaken episodes by state, with and without a cold item, how many the first sweep at
   the tag would end now, how many stay open until their item's review, how many stay open because their item cannot
   be resolved.
2. `learnloop upgrade --vault "$COPY" --to mvp-0.64`, then `learnloop doctor --vault "$COPY"`.
3. The first sweep, on the upgraded copy only: `uv run python -c "import sys; from pathlib import Path; from learnloop.db.repositories
   import Repository; from learnloop.diagnosis.remediation import end_untaken_episodes; from
   learnloop.vault.loader import load_vault; from learnloop.vault.paths import VaultPaths; v = load_vault(Path(sys.argv[1]));
   print(len(end_untaken_episodes(v, Repository.attach(VaultPaths(v.root, v.config).sqlite_path))))" "$COPY"`
   (writes the copy's `remediation_episodes` only), then the counts script again: the number ended must equal the
   first run's `first_sweep_ends_*` total (at a close instant), and `untaken` must fall by it. `learnloop why
   item:<cold item>` on the copy before the upgrade and after it shows `cold_check_reserved` appear for each
   `with_cold_item` episode still open, and disappear for each one the sweep ended.
4. Report counts only. If `item_unresolved_stays_open` is not zero, those episodes keep today's open-ended life and,
   at the tag, their cold item is withheld from Today's queue until they end otherwise: say how many.

## The owner-copy lane, as run (2026-11-21; counts only)

Backup-API copies of the owner's three vaults in a gitignored directory, with this branch, each upgraded to
`mvp-0.63` first; the copies were deleted afterwards and the live databases' SHA-256 were unchanged.

| | arxiv_v2 | linear_algebra | probability |
|---|---|---|---|
| Untaken episodes at `mvp-0.63` | 1 (`prescribed`, no cold item) | 2 (`treatment`, each with a cold item) | 1 (`treatment`, with a cold item) |
| Of them, the first sweep would end | 0 | 2 | 0 |
| Stay open until their item's review is due | 1 | 0 | 1 |
| Item cannot be resolved | 0 | 0 | 0 |
| `learnloop upgrade --to mvp-0.64` | upgraded | upgraded | upgraded |
| Shadow rebuild: mastery, facet and schedule VALUES that differ | 0 | 0 | 0 |
| The first sweep ended | 0 | 2 | 0 |
| Untaken episodes after the sweep | 1 | 0 | 1 |
| A second sweep ended | 0 | 0 | 0 |
| `integrity_check`; `foreign_key_check` | ok; 0 rows | ok; 0 rows | ok; 0 rows |

So on the owner's data the first sweep after the upgrade ends two long-open episodes in one vault and frees
their two reserved questions for ordinary practice; in the other two vaults one episode each stays open until
its missed question's review comes due, and from the tag its reserved question (where it has one) is withheld
from routine practice until then. No episode is unresolvable.

## Judgment calls to read first

1. **The item is the missed item** (above). The decision text names "the item"; this is the only reading under which
   every covered episode has a date.
2. **"Or its review was taken since the episode opened."** Added so the per-attempt sweep cannot miss a review taken
   the moment it fell due. Any FSRS-writing attempt counts, including one the learner asked for before the due date.
3. **No cold-measurement decision is written.** The episode's cold-measurement opportunity (made at treatment) stays
   undecided, as a withdrawal-released episode leaves it; none of the decision values (`scheduled`, the refusals,
   `learner_declined`) is true of an untaken episode, and the bounds forbid new values.
4. **Unresolvable episodes stay open**, and at the tag their cold item is withheld from routine serving while open.
5. **The sweep's timing.** It runs after attempts and after a diagnosis, never on a timer or a queue build, so an
   episode ends at the first attempt after its item falls due. A learner who opens Today and answers nothing sees the
   cold item withheld until some attempt runs the sweep. If the cold item is itself the missed item (a small LO where
   nothing else had an independent surface), it stays withheld while due until any other attempt.
6. **A diagnosis delayed past the miss's review date** ends its episode at the first sweep after it opens.

## What was not verified

- The owner's vaults: no copy opened (the orchestrator's lane, above).
- The desktop, the phone and the TUI: no app run; no UI string changed, and `why item:` names the existing code.
- The full suite and the durability lane: only the sets listed above.
- That every reader of `routine_serving_exclusions` wants the wider set at the tag: by the ledger row, not by a walk.
- The counts script on a vault that holds untaken episodes: run only on an empty fresh vault; its two functions are
  the ones the tests drive.
- The durability lane (WAL, production pragmas): the new UPDATE is one statement in its own commit, like the release.
