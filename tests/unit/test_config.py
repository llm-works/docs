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
        ("site_origin", "https://www.llm-works.ai?preview=1"),
        ("site_origin", "https://www.llm-works.ai/sub"),
        ("site_origin", "https://www.llm-works.ai#x"),
        ("docs_origin", ""),
        ("docs_origin", "https://"),
        ("docs_origin", "https://docs.llm-works.ai/"),
        ("timeout_s", 0),
    ],
)
def test_nav_fields_are_checked(field: str, value: object) -> None:
    """Nav URL scheme, origin form and timeout are validated."""
    nav = build_dict()["nav"] | {field: value}
    with pytest.raises(ValidationError):
        load_build_config(build_dict(nav=nav))


def test_origin_with_port_is_allowed() -> None:
    """A local preview server's origin carries a port."""
    nav = build_dict()["nav"] | {"docs_origin": "http://localhost:8000"}
    assert load_build_config(build_dict(nav=nav)).nav.docs_origin == "http://localhost:8000"


def test_empty_site_origin_is_allowed() -> None:
    """An empty origin keeps links root-relative, for a local preview."""
    nav = build_dict()["nav"] | {"site_origin": ""}
    assert load_build_config(build_dict(nav=nav)).nav.site_origin == ""


def test_unknown_keys_are_rejected() -> None:
    """A misspelt key fails instead of being silently ignored."""
    with pytest.raises(ValidationError):
        load_build_config(build_dict(packages=[package_dict(doc=["INTRO.md"])]))


TREE = [
    {"User guide": "README.md"},
    "start.md",
    {"Guides": [{"Config": ["guides/a.md", {"B": "guides/b.md"}]}, "guides/c.md"]},
]


def test_docs_tree_lists_its_files_in_nav_order() -> None:
    """Sections and titles are arrangement; the files are the allowlist, in tree order."""
    pkg = load_build_config(build_dict(packages=[package_dict(docs=TREE)])).packages[0]
    assert pkg.files == ("README.md", "start.md", "guides/a.md", "guides/b.md", "guides/c.md")


@pytest.mark.parametrize(
    "entry",
    [{"A": "a.md", "B": "b.md"}, {"Empty": []}, {"Number": 3}],
)
def test_docs_entry_shapes_are_checked(entry: object) -> None:
    """An entry is a path, {title: path} or {section: [entries]}, nothing else."""
    with pytest.raises(ValidationError, match="docs entry"):
        load_build_config(build_dict(packages=[package_dict(docs=[entry])]))


def test_docs_paths_inside_sections_are_checked() -> None:
    """Nested paths get the same checks as top-level ones."""
    with pytest.raises(ValidationError, match="docs path"):
        load_build_config(build_dict(packages=[package_dict(docs=[{"S": ["../x.md"]}])]))
    with pytest.raises(ValidationError, match="twice"):
        load_build_config(build_dict(packages=[package_dict(docs=["a.md", {"S": ["a.md"]}])]))


def test_docs_root_is_a_plain_relative_path() -> None:
    """The docs directory is inside the checkout."""
    pkg = load_build_config(build_dict(packages=[package_dict(docs_root="pkg/docs")])).packages[0]
    assert pkg.docs_root == "pkg/docs"
    with pytest.raises(ValidationError, match="docs_root"):
        load_build_config(build_dict(packages=[package_dict(docs_root="../elsewhere")]))


def test_rename_maps_a_listed_file() -> None:
    """A renamed file lands under its new name; others keep theirs."""
    pkg = load_build_config(
        build_dict(packages=[package_dict(docs=TREE, rename={"README.md": "guide.md"})])
    ).packages[0]
    assert pkg.site_path("README.md") == "guide.md"
    assert pkg.site_path("start.md") == "start.md"


@pytest.mark.parametrize(
    ("rename", "match"),
    [
        ({"absent.md": "x.md"}, "not in docs"),
        ({"README.md": "start.md"}, "collides"),
        ({"README.md": "../x.md"}, "rename target"),
    ],
)
def test_rename_is_checked(rename: dict[str, str], match: str) -> None:
    """Renames name a listed file and a free, plain path."""
    with pytest.raises(ValidationError, match=match):
        load_build_config(build_dict(packages=[package_dict(docs=TREE, rename=rename)]))


def test_reference_is_checked() -> None:
    """The reference names an importable package in a plain checkout path."""
    ref = {"package": "llm_saia", "source": "src"}
    pkg = load_build_config(build_dict(packages=[package_dict(reference=ref)])).packages[0]
    assert pkg.reference is not None and pkg.reference.source == "src"
    with pytest.raises(ValidationError, match="import name"):
        load_build_config(build_dict(packages=[package_dict(reference={"package": "llm-saia"})]))
    with pytest.raises(ValidationError, match="reference source"):
        bad = {"package": "x", "source": "/abs"}
        load_build_config(build_dict(packages=[package_dict(reference=bad)]))


def test_brand_urls_are_checked() -> None:
    """The stylesheets come from http(s), or file:// for local previews."""
    brand = build_dict()["brand"] | {"nav_css_url": "ftp://example.com/nav.css"}
    with pytest.raises(ValidationError, match="brand stylesheet URL"):
        load_build_config(build_dict(brand=brand))


@pytest.mark.parametrize("docs_dir", ["pages", ".", "/"])
def test_docs_dir_cannot_hold_the_pages(docs_dir: str) -> None:
    """stage rebuilds docs_dir, so it cannot be the pages or contain them."""
    site = build_dict()["site"] | {"docs_dir": docs_dir}
    with pytest.raises(ValidationError, match="docs_dir"):
        load_build_config(build_dict(site=site))
