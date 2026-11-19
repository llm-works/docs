# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Markdown source: which lines are prose and which are fenced code."""

import re
from collections.abc import Sequence

# A code fence line: its marker, then an info string (opening fences only)
_FENCE = re.compile(r"\s*(`{3,}|~{3,})(.*)$")


def prose_flags(lines: Sequence[str]) -> list[bool]:
    """For each line, whether it is prose: outside fenced code and not a fence line itself.

    A fence closes only on a bare marker of its own character, at least as long as the one that
    opened it (CommonMark): a ``` line inside a ~~~ block, or inside a ```` block, is code.
    """
    flags = []
    fence: str | None = None  # the marker of the block the line is in
    for line in lines:
        marker = _FENCE.match(line)
        if marker and fence is None:
            fence = marker.group(1)
            flags.append(False)
        elif marker and _closes(marker, fence):
            fence = None
            flags.append(False)
        else:
            flags.append(fence is None)
    return flags


def _closes(marker: re.Match[str], fence: str | None) -> bool:
    """Whether a fence line closes the block that `fence` opened."""
    close, rest = marker.group(1), marker.group(2)
    return (
        fence is not None and close[0] == fence[0] and len(close) >= len(fence) and not rest.strip()
    )
