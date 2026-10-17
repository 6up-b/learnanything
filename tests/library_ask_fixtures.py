"""Builders and fakes for reader workbench RW4a's tests (no network).

``build_library_vault`` is the canonical-sources textbook vault (two books and
an exam in one source set, three LOs) with a concept graph and provenance
links the expansion can read:

* ``lo_matrices`` (the question's LO) lists ``lo_vectors`` as a prerequisite
  and ``lo_svd_definition`` as a confusable;
* ``lo_inner`` lists ``lo_matrices`` as a prerequisite (an application);
* each LO is linked to its own passages (``entity_source_links``).

``OrganizerFake`` answers the library organizer from the prompt's own JSON
(plumbing checks, never evidence about quality); knobs name the misbehaviours
the tests need.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from learnloop.ai.execution import report_call_usage
from learnloop.ingest.locators import format_block_span
from learnloop.source_retrieval.library_ask import OrganizerNote, OrganizerResult
from learnloop.vault.yaml_io import read_yaml, write_yaml
from tests.pf_fakes import prompt_context
from tests.recap_fixtures import call, context  # noqa: F401 - re-exported for the RW4a tests
from tests.source_service_fakes import build_textbook_vault, loaded, set_config  # noqa: F401

#: The passages each LO is linked to: (extraction, span).
LINKS: dict[str, list[tuple[str, str]]] = {
    "lo_matrices": [("ext_text", "t2"), ("ext_book", "s2")],
    "lo_vectors": [("ext_book", "s10"), ("ext_book", "s11")],
    "lo_inner": [("ext_book", "s12")],
    "lo_svd_definition": [("ext_book", "s7")],
}
SOURCES = {"ext_text": ("src_text", "rev_text"), "ext_book": ("src_book", "rev_book")}


def _set_lo(paths: Any, lo_id: str, **values: Any) -> None:
    path = paths.learning_object_path("linear-algebra", lo_id)
    payload = read_yaml(path)
    payload.update(values)
    write_yaml(path, payload)


def build_library_vault(root: Path) -> tuple[Any, Any, dict[str, list[str]]]:
    paths, repository, spans = build_textbook_vault(root)
    _set_lo(paths, "lo_matrices", prerequisites=["lo_vectors"], confusables=["lo_svd_definition"])
    _set_lo(paths, "lo_inner", prerequisites=["lo_matrices"])
    for lo_id, keys in LINKS.items():
        for extraction_id, span_id in keys:
            source_id, revision_id = SOURCES[extraction_id]
            repository.insert_entity_source_link(
                entity_type="learning_object", entity_id=lo_id, locator=format_block_span(extraction_id, span_id),
                relation="primary", source_id=source_id, revision_id=revision_id, extraction_id=extraction_id)
    return paths, repository, spans


class OrganizerFake:
    """The library organizer, deterministic. ``wrong_cite``: refs whose line
    cites another passage; ``speak``: the open-question id to name on every
    passage (the code keeps at most one); ``unrelated``: refs judged unrelated;
    ``reverse``: pick in reverse order."""

    provider_name = "fake_organizer"
    provider_type = "codex_sdk"
    model = "fake-organizer-model"

    def __init__(self, *, wrong_cite: tuple[str, ...] = (), speak: str | None = None,
                 unrelated: tuple[str, ...] = (), reverse: bool = False, fail: bool = False) -> None:
        self.wrong_cite = set(wrong_cite)
        self.speak = speak
        self.unrelated = set(unrelated)
        self.reverse = reverse
        self.fail = fail
        self.prompts: list[str] = []
        self.contexts: list[dict[str, Any]] = []

    def supports(self, capability: str) -> bool:
        return capability in {"structured_completion", "bounded_structured_completion", "isolated_turn"}

    def complete(self, request):
        from learnloop.ai.errors import AIProviderUnavailable

        assert request.result_model is OrganizerResult
        self.prompts.append(request.prompt)
        report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 80,
                           "resolved_model": self.model})
        if self.fail:
            raise AIProviderUnavailable("fake failure")
        context = prompt_context(request.prompt)
        self.contexts.append(context)
        refs = [candidate["ref"] for candidate in context["candidates"]]
        judgments = []
        for index, ref in enumerate(refs):
            other = refs[(index + 1) % len(refs)] if len(refs) > 1 else "p999"
            judgments.append(OrganizerNote(
                ref=ref, verdict="unrelated" if ref in self.unrelated else "contributes",
                rationale=f"adds the passage {ref}'s own point",
                cites=[other] if ref in self.wrong_cite else [ref],
                roles=["definition", "not_a_role"], speaks_to=self.speak or ""))
        picks = [ref for ref in refs if ref not in self.unrelated]
        if self.reverse:
            picks = list(reversed(picks))
        return OrganizerResult(judgments=judgments, picks=picks)


def tutor_with_citations(citations: list[tuple[str, str]]):
    """A tutor fake whose answer cites ``citations`` (extraction, span) and records its prompts."""

    from tests.structured_ai import StructuredClientFake

    class CitingTutor(StructuredClientFake):
        provider_name = "fake_tutor"
        provider_type = "fake"
        model = "fake-tutor-model"

        def __init__(self) -> None:
            self.prompts: list[str] = []

        def complete(self, request):
            self.prompts.append(request.prompt)
            return super().complete(request)

        def run_tutor_qa(self, context):
            from learnloop.tutor.ai_contracts import TutorAnswer

            return TutorAnswer.model_validate({
                "answer_md": "From your passages: the determinant changes sign.", "question_type": "mechanism",
                "facets": [], "citations": [{"extraction_id": e, "span_id": s, "label": "x"} for e, s in citations],
            })

    return CitingTutor()


def table_counts(repository: Any, tables: list[str]) -> dict[str, int]:
    with repository.connection() as connection:
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        return {table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                for table in tables if table in names}


def ask_rows(repository: Any) -> list[dict[str, Any]]:
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute("SELECT * FROM library_asks ORDER BY created_at, id")]
