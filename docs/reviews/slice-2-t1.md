# Slice 2 T1 (M3): recurrence with authority

Branch `slice-2/t1`, worktree created by the workflow from `main` at
`22023ab4` (Slice 1 M2 merged). Overrides in force (owner, 2026-10-12,
`implementation_goal.md` §1a): the prerequisite "Slice 1's exit review
supports T1" is waived because report gates are post-hoc, so this stage is
built without waiting for it. **Pattern-link trust stays unverified until the
owner runs Slice 1 M1 and the S1.5 exit review**; whether to switch a vault to
the successor stays the owner's decision.

## Plan (written before coding)

Read: `CLAUDE.md`; architecture `Home.md`; the algorithm-change playbook;
`spec_embedding_consumers_v1.md` §0-§4, §5.8, §12-§15;
`spec_blind_grading_diagnosis_split_v1.md` §5-§7, §9, §12;
`implementation_goal.md` §1a; `docs/reviews/slice-1-m2.md`; Phase 5a's
in-progress `ops/embedding_compare.py` (`git show slice-a/phase-5a:...`).

### Shape

- **One generic matcher, parameterized by kind** (owner-directed):
  `learnloop/matching/` (new package, no domain imports). A `MatchKind`
  names its `judgment_ledger` task, subject kind, embedding identity
  (`record_kind`/`field`/`task_prefix`), AI route, prompt version, the
  question the judge answers and how a subject is rendered. The engine:
  `shortlist` (stored-vector kNN, top-k, optional benchmark-set cutoff,
  structured scope filter applied before ranking, settled-pair skip),
  `judge_pairs` (one isolated structured call per pair through an injected,
  spend-admitted executor; `same | different | unsure` + rationale; every
  verdict appended to `judgment_ledger` with model, prompt version and input
  hash; idempotent per question/judge/prompt/input) and `union` (incremental
  union in adjudication order with the no-chaining refusal, generic over node
  ids and authority tiers). Nothing in it knows about misconceptions; the
  learner-text-gaps stage adds a `same_prerequisite` / registry kind.
- **First kind: hypothesis recurrence** (`same_cause`). Subjects are causal
  hypothesis heads keyed by `episode_key` (the `hypothesis/statement` vectors
  are keyed the same way), text = the Slice 1 recipe (statement + mechanism
  slug), scope = target facet, else learning object (Slice 1 §9.5).

### Files

- `src/learnloop/recurrence.py`: `recurrence_key(h, groups=None)` returns the
  group key when the statement's class was merged; singleton classes keep the
  exact `statement_normalized` key (so a vault with no merges is unchanged).
- `src/learnloop/matching/{__init__,kinds,shortlist,judge,union}.py`.
- `src/learnloop/substrate/recurrence_groups.py`: assembles the three union
  sources from raw ledgers (statement classes from `causal_hypotheses`,
  validated diagnoser citations from `attempt_diagnoses` + receipts, `same_cause`
  verdicts from `judgment_ledger` plus card taps from `diagnosis_feedback`),
  resolves attempt-level links to statement classes deterministically, runs
  the union and writes the DERIVED tables. Called by its replayer, after
  materialization in normalization (fingerprint-skipped when inputs are
  unchanged), and after new verdicts. Makes no model or embedding call.
- `src/learnloop/db/stores/recurrence.py`: registered SQL owner for the new
  tables.
- `src/learnloop/diagnosis/recurrence/`: the same-cause kind, the live step in
  the diagnose job (embed this attempt's new hypotheses, shortlist, judge,
  refresh) run before normalization so promotion and K=3 see the merges, the
  escalation receipt, the backlog, the same-answer/different-cause guard and
  the M3 signals report.
- `src/learnloop/ops/recurrence_benchmarks.py`: B1 (Eedi 2024 loader, raw vs
  LLM-written hypothesis queries, BM25, hybrid, recall@25/MAP@25) and B3
  (vault replay: AUC, recall@k under the production shortlist rule, the
  recall-oriented cutoff and judge load per model, merge precision/recall).
  Written to Phase 5a's `CompareSuite` contract (`name`, `description`,
  `load`, `plan`, `run`, `ctx.vectors`) and run through a small local runner
  until 5a merges (integration point recorded below). No competing
  `embeddings compare` command.
- Changed: `algorithm_versions.py` (`mvp-0.11`), `ops/vault_upgrade.py` +
  `cli/app.py` (`upgrade --to mvp-0.11`, refused while the guard has a false
  merge or has not run for the configured judge), `config/schema.py`
  (`[recurrence]`, `ai.routing.same_cause_judge`), `config/template.py`
  (snapshots), `ai/routing.py`, `db/repositories.py` (group map, the
  `recurrence_key` sites, escalation feedback), `diagnosis/misconceptions.py`
  (refresh after materialization; holding-pen lookup by group key),
  `diagnosis/causal_factor_deferral.py`, `tutor/durable_promotion.py`,
  `diagnosis/error_hunt.py`, `diagnosis/split/jobs.py` (the T1 step),
  `diagnosis/split/card.py` + sidecar + `DiagnosisCard.tsx` (escalation block
  and its one-tap rating), `cli/embeddings.py` (`adjudicate`), new
  `cli/recurrence.py`, `substrate/rebuild_orchestrator.py` (replayer).

### Migration (next free: 171; mobile M1 takes 171 at merge, so expect a renumber)

| Table | Role |
|---|---|
| `hypothesis_recurrence_groups` | DERIVED: members of merged groups only (episode, statement class, group key, how it joined) |
| `hypothesis_recurrence_review` | DERIVED: refused unions, exact-key conflicts, unresolved links, registry disagreements (§3.5) |
| `hypothesis_recurrence_state` | DERIVED: one row: input fingerprint, builder version, active flag, counts |
| `recurrence_escalations` | RECEIPT: what an escalation showed (group, earlier answers, chosen repair, whether its approach differs) |
| `diagnosis_feedback` | RAW_LEDGER rebuilt in place: `response` also accepts `escalation:helped`, `escalation:didnt_help`, `escalation:not_sure` |

One replayer (`recurrence_groups`) owns the three DERIVED tables and runs
before `learning_state`. Head fixture `migration_head_170` → `171`.

### Algorithm successor and kill switches

- `RECURRENCE_GROUP_ALGORITHM_VERSION = "mvp-0.11"` (the spec's label was a
  placeholder; Phase 6 is building another successor in parallel, so expect a
  relabel at merge), immediate successor of `mvp-0.10`, keeping the split
  (`DIAGNOSIS_SPLIT_VERSIONS`) and the P0 projection namespace. Owner-run
  `learnloop upgrade --to mvp-0.11`; the template stays where it is.
- Kill switches: `recurrence.enabled` (off: keys revert to exact statements
  from the next normalization, vault open or rebuild), `recurrence.judge_enabled`
  (no live judge calls), `recurrence.escalation_card_enabled` (UI).

### Spend caps and model routes

- `ai.routing.same_cause_judge`, unset → the resolved diagnosis route (Codex
  on the subscription by default; `estimated_only`). Live: at most
  `recurrence.judge_max_pairs_per_attempt` calls per diagnose job, plus one
  capped embed-on-write batch for the attempt's new hypotheses (metered).
- Backlog (`learnloop embeddings adjudicate --task same_cause --backlog`),
  guard (`learnloop recurrence guard`) and B1/B3 all take Slice A caps and a
  `--dry-run` that prints the estimate and sends nothing.
- No cosine cutoff in code: `recurrence.blocking_cutoffs` (model id → cutoff)
  is empty until B3 sets it; without one, top-k alone blocks.

### `judgment_ledger` writes

- `same_cause` verdicts from the judge: `left_kind = right_kind = 'hypothesis'`
  (episode keys), judge `llm`, model, prompt version, input hash.
- Guard verdicts: the same task on planted subjects (`planted_hypothesis`).
- The M1 owner verdicts already import through `learnloop diagnose
  import-links` (judge `owner`, attempt pairs); T1 reads them.

### Tests

Union and no-chaining (A~B, B~C, A≁C never one group); singleton keys equal
the old keys and a no-merge vault rebuilds identically; R1 (a judge stubbed
to `different` never merges, a score alone never merges or rejects); replay
makes zero model and embedding calls; the live step merges a reworded
recurrence and K=3 escalation fires on it; the escalation receipt and card
block; the escalation tap; the guard blocks the upgrade on a false merge;
the backlog's dry run sends nothing and the run respects caps; B1 loader and
metrics on a tiny fixture; B3 on a seeded vault; upgrade + head fixture path;
kill-switch parity; table roles and the single replayer.

## As built

Commits on `slice-2/t1` (from `22023ab4`): `67bc38f2` (the stage), `5fd10f4d`
(fixes found by the live run on a backup copy, the renumber to 172),
`db59f8ac` (attempt-level verdicts resolve to the two answers' own classes),
plus this review.

> **Renumbered while finishing.** `main` moved on while this branch was built:
> mobile M1 merged as `171_mobile_capture.sql` (and T8 merged). This stage's
> migration is therefore `172_recurrence_groups.sql` and the head fixture is
> `fixtures/migration_head_172` (the 170 head upgraded through 172 only; it has
> no 171 on this branch). At merge the head fixture is regenerated through
> 171 and 172; the DB reference regenerates the same way. `mvp-0.11` is still
> the next free label on `main` (Phase 6 claims one too, so expect a relabel).

### What T1 does

- **One step, parameterized by kind** (`src/learnloop/matching/`, imports
  only `ai` and `db`). `MatchKind` names the `judgment_ledger` task, the
  subject kind, the embedding identity of its subjects, the AI route and
  purpose, the prompt version, the question and the same/different/unsure
  guidance, and how a subject is shown. `shortlist_pairs` ranks stored
  vectors (mean-centred cosine, structured filter applied before ranking,
  settled pairs skipped before ranking, top-k, and a cutoff only when one is
  configured for that model). `judge_pairs` makes one isolated structured
  call per pair through an executor the caller supplies (spend admission and
  receipts stay with the caller), appends each verdict at once
  (`judge='llm'`, model, prompt version, input hash; no score), and skips any
  pair already judged under the same prompt and input. `union_with_refusals`
  is the no-chaining union. `tests/test_matching.py` drives it with a kind
  that is not about misconceptions (learning objectives); the learner-text
  gaps stage registers its prerequisite and sighting kinds the same way.
- **The first kind: hypothesis recurrence** (`diagnosis/recurrence/kind.py`,
  task `same_cause`, prompt `same-cause-judge-v1`, route
  `ai.routing.same_cause_judge`, unset = the resolved diagnosis route).
  Subjects are causal-hypothesis episodes keyed by `episode_key` (the key
  their `hypothesis/statement` vectors already use, so no re-embedding).
  Scope is Slice 1 §9.5's: an earlier attempt, the same target facet, else
  the same learning object. Only learner-state hypotheses are judged.
- **Recurrence groups** (`substrate/recurrence_groups.py`, migration 172).
  Nodes are exact statement classes (the old key, always grouped). Edges:
  validated diagnoser citations of each attempt's diagnosis in force
  (`judge='diagnoser'`), `same_cause` verdicts in `judgment_ledger`
  (hypothesis-keyed judge rows; attempt-keyed M1 owner/LLM imports) and the
  card's "not the same mistake" taps (`learner_card`). Per pair the highest
  authority wins (owner > verifier > llm = diagnoser > learner_card; latest
  within a tier; `unsure` never counts); `same` edges are applied oldest
  first and a union that would join two classes with a `different` at equal
  or higher authority is refused and logged (`refused_union`). A citation
  is resolved to classes exactly: `cause:<event>:<cause>` names the
  diagnosed attempt's class; an existing hypothesis id is matched through
  the event whose `prior_hypothesis_id` continues it (the live diagnoser
  cites this way); the cited attempt's class is the anchor class when
  present, else its only (learner-state) class, else the only one on the
  anchor's facet. Anything else is an `unresolved_link` review case and joins
  nothing. Only merged groups get rows; group keys are `rg:` + a hash of the
  root (oldest) class. Review cases also carry `exact_key_conflict` (a
  `different` inside one exact class) and §3.5's `registry_disagreement`
  (the diagnoser's registry match vs the top-1 registry neighbour, when the
  kNN ranking covered at least two records).
- **The key switch.** `recurrence_key(h, groups)` returns the group key for a
  merged class and the exact statement otherwise. Every §7.6 site loads the
  map once (`Repository.recurrence_group_map()`): candidate projection,
  holding-pen lookups (a raw statement or a key resolves to its group),
  `misconception_candidates_for_learning_object`, promotion of a group's
  members (each keeps its own statement, which the exact-key code had
  overwritten with the representative's), the LO statement filter, factor
  signatures and the K=3 count, durable promotion arms (c)/(d) and error-hunt
  minting. The would-merge log keeps the exact key. The map is empty unless
  the vault is at `mvp-0.11` with `recurrence.enabled`, so every key is
  exact below the successor or with the switch off.
- **When groups refresh.** After materialization in `_normalize_compositional`
  (before the deferral sweep and the holding-pen lookup), after judge
  verdicts, after a "not the same mistake" tap, at the upgrade and by the
  `recurrence_groups` rebuild replayer (first after `activity_substrate`). A
  cheap fingerprint of the ledgers it reads skips unchanged rebuilds. No
  model or embedding call.
- **The live judge** (`diagnosis/recurrence/live.py`), inside the diagnose
  job after the diagnosis is persisted and before its normalization:
  materialize, refresh, embed this attempt's hypotheses (one capped, metered
  batch, receipted under the attempt), shortlist against earlier
  hypotheses, judge at most `recurrence.judge_max_pairs_per_attempt` (4)
  pairs (per-job caps; Codex counts calls), refresh. Pairs past the cap wait
  for the backlog. Failures are logged, never fail the diagnosis. So the
  attempt's own promotion and K=3 count already see its merges.
- **Escalation and the card.** After normalization, when the diagnosis's
  highest-weight learner-state cause has a hypothesis on at least
  `ESCALATION_RECURRENCE_K` (3) distinct attempts up to this one (its
  group), `recurrence_escalations` records the group, the earlier answers
  (newest first), the chosen repair and whether its operator differs from
  every repair shown for those earlier answers. The card leads with "Third
  time with this one - trying a different approach" only when it does;
  otherwise "Third time with this one" and an honest note that the repair is
  the same kind as before. The earlier answers open like citations. One tap
  (Helped / Didn't help / Not sure) is a `diagnosis_feedback` row with
  `response` `escalation:helped|didnt_help|not_sure` (migration 172 rebuilds
  the table to accept them; rows and ids preserved); it is refused when the
  diagnosis has no escalation and never forwarded to a factor.
- **Backlog** (`learnloop embeddings adjudicate --task same_cause --backlog`):
  embeds hypotheses missing a vector for `embedding.model`, shortlists every
  learner-state hypothesis against its earlier in-scope ones, judges the
  unsettled, unjudged pairs (earliest first, `--max-pairs-to-judge`), refreshes
  groups. One `SpendCaps` budget for both routes; `--dry-run` builds no client
  and reports pairs, vectors and the estimate (a lower bound on pairs while
  vectors are missing).
- **The guard** (`learnloop recurrence guard`, §3.6): 10 authored
  same-answer/different-cause pairs and 5 paraphrase pairs (built in, no
  learner data), plus an M1 run's planted `same_answer_different_cause` cases
  with `--from-run`. Judged with the live kind and prompt; verdicts go to the
  ledger on `planted_hypothesis` subjects, which never touch vault groups.
  `learnloop upgrade --to mvp-0.11` refuses while any negative is judged
  `same` (latest verdict per pair under the current prompt), while any
  negative is unjudged, or while the verdicts came from a model other than
  the one the judge route now resolves to.
- **The successor.** `mvp-0.11` (`RECURRENCE_GROUP_ALGORITHM_VERSION`), in
  `P0_SUCCESSOR_VERSIONS` and `DIAGNOSIS_SPLIT_VERSIONS` (it keeps the split),
  plus `RECURRENCE_GROUP_VERSIONS` for the gate. `upgrade_to_mvp011`
  (`diagnosis/recurrence/upgrade.py`, which keeps `ops` free of a new
  `ops -> diagnosis` edge) refuses non-predecessors and a failing guard,
  freezes the manifest, prepares the groups and the projection receipt, then
  renames the config atomically. Defaults fingerprint recorded for
  `mvp-0.11` (the `[recurrence]` section moves the mvp-0.9 and mvp-0.10
  snapshots too; recomputed). Kill switches: `recurrence.enabled`,
  `recurrence.judge_enabled`, `recurrence.escalation_card_enabled`.
- **Benchmarks** (`diagnosis/recurrence/benchmarks.py`). B1 and B3 implement
  Phase 5a's `CompareSuite` contract (`name`, `description`, `load`, `plan`,
  `run`, `ctx.vectors(model, texts, dims=, task_prefix=)`); the one LLM role
  (B1's hypothesis writer, on the diagnoser's route) goes through
  `ctx.complete` or 5a's `ctx.caller.call`. B1: the Eedi Kaggle files
  (`train.csv`, `misconception_mapping.csv`) plus a `manifest.json`; one
  query per labelled wrong answer; raw vs LLM-written hypothesis queries;
  each model raw and mean-centred, BM25 and a BM25 + embedding hybrid;
  recall@25 and MAP@25; hypotheses and vectors cached in the output
  directory. B3: the vault's labelled hypothesis pairs re-scored per model
  (AUC, recall@k of confirmed matches under the production shortlist rule,
  the recall-oriented cutoff and its judge load, merge precision/recall when
  the union is replayed without the label source); it recommends a config
  line only once 30 confirmed matches back it.
- **M3 report** (`learnloop recurrence report --out m3.md`): escalation taps,
  an audit sample of merged groups (statements shown: a local file),
  "not the same mistake" share of citations shown, diagnostic episodes per
  recurring cause before and after the switch, the next attempt after an
  escalated vs a non-escalated diagnosed failure (directional), review-case
  volume and verdicts by judge. Wilson intervals, no thresholds, no call.
- **Also fixed** (Slice 1 M2 code T1 reads): a validated citation's
  `claim_index` is its position before validation, but the stored proposal
  keeps only surviving claims, so `record_pattern_verdicts` could read the
  wrong claim's relation after a dropped claim; it now finds the claim that
  cites that attempt with that quote (`claim_for_citation`).

### Integration point with Phase 5a (`embeddings compare`)

Phase 5a's harness (`ops/embedding_compare.py`, on `slice-a/phase-5a`) is not
on this branch's base, so B1/B3 run through `learnloop recurrence bench` until
it merges. At that merge, in `cli/embeddings.py`'s `embeddings_compare`, call
`register_suites(SUITES)` (from `learnloop.diagnosis.recurrence.benchmarks`)
before `run_compare`, and extend `--suite`'s help to `b1, b3`. The
registration is in the composition root on purpose: `ops -> diagnosis` would
be a new back-edge. The interim command can then become an alias or go.

## Deviations

- **Module placement.** The plan put B1/B3 in `ops/recurrence_benchmarks.py`
  and the upgrade in `ops/vault_upgrade.py`; both live under
  `diagnosis/recurrence/` instead (B3 reads diagnosis subjects, and
  `ops -> diagnosis` would be a new import back-edge). The migration is 172,
  not 171 (see the renumber note above).
- **The display's K is three answers, the deferral's K is three further
  recurrences.** The escalation card fires on the third distinct attempt in a
  group ("Third time with this one"); the existing deferral exit
  (`escalated_unrepaired`) still needs `ESCALATION_RECURRENCE_K` recurrences
  after the case's first factor, i.e. a fourth answer, now counted over
  groups. Both read the same constant; the two notions were already distinct.
- **Groups are vault-wide statement classes; the consumers stay per learning
  object** (spec: "consumers are unchanged in shape"). A merge changes keys
  everywhere the classes occur; the holding pen, promotion and the K=3 count
  still look within the LO. The escalation count is vault-wide (it is a
  display).
- **A rebuild applies every recorded verdict to all history.** Groups are
  not as-of: a verdict recorded today (the backlog, a later judge call)
  regroups older answers at the next rebuild. Live, a merge takes effect from
  the next normalization; `learnloop rebuild` re-applies it to the past
  (promotion and the deferral exits), which is what the shadow rebuild
  previews. The upgrade itself does not rebuild.
- **Only learner-state hypotheses are judged**; all concrete classes still
  join through citations and verdicts.
- **Attempt-level verdicts** (M1 imports) join classes only when a citation or
  one class per side settles which; otherwise they are `unresolved_link`
  review cases. The learner's tap is resolved through the diagnosis it was
  given on, so it applies to exactly the cited pair.
- **Kill-switch latency.** Turning `recurrence.enabled` off empties the
  projection at the next normalization, vault refresh path or rebuild; reads
  in between (an open candidate list) still see the last groups.
- **The TUI** shows the diagnosis as before; the escalation block is in the
  desktop card only.
- **No different-repair generation call.** When the diagnosis has no repair
  with a different operator, the card says so instead of claiming one.

## Live runs on a backup copy (paid calls)

All on `fixtures-local/t1-linear_algebra`, a backup-API copy
(`copy_tree_with_databases`) of this worktree's tracked `fixtures/linear_algebra`
(70 attempts, 2 concrete hypotheses, joint history). The tracked vaults were
never written. The copy was upgraded `mvp-0.8 -> mvp-0.9 -> mvp-0.10`, given
the embedding route and profile (`openrouter_embedding`, `[embedding]` both
switches on), and every paid command ran `--dry-run` first.

| What | Route | Calls | Tokens in / out (cached) | Cost |
|---|---|---|---|---|
| Guard: 15 planted pairs | Codex `codex_low` (gpt-5.6-sol) | 15 | 154,636 / 814 (44,800) | subscription, `estimated_only` |
| 3 live answers: blind grading | Codex `codex_low` | 3 | 49,518 / 5,581 | subscription |
| their diagnoses | Codex `codex_low` | 3 | 75,535 / 7,542 (11,136) | subscription |
| the live same-cause judge | Codex `codex_low` | 8 | 83,142 / 648 (35,840) | subscription |
| live embeddings (hypotheses, registry shortlist) | OpenRouter `qwen/qwen3-embedding-8b` | 7 | 1,360 | $0.0000136 |
| backlog embedding | OpenRouter `qwen/qwen3-embedding-8b` | 1 | 74 | $0.00000074 |
| B3 | OpenRouter `qwen/qwen3-embedding-8b`, `openai/text-embedding-3-small` | 2 | 623 + 607 | $0.0000062 + $0.0000121 |

Metered total about $0.000033 (OpenRouter reported cost). The backlog and B3
calls were not receipted in the vault during the run (fixed in `5fd10f4d`, with
tests); their costs above come from the commands' spend reports.

What the runs showed:

1. **The guard passed on the real judge**: 0 false merges on the 10
   same-answer/different-cause pairs, 5 of 5 paraphrases merged, about 5 s a
   call. The rationales name the mechanism (e.g. "the first attributes it to
   ignoring the coefficient ... the second to failing to change the sign"),
   not the shared answer. The upgrade to `mvp-0.11` then succeeded.
2. **Shadow rebuild, no merges** (before the live answers): at `mvp-0.11` the
   facet / mastery / schedule deltas equal a same-version `mvp-0.10` shadow
   exactly (2 / 7 / 48 real changes in both; the only extra difference is the
   `algorithm_version` stamp on 77 facet rows). Live database hash unchanged.
3. **End to end live.** Three wrong answers on three items of one LO, each
   skipping the "is it an operation on this set at all?" check in different
   words (histograms, nonempty sets, probability simplex). The diagnoser
   (`full`) cited the earlier answers (validated); the judge decided 8 pairs
   (7 `same`, 1 `different`); the third answer escalated: recurrence count 3,
   the two earlier answers, repair `elicit_mapping_codomain_audit`, which
   differs from the earlier `elicit_invariant_closure_gate` and
   `elicit_mapping_codomain_counterexample`, so the card says "Third time
   with this one - trying a different approach". About 100 s per answer
   (grade, diagnosis, judging).
4. **No-chaining, live.** The judge's one `different` keeps two groups apart
   (2 `refused_union` cases), though a diagnoser citation would have linked
   them: groups 6 and 3 classes.
5. **Found and fixed by the run** (`5fd10f4d`): the live diagnoser cites
   EXISTING hypotheses by id with the event's `prior_hypothesis_id` set,
   which the first resolution rule left `unresolved_link` (the diagnosed
   answer had four learner-state classes); registry disagreements were
   logged against a one-record kNN universe (score 0); backlog and B3 calls
   were not receipted.
6. **Shadow rebuild, with merges**: same-version `mvp-0.11`, `--set
   algorithms.algorithm_version=mvp-0.10` and `--set recurrence.enabled=false`
   give identical facet / mastery / schedule deltas (2 / 7 / 51); the
   recurrence replayer builds 2 groups / 9 members only in the first. A full
   rebuild of two further backup copies with and without groups gives the
   same durable misconceptions (1), hypothesis heads (17) and factor
   statuses; the only difference is a surrogate factor id the projection
   sync mints on each rebuild. With three answers no group has reached the
   fourth answer the deferral exit needs, and arm (b) promotion was already
   blocked by the open factors, so the documented differences are the
   recurrence projection and its review cases.
7. **B3 on that copy**: 9 confirmed matches, 1 negative; both models AUC
   0.78, recall@3 0.78, recall@10 1.0 (the cutoff it would set is negative:
   with 9 matches it recommends nothing, as built). B1 did not run: the Eedi
   data needs a Kaggle login.

## Test results (gate)

Run on `8404a695` (the code as delivered; the review's last commit changes
only this file). The same counts held on `db59f8ac` before the package marker
was added.

- `uv sync --extra dev`, `uv pip install pypdfium2`: done (no mobile extra:
  this stage does not touch `learnloop_mobile`).
- `uv run lint-imports --no-cache`: **10 kept, 0 broken**.
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto`: **7331 passed**,
  0 failed, 164 s.
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability`:
  **78 passed**, 7253 deselected, 67 s.
- Frontend (`apps/learnloop-tauri`): `npm install` ok; `npm run typecheck`
  clean; `npm test` **76 passed in 18 files**.
- DB reference: `db_generate_reference.py` then `db_validate_reference.py`:
  `errors: []` (schema head 172, 281 table notes, 590 effective config
  leaves in 34 sections); `validate_vault.py` passed (1,048 notes).
- Not in the gate: `cargo check` (no Rust change; the toolchain on this
  machine is broken, blocker B3).

The gate ran with `TMPDIR` pointed into the worktree: the shared `/tmp` tmpfs
was full (16 GB, mostly another project's session files), which broke shell
here-documents and tool output for a while. Nothing of this stage's lives
there now.

An earlier full-suite run (before `5fd10f4d`) had 9 failures, all fixed: the
parameter registry did not classify the new `[recurrence]` numeric leaves
(the registry audit tests and the two registry CLI tests), the CLI help
snapshot predated the new commands, and the P0 cutover test asserts a clean
registry audit.

New tests: `test_matching.py` (4), `test_recurrence_groups.py` (15),
`test_recurrence_live.py` (12), `test_recurrence_deferral.py` (3),
`test_recurrence_commands.py` (20, two in the durability lane),
`test_recurrence_benchmarks.py` (6), vitest `DiagnosisCard.test.tsx` (+3);
updated `test_recurrence_key.py`, `test_rebuild_orchestrator.py` (stale rows
for the new tables), the CLI help snapshot, the head-fixture paths.

## Files touched

- **New:** `migrations/172_recurrence_groups.sql`;
  `src/learnloop/matching/{__init__,kinds,shortlist,judge,union}.py`;
  `src/learnloop/substrate/recurrence_groups.py`;
  `src/learnloop/db/stores/recurrence.py`;
  `src/learnloop/diagnosis/recurrence/{__init__,kind,judging,live,backlog,guard,upgrade,report,benchmarks}.py`;
  `src/learnloop/cli/recurrence.py`; `tests/recurrence_fakes.py` and the six
  test files above.
- **Changed:** `recurrence.py`, `algorithm_versions.py`, `ai/routing.py`,
  `config/schema.py`, `config/template.py`, `db/repositories.py`,
  `db/table_roles.py`, `diagnosis/{causal_factor_deferral,error_hunt,misconceptions}.py`,
  `diagnosis/split/{card,jobs}.py`, `tutor/durable_promotion.py`,
  `substrate/rebuild_orchestrator.py`, `ops/vault_upgrade.py` (public
  `rewrite_algorithm_version`), `params/parameter_registry.py`,
  `cli/{__init__,app,embeddings}.py`; the desktop card
  (`DiagnosisCard.tsx`, `api/dto.ts`, `api/client.ts`, vitest); the DB
  reference scripts and regenerated notes; `fixtures/migration_head_170` →
  `migration_head_172` and its five path references; `tests/test_architecture.py`
  (SQL owner), `tests/test_recurrence_key.py`, `tests/test_rebuild_orchestrator.py`,
  `tests/cli_help_snapshot.json`.

## Owner-run commands

On a `fixtures-local/` backup copy first (`learnloop.db.copies.copy_tree_with_databases`),
then on the vault. The vault must be at `mvp-0.10` with embeddings enabled
(`ai.routing.embedding = "openrouter_embedding"`, the `openrouter_embedding`
profile, `[embedding] enabled = true`, `backfill_enabled = true`).

```bash
# 0. M1 link verdicts (judge = owner) into judgment_ledger, once M1 has run
uv run learnloop diagnose import-links --run <m1-run-dir> --vault <vault> --dry-run
uv run learnloop diagnose import-links --run <m1-run-dir> --vault <vault>

# 1. The guard (blocks the switch on any false merge); --from-run adds M1's planted cases
uv run learnloop recurrence guard --vault <vault> --dry-run
uv run learnloop recurrence guard --vault <vault> [--from-run <m1-run-dir>]

# 2. The backlog: embed missing hypothesis vectors, judge the shortlisted history
uv run learnloop embeddings adjudicate --task same_cause --backlog --dry-run --vault <vault>
uv run learnloop embeddings adjudicate --task same_cause --backlog --vault <vault>

# 3. B3 (vault replay; sets recurrence.top_k / blocking_cutoffs once >= 30 confirmed matches)
uv run learnloop recurrence bench --suite b3 --vault <copy> --model qwen/qwen3-embedding-8b \
  --model qwen/qwen3-embedding-4b --model google/gemini-embedding-2 \
  --model openai/text-embedding-3-large --model openai/text-embedding-3-small \
  --embedding-price-per-million <upper bound> --dry-run
#    then without --dry-run; copy the printed [recurrence] lines into learnloop.toml

# 4. B1 (Eedi 2024): download train.csv and misconception_mapping.csv from Kaggle
#    ("Eedi - Mining Misconceptions in Mathematics", login required) into <dir>,
#    add <dir>/manifest.json {"sources": [{"name": ..., "version": "2024", "licence": ...}]}
uv run learnloop recurrence bench --suite b1 --benchmark <dir> --vault <copy> --max-cases 400 \
  --embedding-price-per-million <upper bound> --dry-run
#    then without --dry-run (hypothesis writer: the diagnosis route, Codex)

# 5. Shadow-rebuild review before the switch (playbook item 7)
uv run learnloop rebuild --shadow --json --vault <vault>                                          # same version
uv run learnloop rebuild --shadow --set algorithms.algorithm_version=mvp-0.11 --json --vault <vault>
#    compare: facet/mastery/schedule should differ only by the version stamp unless merges
#    change a promotion; `learnloop recurrence groups --vault <copy>` lists the groups

# 6. The switch (refused while the guard fails or has not run for this judge)
uv run learnloop upgrade --to mvp-0.11 --vault <vault>
#    optional: re-apply groups to past promotions and escalations
uv run learnloop rebuild --vault <vault>

# 7. After 2-4 weeks at mvp-0.11: the M3 signals report
uv run learnloop recurrence report --vault <vault> --out m3-report.md
```

Kill switches: `[recurrence] enabled = false` (exact keys again),
`judge_enabled = false` (no live judge calls), `escalation_card_enabled =
false` (UI).

## Open questions

1. **Pattern-link trust is unverified.** The prerequisite "Slice 1's exit
   review supports T1" was waived (report gates are post-hoc). Until the owner
   runs Slice 1 M1 and the S1.5 exit review, nothing shows that diagnoser
   citations are trustworthy; T1 gives them `diagnoser` authority (equal to
   the judge). Whether and when to switch a vault to `mvp-0.11` is the
   owner's decision.
2. **Should the judge also see in-context pairs?** As built (handoff wording)
   it judges every shortlisted pair the citations did not settle, including
   pairs the diagnoser saw and did not cite (spec §3.1 says only pairs not in
   the diagnoser's context). Narrowing it saves calls; spec P6 says drop the
   separate judge if B3 shows citations alone recover nearly all recurrences.
3. **Escalation K.** The card fires on the third answer; the deferral exit on
   the fourth (three further recurrences). Align them?
4. **Different repair.** When the diagnosis offers no repair with a new
   operator, the card says so. Add a bounded "propose a different repair"
   call at escalation time?
5. **Learner taps vs the diagnoser.** By the spec's authority order a "not the
   same mistake" tap cannot undo a diagnoser citation or a judge `same`; it
   only blocks equal-or-lower links. Raise learner taps above the diagnoser
   for the learner's own answers?
6. **Rebuild re-interpretation.** A verdict recorded today regroups older
   answers at the next rebuild (groups are not as-of). Keep, or make groups
   as-of the verdict time?
7. **B3 minimum.** It recommends a cutoff only from 30 confirmed matches; the
   owner vault had 2 concrete hypotheses at the base. Is 30 right?
8. **Migration and label.** 172 and `mvp-0.11` on this branch; expect a
   renumber / relabel against Phase 6 and later merges.
