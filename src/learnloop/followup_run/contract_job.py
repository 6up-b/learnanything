"""Bind the shared contract step to the workflow's existing durable retry slot."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from math import nextafter
from typing import Any

from learnloop.ai.errors import AIInvalidOutput
from learnloop.ai.execution import ModelCheckpoint, content_key, model_settings
from learnloop.ai.structured_contracts import (
    ContractFailure,
    RecoveryAllowance,
    RecoveryState,
    checked_structured_call,
    recover_from_receipts,
    recovery_note,
)
from learnloop.ai.transport import execute_structured_operation
from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.db.stores import followup_serve as store
from learnloop.db.stores.model_calls import insert_checkpoint
from learnloop.diagnosis.ai_contracts import FollowupProbeAuthored, FollowupProbeContext
from learnloop.followup_run import authoring
from learnloop.followup_run.authoring import AUTHORING_PURPOSE, AuthoringRejected, authoring_contract
from learnloop.followup_serve import workflow as wf


class CorrectionDeferred(AuthoringRejected):
    """The shared step recorded an owed correction for the next job lease."""


def correction_receipts(repository: Repository, workflow_id: str) -> list[dict[str, Any]]:
    """Only this job's completed authoring operations, never physical children."""

    with repository.connection() as connection:
        job = store.generation_job(connection, f"workflow:{workflow_id}")
        if job is None:
            return []
        return [dict(row) for row in connection.execute(
            "SELECT * FROM model_call_receipts WHERE owner_id=? AND purpose=? "
            "AND parent_call_id IS NULL AND status='completed' ORDER BY rowid DESC",
            (job["id"], AUTHORING_PURPOSE))]


def has_saved_correction(repository: Repository, workflow_id: str) -> bool:
    """Allow a read-only recovery past the lease cap; request() still forbids sends."""

    retry = wf.noted(repository, workflow_id, reason="authoring_contract_retry")
    key = retry.get("request_key")
    if retry and not key:
        # A retry queued before adoption has only the original four fields.
        with repository.connection() as connection:
            job = store.generation_job(connection, f"workflow:{workflow_id}")
        key = str(job["id"]) if job is not None else None
    if not key:
        return False
    if repository.model_checkpoint(key) is not None:
        return True
    return any((recovery_note(row.get("budget_json")) or {}).get("request_key") == key
               for row in correction_receipts(repository, workflow_id))


@dataclass
class JobContract:
    repository: Repository
    workflow_id: str
    attempt: int
    max_attempts: int
    deadline: datetime
    clock: Clock
    cancelled: Callable[[], bool] | None = None

    def stopped(self) -> bool:
        row = wf.get(self.repository, self.workflow_id)
        return (row is None or row["state"] != wf.PENDING
                or (self.cancelled is not None and self.cancelled()))

    def remaining(self) -> float:
        return (self.deadline - self.clock.now()).total_seconds()

    def admitted(self) -> bool:
        # The lease admits one operation and that provider's existing repair.
        # The spend envelope still admits each physical send independently.
        with self.repository.connection() as connection:
            job = store.generation_job(connection, f"workflow:{self.workflow_id}")
        return (job is not None and job["state"] == "leased" and job["attempt_count"] == self.attempt
                and self.attempt <= self.max_attempts)

    def request(self, client: Any, context: FollowupProbeContext, refs: Mapping[str, str],
                validate: Callable[[FollowupProbeAuthored], Any]) -> FollowupProbeAuthored:
        prompt = authoring.followup_probe_prompt(context)
        contract = authoring_contract(refs)
        with self.repository.connection() as connection:
            job = store.generation_job(connection, f"workflow:{self.workflow_id}")
        if job is None:
            raise AuthoringRejected("generation_attempts_exhausted")
        # The durable job already identifies this logical request. Keep its key
        # through the correction; no new schema-derived identity is needed.
        checkpoint = ModelCheckpoint(self.repository, str(job["id"]), AUTHORING_PURPOSE,
                                     FollowupProbeAuthored.model_validate)
        retry = wf.noted(self.repository, self.workflow_id, reason="authoring_contract_retry")
        if (retry.get("request_key", checkpoint.key) != checkpoint.key
                or retry.get("first_prompt_hash", content_key(prompt)) != content_key(prompt)
                or retry.get("settings", model_settings(client)) != model_settings(client)):
            raise AuthoringRejected(str(retry["rejection_reason"]))
        state = (RecoveryState.from_dict(retry.get("recovery_state")) if "recovery_state" in retry
                 else RecoveryState(0, retry["rejection_reason"]) if retry
                 else RecoveryState())
        claim_key = checkpoint.key + ":recovery"
        claimed = self.repository.model_checkpoint(claim_key)
        if claimed is not None:
            state = RecoveryState.from_dict(claimed["result"])

        def record(value: RecoveryState) -> None:
            nonlocal retry
            if not retry:
                if self.attempt >= self.max_attempts or self.remaining() < 1.0 or self.stopped():
                    raise AuthoringRejected(str(value.owed))
                retry = {"rejection_reason": value.owed, "deadline": self.deadline.isoformat(),
                         "rejected_attempt": self.attempt, "retry_attempt": self.attempt + 1,
                         "request_key": checkpoint.key, "recovery_state": value.as_dict(),
                         "first_prompt_hash": content_key(prompt), "settings": model_settings(client)}
                wf.note(self.repository, self.workflow_id, reason="authoring_contract_retry",
                        detail=retry, clock=self.clock)
            else:
                # Workflow events are append-only. The write-once checkpoint
                # table carries the monotone claim without adding a workflow event.
                with self.repository.atomic(), self.repository.connection() as connection:
                    if self.repository.model_checkpoint(claim_key) is not None or not self.admitted():
                        raise AuthoringRejected(str(value.owed))
                    insert_checkpoint(connection, claim_key, purpose=AUTHORING_PURPOSE, result=value.as_dict())

        def failure(info: ContractFailure) -> BaseException:
            if info.reason == "correction_deferred":
                return CorrectionDeferred(str(info.predicate))
            if info.predicate is None:
                return AIInvalidOutput(info.reason)
            return AuthoringRejected(info.predicate)

        def send(attempt, check):
            if not self.admitted() or self.stopped():
                raise AuthoringRejected(str(state.owed or "generation_attempts_exhausted"))

            def checked(answer):
                check(answer)
                validate(answer)  # Protection remains terminal and inside the operation receipt.
                return answer

            return execute_structured_operation(
                client, purpose=AUTHORING_PURPOSE, prompt=attempt.prompt, result_model=FollowupProbeAuthored,
                timeout_seconds=attempt.timeout_seconds if attempt.correcting else None, check=checked,
            )

        # The receipt commits before checkpoint.save; recover it before considering
        # spent state or the lease cap. The original key, prompt and job must match;
        # parsing and the contract validate the answer again.
        receipts = [row for row in correction_receipts(self.repository, self.workflow_id)
                    if (recovery_note(row.get("budget_json")) or {}).get("request_key") == checkpoint.key]
        recovered = recover_from_receipts(receipts, first_prompt=prompt, request_key=checkpoint.key,
                                          contract=contract, read=FollowupProbeAuthored.model_validate_json)
        if recovered is not None:
            validate(recovered[0])
            checkpoint.save(recovered[0])
        return checked_structured_call(
            # First successes still belong to the existing item persistence and
            # orphan-retirement workflow. Only corrections need this new slot.
            first_prompt=prompt, contract=contract, send=send, checkpoint=checkpoint if retry else None,
            request_key=checkpoint.key, failure=failure,
            recovery=RecoveryAllowance(admit=self.admitted, remaining_seconds=self.remaining,
                                       # The old job accepts exactly one second. The shared
                                       # floor is exclusive, so use its adjacent lower float.
                                       min_request_seconds=nextafter(1.0, 0.0), cancelled=self.stopped, state=state,
                                       record=record, defer=True),
        )
