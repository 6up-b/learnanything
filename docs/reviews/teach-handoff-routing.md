# Teach hand-offs to Teacher lessons (Nov 14 2026)

Owner, Nov 14: "For anyting like 'Learn it with a tutor' or 'Stop diagnosing & teach me', these really should be routed to the proper teacher lesson screens". The rule read from it: a control that asks to be taught, or to learn a topic, opens a Teacher lesson; a control that asks a question about the item, note or passage on screen opens Ask tutor.

Base: main `c85993a087`. Branch `feature/teach-handoffs-to-lessons`. Sections 1-5 are step 0 as it was written before any code: the map, what depends on the tutor conversation, and what a lesson would receive. Step 0 stopped (section 4): a lesson opened on the check's topic knew nothing specific about what the check found, and giving it that needed a new key in the persisted lesson brief and a ruling on a protection rule. The orchestrator chose Option B, shipped live, applying the owner's standing rules (Nov 1: learner history goes to a model whenever it helps, blindness is the grader's only; live changes over switches). Section 6 is what was built.

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

## 6. What was built (Option B, live)

### Backend

- `lesson.turn` `open` takes `probe_episode_id` (plain input, at most 80 characters; `handlers/lesson.py`). A suggestion's Start never passes it, and `open_lesson` drops it, as it drops `preference_id`, for anything but a learner's own start on a topic (`entry` `learning_object`, no selection).
- `teacher/from_check.py` reads the episode: on record, on the lesson's topics, ended (`complete` or `converted_to_tutoring`), with a typed decision (a mapping with no `kind`). Anything else is **ignored, never refused**: the lesson opens as "Teach me this" on the topic does, a warning is logged, and the open turn's payload records `{"version": "lesson_from_check_v1", "probe_episode_id", "status": "ignored", "why"}` with one of "the check is not on record", "the check was on another topic", "the check has not ended", "the check recorded no finding", "the check's finding could not be read".
- An accepted episode: the brief gains `from_check`, the open turn's `refs` gain `probe_episode` (beside IH7's `preference`), and the payload records `status: "used"`.
- `stop_probe_diagnosing` also returns `episode_id` (the episode it converted; null when nothing was open) and `learning_object_id`. Its stop semantics are unchanged: the episode id is read with `open_probe_episode` before the same `stop_diagnosing_and_teach` call.

**What the teacher is told** (`brief["from_check"]`, exactly these keys; `confidence` only when the decision has one in [0, 1]):

```json
{"about": "What the short check on this topic found just before this lesson opened. Topic-level only: the check's questions and the learner's answers to them are not given and must not be asked about.",
 "topic": "<the topic's title>", "learning_object_id": "<lo id>",
 "ended": "the check finished" | "the learner stopped the check and asked to be taught",
 "gap": {"kind": "<kind>", "words": "<words>"},
 "next_step": "repair the belief" | "teach it",
 "confidence": "about 70%"}
```

| Diagnosed gap label | `kind` | `words` |
|---|---|---|
| `misconception:<registered id>` | `mix_up` | the misconception's statement |
| `misconception:<error type>` (legacy, no registry row) | `mix_up` | the error type with spaces |
| `confuses_with:<concept or topic id>` | `confused_with` | "mixes this topic up with <its title>" ("a neighbouring topic" when unknown) |
| `unfamiliar` | `not_learned_yet` | "has not learned this topic yet" |
| `surface_only` | `surface_only` | "knows the surface of this topic but not why it works" |
| `recall_without_mechanism` | `recall_without_mechanism` | "recalls the statement without the mechanism behind it" |
| `procedure_without_selection` | `procedure_without_selection` | "can run the procedure but not choose when to use it" |
| `schema_without_transfer` | `schema_without_transfer` | "has the idea but does not carry it to new situations" |
| `robust_initial_grasp` | `no_gap` | "no gap: the check leaned towards a sound grasp" |
| `other_or_unknown`, empty, anything else | `unnamed` | "a cause the check could not name" |

`next_step` is "repair the belief" when the decision's `instructional_intent` is `repair`, else "teach it". `confidence` is the decision's `diagnostic_confidence` rounded to the nearest ten per cent (a display band, no threshold). Never passed: the first error step or claim, the posterior, the tutor move, the scaffold level, the reveal budget, the target facets, the source refs, the instructional action. The `about` line exists because the doctrine names no such key; changing the doctrine would move its identity, and the entry says what it is instead.

**Brief version: not bumped (judgment call).** `lesson_brief_v1`/`lesson_brief_v2` name the brief's shape for the teacher and for `te2.lesson_te2`, which compares the version for equality, so a bump would make every new TE2 lesson read as a TE1 one. `from_check` is an optional key present only on lessons opened from a check, as IH7's `sources.from_diagnosis` is; an older lesson has none and reads exactly as before, since nothing reads the key but the teacher's prompt (the brief is sent whole). Nothing persisted changes meaning: the lesson row, its origin (`learner_pick`) and its entry are what "Teach me this" on the topic writes; the open turn gains an optional `refs.probe_episode` and `payload.from_check`. The playbook's successor is not needed: no score, schedule or projection reads either.

### Desktop

One module (`app/checkHandoff.ts`): the `CheckHandoff` request, the labels, and `useCheckHandoff`, App's side. `teachFromCheck` opens the lesson (`entry: "learning_object"`, the topic, its title, `probeEpisodeId`) when `algoConfig().lessons` is on, and otherwise runs the caller's fallback at once. While that lesson is open, LessonScreen gets `onOpenFailed`: an opening that fails for **any** reason except `lesson_exists` (the teacher's route down, `teacher_disabled`, a refusal such as `unknown_topic`) closes the lesson screen, shows "<the error's message> The tutor opens instead." and runs the fallback. Every other lesson keeps the screen's own unavailable state and Try again.

| Control | Labels now | Opens |
|---|---|---|
| Review, route `tutoring`, simple (↵) and classic (button and Esc) | "Teach me this"; "Learn it with the tutor" when lessons are off | a lesson on the review's topic with the block's `episodeId`; fallback: the proactive tutor opening on the block's first question (the old behaviour) |
| Practice card during a check, simple and classic | "Stop diagnosing and teach me" on both (was "Teach me instead" / "stop diagnosing & teach me"); classic's tooltip says lesson or tutor | the stop, then a lesson on the item's topic with the stop's `episodeId`; fallback: the screen's own proactive `openAsk` (the old behaviour) |
| Practice card's refusal of Ask during a check | "use “Stop diagnosing and teach me” instead" | |
| Calibration dialogue (TH-1) | "Stop diagnosing and teach me" | the stop, then `endProbeDialogue` (releases and normalizes the turns), then a lesson on the topic with the episode, then `onDone`, so calibration's progress is under the lesson and is what closing it shows; fallback: the proactive tutor opening on the turn's question (App's `setAskTarget` through `CalibrationScreen`). A stop that fails shows the block's results as before |

The tutor wording remains only where the tutor is what opens: the review's label with lessons off, and the fallback notice.

### Terminal app (TH-2)

No lesson surface was built. ^t still stops the check; the notice is now "Check stopped. Lessons are in the desktop app; this question goes on as practice.", the check's hint refusal says "press ^t to stop the check (lessons are in the desktop app)", and the probe panel "^t stops the check". The gap stays: the terminal app can't teach.

### Phone, MCP

Nothing to route (sections 1, 4).

### Step 7: the practice card's mid-check stop

Read: `stop_diagnosing_and_teach` converts the episode but nothing ends the block, and `post_attempt._defers_to_block_end` had skipped each committed in-block answer's normalization, follow-up workflow and diagnosis job (`post_attempt.py:155-188`), leaving them to `end_diagnostic_block`. So after a stop from the practice card or the terminal app, those answers are never normalized (no misconception rows from them, which the brief's node would list), never diagnosed, and their withheld feedback is never shown. The lesson still gets `from_check` (the decision reads the observations' posterior, not the normalization), so it has less than the block-end path gives it only in the topic's misconception list. The calibration dialogue ends its block after the stop and is unaffected. Ledger TH-3; the diagnosis loop is not changed in this step.

### Tests

- Python, `tests/test_teacher_from_check.py`: the finding in topic words, with the first error step, the confidence and scaffold numbers, the posterior's other value, the tutor move and the source ref absent from every teacher prompt, and no item's prompt or answer in the entry; the open turn's refs and record; no `from_check` for a lesson opened any other way; an unknown, foreign, still open, opening-stamped or decision-less episode ignored with its reason while the lesson opens; each gap kind's words; the sidecar stop returning its episode and a real decision reading as topic words; the RPC passing the episode for a learner's own start and not for a suggestion's.
- Vitest: `app/checkHandoff.test.tsx` (the hook's lesson, its fallback on a failed opening with the notice, lessons off; the review's route simple, classic with Esc, lessons off on both; calibration's return), `components/DialogueProbe.test.tsx` (the stop's lesson and fallback; a failed stop), `screens/LessonScreen.test.tsx` (the episode id on open; `onOpenFailed` for `plan_unavailable`, `teacher_disabled`, `unknown_topic`), `screens/PracticeScreen.phase4.test.tsx` (the stop on both cards with its fallback; the refusal line).
- Assertions changed: one. `PracticeScreen.phase4.test.tsx` "a short check looks like any other question" looked for the button "Teach me instead"; it now looks for "Stop diagnosing and teach me" (the label changed by decision). No other existing test asserted the old routing.

### For the UX journey audit (after this step)

- The practice card's stop still leaves the block's answers un-normalized, undiagnosed and their feedback unseen (TH-3).
- The terminal app has the stop and no lesson; it can only say where lessons are.
- The phone has neither hand-off.
- "Stop diagnosing" is the one place simple mode names diagnosing; the owner's words were kept on purpose.
- A lesson from a check that fails after it was saved (its first teacher turn) falls back to the tutor; the saved lesson is then reachable only from Today's "Continue your lesson" (TE2).
- The review's next step says "Teach me this" with lessons on, though the lesson may still fall back to the tutor; the notice says so when it does.
