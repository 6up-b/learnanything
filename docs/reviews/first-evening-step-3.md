# The first evening, step 3: question work owned per topic

Step 3 of the stage "The first evening, finished" (the design's §2 "Once per topic, including the later finish"
through "Cost when the learner abandons the reading", §5's row "Partial first sets and topic claims", §6's row 3
and §8's points on claims, checkpoints and legacy work). A finished section's question work is now claimed per
topic, with one durable claim and its own checkpoint scope per topic, so that step 4 can claim the topics a learner
has read before the section is finished. **The trigger does not change**: work starts only when a section is
finished (desktop, phone-deferred, waiting-for-build and the owed-work drain, exactly as before), the request bytes
are those the section job sent, and nothing reads `reader_seen_spans` or `reader_section_ends`. Branch
`ux/first-evening-topic-work` from main `5508b1a9bb`.

No algorithm tag, no config key, no kill switch, no prompt change, no frontend change.

## Judgment calls to read first

1. **A wave's request is the section job's request.** One finish claims the topics nobody owns and queues *one*
   batch for them (one authoring part per topic, each applied before the next, as UX-37/UX-40), whose payload is the
   section job's (`learning_object_ids`, `reason = reader_section_completed:<section>`, the bundles of exactly those
   topics) plus `topic_keys`. The bundles of a set of topics are the concatenation of each topic's own (each topic's
   are built from its own citations alone; pinned by `test_reader_progression.py`), so for a section none of whose
   topics is owned the request is byte for byte the section job's (proved by digest, below). Each topic's *row*
   keeps only its own bundles; its frozen request (under its own scope) keeps the wave's, as asked.
2. **A topic's key is its own: `topic_questions_key(topic, its own bundles)`.** Not the wave, not the section, not
   the model settings. It is computed once, at the claim, stored on the row and in the batch payload, and read from
   there ever after; a run never recomputes it. The model settings stay in every answer checkpoint's key (unchanged),
   so a settings change re-asks only what has no saved part: a topic's saved request and prepared part are reused
   across it (a section job's key, which hashes the settings, made a settings change rebuild the whole section).
3. **The claim, the stamp's move and the batch are one transaction** (`Repository.atomic()`, `BEGIN IMMEDIATE`). The
   enqueue records into it and starts nothing (`enqueue_practice_expansion(..., start=False)`); the caller starts the
   queue after the commit (`run_queued_work()`), because a foreground queue started inside would run model calls with
   the write lock held. In the sidecar the claim runs on **the queue's own repository** (`ctx.ingest_jobs.repository`):
   after a same-vault reload the context holds another `Repository` instance, whose transaction the queue's insert
   would not join (it would wait for the claim's own lock). `ENQUEUING` is therefore no longer written; it is still
   read (a section job's process that died between its two writes left it).
4. **Section jobs from before are indexed at claim time, not by the migration.** Before every claim, every
   `practice_expansion` job with a section reason and no `topic_keys` (any state: queued, running, failed, held,
   finished, cancelled) has its payload topics recorded as `owner = section_job`, `state = legacy`, with its batch,
   job, section (from the stamp that names its batch, else its bundles), bundles and part proposals; a later claim
   refreshes those proposal references for the same job. The job, its payload, key, `:requests` snapshot, parts,
   retries and stamp are untouched. Indexing in code also covers a job that was still being queued when the
   migration ran.
5. **"Once per topic" changes three rare cases, by design.** A topic owned by another section's work (new or old),
   including one held for review or failed there, is not written again when a second section citing it finishes.
   Before, the second section's job wrote it again (a duplicate set while the first was running, or a fresh set after
   a held or failed one). Such a second section whose every topic is owned elsewhere is `topic_managed` with no work
   of its own; its reply says `enqueuedGeneration: false` (the Reader says "done", not "writing"), and Today lists it
   under `none_needed` (its topics are reported under the section that claimed them).
6. **Later waves are judged with earlier waves' applied rows.** A topic job passes the proposals of the same
   section's topic work in other batches as `applied_patch_ids`: UX-37's rule (applied rows win, a new conflict is
   refused) across waves. No step-3 trigger makes a second wave of one section; `claim_section_topics(...,
   from_stamp="topic_managed")` is the seam step 4 uses, and the test drives it directly.

## Commits

| Commit | What |
|---|---|
| `b6c4ba0bb7` | Migration 257, its table role and AD class, the head fixture upgraded in place, earlier migrations' diffs |
| `be5a34cf1e` | Topic work: the claim, legacy indexing, topic-scoped checkpoints, the job, the sidecar, Today's facts, the pin, tests |
| (last) | This record |

## The table and its role; the migration

`257_reader_topic_question_work.sql` (the next free number in `migrations/` when written; 256 was the head): one
table `reader_topic_question_work`:

| Column | What |
|---|---|
| `id` | the claim's id |
| `learning_object_id`, `purpose` | **the identity**, `UNIQUE`; `purpose` `CHECK IN ('reader_first_set')` |
| `owner` | `topic` (work this row owns) or `section_job` (a topic a section job from before named) |
| `source_id`, `extraction_id`, `section_id` | the origin: where the claim was made |
| `trigger_event` | `section_finished` (the only value written) or `part_read` (admitted for step 4, written by nothing); NULL for a section job's topic |
| `passage_ids_json`, `source_refs_json` | the topic's own frozen grounding (its bundles and their span ids) |
| `requested_count` | what the plan asked for the topic when claimed (`min(3 − existing, 3)`, the existing target) |
| `model_settings_json` | the settings of the first run (kept from then on) |
| `work_key` | the topic's checkpoint scope |
| `batch_id`, `job_id` | the batch queued with the claim and its job (a section job's for `section_job` rows) |
| `proposal_ids_json` | the proposals written for the topic |
| `state` | `queued`, `running`, `written`, `held`, `failed`, `not_needed`, or `legacy` (exactly the `section_job` rows: their job's state is theirs) |
| `error`, `claimed_at`, `updated_at` | |

`CHECK`s: `owner = section_job` iff `state = legacy`; a `topic` row has a trigger, a key and a batch. Indexes on
`(extraction_id, section_id)`, `source_id`, `batch_id`. No foreign keys (the stamp and batch columns have none
either). No backfill.

- **Role: `WORKFLOW`** (`db/table_roles.py`), as `reader_section_progress` whose stamp points at it: never cleared by
  a rebuild, outside the dataset export and adjudication evidence. **AD: `DENIED`**
  (`adaptive_difficulty/protected_tables.py`); columns classed (`column_classes.py`; the bundles and the error as
  content).
- **Head fixture** (`fixtures/migration_head/`, README section added): a backup-API copy of the tracked file
  (`learnloop.db.copies.backup_database`) in the scratch directory, `apply_migrations` under
  `upgrade_allowance(UPGRADE_SCRATCH_COPY)` applied `[257]` only; `wal_checkpoint(TRUNCATE)` `(0, 0, 0)`,
  `journal_mode=DELETE`, `integrity_check` ok, `foreign_key_check` empty, no companion files; the tracked file removed
  and the copy written into its place with `backup_database`; header bytes `01 01`. Compared with the 256 file: six
  objects added (the table, its two autoindexes, three indexes), no definition changed, only `schema_migrations`'s
  rows changed (243 → 244 rows, gains 257).
- **Earlier migrations' "nothing else changed" diffs**: the 17 files that admit `SEEN_SPANS_ADDED_OBJECTS` now also
  admit `TOPIC_WORK_ADDED_OBJECTS` (`tests/reader_topic_question_work_migration_helpers.py`), beside it (`-` in a
  subtraction, `|` in a union), one import line each (function-local in `test_ad23_migration.py` and
  `test_help_assist_work_md_migration.py`, as theirs are). No other assertion changed.
- New `tests/test_reader_topic_question_work_migration.py`: role and AD class; the head holds it empty in rollback
  mode; a vault one below gains exactly the six objects and its `reader_section_progress` and `ingest_jobs` rows are
  unchanged; one claim per topic and only the known purposes, triggers, owners and states.
- The two database reference scripts: run, output not committed (the landing regenerates), results below.

## The stamp `topic_managed` and every reader of it

`SECTION_TOPIC_MANAGED = "topic_managed"` (`db/stores/reader.py:55`; `section_generation.TOPIC_MANAGED`): the section's
question work is its topics' claims, each naming its batch. Not a batch id, not "finished". Every reader of
`reader_section_progress.generation_batch_id`, at this branch:

| Where | What it does with `topic_managed` |
|---|---|
| `src/learnloop/reader/section_generation.py:196-202` (`claim_section_topics`) | Writes it: compare-and-set from NULL (`mark_section_generation`) or from the stamp read (`swap_section_generation`), inside the claim's transaction; `from_stamp = topic_managed` adds topics without moving it. |
| `src/learnloop/reader/section_generation.py:261-265` (`start_section_questions`'s `move`) | Moves only to `waiting_for_build` / `none_needed_after_build` as before; never from `topic_managed` (no caller passes it). |
| `src/learnloop/reader/section_generation.py:162` (`_stamped_section`) | Reads stamps equal to a section job's batch id, to find that job's section; never matches `topic_managed`. |
| `src/learnloop_sidecar/handlers/reader.py:2154` (`reader.mark_section_progress`) | `generation_batch_id is None` gates a first finish: `topic_managed` is non-NULL, so a second finish starts nothing. |
| `src/learnloop_sidecar/handlers/reader.py:2227` | `waiting_for_build` compares to `WAITING_FOR_BUILD` only: false. |
| `src/learnloop_sidecar/handlers/reader.py:2052` (`_progress_payload`, `reader.get_progress` and the progress reply) | Passes the string through as `generationBatchId`; the reply's `batchId` is the batch queued for the claimed topics. Desktop (`api/dto.ts:7337`) and phone (`read/ReaderScreen.tsx:248`) carry it without reading it. |
| `src/learnloop_sidecar/server.py:189` (`_reported_batches`) | Reports the string as a batch id to `plan_fallback.relay_batch_offers`, which finds no offer for it (as for `waiting_for_build` today); the reply's real `batchId` is reported beside it. |
| `src/learnloop_sidecar/section_questions.py:67` (`drain_owed_section_questions`) | Reads only the `OWED` stamps; `topic_managed` is not owed. |
| `src/learnloop/content/pipeline/jobs.py:3514-3515` (`start_waiting_sections`) | Reads only `waiting_for_build` / `none_needed_after_build` rows; claims through `claim_section_topics`. |
| `src/learnloop/db/stores/reader.py:1330` (`deferred_section_generations`) | Called only with owed/waiting/none-needed stamps. |
| `src/learnloop/content/pipeline/add_source.py:2688-2709` (`reading_questions`, Today's facts) | `topic_managed`: aggregates the jobs of the section's own claims (owner `topic`, origin this reading and section), one per batch, with the same per-job logic as a section job's; with no claim of its own: `none_needed`. **Never passed to `ingest_jobs_for_batch()`.** |
| `src/learnloop/content/pipeline/reread.py:303-311` (`carry_progress`) | Carries the stamp as it is (so the new reading's section never starts again); the claims stay with the reading they were made on, and `reading_questions` reports claims made on an earlier reading of the book, under their section's label, after the current reading's sections. |
| `src/learnloop/db/stores/reader.py:1282` (`carry_reader_section_progress`) | `COALESCE` keeps an existing stamp; carries `topic_managed` like any stamp. |
| `src/learnloop/adaptive_difficulty/protected_tables.py:482`, `column_classes.py:598` | Column classification only (AD never reads the stamp's value). |

`SECTION_ENQUEUING` is no longer written (its comment says so); `set_section_generation_batch` had no caller left and
is removed.

## The claim transaction

`claim_section_topics(repository, extraction_id, section_id, lo_ids, refs, enqueue, from_stamp, ...)`, in one
`atomic()`:

1. move the stamp to `topic_managed` (compare-and-set; a lost move returns None, nothing else happens);
2. index section jobs (above);
3. read the claims of `lo_ids` (either owner); the rest, in reading order, are new;
4. none new: return None (the stamp stays `topic_managed`);
5. compute each new topic's key from its own bundles; `enqueue(new, reason, the new topics' bundles, keys)` records
   the batch and job (`topic_keys` in the payload);
6. insert one row per new topic (plain `INSERT`: a topic claimed meanwhile fails the whole transaction).

Any exception (the queue's included, or one after it queued) rolls back the stamp, the rows and the batch. Callers:
the sidecar's finish and owed-work drain (`section_questions.start_section_questions` → `section_generation.
start_section_questions`, then `run_queued_work()`), and a build's `start_waiting_sections` (its `ctx.enqueue_batch`
joins the transaction).

## The job

`handle_practice_expansion`: a payload with `topic_keys` is topic work (`_TopicWork`); one without is a section job,
handled exactly as before (`section_questions_key`, `:requests`, `:part:<i>`, its completed checkpoint).

Topic work: rows of its batch go `running` (first run's model settings kept); `generate_post_probe_practice_proposal(
..., topic_scopes=..., applied_patch_ids=earlier waves)` builds one part per topic as before, and
`generate_authoring_proposal(..., part_scopes=...)` freezes each part's request under `<topic key>:requests`
(`{"context", "parts": [that part]}`) and saves its prepared proposal under `<topic key>:part:0`, through the same
`ModelCheckpoint`s and `_apply_authoring_parts` (receipt keys passed in; a section job's are `<section key>:part:<i>`
as before). Each part report also moves its row: `written` (all rows applied), `held` (written, rows pending for a
look), `failed` (with the error: a model failure, or a refused row), `not_needed` (the plan found nothing). The
result names `patch_ids` as a section job's does.

## The key scheme

| Key | Kept / new | Pinned |
|---|---|---|
| `section_questions_key(client, topics, refs, reason)` and `<it>:requests`, `<it>:part:<i>`, its completed checkpoint | **kept**, for every section job (old payloads), unchanged | `section_questions.work` (unchanged) |
| authoring / repair answer checkpoints (`_authoring_checkpoint`: rendered prompt, schema, settings) | **kept**, shared by both | `section_questions.answer` (unchanged); the one-topic request-bytes pin unchanged |
| `topic_questions_key(topic, own bundles)` = `content_key({"purpose": "reader_first_set", "topic", "source_refs"})`; `<it>:requests`, `<it>:part:0` | **new**, stored on the row and in the payload | **new** `reader_topic_work.work` = `2205315f…ae12367` (`tests/identity_pins_helpers.py`; `--write` added only this line) |

No existing pin, golden or snapshot moved.

## What resumes and what never repeats

- A section job from before (queued, running, failed, held, finished) runs, retries and resumes as before, with its
  own key and frozen request; its topics are never claimed for new work.
- A failed topic resumes its original batch (`resume_batch`, Today's existing Try again with the batch as
  `resume_id`) with its frozen request: same bytes after an unrelated vault edit; its written siblings are not asked
  or applied again.
- A crash after an apply resumes the same proposal ids; the applied part is neither asked nor applied again.
- Work claimed before a process died (committed, never started) runs once on the next start.
- A held topic stays held; nothing commissions it again (no top-up).
- A topic owned through another section or book is never claimed again.
- Not established (the design's §8): exactly-once provider billing across a death between the provider's
  acceptance and the answer's checkpoint.

## Tests, with fail-first evidence

Fail-first run against unchanged production (the migration file present, the head fixture not upgraded), the four
files: **18 failed, 34 passed**. Failures: `ImportError: cannot import name 'claim_section_topics'` (the claim
tests), `TypeError: enqueue_practice_expansion() got an unexpected keyword argument 'start'` (the section-job test),
`'batch_…' == 'topic_managed'` (the two sidecar finishes), an empty claim set (the build-applies test), `KeyError:
'reader_topic_question_work'` / `no such table` (migration). Two targeted fail-firsts on the implementation with one
piece taken out (then restored): without the earlier waves' applied rows, the later-wave test fails (the duplicate is
applied: two live questions); without legacy indexing, the section-jobs test fails (`KeyError: 'lo_topic_b'`: their
topics are claimed again).

`tests/test_section_question_parts.py` (synthetic sections, the house `Writer` fake, calls counted):

- `test_a_finished_sections_topics_are_claimed_once_each_and_written_with_the_section_jobs_bytes`: rows, stamp,
  proposals; **every request digest equals the section job's** on an identical vault, and the same live questions.
- `test_a_topics_key_and_grounding_are_its_own_in_whatever_wave_claims_it`
- `test_a_queue_that_fails_takes_the_claims_and_the_stamp_back` (a failing queue, and one that queued then failed: no
  rows, no stamp, no batch)
- `test_work_claimed_before_a_crash_runs_once_when_the_queue_runs_again`
- `test_a_crash_after_a_topics_apply_resumes_its_proposal_and_asks_nothing_twice`
- `test_two_claims_at_once_give_each_topic_one_owner` (two hosts, two `Repository` instances, the second claim
  arriving while the first transaction is open)
- `test_a_topic_held_for_review_stays_held_and_is_not_written_again_for_another_section`
- `test_a_failed_topic_resumes_its_own_batch_and_frozen_request_and_no_other_section_takes_it`
- `test_two_sections_and_two_sources_citing_a_topic_write_it_once`
- `test_a_later_wave_of_a_section_is_judged_with_the_questions_its_earlier_wave_applied`
- `test_section_jobs_from_before_topic_work_keep_their_keys_and_proposals_and_own_their_topics` (failed, held and
  queued section jobs; the queued one completes under its section key; the failed one resumes with its first request's
  bytes and its proposals; re-indexing names what they wrote since)

`tests/test_section_done_before_build.py` (the house book through the sidecar):
`test_a_finished_section_claims_its_topics_once_and_today_reads_their_work_as_before` (reply, rows, payload keys; Today
writing with progress, then stopped with `resumeId` = the batch; finishing and reading again claim nothing) and
`test_a_section_finished_before_the_build_and_another_citing_its_topic_claim_it_once` (claimed when the build applies,
`section_finished`; another section citing the same topics claims nothing and is `none_needed`).

`tests/test_reader_progression.py`: `test_a_sections_bundles_are_each_topics_own_so_a_claimed_topic_keeps_its_
grounding_in_any_wave` (a preservation guard: passes on main too).

**Assertions changed**, each because the stamp of a section that claims work is now `topic_managed` and its claims
name the batch the stamp used to name:

- `test_section_done_before_build.py::test_a_section_finished_before_the_build_applies_gets_its_questions_when_it_does_once`:
  `stamp == batch id` → `stamp == "topic_managed"` and the claims name that batch, `section_finished`, owner `topic`.
- `test_empty_first_build.py::test_try_again_after_an_empty_build_writes_the_owed_sections_questions`: the same.
- `test_mobile_v4_reader.py::test_a_section_finished_on_the_phone_builds_its_questions_on_the_desktop_once`: the same;
  and its fake candidates now give each section a topic of its own (`lo_svd_definition_<section>`): with one topic
  for both, the desktop's second section would rightly queue nothing (the topic is the first's), and the line it
  checks ("a completion on the desktop is as before") needs a topic nobody owns.

The full first-day journey (`tests/test_first_questions_today.py`, `test_first_questions_arrive.py`) is unchanged and
passes; their sections are stamped with section jobs, the legacy representation.

## What was run

Every Python run through the scratch wrapper (empty home, config and Codex dirs); every pytest run from a script that
refuses an empty target list, `-n 1`, in a 3 GB scope, one at a time.

| Command | Result |
|---|---|
| The four new/extended files (fail-first, unchanged production) | 18 failed, 34 passed |
| The same, final code | 52 passed |
| Migration group: the new migration test, `test_reader_seen_spans_migration`, `test_migrations`, `test_table_roles`, `test_tracked_fixture_databases`, `test_ad_protected_tables` and the 17 diff files | 139 passed (+ 12 after an import-indent fix in two of them) |
| The brief's name filter (57 files: section_question, section_done, reader_progress, first_questions, add_source, ingest_job, migration, table_roles, tracked_fixture, reader_seen) united with the 65 test files naming the code changed (`practice_expansion`, `reader_section_completed`, `reading_questions`, `question_parts`, `generate_authoring_proposal`, `generate_post_probe_practice_proposal`, `mark_section_progress`, `carry_progress`, `source_status_line`, `start_waiting_sections`, `section_generation`, `reader_section_progress`, `part_requests`): 111 files, six chunks of at most 19, `-m "not arc_close"` | 268 passed; 247 passed; 313 passed (5 warnings); 537 passed, 3 skipped; 8,647 passed; 186 passed |
| `scripts/affected_tests.py --files` the ten changed sources | 1,348 files (over 150: the filter above was run instead) |
| `test_identity_pins` | 345 passed, 1 failed (the new pin, unrecorded) → `--write` (one line added) → with the six guards below: 401 passed |
| `test_structure_ratchets`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies`, `test_public_tip_guards` | 401 passed, with `test_identity_pins` (one run) |
| `test_test_layout` alone | 3 passed |
| `test_architecture` alone | 18 passed |
| `ruff check` | All checks passed! |
| `lint-imports --no-cache` | Contracts: 44 kept, 0 broken |
| `scripts/check_gate_partition.py` | collected 32158: landing 32093 + arc_close 65 |
| `db_generate_reference.py`; `db_validate_reference.py` | `table_notes` 400, `uncommitted_inputs` 0; `"errors": []`. Their output (the new table note, the catalog, four table notes, `_generated.md`) was restored, not committed: the landing regenerates |

An earlier run of the first 37 files was cut off (exit 137) when the session running this work ended; it was
rerun whole, in smaller chunks, and only the reruns are counted.

## What a walk must check

With the patient first-day persona and a learner who stops at 60 % (the design's §7 row 3), on the real desktop and
the phone:

1. Finishing a section still writes its questions one topic at a time; Begin appears once the first topic applies;
   "Writing questions: k of N topics finished" counts as before. `reader_section_progress.generation_batch_id` reads
   `topic_managed`; `reader_topic_question_work` has one `topic` row per topic with the batch.
2. Try again on a stopped topic resumes the same batch and asks only that topic.
3. A vault with a section job from before (finished, failed or held): it is untouched and resumes as before; its
   topics appear as `section_job` / `legacy` rows after the next finish, and a section citing them writes nothing
   for them.
4. A section finished on the phone is written on the desktop as before.
5. The 60 % learner sees no difference (no partial questions yet).
6. The sidecar log: no "database is locked" around a finish (the claim's transaction), also after the shelf has
   reloaded the vault.

## What was not verified

- No app, browser, server, phone or real model ran (the rules); the real queue ran only in foreground hosts and one
  two-host thread race. The background worker starting after the claim commits is read, not run.
- A reread of a book with `topic_managed` sections: read, not run (no test drives `carry_over` with claims).
- Provider billing across a death between acceptance and checkpoint (the design's §8).
