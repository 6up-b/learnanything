# Refactor D5: constant gates in the substrate, rebuild, doctor, and the canonical-state predicate

Step D5 of arc D (`docs/specs/refactor_strategy_v3.md` §2.6), on branch `refactor/d5-constant-gates-substrate`, based on main `41387e1236` (D4 landed; the floor `OLDEST_SUPPORTED = mvp-0.58` is enforced at every door, the head is `mvp-0.59`). Structure track: no served or persisted value changes for a vault at or above the floor. The method is D4's (`docs/reviews/refactor-d4.md`).

## 1. Step 0, before any deletion

### (a) The count

`scripts/refactor_measures.py` at the base, floor `mvp-0.58`: 83 gate sites (`x in *_VERSIONS`), 75 constant at the floor, 8 varying (the facet-belief successor's `FACET_BELIEF_FIX_VERSIONS` / `FACET_BELIEF_CORRECTION_VERSIONS`, `mvp-0.59` only: live branches, not this step's). Of the 75, this step's files hold 19 (S1-S19 below) plus D4's three left-overs (L1-L3). The classifier counts only `in` tests against a set; it does not see `is_canonical_state_vault`'s 32 calls (a predicate over `CANONICAL_STATE_VERSIONS`), which are listed separately (§1(d)).

Every set tested at these sites (`CANONICAL_STATE_VERSIONS`, `P0_PROJECTION_VERSIONS`, `REGRADE_CONTRACT_VERSIONS`, `RECURRENCE_GROUP_VERSIONS`) holds both `mvp-0.58` and `mvp-0.59` (checked by importing them), so each gate takes its successor branch on every vault that opens.

### (b) The replay question: can a dead branch still run?

Rebuild replays attempts written under every older tag, under today's tag. Every site below except S13 and the stamp half of S19 reads **the vault's current tag** (`vault.config.algorithms.algorithm_version`, or the `algorithm_version` argument the projection's callers pass from it): below the floor it is dead, whatever tag a replayed row was written under. Where a vault's tag can come from was proven in D4 §1(b) and is unchanged at this base: `load_vault` refuses below the floor and a keyless config (ADR-019); doctor, the MCP server's and phone host's attach, and journals below the floor are refused the same way; a shadow rebuild's forced tag is refused below the floor (`shadow_rebuild.build_candidate_config`); `learnloop upgrade` sets the vault's tag to the table's links, which start at the floor; configs built in code (`LearnLoopConfig()`, tag `mvp-0.6`) reach none of these sites in production (`params/parameter_registry` reads numeric leaves only, `substrate/activities._algorithm_version` is a stamp, ledger D-23); the two harnesses that build their own vault below the floor (`learnloop goldenpath bootstrap`, `learnloop recall-calibration`) are refused by it (D-24).

**A tag this code does not know** (ledger D-31): such a vault opens and today every gate here, and `is_canonical_state_vault`, reads it as below every tag, so it is served the pre-`mvp-0.7` (per-LO, legacy) model. After this step those sites serve it the head's branch. No supported vault holds such a tag, and the head's canonical state is what a newer checkout's vault actually holds, so this does not make D-31 worse for a supported vault; the door fix stays D-31's.

**The tracked fixtures.** `fixtures/migration_head` names `mvp-0.6` and `fixtures/mvp017_route_check_replay` `mvp-0.17`; both open only under the tests' below-floor allowance (D1). After this step a test that opens either at its own tag runs the head's projection path; D4 §4 already showed the `mvp-0.17` fixture rebuilds to the same rows at its tag and at the floor for the attempt path.

### (c) Every gate site in this step's files

Classes as D4: **(a)** a pure tag gate: the gate and its dead branch go. **(b)** tag and kill switch: only the tag half goes; the switch and its off-branch stay for D7. **(c)** a reader of old rows by shape, a marker or a row's own stored tag: kept. **(d)** kept for a later step, with the reason.

Line numbers are the base's (`41387e1236`).

| # | site | set | constant at `mvp-0.58` | dead branch (below the tag) | class |
|---|---|---|---|---|---|
| S1 | `substrate/canonical_projection.py:319` `load_canonical_projection_snapshot` | `P0_PROJECTION_VERSIONS` | yes | the projection reads the v1 observation ledger (no administration, interpretation, adjudication or quarantine lineage) | (a) |
| S2 | `substrate/canonical_projection.py:329` same | `P0_PROJECTION_VERSIONS` | yes | no effective-observation references are loaded | (a) |
| S3 | `substrate/canonical_projection.py:351` same | `REGRADE_CONTRACT_VERSIONS` | yes | no contract-unrecorded hold (`frozenset()`) | (a) |
| S4 | `substrate/canonical_projection.py:671` `project_canonical_facet_state` | `CANONICAL_STATE_VERSIONS` | yes | no canonical projection at all | (a) |
| S5 | `substrate/canonical_projection.py:675` `use_p0` | `P0_PROJECTION_VERSIONS` | yes | raw attempt-type mass (no reliability discount), no adjudicated-outcome override, the coarse outcome schema not loaded | (a) |
| S6 | `substrate/canonical_projection.py:734` `regrade_contracts` | `REGRADE_CONTRACT_VERSIONS` | yes | every non-superseded row across epochs, under the first cited contract; no unrecorded-contract hold | (a) |
| S7 | `substrate/canonical_projection.py:1219` `project_capability_residuals` | `CANONICAL_STATE_VERSIONS` | yes | no residual activation | (a) |
| S8 | `substrate/canonical_projection_rollout.py:83` `refresh_canonical_projection_on_startup` | `CANONICAL_STATE_VERSIONS` | yes | no startup refresh, no baseline marker | (a) |
| S9 | `substrate/p0_projection.py:47` `activate_p0_projection` | `P0_PROJECTION_VERSIONS` | yes | raises `ValueError` (a precondition) | (a) |
| S10 | `substrate/administration_adapters.py:331` `purpose_adapter_path_live` | `P0_PROJECTION_VERSIONS` (or the module constant `P1_PURPOSE_ADAPTERS_ENABLED`, `False`, no config) | yes | the attempt hot path applies its FSRS review unconditionally (an ineligible observation still rewrites the card) | (a) |
| S11 | `substrate/rebuild_orchestrator.py:441` `_run_identifiability` | `CANONICAL_STATE_VERSIONS` | yes | the replayer clears its table and writes no identifiability watermark | (a) |
| S12 | `substrate/recurrence_groups.py:85` `recurrence_active` | `RECURRENCE_GROUP_VERSIONS` | yes | no recurrence groups | (b): switch `recurrence.enabled` |
| S13 | `substrate/recurrence_groups.py:447` `_source_judgments` | `DECIDER_TIER1_VERSIONS` | not a vault tag | — | (c): the tag stored in a same-cause judgment's own `rationale` (strategy §2.6 names it) |
| S14 | `ops/doctor.py:452` `_merge_mvp06_facet_recall_aliases` | `CANONICAL_STATE_VERSIONS` | yes | under `--fix-state`, folds aliased rows of the per-LO `evidence_facet_recall_state` in place | (a) |
| S15 | `ops/doctor.py:1881` `_check_mvp07_canonical_state` | `CANONICAL_STATE_VERSIONS` | yes | the unregistered-canonical-facet check does not run | (a) |
| S16 | `ops/doctor.py:1915` `_mvp07_facet_severity` | `CANONICAL_STATE_VERSIONS` | yes | facet-registry issues are warnings, an empty registry is skipped | (a) |
| S17 | `ops/doctor.py:1981` `_check_facet_contract_completeness` | `CANONICAL_STATE_VERSIONS` | yes | only a facet declaring part of its contract is checked, as a warning | (a) |
| S18 | `ops/doctor.py:2838` `_check_pre_first_practice_identifiability` | `CANONICAL_STATE_VERSIONS` | yes | no identifiability check | (a) |
| S19 | `db/repositories.py:26689` `_guard_legacy_facet_write` | `CANONICAL_STATE_VERSIONS` on the row's stamp | the writers stamp the vault's tag | the per-LO legacy write passes (a row stamped with a pre-canonical tag) | gate half (a) once its writers are gone (L3); the `FACET_BELIEF_FIX_VERSIONS` half reads the row's own stamp: (c) |
| L1 | `learner/facet_evidence_timeline.py:425` `_with_p0_masses` | `P0_PROJECTION_VERSIONS` | yes | the timeline carries no P0 mass map | (a), with S1-S6 in one commit |
| L2 | `learner/facet_evidence_timeline.py:848` `_observation_events_by_facet` | `REGRADE_CONTRACT_VERSIONS` | yes | epochs ordered by first-seen stamp and accumulated across epochs; no unrecorded-contract hold | (a), with S1-S6 in one commit |
| L3 | `learner/facet_state_reader.py:56` `is_canonical_state_vault` | `CANONICAL_STATE_VERSIONS` | yes | the legacy (`mvp-0.6`) per-LO facet state, at each caller (§1(d)) | (a), caller by caller |

**Constant gates of the same sets outside this step's files**, left: `content/proposals/patches.py:648`, `:1111` (`CANONICAL_STATE_VERSIONS`; D6's files), `diagnosis/probe_robust.py:60` (`P0_PROJECTION_VERSIONS`; D6), and the sidecar's `handlers/serializers.py:358` and `handlers/workbench.py:156` (`CANONICAL_STATE_VERSIONS` tested directly, not through the predicate; they snapshot the presented contract): (d), for D6 with the rest of the package-level gates. They are not callers of `is_canonical_state_vault`.

### (d) L3: `is_canonical_state_vault` and every call

At the base the predicate has 32 calls and one wrapper (`attempts/grading.py:284`, a lazy indirection with the same name). Each reads the vault's current tag, so each `False` branch is dead at the floor. What each dead branch does:

| # | call | dead branch (the legacy vault) |
|---|---|---|
| C1 | `attempts/attempts.py:3296` | `_persist_attempt_application(write_legacy_facet_state=True)`: the per-LO `evidence_facet_recall_state` rows and the legacy `facet_uncertainty` rows are persisted (the legacy writer the strategy names, `attempts.py:3322` in its numbering) |
| C2 | `attempts/attempts.py:4264` | an attempt's facet priors read from the per-LO table (`repository.facet_recall_state`) |
| C3 | `attempts/attempts.py:5294` | the don't-know attribution keeps the legacy names (`recall_failure`, `scaffold_failure`) |
| C4 | `attempts/grading.py:373` `builtin_error_type_defaults` | the five legacy builtin severities |
| C5, C6 | `attempts/grading.py:1941`, `:1961` `_grading_error_taxonomy` | the grader's prompt offers the five legacy error types and their selection policy; legacy seed names are not filtered |
| C7 | `attempts/grading.py:1997` `_normalized_recall_error_type` | a grader's legacy error name is not mapped to its mechanism |
| C8-C16 | `learner/facet_state_reader.py:106`, `:363`, `:376`, `:391`, `:417`, `:463`, `:468`, `:521`, `:533` | the read-site wrappers call the legacy repository methods (per-LO recall rows, every stored uncertainty row whatever its stamp) |
| C17, C18 | `learner/capability_grid.py:122`, `:221` | the grid reports `supported=False`; no blueprint readiness |
| C19 | `learner/recall_coverage.py:645` | no canonical reader is built (each facet reads through the wrapper's legacy branch) |
| C20 | `learner/facet_diagnostics.py:395` | the per-cell mass falls back to facet-level mass |
| C21 | `learner/facet_evidence_timeline.py:1191` `ready_derivation` | no Ready derivation (`None`) |
| C22 | `daily_plan/headline.py:71` | no capability cells read for the headline classes |
| C23 | `diagnosis/misconceptions.py:280` | the statement-matching registry normalization instead of the compositional one |
| C24, C25 | `diagnosis/probe_instance_generation.py:244`, `:307` | no compositional pair; no mechanism ids among the misconception ids |
| C26, C27 | `goals/goal_certification.py:114`, `:219` | no demonstrated capabilities; no recipe gaps |
| C28 | `goals/goal_projection.py:709` | no blueprint readiness |
| C29 | `scheduling/selection_rewards.py:438` | the flat recall blend for a blueprint-bearing LO |
| C30 | `learnloop_sidecar/handlers/facet_detail.py:267` | no canonical reader |
| C31 | `learnloop_sidecar/handlers/knowledge_model.py:92` | `supported: false` in the facet timeline DTO |
| C32 | `learnloop_sidecar/handlers/facets.py:74` | facet rows keyed by their raw id, not the canonical one |

No string dispatch names the predicate (no `METHOD_REGISTRY`, Typer, `MODULE_INVENTORY` or `_reg_const` entry; no frontend or phone caller: the frontend reads the DTO fields `supported` / `modelVersion`, which keep their values at the floor). Two tests name it: `test_learner_read_model_pinning` (asserts a basic vault is canonical) and `test_today_headline` (patches `headline.is_canonical_state_vault` to `True`, T4).

### (e) The old-row readers, kept

Every reader in these packages that interprets a row by its shape, a marker or its own stored tag. None is a tag gate on the vault; each stays whatever the floor.

| site (base lines) | what it reads | why it stays |
|---|---|---|
| `substrate/canonical_projection.py:364` `_historical_contract` and the fallback at `:757-779` (the strategy's `:736`) | rows citing no contract, or mixed contracts | evidence written before contract lineage (`mvp-0.7`) or by a pre-contract regrade folds against the live item's rubric |
| `substrate/canonical_projection.py:745` `current_epoch(attempt_evidence)` | grading epochs; a revision-less only grade by shape | the regrade-contract reading of rows written before `mvp-0.26` (the gate around it, S6, goes; the reader is the kept branch) |
| `substrate/canonical_projection.py:826` `unassessed_evidence_row`, `:946` `unverified_evidence_row` | the evidence row's attribution block and its interpretation key | PF-c rows written under or before the unassessed rule replay as written |
| `substrate/canonical_projection.py:586` `_adjudicated_score_fraction` | an adjudication heading the interpretation chain | adjudications recorded before ruling A carry their direction only there |
| `substrate/canonical_projection.py:955-957` | a row without an `observation_id` | the unresolved-cause factor keys such a row `attempt:criterion:0` |
| `substrate/canonical_projection.py:170` `p0_effective_evidence_mass` | an attempt with no active interpretation | a pre-P0.2 attempt contributes zero reliable mass (fail-closed) |
| `learner/facet_evidence_timeline.py:916-931` | the epoch's contract, else the live item's rubric | the timeline's twin of the projection's fallback |
| `learner/facet_evidence_timeline.py:808` `_decoded_attribution` | a row without attribution | legacy rows decode to `None` |
| `grading_epochs.py` (`current_epoch`, `ordered_epochs`, `only_grade`) | revision-less rows, epochs citing no contract | shared by replay, the projection and the timeline (D4) |
| `learner/facet_state_reader.py:168` `current_facet_uncertainty`, `:470`, `:535` | a stored uncertainty row's own `algorithm_version` | row tags (and the set varies at the floor) |
| `db/repositories.py:26687` (S19's other half) | the stamp of an uncertainty row being written | the successor's rows are admitted by their own tag |
| `substrate/recurrence_groups.py:447` (S13) | a judgment's stored `algorithm_version` | a row marker |
| `substrate/compat/activity_backfill.py` (rebuild's `_run_activity_substrate`, `rebuild_orchestrator.py:311`) | attempts and presentations with no activity rows | rebuild backfills the activity ledger for rows written before it; strategy: keep |
| `substrate/family_memory.py:23` `PROJECTION_LEGACY_FALLBACK` (`current_content`) | outcome rows without a content snapshot | rebuild's family memory replays them against current content |
| `substrate/activities.py:279` `resolve_legacy_item` | an item with no family/card/surface | rebuild and the activity backfill resolve it idempotently |
| `diagnosis/error_taxonomy_map.map_legacy_error_type` (called at C3, C5-C7) | an error type stored under a legacy name | maps stored legacy names to mechanisms on read |
| `attempts/attempts.py:1437`, `:1519`, `:1525`, `:1534`, `:1568` (D4's list) | stored grading source, blind record, hold, epochs | replay re-enters the live lane |
| `fixtures/mvp017_route_check_replay` | rows written at `mvp-0.17` | pins the regrade and hold readers; its tests must pass |

### (f) The paths the strategy names for deletion

- **The pre-canonical projection path** (the map's LEGACY-ONLY row: `canonical_projection.py:311` and `db/repositories.py:26940` in its numbering): S1-S6 plus S19's gate half. Reached only through the vault's tag (S1, S4) or a writer's stamp (S19); `load_canonical_observation_ledger` (the v1 ledger) has other readers (`diagnosis/probe_targeting.py:374`, `learner/residual_diagnostics.py:48`, and it is the base of the v2 ledger), so only the projection's use of it goes. The map's two reaches ("the head fixture at mvp-0.6 uses it; a shadow override can reach it") are closed: the shadow override by D1, and the head fixture opens only under the tests' allowance.
- **`substrate/compat/`** holds `activity_backfill.py` (rebuild imports it, `rebuild_orchestrator.py:311`) and a README: not unused, kept.
- **The `facet_uncertainty` and `evidence_facet_recall_state` writers.** `evidence_facet_recall_state`'s writers: the attempt step's persistence when `write_legacy_facet_state` (C1, only on a legacy vault), `replace_attempt_derived_outcome` / `record_attempt_outcome` (the same rows, passed by C1), and `merge_facet_recall_aliases` (S14, doctor's `--fix-state` on a legacy vault). Each is reached only through C1 or S14. `facet_uncertainty`'s writers: C1 (legacy) and the facet-belief successor's (`write_facet_uncertainty`, the successor's switch, varying): the successor's stays, the legacy one goes. The two tables stay (J1's list): rows already in them are read by the class (c) readers above.
