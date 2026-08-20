from __future__ import annotations

from learnloop.cli.runtime import *  # noqa: F401,F403

source_set_app = typer.Typer(no_args_is_help=True, help="Create and manage source collections (§4.3).")

@source_set_app.command("create")
def source_set_create(
    set_id: Annotated[str, typer.Argument(help="Source-set id.")],
    subject_id: Annotated[str, typer.Option("--subject", help="Subject id the set belongs to.")],
    title: Annotated[str, typer.Option("--title", help="Human title.")] = "",
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Create an empty source collection (§4.3)."""

    from learnloop.vault.writer import upsert_source_set

    root = _root(vault)
    upsert_source_set(root, {"id": set_id, "subject_id": subject_id, "title": title or set_id, "members": []})
    _show_source_set(root, set_id, json_output)

@source_set_app.command("add")
def source_set_add(
    set_id: Annotated[str, typer.Argument(help="Source-set id.")],
    source_id: Annotated[str, typer.Option("--source", help="Library source id.")],
    revision_id: Annotated[str, typer.Option("--revision", help="Pinned revision id (required, §4.3).")],
    role: Annotated[str, typer.Option("--role", help="Membership role (open string).")] = "reference",
    units: Annotated[list[str] | None, typer.Option("--unit", help="Scope unit id (repeatable). Empty = whole artifact.")] = None,
    priority: Annotated[int, typer.Option("--priority")] = 1,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Add a pinned source to a collection (membership owns role/scope, §4.3)."""

    from learnloop.vault.loader import load_vault
    from learnloop.vault.writer import upsert_source_set

    root = _root(vault)
    vault_loaded = load_vault(root)
    source_set = next((s for s in vault_loaded.source_sets if s.id == set_id), None)
    if source_set is None:
        typer.echo(f"Source set '{set_id}' does not exist; create it first.", err=True)
        raise typer.Exit(code=1)
    members = [member.model_dump(mode="json", exclude_none=False) for member in source_set.members]
    members = [member for member in members if member.get("source_id") != source_id]
    members.append(
        {
            "source_id": source_id,
            "revision_id": revision_id,
            "default_role": role,
            "scope": [{"unit_id": unit_id, "role_override": None} for unit_id in (units or [])],
            "priority": priority,
        }
    )
    upsert_source_set(
        root,
        {"id": set_id, "subject_id": source_set.subject_id, "title": source_set.title, "members": members},
    )
    _show_source_set(root, set_id, json_output)

@source_set_app.command("update")
def source_set_update(
    set_id: Annotated[str, typer.Argument(help="Source-set id.")],
    title: Annotated[str | None, typer.Option("--title")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Update a collection's title (membership edits use add)."""

    from learnloop.vault.writer import upsert_source_set

    root = _root(vault)
    payload: dict[str, object] = {"id": set_id}
    if title is not None:
        payload["title"] = title
    upsert_source_set(root, payload)
    _show_source_set(root, set_id, json_output)

@source_set_app.command("list")
def source_set_list(
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """List source collections."""

    from learnloop.vault.loader import load_vault

    vault_loaded = load_vault(_root(vault))
    rows = [
        {"id": s.id, "subject_id": s.subject_id, "title": s.title, "members": len(s.members)}
        for s in vault_loaded.source_sets
    ]
    if json_output:
        typer.echo(_dump({"version": 1, "source_sets": rows}))
        return
    for row in rows:
        typer.echo(f"{row['id']:<28} {row['subject_id']:<18} members={row['members']}  {row['title']}")

@source_set_app.command("show")
def source_set_show(
    set_id: Annotated[str, typer.Argument(help="Source-set id.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
    vault: Annotated[Path | None, typer.Option("--vault")] = None,
) -> None:
    """Show a collection's members, roles, and scopes."""

    _show_source_set(_root(vault), set_id, json_output)

__all__ = [name for name in globals() if not name.startswith("__")]
