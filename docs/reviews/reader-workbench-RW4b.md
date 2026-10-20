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
