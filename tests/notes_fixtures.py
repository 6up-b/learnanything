"""Builders and fakes for curriculum C2/C2b's tests (notes linked; no network).

C2b: "your notes" are the vault's own, so every note here is SYNTHETIC vault data written
through the Reader's own annotation API (``reader.annotations.append_annotation``) or the
capture inbox's (``capture.inbox.create_capture``); nothing outside the test's tmp vault
is read.

* :func:`add_annotation` writes a learner's Reader note beside a span (``ext_book`` by
  default, the deliverable fixtures' textbook);
* :func:`add_capture` writes a capture-inbox item;
* :func:`eigen_notes` writes the standard corpus: two notes that discuss eigenvalues (a
  Reader note carrying :data:`SENTINEL`, and a capture), one that only mentions the word,
  one beside the exam (protected: never a note), a bare highlight and a deleted note.

``NoteLinkFake`` answers the note link judge from the prompt's context: a note whose text
contains one of ``discusses`` words discusses it (``how`` and ``about`` as configured);
every other note is unrelated. ``NoteEmbeddingFake`` is a bag-of-words embedding client
(similar words, near vectors) at the width :func:`embeddings_config` sets.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Sequence

from learnloop.ai.execution import model_call, report_call_usage
from learnloop.ai.isolation import TOOL_FREE
from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, STRUCTURED_COMPLETION
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from tests.structured_ai import StructuredClientFake

SENTINEL = "SENTINEL-NOTE-TEXT-7f3a"
#: ext_book's eigenvalue chapter spans (tests.source_retrieval_fakes numbering).
EIGEN_SPAN = "s2"
EIGEN_SPAN_2 = "s3"
#: The exam's question span (protected material).
EXAM_SPAN = "s2"
EMBEDDING_DIMS = 16
EMBEDDING_MODEL = "qwen/qwen3-embedding-8b"


def add_annotation(repository: Repository, text: str, *, extraction_id: str = "ext_book", span_id: str = EIGEN_SPAN,
                   source_id: str = "src_book", revision_id: str = "rev_book", annotation_type: str = "question",
                   thinking: str | None = None) -> str:
    """A learner's Reader note (or highlight with words) beside ``span_id``; its id."""

    from learnloop.reader import annotations as ANN

    with repository.connection() as connection:
        block = connection.execute("SELECT text FROM source_document_blocks WHERE extraction_id = ? AND span_id = ?",
                                   (extraction_id, span_id)).fetchone()
    quote = " ".join(str(block[0]).split()[:4]) if block else ""
    translation = ANN.translate_selection(repository, extraction_id=extraction_id,
                                          raw_selection={"nodes": [{"span_id": span_id, "quote": quote}]})
    assert translation["status"] == "exact", translation
    return ANN.append_annotation(repository, source_id=source_id, revision_id=revision_id,
                                 extraction_id=extraction_id, annotation_type=annotation_type, learner_text=text,
                                 what_i_think_is_going_on=thinking, translation=translation)["annotation_id"]


def edit_annotation(repository: Repository, annotation_id: str, text: str) -> None:
    from learnloop.reader import annotations as ANN

    ANN.edit_annotation(repository, annotation_id=annotation_id, learner_text=text)


def delete_annotation(repository: Repository, annotation_id: str) -> None:
    from learnloop.reader import annotations as ANN

    ANN.delete_intent_annotation(repository, annotation_id=annotation_id)


def add_capture(repository: Repository, text: str, *, note: str | None = None, kind: str = "text",
                url: str | None = None, captured_at: str = "2026-10-03T09:00:00+00:00") -> str:
    """A capture-inbox item; its id."""

    from learnloop.capture.inbox import create_capture

    created = create_capture(repository, client_capture_id=new_ulid(), kind=kind,
                             text=text if kind == "text" else None, url=url, note=note, captured_at=captured_at)
    return str(created["capture_id"])


def dismiss_capture(repository: Repository, capture_id: str) -> None:
    from learnloop.capture.inbox import dismiss_capture as dismiss

    dismiss(repository, capture_id)


def eigen_notes(repository: Repository) -> dict[str, str]:
    """The standard synthetic notes, by name: their note keys (``annotation:<id>`` /
    ``capture:<id>``)."""

    typed = add_annotation(repository, f"Eigenvalues: Av = lv, so det(A - lI) = 0. {SENTINEL}")
    captured = add_capture(repository, "Worked the 2x2 eigen example by hand; eigenvalues 1 and 3.")
    unrelated = add_capture(repository, "Shopping list: eggs, milk. No eigenvalues today.")
    exam = add_annotation(repository, "Eigenvalues on the midterm: copy this one.", extraction_id="ext_exam",
                          span_id=EXAM_SPAN, source_id="src_exam", revision_id="rev_exam")
    bare = add_annotation(repository, "", annotation_type="highlight", span_id=EIGEN_SPAN_2)
    deleted = add_annotation(repository, "Eigenvalues, deleted thought.", span_id=EIGEN_SPAN_2)
    delete_annotation(repository, deleted)
    return {"typed": f"annotation:{typed}", "captured": f"capture:{captured}", "unrelated": f"capture:{unrelated}",
            "exam": f"annotation:{exam}", "bare": f"annotation:{bare}", "deleted": f"annotation:{deleted}"}


def turn_on_embeddings(paths: Any, *, backfill: bool = True) -> None:
    """Switch the vault's embeddings on (its template's ``[embedding]`` table) at the fake's
    width; no route is ever reached: tests inject :class:`NoteEmbeddingFake`."""

    import re

    config_path = paths.root / "learnloop.toml"
    text = config_path.read_text(encoding="utf-8")
    head, _, tail = text.partition("[embedding]\n")
    assert tail, "the vault config has an [embedding] table"
    body, sep, rest = tail.partition("\n[")
    body = re.sub(r"(?m)^enabled = \w+$", "enabled = true", body, count=1)
    body = re.sub(r"(?m)^backfill_enabled = \w+$", f"backfill_enabled = {'true' if backfill else 'false'}", body)
    body = re.sub(r"(?m)^dimensions = \d+$", f"dimensions = {EMBEDDING_DIMS}", body)
    config_path.write_text(head + "[embedding]\n" + body + sep + rest, encoding="utf-8")


class NoteEmbeddingFake:
    """Bag-of-words hashed into a few dimensions: similar words, near vectors."""

    provider_name = "openrouter_embedding"
    provider_type = "openai_embedding"

    def __init__(self, dims: int = EMBEDDING_DIMS, *, synonyms: dict[str, str] | None = None) -> None:
        self.model_id = EMBEDDING_MODEL
        self.model = self.model_id
        self.dims = dims
        self.modalities = frozenset({"text"})
        self.max_input_tokens = 32_768
        #: Words embedded as another (a "meaning" the exact words would miss).
        self.synonyms = dict(synonyms or {})
        self.inputs: list[str] = []

    def embed(self, inputs, task_prefix):
        with model_call(self, purpose="embedding", prompt=None):
            report_call_usage({"input_tokens": sum(len(str(text)) // 4 for text in inputs)})
        vectors = []
        for text in inputs:
            self.inputs.append(str(text))
            vector = [0.0] * self.dims
            for word in str(text).lower().replace(",", " ").replace(".", " ").replace(":", " ").split():
                word = self.synonyms.get(word, word)
                digest = int(hashlib.sha256(word.encode()).hexdigest(), 16)
                vector[digest % self.dims] += 1.0
            vector[0] += 0.001
            vectors.append(vector)
        return vectors


def prompt_context(prompt: str) -> dict[str, Any]:
    start = prompt.index("{", prompt.index("prompt_version"))
    return json.loads(prompt[start:])["context"]


class NoteLinkFake(StructuredClientFake):
    provider_name = "fake_plan_notes"
    provider_type = "chatgpt_plan"
    model = "fake-note-link-model"

    def __init__(self, *, discusses: Sequence[str] = ("Av = lv", "eigen example"), how: str = "restates",
                 about: str = "passage", fail: Exception | None = None,
                 shape: Callable[[list[dict[str, Any]]], list[dict[str, Any]]] | None = None,
                 on_call: Callable[[], None] | None = None) -> None:
        self.discusses = tuple(discusses)
        self.how = how
        self.about = about
        self.fail = fail
        #: Rewrites the verdicts before they are returned (an incomplete answer, F12).
        self.shape = shape
        #: Runs when a request arrives (the learner acting meanwhile, F2).
        self.on_call = on_call
        self.prompts: list[str] = []
        self.contexts: list[dict[str, Any]] = []

    def supports(self, capability: str) -> bool:
        return capability in {STRUCTURED_COMPLETION, BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, TOOL_FREE}

    def complete(self, request: Any) -> Any:
        context = prompt_context(request.prompt)
        self.prompts.append(request.prompt)
        self.contexts.append(context)
        report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 60,
                           "resolved_model": self.model})
        if self.on_call is not None:
            self.on_call()
        if self.fail is not None:
            raise self.fail
        verdicts = []
        for note in context["notes"]:
            if any(word in note["text"] for word in self.discusses):
                verdicts.append({"note": note["id"], "verdict": "discusses", "about": self.about, "how": self.how,
                                 "line": f"your note {self.how} it"})
            else:
                verdicts.append({"note": note["id"], "verdict": "unrelated"})
        if self.shape is not None:
            verdicts = self.shape(verdicts)
        return request.result_model.model_validate({"notes": verdicts})

    @property
    def calls(self) -> int:
        return len(self.contexts)


class MeteredNoteLinkFake(NoteLinkFake):
    """The same answers on a metered (OpenRouter-like) route."""

    provider_name = "fake_metered_notes"
    provider_type = "openrouter"


__all__ = ["EIGEN_SPAN", "MeteredNoteLinkFake", "NoteEmbeddingFake", "NoteLinkFake", "SENTINEL", "add_annotation",
           "add_capture", "delete_annotation", "dismiss_capture", "edit_annotation", "eigen_notes",
           "prompt_context", "turn_on_embeddings"]
