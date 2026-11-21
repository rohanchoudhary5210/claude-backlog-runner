# Template: add missing tests

Goal: raise confidence in existing code without changing its behaviour.

1. Use the scope in the issue (a file, folder or feature). If none is given, pick the most important module that has no tests.
2. Find the project's existing test setup (framework, folder, naming). If there is none, use the language's standard one and say so in the PR.
3. Write focused tests for current behaviour: normal cases, edge cases (empty, zero, missing input) and one error case. Don't change production code — if a test exposes a bug, mark that test as skipped/expected-failure with a note and report the bug in the PR.
4. Run the tests and include the command and result in the PR.
5. Keep it small: at most ~10 tests per PR.
