"""The RPCs a learner press sends, and the feature each one is (plan-first transport T1, landing review round 2).

Owner decision 2026-10-21: "Use OpenRouter instead" serves the request that
asked, or that feature for the session, and never background work. The
ruling on the round-2 verify: every RPC is not a press, and scrolling is not
pressing. Work queued in a request (an ingest batch, a sidecar job) may carry
the learner's grant only when that request is one of the presses below: the
dispatch (``server._handle``) enters ``plan_fallback.pressed(vault, feature)``
for them, and the token is narrowed to ``plan_fallback.FEATURE_TASKS[feature]``.

Everything the desktop sends by itself (reading progress on scroll, Today and
the daily plan, status reads, job polls, opening a book's margin notes or
reading path, the workbench opening or suggesting) is absent, so its queued
work runs on the plan. In-request (synchronous) calls of any RPC still use a
grant the learner gave (``plan_fallback.interactive()``), since they are that
request.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

Feature = str | Callable[[Any], "str | None"]


def _reading_path_retry(params: Any) -> str | None:
    # The reading path is read when the Guide opens (not a press); its
    # "Try again" (retry) is one.
    return "reading_path" if bool(getattr(params, "retry", False)) else None


PRESSED_RPCS: dict[str, Feature] = {
    # Add, Create study map, Build now / whole book, Append, Retry, Allow upload, Read again with OCR.
    "add_source": "build",
    "source_action": "build",
    "build_study_map": "build",
    "confirm_quick_add": "build",
    "start_import_batch": "build",
    "start_extraction_repair": "build",
    "start_inventory": "build",
    "resume_ingest_batch": "build",
    # The Reader's question for this section, the selection's check, the inquiry answer's check.
    "reader.author_section_question": "reader_check",
    "reader.active_question": "reader_check",
    "reader.reconnect_answer": "reader_check",
    # Import this exercise (Reader, textbook proposal, workbench retry) and the primed retry's import.
    "reader.import_exercise": "exercise_import",
    "import_source_exercise": "exercise_import",
    "workbench.retry_import": "exercise_import",
    "start_primed_retry": "exercise_import",
    "request_rung_variant": "rung_variant",
    "request_concept_animation": "animation",
    "promote_tutor_question": "question_promotion",
    # Create a goal (its population), starter practice, commissioning practice.
    "create_goal": "practice",
    "generate_starter_practice": "practice",
    "generate_commissioning_practice": "practice",
    # A hint, Check my work, a rung of help, Compare with the book's method, Show me an example.
    "practice.request_hint": "hints",
    "workbench.check": "hints",
    "workbench.request_help": "hints",
    "workbench.compare_methods": "hints",
    "workbench.show_example": "hints",
    # Ask the library, its notes, the tutor about it, Compare sources, a figure, Find exercises.
    "reader.library_ask": "library",
    "reader.library_ask_notes": "library",
    "reader.library_ask_tutor": "library",
    "reader.library_compare": "library",
    "reader.figure_request": "library",
    "reader.figure_revise": "library",
    "reader.find_exercises": "library",
    "reader.reading_path": _reading_path_retry,
}


def pressed_feature(method_name: str, params: Any, table: Mapping[str, Feature] | None = None) -> str | None:
    """The feature the learner pressed with this RPC, or ``None`` (not a press)."""

    feature = (PRESSED_RPCS if table is None else table).get(method_name)
    if feature is None or isinstance(feature, str):
        return feature
    return feature(params)


__all__ = ["PRESSED_RPCS", "pressed_feature"]
