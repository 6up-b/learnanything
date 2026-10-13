"""S1 (§7.4): ``canonical_exercise`` round-trips, stays out of the hashes, and PF variants point at it."""
from __future__ import annotations

import json

import pytest

from learnloop.ops.pf_publish import build_item_payload
from learnloop.vault.hashes import practice_item_hash, reference_content_hash
from learnloop.vault.models import CanonicalExercise, PracticeItem
from learnloop.vault.writer import upsert_practice_item
from tests.source_service_fakes import build_textbook_vault, loaded

CANONICAL = {"source_id": "src_text", "revision_id": "rev_text", "extraction_id": "ext_text",
             "span_ids": ["t7"], "label": "Exercise 1", "relation": "verbatim"}


def _payload(item_id: str, **extra):
    return {"id": item_id, "learning_object_id": "lo_matrices", "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"], "prompt": "Solve 3x + 5 = 20 for x.",
            "expected_answer": "5", "evidence_facets": ["facet_eigen"], "evidence_weights": {"facet_eigen": 1.0},
            "provenance": {"origin": "canonical_extract", "source_refs": []},
            "created_at": "2026-10-12T00:00:00Z", "updated_at": "2026-10-12T00:00:00Z", **extra}


def test_round_trip_and_hash_independence(tmp_path):
    paths, _repository, _spans = build_textbook_vault(tmp_path / "vault")
    upsert_practice_item(paths.root, _payload("pi_with", canonical_exercise=CANONICAL))
    upsert_practice_item(paths.root, _payload("pi_without"))
    vault = loaded(paths)
    with_item, without = vault.practice_items["pi_with"], vault.practice_items["pi_without"]
    assert with_item.canonical_exercise == CanonicalExercise(**CANONICAL)
    assert "canonical_exercise" not in without.model_dump(mode="json")
    stripped = with_item.model_copy(update={"canonical_exercise": None})
    assert practice_item_hash(with_item) == practice_item_hash(stripped)
    assert reference_content_hash(with_item) == reference_content_hash(stripped)
    # A hints-only change keeps the reference hash; a key change moves it.
    assert reference_content_hash(with_item.model_copy(update={"hints": ["h"]})) == reference_content_hash(with_item)
    assert reference_content_hash(with_item.model_copy(update={"expected_answer": "6"})) != reference_content_hash(with_item)


def test_an_empty_span_list_is_refused():
    with pytest.raises(ValueError):
        CanonicalExercise(source_id="s", extraction_id="e", span_ids=[])


def test_a_pf_variant_of_a_textbook_exercise_points_at_it(tmp_path):
    paths, _repository, _spans = build_textbook_vault(tmp_path / "vault")
    upsert_practice_item(paths.root, _payload("pi_parent", canonical_exercise=CANONICAL))
    vault = loaded(paths)
    parent = vault.practice_items["pi_parent"]
    row = {"payload_json": json.dumps({"stem": "Solve 4x + 5 = 21 for x.", "final_answer": "4",
                                       "solution": "Subtract, divide."}),
           "final_relation": "isomorph", "declared_relation": "isomorph", "family_id": "fam_x", "difficulty": 0.5,
           "generation_path": "ensemble", "id": "pfc_1"}
    payload = build_item_payload(vault, parent, row, item_id="pi_pf_1", now_iso="2026-10-12T00:00:00Z")
    assert payload["canonical_exercise"] == {**CANONICAL, "relation": "variant_of"}
    plain = build_item_payload(vault, vault.practice_items["pi_eigen_1"], row, item_id="pi_pf_2",
                               now_iso="2026-10-12T00:00:00Z")
    assert "canonical_exercise" not in plain
    PracticeItem.model_validate(payload)


def test_the_practice_item_detail_names_the_book_and_the_key_label(tmp_path):
    from learnloop.vault.yaml_io import read_yaml, write_yaml
    from tests.source_service_fakes import build_textbook_vault, call

    paths, _repository, spans = build_textbook_vault(tmp_path / "vault")
    path = paths.practice_item_path("linear-algebra", "pi_eigen_1")
    payload = read_yaml(path)
    payload["canonical_exercise"] = {"source_id": "src_text", "revision_id": "rev_text", "extraction_id": "ext_text",
                                     "span_ids": [spans["exercises"][1]], "label": "Exercise 1, p. 9",
                                     "relation": "verbatim"}
    write_yaml(path, payload)
    detail = call(paths.root, "get_practice_item", {"practiceItemId": "pi_eigen_1"})["result"]
    canonical = detail["canonicalExercise"]
    assert canonical["sourceTitle"] == "Matrix Theory" and canonical["label"] == "Exercise 1, p. 9"
    assert canonical["keyStatus"] and canonical["keyLabel"]
    plain = call(paths.root, "get_practice_item", {"practiceItemId": "pi_eigen_2"})["result"]
    assert "canonicalExercise" not in plain
