# K9.8: discriminating observations and learner actions

Pure move on `refactor/k9.8-discrimination-offer`; no commit. Orchestrator:
**2,218 → 1,149 lines**. New modules: **causal_discrimination.py 690 lines**,
**probe_offer.py 417 lines**. No renames or behaviour changes.

Run 2 retained the already-written modules, callers and registries. It independently
verified the original base captures against HEAD, reran P1–P6 and every required
test/tool command, removed incidental import wrapping, clarified the decision-only
module introduction, closed the existing K9-4 documentation row, and wrote this
record. Earlier run outputs are not evidence here. No base was recaptured from the
edited tree. A temporary indentation error during import-format cleanup was fixed
before the affected tests and final core rerun; final Ruff and AST proofs pass.

Scratch `$S` (scripts, explicit test array and run-2 outputs):
`/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/73b37aee-2550-41c4-88a8-8730b0f3c0c0/scratchpad/refactor-k98`.
`$PY=$S/py.sh`, `$T=$S/t.sh`. Python/tools used `$PY`; tests used `$T`, three
workers, one test command at a time. No network, models, generators or other
worktrees were used. Read strategy §4.3, K9.6/K9.7 records and strategy §2.19 T4 /
§2.20 before verification. Definitions' positions were re-derived at this tip.

## Members and boundary

Definition lengths include decorators and exclude surrounding comments/blank lines.
The original base text and top-level reference graph were checked against HEAD
by `run2_extra_proofs.py`; **no retained name reads any moved name**. Thus no
action name needs to stay for the decision: `_answer_shown` and `ProbeOffer` both
move. No decision → observation dependency or stop condition was found.

| causal_discrimination member | Lines |
|---|---:|
| `pinned_causal_probe` | 9 |
| `classify_probe_response` | 54 |
| `DiscriminatingObservation` | 31 |
| `_measured_hypotheses` | 54 |
| `_observation_support_scores` | 25 |
| `_probe_production_admissibility` | 38 |
| `record_learner_embedded_prediction` | 77 |
| `record_probe_classification` | 190 |
| `deterministic_probe_features` | 55 |
| `auto_classify_pinned_probe` | 67 |
| `BLIND_PROBE_BASIS` | 1 |
| `OBSERVATION_FEATURE_SOURCES` | 6 |
| `VALIDATOR_OWNED_FEATURE_SOURCES` | 1 |
| `DETERMINISTIC_FEATURE_PREFIX` | 1 |
| `_EMBEDDED_PREDICTION_OUTCOME` | 1 |

| probe_offer member | Lines |
|---|---:|
| `ProbeOffer` | 26 |
| `_answer_shown` | 13 |
| `_OfferRefusedAtCommit` | 7 |
| `accept_probe_offer` | 30 |
| `_accept_probe_offer` | 247 |
| `defer_probe_offer` | 21 |
| `request_teaching_now` | 27 |

The nine retained definitions are `OrchestratorParameters`,
`resolve_orchestrator_parameters`, `RepairAction`, `RepairStatus`,
`_with_reveal_spend`, `_episode_for`, `_actions`, `causal_repair_status`,
`_status_for_factor`. Their policy scope/defaults/bounds, status/provenance/loss
constants, messages, action labels and `_UNCOMMITTED_REPAIR_STATES` stay because
the decision uses them. No extra exclusive helper was left behind. Moved public
exports are removed from `__all__`; no re-export or import back from either new
module remains in the orchestrator. `probe_offer` imports `RepairStatus` and
`causal_repair_status` at top level and `pinned_causal_probe` from discrimination.

The discrimination docstring describes feature-source validation, a pinned factor,
then the ordered admission checks: discriminating outcome → measured declared
features → independent production. Resolution precedes the receipt; open-set
evidence resolves nothing; deterministic admitted features earn `validator_owned`
support for its readers. The offer docstring describes acceptance/presentation
and settled decision records, deferral preference and teaching authorisation.
The orchestrator's status table is unchanged. Its inventory/introduction now name
the decision, and the queue description names `machine_checks`.

## P1–P2: identity and global bindings

`$PY python $S/prove_move.py` → exit 0, `run2_proofs.out`:

```text
P1 source lost exactly 22 moved definitions/constants; added 0
P1 causal_discrimination 15 / 15 AST-identical
P1 probe_offer 7 / 7 AST-identical
P1 remaining 9 definitions identical except permitted _status_for_factor docstring; constants identical; __all__ loses only moved exports
P2 88 bindings match; 0 expected __name__ differences; moved __module__ follows home; top-level __qualname__ unchanged
P4 protected tests, journey fixture, structure golden and four prohibited source files byte-identical
P1 failure_triage sentence already absent at base; no moved-definition docstring exception needed
```

The original `base_resolution.json` remains the P2 baseline. The runtime comparison
covers nested code/global reads and checks imported objects with `is` against
their defining module. Tip bindings are in `resolution_results.json`, freshly
produced in run 2. All 22 moved values have unchanged ASTs, including IDs, SQL,
messages, logs, reason strings, defaults and both admission/acceptance check orders.
`decide_probe` and all four prohibited source files are unchanged. Moved definition
`__module__` follows its new home; top-level `__qualname__` stays the same. No
moved body calls `logging.getLogger(__name__)`, so no logger changes here.

`$PY python $S/run2_extra_proofs.py` → exit 0, `run2_extra_proofs.out`:
**original base text/graph verified; zero retained → moved reads; 22/22 other
changed Python files' bodies AST-identical**, after excluding import statements,
normalizing rehomed callable reads, two identity-site path strings and the practice
module's function-reference docstring. No assertion was loosened.

Sole definition-level exception (`run2_named_diffs.txt`):

```diff
 ) -> RepairStatus:
+    """Map a factor to repair status after machine checks and probe valuation.
+
+    Record the decision, then offer a ready instrument or withhold branch repair.
+    """
     factor_id = str(factor["id"])
```

The base has no `_status_for_factor` docstring. The requested failure_triage
sentence was already absent at HEAD, so deleting or rewriting another sentence
would not be a pure move. The existing K9-4 row now records the completed docs;
no new behaviour bug or K9-40+ row was needed.

## P3, P5, P6: patches, imports, references

`$PY python $S/run2_audit.py` → exit 0 (`run2_audit.out`):
**3,156 Python files; zero stale imports, old-module alias attributes or qualified
strings; one patch site; zero source-text assertions or module/qualname/logger
selectors**. Roots: `src/`, `tests/`, `scripts/`, vault `_scripts/`. The scan follows
module imports, package imports and simple alias assignments; it checks the moved
names plus the shared imported `DISCRIMINATING_OUTCOMES` constant.

| Patch site | Consuming globals after move | Action / effective? |
|---|---|---|
| `tests/test_dialogue_causal_join.py:455`, `monkeypatch.setattr(orchestrator, "record_learner_embedded_prediction", _boom)` (base line 457) | `tutor_qa` imports the public function locally from `causal_discrimination` | Alias now points to discrimination; patch still intercepts the call; test passes |

No moved private-name patch needs a T4 port. The `_answer_shown` race test already
uses repository reveal values at this base; only its public offer import moved.
No other mock.patch or module assignment targets this source or its names.

Exact new top-level import statements are in `run2_proofs.out`:

| New module | Top-level imports |
|---|---|
| causal_discrimination | future annotations; dataclasses.dataclass; typing.Any/Mapping; causal_activity_policy.DISCRIMINATING_OUTCOMES; clock.Clock; db.repositories observation channels/Repository; causal_attribution policy version/SUPPORT_BASIS_AUTHORITY; causal_probe_coherence bundle_feature_row_report/candidate_has_current_blind_input_contract/classify_against_blind_bundles; causal_reads formula version/CausalRepairError; content_ids.content_id; vault.models.LoadedVault |
| probe_offer | future annotations; dataclasses.dataclass; typing.Any; clock.Clock; db.repositories.Repository; causal_attribution policy version; causal_probe_coherence candidate_has_current_blind_input_contract/order_probe_candidates; causal_reads formula version; probe_hard_stops conflict reason/_causal_origin/episode_conflict_reason/record_learner_preference; vault.models.LoadedVault; causal_discrimination.pinned_causal_probe; causal_orchestrator.RepairStatus/causal_repair_status |

Private imports from other modules, including function-local imports:
**causal_discrimination: none; probe_offer: `probe_hard_stops._causal_origin` only**.
This is the later-cleanup candidate. Discrimination imports neither the decision
nor offers at any depth; the offer's required decision import is top-level.
`lint-imports --no-cache`: **42 contracts kept, 0 broken**.

## Callers and registries

19 caller files updated, excluding three reference-only edits:

| Directory | Caller files |
|---|---:|
| src/learnloop/diagnosis | 1 (`followups.py`) |
| src/learnloop/followup_run | 1 (`admission.py`) |
| src/learnloop/tutor | 1 (`tutor_qa.py`) |
| src/learnloop_sidecar/handlers | 1 (`remediation.py`) |
| tests | 15 (12 test modules, 3 helpers) |
| scripts; vault _scripts | 0 |

Reference-only edits: causal_attribution's sensor comment, practice's offer
reference, and the two `identity_pins_helpers.py` source-site paths. The shared
`DISCRIMINATING_OUTCOMES` binding comes from causal_activity_policy, with its
remaining consumer now in discrimination; its contract identity assertion follows
that consumer. Concepts/ and Workflows/ have no moved-function module reference;
Journeys/ is absent. No handwritten vault edit or generator was needed.

Registry edits:

- `pyproject.toml`: repoint the existing frozen `tutor_qa → causal_orchestrator`
  ignore to `tutor_qa → causal_discrimination`; no new package pair.
- `architecture_function_local_domain_imports.txt`: repoint orchestrator's
  reveal_ledger and canonical_projection edges to discrimination; repoint tutor_qa's
  orchestrator edge to discrimination. No old target still imported at these sites.
- `identity_pins_helpers.py`: repoint the two moved observation identity-site paths.
- SQL owners: unchanged; the architecture detector reports zero direct SQL writes
  in either new module. `tests/goldens/structure.toml`: untouched.

## Ratchets and tests

`$PY python $S/measure_run.py run2_tip_measures` → exit 0. Its scratch copy of
`refactor_measures.py` injects both untracked new paths into the tracked-file list.
`$PY python $S/run2_base_measures.py` independently reconstructed HEAD sources,
confirmed the original `base_measures.json` exactly and produced
`run2_measures_summary.out`. No edited-tree base or golden writer was used.

| Measure | Base | Tip, both new files counted |
|---|---:|---:|
| Largest import component | 149 | 150 |
| Modules in any import cycle | 255 | 256 |
| Function-local-only edges | 2,802 | 2,803 |
| Modules with such an edge | 573 | 575 |
| First-level packages / root modules / non-upgrade root modules | 46 / 35 / 35 | 46 / 35 / 35 |
| Functions >200 lines | 72 | 72 |
| Stage-artifact comment lines / stage-named test files | 2,370 / 184 | 2,370 / 184 |

Only `learnloop.diagnosis.causal_discrimination` joins the largest component; none
leaves. `probe_offer` is counted but outside the component. The normal structure
test cannot see these untracked modules: the landing orchestrator must raise the
component/cycle goldens to **150/256**, with the new member, when landing.

Every test command in run 2, sequentially, all exits 0:

| Command | Result / output |
|---|---|
| `$T tests/test_identity_pins.py tests/test_diagnosis_journey_golden.py tests/test_architecture.py tests/test_test_layout.py tests/test_structure_ratchets.py tests/test_cli_help_snapshot.py -q -n 3` | 408 passed, 48.81s (`run2_core_tests.out`) |
| `bash $S/run2_affected_1.sh` → `$T "${files[@]}" -q -m "not arc_close" -n 3` | 871 passed, 27.48s; 19 explicit paths (`run2_affected_1.out`) |
| Same six-file core command after import-format cleanup | 408 passed, 49.66s (`run2_core_final.out`) |
| `$PY ruff check` | All checks passed (`run2_ruff.out`) |
| `$PY lint-imports --no-cache` | 42 kept, 0 broken (`run2_imports.out`) |
| `git diff --check` | clean |

Affected selection is the requested text scan of every `tests/test_*.py` for source
module/new modules/moved names, not affected_tests.py. Exact paths and exclusions:
`run2_affected_tests.json`, bash array: `run2_affected_1.sh` (19, under 60). Adding
the shared imported constant to the selector did not change the list. No selected
file is one of the three known startup hangs: test_mobile_v3_probes.py,
test_ih6_workbench_open_item.py, test_ih4_preferences_inform_router.py; none ran.
No socket/bubblewrap failure, kill, retry or other sandbox block occurred in run 2.
No behavioural assertion failed, and nothing triggered a stop. The full suite,
arc_close tests and landing gate are unverified here, as instructed. Final
`.pytest_tmp` inspection found no `run-*` directory, including from run 1.

Review first: the **one**, not two, component-member increase; the shared imported
outcomes constant's caller; the public patch's new home; and the already-absent
failure_triage sentence (there is no moved-definition docstring exception).

## Changed file line counts

Counts include imports/docstrings; base 0 means a new file. All 29 files:

| File | Base | Tip |
|---|---:|---:|
| `docs/reviews/refactor-bug-ledger.md` | 203 | 203 |
| `docs/reviews/refactor-k9.8.md` | 0 | 266 |
| `pyproject.toml` | 1301 | 1301 |
| `src/learnloop/diagnosis/causal_attribution.py` | 3771 | 3771 |
| `src/learnloop/diagnosis/causal_discrimination.py` | 0 | 690 |
| `src/learnloop/diagnosis/causal_orchestrator.py` | 2218 | 1149 |
| `src/learnloop/diagnosis/followups.py` | 2622 | 2622 |
| `src/learnloop/diagnosis/probe_offer.py` | 0 | 417 |
| `src/learnloop/followup_run/admission.py` | 438 | 438 |
| `src/learnloop/tutor/tutor_qa.py` | 2715 | 2713 |
| `src/learnloop_sidecar/handlers/practice.py` | 2212 | 2212 |
| `src/learnloop_sidecar/handlers/remediation.py` | 306 | 306 |
| `tests/architecture_function_local_domain_imports.txt` | 164 | 164 |
| `tests/causal_p2_acceptance_helpers.py` | 398 | 399 |
| `tests/diagnosis_identity_helpers.py` | 501 | 501 |
| `tests/diagnosis_journey_helpers.py` | 485 | 487 |
| `tests/identity_pins_helpers.py` | 1855 | 1855 |
| `tests/test_causal_orchestrator.py` | 667 | 668 |
| `tests/test_causal_p2_acceptance.py` | 1110 | 1110 |
| `tests/test_causal_repair_sidecar_rpcs.py` | 619 | 616 |
| `tests/test_dialogue_causal_join.py` | 809 | 807 |
| `tests/test_followup_codex_review.py` | 1418 | 1418 |
| `tests/test_followup_fg1c_codex_review.py` | 339 | 339 |
| `tests/test_followup_generate_e2e.py` | 241 | 241 |
| `tests/test_followup_router.py` | 206 | 206 |
| `tests/test_pfc_unassessed_readers.py` | 709 | 709 |
| `tests/test_placement_opening_probes.py` | 540 | 540 |
| `tests/test_refusal_records.py` | 452 | 452 |
| `tests/test_ux_phase4_feedback.py` | 3042 | 3042 |
