# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Rendering the main site's nav as the docs header."""

import pytest

from docsite.sitenav import (
    DOCS_ITEM,
    GENERATED_MARK,
    SEARCH,
    THEME_SWITCH,
    NavMarkupError,
    docs_nav,
    render_header,
)

ORIGIN = "https://www.llm-works.ai"

NAV = """\
  <nav aria-label="Primary">
    <div class="container">
      <a href="/" class="logo">llm-works<span>.ai</span></a>
      <ul class="nav-links">
        <li><a href="/#agents">Agents</a></li>
        <li><a href="/platform/" aria-current="page">Platform</a></li>
        <li><a href="/blog/">Blog</a></li>
        <li><a href="https://github.com/llm-works" class="nav-github">GH</a></li>
      </ul>
    </div>
  </nav>
"""


def test_root_relative_links_point_at_the_main_site() -> None:
    """Root-relative hrefs gain the origin; absolute ones are left alone."""
    html = docs_nav(NAV, ORIGIN)
    assert f'href="{ORIGIN}/"' in html
    assert f'href="{ORIGIN}/#agents"' in html
    assert 'href="https://github.com/llm-works"' in html
    assert 'href="/' not in html


def test_main_site_current_marker_is_dropped() -> None:
    """Only the Docs item is current on the docs site."""
    html = docs_nav(NAV, ORIGIN)
    assert html.count('aria-current="page"') == 1
    assert "Platform</a>" in html and 'aria-current="page">Platform' not in html


def test_docs_item_follows_platform_and_search_follows_logo() -> None:
    """The Docs item and the search box land at their anchors."""
    lines = docs_nav(NAV, ORIGIN).splitlines(keepends=True)
    platform = next(i for i, line in enumerate(lines) if "/platform/" in line)
    logo = next(i for i, line in enumerate(lines) if 'class="logo"' in line)
    assert lines[platform + 1] == DOCS_ITEM
    assert lines[logo + 1] == SEARCH


def test_existing_docs_link_is_marked_instead_of_duplicated() -> None:
    """Once the main site links to the docs, that item becomes current."""
    nav = NAV.replace(
        '<li><a href="/blog/">',
        '<li><a href="https://docs.llm-works.ai/">Docs</a></li>\n<li><a href="/blog/">',
    )
    html = docs_nav(nav, ORIGIN)
    assert DOCS_ITEM not in html
    assert '<a href="https://docs.llm-works.ai/" aria-current="page">Docs</a>' in html


def test_empty_origin_keeps_links_root_relative() -> None:
    """A local preview served next to the main site keeps root-relative links."""
    html = docs_nav(NAV, "")
    assert 'href="/platform/"' in html
    assert DOCS_ITEM in html


@pytest.mark.parametrize(
    ("needle", "what"),
    [('class="logo"', "logo"), ('href="/platform/"', "Platform item")],
)
def test_missing_anchor_fails_loudly(needle: str, what: str) -> None:
    """A nav without the logo or the Platform item cannot be rendered."""
    with pytest.raises(NavMarkupError, match=what):
        docs_nav(NAV.replace(needle, 'class="other"'), ORIGIN)


def test_header_wraps_nav_with_mark_and_theme_switch() -> None:
    """The partial starts with the generated mark and ends with the theme switch."""
    header = render_header(NAV, ORIGIN)
    assert header.startswith(GENERATED_MARK)
    assert header.endswith(THEME_SWITCH)
