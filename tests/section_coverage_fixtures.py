"""Builders and fakes for curriculum C0a's tests (section coverage; no network).

``build_coverage_vault`` is T6's retrieval vault (the practice-index LOs, the
book ``src_book`` / ``ext_book`` and the exam ``src_exam``, whose question is
a sentinel about eigenvalues) plus a second book ``src_lay`` / ``ext_lay``
with a held-out unit (``lay_held``, another sentinel), and the LO
``lo_eigen`` whose provenance cites ``ext_book``'s eigenvalue chapter.
``big=True`` adds ``src_big``, a book of many eigenvalue sections (the
crowding test).

``CoverageJudgeFake`` answers ``section_coverage_judge`` from the prompt's own
context: a fixed treatment per section title (``treatments``), else
``develops`` when a passage names the topic's first word and ``not_about``
otherwise. Plumbing checks only, never evidence about judgment quality.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from learnloop.ai.execution import report_call_usage
from learnloop.ai.isolation import TOOL_FREE
from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, STRUCTURED_COMPLETION
from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.db.repositories import Repository
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_source_set
from learnloop.vault.yaml_io import write_yaml
from tests.practice_index_fakes import _learning_object
from tests.source_retrieval_fakes import EXAM_QUESTION, build_retrieval_vault, seed_source
from tests.structured_ai import StructuredClientFake

HELD_OUT_SENTINEL = "HELDOUTSENTINEL the eigenvalues of the held-out midterm matrix are seven and nine."
LAY = {
    "lay_eigen": ("5.1 Eigenvectors and eigenvalues", [
        ("An eigenvector of a square matrix A is a nonzero vector x with Ax = tx; the scalar t is an eigenvalue.", 1),
        ("Eigenvalues of a triangular matrix are the entries on its main diagonal.", 1),
    ]),
    "lay_char": ("5.2 The characteristic equation", [
        ("The eigenvalues of A are the roots of the characteristic equation det(A - tI) = 0.", 2),
    ]),
    "lay_held": ("5.9 Midterm review", [(HELD_OUT_SENTINEL, 3)]),
    "lay_ortho": ("6.1 Inner product and orthogonality", [
        ("Two vectors are orthogonal when their inner product is zero.", 4),
    ]),
}
BIG = {f"big_{index}": (f"{index} Eigenvalues, part {index}", [
    (f"Eigenvalues part {index}: eigenvalues of a square matrix solve the characteristic polynomial.", index),
]) for index in range(1, 9)}
#: ext_book's spans (tests.source_retrieval_fakes.seed_source numbering).
BOOK_EIGEN = "ch_eigen"
BOOK_EIGEN_SPAN = "s2"


def cite(paths: VaultPaths, lo_id: str, source_id: str, extraction_id: str, span_id: str) -> None:
    from learnloop.vault.yaml_io import read_yaml

    path = paths.learning_object_path("linear-algebra", lo_id)
    lo = read_yaml(path)
    lo["provenance"] = {"origin": "human", "source_refs": [{
        "ref_type": "canonical_source", "ref_id": source_id, "locator": f"span:{extraction_id}/{span_id}",
        "source_id": source_id, "extraction_id": extraction_id}]}
    write_yaml(path, lo)


def build_coverage_vault(root: Path, *, big: bool = False, held_out: bool = True,
                         config: str = "", embeddings: bool = False) -> tuple[VaultPaths, Repository]:
    paths, repository = build_retrieval_vault(root, embeddings=embeddings)
    seed_source(repository, source_id="src_lay", revision_id="rev_lay", extraction_id="ext_lay", title="Lay",
                units=LAY, furniture=False)
    members = [
        {"source_id": "src_book", "revision_id": "rev_book", "default_role": "primary_textbook"},
        {"source_id": "src_exam", "revision_id": "rev_exam", "default_role": "exam"},
        {"source_id": "src_lay", "revision_id": "rev_lay", "default_role": "primary_textbook"},
    ]
    if big:
        seed_source(repository, source_id="src_big", revision_id="rev_big", extraction_id="ext_big",
                    title="Big Book", units=BIG, furniture=False)
        members.append({"source_id": "src_big", "revision_id": "rev_big", "default_role": "primary_textbook"})
    upsert_source_set(paths.root, {"id": "sset_la", "subject_id": "linear-algebra",
                                   "title": "Linear algebra sources", "members": members})
    if held_out:
        save_unit_selection(repository, "ext_lay", list(LAY), exam_use_modes={"lay_held": "held_out_evaluation"})
    lo = _learning_object("lo_eigen", "Eigenvalues")
    lo["summary"] = "Eigenvalues of a square matrix are the roots of its characteristic polynomial."
    write_yaml(paths.learning_object_path("linear-algebra", "lo_eigen"), lo)
    cite(paths, "lo_eigen", "src_book", "ext_book", BOOK_EIGEN_SPAN)
    if config:
        with (paths.root / "learnloop.toml").open("a", encoding="utf-8") as handle:
            handle.write("\n" + config + "\n")
    return paths, repository


def hold_out(repository: Repository, *unit_ids: str) -> None:
    """Mark more of ``ext_lay``'s units held out (``lay_held`` stays held out)."""

    modes = {unit_id: "held_out_evaluation" for unit_id in ("lay_held", *unit_ids)}
    save_unit_selection(repository, "ext_lay", list(LAY), exam_use_modes=modes)


def prompt_context(prompt: str) -> dict[str, Any]:
    start = prompt.index("{", prompt.index("prompt_version"))
    return json.loads(prompt[start:])["context"]


class CoverageJudgeFake(StructuredClientFake):
    provider_name = "fake_coverage_judge"
    provider_type = "codex_sdk"
    model = "fake-coverage-model"

    def __init__(self, treatments: Mapping[str, str] | None = None, *, provider_type: str = "codex_sdk",
                 fail: Exception | None = None, notation: str = "", roles: tuple[str, ...] = ("definition",),
                 output_tokens: int = 120, omit: tuple[str, ...] = ()) -> None:
        self.treatments = dict(treatments or {})
        self.provider_type = provider_type
        self.fail = fail
        self.notation = notation
        self.roles = roles
        self.output_tokens = output_tokens
        self.omit = set(omit)
        self.contexts: list[dict[str, Any]] = []
        self.prompts: list[str] = []

    def supports(self, capability: str) -> bool:
        return capability in {STRUCTURED_COMPLETION, BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, TOOL_FREE}

    def complete(self, request: Any) -> Any:
        context = prompt_context(request.prompt)
        self.contexts.append(context)
        self.prompts.append(request.prompt)
        report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": self.output_tokens,
                           "resolved_model": self.model})
        if self.fail is not None:
            raise self.fail
        word = context["topic"]["title"].split()[0].casefold()
        related = [entry["ref"] for entry in context["related_topics"]]
        judgments = []
        for candidate in context["candidates"]:
            if candidate["title"] in self.omit:
                continue
            text = " ".join(passage["text"] for passage in candidate["passages"]).casefold()
            treatment = self.treatments.get(candidate["title"], "develops" if word[:5] in text else "not_about")
            judgments.append({
                "ref": candidate["ref"], "treatment": treatment, "rationale": f"{treatment} the topic",
                "roles": list(self.roles), "assumes": related[:1], "notation": self.notation,
                "passages": [{"ref": passage["ref"], "roles": [{"role": "definition", "confidence": "high"}]}
                             for passage in candidate["passages"][:1]],
            })
        return request.result_model.model_validate({"judgments": judgments, "picks": []})

    @property
    def calls(self) -> int:
        return len(self.contexts)


def table_counts(repository: Repository) -> dict[str, int]:
    with repository.connection() as connection:
        names = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        return {name: connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0] for name in names}
