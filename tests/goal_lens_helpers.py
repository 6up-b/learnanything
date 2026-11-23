"""Builders for the goal lens's tests (Reader workbench v2 RD6; no network, every model a fake).

``build_lens_vault`` is curriculum C0b's deliverable vault with ``lo_eigen`` taking ``lo_det`` as a
prerequisite; ``chain=True`` adds ``lo_rows`` ("Rows and row swaps") as ``lo_det``'s prerequisite, so at
*get the idea* (the closure reaches one step) ``lo_rows`` is needed only deeper. ``scoped_goal`` makes,
resolves, sets the depth of and judges one deliverable; ``lens_context`` is a sidecar context whose
background work runs inline and whose every model is a fake that counts its calls.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from learnloop.db.repositories import Repository
from learnloop.source_retrieval import deliverable_path as DP
from learnloop.source_retrieval import deliverables as DL
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_concept
from learnloop.vault.yaml_io import read_yaml, write_yaml
from tests.deliverable_fixtures import NOW, DeliverableFake, build_deliverable_vault, cover_all
from tests.practice_index_fakes import _learning_object
from tests.reading_path_fixtures import call, context
from tests.section_coverage_fixtures import CoverageJudgeFake


def build_lens_vault(root: Path, *, chain: bool = False, cover: tuple[str, ...] | None = None,
                     config: str = "") -> tuple[VaultPaths, Repository]:
    paths, repository = build_deliverable_vault(root, prerequisite=True, config=config)
    if chain:
        upsert_concept(paths.root, "rows_c", {
            "title": "Row operations", "type": "concept", "aliases": [], "description": "Row operations.",
            "tags": [], "created_at": NOW, "updated_at": NOW})
        lo = _learning_object("lo_rows", "Rows and row swaps")
        lo["concept"] = "rows_c"
        write_yaml(paths.learning_object_path("linear-algebra", "lo_rows"), lo)
        path = paths.learning_object_path("linear-algebra", "lo_det")
        data = read_yaml(path)
        data["prerequisites"] = ["rows_c"]
        write_yaml(path, data)
    wanted = cover if cover is not None else (("lo_eigen", "lo_det", "lo_rows") if chain else ("lo_eigen", "lo_det"))
    if wanted:
        cover_all(paths, repository, *wanted)
    return paths, repository


def scoped_goal(paths: VaultPaths, repository: Repository, *, sentence: str = "eigenvalues",
                depth: str | None = "learn_to_use_it", judge: bool = True, due_at: str | None = None,
                fake: DeliverableFake | None = None) -> str:
    goal_id = DL.create_deliverable(load_vault(paths.root), repository, sentence, due_at=due_at)["goal_id"]
    DL.resolve(load_vault(paths.root), repository, goal_id, client=fake or DeliverableFake())
    if depth:
        DL.add_input(load_vault(paths.root), repository, goal_id, "depth", text=depth)
        if judge:
            DP.judge(load_vault(paths.root), repository, goal_id, client=fake or DeliverableFake())
    return goal_id


def lens_context(paths: VaultPaths, **attrs: Any) -> Any:
    fake = attrs.pop("fake", None) or DeliverableFake()
    coverage = attrs.pop("coverage", None) or CoverageJudgeFake()
    return context(paths.root, deliverable_inline=True, coverage_judge_client=coverage,
                   deliverable_scope_client=fake, deliverable_path_client=fake, **attrs)


def levels(ctx: Any, goal_id: str, extraction_id: str, **params: Any) -> dict[str, dict[str, Any]]:
    """``goal.lens`` over one reading, by section id."""

    reply = call(ctx, "goal.lens", {"goal_id": goal_id, "extraction_id": extraction_id, **params})
    return {level["sectionId"]: level for level in reply["levels"]}


def summary(level: dict[str, Any]) -> tuple[Any, ...]:
    return (level["level"], level["mapping"], level["reasonKey"], level["loIds"])
