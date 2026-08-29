from __future__ import annotations

from learnloop.cli.runtime import *  # noqa: F401,F403

contracts_app = typer.Typer(
    no_args_is_help=True,
    help="Inspect goal terminal-contract versions, pinned consumers, and drift (P0.4 §3.4).",
)

@contracts_app.command("show")
def contracts_show(
    goal_id: Annotated[str, typer.Argument(help="Goal id.")],
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Show the head version, full version history, drift status, and pinned consumers."""

    from learnloop.goals import goal_contracts as gc

    loaded, repository = _contracts_env(vault)
    head = gc.resolve_head(repository, goal_id)
    versions = repository.goal_contract_versions_for_goal(goal_id)
    drift = gc.detect_contract_drift(loaded, repository, goal_id)
    pins = gc.list_consumer_pins(repository, goal_id)
    payload = {
        "version": 1,
        "goal_id": goal_id,
        "head": head.as_dict() if head is not None else None,
        "versions": [
            {
                "id": v["id"],
                "version": v["version"],
                "change_class": v["change_class"],
                "content_hash": v["content_hash"],
                "support_hash": v["support_hash"],
                "author": v["author"],
                "reason": v["reason"],
                "created_at": v["created_at"],
            }
            for v in versions
        ],
        "drift": drift.as_dict(),
        "pinned_consumers": [pin.as_dict() for pin in pins],
    }
    typer.echo(_dump(payload))

@contracts_app.command("compare")
def contracts_compare(
    goal_id: Annotated[str, typer.Argument(help="Goal id.")],
    version_a: Annotated[str, typer.Argument(help="Version id A.")],
    version_b: Annotated[str, typer.Argument(help="Version id B.")],
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Field-level diff of two versions + whether their support hashes differ."""

    from learnloop.goals import goal_contracts as gc

    _, repository = _contracts_env(vault)
    a = repository.fetch_goal_contract_version(version_a)
    b = repository.fetch_goal_contract_version(version_b)
    if a is None or b is None:
        typer.echo(_dump({"version": 1, "error": "unknown_version"}))
        raise typer.Exit(code=1)
    body_a = jsonlib.loads(a["contract_json"])
    body_b = jsonlib.loads(b["contract_json"])
    diff = {
        key: {"a": body_a.get(key), "b": body_b.get(key)}
        for key in sorted(set(body_a) | set(body_b))
        if body_a.get(key) != body_b.get(key)
    }
    typer.echo(
        _dump(
            {
                "version": 1,
                "goal_id": goal_id,
                "change_class": gc.compute_change_class(body_a, body_b),
                "support_hash_differs": a["support_hash"] != b["support_hash"],
                "field_diff": diff,
            }
        )
    )

@contracts_app.command("amend")
def contracts_amend(
    goal_id: Annotated[str, typer.Argument(help="Goal id.")],
    reason: Annotated[str | None, typer.Option("--reason", help="Amendment reason.")] = None,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Adopt the current YAML draft edits as an appended successor (the sanctioned
    drift-adoption path, §3). Requires a confirmed head."""

    from learnloop.goals import goal_contracts as gc

    loaded, repository = _contracts_env(vault)
    head = gc.resolve_head(repository, goal_id)
    if head is None:
        typer.echo(_dump({"version": 1, "error": "not_confirmed", "goal_id": goal_id}))
        raise typer.Exit(code=1)
    goal = next((g for g in loaded.goals if g.id == goal_id), None)
    if goal is None:
        typer.echo(_dump({"version": 1, "error": "goal_missing", "goal_id": goal_id}))
        raise typer.Exit(code=1)
    merged = dict(head.contract)
    merged.update(
        {
            "purpose": goal.title,
            "due_at": goal.due_at,
            "target_recall": goal.target_recall,
            "facet_scope": goal.facet_scope.model_dump(),
            "exam": goal.exam.model_dump(),
        }
    )
    version = gc.append_successor(
        repository, goal_id=goal_id, proposed_body=merged, reason=reason, vault=loaded
    )
    typer.echo(_dump({"version": 1, "amended": version.as_dict()}))

__all__ = [name for name in globals() if not name.startswith("__")]
