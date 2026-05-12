Below is a product/specification for an **evidence-based learning application** built around the research review you provided. The core idea is: instead of being “Anki + ChatGPT,” it should be a **learning operating system** that decides *what kind of practice the learner needs next* based on the knowledge type, learner expertise, forgetting risk, error history, and desired transfer goal.

# Application Spec: **LearnLoop**

## 1. Product Vision

**LearnLoop** is an adaptive learning app that helps users build durable, transferable expertise across domains such as math, statistics, programming, language learning, puzzles, esports, music, and motor skills.

Its thesis is:

> Learning should not be scheduled only by time. It should be scheduled by memory strength, conceptual dependency, error type, task difficulty, and transfer readiness.

The app combines:

1. **Spaced retrieval**
2. **Successive relearning**
3. **Worked examples → completion problems → independent solving**
4. **Interleaving**
5. **Errorful generation with corrective feedback**
6. **Deliberate practice**
7. **Observational learning**
8. **Sleep/exercise/consolidation-aware scheduling**
9. **AI-generated practice and feedback**
10. **Knowledge tracing / mastery modeling**

Your research review emphasizes that retrieval, spacing, interleaving, worked examples, deliberate practice, and feedback should be selected based on *knowledge type* and *expertise level*, not applied uniformly . Current AI tutoring research also supports LLM-based intelligent tutoring systems, but flags risks like over-reliance, fairness, privacy, and technical reliability, so the app should treat AI as a practice generator and feedback assistant, not an unquestioned authority. ([ScienceDirect][1])

---

# 2. Target Users

## Primary users

**1. Serious students**

Examples: linear algebra, statistics, ML, stochastic processes, algorithms, proofs.

They need:

* Worked examples for high-load concepts
* Closed-book derivation practice
* Interleaved problem sets
* Error taxonomies
* Cumulative review
* Proof reconstruction

**2. Language learners**

Examples: Korean, Chinese, Japanese, Spanish.

They need:

* Vocabulary SRS
* Grammar contrast drills
* Cloze sentences
* Dictation
* Speaking/writing prompts
* Confusable-item interleaving

**3. Skill learners**

Examples: dance, esports, piano, sports, drawing.

They need:

* Observational learning
* Deliberate practice loops
* External-focus cues
* Video/audio feedback
* Skill decomposition
* Weakness tracking

**4. Puzzle/problem-solving learners**

Examples: probability puzzles, olympiad-style math, logic puzzles, interview problems.

They need:

* Productive struggle
* Hint ladders
* Heuristic tagging
* Failed-path analysis
* Transfer variants

---

# 3. Core Product Principle

The app should not ask only:

> “When should this card come back?”

It should ask:

> “What is the next best learning action for this learner, on this concept, given their current mastery, error profile, cognitive load, and transfer goal?”

That means the scheduling unit is not just a flashcard. It is a **learning object**.

---

# 4. Learning Object Model

Every item in the system is stored as a **Learning Object**.

## Learning Object fields

```json
{
  "id": "uuid",
  "title": "Bayes rule derivation",
  "domain": "statistics",
  "knowledge_type": "derivation",
  "difficulty": 0.72,
  "prerequisites": ["conditional probability", "joint probability"],
  "representations": ["text", "equation", "diagram", "worked_example"],
  "practice_modes": [
    "worked_example",
    "completion_problem",
    "retrieval",
    "transfer_problem",
    "explain_from_memory"
  ],
  "mastery_state": {
    "recall_strength": 0.64,
    "schema_strength": 0.42,
    "transfer_readiness": 0.31,
    "fluency": 0.58
  },
  "error_history": [
    {
      "timestamp": "2026-05-12T20:10:00",
      "error_type": "conditional_direction_error",
      "severity": 0.8,
      "feedback_given": true
    }
  ],
  "next_review": "2026-05-15T09:00:00",
  "retention_goal": "semester",
  "last_practice_mode": "completion_problem"
}
```

## Knowledge types

The app should classify material into:

| Knowledge Type   | Examples                                          | Best Initial Strategy                      |
| ---------------- | ------------------------------------------------- | ------------------------------------------ |
| Fact             | vocabulary, definitions, formulas                 | Retrieval + spacing                        |
| Concept          | bias-variance, eigenvectors, Buddhist fatalism    | Explain-from-memory + examples             |
| Procedure        | integration by parts, logistic regression fitting | Worked examples → completion problems      |
| Derivation/proof | Bayes theorem, Fine-Gray score, martingale proof  | Worked examples + proof skeleton retrieval |
| Discrimination   | MLE vs MAP, 은/는 vs 이/가                            | Interleaving                               |
| Motor routine    | dance move, aim drill, piano fingering            | Observation + deliberate practice          |
| Tactical pattern | chess motif, esports rotation                     | VOD/example review + scenario retrieval    |
| Transfer schema  | puzzle heuristic, proof technique                 | Errorful generation + variant solving      |

This matters because your source review is explicit that retrieval practice is powerful for stable mappings, but worked examples are better for novices learning high-element-interactivity material like proofs and complex math procedures .

---

# 5. Main User Experience

## Home screen: “Today’s Learning Loop”

The user sees a daily queue divided into four sections:

1. **Warm-up retrieval**

   * Fast recall of mature items.
   * Vocabulary, definitions, theorem statements, formulas.

2. **Deep work block**

   * New or difficult material.
   * Worked examples, derivations, problem-solving, coding, skill practice.

3. **Weakness repair**

   * Items selected from recent errors.
   * The app chooses drills based on error type.

4. **Transfer challenge**

   * Mixed problems, new contexts, explain-from-memory, teach-back prompts.

Example:

```text
Today’s Loop — 75 minutes

1. Retrieval Warm-up — 12 min
   - Korean particles: 은/는 vs 이/가
   - Eigenvalue definition
   - Fine-Gray competing-risk notation

2. Deep Work — 30 min
   - Worked example: deriving the Cox partial likelihood
   - Completion problem: fill missing risk-set terms

3. Weakness Repair — 18 min
   - You keep confusing hazard and cumulative incidence
   - Do 3 contrastive examples

4. Transfer Challenge — 15 min
   - Explain why Cox and Fine-Gray estimate different causal objects
```

---

# 6. Core Features

## Feature 1: Adaptive Spaced Retrieval Engine

The app should use a modern spaced repetition model rather than a basic Leitner box.

Recommended implementation:

* Start with **FSRS-style scheduling** for item-level recall.
* Add custom layers for:

  * concept dependencies,
  * error severity,
  * transfer performance,
  * practice modality,
  * user fatigue.

FSRS is an open-source spaced repetition scheduler with implementations in multiple languages, and it is designed around modeling memory variables such as difficulty, stability, and retrievability. ([GitHub][2]) Duolingo’s older Half-Life Regression model similarly estimated memory half-life from learner history and reportedly reduced recall prediction error by more than 45% against baselines in the cited paper. ([Duolingo Research][3])

### Scheduling logic

Each item has:

* **Difficulty**
* **Stability**
* **Retrievability**
* **Conceptual dependency score**
* **Transfer score**
* **Error volatility**
* **Fatigue sensitivity**

Basic formula:

```text
priority =
  forgetting_risk
+ prerequisite_importance
+ recent_error_severity
+ upcoming_goal_pressure
+ transfer_gap
- overload_penalty
```

The app should distinguish:

* “I forgot the definition.”
* “I remembered the definition but used it incorrectly.”
* “I can solve familiar problems but fail transfer problems.”
* “I can recognize the answer but cannot produce it.”

Those should produce different next actions.

---

## Feature 2: Knowledge Tracing and Mastery Model

The app should maintain a learner model over concepts, not just cards.

Knowledge tracing research models a student’s evolving knowledge state from past interactions to predict future performance, and newer work extends this with deep learning, sparse attention, LLM dialogue signals, and interpretable student-state modeling. ([arXiv][4])

## Mastery dimensions

Each concept should have separate estimates for:

```text
Recall mastery:       Can you remember it?
Recognition mastery:  Can you identify it?
Procedural mastery:   Can you use it?
Schema mastery:       Do you know when to use it?
Transfer mastery:     Can you use it in a new context?
Explanation mastery:  Can you teach it?
Fluency:              Can you do it quickly and accurately?
```

Example:

```text
Concept: Eigenvectors

Recall:      88%
Recognition: 95%
Procedure:   74%
Schema:      61%
Transfer:    42%
Explanation: 58%

Diagnosis:
You can compute eigenvectors when told to, but you struggle to identify when eigenvectors are the right tool.
Recommended next practice:
Interleaved discrimination set: diagonalization vs SVD vs PCA.
```

This is the key difference from ordinary flashcard systems.

---

## Feature 3: Worked Example → Completion → Independent Practice Pipeline

For difficult material, the app should not immediately test the user.

Instead, it should use a staged learning pipeline:

```text
Stage 1: Worked example
Stage 2: Annotated worked example
Stage 3: Completion problem
Stage 4: Near-transfer problem
Stage 5: Closed-book reconstruction
Stage 6: Interleaved transfer problem
Stage 7: Teach-back explanation
```

Example for math:

```text
Topic: Gradient descent convergence

1. Read worked proof with subgoals.
2. Fill in missing inequality.
3. Reconstruct proof skeleton.
4. Solve a similar proof with different constants.
5. Explain the proof from memory.
6. Compare against Newton’s method convergence.
```

Your review’s curriculum framework explicitly recommends worked examples first for novices in mathematically rigorous domains, then fading toward completion problems, retrieval, mixed sets, and far-transfer problems .

---

## Feature 4: Error Taxonomy and Feedback Engine

Every mistake should be classified.

## Error types

For math/statistics:

* Conceptual error
* Algebraic slip
* Notation error
* Theorem-selection error
* Boundary-condition error
* Assumption violation
* Transfer failure
* Overfitting to surface form

For language:

* Pronunciation
* Orthography
* Grammar
* Word order
* Particle/classifier error
* Collocation error
* Retrieval failure
* Production hesitation

For motor/esports/dance:

* Timing error
* Spatial error
* Sequencing error
* Overcorrection
* Targeting error
* Decision error
* Attention-focus error
* Feedback-dependency error

The app should produce feedback like:

```text
You did not forget Bayes rule.
Your error was directional: you used P(A|B) where P(B|A) was needed.

Repair drill:
Do 5 contrastive examples where the wording changes the conditioning direction.
```

This is much better than marking something simply “wrong.”

---

## Feature 5: Interleaving Engine

The app should deliberately mix confusable concepts.

## Examples

Math:

```text
MLE vs MAP
eigendecomposition vs SVD
Cox hazard vs Fine-Gray subdistribution hazard
independence vs conditional independence
Markov property vs martingale property
```

Language:

```text
Korean 은/는 vs 이/가
안 vs 못
Chinese 的 vs 得 vs 地
了 completion vs 了 change-of-state
```

Esports:

```text
aim duel vs reposition
rotate vs hold angle
reload timing vs push timing
```

The interleaving engine should activate when:

* two concepts are often confused,
* user accuracy is high in blocked practice but low in mixed practice,
* the user asks for transfer,
* an exam/project requires discrimination.

Your review highlights interleaving as especially useful for strategy selection and transfer, including STEM problem sets and language grammar patterns .

---

## Feature 6: Productive Struggle and Hint Ladder

The app should support errorful learning without letting the user flail indefinitely.

## Hint ladder

For a problem:

```text
0. No hint
1. Identify relevant concept
2. Identify first step
3. Show partial structure
4. Show worked-example analogy
5. Show solution skeleton
6. Show full solution
7. Schedule reconstruction later
```

The key is that asking for a hint is not failure. It becomes data.

```json
{
  "problem_id": "p_123",
  "hints_used": 3,
  "time_to_first_move": 180,
  "wrong_paths": ["tried independence assumption"],
  "final_success": true
}
```

Then the app can say:

```text
You solved it after a structure hint.
Next time, we’ll test whether you can identify the structure without the hint.
```

---

## Feature 7: AI Tutor Mode

The AI tutor should have several modes.

## Mode A: Socratic Tutor

The tutor asks questions rather than gives answers.

```text
Tutor: What is the conditioning event in this problem?
User: The person has tested positive.
Tutor: Good. So should the denominator be P(disease) or P(test positive)?
```

## Mode B: Error Diagnostician

The user uploads a solution.

The app returns:

```text
Main issue:
You applied the theorem correctly, but the independence assumption is not justified.

Error type:
Assumption violation.

Repair:
Do 3 examples where independence is tempting but false.
```

## Mode C: Practice Generator

The tutor generates:

* cloze cards,
* proof skeletons,
* near-transfer problems,
* far-transfer problems,
* contrastive examples,
* oral exam questions,
* coding exercises.

AI systems are increasingly used for generating practice, giving feedback, scaffolding retrieval practice, and adapting difficulty, but the app should include validation and source grounding where possible. ([Purdue University College of Education][5])

## Mode D: Explain-Like-I’m-Learning

The user can ask:

```text
Explain this in 3 levels:
1. intuition
2. formal definition
3. worked example
```

## Mode E: Adversarial Examiner

For advanced users:

```text
The app challenges weak assumptions, asks edge cases, and tries to break the user’s explanation.
```

Example:

```text
You said this estimator is unbiased. Under what sampling assumptions?
What happens if censoring is informative?
Can you construct a counterexample?
```

---

# 7. AI Safety and Pedagogical Guardrails

The app should avoid becoming a “homework answer machine.”

## Guardrails

1. **Default to questions before answers**
2. **Require user attempt before full solution**
3. **Use hint ladder**
4. **Distinguish learning mode vs answer mode**
5. **Cite uploaded/source material when grounding**
6. **Detect over-reliance**
7. **Show uncertainty for generated problems/solutions**
8. **Use answer verification for math/code**

The system should track:

```text
AI-dependence risk:
- User asks for answers before attempting
- User skips reconstruction
- User reads explanations but avoids retrieval
- User performs well with AI hints but poorly without them
```

Then it can intervene:

```text
You’ve been studying mostly by reading explanations.
Next session will start with closed-book reconstruction before new material.
```

This directly addresses a common weakness in AI tutoring: users can feel like they understand because the explanation is fluent, while their own retrieval and transfer remain weak.

---

# 8. Domain-Specific Modules

## A. Math / ML / Statistics Mode

This should be one of the strongest modules.

### Features

* Theorem cards
* Assumption cards
* Proof skeleton reconstruction
* Derivation replay
* Symbol glossary
* Error taxonomy
* Interleaved problem sets
* Oral exam mode
* “When do I use this?” discrimination drills
* LaTeX input
* Whiteboard/photo upload
* Code + math paired exercises

### Example workflow

```text
Topic: Fine-Gray competing risks

1. Worked example: difference between cause-specific hazard and subdistribution hazard.
2. Retrieval: define risk set modification.
3. Completion: fill missing IPCW term.
4. Interleaving: Cox vs Fine-Gray vs Kaplan-Meier.
5. Transfer: interpret coefficient in bail/recidivism setting.
6. Teach-back: explain why censoring/disposition matters.
```

### UI idea

For every theorem/model:

```text
Definition
Assumptions
Canonical example
Failure mode
Common confusions
Proof sketch
Practice problems
Transfer problems
```

---

## B. Language Mode

### Features

* FSRS-style vocabulary scheduling
* Cloze sentences
* Bidirectional translation
* Dictation
* Pronunciation scoring
* Grammar contrast drills
* Character production
* Error categories
* Conversation simulation
* “Use it in a sentence” tasks

### Example Korean item

```text
Target: 안 vs 못

Recognition:
Choose the correct negative form.

Production:
Translate: “I couldn’t swim yesterday.”

Contrast:
안 갔어요 vs 못 갔어요

Explanation:
Explain the difference in your own words.
```

The app should not rely only on flashcards. Your review emphasizes that language learning benefits from spaced retrieval, sentence production, cloze tasks, and interleaving confusable grammar forms .

---

## C. Puzzle / Problem-Solving Mode

### Features

* Productive struggle timer
* Hint ladder
* Heuristic tagging
* Failed-path capture
* Variant generation
* “Invent your own problem”
* Explain solution from memory
* Disguised re-test

### Puzzle postmortem

```text
What was the deep structure?
What false path was tempting?
What cue should have triggered the right heuristic?
What invariant/constraint mattered?
Can you solve a variant?
```

---

## D. Motor / Esports / Dance Mode

This module should apply learning science to embodied skills.

### Features

* Upload VOD/video
* Segment skill attempts
* Expert model comparison
* External-focus cue generation
* Deliberate practice blocks
* Telemetry import where available
* Feedback fading to avoid dependency
* Sleep/fatigue-aware scheduling

### Feedback principle

Avoid:

```text
Move your wrist more.
Raise your elbow.
Think about your shoulder.
```

Prefer external focus:

```text
Track the crosshair path smoothly through the target.
Land the foot on the beat marker.
Match the ghost trajectory through the arc.
```

Your review notes that external-focus cues tend to improve motor learning more than internal body-focused cues, and that continuous visual feedback can create dependency if it is not faded .

---

# 9. The Daily Learning Algorithm

## Step 1: Load user state

```python
user_state = {
    "available_minutes": 75,
    "energy": "medium",
    "sleep_quality": 0.72,
    "upcoming_deadlines": ["statistics exam in 14 days"],
    "recent_errors": [...],
    "retention_goals": {...}
}
```

## Step 2: Select learning objects

Priority score:

```text
priority =
  0.30 * forgetting_risk
+ 0.20 * prerequisite_importance
+ 0.15 * recent_error_severity
+ 0.15 * transfer_gap
+ 0.10 * deadline_pressure
+ 0.10 * learner_interest
- 0.20 * cognitive_overload_risk
```

## Step 3: Choose practice mode

Decision rules:

```text
If novice + high element interactivity:
    worked example or completion problem

If fact/concept + prior encoding exists:
    retrieval

If high blocked accuracy but low mixed accuracy:
    interleaving

If repeated same error:
    targeted repair drill

If mature item:
    quick recall

If transfer goal:
    novel problem or teach-back

If motor skill:
    observation → practice → feedback → faded retest
```

## Step 4: Score the attempt

Record:

* correctness,
* latency,
* confidence,
* hints used,
* error type,
* explanation quality,
* transfer distance,
* fatigue,
* feedback mode.

## Step 5: Schedule next action

Not just next review — next **learning action**.

```text
Correct + fast + confident:
    increase interval

Correct but slow:
    fluency drill later

Correct with hint:
    retest soon without hint

Wrong due to concept:
    worked example + repair drill

Wrong due to discrimination:
    interleaved contrast set

Wrong due to transfer:
    near-transfer bridge problem
```

---

# 10. Data Model

## Tables

### users

```sql
users (
  id uuid primary key,
  name text,
  timezone text,
  goals jsonb,
  preferred_domains text[],
  created_at timestamp
)
```

### learning_objects

```sql
learning_objects (
  id uuid primary key,
  user_id uuid,
  title text,
  domain text,
  knowledge_type text,
  content jsonb,
  prerequisites uuid[],
  difficulty float,
  source_id uuid,
  created_at timestamp
)
```

### practice_attempts

```sql
practice_attempts (
  id uuid primary key,
  user_id uuid,
  learning_object_id uuid,
  practice_mode text,
  is_correct boolean,
  confidence int,
  latency_seconds int,
  hints_used int,
  error_type text,
  feedback text,
  created_at timestamp
)
```

### mastery_states

```sql
mastery_states (
  user_id uuid,
  learning_object_id uuid,
  recall_strength float,
  schema_strength float,
  transfer_readiness float,
  fluency float,
  retrievability float,
  stability float,
  difficulty float,
  updated_at timestamp,
  primary key (user_id, learning_object_id)
)
```

### review_queue

```sql
review_queue (
  id uuid primary key,
  user_id uuid,
  learning_object_id uuid,
  scheduled_at timestamp,
  recommended_mode text,
  priority float,
  reason text
)
```

### error_events

```sql
error_events (
  id uuid primary key,
  user_id uuid,
  learning_object_id uuid,
  error_type text,
  severity float,
  explanation text,
  repair_plan jsonb,
  created_at timestamp
)
```

---

# 11. Main Screens

## 1. Dashboard

Shows:

* Today’s queue
* Time estimate
* Weak concepts
* Upcoming reviews
* Sleep/readiness prompt
* Progress toward goals

## 2. Concept Map

A graph of concepts:

```text
Conditional probability
   → Bayes rule
      → Bayesian inference
         → MAP estimation
         → hierarchical models
```

Nodes are colored by mastery dimension:

* green = durable
* yellow = fragile
* red = failing
* purple = transfer gap

## 3. Practice Session

The core screen.

Contains:

* prompt,
* scratchpad,
* hint ladder,
* confidence rating,
* feedback panel,
* next-step explanation.

## 4. Error Notebook

Automatically generated.

Example:

```text
Recurring Errors This Week

1. Conditional direction errors — 5 times
2. Confusing hazard with probability — 3 times
3. Algebraic sign errors — 4 times
4. Korean topic/subject particle errors — 7 times
```

Each error has:

```text
Why it happened
How to detect it
Repair drill
Next scheduled retest
```

## 5. Transfer Lab

Mixed, novel problems.

The user can choose:

```text
Near transfer
Medium transfer
Far transfer
Exam simulation
Research-style question
Teach-back
```

## 6. Source Library

The user uploads:

* PDFs,
* notes,
* lectures,
* problem sets,
* textbook chapters,
* videos,
* slides.

The app extracts:

* concepts,
* definitions,
* examples,
* likely prerequisite graph,
* practice items,
* misconception checks.

---

# 12. MVP Scope

## MVP should include

1. User-created topics
2. AI-generated flashcards and cloze prompts
3. FSRS-style spaced scheduler
4. Practice attempt logging
5. Confidence rating
6. Error tagging
7. Worked example → retrieval pipeline
8. Interleaved review sets
9. Daily queue
10. Basic AI tutor with hint ladder
11. Concept mastery dashboard

## MVP should not include yet

* Full video motor-skill analysis
* Deep knowledge tracing model
* Social learning features
* Classroom/instructor dashboards
* Wearable/sleep integrations
* Complex graph curriculum optimization

---

# 13. V1 Features

After MVP:

1. **Concept graph**
2. **Prerequisite-aware scheduling**
3. **Transfer-readiness score**
4. **AI oral exam mode**
5. **PDF/lecture ingestion**
6. **Mistake notebook**
7. **Custom domain templates**
8. **Language pronunciation feedback**
9. **Code execution sandbox**
10. **Whiteboard/photo solution grading**

---

# 14. V2 / Research-Grade Features

## 1. Knowledge tracing model

Use a hybrid model:

```text
FSRS for item memory
+
Bayesian/IRT model for concept mastery
+
LLM-evaluated solution-process signals
+
Graph neural network or transformer over concept dependencies
```

Recent knowledge tracing research increasingly focuses on modeling richer learning states and, in newer work, using problem-solving process data rather than correctness alone. ([arXiv][6])

## 2. Curriculum optimizer

Represent curriculum as a graph:

```text
Concepts = nodes
Prerequisites = edges
Practice actions = interventions
Mastery = belief state
Next activity = policy action
```

Then the app can optimize:

```text
maximize long-term mastery
subject to available time, fatigue, deadlines, and prerequisite constraints
```

A recent 2026 curriculum-optimization system for 9-1-1 call-taker training uses probabilistic beliefs over trainee competence and selects scenarios using bandit-style curriculum optimization, which is directionally similar to what this app should eventually do. ([arXiv][7])

## 3. Multimodal deliberate practice

For dance/esports/music:

* video comparison,
* pose/audio/telemetry analysis,
* expert model imitation,
* external-focus feedback,
* feedback fading,
* transfer retests without augmented feedback.

---

# 15. Recommended Tech Stack

## Frontend

* Next.js
* React
* TypeScript
* Tailwind
* shadcn/ui
* TipTap or Lexical editor for notes
* KaTeX/MathJax for math
* Excalidraw-style whiteboard

## Backend

* Python FastAPI or Node/NestJS
* PostgreSQL
* pgvector for semantic search
* Redis for queues
* Celery or Temporal for background processing
* S3-compatible storage for uploads

## AI layer

* RAG over user notes
* LLM for:

  * practice generation,
  * Socratic tutoring,
  * solution critique,
  * error classification,
  * concept extraction.
* Verification tools:

  * SymPy for math
  * Python sandbox for code
  * unit tests for programming tasks
  * source-grounded answer checking

## Scheduling engine

* FSRS implementation for recall scheduling
* Custom mastery model for concept-level adaptation
* Later: knowledge tracing model

---

# 16. Example User Flow

## User goal

“I want to learn linear algebra deeply for ML.”

## App flow

### Day 1

The app asks:

```text
What is your target?
- Pass exam
- Build research-level intuition
- Prepare for ML
- Refresh old knowledge
```

User selects:

```text
Prepare for ML
```

The app creates modules:

```text
Vectors and spaces
Linear maps
Matrix multiplication
Rank/nullspace
Eigenvalues/eigenvectors
Diagonalization
SVD
PCA
Optimization connections
```

### First session

The app gives:

```text
Worked example: matrix as linear transformation
Completion problem: identify image of basis vectors
Retrieval: define column space
Reflection: explain why matrix multiplication composes maps
```

### Later session

The app notices:

```text
You can compute eigenvectors, but you do not reliably know when eigenvectors matter.
```

It schedules:

```text
Interleaved discrimination:
- eigenvectors
- singular vectors
- principal components
- nullspace basis
```

### After repeated success

The app schedules:

```text
Transfer challenge:
Explain why PCA can be derived from the SVD of centered data.
```

---

# 17. Differentiation from Existing Apps

## Not just Anki

Anki schedules cards. LearnLoop schedules **learning actions**.

## Not just Duolingo

Duolingo is domain-specific. LearnLoop is domain-general and concept-aware.

## Not just ChatGPT

ChatGPT explains. LearnLoop tracks mastery, schedules retrieval, forces reconstruction, diagnoses errors, and reduces over-reliance.

## Not just a course platform

Courses are linear. LearnLoop is adaptive, error-driven, and retention-aware.

---

# 18. Key Metrics

## Learning metrics

* Delayed recall accuracy
* Transfer problem accuracy
* Error recurrence rate
* Time-to-solve
* Hint dependence
* Confidence calibration
* Retention after 7/30/60 days
* Explain-from-memory score

## Product metrics

* Daily active learners
* Session completion rate
* Review adherence
* Long-term retention
* User-generated content reuse
* AI feedback helpfulness
* Reduction in repeated errors

## Anti-metrics

Track things you do **not** want to optimize blindly:

* Time in app
* Number of cards completed
* Immediate accuracy only
* AI explanation consumption
* Streaks without mastery

The app should optimize learning, not addiction.

---

# 19. The Most Important Design Decision

The app should classify every learning activity into one of these modes:

```text
Encoding
Retrieval
Relearning
Discrimination
Transfer
Fluency
Reflection
Repair
Observation
Performance
```

Then it should ask:

```text
Which mode does this learner need next?
```

That is the central intelligence of the product.

---

# 20. MVP Build Plan

## Phase 1: Core learning engine

Build:

* learning objects,
* attempts,
* FSRS-style scheduling,
* daily queue,
* retrieval cards,
* confidence rating,
* basic error tagging.

## Phase 2: AI practice generation

Add:

* upload notes,
* extract concepts,
* generate questions,
* generate cloze prompts,
* generate worked examples,
* generate transfer problems.

## Phase 3: Error-driven adaptation

Add:

* mistake notebook,
* error taxonomy,
* targeted repair drills,
* interleaving engine.

## Phase 4: Concept graph

Add:

* prerequisite graph,
* concept mastery map,
* transfer-readiness score.

## Phase 5: Domain modules

Add templates for:

* math/proofs,
* language,
* coding,
* puzzles,
* motor skills.

---

# 21. Concise Product Definition

**LearnLoop is an adaptive learning system that turns notes, problems, videos, and goals into a personalized sequence of worked examples, retrieval prompts, interleaved drills, transfer challenges, and error-repair loops, scheduled by both memory science and mastery modeling.**

The strongest version is not a prettier flashcard app. It is a **closed-loop tutor**:

```text
Attempt → diagnose → feedback → schedule → retest → transfer → consolidate
```

That loop is the product.

[1]: https://www.sciencedirect.com/science/article/pii/S2666920X25001699?utm_source=chatgpt.com "Large language models in education: a systematic review ..."
[2]: https://github.com/open-spaced-repetition?utm_source=chatgpt.com "Open Spaced Repetition"
[3]: https://research.duolingo.com/papers/settles.acl16.pdf?utm_source=chatgpt.com "A Trainable Spaced Repetition Model for Language Learning"
[4]: https://arxiv.org/abs/2201.06953?utm_source=chatgpt.com "[2201.06953] Knowledge Tracing: A Survey"
[5]: https://education.purdue.edu/news/2026/03/11/artificial-intelligence-in-literacy-education/?utm_source=chatgpt.com "Artificial Intelligence in Literacy Education"
[6]: https://arxiv.org/abs/2501.14256?utm_source=chatgpt.com "Revisiting Applicable and Comprehensive Knowledge Tracing in Large-Scale Data"
[7]: https://arxiv.org/html/2603.05361v1?utm_source=chatgpt.com "PACE: A Personalized Adaptive Curriculum Engine for 9-1- ..."
