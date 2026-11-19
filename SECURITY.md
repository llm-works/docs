# Security Policy

## Reporting Security Vulnerabilities

**DO NOT** open a public GitHub issue for security vulnerabilities.

Use GitHub's private vulnerability reporting:
1. Go to the repository's **Security** tab
2. Click **"Report a vulnerability"**
3. Submit your confidential report

Include a description, steps to reproduce, the potential impact, and a suggested fix if you have
one.

### Response Timeline

- **Initial Response:** Within 48 hours
- **Triage & Assessment:** Within 7 days
- **Fix & Disclosure:** Coordinated with reporter

## Scope

This repository builds a static site. In scope: the build tooling, the GitHub Actions workflows,
and the site shell (header, scripts, styles). Issues in a package's own code or docs belong to that
package's repository and its security policy.

The build trusts its inputs: `etc/docsite.yaml`, the `INFRA_*` environment variables that
override it, and the llm-works package repositories at the refs it names. It does not defend
against a malicious config or package repository (for example a symlink or path in a package's
docs pointing outside them); reports that need control of those inputs are out of scope.
