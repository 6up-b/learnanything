# The first evening, step 6: an honest wait

Step 6 of the stage "The first evening, finished" (the design's §4 part "Build wait: expose truthful progress, then
render it in several lines", §1's rows "Build wait" and "Delivery heartbeat", §6's row 6 and §7's row 6). On the
latest live walk (a student who read half a one-section chapter) Today said "Getting … ready for questions · 1 of 2
steps done", then "Writing questions from what you've read … · 0 of 4 topics done" for three one-minute checks in a
row, with nothing to show whether anything moved or when the first question would come; the persona: "waiting at 0 of
4 was frustrating", and "tell me … roughly how long until I can answer the first question". Now the book's line and
the section's writing carry a typed detail made only of facts recorded when they happened, and Today (desktop and
phone) says it in a few short lines under the existing line, with the rest collapsed. Branch
`ux/first-evening-build-wait`, from `ux/first-evening-next-practice` at `1ac9290577`.

Nothing is built, written, scheduled or scored differently: no model request's bytes, deadline, retry rule, prompt,
config key, kill switch or algorithm tag changes. One migration (258, a WORKFLOW table for operational facts). No
identity pin, golden or snapshot moved.

## Judgment calls to read first

1. **A table, not the job payload, for the live facts (migration 258).** Streamed output arrives on the request's own
   thread hundreds of times a minute, while the section job rewrites its payload with `{**payload, "question_parts":
   …}` from a copy taken at its start: output written into the payload would be overwritten, and rewriting the whole
   payload each second is a large write. The phone's host is another process, so an in-memory registry in the desktop
   sidecar would never reach the phone. `ingest_job_progress` holds one small row per job. The facts that fit the
   existing payload do go there: each topic's `started_at`/`written_at` in `question_parts` (the brief's preference).
2. **"Output" is counted in pieces, at most about once a second.** A piece is a non-empty streamed delta, text or
   reasoning: the stream deadline's own rule for "output advanced" (`_StreamDeadline.output`); a lifecycle event or
   keepalive is not a piece. The runner writes a request's count at most every `OUTPUT_RECORD_SECONDS` (1 s), and a new
   request at once: the screens read every 5 s, a reply streams thousands of pieces. So the recorded count and time
   can lag the stream by under a second; never ahead of it.
3. **"Still writing" is told by the screen, from two reads.** The sidecar never says "still writing": it records the
   count and the time of the last piece. The screen says "still writing" only when the last piece's time or the count
   moved since its previous read of the same wait (`replyGrew`), and on a first read says when the last part came. No
   threshold says "stalled": a long silence is said as its time ("reply arriving, last part 3 minutes ago").
4. **Times are counted to the sidecar's read, not the screen's clock.** Every detail carries `as_of` (the sidecar's
   now); ages are `as_of − time`, floored to whole seconds or minutes, so a phone whose clock differs says nothing
   false. The phone, whose Today is not read again on its own, says clock times ("asked at 18:03") instead of ages that
   would grow false as the screen sat. The desktop rereads every 5 s while a wait shows (the existing `CAUSE_POLL_MS`
   read and the queue-changed signal); no timer was added.
5. **The topic's place only while one job writes.** "Writing topic 1 of 4" is the job's own part order. Where a second
   job writes beside it (a second wave of the part read, or another finished section), the line's "0 of 4 topics done"
   adds both up, so the topic is named without a place ("Writing questions on “…”").
6. **The measured time per topic is this library's own, from its own topics.** The middle of the newest five topics
   written (request to questions applied), the build time's own rule (`build_minutes`, sample 5), with its count. Parts
   written before this step carry no times and count for nothing; a library with none says the first questions can
   take a few minutes. The build's measured time is the existing `build_minutes`, now with its sample count
   (`build_minutes_measured`); its words on the line ("usually about 4 min") are unchanged, and the details name the
   count.
7. **Kept within the wording step's lines.** `todayCause.ts` gains one optional `detail` on two causes (three lines);
   `TodayPlace.tsx` and the phone's `PlanToday.tsx` render the detail under the existing line. No sentence that says
   where questions come from was changed (the wording step owns those).
8. **The drafted-topic count is taken when the checks start.** At "Running quality gates" the candidate has been
   merged from parsed passes and normalized (`mode.normalize`, then the duplicate-id check): its learning-object rows
   are counted. It is said as "8 topics drafted · checking them", and the details say the topics you get can differ.

## Every progress field and its source

The sidecar's status line carries `build_detail` on a build's own working line (`add_source.py:3094`,
`_building_line`) and `writing_detail` on the reading's `questions` fact (`add_source.py:2658`, first active writing
job). Both are made in `src/learnloop/content/pipeline/wait_detail.py`.

| Field | Meaning | Recorded by (path:line) |
|---|---|---|
| `build_detail.as_of`, `writing_detail.as_of` | when the sidecar read the facts | `wait_detail.py:135` (the status line's `SystemClock().now()`, `add_source.py:3094`; the reading's clock, `add_source.py:2658`) |
| `build_detail.started_at` | the build batch's start | `ingest_batches.started_at` (`wait_detail.py:136`) |
| `build_detail.stage` = `queued` | no build step running yet | the batch's jobs' status (`wait_detail.py:134`) |
| `stage` = `reading`, `inventory.done/total` | windows whose answer was checked and kept, of those known | the inventory's `ctx.report(current_window, total_windows)` after each kept window (`jobs.py:1565`, unchanged) |
| `inventory.reused` | units whose inventory is cached and not asked again | `_record_step(ctx, reused=…)` (`jobs.py:1528`) into `ingest_job_progress.reused` |
| `stage` = `planning`, `synthesis.part/parts` | the part the synthesis is on, of how many | the synthesis's `_notify(current=, total=)` → `ctx.report` (`source_set_synthesis.py:1933`, `:1940`, `:1951`, unchanged) |
| `synthesis.pass` | `plan` (base pass), `evidence` (a further pass with the passages the plan asked for), `plan_reused` (a part kept from an earlier run) | `_notify(step=…)` (`source_set_synthesis.py:1940`, `:1951`, `:1933`) → `_synthesis_progress` (`jobs.py:1904`) → `ingest_job_progress.step` |
| `stage` = `checking` | facet identity or the plan's checks | `step="identity"` (`source_set_synthesis.py:685`), `step="validate"` (`:992`, `:1009`) |
| `stage` = `organizing` | the topics' structure across sources | `step="structure"` (`source_set_synthesis.py:2362`) |
| `stage` = `saving` | persisting and applying | `step="persist"` (`:1088`), `step="apply"` (`:2884`) |
| `drafted_topics` | learning-object rows of the parsed, normalized candidate; only on a `validate` step | `_notify(..., drafted_topics=…)` (`source_set_synthesis.py:1009`) |
| `retry` | the runner's own second try, or a later attempt | `ingest_job_progress.try_number` (`runner.py:1099`, each try) or `ingest_jobs.attempt_count > 1` (`wait_detail.py:80`) |
| `delivery.request_sent_at` | the newest request of this try still in flight | `model_call_receipts.started_at`, status `started`, written before the request is sent (`model_calls.py:103`, `wait_detail.py:101`) |
| `delivery.reply_received_at` | the newest reply received | `model_call_receipts.finished_at`, status `completed` |
| `delivery.output_pieces`, `last_output_at` | the in-flight request's streamed pieces so far, and the last one's time | `_OutputPieces` on the plan stream (`chatgpt_plan.py:143`, `:513`) → `report_model_output` (`execution.py:209`) → `job_output_recorder` (`runner.py:1441`) → `ingest_job_progress.output_*`; shown only when its request is in flight this try (`wait_detail.py:112`) |
| `measured` (build) | earlier finished automatic builds' time, scaled to this scope, with how many | `build_minutes_measured` (`add_source.py:2479`) |
| `writing_detail.queued` | the writing job waits its turn | `ingest_jobs.status` |
| `writing_detail.topic` (title, index, total), `topic_started_at` | the topic whose writing was asked for and is not written yet | `question_parts[i].started_at` (`proposals.py:737`); title from the applied topic in the vault |
| `measured` (writing) | middle of the newest five topics' times, with how many | `question_parts[i].started_at` → `written_at` (`proposals.py:776`), `topic_minutes` (`wait_detail.py:162`) |

Not used for any of it: the worker lease heartbeat (it renews the lease every 15 s whatever the model does), a
model's unfinished answer, a percentage, a time left.

## The lines, before and after

"…" is the book's title. Desktop lines sit under the waiting indicator (◐), in the same quiet style as its second
line; "details ▸" is a collapsed `<details>`.

### A book being got ready (desktop)

Before (every read, the whole build):

> ◐ Getting “…” ready for questions · 1 of 2 steps done
> The first time, this can take several minutes. *(after 5 s)*
> Questions come as you finish sections. Keep reading meanwhile.

After (the first two lines and the last are unchanged; the middle lines are new):

| State | New lines | details ▸ |
|---|---|---|
| waiting to start | Waiting to start · Started 10 seconds ago | No book has finished getting ready in this library yet, so no time is given. |
| reading | Reading the text · 0 of 1 part read · Started 20 seconds ago · asked 15 seconds ago, no reply yet | (2 parts were read before and are not read again.) + the measured line |
| planning, no reply yet | Planning questions · part 1 of 1 · Started 2 minutes ago · asked 40 seconds ago, no reply yet | the measured line |
| planning, reply grew since the last read | … · Started 2 minutes ago · still writing | |
| planning, reply arriving, nothing new this read | … · Started 2 minutes ago · reply arriving, last part 8 seconds ago | |
| planning, a long silence | … · reply arriving, last part 3 minutes ago | |
| a further pass | Planning questions · part 1 of 1 · looking at the passages it asked for | A part can take a second look, with the passages it asked to see. |
| a part kept | Planning questions · part 1 of 2 · kept from before | |
| checking, topics drafted | 8 topics drafted · checking them · Started 3 minutes ago · reply received 12 seconds ago | The topics you get can differ once the checks are done. |
| organizing / checking / saving | Organizing the topics / Checking the plan / Saving the plan | |
| a retry | Trying again · Reading the text · 0 of 1 part read | An earlier try stopped; this one picks up from what was kept. |
| measured library | (lines as above; the line keeps "· usually about 4 min") | Earlier builds in this library took about 4 minutes for a book this size (from 3 builds). |

### A section's questions being written (desktop)

Before: "◐ Writing questions from what you’ve read in “…” · 0 of 4 topics done" / "Keep reading meanwhile."

After, under the unchanged line:

| State | New lines | details ▸ |
|---|---|---|
| waiting its turn | Waiting to start · The first questions can take a few minutes. | |
| 0 of 4, no reply yet, first library | Writing topic 1 of 4: “Spectral theorem” · Started 1 minute ago · asked 1 minute ago, no reply yet · The first questions can take a few minutes. | |
| output advancing | … · Started 1 minute ago · still writing | |
| nothing new this read | … · reply arriving, last part 9 seconds ago | |
| measured library | … · Here a topic's questions have taken about 2 minutes to write. | Measured on the last 3 topics written in this library. |
| another job writes too | Writing questions on “Spectral theorem” · … | |
| a retry | Trying again · Writing topic 1 of 4: “…” | An earlier try stopped; topics already written are kept and not written again. |

When the wait ends (questions applied, or the build or writing stopped) the cause is the ready, failed or stopped one,
exactly as before: the detail is shown only on the two waiting causes and disappears with them.

### The phone

Before: "Nothing planned for today." / the cause's sentence (for example "Writing questions from what you’ve read in
“…” · 0 of 4 topics done. Keep reading meanwhile.") / Keep going.

After: the same, with the same lines under the sentence in clock times ("Started at 18:02 · asked at 18:03, no reply
yet"; "reply received at 18:07"), and the same collapsed details. Its Today is read when it opens and on the shared
queue signal, as before: "still writing" shows only where a later read finds the reply grown.

## What is measured, and from how many

- **A build's time**: the existing `build_minutes` (the middle, per section of scope, of the newest five finished
  automatic builds, scaled to this scope), now with how many builds it rests on (1 to 5). None before the library's
  first finished build.
- **A topic's time**: from a topic's writing being asked for (`started_at`) to its questions applied (`written_at`),
  the middle of the newest five such topics in this library, with how many (1 to 5). None before one topic was timed
  (every library before this step, and a new one).
- Nothing else is a measurement: ages are differences of recorded times as of the sidecar's read.

## What is never said

A percentage; a time left or an end time; "almost", "soon"; a minutes figure without this library's own measurement;
a count of topics before the candidate is parsed and normalized; "stalled" or any threshold on silence; "still
writing" on a first read, on a connection that streams nothing, or when the reply did not grow since the last read;
anything the model wrote before it was validated (titles are applied topics' titles); the deny-list's terms.

## Tests (written first; fail-first evidence)

New `tests/test_build_wait_detail.py` (18), `tests/test_ingest_job_progress_migration.py` (3),
`apps/learnloop-tauri/src/app/waitDetail.test.ts`, new describes in `TodayPlace.test.tsx` and the phone's
`Today.plan.test.tsx`, new cases in `copy/denyList.test.tsx`.

Backend, the same new tests run with each source change undone in a scratch copy of the worktree (the stream's
output counter, the per-topic times, the named synthesis steps, a fresh progress row per try): **8 failed, 9 passed**
(17 tests then). Failing: advancing output, a long silence, a retry, the once-a-second write, the named steps and the
topic count, the extra evidence pass, the kept part, the topic being written and the time per topic. Passing on both
(controls, or facts read from rows the test writes itself): no output yet, the reply received, a transport that does
not stream, the request bytes unchanged, the line's detail from written rows, the measured build time, a queued job,
nothing measured before any topic was timed. Against the base commit's code the two new Python files fail to import
(`observe_model_output`, the migration not found).

Frontend, the new tests against the base `todayCause.ts`, `TodayPlace.tsx` and `PlanToday.tsx` (with and without
`app/waitDetail.ts`): desktop **6 failed** in `TodayPlace.test.tsx` (`Unable to find an element by:
[data-testid="today-cause-detail"]`), `waitDetail.test.ts` and `denyList.test.tsx` failed to load (no module); the
phone **3 failed** (the same missing element), 55 passed. The "older sidecar" control passed on both.

Assertions changed in this step's own tests while writing them (none of an existing test): the clock-time patterns
(`\S+` did not admit "01:07 PM"); a TodayPlace expectation that a reply growing from no parts to five said "reply
arriving": by the rule it is growth, so the test now expects "still writing" there and "reply arriving, last part 6
seconds ago" on the next read; two waits for the indicator's 350 ms delay (`findByText`) and an empty list before the
ready read. Existing tests edited: the 17 earlier migration tests' "nothing else changed" diffs admit
`JOB_PROGRESS_ADDED_OBJECTS`; `test_ingest_queue_store.py` lists the new table and four store methods.

## What I ran

Every Python run through the scratch wrapper (`env -i`, empty home and config dirs) in a 3G scope at `-n 1`; npm in a
5G (vitest) or 3G scope with the shared npm cache.

- Affected tests: `scripts/affected_tests.py --files <the 13 changed src files>` listed 1,389 files; filtered by name
  (first_questions, add_source, source_status, ingest_runner, ingest_queue, synthesis_progress, source_set_synthesis,
  chatgpt_plan, section_question, mobile_allowlist, mobile_v4, migration/schema, plan_deadline, model_call, receipts,
  execution, ingest, proposal, authoring, ux_phase1, section, part_read, topic_work, practice_generation, study_map,
  synthesis) plus every edited test file: 140 files in 4 chunks, `-m "not arc_close"`: **493, 751, 404, 232 passed**
  (all exit 0). After the last source edit (the topic's place with two jobs) the 21 files named add_source,
  source_status, section_question, part_read, mobile_v4, ux_phase1, section_done, topic_work and first_questions
  again: **320 passed**.
- `test_build_wait_detail.py test_ingest_job_progress_migration.py test_first_questions_today.py test_identity_pins.py
  test_structure_ratchets.py test_effective_defaults_golden.py test_cli_help_snapshot.py test_kill_switches.py
  test_sqlite_file_copies.py test_public_tip_guards.py test_ingest_queue_store.py test_mobile_allowlist.py`: **801
  passed**. `test_test_layout.py` alone: **3 passed**. `test_architecture.py` alone: **18 passed**.
- `ruff check`: All checks passed! `lint-imports --no-cache`: Contracts: 45 kept, 0 broken.
  `check_gate_partition.py`: collected 32717: landing 32651 + arc_close 66.
- Desktop: `npm run typecheck` clean; `npx vitest run --maxWorkers=4`: **Test Files 324 passed, Tests 3510 passed**;
  `npm run frontend:build`: ✓ built in 2.89s. Phone: typecheck clean; vitest **43 files, 450 passed**; `npm run
  build`: ✓ built in 864ms.
- `desktop_validate.py`: its three counts moved by one for `app/waitDetail.ts` (336 / 325 / 342); it reports the new
  file's reference note missing and three notes stale, which the landing's regeneration writes (not regenerated
  here, per the rules).
- Structure ratchet: `functions_over_200_lines` rose to 71 with `_source_status_line`; the active build's line moved
  into `_building_line`, so it is back at 70. No golden changed. Identity pins: none moved.

## What a live-route walk must check

The second walk's three unchanged minutes (a first library, one web chapter, read to about half):

1. **The build (about the first minute after Add).** Under "Getting “…” ready for questions · 1 of 2 steps done":
   "Reading the text · 0 of 1 part read", then "Planning questions · part 1 of 1" with "Started N minutes ago" and,
   while the reply streams, "still writing" at each 5-second read (or "reply arriving, last part N seconds ago" on a
   read where nothing new came), then "N topics drafted · checking them" and "Saving the plan". details ▸ says no
   time was measured in this library. Check the wording never claims a time left.
2. **Writing at 0 of 4 (the three checks).** Under "Writing questions from what you’ve read in “…” · 0 of 4 topics
   done": "Writing topic 1 of 4: “<the first topic>”", "Started N minutes ago · still writing" (the minutes grow at
   each check; "still writing" while the plan route streams), and "The first questions can take a few minutes." The
   persona should be able to tell, at each check, that a reply is arriving and since when.
3. **The first questions.** As soon as topic 1 applies, the lines give way to "3 questions from what you’ve read … are
   ready" with Begin, as before.
4. **A second book in the same library.** Its writing says "Here a topic's questions have taken about N minutes to
   write." and details ▸ "Measured on the last K topics written in this library." (K up to 5); its build's details
   name the builds measured.
5. **The phone** with an empty plan: the same lines in clock times under the sentence; Keep going the only action.
6. Check the lines at phone width, with reduced motion, and in the real WebKitGTK window; that "details" opens and
   closes by keyboard; that a reply on a route that does not stream says "asked …, no reply yet" until it is received.

## Not verified

- No app, browser, server or model ran: every state is from fakes (the plan stream's fake connection and clock, the
  structured fakes, vitest RPC fakes). The words at phone width, in the real WebKitGTK window, with reduced motion and
  by keyboard (the details toggle) are unseen.
- The output path on the live plan route: the fake stream drives the real reader, deadline and receipts, but a real
  stream's delta rate and the write load of about one small write a second per streaming request on the real vault
  were not measured. Another provider (OpenRouter, Codex) streams nothing here: it says "asked …, no reply yet" until
  its reply is received, by design.
- The append build (a book added to a subject that already has a map) passes no progress callback, so it names no
  step: its stage reads "Planning questions" with no part for its whole run, delivery facts included. A bootstrap
  build (the walk's) names every step.
- Two inventory windows in flight at once share one output row: the newest request written wins.
- Parts written before this step carry no times, so a library with history starts its time per topic from zero
  samples; the measured line appears after its first topic written with this code.
- The phone's Today is not reread on its own, so "still writing" appears there only on a later read.
