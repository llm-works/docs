# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Re-exports from other packages listed and linked, against a package on disk."""

from pathlib import Path

import griffe

from docsite.reexports import Exports

FILES = {
    "__init__.py": (
        "from .core import Own\n"
        "from .sub import Thing, plain\n"
        "from .sub.inner import Unexported\n"
        '__all__ = ["Own", "Thing", "plain", "Unexported"]\n'
    ),
    "core.py": 'class Own:\n    """Defined in a file of this package."""\n',
    "sub/__init__.py": (
        "from ..core import Own\n"
        "from .inner import Thing, plain\n"
        '__all__ = ["Own", "Thing", "plain"]\n'
    ),
    "sub/inner.py": (
        'class Thing:\n    """A thing."""\n\n\nplain = 1\n\n\n'
        'class Unexported:\n    """Not exported by sub."""\n'
    ),
}


def test_reexports_from_other_packages_become_a_linked_table(tmp_path: Path) -> None:
    """Own-file names stay; names another package exports move to the table, linked to it when
    documented; a name its package does not export stays documented here."""
    for name, text in FILES.items():
        (tmp_path / "pkg" / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "pkg" / name).write_text(text, encoding="utf-8")
    loaded = griffe.load(
        "pkg", search_paths=[tmp_path], extensions=griffe.load_extensions(Exports())
    )
    assert isinstance(loaded, griffe.Module)
    assert {"Own", "Unexported"} <= set(loaded.members)
    assert "Thing" not in loaded.members and "plain" not in loaded.members
    assert loaded.docstring is not None
    assert "| [`Thing`][pkg.sub.Thing] | `pkg.sub` |" in loaded.docstring.value
    assert "| `plain` | `pkg.sub` |" in loaded.docstring.value
    # A subpackage gets the same: its own files' names stay, its parent's go to the table
    sub = loaded["sub"]
    assert "Thing" in sub.members and "Own" not in sub.members
    assert "| [`Own`][pkg.Own] | `pkg` |" in sub.docstring.value
