"""Reader follow-ups (Nov 1), item 3: curriculum C1's two follow-ups from the round-5
ruling (``docs/reviews/curriculum-c1-plan-follows-path.md``, "Orchestrator rulings",
round-5 verify 20261101-034720-G33NFM, both ruled Low):

* **(a)** "The subscription precheck resolves the route separately from judge()'s own
  ChatRoute." Now the automatic refresh resolves the path judge's route once, checks it
  plan-only, and passes it into ``judge()``; the plan-only policy is also enforced on the
  exact client that sends (a resolution that lands on a metered client sends nothing).
* **(b)** "The gate check is not bound to the protection admission's generation." Now the
  gate is asked of the same vault snapshot as protection, inside the coverage guard's
  generation-bound validation, at request and write admission.

Every model is a fake; nothing leaves the machine.
"""
from __future__ import annotations

from learnloop.source_retrieval import deliverable_path as DP
from learnloop.source_retrieval import deliverables as DL
from learnloop.vault.loader import load_vault
from tests.deliverable_fixtures import PlanDeliverableFake
from tests.helpers import append_config_toml
from tests.test_curriculum_c1_fix_round5 import MeteredFake, _rows
from tests.test_curriculum_c1_plan_follows_path import C1_OFF, PRIMARIES, _c1


def _stale(tmp_path, monkeypatch):
    c1 = _c1(tmp_path, monkeypatch, due_at="2026-12-20")
    c1.clock.advance(days=1)  # the days left are in the path's key: a day later it is stale
    return c1


# -- (a) the route judge() sends on is the one the refresh checked ------------------------------------------


def test_c1_r5_followup_a_the_refresh_resolves_its_route_once_and_judge_sends_on_it(tmp_path, monkeypatch):
    import learnloop.practice_index.paid as paid

    c1 = _stale(tmp_path, monkeypatch)
    fake = PlanDeliverableFake(primaries=PRIMARIES)
    resolved: list[str] = []
    real = paid.plan_route

    def counting(vault, task, client=None):
        resolved.append(task)
        return real(vault, task, client)

    monkeypatch.setattr(paid, "plan_route", counting)
    monkeypatch.setattr(DL, "plan_route", counting)
    routes: list[object] = []
    real_judge = DP.judge
    monkeypatch.setattr(DP, "judge", lambda *a, **k: (routes.append(k.get("route")), real_judge(*a, **k))[1])
    result = DP.refresh_for_plan(c1.vault, c1.repository, client=fake)
    assert result["status"] == "ready" and fake.calls == 1
    # One resolution of the path judge's route (before: the precheck's, then judge()'s own).
    assert resolved.count(DL.PATH_ROUTE) == 1
    (route,) = routes
    assert isinstance(route, DL.ChatRoute) and route.plan_only and route.client is fake


def test_c1_r5_followup_a_a_metered_client_behind_a_plan_route_sends_nothing(tmp_path, monkeypatch):
    c1 = _stale(tmp_path, monkeypatch)
    monkeypatch.delenv(DL.MODELS_ENV, raising=False)
    vault = c1.vault
    # The planned route is the subscription plan (the template's routing) ...
    assert DP.plan_refresh_route_problem(vault) is None
    metered = MeteredFake(primaries=PRIMARIES)
    resolutions: list[object] = []

    def lands_metered(_vault, route):
        resolutions.append(route)
        return metered, None

    # ... but the client the resolution hands back is a metered one.
    monkeypatch.setattr(DL, "resolve_client", lands_metered)
    rows = _rows(c1)
    result = DP.refresh_for_plan(vault, c1.repository)
    assert resolutions, "the route's client was resolved"
    assert metered.calls == 0 and _rows(c1) == rows
    assert result["status"] == "unavailable" and result["reason"] == DL.PLAN_ONLY_REASON


def test_c1_r5_followup_a_a_guide_judgment_keeps_its_route_rules(tmp_path, monkeypatch):
    # The plan-only policy is the automatic refresh's alone: a learner's own judgment on a
    # metered client still runs (today's behaviour, fix round 5).
    c1 = _stale(tmp_path, monkeypatch)
    metered = MeteredFake(primaries=PRIMARIES)
    append_config_toml(c1.paths.root, "\n[source_retrieval]\nllm_price_per_million = 1.0\n")
    result = DP.judge(load_vault(c1.paths.root), c1.repository, c1.goal_id, client=metered)
    assert result.status == "ready" and metered.calls == 1


# -- (b) the gate is read inside the snapshot validation --------------------------------------------------


class Published:
    """A loaded-vault provider with the sidecar's generation API (``snapshot`` and
    ``admit``): what the coverage guard validates its admission against."""

    def __init__(self, vault) -> None:
        self.state = (vault, 1)

    def __call__(self):
        return self.state[0]

    def snapshot(self):
        return self.state

    def admit(self, generation) -> bool:
        return self.state[1] == generation

    def reload(self, vault) -> None:
        self.state = (vault, self.state[1] + 1)


def _gate_on(vault) -> bool:
    from learnloop.daily_plan.engine import deliverable_plan_active

    return deliverable_plan_active(vault) and DP.plan_refresh_reason(vault) is None


def test_c1_r5_followup_b_a_reload_right_after_the_gates_read_cannot_slip_into_the_admission(tmp_path, monkeypatch):
    c1 = _stale(tmp_path, monkeypatch)
    on_vault = c1.vault
    append_config_toml(c1.paths.root, "\n" + C1_OFF)
    off_vault = load_vault(c1.paths.root)
    assert _gate_on(on_vault) and not _gate_on(off_vault)
    published = Published(on_vault)
    reads: list[bool] = []

    def gate(vault=None) -> bool:
        current = vault if vault is not None else published()
        verdict = _gate_on(current)
        reads.append(verdict)
        if len(reads) == 1:
            # The reload that turns C1 off lands right after the gate's read at the
            # request's admission (the round-5 ruling's window).
            published.reload(off_vault)
        return verdict

    fake = PlanDeliverableFake(primaries=PRIMARIES)
    rows = _rows(c1)
    result = DP.judge(on_vault, c1.repository, c1.goal_id, client=fake, live_vault=published, still_wanted=gate)
    # The admission's snapshot is the reloaded vault, C1 off there: nothing is sent or kept.
    assert fake.calls == 0 and _rows(c1) == rows
    assert result.status == "switched_off"


def test_c1_r5_followup_b_the_gate_reads_the_admitted_snapshots_vault(tmp_path, monkeypatch):
    c1 = _stale(tmp_path, monkeypatch)
    published = Published(c1.vault)
    seen: list[object] = []

    def gate(vault=None) -> bool:
        seen.append(vault)
        return _gate_on(vault if vault is not None else published())

    fake = PlanDeliverableFake(primaries=PRIMARIES)
    result = DP.judge(c1.vault, c1.repository, c1.goal_id, client=fake, live_vault=published, still_wanted=gate)
    assert result.status == "ready" and fake.calls == 1
    # Every check (the attempt's admission, each physical request a transport reports, the
    # write) handed the gate the snapshot it validated.
    assert len(seen) >= 2 and all(vault is published.state[0] for vault in seen)


def test_c1_r5_followup_b_an_unreadable_gate_admits_nothing(tmp_path, monkeypatch):
    c1 = _stale(tmp_path, monkeypatch)

    def broken(_vault) -> bool:
        raise RuntimeError("the switches cannot be read")

    fake = PlanDeliverableFake(primaries=PRIMARIES)
    rows = _rows(c1)
    result = DP.judge(c1.vault, c1.repository, c1.goal_id, client=fake, still_wanted=broken)
    assert fake.calls == 0 and _rows(c1) == rows and result.status == "switched_off"
