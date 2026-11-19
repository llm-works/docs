# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Generated API reference pages: one per package and subpackage, rendered by mkdocstrings.

A package's API is what its __init__ exports. The tree under API reference follows the
subpackages; a subpackage with subpackages of its own is a section led by its page. A page links
its subpackages, then mkdocstrings renders the package: its docstring, with the Exports table
docsite/reexports.py adds for names documented on another package's page, and in full what the
package defines and exports from its own files. The reference's own page does the same for the
package's top level.
"""

from pathlib import Path

from .config import NavItem, Package, Reference

REFERENCE_DIR = "reference"
NAV_TITLE = "API reference"


class ReferenceSourceError(RuntimeError):
    """The package to document is not where the reference config points."""


def reference_modules(checkout: Path, ref: Reference) -> list[str]:
    """The package's public subpackages at every depth, as dotted names: siblings sorted, a
    package before its subpackages. A package's own .py files have no pages: what it exports
    from them is documented on the package's page."""
    root = checkout / ref.source / ref.package
    if not (root / "__init__.py").is_file() or root.is_symlink():
        raise ReferenceSourceError(f"{root} is not a package directory")
    return _walk(root, ref.package)


def _walk(folder: Path, dotted: str) -> list[str]:
    """The public subpackages under `folder`, the package `dotted`, recursively."""
    packages = []
    for entry in sorted(folder.iterdir()):
        if entry.name.startswith("_") or entry.is_symlink():
            continue
        if (entry / "__init__.py").is_file():
            packages.append(f"{dotted}.{entry.name}")
            packages += _walk(entry, f"{dotted}.{entry.name}")
    return packages


def reference_pages(pkg: Package, modules: list[str]) -> dict[str, str]:
    """Page text by path under <name>/: the reference's own page, then one page per
    subpackage in `modules`."""
    if pkg.reference is None:
        return {}
    parents = _parents(modules)
    root = pkg.reference.package
    pages = {f"{REFERENCE_DIR}/index.md": _index_page(pkg, root, modules, parents)}
    for module in modules:
        page = f"# {module}\n\n{_subpackages(module, modules, parents)}::: {module}\n"
        pages[_module_path(module, parents)] = page
    return pages


def reference_nav(modules: list[str]) -> NavItem:
    """The API reference section: its own page, then the subpackage tree by short names."""
    root = modules[0].split(".")[0] if modules else ""
    entries = _nav_entries(root, modules, _parents(modules))
    return {NAV_TITLE: [f"{REFERENCE_DIR}/index.md", *entries]}


def _nav_entries(parent: str, modules: list[str], parents: set[str]) -> list[NavItem]:
    """The nav entries of `parent`'s subpackages; one with subpackages of its own is a section
    led by its page."""
    entries: list[NavItem] = []
    for module in _children(parent, modules):
        short, page = module.rpartition(".")[2], _module_path(module, parents)
        if module in parents:
            entries.append({short: [page, *_nav_entries(module, modules, parents)]})
        else:
            entries.append({short: page})
    return entries


def _parents(modules: list[str]) -> set[str]:
    """The packages that have subpackages."""
    return {module.rpartition(".")[0] for module in modules}


def _children(parent: str, modules: list[str]) -> list[str]:
    """The direct subpackages of `parent`, in order."""
    return [module for module in modules if module.rpartition(".")[0] == parent]


def _module_path(module: str, parents: set[str]) -> str:
    """The page of a package under reference/: one with subpackages gets a folder."""
    rel = module.split(".", 1)[1].replace(".", "/")
    return f"{REFERENCE_DIR}/{rel}/index.md" if module in parents else f"{REFERENCE_DIR}/{rel}.md"


def _subpackages(module: str, modules: list[str], parents: set[str]) -> str:
    """A line linking `module`'s subpackages from its page; empty if it has none."""
    links = _links(module, modules, parents)
    return f"Subpackages: {links}\n\n" if links else ""


def _links(parent: str, modules: list[str], parents: set[str]) -> str:
    """Links to `parent`'s subpackages from the folder of `parent`'s page, where each one is
    <name>.md or, with subpackages of its own, <name>/index.md."""
    return ", ".join(
        f"[`{name}`]({name}/index.md)" if child in parents else f"[`{name}`]({name}.md)"
        for child in _children(parent, modules)
        for name in [child.rpartition(".")[2]]
    )


def _index_page(pkg: Package, root: str, modules: list[str], parents: set[str]) -> str:
    """The reference's own page: what it is generated from, the top-level subpackages, and the
    package's top level rendered like a subpackage's page."""
    links = _links(root, modules, parents)
    return (
        f"# {NAV_TITLE}\n\n"
        f"Generated from the docstrings and type hints of {pkg.name} {pkg.ref}. Each page covers "
        "one package: its subpackages, the names it re-exports from other packages, and its own "
        "API in full.\n\n" + (f"Packages: {links}\n\n" if links else "") + f"::: {root}\n"
    )
