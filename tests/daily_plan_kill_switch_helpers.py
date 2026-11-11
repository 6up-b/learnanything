"""What other test files use from ``tests/test_daily_plan_kill_switch.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.db.copies import copy_tree_with_databases
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.owner_vaults import owner_vault
from tests.helpers import append_config_toml, set_algorithm_version


_VOLATILE = {"schedulerSlateId", "schedulerCandidateId", "generatedAt"}


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _served(value):
    if isinstance(value, dict):
        return {key: _served(item) for key, item in value.items() if key not in _VOLATILE}
    if isinstance(value, list):
        return [_served(item) for item in value]
    return value


def _copy(tmp_path, fixture, name, *, version, toml=None):
    root = tmp_path / name
    copy_tree_with_databases(owner_vault(fixture), root)
    set_algorithm_version(type("Paths", (), {"root": root})(), version)
    if toml:
        append_config_toml(root, toml)
    ctx = SidecarContext()
    ctx.load(root)
    ctx.grading_provider_override = "manual"
    return ctx, root


def _today_reads(ctx):
    return {
        "queue": _served(_call(ctx, "get_today_queue", {})),
        "queue_25": _served(_call(ctx, "get_today_queue", {"availableMinutes": 25})),
        "start": _served(_call(ctx, "get_start_summary", {})),
    }
