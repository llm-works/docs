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
    output=Path("overrides/partials/site-nav.html"),
)


def test_returns_decoded_markup_and_sends_build_user_agent() -> None:
    """The body is decoded as UTF-8; the request names this build, which Cloudflare accepts."""
    response = MagicMock(status=200)
    response.read.return_value = "<nav>é</nav>".encode()
    response.__enter__.return_value = response
    with patch("docsite.fetch.urllib.request.urlopen", return_value=response) as urlopen:
        assert fetch_nav(MagicMock(spec=Logger), NAV) == "<nav>é</nav>"
    assert urlopen.call_args.args[0].get_header("User-agent") == USER_AGENT


def test_network_error_fails() -> None:
    """Connection and HTTP errors surface as FetchError naming the URL."""
    with (
        patch("docsite.fetch.urllib.request.urlopen", side_effect=OSError("refused")),
        pytest.raises(FetchError, match="refused"),
    ):
        fetch_nav(MagicMock(spec=Logger), NAV)
