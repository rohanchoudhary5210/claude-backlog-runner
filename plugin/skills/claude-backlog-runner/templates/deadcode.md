# Template: remove dead code

Goal: delete code that nothing uses, safely.

1. Use the scope in the issue. If none is given, look across the repo.
2. Find candidates: functions, files, assets, exports and config keys with no references. Search the whole repo (including scenes/resources for game projects, e.g. Godot `.tscn`/`.tres`, and string-based lookups) before deciding something is unused.
3. Only remove what you're confident about. List "possibly unused but not removed" items separately in the PR with the reason.
4. Run the tests/build if the repo has them and include the result.
5. Keep the PR small and easy to review; split big cleanups into several issues instead.
