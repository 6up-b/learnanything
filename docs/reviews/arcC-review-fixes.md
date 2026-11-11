# Arc C review fixes: retired config fields and the identities that hashed them

Branch `refactor/arcC-review-fixes`, based on `daadef09dd` (arc C's tip: C1, C2, C3, C4, C5, C6, C7a, J1). Arc C's
contract (`docs/specs/refactor_strategy_v3.md` §2.1 "Deleting", §2.5): a deletion changes nothing at a fixed
input, and old stored rows and old configs still load. The adversarial Codex review of `88607cb3fe..daadef09dd`
found the contract broken by serialization (finding 1, HIGH): C3 deleted `FacetIdentityConfig.merge_locked_facets`,
and both synthesis entries put `facet_identity.model_dump(mode="json")` into the hashed manifest scope whose hash
is the completed-run cache key, so a completed bootstrap or append run is no longer reused for the same request
and a new (paid) agent run starts. Findings 2-5 (`tests/session_tmp.py`) are fixed by the orchestrator on another
branch and are out of scope here.

## 1. Audit (written before any code change)

### 1.1 What arc C removed from surviving models

Method: import every module of `learnloop`, `learnloop_sidecar`, `learnloop_mobile` and `learnloop_mcp` from a
`git archive 88607cb3fe -- src migrations` extract (under the gitignored `fixtures-local/`) and from this tip, and
compare the field names and defaults of every pydantic model and dataclass present in both (2,178 classes at base,
2,104 at tip; the 74 that went are deleted modules' and RPC handlers' own classes, none reachable from surviving
code). Only config models lost fields; no vault, record or receipt model changed:

| Model (parent path) | Removed field | Default at base | Step |
| --- | --- | --- | --- |
| `FacetIdentityConfig` (`facet_identity`) | `merge_locked_facets` | `true` | C3 |
| `PlanConfig` (`plan`) | `pre_questions` | `3` | C3 |
| `MasteryIRTConfig` (`mastery.irt`) | `discrimination_min`, `discrimination_max` | `0.2`, `3.0` | C3 |
| `SeverityExampleConfig` (`recall_coverage.severity_examples.*`) | `target_error_type` | `null` (`"arithmetic_slip"` on the built-in `arithmetic_slip` example) | C3 |
| `ErrorImpact` (`error_impacts.*`) | `lo_mastery_delta` | `0.0` (`-0.05` on the built-in `recall_failure` and `scaffold_failure` entries) | C3 |
| `LearnLoopConfig` | `locks` (`LocksConfig`: `facet_lock_mass`, `facet_surface_groups`) | `2.0`, `2` | C3 |
| `AIConfig` (`ai`) | `agent_harness_opt_in` | `false` | C4 |
| `CodexConfig` (compat) | the whole class | — | C4 |

A default `LearnLoopConfig().model_dump(mode="json")` differs between base and tip in exactly these 15 leaves, and
a legacy `learnloop.toml` that sets every removed key (plus a top-level `[codex]` table) loads at both, differing
in exactly the removed keys: C4's rewrite of the `[codex]` normalization yields the same `ai.providers.codex`
profile. `CodexConfig` was the non-serialized `config.codex` view: never dumped or hashed (its readers showed a
model name, which `codex_profile_value` still returns). The routes `field_llm_probability` and `proof_check` were
retired before arc C (`RETIRED_ROUTES` at base) and are not arc C changes. C1's 66 leaf definitions included no
config field. C2, C5 and C6 removed parameter-registry specs (19 decision specs: the five `locks`/IRT/
`lo_mastery_delta` leaves above and 14 `module:CONSTANT` paths of deleted modules); see 1.3.

### 1.2 Every place a parent model is serialized into something hashed

Search: every `model_dump`/`model_dump_json` in `src` (413 sites in 165 files) whose receiver is the whole config or
one of the parents above (directly or through a variable or argument), every `content_key`/`content_hash`/
`sha256`/`canonical_hash` that takes such a dump, and what each hash then feeds (cache lookups, dedupe keys,
`INSERT OR IGNORE` keys, seeds, version labels, file names), followed to its readers.

| # | Site | Retired field(s) reached | Class | Evidence |
| --- | --- | --- | --- | --- |
| 1 | `content/synthesis/source_set_synthesis.py:2198` (bootstrap) | `facet_identity.merge_locked_facets` | **COMPARED** | scope → `build_manifest` → `compute_manifest_hash` → `agent_run_input_context_hash` → `_reusable_bootstrap_run` → `completed_agent_runs_by_context` (exact equality). A run completed before arc C is not reused: a new agent run starts (Codex reproduced it; so does the new test). |
| 2 | `content/synthesis/source_append.py:286` (append) | same | **COMPARED** | same chain → `completed_agent_run_by_context(APPEND_AGENT_PURPOSE, …)`. |
| 3 | `placement/predictor.py:59` `LiveMasteryPredictor.version_hash` | `mastery.irt.discrimination_min/max` | **COMPARED** | the live predictor's version enters `instructional/valuation.retention_problem`'s `state_hash`, which `instructional/needs.py:166` puts into the `voi_forecasts` receipt key (`INSERT OR IGNORE`): the same need valued at the same state after arc C writes a second forecast instead of deduplicating. It is also the version label of AD's incumbent forecast receipts (`forecaster_version`, grouped by version in `evsi_calibration/forecast_report.py`), placement decisions and quick checks (`predictor_version`). |
| 4 | `field/predictors.py:48` `_mastery_hash_view` (every field arm's `version_hash`: `lo_general`, `mastery_ekf`, the T8 success-head arms, AD's challenger `lo_general+composite`) | `mastery.irt.discrimination_min/max` | **COMPARED (version identity)** | AD's challenger `forecaster_version` label; the eval harness's `manifest.arm_hashes`. The project already holds these hashes fixed when an arm does not read a key (`_OFFLINE_INERT_MASTERY_KEYS`: "arms keep the hashes recorded before the key existed; tests/test_eval_harness.py pins them"); arc C's batch instead re-pinned the three eval digests (`c828893847`). Nothing names or reuses a report by them (the field report is written as `<stem>.json`), so the eval digests alone would be provenance; the shared hash is fixed for #3/#4's labels and the precedent. |
| 5 | `cli/field.py:139`, `cli/success_head.py:186` | all (whole config dict) | feeds #4 | `MasteryConfig.model_validate(config["mastery"])` builds the arms, so a vault that set a non-default `discrimination_*` hashed it into every arm at base; also the field report's `manifest.config_hash` (provenance). |
| 6 | `ops/embedding_compare.py:729` → `:810` | all (whole config) | **COMPARED (name)** | `manifest.config_hash` is part of the identity that names the report files (`{suite}-{identity}.json/.md`): a rerun at a fixed input writes beside the earlier report instead of over it. Nothing reads the file back. |
| 7 | `diagnosis/split/reports.py:272`, `ops/embedding_backfill.py:242` (also copied into the model event's `budget_json`), `practice_index/evaluation.py:858` (`version_manifest`, persisted with the decision), `ops/family_proposals.py:339`, `ops/pf_generation.py:1993`, `practice_index/dossiers.py:481`, `ops/contamination/report.py:453` | all (whole config) | PROVENANCE-ONLY | `config_hash` in a report or run manifest; no code reads it back or compares it (`grep` for `["manifest"]`, `["config_hash"]`, `get("config_hash")`: only the split report's markdown renderer, which prints other manifest keys). C3's claim holds. |
| 8 | `field/evaluation.py:711` `manifest.config_hash` | all | PROVENANCE-ONLY | report field (moves back to base as a side effect of #5's fix). |
| 9 | `daily_plan/engine.py:2189` `_config_hash(plan_config)` → `daily_plans.config_hash` | `plan.pre_questions` | PROVENANCE-ONLY | only the store's column list and `adaptive_difficulty/column_classes.py` name the column; no reader compares it. |
| 10 | `daily_plan/engine.py:1412` plan config → data-capture prefilter receipt (`config_hash`, `config_payload_hash`, content-addressed part) | `plan.pre_questions` | PROVENANCE-ONLY | the part store deduplicates blobs by hash (storage only); the row also carries `code_revision`. The stored payload says what the decision read, which no longer includes the retired key. |
| 11 | `router_objective/decision_state.py:267` → receipt `versions.config` | all | PROVENANCE-ONLY | sits beside `versions.code` (`code_revision()`), which changes at every commit; nothing compares it. |
| 12 | `params/parameter_registry.py` `refresh` (per-path `effective_value_hash`) and `freeze_manifest` (`manifest_hash`) | the 19 removed specs | per-path: COMPARED, unchanged; manifest: PROVENANCE-ONLY | `refresh` compares each spec's stored value hash (a change demotes a promoted status and clears certificates): resolving all 409 base / 390 tip decision specs on a default config, no surviving spec's value hash changed. Removed specs' stored rows are kept, never refreshed, and still enter `freeze_manifest` from the table, so an existing vault's next manifest is built from the same rows; `parameter_registry_manifests.manifest_hash` has no reader (one manifest per version, idempotent by version). |
| 13 | `learnloop_mobile/allowlist.py` `allowlist_digest` (compared with the PWA build) | removed RPCs | unchanged | arc C changed no phone allowlist entry; base and tip digests are equal (`8c72de0e…98fc7`). No other RPC catalog is hashed (sidecar, MCP, Tauri: none found). |
| 14 | `daily_plan/engine.py:458` reading-choice fingerprint; `substrate/canonical_projection_rollout.py:223` fold-inputs fingerprint; `router_objective/decision_state.py` `_config_seen` | all (whole config) | COMPARED in-process only | per-process memos (keyed also on the loaded vault object or the database watcher); a code change restarts the process, so they never compare across arc C. |
| 15 | `substrate/shadow_rebuild.py:201`, `sim/runner.py:225` | all | not a hash | dump → dotted overrides → re-validate. |
| 16 | `cli/config.py:36` (`config effective`), sidecar settings, `cli/router.py`, `cli/placement.py`, … | — | not a hash | display only. |

### 1.3 Beyond config

Registry specs (C2, C5, C6): no aggregate hash of the spec set exists besides `freeze_manifest` (row 12). Removed
RPC names: no hashed catalog besides the phone allowlist (row 13). Vault and record models: unchanged (1.1).
Changed constants in surviving modules: none that enter a hash (the removed `*_VERSION`/policy constants belonged
to deleted code paths: `router/decisions.py`'s staged P2 builder, `activity_patterns`' deleted functions, the
deleted modules' registry entries).

## 2. Fix

(Filled in after the audit.)
