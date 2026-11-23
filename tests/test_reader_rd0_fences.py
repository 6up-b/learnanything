"""The Reader workbench v2 import fences (spec §3.3): each contract is in pyproject.toml, names modules
that exist (or are declared for the stage that adds them), holds on today's import graph, and breaks when
a forbidden import is added to that graph."""

from __future__ import annotations

import copy
import tomllib
from pathlib import Path

import grimp
import pytest
from importlinter.contracts.forbidden import ForbiddenContract

ROOT = Path(__file__).resolve().parents[1]
#: Modules a fence names before they exist, each with the stage that adds it.
DECLARED = {
    "learnloop.intent.inline_veils": "the veil sets of an inline check",
    "learnloop.curriculum.goal_lens": "the goal lens",
}
#: Each fence: the contract, and one import the fence must refuse (importer, imported).
FENCES = {
    "evidence-never-reads-desks-or-pads": ("learnloop.attempts.attempts", "learnloop.pads.blocks"),
    "graders-never-read-the-workbench-v2": ("learnloop.attempts.grading", "learnloop.companion.history"),
    "graders-never-reach-the-workbench-v2": ("learnloop.attempts.grading", "learnloop.db.stores.span_projection_reads"),
    "desks-stay-off-scheduling-and-evidence": ("learnloop.desks.workspace", "learnloop.scheduling.scheduler"),
    "passage-projections-are-read-only": ("learnloop.passage_union.union", "learnloop.attempts.attempts"),
    "passage-spans-reach-only-the-stores": ("learnloop.substrate.passage_spans", "learnloop.reader.annotations"),
    "workbench-v2-calls-the-one-hint-service": ("learnloop.pads.blocks", "learnloop.hints.writer"),
    "notes-are-never-a-source-or-evidence": ("learnloop.pads.blocks", "learnloop.source_retrieval.note_links"),
}


def _contracts() -> dict[str, dict]:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return {entry["id"]: entry for entry in config["tool"]["importlinter"]["contracts"] if "id" in entry}


@pytest.fixture(scope="module")
def graph():
    from importlinter.configuration import configure

    configure()  # the settings a contract's check reads (its timer), as lint-imports sets them
    return grimp.build_graph("learnloop", "learnloop_sidecar", "learnloop_mobile", "learnloop_mcp",
                             include_external_packages=True)


def _check(contract: dict, graph) -> bool:
    options = {key: value for key, value in contract.items() if key not in ("id", "name", "type")}
    if isinstance(options.get("allow_indirect_imports"), bool):
        options["allow_indirect_imports"] = str(options["allow_indirect_imports"]).lower()
    session = {"root_packages": ["learnloop", "learnloop_sidecar", "learnloop_mobile", "learnloop_mcp"],
               "include_external_packages": True}
    checked = ForbiddenContract(name=contract["name"], session_options=session, contract_options=options)
    # A check removes the ignored imports from the graph it is given.
    return checked.check(copy.deepcopy(graph), verbose=False).kept


def test_every_fence_is_declared_and_names_modules_that_exist_or_are_declared(graph):
    contracts = _contracts()
    assert set(FENCES) <= set(contracts)
    for fence in FENCES:
        contract = contracts[fence]
        assert contract["type"] == "forbidden"
        for module in [*contract["source_modules"], *contract["forbidden_modules"]]:
            assert module in graph.modules or module in DECLARED, (fence, module)
    # A source module must exist: the goal lens joins the read-only fence's sources in the stage that adds it.
    assert "learnloop.curriculum.goal_lens" not in graph.modules


@pytest.mark.parametrize("fence", sorted(FENCES))
def test_each_fence_holds_and_a_forbidden_import_breaks_it(graph, fence):
    contract = _contracts()[fence]
    assert _check(contract, graph), fence
    importer, imported = FENCES[fence]
    assert importer in graph.modules and imported in graph.modules, (importer, imported)
    broken = copy.deepcopy(graph)
    broken.add_import(importer=importer, imported=imported, line_number=1, line_contents=f"import {imported}")
    assert not _check(contract, broken), fence


def test_the_fences_cover_the_specs_six_rules():
    contracts = _contracts()
    # 1: nothing that writes evidence reads pads, ink, desks or veil sets.
    evidence = contracts["evidence-never-reads-desks-or-pads"]
    assert {"learnloop.substrate", "learnloop.attempts", "learnloop.scheduling", "learnloop.diagnosis",
            "learnloop.router", "learnloop.adaptive_difficulty"} <= set(evidence["source_modules"])
    assert {"learnloop.desks", "learnloop.pads", "learnloop.intent.inline_veils"} <= set(evidence["forbidden_modules"])
    assert evidence["allow_indirect_imports"] is False
    # 2: the grader never reads pads, ink, threads, desks, veils or the goal lens.
    assert {"learnloop.desks", "learnloop.pads", "learnloop.companion", "learnloop.passage_union",
            "learnloop.intent.inline_veils", "learnloop.curriculum.goal_lens"} <= set(
        contracts["graders-never-read-the-workbench-v2"]["forbidden_modules"])
    # 3: desks import nothing from scheduling, evidence or the router.
    desks = contracts["desks-stay-off-scheduling-and-evidence"]
    assert desks["source_modules"] == ["learnloop.desks"] and desks["allow_indirect_imports"] is False
    assert {"learnloop.scheduling", "learnloop.router", "learnloop.attempts"} <= set(desks["forbidden_modules"])
    # 4: the union read (and its span projections) import no evidence writer.
    assert contracts["passage-projections-are-read-only"]["source_modules"] == ["learnloop.passage_union"]
    assert contracts["passage-spans-reach-only-the-stores"]["allow_indirect_imports"] is False
    # 5: the Reader's hint rule still holds, and the workbench's packages join it.
    assert set(contracts["workbench-calls-the-one-hint-service"]["source_modules"]) == {"learnloop.reader",
                                                                                       "learnloop.workbench"}
    assert set(contracts["workbench-v2-calls-the-one-hint-service"]["forbidden_modules"]) == set(
        contracts["workbench-calls-the-one-hint-service"]["forbidden_modules"])
    # 6: a note is still never a source, input or evidence; the desks, pads and the union read never reach it.
    assert {"learnloop.desks", "learnloop.pads", "learnloop.passage_union", "learnloop.companion"} <= set(
        contracts["notes-are-never-a-source-or-evidence"]["source_modules"])


def test_a_grader_reaching_a_workbench_read_through_any_dependency_breaks_its_fence(graph):
    """The direct-import fence cannot see a grader that reaches the exchange context (desk, window, pad
    blocks) through a dependency; the leaf fence follows every chain."""

    contract = _contracts()["graders-never-reach-the-workbench-v2"]
    assert contract["allow_indirect_imports"] is False
    assert _check(contract, graph)
    for imported in ("learnloop.db.stores.span_projection_reads", "learnloop.db.stores.pad_reads"):
        broken = copy.deepcopy(graph)
        # Every grader reaches the repository; a read of the workbench reachable from it is reachable from them.
        broken.add_import(importer="learnloop.db.repositories", imported=imported, line_number=1, line_contents="x")
        assert not _check(contract, broken), imported


def test_the_union_read_reaching_a_mutating_store_breaks_its_fence(graph):
    contract = _contracts()["passage-projections-are-read-only"]
    assert {"learnloop.db.stores.pads", "learnloop.db.stores.span_projections"} <= set(contract["forbidden_modules"])
    assert _check(contract, graph)
    for imported in ("learnloop.db.stores.pads", "learnloop.db.stores.span_projections"):
        broken = copy.deepcopy(graph)
        broken.add_import(importer="learnloop.passage_union.union", imported=imported, line_number=1,
                          line_contents="x")
        assert not _check(contract, broken), imported


def test_the_read_modules_hold_no_write():
    """The reads the union, the history and the desks use are their own modules, and none writes: a write
    statement in one would also fail the registered-SQL-owner guard (tests/test_architecture.py)."""

    import re

    pattern = re.compile(r"\b(?:INSERT\s+(?:OR\s+\w+\s+)?INTO|UPDATE|DELETE\s+FROM|REPLACE\s+INTO)\b", re.I)
    for name in ("pad_reads", "span_projection_reads"):
        assert not pattern.search((ROOT / "src/learnloop/db/stores" / f"{name}.py").read_text(encoding="utf-8")), name
