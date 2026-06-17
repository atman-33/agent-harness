#!/usr/bin/env python3
"""
Claude Code UserPromptSubmit hook: inject active project context on first message.

Reads the Claude Code hook payload from stdin, extracts the session_id, and
injects the full <tooling-context> XML as a systemMessage on the first user
message of each session only. Subsequent messages in the same session are
passed through unchanged.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_DIR = REPO_ROOT / ".agents" / "harness" / "runtime"
SESSIONS_DIR = RUNTIME_DIR / "claude-sessions"
INJECT_SCRIPT = Path(__file__).resolve().parent / "inject-active-project-context.py"


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        print(json.dumps({"continue": True}))
        return 0

    try:
        hook_input = json.loads(raw)
    except json.JSONDecodeError:
        print(json.dumps({"continue": True}))
        return 0

    session_id = hook_input.get("session_id", "")
    if not session_id:
        print(json.dumps({"continue": True}))
        return 0

    # Only inject context once per session.
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    marker = SESSIONS_DIR / f"{session_id}.done"
    if marker.exists():
        print(json.dumps({"continue": True}))
        return 0

    marker.touch()

    try:
        result = subprocess.run(
            [sys.executable, str(INJECT_SCRIPT), "--output-system-message"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        system_message = result.stdout.strip()
        if system_message:
            print(
                json.dumps(
                    {"continue": True, "systemMessage": system_message},
                    ensure_ascii=False,
                )
            )
        else:
            print(json.dumps({"continue": True}))
    except Exception as exc:
        print(
            json.dumps(
                {
                    "continue": True,
                    "systemMessage": f"agent-harness Claude Code hook failed: {exc}",
                }
            )
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
