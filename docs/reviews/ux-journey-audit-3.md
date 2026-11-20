# UX journey audit, third part

The third part of the UX journey audit. The first part (criteria, inventory, first wave, twelve fix stages) is `docs/reviews/ux-journey-audit.md`; the second (thirteen walks, UX-13 to UX-27, F20 to F38, P11 to P18, the stages re-ranked) is `docs/reviews/ux-journey-audit-2.md`; the criteria ids are in `docs/reviews/ux-journey-audit-criteria.md`. Since the second part, the waiting indicators, two groups of broken controls (UX-14 to UX-27) and a chain of fifteen fixes to a first-day learner's first questions landed, and thirteen more walks were made. Written 2026-11-20 against main `1f9c8de1b3`, on branch `docs/ux-journey-audit`.

The centre of this part is the first-day chain (section 2): ten walks of one person adding one web chapter on the owner's real model route, each made after the fix the previous one produced. The first nine got no practice question or got stuck after one; the tenth answered three questions in a row, the first 8 min 50 s after adding the chapter.

## 0. How to read this

**The walks.** As before: an agent playing one person, given only that person's goals and the screen (`docs/reviews/ux-walk-harness.md`). They are private, under `fixtures-local/ux-walks/<walk>/`, cited as "walk #step". Times written "m:ss" are minutes from the moment the chapter was added (the vault's own record of the source), read from the vault's `ingest_jobs`, `model_call_receipts`, `reader_section_progress` and `practice_attempts` with read-only connections: counts and times only.

| Walk | Person | Ran on | Start | Models | Steps | How it ended |
|---|---|---|---|---|---|---|
| firstq-1 | first-year student, one evening of about forty minutes, waits up to about five minutes for questions | main `ece7907885` (by start time) | empty install | live | 61 | **gave up**: no question; Today asked to finish a section already finished (#47-59) |
| firstq-2 | the same | main `4566d93ae9` (by start time; the vault holds UX-31's `waiting_for_build` stamp) | empty install | live | 58 | **gave up** at its five-minute allowance: "1 of 2 steps done" throughout |
| firstq-3 | first-year student, the whole evening, checks Today every minute for up to fifteen minutes (the patient persona, from here on) | main `4566d93ae9` (by start time) | empty install | live | 82 | **gave up** after 15 waits: "Couldn't write the questions…", then writing again |
| firstq-4 | the patient persona | main `5a7728283a` | empty install | live | 90 | **gave up** after 15 waits: "Writing questions…", nothing offered |
| firstq-5 | the same | main `1119b97462` | empty install | live | 101 | **gave up**: "Couldn't get … ready for questions, after trying twice" at 17:55 |
| firstq-6 | the same | main `9cf7b07914` | empty install | live | 106 | **gave up** after 15 waits: "1 of 2 steps done" for 19 minutes |
| firstq-7 | the same | the UX-41 candidate | empty install | live | 79 | **gave up**: "Couldn't write the questions…", Try again twice with no visible change |
| firstq-8 | the same | the UX-42 candidate | empty install | live | 96 | **gave up** after 15 waits: Today asked to finish a finished section |
| firstq-9 | the same | main `0b1fcf13da` | empty install | live | 105 | **done, with detours**: first answer at 8:18; Begin repeated a question; a follow-up failed |
| firstq-10 | the same | main `1f9c8de1b3` | empty install | live | 87 | **done**: three answers in a row from 8:50; stopped looking for tomorrow |
| student-3 | exam student, midterm in three weeks (re-walk of student-2) | main `ece7907885` (by start time) | empty install | live | 99 | done or given up, goal by goal; no Today question |
| retainer-3 | curious reader, ten minutes a day (re-walk of retainer-2) | main `ece7907885` (by start time) | fresh vault | live | 84 | done or given up, goal by goal |
| expert-2 | data scientist, wants to test out (re-walk of expert-1) | main `ece7907885` (by start time) | empty install | live | 89 | gave up on placement and daily practice; Ask judged expert-grade |

"Ran on" for firstq-4 to firstq-10 is the orchestrator's record; for the others it is main at the walk's start time, read from the branch's history. firstq-1 and firstq-2 had the forty-minute brief; firstq-3 onward the patient brief (the two differ only in how long to wait). Every walk was on the owner's ChatGPT plan route for model work.

**What is the harness, not LearnLoop** (checked against the fidelity table):

- The Decider and embedding routes were unreachable in all thirteen walks (`routes.json`: nine routes "unreachable", one "unset"). So the Reader's intent box always fell back ("LearnLoop's model couldn't choose, so this asks", student-3 #38), topic matching in the goal box ran without embeddings, and the tutor's offers under an answer could find nothing ("nothing in your practice or books fits this yet" under an answer that cites both books, retainer-3 #46). Findings that may be an effect of this are marked.
- **The text view shows TeX where the window draws math.** The persona's text includes KaTeX's hidden TeX annotation, so five personas first said the equations were "backslashes" or "dollar signs" (firstq-9, firstq-10 #8, student-3 #7, expert-2, retainer-3 #32) and then corrected themselves from the screenshot (firstq-10 #10: "the equations actually look normal"). The screenshots show drawn display math with bold vectors (firstq-10 #15, student-3 #66). Not a finding.
- The first file choice "did not work" in most walks: the walker typed a folder prefix into the harness's chooser. Not a finding.
- Fixed one-minute waits: the patient persona looked at Today every 60 s, so "first seen" times are up to a minute after the state changed. The vault's times are given beside them.
- The ChatGPT plan was overloaded twice: firstq-1's first synthesis request (retried at once, unseen) and student-3's quick check at 3:27. What the screen did about the second is LearnLoop's (UX-53).
- firstq-3's greeting changed from "Friday night" to "Friday morning" during the walk (#49): the walk crossed 5 a.m. Not a finding.
- "Undo this article 's questions" (firstq-10 #84): the harness joins the label's text nodes with a space. Not a finding.

---

## 1. Before and after: what landed since the second part

Verdicts as before: **fixed** (as seen by a person), **partly**, **not reached**, **still there**, **worse** (each "worse" is also a defect in section 5).

### 1.1 The fixes and what they claimed

| Landing | What it claimed | Evidence | Verdict |
|---|---|---|---|
| Waiting you can see (`ux-waiting.md`) | One waiting line on Today → question, question → feedback, and where a model writes while the learner watches | "◐ Checking your answer… / This can take a minute." on every Submit (firstq-9 #62, firstq-10 #64, #70, #75); "◐ Opening your feedback…" and "◐ Looking into what happened here…" on a partly right answer (firstq-9 #90-91); "◐ Adding more to today…" (expert-2 #42). Begin and Next opened in 2 to 3 s, too short for the line to be captured | **fixed** for the waits between screens; the build's long wait is section 2.3 |
| UX-13: output ceilings, one automatic retry | A first document's build no longer fails on its output budget; a failed model step is retried once on its own | Every inventory window that ran in the thirteen walks completed at its first try (60 to 69 s); firstq-1's overloaded synthesis request was retried at once and the learner never saw it; firstq-5's "after trying twice" is the retry stopping honestly | **fixed** |
| P11, first questions on Today, and UX-29's "Done with this section" | Today offers a book's first questions with Begin, or says what must happen first | firstq-9 #56, firstq-10 #58: "3 questions from what you read in … are ready. More are being written (1 of 8 topics done). Begin ↵"; Begin opened a question (firstq-9 #58, firstq-10 #60) | **fixed** (F20 closed by firstq-9 and firstq-10) |
| UX-31: a section finished before its book is ready | It waits for the book and gets its questions once | Sections finished at 1:25 to 2:43, before their builds ended, got their questions in firstq-3, -4, -7, -9, -10 (each section stamped with the writing batch); Today said "Your questions from what you read will be written as soon as … is ready" (firstq-10 #46) | **fixed** |
| UX-11: a web page keeps its equations and titles | Displays drawn, headings' words as titles, no furniture | The chapter read as one section "Section 7.1 Symmetric matrices and variance" of 135 passages (firstq-4 to -10), its displays and matrices drawn (firstq-10 #15). Its figures are still dropped (UX-35) and a definition still splits at its emphasis (UX-34, visible in firstq-10 #15) | **fixed**; UX-34 and UX-35 now seen by people |
| UX-33: a section's questions in parts | One saved call per topic | Topic calls of 89 to 143 s each (firstq-4, -9, -10); none hit a deadline | **fixed** |
| UX-37: first questions first | A topic's questions apply as soon as they are ready | firstq-9 and firstq-10 were offered topic 1's three questions while topics 2 to 8 were written | **fixed** |
| Question writing you can follow, and UX-38 | Today shows how far the writing is | "· 0 of 8 topics done" (firstq-10 #54), "(1 of 8 topics done)", "(2 of 8 topics done)" (#78); "The first time, this can take several minutes." after five seconds (firstq-6, -7, -9, -10) | **fixed** |
| UX-39: a live stream is not cut at 480 s | A background call still delivering output runs on, to a 20-minute ceiling | firstq-6: the build's call streamed for 15 minutes and was then cut at the ceiling, and the learner saw "1 of 2 steps done" for 19 minutes | **partly**: what it fixed was real; the call it let run was a runaway (UX-41) |
| UX-40: questions apply, held is not failed | The prompt line no longer steers every question to review | All 9 questions of firstq-9 and all 6 of firstq-10 auto-applied; none held | **fixed** as seen |
| UX-41: runaway whitespace cut and retried | The synthesis prompt agrees with its schema; a runaway is cut at 2,000 spaces | firstq-7, -9, -10 builds took 221 to 242 s and completed; the guard never fired in a walk | **fixed** as seen |
| UX-42: a create without ids keeps its questions | LearnLoop names an unnamed create | No topic refused in firstq-9 or firstq-10 (firstq-7's refusal was the evidence) | **fixed** as seen |
| UX-43: an empty first build is not finished | Asked again once; still empty says so with Try again | firstq-9 and firstq-10 builds held topics; no empty answer occurred | **not reached** (the ordinary path was unchanged: one synthesis receipt each) |
| UX-44: Begin and Next after the first answers | Today counts and Begin opens only what can be asked now; Next goes on | firstq-10: "next: Recognize and verify eigenpairs" under Next and the next question in 2.6 s (#65-67, #73); Today then counted only the second topic's three (#78); the rating row's × reads "hide easy · about right · hard for this session" (#60) | **fixed** |
| UX-45: an empty follow-up is asked again once | A follow-up that ignores its contract is re-asked | firstq-10 answered nothing wrong | **not reached** |
| Broken controls, second round, group A (UX-14, 16 to 22, 27) | See the record | UX-18 exactly as written (expert-2 #59, #61). UX-14, UX-16, UX-19 to UX-22, UX-27: no walk reached a lesson, a plan with blocks, the workbench or a check screen. UX-17: student-3 #32 (no topics yet) kept the old sentence, as the record intends | **UX-18 fixed**; the rest **not reached** |
| Broken controls, second round, group B (UX-15, 23 to 26) | See the record | UX-15: the app's tabs stayed on screen in every observation of all thirteen walks (the harness's browser, not WebKitGTK). UX-25: displays drawn (firstq-10 #15). UX-26: the "ASKING ABOUT YOUR SELECTION" chip draws each formula once (student-3 #66). UX-24: Contents in words for new reads; Ask's source chips still show slugs (UX-56). UX-23: no phone walk | **UX-15, UX-25, UX-26 fixed** in the walks' browser; **UX-24 partly**; UX-23 **not reached** |
| UX-10 (owner's ruling still open) | — | The fresh-vault route asked for the OK (retainer-3 #48-61); the ten empty-install walks never did | **still open, still inconsistent by route** |

### 1.2 "What a walk must check", line by line

**Waiting you can see** (`ux-waiting.md`)

| Line | Answer |
|---|---|
| Today → question: Begin says "opening…" and "◐ Choosing what's next…"; a list row "Opening the question…"; Practise for this goal "Finding a question for this goal…" | Begin opened the question in 2.9 s (firstq-9 #58, firstq-10 #60); no line was captured, as expected under 3 s. A list row: firstq-9 #86 (2.3 s), none captured. Practise for this goal: no question existed (student-3 #32, expert-2 #17), so the finding line was not reached |
| Submit: "◐ Checking your answer…", then "This can take a minute."; "Opening your feedback…"; Next "Choosing what's next…" | Yes, both lines on every Submit (seven Submits in firstq-9 and firstq-10); "◐ Opening your feedback…" on a partly right answer, seen about 40 s after Submit (firstq-9 #90); Next in 2.6 s, no line captured |
| Ask panel "◐ Writing a reply…"; the Reader's AskRail line unchanged and still | The Reader's line, unchanged: "◐ looking in your books, then writing an answer … · cancel" (student-3 #38, firstq-5 #61, firstq-6 #65, retainer-3 #43), 10 to 23 s of model time. The practice Ask panel: not reached |
| Lessons: "The teacher is writing…" | Not reached |
| Hints: "Writing a hint for your work…" | Not reached |
| Goal details: "Working out where this goal is heading…" | Not captured: student-3 opened the details in 1.1 s (#31) |
| The phone, all three cases | Not reached |
| Reduced motion | Not reached |

**Broken controls, second round, group A** (`ux-fix-round-2a.md`)

| Line | Answer |
|---|---|
| UX-14: Close keeps the lesson; "Continue your lesson on …" on Today | Not reached |
| UX-16: "The plan stopped here, but there's more for today…"; never "Nothing else is needed today." with questions on the list | Not reached: no first-day plan had blocks. Today's empty plan said "Nothing planned for today." throughout, including above the offer of questions (UX-52) |
| UX-16, returner: "Catch-up done." | Not reached |
| UX-17: "This goal has 3 topics, but no questions on them yet…" after "make it" | Not reached in that form: expert-2's goal had three topics "not in your library yet" (#12) and no questions; its details were not opened. student-3's goal with no topics kept "None of the topics in your books is part of it so far: add or read a book that covers it" (#32) while the chapter that covers it was being got ready (F30, still) |
| UX-18: "already marked as known…"; "Nothing to ask yet on …"; a topic with questions opens the check | The first two word for word (expert-2 #59, #61). The third: not reached (no topic had questions) |
| UX-19 in the real window | Not reached |
| UX-20: the failed hint line's words | Not reached |
| UX-21: Begin on a lesson offer opens the offer | Not reached |
| UX-22: a sent lesson reply stays | Not reached |
| UX-27: place tabs leave a check | Not reached (expert-2 never opened a check: nothing to ask) |

**Broken controls, second round, group B** (`ux-fix-round-2b.md`)

| Line | Answer |
|---|---|
| UX-15: after "ask follow-up" and an answer, the top bar and tabs stay | Yes in the harness's browser: student-3 (#40-46, #72-79), expert-2 (#29-38) and retainer-3 (#43-47) kept the tabs in every observation. The first general scroll still moved the chapter, not the answer (student-3 #40-44, expert-2 report; F26). The real WebKitGTK window: not checked |
| UX-23: no code under the phone's score | Not reached |
| UX-24: the elevator article's sections in words, in Contents, the path, side by side, the phone | retainer-3's article came from the fresh-vault fixture, read before UX-11: Contents and side by side were not opened. Ask's source chips under an answer showed "· modeling-the-elevator-problem" and, for the chapter, "· root" (retainer-3 #46): UX-56 |
| UX-25: the chapter's displays drawn | Yes (firstq-10 #15; student-3 #66 on the older extraction) |
| UX-26: the chip and "§ from the book" show each formula once | The chip: yes (student-3 #66, drawn once). Selecting from the middle of a formula, a saved exchange, the phone: not reached |

**First questions arrive: Today** (`ux-first-questions-today.md`)

| Line | Answer |
|---|---|
| student-2: "◐ Getting … ready for questions · 0 of 2 steps done", then "1 of 2" | Yes ("0 of 2", retainer-3 #61; "1 of 2", every firstq walk). With nothing finished: "Your first questions come when you finish a section of …: finish its quick check, or press Done with this section at its end." (firstq-1 #47, firstq-8 #45, both on a finished section: UX-31 and UX-43, both since fixed). After two failures: "Couldn't get … ready for questions, after trying twice. Try again, or keep reading: nothing is lost." (firstq-5 #93). Then "◐ Writing questions from what you read in …", then the offer with Begin, and Begin opens a question: yes (firstq-9, firstq-10) |
| expert-1: never "Everything you've read has its questions"; Practise for this goal says the rule after its lead | Yes: "Nothing for this goal is ready to practise yet: getting … ready for questions · 0 of 2 steps done. Questions come as you finish sections. Keep reading meanwhile." (expert-2 #17) |
| retainer-2: "…waiting for your OK" until Give your OK, then the waiting line | Yes: "Questions for … and 2 more are waiting for your OK." (retainer-3 #48), Give your OK → the sheet → OK (#59-61), then "0 of 2 steps done" (#61). Whether the person finds "done for now": retainer-3 never finished a section |
| project-1, notes-1 | Not walked |
| The phone | Not walked |

**UX-31: a section finished before its book is ready** (`ux31-section-done-before-build.md`)

| Line | Answer |
|---|---|
| 1. "Done with this section" while the book is got ready: "◐ Your questions from this section will be written as soon as … is ready. They'll be on Today." | Yes, with the button (firstq-2 #33). When the section is finished by the quick check's "done for now" (firstq-3 to firstq-10, the way every patient persona finished it), the Reader says "✓ Done with this section." instead (firstq-10 #36): the waiting sentence appears only on Today |
| 2. Today while the book is got ready: "Your questions from what you read will be written as soon as … is ready. Keep reading meanwhile." Never "finish a section" | Yes (firstq-10 #46); never "finish a section" in firstq-2 to firstq-10 except firstq-8, the empty build (UX-43) |
| 3. No press: "◐ Writing questions…", then the offer; Begin opens one | Yes (firstq-9 #53-58, firstq-10 #54-60) |
| 4. "Build questions for the whole article at once": the shelf's sentence, no "Chapters found" | The sentence, yes (firstq-8 #58); there it was wrong, because the build had no topics (UX-43, since fixed). No other walk pressed it: three said they left it alone because questions were already being written (firstq-2, firstq-5, firstq-6) |
| 5. The phone | Not reached |

**UX-11: web pages keep their equations** (`ux11-html-extraction.md`)

| Line | Answer |
|---|---|
| The chapter's activities and exercises followed by their matrices, displays drawn, no raw `\begin` | Yes in the screenshots read (firstq-10 #15). The phone: not reached |
| The first build completes with the bigger text | Yes in firstq-4, -7, -9, -10 (inventory 62 to 69 s, synthesis 221 to 244 s). firstq-5 and firstq-6 failed on the call's deadline and its runaway (UX-39, UX-41), not on a size refusal; no step was refused for size |
| A newly added elevator article's sections in words | Not reached (retainer-3 ran before UX-11 landed) |
| A page read before: "This page's text is missing N equations · Read it again" | Not reached |
| Ask, quick checks and questions read the displays | The quick check asked about the factorization the displays carry (firstq-9, firstq-10); a written question named its matrices (firstq-9 #86). Partly |

**Question writing you can follow** (`ux-first-questions-progress.md`)

| Line | Answer |
|---|---|
| 1. "◐ Getting … · 0 of 2 steps done", after five seconds "The first time, this can take several minutes."; it stays through the build | Yes (firstq-6 #44, firstq-9 #43, firstq-10 #46), and it stayed. It also stayed for 19 minutes over a runaway call (firstq-6) |
| 2. "◐ Writing questions from what you read in … · 0 of 8 topics done"; the count goes up with no press | Yes (firstq-10 #54 → #58 → #78: 0, 1, 2 of 8), one topic every 2 to 2.5 minutes (authoring 101 to 128 s, then about 20 s of checks) |
| 3. "N questions from … are ready. More are being written (1 of 8 topics done)." with Begin | Yes (firstq-9 #56, firstq-10 #58) |
| 4. Begin opens one; later Today shows the current count | Yes; firstq-9's later count included answered questions (UX-44, fixed: firstq-10 #78) |
| 5. A topic fails: "Not every topic's questions could be written." under the offer, no Try again while writing | Not reached with an offer. With no offer yet (firstq-7, topic 1 refused, the rest still being written), Today said "Couldn't write the questions from what you read in …. Try again, or keep reading: nothing is lost." with a Try again that changed nothing (#60-70): UX-47 |
| 6. The phone | Not reached |
| 7. A second build: "usually about N min" | Not reached |

**UX-43: an empty first build** (`ux43-empty-build.md`)

| Line | Answer |
|---|---|
| 1. Ordinary build unchanged: one synthesis receipt, no "asked again", Today's usual lines, never "found no topics" | Yes (firstq-10: one `source_set_synthesis`, the build's result without the asked-again mark; firstq-9 the same) |
| 2 to 5. An empty answer and what follows | Not reached (it cannot be ordered from the live model) |

**UX-44: Begin and Next after the first answers** (`ux44-begin-after-first-answers.md`)

| Line | Answer |
|---|---|
| 1. "3 questions … are ready. More are being written (1 of 8 topics done)." Begin opens one | Yes (firstq-10 #58-60) |
| 2. Feedback's "next: *the topic*"; Next opens the second question at once | Yes (firstq-10 #65 "next: Recognize and verify eigenpairs"; #67 the second question in 2.6 s) |
| 3. After the second answer: Next names the next topic, or Today says the writing line with no Begin | firstq-10's second answer was followed by the third question of the same topic (#73); the reserved-for-later branch did not occur |
| 4. The next topic applies: Today counts only the new ones; Begin opens a question never answered | The count: yes (firstq-10 #78: "3 questions … (2 of 8 topics done)" after three answered). Begin was not pressed again |
| 5. "Nothing from … is up today…" | Not reached |
| 6. The full list still "coming back later today"; does the person pick the reserved one | firstq-10 did not open the list. On `0b1fcf13da`, firstq-9 read "coming back later today" for all six, "even the ones I got right" (#85; UX-44c, still open) |
| 7. The rating row's × reads "hide easy · about right · hard for this session" | Yes (firstq-10 #60) |
| 8. The phone | Not reached |

**Records without a "what a walk must check" list.** UX-13 (`ux13-first-questions.md`), UX-33, UX-37, UX-39, UX-40, UX-41, UX-42 and UX-45 end with what they did not verify instead. Their learner-visible claims are answered in 1.1. Of their open lines: UX-37's "combined Today state" (questions offered while more are written and a topic failed) was built by the progress step and not reached; UX-39's "no live-route success is claimed" became firstq-6's runaway; UX-40's "whether the real model follows the new line": yes, 15 of 15 questions auto-applied in firstq-9 and firstq-10; UX-41's guard "not triggered on the real route": still not triggered; UX-42 and UX-45's real-route behaviour: UX-42 not needed in firstq-9 or firstq-10 as far as the screen shows, UX-45 not reached.

**Anything a fix made confusing:** UX-31's waiting sentence shows only for the button, not for the quick check's "done for now" (section 2.2, F41); UX-39 let a runaway call hold "1 of 2 steps done" for 19 minutes (fixed by UX-41).

---

## 2. The first-day chain

### 2.1 The table

One person, one web chapter (the sample chapter of eight topics), a fresh install, the live route. "Readable" is the first screen with the chapter's text; "build" is the end of the book's first build (inventory, then synthesis); "offered" is the first look at Today that showed questions with Begin (the vault time the questions applied in brackets); "answer" is the first submitted practice answer.

| Walk | Ran on | Readable | Section finished | Build | Offered | First answer | Where it stopped, and why | The fix it produced |
|---|---|---|---|---|---|---|---|---|
| firstq-1 | `ece7907885` | 0:05 | 1:45 (the button; the quick check's compare was out of reach, #22-28) | 4:30 | — | — | The section was finished while the build ran and stamped "nothing needed"; Today then asked to finish it (#47); the whole-article press found nothing to do (#52-54) | UX-31 |
| firstq-2 | `4566d93ae9` | 0:05 | 2:13 (the button) | not by 7:51 (the build's synthesis call still running after 6 min 46 s) | — | — | "1 of 2 steps done" through five waits; stopped at its five-minute allowance | none of its own; the same long call is what firstq-5 and firstq-6 measured |
| firstq-3 | `4566d93ae9` | 0:25 | 1:25 (done for now) | 4:38 | — | — | All six topics' questions asked in one call, cut at 480 s (4:39-12:39); "Couldn't write the questions…" at 13:10; Try again writing again at 20:14 | UX-33 |
| firstq-4 | `5a7728283a` | 0:05 | 2:03 (done for now) | 5:26 | — | — | Topics written one call each, but nothing applied until all were in: 4 of 8 saved at 20:09, one refused as invalid; Today "◐ Writing questions from what you read…" with no count for 14 minutes | UX-37, and the progress line (UX-38) |
| firstq-5 | `1119b97462` | 0:05 | 2:31 (done for now) | failed 17:06 | — | — | The build's synthesis call cut at 480 s twice (1:06-9:06, 9:06-17:06); Today "1 of 2 steps done" for 15 minutes, then "Couldn't get … ready for questions, after trying twice" (#93) | UX-39 |
| firstq-6 | `9cf7b07914` | 0:10 | 1:37 (done for now) | failed 21:08 | — | — | The call streamed for 15 minutes (whitespace without end), its retry cut at the 20-minute ceiling; Today "1 of 2 steps done" and "The first time, this can take several minutes." from 2:09 to the end at 21:51 | UX-41 |
| firstq-7 | UX-41 candidate | 0:06 | 2:05 (done for now) | 5:13 | — | — | Topic 1's questions refused because the model left their ids empty (8:22); Today said "Couldn't write the questions…" while topics 2 to 7 were still being written; Try again twice did nothing visible; gave up at 11:01 | UX-42 (and UX-47 here) |
| firstq-8 | UX-42 candidate | 0:06 | 2:43 (done for now) | 2:07, **no topic** | — | — | The build came back with no topic in 23 s and was accepted; the section was stamped "nothing needed"; Today asked to finish the finished section for 15 minutes | UX-43 |
| firstq-9 | `0b1fcf13da` | 0:09 | 1:33 (done for now) | 5:29 | 7:45 (applied 7:12-7:34) | **8:18** | Next after feedback went to Today; Begin reopened a question answered right minutes before (#73, #76); a partly right answer's follow-up came back empty and failed ("Couldn't prepare a question on this. It's noted for later.", #93) | UX-44, UX-45 |
| firstq-10 | `1f9c8de1b3` | 0:06 | 2:06 (done for now) | 5:33 | 8:15 (applied 7:15-7:34) | **8:50** | Three right answers in a row (8:50, 9:34, 10:22); stopped at 11:10 by choice, after looking for tomorrow in three places | — (UX-47 to UX-57 in this part) |

### 2.2 The narrative

The reading was never the problem. In all ten walks the chapter was readable within 5 to 25 seconds, the reading guide offered a depth and a path, and the quick check (written in 4 to 6 s) asked a fair question about the section's main theorem. Every patient persona finished the section within three minutes of adding it, by the quick check's "done for now", usually believing it only closed the check.

Everything after that was the build and the questions, and each walk found the next wall. First the section finished before the book was built was forgotten (firstq-1, UX-31). Then the book's one long synthesis call ran for minutes with "1 of 2 steps done" unchanged (firstq-2), the section's questions for six topics were asked in one call that a 480 s deadline cut (firstq-3, UX-33), topics written one by one were held until all were in (firstq-4, UX-37), the build's own call was cut at 480 s twice (firstq-5, UX-39), and once allowed to run it ran away into whitespace for 15 minutes (firstq-6, UX-41). With the build fixed, a topic whose ids the model left empty was refused whole (firstq-7, UX-42), and a build with no topics was accepted as finished (firstq-8, UX-43). Each of these was a backend failure; in each the screen either held one line for a quarter of an hour or said something untrue (finish a finished section). Eight of the ten personas gave up.

firstq-9 was the first to get practice: three questions from the first topic at 7:45, its first answer at 8:18. It then met the screen's half: Today counted questions already answered, Begin reopened one, Next went back to Today, and a partly right answer's follow-up question came back empty and failed (UX-44, UX-45). firstq-10, on main as it stands, answered three questions in a row with Next, each graded in about 15 s with ticks per rubric line, and saw the second topic's questions arrive while it answered.

What the chain did not change: the section is finished by a control that says "done for now"; the learner waits about five minutes with one line that moves twice; the session ends with no word on tomorrow; the chapter's figures are not in the reading. These are the findings the patient persona repeats (section 6).

### 2.3 The first evening as it is now

From firstq-10 (main `1f9c8de1b3`) and, for a partly right answer, firstq-9 (`0b1fcf13da`; its follow-up failure has since been fixed by UX-45 and was not walked again). Judged against the owner's request of 2026-11-19: loading indicators wherever the wait between screens is long, and while models write.

| Time | The learner | The screen | Judged |
|---|---|---|---|
| 0:00 | Chooses the chapter in the empty Library | "◐ Getting this article ready / Highlights, notes, Ask and questions on each section — available in a minute or two, when the text is ready. / It opens here as soon as it is ready." | Good: says what, how long, and that it opens by itself |
| 0:06 | Reads | The chapter, drawn; "Reading guide" asks how deep ("learn to use it"); path "about 20 min of reading" | Good |
| 1:29-1:34 | Reads on | Guide: "◐ writing a quick check for this section…", then "A quick check on this section is ready, just below." with its controls below the guide's fold ("More below in Reading guide (scroll down)", #29) | The wait is said; the check is out of view (F42) |
| 1:51-2:08 | Answers the check, compares, presses "done for now" | "✓ Done with this section." and "✓ quick check complete — keep going."; the guide's bar at 100 %, the page's at 76 % | The section is finished by a control that says "for now" (F41) |
| 2:35 | Goes to Today | "Nothing planned for today." / "◐ Getting “…” ready for questions · 1 of 2 steps done [Continue reading]" / after 5 s "The first time, this can take several minutes." / "Your questions from what you read will be written as soon as “…” is ready. Keep reading meanwhile." | An indicator and an honest sentence; but the heading says nothing is planned (UX-52) and "Keep reading" is offered to someone at the end |
| 2:35-5:33 | Waits, checking every minute; rereads | The same line, unchanged for three minutes (#47-53) | **The longest silent wait of the evening**: the mark turns, nothing moves; "I cannot tell whether it has moved at all" (firstq-9 #53). F39 |
| 5:33 (seen 6:04) | Waits | "◐ Writing questions from what you read in “…” · 0 of 8 topics done [Continue reading]" | Moves to a count: "reassuring progress" (#55) |
| 6:04-7:34 | Waits | "0 of 8 topics done", unchanged for about two minutes | A count that does not move within a topic |
| ~7:34 (seen 8:15) | Waits | "3 questions from what you read in “…” are ready. More are being written (1 of 8 topics done). [Begin ↵]" above "[Keep going ↵]", still under "Nothing planned for today." | The offer arrives with no press; two buttons show ↵ (UX-52) |
| 8:23 | Begin | The question in 2.9 s, topic named at the top | Short enough |
| 8:34-8:50 | Submits | "◐ Checking your answer… / This can take a minute." (disabled controls), then "Right", "◇ graded by AI", the full answer, a tick per rubric line, "next: Recognize and verify eigenpairs" | Meets the owner's request |
| 9:12, 10:01 | Next | The next question in 2.6 s; the third feedback names the next topic, from the second topic just written | Good |
| (firstq-9, 10:23-11:47) | Submits a partly right answer | "◐ Checking your answer…", then "◐ Opening your feedback…" (seen about 40 s after Submit), then "◐ Looking into what happened here…" (seen at about 58 s), then the feedback with ✓ and ✗ per line and "Possible causes … This is optional, and it doesn't change your grade." (about 80 s after Submit) | Every stage of an 80-second wait named. Then "Couldn't prepare a question on this. It's noted for later." (since fixed by UX-45) and a "Redo the part you missed" whose "What to fix" is written to the system (UX-48) |
| 10:45 | Back to Today | "3 questions … are ready. More are being written (2 of 8 topics done). [Begin ↵]", "1 day" bare under the buttons | Counts only new questions (UX-44 fixed). "1 day" is the streak, unexplained (F38, again) |
| 10:49 | "Done for today" | "2 minutes this session · 3 questions / Since last time: ● Recognize and verify eigenpairs (on your own) [Done ↵]" | What moved, not what comes next (F40). In firstq-9 the same line said "(on your own)" for a topic finished with help (UX-49) |
| 10:55-11:10 | Looks for tomorrow in Progress and the Library | Progress: "knowledge field", "goal overlay", "learning objects", "mastery estimates", "open error events"; Library card: "Questions for this article come up as you read" and "Build questions for the whole article at once" | No tomorrow anywhere (F40); the card's line ignores the questions just answered (UX-30) |

**Against the owner's request.** Between screens the request is met: Submit, the feedback's read and the look into a miss each show a named, turning line within the first second, and Begin and Next take under three seconds. Where models write while the learner watches in the Reader (Ask, the quick check), the still lines remain and are understood. The gap is the build: about five minutes on the good runs (and 15 to 20 minutes on the failing ones, firstq-5 and firstq-6) shown by a line that turns but says the same thing for three minutes, then a count that stays at 0 for two. The indicator cannot tell a slow call from a stuck one, and the learner cannot either: "a minute at the same count felt uncertain" (firstq-10 report), "I could not distinguish slow progress from being stuck" (firstq-3 report). F39 and P19.

---

## 3. The three re-walks

All three ran on main `ece7907885` (between 02:44 and 02:52 that night), before UX-31 and the rest of the chain. What later landings changed is said with each.

**student-3 (was student-2).** Better: the app's tabs never left the screen (student-2 ended on that, UX-15); Ask's quote drew each formula once (#66, UX-26); the past exam landed quietly as a past exam (#27). The same: the goal box said the chapter's own topics were "not in your library yet" (#14; F30, partly the unreachable embeddings and the build not finished); no question from Today in 99 steps; the only practice was two problems the person asked Ask to set and judge (#64-79), which counted for nothing (F44). Worse or new: reopening "learning this for something?" gave a blank form, and the second "make it" made a second goal for the same exam (#17-21); the quiz import waited behind the chapter's build and its card said "◐ Getting this PDF ready" for seven and a half minutes (#27, #92; UX-54); the quick check's writing failed on an overloaded plan and the guide said "◐ writing a quick check for this section…" until the person gave up, then only "Keep reading at your own pace." (#56-62, #96; UX-53); "Practise for this goal" seemed to do nothing (#32: its line probably rendered below the open goal details; not settled). Why no question: the build's synthesis call was still running at the walk's end (7 min 33 s; on main it is now bounded by UX-39 and UX-41), and the section was never finished (54 of 59 passages read; the quick check never came). On main the person would still be told to finish a section first: an exam student who reads part of a chapter and wants to practise is held to the as-you-read rule (F44).

**retainer-3 (was retainer-2).** The same: three highlights took about eighteen actions through a long action list (#10-27; F34); the chapter was one "Document" (#41; fixed for new reads by UX-11); Today named the OK with "and 2 more" and the OK sheet explained itself (#48, #59-61); Settings was "model names and technical paragraphs" (#54); no forecast or daily cap anywhere, and Ask, asked for "five questions or ten minutes a day", said it could change nothing (#77-78; F4, F40). Better: asking about both readings in Ask gave the comparison the person wanted, naming both sources (#42-47). New: the person's own sentence, typed into the note box after "note", was never saved: "✓ saved" showed above the empty box, and the only button that sends the note was already "highlighted ✓" (#24-27, #69-70; the vault's third highlight has no note; UX-50); the word typed into the selection box to find "highlight" was saved as the second highlight's note (#18-20, vault; UX-51); Ask's source chips named sections "· root" and "· modeling-the-elevator-problem" (#46; UX-56); adding the article the fixture already held made a second copy with the same content without a word (#6; UX-57). Side by side was not found this time (retainer-2 found it). Editing or deleting a highlight jumped to the passage (#71-72; part 2's harness note on buttons inside a clickable card may apply).

**expert-2 (was expert-1).** Better: "Check what I already know" now says why it asks nothing: "“Form covariance matrices and explain their structure” is already marked as known, so there's nothing to check now. Its first review is the check." and, after undoing the claim, "Nothing to ask yet on …: it has no question you haven't already seen. Nothing was changed." (#59, #61; UX-18 fixed). "Practise for this goal" said the rule after its lead (#17), not expert-1's "Everything you've read has its questions". Ask was again expert-grade (#78-88). The same: "I know this" was found only through Progress → a concept → its learning object (#56-64; F28); the goal box made a goal with "0 topics from your books · 3 not in your library yet" (#12; F30); Keep going planned "about 10 minutes of reading Document" (#42-44); the follow-up box was covered at the first try (#34; UX-55). Proposing a different topic order filed a change for review in Proposals and restored the map (#48-53; O9, two steps where one was expected). No practice question in 89 steps: the person read 14 of 59 passages and never finished a section, so the as-you-read rule gave nothing to answer (F44, with P14).

---

## 4. The scorecard, updated

Discover / Understand / Recover / Flow, as in the earlier parts. "Before" is the second part's "after"; "now" is this part. Rows these walks did not reach are left out; they stand as in the second part.

| Journey | Before | Now | Who | Still fails |
|---|---|---|---|---|
| First run: add a file and read | pass / pass / pass / pass | pass / pass / pass / pass | all thirteen | M3 (one section; figures dropped, UX-35) |
| **The first evening: finish a section, get its questions** (new row; was "Today on a new library") | pass / partial / partial / fail | pass / partial / partial / partial | firstq-1 to -10 | N-F (F39), I9 (F41), H1 (UX-52), N-K (UX-47) |
| Today on a new library (exam, expert, retainer) | pass / partial / partial / fail | pass / partial / partial / fail | student-3, expert-2, retainer-3 | J3 (as-you-read only, F44), F42 |
| Say the exam or goal | partial / fail / partial / pass | partial / fail / fail / pass | student-3, expert-2 | O9 (a second goal, no edit), O2 (F30) |
| Bring past exams | partial / partial / fail / — | partial / partial / fail / — | student-3 | J3, M10, H1 (UX-54) |
| Practice and feedback | pass / partial / partial / partial | pass / partial / pass / pass | firstq-9, firstq-10 | M7, O3 (UX-48, F38), O2 (UX-49) |
| Ask in the Reader | pass / partial / partial / partial | pass / partial / partial / partial | student-3, expert-2, retainer-3, firstq-5, firstq-6 | F26 (answer out of view), UX-55, UX-56 |
| Reader quick check | (inside Reader rows) | partial / partial / partial / partial | firstq-1 to -10, student-3 | N-D (F42), I9 (F41), H9 (UX-53) |
| Keeping things | partial / partial / partial / fail | partial / fail / partial / fail | retainer-3 | J10, I12 (UX-50, UX-51), M9 (F34) |
| The plan's size and load | fail / partial / fail / partial | fail / fail / fail / partial | all firstq, student-3, retainer-3 | I11, M4 (F40) |
| Session end | (part of the stop offer) | pass / partial / — / pass | firstq-9, firstq-10 | O2 (UX-49), M4 (F40) |
| Progress | pass / fail / — / — | pass / fail / — / — | firstq-9, firstq-10, student-3, expert-2, retainer-3 | O3, H2 |
| Settings | pass / fail / — / — | pass / fail / — / — | student-3, retainer-3 | J7, O3 |
| "I know this" and test out | fail / pass / partial / fail | fail / pass / pass / fail | expert-2 | N-D (F28), J3 (F44) |
| Cross-book | pass / pass / partial / pass | partial / pass / partial / pass | retainer-3 | side by side not found; comparison through Ask instead |

---

## 5. Defects

Severity as before: S1 the journey cannot be finished or the screen misleads about evidence; S2 it finishes only after a long detour or a guess; S3 friction. Each was checked against the fidelity table and the unreachable routes. Every cause was read on main `1f9c8de1b3`.

### 5.1 The list

| Id | Sev | What the person saw | Walk and step | Cause (where the code shows it) | Size |
|---|---|---|---|---|---|
| UX-47 | S2 | With no question offered yet, one topic of a section failed while the others were still being written: Today said "Couldn't write the questions from what you read in “…”. Try again, or keep reading: nothing is lost." Try again, pressed twice, changed nothing visible; the person gave up while the writing went on | firstq-7 #60-70 (the job still running, topic 2 started at 8:22) | `app/todayCause.ts`: `ORDER` ranks `section_failed` above `section_writing` (l.146-147), and a failed topic in the facts while the job runs is enough (l.263, 294-301). The progress record says no Try again while the rest are written only for the offer's line | S, frontend |
| UX-48 | S2 | "Redo the part you missed" says "What to fix:" and then a sentence written for the system, about eliciting the omitted computations before revealing the repaired trace; the person could not tell what to do | firstq-9 #95-96 | `diagnosis/guided_redo.py:350` sends the repair suggestion's `rationale` as `redo_instruction`; `PracticeScreen.tsx:1896` and `:1926` print it as "What to fix" | S (show the failed rubric lines instead), M (a learner-facing instruction) |
| UX-49 | S2 | The session end said "● Construct a diagonalization from an eigenvector basis (on your own)" after a partly right answer on the person's own and a redo marked "practice with help"; the person read it as contradicting the redo | firstq-9 #102 and report | `handlers/sessions.py` `_session_topics`: a topic is `on_your_own` if any own answer in the session earned credit (here the partly right one's correct parts), and later help is not said; `SessionFinishHud.tsx:141-143` shows one mark per topic | S |
| UX-50 | S2 | After "note" on a selection, the Notes rail shows "✓ saved · choose another action or select another passage" above an empty note box; what the person types there is never saved, because the only button that sends it already reads "highlighted ✓" and is disabled | retainer-3 #24-27, #69-70 (the vault's third highlight has no note) | `screens/reader/NotesRail.tsx:236-248`: the note `textarea` is sent only by `captureHighlight`, disabled once `selectionActions` holds "highlight" | S, frontend |
| UX-51 | S3 | The word typed into the selection box ("What do you want to do with this?") to find the "highlight" action was saved as that highlight's note, and showed later as a note on the passage | retainer-3 #18-20 (vault: the second highlight's note is exactly that word) | `ReaderScreen.tsx:3276-3282`: the box's text goes to `captureHighlight(text, …)` as the learner's note for a highlight chosen from it | S, frontend |
| UX-52 | S3 | Today's heading reads "Nothing planned for today." above "3 questions … are ready… [Begin ↵]" and "[Keep going ↵]"; two buttons show ↵ (Enter is Begin's); the person read the heading as "my reading produced no work", and it stayed after practice | firstq-10 #58, #78 and report; firstq-9 #56, #101 | `screens/today/TodayPlace.tsx:1046` (an empty, done plan's heading) and `:1066` ("Keep going ↵"), while the cause line carries the offer and its own "Begin ↵"; Enter goes to the offer (`:955-962`) | S, frontend |
| UX-53 | S3 | A quick check whose writing failed (the plan overloaded) kept "◐ writing a quick check for this section…" for over a minute after the failure; after leaving and coming back, only "Keep reading at your own pace."; no failure and no Try again were ever shown | student-3 #54-63, #96 (vault: the check's job failed at 3:29) | `screens/reader/useReadingProgress.ts:822-856` polls the guide plan, which carries no failed state, for up to 45 × 4 s before "Couldn't write a check"; the state resets when the Reader reopens (`:435`), and the section is not asked again | S (read the job's failure), frontend + a small sidecar field |
| UX-54 | S3 | A second source waits silently behind the first book's build: the past exam's card said "◐ Getting this PDF ready" for seven and a half minutes; its import (about a second's work) was queued behind the chapter's synthesis | student-3 #27, #92 (vault: the import `queued` from 1:09 to the walk's end); retainer-3 (two later books' builds queued behind the first) | `db/stores/ingest_queue.py` `claim_next_ingest_job`: one job at a time, by batch priority then age; a cheap import has no way ahead of a long model step | M, backend (or S: the card says it is waiting its turn) |
| UX-55 | S3 | In the Reader's rail, the first click or typing on a control just scrolled into view hits something covering it: Ask's follow-up box after "ask follow-up", and the Guide's "Done with this section" | student-3 #73, expert-2 #34, firstq-2 #28 and #30 (and part 2: student-2 #70, project-1 #41) | Not traced: likely the rail's sticky footer or composer over a target that `scrollIntoViewWithin` placed at the rail's edge (`block: "nearest"`). Seen five times in four walks of the harness's browser; confirm in WebKitGTK | S, frontend |
| UX-56 | S3 | Ask's source chips under an answer name a section by its slug or "root": "§ source: Wikipedia Elevator Paradox · modeling-the-elevator-problem", "… · root" | retainer-3 #46 | `screens/reader/ReaderAskBranches.tsx:265, 272` print `citation.label` without `sectionWords` (UX-24's fix covers Contents, the path and side by side). A page read again (UX-11) has words; a page read before keeps slugs, and "root" is a one-section reading's unit label | S, frontend |
| UX-57 | S3 | Adding a file that is already in the library, from another place, made a second copy with no word; the Library then held two cards for one article and Today asked an OK "and 2 more" | retainer-3 #6, #48 and report (vault: two sources with the same content hash, different paths) | `content/pipeline/add_source.py` reports `existing` ("Already in your library — opened where you left off.") for the same source; the same content from another path is not caught. Not traced further | S, backend |

### 5.2 Checked and dismissed, or not settled

| Candidate | Verdict |
|---|---|
| "Backslashes" and "dollar signs" in the equations (five walks) | Harness: the text view carries KaTeX's TeX annotation; the screenshots show drawn math. |
| "Nothing in your practice or books fits this yet" under an answer that cites both books (retainer-3 #46) | The tutor's offers ran with the embedding route unreachable. The words still contradict the answer above them; recheck with a key (section 9). |
| The intent box always "couldn't choose, so this asks" | The Decider route is unreachable. |
| "Practise for this goal" did nothing (student-3 #32) | Not settled: the notice renders after the goal card (`TodayPlace.tsx:1189-1205`), and the details were open, so it was probably below the window ("More below"). If so it is F26's kind (a result out of view), not a dead control. |
| The overloaded plan (firstq-1 synthesis, student-3 quick check) | The provider. firstq-1 recovered unseen (UX-13's retry). The silence after student-3's failure is UX-53. |
| The greeting from "Friday night" to "Friday morning" (firstq-3 #49) | The walk crossed 5 a.m. |
| "Undo this article 's questions" | The harness's text joining. |
| Editing or deleting a highlight jumped to the passage (retainer-3 #71-72) | Probably the harness's known gap (buttons inside a clickable card are not numbered); not settled. |
| firstq-2's long synthesis | The same call firstq-5 and firstq-6 measured; fixed by UX-39 and UX-41. |

### 5.3 The open rows, by this wave's evidence

| Row | This wave | Change |
|---|---|---|
| UX-28 (the phone shows a held grade's score) | Not reached (no phone walk) | Unchanged |
| UX-30 (the card says "Writing questions for this article" while the build writes none) | Confirmed: "◐ Writing questions for this article" for the whole of student-3's build (#92). New beside it: after the section's questions were written and answered, the card read "Questions for this article come up as you read" (firstq-10 #84) | Add the second sentence to the row: the card says neither what was written nor what is being written |
| UX-32 ("Build questions for the whole article at once" writes no question) | Confirmed: firstq-1 pressed it and got "Chapters found", then nothing (#52-54); firstq-8 got "All of this article is ready for questions…" on a build with no topics (#58, since UX-43); firstq-2, -5 and -6 said they left it alone for fear of a second build; firstq-10 read it as "where more questions can come from" (#85) | Unchanged; more evidence |
| UX-34 (a definition split at its emphasis) | Now seen: a definition broken over separate lines, "symmetric" glued to the next word (firstq-10 #15) | Raise its due date from the Reader redo to the next frontend-visible extraction fix, with UX-35 |
| UX-35 (figures and captions dropped) | Confirmed by ten personas: the exercises ask to plot on or inspect figures that are not there (firstq-1, -2, -3, -4, -5, -7, -8, -10, student-3 #55, retainer-3) | Raise to the first stage (F43) |
| UX-40b (a held question's review surface) | Not reached: every question auto-applied (firstq-9: 9, firstq-10: 6) | Unchanged |
| UX-44b (the reserved question on today's list) | Not reached on main; firstq-9 picked from the full list on `0b1fcf13da` (#86), whether the reserved one is not settled | Unchanged |
| UX-44c (the full list's "coming back later today" for answered rows) | Confirmed on `0b1fcf13da`: "all six questions are coming back later today, even the ones I got right" (firstq-9 #85); UX-44 did not change these words | Unchanged; more evidence |
| UX-46 (a test that does not wait for its worker) | Not a walk matter | Unchanged |
| UX-10 (the one-time OK) | Still asked on the fresh-vault route (retainer-3 #59-61), never on the empty install (ten walks) | The owner's ruling still needed |

### 5.4 Drafted ledger rows

For `docs/reviews/refactor-bug-ledger.md`, under "From the UX journey audit's walks", in its columns. The stage numbers are section 8's. Not added to the ledger by this part.

```markdown
| UX-47 | UX journey audit part 3, walk firstq-7 #60-70 | With no question offered yet, a topic that failed while the section's other topics are still being written makes Today say "Couldn't write the questions from what you read in “…”. Try again, or keep reading: nothing is lost."; Try again changes nothing visible while the job runs, and the learner gives up while the writing goes on. | new: `todayCause` with a running section job, one failed topic and nothing offered gives `section_writing` (with its count), and the failed topic's line only once the writing has stopped | Rank a failed topic below the writing while the job runs (`app/todayCause.ts` `ORDER`, the `section_failed` case); say the failure, with Try again, once the writing stops | open; stage 1 of the third part |
| UX-48 | UX journey audit part 3, walk firstq-9 #95-96 | "Redo the part you missed" prints the repair suggestion's rationale, written for the system ("elicit the omitted computations…", "repaired trace"), as "What to fix". | new: a guided redo whose suggestion has a rationale shows the failed rubric lines (or a learner-facing instruction), never the rationale | Stop sending `rationale` as `redo_instruction` (`diagnosis/guided_redo.py`); show the ✗ lines the redo targets (`PracticeScreen.tsx`) | open; stage 1 of the third part |
| UX-49 | UX journey audit part 3, walk firstq-9 #102 | The session end marks a topic "(on your own)" when an own answer earned part credit and the topic was then finished with help, beside feedback that said "practice with help". | new: a session with a partly right own answer and a correct assisted redo on one topic names both kinds on the session end | Name what each kind covered (`handlers/sessions.py` `_session_topics`, `SessionFinishHud.tsx`): for example "● part on your own · ◌ finished with help" | open; stage 1 of the third part |
| UX-50 | UX journey audit part 3, walk retainer-3 #24-27, #69-70 | After "note" (or "highlight") on a selection, the Notes rail shows "✓ saved" above an empty note box; what is typed there is never sent, because the only button that sends it is disabled once highlighted. | new: text typed in the note box after the selection was highlighted is saved on that highlight | Save the note on blur or Enter, or give the box its own "save note" once highlighted (`screens/reader/NotesRail.tsx`) | open; stage 1 of the third part |
| UX-51 | UX journey audit part 3, walk retainer-3 #18-20 | Words typed into the selection box to find an action ("highlight") become that highlight's note. | new: choosing "highlight" from the selection box's filtered list saves no note when the typed text matches the action's name | Treat the box's text as a note only when the learner chose "note" or wrote more than an action name (`ReaderScreen.tsx` selection effects) | open; stage 1 of the third part |
| UX-52 | UX journey audit part 3, walks firstq-9 #56, firstq-10 #58, #78 | Today's heading says "Nothing planned for today." above a book's questions offered with "Begin ↵", and "Keep going ↵" shows the same key. | new: a done, empty plan whose cause is `questions_ready` shows no "Nothing planned" heading and only one control marked ↵ | One heading for the offer (or none), ↵ only on Begin (`screens/today/TodayPlace.tsx` done branch) | open; stage 1 of the third part |
| UX-53 | UX journey audit part 3, walk student-3 #54-63, #96 | A quick check whose writing failed keeps "◐ writing a quick check for this section…" until the guide's three-minute poll ends; after the Reader reopens, only "Keep reading at your own pace."; the failure is never said. | new: a failed `reader_quick_check` job shows "Couldn't write a check for this section · Try again" at the next poll and after reopening | Carry the job's failure in the guide plan (or read it), and keep it across reopening (`screens/reader/useReadingProgress.ts`, `GuideRail.tsx`) | open; stage 1 of the third part |
| UX-54 | UX journey audit part 3, walks student-3 #27, #92, retainer-3 | A second source's import (seconds) waits behind another book's long model step; its card says "◐ Getting this PDF ready" for minutes. | new: an import queued while another book's synthesis runs starts before the synthesis ends (or its card says it is waiting its turn) | Let imports and other short steps claim ahead of model steps (`db/stores/ingest_queue.py` `claim_next_ingest_job`), or say "waiting for “…” to finish" | open; stage 1 of the third part (the words), stage 2 (the queue) |
| UX-55 | UX journey audit part 3, walks student-3 #73, expert-2 #34, firstq-2 #28, #30 | In the Reader's rail, the first click or typing on a control just scrolled into view lands on something covering it (Ask's follow-up box, the Guide's "Done with this section"). | new: after `scrollIntoViewWithin` brings the follow-up composer and the section's done control into the rail, the element at their centre is the control itself | Scroll targets clear of the rail's sticky parts; confirm in WebKitGTK | open; stage 1 of the third part |
| UX-56 | UX journey audit part 3, walk retainer-3 #46 | Ask's source chips name a section by its slug or "root" ("· modeling-the-elevator-problem", "· root"). | new: a citation whose label ends in a slug renders in words, and a one-section reading's "root" renders as the book's title alone | `sectionWords` on `citation.label` (`screens/reader/ReaderAskBranches.tsx`) | open; stage 1 of the third part |
| UX-57 | UX journey audit part 3, walk retainer-3 #6, #48 | The same file added from another place becomes a second library copy without a word (same content hash, different path). | new: adding a file whose content matches a source in the library returns `existing` with "Already in your library" | Match on the stored asset hash as well as the source (`content/pipeline/add_source.py`) | open; stage 1 of the third part |
```

---

## 6. Design findings, ranked by learner impact

Works as built, fails a criterion. The second part ended at F38; these continue from F39. The first five are the ones the patient persona repeats across the chain.

**F39 (S2). The build's wait is one unchanging line.** Eleven walks (firstq-1 to -10, student-3). After the section is finished, Today says "◐ Getting “…” ready for questions · 1 of 2 steps done" for about three minutes on a good run (firstq-10 2:35-5:33) and for 15 to 20 minutes on a failing one (firstq-5, firstq-6), then "· 0 of 8 topics done" for about two. The mark turns; the words do not change; "The first time, this can take several minutes." is the only estimate. Expected: something that moves, or a time. Happened: "I cannot tell whether it has moved at all" (firstq-9 #53), "I could not distinguish slow progress from being stuck" (firstq-3), "a minute at the same count felt uncertain" (firstq-10). "Keep reading meanwhile" is offered to people who have just finished. Fails N-F, H1, U9; the owner's 2026-11-19 request. What the sidecar knows and the screen does not: that the call is still delivering (UX-41's delivery counts), how long this machine's last build took, and which step is running.

**F40 (S2). Nothing says what comes tomorrow.** All thirteen walks. The session end says what moved ("2 minutes this session · 3 questions · Since last time: ● …", firstq-10 #79), never what comes back or when; "1 day" sits bare under Today's buttons (firstq-9, firstq-10 #78, read as "come back in one day?"); the full list says "coming back later today" for answered questions (firstq-9 #85, UX-44c); the redo promises "A check on your own comes back on another day." with no day (firstq-9 #95); Progress is a map. Expected: "Tomorrow: about N minutes, these questions." Fails M4, I11, H1, O2. First part F4 and P5, now for a first-day learner.

**F41 (S2). "done for now" finishes the whole section.** Eight walks (firstq-3 to -10). The quick check's "done for now" is the section's completion (UX-29's control). Every patient persona read it as closing the check, was surprised by "✓ Done with this section." at 76 to 84 % of the page, and read on; the page's percentage and the guide's 100 % then disagree (firstq-10 #38: "the side now says 100 while the top says 80"). The same finish by the quick check never shows UX-31's waiting sentence in the Reader. Fails I9, N-C, H4. Whether reading to the end should finish a section without a press is still the owner's call (ledger UX-29); the label is not.

**F42 (S2). The quick check's controls are below the guide's fold.** Eight walks (firstq-1, -2, -4, -5, -6, -7, -9, -10). "A quick check on this section is ready, just below." with "More below in Reading guide (scroll down)"; scrolling over the chapter moves the chapter (firstq-10 #29-31); firstq-1 never reached "compare" and pressed "Done with this section" instead (#22-28). First part F15 named the same fold for "compare with the source". Fails N-D, J3, U1.

**F43 (S2). The chapter's figures are not beside the exercises that use them.** Ten walks. Exercises ask to plot on, or read from, figures that the reading does not have (UX-35); several personas said they could follow the prose but not do the exercises (firstq-1, -2, -3, student-3 #55). Fails M3, O10, J3. UX-35 is the defect; the finding is that it now costs the first evening's practice of the exercises.

**F44 (S2). Practice exists only for finished sections, and what a learner asks Ask to set counts for nothing.** student-3, expert-2, and firstq-1 to -8 by their outcome. An exam student who reads part of a chapter (student-3: 54 of 59 passages), an expert who skims (expert-2: 14 of 59) and a learner whose section's questions failed all reach practice only by asking Ask for problems (student-3 #64-79, expert-2 #29-38): graded in chat, well, and recorded nowhere ("I did not find evidence that my correct Ask answer had become a practice result", expert-2). Keep going plans more reading. Fails J3, M6, O2 (what was shown is not what counts). Inventory: "add exercise to practice" exists in the Notes rail for a selected exercise; no walk found it.

**F45 (S3). Three "nothing" sentences while questions are being made.** firstq-1, -2, -4, -6, -10, student-3, retainer-3. "Nothing planned for today." (heading), "Nothing more to plan today." (Keep going), "Nothing else for today." (the full list), each beside a line that says questions are on the way. "'Nothing planned' and 'Nothing more to plan' made the promise of incoming questions feel less certain" (firstq-6). Fails N-C, O2. UX-52 is the heading's defect; the finding is the set.

**F46 (S2). A goal can be made twice and not changed.** student-3 #15-21, #30-31. Reopening "learning this for something?" shows a blank form, so a correction makes a second goal ("2 deliverables"); "receipt" shows who resolved it, not the date. Strengthens F3, F30 and the Goals place (P2). Fails O9, H3, N-C.

**F47 (S3). Saving your own words in the Reader.** retainer-3. Beyond UX-50 and UX-51: three quotes took about eighteen actions, "Notes & files" opened the vault's file tree when the person looked for saved highlights (#65-66), and nothing in the Reader searches what was kept. Strengthens F34. Fails M9, J10.

**Strengthened, not new.** F28 ("I know this" behind a learning object's id, expert-2 #56-64). F30 (the chapter's own topics "not in your library yet", student-3 #14, expert-2 #12; partly the unreachable embeddings and the unbuilt library). F38 (small words: "1 day", the feedback's third person about the learner, firstq-9 #93; "knowledge field", "goal overlay", "open error events", firstq-10 #82; "bootstrap_synthesis", "authoring batches", firstq-9 #49). F26 (the Ask answer out of view: student-3 #40-45). F35 (one "Document" in the three walks before UX-11).

**What worked, to keep.** The first two minutes: the chapter open in seconds with "It opens here as soon as it is ready", the depth question, the path's "about 20 min of reading". The quick check's question and its "compare, don't grade" ("low pressure", firstq-10). Questions arriving a topic at a time with no press, and Begin beside them ("I appreciated being allowed to begin before every topic was ready", firstq-10). The feedback: a tick or a cross per rubric line, the full answer, "next: *topic*" (firstq-9 and firstq-10: "fair", "accurate and specific"). The partly right answer's waits, each named. The redo that keeps the learner's correct work. UX-18's two sentences (expert-2). Ask, again, for every persona who used it.

---

## 7. Proposals

The earlier P1 to P18 stand. These continue from P19. Proposed wording in *italics*.

**P19. A wait that moves (F39).** The build's line names its step and shows that it is alive; the learner's options stay one line below:

```
◐ Reading the chapter to plan its questions · step 2 of 2 · still writing (2 min so far, usually about 4)
  Your questions from Section 7.1 come next: 8 topics, about 2 minutes each.     [ Continue reading ]
```

"still writing" comes from the call's delivery (UX-41 already counts it); "usually about N" from this machine's last build (none the first time: *the first time takes longer*). When delivery stops for a minute: *Still waiting for the model; nothing is lost. LearnLoop tries again by itself.* When the person is at the section's end, the second button is *Read the next section* or nothing, never "Keep reading". In the Reader, the moment questions apply: a quiet line in the guide, *3 questions on what you read are ready on Today ▸*.

**P20. Two controls for two things (F41, F42).** The quick check opens scrolled to its answer box, with its buttons pinned under the box. After compare:

```
[ Done with this check ]     I've read this section ▸
```

*Done with this check* closes it; the section is finished at its end, or by *I've read this section*, which then says UX-31's sentence in the Reader as well as on Today. The page's and the guide's percentages are one number. (Whether reaching the end finishes the section without a press is the owner's call, ledger UX-29.)

**P21. Tomorrow, in one line (F40, UX-49).** At the session end and under Today's offer once the day is done:

```
3 questions · about 2 minutes
● Recognize and verify eigenpairs (on your own)
◌ Construct a diagonalization: part on your own, finished with help
Tomorrow: about 6 minutes. These 3 come back, and Section 7.1's other 5 topics if they're ready.   [ Done ↵ ]
```

"1 day" becomes *1 day in a row* or goes. A redo's promise names its day: *A check on your own comes back on Saturday.* This is the first slice of P5 (load you can see), for one book.

**P22. Practice while questions are written (F44).** When Ask has set problems and judged them, one line under the exchange: *Keep these as practice? They'll come back like your other questions. [ Keep ] [ No ]* (a kept problem is ordinary practice with help, said as such). And on Today, for a learner with a book read in part: *Questions come from sections you finish. You've read most of Section 7.1: [ I've read it ▸ ]*.

**P23. One sentence for "nothing yet" (F45, UX-52).** Today's heading is the offer or the wait, never "Nothing planned for today." while a book is being got ready or its questions are offered. The three "nothing" lines become one, said once: *Nothing to practise yet: your questions from “…” are being written.*

**P24. The figures with their exercises (F43, UX-35).** Keep each figure's caption and image at its place in the reading; where the image cannot be kept, the caption with *open the page to see this figure ▸*. An exercise that names a figure shows it beside the question written from it.

**P8, the owner's question of 2026-11-20 (one visible search box in the Reader).** These walks strengthen P8, mostly for what the learner kept rather than for the book's text. retainer-3 looked for its saved highlights in "Notes & files" and found the vault's file tree (#65-66), then typed "highlight" into the selection box hoping it would search the actions, and the word was saved as a note (UX-51): the one box the Reader shows looks like a search and is not one. student-3 looked for the data an exercise referred to (#55: the figure was dropped, so search would not have found it). No walk looked for a passage by its words. So P8 should cover the learner's own highlights and notes, not only passages, and the selection box should not look like a search. The front door's "ask your library" was not used in this wave.

**Earlier proposals these walks strengthen.** P5 (load you can see) by F40 in all thirteen walks; P11 is built and worked (firstq-9, firstq-10); P14 (say what you know, where you are) by expert-2 and F44; P17 (the goal box agrees with the library) by student-3 #14 and expert-2 #12; P2 (a Goals place) by F46; P10 (Progress in words) by every first-day persona who opened Progress for tomorrow.

---

## 8. The fix stages, re-ranked

One ordered list for the queue, by learner impact. Done stages are struck. Sizes: S about a day, M two to four days, L a week or more. Constraints kept: help that shows what it gave away waits for the Decider's first stage; feedback, hypotheses and repair screens wait for arc G (G2, `mvp-0.61`); the Reader redo carries search, margin cues and syntopic reading; no persona picker; nothing changes what is computed without saying so.

| # | Stage | Contents | Size | Kind | Owner decision first | Waits for |
|---|---|---|---|---|---|---|
| — | ~~Waiting you can see~~ | Landed (`5f35fa7ac8`); the build's wait moves to stage 2 | — | — | — | — |
| — | ~~First questions arrive~~ | Landed (the chain to `1f9c8de1b3`): UX-13, P11, UX-29's control, UX-31, UX-33, UX-11, UX-37, the progress line, UX-38 to UX-45. Left: UX-30, UX-32 (words), UX-40b, UX-44b, UX-44c | — | — | — | — |
| — | ~~Broken controls, second round~~ | Landed (`9a91561184`). Left: UX-20's why (stage 8), UX-28 (phone) | — | — | — | — |
| 1 | **Broken controls, third round** (new) | UX-47 (Today during a failed topic), UX-48 (the redo's instruction), UX-49 (session end's mark), UX-50 and UX-51 (notes lost or invented), UX-52 (the heading and ↵), UX-53 (a failed quick check said), UX-54's words, UX-55 (covered controls, in the real window), UX-56 (chip slugs), UX-57 (a second copy); with UX-30 and UX-32's words, UX-44c's two kinds of "later", UX-28 if the phone is touched | M (twelve small fixes) | frontend; small sidecar for UX-49, UX-53, UX-57 | no (UX-32's "write everything at once" option stays the owner's) | nothing |
| 2 | **The first evening, finished** (new) | P19 (the build's wait that moves: a delivery heartbeat, the step, this machine's usual time), P20 (check and section as two controls, the check in view; F41, F42), P21 (tomorrow in one line, the session end; F40's first slice), P22 (Ask's problems kept as practice; "I've read it"; F44), P23 (F45), P24 with UX-35 and UX-34 brought forward (F43), UX-54's queue | M-L | backend (a progress field, the forecast's one line, captions at extraction) + frontend | **yes**: whether reaching a section's end finishes it (UX-29), and whether kept Ask problems become practice items | nothing |
| 3 | **Load you can see and steer, for one or two courses** (part 2's 7, moved up) | P5 in full (tomorrow and the week, *less / more*, a daily amount), P16's split between courses, F31's sizes, a 20-minute and a phone 5-minute choice; builds on stage 2's one line | M-L | backend + frontend | yes (spec) | stage 4's course for the split only |
| 4 | **Course setup, graded work and the practice exam** (part 2's 4) | P3, P13, P16's course, the graded-work entry, P17; now also student-3's quiz queued behind the chapter (UX-54) and its second goal (F46) | L | backend + frontend | yes (spec; owner: built inside the audit's fix) | nothing |
| 5 | **A Goals place** (part 2's 5) | P2: every goal, deadline and scope edits, pause and close, a goal reopened to edit instead of made twice (F46), "Am I ready?" outside the Reader | M-L | backend + frontend | yes (spec) | stage 4's course |
| 6 | **Lessons you can find** (part 2's 6; UX-14 done) | P12's list of lessons, the offer on the topic just missed, "I'm stuck" that can teach, the Teacher screens remade, a cancel for a lesson turn | M-L | frontend + small backend | yes, short | "Teach me this" on feedback waits for arc G |
| 7 | **Help shows what it gave away** (part 2's 8) | P6, P15 (F24), F37, UX-20's why, F36, F26 in practice | M | backend + frontend | no | the Decider's first stage; arc G |
| 8 | **Progress in words and the jargon sweep** (part 2's 9) | P10, F5, F6, F16, F18, F32, F38 (now with "knowledge field", "goal overlay", "open error events", the feedback's third person, "bootstrap_synthesis"), UX-12; F33 if the owner agrees | M | mostly frontend | the owner's call on F33 | nothing |
| 9 | **The Reader redo** (part 2's 10) | P8 (now over the learner's own highlights and notes too), P7, syntopic reading, F26, F34 and F47, F35 | L | backend + frontend | yes (spec) | nothing for the frontend parts |
| 10 | **Own notes as sources** (part 2's 11) | P18 (F27) | L | backend + frontend | yes (spec) | stage 4's course; the Reader redo's cues |
| 11 | **Settings cleared** (part 2's 12) | F17, the owner's Nov 8 item, the daily amount with stage 3 | M | frontend + small backend | no | stage 3 |

UX-10 (the one-time OK) still needs the owner's ruling (section 5.3). The phone's pairing page (F11) still needs the host-side change.

After each stage, re-run the walks it came from (I2): after stages 1 and 2, the patient persona (firstq) twice, once with a wrong answer, plus student, retainer and expert; after stage 3, a two-evening walk.

---

## 9. What this part could not check, and a fourth wave

**Not checked here.**

- On the live route since the chain was fixed: a wrong or partly right answer and its follow-up (UX-45 landed after firstq-9; firstq-10 answered all three right); the question reserved for a later check (UX-44b, and UX-44's step 3 branch); an empty build (UX-43); a model that leaves ids empty (UX-42); a topic that fails while others are offered ("Not every topic's questions could be written."); a held question (UX-40b).
- The second round's fixes that need lessons, the workbench, a plan with blocks or a check screen: UX-14, UX-16, UX-19 to UX-22, UX-27 (no walk reached them).
- The phone: every first-question line, UX-23, UX-28, the waiting lines.
- The real WebKitGTK window: UX-15, UX-19, UX-55; reduced motion.
- The Decider and embedding routes, unreachable in every walk: the intent box, topic matching in the goal box (F30), the tutor's offers under an answer (retainer-3 #46).
- A second build in a library ("usually about N min"), a page read before UX-11 and its "Read it again", the elevator article added fresh.
- Tomorrow itself: no walk came back on a second day, so F40 is about what the screen says, not what the next day holds.
- Which commit firstq-1 to -3 and the three re-walks ran on is read from their start times, not recorded; the orchestrator's note groups firstq-1 to -3 as "before UX-31/UX-33/UX-11", but firstq-2's vault holds UX-31's stamp, so firstq-2 and firstq-3 ran after UX-31.

**A fourth wave would need.**

1. Fixtures: a library whose first build is done and whose first topic's questions are applied (so a wrong answer, the follow-up and the reserved question are walked in minutes, not after a nine-minute build); a vault where one topic's writing fails while others are offered; one with an empty build; one with a held question.
2. A wrong-answer persona on the live route on main (the follow-up after UX-45), and a second evening for the patient persona (what tomorrow brings, against P21).
3. Re-walks on main of lesson-1, workbench-1 and returner-1, for the second round's fixes that no walk has reached.
4. The phone on the live route after a desktop first evening.
5. The owner's decision on a Decider and embedding key for walks.
6. A short check in the real WebKitGTK window for UX-15, UX-19 and UX-55 before stage 1 lands.
7. After stage 2: firstq again, with the build's wait timed against P19, and student-3's and expert-2's journeys (a part-read chapter, a skimming expert) against P22.
