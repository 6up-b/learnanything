"""Durable rich author verdicts for one execution of a figure job."""

from copy import copy
from dataclasses import replace
from types import SimpleNamespace

from learnloop import provenance
from learnloop.db.stores.provenance import job_attempt_decisions
from learnloop.figures import records as FR


class RichAttempts(FR.AuthorAttempts):
    def __init__(self, repository, job_id, request, request_id, prompt_version):
        super().__init__(prompt_version=prompt_version, kind=FR.KIND_RICH_AUTHOR)
        self.repository = repository
        self.job_id = job_id
        self.request = request
        self.request_id = request_id
        self.execution = f"{job_id or 'rich'}.{provenance.new_record_id()}"
        self.record_id = None
        self.persisted = False
        if job_id:
            job_attempt_decisions(repository, job_id)

    def start(self, number, *, route=None):
        if self.current:
            self.finish(retrying=True)
        if route is not None:
            if route.calls is not None:
                route.calls.last_resolved_model = None
            self.model = route.model
        super().start(number)
        self.record_id = f"{self.execution}.{number}"
        self.persisted = False
        self.stage()

    def ask(self, route, *args, **kwargs):
        try:
            return route.ask(*args, **kwargs)
        finally:
            self.model = route.model
            self.stage()

    def end(self, rule, **kwargs):
        super().end(rule, **kwargs)
        self.stage()

    def record(self, *, result=None, error=None, interrupted=False, retrying=False):
        outcome = None if result is None else SimpleNamespace(
            view={"figure_id": result.get("figure_id"), "verification": result.get("verification")},
            reused=bool(result.get("reused")))
        snapshot = copy(self)
        snapshot.attempts = [*self.attempts[:-1], copy(self.current)]
        record = snapshot.records(request=self.request, request_id=self.request_id, model=self.model,
                                  job_id=self.job_id, outcome=outcome, error=error)[-1]
        if interrupted or retrying:
            rule = self.current.rule or FR.INTERRUPTED
            status = self.current.status or ("discarded" if self.current.rule else "failed")
            record = replace(record, rule=rule, status=status, chosen_ref=None)
        outcome_code = "retrying" if retrying else "interrupted" if interrupted else record.facts["outcome"]
        return replace(record, id=self.record_id,
                       facts={**record.facts, "outcome": outcome_code})

    def stage(self):
        if self.job_id:
            job_attempt_decisions(self.repository, self.job_id, record=self.record(interrupted=True), publish=False)

    def finish(self, **kwargs):
        if self.current is None or self.persisted:
            return
        job_attempt_decisions(self.repository, self.job_id, record=self.record(**kwargs))
        self.persisted = True
