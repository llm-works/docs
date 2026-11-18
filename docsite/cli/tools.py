# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""One CLI tool per build step."""

from typing import Any, ClassVar

from appinfra.app.tools import Tool, ToolConfig
from pydantic import ValidationError

from ..build import Build
from ..config import load_build_config
from ..fetch import FetchError
from ..sitenav import NavMarkupError
from ..stage import StageError

_STEP_ERRORS = (ValidationError, FetchError, StageError, NavMarkupError, OSError)


class _StepTool(Tool):
    """Loads the build config and runs one step; a failed step exits 1."""

    name: ClassVar[str]
    help_text: ClassVar[str]

    def __init__(self, parent: Any = None) -> None:
        """Register under the subclass's step name."""
        super().__init__(parent, ToolConfig(name=self.name, help_text=self.help_text))

    def run(self, **kwargs: Any) -> int:
        """Run the step; log and return 1 on a config, fetch, stage or nav error."""
        try:
            build = Build(self.lg, load_build_config(self.app.config))
            self._step(build)
        except _STEP_ERRORS as e:
            self.lg.error("build step failed", extra={"step": self.name, "exception": e})
            return 1
        return 0

    def _step(self, build: Build) -> None:
        """The step itself; each subclass calls one Build method."""
        raise NotImplementedError


class FetchTool(_StepTool):
    """Clone packages at their tags and download the nav partial."""

    name = "fetch"
    help_text = "Clone each package at its tag and download the main site's nav"

    def _step(self, build: Build) -> None:
        """Run Build.fetch."""
        build.fetch()


class StageTool(_StepTool):
    """Copy allowlisted docs into the site."""

    name = "stage"
    help_text = "Copy each package's allowlisted docs into the site's docs directory"

    def _step(self, build: Build) -> None:
        """Run Build.stage."""
        build.stage()


class NavTool(_StepTool):
    """Render the docs header from the fetched nav."""

    name = "nav"
    help_text = "Render the docs header from the fetched nav"

    def _step(self, build: Build) -> None:
        """Run Build.nav."""
        build.nav()


class BuildTool(_StepTool):
    """Run every step."""

    name = "build"
    help_text = "Fetch, stage and render the header"

    def _step(self, build: Build) -> None:
        """Run Build.all."""
        build.all()
