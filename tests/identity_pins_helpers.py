"""Identity pins (refactor step K0): every compared identity, computed through its production path at a fixed input.

A compared identity is a value stored and compared later: a cache or reuse key (a completed paid run, a
checkpoint, a receipt), a manifest or version hash, a seed, or a structured prompt whose text keys reuse. Arc C's
removal of an unread config field moved one (canonical synthesis's manifest hash, so finished runs stopped being
reused) because a deletion proof follows imports and names, and a whole ``model_dump`` inside a hash reads every
field without naming it. ``tests/test_identity_pins.py`` holds each identity below to its digest in
``tests/goldens/identities.toml`` and each type whole-dumped into one to its shape in
``tests/goldens/identity_shapes.toml``; its AST check holds every dump beside a hash, seed, manifest or structured
prompt to this module's registry. The design is the serialization sweep of Nov 11 (``docs/reviews/refactor-k0.md``).

The fixed inputs are written out here and never read from a template vault or the init template's text beyond
its config, so a change elsewhere in the tests never moves a pin. Each pin calls the production function that
computes the identity; where production builds the identity inline from production pieces (the router's boundary
identity), the pin builds the same literal from the same pieces and says so.

Vault models keep unknown keys (``extra="allow"``), so a field removed from one stays in the dump of an input
that set it explicitly: the fixed inputs leave several defaulted fields unset so a removal or a default change
moves the pin, and the shape pins catch the rest.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
import copy
from dataclasses import MISSING, dataclass, fields as dataclass_fields, is_dataclass
from functools import cache
import hashlib
import json
from pathlib import Path
import tomllib
from types import SimpleNamespace
from typing import Any

from pydantic import BaseModel

REPO = Path(__file__).resolve().parent.parent
GOLDENS = Path(__file__).resolve().parent / "goldens"
IDENTITIES_PATH = GOLDENS / "identities.toml"
SHAPES_PATH = GOLDENS / "identity_shapes.toml"
REGENERATE = "uv run python tests/test_identity_pins.py --write"

NOW = "2026-01-01T00:00:00Z"
#: Never opened: identities that carry a vault root carry this one.
VAULT_ROOT = Path("/identity-pins/vault")
#: Never opened: the graph nominator reads ``no_database`` here, deterministically.
NO_DATABASE = Path("/identity-pins/no-such-state.sqlite")

KEEP_OR_BUMP = (
    "A refactor must not move a compared identity at a fixed input. Two ways out:\n"
    "  keep the bytes: a removed config field goes into config/retired.py's RETIRED_FIELDS (identity_dump puts it "
    "back); a vault model or dataclass field gets exclude_if or an explicit identity view that names its fields; a "
    "new field stays out of the view;\n"
    "  or bump deliberately: when persisted meaning is meant to change, follow docs/algorithm-change-playbook.md "
    f"(bump the site's version constant), regenerate the pins in that commit with `{REGENERATE}`, and give the "
    "reason in the landing note."
)


def digest(value: Any) -> str:
    """sha256 of the value's sorted, compact JSON (what a pin records)."""

    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _merge(base: dict[str, Any], overlay: Mapping[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, Mapping) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


# -- fixed configs ----------------------------------------------------------------------------------------------

#: An old ``learnloop.toml`` that sets every key arc C retired (``tests/test_retired_config_identities.py``'s), plus a
#: non-default value in each section a compared identity dumps whole, and the embedding switch on so the graph
#: nominator's identity is in the synthesis scope. No ``[algorithms]``: the bare default tag (below every successor
#: whose switches enter a key, so the predecessor branches are pinned too).
LEGACY_TOML = """\
[facet_identity]
merge_locked_facets = false
shortlist_top_k = 5
max_cost_usd = 0.75

[graph_nomination]
top_k = 7
max_query_cost_usd = 0.1

[embedding]
enabled = true

[locks]
facet_lock_mass = 3

[plan]
pre_questions = 5

[mastery.irt]
discrimination_min = 0.5
discrimination_max = 2.5
difficulty_prior_scale = 0.8

[recall_coverage.severity_examples.custom]
expected_error_type = "conceptual_error"
expected_severity_band = [0.1, 0.2]
target_error_type = "conceptual_error"

[error_impacts.recall_failure]
families = { recall = -0.3 }

[error_impacts.custom_impact]
lo_mastery_delta = -0.1

[ai]
agent_harness_opt_in = true

[codex]
provider = "sdk"
model = "gpt-5.5"
timeout_seconds = 200

[router]
epsilon_min = 0.07
"""


def config_from(raw: Mapping[str, Any]) -> Any:
    """A config exactly as ``config.loader.load_config`` builds it from parsed TOML, without the environment."""

    from learnloop.config.loader import normalize_config_input
    from learnloop.config.schema import LearnLoopConfig

    return LearnLoopConfig.model_validate(normalize_config_input(copy.deepcopy(dict(raw))))


@cache
def _init_raw() -> dict[str, Any]:
    from learnloop.config.template import DEFAULT_CONFIG_TEXT

    return tomllib.loads(DEFAULT_CONFIG_TEXT)


def init_config(**overlay: Any) -> Any:
    """A new vault's config (``learnloop init``'s template), with ``overlay`` merged into its TOML."""

    return config_from(_merge(_init_raw(), overlay))


def legacy_config() -> Any:
    return config_from(tomllib.loads(LEGACY_TOML))


CONFIGS: dict[str, Callable[[], Any]] = {"init": init_config, "legacy": legacy_config}


# -- fixed vault content ----------------------------------------------------------------------------------------

RUBRIC = {
    "max_points": 4,
    "criteria": [
        {"id": "c_define", "points": 2, "description": "States the factorization A = U Sigma V^T.",
         "tier": "core", "targets": [{"facet": "fct_svd_define", "capability": "retrieval", "role": "primary"}],
         "correlation_group": "svd", "recipe_ids": ["r_define"], "measurement_status": "direct"},
        {"id": "c_orthogonal", "points": 2, "description": "Says U and V are orthogonal.", "tier": "transfer",
         "targets": [{"facet": "fct_svd_orthogonal", "capability": "schema_interpretation",
                      "role": "supporting"}],
         "depends_on": ["c_define"], "recipe_ids": ["r_define"]},
    ],
    "fatal_errors": [{"id": "fe_eigen", "description": "Confuses SVD with eigendecomposition.", "max_grade": 1,
                      "misconception_id": "err_eigen_confusion"}],
}

ITEM = {
    "id": "pi_pin_svd_001",
    "learning_object_id": "lo_pin_svd",
    "subjects": ["linear-algebra"],
    "practice_mode": "free_recall",
    "attempt_types_allowed": ["independent_attempt", "hinted_attempt"],
    "evidence_facets": ["fct_svd_define", "fct_svd_orthogonal"],
    "evidence_weights": {"fct_svd_define": 0.7, "fct_svd_orthogonal": 0.3},
    "criterion_facet_weights": {"c_define": {"fct_svd_define": 1.0}},
    "trace_contract": {"status": "available",
                       "recipes": [{"id": "r_define", "checkpoints": ["cp_factor", "cp_orthogonal"],
                                    "dependencies": {"cp_orthogonal": ["cp_factor"]}}]},
    "variant_contract": {"variant_kind": "harder", "incidental_changes": ["matrix size"],
                         "held_constant": ["definition"], "preserves_checkpoints": ["cp_factor"],
                         "deepens_checkpoints": ["cp_orthogonal"]},
    "prompt": "Define the singular value decomposition of a real matrix A.",
    "expected_answer": "A = U Sigma V^T with U, V orthogonal and Sigma diagonal with non-negative entries.",
    "difficulty": 0.4,
    "difficulty_source": "author",
    "expected_minutes": 5.0,
    "tags": ["svd"],
    "hints": ["Think of rotations and scalings.", "Which factors are orthogonal?"],
    "hint_policy": {"max_useful_hints": 2, "fsrs_rating_cap_by_hint": {"1": "good", "2": "hard"},
                    "mastery_alpha_dampening_by_hint": {"1": 0.8, "2": 0.5}},
    "retrieval_demand": 0.6,
    "transfer_distance": 0.2,
    "scaffold_level": 0.1,
    "capability": "retrieval",
    "task_features": {"steps": 2},
    "task_feature_schema": "tf_pin_v1",
    "surface_family": "svd_definition",
    "evidence_fingerprint": {"source_family": "strang", "shared_stimulus_id": "stim_svd",
                             "representation": "symbolic", "solution_recipe_family": "definition",
                             "answer_structure": "equation"},
    "misconception_consistent_answer": "A = P D P^-1",
    "repair_targets": ["fct_svd_orthogonal"],
    "grading_rubric": RUBRIC,
    "required_method": {"name": "singular value decomposition", "criterion_ids": ["c_define"],
                        "learning_object_id": "lo_pin_svd", "concept_id": "singular_value_decomposition",
                        "facet_id": "fct_svd_define", "statement": "instruction", "decided_by": "owner"},
    "created_at": NOW,
    "updated_at": NOW,
    "family_id": "fam_pin_svd",
    "variant_relation": "isomorph",
}

#: A second item of the same LO: the pair the family judge compares.
ITEM_2 = _merge(ITEM, {"id": "pi_pin_svd_002", "prompt": "Write the SVD of a 2x3 matrix A in general form.",
                       "family_id": None, "variant_relation": None})

FACET = {
    "id": "fct_svd_define",
    "title": "SVD definition",
    "aliases": ["singular value decomposition"],
    "description": "The factorization of a matrix into orthogonal and diagonal factors.",
    "tags": ["svd"],
    "concept_id": "singular_value_decomposition",
    "kind": "definition",
    "claim": "Every real matrix A factors as U Sigma V^T.",
    "preconditions": ["A is a real matrix"],
    "postconditions": ["U, V orthogonal"],
    "applicability": ["any real matrix"],
    "positive_examples": ["A 2x2 rotation-scaling"],
    "negative_examples": ["P D P^-1"],
    "non_goals": ["computing the SVD numerically"],
    "error_signatures": ["eigendecomposition substituted"],
    "instructional_repairs": ["contrast with eigendecomposition"],
    "status": "reviewed",
    "version": 2,
    "semantic_fingerprint": "fp_pin",
}
FACET_2 = {"id": "fct_svd_orthogonal", "title": "Orthogonal factors", "concept_id": "singular_value_decomposition",
           "kind": "proposition", "claim": "U and V are orthogonal."}

LEARNING_OBJECT = {
    "id": "lo_pin_svd",
    "title": "Singular value decomposition",
    "subjects": ["linear-algebra"],
    "concept": "singular_value_decomposition",
    "knowledge_type": "definition",
    "summary": "Define and use the SVD.",
    "prerequisites": ["lo_pin_orthogonal"],
    "confusables": ["lo_pin_eigen"],
    "blueprints": [{
        "id": "bp_define", "weight": 0.8,
        "recipes": [{
            "id": "r_define",
            "all_of": [{"facet": "fct_svd_define", "capability": "retrieval"}],
            "any_of": [{"facet": "fct_svd_orthogonal", "capability": "schema_interpretation",
                        "modality": "path_specific"}],
            "integration": {"facet": "fct_svd_define", "capability": "coordination", "modality": "facilitating"},
            # An authored key the model does not declare: vault models keep it, and the task graph hashes it.
            "authored_note": "from the owner's outline",
        }],
    }],
    "difficulty_prior": 0.3,
    "difficulty_source": "author",
    "tags": ["svd"],
    "created_at": NOW,
    "updated_at": NOW,
}

CONCEPT = {"title": "Singular Value Decomposition", "type": "procedure", "aliases": ["SVD"],
           "description": "Matrix factorization.", "tags": ["la"], "created_at": NOW, "updated_at": NOW}

ERROR_TYPE = {"id": "err_eigen_confusion", "title": "Eigen confusion", "description": "Uses P D P^-1.",
              "related_concepts": ["singular_value_decomposition"], "severity_default": 0.7,
              "is_misconception": True, "tags": ["svd"], "created_at": NOW, "updated_at": NOW}

FAMILY = {"id": "fam_pin_svd", "learning_object_id": "lo_pin_svd", "idea_statement": "Define the SVD.",
          "retrieval_target": "A = U Sigma V^T", "source_kind": "authored", "created_at": NOW, "updated_at": NOW}

GOAL = {"id": "goal_pin", "title": "Linear algebra for ML", "status": "active", "priority": 0.8,
        "target_recall": 0.85, "due_at": "2026-06-01T00:00:00Z",
        "facet_scope": {"concepts": ["singular_value_decomposition"], "facets": ["fct_svd_define"]},
        "exam": {"enabled": True, "item_count": 12}, "created_at": NOW, "updated_at": NOW}


def vault(config: Any | None = None) -> Any:
    """A ``LoadedVault`` holding the fixed content, built in memory (its root is never opened)."""

    from learnloop.vault import models as m

    loaded = m.LoadedVault(root=VAULT_ROOT, config=config if config is not None else init_config())
    loaded.concepts = {"singular_value_decomposition": m.Concept.model_validate(CONCEPT)}
    loaded.learning_objects = {LEARNING_OBJECT["id"]: m.LearningObject.model_validate(LEARNING_OBJECT)}
    loaded.practice_items = {raw["id"]: m.PracticeItem.model_validate(raw) for raw in (ITEM, ITEM_2)}
    loaded.evidence_facets = {raw["id"]: m.EvidenceFacet.model_validate(raw) for raw in (FACET, FACET_2)}
    loaded.error_types = {ERROR_TYPE["id"]: m.ErrorType.model_validate(ERROR_TYPE)}
    loaded.activity_families = {FAMILY["id"]: m.ActivityFamily.model_validate(FAMILY)}
    loaded.goals = [m.Goal.model_validate(GOAL)]
    return loaded


def item(index: int = 0) -> Any:
    return vault().practice_items[(ITEM, ITEM_2)[index]["id"]]


class _FrozenClock:
    def now(self):  # noqa: ANN201 - the clock protocol
        from datetime import UTC, datetime

        return datetime(2026, 1, 1, tzinfo=UTC)


class FakeStructuredClient:
    """A structured client as checkpoint keys read it (``ai.execution.model_settings``): a name, a model and a
    profile. It never answers."""

    def __init__(self, provider: str = "openrouter", model: str = "openai/gpt-pin", profile: Any = None):
        self.provider_name = provider
        self.provider_type = "openrouter"
        self.model = model
        self.profile = profile if profile is not None else init_config().ai.providers[provider]


# -- the pins ---------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class IdentitySite:
    """One compared identity: the sweep's id, the production functions that compute it (``path::qualname``, which
    also registers them with the AST check), what compares it, what moving it costs, and its pins."""

    id: str
    title: str
    sources: tuple[str, ...]
    consumer: str
    consequence: str
    pins: Mapping[str, Callable[[], Any]]


def _a1_facet_identity(config_name: str) -> Callable[[], Any]:
    def compute() -> Any:
        from learnloop.content.facet_identity.judge import manifest_identity

        return manifest_identity(CONFIGS[config_name]())["config"]
    return compute


def _route(config: Any) -> Any:
    from learnloop.content.facet_identity.judge import resolve_route

    return resolve_route(config).as_dict()


def _route_variants() -> dict[str, Callable[[], Any]]:
    def routed(provider: str, **overlay: Any) -> Callable[[], Any]:
        return lambda: _route(init_config(**_merge({"ai": {"routing": {"facet_identity_judge": provider}}},
                                                   overlay)))
    return {
        "init.subscription": lambda: _route(init_config()),
        "legacy": lambda: _route(legacy_config()),
        "metered_known_price": routed("openrouter_haiku"),
        "metered_unknown_price": routed("openrouter", ai={"providers": {"openrouter": {"model": "pin/unpriced"}}}),
        "owner_price": routed("openrouter", ai={"providers": {"openrouter": {"model": "pin/unpriced"}}},
                              facet_identity={"price_per_million_input": 1.5, "price_per_million_output": 6.0}),
        "decider": routed("openrouter_decider"),
        "problem.unknown_profile": routed("pin_missing_profile"),
        "problem.wrong_type": routed("openrouter_embedding"),
    }


def _nominator(config: Any) -> Any:
    from learnloop.content.synthesis.graph_nomination import GraphNominator

    repository = SimpleNamespace(sqlite_path=str(NO_DATABASE))
    return GraphNominator.for_ingest(vault(config), repository)


def _a3_graph_nomination() -> Any:
    from learnloop.content.synthesis.ai_contracts import CONCEPT_GRAPH_REGISTRY_PROMPT_VERSION

    return _nominator(legacy_config()).identity(prompt_version=CONCEPT_GRAPH_REGISTRY_PROMPT_VERSION)


def _bootstrap_scope(config_name: str) -> Callable[[], Any]:
    def compute() -> Any:
        from learnloop.content.synthesis.source_set_synthesis import bootstrap_scope

        config = CONFIGS[config_name]()
        return bootstrap_scope(vault(config), {"scope": {"chapters": [1, 2]}}, nominator=_nominator(config))
    return compute


def _append_scope(config_name: str) -> Callable[[], Any]:
    def compute() -> Any:
        from learnloop.content.synthesis.source_append import append_scope

        return append_scope(
            vault(CONFIGS[config_name]()), change_kind="source_added", revision_ids={"rev_pin_b", "rev_pin_a"},
            neighborhood={"concepts": ["singular_value_decomposition"], "budget_tokens": 24000},
        )
    return compute


def _manifest(config_name: str) -> dict[str, Any]:
    from learnloop.content.synthesis.ai_contracts import source_set_synthesis_prompt_version
    from learnloop.content.synthesis.synthesis_manifests import build_manifest

    config = CONFIGS[config_name]()
    loaded = vault(config)
    return build_manifest(
        loaded, source_set_id="set_pin", membership=[{"source_id": "src_pin", "role": "primary"}],
        revision_ids=["rev_pin"], extraction_ids=["ext_pin"], unit_inventory_versions={"unit_pin": "inv_v1"},
        scope=_bootstrap_scope(config_name)(), brief={"scope": {"chapters": [1, 2]}},
        prompt_version=source_set_synthesis_prompt_version(bool(config.facet_identity.enabled)),
        provider="chatgpt_medium", model="gpt-pin", assessment_schema_version=None,
        token_budget={"synthesis_shard_input_tokens": 1000}, clock=_FrozenClock(),
    )


def _a4_task_graph() -> Any:
    from learnloop.content.synthesis.synthesis_manifests import task_graph_hash

    return task_graph_hash(vault())


def _pf_input_hash(role: str) -> Callable[[], Any]:
    def compute() -> Any:
        from learnloop.ai.spend import SpendCaps
        from learnloop.content.authoring import pf_contracts as C
        from learnloop.ops.pf_calls import PFCaller, planned_role_clients

        config = init_config(ai={"routing": {"pf_generator": "openrouter", "pf_isomorph_judge": "deepseek_flash"}})
        loaded = vault(config)
        caller = PFCaller(loaded, None, caps=SpendCaps(max_calls=1), price_per_million=None, run_id="run_pin")
        entry = planned_role_clients(loaded, role)[0]
        return {"settings": entry.settings,
                "input_hash": caller.input_hash(entry, "pin prompt", C.SkeletonResult, 512)}
    return compute


def _family_pair_keys() -> Any:
    from learnloop.ops.family_proposals import _settings, pair_passes

    loaded = vault(init_config(ai={"routing": {"pf_family_judge": "openrouter"}}))
    settings = _settings(loaded, "openrouter")
    return {"settings": settings,
            "keys": [p.judgment_id for p in pair_passes(loaded, [("pi_pin_svd_001", "pi_pin_svd_002")], settings)]}


def _contamination_keys() -> Any:
    from learnloop.ops.contamination.detectors import Candidate
    from learnloop.ops.contamination.judge import build_requests, judge_settings

    loaded = vault(init_config())
    settings = judge_settings(loaded, "openrouter", None, "1")
    candidate = Candidate(detector=_contamination_detector(), left_kind="practice_item", left_id="pi_pin_svd_001",
                          right_kind="practice_item", right_id="pi_pin_svd_002",
                          context={"left": "Define the SVD.", "right": "Write the SVD."},
                          subject_text="Define the SVD.", target_text="Write the SVD.")
    return {"settings": settings, "keys": [r.judgment_id for r in build_requests([candidate], settings)]}


def _contamination_detector() -> str:
    from learnloop.ops.contamination.detectors import TASK_FOR_DETECTOR

    return sorted(TASK_FOR_DETECTOR)[0]


def _map_seeds() -> Any:
    from learnloop.hints.map_seeds import MapSeeds

    pinned = item()
    return MapSeeds(item=pinned, item_hash="hash_pin", rubric=[dict(c) for c in RUBRIC["criteria"]],
                    authored_hints=list(pinned.hints),
                    trace_contract=pinned.trace_contract.model_dump(mode="json"),
                    skeletons=[{"id": "sk_pin", "techniques": ["definition"], "operations": ["state"],
                                "checkpoints": ["cp_factor"], "skeleton_text": "State A = U S V^T."}],
                    facet_ids=["fct_svd_define"], learning_object_title="Singular value decomposition")


def _canonical_ingest_prompt() -> Any:
    from learnloop.content.pipeline.ai_contracts import CanonicalIngestContext, canonical_ingest_prompt

    return canonical_ingest_prompt(CanonicalIngestContext(
        vault_root=str(VAULT_ROOT), source_kind="textbook_chapter", canonical_source={"id": "src_pin", "title": "Notes"},
        chunks=[], target_subject="linear-algebra", target_learning_object_ids=["lo_pin_svd"],
        concepts=[{"id": "singular_value_decomposition"}], learning_objects=[{"id": "lo_pin_svd"}],
        instructions="Only definitions."))


def _synthesis_context(**overrides: Any) -> Any:
    from learnloop.content.synthesis.ai_contracts import SourceSetSynthesisContext

    return SourceSetSynthesisContext(**{
        "source_set_id": "set_pin", "subject_id": "linear-algebra", "mode": "bootstrap",
        "brief": {"scope": {"chapters": [1]}}, "unit_inventories": [{"unit_id": "unit_pin", "claims": ["c"]}],
        "exam_profile": {}, "registry_index": {"facets": ["fct_svd_define"]},
        "resolved_spans": [{"span_id": "sp_pin", "text": "A = U S V^T"}], **overrides})


def _synthesis_pass_key(one_facet_per_skill: bool) -> Callable[[], Any]:
    def compute() -> Any:
        from learnloop.ai.execution import model_settings
        from learnloop.content.synthesis.ai_contracts import SourceSetSynthesis, source_set_synthesis_prompt
        from learnloop.content.synthesis.source_set_synthesis import _synthesis_pass_key as key

        prompt = source_set_synthesis_prompt(_synthesis_context(one_facet_per_skill=one_facet_per_skill))
        return key(prompt, SourceSetSynthesis.model_json_schema(), model_settings(FakeStructuredClient()))
    return compute


def _append_checkpoint_key(one_facet_per_skill: bool) -> Callable[[], Any]:
    def compute() -> Any:
        from learnloop.ai.execution import model_settings
        from learnloop.content.synthesis.ai_contracts import AppendReconciliationContext, append_reconciliation_prompt
        from learnloop.content.synthesis.source_append import append_checkpoint_key

        prompt = append_reconciliation_prompt(AppendReconciliationContext(
            source_set_id="set_pin", subject_id="linear-algebra", change_kind="source_added",
            brief={"scope": {"chapters": [2]}}, new_inventories=[{"unit_id": "unit_pin", "claims": ["c"]}],
            neighborhood={"facets": [{"id": "fct_svd_define"}]}, exam_profile={}, revision_diff={},
            resolved_spans=[{"span_id": "sp_pin", "text": "A = U S V^T"}], one_facet_per_skill=one_facet_per_skill))
        return append_checkpoint_key(prompt, {**model_settings(FakeStructuredClient()), "provider": "codex",
                                              "model": "fake-model"})
    return compute


def _inventory_window_key() -> Any:
    from learnloop.ai.execution import model_settings
    from learnloop.content.synthesis.ai_contracts import SourceUnitInventoryContext
    from learnloop.content.synthesis.source_unit_inventory import inventory_window_key

    context = SourceUnitInventoryContext(unit_id="unit_pin", semantic_hash="sem_pin", role="primary",
                                         inventory_profile="textbook", unit_view={"text": "A = U S V^T"})
    return inventory_window_key(context, model_settings(FakeStructuredClient()), schema_version=1)


def _legacy_window_key() -> Any:
    from learnloop.content.pipeline.ai_contracts import CanonicalIngestContext
    from learnloop.content.pipeline.source_ingestion import legacy_window_key

    return legacy_window_key(CanonicalIngestContext(
        vault_root=str(VAULT_ROOT), source_kind="textbook_chapter", canonical_source={"id": "src_pin", "title": "Notes"},
        chunks=[], target_subject="linear-algebra", target_learning_object_ids=["lo_pin_svd"],
        concepts=[{"id": "singular_value_decomposition"}], learning_objects=[{"id": "lo_pin_svd"}],
        instructions="Only definitions."), FakeStructuredClient())


def _facet_judge_key(judge: str, reasoning_effort: str | None = None) -> Callable[[], Any]:
    def compute() -> Any:
        from learnloop.ai.spend import SpendCaps
        from learnloop.content.facet_identity.judge import (
            DeciderGroupJudge,
            GroupRequest,
            LLMGroupJudge,
            Pricing,
        )

        request = GroupRequest(group_id="grp_pin", mode="consolidate", members=(), prompt="pin judge prompt",
                               input_hash="input_pin")
        common = {"caps": SpendCaps(), "pricing": Pricing(None, None, "unknown"), "repository": None,
                  "owner_id": "owner_pin"}
        if judge == "decider":
            return DeciderGroupJudge(client=None, model="decider/pin", **common).checkpoint_key(request)
        return LLMGroupJudge(client=FakeStructuredClient(), provider="openrouter", model="openai/gpt-pin",
                             output_tokens=2048, reasoning_effort=reasoning_effort, **common).checkpoint_key(request)
    return compute


def _structuring_key(nominated: bool) -> Callable[[], Any]:
    def compute() -> Any:
        from learnloop.ai.execution import model_settings
        from learnloop.content.synthesis.ai_contracts import ConceptGraphContext
        from learnloop.content.synthesis.source_set_synthesis import structuring_checkpoint

        context = ConceptGraphContext(
            source_set_id="set_pin", subject_id="linear-algebra",
            concepts=[{"client_item_id": "c_svd", "title": "SVD", "type": "concept", "aliases": [],
                       "description": "A = U S V^T"}],
            source_skeletons=[{"source_id": "src_pin", "units": [{"label": "Chapter 1"}]}],
            registry_concepts=["singular_value_decomposition"],
            registry_edges=[{"source": "a", "target": "b", "relation_type": "prerequisite"}],
            registry_concept_details=(
                [{"id": "singular_value_decomposition", "title": "SVD", "definition": "A = U S V^T"}] if nominated else []),
            registry_nominations=(
                [{"client_item_id": "c_svd", "registry_concept_ids": ["singular_value_decomposition"]}]
                if nominated else []),
        )
        settings = {**model_settings(FakeStructuredClient()), "provider": "codex", "model": "fake-model"}
        return structuring_checkpoint(None, context, settings).key
    return compute


def _glm_ocr_window_key() -> Any:
    from learnloop.ingest.extractors.glm_ocr import GlmOcrDocumentExtractor

    return GlmOcrDocumentExtractor(backend="api")._checkpoint_key("asset_pin", [0, 1, 2])


def _family_input(kind: str) -> Callable[[], Any]:
    def compute() -> Any:
        from learnloop.substrate.families import family_item_input_hash
        from learnloop.vault.hashes import activity_family_hash

        loaded = vault()
        if kind == "item":
            return family_item_input_hash(loaded, loaded.practice_items["pi_pin_svd_001"])
        family = loaded.activity_families["fam_pin_svd"]
        if kind == "publish":
            from learnloop.ops.pf_publish import judged_inputs

            return judged_inputs(loaded, loaded.practice_items["pi_pin_svd_001"], family)
        # family_proposals.plan_json stores the whole family dump; a repeated accept compares it (substrate.families).
        return {"plan_family": family.model_dump(mode="json"), "activity_family_hash": activity_family_hash(family)}
    return compute


def _position_key() -> Any:
    from learnloop.field.probability_arms import position_key
    from learnloop.field.types import ItemFeatures

    features = ItemFeatures(item_id="pi_pin_svd_001", lo_id="lo_pin_svd", observed_at=NOW, subject_id="linear-algebra",
                            a=1.2, b=-0.3, capability="retrieval", family_id="fam_pin_svd", retrievability=0.8)
    return position_key(features, [("pi_pin_svd_002", 1.0)])


#: The result models whose JSON schema the sweep's schema-keyed sites (A20) hash into a key, by import path.
SCHEMA_KEYED_MODELS = (
    "learnloop.content.synthesis.ai_contracts:SourceSetSynthesis",
    "learnloop.content.synthesis.ai_contracts:SourceUnitInventory",
    "learnloop.content.proposals.ai_contracts:AuthoringProposal",
    "learnloop.content.facet_identity.judge:FacetPartitionVerdict",
    "learnloop.ops.family_proposals:FamilyVerdict",
    "learnloop.ops.contamination.judge:ContaminationJudgment",
    "learnloop.practice_index.contracts:FacetDossierDraft",
    "learnloop.practice_index.contracts:PracticeRerank",
    "learnloop.practice_index.contracts:RelevanceLabels",
    "learnloop.practice_index.contracts:WrittenQueries",
    "learnloop.source_retrieval.contracts:QueryRewrite",
    "learnloop.source_retrieval.passage_cues:CueJudgeResult",
    "learnloop.content.authoring.pf_contracts:SkeletonResult",
    "learnloop.content.authoring.pf_contracts:PanelSolve",
    "learnloop.content.authoring.pf_contracts:FreshnessVerdict",
    "learnloop.content.authoring.pf_contracts:EquivalenceResult",
    "learnloop.content.authoring.pf_contracts:PairwiseVerdict",
    "learnloop.content.authoring.pf_contracts:SpanSupportVerdict",
)


def _import(path: str) -> Any:
    import importlib

    module, _, name = path.partition(":")
    return getattr(importlib.import_module(module), name)


def _schema(path: str) -> Callable[[], Any]:
    return lambda: _import(path).model_json_schema()


def _paid_checkpoint_key() -> Any:
    from learnloop.practice_index.contracts import PracticeRerank
    from learnloop.practice_index.paid import PaidRoute, checkpoint_key

    route = _paid_route(PaidRoute)
    return checkpoint_key(route, purpose="practice_rerank", prompt="pin prompt", result_model=PracticeRerank,
                          output_tokens=256)


def _paid_route(route_type: type) -> Any:
    names = {f.name for f in dataclass_fields(route_type)} if is_dataclass(route_type) else set()
    values = {"provider": "openrouter", "model": "openai/gpt-pin", "reasoning_effort": "low"}
    return route_type(**{k: v for k, v in values.items() if k in names}, **{
        f.name: None for f in dataclass_fields(route_type)
        if f.name not in values and f.default is MISSING and f.default_factory is MISSING})


def _model_settings(profile_name: str, **profile: Any) -> Callable[[], Any]:
    def compute() -> Any:
        from learnloop.ai.execution import model_settings

        config = init_config(ai={"providers": {profile_name: profile}}) if profile else init_config()
        return model_settings(FakeStructuredClient(profile_name, "pin/model", config.ai.providers[profile_name]))
    return compute


def _contract(index: int = 0) -> dict[str, Any]:
    from learnloop.learner.assessment_contracts import compile_assessment_contract

    loaded = vault()
    return compile_assessment_contract(loaded, loaded.practice_items[(ITEM, ITEM_2)[index]["id"]])


def _contract_pin(kind: str) -> Callable[[], Any]:
    def compute() -> Any:
        from learnloop.learner.assessment_contracts import contract_hash
        from learnloop.substrate.activities import card_contract_hash, fingerprint_of

        contract = _contract()
        if kind == "rubric":
            return contract["rubric_content_hash"]
        if kind == "contract":
            return contract_hash(contract)
        return {"card_practice": card_contract_hash(contract, purpose="practice"),
                "card_assessment": card_contract_hash(contract, purpose="assessment"),
                "fingerprint": fingerprint_of(contract)}
    return compute


def _target_hash(item_type: str, entity_id: str) -> Callable[[], Any]:
    def compute() -> Any:
        from learnloop.content.proposals.patches import compute_target_hash

        return compute_target_hash(vault(), item_type, entity_id)
    return compute


def _goal_subset() -> Any:
    from learnloop.goals.goal_contracts import _yaml_subset_from_goal

    return _yaml_subset_from_goal(vault().goals[0])


def _placement_version(config_name: str) -> Callable[[], Any]:
    def compute() -> Any:
        from learnloop.placement.predictor import LiveMasteryPredictor

        repository = SimpleNamespace(mastery_states=lambda: {}, item_parameter_states=lambda: {})
        return LiveMasteryPredictor(SimpleNamespace(config=CONFIGS[config_name]()), repository).version_hash
    return compute


#: The field predictors registered at K0 (``field.predictors._REGISTRY``), each pinned on its own so a failure
#: names the arm. A predictor registered later is not pinned until it is added here.
FIELD_PREDICTORS = (
    "base_rate_lo", "facet_beta", "idea_hier", "lo_general", "lo_general+capability", "lo_general+composite",
    "lo_general+hints", "lo_general+hints:step=0.1", "lo_general+hints:step=0.2", "lo_general+hints:step=0.3",
    "lo_general+practice", "lo_general+retrievability", "lo_general+retrievability:beta=0",
    "lo_general+retrievability:beta=0.5", "lo_general+retrievability:beta=1", "lo_general+transfer",
    "lo_general+tutor_signals", "lo_general+tutor_signals:scale=0.5", "lo_general+tutor_signals:scale=1",
    "lo_general+tutor_signals:scale=2", "mastery_ekf",
)


def _field_version(name: str, config_name: str) -> Callable[[], Any]:
    def compute() -> Any:
        from learnloop.field.answer_signals import AnswerSignalArm
        from learnloop.field.predictors import create_predictor
        from learnloop.field.success_head import LogisticHead

        mastery = CONFIGS[config_name]().mastery
        if name == "success_head":
            return LogisticHead(name=name, config=mastery).version_hash
        if name == "success_head+difficulty":
            return LogisticHead(name=name, difficulty=True, moderated=True, config=mastery).version_hash
        if name.startswith("answer_signal:"):
            return AnswerSignalArm(signal=name.partition(":")[2], base_name="lo_general").version_hash
        return create_predictor(name, config=mastery).version_hash
    return compute


def _field_versions() -> dict[str, Callable[[], Any]]:
    from learnloop.field.answer_signals import CONFIDENCE, HEDGING

    names = (*FIELD_PREDICTORS, "success_head", "success_head+difficulty", f"answer_signal:{CONFIDENCE}",
             f"answer_signal:{HEDGING}")
    return {f"{name}.{config_name}": _field_version(name, config_name) for name in names for config_name in CONFIGS}


def _router_settings(config_name: str) -> Callable[[], Any]:
    def compute() -> Any:
        from learnloop.daily_plan.router_chooser import router_settings

        return router_settings(CONFIGS[config_name]())
    return compute


def _objective_settings(config_name: str) -> Callable[[], Any]:
    def compute() -> Any:
        from learnloop.daily_plan.objective_chooser import objective_settings

        return objective_settings(CONFIGS[config_name]())
    return compute


def _boundary(config_name: str) -> dict[str, Any]:
    """An objective block's boundary identity as ``ObjectiveChooser`` assembles it (``objective_chooser.py``,
    ``identity = {...}`` in the objective-block path), from the production settings at a fixed state and support."""

    from learnloop.daily_plan.objective_chooser import KEY_VERSION, objective_settings
    from learnloop.daily_plan.router_chooser import router_settings

    config = CONFIGS[config_name]()
    return {
        "v": KEY_VERSION, "kind": "objective_block", "plan_id": "plan_pin",
        "state": {"minutes_left": 20.0, "items_left": 4, "lanes": {"new": 10.0, "review": 10.0}, "kind": "daily"},
        "support": [{"candidate_id": "blk_review", "lane": "review"}, "stop_for_today"],
        "staged": "blk_review", "as_of": "att_pin", "version": config.algorithms.algorithm_version,
        "settings": router_settings(config), "objective": objective_settings(config), "ready": ("decider", "llm"),
    }


def _numeric_seed(config_name: str) -> Callable[[], Any]:
    def compute() -> Any:
        from learnloop.daily_plan.objective_chooser import numeric_seed
        from learnloop.daily_plan.router_chooser import _hash

        identity = _boundary(config_name)
        return {"key": _hash(identity), "numeric_seed": numeric_seed(identity)}
    return compute


def _followup_switches(config_name: str) -> Callable[[], Any]:
    def compute() -> Any:
        from learnloop.router_objective_switches import followup_generator_switches, followup_switch_snapshot

        config = CONFIGS[config_name]()
        return {"snapshot": followup_switch_snapshot(config), "generator": followup_generator_switches(config)}
    return compute


def _generator_now(config_name: str) -> Callable[[], Any]:
    def compute() -> Any:
        from learnloop.daily_plan.objective_chooser import generator_now

        config = CONFIGS[config_name]()
        return {"none": generator_now(config), "objective": generator_now(config, "objective_pin")}
    return compute


def _lesson_draw(config_name: str) -> Callable[[], Any]:
    def compute() -> Any:
        from learnloop.daily_plan.lesson_suggestion import draw_inputs
        from learnloop.router import lesson_suggestions as LS

        config = CONFIGS[config_name]()
        state = LS.AcceptanceState()
        context = LS.Context(local_hour=9.5, minutes_left=30.0, reentry=False, days_since_last=1.0)
        candidates = [LS.Candidate(ref="lesson:lo_pin_svd", learning_object_ids=("lo_pin_svd",),
                                   reason="cold_missed", predicted_success=0.42, title="SVD")]
        scored = LS.score(state, context, candidates, k=config.router.k)
        snapshot = LS.canonical_hash(draw_inputs(config, state, context, scored))
        return {"snapshot_hash": snapshot, "seed": LS.seed_for("2026-01-01", snapshot)}
    return compute


def _controller_manifests() -> Any:
    from learnloop.scheduling import constraint_engine as ce
    from learnloop.scheduling.controller_snapshot import _controller_param_manifest_hash

    return {"param_manifest_hash": _controller_param_manifest_hash(),
            "constraint_manifest_hash": ce.manifest()["manifest_hash"]}


def _allowlist_digest() -> Any:
    from learnloop_mobile.allowlist import allowlist_digest

    return allowlist_digest()


def _per_config(make: Callable[[str], Callable[[], Any]]) -> dict[str, Callable[[], Any]]:
    return {name: make(name) for name in CONFIGS}


IDENTITY_SITES: tuple[IdentitySite, ...] = (
    IdentitySite(
        "A1", "facet identity config in the synthesis manifest scope",
        ("src/learnloop/content/facet_identity/judge.py::manifest_identity",),
        "agent_runs.input_context_hash of bootstrap synthesis and append (the manifest hash)",
        "a completed bootstrap or append run is not reused: synthesis is paid again",
        _per_config(_a1_facet_identity)),
    IdentitySite(
        "A2", "facet identity judge route in the synthesis manifest scope",
        ("src/learnloop/content/facet_identity/judge.py::JudgeRoute.as_dict",
         "src/learnloop/content/facet_identity/judge.py::resolve_route"),
        "agent_runs.input_context_hash of bootstrap synthesis and append (the manifest hash)",
        "a completed bootstrap or append run is not reused: synthesis is paid again (prices, policy output "
        "budget and the problem text are identity here)",
        _route_variants()),
    IdentitySite(
        "A3", "graph nominator identity in the synthesis manifest scope",
        ("src/learnloop/content/synthesis/graph_nomination.py::GraphNominator.identity",),
        "agent_runs.input_context_hash of bootstrap synthesis and append (the manifest hash)",
        "a completed bootstrap or append run is not reused: synthesis is paid again",
        {"legacy.embedding_on": _a3_graph_nomination}),
    IdentitySite(
        "A1-A4", "bootstrap synthesis scope and full manifest hash",
        ("src/learnloop/content/synthesis/source_set_synthesis.py::bootstrap_scope",
         "src/learnloop/content/synthesis/synthesis_manifests.py::build_manifest",
         "src/learnloop/content/synthesis/synthesis_manifests.py::agent_run_input_context_hash"),
        "agent_runs.input_context_hash of bootstrap synthesis (synthesis_manifests.manifest_hash)",
        "a completed bootstrap run is not reused: synthesis is paid again",
        {**{f"scope.{name}": _bootstrap_scope(name) for name in CONFIGS},
         # agent_run_input_context_hash(manifest) is the manifest hash itself (the documented cache seam).
         **{f"manifest_hash.{name}": (lambda name=name: _manifest(name)["manifest_hash"]) for name in CONFIGS}}),
    IdentitySite(
        "K3.2", "append synthesis scope without a unit filter",
        ("src/learnloop/content/synthesis/source_append.py::append_scope",),
        "agent_runs.input_context_hash of append (the manifest hash)",
        "a completed append run is not reused: the append is paid again",
        {f"scope.{name}": _append_scope(name) for name in CONFIGS}),
    IdentitySite(
        "K3.4", "append call checkpoint key (asdict of its context in the prompt; a synthesis pass key's shape)",
        ("src/learnloop/content/synthesis/ai_contracts.py::append_reconciliation_prompt",
         "src/learnloop/content/synthesis/source_append.py::append_checkpoint_key"),
        "append call checkpoints (model_checkpoints)",
        "cached append calls miss and are paid again on retry",
        {"append_key": _append_checkpoint_key(False), "append_key.one_facet_per_skill": _append_checkpoint_key(True)}),
    IdentitySite(
        "A4", "task graph hash (blueprint dumps) in the synthesis manifest",
        ("src/learnloop/content/synthesis/synthesis_manifests.py::task_graph_hash",),
        "synthesis_manifests.task_graph_hash, inside the manifest hash",
        "a completed bootstrap or append run is not reused: synthesis is paid again",
        {"fixed_vault": _a4_task_graph}),
    IdentitySite(
        "A6", "PF role call input hash (whole provider profile and schema)",
        ("src/learnloop/ops/pf_calls.py::_profile_settings", "src/learnloop/ops/pf_calls.py::PFCaller.input_hash"),
        "pf checkpoints and ledger input_hash (ops/pf_calls.py lookups)",
        "every PF role call is paid again and earlier ledger ids are orphaned",
        {"skeleton.openrouter": _pf_input_hash("skeleton"), "freshness.deepseek": _pf_input_hash("freshness")}),
    IdentitySite(
        "A7", "family judge pair keys (whole profile, whole items and rubric in the prompt)",
        ("src/learnloop/ops/family_proposals.py::_settings", "src/learnloop/ops/family_proposals.py::pair_passes",
         "src/learnloop/ops/family_proposals.py::propose_families"),
        "family_proposals saved pair verdicts by key",
        "every family pair is judged (paid) again",
        {"pair": _family_pair_keys}),
    IdentitySite(
        "A8", "contamination judge request keys (whole profile)",
        ("src/learnloop/ops/contamination/judge.py::judge_settings",
         "src/learnloop/ops/contamination/judge.py::build_requests"),
        "contamination judgments by request key",
        "every contamination judgment is paid again",
        {"pair": _contamination_keys}),
    IdentitySite(
        "A9", "item revision (whole PracticeItem dump)",
        ("src/learnloop/adaptive_difficulty/feature_audit.py::item_revision",
         "src/learnloop/scheduling/scheduler.py::_practice_item_snapshot"),
        "the llm_v1 forecast receipt key item_unassisted_success:item:{hash} and practice_item_snapshots",
        "every item's llm_v1 forecast is paid again and stored revisions read as stale",
        {"item": lambda: _item_revision()}),
    IdentitySite(
        "A10", "facet content hash (whole EvidenceFacet dump)",
        ("src/learnloop/vault/embedding_recipes.py::facet_content_hash",),
        "facet dossiers' source hash (db/stores/practice_index.py) and neighbours' source_hash",
        "every facet dossier looks missing and is paid again, with its neighbours'",
        {"facet": lambda: _facet_content_hash("fct_svd_define"),
         "facet_defaults": lambda: _facet_content_hash("fct_svd_orthogonal")}),
    IdentitySite(
        "A11-A12", "approach map structure hash and prompt (TraceContract, RequiredMethod dumps)",
        ("src/learnloop/hints/map_seeds.py::structure_hash", "src/learnloop/hints/map_builder.py::build_prompt"),
        "approach maps' structure hash (hints/map_builder.py staleness checks)",
        "every approach map is stale and rebuilt as a paid call",
        {"structure_hash": lambda: _map_seeds().structure_hash, "prompt": lambda: _map_prompt()}),
    IdentitySite(
        "A13", "canonical ingest prompt (asdict of its context)",
        ("src/learnloop/content/pipeline/ai_contracts.py::canonical_ingest_prompt",
         "src/learnloop/content/pipeline/source_ingestion.py::_run_ingest_windows"),
        "the legacy ingest window checkpoint key (content_key of prompt, schema, provider, model)",
        "cached ingest windows miss and are paid again",
        {"prompt": _canonical_ingest_prompt}),
    IdentitySite(
        "A14", "source set synthesis pass key (asdict of its context in the prompt)",
        ("src/learnloop/content/synthesis/ai_contracts.py::source_set_synthesis_prompt",
         "src/learnloop/content/synthesis/source_set_synthesis.py::_synthesis_pass_key"),
        "synthesis pass checkpoints (model_checkpoints)",
        "cached synthesis passes miss and are paid again",
        {"pass_key": _synthesis_pass_key(False), "pass_key.one_facet_per_skill": _synthesis_pass_key(True)}),
    IdentitySite(
        "A15", "source unit inventory window key (asdict of its context in the prompt)",
        ("src/learnloop/content/synthesis/ai_contracts.py::source_unit_inventory_prompt",
         "src/learnloop/content/synthesis/source_unit_inventory.py::inventory_window_key"),
        "inventory window checkpoints (model_checkpoints)",
        "cached inventory windows miss and are paid again",
        {"window_key": _inventory_window_key}),
    IdentitySite(
        "K2.1a", "legacy ingest window checkpoint key (rendered prompt and schema, provider and model)",
        ("src/learnloop/content/pipeline/source_ingestion.py::legacy_window_key",),
        "legacy ingest window checkpoints (model_checkpoints)",
        "cached ingest windows miss and are paid again",
        {"window_key": _legacy_window_key}),
    IdentitySite(
        "K2.1b", "facet identity judge checkpoint keys (the LLM judge's carries its output budget)",
        ("src/learnloop/content/facet_identity/judge.py::LLMGroupJudge.checkpoint_key",
         "src/learnloop/content/facet_identity/judge.py::DeciderGroupJudge.checkpoint_key"),
        "facet identity judge checkpoints (model_checkpoints)",
        "every facet identity group is judged (paid) again",
        {"llm": _facet_judge_key("llm"), "llm.reasoning_effort": _facet_judge_key("llm", "high"),
         "decider": _facet_judge_key("decider")}),
    IdentitySite(
        "K2.1c", "GLM-OCR window checkpoint key (file, pages, backend, models)",
        ("src/learnloop/ingest/extractors/glm_ocr.py::GlmOcrDocumentExtractor._checkpoint_key",),
        "GLM-OCR window checkpoints (model_checkpoints)",
        "every hosted OCR window is read (paid) again",
        {"window_key": _glm_ocr_window_key}),
    IdentitySite(
        "K2.1d", "concept graph structuring checkpoint key (asdict of its context in the prompt; a pass key's shape)",
        ("src/learnloop/content/synthesis/ai_contracts.py::concept_graph_structuring_prompt",
         "src/learnloop/content/synthesis/source_set_synthesis.py::structuring_checkpoint"),
        "concept graph structuring checkpoints (model_checkpoints)",
        "a cached structuring answer misses and is paid again on retry",
        {"key": _structuring_key(False), "key.nominated": _structuring_key(True)}),
    IdentitySite(
        "A19", "family item input hash and the family plan dump",
        ("src/learnloop/substrate/families.py::family_item_input",
         "src/learnloop/substrate/families.py::family_item_input_hash",
         "src/learnloop/substrate/families.py::apply_family", "src/learnloop/substrate/families.py::attach_to_family",
         "src/learnloop/vault/hashes.py::activity_family_hash", "src/learnloop/ops/pf_publish.py::judged_inputs"),
        "accepted family judgments (substrate/families.py) and family_proposals.plan_json",
        "accepted family judgments no longer bind (judges re-run, paid); in-flight proposals are refused at apply",
        {"item": _family_input("item"), "family": _family_input("family"),
         "publish_judged_inputs": _family_input("publish")}),
    IdentitySite(
        "A20", "schema-keyed result models (model_json_schema in a checkpoint or input hash)",
        ("src/learnloop/practice_index/paid.py::checkpoint_key", "src/learnloop/practice_index/paid.py::receipt_answer",
         "src/learnloop/content/facet_identity/judge.py::LLMGroupJudge.checkpoint_key",
         "src/learnloop/source_retrieval/queries.py::rewrite_query",
         "src/learnloop/practice_index/listwise.py::request_input_hash",
         "src/learnloop/practice_index/evaluation.py::_generate_queries",
         "src/learnloop/practice_index/evaluation.py::_label_all", "src/learnloop/practice_index/evaluation.py::_score",
         "src/learnloop/practice_index/dossiers.py::generate_dossiers"),
        "every paid checkpoint and receipt keyed by its result schema",
        "the paid answers keyed by that schema are paid again (a docstring or Field description edit moves it)",
        {**{f"schema.{path.rpartition(':')[2]}": _schema(path) for path in SCHEMA_KEYED_MODELS},
         "paid.checkpoint_key": _paid_checkpoint_key}),
    IdentitySite(
        "A22", "model settings in checkpoint keys (chosen profile attributes)",
        ("src/learnloop/ai/execution.py::model_settings",),
        "every checkpoint key that carries model_settings (synthesis passes, inventory windows, ...)",
        "a removed profile attribute silently reads None and every such checkpoint misses (paid again)",
        {"openrouter": _model_settings("openrouter"), "chatgpt_medium": _model_settings("chatgpt_medium"),
         "deepseek_flash": _model_settings("deepseek_flash"),
         # Every attribute model_settings reads set, so a renamed one (read as None) moves this pin.
         "openrouter.every_setting": _model_settings(
             "openrouter", base_url="https://pin.invalid/v1", reasoning_effort="high", thinking="enabled",
             response_format="json_object")}),
    IdentitySite(
        "B1-B3", "assessment contract: rubric content hash, contract hash, card contract hash and fingerprint",
        ("src/learnloop/learner/assessment_contracts.py::compile_assessment_contract",
         "src/learnloop/learner/assessment_contracts.py::contract_hash",
         "src/learnloop/substrate/activities.py::card_contract_hash",
         "src/learnloop/substrate/activities.py::fingerprint_of",
         "src/learnloop/field/outcomes.py::_revision"),
        "frozen contracts (attempts._froze), field outcomes, contract dedupe, card versions and held-out checks",
        "history is reinterpreted silently: frozen contracts stop matching, attempts fall to excluded, a new card "
        "version per item and near-clone checks miss old exposures (an unseen-item leak)",
        {"rubric_content_hash": _contract_pin("rubric"), "contract_hash": _contract_pin("contract"),
         "card": _contract_pin("card")}),
    IdentitySite(
        "B4-B5", "reference content hash and practice item hash",
        ("src/learnloop/db/stores/source_service.py::reference_content_hash",
         "src/learnloop/attempts/attempts.py::GradedContract.graded_reference_contents",
         "src/learnloop/vault/hashes.py::practice_item_hash"),
        "answer-key checks (applicable_checks) and item state rows (substrate/state_sync.py)",
        "answer-key checks no longer bind; every item's state row is rewritten and hint assists go stale",
        {"reference_content_hash": lambda: _reference_hash(), "practice_item_hash": lambda: _item_hash()}),
    IdentitySite(
        "B6", "proposal target hashes (exclude_none=False dumps of six entity types)",
        ("src/learnloop/content/proposals/patches.py::compute_target_hash",
         "src/learnloop/content/synthesis/source_set_synthesis.py::_normalize"),
        "expected_target_hash on update/deactivate proposal items, checked at accept",
        "every pending update or deactivate proposal is refused at accept",
        {kind: _target_hash(kind, entity) for kind, entity in (
            ("learning_object", "lo_pin_svd"), ("practice_item", "pi_pin_svd_001"),
            ("concept", "singular_value_decomposition"), ("error_type", "err_eigen_confusion"),
            ("facet", "fct_svd_define"), ("rubric", "pi_pin_svd_001"))}),
    IdentitySite(
        "B7", "goal contract YAML subset (GoalFacetScope and GoalExamConfig dumps)",
        ("src/learnloop/goals/goal_contracts.py::_yaml_subset_from_goal",),
        "detect_contract_drift against the confirmed head",
        "every confirmed goal reports drift",
        {"goal": _goal_subset}),
    IdentitySite(
        "B9", "controller parameter and constraint manifests",
        ("src/learnloop/scheduling/controller_snapshot.py::_controller_param_manifest_hash",),
        "controller snapshot rows, the epsilon tie-break seed (staged_policy) and decision_params_hash",
        "new controller snapshot rows and a different tie-break seed at a fixed input",
        {"manifests": _controller_manifests}),
    IdentitySite(
        "B10", "phone allowlist digest",
        ("src/learnloop_mobile/allowlist.py::allowlist_digest",),
        "the installed PWA's embedded digest (apps/learnloop-mobile/src/shell/freshness.ts)",
        "the installed phone app reports stale until the PWA is rebuilt (an intended coupling: rebuild the PWA)",
        {"digest": _allowlist_digest}),
    IdentitySite(
        "C1", "placement predictor version hash (whole MasteryConfig)",
        ("src/learnloop/placement/predictor.py::LiveMasteryPredictor.__init__",),
        "forecaster version labels, the valuation retention state_hash and the voi_forecasts receipt key",
        "VOI receipts are written twice instead of deduped and forecaster versions split in reports (H6: put "
        "mastery.irt.difficulty_from_prior and difficulty_prior_scale in RETIRED_FIELDS when it removes them)",
        _per_config(_placement_version)),
    IdentitySite(
        "C2", "field predictor version hashes (ArmConstants, priors, mastery view)",
        ("src/learnloop/field/predictors.py::LoGeneral.__init__",
         "src/learnloop/field/success_head.py::LogisticHead.__init__",
         "src/learnloop/field/answer_signals.py::AnswerSignalArm.__init__"),
        "field evaluation arm hashes, eval harness and forecast version labels",
        "an unchanged predictor reads as a new version (H6: RETIRED_FIELDS for the mastery.irt fields it removes)",
        _field_versions()),
    IdentitySite(
        "C2p", "cached LLM probability position key (asdict of ItemFeatures)",
        ("src/learnloop/field/probability_arms.py::position_key",),
        "the cached probability arms' lookups and field/probability_prep.py's prepared positions",
        "every cached LLM probability misses: the probability arms are prepared (paid) again",
        {"position": _position_key}),
    IdentitySite(
        "C3", "router settings and the numeric policy's seed (whole RouterWeights)",
        ("src/learnloop/daily_plan/router_chooser.py::router_settings",
         "src/learnloop/daily_plan/objective_chooser.py::numeric_seed"),
        "the prefetch boundary key and the numeric policy's rollout RNG (router_objective/value.py)",
        "different draws at a fixed input (P-draw fails) and prefetched decisions miss",
        {**{f"router_settings.{name}": _router_settings(name) for name in CONFIGS},
         **{f"boundary.{name}": _numeric_seed(name) for name in CONFIGS}}),
    IdentitySite(
        "C4", "objective settings and the follow-up switch snapshot (the kill-switch list D7 deletes)",
        ("src/learnloop/daily_plan/objective_chooser.py::objective_settings",
         "src/learnloop/router_objective_switches.py::followup_switch_snapshot"),
        "the prefetch boundary key and numeric_seed (less SEED_NEUTRAL_SWITCHES)",
        "different numeric draws at a fixed input; D7 decides per switch whether to keep its served value or fold "
        "the change into E8",
        {**{f"objective_settings.{name}": _objective_settings(name) for name in CONFIGS},
         **{f"switches.{name}": _followup_switches(name) for name in CONFIGS}}),
    IdentitySite(
        "C5", "RO6 generator key (FOLLOWUP_GENERATOR_SWITCHES)",
        ("src/learnloop/daily_plan/objective_chooser.py::generator_now",
         "src/learnloop/router_objective/tail_data.py::generator_key"),
        "the learned tail's generator grouping and change points (router_objective/tail_data.py)",
        "an RO6 generator change point against all logged history: the learned tail starts over",
        _per_config(_generator_now)),
    IdentitySite(
        "C6", "lesson suggestion draw snapshot and seed (whole RouterWeights)",
        ("src/learnloop/daily_plan/lesson_suggestion.py::draw_inputs",
         "src/learnloop/router/lesson_suggestions.py::seed_for"),
        "the day's lesson card draw (seed) and its row's snapshot_hash",
        "a different card is drawn at a fixed input",
        _per_config(_lesson_draw)),
)


def _item_revision() -> Any:
    from learnloop.adaptive_difficulty.feature_audit import item_revision

    return item_revision(item())[0]


def _facet_content_hash(facet_id: str) -> Any:
    from learnloop.vault.embedding_recipes import facet_content_hash

    return facet_content_hash(vault().evidence_facets[facet_id])


def _map_prompt() -> Any:
    from learnloop.hints.map_builder import build_prompt

    return build_prompt(_map_seeds())


def _reference_hash() -> Any:
    from learnloop.vault.hashes import reference_content_hash

    return reference_content_hash(item())


def _item_hash() -> Any:
    from learnloop.vault.hashes import practice_item_hash

    return practice_item_hash(item())


def pin_names() -> list[str]:
    return sorted(f"{site.id}.{name}" for site in IDENTITY_SITES for name in site.pins)


def site_for(pin: str) -> tuple[IdentitySite, Callable[[], Any]]:
    for site in IDENTITY_SITES:
        for name, compute in site.pins.items():
            if f"{site.id}.{name}" == pin:
                return site, compute
    raise KeyError(pin)


def current_digests() -> dict[str, str]:
    return {pin: digest(site_for(pin)[1]()) for pin in pin_names()}


# -- shape pins -------------------------------------------------------------------------------------------------

#: Each type a compared identity dumps whole (sweep §1E), with the sites that dump it. Nested pydantic models and
#: dataclasses are pinned too, under the root that reaches them.
SHAPE_ROOTS: dict[str, tuple[str, ...]] = {
    "learnloop.config.schema:FacetIdentityConfig": ("A1",),
    "learnloop.config.schema:GraphNominationConfig": ("A3",),
    "learnloop.config.schema:MasteryConfig": ("C1", "C2"),
    "learnloop.config.schema:RouterWeights": ("C3", "C6"),
    "learnloop.config.schema:AIProviderConfig": ("A6", "A7", "A8", "A22"),
    "learnloop.content.facet_identity.judge:Pricing": ("A2",),
    "learnloop.vault.models:PracticeItem": ("A9", "A19", "B1-B3", "B4-B5", "B6", "A11-A12"),
    "learnloop.vault.models:EvidenceFacet": ("A10", "B6", "A3"),
    "learnloop.vault.models:LearningObject": ("B6", "A4"),
    "learnloop.vault.models:Concept": ("B6",),
    "learnloop.vault.models:ErrorType": ("B6",),
    "learnloop.vault.models:ActivityFamily": ("A19",),
    "learnloop.vault.models:GoalFacetScope": ("B7",),
    "learnloop.vault.models:GoalExamConfig": ("B7",),
    "learnloop.field.predictors:ArmConstants": ("C2",),
    "learnloop.field.success_head:HeadPriors": ("C2",),
    "learnloop.field.types:ItemFeatures": ("C2p",),
    "learnloop.vault.models:Blueprint": ("A4",),
    # C3's support rows carry ReadingTarget.as_dict (an asdict); the boundary pin's fixed support has none.
    "learnloop.daily_plan.types:ReadingTarget": ("C3",),
    "learnloop.content.pipeline.ai_contracts:CanonicalIngestContext": ("A13",),
    "learnloop.content.synthesis.ai_contracts:SourceSetSynthesisContext": ("A14",),
    "learnloop.content.synthesis.ai_contracts:AppendReconciliationContext": ("K3.4",),
    "learnloop.content.synthesis.ai_contracts:SourceUnitInventoryContext": ("A15",),
    "learnloop.content.synthesis.ai_contracts:ConceptGraphContext": ("K2.1d",),
}


def _type_name(tp: Any) -> str:
    return f"{tp.__module__}:{tp.__qualname__}"


def _annotation(annotation: Any) -> str:
    text = repr(annotation) if not isinstance(annotation, type) else annotation.__qualname__
    for prefix in ("typing.", "learnloop.vault.models.", "learnloop.config.schema.", "pydantic.types."):
        text = text.replace(prefix, "")
    return text


def _default(value: Any) -> str:
    if isinstance(value, BaseModel):
        return f"{type(value).__qualname__}({json.dumps(value.model_dump(mode='json'), sort_keys=True)})"
    try:
        return json.dumps(value, sort_keys=True, default=str)
    except (TypeError, ValueError):
        return repr(value)


def _nested_types(annotation: Any) -> list[type]:
    import typing

    found: list[type] = []
    if isinstance(annotation, type) and (issubclass(annotation, BaseModel) or is_dataclass(annotation)):
        found.append(annotation)
    for arg in typing.get_args(annotation):
        found.extend(_nested_types(arg))
    return found


def _shape_of(tp: type) -> tuple[list[str], list[type]]:
    lines: list[str] = []
    nested: list[type] = []
    if isinstance(tp, type) and issubclass(tp, BaseModel):
        extra = tp.model_config.get("extra")
        lines.append(f"(extra={extra})")
        for name, info in tp.model_fields.items():
            if info.is_required():
                default = "required"
            elif info.default_factory is not None:
                default = "= " + _default(info.default_factory())
            else:
                default = "= " + _default(info.default)
            excluded = " exclude_if" if getattr(info, "exclude_if", None) is not None else ""
            lines.append(f"{name}: {_annotation(info.annotation)} {default}{excluded}")
            nested.extend(_nested_types(info.annotation))
        from learnloop.config.retired import RETIRED_FIELDS

        for retired in RETIRED_FIELDS:
            if retired.model == tp.__name__:
                lines.append(f"retired {'.'.join(retired.path)}: {_annotation(retired.annotation)} = "
                             f"{_default(retired.default)}")
        for sub in sorted(tp.__subclasses__(), key=_type_name):
            lines.append(f"subclass {_type_name(sub)}")
            nested.append(sub)
    else:
        import typing

        try:
            hints = typing.get_type_hints(tp)
        except (NameError, TypeError):
            hints = {}
        for f in dataclass_fields(tp):
            if f.default is not MISSING:
                default = "= " + _default(f.default)
            elif f.default_factory is not MISSING:
                default = "= " + _default(f.default_factory())
            else:
                default = "required"
            annotation = hints.get(f.name, f.type)
            lines.append(f"{f.name}: {annotation if isinstance(annotation, str) else _annotation(annotation)} {default}")
            nested.extend(_nested_types(annotation))
    return lines, nested


@cache
def current_shapes() -> dict[str, dict[str, Any]]:
    """``{type: {"fields": [...], "sites": [...]}}`` for every shape root and every type nested in one."""

    out: dict[str, dict[str, Any]] = {}
    todo = [(_import(root), sites) for root, sites in SHAPE_ROOTS.items()]
    while todo:
        tp, sites = todo.pop()
        name = _type_name(tp)
        if name in out:
            out[name]["sites"] = sorted({*out[name]["sites"], *sites})
            continue
        lines, nested = _shape_of(tp)
        out[name] = {"fields": lines, "sites": sorted(sites)}
        todo.extend((sub, sites) for sub in nested)
    return dict(sorted(out.items()))


# -- the AST coverage check -------------------------------------------------------------------------------------

#: Functions the AST check flags (a model_dump, asdict, model_json_schema or json.dumps of a config, whose value
#: reaches a hash, seed, manifest or structured-prompt call in the same function) that are not pinned above: each
#: with why its dump may move. ``path::qualname``.
PROMPT_REASON = ("a structured prompt's context: a field change changes what the model is sent, so the request is "
                 "new on purpose (sweep §1A A13-A15: a rename alone re-pays, which a prompt bump intends)")
PROVENANCE_REASON = "provenance only: stored with a run or report and never looked up or compared"
HARNESS_REASON = "an eval harness or experiment's own key: re-running it re-pays only the harness"

PROVENANCE_ONLY: dict[str, str] = {
    "src/learnloop/adaptive_difficulty/replay.py::events_fingerprint":
        "a replay's in-process fingerprint of the events it read; recomputed every replay, never stored as a key",
    "src/learnloop/attempts/grading.py::validate_codex_grading_proposal":
        "the hash is a quoted span's (quote_hash over the learner's quoted text), stored with the grade; the scan "
        "reaches it through the dumped dict the quote is read from",
    "src/learnloop/content/authoring/ai_contracts.py::concept_animation_prompt": PROMPT_REASON,
    "src/learnloop/content/authoring/ai_contracts.py::video_storyboard_prompt": PROMPT_REASON,
    "src/learnloop/content/proposals/ai_contracts.py::authoring_prompt": PROMPT_REASON,
    "src/learnloop/content/proposals/method_phrasing.py::judge_prompt": PROMPT_REASON,
    "src/learnloop/content/proposals/proposals.py::persist_authoring_proposal":
        "agent_runs.input_context_hash of purpose 'authoring', which nothing looks up (only canonical ingest, "
        "synthesis and append read completed_agent_run*_by_context; sweep §1D)",
    "src/learnloop/content/synthesis/ai_contracts.py::vault_epigraphs_prompt": PROMPT_REASON,
    "src/learnloop/curriculum/ai_contracts.py::rung_backfill_prompt": PROMPT_REASON,
    "src/learnloop/curriculum/ai_contracts.py::depth_edge_instance_prompt": PROMPT_REASON,
    "src/learnloop/daily_plan/engine.py::_config_hash":
        "daily_plans.config_hash: provenance of the plan row (sweep §1D)",
    "src/learnloop/diagnosis/ai_contracts.py::probe_instance_surfaces_prompt": PROMPT_REASON,
    "src/learnloop/diagnosis/ai_contracts.py::probe_dialogue_turn_prompt": PROMPT_REASON,
    "src/learnloop/diagnosis/ai_contracts.py::probe_family_trials_prompt": PROMPT_REASON,
    "src/learnloop/diagnosis/ai_contracts.py::followup_probe_prompt": PROMPT_REASON,
    "src/learnloop/diagnosis/grading_hardcases.py::HardCase.content_key": HARNESS_REASON + " (sweep A16)",
    "src/learnloop/diagnosis/split/reports.py::m2_report": PROVENANCE_REASON + " (a report's config_hash)",
    "src/learnloop/diagnosis/text_gaps/pipeline.py::_create":
        "`_seed` authors a seed practice item for the created prerequisite: no hash or random seed (the scan matches "
        "the name)",
    "src/learnloop/experiments/contextual_embeddings/answers.py::answer_and_judge": HARNESS_REASON,
    "src/learnloop/experiments/contextual_embeddings/callers.py::checkpoint_key": HARNESS_REASON + " (sweep A18)",
    "src/learnloop/experiments/contextual_embeddings/corpus.py::_unit": HARNESS_REASON,
    "src/learnloop/experiments/contextual_embeddings/pins.py::pins_fingerprint": HARNESS_REASON,
    "src/learnloop/hints/outcome.py::_write":
        "a judgment_ledger row's input_hash for the hint outcome task, which nothing looks up by input_hash",
    "src/learnloop/hints/writer.py::build_prompt": PROMPT_REASON,
    "src/learnloop/ingest/hashing.py::extraction_result_hash":
        "provenance of an extraction's output (whole DocumentIR), never a lookup key (sweep §1D)",
    "src/learnloop/instructional/tools.py::execute_tool":
        "a tool call's result_ref over the retrieval manifest it returned, stored with the call",
    "src/learnloop/instructional/tools.py::request_tool":
        "a refused request's judgment_ledger input_hash over its own arguments, which nothing looks up",
    "src/learnloop/ops/contamination/report.py::contamination_report": PROVENANCE_REASON + " (a report's config_hash)",
    "src/learnloop/ops/embedding_backfill.py::backfill_embeddings": PROVENANCE_REASON + " (a report's config_hash)",
    "src/learnloop/ops/embedding_compare.py::run_compare":
        HARNESS_REASON + "; its config_hash goes through identity_dump (tests/test_retired_config_identities.py)",
    "src/learnloop/ops/pf_generation.py::_FamilyRun._generate_proposals":
        "candidate ids hash the request, path, provider and the call's input hash (A6, pinned), not the dumped "
        "proposal, which is stored; the scan ignores statement order",
    "src/learnloop/ops/pf_generation.py::_FamilyRun._generate_source_anchored":
        "candidate ids hash the request and the call's input hash (A6, pinned), not the dumped proposal, which is "
        "stored; the scan ignores statement order",
    "src/learnloop/ops/pf_generation.py::generate_practice": PROVENANCE_REASON + " (a report's config_hash)",
    "src/learnloop/placement/report.py::placement_report": PROVENANCE_REASON + " (the placement report)",
    "src/learnloop/projects/ai_contracts.py::probe_authoring_prompt": PROMPT_REASON,
    "src/learnloop/projects/ai_contracts.py::closed_book_prompt": PROMPT_REASON,
    "src/learnloop/projects/ai_contracts.py::probe_grading_prompt": PROMPT_REASON,
    "src/learnloop/reader/ai_contracts.py::reading_passage_check_prompt": PROMPT_REASON,
    "src/learnloop/reader/ai_contracts.py::reader_preset_synthesis_prompt": PROMPT_REASON,
    "src/learnloop/reader/ai_contracts.py::reading_quick_check_prompt": PROMPT_REASON,
    "src/learnloop/reader/ai_contracts.py::reading_active_prompt": PROMPT_REASON,
    "src/learnloop/router_objective/decision_state.py::_config_hash":
        "decision_state versions.config: provenance of the decision row (sweep §1D)",
    "src/learnloop/scheduling/scheduler.py::_fill_offer_trace":
        "the config dumps are the trace's stored config_snapshot (provenance); the hashed draw seed is the label, "
        "session, date and candidate ids, not a dump",
    "src/learnloop/substrate/canonical_projection_rollout.py::_vault_digest":
        "an in-process memo of the vault during one rollout; no persisted consumer (sweep §1D)",
    "src/learnloop/tutor/ai_contracts.py::teach_back_question_prompt": PROMPT_REASON,
    "src/learnloop/tutor/ai_contracts.py::teach_back_authoring_prompt": PROMPT_REASON,
    "src/learnloop/tutor/ai_contracts.py::promotion_analysis_prompt": PROMPT_REASON,
    "src/learnloop/vault/writer.py::upsert_facet":
        "writes the dumped facet to facets.yaml; its semantic_fingerprint is computed first from an explicit field "
        "list (vault/facet_fingerprint.py). The scan ignores statement order, so the list the dump joins taints the "
        "earlier read",
    "src/learnloop/workbench/check.py::build_prompt": PROMPT_REASON,
    "src/learnloop_sidecar/handlers/capture.py::_request_hash":
        "a capture retry's check against its own pending request (same capture id): a request-model change refuses "
        "only a retry in flight across an upgrade",
}
