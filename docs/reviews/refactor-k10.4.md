# Refactor K10.4: pin the figure identities and golden the build

Branch `refactor/k10.4-figure-pins-goldens`, based on main `8c8f935684`. Step K10.4 of the figures chain,
specified in `docs/reviews/k10-figures-strategy-2026-11-14.md` §4.2. Tests only: no file under `src/` changed. No
pin or golden needed a source seam.

## 1. Commits

| Commit | What |
|---|---|
| `30cdbeeda8` | Ports (strategy T4): figure tests patch owners that do not move (§3) |
| `5901f55325` | Identity pins: five sites, 76 pins (§4) |
| `e0bf61ac13` | Build golden, 24 cases (§5) |
| `9bbbab465d` | Rich job golden, 13 cases (§6) |
| `54e72cc39c` | Build golden: a missed prediction and its explanation |
| `c4f3ed91a6` | Goldens: each case runs twice; only hashes with a minted id inside become tokens (§5.2) |
| `4b421eb5a1` | Build golden: five more author-loop exits that coverage found unreached |
| `f5ddb1a658` | Vault references regenerated (§9) |
| (this commit) | This record; ledger row K10-8 |

## 2. Coverage first

A scratch pytest plugin (`sys.monitoring` LINE events on `figures/service.py` and `figures/rich.py`, each location
disabled once seen; coverage.py is not a dev dependency) ran over the figure tests: the 81 test files that import a
figures module, a figure fixture or a figure RPC (2,413 tests, `-m "not arc_close"`). The report covers every
top-level function of the §4.3 groups K10.6-K10.9 move (protection, request, grounding, view, listing, predictions,
and the author loop `_author_attempts_and_store` with `_author_and_store`, `_step_three`, `_free_text`,
`_without_label_text`), plus `rich.py`'s protection functions K10.6 takes. Executable lines come from the compiled
code objects; `def` and decorator lines are left out.

| Group | Lines | Unreached at the base (existing tests) | Goldens alone | Existing tests + goldens (tip) |
|---|---:|---:|---:|---:|
| K10.6 protection (`service.py`) | 146 | 11 | 78 | 11 |
| K10.6 protection (`rich.py`) | 32 | 2 | 15 | 2 |
| K10.7 request | 184 | 14 | 67 | 14 |
| K10.7 grounding | 174 | 13 | 52 | 13 |
| K10.8 view | 376 | 20 | 130 | 20 |
| K10.8 listing | 273 | 22 | 151 | 22 |
| K10.8 predictions | 71 | 6 | 17 | 6 |
| K10.9 author loop | 304 | 42 | 42 | 15 |
| **All** | **1,560** | **130** | **552** | **103** |

The base's unreached author-loop lines told me which cases to add beyond the strategy's list: the second attempt
refused for the day's cap or an unavailable route, a model failure on both attempts, label text still there after the
repair, the sketch engine raising, a status off the menu with the sketch tier on, and under V3 a quick sketch, a quick
sketch failing in the engine, a quick spec failing numerics, a quick spec the source check finds different, and an
empty tier reason. The goldens-alone column is what P-golden itself pins: the predictions case was added because the
goldens reached none of that group.

**Still unreached at the tip, and why each is left** (line numbers at `8c8f935684`):

- Author loop (15): a quick sketch that does not parse or whose engine raises under V3 (2650-2655: the sketch-tier
  equivalents are reached; this branch needs both a rich tier and a broken quick sketch); the `IntegrityError` race
  where another process stored the same input first (2803-2807: needs two processes; no test has it); a
  configuration change landing during the source check (2486: a gate change between two checks); `_without_label_text`
  returning the answer unchanged (2462: the label rule and the strip disagreeing, which their shared vocabulary
  prevents) and its `SimpleNamespace` path (2465-2467: a non-pydantic answer; production answers are always models).
  All defensive; K10.9 moves them inside the loop it rewrites, and P-ast does not apply there, so K10.9's own
  literal-value tests of `_read_answer` are where they get cases (one per record code).
- Protection (13): the lineage read with no figure tables (698); a fuller version as an unrecorded occupant (741); a
  figure row gone (800); an inherited version with no record (729); an item whose passages cannot be read (3439-3441,
  fail closed); a lineage-less row (650); a figure with no home and no keys (609); and **a rich job whose saved
  context has a region or only a home** (`rich_base_keys` 3463, 3468; `rich._withheld` 428, 434): no test builds a
  rich job from a cropped region or from a show-me press with no passage. These move verbatim in K10.6 (P-ast); the
  region and home paths are the ones I would add first, with a show-me rich press fake (the grounding retrieval needs a
  `find` fake through `build_figure`).
- Request (14), grounding (13): refusal branches for switched-off features and malformed requests (`figures_disabled`,
  `prefetch_disabled`, `show_me_disabled`, unknown origin, a region without a box, an Ask figure without its item, a
  figure not on this source), and `except`/`continue` guards around unreadable context (a passage outside the
  extraction, a block that will not decode, ranking context that fails). Defensive; moved verbatim in K10.7.
- View (20), listing (22), predictions (6): parse-failure guards (`except (TypeError, ValueError)`), a not-from-books
  label on a rich or sketch figure with no grounding, a stored sketch that no longer runs at re-verification, rows
  skipped in listing loops, and refusals (`predictions_disabled`, an empty explanation, a gone prediction). Defensive;
  moved verbatim in K10.8.

## 3. Ports (strategy T4)

The strategy counts 18 sites over four names. Three of the names hold: `withheld_message` (7), `prefetch_plan_waits`
(4), `item_passages` (3). **`FS.search_spans` (4) is a miscount**: no test patches `search_spans` on
`figures.service`; the strategy's grep matched `tests/test_roles_switch_off_legacy_parity.py`, whose `FS` is
`source_retrieval.find_sources`. So 14 sites, plus three more on protection names K10.6 moves. Every assertion is
unchanged.

| Site | Was | Now |
|---|---|---|
| `test_figures_prefetch_review_fixes.py` `_held`, `_newer_snapshot_holds` | `FS.withheld_message` | `exam_material.spans_withheld` (same arguments; `withheld_message` and `keys_withheld` both reach it) |
| `test_followups_batch6_prefetch_plan_wait.py` (2 lines, one test) | `FS.withheld_message` | same |
| `test_followups_batch6_prefetch_decided_once.py` | `FS.withheld_message` | same |
| `test_figures_prefetch.py` | `FS.withheld_message` | same |
| `test_followups_batch6_prefetch_next_section.py` | `FS.withheld_message` | same |
| `test_figures_prefetch_review_fixes.py::test_r5_…held_out_passage…` | `FS.keys_withheld` (returned None for every other key) | `spans_withheld`, held for the key, the real predicate otherwise |
| `test_reader_rw5d_p4b_teacher_visuals.py::test_held_out_inputs_are_refused_before_any_call` | `FS.keys_withheld` | `spans_withheld`, held for the grounding keys |
| `…::test_a_shown_figure_held_out_since_is_no_longer_shown` | `FS.figure_withheld` → True | `spans_withheld` → held for every passage |
| `test_followups_batch6_prefetch_plan_wait.py::test_a_pass_retries_at_most_the_daily_build_cap` | `FS.prefetch_plan_waits` → a list of ids | `rich.rich_jobs` (the queue read below every check `prefetch_plan_waits` makes) answers copies of the real waiting prebuild under those ids, each its own input: `_queued_waits` in `tests/followups_batch6_prefetch_plan_wait_helpers.py` |
| `test_followups_batch6_review_fixes.py` (three F2 tests) | `FS.prefetch_plan_waits` | same helper |
| `test_figure_decision_records.py` (3 sites) | `FS.item_passages` | `prefetch.item_protection` (the pass's own reader of it, called by name inside `prefetch`), returning the same `ItemProtection` |

Judgment: the strategy names a public argument as the alternative for the plan-wait sites; `retry_plan_waits` has
none, so they patch the queue's read, which no figures step moves, and the copies go through the real admissibility
checks (switch, mains, held-out, item passages). The weakest of them,
`test_a_pass_retries_at_most_the_daily_build_cap`, would also pass with the patch ineffective (bound 1 and the real job
first), as it did before.

**Not ported, and why** (each fails loudly after its move, not silently): `FS.learner_state_withheld`
(`test_followups_nov2_figure_provenance.py:431`, K10.6) and `FS.section_figures`
(`test_reader_rw5d_p4a_figures_follow.py:159`, K10.8): after the move the name is either gone from `service`
(`monkeypatch.setattr` raises) or patched where nothing calls it, and both tests then fail their assertion. The moving
step ports them (the owner below `learner_state_withheld` is `learner_state.inputs_withheld`, which the lesson figure
reaches only when its author was sent a state). `FS.build_prefetch_figure` (`test_figure_decision_records.py:261`)
and `FS._RichSpawn.after_quick` (2) stay with the build; `FS._prebuilt_pressed` (`test_rw5c_recheck.py:302`) is a
private name K10.8 ports under T4; `FS.RICH.tiers_allowed` patches `rich`.

## 4. Identity pins

`tests/identity_pins_helpers.py`, five sites, 76 pins, all through production functions at fixed inputs (a passage,
the paragraphs around it, a crop digest, a region, a goal, a learner state, a Manim runtime string, written out in the
helper). `uv run python tests/test_identity_pins.py --write` in the commit that adds them: `identities.toml` gains 76
lines and loses none (`git diff` is additions only); `identity_shapes.toml` is unchanged.

| Site | Production path | Pins |
|---|---|---|
| K10.4a | `service.request_hash` (`learner_state.state_hash`, `_recorded_input_key`) | 19: plain; panels; sketch; panels + sketch; the rich menu (with and without sketch); region and crop; a revision; a different kind; a rebuild's check row; show me anchored, retrieved, none, a tutor's goal; a learner state and its recorded-inputs twin; the five alternates `_build` looks up (assembled as `_build` does inline, the tuples copied), with and without their recorded twins; the `FigureRequest` fields the key reads with their defaults |
| K10.4b | `_build`'s request identity, `content_key({input_hash, generation})` (inline) | generation 0 and 1 |
| K10.4c | `routes.author_prompt_version`; `rich.RICH_PROMPT_VERSION` | all 48 combinations (panels × show me × sketch × menu none/default/without sketch × learner) and the rich version |
| K10.4d | `routes.output_model` → `model_json_schema()` | V1, V2, V3 and `FigureManimOutputV1` |
| K10.4e | `rich.rich_build_key` | the init config, and with a price and cap set |

**Shape pins.** No figure identity dumps a type whole: `request_hash` names its fields (K0's A21 class), so a renamed
field raises in the pins. The strategy's "shape pins for `FigureRequest` fields read by the key" is the
`K10.4a.request_fields` pin (the fields `request_hash` reads and their defaults: a request built without one hashes its
default). The region, the passages and the learner state are plain dicts; their bytes are pinned by the values in the
matrix, and by the literal `input_hash` of every build golden case (the real vault's context). Judgment: I did not add
`FigureRequest` to `SHAPE_ROOTS`, which is for types dumped whole; adding it would fail every harmless field addition.

`js_animation` is left out of the menus on purpose: it is unreachable, and K10.17 removes it.

## 5. The build golden

`tests/test_figure_build_golden.py` with `tests/figure_build_golden_helpers.py`; fixture
`tests/fixtures/figure_build_golden.json` (1.35 MB), written only with `FIGURE_BUILD_WRITE_GOLDEN=1`. 30 cases, each
a fresh vault, pressed through the sidecar's RPCs (`reader.figure_request`, `reader.figure_revise`,
`reader.figures`, `figure.request` and `figure.open` for the attempt host, `reader.figure_predict` and
`reader.figure_explain`, `deliver_figure`) or the lesson's builder.

Each case records: the author's prompts in order; what the source check sent its sandbox (each call's definitions,
candidates, elements and the payload's sha256; the grids are large); every row added, changed or removed in
`figure_requests`, `interactive_figures`, `judgment_ledger`, `figure_source_checks`, `help_assists`, `reveal_events`,
`ingest_jobs`, `decision_records`, `model_call_receipts` (the receipts show the gate's order), `figure_predictions` and
`learner_text_gap_jobs`, in write (`rowid`) order; the press's result; and the list after it (read first, so a list
that writes is caught too).

**Cases.** The strategy's fifteen: `grammar_accepted`, `grammar_failed_twice`, `label_text_repaired`,
`prediction_dropped`, `sketch_accepted`, `sketch_fails_in_the_engine`, `v3_manim_with_a_quick_spec`, `v3_manim_only`,
`unsupported`, `source_check_differs_then_passes`, `reuse_under_another_setting` (built, then pressed under the
sketch tier's setting: reused with no call), `revision`, `attempt_host` (its help row and reveal), `lesson_visual` (its
status), `delivery_withheld`. Fifteen more: `grammar_refused_then_accepted`, `model_failed_twice`,
`capped_before_the_second_attempt`, `route_unavailable_for_the_second_attempt`, `label_text_stripped`,
`sketch_engine_raises_then_accepted`, `sketch_tier_status_off_the_menu`, `spec_with_the_sketch_tier_on`,
`v3_quick_sketch`, `v3_quick_sketch_fails_in_the_engine`, `v3_quick_spec_dropped`,
`v3_quick_spec_differs_from_the_book`, `v3_tier_reason_missing_then_given`, `v3_spec_chosen`,
`prediction_missed_and_explained`.

**Fakes only.** `AuthorFake` (and two small subclasses in the test for answers it cannot shape: a V3 quick sketch, an
off-menu status); the source check's sandbox is `FixedSandbox` (patched at `pf_sandbox.run_sandboxed_python` and
`sandbox_available`): each call answers every pair with the next verdict, controls refused, display agreeing. No
process runs. The sealed sketch engine runs in process, as in the other figure tests. The engine-raises case patches
`sketch_verify.verify_sketch` to raise once. The capped and unavailable cases raise from the fake inside the request,
so they also leave a receipt for the refused second request (in production the envelope refuses before sending).

### 5.1 Tokens, and why a move cannot hide behind them

The normalizer walks a case's record in one order: the parts as the test names them (prompts first, the list last);
mapping keys sorted; lists in their own order (rows by `rowid`).

- A ULID (either case, alone or after a prefix: `fig_`, `frq_`, `les_`) or a random UUID becomes `<id:N>`, numbered by
  first appearance in that walk. The same id is the same token everywhere, so which row names which (a request's
  figure, a judgment's `left_id`, a record's subject and trace) is kept: a write naming a different row, or rows
  written in another order, changes the tokens.
- A timestamp within three days of the real clock becomes `<wall>`. Every `SystemClock().now()` returns a frozen
  instant (2026-10-12T09:00:00Z), so times written through the clock stay literal; only modules that read
  `datetime.now` themselves (decision records' `created_at`, receipts' `started_at`/`finished_at`) are `<wall>`.
- `duration_ms` and kin become `<ms>`; `error_where`'s line number becomes `<line>` (the raising frames are the fakes'
  in `tests/`).

Nothing else is replaced. Every content hash, reuse key (`input_hash`), request identity and prompt is literal.

### 5.2 Each case runs twice

A revision's reuse key names the figure it supersedes, and a rich job's owner names a hash of its payload, so a few
hashes carry a minted id. With one shared id sequence those hashes moved with whatever else minted ids in the process
(the revision case failed under the coverage plugin's different test order). So `recorded_twice` runs each case
twice, each in its own `MonkeyPatch` scope, with the case thread's ULIDs drawn from two different fixed sequences
(`freeze_ids` patches `ids._next_ulid` for the case's thread only; other threads mint as usual). After the tokens above,
the two records must be equal except for hashes that differ between the runs; only those become `<hash:N>` (four in
the build golden, all in the revision case; one in the rich job golden, the rich route's owner). Any other difference
fails the case as nondeterministic, which every run now checks.

Stability: compare runs passed at `-n 6` five times and serially under `PYTHONHASHSEED` 0, 1, 3 and 777, and under
the coverage plugin's test order.

**Runtime.** The build golden: about 45 s serial (30 cases × 2 runs, about 0.75 s each, mostly the vault), about 10 s
at `-n 6`. Marked `slow` (the file is over 15 s; each test is under 4 s); in the landing gate, not `arc_close`.

## 6. The rich job golden

`tests/test_figure_rich_job_golden.py`; fixture `tests/fixtures/figure_rich_job_golden.json` (0.38 MB), same switch
and helpers. Each case builds a quick figure through `figure_rich_job_helpers._Rig` (fake author, `RichAuthorFake`,
`Renders`, `InProcessRunner`), snapshots the rows, drains the ingest queue, and records the rich author's prompts, the
renders asked (scene class, the scene's sha256, the settings' names and quality: the wrapper names this machine's
`prlimit`), the function-runner sources' sha256, the rows the job wrote or changed, the job's status, error, phase and
attempt count, and the list.

Cases: `video_lands`; `claim_fails_on_the_first_attempt`; `render_fails_and_is_repaired`; and one per
`RichJobStopped` code: `figures_changed` (the switch goes off while the rich author answers; the next gate check
stops it), `rich_disabled` (opt-in withdrawn), `manim_unavailable`, `exam_material` (a neighbour held out),
`waiting_for_plan` (the plan's limit), `capped` (`SpendLimitExceeded` on the first request), `unpriced` (a metered
client, no price), `unrouted` (no injected client, `ai.routing.figure_rich_author = "manual"`), `not_isolated`,
`models_off` (no injected client under the suite's models-off environment). `test_every_stop_code_has_a_case` reads
the codes from `RichJobStopped`'s docstring. 17 s serial (measured), about 5 s at `-n 6`; marked `slow`.

## 7. Proof

Every pin and golden passes at the tip. Each scratch edit was written into `src/`, the four files
(`test_identity_pins`, both goldens, `test_figure_prompts_golden`) run, and the file restored byte for byte
(`git diff --quiet -- src/` after each). The runs were against the goldens of `c4f3ed91a6` (25 build cases, 13 rich
job cases), before the last five build cases were added:

| Scratch edit | Failed |
|---|---|
| `request_hash`: swap the values of `passage` and `around` | 58: 18 of 19 K10.4a pins (all but `request_fields`), both K10.4b pins, 24 of 25 build cases, all 13 rich job cases, the prompt golden. The build case left passing is `attempt_host`: a show-me press that retrieved nothing, so its passage and paragraphs are both empty and swapping them changes nothing |
| `author_prompt_version`: the sketch suffix before the show-me suffix | 14: the 12 K10.4c combinations with both, `K10.4a.show_me.tutor_goal`, and the build golden's `lesson_visual` (the one case with a goal and the sketch tier on) |
| `AUTHOR_INSTRUCTIONS`: "draws, never code" to "draws, and never code" | 26: all 25 build cases (each sends an author prompt) and the prompt golden; no pin (the version string is unchanged) |
| the quick row loses its `model` column (`_author_attempts_and_store`) | 19: exactly the build cases that store a quick grammar row (not the sketch rows, nor the V3 presses whose quick figure was dropped) |
| `RICH_INSTRUCTIONS`: one word added | 6: the rich job cases that send a rich prompt (the others stop before it) |
| the rich row loses `runtime_digest` | 3: the rich job cases that store a video row |

## 8. Gates

- Targeted: `scripts/affected_tests.py --base 8c8f935684` names 13 files (the ported ones, both goldens,
  `test_identity_pins`, `test_followups_batch6_verify_fixes`, `test_followups_batch7_prefetch_link_served`); with
  `test_retired_config_identities`, `test_architecture`, `test_test_layout`, `test_effective_defaults_golden`,
  `test_cli_help_snapshot`, `test_structure_ratchets`, `test_public_tip_guards`, `test_figure_prompts_golden`,
  `test_sketch_hostile`, `test_manim_sandbox_hostile`: 618 passed, 1 skipped, at `-n 6` under the 5 GB scope.
- The 81 figure test files plus both goldens (the coverage run at the tip): 2,457 passed, 2 skipped.
- `lint-imports --no-cache`: 42 kept, 0 broken. `ruff check`: clean.
- Vault validators and references: §9. `scripts/check_gate_partition.py`: 31,012 collected, landing 30,947 +
  arc_close 65.
- `test_structure_ratchets`: unchanged (no source change).

## 9. Vault

`_scripts/generate_all.py` once after the test commits: 43 generated notes changed (module and table notes that list
the tests reaching them, and the three generators' rows in `Reference/_generated.md`), committed as `f5ddb1a658`; a
second run on the clean tree changed nothing. `db_validate_reference.py`, `module_validate.py` and `validate_vault.py`
pass. **`desktop_validate.py` fails, not from this step:** its hard-coded inventory expects 324 TypeScript files
(`_scripts/desktop_validate.py:196`, set by C5) and the tree has 326, with matching activation and lifecycle drift.
This branch changes nothing under `apps/` or `Reference/Desktop/`, so main `8c8f935684` fails the same way (the first
run here stopped earlier, at the stale `_generated.md` row the regeneration fixed). Whichever step added the two TS
files owes the validator's count.

## 10. Ledger

K10-8 (new, queued): RW5a's "the book check comes in a later version" is still every reconstructed figure's verdict
reason and `figure_verified` rationale, beside a `checked` source check. Not learner-visible (the desktop shows a
reason only on a failed figure). Wording, with K10.10 or the UX audit; it moves the build golden's rows, not a pin.

## 11. Open items and judgment calls

- **The goldens are the base's.** They were recorded with no source change on the branch; K10.5-K10.9 must leave both
  fixtures and the 76 pins byte-identical. K10.11 (records) and K10.14 (view keys) change them on purpose and list the
  change.
- **A hash with a minted id inside** is a token (§5.2), so the revision's reuse key is pinned only by
  `K10.4a.revision` at a fixed input, not by the golden.
- **A move that changes a type's module path** moves no pin: the pins import public names (`request_hash`,
  `FigureRequest`, `SourceContext`, `Grounding`, `author_prompt_version`, `output_model`, `rich_build_key`) and the
  private `_recorded_input_key`; K10.6-K10.8 update those imports and the sites' `sources` paths
  (`test_every_registered_source_exists` fails until they do), as K2.5 did for B6.
- **Runtime.** Both goldens are marked `slow` (45 s and 18 s serial). They are explicit files in every K10 step's
  targeted set, so `-m "not slow"` iterations miss them only if a step forgets to name them.
- **The sandbox stand-in.** `FixedSandbox` answers from a queue, not from sympy; the real harness's answers are pinned
  only by `test_rw5c_source_check.py` (with bubblewrap). The golden pins what the check asks (payload sha256) and what
  the build does with each answer.
- **Not verified:** the goldens on another machine (the numeric integration floats in prediction rows are this
  build's; I1's golden has the same exposure); the plan-wait port's copies against a real second waiting job.

## 12. A rule I broke

One targeted-gate command was launched from zsh with an unset array expanded in quotes, which gave pytest an empty
path argument: pytest collected the whole suite. It ran about ten minutes at `-n 6` inside the 5 GB scope (18% done)
and ended with SIGTERM (exit 143; I did not stop it). I removed its `.pytest_tmp/run-1697221-*`. My test wrapper now
refuses an empty argument and a command line with no `tests/` path, and gate lists are built in a bash script.
