"""Contextual windows over production blocks (spec_local_contextual_retrieval_v1 §4.1, §4.3).

A contextual vector depends on its whole window, so the window rule is part
of every contextual space's identity (``WINDOW_RULE``) and every vector key.
One rule serves the local 9B space and the Voyage fallback alike:

* **units are production blocks**: the ``source_block/text`` recipe of every
  embeddable block of an extraction (furniture and blocks under 20
  non-whitespace characters skipped, as for Qwen);
* **grouped** windows pack consecutive blocks up to ``WINDOW_TOKENS``
  ESTIMATED tokens (markers included), in document order, every block exactly
  once, no overlap, deterministic;
* a window never crosses a **section** boundary, nor a **policy class**
  boundary: ``teaching``, ``solution``, ``exam`` (exam and held-out material)
  and ``assessment_lane`` (problem sets, notes, unknown roles, exercise
  links). Withheld blocks are therefore never joined to teaching text, and a
  teaching block's vector never carries exam text in its context;
* **singleton** windows hold one block each (the same-model context control);
* a block whose estimate passes the window bound alone is split by character
  offsets into parts of at most ``WINDOW_TOKENS`` estimated tokens each
  (markers included; cut on whitespace where the part has any, else hard
  cut), so EVERY window of both variants holds the bound; its vector is the
  token-weighted mean of its parts (``split_mean``; Codex review F15);
* a section header the policy withholds (any class but ``teaching``) reads as
  ``WITHHELD_HEADING`` in every descendant's section path, so a protected
  heading never reaches a permitted block's window, and marking a heading
  changes its descendants' texts, hence their keys (Codex review F1, E0's
  ``permitted_titles`` rule).

Every key is content-addressed (:func:`window_key`): a re-extraction, a new
held-out or exam mark on any block of the window, or a split-rule change
gives new keys, so stale rows are simply never found (never served).
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_block_fts import extraction_blocks, section_header_titles
from learnloop.source_retrieval.recipes import embeddable, section_path, source_block_text
from learnloop.vault.models import LoadedVault

#: The window rule's identity (part of every contextual space id).
WINDOW_RULE = "w4096-section-policy-v1"
#: keep (identity of the window rule): ESTIMATED tokens per grouped window, markers included.
WINDOW_TOKENS = 4096
CHUNK_MARKER_TOKENS = 8
#: keep (identity): the worker's own per-document bound (``pins.MAX_DOCUMENT_TOKENS``);
#: every window stays under ``WINDOW_TOKENS``, far inside it.
MAX_DOCUMENT_TOKENS = 8192
#: keep (identity, structural): the most estimated text tokens one part of a
#: split block holds, so the part with its marker is at most ``WINDOW_TOKENS``.
PART_TOKENS = WINDOW_TOKENS - CHUNK_MARKER_TOKENS
#: What a withheld section header reads as in any section path (never its text; E0's rule).
WITHHELD_HEADING = "(withheld heading)"
VARIANTS = ("grouped", "singleton")
POLICY_CLASSES = ("teaching", "solution", "exam", "assessment_lane")


def token_estimate(text: str | None) -> int:
    """UTF-8 bytes / 3, rounded up (E0's packing estimate; the worker measures)."""

    return math.ceil(len((text or "").encode("utf-8")) / 3)


@dataclass(frozen=True)
class Member:
    """One block, or one part of a split block, inside a window."""

    span_id: str
    text: str
    #: ``(part, parts, start, end)`` character offsets for a split block, else None.
    split: tuple[int, int, int, int] | None = None

    @property
    def tokens(self) -> int:
        return token_estimate(self.text) + CHUNK_MARKER_TOKENS


@dataclass(frozen=True)
class Window:
    extraction_id: str
    variant: str
    policy_class: str
    section: tuple[str, ...]
    members: tuple[Member, ...]

    @property
    def chunks(self) -> list[str]:
        return [member.text for member in self.members]

    @property
    def span_ids(self) -> list[str]:
        return list(dict.fromkeys(member.span_id for member in self.members))

    @property
    def digest(self) -> str:
        return _sha({"rule": WINDOW_RULE, "variant": self.variant, "extraction": self.extraction_id,
                     "class": self.policy_class,
                     "members": [[m.span_id, hashlib.sha256(m.text.encode("utf-8")).hexdigest(),
                                  list(m.split) if m.split else None] for m in self.members]})


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def window_key(space_id: str, window: Window, span_id: str) -> str:
    """The vector key of ``span_id``'s vector in ``window`` (§4.2): the space,
    the extraction, the whole window (members, texts, offsets, policy class)
    and the target block."""

    return "wk_" + _sha({"space": space_id, "window": window.digest, "target": span_id})[:40]


def policy_classes(vault: LoadedVault, repository: Repository,
                   keys: Iterable[tuple[str, str]]) -> dict[tuple[str, str], str]:
    """Each block's policy class (``teaching`` unless withheld), by the
    production predicates: ``exam_exclusions`` for exam and held-out material,
    ``model_reader_withheld`` for solutions and the assessment lane."""

    from learnloop.source_retrieval.corpus import exam_exclusions, model_reader_withheld

    wanted = sorted({(str(key[0]), str(key[1])) for key in keys})
    if not wanted:
        return {}
    exam = exam_exclusions(vault, repository)
    withheld = model_reader_withheld(vault, repository, wanted)
    classes: dict[tuple[str, str], str] = {}
    for key in wanted:
        if key[0] in exam.extractions or key in exam.spans:
            classes[key] = "exam"
        else:
            classes[key] = withheld.get(key, "teaching")
    return classes


def _split(span_id: str, text: str) -> list[Member]:
    """Consecutive character parts, each at most ``PART_TOKENS`` estimated
    tokens: the longest prefix within the bound, cut back to its last
    whitespace when it has one (the next part starts at that whitespace),
    else cut hard, so an unbroken input (CJK, a long formula) still holds the
    bound. Deterministic; the parts concatenate to the text."""

    if token_estimate(text) <= PART_TOKENS:
        return [Member(span_id, text)]
    bounds: list[tuple[int, int]] = []
    start, length = 0, len(text)
    while start < length:
        low, high = start + 1, length  # one character is always within the bound
        while low < high:
            middle = (low + high + 1) // 2
            if token_estimate(text[start:middle]) <= PART_TOKENS:
                low = middle
            else:
                high = middle - 1
        end = low
        if end < length:
            cut = end
            while cut > start and not text[cut].isspace():
                cut -= 1
            if cut > start:
                end = cut
        bounds.append((start, end))
        start = end
    kept = [(start, end) for start, end in bounds if text[start:end].strip()]
    return [Member(span_id, text[start:end], (part, len(kept), start, end))
            for part, (start, end) in enumerate(kept)]


def build_windows(extraction_id: str, blocks: Sequence[tuple[str, str, tuple[str, ...], str]],
                  variant: str) -> list[Window]:
    """Windows of one extraction from ``(span_id, recipe text, section path,
    policy class)`` in document order. Deterministic; every block exactly once."""

    if variant not in VARIANTS:
        raise ValueError(f"unknown window variant {variant!r}")
    windows: list[Window] = []
    current: list[Member] = []
    current_key: tuple[tuple[str, ...], str] | None = None
    tokens = 0

    def close() -> None:
        nonlocal current, tokens
        if current and current_key is not None:
            windows.append(Window(extraction_id, variant, current_key[1], current_key[0], tuple(current)))
        current, tokens = [], 0

    for span_id, text, section, policy in blocks:
        members = _split(span_id, text)
        if len(members) > 1:
            # A split block is its own window(s): each part alone, its vector the mean.
            close()
            for member in members:
                windows.append(Window(extraction_id, variant, policy, tuple(section), (member,)))
            current_key = None
            continue
        member = members[0]
        key = (tuple(section), policy)
        if variant == "singleton":
            windows.append(Window(extraction_id, variant, policy, tuple(section), (member,)))
            continue
        if current and (key != current_key or tokens + member.tokens > WINDOW_TOKENS):
            close()
        current_key = key
        current.append(member)
        tokens += member.tokens
    close()
    return windows


def _header_spans(blocks: Sequence[Any]) -> dict[str, str]:
    """``{extractor block id: span id}`` of the extraction's section headers."""

    return {str(block.extractor_block_id): block.span_id for block in blocks
            if block.block_type == "SectionHeader" and block.extractor_block_id}


def permitted_titles(extraction_id: str, titles: Mapping[str, str], headers: Mapping[str, str],
                     classes: Mapping[tuple[str, str], str]) -> dict[str, str]:
    """``titles`` with every header whose block is not ``teaching`` (or that
    no current block anchors) replaced by ``WITHHELD_HEADING`` (Codex review F1)."""

    permitted: dict[str, str] = {}
    for element, text in titles.items():
        span_id = headers.get(str(element))
        allowed = span_id is not None and classes.get((extraction_id, span_id), "teaching") == "teaching"
        permitted[element] = text if allowed else WITHHELD_HEADING
    return permitted


def extraction_windows(vault: LoadedVault, repository: Repository, extraction_id: str, variant: str,
                       *, classes: Mapping[tuple[str, str], str] | None = None) -> list[Window]:
    """The windows of one extraction's embeddable blocks under the current policy
    (withheld headings redacted from every section path)."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        titles = section_header_titles(connection, extraction_id)
        every = extraction_blocks(connection, extraction_id)
    blocks = [block for block in every if embeddable(block)]
    headers = _header_spans(every)
    wanted = [(block.extraction_id, block.span_id) for block in blocks] + \
        [(extraction_id, span_id) for span_id in headers.values()]
    if classes is None or any(key not in classes for key in wanted):
        classes = {**(classes or {}), **policy_classes(vault, repository, wanted)}
    titles = permitted_titles(extraction_id, titles, headers, classes)
    rows = [(block.span_id, source_block_text(block, titles), tuple(section_path(block, titles)),
             classes.get((block.extraction_id, block.span_id), "teaching")) for block in blocks]
    return build_windows(extraction_id, rows, variant)


def windows_by_extraction(vault: LoadedVault, repository: Repository, extraction_ids: Sequence[str],
                          variants: Sequence[str] = VARIANTS) -> dict[tuple[str, str], list[Window]]:
    """``{(extraction_id, variant): windows}`` under the current policy (one policy read)."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        keys = [(block.extraction_id, block.span_id) for extraction_id in extraction_ids
                for block in extraction_blocks(connection, extraction_id)
                if embeddable(block) or block.block_type == "SectionHeader"]
    classes = policy_classes(vault, repository, keys)
    return {(extraction_id, variant): extraction_windows(vault, repository, extraction_id, variant, classes=classes)
            for extraction_id in extraction_ids for variant in variants}


def expected_keys(space_id: str, windows: Sequence[Window]) -> dict[str, list[tuple[str, int]]]:
    """``{span_id: [(vector key, tokens)]}``: one key per (window, block); a
    split block has one key per part (all must exist), weighted by its tokens."""

    keys: dict[str, list[tuple[str, int]]] = {}
    for window in windows:
        for member in window.members:
            keys.setdefault(member.span_id, []).append((window_key(space_id, window, member.span_id), member.tokens))
    return keys


def mean_vector(parts: Sequence[Sequence[float]], weights: Sequence[int]) -> list[float]:
    """The token-weighted mean of a split block's part vectors (``split_mean``)."""

    total = float(sum(weights)) or 1.0
    width = len(parts[0])
    return [sum(float(part[index]) * weight for part, weight in zip(parts, weights, strict=True)) / total
            for index in range(width)]


__all__ = [
    "CHUNK_MARKER_TOKENS",
    "MAX_DOCUMENT_TOKENS",
    "Member",
    "PART_TOKENS",
    "POLICY_CLASSES",
    "VARIANTS",
    "WITHHELD_HEADING",
    "WINDOW_RULE",
    "WINDOW_TOKENS",
    "Window",
    "build_windows",
    "expected_keys",
    "extraction_windows",
    "mean_vector",
    "permitted_titles",
    "policy_classes",
    "token_estimate",
    "window_key",
    "windows_by_extraction",
]
