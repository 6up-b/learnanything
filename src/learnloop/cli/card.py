from __future__ import annotations

from learnloop.cli.runtime import *  # noqa: F401,F403

card_app = typer.Typer(
    no_args_is_help=True,
    help="Learner-owned card authoring: write, reword, split, retire your practice cards.",
)

@card_app.command("write")
def card_write(
    learning_object_id: Annotated[str, typer.Argument(help="Learning Object to attach the card to.")],
    prompt: Annotated[str, typer.Option("--prompt", help="The question.")],
    answer: Annotated[str, typer.Option("--answer", help="The expected answer.")],
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Author a new card of your own."""

    from learnloop.content.authoring.item_authoring import ItemAuthoringError, author_item

    loaded = load_vault(_root(vault))
    repository = _repository(loaded.root)
    try:
        row = author_item(
            loaded.root, repository, learning_object_id=learning_object_id,
            prompt=prompt, expected_answer=answer,
        )
    except ItemAuthoringError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(row["id"])

@card_app.command("reword")
def card_reword(
    practice_item_id: Annotated[str, typer.Argument(help="Card id.")],
    prompt: Annotated[str | None, typer.Option("--prompt", help="New prompt wording.")] = None,
    answer: Annotated[str | None, typer.Option("--answer", help="New expected answer.")] = None,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Reword a card in place (prompt and/or expected answer)."""

    from learnloop.content.authoring.item_authoring import ItemAuthoringError, edit_item

    loaded = load_vault(_root(vault))
    repository = _repository(loaded.root)
    try:
        result = edit_item(
            loaded.root, repository, practice_item_id=practice_item_id,
            prompt=prompt, expected_answer=answer,
        )
    except ItemAuthoringError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"{practice_item_id} changed: {', '.join(result['changed'])}")

@card_app.command("retire")
def card_retire(
    practice_item_id: Annotated[str, typer.Argument(help="Card id.")],
    reason: Annotated[str, typer.Option("--reason", help="Typed reason (see error output for the taxonomy).")],
    note: Annotated[str | None, typer.Option("--note", help="Optional free-text note.")] = None,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Retire a card: never served again, all history kept."""

    from learnloop.content.authoring.item_authoring import ItemAuthoringError, retire_item

    loaded = load_vault(_root(vault))
    repository = _repository(loaded.root)
    try:
        retire_item(
            loaded.root, repository, practice_item_id=practice_item_id, reason=reason, note=note
        )
    except ItemAuthoringError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"{practice_item_id} -> retired ({reason})")

__all__ = [name for name in globals() if not name.startswith("__")]
