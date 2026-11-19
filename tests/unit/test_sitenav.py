# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Rendering the main site's nav as the docs header."""

import pytest

from docsite.sitenav import DOCS_ITEM, GENERATED_MARK, NavMarkupError, render_header

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
    html = render_header(NAV, ORIGIN)
    assert html.startswith(GENERATED_MARK)
    assert f'href="{ORIGIN}/"' in html
    assert f'href="{ORIGIN}/#agents"' in html
    assert 'href="https://github.com/llm-works"' in html
    assert 'href="/' not in html


def test_only_the_docs_item_is_current_and_follows_platform() -> None:
    """The main site's current marker is dropped; the Docs item lands right after Platform."""
    lines = render_header(NAV, ORIGIN).splitlines(keepends=True)
    platform = next(i for i, line in enumerate(lines) if "/platform/" in line)
    assert lines[platform + 1] == DOCS_ITEM
    assert sum('aria-current="page"' in line for line in lines) == 1


def test_empty_origin_keeps_links_root_relative() -> None:
    """A local preview served next to the main site keeps root-relative links."""
    html = render_header(NAV, "")
    assert 'href="/platform/"' in html
    assert DOCS_ITEM in html


def test_missing_platform_item_fails_loudly() -> None:
    """Without the Platform item there is no place for the Docs item."""
    with pytest.raises(NavMarkupError, match="Platform item"):
        render_header(NAV.replace('href="/platform/"', 'class="other"'), ORIGIN)
