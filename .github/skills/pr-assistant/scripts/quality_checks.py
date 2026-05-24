#!/usr/bin/env python3
"""Cross-platform quality checks before creating a PR."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import List, Tuple


CODE_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".jsx", ".vue"}
DEPENDENCY_FILES = {
    "requirements.txt",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
}
TEST_MARKERS = ("test", "spec", "__tests__", ".test.", ".spec.")
TODO_PATTERN = re.compile(r"\b(TODO|FIXME)\b")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run cross-platform PR quality checks.")
    parser.add_argument("target_branch", nargs="?", default="main", help="Target branch to compare against")
    parser.add_argument("--output", help="Optional output path for the JSON payload")
    return parser


def run_command(command: List[str]) -> Tuple[str, int, str]:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return result.stdout.strip(), result.returncode, result.stderr.strip()


def human_size(size: int) -> str:
    units = ["B", "KiB", "MiB", "GiB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)}{unit}"
            return f"{value:.1f}{unit}"
        value /= 1024
    return f"{size}B"


def changed_files(target_branch: str) -> List[str]:
    output, returncode, _ = run_command(["git", "diff", "--name-only", f"{target_branch}...HEAD"])
    if returncode != 0 or not output:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def add_check(checks: List[dict], name: str, status: str, message: str) -> None:
    checks.append({"name": name, "status": status, "message": message})


def has_test_marker(path_text: str) -> bool:
    lowered = path_text.lower()
    return any(marker in lowered for marker in TEST_MARKERS)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    checks: List[dict] = []

    output, _, _ = run_command(["git", "status", "--porcelain"])
    if output:
        add_check(checks, "uncommitted_changes", "warn", "There are uncommitted changes in the working directory")
    else:
        add_check(checks, "uncommitted_changes", "pass", "No uncommitted changes")

    merge_base, merge_base_code, merge_base_err = run_command(["git", "merge-base", "HEAD", args.target_branch])
    if merge_base_code != 0 or not merge_base:
        message = merge_base_err or f"Could not determine merge-base with {args.target_branch}"
        add_check(checks, "merge_conflicts", "warn", message)
    else:
        merge_tree, _, _ = run_command(["git", "merge-tree", merge_base, args.target_branch, "HEAD"])
        if "<<<<<<<" in merge_tree:
            add_check(checks, "merge_conflicts", "fail", f"Merge conflicts detected with {args.target_branch}")
        else:
            add_check(checks, "merge_conflicts", "pass", f"No merge conflicts with {args.target_branch}")

    output, returncode, _ = run_command(["git", "rev-list", "--count", f"{args.target_branch}..HEAD"])
    ahead = int(output) if returncode == 0 and output.isdigit() else 0
    if ahead == 0:
        add_check(checks, "branch_ahead", "fail", f"Current branch has no commits ahead of {args.target_branch}")
    else:
        add_check(checks, "branch_ahead", "pass", f"Branch is {ahead} commit(s) ahead of {args.target_branch}")

    files = changed_files(args.target_branch)

    todo_count = 0
    large_files: List[str] = []
    has_code_changes = False
    has_test_changes = False

    for relative_path in files:
        path = Path(relative_path)
        lowered = relative_path.lower()
        is_code_file = path.suffix.lower() in CODE_SUFFIXES
        if is_code_file:
            if has_test_marker(lowered):
                has_test_changes = True
            else:
                has_code_changes = True

        if not path.is_file():
            continue

        if is_code_file:
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                content = ""
            todo_count += len(TODO_PATTERN.findall(content))

        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        if size > 1024 * 1024:
            large_files.append(f"{relative_path} ({human_size(size)})")

    if todo_count:
        add_check(checks, "todo_comments", "warn", f"Found {todo_count} TODO/FIXME comment(s) in changed files")
    else:
        add_check(checks, "todo_comments", "pass", "No TODO/FIXME comments in changed files")

    if large_files:
        add_check(checks, "large_files", "warn", f"Large files detected: {', '.join(large_files)}")
    else:
        add_check(checks, "large_files", "pass", "No large files")

    if has_code_changes and not has_test_changes:
        add_check(checks, "test_coverage", "warn", "Code changes detected but no test file changes")
    elif has_code_changes and has_test_changes:
        add_check(checks, "test_coverage", "pass", "Test files updated with code changes")
    else:
        add_check(checks, "test_coverage", "pass", "No code changes requiring tests")

    if any(Path(file_path).name in DEPENDENCY_FILES for file_path in files):
        add_check(checks, "dependencies", "warn", "Dependency files changed - ensure they are properly reviewed")
    else:
        add_check(checks, "dependencies", "pass", "No dependency changes")

    payload = {
        "checks": checks,
        "summary": {
            "failures": sum(1 for check in checks if check["status"] == "fail"),
            "warnings": sum(1 for check in checks if check["status"] == "warn"),
        },
    }

    rendered = json.dumps(payload, indent=2)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())