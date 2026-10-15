"""Read-only views for remote frontends: status, today, progress, library (spec_mcp_frontend_c1 §4).

Every view reads through a read-only attach (``RemoteRuntime.read_repository``):
a write anywhere below it raises instead of happening, so "viewing changes
nothing" is structural, not a convention. In particular ``today`` never builds
or advances a plan, never starts a session and never records study time
(MCP-7, "preview is not participation"): it shows the plan the app already
built today, and says so when there is none yet.

No view shows a question's text: plan blocks carry topics, minutes and why;
practice happens in the app (chat practice is C2).

**Topic names and ids** in ``today`` and ``progress`` go through the read
model's one guard (``learner_context.TextGuard``, Q12): a topic the
learner-text pipeline generated (its title drafted from the learner's words)
shows a fixed label and an opaque keyed alias, as in ``learning_context``. A
plan block's computed "why" embeds the titles it was built with, so a block on
a generated topic, or with a why a model wrote, shows no why (the same
"held back" reason).
"""

from __future__ import annotations

import os
from collections import Counter
from datetime import UTC, datetime
from typing import Any

from learnloop.clock import Clock, SystemClock
from learnloop.db.migrate import applied_versions, discover_migrations
from learnloop.learner_context import HELD_BACK, TextGuard
from learnloop.remote.errors import NotFound

#: The serving routes ``status`` reports, in the order a learner meets them.
READINESS_TASKS = ("grading", "diagnosis", "source_rerank", "source_query_rewrite", "tutor_qa", "embedding")
#: Profile types whose readiness is a key in the environment (no network, no process).
_KEY_TYPES = {"openrouter": "OPENROUTER_API_KEY", "openai_embedding": "OPENROUTER_API_KEY",
              "openai_chat": "OPENAI_API_KEY", "decider": "OPENROUTER_API_KEY"}
PHASE = "C1a"
FRONTEND_NOTE = ("Read-only chat frontend: LearnLoop's state is read here; practice, grading and adding "
                 "material happen in the LearnLoop app for now.")


def _now(clock: Clock | None) -> datetime:
    return (clock or SystemClock()).now().astimezone(UTC)


def _alias_key(runtime: Any) -> bytes | None:
    reader = getattr(runtime, "alias_key", None)
    return reader() if callable(reader) else None


# -- status ------------------------------------------------------------------------


def ai_readiness(vault: Any) -> dict[str, Any]:
    """Per serving route: which profile it uses and whether it can run.

    Read from configuration and the environment only. A Codex or ChatGPT-plan
    route is reported ``not_checked``: checking it would start a local process,
    which a status read must not do."""

    from learnloop.ai.routing import provider_for_task

    config = vault.config
    routes: dict[str, Any] = {}
    for task in READINESS_TASKS:
        if task == "embedding" and not config.embedding.enabled:
            routes[task] = {"state": "off"}
            continue
        try:
            name = provider_for_task(config, task).provider_name
        except Exception:  # noqa: BLE001 - reported, not raised
            routes[task] = {"state": "not_configured"}
            continue
        profile = config.ai.providers.get(name) if name else None
        if not name or name == "manual":
            routes[task] = {"provider": name or None, "state": "manual"}
        elif profile is None:
            routes[task] = {"provider": name, "state": "not_configured"}
        else:
            kind = str(profile.type).lower()
            if kind in _KEY_TYPES:
                env = getattr(profile, "api_key_env", None) or _KEY_TYPES[kind]
                state = "ready" if os.environ.get(env) else "needs_key"
            else:
                state = "not_checked"
            routes[task] = {"provider": name, "type": kind, "state": state}
    grading = routes.get("grading", {}).get("state")
    return {
        "routes": routes,
        "grading": "ready" if grading == "ready" else ("unknown" if grading == "not_checked" else "unavailable"),
        "note": ("Readiness from configuration only; a Codex/ChatGPT-plan route is not probed from chat "
                 "(that would start a local process)."),
    }


def status(runtime: Any) -> dict[str, Any]:
    """The vault, its algorithm version, AI readiness and waiting work."""

    from learnloop.held_grades import held_for_review_attempts

    vault = runtime.vault()
    repository = runtime.read_repository()
    versions = applied_versions(runtime.sqlite_path)
    latest = max((migration.version for migration in discover_migrations()), default=0)
    pending: dict[str, Any] = {}
    with repository.connection() as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        if "post_attempt_jobs" in tables:
            pending["grading_or_diagnosis_jobs"] = int(connection.execute(
                "SELECT COUNT(*) FROM post_attempt_jobs WHERE state IN ('queued', 'leased')").fetchone()[0])
        recent = [row[0] for row in connection.execute(
            "SELECT id FROM practice_attempts ORDER BY created_at DESC, id DESC LIMIT 500")]
        pending["grades_held_for_review"] = len(held_for_review_attempts(connection, recent)) if recent else 0
        last = connection.execute("SELECT MAX(created_at) FROM practice_attempts").fetchone()[0]
    active_los = [lo for lo in vault.learning_objects.values() if lo.status == "active"]
    active_items = [item for item in vault.practice_items.values() if item.status == "active"]
    return {
        "vault": {
            "name": vault.root.name,
            "subjects": sorted(subject.metadata.title for subject in vault.subjects.values()),
            "topics": len(active_los),
            "practice_items": len(active_items),
            "goals_active": sum(1 for goal in vault.goals if goal.status == "active"),
            "last_answer_at": last,
        },
        "algorithm_version": vault.config.algorithms.algorithm_version,
        "database": {"schema_ok": latest in versions, "latest_migration": latest, "attach": "secondary (read side)"},
        "ai": ai_readiness(vault),
        "pending": pending,
        "frontend": {"surface": "chat_mcp", "phase": PHASE, "note": FRONTEND_NOTE},
    }


# -- today -------------------------------------------------------------------------


def today(runtime: Any, *, clock: Clock | None = None) -> dict[str, Any]:
    """Today's plan as the app built it: blocks, minutes and why. Read-only."""

    from learnloop.daily_plan.engine import PlanEnv, load_records, plan_active
    from learnloop.daily_plan.headline import today_headline
    from learnloop.daily_plan.view import plan_view

    vault = runtime.vault()
    repository = runtime.read_repository()
    env = PlanEnv(vault=vault, repository=repository, clock=clock)
    now = _now(clock)
    result: dict[str, Any] = {
        "local_date": env.today(),
        "read_only": True,
        "note": ("Viewing the plan starts nothing and records no study time. Start a session in the "
                 "LearnLoop app."),
    }
    result["due_now"] = _due_now(vault, repository, now)
    if not plan_active(vault):
        result.update(plan_enabled=False, plan=None,
                      plan_note="The daily plan is off for this vault; the app shows the open queue.")
        return result
    records = load_records(repository, local_date_value=env.today())
    if not records:
        result.update(plan_enabled=True, plan=None,
                      plan_note="Today's plan is built when you open LearnLoop or start a session; none yet today.")
    else:
        view = plan_view(env, records[-1], context=None, next_step=None,
                         streak=repository.session_day_streak(clock=clock))
        with repository.connection() as connection:
            guard = TextGuard(connection, vault, repository, alias_key=_alias_key(runtime))
            plan = _plan_projection(view["plan"], records[-1], guard)
        result.update(plan_enabled=True, plan=plan, day=view.get("day"), streak=view.get("streak"))
    try:
        gap = env.gap()
        result["since_last_study"] = {"days": gap.gap_days, "reentry": bool(gap.due)}
    except Exception:  # noqa: BLE001 - optional line
        result["since_last_study"] = None
    if bool(getattr(vault.config.plan, "headline", False)):
        try:
            headline = today_headline(vault, repository, now=now)
            headline.pop("learning_object_classes", None)
            result["headline"] = headline
        except Exception:  # noqa: BLE001 - optional line
            result["headline"] = None
    return result


def _plan_projection(plan: dict[str, Any], record: Any, guard: TextGuard) -> dict[str, Any]:
    """The stored plan without any question text: topics, minutes, why.

    Topics are named by the guard. The why is shown only when it was computed
    (a template, the titles and section it was built with) and none of the
    block's topics, displaced items included, is a generated one."""

    stored = {block.id: block for block in getattr(record, "blocks", None) or ()}
    blocks = []
    for block in plan.get("blocks") or []:
        items = block.get("items") or []
        planned = stored.get(block.get("id"))
        every_lo = [item.learning_object_id for item in (planned.items if planned is not None else ())]
        shown_los = [item.get("learning_object_id") for item in items if item.get("learning_object_id")]
        computed = (planned.chosen.get("why_kind") if planned is not None else block.get("why_kind")) == "computed"
        why = block.get("why") or None
        why_note = None
        if why and (planned is None or not computed or any(guard.generated(lo) for lo in [*every_lo, *shown_los])):
            why, why_note = None, HELD_BACK
        blocks.append({
            "ordinal": block.get("ordinal"), "lane": block.get("lane"), "action": block.get("action"),
            "status": block.get("status"), "minutes": block.get("est_minutes"), "why": why, "why_note": why_note,
            "topics": [guard.topic(lo) for lo in dict.fromkeys(shown_los)],
            "reading": (block.get("reading") or {}).get("section_title") if block.get("reading") else None,
            "items": len(items), "items_done": sum(1 for item in items if item.get("done_at")),
        })
    split = plan.get("split") or {}
    return {
        "kind": plan.get("kind"), "status": plan.get("status"), "minutes_budget": plan.get("minutes_budget"),
        "minutes_left": plan.get("minutes_left"), "split_line": split.get("line"), "blocks": blocks,
        "totals": plan.get("totals"),
    }


def _due_now(vault: Any, repository: Any, now: datetime) -> int:
    from learnloop.clock import parse_utc

    count = 0
    for item_id, state in repository.practice_item_states().items():
        item = vault.practice_items.get(item_id)
        if item is None or item.status != "active" or not state.active:
            continue
        due = parse_utc(state.due_at)
        if due is not None and due <= now:
            count += 1
    return count


# -- progress ----------------------------------------------------------------------


def progress(runtime: Any, *, goal_id: str | None = None, clock: Clock | None = None) -> dict[str, Any]:
    """Per goal and topic: demonstrated vs assumed, certification, retention risks."""

    vault = runtime.vault()
    repository = runtime.read_repository()
    now = _now(clock)
    if goal_id is not None and not any(goal.id == goal_id for goal in vault.goals):
        raise NotFound(f"no goal {goal_id!r} in this vault")
    with repository.connection() as connection:
        guard = TextGuard(connection, vault, repository, alias_key=_alias_key(runtime))
        return _progress(vault, repository, guard, goal_id=goal_id, clock=clock, now=now)


def _progress(vault: Any, repository: Any, guard: TextGuard, *, goal_id: str | None, clock: Clock | None,
              now: datetime) -> dict[str, Any]:
    from learnloop.daily_plan.headline import HEADLINE_CLASSES, classify_learning_objects
    from learnloop.goals.goal_projection import goal_report
    from learnloop.learner_context import retention_risks

    unknowns: list[str] = []
    try:
        classes = classify_learning_objects(vault, repository, now=now)
    except Exception:  # noqa: BLE001 - fail closed: nothing reads as demonstrated
        classes = {}
        unknowns.append("which topics are demonstrated could not be read: none is shown as demonstrated")
    goals = []
    scope_los: set[str] = set()
    for goal in vault.goals:
        if goal_id is not None and goal.id != goal_id:
            continue
        if goal_id is None and goal.status != "active":
            continue
        entry: dict[str, Any] = {"goal_id": goal.id, "title": goal.title, "status": goal.status,
                                 "due_at": goal.due_at, "target_recall": goal.target_recall}
        try:
            report = goal_report(vault, repository, goal, clock=clock)
        except Exception:  # noqa: BLE001 - this goal only
            entry["report"] = None
            unknowns.append(f"the report for goal {goal.title!r} could not be read")
            goals.append(entry)
            continue
        by_lo: dict[str, dict[str, Any]] = {}
        for facet in report.facets:
            row = by_lo.setdefault(facet.learning_object_id, {"facets": 0, "certified": 0, "on_track": 0,
                                                              "known_gap": 0, "recalls": []})
            row["facets"] += 1
            row["certified"] += int(bool(facet.certified))
            row["on_track"] += int(bool(facet.on_track))
            row["known_gap"] += int(facet.label == "known_gap")
            if facet.current_recall is not None:
                row["recalls"].append(float(facet.current_recall))
        topics = []
        scope_los.update(by_lo)
        for lo_id, row in sorted(by_lo.items()):
            recalls = row.pop("recalls")
            topics.append({
                "learning_object_id": guard.lo_ref(lo_id), "topic": guard.topic(lo_id),
                "standing": classes.get(lo_id, "untested") if classes else "unknown",
                **row, "recall_now": round(sum(recalls) / len(recalls), 3) if recalls else None,
            })
        entry["report"] = {
            "facets": report.total, "on_track": report.on_track_count, "certified": report.certified_count,
            "examined": report.examined_count, "at_risk": report.at_risk_count, "topics": topics,
        }
        goals.append(entry)
    counts = Counter(classes.values())
    scope = set(scope_los)
    risks = retention_risks(vault, repository, scope or {lo for lo, lo_obj in vault.learning_objects.items()
                                                         if lo_obj.status == "active"}, now=now,
                            topic=guard.topic, ref=guard.lo_ref)
    return {
        "as_of": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "standing_counts": {name: counts.get(name, 0) for name in HEADLINE_CLASSES},
        "assumed": sorted(str(guard.topic(lo)) for lo, value in classes.items() if value == "assumed"),
        "goals": goals,
        "retention_risks": risks,
        "unknowns": unknowns,
        "labels": {
            "demonstrated": "certified by unassisted, capability-matched answers",
            "assumed": "taken as known from placement or a claim; not demonstrated",
            "learning": "some direct evidence, not yet demonstrated",
            "untested": "no direct evidence yet",
            "recall_now": "a model estimate, not a test",
        },
    }


# -- library -----------------------------------------------------------------------


def library(runtime: Any, *, query: str | None = None, limit: int = 30) -> dict[str, Any]:
    """Sources and their state (titles searchable). Read-only."""

    from learnloop.content.pipeline.add_source import learner_title, source_kind_noun, source_status_line
    from learnloop.content.sources.exam_material import exam_material
    from learnloop.learner_context import protection_issues

    vault = runtime.vault()
    repository = runtime.read_repository()
    subject_by_source = {member.source_id: source_set.subject_id
                         for source_set in vault.source_sets for member in source_set.members}
    # Fail closed: with the source sets unreadable (or the snapshot unsettled)
    # every source reads as possibly exam material.
    try:
        exam = None if protection_issues(vault) else exam_material(vault, repository)
    except Exception:  # noqa: BLE001 - fail closed, as above
        exam = None
    words = [word for word in (query or "").lower().split() if word]
    cards: list[dict[str, Any]] = []
    total = 0
    for artifact in repository.all_source_artifacts():
        revisions = repository.source_revisions_for(artifact["id"])
        current = next((rev for rev in revisions if rev["id"] == artifact.get("current_revision_id")), None)
        if current is None and revisions:
            current = revisions[-1]
        title = learner_title(artifact, current)
        if words and not all(word in title.lower() for word in words):
            continue
        total += 1
        runs = repository.extraction_runs_for_revision(current["id"]) if current else []
        completed = [run for run in runs if run.get("status") == "completed"]
        latest = completed[-1] if completed else (runs[-1] if runs else None)
        counts = repository.document_ir_counts(latest["id"]) if latest else {"unit_count": 0, "block_count": 0}
        if latest is not None and latest.get("status") == "completed" and counts["block_count"] > 0:
            readiness = "ready"
        elif latest is not None:
            readiness = "processing"
        else:
            readiness = "needs_extraction"
        subject = vault.subjects.get(subject_by_source.get(artifact["id"]) or "")
        try:
            line = source_status_line(repository, vault, artifact["id"])
        except Exception:  # noqa: BLE001 - optional line
            line = None
        exam_whole = exam is None or (latest is not None and exam.covers(str(latest["id"])))
        cards.append({
            "source_id": artifact["id"], "title": title,
            "kind": source_kind_noun(repository, artifact["id"], artifact.get("acquisition_kind")),
            "readiness": readiness, "sections": counts["unit_count"],
            "subject": subject.metadata.title if subject is not None else None,
            "status_line": (line or {}).get("text") if isinstance(line, dict) else line,
            "in_reader": bool(artifact.get("reader_enabled", 1)),
            "exam_material": bool(exam_whole),
        })
    cards.sort(key=lambda card: card["title"].lower())
    return {
        "query": query or None, "matched": total, "sources": cards[: max(int(limit), 0)],
        "note": "Exam material is listed by title only; its text is never shown in chat.",
    }


__all__ = ["READINESS_TASKS", "ai_readiness", "library", "progress", "status", "today"]
