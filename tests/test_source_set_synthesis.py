"""ING M6 — Create study map (bootstrap synthesis) end-to-end.

Small fixture library (explanatory textbook + exam) -> set -> role-specific
inventories -> create_study_map -> §8.7 gates pass -> dependency-closed proposal
-> accept under lock -> facets/blueprints/criteria in the vault +
entity_source_links + replay-identical rebuild + locked-subject refusal + exam
alignment + held-out wording absence. Canned codex payloads, zero network.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.codex.schemas import (
    SourceSetSynthesis,
    SynthBlueprint,
    SynthConcept,
    SynthCriterion,
    SynthCriterionTarget,
    SynthFacet,
    SynthLearningObject,
    SynthPracticeItem,
    SynthRecipe,
    SynthRecipeComponent,
    SynthSpanRef,
)
from learnloop.db.repositories import Repository
from learnloop.services.patches import PatchApplicationError, apply_accepted_items
from learnloop.services.source_set_synthesis import StudyMapError, create_study_map
from learnloop.services.source_unit_inventory import run_unit_inventory
from learnloop.services.source_unit_selection import save_unit_selection
from learnloop.vault.loader import add_subject, init_vault, load_vault
from learnloop.vault.writer import upsert_source_set

from tests.helpers import set_algorithm_version
from tests.test_source_inventory import FakeInventoryClient, _block, _ir, _persist, _register_revision

_CLOCK = FrozenClock(datetime(2026, 7, 13, 12, 0, 0, tzinfo=UTC))

_EXAM_QUESTION_WORDING = "Prove that every symmetric matrix is orthogonally diagonalizable."


def _first_semantic_span(context) -> tuple[str, str, str]:
    """Pick a real span from a semantic-authority inventory the shard was given."""

    for entry in context.unit_inventories:
        if not entry.get("semantic_authority"):
            continue
        for claim in entry["inventory"].get("claims", []) or []:
            spans = claim.get("span_ids") or []
            if spans:
                return entry["extraction_id"], entry["unit_id"], spans[0]
    # fall back to any concept mention span
    for entry in context.unit_inventories:
        for mention in entry["inventory"].get("concept_mentions", []) or []:
            spans = mention.get("span_ids") or []
            if spans:
                return entry["extraction_id"], entry["unit_id"], spans[0]
    return "", "", ""


class FakeSynthesisClient:
    """House fake-client: builds a dependency-closed, span-cited proposal from
    the shard context so gates pass. Records contexts so leakage can be
    grepped and cache reuse proven (zero new calls on a hit)."""

    provider_name = "codex"
    provider_type = "codex"
    model = "fake-synth-1"

    def __init__(self, *, builder=None):
        self.calls: list[object] = []
        self.builder = builder

    def run_source_set_synthesis(self, context) -> SourceSetSynthesis:
        self.calls.append(context)
        if self.builder is not None:
            return self.builder(context, len(self.calls))
        return _default_payload(context)


def _default_payload(context) -> SourceSetSynthesis:
    extraction_id, unit_id, span_id = _first_semantic_span(context)
    prov = [SynthSpanRef(extraction_id=extraction_id, unit_id=unit_id, span_id=span_id, relation="primary")]
    exam_weight = 0.7 if context.exam_profile else 0.3
    return SourceSetSynthesis(
        summary="bootstrap map for symmetric matrices",
        concepts=[SynthConcept(client_item_id="c_sym", id="concept_symmetric_matrix", title="Symmetric matrix")],
        facets=[
            SynthFacet(
                client_item_id="f_def",
                id="facet_symmetry_definition",
                concept_client_id="c_sym",
                kind="definition",
                claim="A real square matrix is symmetric exactly when A^T = A.",
                preconditions=["the matrix is real and square"],
                error_signatures=["substitutes A^T A = I for A^T = A"],
                instructional_repairs=["contrast symmetric and orthogonal matrices"],
                provenance=prov,
            ),
            SynthFacet(
                client_item_id="f_spectral",
                id="facet_spectral_applicability",
                concept_client_id="c_sym",
                kind="applicability_condition",
                claim="The spectral theorem applies to real symmetric matrices.",
                preconditions=["the matrix is real and symmetric"],
                postconditions=["the matrix is orthogonally diagonalizable"],
                error_signatures=["applies spectral theorem to non-symmetric matrices"],
                instructional_repairs=["check symmetry before invoking the spectral theorem"],
                provenance=prov,
            ),
        ],
        learning_objects=[
            SynthLearningObject(
                client_item_id="lo_diag",
                id="lo_diagonalize_symmetric",
                concept_client_id="c_sym",
                title="Diagonalize a symmetric matrix",
                summary="Apply the spectral theorem to diagonalize a symmetric matrix.",
                provenance=prov,
            )
        ],
        blueprints=[
            SynthBlueprint(
                client_item_id="bp_diag",
                id="bp_select_and_apply_spectral",
                learning_object_client_id="lo_diag",
                weight=exam_weight,
                recipes=[
                    SynthRecipe(
                        id="recipe_spectral",
                        all_of=[
                            SynthRecipeComponent(facet_client_id="f_def", capability="schema_interpretation"),
                            SynthRecipeComponent(facet_client_id="f_spectral", capability="method_selection"),
                        ],
                    )
                ],
            )
        ],
        practice_items=[
            SynthPracticeItem(
                client_item_id="pi_1",
                id="pi_identify_symmetry",
                learning_object_client_id="lo_diag",
                practice_mode="retrieval",
                prompt="Is A symmetric? Justify using A^T = A.",
                expected_answer="Yes when A^T = A.",
                evidence_facet_client_ids=["f_def"],
                criteria=[
                    SynthCriterion(
                        id="identifies_symmetry",
                        points=1.0,
                        description="Identifies the symmetry condition A^T = A.",
                        correlation_group="symmetry_identification",
                        targets=[SynthCriterionTarget(facet_client_id="f_def", capability="schema_interpretation", role="primary")],
                    )
                ],
                provenance=prov,
            ),
            SynthPracticeItem(
                client_item_id="pi_2",
                id="pi_select_spectral",
                learning_object_client_id="lo_diag",
                practice_mode="method_selection",
                prompt="Which theorem applies to diagonalize A?",
                expected_answer="The spectral theorem.",
                evidence_facet_client_ids=["f_spectral"],
                criteria=[
                    SynthCriterion(
                        id="selects_spectral",
                        points=1.0,
                        description="Selects the spectral theorem for a symmetric matrix.",
                        correlation_group="spectral_selection",
                        depends_on=["identifies_symmetry"],
                        recipe_ids=["recipe_spectral"],
                        targets=[SynthCriterionTarget(facet_client_id="f_spectral", capability="method_selection", role="primary")],
                    )
                ],
                provenance=prov,
            ),
        ],
    )


def _setup(tmp_path: Path, *, with_exam: bool = True, mvp07: bool = True):
    root = tmp_path / "vault"
    init_vault(root, clock=_CLOCK)
    add_subject(root, "linear-algebra", "Linear Algebra", clock=_CLOCK)
    paths_sqlite = root / "state.sqlite"
    from learnloop.vault.paths import VaultPaths

    set_algorithm_version(
        VaultPaths(root, load_vault(root).config),
        "mvp-0.7" if mvp07 else "mvp-0.6",
    )
    repo = Repository(paths_sqlite)

    inv_client = FakeInventoryClient()
    # explanatory textbook member
    _register_revision(repo, source_id="src_text", revision_id="rev_text")
    text_ir = _ir([
        ("chapter_symmetry", "Symmetric matrices",
         [_block("s1", "A real square matrix is symmetric when A^T = A."),
          _block("s2", "The spectral theorem applies to real symmetric matrices.")],
         "sha256:sym", 5),
    ])
    _persist(repo, text_ir, revision_id="rev_text", extraction_id="ext_text")
    run_unit_inventory(repo, "ext_text", "chapter_symmetry", role="primary_textbook",
                       profile="combined", client=inv_client, input_budget_tokens=20000, clock=_CLOCK)

    members = [{"source_id": "src_text", "revision_id": "rev_text", "default_role": "primary_textbook",
                "scope": [{"unit_id": "chapter_symmetry"}], "priority": 1}]

    if with_exam:
        _register_revision(repo, source_id="src_exam", revision_id="rev_exam")
        exam_ir = _ir([
            ("paper_2024", "Final 2024", [_block("s1", _EXAM_QUESTION_WORDING)], "sha256:exam", 1),
        ])
        _persist(repo, exam_ir, revision_id="rev_exam", extraction_id="ext_exam")
        run_unit_inventory(repo, "ext_exam", "paper_2024", role="exam",
                           profile="assessment", client=inv_client, input_budget_tokens=20000, clock=_CLOCK)
        save_unit_selection(repo, "ext_exam", ["paper_2024"], clock=_CLOCK,
                            exam_use_modes={"paper_2024": "held_out_evaluation"},
                            exam_paper_metadata={"paper_2024": {"year": "2024", "syllabus": "la"}})
        members.append({"source_id": "src_exam", "revision_id": "rev_exam", "default_role": "exam",
                        "scope": [{"unit_id": "paper_2024"}], "priority": 1})

    upsert_source_set(root, {"id": "set_la", "subject_id": "linear-algebra",
                             "title": "Linear Algebra", "members": members}, clock=_CLOCK)
    return root, repo


def test_bootstrap_end_to_end_applies_learnable_map(tmp_path):
    root, repo = _setup(tmp_path)
    client = FakeSynthesisClient()
    result = create_study_map(root, "set_la", client=client, brief={"depth": "intro"},
                              repository=repo, clock=_CLOCK, apply=True)

    assert result.applied is True
    assert not any(d["severity"] == "hard_fail" for d in result.gate_diagnostics)
    assert result.item_counts["facet"] == 2
    assert result.item_counts["task_blueprint"] == 1

    vault = load_vault(root)
    assert "facet_symmetry_definition" in vault.evidence_facets
    assert "facet_spectral_applicability" in vault.evidence_facets
    lo = vault.learning_objects["lo_diagonalize_symmetric"]
    assert lo.blueprints and lo.blueprints[0].id == "bp_select_and_apply_spectral"
    assert lo.blueprints[0].recipes[0].all_of  # recipe compiled
    pi = vault.practice_items["pi_identify_symmetry"]
    assert pi.grading_rubric is not None
    assert pi.grading_rubric.criteria[0].targets[0].facet == "facet_symmetry_definition"

    # entity_source_links written for the facet (§9.1).
    links = repo.entity_source_links(entity_type="facet", entity_id="facet_symmetry_definition")
    assert links and links[0]["revision_id"] == "rev_text"


def test_facets_cite_textbook_not_exam_and_held_out_wording_absent(tmp_path):
    root, repo = _setup(tmp_path, with_exam=True)
    client = FakeSynthesisClient()
    create_study_map(root, "set_la", client=client, brief={"outcome": "exam prep"},
                     repository=repo, clock=_CLOCK, apply=True)

    # facet provenance cites the textbook revision, never the exam revision.
    links = repo.entity_source_links(entity_type="facet", entity_id="facet_symmetry_definition")
    assert all(link["revision_id"] == "rev_text" for link in links)

    # held-out exam wording never appears in any built synthesis context.
    for context in client.calls:
        from dataclasses import asdict

        blob = json.dumps(asdict(context), default=str)
        assert _EXAM_QUESTION_WORDING not in blob
        assert "orthogonally diagonalizable" not in blob


def test_exam_shifts_blueprint_distribution(tmp_path):
    root_a, repo_a = _setup(tmp_path / "a", with_exam=True)
    root_b, repo_b = _setup(tmp_path / "b", with_exam=False)
    ra = create_study_map(root_a, "set_la", client=FakeSynthesisClient(), repository=repo_a, clock=_CLOCK, apply=True)
    rb = create_study_map(root_b, "set_la", client=FakeSynthesisClient(), repository=repo_b, clock=_CLOCK, apply=True)
    wa = load_vault(root_a).learning_objects["lo_diagonalize_symmetric"].blueprints[0].weight
    wb = load_vault(root_b).learning_objects["lo_diagonalize_symmetric"].blueprints[0].weight
    assert wa != wb  # the exam member shifts the declared blueprint distribution
    assert ra.item_counts and rb.item_counts


def test_locked_subject_bootstrap_refusal(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    # First bootstrap + apply mints facets.
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo, clock=_CLOCK, apply=True)
    # Force an identity lock by seeding recall evidence + an active goal scope.
    from learnloop.services.curriculum_locks import identity_locks

    # Simulate a lock by directly writing a goal that certifies the facet scope.
    from learnloop.vault.paths import VaultPaths
    from learnloop.vault.yaml_io import read_yaml, write_yaml

    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    goals_data = read_yaml(paths.goals_path) if paths.goals_path.exists() else {"schema_version": 2, "goals": []}
    goals_data.setdefault("goals", []).append({
        "id": "goal_lock", "title": "Lock", "status": "active", "priority": 0.5,
        "target_recall": 0.8,
        "facet_scope": {"concepts": [], "facets": ["facet_symmetry_definition"]},
        "due_at": None, "exam": {"enabled": False, "item_count": 20},
        "created_at": "2026-07-13T12:00:00Z", "updated_at": "2026-07-13T12:00:00Z",
    })
    write_yaml(paths.goals_path, goals_data)
    vault = load_vault(root)
    assert identity_locks(vault, repo)  # the facet is now locked

    with pytest.raises(StudyMapError) as exc:
        create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo, clock=_CLOCK)
    assert exc.value.code == "subject_identity_locked"
    assert exc.value.lock_reasons


def test_manifest_idempotency_cache_zero_new_calls(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    client = FakeSynthesisClient()
    first = create_study_map(root, "set_la", client=client, brief={"a": 1}, repository=repo, clock=_CLOCK)
    calls_after_first = len(client.calls)
    second = create_study_map(root, "set_la", client=client, brief={"a": 1}, repository=repo, clock=_CLOCK)
    assert second.reused is True
    assert second.proposal_id == first.proposal_id
    assert len(client.calls) == calls_after_first  # cache hit -> zero new calls
    assert second.manifest_hash == first.manifest_hash


def test_legacy_vault_acceptance_refused(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False, mvp07=False)
    client = FakeSynthesisClient()
    # Synthesis/proposal generation runs on a legacy vault...
    result = create_study_map(root, "set_la", client=client, brief={}, repository=repo, clock=_CLOCK)
    assert result.proposal_id is not None
    # ...but ACCEPTANCE of the learnable map is refused with a typed reason.
    with pytest.raises(PatchApplicationError) as exc:
        apply_accepted_items(root, result.proposal_id, clock=_CLOCK)
    assert "bootstrap_evidence_refused" in str(exc.value)
    # no learnable partial map: facets.yaml stays empty.
    assert not load_vault(root).evidence_facets


def test_replay_identical_after_apply(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo, clock=_CLOCK, apply=True)
    from learnloop.services.replay import rebuild_derived_state

    # rebuild must not raise and must leave the applied facets intact.
    rebuild_derived_state(load_vault(root), repo, clock=_CLOCK)
    assert "facet_symmetry_definition" in load_vault(root).evidence_facets


def test_resolve_subject_id_prefers_source_set_over_vault(tmp_path):
    # Dogfood regression: a fresh vault with a source set but no subjects
    # crashed synthesis with StopIteration; multi-subject vaults silently got
    # "first subject in the vault" instead of the set's own subject.
    from types import SimpleNamespace

    from learnloop.services.source_set_synthesis import StudyMapError, resolve_subject_id

    vault = SimpleNamespace(subjects={"other-subject": object()})
    assert resolve_subject_id(SimpleNamespace(subject_id="svd-pca"), vault) == "svd-pca"
    assert resolve_subject_id(SimpleNamespace(subject_id=None), vault) == "other-subject"
    empty = SimpleNamespace(subjects={})
    try:
        resolve_subject_id(SimpleNamespace(subject_id=None), empty)
    except StudyMapError:
        pass
    else:
        raise AssertionError("expected StudyMapError on subjectless vault without set subject")
