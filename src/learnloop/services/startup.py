from __future__ import annotations

from dataclasses import dataclass

from learnloop.clock import Clock
from learnloop.codex.client import HttpCodexClient
from learnloop.codex.runtime import CodexRuntimeReport, check_codex_runtime
from learnloop.db.repositories import Repository
from learnloop.services.regrade import DeferredRegradeResult, run_deferred_regrades
from learnloop.vault.models import LoadedVault


@dataclass(frozen=True)
class StartupMaintenanceResult:
    codex_runtime: CodexRuntimeReport
    deferred_regrades: DeferredRegradeResult

    def as_dict(self) -> dict[str, object]:
        return {
            "codex_runtime": self.codex_runtime.as_dict(),
            "deferred_regrades": self.deferred_regrades.as_dict(),
        }


def run_startup_maintenance(
    vault: LoadedVault,
    repository: Repository,
    *,
    clock: Clock | None = None,
) -> StartupMaintenanceResult:
    runtime = check_codex_runtime(vault.root, vault.config.codex)
    client = HttpCodexClient(vault.config.codex) if runtime.ready else None
    regrades = run_deferred_regrades(
        vault,
        repository,
        runtime=runtime,
        codex_client=client,
        clock=clock,
    )
    return StartupMaintenanceResult(codex_runtime=runtime, deferred_regrades=regrades)
