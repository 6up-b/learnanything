from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML


def _yaml() -> YAML:
    yaml = YAML()
    yaml.default_flow_style = False
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    return yaml


def read_yaml(path: Path) -> dict[str, Any]:
    yaml = _yaml()
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected mapping at {path}")
    return loaded


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    yaml = _yaml()
    with path.open("w", encoding="utf-8") as handle:
        yaml.dump(data, handle)


def yaml_to_string(data: dict[str, Any]) -> str:
    yaml = _yaml()
    stream = StringIO()
    yaml.dump(data, stream)
    return stream.getvalue()


def read_markdown_with_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    _, rest = text.split("---\n", 1)
    frontmatter_text, body = rest.split("\n---\n", 1)
    yaml = _yaml()
    metadata = yaml.load(frontmatter_text) or {}
    if not isinstance(metadata, dict):
        raise ValueError(f"Expected frontmatter mapping at {path}")
    return metadata, body


def write_markdown_with_frontmatter(path: Path, metadata: dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    yaml = _yaml()
    stream = StringIO()
    yaml.dump(metadata, stream)
    frontmatter = stream.getvalue().strip()
    normalized_body = body if body.endswith("\n") else body + "\n"
    path.write_text(f"---\n{frontmatter}\n---\n\n{normalized_body}", encoding="utf-8")
