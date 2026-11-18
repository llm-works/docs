# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""The build steps: fetch inputs, assemble the docs tree, render the header and site config."""

import tomllib
from pathlib import Path

import tomli_w
from appinfra.log import Logger

from .config import BuildConfig, NavItem, Package
from .fetch import PackageFetcher, fetch_nav, fetch_text
from .navtree import SectionIndex, index_sections, package_nav, page_title, render_section_index
from .reference import reference_modules, reference_nav, reference_pages
from .siteconf import render_site_config
from .sitenav import render_header
from .stage import DocsStager, Source, StageError, merge, sync_tree

NAV_SOURCE = "nav.html"
# Where fetch saves the brand stylesheets in build_dir, and where stage puts them in docs_dir
BRAND_SOURCE = "brand"
BRAND_ASSETS = "assets/brand"


class Build:
    """Runs the build steps for one configuration; each step reads the previous one's output."""

    def __init__(self, lg: Logger, cfg: BuildConfig) -> None:
        self._lg = lg
        self._cfg = cfg

    def fetch(self) -> None:
        """Clone every package at its tag; download the nav partial and brand stylesheets."""
        fetcher = PackageFetcher(self._lg, self._cfg.site.build_dir)
        for pkg in self._cfg.packages:
            fetcher.fetch(pkg)
        nav_html = fetch_nav(self._lg, self._cfg.nav)
        self._nav_source.parent.mkdir(parents=True, exist_ok=True)
        self._nav_source.write_text(nav_html, encoding="utf-8")
        brand_dir = self._cfg.site.build_dir / BRAND_SOURCE
        brand_dir.mkdir(parents=True, exist_ok=True)
        for name, url in self._brand_files.items():
            css = fetch_text(self._lg, url, self._cfg.brand.timeout_s)
            (brand_dir / name).write_text(css, encoding="utf-8")

    def stage(self) -> None:
        """Sync the docs directory to the site's pages plus each package's docs and reference."""
        site = self._cfg.site
        plan: dict[str, Source] = {
            p.relative_to(site.pages_dir).as_posix(): p
            for p in sorted(site.pages_dir.rglob("*"))
            if p.is_file()
        }
        brand_dir = site.build_dir / BRAND_SOURCE
        brand = {f"{BRAND_ASSETS}/{name}": brand_dir / name for name in self._brand_files}
        merge(plan, brand, "brand stylesheets")
        stager = DocsStager(self._lg)
        for pkg in self._cfg.packages:
            if f"{pkg.name}/index.md" not in plan:
                raise StageError(
                    f"{pkg.name}: no landing page {site.pages_dir}/{pkg.name}/index.md"
                )
            self._stage_package(pkg, stager, plan)
        sync_tree(self._lg, plan, site.docs_dir)

    def _stage_package(self, pkg: Package, stager: DocsStager, plan: dict[str, Source]) -> None:
        """Add a package's docs, its reference and its generated section pages to `plan`."""
        checkout = self._cfg.site.build_dir / pkg.name
        files = stager.files(pkg, checkout)
        merge(plan, {f"{pkg.name}/{path}": src for path, src in files.items()}, pkg.name)
        modules = self._reference_modules(pkg)
        if modules is not None:
            pages = reference_pages(pkg, modules)
            merge(plan, {f"{pkg.name}/{rel}": text for rel, text in pages.items()}, pkg.name)
        _, sections = _package_tree(pkg, modules)
        merge(plan, _section_pages(pkg.name, sections, plan), pkg.name)

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

    def site_config(self) -> Path:
        """Write the Zensical config: the base config with each package's docs in the nav."""
        site = self._cfg.site
        base = tomllib.loads(site.zensical_base.read_text(encoding="utf-8"))
        trees = {
            pkg.name: _package_tree(pkg, self._reference_modules(pkg))[0]
            for pkg in self._cfg.packages
        }
        sources = [
            (site.build_dir / pkg.name / pkg.reference.source).as_posix()
            for pkg in self._cfg.packages
            if pkg.reference is not None
        ]
        config = render_site_config(base, trees, sources)
        site.zensical_config.write_text(tomli_w.dumps(config), encoding="utf-8")
        self._lg.info("site config rendered", extra={"output": str(site.zensical_config)})
        return site.zensical_config

    def all(self) -> None:
        """Fetch, stage, render the header and the site config, in order."""
        self.fetch()
        self.stage()
        self.nav()
        self.site_config()

    def _reference_modules(self, pkg: Package) -> list[str] | None:
        """The modules of the package's API reference; None when it has no reference."""
        if pkg.reference is None:
            return None
        return reference_modules(self._cfg.site.build_dir / pkg.name, pkg.reference)

    @property
    def _nav_source(self) -> Path:
        """Where fetch saves the nav partial and nav reads it."""
        return self._cfg.site.build_dir / NAV_SOURCE

    @property
    def _brand_files(self) -> dict[str, str]:
        """File name -> URL of each brand stylesheet; the names are what the site config loads."""
        return {"tokens.css": self._cfg.brand.tokens_url, "nav.css": self._cfg.brand.nav_css_url}


def _package_tree(
    pkg: Package, modules: list[str] | None
) -> tuple[list[NavItem], dict[str, SectionIndex]]:
    """The package's nav and the section pages it needs generated.

    The nav is the configured docs tree, then the API reference of `modules` (None: the package
    has none), with a generated page first in each section that has none, so that every item in
    the tree opens a page.
    """
    tree = package_nav(pkg)
    if modules is not None:
        tree.append(reference_nav(modules))
    return index_sections(tree)


def _section_pages(
    name: str, sections: dict[str, SectionIndex], plan: dict[str, Source]
) -> dict[str, Source]:
    """The generated section pages of package `name`, by docs path.

    Entries without a title are titled as the site titles them: a Markdown page by its front
    matter or heading, read from what `plan` stages; any other file by its name.
    """

    def title_of(path: str) -> str:
        if not path.endswith(".md"):
            return page_title("", path)
        src = plan[f"{name}/{path}"]
        text = src.read_text(encoding="utf-8") if isinstance(src, Path) else src
        return page_title(text, path)

    return {
        f"{name}/{path}": render_section_index(path, index, title_of)
        for path, index in sections.items()
    }
