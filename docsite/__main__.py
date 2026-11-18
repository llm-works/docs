# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Allow running as `python -m docsite`."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
