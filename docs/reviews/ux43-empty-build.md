# UX-43: a first build with no topic is not a finished build

Ledger row UX-43 (`refactor-bug-ledger.md`). Branch `fix/ux43-empty-build`, on the UX-42 branch tip (`0b1fcf13da`).

## What the walk measured

A first web chapter (135 passages, one section), added through Add, so built "as you read" (practice items are
written later, from reading progress). On the live route the build's synthesis call normally answers with about
11,000 output tokens: 6 to 9 learning objects, each with a blueprint and recipes. In this walk it answered with
1,062 output tokens: 8 concepts, 1 facet, 0 learning objects, 0 blueprints, and a summary ending "Practice items are
deferred to reading progress." The prompt's rule for this mode (`content/synthesis/ai_contracts.py`, rule 1: "When
`brief.practice_items` is `"as_you_read"`, output an EMPTY `practice_items` array: still author concepts, facets,
learning objects, blueprints with full recipes, and criteria-bearing structure") was not followed: the model dropped
the learning objects too. The proposal was accepted, the build job read "Completed", the section the learner had
finished was stamped `none_needed_after_build`, no question was ever written, and for the next fifteen minutes Today
said "Nothing planned for today" and told the learner to finish the section or its quick check, while the Reader
said the section was done. "Build questions for the whole article at once" answered that questions are written when
a section is finished. The persona gave up.

## Step 0 (read from the code, before any change)

### a. What a bootstrap answer passes through, and which builds may legitimately hold no topic

A bootstrap synthesis answer (`source_set_synthesis.py`, `finish_synthesis_run` → `_run_synthesis` →
`_gate_and_persist`) passes, in order:

1. **The wire schema** (`SourceSetSynthesis`, `ai_contracts.py`): every list may be empty; the only shape rule on a
   blueprint is `recipes` with at least one recipe (`min_length=1`). An answer with no `learning_objects` and no
   `blueprints` is valid.
2. **Size checks** in `_run_synthesis` (`_SynthesisBudget.check_pass_output`, `check_shard_output`,
   `check_merged_output`): the answer's size against the run's ceilings. A short answer passes.
3. **The structuring call** (`_structure_merged` → `_model_graph_structuring`): folds same-title concepts and writes
   relations; it reads concepts only.
4. **Normalization** (`normalize.py`): concepts, facets, learning objects (a lost concept anchor is minted, never
   refused), blueprints, practice items (dropped under `as_you_read`, with a review record). Nothing counts kinds.
5. **Client-id collisions** (`_duplicate_client_id_diagnostics`), and **identifiability** (`analyze_identifiability`,
   review findings only).
6. **The synthesis gates** (`synthesis_gates.run_synthesis_gates`; `tests/test_synthesis_gates.py` lists all 18:
   span resolution, scope, unit validity, conflict disposition, lock guard, adequate provenance, criterion target,
   criterion DAG, recipe validity, dependency closure, exam authority, held-out leakage, token truncation,
   practice-exam-only, duplicate ids, dangling edge, near-duplicate facet, identifiability). Every one iterates over
   the proposal's items and judges each item; none asks whether an item of a kind exists. With no learning object
   and no blueprint, `recipe_validity`, `dependency_closure` and the rest have nothing to refuse.
7. **The instrument gates** (`authoring_gates.build_instrument_gates`) over practice-item rows: none here.
8. **The proposal match** (`proposal_match`): an answer equal to a wholly rejected proposal is asked again once.

So an answer with concepts and a facet and nothing else passes every check: each check is per item or per size, and
the one place that says learning objects are owed is a sentence of the prompt. The proposal is persisted and, under
`auto_apply_passing_builds`, applied.

**Which builds may legitimately hold no learning object.** A rule that asks again must not touch these:

| Build | Why it may hold none | The code that shows it |
|---|---|---|
| An append (`APPEND` mode: a new chapter or source into a subject that already has a map) | Told to prefer a provenance link to existing curriculum and to add "at most one" learning object; an append that only links adds nothing new | `ai_contracts.py` append prompt ("prefer a provenance link to existing curriculum; otherwise add at most one focused learning object"); `source_append.py` |
| A bootstrap over a subject that already has a learning object (a rerun of the bootstrap from the Ingest screen or `learnloop synthesize --mode bootstrap`; an automatic build never does this: in `auto` mode it becomes an append) | The subject's topics exist; a rerun that restates or narrows the map can match or settle into it | `jobs.handle_bootstrap_synthesis` → `source_append.subject_has_applied_study_map` ("a subject already carries a live study map once any learning object is scoped to it") |
| A bootstrap under the `narrow_adjunct` authoring preset | Told to "prefer an additive link to existing curriculum, otherwise mint at most one focused learning object" | `brief.py` `NARROW_ADJUNCT_SCOPE`, `ai_contracts.py` rule 1 |
| A bootstrap whose inputs hold no unit with semantic authority (only problem sets, notes, a syllabus, exam material) | No source may mint a claim, so nothing can ground a topic; a syllabus is never inventoried and exam units reach only the assessment profile | `role_authority._MATRIX` (`semantic_contract` False for `problem_set`, `exam`, `notes`, `syllabus`); `_collect_inputs` (exam units to `exam_profile`, scope-only roles skipped, each entry's `semantic_authority`); prompt rule 4 |
| A bootstrap with no inventory at all | No request is sent: `_run_synthesis` returns `call.result_model()` with zero shards | `_run_synthesis`, `if merged is None` |

The brief's example "a source set scoped to `relevant` where nothing is relevant" is not a separate case: `relevant`
is the free-form `brief.scope` that every Add and quick add sends (`quick_add._default_brief`), not a selector. The
units are the chapters the planner chose for the learner to read (exam material withheld, `_choose_scope`), so on an
Add's first build it cannot be told from "the model did not follow its instructions" and is not exempt.

So the line is drawable from facts the run already holds, with no new input: **a bootstrap run owes a topic when its
subject has no learning object yet, its brief is not the narrow adjunct, and at least one of its unit inventories
carries semantic authority.** Every first build through Add is such a run.

### b. What happens downstream of an empty bootstrap

| Where | What happens (code) |
|---|---|
| The job | `handle_bootstrap_synthesis` reports "Study map applied", returns `StudyMapResult.as_dict()` with `mode: "bootstrap"` and `item_counts` holding no `learning_object`; the batch completes |
| `after_auto_build` → `start_waiting_sections` | a section finished while the build ran (`waiting_for_build`) finds no topic citing it (`section_generation_candidates` → `[]`) and keeps waiting |
| The next read of the books (`get_source_library`, `reader.get_progress`, the start: `drain_owed_section_questions`) | `section_topics_settled` is true (the chapter's build completed, applied, nothing pending), the topics are read again from disk, none cites the section: stamped `none_needed_after_build`. A section finished after the build goes the same way at once (`start_section_questions`) |
| The Reader | "✓ Done with this section." (nothing was queued) |
| The status line (`_source_status_line`) | the built book's "Questions for this article come up as you read" (tone `quiet`, no action), with `questions` = `{count: 0, item_ids: [], sections: [], writing: [], waiting: [], failed: [], to_look_at: 0, section_count: 1}`: a `none_needed_after_build` section is skipped (`reading_questions`), so the fact reads exactly like a book with no section finished |
| Today (desktop and the phone's shared sentence, `todayCause.ts`) | no rank (quiet line, no action, no section lists), so it falls to the "built, no section finished" state, chosen by `questions.count === 0`: **"Your first questions come when you finish a section of “…”: finish its quick check, or press Done with this section at its end."** with Continue reading. This is the sentence that told the learner to finish a finished section; its condition reads only `count` |
| "Build questions for the whole article at once" (`source_action build_whole_book`) | `whole_book_state` is `built` (the empty build covers the chapter: `coverage` counts every completed build as built) → the notice **"All of this article is ready for questions. Each section's questions are written when you finish it."**, nothing queued |
| The Library card | "Questions for this article come up as you read" |
| Try again | none offered anywhere; the card's `retry` (`retry_build`) on a completed batch only resumes it, which requeues nothing |

### c. Where a pass's answer is checkpointed relative to its validation

In `_run_synthesis.run_pass` the answer is sized against its ceiling (`check_pass_output`) and then saved
(`checkpoint.save`, a `model_work_checkpoints` row of purpose `synthesis_pass`, keyed by the request key of the exact
prompt and schema, no budget in it). The shard's answer is saved after the shard's size checks
(`save_synthesis_shard_result`, keyed by the shard's first pass key), which on a later run answers the shard before
any pass is asked. The structuring call keeps its own checkpoint. All of this happens inside `ask()`, before
normalization and the gates (`_gate_and_persist`), which judge content. So an empty answer is stored under the very
key a re-ask would send, and a plain re-ask is answered from it at no cost and no new request. A re-ask must first
drop those rows: `_SavedAnswers.discard` (each served shard row and pass checkpoint, deleted only while it still
holds the answer served), the move the rejected-proposal re-ask (`RejectedProposalMatch`) and a gate failure already
make.

## The rule and the request bound

**The rule.** A bootstrap run that owes a topic (`source_set_synthesis.bootstrap_owes_a_topic`: its subject has no
learning object yet, its brief is not the narrow adjunct, and some unit inventory it reads carries semantic
authority) and whose combined answer holds no topic (`holds_a_topic`: no learning object of the answer is named by a
blueprint of the answer, by client id or id, with a recipe) is treated as the model not following its instructions.
Before anything else is done with that answer (no facet-identity judge, no candidate saved for repair, no gates), its
saved rows are dropped (`_SavedAnswers.discard`: the shard row, the pass checkpoint, the structuring checkpoint) and
the same request is sent once more. The second answer is taken as it is, empty or not. The mode field
`asks_again_without_a_topic` is on for `BOOTSTRAP` and off for `APPEND`. The proposal then carries one review record,
gate `asked_again_without_a_topic`, in its gate diagnostics (the synthesis run's `coverage_decisions` and the job's
result), saying the first answer held no topic and the request was sent again.

**Why an identical request.** The first and second requests are byte-identical (the test asserts the two contexts
are equal): same prompt, same schema, same pass key. Nothing in the prompt was wrong (rule 1 already says to author
learning objects and blueprints in this mode), the answer is sampled, and the live route's normal answer to this
very request is 6 to 9 topics; the walk's empty answer was the outlier. Changing the prompt for the re-ask would be a
prompt change (not allowed here) and would move the pass key. Because the empty answer's rows were deleted first, the
second request is not answered from them: it is a real request with its own receipts.

**What the receipts show.** One synthesis run and one agent run for both asks (the agent run's metered usage adds
both answers, drained after each); per ask, the model-call receipts of its pass request (and its structuring
request), so two `model_call_receipts` rows of purpose `source_set_synthesis` with equal `prompt_hash` and
`schema_hash`, different ids and times, the first one's `output_text` the empty answer (the evidence of what was
asked again, which the deleted checkpoint no longer holds); one `model_work_checkpoints` row of purpose `synthesis_pass` at the end, holding the second
answer (the first was deleted); and the review record above in the run's gate diagnostics. The fakes write no
physical receipts, so the receipt rows are read from the code, not a test; the checkpoint row and the diagnostic are
tested.

**The request bound** (logical requests: a request the transport sends once, counting its own transient retries as
one; per synthesis pass of a one-shard build, the first document's case):

| | Before | After |
|---|---|---|
| One handler run of the synthesis job | 1 pass request (2 after a rejected match) | at most 2: the tail asks at most twice, the re-ask and the rejected-match re-ask share those two (each run is still per shard one base pass and at most one span round, and one structuring request per ask) |
| The job's own retry (UX-13, `retries_on_its_own`) | after a failure a fresh try may cure: one more handler run | the same; an empty answer is not a failure (the job completes), so a build empty twice never retries on its own. A failure during the re-ask retries the handler once, whose first ask is fresh (the empty answer was dropped): at most 4 pass requests in all (`test_the_request_bound_with_the_jobs_own_retry`: empty, a timeout, empty, empty = 4, then nothing more) |
| The transport's transient retry (UX-41, plan route `_send`) | each logical request at most 3 physical sends | the same: at most 6 physical sends per handler run, 12 with the job's own retry |
| The learner's Try again | none existed for a completed build | a new build of the empty chapters, with the same bound; never queued without a press (reading on never plans a chapter whose build found no topic: `coverage` puts it in `failed`, which keep-ahead skips) |

On a metered route the re-ask is one more request of the same attempt, held by the attempt's request gate (the
learner's approved amount or the daily cap, when set), as every request is; the build's shown estimate does not
include it (judgment call below). On the plan route it is plan usage, not money.

## States, words and actions

| Where | When | Words | Action |
|---|---|---|---|
| Card line (`source_status_line`) | the latest build completed, applied, nothing pending, and its bootstrap wrote no learning object (`found_no_topics`) | "LearnLoop found no topics to practise in this article" (or "in Ch. 2" when other chapters have topics); tone `problem`; fact `no_topics: true`; details "LearnLoop read it but came back without a topic to write questions from. Try again asks once more; your reading and the sections you finished are kept, and they get their questions once topics are found." | Try again (`source_action retry` → `retry_build`: the empty chapters planned again by `request_auto_build`, never as an approval) |
| Card line, its `questions` fact | any built line, the no-topics line included | new key `none_needed`: labels of finished sections stamped `none_needed_after_build` (or the older `none_needed`) | — |
| Today, desktop (`todayCause.ts`, rank `no_topics` after a stopped build, before a stopped section) | a card line with `noTopics` | "LearnLoop found no topics to practise in “Title”. Try again, or keep reading: the sections you finish get their questions once topics are found." | Try again (the card's retry) · what's sent ▸ · Continue reading (opens the book) |
| Today, the phone (`PlanToday`, the shared `causeSentence` under "Nothing planned for today.") | the same | the same sentence | Keep going (unchanged; the phone offers no retry, as for a stopped build) |
| Today, desktop and phone: the corrected "finish a section" state | before: any card with `questions.count === 0`; now also no finished section with nothing to write (`questions.noneNeeded` empty) | a book whose finished sections had nothing to write: "Nothing from “Title” is up today. More questions come as you finish sections." (the existing none-up state) instead of "Your first questions come when you finish a section of “Title”: …" | Continue reading |
| "Practise for this goal" with nothing ready | the no-topics cause | "Nothing for this goal is ready to practise yet: LearnLoop found no topics to practise in “Title”. …" | Try again · Continue reading |
| Library, "Build questions for the whole article at once" (`whole_book_state` → `no_topics`) | every build of the book found no topic and no other chapter is left | "LearnLoop found no topics to practise in this article, so there are no questions to write from it yet. Try again on its card to look once more." (a notice; nothing queued) | — |
| Library, the same press beside chapters with topics | some chapters have topics, a chapter's build found none | the chapter is left to build, as a failed one is: the press plans it again (with any unbuilt chapters) | — |
| Reader, "Done with this section" on a book whose build found no topic | the section has no topic to write from | "✓ Done with this section." (unchanged: nothing was queued) | — |
| Activity (the job) | twice empty | "Study map applied", completed (unchanged); the result's `gate_diagnostics` has `asked_again_without_a_topic` | — |

## Stamp transitions (`reader_section_progress.generation_batch_id`)

| From | To | Who | When |
|---|---|---|---|
| `waiting_for_build` | `none_needed_after_build` | the read of the books (`drain_owed_section_questions`), unchanged | the empty build settled and no topic cites the section: the stamp is written as before, and is now said (`questions.none_needed`, the card's no-topics line) |
| NULL | `none_needed_after_build` | a completion (`start_section_questions`), unchanged | finished after the empty build settled |
| **`none_needed_after_build`** | **`enqueuing`, then the batch id** | **the build's hook, `jobs.start_waiting_sections` (from `after_auto_build`)** | **new: a build applies and every earlier finished build of the book (not undone) found no topic (`add_source.found_no_topics_before`, the current batch excluded): each such section is decided again from the topics just applied; one with topics citing it is claimed (compare-and-set from `none_needed_after_build`), queued and named in one transaction, as a waiting one is. One with none keeps its stamp** |
| `waiting_for_build` | `enqueuing`, then the batch id | the same hook, unchanged | as before |

The guard against writing twice is UX-31's: every move is a compare-and-set from the stamp read, and only the
winner of the move to `enqueuing` queues anything; the hook claims, enqueues and names the batch in one transaction.

## Code

- `content/synthesis/source_set_synthesis.py`: `bootstrap_owes_a_topic`, `holds_a_topic`,
  `ASKED_AGAIN_WITHOUT_A_TOPIC`; `SynthesisMode.asks_again_without_a_topic` (default off; on for `BOOTSTRAP`); the
  check in `finish_synthesis_run`'s loop, right after the answer is drained and before facet identity.
- `content/pipeline/add_source.py`: `found_no_topics(job)`; `_build_state`'s `no_topics`; `Coverage.empty` (a subset
  of `failed`; an empty chapter is not built, so a press plans it again and keep-ahead skips it);
  `found_no_topics_before`; the card's no-topics line (`NO_TOPICS_DETAILS`); `reading_questions`' `none_needed`;
  `whole_book_state`'s `no_topics` and its notice; `retry_build`'s branch for a build that found no topic.
- `content/pipeline/jobs.py`: `start_waiting_sections` also decides the `none_needed_after_build` rows owed under
  empty builds.
- Desktop: `api/dto.ts` (`noTopics`, `noneNeeded`), `app/todayCause.ts` (cause `no_topics`, its rank, sentence,
  actions, `causeSecondActionLabel`; the finish-a-section condition), `screens/today/TodayPlace.tsx` (Try again and
  Continue reading beside the cause, on Today and the goal line). No new TypeScript file: `desktop_validate.py`'s
  counts do not move. The phone: no source change (it says `causeSentence`).

No prompt, schema, migration, config key or algorithm tag changes.

## What a walk must check

firstq on the live route (a first-day learner, one web chapter, "as you read"). An empty answer cannot be ordered
from the live model, so the walk checks that the ordinary path is unchanged and watches for the empty one:

1. **Ordinary build (must be unchanged).** Add the chapter, read its one section to the end and press "Done with
   this section" while Today says "Getting “…” ready for questions". The build's synthesis is asked once (one
   `source_set_synthesis` receipt for the pass, no `asked_again_without_a_topic` in the job's result), and Today
   goes on to "◐ Writing questions from what you read in “…”…", then "N questions from what you read in “…”. More
   come as you finish sections. [Begin ↵]". The card never says "found no topics".
2. **If the model answers with no topic** (it cannot be ordered; check every build's job result): the result has
   `gate_diagnostics` with `asked_again_without_a_topic`, and the build has two `source_set_synthesis` receipts with
   equal `prompt_hash`, the first with the short answer. If the second answer has topics, step 1's Today lines
   follow, with no press. Removing a built book's learning objects by hand does not reproduce this path: the rule
   judges the model's answer, not the vault.
3. **Still empty after two answers:** the card reads "LearnLoop found no topics to practise in this article" with
   Try again (details: "LearnLoop read it but came back without a topic …"); Today reads "LearnLoop found no topics
   to practise in “…”. Try again, or keep reading: the sections you finish get their questions once topics are
   found." with Try again, what's sent ▸ and Continue reading, and never "Your first questions come when you finish
   a section". The phone's Today shows the same sentence under "Nothing planned for today.". "Build questions for
   the whole article at once" shows "LearnLoop found no topics to practise in this article, so there are no
   questions to write from it yet. Try again on its card to look once more." and queues nothing.
4. **Try again** (Today or the card): the card goes to its working line ("Writing questions for this article"),
   Today to "Getting “…” ready for questions"; when the build finds topics, the section finished in step 1 gets
   "◐ Writing questions from what you read in “…”…" with no further press, then its questions with Begin.
5. **Reading on never rebuilds an empty chapter by itself**: in a book of several chapters whose first build found
   no topic, reading into the next chapter plans only that chapter (keep-ahead), never the empty one again.

## Tests (fail first)

| File | Tests | On the base (`0b1fcf13da`; sources put back with `git show`, restored after) |
|---|---|---|
| `tests/test_empty_first_build.py` (new) | 11. On the synthesis: an empty first answer is asked again once with an equal request, the second (with topics) is taken and only it is kept (the checkpoint), with the review record; two empty answers: two requests, the second taken, and a later run replays the kept empty answer, drops it and asks once (3); the narrow adjunct and a bootstrap over a subject with topics: one request each; `bootstrap_owes_a_topic` and `holds_a_topic` on plain values. On the book (the sidecar, the queue drained by hand, the house fakes): an empty first answer then topics: two requests, the build completes with topics, the finished section's questions are queued; two empty answers: two requests after draining everything, the card's no-topics line with Try again, the section stamped `none_needed_after_build` and listed in `questions.noneNeeded`, the whole-book notice, nothing queued after; the bound with the job's own retry (empty, a timeout, empty, empty: 4, then nothing); a section finished after the empty build; Try again after an empty build that then finds topics: one request, a new build batch, the owed section's questions queued once, never twice on later reads; a later chapter's append that only links: one append request, no re-ask, no no-topics line | 8 of 11 failed: `assert 1 == 2` requests (both synthesis tests, the empty-then-topics build, the twice-empty build), `assert 1 == 4` (the bound), `ImportError` (the pure test: no `bootstrap_owes_a_topic`), `KeyError: 'noneNeeded'` (a section finished after the empty build: its stamp was already `none_needed_after_build` and `enqueuedGeneration` false, the bug), and Try again returned the empty build's own batch (`retry_build` only resumed it). The 3 controls (narrow adjunct, a rerun over a mapped subject, a linking append) pass on both. After the first source commit alone, 4 still failed (the line, the fact, the notice, the owed section) |
| `tests/test_first_questions_today.py` | one assertion extended (below) | — |
| `apps/learnloop-tauri/src/screens/today/TodayPlace.test.tsx`, describe "A book whose build found no topics … (UX-43)" | 4: the sentence with Try again (the card's retry, `sourceAction({sourceId, action: "retry"})`), what's sent and Continue reading (opens the book), never "finish a section" or "Couldn't get"; it outranks another book's "finish a section"; a book whose finished section had nothing to write says the none-up sentence, not "finish a section" (and a book with none finished still does); plain words | 4 of 4 failed (the stopped-build sentence "Couldn't get questions ready for “…”", and "Your first questions come when you finish a section") |
| `apps/learnloop-mobile/src/today/Today.plan.test.tsx`, describe "a book whose build found no topics (UX-43)" | 2: the sentence under "Nothing planned for today."; a finished section with nothing to write never "finish a section" | 2 of 2 failed |
| `apps/learnloop-tauri/src/copy/denyList.test.tsx` | the card lines (two no-topics lines), the cause (with its second action label) and the whole-book notice | the file failed to load (`causeSecondActionLabel` is not a function) |
| `apps/learnloop-tauri/src/components/BookCard.test.tsx` | 1: the card's no-topics line, its Try again sends `retry`, details in plain words | passes on both: the card renders the sidecar's line as it is; the change is the sidecar's |

**Assertions changed, and why.** `tests/test_first_questions_today.py::test_a_built_book_with_no_section_finished_says_none_came_yet`
compares the whole `questions` fact; it now also expects `"none_needed": []` (the fact gained a key; nothing
loosened). No other assertion changed.

## What I ran

Every Python run went through the scratch wrapper (`env -i`, empty `HOME`, `CODEX_HOME` and config dir, `TMPDIR` in
`~/.cache/learnloop-ux43-tmp`) as `uv run --no-sync pytest -q -n 1 -p no:cacheprovider` from a script file that
refuses an empty target list, in a `systemd-run --user --scope -p MemoryMax=3G -p MemorySwapMax=1G`, one at a time.
Every npm/npx run went through the same wrapper with the shared npm cache in a 3G or 4G scope
(`npm ci --offline` first: the worktree had no `node_modules`), vitest with `--maxWorkers=2`.

- The new file on the base sources: 8 failed, 3 passed (above); with `tests/test_first_questions_today.py`: 9 failed,
  30 passed. After the first source commit (`19a3210888`): 4 failed, 7 passed. After the second (`fb277c5137`): 11
  passed.
- After the first source commit: `test_identity_pins`, `test_source_set_synthesis`, `test_synthesis_tail_golden`,
  `test_rerun_proposals`, `test_synthesis_answer_reuse`, `test_first_questions_arrive`: 455 passed (no pin, no golden
  moved). After the second: `test_identity_pins`, `test_structure_ratchets`, `test_first_questions_today`: 376 passed.
- `scripts/affected_tests.py --files` (the three changed Python sources) listed 690 files. I ran the 78 whose names
  contain synthesis, bootstrap, add_source, ingest_runner, status_line, section, first_questions, auto_build,
  ux_phase1, keep_ahead, reread, source_library, source_action, mobile_v4_reader, mobile_v4_plan, mobile_v2_plan,
  sidecar_contract, desktop_rpc, apply_recovery, rerun_proposals, source_append, study_map, quick_add,
  reader_progression, practice_expansion, whole_book, empty_first, retry, reading_request, undo, inventory, append,
  glm, mobile_allowlist, mobile_phone_contract, mobile_(handoff|jobs|two_process|host_coexistence|rpc),
  secondary_attach, host_queue, daily_plan_reading, progressive, reader_first, items_off, build_plan, first_run,
  seeding, startup, model_work_checkpoints, curriculum_c1_fix_round2/3, keep_local, exam_protection, exam_marking,
  reader_requests, reader_quick_check or reader_guidance (with every `tests/test_*.py` whose name contains
  synthesis, bootstrap, add_source, ingest_runner, status_line or section, affected or not), in two chunks with
  `-m "not arc_close"`: 1,077 passed (40 files); 629 passed, 5 skipped (38 files).
- Gates, on the tip's sources: the two edited test files with `test_identity_pins`, `test_retired_config_identities`,
  `test_diagnosis_journey_golden`, `test_structure_ratchets`, `test_mobile_allowlist`,
  `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies`: 798
  passed (no pin, golden or ratchet moved). `test_test_layout` alone: 3 passed. `test_architecture` alone: 18
  passed. `ruff check`: all checks passed. `lint-imports --no-cache`: 43 kept, 0 broken.
  `scripts/check_gate_partition.py`: collected 31,971: landing 31,906 + arc_close 65.
- Desktop: `npm run typecheck` exit 0; `npx vitest run --maxWorkers=2` 315 files, 3,266 tests passed;
  `npm run frontend:build` exit 0.
- Phone: `npm run typecheck` exit 0; `npx vitest run --maxWorkers=2` 42 files, 424 tests passed; `npm run build`
  exit 0.

## Judgment calls

- **Where the line is drawn** (step 0a): a run owes a topic when its subject has none, it is not the narrow adjunct,
  and a unit may teach. A bootstrap rerun over a mapped subject, the narrow adjunct, an append, and a run with no
  teaching unit are left alone. Every Add build is on the owing side, since all of Add's roles teach.
- **Taken as it is, and kept.** The second answer is persisted, applied (concepts and facets) and its checkpoint
  kept. A later Try again therefore replays it at no cost only when its request is unchanged; on an automatic build
  it is not (the applied concepts are in the next request's registry index), so a Try again usually asks fresh, and
  asks again once more if that is empty too.
- **No-topics is told from the job's result** (`found_no_topics`: a completed bootstrap whose `item_counts` has no
  `learning_object`), not from the vault, so the card's line costs no read of the topics. It is a fact about the
  book's newest build; a book whose earlier chapter has topics and whose newest build found none says "in Ch. N".
- **The whole-book press says the truth instead of building**, as the brief asks, when every build of the book found
  no topic; beside chapters with topics, a chapter whose build found none is planned again by the press, as a failed
  one is (F6), because the card has no Try again of its own for it then.
- **An empty chapter is in `Coverage.failed`.** So reading on never plans it again unasked (keep-ahead skips
  `covered | failed`), while a press does. Without this, every reading report would have re-asked an empty answer.
- **The finish-a-section correction uses the existing none-up sentence** ("Nothing from “…” is up today. More
  questions come as you finish sections.") for a book whose finished sections had nothing to write, rather than a
  new sentence; it is true and names no step the Reader contradicts.
- **The metered estimate does not include the re-ask.** On a metered route the re-ask is held by the attempt's
  request gate (the learner's approved amount, or the daily cap) like every request; with neither set, nothing caps
  it, as for any request. The live route is the plan, where it is usage, not money.
- **Owed sections are paid only by a build's hook.** `start_waiting_sections` decides them when a build applies; the
  read of the books (`drain_owed_section_questions`) does not, because a `none_needed_after_build` row carries no
  time to tell a row settled under an empty build from one settled under topics.

## Not verified

- No app, browser, server or model ran; every state is from pytest on the house fakes (`FakeSynthesisClient`,
  `FakeBookSynthesisClient` driven by a script of answers; section questions were queued, not written) and vitest on
  fake RPCs.
- The model-call receipts of the re-ask (two `source_set_synthesis` rows with equal `prompt_hash`): the fakes write
  none; read from the code.
- A build whose topics wait for a look (auto-apply off) after an empty build: the hook runs when the build ends, before
  the learner accepts, so the owed sections stay `none_needed_after_build` until a later build applies (read from the
  code; the waiting rows of UX-31 are picked up by the read of the books, these are not).
- The real worker thread and a live Try again: tested through the foreground drain only.
- A multi-shard first build whose shards are all empty: the rule drops and re-asks every shard (read from the code;
  tested on one shard).
- How often the live model answers with no topic, and whether the same request answers with topics the second time
  (the walk saw it once; the record of four live reruns in `ux41-runaway-whitespace.md` had topics every time).
