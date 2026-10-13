"""S4 (§10.1): five typed tools; strict arguments; no policy field."""
from __future__ import annotations

import pytest

from learnloop.instructional.tools import TOOLS, ToolArgumentsInvalid, drop_unknown_ids, tool_schemas, validate_arguments
from tests.source_service_fakes import build_service_vault, loaded


def test_five_tools_publish_strict_schemas_without_a_policy():
    schemas = tool_schemas()
    assert [schema["name"] for schema in schemas] == [
        "find_practice", "find_sources", "compare_sources", "find_facets", "practice_availability"]
    for schema in schemas:
        assert schema["input_schema"]["additionalProperties"] is False
        assert "policy" not in schema["input_schema"]["properties"]
        assert "practice_item_id" not in schema["input_schema"]["properties"]
    assert {schema["name"]: schema["model_call"] for schema in schemas}["find_facets"] == "none"
    assert {schema["name"]: schema["model_call"] for schema in schemas}["practice_availability"] == "none"


@pytest.mark.parametrize("name", sorted(TOOLS))
def test_extra_fields_and_a_policy_are_refused(name):
    base = {"query": "determinant"} if name != "practice_availability" else {}
    for extra in ({"policy": "post_attempt"}, {"practice_item_id": "pi_x"}, {"anything": 1}):
        with pytest.raises(ToolArgumentsInvalid) as refused:
            validate_arguments(name, {**base, **extra})
        assert refused.value.code == "invalid_arguments"


def test_an_unknown_tool_is_refused():
    with pytest.raises(ToolArgumentsInvalid) as refused:
        validate_arguments("serve_item", {})
    assert refused.value.code == "unknown_tool"


def test_unknown_ids_are_dropped_and_reported(tmp_path):
    paths, repository = build_service_vault(tmp_path / "vault")
    args = validate_arguments("find_practice", {
        "query": "eigen", "facet_ids": ["facet_eigen", "facet_nope"], "learning_object_ids": ["lo_matrices", "lo_x"],
        "target_hypotheses": [{"kind": "misconception", "id": "mc_missing"}, {"kind": "named_gap", "id": "g1"},
                              {"kind": "lo", "id": "lo_matrices"}]})
    kept, dropped = drop_unknown_ids(loaded(paths), repository, args)
    assert kept.facet_ids == ["facet_eigen"] and kept.learning_object_ids == ["lo_matrices"]
    assert [ref.kind for ref in kept.target_hypotheses] == ["learning_object"]  # aliases canonical (F13)
    reasons = {(entry["field"], entry["why"]) for entry in dropped}
    assert ("facet_ids", "unknown facet") in reasons
    assert ("target_hypotheses", "unavailable: learner-text gaps not merged") in reasons
    assert ("target_hypotheses", "unknown misconception") in reasons
