# Slice 2 T4 — contamination detectors (shadow flags)

Spec: `docs/specs/spec_embedding_consumers_v1.md` §7, with §1 (R1–R6), §4 and
§13 (T4 report). Handoff: `docs/specs/implementation_handoffs.md`, "Slice 2 T4,
T5, T7, T8". Branch `slice-2/t4` from `main` at `974c5647`. The handoff's
prerequisite that the owner has reviewed the previous track's report is waived
(owner, 2026-10-12; `implementation_goal.md` §1a): tracks are built in parallel
and their report gates are post-hoc.

## Plan (written before coding)

**Shape.** T4 adds no serving-path code and no live behaviour. The three
lexical detectors stay exactly as they are and remain the floor:

| Detector | Live floor (unchanged) | Shadow addition (owner-run report) |
|---|---|---|
| Held-out exam leakage | `practice_leakage.check_leakage`: 6-word shingles + distinctive numerics, blocks generated items at generation time | kNN of each generated item's stored `item/stem` and `item/expected_answer` vectors over stored held-out span vectors (top-k, no cosine cutoff) shortlists pairs; an LLM judge decides each `leak` |
| Tutor answer leak | `tutor_qa.answer_leak_overlap` (substring / token recall), debits `reveal_events` | rank of the bound item's expected answer among all expected answers for the stored tutor-answer vector (top-k) shortlists; math answers also go through a symbolic check; an LLM judge (or the symbolic verifier) decides each `reveal` |
| Reader reveal | `reader_dialogue` bigram overlap ≥ 0.5 / hash / fingerprint, burns the reserve | kNN of the stored reader-answer vector over stored live-reserve vectors (top-k) shortlists; symbolic check on the reserve's answer; the judge decides; a flag **proposes** a reserve burn and never executes it |

The shadow flags are computed by an owner-run command, not on any serving path,
so no serving path makes an embedding call. Every subject or index without a
complete set of stored vectors degrades to the lexical floor (plus the symbolic
check) and the report says so.

**Files to add.**
- `src/learnloop/ops/contamination/` — `recipes.py` (T4 record kinds and their
  text recipes), `symbolic.py` (safe symbolic answer check), `detectors.py`
  (candidate building from the floor, the symbolic check and stored vectors),
  `judge.py` (the `leak` / `reveal` judge under spend caps), `report.py` (the
  §13 report: flag rates, floor/shadow agreement, proposals, audited samples).
- `src/learnloop/cli/contamination.py` — `learnloop contamination embed` and
  `learnloop contamination report`, both with `--dry-run`.
- `tests/test_contamination_*.py`.

**Files to change (additive).**
- `content/authoring/practice_leakage.py`: public `held_out_spans` (span ids +
  text; the existing text list delegates to it) and `inventory_for_texts`.
- `reader/reader_dialogue.py`: public `surface_statement_text` and
  `lexical_reserve_reveal` (the existing private detector delegates to it, so
  the floor has one definition).
- `diagnosis/offline_review/probes.py`: public `answers_equal` /
  `answers_differ` wrappers over the existing safe exact-arithmetic + SymPy
  comparison (model text reaches SymPy only through `safe_math_text`).
- `vault/embedding_recipes.py`, `ops/embedding_backfill.py`: an optional
  `registry` argument so the Phase 1 backfill (spend caps, receipts, lock,
  idempotency) embeds T4's record kinds without adding them to the default
  backfill.
- `ai/routing.py`, `config/schema.py`, `config/template.py` (defaults
  fingerprint): the `contamination_judge` route.
- `cli/__init__.py`, `tests/cli_help_snapshot.json`.

**Migrations.** None. T4 adds no table: verdicts go to `judgment_ledger`
(tasks `leak` and `reveal`, as §3.1 reserves), vectors to `embedding_vectors`,
and proposals are computed by the report from ledger verdicts and live state.

**Algorithm successors and kill switches.** None. Nothing served changes and
nothing persisted changes meaning; the lexical floor keeps every live decision.
Proposals (`burn_reserve`, `reveal_debit`, `review_item`) are listed in the
report and never executed. A future live switch would be a successor with a
kill switch, decided on this report (R6).

**Spend caps and model routes.**
- `contamination embed`: the Phase 1 backfill on the `embedding` route
  (`ai.routing.embedding`, never falls back), both embedding switches required,
  `SpendCaps` with `--dry-run`.
- `contamination report`: the judge runs on `ai.routing.contamination_judge`
  (unset → the active provider; receipts record the resolved model). Metered
  routes keep the full cap set and the physical-request bound; a Codex route
  runs on the subscription with `estimated_only` cost (Slice A §5 rule 6).
  `--dry-run` prints the estimate with no client, lock or data change.
  `--no-judge` gives a zero-cost report from the floor, the symbolic check and
  stored vectors.

**`judgment_ledger` writes.**
- `leak` — left `practice_item`, right `source_span` (`extraction/span`);
  judge `llm`; verdict `leak` | `clean` | `unsure`.
- `reveal` — left `question_event`, right `practice_item` (tutor answer) or
  `activity_surface` (reader); judge `llm` with verdict `reveal` | `clean` |
  `unsure`, or judge `verifier` (symbolic match on a distinctive math answer,
  verdict `reveal`).
- Ids are content-addressed (`ctj_` / `ctv_` + input hash), so reruns never pay
  twice. Authority when verdicts differ: owner > verifier > llm.

**Tests.** Recipes declare canonical text and never read the learner's
question; the symbolic check matches equivalent forms and never parses unsafe
text; detectors shortlist by rank, not score; a judge stubbed to `clean` yields
no flag (R1); missing vectors degrade to the floor; proposals never change
reservations, exposures or `reveal_events`; dry run changes nothing and builds
no client; caps admit before any call; reruns are cached; the report makes no
embedding call; owner > verifier > llm precedence; the CLI.

## What was built

**`learnloop contamination embed`** (`cli/contamination.py`). It runs the Phase 1
backfill over T4's recipe registry (`ops/contamination/recipes.py`), using the
same switches, caps, receipts, lock and content-hash idempotency. The default
`learnloop embeddings backfill` is unchanged and never embeds these kinds.

| Recipe | Text it embeds (R3) |
|---|---|
| `item/stem` | The Phase 1 recipe itself, shared so one command covers the report |
| `item/expected_answer` | The canonical expected answer (sorted JSON when structured); not retired items |
| `question_event/answer` | The tutor's own `answer_md`, for answered turns bound to an item or asked in the reader. Never the learner's question |
| `surface/statement` | The reserved-surface text the reader floor compares against; only live assessment reserves |
| `exam_span/text` | The block text of each held-out exam span, keyed `extraction/span` |

**`learnloop contamination report`** (`ops/contamination/report.py`). It scans
persisted history and makes no embedding call and no serving-path change.

- **Shortlists** (`detectors.py`). Each detector starts from the live floor,
  unchanged, and adds:
  - **exam_leakage** — generated items only (origin `codex_proposal` or
    `canonical_extract`) against every held-out span. The floor's
    shingle/numeric findings are attributed per span, plus the top-k spans by
    the stored stem and expected-answer vectors.
  - **tutor_answer_leak** — every answered item-bound turn against its item's
    expected answer. The floor plus the symbolic check, plus a shortlist when
    the item's own expected answer ranks in the top k among all expected
    answers for the stored answer vector. The floor counts as caught when the
    live path alone protects the next attempt: the 0.8 `leak_suspected` flag,
    or a reveal-ledger debit at or above `AUTO_PRIME_REVEAL_THRESHOLD`
    (0.35). See deviation 2.
  - **reader_reveal** — every reader answer against every live assessment
    reserve. The floor's hash/fingerprint/bigram rule (now one public
    function the live burn path also uses), the symbolic check on the
    reserve's answer, plus the top-k reserves by the stored answer vector.
- **Rank only** (R4). No cosine cutoff exists anywhere. Scores are reported,
  with the min/median/max for decided flags and clean pairs per detector, as
  input for the benchmark-set cutoff that a future live switch would need.
- **Missing vectors degrade.** An index without every current vector, or a
  subject without its vector, falls back to the floor and the symbolic check.
  The report names the index status, the missing count, and the subjects with
  and without vectors.
- **Symbolic check** (`symbolic.py`). Math runs in the answer are compared with
  the expected answer by the offline review's comparison (exact text, exact
  arithmetic, then SymPy). That comparison is exposed as public
  `answers_equal` / `answers_differ`, and model text reaches SymPy only through
  `safe_math_text`. A rounded decimal within its stated precision counts. A
  match decides (`judge='verifier'`) only when both sides are distinctive: a
  fraction, three or more significant digits, a function call, or a symbolic
  expression. Otherwise it only shortlists.
- **Who decides:** owner, then verifier, then the LLM judge (`judge.py`,
  route `ai.routing.contamination_judge`). The judge gets one isolated,
  bounded structured call per pair. It sees only the two texts: never the
  floor, symbolic or embedding signals, the learner's question, or anything
  about the learner.
  - Verdicts append to `judgment_ledger`: task `leak` (practice_item ×
    source_span) or `reveal` (question_event × practice_item or
    activity_surface).
  - Ids are content-addressed (`ctj_`/`ctv_`), so reruns never pay twice, and
    `--judge-revision` forces a re-judge.
  - The shortlist signals ride in the rationale JSON, for evaluation only.
- **Report contents** (§13, "flag rates with audited samples"). Per detector:
  - subjects and targets;
  - floor flags;
  - symbolic counts;
  - shortlist by reason;
  - judge verdicts by model;
  - decisions by judge;
  - flag rate (`null` when nothing could be measured);
  - floor/shadow agreement (`floor_and_shadow`, `floor_only`, `shadow_only`,
    `floor_undecided`, `unsure`);
  - embedding score summaries;
  - proposals;
  - deterministic samples per agreement category, with ids, signals, the
    decision and its rationale, and 240-character excerpts for the owner's
    audit.
- **Proposals are never executed** (`proposals_executed: 0`):
  - `review_item` (exam);
  - `reveal_debit` (tutor; only when the floor missed and the next attempt
    wasn't already recorded as primed; carries the live debit and the next
    attempt);
  - `burn_reserve` (reader; carries `asked_at` and `reserved_at`).

  Tests assert that `reveal_events`, reservations, exposures and item files are
  untouched.
- **Spend.**
  - `SpendCaps` admits the whole plan before any call.
  - `--dry-run` builds no client, takes no lock, writes nothing and does not
    migrate. It reads an unmigrated copy through `Repository.attach`.
  - `--no-judge` gives a free report from the floor, the symbolic check and
    stored vectors.
  - Metered routes keep the physical-request bound and fail closed on an
    unknown price. A Codex route runs on the subscription with
    `estimated_only` receipts (owner_kind `contamination_report`).
  - A per-vault lock stops two paid runs.

**Shared-code changes.** All are additive. Each live path delegates to the new
public function with identical behaviour.

| Module | Change |
|---|---|
| `practice_leakage` | `HeldOutSpan`, `held_out_spans`, `inventory_for_texts` |
| `reader_dialogue` | `surface_statement_text`, `lexical_reserve_reveal` |
| `offline_review/probes` | `answers_equal`, `answers_differ` |
| `vault/embedding_recipes`, `ops/embedding_backfill` | Optional `registry` |
| `ai/routing`, `config/schema` | The `contamination_judge` task and operations |
| `config/template` | The `mvp-0.9` defaults fingerprint, re-pinned with a comment, for the new unset route |

## Deviations and decisions

1. **No serving-path code at all.** A fresh tutor reply, reader answer or
   generated payload has no stored vector, so a serving-path detector that
   makes no embedding call would always fall back to the floor. The shadow
   flags are therefore computed by the owner-run report over the same
   persisted history, so no serving path ever embeds.
2. **Tutor floor definition.** Spec §7 describes the floor as "token recall ≥
   0.8". Live, a tutor answer also debits the reveal ledger by its overlap,
   and a debit of 0.35 or more alone primes the next attempt. The real run
   (below) showed that both judge-confirmed reveals sat at about 0.56. Counting
   only the 0.8 flag would have reported them as missed when the live path had
   already protected the cold evidence. The report counts either as caught,
   records `leak_suspected` and `live_reveal_amount` separately, and names the
   rule in the manifest (`tutor_floor_rule`). A turn from before the reveal
   ledger (migration 154, `leak_overlap` NULL) was never debited, so its live
   floor is the 0.8 flag alone. Today's lexical rule still shortlists it for
   the judge.
3. **Exam leakage scans generated items only** (`codex_proposal`,
   `canonical_extract`), per §7's "generated practice". Hand-authored and
   imported items are out of scope.
4. **`held_out_spans` deduplicates** a span reachable through two members.
   `HeldOutInventory.span_count` (informational only) can therefore be lower
   than before for such vaults. The fingerprint sets are unchanged.
5. **No migration.** §12 lists no T4 table. Verdicts are ledger rows, and
   proposals are computed from verdicts and live state, so there is nothing to
   renumber at merge.
6. **No owner-verdict command.** The report honours owner rows (owner > verifier
   > llm, tested), but recording one is left to a follow-up (open question 2).
7. **No Settings UI route.** `contamination_judge` is configured in
   `learnloop.toml`, and the sidecar `_ROUTING_TASKS` list is unchanged.
8. **Module catalog not regenerated.** `module_validate.py` already reported 74
   uncovered modules on `main`, including Phase 1's. The DB/config references
   were regenerated and validate clean.

## Manual runs (fixtures-local backup-API copies only)

All copies were made with `learnloop.db.copies.copy_tree_with_databases` from
this worktree's tracked fixtures. Nothing touched `fixtures/linear_algebra`,
`fixtures/probability` or `fixtures/arxiv_v2`.

1. **Dry run on an unmigrated copy** (`t4-linear_algebra`, schema 155): status
   `dry_run`, database sha256 unchanged, no `.learnloop` lock directory.
2. **Fakes on two copies** (`t4-fake-linear_algebra`, `t4-fake-probability`):
   a bag-of-words hash embedder under a fake model id (64 dims, so no fake
   vector sits beside a real model's) and a fake word-overlap judge. The
   script is in the session scratchpad.

   | Copy | Records embedded | Judge calls (dry → run) | Tutor answers | Shortlisted | Decided | Rerun |
   |---|---|---|---|---|---|---|
   | linear_algebra | 139 | 5 → 5 | 10 | 5 | 2 clean, 3 unsure | 5 cached, 0 calls |
   | probability | 162 | 3 → 3 | 5 | 3 | 1 clean, 2 unsure | 3 cached, 0 calls |

   In both copies, exam leakage and reader reveal reported `no_targets`: the
   fixtures have no exam-role sources and no live assessment reserves.
3. **Real interfaces** (`t4-real-linear_algebra`; the copy's `learnloop.toml`
   gained `routing.embedding`, the `openrouter_embedding` profile and
   `[embedding]` with both switches on). Dry runs came first each time.
   - **`contamination embed`**: dry run planned 139 records in 5 calls, 61,421
     tokens by the byte bound, $0.00061. The real run made 5 calls on
     `qwen/qwen3-embedding-8b`, resolved `Qwen/Qwen3-Embedding-8B`: 11,394
     input tokens reported, **$0.000114** reported by OpenRouter, all 139
     embedded.
   - **`contamination report`**: the dry run planned 9 calls on `codex`
     (`gpt-5.6-sol`, subscription). The real runs made **10 Codex calls** (9,
     then 1 more after the tutor-floor change shortlisted one floor-only
     pair): 105,268 input and 947 output tokens reported, cost
     `estimated_only` (subscription), about 54 s for the first 9.
   - **Result on this copy:**
     - 10 tutor answers, all with vectors;
     - 4 caught by the floor;
     - 10 pairs shortlisted (9 by rank, 4 by the floor);
     - the judge found 2 reveals and 8 clean;
     - agreement: `floor_and_shadow` 2, `floor_only` 2 (the floor over-primes),
       `shadow_only` 0;
     - no proposals.

     So on this small copy the floor missed no paraphrased reveal, and the
     rank shortlist is near-exhaustive (9 of 10), as a recall-first rule should
     be at this size.

Total paid spend this stage: **$0.000114 metered**, plus 10 subscription judge
calls.

## Gate

_(pass counts below)_

## Files touched

- **Added:**
  - `src/learnloop/ops/contamination/{__init__,recipes,symbolic,detectors,judge,report}.py`;
  - `src/learnloop/cli/contamination.py`;
  - `tests/test_contamination_report.py` (27 tests);
  - `tests/test_contamination_symbolic.py` (20 tests);
  - this file.
- **Changed:**
  - `src/learnloop/content/authoring/practice_leakage.py`;
  - `src/learnloop/reader/reader_dialogue.py`;
  - `src/learnloop/diagnosis/offline_review/probes.py`;
  - `src/learnloop/vault/embedding_recipes.py`;
  - `src/learnloop/ops/embedding_backfill.py`;
  - `src/learnloop/ai/routing.py`;
  - `src/learnloop/config/schema.py`;
  - `src/learnloop/config/template.py`;
  - `src/learnloop/cli/__init__.py`;
  - `tests/cli_help_snapshot.json`;
  - the regenerated `docs/learnloop-architecture-vault/Reference/` notes
    (config field catalog, plus source stamps and line anchors), with the
    hand-written leaf counts 545 → 546 in `Configuration.md` and
    `Database.md`.

## Migrations

None. Schema head stays 168. `judgment_ledger` gains the tasks `leak` and
`reveal`, as §3.1 reserved them.

## Owner-run commands (live vault; never run by this stage)

The owner's vault configs predate Phase 1. Before the embed step, add to the
vault's `learnloop.toml`:
- `embedding = "openrouter_embedding"` under `[ai.routing]`;
- the `[ai.providers.openrouter_embedding]` profile (`type =
  "openai_embedding"`, `base_url = "https://openrouter.ai/api/v1"`,
  `api_key_env = "OPENROUTER_API_KEY"`);
- `[embedding]` with `enabled = true` and `backfill_enabled = true`.

Optionally set `contamination_judge` under `[ai.routing]`; unset, it uses the
active provider (Codex, subscription).

```bash
# 1. Embed what the report compares (OpenRouter, metered; fractions of a cent).
uv run learnloop contamination embed --vault <vault> --dry-run --json
uv run learnloop contamination embed --vault <vault> --json

# 2. The report: dry run first (no client, lock or writes), then for real.
uv run learnloop contamination report --vault <vault> --dry-run --json
uv run learnloop contamination report --vault <vault> --json > contamination-report.json
#    Free variant (floor + symbolic + stored vectors; writes verifier verdicts only):
#    uv run learnloop contamination report --vault <vault> --no-judge --json
#    Narrow or cap a large run: --detector tutor_answer_leak --top-k 1 --max-calls N
```

Rerunning step 2 is free for pairs already judged. Rerun step 1 first after new
tutor or reader activity. Review the report before any live switch (R6). A live
switch, such as executing `burn_reserve` proposals or debiting reveals, would
be a successor with a kill switch, decided on this report, and is not built
here.

## Open questions

1. **Live switch criteria.** The report gives flag rates, `shadow_only`
   counts, judge-confirmed score ranges and samples. Which `shadow_only` rate
   would justify executing `burn_reserve` / `reveal_debit` proposals live, and
   should it wait for an owner-audited sample?
2. **Owner verdicts.** Should a `learnloop contamination verdict <judgment-id>
   reveal|clean` command record owner audits (`judge='owner'`, superseding)?
   The report already ranks them first.
3. **Floor over-priming.** The real copy showed 2 of 4 floor catches judged
   clean: overlap-based debits prime attempts the judge would not. Is that
   worth a later report, or is over-priming the accepted cost of a generous
   floor?
4. **Exam scope.** Should hand-authored and imported items also be scanned for
   held-out leakage? Today only generated items are.
