"""Structural checks, not a substitute for signed import/on-device acceptance."""

import importlib.util
from pathlib import Path
import plistlib

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
            convert = actions[ids.index("convertimage")]["WFWorkflowActionParameters"]
            assert convert["WFImageFormat"] == "JPEG"
            assert convert["WFImagePreserveMetadata"] is False
            assert ids.index("convertimage") < ids.index("documentpicker.save")


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
            assert any(c.get("WFConditionalActionString") == "received" for c in conditions)
            assert any(c.get("WFCondition") == 100 for c in conditions)
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
                assert p["WFTimeUntilReferenceDate"] == "Other"
                assert p["WFInput"]["Value"]["VariableName"] == "Epoch"
                assert p["WFTimeUntilCustomDate"]["Value"]["VariableName"] == "Now"
            if kind.endswith(".math") and p["WFMathOperation"] == "…":
                assert p["WFScientificMathOperation"] == "Modulus"
                assert p["WFScientificMathOperand"] == 32
            if kind.endswith(".documentpicker.save"):
                assert p["WFFileStorageService"] == "iCloud Drive"
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
    assert len(questions) == 2
    assert questions[1]["DefaultValue"] == "PAIR_CAPTURE_TOKEN_HERE"
    for question in questions:
        action = workflow["WFWorkflowActions"][question["ActionIndex"]]
        assert action["WFWorkflowActionIdentifier"] == "is.workflow.actions.gettext"
        assert question["ParameterKey"] in action["WFWorkflowActionParameters"]
    assert not any(
        a["WFWorkflowActionIdentifier"] == "is.workflow.actions.ask"
        for a in workflow["WFWorkflowActions"]
    )
