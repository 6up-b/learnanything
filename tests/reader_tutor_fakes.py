"""Fakes for reader workbench RW1c's tests (no network).

``LookupTutor`` is a structured tutor fake for the Reader tutor that looks
things up: it records every prompt and the context it was given, and answers
with a ``ReaderTutorAnswerWithTools`` whose excerpt, bridge, citations and
tool requests the test chooses (``excerpt`` may be a callable of the
context, so a test can quote exactly a passage it was given). ``Verifier``
is the sources service's intent-fit verification, the shared
``FakeServiceLLM`` with its prompts recorded; ``RejectAll`` keeps nothing.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Callable

from learnloop.ai.execution import report_call_usage
from tests.library_ask_fixtures import build_library_vault, call, context, set_config  # noqa: F401
from tests.source_service_fakes import FakeServiceLLM

ROOT_QUESTION = "why does the determinant change sign when two rows are swapped?"


def prompt_context(prompt: str) -> dict[str, Any]:
    return json.loads(prompt[prompt.index("{"):])["context"]


class LookupTutor:
    provider_name = "fake_tutor"
    provider_type = "fake"
    model = "fake-tutor-model"

    def __init__(self, *, answer_md: str = "Swapping rows flips the sign.",
                 excerpt: dict[str, Any] | Callable[[dict[str, Any]], dict[str, Any] | None] | None = None,
                 bridge_md: str | None = None, cite: Callable[[dict[str, Any]], list[tuple[str, str]]] | None = None,
                 tool_requests: list[dict[str, Any]] | None = None) -> None:
        self.answer_md = answer_md
        self.excerpt = excerpt
        self.bridge_md = bridge_md
        self.cite = cite
        self.tool_requests = list(tool_requests or [])
        self.prompts: list[str] = []
        self.contexts: list[dict[str, Any]] = []
        self.result_models: list[str] = []

    def supports(self, capability: str) -> bool:
        return capability in {"structured_completion", "bounded_structured_completion"}

    def complete(self, request):
        from learnloop.tutor import ai_contracts as C

        self.prompts.append(request.prompt)
        self.result_models.append(request.result_model.__name__)
        context = prompt_context(request.prompt)
        self.contexts.append(context)
        report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 50,
                           "resolved_model": self.model})
        excerpt = self.excerpt(context) if callable(self.excerpt) else self.excerpt
        cited = self.cite(context) if self.cite else [
            (span["extraction_id"], span["span_id"]) for span in context["source_spans"][:2]]
        payload: dict[str, Any] = {
            "answer_md": self.answer_md, "question_type": "mechanism", "facets": [],
            "citations": [{"extraction_id": e, "span_id": s, "label": "x"} for e, s in cited],
        }
        model = request.result_model
        if model in (C.ReaderTutorAnswer, C.ReaderTutorAnswerWithTools):
            payload.update({"excerpt": excerpt, "bridge_md": self.bridge_md})
        if model in (C.TutorAnswerWithTools, C.ReaderTutorAnswerWithTools):
            payload["tool_requests"] = list(self.tool_requests)
        return model.model_validate(payload)


class Verifier(FakeServiceLLM):
    """The intent-fit verification (and the comparison), prompts recorded."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.prompts: list[str] = []
        self.lock = threading.Lock()

    def complete(self, request):
        with self.lock:
            self.prompts.append(request.prompt)
        return super().complete(request)


class RejectAll(Verifier):
    """A verification that judges every candidate and keeps none."""

    def _IntentVerification(self, request, context):
        from learnloop.source_retrieval.find_sources import INTENT_VERDICTS, IntentJudgment, IntentVerification
        import re

        match = re.search(r"source_intent_fit\.v1\.(\w+)", request.prompt)
        worst = INTENT_VERDICTS[match.group(1) if match else "explain"][-1]
        return IntentVerification(judgments=[IntentJudgment(ref=c["ref"], verdict=worst, rationale="no")
                                             for c in context["candidates"]], picks=[])


class KeepContaining(Verifier):
    """A verification that keeps exactly the candidates containing one of ``phrases``."""

    def __init__(self, *phrases: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.phrases = [phrase.casefold() for phrase in phrases]

    def _IntentVerification(self, request, context):
        from learnloop.source_retrieval.find_sources import INTENT_VERDICTS, IntentJudgment, IntentVerification
        import re

        match = re.search(r"source_intent_fit\.v1\.(\w+)", request.prompt)
        verdicts = INTENT_VERDICTS[match.group(1) if match else "explain"]
        judged = [(c["ref"], verdicts[0] if any(p in c["passage"].casefold() for p in self.phrases) else verdicts[-1])
                  for c in context["candidates"]]
        return IntentVerification(
            judgments=[IntentJudgment(ref=ref, verdict=verdict, rationale="phrase") for ref, verdict in judged],
            picks=[ref for ref, verdict in judged if verdict == verdicts[0]][: context["pick_at_most"]])


#: The book's own sentence for the root question (ext_book s7).
SIGN_PASSAGE = "changes sign when two rows"


class Ready:
    ready = True


def reader_ctx(tmp_path: Path, monkeypatch, tutor: LookupTutor, *, verifier: Any | None = None,
               config: dict[str, dict[str, Any]] | None = None, name: str = "vault"):
    """The textbook library vault behind a sidecar context with the fakes injected."""

    import learnloop_sidecar.handlers.reader as reader_handler

    paths, repository, spans = build_library_vault(tmp_path / name)
    for section, values in (config or {}).items():
        set_config(paths, section, **values)
    ctx = context(paths.root)
    ctx.reader_tutor_rerank_client = verifier if verifier is not None else KeepContaining(SIGN_PASSAGE, "cofactor")
    monkeypatch.setattr(reader_handler, "ready_tutor_qa_provider", lambda vault: ("fake", Ready(), tutor))
    vault, repository = ctx.require_vault()
    return paths, ctx, repository, spans


def ask(ctx, question: str = ROOT_QUESTION, **extra: Any) -> dict[str, Any]:
    params = {"extractionId": "ext_text", "spanId": "t3", "question": question, "selectionSpanIds": ["t3"],
              "selectionQuote": "the determinant changes sign", **extra}
    return call(ctx, "reader.ask", params)


def spans_given(tutor: LookupTutor, index: int = -1) -> list[tuple[str, str, str]]:
    return [(s["extraction_id"], s["span_id"], s.get("relation")) for s in tutor.contexts[index]["source_spans"]]
