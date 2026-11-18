# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

# Settings use ?= so the environment and a Makefile.local (gitignored, assigned with :=) can
# override them; `make config` shows where each value came from.

# Configuration
APPINFRA_DEV_PKG_NAME ?= docsite

# Code quality strictness
# - true: Fail on any code quality violations (CI mode)
# - false: Report violations but don't fail (development mode)
APPINFRA_DEV_CQ_STRICT ?= true

# Include SPDX header check in `make check`; the license comes from pyproject.toml (MIT).
APPINFRA_DEV_CQ_SPDX ?= true

# No ruff rules reported as warnings only: they are enforced in pyproject's select
APPINFRA_DEV_CQ_LINT_SELECT ?= false

# Fail on duplicated code blocks and unused private definitions
APPINFRA_DEV_CQ_DUP ?= strict
APPINFRA_DEV_CQ_DEAD ?= strict

# Report tests that sit in another suite's directory, or leak process-wide state
APPINFRA_DEV_TEST_HEALTH ?= warn

# Test coverage threshold (percentage), measured over unit and integration tests
APPINFRA_PYTEST_COVERAGE_THRESHOLD ?= 95
APPINFRA_PYTEST_COVERAGE_MARKERS ?= unit or integration

# Docstring coverage threshold (percentage)
APPINFRA_DEV_DOCSTRING_THRESHOLD ?= 90

# Locate the framework once, before the first include; the environment and the command line
# can still name another copy.
ifeq ($(origin APPINFRA_SCRIPTS),undefined)
APPINFRA_SCRIPTS := $(shell appinfra scripts-path)
endif

# Include framework (config first: it loads Makefile.local). Makefile.docs is left out: it drives
# MkDocs, and this site is built with Zensical.
include $(APPINFRA_SCRIPTS)/make/Makefile.config
include $(APPINFRA_SCRIPTS)/make/Makefile.env
include $(APPINFRA_SCRIPTS)/make/Makefile.help
include $(APPINFRA_SCRIPTS)/make/Makefile.utils
include $(APPINFRA_SCRIPTS)/make/Makefile.dev
include $(APPINFRA_SCRIPTS)/make/Makefile.pytest
include $(APPINFRA_SCRIPTS)/make/Makefile.install
include $(APPINFRA_SCRIPTS)/make/Makefile.clean

# Site: `python -m docsite build` assembles docs/, the header and zensical.toml from the pinned
# packages and the main-site nav; Zensical renders them. Build inputs are docsite config in
# etc/docsite.yaml, overridable per key with INFRA_<SECTION>_<KEY> environment variables (e.g.
# INFRA_NAV_URL for a local main-site dev server). A Makefile.local exports them to the site
# targets only (`build serve: export INFRA_NAV_URL := ...`): appinfra's own tools read INFRA_*
# as well and reject paths their config does not declare.

# The dev server's address (Zensical's default); set SITE_ADDR := host:port in Makefile.local.
SITE_ADDR ?= localhost:8000

.PHONY: build serve

build: ## Build the docs site into site/
	python -m docsite build
	zensical build --clean

serve: ## Build the site inputs, then serve with live reload on SITE_ADDR (default localhost:8000)
	python -m docsite build
	zensical serve --dev-addr $(SITE_ADDR)
