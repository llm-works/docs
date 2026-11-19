# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""The built site in a browser: pages load without script errors, with header, tree and search.

Runs against site/ from `make build`; skipped without it or without Playwright installed
(`python -m playwright install chromium` gets the browser).
"""

import threading
from collections.abc import Iterator
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

pytest.importorskip("pytest_playwright")

from playwright.sync_api import Page, expect  # noqa: E402

SITE = Path(__file__).resolve().parents[2] / "site"


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        """No request log on stderr."""


@pytest.fixture(scope="module")
def site_url() -> Iterator[str]:
    """site/ served on a free local port for the module's tests."""
    if not (SITE / "index.html").is_file():
        pytest.skip("site/ is not built; run `make build`")
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(_QuietHandler, directory=str(SITE)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    thread.join()


@pytest.mark.parametrize("path", ["", "appinfra/"])
def test_page_loads_with_header_tree_and_search(page: Page, site_url: str, path: str) -> None:
    """The home page and a package page render the shell without a script error."""
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(f"{site_url}/{path}")
    expect(page.locator("nav.site-nav")).to_be_visible()
    expect(page.locator("nav.md-nav--primary")).to_be_attached()
    expect(page.locator(".md-search")).to_be_attached()
    assert errors == []
