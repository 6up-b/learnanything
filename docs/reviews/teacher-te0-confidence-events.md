# Teacher TE0: confidence as events in model contexts and on the router card

Stage `teacher-te0`, branch `teacher/te0` in `learnanything-dl2`, base `e9d4de1aa` (main with T1, AD2+AD3 at
mvp-0.30, RW2d at mvp-0.31, local retrieval P1; migration head 220). Spec: `docs/specs/spec_teacher_v1.md` §0 item 4,
§5.2, §15.2 and §20's TE0 row ("None (context and card only)").

## 1. What changed

One shared module, `learnloop.confidence_events`, reads the two existing readings and renders them as **events in
words with the outcome**. It never renders a raw scalar or a threshold count.

* **The tap.** The source is `practice_attempts.answer_confidence` (1–5, migration 031).
* **The hedge read.** The source is `grading_evidence.learner_confidence` on the attempt's current (unsuperseded)
  rows.
  * A row counts only if it was read as `hedged` or `confident`. `absent` and `unknown` say nothing.
  * An attempt whose criteria were read both ways is "parts of the answer as hedged". No threshold is involved.
  * Rows written from a stated number are not hedge reads (`NOT_GRADER_READS`). These are a self-grade (`self`), an
    imported exam outcome (`exam_import`) and a simulated grade (`sim`).
* **Events**, for example:
  * "marked 5/5 sure; wrong"
  * "no tap; the grader read the answer as hedged; right"
  * "marked 4/5 sure; the grader read parts of the answer as hedged; partly right"
  * "marked 3/5 sure; held for review (no score yet)". The held predicate is THE predicate; a held grade never shows
    a score.
* **The stated limit** (`taps_limit`), for example "your taps so far are all 4–5 (29 taps)".
  * It appears whenever the taps so far do not span the tap's own 1–5 scale. The scale bounds are structural, so no
    constant decides what spread is enough (see open question 1).
* **Readers.**

  | Reader | What it gets | Without confidence data |
  |---|---|---|
  | **Router card**, `learner_state_card_v2` (`router/card.py`, gathered in `daily_plan/router_card.py`) | Each recent-work line gains its event. A typed section `confidence_7d` lists the candidate topics' events in the card's 7-day window, newest first, each with its own outcome. `confidence_limit` carries the limit | `CARD_VERSION` is `learner_state_card_v2` (`PREDECESSOR_CARD_VERSION` is v1, and `AD_CARD_VERSION` is now `v2+ad23`). The card's text and every typed field are byte-identical to a v1 card's. Only the version label differs. This is pinned by hashes of a v1 card built by the base commit's builder |
  | **History-aware diagnoser** (`diagnosis/split`) | `HistoryAttempt` gains `answer_confidence` and `confidence_event`. A blind-overlaid attempt takes the blind record's own read; a joint one takes the current grading evidence. Each rendered history row (and its snapshot export file) gains `confidence`. The diagnosed attempt gains a `confidence` block (version, note, event, taps so far) from `live.current_confidence` | Renders and hashes exactly as before (the stuck-reading and workbench-trace precedent). `DIAGNOSIS_PROMPT_VERSION` and `DIAGNOSIS_CONTEXT_VERSION` are unchanged: the block carries its own `version` (`confidence-events-v1`) and the context hash is content-addressed |
  | **Hint writer** (`hints/writer.build_prompt`, read once per request in `hints/service._write`) | `learner_confidence`: the topic's events, newest first, bounded at `CONTEXT_EVENT_LIMIT` = 12 per topic (a prompt-size bound, `keep`) | The prompt is unchanged. The Decider's state and `state_hash` are untouched |
  | **Tutor** (`tutor_qa._build_context`, practice, feedback and library contexts) | `TutorQAContext.learner_confidence` | `None`, which `tutor_context_payload` drops, so the prompt and `input_context_hash` are as before. The Reader context never carries it (§4, open question 2) |

  The teacher contexts do not exist yet (TE1). `learner_events` is the block `LessonBriefV1` can take.
* **Never the grader.**
  * Nothing in `learnloop.attempts` imports `learnloop.confidence_events`. A new import-linter contract,
    `graders-never-read-confidence-events`, pins this, and an AST test pins it for `blind_grading.py` and
    `grading.py`.
  * `BlindGradingContext` has no field for confidence, and a test pins it.
  * A blind-grading prompt built in a vault whose prior attempt is "marked 5/5 sure, hedged, wrong" contains none
    of it.

## 2. Protection

* **The hint writer and the tutor** read through the shared protection (`learner_protection.withheld_items` and
  `attempt_protection`).
  * An attempt on exam or held-out material, exam work, a reserved surface, an item a check or a cold retry holds,
    or a diagnostic probe contributes no event.
  * When the protection cannot be read, no event shows at all (fail closed).
  * The protection is read only when the topic has some confidence data. A topic without any costs one query and
    no protection read.
  * The block names no question, no answer and no score.
  * Protected attempts' taps still count toward the vault-wide "taps so far" limit. That is only a number, with no
    item, result or text (open question 5).
* **The router card** keeps its own rule, which predates TE0: protected past work keeps its result and shows no
  question and no answer. Its event (tap, hedge read, result) stays with it, because the event carries no more than
  the result the card already shows. A test checks that an exam attempt's event is shown while its answer text is
  not.
* **The diagnoser** is history-aware: it already reads every measuring attempt and the reference solution. TE0 adds
  only these measurement fields. Its records carry no diagnosis prose, as before.
* **The MCP chat read model** (`learner_context.learning_context`) is unchanged. The spec lists no chat consumer for
  TE0, and C1a's narrow text guard applies.

## 3. Playbook review: does TE0 change persisted meaning?

Checked against `docs/algorithm-change-playbook.md`. **No successor**, which confirms the spec's 2026-10-24 default.

1. **Scoring, scheduling, projections, admissibility.** None of these reads anything new.
   * There is no migration, no new table, no config key and no default change.
   * Every `table_roles` classification and every defaults snapshot is unchanged.
   * Replay and rebuild never read the card, a model context or `confidence_events`.
2. **The card version.**
   * `card_version` is stored with each decision's card payload (`router_decision_payloads.format_version`) and its
     hash. It is display and provenance only: `plan_log` shows it as `format_version`, and `learnloop router card`
     prints it.
   * No code branches on it.
   * The mixture design's sampling and its logged propensity, the staged frame's feasibility and the rule's
     choices read the candidates, not the card's version.
   * The similar-decisions retrieval embeds `router_retrieval.context_text` (session, candidates, topics and open
     problems). That text reads neither `recent_work` nor the new section, so v1 and v2 decisions stay comparable
     in that index.
3. **Served decisions.**
   * The 2026-10-17 rule (one eligibility decision, mvp-0.27) makes a change to which items are served as
     measurements, or to which attempts are primed, a successor. TE0 changes neither: eligibility, priming and the
     feasible set are computed before the card is built.
   * What changes is a model input: the router models', when confidence data exists. That input already changes
     with every new attempt.
   * The diagnoser's, the hint writer's and the tutor's model inputs also change, and only when data exists. Their
     outputs are recorded with content-addressed context hashes and keep their meaning:
     * a hint is help, never evidence;
     * a diagnosis is a typed proposal its validators check;
     * the tutor's question classification (whether a question is hint-equivalent) is read from the question as
       before.
   * This is the same class of change as RW2b's workbench trace in the diagnoser context, which landed without a
     successor.
4. **No learned weight.** No weight, margin or threshold is introduced. The constants are:
   * `TAP_MIN`/`TAP_MAX`: structural, the tap's own scale;
   * `CONTEXT_EVENT_LIMIT`: a prompt-size bound, `keep`.

   None is a config key, and none of the touched modules is in the parameter registry's `MODULE_INVENTORY`, so the
   registry is unchanged. The tap/hedge recalibration is LP-min, later.

## 4. Gate

The commands, pass counts and the list of test files run are recorded at the end of this file (§6).

* **Paid calls:** none.
* **Live calls:** none.
* **Manual runs:** none. No `fixtures-local` copy was needed: the stage has no paid command, and the fakes cover the
  interfaces.
* **Ad hoc Python:** the only Python run outside pytest was a stdlib-only parity script under `env -i` with an empty
  `HOME`. It computed the v1 golden from the base commit's `router/card.py`.

## 5. Open questions for the owner

1. **The limit's rule.** The limit is stated whenever the taps do not span 1–5, so "all 4–5", "all 2–5" and "all 5"
   are each stated, and taps that include both 1 and 5 are not. This rule needs no made-up spread threshold. If the
   owner wants it only for a narrower band, that band is a choice the spec would need to name.
2. **The Reader tutor.** The Reader tutor (`context == "reader"`, with or without retrieval) gets no confidence
   events. Its manifest (design A.2) excludes any learner ability reading, and an event carries a past outcome.
   §15.2 says "tutor contexts". Should the Reader tutor be included?
3. **No kill switch.** The spec names none for TE0. It is a context-only change, and every reader renders as before
   without data. A `teacher.confidence_events.enabled` switch would add a config key to every defaults snapshot.
4. **The card's 7-day section is unbounded within the window.** It is a typed field, so it never drops under
   `router.card_token_budget`: the budget drops recent work first. A heavy week could therefore push the card over
   budget. A per-topic bound like the hint writer's is easy to add if wanted.
5. **The scope of "taps so far".** It counts every tap before the context's cutoff, vault-wide, including taps on
   protected attempts (as numbers only). The alternatives are to restrict it to unprotected attempts, or to the
   context's topics.
6. **Self-grades.** A self-grade's `learner_confidence` is derived from the learner's self-grade confidence. It is
   treated as neither a tap nor a hedge read. Should it be rendered as its own event ("self-graded, sure")?
