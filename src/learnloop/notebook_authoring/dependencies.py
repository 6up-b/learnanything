"""Pinned notebook dependencies from LearnLoop distribution metadata."""
from importlib import metadata

from learnloop.notebook_authoring.marimo_adapter import NotebookDependencyError


def notebook_pins() -> dict[str, str]:
    pins = {}
    for requirement in metadata.requires('learnloop') or ():
        dep, _, marker = requirement.partition(';')
        if marker.strip().replace('"', "'") != "extra == 'notebook'":
            continue
        name, exact, pin = dep.strip().partition('==')
        try:
            installed = metadata.version(name)
        except metadata.PackageNotFoundError:
            installed = None
        if not exact or installed != pin:
            raise NotebookDependencyError(f'Install the exact notebook extra requirement {dep.strip()}.')
        pins[name] = pin
    if not {'marimo', 'wigglystuff'} <= pins.keys():
        raise NotebookDependencyError('Missing pinned notebook extra requirements.')
    return pins
