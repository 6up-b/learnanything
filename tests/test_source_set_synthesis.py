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
from learnloop.services.source_set_synthesis import (
    StudyMapError,
    _namespace_synthesis_shard,
    create_study_map,
)
from learnloop.services.source_unit_inventory import run_unit_inventory
from learnloop.services.source_unit_selection import save_unit_selection
from learnloop.vault.loader import add_subject, init_vault, load_vault
from learnloop.vault.writer import upsert_source_set

from tests.helpers import set_algorithm_version
from tests.test_source_inventory import FakeInventoryClient, _block, _ir, _persist, _register_revision

_CLOCK = FrozenClock(datetime(2026, 7, 13, 12, 0, 0, tzinfo=UTC))

_EXAM_QUESTION_WORDING = "Prove that every symmetric matrix is orthogonally diagonalizable."


def test_synthesis_capabilities_use_closed_vocabulary():
    with pytest.raises(ValueError):
        SynthCriterionTarget(capability="apply complement rule")
    with pytest.raises(ValueError):
        SynthRecipeComponent(capability="identify sample space")


def test_synthesis_shards_namespace_declarations_and_references():
    result = SourceSetSynthesis(
        concepts=[SynthConcept(client_item_id="concept_shared")],
        facets=[
            SynthFacet(
                client_item_id="facet_shared",
                concept_client_id="concept_shared",
            )
        ],
        learning_objects=[
            SynthLearningObject(
                client_item_id="lo_shared",
                concept_client_id="concept_shared",
                prerequisite_concept_client_ids=["concept_shared"],
            )
        ],
        practice_items=[
            SynthPracticeItem(
                client_item_id="pi_shared",
                learning_object_client_id="lo_shared",
                evidence_facet_client_ids=["facet_shared"],
                depends_on_client_item_ids=["facet_shared"],
            )
        ],
    )

    namespaced = _namespace_synthesis_shard(result, 1)

    assert namespaced.concepts[0].client_item_id == "shard_2__concept_shared"
    assert namespaced.facets[0].concept_client_id == "shard_2__concept_shared"
    assert namespaced.learning_objects[0].prerequisite_concept_client_ids == [
        "shard_2__concept_shared"
    ]
    assert namespaced.practice_items[0].evidence_facet_client_ids == [
        "shard_2__facet_shared"
    ]
    assert namespaced.practice_items[0].depends_on_client_item_ids == [
        "shard_2__facet_shared"
    ]


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


def test_bootstrap_canonicalizes_prerequisite_and_confusable_concepts(tmp_path):
    root, repo = _setup(tmp_path)

    def builder(context, _call_count):
        payload = _default_payload(context)
        payload.concepts.extend(
            [
                SynthConcept(
                    client_item_id="c_orthogonal",
                    id="concept_orthogonal_matrix",
                    title="Orthogonal matrix",
                    aliases=["orthogonal matrices"],
                ),
                SynthConcept(
                    client_item_id="c_general_diag",
                    id="concept_general_diagonalization",
                    title="General diagonalization",
                ),
            ]
        )
        learning_object = payload.learning_objects[0]
        learning_object.prerequisite_concept_client_ids = ["c_orthogonal"]
        learning_object.confusable_concept_client_ids = ["c_general_diag"]
        return payload

    create_study_map(
        root,
        "set_la",
        client=FakeSynthesisClient(builder=builder),
        repository=repo,
        clock=_CLOCK,
        apply=True,
    )

    learning_object = load_vault(root).learning_objects["lo_diagonalize_symmetric"]
    assert learning_object.prerequisites == ["concept_orthogonal_matrix"]
    assert learning_object.confusables == ["concept_general_diagonalization"]


def test_bootstrap_tolerates_unresolved_concept_relationships(tmp_path):
    """An unresolved prerequisite/confusable is dropped with a review diagnostic
    rather than hard-failing the paid synthesis (weaker models emit these)."""

    root, repo = _setup(tmp_path)

    def builder(context, _call_count):
        payload = _default_payload(context)
        payload.learning_objects[0].prerequisites = ["free text that is not a concept"]
        return payload

    result = create_study_map(
        root,
        "set_la",
        client=FakeSynthesisClient(builder=builder),
        repository=repo,
        clock=_CLOCK,
    )

    assert not any(d["severity"] == "hard_fail" for d in result.gate_diagnostics)
    assert any(
        d.get("gate") == "learning_object_concept"
        and "free text that is not a concept" in d.get("message", "")
        for d in result.gate_diagnostics
    )


def test_bootstrap_mints_concept_for_unanchored_learning_object(tmp_path):
    """A learning object emitted with no concept anchor (empty concept_client_id
    AND concept_id — the reported OpenRouter/weak-model failure) gets a concept
    synthesized from its title instead of aborting the whole build."""

    root, repo = _setup(tmp_path)

    def builder(context, _call_count):
        payload = _default_payload(context)
        lo = payload.learning_objects[0]
        lo.concept_client_id = ""
        lo.concept_id = ""
        return payload

    result = create_study_map(
        root,
        "set_la",
        client=FakeSynthesisClient(builder=builder),
        repository=repo,
        clock=_CLOCK,
        apply=True,
    )

    assert result.applied is True
    assert not any(d["severity"] == "hard_fail" for d in result.gate_diagnostics)
    assert any(
        d.get("gate") == "learning_object_concept" and "no concept anchor" in d.get("message", "")
        for d in result.gate_diagnostics
    )
    vault = load_vault(root)
    lo = vault.learning_objects["lo_diagonalize_symmetric"]
    assert lo.concept in vault.concepts


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


# --- robustness: shard checkpoints, consolidation, revalidation --------------


def _setup_two_chapters(tmp_path: Path):
    """A textbook with TWO inventoried chapters so tiny shard budgets split the
    synthesis into two independent shards."""

    root = tmp_path / "vault"
    init_vault(root, clock=_CLOCK)
    add_subject(root, "linear-algebra", "Linear Algebra", clock=_CLOCK)
    from learnloop.vault.paths import VaultPaths

    set_algorithm_version(VaultPaths(root, load_vault(root).config), "mvp-0.7")
    repo = Repository(root / "state.sqlite")

    inv_client = FakeInventoryClient()
    _register_revision(repo, source_id="src_text", revision_id="rev_text")
    text_ir = _ir([
        ("chapter_symmetry", "Symmetric matrices",
         [_block("s1", "A real square matrix is symmetric when A^T = A."),
          _block("s2", "The spectral theorem applies to real symmetric matrices.")],
         "sha256:sym", 5),
        ("chapter_spectral", "Spectral theorem",
         [_block("s3", "Orthogonal diagonalization follows from the spectral theorem."),
          _block("s4", "Symmetric matrices have real eigenvalues.")],
         "sha256:spec", 6),
    ])
    _persist(repo, text_ir, revision_id="rev_text", extraction_id="ext_text")
    for unit_id in ("chapter_symmetry", "chapter_spectral"):
        run_unit_inventory(repo, "ext_text", unit_id, role="primary_textbook",
                           profile="combined", client=inv_client, input_budget_tokens=20000, clock=_CLOCK)
    upsert_source_set(root, {
        "id": "set_la", "subject_id": "linear-algebra", "title": "Linear Algebra",
        "members": [{
            "source_id": "src_text", "revision_id": "rev_text", "default_role": "primary_textbook",
            "scope": [{"unit_id": "chapter_symmetry"}, {"unit_id": "chapter_spectral"}], "priority": 1,
        }],
    }, clock=_CLOCK)
    return root, repo


def test_shard_checkpoints_survive_post_generation_failure(tmp_path):
    """A failure AFTER the shards ran must not re-pay their model calls: the
    retry reuses every checkpointed shard at zero calls."""

    root, repo = _setup_two_chapters(tmp_path)
    client = FakeSynthesisClient()

    with pytest.raises(StudyMapError) as excinfo:
        create_study_map(
            root, "set_la", client=client, brief={"depth": "intro"},
            repository=repo, clock=_CLOCK,
            budget_overrides={"synthesis_shard_input_tokens": 1, "synthesis_output_tokens": 1},
        )
    assert excinfo.value.code == "budget_exceeded"
    paid_calls = len(client.calls)
    assert paid_calls == 2  # one per shard

    result = create_study_map(
        root, "set_la", client=client, brief={"depth": "intro"},
        repository=repo, clock=_CLOCK,
        budget_overrides={"synthesis_shard_input_tokens": 1},
    )
    assert len(client.calls) == paid_calls  # zero new model calls
    run = repo.synthesis_run(result.synthesis_run_id)
    assert run["actual_usage"]["reused_shards"] == 2
    assert run["actual_usage"]["shard_count"] == 2
    assert run["actual_usage"]["calls"] == 0


def test_synthesis_can_disable_local_token_ceilings(tmp_path):
    root, repo = _setup_two_chapters(tmp_path)

    result = create_study_map(
        root,
        "set_la",
        client=FakeSynthesisClient(),
        brief={"depth": "unlimited-budget"},
        repository=repo,
        clock=_CLOCK,
        budget_overrides={
            "synthesis_shard_input_tokens": 1,
            "synthesis_shard_output_tokens": 1,
            "synthesis_total_input_ceiling": 1,
            "synthesis_output_tokens": 1,
        },
        unlimited_token_budget=True,
    )

    assert result.proposal_id is not None
    run = repo.synthesis_run(result.synthesis_run_id)
    manifest = repo.synthesis_manifest(run["manifest_id"])
    assert manifest["token_budget"]["unlimited"] is True


def test_cross_shard_same_title_concepts_consolidate_deterministically(tmp_path):
    """Two shards re-declaring the identically-titled concept collapse into one
    proposal row, with every shard-2 reference rewritten to the survivor."""

    root, repo = _setup_two_chapters(tmp_path)
    client = FakeSynthesisClient()
    result = create_study_map(
        root, "set_la", client=client, brief={"depth": "intro"},
        repository=repo, clock=_CLOCK,
        budget_overrides={"synthesis_shard_input_tokens": 1},
    )
    # Both shards emitted "Symmetric matrix"; only one concept survives while
    # both shards' facets/LOs/practice items are kept and still resolve.
    assert result.item_counts["concept"] == 1
    assert result.item_counts["facet"] == 4
    assert result.item_counts["learning_object"] == 2
    assert not any(d["severity"] == "hard_fail" for d in result.gate_diagnostics)


def _distinct_title_builder(context, _n):
    payload = _default_payload(context)
    payload.concepts[0].title = f"Symmetric matrix (chapter {context.shard_ordinal + 1})"
    return payload


def test_graph_structuring_merges_near_duplicates_and_authors_relations(tmp_path):
    """The structuring pass sees the whole span (concept list + source
    skeletons) and both folds differently-titled duplicates and authors
    part_of/prerequisite relations over the post-merge survivors."""

    class StructuringClient(FakeSynthesisClient):
        def __init__(self):
            super().__init__(builder=_distinct_title_builder)
            self.structuring_contexts = []

        def run_concept_graph_structuring(self, context):
            self.structuring_contexts.append(context)
            from learnloop.codex.schemas import (
                ConceptGraphStructuring,
                ConceptMergeGroup,
                ConceptRelation,
            )

            ids = [c["client_item_id"] for c in context.concepts]
            return ConceptGraphStructuring(
                merge_groups=[ConceptMergeGroup(canonical_client_id=ids[0], duplicate_client_ids=ids[1:])],
                relations=[
                    # References the merged-away duplicate: must be rewritten to
                    # the canonical survivor and then dropped as a self-edge.
                    ConceptRelation(source=ids[1], target=ids[0], relation_type="related"),
                ],
            )

    root, repo = _setup_two_chapters(tmp_path)
    client = StructuringClient()
    result = create_study_map(
        root, "set_la", client=client, brief={"depth": "intro"},
        repository=repo, clock=_CLOCK,
        budget_overrides={"synthesis_shard_input_tokens": 1},
    )
    assert len(client.structuring_contexts) == 1
    context = client.structuring_contexts[0]
    # Whole-span context: outline skeletons from cached artifacts, per source.
    assert context.source_skeletons
    unit_labels = {unit["label"] for unit in context.source_skeletons[0]["units"]}
    assert {"Symmetric matrices", "Spectral theorem"} <= unit_labels
    assert result.item_counts["concept"] == 1
    run = repo.synthesis_run(result.synthesis_run_id)
    assert run["actual_usage"]["consolidated_concepts"] == 1
    candidate = run["candidate_output"]
    surviving = candidate["concepts"]
    assert len(surviving) == 1
    assert "Symmetric matrix (chapter 2)" in surviving[0]["aliases"]
    # The related self-edge (after merge rewrite) was dropped, not persisted.
    assert "concept_edge" not in result.item_counts


def test_graph_structuring_relations_become_concept_edges(tmp_path):
    """Authored relations compile into concept_edge proposal items and apply
    into the vault's relations graph."""

    class RelatingClient(FakeSynthesisClient):
        def __init__(self):
            super().__init__(builder=_distinct_title_builder)

        def run_concept_graph_structuring(self, context):
            from learnloop.codex.schemas import ConceptGraphStructuring, ConceptRelation

            ids = [c["client_item_id"] for c in context.concepts]
            return ConceptGraphStructuring(
                relations=[
                    ConceptRelation(source=ids[0], target=ids[1], relation_type="part_of",
                                    rationale="chapter concept sits under the umbrella topic"),
                    ConceptRelation(source=ids[0], target=ids[1], relation_type="prerequisite"),
                    # Cycle attempt: must be dropped with a review diagnostic.
                    ConceptRelation(source=ids[1], target=ids[0], relation_type="prerequisite"),
                    # Unknown endpoint: dropped before normalization.
                    ConceptRelation(source="ghost", target=ids[0], relation_type="related"),
                ],
            )

    root, repo = _setup_two_chapters(tmp_path)
    result = create_study_map(
        root, "set_la", client=RelatingClient(), brief={"depth": "intro"},
        repository=repo, clock=_CLOCK, apply=True,
        budget_overrides={"synthesis_shard_input_tokens": 1},
    )
    assert result.item_counts["concept"] == 2
    assert result.item_counts["concept_edge"] == 2  # part_of + one prerequisite
    assert any(
        d.get("gate") == "concept_graph" and "cycle" in d.get("message", "")
        for d in result.gate_diagnostics
    )
    vault = load_vault(root)
    edge_types = sorted(edge.relation_type for edge in vault.edges)
    assert edge_types == ["part_of", "prerequisite"]
    assert all(edge.source != edge.target for edge in vault.edges)


def test_invalid_structuring_nomination_is_a_noop(tmp_path):
    """Unknown ids from the structuring pass never merge or error."""

    class BogusClient(FakeSynthesisClient):
        def __init__(self):
            super().__init__(builder=_distinct_title_builder)

        def run_concept_graph_structuring(self, context):
            from learnloop.codex.schemas import ConceptGraphStructuring, ConceptMergeGroup

            return ConceptGraphStructuring(merge_groups=[
                ConceptMergeGroup(canonical_client_id="nope", duplicate_client_ids=["also_nope"]),
            ])

    root, repo = _setup_two_chapters(tmp_path)
    result = create_study_map(
        root, "set_la", client=BogusClient(), brief={"depth": "intro"},
        repository=repo, clock=_CLOCK,
        budget_overrides={"synthesis_shard_input_tokens": 1},
    )
    assert result.item_counts["concept"] == 2


def test_lo_prerequisites_derive_concept_edges_without_model_relations(tmp_path):
    """Layer-1 floor: even with no authored relations, LO prerequisites and
    confusables derive prerequisite/confusable_with concept edges."""

    def builder(context, _n):
        payload = _default_payload(context)
        payload.concepts.append(
            SynthConcept(client_item_id="c_ortho", id="concept_orthogonality", title="Orthogonality")
        )
        payload.learning_objects[0].prerequisite_concept_client_ids = ["c_ortho"]
        payload.learning_objects[0].confusable_concept_client_ids = ["c_ortho"]
        return payload

    root, repo = _setup(tmp_path)
    result = create_study_map(
        root, "set_la", client=FakeSynthesisClient(builder=builder), brief={"depth": "intro"},
        repository=repo, clock=_CLOCK, apply=True,
    )
    assert result.item_counts["concept_edge"] == 2
    vault = load_vault(root)
    prereq = next(edge for edge in vault.edges if edge.relation_type == "prerequisite")
    assert prereq.source == "concept_orthogonality"
    assert prereq.target == "concept_symmetric_matrix"
    confusable = next(edge for edge in vault.edges if edge.relation_type == "confusable_with")
    assert {confusable.source, confusable.target} == {"concept_orthogonality", "concept_symmetric_matrix"}


def test_revalidate_saved_candidate_completes_without_model(tmp_path, monkeypatch):
    """A post-generation persistence failure preserves the candidate; a later
    revalidation finishes gates + persistence + apply with zero model calls."""

    from learnloop.services.source_set_synthesis import revalidate_synthesis_candidate

    root, repo = _setup(tmp_path)
    client = FakeSynthesisClient()

    def explode(self, batch, rows):
        raise RuntimeError("disk full")

    monkeypatch.setattr(Repository, "persist_proposal_batch", explode)
    with pytest.raises(RuntimeError, match="disk full"):
        create_study_map(root, "set_la", client=client, brief={"depth": "intro"},
                         repository=repo, clock=_CLOCK)
    monkeypatch.undo()
    paid_calls = len(client.calls)

    with repo.connection() as connection:
        run_id = connection.execute(
            "SELECT id FROM synthesis_runs ORDER BY created_at DESC, id DESC LIMIT 1"
        ).fetchone()["id"]
    assert repo.synthesis_run(run_id)["status"] == "failed"
    assert repo.synthesis_run(run_id)["candidate_output"]

    result = revalidate_synthesis_candidate(root, run_id, apply=True, repository=repo, clock=_CLOCK)

    assert len(client.calls) == paid_calls  # zero model calls
    assert result.applied is True
    assert result.item_counts["facet"] == 2
    run = repo.synthesis_run(run_id)
    assert run["status"] == "completed"
    assert run["proposal_id"] == result.proposal_id
    assert run["actual_usage"]["revalidations"] == 1
    applied = load_vault(root)
    assert "facet_symmetry_definition" in applied.evidence_facets


def test_revalidate_requires_a_preserved_candidate(tmp_path):
    from learnloop.services.source_set_synthesis import revalidate_synthesis_candidate

    root, repo = _setup(tmp_path)
    with pytest.raises(StudyMapError) as excinfo:
        revalidate_synthesis_candidate(root, "missing_run", repository=repo, clock=_CLOCK)
    assert excinfo.value.code == "synthesis_run_not_found"


def test_auto_repair_drops_criterion_id_dependencies(tmp_path):
    """The arxiv_v2 failure class: a shard lists rubric criterion ids in item-level
    depends_on_client_item_ids. The namespacer prefixes them (criterion ids stay
    bare), the closure gate hard-fails on the dangling refs, and a repairing
    revalidation finishes the run with zero model calls."""

    from learnloop.services.source_set_synthesis import revalidate_synthesis_candidate

    def builder(context, _n):
        payload = _default_payload(context)
        payload.practice_items[1].depends_on_client_item_ids = ["identifies_symmetry"]
        return payload

    root, repo = _setup(tmp_path)
    client = FakeSynthesisClient(builder=builder)
    with pytest.raises(StudyMapError) as excinfo:
        create_study_map(root, "set_la", client=client, brief={"depth": "intro"},
                         repository=repo, clock=_CLOCK)
    exc = excinfo.value
    assert exc.code == "synthesis_gate_failed"
    assert exc.candidate_preserved
    assert any("dangling requirement" in d["message"] for d in exc.diagnostics)
    run_id = exc.synthesis_run_id
    paid_calls = len(client.calls)

    # A plain revalidation re-runs the same gates over the same candidate: fails.
    with pytest.raises(StudyMapError) as again:
        revalidate_synthesis_candidate(root, run_id, repository=repo, clock=_CLOCK)
    assert again.value.code == "synthesis_gate_failed"

    result = revalidate_synthesis_candidate(
        root, run_id, repair=True, apply=True, repository=repo, clock=_CLOCK
    )
    assert len(client.calls) == paid_calls  # zero model calls
    assert result.applied is True
    assert [op["op"] for op in result.candidate_repairs] == ["drop_dependency"]
    assert result.candidate_repairs[0]["applied"] is True
    assert result.candidate_repairs[0]["dep"].endswith("identifies_symmetry")
    run = repo.synthesis_run(run_id)
    assert run["status"] == "completed"
    assert run["actual_usage"]["candidate_repairs"][0]["applied"] is True
    # The stored candidate is untouched: the repair log is the audit trail.
    assert run["candidate_output"]["practice_items"][1]["depends_on_client_item_ids"]


def test_derive_candidate_repairs_only_targets_criterion_refs():
    """Dangling deps that don't match an embedded criterion id are left for a
    human or agent: no judgment calls are derived mechanically."""

    from learnloop.services.source_set_synthesis import derive_candidate_repairs

    candidate = {
        "concepts": [{"client_item_id": "shard_1__c"}],
        "practice_items": [
            {
                "client_item_id": "shard_1__p1",
                "depends_on_client_item_ids": [
                    "shard_1__crit_a", "shard_1__truly_missing", "shard_1__c",
                ],
                "criteria": [{"id": "crit_a"}],
            }
        ],
    }
    ops = derive_candidate_repairs(candidate)
    assert [(op["op"], op["dep"]) for op in ops] == [("drop_dependency", "shard_1__crit_a")]


def test_apply_candidate_repairs_vocabulary():
    from learnloop.services.source_set_synthesis import apply_candidate_repairs

    candidate = {
        "concepts": [{"client_item_id": "c1"}],
        "practice_items": [
            {"client_item_id": "p1", "depends_on_client_item_ids": ["ghost", "c_old"], "criteria": []}
        ],
    }
    repaired, log = apply_candidate_repairs(candidate, [
        {"op": "drop_dependency", "item_client_id": "p1", "dep": "ghost"},
        {"op": "remap_dependency", "item_client_id": "p1", "dep": "c_old", "to": "c1"},
        {"op": "drop_dependency", "item_client_id": "p1", "dep": "not_there"},
    ])
    assert repaired["practice_items"][0]["depends_on_client_item_ids"] == ["c1"]
    assert [entry["applied"] for entry in log] == [True, True, False]
    # the input candidate is never mutated
    assert candidate["practice_items"][0]["depends_on_client_item_ids"] == ["ghost", "c_old"]

    with pytest.raises(StudyMapError) as excinfo:
        apply_candidate_repairs(candidate, [{"op": "explode"}])
    assert excinfo.value.code == "unknown_repair_op"
    with pytest.raises(StudyMapError) as excinfo:
        apply_candidate_repairs(
            candidate,
            [{"op": "remap_dependency", "item_client_id": "p1", "dep": "ghost", "to": "nope"}],
        )
    assert excinfo.value.code == "invalid_repair_target"


def test_synthesis_progress_reports_shard_and_stage_messages(tmp_path):
    root, repo = _setup_two_chapters(tmp_path)
    events: list[tuple[str, str, int | None, int | None]] = []

    def progress(stage, message, current, total):
        events.append((stage, message, current, total))

    create_study_map(
        root, "set_la", client=FakeSynthesisClient(), brief={"depth": "intro"},
        repository=repo, clock=_CLOCK, apply=True, progress=progress,
        budget_overrides={"synthesis_shard_input_tokens": 1},
    )
    stages = [event[0] for event in events]
    messages = [event[1] for event in events]
    assert "Synthesizing shard 1 of 2" in messages
    assert "Synthesizing shard 2 of 2" in messages
    assert ("synthesis", "Synthesizing shard 2 of 2", 2, 2) in events
    assert "Running quality gates" in messages
    assert "Persisting the study-map proposal" in messages
    assert "Applying the study map" in messages
    assert stages.index("validation") > stages.index("synthesis")
    assert stages.index("apply") > stages.index("persistence")
