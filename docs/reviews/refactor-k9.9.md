# K9.9: the completion policy out of `probe_episodes.py`

Base `4874f304e8`, branch `refactor/k9.9-probe-completion`. The implementer made the move and its proofs and
stopped before three registry entries its brief did not name; the orchestrator added them and committed.

## The three registry entries

The move puts unchanged code in a new file, and three inventories name files:

- `tests/architecture_function_local_domain_imports.txt`: `curriculum.golden_path_run -> diagnosis.probe_episodes`
  became `-> diagnosis.probe_completion` (the same function-local import of `close_diagnostic_segment`; one edge
  out, one in).
- `tests/test_architecture.py`, the registered SQL owners: `diagnosis/probe_completion.py` added beside
  `probe_episodes.py`. `set_target_decision`'s `UPDATE probe_episodes` moved with it, unchanged; the old module still
  writes SQL, so both are owners.
- `pyproject.toml`, the frozen cross-package cycle exceptions: `scheduling.scheduler -> diagnosis.probe_completion`
  added beside `scheduling.scheduler -> diagnosis.probe_episodes`. The scheduler imports `robust_gate_counterfactual`
  from the new module and still imports the core, so the one frozen edge between the same two packages is now two
  lines. No new pair of packages depends on each other.

After them: `lint-imports` 42 kept, 0 broken; `tests/test_architecture.py` 18 passed; `ruff check` clean. The
orchestrator's own AST check: 19 definitions moved and identical apart from the two renames, 66 stayed, of which
five differ only by a function-local import of a moved name; `_robust_gate_verdict`'s source text is identical.

The structure golden rises by one in this step: `probe_completion` joins the import component that `probe_episodes`
is already in (it imports the core and is imported back by function-local imports until the evidence and controls
move out).

## Members and boundaries

`probe_episodes.py`: **3,662 → 3,019 lines**. New `probe_completion.py`: **684 lines**.
19 definitions, 610 original definition lines; 618 after eight comment lines.

| Member | Base line | New line | Definition lines |
|---|---:|---:|---:|
| `persist_episode_beliefs` | 2839 | 31 | 33 → 33 |
| `_evaluate_completion → evaluate_completion` | 2877 | 66 | 153 → 161 |
| `voi_probe_site_active` | 3032 | 229 | 4 → 4 |
| `value_decides_episode` | 3038 | 235 | 18 → 18 |
| `robust_gate_applies` | 3058 | 255 | 17 → 17 |
| `_latest_observation_session` | 3077 | 274 | 9 → 9 |
| `episode_maximum_binds` | 3088 | 285 | 15 → 15 |
| `_plausible_actions_agree` | 3105 | 302 | 40 → 40 |
| `robust_gate_counterfactual` | 3147 | 344 | 30 → 30 |
| `_robust_completion_override` | 3179 | 376 | 25 → 25 |
| `_robust_gate_verdict` | 3206 | 403 | 53 → 53 |
| `robust_gate_completion` | 3261 | 458 | 15 → 15 |
| `_record_robust_selection_forecast` | 3278 | 475 | 39 → 39 |
| `_surface_key` | 3319 | 516 | 20 → 20 |
| `_complete` | 3341 | 538 | 26 → 26 |
| `_complete_on_value_stop` | 3369 | 566 | 29 → 29 |
| `_value_of_information_stop` | 3400 | 597 | 36 → 36 |
| `close_diagnostic_segment` | 3508 | 635 | 36 → 36 |
| `_set_target_decision → set_target_decision` | 3546 | 673 | 12 → 12 |

The reference graph (`reference_graph.json`) has no core caller of a moved
name. `_surface_key` moves: its only reader is the moved evaluator; no remaining
definition reads it. `_record_generation_need` stays because lifecycle entry and
retargeting also use it. `_observation_features` stays with evidence and is not
read by completion. No additional constant moves. Core imports into completion:
`EligibleInstrument`, `EpisodePosterior`, `eligible_instruments`, and
`_record_generation_need`. **The latter is the only private cross-module import**;
there is no private completion import back into the core.

Five function-local import sites in `probe_episodes.py` (six calls):

| Remaining function | Imported completion name |
|---|---|
| `probe_value_block_reason` | `robust_gate_counterfactual` |
| `record_episode_evidence` | `persist_episode_beliefs` |
| `_record_presentation_observation` | `close_diagnostic_segment` (two calls) |
| `stop_diagnosing_and_teach` | `set_target_decision` |
| `episode_contract` | `voi_probe_site_active` |

No top-level completion import in core; no re-export. `causal_orchestrator.py`
is byte-identical to HEAD: **zero import-line changes**.

## Stopping rules, in order

Each of these eight completion branches has one new reason comment. The terminal
status guard, pending-items park and continue returns return None, not completion.

1. `observation_budget_exhausted` (episode count cap binds).
2. `action_equivalent` (unstable posterior, common repair).
3. `couldnt_reliably_distinguish` (deciding robust gate's abstention).
4. `value_of_information_stop` (unstable posterior).
5. `decision_stable` (stable posterior plus breadth).
6. `fast_path_strong_claim` (strong prior plus cross-facet corroboration).
7. `action_equivalent` (stable but breadth-short).
8. `value_of_information_stop` (stable but breadth-short).

The 9-line module docstring lists all eight and the value/robust gate precedence.
The value site's off-path check is unchanged. `voi_stopping.ROBUST_GATE` remains
`"probe_episodes._robust_completion_override"`: persisted reason bytes, not dispatch.
The K9.0 verdict was read in `k9-diagnosis-strategy-2026-11-14.md` at “K9.0 (behaviour”.
`_robust_gate_verdict` and the selection it calls remain unchanged; no behavior fix.
No new product bug was established, so no bug-ledger row was added.

## P1–P5

- **P1 PASS:** 19/19 moved definitions AST-identical after the two definition-name
  renames; exactly those 19 definitions lost from core. 60/60 remaining definitions
  AST-identical after removing the five exact local imports and normalizing the
  one `set_target_decision` call. `_robust_gate_verdict` source text byte-identical;
  `probe_robust.py` and `robust_selection.py` unchanged. Small source diffs for both
  renames and the core call are in `diff__evaluate_completion.txt`,
  `diff__set_target_decision.txt`, `diff_stop_diagnosing_and_teach.txt`; the other
  renamed caller sites are `probe_blocks.end_diagnostic_block`, the placement test,
  and the cutover test. No executable evaluator line changed except its name.
- **P2 PASS with accepted difference:** run-1 baseline descriptors verified before
  same-process object comparisons: 19 functions, **57 matching global reads**,
  **1 expected difference (`__name__`)**. Relocated definitions match by member;
  core definitions retain their unchanged AST and home; other objects use identity.
  Full base/tip tables: `base_resolution.json`, `tip_resolution.json`. The logger
  now names `learnloop.diagnosis.probe_completion` as required. No test/config
  selects the old logger for this message; no logger selector was changed.
  No src/tests/scripts consumer of the moved functions' module metadata was found.
- **P3 audited:** one base patch of the old module, below. No remaining old-module
  patches/assignments, alias attribute calls, getattr dispatch, or stale moved
  mock/monkeypatch strings were found. The sole old qualified completion string
  retained is the immutable `ROBUST_GATE` value above.
- **P4 PASS:** identity pins and all 18 diagnosis journeys passed within the 406
  passes. Both test files, their identity/shape/journey golden bytes and the
  structure golden are unchanged; no writer flag or `--write` used. The journey
  helper's two close-segment calls now use the completion module.
- **P5 INCOMPLETE:** import direction holds. `ruff check` passes. `lint-imports`
  fails as above; architecture registries remain unchanged. `pyproject.toml` only
  repoints `curriculum.golden_path_run -> diagnosis.probe_episodes` to completion;
  no new exception added. The scheduler's old core ignore remains necessary.

Top-level completion imports: future annotations; `json`; `logging`;
`typing.Any/Mapping/Sequence`; `clock.Clock/utc_now_iso`;
`db.repositories.ProbeEpisodeRecord/Repository`; the four core names listed above;
`probe_hypotheses.strong_prior_claim`; `canonical_projection.surface_group_id`;
`vault.models.LoadedVault`.

| Base patch | Consuming globals after move | Result / T4 decision |
|---|---|---|
| `test_probe_robust_cutover.py:169`, `pe._robust_completion_override` | `evaluate_completion.__globals__` in completion | Repointed to `completion._robust_completion_override`; assertion unchanged. A plain-value replacement would need seeded qualifying observations, a pinned channel and remaining instruments to traverse the actual gate, exceeding the brief's small (~10-line) port; the existing test deliberately bypasses those prerequisites. |

Updated caller files by directory: **src 4 external** (probe_blocks, scheduler,
golden_path_run, evsi_calibration/policies), plus the **5 local sites** in core;
**tests 7** (including one helper); **scripts 0**; **vault _scripts 0**.
Explanatory-only references: `voi_stopping.py`, `test_evsi_calibration_sim.py`, and
one hand-written vault note, `Concepts/Diagnosis and Remediation.md`. No Journeys
directory exists here. Generated Reference notes and vault generators untouched.

## Ratchets

The required stock ratchet tests pass, but `refactor_measures.tracked()` uses
`git ls-files` and omits the untracked new module. A scratch-only remeasurement
injecting that one file into its input gives the numbers that landing would see:

| Metric | Base/golden | Stock uncommitted run | Including new module |
|---|---:|---:|---:|
| largest_import_component | 143 | 143 | **144** |
| modules_in_an_import_cycle | 249 | 249 | **250** |
| first_level_packages | 46 | 46 | 46 |
| first_level_root_modules | 35 | 35 | 35 |
| first_level_root_modules_not_upgrade | 35 | 35 | 35 |
| functions_over_200_lines | 72 | 72 | 72 |
| comment_lines_naming_a_stage_artifact | 2371 | 2371 | 2371 |
| test_files_named_for_a_stage | 184 | 184 | 184 |

`learnloop.diagnosis.probe_completion` joins the largest component. No golden was
written. Scratch output: `ratchets-including-new.txt`, `tip_structure_including_new.json`.

## Commands and results

`T`/`PY` are the supplied wrappers in the scratch directory. Test commands ran
serially, each with explicit file arrays and at most four workers.

- `$T tests/test_identity_pins.py tests/test_diagnosis_journey_golden.py tests/test_architecture.py tests/test_test_layout.py tests/test_structure_ratchets.py tests/test_cli_help_snapshot.py -q -n 4`: **406 passed, 2 failed**, 45.93 s. Failures above.
- `$PY python scripts/affected_tests.py --help`: exit 0.
- `$PY python scripts/affected_tests.py --base HEAD --json`: exit 0; selects
  `tests` because pyproject changed. Used the prescribed text-match fallback:
  **73 files**, excluding matching `test_mobile_v3_probes.py`; the other two known
  startup-hanging files do not match and were also never run.
- `bash "$S/run_affected_chunk.sh" 1`: `$T <60 quoted explicit paths> -m "not arc_close" -n 4 -q`: 13 failed, 9838 passed, 19 skipped in 170.15s (0:02:50).
- `bash "$S/run_affected_chunk.sh" 2`: `$T <13 quoted explicit paths> -m "not arc_close" -n 4 -q`: 8 failed, 407 passed, 3 skipped in 35.58s.
- `$PY ruff check`: **passed** (initial run identified four unused imports caused
  by extraction; those were removed and the final check passed).
- `$PY lint-imports --no-cache`: **41 kept, 1 broken**; output above.
- `$PY python "$S/prove_completion.py"`: exit 0; outputs P1/P2/P5 and stock metrics.
- `$PY python "$S/audit_completion_refs.py"`: exit 0; one base patch, zero stale references.
- `$PY python "$S/measure_completion_untracked.py"`: exit 0; actual rises above.
- `git diff --check`: passed.

The affected chunks' **19 non-architecture failures** are all socket-creation
`PermissionError: [Errno 1] Operation not permitted`, not verified:

| Unedited test file | Socket-blocked failures |
|---|---:|
| `tests/test_probability_prep.py` | 2 |
| `tests/test_sidecar_contract.py` | 2 |
| `tests/test_cli_generate_practice.py` | 7 |
| `tests/test_sidecar_tutor_qa.py` | 8 |

Exact node IDs and traces are in `affected-chunk-1.txt` and `affected-chunk-2.txt`.
The two architecture failures recur in chunk 1; none of their assertions was changed.
No other failure occurred. Bubblewrap-specific behavior was not verified.
The three excluded startup-hanging files were `test_mobile_v3_probes.py`,
`test_ih6_workbench_open_item.py`, and `test_ih4_preferences_inform_router.py`.

No full suite or landing gate run. No network, model calls or vault generators;
no credentials/config read; no main checkout/other worktree touched. Final `.pytest_tmp` check: empty, no `run-*` directories or killed-run remnants.

## K9.10 handoff

Completion's new home and public names are implemented, but resolve the architecture
registration stop before landing. Presentations still have a local
`robust_gate_counterfactual` import; evidence has local belief/close-segment imports,
and controls have local target-decision/site imports. Those later moves can turn
the imports downward/top-level. `_observation_features` stays with evidence;
`_surface_key` is already owned by completion. Expect the temporary cycle increase
until later splits remove the back edges. Review the one private patch and the
persisted ROBUST_GATE string first. Do not alter the robust verdict/selection.

All scratch artifacts are under:
`/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/73b37aee-2550-41c4-88a8-8730b0f3c0c0/scratchpad/refactor-k99/`.
