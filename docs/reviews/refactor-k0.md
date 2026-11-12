# Refactor K0: identity pins

Branch `refactor/k0-identity-pins`, based on `ad194ddc3a` (arc C closed). Step K0 of arc K
(`docs/specs/refactor_strategy_v3.md` §2.17), designed by the serialization sweep of Nov 11 (orchestrator scratch,
`serialization-sweep-2026-11-11.md`; its ids A1-A22, B1-B12, C1-C6 are used below). Arc C's review found a
deletion that moved a compared hash: C3 removed the unread `merge_locked_facets`, and canonical synthesis's
manifest hash, the completed-run cache key, moved with it. A deletion proof follows imports and names; a whole
`model_dump` inside a hash reads every field without naming one. K0 makes such a move fail a test.

Rules held: no change at any fixed input (every pin recorded before the fix is unchanged after it), no live model
call, no migration, no `algorithm_version` change.

## 1. What landed

| File | What |
| --- | --- |
| `tests/identity_pins_helpers.py` | The fixed inputs, `IDENTITY_SITES` (one entry per compared identity: production functions, consumer, consequence, pins), `SHAPE_ROOTS`, `PROVENANCE_ONLY` |
| `tests/goldens/identities.toml` | 134 pins, one sha256 each, generated |
| `tests/goldens/identity_shapes.toml` | 58 types: field, annotation, default (and retired fields), with the sites that dump each |
| `tests/test_identity_pins.py` | The pins, the shape pins, the AST coverage check; `--write` regenerates both goldens |
| `src/learnloop/config/retired.py` | `identity_view(model, fields)`: the named fields of `identity_dump` |
| `src/learnloop/content/facet_identity/judge.py` | `manifest_identity` (extracted), `MANIFEST_CONFIG_FIELDS`, `JudgeRoute.as_dict` names the price fields |
| `src/learnloop/content/synthesis/graph_nomination.py` | `IDENTITY_CONFIG_FIELDS`; the identity's config through `identity_view` |
| `src/learnloop/content/synthesis/synthesis_manifests.py` | `task_graph_hash` dumps blueprints through `_BLUEPRINT_IDENTITY_FIELDS` |
| `src/learnloop/content/synthesis/source_set_synthesis.py` | `bootstrap_scope` (extracted) |
| `src/learnloop/content/synthesis/source_append.py` | uses `manifest_identity` |
| `src/learnloop/daily_plan/lesson_suggestion.py` | `draw_inputs` (extracted: what the day's draw seed hashes) |
| `src/learnloop/config/schema.py` | `GraphNominationConfig` keeps retired fields like the other identity-dumped sections |
| `CLAUDE.md`, `docs/algorithm-change-playbook.md`, strategy D7 and H6 rows | the rule, where a reader meets it |

Regenerate: `uv run python tests/test_identity_pins.py --write`, only with a deliberate bump.

## 2. Fixed inputs

- **Configs.** `init`: `learnloop init`'s template (`DEFAULT_CONFIG_TEXT`, tag mvp-0.58, so every successor's
  switches are in the keys); `legacy`: arc C's `LEGACY_TOML` (every retired key set) plus a non-default value in
  each section a compared identity dumps whole (`facet_identity.max_cost_usd`, `graph_nomination`,
  `mastery.irt.difficulty_prior_scale`, `router.epsilon_min`) and `embedding.enabled = true` so the graph
  nominator's identity is in the synthesis scope; no `[algorithms]`, so the bare default tag (mvp-0.6) pins every
  "below the tag the key keeps its predecessor's bytes" branch. Both are built as `load_config` builds them
  (`normalize_config_input`, then validation) without the environment.
- **Vault.** A `LoadedVault` built in memory (root `/identity-pins/vault`, never opened): one LO with a blueprint
  whose recipe has `all_of`, `any_of`, `integration` and an authored key no model declares; two items of that LO
  (the first with every rubric and contract field set, a trace and variant contract, hint policy, fingerprint,
  required method); two facets (one with every field set, one with most at their defaults); a concept, an error
  type, a family and a goal with a facet scope and exam. Vault models keep unknown keys (`extra="allow"`), so a
  field removed from one stays in the dump of an input that set it: the defaulted inputs and the shape pins cover
  removals.
- **Clients and stores.** A fake structured client (name, model, profile from the init config); the graph
  nominator gets a repository whose database path does not exist (`no_database`, deterministic); placement gets a
  repository with no states.

Nothing is read from a template vault or another test's fixtures, so a change elsewhere in the tests never moves a
pin.

## 3. Sites pinned (134 pins)

Each pin calls the production function. Where production assembles an identity inline from production pieces,
the pin does the same and the table says so.

### 1A. Paid generation and judgment reuse (55 pins)

| Id | Production path | What feeds it | Pins |
| --- | --- | --- | --- |
| A1 | `facet_identity.judge.manifest_identity()["config"]` | `[facet_identity]` with retired fields | init, legacy |
| A2 | `resolve_route(config).as_dict()` | route, profile, price (known, owner, unknown), policy output budget, problem text | 8: subscription (init, legacy), metered known price, unknown price (problem), owner price, Decider, unknown profile (problem), wrong profile type (problem) |
| A3 | `GraphNominator.for_ingest(...).identity(prompt_version=...)` | `[graph_nomination]`, embedding model and dims, route, registry index digests | legacy (embedding on) |
| A1-A4 | `source_set_synthesis.bootstrap_scope`, `synthesis_manifests.build_manifest` | the whole bootstrap scope and manifest hash (`agent_run_input_context_hash` is the manifest hash) | scope and manifest hash, init and legacy |
| A4 | `synthesis_manifests.task_graph_hash(vault)` | blueprint dumps, item task shape | fixed vault |
| A6 | `pf_calls.planned_role_clients` settings + `PFCaller.input_hash` | whole provider profile, prompt, `SkeletonResult` schema | skeleton (openrouter), freshness (deepseek) |
| A7 | `family_proposals._settings` + `pair_passes` judgment ids | whole profile; whole items and rubric in the prompt | the pair |
| A8 | `contamination.judge.judge_settings` + `build_requests` judgment ids | whole profile, judge revision, output budget | one candidate |
| A9 | `feature_audit.item_revision(item)` | whole `PracticeItem` dump | item |
| A10 | `embedding_recipes.facet_content_hash(facet)` | whole `EvidenceFacet` less provenance and fingerprint | full facet, defaulted facet |
| A11-A12 | `MapSeeds.structure_hash`, `map_builder.build_prompt(seeds)` | trace contract dump, skeletons, rubric, hints; required method in the prompt | structure hash, prompt |
| A13 | `canonical_ingest_prompt(CanonicalIngestContext(...))` | `asdict(context)` (the window key hashes this prompt with the `AuthoringProposal` schema, A20) | prompt |
| A14 | `source_set_synthesis_prompt` + `_synthesis_pass_key` | `asdict(context)`, schema, `model_settings` | with and without the facet rule |
| A15 | `source_unit_inventory.inventory_window_key` | `asdict(context)` in the prompt, settings | window key |
| A19 | `families.family_item_input_hash`; `ActivityFamily.model_dump` and `vault.hashes.activity_family_hash`; `pf_publish.judged_inputs` | whole item and rubric; the family plan; the publish judgment's inputs | item, family, publish judged inputs |
| A20 | `Model.model_json_schema()` for the 18 result models the sweep's schema-keyed sites use; `practice_index.paid.checkpoint_key` | the schema in a checkpoint or input hash | 18 schemas, one checkpoint key |
| A22 | `ai.execution.model_settings(client)` | six chosen profile attributes | openrouter, chatgpt_medium, deepseek_flash, and openrouter with every attribute set (the silent-`None` case) |

### 1B. History interpretation, dedupe and staleness (14 pins)

| Id | Production path | What feeds it | Pins |
| --- | --- | --- | --- |
| B1-B3 | `compile_assessment_contract` (its `rubric_content_hash`), `contract_hash`, `card_contract_hash` (practice and assessment), `fingerprint_of` | whole rubric, trace and variant contract, fingerprint | 3 |
| B4-B5 | `vault.hashes.reference_content_hash`, `practice_item_hash` | rubric, hint policy, required method | 2 |
| B6 | `proposals.patches.compute_target_hash` for all six entity types | `exclude_none=False` dumps | 6 |
| B7 | `goal_contracts._yaml_subset_from_goal` | `GoalFacetScope` and `GoalExamConfig` dumps, narrowed by `canonicalize_body` (§8) | 1 |
| B9 | `controller_snapshot._controller_param_manifest_hash`, `constraint_engine.manifest()["manifest_hash"]` | registry entries owned by the controller modules; constraint definitions | 1 |
| B10 | `learnloop_mobile.allowlist.allowlist_digest()` | method name, kind, retry policy, API version (an intended coupling: the message says rebuild the PWA) | 1 |

### 1C. Version identities and seeds (65 pins)

| Id | Production path | What feeds it | Pins |
| --- | --- | --- | --- |
| C1 | `LiveMasteryPredictor(...).version_hash` | `identity_dump(config.mastery)` | init, legacy |
| C2 | `create_predictor(name, config=mastery).version_hash` for the 21 registered predictors; `LogisticHead` (plain, difficulty+moderated); `AnswerSignalArm` (confidence, hedging) | `asdict(ArmConstants)`, `asdict(HeadPriors)`, the mastery view | 25 arms x 2 configs |
| C2p | `probability_arms.position_key(features, history)` | `asdict(ItemFeatures)`: the cached LLM probabilities' key | 1 (found by the AST check; not in the sweep) |
| C3 | `router_chooser.router_settings(config)`; `numeric_seed` and the boundary key `_hash` over an objective block's identity | whole `RouterWeights`; the identity literal is assembled as `ObjectiveChooser` does, from `router_settings`, `objective_settings` and a fixed state and support | settings and boundary, init and legacy |
| C4 | `objective_settings(config)`, `followup_switch_snapshot`, `followup_generator_switches` | the chosen list that is the kill-switch list D7 deletes | init (at the tag), legacy (below it: `None`) |
| C5 | `objective_chooser.generator_now(config[, objective])` | RO6's generator payload with `FOLLOWUP_GENERATOR_SWITCHES` | init, legacy |
| C6 | `lesson_suggestion.draw_inputs` + `LS.canonical_hash` + `LS.seed_for` | whole `RouterWeights`, context and candidate `as_dict` | init, legacy |

## 4. Sites left out, and why

- **A5** (`algorithm_version` in the manifest): intentional; it is in both manifest pins anyway.
- **A16** (`grading_hardcases`), **A17** (`embedding_compare`), **A18** (`experiments/.../callers`): harness or
  experiment keys; re-running re-pays only the harness. A17's config hash is already pinned at arc C's base by
  `tests/test_retired_config_identities.py`. All three are on the AST check's allowlist with that reason.
- **A20 beyond the sweep's list:** about 70 other result models are schema-keyed. A schema moves on a docstring or
  `Field(description=)` edit, which usually means the request changed on purpose; pinning all would make every
  prompt edit fail. The 18 pinned are the ones the sweep names.
- **A21 chosen-field keys** not pinned (`_shard_checkpoint_key`, the Decider judge key, `matching/judge.py`,
  text_gaps, `method_statement_judge`, `field/classification.py`, router teach-back, source retrieval's state
  key, figure request and prefetch hashes, reader requests, `extraction_request_hash`, GLM OCR, PDF extraction,
  `canonical_ingest_context_hash`, unit inventory reuse, embedding vector keys): each names its fields, so a model
  field change cannot move it silently (a renamed attribute it reads raises). A whole dump added to one shows in
  the AST check. Pinned among A21: `_synthesis_pass_key` (A14), `inventory_window_key` (A15),
  `paid.checkpoint_key` (A20), `model_settings` (A22, the one with the silent-`None` hazard).
- **B8** (`causal_probe_coherence` bundle input hash): computed inside a repository write path; its TraceContract
  dump is pinned through A11 and B2 and shape-pinned.
- **B11** (a registry leaf's value hash): one leaf's value, not a dump; `tests/goldens/effective_defaults.toml`
  pins every default.
- **B12** (recurrence's table-name list): reads a database; a change self-heals with one rebuild.
- **1D (provenance only):** report `config_hash` values, `daily_plans.config_hash`, decision-state config hashes,
  agent-run context hashes nothing looks up, extraction result hashes, in-process memos. Where the AST check sees
  one it is on the allowlist with its reason (§6).
- **1E (defaults and additions):** covered by the shape pins (§5) for every type the sweep lists except
  `RolePin` (experiment) and the schema-keyed result models beyond A20's 18 (above).

## 5. Shape pins

`SHAPE_ROOTS` names the 22 types a compared identity dumps whole (sweep §1E): `FacetIdentityConfig`,
`GraphNominationConfig`, `MasteryConfig` (with `MasteryIRTConfig`), `RouterWeights`, `AIProviderConfig` and every
subclass, `Pricing`, `PracticeItem`, `EvidenceFacet`, `LearningObject`, `Blueprint`, `Concept`, `ErrorType`,
`ActivityFamily`, `GoalFacetScope`, `GoalExamConfig`, `ArmConstants`, `HeadPriors`, `ItemFeatures`,
`ReadingTarget` (C3's support rows), and the ingest, synthesis and inventory prompt contexts. Every pydantic model
or dataclass nested in their annotations is pinned too: 58 types. A line per field: name, annotation, default (a factory's value), `exclude_if` when set, the
model's `extra` policy, its retired fields and its subclasses. A failure names the type, the lines gone and new,
and the sites that dump it; it says to regenerate the shapes once every identity pin passes again, so a removal
kept through `RETIRED_FIELDS` regenerates the shape and leaves `identities.toml` alone.

## 6. The AST coverage check

**Rule.** In each function under `src/`, a dump (`model_dump`, `asdict`, `model_json_schema`, or `json.dumps` of
an expression that mentions `config`) whose value reaches the arguments of a sink call (`hashlib.*`,
`content_key`, `content_hash`, `canonical_hash`, `render_structured_prompt`, `build_manifest`,
`compute_manifest_hash`, `checkpoint_key`, `generator_key`, `seed_for`, `numeric_seed`, or any name ending in
`hash`, `sha`, `digest`, `seed`, `fingerprint` or `content_id`) directly or through names assigned or mutated
from it, must be a source of a pinned site or be on `PROVENANCE_ONLY` with a reason.

**At the tip** it flags 86 functions (88 before the A2-A4 fix; `task_graph_hash` no longer dumps beside its hash):
34 are registered sources of pinned sites, 52 are on the allowlist: 25 structured prompts whose context should
change the request with its fields; 6 harness or experiment keys; 5 reports' `config_hash` values; 16 with a
reason of their own, among them provenance-only row hashes and in-process memos (`events_fingerprint`,
`_vault_digest`, the plan and decision-state config hashes, `extraction_result_hash`, agent-run and ledger
hashes nothing looks up, a capture's retry check), and six false positives the reasons name (a quote's hash, a
`_seed` that authors an item, two candidate-id hashes, a facet write and an offer trace, where the scan's
order-insensitivity or a name match flags a dump that does not reach the hash). Each reason was checked against
the code. A stale allowlist entry (no longer flagged) or a registered source that no longer exists fails too.

**What it cannot see:** a dump returned to another function that hashes it (the synthesis scope, `router_settings`,
`_profile_settings`, `JudgeRoute.as_dict`), and `prompt_safe`'s automatic dump of a model placed in a structured
prompt. Those are the cross-function cases the pins exist for. It ignores statement order and branches (which is
what makes the false positives above), and a dump stored in an attribute (`self.x = ...`) and hashed in another
method.

## 7. The A2-A4 fix

The synthesis manifest scope's other whole dumps now go through explicit identity views that name today's fields:

- **A2** `JudgeRoute.as_dict` names `Pricing`'s three fields instead of `asdict`; a field added to `Pricing` stays
  out. The problem text stays identity on purpose: each problem variant is pinned, so rewording one fails.
- **A3** `GraphNominator.identity` hashes `identity_view(config.graph_nomination, IDENTITY_CONFIG_FIELDS)`; A1's
  `manifest_identity` likewise uses `identity_view(config.facet_identity, MANIFEST_CONFIG_FIELDS)` (the retired
  `merge_locked_facets` included). `identity_view` leaves a later field out and raises on a named field that is
  gone without a `RETIRED_FIELDS` entry. `GraphNominationConfig` now subclasses `KeepsRetiredFields`, so a future
  retirement remembers an old config's value.
- **A4** `task_graph_hash` dumps blueprints through `_BLUEPRINT_IDENTITY_FIELDS` (Blueprint, BlueprintRecipe,
  RecipeComponent), keeping keys the owner's YAML wrote that no model declares, dumped exactly as before.

**No byte moved.** The pins were recorded on commit 1 (before the fix) and pass unchanged on commit 2:

| Pin | Digest before and after |
| --- | --- |
| A1.init | `a86a21e99129979f…` (also arc C's recorded 88607cb3fe digest of the default dump) |
| A1.legacy | `a073765338abd9e2…` |
| A2.init.subscription | `7243b06bfaf6cd50…` |
| A2.metered_known_price | `5a514f83ce3f3d03…` |
| A3.legacy.embedding_on | `8506f5f19e68acf4…` |
| A4.fixed_vault | `05dda7730cc69d6a…` |
| A1-A4.scope.init / .legacy | `b5cd34e2b496d9dd…` / `d8a2a2b52455e934…` |
| A1-A4.manifest_hash.init / .legacy | `62a02700cde0173f…` / `cbaf0d5d080ee7d4…` |

Beyond the fixed inputs, a scratch check compared `_blueprint_identity` with the old
`model_dump(mode="json", exclude_none=True)` on 3,000 random blueprints (defaults, `None` integrations, extras
holding `None` and nested `None`): equal on all; and each config view with the whole `identity_dump` on the
default and a non-default section: equal. The extraction in commit 1 (`manifest_identity`, `bootstrap_scope`,
`draw_inputs`) is code motion; `tests/test_retired_config_identities.py`'s reuse tests (a run completed before arc C
is reused for the same request) pass through it.

## 8. Proof: each pin fails when its source changes

Driven by a scratch script (orchestrator scratch `refactor-k0/proof.py`): each edit is written into `src/`, `tests/test_identity_pins.py` runs whole, the failures are recorded, and the file is restored byte for byte (`git status` clean after). Each run is checked for its intended failures, for the pins it must leave passing (the "held" cases), and for the keep-or-bump message in the output. All 34 behaved as intended. Three edits were redone: two first runs put a defaulted dataclass field before a required one (an import error, not a pin failure), and the A22 rename moved no pin because no init profile sets the attributes `model_settings` reads, which is A22's silent-`None` hazard itself; the pin `A22.openrouter.every_setting` (every attribute set) was added and catches it.

| Site, scratch edit | Edit | Identity pins that failed | Shape pins that failed |
| --- | --- | --- | --- |
| A1 default | learnloop/config/schema.py: `max_calls: int = Field(default=24, ge=0)` to `max_calls: int = Field(default=25, ge=0)` | A1-A4.manifest_hash.init, A1-A4.manifest_hash.legacy, A1-A4.scope.init, A1-A4.scope.legacy, A1.init, A1.legacy | FacetIdentityConfig |
| A1 removal | learnloop/config/schema.py: remove `reword_confirm: bool = True` | A1-A4.manifest_hash.init, A1-A4.manifest_hash.legacy, A1-A4.scope.init, A1-A4.scope.legacy, A1.init, A1.legacy | FacetIdentityConfig |
| A2 problem text | learnloop/content/facet_identity/judge.py: `f"judge route names an unknown profile {provider!r}"` to `f"judge route names an unknown judge profile {provider!r}"` | A2.problem.unknown_profile | none |
| A2 known price | learnloop/content/facet_identity/judge.py: `"anthropic/claude-haiku-5.5": (0.10, 0.50),` to `"anthropic/claude-haiku-5.5": (0.10, 0.55),` | A2.metered_known_price | none |
| A3 default | learnloop/config/schema.py: `max_query_calls: int = Field(default=8, ge=0)` to `max_query_calls: int = Field(default=9, ge=0)` | A1-A4.manifest_hash.legacy, A1-A4.scope.legacy, A3.legacy.embedding_on | GraphNominationConfig |
| A3 added field (view keeps bytes) | learnloop/config/schema.py: add `added_knob: int = 1` | none (held) | GraphNominationConfig |
| A4 default | learnloop/vault/models.py: `modality: RequirementModality = "hard"` to `modality: RequirementModality = "path_specific"` | A1-A4.manifest_hash.init, A1-A4.manifest_hash.legacy, A4.fixed_vault, B1-B3.contract_hash, B6.learning_object | RecipeComponent |
| A4 added field (view keeps bytes) | learnloop/vault/models.py: add `weight_hint: float = 1.0` | B6.learning_object | RecipeComponent |
| A6/A8/A22 profile field | learnloop/config/schema.py: add `route_tag: str = "default"` | A6.skeleton.openrouter, A7.pair, A8.pair | OpenRouterProviderConfig |
| A22 renamed profile attribute | learnloop/config/schema.py: `reasoning_effort: str \| None = None` to `effort: str \| None = None` | A22.openrouter.every_setting, A6.freshness.deepseek, A6.skeleton.openrouter, A7.pair, A8.pair | AIProviderConfig, ChatGPTPlanProviderConfig, ... (10 in all) |
| A7/A9/A19/B6 PracticeItem default | learnloop/vault/models.py: `status: Literal["active", "retired"] = "active"` to `status: Literal["active", "retired"] = "retired"` | A19.item, A19.publish_judged_inputs, A7.pair, A9.item, B6.practice_item | PracticeItem |
| A10 EvidenceFacet default | learnloop/vault/models.py: `status: Literal["proposed", "reviewed", "retired"] = "review` to `status: Literal["proposed", "reviewed", "retired"] = "propos` | A1-A4.manifest_hash.init, A1-A4.manifest_hash.legacy, A10.facet_defaults | EvidenceFacet |
| A11/B2 TraceContract field | learnloop/vault/models.py: add `notes: list[str] = Field(default_factory=lambda: ["n"])` | A11-A12.prompt, A11-A12.structure_hash, A19.item, A19.publish_judged_inputs, A7.pair, ... (8 in all) | TraceContract |
| A13 context field | learnloop/content/pipeline/ai_contracts.py: add `audience: str = "learner"` | A13.prompt | CanonicalIngestContext |
| A14 context field | learnloop/content/synthesis/ai_contracts.py: add `audience: str = "learner"` | A14.pass_key.one_facet_per_skill, A14.pass_key | SourceSetSynthesisContext |
| A15 context field | learnloop/content/synthesis/ai_contracts.py: add `audience: str = "learner"` | A15.window_key | SourceUnitInventoryContext |
| A19 ActivityFamily default | learnloop/vault/models.py: `generator: dict[str, Any] \| None = None` to `generator: dict[str, Any] \| None = Field(default_factory=dic` | A19.family | ActivityFamily |
| A20 schema docstring | learnloop/practice_index/contracts.py: `"""Judge every candidate, then pick and order the best few."` to `"""Judge every candidate, then pick and order the best ones.` | A20.paid.checkpoint_key, A20.schema.PracticeRerank | none |
| B1-B5 RubricCriterion default | learnloop/vault/models.py: `] \| None = None` to `] \| None = "supporting"` | A19.item, A19.publish_judged_inputs, A7.pair, A9.item, B1-B3.card, ... (11 in all) | RubricCriterion |
| B6 LO default | learnloop/vault/models.py: `status: Literal["active", "dormant", "resolved"] = "active"` to `status: Literal["active", "dormant", "resolved"] = "dormant"` | A1-A4.manifest_hash.init, A1-A4.manifest_hash.legacy, B6.learning_object | LearningObject |
| B6 ErrorType field | learnloop/vault/models.py: add `family: str = "general"` | B6.error_type | ErrorType |
| B7 GoalFacetScope field | learnloop/vault/models.py: add `tags: list[str] = Field(default_factory=lambda: ["t"])` | none (held) | GoalFacetScope |
| B9 registry param kind | learnloop/params/parameter_registry.py: `_reg_const("staged_policy:ATTENTION_BLOCK_MIN_MINUTES", "thr` to `_reg_const("staged_policy:ATTENTION_BLOCK_MIN_MINUTES", "str` | B9.manifests | none |
| B10 allowlist entry | learnloop_mobile/allowlist.py: `MobileMethod("plan_prefetch", "IH0", "short", False,` to `MobileMethod("plan_prefetch", "IH0", "short", True,` | B10.digest | none |
| C1/C2 H6 removal without RETIRED_FIELDS | learnloop/config/schema.py: remove `difficulty_from_prior: bool = True       # derive b from PracticeItem.` | C1.init, C1.legacy, C2.answer_signal:confidence.init, C2.answer_signal:confidence.legacy, C2.answer_signal:hedging.init, ... (48 in all) | MasteryConfig, MasteryIRTConfig |
| C1/C2 H6 removal with RETIRED_FIELDS (keeps bytes) | learnloop/config/schema.py: remove `difficulty_from_prior: bool = True       # derive b from PracticeItem.`; learnloop/config/retired.py: add `RetiredField("MasteryIRTConfig", ("difficulty_from_prior",), bool, Tru` | none (held) | MasteryConfig, MasteryIRTConfig |
| C1/C2 prior scale default | learnloop/config/schema.py: `difficulty_prior_scale: float = 2.5` to `difficulty_prior_scale: float = 2.0` | C1.init, C2.answer_signal:confidence.init, C2.answer_signal:confidence.legacy, C2.answer_signal:hedging.init, C2.answer_signal:hedging.legacy, ... (26 in all) | MasteryConfig, MasteryIRTConfig |
| C2 ArmConstants default | learnloop/field/types.py: `practice_gamma: float = 0.2` to `practice_gamma: float = 0.25` | C2.answer_signal:confidence.init, C2.answer_signal:confidence.legacy, C2.answer_signal:hedging.init, C2.answer_signal:hedging.legacy, C2.idea_hier.init, ... (42 in all) | ArmConstants |
| C2 HeadPriors default | learnloop/field/success_head.py: `ability_variance: float = 0.25` to `ability_variance: float = 0.3` | C2.success_head+difficulty.init, C2.success_head+difficulty.legacy, C2.success_head.init, C2.success_head.legacy | HeadPriors |
| C2p ItemFeatures field | learnloop/field/types.py: add `cohort: str = "solo"` | C2p.position | ItemFeatures |
| C3/C6 RouterWeights default | learnloop/config/schema.py: `staged: float = Field(default=1.0 / 3.0, ge=0.0)` to `staged: float = Field(default=0.4, ge=0.0)` | C3.boundary.init, C3.boundary.legacy, C3.router_settings.init, C3.router_settings.legacy, C6.init, C6.legacy | RouterWeights |
| C4 switch removed (D7) | learnloop/router_objective_switches.py: `FOLLOWUP_SWITCHES: tuple[str, ...] = (*FOLLOWUP_GENERATOR_SW` to `FOLLOWUP_SWITCHES: tuple[str, ...] = (*FOLLOWUP_GENERATOR_SW` | C3.boundary.init, C4.objective_settings.init, C4.switches.init | none |
| C5 generator switch removed (D7) | learnloop/router_objective_switches.py: `"scope_extension", "held_ad_link", "held_reading_map", "pool` to `"scope_extension", "held_ad_link", "held_reading_map")` | C3.boundary.init, C4.objective_settings.init, C4.switches.init, C5.init | none |
| C6 ceiling default | learnloop/config/schema.py: `ceiling_per_day: int = Field(default=3, ge=0)` to `ceiling_per_day: int = Field(default=4, ge=0)` | C6.init, C6.legacy | none |

Read across the rows: a removal or default change of a config field moves its pins (A1, A3, C1-C2), and the same
removal with a `RETIRED_FIELDS` entry moves none, failing only the shape pin, which is regenerated once the
identities pass (the H6 case). A field added to a section behind an explicit view (A3, A4) moves no identity, only
the shape. Vault-model and dataclass defaults and additions move every whole dump of the type (A7, A9, A10,
A11-A15, A19, B1-B6). A removed or reworded string that is identity (A2's problem text, a schema docstring, a switch
list entry, an allowlist entry) moves its pin. **Correction to the sweep:** B7 is not a whole dump in effect:
`goal_contracts.canonicalize_body` keeps only `concepts` and `facets` of the scope, so an added scope field moves
nothing (the pin holds; the shape pin still fails).

## 9. Open items

- **D7:** C3-C6 show every switch removal (a removed `carried_in_prefetch` moves `C4.switches.init`,
  `C4.objective_settings.init` and the boundary seed). Per switch, D7 keeps its served value in the identity or
  folds the move into E8's one recorded change point; a line says so in D7's row.
- **E8:** narrowing the router identity to value-changing switches moves C3-C5 on purpose: regenerate the pins in
  that commit under the playbook.
- **H6:** the rule is in H6's row: `difficulty_from_prior` and `difficulty_prior_scale` go into `RETIRED_FIELDS`
  in the removing commit (§8 shows the pins fail without it and pass with it), and `PracticeItem.difficulty`
  stays on the model.
- **Narrowing (sweep §3.4 steps 2-4):** spend caps and prices are still in the synthesis manifest (A1, A2), whole
  provider profiles in the PF, family and contamination keys (A6-A8): changing a cap or a profile setting is a new
  paid request. Narrowing needs a dual read; not K0.
- **`tests/test_retired_config_identities.py`** stays: it pins arc C's base-commit digests through the full
  `create_study_map` and `append_source` paths, the reuse scenario, and the retired-field structure, none of which
  the K0 pins duplicate.

## 10. Runtime

`tests/test_identity_pins.py`: 199 tests in about 5.3 s serial (`--durations`: the AST scan 4.0 s, the rest under
0.1 s each after the first pin's 0.7 s setup). Unmarked, so in the landing gate and in `-m "not slow"`;
`scripts/check_gate_partition.py` passes.

## 11. Vault

References regenerated once after the source commits (`_scripts/generate_all.py`, 123 generated notes: the module
notes of the edited modules, the configuration field notes that list the test helper sources, and the generators'
record), committed as `7d23fd5680`; a second run on the clean tree changed nothing (a fixed point). No hand-written
note mentions what K0 changed (the only notes naming `identity_dump`, `task_graph_hash` or `model_dump` are
generated). The four validators pass: `db_validate_reference.py`, `module_validate.py`, `desktop_validate.py`,
`validate_vault.py`.

## 12. Gates run

- `scripts/affected_tests.py --base ad194ddc3a` selects 1,280 test files (the `config/schema.py` and `vault`-adjacent
  edits reach most of the suite); with the five named files (`test_identity_pins`, `test_retired_config_identities`,
  `test_architecture`, `test_test_layout`, `test_eval_harness`), 1,285 files, run in seven chunks at `-n 4` under the
  5 GB cap and the full-suite lock, `-m "not arc_close"`: 20,313 passed, 1 failed. The failure,
  `test_model_call_receipt_owners.py::test_tui_grading_records_receipts_with_usage`, waits a fixed ten TUI pauses
  for a grade; it ran while the vault generator was also running, and passes alone three times out of three. K0
  touches nothing on the TUI or grading path. A first attempt at `-n 6` in one scope stopped silently at 42%
  (likely the memory cap) with no failure printed.
- `ruff check`: clean. `lint-imports --no-cache`: 42 kept, 0 broken. `scripts/check_gate_partition.py`: 30,943
  collected, landing 30,883 + arc_close 60.
- The four vault validators pass (§11).
- Not run (the orchestrator's): the full suite, durability, `--fresh-connections`, vitest.
