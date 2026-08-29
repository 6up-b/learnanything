"""Finalizing an agent run with its token cost (spec_diagnostic_augmentation_v1.md §2 A7).

Migration 131 put `actual_input_tokens` / `actual_output_tokens` on `agent_runs`
so §3 C3's `tokens_per_resolved_diagnostic_episode` has a numerator. Filling them
means draining the provider client's accumulator (`learnloop.ai.usage`) at
exactly the moment the run is finalized — on the failure arm as well as the
success arm, because a run that burned 40k tokens and then failed validation is
precisely the cost C3 is watching for.

That pairing is the same three lines at ~20 call sites across seven services, so
it lives here once. Callers that have no client in scope keep using
`Repository.complete_agent_run` directly; passing `client=None` here is the same
thing and reads as a deliberate "nothing to meter".
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from learnloop.clock import Clock
from learnloop.ai.usage import TokenUsage, consume_client_usage

if TYPE_CHECKING:  # pragma: no cover - import cycle: repositories imports nothing here
    from learnloop.db.repositories import Repository


def finish_agent_run(
    repository: Repository,
    agent_run_id: str | None,
    client: Any | None = None,
    *,
    status: str = "completed",
    error_message: str | None = None,
    usage: TokenUsage | None = None,
    clock: Clock | None = None,
) -> bool:
    """Complete `agent_run_id`, recording the tokens `client` reported.

    `usage` wins over `client` for the one shape that needs it: a pipeline whose
    model calls finish in an outer frame but whose run is finalized in an inner
    one (source-set synthesis) drains the client once into a local and hands the
    same value to every arm, so a double-completion cannot overwrite a real cost
    with the zeros a second drain would return.

    With neither a `usage` nor a `client` there is nothing to report, and the
    distinction matters: candidate revalidation finalizes a run that a *previous*
    process already paid for, so it must leave the recorded cost alone rather
    than write the zeros an empty drain would produce.

    `agent_run_id=None` is a no-op returning False, mirroring the `if
    agent_run_id:` guards the synthesis path already carries.
    """

    if not agent_run_id:
        return False
    if usage is not None:
        resolved: TokenUsage | None = usage
    elif client is not None:
        resolved = consume_client_usage(client)
    else:
        resolved = None
    return repository.complete_agent_run(
        agent_run_id,
        status=status,
        error_message=error_message,
        usage=resolved,
        clock=clock,
    )
