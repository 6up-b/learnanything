"""The E1 GPU-hours meter: cumulative charging, refusals, crash charging, and
the cap stopping the orchestrator's own child process."""
from __future__ import annotations

import sys

import pytest

from learnloop.experiments.contextual_embeddings.e1.gpu_meter import GpuBudgetExceeded, GpuMeter, supervise


class Clock:
    def __init__(self, now: float = 1_000_000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


def test_each_worker_is_charged_its_wall_time_and_the_cap_is_cumulative(tmp_path):
    clock = Clock()
    meter = GpuMeter(tmp_path, cap_hours=1.0, clock=clock)
    entry, deadline = meter.open(plan_id="e1_a", label="01", min_slot_s=60)
    assert deadline == pytest.approx(clock.now + 3600)
    clock.now += 1800
    meter.close(entry, status="failed")  # a failed load still counts
    again = GpuMeter(tmp_path, cap_hours=1.0, clock=clock)  # another process, another plan
    entry, deadline = again.open(plan_id="e1_b", label="01", min_slot_s=60)
    assert deadline == pytest.approx(clock.now + 1800)
    clock.now += 1790
    again.close(entry, status="exited")
    with pytest.raises(GpuBudgetExceeded, match="minimum slot"):
        again.open(plan_id="e1_b", label="02", min_slot_s=60)
    assert again.report()["used_hours"] == pytest.approx((1800 + 1790) / 3600, abs=1e-3)


def test_a_live_worker_blocks_a_second_one_and_a_crashed_one_is_charged_to_its_heartbeat(tmp_path):
    clock = Clock()
    meter = GpuMeter(tmp_path, cap_hours=4.0, grace_s=60, clock=clock)
    entry, _deadline = meter.open(plan_id="e1_a", label="01", min_slot_s=0)
    clock.now += 30
    with pytest.raises(GpuBudgetExceeded, match="still running"):
        meter.open(plan_id="e1_a", label="02", min_slot_s=0)
    meter.heartbeat(entry)
    clock.now += 5000  # the orchestrator died: no close, no heartbeat
    assert meter.used_s() == pytest.approx(30 + 60)
    meter.open(plan_id="e1_a", label="02", min_slot_s=0)  # the stale entry no longer blocks


def test_a_different_cap_cannot_reopen_the_meter(tmp_path):
    GpuMeter(tmp_path, cap_hours=4.0).report()
    with pytest.raises(ValueError, match="different cap"):
        GpuMeter(tmp_path, cap_hours=8.0).report()


def test_the_cap_stops_the_supervised_child_and_it_is_charged(tmp_path):
    meter = GpuMeter(tmp_path / "meter", cap_hours=2.0 / 3600)  # two seconds
    deadlines = []
    result = supervise([sys.executable, "-c", "import time; time.sleep(120)"], meter=meter, plan_id="e1_a",
                       label="01", heartbeat=tmp_path / "hb.json", poll_s=0.2, kill_grace_s=1.0, min_slot_s=0,
                       on_open=deadlines.append)
    assert result["stopped_at_cap"] and result["status"] == "stopped_at_cap"
    assert result["returncode"] is not None and result["returncode"] != 0
    assert 1.5 <= result["charged_s"] <= 10 and deadlines
    with pytest.raises(GpuBudgetExceeded):
        meter.open(plan_id="e1_a", label="02", min_slot_s=1)


def test_a_finished_child_is_closed_with_its_return_code(tmp_path):
    meter = GpuMeter(tmp_path, cap_hours=1.0)
    result = supervise([sys.executable, "-c", "raise SystemExit(3)"], meter=meter, plan_id="e1_a", label="01",
                       heartbeat=tmp_path / "hb.json", poll_s=0.05, min_slot_s=0)
    assert result["status"] == "failed" and result["returncode"] == 3 and not result["stopped_at_cap"]
    assert meter.report()["by_status"] == {"failed": 1}
