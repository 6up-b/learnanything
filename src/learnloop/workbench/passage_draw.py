"""Reader workbench RW2c: a logged choice where it costs nothing (spec_reader_workbench_v1 §5.10, G39).

When bridging, or a worked-example search, finds two or more verified
passages that all passed the judge, one is shown by a logged draw and the
others stay one click away ("another passage"). Every option passed the same
judge, so no learner gets worse help on purpose: the cue holdout's pattern
(D10), not a hint-quality experiment (§17 keeps those unplanned).

* **The options**: the passages the judge kept, in its order, at most
  :data:`MAX_OPTIONS`; for a worked example, only those of the best verdict
  class (``follows_learner_route`` before ``worked_example``), so a passage
  that takes the learner's route is never displaced by one that does not.
* **The draw**: uniform over the options, from a seeded ``random.Random``
  (the seed is logged, so the draw reproduces); the propensity is the
  probability the shown option was drawn with (``1 / n``).
* **What is logged** on the bridge or example row (the existing
  ``help_assists`` columns): ``options_json`` (the options, by passage id and
  label), ``probabilities_json``, ``drawn_option_json``, ``propensity``,
  ``seed`` and ``policy_version``. The sources spec's S5 may copy the
  propensity and seed into its reserved fields (§18).
* **"another passage"**: the next option after the one on screen, with no
  search and no call, recorded as its own row with ``chooser =
  'learner_pick'`` and no propensity (a pick, not a draw).

Help, never evidence: nothing here reads or writes an attempt or a reveal.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import random
import time
from typing import Any

POLICY_VERSION = "passage-draw-v1"
#: At most this many passages are drawn between (the rest of the judge's
#: picks are not shown; a display bound).
MAX_OPTIONS = 3
#: The worked example's verdicts, best first (the sources spec's §9.2).
EXAMPLE_VERDICTS = ("follows_learner_route", "worked_example")


def new_seed() -> str:
    """A fresh seed for one draw (logged; :func:`draw` reproduces from it)."""

    return hashlib.sha256(f"passage:{time.time_ns()}:{random.random()}".encode()).hexdigest()[:16]


def _rng(seed: str) -> random.Random:
    return random.Random(int(hashlib.sha256(f"passage-draw:{seed}".encode("utf-8")).hexdigest()[:16], 16))


def option_id(passage: Mapping[str, Any]) -> str:
    return f"{passage.get('extraction_id') or ''}:{passage.get('span_id') or ''}"


def option_record(passage: Mapping[str, Any]) -> dict[str, Any]:
    """What a row keeps of an option: its identity and label, never its text."""

    record = {"option_id": option_id(passage), "span_id": passage.get("span_id"),
              "extraction_id": passage.get("extraction_id"),
              "label": str(passage.get("label") or passage.get("source_title") or "a passage")[:120]}
    if passage.get("verdict"):
        record["verdict"] = str(passage["verdict"])
    if passage.get("role"):
        record["role"] = str(passage["role"])
    return record


def best_class(passages: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """The passages of the best verdict present (worked examples: the route
    first), in the judge's order; passages without a verdict are one class."""

    verdicts = [str(passage.get("verdict") or "") for passage in passages]
    for verdict in EXAMPLE_VERDICTS:
        if verdict in verdicts:
            return [passage for passage in passages if str(passage.get("verdict") or "") == verdict]
    return list(passages)


@dataclass(frozen=True)
class Draw:
    index: int
    propensity: float
    probabilities: tuple[float, ...]
    seed: str
    options: tuple[dict[str, Any], ...]

    @property
    def drawn(self) -> dict[str, Any]:
        return self.options[self.index]

    def columns(self) -> dict[str, Any]:
        """The ``help_assists`` columns that log the draw."""

        return {
            "options_json": json.dumps(list(self.options), sort_keys=True),
            "probabilities_json": json.dumps({option["option_id"]: p for option, p in zip(self.options,
                                                                                        self.probabilities)},
                                             sort_keys=True),
            "drawn_option_json": json.dumps(self.drawn, sort_keys=True),
            "propensity": self.propensity,
            "seed": self.seed,
            "policy_version": POLICY_VERSION,
        }


def draw(passages: Sequence[Mapping[str, Any]], *, seed: str) -> Draw | None:
    """One uniform draw over the options, or None when fewer than two (then
    the first passage is shown as before, with nothing logged)."""

    options = tuple(option_record(passage) for passage in list(passages)[:MAX_OPTIONS])
    if len(options) < 2:
        return None
    probabilities = tuple(1.0 / len(options) for _ in options)
    index = int(_rng(seed).random() * len(options))
    index = min(index, len(options) - 1)
    return Draw(index=index, propensity=probabilities[index], probabilities=probabilities, seed=seed,
                options=options)


def options_of(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    try:
        value = json.loads(row.get("options_json") or "[]")
    except (TypeError, ValueError):
        return []
    return [entry for entry in value if isinstance(entry, dict) and entry.get("option_id")] \
        if isinstance(value, list) else []


def next_option(options: Sequence[Mapping[str, Any]], current_id: str | None) -> dict[str, Any] | None:
    """The option after ``current_id``, wrapping round; None with fewer than two."""

    if len(options) < 2:
        return None
    ids = [str(option["option_id"]) for option in options]
    at = ids.index(current_id) if current_id in ids else -1
    return dict(options[(at + 1) % len(options)])


def _placement(row: Mapping[str, Any]) -> dict[str, Any]:
    try:
        value = json.loads(row.get("placement_json") or "{}")
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def alternatives_view(row: Mapping[str, Any]) -> dict[str, Any]:
    """"another passage" on a shown bridge or example: present only when its
    row logged a draw (or is a pick among one), so with the draw switched off
    a view is exactly what it was."""

    options = options_of(row)
    if len(options) < 2:
        return {}
    placement = _placement(row)
    current = f"{placement.get('extraction_id') or ''}:{placement.get('span_id') or ''}"
    return {"alternatives": len(options) - 1, "option_id": current,
            "draw_assist_id": placement.get("draw_assist_id") or row["id"]}


class NoAlternative(Exception):
    """The row has no other passage to show."""


def another_passage(repository: Any, *, workbench_session_id: str, assist_id: str,
                    line_for: Any, shown_at: str) -> dict[str, Any]:
    """Show the next option of a shown bridge or example (no search, no call):
    a new row, ``chooser = 'learner_pick'``, no propensity, counted by nothing.
    ``line_for(option, placement)`` writes its line. Returns the new row."""

    from learnloop.db.stores import help_assists as store
    from learnloop.ids import new_ulid

    with repository.atomic():
        connection = repository.connection()
        row = store.assist(connection, assist_id)
        if row is None or row.get("workbench_session_id") != workbench_session_id \
                or row.get("assist_kind") not in store.PASSAGE_KINDS or not row.get("shown"):
            raise NoAlternative("not_a_shown_passage")
        options = options_of(row)
        placement = _placement(row)
        current = f"{placement.get('extraction_id') or ''}:{placement.get('span_id') or ''}"
        option = next_option(options, current)
        if option is None:
            raise NoAlternative("no_alternatives")
        picked = {key: placement[key] for key in ("hint_assist_id", "trigger", "verdict", "role", "step_number")
                  if key in placement}
        picked.update({"status": "picked", "draw_assist_id": placement.get("draw_assist_id") or row["id"],
                       "span_id": option.get("span_id"), "extraction_id": option.get("extraction_id"),
                       "label": option.get("label")})
        if option.get("verdict"):
            picked["verdict"] = option["verdict"]
        new = {
            "id": "ha_" + new_ulid(), "surface": row["surface"], "assist_kind": row["assist_kind"],
            "practice_item_id": row.get("practice_item_id"), "practice_item_hash": row.get("practice_item_hash"),
            "practice_session_id": row.get("practice_session_id"), "workbench_session_id": workbench_session_id,
            "submission_id": row.get("submission_id"), "about_step_id": row.get("about_step_id"),
            "body_md": line_for(option, picked), "placement_json": json.dumps(picked, sort_keys=True),
            "chooser": "learner_pick", "options_json": row.get("options_json"),
            "drawn_option_json": json.dumps(option, sort_keys=True), "policy_version": POLICY_VERSION,
            "shown": 1, "counted_by": None, "cited_span_ids_json": json.dumps([str(option.get("span_id"))]),
            "requested_at": shown_at, "shown_at": shown_at,
        }
        store.insert_assist(connection, new)
    return new


__all__ = ["Draw", "EXAMPLE_VERDICTS", "MAX_OPTIONS", "NoAlternative", "POLICY_VERSION", "alternatives_view",
           "another_passage", "best_class", "draw", "new_seed", "next_option", "option_id", "option_record",
           "options_of"]
