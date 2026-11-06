"""Mobile PR-6: which items a device can answer (``spec_mobile_tailnet_v1`` §6.4).

A phone renders text. An item whose stimulus needs a page, a picture or a long
conversation is kept for the desktop (D6): it never becomes a candidate of a phone
build (:class:`DeviceFilter`), the phone shows how many wait, and a by-id open is
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
from dataclasses import dataclass, field
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

#: What the rules are, named in the router's inputs of a phone offer so an offer's
#: filter can be read later. A new rule set is a new name. ``OFF`` is the kill
#: switch (``practice.device_eligibility_enabled``).
DEVICE_POLICY = "device_eligibility_v1"
DEVICE_POLICY_OFF = "off"

#: What Markdown shows as text: fenced and inline code, and display and inline
#: math, where ``n![k](x)`` is a formula. A backslash escape is matched last and
#: kept, so ``\$5`` opens no math (Sol verify V2) and ``\\$x$`` still does.
_LITERAL_TEXT = re.compile(
    r"^(?P<fence>`{3,}|~{3,})[^\n]*\n.*?^(?P=fence)\s*$"
    r"|`[^`\n]*`"
    r"|\$\$.*?\$\$"
    r"|\$[^$\n]*\$"
    r"|\\\(.*?\\\)"
    r"|\\\[.*?\\\]"
    r"|(?P<escape>\\.)",
    re.MULTILINE | re.DOTALL,
)
#: GFM footnotes, which the renderer shows as text and CommonMark alone reads as a
#: reference and its definition. They go before the parse. A definition holding a
#: real image is not seen (ruling R3: Low).
_FOOTNOTE_DEFINITION = re.compile(r"^ {0,3}\[\^[^\]\s]+\]:.*$", re.MULTILINE)
_FOOTNOTE_REFERENCE = re.compile(r"(?<!!)\[\^[^\]\s]+\](?![(\[:])")
_HTML_IMAGE = re.compile(r"<img\b", re.IGNORECASE)
_LLPDF = "llpdf:"
_URL_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
#: Schemes that name a file on this machine rather than a page anywhere.
_LOCAL_SCHEMES = ("file:", "asset:")
_FILE_SUFFIX = re.compile(r"\.[A-Za-z0-9]{1,8}$")

#: CommonMark, as the renderer's remark parser reads it (Codex review F3): only a
#: parser knows that ``![graph]`` is an image when ``[graph]: figures/graph.png``
#: is defined further down and bracketed text when it is not. Math and footnotes
#: have no meaning to it, so they still go first. ``validateLink`` is opened because
#: the default drops ``file:`` links, the very thing asked about here.
_MARKDOWN = MarkdownIt("commonmark")
_MARKDOWN.validateLink = lambda _url: True


def _is_item_asset(target: str) -> bool:
    """A link to a file: a local scheme, or a relative target that is a path.
    ``[0,1](x)`` is an interval and a function, not a link to anything, and
    ``//host/page`` is a page on the web."""

    if target.lower().startswith(_LOCAL_SCHEMES):
        return True
    if _URL_SCHEME.match(target) or target.startswith(("#", "//")):
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

    text = _LITERAL_TEXT.sub(lambda match: match.group("escape") or " ", prompt or "")
    if "[" not in text and "<" not in text:
        return None
    text = _FOOTNOTE_REFERENCE.sub("", _FOOTNOTE_DEFINITION.sub("", text))
    embeds_image = links_asset = False
    for token in _rendered_tokens(_MARKDOWN.parse(text)):
        # ``llpdf:`` counts where the renderer would follow it, a link's or an
        # image's target or raw HTML: as text it is code or prose (Sol verify V2).
        if token.type == "image":
            if str(token.attrGet("src") or "").lower().startswith(_LLPDF):
                return LINKS_LLPDF
            embeds_image = True
        elif token.type == "link_open":
            target = str(token.attrGet("href") or "")
            if target.lower().startswith(_LLPDF):
                return LINKS_LLPDF
            links_asset = links_asset or _is_item_asset(target)
        elif token.type in ("html_inline", "html_block"):
            if _LLPDF in token.content.lower():
                return LINKS_LLPDF
            embeds_image = embeds_image or _HTML_IMAGE.search(token.content) is not None
    if embeds_image:
        return EMBEDS_IMAGE
    return REFERENCES_ITEM_ASSET if links_asset else None


@dataclass
class DeviceFilter:
    """One queue build's device, and what it held back.

    Passed to ``build_due_queue``, whose admission predicate asks it
    (``serving_exclusions.admission_reason``, so a "Check once" asks too, and
    orchestrator ruling R1 holds). So it runs before the exploration's support and
    before ``limit`` (Codex review F1, F2): every counterfactual the router logs is
    an order the phone could have been shown, and the cut, a client's or the
    re-entry cap, falls among items the phone can answer. ``deferred`` is what
    waits for the desktop, wherever the cut fell: an item the build would have
    served, not every such item in the vault, so a card not due is not counted.
    """

    vault: Any
    device_class: str
    deferred: set[str] = field(default_factory=set)
    #: M2a (§6.4): an item this session's phone committed a diagnostic presentation for and
    #: did not render. It stays the session's assignment for the desktop; left in this build it
    #: would be the pinned head of a list that moved past it, and every answer after it a
    #: learner pick nobody made.
    left_for_desktop: frozenset[str] = frozenset()

    def refuses(self, item: Any) -> bool:
        return item.id in self.left_for_desktop or ineligibility_reason(self.vault, item, self.device_class) is not None

    def holds_back(self, item: Any) -> bool:
        """``refuses``, for an item the build would otherwise serve."""

        if not self.refuses(item):
            return False
        self.deferred.add(item.id)
        return True


#: Mobile v2 §2.2: a plan step held back because the phone has no Reader yet (V4 lifts it:
#: "a reading block is never ineligible, because the phone has a Reader").
READING_BEFORE_PHONE_READER = "reading_before_phone_reader"
#: Mobile v2 V3 (D3): a generated follow-up probe is answered on the phone from V3 on; until then
#: it waits for the desktop, as FG1 §10 says.
GENERATED_PROBE = "generated_probe"
#: The plan surface of a phone step (mobile v2 §2.2), beside PR-5's ``phone_queue`` and
#: ``phone_practice``: what a decision taken at a boundary under a phone origin records.
PHONE_PLAN = "phone_plan"


@dataclass
class PlanStepFilter:
    """Mobile v2 §2.2: the phone's door into the shared plan, which filters at the step.

    The plan's build and the router's support are the desktop's, exactly: no item is held
    back from a build or a decision. Only the serving door skips. The engine
    (``daily_plan.engine.advance_with_context``) asks :meth:`holds` of each open item in plan
    order and serves the first the device can show; what it passes over stays assigned in its
    block for the desktop's next Next, and is counted here (``held``), as the queue counts
    ``deferred``. ``None`` in the engine is the desktop, whose steps never come here.
    """

    #: The PR-6 rules, or None with ``practice.device_eligibility_enabled`` off (then only a
    #: generated probe, which a phone door refuses whatever the switch says, is held).
    device_filter: DeviceFilter | None
    #: The surface its boundary decisions record (``phone_plan``) and the device rules in
    #: force (``device_eligibility_v1`` or ``off``), named in each decision's inputs.
    surface: str = PHONE_PLAN
    device_policy: str = DEVICE_POLICY
    #: ``practice_item_id -> bool``: a generated FG1 probe, which the phone serves from V3 on.
    generated_probe: Any = None
    #: What this step passed over, by item id, with its reason.
    held: dict[str, str] = field(default_factory=dict)
    #: Reading blocks this step passed over (the phone's Reader is V4's).
    held_readings: set[str] = field(default_factory=set)

    def holds(self, item: Any) -> str | None:
        """Why the device leaves ``item`` for the desktop, or None when it can serve it."""

        if self.generated_probe is not None and self.generated_probe(item.id):
            return GENERATED_PROBE
        if self.device_filter is None:
            return None
        if item.id in self.device_filter.left_for_desktop:
            return DESKTOP_ONLY_MODE
        return ineligibility_reason(self.device_filter.vault, item, self.device_filter.device_class)

    def detail(self) -> dict[str, str]:
        """What a decision taken at a boundary under this device records (its ``device`` entry)."""

        return {"surface": self.surface, "device_policy": self.device_policy}

    @property
    def held_count(self) -> int:
        return len(self.held)


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
