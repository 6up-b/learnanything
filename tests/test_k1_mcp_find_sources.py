"""K1-4: MCP ``find_sources`` drops a diagnostic probe's own passage and assessment-lane passages."""

from __future__ import annotations

from types import SimpleNamespace

from learnloop.learner_protection import WITHHELD_PROBE, Withheld
from learnloop.remote import sources as RS
from learnloop.source_retrieval.corpus import Exclusions
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_source_set
from tests.source_retrieval_fakes import build_retrieval_vault, seed_source


def _hit(extraction_id: str, span_id: str, text: str) -> dict:
    return {"extraction_id": extraction_id, "span_id": span_id, "text": text, "role": "explanation",
            "block_type": "paragraph", "source_id": "src_x", "revision_id": "rev_x", "section_path": []}


def _spans(repository, extraction_id: str) -> list[str]:
    with repository.connection() as connection:
        return [str(row[0]) for row in connection.execute(
            "SELECT span_id FROM source_document_blocks WHERE extraction_id = ? ORDER BY ordinal", (extraction_id,))]


def _shown(paths, repository, hits, withheld) -> dict:
    wrapped = SimpleNamespace(hits=hits, manifest={}, status="ok", policy="reading")
    return RS._shown(load_vault(paths.root), repository, wrapped, withheld, intent="explain", budget=10_000,
                     los=[], unknown_los=[]).payload


def test_a_diagnostic_probe_items_own_passage_is_not_returned(tmp_path, monkeypatch):
    paths, repository = build_retrieval_vault(tmp_path / "vault", embeddings=False)
    own, other = _spans(repository, "ext_book")[:2]
    monkeypatch.setattr("learnloop.source_retrieval.corpus.item_exclusions",
                        lambda _repository, _item: Exclusions(frozenset(), frozenset({("ext_book", own)})))
    withheld = Withheld(reasons={"probe_item": WITHHELD_PROBE}, known_items=frozenset({"probe_item"}))
    payload = _shown(paths, repository, [_hit("ext_book", own, "the probe's own exercise"),
                                         _hit("ext_book", other, "an ordinary passage")], withheld)
    assert [(p["citation"]["extraction_id"], p["citation"]["span_id"]) for p in payload["passages"]] == [("ext_book", other)]
    assert payload["withheld"]["held_for_a_check"] == 1


def test_a_problem_set_passage_is_not_returned_to_the_chat_host(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault", embeddings=False)
    seed_source(repository, source_id="src_ps", revision_id="rev_ps", extraction_id="ext_ps", title="Problem set",
                units={"ps_q": ("Problems", [("Find the eigenvalues of the matrix A.", 1)])}, furniture=False)
    upsert_source_set(paths.root, {"id": "sset_ps", "subject_id": "linear-algebra", "title": "Problems",
                                   "members": [{"source_id": "src_ps", "revision_id": "rev_ps",
                                                "default_role": "problem_set"}]})
    book = _spans(repository, "ext_book")[0]
    problem = _spans(repository, "ext_ps")[0]
    payload = _shown(paths, repository, [_hit("ext_ps", problem, "Find the eigenvalues of the matrix A."),
                                         _hit("ext_book", book, "an ordinary passage")], Withheld())
    assert [(p["citation"]["extraction_id"], p["citation"]["span_id"]) for p in payload["passages"]] == [("ext_book", book)]
    assert payload["withheld"]["exam_material"] == 1
