# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Finding a package's subpackages, at every depth, for the generated reference."""

from pathlib import Path

import pytest

from docsite.config import Reference
from docsite.reference import ReferenceSourceError, reference_modules


def _package(root: Path) -> Path:
    pkg = root / "src" / "mypkg"
    for rel in (
        "__init__.py",
        "core.py",
        "_private.py",
        "__main__.py",
        "sub/__init__.py",
        "sub/inner.py",
        "sub/deep/__init__.py",
        "_hidden/__init__.py",
    ):
        (pkg / rel).parent.mkdir(parents=True, exist_ok=True)
        (pkg / rel).write_text("", encoding="utf-8")
    (pkg / "docs").mkdir()  # a folder without __init__.py is not a module
    (pkg / "notes.txt").write_text("", encoding="utf-8")
    return pkg


def test_public_subpackages_at_every_depth(tmp_path: Path) -> None:
    """Subpackages follow their package; a package's own .py files, private packages, plain
    folders and symlinks are left out."""
    pkg = _package(tmp_path)
    (pkg / "linked").symlink_to(pkg / "sub")
    ref = Reference(package="mypkg", source="src")
    assert reference_modules(tmp_path, ref) == ["mypkg.sub", "mypkg.sub.deep"]


def test_missing_package_fails(tmp_path: Path) -> None:
    """The reference config must point at a package directory."""
    with pytest.raises(ReferenceSourceError, match="not a package"):
        reference_modules(tmp_path, Reference(package="mypkg"))
