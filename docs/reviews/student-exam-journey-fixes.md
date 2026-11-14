# Fixes from the owner's student-journey audit (Nov 14)

The owner's audit is `docs/reviews/student-exam-journey-audit-2026-11-14.md`. This record covers its finding 1 (SJ-1,
defect A), finding 2 (SJ-2, defect B) and the deadline bug (SJ-3, defect C). Findings 3 to 6 are design questions for
the UX journey audit and are not fixed here; what this work found that belongs to them is listed at the end.

Line numbers are at the base, main `f623e525ac` plus the audit commit.

## Step 0: the paths and their siblings

### A. A skipped first subject leaves Quick Add with nothing to pick

The path:

1. New-vault onboarding, `NewVaultWizard.tsx` `StepVault` (482-493): "first subject — optional … skip this and create a
   subject on the next step." `createVault` (107-135) sends `subject: null`, gets `subjectId: null`, then calls
   `onContinueInIngest(null)` and closes the wizard.
2. `App.tsx` 2492-2497: `onContinueInIngest` opens the guided Quick Add with `quickAddDefaultSubjectId = null`; the
   dialog's `defaultSubjectId` falls back to `registrySubjectId ?? subjectOptions[0]?.id ?? null` (2470), which is
   empty in a vault with no subject.
3. `QuickAddDialog.tsx` 328-335: a `TermSelect` over `subjects` with no other control; 538-541: Analyze is disabled
   while `!subjectId`.
4. Why Quick Add needs a subject: `enqueue_quick_add` (`content/pipeline/quick_add.py` 445-446) refuses
   `subject_required`, because the source set it writes carries a `subject_id`, and `confirm_quick_add`
   (`learnloop_sidecar/handlers/ingest.py`) refuses an unknown subject. Ordinary Add instead files a source under a
   subject named from its title (`ensure_subject`, `content/pipeline/add_source.py` 1113-1132): that is the behaviour
   the audit's finding 5 questions (separate subjects per source), so Quick Add does not take it over here.

Every place a subject is required, and whether one can be made there:

| Place | Requires a subject | Can make one | Same defect |
|---|---|---|---|
| `QuickAddDialog` from the new-vault continuation (`App.tsx` 2492) | yes (Analyze) | no | **yes**: the audit's path |
| `QuickAddDialog` from Ingest's "create study map" (`App.tsx` 2250-2254) | yes | no | **yes**, in a vault with no subject |
| `QuickAddDialog` from the capture inbox (`InboxStrip.tsx` 206) | yes | no | **yes**, in a vault with no subject |
| `QuickAddDialog` inside `NewVaultWizard` (406) | yes | the wizard's own step 2 has "add subject" (661-676) | no, and unreachable: `STEP_LABELS` is `["vault"]`, so steps 2 to 5 never render (listed below) |
| Ingest screen's subject picker (`IngestScreen.tsx` 255-345, `createSubject` 775-795) | yes for its imports | yes ("+ new subject") | no |
| "add to collection", new collection (`AddToCollection.tsx` 126-136, 192-202) | yes | no | **yes**, in a vault with no subject |
| Registry review (`RegistryReviewScreen.tsx` 80-86) | to show a registry | no | no: with no subject there is nothing to review |
| The Reader's deliverable scope (`DeliverableScope.tsx` 105-106, 184) | asks only when subjects exist | no | no: it asks only when there is one to choose (finding 4's surface) |

The subject-creation call the app already uses is `api.runCliCommand(["add-subject", id, title])` (Ingest screen,
the new-vault wizard's step 2); the sidecar reloads the vault after a successful CLI run (`handlers/cli.py`), so a
following `plan_quick_add` sees the subject.

### B. The exam goal the brief promises is never made

The path:

1. `StudyMapBriefWizard.tsx` 256-304: the exam-prep goal step says "This creates the Goal in the same flow."; 93-96:
   `onSubmit(build(), outcome === "exam_prep")`.
2. `QuickAddDialog.tsx` 564-567: `onSubmit={(b) => { setBrief(b); … }}` drops the second argument; `confirmBuild`
   (217-238) sends `confirmQuickAdd` with no flag; `ConfirmQuickAddInput` (`api/dto.ts` 4128-4137) has none.
3. Sidecar `confirm_quick_add_rpc` (`handlers/ingest.py` 1455-1530): `ConfirmQuickAddInput` (1410) has no
   `create_goal`; it calls `enqueue_quick_add`.
4. `enqueue_quick_add` (`quick_add.py` 430-490) calls `enqueue_quick_add_build` (`jobs.py` 5119-5169), whose synthesis
   payload is `source_set_id`, `brief`, `mode`, `apply` (5147-5154): no `create_goal`.
5. `handle_bootstrap_synthesis` (`jobs.py` 1806-1903) reads `payload.get("create_goal", False)` (1855, 1872) into
   `create_study_map`, whose apply step `_apply_map` (`source_set_synthesis.py` 2772-2801) makes the goal only when
   `create_goal and _is_exam_prep(brief)` (2793), through `_create_goal_from_brief` (title, `due_at`,
   `target_recall`, `exam_item_count`, `intent_sentence` from the brief; the id keyed by the proposal, so a second
   apply of the same proposal finds the same goal).

Every place the wizard opens and what it does with `createGoal` and the due date:

| Opener | `createGoal` | Due date |
|---|---|---|
| `QuickAddDialog` (564) | dropped | in the brief, but the wizard's reopen starts it blank (C) |
| The Ingest screen's collections, "edit brief" (`SourceLibrarySidebar.tsx` 756-766) | dropped: `onSubmit={(brief) => …}`; `synthesize` (576-598) sends `buildStudyMap` with no flag | same as above |

No other screen mounts the wizard (Library, Reader and onboarding do not; onboarding reaches it only through
Quick Add).

Every enqueue path for a study-map build, and whether it carries `create_goal` when the brief asks for a goal:

| Path | Brief from | Carries `create_goal` | Should it |
|---|---|---|---|
| Quick Add: `confirm_quick_add` → `enqueue_quick_add` → `enqueue_quick_add_build` | the wizard | no | **yes**: the wizard's promise |
| Collections "synthesize →": `build_study_map` (bootstrap) → `enqueue_source_set_build` (`jobs.py` 5171-5236) | the wizard | no | **yes**: same wizard, same promise |
| `build_study_map` when the subject has a map → `enqueue_source_set_append` → `append_synthesis` | the wizard | no | see "append" below |
| Quick Add or a collection build whose `auto` job finds a map at run time (`jobs.py` 1835-1842 diverts to `handle_append_synthesis`) | the wizard | the payload would, the append does not read it | see "append" below |
| Ordinary Add's automatic build (`add_source.py` 1626-1660) | `_default_brief({"practice_items": "as_you_read"})`, never exam prep | no | no: no brief asks for a goal |
| `enqueue_auto_build` (`jobs.py` 4223) | the planner above | no | no, same reason |
| Retry and revalidation (`retry_synthesis`, `jobs.py` 5309-5380) | copies the failed job's payload | whatever the job had | yes, unchanged: it keeps what the build was asked |
| `create_study_map` RPC (`handlers/ingest.py` 1008-1044) and CLI `create-study-map` / `synthesize` (`cli/app.py` 659, 786) | caller | yes, explicit `create_goal` / `--create-goal` | already correct |
| CLI `quick-add` (`cli/app.py` 395-440) | the default brief (no options) | no | no: no exam brief can be given there |
| Capture resume (`handlers/capture.py` 165-176) | the stored `ConfirmQuickAddInput` | yes once the input carries it | — |

The append: `append_source` (`content/synthesis/source_append.py` 365) takes no `create_goal` and makes no goal, by
the same design as the K2.4a tail (the append applies §10.3's routine items, `refactor-k2.4a.md` row 26). An exam-prep
brief on a subject that already has a map therefore still makes no goal after this fix. That is a design question
(which facets would that goal cover: the subject's whole map, or only what the append added?) and is SJ-8 below; the
wizard's copy says so instead of promising it.

### C. Reopening the brief editor loses the deadline

`StudyMapBriefWizard.tsx` 60: `const [dueDate, setDueDate] = useState("")`, where every other field starts from
`initialBrief`; `build()` (83-90) writes `dueAt` from `dueDate` only, so a reopened exam-prep brief saved again loses
its deadline. Both openers pass the saved brief back (`QuickAddDialog` 560 `effectiveBrief()`,
`SourceLibrarySidebar` 758 `briefs[id]`), so both lose it.

Every other field of the wizard starts from `initialBrief`: outcome, starting level, level notes, depth, notation,
include and exclude topics, scope, practice timing, goal title, intent sentence, target recall, held-out item count,
and the authoring preset (carried through `build()`). Two notes, neither a loss: a blank goal title is saved as
"Exam preparation" and reopens as that text; and `build()` writes only the wizard's own fields, so a key the wizard
does not edit would be dropped, but neither opener puts one in (Quick Add's brief and the collections' briefs come only
from the wizard and Quick Add's own preset, whose `authoringPreset` is carried).

The other date inputs in the app: `GoalWizard` (create only), `DeliverableScope` (create only), and `IntentControl`
("move the deadline": an empty field with its own save, the current deadline shown beside it). None reopens a saved
value into a form that saves everything, so none has the slip.

## SJ-1 (A): a subject can be made where one is required (`dd898a5ef2`)

Fail first: `QuickAddDialog.test.tsx` "with no subject to pick, lets the student create one and Analyze enables" and
"a refused subject leaves Analyze disabled and says why" both failed at the base on `Unable to find an element with the
placeholder text of: new subject title` (the first assertion, Analyze disabled with no subject, passed: the audit's
state). `AddToCollection.test.tsx` "a vault with no subject can still start a collection: the panel makes one" failed
the same way.

The choice: an inline create-subject control, not Ordinary Add's title-named subject. Quick Add needs a subject
because its source set carries one; naming it from the source's title is the behaviour finding 5 questions (three
materials, three subjects), and it would keep the copy's promise only by making the subject for the student. The
control asks for the student's own name (one course, finding 5's direction) and keeps "create a subject on the next
step" true.

The fix: `components/NewSubjectControl.tsx`, a title field and "create subject" over the existing
`api.runCliCommand(["add-subject", id, title])` (the Ingest screen's call; the sidecar reloads the vault after it),
the id the title in kebab case as the Ingest screen makes it. Quick Add shows it in place of the picker when there is
no subject to pick, keeps what it made in its own list (the caller's list arrives from the app snapshot) and selects
it; a refusal (the CLI's stderr) shows as the dialog's error. The add-to-collection panel's new-collection form shows
the same control when the vault has no subject.

Siblings (step 0's table): the three Quick Add openers share the dialog, so all three are fixed; add-to-collection is
fixed; the Ingest screen already had its own control; registry review and the Reader's deliverable scope do not need
one. The new-vault wizard's own "add subject" is in its unreachable step 2 (SJ-9). Copy: the new-vault wizard's "skip
this and create a subject on the next step" is now true and unchanged.

## SJ-2 (B): the exam goal reaches the build (`4983f16155`)

Fail first, at the base:

- The audit's probe as a test: a Quick Add with the wizard's exam-prep brief (title, `dueAt`, target recall, item
  count), enqueued as the dialog's confirm enqueues it, completed with `applied: True` and `len(goals) == 0`
  (`AssertionError: assert 0 == 1`). It ran as a temporary file, since the committed test passes the new argument.
- `QuickAddDialog.test.tsx` "an exam-prep brief asks the build for its goal, with the brief's deadline":
  `expected undefined to be true` (the dialog sent no flag); "a brief that is not exam prep asks for no goal": `expected
  undefined to be false`.
- `SourceLibrarySidebar.test.tsx` (new) "an exam-prep collection brief asks the build for its goal" and "a collection
  with no brief asks for no goal": `expected undefined to be true` / `false`.
- `test_quick_add.py::test_exam_prep_quick_add_ends_with_an_applied_map_and_its_goal` and
  `::test_quick_add_without_an_exam_brief_makes_no_goal`, `test_ingest_jobs.py::test_a_build_asked_for_its_goal_carries_create_goal_to_the_synthesis_job[quick_add|source_set]`,
  `test_sidecar_quick_add.py::test_confirm_quick_add_forwards_the_exam_goal_flag` and
  `::test_confirm_quick_add_without_the_flag_asks_for_no_goal`,
  `test_build_study_map_routing.py::test_a_collection_build_asked_for_its_goal_passes_create_goal`: each failed on the
  missing argument or field (`TypeError` unexpected keyword `create_goal`, pydantic `extra_forbidden`, `KeyError:
  'create_goal'`).

The decision, from the spec: the goal stays behind the explicit flag, not "every exam-prep brief". Spec §5.1 says the
flow *can* end by creating the goal "when the brief's outcome is exam preparation (or the user opts in)"; the
synthesis already gates on `create_goal and _is_exam_prep(brief)`, and the CLI's `--create-goal` is opt-in. The wizard
sets the flag exactly when it shows the promise (`outcome === "exam_prep"`), so in the app copy and behaviour agree;
keeping the flag explicit is what keeps an old job from minting a goal (below).

The fix: `createGoal` from the wizard's `onSubmit` is kept by Quick Add (cleared by the enrichment preset, which sets
general learning) and sent with `confirmQuickAdd`; the collections section keeps it per collection and sends it with
`buildStudyMap`. The sidecar's `ConfirmQuickAddInput` and `BuildStudyMapInput` take `create_goal`;
`enqueue_quick_add`, `enqueue_quick_add_build` and `enqueue_source_set_build` take it and write `create_goal: True`
into the synthesis payload only when asked (a build that does not ask keeps the payload it always had). The job
handler and `_apply_map` were already right. The end-to-end test runs the real batch (fake inventory and synthesis
clients) and finds the applied map and one goal with the brief's title, `due_at`, target recall, held-out count and
the minted facets; the general-learning build finds none.

Siblings (step 0's table): Quick Add and the collection build are fixed. The append is not forwarded the flag
(`build_study_map` passes it only to `enqueue_source_set_build`; a test pins that), because the append makes no goal:
SJ-8. The automatic build's brief is never exam prep; retries and revalidation copy the job's own payload; the
`create_study_map` RPC and the CLI already carry the flag; CLI `quick-add` takes no brief. The K2.4 goldens
(`test_synthesis_tail_golden.py`, with bootstrap's clean case applying with its exam goal) pass unchanged: they call
`create_study_map` directly.

Copy: the wizard said "This creates the Goal in the same flow." That stays true for a subject's first map and is false
for an append, so it now reads "This creates the Goal in the same flow when it builds the subject's first study map.
Adding to an existing map leaves your goals as they are; make one from Today."

### What a rerun of an old exam-prep brief does now

Nothing new: no rerun mints a goal it would not have minted before.

- A retry, a revalidation (`reuse_candidate`) or a crash-resume of a synthesis job queued before this change copies or
  reads that job's payload, which has no `create_goal`, so it makes no goal, as before.
- A capture whose Quick Add was in flight across the upgrade: its stored request has no `create_goal`; the request
  model now has the field, so `_request_hash` differs and the resume is refused as a conflict, as for any
  request-model change (`identity_pins_helpers` registers `capture.py::_request_hash` with that reason). It never
  mints a goal.
- A new build with the same brief from the app is a new confirmation through the wizard: it asks for the goal when the
  brief is exam prep, as the wizard says. If the subject already has a map the build is an append and makes none. A
  second apply of the same proposal finds the goal it made (the goal id is keyed by the proposal).
- `learnloop rebuild` replays derived tables; it runs no synthesis and never writes `goals.yaml`.

So no guard was needed.

## SJ-3 (C): the wizard reopens with the deadline (`0e057e91e8`)

Fail first: `StudyMapBriefWizard.test.tsx` (new) "starts the due date from the brief it was opened with" (`expected
'' to be '2026-11-27'`), "saving without touching the date keeps the deadline, and every other field" (the saved brief
lost `dueAt`), "a date-only deadline opens on that day" (`''`). "clearing the date removes the deadline" passed at the
base and still does.

The fix: the date starts from `initialBrief.dueAt`, read back as the local day `build()` saved (it saves the day's
23:59:59 local time as an ISO instant, whose UTC date is the next day west of Greenwich); a bare `YYYY-MM-DD` is taken
as the day. The test file passes under `TZ=UTC`, `America/New_York` and `Asia/Tokyo`. The round-trip test reopens a
brief with every wizard field set and saves it unchanged: the saved brief equals the opened one, so no other field has
the slip. Both openers (Quick Add, the collections' "edit brief") use the wizard, so both are fixed.

## Gates

See the report for the run: typecheck, vitest, the frontend build, the targeted Python gate
(`scripts/affected_tests.py` against the base plus the rules' fixed list), `lint-imports`, `ruff`, the four vault
validators, `check_gate_partition.py`, and one regeneration of the vault references.

## Found on the way (for the UX journey audit; not fixed)

- **SJ-8** (finding 2's neighbour, design): an exam-prep brief on a subject that already has a study map makes no
  goal: Quick Add or "synthesize →" route to the append, which has no goal step. And the goal a first map makes scopes
  only the facets that map minted, so the lectures or problem sets a student adds later never join the exam goal's
  scope. Choices: (a) the append makes or extends the goal over the subject's whole map; (b) leave goals to Today's
  goal wizard and the Reader's deliverable scope (finding 4), and say so (what the copy now does). Recommendation: (b)
  now, and settle (a) with finding 4's "exam goal during course setup", since that goal should cover the course, not
  the first book.
- **SJ-9** (finding 4, design): `NewVaultWizard` renders only its first step (`STEP_LABELS = ["vault"]`); creating the
  vault closes it. Its steps 2 to 5 (first source with "add subject", proposals, the optional goal with `GoalWizard`,
  the loop) and their header comment are unreachable. The goal step is the course-setup goal finding 4 asks for;
  whether to restore it or delete the dead steps is that design's call.
- Finding 4: the brief wizard's exam goal (title, intent, deadline, target recall, held-out items) and the Reader's
  "Learning this for something?" (sentence, topics, deadline, exam) are two ways to make an exam goal with different
  fields and different scopes (the map's minted facets against the resolved deliverable scope).
- Finding 5: Quick Add still requires a subject while ordinary Add files each source under a subject named from its
  title; after SJ-1 a student who starts in Quick Add names the course once, and one who starts with ordinary Add gets
  one subject per source. The two entry points disagree on what a subject is.
