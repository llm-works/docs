# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""The CLI steps, in process, with a config pointing at local inputs."""

import sys
from pathlib import Path

import pytest

from docsite.cli import main
from tests.integration.conftest import TAG

NAV = """\
  <nav aria-label="Primary">
      <a href="/" class="logo">llm-works</a>
      <ul class="nav-links">
        <li><a href="/platform/">Platform</a></li>
      </ul>
  </nav>
"""


def _config(tmp_path: Path, repo: Path, docs: list[str]) -> Path:
    nav_file = tmp_path / "nav-src.html"
    nav_file.write_text(NAV, encoding="utf-8")
    etc = tmp_path / "etc"
    etc.mkdir()
    allowlist = "".join(f"      - {path}\n" for path in docs)
    (etc / "docsite.yaml").write_text(
        f"""\
logging:
  level: error
site:
  build_dir: {tmp_path / "build"}
  docs_dir: {tmp_path / "docs"}
nav:
  url: {nav_file.as_uri()}
  site_origin: https://www.llm-works.ai
  docs_origin: https://docs.llm-works.ai
  output: {tmp_path / "overrides" / "site-nav.html"}
packages:
  - name: pkg
    repo: {repo}
    tag: {TAG}
    docs:
{allowlist}""",
        encoding="utf-8",
    )
    return etc


def _run(monkeypatch: pytest.MonkeyPatch, etc: Path, step: str) -> int:
    monkeypatch.setattr(sys, "argv", ["docsite", "--etc-dir", str(etc), step])
    return main()


def test_build_runs_every_step(
    monkeypatch: pytest.MonkeyPatch, package_repo: Path, tmp_path: Path
) -> None:
    """`build` fetches, stages the allowlisted docs and renders the header."""
    etc = _config(tmp_path, package_repo, ["INTRO.md", "demo/demo.gif"])
    assert _run(monkeypatch, etc, "build") == 0
    guides = tmp_path / "docs" / "pkg" / "guides"
    assert (guides / "INTRO.md").is_file()
    assert (guides / "demo" / "demo.gif").is_file()
    assert not (guides / "known-issues.md").exists()
    header = (tmp_path / "overrides" / "site-nav.html").read_text(encoding="utf-8")
    assert 'href="https://www.llm-works.ai/platform/"' in header


def test_steps_run_separately(
    monkeypatch: pytest.MonkeyPatch, package_repo: Path, tmp_path: Path
) -> None:
    """fetch, stage and nav each do their part and read the previous step's output."""
    etc = _config(tmp_path, package_repo, ["INTRO.md"])
    assert _run(monkeypatch, etc, "fetch") == 0
    assert (tmp_path / "build" / "nav.html").is_file()
    assert _run(monkeypatch, etc, "stage") == 0
    assert (tmp_path / "docs" / "pkg" / "guides" / "INTRO.md").is_file()
    assert _run(monkeypatch, etc, "nav") == 0
    assert (tmp_path / "overrides" / "site-nav.html").is_file()


def test_failed_step_exits_1(
    monkeypatch: pytest.MonkeyPatch, package_repo: Path, tmp_path: Path
) -> None:
    """A missing allowlisted file fails the build with exit code 1."""
    etc = _config(tmp_path, package_repo, ["absent.md"])
    assert _run(monkeypatch, etc, "build") == 1
