# Slice A Phase 3 — PF-a

## Mapping investigation (before implementation)

P12 fits the existing substrate. No additional owner decision is needed.

1. **Scheduling authority.** `substrate/compat/substrate_cutover.py`
   `purpose_adapters_live` enables the purpose adapters for `mvp-0.8` and its
   successors. The tracked configurations of `linear_algebra`, `probability`,
   and `arxiv_v2` all specify `mvp-0.8` (read only; no working database opened).
   `activity_card_state`, keyed by card lineage, is authoritative; its
   `projection_head_json.reviews` retains the authoritative review stream.
   `practice_item_state` is the legacy compatibility projection. Older vaults
   retain their existing legacy path. PF-a changes neither path.
2. **Additive regrouping.** `resolve_legacy_item` currently deterministically
   creates a purpose/item-specific family, card and surface. Replacing its
   family seed would also replace the card, so that is not a safe grouping
   operation. Keep those genesis identities and append explicit practice-card
   membership events pointing to the shared purpose-`practice` activity family.
   An undo appends a removal; no existing RAW_LEDGER row, administration,
   lineage, reservation, exposure or scheduling state is rewritten. Diagnostic
   and assessment adapters retain their separate families and shared surface
   collision protection.
3. **Authored content.** Add `ActivityFamily` vault content keyed by the
   `activity_families.id`, loaded and written alongside the other authored
   entities. Family content has its own hash/version; immutable
   `activity_family_versions.family_spec_json` records the corresponding
   authored revision. SQLite remains the identity/audit store, not a competing
   authoring authority. There is no parallel practice-family identity table.

Migration 075 already separates lineage from immutable card versions; 077
provides namespaced fingerprint membership and 078 durable mint jobs. Neither
needs to be replaced. Each item keeps its own card.

## Implementation plan

- Extend vault models/loading/writing with `ActivityFamily` and optional item
  `family_id` / `variant_relation`. Omit absent fields from every serialization;
  leave the scheduling hash whitelist unchanged.
- Add append-only membership storage, reversible family application and undo.
  `family_proposals` is WORKFLOW only; all pair verdicts and accept/reject/undo
  decisions append to the Phase 1 `judgment_ledger`.
- Implement `learnloop families propose` with two distinct, versioned judge
  prompts per within-LO pair, unanimous complete-link agreement (no chaining),
  and no review queue. Use Phase 1 `SpendBudget`, bounded requests/retries,
  estimates, `--dry-run`, content-addressed resume, explicit model routing and
  receipts. For large LOs, embeddings block candidates but never decide identity.
- Add a deterministic, cold-only `family_memory_state` DERIVED projection and
  exactly one rebuild owner. P11 default: `same_target` and `isomorph` count;
  `near` and `far` remain transfer probes. P8 default: backfill existing items.
- Add offline prequential memory-per-item/family/LO evaluation and `idea_hier`
  through `learnloop eval`, with counts/exclusions, intervals, version manifest,
  model splits, current-fit/default FSRS weights and distance-discount arms.
  Phase 2 is parallel: isolate the reusable evaluation seam and document any
  integration needed rather than depending on unmerged code.
- Take the next free migration number at completion; classify all new tables,
  upgrade the migration-head fixture through the backup API and regenerate
  schema references. Rebase/renumber/regenerate again before merge if Phase 2
  lands first.
- Test serialization/hash and no-family rebuild compatibility, card preservation,
  ledger completeness, disagreement/no-chaining, spend/resume/cancellation,
  purpose isolation, deterministic cold-only rebuild and offline evaluation.
  Exercise dry-run, fake-judge acceptance and undo on `fixtures-local/` copies.
  Run import contracts, the full suite and the durability lane.

**Stop line:** no Phase 3b, live family retention key, algorithm successor,
generator/publication work, grading changes, or active predictor change. No
merge or push. No paid requests or owner-vault writes during implementation.

## What was built

- `ActivityFamily` authored vault files and separate hashes/revisions, optional
  item membership fields, append-only practice-card memberships and reversible
  application. Practice, diagnostic and assessment card/surface identities are
  preserved. Family metadata does not enter the scheduling hash.
- `families propose` judges every within-LO pair twice with different prompts;
  only complete unanimous components are applied. A contradictory triangle is
  rejected as ambiguous, rather than arbitrarily assigning its shared member.
  Large LOs use existing complete/current stem vectors for top-k blocking only.
  Missing vectors require the separate Phase 1 backfill, never an implicit paid
  job. Agreement includes the declared same-target/isomorph relation.
- The judgment ledger retains paid verdicts as resumable checkpoints, rejection
  decisions and immutable acceptance/undo provenance. Workflow state can be
  recovered; it is not the verdict authority. Undo is sticky for the same
  decision, and unrelated owner edits are retained.
- Explicit candidate/pair/call/retry/token/dollar caps, cancellation between
  requests, conservative input-plus-output token estimates, and bounded provider
  execution. Receipts retain caps, prompt/input pins and resolved model IDs.
- A shadow-only, deterministic `family_memory_state` replayer and one shared
  offline harness with 12 memory arms (three keys × default/current weights ×
  distance on/off) and `idea_hier`. JSON and Markdown reports include counts,
  exclusions, bootstrap intervals, versions and model/revision/origin splits.
  All predictors see each prediction input before any sees its outcome.
- Existing `learnloop eval --vault ...` calibration behavior is retained as the
  group's default; `learnloop eval families` adds the PF replay.
- Migration 167, role/replayer registration, migration-head fixture and database
  references. Final fetch of the primary checkout's main (`be33cdd0`, including
  the parallel daily-loop fixes) still ends at migration 166; Phase 2 has not
  landed there. Thus 167 is next free at completion. This branch was created
  from `1a0f7a0a`; rebase onto the integration base and check the number again
  before merge.

## Decisions, deviations and limitations

1. **No Phase 3b.** No algorithm successor or live family retention key was
   introduced. The default-fingerprint update records only two offline command
   knobs (`max_exhaustive_items=40`, `blocking_top_k=20`), not changed serving.
2. **Phase 2 integration is explicit.** Phase 2 was not merged while this phase
   was built. The pure offline predictor/row seam is not an activatable
   `LearnerPredictor`. Merge its canonical outcome adapter and incumbent arms
   into this single `learnloop eval` harness before any activation decision;
   do not maintain two evaluation implementations. See
   `pf-a-evaluation-integration.md` for the interface and assumptions.
3. **Historical revisions fail closed.** Default reports exclude attempts
   without a verified graded snapshot. `--legacy-fallback current_content`
   explicitly permits reconstructed-current rows and labels them separately.
   Regraded attempts are excluded from prospective evaluation instead of
   backdating their later corrected labels. Legacy calibrated ability mass is
   not invented; graded cold memory rows can still support the FSRS arms.
4. **No invented skeleton distances.** PF-b owns skeletons. The distance arm
   exists but currently has no measured-distance coverage, which reports disclose.
   Authored transfer-distance labels are not substituted for measured distance.
   The current fitted FSRS weights may have seen this log; their results are
   descriptive. Fixed-default-weight arms are the strict fixed-weight comparison.
5. **Spend safety requires a bounded transport.** Unset `pf_*` routes retain
   active-provider fallback. The chosen judge route is pinned during execution:
   an unavailable model fails rather than silently using a different model than
   the dry-run. `openai_chat` and `openrouter` support bounded attempts. Codex's
   opaque app-server turns do not expose a physical-request bound, so this command
   refuses that transport before startup/reserving spend. Configure a bounded
   family-judge route; ordinary Codex commands are unchanged.
6. **Resume is a saved experiment, not fresh alias resolution.** Checkpoints
   use requested provider/model/settings, prompts, authored inputs and
   `--judge-revision` (default `1`). A mutable model alias may later point
   elsewhere; rerunning deliberately reuses the old paid verdict, labelled with
   its original resolved model. Change `--judge-revision` when intentionally
   repeating the experiment after retargeting an alias. Reports never relabel
   cached judgments with the currently requested model.
7. **No artificial owner review.** Two-pass auto-accept and one-step CLI undo
   replace admission/review queues. Existing `codex_proposal` provenance denotes
   AI-authored family wording (the vocabulary predates provider-neutral routing);
   the immutable decision separately pins the actual judges and models.
8. Slice 2 §13 gates concerning T1 calibrators/recurrence, PF-b publication,
   sandboxing and PF-c blind grading are not implemented in PF-a. Existing
   behavior is preserved; this phase tests its family/hash/ledger/replay gates.
9. Shadow replay reuses the existing grading, reveal-window and FSRS authorities.
   Seven narrow import-contract exemptions document these same dependencies
   already used by canonical projection; no broad contract was disabled. The
   startup projection's old lock import now uses the dependency-neutral lock,
   removing one pre-existing deferred cross-domain edge.

## Verification

Final integrated validation passed. No live provider calls were made.

| Check | Result |
|---|---|
| `uv run pytest -n auto` | **6,228 passed**, 14 existing-style deprecation warnings; 223.59 s, 32 workers |
| `uv run pytest -m durability` | **63 passed**, 6,165 deselected; 28.90 s |
| Four PF modules with `--durable-sqlite` | **91 passed**; 58.27 s |
| PF modules plus architecture, focused serial run | **105 passed** |
| `uv run lint-imports --no-cache` | **6 contracts kept, 0 broken** |
| DB reference generator and validator | Head **167**, **264** tables, **521** config leaves, no errors |
| Final head fixture | DELETE journal mode; integrity `ok`; zero FK violations; no `sqlite_sequence` or pending WAL |
| `git diff --check` | Clean |

The four PF modules are `test_activity_families.py`, `test_family_proposals.py`,
`test_family_evaluation.py` and `test_family_memory_projection.py`. The full suite
also covers the eight new single-request transport tests, prior provider behavior,
parameter classification, old `eval` CLI compatibility, no-family legacy
projection pins, table/replayer ownership, fixture integrity and shadow equivalence.

**End-to-end checkpoint:** a backup-API copy of `fixtures/conic-sections` at
`fixtures-local/phase3-checkpoint` ran the real CLI dry-run: one pair, two calls,
31,257 bounded tokens, estimated **$0.031257 at the explicitly supplied test
rate of $1/million tokens** (not a provider quote). Two fake judge passes applied
one two-item family. The replay produced:

- `fixtures-local/phase3-checkpoint-reports/pf-a-000fad0f1a026897.json`
- `fixtures-local/phase3-checkpoint-reports/pf-a-000fad0f1a026897.md`

There were six historical attempts and five cold memory-scoring rows, including
two attributed to the persisted resolved family judge `fake-resolved`.
`idea_hier` correctly had zero eligible calibrated observations in this legacy
fixture; the pure harness regression tests exercise it on nonempty observations.
Default strict revision evaluation also generates, with explicit exclusions.
CLI undo succeeded even after deleting the mutable workflow cache. Rerunning
proposals after undo made zero calls and did not reapply the family. The source
fixture database hash was unchanged. No working-vault files were changed.

**Resolved validation failures:** the first complete suite had 6,212 passes and
14 failures. They were two integration omissions, not retained failures:

- The new numeric `families.*` settings lacked parameter-registry classification,
  failing registry audit/CLI and the audit check in the legacy cutover test.
  They are now explicitly operational, with no measurement/scheduling authority.
- `AUTOINCREMENT` introduced `sqlite_sequence` into previously unchanged vaults.
  Timeline replay and debug time shifting encountered that unclassified internal
  table. Ordinary `INTEGER PRIMARY KEY` remains monotone because deletion and
  replacement are forbidden, and introduces no extra table. The migration head
  was rebuilt from the original 166 fixture after this correction.

All 80 targeted regression tests for these failures passed before the final full
suite. Earlier focused integration checks also caught the new projection missing
from the stale-row cleanup test, SQL-owner registration, and generated reference
line/count drift; each was corrected. Final runs have no failures.

## Exact owner workflow

Supply credentials in the shell, the selected vault's `.env`, or your normal
LearnLoop settings. Never put a key in committed files. The implementation did
not read your personal config directory or search for an owner vault.

First choose the source and make a new backup-API copy:

```bash
OWNER_VAULT=/absolute/path/to/your/vault
COPY="$PWD/fixtures-local/phase3-owner-copy"
uv run python - "$OWNER_VAULT" "$COPY" <<'PY'
from pathlib import Path
import sys
from learnloop.db.copies import copy_tree_with_databases
copy_tree_with_databases(Path(sys.argv[1]), Path(sys.argv[2]))
PY
```

In the chosen vault's existing `[ai.routing]` section, set
`pf_family_judge` to an existing `openai_chat` or `openrouter` profile with an
explicit model. Do not create duplicate TOML sections. Prefer a pinned model
revision, and inspect `learnloop config effective --vault "$COPY"` to confirm
the route. The same configuration must be present in the source before a live
run. If large LOs require embeddings, use Phase 1's explicit dry-run/backfill
workflow first; this command does not enable or backfill them.

Set `PRICE_PER_MILLION` to a positive conservative USD rate at least as high as
both the chosen model's input and output rates. This is an explicit owner price
bound, not an asserted current provider quote. All these caps are maxima; raise
them only after inspecting the estimate:

```bash
PRICE_PER_MILLION=YOUR_VERIFIED_POSITIVE_RATE
uv run learnloop families propose --vault "$COPY" --dry-run --json \
  --price-per-million "$PRICE_PER_MILLION" --judge-revision 1 \
  --max-candidates 500 --max-pairs 1000 --max-calls 2002 \
  --max-retries 2 --max-tokens 10000000 --max-cost-usd 5

# Actual owner-requested run on the chosen real vault, with the same caps.
# To rehearse first, replace "$OWNER_VAULT" with "$COPY" here.
uv run learnloop families propose --vault "$OWNER_VAULT" --json \
  --price-per-million "$PRICE_PER_MILLION" --judge-revision 1 \
  --max-candidates 500 --max-pairs 1000 --max-calls 2002 \
  --max-retries 2 --max-tokens 10000000 --max-cost-usd 5

# One-step undo: paste a family_id or proposal_id from the accepted array.
uv run learnloop families undo FAMILY_OR_PROPOSAL_ID \
  --vault "$OWNER_VAULT" --json
```

Rerunning proposals resumes completed verdicts. An undo remains undone for that
exact decision. A changed item, model setting or explicit judge revision creates
a new decision and must be costed again.

After the real run, make another fresh backup-API copy (same copy command with a
new destination), then generate the report without changing the source:

```bash
REPORT_COPY="$PWD/fixtures-local/phase3-owner-report-copy"
uv run python - "$OWNER_VAULT" "$REPORT_COPY" <<'PY'
from pathlib import Path
import sys
from learnloop.db.copies import copy_tree_with_databases
copy_tree_with_databases(Path(sys.argv[1]), Path(sys.argv[2]))
PY
uv run learnloop eval families --vault "$REPORT_COPY" \
  --output fixtures-local/phase3-owner-reports --json
# Only if you accept the explicitly labelled legacy reconstruction:
uv run learnloop eval families --vault "$REPORT_COPY" \
  --legacy-fallback current_content \
  --output fixtures-local/phase3-owner-reports-legacy --json
```

## Checkpoint and open questions

- Owner reviews replay counts/exclusions and uncertainty, not a claim that a key
  won on thin data. Any Phase 3b decision is a separate reviewed successor.
- Confirm the bounded judge profile, price bound and desired alias revision
  before paid work. No new P8/P11/P12 decision is needed.
- Integrate Phase 2's outcome view/arm registry once its branch lands; rebase,
  renumber migration 167 if occupied, regenerate the head fixture/reference, and
  rerun roles, replay equivalence and durability before merge.
- No merge or push is part of this task.
