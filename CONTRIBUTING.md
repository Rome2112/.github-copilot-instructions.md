# Contributing

Thanks for improving the Isomorphic Engine. Keep changes deterministic, reviewable, and easy to validate in CI.

## Local setup

Use Python 3.10 or newer. Create an isolated environment and install the project tooling:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip ruff



Pull request expectations
Keep changes scoped and understandable.
Preserve deterministic behavior and benchmark integrity.
Update docs when changing public-facing dashboard behavior or the repository interface.
Mention any operational or security considerations in the PR description.