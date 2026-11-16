# Refactor K10.7 and K10.8: the request, grounding, view, listing and predictions out of the figure service; the rest is the build

Branch `refactor/k10.7-8-figure-request-view`, based on main `250b0e16fe`. Steps K10.7 and K10.8 of the figures chain
(`docs/reviews/k10-figures-strategy-2026-11-14.md` §4.3). Structure only: every moved definition is byte for byte its
source (P-ast), and nothing a vault computes or a learner sees changes. The figure goldens and the identity pins pass
unchanged at every commit; no fixture or golden file differs from the base.

## 1. Commits

| Commit | What |
|---|---|
| `afe51553b9` | K10.8's first part, landed first: `figures/view.py` takes the presentation group (§3.1); the `_prebuilt_pressed` T4 port |
| `94e56e70ee` | K10.7: `figures/request.py` takes the request and its admission keys |
| `8d775a4456` | K10.7: `figures/grounding.py` takes the source context and the grounding |
| `1a65c91704` | K10.8: `figures/listing.py` takes the listing; the `section_figures` T4 port |
| `6308458de2` | K10.8: `figures/predictions.py` takes the predictions |
| `150b14ae3e` | K10.8: what is left of `service.py` is the build, renamed `figures/build.py`; the 142-line stage-history docstring replaced by one paragraph |
| `15dda81d25` | Vault references regenerated (§8) |
| (this commit) | This record |

No golden case was added before the moves (§5).

## 2. The order: the view first

The strategy orders the steps request (K10.7) before view (K10.8) and says "the view needs neither the build nor the
request". The second half holds; the first does not survive it: `check_request` reads three of the view's row
predicates (`rich_row`, `sketch_row`, `_advanced_kinds`: a revision's base figure, its tier and panel kinds switched
on). With `request.py` landed first it would import them from `service.py`, which imports `request.py`: a new cycle.
So "leaves first" puts the view first, and the commits run view, request, grounding, listing, predictions, rename.
Each new module imports only modules below it:

```
protection  <-  view  <-  request  <-  grounding
                  ^          ^
                  |          |
               listing  <----+          (listing: view, request, protection)
                  ^
             predictions                (predictions: listing, view, request)
build: view, request, grounding, listing, protection (and nothing imports build but its callers)
```

`rebuild_request` sits among the view functions in `service.py` and the strategy's table names "its view half" under
presentation and the whole function under the build. It has no view half to split: it reads the source check's row and
calls `revision_request` (the build's) to make a `FigureRequest`. In the view it would close view -> build. It stays
with the build, moved beside `revision_request` (judgment call; P-ast: same definition).

## 3. Step 0

### 3.1 What moved where, and the constants that moved with it

Every caller of each moved name at the base (`250b0e16fe`), from an AST sweep resolving `import ... as` aliases and
function-local imports over `src/`, `tests/` and `scripts/` (`callers.py`, scratch): 430 references to
`service.py`'s names (the build's included) outside it, in 49 files. `scripts/` had none. By group, with the `src` callers in full and the tests counted:

**View** (`figures/view.py`, 45 definitions). Moved: `NOT_FROM_BOOKS_LABEL`, `LEDGER_TASK`, `RECONSTRUCTION_REASON`, `LABELS`, `SKETCH_LABEL`, `SKETCH_UNCHECKED_LABEL`, `SKETCH_NOT_FROM_BOOKS_LABEL`, `SKETCH_OFF_KIND`, `ENGINE_CHANGED_REASON`, `rich_row`, `ADVANCED_OFF_KIND`, `shown_row`, `PROPERTY_CHECKS`, `_advanced_kinds`, `advanced_off_row`, `sketch_row`, `sketch_off_row`, `rich_off_row`, `_RECHECKED`, `_RECHECKED_GUARD`, `REVERIFY_VERSION`, `reverify_hash`, `_stored_verifier`, `_record_reverification`, `sketch_rechecked`, `worded_row`, `drawable_now`, `property_checks`, `_label`, `_prediction_view`, `_anchor_span`, `figure_view`, `_sketch_view`, `_manim_view`, `source_rejected`, `_source_rejected_row`, `_source_check_view`, `_coded_answer`, `_code_owned_labels`, `_presented_row`, `redelivered_view`, `fuller_state`, `_prefetch_intent_refused`, `_figure_request`, `_prebuilt_pressed`. Those with callers outside `service.py`:

| Name | Callers in `src` (file:line) | Tests |
|---|---|---|
| `advanced_off_row` | src/learnloop/figures/help.py:420 | 0 refs in 0 files |
| `drawable_now` | src/learnloop/figures/help.py:420 | 2 refs in 1 files |
| `ENGINE_CHANGED_REASON` | - | 1 refs in 1 files |
| `figure_view` | src/learnloop/teacher/visuals.py:340, src/learnloop_sidecar/handlers/figures.py:1532 | 0 refs in 0 files |
| `fuller_state` | - | 7 refs in 1 files |
| `LABELS` | - | 2 refs in 2 files |
| `NOT_FROM_BOOKS_LABEL` | - | 2 refs in 2 files |
| `_prebuilt_pressed` | - | 1 refs in 1 files |
| `PROPERTY_CHECKS` | - | 1 refs in 1 files |
| `_RECHECKED` | - | 9 refs in 2 files |
| `RECONSTRUCTION_REASON` | - | 3 refs in 2 files |
| `redelivered_view` | src/learnloop_sidecar/handlers/figures.py:202 | 1 refs in 1 files |
| `reverify_hash` | - | 2 refs in 1 files |
| `rich_row` | src/learnloop/figures/help.py:415, src/learnloop/teacher/visuals.py:338, src/learnloop_sidecar/handlers/figures.py:1045, src/learnloop_sidecar/handlers/figures.py:1364 | 1 refs in 1 files |
| `SKETCH_LABEL` | - | 2 refs in 2 files |
| `SKETCH_NOT_FROM_BOOKS_LABEL` | - | 1 refs in 1 files |
| `sketch_off_row` | src/learnloop/figures/help.py:421 | 0 refs in 0 files |
| `sketch_row` | - | 1 refs in 1 files |
| `SKETCH_UNCHECKED_LABEL` | - | 1 refs in 1 files |
| `source_rejected` | src/learnloop/figures/help.py:423 | 1 refs in 1 files |

**Request** (`figures/request.py`, 27). Moved: `ORIGINS`, `RESERVED_ORIGINS`, `SERVICE_ORIGINS`, `LESSON_TIERS`, `OFFER_ORIGINS`, `GOAL_AUTHORS`, `GOAL_CHARS`, `GROUNDINGS`, `NOTE_CHARS`, `FigureRefused`, `FigureRequest`, `attempt_hosted`, `lesson_hosted`, `prediction_home`, `anchored`, `show_me_input`, `build_key`, `offer_build_key`, `offered`, `show_me_build_key`, `key_for`, `_key_for`, `_PREFETCH_BUILD`, `PREFETCH_GOAL_AUTHORS`, `_validated_request`, `_validated_prefetch`, `check_request`. Those with callers outside `service.py`:

| Name | Callers in `src` (file:line) | Tests |
|---|---|---|
| `anchored` | src/learnloop_sidecar/handlers/figures.py:524 | 0 refs in 0 files |
| `attempt_hosted` | src/learnloop_sidecar/handlers/figures.py:650 | 0 refs in 0 files |
| `build_key` | - | 6 refs in 3 files |
| `check_request` | src/learnloop_sidecar/handlers/figures.py:512, src/learnloop_sidecar/handlers/figures.py:672, src/learnloop_sidecar/handlers/figures.py:1285 | 4 refs in 3 files |
| `FigureRefused` | src/learnloop/figures/prefetch.py:1427, src/learnloop/teacher/visuals.py:259, src/learnloop_sidecar/handlers/figures.py:163, src/learnloop_sidecar/handlers/figures.py:516, src/learnloop_sidecar/handlers/figures.py:673, src/learnloop_sidecar/handlers/figures.py:870, src/learnloop_sidecar/handlers/figures.py:929, src/learnloop_sidecar/handlers/figures.py:964, src/learnloop_sidecar/handlers/figures.py:1288, src/learnloop_sidecar/handlers/figures.py:1527, src/learnloop_sidecar/handlers/figures.py:283, src/learnloop_sidecar/handlers/figures.py:864 | 25 refs in 12 files |
| `FigureRequest` | src/learnloop/figures/prefetch.py:335, src/learnloop/figures/prefetch.py:1412, src/learnloop/figures/prefetch.py:1418, src/learnloop/teacher/visuals.py:207, src/learnloop/teacher/visuals.py:214, src/learnloop_sidecar/handlers/figures.py:253, src/learnloop_sidecar/handlers/figures.py:512, src/learnloop_sidecar/handlers/figures.py:1285 | 64 refs in 26 files |
| `key_for` | - | 6 refs in 2 files |
| `LESSON_TIERS` | - | 1 refs in 1 files |
| `offer_build_key` | - | 3 refs in 2 files |
| `RESERVED_ORIGINS` | - | 1 refs in 1 files |
| `SERVICE_ORIGINS` | src/learnloop_sidecar/handlers/figures.py:452 | 1 refs in 1 files |

**Grounding** (`figures/grounding.py`, 17). Moved: `GROUNDING_PASSAGES`, `FIGURE_BLOCK_TYPES`, `CONTEXT_BLOCKS`, `PASSAGE_CHARS`, `CONTEXT_CHARS`, `SourceContext`, `Grounding`, `source_context`, `passages_context`, `FindSources`, `_find_sources`, `_reading_learning_objects`, `_passage_ref`, `_with_sources`, `ground`, `_decode`, `crop_image`. Those with callers outside `service.py`:

| Name | Callers in `src` (file:line) | Tests |
|---|---|---|
| `Grounding` | - | 3 refs in 2 files |
| `GROUNDING_PASSAGES` | - | 3 refs in 2 files |
| `SourceContext` | - | 12 refs in 8 files |
| `source_context` | src/learnloop/figures/prefetch.py:335 | 3 refs in 2 files |

**Listing** (`figures/listing.py`, 12). Moved: `_root`, `_listed`, `_prebuilt_within_budget`, `_prebuilt_listed`, `prefetch_pending`, `prefetch_plan_waits`, `list_figures`, `section_figures`, `rich_pending`, `_failed_correction`, `_rich_line`, `shown_figure`. Those with callers outside `service.py`:

| Name | Callers in `src` (file:line) | Tests |
|---|---|---|
| `list_figures` | src/learnloop_sidecar/handlers/figures.py:760 | 19 refs in 7 files |
| `prefetch_pending` | src/learnloop_sidecar/handlers/figures.py:773 | 9 refs in 2 files |
| `prefetch_plan_waits` | src/learnloop/figures/prefetch.py:1738, src/learnloop_sidecar/handlers/figures.py:768 | 15 refs in 4 files |
| `rich_pending` | src/learnloop_sidecar/handlers/figures.py:763 | 25 refs in 5 files |
| `section_figures` | src/learnloop_sidecar/handlers/correspondents.py:214 | 3 refs in 2 files |
| `shown_figure` | src/learnloop_sidecar/handlers/figures.py:1526 | 2 refs in 2 files |

**Predictions** (`figures/predictions.py`, 8). Moved: `EXPLANATION_CHARS`, `ANSWER_CHARS`, `PREDICTION_PREFIX`, `record_prediction`, `_sketch_outcome`, `record_explanation`, `_queue_formative`, `_queued`. Those with callers outside `service.py`:

| Name | Callers in `src` (file:line) | Tests |
|---|---|---|
| `record_explanation` | src/learnloop_sidecar/handlers/figures.py:962 | 1 refs in 1 files |
| `record_prediction` | src/learnloop_sidecar/handlers/figures.py:926 | 0 refs in 0 files |

Membership judgment calls (where to read the diff):
- **Constants go with the lowest module that reads them**, and the modules above import them by name, else a cycle
  closes: `LEDGER_TASK` (`figure_verified`; the view's re-verification and the build's verdicts) and
  `RECONSTRUCTION_REASON` (the view's `shown_row`, the build's author loop) live in `view.py`; `_PREFETCH_BUILD` (the
  context variable `_validated_request` reads and `build_prefetch_figure` sets: one object, imported) in `request.py`.
- **`_figure_request` and `_prebuilt_pressed` go to the view**: `figure_view` and `fuller_state` read them, and the
  listing and the build (`revision_request`) import them from there. The strategy lists `_prebuilt_pressed` with the
  listing's cue budget.
- **`_rich_line` and `_failed_correction` go to the listing**, the build importing them: `rich_pending` builds its
  lines with them. `_rich_line`'s annotation names `FigureRequest`, so in the view it would need the request (a cycle).
- **`GROUNDINGS` goes to the request** (only `_validated_request` reads it), `GROUNDING_PASSAGES` to the grounding.
- **Stays with the build:** `request_hash`, `_recorded_input_key`, `_unrecorded_occupant`, `LEARNER_INPUTS_RECORDED`,
  `_with_learner_inputs`, `REUSE_ORIGIN`, `SHOW_ME_VERSION`, `REQUEST_PREFIX`, `FIGURE_PREFIX`, `TIER_LEDGER_TASK`,
  `rebuild_request`, `revision_request`, `rich_revision_retry`, `build_prefetch_figure` (the strategy's build group).
  The K10.4 pins read `request_hash` and `_recorded_input_key` (sites K10.4a, K10.4b: `_build` too); their bytes are
  untouched and only the file they live in is renamed.
- **Private names now cross module boundaries by import** (they keep their names so P-ast holds and every caller's
  body reads the same): from the view `_advanced_kinds` (request), `_RECHECKED`, `_RECHECKED_GUARD`, `_anchor_span`,
  `_figure_request`, `_label`, `_prebuilt_pressed`, `_source_rejected_row` (listing), `_code_owned_labels`,
  `_coded_answer`, `_prediction_view` (predictions), `_figure_request` (build); from the listing `_rich_line`,
  `_failed_correction` (build); from the request `_PREFETCH_BUILD` (build). Renaming them public is a later one-line
  change each (open item).
- No re-export: `build.py` and the new modules define every name a caller asks them for (`undefined_refs.py` over
  the seven modules reports no undefined name and no name reached through a module that only imports it).

### 3.2 Import directions after the move

| Module | Imports from the figures package | Reaches back into the build? |
|---|---|---|
| `view.py` | `elements`, `labels`, `rich`, `sketch`, `source_check`, `spec`, `verify`, `protection`; function-local `sketch_verify`, `sketch_engine`, `power` | no |
| `request.py` | `rich`, `routes`, `protection`, `sketch` (`sketch_ready`), `view`; function-local `power` | no |
| `grounding.py` | `protection`, `request`; function-local outside the package only | no |
| `listing.py` | `rich`, `sketch`, `spec`, `verify`, `protection`, `request`, `view`; function-local `power`, `prefetch_ledger`, `sketch_verify`, `sketch_engine` | no |
| `predictions.py` | `sketch`, `spec`, `listing`, `request`, `view`; function-local `sketch_verify`, `sketch_engine` | no |
| `build.py` | `labels`, `records`, `rich`, `routes`, `sketch`, `source_check`, `spec`, `verify`, `grounding`, `listing`, `protection`, `request`, `view` | (is the build) |

None of `rich`, `routes`, `sketch`, `source_check`, `spec`, `verify`, `protection`, `power`, `prefetch_ledger` imports
the build or any new module (K10.6 cut the last such edge). The callers outside: the sidecar figure handler imports
`build`, `view`, `request`, `listing`, `predictions` at the top; `prefetch` imports `build`, `request`, `grounding`,
`listing` function-locally where it imported `service` (three sites); `help`, `teacher.visuals`, the correspondents
and lesson handlers import the module they use where they imported `service`. The structure ratchet's cycle count is
unchanged (§6).

### 3.3 The request checks the strategy hands to K8

The handler's own request checks (`learnloop_sidecar/handlers/figures.py` `_request_figure`) stay; none moved. For K8:
one refuses what `check_request` also refuses, with a different error type: an origin no RPC may name
(`SERVICE_ORIGINS`: the handler's `SidecarError("validation_error")`; `_validated_request`'s `RESERVED_ORIGINS` and the
lesson-host rules as `FigureRefused("validation_error")`). A cold check in flight is refused by the handler alone
(`SidecarError("cold_check")`, twice); `FigureRefused` has no code for it.

## 4. What changed outside the moves

- `service.py` -> `build.py`: `git mv`, every definition unchanged (P-ast, 53 of 53). The module docstring (142 lines,
  a history of RW5a-RW5d P5) is one paragraph on what the build does; the history stays in git and `docs/reviews`.
  Each new module has a docstring saying what it does and what it imports.
- Callers were retargeted by a script that rewrites `ALIAS.name` at its AST position, splits
  `from learnloop.figures.service import ...` per new home, and adds or drops the module imports per scope
  (`retarget.py`, scratch; every change printed). The aliases: `FV` view, `FQ` request, `FGR` grounding, `FL` listing,
  `FPR` predictions, `FB` build. Four test files reached module attributes through `service` (`FS.S`, `FS.R`,
  `FS.store`, `FS.RICH`); they now read them through `FB` (the same module objects).
- Docstrings and comments naming a moved name's old home: `labels.py`, `sketch_verify.py` (a comment), `prefetch.py`
  (3), `prefetch_ledger.py`, `learner_state.py`, `teacher/visuals.py`, the lesson and correspondents handlers, the
  package docstring, `identity_pins_helpers.py` (2), `test_figure_rich_failed_correction_durable.py`.
- `tests/identity_pins_helpers.py`: imports from `request`, `grounding` and `build`; the K10.4a and K10.4b
  `IdentitySite` sources name `build.py`. `tests/goldens/identities.toml` and `identity_shapes.toml` unchanged.
- `tests/test_rw5c_never_evidence.py`'s allowlist names `build.py` for `service.py`.

## 5. Golden cases

None added. K10.4's coverage run lists the unreached lines of the request (14), grounding (13), view (20), listing
(22) and predictions (6) groups and calls them defensive guards that move verbatim; P-ast is what covers a verbatim
move. The risk a move adds on an unreached line is a name the new module does not bind (a `NameError` only on that
path). `ruff check` (pyflakes F821, undefined names, annotations included) passes on every new module and on
`build.py` at every commit, and every function-local import moved inside its function.

## 6. Proofs

**P-ast** (`past.py`, scratch; the K10.5-6 script: `ast.dump` of each whole definition with decorators and docstring,
and its source lines with comments and the `#:` lines above a constant):

| Commit | Moved definitions | Result | Rest of `service.py` / `build.py` |
|---|---|---|---|
| `afe51553b9` view | 45 (and `rebuild_request` within the file) | all SAME | 116 SAME; `__all__` lost the moved names |
| `94e56e70ee` request | 27 | all SAME | SAME; `__all__` |
| `8d775a4456` grounding | 17 | all SAME | SAME; `__all__` |
| `1a65c91704` listing | 12 | all SAME | SAME; `__all__` |
| `6308458de2` predictions | 8 | all SAME | SAME; `__all__` |
| `150b14ae3e` rename | 53 (`service.py` -> `build.py`, `__all__` included) | all SAME | n/a |

No rewrite was needed on the moved side: no moved function named its old module. The callers' files were compared
the same way with `FS.name -> NEW.name` mapped: every other definition differs only in a function-local import line
(`service as FS` -> the new module), a docstring naming the new home, an IdentitySite path, or the two T4 ports (§7).

**P-golden.** `tests/test_figure_build_golden.py`, `tests/test_figure_rich_job_golden.py` and
`tests/test_figure_prompts_golden.py` pass at every commit. `git diff 250b0e16fe -- tests/fixtures
tests/goldens/identities.toml` is empty (as are `identity_shapes.toml` and `structure.toml`).

**P-pins.** `tests/test_identity_pins.py` passes at every commit; `identities.toml` and `identity_shapes.toml` are
unchanged; `test_every_registered_source_exists` passes on the renamed sources.

**Structure ratchet** (`refactor_measures.py` at the base and the tip): largest import component 186 -> 186; modules
in a cycle 279 -> 279; functions over 200 lines 73 -> 73 (`_author_attempts_and_store`, now in `build.py`); stage
comment lines 2,374 -> 2,374 (`service.py`'s 52 are now build 28, view 9, listing 8, request 6, predictions 1); first-
level names and stage-named test files unchanged. Nothing fell, so the golden was not rewritten: its `[members]` and
`[stage_comments_by_file]` still name `service.py` (they only word a failure message; open item).

**Targeted gate:** GATE_RESULT

## 7. Tests ported (T4) and changed

| Test | Was | Now |
|---|---|---|
| `test_rw5c_recheck.py::test_a_prebuilt_figure_nobody_pressed_for_that_differs_lists_nothing` | built a pressed figure, set its `origin` to `prefetch` by SQL and patched `FS._prebuilt_pressed` to answer False | builds a real pre-build (`build_prefetch_figure` with figures ahead of need on and mains power: its request's build mode is `prefetch`, nobody pressed), checks it lists, then the source check finds it different and the list is empty. The old test held with the pre-build switch off too (an unpressed prebuild never lists then); the port turns it on, so the source check is what removes the figure. The final assertion is unchanged |
| `test_reader_rw5d_p4a_figures_follow.py::test_an_unreadable_figure_store_offers_no_figure_and_keeps_the_correspondents` | patched `FS.section_figures` to raise | the figure's stored report is made undecodable (`verification_report_json = '{not json'`), so the store's read raises inside `section_figures`; the test first checks the figure is offered. The two final assertions are unchanged |
| `test_sketch_service.py` (8 sites), `test_reader_rw5d_p4a_figures_follow.py` (1) | `FS._RECHECKED.clear()` | `FV._RECHECKED.clear()` (judgment call: not a patch but the "restart" the tests simulate, clearing the process memory of re-verified sketches; the alternative, a public reset function, adds production code for tests only) |
| 49 files | `FS.<moved name>` and `from ...service import` | the new home; no assertion changed |

Private names of the build that tests still use (they did not move; the file was renamed): `FB._RichSpawn.after_quick`
patched (2), `FB._author_context`, `FB._reusable`, `FB._request_row`, `FB._ungrounded_sketch` called. K10.9 rewrites
the author loop and owns those.

## 8. Vault

`_scripts/generate_all.py` once after the source commits (`15dda81d25`): six new module notes
(`Reference/Modules/learnloop/figures/{build,grounding,listing,predictions,request,view}.md`) and the notes that link
them (69 files). The generator leaves a note whose module is gone, and `module_validate.py` and `validate_vault.py`
then fail on `Reference/Modules/learnloop/figures/service.md` (source path missing, unreachable from Home); that note
is removed in the same commit. A second run on the clean tree changed nothing. The four validators pass:
`db_validate_reference`, `desktop_validate` (326/326), `module_validate`, `validate_vault` (2,226 notes, 2,224/2,224
reachable). No desktop file changed (no tsc or vitest run).

## 9. Lines per file

| File | Base | Tip |
|---|---:|---:|
| `figures/service.py` | 3,579 | 0 |
| `figures/build.py` | 0 | 1,538 |
| `figures/view.py` | 0 | 771 |
| `figures/request.py` | 0 | 473 |
| `figures/grounding.py` | 0 | 307 |
| `figures/listing.py` | 0 | 515 |
| `figures/predictions.py` | 0 | 154 |
| `figures/__init__.py` | 28 | 32 |
| `figures/prefetch.py` | 1,854 | 1,856 |
| `learnloop_sidecar/handlers/figures.py` | 1,540 | 1,544 |
| `figures/help.py`, `labels.py`, `learner_state.py`, `prefetch_ledger.py`, `sketch_verify.py`, `teacher/visuals.py`, the correspondents and lesson handlers | unchanged counts | (one-line edits) |

`service.py` after each commit: 3,579 -> 2,913 (view) -> 2,520 (request) -> 2,258 (grounding) -> 1,791 (listing) ->
1,663 (predictions) -> `build.py` 1,538 (the docstring: -142 + 17). The six modules hold 3,758 lines against 3,579:
+179, against the strategy's estimate of about +110 for K10.7 and K10.8 together (+50, +60). The new docstrings and
import blocks are most of it (the five new modules' docstrings and import blocks are 196 lines); the deleted stage history is -125 net.

## 10. Ledger

No bug found; no row added.

## 11. Open items and judgment calls

- Judgment calls: the view first (§2); `rebuild_request` stays with the build (§2); the membership calls of §3.1
  (`LEDGER_TASK`, `RECONSTRUCTION_REASON`, `_PREFETCH_BUILD`, `_figure_request`, `_prebuilt_pressed`, `_rich_line`,
  `_failed_correction`); `FV._RECHECKED.clear()` in tests (§7); module attributes read through `FB` in four tests (§4).
- Private names crossing module boundaries (§3.1): a later step can rename them public.
- `tests/goldens/structure.toml`'s members still name `service.py` until the next `--write` (no number fell here).
- Docstrings outside this step's files still name `figures.service`: `db/stores/figures.py:5` ("only writer is
  `learnloop.figures.service`"), `why/reconstructed.py:35`, and `diagnosis/text_gaps/sources.py:455` (K10.6's open
  item). Outside the lane (D7 edits `diagnosis/`); one-word fixes each.
- The strategy's K10.10 "attempt-host tier tuple beside `LESSON_TIERS` in `figures/request.py`": `LESSON_TIERS` is now
  there.

## 12. Not verified

- The targeted gate (§6) ran at the tip only; each commit ran the pins, the three goldens, `lint-imports`, `ruff` and
  the test files it touched or that import what it moved (330, 935, 626, 690, 500 and 1,010 tests, all passing), not
  the whole selection. `affected_tests.py` against the base answers "the full suite" (a deleted module), so the gate's
  selection is `affected_tests.py --files` over the 61 changed source and test paths (`service.py` left out: every
  file that imported it is in the list) with the figure test files by import and the rules block's fixed list.
- Nothing ran against a real vault, a real sandbox render or a real model. `arc_close` tests in the selection were
  left out (`-m "not arc_close"`).
- The ported `_prebuilt_pressed` test was not run against a deliberately broken source-check clause to show it fails;
  its new first assertion (the pre-build lists before the check) is what makes the last one non-vacuous.

## 13. Rules

- One scratch-script edit (the composer's separator) ran the system `python3` instead of the wrapper; it touched no
  `learnloop` code. Later scratch edits used the Edit tool.
- One status check used `pgrep -f generate_all`, which other sessions' (stale) wait loops also match; it decided
  nothing. The waits used the PID (`tail --pid`).
- Mechanical edits by script, each change printed and reviewed: the definition cutter (`move_defs.py`, K10.6's) and
  the composer for the five new modules; the import-block rewriter for `service.py`/`build.py`; `retarget.py` for
  every caller; the AST-position renamer (`FS` -> `FB` in four tests); `sed` for one-line docstring path changes,
  the IdentitySite paths and the never-evidence allowlist path.
