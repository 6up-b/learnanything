# UX journey audit, second part

The second part of the UX journey audit (the first part, with the criteria, the inventory, the first wave of walks and the twelve fix stages, is `docs/reviews/ux-journey-audit.md`; the criteria ids are in `docs/reviews/ux-journey-audit-criteria.md`). Since the first part, fix stages 1 to 4 landed (`ux-fix-stage-1.md` to `ux-fix-stage-4.md`) and thirteen new walks were made on the fixed application. Written 2026-11-19 against main `713a0efd08`, on branch `docs/ux-journey-audit`.

The owner asked on 2026-11-19 for the audit's fixes to be built, so this part ends in fix stages to be queued (section 8). The owner also asked, the same day, for waiting indicators; a separate stage is building them now (section 8, stage 1). "No persona picker" stays design guidance for the overhaul, not a criterion.

## 0. How to read this

**The walks.** Each walk is an agent playing one person, given only that person's goals and the screen (`docs/reviews/ux-walk-harness.md`). They are private, under `fixtures-local/ux-walks/<walk>/`, cited here as "walk #step" (for example "lesson-1 #42"). No screenshot is copied into this document.

| Walk | Person | Start | Models | Steps | How it ended |
|---|---|---|---|---|---|
| student-2 | exam student, midterm in three weeks, chapter and old quiz (re-walk of student-1) | empty install | live | 89 | stopped: lost the app's tabs (#83-88) |
| beginner-2 | wants machine learning, no book (re-walk of beginner-1) | empty install | live | 23 | **gave up, blocked**: nothing starts without a book |
| retainer-2 | curious reader, ten minutes a day (re-walk of retainer-1) | fresh vault | live | 87 | done or given up, goal by goal |
| seasoned-2 | a month in, goals and housekeeping (re-walk of seasoned-1) | established | live | 83 | done or given up, goal by goal |
| phone-3 | five minutes on the bus (re-walk of phone-2) | established | **faked** | 50 | done |
| lesson-1 | wants to be taught, not quizzed | established | live | 76 | gave up finding the closed lesson |
| workbench-1 | works in steps, likes pictures | established | live | 101 | done |
| exam-1 | five days before an exam, wants a practice exam | established | live | 33 | **gave up, blocked**: no practice exam to sit |
| returner-1 | back after three weeks | established, built three weeks back | live | 56 | done |
| expert-1 | data scientist, wants to test out | empty install | live | 79 | gave up after three empty checks |
| notes-1 | own notes (Markdown folder with links, a flashcard file, a lecture transcript) | empty install | live | 98 | done or given up, goal by goal |
| project-1 | building a PCA image compressor | empty install | live | 73 | done |
| twocourses-1 | a second course beside linear algebra, one daily budget | established | live | 99 | done (read last, after its report was written and its directory stopped changing at 21:01) |

**Why beginner-2 and exam-1 are short.** Both gave up because the journey they came for has no way in, not because of a crash or a harness fault. beginner-2 had the same brief as beginner-1 ("you have no files; ignore the ones in `files/` unless the application makes you need one"). beginner-1 gave in at #42 and added the sample article; beginner-2 did not, tried Today, Add, More options, the ⋯ menu, the Reader's "ask your library" (which answered "Nothing in your books matched this yet." on an empty library, #15-16) and Progress, and said at #22: "It seems I have to find a book before this will help, and choosing that was what I needed help with." exam-1 looked for a practice exam on the goal card, in the ⋯ menu and by uploading last year's quiz (which opened as ordinary reading, #18-19), said at #23 "I'm giving up on sitting an exam here today", and stopped at #32 after checking the readiness report and "plan around my week". Its goal has no held-out exam pool, so the goal card offers no practice exam, and no control can add one.

**What is the harness, not LearnLoop** (checked against the fidelity table):

- The Decider and embedding routes were unreachable in every desktop walk (`routes.json`: nine routes "unreachable", no key in the walk configuration). So the Reader's intent box always fell back ("LearnLoop's model couldn't choose, so this asks", student-2 #34, notes-1 #42), compare scope and meaning search were off, and the goal box's topic matching ran without embeddings. The repeated "0 topics from your books · N not in your library yet" for topics a chapter plainly covers (student-2 #14, expert-1 #15, twocourses-1 #15) may be partly that; it is also true in the narrow sense that the library had no topics yet (question writing had not finished). The finding (F30) is about the words, which say the same thing in both cases.
- phone-3 used faked models: its questions, grades and the "4 / 4" beside "(1/3)" and "(0/1)" are made up. Its flow is judged; only the raw label it printed is a defect (UX-23), because the screen prints whatever reason arrives.
- The established vault's rubric line "Says why, in a line." is the fixture's (`scripts/ux_walk/make_vault.py:108`), so the grade complaints about it (seasoned-2 #48 too generous, twocourses-1 #50 too strict) are about the fixture's items, not about LearnLoop's question writing. What the person could do about a grade they disagreed with is still LearnLoop's (F37).
- Fixture dates: exam-1's brief says the exam is in five days, the vault's goal says Dec 11 ("due in 22d"); returner-1's "goal whose date has passed" is due on the walk's own day ("Nov 19 · getting there", "due today"). So the passed-date state was not walked (section 9).
- "Open another library…" on a notes folder (notes-1 #15) ran the harness's emulated `select_vault`; its failure is not evidence about the real app.
- Deleting an annotation (retainer-2 #75-78) failed because the harness does not number buttons inside a clickable card (harness record, "Still not possible").
- Walker latency: a few gaps of five to six minutes (seasoned-2 #1, #39, #57; returner-1 #7, #50) are the agent, not the person. Clicks that "took" about 8.6 s are the driver's settle limit while the app was busy, so the real wait was at least that.
- lesson-1's report says "the supplied brief did not include a named persona"; the brief did, and the walk followed it. A walker slip.

---

## 1. Before and after: fix stages 1 to 4

"Old" is the first wave's walk and step; "new" is this wave's. Verdicts: **fixed** (as seen by a person), **partly**, **not reached**, **still there**, **worse** (a fix made something misleading; each of these is also a defect in section 5).

### 1.1 Defects and findings the stages claimed

| Item | What it was | Old | New | Verdict |
|---|---|---|---|---|
| UX-1 (fixed before stage 1) | Question writing for a web chapter failed on the output budget; Retry failed the same way | student-1 #101-120, beginner-1 #74-94 | student-2 #30-37 (inventory failed, Try again worked, then the synthesis pass failed at 10,352 of 10,000 tokens, unseen); expert-1 #18-21 (failed, retry worked); retainer-2 #85 ("inventory output exceeded its configured token budget", not retried) | **partly**: Retry now recovers the first step; the first attempt still fails often and the next step has the same wall (UX-13) |
| UX-2 | A source's own TeX macros showed as red commands | student-1 #18, #132; phone-2 #37 | student-2 #87 (screenshot: bold **v**, ℝᵐ, no red); retainer-2 #44; phone-3 #37 ("the equations do look normal") | **fixed** in the Reader, desktop and phone. The three display equations the extraction keeps show as raw `\begin{equation*}` text (UX-25, with UX-11) |
| UX-2, snippets | Today's thread line in raw TeX | student-1 #147 | student-2 #36 (the thread was a plain question, no math) | **not reached** |
| UX-3 | Ask panel had no send button | seasoned-1 #74-81 | seasoned-2 #53-55 ("ask: send your question" used); lesson-1 #72; workbench-1 #46 | **fixed**. A figure closed and reopened: **not reached** |
| UX-4 | "Keep going" with nothing to add said nothing | student-1 #44, retainer-1 #63 | student-2 #28, retainer-2 #62, expert-1 #47, notes-1 #37: "Nothing more to plan today." plus the day's cause | **fixed** (now stage 3's words) |
| UX-5 | A past exam opened in the Reader with a red error | student-1 #33-57 | student-2 #22: "“18.06 Linear Algebra, Exam 1” is in your Library as a past exam. It doesn't open in the Reader, and LearnLoop doesn't write questions from it."; #23 the card's details | **fixed**. Sitting it is still impossible (F22) |
| UX-6 | Empty states as sticky red errors | beginner-1 #80-120, retainer-1 #49-61 | student-2 #29: the goal's line under the card, neutral, with its cause. No red error in any walk | **fixed** for the goal line; the palette notice **not reached** |
| UX-7 | "add it" did nothing with no subject | beginner-1 #54 | expert-1 #57-58, project-1 #22-24: "added as a new topic" at once | **fixed**; but the new topic is named from the sentence ("Covariance and Variance Mastery Check") and sits beside the book's own topic, unmerged (F30) |
| UX-8 | Empty goal said "all facets certified" beside BEHIND | student-1 #128, beginner-1 #84 | student-2 #42, project-1 #27: "NOT STARTED", "Nothing has been checked for this goal yet." | **fixed** as written, **worse** in one sentence: "None of the topics in your books is part of it so far" shows beside a deliverable that says "3 topics from your books" (UX-17) |
| UX-9 | Phone capture said "1 waiting to send" after delivery | phone-2 #31-48 | phone-3 #29-30: "Sent to your desktop · just now." | **fixed** |
| UX-10 (owner) | The one-time AI OK gates only question writing | student-1, beginner-1, retainer-1 | Asked in the fresh-vault walk (retainer-2 #46-61) and in the established vaults' libraries; never asked in the four empty-install walks (student-2, expert-1, project-1, notes-1), where questions were written at once | **still open, and now inconsistent by route**: the owner's ruling is still needed |
| P1, F1 | Today never said why it was empty | student-1 #40-45, beginner-1 #78-82, retainer-1 #61-63 | student-2 #28-37, retainer-2 #46-85, expert-1 #18-47, notes-1 #36-50, project-1 #25-27: the cause line and its action every time | **partly**: Today now names the cause; no first-day walk ever got a Today question (F20) |
| F7 | "Review" asked for permission | retainer-1 #70 | retainer-2 #59-61: "Give your OK" → the Connect sheet → OK; the person still first read it as "checking the questions" (#60) | **fixed** in label; one misreading |
| F9 | The plan's clocks disagreed | seasoned-1 #0-134 | seasoned-2 #13 ("About 25 minutes suggested today. Planned so far: …"), returner-1 #53 ("9 minutes this session · 2 questions"), phone-3 #7, #22 | **partly**: each number now says what it measures, but different sizes still sit side by side (F31) and "Done for today" after one question is new trouble (UX-16) |
| F11 | Phone pairing page didn't know the scan worked | phone-1, phone-2 #1-3 | phone-3 #1-5, the same page; Pair worked with the code box empty | **still there** (stage 4 item 1 was stopped: the page is the host's) |
| F13 | Phone didn't say what reached the desktop | phone-2 #31-53 | phone-3 #29-30 (capture), #16-17 ("…nothing is needed from you: Next goes on" was understood) | **fixed** for capture and the failed look; no "everything is synced" state (phone-3 #45-49) |
| F14 (owner's call) | Router line on learner screens | phone-2 #22 | phone-3 #22, #40; desktop feedback behind the lesson, lesson-1 #16-25 | **still there** (not in any stage) |
| F19 | Phone Today tab opened the question | phone-2 #40-43 | phone-3 #22-25, #40: the plan with "Resume your answer ▸", the draft back word for word | **fixed** |
| Stage 1 sweep, stage 3 item 5 | Refusals as red errors | (none walked) | No walk pressed Hint or Ask during a check | **not reached** |

### 1.2 "What to check in a walk", line by line

**Stage 1** (`ux-fix-stage-1.md`)

| Line | Answer |
|---|---|
| UX-3: "ask ↵" visible beside "show me ▸"; a figure closed with esc and reopened with ? shows building or built; docked layout at the walk's width | The send control is visible and used (seasoned-2 #53-55, the button reads "ask: send your question"; lesson-1 #72; workbench-1 #46). A figure asked for then the panel closed and reopened: not reached. Layout: the inline panel in the workbench clipped the figure and put the reply above it (workbench-1 #44-53, F26). |
| UX-4: Keep going on "Nothing planned for today." shows the new line | Yes, in stage 3's words: "Nothing more to plan today." (student-2 #28, retainer-2 #62). |
| UX-5: past exam lands in the Library, notice, no red error, details line | Yes (student-2 #22-23). |
| UX-6: Practise for this goal shows the dim line; palette Ask on Today is a neutral notice that does not come back | The goal line: yes (student-2 #29). The palette notice: not reached. |
| UX-7: "add it" turns into "added as a new topic", the subject named after the topic | Yes (expert-1 #58, project-1 #22-24). The subject's name was not visible; the topic's name was the sentence's phrase. |
| UX-9: "Saved. Sending…", then "Sent to your desktop.", no stale count | Yes, with stage 4's time (phone-3 #29-30). |

**Stage 2** (`ux-fix-stage-2.md`)

| Line | Answer |
|---|---|
| The chapter's macros render; the ASKING ABOUT chip shows math | Rendered (student-2 #87 screenshot; retainer-2 #44). The chip: the Ask rail's "§ from the book" quote showed math twice and a raw equation environment (UX-26). |
| Today's thread without `\(` | Not reached (no thread held math). |
| Goal details: NOT STARTED, no BEHIND, one sentence, "It is due in N days." | Yes (student-2 #42: "…It is due in 21 days."), but the sentence misleads (UX-17). |
| Side-by-side pane uses the other book's notation | Side by side opened (retainer-2 #45) on a page with no macros; not tested. |
| Phone Reader draws the symbols | Yes (phone-3 #37). |
| A protected source still shows raw commands, by design | Not reached. |
| Practice or feedback copying `\vvec` still red (UX-12) | Not reached: no question from the sample was ever served. |

**Stage 3** (`ux-fix-stage-3.md`)

| Line | Answer |
|---|---|
| Item 1, questions waiting for the OK: the line, Give your OK, what's sent; then "on their way" | Yes (retainer-2 #46-62). |
| Item 1, several books: "and 2 more" | Yes (retainer-2 #46: "…and 2 more are waiting for your OK."). |
| Item 1 with a build failure: "Couldn't get questions ready…" with Try again; the retry starts; what the card says after | Yes (student-2 #36-37, expert-1 #19-21). The retry starts and the line goes back to "on their way". After the next failure (student-2's synthesis, 00:40) nothing reached the person, who had gone to the Reader (UX-13). |
| Item 2: Practise for this goal says why, never red | Yes (student-2 #29). The "up today" variant: not reached. |
| Item 3: the sentences before Begin, after a block, and the done line read as different quantities | Before Begin and during: yes (seasoned-2 #13, lesson-1 #43). Done: "Done for today." with no minutes (under one minute) and "9 minutes this session · 2 questions" (returner-1 #53). Keep going then said "About 10 minutes suggested today" with the 25-minute chip still checked (seasoned-2 #70, F31). |
| Item 4: the card says "Give your OK" | Yes (retainer-2 #46; established vaults' Libraries). |
| Item 5: ^h and ? on a check; a note on a question with no subject | Not reached (returner-1 met a short check but asked for nothing). |
| Item 6: Keep going shows "Nothing more to plan today." and the cause; a finished day with questions on the list offers the list | The first: yes. The second: not reached; instead a finished day said "Nothing else is needed today." while three planned blocks were left (seasoned-2 #59) and while nine items were "coming back later today" (returner-1 #49-51): UX-16. |
| Layout of the cause line's action and what's sent | They sat on the line's end and wrapped cleanly in the screenshots read (student-2, retainer-2). |
| Not verified in the record: "Something new" beside an OK cause | Seen: "Nothing new is ready yet. Keep reading and LearnLoop will have more." beside "on their way" (student-2 #56, notes-1 #50). |

**Stage 4** (`ux-fix-stage-4.md`)

| Line | Answer |
|---|---|
| Item 2: "Saved. Sending…", then "Sent to your desktop · just now."; later "· N min ago"; the waiting line with the desktop away | "Sent to your desktop · just now." yes (phone-3 #29). Leaving and coming back, and the desktop away: not reached. |
| Item 2: a feedback whose look didn't finish says Next goes on | Yes, and understood (phone-3 #16-17). |
| Item 3: Today tab from Capture or Read with a draft: the plan, "Resume your answer ▸", the draft as typed | Yes from Read (phone-3 #40) and from Back to Today (#22-25, "the same question and my exact half sentence"). |
| Item 3: tap Today while grading; VoiceOver; the plan's Next with a draft waiting | Not reached. |
| Item 4: "Up to N minutes today. First: …", "Room for about N more minutes today. Next: …", the done line | The RO4 forms: "About 10 minutes suggested today. The rest is chosen as you go." (#7), "Room for about 9 more minutes of today's suggested time. Next: …" (#22). Done: "Done for today." (under one minute). |
| Item 1: pairing page unchanged | Confirmed unchanged (phone-3 #1-5). |

**Anything a fix broke or made confusing:** UX-16 (stage 3's finished-day line on an engine stop) and UX-17 (stage 2's empty-goal sentence). Both are in section 5.

---

## 2. Walk by walk

Each: what the person wanted, where they got there, where they got stuck or misread, what they could not find, and what the logs show that the report does not.

### 2.1 The re-walks, briefly

**student-2 (was student-1).** Better start, same dead end. The chapter opened at once (#5), the goal box was found at #10 (student-1 needed the same place), Today showed "Dec 10" (#28) and, new, said why it was empty: "on their way", then "Couldn't get questions ready … Try again" (#36), then "on their way" again (#37). The past exam now lands quietly in the Library (#22). No practice question ever came from Today. The only practice was one the person asked the Reader's Ask to set ("ask me first", #63-82): the tutor used the chapter's own matrix, caught the missing normalization and asked for the repair. Not in the report: after the retry the synthesis pass failed at 00:40 while the person was in the Reader, so the "Questions … on their way" they last saw was already false (UX-13); and the walk ended because the app's tabs had scrolled off the window after "ask follow-up" (#83-88, screenshot `0087`: the whole app shifted up, a black band below), with Escape and scrolling unable to bring them back (UX-15). The report's "most equations display properly; the separate A = QDQ line shows backslash commands" is exact: that line is one of the extraction's kept `\begin{equation*}` blocks (UX-25).

**beginner-2 (was beginner-1).** Gave up at #22 (section 0). Nothing in stages 1 to 4 touched this journey. The Reader's front door accepted the wish as a library question and answered "Nothing in your books matched this yet." under "personalized ●" (#15-16), which promises personal help an empty library cannot give. The typed lesson start ("What do you want to learn?") exists but only in the classic shell's "Learn something new" (`D/screens/TodayScreen.tsx:746`), so the person met no way to be taught.

**retainer-2 (was retainer-1).** Selection now works in the harness, so keeping things was walked for the first time: select → "↵ ask · tab actions" → Tab → a long action list → "highlight" (#10-13). "help me remember" closed with no word about what it kept (#16-17); later the Notes rail listed it as "interpretation exact “The **elevator paradox** …”", with raw Markdown and internal labels (#73). On the second selection "highlight" was not among the actions (#20), so the person moved to the Notes rail's own highlight button. Three saves took about twenty actions (M9 fails). Side by side was again the best moment (#43-45). Today named the OK as the cause, with "and 2 more" (#46), and the OK sheet explained itself (#59-61). At the end Today said the chapter's questions had failed (#85); the vault shows "inventory output exceeded its configured token budget", UX-1's own message (UX-13). Not in the report: the side-by-side button and the contents name sections by their HTML ids ("modeling-the-elevator-problem", "external-links", #16, #45; UX-24).

**seasoned-2 (was seasoned-1).** Practice went straight to a fair question (#44-47), and the Ask panel now has its send button: the person disputed a too-generous tick and Ask agreed, "On the rubric as written, I would revise the score to 3/4", but nothing was revised or recorded (#56-57; F37). After that one answer, Next showed "Done for today. / Nothing else is needed today." though the plan had listed four blocks (#59; UX-16). Keep going brought the blocks back under "About 10 minutes suggested today" with the 25-minute chip still checked (#70). Everything else the first walk failed still fails: Progress in decimals and "evidence mass" (#3-11), no date editor and no paused or undated goal (#14-23), no course for the new chapter (#31-33), "Mistake history" with one recalculation (#62-66), Settings as an engine room (#75-78). "Stop for today" inside "Something else would help" worked at once (#80-81).

**phone-3 (was phone-2, faked models).** The pairing page is unchanged (F11): "learnloop-mobile pair", an empty code box that Pair ignores, then "private token" and "Shortcut" (#1-5). After that the phone did well: ten minutes to a question in two taps (#7-9), the half-typed answer survived Back to Today behind "Resume your answer ▸" (#22-25), capture said "Sent to your desktop · just now." (#29), lessons said they wait on the desktop (#44). Still there: the router line on Today (#22, #40; F14), no session shorter than ten minutes, the book as one "Document" (#36), no "everything is on your computer" state (#45-49). New: the feedback printed "valid_alternative_unverified" under the score (#10; UX-23).

### 2.2 lesson-1: asks to be taught

**Wanted:** to be taught a weak topic, leave a lesson halfway and come back, and be taught after a miss.

**Got there:** the lesson itself. "Learn Dot product" (#15) opened a Teacher lesson that honoured "I already know matching components" and "explain before you quiz me" (#19-24), explained projection well, used an interactive figure with a prediction (#25-31), and asked a fair check (#34-39). Asking a question by Ask after a miss worked well (#70-75).

**Stuck or misread:**
- No teaching offer at the start; "A step further · Eigenvalues…" read as one, Begin gave a question (#2-4).
- "I'm stuck" invites "Write what you can, or what's confusing you" (#6). The person wrote what confused them; it was graded "Not yet" and a follow-up question was prepared (#10). The words did reach the diagnosis ("explicitly identifies the missing bridge", #16), but nothing taught.
- After the eigenvalue miss, the lesson on offer was "Learn Dot product (about 15 min)" (#13), and after a variance miss "Learn SVD definition" (#68): never the topic just missed, and with no reason shown.
- **Leaving and coming back failed.** "Close" said nothing (#42). The lesson stays open in the vault (`lessons.closed_at` empty), but the default Today has no "Continue your lesson": the card that does it renders only in the classic shell (UX-14). The person looked in "Something else would help", Library's Continue and Progress, and gave up (#48-55).
- The Today offer that followed said "Learn Eigenvalues and eigenvectors now? (about 15 min) … [Or: SVD definition] [Or: Variance…] [Not now]" over a block row "A lesson you could take · about 1 min" (#56).

**Not in the report:** each lesson turn took 31 to 83 seconds with "The teacher is writing…" and no estimate or cancel (#16-24, #39); after Send the person's own reply vanished from the screen until the teacher answered (#20-24; "I cannot see my own words", UX-22). Behind the lesson, the feedback still showed "Router: no question · drawn by LLM · no question 68%, … floor 2%" (#16; F14). The lesson panel lists "doctrine teacher_doctrine_v1 / route chatgpt_medium · gpt-6.1-sol / 0 forecast(s)" under "inspector" (#23). The figure's button is labelled with its authoring brief ("◇ “Hold the vector a=(3,2) fixed while the learner rotates…”", #25). The status line read "stuck prompt" (#6), a screen-reader string.

**Could not find:** a lesson to resume, a list of lessons taken, a "teach me this" for the idea just missed.

### 2.3 workbench-1: steps, the help ladder, a figure on purpose

**Wanted:** to work in steps, check work part-way, take the smallest help, ask for a picture, and see what help cost.

**Got there:** "Work in steps" sat beside the answer box (#5); steps saved ("saved · just now"); three problems worked in steps were graded fairly and the grader accepted a non-textbook route (#58-76). The figure asked for on purpose arrived in about twenty seconds with "◐ building an interactive version · keep working · it stays here in Ask" and a prediction to make (#36-40). A written question about the same idea gave the nudge the person wanted (#45-53).

**Stuck or misread:**
- The first click on "check my work", "help" and "+ a step" did nothing (#8, #13, #28); the printed keys did (#14, #25, #29). UX-19.
- The help ladder lays out its levels well ("1 a question about your approach … hint", "4 work a piece of it for me … worked help ◌", "▸ suggested: 1 … (why?)", #14-15). Levels 1 and 2 each took about thirty seconds and ended "I couldn't write a hint that fits here; press Hint again or use the item's hint." (#16-23). The workbench has no "Hint" button and no item hint to use. The failed line then stayed beside the step through every later success (#27-58). UX-20.
- The check said "≈ model's reading, not checked" and "1 hint (a check) → practice with help ◌ (not yet checked on your own)" (#27): the person could not tell whether the line was right.
- The key bar's "?" typed a question mark into the step (#32; the submitted answer ends "= 0.?", #63).
- With Ask open, Ctrl+Enter did not submit and Escape did not close Ask (#54-57).
- The written reply appeared above the figure; the person scrolled down for it twice (#47-52).
- Help tallies disagree: the work area said "help used: a check", feedback details said "1 question to the tutor counted as a hint here", the figure was in neither (#61-64). The main feedback surface said nothing about help.
- Retrying the helped question later: it opened with "help used: none", the person answered alone, and feedback then said "Counted as practice with help: the tutor had already shown part of this answer." (#88-93). Told after, not before (O6).

**Could not find:** a history of helped questions, when an on-your-own retry comes, switches for pictures or step working (Settings, #94-99).

### 2.4 exam-1: a practice exam five days out

**Wanted:** to know whether "on track" means ready, sit a practice exam, get a short check after a miss, and see the last five days.

**Got there:** readiness's basis, partly: "predicted recall 84% · target 80%", "113 attempts · 3 / 3 facets examined · 1 certified", "≈ 2 qualifying attempts outstanding … roughly 1 day" (#3-4).

**Stuck:** no practice exam anywhere (section 0). "Practise for this goal" gave one ordinary dot-product question (#9). The quiz uploaded as ordinary reading (the person did not open More options this time) and opened in the Reader (#18-19). The forecast panel was "pooled Brier", "censored", "calibration duel" and an empty track record (#5-7). "plan around my week" gave "your scenario — 7 days/week … roughly 1 day … your what-if, not a system forecast · saved to your forecast ledger" (#29-30). The to-do list showed "measured ready 80%" and "87%" under "2 facets need work … below target" (#31).

**Not in the report:** the readiness screen also says "100% toward target" beside "⚠ 2 facets have enough evidence mass but remain below target" (#3). The bare "1 day" under the goal card that the person read as progress is the streak (`streakLine`, `D/app/todayPlan.ts:287`), printed with no word.

**Could not find:** a practice exam, a place for the solutions, a five-day plan, a date editor. The short check after a miss was not reached.

### 2.5 returner-1: back after three weeks

**Wanted:** to know what waits, what was forgotten, to deal with a passed goal, do ten minutes, set ten minutes a day, see the week.

**Got there:** the welcome is the best screen in this wave: "Welcome back. A short catch-up today: 2 minutes of the most useful questions. Nothing else is waiting on you." and under why? "You were away 22 days. The rest comes back over the next days, a little at a time." (#1-4). Two fair questions, a specific gap found (the missing "nonzero"), and "9 minutes this session · 2 questions … (on your own)" at the end (#25-54). The person would come back.

**Stuck or misread:**
- Three sizes on the welcome screen: 2 minutes, a lesson offer "about 15 min", the 25-minute chip (#1-2).
- Begin did nothing visible: it turned into "Continue ↵" and the screen stayed, because the plan's first block was the lesson offer (#21-22); Continue then opened a question after about fifteen seconds (#23-24). UX-21.
- After the second answer, feedback was held behind "Preparing a question on this…" while Next said "today's plan is done" (#35-37); Next then opened a short check: "Feedback comes when this short check ends · hints are off for now" with "Stop diagnosing and teach me" and a three-part question (#39-48). "I did not expect more questions after 'today's plan is done'." The Today tab did nothing on the check (#46-47); Escape left it (#49).
- "Catch-up done. Nothing else is needed today." beside a full list of nine items "coming back later today" (#49-51).
- why? showed "This pick had a 47% chance. Based on attempt:01M7V958…; … Receipt: learnloop router log --decision 01M7V9…" (#4).
- Feedback's diagnosis spoke about the person in the third person and in internal words: "The current trace…", "The blind-graded failure is specifically…", "The learner knows the nonzero restriction…" (#37).

**Not walked:** the goal whose date has passed (fixture, section 0). No goal edit or close was found (#12-18).

### 2.6 expert-1: knows the material, wants to test out

**Wanted:** to say "I know this", be tested out quickly, get hard questions, dispute a grade, fix a topic's name.

**Got there:** an expert-grade Ask answer on repeated eigenvalues (#26-36); and, once found, "✓ I know this" gave "assumed (not tested)" with its first review date (#66-67), honest about evidence (O2 passes).

**Stuck or misread:**
- No practice question in 79 steps. Question writing failed once and was retried (#18-21); later Today said "Everything you've read has its questions. Reading on brings more." while nothing could be practised (#46-47). The person read it as "practice is ready".
- "I know this" lives behind a button named `lo_goal_covariance_and_variance_mastery_check_318563eb`, in Progress, in edit mode (#64-65).
- "Check what I already know" finished at once: "completed · 0 / 4 questions · 0.0m of 8.0m", then "already assumed known" (#68-69) and, on a topic not marked, "not enough answers to skip it, so it starts as learning" (#76-77). It never asked a question. UX-18.
- "add it" made a topic from the goal sentence's phrase; the book's own "Covariance matrices" topic appeared later beside it, unconnected; no rename or merge (#56-62).
- The app's tabs scrolled off after reading an Ask answer (#41); the palette shortcut in the key bar got the person out (UX-15).
- On the check screen, clicking Progress moved the highlight and left the screen (#70-72). UX-27.

**Could not find:** a chapter-wide "I know this", a check that asks, a harder question, a grade to dispute.

### 2.7 notes-1: own notes as sources

**Wanted:** to bring in a linked Markdown notes folder, a lecture transcript and a flashcard deck, keep their words, practise from them, see where a question came from, see whether a planted error is noticed, know what an outside edit does, and get the material out.

**Got there:** the transcript opened in about four seconds with its wording (#20); a Reader quick check on the lecture was fair and "show me the passage" opened its paragraph (#84-92), so the source of a Reader quick check can be seen. Asking about the wrong note gave a precise correction citing the lecture and the flashcards (#41-48).

**Stuck or misread:**
- No folder import: the chooser refuses a folder (#7-8); "Notes & files" is the vault's own file browser (yaml, `learning_object`, `practice_item`, #3); the person added one note on its own (#31).
- The flashcard file was accepted as a "book" and rendered as one paragraph, fronts and backs run together (#23-27).
- `[[Symmetric matrices]]` showed as literal brackets; the note's links did nothing.
- **The planted error was not noticed** by LearnLoop; it was found only because the person asked (#41-46), and the wrong sentence stays in the note.
- Today never served a question (#36-50, #96).
- Progress went from 0 to 5 topics with no word that anything arrived (#64, #80).
- After "show me the passage" the app's tabs scrolled off again (#92-95); "← Library" brought them back. UX-15.
- Export and sync: the palette found nothing (#66-69); "Data" is database tables (#75); "Study-map changes, 27 waiting" shows a count (#77).

**Could not find:** a folder or deck import, a Today question from a note, what happens when a note is edited outside, a way out.

### 2.8 project-1: a project, not a course

**Wanted:** to say "I am building a PCA image compressor", learn what the project needs in its order, ask from a coding problem, know when the project is done.

**Got there:** after adding the chapter, the goal box took the project in its own words, open-ended (#18-20). Ask was excellent: what to skip (#32-38), a check of the person's own tiny example (#43-46), why the covariance matrix is symmetric from their own `C = A @ A.T / N` (#49-56), and practical finish checks (#62-68). Help arrived inside the task (M1, J12 pass).

**Stuck or misread:**
- No project-first start (#3-9; F23).
- The deliverable said "3 topics from your books" over three rows each "? not in your library yet · added as a new topic" (#24), and the goal details said "None of the topics in your books is part of it so far: add or read a book that covers it" (#27). UX-17 and F30.
- Ask needed a selected passage before it would take a question (#29).
- Four Ask waits of 38 to 46 seconds each (#33-35, #42-44, #50-52, #63-64); answers landed below the fold of a narrow rail and the first scroll moved the chapter (#36-38; F26).
- The reading path's reason changed from enrichment to prerequisite with "◇ Use this section as background…" and nothing about the project (#58).

**Could not find:** a project checklist, the finish checks in the goal, a Today question.

### 2.9 twocourses-1: two courses, one budget

**Wanted:** a second course of its own with an open goal, a plan that splits twenty minutes between the courses with algebra first, practice that says when it switches course, progress per course, and a day of only the second course.

**Got there:** the second reading sits beside the first in the Library (#16); Ask on it stayed inside the article (#73-81); its Reader quick check worked (#83-85).

**Stuck or misread:**
- There is no course: no course choice on Add, one map called "linear-algebra" on Progress (#65-68), no course label on any plan row (#18-21).
- The new goal's deliverable said "Elevator paradox ? not in your library yet" while the Library held it (#15); the Reader later said "No active goal covers this book" (#71).
- why? split the minutes into "keeping what you know" and "going further", with "This pick had a 33% chance. Receipt: learnloop router log --decision 01M7V…" (#20). No 20-minute chip.
- "edit why" took the priority sentence but nothing changed (#28-31).
- After Submit on one question the practice screen went blank but for "esc back" for about thirty seconds (#48-50), then feedback held behind "One moment…" and "Preparing a question…" (#50-53).
- Asking "Something else would help" for probability only, with the wish typed in its box, and choosing "Another question" opened an algebra short check (#88-91). The typed wish went nowhere the person could see (O4).

**Could not find:** a course, minutes per course, a probability-only day, tomorrow's split.

### 2.10 What helped one and hindered another

- **Ask in the Reader** was the strongest thing in this wave for project-1, expert-1, notes-1, twocourses-1 and student-2: grounded, specific, in the person's own setting. It cost each of them 26 to 46 seconds per answer, an answer that landed out of view, and twice the app's tabs (F26, UX-15).
- **Today's cause line** gave every new library a reason, but the reason was never followed by a question on the first day (F20).
- **The welcome after a gap** (returner-1) and **"Resume your answer"** (phone-3) are what the overhaul should copy: one sentence, the gap named, nothing owed.
- **The goal box** in the Reader took a project, an open course and an exam in the learner's words, and then told every one of them that their own book's topics were "not in your library yet" (F30).

---

## 3. The journeys no one had walked

| Journey | Exists | Found | Promised and did | Fails |
|---|---|---|---|---|
| **Lessons** | yes | from Today's offer and "Something else would help" only; no "teach me" on feedback, no resume, no list | taught well; Close kept the lesson but no way back (UX-14); lessons offered on other topics than the one missed (F21) | N-D, H3, J10, O7 (partly), N-F |
| **Workbench and help ladder** | yes (in practice, "Work in steps") | at once | levels and their kind shown before taking; levels 1-2 gave nothing twice (UX-20); first clicks ignored (UX-19); "counts as a hint" said up front | N-F, H9, O11, J5 |
| **Figures on purpose** | yes | via "ask about this step" and Alt+Enter | building → built in about 20 s with a clear line; clipped in the panel; reply placed above it | U9 pass; N-F (placement) |
| **Practice exam** | only for a goal created with a held-out pool | not for exam-1's goal; no way to add one; a stored past exam can't be sat | nothing to sit (F22) | N-D, M10, J3 |
| **Short check after a miss** | yes | arrived on its own (returner-1, twocourses-1) | arrived after "today's plan is done" and on a request for something else; "Stop diagnosing and teach me" present; Today tab did nothing on it | H4, O2, I8 |
| **Coming back after a gap** | yes | at once | a short catch-up, nothing owed (M4, U12 pass); the passed-goal state not walked | J1 (three sizes on one screen) |
| **"I know this"** | yes (per topic) | behind an `lo_…` button in Progress edit mode | honest "assumed (not tested)"; the check that should follow asked nothing (UX-18) | N-D, O9 (partly), N-F |
| **Own notes as sources** | single files only | — | a transcript works; a folder, a deck and note links do not; the planted error went unnoticed; Reader quick checks show their passage; Today questions never came | M9, N-D, O10 |
| **A project as a goal** | yes (an open goal in words) | after a book is added | taken in words; then "None of the topics in your books…" | M2, M10 |
| **Two courses in one day** | no course concept | — | one plan, one map, no split, no course day | M2, I11, J7 |

**The owner's Nov 14 rule** (a control that promises teaching opens a Teacher lesson; Ask stays for questions): every control the walks used followed it. "Learn X" opened a lesson (lesson-1 #15), "Learn X (on the desktop)" said where it lives (phone-3 #44), and Ask stayed Ask. Two gaps against its spirit: "I'm stuck" invites the learner to say what confuses them and then grades it (lesson-1 #6-10), and the lesson on offer after a miss is on another topic (lesson-1 #13, #68). "Stop diagnosing and teach me" was shown on both short checks but not pressed.

**What each level of help cost, and whether the screen said so** (workbench-1): the ladder labels levels 1-3 "hint" and 4-5 "worked help ◌" before they are taken, and "check my work · counts as a hint" says it on the button. What it means afterwards was not said: the work area, feedback's details and the later retry each counted differently, and the retry's "practice with help" came after the answer (F24).

**Figures, every state met:** waiting ("◐ building an interactive version · keep working · it stays here in Ask"), built (with a prediction and a checked label "checked by LearnLoop: 5 checks", lesson-1 #25), assumptions ("assumes · AI-written"). Failed, refused, stale, withheld and spend states were not met.

---

## 4. The scorecard, updated

Discover / Understand / Recover / Flow, as in the first part (section 6 there). "Before" is the first wave; "after" this wave.

| Journey | Before | After | Who (after) | Still fails |
|---|---|---|---|---|
| First run: add a file and read | pass / pass / pass / pass | pass / pass / pass / pass | all desktop | — |
| First run with no file (a wish) | fail / fail / partial / fail | fail / fail / fail / fail | beginner-2 (gave up), project-1, notes-1 | J1, N-D, M2 |
| Say the exam or goal | partial / fail / partial / pass | partial / fail / partial / pass | student-2, project-1, twocourses-1, expert-1 | N-D, H2, O2 (UX-17, F30) |
| See and change goals | fail / partial / fail / — | fail / partial / fail / — | seasoned-2, returner-1, exam-1 | N-D, H3, O9 |
| Bring past exams | partial / fail / fail / — | partial / partial / fail / — | student-2, exam-1 | J3, M10 (UX-5 fixed) |
| Today with built questions | pass / partial / pass / partial | pass / partial / partial / partial | seasoned-2, lesson-1, workbench-1, returner-1, twocourses-1 | O2 (UX-16), UX-21 |
| Today on a new library | pass / fail / fail / fail | pass / partial / partial / fail | student-2, retainer-2, expert-1, project-1, notes-1 | J3, N-F (UX-13, F20) |
| Practice and feedback | pass / pass / partial / pass | pass / partial / partial / partial | seasoned-2, lesson-1, workbench-1, returner-1, twocourses-1, phone-3 | O9 (F37), O6 (F24), N-F (waits) |
| Ask in the Reader | partial / partial / pass / pass | pass / partial / partial / partial | five walks | U3, N-F (F26), UX-15 |
| Ask on feedback | fail / fail / fail / fail | pass / pass / pass / pass | seasoned-2, lesson-1 | (UX-3 fixed) |
| Cross-book: find-section, side by side | pass / pass / partial / pass | pass / pass / partial / pass | retainer-2, notes-1 | UX-24 |
| Keeping things | not testable / fail (phone) | partial / partial / partial / fail | retainer-2, phone-3 | M9, O3 (F34) |
| The plan's size and load | fail / fail / fail / partial | fail / partial / fail / partial | seasoned-2, retainer-2, returner-1, twocourses-1 | I11, M4, J7 (F31) |
| The stop offer | pass / fail / pass / pass | pass / fail / pass / pass | seasoned-2, returner-1, phone-3 | O2 (UX-16) |
| Progress | pass / fail / — / — | pass / fail / — / — | six walks | O3, H2 |
| Mistake history | fail / fail / — / — | fail / fail / — / — | seasoned-2 | I9, N-D |
| Settings | pass / fail / — / — | pass / fail / — / — | seven walks | J7, O3 |
| Phone pairing | partial / fail / pass / — | partial / fail / pass / — | phone-3 | J1, N-F, O3 |
| Phone session and resume | pass / partial / pass / pass | pass / partial / pass / pass | phone-3 | O3 (F14, UX-23) |
| Phone reader | pass / partial / pass / — | pass / pass / pass / — | phone-3 | M3 (one "Document") |
| Phone capture | pass / fail | pass / pass | phone-3 | — |
| **Lessons** | not seen | partial / pass / fail / partial | lesson-1, returner-1 | N-D, J10, N-F (UX-14, UX-22) |
| **Workbench and help ladder** | not seen | pass / partial / partial / fail | workbench-1 | N-F, J5, O11 (UX-19, UX-20) |
| **Figures on purpose** | not seen | partial / pass / pass / partial | workbench-1, lesson-1 | N-F (placement) |
| **Practice exam** | not seen | fail / — / — / — | exam-1, student-2 | N-D, M10 |
| **Short check after a miss** | not seen | — / partial / pass / partial | returner-1, twocourses-1 | H4, I8 |
| **Coming back after a gap** | not seen | pass / pass / pass / partial | returner-1 | J1 (three sizes), UX-21 |
| **"I know this" and test out** | not seen | fail / pass / partial / fail | expert-1 | N-D, N-F (UX-18) |
| **Own notes** | not seen | fail / partial / — / fail | notes-1 | M9, N-D |
| **A project as a goal** | not seen | partial / partial / — / pass | project-1 | M2, M10 |
| **Two courses in one day** | not seen | fail / fail / — / fail | twocourses-1 | M2, I11 |

---

## 5. Defects

Things that are simply broken. Severity as in the first part: S1 the journey cannot be finished or the screen misleads about evidence; S2 it finishes only after a long detour or a guess; S3 friction. Each was checked against the fidelity table and the unreachable routes.

### 5.1 The list

| Id | Sev | What the person saw | Walk and step | Cause (where the code shows it) | Size |
|---|---|---|---|---|---|
| UX-13 | S1 | A new learner's first chapter gets no questions: "Couldn't get questions ready…", or "on their way" that is already false. The inventory window's first attempt failed in three of six first documents (one never retried), and the synthesis pass failed at 10,352 output tokens against its 10,000 limit with no retry offered to the learner, who had moved on | student-2 #30-37 (and the vault at 00:40), expert-1 #18-21, retainer-2 #85 | Output budgets sit at the size the live model usually writes: `inventory_output_tokens = 3000`, `synthesis_shard_output_tokens = 10000` (`S/config/schema.py:851-855`); a pass over its limit is refused (`S/content/synthesis/source_set_synthesis.py:1700-1717`, `pass_output_limit`, `check_pass_output`). Measured outputs: inventory 2,672 to 3,254; synthesis 7,090 to 10,352 | M, backend |
| UX-14 | S1 | "Close" on a lesson keeps it open, but the default Today has no way back into it; the person searched three places and gave up | lesson-1 #42-55 | The lesson row stays open (`lessons.closed_at` empty); `ContinueLessonCard` renders only in the classic `D/screens/TodayScreen.tsx:746`, never in `TodayPlace` | S, frontend |
| UX-15 | S2 | In the Reader, the app's top bar and tabs scroll off the window; Escape and scrolling do not bring them back; the person stopped (student-2) or needed the palette or "← Library" | student-2 #83-88 (screenshot `0087`), expert-1 #41, notes-1 #92-95 | Programmatic scrolls in the Reader scroll the document root as well as the rail: `scrollIntoView` on the follow-up composer (`D/screens/reader/AskRail.tsx:401`) and on passages (`D/screens/ReaderScreen.tsx:1494`, `:3983`, `:4006`). The harness record predicted it ("Seen on the way"); confirm in the WebKitGTK window | S, frontend |
| UX-16 | S2 | "Done for today. Nothing else is needed today." after one answer while three planned blocks were left, and beside nine items "coming back later today" | seasoned-2 #59, returner-1 #49-51 | Stage 3's finished-plan line (`D/app/todayCause.ts`) cannot tell an engine stop with work left from a day with nothing left; the plan's `stopReason` is free text (stage 3 record) | S, needs one plan field (a stop with work left) |
| UX-17 | S2 | Goal details say "None of the topics in your books is part of it so far: add or read a book that covers it" beside a deliverable saying "3 topics from your books", and for a chapter that covers the goal | project-1 #24 vs #27, student-2 #42 | Stage 2's `emptyGoalSentence` (`D/components/GoalBanner.tsx`) uses `total === 0`, which also holds when the goal's topics exist but have no questions yet | S, frontend |
| UX-18 | S2 | "Check what I already know" ends at once, "completed · 0 / 4 questions", and says "not enough answers to skip it" without having asked anything | expert-1 #68-69, #76-77 | `S/diagnosis/quick_check.py` `_candidate_items` finds no never-seen servable item and the session ends "completed"; `D/screens/CalibrationScreen.tsx:348` words the result as a lack of answers | S, frontend wording + a "nothing to ask yet" reason from the sidecar |
| UX-19 | S2 | In "Work in steps", the first click on "check my work", "help" or "+ a step" does nothing; the key does | workbench-1 #8, #13, #28 | Likely: leaving the step box re-renders it (its text vanishes from the screen, #8) and moves the buttons under the pointer. Confirm in the WebKitGTK window | S, frontend |
| UX-20 | S2 | Help levels 1 and 2 each wait about 30 s and end "I couldn't write a hint that fits here; press Hint again or use the item's hint." The workbench has no Hint button and no item hint; the line then stays beside the step | workbench-1 #16-37 | `S/hints/service.py:550` (`NO_FITTING_HINT_MESSAGE`, `:564`) after the writer's rounds fail their checks (`contract_failed`). The level was the learner's, so the unreachable hint chooser is not the cause; why the checks failed twice is not shown | S (message, clearing), M (why the smallest hints fail) |
| UX-21 | S2 | Begin does nothing visible when the plan's first block is a lesson offer: it turns into "Continue ↵" on the same screen | returner-1 #21-23 | The session starts but the first block waits for the offer's Start / Not now | S, frontend |
| UX-22 | S3 | After Send in a lesson, the learner's reply disappears until the teacher answers (up to 83 s) | lesson-1 #20-24 | `D/screens/LessonScreen.tsx:278-283` clears the box and shows nothing while the turn runs | S, frontend |
| UX-23 | S3 | Phone feedback prints a raw reason code under the score: "valid_alternative_unverified" | phone-3 #10 (faked models raised it; the print is real) | `M/practice/FeedbackScreen.tsx:225` renders `manualReviewReason` as text (`S/outcome_contract.py:29`) | S, phone frontend |
| UX-24 | S3 | Web-page sections are named by their HTML ids in the contents and on the side-by-side button ("modeling-the-elevator-problem", "external-links") | retainer-2 #16, #45 | Section titles fall back to anchor ids at extraction or in the render view; not traced | S-M |
| UX-25 | S3 | The display equations the extraction keeps show as raw `\begin{equation*} A = QDQ^{-1} = QDQ^T. \end{equation*}` in the book's text | student-2 #65, retainer-2 #38-44, project-1 (37 screens), expert-1 | The kept environments are not inside `$$`, so the Reader's Markdown renderer leaves them as text. Rendering them is frontend-only; UX-11 (most display math dropped) stays the extraction fix | S, frontend |
| UX-26 | S3 | Ask's "§ from the book" quote shows every formula twice ("matrix 𝑄 Q", "Q T =Q −1") | student-2 #87 | The quote is the selection's rendered text with both KaTeX layers (the harness record saw the same in the capture card) | S, frontend |
| UX-27 | S3 | On a practice check or the "Check what I already know" screen, clicking a place tab moves its highlight and leaves the screen as it was | expert-1 #70-72, returner-1 #46-47 | The first part's inventory 2.1 already noted it (`App.tsx`, the place buttons during an exam or calibration): the places do not leave a check | S, frontend |

UX-1 stays "fixed" in the ledger for what it fixed (Retry no longer fails the same way); UX-13 is what remains. UX-11 (display math dropped at extraction) is now seen by people (student-2, retainer-2, project-1, expert-1): it should come forward from the Reader redo, with UX-25 as its quick part.

### 5.2 Checked and dismissed

| Candidate | Verdict |
|---|---|
| Deleting an annotation failed (retainer-2 #75-78) | Harness: buttons inside a clickable card are not numbered. |
| "Open another library…" on a notes folder: "LearnLoop could not confirm whether this action completed" (notes-1 #15) | `select_vault` is emulated by the harness. The label inviting a notes folder is kept under F27. |
| "Says why" grades too strict or too generous (seasoned-2 #48, twocourses-1 #50) | Fixture rubric (`make_vault.py:108`). What the person could do about it is F37. |
| Exam date Dec 11 vs "five days" (exam-1); goal "due today" not passed (returner-1) | Fixture dates. |
| Phone "4 / 4" beside "(1/3)", "(0/1)" (phone-3 #10) | Faked models. Only the raw reason is kept (UX-23). |
| "Something else is covering that spot" on Ask's follow-up box (student-2 #70, project-1 #41) | The harness's click hit an overlapping element; typing into the already focused box worked. Not settled; a check in the real window is listed in section 9. |
| The goal box's "not in your library yet" for a book's own topics | Partly the unreachable embeddings and partly no topics built yet; the words are F30, not a defect. |
| Reader Ask "Couldn't reach LearnLoop's model. Your question is kept. · try again ↵" (student-2 #73) | The ChatGPT plan was overloaded (vault: "server_is_overloaded"). The app recovered well. |
| The intent box always "couldn't choose, so this asks" | The Decider route is unreachable in the walks. |
| Long gaps of five to six minutes | Walker latency. |

### 5.3 Drafted ledger rows

Added to `docs/reviews/refactor-bug-ledger.md` under "From the UX journey audit's walks". The stage numbers are section 8's.

```markdown
| UX-13 | UX journey audit part 2, walks student-2 #30-37, expert-1 #18-21, retainer-2 #85 (high) | A new learner's first web chapter often gets no questions on the live route. The inventory window's first attempt fails at its 3000-token output budget (outputs measured 2,672 to 3,254; Retry now recovers it), and the synthesis pass fails over its 10,000-token limit (10,352 measured) with "A synthesis pass exceeded its output budget."; nothing retries it and Today keeps saying "on their way" until the learner looks again. | new: an inventory window and a synthesis pass whose output is a little over today's limit complete (or retry once on their own) instead of failing the build | Budgets as safety ceilings above what the live model writes, not at it (`config/schema.py` `[ingest.budgets]`; `content/synthesis/source_set_synthesis.py` `pass_output_limit`, `check_pass_output`); one automatic retry; Today's cause line follows the build's real state | open; stage 2 of the second part |
| UX-14 | UX journey audit part 2, walk lesson-1 #42-55 (high) | A lesson the learner closes stays open but cannot be reached again in the default shell: "Continue your lesson" (`ContinueLessonCard`) renders only in the classic `TodayScreen`. | new: `TodayPlace` with an open lesson shows "Continue your lesson on X" and opens it | Render the continue card in the simple Today; "Close" says the lesson is kept and where | open; stage 3 of the second part |
| UX-15 | UX journey audit part 2, walks student-2 #83-88, expert-1 #41, notes-1 #92-95 | In the Reader, scrolling an element into view (Ask's follow-up composer, a shown passage) also scrolls the window, so the top bar and the place tabs leave the screen and no scroll or Escape brings them back. | new: after the follow-up composer and a passage are scrolled into view, the shell's top bar is still in the viewport | Scroll only the Reader's own panes (`scrollIntoView` in `AskRail.tsx` and `ReaderScreen.tsx` within their scroll containers; the shell root not scrollable); confirm in WebKitGTK | open; stage 3 of the second part |
| UX-16 | UX journey audit part 2, walks seasoned-2 #59, returner-1 #49-51 | Stage 3's "Nothing else is needed today." shows when the plan's engine stopped with planned blocks left, and beside a list of items still coming back today. | new: a plan closed by an engine stop with blocks left never shows "Nothing else is needed today" | One plan field for a stop with work left; Today says LearnLoop stopped here and offers Keep going | open; stage 3 of the second part |
| UX-17 | UX journey audit part 2, walks project-1 #24-27, student-2 #42 | Stage 2's empty-goal sentence says "None of the topics in your books is part of it so far: add or read a book that covers it" when the goal's topics exist (added, or in the open book) but have no questions yet, beside a deliverable that counts them. | new: `GoalBanner` with goal topics and no practicable items says the questions are still to come, not that the books lack the topics | Tell "no topics" from "topics without questions yet" | open; stage 3 of the second part |
| UX-18 | UX journey audit part 2, walk expert-1 #68-77 | "Check what I already know" ends at once as "completed · 0 / 4 questions" and says "not enough answers to skip it" without asking any question, when no servable question exists for the topic. | new: a quick check with no candidate items says nothing can be asked yet and why, and is not "completed" | A "nothing to ask yet" end reason from `diagnosis/quick_check.py`; its own words in `CalibrationScreen` | open; stage 3 of the second part |
| UX-19 | UX journey audit part 2, walk workbench-1 #8, #13, #28 | In "Work in steps", the first click on "check my work", "help" or "+ a step" after typing in a step does nothing; the keyboard shortcut works. | new: a click on each of the three controls straight after editing a step acts once | Keep the controls in place when the step box loses focus; confirm in WebKitGTK | open; stage 3 of the second part |
| UX-20 | UX journey audit part 2, walk workbench-1 #16-37 | Help levels 1 and 2 each end, after about 30 s, "I couldn't write a hint that fits here; press Hint again or use the item's hint." in the workbench, which has no Hint button or item hint; the line stays beside the step after later help succeeds. | new: the workbench's failed-hint line names only controls it shows and clears on the next help | Surface-specific words and clearing (S); find why both smallest levels failed their checks (M) | open; stage 3 of the second part (words), stage 8 (why) |
| UX-21 | UX journey audit part 2, walk returner-1 #21-23 | Begin does nothing visible when the plan's first block is a lesson offer: the button becomes "Continue ↵" and the screen stays. | new: Begin with a lesson offer first either opens the offer's choice or goes to the first practice block | Begin answers the offer (or skips it) and opens something | open; stage 3 of the second part |
| UX-22 | UX journey audit part 2, walk lesson-1 #20-24 | After Send in a lesson, the learner's reply disappears from the screen until the teacher's turn returns (31 to 83 s). | new: a sent reply shows in the conversation, marked as sent, while the turn runs | Show the reply at once | open; stage 3 of the second part |
| UX-23 | UX journey audit part 2, walk phone-3 #10 (faked models) | Phone feedback prints the raw review reason under the score ("valid_alternative_unverified"). | new: a feedback with a review reason shows plain words or nothing | Map known reasons to words; never print the code | open; stage 3 of the second part |
| UX-24 | UX journey audit part 2, walk retainer-2 #16, #45 | Web-page sections are named by their HTML ids ("modeling-the-elevator-problem", "external-links") in the contents and on the side-by-side button. | new: the elevator sample's sections carry their headings as titles | Use the heading text for a section's title | open; stage 3 of the second part |
| UX-25 | UX journey audit part 2, walks student-2 #65, retainer-2 #38-44, project-1, expert-1 | The display equations kept by extraction show as raw `\begin{equation*}…\end{equation*}` text in the Reader. | new: a block holding a bare equation environment renders as display math | Render bare display environments in the Reader's Markdown (frontend; UX-11 stays the extraction fix) | open; stage 3 of the second part |
| UX-26 | UX journey audit part 2, walk student-2 #87 | Ask's "§ from the book" quote of a passage with math shows each formula twice ("matrix 𝑄 Q"). | new: a quoted selection over KaTeX keeps one form of each formula | Quote the source text of the selection, not both rendered layers | open; stage 3 of the second part |
| UX-27 | UX journey audit part 2, walks expert-1 #70-72, returner-1 #46-47 | On a practice check or the "Check what I already know" screen, a place tab moves its highlight but the screen stays. | new: a place tab on these screens leaves them (asking first if an answer would be lost) | Make the tabs leave, or not look clickable there | open; stage 3 of the second part |
```

---

## 6. Design findings, ranked by learner impact

Works as built, fails a criterion. The first part ended at F19; these continue from F20.

**F20 (S1). No first-day learner got a question from Today.** student-2, retainer-2, expert-1, project-1 and notes-1 all added a source and none was served a practice question from Today in the whole walk (student-2's only practice was what it asked Ask to set, #63-82). Expected: a first short session from what they read. Happened: the cause line, then "Everything you've read has its questions. Reading on brings more." (expert-1 #46), read as "practice is ready"; questions come "as you read" sections and the line does not say so. Fails J3, M4, N-F. Inventory: the states exist (2.6); the first session does not. UX-13 is part of it, not all of it.

**F21 (S1). Lessons: offered on the wrong topic, impossible to resume, and never offered for the miss.** lesson-1 #6-13, #42-56, #68. Expected: "teach me this" where they struggled, and a way back to a lesson left halfway. Happened: "I'm stuck" graded the confusion; "Learn Dot product" after an eigenvalue miss and "Learn SVD definition" after a variance miss, with no reason; the closed lesson unreachable (UX-14); no list of lessons. Fails O7 (spirit), N-D, J10, M7. Inventory: resume exists in the classic shell only (2.13).

**F22 (S1). A practice exam can't be sat.** exam-1 #9-23, student-2 #20-26. Expected: sit last year's quiz with answers hidden, then a marked result. Happened: a goal without a held-out pool has no practice exam and no way to add one; a past exam is kept but has no Start and no place for its solutions. Fails N-D, J3, M10. Inventory 2.3, 2.6; first part F8.

**F23 (S1 for the beginner). Nothing starts without a source.** beginner-2 (gave up), project-1 #3-9, notes-1 #3-15, expert-1 #2. Expected: say the aim first. Happened: every first screen asks for a file; the typed lesson start is classic-only; "personalized ●" on an empty library. Fails J1, N-D, M2. First part F3.

**F24 (S2). "With help" is counted three ways and told after.** workbench-1 #27, #61-64, #88-93. The work area, feedback's details and the later retry each counted help differently; the main feedback said nothing; the retry showed "help used: none" and then "Counted as practice with help". Fails O6, O11, N-C. Owner decision 2 (first part 2.5).

**F25 (S2). Waits with no amount, and screens that go blank.** The list for the waiting-indicators stage (section 8, stage 1) to be checked against:

| Where | Walk and step | How long | What the screen showed |
|---|---|---|---|
| Today → question (Begin, Continue) | lesson-1 #3-4; workbench-1 #2-3; returner-1 #23-24; lesson-1 #60-61 | about 15 to 20 s | "Busy", "a region is loading"; returner-1 "opening…" |
| Question → feedback (Submit) | seasoned-2 #46-47; lesson-1 #8-10 (33 s), #46-47, #64-65; returner-1 #32-35 (about 40 s: "It is still reading my one-sentence answer"); workbench-1 #58-60 (about 24 s) | 15 to 40 s | "Reading your answer…" |
| Question → feedback, blank | twocourses-1 #48-50 | about 30 s | only "esc back": the question disappeared |
| Feedback held behind a follow-up | lesson-1 #10-13; returner-1 #35-39; twocourses-1 #50-53 | 10 to 30 s | "Preparing a question on this…", the full answer "One moment…", while Next said "today's plan is done" |
| Reader Ask writing | student-2 #34-35 (42 s), #64-66, #80-81; expert-1 #28-31 (46 s); project-1 #32-35 (43 s), #42-44, #49-52, #62-64 (46 s); notes-1 #42-43; twocourses-1 #76-79 (37 s) | 26 to 46 s each | "◐ looking in your books, then writing an answer … · cancel"; the answer then lands out of view |
| Lesson opening and each turn | lesson-1 #15-18 (about 40 s), #20-24 (83 s), #31-32, #38-39 | 30 to 83 s | "The teacher is writing…"; no cancel; the learner's reply vanished (UX-22) |
| Help ladder levels | workbench-1 #16-18, #22-23 | about 30 s each | "◐ writing a hint for your work… cancel", then the failure line |
| Work check | workbench-1 #25-26 | about 16 s | "reading your steps" |
| Figure | workbench-1 #36-37 | about 20 s | "◐ building an interactive version · keep working · it stays here in Ask" (the model to copy) |
| Goal details | seasoned-2 #14, exam-1 #3, returner-1 #12 | about 9 s | "Busy", then "loading trajectory…" |
| Goal box "make it ↵" | expert-1 #13-14, project-1 #20 | 9 to 20 s | "Busy" only |
| "Something else would help" and the lesson start | lesson-1 #12-16 | 20 to 28 s | "Busy" only |
| Question writing for a new source | student-2, retainer-2, expert-1, project-1, notes-1 | minutes | "on their way", "Writing questions…", no amount; notes-1's cards later "in about 4 min" |
| A Reader quick check being written | notes-1 #85 | about 20 s | "◐ writing a quick check for this section…" |

Fails N-F, U9, H1. What the waiting stage cannot do on the frontend alone: a progress amount for question writing (the sidecar knows windows and passes, the screen does not), a cancel for lesson turns (none exists), and the reason a wait is long (for example, feedback held for a follow-up question).

**F26 (S2). Answers land where the learner isn't looking.** student-2 #47-51, project-1 #36-38, notes-1 #44-46, workbench-1 #47-52. Ask's answer in a narrow rail below the question and passages; the first scroll moves the book; in the workbench the reply sits above the figure. Fails U1, U3, N-F. First part F10.

**F27 (S2). Own notes have no way in beyond single files.** notes-1. No folder or vault import, no deck, Obsidian links shown as `[[text]]`, the planted error not noticed, no word on outside edits, no export ("Data" is tables). Fails M9, N-D, O10. Inventory 2.6; the owner's persona 8.

**F28 (S2). "I know this" is honest but hidden.** expert-1 #42-67. Behind an `lo_…` button in Progress edit mode; the palette's "Check what I already know" points at an empty Progress. Fails N-D, O9.

**F29 (S2). Two courses don't exist as courses.** twocourses-1. No course to add a reading to, no course label on the plan, no per-course progress, no split of one budget, no "only this course today"; a typed wish under "Something else would help" was ignored (#88-91). Fails M2, I11, O4. Student audit finding 5 (SJ-6).

**F30 (S2). The goal box contradicts the library.** student-2 #14, project-1 #24, twocourses-1 #15, expert-1 #15, #56-62. "not in your library yet" for a book's own topics, "3 topics from your books" over rows "not in your library yet · added as a new topic", topics named from the sentence ("… Mastery Check") beside the book's own, with no merge. Fails O2, N-C, O9. SJ-7.

**F31 (S3). Several sizes on one screen.** returner-1 #1 (2 min catch-up, a 15-min lesson offer, the 25-min chip); lesson-1 #56 (a lesson "about 15 min" over its row "about 1 min"); seasoned-2 #70 ("About 10 minutes suggested" with 25 checked); no 20-minute chip (twocourses-1 #21); no phone choice under 10 (phone-3 #7). Fails O2, H4. First part F9.

**F32 (S3). why? shows raw ids and a terminal command.** returner-1 #4, twocourses-1 #20: "This pick had a 47% chance. Based on attempt:01M7V…; Receipt: learnloop router log --decision 01M7V…"; "maintain:" and "push:" lane words. Fails O3, J8 (the workings belong one step further, under details).

**F33 (S3). The router line is still on learner screens.** phone-3 #22, #40; desktop feedback, lesson-1 #16. Owner's call (first part F14).

**F34 (S3). Keeping things in the Reader is slow and its labels are internal.** retainer-2 #10-29, #73. About twenty actions for three saves; "help me remember" silent; "highlight exact", "interpretation exact", raw `**`. Fails M9, O3, N-F.

**F35 (S3). A web chapter is one "Document".** retainer-2 #32-42, phone-3 #36, project-1 #15. No contents, no first-section boundary. Fails M3.

**F36 (S3). Keys in the working space.** workbench-1 #32, #54-57. "?" types into a step; Ctrl+Enter does not submit with Ask open; Escape does not close Ask. Fails J5, H4.

**F37 (S3). A grade can only be disputed upward, and Ask promises what it can't do.** seasoned-2 #48-57. No way to say "this tick is too generous"; Ask answered "I would revise the score to 3/4" and nothing was recorded. Fails O9.

**F38 (S4). Small words.** The bare streak "1 day" (exam-1 #24, read as progress), the status "stuck prompt" (lesson-1 #6), "next block" (workbench-1 #92), the feedback's "The current trace…", "blind-graded failure", "The learner…" (returner-1 #37, lesson-1 #16), the lesson's "doctrine teacher_doctrine_v1 / route chatgpt_medium" (lesson-1 #23), the figure's brief as its button label (lesson-1 #25). Fails O3, M7.

**What worked, to keep.** The welcome after a gap (returner-1 #1-4). "Resume your answer" on the phone (phone-3 #22-25). "Sent to your desktop · just now." (phone-3 #29). Ask in the Reader, in the learner's own setting (project-1, expert-1, notes-1). The figure's waiting line and prediction (workbench-1 #36-40). The lesson's respect for "I already know this part" (lesson-1 #19-24). "assumed (not tested)" (expert-1 #67). Today's cause line with its one action (retainer-2 #46). "Stop for today" acting at once (seasoned-2 #81). Find-section → side by side (retainer-2 #43-45).

---

## 7. Proposals

The first part's P1 to P10 stand. These continue from P11. Proposed wording is in *italics*.

**P11. The first session comes from what was read (F20, UX-13).** When the first questions are written, Today offers them at once, and says how they came:

```
Wednesday evening
5 questions from "Symmetric Matrices and Variance", the part you read.   [ Begin ↵ ]
More come as you read on.
```

While they are written: *Writing questions for "…" · about 2 minutes · keep reading* (an amount from the build's windows and passes). On a failure that retried once already: *Couldn't write questions for "…". Try again, or keep reading: nothing is lost.*

**P12. Lessons you can find and come back to (F21, UX-14).**

```
Today
  Continue your lesson on Dot product · 1 of 2 parts done        [ Continue ]  close it
```

On feedback after a miss, beside "Fix this mix-up": *Teach me this ▸* (a lesson on the topic just missed; waits for arc G, section 8). On "Close": *Your lesson is kept. It's on Today when you want it.* A lesson offer names its reason in one line: *Offered because your last two answers on eigenvalues missed the same step.*

**P13. A practice exam from any exam goal or a stored past exam (F22).**

```
18.06 Linear Algebra, Exam 1 · past exam
  [ Sit it ▸ ]   answers stay hidden until you finish · solutions: add a file ▸
```

On a goal with no held-out pool: *Practice exam: LearnLoop can set one aside from this goal's questions (they won't come up in practice meanwhile). [ Set it aside ]*. Spec first; it joins the graded-work stage.

**P14. Say what you know, where you are (F28, UX-18).** On the Reader's guide and on each topic in plain words:

```
How deep do you want to go?   get the idea · learn to use it · fluency
I know this chapter ▸   (test me on it: up to 4 questions, then skip what I show)
```

A check with nothing to ask says so: *Nothing to ask yet on "Covariance matrices": its questions are still being written. Try again in a few minutes.*

**P15. Help counted once, said before (F24).** One line, the same in the working space, on feedback and on a retry:

```
help on this question: a check (12:04) · a figure (12:06)  → practice with help ◌
```

Before a retry that can't count as on your own: *You saw part of this answer earlier today, so this one is practice with help. Your check on your own comes back on Friday.* (Waits for the Decider's first stage, with P6.)

**P16. Courses (F29, SJ-6).** A course is a name that readings, goals and plan rows carry. Add asks only when there is more than one: *Add to: Linear algebra ▾ · new course…*. Today rows carry the course in grey; the minutes line splits: *20 minutes today: about 14 linear algebra (exam Dec 11 first), 6 probability.* Something else would help gains *Only probability today*. Spec first; it shares the course with P3 and the first part's stage 5.

**P17. The goal box agrees with the library (F30, UX-17).** Three plain states instead of one:

```
Symmetric matrices    in your book · questions still being written
Variance              in your book · ready to practise
Machine learning      not in your books yet   add a topic · find a book
```

"add it" offers to join an existing topic first: *Same as "Covariance matrices"? [ yes ] [ no, a new topic ]*.

**P18. Own notes in (F27).** Add accepts a folder: *Add your notes folder · LearnLoop reads the Markdown files and follows their [[links]]; your files stay where they are.* A flashcard file: *These look like flashcards (front, back). Keep them as cards? [ yes ] [ read them as text ]*. A note that contradicts another source gets a margin cue (P7): *Your note says "product"; your lecture says "sum".* Spec first.

---

## 8. The fix stages, re-ranked

One ordered list for the queue, by learner impact and dependency. Sizes: S about a day, M two to four days, L a week or more. Constraints kept: help that shows what it gave away waits for the Decider's first stage; feedback, hypotheses and repair screens wait for arc G (G2 and the tag `mvp-0.61`); the Reader redo carries search, margin cues and syntopic reading; no persona picker; nothing changes what is computed without saying so. The first part's stages 1 to 4 are done.

| # | Stage | Contents | Size | Kind | Spec first | Waits for |
|---|---|---|---|---|---|---|
| 1 | **Waiting you can see** (owner's request, 2026-11-19; **in progress**, branch `ux/waiting-indicators`, record `docs/reviews/ux-waiting.md`) | One shared waiting indicator per app on Today → question, question → feedback, and wherever a model writes while the learner watches. Check it against F25's table. Not proposed again here | — | frontend | no | (running) |
| 2 | **First questions arrive** | UX-13 (budgets as ceilings above the live model's output, one automatic retry, Today follows the build's real state); P11 (the first session from what was read; an amount for question writing, which the waiting stage cannot show from the frontend); F20's "Everything you've read…" line that says questions come as you read | M | backend + frontend | no | nothing |
| 3 | **Broken controls, second round** | UX-14 (lesson resume), UX-15 (window scroll), UX-16 (stop line; one plan field), UX-17 (empty-goal sentence), UX-18 (empty quick check), UX-19 (first click), UX-20 (hint failure words and clearing), UX-21 (Begin with a lesson offer), UX-22 (reply shown), UX-23 (phone reason code), UX-24 (section names), UX-25 (bare display equations), UX-26 (double math in quotes), UX-27 (place tabs on checks) | M (fourteen small fixes) | frontend, with small sidecar fields for UX-16 and UX-18 and possibly UX-24 | no | nothing |
| 4 | **Course setup, graded work and the practice exam** (first part's stage 5, widened) | P3 (start from a goal; F23), P13 (sit a stored past exam, solutions kept hidden, a held-out pool for an existing goal; F22), P16's course as the thing materials join (F29, SJ-6), the graded-work entry over `seed-exam-attempts`, P17 (F30, SJ-7) | L | backend + frontend | yes | nothing (owner: built inside the audit's fix) |
| 5 | **A Goals place** (first part's stage 6) | P2: every goal, deadline and scope edits, pause and close, a passed date asked about in one line, "Am I ready?" outside the Reader, add reading to a goal | M-L | backend (a goal update call) + frontend | yes | stage 4's course; persisted-meaning changes under the playbook |
| 6 | **Lessons you can find** (first part's stage 12, moved up) | P12: resume and a list of lessons taken (beyond UX-14's card), the reason for an offer, the offer on the topic just missed, "I'm stuck" that can lead to being taught, the Teacher screens remade in the app's design language (owner, Nov 8), lesson turn waits with a cancel (none exists today), UX-22's follow-ups. "Teach me this" on feedback is the feedback part | M-L | frontend + small backend | yes, short | the feedback part waits for arc G (G2, `mvp-0.61`); the rest for nothing |
| 7 | **Load you can see and steer, for one or two courses** (first part's stage 7, widened) | P5 (tomorrow and the week, *less / more*, a default daily amount), P16's split of one budget between courses and "only this course today", F31's sizes on one screen, a 20-minute and a phone 5-minute choice | M-L | backend + frontend | yes | stage 4's course for the split |
| 8 | **Help shows what it gave away** (first part's stage 10) | P6 and P15 (F24): one tally, said before, quoted after; F37 (dispute a too-generous grade; Ask never promises a regrade); UX-20's investigation of why the smallest hints fail their checks; F36's keys in the working space; F10/F26's Ask placement in practice | M | backend + frontend | no | the Decider's first stage (P6, P15); arc G (G1, G3, K6 with G6, then G2 and `mvp-0.61`) for feedback; H1, H2 for tutor context |
| 9 | **Progress in words and the jargon sweep** (first part's stage 8) | P10, F5, F6, F16, F18, plus F32 (ids and CLI under why?), F38, UX-12 (macros in model text outside the Reader); F33 under *details* if the owner agrees; the deny-list extended to the goal report, why?, lessons and the phone's feedback | M | mostly frontend; small backend copy | no | the owner's call on F33 |
| 10 | **The Reader redo** (first part's stage 11) | P8 search, P7 cues, syntopic reading; F26 (answers in view), F34 (keeping in a few seconds, plain labels), F35 (a web chapter's sections), UX-11 (display math kept at extraction, brought forward: it now visibly breaks reading) | L | backend (cue model, search, extraction) + frontend | yes | nothing for the frontend parts; the cue model is its own backend step |
| 11 | **Own notes as sources** (new) | P18 (F27): folder and vault import with links, flashcard decks kept as cards, notes that follow outside edits (and say so), the source of a question shown and opened, a way out | L | backend + frontend | yes | stage 4's course; the Reader redo's cues for contradictions |
| 12 | **Settings cleared** (first part's stage 9) | F17 and the owner's Nov 8 item; the daily amount and spend caps visible (with stage 7); switches a learner can find | M | frontend + small backend | no | stage 7 for the daily amount |

UX-10 (the one-time OK) still needs the owner's ruling, now with new evidence: the empty-install route never asks for it, the fresh-vault route does (section 1.1). The phone pairing page (F11) needs a host-side change (the stage 4 record's options a or b) and can ride with stage 3 if the owner wants it.

After each stage, re-run the walks it came from (I2); after stages 2 and 3, re-run student, retainer, lesson, workbench and expert.

---

## 9. What this part could not check, and a third wave

**Not checked here.**

- The goal whose date has passed: the returner's fixture goal was due on the walk's own day.
- A practice exam sitting, its result screen and the short check after an exam miss: no goal had a held-out pool.
- Stage 3's refusals in place (Hint or Ask during a check), the palette's "Nothing here to ask about" notice, the "today's list still has questions" and "only past exams" cause lines, and stage 4's "· N min ago", the desktop-away line, Next with a draft waiting, Today during grading and VoiceOver.
- A figure closed and reopened (UX-3's second half); figure failure, refusal, staleness, spend and withheld states; figures in the Reader and in a lesson's failure.
- Macros in model-written practice text (UX-12) and in Today's thread line: no fresh-library question was served.
- Intent routing, compare scope, meaning search and topic matching with the Decider and embeddings: unreachable in every walk.
- UX-15 and UX-19 in the real WebKitGTK window, and the "covering that spot" clicks on Ask's follow-up box.
- The phone on live models, a real interruption (the browser closed or the phone locked), and a session taken back on the desktop.
- Load over days: tomorrow and next week after a week of saving things.
- No model available, the terminal app, chat (MCP), and transitions between personas.

**A third wave would need.**

1. Fixtures: a goal whose date passed a week ago; an exam goal with a held-out pool; a library whose first questions are built before the walk (so practice from a fresh source is walked whatever UX-13's state).
2. The owner's decision on a Decider key for walks, so routing, compare scope and topic matching behave as for the owner.
3. Re-walks after stages 2 and 3: student, retainer, lesson, workbench, expert; after stage 4: exam, student, twocourses.
4. A walk over several simulated days (save twenty things, come back the next day and the next week) for the load journey.
5. A phone walk on live models with a real interruption and a hand-back to the desktop.
6. A no-model walk (signed out) across Today, practice, the Reader and lessons.
7. A short check in the real window for UX-15 and UX-19 before stage 3 lands.
