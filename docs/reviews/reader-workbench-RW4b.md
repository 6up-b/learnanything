# Reader workbench RW4b: exercises from my sources (stage `reader-rw4b`)

Branch `reader/rw4b` (worktree `learnanything-rw4b`), base `main` at
`fab576ac1` (migration head 213; AD1, H2b, RW2b + H3 on main). Spec:
`docs/specs/spec_reader_workbench_v1.md` §7.4 in full, §1's RW4b line, the
§13 RW4b row (needs RW4a; the sources spec's S1 for the candidates, the
fallback without), §14 G19, G34, G53, the RW4b test list and §18's cross-spec
notes. `docs/specs/ux_reader_workbench_v1.md` §4.5's "Nothing in practice fits
yet · find an exercise in my sources ▸" and §4.6 (the candidate card).
`docs/specs/spec_source_practice_and_probes_v1.md` §5.4 (the exposure rule),
§6.3 (how a proposal becomes served), §7.1 (the arm), §7.2 (the import),
§7.3 (the ladder's honest key labels), §7.3a (C3: unverified keys never
certify). Consumed, never rebuilt.

## 0. Plan (written before the code)

### 0.1 Which sources-spec pieces are on `main` (checked at `fab576ac1`)

The sources spec's S0–S5 merged at `5db645a33` ("Merge sources/canonical-practice
onto main"; `git merge-base --is-ancestor 5db645a33 fab576ac1` holds). Present
and live by default:

| Piece | Where on main | Default |
|---|---|---|
| S1 arm: textbook exercises as `find_practice`'s own kind (`source_exercises`: `extraction_id`, `span_ids`, `source_id`, `revision_id`, `source_title`, `label`, `page`, `statement`, `label_line`) | `instructional/exercises.py:exercise_candidates`, injected by `instructional/wiring.py`; entry shape `practice_index/retrieval.py:_exercise_entry` | `source_service.exercise_arm = true` |
| S1 interactive import (pick → job → ladder in a time box → write with `canonical_exercise` and the key status → family) | RPC `import_source_exercise` (`learnloop_sidecar/handlers/source_service.py`), job `source_exercise_import` (`content/pipeline/jobs.py:handle_source_exercise_import`), `content/authoring/source_exercise_import.py:import_source_exercise` | on |
| Import status + honest key label | RPC `get_source_exercise_import`; `db/stores/source_service.py:KEY_STATUS_LABELS`, `effective_key_status` | — |
| Delivery of an imported pick | `plan_learner_pick(…, proposal_id, source_exercise_import_id)` → `imported_exercise_selection` + S5's `record_pick` | — |
| The exposure rule | `instructional/exposure.py:independent_check_eligibility` (rules 1–5, `reading_exposure_v1`) | rule 4's judge route `worked_example_equivalence` is unset by default |
| Impressions | RPC `record_proposal_impressions` (`instructional_impressions`) | — |
| `find_sources` with roles and the Reader caller (`reading`) | `instructional/sources.py:propose_sources`, RPC `find_sources`, `instructional/policy.py:caller_for` | — |
| C3 certification gate on unverified keys | `practice_attempts.reference_status`, `reference_status_for_item` | not switchable |

So RW4b is the **view** over a live S1, plus the fallback behind its switch.
What is *not* on main: any Reader rendering of `source_exercises` (RW4a's
practice block shows items only; RW1c's `TutorOffers` ignores them too and
RW1c is not on this base), and `library_exercises.*` config.

### 0.2 What RW4b builds

1. **The candidate view, one shared component** (`screens/reader/ExerciseCandidates.tsx`):
   each textbook-exercise candidate shows its verbatim statement (a `§`
   source-voice passage, never its solution), source and page, *open in the
   book*, *use this one*, the honest line *from your book · verbatim · answer
   completed by LearnLoop's model* with the key's status (before import:
   "checked when you use it"; after: the import's own label, adjusted per
   status: `book_solution` says "answer from the book's solution", `disputed`
   says LearnLoop's check disagrees, and so on), and the exposure label when
   the sources spec's rule marks it. Used by RW4a's "Practice this question"
   (both the comparing posture and the library page). RW3's "Check me" does
   not list proposals on main (it serves one cue check), so nothing to wire
   there. RW1c's `TutorOffers` gets a one-line hook recorded below for the
   landing.
2. **Exposure, from the sources spec's rule, read by one new desktop RPC**
   `reader.exercise_candidates(proposal_id, keys)`: validates each key
   against the stored proposal (`proposed_exercise`), drops any whose region
   is now exam or held-out material (`exam_withheld`, the one predicate),
   and runs `independent_check_eligibility(intent="discriminate",
   picked_proposal_id=proposal_id)` per candidate. Exposed (any reason) →
   the reason's label, and the candidate is **never offered as a check on
   your own**: *use this one* opens it as practice beside the book
   (workbench entry `work_through`, book shown), not book-hidden. Unexposed
   → entry `practice_this` (book hidden, UX S7). If the check fails, the
   exercise candidates are not shown (fail closed), items still are.
3. ***Use this one* → the sources spec's import path, inside the workbench.**
   `workbench.open` gains `source_exercise: {proposal_id, extraction_id,
   span_ids}` beside `import_request`: the session opens at once with the
   verbatim statement as its stem, and the server queues the S1 import with
   the same code as `import_source_exercise` (factored into one helper,
   behaviour unchanged). The workbench's existing pending/bind/failed/retry
   machinery follows the S1 job: `_job_parts` reads the S1 result's
   `practice_item_id`; a rejected or failed import marks the session
   `failed` with the import's own reason and *try again* re-queues the S1
   import; nothing is bound (so nothing is served) until the import wrote
   the item. The session view of an S1 problem carries `sourceExercise`
   (import id, proposal id, effective key status and label) so the header can
   say the key's honest status. **When it binds, the item becomes a learner
   pick**: the shell runs the existing check-me pick (`plan_learner_pick`
   with the proposal and import ids; plan off: the open's delivery), which
   resumes the same open session with the pick's serve (entry
   `practice_this`, so the learner's book choice is kept).
4. **The fallback** "Find an exercise in my sources ▸", beside "Nothing in
   practice fits yet." when `find_practice` returned neither items nor
   exercises, behind `library_exercises.fallback_enabled`. New desktop RPC
   `reader.find_exercises(query, learning_object_ids, extraction_id)`:
   `propose_sources(intent="explain", scope="teaching", roles=["exercise"],
   verify=False)` under the Reader caller (`reading`, derived on the server,
   G19), each hit widened to its exercise region (`exercise_regions`, the
   sources spec's), already-imported regions and exam/held-out material
   dropped, exposure computed (same rule, no proposal) **before** the shown
   spans are recorded as exposure (`record_shown_spans`, context `library`,
   as RW4a does). *Use this one* opens the workbench with the region's
   `reader.import_exercise` request (the existing `import_exercises`,
   unchanged, G34) and becomes a learner pick on binding. Worked examples are
   never offered (roles filter; D14).
5. **Config** (`LibraryExercisesConfig`, classified in the parameter
   registry): `library_exercises.enabled = true` (the view; off: the
   Reader's practice proposals render exactly as on `fab576ac1`, the prompt
   contract has no `library_exercises` key and both RPCs refuse) and
   `library_exercises.fallback_enabled = false` — **the spec's rule** (§7.4:
   "the fallback is retired when the sources spec's candidates are live …
   then defaults off"), since S1 is live on main.

### 0.3 What RW4b does not do

No migration (216 stays reserved and unused). No new model route: the only
model-backed code it reaches is the sources spec's (the import and its
ladder; the exposure rule's own judge route when the owner configures it;
T6's query embedding/rewrite inside `find_sources`). Nothing writes evidence,
mastery or grading inputs beyond what the import path and the workbench
already write. No edits to `adaptive_difficulty/`, the scheduler, the daily
plan, `source_retrieval/reader_tutor.py`, `tutor/reader_modes.py`, RW1c's
`TutorOffers`, or `PracticeScreen.tsx`.

### 0.4 Tests planned

`tests/test_library_exercises.py` (G34, G19, G53, the held-out sentinel, the
exposure label and never-as-check rule, the workbench's S1
running/admitted/refused states, the switch-off pins, the RPC pins);
`tests/test_mobile_allowlist.py` (the two new RPCs desktop-only); config
snapshot/registry tests; vitest `ExerciseCandidates.test.tsx` and
`libraryExercises.test.tsx` (the card, the labels, the fallback line, the
switch-off render).

## 1. What was built

### 1.1 Config (`src/learnloop/config/schema.py`, `LibraryExercisesConfig`)

`[library_exercises] enabled = true`, `fallback_enabled = false` (modelled
defaults, left out of the decision-only template). Both are booleans: the
parameter registry's numeric walk skips them, and both are classified
explicitly in `params/parameter_registry.py` (structural / operational kill
switches, as RW2b's fix round 1 F11 did for its booleans; added in Codex
review round 1, see `reader-rw4b-codex-review.md`). The 19 defaults
snapshots in `config/template.py` were recomputed from the composed defaults
(`defaults_fingerprint_for_version`) with the usual note per version (no
serving change, no successor). `db_generate_reference.py` gained the section's
one-line description (`CONFIG_SECTION_FUNCTIONS`), without which it could not
regenerate the configuration catalog.

### 1.2 The sidecar

- **`src/learnloop_sidecar/handlers/library_exercises.py`** (new; desktop only):
  - `reader.exercise_candidates(proposal_id, keys)`: validates at once that the
    proposal exists and proposed each key (`instructional.practice.proposed_exercise`;
    an unproposed key is `validation_error`), then answers with a library job
    (RW4a's runner, `reader.library_job` / `reader.library_job_cancel`) that,
    per candidate, drops exam and held-out material (`source_retrieval.corpus.exam_withheld`,
    the one exam predicate; counted as `withheld`) and reads the sources
    service's exposure rule (`instructional.exposure.independent_check_eligibility`,
    intent `discriminate`, `picked_proposal_id` = this proposal, the request's
    learning objects for rule 4's scope). Each candidate returns `exposure =
    {exposed, reasons, label, note, offered_as, exposure_rule_version}`:
    `offered_as` is `practice` for any reason, `check_on_your_own` otherwise.
  - `reader.find_exercises(query, learning_object_ids, extraction_id)` (the
    fallback, only while `fallback_enabled`): a library job running
    `instructional.sources.propose_sources(intent="explain", scope="teaching",
    roles=["exercise"], verify=False)` under the Reader caller the server
    derives (`library_ask.reader_caller` → `reading`), each hit widened to its
    exercise region (`instructional.exercises.exercise_regions`), duplicates,
    already-imported regions (`imported_span_keys`) and exam/held-out regions
    dropped, a label (`exercise_label`), the region's verbatim statement, the
    exposure read BEFORE the list is recorded, then the Reader's own import
    request (`selection_for_region`) and finally `record_shown_spans`
    (context `library`, entity type `library_exercises`).
  - `prompt_contract_fields`: `library_exercises: {fallback}` only while the
    view is on (inside the library answer: `library_ask_enabled` and
    `library_exercises.enabled`); wired in `reader.prompt_contract`.
- **`src/learnloop_sidecar/handlers/source_service.py`**: the body of
  `import_source_exercise` moved, unchanged, into
  `queue_source_exercise_import(ctx, vault, repository, *, proposal_id,
  extraction_id, span_ids)` (the import row, the pick's usage verdict, the
  job), which the RPC and the workbench both call.
- **`src/learnloop_sidecar/handlers/workbench.py`**: `workbench.open` accepts
  `source_exercise: {proposal_id, extraction_id, span_ids}` (exclusive with
  `import_request`; refused `library_exercises_disabled` while off). The stem
  is the statement; the stored import request is `{"kind": "source_exercise",
  …}`; `_enqueue_import` dispatches it to `queue_source_exercise_import`, so
  "try again" re-queues the same S1 import; `_job_parts` reads the S1 job's
  `practice_item_id` when its status is `written` (nothing else binds);
  `_job_error` already carries the import's own reason. `_view` adds
  `source_exercise = {proposal_id, import_id, import_status, reason,
  key_status, key_label}` (the effective key status of the bound item) for S1
  problems only; every other problem's view is unchanged (pinned).

### 1.3 The Reader (frontend)

- `screens/reader/exerciseCandidates.ts`: the model (`fromProposal`, fail
  closed; `fromFallback`; `keyStatusLine`, the honest line per key status;
  `exerciseLocator`; `exerciseOpenRequest`: `practice_this` when unexposed,
  `work_through` (book shown) when exposed; `practiceFromToolRun` for RW1c).
- `screens/reader/ExerciseCandidates.tsx`: the card (a `§` source-voice
  statement with "source · p. N · Exercise k", the honest line, the exposure
  label with "practice beside the book, not a check on your own", *open in the
  book ↗*, *use this one ▸*).
- `screens/reader/useLibraryExercises.ts`: asks `reader.exercise_candidates`
  for a landed proposal with exercises (reads the job, paced; cancels it if the
  proposal changes or the pane goes), records the shown exercises'
  impressions (`surface: "reader"`), and runs the fallback on request.
- `screens/reader/ProposalExercises.tsx`: the self-contained block (cards,
  "checking your books' exercises…", the fail-closed line, "Nothing in practice
  fits yet · find an exercise in my sources ▸", the fallback's results),
  used by `LibraryAnswer` after its items; RW1c's hook is this element.
- `LibraryAnswer.tsx` / `LibraryPane.tsx`: an optional `exercises` prop; absent,
  the practice block is RW4a's byte for byte (the snapshot was written with
  `fab576ac1`'s `LibraryAnswer.tsx` in place).
- `ReaderScreen.tsx`: `onUseExercise` prop; `exerciseProps` from the contract
  (`use this one` only while the workbench is on); *use this one* hands the
  shell the request with the exercise's source card and opens that source as a
  detour when another is open; *open in the book* is RW4a's "open" detour.
- `useReaderWorkbench.ts`: `exercise` / `onExerciseShown` /
  `onExerciseAdmitted` props: once the exercise's source is open it calls
  `workbench.open` with `sourceExercise` (or the fallback's `importRequest`)
  and the entry; it reports `onExerciseAdmitted` once when a problem it opened
  pending binds. `ReaderWorkbenchCheck.entry` (optional) lets the admitted pick
  resume its own problem as `practice_this` (the book as the learner left it).
- `app/App.tsx`: `exerciseFromReader` (no session: "Start a session to work on
  this exercise — it will open automatically.", resumed after Begin, as check
  me is); `exerciseAdmitted` runs the existing `pickCheckMe` with the
  proposal and the import id (`plan_learner_pick(…, proposalId,
  sourceExerciseImportId)`; plan off: the open's serve records the delivery
  through `proposalOrigin.importId`), which resumes the same problem with the
  pick's serve. `readerCheckOffer` takes the import id.
- `screens/workbench/Workbench.tsx`: a bound S1 problem shows its honest key
  line ("from your book · verbatim · answer completed by LearnLoop's model ·
  not checked", "… · answer from the book's solution", "… · LearnLoop's check
  disagrees with this answer key", …). Only S1 problems have it.
- Tauri: two passthroughs (`reader_exercise_candidates`, `reader_find_exercises`).

## 2. Gates and where they are tested

| Gate | What holds | Tests |
|---|---|---|
| **G34** exercises from sources | The S1 candidates are the sources service's (`find_practice`'s `source_exercises`), shown only as the server lets through; "use this one" calls its import path (`queue_source_exercise_import`, the same helper as `import_source_exercise`: import row, usage verdict, job). The fallback's candidates are `exercise` regions of the teaching scope (never worked examples, solutions or the exam) and "use this one" sends `reader.import_exercise`'s request unchanged. Nothing is imported without the learner's pick (the fallback search itself imports nothing). | `test_library_exercises.py`: `test_fresh_candidates_…`, `test_use_this_one_opens_at_once_…`, `test_the_fallback_finds_exercise_regions_…`, `test_use_this_one_on_a_fallback_exercise_runs_the_readers_import_unchanged`; vitest `libraryExercises.test.tsx`, `readerWorkbenchExercise.test.tsx` |
| **G19** policy from the caller | The fallback's `find_sources` call gets its policy from the Reader caller the server builds (`reading`, recorded on the manifest); no RW4b input has a `policy` field; no `authoring` material reaches the Reader (S1's verifier keeps its own scope). | `test_the_fallback_finds_…` (`policy`, `manifest.policy`), `test_the_new_rpcs_take_no_policy_…`, `test_with_the_sources_service_faked_…` |
| **G53** consumption degrades cleanly | Sources service absent (`source_service.enabled = false`): no `libraryExercises` contract key, the RPCs refuse. Faked: the fallback's call is the documented one (`propose_sources`, intent `explain`, scope `teaching`, roles `["exercise"]`, `verify=False`, a `reader` caller, no policy). RW4b's modules define none of the service's functions (AST scan). | `test_with_the_sources_service_absent_…`, `test_with_the_sources_service_faked_…`, `test_rw4b_defines_no_second_service_function` |
| Held-out / answer leak (orchestrator note 2) | Exam and held-out exercise regions are never shown: the arm's teaching scope and the fallback's teaching scope exclude them, and the view re-checks the one exam predicate at display time (a mark made after the proposal hides it). Only the verbatim statement reaches the Reader; the solution text never appears in any RW4b payload. | `test_the_held_out_sentinel_is_never_offered_by_the_view_the_arm_or_the_fallback`, `test_fresh_candidates_…` (no solution text), `test_the_fallback_finds_…` |
| Exposure label, never as a check (§7.4) | A shown page or solution, an earlier suggestion of the same question (rules 3, 5; this proposal's own impression does not count), a reveal, an attempt or an equivalent/unjudged worked example label the candidate, and "use this one" opens it as practice beside the book (`work_through`), never book-hidden as your own attempt. | `test_a_seen_page_or_solution_is_labelled_…`, `test_an_earlier_suggestion_counts_…`; vitest `exerciseCandidates.test.ts`, `libraryExercises.test.tsx` |
| Import states (running, admitted, refused) | Running: the problem is open on the stem, steps save, nothing bound, no item exists. Admitted: bound to the written item (`canonical_exercise` verbatim), the honest key status on the view, the plan's learner pick with the proposal and import ids, the same problem resumed with the pick's serve. Refused (`unverified_imports = false`): `failed` with the import's own reason, nothing bound, no item written, "try again" re-queues the same import. | `test_use_this_one_opens_at_once_…`, `test_admitted_the_problem_binds_…`, `test_a_refused_import_…`, `test_a_problem_imports_one_way_…`; vitest `readerWorkbenchExercise.test.tsx` |
| Switch-off pins (orchestrator note 6) | `library_exercises.enabled = false`: the prompt contract equals the base's minus nothing (no key), the RPCs and `workbench.open`'s `sourceExercise` refuse, `find_practice`'s Reader answer is unchanged; the practice block's markup equals `fab576ac1`'s (snapshot written with the base `LibraryAnswer.tsx`), and no RW4b call is made. | `test_switched_off_the_contract_rpcs_and_practice_answer_are_as_before`; vitest `libraryExercises.test.tsx` (two snapshots) |
| Mobile | Both RPCs desktop-only; `reader.prompt_contract` and `workbench.open` extended. | `test_mobile_allowlist.py::test_the_pinned_rw4b_rpcs_are_all_of_them` and the desktop-only parametrization |

## 3. Decisions and deviations

1. **The view's RPCs run as library jobs** (a deviation from §0.2's "answers
   at once"): the exposure rule's judge (`worked_example_equivalence`, which
   resolves to the active provider when its route is unset) and the fallback's
   retrieval (T6's query embedding/rewrite) may call a model, and the sidecar
   is serial (RW4a's W12 / Codex F6 ruling). Validation (unknown proposal,
   unproposed key) still answers at once.
2. **The exposure intent is `discriminate`.** A "check on your own" is the
   learner's unaided attempt with the book hidden; §7.4 names exactly the
   discriminate exclusions (page or solution seen, revealed sibling, equivalent
   worked example). A merely related worked example is shown as a note ("you
   read a worked example like this one"), not an exclusion. An unjudged studied
   example (no route, over budget) excludes, as the rule says.
3. **"Never as a check on your own" = opens as practice beside the book**
   (workbench entry `work_through`): the workbench's own rule then counts the
   book as one hint if the learner keeps it open. The learner can still hide
   it; RW4b changes no assistance accounting.
4. **"Use this one" needs a practice session, as "check me" and RW4a's
   "practice this ▸" do**: without one the shell says so and opens the
   exercise after Begin. The learner pick happens when the import is admitted
   (written), through the existing `pickCheckMe` with the import id.
5. **The learner pick is owed durably** (superseded in Codex review round 1,
   F2): the problem's stored import request keeps the pick's record
   (`reader_exercise`: proposal, exposure, `admitted_at`), the view says
   `exercisePick.due` while the import has bound it and the pick was not
   delivered, whichever visit or restart sees it, and the pick's hand-off
   (`workbench.open` with `admittedSessionId`) acknowledges it only after the
   pick and its serve succeeded. No migration (a JSON field in RW2a's column).
6. **Without the workbench** (`workbench.enabled = false`) a card offers only
   *open in the book*; "use this one" is defined by §5.1's working posture.
7. **Fallback default off** — the spec's rule (§7.4) since S1's candidates are
   live on main. It does not switch itself on when `source_service.exercise_arm`
   is off (open question 2).
8. **The fallback records what it showed** (`source_exposure_events`, context
   `library`) after reading each candidate's prior exposure, per the sources
   spec's `reading` policy; a second search therefore labels those exercises
   as seen (honest: the learner read the question).
9. RW3's "Check me" lists no practice proposals on main (it serves one cue
   check), so the view is wired into RW4a's "practice this question" only;
   RW1c's offers get the one-element hook below.

## 4. Successor

None. Display, a learner's own pick through the existing import and pick
paths, and exposure rows the sources spec already defines. No scoring,
scheduling, projection or serving change; no migration (216 unused).

## 5. The RW1c hook (for the landing to wire)

In RW1c's `screens/reader/TutorOffers.tsx`, `OfferResult`'s practice branch,
right after the items' `</ul>` (inside the `ModelVoice`):

```tsx
{props.exercises && lookup.practice ? <ProposalExercises practice={lookup.practice} itemsShown={(lookup.items ?? []).length} exercises={props.exercises} query={offer.practice?.request.query ?? ""} learningObjectIds={offer.practice?.request.learningObjectIds ?? []} extractionId={props.extractionId ?? null} /> : null}
```

with its two plumbing lines: `runLookup` keeps the proposal on the lookup
(`practice: result` for the `findPractice` path, `practice:
practiceFromToolRun(run)` for a tool run; both from
`screens/reader/exerciseCandidates.ts`), and `practiceLookup` treats a lookup
with exercises as `ready` (so "nothing in your practice or books fits this
yet" shows only when `ProposalExercises` has nothing either). `exercises` is
the `LibraryExercisesProps` the Reader already builds (`exerciseProps` in
`ReaderScreen.tsx`), passed to `TutorOffers` as RW4a's pane gets it.

## 6. Tests and counts

New: `tests/test_library_exercises.py` (18 tests); vitest
`screens/reader/exerciseCandidates.test.ts` (8), `libraryExercises.test.tsx`
(9, two switch-off snapshots in `__snapshots__/libraryExercises.test.tsx.snap`
written with `fab576ac1`'s `LibraryAnswer.tsx` in place, then passing
unchanged against RW4b's), `libraryExercisesReader.test.tsx` (2),
`readerWorkbenchExercise.test.tsx` (5). Changed: `tests/test_mobile_allowlist.py`
(`READER_RW4B_RPCS` + `test_the_pinned_rw4b_rpcs_are_all_of_them`),
`tests/test_rw4_kill_switches.py` (RW4a's "restores RW1b's contract" helper
also drops `libraryExercises`, which lives inside the library answer and
goes with it).

## 7. Files

Backend: `src/learnloop/config/schema.py`, `src/learnloop/config/template.py`
(19 snapshots + notes), `src/learnloop_sidecar/handlers/library_exercises.py`
(new), `…/handlers/__init__.py`, `…/handlers/reader.py` (contract),
`…/handlers/source_service.py` (shared queue helper), `…/handlers/workbench.py`.
Frontend: `api/dto.ts`, `api/client.ts`, `app/App.tsx`, `app/notices.ts`,
`app/readerCheck.ts`, `app/readerWorkbench.ts`, `screens/ReaderScreen.tsx`,
`screens/reader/{exerciseCandidates.ts, ExerciseCandidates.tsx,
ProposalExercises.tsx, useLibraryExercises.ts}` (new),
`screens/reader/{LibraryAnswer.tsx, LibraryPane.tsx, useReaderWorkbench.ts}`,
`screens/workbench/Workbench.tsx`; Tauri `src-tauri/src/{commands.rs, main.rs}`.
References: `_scripts/db_generate_reference.py` (the section's description),
the regenerated catalog (919 leaves, 63 sections; `Config - library_exercises.md`
new) and its two prose counts, plus the generator's commit-label refresh.
Not touched: `adaptive_difficulty/`, the scheduler, the daily plan,
`source_retrieval/reader_tutor.py`, `tutor/reader_modes.py`, `TutorOffers`,
`PracticeScreen.tsx`, any migration.

## 8. Open questions (with the default taken)

1. **Should the view run rule 4's judge at display?** The view reads the
   sources service's rule as written, so with a studied worked example in the
   last day and `ai.routing.worked_example_equivalence` resolving to a provider,
   one judge call per candidate runs (in the job, under the service's daily
   cap; cached in the ledger after). **Default: yes, as the rule says**; the
   alternative is a ledger-only read, which needs a parameter in the sources
   spec's `exposure.py`.
2. **Should the fallback turn itself on when `source_service.exercise_arm` is
   off?** **Default: no**; the owner flips `library_exercises.fallback_enabled`.
3. ~~An import admitted while the learner was away binds on resume without
   a plan pick.~~ Resolved in Codex review round 1 (F2): the pick is owed
   durably and delivered on the next sight of the problem.
4. **Exposed exercise opens with the book shown** (one hint if kept open).
   **Default: yes** (practice beside the book is the honest offer); the owner
   may prefer book hidden with only the label.
5. **"Use this one" without a session** sends the learner to Start first, as
   check me does. **Default: keep** (one consistent rule for learner picks).

## 9. Friction notes for RW3b, RW4d and RW7a

1. **RW7a** ("one exercise worth trying" per core section): use
   `ProposalExercises` (or `ExerciseCandidates` with `exerciseOpenRequest`) so
   the path's exercise gets the same honest line, exposure label and
   import-in-workbench flow; the workbench already has the `path_exercise`
   entry (book open by default), which RW7a should pick over `practice_this`.
2. **RW3b** (discovered cues, "Try this step first" on worked examples): a cue
   leading to an exercise should go through `reader.exercise_candidates`'
   exposure read rather than its own; showing a worked example records
   exposure that the rule then uses to label equivalent exercises.
3. **RW4d** (keep a comparison): nothing here stores proposals; the exercise
   view writes only impressions and the fallback's exposure rows.
4. The shell's learner-pick plumbing (`pickCheckMe`) now takes an import id and
   an entry; any later Reader pick that resumes its own problem should pass
   `entry: "practice_this"` so the learner's book choice is kept.

## 10. Owner-run commands

None required. To try it on a copy: open the Reader, select a passage, "where
else is this explained?", then "practice this question ▸"; textbook exercises
show beside items. The fallback: add `[library_exercises] fallback_enabled =
true` to the copy's `learnloop.toml`. No paid call was made in this stage; no
vault copy was opened.

## 11. Gate (implement step; targeted, per the owner's 2026-10-17 rule)

- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok
  (`TMPDIR` = the worktree's `fixtures-local/tmp`).
- `uv run lint-imports --no-cache`: **28 kept, 0 broken**.
- Targeted pytest, `uv run pytest -n auto` over 159 files (the list is
  `fixtures-local/tmp/rw4b-pytest-files.txt`: every test file that imports or
  calls the workbench, source-service, reader prompt-contract and library-ask
  handlers, the config snapshots and upgrades, the sidecar registry/contract/
  serializer/RPC pins, the mobile allowlist, architecture, table roles,
  coordinated migrations, tracked fixture databases, SQLite copy sites,
  instructional layering, the CLI help snapshot, plus `test_library_exercises.py`):
  **3,138 passed, 2 xfailed** on the final tree. (A first run had 2 failures,
  both fixed: an over-strict comparison in my own switch-off test, and RW4a's
  `test_rw4_kill_switches.py` helper, which now drops `libraryExercises` with
  the library answer.)
- No migration, no DB/connection code: no durability tests needed.
- Frontend: `npm install`; `npm run typecheck` clean; vitest on the 16 touched
  files (`exerciseCandidates`, `libraryExercises`, `libraryExercisesReader`,
  `readerWorkbenchExercise`, `libraryAsk`, `libraryAskSwitchOff`,
  `libraryAskJobs`, `Workbench`, workbench `switchOff`,
  `ReaderScreen.workbench`, `ReaderScreen.checkOffer`, `ReaderScreen.parity`,
  `app/readerWorkbench`, `app/notices`, `App.wrapUpSkim`, `SourceOffers`):
  **16 files, 146 passed**; `npm run frontend:build` ok. **Note:** one earlier
  vitest invocation ran the whole suite by accident (zsh did not split the
  file-list variable, so vitest got no paths): **142 files, 1,120 passed**,
  before the job and `ProposalExercises` changes; the landing gate's full run
  stands.
- `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml`: ok.
- References: `db_generate_reference.py` then `db_validate_reference.py`:
  **0 errors** (919 leaves, 63 sections, head 213).
- No live or paid model call; no vault copy was made or opened.

## Landing onto main

Landed in the `learnanything-merge2` worktree on branch `merge/rw4b-onto-main`, cut from main at `c9ad9cce1` (the
RW1c landing, migration head 213). The stage tip is `f54ad0582`, unchanged, built on `fab576ac1`; RW1c landed in
between. The orchestrator's last verify (Codex job `20261020-135249-T9brJ1` on `f54ad0582`) is clean: no High, no
Medium. Main was neither fast-forwarded nor pushed here.

### Commits and conflicts

- `44b8122d9`: a `--no-ff` merge of `reader/rw4b` onto `c9ad9cce1`. Conflicts, composed so both stages survive:
  - `config/schema.py`: RW1c's `ReaderTutorConfig` and RW4b's `LibraryExercisesConfig`, both kept (the root config
    already carried both fields).
  - `params/parameter_registry.py`: both kill-switch rules (`reader_tutor.*`, `library_exercises.*`).
  - `handlers/reader.py`, `reader.prompt_contract`: both contract fields (`readerTutor`, `libraryExercises`).
  - `api/dto.ts`: `libraryExercises` sits beside `readerTutor` on the contract DTO; `ReaderTutorContractDto` unchanged.
  - `ReaderScreen.tsx`: RW4b moved `openLibraryHit` before the early returns, and main had only narrowed its
    parameter to `Pick<…>`. RW4b's copy already has that signature, so the later copy goes.
  - `config/template.py`: both notes kept on every one of the 19 defaults snapshots, and each snapshot recomputed
    from the composed defaults.
  - 397 generated reference notes took main's side and were regenerated afterwards.
  - Auto-merged without conflict: `handlers/workbench.py` (RW1c's question-hint window beside RW4b's admission) and
    `db_generate_reference.py` (both section descriptions). `ReaderWorkingPosture.tsx`, `useReaderWorkbench.ts`,
    `library_ask.py`, `App.tsx` and the RPC pins were changed on one side only.
- `9d7497d92`: the RW1c hook (below), a landing commit of its own.
- `3feedbc7c`: the gate fix (below).
- `95f988292`: the references regenerated on the merged tree.
- This record.

**Callers checked on the merged tree.**
- `selection_for_region(…, vault=)` has one source caller (`library_exercises.py`) and four test callers, and all of
  them pass `vault=`. RW1c does not call it.
- `learner_pick(within=)` and `LibraryJobs.start(deliver=)` are keyword-only and optional. RW1c's jobs
  (`library_ask.start_job`, the reader tutor) and the hint and workbench-help job runners are unchanged.

### The RW1c hook (§5)

This is wired in `screens/reader/TutorOffers.tsx`, as §5 specifies:
- `OfferResult`'s practice branch renders `ProposalExercises` after the items' list.
- `runLookup` keeps the proposal on the lookup while the view is on: the `findPractice` result, or
  `practiceFromToolRun(run)` for a `find_practice` tool run.
- `practiceLookup` treats a lookup whose only proposals are exercises as `ready`, so RW1c's "nothing in your practice
  or books fits this yet" shows only when the block has nothing either.
- `ReaderScreen` passes its `exerciseProps` through the tutor rail, from `TutorAnswer` to `TutorOffers`.

Without `exercises` (`[library_exercises] enabled = false`, so no contract key), the offers are RW1c's, unchanged.
When a lookup holds only exercises, the empty items list is not rendered.

New vitest `screens/reader/tutorExercises.test.tsx` (4 tests, through the ReaderScreen harness of
`tutorReader.test.tsx`):
- A tutor practice offer shows the proposal's textbook exercises after a press. They come from the server's exposure
  view, with the exposure label "you've recently seen this page or its solution · practice beside the book, not a
  check on your own", and are recorded as impressions.
- A `find_practice` tool run's exercises show too, and an exercises-only proposal is a result, not "nothing fits".
- Switched off, the offer's markup equals the markup of a proposal with no exercises, and no RW4b RPC is called.
- Switched off, an exercises-only proposal is still RW1c's nothing-fits line.

The two "on" tests fail on the merge commit; the two switch-off pins pass on both trees. RW1c's own switch-off pins
pass: `tutorSwitchOff.test.tsx`, and `test_reader_tutor_switch_off.py` after the fix below.

### Gate fix (composition of RW1c with RW4b)

- **The failure.** `tests/test_reader_tutor_switch_off.py` failed on the merge commit (2 tests, `contract`). Its golden
  file was recorded on `fab576ac1`, before `[library_exercises]` existed. At RW4b's defaults the merged prompt
  contract also carries `libraryExercises = {fallback: false}`.
- **The fix.** The record now asserts that key's default shape and drops it. Every other field is still compared byte
  for byte, and RW1c's switches are still the ones under test.
- Nothing else failed.

### Regeneration

- **References.** `db_generate_reference.py`, then `db_validate_reference.py`: **0 errors**, `schema_head` 213,
  333 table notes, **921** configuration leaves in **64** sections (RW1c's two `[reader_tutor]` keys and RW4b's two
  `[library_exercises]` keys on 917).
  - The two prose counts in `Configuration.md` and `Database.md` were moved from 919 / 63 by hand.
  - The rest is commit labels plus RW4b's tests listed in the table notes; 399 files.
- **Defaults snapshots.** With the config template's `.pyc` cleared, all **19** `DEFAULTS_SNAPSHOT_BY_ALGORITHM`
  entries match. They were recomputed in the merge commit, because both stages moved them.
- **CLI help snapshot, RPC pins** (serializer snapshot, desktop RPC contract, mobile allowlist, sidecar registry):
  226 passed, and no file needed rewriting. RW4b's three new RPCs are desktop-only and pinned in
  `READER_RW4B_RPCS`:
  - `reader.exercise_candidates`;
  - `reader.find_exercises`;
  - `workbench.admit`, from fix round 4.
- **`validate_vault.py`**: passes (1,131 notes, 1,129/1,129 reachable).
- **Known failures from before this stage, not fixed:**
  - `desktop_validate.py` still stops on `components/pdfSelection/testing/syntheticBook.ts`.
  - `module_validate.py` reports **914** issues, up from 910 at the RW1c landing. RW4b adds modules without module
    notes, such as the sidecar's `library_exercises.py`.

### Gate

Python 3.12.14. `TMPDIR` was merge2's `fixtures-local/tmp`, and every command after the install ran as `uv run
--no-sync`. Both suite lanes ran under `flock /tmp/learnloop-fullsuite.lock` on `3feedbc7c`; the next commit
changes references only. The AD2+AD3, DL2 and RW3b worktrees and their processes were not touched. Every test uses
fakes. **This is the first full run over RW4b's code**: the stage and its 7 fix rounds ran targeted tests only.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `lint-imports --no-cache` | **28 kept**, 0 broken |
| full suite `pytest -n auto` | **14,486 passed, 2 xfailed, 0 failed** (22 min 2 s; `fixtures-local/rw4b-landing-fullsuite.log`). RW1c's landing ran 14,420 |
| `pytest -m durability` | **113 passed**, 14,375 deselected (3 min 40 s; `fixtures-local/rw4b-landing-durability.log`) |
| `npm install`, `npm run typecheck` | up to date; clean |
| `npm test` (the whole vitest run) | **150 files, 1,184 tests passed** on the first run. The `FeedbackScreen` flake did not fire |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | ok. RW4b added passthroughs to `commands.rs` / `main.rs` (8 lines) |
| thread, lock and timing tests | all passed on the first run, so none was rerun. The `"8841"` MCP flake did not fire |
| tracked fixtures, worktree | `git status` clean after both lanes and the frontend run; no `-wal` beside a fixture |

### Parity (backup-API copies; no model call completed)

**Setup** (as at the RW1c landing; scripts in `fixtures-local/landing-rw4b/scripts/`):
- **Copies.** `fixtures/linear_algebra` and `fixtures/probability` were copied once, with `copy_tree_with_databases`,
  from the main checkout into `fixtures-local/landing-rw4b/orig/`. Every other copy came from `orig/`, or from its
  upgraded copy `u27/`, through the same helper. `arxiv_v2` was not opened. Both vaults start at schema 165, label
  `mvp-0.8`.
- **Code.** Main's code is `git archive c9ad9cce1`; the merge's is `git archive 3feedbc7c`.
- **Environment.** Every run went through `env -i` with only `PATH`, `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`,
  `TMPDIR` and `LANG`. `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` were empty directories.
- **Routes.** `neutralize3.py`, under each code, sent every route to `127.0.0.1:9`. That covers:
  - the tutor and Reader routes, `source_rerank`, `worked_example_equivalence` and the exercise import's routes;
  - the hint routes, `workbench_check`, the AD routes, and the Decider routes (`blackhole_decider`).
- **Switches off.** `query_rewrite`, `tutor_query_rewrite`, `tutor_rerank`, `dense`, `[embedding]` and
  `[learner_text_gaps]`; also `build_on_serve` and outcome placement.
- **Route check.** It resolved all 58 `AITask`s on both codes: nothing outside the two loopback profiles except
  `embedding`, which is disabled and keyless.

**(a) Schema and rows, and (b) nothing served changes**

| Check | linear_algebra | probability |
|---|---|---|
| **(a)** open (migrate), main's code / the merge's | 165 → 213 (48) / the same | the same |
| schema, main@213 vs merge@213 | **identical**: 1,414 objects each, none on one side only, no SQL differs | **identical** (1,413) |
| rows of every table (338), all columns | **identical** (16,539 rows); `schema_migrations` differs only in `applied_at` | **identical** (7,637 rows; the same) |
| `foreign_key_check` / `integrity_check`, both sides | 0 / ok | 0 / ok |
| `rebuild --shadow --json` | **0 differences** after normalisation; facet 0, mastery 2, schedule 8; live database unchanged on both | **0 differences** (facet 0, mastery 1, schedule 1) |
| `doctor --json` | **0 differences** after normalisation; 57 issues, 1 error | **0 differences**; 101 issues, 48 errors |
| at `mvp-0.8`: certification, recipe gaps and curves; the Today queue at a frozen clock (no session, a session, greedy); the daily plan | **byte-identical** (cert 132,860 bytes; queue 41; the plan is off below `mvp-0.14`) | **byte-identical** (queue 67) |
| **(b)** upgraded by main's code to `mvp-0.27` (H1 method: `--to mvp-0.9`, `--to mvp-0.27`, `rebuild-derived-state` twice; all rc 0), then opened by each code | certification and curves **byte-identical** (129,651 bytes; 82 points, 7 corrections); Today queue **byte-identical** (43) | **byte-identical** (cert 17,495 bytes; queue 67) |
| the daily plan at `mvp-0.27` (frozen clock: read, serve, serve again, read) | identical except `router_decisions.card_hash`, `snapshot_hash` and the card hash in `detail_json`, which hash a card carrying the plan's ULID. A second run of main's code differs from the first in exactly these three | the same |

**(c) The Reader and practice through the real sidecar** (stdio), on copies of probability at `mvp-0.27`.

The sequence:
- `initialize`, `get_config`;
- `reader.prompt_contract`; `reader.ask_history`; one `reader.ask` on span `s108`; `reader.ask_history` again;
- one `reader.library_ask`, read through `reader.library_job` until it was done;
- `set_grading_provider manual`, `start_session`;
- one daily-plan serve (`get_daily_plan`, `next_plan_item` with `serve`), then **a learner pick** (`plan_learner_pick`
  on `pi_prob_derive_complement`), then a 12 s wait;
- on that item: `get_practice_item`, `get_probe_contract`, an authored reveal (`practice.record_hint_reveal`),
  `save_practice_draft`, `submit_attempt` with the `submissionId`, then `acknowledge_practice_submission`;
- `submit_dont_know` on `pi_incl_derive_intersections`, acknowledged;
- a workbench `open`, `get` and `submit` on `pi_story_binomial_translation`;
- `get_session`, `shutdown`.

The runs:
- (i) main (`ci`, plus `ci2`, main again as the baseline);
- (ii) the merge with `[library_exercises] enabled = false`, `fallback_enabled = false` (`cii`);
- (iii) the merge at the defaults (`ciii`).

Library-job reads that were still pending, and the JSON-RPC request number, are dropped before comparing. Both
depend on timing.

| Check | Result |
|---|---|
| every response, (i) vs (ii) | **identical** after the normalisation used at the RW1c landing (ULIDs, timestamps, the copy path, `initialize`'s schema-head fields), exactly as main against main again. The one exception is `initialize`'s method list, which gains the three new desktop-only RPCs (`reader.exercise_candidates`, `reader.find_exercises`, `workbench.admit`). They are registered even while switched off, and they refuse |
| (i) vs (iii) | the same, **plus one contract key**: `reader.prompt_contract` gains `libraryExercises = {fallback: false}`. Every other contract key is equal |
| `reader.ask` (route unreachable) | the **same error** in all runs, raw-identical: `-32001`, `provider_unavailable`, retryable. `reader.ask_history` returns the same 3 saved exchanges |
| `reader.library_ask` | the same in all runs: done, status `ok`, 8 keyword hits. It needs no model (its organizer notes are a separate call, not made), so there is no error to compare |
| the learner pick | the same step in all runs (`item`, `pi_prob_derive_complement`) |
| `pick_keyed` | **0 rows** in every run; the block events are `block_chosen`, `block_started`, `item_planned`, `item_served` × 2 each. Only an admitted exercise's keyed pick writes `pick_keyed`, and no exercise can be imported without a model (the tests cover it: `test_reader_rw4b_fix6.py`) |
| the database delta | (ii) and (iii) differ from (i) only in tables where `ci2` (main again) also differs: wall-clock floats in `attempt_debug_payloads`, `scheduler_explanations` and `scheduler_slate_candidates`; the router card hash in `attention_block_events`; AD's background rows (`judgment_ledger` uuids, `item_forecast_payloads` request hashes); and `judgment_work_claims.lease_epoch` (main 3, main again 2, (ii) 3, (iii) 2: AD's second preparation pass, the timing noted at the RW1c landing). No merge-only table or column was written |
| the attempts, all runs | **identical** evidence fields: the `open_text` attempt has `hints_used` 1, `primed` 0, correctness 1.0, `difficulty_rating` hard, assisted, not certifying; the `dont_know` is recorded as stuck, `hints_used` 0; the workbench attempt (`desktop_practice_workbench`) has `hints_used` 0, `primed` 0. The activity classes are the same, there are 0 `reveal_events`, and one client-counted `help_assists` row |

**(d) `reader.exercise_candidates` at the defaults** (the merge's sidecar, probability at `mvp-0.27`):

- **The owner's vaults have no textbook exercise to offer.** Neither has an exercise region in its teaching scope:
  - linear_algebra has no exercise-hinted block;
  - probability's only exercises are MIT "Problem Set 1" (`ext_01KYMSJT…`), which is outside the teaching scope
    ("without teaching authority").
- **The honest empty state.** `find_practice` from the Reader (two questions) returns 5 items each and
  `sourceExercises: []`. `reader.exercise_candidates` with a key the proposal never proposed (the problem set's first
  exercise) refuses `validation_error`. `reader.find_exercises` refuses `library_exercises_disabled` (the fallback is
  off). No response contains the problem set's text.
- **A seeded exercise is withheld.** On a further copy, one block was turned into an exercise: `s32` got
  "Exercise 1." and the exercise hint (`seed_exercise.py`). The exercise arm then finds it (`candidates: 1`), but
  `find_practice` does not propose it: `sourceExercisesStatus` says *"not proposed: textbook exercises are proposed
  only after a judge reads them (skipped: metered rerank route without practice_index.rerank_price_per_million)"*.
  So `reader.exercise_candidates` cannot be reached through the RPCs without a model; its withholding is covered by
  `test_library_exercises.py` (`test_r6_verify_f7_…`, `test_r2_contract_…`). With `fallback_enabled = true` on that
  copy:
  - `reader.find_exercises` shows it: label "Exercise 1", its verbatim statement, exposure `check_on_your_own`, and
    an import request.
  - Its unit was then marked `held_out_evaluation` (`mark_span_heldout.py`, a separate process, sidecar running).
  - The **kept job read again** through `reader.library_job` now returns `none_found`, `dropped.withheld = 1` and no
    candidate.
  - A **fresh** `reader.find_exercises` returns `none_found`, and a fresh `find_practice` returns no exercise.
  - The statement appears in responses before the hold-out and in **none after it**.

**`model_call_receipts`**: 0 rows in all 30 learner databases under `landing-rw4b/` (every copy, run and base
backup), so none `completed`. The other 16 `state.sqlite` files are probability's empty `.learnloop/state.sqlite`,
which have no such table.

### New findings

1. **Composition failure, fixed** (`3feedbc7c`): RW1c's switch-off golden did not know RW4b's contract key.
2. **Owner-visible: on the current vaults the feature shows nothing yet.** Textbook exercises are proposed only after
   the practice index's judge reads them. With the vaults' metered rerank route and no
   `practice_index.rerank_price_per_million`, the judge is skipped and no exercise is proposed. In any case, neither
   vault has an exercise region in its teaching scope. Either way, the Reader shows items as before; nothing breaks.
3. **The tutor offers never show the fallback.** A tutor practice lookup that found neither items nor exercises keeps
   RW1c's quiet nothing-fits line, so "find an exercise in my sources ▸" is reachable only from RW4a's "practice this
   question". This follows §5 exactly, and the fallback is off by default.
4. **Three new RPCs, not two:** `workbench.admit` (fix round 4) is the third. All three are desktop-only and pinned.
5. `src-tauri` gained the passthroughs (8 lines); cargo check is clean.

### For the owner

- **No migration and no `--to` command.** Nothing served changes (parity (a)-(c)).
- **What you see.** Wherever the Reader lists practice proposals (RW4a's "practice this question" and now the tutor's
  *practice this*), textbook exercises from your books show beside the items:
  - the exercise's own words, source and page, *open in the book ↗* and *use this one ▸*;
  - the honest line *from your book · verbatim · answer completed by LearnLoop's model*, with the key's status;
  - when you have already seen the page, its solution or the question, an exposure label, for example *you've
    recently seen this page or its solution · practice beside the book, not a check on your own*.

  *Use this one* opens the workbench at once on the statement, imports the exercise through the sources service, and
  becomes your own pick once the import is admitted. An exposed exercise opens with the book shown.
- **Why you may see none yet:** see finding 2. To get proposals, price the rerank route
  (`practice_index.rerank_price_per_million`) or route it to the ChatGPT plan, and import a book with exercises.
- **The fallback is off by default.** Turn it on with `[library_exercises] fallback_enabled = true`.
- **Turning it off:** `[library_exercises] enabled = false`. The Reader's practice proposals and the tutor's offers
  are then exactly as before (parity (c)(ii) and the switch-off pins).
- **Cost.** The exposure judge may make one `worked_example_equivalence` call per candidate, under the sources
  service's cap, when a worked example was studied in the last day. Its answer is cached in the ledger.

### Open questions (§8; defaults taken)

1. Run rule 4's judge at display: **yes**, as the rule says.
2. The fallback does not turn itself on when `source_service.exercise_arm` is off: **no**; you flip
   `fallback_enabled`.
3. (Resolved in review round 1: the owed pick is durable.)
4. An exposed exercise opens with the book shown: **yes**.
5. *Use this one* without a session sends you to Start first: **keep**.

### Open items

- **Accepted Lows:**
  - a cue's check-me reuses its item;
  - stale submits are dropped;
  - some steps run in separate transactions (fix round 6):
    - the plan's pick vs the workbench's `picked` record (recovered by the keyed receipt);
    - the idempotent selection;
    - the final admission write;
    - background work after the response.
- **Friction notes for RW3b, RW4d and RW7a** (§9):
  - RW7a uses `ProposalExercises` (or `ExerciseCandidates` with `exerciseOpenRequest`) and the workbench's
    `path_exercise` entry.
  - RW3b's exercise cues go through `reader.exercise_candidates`' exposure read.
  - RW4d: nothing here stores proposals.
  - A Reader pick that resumes its own problem passes `entry: "practice_this"`.
- **Owner-visible follow-ups:**
  - finding 2: exercises need a judge route to be proposed at all;
  - finding 3: the fallback is not offered from tutor offers.
- **From before this stage:** `desktop_validate.py` (`syntheticBook.ts`) and `module_validate.py` (914 issues).
