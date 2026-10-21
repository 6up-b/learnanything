"""Builders and fakes for Reader workbench RW7a's tests (reading paths; no network).

``build_path_vault`` is the daily-plan vault (the placement LOs with
``expected_minutes`` items) at DL2's version plus a textbook reading
``ext_text`` of source ``src_text`` with four sections: ``sec_eigen`` (cites
``lo_eigen_basics``, holds Exercise 1.1), ``sec_spectral``
(``lo_spectral``), ``sec_diag`` (``lo_diag``, holds Exercise 3.1) and
``sec_history`` (no LO). LOs cite their section through provenance, the way
ingest links them, so ``reader_progression.learning_objects_by_section``
finds them.

``PathJudgeFake`` answers ``reading_path_judge`` from the prompt's own
context: a fixed label per section ref (``labels``: section id -> label),
else ``core``, with a reason naming the label. Plumbing checks only, never
evidence about label quality.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping

import learnloop.clock as clock_module
import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.ai.execution import report_call_usage
from learnloop.ai.isolation import TOOL_FREE
from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, STRUCTURED_COMPLETION
from learnloop.db.repositories import Repository
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, write_yaml
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.helpers import create_daily_plan_vault
from tests.source_service_fakes import seed_textbook
from tests.structured_ai import StructuredClientFake

DAY1 = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
SOURCE = "src_text"
EXT = "ext_text"
VERSION = "mvp-0.29"

#: section id -> (header, [(text, page)]); spans are numbered t1.. in order.
UNITS: dict[str, tuple[str, list[tuple[str, int]]]] = {
    "sec_eigen": ("1 Eigenvalues", [
        ("Eigenvalues are the roots of the characteristic polynomial det(A - tI) of a square matrix.", 1),
        ("Exercise 1.1 Compute the eigenvalues of the diagonal matrix [[2,0],[0,3]].", 1),
    ]),
    "sec_spectral": ("2 The spectral theorem", [
        ("A real symmetric matrix has an orthonormal basis of eigenvectors and real eigenvalues.", 2),
    ]),
    "sec_diag": ("3 Diagonalization", [
        ("A square matrix is diagonalizable when it has a basis of eigenvectors; then A = P D P^-1.", 3),
        ("Exercise 3.1 Diagonalize the matrix [[1,1],[0,2]] and check that A = P D P^-1.", 3),
    ]),
    "sec_history": ("4 A short history", [
        ("Cauchy and Sylvester named and studied the characteristic equation in the nineteenth century.", 4),
    ]),
}
#: Which LO each section teaches (its provenance cites the section's first text block).
SECTION_LO = {"sec_eigen": "lo_eigen_basics", "sec_spectral": "lo_spectral", "sec_diag": "lo_diag"}
PLAN_LOS = {"lo_extra": [("pi_extra_1", 2.0), ("pi_extra_2", 2.0)]}


class FixedClock:
    """Freezes ``SystemClock.now`` (the sidecar's and the plan's clock)."""

    def __init__(self, monkeypatch: Any, start: datetime = DAY1) -> None:
        self.moment = start
        monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: self.moment)

    def advance(self, **delta: float) -> None:
        self.moment = self.moment + timedelta(**delta)


def build_path_vault(root: Path, *, version: str = VERSION, config: str = "") -> tuple[VaultPaths, Repository, dict[str, list[str]]]:
    paths = create_daily_plan_vault(root, learning_objects=PLAN_LOS, version=version,
                                    plan_toml=config or None)
    repository = Repository(paths.sqlite_path)
    spans = seed_textbook(repository, source_id=SOURCE, revision_id="rev_text", extraction_id=EXT,
                          title="Matrix Theory", units=UNITS)
    for section_id, lo_id in SECTION_LO.items():
        cite(paths, lo_id, spans[section_id][1])
    return paths, repository, spans


def cite(paths: VaultPaths, lo_id: str, span_id: str) -> None:
    lo_path = paths.learning_object_path("linear-algebra", lo_id)
    lo = read_yaml(lo_path)
    lo["provenance"] = {"origin": "human", "source_refs": [{
        "ref_type": "canonical_source", "ref_id": SOURCE, "locator": f"span:{EXT}/{span_id}",
        "source_id": SOURCE, "extraction_id": EXT}]}
    write_yaml(lo_path, lo)


def context(root: Path, **attrs: Any) -> SidecarContext:
    ctx = SidecarContext()
    ctx.load(root)
    ctx.grading_provider_override = "manual"
    for name, value in attrs.items():
        setattr(ctx, name, value)
    return ctx


def call(ctx: SidecarContext, name: str, params: Mapping[str, Any]) -> dict[str, Any]:
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(dict(params)))


def table_counts(repository: Repository) -> dict[str, int]:
    with repository.connection() as connection:
        names = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        return {name: connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0] for name in names}


def prompt_context(prompt: str) -> dict[str, Any]:
    start = prompt.index("{", prompt.index("prompt_version"))
    payload = json.loads(prompt[start:])
    return payload["context"]


class PathJudgeFake(StructuredClientFake):
    provider_name = "fake_path_judge"
    provider_type = "codex_sdk"
    model = "fake-path-model"

    def __init__(self, labels: Mapping[str, str] | None = None, *, provider_type: str = "codex_sdk",
                 fail: Exception | None = None, omit: tuple[str, ...] = (), reason: str | None = None) -> None:
        self.labels = dict(labels or {})
        self.provider_type = provider_type
        self.fail = fail
        self.omit = set(omit)
        self.reason = reason
        self.contexts: list[dict[str, Any]] = []
        self.prompts: list[str] = []

    def supports(self, capability: str) -> bool:
        return capability in {STRUCTURED_COMPLETION, BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, TOOL_FREE}

    def complete(self, request: Any) -> Any:
        context = prompt_context(request.prompt)
        self.contexts.append(context)
        self.prompts.append(request.prompt)
        report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 120,
                           "resolved_model": self.model})
        if self.fail is not None:
            raise self.fail
        rows = []
        for section in context["sections"]:
            if section["section_id"] in self.omit:
                continue
            label = self.labels.get(section["section_id"], "core")
            rows.append({"section_id": section["section_id"], "label": label,
                         "reason": self.reason or f"{label} at this depth"})
        return request.result_model.model_validate({"sections": rows})

    @property
    def calls(self) -> int:
        return len(self.contexts)


_ULID = __import__("re").compile(r"[0-9A-HJKMNP-TV-Z]{26}")


def normalized(value: Any) -> str:
    """A payload as canonical JSON with every ULID replaced (plan, block,
    decision and session ids are fresh per build; nothing else may differ)."""

    return _ULID.sub("<ULID>", json.dumps(value, indent=1, sort_keys=True, default=str))
