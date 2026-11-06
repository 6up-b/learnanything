# Census: error episodes, follow-ups, lessons and minutes (2026-11)

**Why.** Input to the TE2/TE3 re-spec (`docs/specs/spec_teacher_v1.md` revision 5): how often each part of TE2/TE3
would fire on the owner's real use, and which numbers the design rests on are counted and which are priors or
defaults.

**What was read.** Fresh backup-API copies (`learnloop.db.copies.copy_tree_with_databases`) of
`~/learnloop-backups/mvp043-20261103-copy` (three vaults: `arxiv_v2`, `linear_algebra`, `probability`), made under
the worktree's gitignored `fixtures-local/te23-census/` and deleted afterwards. Every query opened the copy
read-only (`mode=ro`), under `env -i` with an empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` and every AI
route pointed at `127.0.0.1:9`. No model call, no `learnloop` command, no live vault.

**The copies' version.** All three are at migration 238 and `mvp-0.43` (TE1b's tag). So data capture (239-240),
FG1 (241-242), RO0 (243) and RO1-RO6 had not run on them: there is no `followup_workflows`, `hypothesis_marks`,
`decision_state_receipts`, `session_receipts` or `router_objective_traces` data to count. Where FG1 or RO would
have acted, this census counts what their predecessor wrote, and says so.

**Public repository.** Aggregate numbers only: counts, rates, distributions, table and column names, enum values.
No stem, answer, hypothesis text, source passage, LO title or other quotation of the owner's material.

**Two kinds of number.** Every number below is one of:
- **E (empirical):** counted from rows in the copies;
- **P (prior or default):** a configured value or seeded prior in code at main `e7a7d7734f`. These are listed in §9
  and never mixed into the counts.

## 1. Headline

| | arxiv_v2 | linear_algebra | probability | All | Kind |
|---|---|---|---|---|---|
| Attempts (all types) | 3 | 70 | 3 | 76 | E |
| Graded attempts (not `self_report`) | 0 | 62 | 3 | 65 | E |
| Graded misses (`correctness < 1`) | 0 | 16 | 3 | 19 | E |
| of which in an exam sitting | 0 | 9 | 0 | 9 | E |
| of which cold (unassisted, unprimed, no earlier reveal on the item) | 0 | 5 | 1 | 6 | E |
| of which practice (hinted, primed or revealed) | 0 | 2 | 2 | 4 | E |
| Active days with a graded attempt | 0 | 6 | 2 | 8 | E |
| First and last graded day | - | Jul 22 - Jul 28 | Aug 4, Oct 25 | | E |
| Misses with two or more concrete rival causes (FG1's probe lane) | 0 | 0 | 1 | 1 | E |
| Lessons opened (`lessons`) | 0 | 0 | 0 | 0 | E |
| Lesson checks, receipts, suggestion responses | 0 | 0 | 0 | 0 | E |
| Router decisions (`router_decisions`) | 0 | 0 | 3 (`plan_block`) | 3 | E |
| Active goals (`profile/goals.yaml`, status active) | 0 | 0 (1 completed) | 0 | 0 | E |

**Reading it.** The owner's real use is one week of linear algebra in July (two exam sittings and some practice)
and two probability days. **No lesson has run, no lesson suggestion has been drawn or answered, and no active goal
exists.** Every rate this census gives is therefore a description of a small past, not an estimate of the future;
it is the reason revision 5 is designed to fire correctly at any volume and to log, not to wait.

## 2. Misses and what followed them

One row per graded miss (`Q3`), aggregated. "Later attempt on the LO" is any later graded attempt on the same LO,
whatever its type, so it is not a cold retest.

| | linear_algebra | probability | Kind |
|---|---|---|---|
| Misses | 16 | 3 | E |
| with an `error_events` row (diagnosed) | 16 | 3 | E |
| with a split diagnosis (`attempt_diagnoses`) | 0 | 1 | E |
| with any causal hypothesis (`causal_hypotheses`) | 2 | 1 | E |
| with two or more distinct hypothesis identities (`episode_key`) | 0 | 1 | E |
| with a hypothesis that names a repair class | 1 | 1 | E |
| with a cause factor (`unresolved_cause_factors`) | 1 | 1 | E |
| with a follow-up task (`followup_tasks.source_attempt_id`) | 0 | 0 | E |
| with an intervention need (`intervention_needs.attempt_id`) | 1 | 0 | E |
| with a cold measurement opportunity | 0 | 1 | E |
| with a tutor question on the attempt (`question_events.attempt_id`) | 2 | 1 | E |
| with a reveal on the item at or after the miss | 0 | 3 | E |
| with a later graded attempt on the same LO | 14 | 2 | E |
| that later attempt fully right | 10 | 0 | E |
| mean days from the miss to that later attempt | 0.16 | 41.3 | E |

**Grade shape** (`Q1`): of 19 misses, 1 scored 0 and 18 were partial (0 < correctness < 1). **Error types**
(`Q4`, linear_algebra's 19 `error_events` rows): `local_slip` 10, `representation_notation_error` 3,
`conceptual_schema_error` 3, `transfer_context_error` 1, `retrieval_failure` 1, `assessment_ambiguity` 1;
probability's 3: `retrieval_failure` 2, `procedure_execution_error` 1. Rows flagged as misconceptions: 5 of 22.

**Confidence on misses** (`Q14`, `Q17`): linear_algebra's taps are all 4 or 5 (29 tapped graded attempts), and 6 of
its misses carry a 4-5 tap; probability's three taps are 1, 2 and 5, all on misses.

## 3. Diagnoses, hypotheses and cause factors

| | arxiv_v2 | linear_algebra | probability | Kind |
|---|---|---|---|---|
| `causal_hypotheses` rows / identities / attempts | 0 / 0 / 0 | 9 / 2 / 2 | 3 / 3 / 1 | E |
| scope `learner_state` / `transient_execution` (identities) | - | 2 / 0 | 2 / 1 | E |
| repair-class basis `unresolved` / `authored_target_ref` / `authored_criterion_ref` (rows) | - | 7 / 2 / 0 | 0 / 2 / 1 | E |
| distinct repair classes among one attempt's rivals | - | 0 and 1 | 1 (all three share it) | E |
| `unresolved_cause_factors` open / retired | 0 / 1 | 1 / 3 | 1 / 0 | E |
| concrete rivals on the open factor (`Q21`) | - | 1 | 3 | E |
| `misconceptions` (resolved) / `misconception_candidates` | 0 / 0 | 1 / 1 | 0 / 0 | E |
| `causal_probe_decision_receipts` | 0 | 0 | 5, all `skip_common_repair` | E |
| `followup_value_decisions` | 0 | 0 | 1, `suppressed_voi_value_below_minutes_cost` | E |
| `voi_forecasts` | 0 | 0 | 1, verdict `stop` | E |
| placement episodes (`probe_episodes`, trigger `initial`, all `pending_items`) | 31 | 9 | 18 | E |
| their `probe_generation_needs` pending / resolved | 31 / 0 | 9 / 0 | 17 / 1 | E |
| `learner_text_gaps` | 0 | 0 | 2 (one `diagnosis` misconception, one `workbench_text` unmatched prerequisite) | E |

**What FG1 would have done** (from these rows; FG1 did not run on the copies). The one miss with three concrete
rivals is FG1's probe lane. The predecessor refused to commission a probe five times because the rivals share a
repair class (`skip_common_repair`) and once suppressed the follow-up on value (`suppressed_voi_value...`); under
FG1 both become facts on the router's card and the router decides (FG1 §5 item 5). The open factor with one
concrete cause is the practice lane. The nine exam misses go through `finish_exam`'s worst-first cap of three.
So on this history FG1's probe lane fires on **1 of 10 non-exam misses** (E, n = 10).

**Placement episodes.** All 58 `initial` episodes are waiting for items, because every vault's file says
`auto_generate_on_entry = false` (E). FG1's successor computes the effective setting as true, so these become 58
deduplicated generation jobs once the vaults are upgraded past `mvp-0.45` (FG1 §4.3).

## 4. Repairs, follow-ups and delayed checks

| | arxiv_v2 | linear_algebra | probability | Kind |
|---|---|---|---|---|
| `remediation_episodes` (case:state) | 0 | misconception:diagnosis 2, misconception:treatment 2 | diagnosis:treatment 1 | E |
| of which with a primed or a cold attempt done | 0 | 0 | 0 | E |
| `causal_repair_class_definitions` | 0 | 16 | 3 | E |
| `followup_tasks` | 0 | 1 `certification_cold_probe`, pending | 0 | E |
| `intervention_needs` | 0 | 1 `diagnose`, fulfilled | 0 | E |
| `cold_measurement_opportunities` (lane) | 0 | 1 `certification_cold_probe` | 2 `repair_cold_retry` | E |
| their decisions | - | 1 `scheduled` | 1 `structurally_refused` | E |
| commitments | 1 `help_me_remember` | 1 `test_me_later` | 0 | E |
| delayed checks from lessons (`lesson_receipts`, commitments `via = lesson`) | 0 | 0 | 0 | E |
| delayed checks resolved | 0 | 0 | 0 | E |

No repair has been verified cold in any vault (E).

## 5. Reveals and help

| | arxiv_v2 | linear_algebra | probability | Kind |
|---|---|---|---|---|
| `reveal_events` | 0 | 0 | 12 `answer_display`, on 1 item | E |
| attempts with `hints_used > 0` | 0 | 2 | 1 | E |
| attempts `primed = 1` | 0 | 0 | 1 | E |
| `question_events` by context: reader / practice / feedback | 1 / 0 / 0 | 11 / 8 / 2 | 3 / 5 / 2 | E |
| `help_assists` | 0 | 0 | 0 | E |
| workbench sessions / steps | 0 / 0 | 0 / 0 | 2 / 175 | E |

## 6. Minutes: active against elapsed

| | linear_algebra | probability | Kind |
|---|---|---|---|
| `sessions` / never ended | 17 / 1 | 1 / 1 | E |
| ended sessions by elapsed length: ≤30 min / 30-120 / 2 h-1 day / >1 day | 2 / 2 / 10 / 2 | - | E |
| median elapsed length of an ended session | 394 min | - | E |
| elapsed minutes over all ended sessions | 8369 | - | E |
| graded attempts with `latency_seconds` | 11 of 62 | 3 of 3 | E |
| answer minutes recorded (`latency_seconds`) | 39.2 | 100.8 | E |
| graded attempts outside any session | 30 (all exam attempts) | 0 | E |
| client-measured attempt durations (`interaction_events.attempt_duration_ms`) | 1 event, 1.1 min | 0 | E |
| workbench elapsed minutes | - | 41.0 | E |

**Reading it.** Session elapsed time is not active time: sessions stay open for hours or days, and recorded answer
time is under 1% of it on linear_algebra. Only 14 of 65 graded attempts carry a latency. This is why RO4 counts a
session's minutes from activity spans (attempts and Reader visits, `router_objective/price.py`) rather than from
`sessions`, and why a lesson must record its own active intervals (revision 5 §11.6): a lesson today leaves
`opened_at`, `closed_at` and turn timestamps, which are elapsed time.

## 7. Per LO bucket

LOs bucketed by graded attempts on them (`Q12`). LO counts are from the vault's `learning-objects/*.yaml`.

| Vault | LOs | LOs with a graded attempt | Bucket (graded attempts) | LOs | Attempts | Misses | Cold misses | Exam misses | Kind |
|---|---|---|---|---|---|---|---|---|---|
| linear_algebra | 21 | 8 | 2-4 | 1 | 4 | 1 | 0 | 0 | E |
| | | | 5-9 | 4 | 26 | 2 | 1 | 1 | E |
| | | | 10+ | 3 | 32 | 13 | 4 | 8 | E |
| probability | 18 | 1 | 2-4 | 1 | 3 | 3 | 1 | 0 | E |
| arxiv_v2 | 34 | 0 | - | - | - | - | - | - | E |

Misses concentrate: 13 of linear_algebra's 16 are on its three most-practised LOs. LOs whose two latest cold
attempts both missed (TE1b's `cold_failing` reason, `Q16`): 2 in linear_algebra, 0 elsewhere (E).

**The unseen pool.** A delayed check (§13), an RO5 randomized check and a rev-4 vault probe all need an item of
the LO that is active, not a diagnostic probe or teach-back, never attempted and never revealed. Counted from the
items' YAML (only `id`, `learning_object_id`, `status`, `practice_mode` and `provenance.origin` were read; one
probability item file did not parse and is left out):

| Vault | Active practice items | LOs with no unseen item | 1 unseen | 2 or more unseen | Kind |
|---|---|---|---|---|---|
| arxiv_v2 | 32 (all `codex_proposal`) | 5 of 34 | 29 | 0 | E |
| linear_algebra | 55 (of 99 files; 40 retired) | 15 of 21 | 1 | 5 | E |
| probability | 77 | 0 of 18 | 4 | 14 | E |

So a lesson that wants one placement probe and one delayed retention check on the same LO from the vault finds two
unseen items on 19 of 73 LOs (E), and none on the 15 linear_algebra LOs the owner has not practised. Each such use
consumes the item for every other unseen-item reader, and a lesson's own teaching text writes `tutor_answer`
reveal rows on the items whose key it overlaps, which removes them from the pool for good.

## 8. How often TE2/TE3 would fire on this history

| Part of revision 5 | Fires on | On this history | Kind |
|---|---|---|---|
| Placement probes in a lesson (§11.3) | Lessons | 0 lessons, so 0 | E |
| Typed-goal resolution and `create_goal_lo` (§11.5) | A typed lesson goal | 0 | E |
| `propose_gap` from a lesson (§11.4) | Learner text in a lesson | 0 lessons; outside lessons 2 text gaps in 4 months | E |
| Detour episodes (§11.4) | A missed lesson check | 0 | E |
| Lesson offers in the objective (§15.1) | A traced `plan_block` decision with a lesson candidate | 3 `plan_block` decisions ever, none traced (pre-RO4); lesson candidates would exist: 2 `cold_failing` LOs, 0 `new_goal` LOs (no active goal) | E |
| AD `lesson` opportunity (§14.2) | Each landed or taught node | 0 | E |
| FG1's probe lane, for comparison | Non-exam misses with two or more rivals | 1 of 10 | E |
| Lessons a month, rev 4's planning figure | - | 12 a month | P (an assumption in §21, never observed) |

## 9. Priors and defaults the re-spec relies on (P)

Values in code at main `e7a7d7734f`. None is counted from the owner's data; each is labelled as the spec labels it
(§18.4: seeded prior with basis, structural, `keep`, or a declared price).

| Quantity | Value | Where | Label |
|---|---|---|---|
| Lesson-check mass, prior centre | 0.5 (logit 0, sd 1.0) | `learner/lesson_weight.py`, `lp_priors_v1` | seeded prior, `legacy` |
| Pool weight λ | Beta(1, 4) | same | seeded prior, `legacy` |
| Delayed-check target retrievability R* | 0.9 | `teacher.delayed.target_retrievability` | seeded prior, `published` |
| Delayed-check fallback dates | 3 days retention, 7 transfer | `teacher.delayed.fallback_*_days` | seeded prior, `legacy` |
| Longest wait for a delayed check | 14 days | `teacher.delayed.max_wait_days` | `keep` |
| Suggestion card's lesson length | 15 min | `router/lesson_suggestions.py` `CARD_MINUTES` | display default |
| Suggestion rate and mute | about 1 a day, about 7 days | `suggestion_priors_v1` | seeded prior, `legacy` |
| Suggestion ceiling | 3 a day | `router.lesson_suggestions.ceiling_per_day` | `keep` |
| Router support size, floor | k = 6, ε = 0.02 | `router.k`, `router.epsilon_min` | config |
| Mix weight w, minimums | 0.8, ℓ = 0.1 each | `[router_objective]` | declared seed |
| Stop coin, randomized checks, open picks | 0.05, 1 embedded a day, 0.1 | `[router_objective]` | declared prices for information |
| FG1 generation attempts per workflow | 2 | `followup_run/jobs.py` `MAX_GENERATION_ATTEMPTS` | structural bound |
| FG1 diagnosis wait | 10 s | `diagnosis.next_item_wait_seconds` | existing value, reused |
| Text-gap creations a day | 3 (+1 for an explicit goal) | `learner_text_gaps.max_creations_per_day` | `keep` |
| Quick check size | 4 | `placement.quick_check_k` | existing value |
| Rev 4's placement probe cap and calibration probability | 8, 1.0 | `teacher.placement.*` (never built) | `keep`, design probability |

## 10. The queries

Rerun with the same isolation on fresh backup-API copies of a later backup. Each statement runs per vault, read-only.
At a head with FG1 and RO0 the census should add `followup_workflows` by lane and settled reason,
`generated_probe_burns`, `hypothesis_marks`, `session_receipts` and `router_objective_traces`; the shape of `Q3`
carries over with `followup_workflows.source_attempt_id` as the join.

```sql
-- Q1 attempts by class (cold / practice / exam / self_report) and misses
WITH a AS (
  SELECT pa.*,
    CASE WHEN pa.attempt_type = 'self_report' THEN 'self_report'
         WHEN pa.attempt_type = 'exam_attempt' THEN 'exam'
         WHEN pa.attempt_type IN ('independent_attempt', 'open_text', 'diagnostic_probe')
              AND COALESCE(pa.hints_used, 0) = 0 AND COALESCE(pa.primed, 0) = 0
              AND NOT EXISTS (SELECT 1 FROM reveal_events r
                              WHERE r.practice_item_id = pa.practice_item_id AND r.created_at < pa.created_at)
           THEN 'cold'
         ELSE 'practice' END AS klass,
    (SELECT COUNT(*) FROM practice_attempts p2
      WHERE p2.practice_item_id = pa.practice_item_id AND p2.created_at < pa.created_at) AS prior_on_item
  FROM practice_attempts pa)
SELECT klass, COUNT(*) AS attempts,
       SUM(correctness < 1.0) AS misses,
       SUM(correctness = 0) AS wrong,
       SUM(correctness > 0 AND correctness < 1.0) AS partial,
       SUM(prior_on_item = 0) AS first_on_item,
       SUM(prior_on_item = 0 AND correctness < 1.0) AS first_on_item_misses
FROM a GROUP BY klass ORDER BY klass;

-- Q2 active days and rates per active day (graded attempts only)
SELECT COUNT(DISTINCT substr(created_at, 1, 10)) AS active_days,
       COUNT(*) AS graded,
       SUM(correctness < 1.0) AS misses,
       ROUND(1.0 * COUNT(*) / COUNT(DISTINCT substr(created_at, 1, 10)), 1) AS graded_per_day,
       ROUND(1.0 * SUM(correctness < 1.0) / COUNT(DISTINCT substr(created_at, 1, 10)), 1) AS misses_per_day,
       MIN(substr(created_at, 1, 10)) AS first_day, MAX(substr(created_at, 1, 10)) AS last_day
FROM practice_attempts WHERE attempt_type <> 'self_report';

-- Q3 what followed each graded miss (one row per miss, aggregated)
WITH m AS (
  SELECT pa.id, pa.learning_object_id, pa.practice_item_id, pa.created_at, pa.attempt_type
  FROM practice_attempts pa WHERE pa.attempt_type <> 'self_report' AND pa.correctness < 1.0),
f AS (
  SELECT m.id,
    m.attempt_type = 'exam_attempt' AS exam,
    EXISTS (SELECT 1 FROM error_events e WHERE e.attempt_id = m.id) AS error_event,
    EXISTS (SELECT 1 FROM attempt_diagnoses d WHERE d.attempt_id = m.id) AS split_diagnosis,
    (SELECT COUNT(DISTINCT h.episode_key) FROM causal_hypotheses h WHERE h.attempt_id = m.id) AS hypotheses,
    (SELECT COUNT(DISTINCT h.episode_key) FROM causal_hypotheses h
      WHERE h.attempt_id = m.id AND h.repair_class_id IS NOT NULL) AS hypotheses_with_class,
    EXISTS (SELECT 1 FROM unresolved_cause_factors u WHERE u.attempt_id = m.id) AS cause_factor,
    EXISTS (SELECT 1 FROM followup_tasks t WHERE t.source_attempt_id = m.id) AS followup_task,
    EXISTS (SELECT 1 FROM intervention_needs n WHERE n.attempt_id = m.id) AS intervention_need,
    EXISTS (SELECT 1 FROM cold_measurement_opportunities c WHERE c.source_attempt_id = m.id) AS cold_opportunity,
    EXISTS (SELECT 1 FROM question_events q WHERE q.attempt_id = m.id) AS tutor_question,
    EXISTS (SELECT 1 FROM reveal_events r WHERE r.practice_item_id = m.practice_item_id
              AND r.created_at >= m.created_at) AS reveal_after,
    (SELECT p2.correctness FROM practice_attempts p2
      WHERE p2.learning_object_id = m.learning_object_id AND p2.created_at > m.created_at
        AND p2.attempt_type <> 'self_report' ORDER BY p2.created_at LIMIT 1) AS next_on_lo,
    (SELECT julianday(p2.created_at) - julianday(m.created_at) FROM practice_attempts p2
      WHERE p2.learning_object_id = m.learning_object_id AND p2.created_at > m.created_at
        AND p2.attempt_type <> 'self_report' ORDER BY p2.created_at LIMIT 1) AS days_to_next_on_lo
  FROM m)
SELECT COUNT(*) AS misses, SUM(exam) AS in_exam,
       SUM(error_event) AS with_error_event, SUM(split_diagnosis) AS with_split_diagnosis,
       SUM(hypotheses >= 1) AS with_any_hypothesis, SUM(hypotheses >= 2) AS with_2plus_hypotheses,
       SUM(hypotheses_with_class >= 1) AS with_classed_hypothesis,
       SUM(cause_factor) AS with_cause_factor, SUM(followup_task) AS with_followup_task,
       SUM(intervention_need) AS with_need, SUM(cold_opportunity) AS with_cold_opportunity,
       SUM(tutor_question) AS with_tutor_question, SUM(reveal_after) AS with_reveal_after,
       SUM(next_on_lo IS NOT NULL) AS with_later_attempt_on_lo,
       SUM(next_on_lo = 1.0) AS later_attempt_right,
       ROUND(AVG(days_to_next_on_lo), 2) AS mean_days_to_next
FROM f;

-- Q4 error events by type (diagnosed misses)
SELECT error_type, COUNT(*) AS n, SUM(is_misconception) AS misconception_flag,
       SUM(status = 'active') AS active,
       SUM(repair_plan_json IS NOT NULL AND repair_plan_json NOT IN ('', '{}', 'null')) AS with_repair_plan
FROM error_events GROUP BY error_type ORDER BY n DESC;

-- Q5 causal hypotheses: status, scope and repair-class basis
SELECT status, cause_scope, repair_class_basis, COUNT(*) AS rows, COUNT(DISTINCT episode_key) AS identities,
       COUNT(DISTINCT attempt_id) AS attempts
FROM causal_hypotheses GROUP BY 1, 2, 3;

-- Q5b distinct repair classes among one attempt's rivals
SELECT COUNT(DISTINCT episode_key) AS identities, COUNT(DISTINCT repair_class_id) AS classes,
       COUNT(DISTINCT r.repair_equivalence_id) AS equivalence_classes
FROM causal_hypotheses h LEFT JOIN causal_repair_class_definitions r USING (repair_class_id)
GROUP BY attempt_id;

-- Q6 cause factors, misconceptions, placement episodes and their generation needs
SELECT 'unresolved_cause_factors' AS t, status AS k, COUNT(*) AS n FROM unresolved_cause_factors GROUP BY status
UNION ALL SELECT 'misconceptions', status, COUNT(*) FROM misconceptions GROUP BY status
UNION ALL SELECT 'misconception_candidates', 'all', COUNT(*) FROM misconception_candidates
UNION ALL SELECT 'probe_episodes', status || ':' || trigger, COUNT(*) FROM probe_episodes GROUP BY status, trigger
UNION ALL SELECT 'probe_generation_needs', status, COUNT(*) FROM probe_generation_needs GROUP BY status
UNION ALL SELECT 'hypothesis_sets', 'all', COUNT(*) FROM hypothesis_sets
UNION ALL SELECT 'causal_probe_decision_receipts', decision, COUNT(*) FROM causal_probe_decision_receipts GROUP BY decision
UNION ALL SELECT 'followup_value_decisions', decision_outcome, COUNT(*) FROM followup_value_decisions GROUP BY decision_outcome
UNION ALL SELECT 'voi_forecasts', verdict, COUNT(*) FROM voi_forecasts GROUP BY verdict;

-- Q7 repairs and follow-ups
SELECT 'remediation_episodes' AS t, case_kind || ':' || state AS k, COUNT(*) AS n,
       SUM(cold_attempt_id IS NOT NULL) AS cold_done, SUM(primed_attempt_id IS NOT NULL) AS primed_done
FROM remediation_episodes GROUP BY case_kind, state
UNION ALL SELECT 'followup_tasks', kind || ':' || status, COUNT(*), SUM(consumed_attempt_id IS NOT NULL), NULL
FROM followup_tasks GROUP BY kind, status
UNION ALL SELECT 'intervention_needs', desired_intent || ':' || status, COUNT(*), NULL, NULL
FROM intervention_needs GROUP BY desired_intent, status
UNION ALL SELECT 'cold_measurement_opportunities', lane || ':' || trigger_kind, COUNT(*), NULL, NULL
FROM cold_measurement_opportunities GROUP BY lane, trigger_kind
UNION ALL SELECT 'cold_measurement_opportunity_decisions', decision, COUNT(*), NULL, NULL
FROM cold_measurement_opportunity_decisions GROUP BY decision
UNION ALL SELECT 'causal_repair_class_definitions', 'all', COUNT(*), NULL, NULL FROM causal_repair_class_definitions;

-- Q8 reveals, hints, tutor questions and help
SELECT 'reveal_events' AS t, source_kind AS k, COUNT(*) AS n, COUNT(DISTINCT practice_item_id) AS items
FROM reveal_events GROUP BY source_kind
UNION ALL SELECT 'attempts_with_hints', 'hints_used>0', COUNT(*), COUNT(DISTINCT practice_item_id)
FROM practice_attempts WHERE hints_used > 0
UNION ALL SELECT 'attempts_primed', 'primed=1', COUNT(*), COUNT(DISTINCT practice_item_id)
FROM practice_attempts WHERE primed = 1
UNION ALL SELECT 'question_events', context, COUNT(*), COUNT(DISTINCT practice_item_id)
FROM question_events GROUP BY context
UNION ALL SELECT 'help_assists', surface, COUNT(*), COUNT(DISTINCT practice_item_id)
FROM help_assists GROUP BY surface;

-- Q9 lessons, lesson checks, delayed checks, suggestions, forecasts
SELECT 'lessons' AS t, COALESCE(close_reason, 'open') AS k, COUNT(*) AS n FROM lessons GROUP BY 2
UNION ALL SELECT 'lesson_checks', 'all', COUNT(*) FROM lesson_checks
UNION ALL SELECT 'lesson_receipts', 'all', COUNT(*) FROM lesson_receipts
UNION ALL SELECT 'router_suggestion_responses', 'all', COUNT(*) FROM router_suggestion_responses
UNION ALL SELECT 'router_decisions', decision_kind, COUNT(*) FROM router_decisions GROUP BY decision_kind
UNION ALL SELECT 'router_outcomes', r_cold_status, COUNT(*) FROM router_outcomes GROUP BY r_cold_status
UNION ALL SELECT 'commitments', created_action, COUNT(*) FROM commitments GROUP BY created_action
UNION ALL SELECT 'commitment_via', json_extract(provenance_json, '$.via'), COUNT(*) FROM commitment_versions GROUP BY 2
UNION ALL SELECT 'forecast_receipts', kind || ':' || status, COUNT(*) FROM forecast_receipts GROUP BY kind, status
UNION ALL SELECT 'item_forecast_scores', forecaster || ':' || status, COUNT(*) FROM item_forecast_scores GROUP BY forecaster, status
UNION ALL SELECT 'learner_text_gaps', source_kind || ':' || kind || ':' || action, COUNT(*) FROM learner_text_gaps GROUP BY 2;

-- Q10 minutes: sessions (elapsed) against attempt latency (active)
WITH s AS (
  SELECT s.id, (julianday(s.ended_at) - julianday(s.started_at)) * 1440.0 AS elapsed_min, s.available_minutes,
         (SELECT SUM(COALESCE(p.latency_seconds, 0)) / 60.0 FROM practice_attempts p WHERE p.session_id = s.id) AS answer_min,
         (SELECT COUNT(*) FROM practice_attempts p WHERE p.session_id = s.id) AS attempts
  FROM sessions s)
SELECT COUNT(*) AS sessions, SUM(elapsed_min IS NULL) AS never_ended,
       ROUND(SUM(elapsed_min), 1) AS elapsed_min_total, ROUND(SUM(answer_min), 1) AS answer_min_total,
       SUM(attempts) AS attempts_in_sessions, SUM(attempts = 0) AS sessions_without_attempts,
       ROUND(AVG(available_minutes), 1) AS mean_available_min
FROM s;

-- Q11 answer latency (active-minute proxy) over all graded attempts
SELECT COUNT(*) AS graded, SUM(latency_seconds IS NOT NULL) AS with_latency,
       ROUND(SUM(latency_seconds) / 60.0, 1) AS answer_minutes_total,
       ROUND(AVG(latency_seconds) / 60.0, 2) AS mean_answer_minutes,
       SUM(session_id IS NULL) AS outside_any_session
FROM practice_attempts WHERE attempt_type <> 'self_report';

-- Q12 per LO bucket (by graded attempts on the LO)
WITH lo AS (
  SELECT learning_object_id,
         COUNT(*) AS n, SUM(correctness < 1.0) AS misses,
         SUM(attempt_type IN ('independent_attempt', 'open_text', 'diagnostic_probe')
             AND COALESCE(hints_used, 0) = 0 AND COALESCE(primed, 0) = 0 AND correctness < 1.0) AS cold_misses,
         SUM(attempt_type = 'exam_attempt' AND correctness < 1.0) AS exam_misses
  FROM practice_attempts WHERE attempt_type <> 'self_report' GROUP BY learning_object_id)
SELECT CASE WHEN n = 1 THEN '1' WHEN n <= 4 THEN '2-4' WHEN n <= 9 THEN '5-9' ELSE '10+' END AS bucket,
       COUNT(*) AS los, SUM(n) AS attempts, SUM(misses) AS misses, SUM(cold_misses) AS cold_misses,
       SUM(exam_misses) AS exam_misses
FROM lo GROUP BY bucket ORDER BY MIN(n);

-- Q13 mastery rows and how many LOs have any evidence
SELECT COUNT(*) AS mastery_rows, SUM(evidence_count > 0) AS with_evidence,
       ROUND(AVG(logit_variance), 2) AS mean_logit_variance
FROM learning_object_mastery;

-- Q14 confidence taps on graded attempts
SELECT COALESCE(CAST(answer_confidence AS TEXT), 'none') AS tap, COUNT(*) AS n, SUM(correctness < 1.0) AS misses
FROM practice_attempts WHERE attempt_type <> 'self_report' GROUP BY 1 ORDER BY 1;

-- Q15 session elapsed-minute distribution (ended sessions)
WITH s AS (SELECT (julianday(ended_at) - julianday(started_at)) * 1440.0 AS m FROM sessions WHERE ended_at IS NOT NULL)
SELECT COUNT(*) AS ended, SUM(m <= 30) AS le_30, SUM(m > 30 AND m <= 120) AS gt30_le120,
       SUM(m > 120 AND m <= 1440) AS gt120_le1day, SUM(m > 1440) AS gt_1day,
       ROUND((SELECT m FROM s ORDER BY m LIMIT 1 OFFSET (SELECT COUNT(*) FROM s) / 2), 1) AS median_min
FROM s;

-- Q16 LOs whose two latest cold graded attempts both missed (TE1b's cold_failing reason)
WITH c AS (
  SELECT learning_object_id, correctness,
         ROW_NUMBER() OVER (PARTITION BY learning_object_id ORDER BY created_at DESC) AS k
  FROM practice_attempts
  WHERE attempt_type IN ('independent_attempt', 'open_text', 'diagnostic_probe', 'exam_attempt')
    AND COALESCE(hints_used, 0) = 0 AND COALESCE(primed, 0) = 0)
SELECT COUNT(*) AS los_cold_failing FROM (
  SELECT learning_object_id FROM c WHERE k <= 2 GROUP BY learning_object_id
  HAVING COUNT(*) = 2 AND MAX(correctness) < 1.0);

-- Q17 LOs with a miss, and misses by confidence tap
SELECT COUNT(DISTINCT learning_object_id) AS los_with_a_miss,
       SUM(answer_confidence >= 4) AS confident_misses, SUM(answer_confidence <= 2) AS unsure_misses
FROM practice_attempts WHERE attempt_type <> 'self_report' AND correctness < 1.0;

-- Q18 client-measured attempt durations
SELECT COUNT(*) AS events_with_duration, ROUND(SUM(attempt_duration_ms) / 60000.0, 1) AS minutes
FROM interaction_events WHERE attempt_duration_ms IS NOT NULL;

-- Q19 workbench sessions and steps
SELECT (SELECT COUNT(*) FROM workbench_sessions) AS workbench_sessions,
       (SELECT COUNT(*) FROM workbench_steps) AS workbench_steps,
       (SELECT ROUND(SUM((julianday(COALESCE(closed_at, updated_at)) - julianday(created_at)) * 1440.0), 1)
          FROM workbench_sessions) AS workbench_elapsed_min;

-- Q20 exam sittings
SELECT COUNT(*) AS sittings, SUM(status = 'completed') AS completed FROM exam_sessions;

-- Q21 the FG1 lane each cause factor would take: concrete rivals per factor (open-set entries not counted)
WITH r AS (
  SELECT u.id, u.status,
         (SELECT COUNT(*) FROM json_each(u.candidate_causes_json) j
           WHERE COALESCE(json_extract(j.value, '$.open_set'), 0) = 0
             AND json_extract(j.value, '$.hypothesis_id') IS NOT NULL
             AND json_extract(j.value, '$.hypothesis_id') IN (SELECT id FROM causal_hypotheses)) AS concrete
  FROM unresolved_cause_factors u)
SELECT status, concrete, COUNT(*) AS factors FROM r GROUP BY status, concrete;
```

The unseen-pool count (§7) reads the vault's YAML, not the database:

```python
# per vault: attempted and revealed item ids from the copy, then the items' YAML
attempted = {r[0] for r in con.execute("SELECT DISTINCT practice_item_id FROM practice_attempts")}
revealed = {r[0] for r in con.execute("SELECT DISTINCT practice_item_id FROM reveal_events")}
for f in vault.glob("subjects/*/practice-items/*.yaml"):
    d = yaml.safe_load(f.read_text())            # fields read: id, learning_object_id, status, practice_mode
    if d["status"] == "active" and d.get("practice_mode") not in ("diagnostic_probe", "teach_back"):
        active[d["learning_object_id"]] += 1
        if d["id"] not in attempted and d["id"] not in revealed:
            unseen[d["learning_object_id"]] += 1
# then the distribution of unseen[lo] over every LO in subjects/*/learning-objects/*.yaml
```
