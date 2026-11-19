# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Fencing the indented code blocks that docstrings put under titles like Example:."""

from types import SimpleNamespace
from typing import Any, cast

import pytest

from docsite.docstring_code import CodeBlocks, fence_code_blocks


def _doc(*lines: str) -> str:
    return "\n".join(lines)


def test_example_code_becomes_a_session() -> None:
    """Indented code under Example: is fenced as a session: >>> opens each statement and
    comment, ... continues a statement, decorators included."""
    text = _doc(
        "Summary.",
        "",
        "Example:",
        "    app = App()",
        "    # comment",
        "    @app.tool()",
        "    def run():",
        "",
        "        pass",
    )
    assert fence_code_blocks(text) == _doc(
        "Summary.",
        "",
        "Example:",
        "    ```pycon",
        "    >>> app = App()",
        "    >>> # comment",
        "    >>> @app.tool()",
        "    ... def run():",
        "    ...",
        "    ...     pass",
        "    ```",
    )


def test_doctest_is_fenced_as_pycon() -> None:
    """A session block, including a bare >>> line, stays together as one code block."""
    out = fence_code_blocks(
        _doc("Example:", "    >>> w = Watcher()", "    >>>", "    >>> w.stop()")
    )
    assert "    ```pycon" in out
    assert out.count("```") == 2


@pytest.mark.parametrize(
    "text",
    [
        _doc("Args:", "    name: The name.", "    size: The size."),
        _doc("Examples:", "    - Config file not found", "    - Invalid YAML"),
        _doc("Note:", "    Requires watchdog. Install with pip."),
    ],
)
def test_items_and_prose_are_left_alone(text: str) -> None:
    """Structured sections, bullet lists and prose pass through unchanged."""
    assert fence_code_blocks(text) == text


def test_extension_rewrites_the_object_docstring() -> None:
    """The griffe hook replaces the docstring text before it is parsed."""
    obj = SimpleNamespace(docstring=SimpleNamespace(value=_doc("Example:", "    x = 1")))
    CodeBlocks().on_instance(obj=cast(Any, obj))
    assert "```pycon" in obj.docstring.value
