# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Selecting allowlisted docs from a checkout on disk, and syncing the docs directory."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from appinfra.log import Logger

from docsite.config import Package
from docsite.stage import DocsStager, Source, StageError, merge, sync_tree


def _checkout(root: Path, files: dict[str, str], docs_root: str = "docs") -> Path:
    for rel, text in files.items():
        path = root / docs_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def _package(*docs: Any, **fields: Any) -> Package:
    return Package(name="pkg", repo="r", tag="v1.0.0", docs=docs, **fields)


def test_files_maps_allowlisted_docs_and_logs_the_rest(tmp_path: Path) -> None:
    """Listed files map to their sources; unlisted ones are logged and left out."""
    checkout = _checkout(tmp_path / "co", {"INTRO.md": "i", "demo/a.gif": "g", "notes.md": "n"})
    lg = MagicMock(spec=Logger)
    files = DocsStager(lg).files(_package("INTRO.md", {"Demo": ["demo/a.gif"]}), checkout)
    assert files == {
        "INTRO.md": checkout / "docs" / "INTRO.md",
        "demo/a.gif": checkout / "docs" / "demo" / "a.gif",
    }
    assert lg.info.call_args.kwargs["extra"]["files"] == ["notes.md"]


def test_docs_root_and_renames_apply(lg: Logger, tmp_path: Path) -> None:
    """Docs come from docs_root; a renamed file maps under its new name."""
    checkout = _checkout(tmp_path / "co", {"README.md": "r"}, docs_root="pkg/docs")
    pkg = _package("README.md", docs_root="pkg/docs", rename={"README.md": "guide.md"})
    assert DocsStager(lg).files(pkg, checkout) == {"guide.md": checkout / "pkg/docs/README.md"}


def test_missing_allowlisted_file_fails(lg: Logger, tmp_path: Path) -> None:
    """A listed file absent at the tag stops the build."""
    checkout = _checkout(tmp_path / "co", {"INTRO.md": "i"})
    with pytest.raises(StageError, match="gone.md"):
        DocsStager(lg).files(_package("INTRO.md", "gone.md"), checkout)


def test_checkout_without_docs_dir_fails(lg: Logger, tmp_path: Path) -> None:
    """A package without its docs directory has every listed file missing."""
    (tmp_path / "co").mkdir()
    with pytest.raises(StageError, match="INTRO.md"):
        DocsStager(lg).files(_package("INTRO.md"), tmp_path / "co")


def test_symlinked_doc_is_rejected(lg: Logger, tmp_path: Path) -> None:
    """A symlink could publish a file from outside the docs root."""
    checkout = _checkout(tmp_path / "co", {"INTRO.md": "i"})
    secret = tmp_path / "secret.txt"
    secret.write_text("s", encoding="utf-8")
    (checkout / "docs" / "leak.md").symlink_to(secret)
    with pytest.raises(StageError, match="symlink"):
        DocsStager(lg).files(_package("leak.md"), checkout)


@pytest.mark.parametrize("docs_root", ["docs", "pkg/docs"])
def test_symlink_in_the_docs_root_path_is_rejected(
    lg: Logger, tmp_path: Path, docs_root: str
) -> None:
    """A symlinked docs root, or a symlinked folder on the way to it, would list files elsewhere."""
    checkout = tmp_path / "co"
    private = checkout / "private"
    (private / "docs").mkdir(parents=True)
    (private / "INTRO.md").write_text("private", encoding="utf-8")
    (private / "docs" / "INTRO.md").write_text("private", encoding="utf-8")
    first = docs_root.split("/")[0]
    (checkout / first).symlink_to(private)
    with pytest.raises(StageError, match="symlink"):
        DocsStager(lg).files(_package("INTRO.md", docs_root=docs_root), checkout)


def test_merge_refuses_a_taken_path() -> None:
    """Two sources for one docs path is an error, never an overwrite."""
    plan: dict[str, Source] = {"pkg/index.md": "landing"}
    merge(plan, {"pkg/guide.md": "g"}, "pkg")
    with pytest.raises(StageError, match="pkg/index.md"):
        merge(plan, {"pkg/index.md": "other"}, "pkg")
    assert plan == {"pkg/index.md": "landing", "pkg/guide.md": "g"}


def test_sync_writes_changes_and_removes_leftovers(lg: Logger, tmp_path: Path) -> None:
    """The docs directory ends up holding exactly the plan; unchanged files are not rewritten."""
    src = tmp_path / "page.md"
    src.write_text("from a file", encoding="utf-8")
    root = tmp_path / "docs"
    (root / "old" / "deep").mkdir(parents=True)
    (root / "old" / "deep" / "gone.md").write_text("stale", encoding="utf-8")
    (root / "same.md").write_text("generated", encoding="utf-8")
    before = (root / "same.md").stat().st_mtime_ns
    sync_tree(lg, {"a/page.md": src, "same.md": "generated"}, root)
    assert (root / "a" / "page.md").read_text(encoding="utf-8") == "from a file"
    assert (root / "same.md").stat().st_mtime_ns == before
    assert not (root / "old").exists()
