# Slice A Phase 1: independent audit

Branch `slice-a/phase-1` (commits `e85d876`, `2b8bf8a`, `0b4bc3a`), audited
against `docs/specs/spec_slice_a_practice_and_field_v1.md` (§1, §1a, §3 row 1,
§5), Slice 1 §9.1–9.2/§9.6/§14, Slice 2 R1–R3/§5.8/§12, `CLAUDE.md` and
`docs/algorithm-change-playbook.md`. Line references are to `0b4bc3a` unless a
section says otherwise.

## Implementer claims re-run on `0b4bc3a`

| Claim | Re-run result |
|---|---|
| Full suite 6,109 passed | **6,109 passed** (`uv run pytest -n auto`, 186 s) |
| Durability lane 59 passed | **59 passed** |
| Five Phase 1 modules under `--durable-sqlite`: 161 | **161 passed** |
| lint-imports clean | **6 kept, 0 broken** |
| `npm run typecheck`, `npm test` 26 | typecheck clean, **26 passed** (7 files) |
| Reference validator: zero errors | **zero errors** |
| Head fixture at 166, rollback journal | `journal_mode=delete`, `max(version)=166`, integrity ok; schema diff vs `migration_head_165` is exactly the 2 tables, 2 indexes and 5 triggers of migration 166; only `schema_migrations` row count changed |

The claims hold. The findings below are things the suite does not test.

## Findings, ranked by severity

Severity: **Medium** = wrong behaviour reachable today or a seam that later
phases would have to break; **Low** = latent, cosmetic, or test/process debt.
No High findings: nothing writes evidence, changes serving, leaks the key, or
lets replay call a model.

| # | Sev | Finding | Verdict |
|---|---|---|---|
| M1 | Medium | Settings health chip turns red for every new vault without an OpenRouter key, even with embeddings disabled | fix |
| M2 | Medium | The embedding-only profile is accepted, reported "ready", and offered as a generation/grading provider | fix |
| M3 | Medium | `embedding.enabled` is enforced only inside backfill; the `embedding` route returns a ready paid client while the master switch is off | fix |
| M4 | Medium | Recipe registry is keyed by record kind only; Phase 5's `item/skeleton` and `facet/dossier_*` cannot be registered without breaking the CLI, report and receipt manifest | fix |
| L1 | Low | MRL per-consumer truncation in `retrieve()` does not renormalize before centering | fix |
| L2 | Low | A malformed paid response escapes `backfill_embeddings`; the CLI replaces the report (run id, charged spend) with `status: invalid`; provider failures lose their SDK error class | fix |
| L3 | Low | A sixth hard-coded `migration_head_166` path (CLAUDE.md lists five) | fix |
| L4 | Low | Template: `[embedding]` splits the `[ai]` comment from `[ai]`; project jargon ("Phase 1", "PF") in every new vault's `learnloop.toml` | fix |
| L5 | Low | Every `learnloop` invocation now imports numpy (~55 ms) through the CLI registration | fix |
| L6 | Low | Replay-makes-no-calls test only patches two factory functions; no Phase 1 test runs in the durability lane | fix |
| L7 | Low | `get_config` lists the embedding profile's ignored `model` field, not the authoritative `embedding.model` that `get_settings` shows | fix |
| L8 | Low | "Unknown price" refusal does not say how to supply a price | fix |
| A1–A9 | — | Spec-naming and deviation decisions | accept (documented below) |
| N1–N5 | — | Docs churn, migration, security, invariants | not a problem |

### M1. Settings chip regression for new vaults (fix)

`src/learnloop_sidecar/context.py:423` (`_settings_ready`) checks readiness for
**every** `AIRoutingConfig` field. The new template sets
`ai.routing.embedding = "openrouter_embedding"`
(`src/learnloop/config/template.py:760`), and that profile is ready only when
`OPENROUTER_API_KEY` is set.

*Scenario (reproduced with a probe):* a new vault, Codex ready, no OpenRouter
key, `embedding.enabled = false`. `_settings_ready` returns **False**, and
`App.tsx:404` shows the settings chip as "missing fields". With the embedding
route removed it returns True. Codex-only users see a broken-settings state for
a feature they never enabled. Existing vaults are unaffected only because their
TOML lacks the route.

*Fix:* check the embedding route only when `embedding.enabled`, and check every
route under its own task semantics (see M2).

### M2. Embedding-only profile usable as a generation provider (fix)

The implementer's review says "Embedding-only profiles cannot be selected for
generation". That holds only in `SettingsScreen.tsx`. The backend accepts the
profile everywhere:

- `available_grading_providers` (`context.py:374`) offers `openrouter_embedding`
  as a grading backend, so `set_grading_provider` accepts it;
- `update_ai_settings` (`handlers/settings.py:231`) accepts it as
  `active_provider` or as a use-case provider;
- `LEARNLOOP_AI_PROVIDER=openrouter_embedding`, `ai.fallback_provider`, or any
  task route can name it.

`check_ai_runtime` then reports it **ready** (the chat health check is skipped
for this type), and `ready_client_for_task("grading")` returns an
`OpenAIEmbeddingProviderClient`.

*Scenario (reproduced):* with `LEARNLOOP_AI_PROVIDER=openrouter_embedding`,
grading resolves `ready=True` to a client with no `complete()`. Every grading
call then raises "does not support structured operation". The configured
fallback provider is never tried, because the primary claimed ready. The
inverse direction (a chat profile on the embedding route) was already refused
(`routing.py:222-234`).

*Fix:* one guard at the shared choke point (`runtime_for_provider`,
`client_for_provider`, `_resolve_selected_provider`). Embedding profiles serve
only the `embedding` task, and the `embedding` task accepts only embedding
profiles. The sidecar also refuses embedding profiles for active, use-case and
grading selection, and leaves them out of the grading picker.

### M3. Master switch not enforced at the route (fix)

`routing.py:119-121, 244` resolves the `embedding` route to a ready, paid
client regardless of `embedding.enabled`. Only `backfill_embeddings` checks
the switches (`ops/embedding_backfill.py:164`).

*Scenario:* a Phase 3 or Phase 5 consumer (family blocking, `find_practice`)
calls `ready_client_for_task(..., "embedding")`. It sends learner-derived text
to OpenRouter in a vault whose template says `enabled = false`, unless every
consumer remembers to re-check the switch. Slice A §5.6 requires separate
switches that are off in the template. The switch should therefore be
enforced where the client is obtained.

*Fix:* `ready_client_for_task("embedding")` returns a no-client resolution
with a clear message while `embedding.enabled` is false.

### M4. Recipes keyed by record kind only (fix)

`vault/embedding_recipes.py:79-104` keys `RECORD_KIND_RECIPES` by `"facet"` and
`"item"`, each with one field. `ops/embedding_backfill.py:150` and the receipt
manifest key `recipe_versions` by kind. The CLI `--record-kind` selects kinds.

Slice 2 R3/§12 declares recipes per **kind/field**: `item/stem`,
`item/skeleton`, `facet/definition`, `facet/dossier_scope|moves|errors|contrast`.

*Scenario:* Phase 5 adds `item/skeleton`. It cannot be registered next to
`item/stem` without changing the registry key, the CLI meaning, the report and
receipt manifest format, and the existing tests. Receipts written by Phase 1
would then use a manifest format that later receipts no longer use.

*Fix:* key recipes by `kind/field`. Selection accepts a kind (all of its
fields) or an exact `kind/field`, and the manifest records `kind/field`
versions.

### L1. MRL view not renormalized (fix)

`db/stores/embedding_vectors.py:117-119` truncates stored and query vectors to
`dimensions` and then centers them. Stored vectors are unit-norm at full width,
because the client truncates and **then** normalizes
(`openai_embedding.py:114-119`). A truncated prefix is not unit-norm, so the
centroid and the centered cosines are weighted by prefix norm. A
per-consumer 1024-d view would then rank differently from vectors embedded at
1024 d. *Fix:* after a real truncation, L2-normalize rows and query, then
center. The full-width path is unchanged.

### L2. Malformed paid response and error class (fix)

`ops/embedding_backfill.py:231-267` catches `AIInterrupted`,
`SpendLimitExceeded` and `AIProviderUnavailable` only. The client raises
`ValueError` for a paid but invalid response (wrong indices, width, norms), and
an `AttributeError`/`TypeError` for a response without `data`. The backfill
also raises `ValueError` itself for a wrong vector count or width.

*Scenario:* a provider returns 200 with a malformed body after charging. The
exception escapes `backfill_embeddings`, and the CLI (`cli/embeddings.py:79`)
prints `{"status": "invalid", "reason": ...}`, dropping `run_id`, `charged`
and `remaining`. The receipt still exists, but the report the owner reads no
longer shows the spend.

Separately, `AIProviderUnavailable` hides the SDK class: the report and the
receipt both say `AIProviderUnavailable`, so an invalid key cannot be told
apart from a 5xx.

*Fix:* treat any invalid response as a non-retried `provider_failed` that
keeps the report. Normalize response-shape errors to `ValueError` in the
client. Carry the SDK class name (never its message) as `provider_error`.

### L3. Sixth hard-coded head-fixture path (fix)

`tests/test_embedding_store.py:170` hard-codes `fixtures/migration_head_166`.
`CLAUDE.md` lists exactly five paths to update, so the next migration will break
this test. *Fix:* resolve the single `fixtures/migration_head_*` directory.

### L4. Template layout and jargon (fix)

`config/template.py:711-721` inserts `[embedding]` between the
"AI is optional / Precedence" comment and `[ai]`, so new vaults' TOML attaches
that comment to the wrong table. `template.py:761-767` writes
"Phase 1 has no PF consumers" and six commented `pf_*` keys into every user's
config. *Fix:* move `[embedding]` after `[ai.routing]` with its own comment, and
drop the commented PF keys (the schema fields stay). Comment changes do not
alter the effective-defaults fingerprint.

### L5. numpy on every CLI start (fix)

`cli/embeddings.py:14` imports `ops.embedding_backfill`, which imports the
numpy-backed store at module load. `learnloop.cli` therefore imports numpy for
every command; numpy was not imported at CLI start before. *Fix:* import the
backfill lazily inside the command.

### L6. Replay test strength, durability coverage (fix)

`tests/test_embedding_store.py:158-184` forbids only
`make_ai_provider_client[_from_profile]`. A replay path that built
`OpenAIEmbeddingProviderClient` or `openai.OpenAI` directly would pass. None of
the Phase 1 tests is in the `-m durability` lane, which CLAUDE.md says is the
only place WAL behaviour is tested. *Fix:* also poison the SDK constructor and
`OpenAIEmbeddingProviderClient.embed`. Mark the replay-preservation test and
the backfill idempotence/resume tests `durability`.

### L7. `get_config` shows the ignored profile model (fix)

`context.py:363` reports `profile.model` for every provider. For
`openai_embedding` profiles that field is ignored: `embedding.model` is
authoritative (`ai/client.py:28-32`). `get_settings` already reports the
authoritative value. *Fix:* the same substitution in `get_config`.

### L8. Unknown-price message (fix)

`ai/spend.py:113-114` says "supply an explicit finite owner price estimate"
but does not say how. *Fix:* the backfill report's reason names
`--price-per-million` and the model id.

## Accepted, with rationale

- **A1. Profile name.** The spec's "`openai_embedding` profile" is the
  profile **type**: Slice 1 §9.1 says "New profile class
  `type: "openai_embedding"`", and Slice 1 §12 names its instance
  `openrouter_qwen3_8b`. The type is implemented exactly; the instance name
  `openrouter_embedding` is free. Caveat: `openrouter_<use_case>` is the
  namespace `settings_store.openrouter_profile_name` materializes. Adding a
  future use case literally named `embedding` would overwrite it with a chat
  profile, which M2's guard then refuses (fails closed). Not worth a rename.
- **A2. Stored width 4096, not Slice 1 §12's `dims = 1024`.** This was not
  listed as a deviation. Slice 1 §9.1/§9.2 store "dimensions per `model_id`",
  with MRL truncation **per consumer**. Storing the full width keeps the
  information, and `retrieve(dimensions=...)` (renormalized after L1) supplies
  the consumer view. The cost is 8 KiB per vector, roughly 8–25 MB for a few
  thousand records. One width per model is fixed once vectors exist, so
  choosing the full width now is the reversible option.
- **A3. Dormant PF routes** (`ai/routing.py:20-25`, `config/schema.py:975-980`,
  `handlers/settings.py:74-79`). Slice A §1 puts per-component routes (PF §5.8)
  in the evaluation layer; Phase 1's row lists only the ledger. The routes are
  unused and default to `None`. Phases 3 and 5 must decide whether an unset PF
  route may fall back to `active_provider`, which it currently does like any
  chat route. The template no longer advertises them (L4).
- **A4. The implementer's ten deviations.**
  1. No successor; the `mvp-0.9` fingerprint is updated in place. *Accept.* No
     persisted meaning changes, and operational config additions have updated
     this fingerprint in place before (`40a0c0e`, `6dfc421`, `4de0924`).
  2. Unknown price refused even under a larger cap. *Accept.* It is stricter
     than "unless the owner raises the cap": an unknown price cannot be
     compared with any finite cap. L8 makes the remedy discoverable.
  3. Caps per invocation; no exactly-once billing across a crash. *Accept.*
     The remote API has no idempotency key.
  4. One stored width per model; a dimension change is refused before paying.
     *Accept,* with L1.
  5. Centering scope `kind × field × model × prefix`. *Accept.* It refines
     §9.2 and is required once dossier fields exist.
  6. Recipes: facet definition fields; item prompt only. *Accept.* Canonical
     text (R3), with no answers, hints or responses.
  7. No PF/diagnosis activation. *Accept.*
  8. The diagnosis route stays in Slice 1. *Accept.* It is not in the Phase 1
     row.
  9. Dry-run may touch WAL coordination files. *Accept.* Verified on a WAL
     vault: only `state.sqlite-shm` changes; the DB and `-wal` bytes do not.
  10. Privacy text distinguishes OpenRouter from custom endpoints. *Accept.* It
      is accurate. The request sets `data_collection=deny`, and the key is
      never sent anywhere else.
- **A5. Non-OpenRouter endpoints.** The client always sends
  `extra_body={"provider": {...}}`, which a strict OpenAI-compatible endpoint
  may reject with HTTP 400. Phase 1 targets OpenRouter only, and hard-coding
  deny is the privacy-safe default. A profile field (Slice 1 §12 shows
  `data_collection = "deny"`) can be added when a non-OpenRouter endpoint is
  actually needed.
- **A6.** The profile's `model` and `dimensions` fields are ignored;
  `embedding.model` and `embedding.dimensions` are authoritative (Slice 1
  §9.6), as the template comment says.
- **A7.** `LEARNLOOP_AI_PROVIDER` does not redirect the embedding route
  (`routing.py:119`). This is correct: the env override names a chat provider,
  and Slice 1 §9.1 forbids an active-provider fallback. `CLAUDE.md`'s phrase
  "overrides every AI route" is now slightly imprecise (owner's file; not
  edited).
- **A8.** Dataset export (`substrate/dataset.py:623`) includes
  `judgment_ledger` (RAW_LEDGER) and excludes `embedding_vectors` (WORKFLOW),
  matching the spec's roles. Vectors also never leave the vault through that
  path.
- **A9.** ADR-015 still names `migration_head_165`. It is a dated decision
  record, not one of the five procedure paths.

## Not a problem

- **N1. Regenerated-docs churn in `0b4bc3a` (~290 files).** I re-ran
  `db_generate_reference.py` at `0b4bc3a`. The output is byte-identical to the
  commit except `source_commit`/`source_commit_timestamp`, which the generator
  stamps from `git rev-parse HEAD` into every page by design. The other line
  changes are citation line numbers shifted by this branch's own source edits
  (`parameter_registry.py` +2 lines, `config/schema.py` +16).
  `1c65ffc` (294 files) set the same precedent. It is deterministic output
  that belongs with the change, not environment noise. Keep it, and regenerate
  after any further source edit.
- **N2. Migration 166.** Roles are correct per spec: `embedding_vectors`
  WORKFLOW, `judgment_ledger` RAW_LEDGER, so rebuild clears neither. The
  ledger's columns match PF §5.8 exactly, including the `judge` enum. SQL
  triggers enforce append-only (UPDATE, DELETE, INSERT OR REPLACE),
  same-question supersession, and model provenance for llm/diagnoser verdicts.
  The vector BLOB is float16 with a length check, and the `UNIQUE` matches
  §9.2. The head fixture was upgraded through the backup API, renamed, kept in
  rollback mode, and its README updated. The five paths were updated
  (`db_generate_reference.py` three times), and the reference regenerated and
  validated.
- **N3. Security and privacy.**
  - The key is read from `os.environ` after `load_config` → `load_dotenv`
    (shell > vault `.env` > global `settings.env`), the existing loader.
  - The key is never logged or receipted. Receipts store `prompt_hash` only
    (`input_text` is `None` for list prompts), and SDK exceptions are replaced
    by a fixed message with `from None`.
  - Reports are aggregate-only; the settings payload exposes only key presence
    and the last-4 hint (existing behaviour).
  - The disclosure appears in `config effective` and Settings.
- **N4. Invariants.**
  - Rebuild clears only DERIVED tables, and nothing on the replay path imports
    the embedding client.
  - No consumer can let an embedding decide identity, novelty or difficulty
    (R1/R2): there are no consumers.
  - No serving, evidence or scheduler file changed.
  - Existing chat routing is unchanged for configurations that do not name the
    embedding profile; M1 and M2 are the two exceptions.
- **N5. Test quality.**
  - Spend tests drive the real `SpendBudget`, covering every cap boundary,
    retries, reconciliation and cancellation.
  - Ledger tests hit the real SQL triggers.
  - Client tests run the real client against the fake SDK, checking batching,
    the base URL, `data_collection`, truncation and receipts.
  - Backfill tests cover dry-run (no client, unchanged DB bytes), resume after
    cancel, and fail-closed caps before client construction.
  - The UI test checks the read-only section and type-based filtering. Its
    `slice(0, 4)` selector choice is brittle but acceptable.

## Fixes applied

*(filled in after the corrections below)*
