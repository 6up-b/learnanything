
# LearnLoop: Revisiting the user intentions and product design

My central conclusion is that LearnLoop's current technical direction is well aligned with your intentions, but its product design needs to evolve beyond an adaptive tutoring and spaced-repetition system into a system for developing, maintaining, and actually using knowledge.

The distinction matters because the document describes something more ambitious than remembering information or completing a curriculum.

You want to encounter something interesting or difficult, decide that it matters to you, and have a system help you:

1. Understand it deeply, without mistaking familiarity for understanding.
    
2. Retain it for as long as it's useful.
    
3. Reconstruct, explain, and reason about it independently.
    
4. Generalize it to unfamiliar problems, alternative assumptions, and real work.
    
5. Do all of this with the smallest necessary amount of effort, rather than managing an ever-expanding study backlog.
    

Your two journeys—learn something and retain something—capture the core of this vision. But I think our previous research reveals a missing third journey: use something to think, create, solve, or make a decision.

That third journey should substantially influence the first two.

## 1. What your document gets right

Your opening principle, "memory and skill be a choice," is particularly important.

It closely echoes Andy Matuschak’s formulation that [spaced repetition can make memory a choice](https://notes.andymatuschak.org/Spaced_repetition_memory_systems_make_memory_a_choice). His insight is that remembering something need not be left entirely to chance: you can deliberately commit to making information durable.

LearnLoop extends this from individual memories to capabilities. The learner isn't merely choosing to remember what a GRU is. They're choosing to become capable of explaining, modifying, and defending the architecture of a GRU-based gesture recognition system.

There are three particularly strong principles in your document.

First, learning should begin with the learner's own intellectual needs. You give examples from real projects, arXiv papers, and difficult mathematics. This is much stronger than beginning with a textbook chapter or an automatically generated collection of flashcards.

Second, recall is not equivalent to understanding. You explicitly require counterfactual reasoning, step-by-step derivations, teach-back, and transfer. This lines up with Michael Nielsen’s [essay on spaced repetition and mathematical understanding](https://cognitivemedium.com/srs-mathematics), which describes mathematical understanding as something that can be progressively deepened rather than simply acquired once.

![](https://www.google.com/s2/favicons?domain=https://cognitivemedium.com&sz=32)

cognitivemedium.com

+1

Third, you recognize that knowledge maintenance competes for limited attention. Your distinction between learning a concept in depth and merely maintaining it is crucial. Without it, every successful capture creates a future obligation. Eventually, the software risks becoming something the learner has to maintain rather than something that helps the learner.

## 2. The biggest missing product principle

I would add the following as a foundational principle:

> The durable unit of LearnLoop should not be a flashcard, question, or source document. It should be a learner-owned commitment to a particular capability, grounded in the context that makes that capability valuable.

A question is an instrument for developing or testing the capability. A source is supporting material. A learning session is an intervention. None of these is necessarily the thing the learner actually cares about.

This follows naturally from Matuschak's evergreen-notes philosophy, where notes are organized around evolving ideas rather than being permanently attached to the book or project in which they originated.

![](https://www.google.com/s2/favicons?domain=https://notes.andymatuschak.org&sz=32)

Evergreen notes should be concept-oriented

+1

For LearnLoop, I would take that one step further: organize the learner's experience around meaningful capabilities and intentions, while preserving concept and facet identities underneath for inference and reuse.

That doesn't mean replacing your existing Learning Objects, knowledge graph, facets, diagnostic probes, or scheduler. It means giving them a clearer learner-facing purpose.

## 3. What our previous research adds

Looking again at Matuschak, Nielsen, Anki, RemNote, Math Academy, and the relevant Hacker News discussions, I see five recurring user needs.

|User need|What the research suggests|Implication for LearnLoop|
|---|---|---|
|Remember what's personally meaningful|Disconnected prompts become burdensome|Attach learning to meaningful intentions and live projects|
|Make capture effortless|Moving from reading to creating practice is still frustrating|Capture from the current context without forcing immediate setup|
|Learn through actual problems|Flashcards alone are insufficient for many complex skills|Treat authentic problem-solving as a first-class learning activity|
|Avoid review debt|Rigid queues become overwhelming after interruptions|Allocate attention by value and capacity, not just due dates|
|Trust what the system says you know|Reviewing familiar prompts can create misleading confidence|Require fresh, independent, appropriately difficult evidence|

These aren't all universal findings. Hacker News is a useful source of experienced-user complaints and design hypotheses, not a representative user survey.

### The particularly important Matuschak insight

One of Matuschak's notes argues that the critical optimization target for memory systems is not merely scheduling efficiency, but the learner's emotional connection to reviewing material.

He describes the danger of review sessions becoming obligations detached from meaningful activities. His related note on orphan prompts emphasizes the importance of connecting new material to ideas the learner already cares about.

![](https://www.google.com/s2/favicons?domain=https://notes.andymatuschak.org&sz=32)

notes.andymatuschak.org

+1

That is directly relevant to your concern about every concept demanding increasingly difficult questions.

A perfectly optimized review algorithm can still produce a terrible product if the learner no longer values what it's scheduling.

### What the Hacker News comments reveal

Three discussions are especially useful:

- In [Spaced repetition systems have gotten better](https://news.ycombinator.com/item?id=44020591), users describe the missing bridge between reading material and reviewing it, and the difficulty of managing long-term workloads.
    
- In [Anki-fy your life](https://news.ycombinator.com/item?id=35210452), experienced learners describe how solving fresh mathematical problems can be more productive than repeatedly reviewing static cards.
    
- In the more recent [A love letter to flashcards](https://news.ycombinator.com/item?id=48861319) discussion, users describe both the benefits of consistent repetition and the limitations of memorizing fixed prompts. One commenter describes generating new contextual examples rather than reviewing the same sentence repeatedly. Others raise reliability concerns about generated examples.
    
    ![](https://www.google.com/s2/favicons?domain=https://news.ycombinator.com&sz=32)
    
    Hacker News
    
    +2
    

The lesson I draw is that LearnLoop should schedule repeated engagement with knowledge, not necessarily repeated presentation of the same question.

This is also where LearnLoop can offer something meaningfully different from existing software. RemNote already supports PDF-grounded tutoring, AI-generated cards, annotations, and spaced review. Math Academy already uses prerequisite relationships and recognizes that advanced problem-solving can implicitly rehearse earlier knowledge. Those features alone are no longer a compelling differentiator.

![](https://www.google.com/s2/favicons?domain=https://help.remnote.com&sz=32)

RemNote Help Center

+1

The opportunity is to combine them with precise learner-specific diagnosis, varied authentic tasks, explicit goals for depth, and reliable evidence about what the person can actually do.

## 4. Important: LearnLoop already implements part of this vision

I also inspected the current `6up-b/learnanything` repository, rather than judging solely from our earlier architectural conversations.

Several of the changes I would ordinarily recommend are already represented in code.

|Existing component|What it provides|My assessment|
|---|---|---|
|`curriculum/commitments.py`|Durable learner intentions, depth presets, policies, and dispositions|Strong foundation|
|`curriculum/commitment_arcs.py`|A staged progression from comprehension through transfer and revisiting|Directly aligned with your intentions|
|`reader/reader_capture.py`|Source-anchored capture, including explicit remember/test actions|Substantial progress on frictionless capture|
|`reader/reader_quick_check.py`|Source-grounded comprehension checks|Useful formative feedback without claiming mastery|
|`reader/reader_restoration.py`|Restores source context and annotations after cold assessment|Important separation of testing from teaching|
|`substrate/activities.py`|Activity family, card, surface, and administration identities|Foundation for varying questions without corrupting evidence|
|`tutor/question_queue.py`|Durable outstanding questions with learner-controlled resolution|Preserves confusion instead of treating every AI answer as closure|

These are real implementation surfaces, not merely ideas from the new intentions document. You can inspect them in the [current LearnLoop source](https://github.com/6up-b/learnanything/tree/main/src/learnloop) and the [v-next design specification](https://github.com/6up-b/learnanything/blob/main/docs/specs/spec_new_improvements_v2.md).

For example, the current commitments module already supports these four depth presets:

- `keep_in_touch`
    
- `remember_key_ideas`
    
- `work_fluently`
    
- `master_tasks_like_these`
    

This is remarkably close to the distinction you've just articulated between maintenance and deep learning.

Likewise, the commitment-arc implementation already describes the sequence:

Current architecture's learning-stage vocabulary; advancement is intended to depend on evidence, not a fixed calendar.

I would not rebuild these concepts under new names.

The important unresolved work is ensuring that they are discoverable, cohesive, easy to use, and demonstrably effective. The existence of a backend service and tests does not yet establish that the full user journey is seamless or that a learning policy produces better outcomes.

In fact, I would now divide the remaining work into three categories: missing user intentions, missing or incomplete product experiences, and empirical validation of the decision engine.

## 5. What is still missing from the user intentions?

I would explicitly add the following seven requirements. Some already have architectural support, but they deserve to be elevated to first-class user needs.

### A. LearnLoop must help me decide what is worth learning

Your document assumes that the user knows what they want to remember. Sometimes they do. Other times, they encounter a paragraph, paper, or unfamiliar technique and aren't sure whether it deserves further attention.

This decision is important because capturing information should not automatically create a recurring obligation.

The user should be able to encounter an idea and choose a level of engagement.

PROPOSED CAPTURE EXPERIENCE

A selected passage: “GRU update gates determine how much previous hidden state is retained.”

Keep as a reference — no review obligation

Test me later — one delayed retrieval check

Help me remember — maintain the key idea

Learn deeply — explain, vary, and apply it

What LearnLoop would do

Create a deeper learning commitment linked to this idea, with explanation, counterfactual reasoning, practical application, and delayed independent verification.

Illustrative interaction, not a screenshot of the existing application.

The current commitment and depth-policy code provides much of the foundation. I would make this choice exceptionally easy to perform from the Reader, a browser, a PDF, an IDE, or an external LLM conversation.

It should also be reversible. An idea can move from reference-only to deep study, and from deep study back to maintenance.

### B. LearnLoop must support authentic, project-driven learning

This is arguably the most consequential addition.

Consider your gesture-control project. You might need to understand GRUs because a specific model is failing to recognize the timing of a gesture.

A traditional learning app identifies the relevant topic, teaches GRUs, and tests whether you understand them.

An ideal LearnLoop experience begins with the actual problem: why is the model failing?

It helps you reason about competing explanations, identify the relevant concepts, choose a discriminating experiment, understand the result, and revise the model.

The learning is embedded in solving something meaningful.

That means LearnLoop needs a learner-facing Quest or Project context, connected to its existing goal and commitment systems.

EXAMPLE QUEST

## Understand and defend my streaming gesture model

Success means I can explain the architecture, identify its limitations, and make justified modifications without relying on the tutor.

Knowledge

Gating mechanisms, temporal state, gradient behavior

Reasoning

GRU vs. TCN/SSM, latency–accuracy tradeoffs

Authentic task

Diagnose a failure and justify an ablation

Proof of capability

Independent explanation and unseen design scenario

This also suggests a new interaction category: Use this now.

Instead of always scheduling a question for later, LearnLoop should sometimes recommend applying an idea in an active task immediately.

The ultimate aim is for the learner to become less dependent on LearnLoop, not more dependent on it.

### C. LearnLoop must distinguish several levels of knowing

Your document says you want to learn some concepts "in their entirety." I would refine that language.

A concept generally has no single finite endpoint called complete understanding. Understanding a GRU as a software engineer, understanding its optimization dynamics, and proving properties of a recurrent architecture are different targets.

Instead, LearnLoop should offer capability-specific depth targets.

|Capability|What would count as evidence?|
|---|---|
|Recall|Reproduce an important fact or relationship from memory|
|Explain|Explain why something works and how its components interact|
|Reconstruct|Independently derive a solution or procedure|
|Discriminate|Identify when an approach applies, or distinguish confusable ideas|
|Vary|Predict consequences of changing assumptions or parameters|
|Transfer|Solve a fresh problem with meaningful structural differences|
|Perform|Apply the knowledge successfully in a real task|
|Teach or defend|Respond coherently to challenging questions and objections|

These are not necessarily a single linear ladder. A person may be highly capable at implementation but weak at formal explanation, or excellent at proving an identity but unable to recognize when it is useful.

LearnLoop's facet-by-capability evidence model is a good foundation for this.

The missing product requirement is that the learner can specify which capabilities matter for this commitment, and the system can demonstrate what has and has not been verified.

Crucially, a successful teach-back to an AI should not automatically imply that the learner can execute an authentic task.

### D. LearnLoop must have an attention budget, not merely a daily queue

This is where I think your new document identifies a genuine product risk.

Imagine you've saved 300 concepts across mathematics, ML, programming, and technical papers.

Even if every review is useful in isolation, maintaining all 300 may crowd out the learning you want to do tomorrow.

The scheduler therefore needs to consider more than predicted forgetting.

It should account for the importance of the commitment, its relationship to a current project, the type of capability being maintained, the opportunity cost of the next action, and the user's available attention.

In practical terms, the daily experience should answer:

What would be the most valuable use of the next ten minutes?

## Today's Learning Loop

Example

12 minutes available · Gesture model is the active project

Keep fresh — 2 min

Recall one important relationship that hasn't appeared in recent practice.

Repair a weak point — 4 min

Revisit the distinction between temporal context and recurrent state.

Apply it — 6 min

Predict how a proposed architecture change would affect streaming inference.

Other commitments can remain paused or on low-frequency maintenance without turning into an intimidating overdue count.

I would also add a recovery experience for someone who hasn't opened LearnLoop in six weeks.

Instead of presenting hundreds of overdue tasks, it should help them re-establish their priorities, sample the state of important knowledge, and build a realistic new plan.

This is directly informed by recurring Anki complaints about accumulating reviews, including disagreement among experienced users about the best way to resume after a long interruption.

![](https://www.google.com/s2/favicons?domain=https://news.ycombinator.com&sz=32)

Hacker News

+1

### E. LearnLoop must let understanding evolve, not only get stronger

This is a subtle but important gap in many learning applications.

Suppose you initially think:

GRUs are preferable to transformers for streaming gesture recognition because they are more computationally efficient.

Later, after experiments and reading, you realize that this is an oversimplification: the comparison depends on architecture size, hardware, context requirements, and the implementation.

This is not a simple transition from "incorrect" to "correct."

Your mental model has evolved.

LearnLoop should preserve your earlier interpretation, the source or experience that changed it, and the more precise version you now believe. It should also be able to suggest retiring or rewriting practice questions that encode an outdated simplification.

This is where Matuschak's evergreen-note ideas become particularly valuable.

I would distinguish three representations of an idea: what a source claims, what the learner currently believes, and what LearnLoop has observed the learner can demonstrate.

Those three representations are related but should never be silently merged.

This opens the door to multi-source comparison, conflicting evidence, alternative explanations, and a genuinely evolving personal knowledge base.

### F. LearnLoop must be trustworthy when judging errors

Your document places substantial emphasis on catching misconceptions early. I agree, but there's an important distinction between identifying an incorrect response and identifying its cause.

For example, someone may incorrectly predict the output shape of a recurrent layer because of a tensor-layout mistake, a misunderstanding of recurrence, or simply a transcription error.

One wrong answer doesn't necessarily distinguish those explanations.

LearnLoop should maintain competing hypotheses about why the error occurred, select a small number of discriminating follow-ups, and provide targeted repair when the explanation is sufficiently supported.

If the cause remains ambiguous, it should say so.

Equally important, the learner needs to be able to disagree with a grade, inspect the cited source or rubric, and correct the system.

I would make the following principle explicit:

The system must never convert model confidence, exposure, familiarity, or assisted performance into stronger claims of independent capability than the evidence warrants.

Much of the measurement architecture is already designed around this distinction. The remaining challenge is reliability in actual use, especially with open-ended mathematical reasoning and technical explanations.

### G. LearnLoop must support gradual independence from the tutor

Right now, your intentions emphasize receiving explanations, having errors corrected, and being tested.

I would explicitly include the ability to learn how to ask better questions, notice one's own uncertainty, and choose appropriate strategies without the tutor.

For instance, after enough practice, LearnLoop could ask the learner to identify the relevant assumptions before offering an explanation, design their own test of a hypothesis, or identify which additional evidence they would need to make a decision.

The long-term outcome should not merely be increased knowledge. It should also be better self-directed learning.

That includes knowing when not to memorize something, when to consult a reference, and when a quick practical experiment is more valuable than another explanation.

## 6. How I would evolve the actual product experience

I would organize the primary user journey as follows:

Encounter

A paper, question, idea, error, code snippet, or project obstacle

Explore and interpret

Ask questions, make connections, articulate confusion

Choose a commitment

Reference, one-time check, maintenance, or deeper capability

Adaptive learning loop

Diagnose → teach or repair → practice → verify independently

Use, maintain, deepen, or retire

Driven by meaningful goals, evidence, and an attention budget

The important change is that the learner can enter and leave this process at different points. It is not a mandatory sequence of screens.

### A. A deeply interactive Reader

Our previous discussions about branching clarification threads are particularly relevant.

Today, LearnLoop's Reader already has durable Ask exchanges and source-anchored capture. But the current `ReaderAskHistoryExchangeDto` contains no parent-exchange field, so the persisted exchange model is still fundamentally flat.

I would extend it into a branching inquiry workspace, where questions belong to specific source passages and can develop into connected investigations.

For example, while reading a paper, you highlight an equation and ask why its authors chose a particular normalization. The answer might branch into three directions: derivation, alternative formulations, and implications for generalization.

These threads should preserve the original highlighted passage, subsequent source citations, your interpretations, and the open questions that remain.

An especially useful feature would be the ability to convert an inquiry thread into a learning commitment. The system could infer the particular distinction or assumption you struggled with, propose a question, and ask whether it deserves future attention.

The Reader should be where understanding develops, not merely where study material is collected.

### B. A practice family rather than a single repeated problem

I think this deserves to be one of the highest-priority technical investments, building on the existing activity-family substrate.

Suppose you encounter a difficult problem involving a conditional expectation.

Initially, you want to reconstruct its solution from beginning to end. But after doing so successfully twice, recalling that particular solution becomes less informative.

A practice family could progressively test different capabilities:

|Session|Activity|What it tests|
|---|---|---|
|Initial|Reconstruct the original solution without assistance|Procedural recall|
|Next|Solve a related problem with changed parameters|Near transfer|
|Later|Explain why a particular step is valid|Conceptual understanding|
|Later|Identify a tempting but invalid approach|Discrimination|
|Later|Determine what breaks when an assumption changes|Structural understanding|
|Delayed|Solve a novel problem using the same principle|Independent transfer|

These should not simply be paraphrases produced by an LLM.

The family needs a stable semantic contract describing what capability it is testing and controlled variation in difficulty, representation, context, and required reasoning.

This is where the existing separation between activity family, card, surface, and administration is valuable.

It also requires avoiding a statistical mistake: six superficially different problems do not necessarily provide six independent pieces of evidence about the learner.

### C. A Reader-to-project bridge

Your learning often begins with technical papers and ends with code or experiments. LearnLoop should be able to preserve that connection.

Imagine reading a paper about streaming recurrent models. You encounter an interesting method and save it to LearnLoop.

Later, you make a change to your gesture model. LearnLoop could connect the code change or experimental note to the original idea, and invite you to explain what you predicted and what you observed.

Over time, this becomes a particularly meaningful kind of learning history: not just what you read, but how your understanding affected your work.

An early implementation could be as simple as allowing the user to attach a GitHub commit, notebook, calculation, or experiment result to a commitment.

Eventually, a GitHub/IDE integration or an MCP interface could expose the same learning context directly inside the AI assistant where the user works.

However, observed real-world activity needs careful evidence semantics. A commit mentioning GRUs is not proof that the user understands recurrence. A reviewed, independently explained experimental decision is stronger evidence.

### D. An independent-ability view instead of a mastery percentage

I would keep the sophisticated internal learner-state estimator, but change what is emphasized in the UI.

Rather than primarily reporting something like "GRUs: 87% mastered," show what the user has demonstrated.

## GRU architecture · Capability evidence

Recall

Verified

Explain mechanisms

Verified

Reconstruct implementation

Some evidence

Compare alternatives

Some evidence

Unseen transfer

Not yet verified

Illustrative evidence coverage, not measured LearnLoop mastery or actual learner data.

Clicking a capability should explain what evidence supports it, whether that evidence was assisted or independent, and what is still unknown.

I would even provide a button such as Challenge this assessment, allowing the learner to take a fresh, appropriately constructed test.

This helps address the concern in your document about being under an illusion of competence.

## 7. One mathematical design change I would prioritize

Your document says you want to serve as few questions as possible.

That is sensible, but I'd formulate the optimization objective more carefully.

The objective should be to achieve the desired durable capability with minimum expected total learner cost, rather than simply minimize the number of questions.

Information-efficient diagnosis is not the same thing as efficient learning.

A diagnostic probe can be extremely informative about what someone doesn't know without teaching them very much. Conversely, a carefully chosen worked example can substantially improve understanding while revealing relatively little about current competence.

So the controller should choose among different kinds of activities based on their purpose.

One possible formulation is:

\[ a^* = \arg\max_{a\in\mathcal A_{\mathrm{allowed}}} \left[ \mathbb E[\Delta V_{\mathrm{goal}}\mid a] -\lambda\,\mathbb E[T_a] -\mu\,B_a -\nu\,R_a \right] \]

Here:

- \(\Delta V_{\mathrm{goal}}\) is the expected improvement in goal-relevant capability, including the value of information that changes a subsequent decision.
    
- \(T_a\) is expected learner time.
    
- \(B_a\) is burden, including frustration and future maintenance obligations.
    
- \(R_a\) penalizes unnecessary repetition, overly familiar practice, or unreliable evidence.
    

These are conceptual terms, not coefficients I'd assign arbitrarily. Their predictive models and decision effects need calibration against real outcomes.

The allowed actions should include doing nothing, because sometimes the best next action is to let the learner work independently.

This produces an important division of responsibility.

A diagnostic policy should ask: Which uncertainty matters enough to resolve, and which question best distinguishes the relevant hypotheses?

An instructional policy should ask: Which explanation, example, hint, or practice activity is most likely to improve capability?

An assessment policy should ask: What fresh evidence is required before making a claim of independent competence?

A maintenance policy should ask: Does this capability still deserve attention, and can it be refreshed through other activities?

The existing `selection_rewards.py`, misconception machinery, and commitment policies offer a useful starting point. I would prioritize better calibration and policy evaluation rather than immediately replacing them with a more complex learned controller.

### An additional optimization: implicit rehearsal

Math Academy's Fractional Implicit Repetition approach is particularly interesting here: working on an advanced task can rehearse simpler component skills, but not every prerequisite is actually practiced, and partial rehearsal requires appropriately discounted credit.

![](https://www.google.com/s2/favicons?domain=https://mathacademy.com&sz=32)

mathacademy.com

LearnLoop could make better scheduling decisions if it records which capabilities were genuinely exercised by a task.

For example, solving a novel probability problem may refresh the learner's use of conditional probability. That might reduce the need for another elementary review question.

But exercising something incidentally should not automatically count as independently verifying every related facet.

This distinction between refreshing readiness and certifying capability is essential if you want to reduce question volume without inflating mastery estimates.

## 8. What I would build next, in priority order

Given what is already in the repository, I would favor improvements that complete vertical user journeys before expanding the research machinery.

|Priority|Work|Implementation direction|
|---|---|---|
|P0|Capture-to-commit golden path|Make source selection → intent choice → visible commitment → first useful activity nearly effortless|
|P0|Humane daily attention policy|Enforce meaningful budgets, maintenance modes, pause/retire, and graceful re-entry|
|P1|Robust dynamic practice families|Use existing activity substrate to generate fresh, semantically controlled tests and transfer problems|
|P1|Evidence transparency and grade correction|Present the capability ledger clearly, with support for disputing AI judgments|
|P2|Branching Reader inquiry|Add parent/child exchanges, thread relationships, and promotion of unresolved questions|
|P2|Authentic project integration|Link commitments to real code, notebooks, experiments, and independent performance|
|P3|Cross-application access|Browser capture, IDE integration, and an MCP interface exposing learning context and approved actions|

I would not make all of these prerequisites for the next release.

The most valuable next test would be whether an unfamiliar user can complete an entire meaningful journey without understanding LearnLoop's internal terminology.

For example:

I found a difficult explanation in an arXiv paper. I want to understand it, remember the important part, and be able to use it in my own project.

That user should not have to understand subjects, source sets, Learning Objects, facet contracts, blueprints, evidence masses, or scheduling intents.

All of those can remain inspectable for sophisticated users. They simply shouldn't be administrative work imposed on someone who wants to learn.

### How to test whether these improvements work

I would use a small set of technically demanding use cases first: learning from a paper, reconstructing a mathematical solution, and understanding or modifying a code architecture.

The success metrics should include capture-to-first-useful-action friction, commitment survival and retirement, review burden, recovery after an interruption, error-diagnosis accuracy, and delayed performance on fresh tasks.

Most importantly, assess unassisted transfer per learner-minute, with separate checks for false confidence and unreliable AI grading.

An internal simulator is useful for testing whether policies behave as intended. But it cannot prove that a policy teaches real people more effectively. That requires longitudinal testing with learners and, eventually, controlled comparisons between alternative interventions.

This is consistent with the evidence and policy-evaluation discipline already developed in the v-next specification.

## 9. My proposed revised user-intentions document

I would keep your original voice and motivating examples, but make the commitments, source interactions, authentic use, attention budget, and honest evidence requirements more explicit.

# LearnLoop — User Intentions (Proposed v2)

## North star

The intention of LearnLoop is to make durable knowledge and skill something a person can deliberately develop, maintain, and use.

When I encounter an idea, concept, problem, or skill that matters to me, I want to be able to choose to understand it, remember it, or become proficient in applying it. LearnLoop should make achieving that intention as effective and frictionless as possible, without replacing the intellectual work necessary for genuine understanding.

**The goal is not to complete study activities. The goal is to develop lasting, independently usable capabilities.**

## 1. Encountering and capturing knowledge

I want to be able to capture anything I encounter in the course of reading, research, work, or personal projects.

This might be a mathematical problem, a section of an arXiv paper, a piece of code, an architectural decision, or an idea that changes how I understand something.

Capture should preserve the original context, my questions, my interpretation, and why the material matters to me.

I should not have to interrupt my activity to configure a learning curriculum.

Saving something should not automatically require me to review it forever.

## 2. Choosing what and how deeply to learn

I want to decide what deserves my attention.

For each idea or capability, I should be able to choose whether I want to:

- Preserve it as a reference.
    
- Perform a one-time memory or understanding check.
    
- Remember its most important ideas.
    
- Develop fluency and retain that knowledge.
    
- Reach deeper proficiency involving reconstruction, counterfactuals, transfer, or authentic application.
    

These intentions should remain adjustable as my interests and projects change.

LearnLoop should help identify valuable learning opportunities, but it should not silently expand the scope of my commitments.

## 3. Developing genuine understanding

I want to be able to understand why an idea works, not merely memorize its description.

For a mathematical problem, I want to reconstruct the solution, justify its steps, recognize when the method applies, and solve unfamiliar variants.

For a technical paper, I want to understand its methods, equations, assumptions, limitations, novelty, and implications.

For my projects, I want to explain and defend architectural decisions, understand tradeoffs, diagnose errors, and predict the consequences of changing an implementation.

LearnLoop should adapt to my demonstrated abilities and use the appropriate combination of explanation, worked examples, guided practice, retrieval, problem-solving, and independent assessment.

## 4. Reading and inquiry

I want to read canonical sources and engage in a continuing dialogue with their ideas.

I should be able to ask questions about highlighted passages, equations, diagrams, and claims without losing my place.

These questions should be connected to their sources and to one another, including connections to material elsewhere in my knowledge base.

LearnLoop should help me identify the important knowledge in a source, including what the author considers important, what I personally find difficult, and which ideas are prerequisites for other goals.

I should be able to turn selected insights or unresolved questions into future practice commitments without automatically turning every passage into a flashcard.

## 5. Retaining and extending knowledge

Once I understand something, I want to preserve that ability for as long as it remains valuable.

Learning activities should evolve as my understanding develops. They should test the underlying concept through different representations, assumptions, contexts, and problem variants rather than repeatedly relying on a familiar question.

I want to be able to choose between maintaining a capability and continuing to deepen it.

LearnLoop should recognize when one activity meaningfully rehearses several capabilities and avoid redundant questioning.

## 6. Applying knowledge in meaningful work

I want learning to improve my ability to complete real tasks and pursue projects that matter to me.

LearnLoop should help me connect what I read and practice to what I build, solve, explain, research, and create.

Evidence from actual work should contribute to my learning history when it genuinely demonstrates relevant capability.

I want the system to help me become increasingly independent of tutoring assistance.

## 7. Detecting errors and correcting misconceptions

I want LearnLoop to notice when I have misunderstood something, am missing an essential prerequisite, or can only reproduce an answer through shallow familiarity.

It should distinguish different possible causes of errors before choosing a repair.

The system should prefer the smallest effective intervention, while recognizing that meaningful practice sometimes requires sustained effort.

I should be able to challenge feedback, inspect supporting sources, and understand why LearnLoop believes something about my capabilities.

## 8. Maintaining an honest picture of ability

I want to know what I have genuinely demonstrated, what I can only accomplish with assistance, and what remains uncertain.

LearnLoop should distinguish recall, understanding, execution, generalization, and calibration, rather than reducing every capability to an unqualified mastery percentage.

The system should use appropriately delayed and unfamiliar tasks to verify durable knowledge and transfer.

Its claims should reflect the strength and limitations of the available evidence.

## 9. Managing my limited attention

I want LearnLoop to decide what learning activities are most valuable given my current goals, time, energy, and retention needs.

The daily queue should respect a manageable attention budget.

I should be able to pause projects, reduce maintenance, retire material, and return after an extended absence without accumulating a punitive backlog.

My learning history should remain useful even when my priorities change.

## 10. Letting my knowledge evolve

I want my understanding of ideas to change over time as I encounter new evidence and perspectives.

LearnLoop should preserve the development of my interpretations, connect related ideas across sources, and help identify contradictions or outdated assumptions.

Practice questions should evolve with my understanding and should be revisable or removable without destroying the underlying learning history.

## Overall success criterion

**LearnLoop succeeds when I can encounter something meaningful, decide how well I want to know it, and reliably develop or preserve the relevant capability with as little unnecessary effort as possible.**

Its purpose is to automate the logistics of learning while preserving the reasoning, interpretation, practice, and discovery that make knowledge genuinely mine.

## 10. Final assessment

I think LearnLoop can meet these intentions without a fundamental rewrite.

In fact, much of the architecture needed to support them is already taking shape. The commitment model, activity substrate, evidence ledger, Reader capture, and staged learning arcs are more sophisticated than what the new document alone might suggest.

The greatest remaining risk is not insufficient algorithmic sophistication. It is that LearnLoop becomes an extraordinarily sophisticated decision engine attached to a workflow that still feels like managing study materials.

The opportunity is to make the system feel like an intellectual companion to the work someone is already doing: it notices what they care about, helps them make sense of it, remembers where they struggled, brings back important ideas when useful, challenges their assumptions, and ultimately helps them become more capable without it.

If I had to choose one product direction to anchor the next iteration, it would be project-driven, source-grounded learning with user-controlled durable commitments and evidence-based adaptive practice.

That is both a coherent first product for technical learners and a strong foundation for the broader system you're envisioning.