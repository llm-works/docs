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
# A small package beside docs/, for the generated reference
SOURCE = {
    "pkgmod/__init__.py": '"""The package."""\n',
    "pkgmod/core.py": '"""Core module."""\n\n\ndef run() -> None:\n    """Run."""\n',
}


def git(cwd: Path, *args: str) -> None:
    """Run git in `cwd` with a fixed test identity."""
    subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


@pytest.fixture
def package_repo(tmp_path: Path) -> Path:
    """A repo with docs/ and a package committed and tagged TAG, plus a branch named `rel`."""
    repo = tmp_path / "pkg-repo"
    files = {f"docs/{rel}": text for rel, text in DOCS.items()} | SOURCE
    for rel, text in files.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    git(tmp_path, "init", "--quiet", "--initial-branch=main", str(repo))
    git(repo, "add", ".")
    git(repo, "commit", "--quiet", "-m", "docs")
    git(repo, "tag", TAG)
    git(repo, "branch", "rel")
    return repo
