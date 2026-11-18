"""What a person could perceive on the screen, as text: the observation the persona reads.

Two halves. ``DUMP_JS`` runs in the page (WebDriver "execute script") and
returns the rendered DOM as a flat list of nodes with what only a browser
knows: whether each node is visible inside the viewport and its clipping
containers, its display kind, live form state, focus. Everything else is
plain logic here, testable without a browser (``dump_static_html`` builds the
same node list from a static page): roles, accessible names, states, reading
order, numbering of the elements a person can act on, and the rendering.

The rendering prints only what is perceivable: visible text in reading order,
each interactive element with its role, name and state, focus, title, dialogs,
notices and busy indicators. Never ids, class names, test ids or hidden text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any

#: Runs in the page. Returns {title, focus, viewport, scroll, nodes, elements}: ``elements`` are
#: WebElement references (by node ``ref``) so a later click needs no DOM marker.
DUMP_JS = r"""
const viewport = { w: window.innerWidth, h: window.innerHeight };
const nodes = [];
const elements = [];
const ATTRS = ["role", "type", "alt", "title", "placeholder", "id", "for", "tabindex", "contenteditable",
  "open", "href", "disabled", "multiple", "size", "required", "readonly", "hidden", "aria-label",
  "aria-labelledby", "aria-describedby", "aria-hidden", "aria-disabled", "aria-checked", "aria-expanded",
  "aria-pressed", "aria-selected", "aria-current", "aria-busy", "aria-live", "aria-modal", "aria-level",
  "aria-valuenow", "aria-valuetext", "aria-invalid", "aria-required", "aria-readonly", "aria-haspopup",
  "aria-multiline", "aria-roledescription", "value", "min", "max", "colspan"];
const clipStack = [];
function intersects(r, box) {
  return r.right > box.left && r.left < box.right && r.bottom > box.top && r.top < box.bottom;
}
function inView(rects) {
  const screen = { left: 0, top: 0, right: viewport.w, bottom: viewport.h };
  for (const r of rects) {
    if (r.width < 1 && r.height < 1) continue;
    if (!intersects(r, screen)) continue;
    if (clipStack.every((box) => intersects(r, box))) return true;
  }
  return false;
}
function displayKind(style, tag, node) {
  const d = style.display;
  // An absolutely placed run of text (a PDF's text layer) is blockified by CSS but reads inline.
  if ((style.position === "absolute" || style.position === "fixed") && node.children.length === 0) return "positioned";
  if (d === "inline" || d === "inline-block" || d === "inline-flex" || d === "inline-grid" || d === "contents") return "inline";
  if ((d === "table-cell" || d === "table-header-group") && (tag === "td" || tag === "th")) return "cell";
  if (d.startsWith("table") && tag !== "table" && tag !== "tr") return "inline";
  if (d === "list-item") return "item";
  return "block";
}
function pseudo(node, which) {
  const content = getComputedStyle(node, which).content;
  if (!content || content === "none" || content === "normal") return null;
  const attr = /^attr\(([^)]+)\)$/.exec(content);
  if (attr) return node.getAttribute(attr[1].trim()) || null;
  const quoted = /^"(.*)"$/s.exec(content);
  return quoted ? quoted[1].replace(/\\"/g, '"') : null;
}
function visit(node, parent) {
  if (node.nodeType === Node.TEXT_NODE) {
    const text = node.textContent;
    if (!text || !text.trim()) return;
    const range = document.createRange();
    range.selectNodeContents(node);
    const visible = inView(Array.from(range.getClientRects()));
    nodes.push({ i: nodes.length, parent, text, visible });
    return;
  }
  if (node.nodeType !== Node.ELEMENT_NODE) return;
  const tag = node.tagName.toLowerCase();
  if (tag === "script" || tag === "style" || tag === "template" || tag === "noscript" || tag === "head") return;
  const style = getComputedStyle(node);
  if (style.display === "none") return;
  const rect = node.getBoundingClientRect();
  const clipped = (style.clip === "rect(0px, 0px, 0px, 0px)") || /inset\(50%/.test(style.clipPath || "");
  const tiny = rect.width <= 1 && rect.height <= 1 && (style.overflow === "hidden" || clipped);
  const hiddenStyle = style.visibility === "hidden" || style.visibility === "collapse" || parseFloat(style.opacity) === 0 || tiny || clipped;
  const attrs = {};
  for (const name of ATTRS) {
    if (node.hasAttribute(name)) attrs[name] = node.getAttribute(name);
  }
  const entry = { i: nodes.length, parent, tag, attrs, display: displayKind(style, tag, node), top: Math.round(rect.top),
    visible: !hiddenStyle && (style.display === "contents" || inView(Array.from(node.getClientRects()))),
    styleHidden: hiddenStyle };
  if (tag === "input" || tag === "textarea" || tag === "select") {
    entry.value = node.value;
    if (tag === "input") { entry.checked = node.checked; entry.indeterminate = node.indeterminate; }
    entry.disabledProp = node.disabled;
    if (tag === "select") {
      entry.options = Array.from(node.selectedOptions || []).map((o) => o.textContent);
    }
  }
  if (tag === "option") entry.selectedProp = node.selected;
  if (tag === "details") entry.openProp = node.open;
  if (tag === "dialog") entry.openProp = node.open;
  if (style.cursor === "pointer" && (!node.parentElement || getComputedStyle(node.parentElement).cursor !== "pointer")) {
    entry.pointer = true;
  }
  if (node === document.activeElement && node !== document.body) entry.focused = true;
  const before = pseudo(node, "::before");
  const after = pseudo(node, "::after");
  if (before && before.trim()) entry.before = before;
  if (after && after.trim()) entry.after = after;
  const scrollable = (/(auto|scroll)/.test(style.overflowY) && node.scrollHeight > node.clientHeight + 2) ||
    (/(auto|scroll)/.test(style.overflowX) && node.scrollWidth > node.clientWidth + 2);
  if (scrollable) {
    entry.scroll = { top: node.scrollTop, height: node.scrollHeight, client: node.clientHeight,
      left: node.scrollLeft, width: node.scrollWidth, clientWidth: node.clientWidth };
  }
  const candidate = /^(a|button|input|select|textarea|summary|option|details|label|dialog)$/.test(tag) ||
    entry.pointer || attrs.role !== undefined || attrs.tabindex !== undefined || attrs.contenteditable !== undefined;
  if (candidate) {
    entry.ref = elements.length;
    elements.push(node);
  }
  nodes.push(entry);
  const index = entry.i;
  // Typeset math: a person sees the formula; its TeX source is the faithful text for it.
  const tex = node.classList && node.classList.contains("katex")
    ? node.querySelector('annotation[encoding="application/x-tex"]') : null;
  if (tex) {
    entry.math = tex.textContent;
    return;
  }
  const clips = style.overflowX !== "visible" || style.overflowY !== "visible";
  if (clips) clipStack.push(rect);
  if (!hiddenStyle || style.visibility === "hidden") {
    for (const child of node.childNodes) visit(child, index);
    if (node.shadowRoot) for (const child of node.shadowRoot.childNodes) visit(child, index);
  }
  if (clips) clipStack.pop();
}
visit(document.body, -1);
const page = document.scrollingElement || document.documentElement;
return { title: document.title, viewport, nodes, elements,
  pageScroll: { top: page.scrollTop, height: page.scrollHeight, client: page.clientHeight } };
"""

INTERACTIVE_ROLES = {
    "button", "link", "textbox", "searchbox", "checkbox", "radio", "combobox", "listbox", "option", "slider",
    "spinbutton", "switch", "tab", "menuitem", "menuitemcheckbox", "menuitemradio", "treeitem", "clickable",
    "gridcell",
}
NAME_FROM_CONTENT = {
    "button", "link", "checkbox", "radio", "tab", "menuitem", "menuitemcheckbox", "menuitemradio", "option",
    "heading", "treeitem", "switch", "clickable", "cell", "gridcell", "columnheader", "rowheader", "tooltip",
}
CONTAINER_ROLES = {"listbox", "menu", "menubar", "tablist", "radiogroup", "tree", "grid", "toolbar", "group"}
NOTICE_ROLES = {"status", "alert", "log", "marquee", "timer"}
TEXT_INPUT_TYPES = {"text", "email", "url", "tel", "password", "search", ""}
BLOCK_TAGS = {
    "address", "article", "aside", "blockquote", "details", "dialog", "dd", "div", "dl", "dt", "fieldset",
    "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr", "li", "main",
    "nav", "ol", "p", "pre", "section", "summary", "table", "tr", "ul", "body", "html", "tbody", "thead",
}


@dataclass
class Node:
    index: int
    parent: int
    tag: str = ""
    text: str | None = None
    attrs: dict[str, str] = field(default_factory=dict)
    visible: bool = True
    display: str = "inline"
    value: str | None = None
    checked: bool | None = None
    selected: bool | None = None
    open: bool | None = None
    disabled_prop: bool | None = None
    options: list[str] = field(default_factory=list)
    pointer: bool = False
    focused: bool = False
    scroll: dict | None = None
    ref: int | None = None
    #: Text a stylesheet draws before or after the element (``::before``/``::after``): seen, not in the DOM.
    before: str | None = None
    after: str | None = None
    math: str | None = None
    top: int | None = None
    children: list["Node"] = field(default_factory=list)

    @property
    def is_text(self) -> bool:
        return self.text is not None


@dataclass
class Element:
    number: int
    ref: int | None
    role: str
    name: str
    states: list[str]

    def describe(self) -> str:
        state = f" ({', '.join(self.states)})" if self.states else ""
        name = f' "{self.name}"' if self.name else ""
        return f"[{self.number}] {self.role}{name}{state}"


@dataclass
class Perception:
    title: str
    text: str
    elements: list[Element]
    focus: str | None
    dialogs: list[str]
    notices: list[str]
    busy: list[str]
    more: list[str]

    def element(self, number: int) -> Element | None:
        return next((element for element in self.elements if element.number == number), None)


def nodes_from_dump(raw: list[dict]) -> list[Node]:
    nodes: list[Node] = []
    for entry in raw:
        nodes.append(Node(
            index=entry["i"], parent=entry["parent"], tag=entry.get("tag", ""), text=entry.get("text"),
            attrs=dict(entry.get("attrs") or {}), visible=bool(entry.get("visible", True)),
            display=entry.get("display", "inline"), value=entry.get("value"), checked=entry.get("checked"),
            selected=entry.get("selectedProp"), open=entry.get("openProp"), disabled_prop=entry.get("disabledProp"),
            options=list(entry.get("options") or []), pointer=bool(entry.get("pointer")),
            focused=bool(entry.get("focused")), scroll=entry.get("scroll"), ref=entry.get("ref"),
            before=entry.get("before"), after=entry.get("after"), math=entry.get("math"), top=entry.get("top"),
        ))
    by_index = {node.index: node for node in nodes}
    for node in nodes:
        if node.parent in by_index:
            by_index[node.parent].children.append(node)
    return nodes


def role_of(node: Node) -> str | None:
    explicit = (node.attrs.get("role") or "").split()
    if explicit and explicit[0] not in ("presentation", "none"):
        return explicit[0]
    tag = node.tag
    if tag == "a" and "href" in node.attrs:
        return "link"
    if tag == "button":
        return "button"
    if tag == "input":
        kind = (node.attrs.get("type") or "text").lower()
        if kind == "hidden":
            return None
        if kind in ("checkbox", "radio"):
            return kind
        if kind == "range":
            return "slider"
        if kind == "number":
            return "spinbutton"
        if kind == "search":
            return "searchbox"
        if kind in ("button", "submit", "reset", "image", "file"):
            return "button"
        return "textbox"
    if tag == "textarea":
        return "textbox"
    if tag == "select":
        return "listbox" if "multiple" in node.attrs or int(node.attrs.get("size") or 1) > 1 else "combobox"
    if tag == "option":
        return "option"
    if tag == "summary":
        return "button"
    if re.fullmatch(r"h[1-6]", tag):
        return "heading"
    if tag == "img" and node.attrs.get("alt"):
        return "img"
    if tag == "dialog":
        return "dialog"
    if tag == "progress":
        return "progressbar"
    if node.attrs.get("contenteditable") in ("", "true", "plaintext-only"):
        return "textbox"
    if tag in ("td",):
        return "cell"
    if tag == "th":
        return "columnheader"
    return None


def _disabled(node: Node, ancestors: list[Node]) -> bool:
    if node.disabled_prop or "disabled" in node.attrs or node.attrs.get("aria-disabled") == "true":
        return True
    return any(ancestor.tag == "fieldset" and "disabled" in ancestor.attrs for ancestor in ancestors)


def _states(node: Node, role: str, ancestors: list[Node]) -> list[str]:
    states = []
    if _disabled(node, ancestors):
        states.append("disabled")
    if role in ("checkbox", "radio", "switch", "menuitemcheckbox", "menuitemradio"):
        aria = node.attrs.get("aria-checked")
        if aria == "mixed":
            states.append("mixed")
        elif aria == "true" or (aria is None and node.checked):
            states.append("checked")
        else:
            states.append("not checked")
    expanded = node.attrs.get("aria-expanded")
    if node.tag == "summary":
        parent_open = next((a.open for a in reversed(ancestors) if a.tag == "details"), None)
        expanded = "true" if parent_open else "false"
    if expanded in ("true", "false"):
        states.append("expanded" if expanded == "true" else "collapsed")
    pressed = node.attrs.get("aria-pressed")
    if pressed in ("true", "mixed"):
        states.append("pressed")
    if node.attrs.get("aria-selected") == "true" or (role == "option" and node.selected):
        states.append("selected")
    current = node.attrs.get("aria-current")
    if current and current != "false":
        states.append("current")
    if node.attrs.get("aria-invalid") == "true":
        states.append("invalid")
    if "required" in node.attrs or node.attrs.get("aria-required") == "true":
        states.append("required")
    if "readonly" in node.attrs or node.attrs.get("aria-readonly") == "true":
        states.append("read-only")
    if node.attrs.get("aria-haspopup") not in (None, "false"):
        states.append("opens a menu")
    if node.focused:
        states.append("focused")
    return states


class Renderer:
    def __init__(self, nodes: list[Node]):
        self.nodes = nodes
        self.by_id = {node.attrs["id"]: node for node in nodes if not node.is_text and node.attrs.get("id")}
        self.labels_for: dict[str, list[Node]] = {}
        for node in nodes:
            if node.tag == "label" and node.attrs.get("for"):
                self.labels_for.setdefault(node.attrs["for"], []).append(node)
        self.elements: list[Element] = []
        self.focus: str | None = None
        self.dialogs: list[str] = []
        self.notices: list[str] = []
        self.busy: list[str] = []
        self.more: list[str] = []

    # -- names --
    def text_of(self, node: Node, *, include_hidden: bool = False, skip: Node | None = None,
                pseudo: bool = True) -> str:
        if node is skip:
            return ""
        if node.is_text:
            return node.text or "" if (node.visible or include_hidden) else ""
        if not include_hidden and not node.visible and not node.children:
            return ""
        if node.tag == "img":
            return node.attrs.get("alt") or ""
        if node.math is not None:
            return f"${node.math.strip()}$" if node.visible or include_hidden else ""
        label = node.attrs.get("aria-label")
        if label and node is not skip and node.tag not in ("input", "textarea", "select"):
            return label
        if node.tag in ("input", "textarea", "select"):
            return self.value_text(node) or ""
        parts = [self.text_of(child, include_hidden=include_hidden, skip=skip, pseudo=pseudo)
                 for child in node.children]
        if pseudo and (node.visible or include_hidden):
            parts = [node.before or "", *parts, node.after or ""]
        return " ".join(part for part in parts if part)

    def value_text(self, node: Node) -> str | None:
        if node.tag == "select":
            return ", ".join(option.strip() for option in node.options) or None
        if node.tag in ("input", "textarea"):
            kind = (node.attrs.get("type") or "text").lower()
            if kind in ("checkbox", "radio", "file", "hidden"):
                return None
            if kind in ("button", "submit", "reset"):
                return node.value or node.attrs.get("value")
            return node.value if node.value is not None else node.attrs.get("value")
        return None

    def name_of(self, node: Node, role: str, ancestors: list[Node]) -> str:
        labelled = node.attrs.get("aria-labelledby")
        if labelled:
            parts = [self.text_of(self.by_id[ref], include_hidden=True) for ref in labelled.split() if ref in self.by_id]
            if any(parts):
                return _clean(" ".join(parts))
        if node.attrs.get("aria-label", "").strip():
            return _clean(node.attrs["aria-label"])
        if node.tag in ("input", "textarea", "select"):
            kind = (node.attrs.get("type") or "text").lower()
            if kind in ("button", "submit", "reset"):
                return _clean(node.value or node.attrs.get("value") or {"submit": "Submit", "reset": "Reset"}.get(kind, ""))
            if kind == "image":
                return _clean(node.attrs.get("alt") or "")
            labels = list(self.labels_for.get(node.attrs.get("id", ""), []))
            wrapping = next((a for a in reversed(ancestors) if a.tag == "label"), None)
            if wrapping is not None:
                labels.append(wrapping)
            text = " ".join(self.text_of(label, skip=node) for label in labels)
            if text.strip():
                return _clean(text)
            if node.attrs.get("title"):
                return _clean(node.attrs["title"])
            if kind == "file":
                return "Choose file"
            return ""
        if node.tag == "img":
            return _clean(node.attrs.get("alt") or "")
        if role in NAME_FROM_CONTENT:
            text = " ".join(self.text_of(child) for child in node.children)
            if text.strip():
                return _clean(text)
        return _clean(node.attrs.get("title") or "")

    # -- rendering --
    def render(self) -> list[str]:
        """The screen in reading order; a modal dialog first, since it is what the person faces."""

        lines: list[str] = []
        current: list[str] = []
        root = next((node for node in self.nodes if node.parent == -1), None)
        if root is None:
            return lines
        modal = [node for node in self.nodes if self._is_modal(node)]
        if modal:
            for dialog in modal:
                self._walk(dialog, self._ancestors(dialog), lines, current)
                self._flush(lines, current)
            lines.append("--- behind the dialog ---")
            self.skip = {dialog.index for dialog in modal}
        self._walk(root, [], lines, current)
        self._flush(lines, current)
        return lines

    skip: set[int] = set()
    positioned_top: int | None = None

    def _is_modal(self, node: Node) -> bool:
        if node.is_text or not node.visible:
            return False
        role = role_of(node)
        if role not in ("dialog", "alertdialog"):
            return False
        return node.attrs.get("aria-modal") == "true" or (node.tag == "dialog" and bool(node.open))

    def _ancestors(self, node: Node) -> list[Node]:
        by_index = {candidate.index: candidate for candidate in self.nodes}
        chain = []
        current = by_index.get(node.parent)
        while current is not None:
            chain.append(current)
            current = by_index.get(current.parent)
        return list(reversed(chain))

    def _flush(self, lines: list[str], current: list[str]) -> None:
        text = _clean(" ".join(current))
        if text:
            lines.append(text)
        current.clear()

    def _walk(self, node: Node, ancestors: list[Node], lines: list[str], current: list[str]) -> None:
        if node.index in self.skip:
            return
        if node.is_text:
            if node.visible:
                current.append(node.text or "")
            return
        role = role_of(node)
        block = node.display in ("block", "item", "cell") or node.tag in BLOCK_TAGS
        if node.display == "positioned":
            # Placed text: a new line where its baseline moves, otherwise one running line.
            block = False
            if node.visible and node.top is not None:
                if self.positioned_top is not None and abs(node.top - self.positioned_top) > 3:
                    self._flush(lines, current)
                self.positioned_top = node.top
        if node.attrs.get("aria-busy") == "true" and node.visible:
            self.busy.append(self.name_of(node, role or "", ancestors) or "a region is loading")
        if role == "progressbar" and node.visible:
            label = self.name_of(node, role, ancestors)
            value = node.attrs.get("aria-valuetext") or node.attrs.get("aria-valuenow") or (
                node.attrs.get("value") if node.tag == "progress" else None)
            if value in (None, ""):
                # No value: an indeterminate bar, the app saying it is working.
                self.busy.append(_clean(f"progress {label}") or "progress")
            else:
                current.append(_clean(f'[progress "{label}" {value}]'))
        if node.scroll:
            self._note_scroll(node, role, ancestors)
        if role in ("dialog", "alertdialog") and (node.visible or node.open):
            if node.tag != "dialog" or node.open:
                name = self.name_of(node, role, ancestors)
                modal = " (modal)" if node.attrs.get("aria-modal") == "true" or node.tag == "dialog" else ""
                self.dialogs.append(f'{role} "{name}"{modal}' if name else f"{role}{modal}")
        live = node.attrs.get("aria-live")
        if (role in NOTICE_ROLES or live in ("polite", "assertive")) and node.visible:
            text = _clean(self.text_of(node))
            if text:
                self.notices.append(f"{role or 'live region'}: {text}")
        interactive = role in INTERACTIVE_ROLES or (
            node.pointer and role is None and node.tag not in ("label", "html", "body")
            and not any(role_of(a) in INTERACTIVE_ROLES or a.pointer for a in ancestors))
        if interactive and node.visible:
            role = role or "clickable"
            if role in CONTAINER_ROLES and role not in ("listbox",):
                interactive = False
        if interactive and node.visible and (role not in ("listbox",) or node.tag == "select"):
            if block:
                self._flush(lines, current)
            element = self._element(node, role or "clickable", ancestors)
            token = element.describe()
            value = self.value_text(node)
            if role in ("textbox", "searchbox", "spinbutton", "combobox", "slider") and node.tag in (
                    "input", "textarea", "select"):
                if value:
                    token += f' value "{_clean(value)[:400]}"'
                elif node.attrs.get("placeholder"):
                    token += f' placeholder "{_clean(node.attrs["placeholder"])}"'
                else:
                    token += " empty"
            elif role in ("textbox",) and node.attrs.get("contenteditable") is not None:
                text = _clean(" ".join(self.text_of(child, pseudo=False) for child in node.children))
                drawn = _clean(" ".join(self.text_of(child) for child in node.children) + " " + (node.before or ""))
                if text:
                    token += f' value "{text[:400]}"'
                elif drawn or node.attrs.get("placeholder"):
                    token += f' placeholder "{drawn or _clean(node.attrs["placeholder"])}"'
                else:
                    token += " empty"
            current.append(token)
            if block:
                self._flush(lines, current)
            return
        if node.math is not None:
            if node.visible:
                current.append(f"${node.math.strip()}$")
            return
        if block:
            self._flush(lines, current)
        prefix = ""
        if role == "heading" and node.visible:
            level = node.attrs.get("aria-level") or (node.tag[1] if re.fullmatch(r"h[1-6]", node.tag) else "2")
            prefix = "#" * int(level) + " "
        elif node.tag == "li" and node.visible:
            prefix = "- "
        elif node.tag == "img" and node.visible and node.attrs.get("alt"):
            current.append(f"[image: {_clean(node.attrs['alt'])}]")
        elif node.tag == "hr" and node.visible:
            current.append("———")
        if prefix:
            current.append(prefix.rstrip())
        if node.visible and node.before:
            current.append(node.before)
        for child in node.children:
            self._walk(child, [*ancestors, node], lines, current)
        if node.visible and node.after:
            current.append(node.after)
        if block:
            self._flush(lines, current)

    def _element(self, node: Node, role: str, ancestors: list[Node]) -> Element:
        element = Element(len(self.elements) + 1, node.ref, role, self.name_of(node, role, ancestors)[:200],
                          _states(node, role, ancestors))
        self.elements.append(element)
        if node.focused:
            self.focus = element.describe()
        return element

    def _note_scroll(self, node: Node, role: str | None, ancestors: list[Node]) -> None:
        scroll = node.scroll or {}
        name = self.name_of(node, role or "", ancestors) if role else ""
        where = f' in "{name}"' if name else ""
        if scroll.get("top", 0) + scroll.get("client", 0) < scroll.get("height", 0) - 2:
            self.more.append(f"More below{where} (scroll down).")
        if scroll.get("top", 0) > 2:
            self.more.append(f"More above{where} (scroll up).")


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def perceive(dump: dict[str, Any]) -> Perception:
    nodes = nodes_from_dump(dump.get("nodes") or [])
    renderer = Renderer(nodes)
    lines = renderer.render()
    focus = renderer.focus
    if focus is None:
        focused = next((node for node in nodes if node.focused), None)
        if focused is not None:
            role = role_of(focused) or focused.tag
            focus = f'{role} "{renderer.name_of(focused, role, [])}"'
    page = dump.get("pageScroll") or {}
    more = list(dict.fromkeys(renderer.more))
    if page.get("top", 0) + page.get("client", 0) < page.get("height", 0) - 2:
        more.insert(0, "More below on the page (scroll down).")
    return Perception(
        title=_clean(dump.get("title") or ""), text="\n".join(lines), elements=renderer.elements, focus=focus,
        dialogs=list(dict.fromkeys(renderer.dialogs)), notices=list(dict.fromkeys(renderer.notices)),
        busy=list(dict.fromkeys(renderer.busy)), more=more,
    )


def render_observation(perception: Perception, *, header: list[str]) -> str:
    """The observation file's text: what happened, then the screen."""

    lines = list(header)
    lines.append(f"Window title: {perception.title or '(none)'}")
    lines.append(f"Focus: {perception.focus or 'nothing in particular'}")
    if perception.dialogs:
        lines.append("Dialog open: " + "; ".join(perception.dialogs))
    if perception.notices:
        lines.extend(f"Notice: {notice}" for notice in perception.notices)
    lines.append("--- screen ---")
    lines.append(perception.text or "(nothing visible)")
    if perception.more:
        lines.append("--- off screen ---")
        lines.extend(perception.more)
    return "\n".join(lines) + "\n"


# -- the same node list from static HTML, for tests and for checking the renderer without a browser --


class _StaticDump(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
    SKIP = {"script", "style", "template", "noscript", "head", "title"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.nodes: list[dict] = []
        self.stack: list[tuple[str, int, bool]] = []
        self.skip_depth = 0
        self.title = ""
        self._in_title = False

    def _hidden(self, attrs: dict[str, str]) -> bool:
        style = (attrs.get("style") or "").replace(" ", "").lower()
        return "hidden" in attrs or "display:none" in style

    def _invisible(self, attrs: dict[str, str]) -> bool:
        style = (attrs.get("style") or "").replace(" ", "").lower()
        return "visibility:hidden" in style or "opacity:0" in style

    def handle_starttag(self, tag: str, raw: list[tuple[str, str | None]]) -> None:
        attrs = {name: value or "" for name, value in raw}
        if tag == "title":
            self._in_title = True
        if self.skip_depth or tag in self.SKIP or self._hidden(attrs) or (
                tag == "input" and attrs.get("type") == "hidden"):
            if tag not in self.VOID:
                self.skip_depth += 1
            return
        parent_visible = self.stack[-1][2] if self.stack else True
        parent = self.stack[-1][1] if self.stack else -1
        visible = parent_visible and not self._invisible(attrs)
        entry: dict[str, Any] = {
            "i": len(self.nodes), "parent": parent, "tag": tag, "attrs": attrs, "visible": visible,
            "display": "block" if tag in BLOCK_TAGS else "inline", "ref": len(self.nodes),
        }
        if tag in ("input", "textarea", "select"):
            entry["value"] = attrs.get("value", "")
            entry["checked"] = "checked" in attrs
        if tag in ("details", "dialog"):
            entry["openProp"] = "open" in attrs
        if "data-walk-focused" in attrs:
            entry["focused"] = True
            del attrs["data-walk-focused"]
        self.nodes.append(entry)
        if tag not in self.VOID:
            self.stack.append((tag, entry["i"], visible))

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        if self.skip_depth:
            if tag not in self.VOID:
                self.skip_depth -= 1
            return
        for position in range(len(self.stack) - 1, -1, -1):
            if self.stack[position][0] == tag:
                del self.stack[position:]
                break

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
            return
        if self.skip_depth or not data.strip() or not self.stack:
            return
        parent, visible = self.stack[-1][1], self.stack[-1][2]
        self.nodes.append({"i": len(self.nodes), "parent": parent, "text": data, "visible": visible})


def dump_static_html(html: str) -> dict[str, Any]:
    """The page dump for static HTML: ``hidden``/inline-style visibility, everything in view.

    A ``data-walk-focused`` attribute marks the focused element (a static page has no focus)."""

    parser = _StaticDump()
    parser.feed(html)
    nodes = parser.nodes
    root_index = next((n["i"] for n in nodes if n.get("tag") == "body"), None)
    if root_index is not None:
        for node in nodes:
            if node["i"] == root_index:
                node["parent"] = -1
    return {"title": parser.title.strip(), "nodes": [n for n in nodes if _under(n, nodes, root_index)]}


def _under(node: dict, nodes: list[dict], root: int | None) -> bool:
    if root is None:
        return True
    by_index = {n["i"]: n for n in nodes}
    current: dict | None = node
    while current is not None:
        if current["i"] == root:
            return True
        current = by_index.get(current["parent"])
    return False
