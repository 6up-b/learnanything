"""Adaptive difficulty AD1: the round-5 verify's remaining items, fix round 6
(orchestrator) (docs/reviews/adaptive-difficulty-ad1-codex-review.md, "Fix
round 6").

The guarantee these pin: nothing is sent or recorded whose content was held
out in the vault snapshot current at that request's or record's admission;
reading the snapshot and admitting are one atomic step relative to reload.
Each test failed on c6dd14a29 for the reason its docstring names. Fakes only:
no network, no paid call.
"""

from __future__ import annotations

import threading
from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault

from tests.ad_fakes import AuditDecider, ForecastLLM, ad_plan_vault, rows
from tests.test_ad1_codex_rereview_fixes import _exercise, _served_with_history, _set_fields
from tests.test_ad1_fix_round4 import EXAM_SET, _add_exam_scope, _builds, _bulk_vault


# -- V1-a [High]: the vault and its generation are published as one snapshot ---------------------


def _publish_with_a_pause(ctx, vault, paused: threading.Event) -> None:
    """A reload's publication as the context performs it (under its lock when
    it has one), pausing between the vault's assignment and the generation's
    bump: the verify's interleaving."""

    lock = ctx.__dict__.get("_vault_lock")
    with lock if lock is not None else nullcontext():
        object.__setattr__(ctx, "vault", vault)
        paused.set()
        threading.Event().wait(0.5)
        object.__setattr__(ctx, "vault_generation", ctx.__dict__.get("vault_generation", 0) + 1)


def test_a_publication_paused_between_assignment_and_bump_is_never_admitted(tmp_path, monkeypatch):
    """V1-a: a worker judged the old vault; the reload assigned the vault that
    holds the revision out and paused before bumping the generation; the
    worker read the unchanged generation and passed both ``check()`` and
    ``confirm()``. The vault and its generation are now published and read
    as one snapshot under the context's lock, so the worker waits for the
    whole publication, sees the generation move, and judges the new vault."""

    from learnloop.adaptive_difficulty.sending import ProtectedContent, SendGuard
    from learnloop.content.sources import exam_material
    from learnloop_sidecar.context import SidecarContext

    paths = ad_plan_vault(tmp_path)
    _set_fields(paths, "pi_m1b", canonical_exercise=_exercise("exam_b"))
    held = exam_material.Material(spans=frozenset({("ext_rereview", "exam_b")}))
    ctx = SidecarContext()
    armed, paused = threading.Event(), threading.Event()
    reloaded: dict = {}

    def predicate(vault_or_sets, _repository):
        sets = getattr(vault_or_sets, "source_sets", None) or []
        verdict = held if any(getattr(entry, "id", None) == EXAM_SET for entry in sets) else exam_material.Material()
        if armed.is_set():
            armed.clear()
            threading.Thread(target=_publish_with_a_pause, args=(ctx, reloaded["vault"], paused)).start()
            assert paused.wait(5), "the reload assigned the protected vault"
        return verdict

    try:
        ctx.load(paths.root)
        vault = ctx.vault
        _add_exam_scope(paths)
        reloaded["vault"] = load_vault(paths.root)
        monkeypatch.setattr(exam_material, "held_out_material", predicate)
        guard = SendGuard(vault, Repository(paths.sqlite_path), items=[vault.practice_items["pi_m1b"]],
                          live_vault=ctx.loaded_vault)
        armed.set()
        with pytest.raises(ProtectedContent) as refused:
            guard.confirm(guard.check("request"), "request")
        assert type(refused.value) is ProtectedContent, "the new snapshot holds it out: protected, not stale"
    finally:
        ctx.map_builds.close()


# -- V1-b (rejected as out of scope): the last confirmation is at dispatch ------------------------


def test_the_last_confirmation_runs_after_the_outer_gate_and_the_receipt(tmp_path, monkeypatch):
    """V1-b pin: a reload after the final confirmation is out of scope, but
    the confirmation is as close to dispatch as the code allows: after the
    outer request gate's admission and the request's start receipt, and
    immediately before the transport sends. On c6dd14a29 the guard confirmed
    before the outer gate, and nothing confirmed after the receipt."""

    import tests.ad_fakes as fakes
    from learnloop.adaptive_difficulty import claims, sending
    from learnloop.adaptive_difficulty.outside import Clients, forecast_presentation
    from learnloop.ai.execution import gate_model_requests

    events: list[str] = []
    paths, step = _served_with_history(tmp_path)

    class Outer:
        def admit(self, client, *, purpose, prompt, budget):
            events.append("outer")
            return None

        def settle(self, admission, usage):
            return None

    confirm = sending.SendGuard.confirm

    def confirming(self, generation, purpose="record"):
        events.append("confirm")
        return confirm(self, generation, purpose)

    record = claims.FencedRepository.record_model_event

    def recording(self, action, event, **kwargs):
        if action == "start":
            events.append("receipt")
        return record(self, action, event, **kwargs)

    usage = fakes.report_call_usage

    def sent(values):
        events.append("send")
        return usage(values)

    monkeypatch.setattr(sending.SendGuard, "confirm", confirming)
    monkeypatch.setattr(claims.FencedRepository, "record_model_event", recording)
    monkeypatch.setattr(fakes, "report_call_usage", sent)
    with gate_model_requests(Outer()):
        outcomes = forecast_presentation(load_vault(paths.root), Repository(paths.sqlite_path),
                                         step["presentation_id"],
                                         clients=Clients(llm=ForecastLLM(p_correct=0.4), decider=AuditDecider()))
    assert sorted(outcome.status for outcome in outcomes) == ["ok", "ok"]
    # Each request (the LLM's, then the Decider's) is sent right after a
    # confirmation that follows its start receipt.
    sends = [index for index, name in enumerate(events) if name == "send"]
    assert len(sends) == 2
    for index in sends:
        assert events[index - 2:index] == ["receipt", "confirm"], events
    decider_send = sends[-1]
    assert "outer" in events[sends[0]:decider_send], "the Decider's physical request passed the outer gate"
    last_outer = max(index for index in range(decider_send) if events[index] == "outer")
    assert events[last_outer + 1:decider_send] == ["confirm", "receipt", "confirm"], events


# -- V3 [Medium]: a transient refusal is stale, retried, never settled -----------------------------


class _Moving:
    """A live-vault provider whose generation moves when told to."""

    def __init__(self, vault):
        self.vault, self.current, self.always = vault, 0, False

    def __call__(self):
        return self.vault

    def generation(self):
        if self.always:
            self.current += 1
        return self.current


AUDIT_ONLY = "[adaptive_difficulty]\noutside_forecasters = []\n"


def test_a_harmless_reload_between_the_audits_check_and_its_record_is_retried(tmp_path, monkeypatch):
    """V3 (the verify's case): an ordinary reload between the audit's record
    check and its record admission refused the record as ``protected``; with
    the forecast off the revision counted as settled, was cached, and no
    later trigger prepared it. It is now ``stale``: kept queued and audited
    by the next trigger."""

    from learnloop.adaptive_difficulty import sending
    from learnloop.adaptive_difficulty.background import schedule_item_preparation
    from learnloop.adaptive_difficulty.outside import Clients

    paths = ad_plan_vault(tmp_path, config=AUDIT_ONLY)
    vault = load_vault(paths.root)
    provider = _Moving(vault)
    check = sending.SendGuard.check
    bumped = threading.Event()

    def check_then_reload(self, purpose="request"):
        generation = check(self, purpose)
        if purpose.startswith("recording the Decider") and not bumped.is_set():
            bumped.set()
            provider.current += 1  # an ordinary reload: nothing new is held out
        return generation

    monkeypatch.setattr(sending.SendGuard, "check", check_then_reload)
    decider = AuditDecider()
    builds, clients = _builds(paths), Clients(llm=ForecastLLM(), decider=decider)
    try:
        first = schedule_item_preparation(vault, paths.sqlite_path, ["pi_m1a"], clients=clients, builds=builds,
                                          live_vault=provider)
        first.join(30)
        assert len(decider.calls) == 1 and bumped.is_set()
        assert rows(paths.sqlite_path, "SELECT * FROM judgment_ledger WHERE task = 'ad_feature_audit'") == []
        again = schedule_item_preparation(vault, paths.sqlite_path, ["pi_m1a"], clients=clients, builds=builds,
                                          live_vault=provider)
        assert again is not None, "stale is retryable: the revision was never cached as prepared"
        again.join(30)
        assert len(decider.calls) == 2
        audits = rows(paths.sqlite_path, "SELECT judge FROM judgment_ledger WHERE task = 'ad_feature_audit'")
        assert [row["judge"] for row in audits] == ["decider"] * 5
    finally:
        builds.close()


def test_four_interrupted_checks_are_stale_and_retried(tmp_path):
    """V3: when the vault kept being reloaded through every rebuild, the
    exhausted check refused as ``protected`` and the revision was settled. It
    is now ``stale``; once the vault holds still, the next trigger audits it."""

    from learnloop.adaptive_difficulty.background import schedule_item_preparation
    from learnloop.adaptive_difficulty.outside import Clients

    paths = ad_plan_vault(tmp_path, config=AUDIT_ONLY)
    vault = load_vault(paths.root)
    provider = _Moving(vault)
    provider.always = True
    decider = AuditDecider()
    builds, clients = _builds(paths), Clients(llm=ForecastLLM(), decider=decider)
    try:
        schedule_item_preparation(vault, paths.sqlite_path, ["pi_m1a"], clients=clients, builds=builds,
                                  live_vault=provider).join(30)
        assert decider.calls == [], "refused before any request"
        provider.always = False
        again = schedule_item_preparation(vault, paths.sqlite_path, ["pi_m1a"], clients=clients, builds=builds,
                                          live_vault=provider)
        assert again is not None
        again.join(30)
        assert len(decider.calls) == 1
    finally:
        builds.close()


def test_a_stale_refusal_reports_stale_and_held_out_content_reports_protected(tmp_path, monkeypatch):
    from learnloop.adaptive_difficulty.outside import Clients, forecast_item

    from tests.test_ad1_codex_rereview_fixes import _hold_out

    paths = ad_plan_vault(tmp_path)
    _set_fields(paths, "pi_m1a", canonical_exercise=_exercise("span_a"))
    vault = load_vault(paths.root)
    provider = _Moving(vault)
    provider.always = True
    stale = forecast_item(vault, Repository(paths.sqlite_path), vault.practice_items["pi_m1a"],
                          clients=Clients(llm=ForecastLLM()), live_vault=provider)
    assert stale.status == "stale"
    provider.always = False

    class HoldingOut(ForecastLLM):
        def complete(self, request):
            _hold_out(monkeypatch, "span_a")
            return super().complete(request)

    held = forecast_item(vault, Repository(paths.sqlite_path), vault.practice_items["pi_m1a"],
                         clients=Clients(llm=HoldingOut()), live_vault=provider)
    assert held.status == "protected"


# -- V4 [Medium]: a failing revision never starves the rest ----------------------------------------


class _AlwaysRaising:
    def __init__(self, failing: str):
        self.failing, self.visits = failing, []

    def audit(self, _vault, _repository, item, **_kwargs):
        self.visits.append(str(item.id))
        if str(item.id) == self.failing:
            raise RuntimeError("this revision's preparation keeps failing")
        return SimpleNamespace(as_dict=lambda: {"status": "current"})

    def forecast(self, *_args, **_kwargs):
        return SimpleNamespace(as_dict=lambda: {"status": "current"})


def test_a_revision_that_keeps_raising_never_starves_the_rest(tmp_path, monkeypatch):
    """V4: an exception while preparing A aborted the run before anything was
    recorded, so A, B, C went back to the front unchanged and every trigger
    visited A alone: [A, A, A, A]. Each revision's exception is caught; A goes
    to the back as retryable, and B and C are prepared in the same run."""

    from learnloop.adaptive_difficulty import background, feature_audit
    from learnloop.adaptive_difficulty.background import schedule_new_revisions
    from learnloop.adaptive_difficulty.outside import Clients

    paths = ad_plan_vault(tmp_path)
    vault = _bulk_vault(paths, 3)
    a, b, c = sorted(vault.practice_items)
    raising = _AlwaysRaising(a)
    monkeypatch.setattr(feature_audit, "audit_revision", raising.audit)
    monkeypatch.setattr(background, "forecast_item", raising.forecast)
    builds, clients = _builds(paths), Clients(llm=ForecastLLM())
    try:
        schedule_new_revisions(SimpleNamespace(practice_items={}), vault, paths.sqlite_path, clients=clients,
                               builds=builds).join(30)
        for _trigger in range(3):
            thread = schedule_new_revisions(vault, vault, paths.sqlite_path, clients=clients, builds=builds)
            assert thread is not None, "A stays retryable"
            thread.join(30)
        assert raising.visits == [a, b, c, a, a, a]
    finally:
        builds.close()
