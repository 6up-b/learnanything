# Reader workbench v2, RD3a: the companion's ask and search in context (backend)

The backend half of stage RD3 of `docs/specs/spec_reader_workbench_v2.md` (§3.4, §8.6, §9.3, §16's RD3 row). Branch
`reader/rd3a-companion-search-backend`, based on main `54be27df69` (migration head 264, latest tag mvp-0.66). RD3's
frontend (the `Companion` component, docks, summon, the pill, the search panel and its animation) waits for RD1; this
step builds what it calls.

**What it delivers.** `companion.ask` / `companion.ask_job` / `companion.ask_cancel` (the companion's question as a
polled job, off the sidecar's serial loop, idempotent by `request_id`), `search.everything` / `search.job` (word groups
at once, meaning groups through a job), their Rust passthroughs and typed `client.ts`/`dto.ts` entries. No UI, no change
to `ReaderScreen` or the desks frontend, no migration, no config key, no kill switch, no algorithm tag, no prompt
change, nothing on the phone.

## 1. What landed

| Item | Where |
|---|---|
| One Ask core in three steps, shared by `reader.ask` and `companion.ask` | `H:reader.py`: `prepare_reader_ask` (every gate and the context, on the request), `generate_reader_answer` (`reader_dialogue.ask`, failures as sidecar errors), `reader_ask_reply` (the reply and its side effects); `reader.ask` runs the three in order |
| Polled jobs (thread, receipts, offers, cancellation gate, honest failure, bounded memory) | `src/learnloop_sidecar/polled_jobs.py` |
| `companion.ask`, `companion.ask_job`, `companion.ask_cancel` | `H:companion_ask.py`; where a question is asked: `learnloop/companion/asks.py` |
| `search.everything`, `search.job` | `H:search.py`; the word groups: `learnloop/companion/search.py`; the notes through `H:notes.py`'s new `notes_search_state` / `search_vault_notes` (the notes' own handler, so nothing new names the notes' modules) |
| Rust passthroughs | `src-tauri/src/commands.rs`, `main.rs` (five commands) |
| Typed client | `src/api/client.ts` (`companionAsk`, `companionAskJob`, `companionAskCancel`, `searchEverything`, `searchJob`), `src/api/dto.ts` |
| Desktop only | `tests/test_mobile_allowlist.py` (`READER_RD3A_RPCS`, pinned to the two handler tuples) |

## 2. The job contract

**`companion.ask`** takes `reader.ask`'s input plus `{request_id, surface, desk_id?, pad_block_ids?, notebook_ref?}`.
`surface` is one of `desk`, `reader` (the old Reader screen, no desk), `lesson`, `notebook`; `desk` requires `desk_id`,
`notebook` requires `notebook_ref`. On the request, in this order:

1. A repeat of `request_id`: the same input answers the same job's current state (running, finished, or `expired`
   with its `question_event_id` once dropped from memory); other input under the same id is refused
   (`request_reused`). Nothing is gated or asked again.
2. Where it is asked (`companion.asks.ask_context`, read-only): the desk must exist and be open (`desk_not_found`);
   its goal and focused window are read from the desk, never taken from the client; each pad block must exist and
   stand (`block_not_found`); at most 40 blocks.
3. `prepare_reader_ask`: every `reader.ask` gate (the Reader switch, source identity, the per-source opt-out, the
   phone's checks, the OK to use AI, the provider's readiness, RW1c's restriction and binding, the retrieval request,
   the learner state). A refusal raises here, so the client gets it at once and no job exists.
4. The job starts and the reply is its state.

On the job thread: `generate_reader_answer` (the model call and the exchange `reader_dialogue.ask` records, which
writes the exchange's passages through `question_event_spans` as every Reader Ask does), then
`record_exchange_context` (`companion_exchange_context`: desk, surface, the focused window's spec plus
`notebook_ref`, the pad blocks, the desk's goal, origin `live`), then `reader_ask_reply` (the gap queue, practice
request, excerpt exposure, offers, the prefetch trigger). Model calls are recorded under `companion.ask:<request_id>`;
background figure prebuilds yield while it runs (the `tutor` foreground mark `reader.ask` has).

**`companion.ask_job {request_id}`** reads at once (never a wait) and **`companion.ask_cancel {request_id}`** cancels;
both answer:

| Field | Meaning |
|---|---|
| `status` | `queued` (started, not yet on its thread), `running`, `done`, `failed`, `cancelled`, `expired` (finished and dropped from memory) |
| `done` | stop polling: finished, failed, expired, or cancelled once its thread has ended |
| `partial_md` | empty until the answer is whole, then the answer (deviation 1) |
| `citations` | the answer's citations when done, else `[]` |
| `streamed_pieces` | output pieces the request in flight has streamed (`observe_model_output`); 0 where the transport does not stream |
| `question_event_id` | the exchange once recorded (also on a cancelled job whose answer was already being written) |
| `kept` | cancelled after its request was sent: the exchange is in the history, the answer is not delivered |
| `answer` | `reader.ask`'s reply, key for key, when done |
| `error` | `{code, message, retryable, details}` when failed |

An unknown id is `job_not_found` ("LearnLoop restarted since it was asked; if it finished, it is in your history").

**Cancellation.** A cancelled job's next physical model request is refused at admission (`polled_jobs._CancelGate`,
composed with the context's closing gate; `SpendCancelled`), so nothing more is sent. A request already sent finishes,
the Ask records its exchange, and the job reads `cancelled` with `kept` true. A finished job keeps its outcome.

**Honest failure.** Every failure ends the job with its error: a sidecar error as raised (`provider_unavailable`,
`question_limit_reached`, ...), a missing OK as `waiting_for_ok`, a busy database as `database_busy`, anything else as
`internal` (logged). When the Ask's own `provider_unavailable` was caused by the job's refusal, the job says what it
was: `cancelled`, or `interrupted` when a context close or vault switch ended the epoch the job started in
(`BackgroundJobs.cancel`). A thread that ended without finishing reads `failed` (`interrupted`), never running forever.

**Memory.** At most 64 finished jobs per registry are kept with their results (running jobs are never dropped); a
dropped job leaves a receipt (its status, its `question_event_id`, its request params) in a bound of 1,024, so a
repeated id is answered as `expired`, never asked twice.

## 3. The mutex proof

`tests/test_reader_rd3a_companion_ask.py::test_a_second_rpc_is_served_while_a_generation_is_held` runs the real serial
loop (`learnloop_sidecar.server.serve`) on a pipe. The fake tutor (`tests/companion_rd3a_helpers.HeldTutor`) makes one
physical request through `model_call` (admitted by the request gate) and holds inside it until released. The test sends
`initialize`, then `companion.ask` (its reply arrives within 5 s: `queued` or `running`, not done), waits until the
tutor is inside its request, then sends `desk.state` (answered while the tutor is still inside) and `companion.ask_job`
(`running`, `done` false, `partial_md` empty), then releases and polls until `done` (the answer and its citations).
With the job run inline on the request (one line, fail-first below) the `companion.ask` reply does not arrive and the
test fails.

## 4. Search in context

`search.everything {query, desk_id?, scopes?}`: `query` 1 to 200 characters, searched when at least 2 after
whitespace is collapsed; `scopes` any of `sources`, `passages`, `notes`, `pads`, `threads`, `exchanges` (all when
omitted; "open on this desk" is the client's own group, §9.3). An unknown or archived desk is refused.

| Group | Words (at once) | Meaning (the job) |
|---|---|---|
| sources in your library | titles (display title, else the revision's or canonical URI); each with the desks it is open on and whether this desk | none (titles) |
| passages and moments | the library's search (`search_library(deep=False)`, `reader.search_sources`' own); off while the Reader is off; a transcript cue (`t=<start>-<end>`) opens the video at its start | the same search's deep pass (stored passage vectors, one query embedding, the query rewrite where configured), only rows found by `meaning`/`rewrite_meaning` that the words did not find; a partial index says its coverage |
| your notes and highlights | the vault's notes by words (`notes.search`'s own search; the notes switch honoured, said when off), and the learner's own words LearnLoop read for a gap whose source no other group shows (not `tutor_question`, an exchange; not `learner_note`, a note, which would bypass the notes switch) | the vault's notes by meaning (`notes.search`'s meaning mode), new notes only |
| your pads | standing block text of pads not archived (removed blocks excluded); transcribed ink flagged `handwriting` | unavailable: no meaning index of pad text |
| threads | answered Reader exchanges by question or answer; each with its answer event and its branch root (walked up `parent_exchange_id`, at most 64 steps), opening a `thread` ref | unavailable: no meaning index of exchanges |
| past companion exchanges | `companion.history`'s words query, newest first across desks, with desk and anchor | unavailable: no meaning index of exchanges |

**Bounds.** Twelve rows per group with `more` when more exist (the panel shows three; §9.3's attention limit is the
client's); cue lookups batched 200 keys a query; one query embedding per meaning search (cached by text, inside the
library retrieval's caps and time box); thread roots bounded per row.

**Rows** carry a `ref` (a `ContentRef`: `source`, `video` with `t`, `pad`, `thread`, `panel: notes`) and a `target`
(`span_id`, `t` or `block_id`) where they have one.

**The meaning job.** Started only when at least one group can be searched by meaning: `meaning.status = pending` with
the `job_id` and the groups; otherwise `unavailable` with one reason per group (embeddings off, the library index
missing, retrieval off, the Reader off, the notes off, no meaning index, or "waiting for your OK to use AI", checked
before anything is sent). A newer search from the same desk cancels the older job (`supersede_key`), which then
delivers nothing (`status = cancelled`, no groups). `search.job {job_id}` reads at once.

## 5. Deviations, with reasons

1. **`partial_md` is not streamed.** No transport in the tree streams answer text: the tutor's answer is structured
   output and arrives whole (`execution.observe_model_output` reports only a count of streamed pieces). The contract
   is built as the spec names it, with `partial_md` empty until the answer is whole and then the answer, and
   `streamed_pieces` as the honest progress measure. Real partial text needs a transport change (streamed structured
   output and partial-JSON parsing), which is outside this step; the job contract would not change.
2. **A third RPC, `companion.ask_cancel`.** The spec lists `companion.ask` and `companion.ask_job`; the brief asks for
   cancellation, which needs a call. `search.job` has no cancel: a newer search supersedes, and closing the panel just
   stops polling.
3. **Idempotency lives as long as the sidecar.** Request ids and their outcomes are kept in memory (finished jobs and
   receipts, bounded). After a sidecar restart the job is gone (`job_not_found`, which says the history has the
   exchange if it finished), and a repeat of that id would ask again. Surviving a restart needs the id persisted
   (options in §8).
4. **Pad text and the desk's goal are recorded, not sent to the tutor.** §8.6 says the companion "adds" the desk, the
   surface, the focused window, pad blocks and the goal; §15.3 calls that a structured prompt change with an identity
   pin, and the brief allows no prompt change beyond what the shared core needs. So they go into
   `companion_exchange_context` and the tutor's prompt is `reader.ask`'s exactly (the identity pins do not move).
   Sending them is its own step, with the pin.
5. **Off the Reader** (`ask_tutor_question` for practice and Today) is not wrapped: `companion.ask` takes `reader.ask`'s
   passage-grounded input, as the brief scopes it. The surfaces named are the ones a passage ask comes from.
6. **An exchange whose model call failed or was cancelled before sending has no context row.** The tutor records the
   question (`answer_status` `pending`, then `failed`) before its call, but its id reaches the companion only when the
   Ask returns, so such a question shows in the history as asked before desks (`backfill`). Fixing it needs the
   question id before the call (a callback through `reader_dialogue.ask` and `tutor_qa.ask_question`; options in §8).
7. **Meaning search covers passages and notes only.** Pads, threads and exchanges have no vectors and no embedding
   recipe in the vault; the brief asks for the existing route and an honest "not available" otherwise, so they say so.
   §8.5's history search by meaning over exchange text is not built for the same reason.
8. **The surface vocabulary.** RD0 left `companion_exchange_context.surface` unconstrained until RD3 named it; it is
   named in code (`companion.asks.ASK_SURFACES`, the params' `Literal`, a test that the two agree) and the history's
   "where" gains "in a notebook". The column stays unconstrained (no migration).
9. **`learnloop_sidecar/handlers/reader.py` grows by 46 lines** (the call's dataclass and the step signatures);
   `tests/goldens/structure.toml`'s one line for it is raised by hand (2980 to 3026). The split cannot move to its own
   module without moving the provider lookup that every `reader.ask` test replaces on this module.

## 6. Tests, and fail-first evidence

New: `tests/test_reader_rd3a_companion_ask.py` (11), `tests/test_reader_rd3a_search.py` (13), helpers
`tests/companion_rd3a_helpers.py`. Edited: `tests/test_mobile_allowlist.py` (the five RPCs pinned desktop-only, and a
test that the pin list is the two handlers' tuples). No assertion was changed or loosened.

Each behaviour was broken on purpose in the worktree (one line replaced by the scratch script), its test run, and the
file restored from git (`git status` clean after each):

| Broken | Test | Result |
|---|---|---|
| the job run inline on the request instead of on its thread | `test_a_second_rpc_is_served_while_a_generation_is_held` | 1 failed (`queue.Empty`: the `companion.ask` reply never came while the tutor was held); rerun after the test's pipe fix: 1 failed, same |
| the repeated-request check | `test_a_repeated_request_id_answers_the_same_job_and_asks_once` | 1 failed (`ValueError: job 'req_once' exists`) |
| the cancel gate's refusal | `test_a_job_cancelled_before_its_request_is_sent_sends_nothing` | 1 failed (`kept` true: the request was sent) |
| the exchange-context write | `test_the_exchange_context_is_recorded_and_its_passages_equal_a_rebuild` | 1 failed (`0 == 1` context rows) |
| the cause unwrap (a close said as `interrupted`) | `test_closing_the_context_interrupts_a_job_honestly` | 1 failed (`provider_unavailable`) |
| the per-desk supersede key | `test_a_newer_search_from_the_desk_supersedes_the_older_job` | 1 failed (older job `running`, not `cancelled`) |
| the meaning job's leave-out of word results | `test_the_meaning_job_adds_only_what_the_words_did_not_find` | 1 failed (`[('s6', True), ('t1', True)]`) |

Some broken runs also showed one teardown error (a job thread the break left running); none in the restored runs.

**No behaviour change for `reader.ask`.** The split moves code without changing it (the same calls in the same order;
the phone check reads the request's origin once on the request). Compared by running every test that exercises
`reader.ask` and the handler's neighbours (below: 3,683 passed, 5 skipped, none failed), including the tests that
replace `ready_tutor_qa_provider` on the module.

## 7. Commands and results

Each pytest run: `uv run --no-sync pytest -q -n 1 -p no:cacheprovider -m "not arc_close" <files>` through the scratch
wrapper in a `systemd-run --user --scope -p MemoryMax=3G -p MemorySwapMax=1G` scope, one at a time.

| Command | Result |
|---|---|
| `tests/test_reader_rd3a_companion_ask.py` (final) | 11 passed |
| `tests/test_reader_rd3a_search.py` | 13 passed |
| `scripts/affected_tests.py --files <the 9 changed src files>` | 621 test files (more than 150) |
| the 210 of them whose names match `reader|ask|tutor|mobile|phone|companion|search|notes|rd0|rd3a|library|desk|figures_rw5b|plan_first|one_ai_ok|protection_surface|ux_walk|rw4_kill|learner_blindness|sidecar|prefetch|explorable|rw1|rw4|ca2|ca3|ca6`, plus the four that import `handlers.reader` without matching, in six chunks of at most 40 | 1022 / 816 / 502 / 749 / 435 (+5 skipped) / 159 passed: 3,683 passed, 5 skipped, 0 failed |
| the two new files + `test_mobile_allowlist.py`, `test_identity_pins.py`, `test_structure_ratchets.py`, `test_effective_defaults_golden.py`, `test_cli_help_snapshot.py`, `test_kill_switches.py`, `test_sqlite_file_copies.py`, `test_desktop_rpc_contract.py`, `test_notes_never_read.py`, `test_reader_rd0_fences.py` | 792 passed |
| `tests/test_test_layout.py` alone | 3 passed |
| `tests/test_architecture.py` alone | 18 passed |
| `uv run ruff check` | All checks passed! |
| `uv run lint-imports --no-cache` | Contracts: 52 kept, 0 broken. |
| `uv run python scripts/check_gate_partition.py` | collected 33199: landing 33133 + arc_close 66 |
| `npm ci` (shared npm cache) | installed (install-script warnings only) |
| `npx tsc --noEmit` (`npm run typecheck`'s command) | exit 0 |
| `npx vitest run --maxWorkers=2 src/api` | 6 passed |
| `cargo check --manifest-path src-tauri/Cargo.toml` (shared cargo cache) | Finished `dev` profile |

Pins and goldens: no identity pin moved (the request key is compared in memory, never hashed); `tests/goldens/
structure.toml`'s line for `handlers/reader.py` raised 2980 to 3026 by hand (deviation 9); no effective default, CLI
snapshot or kill switch moved; `desktop_validate.py`'s counts stand (no new TypeScript file). No bug-ledger row: no
defect was found in existing code.

## 8. Open questions for the orchestrator (options)

- **Idempotency across a restart** (deviation 3): (a) leave it in memory (today: a restart says so, the history has
  any finished exchange); (b) a `request_id` column on `companion_exchange_context` with a partial unique index
  (migration 267, written after the answer, so a repeat after a restart finds a finished exchange; an unfinished one
  is asked again); (c) a small RECEIPT table keyed by `request_id` written before the call (also catches an
  unfinished one, at the cost of a receipt per question).
- **Context for failed questions** (deviation 6): (a) leave it; (b) an `on_question_recorded` callback through
  `reader_dialogue.ask` to `tutor_qa.ask_question`, so the context row is written as the question is (a signature
  change in the shared core, no behaviour change for `reader.ask`).
- **Pad text and goal in the tutor's prompt** (deviation 4): a structured prompt change with the identity pin bumped
  deliberately, best taken with RD4 when pads have a UI.
- **Meaning over pads and exchanges** (deviation 7): an embedding recipe per kind through the vault's backfill (its
  switches, caps, receipts and price), with the identity rules for a new recipe.

## 9. What I did not verify

- Anything in the packaged app or a real webview; the RD3 latency budgets ("edits acknowledged in under 50 ms and
  hover cards in under 250 ms while an answer generates") beyond the serial-loop proof.
- A real provider's streaming (only the fakes'); a real embedding route (the meaning job's passage and notes searches
  ran on doubles of `search_library` and `meaning_search_state`; the notes' meaning search ran in no test here).
- Owner copies (below), the landing gate, the whole suite, the durability lane, `npm run frontend:build`.

## 10. Owner-copy checks for the orchestrator

On backup-API copies (`learnloop.db.copies`), never a live vault; no model call on a copy:

1. `search.everything` over a few queries (a source title word, a word from a recent question, a word from a pad if
   any) on each vault: the time of the call (word groups only), the rows per group and `more`, and
   `meaning.status` with its reasons ("available or not": with the vault's embeddings on and the library index
   complete, `pending`; do not poll the job: it embeds the query, and may rewrite it with a chat model where `source_retrieval.query_rewrite` is on).
2. Job lifecycle with a fake: a sidecar context on a copy with the tutor provider replaced by a fake (as the tests'
   `reader_tutor_fakes.reader_ctx` does), one `companion.ask` per surface (`reader`, and `desk` on a desk made through
   `desk.apply`), polled to `done`; the `companion_exchange_context` row and the exchange's `question_event_spans`
   rows equal to `rebuild_question_event_spans` on the copy; a cancel while held.

## After the first landing attempt (orchestrator's merge of main)

Running the RD3a files with the structure, identity and fence tests at `-n 2` showed one teardown error in six runs.
The cause was two background writes from the gap-reading worker, not only a leftover job thread: a late decision
record from the post-attempt worker, and the search fixture's hand-seeded `tutor_question` gap colliding with the
pipeline's own row for the same question. Every test now makes its contexts through a `workbench` fixture that
releases held fakes, closes the context, joins every polled job and background thread and fails the test naming any
still alive; the search fixture waits for the gap queue to drain before seeding and reading; `BackgroundJobs.close`
logs jobs still running after its bounded join. The combined set ran 10 times at `-n 2` and the two RD3a files 10
times at `-n 1`, all clean.


## Fix round (backend): the RD3 adversarial review (Codex Astra, 2026-11-23)

Branch `reader/rd3-fix-backend` from main `c8ef04e6b3` (RD3b, RD4a and mvp-0.68 landed). The backend half of the one
fix round: findings 1, 2, 8, 9, 10, 16, 18, 19 and the backend side of 7 and 13. Each has a fail-first test in
`tests/test_reader_rd3_fix_backend.py` and a ledger row (`RD3-<finding>`; ids follow the review's numbers so the
frontend half's rows join the table without a clash). No migration, no algorithm tag, no prompt change, no config key.

| # | What was wrong | What changed |
|---|---|---|
| 1 (blocker) | Jobs and records lived per context: after a vault switch, vault A's job id answered in B, a repeated id consulted A's record, and `load()` never ended the epoch | Jobs and records keyed by `polled_jobs.vault_key(ctx)` (the open vault, resolved), checked on every poll, repeat and cancel; `SidecarContext.load` cancels the background epoch on a switch (before the old vault's map builds stop), so A's job sends nothing more and ends `interrupted`; `PolledJob.live()` is false from then on and gates its completion (below) |
| 2 | An answer finishing after `close()`'s bounded joins restarted the post-attempt worker (the gap notification) and queued prefetch work | `reader.reader_ask_reply(live=...)`: with the job's epoch closed it queues the gap reading in the question's own vault without waking the context's worker (`learner_gaps.queue_tutor_question_gap(wake=False)`) and queues no prefetch. The exchange is kept. `reader.ask` passes nothing and is unchanged |
| 8 | The context row was written after the whole generation: failed or cancelled-before-sending questions had no desk; a failed write was swallowed | `tutor_qa.ask_question(on_question_recorded=...)`, passed through `reader_dialogue.ask` and `reader.generate_reader_answer`: called with the question's id right after its row and passages are written, before the model call. The companion's writer records the context then (and notes `question_event_id`, so polls expose it at once). A failed write is retried at the job's end and on every later poll; the poll says `context_recorded` (null before a question exists, false while a write is pending). Two keyword parameters, defaulting to none: no prompt or behaviour change for any other caller |
| 9 | Request-id records were evicted with results (1,024), so a resent old id asked again, even with other input | Every admitted client id is remembered for the sidecar's life in records apart from the kept results (its params, status, notes); a repeat of a dropped one reads `expired`, other input is `request_reused`. Full (10,000 per registry), new ids are refused (`request_ids_full`) rather than an old one forgotten. Search ids are the server's: that registry keeps records of recent jobs only (1,024), as before |
| 10 | No bound on running jobs; finished results pruned only when another job started | At most four jobs run per registry (`jobs_busy`, retryable; a search's meaning pass reports itself unavailable with that reason instead); results beyond 64 are pruned as each job finishes |
| 16 | A nested recorder (query embedding, rewrite) replaced the job's receipt observer | Every root receipt started on a job's thread carries `owning_job: "<kind>:<job_id>"` in its `budget_json` (`execution.annotate_calls`), whoever records it; the nested recorder still owns its row, so there is still one row per call |
| 18 | A newer same-desk search superseded only when it started a job itself | `search.everything` supersedes the desk's running search before any return (a pads-only or too-short search included) |
| 19 | The notes group's `more` was read from rows already cut to twelve | `more` from every match, then the cap |
| 7 (backend) | Note results carried only `panel: notes` | A Reader note or highlight: `ref` its source, `target {note_key, annotation_id, span_id}`; a capture note: `ref` the notes panel, `target {note_key, capture_id}`; rows say `note_ref_kind`. `handlers/notes.search_vault_notes` returns `{hits, basis, meaning}` with each hit's reading and passage (read back through the notes' own module) |
| 13 (backend) | An unrun notes meaning search came back as an empty success; one group's failure failed the job; the job's poll lost the groups with no meaning search | Each meaning group has `status` `ok`, `unavailable` (the retrieval's own reason: the query not embedded, the index unreadable, no note embedded yet) or `failed` (that group only), and `coverage` when partial; `notes.search`'s meaning mode adds `meaning {status, reason, covered, total}`; `search.job` carries `unavailable` |

Also: the cancel gate counts the requests it admits, so the poll says `sent` (a cancel after a request went cannot
unsend it; review 15's backend half), and `kept` now means the cancelled job's answer was recorded (the question id
alone is known early since finding 8).

**Contract changes for the frontend worker** (`apps/learnloop-tauri/src/api/dto.ts`; no `client.ts` call changed):

1. `CompanionAskJobDto.sent?: boolean`: a model request of the job was sent; render "stopping" rather than "nothing
   was sent" when true.
2. `CompanionAskJobDto.contextRecorded?: boolean | null`: null before the question exists, false while a failed
   context write is retried (each poll retries).
3. `CompanionAskJobDto.questionEventId` is set as soon as the question is recorded (before the answer; also on a
   failed or cancelled job). `kept` is true only when a cancelled job's answer was recorded.
4. New `companion.ask` errors: `jobs_busy` (retryable; four asks already generating) and `request_ids_full`.
5. `SearchRowBase.target` may hold `noteKey`, `annotationId` (with `spanId`) or `captureId`; a note row has
   `noteRefKind` (`annotation` | `capture`); an annotation note's `ref` is its source (`kind: "source"`), a capture
   note's the notes panel.
6. `SearchGroupDto.status` adds `unavailable` and `failed` (meaning groups), each with `reason`; `coverage` may come
   on the notes meaning group too.
7. `SearchJobDto.unavailable?: {group, reason}[]`: the groups with no meaning search, on every poll; a stale job id
   whose record says cancelled reads `cancelled`.
8. A poll, repeat or cancel after a vault switch does not find the other vault's job (`job_not_found`).

`sent`, `contextRecorded` and `unavailable` are optional in the types only so the frontend's fixtures still
typecheck; the sidecar always sends them.

**Fail-first.** Each fix was broken on purpose (one line, by the scratch script), its tests run, and the file
restored from git (`git status` clean after each):

| Broken | Tests | Result |
|---|---|---|
| `vault_key` returns "" (no vault scope) | `test_a_job_is_found_only_in_the_vault_it_was_started_in` | 1 failed (DID NOT RAISE `job_not_found`) |
| no epoch cancel in `load` | `test_a_vault_switch_ends_the_jobs_epoch_before_its_request_is_sent` | 1 failed (the job finished, no error) |
| `awake = True` (no live gate) | the stale-completion and after-close tests | 2 failed (`{'prefetch': 1, 'worker': 1}`) |
| no `on_question_recorded` | the failed-answer and cancelled-before-sending tests | 2 failed (no context row) |
| no retry on poll | `test_a_context_write_that_failed_is_retried_and_reported_until_it_lands` | 1 failed (`False is True`) |
| records dropped with results | `test_a_request_id_is_remembered_after_its_result_is_dropped` | 1 failed (DID NOT RAISE `request_reused`) |
| no running bound | `test_running_asks_are_bounded` | 1 failed (DID NOT RAISE `jobs_busy`) |
| no prune on completion | `test_results_are_pruned_as_jobs_finish_not_only_when_the_next_starts` | 1 failed (`2 == 1`); its first version passed with the break (the next start pruned), so it was rewritten to run two jobs at once |
| no `owning_job` annotation | `test_a_receipt_a_nested_recorder_owns_still_names_the_job` | 1 failed (no `budget_json`) |
| no supersede before the returns | `test_every_newer_search_from_the_desk_supersedes_the_running_one` (2 cases) | 2 failed (the old job `done` with groups) |
| `more` after the cap | `test_more_notes_than_the_group_shows_says_there_are_more` | 1 failed (`False is True`) |
| every note row `panel: notes` | `test_a_reader_note_opens_at_its_passage_and_a_capture_note_names_itself` | 1 failed |
| no unavailable branch (notes) | `test_an_unrun_search_by_meaning_is_said_per_group_never_shown_as_nothing_found` | 1 failed (`KeyError: 'reason'`) |
| no per-group catch | `test_a_group_whose_search_by_meaning_fails_says_so_and_the_other_group_still_answers` | 1 failed (the whole job `failed`) |

**Commands and results** (after merging main `ba7884c102`; each pytest run `-n 1 -m "not arc_close"` through the
scratch wrapper in a 3G `systemd-run` scope, one at a time):

| Command | Result |
|---|---|
| `tests/test_reader_rd3_fix_backend.py` | 18 passed |
| the three RD3 files (`test_reader_rd3a_companion_ask.py`, `test_reader_rd3a_search.py`, `test_reader_rd3_fix_backend.py`) five times | 42 passed in each run |
| `scripts/affected_tests.py --files <the 10 changed src files>` | 984 files (more than 150) |
| the 266 of them whose names match `reader|ask|tutor|companion|search|notes|rd0|rd3|rd4|desk|text_gap|learner_gap|gaps|sidecar|context|close|switch|library|mobile|phone|prefetch|plan_first|one_ai_ok|question|model_call|receipt|load|vault_open|rw1|rw4|ca2|ca3|ca6|learner_blindness|protection_surface|explorable`, in seven chunks of at most 40 | 4,425 passed, 9 skipped, 1 xfailed, 1 error: the teardown error of `test_mobile_v3_carried.py::test_keep_going_on_a_finished_plan_commits_its_override_with_the_extension` (a post-attempt worker thread past its grace while the machine logged `database is locked`), which is ledger row L2-1, open before this round; the file alone, three runs: 5 passed each |
| identity pins, structure ratchets, RD0 fences, effective defaults, CLI snapshot, kill switches, sqlite copies, mobile allowlist, desktop RPC contract, notes-never-read, public tip guards | 790 passed |
| `tests/test_architecture.py` alone / `tests/test_test_layout.py` alone | 18 passed / 3 passed |
| `uv run ruff check` / `uv run lint-imports --no-cache` | All checks passed! / Contracts: 52 kept, 0 broken. |
| `uv run python scripts/check_gate_partition.py` | collected 33452: landing 33386 + arc_close 66 |
| `db_validate_reference.py` | exit 1: 14 config notes cite line numbers in `context.py` and `reader_dialogue.py` that this round's inserted lines moved ("cites unrelated source line"); the landing's regeneration of the vault references rewrites them (the brief leaves that to the landing). No database note is affected (no migration) |
| `npx tsc --noEmit` (`npm run typecheck`) / `npx vitest run --maxWorkers=2 src/api` | exit 0 / 4 files, 57 tests passed |

No identity pin, effective default, CLI snapshot or kill switch moved; the structure ratchets hold
(`handlers/reader.py` stays at 3026 lines).
