# Template: fix lint and formatting

Goal: clean up warnings without changing behaviour.

1. Use the project's own linter/formatter config if it has one (e.g. eslint, prettier, ruff, gdlint). Don't add a new tool or change its config.
2. If there is no linter set up, fix only obvious issues (unused imports/variables, inconsistent formatting) by hand and say so in the PR.
3. Don't change logic. If a warning needs a logic change, list it in the PR instead of fixing it.
4. Run the tests/build if available and include the result.
