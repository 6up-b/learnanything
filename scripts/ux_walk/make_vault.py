"""Synthetic starting points for UX walks: ``empty``, ``fresh`` and ``established``.

Never an owner's vault and never learner data: content is written here, the
history comes from the simulation runner (a synthetic student through the real
attempt pipeline, src/learnloop/sim/runner.py), and sources come only from
``samples/`` (samples/NOTICE). Deterministic for a given ``--anchor`` date:
fixed clocks and seeds throughout. The sidecar runs on the wall clock, so
build the vault on the day of the walk (the default anchor is today, UTC), or
the due and overdue items drift.

- ``empty``: nothing. The walk starts the app on a folder that does not exist
  yet and the app creates the library on first launch, as it does for
  ``~/LearnLoop``.
- ``fresh``: a new library (bootstrap's ``create_vault``, as first launch does)
  with one small web page from samples/ added through the app's own Add (the
  sidecar's ``add_source``): what someone sees minutes after starting.
- ``established``: the basic test vault (tests/helpers.py) grown into a small
  linear algebra course: five learning objects with readable items, three
  goals (an exam in three weeks, an open-ended one, a paused one), four weeks
  of synthetic practice ending yesterday (a student with a planted
  misconception: misses, primed retries after a miss, follow-ups, due and
  overdue items), and a web page from samples/ added through Add with its
  first section marked read. Not built yet: a captured note and a finished
  lesson (docs/reviews/ux-walk-harness.md, what is not covered).

    python scripts/ux_walk/make_vault.py established <dest> [--anchor 2026-11-18]
"""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

SAMPLE_PAGE = ROOT / "samples" / "wikipedia-elevator-paradox.html"
SAMPLE_SECTION = ROOT / "samples" / "understanding-linear-algebra-symmetric-matrices-and-variance.html"
SEED = 20261118
SIM_DAYS = 28

#: (lo id, concept, title, prerequisites, [(item id, prompt, expected answer, difficulty)])
COURSE: list[tuple[str, str, str, list[str], list[tuple[str, str, str, float]]]] = [
    ("lo_vectors_dot", "dot_product", "Dot product", [], [
        ("pi_dot_compute", "Compute the dot product of (1, 2, 3) and (4, -5, 6).", "4 - 10 + 18 = 12.", 0.3),
        ("pi_dot_meaning", "What does a zero dot product say about two non-zero vectors?",
         "They are orthogonal (perpendicular).", 0.35),
    ]),
    ("lo_eigen_basics", "eigenvalues", "Eigenvalues and eigenvectors", ["lo_vectors_dot"], [
        ("pi_eigen_define", "Define an eigenvector of a square matrix A.",
         "A non-zero vector v with Av = λv for some scalar λ (its eigenvalue).", 0.45),
        ("pi_eigen_2x2", "Find the eigenvalues of [[2, 0], [0, 3]].", "2 and 3 (the diagonal entries).", 0.4),
        ("pi_eigen_char", "Write the characteristic equation of a 2×2 matrix A.",
         "det(A - λI) = 0, i.e. λ² - tr(A)λ + det(A) = 0.", 0.6),
    ]),
    ("lo_symmetric", "symmetric_matrices", "Symmetric matrices", ["lo_eigen_basics"], [
        ("pi_sym_spectral", "State the spectral theorem for real symmetric matrices.",
         "A real symmetric matrix has real eigenvalues and an orthonormal basis of eigenvectors: A = QΛQᵀ.", 0.65),
        ("pi_sym_orth", "Why are eigenvectors of a symmetric matrix for distinct eigenvalues orthogonal?",
         "λ₁ v₁·v₂ = (Av₁)·v₂ = v₁·(Av₂) = λ₂ v₁·v₂, so (λ₁ - λ₂) v₁·v₂ = 0.", 0.75),
    ]),
    ("lo_variance", "covariance_matrix", "Variance and the covariance matrix", ["lo_symmetric"], [
        ("pi_var_cov", "What does the (i, j) entry of a covariance matrix measure?",
         "The covariance between variable i and variable j (the variance when i = j).", 0.5),
        ("pi_var_direction", "In which direction is the variance of centred data largest?",
         "Along the eigenvector of the covariance matrix with the largest eigenvalue.", 0.7),
    ]),
]

GOALS = [
    {"id": "goal_midterm", "title": "Midterm: eigenvalues to variance", "status": "active", "priority": 0.9,
     "target_recall": 0.8, "concepts": ["eigenvalues", "symmetric_matrices", "covariance_matrix"], "due_days": 21,
     "intent": "Pass the linear algebra midterm"},
    {"id": "goal_linear_algebra_ml", "title": "Linear algebra for ML", "status": "active", "priority": 0.6,
     "target_recall": 0.8, "concepts": ["singular_value_decomposition", "dot_product"], "due_days": None,
     "intent": None},
    {"id": "goal_proofs", "title": "Proof techniques", "status": "paused", "priority": 0.3,
     "target_recall": 0.7, "concepts": ["symmetric_matrices"], "due_days": None, "intent": None},
]


def iso(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _item(item_id: str, lo_id: str, prompt: str, answer: str, difficulty: float, stamp: str) -> dict:
    return {
        "schema_version": 1, "id": item_id, "learning_object_id": lo_id, "subjects": None,
        "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt", "hinted_attempt", "dont_know"],
        "evidence_facets": ["recall"], "evidence_weights": {"recall": 1.0},
        "prompt": prompt, "expected_answer": answer, "difficulty": difficulty, "tags": [],
        "hints": ["Start from the definition."],
        "hint_policy": {"max_useful_hints": 1, "fsrs_rating_cap_by_hint": {"1": "good"},
                        "mastery_alpha_dampening_by_hint": {"1": 0.5}},
        "grading_rubric": {
            "max_points": 4,
            "criteria": [{"id": "correctness", "points": 3, "description": "States the right result."},
                         {"id": "reasoning", "points": 1, "description": "Says why, in a line."}],
            "fatal_errors": [],
        },
        "provenance": {"origin": "human", "source_refs": []},
        "created_at": stamp, "updated_at": stamp,
    }


def build_course(dest: Path, anchor: date) -> None:
    """The basic test vault plus the course above, goals and a simulated month of practice."""

    from learnloop.sim.profiles import load_profile
    from learnloop.sim.runner import run_simulation
    from learnloop.vault.yaml_io import read_yaml, write_yaml
    from tests.helpers import create_basic_vault

    start = datetime(anchor.year, anchor.month, anchor.day, 9, 0, tzinfo=UTC) - timedelta(days=SIM_DAYS)
    stamp = iso(start - timedelta(days=1))
    paths = create_basic_vault(dest, fresh=True)
    concepts = read_yaml(paths.concepts_path)
    for lo_id, concept, title, prerequisites, items in COURSE:
        concepts["concepts"][concept] = {
            "title": title, "type": "concept", "aliases": [], "description": f"{title}.", "tags": [],
            "created_at": stamp, "updated_at": stamp,
        }
        write_yaml(paths.learning_object_path("linear-algebra", lo_id), {
            "schema_version": 1, "id": lo_id, "title": title, "subjects": ["linear-algebra"], "concept": concept,
            "knowledge_type": "definition", "status": "active", "contradicts": None, "summary": f"{title}.",
            "prerequisites": prerequisites, "confusables": [], "difficulty_prior": 0.5, "tags": [],
            "provenance": {"origin": "human", "source_refs": []}, "created_at": stamp, "updated_at": stamp,
        })
        for item_id, prompt, answer, difficulty in items:
            write_yaml(paths.practice_item_path("linear-algebra", item_id),
                       _item(item_id, lo_id, prompt, answer, difficulty, stamp))
    write_yaml(paths.concepts_path, concepts)
    goals = []
    for goal in GOALS:
        due = None if goal["due_days"] is None else iso(start + timedelta(days=SIM_DAYS + goal["due_days"]))
        goals.append({
            "id": goal["id"], "title": goal["title"], "intent_sentence": goal["intent"], "creation_source": "learner",
            "status": goal["status"], "priority": goal["priority"], "target_recall": goal["target_recall"],
            "facet_scope": {"concepts": goal["concepts"]}, "due_at": due, "created_at": stamp, "updated_at": stamp,
        })
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": goals})
    run_simulation(paths.root, load_profile("intermediate_with_misconception"), days=SIM_DAYS, items_per_day=4,
                   seed=SEED, start=start, primed_retries=True)


# -- the app's own path, through a bridge (no browser) ---------------------------------------------


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class AppSession:
    """A bridge on the vault (fake models), driven by its invoke endpoint: what the shell would send."""

    def __init__(self, walk_root: Path, vault: Path, create_if_missing: bool):
        self.port = _free_port()
        self.walk_root = walk_root
        command = [sys.executable, str(Path(__file__).with_name("bridge.py")), "--walk-root", str(walk_root),
                   "--vault", str(vault), "--port", str(self.port)]
        if create_if_missing:
            command.append("--create-if-missing")
        (walk_root / "analyst").mkdir(parents=True, exist_ok=True)
        self.output = (walk_root / "analyst" / "make_vault_bridge.out").open("ab")
        self.process = subprocess.Popen(command, stdout=self.output, stderr=self.output)
        ready = walk_root / "run" / "bridge.ready"
        deadline = time.monotonic() + 180
        while not ready.exists():
            if self.process.poll() is not None or time.monotonic() > deadline:
                raise SystemExit(f"the bridge did not start (see {walk_root / 'analyst'})")
            time.sleep(0.3)

    def invoke(self, command: str, **args: Any) -> Any:
        body = json.dumps({"command": command, "args": args}).encode("utf-8")
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}/__bridge/invoke", data=body,
                                         method="POST", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=900) as response:
            envelope = json.loads(response.read())
        if not envelope["ok"]:
            raise RuntimeError(f"{command}: {envelope['error']}")
        return envelope["result"]

    def close(self) -> None:
        self.process.terminate()
        try:
            self.process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.process.kill()
        self.output.close()
        (self.walk_root / "run" / "bridge.ready").unlink(missing_ok=True)
        # The walk's own bridge log starts empty: the driver reads it from the top for each step.
        log = self.walk_root / "analyst" / "bridge.jsonl"
        if log.exists():
            log.replace(self.walk_root / "analyst" / "make_vault_bridge.jsonl")


def add_and_open(app: AppSession, source: Path) -> dict:
    """Add a sample through the app's Add and wait until its reading is ready (or failed)."""

    added = app.invoke("add_source", input={"sources": [str(source)]})
    deadline = time.monotonic() + 300
    books: list[dict] = []
    while time.monotonic() < deadline:
        library = app.invoke("get_source_library")
        books = [book for book in library.get("sources") or [] if isinstance(book, dict)]
        if books and not library.get("pending") and all(
                book.get("extractionStatus") in ("completed", "failed") for book in books):
            break
        time.sleep(1.0)
    return {"added": added.get("opened"), "library": [
        {key: book.get(key) for key in ("sourceId", "title", "readiness", "extractionStatus")} for book in books]}


def read_part_way(app: AppSession, source_id: str) -> dict:
    """Mark the first section of the reading as read, as a reading session would."""

    plan = app.invoke("reader_guide_plan", input={"extractionId": source_id})
    sections = plan.get("sections") or []
    extraction = plan.get("extractionId") or source_id
    done: dict[str, Any] = {"sections": len(sections)}
    if sections:
        done["marked"] = app.invoke("reader_mark_section_progress", input={
            "extractionId": extraction, "sectionId": sections[0]["id"], "completed": True})
    return done


def make(name: str, dest: Path, anchor: date) -> dict:
    if dest.exists() and any(dest.iterdir()):
        raise SystemExit(f"{dest} is not empty; a walk vault is always built fresh")
    walk_root = dest.parent
    report: dict[str, Any] = {"name": name, "vault": str(dest), "anchor": anchor.isoformat()}
    if name == "empty":
        report["note"] = "nothing built: start the walk with --create-if-missing so first launch creates it"
        return report
    if name == "fresh":
        app = AppSession(walk_root, dest, create_if_missing=True)
        try:
            report["source"] = add_and_open(app, SAMPLE_PAGE)
        finally:
            app.close()
        return report
    if name == "established":
        build_course(dest, anchor)
        app = AppSession(walk_root, dest, create_if_missing=False)
        try:
            source = add_and_open(app, SAMPLE_SECTION)
            report["source"] = source
            if source["library"]:
                report["reading"] = read_part_way(app, source["library"][0]["sourceId"])
        finally:
            app.close()
        return report
    raise SystemExit(f"unknown starting point {name!r}: empty, fresh or established")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("name", choices=("empty", "fresh", "established"))
    parser.add_argument("dest", help="the vault folder to create, inside a walk directory")
    parser.add_argument("--anchor", help="the walk's date (YYYY-MM-DD, default today in UTC)")
    args = parser.parse_args(argv)
    anchor = date.fromisoformat(args.anchor) if args.anchor else datetime.now(UTC).date()
    report = make(args.name, Path(args.dest).resolve(), anchor)
    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
