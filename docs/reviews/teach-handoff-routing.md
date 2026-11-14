# Teach hand-offs to Teacher lessons: step 0 (Nov 14 2026)

Owner, Nov 14: "For anyting like 'Learn it with a tutor' or 'Stop diagnosing & teach me', these really should be routed to the proper teacher lesson screens". The rule read from it: a control that asks to be taught, or to learn a topic, opens a Teacher lesson; a control that asks a question about the item, note or passage on screen opens Ask tutor.

Base: main `c85993a087`. Branch `feature/teach-handoffs-to-lessons`. This record is step 0 of the step: the map, what depends on the tutor conversation, and what a lesson would receive. **The step stops here** (section 4): a lesson opened on the check's topic today knows nothing specific about what the check found, and giving it that needs a new key in the persisted lesson brief and a ruling on a protection rule. No code was changed.

## 1. Every control that opens Ask tutor or a Teacher lesson

"Fits" is the rule above: **yes**, **no** (a mismatch), or **n/a**.

### Desktop app (apps/learnloop-tauri/src)

The two diagnostic hand-offs are in **bold**. Each is reached by more controls than the brief listed.

| Label (as shown) | Where | Opens | With what | Fits |
|---|---|---|---|---|
| **"Learn it with the tutor"** (simple feedback, route `tutoring`), key ↵ | `screens/DiagnosticReviewScreen.tsx:26`, `:77-85`, `:175` | Ask tutor (modal overlay) with a proactive opening | `{context: "practice", practiceItemId: releasedFeedback[0].practiceItemId, sessionId, proactiveOpen: true}`; App's `setAskTarget` (`app/App.tsx:2103`) | **no**: asks to learn, opens the tutor |
| **"Start tutoring session"** (classic feedback, `[ui] practice_feedback = "classic"`), key Esc | `screens/DiagnosticReviewScreen.tsx:19`, `:133-136`, `:224-228` | the same Ask tutor proactive opening | as above | **no**. In classic mode Esc, the only key, also opens the tutor |
| **"Teach me instead"** (simple practice, during a short check) | `screens/PracticeScreen.tsx:1699` -> `stopDiagnosing` `:1258-1268` | `api.stopProbeDiagnosing(item.id)`, then `openAsk({proactiveOpen: true})`: Ask tutor (modal; a proactive open skips the docked panel, `:457-458`) | practice context on the probe item, the screen's ask state | **no** |
| **"stop diagnosing & teach me"** (classic practice) | `screens/PracticeScreen.tsx:1733-1741` (title "end the diagnostic block and start tutoring") | the same as the row above | as above | **no** |
| **"Stop diagnosing and teach me"** (dialogue check) | `components/DialogueProbe.tsx:200-211`, `:374-382` | `stopProbeDiagnosing`, then `endBlock()`: the panel's own results with "Continue". The panel is mounted only by `screens/CalibrationScreen.tsx:156-168`, whose `onDone` returns to the calibration progress. **Nothing teaches.** (The brief's "leads to the same review screen" is not so at this base.) | | **no**: the label promises teaching, nothing opens (ledger TH-1) |
| "Teach me this" (topic inspector) | `components/InspectorOverlay.tsx:609-618`; `app/App.tsx:2433-2436` | Lesson | `{kind: "open", entry: "learning_object", learningObjectIds: [lo], title}` | yes |
| "teach me this ▸" (Reader notes rail, a selection) | `screens/reader/NotesRail.tsx:254-256`; `screens/ReaderScreen.tsx:4371`; `app/App.tsx:1363-1365` | Lesson | `{entry: "reader_selection", selection}` | yes |
| "Learn *X* now? (about N min)" Start (plan block offer) | `screens/today/LessonOfferBlock.tsx:114-120`, `:70-71` | Lesson | `origin: router_suggestion`, the decision and lesson ids | yes |
| "Start a N minute lesson on X?" Start (offer page) | `screens/today/LessonOfferPage.tsx:18`, `:59` | Lesson | as above | yes |
| Today's suggestion card Start | `screens/today/LessonSuggestionCard.tsx` | Lesson | `suggestion: {decisionId, lessonId}` | yes |
| "Continue your lesson on X" / "Learn something new" | `screens/today/ContinueLessonCard.tsx:52-61` | Lesson (`resume` / `typed`) | | yes |
| "learn this" in "Something else would help" | `screens/today/SomethingElse.tsx:27-45`; used by `FeedbackScreen.tsx:1702`, `TodayScreen.tsx:698`, `TodayPlace.tsx:602`, `app/App.tsx:1291` | Lesson | `entry: "learning_object"`, `preferenceId` (IH7) | yes |
| "Start a fresh lesson" (closed lesson) | `screens/LessonScreen.tsx:389-393` | Lesson | `entry: "learning_object"` | yes |
| "Ask" (practice footer), key `?` | `screens/PracticeScreen.tsx:2354`, `:1021-1033`, `:2432`, `:2448` | Ask tutor (docked panel, or overlay) | practice context, the draft ("Explain this with my work") | yes. Refused during a check, with the line "use “stop diagnosing & teach me” instead" (`:1031`) |
| Ask on a step (work in steps) | `screens/PracticeScreen.tsx:460-463`, `:2065` | Ask tutor under the step | | yes |
| key `?` "ask" / "ask tutor" (feedback) | `screens/FeedbackScreen.tsx:2377-2381`, `:2770`, `:3581` | Ask tutor (docked beside feedback with the panel on) | `{context: "feedback", attemptId, practiceItemId, answerVisibleNow}` | yes |
| key `?` "ask tutor" (Library note) | `screens/LibraryScreen.tsx:490-493`, `:546` | Ask tutor | `{context: "library", noteId}` | yes |
| Palette "Ask the tutor about this" | `app/App.tsx:1917-1931`, `askCurrentContext` `:1600-1638` | Ask tutor for the current practice item, feedback or note; the Reader's Ask with a book open | | yes |
| Inbox capture's ask button (title "Create a subject before asking the tutor") | `components/InboxStrip.tsx:176` | Ask tutor | `{context: "library", initialQuestion: capture text}` | yes (a typed question) |
| Today thread "continue ▸" | `screens/today/TodayPlace.tsx:249-254` | Ask tutor, the earlier thread | | yes |
| Reader rail Ask / library pane ask | `screens/ReaderScreen.tsx:4066`; `screens/reader/LibraryPane.tsx:149`; `screens/reader/AskRail.tsx` | Reader's Ask (a passage) | | yes |

Lessons on the desktop are gated by `algoConfig().lessons` (`app/algoConfig.ts:182`, `teacher.lessons` in the sidecar's config; off shows no lesson control). The lesson screen's own unavailable state (`screens/LessonScreen.tsx:140-155`, `:431-441`) is internal to the screen: codes `plan_unavailable`, `teacher_unavailable`, `provider_unavailable` show "Try again"; anything else (e.g. `teacher_disabled`) goes to `onError`. No caller learns that a lesson failed to open, so a fallback would need a callback from the screen.

### Phone web app (apps/learnloop-mobile; host src/learnloop_mobile)

No Ask or tutor at all (`practice/QuestionScreen.tsx:597`: "the phone offers none of them (it has no Ask or tutor at all)"), no lesson surface ("lessons wait on the desktop", `practice/SomethingElse.tsx:20`; `lesson.*` RPCs are desktop only, `src/learnloop_sidecar/handlers/lesson.py:66-73`), and neither hand-off: the phone shows a short check's line but has no stop control and no block-end route (`practice/QuestionScreen.tsx:73`, `:584`). Nothing to route; **gap**: none of the two hand-offs exists there.

### Terminal app (src/learnloop/tui)

| Label | Where | Opens | Fits |
|---|---|---|---|
| ^t "Stop diagnosing" (key bar); panel text "or press ^t to stop diagnosing and start tutoring", "^t stops diagnosing and starts tutoring" | `screens/practice.py:71`, `:236`, `:349-360`, `:436-437` | `stop_diagnosing_and_teach` directly; then the notice "Diagnostic ended — this item now runs as ordinary tutoring/practice." The TUI has no tutor and no lesson: the item just continues as practice | **no**: promises tutoring that the terminal app does not have (ledger TH-2) |

No block-end "tutoring" route is shown in the TUI. **Gap**: the TUI has the stop hand-off and no lesson surface; per the brief it stays, listed here.

### MCP (src/learnloop_mcp)

Read-only tools (status, attempts, diagnoses, hypotheses); no tool opens a tutor or a lesson or stops a check. Nothing to route.

## 2. What depends on the tutor conversation after a "tutoring" route

Both hand-offs persist everything before any screen opens: the stop through `diagnosis/probe_episodes.stop_diagnosing_and_teach` (`:3447-3497`: the active presentation `invalidated`, the typed transition decision built and written to `probe_episodes.target_decision_json`, status and completion reason `converted_to_tutoring`, a `tutoring_transition` state segment); the block end through `diagnosis/probe_blocks.end_diagnostic_block` (`:452-487`: route `tutoring` only when the episode completed with a diagnosed gap, the decision written, a `tutoring_transition` segment). The sidecar's `stop_probe_diagnosing` (`learnloop_sidecar/handlers/practice.py:667-676`) and the TUI call the same function. The frontends only choose what opens next.

| What | Who reads it | Does a lesson in the tutor's place satisfy it? |
|---|---|---|
| Episode status `converted_to_tutoring` | `probe_episodes.py:715`, `:760` (re-probe producers count it as terminal); `calibration_sessions.py:301` (done); `tutor/tutor_qa.py:2696` (the decision is read from such an episode); `CalibrationScreen.tsx:34` (a colour) | **Satisfies**: written at the stop or block end, never by the tutor; nothing checks that a conversation followed |
| `tutoring_transition` segment | `probe_episodes._first_intervention_at` (`:1984-1990`): attempts after it no longer update the pre-intervention posterior | **Satisfies**: opened by the backend; a lesson is an intervention too, so the boundary is right for it |
| Typed transition decision (`target_decision_json`) | `tutor/tutor_qa._diagnostic_decision_for` (`:2667-2702`) only: attached to the tutor's context on any practice or feedback question on an item of the topic once no episode is open (`:2255`), and the proactive opening (`build_tutor_opening`, `:1580-1608`) | **Kept**: still persisted and still read by any later Ask on the topic's items. **Not used by a lesson**: no lesson code reads it (section 3) |
| Proactive open (`proactiveOpen`) | `components/AskOverlay.tsx:465-500` -> `preview_tutor_opening` (`handlers/tutor_qa.py:578-598`) | **Nothing to lose**: ephemeral by design ("never inserts a question_event": no budget, no hint, no evidence, nothing persisted) |
| Tutor promotion (`spec_tutor_promotion.md`; `promote_tutor_question`) | Learner-initiated on an answered tutor turn (a question event); its snapshot (facet uncertainty at promotion) is written then | **Not needed by the diagnosis loop**: nothing waits for a promotion after a tutoring route. A lesson has no promotion control; a learner who wants one still asks the tutor. The lesson's own learner text goes to the text-gap pipeline (TE2 §11.7) |
| Router, causal orchestrator | No reader of the status, the segment or the decision outside the rows above (searched: `converted_to_tutoring`, `tutoring_transition`, `target_decision`, `tutor_move`, `expected_learner_action`, `'tutoring'`) | **Satisfies**: nothing waits on the tutor |

So (b) loses nothing the diagnosis loop needs: every state transition is the backend's, at the stop or the block end.

## 3. What a lesson opened on the check's topic receives today

The open path a hand-off could use without new fields is "Teach me this" on the topic: `lesson.turn` `open` with `entry: "learning_object"`, `origin: "learner_pick"`, no `preferenceId` (`handlers/lesson.py:226-238` -> `teacher/service.open_lesson` `:649-761` -> `teacher/brief.build_brief` `:819-947`).

| Diagnosis finding | Reaches the lesson? | Where |
|---|---|---|
| Typed transition decision (diagnosed gap, its confidence, repair or instruct, the tutor move, the posterior) | **No**. Nothing in `learnloop.teacher` reads `probe_episodes` or `target_decision_json` | `grep` over `src/learnloop/teacher` |
| First error step or claim | **No** | the decision only |
| Leading hypotheses of the check's attempts | **No**. IH7's diagnosed sources run only for an `origin = 'router'` lesson with a decision id, or a `learner_pick` lesson naming a "learn this" preference (`teacher/diagnosed_sources.follow` `:420-425` returns None otherwise). And even then a diagnostic-probe attempt is protected: `PastWork.attempt_reason` -> `learner_protection.attempt_protection` (`:234-235`, `WITHHELD_PROBE = "a diagnostic check"`) -> `PROTECTED` (`diagnosed_sources.py:472-473`) | |
| Missed criteria (grading evidence) | **No**. The brief's history lists each check attempt as `cold` with its result in words and "kept for an exam or a check: result only" (`brief._history` `:381-418`); `read_history` refuses the question, answer and grader notes of a protected attempt (`teacher/actions.read_history` `:196-209`) | |
| Results of the check's answers | **Yes, as words** ("wrong", "partly right (40%)") in the history headers and the node's `last_cold` | `brief.py:863-865`, `:386-399` |
| A misconception the check normalized | **Partly**: the node lists every open misconception on the topic (`brief._misconceptions` `:342-347`), which includes one the block's end normalized (`probe_blocks.end_diagnostic_block` `:356-377`; a blind-graded attempt's after its diagnosis lands), unmarked among the rest: the teacher is not told which one the check found. Not verified for a mid-check stop: `stop_diagnosing_and_teach` normalizes nothing, and the practice screen's stop does not end the block | |

So a lesson would open knowing that the learner just answered the topic cold and missed, and the topic's open misconceptions, but **not what the check found**: not the gap, not its confidence, not where the reasoning first went wrong, not the missed criteria. The teacher would find the edge again itself (TE2 can serve its own probe right after the check).

**What the open path accepts today** (`LessonTurnInput`, `handlers/lesson.py:81-104`): `entry`, `learning_object_ids`, `selection`, `goal_text`, `add_topics`, `subject_id`, `origin` (`learner_pick` | `router_suggestion`), `suggestion_decision_id`, `lesson_id` (a suggestion's), `preference_id`. None of them names a probe episode or a transition decision:

- `origin` is stored in `lessons.origin` and `lesson_episodes.origin`, both `CHECK (origin IN ('learner_pick', 'router'))` (`migrations/234_teacher_lessons.sql:48`, `migrations/247_lesson_episodes.sql:68`); `origin_ref` means a router decision id and IH7 reads it as one (`_decision_time` on `router_decisions`), so an episode id there would be read as a missing offer (`NO_ORIGIN`) and would misstate the lesson's origin to the receipt and the episode log.
- `preference_id` must name a `router_learner_preferences` row of kind `lesson` (IH3's "learn this"); writing one for a hand-off would put a choice the learner never made into the router's preference data, and IH7 would still withhold the probe attempt.

## 4. Why the step stops here, and the options

The brief's stop condition (c) holds: a lesson opened on the check's topic opens with no knowledge of what the check found, and giving it that needs a new persisted field. Concretely, any version that tells the teacher the finding needs:

1. a new input on the open call (the episode id; plain input, no migration);
2. a new key in the lesson brief, which is persisted whole in the lesson's open turn (`lesson_turns.payload_json`, `service.py:748-752`) and is the teacher's only learner context at open (`brief.py` docstring), plus the episode id in the open turn's `refs` (beside IH7's `preference`), so the lesson's decision record names its origin;
3. a ruling on protection: the decision is computed from diagnostic-probe answers, and today everything written about such an answer is withheld from the teacher (`WITHHELD_PROBE`, honoured by the brief, `read_history` and IH7 alike), while the tutor gets the whole decision after the block ends.

(b) is clean (section 2), so the routing itself loses nothing. The choice is what the lesson should know.

**Option A: route now, carry nothing.** Both hand-offs open "Teach me this" on the check's topic (`entry: "learning_object"`, `learner_pick`), with the fallback to today's Ask tutor opening when lessons are off or the lesson can't open. The backend is unchanged; nothing persisted changes meaning (a lesson row where a proactive tutor opening was, and no tutor opening is persisted today). The lesson knows the cold misses and the topic's misconceptions, not the finding; the decision still steers any later Ask on the topic. Cost: the teacher re-finds the edge, possibly with a probe right after a check. Size: frontend only (about 150 lines with tests).

**Option B (recommended): route, and give the lesson the finding as topic-level words.** Option A, plus: the open call takes the episode id (plain input); `open_lesson` checks that the episode is on the lesson's topic, ended (`complete` or `converted_to_tutoring`) and holds a typed decision (no `kind`), and the brief gains a `from_check` entry with only topic-level content: the diagnosed gap in words (the misconception's statement, the confused topic's title, or the missing prerequisite's title, read from the hypothesis set, never an item's text), its confidence in words, and repair or instruct. Left out: the first error step (a step id inside a protected answer's trace), the raw posterior, the tutor move and scaffold numbers (the tutor's contract, not the teacher's). The open turn's `refs` name the episode. Needs from the owner: (i) that a check's finding, as topic-level words, may reach the teacher although the answers it came from stay protected (the proportionate-protection bar suggests yes: no item text, answer or rubric is passed); (ii) whether the brief key ships live or behind a switch with the brief version bumped (`lesson_brief_v1` is not identity-pinned; IH7 added `sources.from_diagnosis` behind its switch, byte for byte off). No migration.

**Option C: B, and also let IH7 search the sections for the finding.** As B, plus `diagnosed_sources.follow` searches the library with the finding's statements (not the protected attempt's hypotheses) and adds matching sections. Larger: IH7's record shape gains a third origin kind. Not recommended in this step.

**Not offered**: reusing `origin = 'router'` or a fabricated "learn this" preference (section 3).

Whichever is chosen, the same step should fix TH-1 (the dialogue check's stop teaches nothing) and TH-2 (the TUI's wording), and the vault gains a note on the hand-off and the Teacher's entry points (the architecture vault has none: `Concepts/Diagnosis and Remediation.md` stops at stopping rules, and no Teacher note exists).

## 5. For the UX journey audit

- The dialogue check's "Stop diagnosing and teach me" ends the block and shows results; no teaching follows (TH-1).
- The TUI promises tutoring on ^t and has no tutor (TH-2).
- The classic block review continues on Esc, the key that leaves everywhere else, and in the `tutoring` route that key opens the tutor.
- "Start tutoring session" (classic) and "Learn it with the tutor" (simple) name the same step differently.
- During a check, the practice screen's refusal of Ask names the classic control's words ("use “stop diagnosing & teach me” instead") while the simple screen's control says "Teach me instead".
- A lesson's failure to open is invisible to whoever opened it (the screen keeps its unavailable state to itself), so no surface can fall back today.
- The phone has neither a stop control nor a block-end route (it leaves a check for the desktop), so a check started on the desktop and answered there is the only path to either hand-off.
