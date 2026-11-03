"""The page's own reading of a book's block (spec_reader_rw5c_checked_labels_v1 §5.2, §5.3).

The Reader shows a block with ``MarkdownMath``: its markdown pipeline finds the math
elements, and KaTeX renders each. So the only reading that cannot disagree with the page
is theirs, and this runs both in a sealed engine and returns what they found, as data:

* :meth:`Trees.page_math`: the math elements of a block, from the same normalization,
  remark plugins and remark-rehype options as the page (``src/render/pageMathSegments.ts``,
  bundled by ``sketch-engine/markdown/build.mjs``; a reference definition, a link title,
  a code span or an unreferenced footnote is simply not one);
* :meth:`Trees.parse`: the tree KaTeX's parser builds for one of them (vendored from
  ``apps/learnloop-tauri``'s lock; ``tests/test_rw5c_katex_tree.py`` pins version and digest).

:mod:`.book_math` translates that tree and nothing else.

**The engine.** The same harness and QuickJS as the sketch engine (:mod:`.sketch_engine`:
the deny-all WASI shim, the same memory cap and wasmtime backstops), built as a variant by
``apps/learnloop-tauri/sketch-engine/build.py`` from the same pinned sources. It differs in
two things. It has the RegExp intrinsic, because KaTeX's lexer is a regular expression and
a sketch never gets one (``SyntaxError: RegExp are not supported``). And it has
:data:`BOOK_MATH_TICKS_PER_CALL` interrupt ticks per call, not a sketch's one frame's worth,
because it runs pinned programs over book text, never a model's program, and markdown is real
work on a long paragraph. The sketch engine's bytes and digest are untouched, so no stored
sketch re-verifies.

**The settings** are the page's: ``rehype-katex`` with no options (``MarkdownMath.tsx``)
calls KaTeX once per math element, ``throwOnError`` true, ``displayMode`` by the
delimiter, every other setting at its default, ``macros`` a new object each time. So a
definition in one segment or block never reaches another (a test pins this), and one
loaded engine can parse every segment of a check.

**The cost** (review file): loading takes about 35 ms in a process that has already
compiled the module (about 120 ms for that once), a segment under a millisecond and a block
about one. A check opens one :class:`Trees` at build or recheck time, never on a Reader read.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

_ENGINE_DIR = Path(__file__).resolve().parents[3] / "apps" / "learnloop-tauri" / "sketch-engine"
#: The tracked artifact; ``engine.lock.json``'s ``variants.book-math.output`` records the same digest.
KATEX_ENGINE_PATH = _ENGINE_DIR / "book-math-engine.wasm"
KATEX_ENGINE_SHA256 = "880bf1c86af1de2017c5119235d846e1ab4a1637c9bb46f094ec8e9360f8f2b2"
#: keep (deterministic work cap, compiled in): the variant's interrupt ticks per call. Measured
#: (review file): the longest block of the coverage corpus, 5,879 characters, fits; a
#: call at the cap is well under a second, inside wasmtime's backstops.
BOOK_MATH_TICKS_PER_CALL = 512
#: The vendored parser, text under its MIT licence (``katex/LICENSE``): byte for byte
#: the ``dist/katex.min.js`` of the npm package ``package-lock.json`` locks.
KATEX_PATH = _ENGINE_DIR / "katex" / "katex.min.js"
KATEX_VERSION = "0.16.47"
KATEX_SHA256 = "a29d2961d3146de5949d78ac7c1a9d93ae54955bad22a6db4fbe836e88e8bf48"
#: The page's markdown pipeline as text, its packages under their licences (``markdown/LICENSES.txt``):
#: what ``markdown/build.mjs`` bundles from ``package-lock.json``'s packages (a vitest rebuilds it and compares).
MARKDOWN_PATH = _ENGINE_DIR / "markdown" / "page-markdown.js"
MARKDOWN_SHA256 = "29fd5be75b4ebba5cddcf63badb71c03013138177d91cf8812a11b9157a835a6"

#: The program beside them: one reading per call, nothing kept. ``loc`` holds the whole
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
  if (p.markdown !== undefined) { return {math: pageMarkdown.pageMathSegments(p.markdown)}; }
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
                 source: Path = KATEX_PATH, source_sha256: str = KATEX_SHA256,
                 markdown: Path = MARKDOWN_PATH, markdown_sha256: str = MARKDOWN_SHA256) -> None:
        self._path, self._expected = path, expected
        self._programs = ((source, source_sha256), (markdown, markdown_sha256))
        self._engine: Any = None

    def _open(self) -> Any:
        if self._engine is None:
            try:
                # Imported here: the sidecar's start imports neither wasmtime nor the engine (RW5d P2).
                from learnloop.figures import sketch_engine as SE

                texts = [program.read_bytes() for program, _digest in self._programs]
                if [hashlib.sha256(text).hexdigest() for text in texts] != [digest for _program, digest in self._programs]:
                    raise TreeRefused("engine_unavailable")
                engine = SE.SketchEngine(path=self._path, expected=self._expected)
            except TreeRefused:
                raise
            except Exception as exc:  # noqa: BLE001 - no file, wrong digest, wasmtime missing: fail closed
                raise TreeRefused("engine_unavailable") from exc
            try:
                engine.load("\n".join(text.decode("utf-8") for text in texts) + _PROGRAM)
            except BaseException as exc:
                engine.close()
                raise TreeRefused("engine_unavailable") from exc
            self._engine = engine
        return self._engine

    def _ask(self, question: dict[str, Any]) -> dict[str, Any]:
        from learnloop.figures import sketch_engine as SE

        engine = self._open()
        try:
            return json.loads(engine.view_text(question, index=0))
        except SE.SketchRunError as exc:
            if exc.trap:
                self.close()
            raise TreeRefused("not_rendered" if exc.kind == "error" else "too_long") from exc
        except RecursionError as exc:
            raise TreeRefused("too_long") from exc

    def page_math(self, markdown: str) -> list[dict[str, Any]]:
        """The math elements the page finds in a block: ``latex``, what the page gives KaTeX; ``start`` and
        ``end``, its place in ``markdown``; ``display``, how the page renders it. Or :class:`TreeRefused`."""

        return self._ask({"markdown": markdown})["math"]

    def parse(self, tex: str, *, display: bool = False) -> list[dict[str, Any]]:
        """KaTeX's tree of ``tex`` under the page's settings, or :class:`TreeRefused`."""

        answer = self._ask({"tex": tex, "display": display})
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
    "BOOK_MATH_TICKS_PER_CALL",
    "KATEX_ENGINE_PATH",
    "KATEX_ENGINE_SHA256",
    "KATEX_PATH",
    "KATEX_SHA256",
    "KATEX_VERSION",
    "MARKDOWN_PATH",
    "MARKDOWN_SHA256",
    "TreeRefused",
    "Trees",
]
