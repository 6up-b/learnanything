"""The ``snapshot`` history mode's as-of export (Slice 1 §5.6).

At job start the whole vault's typed history before the diagnosed attempt is
written to a per-job scratch directory OUTSIDE the vault, which becomes the
diagnoser's read-only workspace (the Codex transport's ``cwd``, replacing the
vault root). The export uses the §5.2 projection: blind-grade-equivalent
fields, legacy causal fields stripped, typed hypotheses without prose. Nothing
at or after the diagnosed attempt is written.

The directory holds learner text, so :func:`snapshot_workspace` deletes it
when the job finishes, whether it succeeds or fails.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from learnloop.diagnosis.split.context import KnownIds
from learnloop.diagnosis.split.history import (
    AttemptRef,
    HistoryAttempt,
    HistoryStore,
    HypothesisRecord,
    RegistryRecord,
    RepairRecord,
)
from learnloop.vault.models import LoadedVault, learning_object_facet_union

SNAPSHOT_EXPORT_VERSION = "diagnosis-snapshot-v1"
_UNSAFE = re.compile(r"[^A-Za-z0-9_.-]+")


def _safe(value: str) -> str:
    return _UNSAFE.sub("-", value).strip("-") or "_"


@dataclass(frozen=True)
class SnapshotManifest:
    root: Path
    manifest_hash: str
    files: tuple[str, ...]
    known: KnownIds
    as_of_attempt_id: str
    attempt_count: int
    #: What each exported file serves (diagnosis input provenance): mapped
    #: from the diagnoser's reported activity by ``provenance.snapshot_reads``.
    entries: Any = None

    @property
    def file_count(self) -> int:
        return len(self.files)

    def as_receipt(self) -> dict[str, Any]:
        return {
            "export_version": SNAPSHOT_EXPORT_VERSION,
            "manifest_hash": self.manifest_hash,
            "file_count": self.file_count,
            "attempt_count": self.attempt_count,
            "as_of_attempt_id": self.as_of_attempt_id,
        }

    def as_context_note(self) -> dict[str, Any]:
        """What the inline context says about the workspace (no learner text)."""

        return {
            "available": True,
            "export_version": SNAPSHOT_EXPORT_VERSION,
            "manifest_hash": self.manifest_hash,
            "file_count": self.file_count,
            "attempt_count": self.attempt_count,
            "layout": [
                "INDEX.md",
                "attempts/<completed_at>_<attempt_id>.md",
                "hypotheses/<id>.md",
                "registry/<id>.md",
                "graph/learning_objects.md",
                "repairs/<facet>.md",
            ],
        }


def _bullets(rows: list[tuple[str, Any]]) -> str:
    lines = []
    for key, value in rows:
        if isinstance(value, (list, tuple)):
            value = ", ".join(str(item) for item in value) if value else "-"
        elif value is None or value == "":
            value = "-"
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)


def render_attempt(attempt: HistoryAttempt, title: str) -> str:
    score = (
        f"{attempt.score:g}/{attempt.max_points:g}"
        if attempt.score is not None and attempt.max_points
        else "-"
    )
    body = [
        f"# Attempt {attempt.attempt_id}",
        "",
        _bullets(
            [
                ("date", attempt.completed_at),
                ("learning_object", f"{attempt.learning_object_id} ({title})"),
                ("practice_item", attempt.practice_item_id),
                ("surface_group", attempt.surface_group),
                ("outcome", "non_pass" if attempt.non_pass else "pass"),
                ("score", score),
                ("failed_criteria", attempt.failed_criteria),
                ("fatal_errors", attempt.fatal_errors),
                ("error_types", attempt.error_types),
                ("target_facets", attempt.target_facets),
                ("item_facets", attempt.item_facets),
                ("validity_scopes", attempt.validity_scopes),
                ("assisted", attempt.assisted),
                ("primed", attempt.primed),
                ("grader_mode", attempt.grader_mode),
            ]
        ),
        "",
        "## Item",
        "",
        attempt.item_prompt.strip() or "-",
        "",
        "## Learner answer",
        "",
        attempt.learner_answer_md.strip() or "-",
        "",
        "## First-divergence quotes",
        "",
        "\n".join(f"- {quote}" for quote in attempt.first_divergence_quotes) or "-",
        "",
    ]
    return "\n".join(body)


def _render_hypothesis(record: HypothesisRecord) -> str:
    return "\n".join(
        [
            f"# Hypothesis {record.id}",
            "",
            _bullets(
                [
                    ("kind", record.kind),
                    ("status", record.lifecycle),
                    ("scope", record.scope),
                    ("learning_object", record.learning_object_id),
                    ("source_attempt", record.source_attempt_id),
                    ("validated_evidence_count", record.validated_evidence_count),
                    ("last_updated", record.last_updated),
                    ("target_facets", record.target_facets),
                ]
            ),
            "",
            "## Statement",
            "",
            record.statement.strip() or "-",
            "",
        ]
    )


def _render_registry(record: RegistryRecord) -> str:
    return "\n".join(
        [
            f"# Registry entry {record.id}",
            "",
            _bullets(
                [
                    ("kind", record.kind),
                    ("status", record.status),
                    ("learning_object", record.learning_object_id),
                    ("facets", record.facet_ids),
                    ("occurrence_count", record.occurrence_count),
                ]
            ),
            "",
            "## Statement",
            "",
            record.statement.strip() or "-",
            "",
        ]
    )


def _render_repairs(facet: str, records: list[RepairRecord]) -> str:
    lines = [f"# Repairs on {facet}", ""]
    for record in records:
        lines.append(
            f"- {record.repair_class_id}: operator={record.operator or '-'}; "
            f"hypotheses={', '.join(record.hypothesis_ids) or '-'}; "
            f"cold verifications succeeded={record.cold_successes}, failed={record.cold_failures}"
        )
    lines.append("")
    return "\n".join(lines)


def _render_graph(vault: LoadedVault) -> tuple[str, set[str]]:
    facets: set[str] = set()
    lines = ["# Learning objects", ""]
    for lo in sorted(vault.learning_objects.values(), key=lambda value: value.id):
        lo_facets = [vault.canonical_facet_id(str(value)) for value in learning_object_facet_union(lo)]
        facets.update(lo_facets)
        lines.append(f"## {lo.id}: {lo.title}")
        lines.append(
            _bullets(
                [
                    ("concept", lo.concept),
                    ("prerequisites", lo.prerequisites),
                    ("confusables", lo.confusables),
                    ("facets", lo_facets),
                ]
            )
        )
        lines.append("")
    lines.append("# Concept edges")
    lines.append("")
    for edge in sorted(vault.edges, key=lambda value: (value.relation_type, value.source, value.target)):
        if edge.relation_type in {"prerequisite", "confusable_with"}:
            lines.append(f"- {edge.source} --{edge.relation_type}--> {edge.target}")
    lines.append("")
    return "\n".join(lines), facets


def export_snapshot(
    vault: LoadedVault,
    store: HistoryStore,
    before: AttemptRef,
    destination: Path,
) -> SnapshotManifest:
    """Write the as-of export into an empty ``destination`` directory."""

    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()):
        raise ValueError("snapshot destination must be empty")
    written: dict[str, str] = {}

    def write(relative: str, text: str) -> None:
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        written[relative] = hashlib.sha256(text.encode("utf-8")).hexdigest()

    from learnloop.diagnosis.split.provenance import (
        DiagnosisReads,
        SnapshotEntries,
        attempt_read,
        hypothesis_read,
        registry_read,
        repair_read,
    )

    served: dict[str, DiagnosisReads] = {}
    index_topics: set[str] = set()
    attempts = store.attempts_before(before, None)
    facets: set[str] = set()
    titles = {lo_id: lo.title for lo_id, lo in vault.learning_objects.items()}
    index_lines = [
        "# Learner history (as of the diagnosed attempt, which is NOT included)",
        "",
        f"- export_version: {SNAPSHOT_EXPORT_VERSION}",
        f"- attempts: {len(attempts)}",
        "",
        "## Attempts (chronological)",
        "",
    ]
    for attempt in attempts:
        relative = f"attempts/{_safe(attempt.completed_at)}_{_safe(attempt.attempt_id)}.md"
        write(relative, render_attempt(attempt, titles.get(attempt.learning_object_id, attempt.learning_object_id)))
        served[relative] = attempt_read(attempt)
        index_topics.add(attempt.learning_object_id)
        facets.update(attempt.facets())
        index_lines.append(
            f"- {relative}: {attempt.learning_object_id}; "
            f"{'non_pass' if attempt.non_pass else 'pass'}; "
            f"errors={', '.join(attempt.error_types) or '-'}"
        )
    hypotheses = store.hypotheses_before(before, list(vault.learning_objects))
    registry = store.registry_before(before, None)
    repairs = store.repairs_before(before, None)
    index_lines += ["", "## Hypotheses", ""]
    for record in hypotheses:
        relative = f"hypotheses/{_safe(record.id)}.md"
        write(relative, _render_hypothesis(record))
        served[relative] = hypothesis_read(record)
        index_topics.update(value for value in (record.learning_object_id,) if value)
        facets.update(record.target_facets)
        index_lines.append(f"- {relative}: {record.kind}; {record.lifecycle}; {record.learning_object_id}")
    index_lines += ["", "## Registry", ""]
    for record in registry:
        relative = f"registry/{_safe(record.id)}.md"
        write(relative, _render_registry(record))
        served[relative] = registry_read(record)
        index_topics.update(value for value in (record.learning_object_id,) if value)
        facets.update(record.facet_ids)
        index_lines.append(f"- {relative}: {record.kind}; {record.status}; {record.learning_object_id}")
    by_facet: dict[str, list[RepairRecord]] = {}
    for record in repairs:
        for facet in record.target_facets or ("unscoped",):
            by_facet.setdefault(facet, []).append(record)
    index_lines += ["", "## Repairs", ""]
    for facet, records in sorted(by_facet.items()):
        relative = f"repairs/{_safe(facet)}.md"
        write(relative, _render_repairs(facet, records))
        served[relative] = DiagnosisReads().join(*(repair_read(record) for record in records))
        index_lines.append(f"- {relative}: {len(records)} repair class(es)")
    graph_text, graph_facets = _render_graph(vault)
    facets.update(graph_facets)
    write("graph/learning_objects.md", graph_text)
    served["graph/learning_objects.md"] = DiagnosisReads(topics=tuple(sorted(vault.learning_objects)))
    index_lines += ["", "## Graph", "", "- graph/learning_objects.md", ""]
    write("INDEX.md", "\n".join(index_lines))
    served["INDEX.md"] = DiagnosisReads(topics=tuple(sorted(value for value in index_topics if value)))

    digest = hashlib.sha256()
    for relative in sorted(written):
        digest.update(f"{relative}\0{written[relative]}\n".encode("utf-8"))
    known = KnownIds(
        attempt_ids=frozenset(attempt.attempt_id for attempt in attempts),
        hypothesis_ids=frozenset(record.id for record in hypotheses),
        registry_ids=frozenset(record.id for record in registry),
        learning_object_ids=frozenset(vault.learning_objects),
        facet_ids=frozenset(facets),
        repaired_trace_ids=frozenset(),
    )
    return SnapshotManifest(
        root=destination,
        manifest_hash=digest.hexdigest(),
        files=tuple(sorted(written)),
        known=known,
        as_of_attempt_id=before.attempt_id,
        attempt_count=len(attempts),
        entries=SnapshotEntries(root=destination, entries=served),
    )


@contextmanager
def snapshot_workspace(
    vault: LoadedVault,
    store: HistoryStore,
    before: AttemptRef,
    *,
    parent: Path | None = None,
) -> Iterator[SnapshotManifest]:
    """A fresh export that is always deleted, on success or failure."""

    root = Path(tempfile.mkdtemp(prefix="learnloop-diagnosis-snapshot-", dir=parent))
    try:
        yield export_snapshot(vault, store, before, root / "history")
    finally:
        shutil.rmtree(root, ignore_errors=True)


__all__ = [
    "SNAPSHOT_EXPORT_VERSION",
    "SnapshotManifest",
    "export_snapshot",
    "render_attempt",
    "snapshot_workspace",
]
