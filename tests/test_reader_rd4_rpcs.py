"""The scratchpads' RD4 RPCs (spec §3.4, §18.1): registered, desktop only, params refusing extra fields, replies
versioned; and the import fences still keep pad text away from everything that writes evidence but its two exits."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from learnloop_sidecar.handlers.pads import PAD_RD4_RPCS
from tests.helpers import create_basic_vault
from tests.reading_path_fixtures import call, context

RD4_RPCS = ("pad.submit_block", "pad.proposals", "proposal.label", "pad.drain", "carried.carry", "carried.list",
            "carried.mark")
MINIMAL = {
    "pad.submit_block": {"submissionId": "s", "blockId": "b", "versionId": "v", "as": "attempt",
                         "target": {"sessionId": "ses", "practiceItemId": "pi"}},
    "pad.proposals": {"padId": "p"},
    "proposal.label": {"labelId": "l", "proposalId": "x", "label": "dismiss", "proposalKind": "promoted_row"},
    "pad.drain": {"deskId": "d"},
    "carried.carry": {"carriedId": "c", "text": "why?", "originKind": "typed"},
    "carried.list": {},
    "carried.mark": {"eventId": "e", "carriedId": "c", "event": "surfaced"},
}


def test_the_rpcs_are_registered_and_desktop_only():
    from learnloop_mobile.allowlist import ALLOWLIST
    from learnloop_sidecar.registry import METHOD_REGISTRY

    assert PAD_RD4_RPCS == RD4_RPCS
    assert all(name in METHOD_REGISTRY and name not in ALLOWLIST for name in RD4_RPCS)


@pytest.mark.parametrize("name", RD4_RPCS)
def test_params_refuse_an_extra_field(name):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    model = METHOD_REGISTRY[name].params_model
    model.model_validate(MINIMAL[name])
    with pytest.raises(ValidationError):
        model.model_validate({**MINIMAL[name], "unexpected": True})


def test_a_submission_target_refuses_an_extra_field_and_names_a_kind():
    from learnloop_sidecar.registry import METHOD_REGISTRY

    model = METHOD_REGISTRY["pad.submit_block"].params_model
    with pytest.raises(ValidationError):
        model.model_validate({**MINIMAL["pad.submit_block"],
                              "target": {"sessionId": "ses", "practiceItemId": "pi", "grade": "full"}})
    with pytest.raises(ValidationError):
        model.model_validate({**MINIMAL["pad.submit_block"], "as": "note"})


@pytest.mark.parametrize("name", ("pad.proposals", "proposal.label", "pad.drain", "carried.carry", "carried.list",
                                  "carried.mark"))
def test_every_reply_is_versioned(tmp_path, name):
    ctx = context(create_basic_vault(tmp_path / "vault").root)
    call(ctx, "pad.apply", {"clientId": "c", "seq": 1, "padId": "p", "ops": [{"op": "create_pad", "kind": "named"}]})
    if name == "carried.mark":
        call(ctx, "carried.carry", MINIMAL["carried.carry"])
    assert call(ctx, name, MINIMAL[name])["version"] == 1


def test_the_gap_pipeline_and_the_substrate_never_import_a_pad_module():
    """Fence 1's exits are the pads' own (``pads.emission``, ``pads.submission``): the pipeline reads a pad text from
    the job's frozen snapshot, and the span recipe from the gap row, never from a pad table or module."""

    import ast
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "src" / "learnloop"
    for package in ("diagnosis", "substrate"):
        for path in (root / package).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = ([alias.name for alias in node.names] if isinstance(node, ast.Import)
                         else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
                for name in names:
                    assert not name.startswith(("learnloop.pads", "learnloop.db.stores.pad")), (path, name)
            assert "pad_block_versions" not in path.read_text(encoding="utf-8"), path


@pytest.fixture(scope="module")
def graph():
    import grimp
    from importlinter.configuration import configure

    configure()
    return grimp.build_graph("learnloop", "learnloop_sidecar", "learnloop_mobile", "learnloop_mcp",
                             include_external_packages=True)


def _fence_kept(contract_id: str, graph) -> bool:
    import copy
    import tomllib
    from pathlib import Path

    from importlinter.contracts.forbidden import ForbiddenContract

    config = tomllib.loads((Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8"))
    contract = next(entry for entry in config["tool"]["importlinter"]["contracts"] if entry.get("id") == contract_id)
    options = {key: value for key, value in contract.items() if key not in ("id", "name", "type")}
    options["allow_indirect_imports"] = str(options["allow_indirect_imports"]).lower()
    session = {"root_packages": ["learnloop", "learnloop_sidecar", "learnloop_mobile", "learnloop_mcp"],
               "include_external_packages": True}
    checked = ForbiddenContract(name=contract["name"], session_options=session, contract_options=options)
    return checked.check(copy.deepcopy(graph), verbose=False).kept


@pytest.mark.parametrize("imported", ["learnloop.db.stores.pad_reads", "learnloop.db.stores.pad_ledgers"])
@pytest.mark.parametrize("importer", ["learnloop.diagnosis.text_gaps.sources", "learnloop.substrate.passage_spans"])
def test_fence_one_refuses_the_pads_read_and_ledger_modules_too(graph, importer, imported):
    """Nothing that writes evidence reads a pad through any of the pads' store modules, the read module included:
    the gap pipeline's only way in is the snapshot the pads' emission froze."""

    import copy

    assert _fence_kept("evidence-never-reads-desks-or-pads", graph)
    broken = copy.deepcopy(graph)
    broken.add_import(importer=importer, imported=imported, line_number=1, line_contents=f"import {imported}")
    assert not _fence_kept("evidence-never-reads-desks-or-pads", broken)
