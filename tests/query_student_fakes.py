"""Local retrieval P2 test doubles: a vault with three teaching sources indexed by the fake 9B, a
fake question generator, a tiny random-initialised student (torch on the CPU, no download), an
in-process trainer launcher under the real P2 meter, and a numpy query service. No test here
starts a process, sends a request or downloads a model."""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
import threading
from typing import Any

import numpy as np

from learnloop.ai.execution import report_call_usage
from learnloop.local_embeddings import pins
from learnloop.local_embeddings import student_pins as SP
from learnloop.source_retrieval import local_index
from learnloop.source_retrieval import student_data as D
from tests.helpers import append_config_toml
from tests.local_embeddings_fakes import FakeLocalModel, InProcessLauncher, no_locks, set_up_data_root
from tests.pf_fakes import prompt_context
from tests.source_retrieval_fakes import build_retrieval_vault, loaded, seed_source

PROBABILITY = {
    "ch_total": ("Chapter 2 Total probability", [
        ("The law of total probability splits an event across a partition of the sample space.", 7),
        ("Each piece is the conditional probability times the probability of the partition cell.", 7),
    ]),
    "ch_bayes": ("Chapter 3 Bayes", [
        ("Bayes' rule reverses a conditional probability using the prior and the likelihood.", 9),
        ("The posterior is proportional to the likelihood times the prior.", 9),
    ]),
}
CALCULUS = {
    "ch_power": ("Chapter 1 Derivatives", [
        ("The power rule says the derivative of x to the n is n times x to the n minus one.", 2),
        ("The chain rule differentiates a composition by multiplying the outer and inner derivatives.", 3),
    ]),
}
BANK_QUESTION = "Why are the eigenvalues of a real symmetric matrix real numbers"


def student_vault(tmp_path: Path, *, extra: str = ""):
    """The retrieval vault plus two more teaching sources, local space on and indexed."""

    paths, repository = build_retrieval_vault(tmp_path / "vault")
    seed_source(repository, source_id="src_prob", revision_id="rev_prob", extraction_id="ext_prob",
                title="Probability Notes", units=PROBABILITY)
    seed_source(repository, source_id="src_calc", revision_id="rev_calc", extraction_id="ext_calc",
                title="Calculus Notes", units=CALCULUS)
    append_config_toml(paths.root, "[embedding.local]\nenabled = true\n" + extra)
    root = pins.data_root()
    root.mkdir(parents=True, exist_ok=True)
    set_up_data_root(root)
    model = FakeLocalModel()
    report = local_index.run_local_index(loaded(paths), repository, launcher=InProcessLauncher(model),
                                         preflight=lambda: [], locks=no_locks, force=True)
    assert report["status"] == "complete", report
    return paths, repository, root, model, report


def write_bank(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.write_text(json.dumps(rows), encoding="utf-8")
    return path


def default_bank(tmp_path: Path, repository) -> Path:
    """One bank question; its gold support is the symmetric-matrix block (never in a prompt)."""

    gold = find_gold(repository)
    return write_bank(tmp_path / "bank.json", [{
        "query_id": "bank_1", "question": BANK_QUESTION, "family": "src_book", "vault": "linear_algebra",
        "origin": "written", "evidence_sets": [{"set_id": "e1", "required": [["ext_book", gold, 0, 10]]}]}])


def find_gold(repository) -> str:
    """The span id of the 'Real symmetric matrices ...' block in the fixture book."""

    from contextlib import closing

    from learnloop.db.connection import connect
    from learnloop.db.stores.source_block_fts import extraction_blocks

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        for block in extraction_blocks(connection, "ext_book"):
            if block.text.startswith("Real symmetric matrices"):
                return block.span_id
    raise AssertionError("the fixture book has no symmetric-matrix block")


class FakeGenerator:
    """The question generator: for every passage, ``per`` questions (one deictic about its first
    block, one copying the bank question when ``leak``), every support a real block ref."""

    provider_name = "fake_generator"
    model = "fake-gpt-6-luna"

    def __init__(self, *, provider_type: str = "chatgpt_plan", per: int = 8, leak: bool = False) -> None:
        self.provider_type = provider_type
        self.per = per
        self.leak = leak
        self.prompts: list[str] = []

    def supports(self, capability: str) -> bool:
        return capability in {"structured_completion", "bounded_structured_completion", "isolated_turn"}

    def complete(self, request):
        assert request.result_model is D.GeneratedQuestionsV1
        self.prompts.append(request.prompt)
        report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 200,
                           "resolved_model": self.model})
        out = []
        for passage in prompt_context(request.prompt)["passages"]:
            refs = [block["ref"] for block in passage["blocks"]]
            questions = []
            for index in range(self.per):
                shape = "deictic" if index == 0 else ("paraphrase" if index % 2 else "plain")
                text = f"question {index} about {passage['passage_ref']} {passage['blocks'][0]['text'][:40]}"
                if self.leak and index == 1:
                    text = BANK_QUESTION
                questions.append({"text": text, "intent": D.INTENTS[index % len(D.INTENTS)], "shape": shape,
                                  "supports": [refs[index % len(refs)]],
                                  "selection_ref": refs[0] if shape == "deictic" else None})
            out.append({"passage_ref": passage["passage_ref"], "questions": questions})
        return D.GeneratedQuestionsV1.model_validate({"passages": out})


# -- the tiny student ------------------------------------------------------------------------------
class TinyTokenizer:
    """Word-hash ids (no download), right padding, an attention mask."""

    def __init__(self, vocab: int = 257) -> None:
        self.vocab = vocab

    def __call__(self, texts, *, padding=True, truncation=True, max_length=512, return_tensors="pt"):
        import torch

        rows = [[1 + int(hashlib.sha256(word.encode()).hexdigest()[:6], 16) % (self.vocab - 1)
                 for word in str(text).lower().split()][:max_length] or [1] for text in texts]
        width = max(len(row) for row in rows)
        ids = torch.zeros((len(rows), width), dtype=torch.long)
        mask = torch.zeros((len(rows), width), dtype=torch.long)
        for index, row in enumerate(rows):
            ids[index, :len(row)] = torch.tensor(row)
            mask[index, :len(row)] = 1
        return {"input_ids": ids, "attention_mask": mask}


def tiny_model():
    """A tiny random-initialised Qwen3 (the pplx-embed-v1 architecture), no download."""

    import torch
    from transformers import Qwen3Config, Qwen3Model

    torch.manual_seed(0)
    config = Qwen3Config(vocab_size=257, hidden_size=32, intermediate_size=64, num_hidden_layers=2,
                         num_attention_heads=2, num_key_value_heads=1, head_dim=16, max_position_embeddings=128)
    return Qwen3Model(config)


def tiny_factory(_base_dir: Path, _base: Mapping[str, Any], *, device: str):
    """Signature-faithful to ``student_trainer.load_base`` (device keyword-only, Codex review F1)."""

    import torch
    from transformers import Qwen3Config, Qwen3Model

    torch.manual_seed(0)
    config = Qwen3Config(vocab_size=257, hidden_size=32, intermediate_size=64, num_hidden_layers=2,
                         num_attention_heads=2, num_key_value_heads=1, head_dim=16, max_position_embeddings=128)
    return Qwen3Model(config).to(device), TinyTokenizer()


class InProcessTrainer:
    """The trainer's ``run_training`` in this process with the tiny student, under the real meter."""

    def __init__(self, *, device: str = "cpu", fail: bool = False) -> None:
        self.device = device
        self.fail = fail
        self.jobs: list[dict[str, Any]] = []

    def __call__(self, job: dict[str, Any], workdir: Path, *, meter: Any, plan_id: str) -> dict[str, Any]:
        from learnloop.local_embeddings import student_trainer

        entry, deadline = meter.open(plan_id=plan_id, label=workdir.name, min_slot_s=0)
        self.jobs.append(job)
        try:
            if self.fail:
                return {"status": "failed", "reason": "fake failure", "supervised": {"charged_s": 1.0}}
            output = student_trainer.run_training(job, model_factory=tiny_factory, device=self.device,
                                                  base_check=lambda _job: [])
            output["supervised"] = {"charged_s": 2.0}
            return output
        finally:
            meter.close(entry, status="exited", returncode=0)


def set_up_bases(root: Path) -> None:
    bases = {}
    for name in SP.SCREEN_BASES:
        directory = root / "fake-bases" / name
        directory.mkdir(parents=True, exist_ok=True)
        bases[name] = {"dir": str(directory), "repo": SP.STUDENT_BASES[name]["repo"],
                       "revision": SP.STUDENT_BASES[name]["revision"], "adopted": True, "weights_verified": True}
    SP.bases_manifest_path(root).parent.mkdir(parents=True, exist_ok=True)
    SP.bases_manifest_path(root).write_text(json.dumps({"version": 1, "bases": bases}), encoding="utf-8")


# -- the numpy query service -------------------------------------------------------------------------
class TeacherService:
    """Query vectors from the fake 9B's query method (a student that matches its teacher)."""

    def __init__(self, model: FakeLocalModel | None = None) -> None:
        self.model = model or FakeLocalModel()
        self.calls: list[list[str]] = []

    def encode(self, texts):
        self.calls.append(list(texts))
        return [list(map(float, row[0])) for row in self.model.encode_queries(list(texts))]


def thread_spawn(service: Any, canaries: Mapping[str, Any] | None = None):
    """A ``spawn`` for :class:`StudentEncoder`: the real ``serve_forever`` in a thread, the status file
    written as the real process writes it. Returns ``(spawn, threads)``."""

    from learnloop.local_embeddings import student_server

    threads: list[threading.Thread] = []

    def spawn(command, *, env, log):
        job = json.loads(Path(command[command.index("--job") + 1]).read_text(encoding="utf-8"))
        status = Path(job["status_path"])

        def ready():
            student_server.W._atomic_json(status, {"status": "ready", "device": "cpu", "pid": __import__("os").getpid(),
                                                   "checkpoint_sha256": job["checkpoint_sha256"],
                                                   "started_unix": __import__("time").time(), "start_s": 0.01,
                                                   "socket": job["socket_path"]})

        thread = threading.Thread(target=student_server.serve_forever, args=(service, Path(job["socket_path"])),
                                  kwargs={"idle_s": 5.0, "timeout_s": 0.2, "ready": ready}, daemon=True)
        thread.start()
        threads.append(thread)
        return type("P", (), {"pid": __import__("os").getpid()})()

    return spawn, threads


def unit(vector) -> np.ndarray:
    array = np.asarray(vector, dtype=np.float64)
    return array / np.linalg.norm(array)
