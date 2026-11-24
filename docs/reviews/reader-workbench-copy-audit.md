# Reader workbench copy audit

Paths in the tables are relative to the checkout. `desks/` and `LessonView.tsx` are under `apps/learnloop-tauri/src/screens/`. `handlers/` is under `src/learnloop_sidecar/`. Python modules outside `handlers/` are under `src/learnloop/`. Section numbers follow the supplied audit.

## 5. Protected material

| Item | File | Old text | New text or disposition |
| --- | --- | --- | --- |
| 5.1 Passage, selection, caption and note headers; Append | `desks/menu/model.ts`, `ContextMenu.tsx`, `desks/DeskShell.tsx`, `desks/pads/PadOverlays.tsx` | “a passage · <quote>”; “Scratchpad · <quote>”; “your pad · <quote>” | Pad-line menu says “Pad options.” The keyboard-created Scratchpad uses “Scratchpad · new notes.” Source menus and their Append action left for the menu worker. Gating Append on known protection needs a data-flow fix (COPY-1). |
| 5.2 Stored passage details | `desks/menu/KnowsPanel.tsx`, `handlers/passage_union.py`, `passage_union/union.py` | “linked passages · <quote>”; “questions written for this passage”; “nothing of [the check] shows” | Panel copy left for the menu worker. Suppressing stored details from protected rows and following protection to the link destination needs a data-flow fix (COPY-2). |
| 5.3 Saved chapters after a protection change | `desks/video/ChaptersPanel.tsx`, `model.ts`, `handlers/video.py`, `source_retrieval/video_chapters.py` | “<chapter title> ◇ <topic title>” | List, result, decision and follow-along replies already mask due cold checks. The panel, ticks and follow chip use “Chapter at <time>” for a masked chapter, and its tags use “Topic details hidden.” Reclassification as exam or held-out material still needs a protection check on saved reads (COPY-3). |
| 5.4 Scheduled lesson follow-up | `LessonView.tsx`, `teacher/service.py` | “I’ll ask you one question on <topic>, on your own, <date>” | “Follow-up question scheduled <date>. Answer it on your own.” Transfer keeps its independent new-situation prompt. The review renders the date and purpose from the existing response. |
| 5.5 Goal sentence, title and unmatched phrases | `desks/goal/GoalBand.tsx`, `PathView.tsx`, `model.ts`, `marks.tsx` | Quoted goal sentence, title, unmatched phrase and proposed topic | “Your goal”, “Switch goal”, “Goal <number> · set <date>”, “A topic still needs a match” and “For your goal.” Goal and phrase identities stay on their existing actions. Restoring descriptive safe labels requires masking data across goal reads (COPY-4). |
| 5.6 Neutral section, exercise and topic details | `curriculum/goal_lens.py`, `desks/goal/model.ts`, `GoalLayer.tsx`, `PathView.tsx` | “A cold check is due on a topic here. Why it matters comes back once you’ve answered it”; “a section held until its cold check” | “Details are hidden while a question is due”; “Topic details hidden”, “Section details hidden”, “Exercise details hidden.” The held section title takes precedence in the current-location label even for optional or unmapped sections. |
| 5.7 Reasons for a refusal | `LessonView.tsx`, `teacher/service.py`, `source_retrieval/video_chapters.py`, `curriculum/goal_lens.py`, `desks/menu/{ContextMenu,ExerciseSheet,verbs}.*` | “exam or held-out material”; “it would give an answer away”; “This video is protected or isn’t a teaching source” | Lesson end offers a new lesson. An unavailable figure says the learner can continue. Unavailable chapter suggestions say the video is still available. Unavailable section suggestions say to choose a different section. Menu notices and exercise refusal left for the menu worker. |

## 2. Claims and ordinary states

| Item | File | Old text | New text or disposition |
| --- | --- | --- | --- |
| 2.1 Handwriting and offline desk changes | `desks/pen/{InkLine,PenLayer,inkCache}.*`, `desks/DeskShell.tsx` | “your ink is kept”; “kept on the page”; “it is kept here until it can be” | Pending ink and desk changes ask learners to keep LearnLoop open. Pen fallback identifies visible ink and explains how to make the intended mark. Failed conversion offers typing or retry in the relevant control. The outbox stores queued changes in memory. |
| 2.2 Adding to a pad, diagrams and lifting | `desks/DeskShell.tsx`, `desks/pads/{PadOverlays,PadStackWindow}.tsx`, `desks/menu/verbs.ts` | “in the running pad”; “appended to”; “the figure is in your running pad”; “it lands when it’s ready”; “lifted to” | Video time says “adding to the running pad…”. Figure generation says “Making a figure for this line…” and reports generation failures. The lift stub describes the new pad the learner can see. Menu Append, Show me and their notifications left for the menu worker. Confirming the specific write and handling a rejected diagram insert need acknowledgments or new error handling (COPY-5). |
| 2.3 Reply offer | `desks/companion/DiffProposal.tsx`, `desks/DeskShell.tsx` | “Add this to your pad”; “accepted · written to” | “Copy the full reply” with a preview of up to six nonblank lines. Local success says “Reply queued”. The callback inserts the whole reply and queues persistence (COPY-5). |
| 2.4 Reconciliation, drain and wait before asking | `desks/DeskShell.tsx`, `desks/pads/DrainPanel.tsx`, `desks/companion/{Companion.tsx,asks.ts}` | “couldn’t be saved, and was undone”; “kept”; “left in the library”; “once [the desk] is saved” | Check the desk after a refusal, look for the separate line after overlapping edits, and keep LearnLoop open for pending writes. Drain says “Saving your choice…”, then “Keep selected” or “Leave selected”. Companion says it is waiting for desk changes or the question hasn’t been sent. The current settle result and Retry need follow-up work (COPY-5, COPY-6). |
| 2.5 Pending reply and lesson outage | `LessonView.tsx`, `handlers/lesson.py`, `teacher/service.py` | “sent”; “your lesson is saved and resumes when it’s back” | “Sending…” while the optimistic reply is pending. A route error says “Your lesson is saved” only for the saved-lesson branch. Both outages point to the existing Try again action. |
| 2.6 Companion focus, queue and history | `desks/companion/{Companion.tsx,asks.ts}` | “following”; “asked”; “pieces so far”; “every exchange stays here”; “it is in your history” | “Open now”, “waiting to send” or “Working on an answer…”, and “Browse saved questions and replies by day and desk.” Expiry offers History or Ask again. “Answer saved in History” comes from the explicit kept flag. |
| 2.7 Scratchpad analysis and provenance | `desks/pads/PadStackWindow.tsx`, `pads/emission.py` | “LearnLoop reads your scratchpads”; “Nothing here is graded”; “quoted, not read as your words” | Explains that typed or converted handwriting can suggest help, quotes can identify the learner’s wording, and submitting writing counts as a practice attempt or teach-back. Tooltips name source, LearnLoop or drawing. The eligibility test and submission action are unchanged. |
| 2.8 Goal progress and positions | `desks/goal/{PathView.tsx,GoalBand.tsx,model.ts}`, `desks/Shelf.tsx` | “read”; “not read”; “nothing due · the path is read”; “you are reading”; “% through” | “Progress recorded”, “No completion recorded”, “No cold checks due. No further reading suggested on this path”, “In view” and “Position <N>%.” A completion flag may reflect all passages shown or a marked completion. |
| 2.9 Readiness and depth | `desks/goal/{GoalBand,PathView,GoalLayer}.tsx`, `desks/goal/model.ts`, `curriculum/goal_lens.py` | “readiness from cold checks”; “its LO is demonstrated”; “not needed for your goal”; “a cold check will tell” | Readiness reflects answers and estimates. Reasons say shown in practice, treated as familiar or pending a cold check. “Optional at this depth” and “Included at a deeper level” describe the reading groups. |
| 2.10 Due and answered counts | `desks/goal/{model.ts,PathView.tsx,GoalBand.tsx}` | “cold checks due today”; “due today” | “<N> cold checks due · answer in Today”; “Due”; “Answered today” still describes the day-filtered state. |
| 2.11 Practice lookup, draft and carried questions | `desks/pads/PadOverlays.tsx`, `desks/Shelf.tsx`, `desks/DeskShell.tsx`, `handlers/pads.py` | “tied to nothing to practise yet”; “your answer is kept”; “it waits in your session”; “it comes back beside a related passage” | “No topic to show. Try again or choose another passage.” The failure points to the draft still visible in the form and its Answer button. Carry confirms the saved question and says it may appear beside a related passage. Distinct lookup outcomes and checking `applied` are follow-up work (COPY-7, COPY-10). |
| 2.12 Notebook run, idle and review | `desks/notebook/{padNotebooks.ts,NotebookFrame.tsx,LessonNotebook.tsx}` | “ran”; “notebook stopped”; “nothing new is revealed or recorded” | “Ready to run” without a result, “Finished” with a result, pause copy points to Resume, and “Review the notebook from this lesson.” |
| 2.13 Chapters, follow and Overview | `desks/video/{ChaptersPanel.tsx,model.ts}`, `desks/overview/Card.tsx` | “no chapters yet”; “cancelled · nothing was kept”; “following ▶ <time>”; “not opened yet” | “No chapters to show” with a reopen hint, “Chapter suggestion stopped”, “Looking for a passage at ▶ <time>…” and “Preview unavailable”. Distinguishing a failed list or cancel needs a separate error state (COPY-9). |
| 2.14 Lesson close, thinking and practice import | `LessonView.tsx`, `desks/menu/ExerciseSheet.tsx` | “Lesson done”; “the teacher kept getting its turns wrong”; “the teacher reads it, the grader never does”; “these 0 are in your queue” | “Lesson finished”; return to Path after a failure; the teacher can use optional thinking and the answer is graded separately. “Working on your lesson…” covers several pending actions. Exact grading status needs a more specific state (COPY-11). Import result text left for the menu worker. |

## 4. Recovery

| Item | File | Old text | New text or disposition |
| --- | --- | --- | --- |
| 4.1 Desk, window, source and settings load | `desks/DeskShell.tsx`, `desks/windows/PanelWindow.tsx` | “opening your desks…”; “once its kind is built”; “that source didn’t open”; “Reading the library settings…” | The existing desk error callback directs the learner to reopen Reader. Window and source failures point to the library. The settings panel uses its existing error state to ask learners to reopen the window. An inline desk retry is follow-up work (COPY-12). |
| 4.2 Exercise, submission and teach-back | `desks/menu/ExerciseSheet.tsx`, `desks/pads/PadOverlays.tsx`, `handlers/pads.py`, `pads/submission.py` | “the import did not finish”; “start a practice session first”; “nothing to submit this to yet”; “The attempt entry point recorded no attempt” | Start a session in Practice, open the pad for the question, reopen the question, or resume the teach-back from Practice. Exercise import failure left for the menu worker. |
| 4.3 Goals with no reading, no check host or failed choice | `desks/goal/{GoalBand.tsx,GoalLayer.tsx,controller.ts}`, `handlers/goal_lens.py` | “not mapped yet”; “map it”; “nothing on the path yet”; “couldn’t keep that choice” | “Find reading”, try again or change topics in Goals, choose a goal you set, reopen Path before retrying a choice, and answer due cold checks in Today. The inactive check button and silent background failure need wiring or state changes (COPY-8). |
| 4.4 Menu suggestion and verb dead ends | `desks/menu/{ContextMenu.tsx,verbs.ts}`, menu portions of `desks/DeskShell.tsx`, `handlers/passage_union.py` | “nothing found”; “no figure”; “couldn’t do that just now”; “That menu is no longer kept” | RPC refusal messages identify the available action, including reopening an expired menu, reselecting a passage and playing the video to a caption. Menu rows, empty states and action notices left for the menu worker. |
| 4.5 Search and inbox results | `desks/search/{SearchPanel.tsx,model.ts}`, `desks/DeskShell.tsx`, `handlers/search.py` | “search every source”; “couldn’t search just now”; “by meaning: couldn’t finish”; “this result has nothing to open yet” | Search prompts for two characters. Failures suggest editing the query or using word matches. An unavailable result directs learners to search by source title, and inbox results point to Today, then Inbox. |
| 4.6 Unavailable conversation, Ask and History | `desks/windows/ThreadWindow.tsx`, `desks/companion/Companion.tsx`, `desks/DeskShell.tsx` | “It is in the companion’s history”; “no answered exchange”; “Something went wrong”; raw History error | Look in the companion’s History, reopen History or the conversation, choose another passage, or give permission to use AI if that is the reason. The actual retry control remains available under its existing condition. |
| 4.7 Pads, lessons and carried lists | `desks/pads/{PadStackWindow,DrainPanel}.tsx`, `desks/Shelf.tsx`, `desks/menu/KnowsPanel.tsx` | “Pads need the desks”; “a lesson opens here only in the desks”; “couldn’t read this pad”; loading plus a raw error | Open the pad from a desk or reopen it from the window list. Open the lesson from Path. Reopen carried questions or today’s pads after an error. Passage details failure left for the menu worker. |
| 4.8 Notebook state and requests | `handlers/notebooks.py`, `desks/notebook/NotebookFrame.tsx`, `notebook_runtime/runtime.py` | “A notebook is a .py file named relative to the vault”; “no marimo cells”; “Nothing was released”; “marimo refused the run” | Open from the lesson, add a Python cell, choose a smaller notebook, reopen and run code, or return to the lesson. Runtime exceptions are translated at the RPC boundary. The session limit still points to closing a notebook. |
| 4.9 Pen limit, expired conversion and erase | `handlers/ink.py`, `desks/pen/{inkCache.ts,InkLine.tsx,PenLayer.tsx}`, `pads/ink.py` | “This reading used its calls”; “LearnLoop restarted”; “not read (<code>)”; “No standing stroke <id>” | Type the handwriting after a limit or if conversion fails. Try again after interruption. The mark is already gone, or open its pad to erase it. |
| 4.10 Lesson questions, unavailable grader and figures | `handlers/lesson.py`, `teacher/service.py`, `LessonView.tsx` | “grading is set to manual”; “lesson_id is required”; “There is no open check”; “couldn’t be graded (<exception>)”; “No later check could be set” | Enable automatic grading in Settings, reopen the lesson or select Submit answer again. The ordinary no-follow-up state has no failure line. Unavailable figures say the lesson can continue. |
| 4.11 Chapters unavailable, expired or already decided | `handlers/video.py`, `desks/video/ChaptersPanel.tsx`, `source_retrieval/video_chapters.py` | “LearnLoop restarted or the vault changed”; “This chapter was decided already”; “no transcript sections”; “over_budget” | Select Suggest from the transcript again, reopen the video for an updated chapter, or continue watching. A cap points to existing chapters. Silent cancel failure remains in COPY-9. |

## 1. Internal vocabulary

| Item | File | Old text | New text or disposition |
| --- | --- | --- | --- |
| 1.1 Topic and outline IDs | `desks/pads/PadOverlays.tsx`, `LessonView.tsx` | Raw topic IDs and unnamed step shows `node.id` | “Choose a topic”, “Topic <number>” and “Lesson step <number>.” The existing option values and keys are unchanged. Safe, descriptive topic names require server data (COPY-10). |
| 1.2 Goal recommendation vocabulary | `desks/goal/{PathView.tsx,GoalLayer.tsx,model.ts}` | “learning objects”; “goal LO”; “primary”; “prerequisite”; converted override names | “Topics for your goal”, “Goal topic”, “Main reading”, “Background” and “Another explanation.” Chosen overrides read as sentences. |
| 1.3 Why a section appears | `curriculum/goal_lens.py`, `desks/goal/marks.tsx` | “coverage judged it”; “coverage no longer finds here”; “is about (your words)”; raw level as mark label | Explain the current or previous link, the main reading or the learner’s choice. “Why this is suggested” names the mark action. |
| 1.4 Passage details taxonomy and matching | `desks/menu/{KnowsPanel.tsx,model.ts,verbs.ts}` | “what this knows”; “how well it is placed”; schema values; “found by search, not checked” | Left for the menu worker. |
| 1.5 Passage link and caption vocabulary | `desks/pads/PassageMarks.tsx`, `desks/pen/PenLayer.tsx`, `desks/DeskShell.tsx`, `desks/menu/{KnowsPanel.tsx,model.ts,verbs.ts}` | “needs re-anchoring”; “from another reading”; “transcript cue”; “no words under it” | Earlier-version link tooltip says it may open nearby. Use “caption” for the video-time action, and tell learners where to draw the pen mark. Source-menu copy and Append highlight notice left for the menu worker. |
| 1.6 Notebook runtime vocabulary | `desks/notebook/{menuBridge.ts,PadCell.tsx,padNotebooks.ts,NotebookFrame.tsx}` | “marimo cell”; “reactive”; “kernel not started”; “raised an error in <N> ms”; “sandboxed”; “vault changed” | “Python cell”, “Run code”, “Ready to run”, “Starting Python”, “Code didn’t finish” and “closed when you switched libraries.” |
| 1.7 Lesson and companion vocabulary | `LessonView.tsx`, `desks/lesson/model.ts`, `desks/companion/Companion.tsx` | “MAP”; “inspector”; “doctrine”; “route”; “forecast(s)”; “committed answers and the reveals”; “pieces so far”; “claims link to the passage” | “Lesson outline”, “How this lesson was made”, “Teaching rules”, “AI service and model”, “Learning estimates”, “Your saved answers and lesson feedback”, and “Source links”. Open a conversation in a window. |
| 1.8 Search terminology and settings | `desks/search/{model.ts,SearchPanel.tsx}`, `handlers/search.py` | “meaning index”; “source_retrieval.enabled = false”; “not embedded yet”; “by meaning” | “Word matches”, “Similar match”, “Looking for similar passages” and partial source coverage in plain words. The RPC keeps its status and groups. |
| 1.9 Desk keys and focus | `desks/keys/router.ts`, `desks/DeskShell.tsx`, `desks/model/workspace.ts`, `desks/windows/PanelWindow.tsx` | “pane · desk”; “share · own slot”; “hovered object”; “first promoted action”; “the drain”; “barrel”; “ungather”; “navi hints”; “rail” | Name the window, its position, the available action, the pen side button, keyboard shortcuts and the book sidebar. |
| 1.10 Protocol and pad refusal messages | `handlers/desks.py`, `desks/{protocol,workspace}.py`, `desks/pads/model.ts`, `pads/blocks.py` | Client, batch, slot, desk and window IDs, block and version IDs, anchor event details, “It no longer applies” | Reopen the desk, window or pad, check the latest text, or add your own note below the line. Error codes and structured details continue through the existing handler. |
| 1.11 Validation details shown to learners | `handlers/{passage_union,goal_lens,ink,pads}.py`, `pads/carried.py` | Span/extraction/annotation/block/request IDs; config keys; “Practice Item <id>”; “A label names the version it expects” | Reselect a passage or pad line, play to a caption, reopen the menu, keep reading or open Practice if reading help is off, reopen a question in Practice, or reopen carried questions. |

## 6. Words for symbols

| Item | File | Old text | New text or disposition |
| --- | --- | --- | --- |
| 6.1 Pin ⚲ | `desks/pads/{PadStackWindow,DrainPanel}.tsx` | Bare pin | “Pinned” tooltip. |
| 6.2 Carried question ◌ | `desks/pads/PassageMarks.tsx`, `desks/menu/model.ts` | “a question you carried” | “Open carried question” in title and accessible name. Menu row already has words and is left for the menu worker. |
| 6.3 Pen/sketch ✎ | `desks/pads/{PassageMarks,PadStackWindow}.tsx` | Bare sketch; ink title; pad backlink | “Sketch”, “Handwriting”, “Open pad line”. |
| 6.4 Window and pad marks § ◇ › ? ⇄ | `desks/DeskShell.tsx`, `desks/pads/PadStackWindow.tsx` | Unlabeled window kind and “source mark” / “tutor mark” | Window type titles; “Show source details”, “Show reply details”, “Show diagram details”, “Show suggestion”. |
| 6.5 Code and video ◆ ▶ | `desks/pads/PadStackWindow.tsx`, `desks/notebook/PadCell.tsx`, `desks/DeskShell.tsx` | Bare code and video marks; “run this cell” accessible name | “Python cell”, “Run code”, “Video” titles. |
| 6.6 Goal marks and check diamonds | `desks/goal/{GoalBand,PathView,marks}.tsx` | Dot and check markings, raw level accessible name | “Cold check due”, “Cold check answered today”, “In view” titles, and “Why this is suggested” for margin marks. The Path legend names the reading groups. |
| 6.7 Window dots and progress | `desks/DeskShell.tsx`, `desks/Shelf.tsx` | Dots with accessible names only; progress bar intervals | Window title on hover. “Current position”, “Goal reading”, and “Chapter” for segments. |
| 6.8 ⓘ i ✓ | `desks/DeskShell.tsx`, `desks/menu/{ContextMenu.tsx,model.ts}`, `desks/video/ChaptersPanel.tsx` | Bare check on the current menu destination | Current destination left for the menu worker. Pad info has “where your words go” and the check beside chapters already says “accepted”. |
| 6.9 + ✕ × ‹ › ☰ | `desks/DeskShell.tsx`, `desks/companion/Companion.tsx`, `desks/pen/PenLayer.tsx`, `desks/Shelf.tsx`, `desks/menu/ContextMenu.tsx` | Unclear close action and previous/next | “Clear selection”, “Hide pen message” and previous/next window titles. New desk, Close and strip controls already have words. Suggestion dismissal left for the menu worker. |
| 6.10 ↩ ↗ → › | `desks/pads/PadStackWindow.tsx`, `desks/companion/Companion.tsx` | Source and history actions carried by arrows | “Open source”, “Open passage”, “Moved to <pad>”, “Open conversation in a window” and “Show older replies”. |
| 6.11 Keys and sequences | `desks/search/SearchPanel.tsx`, `desks/pads/{PadOverlays,DrainPanel}.tsx`, `desks/notebook/{PadCell.tsx,padNotebooks.ts}`, `desks/DeskShell.tsx`, `desks/video/model.ts` | ↵ ⇧↵ ↑↓ = − 0 / . and letters; sequences such as 1k | Keep the keys and name Enter, Shift+Enter, Up/Down arrows, Equals, Minus, Zero, Period and Path in copy or titles. Pad review titles say “Press <number>, then K/L/C”. Follow and search retain their adjacent wording. |
| 6.12 Search, empty location and decorative marks | `desks/search/SearchPanel.tsx`, `desks/goal/{GoalBand,PathView}.tsx`, `desks/pads/PadStackWindow.tsx`, `LessonView.tsx`, `desks/menu/model.ts` | Search icon and placeholder; “—” for no location; decorative marks | Search input has a persistent accessible name and the icon has a Search title. “No passage in view” in the empty-location title. Marks with adjacent words retain them. Menu glyphs left for the menu worker. |

Section 3 and the proposed glossary were outside this pass.

## Verification

The patch changes messages, accessible names and text rendering. It preserves existing event handlers, shortcuts, RPC names and codes, and the payloads used to choose a topic, goal or passage. The keyboard-created Scratchpad title is the one intentional change to text written to a pad. Save and retry behavior remains on the same paths. The raised error types and structured details stay available to callers. No style sheets or class names changed.

### Assertions changed with the copy

| File | Assertions or selectors updated, and why |
| --- | --- |
| `LessonScreen.test.tsx` | Close says “Lesson finished.” A follow-up still shows the schedule and independent answer instruction, and now asserts the topic title is absent. The protection close still offers a new lesson through the existing action. |
| `desks/DeskShell.menu.test.tsx` | Notebook-frame pad header now says “Pad options” and the live notebook insert is “Python cell”. |
| `desks/DeskShell.test.tsx` | Video-time shortcut, Undo grouping, swipe status, queued companion progress, four search-input selectors, drain confirmation, earlier-version tooltip, carried-question button, reply offer and queued status, and unanchored-question recovery. |
| `desks/companion/Companion.test.tsx` | Answer-in-progress text in a running fixture, permission prompt, two explicit History-save assertions, focused-window line, unavailable copy destination, queued reply, and write-wait label. |
| `desks/goal/GoalDesk.test.tsx` | Neutral goal switcher, two topic counts, and switcher plus numbered goal option selectors. The RPC goal identity assertion stays. |
| `desks/goal/components.test.tsx` | Goal label/date, due marker title, hidden topic label, Find reading action, goal refusal, both video-head states, section and paper callout labels, reason-card heading and section basis, two scoped count/control assertions, in-view text and due-row status. |
| `desks/goal/model.test.ts` | Depth line, both topic counts, due count, complete-path line, background and optional location labels, hidden dot, main and background callouts, and neutral held body. |
| `desks/goal/protection.test.tsx` | Neutral fixtures follow the new labels. The existing leak check now opens the goal selector and includes raw goal and unmatched text. The optional held-section location also has an explicit assertion. |
| `desks/goal/shelf.test.tsx` | Main reading counts, alternate reading, no link, optional reading and two partial-link states. Mark and range checks stay. |
| `desks/goal/watch.test.tsx` | Optional-at-this-depth line for other sections. |
| `desks/lesson/lessonWindows.test.tsx` | Close and saved-review descriptions, and the neutral held-title fixture. |
| `desks/notebook/LessonNotebook.test.tsx` | Neutral notebook-review line. The no-release assertion stays. |
| `desks/notebook/NotebookFrame.test.tsx` | Start, restart, repeated stop, library switch, both timed retries and final failure text. Direct checks of the two retry attempt counts replace the counts removed from the UI. |
| `desks/notebook/PadCell.test.tsx` | Python cell, ready states and Run code selector. |
| `desks/notebook/padNotebooks.test.ts` | Ready, starting, finished, paused, failure and Python cell insert metadata. Key and glyph stay pinned. |
| `desks/pads/PadStackWindow.test.tsx` | Provenance-specific titles and scratchpad analysis message, three Python cell selectors, two neutral notebook-menu headers, Practice recovery, both suggestion selectors, and source-details selector. |
| `desks/pads/passageMarks.test.tsx` | Accessible carried-question selector still finds both placements. |
| `desks/pen/PenLayer.test.tsx`, `inkCache.test.ts`, `inkPad.test.tsx` | Conversion-failure and plain-ink prompts, unconfirmed ink save, and typed-recovery prompt. Stroke, write and typing assertions stay. |
| `desks/search/SearchPanel.test.tsx`, `model.test.ts` | Panel input label, failed matching recovery, and dropped “by meaning” prefix on the summary. |
| `desks/video/protection.test.tsx`, `video.test.tsx` | Protected chapter time label in both chip assertions and neutral fixtures. Waiting, suggesting and stopping copy follows the matching states. |
| `tests/test_reader_rd0_protocol.py` | Nothing-to-the-right refusal text. Refused status, code and succeeding rename stay checked. |
| `tests/test_pad_stale_edits_stacks_and_passage_reads.py` | Last-pad refusal text. Stack membership, refused status and code stay checked. |
| `tests/test_reader_rd3a_search.py`, `test_reader_rd3_fix_backend.py` | No-vector passage reason, pad word-matching reason, and failed passage and note matching messages. Per-group statuses and job handling stay checked. |
| `tests/test_reader_rd6a_goal_lens.py`, `test_reader_rd6a_goal_lens_core.py` | Main-reading reason in both layers, both deeper-level reasons, and the learner’s requested cold-check reason. Level, treatment and override checks stay. |
| `tests/test_teacher_te1_review_fixes.py` | Neutral close notice offers a new lesson. Existing protection reason, history and no-additional-call assertions stay. |
| `scripts/desk_harness/run.py` | Similar Match result tag, submitted-writing explanation, Python cell row, moved-pad stub, main callout, shelf main-reading count, neutral reason heading, deeper-level wording, and paper callout. UI queries, interaction and geometry checks otherwise stay. |

### Python test files

The final command uses `pytest -q -n 1 -p no:cacheprovider` with the following explicit files in the checkout’s isolated Python environment.

```text
tests/test_reader_rd0_protocol.py
tests/test_reader_rd0_rpcs.py
tests/test_reader_rd0_reads.py
tests/test_reader_rd3a_search.py
tests/test_reader_rd3_fix_backend.py
tests/test_reader_rd4_carried_and_proposals.py
tests/test_reader_rd4_rpcs.py
tests/test_reader_rd4_submission.py
tests/test_reader_rd6a_goal_lens.py
tests/test_reader_rd6a_goal_lens_core.py
tests/test_reader_rd6_fix_protection.py
tests/test_reader_rd6_fix_reads.py
tests/test_reader_rd8a_ink.py
tests/test_reader_rd8a_rpcs.py
tests/test_reader_rd8a_transcribe.py
tests/test_reader_rd8a_fix_rpcs.py
tests/test_reader_rd9a_lesson_windows.py
tests/test_reader_rd9a_fix.py
tests/test_reader_rd10_video.py
tests/test_reader_rd10_fix_protection.py
tests/test_reader_rd10_fix_sweep.py
tests/test_reader_rw5d_p4b_teacher_visuals.py
tests/test_video_chapters_no_replace.py
tests/test_teacher_te1_lesson.py
tests/test_teacher_te1_review_fixes.py
tests/test_teacher_te2_sidecar.py
tests/test_notebook_rpcs.py
tests/test_notebook_pad_cells.py
tests/test_desktop_rpc_contract.py
tests/test_identity_pins.py
tests/test_menu_promoted_rows.py
tests/test_menu_protected_material.py
tests/test_pad_stale_edits_stacks_and_passage_reads.py
tests/test_notebook_lessons.py
```

Typecheck and Ruff passed. The frontend suite, with the existing lesson tests in `LessonScreen.test.tsx`, reported 57 files and 656 tests passed. The Python run reported 865 passed, including the desktop RPC contract and identity pins. A diff check verified 101 edited-line Python error-code literals against the base. Browser harness execution and visual comparison are pending with the orchestrator.
