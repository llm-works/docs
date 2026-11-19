# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Build config validation."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from docsite.config import load_build_config
from tests.conftest import build_dict, package_dict


def test_valid_config_loads() -> None:
    """A complete config yields typed sections; a package is named by its key."""
    cfg = load_build_config(build_dict())
    assert cfg.site.docs_dir == Path("docs")
    assert cfg.nav.timeout_s == 10.0
    assert cfg.packages[0].name == "llm-saia"
    assert cfg.packages[0].docs == ("INTRO.md", "demo/demo.gif")


def test_no_packages_is_valid() -> None:
    """A build with no packages only renders the header."""
    assert load_build_config(build_dict(packages={})).packages == ()


def test_unrelated_sections_are_ignored() -> None:
    """Logging and other app sections do not reach the build models."""
    raw = build_dict()
    raw["logging"] = {"level": "info"}
    assert load_build_config(raw).packages[0].name == "llm-saia"


def test_unknown_keys_are_rejected() -> None:
    """A misspelt key fails instead of being silently ignored."""
    with pytest.raises(ValidationError):
        load_build_config(build_dict(packages={"x": package_dict(doc=["INTRO.md"])}))


TREE = [
    {"User guide": "README.md"},
    "start.md",
    {"Guides": [{"Config": ["guides/a.md", {"B": "guides/b.md"}]}, "guides/c.md"]},
]


def test_docs_tree_lists_its_files_in_nav_order() -> None:
    """Sections and titles are arrangement; the files are the allowlist, in tree order."""
    pkg = load_build_config(build_dict(packages={"x": package_dict(docs=TREE)})).packages[0]
    assert pkg.files == ("README.md", "start.md", "guides/a.md", "guides/b.md", "guides/c.md")


@pytest.mark.parametrize(
    "entry",
    [{"A": "a.md", "B": "b.md"}, {"Empty": []}, {"Number": 3}],
)
def test_docs_entry_shapes_are_checked(entry: object) -> None:
    """An entry is a path, {title: path} or {section: [entries]}, nothing else."""
    pkg = load_build_config(build_dict(packages={"x": package_dict(docs=[entry])})).packages[0]
    with pytest.raises(ValueError, match="docs entry"):
        _ = pkg.files


def test_rename_maps_a_listed_file() -> None:
    """A renamed file lands under its new name; others keep theirs."""
    packages = {"x": package_dict(docs=TREE, rename={"README.md": "guide.md"})}
    pkg = load_build_config(build_dict(packages=packages)).packages[0]
    assert pkg.site_path("README.md") == "guide.md"
    assert pkg.site_path("start.md") == "start.md"


@pytest.mark.parametrize(
    "docs_dir",
    [
        # the pages: equal, containing, inside
        "pages",
        ".",
        "/",
        "pages/docs",
        # the checkouts (build_dir is .build/src): equal, containing, inside
        ".build/src",
        ".build",
        ".build/src/docs",
    ],
)
def test_docs_dir_is_apart_from_the_inputs(docs_dir: str) -> None:
    """stage rebuilds docs_dir, so it cannot overlap the pages or the checkouts either way."""
    site = build_dict()["site"] | {"docs_dir": docs_dir}
    with pytest.raises(ValidationError, match="docs_dir"):
        load_build_config(build_dict(site=site))
