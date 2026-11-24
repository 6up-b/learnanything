"""Read an explicit artifact and write a structure-only report to explicit scratch."""
from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
from typing import Iterator

from learnloop.notebook_authoring.marimo_adapter import inspect_structure
from learnloop.notebook_authoring.scratch import directory_fd


class OutputPathError(ValueError):
    """The requested output cannot be confined without overwriting existing data."""


@contextmanager
def _output_directory(path: Path, names: tuple[str, ...]) -> Iterator[int]:
    if '..' in path.parts:
        raise OutputPathError('parent traversal is not allowed')
    absolute = path.absolute()
    # Reports may contain private code facts; a checkout is never an output store.
    if any((parent / '.git').is_file() or (parent / '.git/HEAD').is_file()
           for parent in (absolute, *absolute.parents)):
        raise OutputPathError('choose an output directory outside the checkout')
    try:
        with directory_fd(absolute, create=True) as directory:
            # Exclusive creation also refuses a link planted after this preflight.
            for name in names:
                try:
                    os.stat(name, dir_fd=directory, follow_symlinks=False)
                except FileNotFoundError:
                    continue
                raise OutputPathError(f'{name} already exists; choose a fresh output directory')
            yield directory
    except OSError as exc:
        raise OutputPathError('output must use real directories and unused report files, without symlinks') from exc


def check_structure(path: Path, out: Path) -> tuple[dict, str]:
    """Return the report and summary; the source is never imported or modified."""
    if path.suffix != '.py':
        raise ValueError('The structure checker takes a marimo .py notebook.')
    report = inspect_structure(path.read_text(encoding='utf-8'))
    report.update(scope='structure', structure_status='failed' if report['findings'] else 'passed',
                  review_status='incomplete', accepted=False, execution_performed=False,
                  review_layers_performed=[])
    summary = (f"Structure only: {report['structure_status']}; {len(report['cells'])} cells; "
               f"{len(report['findings'])} findings.\n"
               'Review incomplete: no execution, no review layers; not acceptance.\n')
    write_reports(out, 'structure', report, summary)
    return report, summary


def write_reports(out, scope, report, summary, *, manifest=None):
    files = {f'{scope}.json': json.dumps(report, indent=2) + '\n', f'{scope}.txt': summary}
    if manifest is not None:
        files['manifest.json'] = json.dumps(manifest, indent=2) + '\n'
    with _output_directory(out, tuple(files)) as directory:
        for name, contents in files.items():
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
            with os.fdopen(fd, 'w', encoding='utf-8') as handle:
                handle.write(contents)
