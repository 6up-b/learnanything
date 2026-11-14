# K10.1-K10.3: the three Show me figure bugs (behaviour track)

Branch `fix/k10-figure-bugs`, on the figures strategy branch (main `f623e525ac` plus the strategy documents, `212a0a6f6d`). One landing of three fix commits, each from a failing test, plus this record and the ledger rows. Strategy: `docs/reviews/k10-figures-strategy-2026-11-14.md` §4.1. Ledger rows K10-1, K10-2 and K10-3.

| Step | Commit | Ledger |
|---|---|---|
| K10.1 Cancel stops the build | `7f96c0a5c7` | K10-1 fixed |
| K10.2 The Reader says when a figure is withheld | `ffc1cd94c5` | K10-2 fixed |
| K10.3 A video's job continues the press's trace | `d327f4b130` | K10-3 fixed |

Nothing in the admission gate's rules (`FiguresGate`, `GATE_RULES`), the sandboxes, `LibraryJobs` or `fenced` changed.

## The strategy's citations at this tip

Every `file:line` the strategy cites for these three steps holds at `212a0a6f6d`, with two notes:

- The strategy writes `learnloop_sidecar/...`; the package is under `src/` (`src/learnloop_sidecar/handlers/figures.py`).
- `FigureInline.tsx:91` is `SOURCE_CHECK_COPY.block_withheld` ("that passage is held out"), the source check's word for a held-out block. K10.2 reuses it for the failed line, as the strategy says.

Where the strategy's description did not match the code:

1. **K10.1's proof needs an author that enters `model_call`.** `FiguresGate` admits only physical requests, which enter `learnloop.ai.execution.model_call`. A real provider does that; the figure fixtures' `AuthorFake` does not. With the plain fake, a cancelled build still shows the second call (the hold stops it only at `gate.check("store")`, so nothing is stored). The test therefore uses a subclass that wraps each request in `model_call`, as `tests/figures_scope_redesign_helpers.py`'s gated fakes do.
2. **K10.3's "the `job_enqueued` record is its parent" needed one line outside `jobs.py`.** `refusal_records.figure_gate_record` set no `parent_id`, and `provenance.write` does not fill one from the cause. The other records a queued job writes (grade, diagnosis chain, `job_enqueued` itself) set `parent_id=provenance.current_cause()`. The gate's record now does the same. Outside a queued job the cause is `None`, so a press's own gate record is unchanged. The gate's rules and its record's rule, status and facts are unchanged.
3. **K10.3's proof uses the rich author's first request, not the renderer.** The strategy names "a fake renderer whose gate refuses". The job's first gated moment is the rich author's request, so the test withdraws the Manim opt-in just before that request and lets the gate refuse it. The render is never reached. This is the same gate and the same record.

## K10.1: cancelling a press stops its build (K10-1)

**Fail-first.** `tests/test_figure_cancel.py`, both tests red at the base (`assert 2 == 1`: the author made two calls):
- `test_cancel_before_the_second_attempt_sends_nothing_more_and_stores_nothing`. The build runs on its own thread, as in the app (`library_ask_inline = False`). The author's first answer (`half_density`) fails verification, and the author blocks inside that request until the test has called `reader.figure_job_cancel`. After the release, the author has made one call, `interactive_figures` is empty, `reader.figures` lists nothing, the job reads `cancelled`, and the gate's one `figure_admission` record has rule `held`.
- `test_a_cancelled_press_is_recovered_free_by_the_next_press`. The same press is cancelled the same way, then pressed again. The second press makes one author call, the repair attempt: the first attempt's answer comes back from the checkpoint the cancelled press paid for. The figure lands as an illustration.

**What changed.** `_start` (`src/learnloop_sidecar/handlers/figures.py`) takes its job through `LibraryJobs.start(..., on_job=started.append)` and hands `build_figure` the predicate `cancelled() = job.cancelled`. `build_figure` (`src/learnloop/figures/service.py`) takes `cancelled=` and folds it into the gate's `hold`, ahead of the pre-build hold (`_cancel_hold`). The gate already asks the hold before every physical model request and at `gate.check("store")`, so a cancelled build sends nothing more and stores nothing. The `FigureRefused("figures_changed")` it ends with is never shown: `_job_payload` answers `cancelled` first.

**Left as is, by design.** A build that passed its last gate check before the cancel landed still commits and lists. That figure was paid for and finished, and listing it is honest. The `build_figure` docstring says so. A request already sent when the cancel lands also finishes: its answer is checkpointed, and the next press of the same input recovers it with no call (the second test).

**Siblings: every press path that starts a figure build.**

| Path | Cancel? | Verdict |
|---|---|---|
| `reader.figure_request`, `figure.request` (show me), `reader.figure_revise` (not right?, rebuild) | `reader.figure_job_cancel` from the Reader (`useFigures.ts`) | Through `_start`: fixed |
| An attempt host's figure: the Ask panel, the practice hint panel, feedback (`figure.request` with a host, `handlers/figures.py` `_start(ctx, request, attempt=...)`) | None: `askFigures.tsx` never calls a cancel | Through `_start`, so a cancel would now be read. The panel has no cancel to send |
| The hint chooser's `explore_figure` (`handlers/hints.py` `_figure_provider` → `figures/help.qualifying_figure`), `figure.open` | n/a | Offers and opens a stored figure. Builds nothing |
| A lesson's figure (`handlers/lesson.py` `_figure_builder`) | None | Built inline in the lesson turn. A lesson turn has no cancel RPC |
| The rich (video) job | `figure.rich_cancel` → the ingest queue's `cancel` | A different mechanism, already read: `report()` raises `JobCancelled` at each phase, and `run_rich_job` re-raises it (`figures/rich.py` `cancellation`). A request already sent finishes (its docstring says so) |
| `figure.rich_retry` of a correction (`build_figure` inline in the RPC) | None | Synchronous, no job to cancel, and no author call (it goes straight to the rich job) |
| Pre-builds (`figures/prefetch.py` → `build_prefetch_figure`) | None (no press) | Their own hold: power, foreground work, the plan |
| `reader.figure_recheck` (a `LibraryJobs` job) | Not called by the desktop | No model client (the sandbox only), so nothing paid. Its mark would be as unread as K10-1's was; not changed |

**What a learner sees now.** Pressing ✕ on a pending figure stops it. No repair attempt is sent, and the figure does not turn up on the next read. Pressing the same thing again costs at most the attempts not yet paid.

## K10.2: the Reader says when a figure is withheld (K10-2)

**Fail-first.** `apps/learnloop-tauri/src/screens/reader/figures/readerFigures.test.tsx` "a figure withheld when it is delivered leaves a failed line that says so (ledger K10-2)". A press whose job finishes `{figure: null, reused: false, withheld: true}` leaves a failed line under the passage with `data-figure-failed="withheld"` and the words "that passage is held out". At the base no failed line exists (`expected null not to be null`).

**What changed.** In `useFigures.ts` `run()`, a finished job that says `withheld`, with no figure, puts the press's line back as a failed line: code `withheld`, message `SOURCE_CHECK_COPY.block_withheld`, with "try again" and ✕ like every failed line. `FigurePendingLine` writes the line's code into `data-figure-failed` (it was always `""`; nothing read it). The final wording is the UX audit's.

**Siblings: every consumer of the build job's result.**

| Consumer | What it does with `{figure: null, withheld: true}` |
|---|---|
| `useFigures` `run()`: the palette's show me, show me with words, AskRail, TutorOffers, intent palette, revisions | Fixed (above) |
| `askFigures.tsx` (the Ask panel, the practice hint panel) | Its generic failed line, "couldn't build an interactive version of this". Not silent, so it stays (strategy). Its words don't say why: ledger K10-7 |
| `LessonScreen.tsx` | Does not read this result. A lesson's visual comes with the lesson turn and has its own `withheld` status and words (`teacher/visuals.py` `WITHHELD`) |
| `useFigures` `recheck` | Reads only the job's state |
| `figure.open` | Answers a figure or an error, never this shape |

Left for K10.11, as the strategy plans: a stored figure dropped silently from `reader.figures` (its pick withheld, or a spec that no longer parses).

**What a learner sees now.** If the passage becomes held out while its figure is being built, the line under the passage stays and says "that passage is held out". Before, the press seemed to do nothing.

## K10.3: a video's job continues the press's trace (K10-3)

**Step 0: does the ingest worker open a scope per job?** No. The drain thread is a plain `threading.Thread` (`learnloop-ingest-drain`, `IngestJobs._worker_loop` in `content/pipeline/jobs.py`). It starts with every context variable at its default, and `IngestRunner.drain` has no trace code. A foreground drain (tests, CLI) runs on the enqueuing thread, under that request's scope. So the handler opens its own scope, which ends with the job (the post-attempt worker's `_with_busy_retry` is the pattern). The ingest runner's loop is untouched.

**Fail-first.** `tests/test_figure_rich_job.py::test_the_rich_job_continues_the_press_trace`. A press made under a trace scope (as the sidecar's dispatch opens one) enqueues a rich-only job; the job is drained afterwards. The opt-in is withdrawn just before the job's first request, so the job's gate refuses it and writes its `figure_admission` record. The job fails `figures_changed` with no rich call. The `job_enqueued` record for the job (`decided_by = ingest_jobs`) carries the press's trace. The gate's record carries the same trace, with that record as its `parent_id`. After the job the test thread carries no trace. At the base there is no `job_enqueued` record (`not enough values to unpack`).

**What changed.**
- `enqueue_figure_rich` writes `record_job_enqueued(queue="ingest_jobs", job_kind="figure_rich", facts={"build_mode": ...})` inside an outer `repository.atomic()` that `enqueue_batch` joins as a savepoint. The record therefore commits with the job, and a worker already draining cannot lease the job before its record exists.
- `handle_figure_rich` runs inside `provenance.trace_scope()` and calls `continue_job_trace(ctx.repo, ctx.job_id)` first.
- `refusal_records.figure_gate_record` names `provenance.current_cause()` as its parent (above, "did not match" item 2).
- ADR-017's queue-hop paragraph names the rich job and says the other ingest kinds write no record yet.

**Siblings: other ingest jobs enqueued from a press.** None of `enqueue_import`, `enqueue_extraction_repair`, `enqueue_reader_quick_check`, `enqueue_reader_inquiry_check`, `enqueue_reader_selection_check`, `enqueue_reader_exercise_import`, `enqueue_source_exercise_import`, `enqueue_practice_expansion`, `enqueue_goal_population`, `enqueue_rung_variant`, `enqueue_question_promotion`, `enqueue_concept_animation` (the other explanation video), `enqueue_inventory`, `enqueue_quick_add_build`, `enqueue_source_set_build`, `enqueue_source_set_append` or `retry_synthesis` writes a `job_enqueued` record. No ingest handler continues a trace, and none has a scope of its own. Each needs both halves (the record and a handler scope), so none is "the same two lines". The brief also limits this step's `jobs.py` edits to the rich job's two functions, so they go to K10.12 and arc B (ledger K10-6). `retry_figure_rich` (a requeue of the same job) writes no `requeued` record either: a retried rich job continues the original press's trace, not the retry's.

**What a learner sees now.** Nothing changes on screen. `learnloop why <trace>` for a press now also lists its video job's records and receipts.

## Judgment calls

- **The cancel's predicate reads `job.cancelled` without the job's lock.** The hold runs under the gate's lock. Taking the job's lock there would nest it inside the gate's, and the cancel RPC and `fenced` writes take the job's lock. A bool read is atomic, and a cancel that lands a moment after the read is caught at the next check (the next request or the store).
- **The cancel comes first in the combined hold**, before the pre-build hold. A pressed build has no pre-build hold, so the order matters only to a caller that passes both. None does today.
- **The gate's record for a cancel says `held`**, the existing rule, as the strategy says. K10.11 adds the hold's sub-code (`cancelled`). The hold's prose (`_BUILD_CANCELLED`, private) goes into the `FigureRefused` message, which the cancelled job never shows.
- **The withheld line keeps "try again".** A retry of a held-out passage is refused by the server before any call, with its own message. The alternative, a line with only ✕, would be a new kind of line, and that is the UX audit's call.
- **`data-figure-failed` now carries the line's code.** It was always `""`, and no code or test read it. It lets the test state the code and costs nothing.
- **`figure_gate_record`'s parent** (above): one line in `refusal_records.py`, needed for the strategy's proof and consistent with every other record a queued job writes.

## Gates

Listed in the hand-back report with their results: the fail-first tests; the existing figure tests (Python and vitest) with no assertion changed; typecheck, vitest and the frontend build; the targeted Python gate (`scripts/affected_tests.py` against `212a0a6f6d`, with the rules block's fixed list), `lint-imports`, `ruff`, the four vault validators, `check_gate_partition.py`; the identity pins unmoved; one regeneration of the vault references.

## Not verified

- The desktop app was not launched (rules). The withheld line is proven in vitest only.
- A cancel landing between `gate.check("store")` and the store's commit was not staged. By design it commits (above).
- No owner vault was read.
