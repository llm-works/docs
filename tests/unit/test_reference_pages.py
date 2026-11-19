# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""The generated reference's pages and nav section, from a module list."""

from docsite.config import load_build_config
from docsite.reference import NAV_TITLE, reference_nav, reference_pages
from tests.conftest import build_dict, package_dict

MODULES = ["llm_saia.core", "llm_saia.verbs", "llm_saia.verbs.check"]
PACKAGES = {"llm-saia": package_dict(reference={"package": "llm_saia"})}


def test_one_page_per_package_linking_its_subpackages() -> None:
    """Each package has a page rendered by mkdocstrings; one with subpackages is its folder's
    index and links them."""
    pkg = load_build_config(build_dict(packages=PACKAGES)).packages[0]
    pages = reference_pages(pkg, MODULES)
    assert set(pages) == {
        "reference/index.md",
        "reference/core.md",
        "reference/verbs/index.md",
        "reference/verbs/check.md",
    }
    assert pages["reference/core.md"] == "# llm_saia.core\n\n::: llm_saia.core\n"
    assert pages["reference/verbs/index.md"] == (
        "# llm_saia.verbs\n\nSubpackages: [`check`](check.md)\n\n::: llm_saia.verbs\n"
    )


def test_own_page_names_the_ref_and_renders_the_top_level() -> None:
    """The reference's page says what it is generated from, links the top-level modules and
    renders the package itself."""
    pkg = load_build_config(build_dict(packages=PACKAGES)).packages[0]
    index = reference_pages(pkg, MODULES)["reference/index.md"]
    assert f"# {NAV_TITLE}" in index
    assert "llm-saia v0.6.3" in index
    assert "Packages: [`core`](core.md), [`verbs`](verbs/index.md)" in index
    assert index.endswith("::: llm_saia\n")


def test_nav_nests_subpackages_under_their_page() -> None:
    """The section opens with its page; a subpackage is a section led by its own page."""
    assert reference_nav(MODULES) == {
        NAV_TITLE: [
            "reference/index.md",
            {"core": "reference/core.md"},
            {"verbs": ["reference/verbs/index.md", {"check": "reference/verbs/check.md"}]},
        ]
    }
