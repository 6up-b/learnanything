"""Descriptor-relative operations on an explicitly supplied job directory."""
from contextlib import contextmanager
import os
from pathlib import Path


@contextmanager
def directory_fd(path: Path, *, create: bool = False):
    if '..' in path.parts:
        raise ValueError('parent traversal is not allowed')
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    path = path.absolute()
    fd = os.open(path.anchor, flags)
    try:
        for component in path.parts[1:]:
            try:
                child = os.open(component, flags, dir_fd=fd)
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(component, mode=0o700, dir_fd=fd)
                child = os.open(component, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)
