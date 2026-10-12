# Slice A Phase 5a: PF-b generation, verification, selection, publishing

**Branch:** `slice-a/phase-5a`, created from `main` at `974c5647` (Phase 1, the
Phase 2/3 integration and its Codex re-review). The handoff's branch instruction is
overridden: the worktree and branch already existed.

## Plan (written before coding)

Specs read: `CLAUDE.md`; `docs/learnloop-architecture-vault/Home.md`;
`docs/algorithm-change-playbook.md`; `spec_slice_a_practice_and_field_v1.md` in full;
`spec_embedding_consumers_v1.md` §§5.1, 5.3, 5.4, 5.6, 5.7, 5.8 and §13; the Phase 1,
Phase 3 and integration reviews; `db/table_roles.py`.

### Files to add

| File | Role |
|---|---|
| `migrations/169_pf_generation.sql` | `pf_candidates` (WORKFLOW), `item_skeletons` (WORKFLOW), `item_fingerprints` (DERIVED) |
| `db/stores/pf.py` | The only SQL writer for the three tables |
| `content/authoring/pf_sandbox.py` | Bubblewrap sandbox runner built on `concept_animation._sandboxed_command`: fails closed without `bwrap` on every platform; CPU, memory, file-size and wall-clock limits; no vault paths or keys in the environment; generator-program and sympy-equivalence harnesses |
| `content/authoring/pf_contracts.py` | Wire models and versioned prompts for every PF role |
| `substrate/item_fingerprints.py` | Pure symbolic fingerprints in the 077 namespaces, plus the one DERIVED replayer |
| `ops/pf_calls.py` | Role-routed caller: spend admission, per-call checkpoint (`model_work_checkpoints`), receipts, `estimated_only` for Codex |
| `ops/pf_generation.py` | Plan, dry run and run: generator programs, the ensemble path, the single-shot pilot arm; verification, filters, solver panel, structure check, freshness gate |
| `ops/pf_selection.py` | Lexical diversity kernel, MMR and Vendi scores (pure) |
| `ops/pf_publish.py` | Publication into the family as ordinary items, capped per UTC day |
| `ops/embedding_compare.py` | The shared `learnloop embeddings compare` harness with two suites: `b2` and `valid_alternative` |
| `ops/pf_reports.py` | Pilot and scaling-check reports (generation-path comparison, blind pairwise LLM judge, usage signals) |
| `cli/pf.py` | `learnloop pf generate / publish / status` |

### Files to change

`config/schema.py` (`[pf]` section; `pf_proposers`, `pf_selection_judge` routes; list
routes), `config/template.py` (`[pf] generation_enabled = false`, defaults fingerprint),
`params/parameter_registry.py` (`pf.*` operational), `ai/routing.py` (two tasks, list
resolution), `vault/models.py` (`difficulty_source = "solver_panel"`),
`vault/embedding_recipes.py` (`item/skeleton`), `db/table_roles.py`,
`substrate/rebuild_orchestrator.py` (one replayer), `db/repositories.py` (claim one mint
request by id; the generic rotation claim skips `pf_*` jobs), `cli/embeddings.py`
(`compare`), `cli/evaluation.py` (`eval pf-pilot`, `eval pf-scaling`), the sidecar
settings display of list routes, the head fixture and generated references.

### Migrations

One migration, `169_pf_generation.sql` (next free at branch time; Phase 5b is being
renumbered to 169 separately, so expect a renumber at merge). Head fixture
`migration_head_168` → `migration_head_169` by the `CLAUDE.md` procedure.

### Algorithm successors and kill switches

No algorithm successor: publishing verified items is a content change (Slice A §0.3).
Kill switch `pf.generation_enabled`, off in the template; it gates every paid PF command
and publication. `pf.max_published_per_day` (default 10) caps publication per UTC day.
`item_fingerprints` holds rows only for family members, so vaults without families
rebuild unchanged.

### Spend caps and routes

Every paid command uses the Phase 1 framework: `--dry-run` first; candidate, pair, call,
retry, token and dollar caps before each request; unknown metered prices fail closed;
Codex routes run on the subscription (no physical-request bound; token and dollar caps
recorded but not enforced; `estimated_only` on receipts; call and candidate caps still
apply). Routes: `pf_generator`, `pf_proposers` (list; at least two distinct model slugs,
else refused), `pf_solver_panel` (one profile or a list; P10 default three solves per
model), `pf_reference_verifier` (agreement plus the LLM-written sympy check),
`pf_isomorph_judge` (structure check and freshness), `pf_selection_judge`. The scaling
check's tiers are configured route lists `[pf.scaling] cheap` / `frontier`.

### `judgment_ledger` writes

`answer_equivalence` (per panel solve: LLM agreement, then the sandboxed sympy check as
`verifier`), `reference_verified` (per candidate), `isomorph` (structure check against
the parent; freshness against same-LO items), `selection` (ensemble judge),
`pf_publish` (publication decision), `pilot_rating` (blind pairwise judge). Workflow
tables hold pipeline state only; every report reads verdicts from the ledger.

### Tests

Sandbox (network, vault reads and writes outside scratch denied; fails closed without
bubblewrap; limits), generator programs (invariance, CAS), ensemble (two distinct
proposers, panel disagreement never published, structure check, the selection judge
never offered unverified candidates), freshness and fingerprints, solver-panel
difficulty, publication cap and card/membership, replay never executes a generator,
no-family rebuild unchanged, dry-run makes no calls, resume never repays, Codex
`estimated_only`, the compare harness suites, the pilot/scaling reports, CLI help, a
fake-model end-to-end run of both paths on a `fixtures-local/` copy.
