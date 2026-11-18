"""Sweep execution for parameter certificates.

This keeps sim.sweep out of params.sensitivity_certificates.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from learnloop.params.sensitivity_certificates import Certificate, certificate_from_sweep_report


def _value_grid(low: float, high: float, points: int, covered: Any) -> list[Any]:
    if points < 2:
        points = 2
    step = (high - low) / (points - 1)
    grid = [round(low + step * i, 6) for i in range(points)]
    if isinstance(covered, (int, float)) and not isinstance(covered, bool):
        if covered not in grid:
            grid.append(covered)
    return sorted(set(grid))


def certify(
    *,
    path: str,
    covered_value: Any,
    low: float,
    high: float,
    vault_root: Path,
    profile: Any,
    work_dir: Path,
    scenario: Mapping[str, Any] | None = None,
    grid_points: int = 5,
    days: int = 12,
    items_per_day: int = 4,
    seed: int = 42,
) -> Certificate:
    """Run a fine value-grid sweep across ``[low, high]`` on the fixed scenario and
    build a certificate. ``path`` must be a config path the sweep can override."""

    from learnloop.sim.sweep import SweepEntry, run_sweep

    grid = _value_grid(low, high, grid_points, covered_value)
    report = run_sweep(
        Path(vault_root),
        profile,
        sweep_spec=[SweepEntry(param_path=path, values=grid)],
        days=days,
        items_per_day=items_per_day,
        seed=seed,
        work_dir=Path(work_dir),
    )
    scenario_meta = dict(scenario or {})
    scenario_meta.setdefault("profile", getattr(profile, "name", None))
    scenario_meta.setdefault("seed", seed)
    scenario_meta.setdefault("days", days)
    scenario_meta.setdefault("grid", grid)
    return certificate_from_sweep_report(
        path=path,
        covered_value=covered_value,
        plausible_range={"low": low, "high": high},
        scenario=scenario_meta,
        sweep_report=report,
    )
