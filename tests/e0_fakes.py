"""Seeded vaults and deterministic fakes for the E0 harness tests (no network).

``build_e0_vault`` makes a vault under ``<tmp>/fixtures-local/...`` with a
small textbook (numbered environments, a cross-section reference, a bare
equation, an oversized block, an exercise and its solution), a transcript of
short captions and an exam in the source set. ``FakeEmbeddingTransport``
answers every hosted endpoint with hash vectors in a SHUFFLED order (rows
keyed by ``index``), counts requests and can fail on demand.
``FakeQwenClient`` stands in for the production OpenRouter client.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
import hashlib
import json
from pathlib import Path
import random
from typing import Any

import numpy as np
import pytest

from learnloop.db.repositories import Repository
from learnloop.experiments.contextual_embeddings.adapters import HttpResponse
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_source_set
from tests.helpers import append_config_toml, create_basic_vault
from tests.test_source_inventory import _persist

LONG_BLOCK = ("The span of a list of vectors is the set of all linear combinations of that list, and it is the "
              "smallest subspace containing every vector of the list. ") * 30
BOOK = [
    ("Chapter 1 Vector spaces", [
        ("Text", "Definition 1.1 (Vector space). A vector space is a set V with an addition and a scalar "
                 "multiplication satisfying the usual axioms of commutativity and associativity.", None),
        ("Text", "Theorem 1.2 (Unique additive identity). A vector space has a unique additive identity.", None),
        ("Text", "Proof. Suppose 0 and 0' are both additive identities of V; then the following holds by "
                 "Definition 1.1:", None),
        ("Equation", "$$0 = 0 + 0' = 0'$$", None),
        ("Text", LONG_BLOCK, None),
    ]),
    ("Chapter 2 Linear maps", [
        ("Text", "By Theorem 1.2, a linear map T sends the additive identity of V to the unique additive "
                 "identity of W, because T(0) = T(0 + 0) = T(0) + T(0).", None),
        ("Text", "Exercise 2.1. Show that every linear map sends the zero vector to the zero vector.", None),
        ("Text", "Solution: apply linearity to 0 = 0 + 0 and cancel T(0) on both sides.", "solution"),
        ("Text", "Example 2.2. Differentiation is a linear map on the space of real polynomials of degree "
                 "at most n.", "worked_example"),
    ]),
]
CAPTIONS = [f"caption {index}: the lecturer explains why a basis spans the space and is independent, "
            f"with example number {index}." for index in range(1, 13)]
EXAM = "Exam question 1: prove that the additive inverse in a vector space is unique."


def _seed(repository: Repository, *, source_id: str, extraction_id: str, title: str,
          sections: list[tuple[str, list[tuple[str, str, str | None]]]], extractor: str = "marker") -> None:
    revision_id = f"rev_{source_id}"
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, display_title, current_revision_id, "
            "reader_enabled, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            (source_id, "pdf", f"file:///{source_id}.pdf", title, revision_id, 1,
             "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"))
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, created_at) VALUES (?,?,?,?)",
            (revision_id, source_id, f"sha256:{source_id}", "2026-01-01T00:00:00Z"))
        connection.commit()
    blocks: list[DocumentBlock] = []
    units: list[DocumentUnit] = []
    ordinal = 1
    for unit_index, (header, rows) in enumerate(sections):
        header_ref = f"/page/{unit_index + 1}/SectionHeader/{ordinal}"
        span_ids = []
        if header:
            blocks.append(DocumentBlock.build(span_id=f"s{ordinal}", block_type="SectionHeader", text=header,
                                              ordinal=ordinal, page=unit_index + 1, section_path=[header_ref],
                                              extractor_block_id=header_ref))
            span_ids.append(f"s{ordinal}")
            ordinal += 1
        for block_type, text, role_hint in rows:
            blocks.append(DocumentBlock.build(span_id=f"s{ordinal}", block_type=block_type, text=text,
                                              ordinal=ordinal, page=unit_index + 1, role_hint=role_hint,
                                              section_path=[header_ref] if header else ["transcript"]))
            span_ids.append(f"s{ordinal}")
            ordinal += 1
        units.append(DocumentUnit(unit_id=f"{extraction_id}_u{unit_index}", label=header or "transcript",
                                  ordinal=unit_index, semantic_hash=f"sha256:{extraction_id}{unit_index}",
                                  page_start=unit_index + 1, page_end=unit_index + 1, span_ids=span_ids))
    blocks.append(DocumentBlock.build(span_id="s999", block_type="PageHeader", text=f"{title} running header",
                                      ordinal=999, page=1))
    ir = DocumentIR(extractor=extractor, extractor_version="1", units=units, blocks=blocks, assets=[],
                    health=ExtractionHealth())
    _persist(repository, ir, revision_id=revision_id, extraction_id=extraction_id)


def build_e0_vault(tmp_path: Path, name: str = "e0vault", *, exam: bool = True,
                   config: str | None = None, manual_ai: bool = False) -> tuple[VaultPaths, Repository]:
    root = tmp_path / "fixtures-local" / "contextual-embeddings" / "vaults" / name
    root.parent.mkdir(parents=True, exist_ok=True)
    paths = create_basic_vault(root)
    append_config_toml(paths.root, config or "[source_retrieval]\nquery_rewrite = false\n")
    if manual_ai:
        # No production route resolves a client (a verification or comparison the
        # system arms ask for finds none), so no test can reach a real model.
        import tomlkit

        toml = paths.root / "learnloop.toml"
        document = tomlkit.parse(toml.read_text(encoding="utf-8"))
        document["ai"]["active_provider"] = "manual"
        toml.write_text(tomlkit.dumps(document), encoding="utf-8")
        paths = VaultPaths(paths.root, load_vault(paths.root, load_environment=False).config)
    repository = Repository(paths.sqlite_path)
    _seed(repository, source_id="src_book", extraction_id="ext_book", title="Linear Algebra Book", sections=BOOK)
    _seed(repository, source_id="src_talk", extraction_id="ext_talk", title="Lecture on bases",
          sections=[("", [("Caption", text, None) for text in CAPTIONS])], extractor="youtube_transcript")
    members = [{"source_id": "src_book", "revision_id": "rev_src_book", "default_role": "primary_textbook"},
               {"source_id": "src_talk", "revision_id": "rev_src_talk", "default_role": "primary_textbook"}]
    if exam:
        _seed(repository, source_id="src_exam", extraction_id="ext_exam", title="Midterm",
              sections=[("Midterm problems", [("Text", EXAM, None)])])
        members.append({"source_id": "src_exam", "revision_id": "rev_src_exam", "default_role": "exam"})
    upsert_source_set(paths.root, {"id": "sset_e0", "subject_id": "linear-algebra", "title": "E0 sources",
                                   "members": members})
    return paths, repository


def hash_vector(text: str, dims: int) -> list[float]:
    seed = int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")
    generator = np.random.default_rng(seed)
    vector = generator.standard_normal(dims)
    words = set(text.lower().split())
    for word in words:
        vector[int(hashlib.sha256(word.encode()).hexdigest(), 16) % dims] += 3.0
    return [float(value) for value in vector]


def int8_vector(text: str, dims: int) -> list[int]:
    vector = np.asarray(hash_vector(text, dims))
    scaled = np.clip(np.round(vector / (np.max(np.abs(vector)) or 1) * 127), -127, 127)
    return [int(value) for value in scaled]


class FakeEmbeddingTransport:
    """Hosted embedding endpoints: grouped or flat, shuffled rows, counted."""

    def __init__(self, *, dims: Mapping[str, int], int8_models: frozenset[str] = frozenset(),
                 fail: Callable[[int, dict[str, Any]], int | None] | None = None,
                 corrupt: Callable[[list[Any]], list[Any]] | None = None, seed: int = 7) -> None:
        self.dims = dict(dims)
        self.int8_models = int8_models
        self.fail = fail
        self.corrupt = corrupt
        self.random = random.Random(seed)
        self.requests: list[dict[str, Any]] = []
        self.headers: list[dict[str, str]] = []

    def _vector(self, model: str, text: str, context: list[str] | None = None) -> Any:
        key = text if context is None else text + "\n" + " ".join(context)
        if model in self.int8_models:
            return int8_vector(key, self.dims[model])
        return hash_vector(key, self.dims[model])

    def post(self, url: str, *, headers: Mapping[str, str], body: Mapping[str, Any], timeout: float) -> HttpResponse:
        self.requests.append({"url": url, "body": json.loads(json.dumps(body))})
        self.headers.append(dict(headers))
        if self.fail is not None:
            status = self.fail(len(self.requests), dict(body))
            if status is not None:
                return HttpResponse(status, None, f"req-{len(self.requests)}")
        model = body["model"]
        nested = body.get("inputs") if "inputs" in body else body.get("input")
        tokens = 0
        if nested and isinstance(nested[0], list):
            data = []
            for index, chunks in enumerate(nested):
                rows = [{"index": position, "embedding": self._vector(model, text, chunks)}
                        for position, text in enumerate(chunks)]
                tokens += sum(len(text.split()) for text in chunks)
                self.random.shuffle(rows)
                data.append({"index": index, "data": rows})
        else:
            data = [{"index": index, "embedding": self._vector(model, text)} for index, text in enumerate(nested)]
            tokens += sum(len(text.split()) for text in nested)
        self.random.shuffle(data)
        if self.corrupt is not None:
            data = self.corrupt(data)
        return HttpResponse(200, {"data": data, "usage": {"total_tokens": tokens}}, f"req-{len(self.requests)}")


class FakeQwenClient:
    """The production OpenRouter embedding client's identity (transport,
    model, endpoint, dimensions; metered), hash vectors, and one model call
    per batch reporting its input tokens (a request gate admits it)."""

    model_id = model = "qwen/qwen3-embedding-8b"
    provider_type = "openai_embedding"
    provider_name = "openrouter_embedding"
    default_base_url = "https://openrouter.ai/api/v1"
    dims = 4096

    def __init__(self) -> None:
        from types import SimpleNamespace

        self.calls: list[tuple[int, str]] = []
        self.profile = SimpleNamespace(base_url="https://openrouter.ai/api/v1", model=self.model_id)

    def embed(self, inputs: list[str], task_prefix: str) -> list[list[float]]:
        from learnloop.ai.execution import model_call, report_call_usage

        with model_call(self, purpose="embedding", prompt=list(inputs)):
            self.calls.append((len(inputs), task_prefix))
            report_call_usage({"input_tokens": sum(len(str(text).encode("utf-8")) for text in inputs),
                               "output_tokens": 0})
            return [hash_vector(f"{task_prefix}:{text}" if task_prefix == "never" else text, self.dims)
                    for text in inputs]




def _test_price():
    from learnloop.experiments.contextual_embeddings import pins

    if not hasattr(pins, "PriceVerification"):  # a harness from before fix round 4 has no price records
        return None
    return pins.PriceVerification("https://example.invalid/test-price-page", "2026-10-21")


@pytest.fixture
def verified_prices():
    """Mark every metered pin's price verified for one test (the pins are
    frozen dataclasses shared by reference, so module constants see it too),
    then restore them. Production pins stay empty: the orchestrator fills
    them from the providers' published price pages."""

    from learnloop.experiments.contextual_embeddings import pins

    record = _test_price()
    if record is None:
        yield None
        return
    every = [*pins.EMBEDDING_PINS.values(), *pins.ROLE_PINS.values()]
    saved = [(pin, pin.price_verified) for pin in every]
    for pin in every:
        object.__setattr__(pin, "price_verified", record)
    try:
        yield record
    finally:
        for pin, value in saved:
            object.__setattr__(pin, "price_verified", value)


FAKE_KEYS = {"PERPLEXITY_API_KEY": "pplx-test-key-not-real-0000", "VOYAGE_API_KEY": "voyage-test-key-not-real-0000",
             "OPENROUTER_API_KEY": "sk-or-test-key-not-real-0000"}


def _context(prompt: str) -> dict[str, Any]:
    return json.loads(prompt[prompt.index("{"):])["context"]


def _words(text: str) -> set[str]:
    return {word.strip(".,;:()$'").lower() for word in str(text).split() if len(word.strip(".,;:()$'")) > 3}


def fake_respond(role: str, prompt: str, _model: Any) -> dict[str, Any]:
    """Deterministic answers for every E0 role, from the prompt's own JSON."""

    context = _context(prompt)
    if role == "writer":
        questions = []
        for seed in context["seeds"]:
            passages = seed["passages"]
            first = sorted(passages, key=lambda passage: passage["ref"])[0]
            words = " ".join(first["text"].split()[:8])
            questions.append({"seed_ref": seed["seed_ref"], "question": f"Why is it true that {words}?",
                              "support_refs": [first["ref"]], "answer_refs": [first["ref"]],
                              "answerable": seed["stratum"] != "no_support"})
        return {"questions": questions}
    if role == "context":
        return {"contexts": [{"ref": item["ref"], "context": "This passage sits in a chapter of a linear algebra "
                              "text and develops vector spaces, identities, maps and bases; it depends on the "
                              "definitions stated earlier in the same section of the excerpt."}
                             for item in context["excerpt"]]}
    if role in ("label_a", "label_b"):
        question = _words(context["question"])
        labels, required = [], []
        threshold = 3 if role == "label_a" else 4
        for candidate in context["candidates"]:
            overlap = len(question & _words(candidate["text"]))
            relevance = ("required" if overlap >= threshold else "helpful" if overlap >= 2
                         else "background" if overlap == 1 else "unrelated")
            labels.append({"ref": candidate["ref"], "relevance": relevance})
            if relevance == "required":
                required.append(candidate["ref"])
        if getattr(_model, "__name__", "") == "SufficiencyPass":
            return {"sufficient_sets": [[ref] for ref in required[:2]], "answerable": bool(required)}
        return {"labels": labels, "sufficient_sets": [[ref] for ref in required[:2]], "answerable": bool(required)}
    if role == "adjudicator":
        labels = [{"ref": candidate["ref"], "relevance": candidate["pass_1"] or "unrelated"}
                  for candidate in context["candidates"]]
        return {"labels": labels, "sufficient_sets": context["pass_1_sets"],
                "answerable": bool(context["pass_1_sets"]), "unresolved": False}
    if role == "tutor":
        passages = context["passages"]
        return {"answer": "Because of the cited passage." if passages else "The passages do not say.",
                "cited_refs": [passages[0]["ref"]] if passages else [], "abstained": not passages}
    if role in ("judge_a", "judge_b", "judge_adjudicator"):
        ok = "pass" if context.get("cited_refs") else "fail"
        citations = ok if role != "judge_b" or len(context["passages"]) > 2 else "fail"
        return {"correct": ok, "assumptions": "pass", "citations": citations, "abstention": "n/a"}
    raise AssertionError(f"unexpected role {role}")


#: The resolved identity each pinned profile's client reports.
PROFILE_IDENTITY = {
    "codex_luna": ("codex_sdk", "gpt-6-luna", None),
    "codex_low": ("codex_sdk", "gpt-5.6-sol", None),
    "e0_openrouter_sonnet": ("openrouter", "anthropic/claude-sonnet-5.5", "https://openrouter.ai/api/v1"),
}


class FakeRoleClient:
    """A structured transport for one pinned profile: ``complete`` makes one
    physical request (admitted by the context's gate), reports usage and
    answers with ``fake_respond`` for the role named in the purpose."""

    def __init__(self, profile_name: str, *, provider_type: str | None = None, model: str | None = None,
                 base_url: str | None = None, respond: Callable[..., Any] = None,
                 usage: Mapping[str, Any] | None = None) -> None:
        from types import SimpleNamespace

        default = PROFILE_IDENTITY.get(profile_name, ("codex_sdk", "unknown", None))
        self.provider_name = profile_name
        self.provider_type = provider_type or default[0]
        self.model = model or default[1]
        self.profile = SimpleNamespace(base_url=base_url if base_url is not None else default[2], model=self.model,
                                       reasoning_effort=None, max_tokens=None)
        self.respond = respond or fake_respond
        self.usage = dict(usage or {"input_tokens": 500, "output_tokens": 200})
        self.requests: list[dict[str, Any]] = []

    def supports(self, capability: str) -> bool:
        from learnloop.ai.transport import ISOLATED_TURN, STRUCTURED_COMPLETION

        return capability in (STRUCTURED_COMPLETION, ISOLATED_TURN)

    def complete(self, request: Any) -> Any:
        from learnloop.ai.execution import model_call, report_call_usage

        with model_call(self, purpose=request.purpose, prompt=request.prompt, budget=request.output_budget_tokens):
            report_call_usage(dict(self.usage))
        self.requests.append({"purpose": request.purpose, "output_budget_tokens": request.output_budget_tokens})
        role = str(request.purpose).removeprefix("e0_")
        value = self.respond(role, request.prompt, request.result_model)
        return value if hasattr(value, "model_dump") else request.result_model.model_validate(value)


def qwen_bag_of_words(dims: int = 4096) -> Any:
    """``BagOfWordsEmbedder`` with the production Qwen client's endpoint, so
    the Qwen identity check (fix round 4, High 4) accepts it."""

    from tests.embedding_fakes import BagOfWordsEmbedder

    embedder = BagOfWordsEmbedder(dims=dims)
    embedder.default_base_url = "https://openrouter.ai/api/v1"
    return embedder


@pytest.fixture
def unverified_prices():
    """Every metered pin's price UNverified for one test (the empty record a
    pin starts from), then restored: admission must refuse them all."""

    from learnloop.experiments.contextual_embeddings import pins

    empty = pins.PriceVerification()
    every = [*pins.EMBEDDING_PINS.values(), *pins.ROLE_PINS.values()]
    saved = [(pin, pin.price_verified) for pin in every]
    for pin in every:
        object.__setattr__(pin, "price_verified", empty)
    try:
        yield empty
    finally:
        for pin, value in saved:
            object.__setattr__(pin, "price_verified", value)
