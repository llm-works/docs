# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Fetch the inputs of a build: each package at its git ref, and the main site's nav and brand
stylesheets."""

import http.client
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
    """Clones packages at their refs into the build directory."""

    def __init__(self, lg: Logger, build_dir: Path) -> None:
        self._lg = lg
        self._build_dir = build_dir

    def fetch(self, pkg: Package) -> Path:
        """Clone `pkg` at its ref into <build_dir>/<name>, replacing an older checkout.

        A tag or a branch is a shallow clone of its tip. <branch>@<commit> clones the branch's
        history, which an abbreviated commit needs to resolve, and checks the commit out; a
        commit that is not on the branch is not in the clone, and fails.
        """
        dest = self._build_dir / pkg.name
        if dest.exists():
            shutil.rmtree(dest)
        self._build_dir.mkdir(parents=True, exist_ok=True)
        branch, _, commit = pkg.ref.partition("@")
        depth = [] if commit else ["--depth", "1"]
        _git(
            "-c", "advice.detachedHead=false", "clone", "--quiet", "--single-branch", *depth,
            "--branch", branch, "--", pkg.repo, str(dest),
        )  # fmt: skip
        if commit:
            _git(
                "-C", str(dest), "-c", "advice.detachedHead=false",
                "checkout", "--quiet", commit, "--",
            )  # fmt: skip
        head = _git("-C", str(dest), "rev-parse", "--short", "HEAD")
        self._lg.info(
            "package fetched", extra={"package": pkg.name, "ref": pkg.ref, "commit": head}
        )
        return dest


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
    # A body cut off mid-transfer raises IncompleteRead, an HTTPException, not an OSError
    except (OSError, http.client.HTTPException) as e:
        raise FetchError(f"download from {url} failed: {e}") from e
    if status is not None and status != 200:
        raise FetchError(f"download from {url} returned HTTP {status}")
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as e:
        raise FetchError(f"{url} is not valid UTF-8: {e}") from e
    lg.info("fetched", extra={"url": url, "bytes": len(body)})
    return text
