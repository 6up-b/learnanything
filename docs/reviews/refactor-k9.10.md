# K9.10: presentations and serve gates

Base `3cdc4ad278`, branch `refactor/k9.10-probe-presentations`. Structure only;
no renames. `probe_episodes.py`: **3,019 → 2,338 lines**. New
`probe_presentations.py`: **557 lines**. No stop condition or new behavior bug found;
no ledger row, pin, journey, robust verdict, ID, reason/message/SQL change.

## Members and boundary

15 definitions plus one constant, **494 original definition/assignment lines**
(including the dataclass decorator). The only moved-body edit hoists the completion
import; all other moved definitions are AST-identical without normalization.

| Member | Base line | New line | Original lines |
|---|---:|---:|---:|
| `RoutineDisplayCovered` | 1196 | 70 | 12 |
| `probe_eligibility` | 1215 | 89 | 11 |
| `routine_display_covers_item` | 1228 | 102 | 11 |
| `refuse_routine_display_covered` | 1241 | 115 | 16 |
| `commit_presentation` | 1259 | 133 | 55 |
| `record_presentation_forecast` | 1316 | 190 | 50 |
| `presentation_commit_payload` | 1368 | 242 | 86 |
| `_robust_channel_pin` | 1456 | 330 | 33 |
| `serve_presentation` | 1491 | 365 | 20 |
| `probe_serving_block_reason` | 1513 | 387 | 35 |
| `probe_value_block_reason` | 1550 | 424 | 49 |
| `commit_item_presentation` | 1601 | 473 | 36 |
| `PresentationValidation` | 1793 | 512 | 6 |
| `validate_presentation_for_submission` | 1800 | 519 | 39 |
| `PROBE_ITEM_ANSWER_SHOWN` | 1212 | 86 | 1 |
| `shadow_selection_rankings` | 1160 | 34 | 34 |

`shadow_selection_rankings` has only the moved payload builder as an internal
reader, so it moves. `PROBE_ITEM_ANSWER_SHOWN` is consumed by the sidecar and follows
the eligibility/presentation interface. No other exclusive helper or constant exists.
`EligibleInstrument`, `eligible_instruments`, `episode_hypothesis_set`,
`episode_posterior` and `_entropy` stay: lifecycle/instruments/posterior or evidence
also read them. **`_entropy` is the only private name crossing this new boundary**.
The family helpers remain in `probe_families`; only its selection-policy import
leaves the core, since the payload builder was its sole reader.

Order: core < completion < presentations. Presentations imports both at top level.
`probe_value_block_reason`'s local `robust_gate_counterfactual` import becomes a
module import. Completion is byte-identical to base and imports no presentations.
The core adds local validation imports in `record_presentation_activity_classification`
and `_record_presentation_observation`: both are **evidence (moves later)**, neither
is core lifecycle/instruments/posterior. Controls require no presentations import.
No top-level core→presentations import or re-export was added.

All changed/new function-local presentation imports (test repoints included):

| File | Function | Imported names |
|---|---|---|
| `src/learnloop/attempts/attempts.py` | `_validate_probe_presentation` | `validate_presentation_for_submission` |
| `src/learnloop/diagnosis/causal_orchestrator.py` | `_answer_shown` | `routine_display_covers_item` |
| `src/learnloop/diagnosis/causal_orchestrator.py` | `_accept_probe_offer` | `RoutineDisplayCovered, commit_presentation` |
| `src/learnloop/diagnosis/probe_episodes.py` | `record_presentation_activity_classification` | `validate_presentation_for_submission` |
| `src/learnloop/diagnosis/probe_episodes.py` | `_record_presentation_observation` | `validate_presentation_for_submission` |
| `tests/test_probe_orchestration_remainder.py` | `test_session_cap_blocks_further_probe_serving` | `probe_serving_block_reason` |
| `tests/test_probe_orchestration_remainder.py` | `test_planner_shadow_report_summarizes_logged_components` | `commit_item_presentation` |
| `tests/test_serve_eligibility.py` | `test_no_probe_is_committed_for_an_item_submit_would_prime` | `commit_item_presentation` |
| `tests/test_serve_eligibility_review.py` | `test_f4_a_probe_of_an_item_submit_would_prime_is_refused` | `commit_item_presentation` |
| `tests/test_teacher_te2_landing_r1.py` | `test_fg1s_presentation_path_stamps_the_submissions_identity_and_its_regrade_the_replacements` | `commit_presentation, serve_presentation` |
| `tests/test_ux_phase4_feedback.py` | `test_f1k_no_probe_is_committed_for_an_item_inside_routine_display_coverage` | `commit_item_presentation` |
| `tests/test_ux_phase4_feedback.py` | `test_f1l_a_presentation_committed_before_a_display_is_not_served_inside_its_coverage` | `RoutineDisplayCovered, commit_presentation, serve_presentation` |
| `tests/test_ux_phase4_feedback.py` | `test_f1l_a_refused_causal_offer_leaves_the_episode_and_its_presentation_unchanged` | `commit_item_presentation` |
| `tests/test_voi_merge_composition.py` | `test_a_committed_probe_logs_its_value_decision_once_beside_the_selection_forecast` | `record_presentation_forecast` |
| `tests/test_voi_merge_composition.py` | `_answer_presentation` | `serve_presentation` |
| `tests/voi_stopping_helpers.py` | `_answer_probe` | `commit_presentation, serve_presentation` |

In `causal_orchestrator.py`, only `_answer_shown` and `_accept_probe_offer`'s
function-local imports changed. Other worker-owned code is untouched.

## Deletion proof and tests

Before editing, `rg -n 'plan_precommitted_block' src apps scripts tests
 docs/learnloop-architecture-vault/_scripts` produced exactly five hits: its
definition (`probe_episodes.py:1639`), the top-level import/call in
`test_probe_policy.py:20,92`, and the local import/call in
`test_ux_phase4_feedback.py:2818,2825`. Output: `deletion_search.txt`.
Restricting those pre-edit hits to `src apps scripts` leaves only the definition.
`rg -n 'plan_precommitted_block|__all__|importlib|__import__'
 src/learnloop/diagnosis/probe_episodes.py` found only the definition
(`deletion_module_search.txt`). A base `git grep -n` over all tracked file types
independently reproduced the five hits, and the star-import search found none.
There are no runtime top-level/local/dynamic imports, string literals/getattr or
string dispatch, registry/CLI/TUI/frontend/phone callers, or replay/rebuild/upgrade
paths naming it, and no `__all__`/star-import exposure. The reference graph records
no internal reader. Full-token searches also cover importlib and `__import__`
strings. No helper or constant was exclusive to the planner: all its dependencies
survive (notably `_bayes_update` and the family likelihood/EIG functions).

Deleted **151 definition lines** and these two planner-subject tests:

| Test | Fate |
|---|---|
| `test_probe_policy.py::test_precommitted_block_commits_all_before_answers` | Deleted: joint planning, stamped telemetry and consumption of its output. |
| `test_ux_phase4_feedback.py::test_f1l_a_precommitted_block_stamps_its_surviving_members_size_and_indices` | Deleted: planner's member filtering and block-size/index stamps. |

Neither case merely routes to a surviving helper; no plain-value port is needed.
The shared coverage/refusal, commit/serve and sequential-conditioning tests remain,
with all surviving behavior assertions unchanged. Unused ITEM_2/ITEM_3 test imports
and the two now-empty test section headings were removed.

## P1–P6

- **P1 PASS:** 15 moved definitions + 1 constant; 14 definitions exactly identical,
  one differs only by the completion import hoist (small diff below). Exactly those
  definitions/constant plus `plan_precommitted_block` leave the source. All **44**
  remaining definitions are AST-identical after the two exact local imports.
  Completion (including `_robust_gate_verdict`) is byte-identical. No renames.
- **P2 PASS:** baseline captured before edits (`base_resolution.json`), then verified
  against base execution under the original module name. **29 matching body-global
  reads**: 14 relocated definition references, 6 unchanged core definition references
  verified by identity against core and AST against base, 9 other same-process
  object identities. One identical completion import promoted from local to global.
  Zero `__name__` reads. `tip_resolution.json` retains the comparison table.
- **P3 PASS:** no patch/attribute assignment of a source-module global or moved
  private name, and no source-text assertion on a moved definition. No patch is
  repointed and no assertion is weakened. Patch/boundary table below.
- **P4 PASS:** required gate **408 passed**; identity-pin and journey test files and
  all goldens unchanged. No writer flags. The journey helper's four presentation
  calls use its new module alias; snapshots/expected bytes did not move.
- **P5 PASS:** direction above; `ruff check` clean; `lint-imports --no-cache`:
  **42 kept, 0 broken**. No new package pair exception. Top-level imports below.
- **P6 PASS:** AST scan of **3,152 Python files** across src/tests/scripts/vault
  _scripts: **zero** old-module imports of moved names, aliased moved attributes,
  or fully-qualified old-module/moved-name strings. Aliases include PE/pe/probes
  and full dotted imports. `audits.json`/`audits.txt` retain outputs.

```diff
--- base/probe_episodes.py
+++ tip/probe_presentations.py
@@ -17,8 +17,6 @@
     a calibration session's lift, or when the item is not an eligible
     instrument (the caller's own path decides that).
     """
-
-    from learnloop.diagnosis.probe_completion import robust_gate_counterfactual
 
     from learnloop.diagnosis import voi_stopping as voi
 
```

P3 patches/boundaries:

| Candidate | Consuming globals / disposition |
|---|---|
| Source-module patches/assignments and moved private/source-text tests | None; zero patches to repoint, zero T4 conversions. |
| Existing `test_probe_robust_cutover` completion override patch | Completion evaluator still reads completion globals; unchanged and effective. |
| Repository disclosure-method patches in `test_ux_phase4_feedback` | Passed repository object still supplies the methods; unchanged and effective. |
| `test_salience_firewall::test_belief_modules_never_import_the_reading_firewall` | Static source-file guard still applies to the core's belief implementation. It does not assert on a moved definition; unchanged. |

Moved definitions' `__module__` becomes `learnloop.diagnosis.probe_presentations`;
their `__qualname__` strings remain identical. None of the moved bodies reads
`__name__` or calls `logging.getLogger(__name__)`, so no body logger changes here.
Scans of src/tests/scripts found no old module/qualname selector or logger selector
for these definitions (caplog/at_level/logging config included); no selector edit.
Two explanatory source references follow the new home: `voi_stopping`'s forecast
docstring and `serve_eligibility`'s reason-constant comment (constant bytes unchanged).
One UX-test docstring follows the commit's home. No matching hand-written Concepts
reference required editing; Journeys/ does not exist. Generated Reference/ untouched.

New module's top-level imports: future annotations; dataclasses.dataclass;
typing.Any/Mapping; clock.Clock/parse_utc/utc_now_iso;
db.repositories.ProbeEpisodeRecord/ProbePresentationRecord/Repository;
probe_completion.robust_gate_counterfactual; probe_episodes.EligibleInstrument,
_entropy, eligible_instruments, episode_hypothesis_set, episode_posterior;
probe_families.SELECTION_POLICY_VERSION/instrument_expected_information_gain;
vault.models.LoadedVault.

## Registries and callers

- `pyproject.toml`: duplicate the existing core edges for presentations, retaining
  both, for **attempts.attempts, scheduling.scheduler, sim.diagnostic_validation**.
  Each importer still uses core. No new pair of packages gets an exception.
- `architecture_function_local_domain_imports.txt`: add
  `attempts.attempts -> diagnosis.probe_presentations`, retain the core edge for
  remaining evidence imports. No cross-domain local import moves out of core.
- `REGISTERED_SQL_OWNERS`: **no edit**. No literal SQL moves; presentations calls
  repository methods. Adding an owner without SQL would violate its paired test.
- `tests/goldens/structure.toml`: **not edited**. No vault generator run.

Caller/explanatory files updated by directory (the core/new module and registries
are counted separately):

| Directory | Files |
|---|---:|
| `src/learnloop` | 1 |
| `src/learnloop/attempts` | 1 |
| `src/learnloop/diagnosis` | 3 |
| `src/learnloop/scheduling` | 1 |
| `src/learnloop/sim` | 1 |
| `src/learnloop/tui/screens` | 1 |
| `src/learnloop_sidecar/handlers` | 1 |
| `tests` | 22 |

Seven functional external src callers plus two explanatory src files; 22 test/helper
files. scripts: 0; vault _scripts: 0. See file-count table below for each path.

## Ratchets (new module injected in scratch measure)

| Metric | Base / golden | Stock (untracked omitted) | Including new module |
|---|---:|---:|---:|
| largest_import_component | 146 | 146 | **147** |
| modules_in_an_import_cycle | 252 | 252 | **253** |
| first_level_packages | 46 | 46 | 46 |
| first_level_root_modules | 35 | 35 | 35 |
| first_level_root_modules_not_upgrade | 35 | 35 | 35 |
| functions_over_200_lines | 72 | 72 | 72 |
| comment_lines_naming_a_stage_artifact | 2371 | 2369 | 2370 |
| test_files_named_for_a_stage | 184 | 184 | 184 |

Only `learnloop.diagnosis.probe_presentations` joins the largest component.
Expected split increase; orchestrator raises the two module-count goldens.
`measure_presentations.py` uses the original measure with the new file injected
and base source texts reconstructed only for changed files. `ratchets.txt` and
`ratchet_details.json` hold full results.

## Commands and results

`S` is the supplied scratch directory ending in `scratchpad/refactor-k910`;
`T=$S/t.sh`, `PY=$S/py.sh`. Test commands ran serially, with explicit arrays and
four workers. The text matcher used old/new module names and every moved/deleted
name: **72 selected files**, 60 + 12, plus the excluded matching mobile file.
`affected_tests.json`, `affected_chunk_1.sh` and `affected_chunk_2.sh` retain lists.

| Command | Result |
|---|---|
| `$T tests/test_identity_pins.py tests/test_diagnosis_journey_golden.py tests/test_architecture.py tests/test_test_layout.py tests/test_structure_ratchets.py tests/test_cli_help_snapshot.py -q -n 4` | **408 passed**, 45.95s |
| `bash "$S/affected_chunk_1.sh"` → `$T <60 explicit paths> -m "not arc_close" -n 4 -q` | **9822 passed, 19 skipped, 4 failed**, 155.87s; all failures sandbox sockets |
| `bash "$S/affected_chunk_2.sh"` → `$T <12 explicit paths> -m "not arc_close" -n 4 -q` | **399 passed, 3 skipped, 8 failed**, 19.79s; all failures sandbox sockets |
| `$PY ruff check` | **All checks passed** (initial and final) |
| `$PY lint-imports --no-cache` | **42 kept, 0 broken** |
| `$PY python "$S/prove_presentations.py"` | **P1/P2/P5 pass**; repeated after whitespace-only cleanup |
| `$PY python "$S/audit_presentations.py"` | **P3/P6/deletion audit pass** |
| `$PY python "$S/measure_presentations.py"` | Numbers above; no golden write |
| `git diff --check` | Passed |

Unedited sandbox failures, all `PermissionError: [Errno 1] Operation not permitted`
at socket creation: `test_probability_prep.py` **2**,
`test_sidecar_contract.py` **2**, `test_sidecar_tutor_qa.py` **8**. Exact node IDs
and traces are in `affected_1.txt` and `affected_2.txt`. Their behavior is **not
verified**. No other test failure, assertion edit or production bug was found.
Known startup hangs omitted: `test_mobile_v3_probes.py`,
`test_ih6_workbench_open_item.py`, `test_ih4_preferences_inform_router.py` (only
mobile matches the selection). Bubblewrap-specific behavior and excluded/arc-close
cases not verified; no full suite/landing gate. Final `.pytest_tmp` is empty.
No network/model calls, vault/config/credential reads, other checkout edits,
git mutations, or agent sessions. Scratch scripts/output stay under S.

## K9.11 handoff

Evidence's two local validation imports become top-level imports from presentations
when evidence moves. Its existing completion belief/close-segment imports also
remain ready for hoisting. Controls still import completion and the block helpers
locally; `probe_episodes -> probe_blocks` remains for the next cut. No core lifecycle
caller needs presentations. Keep `_entropy` in core (posterior also uses it).
Presentations and completion remain below evidence/controls. Re-measure the new
component with all new parts counted; the two temporary cycle-count increases
here are structural. Review the dead-test classification, shadow helper boundary
and three duplicated frozen edges first. No stop condition remains unresolved.

## Files changed (physical lines)

| File | Before | After | Diff + / − |
|---|---:|---:|---:|
| `pyproject.toml` | 1298 | 1301 | +3 / −0 |
| `src/learnloop/attempts/attempts.py` | 5812 | 5812 | +1 / −1 |
| `src/learnloop/diagnosis/causal_orchestrator.py` | 2965 | 2967 | +5 / −3 |
| `src/learnloop/diagnosis/probe_dialogue.py` | 464 | 466 | +3 / −1 |
| `src/learnloop/diagnosis/probe_episodes.py` | 3019 | 2338 | +4 / −685 |
| `src/learnloop/diagnosis/probe_presentations.py` | 0 | 557 | +557 / −0 |
| `src/learnloop/diagnosis/voi_stopping.py` | 2493 | 2493 | +1 / −1 |
| `src/learnloop/scheduling/scheduler.py` | 3750 | 3752 | +3 / −1 |
| `src/learnloop/serve_eligibility.py` | 1029 | 1029 | +1 / −1 |
| `src/learnloop/sim/diagnostic_validation.py` | 644 | 646 | +4 / −2 |
| `src/learnloop/tui/screens/practice.py` | 579 | 581 | +4 / −2 |
| `src/learnloop_sidecar/handlers/practice.py` | 2210 | 2212 | +6 / −4 |
| `tests/architecture_function_local_domain_imports.txt` | 162 | 163 | +1 / −0 |
| `tests/diagnosis_journey_helpers.py` | 483 | 484 | +5 / −4 |
| `tests/p2_acceptance_helpers.py` | 97 | 99 | +3 / −1 |
| `tests/probe_block_end_helpers.py` | 119 | 121 | +3 / −1 |
| `tests/probe_episodes_helpers.py` | 112 | 114 | +3 / −1 |
| `tests/probe_robust_cutover_helpers.py` | 95 | 97 | +3 / −1 |
| `tests/test_causal_repair_sidecar_rpcs.py` | 617 | 619 | +3 / −1 |
| `tests/test_characterization_probe_regrade.py` | 203 | 205 | +3 / −1 |
| `tests/test_characterization_probe_replay.py` | 135 | 137 | +3 / −1 |
| `tests/test_p2_leakage_suite.py` | 210 | 212 | +3 / −1 |
| `tests/test_probe_audit.py` | 372 | 374 | +3 / −1 |
| `tests/test_probe_episodes.py` | 885 | 887 | +5 / −3 |
| `tests/test_probe_longform_families.py` | 352 | 354 | +3 / −1 |
| `tests/test_probe_orchestration_remainder.py` | 480 | 482 | +5 / −3 |
| `tests/test_probe_policy.py` | 149 | 115 | +5 / −39 |
| `tests/test_probe_predictive_eig.py` | 124 | 124 | +1 / −1 |
| `tests/test_serve_eligibility.py` | 570 | 574 | +5 / −1 |
| `tests/test_serve_eligibility_review.py` | 440 | 444 | +5 / −1 |
| `tests/test_teacher_te2_landing_r1.py` | 229 | 231 | +3 / −1 |
| `tests/test_ux_phase4_feedback.py` | 3054 | 3042 | +15 / −27 |
| `tests/test_voi_merge_composition.py` | 770 | 770 | +2 / −2 |
| `tests/test_voi_stopping.py` | 1299 | 1299 | +1 / −1 |
| `tests/voi_stopping_helpers.py` | 342 | 344 | +3 / −1 |
| `docs/reviews/refactor-k9.10.md` | 0 | 303 | +303 / −0 |

## Orchestrator's review

The orchestrator's own AST check: 15 definitions moved and identical, apart from `probe_value_block_reason`, whose
function-local import of `robust_gate_counterfactual` is now the module's top-level import; 47 stayed identical;
two that stay differ only by a function-local import of a moved name; `plan_precommitted_block` is gone.
`git grep` at the base finds `plan_precommitted_block` in `src`, `apps` and `scripts` only at its definition.

One residue of the deletion is recorded as K9-30: `probe_blocks.py` still reads the selection components
`joint_block` and `block_size`, which only the deleted planner wrote. It is left for the next step, which edits that
module.
