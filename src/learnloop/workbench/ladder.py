"""Reader workbench RW2b: the help ladder's Reader side (spec_reader_workbench_v1 §5.2, §5.5, §5.6, G60, G62).

The Reader defines no hint writer, chooser or map builder (G64): every hint,
its kind and the suggested rung come from :mod:`learnloop.hints` (the
service's workbench surface, :mod:`learnloop.hints.workbench`). This module
assembles what the service is given and presents what it returns:

* :func:`hint_context`: the live steps (numbered), the last shown check's
  verdicts and step graph (a verdict on a step edited since is dropped: it no
  longer describes that step), the about-step (a "that's not where I'm stuck"
  pick, else the answered hint's step, else the first questionable step, else
  the focused step, else the last step), the steps that stand and
  ``continue_from`` (rule 2), the check's error-kind guess and rival
  readings, the header's help style;
* :func:`fallback_level`: the Reader's progression when no judgment is
  available (rung 1, then one above the last rung offered or taken on that
  step, up to 5; §5.5, G62);
* :func:`hint_views`: the problem's shown hints as the workbench restores
  them under their steps (resume keeps the assistance history, §5.1);
* :func:`queue_stuck_texts`: a stuck step's newest text to learner-text gaps
  (``workbench_text``, role ``stuck``) when Help, Check, Leave or Submit sends
  it (in-session updates, §5.2).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import closing
import json
from typing import Any

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import help_assists as assists_store
from learnloop.db.stores import workbench as store
from learnloop.hints import workbench as hint_workbench
from learnloop.reader import workbench as WB

#: The UX's wording for an unavailable service (UX §4.0 "capped", §5.6).
TAILORED_UNAVAILABLE = "Tailored hints are unavailable right now ({reason}). The item's own hints are still here ▸"
NO_AUTHORED_LEFT = "Tailored hints are unavailable right now ({reason}), and the item has no hint of its own left."
#: The service's reasons a hint could not be written (H2a's writer refusals).
WRITER_DOWN_REASONS = frozenset({"codex_refused", "capped", "unpriced", "unrouted", "models_off", "writer_failed",
                                 "unavailable"})
#: What a discriminating answer settled (the service's own lines, H2a).
SETTLED_LINE = "That fits one reading more than the other; the next hint uses it."
UNSETTLED_LINE = "Both readings still stand; the next hint uses your answer."


def help_enabled(vault: Any) -> bool:
    section = getattr(vault.config, "workbench", None)
    return WB.workbench_enabled(vault) and bool(getattr(section, "help_enabled", True))


def live_workbench_steps(repository: Repository, session_id: str) -> list[hint_workbench.WorkbenchStep]:
    with repository.connection() as connection:
        rows = store.steps_for_session(connection, session_id)
    steps = []
    for number, step in enumerate(WB.live_steps(rows), start=1):
        steps.append(hint_workbench.WorkbenchStep(chain_id=str(step["chain_id"]), step_id=str(step["step_id"]),
                                                  number=number, kind=str(step["kind"]),
                                                  body_md=str(step["body_md"] or "")))
    return steps


def _rows(repository: Repository, session_id: str) -> list[dict[str, Any]]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return assists_store.workbench_rows(connection, session_id)


def last_shown_check(rows: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    shown = [row for row in rows if row["assist_kind"] == "check" and row.get("shown")]
    return shown[-1] if shown else None


def _verdicts(check: Mapping[str, Any] | None, steps: Sequence[hint_workbench.WorkbenchStep], *,
              symbolic_enabled: bool = False) -> list[hint_workbench.StepVerdict]:
    """The check's verdicts that still describe the steps (same text). Fix
    round 10: with symbolic checks off a stored symbolic verdict is the
    model's reading, so it is never told to the writer or copied into a new
    hint row as checked."""

    if check is None:
        return []
    from learnloop.symbolic_view import verdict_records

    hashes = {step.chain_id: step.content_hash for step in steps}
    verdicts = [hint_workbench.verdict_from_record(record)
                for record in verdict_records(check, enabled=symbolic_enabled)]
    return [verdict for verdict in verdicts if hashes.get(verdict.chain_id) == verdict.content_hash]


def hint_context(
    vault: Any,
    repository: Repository,
    session: Mapping[str, Any],
    *,
    focused_step: str | None = None,
    feedback_step: str | None = None,
    answered: Mapping[str, Any] | None = None,
    offered_level: int | None = None,
    suggestion_id: str | None = None,
    steps: Sequence[hint_workbench.WorkbenchStep] | None = None,
    symbolic_now: Any = None,
) -> hint_workbench.WorkbenchHintContext:
    """What the hint service is given for one workbench request (module docstring)."""

    section = vault.config.workbench
    live = list(steps) if steps is not None else live_workbench_steps(repository, str(session["id"]))
    rows = _rows(repository, str(session["id"]))
    check = last_shown_check(rows)
    verdicts = _verdicts(check, live, symbolic_enabled=hint_workbench.symbolic_enabled(vault))
    chains = {step.chain_id for step in live}
    first = next((verdict.chain_id for verdict in verdicts if verdict.verdict == "questionable"), None)
    alternatives: tuple[tuple[str, str], ...] = ()
    guess = None
    if check is not None and first is not None and check.get("first_questionable_step_id") == first:
        guess = check.get("error_kind_guess")
        try:
            alternatives = tuple((str(entry.get("kind") or ""), str(entry.get("statement") or ""))
                                 for entry in json.loads(check.get("alternatives_json") or "[]"))
        except (TypeError, ValueError):
            alternatives = ()
    about = None
    for candidate in (feedback_step, (answered or {}).get("about_step_id"), first, focused_step):
        if candidate and candidate in chains:
            about = str(candidate)
            break
    if about is None and live:
        about = next((step.chain_id for step in reversed(live) if step.kind == "step"), live[-1].chain_id)
    standing = hint_workbench.standing_steps(live, verdicts)
    continue_from = hint_workbench.checkpoint_for(live, standing, about)
    return hint_workbench.WorkbenchHintContext(
        workbench_session_id=str(session["id"]), steps=tuple(live), _raw_verdicts=tuple(verdicts),
        check_assist_id=str(check["id"]) if check is not None else None, first_questionable=first,
        error_kind_guess=str(guess) if guess and section.error_kind_enabled else None,
        error_kind_alternatives=alternatives if section.error_kind_enabled else (),
        about=about, continue_from=continue_from, standing=tuple(standing), offered_level=offered_level,
        suggestion_id=suggestion_id, help_style=session.get("help_style"), feedback_step=feedback_step,
        discriminate_enabled=bool(section.discriminate_enabled), error_kind_enabled=bool(section.error_kind_enabled),
        # Fix round 12: the switch read again at every writer call and row
        # serialization (the caller's live reader; else this vault's).
        symbolic_now=symbolic_now if symbolic_now is not None else (lambda: hint_workbench.symbolic_enabled(vault)))


def fallback_level(repository: Repository, session_id: str, about_step: str | None) -> int:
    """The Reader's progression (§5.5, G62): rung 1 the first time on a step,
    then one rung above the last rung offered or taken there, up to 5."""

    entries: list[tuple[str, int]] = []
    for row in _rows(repository, session_id):
        if row["assist_kind"] != "hint" or row.get("about_step_id") != about_step:
            continue
        for level in (row.get("offered_level"), row.get("level")):
            if level:
                entries.append((str(row.get("requested_at") or ""), int(level)))
    for event in offered_events(repository, session_id):
        if event.get("about_step_id") == about_step and event.get("offered_level"):
            entries.append((str(event.get("created_at") or ""), int(event["offered_level"])))
    if not entries:
        return 1
    latest = max(at for at, _level in entries)
    return min(5, max(level for at, level in entries if at == latest) + 1)


def offered_events(repository: Repository, session_id: str) -> list[dict[str, Any]]:
    """The ``workbench_help_offered`` events of a problem, oldest first."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = connection.execute(
            "SELECT payload_json, created_at FROM interaction_events WHERE kind = 'reader_action_invoked' "
            "AND subject_type = ? AND subject_id = ? ORDER BY created_at, rowid",
            (WB.SUBJECT_TYPE, session_id)).fetchall()
    found = []
    for payload_json, created_at in rows:
        try:
            payload = json.loads(payload_json or "{}")
        except (TypeError, ValueError):
            continue
        if payload.get("event") == "workbench_help_offered":
            found.append({**payload, "created_at": created_at})
    return found


def hint_views(vault: Any, repository: Repository, session_id: str) -> list[dict[str, Any]]:
    """The problem's shown hints, discriminating answers and bridges, in
    order, as the workbench restores them under their steps (resume keeps
    the assistance history)."""

    from learnloop.hints import kinds as hint_kinds

    rows = _rows(repository, session_id)
    answers = {json.loads(row.get("placement_json") or "{}").get("question_assist_id"): row
               for row in rows if row["assist_kind"] == "discriminate_answer"}
    bridges = {json.loads(row.get("placement_json") or "{}").get("hint_assist_id"): row
               for row in rows if row["assist_kind"] == "bridge" and row.get("shown")}
    snapshot_numbers: dict[str, int] = {}
    views = []
    for row in rows:
        if row["assist_kind"] != "hint" or not row.get("shown"):
            continue
        try:
            for entry in json.loads(row.get("step_snapshot_json") or "[]"):
                snapshot_numbers[str(entry.get("chain_id"))] = int(entry.get("number") or 0)
        except (TypeError, ValueError):
            pass
        kind = str(row.get("hint_kind") or "next_step")
        level = int(row.get("level") or 3)
        item = vault.practice_items.get(str(row.get("practice_item_id") or ""))
        text = row.get("body_md") or ""
        if not text and row.get("authored_index") is not None and item is not None \
                and 0 <= int(row["authored_index"]) < len(item.hints):
            text = item.hints[int(row["authored_index"])]
        labels = hint_kinds.labels_for(kind, level, origin=hint_kinds.FROM_THE_ITEM if kind == "authored"
                                       else hint_kinds.AI_WRITTEN)
        about = row.get("about_step_id")
        continue_from = row.get("continue_from_step_id")
        answer = answers.get(row["id"])
        bridge = bridges.get(row["id"])
        views.append({
            "assist_id": row["id"], "kind": kind, "level": level, "hint_md": text, "labels": labels,
            "about_step_id": about, "continue_from_step_id": continue_from,
            "step_line": _step_line(snapshot_numbers.get(str(about)) if about else None,
                                    snapshot_numbers.get(str(continue_from)) if continue_from else None),
            "replies": (["smaller_step"] if kind == "waypoint" else []) + ["doesnt_connect", "book_way"],
            "discriminating_answer": {"answer_md": answer.get("feedback_text"),
                                      "message": SETTLED_LINE if json.loads(answer.get("placement_json") or "{}")
                                      .get("settled") else UNSETTLED_LINE}
            if answer is not None else None,
            "bridge": bridge_view(bridge) if bridge is not None else None,
            "claims": row_claims(row, symbolic_enabled=hint_workbench.symbolic_enabled(vault)),
            "symbolic_enabled": hint_workbench.symbolic_enabled(vault),
        })
    return views


def row_claims(row: Mapping[str, Any], *, symbolic_enabled: bool = False) -> list[dict[str, Any]]:
    """A hint row's own claims as checked (Reader §5.3; fix round 1, F14);
    with symbolic checks off a stored checked claim is the model's reading
    (fix round 10)."""

    from learnloop.symbolic_view import stored_claims

    return stored_claims(row, enabled=symbolic_enabled)


def served_claims(repository: Repository, assist_id: str | None, *,
                  symbolic_enabled: bool = False) -> list[dict[str, Any]]:
    """The claims of the hint ``assist_id`` (``[]`` when it has none)."""

    if not assist_id:
        return []
    from contextlib import closing

    from learnloop.db.connection import connect
    from learnloop.db.stores.help_assists import assist

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = assist(connection, assist_id)
    return row_claims(row, symbolic_enabled=symbolic_enabled) if row is not None else []


def _step_line(about: int | None, continue_from: int | None) -> str:
    parts = [f"on your step {about}"] if about else []
    parts.append(f"continues from step {continue_from}" if continue_from else "starts from the givens")
    return " · ".join(parts)


def bridge_view(row: Mapping[str, Any]) -> dict[str, Any]:
    placement = json.loads(row.get("placement_json") or "{}")
    return {"assist_id": row["id"], "line": row.get("body_md") or "", "span_id": placement.get("span_id"),
            "extraction_id": placement.get("extraction_id"), "label": placement.get("label")}


def unavailable_message(reason: str | None, *, authored_left: bool) -> str:
    plain = {
        "codex_refused": "hints aren't written on Codex",
        "capped": "today's hint budget is used",
        "unpriced": "the hint route has no price set",
        "unrouted": "no hint model is set up",
        "models_off": "hint models are off",
        "writer_failed": "the hint model didn't answer",
    }.get(str(reason), str(reason or "unavailable").replace("_", " "))
    return (TAILORED_UNAVAILABLE if authored_left else NO_AUTHORED_LEFT).format(reason=plain)


# ---------------------------------------------------------------------------
# Learner text (``workbench_text``): in-session updates
# ---------------------------------------------------------------------------

def stuck_texts(repository: Repository, session_id: str) -> list[str]:
    """The newest version of every non-empty stuck step (its row id)."""

    with repository.connection() as connection:
        rows = store.steps_for_session(connection, session_id)
    return [str(step["step_id"]) for step in WB.live_steps(rows)
            if step["kind"] == "stuck" and str(step["body_md"] or "").strip()]


def queue_stuck_texts(vault: Any, repository: Repository, session_id: str) -> list[str]:
    """Queue each stuck step's newest text (``workbench_text``, role
    ``stuck``); idempotent per version, so a step queued once and unchanged
    is not queued again. Returns the queued job ids."""

    from learnloop.diagnosis.text_gaps.jobs import enqueue_workbench_text

    queued = []
    for step_id in stuck_texts(repository, session_id):
        job = enqueue_workbench_text(vault, repository, source_id=step_id)
        if job:
            queued.append(job)
    return queued


__all__ = [
    "NO_AUTHORED_LEFT",
    "SETTLED_LINE",
    "UNSETTLED_LINE",
    "WRITER_DOWN_REASONS",
    "TAILORED_UNAVAILABLE",
    "bridge_view",
    "row_claims",
    "served_claims",
    "fallback_level",
    "help_enabled",
    "hint_context",
    "hint_views",
    "last_shown_check",
    "live_workbench_steps",
    "offered_events",
    "queue_stuck_texts",
    "stuck_texts",
    "unavailable_message",
]
