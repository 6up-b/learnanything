# Facet identity at mint time, and a dedupe command

Branch `facets/identity`, worktree `learnanything-facet-identity`, base
`7b44c9b0` (main, which includes Slice 2 T5). Handoff:
`docs/specs/implementation_handoffs.md` §4, "Facet identity at mint time, and a
dedupe command". Evidence: `docs/reviews/facet-duplicate-judging-2026-10-12.md`
(data in `docs/reviews/data/facet-duplicate-judging-2026-10-12.json`).

## 1. Plan (written before coding)

**What changes.** Source-set synthesis and append stop minting duplicate
facets. After the shards (or the append reconciliation) return and before the
gates, a cheap LLM judge sees each concept neighbourhood of candidate facets
whole and partitions it into same-skill sets (`merge`, `absorb`,
`keep_distinct`). Candidates that T5 nominates against registered facets go to
the same judge, which can turn a mint into an alias of (or an absorb into) the
existing facet. A one-off `learnloop facets dedupe` gives the judge each
concept neighbourhood of an existing vault and applies the same actions. Every
`merge` and `absorb` applies live, is listed in the ingest/dedupe result, and
has a one-tap undo.

**Shared component.** Slice 2 T1's `learnloop.matching` (shortlist + pairwise
judge + ledger + union) has not merged. This stage builds the same pattern in
its own package, `learnloop.content.facet_identity`, so the two branches do not
collide. The judge here is a *group* judge (the spec forbids
pairwise-then-transitive linking for facets), so only the shortlist maths and
the ledger conventions are shared. Reuse point at merge: the within-run
shortlist can call `matching.shortlist.centred_unit`, and the Decider's
per-pair verdicts can be partitioned with `matching.union.union_with_refusals`.

**Files to add**
- `src/learnloop/content/facet_identity/`:
  - `views.py`: what the judge sees for one facet; the payload union for
    `merge` and `absorb`.
  - `grouping.py`: concept neighbourhoods (same concept, concept-graph
    adjacency, the lexical near-duplicate pairs, an embedding top-k shortlist
    when vectors exist), bounded to `max_group_size`.
  - `judge.py`: the partition contract, prompt, validation; the LLM executor
    (spend caps, receipts, checkpoint, ledger); the Decider adapter
    (per-pair typed `choice` questions, partitioned with a no-chaining union).
  - `plan.py`: the in-run consolidation plan and the attach (D2) decisions for
    one synthesis or append run.
  - `actions.py`: the action ledger, the vault-level merge, and undo.
  - `dedupe.py`: the `learnloop facets dedupe` orchestration (plan, dry run,
    judge, apply).
- `src/learnloop/cli/facets.py`: `learnloop facets dedupe|actions|undo`.
- Sidecar `facet_identity` handlers: list actions, undo one.
- Frontend: the ingest activity panel lists a synthesis job's facet actions
  with an Undo button.
- Tests (fakes only), including a fake-judge regression set built from the
  study's 39 facets and labels (`tests/data/facet_identity_regression.json`).

**Files to change**
- `content/synthesis/source_set_synthesis.py`: run the plan after graph
  structuring; `_normalize` applies it (retired candidates are not minted;
  their ids become aliases of the survivor, so on-disk references keep the
  original id and an undo is a facets.yaml change only); revalidation re-reads
  the plan from the run record (zero model calls).
- `content/synthesis/source_append.py`: the same plan over the reconciliation's
  new facets, plus attach decisions against registered facets.
- `content/synthesis/ai_contracts.py`: the prompt nudge ("one facet per
  testable skill; don't restate a definition as separate facets") with a
  bumped prompt version, only when facet identity is on.
- `content/synthesis/synthesis_gates.py`: a facet reference is known when it is
  registered, proposed, or an alias of either.
- `vault/loader.py`: learning-object recipe components and practice-item
  criterion targets resolve facet aliases at load, as evidence facets already
  do.
- `config/schema.py`, `config/template.py`, `params/parameter_registry.py`:
  `[facet_identity]` (kill switch, group size, shortlist k, lock policy, caps),
  `ai.routing.facet_identity_judge`, code-default `codex_luna`
  (`gpt-6-luna`) and `openrouter_haiku` profiles; defaults fingerprint.
- `ai/routing.py`: the `facet_identity_judge` task.

**Migrations.** One new table, `facet_identity_actions` (WORKFLOW: the
lifecycle and undo snapshot of each applied action; replay never clears it).
Next free number on this branch is 172; Phase 6 (172/173) and router R0 (174)
merge first, so expect a renumber to 175 at merge.

**Algorithm successors and kill switches.** No successor: a merge is a vault
content change resolved through the existing alias and `facet_merges`
machinery, which projections already apply ("a vault-content merge the owner
can undo is the expected shape"). Evidence is re-keyed by the standard
content-recalibration rebuild of the affected learning objects. Kill switch
`facet_identity.enabled = false` restores today's behaviour exactly: no judge,
no shortlist embedding, the old prompts and versions, the lexical gate only.

**Spend caps and routes.** Route `ai.routing.facet_identity_judge`; unset, it
resolves to the code-default `codex_luna` profile (`gpt-6-luna`, low effort)
when the active provider is Codex, else the active provider. Codex is
`estimated_only` on the subscription (no physical-request bound); OpenRouter
Haiku is metered with the full cap set. Per-run caps under
`[facet_identity]`; the dedupe command takes overrides and `--dry-run` (no
client, zero calls, planned calls and estimated cost).

**`judgment_ledger` writes.** Task `same_facet`. One row per facet pair inside
each judged group (`same` when the judge put them in one merge/absorb set,
`different` otherwise; the action, survivor and set rationale in the
rationale JSON), `judge='llm'` with the resolved model and prompt version.
Decider verdicts use `judge='decider'`, which needs router R0's rebuilt CHECK
at merge.

**Tests.** Grouping; partition validation; in-run consolidation and its
normalization (aliases, references, gates); attach/D2 decisions; vault merge
and undo restoring facets.yaml and derived evidence exactly; the kill switch
(byte-identical prompt and no calls); ledger rows; spend caps and dry run; the
fake-judge regression set (12 agreed pairs merged or absorbed, the must-stay-
distinct pairs kept apart) for both the in-run plan and the dedupe command.
