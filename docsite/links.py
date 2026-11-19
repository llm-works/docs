# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Links in package docs that leave the docs tree, made into links to the repo at the ref.

A package's docs link to files beside them in the repo (the README, the changelog, examples)
with relative paths that work on GitHub. Only the docs tree is published, so on the site those
links point nowhere. A link whose target lies outside the docs root but inside the repo, and
exists at the ref, is rewritten to that file on GitHub at the ref. Links into the docs tree, to
files that do not exist, or out of the repo are left as written, so the build still warns about
them.
"""

import os
import posixpath
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, unquote

from appinfra.log import Logger

from .config import Package
from .markdown import prose_flags
from .stage import Source

_GITHUB = re.compile(r"(https://github\.com/[\w.-]+/[\w.-]+?)(?:\.git)?/?")
# An inline link or image target: "](target" with an optional <...> around it
_INLINE = re.compile(r"(\]\(\s*)(<[^>\n]*>|[^)\s]+)")
# A reference definition: "[label]: target"
_REFDEF = re.compile(r"^(\s{0,3}\[[^\]]+\]:[ \t]*)(<[^>\n]*>|\S+)")
# An inline code span: a run of backticks to the next run of the same length
_CODE_SPAN = re.compile(r"(`+).+?(?<!`)\1(?!`)")
_SCHEME = re.compile(r"[a-zA-Z][a-zA-Z0-9+.-]*:")


def blob_base(repo: str, ref: str) -> str | None:
    """The web address of the repo's files at `ref`, for a GitHub https repo; else None."""
    match = _GITHUB.fullmatch(repo)
    return f"{match.group(1)}/blob/{ref}" if match else None


def repo_paths(checkout: Path) -> frozenset[str]:
    """Every file and directory in the checkout, relative to it, leaving out .git."""
    paths = set()
    for dirpath, dirnames, filenames in os.walk(checkout):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        rel = Path(dirpath).relative_to(checkout)
        for name in dirnames + filenames:
            paths.add((rel / name).as_posix())
    return frozenset(paths)


@dataclass(frozen=True)
class RepoLinks:
    """Where a package's docs sit in its repo, the repo's paths at the ref, and their address."""

    docs_root: str
    paths: frozenset[str]
    base: str

    def rewrite(self, text: str, doc: str) -> tuple[str, int]:
        """`text` of the doc at repo path `doc`, with its links out of the docs tree pointing at
        the repo, and how many were rewritten."""
        doc_dir = posixpath.dirname(doc)
        count = 0

        def target(match: re.Match[str]) -> str:
            nonlocal count
            url = self._url(match.group(2), doc_dir)
            if url is None:
                return match.group(0)
            count += 1
            return match.group(1) + url

        lines = text.splitlines(keepends=True)
        out = [
            _outside_code(line, target) if prose else line
            for line, prose in zip(lines, prose_flags(lines), strict=True)
        ]
        return "".join(out), count

    def _url(self, target: str, doc_dir: str) -> str | None:
        """The repo address for a link target that leaves the docs tree; None to keep it."""
        raw = target[1:-1] if target.startswith("<") else target
        if not raw or raw.startswith(("#", "/")) or _SCHEME.match(raw):
            return None
        cut = min((i for i in (raw.find("#"), raw.find("?")) if i >= 0), default=len(raw))
        path = posixpath.normpath(posixpath.join(doc_dir, unquote(raw[:cut])))
        inside = path == self.docs_root or path.startswith(self.docs_root + "/")
        if inside or path.startswith("../") or path == ".." or path not in self.paths:
            return None
        return f"{self.base}/{quote(path)}{raw[cut:]}"


def link_to_repo(
    lg: Logger, pkg: Package, checkout: Path, files: Mapping[str, Path]
) -> dict[str, Source]:
    """`files` (site path -> file in the checkout), with each Markdown page whose links leave
    the docs tree replaced by its rewritten text."""
    # GitHub addresses a file by tag, branch or commit; of <branch>@<commit>, the commit, and
    # the branch when the commit is empty, as fetch does
    branch, _, commit = pkg.ref.partition("@")
    base = blob_base(pkg.repo, commit or branch)
    if base is None:
        return dict(files)
    links = RepoLinks(pkg.docs_root, repo_paths(checkout), base)
    linked: dict[str, Source] = {}
    total = 0
    for site_path, src in files.items():
        linked[site_path] = src
        if src.suffix == ".md":
            text, count = links.rewrite(src.read_text(encoding="utf-8"), _repo_path(src, checkout))
            if count:
                linked[site_path] = text
                total += count
    if total:
        lg.info("links out of the docs rewritten", extra={"package": pkg.name, "links": total})
    return linked


def _repo_path(src: Path, checkout: Path) -> str:
    """The file's path in the repo."""
    return src.relative_to(checkout).as_posix()


def _outside_code(line: str, replace: Callable[[re.Match[str]], str]) -> str:
    """`line` with its link targets replaced, outside inline code spans."""
    parts = []
    pos = 0
    for span in _CODE_SPAN.finditer(line):
        parts.append(_links(line[pos : span.start()], replace, line_start=pos == 0))
        parts.append(span.group(0))
        pos = span.end()
    parts.append(_links(line[pos:], replace, line_start=pos == 0))
    return "".join(parts)


def _links(text: str, replace: Callable[[re.Match[str]], str], line_start: bool) -> str:
    """`text` with its inline link targets replaced, and a reference definition when the text
    starts the line (the only place one can be)."""
    text = _INLINE.sub(replace, text)
    return _REFDEF.sub(replace, text) if line_start else text
