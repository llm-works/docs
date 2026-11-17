# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""Shared pytest configuration for all test suites."""

# Gives each test the suite of its marker or its tests/<suite>/ directory
pytest_plugins = ["appinfra.pytest_suites"]
