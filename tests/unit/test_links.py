# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Links in package docs that leave the docs tree become links to the repo at the ref."""

import pytest

from docsite.links import RepoLinks

BASE = "https://github.com/o/r/blob/v1.0.0"
# Files and directories of a repo whose docs root is pkg/docs
PATHS = frozenset(
    {
        "README.md",
        "CHANGELOG.md",
        "examples",
        "examples/demo.py",
        "pkg",
        "pkg/docs",
        "pkg/docs/a.md",
    }
)
DOC = "pkg/docs/guides/guide.md"


def _rewrite(text: str) -> tuple[str, int]:
    return RepoLinks(docs_root="pkg/docs", paths=PATHS, base=BASE).rewrite(text, DOC)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # Inline link out of the docs tree, its fragment kept
        ("See [it](../../../README.md#install).", f"See [it]({BASE}/README.md#install)."),
        # Image, and a directory (GitHub redirects a blob URL of a directory to its tree)
        ("![d](../../../examples/)", f"![d]({BASE}/examples)"),
        # Reference definition
        ("[readme]: ../../../README.md", f"[readme]: {BASE}/README.md"),
    ],
)
def test_links_out_of_the_docs_tree_point_at_the_repo(text: str, expected: str) -> None:
    """A link that resolves to a repo file outside the docs root is rewritten."""
    assert _rewrite(text) == (expected, 1)


@pytest.mark.parametrize(
    "text",
    [
        "[in](../a.md#x)",  # inside the docs tree
        "[absent](../../../SECURITY.md)",  # outside, but not in the repo: left to warn
        "[up](../../../../outside.md)",  # leaves the repo
        "[web](https://example.com/README.md)",
        "`a`[x]: ../../../README.md",  # a definition only starts a line
    ],
)
def test_other_links_are_left_alone(text: str) -> None:
    """Links into the docs tree, to nothing, out of the repo or absolute stay as written."""
    assert _rewrite(text) == (text, 0)


def test_code_is_left_alone() -> None:
    """Fenced code and inline code spans are not links."""
    text = (
        "```md\n[x](../../../README.md)\n```\n"
        "Use `[x](../../../README.md)` or ``a `[x](../../../README.md)` b``.\n"
    )
    assert _rewrite(text) == (text, 0)


def test_every_link_on_a_line_is_counted() -> None:
    """Several links on one line, in prose around a code span, are each rewritten."""
    text = "[a](../../../README.md) `code` [b](../../../CHANGELOG.md)\n"
    expected = f"[a]({BASE}/README.md) `code` [b]({BASE}/CHANGELOG.md)\n"
    assert _rewrite(text) == (expected, 2)
