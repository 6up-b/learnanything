# Evidence packets (EP): one view of the learner's evidence for every model

Facts in place of "assisted", hypotheses as claims with their context, the Decider and the action model on the same evidence, the Decider as a helper that annotates the packet, one rule for time with its two axes named, and forecasts kept with what they were made from so model quality can be scored later.

**Status:** draft, Nov 16 2026, for the owner's review. Revised on 2026-11-17 after two independent reviews against main `88b10fb90d`. Not queued. The owner agreed on Nov 16 to the shared read model this spec is the first slice of, and to Part E's time rule with named reads (§7). On Nov 17 the owner decided that prediction snapshots are built as part of this spec (§7.7). Evaluated in `docs/reviews/refactor-strategy-v3-audit-2026-11-16.md` §4.2-§4.4.

**Depends on:** the audit's P1 (a record of what a model was shown), which is EP2 here; E7b (`learner_signals` ahead of arc E) for EP4. EP2s edits status writes in `db/repositories.py` and comes after the refactor's L2 splits that file into stores. EP0, EP0t and EPp can run before any of these.

**Amends:** `spec_slip_vs_gap_v1.md` §3 item 3 ("never the hypothesis statements"), for the action model, if the owner says yes to Q3 and only after ledger row SR-1 is closed. It builds on `spec_learner_input_after_miss_v1.md` §7 and contradicts nothing in it.

## 1. The owner's words (Nov 16 2026, verbatim)

> Another issue I wanted to bring up that you should spec out is revising the Decider model prompt and the GPT prompt to be able to retrieve most of the same information so we can compare them. Another idea though that I'm starting to think is better is that since Decider models are so cheap, we could use them within a harness in the action router to help build better packets/construct histories that are sent to the LLM. I would also replace ambiguous "assisted" label with seperate recorded facts. Hypotheses should be claims that need context in the packet, like what observations supported the hypothesis, when it was last supported, which attempts bear on the same skill, whether those later attempts were independent/repeated/assisted. I'm fine with also increasing the GPT token input a bit also (considering we're using bytes and not tokens anyway). Our current action model feels pretty good, so we don't want to pigeonhole it too much by depriving it of good information either.

Standing rules that bind this spec: only the grader is blind; learner data goes to a model whenever it helps (owner, Nov 1). Weights and thresholds are learned from seeded, stated priors (Oct 24). Decisions are inspectable from stored rows. The learner's narrowing reweights and never removes (Nov 9). No shadow stages. A new successor ships with no kill switch unless the owner asks (Nov 16). Pure moves are proved by an AST identity check and the gate. Learner data stays local; the repo is public.

## 2. In plain words

1. **An attempt carries what actually happened around it**, in words a model can read: which hint, how far in; whether the answer was shown before; first time on this item or family; how long it took; why it came up. The one word "assisted" stops standing for all of them.
2. **A hypothesis arrives with its case file:** what raised it, which observations actually tested it and how, and what you've done on the same skill since.
3. **The Decider and the action model read the same evidence**, so where they answer the same question, comparing them compares the models.
4. **The Decider, being nearly free, reads pairs** (this answer, this hypothesis: does one bear on the other?) in the background. Its labels are shown in the packet; it never removes anything.
5. **What a model was shown is recorded** as a small manifest over payloads LearnLoop already keeps.
6. **Every read says how it treats time:** which events it admits (happened before a moment, or also known by then) and which corrections it applies (today's, or those made by then).
7. **Every forecast is kept with what it was made from** (cutoff, target, distribution, provenance), so model quality can be scored later without reconstruction.

## 3. Part A: attempt facts

### 3.1 Today (checked)

There is no raw attempt-level "assisted" flag. It is derived on read from `attempt_type`, `hints_used` and `primed`, in at least twelve places that disagree (`docs/reviews/refactor-strategy-v3-audit-2026-11-16.md` §4.3 has the table; the canonical one is `diagnosis/causal_activity_policy.py:168`). Three derived values are stored: `facet_outcome_observations.assisted` and `.primed` (`migrations/180_daily_plans.sql:70-85`, a DERIVED table written only by the rebuild: `db/stores/field.py:12-21`, `substrate/rebuild_orchestrator.py:465-468`), `certification_cold_probes.assisted` (`migrations/139_certification_cold_probes.sql:177`) and the retrieval interventions' `next_assisted` (`migrations/193_retrieval_interventions.sql:61`). Two packets tell a model `assisted = primed` with the hint count in the next field (`learner_context.py:1389`, `daily_plan/router_card.py:818`). The diagnoser gets `assisted` and `primed` as bare booleans its prompt never defines (`diagnosis/split/context.py:476`).

The inputs are collapsed too: hint levels 1-3 become a count and levels 4-5 become `primed`; a figure counts as a hint; a reveal total of 0.35 or more forces `primed` (`db/stores/help_assists.py:262-280`, `attempts/attempts.py:2436`). Some facts are less certain than their names: a server hint can be prepared and never shown (`help_assists.py:177`) and attaches to its attempt later by submission key (`:95-110`); `first_hint_progress` can be absent; an answer-display receipt is written before rendering and renewed while on screen, so it records coverage, not reading (`attempts/reveal_ledger.py:534-550`); the coldness check returns a dimension with evidence, not a boolean (`attempts/coldness_receipt.py:1457`); the FSRS cap needs the item's hint policy.

The facts underneath are already rows:

| Fact | Where it is stored |
|---|---|
| Each hint, check, figure or other assist: kind, level, when requested, whether and when shown, the work's length at that moment | `help_assists` (append-only, since migration 210) |
| Each time the answer or part of it was shown: source, amount, when | `reveal_events` (append-only) |
| Whether the first hint came before or after a draft | `practice_attempts.first_hint_progress` |
| A question to the tutor during the attempt, and whether it was hint-equivalent | `question_events` |
| "Don't know", "stuck" | `practice_attempts.declared_dont_know`, `declared_stuck` |
| Response time and active seconds | `practice_attempts.latency_seconds`, active seconds (migration 252) |
| Which presentation the attempt answered, and when it was presented | `probe_presentation_id`, `plan_presentation_id`; `plan_presentations` |
| Why it came up: a randomized check's assignment and its probabilities, a scheduled due date, the learner's pick | the checks' assignment rows (`router_objective/checks.py:140-160`), `scheduler_slate_candidates`, `scheduler_offer_receipts` |
| Earlier attempts on the item, its surface group and its learning object | `practice_attempts`, and derived at read by `field.outcomes.load_attempt_rows` |
| Reading on the topic before the attempt | `reading_exposure_receipts` |

`field/outcomes.py:100-150` derives a serving origin per attempt and no propensity, since no producer proves one. `adaptive_difficulty/outcomes.py` already works the way this part proposes: `AttemptFacts`, then named functions over it.

### 3.2 The facts

One frozen dataclass, `AttemptFacts`, built in two halves (`attempts/facts.py`):

- **Collection**, `collect_facts(reader, attempt_ids, cutoff)`, reads through a reader that carries visibility: AD passes its material view, so withheld exam material stays invisible as in its replay (`adaptive_difficulty/replay.py:331-345`, A8); others pass the connection. `cutoff` is a `Cutoff` (§7.2).
- **A draft form**, `facts_from_draft(draft)`, for the submission path, before an attempt id exists.

No migration and no new table.

| Field | Values |
|---|---|
| `produced_as` | the stored attempt type |
| `hints` | per hint: kind, level 1-5, `requested_at`, `shown` (and when), `before_work` / `after_work` / `unknown`, seconds before the answer |
| `checks`, `figures` | counts of "check my work" and figures, requested and shown |
| `tutor_questions` | count, how many were hint-equivalent, before or after work |
| `shown_before`, `shown_during` | per source: how much of the answer was displayed before the serve (and how long before) or between serve and answer, as display coverage |
| `item_history`, `family_history`, `topic_history` | which time on this item and surface group; time since the last; whether the last feedback was displayed; time since the last exposure of any kind on the learning object |
| `declared` | don't know, stuck |
| `timing` | presented, submitted, elapsed and active seconds, each with `observed` true or false |
| `answering` | an ordinary serve, a probe, a cold check, an exam attempt |
| `delay_source` | why the item came up when it did: `randomized_check` (with the assignment id, topic and item probabilities), `scheduled`, `learner_pick`, `unknown` |
| `pre_exposed`, `bound_presentation`, `correctness`, `forced_failure` | as adaptive difficulty reads them (`adaptive_difficulty/outcomes.py:60-71`, `replay.py:271-277`), so the dataclass is a superset of AD's |
| `detail` and `coverage` | `full`, or `counts_only` for an attempt older than `help_assists`; and per field, whether it was captured, with the source row ids |

**Nothing is inferred backwards.** An attempt from before migration 210 has its hint count and `primed` and says so. A submitted count or flag is kept verbatim beside the rows it summarizes; where the two disagree, both are shown.

### 3.3 The categories stay, as named functions

Each reader that needs a yes or no keeps it, as a function over `AttemptFacts` with the arguments its copy needs today, all in one module (`attempts/fact_predicates.py`):

| Function | Who reads it | Today's copy it replaces |
|---|---|---|
| `counts_as_assisted` | the canonical projection, the facet timeline, certification's cold probe | `causal_activity_policy.attempt_counts_as_assisted` (its bytes kept: `causal_activity_v1`) |
| `unassisted_for_coldness(facts, window)` | the coldness receipt; returns the dimension with its evidence, as today | `coldness_receipt._unassisted` |
| `help_timing`, `outcome_category` | adaptive difficulty | `adaptive_difficulty/outcomes.py` (moved, not changed) |
| `independent_for_outcomes` | intervention outcomes, slip-or-gap's fit | `intervention_outcomes.is_assisted` |
| `fsrs_rating_cap(facts, hint_policy)` | the grade application | `attempts.py:5726` |
| `cold_and_unassisted` | the diagnoser's "demonstrated" | `split/history.py:227` |

EP0 moves each copy to its function with its value unchanged (AST identity and the gate), so twelve derivations become six named ones in one file, and each stored `assisted` column above is documented as the output of one of them. Where two copies that claim to mean the same thing differ (open-text answers counted as assisted in one, any reveal at all in another, primed-only in the two packets), the step names the difference on the bug ledger and doesn't pick a winner.

### 3.4 What a model is shown

A line of facts per attempt, and one legend per packet that defines every term used. In a text packet:

```
Nov 9 · eigenvalues · item 2nd time (3 days ago, feedback shown) · family 4th time · correct
       help: hint level 2 after starting; answer not shown · answering: cold check · came up: randomized check
```

In a JSON packet, the same fields by name. The words "assisted" and "primed" leave every packet. They stay on screens ("with help ◌"): that wording is the UX audit's.

## 4. Part B: hypotheses as claims

### 4.1 Today (checked)

| Packet | What a hypothesis carries |
|---|---|
| The action model's card (`daily_plan/objective_card.py`) | Nothing. Learner-named gaps, and cause-class probabilities "never the hypothesis statements" |
| The Decider's card (`daily_plan/router_card.py:608`) | `topic: kind (status, since DATE): statement`, and the learner's marks |
| The diagnoser (`diagnosis/split/context.py:504`) | statement, status, a count of evidence, a "last updated" that is the newest version's creation time (Slice 1's S3: typed records with status and evidence counts, never prior prose) |
| Follow-up authoring (`followup_run/authoring.py:175`) | a ref, the statement, the cause scope, the target |
| Chat (`learner_context.py:1119`) | counts for and against, repairs tried |
| A research arm nobody serves from (`field/probability_states.py:587`) | evidence for and against as lists of attempts with days and results, repairs tried |

Durable links between a hypothesis and what tested it do exist. `causal_discriminating_observations` (migration 130) records per probe answer the factor, the diagnosed and answering attempts, the pinned prediction bundles, the match result and whether it was admitted. `causal_cold_verifications` records a repair's result and the diagnosis support apart, and its writer refuses a nonzero diagnosis update resting on repair outcome alone (`diagnosis/causal_probe_coherence.py:1905-1927`). No table holds a "last supported" time. Prior weights are in `causal_hypotheses.evidence_json`, a probe's posterior in `probe_observations`. `facet_outcome_observations`, the first draft's source for "same skill", is written only by the rebuild.

### 4.2 The claim card

One builder (`diagnosis/claims.py`: `claim_cards(reader, cutoff, topics) -> list[Claim]`), a pure function over rows gathered by one read. Every packet above becomes a rendering of it.

| Field | From |
|---|---|
| `ref` | a packet-local name (H1, H2) |
| `statement` | the hypothesis's statement, or "withheld" under the existing rule (`statement_text`) |
| `cause_class`, `status` | `cause_scope`, the lifecycle; with the date of the last status change where §7.4 has it, else "since at least DATE" |
| `raised` | date, and the attempt that raised it |
| `weight` | the diagnosis's prior weight; the probe's posterior if one exists, labelled as that; the learner's latest mark beside them, never folded in |
| `supported_by`, `against` | only observations that tested **this hypothesis version**: admitted discriminating observations whose matched bundle is this hypothesis or a rival, and cold verifications with a nonzero diagnosis delta for it. Each with its date and source row id. A hypothesis with none has empty lists and says "not yet tested" |
| `last_tested` | the newest date in those two lists |
| `context` | everything else that bears on it, listed by kind and not by direction: the raising attempt, recurrences joined to its episode, repairs and their cold results (a successful repair with zero diagnosis delta is listed as a repair, not as support), failed or passed cold checks on its facet, the learner's marks and words |
| `since` | every later attempt that bears on the same skill: date, result, relation to the raising item (same item, same family, another family), and its facts (§3.2) |
| `legacy` | the evidence count and last-updated time the old renderings show, labelled as such, until EP4 removes them |

**"Bears on the same skill"** is, deterministically, sharing a target facet with the hypothesis, or its learning object where it names no facet. Facets and surface group are derived per attempt at read by `field.outcomes.load_attempt_rows` under the cutoff, the derivation the rebuilt cache holds, so `since` misses nothing made after a rebuild. EP1 measures that read's cost on the Next path. Part D adds a judged label beside it.

Each entry carries its source observation id and the grade or claim revision it was read at, so one miss cited three times is recognizable as one observation. The research arm's for/against lists keep their own adapter.

**As of when** (§7). The router's, the teacher's and chat's cards read `Cutoff.current()`. A diagnosis reads with the target attempt's own cutoff whether it runs at once or later in a worker, so job timing cannot change the answer: `Cutoff.history_v1(target)` at EP0t (§7.2). The target's own answer is passed apart from its prior history.

**Bounds.** Up to a stated number of rows per list, newest first; the rest are counted ("and 7 earlier"). The manifest (§7.3) records it.

**No new table for support.** Support is derived at read. If the read is too slow on the Next path it becomes a DERIVED projection with one replayer; EP1 measures first. The one new table in this spec is §7.4's status events.

### 4.3 What this does and doesn't change

A claim card changes what models read. It moves no weight: a hypothesis's probability still comes from the diagnosis, the probe and `spec_learner_input_after_miss_v1.md` §7's reweighting. A later independent success on the same skill appears in `since` for the model to weigh; turning it into a number is that spec's job and G4's.

## 5. Part C: the Decider and the action model on the same evidence

### 5.1 Today (checked)

Most Decider call sites already send the prompt the LLM gets and log both verdicts under one input hash (`judgment_ledger`, `ai/agreement.py`). On the objective path:

| | Decider | Action model |
|---|---|---|
| Role | advice and a comparator only (`daily_plan/objective_chooser.py:20`, `:851-857`); on a three-way follow-up choice it answers a binary restraint question (`:2071`) | one of the two served policies: the mix is the LLM policy and the numeric policy (`:1-22`) |
| Builder | `router/card.py` (text, card v3) | `daily_plan/objective_card.py` (JSON), under the same learner protection (`objective_card.py:9-10`) |
| Limit | `router.card_token_budget` 16,000, measured as the token estimate of the JSON card **plus** that of its text rendering (`router/card.py:586-590`) | `router_objective.llm_card_token_budget` 48,000, measured as UTF-8 bytes of the JSON (`objective_card.py:50-52`); whole answers capped at 4,000 characters and rows bounded before the trim (`adaptive_difficulty/history_card.py`) |
| Sees and the other doesn't | open hypotheses, the learner's marks | help, questions, reveals, the learner's statements, goals and weights, exams, other topics, whole answers, the objective in words |
| Trim | drops by kind; the Reader and confidence sections count their omissions, the others don't | oldest entry per section; counts kept in the objective trace |

The numeric policy reads its own inputs (`OI.build`, `objective_chooser.py:859-861`) and the LLM's per-option forecasts (`:888-895`), so a change to the action model's card reaches the numeric policy through those forecasts. Decider sensors (`will_pass_next`, `teach_first`) are read only by the agreement report on this path.

### 5.2 One view, two renderings

`EvidenceView`: a frozen dataclass built once per decision, in the prefetch where `PolicyRequest` is built today, under `Cutoff.current()` at the decision's commit version. Its sections are the union of the two cards': session, options, topics, attempts with facts (§3), claims (§4), help and questions and reveals, the learner's statements, cause-class probabilities, reading, teach-backs, goals and exams, other topics.

- `render_json(view)` is the action model's state.
- `render_text(view)` is the Decider's state: the same rows in the same order, as text.
- On objective-block decisions the Decider's question gains the objective in the action model's words, so both answer the same question. The follow-up restraint question stays and is not compared.
- **The numeric policy** keeps reading its numeric inputs (under `closure`, §7.2) and the LLM's forecasts; the view reaches it only through those.

What stays different is what the two APIs are: the Decider returns a choice and probabilities, with no rationale and no evidence ids; the action model returns both.

### 5.3 One limit, in bytes, and one trim

- **One setting:** `router_objective.evidence_bytes`, measured on one rendering, the UTF-8 bytes of `render_json(view)` with its fixed overhead. The text rendering is built from the rows the JSON kept; its size is recorded, not limited. The two "token" settings retire (`config/retired.py`) at EP3b; predecessor tags keep their budgets.
- **The default is measured, not chosen here.** 96,000 bytes (about 25,000 tokens) is the candidate. EP2's manifests and the traces' `left_out` counts show how often today's 48,000 binds, and EP3a measures the Decider's latency and cost (Q2).
- **One trim** for both renderings: rows admitted by priority, then recency; typed fields (options, topics, claims' headers) never drop; if they alone exceed the limit, every row is cut and the manifest says `over_budget_mandatory`.
- **Two kinds of cut, recorded apart:** rows a source query never returned and rows the byte limit cut. Both models are told the counts, as the action model is today.

### 5.4 Comparing them

`router/agreement.py` already pairs the two models' distributions per decision. With one view it compares them only where both chose among the same options for the same objective, from the same evidence hash, under the same label definitions; missing pairs are counted with their reason; forecasts are scored against the events they forecast. It makes no claim about which choice "the outcome favoured": a resolved outcome belongs to the action taken. An aggregate policy comparison uses logged propensities, and only where they give support.

No extra call is made: both are already called on every routed decision.

## 6. Part D: the Decider annotates the packet

### 6.1 The judgment

One question to start, because it is the one Part B can't answer from rows:

> Does this answer bear on this claim? `supports` / `contradicts` / `unrelated` / `cannot tell`

**State:** the claim's statement and cause class; the attempt's question, the learner's answer (an excerpt), its result and its facts line.

**Asked for:** each new attempt against each open claim that shares a facet or a learning object with it, and each new claim against the recent attempts that do. Batched, up to the API's 128 questions a call.

### 6.2 Where it runs and where it's kept

- **In the post-attempt jobs,** after grading and diagnosis. Never on the Next path: the packet builder reads stored judgments and doesn't wait for one.
- **Stored in `judgment_ledger`** (judge `decider`, a task name of its own). The ledger appends a new row each time and does not dedupe (`db/stores/judgments.py:14-40`), so a pair is claimed first through `judgment_work_claims` (`migrations/176_recurrence_groups.sql:136-150`): one paid answer per (task, producer, prompt version, input). The whole label distribution goes where the Tier-1 judgments already put it, as JSON in the `rationale` column, with `score` the chosen label's probability (`decider_judgments.py:203`, `:460-478`); no migration. The pair's identity (claim revision, attempt, grade revision) is kept apart from the request hash, which also covers the batch's shared context.
- **Spend** goes through the existing admission (`ai/spend.py`) under the Decider's daily cap.

### 6.3 What the packet builder does with it

1. **A label on the row,** with its source and probability: `since: Nov 13, correct, another family, no help (Decider: contradicts, 0.81)`.
2. **Never removal.** A row judged `unrelated` is cut only if the limit cuts it, and is then counted like any other.
3. **A missing judgment** (not yet run, refused, failed) leaves the row labelled `not judged`.
4. **Priority under the limit comes later (EP5b),** only after EP2's manifests show the limit binds and the paired labels and the rows they would displace have been reviewed. It orders by the probability that the answer bears on the claim (`supports` plus `contradicts`), not by the top label, so no threshold is implied. Ranking changes what the router reads, so it is its own successor.

### 6.4 What it is not

- **Not evidence.** A judgment moves no weight, mastery, schedule or certification. It is a label for another model to read.
- **Not a filter on the grader's or the diagnoser's inputs** in this spec.
- **Not the diagnoser's question.** The diagnoser's `fits` / `contradicts` / `silent` (`spec_learner_input_after_miss_v1.md` §7) is about the learner's stated reason or mark; this asks about an answer. EP6 pairs the two only where a declared label mapping says they ask the same thing, and gives `silent` and `cannot tell` an explicit treatment.
- **Not a second decider.** Which block to study stays the router's.

### 6.5 How far the labels can be trusted (EP5a)

- A seeded sample of pairs is asked again, once as before and once with the two texts in swapped order, with the sampling probability logged. The rate is a design propensity the owner sets (Q9).
- The existing owner judge labels a small gold set, bound to the exact claim and grade revisions judged.
- EP6 reports chance-corrected agreement (retest, order, owner) and calibration against the diagnoser's labels where they match. Two judges can agree because both saw the same misleading evidence; independent labels are how that shows.

### 6.6 Later judgments, only after 6.5's report

"Is this the same mistake as that one" (recurrence asks only the LLM today), and "which of these earlier answers is most like the current question". Each is one more question type on the same harness.

## 7. Part E: time. Two axes, named reads

Owner, Nov 16 2026: "the as_of timestamp is quite low resolution--for the following quetions, we need unique answers that as_of doesn't cover entirely "What happened before this attempt", "What did learnloop know when it made this decision", "What does learnloop currently believe about that history, after corrections"? [...] Maybe historical reconstruction and current corrected state should be seperately named operations."

### 7.1 Today (checked)

A fact has two times, when it happened and when LearnLoop knew it; they differ for an imported exam, a late grade, a regrade, a hold, a hypothesis written after later attempts. Correction is separate: what LearnLoop now says the fact was. Each reader mixes these its own way:

| Where | Which events it admits | Which corrections |
|---|---|---|
| `router_objective/checks.py:457-500`, `Closure` ("THE cutoff") | happened and known by the closure (`admits(occurred, received)`) | now: an answer's grade and hold as they stand (its stated exception) |
| `diagnosis/split/history.py` | attempts known by the target's known time (`_cutoff`, `:1246-1250`); records written strictly before the target's completion (`_written_before`, `:1059-1068`) | grading evidence current (`superseded_at IS NULL`, `:798-800`), holds now (`:845`), factor, misconception and candidate status now; a causal hypothesis's latest version written before the cutoff. `lagged_attempts` counts excluded attempts, not fields it could not reconstruct (`:1312-1318`) |
| `daily_plan/objective_inputs.py:329-345`, `decision_reads` | the database at a commit version | now |
| `adaptive_difficulty/replay.py` `load_events(as_of)` | attempts created by `as_of`, through the material view, whose protection is today's | now |
| `field/outcomes.py:697-710` `load_attempt_rows(as_of)` | attempts completed by `as_of` ("not a point-in-time reconstruction") | now |

Elsewhere the cutoff is a bare string or datetime under several names: `as_of` (37 typed parameters), `now_iso` (about 1,650 lines under `src/learnloop`), `before`, `cutoff`. Nothing in a signature says which choice the caller made.

**What the views read that changes in place**, and whether its past is recoverable (lines in `db/repositories.py`):

| Rows | What is overwritten | Past recoverable? |
|---|---|---|
| `grading_evidence` | `superseded_at`, `superseded_by_evidence_id` (`:2200`, `:2296`, `:6060`) | yes, by timestamp |
| `practice_attempts` score columns | `rubric_score`, `correctness`, confidence at regrade (`:2255`, `:2304`, `:6211`) | from grading evidence where its rows exist; else approximate |
| holds | derived from blind records and current evidence (`held_grades.py:62`) | yes by timestamp, except the review reason replay writes |
| `misconceptions` | status, statement, facets, severity, sources (`:2832`) | status yes: `misconception_transition_events` is written at creation and at each transition (`:2643`, `:2856`, since migration 056); the other fields approximate |
| `misconception_candidates` | status, counts, sources, statement fields (`:3317`) | no history: approximate |
| `unresolved_cause_factors` | status (`:17798`, `:17853`, `:17886`); candidate causes only (`:17450`, `:17513`) | no history; a resolution's observation ids date it; otherwise approximate |
| `probe_presentations` | status with `served_at`, `submitted_at`, `ended_at` (`:8071-8104`) | yes, by timestamp |
| `probe_episodes` | completion fields and posterior (`:7855`) | completion by `completed_at`; the rest approximate |
| `remediation_episodes` | state, attempt links (`:3769`, `:4199`) | approximate |
| `error_events` | status, misconception link (`:2554`, `:3495`) | approximate |
| `learner_claims` | `superseded_by`, `applied_after_attempts` (`:5905`, `:5944`) | supersession by the newer claim's creation time; the count approximate |
| `followup_tasks` | status, `not_before`, links (`:1364`-`:4357`) | consumption by the consuming attempt; the rest approximate |
| `fitted_parameters` | `active`, `deactivated_at` (`:7237`, `:7294`) | yes: each fit inserts a row and history rows are kept |
| protection (exam reservations, held-out spans) | applied as of now by the material view | no |

### 7.2 One `Cutoff`, two axes, named presets

One value type, `Cutoff`, generalised from `Closure`. Every view of the read model takes a `Cutoff`, never a bare timestamp. Two explicit fields:

- **`admit`**: `all`, `occurred_before` or `known_by`, with the anchor (an attempt id or a moment), the event-time boundary (strict) and the known-time boundary (inclusive).
- **`corrections`**: `now` or `then`. `then` applies a correction only if known by the known-time boundary, and only for fields the inventory marks recoverable; the rest are listed in `approximate`.

Named presets:

| The question | Preset | `admit` | `corrections` |
|---|---|---|---|
| What does LearnLoop believe now | `Cutoff.current()` | all | now |
| What happened before this attempt (reports, training labels, the learner's timeline: a regrade should reach these) | `Cutoff.corrected_before(attempt)` | occurred_before | now |
| What did LearnLoop know then, where no record was kept (a backfill, features for a model fitted on logged decisions: leakage from the future is the harm) | `Cutoff.as_known_at(attempt or moment)` | known_by | then |
| The router's closed rates and scores | `Cutoff.closure(stamp)` | known_by | now (Closure's stated exception, now a named policy rather than a docstring) |
| Today's diagnosis history, named as it is | `Cutoff.history_v1(target)` | attempts known_by, records written before the target's completion | now, except a causal hypothesis's version: then |
| AD's replay and field outcomes, as they are | `Cutoff.ad_replay(as_of)`, `Cutoff.completed_by(as_of)` | occurred_before (inclusive) | now |
| What a recorded decision was shown | not a cutoff: `as_recorded(decision_id)` (§7.3) | | |

- Every result carries the cutoff it honoured and `approximate: [...]`; a caller can refuse an approximate read.
- EP0t moves each caller onto the preset that reproduces it; a caller that matches none cleanly goes on the bug ledger. Moving the diagnoser to `as_known_at` changes its input and reuse keys: EP4, under the playbook.
- The serialized form (preset, both axes, anchor, boundaries, `approximate`) is defined at EP0t, because snapshots store it.

### 7.3 "What did it know" is read back, not recomputed

A decision's inputs are recorded when it is made, as a small **manifest**: a decision record of kind `packet` (the audit's P1), ids and numbers only, as `decision_records` requires (`provenance.py:10-21`). Per call: per section, rows offered, kept, cut by bytes and not returned by a source query, with the cutting rule, and each kept row's id and content hash; each rendering's bytes and hash, the view's evidence hash, builder and prompt versions, the serialized cutoff; three stages apart (offered to the builder, sent to the model, answered before the deadline); and a pointer to the bytes through the record's `detail_table` and `detail_id`.

The bytes are already kept, so EP2 adds no payload store:

| Payload | Where | Kept |
|---|---|---|
| The router's card, both models' requests and raw answers | `router_decision_payloads`, kinds `card`, `decider_request`, `decider_response`, `llm_request`, `llm_response` (`router/plan_log.py:391-466`; role WORKFLOW) | deleted after `router.payload_retention_days`, default 365 (`config/schema.py:3930`; `db/stores/router.py:352-360`) |
| A model call's prompt and output | `model_call_receipts.input_text`, `output_text` (`migrations/160_model_call_receipts.sql`; RECEIPT) | for root calls only, with no pruning path; a route can withhold its input (`ai/execution.py:48-63`, `:512-522`; no caller today) |
| What a diagnosis was shown | the diagnosis's frozen provenance record (`diagnosis/split/provenance.py`) | with the diagnosis |
| A decision record's facts and alternatives | `decision_records` | replaced by placeholders after the same retention, the row kept (`migrations/254_decision_records_payload_retention.sql`; `ops/startup.py:55-59`) |

`as_recorded(decision_id)` returns the manifest and, per payload, `exact` (bytes matching the stored hash), `pruned` (ids and hashes only), `missing` (with the reason) or `not_sent`. Today the objective trace keeps `evidence_ids`, `left_out`, `bytes` and `items` for the action model's card (`daily_plan/objective_chooser.py:875`); the manifest generalizes that to the three trims that exist.

**Who reads it:** `learnloop why`, the agreement report, prediction snapshots and offline evaluation of routed decisions. `as_known_at` remains for decisions with no manifest: those before EP2, and work that was never a decision.

### 7.4 Status changes become events

- **Reuse** `misconception_transition_events`; it already holds every misconception's creation and transitions.
- **Add** one append-only table, `status_events` (`seq INTEGER PRIMARY KEY AUTOINCREMENT`, `table`, `row_id`, `from_status`, `to_status`, `at`, `cause`), for the rows claim cards read that have no history: `misconception_candidates`, `unresolved_cause_factors`, `remediation_episodes`, `error_events`. `seq` orders these events' knowing within one database.
- **Written in the same transaction** at each insert that sets a first status (`:3162`, `:17474`, and the other two tables') and each genuine transition (`:3317`, `:17798`, `:17853`, `:17886`, and the other two tables'); not at `:17450` and `:17513`, which change only candidate causes.
- **Exactness per field:** status is exact from each row's coverage date; statements, facets, counts and sources stay approximate unless versioned, and a reconstructed old status beside today's statement is labelled as a pair that may never have coexisted.
- **Backfill:** one `backfilled` event per row at its `updated_at`, an observation of current state, not a transition date.
- **A test** fails when a new status update on a covered table writes no event (a scan, as `test_one_retrievability.py` scans).
- **Role:** RECEIPT, as `misconception_transition_events` is; no replay reads it. `history.py` reading it is EP4's change, not this step's. After L2, which splits `db/repositories.py`.

### 7.5 Two caches, kept apart

The first draft merged two caches whose contracts differ on purpose. `decision_reads` (`daily_plan/objective_inputs.py:329-345`) revalidates at every build by the commit version: any commit invalidates. AD's `reading_cache.job_scope` (`adaptive_difficulty/reading_cache.py:10-27`, landing ruling R1) is a snapshot as of the job's first read, over document files outside the database, keyed by database, protection epoch and vault object: a commit does not invalidate it, a protection change does. A view that reads vault files or protection is not a function of the database alone, so EP adds no cache by default. If EP1's measurement asks for one, it is keyed by database, watcher version, vault identity, protection epoch, cutoff and arguments, and R1 stands.

**Prefetch reuse needs an evidence revision.** The objective prefetch key (`objective_chooser.py:1414-1431`) is built from plan state, support, the latest attempt id, settings and the preference and miss-cause marks; a regrade, a judgment or a claim revision changes none of them. At EP3b the key gains the view's evidence hash, kept out of `numeric_seed` like the preference mark; it reaches the mix's seed through the key, which already varies with the decision id.

### 7.6 Not decided here: the clock itself

"Known at" is a wall-clock string, ordered by `(timestamp, id)`. Two events in one second order by id, and two devices' clocks don't share an order. A per-database sequence on every table would give "known" a total order. That is a column on many tables and an interaction with sync, so it is decided with `spec_storage_sync_v1.md`; §7.4's `seq` is the one exception, local to its table. `Cutoff` hides the representation, so that change would not reach a caller.

### 7.7 Prediction snapshots

Owner, Nov 16 2026: "the target set and prediction snapshot (outcome distributions tied to an evidence cutoff, target set, model version, likelihood provenance) could still be useful." Owner, Nov 17 2026: build the plumbing and the recording now, "to evaluate model quality later".

**What it is.** A prediction snapshot is a forecast kept with what makes it scorable later without reconstruction: when it was made and on which evidence (the cutoff), what it was about (the target), what it said (a distribution over named outcomes), and where its numbers came from (model, parameters, likelihood). It is to a forecast what the manifest is to a decision.

#### 7.7.1 Today (checked)

- **The table exists.** `forecast_receipts` (`migrations/206_forecast_receipts.sql:25-85`, RECEIPT) has kind, forecaster and version, scope, deciding decision, exact bindings (or `binding_kind = 'none'` with a censor reason), event, `p`, `forecast_json`, `inputs_json` and its hash, `inputs_as_of`, `parameters_json`, `versions_json`, `status` (`ok`, `failed`, `refused_spend`), `created_at`, `received_at`; idempotent by `receipt_key`; eight kinds registered (`scheduling/forecast_receipts.py:64-93`); an absent, invalid or future `inputs_as_of` replaced by the issue time (`clamped_as_of`, `:204`); written under the existing `diagnosis.forecast_receipts` switch.
- **Scores are derived.** `item_forecast_scores` (migration 214:262-277, DERIVED) joins each `item_unassisted_success` receipt to its bound attempt with log loss and Brier; an ineligible attempt, a repeat included, is `excluded` (`adaptive_difficulty/scoring.py:45-110`).
- **Older stores.** `voi_forecasts` (migration 184, RECEIPT) is read into the same family by `evsi_calibration/forecast_report.py:663-680`. Goal `forecasts` (WORKFLOW) hold point forecasts resolved in place.
- **Adaptive difficulty.** At an eligible plan presentation the serve hook writes `mastery_ekf` and `lo_general+composite` receipts for every item, and the three `ad_threshold@*` receipts and the frozen `item_serve_inputs` row only for a never-attempted item (`adaptive_difficulty/serve.py:109-128`). The threshold receipts store `p_bar` and `p_band` with `p_categories: None` (`serving.py:396-430`), though the model computes the three category probabilities on the way to `p_bar` (`model.py:150-177`).
- **The router objective's trace** freezes each option's LLM forecasts, numeric sensors, value terms, the reference forecast and the mixture.
- **Live readers.** `z_v1`'s recalibration reads receipts at serve, filtered to forecaster `llm_v1` at item scope (`adaptive_difficulty/serve_inputs.py:186-205`). Replay reads `item_serve_inputs` by presentation (`replay.py:435-446`); the scorer reads it for first presentations and `pre_exposed` (`scoring.py:58-62`).
- **Ids** come from `ids.new_ulid` (`db/stores/forecast_receipts.py:16`), which also mints the router's decision id, the seed of its draw (`provenance.py:139-147`).

#### 7.7.2 The contract

No new table. The first version adds keys to the existing JSON bodies, outside `inputs_json`, whose hash may key reuse:

| Piece | Where | What |
|---|---|---|
| Cutoff | `versions_json.snapshot.cutoff` | the serialized `Cutoff` with `approximate`; a reference to what was read (a manifest, an `item_serve_inputs` row, an objective trace); `as_of_status` `exact`, `unknown` or `invalid`, so the clamp no longer certifies a time it replaced |
| Target | `versions_json.snapshot.target` | kind; typed member ids with revisions (item content hash, learning object, facet, surface-group key and its source); unit; conditioning action; horizon and anchor; canonical `target_hash`; `event_version`, `resolver_version`. Members are stored (a hash cannot enumerate them) unless an immutable manifest holds them |
| Distribution | `forecast_json` | probabilities over named outcomes at available precision (`p_categories` filled where computed); `p` keeps the binary event; a point estimate keeps its unit |
| Provenance | `parameters_json`, `versions_json.snapshot.provenance` | likelihood source and version, fitted artifact or prior id, training cutoff, and for a model call its `model_call_receipts` id and prompt and schema versions |
| Not issued | `status`, `forecast_json.reason` | failed, refused, missing or unbound, with the reason; a censored receipt keeps `binding_kind = 'none'` |

A column comes only when a report filters on a value (`target_hash` likely first), as a nullable migration with the head fixture. `target_hash` is registered with the identity pins.

#### 7.7.3 Producers, in order

1. **Adaptive difficulty at every eligible plan presentation, repeats included** (EPp).
   - The three `ad_threshold@*` receipts store `p_categories`: the grid-weighted mixture of `category_probabilities`, `p_bar` its category 2.
   - On a repeat, the predecessor's prediction in the subject and LO views (`ad_threshold_repeat@subject`, `@lo`, three category probabilities), labelled with the predecessor's memory assumptions. Its serve-time inputs ride in `inputs_json` (features, signals with availability, loadings, warmth, state hash, `pre_exposed`) with the memory context: item revision, surface-group key and its source, the last item and surface-group review ids and times, the last topic exposure's id, time and kind. Not in `item_serve_inputs`, which replay and the scorer read. New forecaster names keep them out of `z_v1`'s filter.
2. **The native `voi_forecasts` bodies and the generic writer's producers** (EPp: diagnosis next observation, repair cold outcome, the teacher's forecasts, `lo_cold_success`) gain cutoff and target through one change to the writer. A stop or nominal-best candidate keeps its forecast, marked as never administered.
3. **The router objective's per-option forecasts, through a read adapter** over the trace that already freezes them (EP2; no second write), linked to the decision's manifest. Choice probabilities, mixture propensities, rollout values and `p_cold_7` stay separately labelled. One realized block scores only the option taken.
4. **Adaptive difficulty's successor** (ADM2a in `spec_ad_memory_v1.md`) writes its repeat-aware prediction at the same boundary, beside the predecessor's.

Goal forecasts, the grader's class posterior and attempt surprise (computed with the observation in hand, so not a prediction) get adapters only when a report asks.

#### 7.7.4 Which step, and why there

- **EP0t:** the `Cutoff` serialization and `target_hash`, pure functions, part of the type.
- **EPp,** right after EP0t. It does not wait for EP2 or Q7: only the manifest reference needs EP2, and every week without it loses predecessor predictions on repeats that ADM2a will change. It also closes the two propensity gaps (SR-2, SR-3), small write-time fixes to the same logging.
- **EP2:** the manifest reference, and the router trace adapter. **ADM2a:** the successor's repeat receipts.

#### 7.7.5 Evaluation-only until ADM2a

- No live reader's inputs change: new names stay outside `z_v1`'s filter, repeat inputs stay out of `item_serve_inputs`, `ad_state` and `ad_attempt_trace` are untouched.
- The scorer reads every `item_unassisted_success` receipt, so the predecessor's repeat receipts get `excluded` rows in `item_forecast_scores` at the next rebuild, as the baselines' repeat receipts already do; no existing row changes. A report may score captured repeats under a named evaluation rule; changing which repeats are scored or trained is ADM2a's.
- **Ids:** EPp's new receipts draw ids from a stream of their own (`ids.UlidStream`, as decision records do), so they do not move the router's decision id or seed.
- **Roles and replay:** every role stays as it is; `item_forecast_scores` keeps its one rebuild owner; no replayer is added. Whether ADM2a reads captured repeat inputs as frozen inputs is its step 0's call, the trace naming the source.

#### 7.7.6 Volume, what is lost by waiting, what waits

**Rows per day, a stated scenario (not a measurement):** a day with 10 fresh and 5 repeat eligible plan presentations already writes about 60 receipts (five per fresh presentation, two per repeat). Enriching bodies adds no rows; the predecessor's two views on repeats add 10; at 1-3 KB each, under 200 KB a day. The cost to measure is the extra AD state read on the serve path.

**Lost if not captured now:** a forecast never issued, the predecessor's prediction with the signals available at the serve, category probabilities, exact target membership after a family edit, the versions in force then, statuses before §7.4's events, payload bytes after retention, and the material view as it stood (protection is applied as of now).

**Recoverable by replay, so not stored:** AD, FSRS and EKF predictions under a code version over corrected history; every score; deterministic baselines (plain FSRS retrievability, a running success rate, the last outcome), which are report arms (`spec_ad_memory_v1.md` §9).

**Waits:** a universal forecast table, scoring screens, whole-posterior dumps, per-candidate snapshots at every decision, model calls made only to forecast, the EVSI shadow.

## 8. Build order

| Step | What | Track |
|---|---|---|
| **EP0** | `attempts/facts.py` (collection with a visibility reader, the draft form) and `fact_predicates.py`; the twelve copies call their function; each stored `assisted` column documented; values unchanged (AST identity, pins, goldens, P-shadow); differences to the bug ledger. | structure |
| **EP0t** | `Cutoff`'s two axes and presets (§7.2); each existing cutoff a use of it; the census with each caller's preset; §7.1's inventory as a test fixture; the serialization and `target_hash`. No value changes. | structure |
| **EPp** | Prediction snapshots (§7.7): the writer's convention, AD's `p_categories`, AD's predecessor receipts on repeats with inputs and memory context, the VOI keys, the own id stream; SR-2 and SR-3 fixed. | structure: receipts only, no tag |
| **EP1** | `diagnosis/claims.py`; the five renderings and the research arm read it; old renderings unchanged (goldens), new fields not yet rendered; the read's cost measured. | structure |
| **EP2** | The manifest (P1) over the existing payload stores; `as_recorded`'s four states; the router trace adapter; the manifest reference in snapshots. | structure |
| **EP2s** | §7.4's events, backfill and scan test. After L2. | structure with a migration |
| **EP3a** | The Decider reads `render_text(view)` with the objective question; its latency and cost measured at the candidate size. | behaviour, advice only: versions and pins move, no tag |
| **EP3b** | The action model reads `render_json(view)` (statements only under Q3 and after SR-1); one limit, one trim; the prefetch key's evidence hash. | behaviour: a router successor, alone, no kill switch |
| **EP4** | The other packets render facts and claim cards; "assisted" and "primed" leave every packet; the diagnoser may move to `as_known_at`. | behaviour: per prompt, under the playbook |
| **EP5a** | Part D's judgment, job, work claims and storage; the reliability sample; labels in the Decider's rendering only. | behaviour, advice only |
| **EP5b** | Labels in the action model's rendering and priority under the limit, after EP6's reliability report and evidence that the limit binds. | behaviour: a router successor |
| **EP6** | Agreement on matching questions; the Decider against the diagnoser under a declared label mapping. | report |

**Can start now:** EP0, EP0t, then EPp beside EP1. EP2 waits for Q7, EP2s for L2 and Q8, EP3a for EP2, EP3b for EP3a's measurement and the owner's Q1-Q3, EP5b for EP6. The first draft's EP2c (one cache) is dropped: §7.5.

## 9. Persisted meaning

- **EP0, EP0t, EP1, EP2** change no value; `causal_activity_v1` keeps its bytes.
- **EPp** writes receipts only (§7.7.5). No tag.
- **EP2s** is a migration (`db/table_roles.py`, the head fixture, the reference notes) writing rows no reader uses yet.
- **EP3a** changes only what advice and the agreement report read: card and prompt versions bump, K0's pins move in that commit, no tag.
- **EP3b** changes served decisions through the mix and the numeric policy's forecasts: a successor tag, one row in `ops/upgrades.py`, one test row, no kill switch (owner, Nov 16); undoing it after an upgrade is a follow-up successor. Step 0 lists the pins that move with the card and the evidence hash.
- **EP4** bumps each prompt's version; the diagnoser's context keys reuse, so its bump follows the playbook.
- **EP5a** adds `judgment_ledger` rows under a new task. **EP5b** is a router successor.
- **Replay:** nothing replayed reads a packet, a manifest, a claim card, a snapshot or an EP judgment. AD's replay does read `judgment_ledger` for feature audits and relatedness (`adaptive_difficulty/replay.py:3-8`, `:347`), so the import-closure test is per task.

## 10. Tests

- EP0: on the head fixture and a synthetic vault with one attempt per fact combination, each named predicate equals the copy it replaced, including an old attempt, partial modern capture, a never-shown hint, a late-attached row and a reveal under the threshold; facts read through AD's material view never show a withheld item.
- EP0t: `Closure`'s and `history.py`'s tests pass unchanged through their presets; an imported exam, two events in one second, a delayed diagnosis and a grade held then released land on the documented side of every preset; a live and a delayed diagnosis of one attempt read the same history.
- EPp: a receipt round-trips its cutoff and target; `target_hash` is pinned; a repeat's predecessor receipts have category probabilities summing to one, category 2 equal to `p_bar`; `z_v1`'s inputs, `ad_state`, `ad_attempt_trace` and every existing `item_forecast_scores` row are unchanged; under a frozen clock the router's decision id and seed don't move; a failure or an invalid input time is recorded with its reason.
- EP1: old renderings' goldens unchanged; an unmeasured rival gets no support from a cold check on its facet; a successful repair with zero diagnosis delta is `context`, not `against`; `since` includes an attempt made after the last rebuild.
- EP2: `as_recorded` returns the same ids and hashes after a regrade, a hold and a status change, and `pruned` after retention; dispatched bytes match their hash; a planted item's text appears in no manifest.
- EP2s: every covered insert and transition writes one event in its transaction; `as_known_at` before a change shows the earlier status; a backfilled row reads approximate.
- EP3: both renderings hold the same row ids and visible values in the same order at any limit, measured on the JSON's UTF-8 bytes, Unicode and oversized mandatory sections included; query cuts and byte cuts counted apart; below the tag both requests equal the predecessor's; a commit or a new judgment starts a new prefetch; a planted answer-bearing claim never reaches the learner-visible `why` before a probe, through the real path.
- EP5: a missing or failed judgment changes no row's presence; two workers pay once; the Next path never calls the annotator while its ordinary router call runs.
- The grader's context can reach none of it (the existing blindness test, extended).

## 11. Rules this touches

- **Slip or gap §3 item 3** keeps hypothesis statements from the action model because they "can restate the expected answer". The first draft's reason for lifting it, that the action model writes nothing the learner reads before answering, is false: when the LLM wins the draw its rationale can become the block's learner-visible explanation, and the guard checks length, terms, probabilities and cited ids, not paraphrased content (`router/why.py:202-226`, `:258-284`; `objective_chooser.py:1600-1612`; ledger SR-1). So statements wait for SR-1, and then withholding covers every field that can carry the answer (excerpts, marks, pair-judgment inputs), considering the whole episode's answers as today's rule does. Q3.
- **Slice 1's S3** (prior hypotheses reach the diagnoser only as typed records with status and evidence counts, `spec_blind_grading_diagnosis_split_v1.md:122`): EP4 widens those records, still typed and with no prior prose; the weight is Q5.
- **FG1 §7** (causes stay hidden from the learner before a probe; the locked set doesn't shrink): untouched, given SR-1.
- **AD's A10** ("asking for help is never penalized in the record"): untouched. Facts are read, not rewritten.
- **The reading firewall (A12):** `topic_history` includes reading as an exposure time only, which the diagnoser and the action model already receive.

## 12. Decisions for the owner

**Decided:**
- The shared read model this spec starts, and Part E's time rule with named reads (owner, Nov 16 2026).
- Revise this spec from the two reviews (owner, Nov 17 2026).
- Build prediction snapshots as part of this spec, to evaluate model quality later (owner, Nov 17 2026): §7.7, step EPp.

**Open:**

| # | Question | Recommendation |
|---|---|---|
| Q1 | One view for both router models (the action model gains hypotheses and marks; the Decider gains help, statements, goals, whole answers)? | Yes, the Decider first (EP3a, advice only), then the action model (EP3b); compare only matching questions. |
| Q2 | The limit? | Today's limits through EP3a; set the default at EP3b from the manifests, the traces' `left_out` counts and EP3a's latency, 96,000 bytes the candidate. |
| Q3 | Hypothesis statements for the action model (reverses slip or gap's "never")? | Yes, after SR-1 is closed and with withholding on every field (§11); until then, cause class and target in the statement's place. |
| Q4 | The Decider's first judgment? | Yes, as labels (EP5a); ordering only later (EP5b), by probability, after the reliability report and evidence the limit binds. |
| Q5 | Decider labels, and the claim card's weight, in the diagnoser's packet? | Neither for now: both would anchor its own labels. The router gets both. |
| Q6 | Where two "assisted" derivations disagree? | Named purpose-specific predicates; each genuine discrepancy a ledger row under its own version. |
| Q7 | Retention of router payloads and decision facts (`router.payload_retention_days`, default 365), now that manifests point at them? | Keep 365 days; manifests, ids and hashes stay for good and `as_recorded` says `pruned`. Lengthen only if an evaluation needs the bytes. |
| Q8 | Status history (§7.4)? | Yes, the narrower form. |
| Q9 | The judge-reliability sample rate (§6.5)? | Yours to set, as the dose floor was; I'd start at one pair in twenty, a few calls a day under the Decider's cap. |

## 13. Checked, and not checked

**Checked by me at main `88b10fb90d` (2026-11-17):** every path:line cited in §3.1, §4.1, §5.1, §6.2, §7.1, §7.3, §7.5 and §7.7.1, including the payload stores and their retention, `model_call_receipts.input_text` (root calls only, no pruning path), the no-prose rule, the stored `assisted` columns, each reader's cutoff, every in-place update in §7.1's inventory, the two caches, the prefetch key, the chooser's three roles, the rationale guard, both budget measures, `judgment_ledger`'s append and schema, AD's replay reading it, the forecast receipts and their scorer, AD's serve hook and the receipts' id stream; the parameter counts by grep.

**Checked at earlier tips only:** `router/requests.py`'s `state_text` and `PolicyRequest`; `learner_context.py:1389`, `router_card.py:818`, `intervention_outcomes.py:97-103` (main `250b0e16fe`; a reviewer re-confirmed them at this tip).

**From mappers or the reviews, not re-read by me:** the full list of Decider call sites; the other nine "assisted" derivations; `history_card.py`'s limits; the plan engine's serve hook reaching repeats served by the ordinary plan (`daily_plan/engine.py:5984`).

**Not checked:** the Decider's latency and cost at 25,000 tokens and which model `router_llm` resolves to in the owner's vaults (EP3a measures, with the owner's approval for the calls); the tutor's, teacher's and Reader's prompt templates for "assisted" or "primed"; what each `as_of` caller asks (EP0t's census); status writes outside `db/repositories.py` (EP2s's scan); the serve-path cost of repeat receipts (EPp measures). No test was run and no model was called.
