# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""A local git repository standing in for a package repo, so fetch needs no network."""

import subprocess
from pathlib import Path

import pytest

TAG = "v1.0.0"
DOCS = {
    "INTRO.md": "# Intro\n\n![demo](./demo/demo.gif)\n",
    "demo/demo.gif": "GIF89a",
    "known-issues.md": "internal notes\n",
}


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


@pytest.fixture
def package_repo(tmp_path: Path) -> Path:
    """A repo with docs/ committed and tagged TAG, plus a branch named `rel`."""
    repo = tmp_path / "pkg-repo"
    for rel, text in DOCS.items():
        path = repo / "docs" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    _git(tmp_path, "init", "--quiet", "--initial-branch=main", str(repo))
    _git(repo, "add", ".")
    _git(repo, "commit", "--quiet", "-m", "docs")
    _git(repo, "tag", TAG)
    _git(repo, "branch", "rel")
    return repo
