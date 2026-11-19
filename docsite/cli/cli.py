# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""CLI entry point for the docs build."""

from appinfra.app import AppBuilder

from .tools import BuildTool


def main() -> int:
    """Build the app from etc/docsite.yaml and run the requested step."""
    app = (
        AppBuilder("docsite")
        .with_description("Build tooling for docs.llm-works.ai")
        # The repo root holds etc/docsite.yaml; origin is relative to this file.
        .config.with_spec("llm-works", "docsite", origin="../..")
        .done()
        .cli.with_all_flags()
        .done()
        .tools.with_tools(BuildTool())
        .done()
        .build()
    )
    result: int = app.main()
    return result
