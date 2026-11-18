# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Fetch the inputs of a build: each package at its release tag, and the main site's nav and
brand stylesheets."""

import shutil
import subprocess
import urllib.request
from pathlib import Path

from appinfra.log import Logger

from .config import NavConfig, Package

# www.llm-works.ai sits behind Cloudflare, which rejects urllib's default User-Agent with a
# 403; an agent naming this build is accepted.
USER_AGENT = "llm-works-docs-build (+https://github.com/llm-works/docs)"


class FetchError(RuntimeError):
    """A package or the nav partial could not be fetched."""


class PackageFetcher:
    """Shallow-clones packages at their pinned tags into the build directory."""

    def __init__(self, lg: Logger, build_dir: Path) -> None:
        self._lg = lg
        self._build_dir = build_dir

    def fetch(self, pkg: Package) -> Path:
        """Clone `pkg` at its tag into <build_dir>/<name>, replacing an older checkout."""
        dest = self._build_dir / pkg.name
        if dest.exists():
            shutil.rmtree(dest)
        self._build_dir.mkdir(parents=True, exist_ok=True)
        _git(
            "-c", "advice.detachedHead=false", "clone", "--quiet", "--depth", "1",
            "--branch", pkg.tag, "--", pkg.repo, str(dest),
        )  # fmt: skip
        try:
            _check_pin(dest, pkg)
        except FetchError:
            # A later stage step must not find the rejected checkout.
            shutil.rmtree(dest)
            raise
        self._lg.info("package fetched", extra={"package": pkg.name, "tag": pkg.tag})
        return dest


def _check_pin(dest: Path, pkg: Package) -> None:
    """Fail unless HEAD is the tagged commit; ^{commit} peels an annotated tag.

    --branch also accepts a branch, and prefers one that shares the tag's name; only the
    tagged commit is a valid pin.
    """
    error = f"{pkg.name}: checkout is not at tag {pkg.tag}"
    head = _git("-C", str(dest), "rev-parse", "HEAD")
    try:
        tagged = _git("-C", str(dest), "rev-parse", "--verify", f"refs/tags/{pkg.tag}^{{commit}}")
    except FetchError as e:
        # A shallow clone of a branch lacks any tag that points at an older commit.
        raise FetchError(error) from e
    if head != tagged:
        raise FetchError(error)


def _git(*args: str) -> str:
    """Run git and return its stripped stdout; raise FetchError with stderr when it fails."""
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or f"git exited with {result.returncode}"
        raise FetchError(detail)
    return result.stdout.strip()


def fetch_nav(lg: Logger, nav: NavConfig) -> str:
    """Download the main site's nav partial and return its markup."""
    return fetch_text(lg, nav.url, nav.timeout_s)


def fetch_text(lg: Logger, url: str, timeout_s: float) -> str:
    """Download a text file from the main site (or a file:// URL) and return it."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:  # noqa: S310
            # HTTP responses carry a status; file:// responses (local previews) have None.
            status = response.status
            body: bytes = response.read()
    except OSError as e:
        raise FetchError(f"download from {url} failed: {e}") from e
    if status is not None and status != 200:
        raise FetchError(f"download from {url} returned HTTP {status}")
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as e:
        raise FetchError(f"{url} is not valid UTF-8: {e}") from e
    lg.info("fetched", extra={"url": url, "bytes": len(body)})
    return text
