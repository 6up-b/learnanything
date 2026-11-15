# Refactor K10.5 and K10.6: one name per switch; protection in one module, the package's cycle cut

Branch `refactor/k10.5-6-figure-switches-protection`, based on main `15075cca37`. Steps K10.5 and K10.6 of the figures
chain (`docs/reviews/k10-figures-strategy-2026-11-14.md` §4.3). Structure only: nothing a vault computes or a learner
sees changes. The figure goldens and the identity pins pass unchanged through every commit after the golden commit.

## 1. Commits

| Commit | What |
|---|---|
| `b9e9228972` | Rich job golden: the two cases K10.4 left for K10.6, recorded at the base before any move (§5) |
| `b562858238` | K10.5: one name per switch (§3) |
| `fb23c82624` | K10.6: the spec version lists (and the two version strings they name) move to `figures/spec.py` |
| `b5d9e58368` | K10.6: `routes.rich_text` takes the brief cap from the build |
| `66cad2da41` | K10.6: `figures/protection.py`; callers ask it; `rich._item_protected` merged; the one T4 port |
| `5b6b03683c` | Structure ratchet: modules in an import cycle 283 -> 279 |
| `e3bd54fc8e` | Vault references regenerated (§8) |
| (this commit) | This record |

The three K10.6 source commits cut the cycle's three edges one at a time; each passes the goldens and pins on its own.

## 2. Step 0

### 2.1 Who called each switch wrapper (at `b9e9228972`, the golden commit, before any move)

`service.py`'s own calls, then every caller outside it (AST sweep resolving `import … as` and function-local
imports over `src/`, `tests/` and `scripts/`; no test and no script called any of them):

| Wrapper (`figures/service.py`) | What it was | Callers outside `service.py` | Now asks |
|---|---|---|---|
| `enabled` | `figure_admission.figures_enabled` | `learnloop_sidecar/handlers/figures.py:107`, `:146`; `handlers/correspondents.py:90`; `teacher/visuals.py:67`; in `service.py` 4 calls (and one in `_switch`) | `figures_enabled` |
| `predictions_enabled`, `region_enabled`, `revisions_enabled` | `_switch(vault, name)`: `enabled(vault) and getattr(vault.config.figures, name, False)` | `handlers/figures.py:109` (both), `:110`; in `service.py` 4, 1 and 2 calls | the new `figure_admission` predicates of the same names |
| `advanced_enabled` | `advanced_panels_enabled` | none; in `service.py` 3 calls | `advanced_panels_enabled` |
| `figure_offers_enabled` | `offers_enabled` | `handlers/figures.py:111`, `:468`, `:477`; in `service.py` 1 | `offers_enabled` |
| `show_me_enabled` | `figure_admission.show_me_enabled` | `handlers/figures.py:113`, `:445`; `figures/help.py:416`; `teacher/visuals.py:67`; in `service.py` 10 | the same name, imported from `figure_admission` |
| `help_enabled` | `figure_admission.help_kind_enabled` | `handlers/figures.py:121`, `:198`, `:933`, `:1038`, `:1327`; in `service.py` 1 | `help_kind_enabled` |
| `sketch_switch` | `figure_admission.sketch_enabled` | none; in `service.py` 2 (`build_key`, `sketch_enabled`) | `sketch_enabled` |
| `rich_enabled` | `rich.rich_tiers_switch` = `figure_admission.rich_tiers_enabled` | `handlers/figures.py:125`, `:252`, `:740`, `:750`, `:806`, `:883`; `prefetch_runtime.py:111`; in `service.py` 11 | `rich_tiers_enabled` |
| `teacher_visuals_switch` | `teacher.visuals` (not under `figures.enabled`) | `teacher/visuals.py:67`; in `service.py` 2 | the new `figure_admission.teacher_visuals_enabled`, same body |
| `sketch_enabled` (not a wrapper) | the sketch switch and `engine_ready()` | `handlers/figures.py:117`; in `service.py` 5 | `sketch_engine.sketch_ready` |

**No wrapper's callers change behaviour**: each wrapper returned exactly its predicate. The three `_switch`
predicates and the new ones are equal on every vault (`figures_enabled(vault)` reads `getattr(vault, "config",
vault)` itself; the new predicates read the same attribute with the same default); they differ only on a bare
config passed in, where `_switch` raised `AttributeError` on `vault.config` and no caller passes one.

### 2.2 The raw config reads: unreachable with figures off

The strategy names two raw reads that skip the `figures.enabled` parent. There are three:

| Read | The path that reaches it | Why figures are on there |
|---|---|---|
| `figures/prefetch.py` `_filtered`: `vault.config.figures.show_me_enabled` | `filter_candidates` → `_filtered` | the line above in the same function returns `[]` unless `enabled(vault)` (`power.prefetch_switch`: `figures.enabled` and `figures.prefetch_enabled`), on the same `vault` object |
| `figures/prefetch.py` `_gap_candidates`: `env.vault.config.figures.show_me_enabled` (**not in the strategy**) | `candidates` → `_gap_candidates`; `candidates` has one caller in `src`, `_run_trigger`, and no test calls it | `_run_trigger` returns `status="off"` unless `enabled(env.vault)`, on the same object |
| `learnloop_sidecar/prefetch_runtime.py` `notify_offer`: `vault.config.figures.offers_enabled` | the offer hooks | the condition reads it only after `runs_here(ctx)`, which asks `prefetch_switch(ctx.vault)` |

On every input past those guards `figures.enabled` is true, so `show_me_enabled(vault)` (`figures_enabled(config) and
show_me_enabled`) and `offers_enabled(vault)` equal the raw reads. The one way they could differ is a vault reload
landing between the guard and the read in `notify_offer` (two reads of `ctx.vault` in one expression); the predicate
then answers for the reloaded vault with its parent, the raw read without it. `tests/test_figure_switch_predicates.py`
states the equality over the whole configuration matrix and the filter's behaviour with figures off (§6).

### 2.3 The pairs the map lists (§3.1's first table): equal on every input?

Compared by reading, at `b9e9228972`. A pair is merged only where the two give the same answer on every input; for
each pair that is not, one input where they differ.

| Question | Pair | Verdict | Where they differ |
|---|---|---|---|
| exam spans | `withheld_message(e, spans)` / `keys_withheld(keys)` | not equal | `keys_withheld` is `withheld_message` per source over `(extraction, span)` keys; with no span, `withheld_message(e, [])` still refuses a whole held-back reading (`covers(e)`), while `keys_withheld([])` asks nothing |
| exam spans | `row_withheld(row)` / `figure_withheld(id)` | not equal | `figure_withheld` also fails closed on a missing row and refuses a show-me figure while show me is off; `row_withheld` returns None for that row |
| exam spans | `rich._withheld(base)` / `keys_withheld(rich_base_keys(base))` | not equal | `_withheld` asks the passage's spans alone first, then every key grouped by source; the composition asks one source at a time with all its keys. Base spans clear, a retrieved key on another source X held back (unmarked) and a key on the base's source held out: `_withheld` answers X's refusal ("held back until marked"), the composition the base source's ("held out"): `held_out_refusal` words a source by its reasons. (A build's payload never has both passage spans and retrieved keys today, so the verdicts agree on every payload the build writes; the words do not on every input) |
| exam spans | `check_request`'s check, `ground`'s per-key recheck, the pre-build filter, `close_horizons`' void | compositions | each is a call of `withheld_message` or `keys_withheld` inside a larger function; nothing to merge |
| learner state | `rich.stored_learner_state_withheld(row)` / `rich.intent_learner_state_withheld(payload)` | not equal | different inputs: the row's report record against a payload's `author_context.learner_state` and `learner_state_inputs`; a payload with inputs but no state is None for the second, checked by the first |
| learner state | `service.learner_state_withheld(row)` / `rich.stored_learner_state_withheld(row)` | not equal | the first walks the lineage (`supersedes_id`, `fuller_of_id`), the intents and the unrecorded marker; a row whose earlier version keeps a protected state: the first refuses, the second answers None |
| learner state | `rich._learner_state_withheld(payload)` / `learner_state.inputs_withheld(inputs)` | not equal | the first wraps the reason in `LEARNER_STATE_PROTECTED` (different text) |
| learner state | `rich._inherited_withheld(payload)` / `service.inherited_learner_inputs(row)` | not equal | one checks a payload's list, the other collects a row lineage's records |
| learner state | `_learner_inputs_unrecorded`, `_unrecorded_occupant`, `_recorded_input_key` | different questions | a row predicate, a reuse-index read, a key |
| item passages | `service.item_passages` / `prefetch.item_protection` | not equal (a wrapper) | `item_protection` turns None into `ItemProtection(available=False)`; different return type over the one core |
| item passages | `prefetch.protected(candidate)` / `rich_base_item_protected(base)` | not equal | different inputs: a candidate's whole author context (re-read through `source_context`) against a saved payload's keys |
| item passages | `rich._item_protected(v, r, base, clock)` / `service.rich_base_item_protected(v, r, base, *, clock)` | **equal** | `_item_protected` is a one-line delegate, there only because the cycle made `rich` import it function-locally. Merged: deleted, and its two calls (`rich.run_rich_job`) call `rich_base_item_protected(..., clock=clock)` |
| item passages | `help.qualifying_figure`'s own blocks / the sidecar's `_refuse_own_blocks` | not item passages | an attempt item's own blocks through `item_exclusions`, a different rule (map §3.1); out of K10.6's scope |

## 3. K10.5: one name per switch

- `figure_admission.py` gains `predictions_enabled`, `region_enabled`, `revisions_enabled` (each under
  `figures.enabled`, written like the module's other predicates) and `teacher_visuals_enabled` (`teacher.visuals`,
  the teacher's switch alone, exactly as `teacher_visuals_switch` read it: not under `figures.enabled`).
- `service.py` loses `enabled`, `_switch`, the three `_switch` predicates, `advanced_enabled`,
  `figure_offers_enabled`, `show_me_enabled`, `help_enabled`, `sketch_switch`, `sketch_enabled`, `rich_enabled` and
  `teacher_visuals_switch` (80 lines). Its own calls were renamed by a script that rewrites only `ast.Name` loads at
  their AST positions (so `sketch_enabled` -> `sketch_ready` and `sketch_switch` -> `sketch_enabled` could not chain);
  the callers' `FS.<wrapper>` calls likewise (`scratchpad` script, listed in §11).
- **`sketch_ready` lives in `figures/sketch.py`, not `figures/sketch_engine.py`** (judgment call; the strategy says
  `sketch_engine.py`). With it in `sketch_engine.py`, `service.py` and the sidecar handler import that module at the
  top, and `tests/test_sketch_service.py::test_sidecar_start_imports_neither_wasmtime_nor_the_engine` fails: the
  sidecar must start without loading the sealed engine's module. `sketch.py` already loads at start (service imports
  it), so `sketch_ready` there keeps the engine import function-local, as `service.sketch_enabled` had it, and
  `sketch_engine.py` (frozen, strategy §4.6) is untouched.
- The three raw reads (§2.2) ask `show_me_enabled` / `offers_enabled`. `prefetch_runtime.environment`'s
  function-local import of `service` (used only for `rich_enabled`) goes.
- Not done, and why: `rich.rich_tiers_switch` (a one-line alias of `figure_admission.rich_tiers_enabled`, 6 callers
  in `rich.py`, one in `service.build_key`) and four module-local aliases of a switch (`help.enabled`,
  `prefetch.enabled`, `source_check.enabled`, `learner_state.enabled`) are second names the strategy's list does not
  name. Left as open items (§11) rather than widen the step; I removed `rich_tiers_switch` once and put it back.

## 4. K10.6: protection in one module, the cycle cut

**The cycle's three edges, one commit each:**

1. `prefetch_ledger -> service` (`ALL_SPEC_VERSIONS`): the version lists move to `spec.py`. `spec.py` cannot import
   `sketch.py` or `manim_figure.py` (both import it), so the two strings the lists name, `SKETCH_VERSION` and
   `MANIM_FIG_VERSION`, move there too, each with one home (judgment call: the strategy names only the tuples; the
   alternative, the tuples in `manim_figure.py` or a new module, puts a version list where nobody looks for it).
   Their readers read them there: `service` (`S.SKETCH_VERSION`, `S.MANIM_FIG_VERSION`, five sites, two of them in
   `request_hash`'s key: the values are unchanged and the K10.4a pins prove it), `rich` (4), `help` (1), two tests.
2. `routes -> rich` (`RICH_BRIEF_MAX`): `rich_text(brief_max)`; `author_instructions` and `author_prompt` take
   `rich_brief_max` and refuse a rich menu without it (`ValueError`); the build passes `RICH.RICH_BRIEF_MAX`. The cap
   stays where the parameter registry names its owner.
3. `rich -> service` (three protection functions): `figures/protection.py`.

**What `protection.py` holds** (538 lines; the module docstring with the table is 67 of them):

- from `service.py`: `ATTEMPT_HOST_REFS`, `withheld_message`, `_figure_spans`, `keys_withheld`, `row_withheld`,
  `learner_state_withheld`, `LEARNER_STATE_UNRECORDED`, `_rich_intent`, `_learner_inputs_unrecorded`, `_lineage`,
  `inherited_learner_inputs`, `figure_homes`, `show_me_row`, `figure_withheld`, `RICH_INTENT_KEY`,
  `LIVE_ADMINISTRATION_REASONS`, `stored_plan_open_items`, `item_passages`, `ITEM_PASSAGE_PROTECTED`,
  `rich_base_keys`, `rich_base_item_protected`;
- from `rich.py`: `_withheld`, `LEARNER_STATE_PROTECTED`, `LEARNER_STATE_INPUTS_KEY`, `_carries_learner_state`,
  `INHERITED_LEARNER_INPUTS_KEY`, `_inherits_learner_state`, `_inherited_withheld`, `stored_learner_state_withheld`,
  `intent_learner_state_withheld`, `_learner_state_withheld`; `rich._ATTEMPT_HOST_REFS` is deleted (the one constant
  has one home).

Judgment calls in the membership:
- **`stored_plan_open_items` and `LIVE_ADMINISTRATION_REASONS` move** though the strategy's table puts
  `stored_plan_open_items` under Listing (K10.8): `item_passages` calls it, and protection may not import service.
- **The constants the moved functions read move with them** (`RICH_INTENT_KEY`, `LEARNER_STATE_INPUTS_KEY`,
  `INHERITED_LEARNER_INPUTS_KEY`, `LEARNER_STATE_PROTECTED`): left in `rich`/`service`, protection would import back
  and close a new cycle. `LEARNER_STATE_OFF` stays in `rich` (only the job reads it).
- **Stays in `service.py`:** `_unrecorded_occupant`, `_recorded_input_key`, `LEARNER_INPUTS_RECORDED`,
  `_with_learner_inputs`: they compute the reuse key and the stored report (the build's), and
  `_recorded_input_key` is a K10.4 pin's production path, so the pin helper is untouched. They read
  `protection._learner_inputs_unrecorded`, imported by name: a private name crossing a module boundary, which I kept
  rather than rename a moved function (P-ast); renaming it public is a later step's one-line change.
- Moved names keep their names (privates included), so the moved bodies and every caller's body read the same;
  `rich` and `service` import the names they use from `protection`. Neither re-exports anything: every caller in
  `src` and `tests` asks `protection` (checked by a scan for `FS.<name>`, `RICH.<name>` and
  `from …service import <name>` naming a name the module only imports: none).
- **One merge:** `rich._item_protected` was a one-line delegate to `service.rich_base_item_protected` that existed
  only because the cycle forced a function-local import. Equal on every input (§2.3), so it goes; `run_rich_job`'s two
  calls call `rich_base_item_protected(..., clock=clock)`.
- `prefetch`'s seven function-local imports of protection names (`item_passages` through `service`, six of
  `withheld_message`/`keys_withheld`) become one top-level import (the strategy's "ten" counted the three that import
  the build's names, which stay).
- `_LOG` in `protection.py` is its own logger (`learnloop.figures.protection`): the two warnings `item_passages`
  logs now carry that logger name instead of `learnloop.figures.service`. No test or reader depends on it.

## 5. The two golden cases (before any move)

`tests/test_figure_rich_job_golden.py`, recorded at `15075cca37` + the test change only, with
`FIGURE_BUILD_WRITE_GOLDEN=1` and `-k` on the two cases, in their own commit; the fixture gains two entries and no
other line (checked: `git diff` of the fixture has no `-` line).

- `video_from_a_cropped_region`: a press with a region over the figure block `p4` (the crop patched as
  `tests/figure_region_helpers.crops` does, a route that reads images), whose quick answer asks for a video; the job
  lands.
- `video_from_a_show_me_press_with_only_a_home`: a show-me press with no passage whose retrieval finds nothing, so
  the saved context's only key is the home; the job lands.

Coverage (a scratch `sys.monitoring` plugin): both reach `rich._withheld`'s region line and home line (`rich.py:428`,
`:434` at the base), the two K10.4 named. `rich_base_keys`' region and home lines (`service.py:3463`, `:3468` at
K10.4's base) are still unreached by the goldens: `rich_base_keys` runs only for prebuild jobs and plan waits, and a
pressed job never asks it. It moved verbatim (P-ast); its existing direct test
(`test_followups_batch6_verify_fixes.py`) covers its passage path.

## 6. Tests

| File | Change | Why |
|---|---|---|
| `tests/test_figure_switch_predicates.py` (new) | a goal candidate kept only with figures and show me on (figures off: nothing, no record); over all 16 configurations of figures, prefetch, show me and offers, past the pass's guard the predicates equal the raw settings, and `runs_here` asks the same switch; the three moved feature switches sit under `figures.enabled`; `teacher.visuals` alone, and a lesson asks all three | the strategy's "by construction" test (§2.2). It passes at the base too (as the strategy says: it was true by context) |
| `tests/test_followups_nov2_figure_provenance.py::test_a_lesson_figure_keeps_its_record_and_is_rechecked_by_its_learner_inputs` | **T4 port.** It patched `FS.learner_state_withheld`, which after the move patches nothing. Now it patches the owners below that do not move: `learner_state.read_learner_state` (the lesson's author is sent a state) and, after the build, `learner_state.inputs_withheld` (what the state was read from is protected). Two assertions added: the row keeps the sent inputs, and `learner_state_withheld` refuses it | the lesson figure in this fixture was built with **no** learner state (the old patch never exercised the record); the port makes the test do what its name says. The final assertions (the figure withheld, the lesson's feed `WITHHELD`) are unchanged |
| `tests/test_figure_rich_contract.py` | the V3 instructions test passes `rich_brief_max`, checks the cap appears, and that a rich menu without it raises | the signature change (commit 3) |
| `tests/figure_rich_job_helpers.py`, `tests/test_figure_rich_job_golden.py` | `_Rig.build(find=)`, `RichCase(request=, find=, images=)`, two cases | §5 |
| `test_followups_nov2_figure_provenance.py`, `test_learner_data_relax_2.py`, `test_followups_batch6_verify_fixes.py`, `test_k1_source_sets_gate.py` | `FS.`/`RICH.` -> `FP.` (`protection`) for moved public names; unused `RICH` imports removed | public names moved (T4 governs private ones); no assertion changed |
| `test_reader_rw5d_p4a_figures_follow.py`, `test_figures_help_codex_review.py` | `K.SKETCH_VERSION` / `M.MANIM_FIG_VERSION` -> `spec` | the strings moved |

No other assertion changed. No test patches a moved private name.

## 7. Proofs

**P-ast.** A script (`past.py`, scratch) compares each moved definition at the commit before its move and at the
tip of that commit: `ast.dump` of the whole definition (decorators and docstring included), and the source lines
(comments and the `#:` lines above a constant included), after an explicit rewrite list applied to the base side.

| Commit | Definitions | Result | Rewrites applied |
|---|---|---|---|
| `fb23c82624` (versions) | `SPEC_VERSIONS`, `RICH_SPEC_VERSIONS`, `ALL_SPEC_VERSIONS`, `SKETCH_VERSION`, `MANIM_FIG_VERSION` | all equal (AST and text; `SKETCH_VERSION` gains the new three-line comment above it) | `S.SPEC_VERSION`, `K.SKETCH_VERSION`, `M.MANIM_FIG_VERSION` -> the bare names (now the same module) |
| `66cad2da41` (protection) | the 31 definitions of §4 | 30 equal in AST and text; `_withheld` equal in AST, its text one import line (and the blank after it) shorter | `RICH.stored_learner_state_withheld`, `RICH.intent_learner_state_withheld` -> bare (in `learner_state_withheld`); `RICH.LEARNER_STATE_INPUTS_KEY` -> bare (in `_learner_inputs_unrecorded`, `inherited_learner_inputs`); `_withheld`'s function-local `from learnloop.figures.service import keys_withheld, withheld_message` dropped |

No moved definition differs otherwise. The rewrites are the qualifier of a name that now lives in the same module and
an import the move made unnecessary: the class of the "import lines" the brief allows; I list them so the
orchestrator can judge.

**The rest of each changed file** (same script over every top-level definition not moved, base side mapped by the
listed renames): K10.5 changed exactly `prefetch._filtered`, `prefetch._gap_candidates`,
`prefetch_runtime.environment`, `prefetch_runtime.notify_offer`, `teacher.visuals.active`, the three `__all__` and the
two re-homed functions (`sketch_ready`, `teacher_visuals_enabled`); everything else in the nine files is equal after
the renames (185 + 130 + 331 definitions). The protection commit changed, beyond renamed calls: four function-local
imports in `service` (`_withheld` from `protection`, not `rich`), `rich.run_rich_job` (the merge), the local imports in
`help.qualifying_figure`, `cli.reader.figure_checks`, `teacher.visuals.lesson_view`, `hints._figure_deliverable`,
`prefetch.item_protection`, and two docstrings naming the old home. 496 other definitions equal.

**P-golden.** `tests/test_figure_build_golden.py` (30 cases) and `tests/test_figure_rich_job_golden.py` (15) pass at
every commit from `b562858238` on; neither fixture changed after `b9e9228972` (`git diff b9e9228972 -- tests/fixtures`
is empty). `tests/test_figure_prompts_golden.py` passes unchanged.

**P-pins.** `tests/test_identity_pins.py` passes at every commit; `tests/goldens/identities.toml` and
`identity_shapes.toml` unchanged; `tests/identity_pins_helpers.py` unchanged (`_recorded_input_key` and
`request_hash` stay in `service.py`).

**Structure ratchet** (`scripts/refactor_measures.py` at the base `15075cca37`, from a `git archive` export, and at the
tip): modules in an import cycle **283 -> 279** (the golden lowered with `--write` in `5b6b03683c`); largest component
186 -> 186; functions over 200 lines 73 -> 73; stage-comment lines 2,378 -> 2,378 (service 57 -> 52, rich 20 -> 18,
protection 7); function-local-only edges 2,776 -> 2,776. Nothing rose.

**Targeted gate, at `e3bd54fc8e`:** `scripts/affected_tests.py --base 15075cca37` (789 files: the sidecar handlers
reach most of the suite) with the 107 figure test files (by import: `learnloop.figures`, `figure_admission`,
`teacher.visuals`, the sidecar figure handler and runtime, the figure helpers), the new test, and
`test_identity_pins`, `test_retired_config_identities`, `test_architecture`, `test_test_layout`,
`test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_structure_ratchets`, `test_sketch_hostile`,
`test_manim_sandbox_hostile`, `test_public_tip_guards`, `test_figure_prompts_golden`: 808 files in 7 chunks at
`-n 4` behind the full-suite lock, `-m "not arc_close"`: **14,931 passed, 60 skipped, 6 xfailed, 0 failed.** Earlier,
after K10.5 alone, the 107 figure files ran whole: 2,654 passed and 1 failed, the sidecar-start import test that
moved `sketch_ready` out of `sketch_engine.py` (§3); it and its file pass since.

**lint-imports**: 42 kept, 0 broken (no contract lists `figures.service` or `figures.rich` by name, so none needed
the new module). **ruff**: clean.

## 8. Vault

`_scripts/generate_all.py` once after the source commits: 50 notes (49 changed, `Reference/Modules/learnloop/figures/protection.md`
new), committed as `e3bd54fc8e`; a second run on the clean tree changed nothing. The four validators pass
(`db_validate_reference`, `module_validate`, `desktop_validate`: 326/326, `validate_vault`: 2,222 notes).
`scripts/check_gate_partition.py`: 31,020 collected, landing 30,955 + arc_close 65. No desktop file changed (no tsc or
vitest run).

## 9. Lines per file

| File | Base | After K10.5 | Tip |
|---|---:|---:|---:|
| `figure_admission.py` | 476 | 515 | 515 |
| `figures/service.py` | 3,984 | 3,904 | 3,579 |
| `figures/rich.py` | 1,165 | 1,165 | 1,072 |
| `figures/protection.py` | 0 | 0 | 538 |
| `figures/spec.py` | 1,239 | 1,239 | 1,255 |
| `figures/sketch.py` | 910 | 926 | 924 |
| `figures/manim_figure.py` | 930 | 930 | 928 |
| `figures/routes.py` | 613 | 613 | 620 |
| `figures/prefetch.py` | 1,862 | 1,863 | 1,854 |
| `figures/prefetch_ledger.py` | 616 | 616 | 616 |
| `figures/help.py` | 461 | 461 | 463 |
| `teacher/visuals.py` | 375 | 375 | 376 |
| `cli/reader.py` | 220 | 220 | 220 |
| `learnloop_sidecar/handlers/figures.py` | 1,528 | 1,539 | 1,540 |
| `learnloop_sidecar/handlers/correspondents.py` | 435 | 436 | 436 |
| `learnloop_sidecar/handlers/hints.py` | 544 | 544 | 544 |
| `learnloop_sidecar/prefetch_runtime.py` | 202 | 201 | 201 |
| **All** | **15,560** | **15,547** | **15,681** |

K10.5 nets -13 (service -80; the predicates +39 in `figure_admission`, the rest imports). K10.6 nets +134 against the
strategy's estimate of +40: the module docstring with its table is 67 lines, the five section rules and the imports
of three modules most of the rest. `service.py` is 405 lines shorter.

## 10. Ledger

No bug found; no row added. The stale wording found is listed below, not a defect.

## 11. Open items and judgment calls

- Judgment calls (where to read the diff): `sketch_ready` in `sketch.py` (§3); the two version strings moved to
  `spec.py` (§4); `stored_plan_open_items` and four constants moved with protection; the four reuse-key helpers left
  in `service.py`; `_learner_inputs_unrecorded` imported across the boundary under its private name; the
  `_item_protected` merge; the T4 port that now gives the lesson's author a state (§6); the third raw read (§2.2).
- Second names for a switch outside the strategy's list: `rich.rich_tiers_switch`, `help.enabled`,
  `prefetch.enabled`, `source_check.enabled`, `learner_state.enabled`. Each is one line over a `figure_admission`
  predicate (or `power.prefetch_switch`); a later step can fold them as K10.5 did.
- Stale words kept byte for byte in moved docstrings (strategy §3 principle 6): `rich_base_keys` says "the spans
  ``rich._withheld`` checks"; `rich_base_item_protected`'s and `item_passages`' docstrings name their callers by
  module. Outside the step's files, `diagnosis/text_gaps/sources.py:455` still cites ``figures.service._figure_spans``
  (D7's lane edits `diagnosis/`; not touched).
- `protection.py` names the build's later modules nowhere; K10.7's `check_request` and K10.8's listing read it.

## 12. Not verified

- The targeted gate (§7) ran at `e3bd54fc8e` only; each intermediate commit ran the pins, both goldens, the prompt
  golden and the test files it touched (the protection commit also the 37 rich, prefetch, help, teacher-visual,
  source-check and batch-6 files: 1,384 passed), not the whole selection.
- Nothing ran against a real vault, a real sandbox or a real model; the logger-name change (§4) was checked only by
  grep.
- `arc_close` tests in the affected selection were left out (`-m "not arc_close"`); they are the arc-close gate's.

## 13. Rules

- Two scratch-file edits early on (a docstring count in a test and a table in the scratch header) ran the system
  `python3` instead of the wrapper; neither touched `learnloop`.
- One wait loop used `pgrep -f generate_all.py`, a pattern its own command line contained; it ended on the other
  condition. Later waits used the PID.
- Mechanical edits by script (exact patterns, each printed and reviewed): the AST-position renamer for the wrapper
  calls and the moved names' callers; the definition cutter (`move_defs.py`) and the composer for `protection.py`;
  `sed` for four identical import lines in `service.py`, the `sketch_ready` import line in two files, and four
  one-word docstring fixes.
