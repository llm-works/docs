# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Shared pytest configuration for all test suites."""

from typing import Any

import pytest
from appinfra.log import LogConfig, Logger, LoggerFactory

# Gives each test the suite of its marker or its tests/<suite>/ directory
pytest_plugins = ["appinfra.pytest_suites"]


@pytest.fixture(scope="session")
def lg() -> Logger:
    """A real logger that only prints errors, for tests that do not inspect log calls."""
    return LoggerFactory.create_root(LogConfig.from_params(level="error"))


def package_dict(**overrides: Any) -> dict[str, Any]:
    """A valid `packages` entry's settings, with fields replaced by `overrides`."""
    pkg: dict[str, Any] = {
        "repo": "https://github.com/llm-works/llm-saia.git",
        "ref": "v0.6.3",
        "docs": ["INTRO.md", "demo/demo.gif"],
    }
    pkg.update(overrides)
    return pkg


def build_dict(**overrides: Any) -> dict[str, Any]:
    """A valid build config mapping, with top-level sections replaced by `overrides`."""
    cfg: dict[str, Any] = {
        "site": {
            "build_dir": ".build/src",
            "docs_dir": "docs",
            "pages_dir": "pages",
            "zensical_base": "zensical.base.toml",
            "zensical_config": "zensical.toml",
        },
        "nav": {
            "url": "https://www.llm-works.ai/partials/nav.html",
            "site_origin": "https://www.llm-works.ai",
            "output": "overrides/partials/site-nav.html",
        },
        "brand": {
            "tokens_url": "https://www.llm-works.ai/partials/tokens.css",
            "nav_css_url": "https://www.llm-works.ai/partials/nav.css",
        },
        "packages": {"llm-saia": package_dict()},
    }
    cfg.update(overrides)
    return cfg
