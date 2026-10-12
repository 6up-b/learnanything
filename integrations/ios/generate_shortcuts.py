"""Deterministic native-only unsigned Shortcuts. Device acceptance is required."""

from pathlib import Path
import plistlib
import uuid

ROOT = Path(__file__).parent
ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


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

    def add(self, action, **params):
        self.actions.append({"WFWorkflowActionIdentifier": "is.workflow.actions." + action,
                             "WFWorkflowActionParameters": params})

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
        self.add("documentpicker.save", WFAskWhereToSave=False,
                 WFSaveFileOverwrite=False, WFFileStorageService="iCloud Drive",
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
        w.add("convertimage", WFImageFormat="JPEG", WFImagePreserveMetadata=False,
              WFImageCompressionQuality=0.85)
    w.set("Payload")
    w.add("date", WFDateActionMode="Current Date")
    w.set("Now")
    w.add("format.date", WFDate=var("Now"), WFDateFormatStyle="ISO 8601",
          WFISO8601IncludeTime=True)
    w.set("Captured at")
    # ULID: epoch milliseconds encoded as 10 base32 digits, then 80 random bits.
    w.literal(ALPHABET, "Alphabet")
    w.add("text.split", WFText=var("Alphabet"), WFTextSeparator="Every Character")
    w.set("Characters")
    w.add("date", WFDateActionMode="Specified Date", WFDateActionDate="1970-01-01T00:00:00Z")
    w.set("Epoch")
    w.add("gettimebetweendates", WFInput=var("Epoch"), WFTimeUntilReferenceDate="Other",
          WFTimeUntilCustomDate=var("Now"), WFTimeUntilUnit="Seconds")
    w.add("math", WFMathOperation="×", WFMathOperand=1000)
    w.add("round", WFRoundMode="Always Round Down", WFRoundType="Left of Decimal",
          WFRoundDecimalPlaces=0)
    w.set("Time")
    w.literal("", "Capture ID")
    group = w.block("repeat.count", WFRepeatCount=10)
    w.add("math", WFInput=var("Time"), WFMathOperation="…",
          WFScientificMathOperation="Modulus", WFScientificMathOperand=32)
    w.add("math", WFMathOperation="+", WFMathOperand=1)
    w.set("Index")
    w.add("getitemfromlist", WFInput=var("Characters"), WFItemSpecifier="Item At Index",
          WFItemIndex=var("Index"))
    w.set("Character")
    w.literal("CHARID", "Capture ID", CHAR="Character", ID="Capture ID")
    w.add("math", WFInput=var("Time"), WFMathOperation="÷", WFMathOperand=32)
    w.add("round", WFRoundMode="Always Round Down", WFRoundType="Left of Decimal",
          WFRoundDecimalPlaces=0)
    w.set("Time")
    w.end("repeat.count", group)
    group = w.block("repeat.count", WFRepeatCount=16)
    w.add("number.random", WFRandomNumberMinimum=1, WFRandomNumberMaximum=32)
    w.set("Index")
    w.add("getitemfromlist", WFInput=var("Characters"), WFItemSpecifier="Item At Index",
          WFItemIndex=var("Index"))
    w.set("Character")
    w.literal("IDCHAR", "Capture ID", ID="Capture ID", CHAR="Character")
    w.end("repeat.count", group)
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
    w.add("runworkflow", WFWorkflowName="Flush LearnLoop outbox")
    return w


def flush():
    w = Workflow("Flush LearnLoop outbox")
    # Import-time setup modifies only the owner's private installed copy.
    # Never export/share that configured copy: it contains a plaintext token.
    w.setup("HTTPS host, e.g. https://desktop.tailnet.ts.net (no trailing slash)",
            "Host", "https://desktop.tailnet.ts.net")
    w.add("text.match", WFText=var("Host"),
          WFMatchTextPattern=r"^https://[a-zA-Z0-9.-]+\.ts\.net$")
    w.set("Valid Host")
    valid = w.block("conditional", WFInput=var("Valid Host"), WFCondition=100)
    w.end("conditional", valid, mode=1)
    w.add("showalert", WFAlertActionTitle="Invalid host",
          WFAlertActionMessage="Use an HTTPS .ts.net hostname without a path or trailing slash.")
    w.add("exit")
    w.end("conditional", valid)
    w.setup("Paste the capture-scope pairing token. Keep this configured Shortcut private.",
            "Token", "PAIR_CAPTURE_TOKEN_HERE")
    w.add("documentpicker.open", WFGetFilePath="LearnLoop/outbox",
          WFShowFilePicker=False, WFFileErrorIfNotFound=True, WFFileStorageService="iCloud Drive")
    w.add("file.getfoldercontents", WFGetFolderContentsRecursive=False)
    w.add("filter.files", WFContentItemFilter={
        "WFActionParameterFilterPrefix": 1,
        "WFContentPredicateBoundedDate": False,
        "WFActionParameterFilterTemplates": [
            {"Property": "File Extension", "Operator": 4, "Values": {"String": "json"}}]})
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
    w.add("documentpicker.open", WFShowFilePicker=False,
          WFGetFilePath=text("LearnLoop/outbox/ID.jpg", ID="Capture ID"),
          WFFileErrorIfNotFound=True, WFFileStorageService="iCloud Drive")
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
    w.add("showalert", WFAlertActionTitle="Capture retained",
          WFAlertActionMessage="Receipt missing capture_id. Files retained; flushing stopped.")
    w.add("exit")
    w.end("conditional", has_id)
    w.end("conditional", success, mode=1)
    w.add("showalert", WFAlertActionTitle="Capture retained", WFAlertActionMessage=(
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
