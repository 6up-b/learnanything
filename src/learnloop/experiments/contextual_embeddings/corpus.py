"""E0's corpus: copies, the read-only inventory, policy, candidate units, windows.

**Copies** (spec §5.1.1). Vault copies are made only through
``learnloop.db.copies.copy_tree_with_databases`` (SQLite's backup API, WAL
state included) into a ``fixtures-local`` directory. ``arxiv_v2`` is never
copied (orchestrator rule). A copy is then opened read-only: the vault with
``load_environment=False`` (no settings file, no dotenv), the database
attached read-only and never migrated, so preparing and planning write
nothing to it.

**Policy before encoding** (spec §4.2, D12). A block a model may never read is
withheld from every unit, window, header, label and prompt: exam and
learner-held-out material by the one predicate
(``content.sources.exam_material``), and solutions and the assessment lane by
``source_retrieval.corpus.model_reader_withheld``. A withheld block is a hard
boundary: its former neighbours are never joined into one unit or window.
Policy failure fails closed (``PolicyUnavailable``). The snapshot's
fingerprint and each artifact's dependency keys are persisted; an artifact is
stale when a dependency key is now withheld (a new ``held_out_evaluation``
mark) or its extraction changed (re-extraction).

**Candidate units** (spec §4.1). One common map for every arm: a permitted
content block is one unit; a block over ``UNIT_MAX_TOKENS`` is split at
sentence or whitespace boundaries with its original character offsets; a bare
equation is attached to the explanatory text before it (else the text after
it); adjacent transcript captions merge toward 300-600 tokens. Units never
cross sources, sections, policy boundaries or numbered environments (each
numbered label opens its own unit), and every unit keeps its original
``(extraction_id, span_id, start, end)`` members for labels and citations.

**Windows.** Grouped encoding packs whole sections of one policy segment into
``WINDOW_TOKENS`` (chunk markers counted), splitting only a section that
does not fit, with no overlap: every unit is in exactly one window. A
whole-source window is offered only when the entire permitted segment fits
the provider's validated per-document limit.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from contextlib import closing
from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from learnloop.content.sources import exam_material as EM
from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_block_fts import (
    EXCLUDED_BLOCK_TYPES,
    BlockRow,
    extraction_blocks,
    extraction_fingerprint,
    extraction_units,
    section_header_titles,
)
from learnloop.ingest.block_roles import lead_role, numbered_label, numbered_references
from learnloop.source_retrieval.corpus import current_extractions, model_reader_withheld
from learnloop.source_retrieval.recipes import section_path
from learnloop.tutor.context_delivery import ExtractionText
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths

from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.pins import token_estimate, token_upper_bound

#: Copies and artifacts live only under a directory of this name (gitignored).
LOCAL_ROOT_NAME = "fixtures-local"
EXPERIMENT_DIR = "contextual-embeddings"
#: Never copied, planned or run against (orchestrator rule).
FORBIDDEN_SOURCE_NAMES = frozenset({"arxiv_v2"})
_EQUATION_TYPES = frozenset({"equation", "equationnumber", "math"})
_CAPTION_TYPES = frozenset({"caption"})
_SPLIT_AT = re.compile(r"(?<=[.!?;:])\s+|\n+")

SpanKey = tuple[str, str]


class PolicyUnavailable(RuntimeError):
    """The material policy could not be computed: nothing is built (fail closed)."""


def _sha(*parts: Any) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str, ensure_ascii=False).encode()).hexdigest()


# -- copies ---------------------------------------------------------------------------


def _inside_local_root(path: Path) -> bool:
    return LOCAL_ROOT_NAME in Path(path).resolve().parts


def prepare_copies(sources: Sequence[Path], destination_root: Path, *, label: str) -> list[dict[str, Any]]:
    """Back up each source vault into ``destination_root/<name>-<label>``.

    ``destination_root`` must lie under a ``fixtures-local`` directory; a
    source named ``arxiv_v2`` is refused. Returns one record per copy (its
    path and the databases copied), aggregate only."""

    destination_root = Path(destination_root)
    if not _inside_local_root(destination_root):
        raise ValueError("copies must be made under a fixtures-local directory")
    copies: list[dict[str, Any]] = []
    for source in sources:
        source = Path(source)
        if source.name in FORBIDDEN_SOURCE_NAMES:
            raise ValueError(f"{source.name} is never copied for E0")
        if not (source / "learnloop.toml").is_file():
            raise ValueError("each source must be a vault root (learnloop.toml)")
        target = destination_root / f"{source.name}-{label}"
        databases = copy_tree_with_databases(source, target)
        for database in databases:
            to_rollback_journal(database)
        copies.append({"vault": source.name, "copy": str(target), "databases": len(databases),
                       "journal_mode": "delete"})
    return copies


def is_wal(database: Path) -> bool:
    """Whether a database file's header names the WAL format (read without SQLite)."""

    with open(database, "rb") as handle:
        header = handle.read(20)
    return len(header) >= 20 and header[:16] == b"SQLite format 3\x00" and header[18] == 2


def to_rollback_journal(database: Path) -> None:
    """Put a fresh copy in rollback-journal mode (its companion files go): a
    read-only open of a WAL database creates ``-wal``/``-shm`` files and
    rewrites the shared-memory index, which would be a write to the copy. The
    copy's content is unchanged (a backup copy's WAL is empty)."""

    connection = connect(Path(database))
    try:
        mode = connection.execute("PRAGMA journal_mode = DELETE").fetchone()[0]
    finally:
        connection.close()
    if str(mode).lower() != "delete":
        raise RuntimeError("could not put the copy in rollback-journal mode")


@dataclass
class CopyHandle:
    """A vault copy opened read-only."""

    root: Path
    vault: LoadedVault
    repository: Repository
    sqlite_path: Path

    @property
    def label(self) -> str:
        return self.root.name


def open_copy(root: Path, *, load_environment: bool = False) -> CopyHandle:
    """The copy's vault (no settings or dotenv unless asked) and a read-only,
    never-migrated repository."""

    root = Path(root)
    if root.name in FORBIDDEN_SOURCE_NAMES or root.name.split("-")[0] in FORBIDDEN_SOURCE_NAMES:
        raise ValueError("arxiv_v2 is outside E0")
    if not (root / "learnloop.toml").is_file():
        raise ValueError(f"{root} is not a vault root")
    vault = load_vault(root, load_environment=load_environment)
    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    if not Path(sqlite_path).exists():
        raise ValueError("the copy has no database")
    if is_wal(Path(sqlite_path)):
        # Even a read-only open of a WAL database writes its -wal/-shm files.
        raise ValueError("the copy is in WAL mode: make it with `learnloop experiments e0 prepare` "
                         "(rollback journal) so planning writes nothing to it")
    return CopyHandle(root, vault, Repository.attach(sqlite_path, read_only=True), Path(sqlite_path))


# -- inventory ------------------------------------------------------------------------


def alias(kind: str, value: str) -> str:
    """A stable public alias (reports never carry private ids, titles or paths)."""

    return f"{kind}_{hashlib.sha256(str(value).encode()).hexdigest()[:10]}"


@dataclass(frozen=True)
class ExtractionInfo:
    source_id: str
    extraction_id: str
    revision_id: str | None
    extractor: str | None
    extractor_version: str | None
    request_hash: str | None
    source_bytes_hash: str | None
    fingerprint: tuple[int, int]
    reader_enabled: bool
    title: str

    def public(self) -> dict[str, Any]:
        return {"source": alias("src", self.source_id), "extraction": alias("ext", self.extraction_id),
                "extractor": self.extractor, "extractor_version": self.extractor_version,
                "fingerprint": list(self.fingerprint), "reader_enabled": self.reader_enabled}


def extraction_infos(handle: CopyHandle) -> dict[str, ExtractionInfo]:
    repository = handle.repository
    infos: dict[str, ExtractionInfo] = {}
    with closing(connect(handle.sqlite_path, read_only=True)) as connection:
        for extraction_id, extraction in sorted(current_extractions(repository).items()):
            run = repository.get_extraction_run(extraction_id) or {}
            revision = repository.get_source_revision(str(run.get("revision_id") or "")) or {}
            infos[extraction_id] = ExtractionInfo(
                source_id=extraction.source_id, extraction_id=extraction_id,
                revision_id=run.get("revision_id"), extractor=run.get("extractor"),
                extractor_version=run.get("extractor_version"),
                request_hash=run.get("extraction_request_hash"),
                source_bytes_hash=revision.get("asset_hash"),
                fingerprint=tuple(extraction_fingerprint(connection, extraction_id)),
                reader_enabled=extraction.reader_enabled, title=extraction.title,
            )
    return infos


# -- policy ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PolicySnapshot:
    """What a model may never read, by key, with the reason."""

    withheld: Mapping[SpanKey, str]
    whole_extractions: frozenset[str]
    extraction_fingerprints: Mapping[str, tuple[int, int]]
    fingerprint: str

    def verdict(self, extraction_id: str, span_id: str) -> str | None:
        if extraction_id in self.whole_extractions:
            return "exam_or_held_out"
        return self.withheld.get((str(extraction_id), str(span_id)))

    def permitted(self, extraction_id: str, span_id: str) -> bool:
        return self.verdict(extraction_id, span_id) is None

    def counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for reason in self.withheld.values():
            counts[reason] = counts.get(reason, 0) + 1
        return dict(sorted(counts.items()))


def policy_snapshot(handle: CopyHandle, infos: Mapping[str, ExtractionInfo]) -> PolicySnapshot:
    """Exam/held-out (D12) and solution/assessment-lane material, fail closed."""

    try:
        keys: list[SpanKey] = []
        with closing(connect(handle.sqlite_path, read_only=True)) as connection:
            for extraction_id in infos:
                keys.extend((extraction_id, block.span_id) for block in extraction_blocks(connection, extraction_id))
        exam = EM.exam_material(handle.vault, handle.repository).material
        withheld: dict[SpanKey, str] = {key: reason for key, reason in
                                        model_reader_withheld(handle.vault, handle.repository, keys).items()}
        for key in keys:
            if exam.covers(key[0], key[1]):
                withheld[key] = "exam_or_held_out"
        whole = frozenset(extraction for extraction in exam.extractions if extraction in infos)
    except Exception as exc:  # any failure: nothing is built
        raise PolicyUnavailable(f"material policy unavailable ({type(exc).__name__})") from None
    fingerprints = {key: info.fingerprint for key, info in infos.items()}
    fingerprint = _sha(sorted((list(key), reason) for key, reason in withheld.items()), sorted(whole),
                       sorted((key, list(value)) for key, value in fingerprints.items()))
    return PolicySnapshot(withheld, whole, fingerprints, fingerprint)


@dataclass(frozen=True)
class ArtifactDependency:
    """What an artifact (window, vector, header, label, packet) was built from."""

    extraction_id: str
    extraction_fingerprint: tuple[int, int]
    keys: tuple[SpanKey, ...]
    policy_fingerprint: str

    def as_dict(self) -> dict[str, Any]:
        return {"extraction_id": self.extraction_id, "extraction_fingerprint": list(self.extraction_fingerprint),
                "keys": [list(key) for key in self.keys], "policy_fingerprint": self.policy_fingerprint}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> ArtifactDependency:
        return cls(str(value["extraction_id"]), tuple(value["extraction_fingerprint"]),
                   tuple((str(key[0]), str(key[1])) for key in value["keys"]), str(value["policy_fingerprint"]))


def stale_reasons(dependency: ArtifactDependency, snapshot: PolicySnapshot) -> list[str]:
    """Why an artifact may no longer be used (empty: still valid)."""

    reasons: list[str] = []
    current = snapshot.extraction_fingerprints.get(dependency.extraction_id)
    if current is None:
        reasons.append("extraction_not_current")
    elif tuple(current) != tuple(dependency.extraction_fingerprint):
        reasons.append("re_extracted")
    newly = sorted({snapshot.verdict(*key) for key in dependency.keys if snapshot.verdict(*key) is not None})
    reasons.extend(f"now_withheld:{reason}" for reason in newly)
    return reasons


def invalidate(artifacts: Mapping[str, ArtifactDependency], snapshot: PolicySnapshot) -> dict[str, list[str]]:
    """Every stale artifact id with its reasons (fresh ones are absent)."""

    stale: dict[str, list[str]] = {}
    for artifact_id, dependency in sorted(artifacts.items()):
        reasons = stale_reasons(dependency, snapshot)
        if reasons:
            stale[artifact_id] = reasons
    return stale


# -- candidate units -------------------------------------------------------------------


@dataclass(frozen=True)
class Member:
    span_id: str
    start: int
    end: int


@dataclass(frozen=True)
class CandidateUnit:
    unit_id: str
    source_id: str
    extraction_id: str
    section: tuple[str, ...]
    segment: int
    members: tuple[Member, ...]
    text: str
    tokens: int
    kind: str
    label: str | None = None
    lead: str | None = None
    tags: tuple[str, ...] = ()

    @property
    def keys(self) -> tuple[SpanKey, ...]:
        return tuple(dict.fromkeys((self.extraction_id, member.span_id) for member in self.members))

    def public(self) -> dict[str, Any]:
        return {"unit": self.unit_id, "kind": self.kind, "tokens": self.tokens, "members": len(self.members),
                "tags": list(self.tags)}


def _kind(block: BlockRow) -> str:
    return (block.block_type or "").replace(" ", "").lower()


def _is_content(block: BlockRow) -> bool:
    return block.block_type not in EXCLUDED_BLOCK_TYPES and bool((block.text or "").strip())


def _bare_equation(block: BlockRow) -> bool:
    if _kind(block) in _EQUATION_TYPES:
        return True
    stripped = (block.text or "").strip()
    return (stripped.startswith("$$") and stripped.endswith("$$")) or (
        stripped.startswith("\\[") and stripped.endswith("\\]"))


def split_offsets(text: str, max_tokens: int) -> list[tuple[int, int]]:
    """Deterministic ``[start, end)`` pieces of ``text`` within ``max_tokens``:
    cut at the last sentence or line boundary that fits, else the last space,
    else a hard cut. The pieces cover the text exactly, in order."""

    pieces: list[tuple[int, int]] = []
    start = 0
    length = len(text)
    while start < length:
        end = length
        if token_estimate(text[start:end]) <= max_tokens:
            pieces.append((start, end))
            break
        # The longest prefix within the bound (binary search on characters).
        low, high = start + 1, length
        while low < high:
            middle = (low + high + 1) // 2
            if token_estimate(text[start:middle]) <= max_tokens:
                low = middle
            else:
                high = middle - 1
        limit = low
        window = text[start:limit]
        cut = None
        for match in _SPLIT_AT.finditer(window):
            if match.end() > len(window) // 2:
                cut = start + match.end()
        if cut is None:
            space = window.rfind(" ")
            cut = start + space + 1 if space > len(window) // 2 else limit
        pieces.append((start, cut))
        start = cut
    return pieces


def _unit(extraction: ExtractionInfo, section: tuple[str, ...], segment: int, members: list[Member],
          texts: list[str], kind: str, label: str | None, lead: str | None) -> CandidateUnit:
    text = "\n".join(texts)
    unit_id = "u_" + _sha(extraction.extraction_id, [asdict(member) for member in members])[:16]
    tags = []
    if kind == "captions":
        tags.append("transcript")
    if any(_EQ_IN.search(part) for part in texts):
        tags.append("equation")
    if label:
        tags.append("numbered")
    return CandidateUnit(unit_id, extraction.source_id, extraction.extraction_id, section, segment,
                         tuple(members), text, token_estimate(text), kind, label, lead, tuple(tags))


_EQ_IN = re.compile(r"\$\$|\\\[|\\begin\{(?:equation|align)")


def build_units(extraction: ExtractionInfo, blocks: Sequence[BlockRow], titles: Mapping[str, str],
                policy: PolicySnapshot) -> list[CandidateUnit]:
    """The common candidate map of one extraction (deterministic)."""

    units: list[CandidateUnit] = []
    segment = 0
    # The open unit: (section, members, texts, kind, label, lead).
    open_unit: dict[str, Any] | None = None
    pending_equation: tuple[BlockRow, tuple[str, ...]] | None = None
    min_caption, max_caption = pins.CAPTION_TARGET_TOKENS

    def flush() -> None:
        nonlocal open_unit
        if open_unit is not None:
            units.append(_unit(extraction, open_unit["section"], segment, open_unit["members"], open_unit["texts"],
                               open_unit["kind"], open_unit["label"], open_unit["lead"]))
        open_unit = None

    def flush_pending() -> None:
        nonlocal pending_equation
        if pending_equation is not None:
            block, section = pending_equation
            units.append(_unit(extraction, section, segment, [Member(block.span_id, 0, len(block.text))],
                               [block.text], "equation", None, None))
        pending_equation = None

    for block in blocks:
        if not _is_content(block):
            continue
        if not policy.permitted(extraction.extraction_id, block.span_id):
            # A hard boundary: nothing on either side is ever joined across it.
            flush()
            flush_pending()
            segment += 1
            continue
        section = tuple(section_path(block, titles))
        if open_unit is not None and open_unit["section"] != section:
            flush()
        if pending_equation is not None and pending_equation[1] != section:
            flush_pending()
        tokens = token_estimate(block.text)
        if _kind(block) in _CAPTION_TYPES:
            if open_unit is not None and open_unit["kind"] == "captions":
                current = token_estimate("\n".join(open_unit["texts"]))
                if current < min_caption and current + tokens <= max_caption:
                    open_unit["members"].append(Member(block.span_id, 0, len(block.text)))
                    open_unit["texts"].append(block.text)
                    continue
            flush()
            flush_pending()
            open_unit = {"section": section, "members": [Member(block.span_id, 0, len(block.text))],
                         "texts": [block.text], "kind": "captions", "label": None, "lead": None}
            continue
        if _bare_equation(block):
            if (open_unit is not None and open_unit["kind"] in ("block", "equation_attached")
                    and token_estimate("\n".join(open_unit["texts"])) + tokens <= pins.UNIT_MAX_TOKENS):
                open_unit["members"].append(Member(block.span_id, 0, len(block.text)))
                open_unit["texts"].append(block.text)
                open_unit["kind"] = "equation_attached"
                continue
            flush()
            flush_pending()
            pending_equation = (block, section)
            continue
        flush()
        label_obj = numbered_label(block.text, block.block_type)
        label = f"{label_obj.kind or ''} {label_obj.number}".strip() if label_obj is not None else None
        lead = lead_role(block.text)
        if tokens > pins.UNIT_MAX_TOKENS:
            flush_pending()
            pieces = split_offsets(block.text, pins.UNIT_MAX_TOKENS)
            for start, end in pieces:
                units.append(_unit(extraction, section, segment, [Member(block.span_id, start, end)],
                                   [block.text[start:end]], "split", label if start == 0 else None,
                                   lead if start == 0 else None))
            continue
        members = [Member(block.span_id, 0, len(block.text))]
        texts = [block.text]
        kind = "block"
        if pending_equation is not None:
            equation = pending_equation[0]
            if token_estimate(equation.text) + tokens <= pins.UNIT_MAX_TOKENS and label is None:
                members.insert(0, Member(equation.span_id, 0, len(equation.text)))
                texts.insert(0, equation.text)
                kind = "equation_attached"
                pending_equation = None
            else:
                flush_pending()
        open_unit = {"section": section, "members": members, "texts": texts, "kind": kind,
                     "label": label, "lead": lead}
    flush()
    flush_pending()
    return units


# -- windows --------------------------------------------------------------------------


@dataclass(frozen=True)
class Window:
    window_id: str
    extraction_id: str
    segment: int
    unit_ids: tuple[str, ...]
    tokens: int
    whole_segment: bool = False


def _chunk_tokens(unit: CandidateUnit) -> int:
    return unit.tokens + pins.CHUNK_MARKER_TOKENS


def build_windows(units: Sequence[CandidateUnit], *, window_tokens: int = pins.WINDOW_TOKENS) -> list[Window]:
    """Section-first packing within one extraction's policy segment; no
    overlap; every unit in exactly one window. A unit larger than the window
    on its own (never: units are capped at ``UNIT_MAX_TOKENS``) is refused."""

    windows: list[Window] = []
    by_segment: dict[tuple[str, int], list[CandidateUnit]] = {}
    for unit in units:
        by_segment.setdefault((unit.extraction_id, unit.segment), []).append(unit)
    for (extraction_id, segment), members in by_segment.items():
        runs: list[list[CandidateUnit]] = []
        for unit in members:
            if runs and runs[-1][-1].section == unit.section:
                runs[-1].append(unit)
            else:
                runs.append([unit])
        current: list[CandidateUnit] = []
        current_tokens = 0

        def close() -> None:
            nonlocal current, current_tokens
            if current:
                ids = tuple(unit.unit_id for unit in current)
                windows.append(Window("w_" + _sha(extraction_id, segment, ids)[:16], extraction_id, segment, ids,
                                      current_tokens))
            current, current_tokens = [], 0

        for run in runs:
            run_tokens = sum(_chunk_tokens(unit) for unit in run)
            if current and current_tokens + run_tokens > window_tokens:
                close()
            if run_tokens <= window_tokens:
                current.extend(run)
                current_tokens += run_tokens
                continue
            for unit in run:
                tokens = _chunk_tokens(unit)
                if tokens > window_tokens:
                    raise ValueError("a candidate unit is larger than a window")
                if current and current_tokens + tokens > window_tokens:
                    close()
                current.append(unit)
                current_tokens += tokens
        close()
    return windows


def whole_segment_windows(units: Sequence[CandidateUnit], *, limit_tokens: int) -> list[Window]:
    """One window per permitted segment that fits ``limit_tokens`` whole (the
    secondary whole-source arm); a segment that does not fit gets none. The
    fit is judged by the guaranteed upper bound (``token_upper_bound``), never
    the estimate, so a whole window can never pass the provider's limit
    (Codex review F15)."""

    found: list[Window] = []
    by_segment: dict[tuple[str, int], list[CandidateUnit]] = {}
    for unit in units:
        by_segment.setdefault((unit.extraction_id, unit.segment), []).append(unit)
    for (extraction_id, segment), members in by_segment.items():
        bound = sum(token_upper_bound(unit.text) + pins.CHUNK_MARKER_TOKENS for unit in members)
        tokens = sum(_chunk_tokens(unit) for unit in members)
        if bound <= limit_tokens:
            ids = tuple(unit.unit_id for unit in members)
            found.append(Window("ws_" + _sha(extraction_id, segment, ids)[:16], extraction_id, segment, ids,
                                tokens, whole_segment=True))
    return found


def assert_partition(units: Sequence[CandidateUnit], windows: Sequence[Window]) -> None:
    """Every unit in exactly one (non-whole-segment) window."""

    seen: dict[str, int] = {}
    for window in windows:
        if window.whole_segment:
            continue
        for unit_id in window.unit_ids:
            seen[unit_id] = seen.get(unit_id, 0) + 1
    expected = {unit.unit_id for unit in units}
    if set(seen) != expected or any(count != 1 for count in seen.values()):
        raise AssertionError("windows do not partition the candidate units")


# -- dependencies ---------------------------------------------------------------------


def dependency_map(units: Sequence[CandidateUnit], text: ExtractionText,
                   policy: PolicySnapshot) -> dict[str, dict[str, Any]]:
    """Each unit's numbered references resolved to the units holding them
    (same extraction only; a withheld target is recorded, never followed)."""

    unit_of_span: dict[str, str] = {}
    for unit in units:
        for member in unit.members:
            unit_of_span.setdefault(member.span_id, unit.unit_id)
    found: dict[str, dict[str, Any]] = {}
    for unit in units:
        anchor = text.position(unit.members[0].span_id)
        if anchor is None:
            continue
        own = (unit.label or "").split()[-1] if unit.label else None
        entry = {"targets": [], "unresolved": 0, "withheld": 0}
        for reference in numbered_references(unit.text):
            if own is not None and reference.number == own:
                continue
            target = text.resolve(reference, anchor)
            if target is None:
                if reference.kind is not None:
                    entry["unresolved"] += 1
                continue
            block = text.blocks[target]
            if not policy.permitted(text.extraction_id, block.span_id):
                entry["withheld"] += 1
                continue
            target_unit = unit_of_span.get(block.span_id)
            if target_unit is not None and target_unit != unit.unit_id and target_unit not in entry["targets"]:
                entry["targets"].append(target_unit)
        if entry["targets"] or entry["unresolved"] or entry["withheld"]:
            found[unit.unit_id] = entry
    return found


def support_outside_windows(dependencies: Mapping[str, Mapping[str, Any]], windows: Sequence[Window]) -> dict[str, int]:
    """How many resolved dependencies fall outside their unit's grouped window."""

    window_of: dict[str, str] = {}
    for window in windows:
        if not window.whole_segment:
            for unit_id in window.unit_ids:
                window_of[unit_id] = window.window_id
    inside = outside = 0
    for unit_id, entry in dependencies.items():
        for target in entry["targets"]:
            if window_of.get(target) == window_of.get(unit_id):
                inside += 1
            else:
                outside += 1
    return {"inside": inside, "outside": outside}


# -- families -------------------------------------------------------------------------


def _title_stem(title: str) -> str:
    value = re.sub(r"[^a-z0-9]+", " ", str(title).lower()).strip()
    value = re.sub(r"\b(edition|ed|v\d+|\d+(st|nd|rd|th))\b", " ", value)
    return " ".join(value.split()[:6])


def families(infos: Mapping[str, ExtractionInfo], *, vault_label: str) -> dict[str, str]:
    """``{source_id: family_id}``: alternate editions and overlapping copies
    (same source bytes or the same title stem) share a family."""

    groups: dict[str, str] = {}
    by_key: dict[str, str] = {}
    for info in sorted(infos.values(), key=lambda value: value.source_id):
        keys = [f"bytes:{info.source_bytes_hash}" if info.source_bytes_hash else None,
                f"title:{_title_stem(info.title)}" if _title_stem(info.title) else None]
        family = next((by_key[key] for key in keys if key and key in by_key), None)
        if family is None:
            family = alias("fam", f"{vault_label}:{info.source_id}")
        for key in keys:
            if key:
                by_key.setdefault(key, family)
        groups[info.source_id] = family
    return groups


def reserve_families(family_ids: Iterable[str], *, share: float, seed: int = pins.SEED) -> dict[str, str]:
    """``{family: "development" | "reserved"}``, fixed before any question is
    written. ``share`` 0 (the E0 default: no sealed bank by assumption, §5.1.4)
    reserves nothing; leave-family-out checks then run on development only."""

    ordered = sorted(set(family_ids), key=lambda family: _sha(seed, family))
    reserved = set(ordered[: int(len(ordered) * max(0.0, min(1.0, share)))])
    return {family: ("reserved" if family in reserved else "development") for family in sorted(ordered)}


# -- the snapshot ---------------------------------------------------------------------


@dataclass
class CorpusSnapshot:
    vault_label: str
    infos: dict[str, ExtractionInfo]
    policy: PolicySnapshot
    blocks: dict[str, list[BlockRow]]
    titles: dict[str, dict[str, str]]
    units: list[CandidateUnit]
    windows: list[Window]
    whole_windows: dict[str, list[Window]]
    dependencies: dict[str, dict[str, Any]]
    family_of_source: dict[str, str]
    family_status: dict[str, str]
    outline_units: dict[str, list[Any]] = field(default_factory=dict)
    sqlite_path: Path | None = None

    def unit(self, unit_id: str) -> CandidateUnit:
        return self._units_by_id()[unit_id]

    def _units_by_id(self) -> dict[str, CandidateUnit]:
        cache = getattr(self, "_by_id", None)
        if cache is None:
            cache = {unit.unit_id: unit for unit in self.units}
            self._by_id = cache
        return cache

    def unit_dependency(self, unit: CandidateUnit) -> ArtifactDependency:
        return ArtifactDependency(unit.extraction_id, self.infos[unit.extraction_id].fingerprint, unit.keys,
                                  self.policy.fingerprint)

    def window_dependency(self, window: Window) -> ArtifactDependency:
        keys: list[SpanKey] = []
        for unit_id in window.unit_ids:
            keys.extend(self.unit(unit_id).keys)
        return ArtifactDependency(window.extraction_id, self.infos[window.extraction_id].fingerprint,
                                  tuple(dict.fromkeys(keys)), self.policy.fingerprint)

    def inventory(self) -> dict[str, Any]:
        """Aggregate inventory: counts and token sizes, no text, ids aliased."""

        sources = []
        for extraction_id, info in sorted(self.infos.items(), key=lambda item: alias("ext", item[0])):
            blocks = self.blocks[extraction_id]
            content = [block for block in blocks if _is_content(block)]
            types: dict[str, int] = {}
            for block in blocks:
                types[block.block_type] = types.get(block.block_type, 0) + 1
            units = [unit for unit in self.units if unit.extraction_id == extraction_id]
            withheld = sum(1 for block in content if not self.policy.permitted(extraction_id, block.span_id))
            sources.append({
                **info.public(), "family": self.family_of_source.get(info.source_id),
                "blocks": len(blocks), "content_blocks": len(content), "withheld_blocks": withheld,
                "block_types": dict(sorted(types.items())),
                "content_tokens": sum(token_estimate(block.text) for block in content),
                "permitted_tokens": sum(unit.tokens for unit in units),
                "units": len(units),
                "windows": sum(1 for window in self.windows if window.extraction_id == extraction_id),
                "whole_source_fits": {name: any(window.extraction_id == extraction_id for window in found)
                                      for name, found in sorted(self.whole_windows.items())},
                "outline_units": len(self.outline_units.get(extraction_id, [])),
            })
        kinds: dict[str, int] = {}
        for unit in self.units:
            kinds[unit.kind] = kinds.get(unit.kind, 0) + 1
        return {
            "vault": self.vault_label, "sources": sources, "units": len(self.units),
            "unit_kinds": dict(sorted(kinds.items())), "windows": len(self.windows),
            "unit_tokens": sum(unit.tokens for unit in self.units),
            "window_tokens": sum(window.tokens for window in self.windows),
            "policy": {"fingerprint": self.policy.fingerprint, "withheld": self.policy.counts(),
                       "whole_extractions_withheld": len(self.policy.whole_extractions)},
            "dependencies": {"units_with_references": len(self.dependencies),
                             "resolved": sum(len(entry["targets"]) for entry in self.dependencies.values()),
                             "unresolved": sum(entry["unresolved"] for entry in self.dependencies.values()),
                             "withheld_targets": sum(entry["withheld"] for entry in self.dependencies.values()),
                             "support_vs_windows": support_outside_windows(self.dependencies, self.windows)},
            "families": {"count": len(set(self.family_of_source.values())),
                         "status": dict(sorted(_count(self.family_status.values()).items()))},
        }


def _count(values: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def build_snapshot(handle: CopyHandle, *, reserve_share: float = 0.0,
                   whole_limits: Mapping[str, int] | None = None) -> CorpusSnapshot:
    """The frozen corpus of one copy (read-only; deterministic)."""

    infos = extraction_infos(handle)
    policy = policy_snapshot(handle, infos)
    blocks: dict[str, list[BlockRow]] = {}
    titles: dict[str, dict[str, str]] = {}
    outline: dict[str, list[Any]] = {}
    units: list[CandidateUnit] = []
    dependencies: dict[str, dict[str, Any]] = {}
    with closing(connect(handle.sqlite_path, read_only=True)) as connection:
        for extraction_id, info in infos.items():
            blocks[extraction_id] = extraction_blocks(connection, extraction_id)
            titles[extraction_id] = section_header_titles(connection, extraction_id)
            outline[extraction_id] = extraction_units(connection, extraction_id)
    for extraction_id, info in infos.items():
        extraction_units_list = build_units(info, blocks[extraction_id], titles[extraction_id], policy)
        units.extend(extraction_units_list)
        dependencies.update(dependency_map(extraction_units_list, ExtractionText(extraction_id, blocks[extraction_id]),
                                           policy))
    windows = build_windows(units)
    assert_partition(units, windows)
    limits = whole_limits if whole_limits is not None else {
        name: pin.max_tokens_per_document for name, pin in pins.EMBEDDING_PINS.items() if pin.method == "grouped"}
    whole = {name: whole_segment_windows(units, limit_tokens=limit) for name, limit in sorted(limits.items())}
    family_of_source = families(infos, vault_label=handle.label)
    status = reserve_families(family_of_source.values(), share=reserve_share)
    return CorpusSnapshot(handle.label, infos, policy, blocks, titles, units, windows, whole, dependencies,
                          family_of_source, status, outline, handle.sqlite_path)
