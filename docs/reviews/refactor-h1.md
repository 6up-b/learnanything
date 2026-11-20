# H1 — Name them apart

Base: `bcccfa21749447cf0d43544a8608bcf4c8e9abea`, branch `refactor/h1-name-difficulty-apart`.
This is a naming/routing change. No scalar use is retired, no configuration default or persisted name changes,
and no identity or golden is regenerated. Production change: six files, 31 added / 30 removed lines (61 changed).

## Judgment calls to read first

- New seam calls deliberately pass the same three arguments as the former static calls. They do **not** fetch a
  posterior or add a repository argument. Thus even with EB on they retain the existing authored fallback.
  A future behavioral change can supply a recorded item-parameter posterior deliberately.
- `learner/lesson_weight.py::recorded_trajectory` and `_outcome_item_params` stay on `item_irt_params`.
  L4-2 already records their mismatch: live grading resolves EB state and then subtracts the priming offset;
  reconstruction reads current authored content and does neither. Today's posterior is not historical input.
  This step neither corrects nor masks that difference by routing reconstruction through a live-state lookup.
- `attempts/attempts.py::_belief_update` also keeps the static helper: it needs the **authored prior mean** for
  `update_item_difficulty`, not the posterior being updated. The seam itself necessarily calls the static helper.
- The inventory found a separate existing crossing: `PracticeScreen._difficulty` can display FSRS D (1–10) on
  the scalar's 0–1 bar, ahead of the LO prior. It is unchanged, explicitly audited, and recorded as H1-1 in the
  bug ledger with a strict-xfail test (wanted 0.2, actual 9.0). Fix assigned to H5, due at arc H close.
- No private-vault shadow was possible within this task's prohibition on reading vaults or `fixtures-local`.
  Literal before/after results and the requested synthetic/pinned gates are the local proof, not a claim that
  P-shadow has been run. The owner/orchestrator still owns that proof and the landing gate.

## Inventory

Search: `git grep -n -i difficulty -- src`, followed by exact-field, helper-call and table searches. An AST audit
checked all Python files in `src/` for attribute, `getattr`, mapping/subscript, literal-key, explicit SELECT and
IRT-helper sites. The test records each expression and count with a reason. Generic row/model transport is
identified separately below; it is not a numerical reader just because a whole row carries a field.

Kinds:

- **Scalar**: `PracticeItem.difficulty`, `LearningObject.difficulty_prior`, `pf_candidates.difficulty`; the
  0–1 authored/LLM/panel label, or its IRT `b` transformation/posterior. EB's `ItemParameterState.b_mean` is
  item-response state, **not** FSRS D.
- **FSRS**: `practice_item_state.difficulty`, `activity_card_state.difficulty`, `family_memory_state.difficulty`
  and their `MemoryState`/rollout representations. All three persisted columns stay.
- **Metadata**: labels/toggles/writers that name the field without consuming its numerical value.

Paths below are relative to `src/learnloop/`, except the explicitly named sidecar paths.

### Scalar readers and their uses

| File | Function(s) | Read / purpose |
|---|---|---|
| `learner/mastery.py` | `item_irt_params` | Scalar: item label, then LO prior, then configured default; map to bounded IRT `(a,b)`. |
| `adaptive_difficulty/data_check.py` | `data_check` | Scalar: correlate the stored item label with unassisted correctness. |
| `adaptive_difficulty/serve_inputs.py` | `_z_llm` | Scalar: map label to AD's `z_llm` input/receipt. |
| `adaptive_difficulty/replay.py` | `_historical_signals` | Scalar: reconstruct historical `z_llm`. |
| `content/authoring/exercise_authoring.py` | `author_exercises` | Scalar: clamp authored entry and copy to item/frontmatter and authoring receipt. |
| `content/authoring/practice_generation.py` | `_check_difficulty_band` | Scalar: validate generated payload against requested band. |
| `content/authoring/rung_variants.py` | `audit_variant_direction`, `_variant_kind`, `_variant_instructions` | Scalar: direction/held-axis audit, variant classification and source-label prompt. |
| `diagnosis/causal_probe_coherence.py` | `_item_diff` | Scalar: compare source and candidate instrument labels. |
| `diagnosis/contrast_pairs.py` | `judge_pair`, `_payload_of` | Scalar: pair band checks, judge receipt and copy item to payload. |
| `diagnosis/probe_remint.py` | `_remint_payload` | Scalar: preserve source label in remint payload. |
| `field/outcomes.py` | `_load` | Scalar: mark missing/LLM-label uncertainty; gets `b` through the seam (below). |
| `field/probability_states.py` | `item_view` | Scalar: explain the authored/measured prior, without using FSRS state. |
| `goals/exam_pool.py` | `_difficulty_stratum` | Scalar: stratify held-out pool. |
| `instructional/tools.py` | `_practice_view` | Scalar: serialize label in tool result. |
| `teacher/actions.py` | `find` | Scalar: forward the tool-result field using a literal-key comprehension. |
| `ops/pf_generation.py` | `_candidate_from_row`, `_finalize_difficulty`, `_write`, `_select`, `_resumable_job`, `_plan_resume` | Scalar: decode candidate, panel-derived offset from parent, publication, selection receipt and resume transport. |
| `ops/pf_publish.py` | `build_item_payload` | Scalar: copy candidate value/provenance to published item. |
| `practice_index/retrieval.py` | `_base_matches` | Scalar: min/max index filters. |
| `substrate/surface_mint.py` | `_within_difficulty_bounds`, `run_all_gates` | Scalar: read candidate label and declared bounds for authoring gate. |
| `tutor/teach_back.py` | `ensure_teach_back_item` | Scalar: copy source label, keeping existing 0.6 fallback. |
| `vault/hashes.py` | `practice_item_hash` | Scalar: **frozen hash input**; same stored key and value permanently. |
| `learnloop_sidecar/handlers/facets.py` | `get_facet_mastery` | Scalar: facet-map DTO. |
| `learnloop_sidecar/handlers/knowledge_map.py` | `get_knowledge_map` | Scalar: knowledge-map DTO. |
| `learnloop_sidecar/handlers/serializers.py` | `practice_item_detail`, `learning_object_detail` | Scalar: existing item/LO DTO fields. |
| `tui/screens/practice.py` | `PracticeScreen._difficulty` | **Both, existing crossing H1-1**: item scalar → FSRS D → LO scalar prior → 0.5. Display only; unchanged. |

### Item-parameter callers (scalar/IRT path)

Every call is also pinned by the guard. `resolve_item_irt_params` lives in `learner/mastery.py` and returns
`tuple[float, float] = (a, b)`. Static fallback: `a = discrimination_default`; if prior use is enabled, use item
scalar, else LO scalar, mapped by `difficulty_prior_scale * (d - 0.5) * 2` and clamped; otherwise/default use
`difficulty_default`. EB replaces only `b` with bounded `item_state.b_mean` when enabled **and** supplied.

| File | Function | What it uses `(a,b)` for | Disposition |
|---|---|---|---|
| `diagnosis/probes.py` | `resolve_item_irt` | Probe response probabilities/EIG | **Moved**, no posterior argument. |
| `daily_plan/lesson_suggestion.py` | `_predicted` | LO unassisted-success prediction | **Moved**, item is None. |
| `scheduling/selection_rewards.py` | `item_demand_vector` | Reward demand vector's IRT terms | **Moved**, no posterior argument. |
| `teacher/brief.py` | `lo_prediction` | LO prediction, interval and display words | **Moved**, item is None. |
| `teacher/checks.py` | `cold_reference` | Retention-forecast item's fixed parameters | **Moved**, no posterior argument. |
| `teacher/checks.py` | `check_mass` | Check sensitivity and pool-implied evidence mass | **Moved**, no posterior argument. |
| `learner/lesson_weight.py` | `recorded_trajectory`, `_outcome_item_params` | Reconstruct intervening and resolving response curves from current content | **Left static**, L4-2 (above). |
| `attempts/attempts.py` | `_belief_update` | Authored mean for EB prior initialization | **Left static**, prior must not become posterior. |
| `learner/mastery.py` | `resolve_item_irt_params` | Static fallback underneath EB seam | **Left static**, seam implementation. |
| `attempts/attempts.py` | `_grade_evidence` | Mastery and surprise; EB posterior supplied, priming offset applied afterwards | Already seam; unchanged. |
| `delayed_checks.py` | `predicted_item_success` | Cold-item choice prediction; EB posterior supplied | Already seam; unchanged. |
| `placement/predictor.py` | `_item` | Placement prediction; cached item-parameter posterior supplied | Already seam; unchanged. |
| `scheduling/scheduler.py` | `_practice_information` | Practice information prediction | Already seam, no posterior; unchanged. |
| `adaptive_difficulty/forecasters.py` | `_features` | Incumbent features; omit LLM-estimated label | Already seam, no posterior; unchanged. |
| `field/outcomes.py` | `_load` | Historical incumbent features; omit LLM-estimated label | Already seam, no posterior; unchanged. |

`field/predictors.py` and `field/success_head.py` consume already assembled IRT features (`a`, `b`); they do not
read an item's scalar directly. H3's list includes these downstream consumers, not additional direct label reads.

### FSRS readers and their uses

| File | Function(s) | Read / purpose |
|---|---|---|
| `scheduling/fsrs.py` | `apply_review`, `next_difficulty`, `next_forget_stability`, `next_recall_stability` | FSRS: previous D and local D parameters for the memory update/stability formulae. |
| `scheduling/family_memory_model.py` | `FamilyMemory.observe`, `snapshot_bytes` | FSRS: retain D while adjusting stability for family credit; encode replay-history state. |
| `substrate/card_lineage.py` | `rebuild_card_state` | FSRS: replayed `MemoryState.difficulty` into `activity_card_state`. `fork_card` accepts an informed FSRS prior (not the old item scalar). |
| `substrate/family_memory.py` | `rebuild_family_memory` | FSRS: replayed family D into `family_memory_state`; it is not an item-label lookup. |
| `db/stores/practice_state.py` | `_practice_item_state`, `_record_attempt_practice_item_state`, `_upsert_practice_item_state_record` | FSRS: decode persisted D and copy state D into writes. `practice_item_state(s)` call the decoder. |
| `attempts/attempts.py` | `grade_application`, `_fsrs_review_summary`, `_memory_state` | FSRS: persist review memory, report old/new D and convert stored state to `MemoryState`. |
| `content/proposals/patches.py` | `_apply_reject_side_effect` | FSRS: retain memory while marking a rejected item inactive. |
| `daily_plan/objective_inputs.py` | `_practiced`, `build` | FSRS: SQL reads D into `d`, then median topic D initializes objective memory, default 5.0. |
| `router_objective/decision_state.py` | `_item_rows` | FSRS: SQL reads and rounds D for decision receipt. |
| `router_objective/rollouts.py` | `initial` | FSRS: `Topic.difficulty` into vectorized rollout `d`. |
| `router_objective/memory.py` | `Fsrs.review` | FSRS: local difficulty array in vectorized review update, no scalar lookup. |
| `learnloop_sidecar/handlers/serializers.py` | `practice_item_state_dto` | FSRS: state DTO, distinct from item/LO scalar DTOs in the same module. |
| `tui/screens/practice.py` | `PracticeScreen._difficulty` | FSRS D incorrectly used as scalar display fallback; H1-1 above. |

### Transport, declarations and false positives

These are included in the audit/record to avoid treating every `difficulty` token as a numerical model input.

| File | Function / declaration | Kind and purpose |
|---|---|---|
| `db/stores/activity.py` | `activity_card_state`, `upsert_activity_card_state` | FSRS: generic `SELECT *`/dict transport and pass-through writer for activity memory. No scalar read. |
| `db/stores/pf.py` | `_CANDIDATE_COLUMNS`, `candidate`, `candidates`, `insert_candidate`, `update_candidate` | Scalar: generic candidate row transport/writing. |
| `substrate/shadow_rebuild.py` | `_PROJECTION_SPECS`, `_learner_state_snapshot` | FSRS: compare named `difficulty` fields for practice/activity schedule projections. |
| `substrate/card_lineage.py` | `SEMANTIC_COMPONENTS`, `classify_edit`; `fork_card` | Scalar: contract difficulty is a semantic edit axis; separately, fork takes a supplied FSRS prior. |
| `vault/writer.py` | `LEARNING_OBJECT_ORDER`, `PRACTICE_ITEM_ORDER` | Scalar: field ordering for generic YAML writer; names stay. |
| `vault/models.py`, `db/records.py`, `router_objective/types.py` | `LearningObject`, `PracticeItem`, `PracticeItemState`, `ItemParameterState`, `Topic` | Persisted/content/receipt fields stay; `b_mean` is EB IRT, `Topic.difficulty` is FSRS. |
| `content/authoring/ai_contracts.py`, `content/proposals/ai_contracts.py` | Authoring/proposal fields and prompt contracts | Scalar writers/schema, no label read; no prompt or field renamed. |
| `curriculum/golden_path_fixture.py` | `_practice_item`, `_seed_vault` | Scalar: synthetic authored values only. |
| `learner/recall_calibration.py` | `_fresh_calibration_vault` | Scalar: synthetic authored calibration item only. |
| `followup_run/admission.py` | `SYSTEM_AXES` | Scalar: system-owned instrument axis name, no numerical reader. |
| `field/item_content.py` | `load_content_index` | Metadata: solver-panel feature coverage under the `difficulty` key. |
| `field/success_head.py` | `LogisticHead.__init__`, `_explicit`, `covers`, `_prior` | Metadata toggle `self.difficulty`/coefficient key controlling solver-panel IRT `b`; identity dump retains its name. |
| `cli/success_head.py` | `success_head_eval` | Metadata: solver-panel difficulty feature coverage flag. |

Also checked: `practice_generation`/`promotions` band inversion and `pf_generation.panel_difficulty` transform
supplied probabilities/config scales into scalar labels; they do not read either persisted D column. Whole-model
serialization/hashing continues carrying the stored fields unchanged. `difficulty_rating` (learner's tap), AD model
parameters, `historical_difficulty_prior` and prose about desirable difficulty are not either of these fields.

## Naming and scope

`item_irt_params`'s local `difficulty` is now `scalar_difficulty`; its docs, the EB seam/update docs, the mastery
module explanation and the probe-response docs explicitly say scalar/IRT or FSRS. Existing `difficulty_b`, `item_b`
and `b_mean` already identify IRT b; none became FSRS D. No FSRS implementation needed editing to route the scalar
callers. Nonpersisted `ItemDemandVector` has `as_dict()` output and the mastery trace feeds DTOs, so their existing
`difficulty_b` fields remain. No database column, model field, config key, frontend DTO, prompt or compared dump
was renamed. `CLAUDE.md`, refactor status and vault references were not edited.

## Literal no-value-change proof

Before editing any production file, a new test harness invoked the **unchanged** caller functions at the base
with literal inputs and printed their results. `t.sh tests/test_difficulty_kinds_apart.py -q -n 0 -s` reported
`3 passed in 0.94s`. Those printed Python values were parsed with `ast.literal_eval` and inserted as literal
`EXPECTED` dictionaries; no expected value was computed from the new seam. Before routing edits, the resulting
24 caller/case assertions plus the bug characterization reported `24 passed, 1 xfailed in 2.00s` with `-n 2`.
After routing, all 24 assert **exact Python equality**, including floating-point representations.

All cases use `MasteryConfig()` and assert `eb_difficulty_enabled is False` (not overridden). Learner mean 0.4,
variance 0.3; item-parameter posterior deliberately disagrees (`b_mean=-3.0`); FSRS state D deliberately disagrees
(`difficulty=9.0`). The three cases are item scalar 0.8/LO prior 0.2; absent item scalar/LO prior 0.2; both absent.

| Output | Item 0.8, LO 0.2 | Item absent, LO 0.2 | Both absent |
|---|---:|---:|---:|
| Probe `(a,b)`; demand `(a,b)`; cold-reference `(a,b)`; seam `(a,b)` | `(1.0, 1.5000000000000002)` | `(1.0, -1.5)` | `(1.0, 0.0)` |
| Suggestion predicted success (LO only) | 0.8577942484315435 | 0.8577942484315435 | 0.5934713636269644 |
| Brief `p`; `item_b`; interval | `0.8578; -1.5; [0.6956,0.9514]` | `0.8578; -1.5; [0.6956,0.9514]` | `0.5935; 0.0; [0.3377,0.8136]` |
| Check learned mass | 0.5 | 0.5 | 0.5 |
| Check applied mass (with teacher retention 0.65) | 0.9999938558253978 | 6.144174602214718e-06 | 0.7996425075277717 |
| Check pool `p_a` | 0.2822500859661234 | 0.8598870147006229 | 0.6071010703748768 |
| Check pool target | 0.34868439980135435 | 0.8219707589179596 | 0.6148507960584249 |
| Existing delayed-item predicted success | 0.26106893902450123 | 0.8577942484315435 | 0.5934713636269644 |

Check sensitivity `(a,b)` matches the item-based row above; the pool's lambda is 0.18065079365079373 in all cases.
Cold reference's horizon is 3.0 (`legacy`). Brief words and remaining brief fields, and reference metadata, are
also compared as literal dictionaries. Only storage/history/eligibility/time-horizon dependencies are replaced
in the test; it calls the actual six moved functions and actual parameter/probability/mass calculations.

## Guard and its negative proof

`tests/test_difficulty_kinds_apart.py::test_difficulty_readers_keep_scalar_and_fsrs_apart` scans all Python under
`src/`. `AUDITED_READERS` covers 54 modules / 161 sites and gives a reason and exact `(function, expression)` counts per named module. It recognizes
loaded `.difficulty`/`.difficulty_prior`, `getattr`, mapping `.get`/subscripts, literal field names (including
comprehension column lists), SELECT text naming the columns, and calls to either IRT helper. Replacing the source
expression fails even if the count stays the same; a new module or new reader in an existing module fails. It
intentionally includes mixed adapter modules, metadata false positives and the known H1-1 exception explicitly.

This is a source ratchet, not Python type inference: variable rebinding, dynamic field construction, unrecognized
reflection, or passing an entire record under the same spelling still needs review. It does not prove replay inputs
were frozen (L4-2), or that every existing audited use is desirable.

Three scratch roots under `/tmp/h1-crossing-{scalar,fsrs,unlisted}` held copies of the guard and one mutated source
file; other Python sources were symlinked read-only in effect (only read by the scan) to this checkout. No mutation
was left in the checkout. The scalar scratch added `return memory.difficulty` in `learner/mastery.py`; the FSRS
scratch added `return item.difficulty` in `scheduling/fsrs.py`; the third added a new `h1_unaudited_reader.py`.
The three targeted guard nodes initially returned **3 failed in 10.12s**; they were repeated against the final guard (result below). Relevant failure text:

```text
E AssertionError: Unaudited scalar/FSRS readers (audit kind and reason): {'src/learnloop/learner/mastery.py': {'new': {'_crossing: memory.difficulty': 1}, 'removed': {}}}
E AssertionError: Unaudited scalar/FSRS readers (audit kind and reason): {'src/learnloop/scheduling/fsrs.py': {'new': {'_crossing: item.difficulty': 1}, 'removed': {}}}
E AssertionError: Unaudited scalar/FSRS readers (audit kind and reason): {'src/learnloop/h1_unaudited_reader.py': {'new': {'_crossing: item.difficulty': 1}, 'removed': {}}}
```

## Verification commands

Commands run from the worktree. `T` means
the step's scratch wrapper `t.sh`;
`P` is `py.sh` in that directory. These wrappers supply an empty HOME/CODEX_HOME/config directory. No network
or model calls. Pytest runs use explicit files/nodes, at most two workers; neither the full suite nor arc-close
simulations was requested or run. The requested filename search matched 58 test files (including the new file),
partitioned into 40 and 18; there were no files named `lesson_weight`, `lesson_suggestion` or `delayed_check` at this
tip. Their real owners (`teacher_te1_weight`, `teacher_te1b_suggestions`, `data_capture_a6_delayed_pick`) were also
selected separately.

Chunk 1 (explicit files):

```sh
T \
  tests/test_adaptive_difficulty_ad1.py \
  tests/test_causal_probe_commissioning.py \
  tests/test_certification_cold_probe.py \
  tests/test_characterization_mastery_reliability.py \
  tests/test_characterization_probe_family_em.py \
  tests/test_characterization_probe_regrade.py \
  tests/test_characterization_probe_replay.py \
  tests/test_characterization_probe_submission.py \
  tests/test_diagnostic_probe_freshness.py \
  tests/test_diagnostic_probe_single_use.py \
  tests/test_diagnostic_probe_value.py \
  tests/test_difficulty_band_guards.py \
  tests/test_difficulty_kinds_apart.py \
  tests/test_followup_fg1d_probe_shadow.py \
  tests/test_followups_batch6_power_probe_cache.py \
  tests/test_irt_difficulty.py \
  tests/test_irt_end_to_end.py \
  tests/test_mastery.py \
  tests/test_mastery_step_attribution.py \
  tests/test_mobile_v3_probes.py \
  tests/test_placement_opening_probes.py \
  tests/test_probe_attempt_updates.py \
  tests/test_probe_audit.py \
  tests/test_probe_belief_posterior.py \
  tests/test_probe_block_end.py \
  tests/test_probe_coverage.py \
  tests/test_probe_dialogue.py \
  tests/test_probe_eig.py \
  tests/test_probe_entry.py \
  tests/test_probe_episode_conflict_one_check.py \
  tests/test_probe_episodes.py \
  tests/test_probe_facts.py \
  tests/test_probe_hierarchy.py \
  tests/test_probe_instance_generation.py \
  tests/test_probe_lifecycle.py \
  tests/test_probe_llm_instances.py \
  tests/test_probe_longform_families.py \
  tests/test_probe_migration.py \
  tests/test_probe_observation_admission_readers.py \
  tests/test_probe_orchestration_remainder.py \
  -q -n 2 -m "not arc_close"
```

Chunk 2 (explicit files):

```sh
T \
  tests/test_probe_policy.py \
  tests/test_probe_pool_empty.py \
  tests/test_probe_predictive_eig.py \
  tests/test_probe_proposal_reads.py \
  tests/test_probe_records.py \
  tests/test_probe_remint.py \
  tests/test_probe_robust_cutover.py \
  tests/test_probe_router_authority.py \
  tests/test_probe_router_report.py \
  tests/test_probe_surface_mint.py \
  tests/test_probe_targeting.py \
  tests/test_project_probes.py \
  tests/test_router_probe_ties.py \
  tests/test_scheduler_probe_eig.py \
  tests/test_sidecar_probe.py \
  tests/test_sim_probe_validation.py \
  tests/test_sim_probe_validation_cli.py \
  tests/test_teacher_te2_probes.py \
  -q -n 2 -m "not arc_close"
```

Other exact verification commands (result lines below):

```sh
T tests/test_difficulty_kinds_apart.py -q -n 0 -s
T tests/test_difficulty_kinds_apart.py -q -n 2
T tests/test_identity_pins.py tests/test_retired_config_identities.py tests/test_diagnosis_journey_golden.py tests/test_structure_ratchets.py tests/test_effective_defaults_golden.py tests/test_kill_switches.py -q -n 2 -m "not arc_close"
T /tmp/h1-crossing-scalar/tests/test_difficulty_kinds_apart.py::test_difficulty_readers_keep_scalar_and_fsrs_apart /tmp/h1-crossing-fsrs/tests/test_difficulty_kinds_apart.py::test_difficulty_readers_keep_scalar_and_fsrs_apart /tmp/h1-crossing-unlisted/tests/test_difficulty_kinds_apart.py::test_difficulty_readers_keep_scalar_and_fsrs_apart -q -n 2 --import-mode=importlib
P ruff check
P lint-imports --no-cache
git diff --check
```

The original 40-file chunk stopped reporting progress after 354 completed cases (no reported failures) and was
interrupted with Ctrl-C, exit 130, without a pytest summary. A rerun of just `test_mobile_v3_probes.py` with
`-o faulthandler_timeout=45` completed eight cases then showed both workers waiting in fixture setup:

```text
Timeout (0:00:45)!
... anyio/_backends/_asyncio.py ... run_sync_from_thread
... starlette/testclient.py:516 in __enter__
... tests/mobile_v2_plan_helpers.py:63 in plan_world
```

That diagnostic run was also interrupted (exit 130). The other 39 files were rerun together and passed.
For a base-code check, `/tmp/h1-baseline-src` held the six changed production files from `git show HEAD:<path>`;
other Python files were symlinked to the worktree. `-o pythonpath=/tmp/h1-baseline-src` selected that baseline
without altering production files in the checkout. The first overlay attempt lacked packaged static assets
(`1 error in 2.98s`, missing `pair.html`); the second used a static-directory symlink rejected by the asset guard
(`1 error in 2.25s`, `SchemaMismatch: Packaged assets must not be symlinks`). Copying only the two project-authored
`pair.html`/`pair.js` files as ordinary scratch files corrected the overlay. The base-code run then waited at the
same `TestClient.__enter__` / `plan_world:63` fixture setup, dumped its stack at 30 seconds and was interrupted,
exit 130. This establishes the setup stall on unchanged production code; it does not verify the mobile tests.
No test infrastructure fix or additional product-bug ledger row was inferred from a sandbox setup stall.

## What was not verified

`test_mobile_v3_probes.py` did not finish: setup stall reproduced with base production files as above.
No private-vault P-shadow, P-draw, owner-vault tests, full suite, `--fresh-connections` arc-close run, durability
lane, arc-close simulations, vault-reference validators or four-way replay. No persisted behavior is intentionally
changed; these local checks do not replace the orchestrator's landing gate. EB-on behavior is structurally preserved
by supplying no new posterior to moved callers, but the new literal characterization specifically proves the
required default-off cases. No claim is made to fix historical reconstruction, the scalar display bug, or the
usefulness of the existing authored difficulty signal.

## What H2 needs

- Owner-supplied backup-API copies and permission for owner-side replay; private metrics stay untracked.
- Four arms at this exact behavior baseline: today; `mastery.irt.difficulty_from_prior=false`; AD
  item-conditioned surprise; both changes. Keep FSRS D separate throughout, retaining its schedule/rollout role.
- Report mastery, surprise, due dates, queue and AD scoring with `z_llm` removed. Preserve the same frozen inputs,
  config/tag and completed draws for meaningful comparisons. The inventory above is the reader checklist.
- For cold AD items use its population predictive, else structural `difficulty_default=0` (no label), never
  a per-item manual replacement label.
- Surface L4-2 explicitly: current authored parameters, recorded attempt-time parameters, EB posterior and priming
  offset are different inputs. H2 must not silently repair reconstruction or present today's content as a frozen
  replay capsule; the recorded-input correction belongs to L4.4.
- The owner decides whether AD may feed a stored surprise row under the A2/A12 firewall. If disallowed, use EB b
  or the structural default and drop that arm as specified. H2 adds its script/report and no production changes.

The successful 39-file retry, expanded exactly:

```sh
T \
  tests/test_adaptive_difficulty_ad1.py \
  tests/test_causal_probe_commissioning.py \
  tests/test_certification_cold_probe.py \
  tests/test_characterization_mastery_reliability.py \
  tests/test_characterization_probe_family_em.py \
  tests/test_characterization_probe_regrade.py \
  tests/test_characterization_probe_replay.py \
  tests/test_characterization_probe_submission.py \
  tests/test_diagnostic_probe_freshness.py \
  tests/test_diagnostic_probe_single_use.py \
  tests/test_diagnostic_probe_value.py \
  tests/test_difficulty_band_guards.py \
  tests/test_difficulty_kinds_apart.py \
  tests/test_followup_fg1d_probe_shadow.py \
  tests/test_followups_batch6_power_probe_cache.py \
  tests/test_irt_difficulty.py \
  tests/test_irt_end_to_end.py \
  tests/test_mastery.py \
  tests/test_mastery_step_attribution.py \
  tests/test_placement_opening_probes.py \
  tests/test_probe_attempt_updates.py \
  tests/test_probe_audit.py \
  tests/test_probe_belief_posterior.py \
  tests/test_probe_block_end.py \
  tests/test_probe_coverage.py \
  tests/test_probe_dialogue.py \
  tests/test_probe_eig.py \
  tests/test_probe_entry.py \
  tests/test_probe_episode_conflict_one_check.py \
  tests/test_probe_episodes.py \
  tests/test_probe_facts.py \
  tests/test_probe_hierarchy.py \
  tests/test_probe_instance_generation.py \
  tests/test_probe_lifecycle.py \
  tests/test_probe_llm_instances.py \
  tests/test_probe_longform_families.py \
  tests/test_probe_migration.py \
  tests/test_probe_observation_admission_readers.py \
  tests/test_probe_orchestration_remainder.py \
  -q -n 2 -m "not arc_close"
```

Additional verification commands:

```sh
T tests/test_mobile_v3_probes.py -q -n 2 -m "not arc_close" -o faulthandler_timeout=45
# Run three times during overlay preparation, with the outcomes described above.
T tests/test_mobile_v3_probes.py::test_the_desktops_serving_next_moves_past_a_probe_the_phone_served_and_abandons_it -q -n 1 -m "not arc_close" -o pythonpath=/tmp/h1-baseline-src -o faulthandler_timeout=30
T tests/test_item_parameters.py tests/test_grade_application_core.py tests/test_scheduler.py tests/test_teacher_te1_weight.py tests/test_teacher_te1b_suggestions.py tests/test_data_capture_a6_delayed_pick.py tests/test_fsrs.py tests/test_fsrs_fitting.py tests/test_family_memory_projection.py tests/test_card_lineage.py -q -n 2 -m "not arc_close"
T tests/test_test_layout.py -q -n 1
T tests/test_architecture.py -q -n 1
```

Result lines (repeated checks are recorded too; expected mutation failures are separate from product failures):

| Command / run | Result line |
|---|---|
| Baseline literal capture, `T tests/test_difficulty_kinds_apart.py -q -n 0 -s` | `3 passed in 0.94s` |
| Baseline literal pins, `T tests/test_difficulty_kinds_apart.py -q -n 2` | `24 passed, 1 xfailed in 2.00s` |
| Post-routing proof with initial guard, same `-q -n 2` command | `25 passed, 1 xfailed in 6.66s` |
| Six-file pin/golden/ratchet/kill-switch command | `397 passed in 20.94s` |
| Initial scratch guard mutation command | `3 failed in 10.12s` (expected; three crossing reads rejected) |
| Final scratch guard mutation command (same three nodes) | `3 failed in 10.35s` (expected; final guard rejects all three) |
| Final standalone proof, `T tests/test_difficulty_kinds_apart.py -q -n 2 -rx` | `25 passed, 1 xfailed in 6.57s` |
| Requested chunk 1, 40 files | Interrupted, exit 130; no pytest summary; no reported failures before the setup stall |
| Mobile-only diagnostic, timeout 45 | `Timeout (0:00:45)!`; interrupted, exit 130 |
| Base-code mobile node, overlay missing assets | `1 error in 2.98s` (scratch preparation error) |
| Same base-code node, overlay asset symlink | `1 error in 2.25s` (scratch preparation error) |
| Same base-code node, ordinary copied assets | `Timeout (0:00:30)!`; same fixture setup stall; interrupted, exit 130 |
| Chunk 1 retry, 39 files without mobile | `365 passed, 1 xfailed in 23.48s` |
| Requested chunk 2, 18 files | `163 passed, 2 skipped in 32.41s` |
| Ten additional caller/FSRS files | `141 passed in 7.88s` |
| Layout alone, `T tests/test_test_layout.py -q -n 1` | `3 passed in 19.10s` |
| Architecture alone, `T tests/test_architecture.py -q -n 1` | `18 passed in 29.87s` |
| `P ruff check` (initial, after guard expansion, final) | `All checks passed!` each time |
| `P lint-imports --no-cache` (initial and final) | `Contracts: 43 kept, 0 broken.` each time |
| `git diff --check` (repeated after edits) | exit 0, no output |

The two skips are `test_probe_policy.py`'s conditional skips when an episode has already completed after one
observation; its penalty/repeated-response assertions then cannot be observed. The sole xfail is H1-1. None of
the identity-pin, retired-config identity, journey/default golden or kill-switch tests failed or was regenerated.
All 58 requested matching files were attempted, but only the 57 non-mobile files have a completed local result.

Final checkout check: `git diff --check` exits 0; only the nine intended files are changed/new. No `git add` or `git commit` was run.
