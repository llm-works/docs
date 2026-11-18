# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Downloading the main site's nav, with urlopen mocked at the call site."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from appinfra.log import Logger

from docsite.config import NavConfig
from docsite.fetch import USER_AGENT, FetchError, fetch_nav

NAV = NavConfig(
    url="https://www.llm-works.ai/partials/nav.html",
    site_origin="https://www.llm-works.ai",
    docs_origin="https://docs.llm-works.ai",
    output=Path("overrides/partials/site-nav.html"),
)


def _response(status: int, body: bytes) -> MagicMock:
    response = MagicMock()
    response.status = status
    response.read.return_value = body
    response.__enter__.return_value = response
    return response


def test_returns_decoded_markup_and_sends_build_user_agent() -> None:
    """The body is decoded as UTF-8; the request names this build, which Cloudflare accepts."""
    with patch("docsite.fetch.urllib.request.urlopen") as urlopen:
        urlopen.return_value = _response(200, "<nav>é</nav>".encode())
        assert fetch_nav(MagicMock(spec=Logger), NAV) == "<nav>é</nav>"
    request = urlopen.call_args.args[0]
    assert request.full_url == NAV.url
    assert request.get_header("User-agent") == USER_AGENT
    assert urlopen.call_args.kwargs["timeout"] == NAV.timeout_s


def test_non_200_status_fails() -> None:
    """A redirect page or error body never becomes the header."""
    with patch("docsite.fetch.urllib.request.urlopen") as urlopen:
        urlopen.return_value = _response(204, b"")
        with pytest.raises(FetchError, match="HTTP 204"):
            fetch_nav(MagicMock(spec=Logger), NAV)


def test_non_utf8_body_fails() -> None:
    """Undecodable markup surfaces as FetchError, which the CLI reports as exit 1."""
    with patch("docsite.fetch.urllib.request.urlopen") as urlopen:
        urlopen.return_value = _response(200, b"<nav>\xff</nav>")
        with pytest.raises(FetchError, match="not valid UTF-8"):
            fetch_nav(MagicMock(spec=Logger), NAV)


def test_network_error_fails() -> None:
    """Connection and HTTP errors surface as FetchError naming the URL."""
    with (
        patch("docsite.fetch.urllib.request.urlopen", side_effect=OSError("refused")),
        pytest.raises(FetchError, match="refused"),
    ):
        fetch_nav(MagicMock(spec=Logger), NAV)
