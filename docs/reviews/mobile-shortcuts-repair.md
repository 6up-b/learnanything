# Native Shortcut import and input repair

Real-phone acceptance exposed defects the old structural checks missed. The A1
diagnostic used a nonexistent Quick Look action, then omitted its explicit
input. The owner reports the corrected diagnostic displays the pairing page
and pairing succeeds. Flush then showed several unknown actions.

The repeated Flush failures were `showalert` (Apple's identifier is `alert`).
Auditing every generated action via the installed Apple `WFActionRegistry`
also found `convertimage` missing (`image.convert` is valid), unconnected
intermediate outputs, bare conditional inputs that Apple drops, and obsolete
parameter names. Signing alone had accepted these malformed workflows.

The generator now assigns deterministic UUIDs, connects consumed outputs
explicitly and wraps conditional inputs in the native Variable representation.
Current parameter keys are used for text input, rounding, date differences,
file filters and Run Shortcut. Flush binds one native outbox folder at import,
lists its files once, filters JSON manifests and resolves each image by its
matching name. Capture Save File actions bind the Shortcuts parent folder;
their destination paths already include LearnLoop/outbox. Run Shortcut binds
the installed Flush on import. No credential is embedded in a shared asset.

`integrations/ios/native_actions.json` records the system registry's action
classes and parameter keys, inspected 2026-11-03. Tests now reject unknown
identifiers and obsolete keys, verify earlier-output UUID references and native
conditional wrappers, and require deletion to remain inside BOTH the received
status guard and the nonempty server capture-id guard. Folder and manifest
filter wiring are checked separately. The native action round-trip retained
the corrected inputs; it does not execute a workflow or prove iOS file-provider
behaviour. A3 remains pending until the owner tests the replacements.

No server, queue, schema or algorithm behavior changes. The pairing token stays
valid. The existing `.gitignore` and `README.md` edits are outside this patch.

Validation: **21 Shortcut checks passed**, then **62 passed** across
`test_mobile_shortcuts.py`, `test_mobile_capture.py` and
`test_mobile_host_auth.py`. The sandbox run stalled at the first HTTP fixture;
the same focused selection passed outside the sandbox (one upstream Starlette
TestClient deprecation warning). The signed replacements were retrieved from
the private download endpoint and compared byte-for-byte with the signing
outputs. Phone import and file-provider execution remain the owner's A3 check.
