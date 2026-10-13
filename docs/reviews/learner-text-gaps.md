# Learner-text gaps: prerequisites and misconceptions

Branch `learner/text-gaps`, worktree `learnanything-text-gaps`, created by the
workflow from `main` at `1acf79b2` (router R0 and Slice 2 T1 merged). Prompt:
`docs/specs/implementation_handoffs.md` §4, "Learner-text gaps: prerequisites
and misconceptions". Every item of the prompt is an owner decision
(2026-10-12). Owner decisions in force: recommended defaults accepted; Codex may
run every paid LLM role (estimated cost); the Decider is
`perplexity/pplx-decider-v1.1-27b` on OpenRouter; frictionless defaults (honest
labels, generous defaults, live changes behind kill switches, no shadow
stages).

## Plan (written before coding)

Read: `CLAUDE.md`; architecture `Home.md`; the algorithm-change playbook;
`spec_learner_field_v1.md` §3.1, §4.1, §5.2, G13;
`spec_embedding_consumers_v1.md` §1, §3, §4, §5.8;
`spec_blind_grading_diagnosis_split_v1.md` §3, §5, §7, §8, §12.2;
`spec_action_router_v1.md` §4, §6; `docs/reviews/slice-a-integration-2-3-codex-review.md`
(F4, F5, F11, owner decisions); `docs/reviews/slice-2-t1.md`; `docs/reviews/router-r0.md`;
the stuck-prompt branch's `attempts/stuck.py` (read only, for its interface).

### Shape

One pipeline, `learnloop/diagnosis/text_gaps/` (diagnosis already imports
`tutor` and `placement`; `tutor` never imports it, so no new package cycle).
Each learner text runs once, asynchronously, as a job:

1. **Sources.** A tutor question (`question_events`, after the tutor answers),
   a diagnosis of a wrong answer (`attempt_diagnoses`, after it is applied) and
   a non-empty stuck answer (through a small `StuckTextSource` interface; its
   default adapter reads `learnloop.attempts.stuck.stuck_answers()` when the
   stuck-prompt branch has merged and yields nothing before).
2. **Kind, name first.** The chooser is the model with the whole exchange:
   - the tutor, in the call that answers: `TutorAnswer` gains `learner_gap`
     (the prerequisite's name and one line, and/or the stated belief, written
     BEFORE the kind; prompt version bumped);
   - the diagnoser: its existing output is read deterministically
     (`prerequisite_gap_hypotheses` -> prerequisite, a learner-state event with
     a `misconception_statement` -> misconception, `transient_execution` ->
     slip, else none); no diagnoser prompt change;
   - stuck text: one gap-reader call (route `learner_gap_reader`, unset = the
     diagnosis route) returning the same `NamedGap`.
   The Decider answers the same typed `choice` (prerequisite | misconception |
   slip | wording | none) as a logged second opinion. Both readings go to
   `judgment_ledger` (task `learner_gap_kind`; judge `llm`/`diagnoser` and
   `decider`). `learner_text_gaps.chooser` = `context_model` (default) |
   `decider` selects the authoritative kind; the name always comes from the
   context model (a Decider-only kind with no name is logged, signal only).
3. **Match** with T1's `learnloop.matching` (no parallel matcher), two new
   asymmetric kinds:
   - `same_prerequisite`: the named prerequisite (embedded once, stored as
     `learner_gap/prerequisite`) against `learning_object/statement` vectors
     (a new declared recipe, backfilled by the Phase 1 command). Candidates:
     the item's LO, its declared prerequisite LOs, a vault-wide shortlist
     (stored vectors, top-k; a lexical fallback when the vault has no LO
     vectors) and the prerequisites created that day; all restricted to the
     asking item's subject before ranking (no cross-subject target);
   - `same_belief`: the stated belief against the registry and the holding pen
     (durable misconceptions, holding-pen candidates for the LO and its
     confusable neighbours, plus the `misconception/statement` kNN when
     vectors exist), as the diagnoser's registry candidates are built.
   Every candidate pair is judged by the LLM judge (route `learner_gap_judge`,
   unset = the diagnosis route) AND the Decider, both through `judge_pairs`,
   both in `judgment_ledger` (judge `llm` / `decider`). No score cutoff. For
   prerequisites the chooser switch picks the authoritative judge; for beliefs
   the LLM is authoritative and the Decider is a logged second opinion that
   never joins anything (T1's recommendation).
4. **Act.**
   - Prerequisite, matched: a weak signal on that LO (the field loader reads
     the gap's persisted target, question-time, with its subject). If the
     match is not a declared prerequisite of the item's LO: a separate yes/no
     ("is it needed to do this item?", task `prerequisite_needed`, both
     judges) before adding a `prerequisite` edge; refused on a cycle; labelled
     "added from your question"; one-tap undo deletes it.
   - Prerequisite, missing: one authoring-route call drafts the concept, the
     LO statement and the edge; placed in the asking item's subject (or the
     subject the shortlist points to; never a new subject); written live with
     provenance `learner_text_gap_v1`; seeded with one practice item through
     `tutor/promotions.py` (tutor questions); a light commitment (one delayed
     check: pass -> maintenance, fail -> learning) read by placement; caps:
     `max_creations_per_day` (3), one per learner text; dedupe against the
     day's creations (they are candidates); one-tap undo (LO dormant, edge
     removed). Kill switch `learner_text_gaps.create_prerequisites_enabled`
     (off: nothing new is created and created LOs are not served).
   - Misconception: matched -> a sighting on that registry/holding-pen entry;
     new -> a holding-pen candidate. Promotion stays with T1's rule. A
     tutor question or stuck text that states a belief is now a sighting.
     "Not what I meant" is a `learner_card` `different` verdict.
   - Slip, wording/notation: a signal only. Error types are never created;
     unmatched slip/wording texts are listed for batch review in the report.
5. **Sooner check (successor).** A matched prerequisite on an LO that is
   assumed known or in maintenance brings its next check forward to no sooner
   than `sooner_check_delay_hours` (24) after the gap, never later than it
   was. Algorithm successor `mvp-0.13` (next free after main's `mvp-0.12`),
   kill switch `learner_text_gaps.sooner_check_enabled`.
6. **Events.** Every named gap is a row in `learner_text_gaps` (RAW_LEDGER);
   `named_gaps_for_card()` gives the router's learner-state card its reading.
   No router behaviour.

Also: without a pick (old events, a failed call, the switch off) the F11
grounded rule applies, then the opt-in classifier (unchanged). Asking never
lowers the record (G13): nothing here writes evidence, mastery or
certification. Command-palette asks carry the practice screen's state.

### Files

- New: `src/learnloop/diagnosis/text_gaps/{__init__,contract,kinds,sources,candidates,judges,actions,pipeline,jobs,report,upgrade}.py`;
  `src/learnloop/db/stores/learner_gaps.py`; `src/learnloop/cli/gaps.py`;
  `migrations/177_learner_text_gaps.sql`; tests.
- Changed: `algorithm_versions.py`, `config/schema.py` (+ template snapshots,
  parameter registry), `ai/routing.py`, `tutor/ai_contracts.py`,
  `tutor/tutor_qa.py` (TutorAnswer fields + target persistence only),
  `tutor/promotions.py` (optional extra grounding), `diagnosis/split/jobs.py`
  (enqueue after a diagnosis), `placement/state.py` (commitments, advances),
  `scheduling/scheduler.py` (the advanced check in maintenance),
  `vault/lifecycle.py` (created-LO serving gate), `vault/embedding_recipes.py`
  (`learning_object/statement`), `field/signals.py` (gap targets),
  `db/table_roles.py`, the sidecar (enqueue on ask, worker slot, three RPCs),
  `cli/__init__.py`, `cli/app.py` (`upgrade --to mvp-0.13`), the desktop
  (`AskOverlay`, `App.tsx`, DTO/client).

### Migration (next free: 177; T6 takes 177 at merge, so expect a renumber)

| Table | Role |
|---|---|
| `learner_text_gaps` | RAW_LEDGER: one row per learner text read: source, readings, kind, name, action, target with subject, what was created |
| `learner_text_gap_reversals` | RAW_LEDGER: one-tap undo and "not what I meant" |
| `learner_text_gap_jobs` | WORKFLOW: the lease-fenced queue |
| `learner_gap_check_advances` | RECEIPT: a sooner check (LO, intent, original and advanced due) |
| `learner_gap_commitments` | RECEIPT: a created LO's light commitment (its delayed check) |

No DERIVED table, so no replayer. Head fixture `migration_head_176` -> `177`.

### Spend caps and model routes

- `ai.routing.learner_gap_judge` and `ai.routing.learner_gap_reader` (unset =
  the resolved diagnosis route: Codex on the subscription by default,
  `estimated_only`); `ai.routing.learner_gap_decider` (a decider task: unset =
  `openrouter_decider`, never a chat fallback); creation drafts on
  `ai.routing.authoring`; the seed item on the promotion path's routes.
- Per learner text one `ReviewSpend` budget (`learner_text_gaps.max_calls_per_text`,
  `max_usd_per_text` for metered routes; the Decider at its listed input price,
  embeddings at the known price). `learnloop gaps run --dry-run` prints the
  plan and sends nothing.

### `judgment_ledger` writes

`learner_gap_kind` (unary: the source; `llm`, `diagnoser`, `decider`),
`same_prerequisite` and `same_belief` (pairs; `llm`, `decider`, and
`learner_card` for "not what I meant"), `prerequisite_needed` (LO x item;
`llm`, `decider`).

### Tests

Fake-model tests for each kind and action; grounded candidates only; the
chooser and the Decider both logged; fallback to the grounded rule; edge
cycle refusal and undo; creation dedupe, undo, seed item and daily cap; a
tutor question that states a belief reaches the holding pen; the successor's
kill-switch parity; the report's dry run; table roles; mobile allowlist.
