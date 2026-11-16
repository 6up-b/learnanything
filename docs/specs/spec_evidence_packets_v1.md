# Evidence packets (EP): one view of the learner's evidence for every model

Facts in place of "assisted", hypotheses as claims with their context, the Decider and the action model on the same evidence, the Decider as a helper that annotates the packet, and one rule for time: which of three questions a read answers.

**Status:** draft, Nov 16 2026, for the owner's review. Not queued. The owner agreed the same day to the shared read model this spec is the first slice of, and to Part E (§7). Evaluated in `docs/reviews/refactor-strategy-v3-audit-2026-11-16.md` §4.2-§4.4.

**Depends on:** the audit's E7b (`learner_signals` ahead of arc E) and P1 (a record of what a model was shown). EP0 and EP1 are structure steps and can run before either.

**Amends:** `spec_slip_vs_gap_v1.md` §3 item 3 ("never the hypothesis statements"), for the action model, if the owner says yes to Q3. It builds on `spec_learner_input_after_miss_v1.md` §7 and contradicts nothing in it.

## 1. The owner's words (Nov 16 2026, verbatim)

> Another issue I wanted to bring up that you should spec out is revising the Decider model prompt and the GPT prompt to be able to retrieve most of the same information so we can compare them. Another idea though that I'm starting to think is better is that since Decider models are so cheap, we could use them within a harness in the action router to help build better packets/construct histories that are sent to the LLM. I would also replace ambiguous "assisted" label with seperate recorded facts. Hypotheses should be claims that need context in the packet, like what observations supported the hypothesis, when it was last supported, which attempts bear on the same skill, whether those later attempts were independent/repeated/assisted. I'm fine with also increasing the GPT token input a bit also (considering we're using bytes and not tokens anyway). Our current action model feels pretty good, so we don't want to pigeonhole it too much by depriving it of good information either.

Standing rules that bind this spec: only the grader is blind; learner data goes to a model whenever it helps (owner, Nov 1). Weights and thresholds are learned (Oct 24). The learner's narrowing reweights and never removes (Nov 9). No shadow stages (prefer live changes).

## 2. In plain words

1. **An attempt carries what actually happened around it**, in words a model can read: which hint, how far in; whether the answer was shown before; whether it's the first time on this item or this family. The one word "assisted" stops standing for all of them.
2. **A hypothesis arrives with its case file:** what raised it, what has supported it and when, and what you've done on the same skill since, each with item 1's facts.
3. **The Decider and the action model read the same evidence**, so comparing them compares the models.
4. **The Decider, being nearly free, reads pairs** (this answer, this hypothesis: does one bear on the other?) in the background. Its labels are shown in the packet and decide what is kept first when the packet is full. It never removes anything.
5. **The action model's packet gets larger**, and what was left out is recorded.
6. **Every read says which question about time it answers:** what happened before this attempt, what LearnLoop knew when it decided, or what it believes now. Today one timestamp stands for all three.

## 3. Part A: attempt facts

### 3.1 Today (checked)

There is no stored "assisted". It is derived on read, from `attempt_type`, `hints_used` and `primed`, in at least twelve places that disagree (`docs/reviews/refactor-strategy-v3-audit-2026-11-16.md` §4.3 has the table; the canonical one is `diagnosis/causal_activity_policy.py:168`). Two packets tell a model `assisted = primed` with the hint count in the next field (`learner_context.py:1389`, `daily_plan/router_card.py:818`). The diagnoser gets `assisted` and `primed` as bare booleans its prompt never defines (`diagnosis/split/context.py:476`).

The three inputs are collapsed too: hint levels 1-3 become a count and levels 4-5 become `primed`; a figure counts as a hint; a reveal total of 0.35 or more forces `primed` (`db/stores/help_assists.py:270`, `attempts/attempts.py:2436`).

The facts underneath are already rows:

| Fact | Where it is stored |
|---|---|
| Each hint, check, figure or other assist: kind, level, when requested and shown, the work's length at that moment | `help_assists` (append-only, since migration 210) |
| Each time the answer or part of it was shown: source (tutor answer, repair display, guided redo, source review, answer display), amount, when | `reveal_events` (append-only) |
| Whether the first hint came before or after a draft | `practice_attempts.first_hint_progress` |
| A question to the tutor during the attempt, and whether it was hint-equivalent | `question_events` |
| "Don't know", "stuck" | `practice_attempts.declared_dont_know`, `declared_stuck` |
| Which presentation the attempt answered (a probe, a plan block, a cold check) | `probe_presentation_id`, `plan_presentation_id` |
| Earlier attempts on the item, its surface group and its learning object | `practice_attempts`, `facet_outcome_observations` |
| Reading on the topic before the attempt | `reading_exposure_receipts` |

`adaptive_difficulty/outcomes.py` already works this way: `AttemptFacts`, then `help_timing` and `category` as named functions over it.

### 3.2 The facts

One frozen dataclass, read from those tables by one function (`attempts/facts.py`: `attempt_facts(connection, attempt_ids) -> dict[id, AttemptFacts]`). No migration and no new table.

| Field | Values |
|---|---|
| `produced_as` | the stored attempt type |
| `hints` | per hint: kind, level 1-5, `before_work` or `after_work` or `unknown`, seconds before the answer |
| `checks`, `figures` | counts of "check my work" and figures shown during the attempt |
| `tutor_questions` | count, and how many were hint-equivalent, before or after work |
| `shown_before` | per source: how much of the answer was shown before the serve, and how long before |
| `shown_during` | the same, between serve and answer |
| `item_history` | which time on this item this is; time since the last; whether its feedback was displayed |
| `family_history` | which time on this surface group; time since the last |
| `topic_history` | time since the last exposure of any kind on the learning object |
| `declared` | don't know, stuck |
| `answering` | an ordinary serve, a probe, a cold check, an exam attempt |
| `detail` | `full`, or `counts_only` for an attempt older than `help_assists` |

**Nothing is inferred backwards.** An attempt from before migration 210 has its hint count and `primed` and says so: `detail = counts_only`.

### 3.3 The categories stay, as named functions

Each reader that needs a yes or no keeps it, as a function over `AttemptFacts`, all in one module (`attempts/fact_predicates.py`):

| Function | Who reads it | Today's copy it replaces |
|---|---|---|
| `counts_as_assisted` | the canonical projection, the facet timeline, certification's cold probe | `causal_activity_policy.attempt_counts_as_assisted` (its bytes kept: `causal_activity_v1`) |
| `unassisted_for_coldness` | the coldness receipt | `coldness_receipt._unassisted` |
| `help_timing`, `outcome_category` | adaptive difficulty | `adaptive_difficulty/outcomes.py` (moved, not changed) |
| `independent_for_outcomes` | intervention outcomes, slip-or-gap's fit | `intervention_outcomes.is_assisted` |
| `fsrs_rating_cap` | the grade application | `attempts.py:5726` |
| `cold_and_unassisted` | the diagnoser's "demonstrated" | `split/history.py:227` |

EP0 moves each copy to its function with its value unchanged, so twelve derivations become six named ones in one file. Where two copies that claim to mean the same thing differ (the mapper found at least: open-text answers counted as assisted in one, any reveal at all in another, primed-only in the two packets), the step names the difference on the bug ledger. It doesn't pick a winner silently.

### 3.4 What a model is shown

A line of facts per attempt, and one legend per packet that defines every term used. In a text packet:

```
Nov 9 · eigenvalues · item 2nd time (3 days ago, feedback seen) · family 4th time · correct
       help: hint level 2 after starting; answer not shown · answering: cold check
```

In a JSON packet, the same fields by name. The words "assisted" and "primed" leave every packet. They stay on screens ("with help ◌"): that wording is the UX audit's.

## 4. Part B: hypotheses as claims

### 4.1 Today (checked)

| Packet | What a hypothesis carries |
|---|---|
| The action model's card (`daily_plan/objective_card.py`) | Nothing. Learner-named gaps, and cause-class probabilities "never the hypothesis statements" |
| The Decider's card (`daily_plan/router_card.py:608`) | `topic: kind (status, since DATE): statement`, and the learner's marks |
| The diagnoser (`diagnosis/split/context.py:504`) | statement, status, a count of evidence, a "last updated" that is the newest version's creation time |
| Follow-up authoring (`followup_run/authoring.py:175`) | a ref, the statement, the cause scope, the target |
| Chat (`learner_context.py:1119`) | counts for and against, repairs tried |
| A research arm nobody serves from (`field/probability_states.py:587`) | evidence for and against as lists of attempts with days and results, repairs tried |

No table links a hypothesis to what supported or contradicted it, and none has a last-supported time. Prior weights are inside `causal_hypotheses.evidence_json`; a probe's posterior is in `probe_observations`.

### 4.2 The claim card

One builder (`diagnosis/claims.py`: `claim_cards(connection, cutoff, topics) -> list[Claim]`, `cutoff` a `Cutoff` of §7), a pure function over rows gathered by one read. Every packet above becomes a rendering of it.

| Field | From |
|---|---|
| `ref` | a packet-local name (H1, H2) |
| `statement` | the hypothesis's statement, or "withheld" under the existing rule (`statement_text`) |
| `cause_class`, `status` | `cause_scope`, the lifecycle |
| `raised` | date, and the attempt that raised it |
| `weight` | the diagnosis's prior weight; the probe's posterior if one exists, labelled as that; the learner's latest mark beside them, never folded in |
| `supported_by` | the episode's attempts, recurrences joined to it, failed cold checks, the learner's "my gap" or confirming words, a probe observation that matched its prediction: each with its date |
| `last_supported` | the newest date in `supported_by` |
| `against` | passed cold checks, a probe observation that matched a rival, the learner's "not it" |
| `since` | every later attempt that bears on the same skill: date, result, its relation to the raising item (same item, same family, another family), and its facts (§3.2) |
| `repairs` | repairs tried and their cold results |

**"Bears on the same skill"** is, deterministically, sharing a target facet with the hypothesis, or its learning object where it names no facet (`facet_outcome_observations` already holds each attempt's facets and surface group). Part D adds a judged label beside it.

**As of when** (§7). The router's, the teacher's and chat's cards are `Cutoff.current()`. A diagnosis made as the attempt lands is also current. A diagnosis of an old attempt made later (offline review, a backfill) is `Cutoff.as_known_at(attempt)`, which is what `diagnosis/split/history.py` approximates today.

**Bounds.** Up to a fixed number of rows per list, newest first; the rest are counted ("and 7 earlier"). The trim (§5.3) records it.

**No new table for support.** Support is derived at read. If the read is too slow on the Next path it becomes a DERIVED projection with one replayer; EP1 measures first. The one new table in this spec is §7.4's status events.

### 4.3 What this does and doesn't change

A claim card changes what models read. It moves no weight: a hypothesis's probability still comes from the diagnosis, the probe and `spec_learner_input_after_miss_v1.md` §7's reweighting. A later independent success on the same skill appears in `since` for the model to weigh; turning it into a number is that spec's job and G4's.

## 5. Part C: the Decider and the action model on the same evidence

### 5.1 Today (checked)

Most Decider call sites already send the prompt the LLM gets and log both verdicts under one input hash (`judgment_ledger`, `ai/agreement.py`). The router did too (`BoundaryRequest`: one `state_text`, two wrappers) until the objective path. There:

| | Decider | Action model |
|---|---|---|
| Builder | `router/card.py` (text, card v3) | `daily_plan/objective_card.py` (JSON) |
| Limit | `router.card_token_budget` 16,000, counted as bytes / 4: about 64 KB | `router_objective.llm_card_token_budget` 48,000, counted as bytes: 48 KB |
| Sees and the other doesn't | open hypotheses, the learner's marks | help, questions, reveals, the learner's statements, goals and weights, exams, other topics, whole answers, the objective in words |
| Trim | drops by kind, keeps no count | oldest entry per section; counts kept in the objective trace |

### 5.2 One view, two renderings

`EvidenceView`: a frozen dataclass built once per decision, in the prefetch where `PolicyRequest` is built today. Its sections are the union of the two cards': session, options, topics, attempts with facts (§3), claims (§4), help and questions and reveals, the learner's statements, cause-class probabilities, reading, teach-backs, goals and exams, other topics.

- `render_json(view)` is the action model's state.
- `render_text(view)` is the Decider's state: the same rows in the same order, as text.
- The Decider's question gains the objective in the action model's words (`POLICY_INSTRUCTIONS`' second sentence), so both answer the same question.

What stays different is what the two APIs are: the Decider returns a choice and probabilities, with no rationale and no evidence ids, and the action model returns both.

### 5.3 One limit, in bytes, and one trim

- **One setting, named for what it counts:** `router_objective.evidence_bytes`. The two "token" settings retire (`config/retired.py`).
- **Default 96,000 bytes,** twice the action model's today. That is roughly 25,000 tokens: under a tenth of the Decider's input limit and about $0.0005 a Decider call at the configured price. The owner's "a bit" is the reason it isn't more; the record below shows whether it binds.
- **One trim function** for both renderings, so both models lose the same rows. Order: within the limit, rows are admitted by priority and then recency; Part D supplies the priority. Typed fields (options, topics, claims' headers) never drop.
- **What was cut is recorded** (the audit's P1): per section, rows offered, kept and cut, and bytes, on a `packet` decision record. Both models are told the counts, as the action model is today (`left_out`).

### 5.4 Comparing them

`router/agreement.py` already pairs the two models' distributions per decision. With one view its report means what it says. It gains: agreement by decision kind, and for decisions with a resolved outcome (`router_outcomes`), which model's choice the outcome favoured. The sensors (`will_pass_next`, `teach_first`) are already scored by log loss.

No extra call is made: both are already called on every routed decision.

## 6. Part D: the Decider annotates the packet

### 6.1 The judgment

One question to start, because it is the one Part B can't answer from rows:

> Does this answer bear on this claim? `supports` / `contradicts` / `unrelated` / `cannot tell`

**State:** the claim's statement and cause class; the attempt's question, the learner's answer (an excerpt), its result and its facts line.

**Asked for:** each new attempt against each open claim that shares a facet or a learning object with it, and each new claim against the recent attempts that do. Batched, up to the API's 128 questions a call.

### 6.2 Where it runs and where it's kept

- **In the post-attempt jobs,** after grading and diagnosis. Never on the Next path: the packet builder reads stored judgments and doesn't wait for one.
- **Stored in `judgment_ledger`** (judge `decider`, keyed by the hash of what was sent), which exists and already dedupes by input. No new table.
- **Spend** goes through the existing admission (`ai/spend.py`) under the Decider's daily cap.

### 6.3 What the packet builder does with it

1. **A label on the row,** with its source and probability: `since: Nov 13, correct, another family, no help (Decider: contradicts, 0.81)`.
2. **Priority under the limit.** Rows that bear on an open claim about a candidate topic are admitted before rows that don't.
3. **Never removal.** A row judged `unrelated` is cut only if the limit cuts it, and is then counted like any other.
4. **A missing judgment** (not yet run, refused, failed, a tie) leaves the row labelled `not judged` at its recency priority. The `packet` record counts how many rows were ordered by a judgment and how many by recency.

### 6.4 What it is not

- **Not evidence.** A judgment moves no weight, mastery, schedule or certification. It is a label for another model to read.
- **Not a filter on the grader's or the diagnoser's inputs** in this spec. The diagnoser's own per-hypothesis `fits` / `contradicts` / `silent` (`spec_learner_input_after_miss_v1.md` §7) is logged under the same input hash where both exist, so `ai/agreement.py` reports how often the Decider agrees with it. That agreement is the evidence for trusting it further later.
- **Not a second decider.** It answers a question about two pieces of text. Which block to study stays the router's.

### 6.5 Later judgments, only after 6.1's agreement report

"Is this the same mistake as that one" (recurrence asks only the LLM today), and "which of these earlier answers is most like the current question". Each is one more question type on the same harness.

## 7. Part E: time. Three questions, three named reads

Owner, Nov 16 2026: "the as_of timestamp is quite low resolution--for the following quetions, we need unique answers that as_of doesn't cover entirely "What happened before this attempt", "What did learnloop know when it made this decision", "What does learnloop currently believe about that history, after corrections"? [...] Maybe historical reconstruction and current corrected state should be seperately named operations."

### 7.1 Today (checked)

A fact has two times: when it happened, and when LearnLoop came to know it. They differ for an imported exam, a late grade, a regrade, a hold placed or released, and a hypothesis written by a job that ran after later attempts. On top of both sits a third thing, correction: what LearnLoop now says the fact was.

The code has three separate answers and no shared one:

| Where | What it does |
|---|---|
| `router_objective/checks.py`, `Closure` ("THE cutoff") | `admits(occurred, received)` tests both times. Its docstring states one exception on purpose: an answer's grade and hold are read as they stand now |
| `diagnosis/split/history.py` (`AttemptRef`, `_written_before`, `_known_by`) | Filters on when an attempt happened and when a record was written; a causal hypothesis shows its latest version written before the cutoff. The status of factors, misconceptions and candidates is read from the present, disclosed as `lagged_attempts` |
| `daily_plan/objective_inputs.py`, `decision_reads` | Neither time: the database's commit version (`PRAGMA data_version`), so a read is reused only while nothing was committed |

Elsewhere the cutoff is a bare string or datetime under several names: `as_of` (33 typed parameters: `str`, `str | None`, `datetime`), `now_iso` (658 mentions), `before`, `cutoff`. Nothing in a signature says which question the caller is asking.

Why reconstruction can't answer "what did it know" exactly today: `unresolved_cause_factors`, `misconceptions` and `misconception_candidates` are updated in place (seven `UPDATE` sites in `db/repositories.py`), so their past status is gone.

### 7.2 The three questions as three constructors

One value type, `Cutoff`, generalised from `Closure` (which becomes a use of it). A view of the read model (attempt facts §3, claim cards §4, `EvidenceView` §5) takes a `Cutoff` and never a bare timestamp.

| The owner's question | Constructor | Admits | Corrections |
|---|---|---|---|
| What does LearnLoop believe now | `Cutoff.current()` | everything | as they stand now |
| What happened before this attempt | `Cutoff.corrected_before(attempt)` | events that happened before it, whenever they became known | as they stand now: the latest grade, today's holds, today's statuses |
| What did LearnLoop know when it decided | not a cutoff: `as_recorded(decision_id)` (§7.3) | what the decision was shown | as they stood then |
| The same, where no record was kept | `Cutoff.as_known_at(attempt or moment)` | events that had happened and were known by then | as they stood then, where versions exist; otherwise marked approximate |

- `corrected_before` is for anything that learns from history or shows it: reports, a training label, the learner's own timeline. A regrade should reach these.
- `as_known_at` is for anything that must not see the future: a diagnosis of an old attempt made later, a backfill, features for a model fitted on logged decisions. Leakage from the future is the harm it prevents.
- Every result carries the cutoff it honoured and, for `as_known_at`, what it could not reconstruct (`approximate: [...]`, as `lagged_attempts` does today). A caller can refuse an approximate read; none is silently exact.
- `Closure`'s stated exception becomes a parameter with a name instead of a docstring: its reads are `as_known_at` for which events count and `current` for their grades and holds.

### 7.3 "What did it know" is read back, not recomputed

A decision's inputs are frozen when it is made, on the `packet` record (§5.3). `as_recorded(decision_id)` returns them. This is exact, including what the limit cut, and it stays exact however the tables change afterwards.

- **What the record keeps:** each row's id and content hash per section, the counts §5.3 names, and the rendered packet (Q7: the whole text compressed, or ids and hashes alone).
- **Today:** the objective trace keeps `evidence_ids`, `left_out`, `bytes` and `items` for the action model's card (`daily_plan/objective_chooser.py:875`), not what the rows said.
- **Who reads it:** `learnloop why`, the agreement report (§5.4), and any offline evaluation of a routed decision, which then needs no reconstruction.

So `as_known_at` is kept only for decisions that have no record: those made before EP2, and work that was never a decision (offline review, backfills).

### 7.4 Status changes become events

A new append-only table, `status_events` (`table`, `row_id`, `status`, `at`, `cause`: the attempt, job or learner action that changed it), written in the same transaction as each of the seven updates. The three tables keep their current-status column, so no reader changes.

- It makes `as_known_at` exact for those three tables.
- It gives claim cards (§4.2) "when did this status change", which they have no source for today.
- **Role:** the three tables are `WORKFLOW`; the events are the history of a workflow column, so `RAW_LEDGER` or `WORKFLOW` is step 0's call with `db/table_roles.py`'s tests. No replay reads it.
- **Backfill:** one event per existing row from its `updated_at` (or `created_at`), marked `backfilled`: history before the migration stays approximate and says so.

### 7.5 One cache, keyed by what a view depends on

A view is a function of the database's contents and its cutoff. So the read model holds one cache keyed by (commit version, cutoff, view arguments), validated as `decision_reads` validates today: the version is taken before the read, any commit invalidates, nothing outlives the scope. `decision_reads` and AD's `reading_cache.job_scope` become two uses of it. A `Cutoff.current()` read is never reused across a commit; a closed `as_known_at` read is not reusable across one either, because corrections can reach it (`Closure`'s exception).

### 7.6 Not decided here: the clock itself

"Known at" is a wall-clock string, ordered by `(timestamp, id)`. Two events in one second order by id, and two devices' clocks don't share an order. A per-database sequence number would give "known" a total order. It is a column on many tables and an interaction with sync, so it is decided with `spec_storage_sync_v1.md`, not here. `Cutoff` hides the representation, so that change would not reach a caller.

### 7.7 A later direction: prediction snapshots

Owner, Nov 16 2026, on retiring the EVSI shadow: "the target set and prediction snapshot (outcome distributions tied to an evidence cutoff, target set, model version, likelihood provenance) could still be useful. It would be nice to explore as a research direction".

A prediction snapshot is to a forecast what the `packet` record is to a decision: the outcome distribution a model gave, stored with the `Cutoff` it was made under, the set of targets it was about, the model's version and where its likelihood came from. With those four, a forecast can be scored later against what happened without reconstructing anything, and two models' forecasts can be compared on the same cutoff. `voi_forecasts` holds part of this today (the emission distribution, the belief, each parameter's provenance) without a named cutoff or target set. This spec builds none of it. It is recorded here so that the cutoff type (§7.2) is designed to be the one a snapshot would carry.

## 8. Build order

| Step | What | Track |
|---|---|---|
| **EP0** | `attempts/facts.py` and `fact_predicates.py`; the twelve copies call their named function; every value unchanged (pins, goldens, P-shadow); the differences found go on the bug ledger. | structure |
| **EP0t** | `Cutoff` (§7.2), with `Closure` and `history.py`'s filters as uses of it; a census of every `as_of`, `now_iso`, `before` and `cutoff` parameter with the question each caller asks; no value changes. | structure |
| **EP1** | `diagnosis/claims.py`; the five packet renderings and the research arm read it. Their output is unchanged where they showed a field before (goldens); new fields are not yet rendered. Measures the read's cost. | structure |
| **EP2** | The `packet` record (the audit's P1) for the three trims that exist today, and `as_recorded` (§7.3). | structure |
| **EP2s** | `status_events` (§7.4): the table, the seven writes, the backfill; `as_known_at` reads it. | structure with a migration |
| **EP2c** | The read model's one cache (§7.5); `decision_reads` and `reading_cache.job_scope` use it. | structure, after EP3's view exists |
| **EP3** | The router: `EvidenceView`, two renderings, one limit, one trim, the Decider's question; attempt facts and claim cards rendered in both. | behaviour: a router successor, lands alone; no kill switch unless the owner asks for one (owner, Nov 16; strategy §2.20) |
| **EP4** | The diagnoser's, teacher's, tutor's and chat's packets render facts and claim cards; prompt versions bump; "assisted" and "primed" leave every packet. | behaviour: per prompt, under the playbook where a prompt keys reuse |
| **EP5** | Part D: the judgment, its job, its labels and priority. | behaviour: its own successor after EP3 |
| **EP6** | The agreement report on equal evidence, and the Decider-against-diagnoser agreement. | report |

EP0, EP0t and EP1 can start now; EP2 after Q7 and EP2s after Q8. EP3 needs the owner's answers to Q1-Q4.

## 9. Persisted meaning

- **EP0-EP2** change no value. `causal_activity_v1` keeps its bytes. EP0t changes no read: each caller gets the constructor that reproduces what it does today, and a caller whose present behaviour answers none of the three questions cleanly goes on the bug ledger instead of being changed in the move.
- **EP2s** is a migration (`db/table_roles.py`, the head fixture, the reference notes) and writes rows; it changes no value any reader uses today.
- **EP3** changes what both router models read, so it changes served decisions through the mix: a successor tag and a row in `ops/upgrades.py`. No kill switch by default (owner, Nov 16: a new successor ships without one unless asked, strategy §2.20); if the owner wants to monitor it, the switch is `router_objective.evidence_view` and off serves the two old cards exactly. Card and prompt versions bump; K0's pins move deliberately in that commit. The boundary key and the mix's seed read the card's hash: step 0 says which pins move.
- **EP4** bumps each prompt's version. The diagnoser's context keys reuse (`tests/test_identity_pins.py`); its bump follows the playbook.
- **EP5** adds rows to `judgment_ledger` (a ledger; no replay reads it) and a job type.
- **Replay:** no replayed table reads a packet, a claim card or a judgment. A test on the import closure says so, as arc B's did for `decision_records`.

## 10. Tests

- EP0: for every attempt in the head fixture and in a synthetic vault with one attempt per fact combination, each named predicate equals the copy it replaced.
- EP0t: `Closure`'s and `history.py`'s existing tests pass unchanged through `Cutoff`; a late-received attempt, a regrade and a hypothesis written after later attempts each land on the documented side of all three constructors.
- EP1: each old rendering's golden is unchanged.
- EP2: `as_recorded` returns the same rows after a regrade, a hold and a status change made since the decision.
- EP2s: every status update writes one event in its transaction (a test over the seven sites); `as_known_at` before a status change shows the earlier status; a backfilled row is reported approximate.
- EP3: both renderings contain the same row ids in the same order at any limit; the trim's counts add up; below the tag, both requests are byte-equal to the predecessor's (a golden recorded before the change).
- EP3: a planted item's text appears in no `packet` record.
- EP5: a missing, failed or tied judgment changes no row's presence; the Next path makes no Decider call (a fake that fails if called).
- The grader's context can reach none of it (the existing blindness test, extended).

## 11. Rules this touches

- **Slip or gap §3 item 3** keeps hypothesis statements from the action model because they "can restate the expected answer". Claim cards put them in, under the withholding rule the Decider's card already uses. The action model isn't the grader and writes nothing the learner reads before answering; a lesson or a follow-up it chooses is authored by another call. Q3.
- **FG1 §7** (causes stay hidden from the learner before a probe; the locked set doesn't shrink): untouched. Nothing here is shown to the learner or removes a hypothesis.
- **AD's A10** ("asking for help is never penalized in the record"): untouched. Facts are read, not rewritten.
- **The reading firewall (A12):** `topic_history` includes reading as an exposure time only, which the diagnoser and the action model already receive.

## 12. Decisions for the owner

| # | Question | Recommendation |
|---|---|---|
| Q1 | One view for both router models, with the action model gaining hypotheses and marks and the Decider gaining help, statements, goals and whole answers? | Yes. |
| Q2 | The limit: 96,000 bytes for both? | Yes, and read the `packet` records after two weeks to see whether it binds. |
| Q3 | Hypothesis statements in the action model's packet, under the existing withholding rule (reverses slip or gap's "never")? | Yes. The alternative is claim cards with the statement replaced by its cause class and target, which keeps the case file and loses what the claim is. |
| Q4 | The Decider's first judgment is "does this answer bear on this claim", used for labels and ordering only? | Yes. |
| Q5 | Do the Decider's labels also go to the diagnoser's packet, or only to the router's? | The router's first. The diagnoser produces its own `fits` / `contradicts`; showing it the Decider's would anchor it. |
| Q6 | Where two of today's "assisted" derivations disagree, fix each as a ledger row, or keep the differences as separate named predicates? | Ledger rows, each read on its own: some are differences of purpose and some are bugs (the two packets that say `assisted = primed` look like bugs). |
| Q7 | Does a decision's `packet` record keep the whole rendered packet (compressed), or row ids and content hashes alone? | The whole packet for router decisions and diagnoses. It is the only exact answer to "what did it know" once a row is regraded; ids and hashes say which rows, not what they said. Step 0 of EP2 measures the size per day. |
| Q8 | Status events (§7.4): a migration for three workflow tables' status history? | Yes. Claim cards need the dates, and it removes the one approximation in reading the past. |

## 13. Checked, and not checked

**Checked by me at main `250b0e16fe`:** `router/requests.py`'s `state_text`, `POLICY_INSTRUCTIONS` and `PolicyRequest`; `objective_card.py`'s section order, `_size` and `_trim`; the two budget settings and how each counts; `objective_chooser.py:875` (what the trace keeps) and `:1975` (what only the LLM gets); `learner_context.py:1389` and `router_card.py:818` (`assisted = primed`); `intervention_outcomes.py:97-103`; `adaptive_difficulty/outcomes.py:74-107`.

**Checked by me at main `fbaa1db418` for Part E:** `Closure`'s docstring and `admits` (`router_objective/checks.py:458-500`); `diagnosis/split/history.py` whole; `objective_inputs.py:267-377`; the roles of the three status tables and `causal_hypotheses` in `db/table_roles.py`; the seven `UPDATE` sites and the parameter counts by grep.

**From two read-only mappers, not re-read by me:** the full list of Decider call sites and which share a prompt with an LLM; the other nine "assisted" derivations; the hypothesis tables and each packet's fields; the Decisions API's limits as the code documents them; the two earlier specs' rules as summarized in §11.

**Not checked:**
- The Decider's latency at 25,000 tokens. The router spec quotes under 2 s for a few hundred tokens and about 23 s near the limit; the prefetch timeout is 45 s. EP3's step 0 measures it with the owner's approval for the calls.
- Which model `router_llm` resolves to in the owner's vaults, and so what 96,000 bytes costs there.
- Whether `facet_outcome_observations` is fresh enough at a decision to build `since` from, or needs the attempt's own rows.
- Every prompt template: the tutor's, the teacher's and the Reader's were not enumerated for the words "assisted" or "primed".
- For Part E: what each of the `as_of` and `now_iso` callers actually asks (EP0t's census); whether every status change goes through the seven `UPDATE` sites or some go through a generic writer; whether any call's receipt already stores its request text.
- No test was run and no model was called.
