# Import cycle edges A and B

Pure moves:

- `GradingValidationError` and `resolved_rubric`: `attempts/grading.py` → `vault/models.py`, which already defines every model they need; no destination imports added. Grading explicitly re-exports both original objects. Only `learner/assessment_contracts.py` changes its rubric import; other importers stay unchanged.
- `maybe_promote_self_tagged_fatal_error`: `content/proposals/proposals.py` → new `content/proposals/self_tagged_fatal.py`; its sole caller, `attempts/attempts.py`, imports the new module. No old re-export. The existing lower attempts modules outside cycles cover grading, evidence, hints, salience, stuck answers, traces and calibration, rather than reviewed rubric proposals. The new proposals module is the first natural permitted destination and remains outside every cycle. One source file is added; that increase is intentional.

Pre-move searches of `src/`, `tests/`, `scripts/` and `apps/` found no runtime reliance on the exception's module or qualified name, pickling, or serialized qualified type. `blind_grading.py` has a documentation reference to the old path (still exported); `cli/ai_compare.py` uses the unchanged short class name. The sidecar's existing `isinstance` check imports the preserved exception re-export. Tests neither import nor monkeypatch/setattr/patch the promotion name at its old path; no test import needed updating.

## AST proof

Scratch `l1a_ast_proof.py` parses `git show HEAD:<old path>` and the moved definitions and compares `ast.dump(..., include_attributes=False)`. Output:

```text
PASS GradingValidationError: AST-identical (positions ignored)
PASS resolved_rubric: AST-identical (positions ignored)
PASS maybe_promote_self_tagged_fatal_error: AST-identical (positions ignored)
3/3 moved definitions are AST-identical.
PASS grading re-exports: exception and function identity preserved; isinstance preserved.
```

## Measures and contracts

`py.sh python scripts/refactor_measures.py --json <scratch>/measures-{before,after}.json`:

| Measure | Before | After |
| --- | ---: | ---: |
| largest_import_component | 186 | 144 |
| modules_in_an_import_cycle | 279 | 250 |
| import_component member list size | 186 | 144 |

Regenerated with `py.sh python tests/test_structure_ratchets.py --write`, retaining every ceiling that did not fall. Only the two cycle numbers and their component membership list changed. An additional sweep explicitly including the new untracked module gives the same numbers and confirms that module is outside every cycle; the standard measure enumerates tracked files, so its source file count gains one after staging.

Removed only `learnloop.learner.assessment_contracts -> learnloop.attempts.grading` from `pyproject.toml` (base line 1188). Import-linter reports no unmatched or unnecessary exceptions; no others removed.

## Verification

All tools use the supplied isolated `py.sh` and tests use `t.sh`, with explicit paths and at most four workers. Scratch and logs are in `/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/73b37aee-2550-41c4-88a8-8730b0f3c0c0/scratchpad/refactor-l1a/`.

- `t.sh tests/test_structure_ratchets.py tests/test_architecture.py tests/test_test_layout.py tests/test_identity_pins.py -q -n 4`: **312 passed** (37.54 s).
- `py.sh lint-imports --no-cache`: **42 kept, 0 broken**, 1,258 files / 14,130 dependencies; no unmatched or unnecessary ignores.
- `py.sh ruff check`: **all checks passed**. The initial run identified the now-unused `PracticeItem` import in proposals.py; that import was removed.
- `py.sh python scripts/affected_tests.py`: exit 0; selected `tests` because `pyproject.toml` affects every test (1,429 test files). Used the requested fallback instead of running the whole suite.
- `bash <scratch>/l1a_focused_tests.sh`: selected every `tests/test_*.py` mentioning `resolved_rubric`, `GradingValidationError`, `assessment_contracts` or `maybe_promote_self_tagged_fatal_error`, plus existing `test_attempts*.py`. One chunk of **31 explicit files**, passed as a quoted bash array to `t.sh ... -q -n 4`: **1,014 passed, 3 skipped, 8 failed, 22 errors** (63.37 s).
- Extra direct promotion coverage: `t.sh tests/test_self_attributed_misconceptions.py -q -n 4`: **19 passed** (2.26 s), including repeated-tag promotion, exactly-once, threshold and already-fatal behavior.
- Both full measure invocations, golden regeneration and the additional sweep including the new module completed successfully. `git diff --check` passed.

Fallback files (under `tests/`; the exact newline-delimited list is also in scratch `focused-tests.txt`):

```text
test_architecture.py                   test_assessment_contracts.py
test_attempts.py                       test_blind_grading_contract.py
test_causal_attribution_p0.py          test_characterization_assessment_exam.py
test_chatgpt_plan_workspace.py         test_codex_grading_validation.py
test_diagnosis_contract.py             test_diagnosis_history_modes.py
test_diagnosis_input_provenance.py     test_facet_belief_successor_derivation.py
test_field_workbench_signals.py        test_followup_fg1c_codex_review.py
test_grading_support.py                test_pfc_unassessed_readers.py
test_pfc_unverified_unassessed.py       test_probability_prep.py
test_proposal_persistence.py           test_reader_recap_review_r2.py
test_reader_workbench_rw2a.py           test_required_method_grading.py
test_required_method_rereview.py       test_required_method_round3.py
test_ro1_projection.py                 test_rospeed_join.py
test_route_rules_in_grader.py          test_router_card.py
test_teach_back.py                     test_ux_phase4_feedback.py
test_voi_forecasts.py
```

Sandbox socket creation fails with `PermissionError: [Errno 1] Operation not permitted`: all 22 setup errors in `test_chatgpt_plan_workspace.py`, and `test_probability_prep.py::{test_decider_end_to_end_through_the_fake_endpoint,test_rate_limits_retry_within_caps_and_malformed_answers_fail_closed}`. These require a local fake HTTP server and were not changed.

Six other failures in unedited tests were left unchanged; no claim is made that they pass on the base revision. Full tracebacks and all failing node IDs are in scratch `focused-chunk-1.log`:

- `test_required_method_rereview.py::test_f20_a_partial_judgment_resumes_without_any_paid_pipeline_work`: family status `complete` instead of `judgment_incomplete`, six candidates rejected.
- `test_required_method_round3.py::test_a_published_pf_variant_is_presented_with_the_parents_instruction`: no published item to unpack.
- `test_required_method_round3.py::test_f20_a_missing_judgment_alone_fits_max_calls_one`: `complete` instead of `judgment_incomplete`.
- `test_required_method_round3.py::test_f20_a_resumable_job_resolves_no_pipeline_route_and_plans_no_pipeline_work`: dry plan contains seven roles instead of none.
- `test_required_method_round3.py::test_f22_an_interrupted_selection_is_finished_before_any_judgment`: `complete` instead of `cancelled`.
- `test_required_method_round3.py::test_f22_a_partial_selection_left_by_an_earlier_run_is_finished_first`: `complete` instead of `judgment_incomplete`.

Neither A nor B was stopped. The full suite, unrestricted socket-dependent tests, baseline reproduction/root cause of the six remaining failures, and the orchestrator's landing gate were not verified here. No tests or behavioral assertions were changed.

## What L1 still needs

The supplied edge map leaves C, D and E over the pure-move stop rule (about three definitions), so none was changed:

- C: notes access in `diagnosis/text_gaps/sources.py` → `source_retrieval/note_gaps.py`. Six direct definitions span 135 lines; estimated closure is 18 bindings / 239 lines and reaches reader/notes helpers. Restoring C alone to the map's five-edge cut gives largest component 142.
- D: `diagnosis/probe_episodes.py` → `diagnosis/probe_blocks.py`, planned as K9.9–K9.11. Six direct definitions span 347 lines; estimated closure is 12 bindings / 461 lines with dependencies back into probe_episodes. Restoring D alone gives 126.
- E: `reader/reader_progression.py` → `content/authoring/practice_generation.py`. Two direct definitions need an estimated closure of 18 bindings / 637 lines and reach commissioning, depth rungs and learner mastery. Restoring E alone gives 126.

Those restoration figures refer to the map's hypothetical five-edge cut, not additional measurements of this change. No complete lower extraction for C–E has been established.
