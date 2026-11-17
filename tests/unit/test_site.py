# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Site-wide constants."""

from docsite.site import SITE_URL


def test_site_url_is_the_docs_subdomain() -> None:
    """The site URL is the absolute docs origin, with the trailing slash Zensical expects."""
    assert SITE_URL == "https://docs.llm-works.ai/"
