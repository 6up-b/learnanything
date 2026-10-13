# Reader workbench: experience design (v1)

**Status:** draft for owner review (2026-10-12). Companion to `docs/specs/spec_reader_workbench_v1.md`, written for its **restored scope** (the owner's restoration decision of 2026-10-12, spec §20.8) and for the backend track `spec_source_practice_and_probes_v1.md`. This document changes no data contract. Where it needs one changed, it says so in §10, with the spec section it touches.

**Integrated into the spec on 2026-10-13 (spec §20.9).** Every spec phase's "what the learner sees" now names the sections here that present it. All seventeen proposed changes in §10.1 were adopted, five with a change; §10.1's last column gives each ruling. The open questions in §10.2 are the spec's owner decisions D29–D41, with the defaults recommended here. Where this document and the spec disagreed, the ruling is recorded in the spec's §20.9 and this document was edited to match: the reconnect line's formative check is now called *quick check* ("check me" always means an attempt on your own, spec D43); help during a check on your own uses the ladder's choose-then-take step instead of a confirmation dialog (spec D42); the submit line no longer promises a later check; the recap's "later" carries no number; U2's test governs only what LearnLoop starts; and a comparison has no fixed source limit. From here on the spec wins on behaviour, data and gates, and this document on presentation; a later disagreement goes in the phase's review file.

**Consistency review (2026-10-13, spec §20.10).** A critic compared this document with the spec line by line and found seven contradictions; all seven are fixed in both documents. Tutor offers are fetched when an answer lands and shown only when pressed (spec D44). W11's density had an extra ½ in each component (total mass ½, so its 30% readout was wrong) and its prediction's answer was backwards; the density, readout and prediction are corrected, and the wrong density is now a negative control in the spec's golden case (G45). A hint sits under the step it is about and names the step it continues from, which is never the questionable one (spec D45). *Check my work* counts as a hint in every example. *Where this goes* says what each box is actually used for (§4.10). The help ladder's fallback steps up a rung on each further Help press. A check on your own names only the book until feedback: no exercise number, section, page, link or *why* (spec D46).

**Inputs, read in full:**
- the brainstorm `docs/brainstorming/Improving Reader's design.md` (three rounds, 1,461 lines);
- the spec at `8deb75be` and the restoration edits in progress on `docs/reader-workbench-spec`, plus the coverage audit `docs/reviews/reader-dialogue-coverage.md`;
- the app as it is on `main` at `57d31c63`: `screens/ReaderScreen.tsx` (3,991 lines), `screens/reader/`, `components/` (`ui.tsx`, `QuestionQueue.tsx`, `PlanReadingBanner.tsx`, `AskOverlay.tsx`, `OpenInSource.tsx`, `PdfReaderPane.tsx`), `render/` (`LiveMarkdownEditor.tsx`, `MathLiveEditor.tsx`, `MarkdownMath.tsx`), `styles/app.css` and `styles/palettes.css`, `screens/TodayScreen.tsx` and `screens/today/`, `screens/PracticeScreen.tsx`, `screens/FeedbackScreen.tsx`, `screens/KnowledgeWellView.tsx`; the branch `origin/feat/reader-clarification-branches` (`ReaderAskBranches.tsx`);
- `spec_p3_reader_integration.md` (§1.1 invariants, §5 modes and palette, §11 restoration), `spec_daily_loop_v1.md` (§0, §2, §5.2, §6, §7, §8), `spec_mobile_tailnet_v1.md` (scope and allowlist), router §15.3.

**Citation convention.** `B 504–508` is a line range of the brainstorm. `spec §5.2` is the workbench spec. `P3 §1.1`, `DL §6.10` and `router §15.3` are the other specs. Phase tags in brackets, such as **[RW2b]**, name the spec phase that builds an element (§11 has the full map). Phase names follow the restored scope: RW1a–c, RW2a–d, RW3a–b, RW4a, RW4b, RW4d, RW4e, RW5a–b, RW6a–b and RW7a–b, plus **[SRC]** for `spec_source_practice_and_probes_v1.md`. Elements this document added that no phase built yet are tagged **[UX→RWn]**: the phase that takes them. The spec adopted them all in §20.9.

**Who this is for.** One person: the owner, a self-directed adult learning mathematics and probability from textbooks and papers, on a Linux desktop app with a terminal look (JetBrains Mono, dark palettes, amber accent), and sometimes on a phone over the tailnet. Nobody else will use it, so the design can trust its user, skip onboarding theatre and give full control. It still has to be calm on a tired evening.

---

## 0. The design on one page

The brainstorm's test is the whole brief: *"Does this interaction help the learner return to the thing they wanted to accomplish, more capable than when they encountered the obstacle?"* (B 504–508). Eight design moves answer it:

1. **One page, five postures.** The source never leaves the screen. Reading, investigating, working, comparing and returning are postures of the right-hand side of one page, not separate screens. Nobody navigates to a tab to start learning (B 160).
2. **Every detour is reversible with one key.** A return stack and a breadcrumb record each step away from the reading position. `Alt+←` goes back, and "Does this make sense now?" waits where the learner returns (B 105, 154, 186).
3. **Three voices, one visual grammar.** The author's text (`§`), LearnLoop's model (`◇`) and the learner (`›`) each look different everywhere, never by colour alone. "Checked" appears only when something other than a model checked it (B 206, 261, 1282).
4. **The well's vocabulary in the margin.** The Reader uses the gravity well's discrete markers and never a percentage: `○` untested, `◌` worked with help (a check on your own is pending), `●` demonstrated on your own. A passage note, a recap line and a scheduled check all speak the language the owner already reads on the map (`KnowledgeWellView.tsx`: "dashed amber bead = instructed — cold check pending").
5. **Help is a visible ladder anchored to your own steps.** All five levels are always on screen when help is open. LearnLoop marks the one it would offer first, and taking any level costs one key and no justification. Hints sit under the step they are about, say which steps stand, and never switch to the book's route uninvited (B 510, 713–763, 788).
6. **Quiet by construction.** In reading, nothing moves, blinks, pops or takes focus. LearnLoop speaks only through margin marks, at a density the learner sets. Skim mode mutes it. "No intervention" is the default outcome (B 285–293).
7. **Never wait.** Every model-backed action returns control at once and lands in a known place, with honest pending, failed, capped and offline states. Reading, selecting and typing never stop for a model (P3 §1.1 invariant 1).
8. **Coming back is the hero.** "Last time here", resumable problems and cold checks turn `◌` into `●`, and the Reader shows that change. Open questions are threads to pick up, never a debt count (B 263–273, 1020–1055).

---

## 1. Design principles, as tests

Each principle comes from a brainstorm intention and ends in a test that a screen, a recording or a funnel row can pass or fail.

| # | Principle | From the brainstorm | Test (fails if…) |
|---|---|---|---|
| **U1** | **Return, more capable.** Every detour knows where it came from, and getting back is one key. Arriving back says what changed. | B 504–508 (the design rule); B 98 and 105 ("a detour that returns", "a reversible path back"); B 154 ("investigate something without losing my original task"); B 186 (reconnect); B 1055 (reopen the reader after a cold check) | …any investigating, working or comparing state lacks a visible way back to the exact origin (passage and selection, or problem and step), or `Alt+←` / the first crumb restores anything other than that position. …the origin, once back, doesn't show the question's status. |
| **U2** | **Reading still looks like reading.** The page is the main thing. Learning tools gather around the text, never on it. | B 297 ("Reading should still feel like reading"); B 327 (collapses back into reading); B 136 (one workflow) | …in the reading posture the source pane is narrower than 60% of the window above 1,280 px. …anything LearnLoop starts, other than margin marks, the section-boundary offer that exists today, or a one-line reconnect after a return the learner started, is drawn inside the text column. (What the learner asked for — a figure they built, the fold while they try the next step — may sit inline.) |
| **U3** | **The learner's own words and work are the anchor.** Anything said about the learner's work quotes it. Help continues from it. | B 510 (the owner's pain: "a hint I wouldn't be able to reconcile with the work I already did"); B 519–523 ("preserve the learner's evolving reasoning"); B 727 (never force them to "abandon their existing reasoning"); B 757–763 (the boundary-condition hint); B 1244, 1268 | …a hint at level 2 or above shows no quoted learner step. …a reconnect or recap line refers to "your question" without its words. …a hint switches to the reference route without one of the three reasons in spec §5.2 rule 4. |
| **U4** | **Help is offered, never withheld, always recorded.** LearnLoop suggests where to start, the learner takes what they want, and both can see what was taken. | B 108–118 (help as a deliberate quantity; accepting an explanation is not mastery); B 788 ("always be able to ask for more help"); B 994 (an explicit ask always gets help); B 196 (keep what was written before each hint) | …any help level needs more than two keys from the open ladder, or asks "are you sure?". …an attempt's assistance (book open, hints, worked steps) is not on screen before Submit. …a rung is greyed out because it is "too early". |
| **U5** | **Quiet by construction: no intervention is a legitimate outcome.** LearnLoop's own initiatives are marks the learner can ignore at no cost. | B 285–293 ("no intervention should be a legitimate, sometimes optimal action. An adaptive reader that constantly interrupts can make reading worse"); B 707 (optional, collapsible, density-limited); B 106 (a limited attention budget) | …in the reading or working posture anything takes keyboard focus, opens a modal, shows a toast, animates, blinks or plays a sound without the learner asking. …a ten-minute reading recording shows more LearnLoop marks in a section than the learner's density setting allows, or more than one in a viewport (§10 S8). …skim mode shows any mark LearnLoop started. |
| **U6** | **Say what connects, never what's lacking, and show what the learner can do.** Copy describes relationships and evidence status, never traits. | B 685 ("a warning that says the learner is weak … can make the software feel judgmental"); B 697–699 (a semantic match is not evidence the gap is still there); B 709 ("reinforce what the learner is capable of doing") | …any copy uses trait words ("weak", "you struggle", "you don't understand", "you always"); spec G16's lint extends to every surface here. …a week of cues is all `◌` and never `●`. …a learner step is ever coloured red. |
| **U7** | **Every sentence has a visible author.** Source, model and learner text look different, and the difference survives in greyscale and for a screen reader. | B 206 ("visibly AI-generated … not passed off as the author's"); B 261 (source vs inference vs belief); B 655 (reconstruction vs interpretation); B 1282 (provenance is fundamental); P3 invariant 9 | …a block of text on any screenshot cannot be attributed to source, model or learner without hovering. …"checked" or "verified" appears without a non-LLM check (spec W2). |
| **U8** | **Sources keep their identity.** Several books stay several voices. Their differences are the content. | B 242–261 ("preserve differences … an attractive but misleading consensus"); B 873 (different formulas are not necessarily errors); B 1272 (the textbook is central, not context for an AI) | …a cross-source view contains a model sentence that cites no single source's quote, or a heading such as "summary" or "consensus". …the tutor's answer puts its own explanation above an available excerpt from the learner's book. |
| **U9** | **Waiting never blocks reading.** A model action is fire-and-keep-going, with a known landing place and honest states. | P3 §1.1 invariant 1 and spec W12; B 102 (context switching); B 982 (don't wait for the session to end) | …any model-backed action has an undefined pending, failed, capped or offline state (§4.0). …scroll, selection or typing in another step stalls while a request runs. …a result moves focus when it lands. |
| **U10** | **Struggle is respected; autonomy is the default.** The learner sets how much LearnLoop leans in, and nothing counts the time they take. | B 329–335 (expertise reversal; "defaults to respecting the learner's chosen level of autonomy"); B 510 (scaffolding that adapts to struggle); B 808 ("how much of the solution should remain theirs") | …a timer, an elapsed-time display or "taking a while?" appears in the workbench. …help appears that the learner didn't request. …the first offer ignores the help style: the workbench report shows suggested levels under "let me struggle" no lower than under "balanced" on the same facets. (The chooser stays a judgment, spec §5.5; this tests that it listens.) |
| **U11** | **Cold is honest, and the learner is never trapped.** A check on your own shows nothing from before. Help is one key away and says plainly what taking it changes. | B 1043 ("doing so would transition the attempt to an assisted activity rather than secretly preserving cold status"); B 1047 and 1376 (genuine unfamiliarity); P3 §11 ("the learner is never trapped in a cold task to protect a metric") | …a cold check shows source text, an earlier hint, an inquiry or a figure. …help is blocked. …taking help doesn't say, before it happens, that the attempt becomes practice with help. |
| **U12** | **Everything returns, as a thread to pick up, never as debt.** Questions, unfinished problems, missed predictions and scheduled checks come back at the right moment, each with a way to act on it. | B 263–273 (durable questions; an optional synthesis under a minute); B 106 ("endless accumulation of … overdue reviews"); B 1020–1055 and B 514 (the short unfamiliar problem later); DL L9 (no capture debt) | …any surface shows a count of open or unfinished things as a to-do number, in red, or with "overdue". …a returning visit doesn't offer "continue", the still-open questions and "resume" for unfinished work. |
| **U13** | **Simple first, everything one key away, everything switchable.** One box on selection. The full palette, every shortcut and every off switch remain. | B 164–166 ("select something and express what you're trying to do"); B 168–174 (standard selection, excellent keyboard controls, the ability to disable interventions, one interaction model across books, PDFs, videos and notes) | …selecting text changes rail tab, moves focus or alters the selection. …any action in today's palette needs more than `Tab` plus one choice from a selection. …a LearnLoop-initiated element lacks an off switch reachable from the element itself. …a switched-off feature leaves a disabled button behind. |
| **U14** | **Fewer, better interactions.** Success is getting unstuck sooner and returning to the task, not more clicks. | B 470–474 ("an excellent Reader might actually produce fewer interactions, shorter sessions"); B 459 (complete workflows rather than add actions) | …any report or screen presents interaction counts, streaks or "questions asked" as progress. …the reader report leads with anything other than completed workflows and return-to-reading (§9). |

**The five intentions as a lens, not a feature.** The brainstorm's orient, understand, apply, consolidate and transfer (B 63–73) organize the restored palette **[RW1b]** and map onto the postures: reading and returning serve *orient* and *understand*, investigating serves *understand*, working serves *apply*, comparing serves *understand* and *transfer*, and cold checks serve *consolidate* and *transfer*.

---

## 2. The felt experience: one session, and the days after

A real session, re-narrated with the revised design. The owner is reading the probability textbook in their `probability` vault, in the chapter on continuous distributions. Each moment says what happens, what the learner feels, and what LearnLoop deliberately does **not** do.

**Moment 0 — arriving (Tuesday, 21:10).** Today's plan has a reading block: "Continue §5.4 Mixtures · about 12 min". Enter. The Reader opens at the paragraph where reading stopped last Thursday, with the cyan "Reading for today's plan" banner across the top (`PlanReadingBanner`, as built). At the head of the rail a compact **Last time here** card **[RW6a]** reads: *continue at §5.4 ¶2* (already there), *still open: "why is the density of a sum a convolution?"*, and one line under **Since last time**: *● conditional probability — demonstrated on your own (Sat)*. Below it the Guide shows the reading path at the owner's *Learn* depth **[RW7a]**: §5.4 *core* ("you'll need it for 5.14"), §5.5 *enrichment* ("skip unless you want sums vs mixtures"), and *one exercise worth trying: 5.14*.
- *Feels:* oriented and slightly lifted by the `●` line. Picking up the thread costs nothing.
- *Does not:* show an overdue count, quiz them on arrival, open a modal or replay a summary they didn't ask for.

**Moment 1 — reading.** The text column is the screen. Beside one paragraph sits a thin mark, `◌┆`. They don't hover, and nothing happens. Later, curious, they focus it: *"Connects to a distinction you worked on: density vs the probability of an interval (Exercise 4.3, 2 Oct). Not yet checked on your own since."* **[RW3a/b]** They read on.
- *Feels:* quietly known, not watched.
- *Does not:* interrupt, colour the passage red, call them weak, or show a second mark in the same screenful (the density setting is "normal": at most two per section and one per viewport, §4.4).

**Moment 2 — confusion, in their own words.** The mixture CDF line, `F_X(x) = p F_Y(x) + (1−p) F_Z(x)`, doesn't sit right. They select it. A small box appears under the selection, **unfocused**, so `PgDn` still scrolls. They start typing, and typing focuses it: *"why are the densities weighted by p? isn't p a probability, not a density"* ↵ **[RW1b]**. The box shows `◐` for about a second, then *→ asking · help me reason · change*. The rail switches to Ask, because the learner asked, and shows their words at once with `◐ answering — usually about 9 s`. They read the next two lines while it works. The answer lands without taking focus, and the tab carries a static `•`. It starts with the book: *§ from the book, §5.4 ¶3: "…"*, then *◇ LearnLoop's model:* "condition on which component was chosen, then differentiate; the weights survive because differentiation is linear" **[RW1c]**.
- *Feels:* heard in their own words, and still reading.
- *Does not:* lead with an essay before the book's own words, praise the question, or move the reading position.

**Moment 3 — a branch, and the way back.** "Condition on which component was chosen" lands on a soft spot. *ask follow-up*: *"how does conditioning on a coin flip give P(X ≤ x)?"* A breadcrumb appears above the source: `↩ §5.4 ¶3 › why weighted by p? › conditioning on a coin flip` **[RW1a]**. The tutor looks it up **[RW1c]** and shows an excerpt from §2.7 of the same book (the law of total probability) with *peek*. The source pane scrolls there with the passage outlined, and the crumb trail grows by one. It clicks. `Alt+←` twice: back at §5.4 ¶3, selection still marked. One dim line under the passage, the only time LearnLoop writes inside the text column: *your question "why weighted by p?" — does this make sense now? yes · still unclear… · quick check*. They choose *still unclear…* and type *"ok but why does differentiating keep the weights?"*. A new branch starts from the root, and the answer is two lines. They press *yes*. The root resolves. Its `?` margin mark turns to `✓` for the rest of the visit and is gone next time.
- *Feels:* went down a rabbit hole and came back intact. The original question stayed theirs.
- *Does not:* lose the original question, insist on a check, mark the question resolved on its own, or count branches.

**Moment 4 — the book as a sparring partner.** In Worked Example 5.4.2 a different mark, `▹┆`, sits beside the derivation: *try the next step first* **[RW3b]**. They take it. The next three lines of the book fold under a dotted rule (*the next 3 lines are folded while you try · show*) **[RW1b]**. They write a guess, press ↵, and see their line beside the book's. They missed a (1−p) factor. That miss is kept as a formative record (tier 2, spec W1), and it will appear under "worth a second look".
- *Feels:* an active reader, with nothing at stake.
- *Does not:* grade it, show a score, or let the answer sit visible right under the line they were asked to predict.

**Moment 5 — working the exercise beside the book.** End of section: Exercise 5.14, the one the Guide suggested. They select it and type *"let me work this"* → *work through this* **[RW1b → RW2a]**. The right side widens to half the window. The verbatim stem appears **at once**, taken from the selection, while the import finishes in the background (`◐ setting up checks and hints for this exercise…`) **[UX→RW2a, §10 S2]**. Above *Your work*, one line offers a choice that is already made: *● with the book open (practice beside the book — counts as one hint) ○ without it (your own attempt; you can open it any time)*. They start typing, so the default stands.

They write three steps with live KaTeX. Step 3 is `F_Z(x) = −e^{−x}`, and they're not sure. `Ctrl+K`, *check my work · counts as a hint* **[RW2b]**. `◐ reading your steps…` They keep typing step 4. The verdicts appear in a narrow right-hand column: step 1 `≈ looks valid (model's reading)`; step 2 `✓ checked (symbolic: integral)`; step 3 `? first questionable — at x = 0 this gives −1, and a CDF starts at 0 · looks like a missing constant of integration (model's guess)`. No correction is given. The footer now reads *book open = 1 hint · help used: a check*: a check that points at the first questionable step tells them as much as a level-2 hint, so it counts as one (spec §5.2), and the button said so before they pressed it.
- *Feels:* the slip was found and the fix is still theirs. Nothing about the screen says "wrong".
- *Does not:* show a red ✗, reveal the answer, start a timer, or comment on how long they took.

**Moment 6 — a question before a hint.** `Ctrl+H`. The help ladder opens at once below step 3 with all five levels. Because two explanations of the step-3 slip are open (a support mistake or a missing constant), rung 1 reads *a question that tells apart two explanations of step 3 · not graded · counts as a hint*, and about two seconds later it is marked *▸ suggested (why?)* **[RW2b, restored]**. They take it: *"What is P(Z ≤ 0) when Z ~ Exponential(1)?"* They answer *"0"*. *"That settles it: your support is right; the gap is the constant."* The hint (level 3) follows under step 3, the step it is about, labelled *continues from step 2*, the last step that stands: *"Steps 1–2 stand. Your antiderivative in step 3 matches the density, but a CDF must be 0 at x = 0, and −e^{−x} gives −1 there. What constant keeps your derivation and fixes that?"* They write step 4, `1 − e^{−x}`. About seven seconds later a quiet line appears under the hint: *§ compare with the book: Example 5.3.2's boundary step, p.219 ▸*. They peek: the source pane scrolls to it, outlined, with a crumb back to 5.14 **[RW2b bridging; RW2c route-matched examples]**.

Had the hint said "integrate the piecewise density instead" (the book's route), they would have pressed *this doesn't connect to my work…*, then *I'm using a different approach*, and the next hint would have stayed on their CDF-first route (spec §5.2 rules 4–5).
- *Feels:* the hint met them where they were, and nobody took the pencil.
- *Does not:* restart the explanation, switch to the book's route, hide the higher rungs, or ask "are you sure?".

**Moment 7 — submitting.** `Ctrl+Enter`. The optional 1–5 confidence row works as it does on the practice screen today. One line states what the attempt records: *book open · 3 hints (a check, a level-1 question, a level-3 hint) → practice with help ◌ (not yet checked on your own).* Whether a check on your own follows is RW6b's valuation to decide, later, so the line promises none. The feedback screen is today's, and `Esc` returns to Exercise 5.14 in the Reader, not to the queue **[UX→RW2a, §10 S6]**. Because the answer was right and their route differed from the book's, the feedback carries one optional line: *the book derives the density first; you went CDF-first · compare methods ▸* **[RW2c]**.
- *Feels:* honest bookkeeping, not a penalty.
- *Does not:* call the attempt "assisted (penalty)" or hide that the visible book counts.

**Moment 8 — a question across two books.** In §5.5 the text says a mixture of normals is not normal, and they wonder how their other book treats mixtures against sums. `Ctrl+Shift+F`, or select and type *"how do my other books treat mixtures vs sums?"* → *compare sources*. The comparing posture: the right side lists passages grouped by source, each with its role and a one-line model note on what it contributes **[RW4a]**. One carries *◌ speaks to your open question about convolutions*. They pin two and press *compare* **[RW4d]**: a table with one row per source and columns *contributes · assumes · differs*, each cell quoting its own source. *keep this comparison*: later both passages carry a `⇄` mark. *ask the tutor about these*: the tutor's answer cites only the pinned passages.
- *Feels:* their own library talking to itself, with its differences intact.
- *Does not:* write an essay, merge the books into a "consensus", or rank by their history without saying so (the *personalized* chip is visible and switchable, B 877).

**Moment 9 — an explorable figure.** Back in §5.4 there is the two-sided exponential figure. Select the density equation → *make this explorable* **[RW5a]**. `◐ building an interactive version — about 30 s · keep reading`. They read on. A collapsed line appears under the equation: *▸ interactive version · AI-built · matches the book's equation (checked)*. They open it. First a prediction: *"If λ doubles, what happens to P(X ≤ 0)?"* They answer *it rises*, because the peak at zero gets taller. The figure moves λ to 2 and shows the readout before and after: *30.0% → 30.0%*. A box asks *what changed? (optional)*. They write one line: *λ squeezes both sides toward 0, but p sets the split*. Then they shade `P(X ≤ 0)` and drag `p` with the arrow keys: the readout follows `p` exactly, which is the dialogue's own illustration (B 591–611: at p = 0.30, 30% left of zero and 70% right).
- *Feels:* playing with the idea. The miss is a discovery.
- *Does not:* grade the miss, present the figure as the author's, or animate anything when reduced motion is on.

**Moment 10 — wrapping up and leaving.** They press *Back to today's plan* and are there at once. On Today, one dim line: *Reading wrap-up ready — under a minute ▸* **[RW6a]**. They open it. Three short lists: **resolved** — *why weighted by p?*; **still open** — *density of a sum*; **worth reinforcing** — *◌ piecewise CDF (Exercise 5.14, with help) · a next-step guess and a figure prediction that missed · Wed: a question that tells apart two readings of your step-3 slip (why · undo) · next Mon: a new mixture problem, on your own (why · undo)*. They undo nothing and close it.
- *Feels:* closure in forty seconds.
- *Does not:* block leaving, show the wrap-up as a modal, or list the checks as debt.

**Moment 11 — days later.** Wednesday's plan carries *check · on your own · about 6 min · from your reading of §5.4 (why)*. It is a textbook exercise from the *other* book, verbatim, chosen because its answer separates the two explanations **[SRC, RW6b]**. The cold banner reads: *"A check on your own. Help is still here — using it makes this practice with help."* They solve it. On Monday, on the phone during a train ride, the plan offers the new mixture problem. It is an ordinary item, so the phone can serve it. They solve it. On the map, the dashed amber bead for *piecewise CDF* fills green.

The next time they open the book, *Last time here* says *Since last time: ● piecewise CDF — demonstrated on your own (Mon)*. Had Monday gone wrong, the feedback would have offered *↩ back to where you studied this: Exercise 5.14 and your question "why weighted by p?" (§5.4)* **[RW6b, restored]**.
- *Feels:* proof of capability, in the same visual language as the map.
- *Does not:* claim the chapter is mastered (B 1053), schedule more checks than are worth their minutes, or hide that a check was retired ("No longer needed: you solved one like it on Wednesday · undo").

---

## 3. Information architecture and modes

### 3.1 One page, five postures

The Reader stays one screen: header, optional plan banner, optional **detour strip** (the breadcrumb), body, key bar. The body is always **source pane | right side**. The posture decides what the right side holds and how wide it is.

| Posture | Serves (B 63–73) | Right side | Width of the right side | Entered by |
|---|---|---|---|---|
| **Reading** | orient, understand | The rail: Guide · Ask · Notes, as today | 360 px (today's), collapsible to a 28 px gutter with `\` | Opening a source; leaving any other posture |
| **Investigating** | understand | The rail on Ask, showing the inquiry tree; the detour strip shows the trail | 360 px; widenable to 480 px by drag (remembered) | Asking from the intent box or palette; *ask follow-up*; opening a question from Today's queue |
| **Working** | apply | The workbench, replacing the rail. The rail's tabs fold into the workbench header's `⋯` | **Half the window**, resizable, remembered (min 480 px) **[UX→RW2a, §10 S1]** | *work through this*; *resume*; *check me* on a cue; *practice this question* |
| **Comparing** | understand, transfer | The library answer or the compare table; a *peek* of another source opens here too | Half the window, resizable, remembered | *where else is this explained?*; `Ctrl+Shift+F`; *compare* from an answer |
| **Returning** | orient, consolidate | The rail with the *Last time here* card on top of the Guide | 360 px | Opening a source that has an earlier session; following a "back to where you studied this" link |

The **reading depth** control that exists today ("I want to: skim quickly · read closely · mark for later", P3 §5.1) stays in the header and is orthogonal to posture. Skim is the mute button: no margin cues, no reconnect line, no quick checks, no section-boundary offers.

**Narrow windows** (below the 1,040 px breakpoint `app.css` already uses). In working and comparing the two sides stack: the right side takes the screen, the problem stem or query stays pinned at its top, and *show in the book* peeks the source in a sheet that covers the lower half. `Esc` closes the sheet.

### 3.2 Transitions

```
                    open a source you've read before
   [RETURNING] ──────────────── continue ↵ / first scroll ─────────────▶ [READING] ◀────────────┐
        ▲                                                            │   │   │   │               │
        │ "back to where you studied this"                           │   │   │   └ Esc · Alt+← ──┤
        │ (feedback, after a cold check)              ask / follow-up│   │   │                     │
        │                                                            ▼   │   │                     │
        │                                                 [INVESTIGATING]│   │  resolve · yes ·    │
        │                                                     │  ▲       │   │  Alt+← to origin ───┤
        │                                     work on a step  │  │ ? on  │   │                     │
        │                                                     ▼  │ a step│   │                     │
        │                                                   [WORKING] ◀──┘   │ Esc twice ·         │
        │                                                     │              │ leave for now ──────┤
        │                                      compare / peek │              │                     │
        │                                                     ▼              ▼                     │
        │                                                   [COMPARING] ◀────┘   Esc · Alt+← ──────┘
        │
   Today / plan / phone  ── cold check (practice screen; not a Reader posture) ──▶ feedback ──┘
```

Rules that make the transitions predictable (B 140–160, Jenson's "a sequence of actions becomes easy, predictable, and progressively discoverable"):
- **The learner's act chooses the posture.** There is no posture switcher. Asking enters investigating, *work through this* enters working, *where else…* enters comparing.
- **Postures nest, and the trail shows the nesting.** A question about a step while working gives `↩ Exercise 5.14 · step 3 › why can I drop the constant?`. Comparing from inside an inquiry pushes one crumb.
- **`Esc` peels one layer** (transient, then posture). Order: intent box or palette → help ladder or popover → peek → editor focus → posture back to reading. In the workbench the first `Esc` leaves the editor and the second is *leave for now*, which keeps the session open. At the outermost layer, `Esc` leaves the Reader only during a plan's reading block, where it is DL §6.10's *back to today's plan*. Elsewhere it does nothing, so a stray key never drops the learner out of the book.
- **`Alt+←` / `Alt+→` walk the return stack** of reading positions and postures, like an editor's navigate back and forward. The leftmost crumb is always "where I was before this detour" (spec RW1a's *back to where I was*).
- **Selection never switches the rail tab.** Today `onTextSelection` flips the rail to Notes (`ReaderScreen.tsx`, `setRailTab(... "notes")`). Under the intent box it doesn't: the rail changes only when the learner acts **[RW1b]**.

### 3.3 What persists

| Thing | Lives in | Survives |
|---|---|---|
| Reading position per source | P3 restoration (existing) | restarts |
| The return stack (detours within a visit) | Reader UX state for the visit; its root is P3's restored position | navigation within the visit; app restart restores only the root **[UX→RW1a]** |
| Inquiries, branches and status | `question_events` and branch parents on the answer payload (spec §4.3) | always; open ones also appear in Today's question queue |
| Workbench sessions, steps (with superseded versions) and assists | `workbench_sessions`, `workbench_steps`, `workbench_assists` (spec §5.7) | always; open sessions are never closed automatically (spec §5.1) |
| Library asks, comparisons, kept comparisons | `library_asks`; kept comparisons as `source_object_relations` proposals **[RW4d]** | always |
| Figures and predictions | `interactive_figures`, `figure_predictions` | always (the figure reopens from cache) |
| Formative records (next-step misses, "still unclear", predictions, check verdicts) | learner-text gaps sources and `ReaderObservationV1` **[RW1b, RW5a, RW6a]** | always |
| Scheduled checks | commitments (`test_me_later`, `due_hint`) **[RW6b]** | until answered, retired or undone |
| Rail tab, rail and split widths, help style, cue density, reading font, "cues off" for a source | UX preferences on the device (try/catch around storage; render correctly without it); "cues off" and cue density also in vault config so they hold across devices | per device or per vault, as noted |
| Recap dismissal | per source, until the next session | — |

### 3.4 The visual grammar: three voices and one evidence vocabulary

**Voices.** Each has a glyph, a rule style and a spoken label, so the distinction survives greyscale, colour blindness and screen readers (U7).

| Voice | Glyph and label | Rule | Colour token (default palette) | Screen-reader prefix |
|---|---|---|---|---|
| **The source** (an author, verbatim) | `§` + short source name + locator ("§ Probability · §5.4 p.212") | solid 1 px, `--border-strong` | `--text` | "From the book, section 5.4:" |
| **LearnLoop's model** | `◇ model` (first use in a panel: "◇ LearnLoop's model") | dotted 1 px, `--purple-pill` | text `--text`, label `--purple-text` | "LearnLoop's model:" |
| **You** | `›` + "you" where needed; step numbers `1 ›` | solid 2 px, `--amber-mid` | `--text`, numbers `--amber` | "You wrote:" |

When model text quotes the learner, the quote takes the learner's styling inline (amber quote marks). When it quotes the book, the quote takes the source's.

**Evidence status, from the well.** These are discrete markers and never percentages, so the Reader can't blend "likely to recall" with "shown" (the well's contract: ready-owned depth, demonstrated beads, never blend).

| Marker | Means | Where it appears |
|---|---|---|
| `○` | untested: no evidence yet | recap, cue notes |
| `◌` | **with help**: worked with the book open, hints or worked steps; a check on your own is pending (the well's "instructed" dashed amber bead) | recap, cue notes, the submit line, follow-up lines |
| `●` | **demonstrated**: done on your own | recap ("since last time"), "new use" cues |
| *assumed known (not tested)* | the existing label (`ASSUMED_LABEL`) | unchanged |

**Check status.** This is about one step of work, not about the learner.

| Marker | Means | Never |
|---|---|---|
| `✓ checked` | a non-LLM check passed (symbolic with a negative control, an exact key, a quote match); the method shows on focus | used for a model's opinion |
| `≠ checked` | a non-LLM check found the step doesn't follow ("step 3 doesn't follow from step 2") | red, "wrong", ✗ |
| `≈ model's reading` | the model reads the step as valid; nothing checked it | "correct" |
| `?` | questionable (model's reading); the first one is labelled *first* | "error", "mistake" |
| `·` | not checked yet | — |

**Margin marks**, with a legend in the Guide's footer (*what the marks mean*).

| Mark | Means | Whose | Counts against the density setting |
|---|---|---|---|
| `◌┆` | connects to a distinction you worked on (not yet checked on your own since) | LearnLoop's | yes |
| `●┆` | a new use of something you've demonstrated | LearnLoop's | yes |
| `▹┆` | try the next step first (on worked examples) **[RW3b]** | LearnLoop's | yes |
| `?` | your open question is anchored here | yours | no |
| `✎` | your unfinished work on a problem here | yours | no |
| `⇄` | a comparison you kept | yours | no |
| `◇▸` | an interactive version exists | yours | no |

Marks sit in a 20 px gutter left of the text in the extracted-text view and in an overlay gutter on the PDF surface. They are focusable in reading order. The existing left-border signals stay: amber means your annotation, purple wash means the Guide's "worth a second look".

### 3.5 Keyboard map

The map stays consistent with what the app teaches elsewhere: `^p` palette, `Esc` back, `^↵` submit, `^h` hint, `^d` stuck, `?` ask, and `alt+digit` reserved for the top navigation.

| Where | Key | Does |
|---|---|---|
| Reader | *select text* | intent box appears unfocused; typing focuses it |
| | `↵` in an empty box | Ask (no model call) |
| | `Tab` in the box | the full palette, grouped by intention |
| | `?` with a selection | focus the intent box |
| | `Alt+←` / `Alt+→` | back / forward through the return stack |
| | `Alt+↓` / `Alt+↑` | next / previous margin mark; `↵` opens it |
| | `[` / `]` | previous / next rail tab (outside text fields) |
| | `\` | collapse or expand the rail |
| | `Ctrl+Shift+F` | ask your library (comparing) |
| | `Ctrl+F` | find in this source (exists) |
| | `w` | wrap up this session |
| Inquiry rail | `↑` `↓` · `↵` · `f` · `r` · `o` · `p` | move · expand · follow-up · resolved · reopen · show passage |
| Workbench | `↵` at a step's end · `Shift+↵` | new step · new line in a step |
| | `Alt+↑` / `Alt+↓` | previous / next step |
| | `Ctrl+Backspace` in an empty step | delete the step (undo shows) |
| | `Ctrl+K` | check my work |
| | `Ctrl+H` | help ladder: `1`–`5` or `↑↓` to choose, `↵` to take, `Esc` to close |
| | `Ctrl+D` | I'm stuck |
| | `Ctrl+↵` | submit |
| | `Ctrl+Shift+B` | hide the book (before step 1) / show the book |
| | `?` (not typing) | ask about the focused step |
| | `Esc`, `Esc` | leave the editor; leave for now |
| Comparing | `↑` `↓` · `Space` · `p` · `o` · `c` · `Ctrl+↵` | move · peek · pin · open source · compare pinned · ask the tutor about pinned |
| Figure | `Tab` · arrows · `Shift+arrows` · `t` | next control · adjust · big step · values as a table |

`Ctrl+K` and `Ctrl+Shift+B` must be checked against `LiveMarkdownEditor`'s own bindings in RW2a. If they clash, the editor's binding wins and the action gets the next free chord.

---

## 4. Features

### 4.0 The contract every model-backed action follows

Every model-backed action has the same seven states, rendered in the same way at its **landing place**. Reading, selecting and typing continue through all of them (U9).

| State | What shows | Notes |
|---|---|---|
| **pending** | `◐ <verb>…` and, only when the reader report has a measured p50 for the route, "usually about N s"; a *cancel* link | No skeleton boxes, no progress bars that pretend to know, no motion beyond the static `◐` |
| **landed** | the content with its voice label; if the landing place is off-screen, a static `•` on its rail tab or crumb | No focus move. One polite screen-reader announcement ("Answer ready in Ask") |
| **failed** | one line: what failed, what is kept, *try again ↵* ("Couldn't write a hint. Your steps are saved — try again ↵") | The learner's input is never lost on failure |
| **model unreachable** | "Couldn't reach LearnLoop's model. Your question is kept — try again ↵" | Different from *sidecar down* |
| **sidecar down** | the header's `offline` pill (exists); model actions are absent from the palette, with one Guide line explaining why | A loaded source can still be read and selected |
| **capped** (spend) | "Today's <route> budget ($1.00) is used. <fallback> still works." Example: "The item's own hints are still here" | The owner set the caps, so naming the money is honest |
| **switched off** (kill switch) | the entry point is absent | No disabled ghosts (U13) |

**Landing places:** an Ask answer lands in its exchange; a check and a hint under their steps; a bridge under its hint; organizer lines beside each hit; a figure under its passage; the narrative in the recap; an import in the workbench header; a routed intent in the intent box.

**Microcopy rules for every surface:**
- Name the author (§3.4).
- Name the evidence status with the well's words.
- Hedge model output with "model's reading" or "model's guess", never "probably" sprinkled through prose.
- Name money and time plainly ("about 6 min", "$1.00").
- Never use trait words (U6).
- Say what a choice does before it does it ("counts as one hint").

### 4.1 The intent box **[RW1b]**

- **Entry:** any text selection (drag, `Ctrl`+drag boxes, `Alt`+drag sweep, `Shift`+arrows), on the PDF surface and the extracted text alike. Video transcripts follow the restored "one interaction model on every source kind" (RW1a).
- **Placement and weight:** a 360 px box just below the selection (above it if near the bottom), with one line of placeholder: *what do you want to do with this?*, and a key hint row *↵ ask · tab actions · esc*. It appears about 150 ms after mouse-up so a drag in progress never flickers it. It is **unfocused** (§10 S3): scroll keys scroll, `Ctrl+C` copies, and the first printable key focuses it and is typed into it.
- **Routing:** on ↵ the box shows `◐` while the Decider routes (≤ 4 s), then one line: *→ asking · help me reason · change*. The action starts at once, and *change* cancels it and opens the palette with the text kept. It routes speculatively when typing pauses, so ↵ is usually instant (§10 S4, adopted with a stop at 80% of the daily call cap).
- **Progressive disclosure:** `Tab` opens the palette **grouped by the five intentions** (restored, B 63–73):
  - *Understand:* ask · explain differently · why does this step work? · what does this assume? · another way to see this · make this explorable;
  - *Apply:* work through this · let me try the next step · add this exercise to practice · practice this question · find an exercise in my sources;
  - *Consolidate:* revisit once (test me later) · help me remember · reconstruct this later;
  - *Transfer:* where else is this explained? · connect it · why this matters;
  - *Orient:* what do I need first?;
  - *Mark:* highlight · note · confusing · not worth remembering.

  Today's nine presets, highlight and exercise import keep their behaviour, and the right-click tag menu stays as it is. Options for phases that haven't landed are absent.
- **Undo:** *change* while it runs. Annotations and commitments created by a routed action show *undo* on their receipt line, as captures do today.
- **Attention:** the box never appears for a selection made inside the rail or the workbench. In skim mode it doesn't appear on its own; `?` or `Tab` after a selection opens it. It closes on `Esc` or a click elsewhere, with nothing recorded.
- **Keys while it shows:** printable keys type into it. The Reader's single-key shortcuts (`w`, `[`, `]`, `\`) work only when no intent box is showing.
- **Microcopy:** the routed line names the action in the palette's words, so a *change* lands on a familiar label.

### 4.2 Inquiry: branches, the detour strip, reconnect **[RW1a, RW1c]**

- **Entry:** an ask from the intent box or palette; *ask follow-up* on any exchange; a question opened from Today's queue (it opens the source at its anchor with the inquiry expanded).
- **The detour strip** (between the header and the body, 26 px, only while a detour exists): `↩ §5.4 ¶3 › why weighted by p? › conditioning on a coin flip    alt+← back`. Every crumb is a button. The first is always the reading position from before the detour. It is the brainstorm's "small breadcrumb trail" (B 184).
- **The rail on Ask** shows the current inquiry expanded and other inquiries collapsed under *other questions on this source*. Each exchange shows the learner's question (`›`), the answer (`◇`, with citation chips that are `§` buttons), and *ask follow-up · show passage · status*. Status chips sit on the root only: *open · resolved · revisit once · make it something I can do · dismissed*, plus *reopen* on a closed one (spec D4). The tree with search is the branch's `ReaderAskBranches`, restyled to the voices.
- **Three answer modes from the tutor that looks things up [RW1c]:** an answer shows, in this order, **from the book** (a `§` excerpt, when one directly answers), **LearnLoop's explanation** (`◇`, grounded, with citations), and **connecting it to your work** (`◇`, only when the learner has work or an open question on this; it quotes it) (B 1254–1272). Under the answer: *another way · that didn't help…*. The second takes optional text (W5) and fetches a different source or role, labelled *"from a different book"* or *"a worked example instead"*. Under it sit buttons the learner presses, never actions the tutor performs: the sources spec's requests (*practice this*, *from your books: …*, *how do your books treat this?*, each with the tutor's one-line reason labelled as LearnLoop's) and two of the Reader's own (*make this explorable* on a cited equation or figure, *try the next step first* on a cited derivation). **Nothing appears until a button is pressed** (spec D44). Behind *practice this* and *from your books*, the lookup starts as soon as the answer lands, so pressing shows proposals or passages at once (pressed sooner, the button shows *◐ looking in your books…* in place); a proposal is served only by *practise* on it. *how do your books treat this?* is one heavier model call and is written only when pressed (*◐ comparing…*). A lookup that found nothing turns its button into a quiet line, *nothing in your practice or books fits this yet*, so the learner isn't sent to an empty list. When verification keeps no passage, the answer opens with *"Your books don't cover this directly — this is LearnLoop's model's explanation"*.
- **Reconnect:** when a child is resolved, or when the learner returns to the root passage through the strip or `Alt+←`, one dim line appears under the root passage: *your question "…" — does this make sense now? yes · still unclear… · quick check*. The same line shows at the top of the inquiry in the rail. It disappears when the learner scrolls more than a screen on, and nothing is recorded if it is ignored (spec §4.1). *still unclear…* opens a text box (W5). *quick check* puts one formative question in the rail, revealed for self-comparison (*matches · partly · no*) and never an attempt. It is not called *check me*, which in this design always means an attempt on your own (spec D43).
- **Latency:** answers are pending in place, with the learner's words saved first. A T6-grounded answer can take about 7 s for retrieval alone (spec §3.4 item 12), so the pending line says *looking in your books…* while retrieval runs and *writing…* while the model writes. This is honest about which wait is which.
- **Undo:** status changes undo from the chip (*resolved · undo*). Follow-ups can't be unasked, but can be dismissed.
- **Attention:** an answer never opens the rail on its own unless the learner asked from the intent box (their act). Off-screen arrivals show only a static `•`.
- **Microcopy:** "Does this make sense now?" (never "Did you understand?"); "make it something I can do" for `help_me_remember`; "revisit once" for `test_me_later`.

### 4.3 Active reading: next step, why step, assumptions, reconstruct **[RW1b]**

- **Entry:** a selection inside a derivation or worked example, through the box or the palette; the `▹┆` invitation **[RW3b]**.
- **Let me try the next step:** the following blocks in the source **fold** under a dotted rule (*the next 3 lines are folded while you try · show*) **[UX→RW1b, §10 S5]**. The rail shows *what comes next after this line?* with a learner box. After ↵ or *show me*, the learner's line and the book's (`§`) appear side by side, with a self-check *matches · partly · no*. The fold opens.
- **Why does this step work? / What does this assume?:** the same shape. The expected answer is the source's justification when the source gives one (`§`), otherwise the model's (`◇`, "model's justification").
- **Another way to see this:** the tutor's *alternative* intent, labelled as a different source or role.
- **Reconstruct this later:** a `test_me_later`-class commitment on a derivation. The receipt says *"In a few days you'll be asked to rebuild this derivation without the book."*
- **States:** the question is written by the quick-check producer, pending in the rail. Until it lands, the fold shows *◐ writing the question — the lines stay folded*, with a one-key *unfold*.
- **Records:** misses and "partly" become formative records (tier 2) and appear under "worth a second look" in the recap. They are never grades.

### 4.4 Margin cues **[RW3a, RW3b]**

- **What shows:** a mark in the gutter (`◌┆`, `●┆`, `▹┆`, §3.4). Focus or hover shows one line from a fixed template (G16). A second line says why: *"Because: Exercise 4.3 (2 Oct) and your open question about interval probability · found by LearnLoop's model, not by a test"* (B 697–699).
- **Actions** (in a small popover reachable by `↵` on the mark): *open* (the earlier work: attempt, diagnosis, inquiry or named gap) · *check me* · *not relevant…* (optional text) · *fewer marks like this* · *cues off for this source*.
- **"Check me" stays in the Reader.** It opens the item in the working posture with **the book hidden by default**, because a check beside the book would be assisted; *show the book* is one key and labelled (§10 S7). On submit, `Esc` returns to the passage. Under DL1 it is a learner-pick block.
- **Density control (restored, spec §6.1 `cues.density`):** *margin marks: off · fewer · normal · more* (off is "cues off"; the others are 1, 2 or 4 per section), in the Guide's footer and in every mark's popover (*fewer marks like this* steps it down one notch). This document adds **at most one LearnLoop mark per viewport** at every setting (§10 S8). The label says *"a display limit to protect your attention"*.
- **"Try this step first"** (`▹┆`, restored) reads *"Try the next step before reading it?"*. Pressing it opens §4.3's next-step fold at that line. It is an offer and never a gate on the text.
- **Ordering:** by the probability that the target is still open (restored W4). Guide passages come first on ties.
- **Never:** in skim mode, in the workbench's source pane while working (the learner is busy), animated, or on the line the learner was restored to (it would greet them with a judgement).
- **Positive cues are part of the budget.** A week with only `◌` marks fails U6. RW3b's "new application" kind is where the Reader shows what the learner can do.
- **Undo:** *not relevant* and *cues off* show *undo* until the learner leaves the source; "cues off everywhere" is reversible in Settings.

### 4.5 Ask your library, compare, keep **[RW4a, RW4d, RW4e]**

- **Entry:** `Ctrl+Shift+F` from anywhere in the Reader; *where else is this explained?* from a selection; *Ask* (`Shift+↵`) in the library search box (exists, on the library page). The answer opens in the **comparing posture** beside the current source, so nothing is lost.
- **The answer is sources first** (B 828, spec D12). The header reads *"why is covariance an inner product?" · 3 sources · 6 passages · found by keyword + meaning · notes by LearnLoop's model · personalized ●*. Passages are grouped by source, then by role. The role label comes from ingest and, once RW4e lands, from the instructional roles (*definition · worked example · explanation · counterexample · contrast · prerequisite · application*), with "model's label" when the role is a proposal. Each hit shows a `§` excerpt with its locator and one `◇` line on what it contributes, plus *peek · pin · open*. The restored RW4a groups *prerequisites* and *applications* found through the concept graph under their own subheads.
- **Peek** shows the passage with its neighbours in the right side, and pushes a crumb. **Open** navigates the left pane to that source (also a crumb). The way back is the same `Alt+←`.
- **Personalized** is a visible chip, on by default. When on, at most one hit carries *◌ speaks to your open question about …*. When off, the order is plain retrieval rank (B 877).
- **Compare** (two or more pinned passages from different sources; the sources spec's `compare_sources` has no source limit, only a prompt bound, and lists the sources it could not fit as *also discussed in: …*): one row per source with columns *contributes · assumes · differs from the others*. Each cell is a `◇` line that quotes its own source's `§` passage, and a line that fails quote verification is dropped, never repaired (spec §7.3). The first row is *your passage* when compare started from a selection. The table header says *"Differences kept · each line quotes its own source"*. With RW4d, *requested perspectives* (*geometric view*, *application*) are typed into a small field above the table, and claims, LearnLoop's inferences and the learner's own take sit in three visibly separate bands (B 261).
- **Keep this comparison** stores proposals in the source-object layer **[RW4d]**. Both passages then carry `⇄`, and focusing the mark reopens the table. *Remove* is the undo.
- **Ask the tutor about these** opens an inquiry whose citations are limited to the pinned passages, and says so: *"answers only from these 3 passages"*.
- **Practice this question** lists `find_practice` proposals. With **[SRC]** these include **textbook exercises** labelled *"Exercise 4.12 · from your book · verbatim"*. Choosing one opens it in the working posture (book hidden by default, §10 S7). When nothing fits: *"Nothing in practice fits yet · find an exercise in my sources ▸"* **[RW4b]**.
- **States:** retrieval is pending as *looking in your books…* and organizer lines as *◐ noting what each contributes…*. The hits show **before** the notes do: excerpts first, notes when ready.
- **Attention:** nothing in comparing appears unasked.

### 4.6 Exercises from your books, as practice and as probes **[RW4b, SRC, RW6b]**

Most of this is backend work in the sources spec. The learner meets it in four places, and each uses the same honest labels.

| Where | What the learner sees |
|---|---|
| Comparing, "practice this question" | Textbook exercises beside existing items, labelled *from your book · verbatim · answer completed by LearnLoop's model (verified ✓ / not verified)* |
| Reader, "find an exercise in my sources" | Candidate exercise passages with source and page, and *use this one*. Choosing imports it (spec §7.4), and the import runs in the background while the workbench opens with the stem |
| Today's plan and the phone | An item header line: *Exercise 5.14 · Probability · verbatim*. During a cold check the header carries **the book's name and nothing that locates the exercise in it**: *from Intro to Probability · verbatim* — no exercise number, page, section or link (enough to know it's real, not enough to look it up, or its worked solution, by accident; spec D46). The book opens only through *show the book*, which first says it makes the attempt practice with help (§4.9). After feedback: *original page ↗* |
| A probe chosen to tell explanations apart | The why line: *"chosen because its answer tells apart two explanations of your step-3 slip · about 6 min · LearnLoop's estimate"* |

**Novelty labels (restored, B 1047):** a follow-up says honestly how unfamiliar it is: *new wording · new setup · new kind of problem*. "Same idea, new numbers" is never presented as transfer.

### 4.7 Explorable figures **[RW5a, RW5b]**

- **Entry:** a selected equation, figure block or **region of a figure** (`Ctrl`+drag on the PDF surface, restored) → *make this explorable*. From RW5b, the tutor or a library answer may offer *make this explorable* as a button when a retrieved equation supports one.
- **Placement:** **inline under the passage**, at the full measure of the text column, not in the 360 px rail (§10 S9). It is collapsed to one line once built (*▸ interactive version · AI-built · matches the book's equation (checked)*) and expands in place. Only one is expanded at a time.
- **Inside:** one prediction before the first change (radio choices or one word), then the controls: labelled sliders with numeric fields, the plot or plots, shaded areas with integral readouts and PMF bars (restored), and a *values as a table* toggle (`t`). After a reveal, *what changed? (optional)* takes a line of text (restored, a formative record). **Animation** (a CDF sweeping as `p` moves) plays only on *play* and becomes step buttons under reduced motion.
- **Labels follow verification (spec G23):**
  - *AI-built · matches the book's equation (checked)*;
  - *AI-built illustration of an interpretation · not checked against the book*;
  - *couldn't build a reliable version of this (reason)*;
  - *can't draw this yet — needs a 3-D surface · noted*.
- **States:** pending as a dim line under the passage, *◐ building an interactive version — about 30 s · keep reading* (the estimate only once measured). Failure keeps the request and offers *try again*.
- **Records:** predictions and "what changed?" answers are formative (tier 2). Misses show in the recap. Nothing here is graded.

### 4.8 Last time here, wrap up, the narrative **[RW6a, RW6b]**

- **Last time here** (on opening a source with an earlier session) sits at the head of the Guide, compact by default. Its sections:
  - *continue at …* (↵);
  - **Still open** (inquiries, each with *open* and status chips);
  - **Unfinished** (`✎`, workbench sessions with *resume*, showing how many steps there are and the help used so far);
  - **Worth a second look** (missed predictions, next-step misses, "still unclear");
  - **Since last time** (facets whose evidence changed since the last visit: `●` demonstrated, or a check retired as no longer needed) **[UX→RW6a, §10 S10]**;
  - **Coming up** (scheduled checks with date, purpose, *why* and *undo*, a calm timeline and never a list of counts).

  It collapses after the first scroll or *continue*. *last time ▸* in the Guide header reopens it. *dismiss* hides it for this source until the next session.
- **Wrap up** (restored, B 273: "optional and takes less than a minute"; spec §9.1) is `w`, or *Wrap up (under a minute)* in the rail's footer once the session has activity. After leaving a source with activity, the self-dismissing one-line offer appears **at the destination** (Today, or the library), not in the Reader being closed (§10 S11). It shows the spec's three lists for this session: **resolved** · **still open** · **worth reinforcing** (`◌` work done with help, missed predictions and next steps, and the checks coming up with their dates). Each line has one action (resolve, keep open, revisit once, undo), and the narrative sits collapsed at the foot. One key closes it.
- **The narrative** (≤ 120 words, spec §9.2) is a collapsed *▸ summary written by LearnLoop's model from what you did* inside the card. It is never the first thing shown.
- **Undo:** each scheduled check has *undo*, and the section has *undo all*. Undo takes optional text, *"why? (optional)"* (§9.3 below explains why this matters).
- **Microcopy:** headings carry no counts ("Still open", not "2 open questions"). A retired check reads *"No longer needed: you solved one like it on Wednesday · undo"*.

### 4.9 Cold checks and the loop back **[RW6b, SRC; DL2 serves them]**

- **In the plan:** *check · on your own · about 6 min · from your reading of §5.4 (why)*. *why* expands to the purpose (*to tell apart two explanations of your step-3 slip* or *to see whether the piecewise CDF holds without help*) and the valuation as an estimate (*"expected to settle which repair to try · LearnLoop's estimate"*, W2). The plan's minutes bound how many appear on a day. There is no count anywhere.
- **The cold banner** (practice screen, `hint-banner` style, amber edge): *"A check on your own. Help is still here — using it makes this practice with help."* `^h`, `?` and *show the book* stay live, and each says its consequence in its own label before it is used (U11): `^h` opens the help ladder with nothing revealed, its header reads *"taking any rung makes this practice with help ◌"*, and `↵` on a rung takes it — the ladder's ordinary choose-then-take step (§5.5), so a stray key reveals nothing; `?` opens the ask box with the same line as its placeholder, and sending the question is the take step; *show the book (makes this practice with help)* is a labelled control. There is no confirmation dialog anywhere in this design (spec D42; the earlier draft had one here).
- **The header during the check** names the book and nothing that locates the exercise in it: *from Intro to Probability · verbatim · new setup*. No exercise number, page, section or link, and no *why*: P3's invariant 10 withholds source cues and purpose text from a cold administration, and an exercise number is enough to find the exercise, or its solution, in the book (spec D46). After feedback the header gains *Exercise 3.19 · p.112 · original page ↗* and *why this check ▸*.
- **After feedback,** when the result suggests repair: *↩ back to where you studied this: Exercise 5.14 · your question "why weighted by p?" (§5.4)*. This opens the Reader in the returning posture at that place (restored, B 1055).
- **On the phone:** the same item header and banner. Probe-type checks show the existing *"continue it on the desktop"*.

### 4.10 Where your words go **[RW1b, RW2b, RW6a; learner-text gaps]**

Every free-text box in this design carries a quiet *ⓘ where this goes*. What it says depends on the box, because the boxes go to different places (spec §6.2, §7.8, §8.1, §9.3; the first draft gave every box the gap wording, including *not relevant*, whose text the spec keeps out of learner-text gaps). Every version ends with "never to grade you".

| Box | *ⓘ where this goes* says | Where it goes (spec) |
|---|---|---|
| *still unclear…*, *that didn't help…*, *I'm stuck*, *this doesn't connect… · say more*, an answer to a question before a hint, *not what I asked…* on a practice proposal | *"Kept with this passage or problem. LearnLoop's model may read it to name a gap, such as a prerequisite to look at — never to grade you."* | Learner-text gaps: a reader question, `workbench_text`, or (once the sources spec's adapter exists) its usage-verdict text |
| next-step, why-step and assumption answers; a figure's *what changed?* | *"Kept with this passage. If your answer differed from the book's, LearnLoop's model may read it to name a gap — never to grade you."* | `reader_formative`, only when the learner marked the answer *partly* or *no*, or the prediction missed (§4.3, §8.4); a match is kept and nothing more |
| *not relevant…* on a margin mark | *"Tells LearnLoop this mark missed, so marks like it get better. It isn't read for gaps in your understanding — and never grades you."* | Feedback on the cue judge only (spec §6.2) |
| *why? (optional)* when undoing a scheduled check | *"Tells LearnLoop the check wasn't worth your time, so checks get valued better. It isn't read for gaps — and never grades you."* | The undo's `learner_card` verdict; calibration data (spec §9.3, §15) |
| *your take* on a comparison | *"Kept as your own note on these passages, in your voice. It isn't read for gaps — and never grades you."* | A `learner_connects` relation (spec §7.8) |
| *not right?* on a figure | *"Sent with this figure to the model that builds it, for a better version — never to grade you."* | A figure revision request (spec §8.1) |
| the intent box | *"Used to pick the action you meant. If it becomes a question, it's kept like one."* | The Decider's routing; a routed question then follows the first row |

When a gap is named from the learner's text, the inquiry shows one line: *◇ model noted a possible gap: conditioning a CDF on a discrete choice · see it on the map · not right?* What *not right?* does is spec D37 (this document's §10 Q9).

### 4.11 Reading paths in the Guide **[RW7a, RW7b]**

- The Guide's *your path* card (exists for goals) gains the depth the learner picked (*get the idea · learn to use it · fluency*, mapped to DL2's intents) and, per section, a role chip: *core · prerequisite · enrichment · already shown ● · assumed*. Each chip has a one-line *why*, plus *read it anyway* and *skip it*. One line per path: *one exercise worth trying: 5.14 ▸* (opens the working posture).
- *Already shown ●* uses the evidence vocabulary and appears only when every LO the section teaches is demonstrated (spec §10).
- RW7b's plan change is invisible here, except that the plan's reading block names the section the path chose and why.

### 4.12 The attention budget

| Never interrupts | Allowed, quietly, and only these | Never, anywhere in the Reader |
|---|---|---|
| Scrolling; selecting; typing in the box, a step or an answer; reading an answer; dragging a slider | Margin marks within the density setting · a static `•` on a tab or crumb · the one-line reconnect after a return the learner started · the section-boundary offer (exists) · the *Last time here* card on opening · *wrap-up ready* at the destination · the help ladder's suggested-rung marker, which appears only after the learner opened help | Modals · toasts in reading or working · blinking or pulsing · sounds · focus moves · automatic tab switches · counts of open or unfinished things · timers · "streak" anywhere in the Reader |

**The existing quick-check signal breaks this budget.** `ll-reader-guide-alert` pulses the Guide tab without end, `ll-qc-blink` blinks a `◆`, and an uppercase strip pins itself under the tabs (`app.css`, lines 1219–1281). It should become a static `◆ n` on the Guide tab with no strip (§10 S12).

**Skim is the mute button** (U5). A learner who wants LearnLoop silent for a session picks *skim quickly* and gets the bare book.

**More value-of-information checks, never more noise.** Lifting the count caps (spec §20.7; the four caps in other specs) means LearnLoop may schedule more probes, follow-ups and checks when they are worth their minutes. The experience rule doesn't change. Each check carries *why* and *about N min*, the plan's minutes bound the day, and no surface ever shows how many are waiting.

---

## 5. The workbench in detail **[RW2a–d]**

### 5.1 Opening

- **Entry points:**
  - *work through this* on a selected problem, an imported exercise or an escalated quick check;
  - *resume* (`✎` mark, recap, rail, practice card);
  - *check me* on a cue and *practice this question* (these two default to the book hidden);
  - *one exercise worth trying* in the Guide;
  - on the practice screen, the remembered *Work in steps* button (spec D9).
- **No wait to start** (§10 S2). The stem appears from the selection, verbatim, at once. *◐ setting up checks and hints for this exercise…* shows in the header while the import runs. *Check my work* and *Help* show *available once setup finishes (usually about N s)* until then. Typing steps works immediately.
- **The book choice is a line, not a dialog:** *● with the book open — practice beside the book (counts as one hint) · ○ without it — your own attempt; you can open it any time*. Typing the first step accepts whatever is selected. With the book hidden, the source pane shows a calm placeholder: *"The book is hidden so this can count as your own attempt. Show it any time (Ctrl+Shift+B) — it'll count as one hint from then on."*
- **The header:** *WORKING · Exercise 5.14 · from the book, verbatim · original page ↗* (hidden while the book is hidden), and the help style control *let me struggle · balanced · guide me* (§5.11).

### 5.2 The step editor

- Each step is one `LiveMarkdownEditor` (markdown with live KaTeX) in an ordered list, numbered `1 ›`, `2 ›`. `↵` at the end of a step makes a new step; `Shift+↵` makes a new line in the same step. `Alt+↑/↓` moves between steps.
- **Editing keeps history.** A changed step supersedes the old version (spec §5.1). *↺* beside a step shows *your earlier versions* (the learner voice, dimmed). Nothing is lost.
- **Deleting** an empty step with `Ctrl+Backspace`, or any step from its `⋯` menu, leaves *step 3 deleted · undo* in place until the learner leaves the problem.
- **A verdict column** on the right, 120 px, shows check markers (§3.4). Editing a checked step dims its marker and adds *edited since check*.
- **Restored [RW2b]:** focusing a step lightly outlines the steps it depends on (from the last check), and the check summary lists *assumptions this uses: x ≥ 0; Z ~ Exponential(1)*.
- **Accessibility:** each step is a labelled text box ("Step 3 of 4"). Its verdict and any hint attached to it are linked by `aria-describedby`.

### 5.3 Saving, leaving, resuming

- **Saving** happens as the learner types, through the write queue (spec §5.1). The header shows *saved · just now*, then *saved · 2 min ago* in faint text. If a write fails: *not saved yet — retrying · your text is safe in this window* (amber). If the sidecar is down: *sidecar unreachable — keeping your steps here; they'll save when it's back*. Never "error".
- **Leave for now** (`Esc` twice, the button, navigating away, closing the app) keeps the session open. `✎` appears beside the problem's passage, *resume* appears in the recap, and the practice card offers *resume your steps*.
- **Abandon** is in `⋯`, not on the main row, so it is never one stray key away. It closes the problem at once with *abandoned · your steps are kept · reopen*, and *reopen* stays available from the recap while no attempt was written (§10 S13).
- **Resume** reopens the same steps, the same anchor, the same book visibility and the full assistance history, scrolled to the last edited step.
- **Old sessions** (more than 30 days) show as *unfinished* in the recap, without alarm, and are never closed automatically.

### 5.4 Check my work

- `Ctrl+K`, or the button, which says its cost before it is used: *check my work · counts as a hint*. A check that names the first questionable step tells the learner what a level-2 hint would (spec §5.2), so it is recorded as one, and the footer adds *a check* when the result shows. While pending: *◐ reading your steps (as of 21:42)…* in the verdict column. Editing continues.
- **Results** are markers per step, the first questionable step marked *first*, and its reason quoted from the step: *"? first — at x = 0, '−e^{−x}' gives −1; a CDF starts at 0"*. The restored error-kind guess comes as a second line: *"looks like a missing constant of integration (model's guess)"*.
- **Never** the correction, never red, never a score.
- **Stale results** are labelled: *"checked your steps as of 21:42 — step 3 has changed since"*.
- **Symbolic checks** show their method on focus (*sympy, with a negative control*). Without the sandbox every marker is `≈` or `?` and labelled "model's reading" (spec G9).

### 5.5 The help ladder

- `Ctrl+H` opens it **inline, below the focused step** (never modal, never covering work), with **all five levels visible** at once:

  | Rung | Label | Consequence shown |
  |---|---|---|
  | 1 | a question about your approach | *hint* |
  | 2 | point to the first step that doesn't hold yet | *hint* |
  | 3 | a hint on your step N | *hint* |
  | 4 | write the next step for me, in my notation | *worked help ◌* |
  | 5 | walk me through the rest, keeping my route | *worked help ◌* |

- **The offered rung** gets a `▸` and *suggested (why?)* when the chooser returns (≤ 3 s). Until then the ladder works with no suggestion. On timeout, or when the chooser is unavailable, the suggestion is rung 1 the first time, then one rung above the last one offered or taken on that step each time Help opens there again (spec §5.5); its *why?* reads *"no judgment available right now — the next rung up"*. *why?* expands to the chooser's inputs in plain words: *"you've demonstrated conditioning on your own twice; this is your first boundary-condition problem; help style: balanced · LearnLoop's judgment."*
- **Choosing and taking are separate.** Digits and arrows choose a rung, and `↵` takes it, so a stray keypress can't reveal a worked step. There is no "are you sure?".
- **The ladder never shrinks.** No rung is ever disabled for being "too early" (B 788). With *let me struggle*, the suggestion leans low. With *guide me* it leans high. The learner's choice always wins.
- **When rival explanations are open,** rung 1 reads *a question that tells apart two explanations of step N* (§5.8).
- **Assistance taken** shows in the footer as it accrues: *book open = 1 hint · help used: a check, a question (L1), a hint (L3)*.

### 5.6 Hints, anchored and reconciled

- A hint appears **under the step it is about**, in the model voice, and its label names **the step it continues from** (spec §5.2 rules 2–3; D45). The two can differ: a hint about a questionable step may quote it, but it builds on the steps that stand, so the questionable step is never its checkpoint.

  ```
  3 › = −e^{−x}
      ◇ model · hint, level 3 · on your step 3 · continues from step 2
      ┊ Steps 1–2 stand. Your antiderivative in step 3 matches the density,
      ┊ but a CDF must be 0 at x = 0, and "−e^{−x}" gives −1 there.
      ┊ What constant keeps your derivation and fixes that?
      ┊ this doesn't connect to my work…
  ```

- **"What stands" comes first** (spec §5.2 rule 3). The learner's quoted step uses the learner's styling.
- **Authored hints** are labelled *from the item*.
- **A capped or failed hint writer** shows *"Tailored hints are unavailable right now (reason). The item's own hints are still here ▸"*.
- **Leaks:** a hint that would give the answer away is withheld with *"This hint would give the answer away — take level 4 instead?"*.
- **Compare with the book** arrives later, under the hint, as *◐ finding the matching step in the book…* and then *§ compare with the book: Example 5.3.2's boundary step, p.219 ▸*, which peeks it in the left pane with a crumb. With RW2c the example is chosen to **match the learner's route** where one exists (*"a CDF-first example"*).

### 5.7 "This doesn't connect to my work"

- Under every hint. One click opens, inline:
  - four shortcuts, *that's not where I'm stuck · too big a jump · I'm using a different approach · the notation* (§10 S14 adds the first);
  - *about step: [3 ▾]*, defaulting to the hint's step;
  - a one-line box, *say more (optional)*;
  - *↵ next hint*.
- The next hint is requested at once with the reply, and **must declare a different strategy** (spec §5.2 rule 5). The UI shows it on the hint label as *"a different approach: a worked parallel"*.
- With *I'm using a different approach*, the next hint's first line says which of the learner's steps it builds on.
- Nothing about this is framed as a complaint. The button's tooltip reads *"tells LearnLoop the hint missed — the next one changes approach"*.

### 5.8 A question before a hint (discriminating questions) **[RW2b, restored]**

- **When:** the check leaves a questionable step with two or more rival explanations open (spec §5.2 rule 6). Rung 1 then takes this form, and is the suggested rung, unless there is a single explanation, the help style is *guide me*, or the learner picks a higher rung (spec §5.2 "when it is skipped").
- **Its label says three things before it is answered:** what it's for, that it isn't graded, and what it counts as. *"a question that tells apart two explanations of step 3 · not graded · counts as a hint"*. The spec records it as a level-1 hint (`hints_used` += 1, §5.4), and the learner sees that up front.
- **Shape:** the question in the model voice, a one-line answer box, *↵ answer · skip to a hint*. After the answer comes one line saying what it settled (*"That settles it: your support is right; the gap is the constant"*), or *"Still two possibilities — here's a hint that covers both"*, then the hint at the offered rung.
- **A short problem instead** (once SRC's discriminating search merges): one line under the question, *or try a short problem from your books that tells these apart ▸ (about 5 min)*. Taking it opens a second workbench session in the same posture, with a crumb back to Exercise 5.14, which stays open. Leaving it lets RW6b value it with the other follow-ups.
- **Recorded** as a formative answer (tier 2): in the diagnoser's trace at Submit, in the next hint's context, and in learner-text gaps when written (in-session updates, spec §5.2). It moves no posterior.
- **One at a time.** A second discriminating question appears only if the learner asks for it, and it must clear the same EIG bar (spec §5.2).

### 5.9 Submit

- `Ctrl+↵`. Above the button, the optional confidence row (as on the practice screen) and **one line of record**: *book open · 3 hints (a check, a level-1 question, a level-3 hint) → practice with help ◌ (not yet checked on your own).* With the book hidden and no help: *your own attempt*. It never promises a later check: only RW6b's valuation decides whether one is worth scheduling.
- The feedback screen is today's. `Esc` and `b` return to the problem in the Reader (§10 S6).
- **Restored [RW2c]:** after a correct answer by a route different from the reference, an optional *compare methods ▸* shows both routes side by side, the learner's in their own voice and the reference's labelled by source or model.

### 5.10 I'm stuck

- `Ctrl+D` adds a step of kind *stuck* with the prompt *"Write what you can, or what's confusing you. Being stuck here is useful information."*
- It stays in the work as a dimmed learner-voice block and is never deleted on its own.
- With RW2b it is sent to the hint writer and to learner-text gaps (*ⓘ where this goes*).
- An empty stuck step and no other steps, then Submit, is the existing empty stuck answer, scored 0 with no model call. The line says so before Submit: *"Submitting now records 'stuck' — that's fine."*

### 5.11 Help style and emotional tone

- **Help style** is *let me struggle · balanced · guide me*, a three-way control in the header, remembered (default *balanced*). Each choice has one line:
  - *"offers the lightest help first"*;
  - *"LearnLoop picks from your history"*;
  - *"offers worked steps sooner"*.

  It changes only the suggestion. Every rung stays available.
- **Tone rules:**

  | Situation | Say | Never |
  |---|---|---|
  | A step doesn't hold | "? this is where your expression stops being a CDF" | "wrong", "error", "mistake", red |
  | A valid different route | "your route works — the book goes another way" | "the correct method is…" |
  | Taking worked help | "write the next step for me (worked help ◌)" | "are you sure? this will hurt your score" |
  | Book open | "practice beside the book · counts as one hint" | "assisted (penalty)", "cheating" |
  | Many hints on one step | nothing; the next hint changes approach | "you've used 4 hints" |
  | A long time on a problem | nothing | "taking a while?", any timer |
  | Leaving unfinished | "kept — resume any time" | "you didn't finish" |
  | Correct after help | "solved with help ◌ — not yet checked on your own" | "great job!" with no status, or "doesn't count" |

### 5.12 On the practice screen

The remembered *Work in steps* button (spec D9) opens the same step editor, full width, with the item stem on top and no source pane. Keys and states are the same. The practice screen's `MathLiveEditor` stays the default answer surface until the RW2b checkpoint.

---

## 6. Wireframes

Widths are indicative. `▓` marks a selection, `┆` a margin mark, `◐` pending. Keys are listed in the bottom key bar, as the app does today.

**W1 — Reading (calm), returning card collapsed, marks within density.** **[RW3a, RW6a, RW7a]**

```
┌ READER  ← library  Probability · ch.5  original pdf →                      I want to [read closely ▾] ┐
│ Reading for today's plan · §5.4 Mixtures · about 12 min                      [ Back to today's plan ] │
│ §5.4 Mixtures ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━──────────── 38%                quick checks on │
├────────────────────────────────────────────────────────────────────┬─────────────────────────────────┤
│                                                                    │ GUIDE    ask    notes           │
│    5.4  Mixtures of distributions                                  │ last time ▸ · continue at ¶2 ✓  │
│                                                                    │ ─────────────────────────────── │
│    Suppose X equals Y with probability p and Z otherwise. ...      │ your path · learn to use it     │
│                                                                    │  core  §5.4 Mixtures     why ▸  │
│         f_X(x) = p f_Y(x) + (1 − p) f_Z(x)                         │  enr.  §5.5 Sums vs mix  why ▸  │
│                                                                    │  one exercise worth trying:     │
│ ◌┆ The probability that X lands in an interval is the integral     │   5.14 ▸                        │
│  ┆ of its density over that interval ...                           │ section · 5.4 ━━━━━━──────      │
│                                                                    │ Keep reading at your own pace.  │
│ ? │ The CDF follows by conditioning on which component ...         │                                 │
│                                                                    │ marks: off · fewer · ●normal ·  │
│                                                                    │ more   what the marks mean ▸    │
├────────────────────────────────────────────────────────────────────┴─────────────────────────────────┤
│ select ask·act  alt+← back  alt+↓ next mark  [ ] tabs  \ rail  ^⇧F ask library  w wrap up        ^p │
└──────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**W2 — The intent box (unfocused, then routed).** **[RW1b]**

```
│    The CDF follows by conditioning on which component was chosen:  │
│         ▓▓ F_X(x) = p F_Y(x) + (1 − p) F_Z(x) ▓▓                   │
│    ┌─────────────────────────────────────────────────────┐         │
│    │ what do you want to do with this?                   │  ← no focus yet: PgDn scrolls,
│    │ ↵ ask · tab actions · esc                           │    ^C copies, typing focuses
│    └─────────────────────────────────────────────────────┘         │

    after typing "why are the densities weighted by p?" and ↵:
│    ┌─────────────────────────────────────────────────────┐         │
│    │ › why are the densities weighted by p?              │         │
│    │ → asking · help me reason                    change │  ← ◐ for ~1 s first
│    └─────────────────────────────────────────────────────┘         │

    Tab instead of typing:
│    ┌ what do you want to do? ──────────────────────────────────────────────┐
│    │ UNDERSTAND   ask · explain differently · why does this step work? ·    │
│    │              what does this assume? · another way · make explorable    │
│    │ APPLY        work through this · let me try the next step ·            │
│    │              add this exercise · practice this question ·              │
│    │              exercise from my sources                                  │
│    │ CONSOLIDATE  revisit once · help me remember · reconstruct later       │
│    │ TRANSFER     where else is this explained? · connect it · why it matters│
│    │ ORIENT       what do I need first?                                     │
│    │ MARK         highlight · note · confusing · not worth remembering      │
│    └────────────────────────────────────────────── ↑↓←→ move · ↵ · esc ────┘
```

**W3 — Investigating: the detour strip, a branch and the book first.** **[RW1a, RW1c]**

```
┌ READER  ← library  Probability · ch.5                                       I want to [read closely ▾] ┐
│ ↩ §5.4 ¶3  ›  why weighted by p?  ›  conditioning on a coin flip                       alt+← back   │
├────────────────────────────────────────────────────────────────┬─────────────────────────────────────┤
│   (source scrolled to §2.7, the passage outlined)              │ guide    ASK    notes               │
│                                                                │ ▾ why weighted by p?        open ▾  │
│ ┃ 2.7 Law of total probability                                 │   › why are the densities weighted  │
│ ┃ P(A) = Σ P(A | B_i) P(B_i) ...                               │     by p? isn't p a probability…    │
│                                                                │   § from the book · §5.4 ¶3         │
│                                                                │   │ "F_X(x) = P(X ≤ x) = …"          │
│                                                                │   ◇ LearnLoop's model               │
│                                                                │   ┊ Condition on which component    │
│                                                                │   ┊ was chosen, then differentiate…  │
│                                                                │   another way · that didn't help…   │
│                                                                │   offer: practice this · compare    │
│                                                                │   ▾ conditioning on a coin flip     │
│                                                                │     › how does conditioning on a    │
│                                                                │       coin flip give P(X ≤ x)?      │
│                                                                │     § from the book · §2.7 p.53     │
│                                                                │     │ "P(A) = Σ P(A|B_i)P(B_i)…"     │
│                                                                │     ◇ model · connecting it to your │
│                                                                │     ┊ question: your coin flip is B…│
│                                                                │   f follow-up · p passage · r done  │
├────────────────────────────────────────────────────────────────┴─────────────────────────────────────┤
│ alt+← back to §5.4 ¶3  ↑↓ exchanges  f follow-up  r resolved  o reopen                             ^p │
```

**W4 — Back at the origin: the reconnect line.** **[RW1a]**

```
│ ? │ The CDF follows by conditioning on which component was chosen:  │
│   │      F_X(x) = p F_Y(x) + (1 − p) F_Z(x)                          │
│     ↳ your question "why weighted by p?" — does this make sense now?  │   (dim; gone after a
│       yes · still unclear… · quick check                              │    screen of scrolling)
```

**W5 — Working: the split, steps and check verdicts.** **[RW2a, RW2b]**

```
┌ WORKING · Exercise 5.14 · from the book, verbatim · original page ↗    help: struggle ·[balanced]· guide ┐
├─────────────────────────────────────────┬────────────────────────────────────────────────────────────────┤
│ § Probability · §5.4 · p.231  book open │ Problem                                                        │
│                                         │ § "Let X be Uniform(−1, 0) with probability p and              │
│  5.14  Let X be Uniform(−1,0) with      │    Exponential(1) otherwise. Find the CDF of X."               │
│  probability p and Exponential(1)       │                                                                │
│  otherwise. Find the CDF of X.          │ Your work                                    saved · just now  │
│  ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔    │  1 › F_X(x) = p F_Y(x) + (1 − p) F_Z(x)          ≈ model's    │
│                                         │  2 › for x ≥ 0:  F_Z(x) = ∫₀ˣ e^{−t} dt          ✓ checked    │
│  (the rest of the page, scrollable;     │  3 › = −e^{−x}                                   ? first      │
│   no margin cues while working)         │      ? at x = 0, "−e^{−x}" gives −1; a CDF starts at 0        │
│                                         │        looks like a missing constant of integration (guess)   │
│                                         │  4 › _                                                        │
│                                         │                                                                │
│                                         │ ^k check my work (a hint)  ^h help  ^d I'm stuck   ^↵ submit │
│                                         │ book open = 1 hint · help used: a check     esc leave · ⋯    │
├─────────────────────────────────────────┴────────────────────────────────────────────────────────────────┤
│ ↵ new step  ⇧↵ new line  alt+↑↓ steps  ^k check  ^h help  ^d stuck  ^↵ submit  ^⇧B book  esc esc leave  │
```

**W6 — The help ladder, then a question before the hint.** **[RW2b]**

```
│  3 › = −e^{−x}                                                                   ? first     │
│  ┌ help · ▸ suggested: 1 (why?) · every level is yours ────────────────────────────────────┐ │
│  │ ▸ 1  a question that tells apart two explanations of step 3 · not graded       hint     │ │
│  │      or try a short problem from your books that tells them apart ▸ (~5 min)            │ │
│  │   2  point to the first step that doesn't hold yet                         hint          │ │
│  │   3  a hint on your step 3                                                 hint          │ │
│  │   4  write the next step for me, in my notation                    worked help ◌         │ │
│  │   5  walk me through the rest, keeping my route                    worked help ◌         │ │
│  │ ↑↓ / 1–5 choose · ↵ take · esc close                                                     │ │
│  └──────────────────────────────────────────────────────────────────────────────────────────┘ │

    after ↵:
│  3 › = −e^{−x}                                                                               │
│      ◇ model · a question to choose the right hint · not graded · counts as a hint           │
│      ┊ Two different things could explain step 3. What is P(Z ≤ 0) when Z ~ Exponential(1)?  │
│      ┊ ┌──────────────────────────┐                                                          │
│      ┊ │ 0_                        │   ↵ answer · skip to a hint                               │
│      ┊ └──────────────────────────┘                                                          │
```

**W7 — The hint, "what stands", and "doesn't connect".** **[RW2b, RW2c]**

```
│  3 › = −e^{−x}                                                                               │
│      ◇ model · that settles it: your support is right; the gap is the constant              │
│      ◇ model · hint, level 3 · on your step 3 · continues from step 2                       │
│      ┊ Steps 1–2 stand. Your antiderivative in step 3 matches the density,                  │
│      ┊ but a CDF must be 0 at x = 0, and "−e^{−x}" gives −1 there.                          │
│      ┊ What constant keeps your derivation and fixes that?                                  │
│      ┊ this doesn't connect to my work…                                                     │
│      ┊ § compare with the book: Example 5.3.2's boundary step, p.219 ▸                      │
│  4 › _                                                                                       │

    after "this doesn't connect to my work…":
│      ┊ [that's not where I'm stuck] [too big a jump] [I'm using a different approach]        │
│      ┊ [the notation]                                       about step: [3 ▾]                │
│      ┊ ┌───────────────────────────────────────────────────────────────┐                     │
│      ┊ │ say more (optional)                                            │   ↵ next hint        │
│      ┊ └───────────────────────────────────────────────────────────────┘   ⓘ where this goes │
```

**W8 — Book hidden.** **[RW2a]**

```
├─────────────────────────────────────────┬──────────────────────────────────────────────────────┤
│                                         │ Problem                                              │
│                                         │ § "Let X be Uniform(−1, 0) with probability p…"     │
│     The book is hidden so this can      │                                                      │
│     count as your own attempt.          │ ○ with the book open · ● without it — your own       │
│                                         │   attempt                                            │
│     Show it any time (Ctrl+Shift+B) —   │ Your work                                            │
│     it'll count as one hint from then   │  1 › _                                               │
│     on.                                 │                                                      │
```

**W9 — Comparing: a library answer beside the source.** **[RW4a, RW4e, SRC]**

```
├──────────────────────────────────────────┬───────────────────────────────────────────────────────────┤
│ (current source; origin passage          │ ASK YOUR LIBRARY                       personalized ● ▾  │
│  outlined)                               │ "how do my books treat mixtures vs sums?"                │
│                                          │ 3 sources · 6 passages · keyword + meaning               │
│                                          │ notes by LearnLoop's model                               │
│                                          │ ── Probability (this book) ───────────────────────────── │
│                                          │ definition · §5.4 p.212                                  │
│                                          │ § "X is a mixture of Y and Z if…"                         │
│                                          │ ◇ random choice of a component, then a draw              │
│                                          │                         space peek · p pin · o open      │
│                                          │ ── Intro to Probability (2nd book) ───────────────────── │
│                                          │ contrast · §3.2 p.88                                     │
│                                          │ § "The density of X+Y is not f_X + f_Y; it is…"          │
│                                          │ ◇ warns that a sum convolves; a mixture weights          │
│                                          │ ◌ speaks to your open question about convolutions        │
│                                          │ ── Lecture notes · week 6 ────────────────────────────── │
│                                          │ worked example · p.4  ◐ noting what it contributes…      │
│                                          │ ──────────────────────────────────────────────────────── │
│                                          │ ^↵ ask the tutor about pinned (0) · c compare pinned     │
│                                          │ practice this question ▸                                 │
```

**W10 — The compare table.** **[RW4d]**

```
│ COMPARE · 3 sources · differences kept · each line quotes its own source       perspectives: [ ]   │
├──────────────────────┬─────────────────────────┬──────────────────────────┬────────────────────────┤
│ source               │ contributes             │ assumes                  │ differs from the others│
├──────────────────────┼─────────────────────────┼──────────────────────────┼────────────────────────┤
│ your passage         │ ◇ mixture as random     │ ◇ components independent │ ◇ only book to derive  │
│ § Probability §5.4   │   component choice      │   of the coin  § "…"     │   the CDF first § "…"  │
│ § Intro §3.2         │ ◇ sums vs mixtures      │ ◇ X, Y independent § "…" │ ◇ treats the sum, not  │
│                      │   contrasted § "…"      │                          │   the mixture § "…"    │
│ § Notes wk 6 p.4     │ ◇ a worked mixture of   │ ◇ —                      │ ◇ numeric, no proof    │
│                      │   normals § "…"         │                          │   § "…"                │
├──────────────────────┴─────────────────────────┴──────────────────────────┴────────────────────────┤
│ your take (optional) › ______________________________________________________   keep comparison ⇄ │
│ ^↵ ask the tutor about these (answers only from these 3 passages)                     esc back      │
```

**W11 — An explorable figure, inline.** **[RW5a]**

```
│         f_X(x) = p·λe^{λx}·[x<0] + (1−p)·λe^{−λx}·[x≥0]                                      │
│  ▾ interactive version · AI-built · matches the book's equation (checked)            ✕ close │
│  ┌──────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ Before you move anything: if λ doubles, what happens to P(X ≤ 0)?                        │ │
│  │   (•) it rises   ( ) it falls   ( ) it stays the same       ↵ answer                      │ │
│  │ ──────────────────────────────────────────────────────────────────────────────────────── │ │
│  │   0.8 ┤                ▄                                                                  │ │
│  │       │                █▆▁                                                                │ │
│  │       │               ▁███▅▂                                                              │ │
│  │       │    ▁▁▁▁▂▂▃▃▄▆▇███████▆▅▄▃▂▂▁▁▁▁▁                                                  │ │
│  │   0.0 ┼░░░░░░░░░░░░░░░░┴────────────────                                                  │ │
│  │        −4              0               4    shade: [P(X ≤ 0) ▾]   readout: 30.0%          │ │
│  │   p  [====|---------] 0.30   λ [===|------] 1.0        ▶ play   t values table            │ │
│  │   what changed? (optional) › ______________________________________                      │ │
│  └──────────────────────────────────────────────────────────────────────────────────────────┘ │
```

**W12 — Last time here / wrap up.** **[RW6a, RW6b]**

```
│ LAST TIME HERE · Thu 9 Oct · about 40 min                          dismiss │
│ ↳ continue at §5.4 ¶6 "Mixtures of continuous…"            ↵ continue      │
│ Still open                                                                 │
│   ? density of a sum — why a convolution?        open · resolved · revisit │
│ Unfinished                                                                 │
│   ✎ Exercise 5.14 · 4 steps · help: check, L1 question, L3 hint resume ▸   │
│ Worth a second look                                                        │
│   ◌ your next-step guess in Example 5.4.2 missed a (1−p)        reopen ▸   │
│   ◌ figure: "λ doubles → P(X ≤ 0) rises" (it stays at p)        reopen ▸   │
│ Since last time                                                            │
│   ● conditional probability — demonstrated on your own (Sat)   on the map ▸│
│ Coming up · checks on your own                                             │
│   Wed   a question that tells apart two readings of your step-3 slip       │
│         about 6 min · why · undo                                           │
│   Mon   a new mixture problem · new setup · about 8 min · why · undo       │
│                                                             undo all       │
│ ▸ summary written by LearnLoop's model from what you did                   │
```

**W13 — A cold check, and the loop back.** **[RW6b, SRC, DL2]**

```
┌ PRACTICE · check · on your own · from your reading · about 6 min                                      ┐
│ ┃ A check on your own. Help is still here — using it makes this practice with help.               │
│ from Intro to Probability · verbatim · new setup                                                    │
│ Let W be … Find P(W ≤ 0) and explain why the CDF of W is continuous at 0.                           │
│ ┌──────────────────────────────────────────────────────────────────────────────────────────────┐   │
│ │ type your answer — $math$ renders as you type                                                 │   │
│ └──────────────────────────────────────────────────────────────────────────────────────────────┘   │
│ ^↵ submit · ^h help (makes it practice with help) · ? ask (same) · ^d I'm stuck · esc today       │

    pressing ^h:   ┌ help · taking any rung makes this practice with help ◌ ─────────────┐
                   │ ▸ 1 a question about your approach    …    5 walk me through it    │
                   └ ↑↓ / 1–5 choose · ↵ take · esc keep it on my own ──────────────────┘

    feedback: the header gains what was withheld (spec D46):
│ Exercise 3.19 · Intro to Probability p.112 · original page ↗ · why this check ▸                     │
    and, when repair is suggested:
│ ↩ back to where you studied this: Exercise 5.14 · your question "why weighted by p?" (§5.4)   ▸   │
```

**W14 — Waiting and failure states, in place.** **[all; §4.0]**

```
│   › why are the densities weighted by p?                                       │
│   ◐ looking in your books… then writing · usually about 9 s · cancel           │   pending
│   ◇ Couldn't reach LearnLoop's model. Your question is kept — try again ↵      │   unreachable
│   ◇ Today's tutor budget ($1.00) is used. The book's passage is still here ▸  │   capped
│ OFFLINE  the sidecar is unreachable — you can keep reading this source;        │   sidecar down
│          asking and checks come back when it does                              │   (header pill)
```

**W15 — A narrow window: working, stacked.** **[RW2a]**

```
┌ WORKING · Exercise 5.14 ─────────── help: balanced ┐
│ § "Let X be Uniform(−1,0) w.p. p and Exp(1)…"      │
│                       show in the book ▾  book open│
│ 1 › F_X(x) = p F_Y(x) + (1−p) F_Z(x)        ≈      │
│ 2 › for x ≥ 0: F_Z(x) = ∫₀ˣ e^{−t} dt       ✓      │
│ 3 › = −e^{−x}                               ? first│
│ ^k check  ^h help  ^d stuck            ^↵ submit   │
└────────────────────────────────────────────────────┘
```

**W16 — The phone: a cold check from reading.** (no new phone RPC; spec D20)

```
┌──────────────────────────────┐
│ check · on your own          │
│ from your reading · ~8 min   │
│ ──────────────────────────── │
│ from Intro to Probability    │
│ verbatim                     │
│ Let X be a mixture of …      │
│ Find the CDF of X.           │
│ ┌──────────────────────────┐ │
│ │ your answer              │ │
│ │                          │ │
│ └──────────────────────────┘ │
│ [ photo ] [ voice ] [submit] │
│ help makes it practice with  │
│ help ◌                       │
└──────────────────────────────┘
```

---

## 7. Accessibility, and the phone

### 7.1 Keyboard only

Every posture is fully operable from the keyboard (§3.5).
- Margin marks are focusable in reading order (`Alt+↓/↑` jumps between them).
- The intent box, palette, ladder, popovers and peeks trap nothing: `Esc` always leaves.
- Focus returns to where it was: closing the ladder returns to the step, and closing a peek returns to the hit.
- Visible focus uses the existing `--border-focus` outline (`:focus-visible` rules in `app.css`). It is never removed.

### 7.2 Screen reader

- **Landmarks:** the source pane is `main` ("Probability, section 5.4"), the rail is `complementary` ("Reading guide", "Ask", "Notes"), the workbench is a `region` ("Exercise 5.14, your work"), and the detour strip is `navigation` ("Detour").
- **Voices are spoken** with the prefixes in §3.4 ("From the book, section 5.4:", "LearnLoop's model:", "You wrote:"). Glyphs are `aria-hidden`.
- **Results** are announced once, politely, never assertively: "Answer ready in Ask", "Check finished: step 3 is the first questionable step". Nothing is announced while the learner types in a step.
- **Math:** KaTeX renders with MathML (`output: "htmlAndMathml"`) in the source, answers and steps, so formulas are read, not spelled.
- **Margin marks** are buttons placed before their paragraph in the DOM, labelled with the full sentence ("Note on this paragraph: connects to a distinction you worked on…").
- **Figures:** sliders are `input[type=range]` with `aria-valuetext` ("p equals 0.30"). Readouts sit in a polite live region throttled to one update per second of dragging. *Values as a table* gives a data table equivalent of every plot (B 379: figures carry meaning text extraction loses, so the reverse must hold too).
- **The ladder** is a radio group with each rung's consequence in its accessible name.

### 7.3 Reduced motion and calm

- No animation anywhere in the Reader by default. With `prefers-reduced-motion`, the figure's *play* becomes *step ◂ ▸*.
- The existing infinite quick-check pulse and blink are removed outright, not just under reduced motion (§4.12, §10 S12).
- Nothing auto-scrolls the source except an explicit jump (crumb, citation, peek, continue). Jumps are instant under reduced motion.

### 7.4 Colour and contrast

- **Never colour alone.** Every status has a glyph and a word (§3.4).
- **Contrast.** Any text that carries meaning uses `--dim` (about 6:1 on `--bg` in the default palette), never `--faint` (`#666778` on `#0e0e0e` is about 3.5:1, under WCAG's 4.5:1 for small text). Labels such as "model's reading", "counts as one hint" and "not checked" are meaning-bearing. Much of today's Reader microcopy is `--faint` at 10–11 px, and RW1a's rail split should fix that as it moves the code.
- Check every new token pairing in the four palettes (`dracula`, `gruvbox`, `nord`, `catppuccin-mocha`) as well as the default. The voice rules (`--purple-pill` dotted, `--amber-mid` solid) must stay distinguishable in each.
- Learner work is never red. Red stays for system errors.

### 7.5 Reading comfort

Long reading in 13 px monospace is hard on the eyes. The PDF surface (the default) shows the book's own typography. For the extracted-text view this design proposes a **reading font** preference, *mono (as today) · proportional*, with a measure of about 70 characters and 15–16 px. The chrome stays mono. The default is §10 Q1.

### 7.6 The phone

v1 has **no Reader on the phone** (mobile spec scope) and **no new phone RPC** (spec D20).

| Phone-visible in v1 | Desktop only |
|---|---|
| Cold checks that are ordinary items, served by the plan (they reach the phone through the existing allowlist), with the same item header, cold banner and help consequence (W16) | The Reader, every posture, margin marks, the intent box, the workbench, library asks, compare, figures, the recap and wrap-up |
| Probe-type checks show the existing *"This is a diagnostic check — continue it on the desktop"* | Inquiries (today's question queue is not on the phone allowlist) |
| Photo and voice answers to those checks (mobile §6.6) | Resume of unfinished problems |

Proposed for later, with defaults in §10:
- a read-only *Last time here* on the phone (Q10);
- photo-of-work into the workbench once DL4's transcription route lands (spec §17, deferred), where the phone would be the camera and the desktop the workbench.

---

## 8. Anti-patterns this design refuses

| Refused | Because (the intention it would betray) | Instead |
|---|---|---|
| **The chat-first tutor**: a long AI essay as the first response | B 828 ("shouldn't immediately return a long AI essay"); B 1252 and 1272 (the textbook is central) | The book's own passage first, then a grounded explanation, then a bridge to your work (§4.2) |
| **Interrupting reading**: pop-up quizzes, auto-opening panels, toasts | B 285–293 (an interrupting reader is worse even if each suggestion is relevant) | Margin marks at a density the learner sets; skim mutes everything (§4.4, §4.12) |
| **Blinking attention-getters** (the current quick-check pulse) | B 106 (a limited attention budget); U5 | A static marker (§10 S12) |
| **Trait labels**: "weak at", "you struggle with" | B 685 (judgmental, and possibly wrong); B 697–699 (a match is not evidence) | "Connects to a distinction you worked on · not yet checked on your own" (§4.4) |
| **Only bad news**: cues that only surface errors | B 709 (reinforce what the learner can do) | `●┆` "a new use of something you've demonstrated"; "since last time ●" (§4.4, §4.8) |
| **Hints that restart or switch routes** | B 510 (the owner's pain); B 727 (forcing the learner to abandon their reasoning) | Hints anchored to the step, "what stands" first, the learner's route kept (§5.6) |
| **Gated help**: "try for 5 more minutes first", greyed-out rungs | B 788 (always able to ask for more); B 994 | All rungs visible and takeable; LearnLoop only suggests (§5.5) |
| **Repeating an ineffective hint** | B 794 (change strategy) | "This doesn't connect" changes the approach at once (§5.7) |
| **Timers and pace pressure** in the workbench | B 329–335 (respect autonomy); B 808 | No clock, no elapsed time, no "taking a while?" (§5.11) |
| **Secretly cold or secretly assisted** | B 1043 | Cold says so; help says what it changes before it happens; the book's visibility is stated (§4.9, §5.9) |
| **Fake consensus across sources** | B 261, 873 | Rows per source, every line quoting its own source; "differences kept" (§4.5) |
| **Hidden personalization** | B 877 (a system that confirms what you already think is counterproductive) | A visible *personalized* chip, switchable (§4.5) |
| **AI passed off as the author's** | B 206; P3 invariant 9 | The three voices everywhere; figure labels follow verification (§3.4, §4.7) |
| **Debt counts**: overdue questions, red unfinished counts | B 106 ("an endless accumulation of … overdue reviews"); DL L9 | Threads with *continue* and *resume*, never totals (§4.8) |
| **Engagement as progress**: streaks, "12 questions asked!", time read | B 470–474 | Reports lead with completed workflows and return to reading; no streak in the Reader (§9) |
| **Reading as mastery**: progress bars that imply learning | B 118 (accepting an explanation or highlighting is not mastery); P3 invariant 6 | The header's "% read" stays labelled as reading. Evidence shows only as `○ ◌ ●` (§3.4) |
| **Hijacked selection**: focus steal, selection that jumps, a tab that flips | B 168–174 | An unfocused intent box; selection never changes the rail (§4.1, §10 S3) |
| **Tab-hunting**: the learner must find the right panel before acting | B 160 ("none of these starts with … navigating to a tab") | The act chooses the posture (§3.2) |
| **"Are you sure?" on safe actions** | DL L2 (no step added to protect a model) | Consequences in the label, and a choose-then-take step where a stray key could reveal something (the help ladder, including during a cold check, §4.9). No confirmation dialog anywhere |
| **A summary as proof** | B 559–561 (a model guess written into a summary and later treated as evidence); B 978 | The narrative is collapsed, labelled, and never a source of `●` (§4.8) |

---

## 9. Evaluating the UX at n = 1

### 9.1 Owner checkpoints (aligned with spec §13)

| After | Owner does | Looks at |
|---|---|---|
| **RW1a** (inquiry) | A week of normal reading; optionally one timed walkthrough: ask → branch → return | The funnel: selections → actions → usable result → **back to the origin passage**; detour round trips (`reader_source_restored`) per inquiry; reconnect answers |
| **RW2a** (scratchpad) | A week of solving beside the book; walkthrough: open → solve → leave → resume | Sessions opened, resumed, submitted, abandoned and left open; resume after restart; time from open to first step (should be seconds, §10 S2) |
| **RW2b** (checks and help) | Two weeks | Help level taken vs suggested, by facet over time; recovery after a check; **"doesn't connect" rate by shortcut**; discriminating questions asked, answered and skipped; check and hint latency against the 10 s target |
| **RW3a/b** (cues) | Two weeks with the density at *normal* | Marks per reading hour; open, check-me and not-relevant rates; density changes; the share of `●` vs `◌` cues |
| **RW4a/d** (library, compare) | Use it when curious; no quota | Asks; tutor-on-request rate; compare and keep rates; organizer lines dropped by verification |
| **RW5a** (figures) | Make two or three figures in the probability chapters | Verified, illustrative, failed and unsupported shares; predictions made and missed; "what changed?" answers |
| **RW6a/b** (return, checks) | Two weeks after DL2 | Recap dismissed vs used; wrap-up opened; checks scheduled, undone (with reasons), retired, served and answered; **cold success after reader work** |

### 9.2 UX measures from rows the spec already logs

No new table is needed. Each measure below reads the events and tables in spec §4.3, §5.7, §6.3, §7.5, §8.5 and §9.4.

- **Return rate:** the share of detours (an inquiry branch, a peek, an open of another source) that end with the learner back at the origin passage within the visit. Target direction: up. This is U1's measure.
- **Detour cost:** the minutes from leaving the origin to returning, with model wait separated out.
- **Proactive load:** LearnLoop-started elements shown per reading hour (`cue_shown`, reconnect shown, section-boundary offers, quick-check availability), against the density setting. This is U5's measure.
- **Waiting behaviour:** the share of model waits during which the learner scrolled, selected or typed. A spinner-watching learner means U9 is failing in practice.
- **Unusable help:** "doesn't connect" replies per hint, by shortcut and help style.
- **Help drift:** the level taken by facet over time. It should fall on facets the learner is demonstrating.
- **Undo reasons on scheduled checks.** These are the only direct evidence about the learner's own cost of a check (§9.3).

### 9.3 Calibrating value of information from the learner's side

The owner asked whether EVSI can be calibrated rather than run on baseless assumptions. Most of that is the decision-value spec's work. The experience adds three signals that cost the learner nothing extra, and one rule:

1. **Realized minutes.** Every served check's actual duration, against its expected minutes, calibrates the cost side (`daily_plan/estimates.py`).
2. **Undo with an optional reason** ("why? (optional)", §4.8). An undo reveals that, to this learner, the check was worth less than its minutes plus burden. The undo rate by purpose and by predicted value is direct evidence about λ and the burden term, which today are heuristic constants (spec §20.4 risk 9).
3. **Skips in the plan** of a scheduled check are the same signal, weaker.
4. **Never ask the learner to rate usefulness.** It is a chore, and the brainstorm measures learning, not satisfaction (B 470–474).

### 9.4 "Does this feel right?" — the owner's first-week checklist

Answer each at the end of the week. A "no" names the screen and the moment.

1. Did anything appear while you were reading that you didn't ask for and didn't want?
2. After every detour, could you get back to exactly where you were with one key?
3. When you asked something, did the book's own words come before LearnLoop's?
4. For every block of text you read, did you know who wrote it — the book, LearnLoop's model or you?
5. Did a hint ever make you throw away work that was fine?
6. Did the help LearnLoop suggested first feel too much, too little or about right? Did changing the help style change it?
7. Did any word make you feel judged, rushed or counted?
8. While a model was working, did you keep reading, or did you watch the spinner?
9. Did *Last time here* help you pick up the thread, or did you dismiss it without reading?
10. Were the checks on your own unfamiliar but fair, and did each say why it was there?
11. Did you avoid the workbench because it felt heavy? If so, where did the weight come from?
12. Is there anything you wanted to do in the Reader that took more than two keys?

The existing *how did that feel* affect tap (`AffectTap`) stays at the foot of an inquiry and of the workbench, never opened automatically, as a place for in-the-moment reactions.

---

## 10. Spec decisions that hurt the experience, and open questions

### 10.1 Proposed changes

| # | Spec (as at `8deb75be`, plus the restoration) | Why it hurts | Proposed change | Phase | Spec ruling (§20.9) |
|---|---|---|---|---|---|
| **S1** | §5.1: "the workbench takes the rail's width" | 360 px is too narrow for multi-line derivations with KaTeX, a verdict column and anchored hints. Steps would wrap to illegibility. | In the working posture the right side takes half the window, resizable and remembered (minimum 480 px). Below 1,040 px the sides stack (W15). | RW2a | Adopted (spec §5.1) |
| **S2** | §5.1: on a selected problem, "imported first through `import_exercises` … the workbench opens when the item exists" | The import is a paid model call that can take tens of seconds. Making the learner wait to write step 1 breaks U9 and loses the moment of wanting to try. | Open the workbench at once with the verbatim selection as the stem. Steps attach to the session immediately, and the session binds to the item when the import completes (`workbench_sessions.practice_item_id` nullable until bound). Check, Help and Submit wait for the item, and say so. | RW2a | Adopted; a multi-part import asks which part (spec §5.1, §5.7, G58) |
| **S3** | §4.2: the intent box opens "with the cursor in it" | Focus moves on every selection, so arrow and page keys stop scrolling. That is the "unpredictable selection" complaint the brainstorm cites (B 168–174). Selecting to copy, or just to mark one's place, gets intercepted. | The box appears unfocused. The first printable key focuses it and is typed into it. `↵` and `Tab` work without typing. Scroll and copy keys keep their meaning. Selection never switches the rail tab (today's code does). | RW1b | Adopted (spec §4.2, D2) |
| **S4** | §4.2: routing happens after ↵ (Decider, ≤ 4 s) | Up to four seconds between ↵ and anything happening, on the most frequent interaction | Route speculatively when typing pauses (about 600 ms). On ↵, use that routing if the text is unchanged. It is cheap ($0.0004 a call, inside `reader_intent.max_calls_per_day`) and makes ↵ feel instant. Empty ↵ still makes no call. | RW1b | Adopted with a change: stops at 80% of the daily call cap, disclosed as sending unsubmitted text, own switch (spec §4.2) |
| **S5** | §4.2: "Let me try the next step" doesn't say what happens to the visible next lines | The answer is printed right under the selection, so the exercise defeats itself or asks the learner to look away. | Fold the following blocks in the source pane until the learner answers or presses *show* (§4.3). Frontend only. | RW1b | Adopted, with a cover on the original-page view (spec §4.2) |
| **S6** | §5.4: "the feedback screen is today's" | Today's feedback returns to the queue or plan. After a Reader workbench submission the learner lands away from the book. | Make "back" from feedback aware of where the attempt came from: an attempt that started in the Reader returns to its problem in the Reader. | RW2a | Adopted (spec §5.1) |
| **S7** | D9: in the Reader the source is visible by default, for every entry | Right for *work through this* on the book's own exercise, wrong for *check me* on a cue and *practice this question*, which are meant to test, and where a visible book silently makes every attempt assisted | The default visibility follows the entry's purpose: *work through this* opens with the book; *check me*, *practice this question* and plan items open without it. Each is one key to flip, with the consequence shown. | RW2a, RW3a, RW4a | Adopted (spec §5.1, D9) |
| **S8** | §6.1 (restored): a per-section budget set by `cues.density` (fewer · normal · more = 1, 2 or 4) | Sections vary from half a page to twelve pages. Two marks in one screenful of a short section is dense; two in a long section may be fine. | Keep the learner's per-section setting and add, at every setting, at most one LearnLoop mark per viewport. Never put a mark on the passage a learner is restored to. | RW3a | Adopted with a change: spacing computed at render, nothing appears or disappears on scroll; not a holdout (spec §6.1–6.3) |
| **S9** | §8.1: the figure is "a panel beside the passage" | Beside means the 360 px rail, too small for a plot with sliders. A figure also belongs to its passage. | Inline under the passage at the text column's full measure, collapsed to one line after it is built, one expanded at a time. | RW5a | Adopted (spec §8.1) |
| **S10** | §9.1: the recap lists position, open inquiries, unfinished problems and misses | It only lists open things. The brainstorm asks the Reader to show capability gains (B 106, 709). | Add **Since last time**: facets whose evidence changed since the previous visit (`●` demonstrated; a check retired as no longer needed), read from the capability ledger. Still a pure read. | RW6a | Adopted, read from `lo_certification` (spec §9.1) |
| **S11** | §9.1 (restored): leaving a source after activity shows the Wrap up offer as a self-dismissing one-line note | Right not to block closing, but a note in a Reader the learner is leaving is gone before it can be read | Keep `w` and the rail-footer offer. Show the leaving note **at the destination** (Today, the library) for one view, never in the screen being closed. | RW6a | Adopted; Today renders it from a Reader read (spec §9.1, §18) |
| **S12** | Not in the spec: the existing quick-check signal (`ll-reader-guide-alert` pulse, `ll-qc-blink`, the uppercase strip) | It is an infinite animation in the reader's peripheral vision, against U5 and the spec's own W12 spirit | Replace it with a static `◆ n` on the Guide tab and remove the strip. Add "no LearnLoop-started animation in the Reader" to W12. | RW1a (rail split) | Adopted with a change: a fix for every learner, no switch (spec §4.1) |
| **S13** | §5.1: "Abandon closes it" | One mis-click closes a problem the learner may want back. The steps are kept anyway. | Keep Abandon off the main action row (in `⋯`) and make it reversible: *reopen* sets the session back to `open` when no attempt was written. No confirmation dialog. | RW2a | Adopted (spec §5.1) |
| **S14** | §5.2: "doesn't connect" shortcuts: different approach · too big a jump · notation | The owner's pain is a hint aimed at the wrong place, and that isn't among the shortcuts | Add *that's not where I'm stuck* (with the step picker), making four shortcuts. | RW2b | Adopted; the picked step becomes the next hint's anchor (spec §5.2) |
| **S15** | §9.3: follow-ups listed in the card | With no count cap a session may schedule several. A list can read as homework. | Show them as a dated timeline with purpose, *why* and *undo*; no totals. Retirements are positive ("no longer needed: you solved one like it…"). Undo takes an optional reason, used for calibration (§9.3). | RW6b | Adopted; undo's reason is calibration data (spec §9.3, §15) |
| **S16** | §4.1: the reconnect line "in the rail" | The learner's eyes are on the passage they returned to, not the rail | Also one dim line under the root passage, only on a return the learner started (§4.2, W4). The only inline element LearnLoop adds to the text column. | RW1a | Adopted (spec §4.1) |
| **S17** | §14: no gate covers the experience rules | The firewall gates protect evidence, but nothing protects attention, focus or voice | Add gates. No focus change on selection or on a result landing (vitest). No `animation` in Reader CSS outside figures under *play*. Every model-text component renders a voice label (lint). Meaning-bearing copy uses `--dim`, not `--faint` (lint on the label components). | RW1a, and each phase | Adopted with a change: gates G54–G58, the CSS lint also covers transitions (spec §14) |

### 10.2 Open questions, with recommended defaults

| # | Question | Recommended default | Spec decision |
|---|---|---|---|
| **Q1** | Reading font for the extracted-text view: keep 13 px mono or offer proportional? | Offer *mono · proportional* in Settings. **Default mono**, the owner's established look; the PDF surface is the default anyway. Revisit after RW1a's week. | D29 |
| **Q2** | Should the rail collapse in the reading posture by default? | No. The default is open at 360 px, with `\` remembered per device. | D30 |
| **Q3** | Help style: global, or per subject? | Global and remembered, with a per-session override in the workbench header. | D31 |
| **Q4** | When the learner takes "a short problem from your books that tells these apart" mid-problem, should it open in the same workbench posture or go to the plan? | The same posture, as a second session with a crumb back; the original problem stays open (§5.8). The restored spec already settles that the question itself counts as a level-1 hint, and the label says so before it is answered. | D32 |
| **Q5** | Margin mark density default | *Normal* (2 per section, and 1 per viewport). *Fewer* is one key away from every mark. | D33 |
| **Q6** | What counts as "activity" for the Wrap up offer (spec §9.1)? | At least one inquiry, workbench session, formative answer (next step, why step, prediction) or kept comparison. Scrolling, highlights and cue taps alone don't, because a pure reading session has nothing to wrap. | D34 |
| **Q7** | Show money on paid actions (figures, imports) in the routed line? | No by default; show it only when a route's daily cap is within 20%. The owner set the caps and sees spend in the reports. | D35 |
| **Q8** | Show all scheduled checks in the recap, or only the next few? | The next three by date, then *later ▸* with no number (a number would be the count U12 forbids), because a timeline is easier to read than a list. Retired checks show for one visit. | D36 |
| **Q9** | What does *not right?* do on a gap the model named from the learner's text? | It appends a `learner_card` verdict `different` with optional text and hides the gap from cue targets for this learner. The learner-text-gaps owner confirms that the pipeline can honour it. | D37 |
| **Q10** | A read-only *Last time here* on the phone? | Not in v1 (D20). Revisit when the mobile client is used most days. | D38 |
| **Q11** | Figure animation default | Off: *play* on request; step buttons under reduced motion. | D39 |
| **Q12** | Should *check me* from a cue open in the Reader or on the practice screen? | In the Reader's working posture, book hidden (§4.4, S7), so the learner returns to the passage. | D40 |
| **Q13** | Rail tab switching on a routed Ask: should the answer open the Ask tab? | Yes, because the learner asked; that is their act, not an interruption. Answers that arrive while the learner is in another posture only mark the tab. | D41 |

---

## 11. Map: UX element → spec phase

### 11.1 Built by a phase

| UX element | Section | Phase |
|---|---|---|
| Five postures on one page; the act chooses the posture | §3.1–3.2 | RW1a (rail split) + each posture's phase |
| Detour strip, return stack, `Alt+←/→` | §3.2, §4.2 | RW1a (return stack: **[UX→RW1a]**) |
| Three voices and the evidence vocabulary (`§ ◇ ›`, `○ ◌ ●`, check markers) | §3.4 | RW1a (shared components), applied by every phase |
| Margin gutter and legend | §3.4 | RW3a (gutter); RW1a (`?` marks); RW2a (`✎`); RW4d (`⇄`); RW5a (`◇▸`) |
| Keyboard map | §3.5 | each phase for its own keys; RW1a for the Reader-wide ones |
| The seven-state contract for model actions | §4.0 | each model-backed phase (RW1b, RW1c, RW2b, RW3b, RW4a, RW4d, RW5a, RW6b) |
| Intent box (unfocused, type-to-focus, speculative routing) | §4.1 | RW1b (S3, S4 adopted) |
| Palette grouped by the five intentions | §4.1 | RW1b (restored) |
| Branching inquiry, statuses, reopen | §4.2 | RW1a |
| Reconnect line (rail and inline) | §4.2 | RW1a (S16 adopted) |
| Book first, three answer modes; *another way*, *that didn't help*; offered follow-ons | §4.2 | RW1c, with SRC's `find_sources` intents |
| Next step with fold; why step; what does this assume; reconstruct later | §4.3 | RW1b (fold: S5 adopted) |
| Margin cues, popover, actions, "why" line | §4.4 | RW3a (Guide cues), RW3b (discovered, `●┆`, `▹┆`, ordering) |
| Cue density control (fewer · normal · more), per-viewport limit | §4.4 | RW3a (density control, restored); per-viewport limit S8 adopted in RW3a |
| *Check me* in the Reader with the book hidden | §4.4 | RW3a + RW2a (S7 adopted) |
| Library ask beside the source, sources first, peek, pin, personalized chip | §4.5 | RW4a |
| Roles (counterexample, contrast, prerequisite …) on hits | §4.5 | RW4e (restored); concept-graph subheads RW4a (restored) |
| Compare table, perspectives, claims, inferences and your take kept apart, keep comparison `⇄` | §4.5 | RW4d (restored) |
| Practice this question with textbook exercises | §4.5, §4.6 | RW4a + SRC |
| Find an exercise in my sources | §4.6 | RW4b |
| Item header provenance, cold-safe source naming, novelty labels | §4.6, §4.9 | SRC + RW6b (novelty labels restored) |
| Explorable figure inline, prediction, shaded areas, PMF bars, play, region selection, "what changed?" | §4.7 | RW5a (inline: S9 adopted) |
| Figures offered by the tutor and the library; more figure kinds | §4.7 | RW5b (restored) |
| Last time here card | §4.8 | RW6a |
| Since last time (`●`, retirements) | §4.8 | **[UX→RW6a]** (S10) |
| Wrap up at the destination | §4.8 | RW6a (restored; S11 placement) |
| Narrative, collapsed and labelled | §4.8 | RW6b |
| Coming up timeline, why, undo, undo all, undo reason | §4.8, §4.9 | RW6b (S15) |
| Cold banner, help consequence line, back to where you studied this | §4.9 | RW6b (restored) + DL2 (serving) |
| *ⓘ where this goes*; named-gap line | §4.10 | RW1b, RW2b, RW5a (sources of learner text); learner-text gaps |
| Reading path in the Guide | §4.11 | RW7a (restored); plan following the path RW7b |
| Static quick-check marker, no pulse | §4.12 | **[UX→RW1a]** (S12) |
| Workbench split, opening at once, book choice line | §5.1 | RW2a (S1, S2 adopted) |
| Step editor, history, delete with undo, verdict column | §5.2 | RW2a (editor); RW2b (verdicts) |
| Dependencies and assumptions in the check | §5.2, §5.4 | RW2b (restored) |
| Saving states, leave for now, abandon with reopen, resume | §5.3 | RW2a (S13 adopted) |
| Check my work, error-kind guess | §5.4 | RW2b |
| Help ladder, suggested rung, why, choose/take separation | §5.5 | RW2b |
| Anchored hints, "what stands", leak and cap messages | §5.6 | RW2b |
| Compare with the book; route-matched examples | §5.6 | RW2b (bridging); RW2c (`find_examples`, restored) |
| "This doesn't connect" with four shortcuts | §5.7 | RW2b (S14 adopted) |
| A question before a hint | §5.8 | RW2b (restored) |
| Submit record line, origin-aware back, compare methods | §5.9 | RW2a (S6 adopted); RW2c (compare methods, restored) |
| I'm stuck in the workbench | §5.10 | RW2a (step kind); RW2b (to the hint writer and text gaps) |
| Help style control and tone rules | §5.11 | RW2b |
| *Work in steps* on the practice screen | §5.12 | RW2a |
| Accessibility rules (landmarks, voices spoken, MathML, live regions, contrast) | §7 | RW1a (shared components) and each phase's vitest |
| Phone: cold checks with provenance | §7.6 | RW6b + SRC; no new RPC (D20) |
| UX gates (focus, animation, voice labels, contrast) | §10 S17 | **[UX→RW1a]**, then every phase |
| UX measures (return rate, detour cost, proactive load, waiting behaviour) | §9.2 | RW1a's report, extended per phase |
| Undo reasons as calibration data | §9.3 | RW6b; read by the decision-value calibration work |
| Workbench field signals | — (invisible) | RW2d (successor); no new UI |
| "What helps this learner" record | — (invisible; shapes hints and the chooser) | RW2c |

### 11.2 Deferred, and where each would live in this design

The restored spec labels these DEFERRED (spec §17). Each has a place in this design, so building it later doesn't need a new posture.

| Deferred | Where it would appear |
|---|---|
| Generated-code figures in an isolated surface | the same inline figure slot (§4.7), labelled *"AI-generated code, sandboxed"* |
| Page-image (visual) retrieval | library hits gain a page thumbnail beside the `§` excerpt (§4.5) |
| OS-level or MCP learning service; browser or editor capture | the capture box and inbox (DL C1–C4); questions arriving from elsewhere open as inquiries in the returning posture |
| Local rerankers | invisible; shows only as lower latency in the pending lines |
| Learned cue and hint policies | invisible; the ladder's *why?* would name the policy |
| Formative signals as numeric observations | invisible; W1 tier 2 would change, not the UI |
| Alternative reference routes in solution graphs | the hint label's *"a different approach"*, and *show me the book's way* listing routes |
| Formal verification of proof steps | a new check method behind `✓ checked` (§3.4) |
| Cross-learner data-driven hints | not applicable at n = 1 |
| A learned, causal model of which help works | the ladder's *why?*; RW2c's record is its data |
| A randomized whole-workflow experiment | not planned at n = 1 |
| Whole-library claim extraction with a claim matcher | the compare table's claims band (§4.5), filled ahead of time |
| The router's availability pass | now built by the sources spec (`practice_availability`), with its router wiring deferred there; invisible here, plan blocks would include more source-exercise checks |
| A CAS calculator in the workbench | a *calc* step kind in `⋯`, with its own assistance label |
| Photo of handwritten work as steps | the phone as camera (§7.6), steps arriving in the desktop workbench in the learner's voice with *transcribed by LearnLoop's model* |
| Randomized hint-quality experiments | not planned |

---

*Related:* `docs/specs/spec_reader_workbench_v1.md` · `docs/specs/spec_source_practice_and_probes_v1.md` · `docs/reviews/reader-dialogue-coverage.md` · `docs/brainstorming/Improving Reader's design.md` · `spec_p3_reader_integration.md` (§1.1, §5, §11) · `spec_daily_loop_v1.md` (§2, §5.2, §6, §7) · `spec_mobile_tailnet_v1.md` · `apps/learnloop-tauri/src/screens/KnowledgeWellView.tsx` (the evidence vocabulary this design borrows)
