"""`learnloop ai compare`: the same real work on several subscription profiles, side by side.

Owner direction (2026-10-15, the ChatGPT plan as a peer of Codex): before a
route moves from Codex to the ChatGPT plan, the owner runs one batch of real
work through both and reads the differences. The command is owner-run (the
plan's sign-in is interactive and the owner's) on a backup-API copy of a
vault, never a working vault.

The work, identical for every profile:

* **grading**: a few attempts blind-graded with the learner-blind grader's
  context and wire model (:func:`~learnloop.attempts.blind_grading.blind_grading_context`
  without the C2 verifier observations, so every profile reads the same
  prompt), then validated. The rubric and statement are the ones production
  regrading reads for that answer (:func:`_grading_contract`: a
  method-explicit answer's frozen assessment contract, else the item as it
  is now).
* **one diagnosis**, in the ``snapshot`` history mode by default
  (:func:`~learnloop.diagnosis.split.diagnoser.run_diagnosis`): Codex reads the
  as-of export in its sandbox; the ChatGPT plan is served it by LearnLoop
  (``learnloop.ai.chatgpt_plan.workspace``), so its record of what it read is
  exact.
* **one structured generation**: a teach-back authoring draft for one graded
  item (:func:`~learnloop.tutor.teach_back.request_teach_back_authoring`),
  judged by the tutor's own validator.

Nothing serving is written. Each verdict (a grade, a diagnosis, a draft's
validity) appends to the vault copy's ``judgment_ledger`` under the
comparison's own tasks (``ai_compare_*``, right side the profile), which no
serving reader names, so they never become evidence or certification; the
report links each call to its judgment and its receipts.

The report holds ids, numbers and locally written explanations only (no
learner text, no model or provider prose: a failure keeps its class, code,
HTTP status, parameter name, request and receipt ids, never the provider's
message, which may quote the request): per call its validity, latency,
physical requests and tokens; per profile its totals and plan-allowance
behaviour (the ChatGPT plan's pause state before and after, usage-limit
errors); per pair of profiles their agreement (grading scores and criteria,
diagnosis causal classes and cited attempts, generation validity).

Spend (handoffs §0 rule 6): only subscription profiles run (Codex, the
ChatGPT plan: billing ``subscription``, Slice A plan §5 rule 6). Each profile
has a :class:`~learnloop.ai.spend.SpendBudget` (``subscription=True``) whose
call cap is the plan; every call is admitted by it before it is sent (so its
root receipt records the caps, ``cost_basis = estimated_only`` and no
physical-request bound) and reconciled with the usage the transport
reported. The dry run estimates every planned call (input, the snapshot
export a diagnosis may read, and the output budget) in both output formats.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from itertools import combinations
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import statistics
import subprocess
import time
from typing import Any, Iterator

import tomlkit

from learnloop.ai.chatgpt_plan.session import MANAGE_USAGE_URL, PlanSession
from learnloop.ai.errors import AIInterrupted, AIProviderUnavailable
from learnloop.ai.execution import annotate_calls, content_key, tee_model_calls
from learnloop.ai.output_budget import output_budget
from learnloop.ai.routing import (
    client_for_provider,
    is_generation_profile,
    runtime_for_provider,
    serves_read_only_workspace,
)
from learnloop.ai.spend import (
    ESTIMATED_ONLY,
    SpendBudget,
    SpendCaps,
    SpendEstimate,
    SpendLimitExceeded,
    is_subscription_transport,
    subscription_usage_estimate,
)
from learnloop.attempts.attempts import attempt_graded_contract, regrade_reads_contract
from learnloop.attempts.blind_grading import (
    BlindGradingContext,
    blind_grading_context,
    blind_grading_context_hash,
    blind_grading_prompt,
    blind_prompt_version,
    request_blind_grading_proposal,
    validate_blind_grading_proposal,
)
from learnloop.attempts.grading import GradingValidationError, resolved_rubric
from learnloop.config.loader import load_config
from learnloop.db.copies import backup_database, copy_tree_with_databases
from learnloop.db.stores.judgments import append_judgment
from learnloop.diagnosis.split.context import assemble_diagnosis_context
from learnloop.diagnosis.split.contract import diagnosis_prompt
from learnloop.diagnosis.split.diagnoser import run_diagnosis
from learnloop.diagnosis.split.live import (
    current_attempt_for,
    joint_grade_record,
    live_history_store,
    needs_diagnosis,
    settings_from_config,
)
from learnloop.diagnosis.split.snapshot import snapshot_workspace
from learnloop.ids import new_ulid
from learnloop.tutor.ai_contracts import TEACH_BACK_AUTHORING_PROMPT_VERSION, teach_back_authoring_prompt
from learnloop.tutor.teach_back import (
    TeachBackError,
    request_teach_back_authoring,
    teach_back_authoring_context,
    validate_teach_back_authoring,
)
from learnloop.vault.models import LoadedVault, PracticeItem, Rubric
from learnloop.vault.paths import VaultPaths

#: 2: failures as codes (no provider prose), spend per call and profile,
#: judgment ids, the database-relocating copy.
COMPARE_VERSION = 2
DEFAULT_GRADING_ATTEMPTS = 3
DIAGNOSIS_MODES = ("snapshot", "full", "exact")
#: Prompt-side token estimate: ~4 bytes of UTF-8 per token (the diagnoser's own rounding).
_BYTES_PER_TOKEN = 4
#: Attempt types the blind grader never grades as ordinary answers.
_SKIPPED_ATTEMPT_TYPES = frozenset({"teach_back", "dont_know"})
#: The routes whose output budget each call kind runs under (``ai.output_budget``).
_ROUTES = {"grading": "grading", "diagnosis": "diagnosis", "generation": "teach_back"}
#: ``judgment_ledger`` tasks of the comparison's verdicts. No serving reader
#: names them: they are the comparison's record, never evidence or certification.
GRADING_TASK = "ai_compare_grading"
DIAGNOSIS_TASK = "ai_compare_diagnosis"
GENERATION_TASK = "ai_compare_generation"
#: The right side of every comparison judgment: the profile that answered.
PROFILE_KIND = "ai_profile"


class CompareRefused(ValueError):
    """The comparison cannot run as asked; ``code`` names why (for ``--json``)."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class CompareRequest:
    profiles: tuple[str, ...]
    grading_attempts: int = DEFAULT_GRADING_ATTEMPTS
    #: Explicit grading targets (replace the automatic choice).
    attempt_ids: tuple[str, ...] = ()
    diagnosis: bool = True
    diagnosis_attempt_id: str | None = None
    diagnosis_mode: str = "snapshot"
    generation: bool = True
    #: The whole-operation deadline of each call (a workspace turn's rounds included).
    timeout_seconds: int = 900


@dataclass
class Targets:
    grading: list[str] = field(default_factory=list)
    diagnosis: str | None = None
    generation_item: str | None = None
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {"grading": list(self.grading), "diagnosis": self.diagnosis,
                "generation_item": self.generation_item, "notes": list(self.notes)}


# -- safety ------------------------------------------------------------------------------


def _inside(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def database_location_reason(vault: LoadedVault) -> str | None:
    """Why this vault's database must not be compared on (it lies outside the vault), or None.

    A configured ``storage.sqlite_path`` outside the vault directory may be
    another vault's database (a hand-made copy keeps the original's absolute
    path), so the comparison refuses it before opening anything. A copy made
    with ``--copy-from`` always holds its database inside.
    """

    database = VaultPaths(vault.root, vault.config).sqlite_path.resolve()
    root = Path(vault.root).resolve()
    if _inside(database, root):
        return None
    return (f"{vault.root}'s database ({database}) lies outside the vault, so it may be another vault's. "
            f"Compare on a backup-API copy: learnloop ai compare --copy-from {vault.root} "
            "--vault fixtures-local/<name> ...")


def tracked_database_reason(vault: LoadedVault, *, fresh_copy: bool = False) -> str | None:
    """Why this vault must not be compared on, or None.

    A vault whose database git tracks is a working vault (the owner's
    ``fixtures/linear_algebra``, ``probability`` and ``arxiv_v2`` are): the
    comparison writes receipts and judgments and runs migrations, so it runs
    on a backup-API copy instead (``--copy-from``).

    The check fails closed: only git's own "untracked" (exit 1) or "not a git
    repository" lets the vault through. A check that cannot finish (a timeout,
    an OS error, any other git failure such as dubious ownership) refuses, and
    so does a machine without git, since the vault it could not classify may
    be a working one; ``fresh_copy`` (the copy ``--copy-from`` just made in
    this run) is the one exception there.
    """

    database = VaultPaths(vault.root, vault.config).sqlite_path
    if not database.exists():
        return None
    copy_hint = (f"Compare on a backup-API copy: learnloop ai compare --copy-from {vault.root} "
                 "--vault fixtures-local/<name> ...")
    git = shutil.which("git")
    if git is None:
        if fresh_copy:
            return None
        return (f"git is not available to tell whether {vault.root} is a working vault, so it is treated as "
                f"one. {copy_hint}")
    try:
        result = subprocess.run(
            [git, "-C", str(database.parent), "ls-files", "--error-unmatch", "--", database.name],
            capture_output=True, text=True, timeout=20, check=False,
            # git's messages in English, so "not a git repository" can be matched.
            env={**os.environ, "LC_ALL": "C", "LANGUAGE": "C"},
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return (f"Could not check whether git tracks {database} ({type(exc).__name__}), so {vault.root} is "
                f"treated as a working vault. {copy_hint}")
    if result.returncode == 0:
        return f"{vault.root} is a working vault (git tracks {database.name}). {copy_hint}"
    if result.returncode == 1 or "not a git repository" in (result.stderr or "").lower():
        return None
    return (f"Could not tell whether git tracks {database} (git exited {result.returncode}), so {vault.root} "
            f"is treated as a working vault. {copy_hint}")


def _configured_database(root: Path, *, flag: str) -> str:
    """The vault's ``storage.sqlite_path`` as written (read without loading the environment)."""

    try:
        return load_config(root / "learnloop.toml", load_environment=False).storage.sqlite_path
    except Exception as exc:  # noqa: BLE001 - any unreadable configuration refuses the copy
        raise CompareRefused(f"{flag} {root}: its learnloop.toml could not be read ({type(exc).__name__}).",
                             code="copy_config_unreadable") from None


def _relocate_database(destination: Path, relative: Path) -> None:
    """Point the copy's ``storage.sqlite_path`` at its own database (relative to the copy)."""

    path = destination / "learnloop.toml"
    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    if "storage" not in document:
        document["storage"] = tomlkit.table()
    document["storage"]["sqlite_path"] = relative.as_posix()  # type: ignore[index]
    path.write_text(tomlkit.dumps(document), encoding="utf-8")


def copy_vault(source: Path, destination: Path) -> list[Path]:
    """A backup-API copy of ``source`` at ``destination`` (which must not exist yet).

    The source's configured database is resolved first (Codex review F1): a
    database named other than ``*.sqlite`` is copied through the backup API
    too (never byte-copied with its ``-wal``), and one configured outside the
    source tree (an absolute or ``..`` path) is backed up into the copy. Either
    way the copy's configuration then names its own database, and the copy
    is refused unless its database lies inside it.
    """

    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not source.is_dir():
        raise CompareRefused(f"--copy-from {source} is not a directory.", code="copy_source_missing")
    if destination.exists():
        raise CompareRefused(f"--vault {destination} already exists; --copy-from needs a new directory.",
                             code="copy_destination_exists")
    if source == destination or source in destination.parents:
        raise CompareRefused("--vault must lie outside the vault it copies.", code="copy_inside_source")
    configured = _configured_database(source, flag="--copy-from")
    # Lexical, so a database the tree holds through a symlink is the tree's.
    database = Path(os.path.normpath(source / configured))
    internal = _inside(database, source)
    if not internal and (source / database.name).exists():
        raise CompareRefused(
            f"--copy-from {source}: its database lies outside it and a file named {database.name} lies inside it; "
            "the copy cannot hold both.", code="copy_database_collision")
    destination.parent.mkdir(parents=True, exist_ok=True)
    copied = copy_tree_with_databases(source, destination, database_names={database.name})
    if internal:
        relative = database.relative_to(source)
        # An absolute path, or one that leaves the tree and comes back by
        # name, would still name the source's database from the copy.
        if Path(os.path.normpath(destination / configured)) != destination / relative:
            _relocate_database(destination, relative)
    else:
        if database.exists():
            target = destination / database.name
            backup_database(database, target)
            copied.append(target)
        _relocate_database(destination, Path(database.name))
    placed = (destination / _configured_database(destination, flag="--vault")).resolve()
    if not _inside(placed, destination):  # pragma: no cover - the relocation above always places it inside
        raise CompareRefused(f"The copy's database ({placed}) lies outside {destination}.",
                             code="copy_database_outside")
    return copied


def check_profiles(vault: LoadedVault, request: CompareRequest) -> list[dict[str, Any]]:
    """Each named profile's identity and readiness; refuses a profile that cannot run here."""

    config = vault.config
    if not request.profiles:
        raise CompareRefused("Name at least one profile with --profiles.", code="no_profiles")
    if request.diagnosis_mode not in DIAGNOSIS_MODES:
        raise CompareRefused(f"--diagnosis-mode must be one of {', '.join(DIAGNOSIS_MODES)}.", code="bad_mode")
    rows = []
    for name in request.profiles:
        profile = config.ai.providers.get(name)
        if profile is None:
            raise CompareRefused(f"No provider profile named {name!r} in this vault.", code="unknown_profile")
        if not is_generation_profile(config, name):
            raise CompareRefused(f"{name!r} is an embedding or decision-model profile; it cannot grade.",
                                 code="not_generation")
        if not is_subscription_transport(profile=profile):
            raise CompareRefused(
                f"{name!r} is metered ({profile.type}); the comparison runs subscription profiles only "
                "(Codex, chatgpt_plan).", code="metered_profile")
        runtime = runtime_for_provider(vault.root, config, name)
        rows.append({
            "provider": name, "type": profile.type, "model": profile.model, "billing": "subscription",
            "ready": runtime.ready, "message": runtime.message,
            "read_only_workspace": serves_read_only_workspace(config, name),
        })
    return rows


# -- targets -----------------------------------------------------------------------------


def _record_for(vault: LoadedVault, repository: Any, attempt_id: str) -> dict[str, Any] | None:
    stored = repository.latest_blind_grade_record(attempt_id)
    if stored is not None:
        return dict(stored.get("record") or {})
    row = repository.fetch_practice_attempt(attempt_id)
    return joint_grade_record(vault, repository, row) if row is not None else None


def select_targets(vault: LoadedVault, repository: Any, request: CompareRequest, *, store: Any = None) -> Targets:
    """The attempts to grade, the attempt to diagnose and the item to generate from.

    Deterministic: the most recent non-pass and pass attempts first, then the
    most recent others; the diagnosis is the latest non-pass attempt that
    needs one and has history before it.
    """

    store = store if store is not None else live_history_store(vault, repository)
    attempts = store.all_attempts()
    by_id = {attempt.attempt_id: attempt for attempt in attempts}
    targets = Targets()

    def gradeable(attempt: Any) -> bool:
        return (attempt.practice_item_id in vault.practice_items and bool(attempt.learner_answer_md.strip())
                and attempt.attempt_type not in _SKIPPED_ATTEMPT_TYPES)

    if request.attempt_ids:
        for attempt_id in request.attempt_ids:
            attempt = by_id.get(attempt_id)
            if attempt is None or not gradeable(attempt):
                raise CompareRefused(f"Attempt {attempt_id!r} is not a gradeable attempt in this vault.",
                                     code="unknown_attempt")
        targets.grading = list(dict.fromkeys(request.attempt_ids))
    elif request.grading_attempts > 0:
        recent = [attempt for attempt in reversed(attempts) if gradeable(attempt)]
        chosen: list[str] = []
        for wanted in (True, False):  # the latest non-pass, then the latest pass
            pick = next((a.attempt_id for a in recent if a.non_pass == wanted), None)
            if pick is not None and len(chosen) < request.grading_attempts:
                chosen.append(pick)
        for attempt in recent:
            if len(chosen) >= request.grading_attempts:
                break
            if attempt.attempt_id not in chosen:
                chosen.append(attempt.attempt_id)
        order = {attempt.attempt_id: index for index, attempt in enumerate(attempts)}
        targets.grading = sorted(chosen, key=order.__getitem__)
        if len(chosen) < request.grading_attempts:
            targets.notes.append(f"only {len(chosen)} gradeable attempts in this vault")

    if request.diagnosis:
        if request.diagnosis_attempt_id:
            if request.diagnosis_attempt_id not in by_id:
                raise CompareRefused(f"Attempt {request.diagnosis_attempt_id!r} is not in this vault.",
                                     code="unknown_attempt")
            targets.diagnosis = request.diagnosis_attempt_id
        else:
            for index in range(len(attempts) - 1, 0, -1):
                attempt = attempts[index]
                if not (attempt.non_pass and gradeable(attempt)):
                    continue
                record = _record_for(vault, repository, attempt.attempt_id)
                if record and needs_diagnosis(record):
                    targets.diagnosis = attempt.attempt_id
                    break
            if targets.diagnosis is None:
                targets.notes.append("no non-pass attempt with history needs a diagnosis; diagnosis skipped")

    if request.generation:
        for attempt_id in [*targets.grading, *([targets.diagnosis] if targets.diagnosis else [])]:
            item = vault.practice_items.get(by_id[attempt_id].practice_item_id)
            if item is not None and item.learning_object_id in vault.learning_objects:
                targets.generation_item = item.id
                break
        if targets.generation_item is None:
            item = next((item for item in sorted(vault.practice_items.values(), key=lambda value: value.id)
                         if item.status == "active" and item.learning_object_id in vault.learning_objects), None)
            targets.generation_item = item.id if item is not None else None
        if targets.generation_item is None:
            targets.notes.append("no active item with a learning object; generation skipped")
    return targets


# -- the inputs each call reads (shared by the estimate and the run) ---------------------


def _tokens(text: str) -> int:
    return (len(text.encode("utf-8")) + _BYTES_PER_TOKEN - 1) // _BYTES_PER_TOKEN


def _grading_contract(vault: LoadedVault, repository: Any, item: PracticeItem,
                      attempt_id: str) -> tuple[Rubric, dict[str, Any] | None]:
    """The rubric and assessment contract production regrading reads for this answer (Codex review F4).

    :func:`~learnloop.attempts.attempts.regrade_reads_contract` decides, as in
    :func:`~learnloop.attempts.regrade.regrade_attempt`: a method-explicit
    answer is graded under the statement, rubric and method its contract
    froze; every other answer reads the item as it is now.
    """

    graded = attempt_graded_contract(repository, attempt_id)
    if regrade_reads_contract(vault, item, graded):
        assert graded is not None
        return graded.rubric(), graded.contract
    return resolved_rubric(vault, item), None


def _grading_context(vault: LoadedVault, repository: Any,
                     attempt: Any) -> tuple[PracticeItem, Rubric, BlindGradingContext]:
    item = vault.practice_items[attempt.practice_item_id]
    rubric, contract = _grading_contract(vault, repository, item, attempt.attempt_id)
    context = blind_grading_context(vault, item, attempt_id=attempt.attempt_id,
                                    learner_answer_md=attempt.learner_answer_md,
                                    rubric=rubric, assessment_contract=contract)
    return item, rubric, context


def _diagnosis_inputs(vault: LoadedVault, repository: Any, store: Any, attempt_id: str,
                      mode: str) -> dict[str, Any]:
    """The diagnosis's inline prompt size and, in snapshot mode, its export's (no model call)."""

    row = repository.fetch_practice_attempt(attempt_id)
    record = _record_for(vault, repository, attempt_id)
    current = current_attempt_for(vault, row, record or {}, repository) if row is not None else None
    if current is None:
        return {"input_tokens": None, "note": "item_missing"}
    settings = settings_from_config(vault)
    if mode == "snapshot":
        with snapshot_workspace(vault, store, current.ref()) as manifest:
            assembled = assemble_diagnosis_context(vault, store, current, settings, mode="snapshot",
                                                   snapshot_manifest=manifest.as_context_note())
            export_bytes = sum((manifest.root / name).stat().st_size for name in manifest.files)
            files = manifest.file_count
        return {"input_tokens": _tokens(diagnosis_prompt(assembled)),
                "workspace_tokens": (export_bytes + _BYTES_PER_TOKEN - 1) // _BYTES_PER_TOKEN,
                "workspace_files": files}
    assembled = assemble_diagnosis_context(vault, store, current, settings, mode=mode)  # type: ignore[arg-type]
    return {"input_tokens": _tokens(diagnosis_prompt(assembled))}


def _generation_inputs(vault: LoadedVault, item_id: str) -> tuple[Any, list[dict[str, Any]], str]:
    item = vault.practice_items[item_id]
    lo = vault.learning_objects[item.learning_object_id]
    # The teach-back authoring context exactly as the tutor builds it.
    context, criteria = teach_back_authoring_context(vault, item, lo, quest_sentence=None)
    return context, criteria, teach_back_authoring_prompt(context)


# -- the work ----------------------------------------------------------------------------


#: A code, parameter or request id kept in the report: an identifier, never prose.
_IDENTIFIER = re.compile(r"^[A-Za-z0-9_.:\[\]/-]{1,96}$")


def _identifier(value: Any) -> str | None:
    return value if isinstance(value, str) and _IDENTIFIER.match(value) else None


class _Meter:
    """The model calls one comparison call made, from the receipts' own events."""

    def __init__(self) -> None:
        self.starts: dict[str, dict[str, Any]] = {}
        self.finishes: list[dict[str, Any]] = []

    def __call__(self, action: str, event: dict[str, Any]) -> None:
        if action == "start":
            self.starts[str(event.get("id"))] = dict(event)
        elif action == "finish":
            self.finishes.append(dict(event))

    def roots(self) -> list[str]:
        """The operation receipts (in the vault copy) this call wrote."""

        return [call_id for call_id, event in self.starts.items() if not event.get("parent_call_id")]

    def _usage(self, event: Mapping[str, Any]) -> dict[str, Any]:
        try:
            usage = json.loads(event.get("usage_json") or "{}")
        except (TypeError, ValueError):
            return {}
        return usage if isinstance(usage, dict) else {}

    def request_ids(self) -> list[str]:
        ids = []
        for event in self.finishes:
            plan = self._usage(event).get("chatgpt_plan")
            value = _identifier(plan.get("request_id")) if isinstance(plan, dict) else None
            if value:
                ids.append(value)
        return list(dict.fromkeys(ids))

    def failure_codes(self) -> list[str]:
        codes = [_identifier(event.get("finish_reason")) for event in self.finishes
                 if event.get("status") not in (None, "completed")]
        return list(dict.fromkeys(code for code in codes if code))

    def summary(self) -> dict[str, Any]:
        physical = [event for event in self.finishes
                    if (self.starts.get(str(event.get("id"))) or {}).get("parent_call_id")]
        if not physical:
            # No child receipt: a transport that reports on the operation itself
            # counts once if it reported usage; a local refusal sent nothing.
            physical = [event for event in self.finishes
                        if isinstance(event.get("input_tokens"), int) or isinstance(event.get("output_tokens"), int)]
        tokens: dict[str, int | None] = {}
        for key in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens"):
            values = [event.get(key) for event in physical if isinstance(event.get(key), int)]
            tokens[key] = sum(values) if values else None
        rounds = 0
        served: list[str] = []
        for event in physical:
            workspace = (self._usage(event).get("chatgpt_plan") or {}).get("workspace")
            if isinstance(workspace, dict):
                rounds = max(rounds, int(workspace.get("round") or 0))
                served.extend(str(path) for path in workspace.get("carries") or workspace.get("served") or [])
        return {
            "physical_requests": len(physical),
            "resolved_models": sorted({str(event["resolved_model"]) for event in physical
                                       if event.get("resolved_model")}),
            **tokens,
            **({"workspace_rounds": rounds} if rounds else {}),
            **({"workspace_served_files": len(dict.fromkeys(served))} if served else {}),
        }


@contextmanager
def _measured() -> Iterator[_Meter]:
    meter = _Meter()
    with tee_model_calls(meter):
        yield meter


def _error_class(exc: BaseException) -> str:
    return type(exc).__name__


#: Locally written explanations, by failure class. The provider's own message
#: is never copied into a report: it may quote the request, the learner's
#: answer included (Codex review F3).
_HINTS = {
    "ChatGPTPlanUsageExhausted": ("The ChatGPT plan reported its usage limit; LearnLoop pauses plan requests "
                                  f"for a while. Manage usage: {MANAGE_USAGE_URL}"),
    "ChatGPTPlanNotEligible": "ChatGPT plan usage is unavailable for this account, workspace or policy.",
    "ChatGPTSignInRequired": "Not signed in with ChatGPT on this machine: learnloop ai signin chatgpt.",
    "ChatGPTPlanUnauthorized": ("The ChatGPT plan did not accept the access token; if this repeats, sign in "
                                "again: learnloop ai signin chatgpt."),
    "ChatGPTPlanTransient": "A network, server or availability failure, retried within the deadline.",
    "ChatGPTPlanRequestRejected": "The ChatGPT plan rejected this request's shape (see its code and param).",
    "AITurnTimeout": "The call ran past its deadline (--timeout).",
    "AIOutputTruncated": "The answer ran out of its output budget; it was not accepted.",
    "AIInvalidOutput": "The model refused or answered outside the call's schema; nothing was accepted.",
    "GradingValidationError": "The grade failed LearnLoop's grading validation.",
    "TeachBackError": "The draft failed the tutor's own teach-back authoring checks.",
    "provider_lacks_read_only_workspace": "A snapshot diagnosis needs a profile that serves a read-only workspace.",
}
_REMEDIES = {
    "workspace_inline": ("The route rejected the read-only workspace's function calls; set "
                         'workspace_mode = "inline" on [ai.providers.{provider}].'),
    "json_object": 'The route rejected structured output; set response_format = "json_object" on '
                   "[ai.providers.{provider}].",
}
_DEFAULT_HINT = ("The provider's message is not kept in this report; `learnloop ai latency --vault <vault> "
                 "--provider {provider}` shows it.")


def _failure_record(error: str | None, exc: BaseException | None, meter: _Meter, *, provider: str) -> dict[str, Any]:
    """A failure as codes and ids plus a local explanation, never the provider's prose."""

    details = getattr(exc, "provider_error", None)
    details = details if isinstance(details, dict) else {}
    status = details.get("status")
    request_ids = meter.request_ids()
    own = _identifier(details.get("request_id"))
    if own and own not in request_ids:
        request_ids.append(own)
    remedy = details.get("remedy")
    if remedy in _REMEDIES:
        hint = _REMEDIES[remedy].format(provider=provider)
    else:
        hint = _HINTS.get(str(error or ""), _DEFAULT_HINT.format(provider=provider))
    record = {
        "code": _identifier(details.get("code")) or next(iter(meter.failure_codes()), None),
        "http_status": status if isinstance(status, int) and not isinstance(status, bool) else None,
        "param": _identifier(details.get("param")),
        "request_ids": request_ids,
        "hint": hint,
    }
    return {key: value for key, value in record.items() if value not in (None, [])}


def _grade(vault: LoadedVault, repository: Any, client: Any, attempt: Any) -> dict[str, Any]:
    item, rubric, context = _grading_context(vault, repository, attempt)
    proposal = request_blind_grading_proposal(client, context)
    judgment = {"task": GRADING_TASK, "left_kind": "attempt", "left_id": attempt.attempt_id, "judge": "llm",
                "prompt_version": blind_prompt_version(context), "input_hash": blind_grading_context_hash(context)}
    try:
        validated = validate_blind_grading_proposal(
            proposal, attempt_id=attempt.attempt_id, item=item, vault=vault,
            learner_answer_md=attempt.learner_answer_md, rubric=rubric,
        )
    except (GradingValidationError, ValueError) as exc:
        return {"parsed": True, "valid": False, "error": _error_class(exc),
                "_judgment": {**judgment, "verdict": {"valid": False, "error": _error_class(exc)}}}
    record = validated.as_record()
    criteria = {str(row["criterion_id"]): row.get("points_awarded") for row in record.get("criteria") or []}
    score, maximum = record.get("rubric_score"), record.get("max_points")
    return {
        "parsed": True, "valid": True,
        "rubric_score": score, "max_points": maximum, "criteria": criteria,
        "fatal_errors": len(record.get("fatal_errors") or []),
        "error_attributions": len(record.get("error_attributions") or []),
        "grader_confidence": record.get("grader_confidence"),
        "_judgment": {**judgment, "verdict": {"valid": True, "rubric_score": score, "max_points": maximum,
                                              "criteria": criteria},
                      "score": float(score) / float(maximum) if score is not None and maximum else None},
    }


def _diagnose(vault: LoadedVault, repository: Any, client: Any, attempt_id: str, *, store: Any,
              mode: str) -> dict[str, Any]:
    row = repository.fetch_practice_attempt(attempt_id)
    record = _record_for(vault, repository, attempt_id)
    current = current_attempt_for(vault, row, record or {}, repository) if row is not None else None
    if current is None:
        return {"parsed": False, "valid": False, "error": "item_missing"}
    item = vault.practice_items[str(row["practice_item_id"])]
    outcome = run_diagnosis(client, vault=vault, item=item, rubric=resolved_rubric(vault, item), store=store,
                            current=current, settings=settings_from_config(vault), mode=mode)  # type: ignore[arg-type]
    proposal = outcome.proposal or {}
    snapshot = (outcome.receipt or {}).get("snapshot") or {}
    opened = snapshot.get("opened")
    result: dict[str, Any] = {
        "status": outcome.status,
        "parsed": outcome.proposal is not None,
        "valid": outcome.status == "completed",
        "error": outcome.error,
        "unknown_id_count": outcome.unknown_id_count,
        "evidence_attempt_ids": list(proposal.get("evidence_attempt_ids") or []),
        "causal_classes": sorted(str(event.get("causal_class")) for event in proposal.get("event_diagnoses") or []),
        "event_diagnoses": len(proposal.get("event_diagnoses") or []),
        "abstentions": len(proposal.get("abstentions") or []),
    }
    if mode == "snapshot":
        result["snapshot"] = {
            "file_count": snapshot.get("file_count"),
            "opened_reported": opened is not None,
            "opened_count": len(opened) if isinstance(opened, list) else None,
        }
    if outcome.status in ("completed", "validation_rejected") and outcome.context_hash:
        result["_judgment"] = {
            "task": DIAGNOSIS_TASK, "left_kind": "attempt", "left_id": attempt_id, "judge": "diagnoser",
            "prompt_version": outcome.prompt_version, "input_hash": outcome.context_hash,
            "verdict": {key: result[key] for key in ("status", "causal_classes", "evidence_attempt_ids",
                                                     "event_diagnoses", "abstentions", "unknown_id_count")},
        }
    return result


def _generate(vault: LoadedVault, client: Any, item_id: str) -> dict[str, Any]:
    item = vault.practice_items[item_id]
    lo = vault.learning_objects[item.learning_object_id]
    context, source_criteria, prompt = _generation_inputs(vault, item_id)
    draft = request_teach_back_authoring(client, context)
    result: dict[str, Any] = {"parsed": True, "core_criteria": len(draft.core_criteria)}
    try:
        # The tutor's own validator (Codex review F2): what it rejects, the
        # tutor discards for its deterministic fallback.
        validate_teach_back_authoring(draft, source_criteria=source_criteria, source_item=item,
                                      learning_object=lo, quest_sentence=context.quest_sentence)
    except TeachBackError as exc:
        # The validator's messages are fixed local sentences (no draft text).
        result.update(valid=False, error=_error_class(exc), rejection=str(exc))
    else:
        result.update(valid=True)
    result["_judgment"] = {
        "task": GENERATION_TASK, "left_kind": "practice_item", "left_id": item_id, "judge": "llm",
        "prompt_version": TEACH_BACK_AUTHORING_PROMPT_VERSION, "input_hash": content_key(prompt),
        "verdict": {key: result[key] for key in ("valid", "core_criteria", "error", "rejection") if key in result},
    }
    return result


class _FailureRecorder:
    """The profile's client, forwarding everything, that remembers its last failure.

    A diagnosis records only the failure's class (``run_diagnosis`` handles
    it), so the report takes the failure's structured fields from here.
    """

    def __init__(self, client: Any) -> None:
        self._client = client
        self.failure: BaseException | None = None

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)

    def complete(self, request: Any) -> Any:
        try:
            return self._client.complete(request)
        except Exception as exc:
            self.failure = exc
            raise


def _timed(work: Callable[[], dict[str, Any]], recorder: _FailureRecorder | None = None, *,
           provider: str = "") -> dict[str, Any]:
    """Run one comparison call; an interrupt propagates, any other failure is recorded as codes."""

    if recorder is not None:
        recorder.failure = None
    started = time.monotonic()
    raised: BaseException | None = None
    with _measured() as meter:
        try:
            result = work()
        except AIInterrupted:
            raise
        except (AIProviderUnavailable, ValueError) as exc:
            raised = exc
            result = {"parsed": False, "valid": False, "error": _error_class(exc)}
    if result.get("error"):
        failure = raised if raised is not None else (recorder.failure if recorder is not None else None)
        result["failure"] = _failure_record(result["error"], failure, meter, provider=provider)
    return {**result, "seconds": round(time.monotonic() - started, 3), **meter.summary(),
            "receipt_ids": meter.roots()}


_ALLOWANCE_ERRORS = frozenset({"ChatGPTPlanUsageExhausted", "ChatGPTPlanNotEligible", "ChatGPTSignInRequired"})


def plan_allowance(profile_type: str) -> dict[str, Any] | None:
    """The ChatGPT plan's local allowance state (no network); None for other types."""

    if profile_type != "chatgpt_plan":
        return None
    status = PlanSession().status().as_dict()
    usage_limit = status.get("usage_limit") or {}
    return {"state": status.get("state"), "paused_until": status.get("paused_until"),
            "usage_limit_code": usage_limit.get("code"), "usage_limit_at": usage_limit.get("at")}


# -- spend ------------------------------------------------------------------------------------


def _caps(calls: int, tokens: int) -> SpendCaps:
    """One profile's caps: the plan's calls (enforced); tokens and dollars estimated only."""

    return SpendCaps(max_candidates=0, max_pairs=0, max_retries=0, max_calls=calls,
                     max_total_tokens=max(1, tokens), max_estimated_usd=None)


def _planned_inputs(vault: LoadedVault, repository: Any, targets: Targets, request: CompareRequest,
                    store: Any) -> list[dict[str, Any]]:
    """Every planned call's prompt-side size, the same for every profile (no request)."""

    operations: list[dict[str, Any]] = []
    for attempt_id in targets.grading:
        _item, _rubric, context = _grading_context(vault, repository, store.attempt(attempt_id))
        operations.append({"kind": "grading", "target": attempt_id,
                           "input_tokens": _tokens(blind_grading_prompt(context))})
    if targets.diagnosis is not None:
        operations.append({"kind": "diagnosis", "target": targets.diagnosis, "mode": request.diagnosis_mode,
                           **_diagnosis_inputs(vault, repository, store, targets.diagnosis,
                                               request.diagnosis_mode)})
    if targets.generation_item is not None:
        _context, _criteria, prompt = _generation_inputs(vault, targets.generation_item)
        operations.append({"kind": "generation", "target": targets.generation_item,
                           "input_tokens": _tokens(prompt)})
    return operations


def _profile_estimate(vault: LoadedVault, profile: Mapping[str, Any], operations: Sequence[Mapping[str, Any]],
                      request: CompareRequest) -> dict[str, Any]:
    """One profile's planned calls with their token estimates, its caps and their check."""

    name = profile["provider"]
    config = vault.config
    served_cap = getattr(config.ai.providers.get(name), "max_workspace_chars", None)
    calls = []
    for operation in operations:
        if (operation["kind"] == "diagnosis" and request.diagnosis_mode == "snapshot"
                and not profile["read_only_workspace"]):
            continue  # not run: the profile serves no workspace
        output = output_budget(config, _ROUTES[operation["kind"]], provider=name)
        workspace = operation.get("workspace_tokens")
        if workspace is not None and isinstance(served_cap, int):
            # The ChatGPT plan serves at most max_workspace_chars per turn.
            workspace = min(workspace, (served_cap + _BYTES_PER_TOKEN - 1) // _BYTES_PER_TOKEN)
        input_tokens = operation.get("input_tokens") or 0
        calls.append({
            "kind": operation["kind"], "target": operation["target"], "input_tokens": operation.get("input_tokens"),
            **({"workspace_tokens": workspace} if workspace is not None else {}),
            "output_tokens": output, "total_tokens": input_tokens + (workspace or 0) + output,
        })
    total = sum(call["total_tokens"] for call in calls)
    budget = SpendBudget(_caps(len(calls), total), subscription=True)
    # Within the caps by construction (the call cap is the plan); checked all the same.
    budget.check(SpendEstimate(calls=len(calls), total_tokens=total, estimated_usd=None))
    return {
        "billing": "subscription", "cost_basis": ESTIMATED_ONLY, "physical_request_bound": False,
        "calls": len(calls),
        "estimated_input_tokens": sum(call["input_tokens"] or 0 for call in calls),
        "estimated_workspace_tokens": sum(call.get("workspace_tokens") or 0 for call in calls),
        "estimated_output_tokens": sum(call["output_tokens"] for call in calls),
        "estimated_total_tokens": total,
        "estimated_usd": None,
        "caps": budget.declared(),
        "planned": calls,
    }


_ESTIMATE_BASIS = (
    "prompt bytes / 4 for each call's input; a snapshot diagnosis adds its whole export once (Codex reads it "
    "in its sandbox; the ChatGPT plan serves at most max_workspace_chars and resends what it served each "
    "round, so a multi-round turn can exceed this); output at the route's output budget. Subscription: no "
    "marginal dollar cost (estimated_usd null), no physical-request bound; reported usage reconciles it."
)


# -- plan and run ---------------------------------------------------------------------------


def plan_compare(vault: LoadedVault, repository: Any, request: CompareRequest) -> dict[str, Any]:
    """What a run would do: profiles, targets, calls and their estimates; builds no client and sends nothing."""

    profiles = check_profiles(vault, request)
    store = live_history_store(vault, repository)
    targets = select_targets(vault, repository, request, store=store)
    calls_per_profile = len(targets.grading) + int(targets.diagnosis is not None) + int(
        targets.generation_item is not None)
    operations = _planned_inputs(vault, repository, targets, request, store)
    estimates = {profile["provider"]: _profile_estimate(vault, profile, operations, request) for profile in profiles}
    return {
        "version": COMPARE_VERSION,
        "profiles": profiles,
        "targets": targets.as_dict(),
        "diagnosis_mode": request.diagnosis_mode,
        "calls_per_profile": calls_per_profile,
        "max_calls": sum(estimate["calls"] for estimate in estimates.values()),
        "timeout_seconds": request.timeout_seconds,
        "estimate": {
            "basis": _ESTIMATE_BASIS,
            "operations": operations,
            "profiles": estimates,
            "estimated_total_tokens": sum(estimate["estimated_total_tokens"] for estimate in estimates.values()),
            "estimated_usd": None,
        },
        "billing": "subscription (cost estimated from reported usage, estimated_only; no dollar cap)",
    }


def _append_judgment(repository: Any, payload: Mapping[str, Any], *, provider: str, model: str,
                     run_id: str) -> str:
    """One comparison verdict in the vault copy's ledger (the comparison's own task)."""

    with repository.atomic():
        return append_judgment(
            repository.connection(),
            task=payload["task"], left_kind=payload["left_kind"], left_id=payload["left_id"],
            right_kind=PROFILE_KIND, right_id=provider, judge=payload["judge"], judge_model=model,
            prompt_version=payload["prompt_version"], input_hash=payload["input_hash"],
            verdict=json.dumps(payload["verdict"], sort_keys=True), score=payload.get("score"),
            rationale=json.dumps({"compare_run_id": run_id, "compare_version": COMPARE_VERSION,
                                  "authority": "none"}, sort_keys=True),
        )


def run_compare(
    vault: LoadedVault,
    repository: Any,
    request: CompareRequest,
    *,
    client_factory: Callable[[str], Any] | None = None,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Run the plan on every ready profile; returns the report (ids, numbers and local text only)."""

    plan = plan_compare(vault, repository, request)
    targets = Targets(**{key: value for key, value in plan["targets"].items()})
    store = live_history_store(vault, repository)
    factory = client_factory or (lambda name: client_for_provider(
        vault.root, vault.config, name, timeout_seconds=request.timeout_seconds))
    say = progress or (lambda _message: None)
    run_id = new_ulid()
    results: list[dict[str, Any]] = []
    for profile in plan["profiles"]:
        name = profile["provider"]
        estimate = plan["estimate"]["profiles"][name]
        planned = {(call["kind"], call["target"]): call for call in estimate["planned"]}
        row: dict[str, Any] = {**profile, "grading": {}, "diagnosis": None, "generation": None}
        results.append(row)
        if not profile["ready"]:
            row["error"] = profile["message"] or "not ready"
            say(f"{name}: not ready ({row['error']})")
            continue
        try:
            client = _FailureRecorder(factory(name))
        except AIProviderUnavailable as exc:
            row["error"] = _error_class(exc)
            row["failure"] = _failure_record(_error_class(exc), exc, _Meter(), provider=name)
            say(f"{name}: {row['error']}: {row['failure']['hint']}")
            continue
        budget = SpendBudget(_caps(estimate["calls"], estimate["estimated_total_tokens"]), subscription=True)
        row["allowance_before"] = plan_allowance(profile["type"])
        stopped: str | None = None

        def call(kind: str, target: str, work: Callable[[], dict[str, Any]]) -> dict[str, Any]:
            nonlocal stopped
            if stopped is not None:
                return {"parsed": False, "valid": False, "error": f"not_run: {stopped}"}
            tokens = int(planned[(kind, target)]["total_tokens"])
            say(f"{name}: {kind} {target}")
            try:
                # Admitted before anything is sent: the root receipt records the
                # caps in force (subscription, estimated_only, no physical-request
                # bound) and what this call is.
                with budget.request(SpendEstimate(calls=1, total_tokens=tokens, estimated_usd=None)) as charge, \
                        annotate_calls(ai_compare={"run_id": run_id, "kind": kind, "target": target,
                                                   "planned_total_tokens": tokens}):
                    outcome = _timed(work, client, provider=name)
                    reported = (outcome.get("input_tokens") or 0) + (outcome.get("output_tokens") or 0)
                    charge.reconcile(total_tokens=reported or None)
            except SpendLimitExceeded:
                stopped = "spend_cap"
                return {"parsed": False, "valid": False, "error": "not_run: spend_cap"}
            outcome["spend"] = {
                "planned_total_tokens": tokens,
                **subscription_usage_estimate(outcome, planned_tokens=tokens, price_per_token=None),
            }
            judgment = outcome.pop("_judgment", None)
            if judgment is not None:
                model = ",".join(outcome.get("resolved_models") or []) or str(profile.get("model") or "unknown")
                try:
                    outcome["judgment_id"] = _append_judgment(repository, judgment, provider=name, model=model,
                                                              run_id=run_id)
                except (sqlite3.Error, ValueError) as exc:
                    outcome["judgment_error"] = _error_class(exc)
            if outcome.get("error") in _ALLOWANCE_ERRORS:
                # The plan refuses locally from here on: stop this profile.
                stopped = str(outcome["error"])
            return outcome

        for attempt_id in targets.grading:
            attempt = store.attempt(attempt_id)
            row["grading"][attempt_id] = call(
                "grading", attempt_id, lambda attempt=attempt: _grade(vault, repository, client, attempt))
        if targets.diagnosis is not None:
            if request.diagnosis_mode == "snapshot" and not profile["read_only_workspace"]:
                error = "provider_lacks_read_only_workspace"
                row["diagnosis"] = {"parsed": False, "valid": False, "error": error,
                                    "failure": {"hint": _HINTS[error]}}
            else:
                row["diagnosis"] = call(
                    "diagnosis", targets.diagnosis,
                    lambda: _diagnose(vault, repository, client, targets.diagnosis, store=store,
                                      mode=request.diagnosis_mode))
        if targets.generation_item is not None:
            row["generation"] = call("generation", targets.generation_item,
                                     lambda: _generate(vault, client, targets.generation_item))
        row["allowance_after"] = plan_allowance(profile["type"])
        row["stopped"] = stopped
        row["summary"] = _profile_summary(row)
        row["spend"] = {
            "billing": "subscription", "cost_basis": ESTIMATED_ONLY, "physical_request_bound": False,
            "caps": budget.declared(),
            # Admitted calls; tokens as reconciled (never below a call's reservation).
            "used": asdict(budget.used),
            "estimated_total_tokens": estimate["estimated_total_tokens"],
            "reported_total_tokens": row["summary"]["input_tokens"] + row["summary"]["output_tokens"],
            "estimated_usd": None,
        }
    recorded = {attempt_id: _recorded_grade(store.attempt(attempt_id)) for attempt_id in targets.grading}
    for row in results:
        row["vs_recorded_grade"] = _grading_agreement(
            {attempt_id: grade for attempt_id, grade in row["grading"].items()}, recorded)
    return {
        **plan,
        "run_id": run_id,
        "results": results,
        "agreement": _agreement(results),
        "calls_made": sum(int(row.get("spend", {}).get("used", {}).get("calls") or 0) for row in results),
    }


# -- summaries -----------------------------------------------------------------------------


def _calls(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    calls = [call for call in (row.get("grading") or {}).values() if call]
    calls += [call for call in (row.get("diagnosis"), row.get("generation")) if call]
    return [call for call in calls if "seconds" in call]


def _profile_summary(row: Mapping[str, Any]) -> dict[str, Any]:
    calls = _calls(row)
    seconds = [call["seconds"] for call in calls]
    totals = {key: sum(call.get(key) or 0 for call in calls)
              for key in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens",
                          "physical_requests")}
    count = len(calls) or 1
    return {
        "calls": len(calls),
        "valid": sum(1 for call in calls if call.get("valid")),
        "parsed": sum(1 for call in calls if call.get("parsed")),
        "errors": sorted({str(call["error"]) for call in calls if call.get("error")}),
        "seconds_median": round(statistics.median(seconds), 3) if seconds else None,
        "seconds_max": max(seconds) if seconds else None,
        **totals,
        "tokens_per_call": round((totals["input_tokens"] + totals["output_tokens"]) / count, 1) if calls else None,
        "output_tokens_per_call": round(totals["output_tokens"] / count, 1) if calls else None,
        "allowance_errors": sum(1 for call in calls if call.get("error") in _ALLOWANCE_ERRORS),
    }


def _recorded_grade(attempt: Any) -> dict[str, Any] | None:
    if attempt is None or attempt.score is None or not attempt.max_points:
        return None
    return {"valid": True, "rubric_score": attempt.score, "max_points": attempt.max_points, "criteria": None}


def _grading_agreement(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
    pairs = []
    for attempt_id, one in left.items():
        other = right.get(attempt_id)
        if not (one and other and one.get("valid") and other.get("valid")):
            continue
        maximum = float(one.get("max_points") or other.get("max_points") or 0) or None
        a, b = float(one["rubric_score"]), float(other["rubric_score"])
        criteria = None
        if one.get("criteria") is not None and other.get("criteria") is not None:
            ids = set(one["criteria"]) | set(other["criteria"])
            same = sum(1 for key in ids if one["criteria"].get(key) == other["criteria"].get(key))
            criteria = same / len(ids) if ids else None
        pairs.append({
            "attempt_id": attempt_id, "scores": [a, b], "max_points": maximum, "exact": a == b,
            "abs_diff_fraction": abs(a - b) / maximum if maximum else None,
            "full_credit_agrees": (a == maximum) == (b == maximum) if maximum else None,
            "criterion_agreement": criteria,
        })

    def mean(key: str) -> float | None:
        values = [pair[key] for pair in pairs if pair[key] is not None]
        return round(sum(float(value) for value in values) / len(values), 4) if values else None

    return {
        "compared": len(pairs),
        "exact_rate": mean("exact"),
        "mean_abs_diff_fraction": mean("abs_diff_fraction"),
        "full_credit_agreement": mean("full_credit_agrees"),
        "criterion_agreement": mean("criterion_agreement"),
        "pairs": pairs,
    }


def _jaccard(one: Sequence[str], other: Sequence[str]) -> float | None:
    union = set(one) | set(other)
    return round(len(set(one) & set(other)) / len(union), 4) if union else None


def _agreement(results: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    pairs = []
    for left, right in combinations([row for row in results if row.get("ready")], 2):
        entry: dict[str, Any] = {
            "profiles": [left["provider"], right["provider"]],
            "grading": _grading_agreement(left.get("grading") or {}, right.get("grading") or {}),
        }
        one, other = left.get("diagnosis"), right.get("diagnosis")
        if one and other:
            both = bool(one.get("valid") and other.get("valid"))
            entry["diagnosis"] = {
                "both_valid": both,
                "same_causal_classes": one.get("causal_classes") == other.get("causal_classes") if both else None,
                "evidence_jaccard": _jaccard(one.get("evidence_attempt_ids") or [],
                                             other.get("evidence_attempt_ids") or []) if both else None,
                "unknown_ids": [one.get("unknown_id_count"), other.get("unknown_id_count")],
            }
        one, other = left.get("generation"), right.get("generation")
        if one and other:
            entry["generation"] = {"both_valid": bool(one.get("valid") and other.get("valid")),
                                   "valid": [bool(one.get("valid")), bool(other.get("valid"))]}
        pairs.append(entry)
    return pairs


__all__ = [
    "COMPARE_VERSION",
    "CompareRefused",
    "CompareRequest",
    "DEFAULT_GRADING_ATTEMPTS",
    "DIAGNOSIS_MODES",
    "DIAGNOSIS_TASK",
    "GENERATION_TASK",
    "GRADING_TASK",
    "PROFILE_KIND",
    "Targets",
    "check_profiles",
    "copy_vault",
    "database_location_reason",
    "plan_allowance",
    "plan_compare",
    "run_compare",
    "select_targets",
    "tracked_database_reason",
]
