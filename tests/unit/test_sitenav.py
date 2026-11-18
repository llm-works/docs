# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Rendering the main site's nav as the docs header."""

import pytest

from docsite.sitenav import (
    DOCS_ITEM,
    GENERATED_MARK,
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


def test_docs_item_follows_platform() -> None:
    """The Docs item lands right after Platform; the header carries no search."""
    html = docs_nav(NAV, ORIGIN, DOCS)
    lines = html.splitlines(keepends=True)
    platform = next(i for i, line in enumerate(lines) if "/platform/" in line)
    assert lines[platform + 1] == DOCS_ITEM
    assert "search" not in html


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


def test_missing_platform_item_fails_loudly() -> None:
    """Without the Platform item there is no place for the Docs item."""
    with pytest.raises(NavMarkupError, match="Platform item"):
        docs_nav(NAV.replace('href="/platform/"', 'class="other"'), ORIGIN, DOCS)


def test_header_wraps_nav_with_mark_and_theme_switch() -> None:
    """The partial starts with the generated mark and ends with the theme switch."""
    header = render_header(NAV, ORIGIN, DOCS)
    assert header.startswith(GENERATED_MARK)
    assert header.endswith(THEME_SWITCH)


def test_nav_with_its_own_theme_switch_gets_no_second_one() -> None:
    """Once the main site's partial carries the switch, the header keeps exactly that one."""
    header = render_header(NAV + THEME_SWITCH, ORIGIN, DOCS)
    assert header.count('id="theme-switch"') == 1
