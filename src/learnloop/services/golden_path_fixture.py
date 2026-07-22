"""P2 -- deterministic golden-path fixture bootstrap
(spec_p2_narrow_golden_path §C, §12.7, §12.8).

Builds a FRESHLY INITIALIZED mvp-0.8 vault over the linear-algebra
``symmetric-matrices-and-variance`` chapter, with a planted method-selection target
family (§12.7): two representative end-of-chapter exercises are selected as familiar
anchors and one unseen sibling is reserved as the fresh held-out assessment. Every
owner-in-the-loop artifact (blueprint spec, reviewed depth edge) is produced by a
DETERMINISTIC stub generator following the U-034 artifacts-not-API-calls shape -- no
live AI runs here, so the fixture renders identically offline.

Determinism (§12.8): two builds from the same clock produce byte-identical seeded
content and identical content hashes (blueprint / goal-contract / depth policy /
envelope). IDs are ULIDs and timestamps are supplied by the clock, so a content-hash
comparison (not a raw id/timestamp comparison) is the determinism invariant --
``GoldenPathFixture.content_hashes`` exposes exactly those fields.

This module is the single source shared by the pytest factory (``tests``) and the CLI
affordance (``learnloop goldenpath init-fixture``).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from learnloop.clock import Clock, FrozenClock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.services import golden_path_confirm as GPC
from learnloop.services import task_blueprints as TB
from learnloop.services.activities import resolve_legacy_item
from learnloop.vault.loader import add_subject, init_vault, load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import write_yaml

FIX_NOW = datetime(2026, 5, 19, 12, 0, tzinfo=UTC)
FIX_NOW_ISO = "2026-05-19T12:00:00Z"
ALGORITHM_VERSION = "mvp-0.8"

SUBJECT_ID = "symmetric-matrices-and-variance"
SUBJECT_TITLE = "Symmetric Matrices and Variance"
SOURCE_REV = "symmetric-matrices-rev-1"
UNIT_ID = "symmetric-matrices-and-variance"
FAMILY_KEY = "method-selection-decomposition"
GOAL_ID = "goal_symmetric_method_selection"
BLUEPRINT_SLUG = "bp_symmetric_method_selection"
CONCEPT_ID = "symmetric_matrices"
LO_ID = "lo_symmetric_method_selection"

EXEMPLAR_A = "pi_symmetric_exemplar_a"
EXEMPLAR_B = "pi_symmetric_exemplar_b"
HELD_OUT = "pi_symmetric_heldout_sibling"


# ---------------------------------------------------------------------------
# Deterministic owner-artifact stub generators (U-034 shape; §C table)
# ---------------------------------------------------------------------------

def stub_blueprint(
    *,
    family_key: str = FAMILY_KEY,
    source_rev: str = SOURCE_REV,
    unit_id: str = UNIT_ID,
    exemplar_refs: tuple[str, ...] = (EXEMPLAR_A, EXEMPLAR_B),
    held_out_ref: str = HELD_OUT,
) -> dict[str, Any]:
    """Deterministic TaskBlueprintVersion spec (§3.2 shape). The two exemplars are
    familiar anchors (zero held-out weight); the sibling is the unseen assessment.
    The depth DAG carries one reviewed transfer edge (stub_depth_edge)."""

    exemplars = [{"exemplar_ref": ref, "unit_id": unit_id, "family_key": family_key, "weight": 1.0}
                 for ref in exemplar_refs]
    exemplars.append(
        {"exemplar_ref": held_out_ref, "unit_id": unit_id, "family_key": family_key,
         "weight": 0.0, "held_out": True, "held_out_weight": 1.0}
    )
    return {
        "schema_version": TB.BLUEPRINT_SPEC_SCHEMA_VERSION,
        "source_rev": source_rev,
        "unit_id": unit_id,
        "family_key": family_key,
        "title": "Select the right decomposition/approach for a symmetric-matrix / variance problem",
        "exemplars": exemplars,
        "semantic_facets": ["symmetric_matrix_decomposition_choice"],
        "required_capabilities": ["method_selection", "procedure_execution"],
        "solution_recipes": [
            {
                "id": "recipe_spectral",
                "composition": "conjunctive",
                "all_of": [
                    {"facet": "decomposition_choice", "capability": "method_selection", "modality": "hard"},
                    {"facet": "spectral_execution", "capability": "procedure_execution", "modality": "hard"},
                ],
                "any_of": [],
                "integration": {"facet": "variance_readout", "capability": "coordination", "modality": "hard"},
            }
        ],
        "task_feature_ranges": {"complexity": [0.4, 0.7], "span": [1, 3]},
        "administration_conditions": {"tools": "none", "open_book": False, "time_minutes": 15},
        "invariants": ["choose the decomposition before executing"],
        "permitted_variation_axes": ["matrix_entries", "problem_framing"],
        "response_contract": {"mode": "short_answer"},
        "outcome_schema": {"coarse": ["correct", "wrong_method", "execution_error", "dont_know"]},
        "rubric": {"max_points": 4, "criteria": [{"id": "method", "points": 2}, {"id": "execution", "points": 2}]},
        "fatal_errors": ["applied a non-symmetric method"],
        "failure_signature_triage": {"wrong_method": "method_selection", "execution_error": "procedure_execution"},
        "source_neighborhoods": {"method": ["span_symmetric_intro"], "execution": ["span_spectral_worked"]},
        "target_distribution": {"support": [{"cell": "method_selection x symmetric", "weight": 1.0}]},
        "depth_milestones": [stub_depth_edge()],
        "leakage_boundaries": {"assessment_excludes": list(exemplar_refs)},
        "authoring_version": "stub-1",
        "provenance_version": "owner-review-1",
    }


def stub_depth_edge() -> dict[str, Any]:
    """One reviewed inside-envelope depth edge (§7.5). Served as suggest_next in this
    cut; unprompted activation stays deferred (U-018)."""

    return {
        "edge_id": "edge_symmetric_transfer_1",
        "reviewed": True,
        "direction": "transfer",
        "milestone_slug": "m_method_selection_transfer",
        "task_feature_delta": {"span": 1},
        "capability_delta": [],
        "support_delta": {},
        "exit_evidence": {"kind": "cold_assessment_success"},
        "successor_activity_path": {"pattern": "whole_task_integration"},
        "fresh_proof_rule": "distinct_fresh_surface",
        "burden": {"minutes": 15},
    }


def stub_diagnostic_pack() -> dict[str, Any]:
    """Deterministic diagnostic-pack stub (§5.1, §C). Consumed by the P2 baseline
    track (migration 083); provided here for offline fixture rendering."""

    return {
        "pack_slug": "pack_symmetric_method_selection",
        "cards": [
            {"card_slug": "card_target_setup", "coverage": ["method_selection x symmetric"]},
            {"card_slug": "card_method_selection", "coverage": ["method_selection x confusable"]},
            {"card_slug": "card_procedure", "coverage": ["procedure_execution x symmetric"]},
        ],
    }


def stub_pool_surfaces() -> dict[str, Any]:
    """Deterministic practice-pool stub (§7.3, U-028, §C). Consumed by the P2 pool
    track (migration 085); provided here for offline fixture rendering."""

    return {
        "pool_slug": "pool_symmetric_method_selection",
        "surfaces": [
            {"surface_slug": "surf_setup_1", "angle": "setup_only"},
            {"surface_slug": "surf_move_spotting_1", "angle": "move_spotting"},
        ],
    }


@dataclass(frozen=True)
class GoldenPathFixture:
    root: Path
    receipt: GPC.RunReceipt
    blueprint_version_id: str
    blueprint_content_hash: str
    assessment_surface_id: str
    goal_contract_content_hash: str
    exemplar_refs: tuple[str, ...]
    held_out_ref: str

    @property
    def content_hashes(self) -> dict[str, str]:
        """The timestamp/id-independent content identity of the fixture (§12.8)."""

        return {
            "blueprint_content_hash": self.blueprint_content_hash,
            "goal_contract_content_hash": self.goal_contract_content_hash,
        }

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["root"] = str(self.root)
        data["receipt"] = self.receipt.as_dict()
        data["content_hashes"] = self.content_hashes
        return data


# ---------------------------------------------------------------------------
# Vault seeding
# ---------------------------------------------------------------------------

def _practice_item(item_id: str, prompt: str, *, now_iso: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "id": item_id,
        "learning_object_id": LO_ID,
        "subjects": None,
        "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt", "hinted_attempt", "dont_know"],
        "evidence_facets": ["method_selection"],
        "evidence_weights": {"method_selection": 1.0},
        "prompt": prompt,
        "expected_answer": "Choose the spectral decomposition, then compute directional variance.",
        "difficulty": 0.6,
        "tags": [],
        "hints": ["Which decomposition suits a symmetric matrix?"],
        "hint_policy": {
            "max_useful_hints": 1,
            "fsrs_rating_cap_by_hint": {"1": "good"},
            "mastery_alpha_dampening_by_hint": {"1": 0.5},
        },
        "grading_rubric": {
            "max_points": 4,
            "criteria": [
                {"id": "method", "points": 2, "description": "Selects the correct decomposition."},
                {"id": "execution", "points": 2, "description": "Executes it correctly."},
            ],
            "fatal_errors": [
                {"id": "wrong_method", "description": "Applies a non-symmetric method.", "max_grade": 1}
            ],
        },
        "provenance": {"origin": "human", "source_refs": []},
        "created_at": now_iso,
        "updated_at": now_iso,
    }


def _seed_vault(root: Path, *, clock: Clock, now_iso: str) -> VaultPaths:
    init_vault(root, clock=clock)
    # Design §C: a FRESHLY INITIALIZED mvp-0.8 vault (old-vault migration is dead).
    _pin_algorithm_version(root, ALGORITHM_VERSION)
    add_subject(root, SUBJECT_ID, SUBJECT_TITLE, clock=clock)
    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)

    write_yaml(
        paths.concepts_path,
        {
            "schema_version": 1,
            "concepts": {
                CONCEPT_ID: {
                    "title": "Symmetric Matrices",
                    "type": "concept",
                    "aliases": ["symmetric matrix"],
                    "description": "Symmetric matrices, spectral decomposition, and variance.",
                    "tags": [],
                    "created_at": now_iso,
                    "updated_at": now_iso,
                }
            },
        },
    )
    write_yaml(
        paths.goals_path,
        {
            "schema_version": 2,
            "goals": [
                {
                    "id": GOAL_ID,
                    "title": "Method selection for symmetric-matrix / variance tasks",
                    "status": "active",
                    "priority": 0.8,
                    "target_recall": 0.8,
                    "facet_scope": {"concepts": [CONCEPT_ID]},
                    "due_at": None,
                    "created_at": now_iso,
                    "updated_at": now_iso,
                }
            ],
        },
    )
    write_yaml(
        paths.error_types_path,
        {
            "schema_version": 1,
            "error_types": [
                {
                    "id": "wrong_method",
                    "title": "Wrong method selected",
                    "description": "Chose a decomposition that does not fit a symmetric matrix.",
                    "related_concepts": [CONCEPT_ID],
                    "severity_default": 0.7,
                    "is_misconception": True,
                    "tags": [],
                    "created_at": now_iso,
                    "updated_at": now_iso,
                }
            ],
        },
    )
    write_yaml(
        paths.learning_object_path(SUBJECT_ID, LO_ID),
        {
            "schema_version": 1,
            "id": LO_ID,
            "title": "Method selection for symmetric-matrix problems",
            "subjects": [SUBJECT_ID],
            "concept": CONCEPT_ID,
            "knowledge_type": "procedure_contract",
            "status": "active",
            "contradicts": None,
            "summary": "Select the right decomposition/approach before executing.",
            "prerequisites": [],
            "confusables": [],
            "difficulty_prior": 0.6,
            "tags": [],
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": now_iso,
            "updated_at": now_iso,
        },
    )
    for item_id, prompt in (
        (EXEMPLAR_A, "For the symmetric matrix A below, choose an approach and find its directional variance."),
        (EXEMPLAR_B, "Given the covariance matrix C, select a decomposition and report the maximal variance direction."),
        (HELD_OUT, "For symmetric matrix M, pick the right decomposition and compute the variance along its top eigenvector."),
    ):
        write_yaml(
            paths.practice_item_path(SUBJECT_ID, item_id),
            _practice_item(item_id, prompt, now_iso=now_iso),
        )
    return paths


def _pin_algorithm_version(root: Path, version: str) -> None:
    config_path = root / "learnloop.toml"
    text = config_path.read_text(encoding="utf-8")
    import re

    if re.search(r'algorithm_version\s*=', text):
        text = re.sub(r'algorithm_version\s*=\s*"[^"]*"', f'algorithm_version = "{version}"', text)
    config_path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

def build_golden_path_fixture(
    root: Path,
    *,
    clock: Clock | None = None,
) -> GoldenPathFixture:
    """Deterministically build the P2 golden-path fixture vault and confirm the run.

    Idempotent per §12.8: rebuilding into the same (empty) root with the same clock
    produces identical content hashes. Returns a :class:`GoldenPathFixture`.
    """

    clock = clock or FrozenClock(FIX_NOW)
    now_iso = utc_now_iso(clock)
    paths = _seed_vault(root, clock=clock, now_iso=now_iso)
    vault = load_vault(root)
    repo = Repository(paths.sqlite_path)

    # Owner artifact 1: register + review the blueprint (deterministic stub).
    spec = stub_blueprint()
    blueprint = TB.register_blueprint_version(
        repo, blueprint_slug=BLUEPRINT_SLUG, spec=spec, clock=clock
    )
    TB.place_reading_question(
        repo,
        blueprint_version_id=blueprint.id,
        placement={"section": "symmetric_intro", "phase": "pretest_prime", "pattern": "pretest_prime"},
        clock=clock,
    )
    reviewed = TB.review_blueprint_version(
        repo,
        blueprint_version_id=blueprint.id,
        checks={"source_grounded": True, "rubric_verbatim": True, "one_family": True},
        clock=clock,
    )

    # Reserve the fresh held-out sibling as the assessment surface.
    held_item = _vault_item(vault, HELD_OUT)
    resolved = resolve_legacy_item(vault, repo, held_item, purpose="assessment", clock=clock)

    contract_body = {
        "purpose": "Select the right decomposition/approach for symmetric-matrix / variance tasks",
        "facet_scope": {"concepts": [CONCEPT_ID], "facets": ["method_selection"]},
        "required_capabilities": ["method_selection", "procedure_execution"],
        "baseline_milestone": "m_method_selection_boundary",
        "administration_conditions": {"tools": "none", "open_book": False, "time_minutes": 15},
        "depth_envelope": {
            "envelope_version": "denv_symmetric_v1",
            "bounds": {"target_additions": []},
            "reviewed_edges": [stub_depth_edge()],
        },
        "exemplars": [
            {"id": EXEMPLAR_A, "surface_ref": EXEMPLAR_A, "weight": 1.0},
            {"id": EXEMPLAR_B, "surface_ref": EXEMPLAR_B, "weight": 1.0},
        ],
    }
    receipt = GPC.confirm_exemplar_and_start(
        repo,
        goal_id=GOAL_ID,
        blueprint_version_id=reviewed.id,
        contract_body=contract_body,
        depth_preset="master_tasks_like_these",
        source_rev=SOURCE_REV,
        unit_id=UNIT_ID,
        assessment_surface_id=resolved.surface_id,
        assessment_eligibility={"is_unseen": True, "reason": "fresh_held_out_sibling"},
        clock=clock,
    )

    gc_row = repo.fetch_goal_contract_version(receipt.goal_contract_version_id)
    return GoldenPathFixture(
        root=root,
        receipt=receipt,
        blueprint_version_id=reviewed.id,
        blueprint_content_hash=reviewed.content_hash,
        assessment_surface_id=resolved.surface_id,
        goal_contract_content_hash=gc_row["content_hash"] if gc_row else "",
        exemplar_refs=(EXEMPLAR_A, EXEMPLAR_B),
        held_out_ref=HELD_OUT,
    )


def _vault_item(vault: Any, item_id: str) -> Any:
    item = vault.practice_items.get(item_id)
    if item is None:
        raise ValueError(f"fixture practice item missing: {item_id}")
    return item
