# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Griffe extension: render indented code in docstrings as code blocks.

Packages write docstring examples as plain indented blocks under a title, e.g. `Example:`, which
the Google-style parser hands to Markdown as text: the lines run together into one paragraph and
a `# comment` becomes a heading. This extension wraps such blocks in fences before parsing.
Loaded by mkdocstrings from zensical.base.toml as `docsite/docstring_code.py:CodeBlocks`.
"""

import ast
import re
from typing import Any

from griffe import Extension, Object

# A section title alone on its line, e.g. "Example:" or "Include Example:"
_TITLE = re.compile(r"[A-Z][\w ()/'-]{0,40}:")
# Titles the Google-style parser reads as structured items, which must stay as they are
_STRUCTURED = frozenset(
    {
        "args", "arguments", "params", "parameters", "keyword args", "keyword arguments",
        "other args", "other arguments", "other params", "other parameters", "raises",
        "exceptions", "warns", "warnings", "returns", "return", "yields", "yield", "receives",
        "receive", "attributes", "functions", "methods", "classes", "modules", "type aliases",
        "type parameters", "deprecated",
    }
)  # fmt: skip
# A line of a YAML mapping or list, or a comment
_YAML_LINE = re.compile(r"\s*(#.*|[\w.-]+:(\s.*)?|- .*)")
_EXAMPLE_WORDS = ("example", "usage")


class CodeBlocks(Extension):
    """Fences titled code blocks in every docstring before the parser sees them."""

    def on_instance(self, *, obj: Object, **kwargs: Any) -> None:
        """Rewrite the object's docstring text in place."""
        if obj.docstring is not None:
            obj.docstring.value = fence_code_blocks(obj.docstring.value)


def fence_code_blocks(text: str) -> str:
    """Return `text` with each titled block of code wrapped in a fenced code block."""
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        out.append(lines[i])
        end = _block_end(lines, i)
        block = lines[i + 1 : end]
        if end > i + 1 and _is_code(lines[i].strip()[:-1], block):
            out.extend(_fenced(block))
            i = end
        else:
            i += 1
    return "\n".join(out)


def _block_end(lines: list[str], i: int) -> int:
    """The index after the block indented under a title at line `i`, or i + 1 if none."""
    if not _TITLE.fullmatch(lines[i].strip()):
        return i + 1
    title_indent = _indent(lines[i])
    end = i + 1
    while end < len(lines) and (not lines[end].strip() or _indent(lines[end]) > title_indent):
        end += 1
    while end > i + 1 and not lines[end - 1].strip():
        end -= 1
    return end


def _is_code(title: str, block: list[str]) -> bool:
    """Whether the block under `title` is code rather than items, a doctest or prose."""
    body = [line.strip() for line in block if line.strip()]
    if not body or title.lower() in _STRUCTURED:
        return False
    if any(line.startswith("```") for line in body):
        return False
    # Doctests too: griffe's own doctest parsing stops at a bare ">>>" and leaves the rest as text.
    if _is_doctest(body):
        return True
    if all(line.startswith(("- ", "* ")) for line in body):
        return False
    if any(word in title.lower() for word in _EXAMPLE_WORDS):
        return True
    return _language(_dedent(block)) != "text"


def _fenced(block: list[str]) -> list[str]:
    """The block as a fenced code block at its own indentation."""
    body = _dedent(block)
    pad = " " * min(_indent(line) for line in block if line.strip())
    fence = [f"{pad}```{_language(body)}"]
    fence += [f"{pad}{line}" if line else "" for line in body]
    return [*fence, f"{pad}```"]


def _indent(line: str) -> int:
    """The number of leading spaces."""
    return len(line) - len(line.lstrip())


def _dedent(block: list[str]) -> list[str]:
    """The block's lines without their common indentation."""
    indent = min(_indent(line) for line in block if line.strip())
    return [line[indent:] for line in block]


def _is_doctest(lines: list[str]) -> bool:
    """Whether the block is an interactive session: it opens with a >>> prompt."""
    first = next((line.strip() for line in lines if line.strip()), "")
    return first.startswith(">>>")


def _language(body: list[str]) -> str:
    """pycon for a doctest, python if it parses, yaml if every line looks like YAML, else text.

    `key: value` lines also parse as Python annotations; a block of nothing else is YAML.
    """
    if _is_doctest(body):
        return "pycon"
    yaml_shaped = all(_YAML_LINE.fullmatch(line) for line in body if line.strip())
    try:
        tree = ast.parse("\n".join(body))
    except SyntaxError:
        return "yaml" if yaml_shaped else "text"
    only_annotations = bool(tree.body) and all(isinstance(s, ast.AnnAssign) for s in tree.body)
    return "yaml" if yaml_shaped and only_annotations else "python"
