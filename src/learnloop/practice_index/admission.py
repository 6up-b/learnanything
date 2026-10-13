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
* the learner-set LO lifecycle (dormant or resolved LOs are put away), and a
  card the reader's reference-question sweep adopted while its kill switch
  ``tutor_qa.adopt_reference_questions`` is off (``vault.lifecycle``).

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
from dataclasses import dataclass

from learnloop.attempts.attempts import COLD_FOLLOWUP_TASK_KINDS
from learnloop.clock import Clock
from learnloop.db.repositories import PracticeItemState, Repository
from learnloop.diagnosis.remediation import COLD_RETRIEVAL_DELAY
from learnloop.scheduling.serving_exclusions import out_of_timing_serving_exclusions
from learnloop.substrate.instrument_serving import unservable_reason
from learnloop.vault.lifecycle import (
    REFERENCE_ADOPTION_DISABLED,
    learning_object_servable,
    practice_item_serving_block,
)
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
    "reference_adoption_disabled",
    "cold_check_reserved",
    "revealed_recently",
    "held_out_material",
)


@dataclass(frozen=True)
class PracticeAdmission:
    """One consistent read of every input the rules need; no writes."""

    item_states: dict[str, PracticeItemState]
    exam_reserved: frozenset[str]
    variant_pending: frozenset[str]
    staged_owned: frozenset[str]
    cold_reserved: frozenset[str]
    revealed_recently: frozenset[str]
    #: Items made from held-out material (exam protection, Codex review F1).
    held_out: frozenset[str] = frozenset()

    @classmethod
    def load(cls, vault: LoadedVault, repository: Repository, *,
             clock: Clock | None = None) -> PracticeAdmission:
        # The one place serving reads these sets (``scheduling.serving_exclusions``),
        # shared with Today's queue and learner-field F2's quick check.
        exclusions = out_of_timing_serving_exclusions(
            vault, repository, cold_followup_kinds=COLD_FOLLOWUP_TASK_KINDS,
            reveal_window=COLD_RETRIEVAL_DELAY, clock=clock,
        )
        return cls(
            item_states=repository.practice_item_states(),
            exam_reserved=exclusions.reserved_exam_item_ids,
            variant_pending=exclusions.rung_variant_hold_ids,
            staged_owned=exclusions.staged_owned_item_ids,
            cold_reserved=exclusions.cold_check_reserved_item_ids,
            revealed_recently=exclusions.revealed_recently_item_ids,
            held_out=exclusions.held_out_item_ids,
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
        if item.id in self.held_out:
            return "held_out_material"
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
        if practice_item_serving_block(vault, item) == REFERENCE_ADOPTION_DISABLED:
            # A card the reader's reference-question sweep adopted, while
            # ``tutor_qa.adopt_reference_questions`` is off: Today does not
            # serve it, so it is not proposed either.
            return "reference_adoption_disabled"
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
