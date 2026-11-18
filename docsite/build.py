# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""The build steps: fetch packages and nav, stage allowlisted docs, render the header."""

from pathlib import Path

from appinfra.log import Logger

from .config import BuildConfig
from .fetch import PackageFetcher, fetch_nav
from .sitenav import render_header
from .stage import DocsStager

NAV_SOURCE = "nav.html"


class Build:
    """Runs the build steps for one configuration; each step reads the previous one's output."""

    def __init__(self, lg: Logger, cfg: BuildConfig) -> None:
        self._lg = lg
        self._cfg = cfg

    def fetch(self) -> None:
        """Clone every package at its tag and download the nav partial."""
        fetcher = PackageFetcher(self._lg, self._cfg.site.build_dir)
        for pkg in self._cfg.packages:
            fetcher.fetch(pkg)
        nav_html = fetch_nav(self._lg, self._cfg.nav)
        self._nav_source.parent.mkdir(parents=True, exist_ok=True)
        self._nav_source.write_text(nav_html, encoding="utf-8")

    def stage(self) -> None:
        """Copy each fetched package's allowlisted docs into the site's docs directory."""
        stager = DocsStager(self._lg, self._cfg.site.docs_dir)
        for pkg in self._cfg.packages:
            stager.stage(pkg, self._cfg.site.build_dir / pkg.name)

    def nav(self) -> Path:
        """Render the fetched nav as the docs header partial."""
        nav_html = self._nav_source.read_text(encoding="utf-8")
        nav = self._cfg.nav
        output = nav.output
        output.parent.mkdir(parents=True, exist_ok=True)
        header = render_header(nav_html, nav.site_origin, nav.docs_origin)
        output.write_text(header, encoding="utf-8")
        self._lg.info("header rendered", extra={"output": str(output)})
        return output

    def all(self) -> None:
        """Fetch, stage and render, in order."""
        self.fetch()
        self.stage()
        self.nav()

    @property
    def _nav_source(self) -> Path:
        """Where fetch saves the nav partial and nav reads it."""
        return self._cfg.site.build_dir / NAV_SOURCE
