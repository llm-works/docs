# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Nav trees: a package's configured `docs` tree, with each path where it is staged, and a
generated page for each section that has none."""

import posixpath
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .config import NavItem, Package
from .markdown import prose_flags

# Zensical takes a section's first entry as the section's own page when it is one of these
INDEX_NAMES = ("index.md", "README.md")

_HEADING = re.compile(r"#\s+(.+?)(?:\s+#+)?\s*$")
_FRONT_TITLE = re.compile(r"title:\s*(.+)$")


class NavTreeError(ValueError):
    """A nav tree the site cannot build pages for."""


@dataclass(frozen=True)
class SectionIndex:
    """A generated page for a section without one: the section's title and its entries."""

    title: str
    entries: tuple[NavItem, ...]


def package_nav(pkg: Package) -> list[NavItem]:
    """The package's docs tree with renames applied, paths relative to the package's directory."""
    return map_paths(pkg.docs, pkg.site_path)


def map_paths(items: Sequence[NavItem], fn: Callable[[str], str]) -> list[NavItem]:
    """The tree with `fn` applied to every path; titles and sections are kept."""
    out: list[NavItem] = []
    for item in items:
        if isinstance(item, str):
            out.append(fn(item))
            continue
        ((title, value),) = item.items()
        out.append({title: fn(value) if isinstance(value, str) else map_paths(value, fn)})
    return out


def index_sections(
    items: Sequence[NavItem], base: str = ""
) -> tuple[list[NavItem], dict[str, SectionIndex]]:
    """The tree with a generated index page first in every section that has no page of its own.

    Every item in the tree then opens a page. A generated page sits at the section's titles
    slugged under `base` (Guides > Configuration: guides/configuration/index.md). Returns the
    tree and the generated pages by path; a path a source already takes fails at staging.
    """
    out: list[NavItem] = []
    pages: dict[str, SectionIndex] = {}
    for item in items:
        if isinstance(item, str) or isinstance(next(iter(item.values())), str):
            out.append(item)
            continue
        ((title, value),) = item.items()
        folder = posixpath.join(base, _slug(title))
        entries, nested = index_sections(value, folder)
        pages.update(nested)
        if not _has_page(entries):
            path = posixpath.join(folder, "index.md")
            pages[path] = SectionIndex(title, tuple(entries))
            entries = [path, *entries]
        out.append({title: entries})
    return out, pages


def render_section_index(path: str, index: SectionIndex, title_of: Callable[[str], str]) -> str:
    """The Markdown of a generated section page: its title, then a link to each entry.

    An entry without a title is titled by `title_of(path)`, the page's own heading, as in the
    tree; a section links to its own page, its first entry.
    """
    folder = posixpath.dirname(path)
    lines = [f"# {index.title}", ""]
    for entry in index.entries:
        title, target = _entry_link(entry, title_of)
        lines.append(f"- [{_escape(title)}]({posixpath.relpath(target, folder)})")
    return "\n".join(lines) + "\n"


def page_title(text: str, path: str) -> str:
    """A page's title as the site shows it: the front matter's `title`, else the first level-1
    heading, else the file name."""
    lines = text.splitlines()
    body = lines
    if lines and lines[0].strip() == "---":
        end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), 0)
        for line in lines[1:end]:
            match = _FRONT_TITLE.match(line)
            if match:
                return match.group(1).strip().strip("\"'")
        body = lines[end + 1 :]
    return _heading(body) or _file_title(path)


def _heading(lines: Sequence[str]) -> str | None:
    """The first level-1 heading outside fenced code."""
    for line, prose in zip(lines, prose_flags(lines), strict=True):
        match = _HEADING.match(line) if prose else None
        if match:
            return match.group(1)
    return None


def _file_title(path: str) -> str:
    """A title from the file name: "getting-started.md" -> "Getting started"."""
    stem = posixpath.splitext(posixpath.basename(path))[0]
    return stem.replace("-", " ").replace("_", " ").capitalize()


def _has_page(entries: Sequence[NavItem]) -> bool:
    """Whether the section's first entry is a page the site takes as the section's own."""
    if not entries:
        return False
    first = entries[0]
    path = first if isinstance(first, str) else next(iter(first.values()))
    return isinstance(path, str) and posixpath.basename(path) in INDEX_NAMES


def _entry_link(entry: NavItem, title_of: Callable[[str], str]) -> tuple[str, str]:
    """An entry's title and the path its link goes to."""
    if isinstance(entry, str):
        return title_of(entry), entry
    ((title, value),) = entry.items()
    if isinstance(value, str):
        return title, value
    first = value[0]
    return title, first if isinstance(first, str) else next(iter(first.values()))


def _slug(title: str) -> str:
    """A section title as a path segment: "Development tooling" -> "development-tooling"."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    if not slug:
        raise NavTreeError(f"section title has no letters or digits for its page path: {title!r}")
    return slug


def _escape(title: str) -> str:
    """A title as Markdown link text."""
    return title.replace("[", r"\[").replace("]", r"\]")
