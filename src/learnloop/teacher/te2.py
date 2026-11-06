"""Teacher TE2's switch, prompt and turn shape (spec_teacher_v1 rev 5 §9, §11.3, §11.5, §11.7, §11.8, §18.3).

One successor (``TEACHER_PROBES_VERSIONS``, mvp-0.51; built as mvp-0.50, one constant renumbered at landing) behind
``teacher.probes`` with the existing ``teacher.enabled``:

* **The turn grows** (§9): ``serve_probe {node, readings, p}`` (:mod:`.probes`) and ``propose_gap {ref, gap_kind,
  gap}`` (:mod:`.topics`), with the doctrine's versioned TE2 paragraph (``doctrine/te2/v1.md``) and the prompt
  version suffix :data:`PROMPT_SUFFIX`. A turn under the paragraph is a new doctrine version, so its forecasts are a
  new §12.2 forecaster family (:func:`doctrine_family`).
* **The transcript names the learner's turns** (``ref: t<seq>``) so a ``propose_gap`` can point at the words it
  files; a probe's steps enter the transcript as code's (``probe_requested``, ``probe_ready``, ``probe_result``, ...).
* **The brief** is ``lesson_brief_v2`` (:func:`brief_extras`): no vault probe headers (probes are generated), each
  node says whether a delayed check can be committed on it ("an unseen question exists" or "none yet", no item
  named), and ``where_you_left_off`` carries the last lesson's latest plan on these topics (§11.8).

Off, or below the tag: none of this runs, and the prompt, the schema, the brief, the transcript and the forecaster
family are TE1's (and TE2-log's) exactly.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from learnloop.algorithm_versions import TEACHER_PROBES_VERSIONS
from learnloop.teacher.contracts import (
    TeacherTurnEpisodesV1,
    TeacherTurnTE2EpisodesV1,
    TeacherTurnTE2V1,
    TeacherTurnTE2VisualsEpisodesV1,
    TeacherTurnTE2VisualsV1,
    TeacherTurnV1,
    TeacherTurnVisualsEpisodesV1,
    TeacherTurnVisualsV1,
)

#: The TE2 paragraph's version (recorded on every turn and forecast written under it).
TE2_VERSION = "teacher_te2_v1"
PROMPT_SUFFIX = "+te2-v1"
BRIEF_VERSION_V2 = "lesson_brief_v2"
#: The surface a lesson's probe is claimed on (FG1's burn ledger names it).
LESSON_SURFACE = "lesson"
#: What the brief says of a node's delayed check (§8.1 rev 5; no item named).
UNSEEN_EXISTS = "an unseen question exists"
UNSEEN_NONE = "none yet"
WHERE_YOU_LEFT_OFF = "where you left off"
_PARAGRAPH = Path(__file__).resolve().parent / "doctrine" / "te2" / "v1.md"


def on(vault: Any) -> bool:
    """TE2 serves: the vault at its successor or later, lessons on and ``teacher.probes`` on."""

    config = getattr(vault, "config", None)
    teacher = getattr(config, "teacher", None)
    version = getattr(getattr(config, "algorithms", None), "algorithm_version", None)
    return (version in TEACHER_PROBES_VERSIONS and teacher is not None and bool(getattr(teacher, "enabled", False))
            and bool(getattr(teacher, "probes", False)))


def lesson_te2(state: Any) -> bool:
    """The lesson was opened under TE2 (its brief is ``lesson_brief_v2``)."""

    return str((getattr(state, "brief", None) or {}).get("version") or "") == BRIEF_VERSION_V2


@lru_cache(maxsize=1)
def paragraph() -> str:
    return _PARAGRAPH.read_text(encoding="utf-8").strip() + "\n"


def instructions(text: str, te2: bool) -> str:
    return text if not te2 else f"{text}\n{paragraph()}"


def prompt_version(base: str, te2: bool) -> str:
    return f"{base}{PROMPT_SUFFIX}" if te2 else base


def doctrine_family(doctrine: str, te2: bool) -> str:
    """§12.2: a turn under the TE2 paragraph is a different forecaster (its own λ posterior)."""

    return f"{doctrine}+{TE2_VERSION}" if te2 else doctrine


_TE2_TURNS: dict[type[TeacherTurnV1], type[TeacherTurnV1]] = {
    TeacherTurnV1: TeacherTurnTE2V1,
    TeacherTurnEpisodesV1: TeacherTurnTE2EpisodesV1,
    TeacherTurnVisualsV1: TeacherTurnTE2VisualsV1,
    TeacherTurnVisualsEpisodesV1: TeacherTurnTE2VisualsEpisodesV1,
}


def turn_model(base: type[TeacherTurnV1], te2: bool) -> type[TeacherTurnV1]:
    """The turn's strict schema: ``base`` off; with ``serve_probe`` and ``propose_gap`` on."""

    return _TE2_TURNS[base] if te2 else base


def stored_turn(data: Mapping[str, Any] | None) -> TeacherTurnV1:
    """A stored accepted turn read back: TE1's widest shape when it validates (so a TE1 turn reads back exactly as
    before), else TE2's widest (a turn holding a TE2 request)."""

    try:
        return TeacherTurnVisualsEpisodesV1.model_validate(dict(data or {}))
    except ValidationError:
        return TeacherTurnTE2VisualsEpisodesV1.model_validate(dict(data or {}))


def learner_ref(entry: Mapping[str, Any]) -> str:
    """How the transcript names a learner's turn (``propose_gap``'s ``ref``)."""

    return f"t{int(entry['seq'])}"


# =============================================================================
# The brief's TE2 version (§8.1 rev 5, §11.8)
# =============================================================================


def delayed_check_words(vault: Any, repository: Any, learning_object_id: str, *, withheld: Any,
                        attempted: set[str]) -> str:
    """Whether a delayed check could be committed on the LO now: an unseen, unrevealed, unwithheld question exists
    (the delayed checks' own candidate rule, before this lesson shows anything), or none yet. No item is named."""

    from learnloop.delayed_checks import candidates, revealed_items

    found = candidates(vault, repository, learning_object_id, exclude=(), withheld=withheld, attempted=attempted,
                       revealed=revealed_items(repository, ""))
    return UNSEEN_EXISTS if found else UNSEEN_NONE


def where_you_left_off(vault: Any, repository: Any, learning_object_ids: Sequence[str], *, exclude: str | None,
                       notes_check: Any = None) -> dict[str, Any] | None:
    """The newest earlier lesson on these LOs with a stored plan: its latest plan version, labelled "where you left
    off" (§11.8). Shown only while that lesson's recap may be (the plan's statements were its displayed text:
    :func:`learnloop.teacher.brief.recap_admissible`); None otherwise."""

    from learnloop.db.stores import lessons as store
    from learnloop.teacher.brief import recap_admissible

    with repository.connection() as connection:
        for row in store.lessons_on(connection, learning_object_ids, closed_only=False, exclude=exclude):
            plans = store.plans(connection, str(row["id"]))
            if not plans:
                continue
            latest = plans[-1]
            if not recap_admissible(vault, repository, str(row["id"]), notes_check=notes_check):
                return None
            outline = [{key: node.get(key) for key in ("id", "statement", "lo_id", "premises") if key in node}
                       for node in latest.get("outline") or []]
            return {"label": WHERE_YOU_LEFT_OFF, "lesson": f"l:{row['id']}", "plan_version": latest.get("version"),
                    "closed": row.get("closed_at") is not None, "outline": outline}
    return None


__all__ = [
    "BRIEF_VERSION_V2",
    "LESSON_SURFACE",
    "PROMPT_SUFFIX",
    "TE2_VERSION",
    "UNSEEN_EXISTS",
    "UNSEEN_NONE",
    "WHERE_YOU_LEFT_OFF",
    "delayed_check_words",
    "doctrine_family",
    "instructions",
    "learner_ref",
    "lesson_te2",
    "on",
    "paragraph",
    "prompt_version",
    "stored_turn",
    "turn_model",
    "where_you_left_off",
]
