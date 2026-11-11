"""What other test files use from ``tests/test_source_set_synthesis.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.content.synthesis.ai_contracts import (
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
    VaultEpigraph,
    VaultEpigraphBatch,
)
from learnloop.db.repositories import Repository
from learnloop.content.synthesis.source_unit_inventory import run_unit_inventory
from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.vault.loader import add_subject, init_vault, load_vault
from learnloop.vault.writer import upsert_source_set

from tests.structured_ai import StructuredClientFake
from tests.helpers import set_algorithm_version
from tests.source_inventory_helpers import FakeInventoryClient, _block, _ir, _persist, _register_revision


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


class FakeSynthesisClient(StructuredClientFake):
    """House fake-client: builds a dependency-closed, span-cited proposal from
    the shard context so gates pass. Records contexts so leakage can be
    grepped and cache reuse proven (zero new calls on a hit)."""

    provider_name = "codex"
    provider_type = "codex"
    model = "fake-synth-1"

    def __init__(self, *, builder=None, epigraph_builder=None):
        self.calls: list[object] = []
        self.epigraph_calls: list[object] = []
        self.builder = builder
        self.epigraph_builder = epigraph_builder

    def run_source_set_synthesis(self, context) -> SourceSetSynthesis:
        self.calls.append(context)
        if self.builder is not None:
            return self.builder(context, len(self.calls))
        return _default_payload(context)

    def run_vault_epigraphs(self, context) -> VaultEpigraphBatch:
        self.epigraph_calls.append(context)
        if self.epigraph_builder is not None:
            return self.epigraph_builder(context, len(self.epigraph_calls))
        return default_epigraphs()


def default_epigraphs() -> VaultEpigraphBatch:
    return VaultEpigraphBatch(
        epigraphs=[
            VaultEpigraph(kind="quote", lines=["Symmetry is a promise the transpose keeps."]),
            VaultEpigraph(
                kind="haiku",
                lines=["A equals A T", "the spectral theorem waits", "eigenvectors align"],
            ),
            VaultEpigraph(kind="quote", lines=["Escape will make me diagonal."]),
        ]
    )


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


def _distinct_title_builder(context, _n):
    payload = _default_payload(context)
    payload.concepts[0].title = f"Symmetric matrix (chapter {context.shard_ordinal + 1})"
    return payload
