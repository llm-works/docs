# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""The generated reference's pages and nav section, from a module list."""

from docsite.config import load_build_config
from docsite.reference import NAV_TITLE, reference_nav, reference_pages
from tests.conftest import build_dict, package_dict

MODULES = ["llm_saia.core", "llm_saia.verbs"]


def test_one_page_per_module_rendered_by_mkdocstrings() -> None:
    """Each module page titles the module and hands it to mkdocstrings."""
    pkg = load_build_config(build_dict(packages=[package_dict()])).packages[0]
    pages = reference_pages(pkg, MODULES)
    assert pages["reference/core.md"] == "# llm_saia.core\n\n::: llm_saia.core\n"
    assert set(pages) == {"reference/index.md", "reference/core.md", "reference/verbs.md"}


def test_index_names_the_tag_and_links_every_module() -> None:
    """The landing page says what the reference is generated from."""
    pkg = load_build_config(build_dict(packages=[package_dict()])).packages[0]
    index = reference_pages(pkg, MODULES)["reference/index.md"]
    assert f"# {NAV_TITLE}" in index
    assert "llm-saia v0.6.3" in index
    assert "[`llm_saia.verbs`](verbs.md)" in index


def test_nav_section_lists_modules_by_short_name() -> None:
    """The section opens with the index, then one entry per module."""
    assert reference_nav(MODULES) == {
        NAV_TITLE: [
            "reference/index.md",
            {"core": "reference/core.md"},
            {"verbs": "reference/verbs.md"},
        ]
    }
