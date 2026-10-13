
My original query: "For the learnloop reader, could you help me brainstorm some better features and better design? Recall Scott Jensen's talk to Ubuntu about desktop UX [https://www.youtube.com/watch?v=1fZTOjd_bOQ](https://www.youtube.com/watch?v=1fZTOjd_bOQ) [https://news.ycombinator.com/item?id=46256834](https://news.ycombinator.com/item?id=46256834)  or Andy Matuchak's demonstration of How Might we Learn [https://andymatuschak.org/hmwl/](https://andymatuschak.org/hmwl/) and OS-level spaced repetition [https://notes.andymatuschak.org/zNLoqjEVe5dheMKmTTyB9E3](https://notes.andymatuschak.org/zNLoqjEVe5dheMKmTTyB9E3) . Is there any insight from these excellent talks we could glean to help inform a better Reader design and a better Learnloop UX in total? What would a user want or need from a Reader and how does learning from a textbook work, what are traditional learning from a textbook or doing practice problems from a textbook have as usual pain points? And how could we work to help alleviate them? Are there things we can borrow and use from advancements in embeddings, RAGs, rerank models, etc."

Agent reply: "I think these two talks point toward a much more interesting direction for LearnLoop than simply improving the Reader's interface. They suggest an opportunity to fundamentally redesign the experience of learning from books, papers, exercises, and eventually anything on your computer.

My central thesis would be:

LearnLoop should not primarily be an AI-powered textbook reader. It should be an adaptive learning environment that uses textbooks as one of several ways to help someone develop durable, usable knowledge.

The distinction matters enormously.

Consider the difference between two products:

- An AI Reader: You open a textbook, highlight unfamiliar material, ask questions, receive explanations, and generate flashcards.
    
- A learning environment: You tell the system what you're trying to accomplish. It helps you navigate the textbook, recognizes when a prerequisite is getting in your way, supports you while you solve problems, learns from the mistakes you make, and brings back important concepts when you're likely to need reinforcement.
    

The second system doesn't just make reading more convenient. It changes the relationship between reading, understanding, practicing, remembering, and applying knowledge.

I see three particularly powerful influences here.

Scott Jenson — Design the experience, not just the interface

His [Ubuntu Summit talk](https://www.youtube.com/watch?v=1fZTOjd_bOQ) challenges the assumption that improving desktop software means rearranging familiar interface elements. Instead, reconsider the underlying activities, interactions, and feedback loops.

![](https://www.google.com/s2/favicons?domain=https://discourse.ubuntu.com&sz=32)

Ubuntu Discourse

+1

Andy Matuschak — Make learning continuous with meaningful work

His [How Might We Learn?](https://andymatuschak.org/hmwl/) demo imagines an environment where meaningful projects drive learning, canonical texts provide depth, and guidance and memory support appear in context instead of forcing users into a separate tutoring workflow.

![](https://www.google.com/s2/favicons?domain=https://andymatuschak.org&sz=32)

andymatuschak.org

+1

Matuschak's OS-level memory proposal — Learning shouldn't be trapped inside an application

His [OS-level spaced repetition note](https://notes.andymatuschak.org/zNLoqjEVe5dheMKmTTyB9E3) proposes memory as a shared service accessible from documents, browsers, notes, and other applications. For LearnLoop, that suggests an underlying learning engine which the Reader happens to use, rather than a Reader that owns all learning activity.

![](https://www.google.com/s2/favicons?domain=https://notes.andymatuschak.org&sz=32)

notes.andymatuschak.org

## 1. Start with what somebody actually wants from a textbook

The user's goal is almost never to read a textbook. It's to accomplish something for which the book is a resource.

For example, imagine someone studying probability using a textbook.

Their immediate intention might be to understand why a mixture PDF works, derive the CDF of an unfamiliar distribution, or become capable of solving examination problems independently.

An ordinary PDF reader treats these as basically the same activity: display pages, provide highlights, bookmarks, and search.

But these are different cognitive tasks, requiring different kinds of help.

I would organize LearnLoop around five underlying intentions:

|User intention|What they actually need|
|---|---|
|Orient|Figure out what matters, where to start, and what prior knowledge is necessary|
|Understand|Build intuition, resolve confusion, and connect new ideas to existing knowledge|
|Apply|Solve problems, perform procedures, construct proofs, and make decisions|
|Consolidate|Retain important knowledge, develop fluency, and discover remaining gaps|
|Transfer|Recognize when and how to use that knowledge in unfamiliar situations|

These intentions should govern the experience much more than whether the user is currently looking at a PDF, writing a note, or answering a question.

The most useful design question is therefore:

What is preventing this person from accomplishing their immediate learning goal, and what is the smallest intervention that would help them move forward?

That framing also fits LearnLoop's existing work on learner-state inference, misconception detection, information-efficient probes, and minimal causal repair.

## 2. Where traditional textbook learning fails

Textbooks are unusually demanding interfaces because they assume the learner can coordinate several difficult processes independently: identifying what's important, understanding explanations, monitoring confusion, practicing skills, and deciding when to revisit knowledge.

Matuschak's [Why books don't work](https://andymatuschak.org/books/) argues that textbooks are better than ordinary nonfiction at incorporating exercises and instructional structure, yet still leave much of the cognitive work of learning unsupported.

This is consistent with learning research: practice testing and distributed practice have stronger general support than rereading or highlighting alone.

![](https://www.google.com/s2/favicons?domain=https://andymatuschak.org&sz=32)

Andy Matuschak

+1

|Typical pain point|What happens to the learner|Potential LearnLoop response|
|---|---|---|
|Not knowing what matters|Every page seems equally important; students reread entire chapters|Goal-aware reading paths, explicit learning objectives, and selected exercises|
|Missing prerequisites|An unfamiliar term or mathematical step makes the entire paragraph incomprehensible|A targeted prerequisite detour that returns to the original location|
|The illusion of understanding|A worked solution makes sense until the learner must reproduce it independently|Brief predict-the-next-step tasks, delayed reconstruction, and fresh variants|
|Not knowing why a solution works|Students imitate a procedure without knowing when it applies|Ask learners to justify steps, identify assumptions, and compare alternative methods|
|Getting stuck without useful feedback|Answer keys provide final answers but little explanation of where reasoning diverged|Compare the learner's own steps and diagnose the earliest meaningful error|
|Too much context switching|Students alternate between PDFs, search engines, calculators, notebooks, AI chat, and practice websites|Contextual tools and a persistent problem-solving workspace|
|Forgetting after reading|Material feels familiar immediately but disappears weeks later|Selective delayed retrieval and practice integrated into the learner's goals|
|Poor transfer|Students recognize an exercise type but cannot solve unfamiliar versions|Interleaved problems, altered assumptions, and authentic applications|
|Losing one's train of thought|Looking up one prerequisite leads through several articles and the original question is forgotten|Branching inquiry threads with a reversible path back|
|Losing motivation|Study becomes an endless accumulation of pages, cards, and overdue reviews|Visible capability gains, user-controlled commitments, and a limited attention budget|

There's also a crucial distinction between helping someone complete a problem and helping them learn how to solve it.

A 2025 randomized study of nearly 1,000 high-school mathematics students found that access to a conventional AI assistant improved practice performance, but those students subsequently performed worse on unassisted exams than students without AI access. A tutor with learning-oriented safeguards largely mitigated that harm, although it did not demonstrate an independent exam advantage.

![](https://www.google.com/s2/favicons?domain=https://doi.org&sz=32)

PNAS

This is a strong argument for making the amount of help a deliberate part of LearnLoop's instructional policy, rather than always providing the best possible explanation or complete solution.

It also means the Reader should not interpret a student accepting an explanation, recognizing a derivation, or highlighting a passage as proof of mastery.

## 3. What LearnLoop already has—and what is actually missing

I checked the current [ReaderScreen.tsx](https://github.com/6up-b/learnanything/blob/main/apps/learnloop-tauri/src/screens/ReaderScreen.tsx) and the [Reader integration specification](https://github.com/6up-b/learnanything/blob/main/docs/specs/spec_p3_reader_integration.md).

The implementation is already more developed than a simple Reader-plus-chat design. In particular, it includes reading modes, a personalized reading guide, source-anchored annotation, multiple Ask response modes, optional quick checks, exercise importing, learner-authored practice, source search, video/transcript support, and the beginnings of durable learning arcs.

Those are meaningful foundations. I would not rebuild them or introduce competing versions of the same functionality.

The opportunities I would concentrate on are the connections between these features:

Inquiry should branch and reconnect. The Ask panel currently persists exchanges, but still organizes the conversation primarily as a flat history instead of a structured investigation.

Exercises should become workspaces. Importing an exercise is useful, but the richer opportunity is supporting every stage of solving it without immediately revealing the answer.

Sources should connect through concepts. A learner should be able to compare how multiple books explain the same idea, while preserving the distinct claims of each source.

The experience should adapt to the current activity. Reading, investigating an idea, solving a problem, and reviewing knowledge should feel like related stages of one workflow rather than separate interfaces.

That last point is where I think Jenson's UX argument has the greatest relevance.

## 4. Apply Jenson's idea of learning loops to LearnLoop itself

One of Jenson's most useful examples is surprisingly mundane: moving files between windows.

What matters is not merely that dragging works. It's that a sequence of actions becomes easy, predictable, and progressively discoverable. His talk also discusses integrating file management, text clippings, and window management into more coherent interactions.

![](https://www.google.com/s2/favicons?domain=https://thenewstack.io&sz=32)

The New Stack

I would apply that thinking by examining the loops a learner repeatedly performs.

|Learning loop|What the experience should feel like|
|---|---|
|Encounter → Question → Resolution → Resume|I can investigate something without losing my original task|
|Read → Predict → Check → Understand|I can test my interpretation without constructing a study session|
|Attempt → Error → Diagnosis → Repair → Retry|I can recover from a mistake without being given an entire solution|
|Discover → Save → Revisit → Apply|Important knowledge naturally reappears when useful|
|Project → Knowledge gap → Study → Project|Learning enables progress on something I actually care about|

Notice that none of these starts with opening a particular application or navigating to a tab.

This has implications for the existing Reader UI.

I'd strongly favor progressive disclosure over adding more panels. Right now the Reader has substantial functionality in its capture palette and its Guide, Ask, and Notes rail. That's useful for power users, but an ordinary reader may not know which operation they need.

The first interaction should be extremely simple: select something and express what you're trying to do. More specialized actions can appear as the interaction develops.

The Hacker News discussion is particularly interesting here. Several commenters object to unpredictable text selection, disruptive interface changes, and the lack of configuration for experienced users. Those comments are anecdotes, not representative user research, but they identify a real design tension: simplicity shouldn't come at the expense of capability and control.

![](https://www.google.com/s2/favicons?domain=https://news.ycombinator.com&sz=32)

Hacker News

For LearnLoop, I'd preserve standard text selection, excellent keyboard controls, the ability to disable interventions, and a consistent interaction model across books, PDFs, videos, and notes.

## 5. The Reader features I'd pursue

## A. Branching inquiries instead of linear chat

High priority

The current Ask history is useful, but an investigation is rarely linear. One question about covariance might lead to an inquiry about inner products, then Hilbert spaces, then conditional expectation.

Each branch should retain its parent question, exact source anchor, supporting citations, and unresolved status. A small breadcrumb trail would let the reader return to the original question instantly.

The important innovation is that branches should eventually reconnect. When a prerequisite is resolved, LearnLoop can ask whether the original passage now makes sense and offer a minimal confirmation check.

## B. A genuine exercise workbench

High priority

Importing textbook exercises is already supported. I'd turn an imported exercise into an active workspace with a scratchpad, mathematical notation, step comparison, hint controls, and a link to the original problem.

Rather than immediately grading an answer, LearnLoop could distinguish a transcription error, missing prerequisite, invalid algebraic manipulation, wrong method choice, or conceptual misunderstanding.

Importantly, the system should preserve what the learner attempted before each hint was provided. That information is useful both for diagnosis and for tracking assistance.

## C. Interactive, explorable explanations

High potential

A textbook equation or figure should sometimes become an interactive object, not simply a passage that can be explained verbally.

Imagine exploring a two-sided exponential distribution by changing \(p\) and \(\lambda\), watching its PDF and CDF change, and predicting which area represents a given probability.

This is closely related to Matuschak's synthesized dynamic media and [Bret Victor's explorable explanations](https://worrydream.com/ExplorableExplanations/). Such demonstrations should be optional, visibly AI-generated, and grounded in the original definitions—not passed off as the author's original content.

### D. Goal-aware reading paths

The existing reading guide could become substantially more valuable by connecting its recommendations to a specific capability the learner wants to acquire.

For example, instead of presenting a textbook's full chapter sequence, the Reader might show:

Learning goal

Proposed experience

Become capable of independently deriving continuous mixture distributions.

Choose how deeply you want to explore the material.

Build intuition — definitions, examples, visualizations

Learn to derive — explanations, worked examples, practice

Develop fluency — novel problems, changed assumptions, delayed checks

Suggested next activity

Read the mixture distribution section, then derive the CDF without looking at the answer.

This is an illustrative interaction, not an existing live feature.

The path should explain why material is included, what can be skipped based on existing evidence, and whether it is a prerequisite or enrichment. It should also let the learner override the recommendation.

This mirrors one of my favorite moments in How Might We Learn?: instead of requiring someone to read a thousand-page textbook, Matuschak's demo proposes routes of different depths through the canonical text.

![](https://www.google.com/s2/favicons?domain=https://andymatuschak.org&sz=32)

andymatuschak.org

### E. Cross-source, or syntopic, reading

I think this is one of the strongest longer-term opportunities.

A learner should be able to select a mathematical claim and ask how it relates to explanations elsewhere in their library.

For instance, while studying covariance, LearnLoop could find the corresponding discussion in a probability textbook, a linear algebra resource, and a functional analysis text.

Rather than returning three generic summaries, it could identify what each source contributes:

|Source perspective|Distinct contribution|
|---|---|
|Introductory probability|Covariance as a measure of joint variation|
|Linear algebra|Covariance matrices, quadratic forms, eigendirections|
|Hilbert-space formulation|Centered random variables as vectors and covariance as an inner product|
|Machine learning|Feature decorrelation, PCA, whitening, uncertainty|

The reader can then follow a conceptual connection without losing the source from which it originated.

The important design rule is to preserve differences. What the source claims, what LearnLoop infers, and what the learner believes should remain separate. Otherwise cross-document RAG risks producing an attractive but misleading consensus.

### F. Treat questions, confusion, and insights as durable objects

The Reader currently has annotation and capture infrastructure. I would build on it so that a question can remain an active object across sessions.

For example, a learner might ask why covariance matrices are positive semidefinite. An AI response might be sufficient, but it might also reveal a deeper unresolved issue about quadratic forms.

The interaction shouldn't necessarily end when the chat answer appears.

A question could be marked resolved, unresolved, worth revisiting once, or worth developing into a capability. LearnLoop's existing commitment and disposition machinery is well suited to these distinctions.

I would also add a session-ending synthesis that is optional and takes less than a minute: what was resolved, what remains open, and what deserves later reinforcement. That synthesis should reflect actual activity rather than generating a generic chapter summary.

### G. Personalized misconception-aware reading

This could be particularly distinctive because LearnLoop already has a fairly ambitious latent learner-state model.

Imagine the system knows a learner has previously struggled with confusing probability density with probability mass.

Later, they encounter a new continuous distribution. LearnLoop could subtly highlight a short passage clarifying that distinction, or suggest a small check if the uncertainty matters to their current goal.

But it shouldn't assume that the learner is still confused, and it shouldn't interrupt every time the concept appears.

A reasonable intervention policy might depend on expected learning benefit, information gain, learner effort, interruption cost, and the active goal:

\[ a^*=\arg\max_{a\in\mathcal A} \left[ \mathbb E[\Delta U_{\text{learning}}\mid a] +\beta I(\theta;Y\mid a) -\lambda C(a) \right] \]

Here, \(a\) could be a diagnostic probe, explanation, prerequisite detour, practice exercise, or no intervention. \(\theta\) is the learner's latent state and \(Y\) a possible observation.

This is an illustrative objective, not a validated LearnLoop policy.

The critical point is that no intervention should be a legitimate, sometimes optimal action. An adaptive reader that constantly interrupts can make reading worse, even if each suggestion is individually relevant.

## 6. The Reader should evolve toward a learning workbench

I wouldn't abandon the familiar document layout. Reading should still feel like reading.

Instead, I would let the workspace adapt when the learner transitions from reading into investigation or problem-solving.

LEARNLOOP READER · CONCEPTUAL LAYOUT

Probability · Continuous random variables

Working

Source

Chapter 4 · Mixture distributions

Suppose X equals Y with probability p and Z otherwise. Derive the density of X.

Original page · examples · provenance

Your work

Derive the CDF first

\[ F_X(x)=? \]

Your reasoning and intermediate steps appear here.

Compare step · request hint · check assumption

Current inquiry: Mixture CDF → Conditioning on component → Integration bounds

The workspace can collapse back into normal reading when the learner is finished. The original source stays visible, and the learner controls when a hint or worked solution is revealed.

This is also where expert and novice experiences should differ. A 2025 meta-analysis of instructional assistance found a robust expertise-reversal effect: lower-prior-knowledge learners generally benefited from more guidance, whereas higher-prior-knowledge learners tended to benefit from less.

![](https://www.google.com/s2/favicons?domain=https://doi.org&sz=32)

ScienceDirect

So the ideal design isn't universally Socratic or universally explanatory. It adapts how much assistance is available and defaults to respecting the learner's chosen level of autonomy.

## 7. What embeddings and RAG can actually contribute

I would resist framing this as simply finding a better embedding model.

The biggest opportunity is retrieving the right kind of context for the current learning operation.

A learner asking for an explanation needs different evidence than someone asking for an equivalent worked example, a prerequisite, a counterargument, or a problem that discriminates between two possible misconceptions.

### A hybrid, source-aware retrieval architecture

Reader interaction

Selection + source location + question + active goal + authorized learner context

Exact context

Source spans, equations, nearby blocks

Hybrid retrieval

BM25 + text embeddings + visual retrieval

Learning context

Goals, prerequisites, prior errors, evidence

Rerank and construct evidence

Verified source locations, provenance, ambiguity, relevance to question intent

Instructional decision and response

Explain · show example · probe · scaffold · defer · abstain

The stages are important for different reasons.

Exact source context comes first. When a learner selects an equation, the system should know its exact position and surrounding derivation. Embedding search should supplement this, not replace it. Your existing Marker-based extraction and source anchors are a good starting point.

Hybrid retrieval supports different query types. Lexical search is valuable for equation identifiers, variable names, theorem references, and exact terminology. Dense embeddings help with conceptual paraphrases and related explanations elsewhere in the vault.

Reranking selects evidence for a particular question. A passage highly relevant to defining covariance isn't necessarily the best passage for explaining how covariance relates to the geometry of \(L^2\).

Visual retrieval matters because textbooks are not plain text. Equations, multi-panel figures, diagrams, tables, and spatial relationships can carry essential meaning that text extraction alone may lose.

### Models worth investigating

|Component|Candidate|Why I would test it|
|---|---|---|
|Text embeddings|[Qwen3-Embedding-0.6B](https://qwenlm.github.io/blog/qwen3-embedding/)|A reasonable local starting point for semantic retrieval over extracted text, notes, and concept descriptions|
|Text reranking|[Qwen3-Reranker-0.6B/4B](https://qwenlm.github.io/blog/qwen3-embedding/)|Improve relevance among candidates, especially across multiple sources|
|Visual document retrieval|[ColQwen2.5](https://huggingface.co/vidore/colqwen2.5-v0.2)|Directly retrieve relevant page images, including visually complex content|
|Multimodal retrieval/reranking|[Qwen3-VL-Embedding / Reranker](https://github.com/QwenLM/Qwen3-VL-Embedding)|Jointly handle text, figures, screenshots, and page images|
|Structured extraction|[Marker](https://github.com/datalab-to/marker) plus visual fallback|Preserve sections, equations, bounding boxes, tables, and source references|

Qwen's text embedding and reranking series includes 0.6B, 4B, and 8B variants. Its later multimodal retrieval models provide another option for image-rich textbook passages. ColPali-style retrieval is also interesting because its multi-vector representations preserve more page-level visual information than a single embedding.

![](https://www.google.com/s2/favicons?domain=https://qwenlm.github.io&sz=32)

Qwen

+2

I would benchmark these against your own corpus of technical textbooks rather than assume that the highest-scoring general model will work best for mathematical derivations.

### The valuable thing to index isn't just text

I would preserve relationships between source material and learning objects.

|Object|Example|
|---|---|
|Source span|A paragraph explaining conditional expectation|
|Author claim|Independence implies a certain factorization|
|Concept/facet|Independence, conditioning, joint distributions|
|Exercise|A proof or calculation requiring that relationship|
|Learner question|Why does the integral use these bounds?|
|Learning hypothesis|The learner may misunderstand support restrictions|
|Evidence|A later independent solution, with assistance history|

These should not be collapsed into one vector index.

A source index answers where relevant information can be found. The learner-state model answers what is known or uncertain about the learner. The learning policy decides what to do next.

Embeddings can connect the layers, but similarity alone does not establish conceptual prerequisites, misconception causality, or mastery.

This distinction becomes even more important when generating questions. A retrieval system should be able to say that it lacks adequate evidence instead of inventing an apparently authoritative derivation. Research on RAG grounding continues to find substantial limitations in attribution and source-supported generation.

![](https://www.google.com/s2/favicons?domain=https://aclanthology.org&sz=32)

ACL Anthology

For mathematical material, I would also test independent symbolic and numerical checks where applicable, rather than relying exclusively on another LLM to judge the solution.

## 8. Imagine an actual reading session

Suppose someone opens a probability textbook because they want to solve problems involving mixture distributions.

At the start, LearnLoop knows their active goal is independent problem-solving, not just familiarity with the chapter. The guide identifies a relevant section and one representative exercise.

They begin reading and encounter the expression:

\[ f_X(x)=pf_Y(x)+(1-p)f_Z(x). \]

They understand the formula but are uncertain why the law of total probability produces it.

They select the passage and ask that question. LearnLoop retrieves the surrounding derivation and asks whether they'd prefer an explanation or a short derivation to try themselves.

They attempt the derivation using the CDF. Their response reveals that they understand conditioning but are unsure why the resulting densities are weighted.

Instead of restarting the entire explanation, LearnLoop addresses that specific gap.

Later, the learner makes an error integrating a piecewise density. The workbench records the intermediate steps and identifies two plausible explanations: misunderstanding the support of the distribution or making an integration mistake.

A discriminating question can distinguish those possibilities before selecting a repair. Once the issue is resolved, the learner returns to the original exercise.

When the session ends, LearnLoop has a much richer record than pages read or questions asked. It knows which concepts were discussed, what the learner attempted, what assistance they received, and which understanding claims still need independent verification.

Several days later, LearnLoop can offer a short, unfamiliar mixture problem, without access to the prior explanation. That is a more meaningful retention and transfer check than simply asking the learner to recognize the original formula.

This is the experience I'd want LearnLoop to optimize: a continuous path from confusion to independent competence, with minimal unnecessary detours.

## 9. What I'd prioritize next

I'd sequence the development around completing workflows rather than maximizing the number of available actions.

|Priority|Investment|Rationale|
|---|---|---|
|P0|Reader usability testing and friction audit|Observe actual textbook readers before adding more interface complexity|
|P1|Branching Ask history, parent-child links, reliable return-to-source navigation|Builds directly on the existing dialogue system and eliminates a common context-loss problem|
|P1|Exercise workbench with step capture, hint ladder, and assistance-aware evidence|A direct improvement to real learning and a potential core differentiator|
|P2|Goal-conditioned reading paths and cross-source concept retrieval|Makes existing guides and source indexing substantially more purposeful|
|P2|Source-grounded interactive explanations for selected concept types|Adds new ways to build intuition where static explanations are insufficient|
|P3|OS-level learning service through MCP and other integrations|Lets learning support accompany the person beyond the Reader|

I would also evaluate each phase against learning outcomes, not engagement alone.

An excellent Reader might actually produce fewer interactions, shorter sessions, and fewer generated questions because the learner gets unstuck more efficiently.

The primary measures I'd track are delayed unassisted problem-solving, transfer to novel problems, calibration of self-assessed understanding, learner time, hint dependence, and interruption burden.

A useful first experiment would compare a standard PDF-plus-chat workflow with a source-grounded, step-aware LearnLoop experience, followed by an independent assessment after a delay. That would begin to tell us whether the redesigned interaction genuinely improves learning rather than simply feeling better.

## 10. The larger LearnLoop direction: memory as infrastructure

Matuschak's OS-level spaced repetition proposal is particularly compelling because it questions why memory support should be contained inside a dedicated application.

I think LearnLoop can extend that idea further.

Imagine a shared learning service that receives explicit learning intentions and context from different applications.

Someone is reading a paper in a browser. They identify something important and send it to LearnLoop. Later, while coding, they encounter the same idea in a different context. LearnLoop can retrieve the earlier explanation or offer a quick challenge. When they open the Reader again, the original question, sources, and relevant history are waiting.

Through an MCP interface, an editor integration, or a small desktop capture tool, this could happen without requiring a particular AI provider or document application.

Crucially, the learner would control what context is shared and which activities create lasting study commitments. Passive exposure would not be silently promoted into mastery evidence.

Matuschak's most important caution is relevant here: learning technology should support a person's own purposes, not impose a universal definition of what they should know.

![](https://www.google.com/s2/favicons?domain=https://andymatuschak.org&sz=32)

andymatuschak.org

The larger product could therefore have three layers: a source layer for canonical references, a learner layer for goals and uncertain knowledge state, and an activity layer for practice, explanation, and independent verification. The Reader becomes one interface to that shared infrastructure.

The feature I'd be most excited to prototype first is the Reader + branching inquiry + exercise workbench combination.

It builds on work you've already done, provides an immediately understandable benefit, and creates better evidence for LearnLoop's adaptive engine. More importantly, it connects reading to reasoning instead of turning the Reader into another interface for managing AI-generated content.

The key product question I'd keep coming back to is:

Does this interaction help the learner return to the thing they wanted to accomplish, more capable than when they encountered the obstacle?

That is the standard I'd use to decide which Reader features are genuinely worth building."

My response: "Maybe we could have a selection over a figure or word section then have an llm generate an interactive figure like in your example Bret Victor's explorable explanations. I definitely would like syntopic reading. I also really like the persoanlized misconception aware reading. We could highlight a short passage clarifying the distinction or just indicate that this given passage/information is related to something that the user has gotten wrong a few times before or struggles with. When having a workspace for having problem solving within the reader, how much scaffolding is provided for worked solutions should definitely scale from prior knowledge and adapt over time to how much the student struggles. I feel like a lot of times when I was doing a textbook problem or homework problem I would get stuck and spend a lot of time trying to figure out what i did wrong, and when I would be given a hint I wouldn't be able to reconcile with the work I have already did so far. 

We can also have the user query the reader with a natural language style question, then have the reader display related sources that can help clarify with an optional tutor available to clarify or answer additional questions. 

After the reader session, Learnloop should retain the information elicited by the user and update its model of the learner. As you said, "When the session ends, LearnLoop has a much richer record than pages read or questions asked. It knows which concepts were discussed, what the learner attempted, what assistance they received, and which understanding claims still need independent verification."  On how this would actually work, my preliminary thoughts would be to create natural language summaries and use it to propagate updates and somehow tie to the action router. Then a short unfamilliar problem for cold retrieval of the textbook chapter via a problem without access to the prior explanation."


Agent: "I think these ideas fit together into something considerably more powerful than an adaptive PDF reader. In particular, your observation about receiving hints that you can't reconcile with your existing work is important. That's a problem even many AI tutors haven't really solved: they can generate an excellent explanation without understanding the learner's actual reasoning trajectory.

I'd organize your ideas around a new principle:

LearnLoop should preserve the learner's evolving reasoning, not merely remember what they asked and whether their final answer was correct.

That gives us an architecture in which the Reader, problem workspace, learner-state estimator, and action router reinforce each other.

## 1. The central architecture: from reading to durable learning evidence

Your natural-language summary idea is useful, but I'd make one important modification: the LLM-produced summary should not directly update the learner's mastery estimates.

Instead, it should be a human-readable projection of a more structured record of what happened.

Reader and problem-solving interactions

Selections · questions · derivations · mistakes · hints · interactive explorations

Semantic observation compiler

LLM interprets reasoning, identifies relevant facets, proposes misconceptions, links evidence to source spans

Evidence and learner state

Typed observations, assistance, uncertainty, misconceptions, capability estimates

Narrative learning memory

What the learner tried, where they struggled, what explanations helped, unresolved questions

Action router and instructional policy

Continue · contextual cue · probe · minimal hint · worked example · practice · delayed audit

New learner activity → new observations

The cycle repeats, with cold independent performance providing stronger verification

The key is separating three things:

1. What happened: immutable interaction events and the learner's actual work.
2. What it might mean: semantic interpretations and uncertainty about the learner's understanding.
3. What LearnLoop should do: decisions about tutoring, scaffolding, retrieval, and assessment.

This separation prevents a particularly dangerous feedback loop: an LLM guesses that someone understands a concept, writes that into a summary, and another model subsequently treats the summary as independent proof.

There's research supporting the broad approach of extracting knowledge-component observations from tutoring conversations. Scarlatos, Baker, and Lan's [Exploring Knowledge Tracing in Tutor-Student Dialogues using LLMs](https://arxiv.org/abs/2409.16490) evaluates LLM-based interpretation of dialogue and subsequent knowledge tracing. But this is evidence that dialogue can support prediction, not that an LLM's interpretation of a conversation is automatically a reliable mastery judgment.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://arxiv.org\&sz=32)

arxiv.org



### How this fits LearnLoop's existing architecture

Looking at the current repository, this direction is already partly anticipated by the new [Learner Field v1 specification](https://github.com/6up-b/learnanything/blob/main/docs/specs/spec_learner_field_v1.md).

It explicitly discusses using question type, hint timing, help requests, and subsequent graded performance as weak signals about what needs attention. It also insists that asking questions should not be penalized as evidence of poor mastery.

The [Action Router v1 specification](https://github.com/6up-b/learnanything/blob/main/docs/specs/spec_action_router_v1.md) currently describes a guarded block-level chooser, comparing a staged policy, Perplexity Decider, and a frontier LLM, with local learned routers deferred. I would extend its inputs with Reader-derived information rather than create another competing top-level router.

So this is not a proposal to rebuild LearnLoop's learner model. It's a proposal to make the Reader a richer observation and intervention surface for the learning system you've already designed.

## 2. Generating interactive figures directly from textbook selections

This could be one of LearnLoop's most delightful features.

I'd call it Make this explorable.

The learner selects an equation, paragraph, or region of a figure. LearnLoop turns it into an interactive explanation with parameters to manipulate, predictions to test, and the original source alongside it.

Example: Make this equation explorable

Illustrative interaction · Two-sided exponential distribution

Interactive

The original density has parameter \\(\lambda=1\\). Change \\(p\\) to see how probability mass moves between the negative and positive sides.

Probability density

00.250.50.751-4-2024

x

Mixture parameter p

0.30

Probability to the left of zero

# 30%

Probability to the right of zero

# 70%

In LearnLoop, a generated figure could also ask for a prediction before revealing the result, or animate the associated CDF.

This is especially valuable for probability distributions, optimization objectives, matrix transformations, gradients, attention mechanisms, and dynamical systems.

Recent work makes the generation part plausible. For example, [PaperVoyager (2026)](https://arxiv.org/abs/2603.22999) investigates translating research papers into executable interactive web systems using structured mechanism modeling. Its evaluation is small—19 papers—and doesn't establish improved learning outcomes, but it's directly relevant technically.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://arxiv.org\&sz=32)

arxiv.org



### How I would implement this

| Stage                | Implementation                                                                                                         |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Selection            | Capture exact text span or bounding-box region over the original PDF figure                                            |
| Understanding        | Pass the crop, caption, equations, surrounding paragraphs, and source anchors to a multimodal model                    |
| Mechanism extraction | Identify variables, relationships, valid parameter ranges, assumptions, and what the figure is supposed to demonstrate |
| Generation           | Produce a structured interactive specification, with code only where necessary                                         |
| Verification         | Check equations, invariants, parameter constraints, and selected numerical examples                                    |
| Rendering            | Display within an isolated, unprivileged interactive surface                                                           |
| Learning             | Optionally invite a prediction or an explanation of what changes and why                                               |

I would actually start with a small declarative visualization language rather than unrestricted generated React components.

For example, the model could produce `InteractiveFigureSpecV1` defining chart types, parameters, mathematical functions, domain restrictions, and pedagogical annotations. A trusted renderer then builds the interface using a small set of reusable React components.

For unusual simulations, generated code could be a fallback.

Because LearnLoop is a Tauri application, running arbitrary LLM-generated JavaScript in the main webview is not a safe design. Tauri specifically documents capability isolation concerns with iframes on Linux. I'd use a separate unprivileged rendering environment without access to the application's IPC, files, or network.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://tauri.app\&sz=32)

Tauri

+1



I'd also distinguish a figure reconstructed from the original mathematical model from one that merely illustrates an inferred interpretation. A textbook illustration may not contain enough information to reconstruct an exact simulation.

A particularly interesting extension: the generated figure could become a diagnostic instrument.

Instead of merely moving a slider, the learner predicts what changing the parameter will do, and the system compares the prediction with the computed result. This can surface misconceptions that ordinary verbal questioning might miss.

Exploring a figure is not mastery evidence by itself. But an explicit, independently recorded prediction can become a formative observation.

## 3. Misconception-aware reading should be subtle, contextual, and explainable

I like your idea of indicating that a passage is related to something the learner previously struggled with.

In fact, I would prioritize this above aggressive automatic tutoring.

Suppose someone has repeatedly struggled with the distinction between probability density and cumulative probability.

Later they encounter a paragraph introducing a new continuous distribution.

Rather than interrupting with a question, LearnLoop could display a small contextual marker.

HYPOTHETICAL READER ANNOTATION

The probability of an interval is obtained by integrating the density function over that interval.

Connects to a distinction you revisited earlier

Density vs. cumulative probability

Related to your earlier work on integration bounds. Your current understanding hasn't yet been independently checked.

I'd prefer this to a warning that says the learner is weak at something. The latter can be wrong and can make the software feel judgmental.

### How should LearnLoop decide when to mark a passage?

The matching process would combine the source model with the learner model.

The passage is mapped to a set of candidate learning objects and facets. Those facets are connected to previous attempts, recorded error patterns, and unresolved misconception hypotheses.

Then a small relevance and restraint policy decides whether the relationship deserves attention.

A particularly important distinction:

A semantic match between a passage and a misconception is not evidence that the learner still has that misconception.

The link may simply indicate an opportunity to reinforce or clarify something they previously found difficult.

I would rank possible cues using approximately:

\\[ V\_{\text{cue}} = P(\text{relevant gap})\\, G\_{\text{clarification}} - C\_{\text{interruption}} - C\_{\text{false warning}} \\]

Here, the probabilities and gains initially could be heuristics; they shouldn't be presented as calibrated until you've evaluated them.

I'd make these cues optional, collapsible, and density-limited. Over time, LearnLoop could learn which cues are worth showing through subsequent independently measured performance rather than click-through rates alone.

Another useful extension is to offer two different relationships: this explains a concept you've had difficulty with and this is a new application of something you've demonstrated. The Reader should also reinforce what the learner is capable of doing, not just surface errors.

Your existing `Reading guide` and its “Worth a second look” passages give you a natural place to introduce this without creating a new navigation system.

## 4. The problem workbench: reconcile hints with the learner's existing work

This is where I think LearnLoop could offer a genuinely differentiated experience.

Most AI math tutors can answer a problem. Some can generate hints. Fewer consistently manage the learner's partially completed solution as a stateful object with potentially many valid paths.

That is the core difficulty you described.

### A solution should be represented as a graph, not just a final answer

Imagine a student solving a problem by conditioning on a random variable. They might use a CDF-based approach, while the textbook's answer uses PDFs directly.

Both routes can be valid.

An ordinary LLM tutor often retrieves or generates a worked solution and tells the student what step should come next. But it may implicitly assume the textbook's route, forcing the student to abandon their existing reasoning.

Instead, LearnLoop should construct a partial solution graph containing the student's steps, dependencies, assumptions, and possible continuations.

Student's existing derivation

Steps, assumptions, intermediate expressions, intended strategy

Valid reasoning

Preserve what can be reused; support alternative methods

Earliest unresolved step

Identify ambiguity, invalid transformation, or missing assumption

Minimal continuation or repair

Hint from the learner's current valid checkpoint, then let them continue

Here's a concrete example.

Suppose the learner writes:

\\[ F_Z(x)=-e^{-\lambda x} \\]

for the nonnegative support of an exponential random variable.

An unhelpful tutor might explain the exponential CDF from scratch.

A much better response would be:

> Your differentiation is consistent with the PDF, but check your boundary condition. At \\(x=0\\), your CDF gives \\(-1\\), whereas the cumulative probability should be \\(0\\). What constant of integration would fix this while keeping your existing derivation?

That hint refers to the student's actual work, explains why there is a problem, and identifies the smallest correction needed.

It also preserves the student's agency by not immediately giving the constant.

This is connected to the older [Continuous Hint Factory](https://arxiv.org/abs/1708.06564) and more recent [Data-Driven Hints in Intelligent Tutoring Systems](https://arxiv.org/abs/2603.07311) work. These explore generating next-step hints conditioned on partial learner states, rather than merely producing generic explanations.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://arxiv.org\&sz=32)

arxiv.org

+1



### Adaptive scaffolding: how much help should be given?

I'd make scaffolding an explicit dimension of LearnLoop's intervention policy.

| Assistance level            | Learner experience                                                           |
| --------------------------- | ---------------------------------------------------------------------------- |
| 0 — Independent             | Attempt without scaffolding; optional self-check when requested              |
| 1 — Metacognitive           | A question about the learner's approach or assumptions                       |
| 2 — Localize                | Indicate the first questionable step, without identifying the correction     |
| 3 — Targeted hint           | Explain the relevant principle or propose a subgoal                          |
| 4 — Partial worked solution | Demonstrate the next portion starting from the learner's valid work          |
| 5 — Full walkthrough        | Show and explain a complete solution, ideally preserving the learner's route |

The learner should always be able to ask for more help. LearnLoop's decision is what to suggest or offer first, not a restriction on access.

I'd adapt assistance at the level of learner × concept/facet × task, rather than assigning a global ability or scaffolding level to a person.

A learner could be excellent at computing expectations and relatively inexperienced with conditional probability proofs.

The policy also needs to react within a problem. If the learner repeatedly fails at the same transformation, the next intervention should generally change strategy instead of repeating an ineffective hint.

There's empirical support for adapting worked-example support to prior knowledge. The 2025 expertise-reversal meta-analysis found novices benefited more from higher assistance, while higher-prior-knowledge learners benefited more from reduced assistance. Earlier intelligent tutoring experiments also found advantages for adaptively faded worked examples compared with fixed fading in their settings.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://doi.org\&sz=32)

ScienceDirect

+1



But the more interesting research question for LearnLoop is not just how many hints to provide. It's:

Which intervention lets this particular learner recover from their present reasoning state, and how much of the solution should remain theirs to construct?

I'd treat hint generation and hint verification separately. One 2025 study of LLM-generated propositional-logic hints found that even when explanations appeared clear, accuracy and pedagogical context were significant limitations.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.sciencedirect.com\&sz=32)

ScienceDirect



For mathematics, symbolic verification with SymPy or other domain tools could check supported transformations. The LLM would still be responsible for interpreting intent, choosing an explanation, and handling reasoning too informal for symbolic verification.

## 5. Natural-language source discovery and syntopic reading

I would implement this as a search-first experience with an optional tutor, just as you suggested.

Imagine entering:

> Why can covariance be interpreted as an inner product? Show me where my books explain this, including examples or relevant prerequisites.

The Reader shouldn't immediately return a long AI essay.

It should retrieve candidate passages, rerank them, and organize the results by the role each source plays in answering the question.

Explore your library

Why is covariance an inner product, and where can I learn the geometric interpretation?

Example results — conceptual mockup, not a live library search

Foundation

Probability textbook · Covariance

Builds the definition using centered random variables

Geometric view

Functional analysis notes · \\(L^2\\) spaces

Explains expectation of products as an inner product

Application

Machine learning notes · PCA

Connects covariance geometry to eigendirections and variance

Optional tutor: compare these explanations or ask a follow-up

For implementation, this fits the proposed hybrid source-retrieval work already described in [Embedding Consumers v1, T6](https://github.com/6up-b/learnanything/blob/main/docs/specs/spec_embedding_consumers_v1.md).

I'd extend that retrieval pipeline to support source roles and relationships, not just semantic relevance.

| Retrieval component  | Additional role                                                            |
| -------------------- | -------------------------------------------------------------------------- |
| BM25/FTS5            | Retrieve exact terminology, symbols, exercise references                   |
| Dense embeddings     | Find equivalent concepts expressed differently                             |
| Multimodal retrieval | Find relevant figures, graphs, and visual derivations                      |
| Reranker             | Judge how directly a passage helps answer this particular query            |
| Concept graph        | Surface prerequisites, applications, and connected learning objects        |
| Claim comparison     | Distinguish equivalent claims, different assumptions, genuine disagreement |

The last one is particularly important for syntopic reading.

If two authors present different formulas, LearnLoop shouldn't assume one must be wrong. Their distributions, assumptions, conventions, or notation may differ.

I'd preserve each author's claim with its source context, then allow the model to propose relationships between claims. Those proposed relationships can be verified or reviewed before entering a trusted knowledge graph.

Personalization can improve the ranking, but the learner should be able to turn it off and view ordinary relevance-ranked results. A system that only retrieves what confirms the learner's existing understanding would be counterproductive.

## 6. How the Reader should actually update the learner model

This is the most technically important part of your proposal.

I would build a Reader Observation Compiler which translates raw interactions into typed, source-grounded observations.

Each interaction gets a durable event identity.

A compiler then produces structured interpretations with citations back to those raw events.

For example, here's an illustrative record from the mixture-distribution scenario:

```

{
  "kind": "reader_learning_observation",
  "source_span_ids": ["span_104", "span_105"],
  "learner_trace_ref": "attempt_52:step_3",
  "facet_candidates": [
    "cdf_boundary_conditions",
    "integration_constants"
  ],
  "observed_behavior": "Incorrect boundary value",
  "hypotheses": [
    "Forgot the integration constant",
    "Misunderstood the CDF support"
  ],
  "assistance": {
    "level": 3,
    "reveal_occurred": false
  },
  "verification": "model_proposed",
  "authority": "routing_only",
  "evidence_event_ids": ["event_81", "event_82"]
}

```

Notice what this does not say: “The learner has a 65% chance of understanding integration constants.”

That numerical inference belongs to the learner-state estimator and should depend on the reliability, difficulty, independence, and diagnostic specificity of the evidence.

### Three kinds of signals

I'd distinguish these explicitly.

| Signal type             | Example                                                                            | What it can change                                                                                                      |
| ----------------------- | ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Engagement/context      | Read a passage, opened a diagram, selected a word                                  | Contextual retrieval, suggestions, navigation—not mastery                                                               |
| Formative/diagnostic    | Asked a conceptual question, attempted a step, requested a hint, made a prediction | Candidate misconceptions, support policy, placement priorities; possibly low-weight evidence if independently validated |
| Independent performance | Solved a sufficiently novel problem without revealing hints or answers             | Capability estimates, retention models, misconception resolution, and verified learning claims                          |

This is compatible with the current learner-field specification's separation of question signals from demonstrated evidence.

### The actual statistical update

Let \\(z_t\\) represent the learner's latent knowledge state and \\(y_t\\) an observed response.

A general observation model might be:

\\[ p(y_t\mid z_t,\\;q_t,\\;h_t,\\;e_t) \\]

where \\(q_t\\) describes the problem's demands, \\(h_t\\) describes assistance provided, and \\(e_t\\) describes exposure to relevant prior solutions or cues.

The model should interpret a correct response after a nearly complete worked solution differently from a correct response on an unseen independent task.

The corresponding Bayesian filtering idea is:

\\[ p(z_t\mid D\_{1:t}) \propto p(y_t\mid z_t,q_t,h_t,e_t)\\, p(z_t\mid D\_{1:t-1}) \\]

This is a conceptual formulation; LearnLoop's current EKF and effective-observation machinery have their own approximation and evidence contracts.

For tutoring actions that actually teach something, there is also a state transition:

\\[ z\_{t+1}\sim p(z\_{t+1}\mid z_t,a_t) \\]

That distinction matters: a hint can simultaneously reveal something about the learner and change their understanding.

I'd initially keep LearnLoop's established evidence-discounting and learner-state logic authoritative, while evaluating assistance-conditioned observation and transition models as challengers.

### Natural-language summaries are still valuable

I would generate two separate summaries from the same evidence ledger.

The narrative summary helps the tutor and learner recover the intellectual context of the session:

> Worked through mixture distributions using conditioning on the selected component. The learner constructed the CDF approach but initially made an error involving a boundary condition. A targeted hint enabled correction. Independent application to a novel distribution remains unverified.

The decision summary is shorter, structured, and designed for policy use.

Session state projection — illustrative

| Relevant capability   | Piecewise CDF derivation                                     |
| --------------------- | ------------------------------------------------------------ |
| Observed progress     | Corrected a local error after targeted assistance            |
| Open hypotheses       | Boundary conditions vs. integration constants                |
| Evidence status       | Assisted practice; cold verification pending                 |
| Possible next actions | Continue reading, near-transfer practice, delayed cold audit |

The narrative can be regenerated whenever needed. It isn't an additional independent observation.

I would keep the underlying event log append-only, with the compiler's versions and evidence IDs attached to its outputs. That makes the entire state projection replayable if you improve the semantic model later.

Also, state updates should not have to wait for the Reader session to end. A newly verified problem step or meaningful hint event can update the provisional state immediately. The end-of-session operation consolidates, summarizes, and prepares future actions.

## 7. How to connect this to the action router

I think we need two timescales, rather than making the full router decide every small interaction.

### Within a reading or problem-solving session

A lightweight, guarded Reader intervention policy chooses how to respond to the learner's current activity.

Its possible actions include continuing without intervention, showing a source relationship, presenting a short clarification, requesting a prediction, giving a targeted hint, displaying a partial worked example, or helping the learner return to their original task.

If the learner explicitly asks for a hint, the policy chooses how to help rather than treating no help as an appropriate response.

Initially, this can be mostly rule-based, with semantic interpretation from the LLM and constraints inherited from the broader learning system.

### At study-block boundaries

The existing action router receives a richer `LearnerStateCardV1` containing the compact Reader observations, evidence summaries, open hypotheses, goals, assistance history, and source relationships.

Then it can compare larger actions: another reading block, targeted repair, independent practice, a diagnostic probe, a delayed review, or continuing with the learner's chosen activity.

The current action-router specification already emphasizes hard feasibility constraints, a restraint gate, decision receipts, and logged probabilities when using its model mixture. I'd preserve those features.

You previously explored action-conditioned Q/K retrieval and local learned scoring for routing. That's still an interesting longer-term possibility, particularly for finding which historical learner events are relevant to each candidate action. But I'd follow the current spec's more conservative rollout before promoting a learned router.

A useful value function for the future model would be:

\\[ Q(s,a) = \mathbb E[\Delta C\_{\text{cold}}\mid s,a] +\alpha\\,\operatorname{EIG}(a) -\beta\\,\mathbb E[T(a)] -\gamma\\,R\_{\text{false diagnosis}}(a) \\]

Here, \\(\Delta C\_{\text{cold}}\\) is improvement on later independent capability, `EIG` measures information gain, \\(T\\) is time or effort, and the final term penalizes harmful interventions arising from unreliable diagnoses.

The quantities will initially be uncertain. The real purpose of logging interventions, assistance, propensities, and later outcomes is to make it possible to learn or validate these values.

Crucially, don't optimize only for correctness on the next step. A full solution reveal may maximize immediate correctness while undermining independent problem-solving.

The learner-state model should estimate what the learner knows. The action policy should estimate the consequences of helping in different ways. Those are related but distinct modeling problems.

## 8. The delayed cold problem closes the learning loop

I especially agree with your suggestion that LearnLoop should produce an unfamiliar problem after the Reader session.

I'd make this the primary mechanism for turning a session's provisional learning claims into stronger evidence.

Take the mixture-distribution example. The learner has read the section, explored the interactive figure, completed an exercise, and resolved an error with some help.

A few days later, LearnLoop presents a new problem without the original explanation.

EXAMPLE · DELAYED INDEPENDENT CHECK

Mixture distributions

Cold attempt

Suppose \\(X\\) is generated by choosing between two distributions:

- \\(Y\sim\operatorname{Uniform}(-1,0)\\), chosen with probability \\(p\\).
- \\(Z\sim\operatorname{Exponential}(1)\\), chosen with probability \\(1-p\\).

Derive the piecewise CDF of \\(X\\). Explain why your expression is continuous at \\(x=0\\).

The original chapter, previous hints, and worked examples would stay out of view during the cold attempt. The learner could still request help, but doing so would transition the attempt to an assisted activity rather than secretly preserving cold status.

This tests the same underlying conditioning and support concepts in a different form.

I would distinguish unseen wording, unseen surface, and genuinely unfamiliar application. Changing numerical constants is not necessarily meaningful transfer.

The exercise generator should use the existing practice-family and task-blueprint machinery, with freshness checks and source-grounded verification.

The question should be selected because it tests specific capabilities that remain uncertain, not merely because the learner finished a chapter.

One short problem may provide useful evidence about several facets, but it generally cannot justify a claim that an entire chapter is mastered. If the chapter involves definitions, derivations, geometric interpretations, and transfer tasks, LearnLoop should track which capabilities have actually been covered and schedule further checks selectively.

After the cold attempt closes, the Reader could reopen directly to the most relevant source passage or earlier inquiry branch if repair is warranted. That completes the loop between reading, attempting, verifying, and returning to the source.

## 9. What I'd actually build next

Given what is already present in your codebase, I would not begin with an entirely new learned model or broad Reader redesign.

I'd complete one vertical slice that can be evaluated end to end.

| Stage                           | Change                                                                                          | What it proves                                                            |
| ------------------------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| 1. Step-aware workbench         | Persist problem steps, hint events, assistance levels, and original-source anchors              | Can LearnLoop give a hint from the learner's actual work?                 |
| 2. Reader observation compiler  | Convert those events into typed facet candidates, hypotheses, and assistance-aware observations | Can it preserve reasoning context without inventing mastery evidence?     |
| 3. Misconception-aware cues     | Use existing mapped misconceptions to surface related passages with restrained UI               | Can the Reader help prevent recurrent errors without becoming disruptive? |
| 4. Cold follow-up               | Generate or select a held-out problem on the same capability, administered without source cues  | Does the previous help lead to independent performance?                   |
| 5. Syntopic retrieval           | Add role-aware hybrid search across sources and expose an optional contextual tutor             | Can a learner find a more useful explanation without losing their place?  |
| 6. Interactive figure generator | Introduce verified, declarative simulations from selected equations and figures                 | Do predictions and manipulations improve conceptual understanding?        |

I'd evaluate the entire workflow with one math-heavy textbook first, particularly because derivations give you relatively concrete opportunities to check intermediate reasoning.

Three experiments would be especially informative: compare generic hints with work-aligned hints; compare misconception-aware reading with ordinary reading; and compare Reader summaries alone with typed evidence plus summaries as inputs to the routing policy.

The primary outcome should be delayed, independently demonstrated learning per unit of learner effort. Secondary measures could include time spent stuck, rate of successful continuation after hints, incorrect misconception cues, unnecessary interruptions, and differences between assisted and independent performance.

### My preferred long-term mental model

LearnLoop's Reader becomes a source-grounded environment for constructing understanding.

Its interactive figures help the learner explore an idea. Syntopic reading helps them connect ideas. The problem workbench helps them apply an idea. Misconception-aware cues help them notice important distinctions. The observation compiler preserves what their behavior actually demonstrates. The action router decides what is worth doing next. Delayed independent tasks test whether the learning has become durable.

I think the deeper opportunity is this: LearnLoop could develop a memory not only of what a learner knows, but of how that learner arrives at understanding, where their reasoning tends to diverge, and which forms of assistance help them recover.

That would be a much richer foundation for adaptive tutoring than a static concept-level mastery estimate—and it fits the architecture you've been developing rather than requiring an entirely separate system.&#x20;"

My response: "Tell me what you think of the following and what you would add based on our conversation: natural language queries for our canonical sources. We have the canonical source vault act as a RAG that the action router’s LLM can query. This can be for practice problems or probes to serve the user based on what they need instead of generating a question surface from a card.  We can also serve the learner explanations directly from the canonical source based on natural language queries from the tutor"

Agent response: "I think this is an excellent direction for LearnLoop, and I'd actually make it a foundational capability rather than just another Reader feature.

What you're describing is essentially turning the canonical source vault into a queryable instructional knowledge base, available to both the action router and the tutor.

The important shift is that LearnLoop would no longer depend primarily on generating a practice question from an existing card. It could instead search the learner's textbooks, papers, worked examples, and exercises to find the material best suited to their current learning needs.

I'd extend your idea in one important way:

The vault should retrieve not just relevant content, but content that can fulfill a particular instructional purpose for a particular learner.

For example, the system might search for:

- An unfamiliar exercise that discriminates between two suspected misconceptions.
- A worked example using the learner's current problem-solving approach.
- A short passage explaining a prerequisite the learner is missing.
- An alternative explanation of a concept the learner has struggled with.
- A figure or equation suitable for generating an interactive explanation.
- A problem requiring several concepts the learner is trying to integrate.

That's much more useful than ordinary document RAG, which typically optimizes for finding passages relevant to a question.

## 1. One canonical vault, three related retrieval capabilities

I would expose the vault through three closely related operations.

| Capability      | Question it answers                                                                                   | Consumer                                        |
| --------------- | ----------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| `find_sources`  | What source material explains, demonstrates, or contextualizes this concept?                          | Reader, tutor, action router                    |
| `find_practice` | Which existing exercise best tests or develops this capability?                                       | Practice selector, diagnostic controller, tutor |
| `find_examples` | Which worked example, diagram, or derivation can help this learner progress from their current state? | Tutor, problem workbench                        |

I'd implement these on top of a shared retrieval substrate, rather than building three unrelated indexes.

Your current specifications already anticipate much of this.

In particular, [Embedding Consumers v1](https://github.com/6up-b/learnanything/blob/main/docs/specs/spec_embedding_consumers_v1.md) describes `find_practice(query, constraints)` using facet dossiers, BM25/dense retrieval, item-level reranking, and scheduler admission. Its T6 section separately proposes hybrid retrieval over source blocks.

What's missing is a unified ability to retrieve instructional material directly from canonical source documents, connect it to learner capabilities, and make it available consistently across the Reader and tutoring workflows.

This is more of an integration and content-model extension than an entirely new system.

## 2. Don't eliminate cards—change what they represent

I wouldn't entirely replace question cards with retrieved textbook problems.

I'd separate the skill being developed from the particular exercise used to develop or assess it.

For example:

LEARNING OBJECT / CAPABILITY

Derive the CDF of a mixture distribution

Target facets: conditioning, support, integration boundaries

Existing source exercise

Textbook exercise 4.12, imported verbatim

Generated variant

New distributions, verified to test the same capability

SELECTION POLICY

Serve the most useful eligible problem

Based on uncertainty, difficulty, exposure, novelty, and learning goal

Your current family/card/surface architecture is well suited to this. The card or family can preserve what an activity is supposed to test, while its surface can be a canonical textbook exercise, a generated variant, or another verified presentation.

That gives you the best of both approaches.

Retrieval-first: Prefer an appropriate, already-authored problem when one exists.

Generation-on-demand: If the available problems are too easy, too familiar, unsuitable for diagnosis, or don't test the required capability, generate a new surface using relevant canonical material as a reference.

Importantly, an authentic source problem isn't automatically a good assessment problem. It may be familiar, ambiguous, excessively difficult, or not designed to isolate the misconception you're investigating.

The retrieved problem still needs an explicit competency mapping, answer/rubric verification, and the appropriate exposure checks.

## 3. Let the router query the vault—but keep selection and retrieval separate

I like the idea of giving the action router's LLM access to the vault, but I would be careful about letting that LLM freely retrieve and serve material in one opaque decision.

I'd preserve the action router's current responsibilities: deciding what kind of activity is worthwhile, based on the learner state, uncertainty, expected benefit, and attention budget.

Then the retrieval system finds candidate material that can satisfy that decision.

Learner state + current objective

Weak evidence about integration boundaries; learner wants to derive piecewise CDFs

Action router

Choose a diagnostic probe rather than another explanation

Instructional retrieval

Find an exercise that distinguishes boundary-condition confusion from integration errors

Eligibility and quality checks

Correct scope · suitable difficulty · verified solution · appropriate exposure status

Serve the selected exercise

Preserve the selected item's identity, source provenance, and assessment conditions

There is one complication: the router needs to know that suitable material exists before choosing an action that depends on it.

I'd solve that with a two-stage interface. A cheap candidate-discovery pass tells the router what kinds of activities are actually available, along with estimates of difficulty, relevance, and cost. After the router chooses a block, the practice selector performs final item retrieval and admission.

That lets the router compare feasible options without giving it unrestricted responsibility over assessment material.

It's also consistent with your current [Action Router v1](https://github.com/6up-b/learnanything/blob/main/docs/specs/spec_action_router_v1.md) design: the LLM helps choose the action, while within-block item selection and hard constraints remain separate.

### Natural-language queries with typed constraints

I would avoid making the API just `search(query: string)`.

The LLM should be able to express an educational intention in natural language, but important constraints should be machine-enforceable.

For example:

```

{
  "tool": "find_practice",
  "query": "Find a problem that can distinguish
    confusion about CDF boundary conditions
    from errors in integration.",
  "intent": "diagnostic_probe",
  "target_facets": [
    "piecewise_cdf",
    "boundary_conditions"
  ],
  "constraints": {
    "unseen_required": true,
    "allow_generated_variants": true,
    "exclude_exposed_families": true,
    "answer_visibility": "withhold",
    "max_estimated_minutes": 8
  }
}

```

This gives us a powerful interface for the action router, the tutor, and external agents.

The search can return grounded candidate items, source references, and assessment metadata. Importantly, the tool should return eligible candidates, not automatically administer an exercise merely because an LLM requested it.

A separate tutor query could say:

> Find a worked example using CDF-first derivation, preferably one that illustrates an integration boundary mistake. The learner has already derived the density correctly and should not have to restart.

That's exactly the sort of personalized, work-aligned retrieval that would make your problem-solving workspace much better.

## 4. Serving explanations directly from canonical sources

This might be even more valuable than retrieving practice problems.

One weakness of ordinary AI tutoring is that the model may regenerate an explanation from general knowledge when a carefully written explanation already exists in the learner's textbook.

I would support three response modes.

| Mode                              | What the learner receives                                                                           | Best use                                                                        |
| --------------------------------- | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Original source                   | A short cited excerpt, original equation, figure, or worked example                                 | When the canonical source directly answers the question                         |
| Source-grounded explanation       | A tutor explanation based on the retrieved passages, with links back to them                        | When the learner needs clarification, synthesis, or simpler language            |
| Personalized bridging explanation | A short explanation connecting the source to the learner's existing work or suspected misconception | When the standard explanation didn't resolve the learner's particular confusion |

The third mode is especially promising.

Imagine someone trying to derive the CDF of a piecewise density. They have correctly integrated one side but used the wrong constant on the other.

The tutor could retrieve the textbook's example of integrating a density from its support boundary. Then it could say:

> Your approach is consistent with the method in Section 3.4. The difference appears at the boundary condition. Here's the corresponding step from the book—compare its integration limits to the ones in your derivation.

This is more useful than simply displaying the entire worked solution.

It also makes the original textbook a central part of the learning experience instead of treating the PDF as context to be consumed by an AI.

A recent 2026 study of a learner-state-aware RAG algebra tutor found higher expert ratings for several instructional-quality dimensions than a prompt-only tutor, though it involved scripted interactions rather than real student learning outcomes. Interestingly, the RAG condition also produced more unsupported-content flags, so retrieval grounding alone does not establish correctness.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.frontiersin.org\&sz=32)

frontiersin.org



I'd therefore make cited passages, source-version identities, and a distinction between source-authored content and AI interpretation fundamental to the API.

## 5. What I'd add to make the vault truly instructional

### A. Index instructional roles, not just passages

A conventional RAG corpus might contain text chunks and embeddings.

For LearnLoop, I would give the vault a richer set of retrievable instructional assets.

| Asset                       | Why it matters                                                    |
| --------------------------- | ----------------------------------------------------------------- |
| Definition or theorem       | Establishes the authoritative concept or relationship             |
| Explanation or intuition    | Helps construct understanding                                     |
| Worked example              | Demonstrates a method, possibly with intermediate reasoning steps |
| Exercise                    | Creates an opportunity for practice or assessment                 |
| Figure or interactive model | Supports visual and exploratory understanding                     |
| Counterexample              | Distinguishes a misconception from the correct concept            |
| Prerequisite passage        | Explains something the learner needs before continuing            |
| Alternative treatment       | Allows syntopic reading across authors and sources                |

These would be derived records anchored to immutable source versions, not replacements for the source itself.

A single passage could have several instructional roles. A theorem might be both a source of formal definitions and the basis of an exercise. The role classifications should carry confidence and provenance rather than being assumed infallible.

This would make retrieval much more capable than text similarity alone.

### B. Add misconception-conditioned retrieval

This follows directly from our earlier discussion about personalized misconception-aware reading.

Imagine LearnLoop has two competing hypotheses:

- The learner doesn't understand how a CDF accumulates probability.
- The learner understands the concept but makes mistakes with integration limits.

Instead of simply retrieving information relevant to CDFs, the system can request material that helps distinguish or repair those specific hypotheses.

That suggests two useful retrieval intentions: diagnostic discrimination and targeted remediation.

The diagnostic query finds questions whose possible responses are informative about which hypothesis is more likely. The remediation query finds a short explanation, counterexample, or worked step that addresses a particular gap.

Those are substantially different from generic semantic search.

I would also index source-authored contrasts—passages that explicitly distinguish easily confused ideas. They may be particularly effective for misconceptions such as independence versus zero covariance, PDF versus CDF, and conditional versus unconditional probability.

### C. Make syntopic retrieval a first-class operation

This is where your canonical vault becomes more than an isolated textbook collection.

Suppose the tutor asks:

> Find different explanations of eigenvectors, including a geometric interpretation and a treatment in the context of PCA.

The retriever should be capable of producing a structured set of related passages with their distinct perspectives.

I'd introduce something like `compare_sources(query, facets, requested_perspectives)`.

It would return source-local claims and links, supporting a UI where the learner can explore how different authors approach the same concept.

Importantly, source comparisons should distinguish equivalent claims, different assumptions, and actual disagreements. We shouldn't let an LLM silently fuse every retrieved statement into one supposedly canonical account.

### D. Add source-conditioned interactive explanations

Your explorable-explanations idea fits this retrieval architecture beautifully.

The tutor might issue:

> Find the equation, original figure, and relevant assumptions for the distribution being discussed. Determine whether it can support an interactive parameterized visualization.

The retrieval system supplies grounded mathematical information, and a separate generation-and-verification pipeline produces the interactive figure.

I would keep this distinct from the tutoring decision itself. Retrieving a relevant equation doesn't guarantee that an accurate interactive visualization can be generated.

The same asset could later be reused, versioned, and improved instead of regenerating it every time a learner selects the passage.

## 6. The biggest risk: contamination of independent assessment

I would make this a non-negotiable design constraint.

If the entire source vault is available to the router and tutor, and that vault contains textbook exercises alongside worked solutions, the system can inadvertently expose the very answer it later wants to test.

This becomes especially dangerous if a retrieved explanation contains a solution to a reserved cold problem, or the router's LLM has seen an answer key when deciding which item to serve.

The solution is to make retrieval permissions depend on the instructional context.

| Context                            | Retrieval permissions                                                                                                     |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Reading and exploration            | Source passages, worked examples, explanations, figures                                                                   |
| Assisted problem-solving           | Relevant instructional material and approved hints; solution reveal is tracked                                            |
| Diagnostic or cold attempt         | Eligible problem statements only; no reserved solutions or equivalent worked examples exposed to the learner-facing model |
| Post-attempt feedback              | Relevant solutions, rubrics, explanations, and previous reasoning                                                         |
| Content authoring and verification | Full reference materials through a separate, appropriately isolated workflow                                              |

Even a textbook exercise retrieved from a previously unread page may be a poor cold test if the learner has encountered an equivalent worked example.

This is another reason to preserve generated variants and the current surface-family exposure machinery rather than replacing it.

I would also preserve a retrieval receipt with the query, source version, returned asset IDs, access policy, and eventual exposure events. This makes it possible to reconstruct what the learner and tutor could access at each point.

## 7. Let retrieval become part of LearnLoop's evidence loop

Here's an additional idea I think is particularly valuable.

LearnLoop shouldn't only remember which question it served. It should also remember which explanation it retrieved, why it selected that explanation, and whether it actually helped the learner.

Suppose a student struggles with conditional expectation.

The tutor retrieves a visual explanation from one book. The student remains confused. It then retrieves an algebraic derivation from another book, after which the student successfully solves a related problem.

Later, the student independently solves a novel problem involving the same concept.

That sequence provides potentially useful evidence about the kinds of interventions that help this learner.

We could model each retrieval-supported intervention as:

\\[ (s_t,\\;a_t,\\;r_t,\\;y\_{t+1}) \\]

where \\(s_t\\) is the learner state, \\(a_t\\) is the instructional action, \\(r_t\\) is the retrieved source asset, and \\(y\_{t+1}\\) is the subsequent observation.

I'd store the relationship between an intervention and its later outcomes, including cold assessments. However, improved performance after an explanation doesn't by itself establish that the explanation caused the improvement; comparing policies requires appropriate randomized variation or other causal identification.

Over time, LearnLoop could learn whether a particular learner tends to benefit more from worked examples, interactive visualizations, counterexamples, or targeted hints for specific task types.

This would take the current action router in an interesting direction: selecting both the instructional action and the supporting source material, while retaining separate constraints and evaluation for each decision.

## 8. What I would implement first

I would start by extending the retrieval systems you already have rather than designing a new RAG framework from scratch.

| Priority | Implementation                                                                                 | Why                                                                     |
| -------- | ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| 1        | Add source-anchored exercise and worked-example records to the retrieval index                 | Establishes high-quality instructional assets alongside source passages |
| 2        | Extend `find_practice` to search original textbook exercises, not just existing practice items | Immediately makes the existing scheduler and tutor more useful          |
| 3        | Implement `find_explanations` with instructional intent, facet targets, and source citations   | Enables contextual tutoring and personalized source selection           |
| 4        | Connect retrieval results to the workbench's learner-step history                              | Enables hints that actually reconcile with existing work                |
| 5        | Add cross-source comparison and misconception-conditioned retrieval                            | Delivers the syntopic and personalized Reader experience                |
| 6        | Evaluate retrieval choices against delayed independent performance                             | Establishes whether improved retrieval actually improves learning       |

For the first implementation, I would test whether source-grounded retrieval improves relevance and learning outcomes compared with the existing practice-item selection pipeline. Keep a simple BM25 baseline, a hybrid retriever, and reranking as separate experimental conditions.

A recent textbook-RAG benchmark found hybrid retrieval improved passage recall against BM25, but its small generation pilot did not show that grounded answers were necessarily more accurate than closed-book answers. That reinforces the importance of testing retrieval quality and instructional effectiveness separately.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.nature.com\&sz=32)

Scientific Reports



## 9. My proposed refined version of your idea

I'd describe the feature this way:

## Canonical Source Retrieval as a Shared Instructional Service

LearnLoop's canonical source vault should provide a natural-language, source-grounded retrieval interface accessible to the Reader, tutor, action router, and practice-generation pipeline.

The system should support retrieval of original source passages, explanations, worked examples, figures, exercises, and conceptual relationships based on a learner's goals, demonstrated capabilities, unresolved misconceptions, and current problem-solving context.

The action router determines the most useful instructional objective. Retrieval services identify suitable source-grounded materials, while the scheduler and content-validation systems enforce eligibility, difficulty, freshness, exposure, and assessment constraints.

When appropriate canonical exercises exist, LearnLoop can serve them directly rather than generating new question surfaces. When suitable exercises do not exist, retrieved source materials can ground the generation and verification of new variants.

The tutor should be able to retrieve authoritative explanations, provide direct source references, compare explanations across documents, and adapt the amount of scaffolding to the learner's current reasoning.

Every retrieval-supported intervention should retain its provenance, assistance context, and relationship to subsequent learner observations, enabling the learning system to evaluate and improve its instructional decisions over time.

The most important conceptual addition is that I wouldn't think of the canonical vault as merely a RAG database.

I'd think of it as LearnLoop's instructional substrate.

A conventional RAG system answers, “What information is relevant to this query?”

LearnLoop's system should be capable of answering a much more consequential question:

“Given what this learner is trying to accomplish, what they have already demonstrated, and where their understanding remains uncertain, which existing piece of instructional material is most likely to help them progress—and how should it be used?”

That lets you reuse the enormous amount of pedagogically structured material already contained in textbooks without giving up the adaptivity of your current mastery, misconception, and decision models.

It also creates a cohesive connection between nearly everything we've been discussing: syntopic reading, misconception-aware annotations, problem-solving workspaces, minimal repair, interactive explanations, the action router, and delayed independent verification."
