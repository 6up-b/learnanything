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

The goal run (RD6, `?goal=1`) adds the RD6 deep links' equivalents: the band under the top bar, the marks'
colours, widths and their gap to the text, dimming and nodim, the why on core, supporting, skippable and later passages,
the depth set through curriculum.set_depth, the path view opened with `p` and read it anyway stored, a paper's marks and
head, a pad stack's goal line, and one whole-reading goal.lens per reading in view.

The pads' run (RD4) adds the RD4 deep links' equivalents (the running pad, the sticky tabs' merge and
fillets, the § row's hover fade, the submitted tag, ⓘ, the editor writing through pad.apply, the pad menu,
lift out, a sketch block's tools, arrange and split, a passage's ✎ link, the carried ◌, the drain) and display
math in the companion's answer. The display-math run (`?latex=1`, spec §13.4 rule 5) renders tall and wide
equations in every pad block kind at three widths and in a hover card, and measures each equation's ink
against its nearest clipping ancestor below the window's scroller, before and after a resize.

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
      const families = ["Literata Variable", "Source Serif 4 Variable", "JetBrains Mono Variable", "Caveat Variable"];
      await Promise.all(families.map((family) => document.fonts.load(`16px "${family}"`)));
      return families.filter((family) => !document.fonts.check(`16px "${family}"`));
    }""")
    results.check("the four desk fonts load from the app itself", fonts == [], fonts)
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

    # #cur=sel: c with a selection opens it anchored 10 px below the selection, the selection its chip. The
    # passage is brought to the top of the book first, so the panel has room below it at the book's reading size.
    await page.evaluate("""() => { const p = [...document.querySelectorAll('[data-desk-window="fx_w_book"] [data-span-id]')].find((e) => e.textContent.includes("largest score"));
      const sc = p.closest('.ll-scroll'); sc.scrollTop += p.getBoundingClientRect().top - sc.getBoundingClientRect().top - 40; }""")
    await settle(page, 300)
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
    # Away, the faded panel is inert: Tab never reaches its controls.
    inside = []
    for _ in range(12):
        await page.keyboard.press("Tab")
        inside.append(await page.evaluate("() => Boolean(document.activeElement?.closest('[data-desk-companion], [data-desk-companion-tab]'))"))
    inert = await page.evaluate("() => [...document.querySelectorAll('[data-desk-companion], [data-desk-companion-tab]')].every((e) => e.hasAttribute('inert'))")
    results.check("in the overview the hidden companion is inert: Tab never lands in it", not any(inside) and inert, [inside, inert])
    await page.keyboard.press("Escape")
    await settle(page, 900)
    errors = await page.evaluate("() => window.__deskHarnessErrors")
    results.check("no error reached the shell's error line (companion run)", errors == [], errors)


# The display-math measurement (spec §13.4 rule 5): each equation's ink (the union of the client rects of
# KaTeX's .vlist and .mord spans) against the visible rect of its nearest clipping ancestor below the window's
# own scroller, with at least 3 px of room above and 5 px below; a wide equation is fitted (scale >= 0.75) or
# sits in a horizontal scroller whose bar is visible and which keeps the full height.
MATH_SCROLLERS = ".pscroller, .pscroll, .desk-companion .body, .desk-thread, [data-desk-window]"
MEASURE_MATH = """([scope, scrollers]) => {
  const out = [];
  for (const display of document.querySelectorAll(scope + ' .katex-display')) {
    const rects = [...display.querySelectorAll('.vlist, .mord')].flatMap((e) => [...e.getClientRects()]).filter((r) => r.width > 0 && r.height > 0);
    if (!rects.length) continue;
    const ink = { top: Math.min(...rects.map((r) => r.top)), bottom: Math.max(...rects.map((r) => r.bottom)), left: Math.min(...rects.map((r) => r.left)), right: Math.max(...rects.map((r) => r.right)) };
    let clip = null;
    for (let el = display; el && el !== document.body; el = el.parentElement) {
      if (el !== display && el.matches(scrollers)) break;
      const cs = getComputedStyle(el);
      if (cs.overflowX !== 'visible' || cs.overflowY !== 'visible') { clip = el; break; }
    }
    const katex = display.querySelector(':scope > .katex');
    const scale = katex ? parseFloat(getComputedStyle(katex).fontSize) / parseFloat(getComputedStyle(display).fontSize) / 1.21 : 1;
    const own = display.getBoundingClientRect();
    const row = { where: display.closest('[data-block], .pcard, .desk-companion, [data-latex-column]')?.getAttribute('data-block') || display.closest('.pcard, .desk-companion') ?.className.split(' ')[0] || '', scale: Math.round(scale * 1000) / 1000, ink, clip: null, scroller: false, bar: 0, ok: true, why: '' };
    if (clip) {
      const box = clip.getBoundingClientRect();
      const visible = { top: box.top + clip.clientTop, bottom: box.top + clip.clientTop + clip.clientHeight, left: box.left + clip.clientLeft, right: box.left + clip.clientLeft + clip.clientWidth };
      row.clip = { cls: clip.className, ...visible };
      const scrollsX = ['auto', 'scroll'].includes(getComputedStyle(clip).overflowX) && clip.scrollWidth > clip.clientWidth + 0.5;
      row.scroller = scrollsX;
      row.bar = clip.offsetHeight - clip.clientHeight - clip.clientTop * 2;
      if (ink.top < visible.top + 3) { row.ok = false; row.why += 'top '; }
      if (ink.bottom > visible.bottom - 5) { row.ok = false; row.why += 'bottom '; }
      if (!scrollsX && (ink.left < visible.left - 0.5 || ink.right > visible.right + 0.5)) { row.ok = false; row.why += 'sides '; }
      if (scrollsX && row.bar <= 0) { row.ok = false; row.why += 'no visible bar '; }
    }
    // Fitted or scrolled: never squeezed under 0.75, never wider than its own column unless it scrolls.
    if (scale < 0.75 - 0.005) { row.ok = false; row.why += 'scale '; }
    if (!row.scroller && ink.right > own.right + 1) { row.ok = false; row.why += 'overflows its column '; }
    out.push(row);
  }
  return out;
}"""


async def measure_math(page: Page, scope: str) -> list[dict[str, Any]]:
    return await page.evaluate(MEASURE_MATH, [scope, MATH_SCROLLERS])


async def run_latex(page: Page, base: str, results: Results, shots: Path | None) -> None:
    """Display math in every container is never clipped (spec §13.4; an owner rule)."""
    await page.goto(f"{base}/desk-harness.html?latex=1")
    await page.wait_for_selector("[data-latex-column] .katex-display")
    await page.evaluate("document.fonts.ready")
    await settle(page, 900)
    for width in (640, 430, 300):
        column = f'[data-latex-column="{width}"]'
        rows = []
        for block in ("fx_m_text1", "fx_m_text2", "fx_m_quote", "fx_m_tutor", "fx_m_check", "fx_m_wide"):
            await page.locator(f'{column} [data-block="{block}"]').scroll_into_view_if_needed()
            rows += [row for row in await measure_math(page, f'{column} [data-block="{block}"]')]
        bad = [row for row in rows if not row["ok"]]
        results.check(f"every display equation in a {width} px pad has room above and below and is fitted or scrolls (§13.4)", len(rows) >= 7 and not bad, bad[:2] or len(rows))
        if width == 640:
            results.check("in the wide pad the wide equation fits or is scaled, not scrolled", any(r["where"] == "fx_m_wide" and not r["scroller"] and r["ok"] for r in rows), [r for r in rows if r["where"] == "fx_m_wide"])
        if width == 300:
            results.check("in the narrow pad the wide equation scrolls, with a visible bar and its full height", any(r["where"] == "fx_m_wide" and r["scroller"] and r["bar"] > 0 and r["ok"] for r in rows), [r for r in rows if r["where"] == "fx_m_wide"])
        await shot(page, shots, f"latex-{width}")
    # A hover card holding display math (the tutor's words).
    column = '[data-latex-column="430"]'
    await page.locator(f'{column} [data-block="fx_m_tutor"]').scroll_into_view_if_needed()
    await page.locator(f'{column} [data-block="fx_m_tutor"] [data-mark="tutor"]').hover()
    await page.wait_for_selector(f"{column} [data-pad-card] .katex-display", timeout=3000)
    rows = await measure_math(page, f"{column} [data-pad-card]")
    results.check("display math in a pad's hover card is never clipped (§13.4)", rows and all(row["ok"] for row in rows), rows[:2])
    await shot(page, shots, "latex-card")
    # Re-measured on resize: narrowing the page changes no equation into a clipped one.
    await page.set_viewport_size({"width": 1100, "height": 900})
    await settle(page, 600)
    rows = await measure_math(page, "[data-latex-column]")
    results.check("after a resize every equation is measured again and none is clipped", rows and all(row["ok"] for row in rows), [row for row in rows if not row["ok"]][:2])
    await page.set_viewport_size(VIEWPORT)


async def run_pads(page: Page, base: str, results: Results, shots: Path | None) -> None:
    """The pads (spec §10; the RD4 deep links' equivalents) and display math in the companion's bubbles."""
    await page.goto(f"{base}/desk-harness.html")
    await page.wait_for_selector("[data-desk-window]")
    await settle(page, 1500)
    # Bring the pad stack into view (it is the desk's last window).
    for _ in range(6):
        await page.keyboard.press("Alt+l")
        await page.wait_for_timeout(250)
    await page.wait_for_selector(".desk-pads [data-block]")
    await settle(page, 900)
    scroller = page.locator(".desk-pads .pscroller")

    # #s11=run: the running pad's dated headings, the last one today, and the jot line.
    days = await page.locator(".desk-pads .paper.k-running .day").all_inner_texts()
    jot = await page.locator(".desk-pads .paper.k-running .pb.jot").inner_text()
    results.check("the running pad has dated headings, the newest marked today, and the jot line (#s11=run)", len(days) >= 2 and days[-1].endswith("· TODAY") and "jot · it lands here by default" in jot, [days, jot])
    await shot(page, shots, "pads-run")

    # #tabs=distance,pad=2,padf=0.4: tabs merge into the paper with fillets as the next pad nears.
    geo = await page.evaluate("""() => { const s = document.querySelector('.desk-pads .pscroller'); const p = document.querySelectorAll('.desk-pads .paper')[1]; return { top: p.offsetTop, h: s.clientHeight }; }""")
    await scroller.evaluate("(s, y) => { s.scrollTop = y; }", max(0, geo["top"] - geo["h"] * 0.6))
    await settle(page, 500)
    merges = await page.evaluate("() => [...document.querySelectorAll('.desk-pads .ptab')].map((t) => [Number(t.dataset.merge), getComputedStyle(t).getPropertyValue('--fillet').trim(), parseFloat(t.style.marginLeft)])")
    results.check("the sticky tabs carry a merge amount, fillets at that opacity, and margins by distance (#tabs=distance,pad=2,padf=0.4)", len(merges) == 2 and all(0 <= m[0] <= 1 for m in merges) and all(m[1] != "" for m in merges), merges)
    await shot(page, shots, "pads-tabs-distance")
    await scroller.evaluate("(s) => { s.scrollTop = 0; }")
    await settle(page, 400)

    # The § row hover: the row darkens and its text fades to the paper's white (transitioned, both ways).
    row = page.locator('.desk-pads [data-block="fx_b_r2"]')
    before = await row.evaluate("(r) => [getComputedStyle(r).backgroundColor, getComputedStyle(r.querySelector('.bx p, .bx .quote') || r).color]")
    await row.hover()
    await page.wait_for_timeout(400)
    during = await row.evaluate("(r) => [getComputedStyle(r).backgroundColor, getComputedStyle(r.querySelector('.bx p, .bx .quote') || r).color, getComputedStyle(r.querySelector('.bx .quote') || r).transitionProperty]")
    await page.mouse.move(5, 5)
    await page.wait_for_timeout(400)
    after = await row.evaluate("(r) => [getComputedStyle(r).backgroundColor, getComputedStyle(r.querySelector('.bx p, .bx .quote') || r).color]")
    results.check("a § row darkens on hover and its text fades to the paper's white, and back (§10.3)", during[0] == "rgb(42, 40, 37)" and during[1] == "rgb(253, 253, 252)" and before == after and before != during[:2] and "color" in during[2], [before, during, after])

    # #s12=submitted: the green tag on a submitted block; a quote says it is kept, not read.
    tag = await page.locator('.desk-pads [data-block="fx_b_r4"] .submitted').inner_text()
    quote_emits = await page.locator('.desk-pads [data-block="fx_b_r2"]').get_attribute("data-emits")
    results.check("a submitted block shows its tag; a quote is marked as not read as your words (#s12=submitted)", tag == "submitted · teach-back" and quote_emits == "no", [tag, quote_emits])

    # #s12=info: the ⓘ popover says where the words go.
    await page.locator(".desk-pads .pinfo").click()
    info = await page.locator(".desk-pads .pinfo-pop").inner_text()
    results.check("ⓘ says where your words go and that only submitted blocks count (#s12=info)", "where your words go" in info and "Only blocks you submit" in info, info[:80])
    await shot(page, shots, "pads-info")
    await page.locator(".desk-pads .pinfo").click()

    # The editor: the jot line opens a block; typing and ↵ keep it; the write goes out by pad.apply.
    await page.locator(".desk-pads .paper.k-running .pb.jot").click()
    await page.wait_for_selector("[data-pad-editor] textarea")
    hint = await page.locator("[data-pad-editor] .hintline").inner_text()
    await page.keyboard.type("a harness line with $x^2$")
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(200)
    await page.keyboard.press("Escape")
    await settle(page, 900)
    applied = await calls(page, "pad_apply")
    sent = [op for call in applied for op in call["input"].get("ops", [])]
    results.check("the editor's hint, and a line written and kept goes out through pad.apply (insert, then edit)", hint == "markdown · $math$ · ↵ new line · esc puts it back" and [op["op"] for op in sent][:2] == ["insert_block", "edit_block"] and any(op.get("bodyMd") == "a harness line with $x^2$" for op in sent), [hint, [op["op"] for op in sent]])

    # #s11=menu: right-click a line of yours.
    await page.locator('.desk-pads [data-block="fx_b_r1"]').click(button="right")
    menu = await page.locator(".desk-padmenu").inner_text()
    results.check("the pad menu: the verbs, then INSERT BELOW THIS LINE, marimo arriving with notebooks (#s11=menu)", "Ask about this" in menu and "Submit this block as…" in menu and "INSERT BELOW THIS LINE" in menu and "marimo cell · arrives with notebooks" in menu, menu[:160])
    await shot(page, shots, "pads-menu")
    await page.keyboard.press("Escape")

    # Ask about this, from a pad line linked to no passage: asked beside the desk's book, the block named and
    # its words with the question.
    await page.locator('.desk-pads [data-block="fx_b_r1"]').click(button="right")
    await page.locator(".desk-padmenu").get_by_text("Ask about this").click()
    await settle(page, 500)
    box = page.locator(".desk-companion .input")
    cannot = await page.locator(".desk-companion .cannot").count()
    await box.fill("why only in proportion?", timeout=5000)
    await box.press("Enter")
    await settle(page, 600)
    asked = [call["input"] for call in await calls(page, "companion_ask")]
    last = asked[-1] if asked else {}
    results.check("Ask about this on a pad line asks (beside the desk's book), naming the block, its words with the question",
                  cannot == 0 and last.get("padBlockIds") == ["fx_b_r1"] and last.get("extractionId") == "fx_ext_softmax" and "my pad" in str(last.get("question")), [cannot, {k: last.get(k) for k in ("padBlockIds", "extractionId", "question")}])
    await page.locator(".desk-companion").get_by_role("button", name="c hide").click()
    await settle(page, 600)

    # #s11=lift: lift out leaves a stub and adds the block's own pad to the stack.
    await page.locator('.desk-pads [data-block="fx_b_r7"]').hover()
    await page.locator('.desk-pads [data-block="fx_b_r7"] .lift').click()
    await settle(page, 600)
    stub = await page.locator('.desk-pads [data-block="fx_b_r7"] .lifted').inner_text()
    tabs = await page.locator(".desk-pads .ptab").count()
    results.check("lift out leaves '→ lifted to …' and a third pad in the stack (#s11=lift)", stub.startswith("→ lifted to") and tabs == 3, [stub[:60], tabs])
    await shot(page, shots, "pads-lift")

    # #s11=sketchqk: alt+d adds a sketch block with every tool.
    await page.keyboard.press("Alt+d")
    await settle(page, 500)
    tools = await page.locator(".desk-pads .desk-sketch").last.locator(".bar button").all_inner_texts()
    results.check("alt+d adds a sketch block with every tool (#s11=sketchqk)", [t.split(" ")[-1] for t in tools] == ["pen", "line", "arrow", "box", "text", "eraser"], tools)

    # #s11=arrange and #s11=split: alt+a, choose two, ↵ shows them one above the other.
    await page.keyboard.press("Alt+a")
    arrange = await page.locator(".desk-arrange").inner_text()
    await page.keyboard.press("Enter")
    await settle(page, 500)
    panes = await page.locator(".desk-pads .split .pane").count()
    results.check("alt+a arranges pads above and below each other, and ↵ splits them (#s11=arrange, #s11=split)", "ARRANGE · pads above and below each other" in arrange and panes == 2, [arrange[:60], panes])
    await shot(page, shots, "pads-split")
    await page.keyboard.press("Alt+a")
    await page.keyboard.press("Enter")
    await settle(page, 400)

    # #markback / #backlink: the ✎ beside the passage a block links to scrolls the pad to it and flashes it.
    # Marks show beside windows in view only: bring the pads next to the book (alt+[ moves the window left).
    for _ in range(5):
        await page.keyboard.press("Alt+BracketLeft")
        await page.wait_for_timeout(250)
    await settle(page, 1500)
    marks = page.locator(".desk-pmark.pad")
    back_ok = False
    if await marks.count():
        await marks.first.click()
        await page.wait_for_timeout(250)
        back_ok = await page.locator('.desk-pads [data-block="fx_b_r2"].flash').count() == 1
    results.check("a passage's ✎ mark goes to its pad block and flashes it (#markback, #backlink)", back_ok, await marks.count())

    # The carried question's quiet ◌ beside its passage, logged as surfaced once.
    surfaced = [call for call in await calls(page, "carried_mark") if call["input"].get("event") == "surfaced"]
    results.check("a carried question shows as a quiet ◌ beside its passage and is logged as surfaced once", await page.locator(".desk-pmark.carried").count() >= 1 and len(surfaced) == 1, len(surfaced))

    # The drain: alt+shift+q.
    await page.keyboard.press("Alt+Shift+Q")
    drain = await page.locator(".desk-drain").inner_text()
    results.check("alt+shift+q opens the drain, “Closing <desk>”, with each pad's lines before any question", drain.startswith("Closing “softmax and cross-entropy”") and "keep" in drain and "leave" in drain, drain[:120])
    await shot(page, shots, "pads-drain")
    await page.keyboard.press("Escape")

    # Display math in the companion's bubbles (§13.4): ask about a passage, with a question naming math (the
    # book, beside the pads now, takes the focus first).
    await page.keyboard.press("Alt+l")
    await settle(page, 500)
    await select_passage(page, "largest score")
    await page.keyboard.press("c")
    await settle(page, 400)
    box = page.locator(".desk-companion .input")
    await box.fill("show me the math", timeout=5000)
    await box.press("Enter")
    await page.wait_for_selector(".desk-companion .katex-display", timeout=8000)
    await page.evaluate("document.fonts.ready")
    await settle(page, 700)
    rows = []
    for index in range(await page.locator(".desk-companion .katex-display").count()):
        await page.locator(".desk-companion .katex-display").nth(index).scroll_into_view_if_needed()
        rows += await measure_math(page, ".desk-companion")
    results.check("display math in the companion's answer is never clipped and is fitted or scrolls (§13.4)", rows and all(row["ok"] for row in rows), [row for row in rows if not row["ok"]][:2] or len(rows))
    await shot(page, shots, "companion-math")


async def drag_select(page: Page, text: str) -> None:
    """Select a passage of the book window the way a learner does: a real mouse drag across its text."""
    box = await page.evaluate("""(text) => { const p = [...document.querySelectorAll('[data-desk-window="fx_w_book"] [data-span-id]')].find((e) => e.textContent.includes(text));
      p.scrollIntoView({ block: 'center' }); const r = p.getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height }; }""", text)
    await page.mouse.move(box["x"] + 2, box["y"] + 6)
    await page.mouse.down()
    await page.mouse.move(box["x"] + box["w"] * 0.5, box["y"] + box["h"] - 4, steps=6)
    await page.mouse.move(box["x"] + box["w"] - 4, box["y"] + box["h"] - 4, steps=6)
    await page.mouse.up()


async def run_intent(page: Page, base: str, results: Results, shots: Path | None) -> None:
    """The Reader's intent box over a selection against the desks' c, shift+c and / (a real Reader selection)."""
    await page.goto(f"{base}/desk-harness.html?intent=1")
    await page.wait_for_selector("[data-desk-window]")
    await settle(page, 1500)
    await page.locator('[data-desk-window="fx_w_book"]').click(position={"x": 30, "y": 30})
    await drag_select(page, "largest score")
    await page.wait_for_selector("[data-intent-box]", timeout=4000)
    await shot(page, shots, "intent-armed")
    typed_before = await page.locator("[data-intent-box] input").input_value()
    await page.keyboard.press("c")
    await settle(page, 400)
    rect = await companion_rect(page)
    typed_after = await page.locator("[data-intent-box] input").input_value() if await page.locator("[data-intent-box] input").count() else ""
    results.check("with the intent box shown over a Reader selection, c (focus on the page) summons the companion, typing nothing into the box",
                  rect is not None and rect["mode"] == "anchored" and typed_after == typed_before, [rect, typed_before, typed_after])
    await page.keyboard.press("c")
    await settle(page, 600)
    await page.mouse.click(5, 300)
    await drag_select(page, "every class keeps some")
    await settle(page, 300)
    await shot(page, shots, "intent-second")
    await page.wait_for_selector("[data-intent-box]", timeout=4000)
    await page.keyboard.press("/")
    await settle(page, 400)
    search_open = await page.locator("[data-desk-search]").count() > 0
    results.check("with the intent box shown, / (focus on the page) opens search in context", search_open, search_open)
    await page.keyboard.press("Escape")
    await settle(page, 300)
    # Real typing keeps its keys: with the focus in the box, c is typed there and summons nothing.
    await drag_select(page, "largest score")
    await page.wait_for_selector("[data-intent-box] input", timeout=4000)
    await page.locator("[data-intent-box] input").click()
    await page.keyboard.type("cc/")
    value = await page.locator("[data-intent-box] input").input_value()
    rect = await companion_rect(page)
    results.check("with the focus in the intent box, c and / are typed into it and summon nothing", value.endswith("cc/") and rect is None and await page.locator("[data-desk-search]").count() == 0, [value, rect])


GOAL_BOOK = "[data-desk-window='fx_w_book']"
GOAL_PAPER = "[data-desk-window='fx_w_paper']"


async def mark_facts(page: Page, selector: str) -> dict[str, Any] | None:
    """The first matching mark's colours, width and the gap between it and its passage's text."""
    return await page.evaluate("""(sel) => { const m = document.querySelector(sel); if (!m) return null;
      const cs = getComputedStyle(m), r = m.getBoundingClientRect(), host = m.parentElement, hs = getComputedStyle(host), hr = host.getBoundingClientRect();
      return { bg: cs.backgroundColor, border: cs.borderLeftStyle + ' ' + cs.borderLeftWidth + ' ' + cs.borderLeftColor, w: r.width,
        gap: Math.round((hr.left + parseFloat(hs.borderLeftWidth) + parseFloat(hs.paddingLeft) - r.right) * 10) / 10,
        inset: [Math.round(r.top - hr.top), Math.round(hr.bottom - r.bottom)] }; }""", selector)


async def why_after_hover(page: Page, selector: str) -> dict[str, Any] | None:
    mark = page.locator(selector).first
    await mark.scroll_into_view_if_needed()
    await settle(page, 300)
    await mark.hover()
    await settle(page, 450)
    return await page.evaluate("""() => { const w = document.querySelector('.gwhy.on'); if (!w) return null; const cs = getComputedStyle(w);
      return { head: w.querySelector('.gwh').textContent, body: w.querySelector('.gwr').textContent,
        coverage: w.querySelector('.gwc')?.textContent ?? null, edge: cs.borderLeftStyle, width: w.getBoundingClientRect().width,
        bg: cs.backgroundColor }; }""")


async def run_goal(page: Page, base: str, results: Results, shots: Path | None) -> None:
    """The goal lens (RD6, spec §12): the RD6 deep links' equivalents on the synthetic goal (`?goal=1`)."""
    await page.goto(f"{base}/desk-harness.html?goal=1")
    await page.wait_for_selector(".goalband")
    await settle(page, 2000)
    await shot(page, shots, "goal-frame")
    band = await page.evaluate("() => document.querySelector('.goalband').getBoundingClientRect().toJSON()")
    results.check("#goal=frame: the band sits under the top bar, 50 px high", band["y"] == 38 and band["height"] == 50, band)
    core = await mark_facts(page, f"{GOAL_BOOK} .gm.gl-core")
    results.check("#goal=frame: a core passage has a solid 3 px purple bar 8 px left of its text",
                  bool(core) and core["bg"] == "rgb(91, 74, 154)" and core["w"] == 3 and core["gap"] == 8 and core["inset"] == [5, 5], core)
    sup = await mark_facts(page, f"{GOAL_BOOK} .gm.gl-sup")
    results.check("#goal=frame: a supporting passage has the bar at 34 %", bool(sup) and sup["bg"] == "rgba(91, 74, 154, 0.34)", sup)
    skip = await mark_facts(page, f"{GOAL_BOOK} .gm.gl-skip")
    results.check("#goal=frame: a skippable passage has a dotted 1 px line", bool(skip) and skip["border"] == "dotted 1px rgb(185, 178, 204)", skip)
    dimmed = await page.evaluate(f"() => [...document.querySelectorAll(\"{GOAL_BOOK} [data-span-id].gl-dim\")].map((el) => getComputedStyle(el).color)")
    results.check("#goal=frame: skippable text is dimmed (never hidden)", bool(dimmed) and set(dimmed) == {"rgb(142, 137, 127)"}, dimmed[:3])
    callout = await page.evaluate(f"() => {{ const c = document.querySelector(\"{GOAL_BOOK} .callout.gcall\"); return c ? {{ lab: c.querySelector('.lab').textContent, bg: getComputedStyle(c).backgroundColor }} : null; }}")
    results.check("#goal=frame: a core section opens with a dark callout in LearnLoop's voice",
                  bool(callout) and callout["lab"] == "◎ for your goal · core" and callout["bg"] == "rgb(29, 29, 32)", callout)
    lens_calls = await calls(page, "goal_lens")
    asked = sorted(call["input"]["extractionId"] for call in lens_calls)
    results.check("one whole-reading goal.lens per reading in view, none for a paused window",
                  asked == sorted(set(asked)) and "fx_ext_attention" not in asked and all(set(call["input"]) == {"goalId", "extractionId"} for call in lens_calls), asked)
    judged = await calls(page, "curriculum_path")
    results.check("opening the goal starts what it owes once (curriculum.path, judge: true)", [call["input"].get("judge") for call in judged] == [True], judged)
    await page.locator(f"{GOAL_BOOK} [data-span-id='fx_ext_softmax_s1_2']").scroll_into_view_if_needed()
    await settle(page, 800)
    here = await page.evaluate("() => document.querySelector('[data-goal-here]').textContent")
    results.check("#goal=frame: you are reading maps the focused window's passage through the lens", "Turn scores into softmax weights" in here, here)

    shelf = await page.evaluate("""() => { const row = document.querySelector("[data-shelf-window='fx_w_book']"); if (!row) return null;
      const mark = row.querySelector('.gm.sh'); return { cls: row.className, bg: mark ? getComputedStyle(mark).backgroundColor : null,
        line: row.querySelector('.gwl')?.textContent ?? null, ranges: row.querySelectorAll('.bar .gr').length }; }""")
    results.check("#goal=frame: the book's shelf row carries the bar at its right edge, what it is for, and the path's ranges",
                  bool(shelf) and shelf["bg"] == "rgb(169, 159, 208)" and shelf["line"] == "◎ primary for 2 of your LOs" and shelf["ranges"] >= 1, shelf)
    video = await page.evaluate("""() => { const w = document.querySelector("[data-desk-window='fx_w_video']"); if (!w) return null;
      const group = w.querySelector('.tp.g-sup'); const mark = group?.querySelector('.tx > .gm.gl-tx'); const tx = group?.querySelector('.tx');
      const dim = w.querySelector('.tp.gl-dim [data-transcript-span]');
      return { mark: mark ? { bg: getComputedStyle(mark).backgroundColor, gap: Math.round((tx.getBoundingClientRect().left - mark.getBoundingClientRect().right) * 10) / 10 } : null,
        head: w.querySelector('[data-goal-head]')?.textContent ?? null, segments: w.querySelectorAll('[data-goal-track] .gseg').length,
        segColour: w.querySelector('[data-goal-track] .gseg') ? getComputedStyle(w.querySelector('[data-goal-track] .gseg')).backgroundColor : null,
        dimmed: dim ? getComputedStyle(dim).color : null }; }""")
    results.check("#goal=video: transcript passages carry the marks, the head says where the video sits, the track draws the path's ranges",
                  bool(video) and bool(video["mark"]) and video["mark"]["bg"] == "rgba(91, 74, 154, 0.34)" and video["mark"]["gap"] == 5
                  and (video["head"] or "").startswith("◎ on your path") and video["segments"] == 3
                  and video["segColour"] == "rgba(169, 159, 208, 0.45)" and video["dimmed"] == "rgb(142, 137, 127)", video)
    await page.keyboard.press("Shift+C")
    await settle(page, 700)
    context = await page.evaluate("() => { const g = document.querySelector('.desk-companion .ctx .gctx'); return g ? { text: g.textContent, colour: getComputedStyle(g).color } : null; }")
    results.check("the companion keeps the goal in view", bool(context) and context["text"] == "◎ goal in context" and context["colour"] == "rgb(169, 159, 208)", context)
    await page.keyboard.press("Shift+C")
    await settle(page, 500)

    why = await why_after_hover(page, f"{GOAL_BOOK} .gm.gl-core")
    await shot(page, shots, "goal-why")
    results.check("#goal=why: the why on a core passage: the level, For <goal>: the reason, the coverage line",
                  bool(why) and why["head"] == "core for your goal" and why["body"].startswith("For softmax for attention:")
                  and (why["coverage"] or "").startswith("coverage: introduces") and why["width"] <= 330, why)
    await page.mouse.move(5, 600)
    await settle(page, 400)
    why = await why_after_hover(page, f"{GOAL_BOOK} .gm.gl-sup")
    await shot(page, shots, "goal-whysup")
    results.check("#goal=whysup: the why on a supporting passage", bool(why) and why["head"] == "supporting" and why["edge"] == "solid", why)
    await page.mouse.move(5, 600)
    await settle(page, 400)
    why = await why_after_hover(page, f"{GOAL_BOOK} .gm.gl-skip")
    await shot(page, shots, "goal-whyskip")
    results.check("#goal=whyskip: the why on a skippable passage, its edge dotted",
                  bool(why) and why["head"] == "skippable for now" and why["edge"] == "dotted", why)
    await page.keyboard.press("Escape")
    await page.mouse.move(5, 600)
    await settle(page, 400)

    await page.click("[data-gdepth='get_the_idea']")
    await settle(page, 1200)
    depth = await calls(page, "curriculum_set_depth")
    later = await page.evaluate("() => document.querySelectorAll('.gb-stops .gs.later').length")
    results.check("#goal=basics: get the idea is set through curriculum.set_depth; deeper LOs dim on the band",
                  [call["input"].get("depth") for call in depth] == ["get_the_idea"] and later == 2, {"depth": depth, "later": later})
    why = await why_after_hover(page, f"{GOAL_BOOK} .gm.gl-later")
    await shot(page, shots, "goal-basics")
    results.check("#goal=basics: a prerequisite's passage is later, kept at the deeper depth",
                  bool(why) and why["head"] == "later · kept at learn to use it" and why["edge"] == "dotted", why)
    await page.mouse.move(5, 600)
    await page.click("[data-gdepth='learn_to_use_it']")
    await settle(page, 1200)

    await page.mouse.click(800, 600)
    await page.keyboard.press("p")
    await settle(page, 600)
    await shot(page, shots, "goal-path")
    path = await page.evaluate("() => { const o = document.querySelector('[data-goal-path]'); if (!o) return null; const r = o.getBoundingClientRect();"
                               " return { rows: o.querySelectorAll('[data-gp-lo]').length, box: [r.x, r.y, r.width, r.height], focused: document.activeElement === o }; }")
    results.check("#goal=path: p opens the path view (one row per LO, the reference's frame)",
                  bool(path) and path["rows"] == 5 and path["box"] == [300, 70, 1240, 770] and path["focused"], path)
    await page.click("[data-gp-skip] .gp-anyway")
    await settle(page, 900)
    chosen = await calls(page, "goal_section_choice")
    lit = await page.evaluate(f"() => document.querySelectorAll(\"{GOAL_BOOK} [data-span-id^='fx_ext_softmax_s6_'].gl-dim\").length")
    results.check("#goal=path: read it anyway is stored (goal.section_choice) and the section stays lit",
                  [call["input"].get("choice") for call in chosen] == ["read_anyway"] and lit == 0, {"chosen": chosen, "dimmed": lit})
    await page.keyboard.press("Escape")
    await settle(page, 300)
    closed = await page.evaluate("() => !document.querySelector('[data-goal-path]')")
    results.check("#goal=path: esc closes the path view", closed)

    await page.click(".desk-shelf >> text=Attention as averaging (a note)")
    await settle(page, 1800)
    await shot(page, shots, "goal-paper")
    paper = await mark_facts(page, f"{GOAL_PAPER} .gm.gl-core")
    head = await page.evaluate(f"() => document.querySelector(\"{GOAL_PAPER} .gpcall\")?.textContent ?? null")
    results.check("#goal=paper: the paper's marks keep 11 px from the text and its head says what it is for",
                  bool(paper) and paper["gap"] == 11 and bool(head) and "for your goal · core:" in head, {"mark": paper, "head": head})

    await page.click(".desk-shelf >> text=notes")
    await settle(page, 1800)
    await shot(page, shots, "goal-pads")
    line = await page.evaluate("() => document.querySelector('[data-goal-padline]')?.textContent ?? null")
    results.check("#goal=pads: a pad stack says what it is for, from its pads' anchors", bool(line) and "for your goal" in line, line)

    await page.click("[data-gdim]")
    await page.mouse.move(800, 600)
    await settle(page, 500)
    await shot(page, shots, "goal-nodim")
    undimmed = await page.evaluate("() => ({ dims: document.querySelectorAll('.gl-dim').length, label: document.querySelector('[data-gdim]').textContent })")
    results.check("nodim: dimming off shows every passage at full colour", undimmed["dims"] == 0 and undimmed["label"].endswith("shown"), undimmed)


LESSON = '[data-lesson-paper="fx_lesson_softmax"]'


async def lesson_calls(page: Page) -> dict[str, list[dict[str, Any]]]:
    return {name: await calls(page, name) for name in ("lesson_turn", "lesson_view", "lesson_list")}


async def scroll_stack_to(page: Page, key: str) -> None:
    """Scroll the pad stack until a tab's paper is at the top of its scroller."""
    await page.locator(".desk-pads .pscroller").evaluate(
        "(s, key) => { const p = s.querySelector(`.paper[data-pad=\"${key}\"]`); if (p) s.scrollTop = Math.max(0, p.offsetTop - 120); }", key)
    await settle(page, 700)


async def run_lesson(page: Page, base: str, results: Results, shots: Path | None) -> None:
    """Teacher lessons as windows (RD9a, spec §11.1): a finished lesson replayed in its stack tab with no turn, the
    paused window reading nothing, the additions under it, and a lesson asked for from a selection landing in the
    desk's stack (`?lesson=1`)."""
    await page.goto(f"{base}/desk-harness.html?lesson=1")
    await page.wait_for_selector("[data-desk-window]")
    await settle(page, 1500)
    before = await lesson_calls(page)
    results.check("while the pad stack is out of view its lesson is not read and no turn is made (a paused window)",
                  before["lesson_view"] == [] and before["lesson_turn"] == [], {k: len(v) for k, v in before.items()})
    for _ in range(6):
        await page.keyboard.press("Alt+l")
        await page.wait_for_timeout(250)
    await page.wait_for_selector(f"{LESSON} [data-testid='lesson-view']")
    await page.evaluate("document.fonts.ready")
    await scroll_stack_to(page, "lesson:fx_lesson_softmax")
    await shot(page, shots, "lesson-review")
    seen = await lesson_calls(page)
    results.check("the finished lesson is read once with lesson.view and replayed with no turn (review makes no model call)",
                  [c["input"] for c in seen["lesson_view"]] == [{"lessonId": "fx_lesson_softmax"}] and seen["lesson_turn"] == [], {k: len(v) for k, v in seen.items()})
    tab = await page.evaluate("""() => { const t = document.querySelector('[data-pad-tab="lesson:fx_lesson_softmax"]'); return t ? {
        title: t.querySelector('.tt').textContent, meta: t.querySelector('.tm').textContent, open: t.classList.contains('open') } : null; }""")
    results.check("the lesson's tab reads “Teacher lesson · <topic>” and “made <date> from your <what>”",
                  bool(tab) and tab["title"] == "Teacher lesson · softmax + cross-entropy" and tab["meta"] == "made 21 Nov from your question", tab)
    review = await page.evaluate(f"""() => {{ const p = document.querySelector('{LESSON}'); return {{
        modes: [...p.querySelectorAll('.lmodes button')].map((b) => [b.textContent, b.classList.contains('on')]),
        line: p.querySelector('.lmodes .lmd').textContent,
        kinds: ['lesson-check', 'lesson-learner', 'lesson-check-result', 'lesson-close'].filter((id) => p.querySelector(`[data-testid="${{id}}"]`)),
        inputs: p.querySelectorAll('.lframe textarea, .lframe input').length,
        stop: [...p.querySelectorAll('.lframe button')].some((b) => b.textContent === 'Stop the lesson'),
        additions: p.querySelector('.laddl .lah')?.textContent ?? null,
        note: !!p.querySelector('[data-block="fx_b_add1"]'),
        reading: getComputedStyle(p.querySelector('.ll-article')).fontFamily.split(',')[0],
        head: getComputedStyle(p.querySelector('.lhead')).fontFamily.split(',')[0] }}; }}""")
    results.check("review shows what was recorded (the check, your answer, its result, the close card) and nothing that starts a turn",
                  review["kinds"] == ["lesson-check", "lesson-learner", "lesson-check-result", "lesson-close"] and review["inputs"] == 0 and not review["stop"], review)
    results.check("the modes are review (on) and your additions; redo and extend are not shown",
                  review["modes"] == [["review", True], ["your additions", False]] and review["line"] == "your committed answers and the reveals, as you left them", review["modes"])
    results.check("the learner's notes under the lesson show beneath its review", review["note"] and review["additions"] == "your additions under this lesson", review)
    results.check("interface text is JetBrains Mono, the lesson's reading text Literata",
                  "JetBrains Mono" in review["head"] and "Literata" in review["reading"], [review["head"], review["reading"]])
    rows = await measure_math(page, f"{LESSON} .lframe")
    results.check("display math in the lesson is never clipped (§13.4)", bool(rows) and all(row["ok"] for row in rows), [r for r in rows if not r["ok"]][:2] or len(rows))

    # Your additions: the lesson folds to its head, the notes stay, and a new line goes to the lesson's additions pad.
    await page.locator(f"{LESSON} .lmodes button[data-lmode='additions']").click()
    await settle(page, 300)
    await page.locator(f"{LESSON} .laddl .pb.jot").click()
    await page.wait_for_selector("[data-pad-editor] textarea")
    await page.keyboard.type("a note under the lesson")
    await page.keyboard.press("Enter")
    await page.keyboard.press("Escape")
    await settle(page, 2500)
    batches = await page.evaluate("() => window.__deskHarness.server.padBatches.filter((b) => b.padId === 'fx_pad_lesson_adds').flatMap((b) => b.ops.map((o) => o.op))")
    results.check("a note under the lesson is written to its lesson_additions pad through pad.apply", "insert_block" in batches, batches)
    await shot(page, shots, "lesson-additions")

    # A lesson asked for from a selection (as the app asks while the desks are its place) lands in the desk's stack.
    await page.evaluate("() => window.__deskLessonAsk({ kind: 'open', entry: 'reader_selection', selection: { extractionId: 'fx_ext_softmax', spanIds: ['fx_ext_softmax_s1_3'] } })")
    await page.wait_for_selector('.desk-pads [data-pad-tab^="lesson-opening:"]', timeout=3000)
    opening = await page.evaluate("() => document.querySelector('.desk-pads [data-pad-tab^=\"lesson-opening:\"] .tm').textContent")
    await shot(page, shots, "lesson-opening")
    await page.wait_for_selector('.desk-pads [data-pad-tab="lesson:fx_lesson_opened_1"]', timeout=5000)
    await settle(page, 2500)
    stack = await page.evaluate("() => window.__deskHarness.server.state().desks.find((d) => d.deskId === 'fx_desk_softmax').slots.flatMap((s) => s.windows).find((w) => w.windowId === 'fx_w_pads').stack")
    after = await lesson_calls(page)
    turns = [c["input"] for c in after["lesson_turn"]]
    results.check("a lesson asked for from a selection opens in the desk's stack and is stored there once its turn returns",
                  opening == "opening…" and {"kind": "lesson", "lessonId": "fx_lesson_opened_1"} in stack
                  and len(turns) == 1 and turns[0].get("entry") == "reader_selection", [opening, stack, turns])
    reads = [c["input"]["lessonId"] for c in after["lesson_view"]]
    results.check("the window that opened it goes on showing it (no second read of the new lesson)", "fx_lesson_opened_1" not in reads, reads)
    await shot(page, shots, "lesson-opened")


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
    parser.add_argument("--only", default="", help="comma-separated runs (desks, overview, companion, intent, pads, latex, goal, lesson, preview); all by default")
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
            # Playwright hides scrollbars in headless Chromium; the display-math checks need them drawn, as the
            # app's webview draws them (a wide equation's scroller must show its bar).
            with_bars = await playwright.chromium.launch(headless=True, ignore_default_args=["--hide-scrollbars"])
            runners = ("desks", "overview", "companion", "intent", "pads", "latex", "goal", "lesson", "preview")
            chosen = [name for name in args.only.split(",") if name] or list(runners)
            for runner in (name for name in runners if name in chosen):
                context = await (with_bars if runner in ("pads", "latex", "lesson") else browser).new_context(viewport=VIEWPORT)
                await context.route(lambda url: not url.startswith(base), route_outside)
                page = await context.new_page()
                try:
                    if runner == "desks":
                        await run_desks(page, base, results, args.shots)
                    elif runner == "overview":
                        await run_overview(page, base, results, args.shots)
                    elif runner == "companion":
                        await run_companion(page, base, results, args.shots)
                    elif runner == "intent":
                        await run_intent(page, base, results, args.shots)
                    elif runner == "pads":
                        await run_pads(page, base, results, args.shots)
                    elif runner == "latex":
                        await run_latex(page, base, results, args.shots)
                    elif runner == "goal":
                        await run_goal(page, base, results, args.shots)
                    elif runner == "lesson":
                        await run_lesson(page, base, results, args.shots)
                    else:
                        await run_preview(page, base, results)
                except Exception as error:  # noqa: BLE001 - a broken step is a failed check, and the report still prints
                    results.check(f"the {runner} run reached its end", False, str(error).splitlines()[0])
                await context.close()
            await browser.close()
            await with_bars.close()
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
