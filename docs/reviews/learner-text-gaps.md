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

## As built

Commits on `learner/text-gaps` (from `1acf79b2`): `943e5a3c` (the pipeline),
`55b62f2b` (tests, head fixture 177, the overlay's undo and the palette's ask
state), `eca2cb4b` (DB and config references), `6edf7d1f` (fixes found by the
live run), plus this review.

### The pipeline (`src/learnloop/diagnosis/text_gaps/`)

- **`contract.py`**: `LearnerText` (source, text, anchors, the asking item's
  subject, the context model's `GapReading`), the Decider's typed questions
  (`KIND_QUESTION`, a `choice` over the five kinds; the pair and "needed?"
  choices), `NeededVerdict` and `PrerequisiteDraft`, the stuck-text reader's
  task. `LearnerGap` itself lives in `tutor/ai_contracts.py` (the tutor fills
  it; `tutor` may not import `diagnosis`). Its fields are written name-first:
  `prerequisite_name`, `prerequisite_line`, `belief_statement`, then `kind`.
- **`sources.py`**: the three sources. A tutor question reads the reading the
  tutor persisted with its answer (`question_events.source_context.learner_gap`,
  with the model and prompt version). A diagnosis is read deterministically
  from the validated proposal (refs resolve to one LO; a facet ref only when
  one declared prerequisite LO owns it). Stuck answers come through
  `StuckTextSource`; the default `StuckAnswersAdapter` imports
  `learnloop.attempts.stuck.stuck_answers` when it exists and yields nothing
  until then (integration point: no code change when `practice/stuck-prompt`
  merges; its rows' `has_text`, `learner_answer_md` and `reading.confusion_quote`
  are what the adapter reads).
- **`kinds.py`**: two asymmetric `MatchKind`s on T1's component:
  `same_prerequisite` (query `learner_gap/prerequisite`, `retrieval-query`;
  pool `learning_object/statement`, a new declared recipe) and `same_belief`
  (query `learner_gap/belief`; pool `misconception/statement`, keyed
  `durable:`/`candidate:` exactly as the diagnoser's registry shortlist keys
  them, so its paid vectors are reused).
- **`candidates.py`**: grounded candidates, filtered to the asking subject
  BEFORE ranking. Prerequisites: the item's LO, today's creations, then the
  declared prerequisites and the vault-wide shortlist taking turns for the
  judge's budget (`judge_max_pairs`, 8). The shortlist ranks stored vectors
  (`shortlist_pairs`, plain cosine across the two prompt spaces, top-k, no
  cutoff); a vault with no LO vectors gets a lexical shortlist of the same
  size (a nominator only). Beliefs: the diagnoser's registry scope (durable
  beliefs on the LO, its concept and confusable neighbours; the holding pen on
  the LO) plus the registry kNN when vectors exist.
- **`judges.py`**: one `TextBudget` (`ReviewSpend`) per text: the LLM routes at
  their billing (Codex `estimated_only`; metered at the owner's
  `metered_price_per_million`), the Decider at its listed input price, the
  query embedding at the known price. `LLMPairExecutor` (judge `llm`) and
  `DeciderPairExecutor` (judge `decider`, a `choice` same/different/unsure read
  from the same rendered pair; its rationale records its probabilities) plug
  into `judge_pairs`. `log_reading` and `decider_kind` append the kind
  verdicts; `ask_needed` the "needed?" verdicts of both judges.
- **`actions.py`**: the edge (cycle check over `prerequisite` edges and LO
  declarations; provenance `learner_text_gap_v1` on the edge), the creation
  (concept, LO and edge written under the vault lock; the seed through
  `promote_tutor_question` with the asking LO's source notes as grounding),
  the holding pen (`misconception_candidates` row, or an occurrence on a
  matched legacy candidate), the sooner check (`advance_check`), and
  `reverse_gap` (undo an edge, undo a creation, "not what I meant").
- **`pipeline.py`**: `process_learner_text` (idempotent per source; one ledger
  row with any advance and commitment in one transaction) and
  `named_gaps_for_card` (the router card's typed events).
- **`jobs.py`**: the queue (`learner_text_gap_jobs`; lease-fenced; a creation's
  progress in the payload so a retry never writes twice; 3 attempts, then a
  `failed` row with no target); enqueued by the sidecar after a tutor or
  reader answer and by `apply_diagnosis` after a live diagnosis (and the
  attempt's stuck text); `sweep_backlog` for `learnloop gaps run --backlog`.
- **`report.py`**, **`upgrade.py`** (`upgrade_to_mvp013`: from mvp-0.12, or
  earlier through `upgrade_to_mvp012` and its guard).

### Where it touches existing code

- `tutor/ai_contracts.py`, `tutor/tutor_qa.py`: `TutorAnswer.learner_gap`, the
  rules in the prompt, `TUTOR_QA_PROMPT_VERSION = mvp-0.9-tutor-qa-learner-gap`;
  the reading persisted in `source_context.learner_gap` and returned. The
  opening (no learner question) must leave it null. Nothing else in
  `tutor_qa.py` changed (T6 owns its spans).
- `tutor/promotions.py`: optional `grounding_learning_object_ids` (their
  canonical sources ground auto-apply, as reader spans do).
- `diagnosis/split/jobs.py`: `apply_diagnosis` enqueues the gap reading last
  (never fails the diagnosis). `diagnosis/split/history.py`: a holding-pen
  candidate a learner's text named has no source attempt, so it is visible to
  the diagnoser's registry block by write time (gated by the switches); without
  this a sighting could never be matched by a later diagnosis.
- `field/signals.py`: a tutor question's persisted gap target replaces its
  grounded facet mapping (a weak `prerequisite` observation, 0.15 mass, under
  the daily cap); a stuck answer's or diagnosis's gap adds one. Off with
  `learner_text_gaps.enabled`; undone creations excluded.
- `placement/state.py`: light commitments read as decisions with source
  `learner_text_gap`; mvp-0.13 advances bring an open assumption's
  `first_review_due` forward (`advanced_from` kept) and mark a maintenance LO's
  check due (`gap_check_due_by_lo`) until an answer at or after it. Only
  `load_placement_state` passes the switches; every other caller reads the
  predecessor's state. A "don't know this" on a created LO closes its
  commitment (it has no `assumption_decisions` row to name).
- `scheduling/scheduler.py`: the maintenance gap check is served like the
  assumed check (`gap_sooner_check`), and the reasons say so honestly ("a check
  brought forward: your question pointed at this topic"; "the one check on a
  topic added from your question").
- `vault/lifecycle.py` + `learnloop_sidecar/serving.py`: a created LO's items
  are not served while `create_prerequisites_enabled` (or the pipeline) is off.
- Sidecar: `get_learner_text_gap`, `reverse_learner_text_gap`; the ask RPCs
  (`ask_tutor_question`, `reader.ask`) queue the reading and return
  `learnerGap`; the post-attempt worker has a third `gaps` slot. Placement
  labels: a created LO is "added from your question (one check pending)",
  never "assumed (not tested)"; the map lists it apart.
- Desktop: `AskOverlay` polls the reading after an answer and shows only what
  happened ("Added from your question: <LO>", "Noted: this builds on <LO>
  (link added from your question)", "Noted a possible mix-up: <belief>") with
  its one-tap undo / "not what I meant"; `App.tsx`'s command-palette ask
  carries the practice screen's `openedAtMs` and `attemptProgress`
  (`PracticeScreen.onAskState`); Tauri passthroughs for the two RPCs.
- Config `[learner_text_gaps]` (modelled defaults, not in the 80-line
  template): `enabled`, `chooser = "context_model"`, `decider_enabled`,
  `top_k = 4`, `judge_max_pairs = 8`, `judge_timeout_seconds`,
  `add_edges_enabled`, `create_prerequisites_enabled`,
  `max_creations_per_day = 3`, `seed_check_delay_days = 1`,
  `sightings_enabled`, `sooner_check_enabled`, `sooner_check_delay_hours = 24`,
  `max_calls_per_text = 30`, `max_usd_per_text = 0.25`,
  `metered_price_per_million` (unset). Routes `learner_gap_judge`,
  `learner_gap_reader` (unset: the resolved diagnosis route) and
  `learner_gap_decider` (a decider task). Parameter registry classifies the
  numeric leaves. Defaults snapshots recomputed for every version;
  `mvp-0.13`: `59239469…f38a`.

### Migration 177 (`migrations/177_learner_text_gaps.sql`)

| Table | Role |
|---|---|
| `learner_text_gaps` | RAW_LEDGER, append-only triggers, `UNIQUE (source_kind, source_id)` |
| `learner_text_gap_reversals` | RAW_LEDGER, append-only, one of each reversal per gap |
| `learner_text_gap_jobs` | WORKFLOW (lease-fenced queue) |
| `learner_gap_check_advances` | RECEIPT |
| `learner_gap_commitments` | RECEIPT |

No DERIVED table, no replayer. `fixtures/migration_head_177` is a backup-API
copy of `migration_head_176` with only 177 applied (`wal_checkpoint(TRUNCATE)`,
`journal_mode=DELETE`, `integrity_check` ok, `foreign_key_check` empty); the
eight test paths and both reference scripts point at it; `SCHEMA_HEAD = 177`.

### `judgment_ledger` writes

`learner_gap_kind` (left = the source; `llm` for the tutor and the stuck-text
reader, `diagnoser`, `decider` with its probability as `score`),
`same_prerequisite` and `same_belief` (left `learner_gap:<source>`, right
`learning_object:<id>` / `misconception:durable|candidate:<id>`; `llm`,
`decider`, and `learner_card` `different` for "not what I meant"),
`prerequisite_needed` (left the LO, right the practice item; `llm`, `decider`).
All within R0's judge CHECK.

## Deviations and decisions

- **Asynchronous.** The reading runs off the request path (a queue and a
  worker slot), so the tutor's answer is never slower; the overlay polls for
  the result (up to about 90 s).
- **Diagnoses are read, not re-asked.** A diagnosis names prerequisites only
  from its validated neighbourhood (`prerequisite_gap_hypotheses`), so a
  diagnosis can match a declared prerequisite (judge `diagnoser`, no pair
  judge) but never names a missing one; its misconceptions already go through
  `registry_match` (`belief_registry_path`, logged only). The diagnoser prompt
  is unchanged.
- **The Decider names nothing.** With `chooser = "decider"`, its kind is acted
  on only when the context model named a gap of that kind; otherwise `unnamed`.
- **A missing prerequisite is created only after the authoritative judge says
  `different` to every candidate.** An `unsure` blocks creation
  (`unmatched_prerequisite`, reason `unsure`), and so does a judge that gave no
  verdict.
- **Lexical fallback shortlist** when the vault has no LO vectors (embeddings
  off by default): without it, a vault with embeddings off would create
  duplicates of LOs outside the declared neighbourhood. It only nominates.
- **Sightings and promotion.** A sighting records an occurrence (legacy
  candidate rows) or only the ledger row (durable beliefs, projected
  candidates). It adds no item id, so it never counts as an independent
  surface group: promotion stays with the existing rule on diagnosed attempts.
- **The creation's edge is not "needed?"-checked**: the draft states why the
  asking item builds on it (one call), and the learner can undo it.
- **Seed for stuck text**: none (no tutor exchange to promote); the created LO
  is labelled "no practice item yet". Stuck text is not on main yet.
- **The light commitment needs placement** (mvp-0.11+); below it a created LO
  is ordinary new material.
- **The TUI** asks the tutor without queuing a reading; `learnloop gaps run
  --backlog --history` picks such questions up when they carry a reading.

## Live runs on a backup copy (paid calls)

All on `fixtures-local/ltg-la`, a backup-API copy (`copy_tree_with_databases`)
of this worktree's tracked `fixtures/linear_algebra` (one subject,
`vector-spaces`; 21 LOs; 99 items), upgraded `mvp-0.8 -> 0.9 -> 0.11` with
the owner's upgrade functions (no paid call). The tracked vaults were never
written. Codex is exhausted until 2026-10-18, so the copy routes
`tutor_qa`, `learner_gap_judge`, `learner_gap_reader` and `authoring` to the
default OpenRouter profile (`deepseek/deepseek-chat`; one seed attempt on
`google/gemini-2.5-flash`), embeddings to `openrouter_embedding`
(`qwen/qwen3-embedding-8b`, both switches on), the Decider on its code-default
route, and `metered_price_per_million = 1.5` (an upper bound). Every paid
command ran `--dry-run` first.

| What | Model | Calls | Tokens in / out | Cost (OpenRouter-reported) |
|---|---|---|---|---|
| LO + registry backfill (22 records) | qwen3-embedding-8b | 1 | 900 | $0.000009 |
| 8 tutor questions | deepseek-chat | 8 | 30,819 / 1,935 (agent runs; not receipted by the helper script) | about $0.011 (estimate) |
| query embeddings | qwen3-embedding-8b | 8 | 299 | $0.000003 |
| kind (Decider) | pplx-decider-v1.1-27b | 8 | 2,789 / 8 | $0.000056 |
| same_prerequisite pairs | deepseek-chat / Decider | 50 / 50 | 24,418 / 2,354; 24,725 / 50 | $0.0087 / $0.0005 |
| same_belief pair | deepseek-chat / Decider | 1 / 1 | 409 / 50; 416 / 1 | $0.0002 / $0.00001 |
| prerequisite_needed | deepseek-chat / Decider | 1 / 1 | 369 / 35; 370 / 1 | $0.00015 / $0.00001 |
| drafts | deepseek-chat (2), gemini-2.5-flash (1) | 3 | 2,231 / 507 | $0.0014 |
| seeds (promotion analysis + authoring) | deepseek-chat, gemini-2.5-flash | 3 + 6 | 96,533 / 7,601 | $0.040 |
| seed-path check outside the pipeline (gemini json_schema rejected with 400; gpt-4.1-mini x3, each with one repair) | | about 8 | about 100,000 (not receipted) | under $0.05 (estimate) |

Receipted total $0.0513 (133 physical requests); with the estimates, under
$0.12 in all.

What the runs showed:

1. **Readings.** The tutor named a gap in all 8 questions, name first
   (e.g. "Expanding Binomial Products: the method to expand the product of two
   binomials"; "The zero vector is the number 0" as a belief). Kind agreement
   with the Decider: 8/8.
2. **Matching works on stored vectors; the shortlist found what the declared
   list missed.** "Definition of list equality" matched
   `lo_interpret_finite_lists_and_their_equality` (both judges `same`), which
   is not a declared prerequisite of the asking LO; it came from the vault-wide
   shortlist. In the first round the declared list had crowded it out of the
   judge's budget (the LLM said `unsure` on another LO, so nothing was created:
   the conservative rule held); fixed by letting the two take turns
   (`6edf7d1f`).
3. **"Needed?" disagreed**: the LLM said no ("comparing finite lists is
   unrelated to proving vector identities"), the Decider yes (0.63); the LLM is
   authoritative under the default chooser, so no edge was added. Both logged.
4. **The LLM judge over-matches; the Decider was stricter.** On "Roots of
   unity" deepseek-chat judged `lo_read_and_interpret_complex_numbers` the
   same (the Decider: different), so the gap matched it. On "Multiplying
   complex numbers" it said `same` to three LOs; the item's own LO was taken
   (the first in order). Pair agreement LLM vs Decider: 46/50 (0.92, Wilson
   [0.81, 0.97]). This is the evidence the report gathers for the chooser
   question.
5. **Creation, live.** Three prerequisites the vault lacks were drafted and
   written in `vector-spaces` with their edges ("Expand Products of
   Binomials" -> complex multiplication; "Proof by Mathematical Induction";
   "Simplify expressions with square roots"); a later binomial question did not
   create a fourth. One was undone with `learnloop gaps undo` (LO dormant,
   edge deleted). The daily cap (3) was reached.
6. **The seed failed on every OpenRouter model tried**, honestly: the LO
   stays, labelled "no practice item yet", and no commitment is written. First
   cause (fixed): the seed unit was admitted with the default 2,000-token output
   budget, which truncated the authoring proposal. Remaining cause (not this
   stage's code): deepseek-chat, gemini-2.5-flash and gpt-4.1-mini all fill
   `AuthoringProposalItem.target` on a create (forbidden by its validator) and
   gpt-4.1-mini then omits `proposed_entity_id`; gemini rejects the strict
   schema as too large. Field descriptions on the contract fixed the first
   rule but not the second, so they were reverted (shared contract, out of
   scope); see open question 3. The seed path itself is covered by the fake
   tests; on Codex (the owner's authoring route) it is the existing promotion
   path.
7. **Shadow rebuild (playbook item 7)** on the copy: a same-version shadow
   (`mvp-0.11`) and a candidate `--set algorithms.algorithm_version=mvp-0.13`
   give identical facet / mastery / schedule changes (2 / 7 / 48) once the
   `algorithm_version` stamp is ignored; the candidate also activates the
   (empty) recurrence groups; the live database hash is unchanged
   (`4f0b1008…`). The sooner check changes serving only, and only through
   advance receipts, of which the copy has none at mvp-0.11.

Not run live: the stuck-text reader (no stuck answers on main) and a live
sooner check (the copy would need the mvp-0.12 guard's judge calls first);
both are covered by fake tests.

## Tests

New, all with fakes (`tests/text_gap_fakes.py`: the gap LLM, a choice-answering
Decider, the tutor, a seed proposal):

- `tests/test_learner_text_gaps.py` (29 cases): the tutor names the gap and
  it is persisted; a declared prerequisite matches with both judges logged and
  no edge; an undeclared match adds an edge after a "needed?" yes, with
  one-tap undo (and the wrong reversal refused); "needed?" no adds none; a
  cycle is refused; candidates stay in the asking subject; a missing
  prerequisite is drafted, written, seeded through the promotion path and
  committed (placement reads the commitment); undo of a creation (LO dormant,
  edge and commitment gone); a second question matches the day's creation;
  the daily cap; the creation switch stops serving created LOs; `unsure` never
  creates; a tutor question that states a belief reaches the holding pen (and
  the diagnoser's registry block), "not what I meant" withdraws it with a
  `learner_card` verdict; a sighting on an existing candidate with the Decider
  logged but never joining; the Decider as chooser (kind; prerequisite judge);
  no reading -> nothing targeted, grounded rule; slip and wording signal only
  and listed for batch review, no error type created; the matched target is the
  question's weak signal with its subject, and the switch restores the
  grounded rule; G13 (no evidence, mastery or attempt row moves); the router
  card's events; a text is read once; the LO recipe; the vault-wide kNN
  shortlist (stored vectors; the far LO never reaches the judge); the CLI dry
  runs send and write nothing; declared and shortlisted LOs share the judge's
  budget; a library question's anchor.
- `tests/test_learner_text_gaps_flow.py` (13 cases): an assumed LO's check
  brought forward (not before the bound, then served with its reason) and the
  kill switch's parity; the switch-off queue equals the predecessor version's
  and nothing is written below mvp-0.13; a maintenance LO's check until
  answered; the diagnosis source without a call and its kinds; stuck text
  through the source interface and the backlog dry run; the queue (once per
  text, failure handling, the switch); a job that keeps failing ends as a
  `failed` row with no target; the sidecar (queue on ask, poll, label, undo,
  vault reload); the report and its dry run; the upgrade.
- Vitest: `AskOverlay.test.tsx` (+2: the label and its undo; nothing shown
  when nothing happened), `PracticeScreen.test.tsx` (+1: the palette's ask
  state).
- Updated: `test_embedding_backfill.py` (the LO recipe; the count tests keep
  their one facet and one item record), `test_mvp011_upgrade.py`,
  `test_recurrence_commands.py` (LATEST is mvp-0.13; the default upgrade goes
  through mvp-0.12), `test_placement_sidecar.py` (the map's
  `addedFromQuestion`), `test_mobile_allowlist.py` (the two new RPCs and the
  two ask RPCs desktop-only), `test_architecture.py` (the store's SQL owner),
  the eight head-fixture paths, `cli_help_snapshot.json`.

## Files touched

- **New:** `migrations/177_learner_text_gaps.sql`;
  `src/learnloop/diagnosis/text_gaps/{__init__,contract,kinds,sources,candidates,judges,actions,pipeline,jobs,report,upgrade}.py`;
  `src/learnloop/db/stores/learner_gaps.py`; `src/learnloop/cli/gaps.py`;
  `src/learnloop_sidecar/handlers/learner_gaps.py`; `fixtures/migration_head_177`
  (replaces `migration_head_176`); `tests/text_gap_fakes.py`,
  `tests/test_learner_text_gaps.py`, `tests/test_learner_text_gaps_flow.py`.
- **Changed:** `algorithm_versions.py`, `ai/routing.py`, `config/schema.py`,
  `config/template.py`, `params/parameter_registry.py`, `db/table_roles.py`,
  `tutor/ai_contracts.py`, `tutor/tutor_qa.py`, `tutor/promotions.py`,
  `diagnosis/split/jobs.py`, `diagnosis/split/history.py`, `field/signals.py`,
  `placement/state.py`, `scheduling/scheduler.py`, `vault/lifecycle.py`,
  `vault/embedding_recipes.py`, `cli/__init__.py`, `cli/app.py`; sidecar
  `context.py`, `post_attempt_worker.py`, `serving.py`,
  `handlers/{__init__,tutor_qa,reader,placement,knowledge_map}.py`; desktop
  `AskOverlay.tsx`, `PracticeScreen.tsx`, `App.tsx`, `PlacementControls.tsx`,
  `api/{dto,client}.ts`, `src-tauri/src/{commands,main}.rs` and the vitest
  files; the DB reference scripts and regenerated notes.

## Owner-run commands

On a `fixtures-local/` backup copy first (`learnloop.db.copies.copy_tree_with_databases`),
then on the vault. Nothing needs a command to start: with the defaults the
pipeline reads every tutor question, reader question and live diagnosis from
the next app start (Codex runs the judge, the reader and the draft;
the Decider runs on OpenRouter).

```bash
# 0. Optional, for the vault-wide shortlist: LO statements and the registry
#    (needs embeddings enabled on the vault; a few cents at most)
uv run learnloop embeddings backfill --vault <vault> --record-kind learning_object/statement \
  --record-kind misconception --dry-run
uv run learnloop embeddings backfill --vault <vault> --record-kind learning_object/statement --record-kind misconception

# 1. The successor (sooner checks): from mvp-0.12 (or through its guard from earlier)
uv run learnloop rebuild --shadow --json --vault <copy>
uv run learnloop rebuild --shadow --set algorithms.algorithm_version=mvp-0.13 --json --vault <copy>
#    facet / mastery / schedule deltas equal apart from the version stamp
uv run learnloop upgrade --to mvp-0.13 --vault <vault>

# 2. Backlog: earlier stuck answers (once the stuck prompt merges), and with
#    --history earlier tutor questions with a reading and live diagnoses
uv run learnloop gaps run --vault <vault> --backlog --history --dry-run
uv run learnloop gaps run --vault <vault> --backlog --history --max-texts 20 --max-cost-usd 0.50

# 3. What was read and done; reverse anything as the owner
uv run learnloop gaps list --vault <vault> [--show-text]
uv run learnloop gaps undo <gap id> --vault <vault> --reversal undo_edge|undo_creation|not_this_belief

# 4. After 2-4 weeks: the report (dry run first; --out adds the batch review
#    of slip, wording and unmatched readings, with your own text)
uv run learnloop gaps report --vault <vault> --dry-run
uv run learnloop gaps report --vault <vault> --out gaps-report.md
#    To compare choosers: run a period with [learner_text_gaps] chooser = "decider"
#    and compare undo, first-check pass and "not what I meant" rates per period.
```

Kill switches (`[learner_text_gaps]`): `enabled` (the pipeline; off also
restores the grounded rule in the field loader), `create_prerequisites_enabled`
(no creation, created LOs not served), `add_edges_enabled`,
`sightings_enabled`, `decider_enabled`, `sooner_check_enabled` (mvp-0.13).

**What to watch:** created-then-undone (each one is a wrong creation); the
first-check pass rate of created prerequisites (very high: the learner knew
it; very low: the seed item or the LO is off); "not what I meant" taps on
beliefs; LLM vs Decider agreement on the kind and on pairs (the live run's
deepseek judge over-matched where the Decider did not); `unmatched_prerequisite`
rows with reason `unsure` (a judge that is unsure a lot blocks creation);
the daily cap being hit.

## Open questions

1. **Which chooser?** The default (the context model) is authoritative for
   kinds and prerequisite matches. The live run (deepseek-chat as the judge)
   showed the LLM judge over-matching where the Decider said different. With
   Codex as the judge this may differ; the report gives agreement now and
   outcome rates per chooser once both have run for a period.
2. **Seeds on OpenRouter.** Every OpenRouter model tried produced an
   `AuthoringProposal` its validator rejects (`target` set on a create, a
   missing `proposed_entity_id`), so seeds fail there (honestly labelled).
   This is the shared authoring contract, not this stage's code; Codex (your
   authoring route) is the tested path. Should the contract describe both
   rules in its schema, or tolerate `target` on a create when it names the
   payload's parent?
3. **Sightings and promotion.** A tutor question or stuck text that states a
   belief adds an occurrence, not an independent surface group, so it never
   promotes a belief by itself (promotion still needs diagnosed answers). Count
   it toward independence instead?
4. **The creation's edge** is added with the draft, without a separate
   "needed?" call (the learner can undo it). Ask "needed?" there too?
5. **Stuck answers** are read by a separate reader call once the stuck prompt
   merges (the diagnoser of the same answer reads its causes too). Keep both,
   or read stuck text only through its diagnosis?
6. **Thresholds of the defaults** (owner-accepted): `max_creations_per_day = 3`,
   `seed_check_delay_days = 1`, `sooner_check_delay_hours = 24`,
   `judge_max_pairs = 8`, `top_k = 4`.
7. **Migration and label.** 177 and `mvp-0.13` on this branch; T6 takes 177 and
   the stuck prompt, DL1 and R1 ship successors too, so expect a renumber and a
   relabel at merge.

## Gate

Run on `6edf7d1f` (the code as delivered; the review commit after it changes
only this file), `TMPDIR` in the gitignored `fixtures-local/tmp`:

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | OK |
| `uv run lint-imports --no-cache` | **12 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8207 passed**, 0 failed (46 warnings), 198 s |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **87 passed**, 8120 deselected, 83 s |
| Frontend (`apps/learnloop-tauri`): `npm install`, `npm run typecheck`, `npm test` | typecheck clean; **112 passed in 23 files**; `npm run frontend:build` built |
| `db_generate_reference.py` then `db_validate_reference.py` | `errors: []`: schema 177, 302 table notes, 657 config leaves in 38 sections |
| `validate_vault.py` (extra) | passed (1,073 notes) |

The first full run (on `55b62f2b`) had one failure, fixed in `6edf7d1f`:
`test_capture_route_recovery.py::test_destination_retry_recovers_one_result[tutor-receipt_write]`
(a recovered ask did not replay its `learnerGap`). Its log also showed the
gaps worker failing on a library question (`Note` has no `title`), fixed in
the same commit and now tested. `cargo check` not run (two passthrough lines
added in the shape of their neighbours; the toolchain on this machine is
broken, per earlier stages).
