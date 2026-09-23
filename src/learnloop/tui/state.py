from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from learnloop.ai.execution import record_model_calls
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.scheduling.scheduler import SchedulerSession, ScheduledItem, build_due_queue
from learnloop.ops.startup import StartupMaintenanceResult, run_startup_maintenance
from learnloop.substrate.state_sync import StateSyncResult, sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.repository import open_vault_repository


TUI_OWNER_KIND = "tui"


@dataclass
class TuiState:
    vault_root: Path
    vault: LoadedVault
    repository: Repository
    queue: list[ScheduledItem] = field(default_factory=list)
    state_sync: StateSyncResult | None = None
    startup_maintenance: StartupMaintenanceResult | None = None
    # One owner for every model call this TUI session makes.
    receipt_owner_id: str = field(default_factory=lambda: f"session:{new_ulid()}")

    @classmethod
    def load(cls, vault_root: Path) -> "TuiState":
        vault = load_vault(vault_root)
        repository = open_vault_repository(
            vault.root,
            VaultPaths(vault.root, vault.config).sqlite_path,
        )
        state = cls(vault_root=vault.root, vault=vault, repository=repository)
        state.refresh()
        return state

    def refresh(self, *, session: SchedulerSession | None = None) -> None:
        self.vault = load_vault(self.vault_root)
        self.repository = open_vault_repository(
            self.vault.root,
            VaultPaths(self.vault.root, self.vault.config).sqlite_path,
        )
        self.state_sync = sync_vault_state(self.vault, self.repository)
        with self.model_receipts():
            self.startup_maintenance = run_startup_maintenance(self.vault, self.repository)
        self.queue = build_due_queue(
            self.vault,
            self.repository,
            session=session or SchedulerSession(),
        )

    def model_receipts(self):
        """Record the model calls made inside this block as this session's receipts."""

        return record_model_calls(self.repository, owner_kind=TUI_OWNER_KIND, owner_id=self.receipt_owner_id)
