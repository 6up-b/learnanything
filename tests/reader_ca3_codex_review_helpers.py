"""What other test files use from ``tests/test_reader_ca3_codex_review.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from tests.source_service_fakes import FakeServiceLLM, seed_textbook


QUESTION = "why does the determinant change sign when two rows are swapped"


class LastWordsLLM(FakeServiceLLM):
    """The service fake, except that every comparison line quotes the last
    words of its passage (so an anchor's quote comes from its last block)."""

    def _SourceComparison(self, request, context):
        from learnloop.source_retrieval.compare import Contribution, PairRelation, SourceComparison

        sources = context["sources"]

        def quote(text: str, words: int = 6) -> str:
            return " ".join(text.split()[-words:])

        contributions = [Contribution(source_ref=src["ref"], contribution=f"{src['source']} states it its way",
                                      perspective="its own view", quote=quote(src["passage"])) for src in sources]
        relations = [PairRelation(left_ref=left["ref"], right_ref=right["ref"], relation="different_notation",
                                  statement="same idea, different notation", left_quote=quote(left["passage"], 5),
                                  right_quote=quote(right["passage"], 5))
                     for left, right in zip(sources, sources[1:], strict=False)]
        return SourceComparison(contributions=contributions, relations=relations, missing_perspectives=[])


def _third(repository) -> str:
    spans = seed_textbook(repository, source_id="src_third", revision_id="rev_third", extraction_id="ext_third",
                          title="Third Book", units={"c1": ("Determinants", [
                              ("Swapping two rows of a matrix changes the sign of its determinant, by the "
                               "alternating property of determinants.", 1)])})
    return f"ext_third:{spans['c1'][1]}"
