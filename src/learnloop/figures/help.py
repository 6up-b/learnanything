"""Reader RW5d P3: figures as a help kind inside attempts (spec_reader_show_me_figures_v1 §6.4, §11.2-§11.4).

The pure reads the attempt hosts need; the writes are the sidecar's (the
help row and its reveal are written in one transaction with the delivery,
as a hint's are, ``learnloop_sidecar.handlers.figures``):

* :func:`reveal_text`: every model-written string of a figure (what it
  demonstrates, its assumptions, labels, annotations and every other string
  of its spec or program) and its readouts at their defaults as formatted:
  the text the existing overlap check reads against the item's key, so a
  figure that states the answer writes the ``tutor_answer`` reveal with basis
  ``figure:<id>`` (§11.2 row 2).
* :func:`qualifying_figure`: the hint chooser's ``explore_figure``
  precondition (§11.4): a shown figure that already exists whose place in the
  books treats the item's learning object, that was not built from the
  item's own blocks (its exercise, solution or worked answer) and does not
  overlap the item's key, and that is not withheld now. No figure is ever
  built for a hint: the option costs no wait and no spend.
* :func:`chain_root`: a figure and its "not right?" versions are one figure
  for the once-per-attempt count (§11.4b).

Nothing here writes evidence, and nothing that writes evidence imports this
package (the ``evidence-never-reads-figures`` contract): a figure reaches an
attempt only as one hint-equivalent through the hint service's existing
submit fold (``hints_used``, its existing meaning) and, on overlap, the
existing reveal row. Figures never reach the grader.
"""
from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping, Sequence
from contextlib import closing
from typing import Any

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import figures as store
from learnloop.figure_admission import help_kind_enabled

#: The ladder level a figure's help row is written at (§11.2): one
#: hint-equivalent in the fold, the level of ``explore_figure`` (§11.4). A
#: structural identity (the hints spec's level 2, "where it stops holding"),
#: never a weight.
FIGURE_LEVEL = 2
#: The hint kind the chooser serves a figure as (``help_assists.hint_kind``).
EXPLORE_FIGURE = "explore_figure"
#: keep: read size: the newest shown figures the chooser's precondition
#: scans for one that qualifies (a bound on a local read, never a weight,
#: margin or threshold).
QUALIFYING_SCAN = 200
#: The CA2 vocabulary's dim line under the box, per host (§6.4).
COST_LINES: Mapping[str, str] = {
    "feedback": "show me is free here",
    "open": "a figure on this counts as a hint",
    "cold": "a figure on this makes this practice with help ◌",
}
#: The banner after a cold take step (§11.3).
TAKE_STEP_BANNER = "Practice with help ◌ — you asked for a figure"
#: The chooser's line label (§11.4).
EXPLORE_LABEL = "a figure to explore"
#: The coverage treatments that say a section is about a learning object
#: (curriculum C0a's structural vocabulary; ``mentions`` and ``not_about`` do not).
_TREATS = ("introduces", "develops", "applies")


def enabled(vault: Any) -> bool:
    """``figures.help_kind_enabled`` (under ``figures.enabled`` and ``show_me_enabled``)."""

    return help_kind_enabled(vault)


# ---------------------------------------------------------------------------
# The figure's text, for the reveal check
# ---------------------------------------------------------------------------

#: The keys whose values are the figure's words (§11.2 row 2: what it
#: demonstrates, its assumptions, labels, annotations, captions, prediction
#: prompts and choices): its expressions, enums and span ids are not text.
_TEXT_KEYS = frozenset({"demonstrates", "text", "label", "labels", "title", "caption", "annotation",
                        "annotations", "prompt", "choices", "note", "legend", "readout_label"})
#: A string literal in a sketch's program (its drawn words).
_LITERAL = re.compile(r'"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\'')


def _words(value: Any, *, keyed: bool = False) -> Iterable[str]:
    """The text values of a figure's JSON: every string under a text key
    (:data:`_TEXT_KEYS`), however deep; a sketch's program contributes its
    string literals."""

    if isinstance(value, str):
        if keyed and value.strip():
            yield value
    elif isinstance(value, Mapping):
        for key, item in value.items():
            if key == "code" and isinstance(item, str):
                yield from (first or second for first, second in _LITERAL.findall(item) if (first or second).strip())
            else:
                yield from _words(item, keyed=keyed or key in _TEXT_KEYS)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _words(item, keyed=keyed)


def _readouts(spec_json: str) -> list[str]:
    """A grammar figure's readouts and highlighted values at the defaults, as
    the figure formats them (a figure that computes the item's number shows it)."""

    from learnloop.figures import spec as S

    try:
        evaluated = S.evaluate_figure(S.parse_spec(spec_json))
    except Exception:  # noqa: BLE001 - an unparseable spec contributes its strings only
        return []
    out: list[str] = []
    for panel in evaluated.get("panels") or ():
        values: list[tuple[Any, str]] = []
        if panel.get("kind") == "readout":
            values.append((panel.get("value"), str(panel.get("format") or "number")))
        highlight = panel.get("highlight") or {}
        if highlight.get("value") is not None:
            values.append((highlight.get("value"), "number"))
        if panel.get("determinant") is not None:
            values.append((panel.get("determinant"), "number"))
        for value, form in values:
            if value is None:
                continue
            number = float(value)
            out.append(f"{number * 100:.4g}%" if form == "percent" else f"{number:.4g}")
    return out


def reveal_text(row: Mapping[str, Any]) -> str:
    """A stored figure's words (:func:`_words`: what it demonstrates, its
    assumptions, labels, annotations, prompts; a sketch's drawn strings) and
    its readouts at the defaults as formatted (§11.2 row 2, §11.4b): the text
    the overlap check reads. Its goal and its verification report are not
    the author's output."""

    raw = row.get("spec_json")
    if not raw:
        return ""
    try:
        data = json.loads(raw) if isinstance(raw, str) else dict(raw)
    except (TypeError, ValueError):
        return str(raw)
    parts = list(_words(data))
    if row.get("spec_version") == _grammar_version():
        parts += _readouts(raw if isinstance(raw, str) else json.dumps(raw))
    return "\n".join(parts)


def _grammar_version() -> str:
    from learnloop.figures import spec as S

    return S.SPEC_VERSION


# ---------------------------------------------------------------------------
# One figure per attempt, its versions included
# ---------------------------------------------------------------------------

def chain_root(connection: Any, figure_id: str) -> str:
    """The first version of ``figure_id``'s "not right?" chain (itself when
    it supersedes nothing); a rich figure's quick version is its root too."""

    seen: set[str] = set()
    current = str(figure_id)
    while current and current not in seen:
        seen.add(current)
        row = connection.execute(
            "SELECT supersedes_id, fuller_of_id FROM interactive_figures WHERE id = ?", (current,)).fetchone()
        if row is None:
            break
        parent = row[0] or row[1]
        if not parent:
            break
        current = str(parent)
    return current


# ---------------------------------------------------------------------------
# The chooser's precondition
# ---------------------------------------------------------------------------

def figure_keys(repository: Repository, row: Mapping[str, Any]) -> list[tuple[str, str]]:
    """Every ``(extraction_id, span_id)`` a figure is placed at or built from:
    its anchor, its region and crop, the passages around it, its retrieved
    passages and (a goal-only figure) where it was asked."""

    from learnloop.figure_admission import figure_home_keys

    keys: list[tuple[str, str]] = []
    if row.get("extraction_id"):
        spans = [*(row.get("span_ids") or ()), *(row.get("input_span_ids") or ())]
        if (row.get("region") or {}).get("span_id"):
            spans.append(str(row["region"]["span_id"]))
        keys += [(str(row["extraction_id"]), str(span)) for span in spans if span]
    keys += [(str(key[0]), str(key[1])) for key in row.get("input_span_keys") or () if len(key) == 2]
    if not row.get("span_ids") and not row.get("region") and row.get("id"):
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            keys += [(str(key[0]), str(key[1])) for key in figure_home_keys(connection, str(row["id"]))]
    return list(dict.fromkeys(keys))


def _placed_keys(repository: Repository, row: Mapping[str, Any]) -> list[tuple[str, str]]:
    """Where a figure sits in the books: its anchor (and region), or its
    retrieved passages and the reading positions it was asked at."""

    from learnloop.figure_admission import figure_home_keys

    if row.get("extraction_id") and (row.get("span_ids") or row.get("region")):
        spans = list(row.get("span_ids") or ())
        if (row.get("region") or {}).get("span_id"):
            spans.append(str(row["region"]["span_id"]))
        return [(str(row["extraction_id"]), str(span)) for span in dict.fromkeys(spans)]
    keys = [(str(key[0]), str(key[1])) for key in row.get("input_span_keys") or () if len(key) == 2]
    if row.get("id"):
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            keys += [(str(key[0]), str(key[1])) for key in figure_home_keys(connection, str(row["id"]))]
    return list(dict.fromkeys(keys))


class _SectionTopics:
    """The learning objects a passage's section treats: its provenance links
    and (curriculum C0a) its coverage rows that say the section is about the
    object, the learner's corrections standing over the judge. Cached per
    read."""

    def __init__(self, vault: Any, repository: Repository) -> None:
        self.vault = vault
        self.repository = repository
        self._sections: dict[str, dict[str, str]] = {}
        self._los: dict[tuple[str, str], set[str]] = {}

    def _section(self, extraction_id: str, span_id: str) -> str | None:
        if extraction_id not in self._sections:
            from learnloop.reader.reader_guidance import extraction_sections

            ir = self.repository.load_document_ir(extraction_id)
            if ir is None:
                self._sections[extraction_id] = {}
            else:
                _sections, _blocks, span_to_section = extraction_sections(ir)
                self._sections[extraction_id] = {str(span): str(section)
                                                 for span, section in span_to_section.items() if section is not None}
        return self._sections[extraction_id].get(span_id)

    def treats(self, extraction_id: str, span_id: str) -> set[str]:
        section = self._section(extraction_id, span_id)
        if section is None:
            return set()
        key = (extraction_id, section)
        if key not in self._los:
            from learnloop.reader.reader_progression import learning_objects_for_section

            found: set[str] = set()
            try:
                found |= {str(lo) for lo in learning_objects_for_section(
                    self.vault, self.repository, extraction_id=extraction_id, section_id=section)}
            except Exception:  # noqa: BLE001 - provenance unreadable: coverage alone
                pass
            found |= _covered(self.repository, extraction_id, section)
            self._los[key] = found
        return self._los[key]


def _covered(repository: Repository, extraction_id: str, section_id: str) -> set[str]:
    """Coverage's learning objects for a section: the newest learner row per
    object stands (``is_about`` counts, ``not_about``/``none`` removes), else
    a judge row that says the section treats it."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'section_coverage'"
                              ).fetchone() is None:
            return set()
        rows = connection.execute(
            "SELECT learning_object_id, treatment, learner_override FROM section_coverage "
            "WHERE extraction_id = ? AND section_id = ? ORDER BY created_at, id",
            (extraction_id, section_id)).fetchall()
    judged: set[str] = set()
    learner: dict[str, str] = {}
    for lo_id, treatment, override in rows:
        if override is not None:
            learner[str(lo_id)] = str(override)
        elif treatment in _TREATS:
            judged.add(str(lo_id))
    return {lo for lo in judged if learner.get(lo) not in ("not_about", "none")} | {
        lo for lo, override in learner.items() if override == "is_about"}


def qualifying_figure(vault: Any, repository: Repository, item: Any, *,
                      exclude_roots: Sequence[str] = ()) -> dict[str, Any] | None:
    """The newest shown figure the chooser may offer for ``item`` as
    ``explore_figure`` (§11.4), or None: its place in the books treats the
    item's learning object; none of the passages it was placed at or built
    from is the item's own (``item_exclusions``: its exercise, solution or
    worked answer); its text does not overlap the item's key; it can be
    drawn and shown now (switches, held-out material). ``exclude_roots``:
    figures already opened in this attempt (their chain roots)."""

    from learnloop.figures import service as FS
    from learnloop.source_retrieval.corpus import item_exclusions
    from learnloop.tutor.tutor_qa import span_leaks_expected

    if not enabled(vault):
        return None
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if not store.has_tables(connection):
            return None
        rows = store.shown_figures(connection, FS.SPEC_VERSIONS, limit=QUALIFYING_SCAN)
        superseded = {str(row[0]) for row in connection.execute(
            "SELECT supersedes_id FROM interactive_figures WHERE supersedes_id IS NOT NULL")}
        roots = {str(row["id"]): chain_root(connection, str(row["id"])) for row in rows}
    excluded_roots = set(exclude_roots)
    own = None
    topics = _SectionTopics(vault, repository)
    for row in rows:
        figure_id = str(row["id"])
        if figure_id in superseded or roots.get(figure_id) in excluded_roots:
            continue
        if FS.show_me_row(row) and not FS.show_me_enabled(vault):
            continue
        if not FS.drawable_now(vault, row) or FS.advanced_off_row(vault, row) is not row \
                or FS.sketch_off_row(vault, row) is not row:
            continue
        placed = _placed_keys(repository, row)
        if not any(item.learning_object_id in topics.treats(key[0], key[1]) for key in placed):
            continue
        if own is None:
            own = item_exclusions(repository, item)
        keys = figure_keys(repository, row)
        if any(key in own.spans or key[0] in own.extractions for key in keys):
            continue
        if span_leaks_expected(reveal_text(row), item.expected_answer):
            continue
        if FS.row_withheld(vault, repository, row) is not None:
            continue
        return row
    return None


def offer_view(row: Mapping[str, Any]) -> dict[str, Any]:
    """What the chooser's served line carries (§11.4: one line that opens the figure)."""

    return {"figure_id": str(row["id"]), "label": EXPLORE_LABEL, "goal_text": row.get("goal_text"),
            "kind": row.get("kind"), "tier": row.get("tier") or "grammar"}


__all__ = [
    "COST_LINES",
    "EXPLORE_FIGURE",
    "EXPLORE_LABEL",
    "FIGURE_LEVEL",
    "QUALIFYING_SCAN",
    "TAKE_STEP_BANNER",
    "chain_root",
    "enabled",
    "figure_keys",
    "offer_view",
    "qualifying_figure",
    "reveal_text",
]
