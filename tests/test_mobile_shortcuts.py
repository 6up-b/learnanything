"""Structural checks, not a substitute for signed import/on-device acceptance."""

import importlib.util
import json
from pathlib import Path
import plistlib
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]
IOS = ROOT / "integrations" / "ios"


def generated():
    spec = importlib.util.spec_from_file_location("shortcut_generator", IOS / "generate_shortcuts.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return list(module.generate())


def test_assets_are_reproducible_native_plists():
    for name, data in generated():
        assert (IOS / f"{name}.shortcut").read_bytes() == data
        actions = plistlib.loads(data)["WFWorkflowActions"]
        assert actions
        assert all(a["WFWorkflowActionIdentifier"].startswith("is.workflow.actions.") for a in actions)
        stack = []
        for action in actions:
            params = action["WFWorkflowActionParameters"]
            if "WFControlFlowMode" not in params:
                continue
            group = params["GroupingIdentifier"]
            mode = params["WFControlFlowMode"]
            if mode == 0:
                stack.append(group)
            elif mode == 2:
                assert stack.pop() == group
            else:
                assert stack[-1] == group
        assert not stack


def test_capture_saves_before_running_flush_and_generates_ulid():
    for name, data in generated():
        if name.startswith("Flush"):
            continue
        actions = plistlib.loads(data)["WFWorkflowActions"]
        ids = [a["WFWorkflowActionIdentifier"].removeprefix("is.workflow.actions.") for a in actions]
        assert "downloadurl" not in ids
        assert ids.index("documentpicker.save") < ids.index("runworkflow")
        assert ids.count("documentpicker.save") == (2 if name.startswith("Photo") else 1)
        repeats = [a["WFWorkflowActionParameters"]["WFRepeatCount"]
                   for a in actions if a["WFWorkflowActionParameters"].get("WFControlFlowMode") == 0
                   and a["WFWorkflowActionIdentifier"].endswith("repeat.count")]
        assert repeats == [10, 16]
        if name.startswith("Photo"):
            convert = actions[ids.index("image.convert")]["WFWorkflowActionParameters"]
            assert convert["WFImageFormat"] == "JPEG"
            assert convert["WFImagePreserveMetadata"] is False
            assert ids.index("image.convert") < ids.index("documentpicker.save")


def test_flush_never_deletes_without_received_receipt_and_id():
    data = dict(generated())["Flush LearnLoop outbox"]
    actions = plistlib.loads(data)["WFWorkflowActions"]
    conditions = []
    deleted = 0
    for action in actions:
        kind = action["WFWorkflowActionIdentifier"]
        p = action["WFWorkflowActionParameters"]
        if kind.endswith(".conditional"):
            if p["WFControlFlowMode"] == 0:
                conditions.append(p)
            elif p["WFControlFlowMode"] == 2:
                conditions.pop()
        if kind.endswith(".file.delete"):
            deleted += 1
            assert any(c.get("WFConditionalActionString") == "received"
                       and c["WFInput"]["Variable"]["Value"].get("VariableName") == "Status"
                       for c in conditions)
            assert any(c.get("WFCondition") == 100
                       and c["WFInput"]["Variable"]["Value"].get("VariableName") == "Server ID"
                       for c in conditions)
        if kind.endswith(".ask"):
            assert p["WFAskActionDefaultAnswer"] == ""
        if kind.endswith(".downloadurl"):
            assert p["WFHTTPMethod"] == "POST"
            assert p["WFHTTPBodyType"] in {"Form", "JSON"}
    assert deleted == 2
    assert not (IOS / "LearnLoop.js").exists()


def test_native_math_http_and_storage_parameters():
    """Keep documented native parameter names, not plausible invented ones."""
    for name, data in generated():
        actions = plistlib.loads(data)["WFWorkflowActions"]
        for action in actions:
            kind = action["WFWorkflowActionIdentifier"]
            p = action["WFWorkflowActionParameters"]
            if kind.endswith(".gettimebetweendates"):
                assert p["WFInput"]["Value"]["VariableName"] == "Epoch"
                assert p["WFTimeUntilFromDate"]["Value"]["VariableName"] == "Now"
            if kind.endswith(".math") and p["WFMathOperation"] == "…":
                assert p["WFScientificMathOperation"] == "Modulus"
                assert p["WFScientificMathOperand"] == 32
            if kind.endswith(".documentpicker.save"):
                assert not p["WFSaveFileOverwrite"]
                assert "LearnLoop/outbox/" in p["WFFileDestinationPath"]["Value"]["string"]
            if kind.endswith(".downloadurl"):
                assert p["Advanced"] and p["ShowHeaders"]
        if name.startswith("Flush"):
            ids = [a["WFWorkflowActionIdentifier"] for a in actions]
            assert ids.index("is.workflow.actions.text.match") < ids.index("is.workflow.actions.downloadurl")


def test_host_and_token_are_import_time_setup_not_per_capture_questions():
    workflow = plistlib.loads(dict(generated())["Flush LearnLoop outbox"])
    questions = workflow["WFWorkflowImportQuestions"]
    assert len(questions) == 3
    assert questions[1]["DefaultValue"] == "PAIR_CAPTURE_TOKEN_HERE"
    for question in questions[:2]:
        action = workflow["WFWorkflowActions"][question["ActionIndex"]]
        assert action["WFWorkflowActionIdentifier"] == "is.workflow.actions.gettext"
        assert question["ParameterKey"] in action["WFWorkflowActionParameters"]
    folder = questions[2]
    assert folder["ParameterKey"] == "WFFolder"
    assert workflow["WFWorkflowActions"][folder["ActionIndex"]]["WFWorkflowActionIdentifier"].endswith(".file.getfoldercontents")
    assert not any(
        a["WFWorkflowActionIdentifier"] == "is.workflow.actions.ask"
        for a in workflow["WFWorkflowActions"]
    )


def test_actions_and_parameters_exist_in_the_native_registry():
    catalog = json.loads((IOS / "native_actions.json").read_text())["actions"]
    metadata = {"UUID", "CustomOutputName", "Advanced", "GroupingIdentifier", "WFControlFlowMode"}
    for name, data in generated():
        for action in plistlib.loads(data)["WFWorkflowActions"]:
            identifier = action["WFWorkflowActionIdentifier"]
            assert identifier in catalog, (name, identifier)
            params = action["WFWorkflowActionParameters"]
            allowed = set(catalog[identifier]["parameters"]) | metadata
            if identifier.endswith(".conditional"):
                # Apple's legacy single-condition form is supported alongside
                # the newer WFConditions form, but requires a Variable wrapper.
                allowed |= {"WFInput", "WFCondition", "WFConditionalActionString"}
            assert set(params) <= allowed, (name, identifier, set(params) - allowed)


def test_imported_workflows_have_explicit_input_connections():
    def references(value):
        if isinstance(value, dict):
            if value.get("Type") == "ActionOutput":
                yield value["OutputUUID"]
            for child in value.values():
                yield from references(child)
        elif isinstance(value, list):
            for child in value:
                yield from references(child)

    for name, data in generated():
        seen = set()
        for action in plistlib.loads(data)["WFWorkflowActions"]:
            params = action["WFWorkflowActionParameters"]
            identifier = action["WFWorkflowActionIdentifier"]
            for reference in references(params):
                assert reference in seen, (name, identifier, reference)
            assert params["UUID"] not in seen
            seen.add(params["UUID"])
            if identifier.endswith(".setvariable"):
                assert params["WFInput"]["Value"]["Type"] == "ActionOutput"
            if identifier.endswith(".conditional") and params.get("WFControlFlowMode") == 0:
                assert params["WFInput"]["Type"] == "Variable"
                assert params["WFInput"]["Variable"]["WFSerializationType"] == "WFTextTokenAttachment"


def test_flush_binds_one_folder_and_only_uploads_manifest_files():
    workflow = plistlib.loads(dict(generated())["Flush LearnLoop outbox"])
    actions = workflow["WFWorkflowActions"]
    assert not any(a["WFWorkflowActionIdentifier"].endswith(".documentpicker.open") for a in actions)
    listing = next(a for a in actions if a["WFWorkflowActionIdentifier"].endswith(".file.getfoldercontents"))
    assert listing["WFWorkflowActionParameters"]["Recursive"] is False
    filters = [a["WFWorkflowActionParameters"] for a in actions
               if a["WFWorkflowActionIdentifier"].endswith(".filter.files")]
    assert len(filters) == 2
    assert all(p["WFContentItemInputParameter"]["Value"]["VariableName"] == "Outbox files" for p in filters)
    manifests = filters[0]["WFContentItemFilter"]
    assert manifests["WFSerializationType"] == "WFContentPredicateTableTemplate"
    assert manifests["Value"]["WFActionParameterFilterTemplates"] == [
        {"Property": "File Extension", "Operator": 4, "Values": {"String": "json"}}]
    image = filters[1]["WFContentItemFilter"]["Value"]["WFActionParameterFilterTemplates"][0]
    assert image["Property"] == "Name"
    assert image["Values"]["String"]["Value"]["string"] == "\ufffc.jpg"


@pytest.mark.parametrize("url,accepted", [
    ("https://desktop.tailnet.ts.net", True),
    ("https://desktop.tailnet.ts.net:443", True),
    ("https://desktop.tailnet.ts.net:8445", True),
    ("https://desktop.tailnet.ts.net:1", True),
    ("https://desktop.tailnet.ts.net:65535", True),
    ("https://desktop.tailnet.ts.net:0", False),
    ("https://desktop.tailnet.ts.net:65536", False),
    ("https://desktop.tailnet.ts.net:8445/app", False),
    ("https://desktop.tailnet.ts.net:8445/", False),
    ("https://desktop.tailnet.ts.net:8445\n", False),
    ("http://desktop.tailnet.ts.net:8445", False),
    ("https://desktop.tailnet.ts.net.evil.invalid:8445", False),
    ("https://token@desktop.tailnet.ts.net:8445", False),
])
def test_flush_accepts_https_ports_without_allowing_other_url_components(url, accepted):
    workflow = plistlib.loads(dict(generated())["Flush LearnLoop outbox"])
    pattern = next(a["WFWorkflowActionParameters"]["WFMatchTextPattern"]
                   for a in workflow["WFWorkflowActions"]
                   if a["WFWorkflowActionIdentifier"].endswith(".text.match"))
    # Shortcuts uses ICU's strict end anchor; Python <=3.13 spells it \\Z.
    assert bool(re.search(pattern.replace(r"\z", r"\Z"), url)) is accepted
