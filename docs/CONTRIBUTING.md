# Contributing to WEALTH

Welcome to WEALTH — the capital intelligence organ of the arifOS Federation.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## Developer Certificate of Origin (DCO)

To ensure clear licensing and provenance, we require all contributors to sign off their commits using the Developer Certificate of Origin (DCO). By adding `Signed-off-by: Your Name <your.email@example.com>` to your commit messages (e.g., via `git commit -s`), you certify that you have the right to submit the code under the project's license.

## How to Contribute

1. **Fork the Repository:** Create a personal fork of the repository on GitHub.
2. **Create a Branch:** Create a branch for your changes (e.g., `feat/new-valuation-model` or `fix/npv-calculation`).
3. **Write Tests:** Ensure any new features or bug fixes are covered by the test suite. WEALTH has both Python (`pytest`) and Node.js (`npm test`) test suites.
4. **Format & Lint:** Run `ruff check . && ruff format .` for Python code before submitting.
5. **Submit a Pull Request:** Open a Pull Request against the `main` branch. Use conventional commits (`feat:`, `fix:`, `chore:`, `docs:`).

## Governance & License Note

All contributions to WEALTH are accepted under the terms of the [GNU Affero General Public License v3.0 (AGPL-3.0)](LICENSE). By contributing, you agree that your contributions will be licensed under AGPL-3.0.

**Important:** AGPL-3.0 requires that any modified version of WEALTH deployed as a network service must disclose its source code. This preserves the amanah (trust) — anyone who builds on this work must contribute back.
