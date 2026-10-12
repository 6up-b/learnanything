# Slice A Phase 1: implementation plan and checkpoint

## Scope and plan

Branch: `slice-a/phase-1`, created from `main` at `a3c8a867`.
Read: `CLAUDE.md`, the complete Slice A plan, Slice 1 §§9.1–9.2,
9.6 and embedding tests in §14, embedding consumers R1–R3 and §5.8,
the table-role registry, algorithm-change playbook and architecture Home.

1. Add the model-independent embedding contract and OpenRouter embedding
   transport under `src/learnloop/ai/`, including explicit routing, readiness,
   configuration/template defaults, privacy disclosure and call receipts.
2. Add migration `166_embedding_substrate_and_judgments.sql`: float16
   `embedding_vectors` (WORKFLOW) and append-only `judgment_ledger`
   (RAW_LEDGER), with store APIs and exact, model-isolated centered retrieval.
   Upgrade the migration-head fixture through a backup-API copy under
   `fixtures-local/`, retain rollback journal mode, update fixture references
   and regenerate/validate the database documentation.
3. Add reusable spend admission controls (candidate, pair, request/retry,
   token and estimated-cost caps), dry-run estimates and budget receipts.
   Unknown pricing fails closed unless explicitly bounded by the owner.
4. Add `learnloop embeddings backfill`, with a declarative recipe registry
   starting with canonical `facet/definition` and `item/stem`, batched calls,
   content-addressed resume, cancellation and aggregate-only reports.
5. Test clients with fake transports; stores, ledger immutability, spend
   admission, CLI dry-run, resume/idempotence and replay without provider calls.
   Run touched tests, durability tests, import lint and the full parallel suite.

## Invariants and boundaries

- No algorithm successor: scheduling, grading, persisted evidence semantics
  and served content remain unchanged.
- `embedding.enabled` and `embedding.backfill_enabled` default to false.
  PF generation and consumers belong to later phases.
- Rebuild consumes persisted inputs and never invokes embeddings or judges.
- Embeddings nominate/rank only; never decide identity, novelty or difficulty.
- No reads from the owner's settings or searches for their vault; no paid
  provider calls during implementation. Never modify tracked working vaults.
- Only the migration-head fixture is replaced under the documented procedure.
- No push, merge, or work on subsequent phases.

## Built

- Model-independent `EmbeddingClient`; one batched OpenAI-compatible request
  per `embed`, with hidden SDK retries disabled, OpenRouter non-retention
  routing, bounded coarse prefixes, response validation and usage receipts.
- Explicit embedding route, provider profile and readiness checks; no implicit
  active/chat provider fallback. Current templates offer an explicit
  `openrouter_embedding` profile but both embedding switches stay off.
- Float16 vectors, content-hash idempotence, exact mean-centered cosine
  retrieval, and a complete-current-record manifest required before retrieval.
  Vectors never write learner evidence or determine identity/novelty/difficulty.
- Append-only judgment ledger for unary and binary verdicts, with correction
  links rather than edits. LLM/diagnoser verdicts require model and prompt
  provenance in both the API and SQL. It has no learner-evidence writer.
- Finite candidate, pair, call, retry, token and estimated-dollar caps, pre-call
  admission, conservative usage reconciliation and receipt `budget_json`.
  Receipts also persist recipe/prompt version, model, dimensions, price basis
  and config fingerprint, linked to the aggregate report's `run_id`.
- `learnloop embeddings backfill`: canonical recipe registry, aggregate-only
  dry-run, batched checkpointing, content-aware resume, separate backfill lock
  and clean cancellation between batches. SIGINT/SIGTERM allows the in-flight
  batch to finish and save before stopping. The lock does not block practice.
- Settings displays read-only enabled/backfill status, model, dimensions and
  privacy disclosure. Embedding-only profiles cannot be selected for generation.

## Decisions and deviations

1. **No algorithm successor.** Infrastructure is dormant, with no serving or
   evidence changes. The effective-default fingerprint changes only because
   additive disabled configuration is included in that fingerprint.
2. **Unknown pricing fails closed even with a larger dollar cap.** The owner
   can supply `--price-per-million` as an explicit finite positive estimate.
   Zero/negative/non-finite overrides are refused. This is
   stricter and more auditable than pretending an unknown price fits a very
   large cap. Qwen's built-in $0.01/M estimate is from the specification, not a
   live quote; provider-reported usage/cost reconciles upward before admitting
   another request. Token estimates conservatively use UTF-8 byte length plus
   a prefix/framing allowance; oversized records are refused, never truncated.
3. **Caps are per invocation.** Retries consume the same invocation's remaining
   caps; rerunning gets new caps but excludes persisted work. Successful vector
   batches themselves are the content-addressed checkpoint; no redundant
   workflow table is needed. A process death after remote completion but before
   local commit can still leave a charged, uncheckpointed request; a remote API
   without an idempotency contract cannot provide exactly-once billing.
4. **One stored dimension per model ID.** The specified unique key omits
   dimensions. Changing dimensions for an already-populated model is refused
   before paying, rather than returning incompatible cached vectors. Old-model
   vectors are retained when backfilling another model. Retrieval supports an
   explicit lower per-consumer `dimensions` view by truncating before centering
   and ranking; this does not mutate or duplicate stored paid vectors.
5. **Centering scope is the current recipe view.** The centroid uses the
   current `record_kind × field × model × task_prefix` manifest, excluding
   stale revisions; candidate filters are applied before ranking. This refines
   the spec's `record_kind × model` scope to avoid mixing heterogeneous dossier
   fields or document/query conventions. Phase 1 has one field per record kind.
6. **Canonical recipes:** `facet/definition` includes authored title, claim,
   description, pre/postconditions, applicability, examples and non-goals;
   `item/stem` is the authored prompt only. Retired records are excluded.
   Expected answers, hints and learner responses are not embedded.
7. No diagnosis, family generation, placement, benchmark or evaluation arm is
   activated. PF route names are additive seams only; generation remains a later
   phase and has no executable paid command here.
8. **Cross-spec scope:** the diagnosis route mentioned alongside embeddings in
   Slice 1 §9.1 belongs to Slice 1, not the Phase 1 substrate row. No live
   retrieval consumer or mutable active/pending model pointer exists in Phase 1.
   `embedding.model` selects the model to backfill; mandatory manifest validation
   refuses partial indexes. The first serving consumer must keep its previous
   model until replacements are complete for **every affected record kind**.
   It must not interpret a changed backfill target as permission to serve a
   partial replacement. Both points were reviewed and retained as scope
   boundaries rather than silently adding Slice 1 behavior.
9. **Dry-run makes no model calls, migrations or data changes.** A normal
   read-only SQLite WAL reader may create coordination sidecars. Immutable
   reads were deliberately not used: ignoring committed WAL frames could
   misclassify completed work and cause duplicate payment.
10. Privacy text distinguishes the default OpenRouter endpoint from custom
    endpoints: custom services may ignore the OpenRouter retention option.
    The owner must verify their retention policy.

## Verification

Final integrated validation, with `LEARNLOOP_CONFIG_DIR` isolated under
`fixtures-local/`:

| Command/check | Result |
|---|---|
| `uv run pytest -n auto` | **6,109 passed**, 14 existing deprecation warnings, 187.78 s, 32 workers |
| `uv run pytest -m durability` | **59 passed**, 6,050 deselected |
| Five Phase 1 test modules with `--durable-sqlite` | **161 passed** |
| `uv run lint-imports --no-cache` | **6 contracts kept, 0 broken** |
| Database-reference generator and validator | Schema **166**, **261** tables, **519** config leaves, zero errors |
| `npm run typecheck` | Passed |
| `npm test` | **26 tests passed** across 7 files |
| `npm run frontend:build` | Passed; existing-style Vite chunk-size warning (>500 kB) |
| Fake-client backfill on backup-API copy `fixtures-local/phase1-smoke` | First run: 5 vectors, 1 batch; second run: 0 calls, 5 cached; source DB hash unchanged |
| Migration head | DELETE journal mode, integrity and foreign-key checks clean; no working-vault edits |

The five modules are `test_embedding_backfill.py`,
`test_openai_embedding_client.py`, `test_embedding_store.py`,
`test_judgment_ledger.py` and `test_spend_controls.py`. The store tests include
two same-version umbrella rebuilds preserving paid vectors and verdicts while
model construction is forbidden. Existing migration/rebuild/shadow-equivalence,
SQL-owner and fixture-copy-policy tests also pass in the full suite.

Two independent reviews covered backfill/spend/privacy and
client/routing/persistence. Concrete findings were fixed and regression-tested:
positive price admission, durable recipe provenance, UI disclosure, LLM
judgment provenance, per-consumer dimension views, and SDK failure normalization
so real provider failures use bounded retries. No live provider call was made.

### Initial validation failures and resolution

The initial full run had 6,079 passed and the following three failures (failure
sections reproduced below). All pass in the final full run.

- Registered the two new SQL-writing stores in the architecture ownership list.
- Regenerated the CLI snapshot under pytest's captured-output environment;
  only root help and the two new embedding help entries changed.
- The pre-existing PDF-page test assumes the optional `pypdfium2` renderer.
  The clean development environment lacked it. Installed `pypdfium2==5.14.0`
  into the workspace virtual environment using `uv pip install pypdfium2`;
  no production dependency or unrelated reader code was changed. To reproduce
  the full run from a fresh development environment, use:

  ```bash
  uv sync --extra dev
  uv pip install pypdfium2
  uv run pytest -n auto
  ```

```text
_______________ test_sql_writes_stay_in_registered_owner_modules _______________

    def test_sql_writes_stay_in_registered_owner_modules() -> None:
        violations: list[str] = []
        for root in (LEARNLOOP_ROOT, SIDECAR_ROOT):
            for path in python_files(root):
                relative = str(path.relative_to(REPOSITORY_ROOT))
                lines = _sql_write_lines(source_text(path))
                if lines and relative not in REGISTERED_SQL_OWNERS:
                    violations.append(f"{relative}: {lines}")
>       assert not violations, "\n".join(violations)
E       AssertionError: src/learnloop/db/stores/embedding_vectors.py: [58]
E         src/learnloop/db/stores/judgments.py: [27]
E       assert not ['src/learnloop/db/stores/embedding_vectors.py: [58]', 'src/learnloop/db/stores/judgments.py: [27]']

tests/test_architecture.py:401: AssertionError

___________________ test_recursive_cli_help_matches_snapshot ___________________

    def test_recursive_cli_help_matches_snapshot() -> None:
        expected = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
>       assert _help_snapshot() == expected
E       AssertionError: assert {'<root>': {'...24cb04'}, ...} == {'<root>': {'...24cb04'}, ...}
E         Omitting 171 identical items, use -vv to show
E         Differing items:
E         {'<root>': {'bytes': 20867, 'sha256': 'd351c91c300320f53c3715f962c1cda62029ece0ee2292ec231c261b5e8b0f52'}} != {'<root>': {'bytes': 20782, 'sha256': '36c4ca75e85ee51e998d109207b3aff5c8d8777710b586d04be88f78bcc24698'}}
E         Left contains 2 more items:
E         {'embeddings': {'bytes': 1587,
E                         'sha256': '06c65cc5fd4fa58de73a7538dba27ec25e0c9987651a60fcd34a04f71e4070e7'}, ...
E         ...Full output truncated (3 lines hidden), use '-vv' to show

tests/test_cli_help_snapshot.py:48: AssertionError

_______________ test_span_view_renders_available_local_pdf_page ________________

    def test_span_view_renders_available_local_pdf_page(tmp_path):
        from pypdf import PdfWriter

        repo = _setup(tmp_path)
        pdf_path = tmp_path / "book.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=300, height=400)
        writer.add_blank_page(width=300, height=400)
        with pdf_path.open("wb") as output:
            writer.write(output)
        with repo.connection() as connection:
            connection.execute(
                "UPDATE source_revisions SET original_uri = ? WHERE id = 'rev1'",
                (str(pdf_path),),
            )
            connection.commit()

        view = build_span_view(repo, "ext1", "s1", record=False)
>       assert view["viewer_mode"] == "pdf_page"
E       AssertionError: assert 'pdf_text' == 'pdf_page'
E         - pdf_page
E         + pdf_text

tests/test_span_view.py:123: AssertionError
```

Documentation regeneration also initially identified the new `embedding`
section missing from the generator's section-function map and stale prose
counts (495 instead of 519); both were corrected before final validation.

## Owner-run commands

No credentials or real embedding calls were used during implementation. Supply
`OPENROUTER_API_KEY` through your shell or the **copy's** `.env`; never commit it.
The following is opt-in work for the owner, not a command run against your vault
by the implementing agent.

First copy a path **you explicitly choose**, using SQLite's backup API:

```bash
export LEARNLOOP_CONFIG_DIR="$PWD/fixtures-local/phase1-owner-config"
SOURCE=/absolute/path/you/choose
COPY="$PWD/fixtures-local/phase1-owner-copy"
uv run python - "$SOURCE" "$COPY" <<'PY'
from pathlib import Path
import sys
from learnloop.db.copies import copy_tree_with_databases
copy_tree_with_databases(Path(sys.argv[1]), Path(sys.argv[2]))
PY
```

The destination must be new. If your SQLite file uses a non-`.sqlite` filename,
pass that filename in `database_names` to the copier.

In the copy's `learnloop.toml`, merge these settings into the existing sections
(do not create duplicate TOML sections):

```toml
[embedding]
enabled = true
backfill_enabled = true
model = "qwen/qwen3-embedding-8b"
dimensions = 4096

[ai.routing]
embedding = "openrouter_embedding"

[ai.providers.openrouter_embedding]
type = "openai_embedding"
model = "qwen/qwen3-embedding-8b"
base_url = "https://openrouter.ai/api/v1"
api_key_env = "OPENROUTER_API_KEY"
```

Review the estimate, then run with the same explicit caps:

```bash
uv run learnloop embeddings backfill --vault "$COPY" --dry-run --json \
  --max-candidates 10000 --max-calls 400 --max-retries 2 \
  --max-tokens 10000000 --max-cost-usd 1
uv run learnloop embeddings backfill --vault "$COPY" --json \
  --max-candidates 10000 --max-calls 400 --max-retries 2 \
  --max-tokens 10000000 --max-cost-usd 1
# A second identical run should report zero new calls and embedded records.
uv run learnloop embeddings backfill --vault "$COPY" --dry-run --json
```

Raises to these example caps are owner decisions, not recommendations to spend
without inspecting the dry-run. Use `--record-kind facet` or `--record-kind item`
to narrow scope. Reports expose estimates, charged usage and remaining work.
Embeddings approximate plaintext: keep the copy and its receipts/vectors under
the same private backup/export/sync controls as practice attempts.

## Open questions and checkpoint boundary

- No owner decision is needed to use the disabled substrate. Confirm live
  provider pricing and endpoint/model availability before the first paid run.
- Phase 3's P12 family-to-existing-substrate mapping remains an owner decision;
  this phase deliberately makes none of those modeling choices.
- No benchmark-based embedding-model selection, calibrator or threshold is
  introduced. Retrieval consumers and any model-switch activation policy remain
  in later phases, using the required complete manifest and retaining the old
  model until all affected scopes are complete.
- Stop at Phase 1. Do not merge/push or begin Phase 2/3 without instruction.
