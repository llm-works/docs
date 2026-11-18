# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Staging allowlisted docs from a checkout on disk."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from appinfra.log import Logger

from docsite.config import Package
from docsite.stage import DocsStager, StageError


def _checkout(root: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        path = root / "docs" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def _package(*docs: str) -> Package:
    return Package(name="pkg", repo="r", tag="v1.0.0", docs=docs)


def test_copies_only_allowlisted_files(tmp_path: Path) -> None:
    """Listed files land under <docs_dir>/<name>/guides; unlisted ones are logged, not copied."""
    checkout = _checkout(tmp_path / "co", {"INTRO.md": "i", "demo/a.gif": "g", "notes.md": "n"})
    lg = MagicMock(spec=Logger)
    dest = DocsStager(lg, tmp_path / "docs").stage(_package("INTRO.md", "demo/a.gif"), checkout)
    assert dest == tmp_path / "docs" / "pkg" / "guides"
    assert sorted(p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file()) == [
        "INTRO.md",
        "demo/a.gif",
    ]
    skipped = lg.info.call_args_list[0]
    assert skipped.kwargs["extra"]["files"] == ["notes.md"]


def test_missing_allowlisted_file_fails(lg: Logger, tmp_path: Path) -> None:
    """A listed file absent at the tag stops the build."""
    checkout = _checkout(tmp_path / "co", {"INTRO.md": "i"})
    with pytest.raises(StageError, match="gone.md"):
        DocsStager(lg, tmp_path / "docs").stage(_package("INTRO.md", "gone.md"), checkout)


def test_symlinked_doc_is_rejected(lg: Logger, tmp_path: Path) -> None:
    """A symlink could publish a file from outside docs/."""
    checkout = _checkout(tmp_path / "co", {"INTRO.md": "i"})
    secret = tmp_path / "secret.txt"
    secret.write_text("s", encoding="utf-8")
    (checkout / "docs" / "leak.md").symlink_to(secret)
    with pytest.raises(StageError, match="symlink"):
        DocsStager(lg, tmp_path / "docs").stage(_package("leak.md"), checkout)


def test_symlinked_docs_root_is_rejected(lg: Logger, tmp_path: Path) -> None:
    """docs/ pointing elsewhere would publish that directory's files under allowlisted names."""
    checkout = tmp_path / "co"
    private = checkout / "private"
    private.mkdir(parents=True)
    (private / "INTRO.md").write_text("private", encoding="utf-8")
    (checkout / "docs").symlink_to(private)
    with pytest.raises(StageError, match="symlink"):
        DocsStager(lg, tmp_path / "docs").stage(_package("INTRO.md"), checkout)
    assert not (tmp_path / "docs" / "pkg").exists()


def test_checkout_without_docs_dir_fails(lg: Logger, tmp_path: Path) -> None:
    """A package without docs/ has every listed file missing."""
    (tmp_path / "co").mkdir()
    with pytest.raises(StageError, match="INTRO.md"):
        DocsStager(lg, tmp_path / "docs").stage(_package("INTRO.md"), tmp_path / "co")


def test_restage_removes_files_dropped_from_allowlist(lg: Logger, tmp_path: Path) -> None:
    """Staging replaces the previous output, so a delisted file disappears."""
    checkout = _checkout(tmp_path / "co", {"INTRO.md": "i", "old.md": "o"})
    stager = DocsStager(lg, tmp_path / "docs")
    stager.stage(_package("INTRO.md", "old.md"), checkout)
    dest = stager.stage(_package("INTRO.md"), checkout)
    assert not (dest / "old.md").exists()
