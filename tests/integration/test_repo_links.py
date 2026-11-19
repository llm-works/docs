# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Rewriting links out of a package's docs tree, against a checkout on disk."""

from pathlib import Path
from unittest.mock import MagicMock

from appinfra.log import Logger

from docsite.config import Package
from docsite.links import link_to_repo, repo_paths

REPO = "https://github.com/o/r.git"


def _write(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def test_repo_paths_lists_files_and_directories_without_git(tmp_path: Path) -> None:
    """Every file and directory of the checkout, but nothing under .git."""
    _write(tmp_path, {"README.md": "r", "docs/a.md": "a", ".git/HEAD": "ref"})
    assert repo_paths(tmp_path) == frozenset({"README.md", "docs", "docs/a.md"})


def test_link_to_repo_rewrites_only_changed_markdown(tmp_path: Path) -> None:
    """A page with a link out of the docs tree becomes text; other files stay files."""
    _write(
        tmp_path,
        {
            "README.md": "readme",
            "docs/README.md": "See the [main README](../README.md).\n",
            "docs/plain.md": "[in](README.md)\n",
            "docs/img.gif": "GIF89a",
        },
    )
    # Of <branch>@<commit>, the link takes the commit
    docs = ("README.md", "plain.md", "img.gif")
    pkg = Package(name="pkg", repo=REPO, ref="main@abc1234", docs=docs)
    files = {
        "guide.md": tmp_path / "docs/README.md",
        "plain.md": tmp_path / "docs/plain.md",
        "img.gif": tmp_path / "docs/img.gif",
    }
    lg = MagicMock(spec=Logger)
    linked = link_to_repo(lg, pkg, tmp_path, files)
    assert linked == {
        "guide.md": "See the [main README](https://github.com/o/r/blob/abc1234/README.md).\n",
        "plain.md": tmp_path / "docs/plain.md",
        "img.gif": tmp_path / "docs/img.gif",
    }
    assert lg.info.call_args.kwargs["extra"] == {"package": "pkg", "links": 1}


def test_branch_with_an_empty_commit_links_to_the_branch(lg: Logger, tmp_path: Path) -> None:
    """`develop@` is fetched at the branch tip, so its links go to the branch."""
    _write(tmp_path, {"README.md": "r", "docs/a.md": "[r](../README.md)\n"})
    pkg = Package(name="pkg", repo=REPO, ref="develop@", docs=("a.md",))
    linked = link_to_repo(lg, pkg, tmp_path, {"a.md": tmp_path / "docs/a.md"})
    assert linked["a.md"] == "[r](https://github.com/o/r/blob/develop/README.md)\n"


def test_link_to_repo_leaves_a_repo_without_web_address(lg: Logger, tmp_path: Path) -> None:
    """Without a GitHub repo there is nowhere to point the links: files pass through."""
    _write(tmp_path, {"README.md": "r", "docs/a.md": "[r](../README.md)\n"})
    pkg = Package(name="pkg", repo="/srv/git/pkg", ref="v1.0.0", docs=("a.md",))
    files = {"a.md": tmp_path / "docs/a.md"}
    assert link_to_repo(lg, pkg, tmp_path, files) == files
