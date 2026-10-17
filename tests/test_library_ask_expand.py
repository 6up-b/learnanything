"""RW4a's caller-side concept-graph expansion (spec_reader_workbench_v1 §7.2).

For the question's LOs the Reader reads the graph as it is
(``find_sources.expanded_learning_objects``: prerequisites, the LOs that list
them as a prerequisite, confusables) and makes ONE more
``find_sources(intent="explain", learning_object_ids=<expanded LOs>,
verify=False)`` call per expansion it asks for. Only passages linked to those
LOs by provenance are kept from it, each with its label; a passage that is
merely similar never becomes a "Prerequisite" (similarity never creates an
edge). The organizer then judges the union once.
"""
from __future__ import annotations

import pytest

from learnloop.source_retrieval import library_ask as LA
from learnloop.source_retrieval.find_sources import expanded_learning_objects, expansion_lists, find_sources
from learnloop.vault.loader import load_vault
from tests.library_ask_fixtures import LINKS, OrganizerFake, build_library_vault, call, context, set_config

QUESTION = "eigenvalues characteristic polynomial determinant"


@pytest.fixture
def library(tmp_path):
    paths, repository, _spans = build_library_vault(tmp_path / "vault")
    return paths, repository


class SpyFind:
    """The sources service's find_sources, called for real and recorded."""

    def __init__(self, vault, repository):
        self.vault, self.repository = vault, repository
        self.calls: list[dict] = []

    def __call__(self, query, **kwargs):
        self.calls.append({"query": query, **kwargs})
        return find_sources(self.vault, self.repository, query, policy="reading", **kwargs)


def _ask(paths, repository, **extra):
    vault = load_vault(paths.root)
    spy = SpyFind(vault, repository)
    result = LA.ask_library(vault, repository, QUESTION, find=spy, caller={"kind": "reader"},
                            extraction_id="ext_text", anchor_span_ids=["t2"],
                            learning_object_ids=["lo_matrices"], **extra)
    return result, spy


def test_the_graph_is_read_as_it_is(library):
    paths, _repository = library
    vault = load_vault(paths.root)
    assert expanded_learning_objects(vault, ["lo_matrices"], "prerequisites") == ["lo_vectors"]
    assert expanded_learning_objects(vault, ["lo_matrices"], "applications") == ["lo_inner"]
    assert expanded_learning_objects(vault, ["lo_matrices"], "confusables") == ["lo_svd_definition"]
    with pytest.raises(ValueError):
        expanded_learning_objects(vault, ["lo_matrices"], "similar")


def test_the_sources_specs_expand_lists_read_the_same_graph(library):
    """The refactor kept expansion_lists' behaviour (one graph read for both)."""

    paths, repository = library
    vault = load_vault(paths.root)
    lists = expansion_lists(vault, repository, ["lo_matrices"], ["prerequisites", "applications"])
    assert set(lists) == {"expand_prerequisites", "expand_applications"}
    assert lists["expand_prerequisites"] and set(lists["expand_prerequisites"]) <= set(LINKS["lo_vectors"])
    assert set(lists["expand_applications"]) == set(LINKS["lo_inner"])


def test_one_extra_call_per_expansion_with_the_expanded_los_and_no_verification(library):
    paths, repository = library
    result, spy = _ask(paths, repository)
    main, *extra = spy.calls
    assert main["learning_object_ids"] == ["lo_matrices"] and main["verify"] is False
    assert [call["learning_object_ids"] for call in extra] == [["lo_vectors"], ["lo_inner"]]
    assert all(call["intent"] == "explain" and call["verify"] is False and call["scope"] == "library"
               for call in spy.calls)
    labels = {hit["key"]: hit["group"] for hit in result["hits"] if hit["expansion"]}
    assert labels and set(labels.values()) <= {"Prerequisite", "Application"}
    for hit in result["hits"]:
        if hit["expansion"] == "prerequisites":
            assert (hit["extraction_id"], hit["span_id"]) in LINKS["lo_vectors"] and hit["learning_object_ids"] == ["lo_vectors"]
        if hit["expansion"] == "applications":
            assert (hit["extraction_id"], hit["span_id"]) in LINKS["lo_inner"]
    subheads = [group["label"] for group in result["groups"]["expansions"]]
    assert subheads == [label for label in ("Prerequisite", "Application") if label in set(labels.values())]


def test_a_similar_passage_never_becomes_an_expansion(library, monkeypatch):
    """An expansion call's hits that are not linked to the expanded LOs (they
    match the question's words) are left out, whatever they rank."""

    paths, repository = library
    result, spy = _ask(paths, repository)
    expansion_hits = {hit["key"] for hit in result["hits"] if hit["expansion"]}
    linked = {f"{e}:{s}" for lo in ("lo_vectors", "lo_inner") for e, s in LINKS[lo]}
    assert expansion_hits <= linked
    # The expansion calls did return unlinked, similar passages: they were dropped.
    extra_keys = {f"{h['extraction_id']}:{h['span_id']}" for record in
                  [find_sources(load_vault(paths.root), repository, QUESTION, policy="reading",
                                learning_object_ids=["lo_vectors"], verify=False, limit=LA.EXPANSION_POOL)]
                  for h in record.hits}
    assert extra_keys - linked


def test_the_expansion_calls_are_on_the_manifest(library):
    paths, repository = library
    result, _spy = _ask(paths, repository)
    with repository.connection() as connection:
        import json

        manifest = json.loads(connection.execute(
            "SELECT manifest_json FROM library_asks WHERE id = ?", (result["ask_id"],)).fetchone()[0])
    records = manifest["expansions"]
    assert [r["expansion"] for r in records] == ["prerequisites", "applications"]
    assert records[0]["learning_object_ids"] == ["lo_vectors"] and records[0]["manifest"]["policy"] == "reading"
    assert records[0]["manifest"]["verification"]["status"] == "not_requested"


def test_the_organizer_judges_the_union_once(library):
    paths, repository = library
    result, _spy = _ask(paths, repository)
    fake = OrganizerFake()
    notes = LA.organize(load_vault(paths.root), repository, result["ask_id"], client=fake)
    assert len(fake.prompts) == 1
    judged = len(fake.contexts[0]["candidates"])
    assert judged == len(result["hits"]) and any(hit["expansion"] for hit in result["hits"])
    assert {note["key"] for note in notes["notes"]} == {hit["key"] for hit in result["hits"]}


def test_what_do_i_need_first_lists_the_prerequisites_with_their_status(library):
    paths, repository = library
    result, spy = _ask(paths, repository, entry="what_do_i_need_first")
    assert len(spy.calls) == 2  # the main call and the prerequisites expansion only
    (prerequisites,) = result["expansions"]
    assert prerequisites["expansion"] == "prerequisites"
    (lo,) = prerequisites["learning_objects"]
    assert lo["learning_object_id"] == "lo_vectors" and lo["title"] == "Vector lists"
    assert lo["demonstrated"] is False  # nothing shown on their own yet
    assert lo["keys"] and set(lo["keys"]) <= {f"{e}:{s}" for e, s in LINKS["lo_vectors"]}


def test_where_is_this_used_is_the_applications_expansion(library):
    paths, repository = library
    result, spy = _ask(paths, repository, entry="where_is_this_used")
    assert [call["learning_object_ids"] for call in spy.calls[1:]] == [["lo_inner"]]
    assert [e["expansion"] for e in result["expansions"]] == ["applications"]


def test_where_else_explained_leaves_out_the_passage_in_view(library):
    paths, repository = library
    result, spy = _ask(paths, repository, entry="where_else_explained")
    assert spy.calls[0]["exclude_span_keys"] == ["ext_text:t2"]
    assert "ext_text:t2" not in {hit["key"] for hit in result["hits"]}


def test_expand_graph_off_makes_no_extra_call(library):
    paths, repository = library
    set_config(paths, "library_ask", expand_graph=False)
    result, spy = _ask(paths, repository)
    assert len(spy.calls) == 1 and result["expansions"] == [] and result["expand_graph"] is False
    assert not any(hit["expansion"] for hit in result["hits"])


def test_no_anchor_los_means_no_expansion(library):
    paths, repository = library
    vault = load_vault(paths.root)
    spy = SpyFind(vault, repository)
    result = LA.ask_library(vault, repository, QUESTION, find=spy, caller={"kind": "reader"}, entry="library_search")
    assert len(spy.calls) == 1 and result["expansions"] == []


def test_the_rpc_reads_the_anchor_passages_los(library, monkeypatch):
    paths, _repository = library
    ctx = context(paths.root)
    monkeypatch.setattr(LA, "learning_objects_for_span", lambda *a, **k: ["lo_matrices"])
    result = call(ctx, "reader.library_ask", {"query": QUESTION, "extractionId": "ext_text", "spanIds": ["t2"]})
    assert any(hit["expansion"] for hit in result["hits"])
