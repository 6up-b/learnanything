from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from learnloop.db.repositories import Repository
from learnloop.services.scheduler import SchedulerSession, ScheduledItem, build_due_queue
from learnloop.services.startup import StartupMaintenanceResult, run_startup_maintenance
from learnloop.services.state_sync import StateSyncResult, sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths


@dataclass
class TuiState:
    vault_root: Path
    vault: LoadedVault
    repository: Repository
    queue: list[ScheduledItem] = field(default_factory=list)
    state_sync: StateSyncResult | None = None
    startup_maintenance: StartupMaintenanceResult | None = None

    @classmethod
    def load(cls, vault_root: Path) -> "TuiState":
        vault = load_vault(vault_root)
        repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
        state = cls(vault_root=vault.root, vault=vault, repository=repository)
        state.refresh()
        return state

    def refresh(self, *, session: SchedulerSession | None = None) -> None:
        self.vault = load_vault(self.vault_root)
        self.repository = Repository(VaultPaths(self.vault.root, self.vault.config).sqlite_path)
        self.state_sync = sync_vault_state(self.vault, self.repository)
        self.startup_maintenance = run_startup_maintenance(self.vault, self.repository)
        self.queue = build_due_queue(
            self.vault,
            self.repository,
            session=session or SchedulerSession(),
        )
