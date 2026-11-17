# LLM Works Docs

[![CI](https://github.com/llm-works/docs/actions/workflows/ci.yml/badge.svg)](https://github.com/llm-works/docs/actions/workflows/ci.yml)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

Shell and build for [docs.llm-works.ai](https://docs.llm-works.ai), the documentation site for
the LLM Works open-source packages.

This repo holds the site's structure, header, styling and build tooling. Package content
(guides, examples, docstrings) lives in each package's own repository and is fetched at a pinned
release tag during the build. Fixes to a package's docs go to that package's repository.

## Development

```bash
python -m pip install -e ".[dev]"
make check          # format, lint, type check, tests
make help           # every target
```

## Branches and releases

- `develop` is the default branch; pull requests target it.
- `main` is what is live. A merge from `develop` into `main` is a release: it deploys the site.
- There are no version tags and nothing is published to PyPI.

## License

MIT, see [LICENSE](LICENSE). Package content keeps the license of the package it comes from.
