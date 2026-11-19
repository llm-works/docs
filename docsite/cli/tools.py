# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright 2026 The llm-works-docs Authors

"""The CLI's one tool: the build."""

from typing import Any

from appinfra.app.tools import Tool, ToolConfig

from ..build import Build
from ..config import load_build_config
from ..fetch import FetchError
from ..reference import ReferenceSourceError
from ..siteconf import SiteConfigError
from ..stage import StageError

# ValueError covers an invalid config, the nav markup, the docs tree and the base TOML
_BUILD_ERRORS = (
    ValueError,
    FetchError,
    StageError,
    SiteConfigError,
    ReferenceSourceError,
    OSError,
)


class BuildTool(Tool):
    """Fetch, stage, and render the header and the Zensical config; a failure exits 1."""

    def __init__(self, parent: Any = None) -> None:
        """Register as `build`."""
        help_text = "Fetch, stage, and render the header and the Zensical config"
        super().__init__(parent, ToolConfig(name="build", help_text=help_text))

    def run(self, **kwargs: Any) -> int:
        """Run every build step; log and return 1 on a known error."""
        try:
            Build(self.lg, load_build_config(self.app.config)).all()
        except _BUILD_ERRORS as e:
            self.lg.error("build failed", extra={"exception": e})
            return 1
        return 0
