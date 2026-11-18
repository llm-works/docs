# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Typed build configuration, validated from the `site`, `nav` and `packages` sections."""

import re
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

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
    """Where checkouts and staged docs go."""

    build_dir: Path
    docs_dir: Path


class NavConfig(_Frozen):
    """The main site's nav partial and where the rendered header goes."""

    url: str
    site_origin: str
    output: Path
    timeout_s: float = Field(default=10.0, gt=0)

    @field_validator("url")
    @classmethod
    def _url_scheme(cls, value: str) -> str:
        """Accept http(s), and file:// for local previews and tests."""
        if not value.startswith(("https://", "http://", "file://")):
            raise ValueError("nav.url must be an http(s) or file URL")
        return value

    @field_validator("site_origin")
    @classmethod
    def _origin_form(cls, value: str) -> str:
        """An origin without a trailing slash, or empty for root-relative links."""
        if value and (not value.startswith(("https://", "http://")) or value.endswith("/")):
            raise ValueError("nav.site_origin must be empty or an http(s) origin without '/'")
        return value


class Package(_Frozen):
    """One package: its repo, the release tag to build from, and its docs allowlist."""

    name: str
    repo: str = Field(min_length=1)
    tag: str
    docs: tuple[str, ...] = Field(min_length=1)

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

    @field_validator("docs")
    @classmethod
    def _docs_paths(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Each entry is an exact path inside docs/, listed once."""
        for path in value:
            _check_doc_path(path)
        if len(set(value)) != len(value):
            raise ValueError("docs allowlist lists a path twice")
        return value


def _check_doc_path(path: str) -> None:
    """Reject paths that could escape docs/ or match more than one file."""
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts or path != pure.as_posix():
        raise ValueError(f"docs path {path!r} must be a normalized path inside docs/")
    if _GLOB_CHARS & set(path):
        raise ValueError(f"docs path {path!r} must be an exact path, not a pattern")


class BuildConfig(_Frozen):
    """The whole build: site paths, nav source and the packages to publish."""

    site: SiteConfig
    nav: NavConfig
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
    sections = {key: _plain(raw.get(key)) for key in ("site", "nav", "packages")}
    return BuildConfig.model_validate(sections)


def _plain(value: Any) -> Any:
    """Turn the config library's mapping and sequence types into dicts and lists."""
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_plain(item) for item in value]
    return value
