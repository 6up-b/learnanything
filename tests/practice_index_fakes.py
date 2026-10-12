"""Deterministic fakes and a small vault for practice-index tests (no network).

``HashingEmbedder`` is a feature-hashed bag of words. ``FakePracticeLLM``
answers every practice-index structured operation from the prompt's own JSON
payload, using lexical overlap where a real model would judge. Results are
plumbing checks, not evidence about which retrieval path is better.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from learnloop.ai.execution import model_call, report_call_usage
from learnloop.ai.transport import (
    BOUNDED_STRUCTURED_COMPLETION,
    STRUCTURED_COMPLETION,
    StructuredRequest,
)
from learnloop.practice_index.contracts import (
    CandidateJudgment,
    DossierContrast,
    FacetDossierDraft,
    PracticeRerank,
    RelevanceLabels,
    WrittenQueries,
    WrittenQuery,
)
from learnloop.practice_index.text import tokenize
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import write_yaml
from tests.helpers import NOW_ISO, create_basic_vault, write_facets


EMBED_DIMS = 64


class HashingEmbedder:
    model_id = model = "qwen/qwen3-embedding-8b"
    dims = EMBED_DIMS
    modalities = frozenset({"text"})
    max_input_tokens = 32_768
    provider_name = "fake_embedding"

    def __init__(self) -> None:
        self.calls: list[tuple[list[str], str]] = []

    def embed(self, inputs, task_prefix):
        with model_call(self, purpose="embedding", prompt=list(inputs)):
            self.calls.append((list(inputs), task_prefix))
            report_call_usage({"input_tokens": sum(len(t) for t in inputs) // 4, "output_tokens": 0})
            vectors = []
            for text in inputs:
                vector = [0.0] * EMBED_DIMS
                for token in tokenize(text):
                    index = int(hashlib.sha256(token.encode()).hexdigest(), 16) % EMBED_DIMS
                    vector[index] += 1.0
                vector[-1] += 0.5  # never all-zero
                vectors.append(vector)
            return vectors


def _payload(prompt: str) -> dict[str, Any]:
    return json.loads(prompt.rsplit("\n\n", 1)[1])


def _overlap(left: str, right: str) -> int:
    return len(set(tokenize(left)) & set(tokenize(right)))


class FakePracticeLLM:
    """A structured client for the four practice-index roles."""

    provider_name = "fake_codex"
    provider_type = "codex_sdk"
    model = "fake-practice-model"

    def __init__(self, *, provider_type: str = "codex_sdk", fail_purposes: set[str] | None = None):
        self.provider_type = provider_type
        self.fail_purposes = fail_purposes or set()
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def supports(self, capability: str) -> bool:
        # One fake "physical request" per complete(): no hidden retry or repair.
        return capability in {STRUCTURED_COMPLETION, BOUNDED_STRUCTURED_COMPLETION}

    def complete(self, request: StructuredRequest[Any]) -> Any:
        payload = _payload(request.prompt)
        self.calls.append((request.purpose, payload))
        with model_call(self, purpose=f"{request.purpose}:fake_turn", prompt=request.prompt):
            report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 64,
                               "resolved_model": self.model})
            if request.purpose in self.fail_purposes:
                from learnloop.ai.errors import AIProviderUnavailable

                raise AIProviderUnavailable("fake failure")
            handler = getattr(self, "_" + request.purpose)
            return handler(payload["context"])

    def _practice_dossier(self, context: dict[str, Any]) -> FacetDossierDraft:
        facet = context["facet"]
        label = facet.get("title") or facet.get("claim") or facet["id"]
        covers = [label, *(facet.get("applicability") or [])]
        moves = facet.get("postconditions") or facet.get("preconditions") or [f"apply {label}"]
        return FacetDossierDraft(
            covers=covers, excludes=list(facet.get("non_goals") or []), moves=list(moves),
            errors=list(facet.get("error_signatures") or []),
            contrast=[DossierContrast(neighbor_ref=n["ref"],
                                      difference=f"{label} rather than {n['title']}")
                      for n in context.get("neighbors", [])],
        )

    @staticmethod
    def _grade(request: str, candidate: dict[str, Any]) -> str:
        text = " ".join(str(candidate.get(key) or "") for key in ("prompt", "learning_object"))
        hits = _overlap(request, text)
        return "relevant" if hits >= 2 else "partial" if hits == 1 else "not_relevant"

    def _practice_rerank(self, context: dict[str, Any]) -> PracticeRerank:
        judged = [(c["ref"], self._grade(context["request"], c)) for c in context["candidates"]]
        order = {"relevant": 0, "partial": 1}
        picks = [ref for ref, grade in sorted(judged, key=lambda pair: (order.get(pair[1], 9), pair[0]))
                 if grade != "not_relevant"][: context["pick_at_most"]]
        return PracticeRerank(
            judgments=[CandidateJudgment(ref=ref, relevance=grade, rationale=f"{grade} by overlap")
                       for ref, grade in judged],
            picks=picks,
        )

    def _practice_query_writer(self, context: dict[str, Any]) -> WrittenQueries:
        queries = []
        for seed in context["seeds"]:
            if seed["kind"] == "skill":
                text = f"I want practice on {seed['skill']}"
            else:
                words = tokenize(seed["question"])[:4]
                text = f"questions about {' '.join(words)} {seed.get('learning_object') or ''}"
            queries.append(WrittenQuery(seed_ref=seed["seed_ref"], query=text))
        return WrittenQueries(queries=queries)

    def _practice_relevance_judge(self, context: dict[str, Any]) -> RelevanceLabels:
        return RelevanceLabels(labels=[
            CandidateJudgment(ref=c["ref"], relevance=self._grade(context["request"], c),
                              rationale="overlap")
            for c in context["candidates"]
        ])


# -- a small vault with registered facets ---------------------------------

TOPICS = {
    "eigen": ("Eigenvalues and eigenvectors", "Find eigenvalues as roots of the characteristic polynomial.",
              ["Compute the eigenvalues of [[2,0],[0,3]].", "Find an eigenvector of a rotation-free shear.",
               "Explain why the characteristic polynomial det(A - tI) gives eigenvalues."]),
    "determinant": ("Determinants", "Compute determinants by cofactor expansion.",
                    ["Compute the determinant of [[1,2],[3,4]] by cofactor expansion.",
                     "What happens to a determinant when two rows are swapped?",
                     "Use row reduction to evaluate a 3x3 determinant."]),
    "matmul": ("Matrix multiplication", "Multiply matrices row by column.",
               ["Multiply [[1,2],[0,1]] by [[3],[4]] row by column.",
                "Is matrix multiplication commutative? Give an example.",
                "Compute the product AB for two 2x2 matrices."]),
    "independence": ("Linear independence", "Decide whether a list of vectors is linearly independent.",
                     ["Are (1,0) and (2,0) linearly independent?",
                      "Show that a list containing the zero vector is dependent.",
                      "Find a dependence relation among three vectors in R^2."]),
    "span": ("Span", "Describe the span of a list of vectors.",
             ["Describe the span of (1,1) in R^2.",
              "Is (3,4) in the span of (1,0) and (0,1)?",
              "What is the span of the empty list?"]),
    "orthogonal": ("Orthogonality", "Use inner products to test orthogonality.",
                   ["Are (1,2) and (2,-1) orthogonal under the dot product?",
                    "Project (3,4) onto the unit vector (1,0).",
                    "Explain why orthogonal nonzero vectors are independent."]),
}


def facet_definitions() -> list[dict[str, Any]]:
    facets = []
    for key, (title, claim, _prompts) in TOPICS.items():
        facets.append({
            "id": f"facet_{key}", "title": title, "claim": claim, "status": "reviewed",
            "applicability": [f"problems about {title.lower()}"],
            "postconditions": [f"the {title.lower()} result is computed and checked"],
            "error_signatures": [f"confusing {title.lower()} with a neighbouring idea"],
            "non_goals": ["proof theory"],
            "concept_id": "singular_value_decomposition",
        })
    return facets


def _item(item_id: str, lo_id: str, prompt: str, facets: list[str], **extra: Any) -> dict[str, Any]:
    return {
        "schema_version": 1, "id": item_id, "learning_object_id": lo_id, "subjects": None,
        "practice_mode": extra.pop("practice_mode", "short_answer"),
        "attempt_types_allowed": ["independent_attempt", "hinted_attempt", "dont_know"],
        "evidence_facets": facets, "evidence_weights": {facet: 1.0 for facet in facets},
        "prompt": prompt, "expected_answer": f"ANSWER-{item_id}", "difficulty": 0.5,
        "tags": [], "hints": [], "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "correct", "points": 4, "description": f"Correct work for {item_id}."}],
            "fatal_errors": [],
        },
        "provenance": {"origin": "human", "source_refs": []},
        "created_at": NOW_ISO, "updated_at": NOW_ISO, **extra,
    }


def _learning_object(lo_id: str, title: str) -> dict[str, Any]:
    return {
        "schema_version": 1, "id": lo_id, "title": title, "subjects": ["linear-algebra"],
        "concept": "singular_value_decomposition", "knowledge_type": "procedure",
        "status": "active", "contradicts": None, "summary": title, "prerequisites": [],
        "confusables": [], "difficulty_prior": 0.5, "tags": [],
        "provenance": {"origin": "human", "source_refs": []},
        "created_at": NOW_ISO, "updated_at": NOW_ISO,
    }


def build_practice_vault(root: Path) -> VaultPaths:
    """Basic vault plus six registered facets, three LOs and eighteen items."""
    paths = create_basic_vault(root)
    write_facets(paths, facet_definitions())
    los = {"lo_matrices": ("Matrix computations", ["eigen", "determinant", "matmul"]),
           "lo_vectors": ("Vector lists", ["independence", "span"]),
           "lo_inner": ("Inner products", ["orthogonal"])}
    for lo_id, (title, keys) in los.items():
        write_yaml(paths.learning_object_path("linear-algebra", lo_id), _learning_object(lo_id, title))
        for key in keys:
            for index, prompt in enumerate(TOPICS[key][2], start=1):
                item_id = f"pi_{key}_{index}"
                write_yaml(paths.practice_item_path("linear-algebra", item_id),
                           _item(item_id, lo_id, prompt, [f"facet_{key}"]))
    return paths


def enable_practice_index(paths: VaultPaths, *, embeddings: bool = True) -> None:
    """Flip the paid-batch switches (and embeddings) in the template's own tables."""
    import re

    config_path = paths.root / "learnloop.toml"
    text = config_path.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^dossiers_enabled = false$", "dossiers_enabled = true", text)
    text = re.sub(r"(?m)^evaluation_enabled = false$", "evaluation_enabled = true", text)
    if embeddings:
        text = re.sub(r"(?m)^enabled = false$", "enabled = true", text, count=1)
        text = re.sub(r"(?m)^backfill_enabled = false$", "backfill_enabled = true", text)
        text = re.sub(r"(?m)^dimensions = 4096$", f"dimensions = {EMBED_DIMS}", text)
    if "dossiers_enabled = true" not in text:
        text += "\n[practice_index]\ndossiers_enabled = true\nevaluation_enabled = true\n"
    config_path.write_text(text, encoding="utf-8")
