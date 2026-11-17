# K9.6: factor/receipt reads and probe hard stops

Implemented against uncommitted HEAD on `refactor/k9.6-causal-reads`, under the
run 2 ruling. No commit made. `causal_orchestrator.py`: **3,435 → 2,965 lines**.
Named edit 2 is dropped: `hard_refusal` retains its conflict check, byte-for-byte
apart from the function-local import split. K9-9 remains open with its new deadline.

Scratch (`$S`, including `$T=t.sh`, `$PY=py.sh`):
`/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/73b37aee-2550-41c4-88a8-8730b0f3c0c0/scratchpad/refactor-k96`.
All Python/tools ran through `$PY`, tests through `$T`, without network or model calls.
Read the requested strategy sections and both K9.5 records before editing.

## Members and boundaries

Line counts include docstrings/imports; definition counts below include decorators
but exclude surrounding comments/blank lines. Shared constant comments moved with
their values. The pre-edit reference graph (`reference_graph.json`, `preflight.out`)
found **no read → decision dependency**. No resolver, `RepairStatus`, or decision
message moved. The required `EPISODE_CONFLICT_*` copy belongs to the hard stops.

### causal_reads.py — 377 lines

| Definition | Lines |
|---|---:|
| `open_factors_for_hypothesis` | 21 |
| `_durable_case_factor` | 31 |
| `_case_repair_class_id` | 19 |
| `_unmapped_case_obligation` | 26 |
| `diagnosis_receipt` | 11 |
| `_receipt_repair_class_id` | 24 |
| `_repair_class_by_hypothesis` | 12 |
| `_avoided_overteaching_minutes` | 51 |
| `_probe_burden_minutes` | 21 |
| `_recent_diagnostic_burden` | 11 |
| `DiscriminationInputs` | 10 |
| `_discrimination_inputs` | 66 |
| `CausalRepairError` | 2 |
| `CAUSAL_ORCHESTRATOR_FORMULA_VERSION` | 1 |
| `MACHINE_CHECK_REPAIR_MAPPING` | 1 |
| `MACHINE_CHECK_INSTRUMENT_COMMISSIONING` | 1 |
| `PROBE_BLOCKING_MACHINE_CHECK_KINDS` | 1 |
| `SWEPT_MACHINE_CHECK_KINDS` | 3 |

### probe_hard_stops.py — 147 lines

| Definition | Lines |
|---|---:|
| `LEARNER_PREFERENCES` | 1 |
| `record_learner_preference` | 35 |
| `learner_preference` | 15 |
| `EPISODE_CONFLICT_REASON` | 1 |
| `EPISODE_CONFLICT_MESSAGE` | 5 |
| `_causal_origin` | 2 |
| `causal_origin` | 4 |
| `causal_origin_factor` | 5 |
| `episode_conflict_reason` | 24 |
| `probe_episode_conflict` | 11 |

`_causal_origin` moves with its three consumers; it is a required hard-stop helper,
not another rename. `content_ids.py` is **21 lines**, holding only `content_id`.
The decision, parameters/resolver, machine checks, cold verification, observations,
and learner actions remain in the orchestrator. Its imports include only moved
names read by remaining code; moved names were removed from `__all__` (no re-export).

## Named edits

1. The three `_content_id` definitions were AST-identical **before editing**.
   `content_ids.content_id` preserves their signature/body bytes except the public
   name and new docstring explaining stored-row deduplication and identity pins.
   All 17 calls in the original three modules use it. The new reads/stops need no
   content-id call. One further exact copy exists at
   `src/learnloop/attempts/coldness_receipt.py:277`; left untouched, as was the
   different `missing_vocabulary._content_id(value)`.
2. Dropped by the ruling. Router changes only the local imports; checks, order,
   results and returned strings are unchanged. See the counterexample below.
3. Corrected the orchestrator docstring: observation and learner self-report each
   resolve a factor; the episode posterior moves independently. Confirmed the
   self-report resolution at `causal_attribution.record_unresolved_cause_self_report`
   (base line 3736). The module inventory now names what remains. Corrected only
   `decide_probe`'s fitted-store sentence: its scope has no writer today, including
   `cli/fit.py`; defaults serve. The ladder is AST-identical.
4. The new docstrings explain the reads/consumers and four hard stops. They name
   machine checks → preference → conflict for the divergent-repair status path,
   and preference → machine checks → conflict for the router. Answer exposure is
   checked by acceptance, before conflict and again at presentation commit. The
   reason recorded depends on which applicable stop wins. The hard-stop docstring
   also records the router's retained copy and the empty-id difference, without a
   step name.

## P1: AST identity

`$PY python $S/preflight.py` captured the base graph/bindings/ratchets before edits.
`$PY python $S/prove_move.py` (exit 0; `proofs.out`, `named_diffs.txt`):

```text
Three _content_id copies AST-identical: True
orchestrator lost exactly 28 moved definitions + _content_id; no new definitions
causal_reads: 18/18 definitions identical after permitted rename
probe_hard_stops: 10/10 definitions identical after permitted rename
remaining orchestrator: 60/60 identical after call renames and moved-export removal
causal_attribution: 84/84 remaining definitions identical
causal_probe_coherence: 51/51 remaining definitions identical (one docstring excluded)
content_id: identical signature/body (public name + docstring only)
router: all definitions identical (hard_refusal import statements excluded)
```

The exceptions are bounded by AST checks, not a textual similarity score. The
small code differences (full unified forms in `named_diffs.txt`) are:

```diff
-def _probe_episode_conflict(...):
+def probe_episode_conflict(...):
-_probe_episode_conflict(...)
+probe_episode_conflict(...)
-def _content_id(prefix: str, value: Any) -> str:
+def content_id(prefix: str, value: Any) -> str:
+    """Identify content so new rows deduplicate against stored rows.
+    The serialized bytes are pinned by tests/test_identity_pins.py ...
+    """
-_content_id(...)
+content_id(...)
-from learnloop.diagnosis.causal_orchestrator import (causal_origin, episode_conflict_reason, learner_preference, pending_machine_checks_for_factor)
+from learnloop.diagnosis.probe_hard_stops import (causal_origin, episode_conflict_reason, learner_preference)
+from learnloop.diagnosis.causal_orchestrator import pending_machine_checks_for_factor
```

The only constant-list edit in the remaining orchestrator is removing moved exports
from `__all__`: `CAUSAL_ORCHESTRATOR_FORMULA_VERSION`, `CausalRepairError`,
`DiscriminationInputs`, `EPISODE_CONFLICT_MESSAGE`, `EPISODE_CONFLICT_REASON`,
`LEARNER_PREFERENCES`, `MACHINE_CHECK_INSTRUMENT_COMMISSIONING`,
`MACHINE_CHECK_REPAIR_MAPPING`, `PROBE_BLOCKING_MACHINE_CHECK_KINDS`,
`episode_conflict_reason`, `learner_preference`, `open_factors_for_hypothesis`,
`record_learner_preference`. Function/class bodies, constant values, SQL, messages,
logs, reason strings and default values otherwise match the base under those two
symbol substitutions. `probe_episodes.py`, `_robust_gate_verdict`, and
`evaluate_selection` are untouched.

## P2: name resolution

Pre-edit runtime descriptors are in `base_resolution.json` (name → module/qualname
or repr). `prove_move.py` imports the new homes at the tip and compares all **57
bindings across 28 definitions**, including nested code: **57 match**. External
objects are also compared with `is` against their defining imports. A moved
function/class necessarily changes `__module__`; that metadata alone is mapped to
its new home, whose definition P1 proves identical. Full results are retained in
`resolution_results.txt`.

Every moved function's runtime global reads follow. Builtins resolve to the same
builtin objects, `Mapping` to `typing.Mapping`; other non-builtin names resolve to
the identical moved definitions/constants established in P1.

| Function | Runtime global reads |
|---|---|
| `open_factors_for_hypothesis` | `Mapping`, `isinstance`, `str` |
| `_durable_case_factor` | `Mapping`, `getattr`, `isinstance`, `str` |
| `_case_repair_class_id` | `_receipt_repair_class_id`, `diagnosis_receipt`, `str` |
| `_unmapped_case_obligation` | `MACHINE_CHECK_REPAIR_MAPPING`, `str` |
| `diagnosis_receipt` | `Mapping`, `isinstance` |
| `_receipt_repair_class_id` | `Mapping`, `isinstance`, `str` |
| `_repair_class_by_hypothesis` | `Mapping`, `isinstance`, `str` |
| `_avoided_overteaching_minutes` | `Mapping`, `bool`, `diagnosis_receipt`, `float`, `int`, `isinstance`, `len`, `max`, `str`, `sum` |
| `_probe_burden_minutes` | `bool`, `float`, `int`, `isinstance` |
| `_recent_diagnostic_burden` | `max`, `str`, `sum` |
| `_discrimination_inputs` | `DiscriminationInputs`, `Mapping`, `isinstance`, `len`, `list`, `str`, `sum`, `tuple` |
| `record_learner_preference` | `LEARNER_PREFERENCES`, `ValueError`, `dict` |
| `learner_preference` | `str` |
| `_causal_origin` | none |
| `causal_origin` | `_causal_origin` |
| `causal_origin_factor` | `_causal_origin`, `len` |
| `episode_conflict_reason` | `EPISODE_CONFLICT_REASON` |
| `probe_episode_conflict` | `_causal_origin`, `episode_conflict_reason`, `str` |

Class/value bindings are checked too (`DiscriminationInputs`' generated repr reads
builtin `id`; the other moved class/constants have no runtime global reads).
Annotations/decorators retain the original `Any`, `Mapping`, `Sequence`, `dataclass`,
`Repository`, `Clock`, `ProbeEpisodeRecord` import sources. Original function-local
imports are unchanged: `_durable_case_factor` reads `causal_attribution._normalized`;
`episode_conflict_reason` reads `probe_episodes.episode_has_observations`.

## P3: callers and patches

Import/alias/string/attribute search covered `src/`, `tests/`, `scripts/`, and
`docs/learnloop-architecture-vault/_scripts/`. `audit_refs.py` AST-audits module
aliases, getattr/getsource, monkeypatch/setattr, mock.patch, and direct assignments.
No stale moved attribute or qualified patch-string target was found.

12 import callers updated, counted by directory (besides the three original
implementation modules):

| Directory | Files | Moved imports |
|---|---|---|
| `src/learnloop/cli` | 1 (`app.py`) | commissioning kind |
| `src/learnloop/diagnosis` | 2 (`followups.py`, `remediation.py`) | `CausalRepairError` |
| `src/learnloop/followup_run` | 3 (`router.py`, `serving.py`, `jobs.py`) | origins, conflict, preferences |
| `src/learnloop_sidecar/handlers` | 1 (`remediation.py`) | `CausalRepairError` |
| `tests` | 5 (`test_causal_orchestrator.py`, `test_causal_p2_acceptance.py`, `test_causal_probe_commissioning.py`, `test_followup_codex_review.py`, `test_followup_journey.py`) | formula/kinds, conflict, preferences |
| `scripts`, vault `_scripts`, handwritten notes | 0 | no moved-name inventory or module reference found |

`tutor/tutor_qa.py` imports only `record_learner_embedded_prediction`, which stays.
Vault `Concepts/` was searched; `Journeys/` does not exist at this tip; `Workflows/`
was checked too. No generator was run and no generated reference was changed.

Every test patch/direct module assignment targeting causal_orchestrator:

| Site | Target | Consuming globals after move | Still effective / action |
|---|---|---|---|
| `tests/test_dialogue_causal_join.py:457` | `orchestrator.record_learner_embedded_prediction = _boom` via monkeypatch | `tutor_qa` imports that function locally from the unchanged orchestrator | yes; unchanged |

There are no patches of moved private names or source assertions requiring a T4
port, no repointed patches, and no assertions loosened. The five test edits only
redirect imports. Pin and journey test/helper content was not edited.

## P4–P5: pins, imports, ratchets and tests

The pin test, 18-journey test/golden, both identity goldens and structure golden are
byte-identical to HEAD. No writer flags or golden regeneration were used.

Top-level imports (no new module imports causal_orchestrator at any depth):

| Module | Imports |
|---|---|
| `causal_reads` | future annotations; dataclasses.dataclass; typing.Any/Mapping/Sequence; db.repositories.Repository |
| `probe_hard_stops` | future annotations; typing.Any/Mapping; clock.Clock; db.repositories.ProbeEpisodeRecord/Repository |
| `content_ids` | future annotations; hashlib; json; typing.Any (stdlib only) |

No import contract or ignore edge names a moved dependency. The existing
`tutor_qa → causal_orchestrator` edge still describes its remaining import;
`pyproject.toml` and architecture exception inventories stay unchanged.

Measured base → tip (not just golden limits): largest import component **143 →
143**, modules in any import cycle **249 → 249**; no module joined or left the
largest component. All other measured ratchets are unchanged: first-level
packages 46, root modules 35, non-upgrade root modules 35, functions >200 lines 72,
stage-artifact comment lines 2371, stage-named test files 184. Golden untouched.

Commands run individually (test commands never overlapped):

| Command | Result |
|---|---|
| `$T tests/test_identity_pins.py tests/test_diagnosis_journey_golden.py tests/test_architecture.py tests/test_test_layout.py tests/test_structure_ratchets.py tests/test_cli_help_snapshot.py -q -n 4` | **408 passed**, 46.55s |
| `$PY python scripts/affected_tests.py --help` then `--base HEAD --json` | exit 0; selected **1,069** files |
| `bash $S/affected_1.sh` → `$T "${paths[@]}" -m "not arc_close" -n 4 -q --junitxml=$S/affected_1.xml` | **1,493 passed**, 45.45s, **54 files** |
| `$PY ruff check` | all checks passed |
| `$PY lint-imports --no-cache` | **42 kept, 0 broken** |
| `$PY python $S/prove_move.py` | P1/P2/P5 assertions passed |
| `$PY python $S/conflict_counterexample.py` | assertions passed; output below |
| `git diff --check` | clean |

The brief's >400-file rule selected every `tests/test_*.py` whose text mentions
causal_orchestrator, causal_reads, probe_hard_stops, hard_refusal,
causal_attribution or causal_probe_coherence. Exact paths and the quoted bash
array are in `selected_tests.json` / `affected_1.sh`; stdout and JUnit are retained.
The three prohibited startup-hang files were excluded by the selector script
(none occurred in the 54-file fallback). No test failure, socket/bubblewrap failure,
or hang was observed. No killed test run; `.pytest_tmp` is empty at final check.
Full suite, landing gate and generated-vault regeneration are left to the
orchestrator, as requested; the other 1,015 affected files were not run.

## Counterexample retained (K9-9)

Run 1 correctly stopped before code changes: replacing the router copy was not an
equivalent edit. Run 2 preserves both behaviours. The real schema permits an empty
`learning_object_id` (`TEXT NOT NULL`, no nonempty constraint); `str("")` is still
empty. `conflict_counterexample.py` uses a temporary copy of the synthetic migration
fixture, a foreign in-progress episode and submitted presentation, without patches,
preferences or machine checks. The nonempty id is a control. Its import/call now
use `probe_hard_stops.probe_episode_conflict`; the reproduction is otherwise intact.
`$PY python $S/conflict_counterexample.py` (exit 0):

```text
Three _content_id copies AST-identical: True
{"learning_object_id": "", "hard_refusal": "another_probe_episode_is_open", "shared_conflict": null}
{"learning_object_id": "lo_nonempty", "hard_refusal": "another_probe_episode_is_open", "shared_conflict": "another_probe_episode_is_open"}
```

K9-9 now requires one check with empty-id behaviour deliberately chosen, with arc
G's G1 (setting the hard-stop order in hard_refusal) or by K9 close, whichever
comes first. This move leaves both checks as they were; no new stop condition
was encountered under the ruling.

## K9.7 handoff / first review points

Machine checks need `causal_reads.{CAUSAL_ORCHESTRATOR_FORMULA_VERSION,
MACHINE_CHECK_REPAIR_MAPPING,MACHINE_CHECK_INSTRUMENT_COMMISSIONING,
PROBE_BLOCKING_MACHINE_CHECK_KINDS,SWEPT_MACHINE_CHECK_KINDS}` and
`content_ids.content_id`; their cold-sweep dependency still awaits K9.7.
Cold verification needs `causal_reads.{CAUSAL_ORCHESTRATOR_FORMULA_VERSION,
_case_repair_class_id,_receipt_repair_class_id,diagnosis_receipt,
open_factors_for_hypothesis}`. Neither group currently needs a name
from probe_hard_stops; decision/actions and router own those dependencies.

Review first: the extra required `_causal_origin` move, the removed moved-name
`__all__` entries, the fourth stop's acceptance-only exposure checks, and the
intentionally retained K9-9 discrepancy/deadline. No behaviour bug was fixed.
