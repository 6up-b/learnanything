# Facet identity at mint time, and a dedupe command

> **Codex review (2026-10-12):** 11 findings, all fixed; see
> `docs/reviews/facet-identity-codex-review.md`. Statements below that the
> fixes changed are marked *(review Fn)*. The lock policy default is now the
> knowledge model's (`merge_locked_facets = false`).

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
  study's 39 facets and labels (`tests/facet_identity_regression.json`; tests/ is flat).

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

## 2. What was built

**The judge** (`content/facet_identity/judge.py`). One structured call per
concept neighbourhood returns a partition: `merge` and `absorb` sets (with a
canonical member and, for absorb, `example` or `precondition`); every facet
not listed is kept distinct. Validation is conservative: an unknown or
repeated label is dropped, a missing canonical falls back to the first member,
and in attach mode a set keeps at most one registered facet, which survives.
Two modes: `consolidate` (peers) and `attach` (new `N*` candidates against
registered `E*` facets, registered pairs never decided). Checkpointed in
`model_work_checkpoints`; a rerun reuses the verdict and its ledger rows and
pays nothing. Spend: `SpendBudget` per run with `[facet_identity]` caps; Codex
routes are `estimated_only` with no physical-request bound, metered routes
keep `single_request()` and the full cap set; an unknown metered price
refuses. A failed call is retried within `max_retries`; a truncated output is
never retried. The Decider path (`DeciderGroupJudge`) asks one typed `choice`
question per pair (up to 128 per request) and partitions with a no-chaining
union (a union is refused when any cross pair was answered `distinct`).

**Grouping** (`grouping.py`). Union-find over same concept, concept-graph
adjacency, the lexical near-duplicate pairs (Jaccard ≥ 0.85) and, when vectors
exist, each facet's top-k by mean-centred cosine. A neighbourhood over
`max_group_size` (40) is split by average-link agglomeration over the vectors,
or by packing whole concepts in graph order. Every facet lands in one group.
On `linear_algebra` the concept graph connects all 39 facets into one group.

**In-run consolidation and attach** (`plan.py`, `source_set_synthesis.py`,
`source_append.py`). After graph structuring (bootstrap) or reconciliation
(append), the plan judges the run's candidates, then the survivors against
registered facets (T5's top-4 nominations when embeddings are on, plus the
registered facets of the candidate's registry concept and lexical
near-duplicates). The plan is stored on the synthesis run
(`actual_usage.facet_identity`); `_normalize` applies it and revalidation
replays it with zero judge calls. A retired candidate is not minted: its id
becomes the survivor's alias, the survivor's payload is the union (merge) or
gains the claim as an example or precondition (absorb), and the proposal's
recipe components, criterion targets and evidence facets keep the retired id
on disk. Analysis lists (identifiability, recipe facets, goal facet ids) see
the survivor. On a registered survivor the update row is growth-only (alias,
plus the absorbed claim), which the append vocabulary gate now verifies.

**Resolution at load** (`vault/loader.py`). Learning-object recipe
components, criterion targets, discrimination profiles, contrast components
and planted errors resolve facet aliases at load, as evidence facets already
did. A vault with no alias references loads exactly as before.

**Actions and undo** (`actions.py`, `db/stores/facet_identity.py`, migration
172). Each merge/absorb set is one row in `facet_identity_actions` with the
facets.yaml entries before and after and any `facet_merges` rows it inserted.
Because references keep their ids, an action changes only facets.yaml (and,
for registered facets, `facet_merges`), and undo restores exactly that, then
re-syncs and re-folds the affected learning objects. *(review F9)* Evidence
resolved at projection time returns; rows graded while the merge stood
(exercised facets, A5 notes, error events) keep the survivor's id. *(review
F4)* A merge commits its intent (`applying`, with its `facet_merges` rows)
before facets.yaml is replaced atomically, an undo records `undoing` with the
owner's verdicts first, and recovery (every merge, undo, dedupe and `doctor
--fix-state`) finishes either. *(review F3)* An undo writes `judge='owner'`
`different` rows; no later dedupe or attach re-merges the pair. Undo refuses (writing
nothing) when the action is already undone, its proposal is not applied yet,
or the survivor's entry changed since; it names the later action to undo
first. Ingest actions are recorded `proposed` and become undoable once their
proposal is applied.

**Dedupe** (`dedupe.py`, `learnloop facets dedupe|actions|undo`). Registered,
non-retired facets (one subject with `--subject`) are grouped by concept
neighbourhood (stored vectors only bound a large group, never link), judged,
and every set is applied through `merge_registered_facets`. `--dry-run`
plans groups, pairs, calls, tokens and cost with no client and no change.

**Prompt nudge.** With facet identity on, bootstrap synthesis gets rule 15
("one facet per testable skill; don't restate a definition as separate
facets; a special case is an example or precondition") under
`mvp-1.2-one-facet-per-testable-skill`, and append reconciliation gets rule 9
under `mvp-0.9-append-one-facet-per-testable-skill`. The shard checkpoint key
now carries the effective prompt version. Off, both requests are byte-for-byte
today's (tested).

**Desktop.** `list_facet_identity_actions` and `undo_facet_identity_action`
(sidecar, Tauri bridge, client). A completed synthesis or append job in the
Ingest activity shows "duplicate facets · N changes" with each merge and an
Undo button; a merge riding on an unapplied proposal says "applies with the
proposal", and a skipped check says why.

**Config.** `[facet_identity]` (kill switch, `max_group_size` 40,
`shortlist_top_k` 4, `attach_top_k` 4, `merge_locked_facets` false *(review F2)*, per-run caps,
owner price override), `ai.routing.facet_identity_judge` (default
`codex_luna` when the active provider is Codex, else the active provider),
code-default `codex_luna` (`gpt-6-luna`, low effort) and `openrouter_haiku`
(`anthropic/claude-haiku-5.5`) profiles. Defaults fingerprints recorded with a
decision note; parameter registry classifies `facet_identity.*` as
operational.

## 3. Decisions and deviations

1. **Group judge, own package.** T1's `learnloop.matching` judges pairs and
   unions them; the spec forbids that for facets, so only the shortlist maths
   and ledger conventions are shared. Reuse points at merge:
   `grouping.centred_unit` is `matching.shortlist.centred_unit`, and
   `judge.partition_from_pairs` can delegate to `matching.union.union_with_refusals`.
2. **References keep their ids; aliases resolve at load.** This makes every
   undo a facets.yaml-plus-`facet_merges` restore, exact for in-run, attach and
   vault merges alike, at the cost of one loader change (alias resolution for
   recipe components and criterion targets). A writer that later round-trips a
   loaded learning object or item persists the survivor's id; undoing a merge
   after such an edit leaves that entity on the survivor.
3. *(Superseded, review F2: the default is now `false`, the knowledge
   model's single lock policy; locked sets are listed as `locked_proposals`.)*
   **Locked facets are merged by default** (`merge_locked_facets = true`).
   On the `linear_algebra` copy 20 of 39 facets are identity-locked
   (independent surface groups, probe episodes) and 10 of the 15 cluster
   members among them, so the knowledge model's strict policy (§3.4: locked
   merge needs restructure-with-history) would refuse almost every agreed
   merge. The owner's option c (apply live, one-tap undo) is honoured: a merge
   re-keys history through `facet_merges` exactly as projections already do,
   the result labels each locked facet with its lock reasons, and undo
   restores it. `merge_locked_facets = false` restores the strict policy.
   Open question 1.
4. **No algorithm successor.** A merge is vault content resolved by existing
   alias and `facet_merges` semantics. *(Corrected, review F1: as first built,
   a criterion or recipe naming both merged facets resolved to `[A, A]`,
   which split and discounted a correct answer's mass, wrote no negative
   evidence for a wrong one and squared recipe readiness. Duplicates that
   alias resolution creates now collapse at load, so a merged item counts
   exactly like one authored with the survivor alone; projection code is
   unchanged.)* Affected learning objects are re-folded by the standard
   content recalibration (one derived-state marker).
5. **Attach on a registered facet is growth-only.** A merge into a registered
   facet is the alias alone; an absorb also appends the claim to its examples
   or preconditions. Claim, repairs, signatures and status never change (§10.2).
6. **Embeddings.** In-run shortlist edges use T5's capped embedding of the
   run's candidates; attach uses T5's top-4 registry nominations. Both need
   embeddings on (default off); without them grouping is by concept,
   concept graph and lexical pairs, and attach by registry concept and
   lexical pairs. Dedupe uses stored vectors only to split a large group.
7. **Ledger volume.** One row per facet pair of each judged group (`same` or
   `different`): 741 rows for the 39-facet group. Candidates are keyed by
   content (`facet_candidate`, `sha:…`) so a rerun asks the same question.
8. **Decider dormant on this branch.** Router R0 (the `decider` profile type,
   `ai.decisions.ChoiceQuestion`, `judge='decider'` in the ledger CHECK) has
   not merged. The adapter, partition and question construction are built and
   tested with a fake; the ledger test skips with that reason until R0's CHECK
   is present.
9. **Prompt and budget, from the live runs.** The partition prompt now names
   absorb patterns (axiom subset, terminology remark, routine proof) and lets
   the judge omit singleton sets; the output budget is 1,200 + 160 tokens per
   facet after Haiku truncated at 3,910.

## 4. Live runs (backup-API copies under `fixtures-local/`)

All on copies of the worktree's tracked `fixtures/linear_algebra`
(`fi-linear_algebra-inspect`, `-dedupe`, `-inrun`, `-baseline`). Dry runs
first; every call within the default caps.

**Codex model check.** The Codex CLI's model list (`~/.codex/models_cache.json`,
fetched 2026-10-12 by client 0.162.1) offers `gpt-6-luna` ("fast and
affordable model for easier tasks"); a minimal two-facet call through
`codex_luna` returned a valid merge in 4 s (14,804 reported tokens).

**Codex usage limit.** After 11 completed calls the subscription answered
"You've hit your usage limit … try again at Oct 18th, 2026 1:00 PM" (7 failed
calls, no output). Codex was not called again; the remaining live runs used
the metered Haiku route.

| Run | Judge | Prompt | Agreed merge pairs found (of 12) | Must-stay-distinct kept apart (of 7) | Agreed non-merge pairs merged |
|---|---|---|---|---|---|
| Dedupe, fresh copy, applied | Codex `gpt-6-luna` (default) | draft | **8** | **7** | 0 |
| Plan only | Codex, low | draft | 7 | 7 | 0 |
| Plan only | Codex, medium | draft | 7 | 7 | 1 |
| Plan only | Codex, low | intermediate | 7 | 7 | 0 |
| Plan only, groups of 12 / 20 (no vectors) | Codex, low | intermediate | 4 / 4 | 7 / 7 | 0 / 1 |
| Plan only | Haiku 5.5 | final | 9 | 7 | 1 |
| **In-run, preserved candidate** | Haiku 5.5 | final | **9** | **7** | 0 |

- The applied Codex dedupe made 5 merges; the misses were the terminology
  note, the axiom subset (two pairs) and the coordinatewise proof method, all
  "near_duplicate" in the study. It also merged the one pair the study's
  judges disagreed on (the zero vector vs the overloaded symbol 0).
- The in-run regression re-ran consolidation over the run that produced the
  duplicates (synthesis run `01KY3Y4DD5ZJXEYK4GMESB51M8`'s preserved
  candidate, registry emptied as at first ingest, attach off): 7 merges, 9 of
  12 pairs, no false merge. A full re-synthesis was not run: the copy's subject
  is identity-locked (bootstrap refuses), and a new synthesis mints different
  facets, so the study's pairs could not be scored on it.
- Smaller groups (split by concept without vectors) separate duplicates; the
  default keeps the whole 39-facet neighbourhood.
- Undo on real data: undoing all five applied merges restored facets.yaml
  byte-for-byte in content and order, removed all `facet_merges` rows, and left
  `facet_recall_state` and `facet_capability_evidence` identical to a baseline
  copy given the same content recalibration of the same 10 learning objects.
  (Against the fixture's stored rows they differ for unrelated facets: the
  stored projection predates current replay code, so any re-fold moves them.)

**Calls and cost.**

| Route | Calls | Tokens (reported) | Cost |
|---|---|---|---|
| Codex `gpt-6-luna` (subscription) | 11 completed, 7 failed (usage limit; one diagnostic call outside the judge has no receipt) | 199,551 input, 9,696 output | $0 metered, `estimated_only` |
| OpenRouter `anthropic/claude-haiku-5.5` | 11 (9 truncated at the old output budget) | 119,959 input, 42,406 output | **$0.0332** (OpenRouter-reported) |

## 5. Gate

Run on `bc56efba` (clean tree; the commit after it adds only this section).

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **12 contracts kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **7,672 passed, 1 skipped**, 46 warnings (existing: 32 from the mobile host tests, fork and sqlite datetime deprecations), 244 s |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **83 passed**, 7,590 deselected, 1 warning, 85 s |
| Frontend (`npm install`, `npm run typecheck`, `npm test`) | typecheck clean; **22 files, 97 tests passed** |
| DB/config references (`db_generate_reference.py`, `db_validate_reference.py`) | schema head 172, 285 table notes, 640 config leaves in 35 sections, **0 errors**; docs-vault validator passed (1,053 notes) |

The one skip is `test_the_decider_answers_per_pair_choices_and_partitions`:
`judge='decider'` needs router R0's ledger CHECK (decision 8). New tests:
`test_facet_identity.py` (17), `test_facet_identity_actions.py` (6),
`test_facet_identity_ingest.py` (8), `FacetIdentityPanel.test.tsx` (6).
`cargo check` was not run: the Rust change is two `sidecar_passthrough!`
lines, which `test_desktop_rpc_contract.py` checks across all four layers.

## 6. Files touched

- New: `src/learnloop/content/facet_identity/{__init__,views,grouping,judge,plan,actions,dedupe}.py`,
  `src/learnloop/db/stores/facet_identity.py`, `src/learnloop/cli/facets.py`,
  `src/learnloop_sidecar/handlers/facet_identity.py`,
  `migrations/172_facet_identity_actions.sql`,
  `apps/learnloop-tauri/src/components/FacetIdentityPanel.tsx` (+ test),
  `tests/test_facet_identity{,_actions,_ingest}.py`, `tests/facet_identity_fakes.py`,
  `tests/facet_identity_regression.json` (the study's 39 facets, concepts,
  graph and labels), this file.
- Changed: `content/synthesis/{source_set_synthesis,source_append,ai_contracts,synthesis_gates}.py`,
  `vault/loader.py`, `config/{schema,template,loader}.py`, `ai/routing.py`,
  `params/parameter_registry.py`, `db/table_roles.py`, `cli/__init__.py`,
  `learnloop_sidecar/handlers/__init__.py`, the Tauri bridge (`commands.rs`,
  `main.rs`), `api/{client,dto}.ts`, `components/IngestActivity.tsx`,
  `tests/test_architecture.py` (SQL owner), `tests/test_graph_nomination_ingest.py`
  (T5's byte-identity tests now pin facet identity off), the head-fixture
  paths, `tests/cli_help_snapshot.json`, the reference generator/validator
  (head 172, section description) and the regenerated reference notes.
- Fixtures: `fixtures/migration_head_171` upgraded through 172 on a
  backup-API copy (`wal_checkpoint(TRUNCATE)`, `journal_mode=DELETE`,
  integrity ok, foreign keys clean) and renamed `migration_head_172`.
  `fixtures/linear_algebra`, `probability` and `arxiv_v2` untouched.

## 7. Migrations

`172_facet_identity_actions.sql`: one WORKFLOW table, `facet_identity_actions`.
Phase 6 (172/173) and router R0 (174) merge first, so renumber it to 175 and
rename the head fixture (`migration_head_175`, README, five test/script
paths, both `SCHEMA_HEAD` constants), then regenerate the references.

## 8. Owner-run commands

The default judge is Codex `gpt-6-luna`, out until **2026-10-18 13:00** (usage
limit). To run before then, set the metered Haiku route in the vault's
`learnloop.toml` (about $0.003–0.005 per 39-facet group; OPENROUTER_API_KEY):

```toml
[ai.routing]
facet_identity_judge = "openrouter_haiku"
```

Dedupe each vault, dry run first (no call, no change; shows groups, pairs,
calls, estimated cost and which facets are identity-locked):

```bash
uv run learnloop facets dedupe --vault fixtures/linear_algebra --dry-run --json
uv run learnloop facets dedupe --vault fixtures/linear_algebra --json
uv run learnloop facets dedupe --vault fixtures/probability --dry-run --json
uv run learnloop facets dedupe --vault fixtures/probability --json
uv run learnloop facets dedupe --vault fixtures/arxiv_v2 --dry-run --json
uv run learnloop facets dedupe --vault fixtures/arxiv_v2 --json
```

`probability` had a malformed practice item when T5 copied it; dedupe refuses
a vault with validation issues, so run `learnloop doctor --vault
fixtures/probability` first. A large vault splits neighbourhoods over 40
facets; with embeddings on (and the T5 backfill complete) the split uses the
stored vectors, otherwise whole concepts.

What to check after each run:

- `uv run learnloop facets actions --vault <vault> --json`: every merge or
  absorb with both claims, the rationale and whether a facet was locked. Undo
  any you disagree with: `uv run learnloop facets undo <action-id> --vault <vault>`
  (undo the newest first when two touch the same facet; the command names it).
- `uv run learnloop doctor --vault <vault>`: no new `unregistered` errors.
- The first dedupe re-folds the affected learning objects under current
  replay code (one recalibration marker), so beliefs of nearby facets can move
  even where nothing merged; that is the stored projection catching up.
- With embeddings on, rerun `uv run learnloop embeddings backfill --vault <vault>`:
  survivors' definitions changed, so T5's index is incomplete until then
  (nominations fall back to lexical, labelled).
- New ingests list their merges in the Ingest activity with an Undo button.

Kill switch: `[facet_identity] enabled = false` (no judge, no new merges,
stored plans are not replayed, today's gate; merges already in a vault keep
resolving at load). Lock policy *(review F2)*: the default refuses locked
facets and lists those sets under `locked_proposals`; on the `linear_algebra`
copy all 5 sets the judge found were locked (every one by the `probe` arm),
so the default applies nothing there. The owner's override is
`[facet_identity] merge_locked_facets = true`; rerunning dedupe then applies
the listed sets from the reused verdict (no new call).

## 9. Merge notes

- **Slice 2 T1** (`learnloop.matching`, not merged): reuse
  `matching.shortlist.centred_unit` in `grouping.py` and
  `matching.union.union_with_refusals` in `judge.partition_from_pairs`; T1's
  `judgment_work_claims` could also guard the group judge across processes.
- **Router R0**: the Decider path activates through `routing.is_decider_profile`
  and `ai.decisions.ChoiceQuestion` (both looked up at run time), but R0's
  `route_profile_mismatch` refuses a decider profile on any non-decider task,
  so add `facet_identity_judge` to the routes that accept one; R0's ledger
  CHECK already accepts `judge='decider'`, which un-skips the ledger test.
- **Defaults fingerprints** must be recomputed after R0 and Phase 6 (both
  also add config).

## 10. Open questions

1. **Locked facets.** The default is now the knowledge model's strict lock
   (`merge_locked_facets = false`, review F2), which on `linear_algebra`
   applies none of the 5 sets (all probe-locked). Override it (option c on
   locked facets too), or keep it until restructure-with-history exists?
2. **Recall of a cheap judge.** Live runs found 8–9 of the 12 agreed pairs,
   never a must-stay-distinct pair. The misses are "bundled extras" (a
   terminology note, the axiom subset, the routine proof). Accept, rerun
   dedupe (a second pass sees the consolidated facets), raise Codex effort, or
   use a stronger model for the one-off dedupe?
3. **Default route while Codex is limited.** Keep `codex_luna` (an ingest
   during an outage keeps its candidates and says "duplicate check failed"),
   or fall back to `openrouter_haiku` automatically?
4. **Ledger volume.** One row per pair per judged group (741 for 39 facets).
   Keep, or record only `same` pairs plus the shortlisted `different` ones?
5. **Attach without embeddings.** With embeddings off, attach compares a
   candidate with the registered facets of its own registry concept and
   lexical near-duplicates. Keep, or attach only on T5 nominations?
