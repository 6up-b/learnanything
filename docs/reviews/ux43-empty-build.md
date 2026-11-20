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
