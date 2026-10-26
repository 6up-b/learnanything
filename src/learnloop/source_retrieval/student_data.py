"""The query student's training data: synthetic questions from permitted passages (spec_local_contextual_retrieval_v1 §7.1 "Data", "Leakage rules"; Q8; P2).

``learnloop embeddings local student generate --vault V --bank BANK`` asks the generator for
8-12 varied questions per passage over the vault's own books and stores them, with their
intended supporting blocks, under the data root (never in the vault or the repository, §11).

* **Permitted text only.** Passages are consecutive ``teaching``-class blocks of a section (the
  window rule's policy classes: no exam, held-out, solution or assessment-lane block, by the
  production predicates), at most :data:`~learnloop.local_embeddings.student_pins.PASSAGE_TOKENS`
  estimated tokens. Protection is read again for every call, so a block held out since the run
  began never reaches the model.
* **The bank never leaks (spec §7.1).** The frozen E0/E1 bank's gold supports (every required
  span and answer span) are left out of every passage, so they never enter a generation prompt
  and are never a hard negative. A question with 5-gram overlap above 0.5 with any bank question
  is dropped here; the teacher-cosine guard (>= 0.90) runs when the teacher has encoded both
  (``query_student.run_targets``). Counts are reported. A run without a bank is refused.
* **The generator (Q8).** Route ``ai.routing.retrieval_query_generator`` (default: the ChatGPT
  plan's ``chatgpt_luna``, GPT-6 Luna). Background-quiet: no OpenRouter offer is raised and no
  grant is ridden unless the command itself carries the owner's grant
  (``LEARNLOOP_AI_FALLBACK=openrouter``); a plan that cannot serve is reported with how to ask.
  A metered route needs ``source_retrieval.llm_price_per_million`` and is capped at
  ``embedding.local.student_generator_max_cost_usd`` ($5, keep). Receipts go to the vault
  (owner kind ``retrieval_query_generation``).
* **Shapes.** The intents of ``find_sources`` (explain, remediate, alternative, worked example,
  compare), deictic Reader questions about a selected block (the query then carries the
  selection exactly as the Reader sends it), definition and theorem lookups, and paraphrases
  sharing no vocabulary with the passage.
* **Splits and budgets.** Families group a vault's sources by the bank's own rule (Codex review
  F8): alternate editions and overlapping copies (the same source bytes or the same title stem)
  share a family, recorded once in the data directory's ``families.json`` and read by
  generation, the splits, training and evaluation alike. One family per vault (by a stable hash
  over the mapping's current families) is held out: never trained on, the unseen-source test. A
  stored row's split is re-derived from the current hold-out whenever a dataset is built
  (:func:`current_split`), so a family held out after its rows were generated leaves training.
  Of the rest, a passage-disjoint tenth is the development split. Every question has a stable rank, so the 2k/10k/50k budgets are nested by
  construction (the first 2,000 are inside the first 10,000).
* **Resumable.** A passage whose questions are stored is never asked again.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import nullcontext
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Literal

from pydantic import Field

from learnloop.ai import plan_fallback
from learnloop.ai.errors import AIInvalidOutput, AIProviderUnavailable
from learnloop.ai.schemas import WireModel
from learnloop.ai.spend import SpendBudget, SpendCaps, SpendLimitExceeded
from learnloop.ai.transport import render_structured_prompt
from learnloop.db.repositories import Repository
from learnloop.local_embeddings import pins
from learnloop.local_embeddings import student_pins as SP
from learnloop.practice_index.paid import (
    PaidCalls,
    estimated_call_tokens,
    plan_route,
    resolve_client,
    transport_problem,
)
from learnloop.source_retrieval.corpus import current_extractions
from learnloop.source_retrieval.windows import extraction_windows, token_estimate
from learnloop.vault.models import LoadedVault

TASK = "retrieval_query_generator"
OWNER_KIND = "retrieval_query_generation"
PROMPT_VERSION = "query-student-questions-v1"
#: The test suite sets it to ``off``: no generator model is reached (an injected client still answers).
MODELS_ENV = "LEARNLOOP_QUERY_STUDENT_MODELS"
CAP_SETTING = "embedding.local.student_generator_max_cost_usd"
PRICE_SETTING = "source_retrieval.llm_price_per_million"
INTENTS = ("explain", "remediate", "alternative", "worked_example", "compare")
SHAPES = ("plain", "deictic", "definition_lookup", "theorem_lookup", "paraphrase")
SELECTION_LABEL = "Selected passage: "
#: keep (measurement split, structural): one passage in ten of the training families is development.
DEV_SHARE_DENOMINATOR = 10
#: keep (spec §7.1): the longest question text accepted from the generator, in characters.
MAX_QUESTION_CHARS = 600
#: keep (operational): retries one call may use (a failed or invalid answer is a new attempt).
MAX_RETRIES_PER_CALL = 1
#: keep (prompt size): the tokens one call's answer may use at most.
OUTPUT_TOKENS = 4_000


def models_off() -> bool:
    return os.environ.get(MODELS_ENV, "").strip().lower() == "off"


def _sha(*parts: Any) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()


def vault_key(vault: LoadedVault) -> str:
    root = Path(vault.root).resolve()
    return f"{root.name}-{_sha(str(root))[:12]}"


def data_dir(data_root: Path, space_id: str, vault: LoadedVault) -> Path:
    return SP.space_home(data_root, space_id) / "data" / vault_key(vault)


# -- the bank (read only for its guards; never a prompt) -------------------------------------
def retrieval_text(question: str, selection: str | None) -> str:
    """The text a query encoder sees: the question, and a selection exactly as the Reader sends it."""

    question = " ".join(str(question).split())
    return f"{question}\n\n{SELECTION_LABEL}{selection}" if selection else question


def load_bank(path: Path) -> list[dict[str, Any]]:
    """The frozen E0/E1 bank (its private JSON or JSONL rows, read by key; never imported from
    ``experiments``): per question its id, retrieval text, family, vault, origin and evidence."""

    raw = Path(path).read_text(encoding="utf-8")
    try:
        loaded = json.loads(raw)
        rows = loaded.get("questions", loaded) if isinstance(loaded, dict) else loaded
    except ValueError:
        rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    bank = []
    for row in rows:
        if not isinstance(row, Mapping) or not str(row.get("question") or "").strip():
            continue
        sets = []
        for item in row.get("evidence_sets") or []:
            required = item.get("required") if isinstance(item, Mapping) else item
            sets.append([(str(ref[0]), str(ref[1])) for ref in required or [] if len(ref) >= 2])
        bank.append({"query_id": str(row.get("query_id") or _sha(row.get("question"))[:16]),
                     "text": retrieval_text(str(row["question"]), row.get("selected_passage")),
                     "question": " ".join(str(row["question"]).split()),
                     "family": str(row.get("family") or ""), "vault": str(row.get("vault") or ""),
                     "origin": str(row.get("origin") or ""), "deictic": bool(row.get("selected_passage")),
                     "answerable": bool(row.get("answerable", True)), "evidence_sets": sets,
                     "answer_spans": [(str(ref[0]), str(ref[1])) for ref in row.get("answer_spans") or []
                                      if len(ref) >= 2],
                     # Codex review F4: the bank's own slice and stratum (its denominators), kept.
                     "split": str(row.get("split") or ""), "stratum": str(row.get("stratum") or ""),
                     # Codex review F5: the blocks the label protocol judged for this question, when the
                     # bank records them; a retrieved block outside them is unjudged, never a miss.
                     "judged": (None if row.get("judged") is None else
                                sorted({(str(ref[0]), str(ref[1])) for ref in row.get("judged") or []
                                        if len(ref) >= 2}))})
    if not bank:
        raise ValueError(f"{path} holds no bank question")
    return bank


def bank_supports(bank: Sequence[Mapping[str, Any]]) -> set[tuple[str, str]]:
    """Every gold support of the bank: never in a prompt, never a hard negative."""

    return {tuple(ref) for question in bank for refs in question["evidence_sets"] for ref in refs} | \
        {tuple(ref) for question in bank for ref in question.get("answer_spans") or []}


_WORD = re.compile(r"[a-z0-9]+")


def ngrams(text: str, n: int = SP.LEAKAGE_NGRAM) -> set[tuple[str, ...]]:
    """Word n-grams of the lowercased text; a text shorter than ``n`` is its one n-gram (structural)."""

    words = _WORD.findall(str(text).lower())
    if not words:
        return set()
    size = min(n, len(words))
    return {tuple(words[index:index + size]) for index in range(len(words) - size + 1)}


def ngram_overlap(query: str, bank_grams: Sequence[set[tuple[str, ...]]]) -> float:
    """The largest share of the query's 5-grams any one bank question holds."""

    grams = ngrams(query)
    if not grams:
        return 0.0
    return max((len(grams & other) / len(grams) for other in bank_grams if other), default=0.0)


# -- passages (permitted text only) -------------------------------------------------------------
def passages(vault: LoadedVault, repository: Repository, *, excluded: set[tuple[str, str]],
             extraction_ids: Iterable[str] | None = None) -> list[dict[str, Any]]:
    """Consecutive teaching blocks of one section, at most PASSAGE_TOKENS estimated tokens each,
    with the bank's gold supports left out (the passage then ends at the gap). ``extraction_ids``
    limits the read (the per-call protection check reads only the batch's sources)."""

    found = []
    wanted = None if extraction_ids is None else set(extraction_ids)
    for extraction_id, extraction in sorted(current_extractions(repository).items()):
        if wanted is not None and extraction_id not in wanted:
            continue
        windows = extraction_windows(vault, repository, extraction_id, "singleton")
        current: list[dict[str, Any]] = []
        section: tuple[str, ...] | None = None
        tokens = 0

        def close() -> None:
            nonlocal current, tokens
            if current:
                text_key = _sha(PROMPT_VERSION, extraction_id, [[b["span_id"], b["text"]] for b in current])
                found.append({"key": "pg_" + text_key[:24], "extraction_id": extraction_id,
                              "source_id": extraction.source_id, "section": list(section or ()),
                              "blocks": list(current)})
            current, tokens = [], 0

        for window in windows:
            member = window.members[0]
            if window.policy_class != "teaching" or (extraction_id, member.span_id) in excluded or member.split:
                close()
                continue
            size = token_estimate(member.text)
            if window.section != section or tokens + size > SP.PASSAGE_TOKENS:
                close()
                section = window.section
            current.append({"span_id": member.span_id, "text": member.text})
            tokens += size
        close()
    return found


# -- source families (one mapping for generation, splits, training and evaluation) -------------------
def _title_stem(title: str) -> str:
    """The bank's edition rule (``experiments.contextual_embeddings.corpus``, restated: production
    never imports experiments): lowercased words, edition and ordinal words dropped, the first six."""

    value = re.sub(r"[^a-z0-9]+", " ", str(title).lower()).strip()
    value = re.sub(r"\b(edition|ed|v\d+|\d+(st|nd|rd|th))\b", " ", value)
    return " ".join(value.split()[:6])


def _family_keys(repository: Repository, extraction_id: str, title: str) -> list[str]:
    run = repository.get_extraction_run(extraction_id) or {}
    revision = repository.get_source_revision(str(run.get("revision_id") or "")) or {}
    keys = []
    if revision.get("asset_hash"):
        keys.append(f"bytes:{revision['asset_hash']}")
    if _title_stem(title):
        keys.append(f"title:{_title_stem(title)}")
    return keys


def family_map(directory: Path | None, repository: Repository, *, persist: bool = True) -> dict[str, str]:
    """``{source_id: family}``: sources sharing source bytes or a title stem share a family.
    With ``directory``, the mapping is persisted there (``families.json``) and a source keeps the
    family it was first given, so a later book never moves a trained question's family. With
    ``persist=False`` (every dry run, Codex re-review F18) the stored assignments are read and the
    additions computed in memory: nothing is created or rewritten."""

    path = None if directory is None else Path(directory) / "families.json"
    stored: dict[str, Any] = {"sources": {}, "keys": {}}
    if path is not None and path.is_file():
        try:
            stored = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            stored = {"sources": {}, "keys": {}}
    sources: dict[str, str] = dict(stored.get("sources") or {})
    by_key: dict[str, str] = dict(stored.get("keys") or {})
    changed = False
    for extraction_id, extraction in sorted(current_extractions(repository).items(),
                                            key=lambda item: item[1].source_id):
        keys = _family_keys(repository, extraction_id, extraction.title)
        family = sources.get(extraction.source_id) or next((by_key[key] for key in keys if key in by_key), None) \
            or f"fam_{extraction.source_id}"
        if sources.get(extraction.source_id) != family:
            sources[extraction.source_id] = family
            changed = True
        for key in keys:
            if key not in by_key:
                by_key[key] = family
                changed = True
    if path is not None and changed and persist:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        temporary.write_text(json.dumps({"sources": sources, "keys": by_key}, sort_keys=True, indent=1) + "\n",
                             encoding="utf-8")
        os.replace(temporary, path)
    return sources


def extraction_families(repository: Repository, families: Mapping[str, str]) -> dict[str, str]:
    """``{extraction_id: family}`` for the vault's current extractions."""

    return {extraction_id: families.get(extraction.source_id, f"fam_{extraction.source_id}")
            for extraction_id, extraction in current_extractions(repository).items()}


def question_families(question: Mapping[str, Any], by_extraction: Mapping[str, str]) -> set[str]:
    """A bank question's families in THIS mapping: those of its evidence's sources (the bank's own
    family labels are aliases of another tool and never compared, Codex review F8)."""

    refs = [ref for required in question.get("evidence_sets") or [] for ref in required] + \
        list(question.get("answer_spans") or [])
    return {by_extraction[str(ref[0])] for ref in refs if str(ref[0]) in by_extraction}


def family_of(passage: Mapping[str, Any]) -> str:
    return str(passage.get("family") or passage["source_id"])


def split_of(passage: Mapping[str, Any], held_out: str | None) -> str:
    if family_of(passage) == held_out:
        return "heldout"
    return "dev" if int(_sha("dev", passage["key"])[:8], 16) % DEV_SHARE_DENOMINATOR == 0 else "train"


def held_out_family(found: Sequence[Mapping[str, Any]]) -> str | None:
    """One family per vault is never trained on (the unseen-source test), when it has two or more."""

    return held_out_among(family_of(passage) for passage in found)


def held_out_among(families: Iterable[str]) -> str | None:
    """The held-out family among ``families`` (two or more), by a stable hash."""

    found = sorted({str(family) for family in families})
    if len(found) < 2:
        return None
    return min(found, key=lambda family: _sha("heldout", family))


def vault_held_out(by_extraction: Mapping[str, str]) -> str | None:
    """THE vault's held-out family, read by generation and by every dataset build alike (Codex
    final verify F19, spec §7): the hold-out among the family mapping's current families."""

    return held_out_among(by_extraction.values())


def current_split(row: Mapping[str, Any], held_out: str | None) -> str:
    """A stored row's split under the CURRENT hold-out (F19, spec §7: a held-out family is never
    trained on). A row stored before its family was held out is held out now; a row of a family no
    longer held out takes its passage's split. A row without a passage key keeps its stored split
    unless its family is the held-out one."""

    if str(row.get("family")) == held_out:
        return "heldout"
    if row.get("passage"):
        return split_of({"key": row["passage"], "family": row.get("family")}, held_out)
    return str(row.get("split") or "")


def current_rows(rows: Iterable[Mapping[str, Any]], by_extraction: Mapping[str, str]) -> list[dict[str, Any]]:
    """Stored rows under the CURRENT family mapping and hold-out (F19, F20): each row's family from
    its extraction, its split by :func:`current_split`. Generation's progress, every dataset build
    and the doctor's view all count these, never the labels stored with the rows."""

    held_out = vault_held_out(by_extraction)
    out = []
    for row in rows:
        row = {**row, "family": by_extraction.get(str(row.get("extraction_id")), row.get("family"))}
        out.append({**row, "split": current_split(row, held_out)})
    return out


# -- the generator's contract -----------------------------------------------------------------------
class GeneratedQuestionV1(WireModel):
    text: str = Field(description="The question as a learner would type it (never quoting the passage)")
    intent: Literal["explain", "remediate", "alternative", "worked_example", "compare"]
    shape: Literal["plain", "deictic", "definition_lookup", "theorem_lookup", "paraphrase"]
    supports: list[str] = Field(description="The refs of every block a complete answer needs")
    selection_ref: str | None = Field(default=None, description="deictic only: the block the learner selected")


class PassageQuestionsV1(WireModel):
    passage_ref: str
    questions: list[GeneratedQuestionV1]


class GeneratedQuestionsV1(WireModel):
    passages: list[PassageQuestionsV1]


INSTRUCTIONS = (
    "You write retrieval training questions for a learner's own textbook. For EACH passage write "
    f"{SP.QUERIES_PER_PASSAGE_MIN} to {SP.QUERIES_PER_PASSAGE_MAX} varied questions that this passage answers. "
    "Vary the intent (explain, remediate a misunderstanding, an alternative explanation, a worked example, "
    "a comparison) and the shape: plain questions; deictic Reader questions about one selected block "
    "('what does this step mean?', set selection_ref to that block); definition and theorem lookups; "
    "and paraphrases that share no vocabulary with the passage. Never copy a sentence from the passage. "
    "List in supports the refs of every block a complete answer needs (no fewer, no extra)."
)


def call_prompt(batch: Sequence[Mapping[str, Any]]) -> tuple[str, dict[str, dict[str, Any]]]:
    """The call's prompt and ``{passage ref: {"passage": passage, "blocks": {ref: span_id}}}``."""

    refs: dict[str, dict[str, Any]] = {}
    payload_passages = []
    for p_index, passage in enumerate(batch, start=1):
        passage_ref = f"p{p_index}"
        blocks = {f"{passage_ref}b{b_index}": block for b_index, block in enumerate(passage["blocks"], start=1)}
        refs[passage_ref] = {"passage": passage, "blocks": {ref: block["span_id"] for ref, block in blocks.items()}}
        payload_passages.append({"passage_ref": passage_ref, "section": " / ".join(passage["section"]),
                                 "blocks": [{"ref": ref, "text": block["text"]} for ref, block in blocks.items()]})
    prompt = render_structured_prompt("Retrieval training questions", PROMPT_VERSION,
                                      {"instructions": INSTRUCTIONS, "context": {"passages": payload_passages}})
    return prompt, refs


def validated(answer: GeneratedQuestionsV1, refs: Mapping[str, Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Each passage's valid questions (unknown refs, empty or overlong text dropped; at most the cap)."""

    out: dict[str, list[dict[str, Any]]] = {ref: [] for ref in refs}
    for item in answer.passages:
        entry = refs.get(item.passage_ref)
        if entry is None:
            continue
        blocks = entry["blocks"]
        seen: set[str] = set()
        for question in item.questions:
            text = " ".join(question.text.split())
            supports = [blocks[ref] for ref in dict.fromkeys(question.supports) if ref in blocks]
            if not text or len(text) > MAX_QUESTION_CHARS or not supports or text.lower() in seen:
                continue
            selection = blocks.get(question.selection_ref or "") if question.shape == "deictic" else None
            if question.shape == "deictic" and selection is None:
                continue
            seen.add(text.lower())
            out[item.passage_ref].append({"question": text, "intent": question.intent, "shape": question.shape,
                                          "supports": supports, "selection": selection})
            if len(out[item.passage_ref]) >= SP.QUERIES_PER_PASSAGE_MAX:
                break
    return out


# -- the store ----------------------------------------------------------------------------------------
def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _append_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def stored_queries(directory: Path) -> list[dict[str, Any]]:
    return _read_jsonl(Path(directory) / "queries.jsonl")


def done_passages(directory: Path) -> set[str]:
    return {str(row["key"]) for row in _read_jsonl(Path(directory) / "passages.jsonl")}


def query_rows(passage: Mapping[str, Any], questions: Sequence[Mapping[str, Any]], *, split: str, vault: str,
               bank_grams: Sequence[set[tuple[str, ...]]]) -> tuple[list[dict[str, Any]], int]:
    """Stored rows for one passage's questions; returns ``(rows, dropped by the 5-gram guard)``."""

    texts = {block["span_id"]: block["text"] for block in passage["blocks"]}
    rows, dropped = [], 0
    for question in questions:
        if ngram_overlap(question["question"], bank_grams) > SP.LEAKAGE_MAX_5GRAM_OVERLAP:
            dropped += 1
            continue
        text = retrieval_text(question["question"], texts.get(question["selection"]) if question["selection"] else None)
        identity = _sha(passage["key"], text)
        rows.append({"id": "sq_" + identity[:24], "rank": _sha("budget", identity), "text": text,
                     "question": question["question"], "intent": question["intent"], "shape": question["shape"],
                     "supports": list(question["supports"]), "selection": question["selection"],
                     "passage": passage["key"], "extraction_id": passage["extraction_id"],
                     "family": family_of(passage), "split": split, "vault": vault, "origin": "synthetic",
                     "prompt_version": PROMPT_VERSION})
    return rows, dropped


def budgets_of(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """How many training questions each nested budget can take today."""

    train = sum(1 for row in rows if row.get("split") == "train" and not row.get("dropped"))
    return {str(budget): min(budget, train) for budget in SP.BUDGETS}


def nested(rows: Sequence[Mapping[str, Any]], budget: int) -> list[Mapping[str, Any]]:
    """The first ``budget`` training questions by stable rank (nested across budgets by construction)."""

    train = sorted((row for row in rows if row.get("split") == "train" and not row.get("dropped")),
                   key=lambda row: row["rank"])
    return train[:budget]


# -- the run --------------------------------------------------------------------------------------------
def _caps(calls: int, *, subscription: bool, cap: float, passages: int = 0) -> SpendCaps:
    return SpendCaps(max_candidates=max(calls, passages, 1), max_pairs=0, max_retries=max(calls, 1) * MAX_RETRIES_PER_CALL,
                     max_calls=max(calls, 1) * (1 + MAX_RETRIES_PER_CALL), max_total_tokens=10 ** 12,
                     max_estimated_usd=None if subscription else cap)


def generate(vault: LoadedVault, repository: Repository, *, space_id: str, bank_path: Path | None,
             data_root: Path | None = None, budget: int = max(SP.BUDGETS), dry_run: bool = False,
             client: Any | None = None, cancelled: Callable[[], bool] = lambda: False) -> dict[str, Any]:
    """Generate (or plan) synthetic questions up to ``budget`` training questions for this vault."""

    root = data_root or pins.data_root()
    out: dict[str, Any] = {"job": "query_student_generate", "space_id": space_id, "dry_run": dry_run,
                           "vault": vault_key(vault)}
    if bank_path is None:
        return {**out, "status": "refused",
                "reason": "the frozen E0/E1 bank is required (--bank): its gold supports are left out of every "
                          "prompt and its questions are the leakage guard; nothing is generated without it"}
    bank = load_bank(bank_path)
    excluded = bank_supports(bank)
    bank_grams = [ngrams(question["text"]) for question in bank]
    directory = data_dir(root, space_id, vault)
    families = family_map(directory, repository, persist=not dry_run)
    found = [{**passage, "family": families.get(passage["source_id"], f"fam_{passage['source_id']}")}
             for passage in passages(vault, repository, excluded=excluded)]
    by_extraction = extraction_families(repository, families)
    held_out = vault_held_out(by_extraction)
    done = done_passages(directory)
    # F20: progress and the remaining budget count the CURRENT splits, never the stored labels.
    stored = current_rows(stored_queries(directory), by_extraction)
    owed = [passage for passage in found if passage["key"] not in done]
    route = plan_route(vault, TASK, client)
    price = vault.config.source_retrieval.llm_price_per_million
    subscription = route.billing == "subscription"
    cap = float(vault.config.embedding.local.student_generator_max_cost_usd)
    trainable_now = sum(1 for row in stored if row["split"] == "train")
    expected_per_passage = (SP.QUERIES_PER_PASSAGE_MIN + SP.QUERIES_PER_PASSAGE_MAX) / 2
    train_owed = [passage for passage in owed if split_of(passage, held_out) == "train"]
    # Plan only as many passages as the budget can still use (development and held-out passages
    # are always asked: they are the measurements).
    room = max(0, budget - trainable_now)
    needed_train = min(len(train_owed), int(-(-room // expected_per_passage)))
    keep_train = {passage["key"] for passage in train_owed[:needed_train]}
    plan_passages = [passage for passage in owed
                     if split_of(passage, held_out) != "train" or passage["key"] in keep_train]
    batches = [plan_passages[index:index + SP.PASSAGES_PER_CALL]
               for index in range(0, len(plan_passages), SP.PASSAGES_PER_CALL)]
    planner = PaidCalls(route=route, budget=SpendBudget(_caps(len(batches), subscription=subscription, cap=cap, passages=len(plan_passages)),
                                                        subscription=subscription),
                        price_per_million=price, repository=None, owner_kind=OWNER_KIND, owner_id="plan")
    tokens = [estimated_call_tokens(call_prompt(batch)[0], GeneratedQuestionsV1, OUTPUT_TOKENS) for batch in batches]
    out.update({
        "route": route.as_dict(), "bank_questions": len(bank), "bank_supports_excluded": len(excluded),
        "passages": {"eligible": len(found), "done": len(done), "owed": len(owed), "planned": len(plan_passages),
                     "held_out_family": held_out,
                     "by_split": {split: sum(1 for p in found if split_of(p, held_out) == split)
                                  for split in ("train", "dev", "heldout")}},
        "questions": {"stored": len(stored), "train": trainable_now,
                      "expected_new": int(len(plan_passages) * expected_per_passage)},
        "reachable_budgets": {str(b): min(b, trainable_now + int(len(train_owed) * expected_per_passage))
                              for b in SP.BUDGETS},
        "calls": len(batches), "spend_plan": planner.plan(tokens),
        "caps": {CAP_SETTING: cap, "subscription_exempt_from_dollar_cap": subscription},
    })
    if dry_run or not batches:
        return {**out, "status": "dry_run" if dry_run else "complete"}
    if not subscription and price is None and client is None:
        return {**out, "status": "skipped", "reason": f"a metered generator route needs {PRICE_SETTING}"}
    if client is None and models_off():
        return {**out, "status": "unavailable", "reason": f"{MODELS_ENV}=off: no generator model is reached"}
    granted = plan_fallback.is_granted(TASK, vault.root)
    # Background-quiet (Q8): no OpenRouter offer and no grant unless this command carries the owner's.
    with (nullcontext() if granted else plan_fallback.quiet()):
        if client is None:
            client, reason = resolve_client(vault, route)
        else:
            reason = transport_problem(route, client)
        if client is None or reason is not None:
            hint = ("" if granted else " If the ChatGPT plan is down, rerun this command with "
                    "LEARNLOOP_AI_FALLBACK=openrouter to use OpenRouter instead (metered, capped at "
                    f"${cap:.2f} by {CAP_SETTING}, and {PRICE_SETTING} must be set).")
            return {**out, "status": "unavailable", "reason": f"{reason}.{hint}"}
        budget_obj = SpendBudget(_caps(len(batches), subscription=subscription, cap=cap, passages=len(plan_passages)), subscription=subscription)
        calls = PaidCalls(route=route, budget=budget_obj, price_per_million=price, repository=repository,
                          owner_kind=OWNER_KIND, owner_id=space_id)
        counts = {"calls_done": 0, "questions_written": 0, "ngram_dropped": 0, "invalid_dropped": 0,
                  "passages_written": 0}
        status = "complete"
        for batch in batches:
            if cancelled():
                status = "cancelled"
                break
            # Protection read again: a block held out since the run began never reaches the model.
            allowed = {passage["key"] for passage in passages(
                vault, repository, excluded=excluded, extraction_ids={p["extraction_id"] for p in batch})}
            batch = [passage for passage in batch if passage["key"] in allowed]
            if not batch:
                continue
            prompt, refs = call_prompt(batch)
            try:
                answer = calls.call(client, purpose=TASK, prompt=prompt, result_model=GeneratedQuestionsV1,
                                    output_tokens=OUTPUT_TOKENS, metadata={"owner_id": space_id},
                                    candidates=len(batch))
            except SpendLimitExceeded as exc:
                status, out["reason"] = "capped", str(exc)[:200]
                break
            except (AIProviderUnavailable, AIInvalidOutput, TimeoutError) as exc:
                status, out["reason"] = "failed", f"{type(exc).__name__}: {str(exc)[:200]}"
                break
            counts["calls_done"] += 1
            for passage_ref, questions in validated(answer, refs).items():
                passage = refs[passage_ref]["passage"]
                asked = len([q for item in answer.passages if item.passage_ref == passage_ref for q in item.questions])
                counts["invalid_dropped"] += max(0, min(asked, SP.QUERIES_PER_PASSAGE_MAX) - len(questions))
                rows, dropped = query_rows(passage, questions, split=split_of(passage, held_out),
                                           vault=vault_key(vault), bank_grams=bank_grams)
                counts["ngram_dropped"] += dropped
                _append_jsonl(directory / "queries.jsonl", rows)
                _append_jsonl(directory / "passages.jsonl", [{"key": passage["key"], "questions": len(rows),
                                                              "prompt_version": PROMPT_VERSION}])
                counts["questions_written"] += len(rows)
                counts["passages_written"] += 1
        out["usage"] = calls.report()
    rows = current_rows(stored_queries(directory), by_extraction)
    return {**out, "status": status, **counts, "budgets": budgets_of(rows)}


__all__ = ["CAP_SETTING", "GeneratedQuestionsV1", "INTENTS", "MODELS_ENV", "OWNER_KIND", "PROMPT_VERSION", "SHAPES",
           "TASK", "bank_supports", "budgets_of", "call_prompt", "data_dir", "extraction_families", "family_map",
           "current_rows", "current_split", "family_of", "generate", "held_out_among", "held_out_family", "question_families",
           "vault_held_out",
           "load_bank", "nested", "ngram_overlap", "ngrams", "passages", "query_rows", "retrieval_text", "split_of",
           "stored_queries", "validated", "vault_key"]
