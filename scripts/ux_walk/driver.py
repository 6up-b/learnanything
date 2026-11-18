"""The walk driver: one headless Chromium, driven through chromedriver, answering one persona's `walk` steps.

W3C WebDriver over HTTP with the standard library only. The driver reads the
persona's ``channel/`` (walk_protocol.py), performs each step, waits for the
app to settle, and writes the observation: ``observations/NNNN.txt`` (what a
person could perceive: walk_perceive.py) and ``observations/NNNN.png``.
What the persona never sees goes to ``<walk>/analyst/``: ``steps.jsonl`` (each
step, its time, its target, the bridge calls that failed during it) and
``console.jsonl`` (console errors and unhandled rejections).

    python scripts/ux_walk/driver.py --walk-root <walk> --url http://127.0.0.1:<port>/ [--viewport phone]
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import walk_perceive  # noqa: E402
import walk_protocol  # noqa: E402

ELEMENT_KEY = "element-6066-11e4-a52e-4f735466cecf"
DESKTOP = (1380, 880)  # the Tauri window's size (tauri.conf.json)
PHONE = (390, 844)
PHONE_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/18.0 Mobile/15E148 Safari/604.1")
KEYS = {
    "enter": "", "return": "", "escape": "", "esc": "", "tab": "",
    "backspace": "", "delete": "", "space": " ", "arrowup": "", "arrowdown": "",
    "arrowleft": "", "arrowright": "", "up": "", "down": "", "left": "",
    "right": "", "home": "", "end": "", "pageup": "", "pagedown": "",
    "shift": "", "control": "", "ctrl": "", "alt": "", "meta": "", "cmd": "",
    **{f"f{number}": chr(0xE031 + number - 1) for number in range(1, 13)},
}
MODIFIERS = {"shift", "control", "ctrl", "alt", "meta", "cmd"}
FIND_TEXT_JS = r"""
const wanted = arguments[0].toLowerCase();
const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
let best = null;
while (walker.nextNode()) {
  const node = walker.currentNode;
  if (!node.textContent.toLowerCase().includes(wanted)) continue;
  const element = node.parentElement;
  const rect = element.getBoundingClientRect();
  const style = getComputedStyle(element);
  if (rect.width < 1 || rect.height < 1 || style.visibility === "hidden") continue;
  if (rect.bottom < 0 || rect.top > innerHeight || rect.right < 0 || rect.left > innerWidth) continue;
  best = element;
  break;
}
return best;
"""
NO_CONSOLE_JS = "return (window.__walkConsole && window.__walkConsole.drain()) || [];"


class WebDriverError(Exception):
    def __init__(self, error: str, message: str):
        super().__init__(f"{error}: {message}")
        self.error = error
        self.message = message


class WebDriver:
    def __init__(self, base: str):
        self.base = base.rstrip("/")
        self.session: str | None = None

    def request(self, method: str, path: str, body: Any = None, timeout: float = 120) -> Any:
        url = self.base + (f"/session/{self.session}" if self.session and not path.startswith("/session") and
                           path != "/status" else "") + path
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(url, data=data, method=method,
                                         headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read() or b"{}")
        except urllib.error.HTTPError as exc:
            payload = json.loads(exc.read() or b"{}")
            value = payload.get("value") or {}
            raise WebDriverError(value.get("error", str(exc.code)), value.get("message", "")) from None
        return payload.get("value")

    def new_session(self, capabilities: dict) -> None:
        value = self.request("POST", "/session", {"capabilities": {"alwaysMatch": capabilities}})
        self.session = value["sessionId"]

    def execute(self, script: str, *args: Any) -> Any:
        return self.request("POST", "/execute/sync", {"script": script, "args": list(args)})

    def screenshot(self) -> bytes:
        return base64.b64decode(self.request("GET", "/screenshot"))

    def actions(self, sources: list[dict]) -> None:
        self.request("POST", "/actions", {"actions": sources})
        self.request("DELETE", "/actions")

    def close(self) -> None:
        if self.session:
            try:
                self.request("DELETE", "", timeout=20)
            except (WebDriverError, OSError):
                pass
            self.session = None


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def element_ref(raw: Any) -> str | None:
    return raw.get(ELEMENT_KEY) if isinstance(raw, dict) else None


def key_sequence(spec: str) -> list[dict]:
    """``Control+k`` as WebDriver key actions: modifiers down, the key, modifiers up."""

    parts = [part for part in spec.split("+") if part]
    if not parts:
        raise ValueError("no key named")
    *mods, key = parts
    codes = []
    for mod in mods:
        if mod.lower() not in MODIFIERS:
            raise ValueError(f"{mod} is not a modifier (Shift, Control, Alt, Meta)")
        codes.append(KEYS[mod.lower()])
    main = KEYS.get(key.lower(), key if len(key) == 1 else None)
    if main is None:
        raise ValueError(f"unknown key {key!r}")
    actions = [{"type": "keyDown", "value": code} for code in codes]
    actions += [{"type": "keyDown", "value": main}, {"type": "keyUp", "value": main}]
    actions += [{"type": "keyUp", "value": code} for code in reversed(codes)]
    return actions


def matches(name: str, wanted: str) -> int:
    """2 for an exact (case-insensitive) name, 1 when the name contains it, else 0."""

    name, wanted = name.casefold().strip(), wanted.casefold().strip()
    if not wanted:
        return 0
    if name == wanted:
        return 2
    return 1 if wanted in name else 0


class StepFailed(Exception):
    pass


class Driver:
    def __init__(self, args: argparse.Namespace):
        self.walk_root = Path(args.walk_root).resolve()
        self.persona = self.walk_root / "persona"
        self.channel = self.persona / "channel"
        self.observations = self.persona / "observations"
        self.files = self.persona / "files"
        self.analyst = self.walk_root / "analyst"
        for directory in (self.channel, self.observations, self.files, self.analyst):
            directory.mkdir(parents=True, exist_ok=True)
        self.url = args.url
        self.bridge = args.bridge or args.url.rstrip("/")
        self.viewport = args.viewport
        self.chromedriver = args.chromedriver
        self.chromium = args.chromium
        self.settle_limit = args.settle
        self.stopping = False
        self.process: subprocess.Popen | None = None
        self.webdriver: WebDriver | None = None
        self.last_elements: dict[int, tuple[str | None, str, str]] = {}
        self.bridge_offset = 0
        self.seen_urls = 0
        self.seen_close = False

    # -- lifecycle --
    def start(self) -> None:
        port = free_port()
        log = (self.analyst / "chromedriver.log").open("ab")
        self.process = subprocess.Popen(
            [self.chromedriver, f"--port={port}", "--allowed-ips=127.0.0.1", "--log-level=WARNING"],
            stdout=log, stderr=log, start_new_session=False)
        self.webdriver = WebDriver(f"http://127.0.0.1:{port}")
        deadline = time.monotonic() + 30
        while True:
            try:
                if self.webdriver.request("GET", "/status").get("ready"):
                    break
            except (OSError, WebDriverError):
                pass
            if time.monotonic() > deadline:
                raise SystemExit("chromedriver did not start")
            time.sleep(0.2)
        profile = self.walk_root / "run" / "chrome-profile"
        profile.mkdir(parents=True, exist_ok=True)
        width, height = PHONE if self.viewport == "phone" else DESKTOP
        chrome_args = [
            "--headless=new", f"--window-size={width},{height}", f"--user-data-dir={profile}",
            "--no-first-run", "--no-default-browser-check", "--disable-extensions", "--disable-sync",
            "--disable-background-networking", "--disable-component-update", "--disable-domain-reliability",
            "--disable-client-side-phishing-detection", "--no-pings", "--metrics-recording-only",
            "--disable-features=Translate,OptimizationHints,MediaRouter,AutofillServerCommunication",
            "--password-store=basic", "--force-device-scale-factor=1", "--lang=en-US",
            # Nothing but the walk's own loopback servers resolves: no request leaves the machine.
            "--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE 127.0.0.1",
        ]
        options: dict[str, Any] = {"args": chrome_args}
        if self.chromium:
            options["binary"] = self.chromium
        if self.viewport == "phone":
            options["mobileEmulation"] = {
                "deviceMetrics": {"width": width, "height": height, "pixelRatio": 2.0, "touch": True},
                "userAgent": PHONE_UA,
            }
        self.webdriver.new_session({"browserName": "chrome", "goog:chromeOptions": options,
                                    "pageLoadStrategy": "normal", "unhandledPromptBehavior": "ignore"})
        self.fit_viewport(width, height)
        self.webdriver.request("POST", "/url", {"url": self.url})
        inner = self.webdriver.execute("return [window.innerWidth, window.innerHeight, devicePixelRatio];")
        capture = self.webdriver.execute("return !!window.__walkConsole;")
        self.log_step({"step": 0, "verb": "open", "url": self.url, "viewport": self.viewport, "page_size": inner,
                       "console_capture": capture})

    def fit_viewport(self, width: int, height: int) -> None:
        """Size the window so the page itself (not the window) is ``width`` x ``height``."""

        assert self.webdriver is not None
        if self.viewport == "phone" and (width, height) == PHONE:
            return  # mobile emulation fixes the page size itself
        self.webdriver.request("POST", "/window/rect", {"width": width, "height": height})
        inner = self.webdriver.execute("return [window.innerWidth, window.innerHeight];")
        if inner and (inner[0] != width or inner[1] != height):
            self.webdriver.request("POST", "/window/rect", {"width": width + (width - inner[0]),
                                                             "height": height + (height - inner[1])})

    def stop(self) -> None:
        if self.webdriver is not None:
            self.webdriver.close()
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()

    # -- the bridge and the logs --
    def bridge_state(self) -> dict:
        try:
            with urllib.request.urlopen(self.bridge + "/__bridge/state", timeout=5) as response:
                return json.loads(response.read())
        except (OSError, ValueError):
            return {}

    def answer_dialog(self, dialog_id: int, paths: list[str] | None) -> dict:
        body = json.dumps({"id": dialog_id, "paths": paths}).encode("utf-8")
        request = urllib.request.Request(self.bridge + "/__bridge/dialog/answer", data=body, method="POST",
                                         headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read())

    def bridge_records(self) -> list[dict]:
        path = self.analyst / "bridge.jsonl"
        if not path.exists():
            return []
        with path.open("rb") as stream:
            stream.seek(self.bridge_offset)
            data = stream.read()
            self.bridge_offset += len(data)
        return [json.loads(line) for line in data.splitlines() if line.strip()]

    def log_step(self, record: dict) -> None:
        with (self.analyst / "steps.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"t": round(time.time(), 3), **record}, default=str) + "\n")

    # -- perceiving --
    def dump(self) -> tuple[walk_perceive.Perception, list[Any]]:
        assert self.webdriver is not None
        raw = self.webdriver.execute(walk_perceive.DUMP_JS)
        return walk_perceive.perceive(raw), raw.get("elements") or []

    def settle(self, minimum: float = 0.4) -> None:
        time.sleep(minimum)
        deadline = time.monotonic() + self.settle_limit
        previous = None
        steady = 0
        while time.monotonic() < deadline:
            state = self.bridge_state()
            try:
                perception, _refs = self.dump()
                digest = hashlib.sha1(perception.text.encode("utf-8")).hexdigest()
            except WebDriverError:
                digest = None
            if not state.get("inflight") and digest == previous and not state.get("dialog_pending_new"):
                steady += 1
                if steady >= 2:
                    return
            else:
                steady = 0
            previous = digest
            time.sleep(0.3)

    def observe(self, step: int, header: list[str], screenshot: bool = True) -> tuple[str, str | None, dict]:
        assert self.webdriver is not None
        state = self.bridge_state()
        perception, refs = self.dump()
        self.last_elements = {
            element.number: (element_ref(refs[element.ref]) if element.ref is not None and element.ref < len(refs)
                             else None, element.role, element.name)
            for element in perception.elements
        }
        lines = list(header)
        dialog = state.get("dialog")
        if dialog:
            options = dialog.get("options") or {}
            kind = "folder chooser" if options.get("directory") else "file chooser"
            title = f' "{options["title"]}"' if options.get("title") else ""
            lines.append(f"A {kind}{title} is open over the app. Choose with `walk upload "
                         f"{'--folder NAME' if options.get('directory') else 'FILE'}` or close it with "
                         "`walk upload --cancel`.")
            filters = options.get("filters") or []
            if filters:
                lines.append("It shows: " + "; ".join(
                    f"{entry.get('name')} ({', '.join(entry.get('extensions') or [])})" for entry in filters))
            lines.append("Your files: " + (", ".join(self.list_files()) or "(none)"))
        urls = state.get("opened_urls") or []
        for entry in urls[self.seen_urls:]:
            lines.append(f"The app asked to open {entry['url']} in your web browser (that does not happen on this "
                         "walk).")
        self.seen_urls = len(urls)
        if state.get("window_closed") and not self.seen_close:
            lines.append("The LearnLoop window closed. (On this walk the page stays; in the app it would be gone.)")
            self.seen_close = True
        busy = list(perception.busy)
        if state.get("inflight"):
            busy.insert(0, "the app is still working")
        lines.append(f"Busy: {'yes, ' + '; '.join(busy) if busy else 'no'}")
        text = walk_perceive.render_observation(perception, header=lines)
        stem = f"{step:04d}"
        (self.observations / f"{stem}.txt").write_text(text, encoding="utf-8")
        shot = None
        if screenshot:
            (self.observations / f"{stem}.png").write_bytes(self.webdriver.screenshot())
            shot = f"observations/{stem}.png"
        return f"observations/{stem}.txt", shot, state

    def list_files(self) -> list[str]:
        found = []
        for path in sorted(self.files.rglob("*")):
            relative = path.relative_to(self.files).as_posix()
            found.append(relative + ("/" if path.is_dir() else ""))
        return found[:60]

    # -- resolving what to act on --
    def resolve(self, target: dict) -> tuple[str, str]:
        """A WebElement id and a description, for a number, a label, or a role and name."""

        if "number" in target:
            entry = self.last_elements.get(int(target["number"]))
            if entry is None:
                raise StepFailed(f"There is no [{target['number']}] in the last observation; look again.")
            ref, role, name = entry
            if ref is None:
                raise StepFailed("That element cannot be reached; look again.")
            return ref, f'{role} "{name}"'
        perception, refs = self.dump()
        wanted = str(target.get("name") or target.get("text") or "")
        role = target.get("role")
        scored = []
        for element in perception.elements:
            if role and element.role != role:
                continue
            score = matches(element.name, wanted)
            if score:
                scored.append((score, element))
        if scored:
            best = max(score for score, _ in scored)
            chosen = [element for score, element in scored if score == best]
            if len(chosen) > 1:
                listing = "; ".join(element.describe() for element in chosen[:8])
                self.last_elements = {
                    element.number: (element_ref(refs[element.ref]) if element.ref is not None else None,
                                     element.role, element.name) for element in perception.elements}
                raise StepFailed(f'More than one thing is labelled "{wanted}": {listing}. Use its number.')
            element = chosen[0]
            if element.ref is None:
                raise StepFailed("That element cannot be reached.")
            return element_ref(refs[element.ref]) or "", element.describe()
        if role is None:
            assert self.webdriver is not None
            found = self.webdriver.execute(FIND_TEXT_JS, wanted)
            if element_ref(found):
                return element_ref(found) or "", f'text "{wanted}"'
        raise StepFailed(f'Nothing on the screen is labelled "{wanted}".')

    # -- the verbs --
    def run(self, action: dict) -> tuple[str, dict]:
        """Perform one step; returns what was done (for the header) and analyst detail."""

        assert self.webdriver is not None
        verb = action.get("verb")
        state = self.bridge_state()
        dialog = state.get("dialog")
        if dialog and verb not in ("look", "upload", "say", "wait") and not (
                verb == "key" and str(action.get("keys", "")).lower() in ("escape", "esc")):
            raise StepFailed("A file chooser is open over the app. Choose with `walk upload` or close it with "
                             "`walk upload --cancel` first.")
        if verb == "_malformed":
            raise StepFailed(action.get("error", "malformed step"))
        if verb == "look":
            return "look", {}
        if verb == "say":
            return f'say "{action.get("text", "")}"', {"note": action.get("text")}
        if verb == "click":
            ref, description = self.resolve(action["target"])
            self.click(ref)
            return f"click {description}", {"target": description}
        if verb == "hover":
            ref, description = self.resolve(action["target"])
            self.webdriver.actions([{"type": "pointer", "id": "mouse", "parameters": {"pointerType": "mouse"},
                                     "actions": [{"type": "pointerMove", "duration": 100, "x": 0, "y": 0,
                                                  "origin": {ELEMENT_KEY: ref}}]}])
            return f"hover {description}", {"target": description}
        if verb == "type":
            return self.type(action)
        if verb == "key":
            keys = str(action.get("keys", ""))
            if dialog and keys.lower() in ("escape", "esc"):
                self.answer_dialog(dialog["id"], None)
                return "key Escape (closed the file chooser)", {}
            try:
                sequence = key_sequence(keys)
            except ValueError as exc:
                raise StepFailed(str(exc)) from None
            self.webdriver.actions([{"type": "key", "id": "keyboard", "actions": sequence}])
            return f"key {keys}", {}
        if verb == "scroll":
            return self.scroll(action)
        if verb == "back":
            self.webdriver.request("POST", "/back", {})
            return "back", {}
        if verb == "wait":
            if action.get("text"):
                limit = min(float(action.get("limit") or 15), 120.0)
                deadline = time.monotonic() + limit
                wanted = str(action["text"]).casefold()
                while time.monotonic() < deadline:
                    perception, _ = self.dump()
                    if wanted in perception.text.casefold():
                        return f'wait for "{action["text"]}" (it appeared)', {}
                    time.sleep(0.5)
                raise StepFailed(f'"{action["text"]}" did not appear within {int(limit)} s.')
            seconds = min(float(action.get("seconds") or 2), 120.0)
            time.sleep(seconds)
            return f"wait {seconds:g} s", {}
        if verb == "upload":
            return self.upload(action, dialog)
        if verb == "resize":
            if action.get("preset"):
                width, height = PHONE if action["preset"] == "phone" else DESKTOP
            else:
                width, height = int(action["width"]), int(action["height"])
            self.fit_viewport(width, height)
            return f"resize {width}×{height}", {}
        raise StepFailed(f"unknown verb {verb!r}")

    def click(self, ref: str) -> None:
        assert self.webdriver is not None
        try:
            self.webdriver.request("POST", f"/element/{ref}/click", {})
        except WebDriverError as exc:
            if exc.error == "element click intercepted":
                raise StepFailed("Something else is covering that spot; the click did not reach it.") from None
            if exc.error == "stale element reference":
                raise StepFailed("That is no longer on the screen; look again.") from None
            if exc.error == "element not interactable":
                raise StepFailed("That cannot be clicked right now.") from None
            raise

    def type(self, action: dict) -> tuple[str, dict]:
        assert self.webdriver is not None
        description = "the focused field"
        if action.get("into"):
            ref, description = self.resolve(action["into"])
            self.click(ref)
        else:
            active = element_ref(self.webdriver.request("GET", "/element/active"))
            tag = self.webdriver.execute("return document.activeElement && document.activeElement.tagName;")
            if not active or str(tag).lower() == "body":
                raise StepFailed("No field has focus. Click a field first, or use `--into`.")
            ref = active
        if action.get("clear"):
            try:
                self.webdriver.request("POST", f"/element/{ref}/clear", {})
            except WebDriverError:
                pass
        text = str(action.get("text", "")) + ("" if action.get("enter") else "")
        try:
            self.webdriver.request("POST", f"/element/{ref}/value", {"text": text})
        except WebDriverError as exc:
            if exc.error in ("element not interactable", "invalid element state"):
                raise StepFailed("That field does not take typing right now.") from None
            raise
        shown = action.get("text", "")
        return f'type "{shown[:80]}" into {description}' + (" and press Enter" if action.get("enter") else ""), {}

    def scroll(self, action: dict) -> tuple[str, dict]:
        assert self.webdriver is not None
        inner = self.webdriver.execute("return [window.innerWidth, window.innerHeight];")
        size = {"width": inner[0], "height": inner[1]}
        amount = action.get("amount", "page")
        step = int(size["height"] * 0.8) if amount == "page" else int(amount) * 40
        dx, dy = 0, 0
        direction = action.get("direction", "down")
        if direction in ("down", "up"):
            dy = step if direction == "down" else -step
        else:
            dx = step if direction == "right" else -step
        origin: Any = "viewport"
        x, y = int(size["width"] / 2), int(size["height"] / 2)
        where = ""
        if action.get("within"):
            ref, description = self.resolve(action["within"])
            origin, x, y = {ELEMENT_KEY: ref}, 0, 0
            where = f" in {description}"
        self.webdriver.actions([{"type": "wheel", "id": "wheel", "actions": [
            {"type": "scroll", "x": x, "y": y, "deltaX": dx, "deltaY": dy, "origin": origin}]}])
        return f"scroll {direction}{where}", {}

    def upload(self, action: dict, dialog: dict | None) -> tuple[str, dict]:
        if not dialog:
            raise StepFailed("No file chooser is open. Click the control that opens one first.")
        options = dialog.get("options") or {}
        if action.get("cancel"):
            self.answer_dialog(dialog["id"], None)
            return "closed the file chooser without choosing", {}
        if options.get("directory"):
            name = action.get("folder")
            if not name:
                raise StepFailed("This chooser wants a folder: `walk upload --folder NAME`.")
            folder = (self.files / name).resolve()
            if not folder.is_relative_to(self.files.resolve()):
                raise StepFailed("Choose a folder inside your files.")
            folder.mkdir(parents=True, exist_ok=True)
            self.answer_dialog(dialog["id"], [str(folder)])
            return f"chose the folder {name}", {"paths": [str(folder)]}
        names = action.get("files") or []
        if not names:
            raise StepFailed("This chooser wants a file: `walk upload FILE`.")
        if len(names) > 1 and not options.get("multiple"):
            raise StepFailed("This chooser takes one file.")
        paths = []
        for name in names:
            path = (self.files / name).resolve()
            if not path.is_relative_to(self.files.resolve()) or not path.is_file():
                raise StepFailed(f"There is no file {name!r} in your files. Yours: {', '.join(self.list_files())}")
            paths.append(str(path))
        result = self.answer_dialog(dialog["id"], paths)
        if not result.get("ok"):
            raise StepFailed(str((result.get("error") or {}).get("message") or "The chooser refused that."))
        return f"chose {', '.join(names)}", {"paths": paths}

    # -- the loop --
    def step(self, seq: int, action: dict) -> None:
        started = time.monotonic()
        ok, error, detail, done = True, None, {}, action.get("verb", "?")
        try:
            done, detail = self.run(action)
        except StepFailed as exc:
            ok, error = False, str(exc)
        except WebDriverError as exc:
            ok, error = False, f"The browser refused that ({exc.error})."
            detail = {"webdriver": exc.message[:500]}
        if action.get("verb") != "say":
            self.settle()
        elapsed = time.monotonic() - started
        header = [f"Step {seq}: {done}" + ("" if ok else " — did not work"), f"Took: {elapsed:.1f} s"]
        if error:
            header.append(f"Problem: {error}")
        try:
            observation, shot, _state = self.observe(seq, header, screenshot=action.get("verb") != "say")
        except WebDriverError as exc:
            observation, shot = None, None
            ok, error = False, f"The screen could not be read ({exc.error})."
        records = self.bridge_records()
        failed = [record for record in records if record.get("kind") == "invoke" and not record.get("ok")]
        try:
            console = self.webdriver.execute(NO_CONSOLE_JS) if self.webdriver else []
        except WebDriverError:
            console = []
        if console:
            with (self.analyst / "console.jsonl").open("a", encoding="utf-8") as stream:
                for entry in console:
                    stream.write(json.dumps({"step": seq, **entry}) + "\n")
        self.log_step({
            "step": seq, "action": action, "done": done, "ok": ok, "error": error, "ms": round(elapsed * 1000),
            "observation": observation, "screenshot": shot, "detail": detail,
            "bridge_calls": sum(1 for record in records if record.get("kind") == "invoke"),
            "failed_bridge_calls": failed, "console_entries": len(console),
            "fake_model_calls": sum(1 for record in records if record.get("kind") == "fake_model"),
        })
        walk_protocol.write_done(self.channel, seq, {"ok": ok, "error": error, "observation": observation,
                                                     "screenshot": shot, "elapsed": round(elapsed, 2)})

    def beat(self) -> None:
        # Its own thread: a long step (a wait, a slow screen) must not look like a dead driver to `walk`.
        while not self.stopping:
            walk_protocol.heartbeat(self.channel, last=self.last, running=self.running)
            time.sleep(1.0)

    def loop(self) -> None:
        self.last = walk_protocol.last_done(self.channel)
        self.running: int | None = None
        threading.Thread(target=self.beat, daemon=True).start()
        # The screen as the walk begins, before the persona's first step.
        self.settle(minimum=1.0)
        if self.last == 0 and not (self.observations / "0000.txt").exists():
            self.observe(0, ["Step 0: the app as the walk begins"])
        while not self.stopping:
            found = walk_protocol.next_action(self.channel, self.last)
            if found is None:
                time.sleep(0.15)
                continue
            seq, action = found
            self.running = seq
            self.step(seq, action)
            self.last, self.running = seq, None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--walk-root", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--bridge", help="the bridge's base URL when it differs from --url (phone walks)")
    parser.add_argument("--viewport", choices=("desktop", "phone"), default="desktop")
    parser.add_argument("--chromedriver", default="/usr/bin/chromedriver")
    parser.add_argument("--chromium", default="/usr/bin/chromium")
    parser.add_argument("--settle", type=float, default=8.0, help="most seconds to wait for the screen to settle")
    args = parser.parse_args(argv)
    driver = Driver(args)

    def stop(_signum: int, _frame: Any) -> None:
        driver.stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        driver.start()
        (driver.walk_root / "run" / "driver.ready").write_text(json.dumps({"pid": os.getpid()}), encoding="utf-8")
        driver.loop()
    finally:
        driver.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
