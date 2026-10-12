"""Keyword search, rank fusion and the strict wire contracts of the practice index."""
from __future__ import annotations

import pytest

from learnloop.ai.strict_schema import strict_output_schema
from learnloop.practice_index.contracts import (
    FacetDossierDraft,
    PracticeRerank,
    RelevanceLabels,
    WrittenQueries,
)
from learnloop.practice_index.text import BM25, reciprocal_rank_fusion, tokenize
from learnloop.practice_index.tool import FIND_PRACTICE_TOOL, FindPracticeArguments


def test_tokenizer_folds_case_plurals_and_request_boilerplate():
    assert tokenize("Give me practice questions on Eigenvalues!") == ["eigenvalue"]
    assert tokenize("class glass") == ["class", "glass"]


def test_bm25_ranks_overlap_and_omits_documents_without_it():
    index = BM25({
        "a": "eigenvalues of a diagonal matrix",
        "b": "determinant by cofactor expansion",
        "c": "eigenvalues eigenvalues characteristic polynomial",
    })
    assert index.ranking("eigenvalue practice") == ["c", "a"]
    assert index.ranking("eigenvalue", candidates=["a", "b"]) == ["a"]
    assert index.ranking("unrelated words") == []


def test_reciprocal_rank_fusion_uses_ranks_and_breaks_ties_by_id():
    order, ranks = reciprocal_rank_fusion({"x": ["a", "b"], "y": ["b", "c"]}, k=60)
    assert order == ["b", "a", "c"]
    assert ranks["b"] == {"x": 2, "y": 1}
    assert reciprocal_rank_fusion({"x": ["b"], "y": ["a"]})[0] == ["a", "b"]
    assert reciprocal_rank_fusion({}) == ([], {})


def _non_strict(schema):
    failures = []
    if isinstance(schema, dict):
        if schema.get("type") == "object" or "properties" in schema:
            properties = schema.get("properties", {})
            if schema.get("additionalProperties") is not False or set(schema.get("required", [])) != set(properties):
                failures.append(schema)
        for child in schema.values():
            failures.extend(_non_strict(child))
    elif isinstance(schema, list):
        for child in schema:
            failures.extend(_non_strict(child))
    return failures


@pytest.mark.parametrize("model", [FacetDossierDraft, PracticeRerank, RelevanceLabels, WrittenQueries])
def test_wire_contracts_are_strict(model):
    assert not _non_strict(strict_output_schema(model))
    with pytest.raises(Exception):
        model.model_validate({"unexpected": 1})


def test_agent_tool_declares_a_closed_schema():
    schema = FIND_PRACTICE_TOOL["input_schema"]
    assert FIND_PRACTICE_TOOL["name"] == "find_practice"
    assert schema["required"] == ["query"]
    assert schema["additionalProperties"] is False
    with pytest.raises(Exception):
        FindPracticeArguments.model_validate({"query": "x", "serve": True})
