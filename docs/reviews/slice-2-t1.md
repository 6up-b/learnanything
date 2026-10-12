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
