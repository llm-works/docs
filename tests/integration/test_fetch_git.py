# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Cloning packages at their tags with real git, against a local repository."""

from pathlib import Path

import pytest
from appinfra.log import Logger

from docsite.config import Package
from docsite.fetch import FetchError, PackageFetcher
from tests.integration.conftest import TAG


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


def test_branch_name_is_not_accepted_as_a_pin(
    lg: Logger, package_repo: Path, tmp_path: Path
) -> None:
    """git clone --branch takes branches too; only a release tag is a valid pin."""
    with pytest.raises(FetchError):
        PackageFetcher(lg, tmp_path / "build").fetch(_package(package_repo, "rel"))
