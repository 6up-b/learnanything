# The new-vault journey for a student preparing for an exam (owner's audit, 2026-11-14)

The owner evaluated the journey of making a new vault as a student studying for a midterm or final: seeding priors from past exams and coursework, adding a textbook, adding lectures, and setting the exam as the goal. The audit below is the owner's, kept as written. The triage after it is the refactor orchestrator's.

## The audit

Method: Playwright against the actual React frontend and Python sidecar with disposable vaults. Synthetic textbook material, lecture captions and a graded exam were imported, then a midterm with a November 27 deadline was created. Today showed the saved goal.

| Student need | Current assessment |
|---|---|
| Create a course vault | Has a reproducible onboarding blocker |
| Seed knowledge from past exams/coursework | Backend support exists; desktop workflow is incomplete |
| Add a textbook | Available; extraction, curriculum building, and practice readiness need clearer distinctions |
| Add lectures | Captions, YouTube, and audio paths exist; configuration and course association need work |
| Study toward a midterm | Available through the Reader, but poorly connected to onboarding |
| Read → practise → feedback → independent checks | Implemented and tested in parts; complete live journey still needs validation |

The most consequential findings:

1. **"First subject (optional)" can strand the student.** Skipping it creates the vault, then opens Quick Add with an empty, required subject picker. That dialog has no subject-creation control, so Analyze remains disabled. The preceding copy explicitly promises subject creation on the next step. Required-subject gate: `apps/learnloop-tauri/src/components/QuickAddDialog.tsx:541`.
2. **Quick Add's exam-prep flow promises a goal it does not create.** The brief wizard says "This creates the Goal in the same flow." Its callback discards the `createGoal` argument, and the queued synthesis payload omits `create_goal`. An additional probe produced a completed, applied study map with zero goals despite an exam-prep brief and deadline. Callback: `apps/learnloop-tauri/src/components/QuickAddDialog.tsx:564`; build payload: `src/learnloop/content/pipeline/jobs.py:5147`.
3. **Importing graded work does not onboard prior performance.** The initial level buttons seed one global self-rating. Adding a graded exam through "past exam or problem set" marked it for practice only; it created no historical attempts. The advanced exam-seeding screen directs students to `learnloop seed-exam-attempts --outcomes <file>`. That backend does support discounted, backdated evidence, but entering grades, dates, and reviewing question mappings needs a desktop interface. General coursework has no comparable visible onboarding journey. Current CLI handoff: `apps/learnloop-tauri/src/screens/IngestScreen.tsx:1417`.
4. **The best midterm flow is hidden inside the Reader.** "Learning this for something?" accepts a natural-language goal, topic list, deadline, and exam checkbox, and saves a real goal. The newer implementation also supports scope corrections, syllabus inputs, cross-book study paths, and "Am I ready?" checks. This should be prominent during course setup; currently it is a small link leading to a compact sidebar form. Implementation: `apps/learnloop-tauri/src/screens/reader/DeliverableScope.tsx:299`.
5. **Materials do not naturally converge into one course.** Ordinary Add chooses subjects from individual source titles. In the audit, the vault accumulated "Probability 101", "Textbook", and "Lecture" as separate subjects. There is no course selector in ordinary Add. Collections and deliverable scope can connect materials, but students must discover those mechanisms themselves. Subject assignment: `src/learnloop/content/pipeline/add_source.py:1113`.
6. **Readiness messages blur missing materials and unfinished curriculum.** Before a study map existed, the midterm resolver described conditional probability and Bayes' theorem as "not in your library yet", while those passages were visible in the Reader. It needs to distinguish "material imported", "topics still being built", "scope needs review", and "ready to practise". The underlying readiness model is better: it distinguishes demonstrated, predicted likely, and untested, rather than equating reading with mastery. Readiness logic: `src/learnloop/source_retrieval/deliverable_path.py:1448`.

The initial empty Library is reasonably clear. The explicit new-vault route then introduces inventories, token budgets, enrichment, synthesis, and advanced screens before establishing the student's course and exam. There is also a smaller deadline bug: reopening the brief editor initializes its date blank, so saving another edit can discard the previous deadline. Date initialization: `apps/learnloop-tauri/src/components/StudyMapBriefWizard.tsx:60`.

## Triage (orchestrator)

Checked against the code at main `f623e525ac`:

- Finding 1: the Analyze button is disabled while `subjectId` is empty (`QuickAddDialog.tsx`, the `disabled={busy || !source.trim() || !subjectId || ...}` line), and the dialog offers no way to make a subject.
- Finding 2: the wizard's `onSubmit` receives `(brief, createGoal)`; Quick Add's handler takes only the brief. The bootstrap batch's synthesis payload has `source_set_id`, `brief`, `mode`, `apply` and no `create_goal`, while the job handler reads `payload.get("create_goal", False)` and the synthesis already wires an exam goal when asked.
- The deadline bug: `useState("")` for the due date, where every other field starts from `initialBrief`.

| # | What it is | Where it goes |
|---|---|---|
| 1 | Defect: a promised step that does not exist | Fixed from a failing test in the step this record lands with |
| 2 | Defect: a promise in the copy that the flow drops | Same step |
| Deadline | Defect: an edit can lose a saved deadline | Same step |
| 3 | Design: a desktop way to enter graded work over the existing `seed-exam-attempts` backend (grades, dates, the question-to-topic mapping to review); the same question for coursework | UX journey audit, persona "student preparing for an exam"; needs a spec before code |
| 4 | Design: the exam goal asked during course setup, using the Reader's deliverable scope | Same |
| 5 | Design: one course as the thing a student's materials join | Same; touches the ingestion hierarchy (library first, "add to study map") |
| 6 | Design and wording: readiness states named for what they are | Same; the states exist in the model, the messages do not carry them |

Not verified by this record: the audit's screenshots (they were under `/tmp`) and the "complete live journey" row, which the audit itself marks as still needing validation.
