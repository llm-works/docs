# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Finding a package's top-level modules for the generated reference."""

from pathlib import Path

import pytest

from docsite.config import Reference
from docsite.reference import ReferenceSourceError, reference_modules


def _package(root: Path) -> Path:
    pkg = root / "src" / "mypkg"
    for rel in ("__init__.py", "core.py", "_private.py", "__main__.py", "sub/__init__.py"):
        (pkg / rel).parent.mkdir(parents=True, exist_ok=True)
        (pkg / rel).write_text("", encoding="utf-8")
    (pkg / "docs").mkdir()  # a folder without __init__.py is not a module
    (pkg / "notes.txt").write_text("", encoding="utf-8")
    return pkg


def test_public_modules_and_subpackages_sorted(tmp_path: Path) -> None:
    """Private modules, plain folders, other files and symlinks are left out."""
    pkg = _package(tmp_path)
    (pkg / "linked.py").symlink_to(pkg / "core.py")
    ref = Reference(package="mypkg", source="src")
    assert reference_modules(tmp_path, ref) == ["mypkg.core", "mypkg.sub"]


def test_missing_package_fails(tmp_path: Path) -> None:
    """The reference config must point at a package directory."""
    with pytest.raises(ReferenceSourceError, match="not a package"):
        reference_modules(tmp_path, Reference(package="mypkg"))
