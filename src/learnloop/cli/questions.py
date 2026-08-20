from __future__ import annotations

from learnloop.cli.runtime import *  # noqa: F401,F403

questions_app = typer.Typer(
    no_args_is_help=True,
    help="Outstanding-question queue: questions you raised that are still open.",
)

@questions_app.command("list")
def questions_list(
    all_states: Annotated[bool, typer.Option("--all", help="Include resolved and dismissed questions.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """List the open-question queue (newest first)."""

    from learnloop.tutor.question_queue import list_question_queue

    loaded = load_vault(_root(vault))
    repository = _repository(loaded.root)
    rows = list_question_queue(repository, resolution=None if all_states else "open")
    if json_output:
        typer.echo(_dump({"version": 1, "questions": rows}))
        return
    if not rows:
        typer.echo("No open questions." if not all_states else "No questions recorded.")
        return
    for row in rows:
        question = " ".join((row["question_md"] or "").split())
        if len(question) > 100:
            question = question[:97] + "..."
        promoted = " promoted" if row["promotion"] else ""
        typer.echo(
            f"{row['id']} [{row['resolution']}] ({row['context']}, {row['created_at'][:10]}, "
            f"tutor {row['answer_status']}{promoted}) {question}"
        )

@questions_app.command("resolve")
def questions_resolve(
    question_event_id: Annotated[str, typer.Argument(help="Question event id (see `questions list`).")],
    as_state: Annotated[str, typer.Option("--as", help="resolved | dismissed | open (reopen).")] = "resolved",
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
) -> None:
    """Mark a question resolved/dismissed, or reopen it."""

    from learnloop.tutor.question_queue import QuestionQueueError, set_question_resolution

    loaded = load_vault(_root(vault))
    repository = _repository(loaded.root)
    try:
        event = set_question_resolution(
            repository, question_event_id=question_event_id, resolution=as_state
        )
    except QuestionQueueError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"{event['id']} -> {event['resolution']}")

__all__ = [name for name in globals() if not name.startswith("__")]
