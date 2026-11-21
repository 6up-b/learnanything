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
computes the identity; where production builds the identity inline (the router's boundary identity), the pin drives
the production method that assembles it and captures the dictionary it hashes (C3b).

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

from tests import diagnosis_identity_helpers as diagnosis_pins

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
#: The configs the router objective's boundary and generator identities (C3-C5) are pinned for: a new vault's. The
#: tagless ``legacy`` config is refused at every door, so an arm for it would pin an identity no vault computes.
OBJECTIVE_CONFIGS: tuple[str, ...] = ("init",)


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


def _inventory_row_key() -> Any:
    from learnloop.content.synthesis.source_unit_inventory import inventory_row_key

    return inventory_row_key(provider="codex", model="fake-model", schema_version=1)


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


def _section_authoring_key() -> Any:
    from learnloop.content.proposals.ai_contracts import AuthoringContext
    from learnloop.content.proposals.proposals import _authoring_checkpoint

    context = AuthoringContext(
        vault_root=str(VAULT_ROOT), source_ids=["src_pin"], instructions="Write three questions for lo_pin_svd.",
        subjects=["linear-algebra"], source_refs=[{"ref_type": "note", "ref_id": "src_pin"}],
        learning_objects=[{"id": "lo_pin_svd", "title": "SVD"}],
    )
    return _authoring_checkpoint(None, FakeStructuredClient(), context).key


def _section_questions_key() -> Any:
    from learnloop.content.authoring.practice_generation import section_questions_key

    return section_questions_key(FakeStructuredClient(), ["lo_pin_svd"],
                                 [{"ref_type": "note", "ref_id": "src_pin"}], "reader_section_completed:u1")


def _topic_questions_key() -> Any:
    from learnloop.content.authoring.practice_generation import topic_questions_key

    return topic_questions_key("lo_pin_svd", [{"ref_type": "canonical_source", "ref_id": "reader_citation:ext_pin:lo_pin_svd:s1-s2",
                                               "span_ids": ["s1", "s2"], "learning_object_ids": ["lo_pin_svd"]}])


def _persona_fire_key() -> Any:
    from learnloop.diagnosis.diagnostic_gate import fire_checkpoint

    context = {"answer": "Q^T x is the coordinate vector", "expected": "Qx is the coordinate vector",
               "payload": {"id": "pi_pin_svd_001", "prompt": "Which of Qx / Q^T x is the coordinate vector?"}}
    return fire_checkpoint(None, FakeStructuredClient(), context, trial="belief_declared").key


def _epigraph_key() -> Any:
    from learnloop.content.synthesis.ai_contracts import VaultEpigraphContext
    from learnloop.content.synthesis.vault_epigraphs import epigraph_checkpoint

    context = VaultEpigraphContext(
        subject_id="linear-algebra", source_set_id="set_pin", mode="bootstrap", subject_title="Linear Algebra",
        source_set_title="Notes", brief={"depth": "intro"}, summary="SVD", concepts=["SVD"],
        claims=["A = U S V^T"], learning_objects=["Compute an SVD"], recent_epigraphs=["Rank is destiny."])
    return epigraph_checkpoint(None, FakeStructuredClient(), context).key


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
    """A hand-written boundary identity with the production settings at a fixed state and support: what ``C3.boundary``
    holds ``numeric_seed`` and ``_hash`` to. It is not what the chooser assembles (``C3b`` pins that)."""

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


def _chooser_boundary() -> Any:
    """The identity ``ObjectiveChooser.choose`` assembles for an objective block, captured as the chooser hashes it, on a
    new vault at the head and two fixed candidates: so a field the chooser adds, drops or reorders (its own literal, a
    candidate's ``log_row``, the settings it reads) moves the pin, which ``_boundary``'s hand-built dictionary cannot.

    What it holds is the numeric seed's input: the last identity hashed is the one ``numeric_seed`` reduces (less the
    seed-neutral switches), so its ``identity`` and ``key`` are that reduced identity and its hash, not the boundary
    key. A field only the key names (a seed-neutral switch) can leave this pin as it was; ``start_key`` pins the key
    itself."""

    seen, _started = _run_chooser_boundary()
    identity = seen[-1]
    from learnloop.daily_plan import objective_chooser as OC

    return {"identity": identity, "key": OC._hash(identity), "numeric_seed": OC.numeric_seed(identity)}


def _chooser_start_key() -> Any:
    """The boundary key ``ObjectiveChooser.choose`` hands to its job's start (``_start_objective``) for the same fixed
    boundary as ``_chooser_boundary``: the key a prefetched job is looked up by at the serve, the full identity hashed
    (every seed-neutral switch included)."""

    _seen, started = _run_chooser_boundary()
    assert len(started) == 1, started
    return {"key": started[0]}


def _mix_seed() -> Any:
    """The mix's (and the stop coin's) seed for a fixed boundary key and decision id through production's own
    derivation (``objective_seeds.mix_seed`` with no runtime seed, so ``mix.seed_for``), unwrapped: the pinned draws
    map each distinct seed to its first-seen ordinal, which an argument swap keeps."""

    from types import SimpleNamespace

    from learnloop.daily_plan.objective_seeds import mix_seed

    return {"seed": mix_seed(SimpleNamespace(seed=None), "boundary-key-pin", "01JPINDECISION0000000000000")}


def _run_chooser_boundary() -> tuple[list[dict[str, Any]], list[str]]:
    """Run ``ObjectiveChooser.choose`` (``start_only``) on the fixed boundary: every objective-block identity it hashed,
    in order, and the keys it handed to ``_start_objective`` (stubbed: nothing starts)."""

    import tempfile

    from learnloop.daily_plan import objective_chooser as OC
    from learnloop.daily_plan import objective_seeds as OS
    from learnloop.daily_plan.router_runtime import DecisionPending
    from learnloop.daily_plan.types import BlockCandidate, PlanState
    from learnloop.vault.paths import VaultPaths
    from learnloop.db.repositories import Repository
    from learnloop.vault.loader import load_vault

    from tests.helpers import create_basic_vault
    from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime

    def candidate(candidate_id: str, lane: str, minutes: float, value: float) -> BlockCandidate:
        return BlockCandidate(
            candidate_id=candidate_id, lane=lane, action="maintain", subtype=None, learning_object_ids=("lo_pin",),
            item_ids=(f"pi_{candidate_id}",), reading=None, est_minutes=minutes, planner_value=value, reason="pin",
            annotations={"reason_code": "maintain", "reversible": True})

    state = PlanState(plan_id="plan_pin", kind="normal", minutes_budget=25.0, minutes_left=20.0,
                      lane_minutes_left={"maintain": 10.0, "new": 10.0}, days_since_last_activity=0, streak_days=1,
                      current_block_id=None, items_left=4)
    seen: list[dict[str, Any]] = []
    started: list[str] = []
    real_hash = OC._hash

    def recording(value: Any) -> str:
        if isinstance(value, dict) and value.get("kind") == "objective_block":
            seen.append(copy.deepcopy(value))
        return real_hash(value)

    with tempfile.TemporaryDirectory() as root:
        paths = create_basic_vault(Path(root) / "vault")
        vault = load_vault(paths.root)
        repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
        runtime = fake_runtime(decider=FakeDecider(), llm=FakeLLM())
        # start_only: the chooser assembles the identity, starts the boundary's job (stubbed) and leaves the decision open.
        chooser = OC.ObjectiveChooser(vault, repository, runtime, start_only=True)
        chooser._start_objective = lambda key, *args, **kwargs: started.append(key)  # type: ignore[method-assign]
        # Both hashes the identity reaches are recorded, the key's and the numeric seed's (its own module), so the
        # last one recorded is the seed's reduced identity, as when the two sat in one module.
        OC._hash = OS._hash = recording
        try:
            chooser.choose(state, [candidate("blk_a", "maintain", 5.0, 0.5), candidate("blk_b", "new", 6.0, 0.4)])
        except DecisionPending:
            pass
        finally:
            OC._hash = OS._hash = real_hash
    return seen, started


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


# -- figures (K10.4): the reuse key, the request identity, the prompt versions, the contracts ---------------------

#: A pressed figure's fixed input: the selection, what the author is sent around it, a crop's digest and a region.
FIGURE_PASSAGE = [{"span_id": "s3", "block_type": "Equation", "text": "f_X(x) = p\\lambda e^{\\lambda x} for x < 0"}]
FIGURE_AROUND = [{"span_id": "s2", "block_type": "Text", "text": "The two-sided exponential has density f_X."},
                 {"span_id": "s4", "block_type": "Text", "text": "Hence P(X <= 0) = p, whatever lambda is."}]
FIGURE_IMAGE = "ab" * 32
FIGURE_REGION = {"span_id": "s5", "bbox": [100.0, 100.0, 400.0, 300.0]}
FIGURE_RUNTIME = "manim Manim Community v0.19.1; bwrap-pin"
FIGURE_MENU = ("grammar", "sketch", "manim")
FIGURE_GOAL = "show how p splits the mass either side of zero"
#: What the author is sent about the learner (only its hash is in the key).
FIGURE_LEARNER = {"topics": [{"learning_object_id": "lo_pin_svd", "title": "Two-sided exponential",
                              "status": "practising", "open_gaps": ["mixes up p and 1 - p"]}],
                  "recent_answers": [{"question": "P(X <= 0)?", "answer": "1 - p", "graded": "incorrect"}]}


def _figure_request(**changes: Any) -> Any:
    from learnloop.figures.request import FigureRequest

    return FigureRequest(**{"extraction_id": "ext_pin", "span_ids": ["s3"], **changes})


def _figure_context() -> Any:
    from learnloop.figures.grounding import SourceContext

    return SourceContext(passage=copy.deepcopy(FIGURE_PASSAGE), around=copy.deepcopy(FIGURE_AROUND),
                         span_texts={item["span_id"]: item["text"] for item in FIGURE_PASSAGE + FIGURE_AROUND})


def _reuse_key(request: dict[str, Any] | None = None, *, image: str | None = None, grounding: Any = None,
               **settings: Any) -> Callable[[], Any]:
    def compute() -> Any:
        from learnloop.figures.build import request_hash

        return request_hash(_figure_request(**(request or {})), _figure_context(), image, grounding=grounding,
                            **settings)
    return compute


def _grounding(mode: str) -> Any:
    from learnloop.figures.grounding import Grounding

    keys = [("ext_pin", "s3"), ("ext_two", "q1")] if mode == "retrieved" else []
    return Grounding(mode, keys=keys)


def _alternate_keys(*, learner: bool) -> list[str]:
    """The keys a build looks a shown figure up under besides its own: the same input under the other settings of the
    panels, the sketch tier and the rich menu, each followed by its recorded-inputs twin when a learner state was
    sent. Production assembles this list inline in ``figures.build._build``; the setting tuples are copied from
    there (the panels on, the sketch tier on, the rich menu with Manim: the default build)."""

    from learnloop.figures.build import _recorded_input_key, request_hash

    advanced, sketch, tiers = True, True, FIGURE_MENU
    state = FIGURE_LEARNER if learner else None
    request, context = _figure_request(), _figure_context()
    other = [request_hash(request, context, None, advanced=a, sketch=k, tiers=t, rich_runtime=FIGURE_RUNTIME,
                          learner_state=state)
             for a, k, t in ((not advanced, sketch, tiers), (advanced, not sketch, None),
                             (not advanced, not sketch, None), (advanced, sketch, None),
                             (not advanced, sketch, None)) if (a, k, t) != (advanced, sketch, tiers)]
    if learner:
        other = [key for plain in other for key in (plain, _recorded_input_key(plain))]
    return other


def _recorded_twin() -> Any:
    from learnloop.figures.build import _recorded_input_key

    return _recorded_input_key(_reuse_key(advanced=True, sketch=True, tiers=FIGURE_MENU, rich_runtime=FIGURE_RUNTIME,
                                          learner_state=FIGURE_LEARNER)())


def _request_fields() -> Any:
    """The FigureRequest fields the reuse key reads, with their defaults: a request built without one hashes its
    default, so a renamed field or a changed default moves every key built from such requests."""

    from learnloop.figures.request import FigureRequest

    read = ("extraction_id", "span_ids", "region", "supersedes_id", "revision_note", "source_check_id",
            "different_kind", "goal_text", "goal_author")
    found = {item.name: item for item in dataclass_fields(FigureRequest)}

    def default(item: Any) -> str:
        if item.default is not MISSING:
            return repr(item.default)
        return repr(item.default_factory()) if item.default_factory is not MISSING else "required"

    return {name: default(found[name]) for name in read}


def _figure_reuse_keys() -> dict[str, Callable[[], Any]]:
    show_me = {"extraction_id": "ext_pin", "goal_text": FIGURE_GOAL, "goal_author": "learner"}
    rich = {"advanced": True, "sketch": True, "tiers": FIGURE_MENU, "rich_runtime": FIGURE_RUNTIME}
    return {
        "plain": _reuse_key(),
        "panels": _reuse_key(advanced=True),
        "sketch": _reuse_key(sketch=True),
        "panels_sketch": _reuse_key(advanced=True, sketch=True),
        "rich_menu": _reuse_key(**rich),
        "rich_menu_no_sketch": _reuse_key(advanced=True, tiers=("grammar", "manim"), rich_runtime=FIGURE_RUNTIME),
        "region_and_crop": _reuse_key({"region": copy.deepcopy(FIGURE_REGION)}, image=FIGURE_IMAGE, advanced=True),
        "revision": _reuse_key({"supersedes_id": "fig_pin", "revision_note": "show p = 0.7 instead"}, advanced=True),
        "different_kind": _reuse_key({"supersedes_id": "fig_pin", "revision_note": "a video instead",
                                      "different_kind": True}, **rich),
        "source_check_rebuild": _reuse_key({"source_check_id": "fsc_pin"}, advanced=True),
        "show_me.anchor": _reuse_key(show_me, grounding=_grounding("anchor"), advanced=True),
        "show_me.retrieved": _reuse_key({**show_me, "span_ids": []}, grounding=_grounding("retrieved"),
                                        advanced=True),
        "show_me.none": _reuse_key({**show_me, "span_ids": []}, grounding=_grounding("none"), advanced=True),
        "show_me.tutor_goal": _reuse_key({**show_me, "goal_author": "tutor"}, grounding=_grounding("anchor"), **rich),
        "learner_state": _reuse_key(learner_state=FIGURE_LEARNER, **rich),
        "learner_state.recorded_twin": _recorded_twin,
        "alternates": lambda: _alternate_keys(learner=False),
        "alternates.with_learner_state": lambda: _alternate_keys(learner=True),
        "request_fields": _request_fields,
    }


def _figure_request_identity(generation: int) -> Callable[[], Any]:
    """``figures.build._build``'s request identity, assembled there inline: the input and its retry generation."""

    def compute() -> Any:
        from learnloop.ai.execution import content_key

        return content_key({"input_hash": _reuse_key(advanced=True)(), "generation": generation})
    return compute


#: Every menu ``author_prompt_version`` is built with: none (V1/V2), the default rich menu, the menu without sketch.
FIGURE_MENUS: dict[str, tuple[str, ...] | None] = {"none": None, "gsm": FIGURE_MENU, "gm": ("grammar", "manim")}


def _prompt_version(advanced: bool, show_me: bool, sketch: bool, menu: str, learner: bool) -> Callable[[], Any]:
    def compute() -> Any:
        from learnloop.figures.routes import author_prompt_version

        return author_prompt_version(advanced=advanced, show_me=show_me, sketch=sketch, tiers=FIGURE_MENUS[menu],
                                     learner=learner)
    return compute


def _figure_prompt_versions() -> dict[str, Callable[[], Any]]:
    pins: dict[str, Callable[[], Any]] = {}
    for advanced in (False, True):
        for show_me in (False, True):
            for sketch in (False, True):
                for menu in FIGURE_MENUS:
                    for learner in (False, True):
                        name = (f"author.{'panels' if advanced else 'plain'}{'+show_me' if show_me else ''}"
                                f"{'+sketch' if sketch else ''}+menu_{menu}{'+learner' if learner else ''}")
                        pins[name] = _prompt_version(advanced, show_me, sketch, menu, learner)

    def rich() -> Any:
        from learnloop.figures.rich import RICH_PROMPT_VERSION

        return RICH_PROMPT_VERSION
    pins["rich"] = rich
    return pins


def _figure_contract(sketch: bool, menu: str) -> Callable[[], Any]:
    def compute() -> Any:
        from learnloop.figures.routes import output_model

        model = output_model(sketch=sketch, tiers=FIGURE_MENUS[menu])
        return {"model": model.__name__, "schema": model.model_json_schema()}
    return compute


def _rich_contract() -> Any:
    from learnloop.figures.rich import FigureManimOutputV1

    return {"model": FigureManimOutputV1.__name__, "schema": FigureManimOutputV1.model_json_schema()}


def _rich_build_key(**figures: Any) -> Callable[[], Any]:
    """The key a rich job's gate compares before every request, read from a vault that is never opened."""

    def compute() -> Any:
        from learnloop.figures.rich import rich_build_key

        config = init_config(figures=figures) if figures else init_config()
        return rich_build_key(SimpleNamespace(root=VAULT_ROOT, config=config))
    return compute


IDENTITY_SITES: tuple[IdentitySite, ...] = (
    IdentitySite(
        "K9.5m", "pattern, card, reversal and pack-card ledger identities",
        ("src/learnloop/diagnosis/split/jobs.py::record_pattern_verdicts",
         "src/learnloop/diagnosis/recurrence/guard.py::record_diagnoser_links",
         "src/learnloop/diagnosis/split/card.py::record_card_tap",
         "src/learnloop/diagnosis/text_gaps/actions.py::not_this_belief",
         "src/learnloop/diagnosis/text_gaps/actions.py::reversal_verdict",
         "src/learnloop/diagnosis/diagnostic_pack.py::assemble_pack"),
        "judgment deduplication and diagnostic pack card revisions", "old verdicts or cards stop matching",
        {"pattern": diagnosis_pins.pattern_verdict, "guard_link": diagnosis_pins.guard_link,
         "card": diagnosis_pins.card_verdict, "belief_reversal": diagnosis_pins.belief_reversal,
         "prerequisite_reversal": diagnosis_pins.prerequisite_reversal, "pack_card": diagnosis_pins.pack_card}),
    IdentitySite(
        "K9.5l", "probe families, instances, causal emissions and text-gap creation",
        ("src/learnloop/diagnosis/probe_families.py::ProbeFamilyTemplate.schema_hash",
         "src/learnloop/diagnosis/probe_families.py::CompiledInstrument.compiled_likelihood_hash",
         "src/learnloop/diagnosis/probe_instance_generation.py::_instance_payload",
         "src/learnloop/diagnosis/causal_diagnostic_selector.py::_stable_emission_key",
         "src/learnloop/diagnosis/text_gaps/actions.py::creation_ids",
         "src/learnloop/diagnosis/text_gaps/actions.py::edge_id_for",
         "src/learnloop/diagnosis/recurrence/guard.py::_case",
         "src/learnloop/diagnosis/recurrence/guard.py::suite_hash",
         "src/learnloop/diagnosis/text_gaps/tier1.py::ask_needed"),
        "pinned instrument snapshots, generated item and prerequisite inserts, guard and judge reuse",
        "replays diverge or retries create duplicate entities",
        {"family": diagnosis_pins.family_schema, "compiled": diagnosis_pins.compiled_likelihood,
         "instances": diagnosis_pins.parametric_ids, "emissions": diagnosis_pins.emission_keys,
         "creation": diagnosis_pins.gap_creation, "guard_suite": diagnosis_pins.guard_suite_identity,
         "needed_tier1": diagnosis_pins.needed_tier1}),
    IdentitySite(
        "K9.5a", "causal discriminating observations and machine checks",
        ("src/learnloop/diagnosis/causal_discrimination.py::record_learner_embedded_prediction",
         "src/learnloop/diagnosis/causal_discrimination.py::record_probe_classification",
         "src/learnloop/diagnosis/machine_checks.py::_machine_check_id"),
        "idempotent observation and machine-check inserts", "duplicate observations or obligations",
        {"cdo_question": diagnosis_pins.embedded_prediction, "cdo_probe": diagnosis_pins.probe_classification,
         "cmc": diagnosis_pins.machine_check}),
    IdentitySite(
        "K9.5b", "blind bundles, probe candidates, audits and cold observations",
        tuple("src/learnloop/diagnosis/causal_probe_coherence.py::" + name for name in (
            "generate_blind_prediction_bundle", "audit_manipulation_contract", "create_probe_candidate",
            "record_causal_cold_outcome", "record_delayed_cold_verification")),
        "idempotent causal stores and pinned bundle references", "old bundles and repair observations no longer match",
        {"bpb": lambda: diagnosis_pins.blind_bundle("bundle_id"), "bpi": lambda: diagnosis_pins.blind_bundle("input_hash"),
         "pma": diagnosis_pins.manipulation_audit, "cpc": diagnosis_pins.probe_candidate,
         "cco": diagnosis_pins.cold_outcome, "ccv": diagnosis_pins.cold_verification}),
    IdentitySite(
        "K9.5c", "attribution validation, repair classes, receipts and taxonomy",
        tuple("src/learnloop/diagnosis/causal_attribution.py::" + name for name in (
            "RepairValidationResult.as_dict", "_repair_class", "repair_equivalence_id", "_candidate_key",
            "materialize_causal_episode", "mint_causal_mechanism_taxonomy")),
        "repair equivalence, hypothesis deduplication and immutable taxonomy snapshots",
        "identical facts fork their stored identities",
        {"rv": diagnosis_pins.repair_validation, "rc": diagnosis_pins.repair_class,
         "dr": diagnosis_pins.diagnosis_receipt, "re": diagnosis_pins.repair_equivalence,
         "ck": diagnosis_pins.dialogue_candidate, "mechanism": lambda: diagnosis_pins.taxonomy("mechanism"),
         "ch": lambda: diagnosis_pins.taxonomy("source_head_hash"),
         "ctv": lambda: diagnosis_pins.taxonomy("taxonomy_version_id")}),
    IdentitySite(
        "K9.5d", "missing-vocabulary refusal identity",
        ("src/learnloop/diagnosis/missing_vocabulary.py::_note_id",),
        "missing vocabulary note inserts", "re-materialization duplicates an abstention",
        {"mvn": diagnosis_pins.missing_vocabulary}),
    IdentitySite(
        "K9.5e", "prior-analysis assignment and correct-answer sample",
        ("src/learnloop/diagnosis/split/prior_analysis.py::assign",
         "src/learnloop/diagnosis/split/live.py::sampled_correct_answer"),
        "diagnosis experiment assignment and shadow sample", "the same attempt switches experiment arms",
        {"prior_draw": diagnosis_pins.prior_draw, "correct_sample": diagnosis_pins.correct_sample}),
    IdentitySite(
        "K9.5f", "text-gap judge checkpoint keys",
        ("src/learnloop/diagnosis/text_gaps/judges.py::kind_input_hash",
         "src/learnloop/diagnosis/text_gaps/judges.py::ask_needed"),
        "judgment ledger reuse", "paid judgments stop matching",
        {"kind": diagnosis_pins.text_kind, "needed": diagnosis_pins.text_needed}),
    IdentitySite(
        "K9.5g", "recurrence guard verdict reuse",
        ("src/learnloop/diagnosis/recurrence/guard.py::_subject",),
        "matching.judge.already_judged under GUARD_KIND", "standing guard verdicts stop matching",
        {"pair": diagnosis_pins.recurrence_reuse}),
    IdentitySite(
        "K9.5h", "diagnosis prompt version and ordered suffixes",
        ("src/learnloop/diagnosis/split/jobs.py::_diagnose",),
        "diagnosis rows and agent run prompt versions", "existing diagnoses stop matching the current prompt",
        {f"workbench{w}_figures{f}_prior{p}": lambda w=w, f=f, p=p: diagnosis_pins.prompt_version(w, f, p)
         for w in (False, True) for f in (False, True) for p in (False, True)}),
    IdentitySite(
        "K9.5i", "robust composition decision context and ensemble seed",
        ("src/learnloop/diagnosis/robust_composition.py::decision_context_hash",
         "src/learnloop/diagnosis/robust_composition.py::_seed_int"),
        "committed robust selection snapshots", "identical decisions draw different ensembles",
        {"context": diagnosis_pins.robust_context, "seed": diagnosis_pins.robust_seed}),
    IdentitySite(
        "K9.5j", "diagnosis retrieval and embedding cache keys",
        ("src/learnloop/diagnosis/split/retrieval.py::content_hash",
         "src/learnloop/diagnosis/split/embeddings.py::_record",
         "src/learnloop/diagnosis/text_gaps/kinds.py::query_hash"),
        "embedding cache lookup", "paid vectors stop being reused",
        {"retrieval": diagnosis_pins.retrieval_hash, "embedding": diagnosis_pins.embedding_hash,
         "gap_query": diagnosis_pins.gap_query_hash}),
    IdentitySite(
        "K9.5k", "assessment contract, pack identity and contrast assignment",
        ("src/learnloop/diagnosis/voi_forecasting.py::facet_contract_criteria_hash",
         "src/learnloop/diagnosis/diagnostic_pack.py::pack_content_hash",
         "src/learnloop/diagnosis/contrast_pairs.py::randomization_draw"),
        "forecast contract comparison, pack reuse and recorded pair randomization",
        "contracts or packs fork and contrast order changes",
        {"criteria": diagnosis_pins.criteria_hash, "pack": diagnosis_pins.pack_hash,
         "contrast_draw": diagnosis_pins.contrast_draw}),

    IdentitySite(
        "A1", "facet identity config in the synthesis manifest scope",
        ("src/learnloop/content/facet_identity/judge.py::manifest_identity",),
        "synthesis_manifests.manifest_hash of bootstrap synthesis and append, recorded in agent_runs.input_context_hash (a record: nothing reuses a run by it since K2.3)",
        "the record names a run's facet identity config differently; nothing is paid again",
        _per_config(_a1_facet_identity)),
    IdentitySite(
        "A2", "facet identity judge route in the synthesis manifest scope",
        ("src/learnloop/content/facet_identity/judge.py::JudgeRoute.as_dict",
         "src/learnloop/content/facet_identity/judge.py::resolve_route"),
        "synthesis_manifests.manifest_hash of bootstrap synthesis and append, recorded in agent_runs.input_context_hash (a record: nothing reuses a run by it since K2.3)",
        "the record names a run's judge route differently (prices, policy output budget and the problem text "
        "are in it); nothing is paid again",
        _route_variants()),
    IdentitySite(
        "A3", "graph nominator identity in the synthesis manifest scope",
        ("src/learnloop/content/synthesis/graph_nomination.py::GraphNominator.identity",),
        "synthesis_manifests.manifest_hash of bootstrap synthesis and append, recorded in agent_runs.input_context_hash (a record: nothing reuses a run by it since K2.3)",
        "the record names a run's nominator differently; nothing is paid again",
        {"legacy.embedding_on": _a3_graph_nomination}),
    IdentitySite(
        "A1-A4", "bootstrap synthesis scope and full manifest hash",
        ("src/learnloop/content/synthesis/source_set_synthesis.py::bootstrap_scope",
         "src/learnloop/content/synthesis/synthesis_manifests.py::build_manifest",
         "src/learnloop/content/synthesis/synthesis_manifests.py::agent_run_input_context_hash"),
        "synthesis_manifests.manifest_hash of bootstrap synthesis, recorded in agent_runs.input_context_hash (a "
        "record: nothing reuses a run by it since K2.3)",
        "a bootstrap's record is named differently; nothing is paid again",
        {**{f"scope.{name}": _bootstrap_scope(name) for name in CONFIGS},
         # agent_run_input_context_hash(manifest) is the manifest hash itself (what the agent run records).
         **{f"manifest_hash.{name}": (lambda name=name: _manifest(name)["manifest_hash"]) for name in CONFIGS}}),
    IdentitySite(
        "K3.2", "append synthesis scope without a unit filter",
        ("src/learnloop/content/synthesis/source_append.py::append_scope",),
        "synthesis_manifests.scope of append, inside its manifest hash (a record: nothing reuses a run by it since "
        "K2.3)",
        "an append's record is named differently; nothing is paid again",
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
        "synthesis_manifests.task_graph_hash, inside the manifest hash (a record since K2.3)",
        "the record names a run's task graph differently; nothing is paid again",
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
        "K2.2a", "source unit inventory row key (the inventory prompt over an empty context, schema version, "
                 "provider and model)",
        ("src/learnloop/content/synthesis/source_unit_inventory.py::inventory_row_key",),
        "source_unit_inventories.usage_json request_key, matched before a row is reused (reusable_unit_inventories)",
        "every inventory row stops answering; its windows are read from their checkpoints, or paid where none is kept",
        {"row_key": _inventory_row_key}),
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
        "section_questions", "section authoring answer and completed work checkpoints",
        ("src/learnloop/content/proposals/ai_contracts.py::authoring_prompt",
         "src/learnloop/content/proposals/proposals.py::_authoring_checkpoint",
         "src/learnloop/content/authoring/practice_generation.py::section_questions_key"),
        "section request snapshots, authoring/repair answers and completed section results",
        "a saved section answer misses and is paid again on retry or rebuild",
        {"answer": _section_authoring_key, "work": _section_questions_key}),
    IdentitySite(
        "reader_topic_work", "a topic's first-set checkpoint scope (its own topic and grounding)",
        ("src/learnloop/content/authoring/practice_generation.py::topic_questions_key",),
        "a topic's frozen request snapshot and prepared part (<scope>:requests, <scope>:part:0), stored on its claim",
        "claims made keep the scope frozen in their row and batch payload; a topic claimed after the move is "
        "scoped anew, and a run that recomputed the scope would miss its saved request and part and pay again",
        {"work": _topic_questions_key}),
    IdentitySite(
        "K2.1e", "persona fire judgement checkpoint key (rendered prompt, schema, grader settings, the trial)",
        ("src/learnloop/diagnosis/ai_contracts.py::diagnostic_fire_prompt",
         "src/learnloop/diagnosis/diagnostic_gate.py::fire_checkpoint"),
        "persona fire judgement checkpoints (model_checkpoints)",
        "every cached persona judgement misses and is paid again on retry",
        {"key": _persona_fire_key}),
    IdentitySite(
        "K2.1f", "vault epigraph batch checkpoint key (asdict of its context in the prompt)",
        ("src/learnloop/content/synthesis/ai_contracts.py::vault_epigraphs_prompt",
         "src/learnloop/content/synthesis/vault_epigraphs.py::epigraph_checkpoint"),
        "vault epigraph checkpoints (model_checkpoints)",
        "a cached epigraph batch misses and is paid again on retry",
        {"key": _epigraph_key}),
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
         "src/learnloop/content/synthesis/normalize.py::_mint_gate"),
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
         "src/learnloop/daily_plan/objective_seeds.py::numeric_seed"),
        "the prefetch boundary key and the numeric policy's rollout RNG (router_objective/rollouts.py)",
        "different draws at a fixed input (P-draw fails) and prefetched decisions miss",
        {**{f"router_settings.{name}": _router_settings(name) for name in OBJECTIVE_CONFIGS},
         **{f"boundary.{name}": _numeric_seed(name) for name in OBJECTIVE_CONFIGS}}),
    IdentitySite(
        "C3b", "the objective block's boundary identity as ObjectiveChooser.choose assembles it",
        ("src/learnloop/daily_plan/objective_chooser.py::ObjectiveChooser.choose",
         "src/learnloop/daily_plan/types.py::BlockCandidate.log_row"),
        "the prefetch boundary key and the numeric policy's seed (a started job is looked up by it at the serve)",
        "prefetched decisions miss and the numeric draws move at a fixed input",
        {"chooser": _chooser_boundary, "start_key": _chooser_start_key}),
    IdentitySite(
        "C3m", "the mix's and the stop coin's seed for one decision (boundary key, decision id)",
        ("src/learnloop/daily_plan/objective_seeds.py::mix_seed",
         "src/learnloop/router_objective/mix.py::seed_for"),
        "the mix's two uniforms and the stop coin's, and the seed every decision record and trace names",
        "every decision draws differently at a fixed input (P-draw fails), and a recorded seed no longer recomputes",
        {"seed": _mix_seed}),
    IdentitySite(
        "C4", "objective settings and the follow-up switch snapshot (the kill-switch list D7 deletes)",
        ("src/learnloop/daily_plan/objective_chooser.py::objective_settings",
         "src/learnloop/router_objective_switches.py::followup_switch_snapshot"),
        "the prefetch boundary key and numeric_seed (less SEED_NEUTRAL_SWITCHES)",
        "different numeric draws at a fixed input; D7 decides per switch whether to keep its served value or fold "
        "the change into E8",
        {**{f"objective_settings.{name}": _objective_settings(name) for name in OBJECTIVE_CONFIGS},
         **{f"switches.{name}": _followup_switches(name) for name in OBJECTIVE_CONFIGS}}),
    IdentitySite(
        "C5", "RO6 generator key (FOLLOWUP_GENERATOR_SWITCHES)",
        ("src/learnloop/daily_plan/objective_chooser.py::generator_now",
         "src/learnloop/router_objective/tail_data.py::generator_key"),
        "the learned tail's generator grouping and change points (router_objective/tail_data.py)",
        "an RO6 generator change point against all logged history: the learned tail starts over",
        {name: _generator_now(name) for name in OBJECTIVE_CONFIGS}),
    IdentitySite(
        "C6", "lesson suggestion draw snapshot and seed (whole RouterWeights)",
        ("src/learnloop/daily_plan/lesson_suggestion.py::draw_inputs",
         "src/learnloop/router/lesson_suggestions.py::seed_for"),
        "the day's lesson card draw (seed) and its row's snapshot_hash",
        "a different card is drawn at a fixed input",
        _per_config(_lesson_draw)),
    IdentitySite(
        "K10.4a", "figure reuse key (request_hash) over the build's matrix, its alternates and recorded twins",
        ("src/learnloop/figures/build.py::request_hash", "src/learnloop/figures/build.py::_build",
         "src/learnloop/figures/build.py::_recorded_input_key", "src/learnloop/figures/learner_state.py::state_hash"),
        "interactive_figures.input_hash: the reuse index (db/stores/figures.py reusable, latest_for_input) every "
        "press and pre-build looks its figure up by, under its own setting and the five others",
        "every stored figure is orphaned: each later press of the same input pays for a new build",
        _figure_reuse_keys()),
    IdentitySite(
        "K10.4b", "figure request identity (content_key of the input and its retry generation)",
        ("src/learnloop/figures/build.py::_build",),
        "the author route's owner and checkpoints: a build rerun after a crash recovers its paid answers by it",
        "a build interrupted after a paid answer pays for it again",
        {f"generation.{generation}": _figure_request_identity(generation) for generation in (0, 1)}),
    IdentitySite(
        "K10.4c", "figure author and rich author prompt versions",
        ("src/learnloop/figures/routes.py::author_prompt_version", "src/learnloop/figures/rich.py::rich_prompt"),
        "inside every figure reuse key (K10.4a), on every stored figure and in the rich job's receipts",
        "every stored figure under the moved version is orphaned (a press re-pays) and drawable-now checks change",
        _figure_prompt_versions()),
    IdentitySite(
        "K10.4d", "figure author output contracts (V1, V2, V3) and the rich author's: their JSON schemas",
        ("src/learnloop/figures/routes.py::output_model", "src/learnloop/figures/routes.py::FigureRoute.ask"),
        "the paid checkpoint key of every figure author and rich author request (practice_index.paid)",
        "the checkpointed answers keyed by that schema are paid again (a docstring or Field description edit moves it)",
        {"author.v1": _figure_contract(False, "none"), "author.v2": _figure_contract(True, "none"),
         "author.v3": _figure_contract(True, "gsm"), "rich": _rich_contract}),
    IdentitySite(
        "K10.4e", "rich job build key (the route, the day's cap and price, the switches and the opt-in)",
        ("src/learnloop/figures/rich.py::rich_build_key",),
        "the rich job's admission gate, compared before every request it makes (figure_admission.FiguresGate)",
        "a change stops every running rich job with nothing stored (figures_changed)",
        {"init": _rich_build_key(), "priced": _rich_build_key(price_per_million=2.0, max_daily_cost_usd=0.5)}),
    IdentitySite(
        "EP0t", "a prediction target's canonical serialization and target_hash (evidence packets EP0t, §7.7.4)",
        ("src/learnloop/db/prediction_target.py::PredictionTarget.canonical_json",
         "src/learnloop/db/prediction_target.py::PredictionTarget.target_hash"),
        "prediction snapshots' versions_json.snapshot.target (EPp on): reports group, join and later filter "
        "forecasts by target_hash",
        "one target recorded before and after the move carries two hashes: reports split it or miss its forecasts",
        {"full": lambda: prediction_target_pin(), "minimal": lambda: prediction_target_pin(minimal=True)}),
    IdentitySite(
        "EPp", "a prediction snapshot's serialized shape (evidence packets EPp, §7.7.2)",
        ("src/learnloop/scheduling/prediction_snapshots.py::receipt_bodies",
         "src/learnloop/scheduling/prediction_snapshots.py::voi_snapshot"),
        "forecast receipts' versions_json.snapshot and forecast_json.distribution, voi_forecasts' "
        "versions_json.snapshot: the evaluation reports that read them back later",
        "receipts written before and after the move are read by two shapes: a report misreads or drops one",
        {"stated": lambda: prediction_snapshot_pin(), "derived": lambda: prediction_snapshot_pin(stated=False),
         "voi": lambda: prediction_snapshot_pin(voi=True)}),
    IdentitySite(
        "EPp-repeat", "the predecessor's repeat receipts: their keys and versions and their inputs_json's shape "
        "(evidence packets EPp, §7.7.3 item 1)",
        ("src/learnloop/adaptive_difficulty/repeat_receipts.py::shared_inputs",
         "src/learnloop/adaptive_difficulty/repeat_receipts.py::view_inputs",
         "src/learnloop/adaptive_difficulty/repeat_receipts.py::memory_context",
         "src/learnloop/adaptive_difficulty/repeat_receipts.py::delay_context",
         "src/learnloop/adaptive_difficulty/repeat_receipts.py::build_receipt"),
        "ad_threshold_repeat@* receipts' receipt_key (idempotence per presentation), inputs_json and its "
        "inputs_hash: the memory successor's comparison reads them back by forecaster, key and input shape",
        "repeats captured before and after the move are keyed or shaped two ways: the comparison splits or "
        "misreads them",
        {"keys": lambda: repeat_receipt_pin(), "inputs": lambda: repeat_receipt_pin(inputs=True)}),
)


def repeat_receipt_pin(*, inputs: bool = False) -> dict[str, Any]:
    """A repeat receipt at fixed plain values: its key, forecaster version and versions, or its inputs (the memory
    context and the delay read through a fixed fake view, assembled by the pure functions)."""

    from types import SimpleNamespace

    from learnloop.adaptive_difficulty import repeat_receipts as RR
    from learnloop.adaptive_difficulty.snapshot_parts import ServedItem

    item = SimpleNamespace(id="pi_pin", learning_object_id="lo_pin", evidence_fingerprint=None, surface_family="fam")
    sibling = SimpleNamespace(id="pi_sib", learning_object_id="lo_pin", evidence_fingerprint=None,
                              surface_family="fam")
    served_at = "2026-10-12T09:00:00Z"
    if not inputs:
        receipts = [RR.build_receipt(name, item=item, presentation_kind="plan_presentation",
                                     presentation_id="pp_pin", served_at=served_at, forecast={"p": 0.5},
                                     inputs={"a": 1}, p=0.5, status="ok", parts=None)
                    for name in RR.REPEAT_FORECASTERS]
        return [{"receipt_key": r.receipt_key, "forecaster_version": r.forecaster_version,
                 "versions": dict(r.versions), "columns": dict(r.columns), "scope": r.scope,
                 "binding_kind": r.binding_kind, "kind": r.kind} for r in receipts]
    rows = [{"id": "a_pin", "practice_item_id": "pi_pin", "learning_object_id": "lo_pin",
             "created_at": "2026-10-09T09:00:00Z", "attempt_type": "independent_attempt",
             "plan_presentation_id": None, "correctness": 0.0, "hints_used": 0, "primed": 0},
            {"id": "s_pin", "practice_item_id": "pi_sib", "learning_object_id": "lo_pin",
             "created_at": "2026-10-10T09:00:00Z", "attempt_type": "independent_attempt",
             "plan_presentation_id": "pp_old", "correctness": 1.0, "hints_used": 1, "primed": 0}]
    view = SimpleNamespace(
        attempts=lambda _c: rows, reveals=lambda _c: [],
        item=lambda item_id: {"pi_pin": item, "pi_sib": sibling}.get(str(item_id)),
        presentation=lambda _c, _pid: {"origin": "chooser", "router_decision_id": "rd_pin", "block_id": "b_pin",
                                       "scheduler_candidate_id": None})
    served = ServedItem("pi_pin", "h" * 64, "lo_pin", ("facet_pin",), "fam", "surface_family")
    memory = RR.memory_context(None, view, item, served, served_at)
    shared = RR.shared_inputs(
        item, content_hash="h" * 64, state_hash="state_pin",
        features={"stamped_features": {"complexity": 1}, "task_feature_schema": "v1", "audit": {},
                  "resolved_features": {"complexity": 1}},
        recalibration="z_v1_logit_intercept_map_n01_v1", warmth=0.25,
        exposure={"available": True, "id": "s_pin", "at": "2026-10-10T09:00:00Z", "kind": "attempt",
                  "hours_before_serve": 48.0},
        pre_exposed=False, memory=memory, delay=RR.delay_context(None, view, "pp_pin", memory, served_at),
        coupling={})
    spec = SimpleNamespace(signals={"z_llm": 0.5, "z_origin": 1.0}, loadings={"facet_pin": 1.0})
    vector = {"z_llm": {"value": 0.5, "available": True, "receipt_id": None, "received_at": None,
                        "source": "item.difficulty"},
              "z_panel": {"value": None, "available": False, "why": "not_solver_panel"},
              "z_v1": {"value": 0.1, "available": True, "receipt_id": "r_pin", "received_at": served_at, "p": 0.4,
                       "p_recalibrated": 0.4, "recalibration": {"version": "v", "intercept": 0.0, "n": 0}},
              "z_origin": {"value": 1.0, "available": True, "receipt_id": None, "received_at": None,
                           "source": "generated"}}
    return RR.view_inputs(shared, view="subject", mixture="bank", vector=vector, spec=spec)


def prediction_snapshot_pin(*, stated: bool = True, voi: bool = False) -> dict[str, Any]:
    """The bodies a fixed receipt is written with: one whose producer states its snapshot, one whose writer
    derives it, and a VOI forecast's."""

    from learnloop.db.evidence_cutoff import Cutoff
    from learnloop.db.prediction_target import PredictionTarget, TargetMember
    from learnloop.scheduling import prediction_snapshots as PS
    from learnloop.scheduling.forecast_receipts import ForecastReceipt

    if voi:
        return PS.voi_snapshot(
            site="probe_selection", forecast_version="voi_forecast_v4",
            forecast={"predicted_outcomes": {"pass": 0.7, "fail": 0.3}, "forecast_of": "committed",
                      "chosen_ref": "cand_pin", "verdict": "measure"},
            columns={"chosen_practice_item_id": "pi_pin_svd_000", "learning_object_id": "lo_pin_svd",
                     "presentation_id": "pp_pin"})
    parts = None
    if stated:
        parts = PS.SnapshotParts(
            cutoff=Cutoff.ad_replay("2026-10-12T08:00:00Z"), source={"ad_state_hash": "state_pin"},
            target=PredictionTarget(
                kind="item_unassisted_success",
                members=(TargetMember("item", "pi_pin_svd_000", revision="sha256:" + "0" * 64),
                         TargetMember("learning_object", "lo_pin_svd")),
                unit="ad_category3", event_version="ad_category:ad_priors_v1",
                resolver_version="ad_forecast_scores_v1", action_kind="serve", action_id="pi_pin_svd_000",
                horizon_kind="presentation", anchor_kind="plan_presentation", anchor_id="pp_pin"),
            distribution=PS.categorical_distribution({"0": 0.5, "1": 0.25, "2": 0.25}, unit="ad_category3",
                                                     event="unassisted_success", event_outcomes=("2",)),
            provenance={"prior": {"version": "ad_priors_v1", "source": "code"}})
    receipt = ForecastReceipt(
        receipt_key="pin", kind="item_unassisted_success", forecaster="pin_forecaster", forecaster_version="v1",
        scope="presentation", decision_kind="serve", binding_kind="plan_presentation", event="unassisted_success",
        forecast={"p": 0.25, "event": "unassisted_success", "p_categories": None}, inputs={"a": 1}, parameters=[],
        versions={"prompt": "prompt_pin", "model": "model_pin"}, inputs_as_of="2026-10-12T08:00:00Z", p=0.25,
        columns={"decision_ref": "pp_pin", "practice_item_id": "pi_pin_svd_000", "learning_object_id": "lo_pin_svd",
                 "plan_presentation_id": "pp_pin"},
        snapshot=parts)
    forecast, versions = PS.receipt_bodies(receipt, "2026-10-12T09:00:00Z", "2026-10-12T08:00:00Z")
    return {"forecast": forecast, "versions": versions}


def prediction_target_pin(*, minimal: bool = False) -> dict[str, str]:
    """A fixed target, every typed field set (members given out of canonical order), or only the required ones."""

    from learnloop.db.prediction_target import PredictionTarget, TargetMember

    if minimal:
        target = PredictionTarget(kind="lo_cold_success", members=(TargetMember("learning_object", "lo_pin_svd"),),
                                  unit="binary", event_version="cold_success@1", resolver_version="resolver@1")
    else:
        target = PredictionTarget(
            kind="item_unassisted_success",
            members=(TargetMember("surface_group", "svd_compute", source="authored"),
                     TargetMember("item", "pi_pin_svd_000", revision="sha256:" + "0" * 64),
                     TargetMember("facet", "svd_definition"), TargetMember("learning_object", "lo_pin_svd")),
            unit="category3", event_version="ad_category@1", resolver_version="ad_resolver@1",
            action_kind="serve", action_id="pi_pin_svd_000", horizon_kind="next_attempt", horizon=None,
            anchor_kind="plan_presentation", anchor_id="pp_pin")
    return {"canonical_json": target.canonical_json(), "target_hash": target.target_hash()}


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
    "learnloop.content.proposals.ai_contracts:AuthoringContext": ("section_questions",),
    "learnloop.vault.models:TraceContract": ("K9.5b",),
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
    "learnloop.content.synthesis.ai_contracts:SourceUnitInventoryContext": ("A15", "K2.2a"),
    "learnloop.content.synthesis.ai_contracts:ConceptGraphContext": ("K2.1d",),
    "learnloop.content.synthesis.ai_contracts:VaultEpigraphContext": ("K2.1f",),
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
    "src/learnloop/content/proposals/method_phrasing.py::judge_prompt": PROMPT_REASON,
    "src/learnloop/content/proposals/proposals.py::persist_authoring_proposal":
        "agent_runs.input_context_hash of purpose 'authoring', which nothing looks up (only canonical ingest, "
        "synthesis and append read completed_agent_run*_by_context; sweep §1D)",
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
