"""P4 (siblings): the tutor's find_sources and compare_sources tools drop what a model may not read
(solutions, assessment-lane passages) before the retrieval's verification and comparison models read it."""

from __future__ import annotations

from learnloop.instructional import tools as T
from learnloop.source_retrieval import compare as CMP
from learnloop.source_retrieval import find_sources as FS
from learnloop.source_retrieval.policy import CallerContext
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_source_set
from tests.source_retrieval_fakes import build_retrieval_vault, seed_source

PROBLEM = "Find the eigenvalues of the matrix A with a repeated eigenvalue."


def _world(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault", embeddings=False)
    seed_source(repository, source_id="src_ps", revision_id="rev_ps", extraction_id="ext_ps", title="Problem set",
                units={"ps_q": ("Problems", [(PROBLEM, 1)])}, furniture=False)
    upsert_source_set(paths.root, {"id": "sset_ps", "subject_id": "linear-algebra", "title": "Problems",
                                   "members": [{"source_id": "src_ps", "revision_id": "rev_ps",
                                                "default_role": "problem_set"}]})
    return load_vault(paths.root), repository


def test_the_find_sources_tool_never_sends_an_assessment_lane_passage_to_verification(tmp_path, monkeypatch):
    vault, repository = _world(tmp_path)
    judged: list[tuple[str, str]] = []

    def record(_vault, _repository, *, pool, **_kwargs):
        judged.extend(hit.key for hit in pool)
        return "verified", {}, [], None

    monkeypatch.setattr(FS, "_verify", record)
    result = T.execute_tool(vault, repository, "find_sources",
                            T.FindSourcesArgs(query="eigenvalues of the matrix"), caller=CallerContext(kind="reader"))
    assert any(key[0] == "ext_book" for key in judged), "the verification was not reached: the fixture proves nothing"
    assert not [key for key in judged if key[0] == "ext_ps"]
    assert result["result"]["passages"] == []
    assert result["result"]["withheld_from_model"]["assessment_lane"] >= 1


def test_the_compare_sources_tool_never_sends_an_assessment_lane_passage_to_verification(tmp_path, monkeypatch):
    vault, repository = _world(tmp_path)
    judged: list[tuple[str, str]] = []

    def record(_vault, _repository, *, pool, **_kwargs):
        judged.extend(hit.key for hit in pool)
        return "verified", {}, [], None

    monkeypatch.setattr(CMP, "_verify", record)
    try:
        T.execute_tool(vault, repository, "compare_sources", T.CompareSourcesArgs(query="eigenvalues of the matrix"),
                       caller=CallerContext(kind="reader"))
    except Exception:  # noqa: BLE001 - only what the verification was shown matters here
        pass
    assert any(key[0] == "ext_book" for key in judged), "the verification was not reached: the fixture proves nothing"
    assert not [key for key in judged if key[0] == "ext_ps"]
