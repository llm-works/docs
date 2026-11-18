# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Typed build configuration, validated from the `site`, `nav`, `brand` and `packages` sections."""

import re
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# A package name becomes a directory name; keep it to a plain slug.
_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")
# A tag is passed to git; no leading dash, no path or shell metacharacters.
_TAG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_GLOB_CHARS = frozenset("*?[]")


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
        """The stage step deletes docs_dir, so it cannot be or contain the pages."""
        pages = self.pages_dir.resolve()
        if self.docs_dir.resolve() in (pages, *pages.parents):
            raise ValueError("site.docs_dir is rebuilt on every stage; it cannot hold pages_dir")
        return self


class NavConfig(_Frozen):
    """The main site's nav partial and where the rendered header goes."""

    url: str
    site_origin: str
    docs_origin: str
    output: Path
    timeout_s: float = Field(default=10.0, gt=0)

    @field_validator("url")
    @classmethod
    def _url_scheme(cls, value: str) -> str:
        """Accept http(s), and file:// for local previews and tests."""
        _check_url("nav.url", value)
        return value

    @field_validator("site_origin")
    @classmethod
    def _site_origin_form(cls, value: str) -> str:
        """An origin without a trailing slash, or empty for root-relative links."""
        if value:
            _check_origin("nav.site_origin", value)
        return value

    @field_validator("docs_origin")
    @classmethod
    def _docs_origin_form(cls, value: str) -> str:
        """The docs site's origin, without a trailing slash."""
        _check_origin("nav.docs_origin", value)
        return value


class BrandConfig(_Frozen):
    """The main site's shared stylesheets, fetched with the nav, loaded before the docs' own CSS.

    tokens.css holds the brand's custom properties (colors, edges, fonts, card spacing); nav.css
    styles the nav partial and its theme switch.
    """

    tokens_url: str
    nav_css_url: str
    timeout_s: float = Field(default=10.0, gt=0)

    @field_validator("tokens_url", "nav_css_url")
    @classmethod
    def _url_scheme(cls, value: str) -> str:
        """Accept http(s), and file:// for local previews and tests."""
        _check_url("brand stylesheet URL", value)
        return value


def _check_url(field: str, value: str) -> None:
    """Accept http(s), and file:// for local previews and tests."""
    if not value.startswith(("https://", "http://", "file://")):
        raise ValueError(f"{field} must be an http(s) or file URL")


def _check_origin(field: str, value: str) -> None:
    """Reject anything but scheme://host[:port], with no path, query or fragment."""
    parts = urlsplit(value)
    # Comparing against the rebuilt origin also catches what urlsplit drops, like a bare '?'.
    if (
        parts.scheme not in ("https", "http")
        or not parts.hostname
        or value != f"{parts.scheme}://{parts.netloc}"
    ):
        raise ValueError(f"{field} must be an http(s) origin: scheme://host[:port], nothing after")


# A site nav entry: a path, {title: path}, or {title: [entries]} for a section.
NavItem = str | dict[str, Any]

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class Reference(_Frozen):
    """A generated API reference: one page per top-level module of `package`, with submodules."""

    # The import name, e.g. appinfra or llm_saia
    package: str
    # The checkout directory that holds the package directory
    source: str = "."

    @field_validator("package")
    @classmethod
    def _package_name(cls, value: str) -> str:
        """An importable top-level name."""
        if not _IDENTIFIER.fullmatch(value):
            raise ValueError(f"reference package {value!r} is not an import name")
        return value

    @field_validator("source")
    @classmethod
    def _source_path(cls, value: str) -> str:
        """A plain path inside the checkout."""
        _check_doc_path(value, "reference source")
        return value


class Package(_Frozen):
    """One package: its repo, the release tag to build from, and its docs tree.

    `docs` is both the allowlist and the package's place in the site nav: the package's docs are
    the source and are published as they are, while the arrangement (order, sections, titles) is
    the site's. Every path in it is published, and nothing else is.
    """

    name: str
    repo: str = Field(min_length=1)
    tag: str
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

    @field_validator("name")
    @classmethod
    def _name_slug(cls, value: str) -> str:
        """The name becomes a directory name."""
        if not _NAME.fullmatch(value):
            raise ValueError(f"package name {value!r} must be a lowercase slug")
        return value

    @field_validator("tag")
    @classmethod
    def _tag_form(cls, value: str) -> str:
        """The tag is passed to git, so it cannot look like an option."""
        if not _TAG.fullmatch(value):
            raise ValueError(f"tag {value!r} is not a plain tag name")
        return value

    @field_validator("docs_root")
    @classmethod
    def _docs_root_path(cls, value: str) -> str:
        """The docs directory is a plain path inside the checkout."""
        _check_doc_path(value, "docs_root")
        return value

    @field_validator("docs")
    @classmethod
    def _docs_paths(cls, value: tuple[NavItem, ...]) -> tuple[NavItem, ...]:
        """Each path is exact, inside the docs root, and listed once."""
        files = list(_nav_files(value))
        for path in files:
            _check_doc_path(path, "docs path")
        if len(set(files)) != len(files):
            raise ValueError("docs allowlist lists a path twice")
        return value

    @model_validator(mode="after")
    def _renames_fit(self) -> "Package":
        """Each rename maps a listed file to a free, plain path."""
        files = set(self.files)
        for src, dst in self.rename.items():
            _check_doc_path(dst, "rename target")
            if src not in files:
                raise ValueError(f"rename source {src!r} is not in docs")
        targets = [self.site_path(path) for path in files]
        if len(set(targets)) != len(targets):
            raise ValueError("rename target collides with another docs path")
        return self


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


def _check_doc_path(path: str, what: str) -> None:
    """Reject paths that could escape their root or match more than one file."""
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts or path != pure.as_posix():
        raise ValueError(f"{what} {path!r} must be a normalized relative path")
    if _GLOB_CHARS & set(path):
        raise ValueError(f"{what} {path!r} must be an exact path, not a pattern")


class BuildConfig(_Frozen):
    """The whole build: site paths, nav source, brand stylesheets and the packages to publish."""

    site: SiteConfig
    nav: NavConfig
    brand: BrandConfig
    packages: tuple[Package, ...]

    @model_validator(mode="after")
    def _unique_names(self) -> "BuildConfig":
        """Two packages cannot stage into the same directory."""
        names = [pkg.name for pkg in self.packages]
        if len(set(names)) != len(names):
            raise ValueError("package names must be unique")
        return self


def load_build_config(raw: Mapping[str, Any]) -> BuildConfig:
    """Validate the build sections of the app config; other sections are ignored."""
    sections = {key: _plain(raw.get(key)) for key in ("site", "nav", "brand", "packages")}
    return BuildConfig.model_validate(sections)


def _plain(value: Any) -> Any:
    """Turn the config library's mapping and sequence types into dicts and lists."""
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_plain(item) for item in value]
    return value
