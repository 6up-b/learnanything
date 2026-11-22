# L3: serving reach and the owner's tooling list

Snapshot: `f4ccb20266cb4f9ba8981a3decad54b3783585a1`, inspected read-only on 2026-11-21. No files changed.

The owner’s 2026-11-20 instruction is recorded at `docs/reviews/refactor-status.md:277`: produce the per-package list; the owner marks what stays. The L3 entry at `docs/specs/refactor_strategy_v3.md:786` still refers to “decision 7,” but this revision no longer contains a separately numbered decision-7 entry.

**Result:** 260 modules, 98,157 physical lines, are tooling-only under the roots below. No static serving-to-tooling boundary violations were found. Five tooling-only modules also have **inferred dynamic reach from the serving parameter registry**; their rows are marked `R`.

### Roots and counting

Roots are packages expanded to **every tracked Python module beneath them**, including `__init__.py`. This matches the package-root convention in `scripts/refactor_measures.py`, rather than starting only at each executable’s main function.

| Class | Exact roots | Entry modules and functions |
|---|---|---|
| Serving | Every module in `learnloop_sidecar/` — 91 modules | `learnloop_sidecar/__main__.py:main` → `learnloop_sidecar/server.py:serve` |
| Serving | Every module in `learnloop_mobile/` — 11 modules | `learnloop-mobile = learnloop_mobile.cli:app`; `learnloop_mobile/__main__.py`; `learnloop_mobile/cli.py:serve` → `learnloop_mobile/host.py:create_app` |
| Serving | Every module in `learnloop_mcp/` — 6 modules | `learnloop_mcp/__main__.py:main` → `learnloop_mcp/cli.py:serve`; `learnloop_mcp/server.py:build_server`; HTTP transport in `learnloop_mcp/http_app.py` |
| Tooling | Every module in `learnloop/cli/` — 58 modules | `learnloop = learnloop.cli:app` in `pyproject.toml` |
| Tooling | `learnloop/__main__.py` — 1 module | The additional executable entry point for `python -m learnloop` |
| Tooling | Every module in `learnloop/tui/` — 11 modules | `learnloop/tui/app.py:run`, reached by `learnloop today` |
| Tooling | Every module in `learnloop/experiments/` — 36 modules | CLI experiment commands and their research implementations |
| Tooling | Every module in `learnloop/evsi_calibration/` — 17 modules | EVSI simulation, comparison and calibration commands |
| Tooling | Every module in `learnloop/sim/` — 15 modules | CLI simulations, scripts and test harnesses |
| Tooling | Every module in `learnloop/notebook_authoring/` — 3 modules | `learnloop/cli/notebook.py` → `check.py` → `marimo_adapter.py` |
| Tooling | All 27 tracked Python files under `scripts/`, listed below | Each file is independently seeded |
| Tests | All 1,984 tracked Python files under `tests/` | Includes helpers and `conftest.py`; none executed |

The exact script roots are:

```text
scripts/adm0_simulation_report.py
scripts/affected_tests.py
scripts/benchmark_chatgpt_plan_latency.py
scripts/benchmark_sqlite_concurrency.py
scripts/check_credit_report.py
scripts/check_gate_partition.py
scripts/probe_router_report.py
scripts/refactor_measures.py
scripts/s0_landing.py
scripts/sanitize_migration_head_fixture.py
scripts/sanitized_head_transcript.py
scripts/table_review.py
scripts/vault_report.py
scripts/voi_cap_report.py
scripts/ux_walk/bridge.py
scripts/ux_walk/driver.py
scripts/ux_walk/fake_model.py
scripts/ux_walk/make_vault.py
scripts/ux_walk/phone_proxy.py
scripts/ux_walk/replay.py
scripts/ux_walk/route_check.py
scripts/ux_walk/start.py
scripts/ux_walk/stop.py
scripts/ux_walk/walk_client.py
scripts/ux_walk/walk_commands.py
scripts/ux_walk/walk_perceive.py
scripts/ux_walk/walk_protocol.py
```

Both `pyproject.toml` console-script targets resolve to source modules and their declared application objects. There are no unresolved project entry-point declarations.

Serving takes precedence over tooling, tooling over tests, and tests over unreachable. Thus a module used by both the CLI and sidecar is serving. Seeding whole serving packages also classifies their administrative helpers, such as `learnloop_mobile/client_contract.py`, as serving; this is the measurement convention, not a claim that every function handles a learner request.

### Reach totals

Counts include `__init__.py`, blank lines, comments and docstrings. All parsed Python files were syntactically readable.

| Scope | Serving | Tooling only | Tests only | Unreachable | Total |
|---|---:|---:|---:|---:|---:|
| All four packages under `src/`: modules | 1,057 | 260 | 0 | 2 | 1,319 |
| All four packages: lines | 528,345 | 98,157 | 0 | 860 | 627,362 |
| `learnloop` and `learnloop_sidecar` only: modules | 1,040 | 260 | 0 | 2 | 1,302 |
| Those two packages: lines | 524,633 | 98,157 | 0 | 860 | 623,650 |

**Comparison with the strategy**

| Measurement | Modules | Lines | Change from 241 / 92,381 |
|---|---:|---:|---:|
| Current CLI/TUI-only measure, using the existing script’s roots | 253 | 95,270 | +12 modules; +2,889 lines |
| Add experiments, EVSI calibration, simulation, scripts and notebook-authoring roots | 259 | 98,152 | +18 modules; +5,771 lines |
| Also include the executable CLI shim `learnloop/__main__.py` | **260** | **98,157** | **+19 modules; +5,776 lines** |

The broader roots add these six modules beyond the current CLI/TUI measure:

| Module | Lines | Additional root |
|---|---:|---|
| `learnloop/config/kill_switches.py` | 186 | `scripts/vault_report.py` |
| `learnloop/router_objective/diagnostic_value.py` | 320 | `scripts/probe_router_report.py` |
| `learnloop/sim/ad_gates.py` | 395 | Simulation package |
| `learnloop/sim/ad_memory_experiment.py` | 224 | Simulation package |
| `learnloop/sim/ad_memory_synthetic.py` | 468 | Simulation package |
| `learnloop/sim/ad_synthetic.py` | 1,289 | Simulation package |

The CLI shim adds another five lines. These root changes account for 2,887 lines of the difference; the remaining 2,889 are the net change in the comparable CLI/TUI measurement. That net combines source changes and changes in reach; it is not a count of newly written code.

`learnloop/diagnosis/failure_triage.py` is already gone. K9.15, recorded at `docs/reviews/refactor-status.md:236` and `docs/reviews/refactor-k9.15.md`, removed its 1,054 lines and its registry entries. Its historical tables remain. The 11 CLI-only `field` modules remain and appear individually below.

**Exhaustive classification:** every tooling-only source module is listed below; the two unreachable modules are listed afterward; there are no tests-only modules. **Every other tracked Python module under `src/` is serving, verified by the import walk.** The package totals provide a cross-check:

| Package | Serving modules / lines | Tooling modules / lines | Unreachable modules / lines |
|---|---:|---:|---:|
| `learnloop/` — immediate files | 36 / 11,540 | 2 / 34 | 0 / 0 |
| `learnloop/adaptive_difficulty/` | 43 / 17,771 | 6 / 2,185 | 0 / 0 |
| `learnloop/ai/` | 41 / 13,329 | 1 / 187 | 1 / 47 |
| `learnloop/attempts/` | 31 / 21,972 | 3 / 669 | 0 / 0 |
| `learnloop/capture/` | 8 / 1,247 | 0 / 0 | 0 / 0 |
| `learnloop/cli/` | 0 / 0 | 58 / 19,301 | 0 / 0 |
| `learnloop/config/` | 7 / 5,773 | 1 / 186 | 0 / 0 |
| `learnloop/content/` | 87 / 62,275 | 3 / 737 | 0 / 0 |
| `learnloop/curriculum/` | 14 / 5,255 | 7 / 2,357 | 0 / 0 |
| `learnloop/daily_plan/` | 40 / 23,822 | 2 / 324 | 0 / 0 |
| `learnloop/data_capture/` | 4 / 752 | 0 / 0 | 0 / 0 |
| `learnloop/db/` | 85 / 48,430 | 1 / 188 | 0 / 0 |
| `learnloop/diagnosis/` | 106 / 65,313 | 14 / 6,880 | 0 / 0 |
| `learnloop/evsi_calibration/` | 0 / 0 | 17 / 10,523 | 0 / 0 |
| `learnloop/experiments/` | 0 / 0 | 36 / 14,119 | 0 / 0 |
| `learnloop/field/` | 7 / 2,889 | 11 / 4,142 | 0 / 0 |
| `learnloop/figures/` | 32 / 20,384 | 0 / 0 | 1 / 813 |
| `learnloop/followup_run/` | 11 / 2,999 | 0 / 0 | 0 / 0 |
| `learnloop/followup_serve/` | 6 / 1,201 | 0 / 0 | 0 / 0 |
| `learnloop/goals/` | 19 / 7,805 | 0 / 0 | 0 / 0 |
| `learnloop/hints/` | 17 / 9,591 | 2 / 938 | 0 / 0 |
| `learnloop/ingest/` | 23 / 6,864 | 0 / 0 | 0 / 0 |
| `learnloop/instructional/` | 17 / 7,642 | 1 / 318 | 0 / 0 |
| `learnloop/intent/` | 4 / 959 | 1 / 68 | 0 / 0 |
| `learnloop/learner/` | 23 / 11,454 | 4 / 1,033 | 0 / 0 |
| `learnloop/local_embeddings/` | 13 / 3,815 | 0 / 0 | 0 / 0 |
| `learnloop/matching/` | 5 / 996 | 0 / 0 | 0 / 0 |
| `learnloop/notebook_authoring/` | 0 / 0 | 3 / 194 | 0 / 0 |
| `learnloop/ops/` | 10 / 3,327 | 20 / 11,145 | 0 / 0 |
| `learnloop/params/` | 4 / 3,950 | 0 / 0 | 0 / 0 |
| `learnloop/placement/` | 8 / 3,209 | 1 / 395 | 0 / 0 |
| `learnloop/practice_index/` | 11 / 4,096 | 3 / 1,044 | 0 / 0 |
| `learnloop/projects/` | 5 / 2,761 | 5 / 2,529 | 0 / 0 |
| `learnloop/reader/` | 32 / 16,749 | 1 / 965 | 0 / 0 |
| `learnloop/recognition/` | 0 / 0 | 4 / 492 | 0 / 0 |
| `learnloop/remote/` | 7 / 1,604 | 0 / 0 | 0 / 0 |
| `learnloop/router/` | 10 / 6,072 | 2 / 282 | 0 / 0 |
| `learnloop/router_objective/` | 35 / 11,742 | 9 / 1,982 | 0 / 0 |
| `learnloop/scheduling/` | 37 / 14,778 | 4 / 1,555 | 0 / 0 |
| `learnloop/sim/` | 0 / 0 | 15 / 6,208 | 0 / 0 |
| `learnloop/source_retrieval/` | 36 / 26,978 | 6 / 2,577 | 0 / 0 |
| `learnloop/substrate/` | 21 / 8,861 | 4 / 1,783 | 0 / 0 |
| `learnloop/teacher/` | 18 / 7,689 | 1 / 322 | 0 / 0 |
| `learnloop/tui/` | 0 / 0 | 11 / 2,422 | 0 / 0 |
| `learnloop/tutor/` | 10 / 8,947 | 0 / 0 | 0 / 0 |
| `learnloop/vault/` | 13 / 4,717 | 1 / 73 | 0 / 0 |
| `learnloop/why/` | 4 / 1,317 | 0 / 0 | 0 / 0 |
| `learnloop/workbench/` | 9 / 4,543 | 0 / 0 | 0 / 0 |
| `learnloop_mcp/` | 6 / 932 | 0 / 0 | 0 / 0 |
| `learnloop_mobile/` | 11 / 2,780 | 0 / 0 | 0 / 0 |
| `learnloop_sidecar/` | 91 / 39,215 | 0 / 0 | 0 / 0 |

### The list the owner marks

Packages are sorted by tooling-only lines, largest first.

Module paths are relative to `src/`. They correspond to the generated notes’ `source_path` field. Their note titles are the dotted module names, with `__init__.py` represented by the package name. Existing notes have `title`, `source_path`, `package`, `layer`, `refactor_status` and source-line facts; this review does not modify them or add `reach`.

To keep paths readable:

- `C/name` means `learnloop/cli/name.py`.
- `L/path` means `learnloop/path.py`.
- The **path column lists the path before the row’s module**: append `→ this module`. `Root` means the row itself is seeded, so its shortest path has zero edges.
- `⇢ package` denotes the implicit package-initialization step.
- One shortest path is shown; ties were settled by sorted module name. These paths are **verified by the import walk**.
- Descriptions summarize module docstrings. “No module docstring” is literal, not an inferred purpose.
- `CLI …` identifies a command or command group present in `tests/cli_surface.json`; helper rows name the command they support.
- `R` means the parameter registry also loads the module by string; details follow the tables.
- `G` means the module is named in `tests/goldens/structure.toml`.
- `A` means it is named in `tests/fixtures/attempt_facts_census.toml`.
- `E` means it is named in `tests/fixtures/evidence_cutoff_census.toml`.
- `I` means it is named in `tests/goldens/identity_shapes.toml`.
- `W(table)` means a source-wide attribute-call scan found this module to be the sole caller of a repository write method for that table. This is **inferred ownership**, not a complete call-graph proof or permission to drop the table.

A blank removal-tie cell means no additional tie was identified by these checks. All modules also fall within the dynamic module-import smoke test in `tests/test_architecture.py`, discussed below.

**`learnloop/cli/` — 58 modules, 19,301 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/cli/__init__.py` | 112 | Root | No module docstring. | Console entry point; shared command registration | |
| `learnloop/cli/ad.py` | 251 | Root | Owner-run adaptive-difficulty commands. | CLI `ad` | |
| `learnloop/cli/ai.py` | 602 | Root | Provider sign-in, status, latency and comparison. | CLI `ai` | |
| `learnloop/cli/ai_compare.py` | 1,204 | Root | Compare the same real work across subscription profiles. | CLI `ai compare`; G | |
| `learnloop/cli/app.py` | 5,221 | Root | No module docstring. | Root CLI commands, including `init`, `upgrade`, `doctor`, `today`; G | |
| `learnloop/cli/calibration.py` | 70 | Root | No module docstring. | CLI `calibration import-bundle`, `bootstrap-sample` | |
| `learnloop/cli/card.py` | 78 | Root | No module docstring. | CLI `card write`, `reword`, `retire` | |
| `learnloop/cli/claims.py` | 32 | Root | No module docstring. | CLI `claims export`, `purge` | |
| `learnloop/cli/clarification.py` | 143 | Root | No module docstring. | CLI `clarification` | |
| `learnloop/cli/config.py` | 42 | Root | No module docstring. | CLI `config effective` | |
| `learnloop/cli/contamination.py` | 146 | Root | Embed and report shadow contamination flags. | CLI `contamination embed`, `report` | |
| `learnloop/cli/contracts.py` | 117 | Root | No module docstring. | CLI `contracts show`, `compare`, `amend` | |
| `learnloop/cli/controller.py` | 41 | Root | No module docstring. | CLI `controller open-world-gate` | |
| `learnloop/cli/curriculum.py` | 101 | Root | Whole-book section coverage. | CLI `curriculum cover`, `report` | |
| `learnloop/cli/data.py` | 218 | Root | Collection inspection and reproducible datasets. | CLI `data-quality`, `usage`, `dataset-export`, `adjudicate-remediation`; W(`false_remediation_adjudications`) | |
| `learnloop/cli/data_capture.py` | 55 | Root | Report whether long-horizon data capture works. | CLI `data-capture report` | |
| `learnloop/cli/decider.py` | 70 | Root | Evidence about the Decider’s Tier-1 judgments. | CLI `decider agreement` | |
| `learnloop/cli/depth.py` | 155 | Root | No module docstring. | CLI `depth` | |
| `learnloop/cli/diagnose.py` | 792 | Root | Offline review of blind grading and diagnosis. | CLI `diagnose`; sole observed caller of `requeue_post_attempt_job` | |
| `learnloop/cli/diagnosis.py` | 346 | Root | No module docstring. | CLI `diagnosis queue`, `adjudicate`, `scoreboard`, `calibration` | |
| `learnloop/cli/embeddings.py` | 751 | Root | Opt-in embedding maintenance with cost estimates. | CLI `embeddings`, including local/student commands | |
| `learnloop/cli/evaluation.py` | 201 | Root | One read-only offline evaluation harness. | CLI `eval`, `eval families`, `practice-index`, `success-head`, `placement`, `pf-pilot`, `pf-scaling`, `judges` | |
| `learnloop/cli/evsi.py` | 292 | Root | EVSI simulation and calibration commands. | CLI `evsi`; G | |
| `learnloop/cli/exam.py` | 202 | Root | No module docstring. | CLI `exam reserve`, `start`, `answer`, `finish`; G | |
| `learnloop/cli/experiments.py` | 306 | Root | Research experiments on copies. | CLI `experiments e0`, `experiments e1`; G | |
| `learnloop/cli/facets.py` | 187 | Root | Deduplicate facets, inspect actions and decide rewords. | CLI `facets` | |
| `learnloop/cli/families.py` | 107 | Root | Explicit family authoring. | CLI `families propose`, `undo` | |
| `learnloop/cli/field.py` | 311 | Root | Offline learner-field inspection and evaluation. | CLI `field data-check`; supports `eval` | |
| `learnloop/cli/field_classification.py` | 186 | Root | Opt-in question classification registration. | CLI `field classify-questions`; G | |
| `learnloop/cli/fit.py` | 212 | Root | No module docstring. | CLI `fit`; W(`fitted_parameters`) | |
| `learnloop/cli/gaps.py` | 190 | Root | Learner-text gap commands. | CLI `gaps`; G | |
| `learnloop/cli/goldenpath.py` | 25 | Root | No module docstring. | CLI `goldenpath init-fixture` | |
| `learnloop/cli/grading.py` | 374 | Root | No module docstring. | CLI `grading`; G | |
| `learnloop/cli/hints.py` | 128 | Root | Hint-use reporting and approach-map tooling. | CLI `hints report`, `hints maps build` | |
| `learnloop/cli/inbox.py` | 28 | Root | Read-only capture inbox view. | CLI `inbox list` | |
| `learnloop/cli/ingest_batches.py` | 90 | Root | No module docstring. | CLI `ingest-batches`; G | |
| `learnloop/cli/mcp.py` | 193 | Root | MCP serving, endpoint-token and activity commands. | CLI `mcp`; launches a serving adapter | |
| `learnloop/cli/notebook.py` | 33 | Root | Explicit owner-side artifact checks. | `notebook check` exists in source but is absent from `tests/cli_surface.json` | |
| `learnloop/cli/pf.py` | 118 | Root | Generate, verify, select and publish PF-b items. | CLI `pf generate`, `publish`, `status` | |
| `learnloop/cli/placement.py` | 100 | Root | Placement status and evaluation. | CLI `placement status`, `eval placement` | |
| `learnloop/cli/plan.py` | 95 | Root | Plan display and reporting. | CLI `plan show`, `report` | |
| `learnloop/cli/practice_index.py` | 295 | Root | Dossiers, practice retrieval, coverage and evaluation. | CLI `practice-index`, `eval practice-index` | |
| `learnloop/cli/probability_arms.py` | 441 | Root | Adapter for probability arms and judge routes. | Supports `eval` and `eval judges`; G | |
| `learnloop/cli/project.py` | 889 | Root | Delayed questions on agent-written code. | CLI `project`; existing owner decision keeps projects | |
| `learnloop/cli/questions.py` | 60 | Root | No module docstring. | CLI `questions list`, `resolve` | |
| `learnloop/cli/reader.py` | 220 | Root | Reader workflow-funnel reporting. | CLI `reader report`, `figure-checks`, `cues discover`, `label-roles` | |
| `learnloop/cli/receipts.py` | 145 | Root | Model-call receipts for one CLI command. | Shared CLI receipt lifecycle | |
| `learnloop/cli/recurrence.py` | 239 | Root | Recurrence groups with authority. | CLI `recurrence` | |
| `learnloop/cli/registry.py` | 296 | Root | No module docstring. | CLI `registry`; dynamic parameter loading | |
| `learnloop/cli/render.py` | 180 | Root | No module docstring. | Shared CLI namespace | |
| `learnloop/cli/router.py` | 465 | Root | Inspect logged router decisions and reports. | CLI `router` | |
| `learnloop/cli/runtime.py` | 873 | Root | No module docstring. | Shared CLI namespace and imports | |
| `learnloop/cli/sim.py` | 391 | Root | No module docstring. | CLI `sim` | |
| `learnloop/cli/source_set.py` | 116 | Root | No module docstring. | CLI `source-set` | |
| `learnloop/cli/sources.py` | 414 | Root | Source retrieval from the command line. | CLI `sources`, including exercise commands | |
| `learnloop/cli/success_head.py` | 234 | Root | Offline T8 success-head replay report. | CLI `eval success-head`; G | |
| `learnloop/cli/surfaces.py` | 70 | Root | No module docstring. | CLI `surfaces audit`, `retire` | |
| `learnloop/cli/teacher.py` | 48 | Root | Learned lesson-check weight reporting. | CLI `teacher report` | |

**`learnloop/experiments/` — 36 modules, 14,119 lines**

These rows collectively implement the snapshot’s `experiments e0` and `experiments e1` commands. Their plans, receipts, caches and reports are experiment-owned artifacts; removal would also retire those workflows.

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/experiments/__init__.py` | 9 | Root | Research experiments outside production serving. | | |
| `learnloop/experiments/contextual_embeddings/__init__.py` | 29 | Root | E0 hosted contextual embeddings without a GPU. | | |
| `learnloop/experiments/contextual_embeddings/adapters.py` | 1,151 | Root | Isolated Qwen, Perplexity and Voyage adapters. | G | |
| `learnloop/experiments/contextual_embeddings/answers.py` | 190 | Root | Blind answer evaluation for E0 finalists. | G | |
| `learnloop/experiments/contextual_embeddings/anthropic_api.py` | 373 | Root | Experiment-only Anthropic Messages transport. | G | |
| `learnloop/experiments/contextual_embeddings/bank.py` | 1,072 | Root | Question bank, labels and adjudication. | G | |
| `learnloop/experiments/contextual_embeddings/boundary.py` | 192 | Root | Keep provider messages within E0 paths. | | |
| `learnloop/experiments/contextual_embeddings/budget.py` | 772 | Root | One spend-admission limit across paid calls. | G | |
| `learnloop/experiments/contextual_embeddings/callers.py` | 628 | Root | Paid writer, context, label, tutor and judge roles. | G | |
| `learnloop/experiments/contextual_embeddings/corpus.py` | 975 | Root | Corpus copies, inventory, policy and candidate windows. | G | |
| `learnloop/experiments/contextual_embeddings/credentials.py` | 114 | Root | Read hosted credentials from the process environment. | Source inspected; no credentials read | |
| `learnloop/experiments/contextual_embeddings/delivery.py` | 391 | Root | Compare what delivery arms give the same tutor. | G | |
| `learnloop/experiments/contextual_embeddings/e1/__init__.py` | 26 | Root | E1 local contextual-embedding batch pilot. | | |
| `learnloop/experiments/contextual_embeddings/e1/decide.py` | 136 | Root | Prespecified E1 scoring and decision. | | |
| `learnloop/experiments/contextual_embeddings/e1/gpu_meter.py` | 190 | Root | Meter the experiment’s GPU-hour allowance. | | |
| `learnloop/experiments/contextual_embeddings/e1/ledger.py` | 90 | Root | E1 hard-cap authorization ledger. | | |
| `learnloop/experiments/contextual_embeddings/e1/local.py` | 314 | Root | Local jobs, worker launch, vectors and ranking. | Launches worker by file path | |
| `learnloop/experiments/contextual_embeddings/e1/pins.py` | 260 | Root | Frozen local-model and experiment constants. | | |
| `learnloop/experiments/contextual_embeddings/e1/plan.py` | 310 | Root | Inputs, GPU and dollar estimates, and plan identity. | | |
| `learnloop/experiments/contextual_embeddings/e1/replay.py` | 513 | Root | Import, replay and verify E0 artifacts by path. | | |
| `learnloop/experiments/contextual_embeddings/e1/report.py` | 51 | Root | Aggregate-only E1 reporting. | | |
| `learnloop/experiments/contextual_embeddings/e1/run.py` | 484 | Root | Dry run, preflight, GPU, labeling and scoring stages. | | |
| `learnloop/experiments/contextual_embeddings/e1/supplement.py` | 345 | Root | Labels for new candidates from local arms. | | |
| `learnloop/experiments/contextual_embeddings/e1/worker.py` | 853 | Root | Batch worker loading the local BF16 model. | Static import plus subprocess launch through `e1/local.py:237` | |
| `learnloop/experiments/contextual_embeddings/evaluate.py` | 94 | Root | Per-question scores and paired comparisons. | G | |
| `learnloop/experiments/contextual_embeddings/live.py` | 267 | Root | Wiring for a paid E0 run. | G | |
| `learnloop/experiments/contextual_embeddings/metrics.py` | 181 | Root | Evidence, ranking, agreement and interval metrics. | | |
| `learnloop/experiments/contextual_embeddings/paid.py` | 687 | Root | Frozen steps for an authorized paid run. | G | |
| `learnloop/experiments/contextual_embeddings/pins.py` | 575 | Root | Frozen models, routes, contracts, costs and seeds. | G | |
| `learnloop/experiments/contextual_embeddings/plan.py` | 493 | Root | Frozen run plan and cost estimate. | G | |
| `learnloop/experiments/contextual_embeddings/records.py` | 109 | Root | Experiment-owned receipts and verdicts. | | |
| `learnloop/experiments/contextual_embeddings/report.py` | 181 | Root | Aggregate-only E0 report. | | |
| `learnloop/experiments/contextual_embeddings/retrieval.py` | 327 | Root | Retrieval arms over common candidate units. | G | |
| `learnloop/experiments/contextual_embeddings/runner.py` | 636 | Root | Dry-run and paid-run execution. | G | |
| `learnloop/experiments/contextual_embeddings/stop_rules.py` | 190 | Root | Compute the experiment’s stop rules. | | |
| `learnloop/experiments/contextual_embeddings/system_arms.py` | 911 | Root | Named system arms on separate service copies. | Direct SQL modifies `source_document_blocks` on copies; G | |

**`learnloop/ops/` — 20 modules, 11,145 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/ops/capture_report.py` | 654 | C/data_capture | Counts and coverage for captured records. | CLI `data-capture report` | |
| `learnloop/ops/contamination/__init__.py` | 13 | C/contamination → L/ops/contamination/detectors ⇢ package | Contamination detectors as shadow flags. | | |
| `learnloop/ops/contamination/decider.py` | 57 | C/contamination → L/ops/contamination/report → L/ops/contamination/judge | Decider leak/reveal verdict. | | |
| `learnloop/ops/contamination/detectors.py` | 570 | C/contamination | Lexical, symbolic and vector contamination candidates. | | |
| `learnloop/ops/contamination/judge.py` | 415 | C/contamination → L/ops/contamination/report | Bounded leak/reveal judgments on shortlisted pairs. | G | |
| `learnloop/ops/contamination/recipes.py` | 146 | C/contamination | Embedding recipes for contamination records. | | |
| `learnloop/ops/contamination/report.py` | 581 | C/contamination | Shadow flags with audited samples. | CLI `contamination report`; G | |
| `learnloop/ops/contamination/symbolic.py` | 315 | C/contamination → L/ops/contamination/detectors | Symbolic answer checks for reveal detectors. | | |
| `learnloop/ops/content_fixes.py` | 194 | C/app | Repair content that doctor can safely fix. | CLI `doctor --fix-content` | |
| `learnloop/ops/debug_time.py` | 75 | C/runtime | No module docstring. | Uses timestamp-shifting SQL owner; named by `scripts/table_review.py:70` | |
| `learnloop/ops/debug_time_store.py` | 48 | C/runtime → L/ops/debug_time | SQL owner for debug-time mutations. | Dynamic table/column `UPDATE` at line 35; tables cannot be enumerated from its SQL literal alone | |
| `learnloop/ops/doctor.py` | 2,967 | C/runtime | No module docstring. | CLI `doctor`; G; named by `scripts/table_review.py:71` | |
| `learnloop/ops/embedding_compare.py` | 905 | C/embeddings | Shared embedding benchmark harness. | CLI `embeddings compare`; G | |
| `learnloop/ops/graph_nomination_report.py` | 361 | C/embeddings | Nomination recall on doctor-found duplicates. | CLI `embeddings nomination-report` | |
| `learnloop/ops/model_routes.py` | 169 | C/runtime → L/ops/doctor | Model-route health from call receipts. | CLI `doctor` | |
| `learnloop/ops/pf_generation.py` | 2,201 | C/pf | Generate, verify, filter, select and publish PF-b items. | W(`pf_candidates`, `item_skeletons`); sole observed claim/release caller for `surface_mint_requests`; G | |
| `learnloop/ops/pf_publish.py` | 572 | C/pf → L/ops/pf_generation | Publish verified survivors as ordinary items. | Content publication; G | |
| `learnloop/ops/pf_reports.py` | 642 | C/evaluation | PF-b pilot and scaling reports. | CLI `eval pf-pilot`, `eval pf-scaling` | |
| `learnloop/ops/pf_selection.py` | 88 | C/pf → L/ops/pf_generation | Pure diversity scores for PF-b selection. | | |
| `learnloop/ops/plan_transport.py` | 172 | C/app | Settings that still pin the old Codex harness. | G | |

**`learnloop/evsi_calibration/` — 17 modules, 10,523 lines**

These implement the `evsi` CLI family and `diagnosis calibration`. Their fit/report artifacts and Eedi inputs are part of the workflow; none were opened.

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/evsi_calibration/__init__.py` | 30 | Root | Measure EVSI/EIG calibration rather than assume it. | | |
| `learnloop/evsi_calibration/artifacts.py` | 43 | Root | Crash-safe fit and report artifact writes. | Artifact writer | |
| `learnloop/evsi_calibration/compare.py` | 1,483 | Root | Compare every recorded value in two simulation reports. | CLI `evsi compare`; G | |
| `learnloop/evsi_calibration/eedi.py` | 327 | Root | Read the two Eedi releases used by calibration. | External input format | |
| `learnloop/evsi_calibration/experiments.py` | 534 | Root | Full study behind EVSI simulation. | CLI `evsi simulate`; G | |
| `learnloop/evsi_calibration/families.py` | 953 | Root | True-learner simulator families over Eedi questions. | G | |
| `learnloop/evsi_calibration/family_data.py` | 289 | Root | Arrange Eedi answers for simulator families. | | |
| `learnloop/evsi_calibration/family_fit.py` | 961 | Root | Fit different simulator families to shared answers. | Fit artifacts | |
| `learnloop/evsi_calibration/forecast_report.py` | 902 | Root | Assess saved diagnosis forecasts. | CLI `diagnosis calibration`; A; G | |
| `learnloop/evsi_calibration/live_report.py` | 1,109 | Root | Assess live VOI forecasts. | CLI `evsi calibration`; G | |
| `learnloop/evsi_calibration/metrics.py` | 274 | Root | Score calibration, information, actions and time. | | |
| `learnloop/evsi_calibration/multifamily.py` | 1,300 | Root | Multi-family calibration study. | CLI `evsi multisim`; G | |
| `learnloop/evsi_calibration/multisim.py` | 412 | Root | Diagnostic episodes against any simulator family. | G | |
| `learnloop/evsi_calibration/policies.py` | 583 | Root | Compare selection and stopping policies. | G | |
| `learnloop/evsi_calibration/response_fit.py` | 579 | Root | Fit misconception responses to real answer patterns. | Fit artifacts | |
| `learnloop/evsi_calibration/simulate.py` | 375 | Root | Record episode forecasts against simulated outcomes. | | |
| `learnloop/evsi_calibration/world.py` | 369 | Root | Scenarios, true learners and the system’s model. | | |

**`learnloop/diagnosis/` — 14 modules, 6,880 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/diagnosis/gate_fit.py` | 206 | C/fit | Fit follow-up gates from override/usefulness labels. | CLI `fit gate` | |
| `learnloop/diagnosis/grading_hardcases.py` | 928 | C/grading | Wrong rejection and acceptance by judge route. | CLI `grading hardcases`; `fixtures/grading_hardcases/README.md:4`; G | |
| `learnloop/diagnosis/offline_review/links.py` | 132 | C/diagnose | Import pattern-link verdicts into the judgment ledger. | Writes through shared ledger APIs | |
| `learnloop/diagnosis/offline_review/report.py` | 1,068 | C/diagnose | M1 metrics from one run’s scratch copy. | CLI `diagnose report` | |
| `learnloop/diagnosis/offline_review/spot_check.py` | 482 | C/diagnose | Optional owner spot-check. | CLI `diagnose review`; G | |
| `learnloop/diagnosis/probe_audit.py` | 746 | C/app | Probe pilot audit and retirement telemetry. | CLI `probe-audit`; W(`probe_regrade_checks`) | |
| `learnloop/diagnosis/probe_coverage.py` | 174 | C/app | Hypothesis-contrast and family coverage. | CLI `probe-coverage` | |
| `learnloop/diagnosis/probe_lifecycle.py` | 271 | C/app | Family-version and instance lifecycle transitions. | W(`probe_family_lifecycle_events`); sole observed status-update caller for `probe_family_templates` | |
| `learnloop/diagnosis/recurrence/benchmarks.py` | 1,381 | C/embeddings | Eedi and replay recurrence benchmarks. | CLI comparison/recurrence workflows; G | |
| `learnloop/diagnosis/recurrence/report.py` | 295 | C/recurrence | M3 recurrence signals report. | CLI `recurrence report` | |
| `learnloop/diagnosis/split/pfc_report.py` | 437 | C/diagnose | PF-c before/after report. | CLI `diagnose pfc-report` | |
| `learnloop/diagnosis/split/reports.py` | 348 | C/diagnose | End-of-M2 report and learner signals. | CLI `diagnose m2-report`; G | |
| `learnloop/diagnosis/taxonomy_regrade.py` | 115 | C/app | Non-destructive taxonomy regrade checks. | CLI `taxonomy-regrade-check` | |
| `learnloop/diagnosis/text_gaps/report.py` | 297 | C/gaps | Gap-pipeline results by kind and chooser. | CLI `gaps report` | |

`learnloop/diagnosis/failure_triage.py` has no decision row because it is absent at this commit. Its former registry-only reach must not be copied into a current inventory.

**`learnloop/sim/` — 15 modules, 6,208 lines**

Seeding simulation modules as tooling means test-driven simulation libraries are tooling here, rather than tests-only. Removing them can remove validation gates even when no learner-facing path uses them.

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/sim/__init__.py` | 20 | Root | Synthetic-student belief-pipeline harness. | | |
| `learnloop/sim/ad_gates.py` | 395 | Root | AD simulation gates expressed as metrics. | Test-gate library; additional tooling root reach | |
| `learnloop/sim/ad_memory_experiment.py` | 224 | Root | Registered ADM runs and aggregate diagnostics. | Used by ADM reporting; additional tooling root reach | |
| `learnloop/sim/ad_memory_synthetic.py` | 468 | Root | Synthetic-only ADM experiment. | Additional tooling root reach | |
| `learnloop/sim/ad_synthetic.py` | 1,289 | Root | Synthetic learners, structured fixtures and readers. | Test/gate fixture builder; additional tooling root reach | |
| `learnloop/sim/certify.py` | 66 | Root | Execute parameter-certificate sweeps. | CLI registry certification | |
| `learnloop/sim/diagnostic_validation.py` | 646 | Root | End-to-end validation of planted hypotheses. | CLI `sim probe-validation`; G | |
| `learnloop/sim/grader_confusion.py` | 337 | Root | Inject planted grader confusion. | Simulation test dependency | |
| `learnloop/sim/kinship_admission.py` | 116 | Root | Admission simulation for soft-kinship features. | Coupled to `scheduling/kinship_feature.py` | |
| `learnloop/sim/metrics.py` | 372 | Root | Compare end-of-run beliefs with truth. | | |
| `learnloop/sim/offline_benchmarks.py` | 193 | Root | Offline forgetting-model benchmarks. | CLI `sim benchmark-forgetting` | |
| `learnloop/sim/profiles.py` | 191 | Root | Student presets and YAML loading. | Profile format | |
| `learnloop/sim/runner.py` | 1,114 | Root | Drive synthetic students through the real pipeline. | CLI `sim run` | |
| `learnloop/sim/student.py` | 481 | Root | Parameterized ground-truth learner model. | | |
| `learnloop/sim/sweep.py` | 296 | Root | Measure scheduling sensitivity to configuration. | CLI `sim sweep` | |

**`learnloop/field/` — 11 modules, 4,142 lines**

These are the strategy’s 11 CLI-only field modules, individually retained in the list.

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/field/answer_signals.py` | 391 | C/field | Offline answer-signal arms for predictor comparisons. | A; G | |
| `learnloop/field/classification.py` | 232 | C/field_classification | Explicit bounded paid question classification. | CLI `field classify-questions`; persisted classification workflow; G | |
| `learnloop/field/decider.py` | 109 | C/field_classification | Decider judgments for question classification. | CLI `field classify-questions` | |
| `learnloop/field/evaluation.py` | 836 | C/field | Store-free paired prequential evaluation. | CLI `eval`; A; G | |
| `learnloop/field/item_content.py` | 174 | C/success_head | Read-only index of shown text and stored vectors. | CLI `eval success-head` | |
| `learnloop/field/memory.py` | 44 | C/field → L/field/evaluation | Memory arms registered in the field arm registry. | Arm registration; static import verified | |
| `learnloop/field/priors.py` | 62 | C/field | Time-frozen priors from historical identities. | CLI evaluation | |
| `learnloop/field/probability_prep.py` | 675 | C/probability_arms | Paid preparation and cache loading for probability arms. | Cache/checkpoint writer; G | |
| `learnloop/field/probability_states.py` | 806 | C/probability_arms | State rendered for each probability variant. | E | |
| `learnloop/field/success_head.py` | 501 | C/success_head | Pure prequential success-head arms and analysis. | CLI `eval success-head`; I | |
| `learnloop/field/success_head_analysis.py` | 312 | C/success_head | Prespecified aggregate-only T8 analysis. | CLI `eval success-head`; G | |

**`learnloop/source_retrieval/` — 6 modules, 2,577 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/source_retrieval/b4.py` | 437 | C/embeddings → L/source_retrieval/suites | Compare PDF page images with extracted text chunks. | Benchmark suite | |
| `learnloop/source_retrieval/bench.py` | 363 | C/embeddings → L/source_retrieval/suites | Shared retrieval-comparison suite pieces. | G | |
| `learnloop/source_retrieval/evaluation.py` | 1,086 | C/embeddings → L/source_retrieval/suites | Compare source retrieval with substring search. | CLI `embeddings compare`; G | |
| `learnloop/source_retrieval/role_labeller.py` | 560 | C/reader | Owner-run batch role labeling. | CLI `reader label-roles`; G | |
| `learnloop/source_retrieval/suites.py` | 30 | C/embeddings | Register retrieval suites on the compare harness. | Suite registration | |
| `learnloop/source_retrieval/timing.py` | 101 | C/sources | Retrieval time from question receipts. | CLI sources reporting | |

**`learnloop/projects/` — 5 modules, 2,529 lines**

The existing owner decision in strategy §2.13 keeps projects and its CLI working. These are tooling-only by reach, but that does not supersede the keep decision.

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/projects/ai_contracts.py` | 227 | C/project → L/projects/probes | Structured AI contracts for delayed probes. | Existing keep decision | |
| `learnloop/projects/ai_runtime.py` | 506 | C/project | Routes, spend admission and model-call receipts. | Existing keep decision; G | |
| `learnloop/projects/hooks.py` | 157 | C/project | Optional append-only post-commit hook. | Installed external Git hooks; existing keep decision | |
| `learnloop/projects/probes.py` | 1,196 | C/project | Generate, seal, answer and grade delayed probes. | Standalone project store; existing keep decision; G | |
| `learnloop/projects/report.py` | 443 | C/project | Report probe validity and value. | CLI `project report`; existing keep decision | |

**`learnloop/tui/` — 11 modules, 2,422 lines**

The strategy already records the owner’s intention to rebuild this as a full alternative frontend. `learnloop today` remains its CLI door.

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/tui/__init__.py` | 1 | Root | Textual TUI. | CLI `today`; optional `tui` dependency | |
| `learnloop/tui/app.py` | 59 | Root | No module docstring. | `run` entry function | |
| `learnloop/tui/minutes_memory.py` | 87 | Root | Remember TUI session minutes. | Persistent preference | |
| `learnloop/tui/screens/__init__.py` | 1 | Root | Textual screens. | | |
| `learnloop/tui/screens/feedback.py` | 681 | Root | No module docstring. | G | |
| `learnloop/tui/screens/practice.py` | 578 | Root | No module docstring. | G | |
| `learnloop/tui/screens/start.py` | 386 | Root | No module docstring. | | |
| `learnloop/tui/screens/today.py` | 422 | Root | No module docstring. | G | |
| `learnloop/tui/state.py` | 64 | Root | No module docstring. | | |
| `learnloop/tui/theme.py` | 28 | Root | No module docstring. | | |
| `learnloop/tui/widgets.py` | 115 | Root | No module docstring. | | |

**`learnloop/curriculum/` — 7 modules, 2,357 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/curriculum/ai_contracts.py` | 143 | C/depth → L/curriculum/depth_edge_authoring | Structured contracts for curriculum depth features. | | |
| `learnloop/curriculum/concepts.py` | 470 | C/runtime | No module docstring. | Direct SQL writes to shared change/content/proposal tables | |
| `learnloop/curriculum/depth_edge_authoring.py` | 554 | C/depth | Author curated depth edges. | W(`depth_edge_templates`, `depth_edge_template_versions`, `depth_edge_instances`, `depth_milestone_versions`) | |
| `learnloop/curriculum/golden_path_confirm.py` | 368 | C/goldenpath → L/curriculum/golden_path_fixture | One atomic exemplar confirmation. | Sole observed caller of `confirm_golden_path_atomic`, spanning nine tables | |
| `learnloop/curriculum/golden_path_fixture.py` | 414 | C/goldenpath | Deterministic golden-path fixture bootstrap. | CLI `goldenpath init-fixture`; `tests/test_golden_path_fixture.py:7` | |
| `learnloop/curriculum/rung_backfill.py` | 156 | C/depth | Backfill depth-rung metadata on legacy items. | Content mutation; G | |
| `learnloop/curriculum/task_blueprints.py` | 252 | C/goldenpath → L/curriculum/golden_path_fixture | Reviewed immutable task-blueprint versions. | W(`task_blueprints`, `target_exemplars`); version/review write methods | |

**`learnloop/adaptive_difficulty/` — 6 modules, 2,185 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/adaptive_difficulty/arms.py` | 245 | C/ad | Harness arms scored on AD replay. | CLI `ad eval`; G | |
| `learnloop/adaptive_difficulty/backfill.py` | 277 | C/ad | Owner-run AD backfills. | CLI `ad backfill`; G | |
| `learnloop/adaptive_difficulty/data_check.py` | 197 | C/ad | AD data-check report. | CLI `ad data-check`; A | |
| `learnloop/adaptive_difficulty/dose_report.py` | 457 | L/sim/ad_gates | Dose-and-burden analysis. | Simulation-gate dependency | |
| `learnloop/adaptive_difficulty/history_audit.py` | 214 | C/ad | Owner-run forecast-history audit. | CLI `ad forecast-audit`; R; G | |
| `learnloop/adaptive_difficulty/report.py` | 795 | C/ad | Adaptive-difficulty report. | CLI `ad report`; G | |

**`learnloop/router_objective/` — 9 modules, 1,982 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/router_objective/calibration_report.py` | 213 | C/router | Calibration and cost by arm and day. | CLI `router objective-report` | |
| `learnloop/router_objective/diagnostic_value.py` | 320 | `scripts/probe_router_report.py` | Price a post-miss probe by the action its result enables. | Script-only additional reach | |
| `learnloop/router_objective/forecast_resolve.py` | 176 | C/router | Bind per-option forecasts to observed outcomes. | CLI `router objective-report` | |
| `learnloop/router_objective/goal_read.py` | 224 | C/router → L/router_objective/calibration_report | Two-stage versioned goal-date sensor. | R; G | |
| `learnloop/router_objective/miss_cause_report.py` | 129 | C/data_capture → L/ops/capture_report | Slip-or-gap capture report. | CLI `data-capture report` | |
| `learnloop/router_objective/objective_report.py` | 243 | C/router | Separate objective evaluations and comparators. | CLI `router objective-report`; G | |
| `learnloop/router_objective/preference_report.py` | 230 | C/data_capture → L/ops/capture_report | Report what the learner said would help. | A | |
| `learnloop/router_objective/report.py` | 247 | C/data_capture → L/ops/capture_report | Router capture coverage and daily byte counts. | | |
| `learnloop/router_objective/tail_report.py` | 200 | C/router | Learned-tail section of the objective report. | R; G | |

**`learnloop/substrate/` — 4 modules, 1,783 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/substrate/data_quality.py` | 175 | C/app | Dataset diagnostics in a consistent read transaction. | CLI `data-quality`; G | |
| `learnloop/substrate/dataset.py` | 752 | C/data | Reproducible datasets from database backups. | CLI `dataset-export`; artifact format; A; G | |
| `learnloop/substrate/model_usage.py` | 338 | C/data | Read-only usage report from model-call receipts. | CLI `usage` | |
| `learnloop/substrate/shadow_rebuild.py` | 518 | C/runtime | Evaluate a rebuild without changing the live database. | Rebuild tooling; G; `scripts/table_review.py:75` | |

**`learnloop/scheduling/` — 4 modules, 1,555 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/scheduling/evaluation.py` | 600 | C/field | Calibration reporting over logged decisions. | CLI `eval`; A; G | |
| `learnloop/scheduling/fsrs_fitting.py` | 214 | C/fit | Pure-Python FSRS-6 weight fitting. | CLI `fit fsrs`; G | |
| `learnloop/scheduling/kinship_feature.py` | 525 | C/controller → L/scheduling/open_world_gate | Descoped heuristic soft-kinship feature. | R; sole literal SQL writer found for three `familiarity_kernel_*` tables; migrations 100 and 101 | |
| `learnloop/scheduling/open_world_gate.py` | 216 | C/controller | Executable open-world dependency check. | CLI `controller open-world-gate`; string-loaded capability checks | |

**`learnloop/practice_index/` — 3 modules, 1,044 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/practice_index/coverage.py` | 92 | C/practice_index | Find facets with insufficient admissible items. | CLI `practice-index coverage` | |
| `learnloop/practice_index/evaluation.py` | 897 | C/practice_index | Compare two-level dossier retrieval with direct retrieval. | CLI `practice-index eval`, `eval practice-index`; G | |
| `learnloop/practice_index/tool.py` | 55 | C/practice_index | Agent-tool schema and dispatcher for finding practice. | CLI `practice-index tool-spec` | |

**`learnloop/learner/` — 4 modules, 1,033 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/learner/calibration.py` | 110 | C/runtime → L/ops/doctor | Monitor difficulty miscalibration. | CLI doctor path | |
| `learnloop/learner/independence_audit.py` | 278 | C/app | Recheck promoted beliefs against independence rules. | CLI `independence-audit` | |
| `learnloop/learner/recall_calibration.py` | 349 | C/runtime | No module docstring. | CLI `recall-calibration` | |
| `learnloop/learner/residual_diagnostics.py` | 296 | C/app | Residual-dependence diagnostics. | CLI `residual-diagnostics` | |

**`learnloop/reader/` — 1 module, 965 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/reader/reader_report.py` | 965 | C/reader | Reader workflow-funnel report. | CLI `reader report`; A; G | |

**`learnloop/hints/` — 2 modules, 938 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/hints/map_report.py` | 112 | C/hints | Approach-map rows in the hints report. | CLI `hints report` | |
| `learnloop/hints/report.py` | 826 | C/hints | Which hints are used and what follows. | CLI `hints report`; A; G | |

**`learnloop/content/` — 3 modules, 737 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/content/facet_identity/dedupe.py` | 247 | C/facets | One-off cleanup of existing facet identities. | CLI `facets dedupe`; identity mutation; G | |
| `learnloop/content/synthesis/facet_candidates.py` | 188 | C/app | Harvest candidate facets. | CLI `facet-candidates` | |
| `learnloop/content/synthesis/synthesis_eval.py` | 302 | C/app | Synthesis-quality evaluation harness. | CLI `synthesis-eval` | |

**`learnloop/attempts/` — 3 modules, 669 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/attempts/calibration_streams.py` | 215 | C/calibration | Calibration streams and retrospective bootstrap. | R; W(`calibration_stream_samples`) | |
| `learnloop/attempts/measurement_corrections.py` | 278 | C/app | Append-only assessment-contract corrections. | CLI `correct-measurement`; W(`measurement_contract_corrections`); triggers projection rebuild | |
| `learnloop/attempts/observations.py` | 176 | C/runtime | No module docstring. | CLI observation commands; W(`observation_templates`, `observation_events`) | |

**`learnloop/recognition/` — 4 modules, 492 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/recognition/__init__.py` | 6 | C/data_capture → L/ops/capture_report → L/recognition/report ⇢ package | Recognition and effort capture. | | |
| `learnloop/recognition/cue.py` | 203 | C/data_capture → L/ops/capture_report → L/recognition/report | Label the cue associated with an attempt. | | |
| `learnloop/recognition/ledger.py` | 142 | C/data_capture → L/ops/capture_report → L/recognition/report | Gather the records needed by cue labeling. | | |
| `learnloop/recognition/report.py` | 141 | C/data_capture → L/ops/capture_report | Split capture results by cue. | CLI `data-capture report` | |

**`learnloop/placement/` — 1 module, 395 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/placement/report.py` | 395 | C/placement | Learner-field assumption report. | CLI `eval placement`; G | |

**`learnloop/daily_plan/` — 2 modules, 324 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/daily_plan/report.py` | 182 | C/plan | Plan display and reporting. | CLI `plan show`, `plan report` | |
| `learnloop/daily_plan/schedule_effects.py` | 142 | C/app | Report how a schedule change affects serving. | Upgrade/report workflow | |

**`learnloop/teacher/` — 1 module, 322 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/teacher/report.py` | 322 | C/teacher | Report learned lesson-check weights. | CLI `teacher report` | |

**`learnloop/instructional/` — 1 module, 318 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/instructional/harvest.py` | 318 | C/sources | Owner-run textbook-exercise batch work. | CLI `sources exercises harvest`, `verify`; G | |

**`learnloop/router/` — 2 modules, 282 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/router/agreement.py` | 119 | C/decider | Router rows for Decider agreement reporting. | CLI `decider agreement` | |
| `learnloop/router/suggestion_report.py` | 163 | C/router | Lesson suggestions by randomized arm. | CLI `router report`; G | |

**`learnloop/notebook_authoring/` — 3 modules, 194 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/notebook_authoring/__init__.py` | 1 | Root | Owner-side checks without implicit learner context. | Explicit import-linter boundary; G | |
| `learnloop/notebook_authoring/check.py` | 68 | Root | Read an explicit artifact and write a structure report. | `notebook check`; absent from CLI snapshot | |
| `learnloop/notebook_authoring/marimo_adapter.py` | 125 | Root | Isolate pinned static marimo interfaces. | Subprocess `-m` self-launch at line 101; optional notebook dependencies | |

**`learnloop/db/` — 1 module, 188 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/db/storage.py` | 188 | C/runtime → L/ops/doctor | Side-effect-free database-storage facts. | CLI doctor path | |

**`learnloop/ai/` — 1 module, 187 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/ai/agreement.py` | 187 | C/decider | Compare Decider and LLM results without model calls. | CLI `decider agreement` | |

**`learnloop/config/` — 1 module, 186 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/config/kill_switches.py` | 186 | `scripts/vault_report.py` | Table of predecessor-restoring switches and defaults. | Script-only additional reach | |

**`learnloop/vault/` — 1 module, 73 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/vault/working_vault.py` | 73 | C/ai_compare | Explicitly mark a live working vault. | Safety marker used by comparison tooling | |

**`learnloop/intent/` — 1 module, 68 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/intent/report.py` | 68 | C/plan | Report committed intent in the plan report. | CLI `plan report` | |

**`learnloop/` immediate files — 2 modules, 34 lines**

| Module | Lines | Shortest path | Docstring summary | Removal ties | Keep/go |
|---|---:|---|---|---|---|
| `learnloop/__main__.py` | 5 | Root | No module docstring. | Executable `python -m learnloop` entry point | |
| `learnloop/app_launch.py` | 29 | C/app | Application launchers shared by entry-point adapters. | CLI launch bridge into serving adapters | |

### String loading and storage ties

**Parameter-registry imports**

`learnloop/params/parameter_registry.py:106` defines 100 source inventory entries. All 100 resolve to current source files. `MODULE_IMPORTS` at line 302 adds `learnloop.ai.providers.chatgpt_plan`. `_resolve_module_constant` imports the selected module at line 3018.

The following five inventory targets are tooling-only in the static graph. Their dynamic serving reach is **inferred from the registry source**, not verified by the import walk or by executing refresh:

| Module | Inventory key | Inventory source line |
|---|---|---:|
| `learnloop/attempts/calibration_streams.py` | `calibration_streams` | 110 |
| `learnloop/scheduling/kinship_feature.py` | `kinship_feature` | 165 |
| `learnloop/adaptive_difficulty/history_audit.py` | `ad_history_audit` | 269 |
| `learnloop/router_objective/goal_read.py` | `router_objective_goal_read` | 286 |
| `learnloop/router_objective/tail_report.py` | `router_objective_tail_report` | 293 |

None is globally string-only: each also has the static tooling path shown in its decision row. Removing one requires handling the registry inventory and registrations, not merely removing its CLI caller.

**Storage findings**

The literal SQL scan found `learnloop/scheduling/kinship_feature.py` to be the only source module with literal writes to:

- `familiarity_kernel_events`
- `familiarity_kernel_features`
- `familiarity_kernel_models`

Their schema is in `migrations/100_kinship_kernel_and_shadow_components.sql`, with further constraints in `migrations/101_dual_authority_and_kinship_dedup.sql`. This does not establish ownership of dynamically constructed SQL.

The `W` rows have these schema ties:

| Tooling caller | Write-method/table tie | Migration |
|---|---|---|
| `learnloop/cli/data.py` | `record_false_remediation` → `false_remediation_adjudications` | `migrations/162_false_remediation_adjudications.sql` |
| `learnloop/cli/fit.py` | `insert_fitted_parameters` → `fitted_parameters` | `migrations/016_fitted_parameters.sql` |
| `learnloop/attempts/calibration_streams.py` | `insert_calibration_stream_sample` → `calibration_stream_samples` | `migrations/066_grader_channel.sql` |
| `learnloop/attempts/measurement_corrections.py` | `append_measurement_contract_corrections` → `measurement_contract_corrections` | `migrations/116_measurement_contract_corrections.sql` |
| `learnloop/attempts/observations.py` | Insert observation templates and events | `migrations/001_initial.sql` |
| `learnloop/curriculum/depth_edge_authoring.py` | Template, template-version and instance writes | `migrations/107_depth_edge_templates.sql` |
| `learnloop/curriculum/depth_edge_authoring.py` | Insert depth-milestone versions | `migrations/072_commitments.sql` |
| `learnloop/curriculum/task_blueprints.py` | Blueprint, exemplar, version and review-event writes | `migrations/081_task_blueprints.sql` |
| `learnloop/curriculum/golden_path_confirm.py` | Atomic confirmation across blueprint, goal-contract, commitment, surface and golden-path tables | Migrations 065, 068, 072, 081 and 082 |
| `learnloop/diagnosis/probe_audit.py` | Insert probe regrade checks | `migrations/030_probe_pilot_and_policy.sql` |
| `learnloop/diagnosis/probe_lifecycle.py` | Update family-template status and insert lifecycle events | Migrations 028 and 030 |
| `learnloop/ops/pf_generation.py` | Insert/update candidates and insert skeletons | `migrations/174_pf_generation.sql` |
| `learnloop/ops/pf_generation.py` | Claim/release surface-mint requests | `migrations/078_surface_mint_jobs.sql` |

These are reasons to inspect removal together with storage behavior. They are not table-drop recommendations: stores, other methods, readers and historical records remain.

A textual scan of 380 tracked migration, fixture and golden files found the module references marked above. It found no literal tooling-module path or dotted module name in migration SQL. The `A`, `E`, `I` and `G` markers name the fixture/golden files that need review if a row goes.

### Boundary violations today

**None — verified by the import walk.**

There are zero static import edges from any serving-reachable module into:

```text
learnloop.cli
learnloop.tui
learnloop.experiments
learnloop.evsi_calibration
learnloop.sim
```

This includes function-local imports. There are therefore no violating `path:line` entries to list.

`pyproject.toml` currently defines 45 import-linter contracts over all four root packages, with external packages included. Existing entry-point independence contracts mostly use `allow_indirect_imports = true`, so they express direct boundaries. The existing `experiments-stay-outside-production` and `notebook-authoring-stays-outside-production` contracts use explicit source lists and `allow_indirect_imports = false`.

The notebook contract is the relevant model for L3’s transitive boundary. A static forbidden-import contract will not detect the registry’s string loads. This review did not run import-linter, so “zero edges” is an AST-walk result, not a reported contract-test pass.

### Tests-only modules

**None under the stated static roots.**

This does not mean all tooling modules have non-test users. The simulation and notebook packages are explicitly seeded as tooling roots, and every serving-package module is explicitly seeded as serving.

### Unreachable modules

These have no path from the stated roots under the static import rule. They do **not** both qualify for deletion.

| Module | Lines | Docstring summary | Evidence outside static reach | Disposition |
|---|---:|---|---|---|
| `learnloop/ai/providers/structured_output.py` | 47 | Provider repair prompts for malformed structured output. | No source string/file-load reference found. The generic module-import test dynamically discovers it. | Candidate for deletion review; no specific static consumer found |
| `learnloop/figures/source_check_harness.py` | 813 | Fixed figure-source check harness run in the sandbox. | `learnloop/figures/source_check.py:90` reads this file as text. The generic module-import test also discovers it. | Serving artifact by inferred file-use reach; do not treat as dead |

The generic import test at `tests/test_architecture.py:590–602` walks `learnloop` and `learnloop_sidecar` packages and imports discovered modules except `.__main__`. Its targets are dynamically enumerated, so it is not an edge in the static totals. It gives the first row inferred test reach, and does not replace the second row’s serving file-use evidence.

### Dynamic imports and unresolved reach

The following source and script sites sit outside the static edge definition. Literal target names and source paths were inspected; no loader was executed.

| Site | Target or inference |
|---|---|
| `learnloop/ai/__init__.py:33` | `_EXPORTS` names `learnloop/ai/client.py`, `routing.py`, `runtime.py`; all already statically serving |
| `learnloop/diagnosis/scoreboard.py:1550` | `_FALSE_CERTIFICATION_PRODUCER` names `learnloop/goals/certification_cold_probe.py`; already serving |
| `learnloop/instructional/valuation.py:397` | `NAMED_GAPS_MODULE` names `learnloop/diagnosis/text_gaps/pipeline.py`; already serving |
| `learnloop/params/parameter_registry.py:3018` | Inventory-derived names; the five non-serving static targets are listed individually above |
| `learnloop/scheduling/open_world_gate.py:73` | Capability checks name `diagnosis/robust_composition.py`, `attempts/effective_observation.py`, `learner/familiarity.py`, `substrate/administration_adapters.py`, `curriculum/golden_path_assessment.py`, `reader/annotations.py`, `attempts/salience_firewall.py`, `scheduling/constraint_engine.py`, `scheduling/staged_policy.py`, `scheduling/dispersion.py`, `scheduling/interleaving.py`, all beneath `learnloop/`; all already serving |
| `learnloop/local_embeddings/student_server.py:65` | Sibling `learnloop/local_embeddings/worker.py`; fallback to an existing static import |
| `learnloop/local_embeddings/student_server.py:82` | Sibling `learnloop/local_embeddings/student_trainer.py`; fallback to an existing static import |
| `learnloop/local_embeddings/student_trainer.py:72` | Sibling `learnloop/local_embeddings/worker.py`; fallback to an existing static import |
| `learnloop/ingest/fetchers.py:146` | Optional external targets at inspected call sites: `trafilatura`, `pypdf`, `youtube_transcript_api`; external imports not followed |
| `learnloop/experiments/contextual_embeddings/e1/run.py:136` | Literal standard-library `sys` |
| `learnloop_sidecar/handlers/reader.py:1840` | Literal standard-library `re` |
| `scripts/check_credit_report.py:50` | Sibling `scripts/probe_router_report.py`; already a tooling root |
| `scripts/probe_router_report.py:82` | Sibling `scripts/vault_report.py`; already a tooling root |
| `scripts/refactor_measures.py:171` | Computed module selected while examining version-set definitions; no individual runtime target resolved for this call |
| `learnloop/content/authoring/pf_sandbox.py:248` | Inside generated sandbox code: module `program`, supplied at runtime; unresolved generated content |
| `learnloop/content/authoring/pf_sandbox.py:296` | Inside generated sandbox code: names from `payload["programs"]`; unresolved generated content |
| `learnloop/notebook_authoring/marimo_adapter.py:101` | Subprocess `-m learnloop.notebook_authoring.marimo_adapter`; already a tooling root |
| `learnloop/figures/source_check.py:90` | Reads the harness source as text; inferred serving artifact reach |

The following computed test loaders were not expanded into additional graph edges. This is the complete set of variable-target `import_module`/`spec_from_file_location` sites found in the tracked test ASTs; literal imports of standard-library modules and literal source-module names were resolvable and do not create additional static edges.

| Test site | Unresolved or inferred target source |
|---|---|
| `tests/background_owners.py:75` | `OWNERS` table |
| `tests/identity_pins_helpers.py:719` | Module part of a caller-supplied identity-pin path |
| `tests/pinned_draws.py:162` | `SEED_SOURCES` table |
| `tests/pinned_draws.py:167` | `NUMERIC_POLICY` |
| `tests/test_architecture.py:590` | Package names `learnloop`, `learnloop_sidecar` |
| `tests/test_architecture.py:602` | Runtime `pkgutil.walk_packages` enumeration |
| `tests/test_architecture.py:643` | Local `dynamic_attributes` dictionary |
| `tests/test_architecture.py:647` | Scoreboard producer tuple |
| `tests/test_check_credit_activation.py:243` | Computed script path |
| `tests/test_check_credit_report.py:19` | Computed script path |
| `tests/test_desktop_activation_audit.py:32` | `SCRIPT`, outside the analyzed source/script root set |
| `tests/test_eval_harness.py:518` | Intentionally missing `learnloop.field.offline_llm` and `learnloop.cli.field_llm`; test expects absence |
| `tests/test_generated_provenance.py:25` | Documentation generator path |
| `tests/test_mobile_shortcuts.py:21` | iOS shortcut generator path |
| `tests/test_module_catalog_inventory.py:29` | Documentation module-validator path |
| `tests/test_output_budget.py:143` | Local retired-cap module dictionary |
| `tests/test_probe_records.py:29` | Parameterized `learnloop.diagnosis.{module}` |
| `tests/test_provider_resolution_parity.py:55` | `RESOLUTION_SITES` table |
| `tests/test_public_tip_guards.py:250` | Computed sanitizer script path |
| `tests/test_s0_landing.py:42` | Computed landing-script path |
| `tests/test_ux_walk_harness.py:29` | Caller-selected `scripts/ux_walk/{name}.py` |

Other file loaders with literal repository-relative script targets resolve to already-seeded scripts: `tests/test_affected_tests.py:17`, `tests/test_probe_router_report.py:30`, `tests/test_refactor_measures.py:16`, `tests/test_structure_ratchets.py:35`, `tests/test_table_review.py:121`, and `tests/test_vault_report.py:74`.

### Not verified

No tests, project imports, import-linter execution, model calls, network requests, installations, database opens or learner-vault reads were performed. Runtime dispatch, generated code, external packages, dynamically chosen loader arguments and complete storage-call ownership were not verified. Static reach is not proof that a function is called, or that deleting its module preserves behavior.

**Exact import-edge rule:** reproduce `scripts/refactor_measures.py`’s `_Imports` and use `top ∪ local`, as its reach and largest-cycle calculations do. Include ordinary and function-local `import`/`from` statements, including both branches of ordinary conditions and imports inside `try` blocks. Skip the non-runtime branch only for a bare `TYPE_CHECKING`, a name-qualified `.TYPE_CHECKING`, or its `not` form. Resolve relative imports from the current package. For `import a.b`, use the longest existing module prefix. For `from a import b`, use `a.b` when that module exists, otherwise the longest existing prefix of `a`. Omit self-edges and targets outside the indexed module set. During reach traversal, also visit every existing parent package initializer. String imports, entry-point declarations, subprocess execution and source read as text add no static import edge.
