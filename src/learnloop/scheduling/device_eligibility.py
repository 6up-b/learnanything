"""Mobile PR-6: which items a device can answer (``spec_mobile_tailnet_v1`` §6.4).

A phone renders text. An item whose stimulus needs a page, a picture or a long
conversation is kept for the desktop (D6): it is filtered from the phone's queue
before the offer is logged, the phone shows how many wait, and a by-id open is
refused with ``desktop_only``. :func:`ineligibility_reason` is the one decision;
the sidecar asks it at every door (``learnloop_sidecar.serving``), with the device
class from the request origin (§6.8), never from a parameter.

**What is structural and what is not.** The reasons read the item's contract and
the parsed Markdown of its prompt, as the renderer resolves it, reference
definitions included: an image, an ``llpdf://`` link, a link to a file in the vault.
Text cues ("see the figure below") are never read here. Phrase lists
misfire, so a suspected figure is not filtered: M2's report logs it as
``suspected_figure`` for review (§6.4). A test pins that such a prompt stays
eligible.

**Reasons that are not here, on purpose.** Each was checked when this landed:

* A diagnostic probe is served on the phone only as far as its contract (§6.4, M2):
  an active contract is not rendered there, which is the client's rule, because the
  contract is per serve, not per item.
* A workbench problem is a way of answering, not a kind of item. Its item is
  ordinary text, its open problem stays on the desktop, and an answer from the
  phone counts its carried help as any other surface does.
* A delayed lesson check (DL2's Check once on a vault item) is an ordinary item.
  Only a lesson's own held check item is the lesson's (``lesson_check``).
* A figure a learner asks for ("Show me") is help beside an item, not its stimulus.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from functools import lru_cache
from typing import Any

from markdown_it import MarkdownIt
from markdown_it.token import Token

from learnloop.vault.lifecycle import minted_for_lesson

DESKTOP = "desktop"
PHONE = "phone"

#: Practice modes the phone never serves. A dialogue microprobe is a block of
#: linked turns with its own surface (probe redesign §8.1).
DESKTOP_ONLY_MODES = frozenset({"diagnostic_microprobe"})
#: Multi-turn on a phone keyboard, until voice teach-back (M3).
_TEACH_BACK_MODE = "teach_back"

ERROR_HUNT = "error_hunt"
LADDERED_STEM = "laddered_stem"
MULTI_TURN_TEACH_BACK = "multi_turn_teach_back"
DESKTOP_ONLY_MODE = "desktop_only_mode"
LESSON_CHECK = "lesson_check"
EMBEDS_IMAGE = "embeds_image"
LINKS_LLPDF = "links_llpdf"
REFERENCES_ITEM_ASSET = "references_item_asset"

#: What Markdown shows as text: fenced and inline code, and display and inline
#: math, where ``n![k](x)`` is a formula and ``llpdf://`` an example.
_LITERAL_TEXT = re.compile(
    r"^(?P<fence>`{3,}|~{3,})[^\n]*\n.*?^(?P=fence)\s*$"
    r"|`[^`\n]*`"
    r"|\$\$.*?\$\$"
    r"|\$[^$\n]*\$"
    r"|\\\(.*?\\\)"
    r"|\\\[.*?\\\]",
    re.MULTILINE | re.DOTALL,
)
_HTML_IMAGE = re.compile(r"<img\b", re.IGNORECASE)
_URL_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
#: Schemes that name a file on this machine rather than a page anywhere.
_LOCAL_SCHEMES = ("file:", "asset:")
_FILE_SUFFIX = re.compile(r"\.[A-Za-z0-9]{1,8}$")

#: CommonMark, as the renderer's remark parser reads it (Codex review F3): only a
#: parser knows that ``![graph]`` is an image when ``[graph]: figures/graph.png``
#: is defined further down and bracketed text when it is not. Math has no meaning
#: to it, so ``_LITERAL_TEXT`` still goes first. ``validateLink`` is opened because
#: the default drops ``file:`` links, the very thing asked about here.
_MARKDOWN = MarkdownIt("commonmark")
_MARKDOWN.validateLink = lambda _url: True


def _is_item_asset(target: str) -> bool:
    """A link to a file: a local scheme, or a relative target that is a path.
    ``[0,1](x)`` is an interval and a function, not a link to anything."""

    if target.lower().startswith(_LOCAL_SCHEMES):
        return True
    if _URL_SCHEME.match(target) or target.startswith("#"):
        return False
    return "/" in target or _FILE_SUFFIX.search(target) is not None


def _rendered_tokens(tokens: Iterable[Token]) -> Iterator[Token]:
    for token in tokens:
        yield token
        if token.children:
            yield from _rendered_tokens(token.children)


@lru_cache(maxsize=4096)
def _prompt_reason(prompt: str) -> str | None:
    """Read per candidate on every phone build, and a prompt's parse never changes."""

    text = _LITERAL_TEXT.sub(" ", prompt or "")
    if "llpdf://" in text.lower():
        return LINKS_LLPDF
    if "[" not in text and "<" not in text:
        return None
    links_asset = False
    for token in _rendered_tokens(_MARKDOWN.parse(text)):
        if token.type == "image" or (token.type in ("html_inline", "html_block") and _HTML_IMAGE.search(token.content)):
            return EMBEDS_IMAGE
        if token.type == "link_open" and _is_item_asset(str(token.attrGet("href") or "")):
            links_asset = True
    return REFERENCES_ITEM_ASSET if links_asset else None


def ineligibility_reason(vault: Any, item: Any, device_class: str) -> str | None:
    """Why ``device_class`` cannot answer ``item``, or None when it can.

    Only ``phone`` has reasons: a desktop request (no origin) never reaches a
    filter, and asks here with ``desktop`` only to get None. Returns the first
    reason. ``vault`` is part of the question the spec asks (§6.4) so a later
    reason can read the vault without every door changing; none does yet. A
    laddered stem's stimulus is one of the reasons as a whole, so only the prompt
    is scanned.
    """

    del vault
    if device_class != PHONE:
        return None
    if item.practice_mode in DESKTOP_ONLY_MODES:
        return DESKTOP_ONLY_MODE
    if item.practice_mode == _TEACH_BACK_MODE or item.teach_back_source is not None:
        return MULTI_TURN_TEACH_BACK
    if item.error_hunt is not None:
        return ERROR_HUNT
    if item.laddered_stem is not None:
        return LADDERED_STEM
    if minted_for_lesson(item):
        return LESSON_CHECK
    return _prompt_reason(item.prompt)
