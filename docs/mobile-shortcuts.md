# Native phone capture assets (M1)

The three `.shortcut` files in `integrations/ios/` are real **unsigned plist
workflows**, generated deterministically. They have **not** been signed, imported,
or exercised on an iPhone. Structural tests do not establish device compatibility.
No Scriptable or other companion app is required.

## iOS setup

1. Finish host/Tailscale setup and run
   `learnloop-mobile pair --label "iPhone Shortcut" --scope capture`. Open its QR
   URL or enter the manual code on `/pair`; copy the once-issued token. Keep it
   in your password manager, not in a tracked file or shared Shortcut.
2. Create **iCloud Drive → Shortcuts → LearnLoop → outbox** in Files. Native
   Shortcuts' default file provider is its `Shortcuts` folder; action paths are
   `LearnLoop/outbox`. If your iOS release uses a different base folder, bind
   *all* Save/Get File actions to the same folder when importing. This extra
   `Shortcuts` sandbox directory is the concrete implementation of the spec's
   `Files/LearnLoop/outbox`.
3. Regenerate assets if needed:

   ```sh
   uv run python integrations/ios/generate_shortcuts.py
   ```

   On macOS, the owner can sign each file for sharing:

   ```sh
   shortcuts sign --mode anyone \
     --input "integrations/ios/Capture to LearnLoop.shortcut" \
     --output "$HOME/Desktop/Capture to LearnLoop.signed.shortcut"
   ```

   Repeat for `Photo to LearnLoop` and `Flush LearnLoop outbox`. Signing may
   contact Apple; it has not been performed here. Import the signed files.
   Unsigned files are not directly installable on all iOS releases.
4. Share one text/URL to `Capture to LearnLoop`. Enter `text` or `url` at its
   kind prompt (`url` also covers arXiv IDs). Share one image to `Photo to
   LearnLoop`; it converts to JPEG and strips metadata before persisting it.
5. Import `Flush LearnLoop outbox` first. Its setup questions ask once for
   the HTTPS tailnet host without a trailing slash and the capture token.
   These values are stored in **your private installed Shortcut**, not the
   files shipped here. Never export/share your configured copy; revoke its token
   if you accidentally do. Setup text is not a password field: avoid observers,
   clear the clipboard, and do not screenshot it. Change the two initial Text
   actions after re-pairing. Capture invokes flush **after saving**; subsequent
   shares require no host/token prompts.

The workflow creates a ULID using a base32 epoch-millisecond prefix and 16
random base32 characters. The manifest holds the original timestamp, kind and
text/URL; photos have a sibling `<id>.jpg`. Save order is JPEG then manifest,
both **before networking**. Retries load those exact saved values/files, never
regenerating the ID, timestamp or JPEG. Files may sync via iCloud and contain
sensitive content; do not use this storage if that policy is unacceptable.

## Native-only error handling: accepted limitation

The owner chose native-only Shortcuts, with a usually-online desktop. Native
“Get Contents of URL” does not reliably expose HTTP status/catch network errors.
Consequently this implementation does **not** claim automatic 409 quarantine or
401-specific token replacement. The safety rule is narrower:

- Delete a manifest/JPEG pair only after a parsed response has `status=received`
  **and a nonempty `capture_id`** (the host returns this on 201/200).
- A thrown HTTP/network error stops the Shortcut; the pre-saved files remain.
- A parseable response without the receipt shows an alert and stops flushing.
- Check the token after 401; inspect a conflicting manifest after 409 and move
  it and its JPEG manually to `outbox/conflict/`. Do not silently change an
  existing payload or generate a new ID on retry.
- Other errors (413/415/422/429/5xx) retain the outbox. Inspect the host error,
  fix the cause, then run `Flush LearnLoop outbox`.

There is no background retry or cross-process lock. Run one capture/flush at a
time. A crash between the JPEG and manifest writes can leave an orphan JPEG;
inspect it manually. Do not remove files while a Shortcut is running. Storage
errors abort before sending; Shortcuts shows the error. Capturing does not start
practice or invoke AI.

### Owner acceptance required (A3)

Sign/import on the target iOS release; inspect action parameters/file-provider
bindings; confirm a 26-character ULID accepted by the host; share a HEIC image and
confirm actual JPEG multipart `file` bytes; verify text and URL JSON requests;
disable networking and confirm manifest/JPEG persistence; reconnect and flush
twice (one server capture); verify 401 and 409 leave files intact; cancel setup;
test quota failure; verify deletion requires a genuine receipt. In particular,
confirm native Shortcuts serializes the Form `file` field as a binary file, not
text, and the Dictionary-to-Text manifest as JSON. Revoke test tokens afterwards.
Until these pass, the assets are **unverified integration candidates**, not a
claim of completed phone acceptance.

## Android instructions

Use Tailscale plus a share-capable HTTP automation client exposing HTTP status
(for example HTTP Shortcuts). This is a manual recipe, not a shipped Android
app/export. Store the token in its private secret variable; exclude it from
exports. Configure:

```text
POST https://<desktop>.<tailnet>.ts.net/api/v1/capture
Authorization: Bearer <private token>
Content-Type: application/json
```

```json
{
  "client_capture_id": "01J00000000000000000000001",
  "kind": "text",
  "text": "Selected text",
  "source_app": "android_share",
  "captured_at": "2026-01-01T12:00:00Z"
}
```

Generate a **new ULID and timestamp per new capture**, not per attempt; the values
above are examples. URLs use `kind=url` and `url` instead of `text`. Images use
multipart scalar fields plus one binary field named `file`, with `kind=image`.
Convert HEIC to JPEG first. Let the client set the multipart boundary.

Persist the manifest and JPEG before attempting the request; flush those exact
files later. Delete only on 200/201 receipt, quarantine 409 without modifying the
payload, stop on 401 and replace the token, retain all other errors visibly.
If the tool cannot persist files and branch on statuses, label it **online-only**,
not an offline-capable integration. Perform the airplane-mode/idempotency/token
rotation checks above before trusting it. Desktop inbox routing remains manual.
