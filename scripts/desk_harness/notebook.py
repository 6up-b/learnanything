"""The notebook frame's real-webview harness (docs/reviews/notebook-frame-b4-b5.md).

Build the harness page once (from apps/learnloop-tauri: `npx vite build --config vite.desks.config.mjs`), then
from the repository root, with the notebook extra installed and bubblewrap on the machine:

    uv run --no-sync --with playwright==1.65.2 --with pillow==11.3.0 python scripts/desk_harness/notebook.py \
        [--ref <the private reference directory>] [--shots DIR]

It starts a real sandboxed marimo session on a synthetic lesson notebook (written here, project-authored), serves
the harness page as the app's development origin (http://localhost:1420, one of the origins a notebook frame may
be framed by and posts its bridge to), and drives the page's notebook fixture (`?notebook=1`) in headless Chromium.
No window opens; nothing leaves the machine but requests to the session's own 127.0.0.1 proxy.

Chromium's local-network-access checks treat a page answered by Playwright (no address) as public and refuse its
frames on 127.0.0.1, which the app's own origin is not subject to (WebKitGTK has no such checks); the harness turns
them off for its browser.

Checks: the frame's honest states, its box and even margins, the paper theme inside the frame (colours and faces),
the bridge (the four messages accepted; forged, malformed and wrong-origin ones refused), an edit round trip, a
reload keeping the kernel without marimo's "Reconnected" banner, a paused window's frame inert, a preview's
placeholder. With `--ref`, the frame is also compared with the mockup's Teacher lesson state
(`#tabs=distance,pad=3` at 1440 × 900): the frame's box, the margins round it and the colours inside it, measured
on both screenshots the same way (written to <ref>/compare/notebook__*). Exit status 0 when every check passes.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import mimetypes
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from playwright.async_api import Page, Route, async_playwright

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "apps" / "learnloop-tauri" / "dist-desk-harness"
ORIGIN = "http://localhost:1420"
VIEWPORT = {"width": 1440, "height": 900}
CHROMIUM_ARGS = ["--disable-features=LocalNetworkAccessChecks,PrivateNetworkAccessForNavigations,"
                 "PrivateNetworkAccessRespectPreflightResults"]
#: The fixture's frame, where the mockup's Teacher lesson state draws it (x, y, width, height at 1440 × 900).
FRAME_BOX = (859, 288, 516, 518)
GEOMETRY_TOLERANCE_PX = 2

LESSON = '''import marimo

app = marimo.App(width="medium")


@app.cell
def imports():
    import marimo as mo
    return (mo,)


@app.cell
def title(mo):
    mo.md(
        """
        # A slope you can see

        *A synthetic lesson notebook for the frame's tests: one idea, one control, one commit point.*
        """
    )
    return


@app.cell
def prose(mo):
    mo.md(
        """
        **Part 1 · A line.** Drag the slider and watch the value follow. The square of the slider is shown
        below; nothing here is graded and nothing leaves the notebook.
        """
    )
    return


@app.cell
def controls(mo):
    x = mo.ui.slider(1, 20, value=3, label="x")
    x
    return (x,)


@app.cell
def square(mo, x):
    mo.md(f"<span id='ll-square'>square={x.value * x.value}</span>")
    return


@app.cell
def commit_point(mo):
    mo.Html(
        "<div class='ll-commit' id='ll-commit'>Before you drag: will the square grow faster than x?"
        "<div class='ll-verdict'>committed · revealed after you answer</div></div>"
    )
    return


if __name__ == "__main__":
    app.run()
'''


class Checks:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def check(self, name: str, ok: bool, detail: Any = None) -> bool:
        self.rows.append({"check": name, "ok": bool(ok), "detail": detail})
        print(("PASS " if ok else "FAIL ") + name + ("" if detail is None else f"  {json.dumps(detail, default=str)[:300]}"))
        return bool(ok)

    @property
    def failed(self) -> int:
        return sum(1 for row in self.rows if not row["ok"])


def hexes(rgb: str) -> str:
    """`rgb(a, b, c)` (or with alpha) as `#rrggbb`."""

    inside = rgb[rgb.index("(") + 1:rgb.rindex(")")].replace("/", " ").replace(",", " ").split()
    try:
        values = [round(float(part)) for part in inside[:3]]
    except ValueError:
        return rgb
    return "#" + "".join(f"{value:02x}" for value in values)


async def serve_dist(route: Route) -> None:
    url = route.request.url
    if not url.startswith(ORIGIN):
        await route.continue_() if "127.0.0.1" in url else await route.abort()
        return
    path = url[len(ORIGIN):].split("?")[0].lstrip("/") or "desk-harness.html"
    file = (DIST / path).resolve()
    if not file.is_relative_to(DIST.resolve()) or not file.is_file():
        await route.fulfill(status=404, body="not found")
        return
    await route.fulfill(status=200, body=file.read_bytes(), content_type=mimetypes.guess_type(file.name)[0] or "application/octet-stream")


async def open_fixture(browser: Any, session: dict[str, Any], query: str = "") -> Page:
    page = await browser.new_page(viewport=VIEWPORT)
    await page.route("**/*", serve_dist)
    await page.add_init_script("window.__notebookHarness = " + json.dumps(
        {"frameUrl": session["frame_url"], "sessionId": session["session_id"]}) + ";")
    await page.goto(f"{ORIGIN}/desk-harness.html?notebook=1{query}")
    return page


async def notebook_frame(page: Page, timeout: float = 30.0) -> Any:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for frame in page.frames:
            if "127.0.0.1" in frame.url:
                try:
                    if await frame.locator("#ll-square").count():
                        return frame
                except Exception:  # noqa: BLE001 - the frame is still loading
                    pass
        await asyncio.sleep(0.05)
    raise TimeoutError("the notebook frame never showed its cells")


async def text_in(frame: Any, selector: str) -> str:
    return (await frame.locator(selector).first.text_content()) or ""


async def until_text(frame: Any, selector: str, want: str, timeout: float = 10.0) -> float:
    started = time.monotonic()
    while time.monotonic() - started < timeout:
        try:
            if want in await frame.locator(selector).first.text_content(timeout=500):
                return time.monotonic() - started
        except Exception:  # noqa: BLE001 - re-rendering
            pass
        await asyncio.sleep(0.01)
    raise TimeoutError(f"{selector} never read {want!r}")


MEASURE = """() => {
  const style = (el) => { if (!el) return null; const s = getComputedStyle(el); const r = el.getBoundingClientRect();
    return { family: s.fontFamily, size: s.fontSize, line: s.lineHeight, color: s.color, background: s.backgroundColor,
             borderLeft: s.borderLeftColor + ' ' + s.borderLeftWidth, box: [r.x, r.y, r.width, r.height] }; };
  return { body: style(document.body), h1: style(document.querySelector('h1')), em: style(document.querySelector('em')),
           strong: style(document.querySelector('strong')), para: style(document.querySelector('strong')?.parentElement),
           paraTag: (() => { const p = document.querySelector('strong')?.parentElement; return p ? p.tagName + '.' + p.className : null; })(), commit: style(document.getElementById('ll-commit')),
           verdict: style(document.querySelector('.ll-verdict')),
           tauri: typeof window.__TAURI_INTERNALS__ !== 'undefined' || typeof window.__TAURI__ !== 'undefined' };
}"""


async def run_checks(browser: Any, session: dict[str, Any], checks: Checks, shots: Path | None) -> dict[str, Any]:
    facts: dict[str, Any] = {}
    page = await open_fixture(browser, session)
    started = time.monotonic()
    frame = await notebook_frame(page)
    facts["frame_interactive_s"] = round(time.monotonic() - started, 3)
    await page.evaluate("document.fonts.ready")
    await asyncio.sleep(1.0)
    element = page.locator("iframe.ll-nb-frame")
    checks.check("the frame is mounted at the session's URL once ready",
                 await element.get_attribute("src") == session["frame_url"]
                 and await page.locator("[data-notebook-state=ready]").count() == 1)
    checks.check("the frame is sandboxed (scripts, its own origin, forms, downloads; nothing else)",
                 await element.get_attribute("sandbox") == "allow-scripts allow-same-origin allow-forms allow-downloads")
    box = await element.bounding_box()
    facts["frame_box"] = box
    checks.check("the frame's box is the mockup's lesson frame (within 2 px)",
                 box is not None and all(abs(a - b) <= GEOMETRY_TOLERANCE_PX for a, b in zip(
                     (box["x"], box["y"], box["width"], box["height"]), FRAME_BOX, strict=True)), box)
    paper = await page.locator("[data-notebook-paper]").bounding_box()
    if paper and box:
        left, right = box["x"] - (paper["x"] + 1), (paper["x"] + paper["width"] - 1) - (box["x"] + box["width"])
        facts["margins"] = {"left": left, "right": right}
        checks.check("the margins either side of the frame are equal", abs(left - right) <= 1, facts["margins"])
    inside = await frame.evaluate(MEASURE)
    facts["inside"] = inside
    checks.check("the frame has no Tauri globals", inside["tauri"] is False)
    checks.check("the page is the workbench's paper", hexes(inside["body"]["background"]) == "#f7f5f0", inside["body"]["background"])
    checks.check("headings and prose are Literata in the paper's ink",
                 inside["h1"]["family"].startswith('"Literata') and inside["em"]["family"].startswith('"Literata')
                 and hexes(inside["h1"]["color"]) == "#1f1e1c" and hexes(inside["strong"]["color"]) == "#1f1e1c",
                 {k: (inside[k]["family"][:24], inside[k]["color"]) for k in ("h1", "em", "strong")})
    checks.check("prose is at the mockup's measured size and line (14.4 px on 24 px)",
                 inside["para"] is not None and inside["para"]["size"] == "14.4px" and inside["para"]["line"] == "24px",
                 inside["para"] and (inside["para"]["size"], inside["para"]["line"], inside["paraTag"]))
    checks.check("a commit point is a paper card with the purple voice edge",
                 hexes(inside["commit"]["background"]) == "#fdfdfc" and inside["commit"]["borderLeft"].endswith("3px")
                 and hexes(inside["commit"]["borderLeft"].rsplit(" ", 1)[0]) == "#5b4a9a", inside["commit"])
    loaded = await frame.evaluate("() => [...document.fonts].filter(f => f.status === 'loaded').map(f => f.family)")
    checks.check("the theme's faces load from the frame's own origin",
                 "Literata Variable" in loaded and "JetBrains Mono Variable" in loaded, sorted(set(loaded)))
    if shots:
        await page.screenshot(path=str(shots / "notebook__ready.png"))

    # The bridge: the four messages, then what must be refused.
    await frame.locator("#ll-square").first.click()
    await frame.evaluate("""() => { const el = document.getElementById('ll-square'); const r = document.createRange();
        r.selectNodeContents(el); const s = getSelection(); s.removeAllRanges(); s.addRange(r); }""")
    await page.keyboard.press("c")
    await frame.locator("#ll-square").first.click(button="right")
    await page.keyboard.press("Escape")
    await asyncio.sleep(0.4)
    messages = await page.evaluate("window.__notebookMessages")
    kinds = [message["ll"] for message in messages]
    companion = next((message for message in messages if message["ll"] == "companion"), None)
    checks.check("the bridge's four messages reach the workbench", {"click", "companion", "menu", "escape"} <= set(kinds), kinds)
    checks.check("a selection's text and box arrive in page coordinates, inside the frame",
                 companion is not None and companion["text"] == "square=9" and companion["rect"] is not None
                 and box is not None and box["x"] <= companion["rect"]["x"] <= box["x"] + box["width"], companion)
    before = len(messages)
    await frame.evaluate("""() => {
        parent.postMessage({ ll: 'run', code: 'evil()' }, '*');
        parent.postMessage({ ll: 'companion', text: 5, rect: null, shift: false }, '*');
        parent.postMessage({ ll: 'companion', text: 'x', rect: null, shift: false, extra: 1 }, '*');
        parent.postMessage({ ll: 'menu', text: 'x', rect: { x: 1, y: 1, width: 1 }, x: 0, y: 0 }, '*');
        parent.postMessage('{"ll":"click"}', '*');
        parent.postMessage({ ll: 'companion', text: 'y'.repeat(5000), rect: null, shift: false }, '*'); }""")
    await page.evaluate("""() => { const f = document.createElement('iframe'); f.id = 'impostor';
        f.srcdoc = "<script>parent.postMessage({ ll: 'escape' }, '*'); parent.postMessage({ ll: 'click' }, '*');<\\/script>";
        document.body.appendChild(f); }""")
    await page.evaluate("""() => window.postMessage({ ll: 'escape' }, '*')""")
    await asyncio.sleep(0.6)
    after = await page.evaluate("window.__notebookMessages")
    checks.check("forged, malformed, oversized, wrong-origin and same-page messages are refused", len(after) == before,
                 after[before:])
    await frame.evaluate("() => parent.postMessage({ ll: 'companion', text: 'from notebook code', rect: null, shift: false }, '*')")
    await asyncio.sleep(0.3)
    last = (await page.evaluate("window.__notebookMessages"))[-1]
    checks.check("a well-formed message from notebook code is accepted as untrusted text (it shares the frame's origin)",
                 last == {"ll": "companion", "text": "from notebook code", "rect": None, "shift": False}, last)

    # An edit round trip, then a reload keeping the kernel without marimo's banner.
    thumb = frame.locator("[role=slider]").first
    await thumb.focus()
    t0 = time.monotonic()
    await thumb.press("ArrowRight")
    await until_text(frame, "#ll-square", "square=16")
    facts["edit_round_trip_ms"] = round(1000 * (time.monotonic() - t0), 1)
    checks.check("an edit in the frame reaches the kernel and back", facts["edit_round_trip_ms"] < 5000, facts["edit_round_trip_ms"])
    await page.evaluate("() => { const f = document.querySelector('iframe.ll-nb-frame'); f.src = f.src; }")
    await asyncio.sleep(0.5)
    frame = await notebook_frame(page)
    await until_text(frame, "#ll-square", "square=16")
    await asyncio.sleep(1.5)
    body = await frame.locator("body").inner_text()
    checks.check("a reloaded frame keeps its kernel and shows no Reconnected banner", "Reconnected" not in body and "square=16" in body)
    await page.close()

    # The honest states, the paused frame and the preview.
    for state, words, action in (("starting", "starting the notebook", None), ("restarting", "starting it again", None),
                                 ("stopped", "paused while no window showed it", "resume"),
                                 ("failed", "couldn't run", "try again"), ("unavailable", "bubblewrap", "try again")):
        page = await open_fixture(browser, session, f"&nbstate={state}")
        await page.wait_for_selector(f"[data-notebook-state={state if state != 'unavailable' else 'unavailable'}]", timeout=10000)
        line = await page.locator(".ll-nb-status").inner_text()
        family = await page.locator(".ll-nb-status").evaluate("el => getComputedStyle(el).fontFamily")
        button = await page.locator(".ll-nb-status button").count()
        checks.check(f"the {state} state says so in one line in the interface face",
                     words in line and family.startswith('"JetBrains Mono') and (button == 1) == (action is not None),
                     {"line": line, "family": family[:30]})
        if shots:
            await page.screenshot(path=str(shots / f"notebook__{state}.png"), clip={"x": 838, "y": 160, "width": 560, "height": 300})
        await page.close()
    page = await open_fixture(browser, session)
    await notebook_frame(page)
    await page.evaluate("window.__notebookPause(true)")
    await asyncio.sleep(0.3)
    inert = await page.locator("iframe.ll-nb-frame").evaluate("el => [el.hasAttribute('inert'), el.tabIndex]")
    checks.check("a paused window's frame stays (its server too) but takes no input or focus", inert == [True, -1], inert)
    await page.evaluate("window.__notebookPause(false)")
    await asyncio.sleep(0.3)
    inert = await page.locator("iframe.ll-nb-frame").evaluate("el => [el.hasAttribute('inert'), el.tabIndex]")
    checks.check("back on screen, the same frame takes input again", inert == [False, 0], inert)
    await page.close()
    page = await open_fixture(browser, session, "&nbpreview=1")
    await page.wait_for_selector("[data-notebook-placeholder]")
    checks.check("an overview card shows a placeholder, never a second live frame",
                 await page.locator("iframe").count() == 0 and "notebook" in await page.locator("[data-notebook-placeholder]").inner_text())
    await page.close()
    return facts


#: The pad cells fixture's cells (project-authored): a control with a widget, and a cell computed from it.
PAD_CELLS = [
    {"blockId": "fx_cell_temp", "code": "import marimo as mo\nfrom wigglystuff import Slider2D\n"
     "t = mo.ui.slider(1, 20, value=6, label='temperature x10')\nw = mo.ui.anywidget(Slider2D())\nmo.vstack([t, w])"},
    {"blockId": "fx_cell_soft", "code": "import math\nlogits = [2.0, 1.0, 0.1]\nT = t.value / 10\n"
     "ps = [math.exp(z / T) for z in logits]\nmo.md(f\"<span id='ll-soft'>p={ps[0] / sum(ps):.3f}</span>\")"},
]
EDITED_SOFT = ("import math\nlogits = [2.0, 1.0, 0.1]\nT = t.value / 10\nps = [math.exp(z / T) for z in logits]\n"
               "mo.md(f\"<span id='ll-soft'>q={ps[0] / sum(ps):.2f}</span>\")")


async def pad_frame(page: Page, want: str, timeout: float = 40.0) -> Any:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for frame in page.frames:
            if "127.0.0.1" in frame.url:
                try:
                    text = await frame.locator("#ll-soft").first.text_content(timeout=300)
                    if text and want in text:
                        return frame
                except Exception:  # noqa: BLE001 - still loading
                    pass
        await asyncio.sleep(0.1)
    raise TimeoutError(f"the pad's frame never read {want!r}")


async def run_pad_cells(browser: Any, runtime: Any, checks: Checks, shots: Path | None) -> dict[str, Any]:
    """A pad holding two marimo cells and a widget, run in a real sandboxed session through the page's RPCs."""

    import hashlib

    from learnloop.notebook_runtime import adapter
    from learnloop.notebook_runtime.sandbox import Limits
    from learnloop_sidecar.dto import Verbatim, versioned

    facts: dict[str, Any] = {}
    page = await browser.new_page(viewport=VIEWPORT)
    await page.route("**/*", serve_dist)
    await page.add_init_script("window.__notebookHarness = " + json.dumps({"frameUrl": "", "sessionId": "", "padCells": PAD_CELLS}) + ";")

    async def nb_rpc(command: str, data: dict[str, Any]) -> Any:
        blocks = await page.evaluate("() => window.__padCellsServer.padGet('fx_pad_cells').blocks.map(b => [b.blockId, b.kind, b.bodyMd])")
        cells = [(adapter.cell_name(block_id), code) for block_id, kind, code in blocks if kind == "cell"]
        names = {block_id: adapter.cell_name(block_id) for block_id, kind, _code in blocks if kind == "cell"}

        def work() -> dict[str, Any]:
            if command == "notebook_open":
                view = runtime.open(vault_key="harness", owner=data["owner"], source=adapter.notebook_from_cells(cells).encode(),
                                    view=data.get("view", "app"), limits=Limits(memory_mib=2048, scratch_mib=256), idle_minutes=10,
                                    max_sessions=4, revision=hashlib.sha256("\n".join(n for n, _c in cells).encode()).hexdigest())
                view = {**view, "pad_cells": names}
            elif command == "notebook_status":
                view = runtime.status(vault_key="harness", session_id=data["sessionId"])
            else:
                view = runtime.run_cells(vault_key="harness", session_id=data["sessionId"],
                                         cells=[(cell["name"], cell["code"]) for cell in data["cells"]])
            for key in ("cell_runs", "pad_cells"):
                if key in view:
                    view[key] = Verbatim(view[key])
            return versioned(view)

        return await asyncio.get_running_loop().run_in_executor(None, work)

    await page.expose_function("__nbRpc", nb_rpc)
    await page.goto(f"{ORIGIN}/desk-harness.html?padcells=1")
    await page.wait_for_selector("[data-cell-block]")
    cells = page.locator("[data-cell-block]")
    states = await page.locator("[data-cell-state]").all_inner_texts()
    checks.check("a pad's cells show their header and code, and no kernel before ⇧↵",
                 await cells.count() == 2 and states == ["kernel not started"] * 2
                 and await page.locator("[data-cell-group]").count() == 0
                 and "runs when you press ⇧↵" in await cells.first.inner_text(), states)
    started = time.monotonic()
    await page.locator("[data-cell-block='fx_cell_temp'] .run").click()
    frame = await pad_frame(page, "p=")
    facts["first_run_to_output_s"] = round(time.monotonic() - started, 3)
    group = page.locator("[data-cell-group]")
    checks.check("the first ⇧↵ starts the pad's kernel: one framed group, under the pad's last cell",
                 await group.count() == 1
                 and await group.evaluate("el => el.closest('[data-cell-block]').getAttribute('data-cell-block')") == "fx_cell_soft",
                 facts["first_run_to_output_s"])
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        states = await page.locator("[data-cell-state]").all_inner_texts()
        if all(state.startswith("ran in") for state in states):
            break
        await asyncio.sleep(0.25)
    checks.check("each cell's header reads its own run (ran in N ms)", all(state.startswith("ran in") for state in states), states)
    def pad_session() -> Any:
        return next(each for each in runtime.sessions() if each.owner == "pad:fx_pad_cells")

    session = pad_session()
    sid, pid = session.session_id, session.process.pid
    before = await text_in(frame, "#ll-soft")
    thumb = frame.locator("[role=slider]").first
    await thumb.focus()
    await thumb.press("ArrowRight")
    deadline = time.monotonic() + 10
    after = before
    while time.monotonic() < deadline and after == before:
        after = await text_in(frame, "#ll-soft")
        await asyncio.sleep(0.05)
    widget = await frame.evaluate("""() => [...document.querySelectorAll('*')].filter(el => el.shadowRoot)
        .map(el => el.shadowRoot.textContent).join(' ')""")
    checks.check("the widgets are live in the pad's frame (a control reruns the cell that reads it; the anywidget renders)",
                 after != before and "X:" in widget, {"before": before, "after": after, "widget": widget[:80]})
    if shots:
        await page.screenshot(path=str(shots / "padcells__ran.png"))
    # Edit the second cell and run it: it runs in the live kernel.
    await page.locator("[data-cell-block='fx_cell_soft'] .ll-cell-code").click()
    area = page.locator("[data-cell-block='fx_cell_soft'] textarea")
    await area.fill(EDITED_SOFT)
    t0 = time.monotonic()
    await area.press("Shift+Enter")
    await pad_frame(page, "q=")
    facts["edit_to_output_ms"] = round(1000 * (time.monotonic() - t0), 1)
    pads = [each for each in runtime.sessions() if each.owner.startswith("pad:")]
    checks.check("an edited cell runs in the live kernel (same session, same process)",
                 pad_session().session_id == sid and pad_session().process.pid == pid and len(pads) == 1,
                 facts["edit_to_output_ms"])
    await page.keyboard.press("Escape")
    stored = None
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline and stored != EDITED_SOFT:
        stored = await page.evaluate("() => window.__padCellsServer.padGet('fx_pad_cells').blocks.find(b => b.blockId === 'fx_cell_soft').bodyMd")
        await asyncio.sleep(0.2)
    checks.check("the edit is the pad's (an edit_block through the pad's write protocol)", stored == EDITED_SOFT)
    # Move the pad's window: it remounts, its frame reattaches to the same kernel.
    await page.evaluate("window.__padCellsMove()")
    await page.wait_for_selector("[data-padcells-side=right] [data-cell-group]", timeout=15000)
    moved = await pad_frame(page, "q=")
    checks.check("moving the pad keeps its kernel (the same session and process; its output kept)",
                 pad_session().session_id == sid and pad_session().process.pid == pid
                 and "q=" in await text_in(moved, "#ll-soft"))
    if shots:
        await page.screenshot(path=str(shots / "padcells__moved.png"))
    await page.close()
    return facts


def sample_lesson_frame(png: Path) -> dict[str, Any]:
    """The lesson frame measured on a screenshot: its 1 px rule's box, the margins round it, the colours inside."""

    from PIL import Image

    image = Image.open(png).convert("RGB")

    def hexed(xy: tuple[int, int]) -> str:
        return "#%02x%02x%02x" % image.getpixel(xy)

    rule = (0xdc, 0xd7, 0xcc)
    row = 500
    xs = [x for x in range(840, 1400) if image.getpixel((x, row)) == rule]
    col = 1000
    ys = [y for y in range(160, 880) if image.getpixel((col, y)) == rule]
    out: dict[str, Any] = {"rule_x": xs[:1] + xs[-1:], "rule_top_y": ys[:1]}
    if len(xs) >= 2:
        left, right = xs[0], xs[-1]
        paper_left = next((x for x in range(left - 1, 830, -1) if image.getpixel((x, row)) != (0xfd, 0xfd, 0xfc)), None)
        paper_right = next((x for x in range(right + 1, 1410) if image.getpixel((x, row)) != (0xfd, 0xfd, 0xfc)), None)
        out.update(frame_left=left, frame_right=right, frame_width=right - left + 1,
                   margin_left=(left - paper_left - 1) if paper_left else None,
                   margin_right=(paper_right - right - 1) if paper_right else None,
                   page=hexed((left + 3, row)), surround=hexed((left - 4, row)))
        # The notebook's content column: the outermost card edges inside the frame (a card's rule, or a commit
        # point's purple voice edge), on any row.
        edges = {(0xe3, 0xe0, 0xd8), (0x5b, 0x4a, 0x9a)}
        inner = [x for y in range(ys[0] + 2 if ys else 300, min(ys[0] + 520, image.height - 1) if ys else 800, 2)
                 for x in range(left + 1, right) if image.getpixel((x, y)) in edges]
        if inner:
            out.update(content_margin_left=min(inner) - left - 1, content_margin_right=right - max(inner) - 1)
    return out


async def compare_reference(browser: Any, session: dict[str, Any], ref: Path) -> dict[str, Any]:
    stem = "arxiv_v2__tabs_distance_pad_3__design"
    reference_png = ref / f"{stem}.png"
    if not reference_png.exists():
        return {"status": "no reference capture", "file": reference_png.name}
    out = ref / "compare"
    out.mkdir(parents=True, exist_ok=True, mode=0o700)
    page = await open_fixture(browser, session)
    await notebook_frame(page)
    await page.evaluate("document.fonts.ready")
    await asyncio.sleep(1.5)
    harness_png = out / f"notebook__{stem}__harness.png"
    await page.screenshot(path=str(harness_png))
    await page.close()
    mock, app = sample_lesson_frame(reference_png), sample_lesson_frame(harness_png)
    differences = []
    for key in ("frame_left", "frame_right", "frame_width", "margin_left", "margin_right", "content_margin_left",
                "content_margin_right"):
        if mock.get(key) is None or app.get(key) is None or abs(mock[key] - app[key]) > GEOMETRY_TOLERANCE_PX:
            differences.append({"prop": key, "mockup": mock.get(key), "app": app.get(key)})
    for key in ("page", "surround"):
        if mock.get(key) != app.get(key):
            differences.append({"prop": key, "mockup": mock.get(key), "app": app.get(key)})
    if (mock.get("rule_top_y") or [None])[0] != (app.get("rule_top_y") or [None])[0]:
        differences.append({"prop": "frame_top", "mockup": mock.get("rule_top_y"), "app": app.get("rule_top_y")})
    result = {"status": "compared", "state": "tabs=distance,pad=3", "viewport": "design", "mockup": mock, "app": app,
              "differences": differences}
    (out / "notebook__result.json").write_text(json.dumps(result, indent=1))
    return result


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ref", type=Path, default=None, help="the private reference directory")
    parser.add_argument("--shots", type=Path, default=None)
    args = parser.parse_args()
    if not DIST.exists():
        print("build the harness page first: npx vite build --config vite.desks.config.mjs", file=sys.stderr)
        return 2
    sys.path.insert(0, str(ROOT / "src"))
    from learnloop.notebook_runtime.runtime import NotebookRuntime
    from learnloop.notebook_runtime.sandbox import Limits, missing_requirements, scope_available
    from learnloop.notebook_runtime.supervisor import SandboxBackend

    problems = missing_requirements()
    if problems:
        print("the notebook runtime cannot run here: " + "; ".join(problems), file=sys.stderr)
        return 2
    if args.shots:
        args.shots.mkdir(parents=True, exist_ok=True)
    base = Path(tempfile.mkdtemp(prefix="nbh-"))
    # uv's `--with` runs this script on a throwaway environment; the server runs on the project's own.
    project_python = ROOT / ".venv" / "bin" / "python"
    runtime = NotebookRuntime(base_dir=base, backend=SandboxBackend(
        scoped=scope_available(), python=str(project_python) if project_python.exists() else None))
    checks = Checks()
    try:
        view = runtime.open(vault_key="harness", owner="lesson:fx_lesson", source=LESSON.encode(), view="app",
                            limits=Limits(memory_mib=2048, scratch_mib=256), idle_minutes=10, max_sessions=2)
        deadline = time.monotonic() + 60
        while (view := runtime.status(vault_key="harness", session_id=view["session_id"]))["state"] != "ready":
            if time.monotonic() > deadline or view["state"] == "failed":
                print(f"the session did not start: {view}", file=sys.stderr)
                return 1
            time.sleep(0.05)
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True, args=CHROMIUM_ARGS)
            facts = await run_checks(browser, view, checks, args.shots)
            facts["pad_cells"] = await run_pad_cells(browser, runtime, checks, args.shots)
            if args.ref:
                facts["reference"] = await compare_reference(browser, view, args.ref)
                print("reference:", json.dumps(facts["reference"].get("differences"), default=str))
            await browser.close()
        print(json.dumps({key: value for key, value in facts.items() if key != "inside"}, default=str))
        print(f"{len(checks.rows) - checks.failed} of {len(checks.rows)} checks passed")
        return 0 if checks.failed == 0 else 1
    finally:
        runtime.close()
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
