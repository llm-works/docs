# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Assemble the site's docs directory: select each package's allowlisted docs, then sync."""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from appinfra.log import Logger

from .config import Package

# What a docs file is made from: a file to copy, or generated text
Source = Path | str


class StageError(RuntimeError):
    """A package's docs do not match its allowlist, or two sources claim one docs path."""


@dataclass(frozen=True)
class Selection:
    """How a package's docs directory compares with its allowlist."""

    copy: tuple[str, ...]
    missing: tuple[str, ...]
    unlisted: tuple[str, ...]


def select(available: Iterable[str], allowlist: Sequence[str]) -> Selection:
    """Split docs files into those to copy, listed-but-absent, and present-but-unlisted."""
    present = set(available)
    listed = set(allowlist)
    return Selection(
        copy=tuple(path for path in allowlist if path in present),
        missing=tuple(path for path in allowlist if path not in present),
        unlisted=tuple(sorted(present - listed)),
    )


class DocsStager:
    """Maps a checkout's allowlisted docs to their site paths, relative to the package's dir."""

    def __init__(self, lg: Logger) -> None:
        self._lg = lg

    def files(self, pkg: Package, checkout: Path) -> dict[str, Path]:
        """Site path (renames applied) -> source file; fail on a missing file."""
        source = checkout / pkg.docs_root
        sel = select(_list_files(source), pkg.files)
        if sel.missing:
            raise StageError(f"{pkg.name} {pkg.ref}: allowlisted docs missing: {list(sel.missing)}")
        if sel.unlisted:
            self._lg.info(
                "docs not in allowlist, skipped",
                extra={"package": pkg.name, "files": list(sel.unlisted)},
            )
        return {pkg.site_path(path): source / path for path in sel.copy}


def merge(plan: dict[str, Source], files: Mapping[str, Source], owner: str) -> None:
    """Add `files` to `plan`; a path that is already taken is an error, never an overwrite."""
    taken = sorted(plan.keys() & files.keys())
    if taken:
        raise StageError(f"{owner}: docs paths already taken by another source: {taken}")
    plan.update(files)


def sync_tree(lg: Logger, plan: Mapping[str, Source], root: Path) -> None:
    """Make `root` hold exactly `plan`: write changed files, remove the rest.

    Files are updated in place rather than by recreating the directory, so a live-reload server
    watching `root` keeps seeing changes.
    """
    written = 0
    for rel, src in plan.items():
        data = src.read_bytes() if isinstance(src, Path) else src.encode("utf-8")
        target = root / rel
        if target.is_file() and target.read_bytes() == data:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        written += 1
    removed = _remove_extras(root, set(plan))
    lg.info("docs synced", extra={"files": len(plan), "written": written, "removed": removed})


def _remove_extras(root: Path, keep: set[str]) -> int:
    """Delete files under `root` not in `keep`, then directories left empty."""
    removed = 0
    for path in sorted(root.rglob("*"), reverse=True):
        rel = path.relative_to(root).as_posix()
        if (path.is_file() or path.is_symlink()) and rel not in keep:
            path.unlink()
            removed += 1
        elif path.is_dir() and not any(path.iterdir()):
            path.rmdir()
    return removed


def _list_files(root: Path) -> list[str]:
    """Every file and symlink under `root`, as POSIX paths relative to it."""
    if not root.is_dir():
        return []
    entries = (p for p in root.rglob("*") if p.is_symlink() or p.is_file())
    return [p.relative_to(root).as_posix() for p in entries]
