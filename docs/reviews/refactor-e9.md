# E9. Feature ownership of root modules

## Step 0. Importers before any move

At `9038b096e744`, none of the 37 measured root modules qualifies for a pure move into a feature package. Thirty-five have direct imports from multiple production packages or coordinators. Of the two with a single importing production package, `app_launch` is an adapter coordinator and `reader_learner_state` spans Reader and daily plan. The package initializer and entry point are included for completeness.

The scratch inventory took the root stems from `src/learnloop/*.py` and parsed each of the 3,517 tracked Python files returned by `git ls-files -z -- '*.py'` with `ast.parse`. It walked every `Import` and `ImportFrom`, including function-local and type-checking imports. For source files it resolved relative imports against the importing package with `importlib.util.resolve_name`. For a from-import it checked both the module and the module plus each imported name, so `from learnloop import held_grades as held` counts. It matched the first component after `learnloop.` against the root stems and counted each importing file once. For the initializer it also counted explicit imports of the package or its version. The table reports direct Python imports. Calls through injected objects, implicit package initialization, and import statements embedded in strings do not count as edges.

Package names in the table are relative to `learnloop` unless written in full. A slash after `root` names an importing root module. The tests, scripts, and fixture columns give counts of importing files outside production. “Shared” means the module stays at the root as a cross-cutting leaf or application coordinator.

| Root module | Direct production importers by package | Tests | Scripts | Fixtures | Verdict and reason |
|---|---|---:|---:|---:|---|
| `__init__` | — | 7 | 0 | 0 | Shared — stay. Package initializer. Defines the package version. |
| `__main__` | — | 0 | 0 | 0 | Shared — stay. Package entry point for `python -m learnloop`. |
| `activation_journal` | `cli`, `db`, `learnloop_mobile`, `learnloop_sidecar`, `ops`, `remote`, `vault` | 5 | 0 | 0 | Shared — stay. Both vault opening and the activation/recovery paths consult the journal. |
| `adf_numeric` | `adaptive_difficulty`, `daily_plan`, `figures`, `learner`, `router`, `router_objective`, `teacher` | 1 | 0 | 0 | Shared — stay. Adaptive difficulty and the lesson-check weight use the same numeric primitives. |
| `algorithm_versions` | `adaptive_difficulty`, `attempts`, `cli`, `config`, `daily_plan`, `db`, `diagnosis`, `figures`, `goals`, `learner`, `ops`, `pads`, `placement`, `reader`, `root/version_floor`, `scheduling`, `substrate` | 284 | 1 | 0 | Shared — stay. Several features gate persisted behavior on the same version vocabulary. |
| `app_launch` | `cli` | 2 | 0 | 0 | Shared — stay. ADR-005 places CLI launches of the TUI and MCP in this neutral coordinator. Moving it into the CLI would introduce two direct adapter dependencies forbidden by `entry-points-are-independent`. |
| `attempt_types` | `attempts`, `cli`, `content`, `scheduling`, `tui`, `vault` | 3 | 0 | 0 | Shared — stay. Attempt ingestion, scheduling, and content share the accepted attempt kinds. |
| `bootstrap` | `cli`, `learnloop_sidecar` | 6 | 0 | 0 | Shared — stay. The CLI and sidecar use the same vault creation policy. |
| `causal_activity_policy` | `attempts`, `daily_plan`, `db`, `diagnosis`, `learner`, `ops`, `placement`, `router_objective` | 2 | 0 | 0 | Shared — stay. Attempts, diagnosis, and the router use the same activity classification. |
| `clock` | `adaptive_difficulty`, `ai`, `attempts`, `cli`, `companion`, `content`, `curriculum`, `daily_plan`, `data_capture`, `db`, `desks`, `diagnosis`, `field`, `figures`, `followup_run`, `followup_serve`, `goals`, `hints`, `instructional`, `intent`, `learner`, `learnloop_mcp`, `learnloop_sidecar`, `matching`, `ops`, `pads`, `params`, `placement`, `practice_index`, `projects`, `reader`, `remote`, `root/bootstrap`, `root/delayed_checks`, `root/delayed_completion`, `root/learner_context`, `root/migration_coordinator`, `root/reader_learner_state`, `root/reading_sources`, `router`, `router_objective`, `scheduling`, `sim`, `source_retrieval`, `substrate`, `teacher`, `tui`, `tutor`, `vault`, `workbench` | 633 | 3 | 1 | Shared — stay. Shared clock and timestamp functions underpin storage and feature decisions. |
| `confidence_events` | `daily_plan`, `diagnosis`, `hints`, `root/reader_learner_state`, `tutor` | 5 | 0 | 0 | Shared — stay. Diagnosis, hints, and tutor context read the same learner confidence events. |
| `decider_judgments` | `adaptive_difficulty`, `cli`, `content`, `diagnosis`, `field`, `hints`, `learnloop_sidecar`, `ops`, `reader`, `source_retrieval` | 10 | 0 | 0 | Shared — stay. Diagnosis, retrieval, and other features request these judgments. |
| `delayed_checks` | `daily_plan`, `teacher` | 6 | 0 | 0 | Shared — stay. Teacher and daily plan both call the delayed-check item picker. |
| `delayed_completion` | `adaptive_difficulty`, `daily_plan`, `router` | 3 | 0 | 0 | Shared — stay. Adaptive difficulty and the router share a versioned completion definition. |
| `figure_admission` | `diagnosis`, `figures`, `learnloop_sidecar`, `source_retrieval`, `teacher`, `tutor`, `workbench` | 9 | 0 | 0 | Shared — stay. Figures, diagnosis, tutor, and teacher all use the figure gate or its vocabulary. |
| `grading_epochs` | `adaptive_difficulty`, `attempts`, `learner`, `learnloop_sidecar`, `router_objective`, `substrate`, `workbench` | 3 | 0 | 0 | Shared — stay. Attempt regrading, adaptive replay, and the learner timeline read the same grade epochs. |
| `held_grades` | `adaptive_difficulty`, `attempts`, `curriculum`, `daily_plan`, `db`, `diagnosis`, `evsi_calibration`, `goals`, `hints`, `instructional`, `learner`, `learnloop_sidecar`, `ops`, `placement`, `reader`, `remote`, `root/learner_protection`, `router_objective`, `scheduling`, `substrate`, `tutor`, `workbench` | 19 | 1 | 1 | Shared — stay. Scheduling, attempts, learner state, and other features all need the held-grade predicate. |
| `hint_window` | `db`, `field`, `learnloop_sidecar` | 1 | 0 | 0 | Shared — stay. Both the question store and field signals assign help to attempts. The sidecar also reads the window. |
| `ids` | `adaptive_difficulty`, `attempts`, `capture`, `cli`, `content`, `curriculum`, `daily_plan`, `data_capture`, `db`, `diagnosis`, `figures`, `followup_run`, `goals`, `hints`, `instructional`, `intent`, `learnloop_mcp`, `learnloop_mobile`, `learnloop_sidecar`, `ops`, `pads`, `placement`, `practice_index`, `projects`, `reader`, `root/bootstrap`, `root/provenance`, `router`, `router_objective`, `scheduling`, `sim`, `source_retrieval`, `teacher`, `tui`, `tutor`, `vault`, `workbench` | 69 | 0 | 0 | Shared — stay. Shared identifiers and normalization span the stores, services, and adapters. |
| `learner_context` | `learnloop_mcp`, `remote`, `teacher` | 11 | 0 | 0 | Shared — stay. Teacher, remote, and MCP consume the learner read model. |
| `learner_protection` | `adaptive_difficulty`, `content`, `daily_plan`, `diagnosis`, `experiments`, `figures`, `followup_run`, `remote`, `root/confidence_events`, `root/learner_context`, `root/reader_learner_state`, `source_retrieval`, `teacher` | 30 | 0 | 0 | Shared — stay. The same disclosure policy protects several features’ model inputs. |
| `migration_coordinator` | `ops`, `vault` | 4 | 1 | 0 | Shared — stay. Vault opening and maintenance coordinate database migrations through it. |
| `numeric` | `attempts`, `content`, `db`, `diagnosis`, `field`, `goals`, `learner`, `scheduling` | 2 | 0 | 0 | Shared — stay. Shared numeric operations are imported by scoring, scheduling, and diagnosis. |
| `outcome_contract` | `attempts`, `daily_plan`, `data_capture`, `db`, `diagnosis`, `evsi_calibration`, `goals`, `learner`, `learnloop_sidecar`, `recognition`, `root/delayed_completion`, `root/held_grades`, `router`, `router_objective`, `scheduling`, `substrate`, `workbench` | 16 | 0 | 0 | Shared — stay. Several consumers use the same observational label eligibility rules. |
| `plan_refs` | `daily_plan`, `db`, `followup_run`, `followup_serve`, `router`, `router_objective`, `teacher`, `why` | 2 | 1 | 0 | Shared — stay. Planning, routing, and teacher code share stable option references. |
| `provenance` | `ai`, `attempts`, `cli`, `content`, `daily_plan`, `db`, `diagnosis`, `figures`, `learnloop_mcp`, `learnloop_mobile`, `learnloop_sidecar`, `root/refusal_records`, `router`, `router_objective`, `scheduling`, `source_retrieval`, `why` | 24 | 0 | 0 | Shared — stay. Decision records and trace IDs cross producer and reader boundaries. |
| `reader_learner_state` | `learnloop_sidecar` | 3 | 0 | 0 | Unclear — stay. Reader Ask is the consumer, but its package cannot own the module without adding a package cycle. The sidecar injects its result. See the dependency paths below. |
| `reading_sources` | `adaptive_difficulty`, `attempts`, `data_capture` | 0 | 0 | 0 | Shared — stay. Adaptive reading history, exposure capture, and the attempts firewall all consume this vocabulary. |
| `recurrence` | `db`, `diagnosis`, `substrate`, `tutor` | 6 | 0 | 0 | Shared — stay. Stores, diagnosis, substrate, and tutor share recurrence keys. |
| `refusal_records` | `daily_plan`, `db`, `followup_run`, `hints`, `root/decider_judgments`, `root/figure_admission`, `source_retrieval`, `teacher` | 4 | 0 | 0 | Shared — stay. Planning, hints, and retrieval record refusals through the same interface. |
| `reveal_coverage` | `attempts`, `db`, `instructional`, `practice_index`, `root/serve_eligibility`, `scheduling` | 3 | 0 | 0 | Shared — stay. Attempts, practice indexing, and scheduling use the exposure-coverage rule. |
| `router_objective_switches` | `adaptive_difficulty`, `daily_plan`, `diagnosis`, `goals`, `learnloop_sidecar`, `ops`, `router_objective`, `teacher` | 21 | 0 | 0 | Shared — stay. Daily plan, teacher, and objective code all consume these serving switches. |
| `sandbox_profile` | `content`, `notebook_runtime` | 0 | 0 | 0 | Shared — stay. The concept-animation renderer and the notebook runtime share exactly one sandbox policy. |
| `section_map` | `adaptive_difficulty`, `daily_plan`, `data_capture`, `intent`, `learnloop_sidecar`, `passage_union`, `reader`, `source_retrieval` | 3 | 0 | 0 | Shared — stay. Reader, passage union, and adaptive difficulty all map sections and spans to learning objects. |
| `serve_eligibility` | `adaptive_difficulty`, `attempts`, `cli`, `content`, `daily_plan`, `diagnosis`, `learnloop_sidecar`, `root/delayed_checks`, `root/learner_protection`, `scheduling`, `teacher` | 10 | 0 | 0 | Shared — stay. Attempts, scheduling, teacher, and planning share serve eligibility. |
| `symbolic_view` | `diagnosis`, `hints`, `learnloop_sidecar`, `workbench` | 1 | 0 | 0 | Shared — stay. Diagnosis, hints, and workbench consume the same stored symbolic result. |
| `text_canon` | `practice_index`, `source_retrieval`, `tutor` | 1 | 0 | 0 | Shared — stay. Practice indexing, tutor, and retrieval share text normalization. |
| `vault_lock` | `cli`, `content`, `db`, `diagnosis`, `goals`, `intent`, `learnloop_sidecar`, `ops`, `root/migration_coordinator`, `source_retrieval`, `substrate`, `vault` | 6 | 0 | 0 | Shared — stay. Vault, content, substrate, and maintenance code coordinate mutations with the same lock. |
| `version_floor` | `learnloop_mobile`, `learnloop_sidecar`, `ops`, `remote`, `root/activation_journal`, `substrate`, `vault` | 9 | 0 | 0 | Shared — stay. Vault opening, replay, remote, and adapters all enforce the compatibility floor. |

### The two single-package cases

- `cli.app` and `cli.mcp` are the only production importers of `app_launch`. Its two function-local imports target `learnloop.tui.app` and `learnloop_mcp.cli`. Putting either in the CLI would break the direct-import contract. The neutral coordinator is an explicit architecture decision. [ADR-005](../learnloop-architecture-vault/Decisions/ADR-005%20Independent%20adapters.md)
- `learnloop_sidecar.handlers.reader_tutor` builds the Reader learner state and injects it into the Ask path. The decisive edges are `reader_learner_state._readiness → daily_plan.headline` and `daily_plan.router_reader → reader.recap`. Under `reader`, the first edge would close a cycle between sibling packages guarded by `frozen-cross-package-cycles`. Moving domain code for readiness, confidence, and protected attempt history into an adapter would also conflict with ADR-005. The original feature record gives the same dependency rationale. [Learner-blindness implementation record](learner-blindness-relax.md)

### Disposition

All seven candidates in the November 12 audit stay. The November 16 audit provides a historical count and target, with no additional E9 move. There are no moved definitions, rewritten import bindings, old names to shim, or direct-importer test files for moves. No assertion, contract, identity pin, or structure golden needs an edit. Both root-module ratchets remain at 37.

## Verification

The destination check used the configured import-linter contracts against two in-memory copies of the Grimp graph. For each candidate it first checked the contract against the original graph. On a fresh copy, it replaced the module node and redirected every incoming and outgoing import to its proposed name, then ran the same contract with the same exclusions. Each pair was checked independently.

| Proposed destination | Contract | Original graph | Graph after move |
|---|---|---|---|
| `learnloop.reader.reader_learner_state` | `frozen-cross-package-cycles` | Kept | Broken |
| `learnloop.cli.app_launch` | `entry-points-are-independent` | Kept | Broken |

The test commands ran separately through the isolated `uv run --no-sync` environment. The shared uv cache refused the lock on this mount, so the invocation added `--no-cache` to use temporary storage for the run.

| Command | Result |
|---|---|
| `pytest -q -n 1 -p no:cacheprovider tests/test_identity_pins.py` | 363 passed |
| `pytest -q -n 1 -p no:cacheprovider tests/test_structure_ratchets.py` | 3 passed |
| `pytest -q -n 1 -p no:cacheprovider tests/test_architecture.py` | 18 passed |
| `pytest -q -n 1 -p no:cacheprovider tests/test_test_layout.py` | 3 passed |
| `pytest -q -n 1 -p no:cacheprovider tests/test_module_catalog_inventory.py` | 9 passed |
| `ruff check` | All checks passed! |
| `lint-imports --no-cache` | 54 contracts kept, 0 broken |
| `python scripts/check_gate_partition.py` | Collected 34,038 tests, comprising 33,972 landing and 66 arc-close tests. Exit 0. |

`git diff --exit-code HEAD -- src tests scripts pyproject.toml` returned 0. The inventory is the only deliverable. Git could not stage it because the linked worktree's index is read-only in this sandbox.
