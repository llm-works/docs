# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Render the Zensical config: the tracked base, with each package's docs tree in the nav."""

import copy
from collections.abc import Mapping, Sequence
from typing import Any

from .config import NavItem
from .navtree import map_paths

PACKAGES_SECTION = "Packages"


class SiteConfigError(RuntimeError):
    """The base config has no place for a configured package."""


def render_site_config(
    base: Mapping[str, Any],
    trees: Mapping[str, list[NavItem]],
    reference_sources: Sequence[str],
) -> dict[str, Any]:
    """Return `base` with each package's `{name: name/index.md}` nav entry expanded.

    The base lists every package under the Packages section by its landing page. `trees` maps a
    package name to its tree, with paths relative to the package's directory; the tree goes below
    the landing page. `reference_sources` are the checkout directories mkdocstrings reads.
    """
    config = copy.deepcopy(dict(base))
    section = _packages_section(config)
    for name, tree in trees.items():
        _expand(section, name, tree)
    if reference_sources:
        project = config.setdefault("project", {})
        handler = project.setdefault("plugins", {}).setdefault("mkdocstrings", {})
        handler.setdefault("handlers", {}).setdefault("python", {})["paths"] = list(
            reference_sources
        )
    return config


def _packages_section(config: dict[str, Any]) -> list[Any]:
    """The list under {"Packages": [...]} in project.nav."""
    nav = config.get("project", {}).get("nav", [])
    for item in nav:
        if isinstance(item, dict) and isinstance(item.get(PACKAGES_SECTION), list):
            section: list[Any] = item[PACKAGES_SECTION]
            return section
    raise SiteConfigError(f"base config has no {PACKAGES_SECTION!r} section in project.nav")


def _expand(section: list[Any], name: str, tree: list[NavItem]) -> None:
    """Replace the package's landing entry with its landing page plus `tree`."""
    landing = f"{name}/index.md"
    for i, item in enumerate(section):
        if item == {name: landing}:
            section[i] = {name: [landing, *map_paths(tree, lambda path: f"{name}/{path}")]}
            return
    raise SiteConfigError(f"{PACKAGES_SECTION} has no entry {{{name!r}: {landing!r}}}")
