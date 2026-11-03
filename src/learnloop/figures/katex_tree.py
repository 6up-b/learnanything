"""KaTeX's own parse tree of a book's equation (spec_reader_rw5c_checked_labels_v1 §5.3).

The Reader shows a source's math with KaTeX, so the only reading of a segment that
cannot disagree with the page is KaTeX's. This runs the KaTeX the Reader renders
with (vendored from ``apps/learnloop-tauri``'s lock; ``tests/test_rw5c_katex_tree.py``
pins version and digest to it) in a sealed engine, and returns the tree its parser
builds, as data. :mod:`.book_math` translates that tree and nothing else.

**The engine.** The same harness, QuickJS and caps as the sketch engine
(:mod:`.sketch_engine`: the deny-all WASI shim, the same interrupt ticks and memory
cap, the same wasmtime backstops), built as a variant by
``apps/learnloop-tauri/sketch-engine/build.py`` from the same pinned sources. It
differs in one thing: it has the RegExp intrinsic, because KaTeX's lexer is a regular
expression and a sketch never gets one (``SyntaxError: RegExp are not supported``). The
sketch engine's bytes and digest are untouched, so no stored sketch re-verifies.

**The settings** are the page's: ``rehype-katex`` with no options (``MarkdownMath.tsx``)
calls KaTeX once per math element, ``throwOnError`` true, ``displayMode`` by the
delimiter, every other setting at its default, ``macros`` a new object each time. So a
definition in one segment or block never reaches another (a test pins this), and one
loaded engine can parse every segment of a check.

**The cost** (review file): loading takes about 20 ms in a process that has already
compiled the module (about 120 ms for that once) and a segment under a millisecond. A
check opens one :class:`Trees` at build or recheck time, never on a Reader read.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

_ENGINE_DIR = Path(__file__).resolve().parents[3] / "apps" / "learnloop-tauri" / "sketch-engine"
#: The tracked artifact; ``engine.lock.json``'s ``variants.book-math.output`` records the same digest.
KATEX_ENGINE_PATH = _ENGINE_DIR / "book-math-engine.wasm"
KATEX_ENGINE_SHA256 = "f2b6894c68f7c8eebbecaecc869a5cac83a1de724494c1ccf1aa50bf3364ff8a"
#: The vendored parser, text under its MIT licence (``katex/LICENSE``): byte for byte
#: the ``dist/katex.min.js`` of the npm package ``package-lock.json`` locks.
KATEX_PATH = _ENGINE_DIR / "katex" / "katex.min.js"
KATEX_VERSION = "0.16.47"
KATEX_SHA256 = "a29d2961d3146de5949d78ac7c1a9d93ae54955bad22a6db4fbe836e88e8bf48"

#: The program beside KaTeX: one parse per call, nothing kept. ``loc`` holds the whole
#: lexer, so only its offsets cross (as ``at``); a definition reaching ``macros`` is
#: reported, though the reader refuses every one before it asks.
_PROGRAM = """
function plain(node) {
  if (Array.isArray(node)) { return node.map(plain); }
  if (node === null || typeof node !== "object") { return node; }
  var out = {};
  for (var key in node) {
    if (key === "loc") { if (node.loc) { out.at = [node.loc.start, node.loc.end]; } }
    else { out[key] = plain(node[key]); }
  }
  return out;
}
function view(state, p) {
  var macros = {};
  try {
    var tree = katex.__parse(p.tex, {displayMode: p.display, throwOnError: true, macros: macros});
    return {tree: plain(tree), macros: Object.keys(macros).length};
  } catch (error) {
    if (error && error.name === "ParseError") { return {refused: true}; }
    throw error;
  }
}
"""


class TreeRefused(Exception):
    """No tree, and why as the reader's closed key: ``not_rendered`` (KaTeX refuses; the page shows an
    error), ``macro_definition``, ``too_long`` (over a cap) or ``engine_unavailable`` (no engine here)."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class Trees:
    """One loaded engine for one check (not thread-safe, as :class:`.sketch_engine.SketchEngine`).
    It opens on the first parse; a trap (over a wasm backstop) drops it and the next parse opens a new one."""

    def __init__(self, *, path: Path = KATEX_ENGINE_PATH, expected: str = KATEX_ENGINE_SHA256,
                 source: Path = KATEX_PATH, source_sha256: str = KATEX_SHA256) -> None:
        self._path, self._expected = path, expected
        self._source, self._source_sha256 = source, source_sha256
        self._engine: Any = None

    def _open(self) -> Any:
        if self._engine is None:
            try:
                # Imported here: the sidecar's start imports neither wasmtime nor the engine (RW5d P2).
                from learnloop.figures import sketch_engine as SE

                text = self._source.read_bytes()
                if hashlib.sha256(text).hexdigest() != self._source_sha256:
                    raise TreeRefused("engine_unavailable")
                engine = SE.SketchEngine(path=self._path, expected=self._expected)
            except TreeRefused:
                raise
            except Exception as exc:  # noqa: BLE001 - no file, wrong digest, wasmtime missing: fail closed
                raise TreeRefused("engine_unavailable") from exc
            try:
                engine.load(text.decode("utf-8") + _PROGRAM)
            except BaseException as exc:
                engine.close()
                raise TreeRefused("engine_unavailable") from exc
            self._engine = engine
        return self._engine

    def parse(self, tex: str, *, display: bool = False) -> list[dict[str, Any]]:
        """KaTeX's tree of ``tex`` under the page's settings, or :class:`TreeRefused`."""

        from learnloop.figures import sketch_engine as SE

        engine = self._open()
        try:
            answer = json.loads(engine.view_text({"tex": tex, "display": display}, index=0))
        except SE.SketchRunError as exc:
            if exc.trap:
                self.close()
            raise TreeRefused("not_rendered" if exc.kind == "error" else "too_long") from exc
        except RecursionError as exc:
            raise TreeRefused("too_long") from exc
        if answer.get("refused"):
            raise TreeRefused("not_rendered")
        if answer.get("macros"):
            raise TreeRefused("macro_definition")
        return answer["tree"]

    def close(self) -> None:
        engine, self._engine = self._engine, None
        if engine is not None:
            engine.close()

    def __enter__(self) -> "Trees":
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.close()


__all__ = [
    "KATEX_ENGINE_PATH",
    "KATEX_ENGINE_SHA256",
    "KATEX_PATH",
    "KATEX_SHA256",
    "KATEX_VERSION",
    "TreeRefused",
    "Trees",
]
