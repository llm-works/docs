# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Fetch the inputs of a build: each package at its release tag, and the main site's nav."""

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
        # --branch also accepts a branch name; only a release tag is a valid pin.
        _git("-C", str(dest), "rev-parse", "--quiet", "--verify", f"refs/tags/{pkg.tag}")
        self._lg.info("package fetched", extra={"package": pkg.name, "tag": pkg.tag})
        return dest


def _git(*args: str) -> None:
    """Run git; raise FetchError with its stderr when it fails."""
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or f"git exited with {result.returncode}"
        raise FetchError(detail)


def fetch_nav(lg: Logger, nav: NavConfig) -> str:
    """Download the main site's nav partial and return its markup."""
    request = urllib.request.Request(nav.url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=nav.timeout_s) as response:  # noqa: S310
            # HTTP responses carry a status; file:// responses (local previews) have None.
            status = response.status
            body: bytes = response.read()
    except OSError as e:
        raise FetchError(f"nav download from {nav.url} failed: {e}") from e
    if status is not None and status != 200:
        raise FetchError(f"nav download from {nav.url} returned HTTP {status}")
    lg.info("nav fetched", extra={"url": nav.url, "bytes": len(body)})
    return body.decode("utf-8")
