# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""The CLI steps, in process, with a config pointing at local inputs."""

import sys
import tomllib
from pathlib import Path

import pytest

from docsite.cli import main
from tests.integration.conftest import TAG, git

NAV = """\
  <nav aria-label="Primary">
      <a href="/" class="logo">llm-works</a>
      <ul class="nav-links">
        <li><a href="/platform/">Platform</a></li>
      </ul>
  </nav>
"""

BASE = """\
[project]
site_name = "Docs"
nav = [
  { "Home" = "index.md" },
  { "Packages" = ["packages/index.md", { "pkg" = "pkg/index.md" }] },
]
"""

PACKAGE = """\
  pkg:
    repo: {repo}
    ref: {ref}
    rename:
      INTRO.md: intro.md
    reference:
      package: pkgmod
    docs:
      - Introduction: INTRO.md
      - Demo:
          - demo/demo.gif
"""


def _inputs(tmp_path: Path) -> None:
    """The site's own pages, the base Zensical config, and the main site's nav and stylesheets."""
    for rel in ("index.md", "packages/index.md", "pkg/index.md"):
        page = tmp_path / "pages" / rel
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(f"# {rel}\n", encoding="utf-8")
    (tmp_path / "base.toml").write_text(BASE, encoding="utf-8")
    (tmp_path / "nav-src.html").write_text(NAV, encoding="utf-8")
    (tmp_path / "tokens.css").write_text(":root { --bg: #000; }\n", encoding="utf-8")
    (tmp_path / "nav.css").write_text(".site-nav { color: red; }\n", encoding="utf-8")


def _config(tmp_path: Path, repo: Path, package: str = PACKAGE) -> Path:
    _inputs(tmp_path)
    etc = tmp_path / "etc"
    etc.mkdir()
    (etc / "docsite.yaml").write_text(
        f"""\
logging:
  level: error
site:
  build_dir: {tmp_path / "build"}
  docs_dir: {tmp_path / "docs"}
  pages_dir: {tmp_path / "pages"}
  zensical_base: {tmp_path / "base.toml"}
  zensical_config: {tmp_path / "zensical.toml"}
nav:
  url: {(tmp_path / "nav-src.html").as_uri()}
  site_origin: https://www.llm-works.ai
  output: {tmp_path / "overrides" / "site-nav.html"}
brand:
  tokens_url: {(tmp_path / "tokens.css").as_uri()}
  nav_css_url: {(tmp_path / "nav.css").as_uri()}
packages:
{package.format(repo=repo, ref=TAG)}""",
        encoding="utf-8",
    )
    return etc


def _run(monkeypatch: pytest.MonkeyPatch, etc: Path) -> int:
    monkeypatch.setattr(sys, "argv", ["docsite", "--etc-dir", str(etc), "build"])
    return main()


def test_build_runs_every_step(
    monkeypatch: pytest.MonkeyPatch, package_repo: Path, tmp_path: Path
) -> None:
    """`build` assembles docs/, renders the header and writes the Zensical config."""
    assert _run(monkeypatch, _config(tmp_path, package_repo)) == 0
    docs = tmp_path / "docs"
    assert (docs / "index.md").is_file()
    assert (docs / "pkg" / "intro.md").is_file()
    assert (docs / "pkg" / "demo" / "demo.gif").is_file()
    assert not (docs / "pkg" / "known-issues.md").exists()
    # pkgmod has no subpackages: its API, core.py included, is on the reference's own page
    assert (
        (docs / "pkg" / "reference" / "index.md")
        .read_text(encoding="utf-8")
        .endswith("::: pkgmod\n")
    )
    assert not (docs / "pkg" / "reference" / "core.md").exists()
    assert (
        (docs / "assets" / "brand" / "tokens.css").read_text(encoding="utf-8").startswith(":root")
    )
    header = (tmp_path / "overrides" / "site-nav.html").read_text(encoding="utf-8")
    assert 'href="https://www.llm-works.ai/platform/"' in header
    config = tomllib.loads((tmp_path / "zensical.toml").read_text(encoding="utf-8"))
    # The staged directory, relative to zensical.toml
    assert config["project"]["docs_dir"] == "docs"
    entry = config["project"]["nav"][1]["Packages"][1]["pkg"]
    assert entry[:3] == [
        "pkg/index.md",
        {"Introduction": "pkg/intro.md"},
        {"Demo": ["pkg/demo/index.md", "pkg/demo/demo.gif"]},
    ]
    assert entry[3]["API reference"][0] == "pkg/reference/index.md"
    # The Demo section has no page of its own: one is generated, listing its entries
    assert (docs / "pkg" / "demo" / "index.md").read_text(encoding="utf-8") == (
        "# Demo\n\n- [Demo](demo.gif)\n"
    )
    python = config["project"]["plugins"]["mkdocstrings"]["handlers"]["python"]
    assert python["paths"] == [(tmp_path / "build" / "pkg").as_posix()]


def test_environment_overrides_a_packages_ref(
    monkeypatch: pytest.MonkeyPatch, package_repo: Path, tmp_path: Path
) -> None:
    """INFRA_PACKAGES_<NAME>_REF builds a preview from a branch instead of the configured tag."""
    (package_repo / "docs" / "INTRO.md").write_text("# On main\n", encoding="utf-8")
    git(package_repo, "commit", "--quiet", "-am", "newer")
    monkeypatch.setenv("INFRA_PACKAGES_PKG_REF", "main")
    assert _run(monkeypatch, _config(tmp_path, package_repo)) == 0
    intro = tmp_path / "docs" / "pkg" / "intro.md"
    assert intro.read_text(encoding="utf-8") == "# On main\n"


def test_failed_build_exits_1(
    monkeypatch: pytest.MonkeyPatch, package_repo: Path, tmp_path: Path
) -> None:
    """A missing allowlisted file fails the build with exit code 1."""
    package = PACKAGE.replace("demo/demo.gif", "absent.md")
    assert _run(monkeypatch, _config(tmp_path, package_repo, package)) == 1


def test_package_without_landing_page_fails(
    monkeypatch: pytest.MonkeyPatch, package_repo: Path, tmp_path: Path
) -> None:
    """Each package needs pages/<name>/index.md before its docs are staged."""
    etc = _config(tmp_path, package_repo)
    (tmp_path / "pages" / "pkg" / "index.md").unlink()
    assert _run(monkeypatch, etc) == 1
