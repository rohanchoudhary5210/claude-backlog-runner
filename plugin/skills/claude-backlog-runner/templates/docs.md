# Template: bring docs up to date

Goal: docs that match what the code does today.

1. Use the scope in the issue. If none is given, start with README.md.
2. Compare the docs with the code: setup steps, commands, config options, file paths, examples. Run the documented commands where it's safe (no installs that change the system, no network calls to paid services).
3. Fix what's wrong or missing. Keep the existing tone and structure; don't rewrite what's already correct.
4. In the PR, list each change and why (e.g. "flag was renamed in src/cli.py").
5. Don't change code. If the code looks wrong rather than the docs, say so in the PR instead.
