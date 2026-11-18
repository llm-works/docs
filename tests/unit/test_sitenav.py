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
DOCS = "https://docs.llm-works.ai"

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


def _with_docs_link(href: str) -> str:
    """NAV with a Docs item linking to `href` before Blog."""
    return NAV.replace(
        '<li><a href="/blog/">', f'<li><a href="{href}">Docs</a></li>\n<li><a href="/blog/">'
    )


def test_root_relative_links_point_at_the_main_site() -> None:
    """Root-relative hrefs gain the origin; absolute ones are left alone."""
    html = docs_nav(NAV, ORIGIN, DOCS)
    assert f'href="{ORIGIN}/"' in html
    assert f'href="{ORIGIN}/#agents"' in html
    assert 'href="https://github.com/llm-works"' in html
    assert 'href="/' not in html


def test_main_site_current_marker_is_dropped() -> None:
    """Only the Docs item is current on the docs site."""
    html = docs_nav(NAV, ORIGIN, DOCS)
    assert html.count('aria-current="page"') == 1
    assert "Platform</a>" in html and 'aria-current="page">Platform' not in html


def test_docs_item_follows_platform_and_search_follows_logo() -> None:
    """The Docs item and the search box land at their anchors."""
    lines = docs_nav(NAV, ORIGIN, DOCS).splitlines(keepends=True)
    platform = next(i for i, line in enumerate(lines) if "/platform/" in line)
    logo = next(i for i, line in enumerate(lines) if 'class="logo"' in line)
    assert lines[platform + 1] == DOCS_ITEM
    assert lines[logo + 1] == SEARCH


def test_existing_docs_link_is_marked_instead_of_duplicated() -> None:
    """Once the main site links to the docs, that item becomes current."""
    html = docs_nav(_with_docs_link(f"{DOCS}/"), ORIGIN, DOCS)
    assert DOCS_ITEM not in html
    assert f'<a href="{DOCS}/" aria-current="page">Docs</a>' in html


def test_docs_link_to_another_origin_is_not_matched() -> None:
    """Only a link to the configured docs origin counts as the Docs item."""
    html = docs_nav(_with_docs_link(f"{DOCS}/"), ORIGIN, "https://staging.llm-works.ai")
    assert DOCS_ITEM in html
    assert f'<a href="{DOCS}/">Docs</a>' in html


def test_empty_origin_keeps_links_root_relative() -> None:
    """A local preview served next to the main site keeps root-relative links."""
    html = docs_nav(NAV, "", DOCS)
    assert 'href="/platform/"' in html
    assert DOCS_ITEM in html


@pytest.mark.parametrize(
    ("needle", "what"),
    [('class="logo"', "logo"), ('href="/platform/"', "Platform item")],
)
def test_missing_anchor_fails_loudly(needle: str, what: str) -> None:
    """A nav without the logo or the Platform item cannot be rendered."""
    with pytest.raises(NavMarkupError, match=what):
        docs_nav(NAV.replace(needle, 'class="other"'), ORIGIN, DOCS)


def test_header_wraps_nav_with_mark_and_theme_switch() -> None:
    """The partial starts with the generated mark and ends with the theme switch."""
    header = render_header(NAV, ORIGIN, DOCS)
    assert header.startswith(GENERATED_MARK)
    assert header.endswith(THEME_SWITCH)
