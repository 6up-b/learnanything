# K9.7: machine checks and cold verification

Pure move on `refactor/k9.7-machine-checks`; no commit. Orchestrator:
**2,965 → 2,216 lines**. New modules: **machine_checks.py 354 lines**,
**causal_cold_verification.py 434 lines**. No renames or behaviour fixes.
Read §4.3, the K9.6 handoff, and strategy §2.19 T4 / §2.20 before editing.

Scratch `$S` (all proof scripts, captured tables, commands and outputs):
`/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/73b37aee-2550-41c4-88a8-8730b0f3c0c0/scratchpad/refactor-k97`.
`$PY=$S/py.sh`, `$T=$S/t.sh`. Every Python/tool invocation used `$PY`;
every test used `$T`, with explicit file arrays and at most four workers.

## Members and boundary

Definition lengths exclude surrounding blank lines. No additional helper or
constant belongs exclusively to these groups. `preflight.py` captured base
positions, the definition reference graph and runtime global bindings before
editing. `reference_graph_complete.json` extends that graph to imported names,
constants and annotations, using the saved base source.

| New module | Member | Lines |
|---|---|---:|
| machine_checks | `_machine_check_id` | 12 |
| machine_checks | `backfill_obligation` | 33 |
| machine_checks | `instrument_commissioning_obligation` | 26 |
| machine_checks | `enqueue_backfill_obligation` | 24 |
| machine_checks | `sweep_machine_checks` | 112 |
| machine_checks | `_close_orphan_checks` | 26 |
| machine_checks | `close_satisfied_backfills` | 28 |
| machine_checks | `resolve_machine_check` | 13 |
| machine_checks | `pending_machine_checks_for_factor` | 32 |
| causal_cold_verification | `cold_verification_context` | 108 |
| causal_cold_verification | `record_cold_verification_from_task` | 177 |
| causal_cold_verification | `sweep_expired_cold_retries` | 117 |

Machine definitions total 306 lines; cold definitions total 402. Constants remain
in `causal_reads`: both kinds, blocking/swept kind sets and formula version.
The decision, resolver, status types, offers, learner actions and discriminating
observations stay: none is read by a moved function. Both protected functions
(`_answer_shown`, `_accept_probe_offer`) and `probe_episodes.py` are byte-identical.

Cold verification imports the reads; machine checks import the reads and cold
sweep at top level. Neither new module imports the orchestrator at any depth.
The orchestrator needs only four moved names: `backfill_obligation`,
`enqueue_backfill_obligation`, `close_satisfied_backfills`,
`pending_machine_checks_for_factor`. It has **no remaining cold consumer**, so
following the brief's used-names-only rule it does not add an unused cold import.
Its exports lose all ten moved public names; the two private helpers were never
exported. The sweep's body, order, strings and IDs are unchanged.

## Proofs P1–P6

`$PY python $S/prove_move.py` → exit 0 (`proofs.out`):

```text
P1 source lost exactly 12 moved definitions; added 0
P1 machine_checks 9 / 9 AST-identical
P1 causal_cold_verification 3 / 3 AST-identical
P1 remaining 26 / 26 AST-identical, including both protected functions
P1 constants identical; __all__ loses only moved names; no named AST exceptions
P2 71 bindings match; 3 expected __name__ differences; all annotation objects match
```

P2 compares the before-edit `base_resolution.json` table with runtime bindings
through `$PY`, including nested code's global reads; `resolution_results.json`
records the tip table. External/imported bindings are also checked by `is`
against their defining imports. Moved function bindings map to their new homes,
whose bodies P1 proves identical. All 12 definitions' `__module__` changes;
their top-level `__qualname__` values remain identical. Logger names follow
`machine_checks` for `sweep_machine_checks`, and `causal_cold_verification` for
`record_cold_verification_from_task` and `sweep_expired_cold_retries`.

P3 / P6: `$PY python $S/audit_refs.py` → exit 0 (`audit.out`):
**3,153 Python files, zero stale imports, old-module alias attributes or qualified
strings; one patch site; zero old module/qualname/logger selectors**. The scan
covers `src/`, `tests/`, `scripts/` and vault `_scripts/`, follows simple alias
assignments, and also checks logging/config strings. No T4 private patch or
source-text assertion needs porting; no assertion was loosened.

| Patch site | Target | Consuming globals after move | Action |
|---|---|---|---|
| `tests/test_dialogue_causal_join.py:457` | `monkeypatch.setattr(orchestrator, "record_learner_embedded_prediction", _boom)` | `tutor_qa` locally imports the retained orchestrator function | Still effective; unchanged |

P4: the pin test, journey test and journey JSON are byte-identical to HEAD;
both tests pass in the 408-test command below, without writer flags. The journey
helper's four machine calls now use `machine_checks`; its assertions are unchanged.
The identity helper imports the new queue home; the identity-site path inventory
points `_machine_check_id` at its new source. No pin/golden value changed.

P5 top-level imports (full exact statements in `proofs.out`):

| Module | Imports |
|---|---|
| machine_checks | future annotations; logging; typing.Any/Mapping; clock.Clock; db.repositories.Repository; followup_serve.gates.RIVAL_CAUSES_FACTOR_VERSION; causal_probe_coherence.candidate_has_current_blind_input_contract; probe_targeting.classify_cause_set; causal_reads formula/kinds/sets; content_ids.content_id; vault.models.LoadedVault; causal_cold_verification.sweep_expired_cold_retries |
| causal_cold_verification | future annotations; logging; typing.Any/Mapping; clock.Clock; db.repositories.Repository; causal_probe_coherence.candidate_has_current_blind_input_contract; causal_reads formula/_case_repair_class_id/_receipt_repair_class_id/diagnosis_receipt/open_factors_for_hypothesis; vault.models.LoadedVault |

`lint-imports --no-cache`: **42 contracts kept, 0 broken**.

## Callers and registries

| Directory | Caller files updated | Other reference edits |
|---|---:|---|
| src/learnloop/cli | 1 | resolve-machine-check import |
| src/learnloop/diagnosis | 2 | followups' two local imports; remediation context import; one additional causal_factor_deferral docstring reference |
| src/learnloop/followup_run | 1 | router pending-check import |
| src/learnloop/attempts | 0 | one coldness_receipt docstring reference |
| src/learnloop/goals | 0 | one certification_cold_probe docstring reference |
| tests | 11 | nine test files, two callable helpers; one additional identity-site path inventory file |
| scripts; vault _scripts; handwritten Concepts/Workflows | 0 | no moved references; Journeys directory absent |

Registry edits, exhaustively:

- `tests/architecture_function_local_domain_imports.txt`: repoint orchestrator →
  attempts.coldness_receipt and → substrate.instrument_serving to the cold module;
  add cold → substrate.canonical_projection while retaining the orchestrator edge.
- `tests/identity_pins_helpers.py`: repoint only the `_machine_check_id` source path
  in the identity-site inventory.
- SQL-owner registry: unchanged; the existing detector finds **zero direct SQL
  writes in either new module**. `pyproject.toml`: unchanged; no frozen edge needs
  repointing (tutor_qa still imports the retained observation function).
- `tests/goldens/structure.toml`: untouched. No generator or generated note edited.

## Ratchets and tests

`measure_with_new.py` is a scratch copy of `refactor_measures.py` whose tracked-file
list explicitly injects the two new paths; it never writes a golden.
`$PY python $S/measure_run.py base_measures` and `... tip_measures` → exit 0:

| Measure | Base | Tip, new files counted |
|---|---:|---:|
| Largest import component | 146 | 148 |
| Modules in any import cycle | 252 | 254 |
| Function-local-only edges | 2,794 | 2,798 |
| Modules with such an edge | 570 | 572 |
| First-level packages / root modules / non-upgrade root modules | 46 / 35 / 35 | 46 / 35 / 35 |
| Functions >200 lines | 72 | 72 |
| Stage-artifact comment lines / stage-named test files | 2,371 / 184 | 2,371 / 184 |

Only `learnloop.diagnosis.machine_checks` and
`learnloop.diagnosis.causal_cold_verification` join the largest component; none
leaves. The normal structure test cannot see these untracked paths. The landing
orchestrator must raise the component/cycle golden with both modules counted.

Commands ran individually; test runs did not overlap:

| Command | Result |
|---|---|
| `$T tests/test_identity_pins.py tests/test_diagnosis_journey_golden.py tests/test_architecture.py tests/test_test_layout.py tests/test_structure_ratchets.py tests/test_cli_help_snapshot.py -q -n 4` | **408 passed**, 45.90s |
| `bash $S/affected_1.sh` → `$T "${files[@]}" -q -m "not arc_close" -n 4` | **1,275 passed**, 29.37s; 36 explicit files, one chunk |
| `$PY ruff check` | All checks passed |
| `$PY lint-imports --no-cache` | 42 kept, 0 broken |
| `git diff --check` | clean |

`audit_refs.py` selects every `tests/test_*.py` whose text contains the old/new
module names or any moved name, including module-name substrings in helper
imports. Exact list: `affected_tests.json` and `affected_1.sh`. The three known
startup-hang files were not selected and were not run. No socket/bubblewrap
failure occurred. No tests failed, no stop condition or new behaviour bug was
found, and no ledger row was needed. Full suite/landing gate remain for the
orchestrator. Final `.pytest_tmp` inspection: no `run-*` directory.

## K9.8 handoff / first review points

The observation and learner-action groups remain unchanged at their current
locations in the 2,216-line orchestrator. Import their reads from `causal_reads`,
the four machine-check functions above from `machine_checks`, and hard stops
from `probe_hard_stops`; do not recover moved names from the orchestrator.
The decision's parameters and statuses remain its own boundary. The offer's
`request_teaching_now` still reads `causal_repair_status`; the observation does
not gain a dependency on cold verification. Re-derive positions and its exclusive
helpers from the graph, and account for the other worker's local imports in the
two protected functions when combining landings. K9-4's discrimination-docstring
correction remains K9.8's work.

Review first: the used-names-only absence of a direct cold import in the
orchestrator, the identity-site path inventory change, and the two-component
ratchet increase hidden from the ordinary untracked-file test run.
