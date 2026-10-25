"""Embedding space identity (spec_local_contextual_retrieval_v1 §4.2).

Every field is part of the id, so a change to any of them is a new space;
vectors are never mixed across spaces (the preview card's own requirement).

* ``space_id``: the document space (model, revision, reviewed code digests,
  precision, fp32 modules, software epoch, window variant and rule, recipe,
  width, output and score transform). Pure: no file is read here.
* ``query_encoder_id``: which encoder made a query vector for that space.
  NOT part of the space id: a new query student never invalidates documents.
"""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from typing import Any

from learnloop.local_embeddings import pins

#: The block recipe both contextual spaces embed (``source_block/text`` v1).
RECIPE = "source_block/text v1"


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def local_space_pins(*, variant: str, software_epoch: Mapping[str, str], window_rule: str) -> dict[str, Any]:
    return {"kind": "local", "repo": pins.MODEL_REPO, "revision": pins.MODEL_REVISION,
            "code_sha256s": {name: pins.MODEL_FILES[name][1] for name in pins.REMOTE_CODE_FILES},
            "precision": pins.PRECISION, "fp32_modules": list(pins.FP32_MODULES),
            "software_epoch": dict(sorted(software_epoch.items())), "variant": variant,
            "window_rule": window_rule, "recipe": RECIPE, "dims": pins.MODEL_DIMENSIONS,
            "output": pins.OUTPUT_FORMAT, "score_transform": pins.SCORE_TRANSFORM}


def hosted_space_pins(*, provider: str, model: str, dims: int, variant: str, window_rule: str) -> dict[str, Any]:
    return {"kind": "hosted", "provider": provider, "model": model, "dims": int(dims), "variant": variant,
            "window_rule": window_rule, "recipe": RECIPE, "output": "float",
            "input_types": ["document", "query"], "score_transform": "l2_normalize_cosine"}


def space_id(space_pins: Mapping[str, Any]) -> str:
    prefix = "ls_" if space_pins.get("kind") == "local" else "hs_"
    return prefix + _digest(dict(space_pins))[:24]


def query_encoder_id(space: str, *, encoder: str, precision: str = pins.PRECISION,
                     device_class: str = "gpu", method: str = pins.QUERY_METHOD) -> str:
    """``encoder`` is ``teacher``, ``student:<checkpoint sha256>`` or a hosted model name."""

    return "qe_" + _digest({"space": space, "encoder": encoder, "method": method, "precision": precision,
                            "device": device_class})[:24]


__all__ = ["RECIPE", "hosted_space_pins", "local_space_pins", "query_encoder_id", "space_id"]
