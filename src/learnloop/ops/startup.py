from __future__ import annotations

from dataclasses import dataclass

from learnloop.ai.routing import ready_client_for_task, runtime_for_provider
from learnloop.ai.runtime import AIRuntimeReport
from learnloop.clock import Clock
from learnloop.ai.providers.codex import CodexRuntimeReport
from learnloop.config import CODEX_PROVIDER_NAMES
from learnloop.db.repositories import Repository
from learnloop.attempts.regrade import DeferredRegradeResult, run_deferred_ai_regrades, run_deferred_regrades
from learnloop.vault.models import LoadedVault


@dataclass(frozen=True)
class StartupMaintenanceResult:
    codex_runtime: CodexRuntimeReport
    deferred_regrades: DeferredRegradeResult
    ai_runtime: AIRuntimeReport | None = None
    # Meas §3.A8: clarification requests whose window closed since last startup.
    expired_clarifications: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "codex_runtime": self.codex_runtime.as_dict(),
            "ai_runtime": self.ai_runtime.as_dict() if self.ai_runtime else None,
            "deferred_regrades": self.deferred_regrades.as_dict(),
            "expired_clarifications": list(self.expired_clarifications),
        }


def run_startup_maintenance(
    vault: LoadedVault,
    repository: Repository,
    *,
    clock: Clock | None = None,
) -> StartupMaintenanceResult:
    # Meas §3.A8: drain answers whose re-grade never ran (a provider outage
    # between persisting the learner's words and grading them), then close the
    # window on questions nobody answered. Order matters: an answer that resolves
    # here must not first be expired out from under itself.
    from learnloop.attempts.clarification import resolve_awaiting_regrades

    # Meas §3.A8: close the window on questions nobody answered, BEFORE the
    # deferred regrades below. This is the only sweep on the path — without it an
    # ignored question leaves `manual_review_reason = provisional_pending_clarification`
    # on the attempt forever, and `pending_clarification` correctly stops offering
    # the question after the TTL, so the surface would read "provisional, not
    # final" with no action available. Expiry writes no grade: the provisional
    # grade already recorded the hedge or abstention the question existed to
    # repair, so timing out to it means changing nothing but the review state.
    from learnloop.attempts.clarification import expire_clarifications

    expired = tuple(expire_clarifications(repository, clock=clock))
    codex_runtime = runtime_for_provider(vault.root, vault.config, "codex")
    resolved = ready_client_for_task(vault.root, vault.config, "grading")
    provider_name, runtime, client = (
        resolved.provider_name,
        resolved.runtime,
        resolved.client,
    )
    if provider_name in CODEX_PROVIDER_NAMES:
        regrades = run_deferred_regrades(
            vault,
            repository,
            runtime=runtime,
            codex_client=client,
            clock=clock,
        )
        resolve_awaiting_regrades(
            vault, repository, runtime=runtime, client=client, clock=clock
        )
        return StartupMaintenanceResult(
            codex_runtime=codex_runtime,
            ai_runtime=None,
            deferred_regrades=regrades,
            expired_clarifications=expired,
        )

    regrades = run_deferred_ai_regrades(
        vault,
        repository,
        runtime=runtime,
        ai_client=client,
        clock=clock,
    )
    resolve_awaiting_regrades(
        vault, repository, runtime=runtime, client=client, clock=clock
    )
    return StartupMaintenanceResult(
        codex_runtime=codex_runtime,
        ai_runtime=runtime,
        deferred_regrades=regrades,
        expired_clarifications=expired,
    )
