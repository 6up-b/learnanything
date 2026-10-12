"""Deterministic symbolic fingerprints for PF items (Slice 2 §5.4, migration 169).

A fingerprint is a set of namespaced exact keys in the 077 vocabulary
(``learner.familiarity.NAMESPACES``); namespaces are never interchangeable.
The freshness gate uses them two ways:

* **exact keys decide** a duplicate: the same normalized stem
  (``surface_hash``/``stem``) or the same generator draw
  (``parameter_template``/``parameters``);
* **suspect keys nominate** a pair for the LLM isomorph judge, regardless of any
  embedding score: the same final answer and quantities (``verbatim_target``),
  the same sympy normal form, or the same skeleton technique sequence
  (``solution_recipe``). A suspect key never rejects on its own (R1/R2).

``item_fingerprints`` is DERIVED and holds rows only for practice-family members,
so a vault without families rebuilds unchanged. The replayer reads vault content
plus persisted inputs (skeletons, published candidates' sandbox-computed normal
forms); it never calls a model and never executes a generator program.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any, Iterable, Mapping, Sequence

from learnloop.db.repositories import Repository
from learnloop.db.stores.pf import candidates, replace_item_fingerprints, skeletons_for_hashes
from learnloop.vault.hashes import practice_item_hash, skeleton_content_hash
from learnloop.vault.models import LoadedVault, PracticeItem

FINGERPRINT_VERSION = "pf-fingerprint-v1"
FINAL_ANSWER_PREFIX = "Final answer:"
WORKED_SOLUTION_PREFIX = "Worked solution:"

# Keys that decide a duplicate without a judge (exact identity).
EXACT_COMPONENTS = frozenset({("surface_hash", "stem"), ("parameter_template", "parameters")})

_NUMBER = re.compile(r"(?<![\w.])\d+(?:\.\d+)?")
_LATEX_DELIMITERS = re.compile(r"\\[()\[\]]|\$")


def _sha(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def normalize_text(text: str) -> str:
    """Case-, width- and whitespace-insensitive text identity."""
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def render_expected_answer(final_answer: str, solution: str) -> str:
    """The expected answer a published PF item carries: key first, then the work."""
    return f"{FINAL_ANSWER_PREFIX} {final_answer.strip()}\n\n{WORKED_SOLUTION_PREFIX}\n{solution.strip()}"


def final_answer_text(expected_answer: str | Mapping[str, Any]) -> str:
    """The final answer of an item's reference, or the whole reference."""
    if isinstance(expected_answer, Mapping):
        for key in ("final_answer", "answer", "result"):
            value = expected_answer.get(key)
            if isinstance(value, (str, int, float)) and not isinstance(value, bool):
                return str(value)
        return json.dumps(expected_answer, sort_keys=True, ensure_ascii=False)
    for line in str(expected_answer).splitlines():
        stripped = line.strip()
        if stripped.casefold().startswith(FINAL_ANSWER_PREFIX.casefold()):
            return stripped.split(":", 1)[1].strip()
    return str(expected_answer)


def normalize_answer(answer: str) -> str:
    text = _LATEX_DELIMITERS.sub("", unicodedata.normalize("NFKC", answer).casefold())
    text = "".join(text.split()).rstrip(".")
    return _NUMBER.sub(lambda match: _canonical_number(match.group(0)), text)


def _canonical_number(token: str) -> str:
    if "." in token:
        whole, fraction = token.split(".", 1)
        fraction = fraction.rstrip("0")
        whole = whole.lstrip("0") or "0"
        return f"{whole}.{fraction}" if fraction else whole
    return token.lstrip("0") or "0"


def key_quantities(text: str) -> list[str]:
    """The sorted multiset of numeric literals in a stem (its parameters)."""
    return sorted(_canonical_number(token) for token in _NUMBER.findall(unicodedata.normalize("NFKC", text)))


def technique_signature(techniques: Sequence[str]) -> str:
    return _sha([normalize_text(step) for step in techniques if step.strip()])


def fingerprint_keys(
    *, prompt: str, expected_answer: str | Mapping[str, Any],
    skeletons: Sequence[Mapping[str, Any]] = (), generator_hash: str | None = None,
    parameters: Mapping[str, Any] | None = None, sympy_normal_form: str | None = None,
) -> list[tuple[str, str, str]]:
    """``(namespace, component, value_hash)`` keys; missing inputs yield no key."""
    keys: list[tuple[str, str, str]] = [
        ("surface_hash", "stem", _sha(["stem", normalize_text(prompt)])),
    ]
    answer = normalize_answer(final_answer_text(expected_answer))
    if answer:
        keys.append(("verbatim_target", "answer", _sha(["answer", answer])))
    quantities = key_quantities(prompt)
    if quantities and answer:
        keys.append(("verbatim_target", "answer_quantities", _sha(["answer_quantities", answer, quantities])))
    if sympy_normal_form:
        keys.append(("verbatim_target", "answer_sympy", _sha(["sympy", sympy_normal_form])))
    if generator_hash:
        keys.append(("parameter_template", "generator", _sha(["generator", generator_hash])))
        if parameters is not None:
            keys.append(("parameter_template", "parameters",
                         _sha(["parameters", generator_hash, dict(parameters)])))
    for skeleton in skeletons:
        techniques = skeleton.get("techniques") or []
        if techniques:
            keys.append(("solution_recipe", f"skeleton:{skeleton['model_id']}",
                         _sha(["skeleton", technique_signature(techniques)])))
    return sorted(set(keys))


def published_candidate_payloads(connection: Any) -> dict[str, dict[str, Any]]:
    """Published item id -> its candidate payload (sandbox outputs are persisted)."""
    result: dict[str, dict[str, Any]] = {}
    for row in candidates(connection, where="status='published' AND published_item_id IS NOT NULL"):
        result[row["published_item_id"]] = json.loads(row["payload_json"])
    return result


def item_fingerprint_keys(item: PracticeItem, *, skeletons: Sequence[Mapping[str, Any]] = (),
                          payload: Mapping[str, Any] | None = None) -> list[tuple[str, str, str]]:
    payload = payload or {}
    return fingerprint_keys(
        prompt=item.prompt, expected_answer=item.expected_answer, skeletons=skeletons,
        generator_hash=payload.get("generator_hash"), parameters=payload.get("parameters"),
        sympy_normal_form=payload.get("sympy_normal_form"),
    )


def family_items(vault: LoadedVault) -> list[PracticeItem]:
    return [item for _, item in sorted(vault.practice_items.items()) if item.family_id is not None]


def compute_item_fingerprints(vault: LoadedVault, connection: Any) -> list[dict[str, Any]]:
    items = family_items(vault)
    if not items:
        return []
    hashes = {item.id: skeleton_content_hash(item.prompt, item.expected_answer) for item in items}
    skeletons = skeletons_for_hashes(connection, hashes.values())
    payloads = published_candidate_payloads(connection)
    rows: list[dict[str, Any]] = []
    for item in items:
        content = practice_item_hash(item)
        for namespace, component, value in item_fingerprint_keys(
            item, skeletons=skeletons.get(hashes[item.id], ()), payload=payloads.get(item.id),
        ):
            rows.append({
                "practice_item_id": item.id, "namespace": namespace, "component": component,
                "value_hash": value, "item_content_hash": content,
                "fingerprint_version": FINGERPRINT_VERSION,
            })
    return rows


def rebuild_item_fingerprints(vault: LoadedVault, repository: Repository) -> dict[str, int]:
    """The single DERIVED replayer: pure recomputation inside the caller's transaction."""
    with repository.connection() as connection:
        rows = compute_item_fingerprints(vault, connection)
        cleared, written = replace_item_fingerprints(connection, rows)
    return {"cleared": cleared, "written": written,
            "items": len({row["practice_item_id"] for row in rows})}


def shared_keys(left: Iterable[tuple[str, str, str]],
                right: Iterable[tuple[str, str, str]]) -> list[tuple[str, str]]:
    """``(namespace, component)`` pairs whose value matches on both sides.

    Skeleton components match across models by technique signature alone.
    """
    def normalized(keys: Iterable[tuple[str, str, str]]) -> set[tuple[str, str, str]]:
        return {(namespace, "skeleton" if component.startswith("skeleton:") else component, value)
                for namespace, component, value in keys}

    common = normalized(left) & normalized(right)
    return sorted({(namespace, component) for namespace, component, _ in common})


__all__ = [
    "EXACT_COMPONENTS", "FINAL_ANSWER_PREFIX", "FINGERPRINT_VERSION", "WORKED_SOLUTION_PREFIX",
    "compute_item_fingerprints", "final_answer_text", "fingerprint_keys", "item_fingerprint_keys",
    "key_quantities", "normalize_answer", "normalize_text", "rebuild_item_fingerprints",
    "render_expected_answer", "shared_keys", "skeleton_content_hash", "technique_signature",
]
