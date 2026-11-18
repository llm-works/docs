# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Generated API reference pages: one per top-level module, rendered by mkdocstrings."""

from pathlib import Path

from .config import NavItem, Package, Reference

REFERENCE_DIR = "reference"
NAV_TITLE = "API reference"


class ReferenceSourceError(RuntimeError):
    """The package to document is not where the reference config points."""


def reference_modules(checkout: Path, ref: Reference) -> list[str]:
    """The package's public top-level modules and subpackages, as dotted names, sorted."""
    root = checkout / ref.source / ref.package
    if not (root / "__init__.py").is_file() or root.is_symlink():
        raise ReferenceSourceError(f"{root} is not a package directory")
    modules = []
    for entry in sorted(root.iterdir()):
        name = entry.stem if entry.suffix == ".py" else entry.name
        if name.startswith("_") or entry.is_symlink():
            continue
        is_module = entry.is_file() and entry.suffix == ".py"
        if is_module or (entry / "__init__.py").is_file():
            modules.append(f"{ref.package}.{name}")
    return modules


def reference_pages(pkg: Package, modules: list[str]) -> dict[str, str]:
    """Page text by path under <name>/: an index, then one page per module."""
    pages = {f"{REFERENCE_DIR}/index.md": _index_page(pkg, modules)}
    for module in modules:
        pages[_module_path(module)] = f"# {module}\n\n::: {module}\n"
    return pages


def reference_nav(modules: list[str]) -> NavItem:
    """The API reference section: the index, then each module by its short name."""
    entries: list[NavItem] = [f"{REFERENCE_DIR}/index.md"]
    entries += [{module.split(".", 1)[1]: _module_path(module)} for module in modules]
    return {NAV_TITLE: entries}


def _module_path(module: str) -> str:
    """The page of a module, under reference/."""
    return f"{REFERENCE_DIR}/{module.split('.', 1)[1]}.md"


def _index_page(pkg: Package, modules: list[str]) -> str:
    """The reference landing page: what it is generated from, and every module."""
    links = "\n".join(f"- [`{m}`]({m.split('.', 1)[1]}.md)" for m in modules)
    return (
        f"# {NAV_TITLE}\n\n"
        f"Generated from the docstrings and type hints of {pkg.name} {pkg.tag}. Each page covers "
        "one top-level module and its submodules.\n\n"
        f"{links}\n"
    )
