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
