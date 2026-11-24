"""Write one activity in caller-owned job scratch from ordered, named cells."""
from __future__ import annotations

from collections.abc import Sequence
from contextlib import suppress
import fcntl
import os
from pathlib import Path
import stat
from uuid import uuid4

from learnloop.notebook_authoring.marimo_adapter import generate, inspect_cells
from learnloop.notebook_authoring.scratch import directory_fd


def _publish(directory: int, source: str, *, replace: bool) -> None:
    temporary = f'.{uuid4().hex}.py'
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=directory)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as handle:
            handle.write(source)
        if replace:
            os.replace(temporary, 'activity.py', src_dir_fd=directory, dst_dir_fd=directory)
        else:
            os.link(temporary, 'activity.py', src_dir_fd=directory, dst_dir_fd=directory)
    finally:
        with suppress(FileNotFoundError):
            os.unlink(temporary, dir_fd=directory)


def write_cells(scratch: Path, cells: Sequence[tuple[str, str]], *, held: Sequence[str] = ()) -> Path:
    """Create activity.py exclusively. Only a successfully checked revision appears."""
    with directory_fd(scratch) as directory:
        fcntl.flock(directory, fcntl.LOCK_EX)
        _publish(directory, generate(list(cells), held=held), replace=False)
    return scratch / 'activity.py'


def edit_cell(scratch: Path, name: str, code: str) -> Path:
    """Replace a named cell in a writer-generated revision, retaining order and names."""
    with directory_fd(scratch) as directory:
        fcntl.flock(directory, fcntl.LOCK_EX)
        fd = os.open('activity.py', os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW, dir_fd=directory)
        with os.fdopen(fd, encoding='utf-8') as handle:
            entry = os.fstat(fd)
            if not stat.S_ISREG(entry.st_mode) or entry.st_nlink != 1:
                raise ValueError('Edit requires a regular job artifact with no other links.')
            original = handle.read()
        report = inspect_cells(original)
        cells = [(cell['name'], cell['code']) for cell in report['cells']]
        held = [c['name'] for c in report['cells'] if c['options'].get('disabled')]
        if report['findings'] or generate(cells, held=held) != original:
            raise ValueError('Edit requires a notebook produced by write_cells.')
        if name not in dict(cells):
            raise ValueError(f'Unknown cell: {name!r}')
        updated = [(n, code if n == name else old) for n, old in cells]
        _publish(directory, generate(updated, held=held), replace=True)
    return scratch / 'activity.py'
