from __future__ import annotations

from dataclasses import dataclass

from learnloop.ai.client import make_ai_provider_client
from learnloop.ai.routing import fallback_provider_for, provider_for_task
from learnloop.ai.runtime import AIRuntimeReport, check_ai_runtime
from learnloop.clock import Clock
from learnloop.codex.client import make_codex_client
from learnloop.codex.runtime import CodexRuntimeReport, check_codex_runtime
from learnloop.config import CODEX_PROVIDER_NAMES
from learnloop.db.repositories import Repository
from learnloop.services.regrade import DeferredRegradeResult, run_deferred_ai_regrades, run_deferred_regrades
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
    from learnloop.services.clarification import resolve_awaiting_regrades

    # Meas §3.A8: close the window on questions nobody answered, BEFORE the
    # deferred regrades below. This is the only sweep on the path — without it an
    # ignored question leaves `manual_review_reason = provisional_pending_clarification`
    # on the attempt forever, and `pending_clarification` correctly stops offering
    # the question after the TTL, so the surface would read "provisional, not
    # final" with no action available. Expiry writes no grade: the provisional
    # grade already recorded the hedge or abstention the question existed to
    # repair, so timing out to it means changing nothing but the review state.
    from learnloop.services.clarification import expire_clarifications

    expired = tuple(expire_clarifications(repository, clock=clock))
    codex_runtime = check_codex_runtime(vault.root, vault.config.codex)
    selection = provider_for_task(vault.config, "grading")
    provider_name = selection.provider_name
    ai_runtime: AIRuntimeReport | None = None
    if provider_name in CODEX_PROVIDER_NAMES:
        client = make_codex_client(vault.config.codex, vault.root) if codex_runtime.ready else None
        regrades = run_deferred_regrades(
            vault,
            repository,
            runtime=codex_runtime,
            codex_client=client,
            clock=clock,
        )
        resolve_awaiting_regrades(
            vault, repository, runtime=codex_runtime, client=client, clock=clock
        )
        return StartupMaintenanceResult(
            codex_runtime=codex_runtime,
            ai_runtime=None,
            deferred_regrades=regrades,
            expired_clarifications=expired,
        )

    ai_runtime = check_ai_runtime(vault.root, vault.config, provider_name=provider_name)
    if not ai_runtime.ready:
        fallback = fallback_provider_for(vault.config, selection)
        if fallback in CODEX_PROVIDER_NAMES and codex_runtime.ready:
            client = make_codex_client(vault.config.codex, vault.root)
            regrades = run_deferred_regrades(
                vault,
                repository,
                runtime=codex_runtime,
                codex_client=client,
                clock=clock,
            )
            resolve_awaiting_regrades(
                vault, repository, runtime=codex_runtime, client=client, clock=clock
            )
            return StartupMaintenanceResult(
                codex_runtime=codex_runtime,
                ai_runtime=ai_runtime,
                deferred_regrades=regrades,
                expired_clarifications=expired,
            )
    ai_client = make_ai_provider_client(vault.config, vault.root, provider_name=provider_name) if ai_runtime.ready else None
    regrades = run_deferred_ai_regrades(
        vault,
        repository,
        runtime=ai_runtime,
        ai_client=ai_client,
        clock=clock,
    )
    resolve_awaiting_regrades(
        vault, repository, runtime=ai_runtime, client=ai_client, clock=clock
    )
    return StartupMaintenanceResult(
        codex_runtime=codex_runtime,
        ai_runtime=ai_runtime,
        deferred_regrades=regrades,
        expired_clarifications=expired,
    )
