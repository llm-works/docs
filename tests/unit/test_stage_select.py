# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Comparing a package's docs/ with its allowlist."""

from docsite.stage import select


def test_select_splits_copy_missing_and_unlisted() -> None:
    """Listed files present are copied; listed-absent are missing; extras are unlisted."""
    sel = select(
        ["INTRO.md", "known-issues.md", "demo/demo.gif", "demo/demo.tape"],
        ["INTRO.md", "demo/demo.gif", "gone.md"],
    )
    assert sel.copy == ("INTRO.md", "demo/demo.gif")
    assert sel.missing == ("gone.md",)
    assert sel.unlisted == ("demo/demo.tape", "known-issues.md")


def test_select_keeps_allowlist_order() -> None:
    """Copy order follows the allowlist, not the filesystem."""
    sel = select(["b.md", "a.md"], ["b.md", "a.md"])
    assert sel.copy == ("b.md", "a.md")
    assert sel.missing == () and sel.unlisted == ()
