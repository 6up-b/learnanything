# Figures and explanation videos map (K10, 2026-11-12)

Refactor step K10, job 1: the deep map of "Show me" figures and explanation videos that the Nov 8 map (`docs/reviews/architecture-map-2026-11-08.md`) read by size only. It names problems and recommends nothing; job 2 (the structure strategy) stands on it after the orchestrator has checked its claims. **Base: main `c4556cc700`**, branch `refactor/k10-figures-map`. Docs only; no source, test or vault note changed.

## Summary for the owner

(Written last; see the end of this section's commit history. Filled in below.)

## How to read this

**Scope** (brief K10): `src/learnloop/figures/` whole (25 modules), `figure_admission.py`, `teacher/visuals.py`, the sidecar's `handlers/figures.py` and `prefetch_runtime.py`, `reader/phone_media.py`, the figure stores (`db/stores/figures.py`, `db/stores/figure_prefetch.py`), the parts of `content/authoring/concept_animation.py` and `pf_sandbox.py` the figure tiers call, the `[figures]` config, and the desktop's figure and video code under `apps/learnloop-tauri/src` and `src-tauri`.

**Severity** is what a finding costs. **High:** it hides a cause, makes two answers to one question possible, or regularly costs a stage real time. **Medium:** it costs when you're in that area. **Low:** noise. Ids are prefixed `F10` so they don't collide with the Nov 8 map's, K2's or K9's: F10P packages and imports, F10D journeys, F10B boundaries and duplicated predicates, F10O decisions and what's recorded, F10F functional core, F10C comments, dead code and onboarding, F10H change cost, F10U what the learner sees, F10V vault.

**Evidence** is `file:line` at `c4556cc700`; `src/learnloop/` is dropped from paths under it, so `figures/service.py:2482` means `src/learnloop/figures/service.py:2482`. Paths under `src/learnloop_sidecar/` keep the `learnloop_sidecar/` prefix, and frontend paths start `apps/`. A bare `:line` continues the file before it. "Read" means I read the code; "traced" means I followed the calls without running them. Nothing was executed except an AST and import sweep over `src/` (K9's script, scoped to figures; script and output in the orchestrator's scratch, `refactor-k10/sweep_k10.py`, `sweep.txt`, `importers.txt`, `fs_names.txt`) and read-only `git log`/`git show`. No vault, backup or learner data was opened. Three read-only sweeps were delegated (the desktop's figure and video code; change cost from git history; the vault notes). Every claim of theirs used below was spot-checked at its cited line or commit, and those not checked are listed in "Not verified".

| § | Contents | Brief item |
|---|---|---|
| 1 | Packages, modules, deep and shallow, long functions, `service.py`'s names, imports and cycles, reachability | 1 |
| 2 | The journeys end to end | 2 |
| 3 | Boundaries and duplicated predicates | 3 |
| 4 | Decision points and what's recorded; which deciders are pure | 4 |
| 5 | Functional core and shell | 5 |
| 6 | Comments, dead code, onboarding | 6 |
| 7 | Change cost, counted | 7 |
| 8 | What the learner sees (input to the UX journey audit) | 8 |
| 9 | The vault notes | 9 |
| | Possible bugs found; Not verified | |

## 1. Packages and modules

Sizes are from the AST and tokenizer sweep at this tip; "code" means non-blank lines that aren't comments or docstrings, as in the Nov 8 map. Public names are module-level functions, classes and lower-case assignments without a leading underscore (upper-case constants left out, as K9 counts them). The class heuristic is the Nov 8 map's (deep: ≥250 code lines and ≤10 public names, or ≥400 and ≤1 public name per 40 lines; wide: ≥30 public names, or ≥20 with under 20 lines per name), corrected by reading where the heuristic misleads (noted in the last column). "Outside importers" are modules outside the scope list above.

| module | raw | code | public | outside importers (file:line) | class |
|---|---:|---:|---:|---|---|
| `figures/service.py` | 3,956 | 2,483 | 78 | `cli/reader.py:113`, `learnloop_sidecar/handlers/correspondents.py:47`, `handlers/hints.py:347`, `handlers/lesson.py:176`, `learnloop_sidecar/prefetch_runtime.py:109` (and the sidecar's `handlers/figures.py:75`, `teacher/visuals.py:65`) | wide; the god module |
| `figures/prefetch.py` | 1,862 | 1,260 | 37 | `learnloop_sidecar/prefetch_runtime.py:72`, `:98` (function-local only) | wide; composition layer |
| `figures/book_math.py` | 1,301 | 970 | 9 | none (source check only) | deep |
| `figures/spec.py` | 1,239 | 916 | 50 | none | wide (the grammar's data model: many small types) |
| `figures/rich.py` | 1,165 | 743 | 33 | `content/pipeline/jobs.py:3882` | wide; menu + route + job + readers in one |
| `figures/source_check.py` | 1,092 | 797 | 26 | `cli/reader.py:85`, `:114` | medium |
| `figures/manim_figure.py` | 930 | 674 | 17 | none | medium |
| `figures/sketch.py` | 910 | 642 | 32 | none | wide (the sketch program's types) |
| `figures/grammar.py` | 820 | 558 | 17 | none | medium; the expression grammar, imported by 8 figure modules |
| `figures/sketch_verify.py` | 818 | 554 | 8 | none | deep |
| `figures/source_check_harness.py` | 813 | 633 | 37 | none (read as text: §1.4) | a program, not a module |
| `figures/prefetch_model.py` | 633 | 377 | 17 | none | medium; pure (§5) |
| `figures/prefetch_ledger.py` | 616 | 391 | 25 | `cli/reader.py:79`, `:143` | wide |
| `figures/routes.py` | 613 | 405 | 17 | none | medium; prompt assembly + route |
| `figures/elements.py` | 603 | 427 | 11 | none | medium |
| `figures/sketch_engine.py` | 500 | 319 | 8 | none | deep (sealed wasm runner) |
| `figures/verify.py` | 467 | 315 | 13 | none | medium |
| `figures/learner_state.py` | 464 | 284 | 10 | none | deep |
| `figures/help.py` | 461 | 282 | 8 | `learnloop_sidecar/handlers/hints.py:267` | deep by count; half of it is a number formatter (§3.1) |
| `figures/records.py` | 435 | 296 | 10 | none | deep; B4's records |
| `figures/labels.py` | 320 | 171 | 6 | none | medium |
| `figures/power.py` | 317 | 195 | 9 | `learnloop_sidecar/prefetch_runtime.py:32` | medium |
| `figures/katex_tree.py` | 184 | 107 | 2 | none | medium |
| `figures/display_format.py` | 126 | 86 | 2 | none | medium (also run inside the sandbox) |
| `figures/foreground.py` | 87 | 50 | 4 | `learnloop_sidecar/server.py:223` | medium |
| `figures/__init__.py` | 28 | 0 | 0 | | init |
| **figures total** | **20,732** | **13,935** | | | 25 modules + init |
| `figure_admission.py` | 476 | 225 | 23 | 11 modules: `diagnosis/text_gaps/{jobs,sources}`, `diagnosis/split/figure_trace`, `source_retrieval/{library_ask,reader_tutor}`, `tutor/{reader_modes,tutor_qa}`, `workbench/help_outcomes`, `learnloop_sidecar/{context, handlers/hints, handlers/reader_tutor}` (`importers.txt`) | wide; a leaf so evidence-side code needn't import figures (`figure_admission.py:1-7`) |
| `learnloop_sidecar/handlers/figures.py` | 1,520 | 930 | 42 | `handlers/__init__.py:3`, `handlers/hints.py:268`, `handlers/reader.py:559`, `prefetch_runtime.py:99` | wide; adapts and decides (§3.3) |
| `teacher/visuals.py` | 375 | 217 | 18 | `teacher/service.py:74` | medium |
| `reader/phone_media.py` | 250 | 157 | 8 | `learnloop_mobile/media.py:53`, `learnloop_sidecar/phone_reader.py:23`, `learnloop_sidecar/serving.py:86` | medium; holds no figure code (§2.6) |
| `db/stores/figures.py`, `db/stores/figure_prefetch.py` | 412, 54 | | | | stores |
| `learnloop_sidecar/prefetch_runtime.py` | 202 | | | | the drain thread |

Together the scope is about 24,000 lines of Python (23,381 for the 30 swept modules) plus the desktop's `screens/reader/figures/` tree (§8).

### 1.1 The functions over about 200 lines

Only one function in the scope passes 200 lines; four more are over 120.

| lines | function | what it does |
|---:|---|---|
| 304 | `_author_attempts_and_store`, `figures/service.py:2482` | the whole author loop: up to two calls, three output contracts (V1/V2/V3 by flags), the free-text label rule, the tier verdict, a rich brief with an optional quick spec or sketch, the sketch path, the grammar path, step 3 (source check) inside the loop, then the row, the request row, two judgments and the check row in one transaction (§2.1 steps 9-14) |
| 187 | `verify_sketch`, `figures/sketch_verify.py:610` | runs a sketch program in the sealed engine over a grid and checks its declared probes and claims |
| 159 | `parse_sketch`, `figures/sketch.py:457` | the sketch program's parser and caps |
| 141 | `scene_problems`, `figures/sketch.py:680` | the sketch scene's validation |
| 124 | `_build`, `figures/service.py:2116` | grounding, context, the crop, the menu, the learner state, the reuse key and five alternative keys, reuse, the per-input lock, the request identity, then the author or the rich revision |

### 1.2 What `service.py`'s 78 public names are, and who calls each group

The Nov 8 map counted 76; this sweep counts 78 (the definitions are in `fs_names.txt`, each with its line). 31 of the 78 have no caller outside `service.py` in `src`; 11 of those are used by tests only (`SourceContext`, `Grounding`, `build_key`, `offer_build_key`, `key_for`, `learner_state_withheld`, `sketch_row`, `reverify_hash`, `fuller_state`, `BuildOutcome`, `stored_plan_open_items`) and 20 by nothing outside the module (for example `lesson_hosted` `:360`, `prediction_home` `:374`, `show_me_input` `:392`, `show_me_build_key` `:438`, `advanced_enabled` `:490`, `sketch_switch` `:516`, `inherited_learner_inputs` `:709`, `figure_homes` `:771`, `ground` `:947`, `crop_image` `:1013`, `property_checks` `:1265`, `ensure_rich_job` `:2795`, `rich_base_keys` `:3425`). Grouped by job:

| group | names (line) | callers |
|---|---|---|
| Request model and validation | `FigureRefused` `:257`, `FigureRequest` `:272`, `SourceContext` `:329`, `Grounding` `:341`, `BuildOutcome` `:1994`, `attempt_hosted` `:353`, `lesson_hosted`, `anchored` `:386`, `show_me_input`, `offered` `:431`, `check_request` `:1942` | the sidecar (`learnloop_sidecar/handlers/figures.py:439`, `:492`, `:652`, `:1265`), `teacher/visuals.py:207`, `figures/prefetch.py:335`, `:1419` |
| Admission keys | `build_key` `:405`, `offer_build_key` `:424`, `show_me_build_key` `:438`, `key_for` `:444` | inside `build_figure` only (`:2089`) |
| Switches (one-line wrappers over `figure_admission`) | `enabled` `:399`, `predictions_enabled` `:478`, `region_enabled` `:482`, `revisions_enabled` `:486`, `advanced_enabled` `:490`, `figure_offers_enabled` `:496`, `show_me_enabled` `:502`, `help_enabled` `:508`, `sketch_switch` `:516`, `sketch_enabled` `:522`, `rich_enabled` `:534`, `teacher_visuals_switch` `:367` | the sidecar (`handlers/figures.py:107-125`), `teacher/visuals.py:67`, `handlers/correspondents.py:90`, `prefetch_runtime.py:111` |
| Protection | `withheld_message` `:554`, `keys_withheld` `:581`, `row_withheld` `:597`, `learner_state_withheld` `:624`, `inherited_learner_inputs` `:709`, `figure_homes` `:771`, `figure_withheld` `:787`, `item_passages` `:3377`, `rich_base_keys`, `rich_base_item_protected` `:3444` | `figures/prefetch.py:959`, `figures/rich.py:423`, `:444` (function-local), `figures/help.py:393`, `cli/reader.py:113`, the sidecar (`handlers/figures.py:184`, `handlers/hints.py:347`), `teacher/visuals.py:334` |
| Context and grounding | `source_context` `:805`, `passages_context` `:839`, `ground` `:947`, `crop_image` `:1013`, `FindSources` `:892` | `figures/prefetch.py:335` (`source_context`); the rest inside `_build` |
| Presentation | `shown_row` `:1038`, `advanced_off_row` `:1068`, `sketch_row` `:1086`, `sketch_off_row` `:1092`, `rich_off_row` `:1104`, `rich_row` `:540`, `reverify_hash` `:1125`, `sketch_rechecked` `:1176`, `worded_row` `:1223`, `drawable_now` `:1258`, `property_checks` `:1265`, `figure_view` `:1325`, `source_rejected` `:1486`, `redelivered_view` `:1585`, `fuller_state` `:1619`, `show_me_row` `:781`, `prediction_home` | the sidecar (`handlers/figures.py:190`, `:1512`), `teacher/visuals.py:339`, `figures/help.py`, `figures/labels.py` |
| Build | `request_hash` `:1706`, `build_figure` `:2062`, `retry_rich_job` `:2291`, `ensure_rich_job` `:2795`, `resume_rich_intents` `:2814`, `revision_request` `:3147`, `rebuild_request` `:1556`, `rich_revision_retry` `:3717`, `build_prefetch_figure` `:3510` | the sidecar (`handlers/figures.py:262`, `:840`, `:849`), `handlers/lesson.py:180`, `figures/prefetch.py:1431` |
| Listing and reading | `list_figures` `:3530`, `section_figures` `:3544`, `rich_pending` `:3597`, `shown_figure` `:3746`, `prefetch_pending` `:3308`, `prefetch_plan_waits` `:3458`, `stored_plan_open_items` `:3357` | the sidecar (`handlers/figures.py:740-753`, `:1506`), `handlers/correspondents.py:213`, `figures/prefetch.py:1746` |
| Predictions | `record_prediction` `:3786`, `record_explanation` `:3858` | the sidecar (`handlers/figures.py:906`) |

The module also re-exports labels and constants it doesn't own (`NOT_FROM_BOOKS_LABEL = L.NOT_FROM_BOOKS_LABEL` `:222`, `SKETCH_LABEL` `:248-250`, `GROUNDING_PASSAGES = ADMISSION_GROUNDING_PASSAGES` `:216`). Eight unrelated jobs share one namespace, and the module docstring (`:1-142`) is a history of six stages rather than a description of the module.

### 1.3 Imports and cycles

No figures module is in the codebase's largest import component (the 191-module cycle): the sweep's `big_scc` holds none of the 30 swept modules. Of 430 import statements from the scope to `src` modules, 265 are function-local (`sweep.txt`).

**One cycle inside the package, four modules, closed only by function-local imports:**

| edge | where |
|---|---|
| `service` → `rich` | top level `figures/service.py:183`; also local `:1678`, `:2313`, `:3478`, `:3689` |
| `service` → `routes` | top level `figures/service.py:184` |
| `service` → `prefetch_ledger` | local `figures/service.py:3323` |
| `rich` → `routes` | top level `figures/rich.py:76` |
| `rich` → `service` | local `figures/rich.py:423`, `:444` |
| `rich` → `prefetch_ledger` | local `figures/rich.py:597` |
| `routes` → `rich` | local `figures/routes.py:368` |
| `prefetch_ledger` → `service` | local `figures/prefetch_ledger.py:169` |

So `service` and `rich` depend on each other: `service` owns the quick build and calls into `rich` for the menu and the job, while `rich`'s job asks `service` for the one protection predicate (`withheld_message`, `keys_withheld`, `rich_base_item_protected`). To avoid a third edge, `rich` keeps its own copy of `service.ATTEMPT_HOST_REFS` (`figures/rich.py:364-365` against `figures/service.py:208`). `prefetch` imports `service` 11 times, all function-local (`figures/prefetch.py:320`, `:332`, `:463`, `:586`, `:671`, `:801`, `:959`, `:1353`, `:1628`, `:1729`), and nothing in the package imports `prefetch` back, as its docstring promises (`figures/prefetch.py:5-6`).

**Leaves.** `grammar` imports nothing in the package and is imported by eight modules; `spec`, `verify`, `display_format`, `foreground`, `prefetch_model`, `labels` and `katex_tree` import at most `grammar`, `spec` or one sibling. The functional parts are leaves; the cycle is among the modules that do I/O.

**Across the edge.** `figure_admission` is imported by `service` (`:166-178`, `:511`), `rich` (`:71-73`), `source_check` (`:47`), `learner_state` (`:68`), `help` (`:39`) and eleven outside modules (§1 table); it imports only `ai.execution` (`figure_admission.py:36`). The sidecar's handler imports `service` at top level and `rich`, `source_check`, `help` and `prefetch_runtime` function-locally (`learnloop_sidecar/handlers/figures.py:75`, `:136`, `:673`, `:751`). `prefetch_runtime` imports the handler back function-locally (`learnloop_sidecar/prefetch_runtime.py:99`, `:189`) for `_rich_spawner`, a private name.

### 1.4 Reachability

Every figures module is reachable from the sidecar's serving roots (`sweep.txt`, column `reach`), except one:

- **`figures/source_check_harness.py` is not imported; it is read as text.** `figures/source_check.py:88-94` reads it and `display_format.py` with `Path(__file__).parent / "source_check_harness.py"` at import time, and `:518-519` sends the text to `pf_sandbox.run_sandboxed_python`. The harness says so itself (`figures/source_check_harness.py:3-6`) and imports `sympy` and `mpmath` at module level (`:51-53`), so importing it as a module would load them; its `display_format` import falls back to the package copy when imported rather than run (`:56-59`). Because `source_check` is imported at the top of `service` (`figures/service.py:186`), the harness file is read from disk whenever the figure service is imported.
- **Two modules read the desktop's tree at run time.** `figures/sketch_engine.py:51-53` loads `apps/learnloop-tauri/src/screens/reader/figures/sketch/sketch-engine.wasm` and `apps/learnloop-tauri/sketch-engine/engine.lock.json` through `Path(__file__).resolve().parents[3]`, and `figures/katex_tree.py:44-46` loads `apps/learnloop-tauri/sketch-engine/book-math-engine.wasm` the same way. The Python package's verification depends on files under the desktop app, so it works only from a source checkout.
- **CLI-only callers.** `cli/reader.py` imports `prefetch_ledger` (`:79`, `:143`), `source_check` (`:85`, `:114`) and `service` (`:113`) for reports; nothing in the package is reachable only from the CLI.
- **Phone and MCP.** Neither imports a figure module. The phone's host never registers a figure method: all 14 RPCs (`learnloop_sidecar/handlers/figures.py:84-99`) are pinned desktop-only by `tests/test_mobile_allowlist.py:649-652`, and the prefetch runtime refuses secondary contexts (`learnloop_sidecar/prefetch_runtime.py:141`).

### Findings

| Id | Severity | Finding | Evidence |
|---|---|---|---|
| F10P1 | high | `service.py` is eight modules in one (request model, admission keys, twelve switch wrappers, protection, context, presentation, build, listing, predictions) with 78 public names, 31 of them unused outside it; the 304-line author loop and the 124-line `_build` hold the tier choice, verification, retries, salvage and storage together. A reader can't change how a figure is presented without scrolling past the build, or the build without the rich job's intent plumbing. | §1.1, §1.2; `figures/service.py:2482`, `:2116` |
| F10P2 | medium | `service` ↔ `rich` (with `routes` and `prefetch_ledger`) is a cycle held only by function-local imports, and `rich` copies `ATTEMPT_HOST_REFS` to avoid one more edge. The menu, the rich route, the job and the job readers live in `rich`, the quick build and the protection predicate in `service`, so a change to "what may go to the rich author" touches both. | `figures/rich.py:364-365`, `:423`, `:444`; `figures/service.py:183`, `:208` |
| F10P3 | medium | Backend verification loads wasm artifacts from `apps/learnloop-tauri/` by relative path. Python and TypeScript share one engine on purpose (the sketch's parity), but the dependency is invisible to packaging and import tooling. | `figures/sketch_engine.py:51-53`; `figures/katex_tree.py:44-46` |
| F10P4 | low | `source_check_harness.py` sits in the package as a module, is read as text at import time and imports `sympy` if anyone ever imports it; a module walker or a coverage tool sees a module nothing imports. | `figures/source_check.py:88-94`; `figures/source_check_harness.py:51-59` |
| F10P5 | low | `service.py` re-exports constants and one-line switch wrappers over `figure_admission` (twelve wrappers), so a switch has two names (`FS.show_me_enabled` and `figure_admission.show_me_enabled`) and callers use both. | `figures/service.py:399-537`; `teacher/visuals.py:67`; `figures/prefetch.py:987` |
