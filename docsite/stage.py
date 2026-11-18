# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Stage a fetched package's allowlisted docs into the site's docs directory."""

import shutil
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from appinfra.log import Logger

from .config import Package


class StageError(RuntimeError):
    """A package's docs do not match its allowlist."""


@dataclass(frozen=True)
class Selection:
    """How a package's docs/ compares with its allowlist."""

    copy: tuple[str, ...]
    missing: tuple[str, ...]
    unlisted: tuple[str, ...]


def select(available: Iterable[str], allowlist: Sequence[str]) -> Selection:
    """Split docs/ files into those to copy, listed-but-absent, and present-but-unlisted."""
    present = set(available)
    listed = set(allowlist)
    return Selection(
        copy=tuple(path for path in allowlist if path in present),
        missing=tuple(path for path in allowlist if path not in present),
        unlisted=tuple(sorted(present - listed)),
    )


class DocsStager:
    """Copies allowlisted docs from a checkout to <docs_dir>/<name>/guides."""

    def __init__(self, lg: Logger, docs_dir: Path) -> None:
        self._lg = lg
        self._docs_dir = docs_dir

    def stage(self, pkg: Package, checkout: Path) -> Path:
        """Copy `pkg`'s allowlisted docs; fail if any listed file is missing or a symlink."""
        source = checkout / "docs"
        # rglob follows a symlinked root, which would list files from wherever it points.
        if source.is_symlink():
            raise StageError(f"{pkg.name} {pkg.tag}: docs/ is a symlink")
        sel = select(_list_files(source), pkg.docs)
        if sel.missing:
            raise StageError(f"{pkg.name} {pkg.tag}: allowlisted docs missing: {list(sel.missing)}")
        if sel.unlisted:
            self._lg.info(
                "docs not in allowlist, skipped",
                extra={"package": pkg.name, "files": list(sel.unlisted)},
            )
        dest = self._docs_dir / pkg.name / "guides"
        if dest.exists():
            shutil.rmtree(dest)
        for path in sel.copy:
            _copy_file(source, dest, path, pkg.name)
        self._lg.info("docs staged", extra={"package": pkg.name, "files": len(sel.copy)})
        return dest


def _list_files(root: Path) -> list[str]:
    """Every file and symlink under `root`, as POSIX paths relative to it."""
    if not root.is_dir():
        return []
    entries = (p for p in root.rglob("*") if p.is_symlink() or p.is_file())
    return [p.relative_to(root).as_posix() for p in entries]


def _copy_file(source: Path, dest: Path, path: str, pkg_name: str) -> None:
    """Copy one regular file; a symlink could pull content from outside docs/."""
    src = source / path
    if src.is_symlink():
        raise StageError(f"{pkg_name}: allowlisted docs path {path!r} is a symlink")
    target = dest / path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, target)
