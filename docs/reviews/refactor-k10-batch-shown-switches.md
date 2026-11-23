# Refactor K10.10, K10.14 and K10.16: one presentation chain and one shown set; the desktop reads `shown` and the label code; the eight figure content switches retired

Branch `refactor/k10-batch-shown-switches`, based on main `0e6e9adbc8` (latest tag `mvp-0.67`, migration head 265).
Three figures steps from `docs/reviews/k10-figures-strategy-2026-11-14.md` (§4.4, §4.7, §4.9), in order, one commit
series each, one landing. K10.10 is structure. K10.14 adds two keys to every figure view (a deliberate golden change,
§2.3). K10.16 is structure for the default configuration (the owner answered Q1 yes on 2026-11-14): new builds' prompts,
prompt versions and reuse keys are byte for byte today's default, and every identity pin keeps its bytes. No algorithm
tag, no migration, no model call, no owner vault.

## Commits

| Commit | What |
|---|---|
| `6646149ed3` | K10.10: `section_figures` presents through the view's chain with re-verification off; `drawable_now` and `shown_figure` read the chain's `available_row`; the teacher's visuals read `store.SHOWN` |
| `d025ea2a6a` | K10.10: `ATTEMPT_HOST_TIERS` beside `LESSON_TIERS`; the build's lesson door and the sidecar's attempt-host doors read them |
| `9ec2ae475b` | K10.14: the view carries `shown` and `label_code`; the build, rich job and RW5c switch-off goldens gain exactly those two keys |
| `04f574ae62` | K10.14: the desktop reads `shown` and the label code; the Ask panel's second fuller drop goes |
| `2fd56de24a` | K10.16: the eight switches retired into `RETIRED_FIELDS`; their readers, off-paths and tests (§3) |
| (this commit) | This record; the Figures note for all three steps |

Net source lines (`git diff --shortstat`, `src/` only): K10.10 +62 −46; K10.14 +39 −17 (and the desktop +83 −65
across 21 files, 17 of them test fixtures); K10.16 +246 −513. Tests: K10.16 −1,846 +257 (three deleted files, the RW5c
predecessor golden among them).

## 1. K10.10: one presentation chain and one shown set

### 1.1 What changed

- **One chain.** `figures/view.py` gains `available_row` (the chain's step after `shown_row`: a tier or panel kind that
  is off, or that this machine can't run, shown as "can't draw this yet"). `_presented_row` takes `reverify` and passes
  it to `sketch_rechecked` as `run`. `section_figures` (`figures/listing.py`) now calls
  `_presented_row(vault, repository, pick, reverify=False)` instead of its copy of the chain minus one step.
- **`run=False`** is exactly what the copy did: nothing runs, nothing is written, and only a failure this process
  already found (`_RECHECKED`) is honoured. A remembered *passing* verdict leaves the stored row as it is, as before
  (the copy only skipped a failed one), so a section's label is still the stored report's. Opening the figure
  re-verifies it.
- **`drawable_now`** is `available_row(vault, row) is row`. Each off-row returns the same object when it does not
  apply, so the composite is the same object exactly when each step is: equal on every input.
- **`shown_figure`** reads `available_row` once and maps the step that fired to the same refusal as before
  (`sketch_disabled` for `SKETCH_OFF_KIND`, else `not_found`). `rich_off_row` cannot fire there (the spec-version check
  above it already refuses a rich row).
- **The shown set.** `teacher/visuals.py` (`build_step`, `lesson_view`) reads `db.stores.figures.SHOWN` instead of two
  literal `("verified", "illustrative")`; it imports it as `SHOWN_VERIFICATIONS` because the module's own `SHOWN` is the
  lesson step's status string.
- **Tier tuples.** `figures/request.py` has `ATTEMPT_HOST_TIERS = ("grammar", "sketch")` beside `LESSON_TIERS`. The doors
  read them through `rich.rich_on_menu`: `build_figure`'s lesson door (`lesson_hosted(request) and not
  rich_on_menu(LESSON_TIERS)`), the sidecar press's spawner (`_start`), and the attempt host's view, open and record
  doors (`attempt_view`, `_refuse_rich`, `record_attempt_figure`). The sidecar handler now imports `figures.rich` at the
  top (it already imported `figures.build`, which imports `rich`, so no new edge in the import graph).

### 1.2 Judgment calls

- **The rich worker's door keeps its own check.** `rich.attempt_hosted_job` (the worker's refusal of an attempt-hosted
  job) cannot import `request` (which imports `rich`). Moving `ATTEMPT_HOST_TIERS` into `protection` beside
  `ATTEMPT_HOST_REFS` would let it, but the constant is a tier policy, not protection; the strategy puts it in
  `request.py`. The constant's comment names the worker's door as the same rule.
- **The lesson handler's `spawn_rich=None`** (`learnloop_sidecar/handlers/lesson.py`) stays: `build_figure`'s door already
  enforces it from `LESSON_TIERS`, and its comment names the constant.

### 1.3 Proof

- No golden, pin or fixture moved at either commit. `tests/test_figure_build_golden.py` (its lesson case included) and
  `tests/test_identity_pins.py`: `387 passed`. The build golden has no section-figures case; `section_figures` is
  covered by `tests/test_reader_rw5d_p4a_figures_follow.py` (including `test_the_quiet_read_never_reverifies_an_outdated_sketch_or_writes`)
  and `tests/test_rw5c_recheck.py::test_section_figures_leave_a_rejected_figure_out`.
- New `tests/test_sketch_service.py::test_a_read_without_a_run_honours_only_a_failure_already_found`, with plain values
  and no vault: without a run nothing is verified and the row comes back unchanged; after a passing run it still comes
  back unchanged; after a failing run it comes back failed with its program withheld.
- Targeted set (the K10.10 files' tests): `503 passed in 131.11s`; then `95 passed in 42.33s`.

## 2. K10.14: the desktop reads `shown` and the label code from the server

### 2.1 The server

`figure_view` adds two keys from the presented row: `shown` (its verification in `store.SHOWN`) and `label_code`, a
closed code (`view.LABEL_CODES`: `illustrative`, `not_from_books`, `sketch`, `sketch_unchecked`,
`sketch_not_from_books`, `manim`, `manim_unchecked`, `manim_not_from_books`, `rich_off`, `engine_changed`,
`unsupported`, `failed`). `_label` is now written from `_label_code`, so the words and the code cannot drift; its output
is unchanged for every input (the two dynamic labels, `unsupported` and `failed`, keep their text). `rich_off` is the
code for "can't show this kind here". `redelivered_view` keeps the two keys with the others it refreshes.

### 2.2 The desktop

- `api/dto.ts`: `FigureViewDto` gains `shown: boolean` and `labelCode: FigureLabelCode` (the closed union).
- The literal copies read `figure.shown`: `FigureInline.tsx` (`FigureInline`), `useFigures.ts` (the finished job, and
  the followed figure's open, the map's fourth copy), `askFigures.tsx` (`land`).
- One `figureBadge(figure, withdrawn)` in `FigureInline.tsx` maps the code to the Reader's own words. It replaces the
  branch on the server's English label (`figure.label === RICH_FRAME.cantShow`) and the three per-tier badge
  functions' selection; `manimBadge` (`RichFigure.tsx`) and `sketchBadge` (`SketchFigure.tsx`) are deleted. The
  desktop-only facts stay on top: a sketch's checks stand only while its page run agrees (`checksStand`), and a grammar
  figure with code-owned labels shows `CheckedBadge`. Drawing the server's words instead (K10-5, the UX audit's call)
  is one line: `figureBadge` returns `figure.label`.
- The "needs …" detail line shows for `labelCode === "unsupported"` (it was `verification === "unsupported"` and the
  label not "can't show this kind here": the same set).
- The Ask panel's `quickOnly` goes: the server's attempt view already carries no fuller version (`attempt_view`,
  pinned by `tests/test_figures_help_codex_review.py`).
- Not changed: `frameBadge` stays for `AskRail.tsx` and `useFigures.ts`'s failed pending line (status-derived lines,
  not badges). `AskRail.tsx` is a Reader file the workbench worker owns; it is untouched.

### 2.3 The golden change (deliberate)

Every view gains `shown` and `label_code` (`labelCode` on the wire), nothing else. `git diff` of the three goldens shows
only added lines: `tests/fixtures/figure_build_golden.json` +104, `tests/fixtures/figure_rich_job_golden.json` +38
(written with `FIGURE_BUILD_WRITE_GOLDEN=1`), `tests/fixtures/rw5c_switch_off_golden.json` +6. The RW5c golden pins a
predecessor's views; the two keys were copied into its three views by a scratch script that first checked every other
key of each view equal (the file goes in K10.16 anyway, §3.4).

### 2.4 Proof

- New `tests/test_figure_view_label_codes.py`: each of the twelve codes from a literal row, the label following the code,
  and the desktop's `FigureLabelCode` union equal to `LABEL_CODES` (read from `dto.ts`).
- The figure test files (61, in two chunks): `675 passed in 326.54s`; `955 passed, 1 skipped in 194.35s`.
- Desktop: `npm run typecheck` clean; `npx vitest run --maxWorkers=2` over the figure, Ask panel, lesson, reader and
  practice tests that render figures: `Test Files 50 passed (50)`, `Tests 893 passed (893)`. Test fixtures gained
  `shown`/`labelCode` where they build a view (a failed or unsupported override says `shown: false` and its code);
  `SketchFigure.test.tsx`'s badge test now calls `figureBadge` with codes (one case added: a withdrawn check reads
  unchecked); the Ask panel's R1 test's server answer carries `fuller: null`, as the server sends it.

## 3. K10.16: the eight figure content switches retired

### 3.1 What was removed

- **Config.** `FiguresConfig` loses `predictions_enabled`, `region_enabled`, `revisions_enabled`,
  `advanced_panels_enabled`, `offers_enabled`, `show_me_enabled`, `sketch_enabled`, `checked_labels_enabled`, and
  becomes a `KeepsRetiredFields`. Each is a `RetiredField("FiguresConfig", …, bool, True, "K10.16")` in
  `config/retired.py`, in the same commit. Their rows leave `config/kill_switches.py` (`UNTAGGED_SWITCHES`) and
  `params/parameter_registry.py` (folded into `figures.enabled`'s rule). The docstring says the features are on wherever
  figures are.
- **Predicates.** The eight predicates leave `figure_admission.py`; `help_kind_enabled` asks `figures_enabled` (it asked
  `show_me_enabled`, now the same). Every reader asks `figures_enabled`, then the checks that sat under a
  `figures_enabled` guard already were deleted: `_validated_request`'s offers, show-me, region and revision refusals;
  `check_request`'s show-me and panels refusals of a revision's base; the sidecar's show-me and offers refusals in
  `_request_figure` (under `_require`); `_listed`'s and `rich_pending`'s show-me filters.
- **The admission keys.** `build_key` drops its three switch members; `offer_build_key` and `show_me_build_key` go (each
  was `build_key` plus a switch); `key_for` returns `build_key` for every request but the pre-build, lesson and
  attempt-host ones, which keep their own switch. `source_check.recheck_key` drops its duplicate. Admission only:
  compared within one build, never stored.
- **The view's switch-dependent shape.** The show-me keys (`goal_text`, `goal_author`, `grounding`, `passages`) are always
  present; predictions are always read; `source_check.rebuild` is `True` (it was `revisions_enabled`).
- **The off-rows.** `advanced_off_row` and `ADVANCED_OFF_KIND` go; `available_row` is `rich_off_row(sketch_off_row(row))`.
- **The contract.** `prompt_contract_fields` sends `predictions`, `region`, `revisions`, `offers` and `show_me` as
  constant `True` (no conditionals).
- **The CLI and the report.** `learnloop reader report` passes `figures.enabled` for the offers, show-me and sketch
  blocks and adds the source-check block with figures on.
- **Docs.** The schema docstring, the disclosures text (no switch names), module docstrings, `dto.ts`'s comments, the
  Figures note.
- **Effective defaults.** `tests/goldens/effective_defaults.toml` loses exactly the eight lines (written with the test's
  `--write`).

### 3.2 What stayed, and why (deviations from the strategy's list, each with its reason)

- **The V1 and V2 output contracts stay.** The strategy lists them as off-paths; they are not. V3 applies only with a
  rich tier on the menu, which needs `rich_tiers_enabled` (kept), the Manim opt-in and a runnable machine, and a
  spawner, which lessons and attempt hosts never have. Every build without a rich menu uses V2, and V1 where the sketch
  engine can't load.
- **`sketch_off_row` stays**, for the engine: `sketch_ready` is now `figures_enabled and engine_ready()`. Its kind and
  reason no longer name the retired key: `SKETCH_OFF_KIND` reads "a simulation (the sketch engine can't run here)", and
  the two `sketch_disabled` refusals say the engine can't run here. Learner-visible only on a machine without the
  engine.
- **The prompt version.** The build passes `advanced = True` (a constant, with a comment): every new build is prompted
  and keyed under `ADVANCED_PROMPT_VERSION`, byte for byte today's default. `routes.author_prompt_version`,
  `author_instructions` and `author_prompt` keep their `advanced` parameter, because the reuse key's alternates (kept as
  the legacy reader the strategy names) compute the pre-panels version through it and K10.4's pins name both versions.
  The show-me suffix was never a switch (it marks a goal or no passage); the sketch suffix now follows the engine.
- **The reuse key's alternates** stay unchanged (the legacy reader), at `advanced = True`: the same list as today's
  default.
- **The desktop's contract keys** stay (constant `True`): removing them needs edits in `ReaderScreen.tsx`,
  `AskRail.tsx`, `intentPalette.ts` and `LibraryPane.tsx`, the Reader workbench worker's files. Their stale comments
  there are left for that worker.
- **The report's parameters** (`figure_offers_enabled`, `figure_show_me_enabled`, `figure_sketch_enabled`) stay; the CLI
  passes `figures.enabled` for each. Not in the strategy's list.
- **The tutor's explorable-without-show-me contract** (`tutor_show_me_enabled` is now `tutor_explorable_enabled`) is
  unreachable but stays: not in the strategy's list, and `reader_tutor.offers_enabled` still decides the tutor's pair.
- **`spec.parse_spec`'s `advanced=False`** and its "switched off (figures.advanced_panels_enabled)" problem text stay: the
  pure parser's option, reachable only from tests now; changing a problem string is a prompt-text change.

### 3.3 Proof

- **P-pins.** `tests/test_identity_pins.py` passes unchanged at every commit (no pin file differs from the base).
- **Retired fields keep the bytes.** `tests/test_retired_config_identities.py`: `23 passed`. Its hand-written
  `_pre_arc_c_shape` gains the eight fields at their defaults (as D7 added its switches). New
  `test_a_config_setting_the_retired_figure_switches_keeps_every_identity` (default, and a config setting all eight
  false) compares `content_key(identity_dump(config))` and the `figures` section's dump with digests recorded on a
  `git archive` extract of `04f574ae62` (the switches present); the same scratch script gave the same four digests on
  this tree. New `test_a_vault_that_still_sets_a_retired_figure_switch_loads_and_the_switch_reads_nothing`.
- **P-golden for the default configuration.** `tests/test_figure_build_golden.py`, `tests/test_figure_rich_job_golden.py`
  and `tests/test_figure_prompts_golden.py` pass with no change but one case (below).
- **The one golden case that changed:** `reuse_under_another_setting` toggled `figures.sketch_enabled` on the vault's
  file between two presses. That toggle never reached the second press (the sidecar context kept the vault it loaded),
  so the case recorded a plain reuse under the same setting. It now makes the sketch engine available instead, which
  reaches the build at once: the second press runs under the sketch tier's setting and is still reused, through the
  reuse key's alternate. Its record gains `tier`/`sketch` on the second view and the list's view, and the request row's
  `tiers_allowed` is `["grammar", "sketch"]`; no figure is written and no author call is made, as before.
- **Effective defaults** lose exactly eight lines; `tests/test_effective_defaults_golden.py`, `tests/test_kill_switches.py`,
  `tests/test_cli_help_snapshot.py` pass.

### 3.4 Tests changed

The figure tests ran with the sketch tier off by config (`build_figure_vault(sketch=False)`, the default, and the rw5c,
help and learner-state helpers). With no switch, "the tier unavailable" is now what a machine without the engine has:
`tests/figure_fixtures.py` gains `sketch_engine_absent()` (it patches `figures.sketch_engine.engine_ready` to answer
False for the rest of the test) and `end_sketch_engine_absence()`; `tests/conftest.py` undoes it after every test (an
autouse fixture that touches the figure helpers only when a test imported them). Those tests keep pinning the contract
with no sketch, which production still serves where the engine can't load.

Deleted, because the behaviour they pinned is gone (each tested a retired switch's off path):
`test_figure_offers.py` (`test_offers_off_the_contract_has_none_and_the_press_is_refused`,
`test_an_offered_build_stops_when_offers_are_switched_off_before_its_request`,
`test_a_selection_build_does_not_stop_for_the_offers_switch`,
`test_a_build_stops_when_the_advanced_panels_are_switched_off_mid_build`,
`test_with_the_panels_off_the_author_may_not_emit_them_and_stored_ones_are_cant_draw`);
`test_figure_predictions.py::test_predictions_switch_off`; `test_figure_region.py::test_region_switch_off_refuses_a_region`;
`test_figure_revisions.py::test_revisions_switch_off`; `test_figures_rw5b_review.py`
(`test_a_figure_that_cant_be_drawn_now_is_not_reused_across_the_switch`,
`test_a_figure_using_a_switched_off_panel_is_not_revised`,
`test_with_the_panels_off_a_chain_shows_its_newest_drawable_version`); `test_figures_show_me.py`
(`test_a_goal_alone_is_refused_while_show_me_is_off`, `test_show_me_off_lists_no_show_me_figure_and_the_view_is_rw5bs`);
`test_rw5c_recheck.py` (`test_a_recheck_with_the_switch_off_or_turned_off_before_its_write_writes_nothing`,
`test_rebuild_is_not_offered_with_revisions_off`, `test_a_kept_build_result_read_after_the_switch_turns_off_shows_no_label`);
`test_sketch_service.py::test_off_never_loads_the_engine`; `test_figure_switch_predicates.py`'s two tests of the retired
predicates. Whole files: `tests/test_rw5c_switch_off.py` with `tests/rw5c_golden_source.py` and
`tests/fixtures/rw5c_switch_off_golden.json` (the checked-labels predecessor's parity), and
`tests/figures_rw5b_review_helpers.py` (the panels flip).

Ported, the assertion kept (the switch it flipped replaced by one that still exists):
- to `figures.enabled` off: the organizer and tutor offer tests in `test_figure_offers.py` (four), the gate-key test
  (now: an offered build is admitted under `build_key` and stops when figures go off), `test_rw5c_source_check.py`'s
  three mid-build stops, `test_figures_show_me_codex_review.py`'s reuse refusal (and its flip matrix loses the show-me
  row), `test_figures_rw5b_review.py`'s ledger rationale, `test_rw5c_recheck.py`'s report block;
- to the engine: `test_sketch_service.py` (the no-sketch contract, a stored sketch listing as "can't draw this yet",
  switching the tier on reusing a grammar figure, the tier offered wherever the engine runs),
  `test_figures_switch_off.py::test_sketch_on_adds_only_its_flag`, `test_followups_nov2_figure_provenance.py`'s
  other-setting reuse (it flipped the panels);
- "stored before RW5c" (`test_rw5c_recheck.py`) is a build with `source_check.enabled` patched off for that build only;
- "stored before the panels" (`test_figures_rw5b_review.py`, two tests) is a build with `routes.author_prompt_version`
  patched to the plain version for that build only: the legacy reader still reuses it.

Assertions changed: `test_sketch_service.py`'s "can't draw this yet" label names `sketch engine`, not `sketch_enabled`
(the kind's wording, §3.2); `test_figure_switch_predicates.py`'s goal candidate is kept with figures on (two cases, was
three) and the teacher's visuals ask two switches (was three); `test_rw5c_source_check.py`'s build key reads index 1
(`figures_enabled`), and its `offer_build_key` line goes with the function;
`test_reader_rw5d_p4b_teacher_visuals.py` loses its show-me case; `test_figures_show_me.py`'s intent-box test loses
its show-me-off half; `test_figures_show_me.py::test_no_goal_no_button` (was
`…_and_show_me_off_is_rw5bs_tutor`) loses its off half.

### 3.5 Owner-copy counts to take

The legacy reuse reads stay until the owner's count shows no stored figure needs them (strategy, Summary). Run on the
owner's vault (agents don't open it):

```sql
SELECT prompt_version, tier, COUNT(*) FROM interactive_figures GROUP BY prompt_version, tier ORDER BY 3 DESC;
SELECT COUNT(*) FROM interactive_figures WHERE verification = 'verified';
```

A row whose `prompt_version` starts `figure_author.v1.1` (no `-panels`), or lacks `+sketch-v1` where a sketch-capable
machine would add it now, is one the alternates still find. If none, a later chore deletes the alternates (one re-paid
build per such input pressed again).

## 4. Commands (every run through the scratch wrapper, in a memory-capped scope, `-n 1`)

| Command | Result |
|---|---|
| `pytest tests/test_identity_pins.py` (base) | `357 passed` |
| K10.10: the figure goldens, follow, teacher visuals, rw5c recheck and switch-off, sketch service, pins | `503 passed in 131.11s` |
| K10.10: figures help (2), sketch service, structure ratchets, rich contract | `95 passed in 42.33s` |
| K10.10: pins + build golden after the commits | `387 passed in 56.66s` |
| K10.14: goldens written with `FIGURE_BUILD_WRITE_GOLDEN=1` | `46 passed`; diff: additions only |
| K10.14: the 61 figure-named affected files, two chunks | `675 passed in 326.54s`; `955 passed, 1 skipped in 194.35s` |
| K10.14: label codes + pins | `370 passed in 16.53s` |
| K10.14: `npm run typecheck` | clean |
| K10.14: `npx vitest run --maxWorkers=2` (figures, Ask panel, lesson, reader, practice) | `Test Files 50 passed (50)`, `Tests 893 passed (893)` |
| K10.16: `python tests/test_effective_defaults_golden.py --write` | eight lines removed, nothing else |
| K10.16: `tests/test_retired_config_identities.py` | `23 passed` |
| K10.16: affected files by name filter (figure, sketch, rw5, manim, visual, show_me, rich, switch, kill, identity_pins, retired, effective_defaults, cli_help, reader_tutor, tutor_offers, library_ask, organizer, reader_intent, disclos, parameter_registry, reader_report, config_) plus every edited test file: 91 files in chunks of at most 40 | `644 passed in 327.97s`; `844 passed, 5 skipped, 1 xfailed in 277.56s`; `347 passed in 119.23s` |
| K10.16: effective defaults, kill switches, learner blindness (2), learner data relax 2, mobile v4 review, reader rw1c review, source identity guard, sqlite file copies, structure ratchets, teacher te1 lesson | `452 passed in 81.87s` |
| K10.16: pins, the three figure goldens, CLI help snapshot, label codes (after the commit) | `443 passed in 132.29s` |
| `tests/test_test_layout.py` alone | `3 passed` |
| `tests/test_architecture.py` alone | `18 passed` |
| `ruff check` | `All checks passed!` |
| `lint-imports --no-cache` | `Contracts: 52 kept, 0 broken.` |
| `python scripts/check_gate_partition.py` | `collected 33238: landing 33172 + arc_close 66` |
| `npm run typecheck`; `npx vitest run --maxWorkers=2` (figures, Ask panel, lesson) after K10.16 | clean; `Test Files 22 passed (22)`, `Tests 624 passed (624)` |
| `cargo check --manifest-path src-tauri/Cargo.toml` | `Finished dev profile` |

`scripts/affected_tests.py` listed 613 files for the K10.10/K10.14 sources and 1,404 for the batch (the config schema
reaches nearly every test), hence the name filter above.

## 5. What I did not verify

- The desktop app and the Tauri shell were not launched; `cargo check` was run (§4).
- `tests/test_kill_switches.py`, `tests/test_cli_help_snapshot.py` and `tests/test_sqlite_file_copies.py` ran in the
  sets above; the vault validators were not run (the landing regenerates the references).
- The real sketch engine's absence on a machine without wasmtime: the tests patch `engine_ready`.
- The full suite and both gates (the landing runs them); I ran the figure-named and edited test files, chunked.
- Vault references were not regenerated (the landing does).
