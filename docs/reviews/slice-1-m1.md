# Slice 1 M1: offline review of blind grading and history-aware diagnosis

## Plan (written before coding)

Branch `slice-1/m1`, worktree created from `main` at `aa9320f8` by the
workflow (the prompt's branch instruction is overridden). All five arms
(a)–(e) are built in one go (owner, 2026-10-12), and the contracts are shaped
for reuse by M2 and Slice 2 T1.

Read: `CLAUDE.md`; architecture `Home.md`; the algorithm-change playbook;
`spec_blind_grading_diagnosis_split_v1.md` in full (build targets: §4, §5
including §5.6, §9.4, §12 M1 row and §12.1, §13 E1–E6, the M1 tests in §14);
`spec_slice_a_practice_and_field_v1.md` §4 and §5.

### Files

- **AI layer (infrastructure).**
  - `ai/transport.py`: capability `READ_ONLY_WORKSPACE`;
    `StructuredRequest.workspace`; `execute_structured_operation(workspace=)`
    refuses a workspace on a transport without the capability.
  - `ai/providers/codex.py`: the SDK client honours the workspace. The app
    server, the thread and the turn all start with `cwd=<workspace>` (it
    replaces `vault_root`, never joins it), in Codex's read-only sandbox with
    approvals off. It fails closed when the installed SDK cannot express a
    read-only sandbox.
  - `ai/routing.py` + `config/schema.py`: new routes `diagnosis` (unset →
    the resolved grading route), `diagnosis_judge` and `diagnosis_generator`
    (unset → active provider). Effective-defaults snapshot updated; no
    `[diagnosis]` config section yet (M1 settings are CLI options over a
    `DiagnosisSettings` dataclass that M2's config section will map onto).
- **Blind grader** — `attempts/blind_grading.py`: `BlindGradingContext` (no
  history-capable field), `BlindGradingProposal` (§4.2 field order:
  `local_analysis_md` → `repaired_traces[]` with ids → localization →
  `exercised_facets` last; `validity_scope`, no causal fields), the
  `mvp-2.0-blind-local-grader` prompt, calibration identities
  `grading_prompt_v2_blind` / `blind_grading_proposal_v1`, and a validator
  that maps onto `GradingProposal` and reuses `validate_codex_grading_proposal`.
- **Diagnoser** — package `diagnosis/split/`:
  - `settings.py` (history modes, §12 defaults, versions);
  - `history.py` (typed blind-grade-equivalent records, a vault-backed
    history store with as-of cutoff and legacy causal stripping, a static
    store for planted learners, the one-hop LO neighbourhood);
  - `context.py` (deterministic `DiagnosisContext` assembly for
    `exact | full | snapshot | hybrid`, token budget with oldest-first
    truncation and disclosure, cache-stable layout, context hash);
  - `contract.py` (`DiagnosisProposal`, recite-first variant, prompt);
  - `validation.py` (§5.4 validators with `validation_report`, S4 citation
    validity grouped by surface group, firewalls, `anchoring_suspect`);
  - `snapshot.py` (§5.6 as-of export, manifest hash, deletion on exit);
  - `retrieval.py` (§9.4 hybrid: exact ∪ kNN over `attempt/divergence`
    through the Phase 1 client and store, reciprocal-rank fusion, exact
    fallback);
  - `legacy_view.py` (arm (a): the stored joint diagnosis through the §4.2
    mapping in reverse — the seed of M2's `diagnosis_for_attempt`);
  - `diagnoser.py` (assemble → call → validate → receipt).
- **M1 harness** — package `diagnosis/offline_review/`: planted scenarios
  (changed cause, paraphrased recurrence, same answer/different cause), E1
  probes (valid alternative, real-vs-synthetic), the blind two-pass LLM judge,
  the runner (sample, scratch copy, stages, spend), the report, the
  spot-check screens, and the pattern-link import.
- **Scratch store** — `db/stores/diagnosis_review.py`: `review_*` tables
  created only inside the scratch copy (never a vault migration).
- **CLI** — `cli/diagnose.py`: `learnloop diagnose run | report | review |
  import-links`.

### Migrations, successors, kill switches

None. M1 adds no vault migration and no algorithm successor, and serves
nothing differently. Every model output lands in a backup-API scratch copy
under the run directory. The only vault writes are the ones the spec asks
for: the owner's optional spot-check verdicts on arm (a) go to
`diagnosis_adjudications` (as `learnloop diagnosis adjudicate` does), and
`import-links` appends pattern-link verdicts to `judgment_ledger`.

### Spend caps and routes

Every paid component is its own route: `grading` (blind grader),
`diagnosis` (diagnoser, arms b–e), `diagnosis_judge` (pairwise, planted-cause
and pattern-link judging), `diagnosis_generator` (planted traces, E1 probes),
`embedding` (arm c). `learnloop diagnose run --dry-run` prints the planned
calls, tokens and cost per route without copying the database or building a
client. Metered routes keep the full Phase 1 cap set; Codex routes are billed
to the subscription, so their token and dollar caps are not enforced and their
cost is reported as `estimated_only` (Slice A §5 rule 6); call caps apply to
every route. Unknown metered prices fail closed unless the owner passes a
price.

### `judgment_ledger` writes

Into the scratch copy's ledger: every judge verdict (`diagnosis_pairwise`,
`diagnosis_rating`, `planted_cause_match`, `same_cause`) with model, prompt
version and input hash. Into the vault's ledger, only on `import-links`:
`same_cause` rows (judge `llm`, and `owner` for spot-check link verdicts).

### Tests

`test_blind_grading_contract.py`, `test_diagnosis_contract.py`,
`test_diagnosis_context.py`, `test_diagnosis_history_modes.py` (including the
Codex workspace and snapshot lifecycle), `test_diagnose_review.py` (end to
end with fakes on a `fixtures-local`-style copy, spot-check, import), plus
routing/config snapshot updates and the CLI help snapshot.
