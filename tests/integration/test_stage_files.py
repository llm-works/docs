# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Selecting allowlisted docs from a checkout on disk, and syncing the docs directory."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from appinfra.log import Logger

from docsite.config import Package
from docsite.stage import DocsStager, Source, StageError, merge, sync_tree, text_pages


def _checkout(root: Path, files: dict[str, str], docs_root: str = "docs") -> Path:
    for rel, text in files.items():
        path = root / docs_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def _package(*docs: Any, **fields: Any) -> Package:
    return Package(name="pkg", repo="r", ref="v1.0.0", docs=docs, **fields)


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


def test_missing_allowlisted_file_fails(lg: Logger, tmp_path: Path) -> None:
    """A listed file absent at the ref stops the build."""
    checkout = _checkout(tmp_path / "co", {"INTRO.md": "i"})
    with pytest.raises(StageError, match="gone.md"):
        DocsStager(lg).files(_package("INTRO.md", "gone.md"), checkout)


def test_plain_text_file_renamed_to_markdown_becomes_a_page(tmp_path: Path) -> None:
    """LICENSE staged as license.md shows its text as it is, in a code block under a title."""
    (tmp_path / "LICENSE").write_text("Apache License\n  1. Definitions.\n", encoding="utf-8")
    (tmp_path / "a.md").write_text("# A\n", encoding="utf-8")
    pages = text_pages({"license.md": tmp_path / "LICENSE", "a.md": tmp_path / "a.md"})
    assert pages["license.md"] == "# License\n\n```text\nApache License\n  1. Definitions.\n```\n"
    assert pages["a.md"] == tmp_path / "a.md"


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
