# mvp-0.77: the probe router's fix round 3

The successor of mvp-0.76 for the findings of the probe router's re-review (2026-11-26; record
`docs/reviews/algorithm-probe-router.md`, "Fix round 3"; ledger rows G2-R21 onward, finding n is G2-R(20+n)) that
change a logged propensity, a stored decision's meaning or what an episode administers. One constant
(`PROBE_ROUTER_FIXES_ALGORITHM_VERSION` in `algorithm_versions.py`, read through `probe_router_fixes_on`), one upgrade
row (`ops/upgrades.py`: an idempotent projection, since only decisions made after the upgrade behave differently and
replay runs no decision policy), one test row (`tests/test_upgrades.py`). No migration. Below the tag every answer is
mvp-0.76's. Owner rule: a logged propensity is exactly the served distribution.

## What changes at the tag

- G2-R25 (finding 5): a head a standing router pin forces is logged with probability 1 and its decision recorded.
  Up to mvp-0.76 the live queue promoted the probe router's pin after the composition, and the offer's probability
  calculation (`_support_outcomes`, `_composed_head_probability`) recomposed each near-tie outcome without that
  promotion: when the recomposed heads agreed by chance the forced head logged its sampled share (0.5 in the test),
  and when they differed `OfferHeadMismatch` was caught and the offer went out without a decision. From the tag the
  promotion (`scheduler._router_pin_first`) runs inside `compose`, the one composition live service and every
  probability calculation share, and a head mismatch refuses the offer (`offer_not_decided`, retryable; the
  `today_offer` record names both heads). Tests: `tests/test_probe_router_fixes_mvp077.py::test_r25_*` (both
  near-tie outcomes through offer publication, both sides of the tag) and
  `tests/test_forced_withdrawal_records.py::test_a_head_mismatch_records_both_heads_and_from_mvp_077_refuses_the_offer`.

- G2-R34 (finding 14): a learned draw logs its served option's exact share. The chooser rounded any share within
  1e-12 of 1 to 1 (`router.mixture.Draw.deterministic`), read as `1.0 if drawn.deterministic else drawn.propensity`
  at five sites (the objective chooser's boundary and post-miss choice, the router chooser's block, restraint and
  follow-up restraint), so with the permitted exploration floor of 5e-13 and both policies on one arm the row logged
  1 while `served_pi` kept 5e-13 on the other arm. From the tag every site reads `Draw.logged_propensity`, which logs
  1 only when no other option has mass (`Draw.sole_option`). Tests:
  `tests/test_probe_router_fixes_mvp077.py::test_r34_*` (through the persisted learner-lane row, both sides of the tag).

- G2-R33 (finding 13, owner decision: option (a)): the probe instrument ranks on the selection objective's expected
  information over the observed posterior, with no family multiplier. Up to mvp-0.76 an instrument whose family had
  already produced an observation this episode had its ranking score multiplied by the hand-set
  `probe.block.family_redundancy_penalty` (0.6) per observation, so on the hypothesis-information fallback 0.40 ranked
  as 0.24 and lost to 0.30, and the continuation (which takes the first item) never valued the displaced question. The
  posterior the information is computed over already conditions on what that observation showed. From the tag
  `redundancy_penalty` is 1 and `ranking_basis` (`expected_information_over_observed_posterior`) is recorded in the
  selected instrument's selection components; the probe selection forecast no longer lists the multiplier as a
  parameter. The config field is retired (`config/retired.py` `RETIRED_FIELDS`: identity dumps keep their bytes, and
  a `learnloop.toml` that still sets it loads); below the tag its remembered value still ranks
  (`config.retired.retired_value`). Test: `tests/test_probe_router_fixes_mvp077.py::test_r33_*` (both sides of the
  tag). Not done here, to the gated-experiments follow-up: valuing every feasible instrument for router-owned
  episodes (the continuation still values the first-ranked one), and a family discount learned from outcomes with a
  seeded prior.

- G2-R31 (finding 11): the episode administers the lock its offer was valued on. Up to mvp-0.76 a diagnosis receipt
  with unequal support scores gave the probe candidate a support-weighted lock and the learner lane valued the offer
  on it, while entry and retarget (`enter_episode`, `retarget_episode_to_causal_factor`) locked a fresh set without the
  scores, which fell back to the verbalized or uniform prior: the pin named the candidate lock while the presentation
  froze the episode's other posterior, and revaluing the offer reproduced the original numbers. From the tag the
  learner lane's acceptance passes the candidate's lock (`valued_lock_id`) and both doors bind the episode to that row
  (`probe_episodes.valued_causal_lock`: its hypotheses, pinned versions and prior); the presentation's frozen
  posterior is the valued prior. It changes the prior (so the posteriors) of episodes opened after the upgrade; an
  existing episode keeps its lock and replay reads it as before. Test:
  `tests/test_probe_router_fixes_mvp077.py::test_r31_*` (entry and retarget, both sides of the tag).

## Fixed without the tag (same round)

- G2-R29 (finding 9): a probe router decision's "Check once" never takes a probe instrument. `measurement._arrange`
  shares no pending check touching the decision's exclusions, and the replacement an unread answer leaves reads them
  again (`measurement.decision_exclusions`) and carries them through sharing, this settlement's fresh checks and the
  new pick. Tests: `tests/test_probe_router_continuation.py::test_a_probe_decisions_measurement_never_shares_a_check_on_its_instrument`,
  `::test_a_replacement_check_keeps_the_decisions_instrument_exclusions`.
- G2-R18's residue: a facts receipt's lookup and insertion are one write transaction
  (`insert_causal_probe_decision_receipt(once=True)`), so two identical status reads at once append one receipt.
  Test: `tests/test_probe_router_decision_integrity.py::test_r18_two_identical_reads_at_once_append_one_pending_receipt`.
- G2-R36 (finding 16): the live-to-rebuild proof snapshots every table's complete rows live, before the first
  rebuild, and compares each rebuild with them row by row (only the rebuild's receipt, a derived projection live had
  not built and the activity catalog's documented first-rebuild backfill may be added; the second rebuild reproduces
  the first). The upgrade history pins a real predecessor decision and answers it after the activation. Tests:
  `tests/test_probe_router_continuation.py::test_a_rebuild_after_a_router_stop_reproduces_the_live_rows_and_writes_no_ledger`,
  `tests/test_probe_router_replay.py::test_a_predecessor_decisions_pin_answered_after_activation_rebuilds_to_the_live_rows`.
- G2-R26 (finding 6): one resolver for a router-owned episode's next question (`probe_controls.router_next`:
  pending, the exact standing presentation, or the completed transition; it retires a pin that became protected),
  read by the sidecar's `get_next_probe_item` and the terminal client; the desktop's Continue waits while the router
  chooses and opens only its question (`app/routerDecisionPoll.nextDiagnosticItem`). Tests:
  `tests/test_probe_router_continuation.py` (Continue on both sides of the worker's commit, after a stop, a protected
  pin, the terminal client), `apps/learnloop-tauri/src/screens/DiagnosticReviewScreen.routerContinue.test.tsx`.

## Pins and goldens

`tests/cli_surface.json`: only the `upgrade --to` default moves to mvp-0.77. Chain-pinned tests shift mechanically.
Regenerated by their writers for the new head tag only: `tests/goldens/identities.toml` (init manifests and offer
identities carry the tag), `tests/goldens/effective_defaults.toml` (the `algorithm_version` line),
`tests/fixtures/diagnosis_journey_golden.json` (`algorithm_version` and `projection_algorithm_version` only),
`tests/goldens/placement_stored_misses.json` (the tag in the report). The VOI restore golden, written twice, is
byte-identical and unchanged; the grade application golden is unchanged.

G2-R33 moved, by their writers: `tests/goldens/effective_defaults.toml` (the retired
`probe.block.family_redundancy_penalty` line goes), `tests/fixtures/diagnosis_journey_golden.json` (the selected
presentations carry `ranking_basis`, two observed-family presentations log `redundancy_penalty` 1.0 instead of 0.6,
the probe selection forecasts drop the multiplier parameter and their config hash moves with it; no selected item
changes). Identity pins unchanged (the retired field keeps the bytes). `tests/goldens/due_queue/admission_empty.json` and
`intent_targets_serving.json` (`DUE_QUEUE_GOLDEN_WRITE=1`): the selected probe presentations carry `ranking_basis`.

G2-R31 moved `tests/fixtures/diagnosis_journey_golden.json` (`router_learner_offered`): the accepted offer adds no
fresh `hypothesis_sets` row (the episode binds the candidate's valued lock), so the later surrogate ids renumber by one.

## The owner-copy procedure (for the orchestrator, from an mvp-0.76 copy; counts and digests only)

Make a backup-API copy of an mvp-0.76 vault for `COPY` (`COPY_DB` its `state.sqlite`). Run the 0.76 record's payload,
mastery and trace digests on it, then `learnloop upgrade --vault "$COPY" --to mvp-0.77`, the same digests again and
the queries below (before and after the upgrade; they must print the same counts, since the row is an idempotent
projection and nothing recorded is rewritten). Expected: every digest differs only in `algorithm_version`, and
`learnloop rebuild-derived-state --vault "$COPY" --json` run twice leaves the digests equal after each run.

```sh
sqlite3 -readonly -header "$COPY_DB" <<'SQL'
-- Decisions a 1e-12 rounding logged as 1 while another option kept mass (G2-R34 would log them exact from the tag).
SELECT count(*) AS rounded_draws
FROM router_decisions d, json_each(d.candidates_json) c
WHERE d.propensity = 1.0 AND json_extract(c.value, '$.ref') <> d.chosen_ref
  AND json_extract(c.value, '$.propensity') > 0;
-- Today offers published without a decision (head mismatches; refused from the tag).
SELECT count(*) AS head_mismatch_records FROM decision_records
WHERE kind = 'today_offer' AND status = 'failed' AND rule = 'head_mismatch';
-- Probe presentations ranked with the family multiplier below 1 (G2-R33's predecessor rule; history, unchanged).
SELECT count(*) AS family_penalized_presentations FROM probe_presentations
WHERE json_extract(selection_components_json, '$.redundancy_penalty') < 1.0;
-- Router-owned episodes whose lock is not their offer's (G2-R31's predecessor; history, unchanged).
SELECT count(*) AS episodes_off_their_valued_lock
FROM probe_presentations p JOIN probe_episodes e ON e.id = p.probe_episode_id
WHERE json_extract(p.selection_components_json, '$.causal_probe.router_decision_id') IS NOT NULL
  AND json_extract(p.selection_components_json, '$.causal_probe.hypothesis_set_id') <> e.hypothesis_set_id;
SQL
```

The four counts describe history the tag does not rewrite; they bound how often the
predecessor's rules acted.

## The owner-copy run (Nov 26 2026, orchestrator; counts and digests only)

Backup-API copies of the three floor-set vaults walked to `mvp-0.76` with this tip, then upgraded in place to
`mvp-0.77`. The copies were deleted afterwards. Digests leave out `algorithm_version` and `updated_at`.

| | vault 1 | vault 2 | vault 3 |
|---|---|---|---|
| rounded draws; head-mismatch records; family-penalized presentations; episodes off their valued lock (before = after) | 0; 0; 0; 0 | 0; 0; 0; 0 | 0; 0; 0; 0 |
| router decisions; probe episodes; probe presentations | 0; 31; 0 | 0; 9; 0 | 3; 18; 0 |
| twelve table digests, 0.76 against 0.77 | same | same | same |
| after rebuild 1 and 2: eleven digests same as after the upgrade; the payload digest | same; moves once at rebuild 1, same at rebuild 2 | same; as vault 1 | same; as vault 1 |
| `remint:missing_source_locators`; `answers:grade_record_missing` from the doctor | 0; 0 | 0; 0 | 0; 0 |
| integrity; foreign-key violations; schema head | ok; 0; 276 | ok; 0; 276 | ok; 0; 276 |

- The upgrade is an idempotent projection and rewrites nothing; the first rebuild afterwards rewrites the attempt
  payloads (their digest moves once and is then stable). I read that as the payloads carrying the tag in their JSON; the
  run did not open a payload to confirm it.
- **Not exercised here:** no copy holds a probe presentation or a learner-lane router decision, so none of the tag's four
  rules is reached by this history. They are covered by the tests only.
- The doctor exits 1 on each copy on the content errors that predate these tags.

