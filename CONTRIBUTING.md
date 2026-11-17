# Contributing to llm-works/docs

This repository holds the site shell and build tooling. To fix or extend a package's guides,
examples or API docs, open a pull request on that package's repository instead; the site picks up
the change when its pinned release tag is bumped here.

## Development Setup

```bash
git clone https://github.com/llm-works/docs.git
cd docs

python -m pip install -e ".[dev]"
```

## Running Checks

```bash
make test           # unit tests
make check          # format, lint, type check, tests
```

## Sign-off (DCO)

We use the [Developer Certificate of Origin (DCO)](https://developercertificate.org). Every commit
must be signed off, asserting you have the right to submit it under the project's MIT license.

```bash
git commit -s -m "your commit message"
```

Forgot? Amend with `git commit --amend -s`.

## PR Process

- Fork the repo, work on a branch
- Ensure every commit has `Signed-off-by:`
- Open PR against `develop`
- Maintainer review + merge gate applies — not every PR will be merged

**Merge policy:** all PRs are squash-merged.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
