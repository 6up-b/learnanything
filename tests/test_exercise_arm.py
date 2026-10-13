"""S1 (G4): the source-exercise arm proposes textbook exercises, never served, never held out."""
from __future__ import annotations

import json

from learnloop.instructional.exercises import exercise_candidates, exercise_label, imported_span_keys
from learnloop.practice_index.retrieval import PracticeConstraints, find_practice
from learnloop.source_retrieval.corpus import library_scope
from learnloop.source_retrieval.search import search_spans
from learnloop.vault.writer import upsert_practice_item
from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, loaded, table_counts

QUERY = "solve for the eigenvalue x"


def test_the_positive_role_filter_keeps_only_effective_exercise_blocks(tmp_path):
    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    vault = loaded(paths)
    search = search_spans(vault, repository, "eigenvalue determinant", library_scope(repository),
                          deep=False, roles=("exercise",))
    keys = {hit.key for hit in search.hits}
    assert keys and keys <= {("ext_text", span) for span in spans["exercises"]}
    # The "Exercises" heading itself is not an exercise region lead.
    assert ("ext_text", spans["exercises"][0]) not in {
        (candidate["extraction_id"], candidate["span_ids"][0])
        for candidate in exercise_candidates(vault, repository, "eigenvalue", PracticeConstraints(),
                                             pool_size=10).candidates}
    assert search.list_ends["keyword"] is True and search.fused_keys


def test_the_arm_returns_regions_in_the_teaching_scope_only(tmp_path):
    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    vault = loaded(paths)
    pool = exercise_candidates(vault, repository, QUERY, PracticeConstraints(learning_object_ids=("lo_matrices",)),
                               pool_size=10)
    assert pool.candidates
    for candidate in pool.candidates:
        assert candidate["extraction_id"] == "ext_text"  # never the exam
        assert set(candidate["span_ids"]) <= set(spans["exercises"])
        assert candidate["kind"] == "source_exercise" and candidate["statement"]
        assert candidate["source_title"] == "Matrix Theory" and candidate["page"] == 9
        assert candidate["label"].startswith("Exercise")
    assert all("Exam" not in candidate["statement"] for candidate in pool.candidates)


def test_an_already_imported_exercise_is_dropped(tmp_path):
    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    vault = loaded(paths)
    first = exercise_candidates(vault, repository, QUERY, PracticeConstraints(), pool_size=10).candidates
    taken = first[0]
    upsert_practice_item(paths.root, {
        "id": "pi_imported", "learning_object_id": "lo_matrices", "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt"], "prompt": taken["statement"], "expected_answer": "5",
        "evidence_facets": ["facet_eigen"], "evidence_weights": {"facet_eigen": 1.0},
        "provenance": {"origin": "canonical_extract", "source_refs": []},
        "canonical_exercise": {"source_id": "src_text", "extraction_id": "ext_text",
                               "span_ids": taken["span_ids"], "relation": "verbatim"},
        "created_at": "2026-10-12T00:00:00Z", "updated_at": "2026-10-12T00:00:00Z",
    })
    vault = loaded(paths)
    assert ("ext_text", taken["span_ids"][0]) in imported_span_keys(vault, repository)
    second = exercise_candidates(vault, repository, QUERY, PracticeConstraints(), pool_size=10)
    assert taken["key"] not in {candidate["key"] for candidate in second.candidates}
    assert second.dropped.get("already_imported") == 1


def test_find_practice_judges_items_and_exercises_in_one_pool(tmp_path):
    paths, repository, _spans = build_textbook_vault(tmp_path / "vault")
    vault = loaded(paths)
    before = table_counts(repository, ["practice_attempts"])
    llm = FakeServiceLLM()
    result = find_practice(vault, repository, QUERY, {"learning_object_ids": ["lo_matrices"]},
                           exercise_arm=exercise_candidates, rerank_client=llm, caller={"kind": "tutor", "ref": "q"})
    assert result["kinds"] == "both"
    assert [name for _purpose, name in llm.calls] == ["MixedPracticeRerank"]
    exercises = result["source_exercises"]
    assert exercises and all(entry["kind"] == "source_exercise" for entry in exercises)
    entry = exercises[0]
    assert entry["label_line"].startswith("From Matrix Theory, p. 9")
    assert "facet_eigen" in entry["provisional"]["facets"]
    assert entry["provisional"]["basis"].startswith("matched on the exercise's text")
    with repository.connection() as connection:
        row = connection.execute("SELECT proposed_json, manifest_json FROM practice_index_proposals").fetchone()
    proposed = json.loads(row["proposed_json"])
    assert any(item.get("kind") == "source_exercise" for item in proposed)
    assert json.loads(row["manifest_json"])["rerank_prompt_version"] == "practice_rerank.v2"
    # Proposing never serves.
    assert table_counts(repository, ["practice_attempts"]) == before


def test_unjudged_exercises_are_never_proposed(tmp_path):
    paths, repository, _spans = build_textbook_vault(tmp_path / "vault")
    vault = loaded(paths)
    result = find_practice(vault, repository, QUERY, {"rerank": False}, exercise_arm=exercise_candidates)
    assert result["source_exercises"] == []
    assert "not proposed" in result["source_exercises_status"]


def test_kinds_items_skips_the_arm_and_source_exercises_skips_items(tmp_path):
    paths, repository, _spans = build_textbook_vault(tmp_path / "vault")
    vault = loaded(paths)
    llm = FakeServiceLLM()
    items_only = find_practice(vault, repository, QUERY, {"kinds": "items"}, exercise_arm=exercise_candidates,
                               rerank_client=llm)
    assert "source_exercises" not in items_only and llm.calls[-1][1] == "PracticeRerank"
    exercises_only = find_practice(vault, repository, QUERY, {"kinds": "source_exercises"},
                                   exercise_arm=exercise_candidates, rerank_client=llm)
    assert exercises_only["items"] == [] and exercises_only["source_exercises"]


def test_exercise_labels():
    assert exercise_label("Exercise 4.12 Show that ...", 3) == "Exercise 4.12"
    assert exercise_label("Problem 7 Compute", None) == "Problem 7"
    assert exercise_label("3. Explain why", 9) == "Exercise 3, p. 9"
    assert exercise_label("Show that A is invertible.", 11) == "Exercise on p. 11"
