"""The desks' real-webview harness (docs/specs/spec_reader_workbench_v2.md §18.3).

Builds nothing: run it after building the harness page once,

    cd apps/learnloop-tauri && npx vite build --config vite.desks.config.mjs

then, from the repository root (Playwright is not a project dependency; uv fetches it for this run):

    uv run --no-project --with playwright==1.65.2 --with pillow==11.3.0 python scripts/desk_harness/run.py [--shots DIR]

It serves the built page on 127.0.0.1, drives it in headless Chromium (no window opens), and checks
what jsdom cannot: geometry (every window fills its slot's height, focus mode is the whole viewport,
leaving it restores every rect), two players on one desk keeping their own clocks (real iframes,
`event.source`), a hidden desk's player paused, a duplicate open focusing the existing window, a
preview logging no reading activity, which-key on an Alt hold, close and undo, and the writes the
outbox sent. YouTube is never contacted: its embed URL is answered by a local stub player, and every
other outside request is refused. WebKit is the target engine (WebKitGTK in the packaged app); the
Playwright WebKit build is not installed here, so this harness runs Chromium only.

The overview's run (RD2) adds: the zoom's last frame against the committed overview, and back, as
screenshots compared under a documented tolerance (a pixel counts as changed when a channel differs by
more than PIXEL_THRESHOLD; at most MAX_CHANGED_SHARE of the stage may change); the four ways back
restoring the reading layout within 1 px; every navigation path keeping the selection inside the view;
the alt + wheel zoom and ctrl+drag on the background; a zoom's frames writing only transforms,
opacities, visibility and the selection's edge, inserting no element and touching no custom property;
previews logging nothing; the laptop rail. It records the zoom's frame times as information (the owner
deferred the frame budget). Pillow compares the screenshots (`--with pillow`).

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

# The screenshot tolerance for the commit-identity check (spec §6.3, §18.3): rasterising text and 1 px
# borders under a transform and after a layout differs a little; anything larger is a different frame.
PIXEL_THRESHOLD = 24
MAX_CHANGED_SHARE = 0.001

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

    # Two players: the video window's frame reports its own time; press space on it to play. The clocks are
    # read from the DOM's text: a paused window's content is not rendered (content-visibility), so it has
    # no rendered text to read.
    await page.keyboard.press("Alt+l")
    await settle(page, 1200)
    clock_a = await page.locator('[data-desk-window="fx_w_video"]').text_content() or ''
    results.check("the first player shows its own time", "1:15" in clock_a, clock_a[:120])
    await page.keyboard.press("Space")
    await settle(page, 400)
    frame_a = page.frame_locator('[data-desk-window="fx_w_video"] iframe')
    commands_a = await frame_a.locator("#s").inner_text()
    results.check("space plays the focused video", "playVideo" in commands_a, commands_a)

    # A field focused in the active window, then alt+j to the next desk: the typing goes nowhere on the
    # hidden desk, the focus is in the new active window, and the hidden desk's windows are inert.
    await page.evaluate("""() => { const body = document.querySelector('[data-desk-window="fx_w_video"] [data-desk-pane-body]');
      const field = document.createElement('input'); field.id = 'harness-draft'; body.prepend(field); field.focus(); }""")
    await page.keyboard.press("Alt+j")
    await settle(page, 900)
    await page.keyboard.type("zz")
    typed = await page.evaluate("""() => ({ value: document.getElementById('harness-draft').value,
      owner: document.activeElement?.closest('[data-desk-window]')?.getAttribute('data-desk-window') ?? null,
      inert: document.querySelector('[data-desk-window="fx_w_book"]').inert })""")
    results.check("a field on a desk left behind takes no typing; the focus follows the active window",
                  typed == {"value": "", "owner": "fx_w_video2", "inert": True}, typed)
    await page.evaluate("() => document.getElementById('harness-draft').remove()")

    # #desk=1: the attention desk; the first desk's windows are hidden and its player paused.
    await page.get_by_role("button", name="attention", exact=True).click()
    await settle(page, 1500)
    states = {w["id"]: w["state"] for w in await windows(page)}
    results.check("switching desks hides the other desk's windows (#desk=1)",
                  states.get("fx_w_book") == "hidden" and states.get("fx_w_video2") == "active", states)
    commands_after = await frame_a.locator("#s").inner_text()
    results.check("a hidden desk's player is paused", commands_after.endswith("pauseVideo"), commands_after)
    clock_b = await page.locator('[data-desk-window="fx_w_video2"]').text_content() or ''
    clock_a_again = await page.locator('[data-desk-window="fx_w_video"]').text_content() or ''
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

    # Pairs: alt+, stacks the two windows top and bottom; alt+. gives one back its slot. A mark left in each
    # window's content shows that neither is remounted by pairing or unpairing.
    await page.evaluate("""() => { for (const id of ['fx_w_video2', 'fx_w_paper2']) {
      const mark = document.createElement('span'); mark.dataset.harnessMark = id;
      document.querySelector(`[data-desk-window="${id}"] [data-desk-pane-body]`).append(mark); } }""")
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
    marks = await page.evaluate("() => [...document.querySelectorAll('[data-harness-mark]')].map((m) => [m.dataset.harnessMark, m.closest('[data-desk-window]')?.getAttribute('data-desk-window')])")
    results.check("pairing and unpairing remount neither window (its content keeps a mark)",
                  sorted(marks) == [["fx_w_paper2", "fx_w_paper2"], ["fx_w_video2", "fx_w_video2"]], marks)

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
    # Each window is its own element, placed at desk:slot:pane.
    screen_slots = await page.evaluate("""() => { const out = {}; for (const el of document.querySelectorAll('[data-desk-slot^="fx_desk_attention:"]')) {
      const [, slot, pane] = el.dataset.deskSlot.split(':'); (out[slot] ??= [])[Number(pane)] = el.dataset.deskSlotWindow; }
      return Object.keys(out).sort((a, b) => Number(a) - Number(b)).map((k) => out[k]); }""")
    results.check("the server's slots equal the screen's", server_slots == screen_slots, [server_slots, screen_slots])
    fonts = await page.evaluate("""async () => {
      const families = ["Inter Variable", "Literata Variable", "Source Serif 4 Variable", "JetBrains Mono Variable", "Caveat Variable"];
      await Promise.all(families.map((family) => document.fonts.load(`16px "${family}"`)));
      return families.filter((family) => !document.fonts.check(`16px "${family}"`));
    }""")
    results.check("the five desk fonts load from the app itself", fonts == [], fonts)
    errors = await page.evaluate("() => window.__deskHarnessErrors")
    results.check("no error reached the shell's error line", errors == [], errors)


def changed_share(first: bytes, second: bytes, box: dict[str, float]) -> float:
    """The share of the stage's pixels that differ by more than the threshold in any channel."""

    import io

    from PIL import Image, ImageChops

    def crop(data: bytes) -> Any:
        image = Image.open(io.BytesIO(data)).convert("RGB")
        return image.crop((int(box["x"]), int(box["y"]), int(box["x"] + box["w"]), int(box["y"] + box["h"])))

    a, b = crop(first), crop(second)
    diff = ImageChops.difference(a, b).convert("RGB")
    pixels = diff.getdata()
    changed = sum(1 for r, g, bl in pixels if max(r, g, bl) > PIXEL_THRESHOLD)
    return changed / max(1, a.size[0] * a.size[1])


async def slot_rects(page: Page) -> dict[str, list[float]]:
    return await page.evaluate("""() => Object.fromEntries([...document.querySelectorAll('[data-desk-slot]')]
      .filter((el) => getComputedStyle(el).visibility !== 'hidden')
      .map((el) => { const r = el.getBoundingClientRect(); return [el.dataset.deskSlot, [r.x, r.y, r.width, r.height]]; }))""")


async def overview_on(page: Page) -> bool:
    return await page.evaluate("() => document.querySelector('[data-desk-shell]').dataset.overview === 'on'")


async def selection_inside(page: Page) -> bool:
    return await page.evaluate("""() => {
      const sel = document.querySelector('.ov-selected'); const st = document.querySelector('[data-desk-stage]');
      if (!sel || !st) return false;
      const r = sel.getBoundingClientRect(), s = st.getBoundingClientRect();
      return r.left >= s.left + 47.5 && r.right <= s.right - 47.5 && r.top >= s.top + 73.5 && r.bottom <= s.bottom - 47.5;
    }""")


async def run_overview(page: Page, base: str, results: Results, shots: Path | None) -> None:
    await page.goto(f"{base}/desk-harness.html")
    await page.wait_for_selector("[data-desk-window]")
    await settle(page, 1500)
    box = await stage_box(page)
    reading = await slot_rects(page)

    # A first trip builds the cards' miniatures; the identity check then compares like with like.
    await page.keyboard.press("Alt+o")
    await settle(page, 900)
    results.check("alt+o zooms into the overview", await overview_on(page))
    await shot(page, shots, "overview")
    states = await page.evaluate("() => [...new Set([...document.querySelectorAll('[data-desk-window]')].map((p) => p.dataset.windowState))]")
    results.check("in the overview every window is a preview card", states == ["preview"], states)
    await page.keyboard.press("Escape")
    await settle(page, 900)
    results.check("esc zooms back to the reading view", not await overview_on(page))

    # The commit-identity invariant, entering: the zoom's last frame against the committed overview.
    began = await page.evaluate("() => window.__deskDebug.beginZoom()")
    await page.evaluate("() => window.__deskDebug.setZoomProgress(1)")
    await page.wait_for_timeout(100)
    last_frame = await page.screenshot()
    await page.evaluate("() => window.__deskDebug.finishZoom(1)")
    await page.wait_for_timeout(100)
    committed = await page.screenshot()
    share_in = changed_share(last_frame, committed, box)
    results.check(f"entering: the last frame equals the committed overview (changed {share_in:.4%} ≤ {MAX_CHANGED_SHARE:.1%})", began and share_in <= MAX_CHANGED_SHARE, share_in)
    if shots is not None:
        (shots / "identity-in-last.png").write_bytes(last_frame)
        (shots / "identity-in-committed.png").write_bytes(committed)

    # And leaving: the zoom's last frame against the committed reading view.
    await page.evaluate("() => window.__deskDebug.beginZoom()")
    await page.evaluate("() => window.__deskDebug.setZoomProgress(0)")
    await page.wait_for_timeout(100)
    last_frame = await page.screenshot()
    await page.evaluate("() => window.__deskDebug.finishZoom(0)")
    await page.wait_for_timeout(300)
    committed = await page.screenshot()
    share_out = changed_share(last_frame, committed, box)
    results.check(f"leaving: the last frame equals the committed reading view (changed {share_out:.4%} ≤ {MAX_CHANGED_SHARE:.1%})", share_out <= MAX_CHANGED_SHARE, share_out)
    if shots is not None:
        (shots / "identity-out-last.png").write_bytes(last_frame)
        (shots / "identity-out-committed.png").write_bytes(committed)

    # The other exits meet the same invariant: to a desk never opened (its content is prepared before the
    # zoom), into focus mode (alt+↵: the full-screen rect is the zoom's destination), and after keyboard
    # navigation in the overview (its camera ease must not run under the zoom).
    async def identity_exit(name: str, to: str, focus_after: bool, before: str | None = None) -> float:
        await page.evaluate("() => { window.__deskDebug.beginZoom(); window.__deskDebug.setZoomProgress(1); window.__deskDebug.finishZoom(1); }")
        await settle(page, 600)
        if before:
            for key in before.split():
                await page.keyboard.press(key)
            await page.wait_for_timeout(60)
        began = await page.evaluate(f"() => window.__deskDebug.beginZoom({to}, {'true' if focus_after else 'false'})")
        await page.evaluate("() => window.__deskDebug.setZoomProgress(0)")
        await page.wait_for_timeout(900)
        last = await page.screenshot()
        await page.evaluate("() => window.__deskDebug.finishZoom(0)")
        await page.wait_for_timeout(300)
        committed = await page.screenshot()
        share = changed_share(last, committed, box)
        results.check(f"{name}: the last frame equals the committed view (changed {share:.4%} ≤ {MAX_CHANGED_SHARE:.1%})", bool(began) and share <= MAX_CHANGED_SHARE, share)
        if shots is not None:
            (shots / f"identity-{name.split()[0]}-last.png").write_bytes(last)
            (shots / f"identity-{name.split()[0]}-committed.png").write_bytes(committed)
        await page.keyboard.press("Escape") if focus_after else None
        await settle(page, 600)
        return share

    await identity_exit("unvisited: leaving to a desk never opened", "{ deskId: 'fx_desk_backprop', windowId: 'fx_w_book_range' }", False)
    await page.get_by_role("button", name="softmax and cross-entropy", exact=True).click()
    await settle(page, 900)
    await identity_exit("focus: leaving into focus mode (alt+↵)", "{ deskId: 'fx_desk_softmax', windowId: 'fx_w_book' }", True)
    await identity_exit("navigated: leaving after keyboard navigation in the overview", "null", False, before="j l")
    await page.get_by_role("button", name="softmax and cross-entropy", exact=True).click()
    await settle(page, 900)

    # A zoom's frames: transforms and opacities only, no element inserted, no custom property touched.
    await page.evaluate("""() => {
      window.__zoomMutations = { styles: new Set(), props: new Set(), added: 0, custom: 0 };
      const seen = new WeakMap();
      for (const el of document.querySelectorAll('[data-desk-world], [data-desk-world] *')) seen.set(el, el.getAttribute('style') || '');
      window.__zoomObserver = new MutationObserver((records) => {
        for (const r of records) {
          if (r.type === 'childList') { window.__zoomMutations.added += r.addedNodes.length; continue; }
          const el = r.target, before = (r.oldValue || ''), after = el.getAttribute('style') || '';
          const props = (text) => Object.fromEntries(text.split(';').map((x) => x.trim()).filter(Boolean).map((x) => { const i = x.indexOf(':'); return [x.slice(0, i).trim(), x.slice(i + 1).trim()]; }));
          const a = props(before), b = props(after);
          for (const key of new Set([...Object.keys(a), ...Object.keys(b)])) if (a[key] !== b[key]) { window.__zoomMutations.props.add(key); if (key.startsWith('--')) window.__zoomMutations.custom += 1; }
        }
      });
    }""")
    await page.evaluate("() => window.__deskDebug.beginZoom()")
    await page.evaluate("""() => window.__zoomObserver.observe(document.querySelector('[data-desk-shell]'), { attributes: true, attributeFilter: ['style'], attributeOldValue: true, subtree: true, childList: true })""")
    for p in (0.1, 0.25, 0.5, 0.75, 0.9):
        await page.evaluate(f"() => window.__deskDebug.setZoomProgress({p})")
        await page.wait_for_timeout(30)
    mutations = await page.evaluate("() => { window.__zoomObserver.disconnect(); const m = window.__zoomMutations; return { props: [...m.props].sort(), added: m.added, custom: m.custom }; }")
    allowed = {"transform", "opacity", "box-shadow"}
    results.check("a zoom's frames write only transforms, opacities and the selection's edge", set(mutations["props"]) <= allowed and mutations["custom"] == 0, mutations)
    results.check("a zoom's frames insert no element", mutations["added"] == 0, mutations["added"])
    await page.evaluate("() => window.__deskDebug.finishZoom(1)")
    await settle(page, 500)

    # Navigation keeps the selection inside the view (48 px, 74 from the top) on every path.
    inside = []
    for key in ["l", "l", "l", "l", "l", "j", "j", "k", "h", "h", "ArrowDown", "ArrowRight", "ArrowUp", "ArrowLeft", "Alt+j", "Alt+l", "Alt+k", "Alt+h"]:
        await page.keyboard.press(key)
        await page.wait_for_timeout(260)
        inside.append((key, await selection_inside(page)))
    results.check("every navigation path keeps the selection inside the view", all(ok for _key, ok in inside), [k for k, ok in inside if not ok])
    await shot(page, shots, "overview-navigated")

    # Previews log nothing: in the overview, panning with the wheel opens no visit and saves no progress.
    async def reading_activity() -> int:
        logged = await calls(page, "reader_log_activity")
        opened = sum(1 for c in logged for e in c["input"].get("events", []) if e.get("kind") != "reader_view_closed")
        return opened + len(await calls(page, "reader_note_reading_progress"))

    await settle(page, 2000)
    before_activity = await reading_activity()
    await page.mouse.move(800, 500)
    for _ in range(4):
        await page.mouse.wheel(0, 120)
        await page.wait_for_timeout(120)
    await settle(page, 2500)
    after_activity = await reading_activity()
    results.check("in the overview nothing opens a visit or saves reading progress", after_activity == before_activity, [before_activity, after_activity])

    # The four ways back restore the reading layout within 1 px: esc, o, alt+o, and ↵ / a click on the
    # card it was entered from.
    def same(a: dict[str, list[float]], b: dict[str, list[float]]) -> bool:
        return a.keys() == b.keys() and all(all(abs(x - y) <= 1 for x, y in zip(a[k], b[k], strict=True)) for k in a)

    await page.keyboard.press("Escape")
    await settle(page, 900)
    restored = {"esc": same(reading, await slot_rects(page))}
    for way in ("o", "Alt+o"):
        await page.keyboard.press("Alt+o")
        await settle(page, 900)
        await page.keyboard.press(way)
        await settle(page, 900)
        restored[way] = same(reading, await slot_rects(page))
    await page.keyboard.press("Alt+o")
    await settle(page, 900)
    await page.keyboard.press("Enter")
    await settle(page, 900)
    restored["enter"] = same(reading, await slot_rects(page))
    await page.keyboard.press("Alt+o")
    await settle(page, 900)
    await page.locator('.ov-selected').click()
    await settle(page, 900)
    restored["click"] = same(reading, await slot_rects(page))
    results.check("the four ways back restore the reading layout within 1 px", all(restored.values()), restored)

    # The frame trace of one alt+o zoom (information: the owner deferred the frame budget).
    await page.keyboard.press("Alt+o")
    await settle(page, 900)
    times = await page.evaluate("() => window.__deskDebug.zoomFrameTimes()")
    gaps = sorted(b - a for a, b in zip(times, times[1:], strict=False))
    if gaps:
        p95 = gaps[min(len(gaps) - 1, int(len(gaps) * 0.95))]
        results.check(f"frame trace (information): {len(times)} frames, median {gaps[len(gaps) // 2]:.1f} ms, p95 {p95:.1f} ms, max {gaps[-1]:.1f} ms", True)
    await page.keyboard.press("Escape")
    await settle(page, 900)

    # alt + a mouse-wheel notch zooms all the way; the other way comes back.
    await page.mouse.move(800, 500)
    await page.keyboard.down("Alt")
    await page.mouse.wheel(0, 120)
    await page.keyboard.up("Alt")
    await settle(page, 900)
    results.check("alt + a wheel notch zooms out to the overview", await overview_on(page))
    await page.wait_for_timeout(200)
    await page.keyboard.down("Alt")
    await page.mouse.wheel(0, -120)
    await page.keyboard.up("Alt")
    await settle(page, 900)
    results.check("alt + a notch the other way zooms back in", not await overview_on(page))

    # ctrl+drag on the stage background scrubs the zoom; letting go past 40 % completes it.
    gap_x = box["x"] + 34 + (box["w"] - 78) / 2 + 5
    await page.mouse.move(gap_x, box["y"] + 200)
    await page.keyboard.down("Control")
    await page.mouse.down()
    await page.mouse.move(gap_x, box["y"] + 260, steps=4)
    hud = await page.locator(".desk-hud").inner_text() if await page.locator(".desk-hud").count() else ""
    await page.mouse.move(gap_x, box["y"] + 400, steps=6)
    await page.mouse.up()
    await page.keyboard.up("Control")
    await settle(page, 900)
    results.check("ctrl+drag on the background scrubs the zoom, with the HUD saying so", await overview_on(page) and "ctrl + drag" in hud, hud)
    await page.keyboard.press("Escape")
    await settle(page, 900)

    # A paused window's content is not rendered (content-visibility), as the lifecycle contract asks.
    paused_cv = await page.evaluate("""() => [...document.querySelectorAll('.desk-window.paused .desk-pane-body')].map((b) => getComputedStyle(b).contentVisibility)""")
    results.check("a paused window's content is not rendered (content-visibility: auto)", bool(paused_cv) and set(paused_cv) == {"auto"}, paused_cv)

    # alt + a sideways swipe pans the strip, then snaps to the nearest window and focuses it.
    before_focus = [w["id"] for w in await windows(page) if w["state"] == "active"]
    await page.mouse.move(800, 500)
    await page.keyboard.down("Alt")
    for _ in range(6):
        await page.mouse.wheel(110, 0)
        await page.wait_for_timeout(16)
    await page.keyboard.up("Alt")
    await settle(page, 900)
    after_focus = [w["id"] for w in await windows(page) if w["state"] == "active"]
    left_edges = await page.evaluate("""() => [...document.querySelectorAll('[data-desk-slot]')].map((el) => el.getBoundingClientRect().left - document.querySelector('[data-desk-stage]').getBoundingClientRect().left)""")
    snapped = any(abs(x - 34) <= 1 for x in left_edges)
    results.check("alt + a sideways swipe pans the strip and snaps to a window, which takes the focus", after_focus != before_focus and snapped, [before_focus, after_focus])

    # In the overview a card dragged onto another desk's row moves there.
    await page.keyboard.press("Alt+o")
    await settle(page, 900)
    source = page.locator('[data-desk-slot-window="fx_w_paper"]')
    target = page.locator('[data-desk-slot-window="fx_w_video2"]')
    sb, tb = await source.bounding_box(), await target.bounding_box()
    if sb and tb:
        await page.mouse.move(sb["x"] + sb["width"] / 2, sb["y"] + sb["height"] / 2)
        await page.mouse.down()
        await page.mouse.move(tb["x"] + tb["width"] * 0.8, tb["y"] + tb["height"] / 2, steps=8)
        await page.mouse.up()
        await settle(page, 700)
    moved_to = await page.evaluate("() => window.__deskHarness.server.state().desks.find((d) => d.slots.some((s) => s.windows.some((w) => w.windowId === 'fx_w_paper'))).deskId")
    results.check("in the overview a card dragged onto another desk's row moves there", moved_to == "fx_desk_attention", moved_to)
    await page.keyboard.press("Escape")
    await settle(page, 900)

    # The laptop rail: below 1400 px the shelf folds to 44 px; ☰ overlays it at 260 px.
    await page.set_viewport_size({"width": 1280, "height": 800})
    await settle(page, 600)
    rail = await page.evaluate("() => { const r = document.querySelector('.desk-shelf-rail')?.getBoundingClientRect(); return r ? r.width : 0; }")
    await page.get_by_role("button", name="show the strip").click()
    await settle(page, 300)
    overlay = await page.evaluate("() => { const r = document.querySelector('.desk-shelf-overlay')?.getBoundingClientRect(); return r ? r.width : 0; }")
    results.check("below 1400 px the shelf is a 44 px rail whose ☰ overlays it at 260 px", abs(rail - 44) <= 1 and abs(overlay - 260) <= 1, [rail, overlay])
    await shot(page, shots, "laptop-rail")
    errors = await page.evaluate("() => window.__deskHarnessErrors")
    results.check("no error reached the shell's error line (overview run)", errors == [], errors)


async def companion_rect(page: Page) -> dict[str, float] | None:
    """The companion panel's rect relative to the stage, or None when it is not shown."""
    return await page.evaluate("""() => { const c = document.querySelector('[data-desk-companion]'); if (!c) return null;
      const s = document.querySelector('[data-desk-stage]').getBoundingClientRect(); const r = c.getBoundingClientRect();
      return { x: r.x - s.x, y: r.y - s.y, w: r.width, h: r.height, mode: c.dataset.companionMode }; }""")


async def select_passage(page: Page, text: str) -> dict[str, float]:
    """Select one passage of the book window whose text holds `text`; returns its rect relative to the stage."""
    return await page.evaluate("""(text) => { const p = [...document.querySelectorAll('[data-desk-window="fx_w_book"] [data-span-id]')].find((e) => e.textContent.includes(text));
      const range = document.createRange(); range.selectNodeContents(p); const sel = getSelection(); sel.removeAllRanges(); sel.addRange(range);
      const s = document.querySelector('[data-desk-stage]').getBoundingClientRect(); const r = range.getBoundingClientRect();
      return { x: r.x - s.x, y: r.y - s.y, w: r.width, h: r.height }; }""", text)


async def sample_rects(page: Page, ms: int) -> list[dict[str, float]]:
    """The companion's on-screen rect at every animation frame for `ms` (transforms included)."""
    return await page.evaluate("""(ms) => new Promise((done) => { const out = []; const t0 = performance.now();
      const s = document.querySelector('[data-desk-stage]').getBoundingClientRect();
      const tick = () => { const c = document.querySelector('[data-desk-companion]'); if (c) { const r = c.getBoundingClientRect(); out.push({ x: r.x - s.x, y: r.y - s.y, w: r.width, h: r.height, o: Number(getComputedStyle(c).opacity) }); }
        if (performance.now() - t0 < ms) requestAnimationFrame(tick); else done(out); }; requestAnimationFrame(tick); })""", ms)


async def run_companion(page: Page, base: str, results: Results, shots: Path | None) -> None:
    """The companion and search (spec §8, §9.3; the RD3 deep links' equivalents)."""
    await page.goto(f"{base}/desk-harness.html")
    await page.wait_for_selector("[data-desk-window]")
    await settle(page, 1500)
    stage = await stage_box(page)
    sw, sh = stage["w"], stage["h"]
    dock_br = {"x": sw - 400 - 14, "y": sh - round(sh * 0.52) - 14, "w": 400, "h": round(sh * 0.52)}

    def near(a: dict[str, float] | None, b: dict[str, float], tol: float = 1.5) -> bool:
        return a is not None and all(abs(a[k] - b[k]) <= tol for k in ("x", "y", "w", "h"))

    # #cur=sel: c with a selection opens it anchored 10 px below the selection, the selection its chip.
    sel = await select_passage(page, "largest score")
    await page.keyboard.press("c")
    samples = await sample_rects(page, 320)
    rect = await companion_rect(page)
    chip = await page.locator(".desk-companion .chip").inner_text() if await page.locator(".desk-companion .chip").count() else ""
    results.check("c with a selection opens the companion anchored 10 px below it, the selection its chip (#cur=sel)",
                  rect is not None and rect["mode"] == "anchored" and abs(rect["y"] - (sel["y"] + sel["h"] + 10)) <= 2 and "largest score" in chip, [rect, sel, chip[:60]])
    results.check("the summon never passes through the dock (every frame away from it)", all(not near(sample, dock_br, 40) for sample in samples) and len(samples) > 3, len(samples))
    await shot(page, shots, "companion-cur-sel")

    # c again dissolves it in place: every frame stays at the anchor, and it fades out.
    anchored = rect
    await page.keyboard.press("c")
    samples = await sample_rects(page, 300)
    centred = [abs((s["x"] + s["w"] / 2) - (anchored["x"] + anchored["w"] / 2)) <= 12 and abs((s["y"] + s["h"] / 2) - (anchored["y"] + anchored["h"] / 2)) <= 12 for s in samples] if anchored else [False]
    results.check("c again dissolves it where it is: no frame moves toward the dock, and it goes", all(centred) and await companion_rect(page) is None, [len(samples), samples[-1] if samples else None])

    # #cur=shiftc: shift+c opens it at its dock (br, 400 × 52 %).
    await page.keyboard.press("Shift+C")
    await settle(page, 400)
    results.check("shift+c opens it at its dock, 400 wide and 52 % high, 14 px in (#cur=shiftc)", near(await companion_rect(page), dock_br), await companion_rect(page))

    # A docked companion never moves when the learner scrolls, pans, reorders, pairs, gathers or switches desks.
    before = await companion_rect(page)
    still = []
    for action in ("scroll", "Alt+l", "Alt+BracketRight", "Alt+BracketLeft", "Alt+h", "Alt+g", "Alt+j", "Alt+k"):
        if action == "scroll":
            await page.evaluate("() => { const b = document.querySelector('[data-desk-window=\"fx_w_book\"] [data-desk-pane-body] *'); const sc = [...document.querySelectorAll('[data-desk-window=\"fx_w_book\"] *')].find((e) => e.scrollHeight > e.clientHeight + 20); if (sc) sc.scrollTop += 300; }")
        else:
            await page.keyboard.press(action)
        await settle(page, 500)
        still.append((action, near(await companion_rect(page), before)))
    results.check("a docked companion never moves on scroll, pan, reorder, gather or a desk switch", all(ok for _a, ok in still), [a for a, ok in still if not ok])

    # #cur=handoff: an anchored companion hands off to its dock by a FLIP when its text scrolls away.
    await page.keyboard.press("c")
    await settle(page, 400)
    sel = await select_passage(page, "Adding the same constant")
    await page.keyboard.press("c")
    await page.wait_for_timeout(400)
    anchored = await companion_rect(page)
    await page.evaluate("() => { const sc = [...document.querySelectorAll('[data-desk-window=\"fx_w_book\"] *')].find((e) => e.scrollHeight > e.clientHeight + 20); if (sc) sc.scrollTop += 240; }")
    samples = await sample_rects(page, 400)
    landed = await companion_rect(page)
    between = [s for s in samples if not near(s, anchored or dock_br, 3) and not near(s, dock_br, 3)]
    results.check("its text scrolled away, an anchored companion hands off to its dock by a FLIP (frames between, #cur=handoff)",
                  anchored is not None and anchored["mode"] == "anchored" and near(landed, dock_br) and len(between) >= 2, [anchored, landed, len(between)])
    await shot(page, shots, "companion-handoff")

    # #dock=right: dragging the handle and dropping it near the right edge snaps it to the right dock.
    grab = page.locator(".desk-companion .grab")
    gb = await grab.bounding_box()
    if gb:
        await page.mouse.move(gb["x"] + gb["width"] / 2, gb["y"] + 4)
        await page.mouse.down()
        await page.mouse.move(stage["x"] + sw - 120, stage["y"] + 120, steps=8)
        await page.mouse.up()
    await settle(page, 500)
    right = await companion_rect(page)
    rw = min(420, sw * 0.34)
    results.check("dragged near the right edge, it snaps to the right dock (#dock=right)", near(right, {"x": sw - rw - 14, "y": 14, "w": rw, "h": sh - 28}), right)
    await shot(page, shots, "companion-dock-right")

    # Asking, with the fake tutor held open: the question shows at once; edits and hovers are timed.
    await page.evaluate("() => { window.__deskHarness.companion.held = true; }")
    box = page.locator(".desk-companion .input")
    await box.fill("why does the largest score win?")
    await box.press("Enter")
    await page.wait_for_timeout(200)
    asking = await page.locator('.desk-companion [data-exchange-status="asking"]').count()
    edit_ms = await page.evaluate("""async () => { const input = document.querySelector('.desk-companion .input'); const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
      const times = []; for (let i = 0; i < 20; i += 1) { const t0 = performance.now(); set.call(input, 'draft ' + i); input.dispatchEvent(new Event('input', { bubbles: true }));
        await new Promise((r) => requestAnimationFrame(() => r())); times.push(performance.now() - t0); } times.sort((a, b) => a - b); return { median: times[10], max: times[19] }; }""")
    results.check(f"while an answer generates the question shows at once; an edit renders in {edit_ms['median']:.1f} ms median, {edit_ms['max']:.1f} ms max (information; under 50 ms asked)",
                  asking == 1, [asking, edit_ms])
    await page.evaluate("() => { window.__deskHarness.companion.held = false; }")
    await page.wait_for_timeout(3600)
    answered = await page.locator('.desk-companion [data-exchange-status="answered"]').count()
    results.check("released, the answer arrives through the poller with its claim", answered == 1 and await page.locator(".desk-companion .claim").count() >= 1, answered)

    # #hist: the history by day and desk.
    await page.locator(".desk-companion .ctabs button", has_text="history").click()
    await settle(page, 600)
    days = await page.locator(".desk-companion .hday").count()
    results.check("the history tab lists exchanges by day and desk (#hist)", days >= 2, days)
    await shot(page, shots, "companion-hist")

    # #spot=softmax: / opens search; groups, open on this desk first; the meaning pass merges in with its tag.
    # A second question is asked first and held open, so the hover below is timed while an answer generates.
    await page.locator(".desk-companion .ctabs button", has_text="tutor").click()
    await page.evaluate("() => { window.__deskHarness.companion.held = true; }")
    await page.locator(".desk-companion .input").fill("and what does a temperature change?")
    await page.locator(".desk-companion .input").press("Enter")
    await page.wait_for_timeout(300)
    await page.mouse.click(stage["x"] + 400, stage["y"] + 300)
    await page.keyboard.press("/")
    await page.wait_for_timeout(250)
    await page.keyboard.type("softmax")
    await page.wait_for_timeout(4200)
    groups = await page.evaluate("() => [...document.querySelectorAll('[data-search-group]')].map((g) => g.dataset.searchGroup)")
    # The meaning rows join the passages group after its word rows: tab shows the group whole.
    for _ in range(12):
        if await page.evaluate("() => Boolean(document.querySelector('[data-search-group=\"passages\"] .r.sel'))"):
            break
        await page.keyboard.press("ArrowDown")
    await page.keyboard.press("Tab")
    await page.wait_for_timeout(200)
    tagged = await page.locator(".desk-search .r .w", has_text="by meaning").count()
    results.check("/ opens search: groups in order with open on this desk first; the meaning pass merges in tagged (#spot=softmax)",
                  bool(groups) and groups[0] == "open" and "passages" in groups and tagged >= 1, [groups, tagged])
    sel_top = await page.evaluate("() => document.querySelector('.desk-search-sel')?.style.top")
    await page.keyboard.press("ArrowUp")
    await page.wait_for_timeout(200)
    moved = await page.evaluate("() => document.querySelector('.desk-search-sel')?.style.top")
    results.check("↑ glides the selection block to the row above", sel_top != moved, [sel_top, moved])
    # The pointer's hover response while an answer generates (the fake tutor held): a row under the pointer
    # takes the selection. Pad marks' hover cards arrive with pads; this is the hover there is now.
    generating = await page.locator('.desk-companion [data-exchange-status="asking"]').count()
    hover_ms = await page.evaluate("""async () => { const rows = [...document.querySelectorAll('.desk-search .r')]; const row = rows[rows.length - 1];
      const t0 = performance.now(); row.dispatchEvent(new MouseEvent('mousemove', { bubbles: true }));
      for (let i = 0; i < 60 && !row.classList.contains('sel'); i += 1) await new Promise((r) => requestAnimationFrame(() => r()));
      return row.classList.contains('sel') ? performance.now() - t0 : null; }""")
    await page.evaluate("() => { window.__deskHarness.companion.held = false; }")
    results.check(f"while an answer generates, a hovered search row takes the selection in {hover_ms:.1f} ms (information; hover cards under 250 ms asked)" if hover_ms is not None else "a hovered search row takes the selection", hover_ms is not None and generating == 1, [hover_ms, generating])
    await shot(page, shots, "search-softmax")
    await page.keyboard.press("Escape")
    await settle(page, 300)
    results.check("esc closes search", await page.locator("[data-desk-search]").count() == 0)

    # #switch: the shelf's "/ switch" opens it too.
    await page.get_by_role("button", name="/ switch").click()
    await settle(page, 300)
    results.check("the shelf's / switch opens search (#switch)", await page.locator("[data-desk-search]").count() == 1)
    await page.keyboard.press("Escape")
    await settle(page, 300)

    # #ov: in the overview the companion is the pill.
    await page.keyboard.press("Alt+o")
    await settle(page, 900)
    pill = await page.evaluate("() => { const p = document.querySelector('[data-desk-companion-pill]'); return p ? { on: p.classList.contains('on'), o: getComputedStyle(p).opacity } : null; }")
    results.check("in the overview the companion is its pill (#ov)", pill is not None and pill["on"] and float(pill["o"]) > 0.95, pill)
    await shot(page, shots, "companion-pill")
    await page.keyboard.press("Escape")
    await settle(page, 900)
    errors = await page.evaluate("() => window.__deskHarnessErrors")
    results.check("no error reached the shell's error line (companion run)", errors == [], errors)


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
            for runner in ("desks", "overview", "companion", "preview"):
                context = await browser.new_context(viewport=VIEWPORT)
                await context.route(lambda url: not url.startswith(base), route_outside)
                page = await context.new_page()
                try:
                    if runner == "desks":
                        await run_desks(page, base, results, args.shots)
                    elif runner == "overview":
                        await run_overview(page, base, results, args.shots)
                    elif runner == "companion":
                        await run_companion(page, base, results, args.shots)
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
