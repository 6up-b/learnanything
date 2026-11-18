# UX journey audit

The end-of-queue UX journey audit the owner asked for on 2026-10-31 (brief and dated additions: Nov 8, Nov 9, Nov 12, Nov 14, Nov 18). Branch `docs/ux-journey-audit`, written against main `8c40bd4343`.

| Part | What | Where | State |
|---|---|---|---|
| 1 | Criteria: Jenson, Matuschak, ISO 9241, Norman, Nielsen and the owner's principles, as a pass/fail checklist | `docs/reviews/ux-journey-audit-criteria.md` | done |
| 2 | Inventory of every journey on every frontend, from the code | section 2 below | done |
| 3 | The persona walks: per-walk reading, the same surfaces side by side, scorecard, findings, defects, proposals, fix stages | sections 3 onward | added when the walks are complete |

Fixes are proposed here, not made. The owner reviews this audit before any fix stage is queued. The one exception is the graded-work entry, which the owner asked to be specified and built inside the audit's fix stage (brief, Nov 14).

## 1. How to read this

**Owner decisions of 2026-11-18,** taken as dated additions to the brief:

1. The persona walks run on the owner's real model route (the ChatGPT plan), so personas judge real questions, grades, feedback and lessons. Only the phone walk uses faked models.
2. When help shows the learner part of an answer, feedback will quote the text that gave it away, per rubric criterion ("the tutor showed you this step: ..."). Wording and placement are a design question for this audit. Section 2.5 lists where the app says "with help" today.
3. The Reader will get a cheap natural-language search across all of the learner's sources. Results are passages, not a generated answer. Its screen belongs to the Reader redo, beside syntopic reading. Section 2.11 lists every way to search or jump across sources today.
4. Reader margin cues will be chosen by a small decision model, with a generated one-line explanation and an exact quoted sentence for each cue shown. Section 2.12 records what a cue shows today.

**Paths.** `D/` is `apps/learnloop-tauri/src/`, `M/` is `apps/learnloop-mobile/src/`, `S/` is `src/learnloop/`, `T/` is `src/learnloop/tui/screens/`. Line numbers are at `8c40bd4343`. Labels are quoted exactly as the code writes them; `{x}` marks a filled-in value.

**Defaults assumed.** The simple shell and simple feedback (`[ui] shell = "simple"`, `practice_feedback = "simple"`, `S/config/schema.py:4353`). The backend's feature switches are on by default for a vault at the current algorithm tag: lessons (`teacher.enabled`, `schema.py:4450`), the workbench, recap and wrap-up, adaptive hints, the Ask panel, adaptive difficulty, margin cues, reading paths, compare, correspondence and figures. The exceptions that default off are symbolic checks in the workbench, the library-exercises fallback and note gaps. The desktop holds all of these as off (`D/app/algoConfig.ts:98-117`) only until the sidecar sends its config. No switch can be changed from the UI: every one is a `learnloop.toml` edit.

**Reachability marks** (the brief's four):

- **pointer**: reachable by pointer from a visible control;
- **keys**: keyboard only (including palette-only and palette `>` CLI grammar);
- **switch**: behind a switch whose default hides it (named);
- **none**: no entry in this frontend (CLI only, or not built).

**How this was made.** From code and specs only; nothing was run. Four read-only surveys of the code (desktop Today, practice and feedback; the desktop Reader; desktop ingest, goals and settings; phone, terminal app, MCP and lessons) were merged here. Every claim that changes a conclusion below was re-read at the cited lines, and two survey claims were corrected that way (lessons and the workbench are on by default, not off; "Continue your lesson" has no entry in the simple shell). Criteria ids (J1, M4, O7, U11, ...) refer to the criteria page.

---

## 2. Inventory

### 2.0 The journeys at a glance

| Journey (brief item 2) | Desktop | Phone | Terminal app | Chat (MCP) |
|---|---|---|---|---|
| First run, new library | pointer (but the new-library route lands in the token-budget builder, 2.6) | pointer, after pairing from a terminal (2.16) | none (opens an existing vault) | none |
| Ingest and the library | pointer (Add); exam seeding none (CLI only) | none (capture only) | none | read only (`library`) |
| Capture | pointer, but the inbox shows only when something new arrived (2.7) | pointer | none | none |
| A day: Today and the plan | pointer | pointer | pointer (keys) | read only (`today`) |
| Stop offer and "keep going" | pointer (shown as the plan-done screen, reason never shown) | pointer (same) | none | none |
| Practice and cold checks | pointer | pointer | keys | none (practice "happens in the app") |
| Feedback, follow-ups | pointer | pointer | keys | none |
| "Coming up" (dated checks) | pointer, in the Reader only | none | none | none |
| Goals: create | first goal: no Today control (2.8); Reader or Quick Add brief only | none | none | none |
| Goals: progress | pointer (goal card details) | none (placeholder) | none | read only (`progress`) |
| Goals: change deadline, scope, delete | none | none | none | none |
| "Am I ready?" | pointer, Reader only | none | none | none |
| Reader: Guide, paths, intent box, Ask | pointer | partial: sections, Ask on a selection (2.16) | none | passages only (`find_sources`) |
| Compare, find-section, also in your books, side by side | pointer, with gaps (2.9, 2.11) | none | none | none |
| Show me figures | pointer | none | none | none |
| Workbench and help ladder | pointer | none | none | none |
| Margin cues | pointer (hover, click) | none | none | none |
| Teacher lessons | pointer from offers and topic actions; resuming an open lesson: none in the simple shell (2.13) | none ("lessons wait on the desktop") | none | none |
| Ask tutor | pointer | Reader selection only | none | none |
| Graded past work (exams, homework) | none (CLI only) | none | none | none |
| Own notes (Markdown folders, Obsidian, flashcard decks) | single `.md` files only; folders, vaults and decks none | none | none | none |
| Settings, switches, spend | pointer for routes; switches none; spend caps none (2.14) | none | none | none |
| Multi-device hand-off | pointer | pointer | none | none |

### 2.1 Shell and navigation (desktop)

| Place or tool | Label | Where | Key | Mark |
|---|---|---|---|---|
| Today | "Today" | `D/components/ShellNav.tsx:65`, labels `D/app/shell.ts:33` | Alt+1 | pointer |
| Library | "Library" | `shell.ts:34` | Alt+2 (and Alt+7) | pointer |
| Reader | "Reader" | `shell.ts:35` | Alt+3 (and Alt+9) | pointer |
| Progress | "Progress" | `shell.ts:36`; opens the concept-graph screen (`shell.ts:53-57`, `D/app/App.tsx:2223`) | Alt+4 | pointer |
| Add | "+ Add" (tooltip "Add a book, paper or video (Ctrl+O)") | `ShellNav.tsx:76-77` | Ctrl+O (opens the OS file chooser, not the popover) | pointer |
| Palette | "^K" | `ShellNav.tsx:81` | Ctrl+K, Ctrl+P, ":" | pointer |
| ⋯ menu | "Settings Ctrl+,", "Under the hood", "Switch library" (a label), the recent libraries, "Open another library…", "New library…", "Keyboard & help" | `ShellNav.tsx:177-219` | Ctrl+, and Alt+S (Alt+S also closes Settings) | pointer |
| Grading down | "Grading isn't working · Fix" | `ShellNav.tsx:72` | — | pointer, only when an AI is connected and grading fails |
| Under the hood tools | Imports & builds, Study-map changes, Subjects & topics, Concept graph editor, Analyst views, Mistake history, Calibration, System health, Data, Files, Inspector, Spend & AI routes | `shell.ts:86-99` | Alt+5, Alt+6, Alt+0 for some | pointer |

Palette commands (`D/app/App.tsx:1891-1945`): "Add a book, paper or video", "Continue reading", "Start today's plan", "Check what I already know", "Open settings", "Under the hood", "Go to Today / Library / Reader / Progress", "Ask the tutor about this", "Keyboard & help", "Open another library…", "New library…", and each Under-the-hood tool ("under the hood · was X"). A leading `>` switches to the CLI grammar (`D/components/CommandPalette.tsx:88-120`), whose words are internal ("LO / PI", "probe", `populate-goal`, `calibrate`, `ingest --allow-auto-captions`).

Problems the shell shows from code:

- "Progress" opens the concept-graph screen, with an "edit" toggle (`D/screens/GraphScreen.tsx:450`); "Concept graph editor" and "Analyst views" under the hood open the same screens.
- Palette "Check what I already know" (`App.tsx:1909`) only goes to Progress, hinted "on Progress: pick a topic, then Check what I already know".
- During a practice exam or calibration, the place buttons move their highlight but the screen stays (`App.tsx:1974`, `:1981`); the exam is left only with Esc (`D/screens/ExamScreen.tsx:143`).
- One key, two meanings: Ctrl+K is the palette and, in the workbench, "Check my work" (`D/app/keymap.ts:132-139`); `?` is "why?" on Today and Ask in practice and feedback; Ctrl+S is Skip in practice, Alt+S is Settings.
- Simple Today has no key bar, so `?`, `d`, `l`, `p`, ←/→ and Enter are discoverable only through the "(l)", "(p)" and "↵" hints.

### 2.2 A day with LearnLoop: Today, the plan, the stop offer

Today is `D/screens/today/TodayPlace.tsx`; the plan sentence is built in `D/app/todayPlan.ts`.

**Entry points.** "Today" (Alt+1); palette "Start today's plan"; the app opens on it.

| Control | Label | Where | Key | Shown when |
|---|---|---|---|---|
| Minute choice | "10m", "25m", … (radio spans) | `TodayPlace.tsx:152`, `:916` | ←/→ | plan not done |
| Begin | "Begin ↵" / "Continue ↵" / "opening…" | `:891` | Enter | rows exist |
| Plan sentence | "25 minutes today: …", "About N minutes suggested today: …", "About N minutes left today", "… past today's suggested time" | `:841-846`; `todayPlan.ts:197-211` | — | plan open |
| why? | "why? ▸", then "How today's minutes are split:", "details ▸" | `:848`, `:190-217` | `?` | plan open |
| Block rows | "6 short questions · X", "Fix a mix-up · X", "New: X", "A step further · X", "Your pick · X", "A lesson you could take · X", with " · on your own" | `todayPlan.ts:71-84`, `:117`; `TodayPlace.tsx:876` | — | plan rows |
| Skip a block | "skip" | `:880` | — | current block |
| Something else | "Something else would help" → "What would help right now?" with server options ("Another question", "Review something from earlier", "Something new", "Read the source", "Learn this", "Stop for today"), "Anything you'd like us to know? (optional)", "This is only what you'd like to do next. It isn't counted as knowing something.", "Never mind" | `D/screens/today/SomethingElse.tsx:19`, `:124-155`; options `S/router_objective/preferences.py:86-91` | — | session open and the sidecar's `somethingElse` flag |
| Threads | "Pick up a thread"; "resume ▸" / "open in book ▸" / "continue ▸"; "more ▸" | `TodayPlace.tsx:250-283` | — | open questions or problems exist |
| Captures | "New captures ▸" | `:302` | — | new captures exist (2.7) |
| Goal card | see 2.8 | | | an active goal |
| Lesson offers | see 2.13 | | | |
| Full list | "all of today's list (l)"; "back to the plan (p)" | `:940`, `:368` | l, p, Esc | always |
| Streak | "4 days · best 9" | `todayPlan.ts:262` | — | streak > 0 |
| Wrap-up line | "Reading wrap-up ready — under a minute ▸" | `D/screens/reader/recapCopy.ts:18` | — | after leaving the Reader |

**States.**

| State | Text | Where |
|---|---|---|
| Loading | "…" | `TodayPlace.tsx:764` |
| Failed | "Couldn't plan today · Try again" | `:756-758` |
| No books | "Nothing to plan yet. Add a book, paper or lecture and LearnLoop will plan your days around it." + "+ Add" | `:780-783` |
| Waiting | "Nothing to do right now. Back in N min: a question on X." | `D/app/dailyPlan.ts:187` |
| Question open elsewhere in the session | "A question is in progress on X. What comes next is chosen when you finish it or go on." | `dailyPlan.ts:193` |
| Deciding | "Choosing what's next…" | `TodayPlace.tsx:846` |
| Empty | "Nothing planned for today." | `:807`, `:846` |
| Stale choice | "That is no longer something the plan can do. Here is what it can do now." (the server's line) | `S/daily_plan/learner_action.py:415` |
| Full list failed | "Couldn't read today's list" / "Couldn't refresh today's list; what's below may be out of date · Try again" | `:374-376` |
| No model | none needed: the plan runs without a model; failed rows read "(not available right now)" in the classic view (`D/screens/today/DailyPlanView.tsx:129`) | |

**Re-entry** (more than `reentry_gap_days`, default 7, away; `S/daily_plan/reentry.py:5`): "Welcome back. A short catch-up today: N minutes of the most useful questions. Nothing else is waiting on you." (`todayPlan.ts:218`); under why?: "You were away N days. Today's catch-up starts with what faded most: … The rest comes back over the next days, a little at a time." (`:225-227`); done: "Catch-up done." "Something new" is hidden during re-entry (`TodayPlace.tsx:813`). Nothing asks about a goal whose date has passed (brief, persona 5): not found.

**The stop offer.** There is no screen of its own. When the router's objective stops at a boundary, the desktop shows the plan-done screen: "Done for today · N minutes." (`todayPlan.ts:251`) with "Keep going ↵", "Something new" and "Done for today" (key `d`). The phone does the same (`M/today/PlanToday.tsx:104-121`, comment "J5: the stop offer"). The stop's reason (`stopReason`, `D/api/dto.ts:8259`, `:8334`) is never rendered on either, so a stop the engine chose looks exactly like finishing the plan. "Something new" then reads "about N min of new material today, and a little more review on the days after. add it" or "Nothing new is ready yet. Keep reading and LearnLoop will have more."

**Exit.** "Done for today" ends the session and shows "Since last time: ● X (on your own) · ◌ Y (with help)" with "Done ↵" (`D/components/SessionFinishHud.tsx:135-150`).

**Jargon under why?** The block reasons the server writes ("maintain: … past their 90% recall target", "repair: … where a diagnosed problem is still open", "push: …", `S/daily_plan/lanes.py:465-490`) appear to reach `block.why`; not traced end to end.

### 2.3 Practice, cold checks, short checks, the practice exam

`D/screens/PracticeScreen.tsx`. **Entry points:** Today "Begin" / "Continue", a full-list row, the goal card's "Practise for this goal", feedback's "Try a similar one (t)", calibration's "Practice next target".

| Control | Label | Where | Key |
|---|---|---|---|
| Submit | "Submit" | `:2307` | Ctrl+Enter |
| Hint | "Hint" / "Hint again" (hidden during a short check, and on a cold follow-up unless the server sends the take step) | `:2315`, `:2313` | Ctrl+H |
| Stuck | "I'm stuck" | `:2319` | Ctrl+D |
| Ask | "Ask" | `:2322` | `?` |
| Skip | "Skip" | `:2325` | Ctrl+S |
| Card controls | "⋯", then "THIS CARD: reword · split in two · retire · ↓ easier · ↑ harder · ◊ teach it" (spans with no role or tab stop: pointer only; tooltips say "mint an easier sibling one depth waypoint down…") | `:1644`; `D/components/CardControls.tsx:109-116`, `:417-489` | — |
| Back | "esc back" (key bar) | `:2401` | Esc |

"Skip" is a plain skip button next to "I'm stuck" (criterion O4 asks whether skip is "not now"; the walk should check what it records).

**Cold checks.** The banner comes from the server (`S/intent/checks.py`): "A check on your own. Help is still here — using it makes this practice with help." (`:42`); "A check on your own: this one is measured on your own, so no help is offered." (`:56`); "Practice: you've seen this answer, so this one is practice, not your check on your own. Your check comes back later." (`:50-53`). The first hint on a check shows "Taking any help makes this attempt practice with help, not a check on your own." with "Take a hint" (`:45`, shown at `PracticeScreen.tsx:2196-2199`). A cold follow-up reads "On your own · no hints on this one", or, opened from feedback, "On your own · this one can't count when it's opened from feedback. Go back and open it from Today." (`:1736-1737`); Ctrl+H there: "No hints on this one: it's a check on your own." (`:1196`).

**Short diagnostic check.** "Feedback comes when this short check ends · hints are off for now" with "why? ▸" → "To see which of two things to help with next. Answer with what you know." (`:1661-1668`). Exit: "Stop diagnosing and teach me" (2.13). Results: "That's the short check done. Here's what it showed." (`D/screens/DiagnosticReviewScreen.tsx:163`), next step "A few more questions" / "Back to practice" / "Fix this mix-up · about 4 min".

**States.**

| State | Text | Where |
|---|---|---|
| Loading | "Loading the question…" | `:1603` |
| Grading | "Reading your answer…" | `:2248` |
| Saved, grading unfinished | "Your answer is saved. LearnLoop is finishing the grading." + "Try again" (r) | `:1505-1507` |
| Recovery | "Attempt recorded · route recovery required" (jargon) | `:1527` |
| Gone | "This question isn't available any more." + "Next question" / "Try again" | `:1562-1565` |
| Load failed | "Practice item unavailable" + "Retry loading" / "Back to Today" | `:1578-1586` |
| No model | "Grade this one yourself", "How did you do?" with "Got it / Partly / Missed" | `:2739-2761` |
| Refused submit | the server's text verbatim, e.g. "a cold retry must be unassisted and unprimed: its answer was shown (tutor answer at 2026-…)" (jargon and a raw timestamp) | `S/serve_eligibility.py:168`, `:639-641`; shown via `D/errors.ts:81` |

**Practice exam** (`D/screens/ExamScreen.tsx`). Entry: goal card "Practice exam" or "take practice exam" in its details. Header "Practice exam", "no hints · no tutor · answers are final" (`:195-201`); "Submit answer" / "Submit blank answer" after "Submit a blank answer? This item has no skip…" (`:236-249`); "Preparing exam…" / "Scoring exam…" (`:159`); "The exam could not be started." / "This goal has no exam items available yet." (`:173`, `:83`). Results use "we projected X — you scored Y", "calibration (Brier): … — lower is better", "Per facet · predicted vs observed" (`:425-447`). Exit: Esc while sitting it; "Back to today" after.

**Calibration** (`D/screens/CalibrationScreen.tsx`): Under the hood → Calibration → "start calibration" (needs a session: "start a session first — calibration attaches…", `D/screens/underhood/tools.tsx:99`, `:117`), or palette `> calibrate`. The screen shows raw ids and internal words: "goal {id}", "open episodes", "Practice next target · {practiceItemId}", "Diagnostic dialogue · {learningObjectId}", "no runnable target … parked" (`:214-299`). Mark: pointer, under the hood. The quick check "Check what I already know" (`D/components/PlacementControls.tsx:189`, a `role="button"` span with no tab stop) is pointer only, from the topic inspector, and needs a session.

### 2.4 Feedback, follow-ups and "Coming up"

`D/screens/FeedbackScreen.tsx`, `D/screens/feedback/FeedbackSurface.tsx`.

| Element | Label | Where | Key |
|---|---|---|---|
| Back | "← Today's plan" / "← Today" / "← Back to the book" | `FeedbackSurface.tsx:272`; `D/app/practiceFeedback.ts:89-93` | Esc, b |
| Verdict | "Right" / "Partly right" / "Not yet" / "Held for review"; "◇ graded by AI" / "graded by you" | `practiceFeedback.ts:30-35`; `FeedbackSurface.tsx:285-288` | — |
| Contest | "I think I was right ▸" → "Why? One line, optional", "Look again" / "Looking again…", "never mind"; outcomes "Looked at it again: still X / now X.", "Your note is kept. The grader can't look again right now.", "Your note couldn't be sent. Try again." | `FeedbackSurface.tsx:292-342`; `FeedbackScreen.tsx:2111-2128` | r |
| Next | "Next" / "Opening…", with "next: X", "today's plan is done", "back in N min", "preparing a question…" | `FeedbackSurface.tsx:466`; `dailyPlan.ts:207-217` | n, Enter |
| One next step | "Fix this mix-up · about 4 min" / "Redo the part you missed" / "Try a similar one (t)" | `FeedbackScreen.tsx:2411-2415` | t |
| why? | "Possible causes", "What you already showed", "You've made this mistake before", "this doesn't sound right" → "Noted. Thanks." | `FeedbackSurface.tsx:418-456` | — |
| Details | "details ▸": "how sure the grader was: 0.83", "UNASSISTED CHECK · PASSED … the repair is confirmed and the factor is closed.", "open in inspector", the card controls | `FeedbackScreen.tsx:2568`, `:203-218`, `:2750` | `.` |
| Something else | "Something else would help" | `:2539` | — |

**Follow-ups.** The panel's lines come from the server: "Preparing a question on this…", "Couldn't prepare a question on this. It's noted for later.", "This question comes first.", "Your next question is ready.", "A question on X is coming in your next block." (`S/followup_run/serving.py:21-28`, `:75`). While a follow-up is pending, the answer and causes are held: "The answer and the possible causes come after the question, so your answer can tell them apart." with "Show anyway" / "Continue without it" (`D/components/FollowupPanel.tsx:50-56`). The router's line sits on the main surface by default (`ui.show_router_decisions = true`): "Router: X · by the rules · A 60%, B 40% · floor 5%" with details showing model names, raw JSON and "Decision {id}" (`S/followup_run/decision_view.py:80-85`; `FollowupPanel.tsx:13-24`). "See the earlier answer and the possible causes" (`FeedbackScreen.tsx:2489`) opens the topic inspector.

**Diagnosis arriving later.** The one sentence updates in place, with no notice (`FeedbackSurface.tsx:248-252`); in details, "analyzing your pattern…" or "The pattern analysis for this answer did not complete; your grade above stands." (`D/components/DiagnosisCard.tsx:201-224`).

**Back to the source.** "Back to where you studied this" (`S/intent/checks.py:95`) follows "Your check on your own." (`D/components/IntentCheckFeedback.tsx:19-24`) only when a check was satisfied and knows its source; a removed source reads "The source you studied this in is no longer in the library." (`App.tsx:1222`).

**"Coming up"** is not on feedback or Today. It lives in the Reader's "Last time here" and wrap-up: "Coming up · checks on your own" with "why", "undo", "undo all", "keep it", "later ▸", and "No longer needed: you solved one like it on …" (`D/screens/reader/ComingUp.tsx:129`; `recapCopy.ts:77-98`). A learner who never opens the Reader never sees what is scheduled.

**Keys bound but not shown** (`FeedbackScreen.tsx:2368-2380`): D starts a diagnostic follow-up; a adds an error; j captures a note; o opens notes; u and x rate a follow-up; t starts a similar question even on a right answer, where no button is shown.

**Load failed:** "Couldn't load the feedback." with "Try again" / "Next question" (`:2782-2785`). The answer panel: "Hidden while you were away. Show it ▸" / "It can't be shown right now. Try again ▸" / "One moment…" (`FeedbackSurface.tsx:146-159`).

### 2.5 Where the app tells the learner an answer was "with help" (owner decision 2)

Every place a learner-facing screen says an answer was with help, assisted, primed or not on your own. "Simple" means the default shell.

**Desktop, simple shell.**

| Where | Exact label | When |
|---|---|---|
| `D/screens/feedback/FeedbackSurface.tsx:168` | "◌ Practice with help." | a primed retry or redo |
| `FeedbackSurface.tsx:166` | "Counted as practice with help: the tutor had already shown part of this answer." | auto-primed by the reveal ledger (help text overlapped the answer key) |
| `D/screens/FeedbackScreen.tsx:260-264` (details) | "Counted as assisted — tutor answers before this attempt covered part of the solution. An unassisted check will confirm the repair." + "(N% of the answer already shown)" | the same auto-prime, in other words |
| `FeedbackScreen.tsx:205-218` (details) | "unassisted check · passed / did not hold / no verdict"; "…you answered it without help, so the repair is confirmed and the factor is closed." | a cold check result |
| `FeedbackSurface.tsx:175-180` | "This was the check on your own for the fix from {date}: it held." (and "…it didn't hold yet, so the fix comes back with more support.") | a cold check result |
| `D/app/practiceFeedback.ts:21-23` | "The repair showed too much of the answer for this check to tell whether it helped." | reveal over budget |
| `FeedbackScreen.tsx:2578` (details) | "N question(s) to the tutor counted as a hint / hints here" | tutor questions that counted |
| `D/components/IntentCheckFeedback.tsx:19` | "Your check on your own." | a check satisfied |
| `D/screens/PracticeScreen.tsx:1634` | "◌ with help" | a primed retry or redo, while answering |
| `PracticeScreen.tsx:1728`; `S/intent/checks.py:42`, `:45`, `:50-56` | the cold, measured and practice banners and the take-step line (2.3) | a check |
| `D/components/askPanel.tsx:46`, `:60`, `:67`, `:75` | "…a question about the maths makes this practice with help ◌…"; "That's worked help ◌"; "Practice with help ◌ — you asked about the maths"; "counts as help" / "a clarification · still on your own" | Ask during a check |
| `D/components/askFigures.tsx:32`, `:41` | "a figure on this makes this practice with help ◌"; "Practice with help ◌ — you asked for a figure" | a figure during a check |
| `PracticeScreen.tsx:3039`, `:3079`, `:3090` | "help used: … worked help (L4) · practice with help" ("L4" is internal) | worked help |
| `D/screens/workbench/helpModel.ts:87-88` | "worked help ◌" | workbench rungs 4-5 |
| `D/app/todayPlan.ts:316-318` | "on your own · no hints" | full list, a cold follow-up |
| `todayPlan.ts:336-337` | "…Help is still here — using it makes this practice with help." | full list why? on the same row: contradicts "no hints" unless the server sends the take step |
| `D/screens/today/TodayPlace.tsx:876` | " · on your own" | any plan row from a follow-up, including ones that are not cold (`todayPlan.ts:132`) |
| `D/components/SessionFinishHud.tsx:140-141` | "● X (on your own)" / "◌ X (with help)" | session end (rule: `src/learnloop_sidecar/handlers/sessions.py:276-284`) |
| `D/screens/KnowledgeWellView.tsx:446`, `:539` | "◌ dashed amber bead = instructed — cold check pending (not demonstrated)"; "repaired with help, unverified" | Progress → knowledge field → well |
| `D/screens/reader/RecapCard.tsx:145`, `:169`; `S/reader/recap.py:135-141` | "help so far: the book, N hints on the answer box"; "● X — demonstrated on your own (date)" | the Reader's "Last time here" |
| `D/screens/reader/WrapUpPanel.tsx:42-43` | "◌ X · with help · help so far: …"; "◌ worked with help — not yet checked on your own" | Reader wrap-up |
| `D/screens/reader/deliverableSlice.ts:39-41`; `S/source_retrieval/deliverable_path.py:1463-1480` | "Shown on your own, without help." / "Not tested on your own yet."; "N of M shown on your own"; "Readiness is only checks on your own, later: reading never counts." | "Am I ready?": work done with help is never named; it reads as "Not tested" |
| `D/screens/RepairScreen.tsx:315-316`; `PracticeScreen.tsx:1900` | "A check on your own comes back on another day." | after a repair or redo |
| `D/screens/LessonScreen.tsx:423`, `:649` | "On your own: no notes or help for this one."; "I'll ask you one question on X, on your own, …" | lesson checks |
| `D/screens/reader/useLibraryAsk.ts:85`; `ActiveReadingCard.tsx:37` | "not yet shown on your own"; "…you'll be asked this later, on your own." | Reader |

**Desktop, under the hood, classic or unrendered.** Inspector (`D/components/KnowledgeModel.tsx`): "assisted (no credit)" (`:493`), "N direct observations (U unassisted)" (`:555`), "primed" pill (`:609`), "Assisted observation — certifies no direct credit." (`:624`), and a legend "◌ tested" (`:465`). Classic Today, practice, feedback and HUD: "unassisted check on X waiting until … — recent tutor help covered this answer." (`D/screens/TodayScreen.tsx:934-938`), "unassisted check - answer this one cold" (`:1362`), "using a hint (or opening it primed) voids the measurement…" (`:1417`), "the retry is scored as source-fresh (primed) evidence" (`FeedbackScreen.tsx:1190`), "unassisted checks N answered ✓M confirmed" (`SessionFinishHud.tsx:248`). Diagnostic details: "(scored as primed evidence)" (`D/components/RepairAffordances.tsx:77`). The Ask overlay with the panel switched off: "tutor answers are logged · never reveals the answer" (`D/components/AskOverlay.tsx:1349`), which the auto-prime line contradicts. Defined but never rendered: "worked with help · a check on your own is pending" (`D/screens/reader/voices.tsx:137`).

**Phone.** "◌ with help" (`M/practice/QuestionScreen.tsx:624`) after a hint; the hint sheet "With a hint, this answer counts as answered with help (◌), not on your own." (`:634`); the server's eligibility line, e.g. "Practice with help: help was taken, so this attempt is not the check on your own." (`:614`; `S/serve_eligibility.py:693`); the check banners (`:612`). The phone's feedback, Today and Progress have no with-help label.

**Terminal app.** Internal words only ("attempt type", "rating cap"; `T/practice.py:448-505`).

**What this means for decision 2.**

- **Nothing quotes the help that gave the answer away.** The auto-primed line gives a percentage at most (`FeedbackScreen.tsx:264`); the refused-submit error names the kind of help and a timestamp (`S/serve_eligibility.py:639-641`), never its text; Ask's "earlier on this question ▸" re-shows old tutor answers, but as help that counts as a hint, not as the reason. The quote has no place on screen yet.
- **After an ordinary hint, desktop feedback says nothing.** A hint taken on a check converts the attempt, but the practice banner does not change (it swaps only after an Ask about the maths or a figure, `PracticeScreen.tsx:1723-1728`), and feedback simply omits "Your check on your own." The server's eligibility line is shown on the phone and never on the desktop.
- **One idea, many words:** "practice with help", "with help", "assisted", "worked help", "primed", "instructed", "unassisted", "cold", "on your own", "independent evidence" (phone, `M/practice/FeedbackScreen.tsx:57`). The glyph ◌ means "with help" in most places, "tested" in the inspector legend, and "worth a second look" in the Reader recap (`RecapCard.tsx:156`).
- **"Am I ready?" folds with-help work into "Not tested"**, which is honest about certification but hides that the learner did work on it.

### 2.6 First run, a new library, ingest and the library

**First run.** With no books, the app lands on the Library (`App.tsx:479-492`): "Drop a book, paper or lecture here", "Choose a file…", "or paste a link", "Add", "More options ▸" (`D/components/AddSource.tsx:126-163`). Today says "Nothing to plan yet…" with "+ Add". Mark: pointer.

**A new library.** "New library…" (⋯ menu, palette) opens a dialog titled "new vault" with "vault directory" / "browse…", "first subject — optional", "where are you starting from — optional" (new to this / some exposure / comfortable / strong background) and "create vault ↵" (`D/components/NewVaultWizard.tsx:467-495`; prose names "SQLite state" and "the ingest screen"). On success the app opens Under the hood → Imports & builds with the "SETUP 03/03" guide and the guided "Quick add → study map" dialog ("NEW VAULT SETUP · GUIDED INGEST", "02 inventory budget", `D/components/QuickAddDialog.tsx:266-271`; `App.tsx:2499-2506`). So the explicit new-library route shows token budgets, "Enrichment · interesting adjunct", "inventory output budget · per unit … tokens · 12,000 recommended", "reader on/off", raw role ids, "~N input tokens" and "external AI consent" ticks (`QuickAddDialog.tsx:19`, `:379-529`) before it has asked what course or exam the learner has, while the drop-a-book route opens the Reader at once. The wizard's steps 2 to 5 (first source, proposals, goal, the loop) exist but cannot render (`STEP_LABELS = ["vault"]`, `:27`; SJ-9). States: "Choose a directory for the vault.", "Could not create the vault.", "Could not open the directory browser." (`:111-145`); startup "Loading LearnLoop vault" / the error + "retry vault load" (`App.tsx:1965-1971`).

**Adding.** "+ Add" (popover), drop anywhere ("Drop to add to your library", `AddSource.tsx:302`), the book shelf's foot ("Drop more books here, or add one:"), palette; Ctrl+O (file chooser) and Ctrl+V outside a field (adds a pasted link at once) are keyboard only (`D/app/useGlobalAdd.ts:208-219`). More options: "Only some pages", "This is a past exam or problem set (no reading questions)", "Read with text recognition" (`AddSource.tsx:169-183`). Accepted: PDFs, web pages, arXiv, YouTube, captions (`.vtt`, `.srt`), audio, images, single `.md` files.

**A source's states** (the server's lines, `S/content/pipeline/add_source.py`, rendered on the card at `D/components/BookCard.tsx:58-67`):

| Kind | Lines (action) |
|---|---|
| Working ◐ | "Getting this {noun} ready"; "Chapters found"; "Writing questions for {phrase}"; "Questions for {phrase} in about N min" (`:2404-2518`) |
| Failed | "Couldn't reach the page · Try again" (for any web, arXiv or YouTube failure, `:2229-2232`); "Couldn't read this PDF"; "Couldn't get this {noun} ready"; "This video has no captions"; "Text recognition isn't set up · Set it up"; "This PDF is a scan — LearnLoop can show its pages but can't read them yet · Set it up"; "Questions for this {noun} need another try · Retry"; "Questions for {phrase} are too much to write at once" (no action) |
| Needs an OK | "Transcribing this recording sends it to an online service · OK"; "…sends the whole file to z.ai (GLM-OCR) · OK"; "Reading this PDF sends the whole file to your AI · OK"; "Questions wait for your OK · Review" (`:2496`), whose action is `connect_ai`: **"Review" opens the Connect-an-AI sheet** (`D/screens/LibraryPlace.tsx:157`) |
| Spend | "Building questions for {phrase} would cost about $X · Build them"; "…would cost more than expected"; "Paused — today's AI budget is used · Raise it" (`:2385`), whose action opens Settings, **which has no spend cap** (2.14) |
| Stale | "This {noun}'s file changed after it was read · Open the reading you had"; "Its original file changed or is missing…"; "Questions for this {noun} were taken back out · Build them again" |
| Review | "Questions for this {noun} need a look · Review"; "N changes need a look · Review" (→ Study-map changes) |
| Ready | "Questions for {built} come up as you read" |
| No model | "Questions need an AI connection · Connect"; "…come up as you read once an AI is connected · Connect"; shelf "○ Connect an AI to get questions — Continue with ChatGPT · other…" (`BookShelf.tsx:69-75`); Add: "Connect an AI first: Continue with ChatGPT, or add an OpenRouter key." (`D/copy/ingestErrors.ts:20`) |

Book card actions: "Continue" / "Open", "details ▸" → "Build questions for the whole {noun} at once", "Undo this {noun}'s questions", "Read it again with text recognition", "See how it was added and built", "What you want from this {noun}" (`BookCard.tsx:120-159`). A past exam reads "{noun} · for practice only" with no Open (`:114`).

**Under the hood → Imports & builds** (`D/screens/IngestScreen.tsx`, `D/components/SourceLibrarySidebar.tsx`): "＋ create study map", "outline & select →", "＋ collection", "✕ delete", "synthesize →", "brief" (spans, pointer only, `SourceLibrarySidebar.tsx:142-729`); mode chips "📚 canonical source" / "📝 exam seeding"; "▶ import source" / "▶ seed exam"; a "pdf engine" select; build tracking "↻ retry synthesis", "↻ revalidate candidate (no new model run)", "checkpoint ladder… token bars" (`D/components/IngestActivity.tsx:540-771`). Study-map changes: "proposals · AI inbox", "A Bulk accept auto_apply" (`D/screens/ProposalsScreen.tsx:150`, `:932-936`). Collections: "add to collection", roles including `problem_set` and `exam`, a syllabus hint (`D/components/AddToCollection.tsx:22-31`, `:155-250`). "add to study map" (the ingestion redesign's verb): not found.

**The student's materials (persona 1).**

| Material | What exists | Mark |
|---|---|---|
| Textbook, lecture captions or recording | Add | pointer |
| Practice exam for a coming exam | Add → "This is a past exam or problem set" (kept out of the reader, no questions built, not exam-protected: `add_source.py:251`, `:1550-1551`); the collection role `exam`; "Mark exam material on this reading" appears only after "This reading is held back until you mark its exam material" (`S/content/pipeline/exam_marking.py:69-71`; `LibraryPlace.tsx:188-235`); the goal wizard's "hold out a practice exam N items" | pointer, scattered |
| Outline or syllabus of the exam | the collection role syllabus; the Reader's deliverable "from your syllabus · read it ↵" (2.8) | pointer (Reader) |
| Past graded exams | "📝 exam seeding" ends in the text "learnloop seed-exam-attempts --outcomes <file>" (`IngestScreen.tsx:1419`, `:1483`); not a palette command | none (CLI only) |
| Past graded homework | not found | none |

**Own notes (persona 8).** Single `.md` files can be added. Folders of Markdown, an Obsidian vault and flashcard decks (with or without review history) have no import path: the pickers set `directory: false` (`D/components/useSourceFileDrop.ts:66`, `:81`); "obsidian", "anki", "apkg", "flashcard" and "deck" match nothing in the frontend or `src/`. Allowlisted personal notes reach the Reader as "from your notes" (2.9 i), which is linking, not importing.

**Subjects (student finding 5).** Ordinary Add names a subject from each source's title (`add_source.py:1113`); Quick Add requires one and now lets the learner create it ("no subjects yet — name one…", "create subject", `D/components/NewSubjectControl.tsx:58`, `:87`). There is no course chooser in ordinary Add.

### 2.7 Capture

| Frontend | Entry | Mark |
|---|---|---|
| Desktop | "New captures ▸" on Today (`TodayPlace.tsx:302`), shown only when new captures exist; once open it has no close (`:299`). Classic: "Inbox · N" (`TodayScreen.tsx:755`) | pointer, but only when something arrived |
| Desktop actions | "Include handled" / "Show new", "Tutor subject" select, "Quick Add source" (a link capture opens the token-budget study-map builder, not Add), "Make a card", "Ask tutor" (disabled: "Create a subject before asking the tutor"), "View photo", "Photo → card (manual); capture kept as provenance.", "Dismiss", "Purge" → "Delete captured content permanently?…" (`D/components/InboxStrip.tsx:130-189`) | pointer |
| Desktop states | "Could not load the inbox." + "Retry"; "Could not update the capture."; "Phone captures are pinned to {vault}, not this vault. Open that vault to see them."; media deletion pending / retained lines (`:72-158`) | |
| Desktop: capture in place | none: no capture box on the desktop; from the Reader the learner marks, notes or asks (2.9 b) | none |
| Phone | "+" tab (`M/App.tsx:737`): "A thought, a problem or a link", "Note (optional)", "Save", "Photo" (`M/capture/CaptureScreen.tsx:59-79`); "Saved.", "N waiting to send.", "Dismiss"; "The desktop refused this ({status})." (an HTTP code, `M/store/outbox.ts:320-322`) | pointer |
| Chat | none (the MCP tools are read-only apart from recording passages read, 2.18) | none |

Captures are routed by hand from the inbox; nothing turns one into practice in one step.

### 2.8 Goals, deliverables and "Am I ready?"

**Outside the Reader.**

| Control | Label | Where | Mark |
|---|---|---|---|
| Goal card | "{title} · {date} · on track / getting there / needs more practice" | `D/components/GoalCard.tsx:14-18`, `:98` | pointer, when a goal exists |
| Practise | "Practise for this goal" | `:101` | pointer |
| Practice exam | "Practice exam" (when the exam pool is ready) | `:105` | pointer |
| Details | "details ▸" → the goal report | `:109-121` | pointer |
| New goal | "+ new goal" (a span) | `D/components/GoalBanner.tsx:801` | pointer, inside details only |
| First goal | **no Today control creates a goal when none exists** in the simple shell; classic has "set a goal ↵" (`TodayScreen.tsx:1876`) | | none on Today |
| Quick Add brief | "general learning / reference mastery / exam prep" → "goal title", "due date", "target recall", "held-out exam items" (`D/components/StudyMapBriefWizard.tsx:21-23`, `:258-297`); copy "Adding to an existing map leaves your goals as they are; make one from Today" (`:306-307`), though Today has no such control | pointer, deep (first map only) |
| Goal wizard | "what / how well / by when / exam"; "goal title", "quest / larger intent · optional", "advanced · explicit facet ids", "target recall", "open-ended (no deadline)", "hold out a practice exam N items", "create goal ↵" (`D/components/GoalWizard.tsx:15-644`); failures show the raw error | pointer, via "+ new goal" |
| Palette | `> populate-goal` | `CommandPalette.tsx:107` | keys |

The goal report (`GoalBanner.tsx`): "ON TRACK / CLOSING IN / BEHIND" (`:44-49`, against the card's "getting there / needs more practice"); "predicted recall N% · target T%", "{n}/{t} facets ≥ T%", "certified · examined · untouched", "≈ N qualifying attempts outstanding…" (`:78-100`, `:506-507`); "▸ plan around my week"; "▸ how good are these forecasts?"; "▸ to do: N facets need work"; "practice at-risk facets ↵" and "take practice exam" (duplicating the card's buttons); "exam not ready — N reservable items; no held-out coverage yet for: …"; "edit why" / "add why"; "trajectory · demonstrated + ready lanes". A smoke walk on the harness met "LearnLoop could not confirm whether this action completed" here (ledger E-2, now fixed on main).

**Changing a goal.** The simple shell offers only "edit why". The review card "keep / pause / complete / expire" (`D/components/GoalReviewCard.tsx:87-90`) is mounted only in the classic Today (`TodayScreen.tsx:877`). The client has no call to change a goal's deadline or scope (`D/api/client.ts:1185-1199`: create, status, intent). Delete: not found. Mark: **none** for changing the deadline or scope (the seasoned persona's "change or modify goals").

**In the Reader** (`D/screens/reader/DeliverableScope.tsx`, `deliverableSlice.ts`, `DeliverableSliceCard.tsx`): "learning this for something? ▸" / "your deliverable ▸" (`DeliverableScope.tsx:38-39`, `:325-328`); sentence, topics, deadline, "it's an exam", "make it ↵" (`:40-46`); corrections "add it" / "no", "not this…", "add…", "receipt"; "from your syllabus" + "read it ↵"; "How deep for this?"; "{topic}: on your path in {book} {section} ▸", "not in your books yet:"; "this book alone" / "back to your deliverable"; "I know this — check me later"; **"Am I ready?"** (`DeliverableSliceCard.tsx:303`) and "Readiness is only checks on your own, later: reading never counts."; from a selection, "scope my deliverable from this passage" (`ScopeFromPassage.tsx:25`). States: "◐ choosing a path across your books…", "◐ checking where your books treat these topics…", "Couldn't load your deliverable's path.", "Couldn't scope from that passage.". "Am I ready?" has no entry outside the Reader.

So a goal can be made three ways with three different field sets (the goal wizard, the Quick Add brief, the Reader's deliverable), and only the Reader's has "Am I ready?".

### 2.9 The Reader (desktop)

`D/screens/ReaderScreen.tsx` ("RS") and `D/screens/reader/` ("R/"). Shared model-action states (`R/ModelActionState.tsx`): pending "◐ {verb}… · cancel" (`:88`); "Couldn't reach LearnLoop's model." (`:99`); "LearnLoop's background service isn't responding. The source still reads." (`:101`); "Today's {route} budget ({amount}) is used. {fallback} still works." (`:105`); "{failure} {kept} · try again ↵" (`:110`). A `usuallySeconds` wait estimate exists (`:89`) but no caller passes one.

**a. Opening a book, the Guide, "Last time here", reading paths.** Entry: "Reader" (Alt+3), shelf "Continue" / "Open", palette "Continue reading"; front door "Pick a book to read, or search them all." (RS:2974), cards "read →" / "watch →". Back: "← Library" (RS:3558). "I want to [skim quickly / read closely / mark for later]" (RS:3580). Rail tabs GUIDE · ASK · NOTES (RS:4113-4136; `[` `]` and `\`). "Last time here" / "last time ▸" (`R/RecapCard.tsx:88-104`). Reading path: "YOUR PATH", "How deep do you want to go?", "get the idea · definitions, examples, visualizations" / "learn to use it · …" / "fluency · …", section labels "core / prerequisite / enrichment / already shown ● / assumed" with "why ▸", "skip it" / "read it anyway", "undo"; "one exercise worth trying: … Try it ▸" (`R/readingPath.ts:10-26`; `S/source_retrieval/reading_paths.py:97-115`). States: "◐ connecting this source to your learning path…", "No personalized guide is available for this source yet." (`R/GuideRail.tsx:211-213`); "◐ reading a path for this book…", "Couldn't read a path for this book just now. Try again ↵", "Today's reading-path budget ($x) is used. The book and the Guide still work.", "This reading is held out for an exam: it has no reading path."; with no model: **"LEARNLOOP_READING_PATH_MODELS=off: no reading-path model is reached."** (`reading_paths.py:678`, shown at `R/ReadingPathCard.tsx:178`). Reader switched off or sidecar down: "…Set tutor_qa.reader_enabled = true in learnloop.toml" (RS:3076), "the sidecar is unreachable — only the offline demo chapter is available." (RS:3088). "YOUR PATH" heads three different cards (goal fallback, reading path, deliverable slice).

**b. Selection: the intent box and active reading.** The box appears about 150 ms after a selection, without focus; typing focuses it; Tab opens the action palette; `?` focuses it (`R/useIntentBox.ts:1-19`, `:73`). "what do you want to do with this?", "↵ ask · tab actions · esc", "ⓘ where this goes" (tooltip); routing "◐ choosing…", routed line "→ Understand · ask · help me reason" + "change"; fallbacks "(LearnLoop's model couldn't choose, so this asks)" / "(that isn't on offer here, so this asks)" (`R/IntentBox.tsx:51-80`). Actions (`S/reader/reader_intent.py:159-247`), grouped Understand / Apply / Consolidate / Transfer / Orient / Mark: "ask", "ask · help me reason", "ask · ask me first", "explain differently", "worked example", "research this", "why does this step work?", "what does this assume?", "another way to see this", "show me…" (or "make this explorable"), "work through this", "let me try the next step", "add this exercise to practice", "revisit once (test me later)", "help me remember", "reconstruct this later", "connect it", "why this matters", "where else is this explained?", "how do my other books treat this?", "where is this used?", "what matters here?", "what do I need first?", "highlight", "note", "confusing", "not worth remembering". Active reading (`R/ActiveReadingCard.tsx`): "Write it in your own words…", "compare with the book ^↵", **"show me"** (reveals the book's step, `:165`), "how did yours compare?", "add to practice", "don't bring this back"; reconstruct: "Added to your practice: later you'll be asked to rebuild this derivation without the book." / "Undone: it won't be asked.". Protected passage: "This passage is held out of LearnLoop's models. You can still highlight it, mark it and keep notes." (`R/intentPalette.ts:20`). "show me" means three things (reveal the book's step here, build a figure in the palette and Ask, a worked example in the phone's dose offer).

**c. Ask.** The Reader's rail: "Ask" + "answers now, grounded in the selected passage · background requests live under notes" (`R/AskRail.tsx:202-204`); chips "ASKING ABOUT YOUR SELECTION" / "FOLLOW-UP TO:" / "… IN {book}" + "ask about this book instead"; "help style: let me struggle · balanced · guide me" (`D/components/askPanel.tsx:107`); "personalized ●/○" (explained only in a tooltip); "ask about this passage…", "ask · ↵"; pending "looking in your books, then writing an answer"; failed "Couldn't get an answer." "Your question is kept."; history "Previous asks", "find in asks…". "ⓘ what's sent" and the removable context chips exist only in the Ask overlay used by practice, feedback and the workbench (`askPanel.tsx:58`; `AskOverlay.tsx:794-841`), not in the Reader's rail. While working a problem: "Ask the tutor is beside the book. Leave for now (your steps are kept) and Ask opens." (`R/ReaderWorkingPosture.tsx:19`).

**d. Compare, find-section, also in your books, side by side.** Doors: the action "how do my other books treat this?" (`reader_intent.py:224`); the side-by-side pane's button; the tutor's "how do your books treat this?" → "compared beside the book ▸" (`R/TutorOffers.tsx:71-81`); natural language in Ask your library (Ctrl+Shift+F or ⇧↵), "reading which books you named", fallback "couldn't read which books you named · compare all your books on "…" ▸" (`R/useLibraryAsk.ts:92-105`); "compare these books ▸" / "compare pinned (n)" (`R/LibraryAnswer.tsx:640-646`); "compare" in find-section and also-in. Scope row: "comparing" + "your passage" / "all your books" / book chips, "+ add a book", "on: {topic}" + "change", ""X" isn't in your library" (`R/CompareScope.tsx:147-236`). Table: "differences kept · each line quotes its own book", "by point / by book", "not addressed here", "where else is this explained? ▸" (`R/ComparePointTable.tsx:42-602`); "/ refine"; "keep comparison ⇄" → "kept ⇄"; "you compared these on … · reopen ⇄". States: "finding each book's passages, then lining them up"; "cancelled · compare again ↵"; "Only one of your books has a checked passage on this; pin one from another book to compare."; while working: "Your comparison opens beside the book. Leave for now (your steps are kept) and it starts.". Find-section: "find this section in my other books ▸" in the Guide's footer (`R/FindSection.tsx:374`), hidden once the section has judged coverage; "found by search, not checked"; "peek / go there / compare / not about this / undo"; "read side by side (s)". Also in your books: "also in {names} and others ▸" under the section bar (`R/AlsoInBooks.tsx:545`), key `x`; "introduces it / develops it / uses it / mentions it"; "hide for this book" / "hide everywhere". Side by side: Ctrl+\ or `s`; "follow along ●/○ (^⇧L)", "✕", "side by side needs a wider window", "no matching section here · stays put" (`R/SideBySidePane.tsx:229-253`). The rail (with the Guide footer) is hidden while comparing (RS:4104). Kept comparisons do not reach the phone.

**e. Show me figures:** section 2.10.

**f. The workbench.** Entries: "work through this", "Try it ▸" on the path, "✎ … · resume / reopen" in "your problems here", the gutter "✎", recap "Resume this problem ▸". Controls: "check my work · counts as a hint · ctrl+k", "help · ctrl+h", "I'm stuck · ctrl+d", "submit · ctrl+↵", "esc · back to reading", "show in the book ▾" / "answer box instead" (`D/screens/workbench/Workbench.tsx:459-871`); "as printed", "cropping the page…", "Couldn't crop the page just now." (`D/components/AsPrinted.tsx:28-34`). Ladder "help · every level is yours": "a question about your approach", "point to the first step that doesn't hold yet", "a hint on your step — …", "work a piece of it for me, in my notation", "walk me through the rest, keeping my route" (`S/hints/workbench.py:75-81`); "this doesn't connect to my work…" with "that's not where I'm stuck / too big a jump / I'm using a different approach / the notation"; "show me the book's way". States: "setting up checks and hints for this exercise…", "Setup didn't finish."; offline "sidecar unreachable — keeping your steps here…"; "symbolic checks aren't available here, so every marker is the model's reading" and "sympy, with a negative control" (jargon).

**g. Deliverables:** section 2.8.

**h. Wrap-up, "Coming up", summary, dose and quick checks.** "Wrap up (under a minute)" (RS:4592, key `w`); "Wrap up · under a minute", "Nothing to wrap up from this session." (`R/WrapUpPanel.tsx:93-97`); "Coming up" (2.4); "▸ summary written by LearnLoop's model from what you did" (`R/DigestNarrative.tsx:28-32`); dose offer "{text}" + "yes" / "no thanks" / "why?" (`R/DoseOffer.tsx:145-155`); quick checks "A quick check on this section is ready, just below.", "◐ writing a quick check for this section…", "quick check · optional · formative, never a grade" (`R/GuideRail.tsx:182-207`; `R/InquiryQuickCheck.tsx:83`); reconnect "↳ your question "…" — does this make sense now?" (`R/ReconnectLine.tsx:60`). Many check phrasings compete: "quick check", "check me", "check my work", "a check on your own", "I know this — check me later", "Check what I already know".

**i. Notes.** "from your notes" on a gutter "›" (`R/ReaderNotes.tsx:33`, `:214`); right-click "› link one of your notes…" → "search your notes", "exact words" / "by meaning" (`R/ReaderNotes.tsx:42-47`, `:490`); "teach me this ▸" (`R/NotesRail.tsx:256`).

**Breadcrumbs and return.** "↩ … › …", "alt+← back", "close peek" (`R/DetourStrip.tsx:51-96`); Alt+← / Alt+→ (`R/useReaderInquiry.ts:661-675`).

**Keys and space.** `\` (rail) beside Ctrl+\ (side by side); Ctrl+F means Ask history, transcript or the browser's find; `c` is "compare pinned" or "compare"; `t` is a figure's values table or the compare table's "your take". The gutter holds the cue mark, the notes "›", the workbench "✎" and "worth a second look", at nearly the same offsets.

### 2.10 Show me figures: every request state (desktop)

The figures map (`docs/reviews/k10-figures-map-2026-11-12.md` §8) is still the reference; the strings below were re-read at this commit.

| State | Reader | Ask panel (practice, workbench) | Lesson |
|---|---|---|---|
| Entry | "show me…" in the action palette; "show me ▸" / "alt+↵ show me ▸" in the Ask rail (`R/AskRail.tsx:305-308`); tutor "show me:" "(AI-written)"; library hit "make this explorable" → "building it under the passage"; also-in "◇▸ interactive version from {book} §{n}" | "show me ▸" with its cost line (`AskOverlay.tsx:1295-1308`) | inside the turn |
| Waiting | "◐ building an interactive version — keep reading" / "…from your words · keep reading"; rich "◐ writing an animation for this passage" / "◐ checking it" / "◐ rendering the video (manim)"; "◐ the animation is waiting for the ChatGPT plan" (`R/figures/FigureInline.tsx:182`; `R/figures/RichFigure.tsx:53-64`) | "◐ building an interactive version · keep working" | the turn waits |
| Wait estimate | none anywhere | none | none |
| Partial | "◌ a fuller animation is being written · keep reading"; "◇ a fuller animation is ready" + "open ▸"; "◂ the quick version"; "checks withdrawn: this run differs from the one LearnLoop checked…" (`R/figures/sketch/SketchFigure.tsx:49`) | fuller dropped | fuller dropped |
| Failed | "couldn't build a reliable version of this ({reason})"; "couldn't build an interactive version"; "the fuller animation couldn't be built"; 30+ "LearnLoop couldn't read the book's equation exactly: …" (`FigureInline.tsx:33-96`, `:258`, `:599`) | "couldn't build an interactive version of this" | "couldn't build a figure for this step" |
| Refused | "that passage is held out" | the server's message | "…it would give an answer away, or its passage is held out now" |
| Spend | the server's "Today's figure budget ($x) is used" as an error | same | unavailable |
| Withheld at delivery | nothing (the line disappears) | the generic failed line | — |
| Stale | "couldn't run under this version · rebuild"; "That figure isn't shown now: its own book no longer lists it." (`R/AlsoInBooks.tsx:85`) | same | not shown |
| Can't | "can't draw this yet · noted"; "can't show this kind here" | | |
| Labels | "AI-built illustration of an interpretation · not checked against the book"; "AI-written simulation · sandboxed · not checked against the book"; "AI-made video · not checked against the book"; "not from your books — LearnLoop's model's illustration · not checked against the book"; "matches the book's equation (checked)", "the rest is an illustration" | | |
| Opt-in | "LearnLoop can make narrated animations by running AI-written animation code in a sealed sandbox…" "allow" / "not now" | never | never |

The phone has no figures (owner, Nov 14: by design). The figures map's findings F10U1 to F10U7 (withheld figures vanish, no wait estimate and no timeout, cancel doesn't cancel, one generic failure line per host, four hosts with four vocabularies) are the walk's checklist for this journey.

### 2.11 Searching and jumping across sources today (owner decision 3)

| # | Frontend | Way | Label | Where | Key | Returns | Gate |
|---|---|---|---|---|---|---|---|
| 1 | Desktop | Reader front-door search | "search all sources…"; "N hits across N sources · keyword match · Enter also searches by meaning"; empty "no matches — this searches the text of every book that is ready." | RS:3001-3069; `R/searchBasis.ts:18-20` | typing = words; ↵ = meaning | passages (snippets) that open the book at the span | Reader on; **only with no book open** |
| 2 | Desktop | Ask your library | "⇧↵ ask your library" (front door); "ASK YOUR LIBRARY" / "ask your library…", "↵ ask · esc back to reading" (open book) | RS:3011; `R/LibraryPane.tsx:153-161`; RS:1757-1768 | ⇧↵; **Ctrl+Shift+F only** with a book open (not on the key bar or in Keyboard & help) | up to eight passages grouped by book, with model notes; "peek", "open", pin, compare, "ask the tutor about pinned" | `library_ask` (on) |
| 3 | Desktop | Selection actions | "where else is this explained?", "where is this used?", "what do I need first?", "another way to see this" | `S/reader/reader_intent.py:183-240` | Tab from a selection | passages | on |
| 4 | Desktop | Compare | 2.9 d | | | a generated table quoting passages | on |
| 5 | Desktop | Find-section | "find this section in my other books ▸" | `R/FindSection.tsx:374` | Guide footer | sections, by search, "found by search, not checked" | on; hidden once coverage is judged |
| 6 | Desktop | Also in your books | "also in … ▸" | `R/AlsoInBooks.tsx:545` | `x` | judged sections | on; absent with no judged coverage |
| 7 | Desktop | Side by side | Ctrl+\ / `s` | RS:1714 | | a second pane at the matching section | on |
| 8 | Desktop | Tutor citations | "open in your book" / "from your books" | `R/TutorAnswer.tsx:35`; `R/TutorOffers.tsx:70` | | passages; another book opens as a detour | on |
| 9 | Desktop | Show-me source chips | "from your books: § …" | `R/AskRail.tsx:128-133` | | peek | on |
| 10 | Desktop | Deliverable path | "on your path in {book} {section} ▸" | `R/DeliverableSliceCard.tsx:276` | | opens the other book | on |
| 11 | Desktop | Compare cell | "where else is this explained? ▸" | `R/ComparePointTable.tsx:602` | Space peek, `o` open | library ask | on |
| 12 | Desktop | Within a book | Guide contents, path rows, "Worth a second look" | `R/GuideRail.tsx:262`, `:301`; `R/ReadingPathCard.tsx:238` | | jump within the book | |
| 13 | Desktop | Return | "↩ … › …", "alt+← back" | `R/DetourStrip.tsx:51-96` | Alt+← / Alt+→ | the return stack | on |
| 14 | Desktop | Ask history, transcript | "find in asks…"; "find in transcript…" | `R/AskRail.tsx:359`; `R/YouTubeWatchPanel.tsx:424` | Ctrl+F | this book's questions; a video's lines | |
| 15 | Desktop | Notes | "search your notes" (only inside "link one of your notes…") | `R/ReaderNotes.tsx:490` | right-click | notes | notes |
| 16 | Desktop | Palette | "Continue reading", "Go to Reader / Library" | `App.tsx:1894-1918` | Ctrl+K | a place | |
| 17 | Phone | Book list and sections | "Continue reading {title}"; "Sections" with "· you're here / read / started" | `M/read/ReadScreen.tsx:62`; `M/read/SectionList.tsx:24-32` | | a book or a section | `phone_reader` (on) |
| 18 | Phone | Ask on a selection | "Selected passage" → "Ask", then "Another way" / "That didn't help" | `M/read/SelectionSheet.tsx:115-138` | | a generated answer about the passage | `phone_reader` |
| 19 | Chat | `find_sources` | "Passages from the learner's own sources… verbatim, with citations…" | `src/learnloop_mcp/server.py:548-599` | — | passages (and records them as read) | MCP server running |

Not found: a search box or filter on the Library shelf (`D/components/BookShelf.tsx`, `D/screens/LibraryPlace.tsx`); an "open book" or "go to section" palette command; any search on the phone or in the terminal app.

**What this means for decision 3.** A natural-language search over all sources already half-exists twice: the front door's "Enter also searches by meaning" (only before a book is open) and Ask your library (passages plus model notes, keyboard-only once a book is open). A learner reading a book has no visible search control at all. The new search's screen can replace or merge these two doors; the inventory finds no other surface competing for it.

### 2.12 Reader margin cues today (owner decision 4)

**What a cue shows.**

| Part | Today | Where |
|---|---|---|
| The mark | a gutter glyph drawn by CSS, no text: "◌┆" (connects, distinction, prerequisite), "●┆" (application), "▹┆" (try first) | `R/cues.ts:33`, `:77` |
| The note | from the Guide: "Connects to something you worked on: {topic}."; discovered: "Comes before something you worked on: {topic}." / "A new use of something you've shown: {topic}." / "Try the next step before reading it?" | `S/reader/reader_cues.py:88`; `S/source_retrieval/passage_cues.py:145-147` |
| The "Because:" line | from the Guide: "Because: your answer on {day} · from the Guide's citations" / "Because: an answer you gave · from the Guide's citations"; discovered: "Because: your work on {topic} · …", "Because: a question you raised about {topic} · …", "Because: what you've shown on {topic} · …", "Because: work on {topic} done with help so far · …", each ending "found by LearnLoop's model, not by a test" | `reader_cues.py:90-91`; `passage_cues.py:148-151` |
| Screen reader | "Note on this paragraph: {note} {because}" | `reader_cues.py:93` |
| Inside the popover | "open · what you worked on" → "You answered a question on this on {day}." / "the question" / "your answer" / "its reading of that answer" / "LearnLoop's model is still reading that answer."; for discovered cues "the passage's own words", "what LearnLoop's model connected it to", "found by LearnLoop's model, not by a test"; "try the next step first · the next lines fold while you try; nothing is graded" (try-first only); "check me · a short question on your own, with the book out of view" → "◐ finding a short question…" / "Nothing in your practice fits this yet." / "Couldn't find a question just now. try again" | `R/MarginMark.tsx:268-351`; `R/cues.ts:38-49`, `:80-82` |

All notes and Because lines are fixed templates filled with a topic title or a day (`reader_cues.py` "fixed templates (G16)"); none is generated text, and none quotes a sentence from the passage on the surface (the passage's words appear only inside the popover, for discovered cues).

**Opening and dismissing.** Hover or focus shows the note and Because line (`MarginMark.tsx:215-238`); click or Enter opens the popover; Alt+↓ / Alt+↑ move between marks (`R/useReaderCues.ts:383-404`; the key bar shows "alt+↓ next mark" only while a mark is drawn, RS:4688); Esc closes and returns focus to the mark (`MarginMark.tsx:196-200`, `:245-249`). Dismiss: "not relevant…" → "why? (optional)" + "send" (Ctrl+↵), "Tells LearnLoop this mark missed… never grades you."; "fewer marks like this"; "marks off for this book" / "marks off everywhere"; "close · esc" (`:366-392`). Each leaves a receipt in the Guide footer with "undo": "Marked not relevant.", "Margin marks: {density}.", "Margin marks are off for this book." / "…everywhere.", and "turn back on" (`R/cues.ts:62-65`; `MarginMark.tsx:451-458`).

**How many.** At most one per screenful (`cues.one_per_viewport`, on); per section by density: off 0, fewer 1, **normal 2** (default), more 4 (`R/cues.ts:22`; `S/config/schema.py:2311-2312`). Never while skimming or working, on the restored line, or for the held-out control group (`R/cues.ts:148-156`). The density control "margin marks: off · fewer · normal · more", "a display limit to protect your attention" and "what the marks mean ▸" sit in the Guide footer (`MarginMark.tsx:430-479`), hidden while comparing or working; also Settings → Reader (`D/screens/SettingsScreen.tsx:998`).

**Switches.** `cues.enabled`, `discovery_enabled`, `try_first_enabled`, `value_order_enabled`, all on (`schema.py:2310-2316`). Phone: no cues.

**What this means for decision 4.** The surfaces a decision-model cue needs already exist: the note line, the Because line, the popover with "the passage's own words", the dismiss reasons (which can become training labels), the density budget and the holdout. What changes is the content: today's note is a template naming a topic, and the passage's own sentence is one click deep. The audit's question for the redo is where the one-line explanation and the quoted sentence sit (hover line, popover, or both) without breaking U2 (nothing on the text) and U5 (quiet).

### 2.13 Teacher lessons and Ask tutor: every control (owner's Nov 14 rule)

The rule: a control that asks to be taught, or to learn a topic, opens a Teacher lesson; a control that asks a question about the item, note or passage on screen opens Ask tutor. Lessons are on by default (`teacher.enabled`, `S/config/schema.py:4450`; the sidecar sends `teacher.lessons`, `src/learnloop_sidecar/context.py:1058-1065`). "Fits" is yes when the label promises the surface it opens.

**Desktop: controls that open a lesson.**

| Label | Where | Key | Opens | Fits | Mark |
|---|---|---|---|---|---|
| "Teach me this" (lessons on) / "Learn it with the tutor" (lessons off), short-check review, simple | `D/screens/DiagnosticReviewScreen.tsx:116-118`, `:190`, `:213` | ↵ | lesson on the topic with the check's finding; fallback the tutor | yes | pointer |
| Same, classic review | `:239-248` | Esc, but the key bar says "esc continue" | same | label yes; key bar no | pointer |
| "Stop diagnosing and teach me", practice (simple and classic) | `D/screens/PracticeScreen.tsx:1666`, `:1700-1709` | — | stop, then a lesson; fallback the tutor | yes ("diagnosing" is the one internal word kept on purpose) | pointer |
| "Stop diagnosing and teach me", calibration dialogue | `D/components/DialogueProbe.tsx:383`, `:196-224` | — | stop, lesson, then calibration; a failed stop shows only the results | yes | pointer (under the hood) |
| "▸ Teach me this", topic inspector | `D/components/InspectorOverlay.tsx:609-619` | none (a `span role="button"` with no tab stop) | lesson | yes | pointer only |
| "teach me this ▸", Reader notes rail | `R/NotesRail.tsx:254-256` | — | lesson on the selection's section | yes | pointer |
| "Learn X now? (about N min)" Start / "Or: Y" / "Not now" (plan block) | `D/screens/today/LessonOfferBlock.tsx:114-127` | — | lesson (router suggestion) | yes | pointer |
| "This looks like something to learn. Start a N minute lesson on X?" Start | `D/screens/today/LessonOfferPage.tsx:18`, `:59` | — | lesson | yes | pointer |
| Suggestion card "Learn X now?" Start; "Your lesson on X hasn't opened yet." + "Open the lesson" | `D/screens/today/LessonSuggestionCard.tsx:73-108` | — | lesson | yes | pointer |
| "Learn {topic}" / "Learn this" in "Something else would help" | `D/screens/today/SomethingElse.tsx:19-36` | — | lesson (a learner's pick) | yes | pointer |
| "Continue your lesson on X" + "Continue" / "Close it"; "Learn something new" | `D/screens/today/ContinueLessonCard.tsx:52-61` | — | resume / a typed goal | yes | **switch: classic shell only** (`D/screens/TodayScreen.tsx:748`; `TodayPlace` never renders it) |
| "Start a fresh lesson" | `D/screens/LessonScreen.tsx:400-406` | — | lesson | yes | only after a lesson closed for a protection change |

No palette command opens a lesson.

**Desktop: controls that open Ask tutor.**

| Label | Where | Key | Opens | Fits |
|---|---|---|---|---|
| "Ask" (practice); key bar "ask tutor" (classic); refused during a check with "ask-tutor is disabled during a diagnostic check — use “Stop diagnosing and teach me” instead." | `PracticeScreen.tsx:2322`, `:2416`, `:1032` | `?` | Ask (docked or overlay), practice context | yes |
| Ask on a step | `:985-988`, `:2033` | `?` | Ask under the step | yes |
| Feedback "ask" / "ask tutor" | `D/screens/FeedbackScreen.tsx:2766`, `:3577` | `?` | Ask, feedback context | yes |
| Library note "ask tutor" | `D/screens/LibraryScreen.tsx:546` | `?` | Ask, note context | yes |
| Palette "Ask the tutor about this" ("Nothing here to ask about: open a question, feedback or a note first.") | `App.tsx:1920-1936` | palette | the context on screen, or the Reader's Ask | yes |
| Inbox "Ask tutor" | `D/components/InboxStrip.tsx:176` | — | Ask with the capture's text | yes |
| Today thread "continue ▸" | `D/screens/today/TodayPlace.tsx:254` | — | the earlier Ask thread | yes |
| Reader rail Ask, library pane | RS:4066; `R/LibraryPane.tsx:149`; `R/AskRail.tsx:202` | — | the Reader's Ask | yes |
| "ask the tutor about pinned (N)" | `R/LibraryAnswer.tsx:408-420`; `R/useLibraryAsk.ts:75` | Ctrl+↵ | Ask on the pinned passages | yes (not in the routing record) |
| "ask the tutor about this comparison" | `R/CompareScope.tsx:345`, `:469`; `useLibraryAsk.ts:113` | Ctrl+↵ | Ask on the comparison | yes (not in the routing record) |

**Near misses.** "◊ teach it" (`D/components/CardControls.tsx:262`) opens teach-back, where the learner teaches an AI student; the label can read as "teach me" (the tooltip explains). "Teach it anyway" stays inside a lesson (`LessonScreen.tsx:413`).

**Phone.** Reader selection "Ask" / "Another way" / "That didn't help" (`M/read/SelectionSheet.tsx:134-138`): fits. "Learn X (on the desktop)" in Something else saves the choice and says "{label} is a lesson, and lessons wait on the desktop. Your choice is saved." (`M/practice/SomethingElse.tsx:20`, `:109`): honest, opens nothing. No check hand-off: no stop control during a short check (`M/practice/QuestionScreen.tsx:607-612`).

**Terminal app.** ^t stops a short check: "Check stopped. Lessons are in the desktop app; this question goes on as practice." (`T/practice.py:325`). ^t is not on the key bar (`:191-199`); the probe panel still names "ask-tutor" (`:398-399`) though the terminal app has no tutor.

**Chat.** No tool opens a tutor, a lesson or practice.

**Lesson screen states** (`D/screens/LessonScreen.tsx`): header "Lesson · {goal or title}", "Check what I already know first", "Stop the lesson", "Close" (`:318-330`); typed start "What do you want to learn?", "Find it in my books", "Not in your books yet: “…”. Add it as a topic?" with "Look in my library" / "Create it" / "No", "It will be taught from LearnLoop's model, not from your books.", "Start the lesson" (`:337-390`); waiting "The teacher is writing…", "The map appears once the teacher plans the lesson."; teacher, plan or provider unavailable: the server's message + "Try again" (`:150-165`, `:442-452`); opened from a check and failed: the screen closes and "{message} The tutor opens instead." (`D/app/checkHandoff.ts:47-53`); any other error (e.g. `teacher_disabled`): a toast only, and the dialog stays open with a header, Close and no body (`:166-168`); closed: "Lesson done.", "Lesson stopped.", "This lesson reached its spending cap.", "The teacher became unavailable, so the lesson closed.", "The teacher kept getting its turns wrong, so the lesson closed.", "Lesson closed.", then "I'll ask you one question on X, on your own, …" or "No later check could be set this time." (`:70-75`, `:643-655`).

**Where the routing record is out of date** (`docs/reviews/teach-handoff-routing.md`): its §6 says a saved lesson that fell back is "reachable only from Today's Continue your lesson", which the simple shell does not render; its §1 says the phone has "no Ask or tutor at all" (the phone Reader has Ask since V4); its MCP section names tools that are not the server's (2.18).

### 2.14 Settings, switches, spend, transport and "no model available"

**Entry:** "Settings Ctrl+," (⋯), Ctrl+, / Alt+S, palette "Open settings", "Grading isn't working · Fix", card actions "Set it up / Raise it / Fix it". Footer "esc close · vault + machine preferences" (`D/screens/SettingsScreen.tsx:115-117`).

| Section | Contents | Where |
|---|---|---|
| AI models | grading / diagnosis / ingest-synthesis / tutor / animation rows: provider select, OpenRouter "model slug…", "apply"; "Choices persist to learnloop.toml; … materializes a per-use-case provider profile"; "LEARNLOOP_AI_PROVIDER={x} is set in the environment and overrides every route below." | `:28-34`, `:369-440` |
| Embeddings | status, backfill, model, dimensions, disclosure | `:447` |
| Decision models | per judge "key present / not ready" | `:476` |
| OpenRouter API key | "saved · ends in ····x" / "not set" | `:495` |
| ChatGPT plan | "not signed in", "signed in as … · plan usage enabled / not granted", "usage limit reached · paused until …" + "try again now", "Continue with ChatGPT", "sign out"; OpenRouter stand-in "…it charges your OpenRouter account." + "Stop using OpenRouter" | `D/components/ChatGPTPlanSettings.tsx:24-252` |
| Ingestion | PDF engine, audio mode, text recognition, transcription | `:548`; `D/components/NativeMediaSettings.tsx:20-24` |
| Animation | renderer manim / video model, quality "ql/qm/qh", length, shots | `:726` |
| Token budgets | inventory and synthesis token limits; "[ingest.budgets] in this vault's learnloop.toml" | `:918-986` |
| Reader, notes, correspondence, Hints | margin-mark density; help style | `:998-1003` |
| Appearance | five palettes | `:1005` |

- **Spend caps are not shown or settable anywhere** (`[ingest.cost_pause] daily_cap_usd = 5.0`, `S/config/schema.py:919`; no cap, usd or spend control in Settings). "Raise it" on a paused book and Under the hood → "Spend & AI routes" ("spend caps, per-route models and provider limits live in Settings for now. from a terminal: learnloop ai status.", `D/screens/underhood/tools.tsx:140-144`) both point at a page with no cap.
- **No feature switch is in the UI.** Keyboard & help tells the learner to set `shell = "classic"` under `[ui]` (`D/components/KeyboardHelp.tsx:79-81`).
- **Older utilities still in Settings** (owner, Nov 8: clear them): embeddings backfill, decision models, animation quality, token budgets, per-route model slugs, PDF engine. None is marked retired.
- **"Use OpenRouter instead"** (`D/components/PlanFallbackOffer.tsx`): "ChatGPT isn't available right now. OpenRouter can do this instead, with your OpenRouter key (it charges that account)…", "Use OpenRouter instead", "Continue with ChatGPT" (signed out), "Not now"; after: "…You can stop it any time in Settings, ChatGPT plan." (`:104-154`).
- **Connect an AI** (`D/components/ConnectAI.tsx`): "Get questions on what you read", "Continue with ChatGPT", "Use an OpenRouter key", "Other (advanced) ▸", "What leaves this computer: passages of the books you add, and your answers…", "Not now"; errors "Signing in didn't finish. Try again.", "LearnLoop couldn't connect.".
- **"What's sent"**: Ask overlay's "ⓘ what's sent" (not the Reader rail), Connect's "What leaves this computer", embeddings and judge disclosures, Quick Add's consent ticks, the card's upload OKs.

**No model available, by surface.** Top bar: "Grading isn't working · Fix". Library: "Connect an AI…" lines (2.6). Practice: self-grade (2.3). Reader: "Couldn't reach LearnLoop's model." and the reading path's environment-variable line (2.9 a). Today: works without a model. Lessons: the server's message + "Try again". Phone: "AI grading is unavailable; your answer is saved. Retry later or finish on the desktop." (`M/practice/QuestionScreen.tsx:85`), "Grading isn't available right now. Your answer is saved." Terminal app: "AI grading is unavailable. Enter a self-grade below." / "AI grading failed: {ExceptionClass}…" (`T/feedback.py:158`, `:303`). Budget spent: book card "Paused…", Reader "Today's {route} budget ({amount}) is used…", figures as an error message, lessons "This lesson reached its spending cap.".

### 2.15 Progress views

"Progress" (Alt+4) opens the concept-graph screen: "concept map" / "knowledge field", "edit" / "● edit mode", "goal overlay", "tab/shift+tab walk concepts" (`D/screens/GraphScreen.tsx:426-551`); the knowledge field's "view: terrain / well / strata" (`D/screens/KnowledgeMapScreen.tsx:165-180`). Topic inspector: header "CLI mirror · learnloop show {id}", "search by id — pi_… lo_… att_… ee_…", "loading {id} …" (`InspectorOverlay.tsx:225`); "▸ Teach me this"; "Starting point" with "? Check what I already know" (pointer only). States: "Demonstrated N%", "━ solid = Demonstrated evidence", "● filled bead = Demonstrated"; "assumed (not tested)"; "untested", "absent · no blueprint", "× means no blueprint, not failure" (`KnowledgeMapScreen.tsx:291-418`). "Worked with help" is not on the map or the inspector except the well's "instructed" bead (2.5). Waiting "loading concept graph…", "loading knowledge map…"; empty "no mapped evidence yet"; jargon on the surface: stress, Ready variance, evidence mass, latent similarity, BlueprintRecipe, capability rim, facet contract, probe. The phone's Progress is a placeholder: "Your goals and past answers are coming to the phone in a later update." (`M/progress/ProgressScreen.tsx:7-8`). Nothing answers the well's three questions (what can I do on my own, what's fading, what's next) in words on Progress or Today.

### 2.16 The phone

Host: `learnloop-mobile serve` (`src/learnloop_mobile/cli.py:38`), `mobile.enabled` off by default (`src/learnloop_mobile/config.py:18`); switches `phone_plan`, `phone_probes`, `phone_reader` on (`:27-37`). No desktop control starts the host or pairs a phone.

| Journey | Entry and labels | States | Mark |
|---|---|---|---|
| Pairing | "Pair this phone", "On the desktop, run learnloop-mobile pair --scope app, then enter its manual code.", "Manual code", "Pair" (`M/pair/PairScreen.tsx:38-46`) | "That code is for the Shortcut. Run learnloop-mobile pair --scope app on the desktop."; "That didn't pair…"; "Pair again to send N waiting captures."; "LearnLoop is open in another tab…" (`M/shell/DbBlocked.tsx:8`). The CLI's default scope is `capture` (`cli.py:58`), so the plain `pair` command yields the Shortcut error | pointer, after a terminal command |
| Today | "{n} min" chips, "Begin" / "Next" / "End session", "Skip it" (held step); "why?" → "Why this", "details" → "How this was chosen" (raw model names, JSON, "Decision {id}", `M/practice/RouterLine.tsx:16-53`) (`M/today/PlanToday.tsx`) | "Reading today's plan…" / "Today's plan couldn't be read." + "Try again"; "Nothing planned for today." / "Nothing here for the phone right now."; "A question is in progress on the desktop. Next here goes on without it."; "Choosing what's next…"; stop offer "Done for today · N minutes." + "Keep going" / "Done for today"; "N questions / a reading … waiting for the desktop" (`M/today/planWords.ts:72-81`). Queue mode (plan off): "How long have you got?" 10/15/25 | pointer |
| A short session | "Submit" / "Try again", "I'm stuck", "Hint" (sheet "With a hint, this answer counts as answered with help (◌)…", "Show a hint"), "Skip", "Back" (`M/practice/QuestionScreen.tsx:631-682`) | "Opening…"; "Grading. You can leave; the result will be here when you come back."; "AI grading is unavailable; your answer is saved…"; short check "Feedback comes when this short check ends · hints are off for now" with **no stop control**; with probes off: "This is a diagnostic check. Continue it on the desktop." + "Next"; a desktop-only item skips silently to the next (`:245-247`) | pointer |
| Feedback | score; "Show anyway" / "Continue without it"; "Looking into what happened here…" / "The look into this answer didn't finish. Your grade stands."; "Possible causes" with "This is my gap / Partly / Not it"; "Show the full answer"; "I think I was right"; "See the feedback on your earlier answer"; "Next" with "Preparing a question on this…" (`M/practice/FeedbackScreen.tsx`, `FeedbackParts.tsx`); "it won't count as independent evidence" (`:57`) | "Reading your feedback…"; load error + Try again / Next | pointer |
| Photo answers, "Fix what was read" | not found (the only file input is capture's "Photo") | | none |
| Capture | 2.7 | | pointer |
| Reader | "Continue reading {title}", book list; "Sections"; "Next section" / "Done with this section"; plan banner "Reading for today's plan · …", "Back to today's plan", "Skip this reading"; "as printed" / "View the page"; selection sheet "Ask", "Save", "Copy"; dose "Try it" / "Show me", "Not now"; quick check "Compare with the source", "Done for now" (`M/read/ReaderScreen.tsx:308-452`; `M/read/SelectionSheet.tsx:115-146`) | "Reading is on the desktop for now."; "Your books open here when the desktop is reachable."; "The list on this phone; the desktop isn't reachable."; "No book is ready to read yet. Add one on the desktop."; "A passage held out for your exam. It isn't shown here."; Ask: "Ask isn't available right now…", "The desktop isn't reachable. Ask works when it is.", "This passage is held out of LearnLoop's models." | pointer |
| Kept comparisons | not on the phone (no phone method) | | none |
| Progress | placeholder (2.15) | | none |
| Something else | "Something else would help" → "What would help right now?"; options a phone can't serve get " (on the desktop)"; a lesson choice is saved, nothing opens | "Looking at what the plan could do…"; "Nothing else is available right now." | pointer |
| Offline | one line, never a modal: "Desktop offline. Reading and capture still work.{ N captures waiting to send.}", "Desktop is busy — trying again.", "Grading isn't available right now. Your answer is saved.", "LearnLoop was updated." + Reload (`M/shell/ConnectionLine.tsx:6-22`) | | |

### 2.17 The terminal app

Launched with `learnloop today [--vault]` (`S/cli/app.py:3784-3800`); without the extra: "The terminal app needs the tui extra: uv sync --extra tui…". It opens an existing vault only ("LearnLoop could not open this vault." + the raw exception, `S/tui/app.py:19-20`).

| Screen | Key bar | Bound, not shown | What the learner meets |
|---|---|---|---|
| Start (`T/start.py`) | "↵ Begin session · ←/→ Minutes · s Skip warm-up" | q | minute chips, "begin session ↵"; internal words on the surface: "scheduler mode short_session — probe_eig suppressed", "N active learning_objects", "probe queue", "overdue >2d", "diagnostic follow-up still queued" (`:290-341`) |
| Today (`T/today.py`) | "j/k Move · enter Practice · 1-9 Quick open · r Refresh" | l/→ | "Due now / Probe queue / Later today"; "No scheduled items."; "press ? for the per-item breakdown" but no `?` binding (`:300-302`); "alg {version}", "AI codex ● ready", the vault path, raw ids, "{component} × 0.42"; no way back to Start or to end the session |
| Practice (`T/practice.py`) | "^enter/^j/F10 Submit · ^h Hint · ^d I'm stuck · ^s Skip · esc Back" | ^t stop the check | "Submit Answer"; ^s leaves the screen and records no skip (`:330-331`); check panel "Diagnostic · observation N of up to M", "feedback is delayed for measurement integrity · hints and ask-tutor are unavailable · ^t stops the check"; "Probe phase · hypothesis set locked", "probe-EIG · information gain", R(t), stability, FSRS-6, rating cap, facets, ±sd |
| Feedback (`T/feedback.py`) | "n / enter Next item · esc Back to queue" (enter is not bound) | ^s Submit grade | "Sending answer to {provider} for evaluation..."; self-grade form (criterion points, confidence, error type, fatal toggles); "score=… rating=… due=… mastery=…", "bayesian … nats vs τ", "Belief update", "tutor note" (the terminal app has no tutor) |

The terminal app has no Reader, capture, goals, lessons, Ask, figures, settings or phone hand-off. It is an owner's power tool; every screen fails O3 (no jargon).

### 2.18 Chat (MCP)

`learnloop mcp serve [--transport http|stdio]` (`S/cli/mcp.py:57-67`), `learnloop mcp token show|rotate`, `learnloop mcp activity`. The server tells the chat model that practice and grading "happen in the LearnLoop app for now: say so rather than improvising a quiz" and to say "LearnLoop at home is offline" when unreachable (`src/learnloop_mcp/server.py:49-61`).

| Tool | What the chat model reads (abridged) | Writes |
|---|---|---|
| `status` | the vault, its version, whether grading is set up, work waiting | no |
| `today` | today's plan: blocks, minutes and why; viewing starts nothing | no |
| `progress` | demonstrated / assumed / learning / untested; certification per goal; topics at risk | no |
| `library` | the sources; exam material by title only | no |
| `find_sources` | verbatim passages with citations, by intent (explain, remediate, alternative, worked example); a dry run shows only the plan | records the passages as read (`readOnlyHint=False`, `:557`) |
| `learning_context` | misconceptions, open hypotheses, recurring mistakes, recent answers; model-written wording held back | no |

No tool captures, practises, compares, teaches or opens a tutor; capture, confirms and chat practice (MCP C1b, C2) are not built at this commit. The routing record's MCP list ("status, attempts, diagnoses, hypotheses") is stale.

### 2.19 One learner on several devices

Desktop: every session start goes through `startSessionOrAsk` (`D/app/sessionHandoff.ts:67-82`): "You have a session open on {owner || 'another device'}.", the draft's first line, "Continue it here, or start fresh. Starting fresh keeps that answer on record.", "Cancel" / "Start fresh" / "Continue it here" (`D/components/SessionElsewherePrompt.tsx:55-63`). When the phone takes a session: "This session continued on {owner || 'your phone'}." + "Nothing here is being saved to it now. Your answers from there carry over if you take it back.", or "This session ended on another device.", with "Start fresh" / "Take it back" / "OK" (`D/components/SessionMovedBanner.tsx:65-78`); practice freezes its writes (`PracticeScreen.tsx:531`). The phone mirrors it ("This session continued on {owner ?? 'the desktop'}.", "Take it back" / "Start fresh"; "A session is open elsewhere" sheet with "Continue it here" / "Start fresh" / "Cancel"; "Its open question has an unsent answer that can only be finished on the desktop…", `M/App.tsx:460`, `:764-870`). Chat has no session.

### 2.20 What the inventory already shows (input to Part 3)

**Journeys with no visible entry.**

1. Entering graded past work (exams, homework, coursework): CLI only (`learnloop seed-exam-attempts`); homework not at all. (Owner: specified and built inside this audit's fix.)
2. Changing a goal's deadline or scope, or deleting a goal: no control and no client call. Pausing or completing one: classic shell only.
3. Creating a first goal from Today in the default shell: no control, though the brief wizard's copy says "make one from Today".
4. Resuming a saved lesson, and "Learn something new": classic shell only. A lesson that fell back to the tutor after being saved is then unreachable in the default shell.
5. "Am I ready?": Reader only, under "learning this for something? ▸".
6. Importing a notes folder, an Obsidian vault or a flashcard deck: none.
7. Spend caps: not shown or settable; two controls point to where they would be.
8. Feature switches: none in the UI.
9. Search while a book is open: Ctrl+Shift+F only, undocumented.
10. "Coming up" (what is scheduled and why): only in the Reader's recap and wrap-up.
11. Pairing a phone and starting the phone or chat hosts: terminal only.
12. Capture on the desktop without the phone: no capture box; the inbox appears only when something new has arrived.

**Labels that promise a different surface.**

1. "Progress" opens the concept-graph editor.
2. "Questions wait for your OK · Review" opens Connect an AI.
3. "Raise it" (a paused book) opens Settings, which has no cap.
4. Palette "Check what I already know" opens Progress.
5. "See the earlier answer and the possible causes" opens the topic inspector.
6. Inbox "Quick Add source" opens the token-budget study-map builder, not Add.
7. "New library…" opens a "new vault" dialog that leads into "Imports & builds".
8. "make one from Today" (brief wizard) names a control the default Today lacks.
9. The classic review's "esc continue" opens a lesson.
10. "◊ teach it" opens teach-back (the learner teaches), not a lesson.
11. "show me" reveals the book's step in active reading, builds a figure elsewhere, and shows a worked example on the phone.
12. "Couldn't reach the page" stands for any arXiv or YouTube failure.
13. The terminal app's "^t … start tutoring" wording is gone, but its panel still names "ask-tutor", and its feedback a "tutor note", in an app with no tutor.

**States with no screen.**

1. The engine's stop reason: a stop looks like finishing the plan.
2. A figure withheld at delivery; any wait estimate; a stuck figure build (no timeout).
3. A hint taken on a check: the banner does not change and feedback says nothing.
4. Which help gave part of the answer away (decision 2): a percentage at most.
5. A lesson that fails to open for a reason other than an unavailable route: an empty dialog and a toast.
6. A goal whose date has passed: nothing asks what now.
7. Reading path with no model: an environment-variable name.
8. The diagnosis arriving after feedback: the sentence changes in place with no notice.
9. Spend refusals that look like any other error (figures, failed builds: the code is dropped).

**Keys and gestures in conflict.** Ctrl+K (palette / Check my work); `?` (why? / Ask); `\` and Ctrl+\; Ctrl+F (three finds); `c` and `t` in the Reader; Alt+S opens and closes Settings; Ctrl+V on Imports & builds adds a source instead of pasting into its field; feedback's hidden `t` starts a similar question even on a right answer; pointer-only spans for "+ new goal", "Teach me this" (inspector), "Check what I already know", the card controls and the Imports & builds actions.

**Jargon on main paths** (default shell, no *details* opened): the new-library route's token budgets and "inventory", "enrichment adjunct", "synthesis", role ids; the router line on feedback ("Router: … floor 5%"); "Stop diagnosing" (kept on purpose); "Attempt recorded · route recovery required"; refused-submit messages with "unassisted and unprimed" and a timestamp; "L4" in the help record; the goal report's facets, certified, qualifying attempts, reservable items; Progress's graph-editor vocabulary and the inspector's "CLI mirror"; the Reader's `tutor_qa.reader_enabled` and `LEARNLOOP_READING_PATH_MODELS` lines; "sidecar unreachable"; "sympy"; "manim"; the phone's "diagnostic check", "independent evidence", HTTP status and router details; the whole terminal app.

### 2.21 What the inventory could not check

- Nothing was run: no layout, timing, focus order, or how a state looks once rendered. The persona walks cover that.
- The plan's why? text was not traced end to end from `lanes.py` to the screen.
- The `deadline` choice of the topic intent control (said to add a goal, `D/api/client.ts:1287`) was not followed in the UI.
- Which features a vault below the current algorithm tag hides (each switch is tag-gated); the walks use vaults at the tag.
- The classic shell was inventoried only where it holds the only entry to a journey.
- Accessibility beyond role and tab-stop checks on the controls named.
- The figures and lessons on the real model route (decision 1): only the walks can show what real teacher turns, figures and grades look like.

---

Sections 3 onward (the walks one by one, the same surfaces side by side, the scorecard, findings, defects with ledger rows, proposals with sketches, and the proposed fix stages) are added when the persona walks are complete.
