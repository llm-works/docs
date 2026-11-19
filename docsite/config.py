# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Typed build configuration, validated from the `site`, `nav`, `brand` and `packages` sections."""

from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _Frozen(BaseModel):
    """Immutable model that rejects unknown keys, so a misspelt key fails loudly."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class SiteConfig(_Frozen):
    """Where checkouts, pages and staged docs live, and the Zensical config in and out."""

    build_dir: Path
    docs_dir: Path
    pages_dir: Path
    zensical_base: Path
    zensical_config: Path

    @model_validator(mode="after")
    def _docs_dir_is_disposable(self) -> "SiteConfig":
        """stage deletes what docs_dir holds beyond its plan, and reads the pages and checkouts:
        docs_dir cannot be, contain or lie inside pages_dir or build_dir."""
        docs = self.docs_dir.resolve()
        for name, path in (("pages_dir", self.pages_dir), ("build_dir", self.build_dir)):
            other = path.resolve()
            if docs == other or docs in other.parents or other in docs.parents:
                raise ValueError(
                    f"site.docs_dir is rebuilt on every stage; it cannot overlap site.{name}"
                )
        return self


class NavConfig(_Frozen):
    """The main site's nav partial and where the rendered header goes.

    `site_origin` is scheme://host[:port] with no trailing slash; empty keeps the nav's links
    root-relative, for a local preview.
    """

    url: str
    site_origin: str
    output: Path
    timeout_s: float = 10.0


class BrandConfig(_Frozen):
    """The main site's shared stylesheets, fetched with the nav, loaded before the docs' own CSS.

    tokens.css holds the brand's custom properties (colors, edges, fonts, card spacing); nav.css
    styles the nav partial and its theme switch.
    """

    tokens_url: str
    nav_css_url: str
    timeout_s: float = 10.0


# A site nav entry: a path, {title: path}, or {title: [entries]} for a section.
NavItem = str | dict[str, Any]


class Reference(_Frozen):
    """A generated API reference: one page per package and subpackage of `package`."""

    # The import name, e.g. appinfra or llm_saia
    package: str
    # The checkout directory that holds the package directory
    source: str = "."
    # Subpackages left out of the reference with everything under them, as dotted paths relative
    # to the package (examples, cli.tools). The packages ship their runnable examples as one.
    exclude: tuple[str, ...] = ("examples",)


class Package(_Frozen):
    """One package: its repo, the git ref to build from, and its docs tree.

    `ref` is a tag, a branch, or <branch>@<commit> for a commit on that branch (the commit may
    be abbreviated). The published site builds from release tags; a branch is for previews.

    `docs` is both the allowlist and the package's place in the site nav: the package's docs are
    the source and are published as they are, while the arrangement (order, sections, titles) is
    the site's. Every path in it is published, and nothing else is.
    """

    name: str
    repo: str
    ref: str
    docs_root: str = "docs"
    docs: tuple[NavItem, ...] = Field(min_length=1)
    # Staged under another name, e.g. README.md, which the generator would take as the index
    rename: dict[str, str] = Field(default_factory=dict)
    # Generated API reference; a package without one publishes only its docs
    reference: Reference | None = None

    @property
    def files(self) -> tuple[str, ...]:
        """Every path in the docs tree, in nav order."""
        return tuple(_nav_files(self.docs))

    def site_path(self, path: str) -> str:
        """Where a docs path lands in the site, relative to the package's directory."""
        return self.rename.get(path, path)


def _nav_files(items: Sequence[NavItem]) -> Iterator[str]:
    """Yield the paths of a docs tree in order; reject entries of any other shape."""
    for item in items:
        if isinstance(item, str):
            yield item
            continue
        if not (isinstance(item, dict) and len(item) == 1):
            raise ValueError(f"docs entry {item!r} must be a path or a one-key mapping")
        (value,) = item.values()
        if isinstance(value, str):
            yield value
        elif isinstance(value, list | tuple) and value:
            yield from _nav_files(value)
        else:
            raise ValueError(f"docs entry {item!r} needs a path or a non-empty list")


class BuildConfig(_Frozen):
    """The whole build: site paths, nav source, brand stylesheets and the packages to publish."""

    site: SiteConfig
    nav: NavConfig
    brand: BrandConfig
    packages: tuple[Package, ...]


def load_build_config(raw: Mapping[str, Any]) -> BuildConfig:
    """Validate the build sections of the app config; other sections are ignored.

    `packages` maps each package name to its settings, so an environment variable can override
    one of them, e.g. INFRA_PACKAGES_APPINFRA_REF=develop.
    """
    sections = {key: _plain(raw.get(key)) for key in ("site", "nav", "brand")}
    packages = _plain(raw.get("packages")) or {}
    sections["packages"] = [{"name": name, **pkg} for name, pkg in packages.items()]
    return BuildConfig.model_validate(sections)


def _plain(value: Any) -> Any:
    """Turn the config library's mapping and sequence types into dicts and lists."""
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_plain(item) for item in value]
    return value
