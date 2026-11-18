# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Fencing the indented code blocks that docstrings put under titles like Example:."""

from types import SimpleNamespace
from typing import Any, cast

import pytest

from docsite.docstring_code import CodeBlocks, fence_code_blocks


def _doc(*lines: str) -> str:
    return "\n".join(lines)


def test_example_block_becomes_a_python_fence() -> None:
    """Indented code under Example: keeps its lines, inside a python fence."""
    text = _doc("Summary.", "", "Example:", "    app = App()", "    # comment", "    app.run()")
    assert fence_code_blocks(text) == _doc(
        "Summary.",
        "",
        "Example:",
        "    ```python",
        "    app = App()",
        "    # comment",
        "    app.run()",
        "    ```",
    )


def test_yaml_example_gets_a_yaml_fence() -> None:
    """A block that is not Python but looks like YAML is fenced as yaml."""
    text = _doc("Include Example:", "    # In config.yaml:", '    db: !include "./db.yaml"')
    assert "    ```yaml" in fence_code_blocks(text)


def test_doctest_is_fenced_as_pycon() -> None:
    """A session block, including a bare >>> line, stays together as one code block."""
    text = _doc(
        "Example:", "    >>> w = Watcher()", "    >>>", "    >>> # comment", "    >>> w.stop()"
    )
    out = fence_code_blocks(text)
    assert "    ```pycon" in out
    assert out.count("```") == 2


def test_nested_title_is_fenced_at_its_indent() -> None:
    """An Example: inside another section is found, and its block keeps that indent."""
    text = _doc(
        "Hyphenated Keys:",
        "    Text here.",
        "",
        "    Example:",
        "        YAML: a.b",
        "        Env: X=1",
    )
    out = fence_code_blocks(text)
    assert "        ```yaml" in out
    assert out.endswith("        ```")


@pytest.mark.parametrize(
    "text",
    [
        _doc("Args:", "    name: The name.", "    size: The size."),
        _doc("Examples:", "    - Config file not found", "    - Invalid YAML"),
        _doc("Note:", "    Requires watchdog. Install with pip."),
        _doc("Example:", "    ```python", "    x = 1", "    ```"),
        _doc("Example:"),
        _doc(
            "This sentence ends with a colon and is much longer than any section title:",
            "    x = 1",
        ),
    ],
)
def test_items_prose_and_existing_fences_are_left_alone(text: str) -> None:
    """Structured sections, bullet lists, prose, fences and non-titles pass through unchanged."""
    assert fence_code_blocks(text) == text


def test_untitled_code_under_a_title_is_fenced_when_it_parses() -> None:
    """Under a title without 'example', a block is code only if it reads as Python or YAML."""
    assert "```python" in fence_code_blocks(_doc("Environment Variables:", "    INFRA_X=1"))
    assert "```text" not in fence_code_blocks(_doc("Format:", "    INFRA_<SECTION>=value"))


def test_extension_rewrites_the_object_docstring() -> None:
    """The griffe hook replaces the docstring text before it is parsed."""
    obj = SimpleNamespace(docstring=SimpleNamespace(value=_doc("Example:", "    x = 1")))
    CodeBlocks().on_instance(obj=cast(Any, obj))
    assert "```python" in obj.docstring.value
    no_doc = SimpleNamespace(docstring=None)
    CodeBlocks().on_instance(obj=cast(Any, no_doc))
    assert no_doc.docstring is None
