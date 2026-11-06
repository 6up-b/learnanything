"""Deterministic native-only unsigned Shortcuts. Device acceptance is required."""

from pathlib import Path
import plistlib
import uuid

ROOT = Path(__file__).parent
ID_DATE_FORMAT = "yyyyMMddHHmmssSSS"
ID_PADDING = "000000000"


def var(name):
    return {"Value": {"Type": "Variable", "VariableName": name},
            "WFSerializationType": "WFTextTokenAttachment"}


def text(value, **variables):
    attachments = {}
    for marker, name in variables.items():
        offset = value.index(marker)
        value = value.replace(marker, "\ufffc", 1)
        attachments[f"{{{offset}, 1}}"] = {"Type": "Variable", "VariableName": name}
    return {"Value": {"string": value, "attachmentsByRange": attachments},
            "WFSerializationType": "WFTextTokenString"}


class Workflow:
    def __init__(self, name):
        self.name = name
        self.actions = []
        self.import_questions = []
        self.output = None

    def add(self, action, **params):
        # Serialized workflows need explicit edges: the editor does not infer
        # "the preceding action" when it imports a generated plist.
        if action in {
            "setvariable", "image.convert", "math", "round", "documentpicker.save",
            "repeat.each", "detect.dictionary",
        } and "WFInput" not in params and params.get("WFControlFlowMode", 0) != 2:
            if self.output is None:
                raise ValueError(f"{action} needs an input")
            params["WFInput"] = self.output
        if action == "conditional" and "WFInput" in params:
            params["WFInput"] = {"Type": "Variable", "Variable": params["WFInput"]}
        identifier = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{self.name}/{len(self.actions)}/{action}"))
        params["UUID"] = identifier
        self.actions.append({"WFWorkflowActionIdentifier": "is.workflow.actions." + action,
                             "WFWorkflowActionParameters": params})
        self.output = {"Value": {"Type": "ActionOutput", "OutputUUID": identifier,
                                 "OutputName": action},
                       "WFSerializationType": "WFTextTokenAttachment"}

    def set(self, name):
        self.add("setvariable", WFVariableName=name)

    def literal(self, value, name, **variables):
        self.add("gettext", WFTextActionText=text(value, **variables))
        self.set(name)

    def ask(self, prompt, name):
        self.add("ask", WFAskActionPrompt=prompt, WFInputType="Text",
                 WFAskActionDefaultAnswer="")
        self.set(name)

    def setup(self, prompt, name, default):
        self.import_questions.append({
            "ActionIndex": len(self.actions), "Category": "Parameter",
            "ParameterKey": "WFTextActionText", "Text": prompt,
            "DefaultValue": default,
        })
        self.add("gettext", WFTextActionText=default)
        self.set(name)

    def configure(self, key, prompt):
        """Let Shortcuts create a native folder/shortcut reference on import."""
        self.import_questions.append({
            "ActionIndex": len(self.actions), "Category": "Parameter",
            "ParameterKey": key, "Text": prompt, "DefaultValue": "",
        })

    def block(self, action, **params):
        group = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{self.name}/{len(self.actions)}"))
        self.add(action, GroupingIdentifier=group, WFControlFlowMode=0, **params)
        return group

    def end(self, action, group, mode=2):
        self.add(action, GroupingIdentifier=group, WFControlFlowMode=mode)

    def dictionary(self, fields):
        self.add("dictionary", WFItems=dictionary(fields))

    def save(self, input_name, extension):
        self.add("setitemname", WFInput=var(input_name),
                 WFName=text(f"ID.{extension}", ID="Capture ID"))
        self.configure("WFFolder", "Choose iCloud Drive → Shortcuts (the parent of LearnLoop).")
        self.add("documentpicker.save", WFAskWhereToSave=False,
                 WFSaveFileOverwrite=False,
                 WFFileDestinationPath=text(f"LearnLoop/outbox/ID.{extension}", ID="Capture ID"))
        self.set("Saved " + extension)

    def get_key(self, source, key, target):
        self.add("getvalueforkey", WFInput=var(source), WFDictionaryKey=key)
        self.set(target)


def dictionary(fields):
    return {"Value": {"WFDictionaryFieldValueItems": [
        {"WFItemType": 0, "WFKey": text(k), "WFValue": v}
        for k, v in fields.items()]}, "WFSerializationType": "WFDictionaryFieldValue"}


def capture(photo=False):
    w = Workflow("Photo to LearnLoop" if photo else "Capture to LearnLoop")
    w.add("getvariable", WFVariable={"Value": {"Type": "ExtensionInput"},
                                     "WFSerializationType": "WFTextTokenAttachment"})
    if photo:
        w.add("image.convert", WFImageFormat="JPEG", WFImagePreserveMetadata=False,
              WFImageCompressionQuality=0.85)
    w.set("Payload")
    w.add("date", WFDateActionMode="Current Date")
    w.set("Now")
    w.add("format.date", WFDate=var("Now"), WFDateFormatStyle="ISO 8601",
          WFISO8601IncludeTime=True)
    w.set("Captured at")
    # A canonical-ULID-shaped ID built from one date format, with no arithmetic:
    # 17 timestamp digits and 9 digits of padding. The base32 encoder this replaces
    # failed on a real iPhone ("You asked for item 0") although its parameters
    # round-tripped through Apple's registry. One phone cannot share a millisecond
    # with itself, and a retry reuses the saved ID, so uniqueness needs no randomness.
    w.add("format.date", WFDate=var("Now"), WFDateFormatStyle="Custom", WFDateFormat=ID_DATE_FORMAT)
    w.set("ID time")
    w.literal(f"STAMP{ID_PADDING}", "Capture ID", STAMP="ID time")
    if photo:
        w.save("Payload", "jpg")
    else:
        w.ask("Capture kind: enter text or url (use url for arXiv IDs)", "Kind")
    fields = {"client_capture_id": var("Capture ID"), "captured_at": var("Captured at"),
              "source_app": text("ios_shortcut"), "kind": text("image") if photo else var("Kind")}
    if not photo:
        branch = w.block("conditional", WFInput=var("Kind"), WFCondition=4,
                         WFConditionalActionString="url")
        w.dictionary({**fields, "url": var("Payload")})
        w.set("Manifest")
        w.end("conditional", branch, mode=1)
        w.dictionary({**fields, "text": var("Payload")})
        w.set("Manifest")
        w.end("conditional", branch)
    else:
        w.dictionary(fields)
        w.set("Manifest")
    w.add("gettext", WFTextActionText=var("Manifest"))
    w.set("Manifest JSON")
    w.save("Manifest JSON", "json")
    w.add("notification", WFNotificationActionBody=(
        "Saved to Files → iCloud Drive → Shortcuts → LearnLoop → outbox. "
        "Sending now; failures keep this copy."))
    w.configure("WFWorkflow", "Choose the installed Flush LearnLoop outbox Shortcut.")
    w.add("runworkflow", WFWorkflow={"workflowName": "Flush LearnLoop outbox", "isSelf": False})
    return w


def flush():
    w = Workflow("Flush LearnLoop outbox")
    # Import-time setup modifies only the owner's private installed copy.
    # Never export/share that configured copy: it contains a plaintext token.
    w.setup("HTTPS host, e.g. https://desktop.tailnet.ts.net:8445 (no trailing slash)",
            "Host", "https://desktop.tailnet.ts.net")
    w.add("text.match", text=var("Host"),
          WFMatchTextPattern=(r"\Ahttps://[a-zA-Z0-9.-]+\.ts\.net"
                              r"(?::(?:[1-9][0-9]{0,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|"
                              r"65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5]))?\z"))
    w.set("Valid Host")
    valid = w.block("conditional", WFInput=var("Valid Host"), WFCondition=100)
    w.end("conditional", valid, mode=1)
    w.add("alert", WFAlertActionTitle="Invalid host",
          WFAlertActionMessage="Use an HTTPS .ts.net hostname with an optional port (1–65535), without a path or trailing slash.")
    w.add("exit")
    w.end("conditional", valid)
    w.setup("Paste the capture-scope pairing token. Keep this configured Shortcut private.",
            "Token", "PAIR_CAPTURE_TOKEN_HERE")
    w.configure("WFFolder", "Choose iCloud Drive → Shortcuts → LearnLoop → outbox.")
    w.add("file.getfoldercontents", Recursive=False)
    w.set("Outbox files")
    w.add("filter.files", WFContentItemInputParameter=var("Outbox files"), WFContentItemFilter={"Value": {
        "WFActionParameterFilterPrefix": 1,
        "WFContentPredicateBoundedDate": False,
        "WFActionParameterFilterTemplates": [
            {"Property": "File Extension", "Operator": 4, "Values": {"String": "json"}}]},
        "WFSerializationType": "WFContentPredicateTableTemplate"})
    group = w.block("repeat.each")
    w.add("getvariable", WFVariable=var("Repeat Item"))
    w.set("Manifest File")
    w.add("detect.dictionary")
    w.set("Manifest")
    w.get_key("Manifest", "client_capture_id", "Capture ID")
    w.get_key("Manifest", "kind", "Kind")
    w.literal("HOST/api/v1/capture", "Endpoint", HOST="Host")
    headers = dictionary({"Authorization": text("Bearer TOKEN", TOKEN="Token")})
    branch = w.block("conditional", WFInput=var("Kind"), WFCondition=4,
                     WFConditionalActionString="image")
    w.add("filter.files", WFContentItemInputParameter=var("Outbox files"), WFContentItemFilter={
        "WFSerializationType": "WFContentPredicateTableTemplate", "Value": {
            "WFActionParameterFilterPrefix": 1, "WFContentPredicateBoundedDate": False,
            "WFActionParameterFilterTemplates": [{"Property": "Name", "Operator": 4,
                "Values": {"String": text("ID.jpg", ID="Capture ID")}}]}})
    w.add("getitemfromlist", WFInput=w.output, WFItemSpecifier="First Item")
    w.set("JPEG File")
    for key in ["captured_at", "source_app"]:
        w.get_key("Manifest", key, key)
    w.add("downloadurl", WFURL=var("Endpoint"), WFHTTPMethod="POST",
          Advanced=True, ShowHeaders=True, WFHTTPHeaders=headers, WFHTTPBodyType="Form",
          WFFormValues=dictionary({
              "client_capture_id": var("Capture ID"), "kind": text("image"),
              "captured_at": var("captured_at"), "source_app": var("source_app"),
              "file": var("JPEG File")}))
    w.set("Receipt")
    w.end("conditional", branch, mode=1)
    w.add("downloadurl", WFURL=var("Endpoint"), WFHTTPMethod="POST",
          Advanced=True, ShowHeaders=True, WFHTTPHeaders=headers,
          WFHTTPBodyType="JSON", WFJSONValues=var("Manifest"))
    w.set("Receipt")
    w.end("conditional", branch)
    w.get_key("Receipt", "status", "Status")
    success = w.block("conditional", WFInput=var("Status"), WFCondition=4,
                      WFConditionalActionString="received")
    w.get_key("Receipt", "capture_id", "Server ID")
    has_id = w.block("conditional", WFInput=var("Server ID"), WFCondition=100)
    image = w.block("conditional", WFInput=var("Kind"), WFCondition=4,
                    WFConditionalActionString="image")
    w.add("file.delete", WFInput=var("JPEG File"))
    w.end("conditional", image)
    w.add("file.delete", WFInput=var("Manifest File"))
    w.end("conditional", has_id, mode=1)
    w.add("alert", WFAlertActionTitle="Capture retained",
          WFAlertActionMessage="Receipt missing capture_id. Files retained; flushing stopped.")
    w.add("exit")
    w.end("conditional", has_id)
    w.end("conditional", success, mode=1)
    w.add("alert", WFAlertActionTitle="Capture retained", WFAlertActionMessage=(
        "No received receipt. Stop here. Check token/host; inspect conflicts manually. "
        "Files remain in the outbox."))
    w.add("exit")
    w.end("conditional", success)
    w.end("repeat.each", group)
    return w


def generate():
    for workflow in [capture(), capture(photo=True), flush()]:
        value = {
            "WFWorkflowClientVersion": "3036.0.4.2",
            "WFWorkflowMinimumClientVersion": 900,
            "WFWorkflowName": workflow.name,
            "WFWorkflowIcon": {"WFWorkflowIconStartColor": 4282601983,
                               "WFWorkflowIconGlyphNumber": 59511},
            "WFWorkflowTypes": [] if workflow.name.startswith("Flush") else ["ActionExtension"],
            "WFWorkflowInputContentItemClasses": (
                ["WFImageContentItem"] if workflow.name.startswith("Photo")
                else ["WFStringContentItem", "WFURLContentItem"]),
            "WFWorkflowActions": workflow.actions,
            "WFWorkflowImportQuestions": workflow.import_questions,
        }
        yield workflow.name, plistlib.dumps(value, sort_keys=True)


if __name__ == "__main__":
    for name, content in generate():
        (ROOT / f"{name}.shortcut").write_bytes(content)
