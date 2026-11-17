# K9.11: probe evidence and learner controls

Base `7b1dd633e4446ed498e2894d06de5a62826ce35e` on
`refactor/k9.11-probe-evidence`. Structure only. This second run
retained the interrupted run's move, caller/test ports, import registries, K9-30
deletion and note edit. It independently reran the proofs against the preserved
pre-edit captures (verified equal to `git show HEAD`), corrected two explanatory
source references, completed the tests and measurements, and wrote this record.
Only results produced in this second run are reported below.

Scratch root (`S`):
`/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/73b37aee-2550-41c4-88a8-8730b0f3c0c0/scratchpad/refactor-k911`.
`T=$S/t.sh`, `PY=$S/py.sh`. All Python/tools used `PY`; all tests used `T`,
serial commands, three workers (two on the interrupted chunk's retry). No base
capture was regenerated from the edited tree.

## Members and boundaries

`probe_episodes.py`: **2,338 → 1,367 lines**. New `probe_evidence.py`: **816**;
new `probe_controls.py`: **185**. `probe_blocks.py`: **528 → 521**.
Evidence moves 12 definitions, 748 original definition lines, 740 after import
hoists. Controls moves four definitions and one constant, 151 original lines,
140 after hoists. Counts include decorators.

| Member | Base line | New line | Definition lines, base → new |
|---|---:|---:|---:|
| `record_episode_evidence` | 1390 | 54 | 80 → 77 |
| `record_presentation_activity_classification` | 1472 | 133 | 51 → 49 |
| `_presentation_contamination` | 1525 | 184 | 13 → 13 |
| `_record_presentation_activity_fact` | 1540 | 199 | 44 → 44 |
| `_robust_observation_snapshot` | 1586 | 245 | 31 → 31 |
| `_dual_write_probe_grade` | 1619 | 278 | 81 → 81 |
| `dual_write_presentationless_probe_grade` | 1702 | 361 | 27 → 27 |
| `dual_write_regraded_probe_grade` | 1731 | 390 | 80 → 80 |
| `_record_presentation_observation` | 1813 | 472 | 264 → 261 |
| `_attempt_rubric_score` | 2079 | 735 | 5 → 5 |
| `_assess_longform_trace` | 2086 | 742 | 46 → 46 |
| `_observation_features` | 2134 | 790 | 26 → 26 |
| `PROBE_ASSISTANCE_RESTRICTIONS` (controls) | 69 | 37 | 7 → 7 |
| `StoppedCheck` (controls) | 2166 | 46 | 7 → 7 |
| `stop_diagnosing_and_teach` (controls) | 2174 | 55 | 58 → 49 |
| `episode_contract` (controls) | 2258 | 106 | 35 → 33 |
| `next_probe_item` (controls) | 2295 | 141 | 44 → 44 |

The base top-level reference graph has **zero core readers of moving names**.
Lifecycle, instruments, `episode_posterior`, `_bayes_update` and the likelihood
helpers remain together. `_first_intervention_at`,
`_observation_likelihoods_from_row`, `_fired_error_types`, `_item_max_points`,
`_incidental_likelihoods`, and `_resolved_slot_map_from_snapshot` remain because
posterior replay reads them directly or through its likelihood reader.
The five private names newly imported across modules, all core → evidence,
are `_bayes_update`, `_entropy`, `_fired_error_types`, `_item_max_points`, and
`_resolved_slot_map_from_snapshot`. Controls imports no private core name.
The existing core → completion `_record_generation_need` and core →
presentations `_entropy` private imports are unchanged; these and the five
evidence bindings are all private imports among the six ordered modules.
No other exclusive helper/constant was found. No re-export was added.

`_first_error_from_block` becomes `first_error_from_block`; its two callers are
`probe_blocks.end_diagnostic_block` and `probe_controls.stop_diagnosing_and_teach`.
All edges among the six ordered modules are top-level and downward.
Core imports none of the other five; blocks imports neither evidence nor controls.

Local imports hoisted (12 imported bindings across these sites):

| Function | New top-level binding(s) |
|---|---|
| evidence `record_episode_evidence` | completion `persist_episode_beliefs`; blocks `block_complete`, `end_diagnostic_block` |
| evidence `record_presentation_activity_classification` | presentations `validate_presentation_for_submission` |
| evidence `_record_presentation_observation` | presentations `validate_presentation_for_submission`; completion `close_diagnostic_segment` |
| controls `stop_diagnosing_and_teach` | completion `set_target_decision`; blocks `first_error_from_block`, `block_observation_rows`, `build_typed_transition_decision`, `settle_block_answers` |
| controls `episode_contract` | completion `voi_probe_site_active` |

Additionally, blocks' existing local core import in
`_next_observation_does_not_pay` was hoisted into its existing top-level core
import, so every edge in the specified order is top-level.

## Deletions

Fresh searches and read-only fixture queries: `run2_audit.py` → `run2_audit.txt`;
star-import search: `run2_star_exports.txt` (empty).

1. `git grep -n -w abandon_episode HEAD -- src apps scripts tests
   docs/learnloop-architecture-vault/_scripts`: exactly the definition at
   `probe_episodes.py:2234`, test import at `test_attempt_completion.py:25`, and
   its calls at base lines 205 and 228. The same current-tree search has zero hits.
   Thus no product import (top-level, local or importlib), string dispatch,
   sidecar/CLI/TUI/phone/desktop call, replay, rebuild or upgrade entry reaches it.
   The base module search for `__all__|importlib|__import__` and the full runtime/
   test/script search for `probe_(episodes|blocks) import \*` both have no matches.
   Deleted **19 definition lines**, with no exclusive helper to delete.

   | Test case in `test_attempt_completion.py` | Fate |
   |---|---|
   | `test_resumed_completion_routes_to_the_episode_the_attempt_was_applied_under` | Ported to a direct repository status value (`abandoned`, `learner_abandoned`); tests routing to the original episode, assertion unchanged. |
   | `test_resumed_diagnostic_completion_evaluates_followups_after_its_episode_ended` | Same value port with its fixed clock; tests resumed followups, assertion unchanged. |

   No abandon-subject case existed, so no test case was deleted. These fixtures
   need a terminal episode, not the removed control's presentation side effects.

2. `git grep -n -E 'joint_block|block_size' HEAD -- src apps`: the sole
   `joint_block` occurrence is the reader in blocks at base line 99; the other
   two hits are the unrelated `max_block_size` config declaration/registration.
   Current `git grep -n joint_block -- src apps`: no matches. No presentation
   selection-component writer remains. Both tracked fixture databases were
   opened with `sqlite3.connect(file_uri + '?mode=ro', uri=True)` through `PY`.
   Every selection-named presentation column was searched for `%joint_block%`;
   `fixtures/migration_head/state.sqlite`: **0 rows**;
   `fixtures/mvp017_route_check_replay/state.sqlite`: **0 rows**.
   K9-30 Fix and Status now record removal here. Only this executable branch
   was removed (surrounding docstrings updated for the surviving behavior):

   ```diff
   -    if components.get("joint_block"):
   -        target = int(components.get("block_size") or 0)
   -        if target <= 0:
   -            target = vault.config.probe.block.default_block_observations
   -        return len(segment_rows) >= target
   ```

## Proofs P1–P6

`PY python "$S/prove_move.py"` → `run2_proofs.txt`, exit 0:

```text
P1: 17 moved definitions/constant identical after exact import hoists and rename; 31 remaining definitions/assignments AST-identical; lost exactly moved + abandon_episode
P1 blocks: exact five-line branch deletion, rename, call rename, one import hoist; remaining bodies identical
P2: 41 captured global reads match (relocated members/core functions verified by member identity + P1); 12 hoisted import bindings identical; __name__ reads: 0
P5: all six-module edges top-level/downward; core has zero downstream imports
P3: 0 patches/assignments of source-module globals in base audit; 0 current patches to old source modules; no source-text assertion to port
P6: 0 stale from-imports, module-alias/qualified attributes, or qualified strings; 0 old metadata/logger selectors
Protected files: all byte-identical to HEAD
```

- P1 exceptions are individually shown in `run2_p1_exceptions.diff`: the five
  moved functions with import hoists, controls' renamed call, blocks' renamed
  definition/call, hoist, deletion and docstrings. The posterior and Bayes update
  are AST-identical. No ID, SQL, message/log/reason bytes or answer-write order
  changed. Completion and presentations are byte-identical to HEAD.
- P2 compares the original **pre-edit** `base_resolution.json` capture, verifies
  it against the original source executed in a base namespace, then compares
  against tip through `PY`. Relocated objects resolve by home/member plus P1;
  unchanged external objects by identity; the moved restrictions dictionary by
  equal value. New table: `run2_tip_resolution.json`. Fifteen moved functions
  checked; the other members are a dataclass and a dictionary.
- P3 was also freshly audited at **base and tip** by `run2_audit.py`, including
  aliases, `mock.patch`/`patch.object`, `monkeypatch.setattr`, attribute
  assignments and `getsource`. `run2_patches.json` is `{"base": [], "tip": []}`.

  | Source-module patch | Consuming globals after move | T4 action |
  |---|---|---|
  | None in base or tip | No patch can silently miss its consumer | No private patch or source assertion needed porting/repointing |

- P4: **PASS**, unchanged identity pins and all diagnosis journeys in the final
  **408 passed** core command. Test files, identity/shape goldens, journey JSON
  and structure golden unchanged; no writer option used. Only the journey
  helper's control calls/imports were repointed.
- P5: `lint-imports --no-cache`: **42 kept, 0 broken**. Top-level imports listed
  below and in `run2_imports.json`.
- P6 scans `src/`, `tests/`, `scripts/`, and the vault `_scripts` via AST
  from-imports, old module aliases/qualified attributes, and fully qualified
  moved-name strings: **zero stale references**. Additional short-name metadata/
  logger search found only two explanatory docstring references, now corrected
  (`teacher/from_check.py`, `diagnosis/causal_activity_policy.py`). Final search
  is recorded in `run2_metadata_search.txt`.

Moved definitions' `__module__` follows their new home. Their top-level
`__qualname__` spelling remains unchanged. No moved function reads `__name__`
or creates a module-named logger, so no logger selector changed. No consumer
selects the old module/qualname metadata.

All new top-level imports (prefixes below are under `learnloop`):

- evidence: future annotations; `typing.Any/Iterable/Mapping`;
  `clock.Clock/parse_utc`; `db.repositories.ProbeEpisodeRecord/ProbePresentationRecord/Repository`;
  `diagnosis.probe_families.APPROVED_DIAGNOSTIC_GRADING_SOURCES/CompiledInstrument/InstrumentCard/classify_outcome/instrument_observation_likelihoods/record_real_observation_counts`;
  `diagnosis.probes.HypothesisSet`; `attempts.outcome_schemas.COARSE_RESPONSE_SLUG`;
  `vault.models.LoadedVault`; core's five private names above plus
  `episode_hypothesis_set/episode_posterior`; blocks `block_complete/end_diagnostic_block`;
  completion `close_diagnostic_segment/persist_episode_beliefs`;
  presentations `validate_presentation_for_submission`.
- controls: future annotations; `dataclasses.dataclass`; `typing.Any`;
  `clock.Clock/utc_now_iso`; `db.repositories.Repository`; `vault.models.LoadedVault`;
  core `EligibleInstrument/eligible_instruments/episode_hypothesis_set/episode_posterior`;
  blocks `first_error_from_block/block_observation_rows/build_typed_transition_decision/settle_block_answers`;
  completion `set_target_decision/voi_probe_site_active`.

## Registries and callers

- `pyproject.toml`: repoint the existing frozen
  `attempts.attempts -> diagnosis.probe_episodes` edge to `probe_evidence`.
  Attempts no longer imports core; no duplication or new package pair needed.
- `tests/architecture_function_local_domain_imports.txt`: same attempts edge
  repointed; evidence's local `attempts.grade_resolution` and
  `attempts.outcome_schemas` edges moved from core to evidence (three old lines
  out, three new lines in).
- `REGISTERED_SQL_OWNERS`: unchanged; neither new module contains SQL. A
  mistaken temporary evidence entry in this run was removed after inspection;
  the full core test command was rerun successfully.
- Parameter paths unchanged: the registered `FALLBACK_FAMILY_VERSION` stays in
  core. `tests/goldens/structure.toml` deliberately unchanged.
- K9-30 Fix/Status updated; no new behavior bug found and no K9-50+ row needed.

Caller files by directory: **src 3 external**, **tests 9** (including one helper),
**scripts 0**, **vault _scripts 0**. The three src callers are attempts (four
function-local imports, including the regrade publication door), TUI practice,
and sidecar practice. Tests: diagnosis_journey_helpers,
test_daily_loop_lo_lifecycle_serving, test_dual_authority_administration,
test_grade_resolution_pipeline, test_instrument_servability_journeys,
test_probe_episodes, test_teach_handoff_stop_settles, test_today_surfaces,
test_voi_stopping. Additionally, test_attempt_completion has the two deletion
ports above; blocks has the renamed call. Two source docstrings and the
hand-written Concepts/Diagnosis and Remediation note name the new homes.
No Journeys directory exists. Generated Reference notes/generators untouched.
causal_orchestrator, causal_reads, machine_checks and causal_cold_verification
are byte-identical to HEAD.

## Import component measurement

`PY python "$S/run2_measure.py"` uses the measure's serial parser/graph and
injects the two untracked modules into its file list. Base source is read with
`git show HEAD` for changed files; no checkout, index or golden is written.

| Metric | Base/golden | Stock uncommitted tip | Including both new files |
|---|---:|---:|---:|
| largest_import_component | 149 | 148 | **150** |
| modules_in_an_import_cycle | 255 | 254 | **256** |

The core→blocks edge is cut, but the global ratchet **rises by one**. Evidence
joins; controls stays outside; no old member leaves. The stock tests omit the
untracked evidence node and the returning attempts→evidence edge. The
orchestrator must account for 150/256 when landing; the golden is not edited here.
`run2_measure.txt` and `run2_structure.json` contain the measurements. All five
other specified modules remain in the largest component. One actual import
chain per member (all names below prefixed `learnloop.`):

```text
diagnosis.probe_episodes -> diagnosis.probe_instance_generation -> diagnosis.probe_episodes
diagnosis.probe_completion -> diagnosis.calibration_sessions -> placement.state -> attempts.reveal_ledger -> diagnosis.remediation -> diagnosis.causal_orchestrator -> diagnosis.probe_presentations -> diagnosis.probe_completion
diagnosis.probe_presentations -> diagnosis.probe_episodes -> placement.state -> attempts.reveal_ledger -> diagnosis.remediation -> diagnosis.causal_orchestrator -> diagnosis.probe_presentations
diagnosis.probe_blocks -> diagnosis.split.jobs -> attempts.grading -> diagnosis.discrimination_profiles -> diagnosis.scoreboard -> substrate.replay -> attempts.attempts -> diagnosis.probe_evidence -> diagnosis.probe_blocks
diagnosis.probe_evidence -> diagnosis.probe_blocks -> diagnosis.split.jobs -> attempts.grading -> diagnosis.discrimination_profiles -> diagnosis.scoreboard -> substrate.replay -> attempts.attempts -> diagnosis.probe_evidence
```

## Commands and results

- `T tests/test_identity_pins.py tests/test_diagnosis_journey_golden.py tests/test_architecture.py tests/test_test_layout.py tests/test_structure_ratchets.py tests/test_cli_help_snapshot.py -q -n 3`:
  first run **407 passed, 1 failed** (48.52 s), solely the temporary idle SQL
  owner registration described above; final repeat **408 passed** (49.92 s),
  `run2_core_tests_final.txt`.
- `PY python "$S/run2_audit.py"`: exit 0; proof/search/fixture outputs above.
  Selects **71 affected files** by source/new module and moved/renamed-name text;
  excludes the three prescribed hanging startup files. Lists are
  `run2_affected.json`, `run2_affected_1.txt` (60), `run2_affected_2.txt` (11).
  `run2_affected.sh` reads a quoted bash array and invokes only `T`.
- `bash "$S/run2_affected.sh" 1`: `T <60 explicit paths> -m "not arc_close" -n 3 -q`:
  interrupted with Ctrl-C, **exit 130**, after progress stalled near 92%; no
  completed result counts. The remaining worker's newest fixture directory
  was `test_every_other_registered_method_answers_403` in `test_mobile_rpc.py`;
  its `world` fixture enters Starlette `TestClient`, the same startup pattern
  as the prescribed mobile exclusion. No result from the incomplete command
  is counted as verified. After a two-minute pause and removal of its exact
  `run-3-oj52ymkm` directory, retry omits this additional sandbox hang.
- `bash "$S/run2_affected.sh" retry 2`: `T <59 explicit paths> -m "not arc_close" -n 2 -q -o faulthandler_timeout=30`:
  **10,131 passed, 19 skipped, 12 failed** (169.52 s), exit 1;
  `run2_affected_retry.log`. All twelve fail at socket creation with
  `PermissionError: [Errno 1] Operation not permitted`, not an outcome assertion.
  `run2_affected_retry.txt` contains the explicit paths.
- `bash "$S/run2_affected.sh" 2`: `T <11 explicit paths> -m "not arc_close" -n 3 -q -o faulthandler_timeout=30`:
  **397 passed, 3 skipped** (22.22 s), exit 0; `run2_affected_2.log`.
- `PY ruff check`: **All checks passed** (`run2_ruff.txt`).
- `PY lint-imports --no-cache`: **42 kept, 0 broken** (`run2_lint_imports.txt`).
- `PY python "$S/prove_move.py"`: exit 0, P1/P2/P3/P5/P6 above.
- `PY python "$S/run2_measure.py"`: exit 0, measurements above.
- `git diff --check`: passed.

Socket-blocked tests (all three files are unedited; exact node IDs/traces in
`run2_affected_retry.log`, summary in `run2_sandbox_failures.txt`):

| File | Socket-blocked failures |
|---|---:|
| `tests/test_probability_prep.py` | 2 |
| `tests/test_sidecar_contract.py` | 2 |
| `tests/test_sidecar_tutor_qa.py` | 8 |

These twelve are **not verified**, as is `tests/test_mobile_rpc.py` after its
observed startup hang. Prescribed exclusions: `test_mobile_v3_probes.py`,
`test_ih6_workbench_open_item.py`, `test_ih4_preferences_inform_router.py`.
The joint-block deletion is retained: neither a behavior assertion nor a
journey changed; the failures above are the sandbox's socket restriction.
No production behavior stop condition arose. Full suite/landing gate and
bubblewrap-specific behavior were not verified. No network/model calls,
vault generators, other worktrees or credentials/config were used.

Final `.pytest_tmp` check: no `run-*` directories remain. The interrupted
command's exact directory was removed through `PY`/`shutil.rmtree` after the
two-minute pause; completed commands removed their own directories. No test
command was OOM-killed in this run. All changes remain uncommitted for the
orchestrator.
