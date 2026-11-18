# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Rendering the Zensical config from the base config and the package trees."""

from typing import Any

import pytest

from docsite.siteconf import SiteConfigError, render_site_config


def _base() -> dict[str, Any]:
    return {
        "project": {
            "site_name": "Docs",
            "nav": [
                {"Home": "index.md"},
                {
                    "Packages": [
                        "packages/index.md",
                        {"pkg": "pkg/index.md"},
                        {"other": "other/index.md"},
                    ]
                },
            ],
        }
    }


def test_package_entry_expands_under_its_landing_page() -> None:
    """The landing page stays first, the tree follows under <name>/; other entries stay."""
    tree = ["guide.md", {"API": ["api/a.md"]}]
    config = render_site_config(_base(), {"pkg": tree}, [], "docs")
    packages = config["project"]["nav"][1]["Packages"]
    assert packages[1] == {"pkg": ["pkg/index.md", "pkg/guide.md", {"API": ["pkg/api/a.md"]}]}
    assert packages[2] == {"other": "other/index.md"}


def test_base_is_not_modified() -> None:
    """The base mapping can be rendered again."""
    base = _base()
    render_site_config(base, {"pkg": ["guide.md"]}, [], "docs")
    assert base == _base()


def test_reference_sources_point_mkdocstrings_at_checkouts() -> None:
    """With references, the Python handler reads the given checkout directories."""
    config = render_site_config(_base(), {}, [".build/src/pkg"], "docs")
    handler = config["project"]["plugins"]["mkdocstrings"]["handlers"]["python"]
    assert handler["paths"] == [".build/src/pkg"]
    assert "plugins" not in render_site_config(_base(), {}, [], "docs")["project"]


def test_docs_dir_is_the_staged_directory() -> None:
    """Zensical reads the directory stage fills, whatever the base config says."""
    base = _base()
    base["project"]["docs_dir"] = "elsewhere"
    config = render_site_config(base, {}, [], docs_dir="build/docs")
    assert config["project"]["docs_dir"] == "build/docs"


def test_package_without_an_entry_fails() -> None:
    """A configured package needs its landing entry in the base nav."""
    with pytest.raises(SiteConfigError, match="'absent'"):
        render_site_config(_base(), {"absent": []}, [], "docs")


def test_base_without_packages_section_fails() -> None:
    """The base nav must have the Packages section."""
    with pytest.raises(SiteConfigError, match="Packages"):
        render_site_config({"project": {"nav": [{"Home": "index.md"}]}}, {"pkg": []}, [], "docs")
