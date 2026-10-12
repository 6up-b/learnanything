"""Read-only admission for learner-requested practice (``find_practice``).

``build_due_queue`` decides what the scheduler SERVES. A tool that only PROPOSES
practice must not propose anything the scheduler would refuse to serve, so this
module applies the same ordinary-practice eligibility rules, built from the
same predicates and reads, without writing anything:

* item lifecycle: retired items and deactivated scheduler state;
* exam reserves (held-out exam pools are quarantined from practice);
* the pending rung-variant hold and staged-controller ownership;
* the diagnostic freshness reserve: dialogue-turn instances and
  ``diagnostic_probe`` surfaces never become ordinary practice;
* servability of the stimulus (``instrument_serving``);
* the learner-set LO lifecycle (dormant or resolved LOs are put away).

Two rules are specific to a proposal, because a proposal is a learner choosing
an item outside the scheduler's timing:

* **reserved cold checks**: the selected item of an open cold follow-up task
  is a single-use measurement; practising it early would spend it;
* **the reveal ledger**: an item whose answer was revealed within the cold
  retrieval delay is not proposed, the same window the scheduler uses before a
  revealed cold task is cold again.

The routine queue's cold-start gate (never-attempted LOs wait for a goal or an
episode) does NOT apply: an explicit request for practice is the learner
adopting the material, as with requested cards. When ``build_due_queue``
gains a new eligibility rule, add it here too; the parity test pins them.
"""
from __future__ import annotations

from collections.abc import Iterable
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC

from learnloop.attempts.attempts import COLD_FOLLOWUP_TASK_KINDS
from learnloop.clock import Clock, SystemClock
from learnloop.db.connection import connect
from learnloop.db.repositories import PracticeItemState, Repository
from learnloop.db.stores.practice_index import items_revealed_between
from learnloop.diagnosis.remediation import COLD_RETRIEVAL_DELAY
from learnloop.goals.exam_pool import reserved_item_ids as reserved_exam_pool_item_ids
from learnloop.scheduling.controller_ownership import staged_owned_practice_item_ids
from learnloop.substrate.instrument_serving import unservable_reason
from learnloop.vault.lifecycle import learning_object_servable
from learnloop.vault.models import LoadedVault, PracticeItem


EXCLUSION_REASONS = (
    "retired",
    "inactive_state",
    "exam_reserved",
    "variant_pending",
    "staged_owned",
    "dialogue_instance",
    "diagnostic_reserve",
    "unservable",
    "no_learning_object",
    "lo_not_servable",
    "cold_check_reserved",
    "revealed_recently",
)


def _iso(value) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class PracticeAdmission:
    """One consistent read of every input the rules need; no writes."""

    item_states: dict[str, PracticeItemState]
    exam_reserved: frozenset[str]
    variant_pending: frozenset[str]
    staged_owned: frozenset[str]
    cold_reserved: frozenset[str]
    revealed_recently: frozenset[str]

    @classmethod
    def load(cls, vault: LoadedVault, repository: Repository, *,
             clock: Clock | None = None) -> PracticeAdmission:
        now = (clock or SystemClock()).now()
        cold_reserved = {
            str(task["selected_item_id"])
            for kind in sorted(COLD_FOLLOWUP_TASK_KINDS)
            for task in repository.open_followup_tasks_of_kind(kind)
            if task.get("selected_item_id")
        }
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            revealed = items_revealed_between(
                connection, since=_iso(now - COLD_RETRIEVAL_DELAY), until=_iso(now),
            )
        return cls(
            item_states=repository.practice_item_states(),
            exam_reserved=frozenset(reserved_exam_pool_item_ids(repository)),
            variant_pending=frozenset(repository.rung_variant_pending_source_ids()),
            staged_owned=frozenset(staged_owned_practice_item_ids(vault, repository)),
            cold_reserved=frozenset(cold_reserved),
            revealed_recently=frozenset(revealed),
        )

    def exclusion_reason(self, vault: LoadedVault, item: PracticeItem) -> str | None:
        """Why the item cannot be proposed as ordinary practice, or ``None``."""
        if item.status != "active":
            return "retired"
        state = self.item_states.get(item.id)
        if state is not None and not state.active:
            return "inactive_state"
        if item.id in self.exam_reserved:
            return "exam_reserved"
        if item.id in self.variant_pending:
            return "variant_pending"
        if item.id in self.staged_owned:
            return "staged_owned"
        if item.practice_mode == "diagnostic_microprobe":
            return "dialogue_instance"
        if item.practice_mode == "diagnostic_probe":
            return "diagnostic_reserve"
        if unservable_reason(item) is not None:
            return "unservable"
        learning_object = vault.learning_object_for_item(item)
        if learning_object is None:
            return "no_learning_object"
        if not learning_object_servable(vault, learning_object.id):
            return "lo_not_servable"
        if item.id in self.cold_reserved:
            return "cold_check_reserved"
        if item.id in self.revealed_recently:
            return "revealed_recently"
        return None

    def admit(self, vault: LoadedVault,
              item_ids: Iterable[str]) -> tuple[list[str], dict[str, str]]:
        """Admitted ids in input order, and the reason for each exclusion."""
        admitted: list[str] = []
        excluded: dict[str, str] = {}
        for item_id in item_ids:
            item = vault.practice_items.get(item_id)
            reason = "retired" if item is None else self.exclusion_reason(vault, item)
            if reason is None:
                admitted.append(item_id)
            else:
                excluded[item_id] = reason
        return admitted, excluded


__all__ = ["EXCLUSION_REASONS", "PracticeAdmission"]
