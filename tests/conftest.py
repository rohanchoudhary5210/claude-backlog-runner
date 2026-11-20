import sys
from pathlib import Path

# The runner package lives inside the skill folder (plugin layout).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "claude-backlog-runner"))
