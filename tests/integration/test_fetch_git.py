# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Cloning packages at their refs with real git, against a local repository."""

import subprocess
from pathlib import Path

import pytest
from appinfra.log import Logger

from docsite.config import Package
from docsite.fetch import FetchError, PackageFetcher
from tests.integration.conftest import TAG, git


def _package(repo: Path, ref: str = TAG) -> Package:
    # A file:// URL goes through git's transport like a remote, so --depth applies
    return Package(name="pkg", repo=repo.as_uri(), ref=ref, docs=("INTRO.md",))


def test_clones_the_tag_into_build_dir(lg: Logger, package_repo: Path, tmp_path: Path) -> None:
    """The checkout holds the tagged docs."""
    dest = PackageFetcher(lg, tmp_path / "build").fetch(_package(package_repo))
    assert (dest / "docs" / "INTRO.md").is_file()


def test_unknown_ref_fails(lg: Logger, package_repo: Path, tmp_path: Path) -> None:
    """A ref that does not exist stops the build with git's message."""
    with pytest.raises(FetchError, match="v9.9.9"):
        PackageFetcher(lg, tmp_path / "build").fetch(_package(package_repo, "v9.9.9"))


def _commit_intro(repo: Path, text: str) -> str:
    """Commit a new INTRO.md; return the commit, abbreviated."""
    (repo / "docs" / "INTRO.md").write_text(text, encoding="utf-8")
    git(repo, "commit", "--quiet", "-am", text)
    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return head.stdout.strip()


def test_commit_on_a_branch_is_checked_out(lg: Logger, package_repo: Path, tmp_path: Path) -> None:
    """<branch>@<commit> fetches that commit, abbreviated, though the branch has moved on."""
    older = _commit_intro(package_repo, "# Older\n")
    _commit_intro(package_repo, "# Newer\n")
    dest = PackageFetcher(lg, tmp_path / "build").fetch(_package(package_repo, f"main@{older}"))
    assert (dest / "docs" / "INTRO.md").read_text(encoding="utf-8") == "# Older\n"
