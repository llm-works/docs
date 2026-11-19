# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Griffe extension: a package's names from other packages listed and linked, not documented
twice.

The reference has a page per package (docsite/reference.py), and a package's API is what its
__init__ exports. What it exports from its own files is documented in full on its page. A name
it re-exports from another package (`from ..config import Config`, or from a subpackage) is
documented on that package's page when that package exports it too; this extension takes such a
name off the exporting package and adds an Exports table to its docstring instead, each name
linked to that page. Any other name stays documented in full where it is exported.
Loaded by mkdocstrings from zensical.base.toml as `docsite/reexports.py:Exports`.
"""

from collections.abc import Iterator
from typing import Any

from griffe import (
    Alias,
    AliasResolutionError,
    CyclicAliasError,
    Docstring,
    Extension,
    GriffeLoader,
    Module,
    Object,
)

_HEADER = (
    "**Exports**, documented in the package that defines them:\n\n| Name | Package |\n|---|---|\n"
)


class Exports(Extension):
    """Replaces each package's re-exports from other packages with an Exports table."""

    def on_package(self, *, pkg: Module, loader: GriffeLoader, **kwargs: Any) -> None:
        """Rewrite every package of the loaded package."""
        for package in _packages(pkg):
            rows = [_row(name, *place) for name, place in _take_exports(package)]
            if rows:
                _append(package, _HEADER + "\n".join(rows), loader)


def _packages(module: Module) -> Iterator[Module]:
    """The package and all its subpackages; plain modules have no pages. (griffe's is_package
    holds only for the top-level package; every package is an __init__ module.)"""
    yield module
    for submodule in module.modules.values():
        if isinstance(submodule, Module) and submodule.is_init_module:
            yield from _packages(submodule)


def _take_exports(package: Module) -> list[tuple[str, tuple[Module, str, Object]]]:
    """Remove the package's public re-exports documented on another package's page; return each
    name with that package, the name it has there, and the object."""
    taken = []
    for name, member in list(package.members.items()):
        if isinstance(member, Alias) and member.is_public:
            place = _documented_on(member, package)
            if place is not None:
                package.del_member(name)
                taken.append((name, place))
    return taken


def _documented_on(alias: Alias, package: Module) -> tuple[Module, str, Object] | None:
    """The other public package that defines and exports the alias's object, its name there,
    and the object; None when the object is documented here (defined in this package, or not
    exported where it is defined) or comes from outside."""
    try:
        target = alias.final_target
    except (AliasResolutionError, CyclicAliasError):
        return None  # outside the loaded package
    if isinstance(target, Alias) or target.is_module or target.package is not package.package:
        return None
    owner = target.module if target.module.is_init_module else target.module.parent
    if not isinstance(owner, Module) or owner is package:
        return None
    if any(part.startswith("_") for part in owner.path.split(".")):
        return None
    name = _exported_name(owner, target)
    return None if name is None else (owner, name, target)


def _exported_name(package: Module, target: Object) -> str | None:
    """The public name under which `package` exports `target`, or None."""
    for name, member in package.members.items():
        if not member.is_public:
            continue
        if member is target:
            return name
        if isinstance(member, Alias):
            try:
                if member.final_target is target:
                    return name
            except (AliasResolutionError, CyclicAliasError):
                continue
    return None


def _row(name: str, owner: Module, owner_name: str, target: Object) -> str:
    """A table row: the name, linked to where it is documented when it has docstrings
    (mkdocstrings skips an object without), and that package."""
    shown = f"[`{name}`][{owner.path}.{owner_name}]" if target.has_docstrings else f"`{name}`"
    return f"| {shown} | `{owner.path}` |"


def _append(module: Module, text: str, loader: GriffeLoader) -> None:
    """Append `text` to the module's docstring, creating one if it has none."""
    if module.docstring is not None:
        module.docstring.value = f"{module.docstring.value}\n\n{text}"
    else:
        module.docstring = Docstring(
            text,
            parent=module,
            parser=loader.docstring_parser,
            parser_options=loader.docstring_options,
        )
