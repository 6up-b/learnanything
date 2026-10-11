# LearnLoop — User intentions v2

**Working design draft · October 11, 2026**

This is an expanded proposal based on `User intentions(1).md`. It preserves the original emphasis on chosen memory and skill, frictionless capture, canonical sources, teach-back, transfer, efficient diagnosis, and minimal repair. The added intentions and acceptance criteria are proposed product requirements, not claims that all of these experiences are currently implemented or experimentally validated.

## 1. The central intention: make memory and skill a choice

I want to choose which knowledge and capabilities become a dependable part of what I can do. When I invest attention in understanding something, I want that investment to remain useful rather than disappearing after the conversation, reading session, or project ends.

I want LearnLoop to help me acquire and retain knowledge, while connecting both to a third loop: using knowledge to reason, solve, build, explain, and participate in work that matters to me. Curiosity is also a sufficient reason to learn; I should not need a career objective or an elaborate project plan to justify an interest.

This is not a promise of effortless expertise or permanent perfect recall. It is a promise of meaningful control over what I pursue, how deeply I pursue it, what I choose to maintain, and how much attention I am willing to spend.

The system should manage clerical work and coordination. It should support, not replace, the thinking and practice through which I become capable.

## 2. Journeys and entry points

There are two main journeys in the original intention: **learning something** and **retaining it**. Both should connect naturally to **using it**, and to returning when my goals or circumstances change.

There are also two main entry points, which are different from those journeys:

- **A specific thing:** a difficult problem, a passage, a diagram, a question, an explanation, a project decision, or a mistake I want to understand and remember.
- **A canonical source:** a paper, textbook, lecture, or other substantial resource that I want to work through at an appropriate depth.

I should be able to move between these entry points. A project question might lead to a textbook section; reading that section might produce a question, a practice task, or a change to the project. I should not have to duplicate the same idea into disconnected workflows.

## 3. Capture the thing and why it matters—not just a flashcard

When something interests or challenges me, I want to save it without interrupting what I am doing. A capture should preserve the relevant source, location, surrounding context, and any question or interpretation I supplied.

I should be able to save a math problem, mark an equation, point at a figure, capture code, or preserve a useful tutor exchange. I should not have to decide how to turn it into an ideal question-and-answer pair at that moment.

Saving something should not automatically enroll me in indefinite practice. I want distinguishable intentions such as:

- Keep this as a reference or tentative interest.
- Help me understand this now.
- Check once later whether I retained this.
- Help me maintain this capability.
- Help me develop this capability further.

These are examples of intentions, not a requirement to present a large menu every time. Sensible defaults and progressive disclosure should keep common actions simple.

The system may propose useful practice, but proposals are not commitments. A captured item must remain accessible even when I decline practice. Asking for a connection or an explanation must not silently create an ongoing memory obligation.

## 4. Express what I want to be able to do

For material I adopt into practice, I want an understandable capability target rather than an unexplained collection of cards.

A target should connect the thing I care about to an observable outcome, with enough context to make “good enough” meaningful. For example:

> Explain and defend the temporal-model choice in my gesture project, trace the main computations, and reason about a changed deployment constraint without relying on the original explanation.

Or:

> Solve fresh problems of this kind from a blank page, justify the important steps, and recognize a similar-looking problem for which the method does not apply.

The system should help define scope, relevant task types, acceptable assistance, desired depth, and any deadline. It should suggest these details rather than requiring me to complete an assessment-design form.

A source can contain more knowledge than I currently need. LearnLoop should make exclusions visible without presenting them as failures. It should also suggest important omitted concepts that a novice might not know to request, while leaving me able to accept or reject the suggested scope.

## 5. Keep depth separate from ongoing obligation

I may want a deep understanding of one narrow idea without agreeing to an ever-expanding curriculum. Conversely, I may want a light, ongoing connection to a broad field without trying to master its technical details.

The existing depth vocabulary—`keep_in_touch`, `remember_key_ideas`, `work_fluently`, and `master_tasks_like_these`—can serve as starting presets. The user-facing experience should explain the actual capability and activity implications, not rely on the label alone.

Depth is separate from whether a commitment is active, paused, reference-only, satisfied, or stopped. A one-time delayed check is different from indefinite maintenance. Reaching a target should permit closure, not automatically expand the target.

When I ask to keep developing, LearnLoop may propose deeper tasks within the scope I authorized. It should ask before substantially widening that scope or increasing the recurring burden.

## 6. Understand flexibly, not just reproduce familiar answers

I want to explain an idea, connect its parts, justify decisions, examine assumptions, and adapt it when conditions change.

For a project, I want to answer questions such as: What does this component do? Why was this decision made? What alternatives were considered? What would change under another constraint? What evidence would show that the design is failing?

For a paper, I want to understand its equations and diagrams, distinguish its contribution from its setup, identify assumptions and limitations, and explain what follows from its results. LearnLoop must distinguish the authors’ stated reasons from a plausible interpretation or an unresolved question; it must not invent motives and teach them as facts.

For mathematics, I want to reconstruct a valid complete solution through cold retrieval, explain why its important steps work, and transfer the approach to fresh problems. An equally valid alternative solution should not be marked wrong merely because it differs from a stored solution.

Practice should address not only execution after the method has been named, but recognizing when to use a method, choosing among alternatives, and recognizing when not to use it.

## 7. Let practice evolve while preserving a stable target

The same capability may benefit from different activities at different times: a worked example, a prediction, a short explanation, an error hunt, a partial solution, an independent solution, a counterexample, a teach-back, or an authentic project task.

I want the activity to reflect what would help now. New wording alone is not sufficient variation. Fresh practice should vary the relevant representation, assumptions, task structure, or required decision while remaining faithful to the intended capability.

Short interactions should coexist with longer work. I should not need to produce an essay for every memory check, but I should also not be told that rapid recognition demonstrates the ability to construct a solution.

Generated tasks need quality control. Their assumptions, expected evidence, acceptable answers, and source grounding should be inspectable. Where suitable checks exist, mathematical and code tasks should use them. An ambiguous or unverified task should not confidently downgrade my learning record.

## 8. Read and make sense of canonical sources without losing the source

I want to read the original source, ask questions at the point of confusion, explore an explanation, and return to where I was reading. Explanations should be a layer around the source, not an untraceable replacement for it.

A clarification may branch into subquestions. Those branches should preserve what prompted them and remain revisitable without forcing me to reconstruct a long chronological chat.

My annotations should be able to record confusion, a tentative interpretation, a connection, a disagreement, an unresolved question, or something I want to revisit. Not every annotation should become a graded task.

I want help synthesizing across sections and sources, not only recalling isolated passages. LearnLoop should distinguish what a source states, what follows by derivation, what is a synthesis across sources, and what remains speculative or disputed.

“Fully extract the knowledge” should mean covering the capabilities and material I deliberately chose, with visible gaps and limitations. It should not mean converting every sentence into a permanent review obligation or claiming complete mastery of a field.

## 9. Support authentic use and return me to it

When I encounter a gap while building, debugging, analyzing, or discussing something, I want help that is connected to that work. A repair should end with a return to the task that made the gap matter.

For my gesture model, practice might culminate in explaining an actual module, predicting the effect of a modification, designing a comparison, or interpreting a result—not only answering detached questions about recurrent networks.

Useful work may provide learning evidence when the system can establish what I actually did and what assistance I used. Merely observing that I opened a file, read a paragraph, or accepted generated code is not evidence that I can perform the underlying task independently.

Connections to editors, notebooks, browsers, and preferred assistants should use explicit permissions. The learning record should remain portable across interfaces and models; broad background monitoring should not be required.

## 10. Give me a finite, humane daily plan

When I arrive, I want to know what is worth doing within the time and energy I actually have. The queue should allocate attention across my chosen commitments rather than allowing every captured concept to compete indefinitely.

A session should have a clear purpose, a realistic size, and a stopping point. “Today is complete” should mean I completed the agreed attention budget, not that no knowledge remains uncertain.

The plan may recommend maintenance, repair, development, source reading, project work, or no intervention. Maintenance must not silently become escalation.

When my commitments exceed my budget, LearnLoop should expose the tradeoff: reduce scope, accept lower availability, pause something, or allocate more time. It should not promise that an unlimited collection can be maintained without cost.

After a break, I want a manageable re-entry rather than a debt-collection screen. The system should help me choose what still matters, estimate what may need attention, and offer a small number of useful checks. It must not reset the clock as though no forgetting could have occurred, nor claim that an estimate is a fresh demonstration.

## 11. Diagnose only when it improves what happens next

I want important mistakes and misconceptions identified before they become recurring obstacles. I also want room to think, notice my own error, and ask directly for help.

A wrong answer can arise from several causes, including an ambiguous question or a grading error. LearnLoop should not assign a confident misconception merely because one explanation seems plausible.

When different possible causes would require different interventions, a short discriminating probe may be worthwhile. When the same safe, minimal repair is suitable across the plausible causes, further interrogation may be unnecessary.

The objective is to minimize avoidable diagnostic and coordination effort while supporting durable learning—not to minimize all questions regardless of learning value. Necessary practice and unnecessary diagnosis are different costs.

A repair should preserve correct work, address the relevant gap, and give me an appropriate opportunity to use the corrected understanding. Later independent evidence is needed before describing a repair as durable.

## 12. Tell me what I have demonstrated, with honest limits

I want to know what I can do with support, independently now, after a delay, and on a meaningfully unfamiliar task. These are different claims.

A learning record should preserve the task, my response, the assistance and source access available, the time and context of the attempt, the relevant grading criteria, and uncertainty in the interpretation.

Immediate agreement with a tutor, a successful hinted response, or a fluent teach-back of a familiar explanation must not be treated as interchangeable with independent delayed performance.

The interface should distinguish historical demonstrations from current predictions. “Not yet tested” should remain different from “cannot do.” Coverage of source topics should remain different from demonstrated capability.

I should be able to inspect and contest a grade, repair an ambiguous prompt, correct a source interpretation, and revise a goal. Corrections should update derived learning state without erasing the original record of what happened.

## 13. Preserve agency, curiosity, and accessible participation

I should be able to ask for a direct answer, choose a hint, skip an activity, change the session length, or decline a learning commitment. The system should make the evidential consequences clear without withholding help to force compliance.

I want response modes appropriate to the task: concise text, speech, mathematical working, diagrams, code, or other artifacts. Input burden and presentation style should not unnecessarily become proxies for subject knowledge.

Some valuable activities are reflective rather than assessable: noticing a connection, forming a research question, reconsidering a design preference, or preparing for a conversation with another practitioner. These should not require artificial correctness scores.

The system should help me retain the reason I cared about an idea and notice progress that matters in my life. It should not make me primarily manage cards, optimize streaks, or satisfy the tutor’s agenda.

## 14. Observable product acceptance criteria

These are proposed tests of the experience, not reports of completed validation.

1. **Capture without debt.** I save a difficult passage and resume reading immediately. It remains available, but no ongoing practice begins until I choose it.
2. **Targeted capability.** I adopt a project question, accept a plain-language outcome, and receive an appropriate first activity without manually constructing a curriculum.
3. **Source continuity.** I follow a branching clarification and return to the exact source location, with its assumptions and unresolved questions preserved.
4. **Bounded repair.** A mistaken step is corrected without re-teaching correct work or demanding extra probes that would not change the intervention.
5. **Independent transfer.** A later unfamiliar task can reveal that a previously fluent explanation was insufficient; the record represents that distinction honestly.
6. **A real stopping point.** A short session ends at the agreed budget. New captures do not create an invisible recurring burden.
7. **Humane re-entry.** After a lapse, I can resume with a small useful session and choose priorities without clearing every overdue item.
8. **Contestability.** I can challenge an invalid question or grade without being forced to accept a false weakness in my record.
9. **Return to work.** A learning episode culminates in meaningful progress on the original problem or a clearly chosen capability.

## 15. Success and non-goals

The primary outcome to evaluate is improvement in delayed, appropriately independent performance on relevant fresh tasks, alongside usefulness in authentic work and sustainable attention cost.

Supporting measures can include capture-to-use friction, avoidable diagnostic time, assistance required, trust in feedback, unwanted commitments, and successful return after interruptions. Generated-card counts, conversation length, and streaks are not sufficient measures of success.

LearnLoop is not trying to memorize every source, eliminate all productive struggle, certify universal mastery, turn every interaction into an exam, or require a new social platform or all-seeing agent before it becomes useful.

## Research informing this expansion

The original document supplies the core intentions. The sources below provide design observations and adjacent-product examples; they do not establish that this complete proposed design will produce the intended outcomes.

- Andy Matuschak, *How Might We Learn?* — authentic pursuits, contextualized study, dynamic practice, and preserving canonical artifacts. https://andymatuschak.org/hmwl/
- Andy Matuschak, *Idea-centric memory system* — ideas rather than fixed prompts as durable objects of practice. https://notes.andymatuschak.org/z7wCFe7MP9VeCVApcBLC7SN
- Andy Matuschak, *Highlight-driven practice and comprehension support* — reader control and gradual commitment. https://notes.andymatuschak.org/zPNoWjs5jQ7iMDpxxBtjSbg
- Andy Matuschak, *Prompt-writing supports reading comprehension* — useful intellectual work, authoring costs, and obligations. https://notes.andymatuschak.org/zSv7fL6SRMchq1bvuoQjrxz
- Andy Matuschak, *How to write good prompts* — task design, multi-angle understanding, and iterative authoring. https://andymatuschak.org/prompts/
- Hacker News, *Spaced repetition systems have gotten better*, May 2025 — first-person reports about capture friction, authoring, context, and generalization. Qualitative leads, not a representative sample or controlled evidence. https://news.ycombinator.com/item?id=44020591
- Hacker News, *Anki – Powerful, intelligent flash cards*, January 2024 — contrasting experiences with backlogs, limits, and sustainability. https://news.ycombinator.com/item?id=39163094
- Readwise, *How to Increase Retention with Mastery* — highlight-to-active-recall workflow. https://docs.readwise.io/readwise/guides/mastery
- RemNote, *Guided Learn Mode* — source-based study plans, practice, and progress tracking. https://help.remnote.com/en/articles/15724936-guided-learn-mode
- Google Workspace, *New ways to customize and interact with your content in NotebookLM*, March 2026 — saved quiz/card progress and review controls. https://workspaceupdates.googleblog.com/2026/03/new-ways-to-customize-and-interact-with-your-content-in-NotebookLM.html
- SuperMemo, archived *Incremental reading* documentation — staged extraction, retained context, and prioritization under excess material. https://super-memory.org/archive/help/read.htm
