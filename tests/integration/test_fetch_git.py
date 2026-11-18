# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Cloning packages at their tags with real git, against a local repository."""

from pathlib import Path

import pytest
from appinfra.log import Logger

from docsite.config import Package
from docsite.fetch import FetchError, PackageFetcher
from tests.integration.conftest import TAG, git


def _package(repo: Path, tag: str = TAG) -> Package:
    return Package(name="pkg", repo=str(repo), tag=tag, docs=("INTRO.md",))


def test_clones_the_tag_into_build_dir(lg: Logger, package_repo: Path, tmp_path: Path) -> None:
    """The checkout holds the tagged docs."""
    dest = PackageFetcher(lg, tmp_path / "build").fetch(_package(package_repo))
    assert dest == tmp_path / "build" / "pkg"
    assert (dest / "docs" / "INTRO.md").is_file()


def test_refetch_replaces_the_old_checkout(lg: Logger, package_repo: Path, tmp_path: Path) -> None:
    """Files left from an earlier fetch do not survive a new one."""
    fetcher = PackageFetcher(lg, tmp_path / "build")
    stale = fetcher.fetch(_package(package_repo)) / "stale.md"
    stale.write_text("old", encoding="utf-8")
    fetcher.fetch(_package(package_repo))
    assert not stale.exists()


def test_unknown_tag_fails(lg: Logger, package_repo: Path, tmp_path: Path) -> None:
    """A tag that does not exist stops the build with git's message."""
    with pytest.raises(FetchError, match="v9.9.9"):
        PackageFetcher(lg, tmp_path / "build").fetch(_package(package_repo, "v9.9.9"))


def test_branch_sharing_the_tag_name_is_rejected(
    lg: Logger, package_repo: Path, tmp_path: Path
) -> None:
    """clone --branch prefers a same-name branch; its newer commit is not the pinned one."""
    (package_repo / "docs" / "INTRO.md").write_text("# Newer\n", encoding="utf-8")
    git(package_repo, "commit", "--quiet", "-am", "newer")
    git(package_repo, "branch", TAG)
    with pytest.raises(FetchError, match=f"not at tag {TAG}"):
        PackageFetcher(lg, tmp_path / "build").fetch(_package(package_repo))


def test_annotated_tag_is_accepted(lg: Logger, package_repo: Path, tmp_path: Path) -> None:
    """An annotated tag resolves to its commit, so the pin check passes."""
    git(package_repo, "tag", "-a", "v2.0.0", "-m", "release")
    dest = PackageFetcher(lg, tmp_path / "build").fetch(_package(package_repo, "v2.0.0"))
    assert (dest / "docs" / "INTRO.md").is_file()


def test_branch_name_is_not_accepted_as_a_pin(
    lg: Logger, package_repo: Path, tmp_path: Path
) -> None:
    """git clone --branch takes branches too; only a release tag is a valid pin."""
    with pytest.raises(FetchError):
        PackageFetcher(lg, tmp_path / "build").fetch(_package(package_repo, "rel"))
