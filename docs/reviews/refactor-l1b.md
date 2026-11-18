# Three import-cycle cuts

Scratch: `/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/73b37aee-2550-41c4-88a8-8730b0f3c0c0/scratchpad/refactor-l1b/` (called `$S` below). All tools use `$S/py.sh`; all tests use `$S/t.sh`, explicit paths, at most three workers, one test command at a time. No golden or generated Reference note changed; no generators run.

## Cuts

| Cut edge removed | Definitions moved (HEAD source lines) | New home | Importers updated | Largest / any-cycle modules |
|---|---|---|---|---:|
| `diagnosis.text_gaps.provenance → diagnosis.text_gaps.sources` | `FIGURE_PREDICTION_PREFIX` 402, `FIGURE_EXPLANATION_SUFFIX` 406, `figure_prediction_id` 415–421, `figure_input_manifest` 450–470, `figure_input_keys` 473–489 (47 definition lines) | `diagnosis/text_gaps/figure_inputs.py` | src: 3 (sources, provenance, jobs); tests: 5; scripts: 0; vault scripts: 0 | 113 / 240 |
| `reader.reader_progression → content.authoring.practice_generation` | `section_generation_candidates` 61–100 (40 lines) | `reader/section_generation.py` | src: 1 sidecar handler; tests: 1 | 94 / 225 |
| `params.sensitivity_certificates → sim.sweep` | `_value_grid` 97–105 and `certify` 108–149 (51 lines); `_value_grid` has no other caller | `sim/certify.py` | src: 1 CLI file, two sites; tests: 0 | 84 / 220 |

Baseline HEAD `88b10fb90d`: **151 / 257**. Each largest-component measurement matches the supplied prediction exactly. Both figure constants move together; sources uses the prefix internally, and removes all moved names from `__all__`. Every external constant attribute read now targets the leaf, including the equality-only read in `test_ro2_history_protection.py`. No compatibility re-export is added.

**Import timing judgment:** provenance’s three figure-helper imports move from function-local to module-level. The moved section function retains its local authoring import, and `certify` retains its local `SweepEntry, run_sweep` import. Keeping that sweep import local differs from the suggested module-level arrangement: hoisting it would violate exact moved-definition AST identity and the changed-body stop rule. No moved body line changed; no new import-contract exception. Reader’s pre-existing `learning_objects_for_section` re-export remains, with the same F401 marker as its adjacent re-exports.

### Members leaving the largest component

Names below omit only the `learnloop.` prefix; departures are relative to the preceding row, not all cycle membership.

- Cut 1 (38): `attempts.coldness_receipt`, `attempts.reveal_ledger`, `confidence_events`, `content.authoring.practice_leakage`, `diagnosis.calibration_sessions`, `diagnosis.causal_activity_policy`, `diagnosis.causal_attribution`, `diagnosis.causal_cold_verification`, `diagnosis.causal_discrimination`, `diagnosis.causal_orchestrator`, `diagnosis.causal_probe_coherence`, `diagnosis.causal_reads`, `diagnosis.diagnosis_adjudication`, `diagnosis.diagnostic_surface_supply`, `diagnosis.forecast_receipts`, `diagnosis.guided_redo`, `diagnosis.machine_checks`, `diagnosis.misconceptions`, `diagnosis.missing_vocabulary`, `diagnosis.probe_completion`, `diagnosis.probe_episodes`, `diagnosis.probe_hard_stops`, `diagnosis.probe_instance_generation`, `diagnosis.probe_presentations`, `diagnosis.probe_targeting`, `diagnosis.remediation`, `diagnosis.text_gaps.provenance`, `goals.certification_cold_probe`, `goals.exam_pool`, `learner.facet_evidence_timeline`, `learner_protection`, `placement.decisions`, `placement.signals`, `placement.state`, `scheduling.intent.recall_targets`, `scheduling.serving_exclusions`, `substrate.canonical_projection`, `tutor.durable_promotion`.

- Cut 2 (19): `hints.map_builder`, `hints.map_seeds`, `hints.maps`, `intent.control`, `reader.reader_dialogue`, `reader.reader_observations`, `reader.reader_progression`, `reader.recap`, `source_retrieval.compare`, `source_retrieval.find_sources`, `source_retrieval.kept_comparisons`, `source_retrieval.library_ask`, `source_retrieval.reader_tutor`, `source_retrieval.reading_paths`, `source_retrieval.section_coverage`, `source_retrieval.tutor`, `source_retrieval.vault_notes`, `tutor.reader_modes`, `tutor.tutor_qa`.

- Cut 3 (10): `params.sensitivity_certificates`, `scheduling.frame_constraints`, `scheduling.intent.feasibility`, `scheduling.intent.serving`, `scheduling.scheduler`, `scheduling.shadow_components`, `scheduling.staged_policy`, `sim.runner`, `sim.sweep`, `substrate.state_sync`.

## Proofs P1–P6

- **P1:** `py.sh python "$S/prove_moves.py"`: PASS **8/8 moved definitions/constants AST-identical**, positions ignored; original files lose exactly the specified bindings; **89 remaining top-level bindings** identical, except `sources.__all__` loses exactly moved entries and `provenance.figure_prediction_record` loses its named local import. Source import additions/removals are separately visible in the diff. `prove_callers.py`: PASS **345 remaining definitions** across changed Python files after removing import nodes, normalizing the specified module-alias reads/patch target, and normalizing the one updated Sphinx module reference in `enqueue_figure_explanation`. No SQL, message, log, reason or assertion text changed. `proofs.log`, `callers-proof.log` hold output.
- **P2:** `capture_globals.py` captured base global reads **before any edit** (`globals.log`). `prove_moves.py` reconstructs original imports/moved bindings from `git show HEAD:<file>` and verifies external global objects with `is`, signature/default equality, identical local-import ASTs, and the moved helper mapping. Figure functions read only the identical `json` module, builtins and the moved suffix literal. Section candidates reads the identical `learning_objects_for_section` object and `sorted`; certify reads identical `Path`, `certificate_from_sweep_report`, builtins and the AST-identical moved `_value_grid`. Literal constants retain exact type/value; their allocated string object identity is not a behavior guarantee (the first capture comparison using `is` correctly exposed separate allocations and was replaced by type/value checking). All six functions pass; annotations also retain their imports.
- **P3:** `audit_patches.py` scans original test ASTs, resolves source-module aliases and string patch targets, examines mock/monkeypatch calls and attribute assignments, and lists source-text review candidates (`patch-audit.txt`, `patch-sites.txt`, `name-sites.txt`). **One affected mutation:** `test_mobile_v4_reader.py`’s patch of `progression.section_generation_candidates` now patches `generation.section_generation_candidates`. Leaving it at progression would stop intercepting the sidecar. The adjacent `source_refs_for_section` patch stays on progression. No patch/assignment of the moved figure names, certify, `_value_grid`, or their old global bindings was found. The `inspect.getsource(S.learner_text)` assertion in the constant-equality test still reads sources; only its constant reads target the leaf. Other source-text candidates inspect fixture/config files or unrelated functions. No assertion weakened; the 345-definition caller proof checks test bodies too.
- **P4:** `tests/test_identity_pins.py` is byte-for-byte unchanged from HEAD; included in the **390 passed** core gate below.
- **P5:** `measure_cuts.py` writes `$S/measures_with_untracked.py`, a copy of `scripts/refactor_measures.py` changing only ROOT and `git ls-files` enumeration to `--cached --others --exclude-standard`; graph/structure logic is unchanged. `measure-{base,cut1,cut2,cut3}.json` hold each full result. Largest **151→113→94→84**; any-cycle **257→240→225→220**. All other ratchets unchanged: first-level packages **46**, root modules **35**, non-upgrade root modules **35**, functions over 200 lines **72**, stage-artifact comment lines **2370**, stage-named test files **184**. Non-ratcheted local-only edges **2802→2802→2803→2804**, modules holding them **577→576→576→577**; the extra sidecar/CLI destination edges account for growth. Three new source modules are untracked; the normal ratchet test passes and intentionally does not enumerate them yet. Final import-linter: **42 kept / 0 broken**. `verify_new_graph.py`: PASS all three new modules outside every cycle; the two orchestration modules have no incoming edge from the largest component; the figure leaf has no LearnLoop import. A final untracked-aware sweep remains **84 / 220** (`measure-final.json`).
- **P6:** `tests/test_architecture.py` discovers files dynamically and has no moved-name module inventory to alter. Its companion `architecture_function_local_domain_imports.txt` repoints `reader.reader_progression → content.authoring.practice_generation` to `reader.section_generation → content.authoring.practice_generation`, and deletes `params.sensitivity_certificates → sim.sweep` (the remaining local sweep import is inside sim). Vault `_scripts` inventories were inspected: no moved-name entries; module discovery is dynamic, so no generator script edit needed. Hand-written `Workflows/Reader to Practice Workflow.md` and `Concepts/Parameter Governance and Evaluation.md` gain the new module path and explicit function home. No `Journeys/` directory exists here. Old module doc references to certify, and jobs’ Sphinx suffix reference, now name their new homes.

### Contract entries

Removed exactly `learnloop.params.sensitivity_certificates -> learnloop.sim.sweep` from the frozen-cycle contract’s `ignore_imports` in `pyproject.toml`. Neither other cut edge has an entry there. No new contract or exception. The function-local inventory changes above are a relocation/removal, not new permitted dependencies.

## Validation

- `$T tests/test_identity_pins.py tests/test_architecture.py tests/test_test_layout.py tests/test_structure_ratchets.py tests/test_cli_help_snapshot.py -q -n 3`: **390 passed**, 48.92 s (`core-tests.log`).
- `$PY python scripts/affected_tests.py --help`: exit 0. `$PY python scripts/affected_tests.py --base HEAD --json`: exit 0; full mode, `tests`, because `pyproject.toml` affects every test. It **does** include all three untracked source files (`affected.json`). Used the requested fallback, not the full suite.
- `bash "$S/focused_tests.sh" 1`: 60 explicit files, `-q -m "not arc_close" -n 3`; interrupted after three MCP-backed cases stalled, no final counts (`focused-1-interrupted.log`). A 56-file retry with `-n 3 -o faulthandler_timeout=45` then stalled in the mobile reader TestClient fixture (`retry-1-interrupted.log`); interrupted, no final counts.
- `bash "$S/retry_chunk.sh" 1`: 55 explicit files, `-q -m "not arc_close" -n 2 -o faulthandler_timeout=45`: **4 failed, 1247 passed in 186.41s (0:03:06)** (`retry-1.log`).
- `bash "$S/retry_chunk.sh" 2`: 21 explicit files, the same flags and two workers: **6 failed, 407 passed, 4 errors in 38.06s** (`retry-2.log`).
- `$PY ruff check`: final **all checks passed**. Initial run found four F401s: three source-module imports now used only for moved constants, removed; existing reader section-map re-export marked like its neighbors.
- `$PY lint-imports --no-cache`: **42 kept, 0 broken**, no unmatched/unnecessary ignore warning (`imports.log`).
- `git diff --check`: passes. No full suite, generators, real model/network calls, live vaults or orchestrator landing gate run. No stop rule triggered. Sandbox/test limitations and final temporary-directory check are below.

## What is left

Single-edge removal from the final graph, sorted by resulting largest component, then module names for ties. The first nine edges call destination functions with dependencies requiring design/closure checks. The final edge reads four small helper definitions that may have a lower home; no complete pure-move closure is claimed. Sizes include all three new files. Module names omit `learnloop.`.

| Edge | Largest after removal | Kind / evidence |
|---|---:|---|
| `attempts.attempts → diagnosis.probe_evidence` | 42 | Function calls: four recording/dual-write functions, 233 definition lines before dependencies; needs design. |
| `diagnosis.probe_evidence → diagnosis.probe_blocks` | 42 | Calls `block_complete` (48 lines), `end_diagnostic_block` (85), plus block/completion helpers; needs design. |
| `diagnosis.text_gaps.actions → tutor.promotions` | 53 | Calls `promote_tutor_question` (194 lines), plus its exception/dependencies; needs design. |
| `substrate.replay → attempts.attempts` | 65 | Calls `replay_existing_attempt` (138 lines), imports two result/attribution types; needs design. |
| `tutor.promotions → content.authoring.practice_generation` | 66 | Calls diagnostic generation (107 lines) and ability/band helpers; four imported definitions plus closure; needs design. |
| `adaptive_difficulty.material_view → field.outcomes` | 75 | Calls `load_attempt_rows` (14 lines but delegates to `_load`) and `measurement_masses` (28, observation/read dependencies); needs design. |
| `content.authoring.practice_generation → adaptive_difficulty.generation` | 76 | Calls commissioning, guards, contract switch and goal focus; also reads contract strings; needs design. |
| `content.proposals.proposals → content.proposals.patches` | 76 | Calls apply/reject and outstanding-intent guards; five definitions directly imported, plus apply/lock/compile closure; needs design. |
| `diagnosis.text_gaps.sources → source_retrieval.note_gaps` | 77 | Calls enabled/link lookup/note text/refusal/payload and catches `NoteWithheld`; needs design. |
| `goals.goal_lo → diagnosis.text_gaps.actions` | 77 | Small-definition candidate: `_hash`, `slug`, `day_start`, `creations_today` total 12 definition lines, plus `_SLUG`/imports; the last calls candidates. Lower home/closure still needs checking. |

Ranking script/output: `measure_cuts.py`, `top-edges.json`, `inspect_edges.py`, `edge-details.txt`.

## Restricted-environment results and open verification

The fallback matches **81 files** (`focused-tests.txt`); **76 files** finish in the two final chunks. The four startup hangs listed in the task did not match this fallback and were not run. Five additional matching files remain unverified: `test_diagnosis_input_provenance_landing.py`, `test_mcp_c1a_narrow.py`, `test_mcp_c1a_review.py`, `test_mcp_tools.py`, `test_mobile_v4_reader.py`. The first three stalled in MCP-backed cases; the mobile reader traceback stops in `starlette.testclient.TestClient.__enter__`, `anyio.from_thread.start_task_soon` (`mobile_v4_reader_helpers.py:115`). No claim is made that the hangs are caused by this diff or conclusively by the sandbox. The bounded MCP-tools attempt is recorded below.

Two failures in `test_probability_cli.py` and the four setup errors are confirmed sandbox socket denials (`PermissionError: [Errno 1] Operation not permitted`) in the fake ChatGPT HTTP server, with the setup errors all in `test_t6_followup_composition.py`. These are not verified. The two `test_figures_fix_round2.py` failures have missing sandbox-program output; the diagnostic rerun below records the execution reason. Of the six other assertion failures, the diagnostic below confirms `sandbox_failed` for one figure check; the remaining five are unclassified, with no claim of a baseline pass/failure; `docs/reviews/refactor-bug-ledger.md` **L1-10** assigns comparison/diagnosis before landing. No behavior fix or relaxed assertion is included.

Failed node IDs:

- `tests/test_figures_fix_round2.py::test_f4_pf_generator_tests_count_an_inconclusive_answer_as_not_passing`
- `tests/test_figures_fix_round2.py::test_f4_pf_equivalence_confirms_nothing_when_a_control_is_answered_with_no_boolean`
- `tests/test_probability_cli.py::test_prepare_then_replay_writes_reports_with_pairwise_comparisons`
- `tests/test_probability_cli.py::test_judges_live_check_is_one_capped_call_with_no_learner_data`
- `tests/test_rw5c_labels.py::test_a_model_label_saying_checked_reaches_no_slot_of_a_checked_figure`
- `tests/test_rw5c_labels.py::test_an_area_prediction_answers_by_element_id_and_stores_the_shades_label`
- `tests/test_required_method_round3_review.py::test_f6_a_job_whose_every_verdict_is_recorded_publishes_without_a_judge`
- `tests/test_required_method_round3_review.py::test_f7_a_resume_is_estimated_from_the_persisted_unfinished_stem`
- `tests/test_required_method_round3_review.py::test_f7_a_selection_to_finish_is_estimated_from_its_survivors`
- `tests/test_rw5c_labels.py::test_a2_a_derived_sum_keeps_a_compound_left_hand_side_whole`

Socket-blocked node IDs:

- `tests/test_t6_followup_composition.py::test_the_plan_route_gets_the_policy_budget_in_the_prompt_and_the_routes_effort`
- `tests/test_t6_followup_composition.py::test_a_plan_truncation_is_retried_once_on_the_subscription_with_no_output_cap`
- `tests/test_t6_followup_composition.py::test_the_latency_probe_asks_for_each_profiles_policy_budget`
- `tests/test_t6_followup_composition.py::test_a_truncated_latency_call_is_logged_and_failed`

Additional bounded/diagnostic commands:

- `bash "$S/mcp_attempt.sh"`: `timeout --signal=INT --kill-after=5 55 "$T" tests/test_mcp_tools.py -q -m "not arc_close" -n 2 -o faulthandler_timeout=25`: **exit 137 from enforced timeout**, no final pytest counts. Tracebacks show `_call_all` / `anyio.run` in `test_every_call_is_recorded_with_its_origin_and_is_never_evidence` and `test_no_protected_text_reaches_any_payload`; this was an intentional timeout, not an observed OOM. No claim of completed MCP coverage (`mcp-tools.log`).
- `$T tests/test_figures_fix_round2.py::test_f4_pf_generator_tests_count_an_inconclusive_answer_as_not_passing tests/test_rw5c_labels.py::test_a2_a_derived_sum_keeps_a_compound_left_hand_side_whole -q -n 2 -l`: **2 failed**, 2.07 s, diagnostic repeat. Generator result: `ok=False`, `output=None`, bwrap `NETLINK_ROUTE socket: Operation not permitted`. Figure result: `undecided`, `reason='sandbox_failed'` (`sandbox-diagnostic.log`). These are not verified outside the sandbox. The equivalence-check test uses the same sandbox runner but was not separately repeated with locals.
- Final `.pytest_tmp` check: **no `run-*` directories remain**. Interrupted-run directories were removed using exact paths after stopping their runs; successful final test teardown cleaned the remaining directory.

No cut was stopped, no identity pin moved, and no new exception was needed. Review first the decision to retain certify’s local sweep import for strict AST identity, the five additional startup-hang files (including the changed mobile patch test), and L1-10’s five unresolved assertion failures plus its diagnosed figure-sandbox failure. The full landing gate, baseline reproduction and unrestricted sandbox-dependent coverage remain for the orchestrator.

## Orchestrator's review (Nov 17)

- The six assertions the restricted sandbox could not resolve (three in `tests/test_rw5c_labels.py`, three in `tests/test_required_method_round3_review.py`), the socket and bubblewrap cases, and the five files that hang at startup there were run outside the sandbox on this tree: 299 passed, 2 expected failures, in 14 files. They were sandbox effects, so the ledger row the implementer drafted for them (L1-10) is not added.
- `certify` and `section_generation_candidates` keep their function-local imports of `sim.sweep` and `practice_generation`: the moved bodies stay AST-identical, and the import graph counts function-local imports either way.
- `reader_progression` still binds `learning_objects_for_section` for the modules that import it from there, as it already does for the two names beside it.
