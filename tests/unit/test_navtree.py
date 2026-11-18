# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""A package's nav tree: the configured tree with each path where it is staged, and the pages
generated for sections without one."""

import pytest

from docsite.config import load_build_config
from docsite.navtree import (
    NavTreeError,
    SectionIndex,
    index_sections,
    map_paths,
    package_nav,
    page_title,
    render_section_index,
)
from tests.conftest import build_dict, package_dict


def test_map_paths_keeps_titles_and_sections() -> None:
    """Only paths change; titles and nesting stay."""
    tree = ["a.md", {"T": "b.md"}, {"S": ["c.md", {"U": ["d.md"]}]}]
    assert map_paths(tree, str.upper) == ["A.MD", {"T": "B.MD"}, {"S": ["C.MD", {"U": ["D.MD"]}]}]


def test_package_nav_applies_renames_at_any_depth() -> None:
    """A renamed file appears in the nav under the name it is staged as."""
    docs = [{"Guide": "README.md"}, {"Sub": ["sub/README.md", "sub/x.md"]}]
    rename = {"README.md": "guide.md", "sub/README.md": "sub/overview.md"}
    pkg = load_build_config(build_dict(packages=[package_dict(docs=docs, rename=rename)])).packages[
        0
    ]
    assert package_nav(pkg) == [{"Guide": "guide.md"}, {"Sub": ["sub/overview.md", "sub/x.md"]}]


def test_index_sections_adds_a_page_to_sections_without_one() -> None:
    """A section gets a generated page first, at its titles slugged; nested sections too."""
    tree = ["intro.md", {"Guides": [{"Dev tooling": ["g/a.md"]}, {"B": "g/b.md"}]}]
    out, pages = index_sections(tree)
    assert out == [
        "intro.md",
        {
            "Guides": [
                "guides/index.md",
                {"Dev tooling": ["guides/dev-tooling/index.md", "g/a.md"]},
                {"B": "g/b.md"},
            ]
        },
    ]
    assert pages == {
        "guides/dev-tooling/index.md": SectionIndex("Dev tooling", ("g/a.md",)),
        "guides/index.md": SectionIndex(
            "Guides", ({"Dev tooling": ["guides/dev-tooling/index.md", "g/a.md"]}, {"B": "g/b.md"})
        ),
    }


def test_index_sections_keeps_a_section_page_of_its_own() -> None:
    """A section whose first entry is an index or README page already has its page."""
    tree = [{"A": ["a/index.md", "a/x.md"]}, {"B": [{"Over": "b/README.md"}, "b/y.md"]}]
    assert index_sections(tree) == (tree, {})


def test_index_sections_rejects_a_title_without_a_path() -> None:
    """A title with no letters or digits gives no path for its page."""
    with pytest.raises(NavTreeError, match="no letters or digits"):
        index_sections([{"--": ["a.md"]}])


def test_render_section_index_links_each_entry() -> None:
    """Links are relative to the page; bare paths take their page's title, sections their page."""
    index = SectionIndex(
        "Guides [all]", ("g/a.md", {"Titled": "g/b.md"}, {"Sub": ["guides/sub/index.md", "x.md"]})
    )
    titles = {"g/a.md": "Page A"}
    assert render_section_index("guides/index.md", index, titles.__getitem__) == (
        "# Guides [all]\n\n- [Page A](../g/a.md)\n- [Titled](../g/b.md)\n- [Sub](sub/index.md)\n"
    )


@pytest.mark.parametrize(
    ("text", "title"),
    [
        ("---\ntitle: 'From front'\n---\n# Heading\n", "From front"),
        ("---\nkeywords: [a]\n---\n\n# Heading #\n", "Heading"),
        ("```\n# not a title\n```\n# Real\n", "Real"),
        # A fence closes only on its own character, at least as long as it opened
        ("~~~\n```\n# not a title\n~~~\n# Real\n", "Real"),
        ("````\n```\n# not a title\n```\n````\n# Real\n", "Real"),
        ("## Only a subheading\n", "Getting started"),
    ],
)
def test_page_title_follows_the_site(text: str, title: str) -> None:
    """Front matter title, else the first level-1 heading outside code, else the file name."""
    assert page_title(text, "docs/getting-started.md") == title
