# Semantic judgments by the Decider (draft v1)

Status: draft for the owner's review, 2026-11-18. Nothing here is built. Sections 2 to 5 follow the owner's decisions of that day; section 5a holds proposals the owner has not yet answered. Source: the owner's requests of
2026-11-18 and a read-only survey of the code the same day (the survey's call-site tables are the reference for
file and line; this spec states the design).

## 1. What this replaces

LearnLoop decides several questions about meaning by counting shared words:

- whether help showed the learner part of the answer (token overlap with the answer key);
- whether a Teacher reply gave away an open lesson check (the same overlap, against the committed solution);
- whether a Reader answer exposed a reserved question (word-pair overlap);
- whether a follow-up item needs fresh work (equal surface group ids);
- which skill a rubric criterion measures, when the item has no explicit mapping (shared words between the
  criterion's text and facet ids).

Each is wrong in both directions. A paraphrased solution scores low. A reply that repeats the question's own
words, or confirms a step the learner already wrote, scores high. The cost is real: any positive overlap is
recorded as a reveal, a sum of 0.35 marks the attempt as primed, and one small recorded reveal on a cold item can
fail its coldness check. The 0.8 threshold only sets a flag.

The Decider is a small, cheap model that answers closed questions (one of several named options, or a selection of
ids). It already judges gap matches, misconception matches, diagnosis links and the offline contamination report.
This spec gives it the questions above.

## 2. Owner decisions (2026-11-18)

1. The Decider adjudicates whether help showed a step the learner was meant to produce: for clarification,
   verification and other hints. It compares what the learner actually saw with the question stem and the
   grading rubric. For each rubric criterion it marks as revealed, it quotes the text that gave it away.
2. Until the Decider's verdict arrives, and when it does not answer, the word count stays in force.
3. The learner is shown the quote in feedback.
4. Before anything changes, the Decider is run over tutor replies already stored, to measure how often it
   disagrees with the word count (model calls on backup copies of the owner's vaults, through the Decider's own
   route; it is not on the ChatGPT plan).
5. The same treatment for: a Teacher reply and an open lesson check; whether a follow-up is actually new; which
   existing facets a rubric criterion tests; whether a Reader answer exposed a reserved question.
6. The offline contamination report selects rubric criterion ids directly.
7. One shared answer-reveal judgment for Ask, Teacher, generated hints and the rest.

## 3. Rules

- R1. The learner never waits for the Decider. A deterministic value is recorded at once and is in force until a
  complete verdict arrives.
- R2. A rebuild never calls a model. It reads what was stored.
- R3. Every quote is checked: it must be an exact slice of the text that was displayed, or it establishes
  nothing. (Stricter than the grader's located errors, which fold case and spaces.)
- R4. Guards that run before text is shown stay as they are: withholding a passage, refusing a hint that states
  the answer, excluding solution blocks. A late verdict cannot take text back.
- R5. The Decider may answer "cannot tell". That is an answer, and the deterministic value then stands.
- R6. A decision that has been used is frozen with the value that was in force when it was used (a submitted
  attempt, a coldness receipt, a withdrawn check, a burned reserve). A later verdict explains the display and
  affects decisions still open. It does not rewrite a finished one; a disagreement goes to a review list.
- R7. A verdict is applied once: a retry or a duplicate must never charge a reveal twice, and the semantic
  amount is never added on top of the word count.
- R8. No new hand-picked threshold. The first rollout keeps today's accumulation rule so stored meaning does not
  move; section 6 replaces it.

## 4. The shared answer-reveal judgment

One function: `judge_answer_reveal(display, protected, prior_work)`.

- **display**: the ordered pieces of text the learner got (reply, bridge, excerpt, opened citations, a hint's
  body, a figure's words and values), each with a stable id. Every display gets an id, including one whose word
  count is zero. Today a zero writes no reveal row, so a paraphrase found later has nothing to attach to.
- **protected**: the item's revision, its public stem and givens, and its protected parts. For an item: the
  rubric criteria by id with their points. For a lesson check with no usable criteria: its committed solution as
  one part. For a reserved question: two parts, the question's identity and its answer, because a paraphrase of
  the question spoils it without revealing a solution.
- **prior_work**: what the learner had written before this display (the draft at the time of the question, not
  the answer submitted later, which would leak hindsight).

For each protected part the Decider is asked: given the public question and the learner's work before this
display, which displayed passage first supplies this part, or confirms an answer the learner had not settled?
Options: a passage id, "not revealed", "cannot tell". Confirming a tentative guess is new information. Repeating
a given, or reasoning the learner already wrote down, is not.

The result per part: the criterion id, the verdict, the passage, the exact quote and the judgment's id. The
judgments go to the judgment ledger; one measurement record ties them to the display and to the word count taken
at intake.

**The amount.** For an item, a complete verdict is the share of the rubric's points newly supplied. A part
counts once across prose and citations, and once across turns. If any part is unresolved, or the prior work
cannot be reconstructed, the word count stands. A complete negative verdict replaces a false positive.

**Who supplies what** (each surface is an adapter to the one function):

| Surface | What it must bring that it does not pass today |
|---|---|
| Ask tutor, bound Reader | The draft before the reply; the exact visible prose, bridge, excerpt and opened citations |
| Generated hints, Workbench, figures | The shown version of the hint or figure readout; the retained draft (marked when truncated). For a figure the verdict covers its words and values, not its geometry |
| Teacher, open check | The check's question, committed solution and rubric; the learner's turns before the help. The check's identity is re-read before a late withdrawal |
| Reader reserve | The reservations in force when the answer was displayed. An explicit declaration or an exact identity hit stays decisive. A late positive burns a reserve that is still eligible; a late negative restores nothing |
| Displayed repair, source review | The repair's actual wording, kept apart from its declared budget |
| Contamination report | The protected rubric with criterion ids (today it passes descriptions only) |

## 5. The other two questions

**Is this follow-up fresh work?** "Having seen the source item and its solution, could the learner complete this
item by carrying over the answer or the solution steps with only surface substitutions?" Options: carryover,
fresh work, cannot tell. Asked once per pair of item revisions, when the follow-up is generated or commissioned,
never at serve. Until answered, the group-id rule stands. The verdict is frozen into the attempt's
classification when it is made. This changes which new attempts can verify a capability; it does not change the
repeat discount or the grouping of old evidence (that would need an algorithm tag).

**Which facets does this criterion test?** "Which of these existing facets must a learner exercise to earn this
criterion's points?" Options: the item's facet ids (several allowed), none, cannot tell. Asked once per item
revision at creation, revision or import. Authored mappings are kept; no facet is ever created here. The mapping
is frozen into the next presentation's assessment contract before the learner answers, so grading, diagnosis and
replay read the same one. Old answers keep the mapping they were graded with. The same request checks that a
generated probe's rubric really requires its declared target.

## 5a. Source passages and margin cues (owner's request of 2026-11-18; the five changes below are proposed and await the owner)

The owner's request: source reranking and Reader margin cues should be done by the Decider. For source passages,
classify the batch and select passage ids, with a separate choice for whether a relevant passage gives away the
active exercise. Use the same thing to let the learner query all their sources in plain language from the Reader.
For margin cues, the Decider identifies the relation and lists the passages; the learner-facing explanation is
generated and the verified quote extracted only for the selected cues.

Today one shared listwise judge (`practice_index/listwise.judge_listwise`) serves six jobs with a full model. For
margin cues it writes a relation, a rationale, a copied quote and role labels for every one of up to twelve
passages per target, then picks at most two.

Proposed shape:

1. The Decider sits inside the shared listwise judge. Each job declares its closed vocabulary; the Decider
   answers first, and the current model is asked only when the Decider does not answer (as the contamination
   report already works). All six jobs get it through one seam.
2. The Decider selects; it does not rank. Each passage is judged relevant or not (and, for cues, which relation),
   the search order is kept among those selected, and a job that needs a top pick asks one more "which is best".
3. The quote is a sentence the Decider picks by number, so it is exact by construction. The writing model writes
   only the explanation, for at most two cues per target.
4. The give-away choice is the shared answer-reveal judgment with the active exercise as the protected thing.
   At first it may only withhold: a Decider "gives away" adds to today's word-overlap guard. Whether a Decider
   "safe" may release a passage the guard withheld waits for the measurement.
5. Measure before switching: the full model's judgments are stored, and `learnloop decider agreement` compares
   the Decider with them on the same inputs.

Search across sources: the existing word and vector search builds the shortlist, the Decider selects from it,
and the results are passages (never a generated answer). The shortlist passes the same exclusions as every other
reader of sources (held-out exam material, solutions, reserved questions) before the Decider sees it.

To watch: the tutor's passage check runs while the learner waits for a reply, so its timing is confirmed before
that job switches.

## 6. Stages

| Stage | What | Size | Tag |
|---|---|---|---|
| DJ0 | Measure on stored tutor replies: per-criterion verdicts against the 0.8 flag, the amount and the 0.35 outcome; both directions; unanswered; missing context; a small set the owner reviews. Writes nothing live | S | no |
| DJ1 | The shared module, display ids, the measurement record; Ask tutor and bound Reader; the quote in feedback | M | no (new events only) |
| DJ2 | Criterion to facet mapping; generated probe target check | M | no (new presentations) |
| DJ3 | Follow-up novelty | M | no (new classifications) |
| DJ4 | Hints, Workbench and figures; "did this reply actually help" replaces the question-type rule for hint counting | M | no |
| DJ5 | Teacher open check; Reader reserve; displayed repair | M | no |
| DJ7 | The listwise seam (section 5a): the Decider classifies and selects inside the shared listwise judge; margin cues, Find Sources, the tutor's passage check, practice reranking, solution matching and worked-example equivalence get it at once. Proposed, awaiting the owner | M | no |
| DJ8 | Natural-language search across all sources in the Reader (section 5a). Proposed, awaiting the owner; its screen belongs to the Reader redo | M | no |
| DJ6 | Per-criterion consequence: a revealed criterion earns no cold credit and the rest of the answer still counts, replacing the summed amount and its 0.35 rule | M | yes |
| Later | The survey's remaining candidates, in its order: duplicate exercises at import, replacement hint strategy, practice diversity, diagnostic item properties, facet mint or alias, exam import work, source block roles | S to L | mostly no |

DJ1 to DJ5 share one batch runner keyed by revision, with reuse of recorded answers, "cannot tell", validation of
the ids offered, and the receipt of which value was in force when a decision was made.

Placement: DJ0 can run now. DJ1 after arc G's G1. DJ6 belongs with the evidence packet spec, whose reveal events
it annotates.

## 7. Not here

Guards before display; exact quotation and symbolic checks (done in code); retrieval shortlists; the router's
arithmetic; explicit learner actions (a button, a submitted reply, an opened hint); anything inside a rebuild or
on a keystroke; report-only editorial flags.

## 8. Open questions for the owner

1. DJ6: should a revealed criterion simply earn no cold credit while the other criteria count in full, or should
   the whole attempt still be marked as helped when most of the rubric was shown?
2. R6: a verdict that arrives after an attempt was submitted and disagrees with the word count goes to a review
   list and changes nothing. Or should it reinterpret the attempt (this needs a correction design and a tag)?
3. Calls: one batch per item-bound tutor reply, per shown hint and per help reply in a lesson. Is any surface
   to be left out to save plan usage?
