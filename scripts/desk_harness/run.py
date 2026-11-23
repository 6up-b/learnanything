"""The desks' real-webview harness (docs/specs/spec_reader_workbench_v2.md §18.3).

Builds nothing: run it after building the harness page once,

    cd apps/learnloop-tauri && npx vite build --config vite.desks.config.mjs

then, from the repository root (Playwright is not a project dependency; uv fetches it for this run):

    uv run --no-project --with playwright==1.65.2 python scripts/desk_harness/run.py [--shots DIR]

It serves the built page on 127.0.0.1, drives it in headless Chromium (no window opens), and checks
what jsdom cannot: geometry (every window fills its slot's height, focus mode is the whole viewport,
leaving it restores every rect), two players on one desk keeping their own clocks (real iframes,
`event.source`), a hidden desk's player paused, a duplicate open focusing the existing window, a
preview logging no reading activity, which-key on an Alt hold, close and undo, and the writes the
outbox sent. YouTube is never contacted: its embed URL is answered by a local stub player, and every
other outside request is refused. WebKit is the target engine (WebKitGTK in the packaged app); the
Playwright WebKit build is not installed here, so this harness runs Chromium only.

Exit status: 0 when every check passes, 1 otherwise. Screenshots go to --shots when given.
"""

from __future__ import annotations

import argparse
import asyncio
import functools
import http.server
import json
import threading
from pathlib import Path
from typing import Any

from playwright.async_api import Page, Route, async_playwright

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "apps" / "learnloop-tauri" / "dist-desk-harness"
VIEWPORT = {"width": 1600, "height": 960}

# A stand-in for the YouTube widget: after the page's "listening" handshake it reports a time of its
# own (from the URL's `t` parameter) as the real widget does, and records every command it is sent.
STUB_PLAYER = """<!doctype html><html><body style="margin:0;background:#111;color:#888;font:12px monospace">
<div id="s">stub player</div><script>
const time = Number(new URLSearchParams(location.search).get("t") || "0");
window.commands = [];
window.addEventListener("message", (event) => {
  let data; try { data = JSON.parse(event.data); } catch { return; }
  if (data.event === "listening") {
    parent.postMessage(JSON.stringify({ event: "infoDelivery", info: { currentTime: time, playerState: 2 } }), "*");
  }
  if (data.event === "command") {
    window.commands.push(data.func);
    document.getElementById("s").textContent = "stub player: " + window.commands.join(",");
    parent.postMessage(JSON.stringify({ event: "infoDelivery", info: { currentTime: time, playerState: data.func === "playVideo" ? 1 : 2 } }), "*");
  }
});
</script></body></html>"""

# The two fixture videos report different times, so each panel's clock shows whose messages it took.
STUB_TIMES = {"fxSoftmax01": 75, "fxMasks0002": 42}


class Results:
    def __init__(self) -> None:
        self.rows: list[tuple[str, bool, str]] = []

    def check(self, name: str, ok: bool, detail: Any = "") -> None:
        self.rows.append((name, bool(ok), json.dumps(detail, default=str)[:300] if detail != "" else ""))

    @property
    def ok(self) -> bool:
        return all(passed for _name, passed, _detail in self.rows)


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return


def serve(directory: Path) -> tuple[http.server.ThreadingHTTPServer, int]:
    handler = functools.partial(QuietHandler, directory=str(directory))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, server.server_address[1]


OUTSIDE: list[str] = []


async def route_outside(route: Route) -> None:
    url = route.request.url
    OUTSIDE.append(url)
    if url.startswith("https://www.youtube-nocookie.com/embed/"):
        video = url.split("/embed/")[1].split("?")[0]
        await route.fulfill(status=200, content_type="text/html", body=STUB_PLAYER.replace(
            'get("t") || "0"', f'get("t") || "{STUB_TIMES.get(video, 0)}"'))
        return
    await route.abort()


async def windows(page: Page) -> list[dict[str, Any]]:
    return await page.evaluate("""() => [...document.querySelectorAll('[data-desk-window]')].map((pane) => {
      const slot = pane.closest('.desk-window');
      const body = pane.querySelector('[data-desk-pane-body]');
      const r = slot.getBoundingClientRect(), p = pane.getBoundingClientRect(), b = body.getBoundingClientRect();
      return { id: pane.getAttribute('data-desk-window'), state: pane.getAttribute('data-window-state'), kind: pane.getAttribute('data-window-kind'),
        slot: { x: r.x, y: r.y, w: r.width, h: r.height }, pane: { y: p.y, h: p.height }, body: { y: b.y, h: b.height },
        mask: getComputedStyle(slot).maskImage || getComputedStyle(slot).webkitMaskImage || 'none' };
    })""")


async def stage_box(page: Page) -> dict[str, float]:
    return await page.evaluate("""() => { const r = document.querySelector('[data-desk-stage]').getBoundingClientRect();
      return { x: r.x, y: r.y, w: r.width, h: r.height }; }""")


async def calls(page: Page, command: str) -> list[dict[str, Any]]:
    return await page.evaluate("(command) => window.__deskHarness.calls.filter((c) => c.command === command)", command)


async def settle(page: Page, ms: int = 700) -> None:
    await page.wait_for_timeout(ms)


async def shot(page: Page, shots: Path | None, name: str) -> None:
    if shots is not None:
        await page.screenshot(path=str(shots / f"{name}.png"))


async def run_desks(page: Page, base: str, results: Results, shots: Path | None) -> None:
    await page.goto(f"{base}/desk-harness.html")
    await page.wait_for_selector("[data-desk-window]")
    await settle(page, 1500)
    await shot(page, shots, "desk-0")

    stage = await stage_box(page)
    current = [w for w in await windows(page) if w["state"] in ("active", "visible", "offscreen")]
    results.check("windows render on the first desk", len(current) >= 5, [w["id"] for w in current])
    fills = [abs(w["slot"]["h"] - (stage["h"] - 16)) <= 0.5 and abs((w["body"]["y"] + w["body"]["h"]) - (w["slot"]["y"] + w["slot"]["h"])) <= 1
             for w in current]
    results.check("every window fills its slot's height (the body reaches the slot's bottom)", all(fills),
                  [(w["id"], round(w["slot"]["h"]), round(w["body"]["y"] + w["body"]["h"] - w["slot"]["y"] - w["slot"]["h"])) for w in current])
    in_view = [w["id"] for w in current if w["state"] in ("active", "visible")]
    results.check("two windows in view, the book active", in_view[:1] == ["fx_w_book"] and len(in_view) == 2, in_view)
    slivers = await page.locator(".desk-sliver").count()
    results.check("a sliver for the off-screen neighbour", slivers == 1, slivers)

    # Which-key: Alt held 400 ms shows it; releasing hides it.
    await page.keyboard.down("Alt")
    await page.wait_for_timeout(480)
    shown = await page.locator(".desk-whichkey").count()
    await page.keyboard.up("Alt")
    await settle(page, 150)
    hidden = await page.locator(".desk-whichkey").count()
    results.check("which-key shows on an Alt hold and hides on release", shown == 1 and hidden == 0, [shown, hidden])

    # #focus=3: alt+l three times brings the guide panel in view; slivers both sides; the soft crop.
    for _ in range(3):
        await page.keyboard.press("Alt+l")
        await settle(page, 250)
    await settle(page, 700)
    now = await windows(page)
    active = [w["id"] for w in now if w["state"] == "active"]
    results.check("alt+l moves the focus along the strip (#focus=3)", active == ["fx_w_guide"], active)
    results.check("the guide panel hosts the book's rail", await page.locator('[data-rail-host="guide"] [role="complementary"]').count() == 1)
    results.check("slivers on both sides once the strip has moved", await page.locator(".desk-sliver").count() == 2)
    await shot(page, shots, "focus-3")

    # #move: alt+] moves the focused window one slot right.
    order_before = await page.evaluate("() => [...document.querySelectorAll('[data-shelf-window]')].map((e) => e.dataset.shelfWindow)")
    await page.keyboard.press("Alt+BracketRight")
    await settle(page, 700)
    order_after = await page.evaluate("() => [...document.querySelectorAll('[data-shelf-window]')].map((e) => e.dataset.shelfWindow)")
    moved = order_before.index("fx_w_guide") + 1 == order_after.index("fx_w_guide")
    results.check("alt+] moves the focused window one slot (#move)", moved, [order_before, order_after])
    await shot(page, shots, "move")

    # Back to the book; duplicate-source: opening the book beside focuses the window already open.
    for _ in range(6):
        await page.keyboard.press("Alt+h")
        await settle(page, 120)
    await settle(page, 600)
    before = len(await windows(page))
    await page.get_by_role("button", name="+ open beside").click()
    await page.get_by_role("dialog", name="open beside").get_by_role("button", name="Softmax, a short book").click()
    await settle(page, 700)
    after = await windows(page)
    results.check("opening a source already on the desk opens no second window", len(after) == before, [before, len(after)])
    results.check("…and focuses the window that shows it", [w["id"] for w in after if w["state"] == "active"] == ["fx_w_book"])

    # Two players: the video window's frame reports its own time; press space on it to play.
    await page.keyboard.press("Alt+l")
    await settle(page, 1200)
    clock_a = await page.locator('[data-desk-window="fx_w_video"]').inner_text()
    results.check("the first player shows its own time", "1:15" in clock_a, clock_a[:120])
    await page.keyboard.press("Space")
    await settle(page, 400)
    frame_a = page.frame_locator('[data-desk-window="fx_w_video"] iframe')
    commands_a = await frame_a.locator("#s").inner_text()
    results.check("space plays the focused video", "playVideo" in commands_a, commands_a)

    # #desk=1: the attention desk; the first desk's windows are hidden and its player paused.
    await page.get_by_role("button", name="attention", exact=True).click()
    await settle(page, 1500)
    states = {w["id"]: w["state"] for w in await windows(page)}
    results.check("switching desks hides the other desk's windows (#desk=1)",
                  states.get("fx_w_book") == "hidden" and states.get("fx_w_video2") == "active", states)
    commands_after = await frame_a.locator("#s").inner_text()
    results.check("a hidden desk's player is paused", commands_after.endswith("pauseVideo"), commands_after)
    clock_b = await page.locator('[data-desk-window="fx_w_video2"]').inner_text()
    clock_a_again = await page.locator('[data-desk-window="fx_w_video"]').inner_text()
    results.check("two players each keep their own clock (event.source)", "0:42" in clock_b and "1:15" in clock_a_again and "1:15" not in clock_b,
                  [clock_a_again[:80], clock_b[:80]])
    await shot(page, shots, "desk-1")

    # #zoom=after: focus mode is the whole viewport; = zooms; esc restores every rect.
    rects_before = {w["id"]: w["slot"] for w in await windows(page) if w["state"] in ("active", "visible")}
    await page.keyboard.press("Alt+Enter")
    await settle(page, 700)
    full = [w for w in await windows(page) if w["state"] == "active"][0]
    viewport_ok = abs(full["slot"]["x"]) <= 0.5 and abs(full["slot"]["y"]) <= 0.5 and abs(full["slot"]["w"] - VIEWPORT["width"]) <= 0.5 and abs(full["slot"]["h"] - VIEWPORT["height"]) <= 0.5
    results.check("focus mode is truly full screen (#zoom=after)", viewport_ok, full["slot"])
    await page.keyboard.press("Equal")
    await settle(page, 200)
    badge = await page.locator(".desk-zoom-badge").inner_text()
    results.check("= zooms the document in focus mode", badge.startswith("110%"), badge)
    await shot(page, shots, "zoom-after")
    await page.keyboard.press("Digit0")
    await page.keyboard.press("Escape")
    await settle(page, 900)
    rects_after = {w["id"]: w["slot"] for w in await windows(page) if w["state"] in ("active", "visible")}
    same = rects_before.keys() == rects_after.keys() and all(
        all(abs(rects_before[k][dim] - rects_after[k][dim]) <= 1 for dim in ("x", "y", "w", "h")) for k in rects_before)
    results.check("leaving focus mode restores every window's rect within 1 px", same, [rects_before, rects_after])

    # Pairs: alt+, stacks the two windows top and bottom; alt+. gives one back its slot.
    await page.keyboard.press("Alt+Comma")
    await settle(page, 700)
    pair = [w for w in await windows(page) if w["id"] in ("fx_w_video2", "fx_w_paper2")]
    stacked = len(pair) == 2 and abs(pair[0]["slot"]["x"] - pair[1]["slot"]["x"]) < 0.5 and pair[0]["pane"]["y"] != pair[1]["pane"]["y"]
    halves = stacked and abs(pair[0]["pane"]["h"] - pair[1]["pane"]["h"]) <= 1
    results.check("alt+, stacks two windows in one slot, equal heights", stacked and halves, pair)
    await page.keyboard.press("Alt+Comma")
    await settle(page, 300)
    toast = await page.locator(".desk-toast").inner_text() if await page.locator(".desk-toast").count() else ""
    results.check("a third window in a slot is refused with a toast", "at most two" in toast or "nothing to the right" in toast, toast)
    await page.keyboard.press("Alt+Period")
    await settle(page, 700)
    results.check("alt+. gives the window its own slot", len({round(w["slot"]["x"]) for w in await windows(page) if w["id"] in ("fx_w_video2", "fx_w_paper2")}) == 2)

    # Close and undo.
    count = len([w for w in await windows(page) if w["state"] != "hidden"])
    await page.keyboard.press("Alt+w")
    await settle(page, 500)
    closed = len([w for w in await windows(page) if w["state"] != "hidden"])
    undo = page.locator(".desk-shelf .undo")
    has_undo = await undo.count() == 1
    if has_undo:
        await undo.click()
        await settle(page, 500)
    reopened = len([w for w in await windows(page) if w["state"] != "hidden"])
    results.check("alt+w closes, and the shelf's undo reopens it", closed == count - 1 and has_undo and reopened == count, [count, closed, reopened])

    # The writes: one sequence for this client, in order, and the server's slots equal the screen's.
    await settle(page, 600)
    sent = await page.evaluate("() => window.__deskHarness.server.batches.map((b) => [b.clientId, b.seq, b.ops.length])")
    seqs = [row[1] for row in sent]
    results.check("the outbox sent numbered batches, in order, from one client", seqs == list(range(1, len(seqs) + 1)) and len({row[0] for row in sent}) == 1, sent)
    server_slots = await page.evaluate("() => window.__deskHarness.server.state().desks.find((d) => d.deskId === 'fx_desk_attention').slots.map((s) => s.windows.map((w) => w.windowId))")
    screen_slots = await page.evaluate("""() => { const out = {}; for (const el of document.querySelectorAll('[data-desk-slot^="fx_desk_attention:"]')) {
      out[el.dataset.deskSlot.split(':')[1]] = [...el.querySelectorAll('[data-desk-window]')].map((p) => p.dataset.deskWindow); }
      return Object.keys(out).sort().map((k) => out[k]); }""")
    results.check("the server's slots equal the screen's", server_slots == screen_slots, [server_slots, screen_slots])
    fonts = await page.evaluate("""async () => {
      const families = ["Inter Variable", "Literata Variable", "Source Serif 4 Variable", "JetBrains Mono Variable", "Caveat Variable"];
      await Promise.all(families.map((family) => document.fonts.load(`16px "${family}"`)));
      return families.filter((family) => !document.fonts.check(`16px "${family}"`));
    }""")
    results.check("the five desk fonts load from the app itself", fonts == [], fonts)
    errors = await page.evaluate("() => window.__deskHarnessErrors")
    results.check("no error reached the shell's error line", errors == [], errors)


async def run_preview(page: Page, base: str, results: Results) -> None:
    """A preview (a card or miniature) logs no reading activity; the same window active does (control)."""
    for state, expect_activity in (("preview", False), ("active", True)):
        await page.goto(f"{base}/desk-harness.html?preview={state}")
        await page.wait_for_selector("[data-preview-card]")
        await settle(page, 1200)
        await page.mouse.move(200, 200)
        await page.mouse.wheel(0, 600)
        await settle(page, 2500)
        logged = await calls(page, "reader_log_activity")
        kinds = sorted({event.get("kind") for call in logged for event in call["input"].get("events", [])})
        progress = await calls(page, "reader_note_reading_progress")
        if expect_activity:
            results.check("control: the same window, active, opens a reading visit", "reader_view_opened" in kinds, kinds)
        else:
            results.check("a preview logs no reading activity (no visit, no progress)", kinds == [] and progress == [], [kinds, len(progress)])


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--shots", type=Path, default=None)
    args = parser.parse_args()
    if not (DIST / "desk-harness.html").exists():
        print("Build the harness page first: cd apps/learnloop-tauri && npx vite build --config vite.desks.config.mjs")
        return 2
    if args.shots is not None:
        args.shots.mkdir(parents=True, exist_ok=True)
    server, port = serve(DIST)
    base = f"http://127.0.0.1:{port}"
    results = Results()
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            for runner in ("desks", "preview"):
                context = await browser.new_context(viewport=VIEWPORT)
                await context.route(lambda url: not url.startswith(base), route_outside)
                page = await context.new_page()
                try:
                    if runner == "desks":
                        await run_desks(page, base, results, args.shots)
                    else:
                        await run_preview(page, base, results)
                except Exception as error:  # noqa: BLE001 - a broken step is a failed check, and the report still prints
                    results.check(f"the {runner} run reached its end", False, str(error).splitlines()[0])
                await context.close()
            await browser.close()
    finally:
        server.shutdown()
    asked = sorted({url.split("/")[2] for url in OUTSIDE})
    results.check("no request left the page but the stubbed player's", asked in ([], ["www.youtube-nocookie.com"]), asked)
    for name, passed, detail in results.rows:
        print(f"{'PASS' if passed else 'FAIL'}  {name}" + (f"  {detail}" if not passed and detail else ""))
    print(f"{sum(1 for row in results.rows if row[1])} passed, {sum(1 for row in results.rows if not row[1])} failed")
    return 0 if results.ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
