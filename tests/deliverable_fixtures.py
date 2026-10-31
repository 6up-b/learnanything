"""Builders and fakes for curriculum C0b's tests (scope resolution and the deliverable path; no network).

``build_deliverable_vault`` is C0a's coverage vault (the book ``ext_book``, the exam
``src_exam`` whose question is a sentinel, the second book ``ext_lay`` with a held-out
unit carrying another sentinel) plus ``lo_det`` ("Determinants", on its own concept
``determinants_c``), which ``lo_eigen`` takes as a prerequisite when
``prerequisite=True``.

``DeliverableFake`` answers both C0b routes from the prompt's own context:

* ``deliverable_scope_resolver``: every topic whose title's first word appears in an
  input is needed (the phrase is that word), the configured ``excluded`` titles never
  are, and the configured ``unmatched`` phrases are returned with a proposal;
* ``deliverable_path_judge``: per topic with sections, the configured primary (by
  section title) or the first section, a reason naming the book, and the other
  sections as alternates.

Plumbing checks only, never evidence about judgment quality.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from learnloop.ai.execution import report_call_usage
from learnloop.ai.isolation import TOOL_FREE
from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, STRUCTURED_COMPLETION
from learnloop.db.repositories import Repository
from learnloop.source_retrieval import section_coverage as SC
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_concept
from learnloop.vault.yaml_io import read_yaml, write_yaml
from tests.practice_index_fakes import _learning_object
from tests.section_coverage_fixtures import CoverageJudgeFake, build_coverage_vault
from tests.structured_ai import StructuredClientFake

NOW = "2026-10-31T09:00:00Z"


def build_deliverable_vault(root: Path, *, config: str = "", prerequisite: bool = False,
                            held_out: bool = True) -> tuple[VaultPaths, Repository]:
    paths, repository = build_coverage_vault(root, config=config, held_out=held_out)
    upsert_concept(paths.root, "determinants_c", {
        "title": "Determinants", "type": "concept", "aliases": [], "description": "Determinants of square matrices.",
        "tags": [], "created_at": NOW, "updated_at": NOW})
    lo = _learning_object("lo_det", "Determinants")
    lo["concept"] = "determinants_c"
    lo["summary"] = "The determinant of a square matrix, by cofactor expansion; invertible exactly when nonzero."
    write_yaml(paths.learning_object_path("linear-algebra", "lo_det"), lo)
    if prerequisite:
        path = paths.learning_object_path("linear-algebra", "lo_eigen")
        data = read_yaml(path)
        data["prerequisites"] = ["determinants_c"]
        write_yaml(path, data)
    return paths, repository


def cover_all(paths: VaultPaths, repository: Repository, *lo_ids: str,
              treatments: Mapping[str, str] | None = None) -> CoverageJudgeFake:
    """Judge C0a coverage for the LOs with C0a's fake (so the path has rows to read)."""

    judge = CoverageJudgeFake(treatments=treatments)
    vault = load_vault(paths.root)
    for lo_id in lo_ids:
        SC.judge(vault, repository, lo_id, client=judge)
    return judge


def prompt_context(prompt: str) -> dict[str, Any]:
    start = prompt.index("{", prompt.index("prompt_version"))
    return json.loads(prompt[start:])["context"]


class DeliverableFake(StructuredClientFake):
    provider_name = "fake_deliverable"
    provider_type = "codex_sdk"
    model = "fake-deliverable-model"

    def __init__(self, *, unmatched: tuple[str, ...] = (), excluded: tuple[str, ...] = (),
                 primaries: Mapping[str, str] | None = None, needs: tuple[str, ...] | None = None,
                 fail: Exception | None = None, reasons: Mapping[str, str] | None = None,
                 omit: tuple[str, ...] = (), bogus_primary: tuple[str, ...] = ()) -> None:
        self.unmatched = unmatched
        self.excluded = set(excluded)
        self.primaries = dict(primaries or {})
        self.needs = needs
        self.fail = fail
        self.reasons = dict(reasons or {})
        self.omit = set(omit)
        self.bogus_primary = set(bogus_primary)
        self.prompts: list[str] = []
        self.contexts: list[dict[str, Any]] = []
        self.purposes: list[str] = []

    def supports(self, capability: str) -> bool:
        return capability in {STRUCTURED_COMPLETION, BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, TOOL_FREE}

    def complete(self, request: Any) -> Any:
        context = prompt_context(request.prompt)
        self.prompts.append(request.prompt)
        self.contexts.append(context)
        scope = "Deliverable scope" in request.prompt
        self.purposes.append("scope" if scope else "path")
        report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 80,
                           "resolved_model": self.model})
        if self.fail is not None:
            raise self.fail
        if scope:
            return request.result_model.model_validate(self._scope(context))
        return request.result_model.model_validate(self._path(context))

    def _scope(self, context: Mapping[str, Any]) -> dict[str, Any]:
        text = " ".join(str(entry["text"]) for entry in context["inputs"]).casefold()
        needs = []
        for topic in context["topics"]:
            if topic["title"] in self.excluded:
                continue
            word = topic["title"].split()[0].casefold()
            if (self.needs is not None and topic["id"] in self.needs) or (self.needs is None and word in text):
                needs.append({"learning_object_id": topic["id"], "phrase": word})
        needs.append({"learning_object_id": "lo_not_in_the_vault", "phrase": "ghost"})
        unmatched = [{"phrase": phrase, "proposed_title": phrase.title(),
                      "proposed_statement": f"What {phrase} means and how to use it."} for phrase in self.unmatched]
        return {"needs": needs, "unmatched": unmatched}

    def _path(self, context: Mapping[str, Any]) -> dict[str, Any]:
        entries = []
        for topic in context["topics"]:
            if topic["title"] in self.omit:
                continue
            sections = topic["sections"]
            wanted = self.primaries.get(topic["title"])
            primary = next((s for s in sections if s["title"] == wanted), sections[0])
            ref = "ext_nowhere/sec_nowhere" if topic["title"] in self.bogus_primary else primary["ref"]
            entries.append({
                "learning_object_id": topic["id"], "primary": ref,
                "reason": self.reasons.get(topic["title"], f"Clear in {primary['book']}."),
                "alternates": [{"section": s["ref"], "difference": f"another view in {s['book']}"}
                               for s in sections if s["ref"] != primary["ref"]],
            })
        # Prerequisites listed last on purpose: code puts them first.
        entries.sort(key=lambda entry: next((t["kind"] == "prerequisite" for t in context["topics"]
                                             if t["id"] == entry["learning_object_id"]), False))
        return {"entries": entries}

    @property
    def calls(self) -> int:
        return len(self.contexts)
