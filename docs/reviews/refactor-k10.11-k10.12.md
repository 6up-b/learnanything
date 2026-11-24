# Refactor K10.11 and K10.12: why a figure request went as it did, and every rich attempt

Branch `refactor/k10.11-figure-records`, cut from the K2.7 tip with its status commit (`debfa75492`). Implements
K10.11 and K10.12 of `k10-figures-strategy-2026-11-14.md` §4.5 (map findings F10O1, F10O2, F10O3, F10O5, F10O6;
ADR-017's open item for the rich jobs). Records only: nothing shown, refused or built changes; no prompt, config,
schema or persisted-meaning change; no model call; no kill switch.

**Storage and the playbook.** No migration: every new record is a row of the existing `decision_records` table
(migration 253), as the brief preferred, so 269 was not taken. Decision records are not persisted meaning: the
playbook governs "scoring, scheduling, projection, or admissibility semantics", and nothing in serving, replay or
scoring reads `decision_records` (B1's ruling for the table, `refactor-b1.md`); no successor tag.

## Judgment calls to read first

1. **Where a request is recorded.** One `figure_request` record per request: the build writes it when it ends
   (`figures/build.py` `build_figure`, so a press, a lesson's figure, a revision, a retry and a prebuild are all
   covered by one site), and the sidecar writes it only when the request path refuses the request before any build
   job (`learnloop_sidecar/handlers/figures.py` `_refusals_recorded`, around `reader.figure_request`,
   `figure.request` and `reader.figure_revise`). An error raised after the job started is the job's (a job that
   finishes before its first read raises its error from the start), so the sidecar skips it (a context variable
   set by `_start`); `test_why_didnt_show_me_work_names_the_refusal_and_the_menu` would see two records otherwise.
   `check_request` inside the build now runs inside the recorded block, so a direct caller's validation refusal is
   recorded too.
2. **The request's subject.** `figure:<id>` when a figure resulted (built or reused), so `why figure:<id>` shows the
   request beside the author's attempts; otherwise `figure_request:<request identity>` (the build's
   `content_key` of its input and generation, the id the author's records and receipts already carry) once the
   input is hashed, and none for a refusal before that. `figure_request` joined `provenance.SUBJECT_KINDS` (and the
   CLI's help), as B8 added `goal` and `lesson`.
3. **The gate's hold codes.** A hold returns prose, which a record can't keep. Each hold's reason now carries its
   code: `figure_admission.HoldReason` is a `str` with a `code` attribute, so `gate.changed`, the
   `FiguresChanged` message and the rich job's `BACKGROUND_HOLDS` membership test read exactly as before. Tagged
   where each reason is made: `power.background_hold` (`prefetch_off`, `power`, `foreground`), the build's
   prebuild and cancel holds (`plan`, `cancelled`), the rich job's (`plan`, `render_cap`, `learner_state`,
   `item_protection`). A plain-string hold is recorded `unclassified`. The strategy also names `exam material`
   as a hold code; no hold in the code returns exam material (the rich job and the build check it up front and
   raise), so the code set has none.
4. **The menu as a core.** `rich.tier_menu(MenuFacts)` is pure and returns the menu and a code per absent tier;
   `menu_facts` reads the facts in `manim_tier_ready`'s order, so the Manim probe runs only with a spawner, the
   rich tiers on and the standing opt-in, as before (a test over every combination checks both the menu and that
   it probes exactly when it did). With no spawner, the absent code is the host when one explains it (`lesson_host`,
   `attempt_host`), else `rich_off` or `no_spawner`; the host is consulted only then, so a caller passing a spawner
   with an attempt-hosted request keeps today's menu.
5. **Which reuse key matched.** `_reusable` returns the figure with its match (`this_setting`, `rich_only`,
   `other_setting`, `recorded_inputs_twin`, the last told apart by the recorded keys the build passes);
   `built_meanwhile` is the row a concurrent build stored while this one waited for the lock.
6. **One trace per build.** A build with no entry trace (a lesson's, the CLI's, the goldens') opens one, so its
   request, gate and author records share it; under an entry point's trace (a press, a job) it keeps that trace and
   its cause. This moves only trace tokens in the goldens.
7. **Withheld, once.** `figure_withheld` is written once per vault, figure and rule in a process (the Reader polls
   its list every few seconds while a video builds): at delivery, for a listed chain whose pick is withheld now
   (`listing._listed` appends the pick's id to an optional list; it still writes nothing itself), and for a
   listed figure whose spec no longer parses. The reason a pick is withheld (exam material, learner state, an
   item) is not split into codes: `row_withheld` answers with prose, and a code would need it to return one.
8. **Rich attempts' codes.** The strategy's list, plus `model_failed` (the call raised and a retry followed) and
   `request_refused` (a second request refused by the day's budget or an unavailable route), which the loop also
   ends attempts with. `brief_invalid` is the rich author's answer refused by `manim_figure.parse_figure` (its
   declared fields, title or narration), `scene_invalid` the scene refused by `validate_scene_code`.
   `render_timeout` is a render result with no exit code whose stderr says it timed out (the renderer's own
   timeout result). When the pacing repair comes back worse and the earlier scene renders, the last attempt keeps
   its own code and gains `fallback_rendered`. A job that stops before any attempt writes only its stop record.
9. **Records.py in K10.11's commit.** The rich builders (`KIND_RICH_AUTHOR`, `RICH_ATTEMPT_CODES`,
   `rich_stop_record`, `AuthorAttempts.kind` and its `job_id`) landed with K10.11's records module and are first
   used in K10.12's commit.

## What was built

| Step | Where | What |
|---|---|---|
| K10.11 | `figures/records.py` | `KIND_REQUEST`, `KIND_WITHHELD`, `request_record`, `withheld_record`, `write_withheld_once`, `REUSE_MATCHES` |
| K10.11 | `figures/rich.py` | `TIER_ABSENT_CODES`, `MenuFacts`, `tier_menu`, `menu_facts`; `tiers_allowed` over them |
| K10.11 | `figures/build.py` | `_RequestNote`, `_record_request`; `_reusable` names its match; the gate's subject once the request is identified |
| K10.11 | `figure_admission.py`, `refusal_records.py` | `HoldReason`, `hold_reason`, `HOLD_CODES`; the gate's `hold_code` and `subject`; `figure_gate_record(held=, subject=)` (bytes unchanged for a gate with neither) |
| K10.11 | `figures/power.py`, `build.py`, `rich.py` | each hold reason tagged with its code |
| K10.11 | `figures/listing.py`, sidecar `handlers/figures.py` | `figure_withheld` at delivery and in the list; request-path refusals recorded |
| K10.11 | `provenance.py`, `cli/app.py` | `figure_request` subject kind |
| K10.12 | `figures/rich.py`, `figures/jobs.py`, `figures/records.py` | `run_rich_job` wraps the job (`_rich_job`), notes each attempt, writes `figure_rich_author` and `figure_rich_stop`; the handler passes `job_id` |

## Proofs

**P-fail, one case per code** (`tests/test_figure_request_records.py`, 57 tests; `tests/test_figure_rich_attempt_records.py`,
12 tests): every absent-tier code (pure, over `MenuFacts`), every hold code (the hold that returns it; the
`cancelled` hold end to end through a build, `learner_state` end to end through a rich job, `item_protection`
through the hold `run_rich_job` composed), every reuse match, every withheld rule (each written once over repeated
polls), the request's outcomes (`built`, `reused`, `rich_job_started`, `rich_job_pending`), refusals in the build
(the six route codes, `figures_changed` with the gate's rule) and on the request path (`not_offered`,
`validation_error`, `cold_check`, `exam_material`, `figures_disabled`, a revision's `not_found`), and every rich
attempt code and stop (a stop survives the requeue that rewrites the job's error). The code sets are read from the
constants, so a new code fails its file's coverage test until a case stages it. The why case
(`tests/test_why_cases.py::test_why_didnt_show_me_work_names_the_refusal_and_the_menu`) answers "why didn't Show me
work?" from `why --json` alone, for a refusal in the build and one on the request path.

**P-golden** (scratch `golden_compare.py`: take the step's new rows out, renumber the walk's tokens, compare; trace
tokens left out, judgment call 6):

| Golden | Cases identical apart from new rows | New rows |
|---|---|---|
| `figure_build_golden.json` | 30 / 30 | 27 `figure_request` built, 1 reused, 4 `rich_job_started`; `figure_withheld`: the delivery case's `withheld_at_delivery` and the list read after it `pick_withheld` |
| `figure_rich_job_golden.json` | 15 / 15 | 1 `figure_withheld` (`stopped_exam_material`'s list); 11 `figure_rich_author` (4 accepted, 1 render_repaired, 1 claim_failed, 1 render_failed, 1 interrupted, 1 model_failed, 2 request_refused); 10 `figure_rich_stop` (one per stop case); `stopped_figures_changed`'s gate record now names its job |
| `figure_prompts_golden.json` | unchanged | none |

The build golden's `delivery_withheld` case now delivers the job's own result (ledger K10-10, below); its recorded
delivery is unchanged.

**P-pins.** `tests/test_identity_pins.py` passes unchanged.

**Bytes per week** (B6's method on a synthetic journey: the journey's rows re-inserted 400 times into a scratch
table with `decision_records`' DDL and indexes, the file size after `VACUUM`): a `figure_request` row is 807 bytes on
disk (383 bytes of columns), a `figure_withheld` row 640 (244). The rich rows were sized from the rich golden's rows
scaled to real ids: about 850 bytes for a `figure_rich_author` row and 600 for a `figure_rich_stop`. At an assumed
20 presses and 10 prebuilds a day, 3 videos a week of two attempts and five withheld figures, that is about
180 KB a week (30 requests × 807 B × 7 = 169 KB, plus about 9 KB for the rest), about 9 MB a year. The press counts are
assumptions: no owner vault was opened (the strategy's §8 says the same of K10.11's storage estimate).

## Findings

- **K10-10** (ledger, fixed here): the build golden's `delivery_withheld` case handed `deliver_figure` the RPC's
  camelCase result, so the delivery's withheld check asked about the id `""`, which fails closed; the case never
  exercised the check it is named for.
- The strategy's line numbers are from Nov 14; K10.6-K10.10 and K2.7 moved the code: the menu is in `figures/rich.py`
  (`tiers_allowed`), the request path in `figures/build.py` (`build_figure`, `_build`, `_reusable`), the listing's
  drops in `figures/listing.py` (`_listed`, `list_figures`), the gate's record in `refusal_records.py`
  (`figure_gate_record`), the rich job in `figures/rich.py` (`run_rich_job`, `_run`, `_repair_render`) and its
  handler in `figures/jobs.py`.

## Assertions changed

- `test_figure_decision_records.py::test_a_refused_build_leaves_a_refused_record`: the trace now holds the author's
  record and the request's; the test selects the author's (asserted as before) and asserts the request's.
- `test_figure_decision_records.py::test_records_that_cannot_be_built_or_written_change_no_decision_build_or_prompt`:
  the record kinds gain the two prebuilds' `figure_request` rows; `request_record` joins the builders made to raise.
- `reader_source_identity_guard_helpers._refused` ("nothing is written"): for the two figure-request RPCs, nothing is
  written but one `figure_request` record refusing with the mismatch code (asserted exactly); every other count
  must still be equal.
- `test_learner_data_relax_2.py`: a call of the private `_reusable` reads the figure from its new `(figure, match)`.
- `test_why_reader.py`: the subject-kind case gains `figure_request`.

## Commands and results

All through the scratch wrapper (isolated home, config and temp dir), tests memory-capped at 3 GB with `-n 1`, one
command at a time.

| Command | Result |
|---|---|
| `tests/test_figure_request_records.py` | 57 passed |
| `tests/test_figure_rich_attempt_records.py` | 12 passed |
| goldens rewritten (`FIGURE_BUILD_WRITE_GOLDEN=1`): build, rich job, prompts | 47 passed; compared as above |
| affected tests: `scripts/affected_tests.py --files <changed src>` listed 1,069 files; name filter: test files mentioning `learnloop.figures`, `figure_admission`, `FiguresGate`, `refusal_records`, `decision_records`, the sidecar's figure handler, the figure and rich fixtures, the why helpers or `SUBJECT_KINDS`, plus those importing a helper that names a figures module: 180 files, 5 chunks, `-m "not arc_close"`, at the tip | 1,206 passed; 619 passed; 1,390 passed, 4 skipped; 1,423 passed, 7 skipped; 413 passed, 7 skipped |
| (the same set after K10.11 alone, before the identity-guard helper's port) | 5 failures, all the "nothing is written" helper meeting the new refusal record; ported (above) and passing |
| `test_identity_pins.py`, `test_structure_ratchets.py`, `test_effective_defaults_golden.py`, `test_cli_help_snapshot.py`, `test_kill_switches.py`, `test_sqlite_file_copies.py` | 398 passed |
| `tests/test_test_layout.py` alone | 3 passed |
| `tests/test_architecture.py` alone | 18 passed |
| `ruff check` | All checks passed |
| `lint-imports --no-cache` | 52 kept, 0 broken |
| `scripts/check_gate_partition.py` | collected 33527: landing 33461 + arc_close 66 |
| `validate_vault.py` | passed (2,428 notes) |

Structure golden: `golden_json_lines` 295,944 -> 296,669, raised by hand in the two golden commits with the reasons
beside it; nothing else moved (`private_patch_sites` rose by 2 with the first version of the tests, which then
stopped patching private names).


## Not verified

- The whole suite, the durability lane and the arc-close gate (the landing runs them).
- Real press, prebuild and video counts for the storage estimate (synthetic).
- The vault's generated references (the landing regenerates them).

**Fix round (2026-11-23).** K-R9 and K-R13 through K-R18 repair rich attempt recovery, cancellation, request identity, validation refusals and withheld-poll retries. The additional decisions describe figure authoring and delivery. They leave “scoring, scheduling, projection, or admissibility semantics” intact.
