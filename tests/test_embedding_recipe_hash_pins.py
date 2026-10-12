"""Pinned embedding content hashes: a stored vector is keyed by its recipe's hash.

A recipe whose hash moves for unchanged input re-buys every stored vector of
that kind, so the pins below are literal digests of fixed sample inputs. All
pins except the two Slice 2 T5 recipes were computed on main before the T5
merge (f948926d), when T5 moved the facet/definition text composition into
``facet_definition_text`` and ``EmbeddingRecipe.record``; the merge must match
them exactly. Phase 5a's ``item/skeleton`` was pinned at its merge from the
branch's own hash composition. A deliberate recipe change bumps that recipe's
version (and thereby its hash) and updates its pins here, never silently.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from learnloop.diagnosis.split import embeddings as split_embeddings
from learnloop.diagnosis.split.retrieval import content_hash as divergence_hash
from learnloop.ops.contamination.recipes import CONTAMINATION_RECIPES
from learnloop.vault.embedding_recipes import (
    EMBEDDING_RECIPES,
    concept_definition_text,
    facet_definition_text,
)
from learnloop.vault.models import EvidenceFacet


FACETS = {
    "f_full": EvidenceFacet(
        id="f_full", title="Spectral theorem",
        claim="A real symmetric matrix is orthogonally diagonalizable.",
        description="Über alles: eigenvalues λ are real — «quoted» text.\nSecond line.",
        preconditions=["A is real", "A = Aᵀ"], postconditions=["Q is orthogonal"],
        applicability=["square matrices"], positive_examples=["[[2,1],[1,2]]"],
        negative_examples=["[[0,1],[0,0]]"], non_goals=["complex Hermitian case"],
        instructional_repairs=["Check symmetry first."], error_signatures=["sig"],
        aliases=["alias"], tags=["t"],
    ),
    "f_title_only": EvidenceFacet(id="f_title_only", title="Only a title"),
    "f_blank_desc": EvidenceFacet(
        id="f_blank_desc", title="T", claim="C", description="   ", preconditions=["", " spaced "],
    ),
    "f_no_title": EvidenceFacet(id="f_no_title", claim="Claim without title", non_goals=["x"]),
    "f_retired": EvidenceFacet(id="f_retired", title="Retired", status="retired"),
}
ITEMS = {
    "i1": SimpleNamespace(status="active", prompt="Compute det(A) for A = [[1,2],[3,4]]."),
    "i2": SimpleNamespace(status="active", prompt="Ünïcödé prompt — with λ and\nnewlines."),
    "i3": SimpleNamespace(status="retired", prompt="Retired prompt"),
}
TEXTS = ("Scope: what the facet covers.", "Ünïcödé — λ\nline two")

FACET_DEFINITION_PINS = {
    "f_blank_desc": "29e08b57f7ec57d8b836e89a9bd7d11afd244c08528d66e8024cfb6ae92c88e5",
    "f_full": "d9041b2f49e0305ed484a3a7f326d4478f38452a6f8dba1f4809ea73b76c887d",
    "f_no_title": "a03b9947af5b418ec8698c1d7e40173771a86106357b62f068cdbbe420bfd53b",
    "f_title_only": "d23728ebb65eb0fe9c0151e8ad85fbcfa2acc00b41c841036bffbd0b8f5b16fb",
}
ITEM_STEM_PINS = {
    "i1": "1eef498ae6b7220819b942e3786df360962952c5249852bbd4bb58256d99e85e",
    "i2": "90ebf219aeb2a12b1dc362b22922712d7a59f79697ef9aff395931f64d6914ce",
}
# Recipe name -> hashes of TEXTS, in order.
TEXT_PINS = {
    "facet/dossier_contrast": (
        "a101ec8a11803df4bc3e2a2994a0c1e61e314820b00a9d92e432efb3dacb9d5b",
        "4142b3cf2ac1d4a738e898d35a0e59ef716448efb6fbd9bfdd46622a42bd7e67",
    ),
    "facet/dossier_errors": (
        "e47719e18d362fa2c633af56b47dd6ab0a39faa64fa2f9386c63ec19d5ff737f",
        "c448c3a8a1e1774769e324c61a3416ed65ebafb42dc4146546a84b1e1eb53774",
    ),
    "facet/dossier_moves": (
        "6a93f3f70e7cee57ec8c5b50532f46ca83a5181967e29142fa942230ecbf8362",
        "f91115d40a4d74b22284829a36bd8465710adbac90eaf5df589e9fc6d5dad788",
    ),
    "facet/dossier_scope": (
        "f32578ff67571a8d7ec905c3498aaa5adabe36cc9e214a46a074adff7edbe75a",
        "320dbcc3fbe410227a30ce40998008f6743e8988e61311eaa5131e4cb608021e",
    ),
}
CONTAMINATION_PINS = {
    "exam_span/text": (
        "fc62337ac1258b37a037e36497da785c5c6fbbd02cddf30da510bec1d96e1d3f",
        "74dadfce6416e01264a6646b3b77eaf20e92e3f04a21649d3e4c671bb1928f95",
    ),
    "item/expected_answer": (
        "54c9b85c505952cadabff9ab19c4065aa0e93a82f04968650bcb0eac4bd5a738",
        "daf11a06f4cec78dd24d21d803f2c89f333652fdd3637c2cddd093745d72ae8f",
    ),
    "item/stem": (
        "d9e2d3e2488feb336d055050366ba18fc1f5f4b03cbd826f185ceadd9351092a",
        "69c7b3d469f12c6a53cd9d082461038ad7cb5d73e9fe255f8b71711f8067ec07",
    ),
    "question_event/answer": (
        "9ea4b885f514075bf23584c676cb557b840116a1801943ee9c8b44471302deef",
        "fd2cc1750a458c476c4bbfd60ed6191a6f0c121a379431dd79d86b38cd24cac0",
    ),
    "surface/statement": (
        "97fe597432d63c4870d394c09ea521180b1f71a6ae0ba2a29f614efe8ec8d9ab",
        "516fc7b75dcb5f9c015fe8ae885a9970636f7455c3a04f4b4b0fe2f1fc96bb89",
    ),
}


def test_facet_definition_and_item_stem_hashes_are_pinned():
    loaded = SimpleNamespace(evidence_facets=FACETS, practice_items=ITEMS)
    facets = {r.record_id: r for r in EMBEDDING_RECIPES["facet/definition"].records(loaded)}
    assert {key: r.content_hash for key, r in facets.items()} == FACET_DEFINITION_PINS
    # The ingest-side text helper composes a proposal payload the same way.
    for facet_id, record in facets.items():
        assert facet_definition_text(FACETS[facet_id].model_dump(mode="json")) == record.text
    stems = EMBEDDING_RECIPES["item/stem"].records(loaded)
    assert {r.record_id: r.content_hash for r in stems} == ITEM_STEM_PINS


@pytest.mark.parametrize("name", sorted(TEXT_PINS))
def test_dossier_recipe_hashes_are_pinned(name):
    recipe = EMBEDDING_RECIPES[name]
    assert tuple(recipe.content_hash(text) for text in TEXTS) == TEXT_PINS[name]
    assert recipe.record("r", TEXTS[0]).content_hash == TEXT_PINS[name][0]


def test_database_backed_recipe_hashes_are_pinned():
    # Slice 1 M2's kinds hash outside EmbeddingRecipe; reuse must not move them.
    hypothesis = split_embeddings.hypothesis_text(
        {"statement": "Confuses rows with columns", "operation": "transpose_swap"},
    )
    assert split_embeddings._record("hypothesis", "statement", 1, "ep1", hypothesis).content_hash == (
        "a788d491416f3514b0c540420187fa7b6dc0a953cca60b3bc0cf6e0013509cd6"
    )
    assert split_embeddings.misconception_record(
        "durable:m1", "Believes det(A+B) = det A + det B",
    ).content_hash == "67ec1fffcc7d6942c363d2770a3d3b6dd352c6b816d8501825c40f0dce2c7e4e"
    assert divergence_hash("Stem\nQuote: x\nError types: sign") == (
        "21209a1ab1a0e120ca32b981bee2118213d749ee6963e76519969a120bb165fb"
    )


def test_contamination_recipe_hashes_are_pinned():
    assert sorted(CONTAMINATION_RECIPES) == sorted(CONTAMINATION_PINS)
    for name, pins in CONTAMINATION_PINS.items():
        assert tuple(CONTAMINATION_RECIPES[name].content_hash(text) for text in TEXTS) == pins, name


def test_slice_2_t5_recipe_hashes_are_pinned():
    # First pinned at the T5 merge, from T5's own implementation.
    concept = SimpleNamespace(
        title="Symmetric matrix", type="definition",
        description="A square matrix equal to its transpose.", aliases=["self-adjoint", " "],
    )
    assert EMBEDDING_RECIPES["concept/definition"].content_hash(concept_definition_text(concept)) == (
        "79348c7950e9bdb6f58917a6ef2b83a37a7f561e39f343f61f785624fb49dc8b"
    )
    assert EMBEDDING_RECIPES["facet_repair/text"].content_hash("Check symmetry first.") == (
        "052cfbc04bd2b55311642accddbc183ecf4cdd5dfee6e5f8d4b086da80ded2d2"
    )


def test_phase_5a_item_skeleton_recipe_hashes_are_pinned():
    # First pinned at the Phase 5a merge: sha256 of ["item", "skeleton", 1, text],
    # the composition the branch's own recipe used.
    recipe = EMBEDDING_RECIPES["item/skeleton"]
    pins = (
        "b4e0996060f5c883df2d5d26578f7d34aac2f3db8a13e28ee7daebc8de51072b",
        "74e84869cf02c6b408c4540a0557b55bfa63e072b688d46810888d611576d14d",
    )
    assert tuple(recipe.content_hash(text) for text in TEXTS) == pins
    assert recipe.record("pi_1", TEXTS[0]).content_hash == pins[0]


def test_slice_2_t6_source_block_recipe_hashes_are_pinned():
    # First pinned at Slice 2 T6, from T6's own composition: sha256 of
    # ["source_block", "text", 1, text], where text is "Section: <header text
    # path>\n<whitespace-collapsed block text>" (header refs resolved).
    from learnloop.db.stores.source_block_fts import BlockRow
    from learnloop.source_retrieval.recipes import SOURCE_RETRIEVAL_RECIPES, source_block_text

    recipe = SOURCE_RETRIEVAL_RECIPES["source_block/text"]
    assert tuple(recipe.content_hash(text) for text in TEXTS) == (
        "c2850b583a37b3f67b00bf1b428ad1163d7742a84c07293b0cb29f40d0a88900",
        "a8192054db2629be071b0dd31202ce416c06133cb5c985aa82ccdfcb383ef146",
    )
    block = BlockRow("ext_1", "s2", "Text", "  Eigenvalues are   the roots\nof det(A - tI).  ", 3,
                     '["/page/3/SectionHeader/1", "anchor"]', 2, None)
    text = source_block_text(block, {"/page/3/SectionHeader/1": "Chapter 5 Eigenvalues"})
    assert text == "Section: Chapter 5 Eigenvalues > anchor\nEigenvalues are the roots of det(A - tI)."
    assert recipe.record("ext_1/s2", text).content_hash == (
        "9b438f0f183b8b5811c61a760e8d1d0aaaf1891533602a1abae462a79cddd5e4"
    )
