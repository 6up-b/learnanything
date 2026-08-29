
## Interesting resources for guiding Learnloop further direction
- Lead user insights for larger-scope design ideas
	- https://augmentingcognition.com/ltm.html 
	- https://cognitivemedium.com/srs-mathematics 
	- https://numinous.productions/ttft/
	- https://michaelnotebook.com/memorize/index.html 
	- https://michaelnotebook.com/ongoing/hiums.html 
	- https://quantum.country 
	- https://lesleylai.info/en/flashcards/
	- https://news.ycombinator.com/item?id=48861319
	- https://notes.andymatuschak.org/zKy4FsHTcf8LdkgXkMueeGL
	- https://www.supermemo.com/en/blog/twenty-rules-of-formulating-knowledge
	- https://borretti.me/article/the-applicability-of-spaced-repetition
	- see spec_andymatusnotes for more on andy matus's notes
- Algorithim insights
	- https://arxiv.org/html/2504.04204v1 primary
	- https://arxiv.org/html/2508.21184
	- https://openreview.net/pdf?id=CY9MlORQs5 
	- https://arxiv.org/html/2504.04204v2
	- https://arxiv.org/html/2602.14279
	- https://arxiv.org/html/2602.23201
	- https://arxiv.org/html/2604.13817
	- https://arxiv.org/html/2508.21184 
	- https://arxiv.org/html/2507.05220 
	- https://arxiv.org/html/2504.04204v2
## Ingestion as a peritextual active reader
SuperMemo's incremental reading model treats reading as a funnel from sources, to selected passages, to extracts, to active knowledge and eventually creative application. 

We can have
- skim: identify core claims, terms, figs, and questions
- anchor reading: deeply process 1 especially important section in a source
- syntopic view: compare several sources around a concept or open question
- incremental reading: revisit selected passages over time, extract and refine only what remains directly valuable. 

So the user opens the source, begins reading, then begins asking (this triggers background extraction and inventory, progressively proposed study structure). 

We should have the reader be able to view the canonical source within the Tauri application, then be able to do the following:
- Ask
- Show a worked example
- Find an alternative explanation
- Why does this matter
- Help me remember this
- Mark this as confusing
- Connect it to something I know
- Test me later on this
- Not worth remembering
The reader then supports the metacognitive feedback loops that books usually leave to the reader, like "Did I understand this?". 
We can have this tie back into our existing section based learnloop ask tutor, primed attempts and other aspects.
For practice items, we have cold retrieval first. Then, we can have immediate restoration of the source neighborhood afterward, including the learner's original annotations. 

Additionally, we should make the authoring of additional prompts/PI easier. AI should reduce the friction and mechanical cost of prompt creation without automating the interpretive act that makes the material personally meaningful and effective. We can have both large automatic study map generation from the canonical source, but we should have users write author good question/answer for themselves since writing flashcards is itself a thinking skill. Early cards from a user are often "exhaust" from the process of forming an understanding. 
Another issue I noticed from conducting research on lead users was how other learning system frame deletion as failure. However, we should look into how we could frame it as healthy model maintenance.
A PI can be originally useful, then too easy. Or it can be ambiguous, missing context, test duplicate surfaces, wrong granularity, no longer relevant, repeatedly failed because the underlying explanation is poor, or retired because a better activity replaced it. Retiring a PI shouldn't remove or delete the underlying knowledge of the user latent state or the underlying facet evidence/source relationship/learning goal. In the end, the most important thing is that the learner is actually using and getting value from the application. This means making the friction as low as possible for usual pain points throughout the learning process. 

Users need assistance developing the meta skill of formulation (which should result in better scores and better transfer). For example, what is the atomic claim, what would prove I understand it rather than recognize wording, what mistake would reveal I have a shallow internal model, what should  I be able to produce or discriminate, is this worth committing to long-term review. This can be a scale, where novices can be heavily scaffolded and experts can be more free form. 


  In this way, we can hope to have something where the friction experienced by the user to add a PI is minimized since AI authorship
  can fill all of the minutia and the user reaps the cognitive benefit of making the question and answer. We can also have several
  steps of how a user can go through and approach a canonical source they haven't seen before, and as they go through it more and
  more PIs/LOs can be created dynamically based on user intent of what they find valuable to memorize and keep. The learner can
  select exercises they want to practice and be good at from the chapter's end, and the user's annotations and questions on topics
  from the canonical source can then be turned into LOs and PIs that are emotionally important to the learner instead of a bunch of
  random cards. PIs and LOs for learners who are students or following courses could also be based on canonical ingestion of the
  final practice exams they want to get good scores on in order to guide authoring. But even after being able to solve a final
  practice exam, the student can always be escalated to higher depth ladder questions.

## Quest
We could also look into a Quest system that helps guide larger term meaning from goals independent from exams or mastery by n days. We should be able to say "I need this for the model I'm implementing", "I want to be conversationally fluent by my trip", "I want to be able to fully understand this paper". These "why"s can guide item generation and future resurfacing without being shown as a direct cue during every cold attempt. 

Michael Nielson found Anki to be most effctive when it was embedded in a concrete writing/research project. The deeper goal is metabolizing an experience so that one thinks or acts differently in the future with these priors. In this way the top level object isn't just "reach n% recall by {date}", but "understand covariance geometrically well enough to be able to teach it and reason about PCA without treating it like a formula". So the recall target is a measurable subgoal of the project rather than the project itself. To ensure and create a habit, the user should feel like they know why they're learning this, what the knowledge lets them do, which parts deserve recurring attention and which things can remain searchable references (although this can become ambiguous when trying to have long term learning versus studying for an actual exam or technical interview where minutia that might be better as a searchable reference becomes important). We need to distinguish useless clerical friction that should be relinquished to an AI from functional friction: the effort of deciding what a practice item/card in Anki's case is about may be where a lot of encoding and understanding occurs.


## Algorithmic critiques
Some of the most important aspects of the app is to be able to discover which parts are already understood and which facts are most salient to the learner. I haven't had enough time with mvp-0.7 LO, but from vaults like arxiv and linear_algebra it felt like learnloop needed a lot of evidence to have a significant mastery increase. This might be different now that facets are shared.

Specifically for domains that are highly conceptual and abstract, the learner is not memorizing a bag of tricks or solutions to memorize for practice items, we're instead trying to solidify an internal model that is built through reading, thinking and solving problems. The goal is to have an AI know which facts are salient for you, what you already know, which microvolumes of knowledge can be encoded lightly with just a few PIs/loops and which things need more shoring up and consequently more coverage. 

I think in general all PIs and probes being static (especially from probe to PI) reduces their real effectiveness and obfuscates the process of real effective mastery. For example, durable understanding needs varied cues, increasing complexity, connectivity and surprise. A single stored question by itself can't test transfer because the learner becomes familliar with the prompt's surface. For mathematics this is more clear--restating the same idea, constructing a proof, answering structural quesitons, modifying failed problems, solving same family with different parameters, attempting cold retrieval. Perhaps instead we should look for how families of Pis can be dynamic and produce:
- direct retrieval
- explanation from memory
- geometric representations
- example generation
- counterexample generation
- contrastive discrimination
- error diagnosis
- near-transfer variants
- far transfer or new context problems
- teach back
- authentic use

Perhaps PIs can be an administered instance of a richer practice family represented by the LO while preserving the current immutable assessment contract at presentation time. We would have a family emitting different PI instances over time with a depth ladder (retrieve, explain, represent, discrminate, transfer, edge cases, teach), but the depth ladder has to be extensible enough to different fields and subjects. Generated             variants need to be quality filtered and familiarity discounted (not assumed to be entirely independent merely because the wording or numbers changed). 
## Deepened rigor for technical studies
For mathematics, computer science, ML and other things, we should have a series of deepening actions such as being able to reconstruct the proof, identify the key area in 1 sentance, explain why each assumption is needed, then with high mastery the person should be able to remove an assumption and find where the proof fails, or apply the technique elsewhere. 

I think for these types of subjects also we have visible learning arcs.
- I can retrieve it
- I can explain it
- I can recognize when it applies vs when it doesn't apply
- I can distinguish nearby ideas
- I can vary assumptions and handle edge cases
- I can apply it within new settings and ransfer
- I can teach it or make something with it

For learners who make repeated errors and schema-based misconceptions, we should also prompt them with the canonical source material side-by-side and explain what they should've done (and why they're wrong) as a means of immediate remediation. We have to be careful with this because we don't want failure to be punishing or the user to resent not getting something exactly correct then having to write a trivial explanation like a school assignment. 

## Lowering friction

From Matuschak's experiments we can see that deciding what the particular reader wants to learn is a big failure point for other systems. We should begin emphasizing task and commitment quality within evidence collection/telemetry. For example, P(candidate is accepted), P(candidate survives 90 days without retirement), P(candidate improves unseen transfer), P(candidate produces robust delayed performance), P(candidate's value exceeds its review burden). 

Maybe another ML question would be which proposed activity is worth adding to this learner's recurring attention as opposed to which already accepted item should appear 6 positions earlier in the Today queue. We should add burden outcomes so we don't optimize for narrow proxies.

Another source of friction is how do we reduce ceremony for a user stating "I just read this paragraph on eigenvectors that helped me change how I understand them. Help me remember it". 
## Brainstorming on what a new user journey would look like

1. The learner creates a Quest: "Understand covariance geometrically "
2. While reading the canonical source, she highlights a passage explaining that real symmetric matrices have orthogonal eigenspace and writes "I know how to compute eigenvectors but I don't see why this forces the axes of a covariance ellipse to be perpendicular".
3. Learnloop maps this to existing canonical facets but preserves the personal annotation. It then proposes some committments:
	1. Explain geometriclaly why symmetry leads to orthogonal principal directions
	2. Contrast a covariance matrix with a nonsymmetric linear map having nonorthogonal eigenvectors
4. PI family evolves: 
	1. retrieve the symmetry -> orthogonality claim
	2. explain the covariance ellipse without equations
	3. diagnoalize an unseen 2x2 covariance matrix
	4. distinguish covariance/PCA/SVD in mixed scenarios 
	5. teach it to a student who will ask questions about your weakest facets
5. A computational failure updates procedure evidence. A wrong explanation may reveal a schema misconception. 
## Data collection
We should be able to produce a corpus of task targeting. We have a learner highlight and intent, generated candidates, acceptence/rejection/edits, prompt revisions, attempts with error patterns, culling or retention, delayed unseen transfer, and maybe even self reported authentic use outcome. We can have learner specific taste models with domain specific prompt generation policies. 

## Example user journeys
Internally, the system can preserve its existing loop:

**source → study map → attempt → feedback/tutor → updated evidence → next decision → later cold retrieval**.

But users should enter through the job they are trying to accomplish:

- **Learn this**
    
- **Prepare for something**
    
- **Fix this weakness**
    
- **Use this in a project**
    
- **Practice for a few minutes**
    
- **Return to something I abandoned**
    

LearnLoop can translate those ordinary intentions into sources, facets, capabilities, Learning Objects, Practice Items, goals, and evidence behind the scenes.

## Journey map

|Journey|What the user says|Product maturity|
|---|---|---|
|First useful session|“Help me start learning this chapter.”|Mostly supported|
|Quick insight capture|“This paragraph matters; help me keep it.”|High-priority extension|
|Full textbook/course|“Build me a coherent path through this material.”|Mostly supported|
|Exam preparation|“I need to be ready by September.”|Mostly supported|
|Recurring-error diagnosis|“Why do I keep getting these problems wrong?”|Engine largely supported; UX incomplete|
|Recall-to-transfer progression|“I remember it, but I cannot use it.”|Strong architectural fit|
|Tutor-to-memory|“That explanation finally made sense.”|Partially supported|
|Project-linked learning|“I need this concept for something I’m building.”|High-value extension|
|Multi-source reconciliation|“These books explain this differently.”|Strongly supported underneath|
|Three-minute session|“Give me one useful thing now.”|Small but important UX extension|
|Return after a hiatus|“I have not studied in three months.”|Important extension|
|Prompt maintenance|“This question is bad, but the idea matters.”|Important extension|
|Knowledge-garden review|“Help me clean up what I am learning.”|Primitives exist; UX opportunity|

---

# 1. The first useful session

### User story

A learner wants to relearn linear algebra from Axler. They have never used LearnLoop and do not yet understand what a vault, facet, or Learning Object is.

### Journey

1. They launch LearnLoop and choose **Learn from a source**.
    
2. They add the textbook PDF.
    
3. LearnLoop displays the chapter outline and extraction health.
    
4. They select Chapters 2–4 rather than ingesting the entire book.
    
5. LearnLoop asks:
    
    - What is your goal?
        
    - What level are you starting from?
        
    - Do you want computational fluency, proof fluency, intuition, or a mixture?
        
6. They choose:  
    **“I studied this before, but I want geometric intuition and enough computational fluency for machine learning.”**
    
7. LearnLoop previews the proposed study map in learner-facing terms:
    
    - major ideas;
        
    - expected prerequisites;
        
    - types of practice;
        
    - approximate study scope;
        
    - anything ambiguous or requiring confirmation.
        
8. The learner reviews only exceptions rather than manually approving every generated object.
    
9. LearnLoop gives them a five-minute cold baseline containing:
    
    - one definition or interpretation question;
        
    - one simple application;
        
    - one discrimination question.
        
10. The session ends with:
    

- what appears familiar;
    
- what remains uncertain;
    
- the next recommended session;
    
- one source section worth reading.
    

LearnLoop already supports importing multiple source types, selecting source scope, building study maps, and serving ordinary practice, repair, transfer, teach-back, and diagnostic work from the Today queue.

### North-star moment

The user answers their first meaningful question within ten minutes of installation. They never need to understand the internal schema before receiving value.

### Design implication

The first-run wizard should ask about **intent and material**, not architecture. “Create vault” can happen invisibly or be framed as “Choose where your learning data will live.”

---

# 2. Quick insight capture: “Learn this”

### User story

The learner is reading a blog post and encounters:

> Multiplication by a matrix can be understood as changing coordinates, applying a simpler transformation, and changing coordinates back.

They do not want to build an entire course. They simply want this idea to become part of how they think. 

### Journey

1. They highlight the paragraph and send it to LearnLoop through a browser extension, share sheet, paste action, or command palette.
    
2. LearnLoop preserves the surrounding source context.
    
3. It asks one question:
    
    **What should future-you be able to do with this?**
    
4. The learner chooses or writes:
    
    - recall the statement;
        
    - explain it intuitively;
        
    - recognize when it applies;
        
    - use it in a derivation;
        
    - remember the exact wording.
        
5. They choose **explain and apply**.
    
6. Before generating anything, LearnLoop asks them for their current interpretation:
    
    > “Diagonalization isolates independent directions, so changing to the eigenbasis makes the action easier to understand.”
    
7. LearnLoop proposes a small activity set:
    
    - explain why (A=PDP^{-1}) represents a change of coordinates;
        
    - identify what (P^{-1}), (D), and (P) do to a vector;
        
    - distinguish diagonalization from merely writing a matrix in a different notation;
        
    - apply the interpretation to a new (2\times2) matrix.
        
8. The learner accepts one or two activities, not an automatically generated twenty-card deck.
    
9. A first cold retrieval is scheduled.
    
10. After the cold answer, LearnLoop restores the exact source paragraph, the learner’s original interpretation, and any alternate explanation.
    

### North-star moment

An insight moves from “interesting thing I read” to “idea I can explain and use” with less than a minute of administrative work.

### Why this journey matters

This should be one of LearnLoop’s flagship experiences. It supports the lead-user need for situated, personally meaningful memory without forcing every encounter through full curriculum synthesis.

It also preserves the valuable generative act: the learner still states what the idea means to them before AI proposes practice.

---

# 3. Building a full course from several sources

### User story

The learner wants a self-directed probability course using:

- Ross for introductory exercises;
    
- a more rigorous text for theory;
    
- lecture videos for intuition;
    
- their own notes;
    
- a problem set.
    

### Journey

1. They create a subject called **Probability**.
    
2. They add each source to the library.
    
3. For each source, LearnLoop suggests—but does not silently decide—its role:
    
    - primary textbook;
        
    - alternate explanation;
        
    - lecture;
        
    - reference;
        
    - problem set;
        
    - exam.
        
4. The learner selects chapters and lecture units.
    
5. LearnLoop builds one study map rather than generating a separate deck for every source.
    
6. Duplicate formulations of the same idea attach to the same canonical facet.
    
7. The learner sees:
    
    - topics covered by multiple sources;
        
    - gaps no source covers well;
        
    - notation differences;
        
    - prerequisite relationships;
        
    - sources allowed to define claims;
        
    - sources allowed only to shape practice.
        
8. Initial practice determines where the learner should start.
    
9. Later, adding another source updates only the affected neighborhood of the map.
    
10. LearnLoop shows exactly what changed.
    

LearnLoop’s current source model already separates source identity, immutable revisions, extraction spans, source roles, scope, authority, and append behavior.

### North-star moment

The learner experiences multiple books as **several views of one body of knowledge**, rather than several duplicated card collections. This helps the learner take the best parts from each canonical source and also learn multiple interpretations/approaches to teaching 1 concept. 

### Design implication

The UI should emphasize:

> “You are adding another explanation of existing ideas.”

Not:

> “Generate another deck from this PDF.”

---

# 4. Honest exam preparation

### User story

A student has a linear algebra final in six weeks. They have lecture notes, a textbook, homework, and two past exams.

### Journey

1. They choose **Prepare for an exam**.
    
2. They provide:
    
    - exam date;
        
    - syllabus or topic list;
        
    - desired confidence or recall target;
        
    - available time per week.
        
3. They import notes, textbook sections, and past exams.
    
4. LearnLoop distinguishes:
    
    - explanatory sources;
        
    - practice sources;
        
    - held-out exam items;
        
    - historical exam results.
        
5. The learner creates a quarantined held-out pool that ordinary practice cannot leak into.
    
6. LearnLoop builds a coverage map:
    
    - covered and demonstrated;
        
    - covered but untested;
        
    - weak;
        
    - likely to decay before the exam;
        
    - absent from the current practice bank.
        
7. Daily sessions combine:
    
    - due memory work;
        
    - weak prerequisite repair;
        
    - exam-frontier practice;
        
    - method selection;
        
    - mixed-topic transfer.
        
8. Weekly, the learner takes a short calibration check.
    
9. LearnLoop freezes its prediction before revealing the result.
    
10. Afterward, it shows:
    
    - predicted performance;
        
    - demonstrated performance;
        
    - where confidence was justified;
        
    - where the system or learner was overconfident;
        
    - the next week’s revised plan.
        

Goals, recall targets, deadlines, and held-out exam pools are already part of LearnLoop’s documented journey. Held-out items remain excluded from ordinary practice so they can serve as honest measurements.

### North-star moment

The learner can distinguish:

- “The system thinks I am likely to succeed.”
    
- “I have directly demonstrated this under appropriate conditions.”
    

That distinction should be visible throughout exam prep.

---

# 5. Diagnosing a recurring mathematical error

### User story

The learner can solve ordinary linear equations but repeatedly fails eigenvector problems.

They answer (Av=\lambda v) incorrectly. A conventional system would mark the whole problem wrong and schedule it sooner.

### Journey

1. LearnLoop grades against a structured rubric:
    
    - interpret the eigenvector equation;
        
    - rearrange to ((A-\lambda I)v=0);
        
    - solve the resulting system;
        
    - enforce a nonzero solution;
        
    - interpret the eigenspace.
        
2. The first failure occurs when forming (A-\lambda I).
    
3. The system does **not** lower every prerequisite and capability.
    
4. It identifies several plausible explanations:
    
    - forgot what (\lambda I) means;
        
    - matrix subtraction error;
        
    - does not understand why singularity is required;
        
    - understands components but cannot coordinate them.
        
5. LearnLoop gives two bounded diagnostic probes:
    
    - form (A-3I) without solving anything;
        
    - explain why a nonzero null-space vector requires (\det(A-\lambda I)=0).
        
6. The first succeeds; the second fails.
    
7. LearnLoop updates the likely explanation: the issue is conceptual coordination, not matrix arithmetic.
    
8. The repair sequence becomes:
    
    - a visual explanation of null spaces and singularity;
        
    - one worked example;
        
    - one completion problem;
        
    - one near-transfer problem;
        
    - a later cold whole-task problem.
        
9. Once the learner succeeds on sufficiently distinct unassisted surfaces, the error hypothesis becomes resolved rather than merely disappearing from the recent-error list.
    

LearnLoop’s current evidence logic already supports first-error localization, marking downstream criteria unassessable, and creating unresolved-cause factors instead of penalizing every possible target.

### North-star moment

The learner feels:

> “It found the reason I was stuck,”

rather than:

> “It gave me the same problem again.”

### This may be LearnLoop’s strongest differentiated journey

Most learning tools schedule answers. LearnLoop can schedule **experiments about the learner**.

---

# 6. Moving from recall to flexible use

### User story

The learner can correctly define covariance and identify its formula, but they cannot explain its geometric meaning or recognize how it relates to PCA.

### Journey

1. LearnLoop notices strong evidence for retrieval but weak or absent evidence for:
    
    - schema interpretation;
        
    - method selection;
        
    - transfer;
        
    - coordination with eigenvectors.
        
2. Instead of repeating the formula, it advances the activity type.
    
3. The learner receives:
    
    - describe the covariance ellipse;
        
    - predict how covariance changes after rotating the data;
        
    - compare two datasets with the same marginal variance but different covariance;
        
    - explain why PCA looks at eigenvectors of the covariance matrix;
        
    - choose between two candidate methods for a new problem.
        
4. The learner can see a capability profile:
    
    |Capability|State|
    |---|---|
    |Recall definition|Demonstrated|
    |Compute simple covariance|Demonstrated|
    |Interpret geometry|Developing|
    |Select PCA-related method|Untested|
    |Transfer to unfamiliar representation|Weak evidence|
    
5. Once a capability is stable, LearnLoop uses maintenance-level retrieval rather than continuing to drill it heavily.
    
6. New practice targets the untested or weak dimensions.
    

### North-star moment

The learner sees that “knowing covariance” is not one number.

LearnLoop’s model already treats facets and capabilities separately, and it prevents retrieval evidence from certifying method selection or component knowledge from certifying integration.

### Design implication

The product should expose a visible learning arc:

**retrieve → explain → distinguish → vary → apply → coordinate → teach/create**

The underlying engine is already much closer to supporting this than a conventional flashcard system.

---

# 7. A tutor conversation becomes durable knowledge

### User story

During a problem, the learner asks:

> “Why does an orthogonal matrix preserve length?”

The tutor gives an explanation that finally makes the idea click.

### Journey

1. The learner asks the tutor from within the attempt.
    
2. LearnLoop grounds the answer in the source and current problem.
    
3. Because help was used, the current result receives reduced or no unassisted demonstration credit.
    
4. At the end of the exchange, LearnLoop offers:
    
    **Keep this insight?**
    
    - save as note;
        
    - turn into future practice;
        
    - attach to the current idea;
        
    - discard.
        
5. The learner selects **save and practice later**.
    
6. LearnLoop proposes:
    
    - a concise learner-owned note;
        
    - the underlying facet;
        
    - one future cold explanation prompt;
        
    - one application prompt.
        
7. The learner edits the note into their own language.
    
8. The tutor exchange remains linked as provenance but is not shown during the future cold attempt.
    
9. Days later, the learner must explain:  
    [  
    |Qx|^2=x^TQ^TQx=x^Tx.  
    ]
    
10. After answering, they can reopen the original conversation and source section.
    

The current feedback journey already allows the learner to open source spans, ask the tutor in context, save useful exchanges, add repair notes, and perform primed retries.

### North-star moment

A valuable AI conversation does not vanish into chat history. It becomes part of the learner’s durable conceptual system.

---

# 8. Project-linked, just-in-time learning

### User story

The learner is implementing PCA in a notebook. They can call the library function but realize they do not fully understand why centering is necessary.

### Journey

1. They create or open a project goal:  
    **Implement PCA from scratch and explain each step.**
    
2. From the notebook or LearnLoop, they capture:
    
    - the relevant code;
        
    - the confusion;
        
    - the project context.
        
3. LearnLoop retrieves the relevant idea page and asks whether they want:
    
    - a quick explanation;
        
    - a prerequisite repair;
        
    - a worked derivation;
        
    - a practice problem.
        
4. The learner studies centering and covariance just in time.
    
5. They complete the implementation.
    
6. LearnLoop records the project use as application evidence with appropriate caveats:
    
    - tools and sources were available;
        
    - the work may have been scaffolded;
        
    - it is not equivalent to a cold test.
        
7. It extracts a reusable lesson:  
    **Without centering, the second-moment matrix reflects position relative to the origin rather than variation around the mean.**
    
8. Several days later, LearnLoop asks a cold transfer question using a different dataset.
    
9. The project artifact remains linked to the idea as an example of real use.
    

### North-star moment

Study serves a real act of creation rather than becoming a separate hobby of maintaining a study system.

### Design implication

Goals should support not only dates and target recall but also **project outcomes**:

- implement;
    
- write;
    
- explain;
    
- reproduce;
    
- analyze;
    
- present;
    
- perform.
    

---

# 9. Reconciling multiple explanations and notation systems

### User story

The learner studies diagonalization from Axler, Strang, and a lecture video. Each source uses different notation and emphasizes a different intuition.

### Journey

1. The learner adds the new sources to the existing linear algebra source set.
    
2. LearnLoop recognizes that all three discuss the same underlying facets.
    
3. It attaches:
    
    - Axler’s abstract operator framing;
        
    - Strang’s geometric eigenvector framing;
        
    - the video’s animated coordinate-change explanation.
        
4. It detects notation differences:
    
    - (PDP^{-1});
        
    - (S\Lambda S^{-1});
        
    - basis-change language.
        
5. The learner confirms a notation map.
    
6. LearnLoop does not create three separate “definition of diagonalization” objects.
    
7. Future practice deliberately alternates representations:
    
    - explain in operator language;
        
    - interpret geometrically;
        
    - translate between notations.
        
8. When sources genuinely disagree, LearnLoop presents the conflict and supporting spans rather than silently blending them.
    
9. The learner can choose a preferred explanation without deleting the alternatives.
    

### North-star moment

The learner becomes robust to differences in notation and framing rather than memorizing one source’s surface form.

---

# 10. The three-minute session

### User story

The learner is waiting for a train and has three minutes.

### Journey

1. They open LearnLoop and tap **One useful item**.
    
2. There is no required setup form.
    
3. LearnLoop chooses one item based on:
    
    - what is meaningfully due;
        
    - active goals;
        
    - open errors;
        
    - expected session length;
        
    - whether the item can be completed cleanly in three minutes.
        
4. The learner answers.
    
5. They receive concise feedback.
    
6. The app offers:
    
    - stop;
        
    - do one repair;
        
    - continue for five more minutes.
        
7. Stopping after one item is treated as a completed session, not a broken streak or failed plan.
    

The current scheduler already accepts available minutes and energy, adjusts queue size, and alters short-session behavior.

### North-star moment

LearnLoop remains useful at the scale of ordinary life rather than requiring a formal study ritual every time.

### Suggested session entrances

- **One item**
    
- **Three minutes**
    
- **Ten minutes**
    
- **Focused repair**
    
- **Deep study**
    
- **Continue project**
    

Sleep and energy can still improve planning, but should be optional for very short sessions.

---

# 11. Returning after a three-month hiatus

### User story

The learner used LearnLoop heavily, stopped for three months, and now sees hundreds of nominally overdue items.

A conventional SRS presents a punishing backlog.

### Journey

1. LearnLoop welcomes them back without showing a giant red count.
    
2. It asks:
    
    - Are your old goals still relevant?
        
    - Which subjects do you want to resume?
        
    - How much time do you want to spend this week?
        
3. The learner chooses only linear algebra and archives the old Korean goal.
    
4. LearnLoop gives a small re-entry assessment sampled across:
    
    - high-value concepts;
        
    - previously demonstrated capabilities;
        
    - known historical weaknesses.
        
5. It uses present evidence rather than assuming every overdue item deserves immediate review.
    
6. The system creates three groups:
    
    - retained well;
        
    - likely recoverable with one reminder;
        
    - genuinely weak or forgotten.
        
7. Low-value prompts are retired or deferred.
    
8. The learner receives a manageable seven-day re-entry plan.
    
9. Old history remains intact; the schedule is reconstituted around current priorities.
    

### North-star moment

The user feels invited back rather than punished for leaving.

### Why this matters

A long-term learning product should optimize not only for streak continuation, but also for **graceful resumption**. This is likely a major retention feature.

---

# 12. Repairing or retiring a bad prompt

### User story

The learner answers an item correctly but realizes they memorized the wording rather than the idea.

### Journey

1. In feedback, they select:
    
    **I knew the prompt, not the concept.**
    
2. LearnLoop opens the underlying idea page.
    
3. It shows:
    
    - the current Practice Item;
        
    - sibling items;
        
    - correlation or surface group;
        
    - capabilities the item claims to assess;
        
    - prior attempts.
        
4. The learner chooses:
    
    - rewrite wording;
        
    - replace with application;
        
    - generate a counterexample task;
        
    - split an overloaded item;
        
    - merge with a duplicate;
        
    - retire the item;
        
    - keep the idea but stop scheduling this surface.
        
5. LearnLoop preserves:
    
    - the underlying facet;
        
    - source provenance;
        
    - prior evidence;
        
    - the fact that this item was retired.
        
6. A replacement activity enters the proposal queue.
    
7. The retired item no longer creates review burden.
    

Other useful maintenance signals would include:

- too trivial;
    
- ambiguous;
    
- answer depends on missing context;
    
- tests the wrong capability;
    
- repeated near-clone;
    
- no longer relevant;
    
- explanation is bad;
    
- I do not care enough to retain this;
    
- this should be reference material, not memorized material.
    

### North-star moment

The learner can say:

> “This instrument is bad, but the idea is still valuable.”

That is only possible because LearnLoop can make the idea durable and the Practice Item disposable.

---

# 13. The weekly knowledge-garden review

### User story

A serious learner has used LearnLoop for six months. The system now contains hundreds of ideas, notes, errors, sources, and activities.

### Journey

Once a week or month, LearnLoop offers a ten-minute maintenance review:

1. unresolved source conflicts;
    
2. proposed duplicate facets;
    
3. stale or repeatedly skipped prompts;
    
4. ideas without meaningful practice;
    
5. practice items without clear source grounding;
    
6. goals no longer receiving attention;
    
7. recurring errors that may need a better explanation;
    
8. mastered low-priority material consuming excessive review time;
    
9. notes worth converting into practice;
    
10. concepts that have become relevant to a current project.
    

The learner handles only a few high-value maintenance decisions. LearnLoop performs safe mechanical cleanup automatically and preserves a rollback trail.

### North-star moment

The system becomes more coherent over time rather than accumulating endless generated debris.

---

# Domain-specific variants

## Research-paper journey

A learner imports a paper and chooses **Understand and critique**, not merely “memorize.”

LearnLoop creates a map of:

- central claims;
    
- assumptions;
    
- method components;
    
- evidence;
    
- limitations;
    
- comparison points;
    
- equations worth reconstructing.
    

The learning sequence might be:

1. state the paper’s problem;
    
2. reconstruct the proposed method;
    
3. explain why each component is needed;
    
4. identify assumptions;
    
5. predict a failure mode;
    
6. compare with a later paper;
    
7. design an ablation or replication.
    

When another paper is added, LearnLoop attaches confirmations, refinements, and contradictions rather than generating a disconnected new deck.

## Mathematical-proof journey

A learner studies a theorem.

The progression becomes:

1. retrieve the theorem statement;
    
2. explain what it means geometrically;
    
3. identify prerequisite lemmas;
    
4. predict the proof strategy;
    
5. reconstruct a missing step;
    
6. reconstruct the whole proof;
    
7. identify where each assumption is used;
    
8. remove an assumption and find a counterexample;
    
9. apply the proof technique to a nearby theorem.
    

This is much closer to proof fluency than memorizing the final proof line by line.

## Language-from-real-life journey

The learner encounters a Korean phrase in a real conversation.

They capture:

- the phrase;
    
- who said it;
    
- what was happening;
    
- pronunciation or audio;
    
- their attempted interpretation.
    

LearnLoop progresses through:

1. comprehension in original context;
    
2. comprehension without context;
    
3. production;
    
4. grammatical variation;
    
5. use in a short dialogue;
    
6. recognition in a new speaker’s phrasing.
    

The exact original situation remains available after cold practice because it is part of why the phrase was memorable.

## VOD or motor-skill journey

After dance practice or an Overwatch match, the learner marks a timestamp:

> “I moved too early because I reacted to the tank rather than watching the opposing cooldown.”

LearnLoop captures:

- situation;
    
- cue;
    
- decision;
    
- observed error;
    
- intended response;
    
- drill.
    

Before the next session, it asks the learner to reconstruct the cue and plan. Afterward, the learner records whether the cue appeared and whether they acted correctly. Automated video analysis can come later; the useful journey can begin with manual timestamped reflection.

---

# The four flagship journeys I would prioritize

## 1. Learn this

Turn one meaningful source passage, note, or conversation into durable, contextual practice with minimal friction.

## 2. Fix this

Use bounded diagnostic probes to identify why the learner is failing and choose a targeted repair.

## 3. Use this

Move beyond retrieval into projects, transfer, method selection, explanation, and creation.

## 4. Return to this

Help the learner resume after days or months without backlog punishment.

The existing “build a study map from a source” journey remains important, but these four give LearnLoop a stronger identity than “AI-generated adaptive courseware.”

# A possible home screen organized around journeys

Instead of leading with implementation nouns, the primary actions could be:

### Continue

**Practice what matters today**  
One item, short session, or full session.

### Learn

**Learn something from a source**  
Capture one insight or build a complete study map.

### Repair

**Work on something I keep getting wrong**  
Open errors, misconceptions, and targeted repair plans.

### Apply

**Use knowledge in a project or challenge**  
Link learning to code, writing, research, exams, or performance.

### Review

**See what I know and maintain my learning system**  
Inspect capabilities, evidence, prompts, sources, and goals.

Underneath, all of these can reuse the same LearnLoop primitives. The primary UX distinction is **why the user entered the app and what a successful exit looks like**.


## An agent's approach to probe EIG changes
Yes. A fixed hypothesis set is necessary for valid EIG calculations, but a permanently closed hypothesis ontology would be unrealistic. The right design is:

> **Lock hypotheses within a diagnostic episode, but allow controlled, versioned expansion between diagnostic blocks or episodes.**

Probe EIG answers, “Which observation best separates the explanations currently under consideration?” It cannot discover an explanation absent from the model. MCTS does not automatically fix that either; it must be given an explicit **expand the model class** action.

The current LearnLoop implementation already has the beginnings of this design:

- Each episode receives a locked hypothesis-set snapshot.
    
- Every set contains executable `other_or_unknown` mass.
    
- At block end, sufficiently large `other_or_unknown` mass creates an open-set review need without mutating the active set.
    
- Newly active misconceptions can enter the next freshly instantiated hypothesis set.
    

What is missing is the explicit transition from that open-set need to a new executable hypothesis card and successor episode.

# The proposed architecture

Think of three separate objects.

## 1. Hypothesis card

A reusable, versioned explanation of a possible learner state.

For example:

> The learner remembers that eigenvalue problems require a singular matrix but does not understand the equivalence between  
> (Av=\lambda v) and ((A-\lambda I)v=0).

A hypothesis card should contain more than prose. It must be executable:

```python
class HypothesisCard:
    id: str
    version: int

    # Semantic identity
    label: str
    learner_model_claim: str
    scope: HypothesisScope
    applicability_conditions: list[str]

    # What distinguishes it
    predicted_observations_by_probe_family: dict[str, OutcomeDistribution]
    signature_error_types: list[str]
    cannot_separate_from: list[str]
    disconfirming_observations: list[str]

    # What to do if supported
    instructional_actions: list[str]
    candidate_practice_families: list[str]

    # Governance
    status: str  # proposed | provisional | active | trusted | retired | merged
    provenance: list[str]
    discovery_evidence_ids: list[str]
    authoring_inputs_hash: str
```

This is analogous to LearnLoop’s existing versioned probe family/card design, where the durable measurement object is the family/card binding rather than the generated surface instance.

## 2. Hypothesis-set snapshot

A particular episode’s bounded set of instantiated cards and priors:

[  
H^v={h_1,h_2,\ldots,h_k,h_\bot},  
]

where (h_\bot) is `other_or_unknown`.

This object remains immutable. Every committed probe records:

- the exact hypothesis-set ID;
    
- the exact card versions;
    
- the posterior before selection;
    
- the likelihood matrix used;
    
- the expected EIG;
    
- the generated or existing instrument version.
    

That makes replay possible even after the ontology grows.

## 3. Diagnostic episode

The episode is a measurement period over one locked hypothesis set and one learner-state segment.

A new card does not get inserted into the middle of that episode. Instead, LearnLoop creates:

[  
E_1(H^v)  
\longrightarrow  
E_2(H^{v+1}),  
]

with lineage explaining that (E_2) is an open-set expansion of (E_1).

# How a missing hypothesis is detected

There should be several model-misspecification signals.

## Open-set posterior mass

The primary signal is:

[  
P(h_\bot\mid D) > \tau_{\text{open}},  
]

where the current default threshold is 0.35.

This means the observed pattern fits the broad unknown model better than the named alternatives.

## Low posterior predictive probability

Even if `other_or_unknown` does not win, the entire current hypothesis set may assign very low probability to an observation:

# [  
P(o\mid H^v,D)

\sum_{h\in H^v}P(o\mid h,q)P(h\mid D).  
]

Repeated highly surprising observations suggest that the model class is inadequate, not merely uncertain.

## Repeated unexplained error signature

Suppose several distinct items produce the same first divergent step, but no active card predicts it. This is stronger evidence of a missing mechanism than a single strange answer.

## Failed intervention

LearnLoop diagnoses (h_i), delivers the corresponding practice family, and the learner continues making the same error on appropriately varied surfaces.

That can mean:

- the intervention was poor;
    
- the learner did not engage;
    
- or the diagnosis itself was wrong.
    

After ruling out the first two, repeated repair failure should trigger hypothesis expansion.

## Learner-supplied explanation

The learner might say:

> “I did not confuse the conditional probabilities. I interpreted ‘positive’ as the actual condition rather than the test result.”

That proposed explanation should enter the candidate pipeline with bounded trust rather than being either accepted as fact or ignored.

## New semantic information

A new source, tutor trace, proof step, code execution trace, or domain-specific observation might reveal a possible misconception that was not known when the original study map was synthesized.

# The expansion pipeline

When the open-set trigger fires, LearnLoop should not immediately ask an LLM to invent one hypothesis and install it. It should use a retrieve–generate–validate–rerank pipeline.

## Step 1: Build a residual-evidence dossier

The author receives:

- the LO, canonical facets, capabilities, and dependencies;
    
- the locked hypothesis set and posterior;
    
- raw learner responses;
    
- rubric evidence and first invalid steps;
    
- probe contexts and surface families;
    
- error signatures;
    
- predictions made by existing hypotheses;
    
- the discrepancy between predictions and observations;
    
- learner self-explanations;
    
- related known misconceptions and confusable concepts;
    
- source spans establishing the correct domain semantics.
    

The important input is not merely “the learner got this wrong.” It is:

> “Here are the exact response patterns that the existing model failed to explain.”

## Step 2: Retrieve before generating

LearnLoop should search:

1. existing active or resolved misconception cards;
    
2. cards attached to related facets or prerequisite LOs;
    
3. domain-level hypothesis templates;
    
4. cards with similar error signatures;
    
5. semantically similar but differently worded hypotheses.
    

The current hypothesis builder already draws from authored confusables and active misconceptions.

Only if retrieval does not adequately explain the residual should the diagnostic author generate new candidates.

## Step 3: Generate several candidate cards

This is where BED-LLM-style diagnostic authoring belongs.

The model should generate perhaps three candidate explanations, not one:

- a narrow mechanism hypothesis;
    
- a compositional or coordination hypothesis;
    
- a representation or parsing hypothesis.
    

Each candidate must state:

- what the learner believes or fails to represent;
    
- which evidence supports that explanation;
    
- what evidence would falsify it;
    
- how it differs from the current hypotheses;
    
- which probe families could distinguish it;
    
- which response patterns it predicts;
    
- what instructional intervention would follow.
    

The LLM proposes; local code decides whether a card is admissible.

## Step 4: Validate candidates locally

A candidate hypothesis should fail admission unless it passes several gates.

### Semantic validity

It must correspond to a coherent misconception, missing relation, capability deficit, or coordination failure—not an unsupported personality claim such as “the learner is careless.”

### Novelty

It must not merely paraphrase an existing card.

### Identifiability

There must be at least one feasible probe for which the candidate predicts a materially different outcome distribution from another plausible hypothesis:

[  
D_{\mathrm{JS}}  
\left(  
P(O\mid h_{\text{new}},q),  
P(O\mid h_i,q)  
\right)

> \epsilon.  
> ]

A hypothesis that cannot be distinguished from any existing hypothesis should be merged, refined, or left under `other_or_unknown`.

### Falsifiability

The card must identify observations that would lower its probability.

### Action relevance

Supporting the card should change what LearnLoop does next. If two hypotheses imply exactly the same probes and exactly the same practice family, differentiating them may have little decision value.

### Instrument feasibility

At least one current probe family must be able to elicit the distinction—or LearnLoop must also author a new instrument card.

### Simulation gates

The card and its instruments should be tested with:

- a planted learner exhibiting the candidate state;
    
- clean learners who should not be diagnosed with it;
    
- nearby competing hypotheses;
    
- noisy and contaminated answers.
    

LearnLoop already validates probe policy end to end against planted behavioral types and checks whether the episode selects the matching instructional action.

# How posterior mass transfers to the expanded set

Suppose the original posterior is:

[  
P(h_1)=0.20,\quad  
P(h_2)=0.25,\quad  
P(h_3)=0.10,\quad  
P(h_\bot)=0.45.  
]

LearnLoop generates two plausible candidates (c_1,c_2).

The conservative rule is to split only the existing open-set mass:

# [  
H^{v+1}

{h_1,h_2,h_3,c_1,c_2,h_\bot}.  
]

For old named hypotheses:

[  
P_{v+1}(h_i)=P_v(h_i).  
]

For new candidates:

[  
P_{v+1}(c_j)=P_v(h_\bot)\rho_j,  
]

and retain some residual open-set mass:

[  
P_{v+1}(h_\bot)=P_v(h_\bot)\rho_\bot,  
]

where

[  
\sum_j\rho_j+\rho_\bot=1.  
]

For example:

[  
\rho_1=0.55,\quad \rho_2=0.25,\quad \rho_\bot=0.20,  
]

giving:

[  
P(c_1)=0.2475,\quad  
P(c_2)=0.1125,\quad  
P(h_\bot)=0.09.  
]

## Avoid double-using discovery evidence

The observations used to invent (c_1) and (c_2) cannot also be treated as clean confirmatory evidence for them.

Otherwise the system performs:

1. inspect data;
    
2. invent an explanation that fits it;
    
3. use the same data to claim strong posterior support.
    

That is diagnostic overfitting.

Historical observations can be used to:

- rank candidates;
    
- allocate the old `other` mass conservatively;
    
- reject candidates that plainly do not fit;
    
- identify useful probes.
    

But the card should require **prospective confirmation** on later probes.

One implementation is a tempered retrospective score:

[  
\rho_j  
\propto  
\exp(\tau s_j),  
\qquad 0\leq\tau\leq0.3,  
]

where (s_j) measures retrospective compatibility. The small temperature prevents the discovery evidence from producing an overconfident prior.

The card might carry:

```text
status = provisional
prospective_confirmations_required = 2
independent_surface_groups_required = 2
```

# How EIG works after expansion

Once (H^{v+1}) is created, LearnLoop recompiles candidate instruments against the new set and selects:

# [  
q^*

\arg\max_q  
I(H^{v+1};O_q\mid D)  
]

or uses predictive EIG when the required held-out target instruments exist.

The current implementation intentionally treats predictive EIG and hypothesis EIG as alternative objectives rather than adding them together.

That should remain true after expansion:

- **Hypothesis EIG** asks which probe best identifies the explanation.
    
- **Predictive EIG** asks which probe best improves predictions on target instruments.
    
- The configured policy selects one objective and logs the other for audit.
    
- Expansion changes the model against which either objective is computed.
    

If no existing PI distinguishes the new card, the system authors new **probe instances or instrument cards**, but those instruments must discriminate the newly expanded set. Hypothesis generation and item generation should remain distinct services.

# How this fits into MCTS

The critical point is:

> Do not let the LLM invent arbitrary hypotheses inside every MCTS rollout.

That would produce an unbounded branching factor, non-replayable transitions, and constantly changing observation likelihoods.

Instead, use a two-level architecture.

## Inner controller: fixed-model probe selection

For a fixed hypothesis-set version (H^v):

- greedy EIG or conditional block EIG selects probes;
    
- posterior updates are ordinary Bayesian updates;
    
- likelihoods are stable;
    
- MCTS may look ahead over bounded sequences of existing validated actions.
    

The current implementation already distinguishes sequential posterior-conditioned selection from precommitted joint conditional-EIG blocks.

## Outer controller: model-space decisions

At diagnostic block boundaries, the controller chooses among macro-actions:

```text
PROBE_MORE
EXPAND_HYPOTHESIS_SPACE
AUTHOR_MISSING_INSTRUMENT
BEGIN_PRACTICE_FAMILY
CONVERT_TO_TUTORING
STOP_DIAGNOSIS
```

`EXPAND_HYPOTHESIS_SPACE` is therefore an explicit MCTS action, not an implicit side effect of a probe outcome.

A planner state might be:

[  
s=  
(H^v,b^v,z_{\text{segment}},B,D,Q,C),  
]

where:

- (H^v): current hypothesis-set version;
    
- (b^v): posterior over that set;
    
- (z_{\text{segment}}): learner-state segment;
    
- (B): remaining time and observation budget;
    
- (D): observations collected;
    
- (Q): available validated probes;
    
- (C): current candidate-card cache and open-set indicators.
    

The possible actions are:

[  
a\in  
{  
\operatorname{probe}(q),  
\operatorname{expand},  
\operatorname{authorInstrument},  
\operatorname{practice}(f),  
\operatorname{stop}  
}.  
]

## Value of the expansion action

Conceptually:

# [  
V_{\text{expand}}(s)

## \mathbb{E}_{C\sim G(D,H^v)}  
\left[  
V^*(H^{v+1},b^{v+1},C)  
\right]

## c_{\text{author}}

c_{\text{delay}}.  
]

The planner compares that with:

- the value of asking another probe under the current model;
    
- the value of starting instruction now;
    
- the cost of further diagnostic burden.
    

Expansion becomes attractive when:

- `other_or_unknown` has substantial mass;
    
- remaining known hypotheses imply different interventions;
    
- another current-model probe has low information value;
    
- a newly authored hypothesis is likely to change the instructional decision.
    

## Progressive widening

MCTS should initially treat `expand` as one abstract macro-action.

Only when that action is selected or sufficiently visited should LearnLoop materialize a bounded number of candidate cards. For example:

1. Retrieve up to five related cards.
    
2. Generate at most three new candidates.
    
3. Admit at most two provisional cards.
    
4. Rebuild the set.
    
5. Re-root the search tree.
    

This is a form of progressive widening: the hypothesis branch expands only when evidence and planning value justify the additional complexity.

## Re-root after expansion

Once (H^{v+1}) exists, the old tree’s values are not directly valid because:

- the belief-state dimension changed;
    
- observation likelihoods changed;
    
- probe rankings changed;
    
- terminal instructional decisions may have changed.
    

Therefore:

> Preserve the old tree for audit, but re-root planning at the new hypothesis-set snapshot.

Statistics for unchanged instruments can warm-start heuristics, but old node (Q)-values should not be treated as exact values under the new model.

# Measurement and learning must remain separate

MCTS may eventually plan both probes and practice interventions, but they have different transition semantics.

## Probe transition

A probe is intended to reveal the current state:

# [  
b_{t+1}

\operatorname{BayesUpdate}(b_t,o_t,q_t).  
]

The learner state is assumed approximately stationary during the diagnostic block.

## Practice transition

Practice is intended to change the state:

[  
z_{t+1}  
\sim  
P(z_{t+1}\mid z_t,f_t),  
]

where (f_t) is the selected practice family.

Once practice or explanatory feedback begins:

- close the diagnostic state segment;
    
- retain the old posterior as a diagnosis of the pre-instruction state;
    
- begin a new learner-state segment;
    
- later use cold probes to measure whether the boundary moved.
    

This prevents MCTS from confusing:

> “The learner answered differently because our hypothesis was wrong”

with:

> “The learner answered differently because we just taught them.”

# Recommended card lifecycle

A newly authored hypothesis should not immediately become a permanent diagnosis.

```text
proposed
   ↓ structural + semantic validation
provisional
   ↓ prospective probe support
episode_supported
   ↓ recurrence across independent surfaces or human review
active_registry_card
   ↓ repeated real-world calibration
trusted
```

Possible exits:

```text
provisional → rejected
active → merged_into_existing
active → resolved
trusted → retired
```

A card may be:

- **episode-local**, explaining one unusual response;
    
- **LO-local**, recurring for one Learning Object;
    
- **facet-level**, reusable across several LOs;
    
- **domain-template**, such as “executes procedure but cannot select it”;
    
- **cross-domain mechanism**, such as “uses a familiar surface cue instead of checking applicability conditions.”
    

Promotion should depend on recurrence and prospective evidence, not merely confidence from the authoring model.

# Concrete example

Assume an eigenvector episode contains:

- `unfamiliar`;
    
- `recall_without_mechanism`;
    
- `procedure_without_selection`;
    
- `robust_initial_grasp`;
    
- `other_or_unknown`.
    

The learner:

1. correctly defines an eigenvector;
    
2. correctly computes (A-\lambda I);
    
3. correctly solves a null-space system;
    
4. repeatedly says that (\det(A-\lambda I)=0) is “the definition of eigenvector”;
    
5. cannot derive ((A-\lambda I)v=0) from (Av=\lambda v).
    

No named hypothesis cleanly predicts this pattern. `other_or_unknown` rises above the trigger.

LearnLoop retrieves existing cards and finds nothing sufficiently close. The authoring pipeline proposes:

> **Rule without equivalence model:** The learner remembers the determinant/singularity procedure but does not represent why the eigenvector equation is equivalent to a null-space equation.

It predicts:

- success on computing (A-\lambda I);
    
- success on determinant procedures;
    
- failure on bidirectional equation translation;
    
- failure on explaining why a nonzero null-space vector is an eigenvector;
    
- improvement from an equivalence-bridge practice family.
    

The card passes identifiability because a translation probe distinguishes it from:

- `recall_without_mechanism`, which predicts weaker definition recall;
    
- `procedure_without_selection`, which predicts uncertainty about when to invoke the eigenvector procedure;
    
- `robust_initial_grasp`, which predicts successful translation.
    

A successor episode is created. The old `other` mass is partially assigned to the provisional card. EIG chooses:

> Given ((A-4I)v=0) and (v\neq0), derive what (Av) equals and explain every step.

The learner fails in the predicted manner. On a second, surface-varied prospective probe, the same signature appears.

The hypothesis becomes episode-supported, and the planner selects the **equivalence bridge** practice family rather than:

- definition retrieval;
    
- matrix subtraction drills;
    
- generic full eigenvector problems.
    

After instruction, LearnLoop starts a new learner-state segment and later cold-tests the same relationship in unfamiliar notation.

# What I would change in the current implementation

The existing `open_set_misconception_review` need is the correct entry point. I would extend it with:

```text
hypothesis_cards
hypothesis_card_versions
hypothesis_set_members
hypothesis_set_lineage
hypothesis_authoring_runs
hypothesis_discovery_evidence
hypothesis_validation_results
```

And add a typed transition:

```python
OpenSetTransition(
    source_episode_id=...,
    source_hypothesis_set_id=...,
    residual_evidence_ids=[...],
    action="expand_hypothesis_space",
    successor_episode_id=...,
    successor_hypothesis_set_id=...,
)
```

The runtime flow becomes:

```text
fixed-set probe block
        ↓
posterior + open-set/model-fit test
        ↓
continue probing ────────────────┐
        or                       │
open-set expansion need          │
        ↓                        │
retrieve → generate → validate   │
        ↓                        │
new provisional cards            │
        ↓                        │
successor hypothesis-set snapshot│
        ↓                        │
re-root EIG/MCTS  ←──────────────┘
        ↓
prospective confirmation
        ↓
highest-gain practice family
        ↓
new state segment + later cold probe
```

The central invariant should be:

> **Hypothesis sets are immutable measurement snapshots; the hypothesis ontology is open and evolves through versioned successor sets.**

That gives LearnLoop both properties it needs: statistically coherent probe EIG and realistic open-world diagnosis.



## Agents take

## Verdict
 
 
  spec_new_improvements_v2.md has the right product identity: LearnLoop should be an evidence-driven practice system that measures,
  diagnoses, teaches, and cold-reassesses—not a flashcard scheduler. Its strongest decisions are the separation of evidence from
  predictions, immutable diagnostic episodes, disposable activity surfaces, reading-first ingestion, and deferring MCTS.
 
 
  I would not freeze the architecture yet. Four parts need revision:
 
 
  1. The durable learner object should be a practice commitment, not a PI, card, LO, or canonical facet.
  2. Worked examples and other teaching experiences require a first-class instructional activity purpose, alongside diagnostic and
     practice families.
 
 
  3. Capability, task complexity, transfer distance, representation, scaffolding, and constraints must remain separate dimensions—not
     one “depth ladder.”
 
 
  4. Probe selection should maximize decision value under model uncertainty, not raw EIG from uncertain hand-authored likelihoods.
 
 
  I evaluated the requested Andy document under its actual filename, spec_andymatusnotes.md:1.
 
 
  
 ## Decisions to keep, revise, or reject
  
  
    v2 choice                                              Verdict                 Recommendation
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Measure → diagnose → teach → cold reassess             Keep                    This is the correct north star.
   ─────────────────────────────────────────────────────  ──────────────────────  ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    Knowledge / learner / activity planes                  Keep                    Rename the knowledge plane to “source assertions and reviewed domain model”; it does not contain unquestionable truth.
   ─────────────────────────────────────────────────────  ──────────────────────  ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    Shared probe/PI substrate with no role transitions     Keep                    Extend the purposes to diagnostic, instructional, practice, and assessment.
   ─────────────────────────────────────────────────────  ──────────────────────  ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    One familiarity namespace                              Keep                    Make it global across families, not merely a family-local cap.
   ─────────────────────────────────────────────────────  ──────────────────────  ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    Practice card + rotating surfaces                      Revise                  Put learner intent and scheduling above cards; keep card state for psychometrics and script familiarity.
   ─────────────────────────────────────────────────────  ──────────────────────  ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    FSRS state on the practice card                        Revise                  FSRS is appropriate for stable memory traces, not automatically for variable complex tasks.
   ─────────────────────────────────────────────────────  ──────────────────────  ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    “Depth ladder = capability vocabulary”                 Reject                  These are multiple orthogonal axes.
   ─────────────────────────────────────────────────────  ──────────────────────  ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    Greedy EIG within measure mode                         Revise                  Use robust EIG initially, progressing to expected value of sample information.
   ─────────────────────────────────────────────────────  ──────────────────────  ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    Thin scored outer mode controller                      Revise                  Do not compare entropy, FSRS risk, and guessed learning gain using arbitrary weights.
   ─────────────────────────────────────────────────────  ──────────────────────  ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    Boundary as derived view                               Keep                    Separate historical evidence from current-readiness prediction and uncertainty.
   ─────────────────────────────────────────────────────  ──────────────────────  ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    Reading-first, demand-paged ingestion                  Keep                    This is likely the best product-facing direction in the document.
   ─────────────────────────────────────────────────────  ──────────────────────  ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    Immutable hypothesis sets with successor lineage       Keep                    This is the correct open-world contract.
   ─────────────────────────────────────────────────────  ──────────────────────  ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    No MCTS now                                            Keep                    Reconsider only after a calibrated rollable learner model exists.
   ─────────────────────────────────────────────────────  ──────────────────────  ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    Simulation as the “no uncalibrated knobs” criterion    Reject as sufficient    Simulation proves that a mechanism reacts; it does not establish that its numbers match learners.
  
  
   ## Recommended durable product model
  
  
   Andy’s central insight is stronger than “families generate varied prompts”: the thing the learner cares about must exist independently of its prompts. His notes explicitly describe the emotional mismatch caused by forcing an interesting thing into a task-shaped object
   spec_andymatusnotes.md:37 and spec_andymatusnotes.md:55.
  
  
   The hierarchy should be:

  The current system has the right composition shape, but the channel is a fixed symmetric reliability of 0.90 or 0.80 src/learnloop/
  services/probe_families.py:56. Real errors are asymmetric: graders may confuse partial success with success much more often than
  they confuse a signature misconception with success.

  Calibrate separate confusion models by grader version, rubric type, response length/task family, domain, and outcome. Store the raw
  grade, calibrated distribution over Z, calibration-model version, and any adjudication. High-influence or low-confidence responses
  should receive a second grade or ask the learner for clarification.

  Currently, the probe submission path obtains likelihoods without passing per-attempt grader confidence src/learnloop/services/
  probe_episodes.py:1418. More seriously, the canonical certification projection calculates evidence mass without consuming grader
  reliability src/learnloop/services/canonical_projection.py:265. L0 should fix both paths before open-world diagnoses receive more
  authority.

  ### 3. Replace raw EIG with decision-focused value

  Raw hypothesis EIG values distinctions even when every surviving hypothesis implies the same intervention. V2 recognizes that as a
  stop condition, but it should also affect selection.

  The target objective should become:

  ## [
  EVSI(q)=
  \min_a E[L(a,H)]

  ## E_g\left[\min_a E[L(a,H)\mid g,q]\right]

  C(q)
  ]

  This is the expected reduction in downstream decision loss from asking the probe, minus time, fatigue, and burden.

  Recommended policy:

  - Use hypothesis EIG when naming the distinction is itself important for inspectability.
  - Use predictive EIG for baselines/readiness, against an explicit frozen distribution of goal-relevant terminal tasks.
  - Prefer EVSI when hypotheses map to different repairs.
  - Normalize all objectives by expected burden or seconds.
  - Stop when no candidate has positive robust value, all plausible states imply the same action, fatigue caps are reached, or the
    episode needs open-set expansion.

  The cited adaptive-elicitation work supports greedy selection as a practical direction, but its guarantee relies on a meta-trained
  predictive simulator close to the real response distribution and approximate submodularity. It explicitly warns that a poorly
  calibrated simulator can harm performance. LearnLoop currently substitutes prompted and hand-authored likelihoods, so greedy EIG is
  a heuristic—not yet a theorem-backed authority. See the Adaptive Elicitation paper (https://arxiv.org/html/2504.04204v2).

  ### 4. Represent uncertainty in the likelihoods

  The current ordinal vocabulary maps words to fixed numbers such as 0.60, 0.25, and 0.10 with pseudo-count 8 src/learnloop/services/
  probe_families.py:28. Treat these as weak priors with uncertainty, not as point truth.

  Use a hierarchical model:

  - family-level prior;
  - card-level residual;
  - surface/task-feature residual;
  - grader channel;
  - uncertainty interval around each conditional.

  Rank probes using expected value or a conservative lower bound across plausible likelihood matrices. If the winning probe changes
  under small credible perturbations, the correct action is to abstain or author a stronger instrument.

  The current “real learner calibration” assigns fractional latent labels using the posterior produced by the same model src/
  learnloop/services/probe_families.py:1624. That can be useful as EM-style exploratory fitting, but it is not independent
  calibration and can reinforce its own priors. Authority-grade calibration needs audited anchor episodes, human-confirmed diagnoses,
  prospective confirmation, or a jointly fitted identifiable model with held-out evaluation.

  ### 5. Define genuinely held-out predictive targets

  The current predictive target pool is the first eligible instruments in deterministic ID order src/learnloop/services/
  probe_episodes.py:449. That is reproducible but does not represent what the learner ultimately needs to do.

  Freeze a goal-conditioned target distribution containing:

  - required capabilities;
  - task complexity;
  - transfer distances;
  - representations and response forms;
  - source/exam weights;
  - unseen surface groups.

  Predictive EIG should measure uncertainty reduction over that distribution, not whatever cards happen to sort first.

  ### 6. Make open-world detection model-misspecification driven

  The current trigger is mainly posterior mass on other_or_unknown src/learnloop/services/probe_blocks.py:97. Add:

  - low posterior-predictive probability or high surprise;
  - repeated unexplained signatures across independent surfaces;
  - varied repair failures;
  - learner counter-explanations;
  - newly ingested semantic distinctions;
  - systematic grader disagreement.

  The generic other row should be an alarm state, not a diagnosis. Expansion must remain between episodes: generate a provisional
  successor set, confirm on prospectively minted surfaces, and preserve the original episode’s ontology unchanged.

  ## PI, teaching, and scheduling direction

  ### Separate activity purpose from administration context

  V2 currently defines diagnostic and practice families, then introduces worked examples as a policy. Worked examples do not
  naturally belong to either: they are instruction, and success while studying one should not certify independent capability.

  Use immutable authoring purposes:

  - diagnostic: discriminate learner states;
  - instructional: change learner state;
  - practice: strengthen or generalize;
  - assessment: estimate terminal performance.

  Then record administration context independently: cold, scaffolded, feedback-exposed, collaborative, timed, tools-available, and so
  on.

  ### Use a staged instructional policy

  Andy’s notes support:

  1. worked example;
  2. completion/faded example;
  3. independently solved near-transfer task;
  4. varied and interleaved application;
  5. delayed unseen cold proof.

  Worked examples are especially useful during initial acquisition of high-element-interactivity material, while problem solving
  becomes more valuable after acquisition. That is supported by van Gog’s worked-example study
  (https://onlinelibrary.wiley.com/doi/10.1111/cogs.12002) and the later Ruitenburg et al. study
  (https://doi.org/10.1016/j.learninstruc.2024.102027).

  Likewise, retrieval practice has positive transfer overall, but elaboration, initial success, response alignment, and transfer
  distance matter; it is not enough to rotate wording. See Pan and Rickard’s meta-analysis (https://doi.org/10.1037/bul0000151).

  Therefore, the “~80% expected success” rule should not be universal:

  - Worked-example study has no meaningful correctness target.
  - Completion tasks may target very high success.
  - Independent repair might target roughly 70–85%.
  - Diagnostic probes maximize discrimination, not desired difficulty.
  - Cold assessments sample the terminal task distribution even when predicted success is low.

  ### Do not collapse all progression into capability

  The proposed capability ladder conflicts with the current closed vocabulary src/learnloop/vault/models.py:414, but the deeper
  problem is conceptual.

  Represent these separately:

  - capability: retrieve, interpret, select, execute, coordinate, explain;
  - cognitive complexity/element interactivity;
  - transfer distance;
  - representation;
  - response form;
  - scaffolding and cue availability;
  - context, tools, time pressure, and collaboration;
  - integration/whole-task demand.

  RecipeComponent.modality already means hard/path-specific/facilitating/instructional-order src/learnloop/vault/models.py:233. Time
  pressure must not be added as another value in that field.

  ### Split learner state from card and surface state

  Current FSRS state is keyed directly to practice_item_id migrations/001_initial.sql:204, and PracticeItem still contains a static
  prompt and expected answer src/learnloop/vault/models.py:342.

  Use three kinds of state:

  - Target readiness: learner state for a commitment × facet × capability/task regime.
  - Card psychometrics: difficulty, discrimination, validity, and rubric calibration.
  - Surface familiarity: recency, exact-script exposure, kinship, and burn state.

  For literal stable recall, FSRS can remain the target-trace model. For variable conceptual or complex-skill families, use a family/
  capability readiness or survival model conditioned on task features. Do not blindly interpret performance on one rotating surface
  as retention of every sibling.

  An attempt should update related activities through a conservative transfer kernel based on shared facet, capability,
  representation, response structure, and solution family. This provides Andy’s shared scheduling effect without double-counting
  evidence.

  Also add explicit scheduler constraints for:

  - no back-to-back same-facet siblings;
  - cross-day dispersion of angles;
  - goal-dependent interleaving;
  - delayed unseen proof surfaces;
  - global near-clone/fingerprint caps.

  ## Controller and boundary

  The current live scheduler remains a weighted sum of forgetting risk, goal frontier, recent error, and probe EIG src/learnloop/
  services/scheduler.py:645. Its supposed information and learning-gain terms contain hand-set variance reductions, correctness
  adjustments, target bands, and gains—for example src/learnloop/services/selection_rewards.py:260 and src/learnloop/services/
  ability_transition.py:22.

  Do not replace this with another weighted sum called a controller. Eventually, all modes should be evaluated in a common unit:

  > expected goal-weighted delayed unseen performance gained or preserved per minute.

  Until those transition estimates are calibrated, use a transparent constrained policy/state machine and run the scored controller
  in shadow mode:

  1. Measure only when uncertainty changes the next action and robust EVSI exceeds cost.
  2. Teach the best-supported boundary gap.
  3. Maintain high-value traces approaching their retention limit.
  4. Reassess cold after an appropriate delay.
  5. Expand only when evidence indicates model misspecification.
  6. Stop when marginal value is non-positive.

  The existing shadow-only intent planner correctly requires held-out gains before promotion src/learnloop/services/
  intent_planner.py:1. Preserve that discipline.

  For the boundary UI, maintain two visibly separate axes:

  - historical evidence: untested, attempted, demonstrated, contradicted, contested;
  - current prediction: likely retained, uncertain, likely decayed, with interval and timestamp.

  Current Ready is capability-agnostic and deliberately repeated across every capability cell src/learnloop/services/
  capability_grid.py:1. That can support an “ever demonstrated” grid, but it cannot honestly power capability-specific current
  readiness. Either activate and calibrate the capability residual model or label the pooled prediction clearly.

  ## Canonical ingestion direction

  The source layer is already one of the strongest parts of the implementation:

  - immutable artifact → revision → extraction lineage and block IR migrations/032_source_layer.sql:7;
  - canonical IR rather than markdown-as-truth src/learnloop/ingest/ir.py:1;
  - deterministic, ambiguity-preserving reanchoring src/learnloop/ingest/reanchor.py:1;
  - span-cited inventory validation src/learnloop/services/source_unit_inventory.py:273;
  - explicit provenance, alternate notation, and conflict storage migrations/044_provenance_manifests_apply_intents.sql:9.

  Preserve four distinct layers:

  1. Raw immutable source/revision/block.
  2. Source-specific assertions with span provenance.
  3. Versioned reviewed canonical concepts/facets/recipes and unresolved conflicts.
  4. Learner annotations, commitments, practice state, and evidence.

  The current inventories are explicitly candidate JSON rather than canonical entities migrations/041_source_unit_inventories.sql:13,
  but synthesis then creates facet claims directly and marks them reviewed src/learnloop/services/source_set_synthesis.py:525. Add
  durable first-class source assertions between these stages and keep synthesized canonical facets proposed until accepted.

  “Canonical” must mean a reviewed, versioned reconciliation—not that alternate formulations or contradictions were erased.

  For the reader:

  - Demand-page inventory and proposals around the current reading neighborhood.
  - Acknowledge capture immediately; synthesis must never block saving the learner’s intent.
  - Let proposals accumulate for exception review; never silently apply them while reading.
  - Treat highlights, dwell, revisits, and questions as salience signals only. They are missing-not-at-random and are not evidence of
    understanding.

  - Preserve annotations verbatim alongside canonical mappings.
  - Anchor highlights with block ID plus local offsets, exact quote, prefix/suffix, and PDF geometry where available. Whole-block
    anchoring alone is insufficient for precise highlights.

  - Add per-block extraction health. The current IR only models page-level health src/learnloop/ingest/ir.py:117, while v2 promises
    equation/figure-level fallback.

  ## Implementation priority

  1. Measurement integrity: calibrated outcome distributions, grader-versioned observations, reliability-aware certification, robust
     likelihood sensitivity, true target pools, and complete stop rules.

  2. Durable activity model: practice commitments, four family purposes, card/surface/administration separation, global familiarity,
     retirement semantics.

  3. Scheduling state: target-level readiness, separate surface warmth, sibling dispersion, interleaving, delayed unseen proof.
  4. Canonical reader foundation: first-class source assertions, annotation selectors, per-block health, demand-paged proposals. This
     can proceed in parallel with steps 2–3 once identifiers are fixed.

  5. Boundary and controller: capability-honest read models; shadow decision policy evaluated on delayed held-out outcomes.
  6. Open-world diagnosis: successor hypothesis sets, model-misspecification triggers, discovery/confirmation split.
  7. Learned policies or planning: only after sufficient exploration data and a calibrated learner transition model exist.

  The key philosophy is: the learner commits to a thing; LearnLoop maintains a corrigible model of that thing and the learner’s
  relationship to it; activities are disposable experiments and experiences chosen to improve delayed, unseen, goal-relevant
  performance. That is the cleanest synthesis of v2, the earlier brainstorming, Andy’s insights, and what the current implementation
  can realistically support.

 ## Recommended durable product model
 

  Andy’s central insight is stronger than “families generate varied prompts”: the thing the learner cares about must exist independently of its prompts. His notes explicitly describe the emotional mismatch caused by forcing an interesting thing into a task-shaped object
  spec_andymatusnotes.md:37 and spec_andymatusnotes.md:55.

 
  The hierarchy should be:


  Practice commitment
  ├── learner intent, purpose, desired depth, goal and personal interpretation
  ├── knowledge targets
  │   ├── source-specific assertions
  │   ├── canonical facets / concepts / recipes
  │   └── learner annotations
  └── activity families
      ├── diagnostic
      ├── instructional
      ├── practice
      └── assessment
          └── card / activity contract
              └── surface instance
                  └── administration event
                      └── observation and evidence


  A practice commitment might be “understand eigenvectors,” “be able to use Bayes factors,” a poem, a technique, a project capability, or something the learner simply wants to revisit. This is broader than an EvidenceFacet, which is specifically an assessable semantic atom.


  Cards and surfaces can then be freely retired without deleting the learner’s intent, annotations, evidence, or connection to the underlying thing.


  This also resolves a tension in v2: formulation can be a valuable encoding act, but capture should never require formulation. The learner should be able to say “bring this into my practice” immediately, then optionally formulate, annotate, or author activities later.


  ## Probe algorithm direction

  ### 1. Preserve the strong foundations
  
  
    The existing probe architecture already has several excellent invariants:
  
  
    - Locked episode hypothesis sets and immutable presentation snapshots are persisted in migrations/028_probe_episodes.sql:64.
    - Selection and posterior replay use the persisted instrument snapshot.
    - Instruction closes the pre-intervention diagnostic segment in src/learnloop/services/probe_episodes.py:1057.
    - Contaminated observations are tempered rather than silently treated as cold evidence.
    - Diagnostic surfaces are not reused.
  
  
    Keep all of these.
  
  
    ### 2. Model grading explicitly
  
  
    The observation model should distinguish:
  
  
    - H: learner hypothesis/state;
    - Z: the learner’s latent true response class;
    - G: the grader’s observed classification.
  
  
    Use:
  
  
    [
    P(G \mid H,q)=\sum_z P(G\mid Z=z,\text{grader,rubric,domain})P(Z=z\mid H,q)
    ]
  
  
    The current system has the right composition shape, but the channel is a fixed symmetric reliability of 0.90 or 0.80 src/learnloop/services/probe_families.py:56. Real errors are asymmetric: graders may confuse partial success with success much more often than they confuse a
    signature misconception with success.
  
  
    Calibrate separate confusion models by grader version, rubric type, response length/task family, domain, and outcome. Store the raw grade, calibrated distribution over Z, calibration-model version, and any adjudication. High-influence or low-confidence responses should receive a
    second grade or ask the learner for clarification.
  
  
    Currently, the probe submission path obtains likelihoods without passing per-attempt grader confidence src/learnloop/services/probe_episodes.py:1418. More seriously, the canonical certification projection calculates evidence mass without consuming grader reliability src/
    learnloop/services/canonical_projection.py:265. L0 should fix both paths before open-world diagnoses receive more authority.
  
  
    ### 3. Replace raw EIG with decision-focused value
   
   
     Raw hypothesis EIG values distinctions even when every surviving hypothesis implies the same intervention. V2 recognizes that as a stop condition, but it should also affect selection.
   
   
     The target objective should become:
   
   
     ## [
     EVSI(q)=
     \min_a E[L(a,H)]
   
   
     ## E_g\left[\min_a E[L(a,H)\mid g,q]\right]
   
   
     C(q)
     ]
   
   
     This is the expected reduction in downstream decision loss from asking the probe, minus time, fatigue, and burden.
   
   
     Recommended policy:
   
   
     - Use hypothesis EIG when naming the distinction is itself important for inspectability.
     - Use predictive EIG for baselines/readiness, against an explicit frozen distribution of goal-relevant terminal tasks.
     - Prefer EVSI when hypotheses map to different repairs.
     - Normalize all objectives by expected burden or seconds.
     - Stop when no candidate has positive robust value, all plausible states imply the same action, fatigue caps are reached, or the episode needs open-set expansion.
   
   
     The cited adaptive-elicitation work supports greedy selection as a practical direction, but its guarantee relies on a meta-trained predictive simulator close to the real response distribution and approximate submodularity. It explicitly warns that a poorly calibrated simulator
     can harm performance. LearnLoop currently substitutes prompted and hand-authored likelihoods, so greedy EIG is a heuristic—not yet a theorem-backed authority. See the Adaptive Elicitation paper (https://arxiv.org/html/2504.04204v2).
   
   
     ### 4. Represent uncertainty in the likelihoods
     
     
       The current ordinal vocabulary maps words to fixed numbers such as 0.60, 0.25, and 0.10 with pseudo-count 8 src/learnloop/services/probe_families.py:28. Treat these as weak priors with uncertainty, not as point truth.
     
     
       Use a hierarchical model:
     
     
       - family-level prior;
       - card-level residual;
       - surface/task-feature residual;
       - grader channel;
       - uncertainty interval around each conditional.
     
     
       Rank probes using expected value or a conservative lower bound across plausible likelihood matrices. If the winning probe changes under small credible perturbations, the correct action is to abstain or author a stronger instrument.
     
     
       The current “real learner calibration” assigns fractional latent labels using the posterior produced by the same model src/learnloop/services/probe_families.py:1624. That can be useful as EM-style exploratory fitting, but it is not independent calibration and can reinforce its
       own priors. Authority-grade calibration needs audited anchor episodes, human-confirmed diagnoses, prospective confirmation, or a jointly fitted identifiable model with held-out evaluation.
     
     
       ### 5. Define genuinely held-out predictive targets
     
     
       The current predictive target pool is the first eligible instruments in deterministic ID order src/learnloop/services/probe_episodes.py:449. That is reproducible but does not represent what the learner ultimately needs to do.
     
     
       Freeze a goal-conditioned target distribution containing:
     
     
       - required capabilities;
       - task complexity;
       - transfer distances;
       - representations and response forms;
       - source/exam weights;
       - unseen surface groups.
     
     
       Predictive EIG should measure uncertainty reduction over that distribution, not whatever cards happen to sort first.
     
     
       ### 6. Make open-world detection model-misspecification driven
       
       
         The current trigger is mainly posterior mass on other_or_unknown src/learnloop/services/probe_blocks.py:97. Add:
       
       
         - low posterior-predictive probability or high surprise;
         - repeated unexplained signatures across independent surfaces;
         - varied repair failures;
         - learner counter-explanations;
         - newly ingested semantic distinctions;
         - systematic grader disagreement.
       
       
         The generic other row should be an alarm state, not a diagnosis. Expansion must remain between episodes: generate a provisional successor set, confirm on prospectively minted surfaces, and preserve the original episode’s ontology unchanged.
       
       
         ## PI, teaching, and scheduling direction
       
       
         ### Separate activity purpose from administration context
       
       
         V2 currently defines diagnostic and practice families, then introduces worked examples as a policy. Worked examples do not naturally belong to either: they are instruction, and success while studying one should not certify independent capability.
       
       
         Use immutable authoring purposes:
       
       
         - diagnostic: discriminate learner states;
         - instructional: change learner state;
         - practice: strengthen or generalize;
         - assessment: estimate terminal performance.
       
       
         Then record administration context independently: cold, scaffolded, feedback-exposed, collaborative, timed, tools-available, and so on.
       
       
         ### Use a staged instructional policy

─ Worked for 11m 43s ────────────────────────────────────────────────────────────────────────────────────────────────────────────────


› Tell me your thoughts on the following extension of ingestion from the original brainstorm spec_new_improvements.md: ## Ingestion
  as a peritextual active reader
  SuperMemo's incremental reading model treats reading as a funnel from sources, to selected passages, to extracts, to active
  knowledge and eventually creative application.

  We can have
  - skim: identify core claims, terms, figs, and questions
  - anchor reading: deeply process 1 especially important section in a source
  - syntopic view: compare several sources around a concept or open question
  - incremental reading: revisit selected passages over time, extract and refine only what remains directly valuable.

  So the user opens the source, begins reading, then begins asking (this triggers background extraction and inventory, progressively
  proposed study structure).

  We should have the reader be able to view the canonical source within the Tauri application, then be able to do the following:
  - Ask
  - Show a worked example
  - Find an alternative explanation
  - Why does this matter
  - Help me remember this
  - Mark this as confusing
  - Connect it to something I know
  - Test me later on this
  - Not worth remembering
  The reader then supports the metacognitive feedback loops that books usually leave to the reader, like "Did I understand this?".
  We can have this tie back into our existing section based learnloop ask tutor, primed attempts and other aspects.
  For practice items, we have cold retrieval first. Then, we can have immediate restoration of the source neighborhood afterward,
  including the learner's original annotations.

  Additionally, we should make the authoring of additional prompts/PI easier. AI should reduce the friction and mechanical cost of
  prompt creation without automating the interpretive act that makes the material personally meaningful and effective. We can have
  both large automatic study map generation from the canonical source, but we should have users write author good question/answer
  for themselves since writing flashcards is itself a thinking skill. Early cards from a user are often "exhaust" from the process
  of forming an understanding.
  Another issue I noticed from conducting research on lead users was how other learning system frame deletion as failure. However,
  we should look into how we could frame it as healthy model maintenance.
  A PI can be originally useful, then too easy. Or it can be ambiguous, missing context, test duplicate surfaces, wrong granularity,
  no longer relevant, repeatedly failed because the underlying explanation is poor, or retired because a better activity replaced
  it. Retiring a PI shouldn't remove or delete the underlying knowledge of the user latent state or the underlying facet evidence/
  source relationship/learning goal. In the end, the most important thing is that the learner is actually using and getting value
  from the application. This means making the friction as low as possible for usual pain points throughout the learning process.

  Users need assistance developing the meta skill of formulation (which should result in better scores and better transfer). For
  example, what is the atomic claim, what would prove I understand it rather than recognize wording, what mistake would reveal I
  have a shallow internal model, what should  I be able to produce or discriminate, is this worth committing to long-term review.
  This can be a scale, where novices can be heavily scaffolded and experts can be more free form.

  In this way, we can hope to have something where the friction experienced by the user to add a PI is minimized since AI authorship
  can fill all of the minutia and the user reaps the cognitive benefit of making the question and answer. We can also have several
  steps of how a user can go through and approach a canonical source they haven't seen before, and as they go through it more and
  more PIs/LOs can be created dynamically based on user intent of what they find valuable to memorize and keep. The learner can
  select exercises they want to practice and be good at from the chapter's end, and the user's annotations and questions on topics
  from the canonical source can then be turned into LOs and PIs that are emotionally important to the learner instead of a bunch of
  random cards. PIs and LOs for learners who are students or following courses could also be based on canonical ingestion of the
  final practice exams they want to get good scores on in order to guide authoring. But even after being able to solve a final
  practice exam, the student can always be escalated to higher depth ladder questions.


• This is one of the strongest product directions in the brainstorm. It turns ingestion from a batch preprocessing step into
  LearnLoop’s front door: reading progressively becomes annotation, interpretation, commitment, instruction, practice, and eventually
  application.

  The central rule should be:

  > Reading interactions create durable captures and proposals—not automatic knowledge objects or evidence.

  The progression should be:

  Source passage
  → learner annotation or question
  → practice commitment
  → proposed canonical mapping
  → proposed activities
  → accepted practice
  → cold observation
  → evidence

  ## The four reading modes

  The modes are useful because they describe different learner intentions, not merely UI layouts.

   Mode                   Primary objective                                            Durable output
  ━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Skim                   Orient and decide where attention is worthwhile              Questions, candidate claims, section salience
  ─────────────────────  ───────────────────────────────────────────────────────────  ───────────────────────────────────────────────
   Anchor reading         Build a model of one consequential section                   Interpretations, worked examples, commitments
  ─────────────────────  ───────────────────────────────────────────────────────────  ───────────────────────────────────────────────
   Incremental reading    Revisit and refine material whose value remains uncertain    Refine, promote, defer, or release decisions
  ─────────────────────  ───────────────────────────────────────────────────────────  ───────────────────────────────────────────────
   Syntopic view          Compare source-relative answers to one concept or            Agreements, conflicts, alternate formulations
                          question

  A few refinements:

  - Skimming past something is not evidence that it is understood. It may inform proposal priority, but never learner certification.
  - Incremental reading should feed the same maintenance system as practice commitments; it should not become an entirely separate
    queue.

  - Syntopic reading needs first-class source assertions. It cannot safely operate by merging several sources into one AI-generated
    “canonical answer.”

  - Anchor reading should be the richest mode, but the system must remain quiet unless invoked. A reader that constantly asks “Did
    you understand this?” will become intolerable.

  ## Collapse the action palette into three primitives

  The nine actions are good, but presenting all nine equally will feel like a context-menu cockpit. Internally, they reduce to three
  mechanisms:

  ### Ask or transform

  - Ask
  - Show a worked example
  - Alternative explanation
  - Why does this matter?

  These create a tutor exchange anchored to the selected passage. The exchange should remain available later as provenance, but
  hidden during cold attempts.

  ### Commit or elaborate

  - Help me remember this
  - Connect it to something I know
  - Test me later

  These should have distinct semantics:

  - Test me later: one delayed cold check; not necessarily permanent review.
  - Help me remember: create or extend an ongoing practice commitment.
  - Connect it: create a learner-authored interpretation or proposed relationship. It must not silently add a canonical graph edge.

  This distinction prevents every interesting highlight from becoming a lifelong flashcard.

  ### Disposition

  - Mark confusing
  - Not worth remembering

  These are learner-local signals:

  - “Confusing” seeds a question or provisional diagnostic hypothesis; it is not evidence of inability.
  - “Not worth remembering” suppresses future proposals for that learner. It does not delete the source assertion or imply the
    material is unimportant universally.

  The UI can initially show three main actions—Ask, Practice, Mark—with the specific presets underneath.

  ## Capture first; formulation is an optional deepening act

  The extension is right that formulation can itself produce learning. But “users should write good questions and answers” should not
  become a new entrance requirement.

  A better progressive authoring flow is:

  1. Capture: “Bring this into my practice.” Saved immediately, locally, before any AI work.
  2. Intent: “What do you want to be able to do with it?” Remember, explain, distinguish, use, solve, or connect.
  3. Optional formulation: Write a question, expected answer, interpretation, or likely mistake.
  4. Mechanical completion: AI fills canonical mapping, rubric, provenance, capability targets, fingerprints, difficulty priors,
     activity-family attachment, and sibling proposals.

  5. Non-blocking lint: Warn about ambiguity, wording recognition, excessive breadth, missing context, or duplication.

  This preserves the meaningful interpretive act while allowing someone to capture an idea in two seconds.

  For novices, the formulation coach might ask one question at a time:

  - “What would you like to be able to do without seeing this passage?”
  - “What answer would demonstrate understanding?”
  - “What tempting mistake would reveal shallow understanding?”

  Experts should be able to write freely and receive post-hoc suggestions. The coach should never prevent saving.

  Also, do not assume user-authored prompts necessarily improve transfer. Log authorship and later compare delayed unseen
  performance, survival, and retirement against AI-authored activities.

  ## Do not dynamically create LOs for every valuable passage

  The phrase “more and more PIs/LOs can be created dynamically” is directionally right but architecturally risky.

  A highlight usually needs a learner-local practice commitment, not a new canonical LO. Several annotations may map to one existing
  facet; several facets may support one LO; a personal interpretation may belong only to the learner.

  During reading, create:

  - annotations immediately;
  - practice commitments immediately;
  - canonical mappings as proposals;
  - new facets or LOs only when existing knowledge objects genuinely cannot represent the target;
  - activity cards only after their purpose and assessment contract are clear.

  This prevents the knowledge graph from becoming a transcript of everything the learner clicked.

  ## Cold retrieval followed by restoration is excellent

  This should become a product-level contract:

  1. Present the activity without source cues or prior annotations.
  2. Freeze the response.
  3. Grade and record the observation.
  4. Restore the exact source neighborhood.
  5. Restore the learner’s original annotations and tutor exchange.
  6. Offer explanation, comparison, correction, or a worked example.
  7. Later use an unseen sibling surface for cold confirmation.

  The restoration event is instruction, not additional evidence. It should be logged as an exposure so the system knows that related
  surfaces are temporarily warm.

  “Cold” should also be defined relative to the goal. If the target is open-book analysis, coding with documentation, or tool-
  assisted work, those tools may belong in the terminal performance contract. Cold should mean “without unintended learning cues,”
  not universally closed-book.

  ## Retirement should operate at two levels

  The extension’s treatment of deletion is exactly right. LearnLoop should distinguish:

  ### Activity-level retirement

  - ambiguous;
  - duplicated surface;
  - memorized wording;
  - missing context;
  - wrong difficulty or granularity;
  - bad rubric;
  - superseded by a better activity.

  ### Commitment-level disposition

  - stop testing this idea;
  - keep it as reference only;
  - reduce the desired depth;
  - pause until the associated project returns;
  - no longer relevant;
  - not worth the review burden.

  Retiring an activity should:

  - stop its scheduling;
  - preserve all attempts and observations;
  - preserve facet evidence and provenance;
  - preserve the practice commitment;
  - optionally propose a replacement;
  - record a reason for later quality analysis.

  The interface should frame this as “Refine practice,” not deletion. High retirement churn among early learner-authored activities
  may be evidence that understanding matured.

  “Too easy” should not automatically escalate. The user may have achieved the desired goal and should be allowed to stop. Deeper
  tasks should be an invitation conditioned on their purpose, not an endless difficulty treadmill.

  ## Technical ingestion model

  The in-app “canonical source” should actually consist of three things:

  - the immutable original artifact and revision;
  - the extracted document IR used for computation and anchoring;
  - a rendered reader view.

  Converted markdown is a view, not the canonical source. Every equation, figure, and suspicious extraction should offer “view
  original,” ideally as a PDF region rather than forcing the user into a separate full-document viewer.

  Annotations should store:

  - source/revision/extraction identity;
  - block locator;
  - local character offsets;
  - exact selected quote;
  - prefix and suffix context;
  - page geometry when available;
  - reanchoring status;
  - the learner’s text verbatim.

  A block ID alone preserves the neighborhood but may not recover the exact highlighted phrase after re-extraction.

  Background synthesis should be demand-paged and idempotent:

  - explicit learner actions receive highest priority;
  - current and adjacent sections may be prefetched;
  - jobs are keyed by source revision, span/window, action, schema, and model version;
  - caps and token use remain visible;
  - the selected passage is saved before any remote request;
  - only the necessary neighborhood is sent to an external model.

  ## Syntopic reading requires a claim layer

  Even if the syntopic UI is deferred, support its data model now:

  Source assertion
  ├── exact source span
  ├── terminology and scope
  ├── source role
  └── confidence/extraction health

  Canonical claim cluster
  ├── supports
  ├── contradicts
  ├── refines
  ├── uses alternate definition
  └── unresolved

  The syntopic view can then answer:

  - Which sources make the same claim?
  - Where do definitions differ?
  - Is the disagreement substantive or terminological?
  - Which source provides the best example or proof?
  - What remains an open question?

  The learner should always be able to inspect the source-relative statements behind a synthesis.

  ## Exams and end-of-chapter exercises

  Exercises and exams should guide the terminal task distribution, not become semantic authority.

  For exams:

  - designate some papers as blueprint-only;
  - allow some for practice;
  - keep at least one genuinely held out;
  - derive capability, representation, time, and task-complexity requirements;
  - never expose held-out solutions through synthesis;
  - schedule practice toward the observed exam task distribution.

  For chapter exercises, the learner can select “I want to become good at tasks like this.” That should create a goal-linked activity
  family, not merely schedule the exact exercise repeatedly.

  Once the target exam or exercise capability is demonstrated, LearnLoop can offer deeper transfer, explanation, or integration tasks
  —but the learner’s original goal determines whether those matter.

  ## Main product risks

  The biggest failure modes are:

  - turning every highlight into a card;
  - interrupting reading too often;
  - treating dwell or skipping as knowledge evidence;
  - automatically canonicalizing personal interpretations;
  - making formulation mandatory;
  - allowing background AI latency to block capture;
  - restoring source material before freezing cold evidence;
  - confusing “retire this prompt” with “forget this idea”;
  - escalating depth after the learner has already achieved their actual goal.

  Handled carefully, this reader is more than an ingestion UI. It becomes the place where the learner’s initial curiosity is
  preserved all the way through understanding, practice, transfer, and eventual retirement. That is a much more compelling front door
  for LearnLoop than “import a source and generate a study map.”


› I think definitely the most important parts of given subjects within a vault is the end-of-chapter exercises where the learner
  selects "I want to become good at tasks like this", where the user can select the exercises they think  exemplify the textbook
  chapter's knowledge. Could you explain more on how we can have durable FSRS from PI card content vs the dynamic surface it can
  occupy? Probes should be intended to find the jagged boundary of knowledge the user has within the least amount of questions to
  the user  via maximizing EIG, then we can provide PIs in the direction of the learner's gradient that are able to grow with the
  user's latent state as they get better and learn more. Let's make a unified approach based on our discussion on what we should do
  for the next mvp version of LearnLoop


• My recommendation for the next MVP is an exemplar-driven adaptive practice loop:

  Select “I want to become good at tasks like this”
  → derive a goal-conditioned task blueprint
  → locate the jagged boundary with a short EIG probe episode
  → teach or practice the nearest actionable gap
  → schedule durable PI cards with FSRS
  → rotate concrete surfaces without changing the card’s meaning
  → cold-reassess on an unseen target-like task
  → maintain, deepen, or stop

  This makes end-of-chapter exercises the organizing center of ingestion, while sources, facets, probes, and PIs become supporting
  machinery.

  ## 1. End-of-chapter exercises define the destination

  When a learner selects an exercise, the original exercise should become a target exemplar, not merely another PI.

  LearnLoop should derive:

  - the expected product and grading rubric;
  - one or more valid solution recipes;
  - required facets and capabilities;
  - prerequisite and integration requirements;
  - representation and response form;
  - allowed tools, time constraints, and target complexity;
  - common errors and confusable methods;
  - the invariants defining “tasks like this.”

  Several selected exercises form a target task distribution. This is more informative than a generic request to “understand Chapter
  6.”

  The original exercise will already be familiar, so it should not normally provide strong cold evidence. It anchors generation and
  explanation; unseen isomorphs and held-out exercises provide proof.

  Exam ingestion should work similarly:

  - some exams are blueprint-only;
  - some are available for practice;
  - at least one remains genuinely held out;
  - solutions help author rubrics but must never leak into held-out surfaces.

  ## 2. Durable FSRS card versus dynamic surface

  The clean distinction is:

  > FSRS schedules a stable assessment contract. The surface generator decides how that contract is instantiated today.

   Object                 Durable meaning                                        Examples
  ━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Practice commitment    What the learner wants to become able to do            “Solve and interpret eigenvector problems”
  ─────────────────────  ─────────────────────────────────────────────────────  ─────────────────────────────────────────────────────
   Activity family        How that ability can be developed at different         examples, completions, component practice,
                          stages                                                 integration
  ─────────────────────  ─────────────────────────────────────────────────────  ─────────────────────────────────────────────────────
   PI card                One stable memory/skill trace and assessment           “Interpret an eigenpair geometrically from an
                          contract                                               unfamiliar matrix”
  ─────────────────────  ─────────────────────────────────────────────────────  ─────────────────────────────────────────────────────
   Surface                One concrete realization of that contract              a particular matrix, diagram, wording, or parameter
                                                                                 set
  ─────────────────────  ─────────────────────────────────────────────────────  ─────────────────────────────────────────────────────
   Administration         The context in which a surface was served              cold, hinted, timed, scaffolded
  ─────────────────────  ─────────────────────────────────────────────────────  ─────────────────────────────────────────────────────
   Evidence               What the response demonstrated                         facet × capability observations
  ─────────────────────  ─────────────────────────────────────────────────────  ─────────────────────────────────────────────────────
   FSRS state             When this card-level trace should next be exercised    difficulty, stability, retrievability, due date

  ### What belongs in the durable PI card

  A card should contain:

  - target facet or blueprint component;
  - target capability;
  - response contract;
  - rubric and evidence attribution;
  - task-family invariants;
  - acceptable difficulty range;
  - representation constraints;
  - surface rotation policy;
  - source exemplars;
  - generator and validation contract;
  - semantic contract hash.

  For example:

  Card:
    Target: interpret Av = λv as invariant direction and scaling
    Capability: schema interpretation
    Response: short explanation plus geometric prediction
    Invariants:
      - unseen 2×2 matrix with a real eigenpair
      - learner must predict the transformation geometrically
      - computation alone is insufficient
    Difficulty band: introductory
    Rubric:
      - identifies invariant direction
      - explains scaling/sign
      - connects algebraic and geometric representations

  ### What belongs in a surface

  A surface contains:

  - concrete prompt text;
  - particular values, diagram, or scenario;
  - instance-specific expected answer;
  - rendering and assets;
  - generator version and seed;
  - estimated difficulty residual;
  - fingerprint and kinship data;
  - exposure history;
  - immutable snapshot of the rubric actually used.

  Changing the matrix or wording does not create a new FSRS trace. Changing from “interpret an eigenpair” to “select an
  eigendecomposition method under constraints” does.

  ### When FSRS state survives a card edit

  Use a durable card_lineage_id separate from immutable card versions.

  Preserve FSRS state when changes are surface-preserving:

  - wording;
  - formatting;
  - parameter pool;
  - equivalent diagrams;
  - generator bug fixes that do not change the task;
  - minor rubric clarification.

  Fork a new lineage and new FSRS state when changes alter what is being learned:

  - different facet or capability;
  - materially different response contract;
  - different prerequisite structure;
  - major difficulty/depth change;
  - open-book becoming closed-book;
  - component practice becoming whole-task integration;
  - changed rubric semantics.

  This prevents accumulated stability from being incorrectly transferred to a harder skill.

  ### How an attempt updates state

  One administration can affect three systems differently:

  1. FSRS: Was the card-level trace successfully retrieved, and when should it recur?
  2. Evidence ledger: What facet × capability did this response demonstrate, under what assistance and familiarity?
  3. Surface familiarity: Is this particular wording, parameter set, or near-clone now warm?

  A hinted attempt may reset or shorten the FSRS interval because the learner failed to retrieve, while receiving little or no cold
  certification credit. These are not contradictory: scheduling and evidence serve different purposes.

  If a generated surface is ambiguous, badly graded, or outside the card’s difficulty bounds, quarantine the surface and do not let
  it materially update the card’s FSRS state.

  ### Cross-card effects

  Performance on one card should not pretend that sibling cards were reviewed. Instead:

  - update shared facet/capability evidence;
  - suppress closely related siblings temporarily through familiarity;
  - update the family’s estimate of which activity stage is appropriate;
  - preserve each sibling’s own FSRS state.

  The concise rule is:

  > Surfaces vary; cards remain semantically stable; families grow.

  ## 3. PIs grow through families, not by mutating cards

  A single card should not evolve from recall into explanation, transfer, and whole-task coordination. That destroys the meaning of
  its FSRS history.

  Instead, a family mints successor cards as the learner advances:

  Worked example
  → example completion
  → independent component practice
  → discrimination or method selection
  → varied near transfer
  → whole-task integration
  → delayed target-like assessment

  Each stage has its own stable contract. Earlier cards may be:

  - maintained because the target requires durable recall;
  - reduced in frequency;
  - retired as redundant;
  - retained as remedial fallback;
  - superseded by an integrated task.

  A new, deeper card starts with a prior informed by existing evidence, but it does not inherit historical certification. The learner
  still has to demonstrate the new capability.

  ## 4. Goal-conditioned jagged-boundary probes

  The boundary should be scoped to the selected target exercises. LearnLoop does not need to map the learner’s entire chapter before
  helping them.

  The learner state is a posterior over relevant facet × capability cells plus hypotheses about recurring failure mechanisms.

  Use two EIG objectives:

  ### Predictive EIG for initial boundary mapping

  Select the question expected to reduce uncertainty about performance on the selected target task distribution.

  This answers:

  > Which question will most improve our prediction of whether the learner can solve these exercises, and where failure would occur?

  ### Hypothesis EIG after a localized failure

  Once a failure suggests several plausible causes, select the question that best separates them:

  - missing prerequisite;
  - can execute but cannot select the method;
  - can calculate but cannot interpret;
  - representation-specific weakness;
  - integration failure;
  - misconception;
  - unfamiliarity.

  Diagnostic cards remain pre-authored and validated; their concrete surfaces are minted just in time and burned after use.

  ### Top-down probe strategy

  Start with a representative whole or partial target task. This behaves like adaptive group testing:

  - A strong, rubric-localized success can cover several requirements efficiently.
  - A failure creates ambiguity.
  - Subsequent probes split that ambiguity into component or misconception hypotheses.
  - Stop as soon as the intervention decision is stable.

  Rank with cost-normalized information:

  [
  score(q)=\frac{EIG(q)}{\text{expected seconds}+\text{burden}}
  ]

  Raw EIG is sufficient only when all candidates cost approximately the same.

  Stop when:

  - the next action would be the same under all plausible hypotheses;
  - maximum robust EIG is below cost;
  - the posterior is sufficiently stable across independent surfaces;
  - the question budget or fatigue budget is reached;
  - model surprise indicates that the hypothesis set needs expansion.

  The outcome should not merely be “60% mastery.” It should be something actionable:

  > You can execute the eigenvalue procedure, but an unseen interpretation task suggests the algebra-to-geometry link is not yet
  > reliable.

  ## 5. The learner’s gradient

  The “gradient” should mean the shortest instructional path from the current boundary to the selected exemplar distribution.

  For every required component, distinguish:

  - uncertain and decision-relevant → probe;
  - known absent → worked example or explanation;
  - partially acquired → completion/faded guidance;
  - independently usable but narrow → varied practice;
  - components strong but whole task weak → integration practice;
  - terminal task demonstrated → maintain, stop, or optionally deepen.

  For the MVP, this should be a transparent staged policy, not a weighted formula claiming to know expected learning gain.

  A useful controller is:

  if uncertainty changes what we would teach:
      measure
  elif target knowledge has not been acquired:
      show example / explain
  elif capability is fragile or scaffold-dependent:
      completion / targeted practice
  elif components are present but target task still fails:
      whole-task integration
  elif target performance is not yet demonstrated cold:
      unseen target-like assessment
  elif retention is becoming due:
      maintain
  else:
      stop or offer optional depth

  This creates an actual loop:

  measure → teach → practice → cold proof → maintain
                     ↑             |
                     └── repair ───┘

  ## 6. Unified next-MVP product journey

  A vertical slice should look like this:

  1. The learner opens a chapter in the reader.
  2. LearnLoop extracts its structure and exercise section.
  3. The learner selects one to three exercises: “I want to become good at tasks like these.”
  4. LearnLoop creates a practice commitment and proposes a task blueprint.
  5. The learner confirms the target conditions: desired depth, tools, timing, exam relevance.
  6. LearnLoop runs a short two-to-four-question adaptive probe episode.
  7. The boundary view shows demonstrated, uncertain, and missing components.
  8. The controller selects a worked example, completion, or PI card at the nearest gap.
  9. The PI card is scheduled durably by FSRS; its surfaces rotate according to familiarity.
  10. After practice, LearnLoop serves an unseen target-like cold assessment.
  11. The original source neighborhood and annotations are restored afterward.
  12. The learner can maintain, deepen, pause, or declare the goal complete.
  13. Ambiguous or obsolete cards can be retired without removing the commitment or evidence.

  ## 7. Minimal new data model

  The MVP needs roughly these durable objects:

  - practice_commitments
  - target_exemplars
  - activity_families
  - practice_cards
  - practice_card_versions
  - practice_card_state
  - activity_surfaces
  - activity_administrations
  - shared surface fingerprints/exposures
  - source annotations

  For migration compatibility:

  - Backfill each existing PracticeItem as a fixed surface under a one-card family.
  - Copy existing practice_item_state into card-level state.
  - Continue materializing generated surfaces as PracticeItem-compatible snapshots so the current attempt/grading pipeline survives.
  - Split the current content hash into a card semantic-contract hash and a concrete surface hash.
  - Preserve all old IDs and replay behavior under their existing algorithm version.

  ## 8. Scope boundaries for this MVP

  Include:

  - chapter reader;
  - exercise identification and selection;
  - target blueprint generation and review;
  - goal-conditioned EIG probes;
  - worked example/completion/practice stages;
  - durable card-level FSRS;
  - dynamic surface generation;
  - cold reassessment and source restoration;
  - boundary visualization;
  - activity and commitment retirement.

  Defer:

  - full syntopic comparison UI;
  - MCTS;
  - a learned outer controller;
  - unrestricted open-world hypothesis generation during an episode;
  - population-level card promotion;
  - automatic escalation beyond the learner’s chosen goal;
  - whole-library eager synthesis.

  The MVP’s core promise should be:

  > Choose the kinds of problems you want to become good at. LearnLoop will determine the smallest useful set of questions needed to
  > locate your current boundary, give you practice that grows from that boundary toward those problems, and maintain each stable
  > ability without teaching you to memorize the surfaces.• This is one of the strongest product directions in the brainstorm. It turns ingestion from a batch preprocessing step into
