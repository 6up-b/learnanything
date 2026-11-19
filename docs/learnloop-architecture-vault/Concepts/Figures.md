---
title: Figures
aliases:
  - Figures and explanation videos
  - Show me
status: active
doc_version: 1.0.0
implementation_version: mvp-0.60
last_reviewed: 2026-11-19
source_commit: e6314fc0df008db528d657cbf3f80fe8dedd0982
source_commit_timestamp: "2026-11-18T23:18:17-05:00"
source_paths:
  - src/learnloop/figures
  - src/learnloop/figure_admission.py
  - src/learnloop_sidecar/handlers/figures.py
  - src/learnloop_sidecar/prefetch_runtime.py
  - src/learnloop/teacher/visuals.py
  - src/learnloop/content/pipeline/jobs.py
  - src/learnloop/content/authoring/concept_animation.py
  - src/learnloop/db/stores/figures.py
  - src/learnloop/db/table_roles.py
  - src/learnloop/attempts/attempts.py
  - src/learnloop/substrate/rebuild_orchestrator.py
  - src/learnloop/config/schema.py
  - tests/identity_pins_helpers.py
  - apps/learnloop-tauri/src/screens/reader/figures
tags:
  - learnloop/concept
  - learnloop/reader
  - learnloop/ai
---

# Figures

“Show me” builds an illustration the learner can explore: change a parameter, predict a result, or watch an explanation video. It accepts a passage, a question, or both. Figures are help, never certification. A prediction is formative; the submitted attempt remains the assessment. The entry contract is `src/learnloop/figures/request.py` (`FigureRequest`, `check_request`); formative answers belong to `src/learnloop/figures/predictions.py` (`record_prediction`, `record_explanation`). See [[Reader Tutor and Teach-Back]] and [[Evidence and Measurement]].

The supported surfaces are the desktop Reader, its offers and tutor answers, attempt help panels, and teacher lessons. The product decision excludes figures on the phone and MCP. The desktop adapter owns the request and delivery in `src/learnloop_sidecar/handlers/figures.py` (`figure_request`, `_start`, `deliver_figure`); lessons use `src/learnloop/teacher/visuals.py` (`figure_request`, `build`).

## What the learner sees

Request progress and a stored figure's verification are separate. A job can finish with an unsupported or failed figure. The adapter's `src/learnloop_sidecar/handlers/library_ask.py` (`_job_payload`) supplies job state; `src/learnloop/figures/view.py` (`figure_view`, `_label`) supplies figure state and its code-owned words.

| State | Meaning and owner |
|---|---|
| Pending | A pressed quick build is running in memory. `src/learnloop_sidecar/handlers/figures.py` (`_start`) starts it; `apps/learnloop-tauri/src/screens/reader/figures/FigureInline.tsx` (`FigurePendingLine`) draws the pending line. |
| Illustration | A usable grammar figure, simulation, or video passed its applicable checks. It makes no whole-figure claim of matching the book. `src/learnloop/figures/view.py` (`figure_view`, `_label`, `shown_row`) also presents legacy `verified` rows as illustrations. |
| Unsupported | The author cannot express the request in an offered medium, or the stored tier/panels are unavailable now. `src/learnloop/figures/view.py` (`advanced_off_row`, `sketch_off_row`, `rich_off_row`, `_label`) withholds the spec/program and gives the reason. |
| Failed | Authoring or verification produced no usable figure; a source check that proves a stated definition different also suppresses it. `src/learnloop/figures/build.py` (`_author_attempts_and_store`) and `src/learnloop/figures/view.py` (`_source_rejected_row`) own those outcomes. |
| Withheld | A finished figure is protected now. `src/learnloop_sidecar/handlers/figures.py` (`deliver_figure`) returns `figure: null, withheld: true`; `apps/learnloop-tauri/src/screens/reader/figures/useFigures.ts` (`useFigures`, its `run`) leaves a failed line saying “that passage is held out”. |
| Cancelled | The quick job's cancel mark takes precedence over its result. `src/learnloop_sidecar/handlers/figures.py` (`reader_figure_job_cancel`) and `src/learnloop_sidecar/handlers/library_ask.py` (`_job_payload`) own it. |
| Video pending, waiting, failed, cancelled, ready | A rich job reports writing, checking, or rendering; it can wait for the plan, fail with a reason, or finish as a fuller version. `src/learnloop/figures/rich.py` (`job_state`, `PHASES`) and `src/learnloop/figures/view.py` (`fuller_state`) build these lines. |

## Tiers and the choice of medium

The server constructs the menu before the author chooses. The master switch defaults on; a missing figures section is treated as off by `src/learnloop/figure_admission.py` (`figures_enabled`). Configured defaults below come from `src/learnloop/config/schema.py` (`FiguresConfig`).

| Tier | What makes it | Availability by default |
|---|---|---|
| `grammar` | The author writes a declarative spec; trusted code evaluates and draws it. Plots, bars, linear maps and readouts can include advanced heat maps, fields, trajectories and iterates. `src/learnloop/figures/spec.py` (`InteractiveFigureSpecV1`, `parse_author_spec`, `evaluate_figure`). | Base tier whenever figures are enabled. Advanced panels have their own default-on switch. |
| `sketch` | The author writes a bounded simulation program that returns a display list and declared probes. `src/learnloop/figures/sketch.py` (`SketchProgramV1`, `parse_author_sketch`). | Switch on, but offered only when `src/learnloop/figures/sketch.py` (`sketch_ready`) also finds the sealed engine ready. |
| `manim` | A second author writes a narrated Python scene; a durable job verifies declared functions and renders a video. `src/learnloop/figures/rich.py` (`run_rich_job`, `_run`). | Rich switch on; actual availability requires a spawner, Linux, bubblewrap, Manim and standing opt-in. `manim_opt_in` defaults to unset, so this tier is not initially offered. `src/learnloop/figures/rich.py` (`manim_tier_ready`, `manim_runtime_state`). |
| `js_animation` | The declared rich tier for a JavaScript animation. No reachable builder accepts it: `src/learnloop/figures/rich.py` (`run_rich_job`) accepts only `manim`. | Dormant: `JS_ANIMATION_BUILD_FLAG = False` prevents every menu entry in `src/learnloop/figures/rich.py` (`tiers_allowed`). Removal is queued as K10.17. |

`src/learnloop/figures/build.py` (`_build`) combines runtime readiness with the available rich-job spawner. Without a rich entry, `src/learnloop/figures/routes.py` (`output_model`, `author_instructions`) uses V1 for grammar alone or V2 for grammar/sketch, preferring grammar and requesting `why_not_spec` for a sketch. With a rich entry it uses V3: the author chooses the best explanatory medium from a neutral menu with cost, latency and checkability, supplies `why_this_tier`, and may include a quick spec or sketch alongside its rich brief. `src/learnloop/figures/build.py` (`_author_attempts_and_store`, `_append_tier`) validates that choice and records `figure_tier` in the judgment ledger.

Attempts and lessons are quick-only. The adapter removes the rich spawner for attempts in `src/learnloop_sidecar/handlers/figures.py` (`_start`); `src/learnloop/figures/build.py` (`build_figure`) removes it for lessons, whose allowed tiers are `LESSON_TIERS` in `src/learnloop/figures/request.py`. An ordinary animation revision goes directly to its rich author with the previous program and note; “try a different kind” returns to tier choice (`src/learnloop/figures/build.py`, `_build`, `_rich_revision`, `revision_request`).

## One request, from words to a kept figure

### Request and grounding

`src/learnloop_sidecar/handlers/figures.py` (`figure_request`, `_request_figure`, `offered_spans`, `tutor_figure_goal`) derives the caller and validates host/offer references on the server. `src/learnloop/figures/request.py` (`check_request`, `_validated_request`, `_validated_prefetch`) normalizes the goal, selection, region and revision, enforces their switches and reserved origins, and checks protection before a job or model call. A request with no anchor normally keeps a reading position as its home; attempt and lesson figures can have no home. The home is a placement, never source text sent to the author.

`src/learnloop/figures/build.py` (`build_figure`) repeats the request check and installs one `FiguresGate` around grounding, reuse and authoring. `src/learnloop/figure_admission.py` (`FiguresGate.check`, `FiguresGate.admit`) compares the live vault/configuration before every physical model request, including retries, and at explicit build boundaries. `src/learnloop/figures/request.py` (`key_for`, `build_key`, `offer_build_key`, `show_me_build_key`) defines the relevant route, price, cap and switch dependencies. This admission key is separate from content identity.

`src/learnloop/figures/grounding.py` (`ground`) returns `anchor`, `retrieved`, or `none`. Without an anchor it uses fixed cited passages when supplied, otherwise verified retrieval through `source_retrieval.find_sources.find_sources_for_caller`, under the derived caller policy. It keeps at most three permitted passages. Retrieval failure or no verified match yields `none`: an illustration labelled “not from your books”, with source claims removed by `src/learnloop/figures/build.py` (`_ungrounded`, `_ungrounded_sketch`).

`src/learnloop/figures/grounding.py` (`source_context`, `passages_context`) reads the selected/retrieved text and up to two neighbouring blocks on either side, excluding exam neighbours. `crop_image` sends a figure block's crop or just the requested region. `src/learnloop/figures/build.py` (`_build`) refuses a region if its author route cannot read images. `_learner_state` optionally adds the learner's state on these topics through `src/learnloop/figures/learner_state.py` (`read_learner_state`), keeping the input manifest for later protection checks.

### Protection at each boundary

A figure may not expose exam or held-out source material, protected work behind an author's learner state, or an attempt item's own exercise/solution through reused help. Background builds also avoid passages of items being administered or held open by today's plan. These are distinct checks over distinct inputs; their owners are in `src/learnloop/figures/protection.py`, with attempt policy in the desktop adapter.

| Moment | Predicate and inputs |
|---|---|
| Request and kept grounding | `src/learnloop/figures/protection.py`: `withheld_message` delegates to `src/learnloop/content/sources/exam_material.py` (`spans_withheld`); `keys_withheld` groups keys by source. The request checks the anchor/region or home, fixed grounding and revision base; `ground` rechecks every kept passage. This covers all exam material, including an unmarked past paper, not just the Reader Ask's narrower held-out partition. |
| Stored figure delivery, listing, opening and predictions | `src/learnloop/figures/protection.py`: `row_withheld` covers every sent span, crop, retrieved key and home; `learner_state_withheld` walks `supersedes_id`/`fuller_of_id`, reports and rich intents. `figure_withheld` adds the missing-row and show-me-switch checks for delivery. Unrecorded learner-state dependencies with the marked prompt version are permanently withheld. |
| Rich job start | `src/learnloop/figures/protection.py`: `_withheld` checks its saved source context; `_learner_state_withheld` and `_inherited_withheld` check current and inherited learner-state inputs. `src/learnloop/figures/rich.py` (`run_rich_job`) checks them before sending. |
| Every rich request and store | `src/learnloop/figures/rich.py` (`run_rich_job`) installs the learner-state predicates as gate holds. A background job adds `src/learnloop/figures/protection.py` (`rich_base_item_protected`) over `rich_base_keys`, plus power, plan and foreground holds. |
| Background candidate filter | `src/learnloop/figures/prefetch.py` (`item_protection`, `protected`, `_filtered`) checks the whole author context and planned grounding. `src/learnloop/figures/protection.py` (`item_passages`, `stored_plan_open_items`) gathers live administrations and the stored plan's open items; an unreadable set stops prebuilding. |
| Attempt help | `src/learnloop_sidecar/handlers/figures.py` (`_attempt_host`, `_attempt_caller`, `_request_attempt_figure`, `_refuse_own_blocks`, `figure_open`) derives the current attempt and refuses cold checks without an allowed take step, rich figures, and stored figures made from the item's own blocks. `src/learnloop/figures/help.py` (`qualifying_figure`) applies the chooser's corresponding rule. |

Protection is asked again because the material or configuration can change while a build runs. Source-context protection at rich-job start and learner-state holds during its requests are separate mechanisms; the gate does not replace the delivery/read checks (`src/learnloop/figures/rich.py`, `run_rich_job`; `src/learnloop_sidecar/handlers/figures.py`, `deliver_figure`; `src/learnloop/figures/listing.py`, `_listed`, `shown_figure`). See [[Privacy and Trust Boundaries]].

### Authoring, compartments and verification

`src/learnloop/figures/build.py` (`_build`) hashes the complete author input, looks for a reusable drawable figure under current and alternate settings, and serializes identical in-process builds with `_building`. A reuse still records the request through `_reused`. A new build gets a stable request identity from the input hash and stored build generation. `src/learnloop/figures/routes.py` (`FigureRoute.problem`, `FigureRoute.ask`, `daily_envelope`) owns route readiness, isolated structured calls, the two-call limit, checkpoints and the shared daily author/rich-author spend envelope. Metered calls need a configured price.

The author loop currently lives in `src/learnloop/figures/build.py` (`_author_attempts_and_store`); parsing, retry decisions, verification and storage are still in that function. It makes at most two calls, tells the second the first's problems, validates the offered status and rich brief, and salvages malformed predictions separately. `src/learnloop/figures/labels.py` (`label_problems`, `strip_json`) reserves badge vocabulary for code: invalid label-like text prompts repair, then is stripped from quick figures. An unusable optional quick figure is dropped while its rich build continues.

| Boundary | What code checks |
|---|---|
| Declarative grammar | `src/learnloop/figures/spec.py` (`parse_author_spec`) restricts the schema and expression language; `src/learnloop/figures/verify.py` (`verify_numerics`, `check_claims`, `verified_assumptions`) checks finite values and declared properties on the parameter grid, drops undecidable predictions, and checks quoted text against supplied spans. Quote presence alone does not prove equation equality. |
| Sealed sketch | `src/learnloop/figures/sketch.py` (`parse_sketch`) validates program declarations; `src/learnloop/figures/sketch_verify.py` (`verify_sketch`) runs sampled settings, checks deterministic read digests, display/probe bindings and claims. `src/learnloop/figures/sketch_engine.py` (`SketchEngine`, `engine_ready`) runs digest-pinned QuickJS WebAssembly with deny-all WASI shims and work/memory/time limits. It has no clock, network, files, environment or external randomness. |
| Book equation check | `src/learnloop/figures/build.py` (`_step_three`) calls `src/learnloop/figures/source_check.py` (`check_figure`, `_check`) only for a grammar candidate that passed numerics. `read_candidates` uses `src/learnloop/figures/book_math.py` (`read_relation`); `_run_sandbox` sends the comparison harness to `src/learnloop/content/authoring/pf_sandbox.py` (`run_sandboxed_python`). Equality, controls and the displayed expression must agree before an element can carry a book label. No model decides this check. |

A proved difference in a stated source claim uses the repair call if available and otherwise withholds the figure at presentation. An unavailable or inconclusive source check certifies nothing and does not by itself fail the build (`src/learnloop/figures/build.py`, `_author_attempts_and_store`, `_step_three`; `src/learnloop/figures/view.py`, `source_rejected`). “Matches the book's equation (checked)” belongs only to a checked grammar element. The rest stays an illustration; sketch checks cover declared probes, and video checks do not inspect every frame (`src/learnloop/figures/labels.py`, `BOOK_CHECKED_LABEL`, `REST_ILLUSTRATION_LABEL`, `MANIM_NOT_COVERED`; `src/learnloop/figures/view.py`, `_source_check_view`). Figures themselves are never “checked”.

Before committing, `src/learnloop/figures/build.py` (`_author_attempts_and_store`, `_store_sketch`) asks the gate again. It stores the request, figure, verification/tier judgments and any source check in one repository transaction. A quick figure's report includes its rich intent in that commit; `after_quick` then enqueues it. `ensure_rich_job` and `resume_rich_intents` recover the commit-to-enqueue window without rebuilding the paid quick output.

### Presentation, listing and attempt help

`src/learnloop_sidecar/handlers/figures.py` (`deliver_figure`) checks protection on the stored row at delivery. `src/learnloop/figures/view.py` (`_presented_row`, `figure_view`, `redelivered_view`) computes the current presentation without rewriting the figure: legacy verification becomes illustrative, disabled tiers lose their programs, a changed sketch engine/verifier causes re-verification, source differences suppress content, and label-like text is removed. Re-verification appends a judgment (`sketch_rechecked`, `_record_reverification`).

`src/learnloop/figures/listing.py` (`_listed`, `list_figures`) chooses the newest drawable version of each chain, otherwise its newest shown/failed/unsupported candidate. It omits protected picks and unparsable specs. An unanchored figure appears at each recorded home; a fuller video stays with its quick figure. Unpressed prebuilds use a section cue budget. `section_figures` supplies corresponding-section links without running a new sketch verification; `shown_figure` is the guarded quick-figure reader for opens and predictions.

The desktop's trusted frame owns the badge and controls (`apps/learnloop-tauri/src/screens/reader/figures/FigureInline.tsx`, `FigureInline`, `frameBadge`). A sketch runs in an opaque-origin sandboxed iframe and worker with a private channel, network denied, validated messages and a watchdog (`apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchCompartment.ts`, `createSketchCompartment`; `apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchRunner.ts`, `workerRunner`, `withWatchdog`). The sealed engine returns data for trusted drawing. The shell adds a header-based refusal for LearnLoop commands (`apps/learnloop-tauri/src-tauri/src/frame_guard.rs`, `refusal_reason`, `refusal_on`); the opaque-origin frame and network policy remain the primary compartment boundary.

An open attempt records one hint-equivalent per figure chain per attempt and its applicable reveal in the same transaction; failed recording withholds delivery. Feedback after submission is free. An eligible cold check must first take the help-conversion step; exams and measured checks that allow no help are refused. These decisions remain in `src/learnloop_sidecar/handlers/figures.py` (`record_attempt_figure`, `figure_take_step`, `take_step_available`, `attempt_view`); the hint chooser uses `src/learnloop/figures/help.py` (`qualifying_figure`). See [[Attempt Processing]].

### Prefetch and predictions

Prefetch predicts whether an illustration will be opened, never whether the learner knows its topic. `src/learnloop/figures/prefetch.py` (`run_trigger`, `candidates`, `judge_section`, `judge_gap`) collects candidates from plan reading, the next section, explorable offers, planned lesson visuals and open gaps. The `figure_prefetch_judge` route supplies content judgments. `filter_candidates` removes protected and redundant work; `decide_and_log` recomputes the numeric model from stored rows through `src/learnloop/figures/prefetch_ledger.py` (`load_model`).

`src/learnloop/figures/prefetch_model.py` (`Model.decide`, `Model._draw`) makes one Thompson draw of expected saved learner minutes: opening probability times measured tier wait, minus expected foreground time lost to a plan pause. No measured wait means no build. Sixty-four further draws estimate propensity. `Model.digest` identifies the posterior; `src/learnloop/figures/prefetch.py` (`decide_and_log`, `_prebuild_records`) records the seed, draw order, values and model version. The current default uses `prefetch_decision_v2`, with pressed quick-call latency shrunk toward background measurements and foreground-only blocked minutes (`src/learnloop/figures/prefetch_ledger.py`, `pressed_waits_on`, `load_model`; `src/learnloop/figures/prefetch_model.py`, `wait_estimate`).

Only desktop-sidecar background work runs these passes (`src/learnloop_sidecar/prefetch_runtime.py`, `environment`, `runs_here`). Builds require mains power and subscription routes, yield to foreground work, and obey daily build/render caps; they never make metered offers (`src/learnloop/figures/power.py`, `background_hold`; `src/learnloop/figures/prefetch.py`, `decide_and_log`, `run_builds`; `src/learnloop/figures/rich.py`, `_prefetch_hold`). `close_horizons` records `opened`, `asked`, `neither` or `void` outcomes at each candidate's horizon. The next pass recomputes its model from that ledger; no posterior table is maintained.

Learner predictions are a separate feature. `src/learnloop/figures/view.py` (`figure_view`, `_sketch_view`) withholds the answer before submission. `src/learnloop/figures/predictions.py` (`record_prediction`) reopens a currently permitted figure, computes its grammar/sketch outcome in code, and records one answer per figure/prediction. A miss queues a formative learner-text reading; `record_explanation` adds the optional “what changed, and why?” once. These records do not become assessment evidence.

### Cancellation, restart and video traces

A pressed quick build is intentionally not a durable queue job. `src/learnloop_sidecar/handlers/figures.py` (`_jobs`, `_start`, `reader_figure_job_cancel`) uses in-memory `LibraryJobs` and passes its cancel predicate to `src/learnloop/figures/build.py` (`build_figure`, `_cancel_hold`). Cancellation stops subsequent physical requests and storage at the next gate check. A request already sent can finish and checkpoint; a build past its final check can still commit. After restart the learner presses again, and the stable identity recovers already-paid answers rather than retaining a pending press.

Rich video work is durable. `src/learnloop/figures/build.py` (`_RichSpawn`, `ensure_rich_job`) hands its brief and saved context to `src/learnloop/content/pipeline/jobs.py` (`IngestJobs.enqueue_figure_rich`). The queue row and `job_enqueued` decision record commit together. `handle_figure_rich` opens its own trace scope and calls `src/learnloop/db/stores/provenance.py` (`continue_job_trace`) before running the video, so its calls and gate refusal join the originating trace with the enqueue record as cause. See [[ADR-017 One decision record, one trace id, one entry point]].

`src/learnloop/figures/rich.py` (`run_rich_job`, `_run`, `_repair_render`) checks current permission/protection, writes at most two rich-author attempts, parses the scene and verifies declared functions. `src/learnloop/figures/manim_figure.py` (`check_claims`, `extract_functions`, `sandboxed_runner`) isolates those functions in the PF sandbox. Rendering uses `src/learnloop/content/authoring/concept_animation.py` (`validate_scene_code`, `lint_scene_pacing`, `render_scene`, `_sandboxed_command`, `capped_scope_prefix`): mandatory Linux bubblewrap, preferring a memory/CPU/task-capped systemd user scope and falling back to an address-space limit through `prlimit` when available. The wrapper can be empty if neither is available; prebuild niceness uses `nice`/`ionice` when present. `store_video_bytes` stores content-addressed media; `src/learnloop/figures/view.py` (`_manim_view`) sends video metadata and transcript, never scene code. `apps/learnloop-tauri/src-tauri/src/main.rs` (`serve_llmedia`) serves the video by content-addressed name with Range support.

`src/learnloop_sidecar/handlers/figures.py` (`figure_rich_cancel`) cancels the ingest job. `handle_figure_rich` passes `JobCancelled` into the rich runner; progress reports notice cancellation, including after a render, before storage. A model request already sent finishes. A plan-unavailable job can be requeued on later learner activity (`src/learnloop/figures/prefetch.py`, `retry_plan_waits`; `src/learnloop_sidecar/handlers/figures.py`, `retry_plan_wait`).

The trace answers which author calls ran and which quick attempts failed, plus prefetch choices, filters, build guards and gate refusals. `src/learnloop/figures/records.py` (`AuthorAttempts.write`, `prebuild_record`, `FilterLog.record`, `build_stop_record`) and `src/learnloop/refusal_records.py` (`figure_gate_record`) write those records; `src/learnloop/why/reader.py` (`answer`) reads them. Request-level refusals/reuses and excluded-tier reasons are not recorded as a complete request decision; rich attempts retain call receipts and the last failure rather than quick-author-style per-attempt problem records (`src/learnloop/figures/build.py`, `_reused`, `_author_and_store`; `src/learnloop/figures/rich.py`, `_run`, `_store`).

## Persistence, identity and replay

`src/learnloop/db/table_roles.py` (`TABLE_ROLES`, `TableRole`) is the authority for these roles. `src/learnloop/db/stores/figures.py` (`insert_request`, `insert_figure`, `insert_prediction`, `insert_source_check`) owns figure SQL; `src/learnloop/db/stores/figure_prefetch.py` (`insert_decisions`, `insert_pause`, `link_request`, `close_decision`) owns the prefetch ledger. See [[State and Persistence]] and [[Synthesis Identity and Caches]].

| Table | Role and purpose |
|---|---|
| `interactive_figures` | `WORKFLOW`: paid built versions, spec/program, source-input manifest, verification report, reuse hash, lineage and media reference. Kept across rebuilds. |
| `figure_requests` | `RAW_LEDGER`: words/goal author, anchor/home, host and derived policy, grounding manifest, linked figure set once. |
| `figure_predictions` | `RAW_LEDGER`: formative learner answer and observed outcome; optional explanation set once. |
| `figure_source_checks` | `RAW_LEDGER`: append-only code checks with certification/harness/reader versions and element labels. |
| `figure_prefetch_decisions`, `plan_usage_pauses` | `RAW_LEDGER`: decisions with propensities and set-once outcome/link fields; observed plan pauses for recomputing prefetch. |
| `judgment_ledger` | `RAW_LEDGER`: verification, tier and source-check verdicts. |
| `ingest_jobs`, `ingest_batches`, `ingest_job_dependencies` | `WORKFLOW`: durable rich execution, progress, retry and cancellation. |
| `model_work_checkpoints`, `model_call_receipts` | `WORKFLOW`, `RECEIPT`: recovery of paid output and physical-call provenance. |
| `decision_records` | `RECEIPT`: explanatory trace records; no replay authority. |
| `help_assists`, `reveal_events` | `RAW_LEDGER`: attempt assistance and reveal accounting, distinct from figure certification. |

No figure output is regenerated, cleared or replayed by a learner rebuild. The request/prediction/prebuild ledgers are not ability evidence, and the prefetch posterior is recomputed at decision time. Table-role preservation and replayer ownership are enforced in `src/learnloop/substrate/rebuild_orchestrator.py` (`validate_replayer_registry`, `derived_table_owners`). Paid-answer recovery, a new-engine sketch verification, a code-only source recheck and recalculating prefetch are separate operations (`src/learnloop/figures/build.py`, `_build`; `src/learnloop/figures/view.py`, `sketch_rechecked`; `src/learnloop/figures/source_check.py`, `recheck`; `src/learnloop/figures/prefetch_ledger.py`, `load_model`). The learner rebuild replays the submitted attempt with its recorded `hints_used` and `primed` values through `src/learnloop/attempts/attempts.py` (`replay_existing_attempt`); it does not re-derive assistance from today's figure or reveal state. See [[Attempt Processing]].

The pinned identities are registered in `tests/identity_pins_helpers.py` (`IDENTITY_SITES`, `_figure_reuse_keys`, `_figure_request_identity`, `_figure_prompt_versions`, `_figure_contract`, `_rich_contract`, `_rich_build_key`). Their names and consequences are:

| Pin | What moves it and why that matters |
|---|---|
| `K10.4a` — figure reuse key | `src/learnloop/figures/build.py` (`request_hash`, `_recorded_input_key`, `_build`) hashes spec/prompt versions, source text/context/crop, home extraction, selection/region, revision/base, goal/author/grounding, menu/runtime and nonempty learner-state hash. Source-check rebuild and different-kind markers also change it. Pins include alternate settings, recorded-input twins and request-field defaults. Changed bytes can make a later press pay again. The actual origin is normalized to a constant. |
| `K10.4b` — build request identity | `src/learnloop/figures/build.py` (`_build`) hashes `{input_hash, generation}`. A stored failure advances generation for a fresh retry; a crash before storing keeps the identity so paid answers recover. This identity differs from the minted `figure_requests.id`. |
| `K10.4c` — prompt versions | `src/learnloop/figures/routes.py` (`author_prompt_version`) combines panels, show-me, sketch, rich-menu and learner suffixes; `src/learnloop/figures/rich.py` (`RICH_PROMPT_VERSION`, `rich_prompt`) supplies the rich version. A version change changes reuse/checkpoint identity. |
| `K10.4d` — output contracts | `src/learnloop/figures/routes.py` (`output_model`, `FigureRoute.ask`) chooses V1/V2/V3; `src/learnloop/figures/rich.py` (`FigureManimOutputV1`) defines the rich schema. JSON schema bytes, including descriptions, affect paid checkpoint keys. |
| `K10.4e` — rich admission key | `src/learnloop/figures/rich.py` (`rich_build_key`) includes route, cap, price, switches and opt-in. Changing it stops a running job before its next request/store; this is admission identity, not the content reuse hash. |

## Switches

Each row names the predicate that decides the setting, including parent switches. Unless stated otherwise, the boolean defaults to true in `src/learnloop/config/schema.py` (`FiguresConfig`, `FiguresPrefetchConfig`, `TeacherConfig`). Several module-local names remain delegates: `src/learnloop/figures/rich.py` (`rich_tiers_switch`), `src/learnloop/figures/source_check.py` (`enabled`), `src/learnloop/figures/learner_state.py` (`enabled`), `src/learnloop/figures/help.py` (`enabled`) and `src/learnloop/figures/prefetch.py` (`enabled`); their implementation delegates to the predicates below.

| Setting | Single predicate and what it gates |
|---|---|
| `figures.enabled` | `src/learnloop/figure_admission.py` (`figures_enabled`): master feature and figure-derived requests. Missing section defaults off. |
| `figures.predictions_enabled` | `src/learnloop/figure_admission.py` (`predictions_enabled`): prediction presentation, answer and explanation recording. |
| `figures.region_enabled` | `src/learnloop/figure_admission.py` (`region_enabled`): region selection requests and cropped input. |
| `figures.revisions_enabled` | `src/learnloop/figure_admission.py` (`revisions_enabled`): “not right?” and source-difference rebuild requests. |
| `figures.advanced_panels_enabled` | `src/learnloop/figure_admission.py` (`advanced_panels_enabled`): advanced prompt panels and their current presentation. |
| `figures.offers_enabled` | `src/learnloop/figure_admission.py` (`offers_enabled`): library/tutor offers and their initial builds. |
| `figures.show_me_enabled` | `src/learnloop/figure_admission.py` (`show_me_enabled`): goals/unanchored requests and their views. |
| `figures.sketch_enabled` | `src/learnloop/figure_admission.py` (`sketch_enabled`): sketch permission; machine readiness is separately `src/learnloop/figures/sketch.py` (`sketch_ready`). |
| `figures.checked_labels_enabled` | `src/learnloop/figure_admission.py` (`checked_labels_enabled`): book checks, source-check reads and element labels. |
| `figures.rich_tiers_enabled` | `src/learnloop/figure_admission.py` (`rich_tiers_enabled`): rich menu, jobs and stored rich presentation. |
| `figures.author_learner_state` | `src/learnloop/figure_admission.py` (`author_learner_state_enabled`): whether the author is sent learner state. Empty state adds no prompt/key suffix. |
| `figures.help_kind_enabled` | `src/learnloop/figure_admission.py` (`help_kind_enabled`): figures as attempt help/chooser kind; requires show-me as well as the master switch. |
| `figures.prefetch_enabled` | `src/learnloop/figures/power.py` (`prefetch_switch`): background passes/builds and listing unpressed prebuilds; requires the master switch. |
| `figures.prefetch.pressed_waits` | `src/learnloop/figures/prefetch_ledger.py` (`pressed_waits_on`): chooses the pressed-wait successor model only at a supported algorithm tag; false uses `prefetch_decision_v1`. |
| `teacher.visuals` | `src/learnloop/figure_admission.py` (`teacher_visuals_enabled`): teacher switch alone. `src/learnloop/teacher/visuals.py` (`active`) also requires figures and show-me. |
| `figures.manim_opt_in` | `src/learnloop/figure_admission.py` (`manim_opt_in`): unset, `declined`, or `standing`, default unset. `src/learnloop/figures/rich.py` (`manim_tier_ready`) requires standing permission and runtime readiness. |

The eight content switches queued for retirement in K10.16 are predictions, region, revisions, advanced panels, offers, show-me, sketch and checked labels. They still operate as above. The master switch, rich/Manim permission, prefetch, help kind, author learner state and teacher visuals remain product controls. Alternate reuse reads remain until the owner's stored-version counts establish that they are unnecessary (`src/learnloop/figures/build.py`, `_build`, `_reusable`); the approved retirement and count requirement are in `docs/reviews/k10-figures-strategy-2026-11-14.md` §4.9. That decision does not retire `figures.prefetch.pressed_waits`.

For test/process isolation, `src/learnloop/figures/routes.py` (`models_off`) also reads `LEARNLOOP_FIGURE_MODELS=off`. `src/learnloop_sidecar/prefetch_runtime.py` (`runs_here`) reads `LEARNLOOP_FIGURE_PREFETCH=off` to suppress queued triggers unless its inline test seam is injected. These are process controls, separate from vault content switches.

## Known gaps

These unresolved rows are tracked in `docs/reviews/refactor-bug-ledger.md`.

| Ledger id | Current limit and code owner |
|---|---|
| K10-5 | The server and desktop word “not from books” differently. Compare `src/learnloop/figures/view.py` (`_label`) and `src/learnloop/figures/labels.py` (`NOT_FROM_BOOKS_LABEL`) with `apps/learnloop-tauri/src/screens/reader/figures/FigureInline.tsx` (`frameBadge`). Badge wording remains an owner decision. |
| K10-6 | Other ingest kinds lack the rich job's enqueue/trace pair, and rich requeue writes no new requeue record. `src/learnloop/content/pipeline/jobs.py` (`IngestJobs.enqueue_figure_rich`, `handle_figure_rich`, `IngestJobs.retry_figure_rich`) shows the implemented trace boundary and the remaining retry limit. |
| K10-7 | The Ask/practice hint panel uses a generic failure line when delivery is withheld. `apps/learnloop-tauri/src/components/askFigures.tsx` (`usePanelFigures`, its `land`) does not explain the held-out reason as the Reader does. |
| K10-8 | A reconstructed grammar figure still stores “the book check comes in a later version”, even when the same build writes a source check. `src/learnloop/figures/view.py` (`RECONSTRUCTION_REASON`, `shown_row`) and `src/learnloop/figures/build.py` (`_author_attempts_and_store`) own the stale reason. |

## Related notes

- [[AI Architecture]]
- [[Reader Tutor and Teach-Back]]
- [[State and Persistence]]
- [[Privacy and Trust Boundaries]]
- [[Debug a decision]]
