# Method-explicit items, round-3 Codex review (stage `method-explicit-3`)

Branch `grading/method-explicit-items`, worktree `learnanything-merge`. Main
is at `4108e1ccd` (mvp-0.24) and was not merged here; this lands next as
mvp-0.25, relabelled at the merge. Codex job `20261014-193301-X2dw9X`,
read-only, reviewed `e96075e94..5392d7c3c` (round 3: the instruction
rendered from the field, fail-closed historical reconstruction, PF
selection and resume).

The verdict was **REOPENED**, with eight findings: F1 High, F2 to F8
Medium. Every finding reproduced on the base and is fixed. No finding was
rejected.

| Commit | What |
|---|---|
| `2d7c49483` | the fixes and their tests |
| `634839d7b` | regenerated architecture references (citations, source paths and source-commit stamps only) |
| (this commit) | this record, and the pointer in `method-explicit-items.md` |

Counts (`git diff --numstat 5392d7c3c..2d7c49483`): `src/` +595 / −110,
`tests/` +634 / −0, `apps/` +20 / −2. No migration, no new table, no
configuration key, no prompt version and no CLI help changed.

## Findings

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | High | Changing the required method reuses verification of a different question | fixed | `2d7c49483` | `test_f1_*` (3) |
| F2 | Medium | Rendered method names bypass answer withholding | fixed | `2d7c49483` | `test_f2_*` (1) |
| F3 | Medium | Historical review and diagnosis use today's method | fixed | `2d7c49483` | `test_f3_*` (3 tests x clear, rename, add = 9) |
| F4 | Medium | Prompt-only review surfaces still omit the instruction | fixed on this branch; MCP is a merge note (below) | `2d7c49483` | `test_f4_*` (3), plus the F5 tutor test |
| F5 | Medium | Clipping removes the appended instruction from model contexts | fixed | `2d7c49483` | `test_f5_*` (3) |
| F6 | Medium | Recovery requires an available judge even when every verdict is recorded | fixed | `2d7c49483` | `test_f6_*` (1) |
| F7 | Medium | Resume estimates ignore the persisted unfinished prompts | fixed | `2d7c49483` | `test_f7_*` (2) |
| F8 | Medium | Unrelated later inheritance can unverify an inline historical contract | fixed | `2d7c49483` | `test_f8_*` (3, one a control) |

The tests are in `tests/test_required_method_round3_review.py` (25 cases).

## F1 (High): the answer key names the required method

**Reproduction.** Round 3 moved the instruction out of the stored statement,
and `reference_content_hash` (statement, expected answer, rubric) did not
look at the field. A verified exercise requiring induction, changed to
require generating functions, kept the same key hash. Its old check stayed
`book_solution` (verified), and a dispute recorded against the new
revision lowered a regrade bound to the contract frozen under induction.

**Fix.** `reference_content_hash` adds `required_method_key(item)` when the
item has one: the method's name (whitespace-normalized) and the criteria
graded on its use.

- Changing only the method (set, renamed, cleared, or its criteria changed)
  makes another revision. Its key status is `changed_since_check`, so it
  certifies nothing until its key is checked (`learnloop sources exercises
  verify`, or the desktop's re-check after an edit). An accepted override is
  not re-checked automatically.
- Who decided the requirement (`statement`, `decided_by`, `judgment_id`)
  and the target it links are not part of the question, so they are not in
  the key.
- An item without a required method keeps its hash exactly. That covers
  every item on main, and with them every check and every recorded binding.
- A contract that recorded its hash binds exactly that hash, as before.
- A historical reconstruction (`GradedContract.graded_reference_contents`)
  rebuilds each candidate revision with the method the contract froze, not
  today's.

**Consequence for existing tests.** `_verified_method_import` in
`test_required_method_authority.py` added a method to a verified import
without checking the new revision. Under F1 that revision is unchecked, so
the helper now records its check (`rkc_method_revision`). The six F13
tests that use the helper are otherwise unchanged and pass.

**Known limit (branch-run vaults only).** A method contract frozen on this
branch before this fix recorded its hash under the earlier identity, and
the checks of that time used the same identity. Those bindings are kept
exactly. A check recorded after this fix uses the new identity, so it never
binds such a contract. Only vaults that ran this unmerged branch have such
contracts; main has no `required_method` field.

**Tests (3).**

- The key carries the name and criteria, ignores provenance and links, and
  is unchanged for an item without a method.
- Changing only the method through the owner's override leaves the
  statement, key and rubric unchanged. The status becomes
  `changed_since_check`, and `reference_status_for_item` becomes
  `unverified`.
- An answer graded under induction stays verified, with no binding, after
  the generating-functions revision is disputed.

## F2: withholding reads the rendered question

**Reproduction.** In `_practice_view`, `withhold.keep(item.prompt)` checked
the stored stem only, then rendered the instruction. The verify's case
(bound answer "cofactor expansion", listed stem "Compute det(A).", method
cofactor expansion) returned the item with `withheld = 0`.

**Fix.** The filter checks `presented_prompt(item.prompt,
item.required_method)`, the complete rendered text. The test is the
negative case: the answer occurs only in `required_method.name`. The same
item without a method is still listed.

## F3: readers of a recorded answer render the question it was given

**Reproduction.** Exam review (`_item_review_fields`), the adjudication case
and the diagnoser's history rendered the item as it is now. Clearing,
renaming or adding a method after an answer changed the question shown
beside that answer and its grade. Desktop exam review also preferred the
session's current presentation over the review field.

**Fix.** One rule, `learnloop.vault.required_method.answered_prompt(item,
contract)`:

- a method-explicit answer (its contract froze a required method, or the
  item has one now) is rendered from the contract it was graded under: the
  contract's statement, then the instruction of the method it froze, if
  any;
- every other answer reads the item as it is now, exactly as before.

This is the question `build_grading_context` sends the grader. The
contracts are read by `learnloop.db.stores.answered_contracts`, which is
read-only and picks the same contract as `attempt_graded_contract`: the
first one the evidence rows cite, superseded rows included.

| Consumer | Change |
|---|---|
| Exam review (`_report_dto` → `_item_review_fields`) | `prompt` from the answer's attempt contract. New `presentation`: the item's blocks with the contract's statement and instruction, or null when the item's own presentation applies. `ExamScreen` prefers it (`ExamItemOutcomeDto.presentation`). |
| Adjudication case (`_case`) | `prompt` from the attempt's contract |
| Diagnosis history (`VaultHistoryStore`, both the stored and the blind-record path) | `item_prompt` from each attempt's contract (one bulk read) |
| The attempt being diagnosed (`current_attempt_from`; `current_attempt_for` gets the repository from both job call sites) | `item_prompt` from its contract |

**Tests (3 x 3).** A real attempt goes through `apply_attempt` (contract
frozen) on an mvp-0.7 vault. The method is then cleared, renamed or added.
The adjudication queue, the diagnosis history and current attempt, and the
exam review (prompt and presentation blocks) each show the question as it
was given.

## F4: prompt-only readers render the instruction

**Reproduction.** The offline review's spot-check export and its judge's
item view used `item.prompt`. So did the Inspector's Prompt section, the
practice-index result, teach-back authoring (its source task), the source
tutor's verifier context (`TutorPool.verify_context`, the raw stem) and
several model contexts.

**Audit.** Every `.prompt` read of a practice item in `src/`,
`learnloop_sidecar` and the desktop app was classified.

| Class | Sites | Now |
|---|---|---|
| The learner answers it | practice, exams, golden path and Today (presentation block); TUI practice; Reader quick check; guided redo; teach-back session start (`handlers/teach_back.py`); probe dialogue turn (`prompt_md`) | rendered (the last two changed here) |
| A recorded answer is reviewed | exam review, adjudication, diagnosis history and current attempt (F3); offline spot check and harness (below); Inspector (current item: `ItemPresentation`) | rendered |
| A model reads the question as asked | grader (contract); tutor (`tutor_qa`, `instructional/tools`, source tutor verifier, `find_sources`); learner-text gap sources and the "needed for this item?" judge; diagnostic augmentation trials; teach-back authoring (`source_prompt`, the deterministic fallback, the question context); offline harness judge, planted-error writer, probes; practice-index rerank, eval labels, dossiers; rung backfill classifier | rendered (fitted where a budget applies, F5) |
| A reader of a result list | `learnloop practice-index find --json` / sidecar find result; golden-path setup exemplar list; source-offer impressions (`shown_fields`) | rendered |
| Identity, matching, search or embedding (the stored stem by design) | `reference_content_hash` (its own field now, F1), `practice_item_hash`, skeleton and contract hashes, item fingerprints, embedding recipes and the practice index's `item_text`, exposure similarity, inspector search, de-duplication, probe instance keys | unchanged |
| Editing and generation inputs (the writer must not write the sentence; the method is passed as a field) | card controls, `item_authoring`, proposals' existing-item and source excerpts, rung variants, practice generation, tutor promotion's existing items, the method-phrasing judge (given the field separately) | unchanged |
| One-line titles and previews | knowledge map and facet titles, Reader `prompt_preview`, the sidecar detail's raw `prompt` beside its `presentation`, golden-path self-grade header | unchanged |

**The offline review harness.** It blind-grades and diagnoses every target
against the item as it is now, so its judge, its planted-error writer and
its spot-check target prompt show the item now, rendered. A cited earlier
answer shows the question its history gave the diagnoser
(`HistoryAttempt.item_prompt`, F3).

Grading targets against their frozen contracts in the harness would change
its comparison design, so that is left as an open question (below).

**Mobile.** The allowlist is empty (`learnloop_mobile/allowlist.py`), so
there is nothing to change.

**CLI.** Only the practice-index JSON prints a stem. Exam and attempt
commands print ids and grades.

**MCP (branch `mcp/c1-read-context`): merge note.** That branch is not this
one, so it is not edited here.

- `learnloop/learner_context.py` `_pins` (line 425 there) reads only
  `json_extract(contract_json, '$.prompt')`. Its historical stem therefore
  loses the instruction of a method-explicit answer.
- Whichever lands second must render the pin with
  `answered_prompt(item, {"prompt": ..., "required_method": ...})`. The
  alternative is to read `$.required_method` too and use
  `presented_prompt(prompt, required_method)`.
- `learnloop.db.stores.answered_contracts.answered_contracts` returns both
  fields per attempt.
- This lands first (as mvp-0.25), so the MCP landing carries the change. It
  is recorded in `method-explicit-items.md` for that landing.

**Tests (3, plus the F5 tutor test).**

- The planted-error payload and the gap judge's context render the
  sentence for a method item, and the bare stem otherwise.
- Teach-back's fallback authoring shows the task with its sentence.
- The practice-index rerank context keeps the sentence for a long stem.

## F5: a long stem keeps the whole instruction

**Reproduction.** The paths appended the instruction, then clipped the
whole string: `_practice_view` at 400 characters, `find_sources` and the
remediate tutor at 700. A long stem lost the requirement entirely. The
source tutor's main path sent the raw stem, and `verify_prompt` clipped it.

**Fix.** `fit_presented_prompt(prompt, method, limit, clip)` shortens only
the statement with the surface's own clipper, then appends the sentence.
Without a method it is `clip(prompt, limit)` exactly, so every other
item's context (and every checkpoint key over it) is unchanged.

- `source_retrieval.verify.practice_question(item)` is the one fitted
  question for item-bound verification. It cuts like `find_sources` and the
  remediate path did. With `ellipsis=True` it clips like `verify_prompt`,
  for the tutor's pool.
- The instruction is kept as one sentence at the end of `prompt`, not as a
  separate field. Every consumer that reads `prompt` therefore gets it, and
  the limit still bounds the whole string.

Other users of the fitted question: the TUI queue preview, the practice
index's rerank, eval-label and dossier contexts, rung backfill, and the
source-offer impressions.

**Tests (3).**

- The practice tool with a stem of about 1,600 characters: the bare item
  clips to exactly 400 as before; the method item ends with `… Use cofactor
  expansion in your answer.` within 400.
- The source tutor's recorded verification context ends with the sentence
  within 700. It was the bare stem.
- `find_sources` (assisted practice, verified) does the same.

## F6: a ledgered verdict needs no judge

**Reproduction.** A run stopped after the last verdict was ledgered and
before publication. The rerun planned zero judgments, but `judge_variant_stem`
resolved the judge before reading the ledger, and an unavailable judge
returned None. The job ended `judgment_incomplete` with its request
`failed`, although publication had consumed the ledgered verdicts. On the
base the second run published both variants and still reported
`judgment_incomplete`.

**Fix.** `judge_variant_stem` reads `variant_method_verdict` (the ledger)
first and returns a recorded verdict without resolving a client. Only a
missing verdict resolves and calls the judge. Publication from the backlog
uses the same path.

**Test.** The first run is interrupted inside publication after both
verdicts. The rerun's dry run plans no judgment. With
`resolve_statement_judge` returning None, and recording any call, the rerun
completes, publishes both, admits the request, and resolves no judge.

## F7: the resume is estimated from what is persisted

**Reproduction.** `_plan_resume` estimated each missing judgment and the
selection request from `parent.prompt`. The verify measured 1,647 tokens
instead of 4,647 for a 3,015-character variant. In the test, a selected
variant of 2,845 characters was planned at 1,638 tokens instead of 4,459.

**Fix.** `_resumable_job` returns the persisted inputs of the unfinished
work:

- the stems still to be judged (`missing_stems`);
- the survivors (`survivor_inputs`: stem, relation, difficulty,
  verification, whether judged).

`_plan_resume` then estimates from them:

- each missing judgment from its own stem;
- a selection to finish from the survivors the judge will be shown, with
  six-decimal placeholders for the scores it adds;
- up to one judgment per slot, the longest unjudged survivors, as an upper
  bound. The per-call figure is the largest.

**Tests (2).**

- A waiting variant stretched to 2,845 characters is planned at exactly
  its own estimate. A token cap halfway between the parent-based
  and the variant-based estimate refuses the dry run (`over_budget`); the
  base admitted it.
- A selection to finish (the F22 partial state) grows its selection
  estimate with the survivors' stems; the base's did not move.

## F8: inheritance is established from the graded revision's provenance

**Reproduction.** A historical (unrecorded-hash) contract graded under an
inline rubric reconstructs exactly (`frozen`). A later snapshot of the same
item with a different question and no rubric of its own made
`inherited_known` true. With the default since changed, the binding became
`ambiguous_default` and lowered the attempt to unverified.

**Fix.** `graded_reference_contents(..., attempt=)` decides "may the revision
graded have inherited a default?" from that revision's own provenance.

1. **The attempt-time revision.** The attempt's scheduler candidate (the
   attempt row's, else its submission intent's or probe presentation's) has
   a `decision_features` row at or before the attempt. Its `content_hash`
   addresses the exact `practice_item_snapshots` serialization. This is the
   receipt chain field outcomes read as `exact`.
   - When that revision has the frozen statement and answer, its rubric is
     the one graded.
   - Inline and reproducing the contract: `frozen`.
   - Inherited and not reproducible today: `ambiguous_default`, unverified.
2. **Otherwise.** A revision recorded with the graded statement and answer
   (the current item, a snapshot, or a key check of exactly the inherited
   rebuild) that has no rubric of its own. A revision of another question
   is never the one graded.

When neither establishes it, the existing rules apply: `frozen`,
`ambiguous` among the checked, or `unresolved`, which binds fail closed
against every checked revision. The regrade passes its attempt row.

**Tests (3).**

- The verify's reproduction stays verified, with no binding.
- Control: a same-question revision that inherited still binds
  `ambiguous_default`, unverified. This one passes on the base too.
- With the attempt's selection receipt pinning the inline revision, a later
  same-question inherited snapshot never unverifies it.

The round-3 F19 tests (historical and recorded, disputed or not) pass
unchanged.

## Fail-first

The base `5392d7c3c` was exported (`src`, `tests`, `pyproject.toml`) to
`fixtures-local/tmp/base_5392d7c3c`, with `migrations` linked in. No tracked
vault was linked. The final `tests/test_required_method_round3_review.py`
ran there with the worktree's interpreter, `pytest -o pythonpath=src`.
Tracebacks confirm the export's modules.

**24 failed, 1 passed.** Every failure is a behavioural `AssertionError`;
none is an import, type or attribute error.

| Finding | Failed on the base | What the base did |
|---|---|---|
| F1 | 3 | one hash for no method, induction, generating functions and no criteria; `book_solution` after the method change; the induction contract lowered by the new revision's dispute |
| F2 | 1 | the item was listed with the protected answer in its rendered sentence |
| F3 | 9 | today's method in adjudication, history, current attempt and exam review, for clear, rename and add |
| F4 | 3 | the bare stem in the planted payload and gap judge; teach-back's task without the sentence; a long stem's rerank context without the sentence |
| F5 | 3 | the practice tool's sentence clipped away; the tutor's verifier given the bare stem; `find_sources` cut the sentence at 700 |
| F6 | 1 | `judgment_incomplete` (both variants published, request failed) |
| F7 | 2 | 1,638 tokens planned for a 4,459-token judgment; the selection estimate did not grow |
| F8 | 2 | the unrelated snapshot and the pinned case both unverified |

The one that passes on the base is the intended control (F8, a
same-question inherited revision fails closed).

## Gate

The gate ran on the tree at `634839d7b`. The only uncommitted changes were
this record and the pointer in `method-explicit-items.md`. `TMPDIR` was the
worktree's `fixtures-local/tmp`. The full suite and the durability lane each
ran under `/tmp/learnloop-fullsuite.lock`, one after the other.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | **17 kept, 0 broken** |
| Targeted run before the commit (91 related test files, plus `test_architecture.py` and `test_instructional_layering.py`) | **1216 passed** |
| Full suite: `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10584 passed**, 0 failed, 0 skipped (48 warnings, 469.46s). That is 10559 + 25 new |
| Durability lane: `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **99 passed**, 10485 deselected, 0 failed (1 warning, 120.52s) |
| Frontend (`apps/learnloop-tauri`): `npm install`, `npm run typecheck`, `npm test`, `npm run frontend:build` | typecheck clean; vitest **74 files, 479 tests passed**; build succeeded |
| Cargo | not applicable: nothing under `src-tauri` changed |
| `db_generate_reference.py`, then `db_validate_reference.py` | **0 errors**: 318 table notes, schema unchanged. Only citations, capped source-path lists and source-commit stamps moved (`634839d7b`) |
| `validate_vault.py` | passed (1,099 notes, 22,001 links) |
| CLI help snapshot, defaults and template snapshots | unchanged (no command, option or configuration key changed) |
| Undefined names and new unused imports in the changed files (`ruff --select F821`, F401 count against `HEAD~`) | none |

There were no paid calls and no live check. No external interface changed,
and the prompt versions are unchanged: only method items' contexts gain the
sentence. No key, env file or vault database was read, and no tracked vault
was opened. Main was not merged in.

## The stage notes, assessed

1. **Is any path still reading or matching the instruction in stored
   text?** No. Grading reads the field, through the frozen contract. The
   only reader of the statement for a method is `advisory_statement_flag`,
   which raises doctor and report flags and has no grading authority. A
   stale `build_item_payload` docstring ("gains the canonical sentence") is
   corrected. With F3 to F5, the grader and every answering, review and
   model surface show the same question: statement, then the rendered
   sentence (contract-frozen for recorded answers).
2. **Every surface uses `presented_prompt`?** Yes, after F4 and F5: see the
   audit table. MCP is the merge note above, and the mobile allowlist is
   empty.
3. **Historical reconstruction.** A recorded hash binds exactly (F1 keeps
   the earlier identity's bindings). The unrecoverable-default rule now
   fires only on the graded revision's own provenance (F8), which answers
   open question 9 ("broad").
4. **PF selection and resume.** The atomic selection and markers are
   unchanged. Resume now reads the ledger before any judge (F6), and the
   budget estimates the persisted unfinished inputs (F7).
5. **Replay and regrade read only the frozen field.** Confirmed:

   - `regrade_reads_contract` and `build_grading_context` take the method
     and statement from the contract;
   - `bind_replacement_grade` binds the recorded (or provenance-rebuilt)
     revision;
   - replay makes no model call and no new replay path was added.

**Open question 1 (8 in round 3): legacy stems that show the sentence
twice.** Agreed with the review: not merge-blocking. Such statements exist
only in vaults that ran this unmerged branch before round 3. Removing the
sentence by text would bring back the matcher round 3 retired, so nothing
removes it automatically.

**Open question 3 (10): markerless old selections are redone.** Agreed:
conservative and honest. F7 makes their remaining work budgeted accurately,
from the persisted survivors, which is the review's condition.

**OWNER-DIRECTED (2026-10-13 rubric rule).** "When the method is the point
of the item, the question must say 'Use {method} in your answer'." This now
holds wherever the question is shown or sent:

- every answering surface;
- every review of a recorded answer, as given;
- every model context, never clipped away;
- the grader.

## Not changed, and open questions

- **The offline review harness regrades against today's item.** Its blind
  grade, diagnosis and judge read the item as it is now (now rendered).
  Grading its real targets under their frozen contracts, as production
  regrades do for method items, would change the harness's comparison
  design. That is for the owner.
- **Non-method answers still show today's statement** in exam review,
  adjudication and diagnosis history, as before this branch. F3 renders
  from the contract only for method-explicit answers, the stage's scope.
  Doing it for every edited item would change diagnoser inputs beyond this
  stage.
- **Exam answers' contract.** An exam answer's attempt freezes its contract
  at `finish_exam` (`apply_attempt`), not at presentation. A method changed
  between answering and finishing is frozen as of finish. This was not
  changed here.
- The successor placeholder (`mvp-0.22-placeholder`) and the kill switch
  (`[required_method] enabled`) stay. The integration relabels to
  `mvp-0.25`.
