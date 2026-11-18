# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Build config validation."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from docsite.config import load_build_config
from tests.conftest import build_dict, package_dict


def test_valid_config_loads() -> None:
    """A complete config yields typed sections, with the nav timeout defaulted."""
    cfg = load_build_config(build_dict())
    assert cfg.site.docs_dir == Path("docs")
    assert cfg.nav.timeout_s == 10.0
    assert cfg.packages[0].docs == ("INTRO.md", "demo/demo.gif")


def test_no_packages_is_valid() -> None:
    """A build with no packages only renders the header."""
    assert load_build_config(build_dict(packages=[])).packages == ()


def test_unrelated_sections_are_ignored() -> None:
    """Logging and other app sections do not reach the build models."""
    raw = build_dict()
    raw["logging"] = {"level": "info"}
    assert load_build_config(raw).packages[0].name == "llm-saia"


@pytest.mark.parametrize(
    "path",
    ["../secrets.md", "/etc/passwd", "a/../b.md", "./INTRO.md", "*.md", "guide[1].md"],
)
def test_docs_path_must_be_exact_and_inside_docs(path: str) -> None:
    """Allowlist entries cannot escape docs/ or act as patterns."""
    with pytest.raises(ValidationError, match="docs path"):
        load_build_config(build_dict(packages=[package_dict(docs=[path])]))


def test_docs_allowlist_rejects_duplicates_and_empty() -> None:
    """Each path is listed once, and a package publishes at least one file."""
    with pytest.raises(ValidationError, match="twice"):
        load_build_config(build_dict(packages=[package_dict(docs=["a.md", "a.md"])]))
    with pytest.raises(ValidationError):
        load_build_config(build_dict(packages=[package_dict(docs=[])]))


@pytest.mark.parametrize("name", ["../x", "LLM", "-x", "a/b"])
def test_package_name_is_a_slug(name: str) -> None:
    """The name becomes a directory, so it is a lowercase slug."""
    with pytest.raises(ValidationError, match="slug"):
        load_build_config(build_dict(packages=[package_dict(name=name)]))


@pytest.mark.parametrize("tag", ["--upload-pack=x", "v1 2", "v1;rm"])
def test_tag_is_a_plain_name(tag: str) -> None:
    """The tag reaches git, so options and metacharacters are rejected."""
    with pytest.raises(ValidationError, match="tag"):
        load_build_config(build_dict(packages=[package_dict(tag=tag)]))


def test_package_names_are_unique() -> None:
    """Two packages cannot stage into the same directory."""
    with pytest.raises(ValidationError, match="unique"):
        load_build_config(build_dict(packages=[package_dict(), package_dict()]))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("url", "ftp://example.com/nav.html"),
        ("site_origin", "https://www.llm-works.ai/"),
        ("site_origin", "www.llm-works.ai"),
        ("timeout_s", 0),
    ],
)
def test_nav_fields_are_checked(field: str, value: object) -> None:
    """Nav URL scheme, origin form and timeout are validated."""
    nav = build_dict()["nav"] | {field: value}
    with pytest.raises(ValidationError):
        load_build_config(build_dict(nav=nav))


def test_empty_site_origin_is_allowed() -> None:
    """An empty origin keeps links root-relative, for a local preview."""
    nav = build_dict()["nav"] | {"site_origin": ""}
    assert load_build_config(build_dict(nav=nav)).nav.site_origin == ""


def test_unknown_keys_are_rejected() -> None:
    """A misspelt key fails instead of being silently ignored."""
    with pytest.raises(ValidationError):
        load_build_config(build_dict(packages=[package_dict(doc=["INTRO.md"])]))
