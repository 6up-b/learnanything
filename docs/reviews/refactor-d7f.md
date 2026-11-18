# D7 batch 1, part 5 — replay-read switches

Base `931c8d072e`, floor `mvp-0.58`, head `mvp-0.60`. Step 0 references below use base line numbers. The November 12 owner-copy report in [D7.0](refactor-d7.0.md) found zero tagged-switch overrides on all three copies. The defaults therefore establish owner behavior without inspecting any vault configuration. Neither switch is recorded in projection_switches or compared by doctor (D7-1). Step d of [the rebuild fix](refactor-adfix3.md) landed before this work.

## 1. Bounded ledger — step 0

`replay.ledger_bounded` is inventory class A, introduced at `mvp-0.34`, below the floor. The schema (`src/learnloop/config/schema.py:4475`) and effective defaults (`tests/goldens/effective_defaults.toml:940`) both say true. Its sole production reader, `src/learnloop/attempts/attempts.py:1315`, defaults a missing field to true. Its only caller is `replay_existing_attempt` at line 1450. ON supplies the attempt's (created_at, id) cutoff to the recent-attempt windows and canonical facet projection. OFF supplies None, so later attempts can affect familiarity, event severity, item quality, mastery, surprise and schedules. A missing timestamp already supplies None. Live writes never call this predicate. Direct replay and the rebuild's learner replayer do. All three owner copies run ON, including at the floor.

The other base references are declarations and descriptive metadata in `algorithm_versions.py:493`, `config/kill_switches.py:45`, `params/parameter_registry.py:1684`, the vault generator `_scripts/db_generate_reference.py:1346`, and the Algorithm Versions and Reproducibility note, line 59. Test references occur in `test_kill_switches.py:42`, `test_rebuild_equivalence_review.py:218,233–234,258`, `test_rebuild_equivalence.py:21`, `test_mvp017_route_check_replay.py:152`, and the independent retirement/legacy-input check in `test_retired_config_identities.py:295,381`. Generated configuration and module references await the landing regeneration. The previous whole-section removals also required deleting the orphaned generated section note by hand (D7a §6). The obsolete generated Reference/Configuration/Fields/Config - replay.md was removed by hand here. The generator writes current notes and checks the directory count without pruning old files (_scripts/db_generate_reference.py:2021,2266–2274). The two hand-written catalog counts now report 1,159 leaves and Configuration.md reports 75 sections.

## 2. Claim fixes — step 0

`mastery.claim_fixes_enabled` is inventory class A, introduced at `mvp-0.33`, also below the floor. Both `src/learnloop/config/schema.py:214` and `tests/goldens/effective_defaults.toml:656` default to true. The three copies use this default. The direct reader at `src/learnloop/learner/mastery.py:183` falls back to false for a missing field (D7-3). These are its eight callers under `src/learnloop/`:

| Base location | ON | OFF |
| --- | --- | --- |
| learner/mastery.py:312 | Seed using claims known at the replay point, retain cold and past anchor variance | Seed from current claims using the claim's own variance floor |
| learner/mastery.py:489 | Re-anchor atomically and record the live claim's applied attempt count | No enclosing transaction or position write here |
| learner/mastery.py:549 | Preserve an existing unevidenced row's larger variance | Replace it with the new seed variance |
| learner/mastery.py:557 | Precision-weight the mean, retain the variance floor | Precision-weight both mean and variance |
| learner/mastery.py:577 | Rank by specificity, recency, pseudo-count and ID | Rank by specificity, pseudo-count, higher claimed level, stamp and ID |
| placement/claim_check.py:51 | Show the resolving review's claim feedback when placement is active | Suppress the line |
| substrate/replay.py:162 | Place covering claims in the attempt stream and apply re-anchors at their recorded positions | Skip the claim stream and seed from claims in force now |
| tutor/promotions.py:818 | Insert and re-anchor the tutor gap claim atomically, with retry deduplication | Insert a plain claim only |

Replay and rebuild read this switch through the claim stream and mastery routines. Doctor compares recorded projection switches (`ops/doctor.py:1646–1661`), which omit it. C1 hashes the mastery identity (`placement/predictor.py:62`), and C2 excludes this field from the offline arm's hash (`field/predictors.py:46,54`). The registry and table entries are at `params/parameter_registry.py:2577` and `config/kill_switches.py:44`. Other literal references appear in the algorithm tag comment (line 472), the hand-written algorithm versions note (line 58), the generated mastery reference, and tests: the kill-switch list line 41, identity shape golden line 159, retired-config tests lines 293 and 378, test_lp_claim_fixes.py:4,59,135–144,422–423, test_lp_claim_fixes_review.py:37 and test_lp_claim_fixes_rereview.py:133. The two named tag constants still belong to SUCCESSOR_CHAIN.

## Bounded ledger removal and proof

The predicate and the now-empty ReplayConfig section are gone. The cutoff still handles a missing timestamp and live writes still supply no replay position. At base, attempts.py:3019–3021,3129 used the replay position for the canonical facet projection and line 3430 passed it to the prior-state read. The latest-tag grade-channel fix remains governed by the tag. The one legacy key is archived on LearnLoopConfig, which owned the removed section. The retired-config tests already pin both config digests, including the old explicit false value. Their independent default-shape reconstruction now supplies the whole retired table.

Base lines removed or ported:

- src/learnloop/attempts/attempts.py:513–515,1308–1315,1450; config/schema.py:4463–4475,4726; config/kill_switches.py:45; params/parameter_registry.py:1678–1688; algorithm_versions.py:492–493. The tag constant remains in the successor chain at base line 969.
- The effective default at tests/goldens/effective_defaults.toml:940, the kept-list entry at tests/test_kill_switches.py:42, the generator description at _scripts/db_generate_reference.py:1346–1353 and the switch clause in the hand-written Algorithm Versions and Reproducibility note, line 59.
- tests/test_rebuild_equivalence_review.py:230–235 checked only the former default and classification, so that test went. The mixed test at lines 246–260 retains the exact live-versus-rebuild mastery assertion. Its OFF-only comparison, SWITCH_OFF, and the private helper's config parameter/append in tests/rebuild_equivalence_review_helpers.py:14,18,22–23 went together. The separate live-write comparison at the two tags remains. The fixture and equivalence test docstrings now describe the kept behavior.
- Dead-code check: `git grep -nE 'replay_reads_bounded_ledger|\bReplayConfig\b' -- src tests scripts apps docs/learnloop-architecture-vault/_scripts` gives no matches. Searching the same paths for `ledger_bounded` finds only the retirement row and the two independent legacy-config test entries. No version set was left exclusively serving this switch.

Each side copied the three November 12 owner snapshots with copy_tree_with_databases into fixtures-local/d7f. Base ran the git archive of HEAD's src and migrations on PYTHONPATH; the driver asserted default_migrations_dir() pointed into the selected tree. Each side ran the real upgrade CLI through 0.59 to 0.60, then rebuild-derived-state. The fixture copies were retagged separately to the floor and head. After the first rebuild the driver selected every column of every DERIVED table, practice_item_state and practice_attempts, checked column names and compared row multisets (including duplicates). It then repeated the CLI rebuild at tip and compared all columns without exclusions. Counts below are common to base and tip.

| Table | Linear algebra | arXiv | Probability | Fixture at 0.58 | Fixture at 0.60 |
| --- | ---: | ---: | ---: | ---: | ---: |
| ability_transition_events | 70 | 3 | 3 | 18 | 18 |
| ad_attempt_trace | 90 | 0 | 4 | 23 | 23 |
| ad_state | 9 | 1 | 2 | 5 | 5 |
| attempt_surprise | 70 | 3 | 3 | 18 | 18 |
| capability_residual_state | 0 | 0 | 0 | 0 | 0 |
| confidence_calibration_state | 0 | 0 | 0 | 0 | 0 |
| facet_capability_evidence | 36 | 2 | 1 | 4 | 4 |
| facet_outcome_observations | 82 | 5 | 3 | 27 | 27 |
| facet_recall_state | 76 | 4 | 2 | 11 | 11 |
| facet_uncertainty | 4 | 3 | 1 | 0 | 5 |
| family_memory_state | 0 | 0 | 0 | 0 | 0 |
| hypothesis_recurrence_groups | 0 | 0 | 0 | 0 | 0 |
| hypothesis_recurrence_review | 0 | 0 | 2 | 0 | 0 |
| hypothesis_recurrence_state | 1 | 1 | 1 | 1 | 1 |
| item_fingerprints | 0 | 0 | 0 | 0 | 0 |
| item_forecast_scores | 0 | 0 | 7 | 0 | 0 |
| item_parameter_state | 0 | 0 | 0 | 0 | 0 |
| learning_object_mastery | 21 | 34 | 18 | 5 | 5 |
| learning_outcome_labels | 291 | 0 | 3 | 80 | 80 |
| lesson_weight_state | 0 | 0 | 0 | 0 | 0 |
| lesson_weight_trace | 0 | 0 | 0 | 0 | 0 |
| practice_attempts | 70 | 3 | 3 | 18 | 18 |
| practice_item_quality_state | 54 | 2 | 1 | 5 | 5 |
| practice_item_state | 99 | 32 | 77 | 6 | 6 |
| retrieval_fusion_posteriors | 0 | 0 | 0 | 0 | 0 |
| retrieval_intervention_outcomes | 0 | 0 | 0 | 0 | 0 |
| router_outcomes | 0 | 0 | 3 | 0 | 0 |
| source_block_fts | 972 | 4606 | 510 | 0 | 0 |
| subject_identifiability_watermarks | 1 | 1 | 1 | 1 | 1 |
| **Total rows** | 1946 | 4700 | 645 | 222 | 227 |
| Base vs tip, non-stamp differences | 0 | 0 | 0 | 0 | 0 |
| Base vs tip, stamp-only rows | 112 | 6 | 3 | 0 | 0 |
| Tip first vs second rebuild, any differing rows | 0 | 0 | 0 | 0 | 0 |

The only owner-copy differences between separate runs were facet_recall_state.updated_at and facet_capability_evidence.created_at/updated_at. These are the canonical stamps explained by D-35 in the rebuild fix. No watermark differed. On the initial fixture comparison the CLI's first sync created one practice_item_state row with a wall-clock updated_at. The fixture proof reran from fresh copies with SystemClock.now fixed to the same instant on both sides for the first CLI run and a day later for the repeat. All 29 tables matched exactly, with the item-state timestamp included. The fixture's second rebuild also matched the first on the base at both tags.

## Claim fixes stop

A reversible retirement of just the schema leaf (MasteryConfig adopting KeepsRetiredFields) and its true retired default produced exactly one failure in the unchanged identity-pin and retired-config suites. At tests/test_identity_pins.py:116 the shape lost `claim_fixes_enabled: bool = true` and gained `retired claim_fixes_enabled: bool = true`. All digest checks passed. The shape helper enumerates live and retired fields separately (tests/identity_pins_helpers.py:1710–1727). The task requires stopping on a moved pin. No OFF-only tests were deleted or ported for the stopped switch. Both trial edits were undone and the kept-because list now names this pin. The runtime, tests, golden and registry entry for this switch remain as at base. No claim-removal rebuild is claimed.

## Reproducing the rebuild comparison

Run from this worktree with the supplied empty-home wrapper. The scratch driver re-execs that interpreter with the selected src first on PYTHONPATH. It runs the CLI's Typer entry point for every upgrade and rebuild. The dumps are local to fixtures-local/d7f. The implementer deleted that directory after the comparisons.

```bash
S=/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/73b37aee-2550-41c4-88a8-8730b0f3c0c0/scratchpad/refactor-d7f
mkdir -p "$S/base"
git archive 931c8d072e src migrations | tar -x -C "$S/base"
for side in base ledger; do
    for copy in linear_algebra arxiv_v2 probability fixture58 fixture60; do
        "$S/py.sh" python "$S/proof.py" "$side" "$copy" || exit 1
    done
done
rm -r -- fixtures-local/d7f/base fixtures-local/d7f/ledger
rmdir fixtures-local/d7f
```

## Cost and goldens

| Implementer | Runtime source diff | Effective config leaves removed | Tagged rows / kept-because entries | Full landing gates |
| --- | --- | ---: | --- | ---: |
| Codex, one implementer, bounded ledger | +4 / −44 | 1 (1,168 to 1,167) | 73 to 72 / 71 to 70 | 0 |
| Same implementer, claim fixes stopped | 0 | 0 | 0 removed | 0 |

Implementer token telemetry is unavailable in this session, so the §2.20 cost-per-line and cost-per-leaf comparison to part 1 cannot be calculated. The orchestrator owns the landing gate. The unchanged identity tests and both identity goldens are the reference for the delivered diff. The effective-defaults golden lost only replay.ledger_bounded. The diagnosis journey recorder changed only fg1_wait's versions.config field, the provenance hash of the plain config dump (router_objective/decision_state.py:267). The CLI help snapshot stayed fixed.

## Verification commands

`T=$S/t.sh` and `PY=$S/py.sh`, with S as above. Commands ran sequentially. The full suite, landing gate, vault reference generators and validators belong to the orchestrator. No live or retired vault was opened.

- Named gate: `"$T" tests/test_identity_pins.py tests/test_retired_config_identities.py tests/test_architecture.py tests/test_test_layout.py tests/test_structure_ratchets.py tests/test_effective_defaults_golden.py tests/test_cli_help_snapshot.py tests/test_kill_switches.py tests/test_diagnosis_journey_golden.py -q -n 3`. Initially 438 passed, one failed (fg1_wait's plain-config hash). `DIAGNOSIS_JOURNEY_WRITE_GOLDEN=1 "$T" 'tests/test_diagnosis_journey_golden.py::test_diagnosis_journey[fg1_wait]' -q` passed and changed one line. Final named gate 439 passed.
- Claim-retirement trial: `"$T" tests/test_identity_pins.py tests/test_retired_config_identities.py -q -n 3` gave 359 passed, one shape-pin failure. Neither the test nor its goldens were edited.
- Sweep: `bash "$S/sweep.sh"` builds a sorted union of base and tip filenames matching `rg -il 'ledger_bounded|claim_fixes|rebuild|replay|kill_switch' tests --max-depth 1 --glob 'test_*.py'`. Both lists had 386 matches. Seven matching files start clients that can hang here: test_ih3_phone_host.py, test_ih4_preferences_inform_router.py, test_mcp_c1a_narrow.py, test_mobile_handoff.py, test_mobile_rpc.py, test_mobile_v2_plan.py and test_mobile_v4_reader.py. The other two named sandbox exclusions, test_mobile_v3_probes.py and test_ih6_workbench_open_item.py, did not match. All 379 other files were attempted. Each numbered command reads its exact filenames with `mapfile -t files < "$S/chunk-$i.txt"` and runs `"$T" "${files[@]}" -m 'not arc_close' -v -n 3`.

| Command | Files | Passed | Skipped | Xfailed | Failed |
| --- | ---: | ---: | ---: | ---: | ---: |
| Chunk 1, activity_backfill to coldness_receipt | 60 | 1080 | 9 | 0 | 0 |
| Chunk 2, commitment_arcs to figure_requests_migration | 60 | 1089 | 7 | 1 | 4 |
| Chunk 3, figure_wait_estimate to km2b_consumer_rekey | 60 | 1084 | 0 | 0 | 2 |
| Chunk 4, knowledge_map_text_neighbors to reader_activity | 60 | 1158 | 27 | 2 | 32 |
| Chunk 5, reader_ca1_as_printed to router_coldness_covariates | 60 | 1396 | 1 | 4 | 3 |
| Chunk 6, router_g4_restraint to teacher_te2log_episodes | 60 | 9499 | 5 | 0 | 51 |
| Chunk 7 rerun, tier1_decider to workbench_assistance | 19 | 662 | 6 | 0 | 2 |
| Two isolated TUI retries | | 2 | 0 | 0 | 0 |
| **Completed sweep cases** | **379** | **15970** | **55** | **7** | **94** |

Chunk 7 initially stalled at 90% in test_tui_feedback.py::test_committed_model_grade_is_not_regraded_when_a_later_step_fails. Its rerun added `--deselect=tests/test_tui_feedback.py::test_committed_model_grade_is_not_regraded_when_a_later_step_fails --deselect=tests/test_tui_feedback.py::test_tui_retry_resumes_a_committed_grade_instead_of_recording_another`. Each of the three isolated cases was then run as `timeout -s TERM -k 5 45 "$T" "tests/test_tui_feedback.py::$case" -o faulthandler_timeout=25 -m 'not arc_close' -v`. The two retry parameters, auto_grade and empty_stuck, passed. The first case timed out again in asyncio runner shutdown at test_tui_feedback.py:249. It is additional to the counts of completed cases.

- `"$PY" ruff check`: all checks passed.
- `"$PY" lint-imports --no-cache`: 43 contracts kept, zero broken.

### Baseline check on sweep failures

All 94 failed node IDs also failed on archived HEAD. The TUI timeout reproduced at the same asyncio shutdown frame on HEAD. The failures break down as follows:

| Sandbox dependency | Failing tests per file |
| --- | --- |
| HTTP or Unix socket | deferred_regrade 1, field_signal_production_paths 3, probability_cli 2, probability_prep 2, query_student 6, sidecar_tutor_qa 8, tui_feedback 1, tutor_delivery_fixes 1 |
| Bubblewrap-backed PF generation or figure checks | item_fingerprints 2, pf_generation 22, required_method_authority 3, rw5c_recheck 11, rw5c_source_check 32 |

The socket traces include EPERM and query-server startup timeouts. An empty JSON program run through the production PF sandbox returned exit 1 with `bwrap: loopback: Failed to create NETLINK_ROUTE socket: Operation not permitted`. The baseline comparison establishes the failed node IDs. One sandboxed figure test (the cancelled-factor case) failed an earlier assertion on the archived base than on the tip.

The baseline wrapper command was `mapfile -t ids < "$S/failure-nodeids.txt"; "$T" "${ids[@]}" -o "pythonpath=$S/base/src $S" -p d7f_basecheck -m 'not arc_close' -q -n 3`. A scratch pytest plugin asserted the imported code resolved its migrations directory under the archive. The initial extraction of node IDs split one parameter containing a literal spaced minus: the command collected no tests. A single item_fingerprints control failed as on tip, and a serial collection check reported the malformed selector. Preserving each full ID gave 94 failures. Repeating with the tracked desktop sketch-engine assets also extracted gave 94 failures. The corresponding 45-second serial timeout command, with the same base import options, exited 124.

No new suite failure was unique to this diff. Generated module references and the generated configuration catalog await the orchestrator. The single held switch still has D7-1's unrecorded replay setting and D7-3's missing-field fallback.
