"""One diagnosis: assemble the context, call the diagnoser, validate (§5).

This is the unit both M1 (offline, into a scratch copy) and M2 (the async
worker) run. It never writes; the caller persists the outcome as a
``attempt_diagnoses``-shaped row plus a context receipt.
"""

from __future__ import annotations

import time
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from learnloop.ai.errors import AIInterrupted, AIProviderUnavailable
from learnloop.ai.spend import SpendLimitExceeded
from learnloop.ai.transport import READ_ONLY_WORKSPACE, OperationClient
from learnloop.diagnosis.split.context import (
    AssembledContext,
    CurrentAttempt,
    HistoryRetriever,
    RegistryRetriever,
    assemble_diagnosis_context,
)
from learnloop.diagnosis.split.contract import diagnosis_prompt, request_diagnosis_proposal
from learnloop.diagnosis.split.history import HistoryStore
from learnloop.diagnosis.split.settings import (
    DIAGNOSIS_PROMPT_VERSION,
    DiagnosisSettings,
    HistoryMode,
)
from learnloop.diagnosis.split.snapshot import snapshot_workspace
from learnloop.diagnosis.split.validation import validate_diagnosis_proposal
from learnloop.vault.models import LoadedVault, PracticeItem, Rubric

#: (purpose, estimated prompt tokens) -> context admitting one paid request.
CallGuard = Callable[[str, int], AbstractContextManager]

SKIPPED_NO_WORKSPACE = "provider_lacks_read_only_workspace"


@dataclass
class DiagnosisOutcome:
    attempt_id: str
    mode: str
    status: str  # completed | failed | validation_rejected | skipped
    proposal: dict[str, Any] | None = None
    validation_report: dict[str, Any] = field(default_factory=dict)
    receipt: dict[str, Any] = field(default_factory=dict)
    anchoring_suspect: bool = False
    validated_citations: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    provider: str | None = None
    model: str | None = None
    prompt_version: str = DIAGNOSIS_PROMPT_VERSION
    latency_seconds: float | None = None
    context_hash: str | None = None
    prompt_tokens: int | None = None

    @property
    def unknown_id_count(self) -> int:
        return int(self.validation_report.get("unknown_id_count") or 0)


def supports_snapshot(client: Any) -> bool:
    supports = getattr(client, "supports", None)
    return bool(callable(supports) and supports(READ_ONLY_WORKSPACE))


def _call(
    client: OperationClient,
    assembled: AssembledContext,
    *,
    guard: CallGuard | None,
    workspace: Path | None,
) -> tuple[Any, int]:
    prompt_tokens = (len(diagnosis_prompt(assembled).encode("utf-8")) + 3) // 4
    with (guard("diagnosis", prompt_tokens) if guard is not None else nullcontext()):
        return request_diagnosis_proposal(client, assembled, workspace=workspace), prompt_tokens


def run_diagnosis(
    client: OperationClient,
    *,
    vault: LoadedVault,
    item: PracticeItem,
    rubric: Rubric,
    store: HistoryStore,
    current: CurrentAttempt,
    settings: DiagnosisSettings,
    mode: HistoryMode | None = None,
    retriever: HistoryRetriever | None = None,
    guard: CallGuard | None = None,
    snapshot_parent: Path | None = None,
    token_budget: int | None = None,
    registry_retriever: RegistryRetriever | None = None,
) -> DiagnosisOutcome:
    """Diagnose one blind-graded attempt in one history mode.

    Provider failures and invalid output become ``status='failed'`` with the
    error class recorded; a spend refusal or cancellation propagates, because
    the caller must stop rather than record a diagnosis that never ran.
    """

    mode = mode or settings.history_mode
    outcome = DiagnosisOutcome(
        attempt_id=current.attempt_id,
        mode=mode,
        status="failed",
        provider=getattr(client, "provider_name", None),
        model=getattr(client, "model", None),
    )
    if mode == "snapshot" and not supports_snapshot(client):
        outcome.status = "skipped"
        outcome.error = SKIPPED_NO_WORKSPACE
        return outcome
    started = time.monotonic()
    try:
        if mode == "snapshot":
            with snapshot_workspace(vault, store, current.ref(), parent=snapshot_parent) as manifest:
                assembled = assemble_diagnosis_context(
                    vault,
                    store,
                    current,
                    settings,
                    mode=mode,
                    snapshot_manifest=manifest.as_context_note(),
                    token_budget=token_budget,
                    registry_retriever=registry_retriever,
                )
                outcome.receipt = dict(assembled.receipt)
                outcome.context_hash = assembled.context_hash
                proposal, outcome.prompt_tokens = _call(client, assembled, guard=guard, workspace=manifest.root)
                activity = getattr(client, "workspace_activity", None)
                opened = activity() if callable(activity) else None
                outcome.receipt["snapshot"] = {
                    **manifest.as_receipt(),
                    "opened": opened,
                    "opened_reported": opened is not None,
                }
                validated = validate_diagnosis_proposal(
                    proposal,
                    assembled=assembled,
                    current=current,
                    vault=vault,
                    item=item,
                    rubric=rubric,
                    store=store,
                    snapshot_known=manifest.known,
                )
        else:
            assembled = assemble_diagnosis_context(
                vault,
                store,
                current,
                settings,
                mode=mode,
                retriever=retriever,
                token_budget=token_budget,
                registry_retriever=registry_retriever,
            )
            outcome.receipt = dict(assembled.receipt)
            outcome.context_hash = assembled.context_hash
            proposal, outcome.prompt_tokens = _call(client, assembled, guard=guard, workspace=None)
            validated = validate_diagnosis_proposal(
                proposal,
                assembled=assembled,
                current=current,
                vault=vault,
                item=item,
                rubric=rubric,
                store=store,
            )
    except (AIInterrupted, SpendLimitExceeded):
        raise
    except (AIProviderUnavailable, ValueError) as exc:
        outcome.error = type(exc).__name__
        outcome.latency_seconds = round(time.monotonic() - started, 3)
        return outcome
    outcome.latency_seconds = round(time.monotonic() - started, 3)
    outcome.status = validated.status
    outcome.proposal = validated.proposal
    outcome.validation_report = validated.report
    outcome.anchoring_suspect = validated.anchoring_suspect
    outcome.validated_citations = validated.citations_as_dicts()
    outcome.receipt["anchoring_suspect"] = validated.anchoring_suspect
    outcome.receipt["validated_citations"] = outcome.validated_citations
    return outcome


__all__ = [
    "CallGuard",
    "DiagnosisOutcome",
    "SKIPPED_NO_WORKSPACE",
    "run_diagnosis",
    "supports_snapshot",
]
