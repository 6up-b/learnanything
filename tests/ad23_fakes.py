"""Builders for adaptive difficulty AD2+AD3's tests (no network, no model call).

``ad23_vault`` is AD1's daily-plan vault at the successor's tag (``mvp-0.30``)
with the outside forecasters and the feature audit off (no background job),
items carrying task features, and extra LOs when asked. ``answer`` records a
graded attempt through the real pipeline (a manual self-grade), bound to its
plan presentation when given. ``fake_proposal`` is a structured client
answering the relatedness proposal.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import timedelta
from pathlib import Path
from typing import Any

import yaml

from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.ai.execution import report_call_usage
from learnloop.ai.isolation import TOOL_FREE
from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, STRUCTURED_COMPLETION
from learnloop.vault.loader import load_vault

from tests.ad_fakes import ITEMS, LO, TASK_FEATURES, ad_plan_vault, plan_env, rows, stamp_task_features
from tests.daily_plan_fakes import MovableClock, iso, make_env, scheduled, seed_due
from tests.helpers import append_config_toml, create_daily_plan_vault

SUCCESSOR = "mvp-0.30"
QUIET = """
[adaptive_difficulty]
outside_forecasters = []
feature_audit = false
"""
EASY = {"complexity": 0, "transfer": "same_context", "scaffolding": "cue", "span": "atomic",
        "response": "short_constructed", "tools": ["closed_book"]}
#: ``learned_coupling`` is off by default (owner decision 2026-10-19: on only after the owner adopts
#: a coupling version); the tests of the proposal and the coupled subject view turn it on.
COUPLED = "learned_coupling = true\n"
HARD = {"complexity": 2, "transfer": "near", "scaffolding": "none", "span": "single_step",
        "response": "long_constructed", "tools": ["closed_book"]}


def ad23_vault(tmp_path: Path, *, config: str = "", version: str = SUCCESSOR, items: Sequence[str] = ITEMS,
               features: Mapping[str, Mapping[str, Any]] | None = None,
               learning_objects: Mapping[str, Sequence[str]] | None = None, ad: str = "") -> Any:
    """The plan vault at ``version`` with AD's background work off and every item's features stamped.

    ``ad``: more ``[adaptive_difficulty]`` keys; ``config``: TOML appended after that section
    (keys before any header still land in ``[adaptive_difficulty]``)."""

    los = {LO: [(item, 2.0) for item in items]}
    for lo, lo_items in (learning_objects or {}).items():
        los[lo] = [(item, 2.0) for item in lo_items]
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects=los, version=version)
    for lo, lo_items in los.items():
        for item, _minutes in lo_items:
            stamp_task_features(paths, item, (features or {}).get(item, TASK_FEATURES), difficulty_source="llm_estimate")
    append_config_toml(paths.root, QUIET + (ad or "") + (config or ""))
    return paths


def ad_epoch(paths: Any) -> str | None:
    """The vault's protection epoch now (with the test's held-out material in force): what an AD
    artefact AD wrote now would be stamped with (the AD23 redesign, round 2). A test seeding AD's own
    rows directly stamps them with it."""

    from learnloop.adaptive_difficulty.material_view import detached_view
    from learnloop.db.repositories import Repository

    return detached_view(load_vault(paths.root), Repository(paths.sqlite_path)).epoch


#: The protection epoch a test seeds an AD row with before its vault's protection is final: rewritten
#: to the vault's own epoch by :func:`restamp` once it is.
SEEDED = "__seeded_epoch__"


def restamp(paths: Any, epoch: str | None = None) -> str | None:
    """Rewrite every seeded stamp (:data:`SEEDED`) in AD's column-stamped tables to ``epoch`` (default:
    the vault's epoch now). Test-only: the tables' append-only triggers are dropped around the
    update and recreated as they were."""

    import sqlite3
    from contextlib import closing

    from learnloop.adaptive_difficulty.protected_tables import EPOCH

    epoch = epoch if epoch is not None else ad_epoch(paths)
    tables = [table for table, rule in EPOCH.items() if rule.startswith("column:")]
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        for table in tables:
            triggers = connection.execute(
                "SELECT name, sql FROM sqlite_master WHERE type = 'trigger' AND tbl_name = ? AND name LIKE '%no_update'",
                (table,)).fetchall()
            for name, _sql in triggers:
                connection.execute(f"DROP TRIGGER {name}")
            connection.execute(f"UPDATE {table} SET protection_epoch = ? WHERE protection_epoch = ?", (epoch, SEEDED))
            for _name, sql in triggers:
                connection.execute(sql)
        connection.commit()
    return epoch


def env_for(paths: Any, *, clock: MovableClock | None = None, items: Sequence[str] = ITEMS, session: str = "s1",
            lo: str = LO, policy: Any = None) -> tuple[Any, MovableClock]:
    clock = clock or MovableClock()
    item_los = {}
    vault = load_vault(paths.root)
    for item_id in items:
        item_los[item_id] = vault.practice_items[item_id].learning_object_id
    kwargs = {"clock": clock, "session_id": session}
    if policy is not None:
        kwargs["policy"] = policy
    env = make_env(paths.root, [scheduled(item, item_los[item], forgetting_risk=0.6) for item in items], **kwargs)
    for item in items:
        seed_due(env.repository, item, due=clock.now() - timedelta(days=11), last=None)
    with env.repository.connection() as connection:
        connection.execute("INSERT OR IGNORE INTO sessions(id, started_at, available_minutes) VALUES (?, ?, 30)",
                           (session, iso(clock.now())))
        connection.commit()
    return env, clock


def intent_gated(env: Any) -> Any:
    """``env`` with its scheduled supplier gated by DL2's intent as the scheduler's due queue gates
    every item (``admission_reason``'s intent gate): the fakes' supplier stands in for that queue,
    so without this an item intent withholds would reach the plan's pool."""

    import dataclasses

    from learnloop.scheduling.intent.serving import intent_serving

    supplier = env.eligible

    def eligible(minutes: Any) -> list[Any]:
        serving = intent_serving(env.vault, env.repository, now=env.now())
        return [item for item in supplier(minutes)
                if serving is None or serving.withhold_reason(item.practice_item_id) is None]

    return dataclasses.replace(env, eligible=eligible)


def commit(paths: Any, choices: Sequence[tuple[str, str, str]], *, clock: Any = None) -> None:
    """Apply DL2 intent choices ``(scope kind, scope id, choice)`` to the vault (its commitments)."""

    from learnloop.db.repositories import Repository
    from learnloop.intent.control import Scope, apply_choice

    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    for kind, ref, choice in choices:
        apply_choice(vault, repository, Scope(kind, ref), choice, clock=clock or MovableClock())


def cold_followup(paths: Any, item_id: str, *, clock: Any = None, context_json: str | None = None) -> str:
    """Real incumbent state: an open cold retry holding ``item_id`` (``followup_tasks``). ``context_json``
    replaces the task's stored context verbatim (a malformed one is the boundary probe's)."""

    from learnloop.db.repositories import Repository

    repository = Repository(paths.sqlite_path)
    task = repository.create_followup_task(kind="cold_retry", case_kind="diagnosis", case_ref=f"case-{item_id}",
                                           not_before="2026-01-01T00:00:00Z", selected_item_id=item_id,
                                           clock=clock)
    if context_json is not None:
        import sqlite3
        from contextlib import closing as _closing

        with _closing(sqlite3.connect(paths.sqlite_path)) as connection:
            connection.execute("UPDATE followup_tasks SET context_json = ? WHERE id = ?", (context_json, task["id"]))
            connection.commit()
    return str(task["id"])


def close_followups(paths: Any) -> None:
    """The open follow-ups served their items (``consumed``)."""

    import sqlite3
    from contextlib import closing as _closing

    with _closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute("UPDATE followup_tasks SET status = 'consumed' WHERE status IN ('pending', 'served')")
        connection.commit()


def pending_variant(paths: Any, item_id: str, *, lo: str = LO) -> None:
    """Real incumbent state: a learner's easier-variant request for ``item_id`` still being authored
    (a live ``rung_variant`` job), which holds the item (the routine gate's ``rung_variant_hold``)."""

    import sqlite3
    from contextlib import closing as _closing

    at = "2026-10-12T09:00:00Z"
    with _closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute("INSERT INTO ingest_batches(id, workflow_type, status, created_at) VALUES (?, 'rung_variant', "
                           "'running', ?)", (f"b_{item_id}", at))
        connection.execute("INSERT INTO ingest_jobs(id, batch_id, ordinal, job_type, status, created_at) VALUES "
                           "(?, ?, 0, 'rung_variant', 'running', ?)", (f"j_{item_id}", f"b_{item_id}", at))
        connection.execute(
            "INSERT INTO rung_variant_requests(id, source_practice_item_id, learning_object_id, direction, "
            "source_waypoint_slug, target_waypoint_slug, target_rung_json, status, batch_id, created_at, updated_at) "
            "VALUES (?, ?, ?, 'easier', 'w1', 'w0', '{}', 'generating', ?, ?, ?)",
            (f"rv_{item_id}", item_id, lo, f"b_{item_id}", at, at))
        connection.commit()


def answer(paths: Any, item_id: str, *, correct: bool = True, presentation_id: str | None = None,
           session_id: str | None = "s1", hints: int = 0, clock: Any = None, points: float | None = None,
           first_hint_progress: str | None = None) -> str:
    """A graded attempt through the real pipeline (a manual self-grade)."""

    vault = load_vault(paths.root)
    from learnloop.db.repositories import Repository

    repository = Repository(paths.sqlite_path)
    draft = AttemptDraft(practice_item_id=item_id, learner_answer_md="An answer.",
                         attempt_type="hinted_attempt" if hints else "independent_attempt", hints_used=hints,
                         session_id=session_id, plan_presentation_id=presentation_id,
                         first_hint_progress=first_hint_progress)
    grade = SelfGradeInput(criterion_points={"correctness": 4.0 if points is None and correct else
                                             (points if points is not None else 0.0)}, confidence=4)
    result = complete_self_graded_attempt(vault, repository, draft, grade, clock=clock)
    return str(result.attempt_id)


def set_item(paths: Any, item_id: str, **fields: Any) -> None:
    """Rewrite fields of an item's YAML (expected minutes, status, capability, facets...)."""

    path = paths.practice_item_path("linear-algebra", item_id)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload.update(fields)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def reveal(paths: Any, item_id: str, *, amount: float, at: str, lo: str = LO, reveal_id: str | None = None) -> None:
    """A ``reveal_events`` row (a tutor answer overlapping the item's answer)."""

    import sqlite3
    from contextlib import closing as _closing

    with _closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO reveal_events(id, practice_item_id, learning_object_id, source_kind, amount, basis, created_at) "
            "VALUES (?, ?, ?, 'tutor_answer', ?, 'overlap', ?)",
            (reveal_id or f"rv_{item_id}_{at}", item_id, lo, amount, at))
        connection.commit()


def selections(paths: Any, kind: str | None = None) -> list[dict[str, Any]]:
    import sqlite3
    from contextlib import closing as _closing

    from learnloop.db.stores import ad_serving

    with _closing(sqlite3.connect(paths.sqlite_path)) as connection:
        return ad_serving.selections(connection, kind=kind)


def block_events(paths: Any, kind: str) -> list[dict[str, Any]]:
    import json as _json

    found = rows(paths.sqlite_path, "SELECT * FROM attention_block_events WHERE kind = ? ORDER BY created_at, rowid",
                 (kind,))
    for row in found:
        row["detail"] = _json.loads(row.get("detail_json") or "{}")
    return found


class ProposalLLM:
    """A structured client answering the relatedness proposal, recording every prompt."""

    provider_name = "fake_llm"
    provider_type = "chatgpt_plan"
    model = "fake-relatedness"

    def __init__(self, answer: Mapping[str, Any] | None = None, *, fail: Exception | None = None) -> None:
        self.answer = dict(answer or {"items": [], "learning_objects": []})
        self.fail = fail
        self.prompts: list[str] = []

    def supports(self, capability: str) -> bool:
        return capability in {STRUCTURED_COMPLETION, BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, TOOL_FREE}

    def complete(self, request: Any) -> Any:
        self.prompts.append(request.prompt)
        report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 50,
                           "resolved_model": self.model})
        if self.fail is not None:
            raise self.fail
        return request.result_model.model_validate(self.answer)


__all__ = ["EASY", "HARD", "ITEMS", "LO", "ProposalLLM", "QUIET", "SUCCESSOR", "TASK_FEATURES", "ad23_vault",
           "answer", "block_events", "env_for", "reveal", "rows", "selections", "set_item"]
