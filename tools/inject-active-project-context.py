#!/usr/bin/env python3

from __future__ import annotations

from datetime import datetime, timezone
import json
import re
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

try:
    import yaml
except ModuleNotFoundError as exc:  # pragma: no cover - exercised via hook execution
    print(
        json.dumps(
            {
                "continue": True,
                "systemMessage": (
                    "agent-harness SessionStart hook failed: PyYAML is required. "
                    "Install it with `python -m pip install pyyaml`."
                ),
            },
            ensure_ascii=False,
        )
    )
    raise SystemExit(0) from exc


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "agent-harness.yaml"
DEFAULT_RUNTIME_DIR = REPO_ROOT / "runtime"
DEFAULT_SNAPSHOT_PATH = DEFAULT_RUNTIME_DIR / "active-project-context.json"


class HookError(Exception):
    pass


def is_relative_path(value: str) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    if value.startswith("~"):
        return False
    return not PurePosixPath(value).is_absolute() and not PureWindowsPath(value).is_absolute()


def resolve_repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (REPO_ROOT / path).resolve()


def repo_relative_string(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def read_hook_input() -> None:
    if sys.stdin.isatty():
        return

    raw = sys.stdin.read()
    if not raw.strip():
        return

    try:
        json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HookError(f"Hook stdin is not valid JSON: {exc}") from exc


def load_yaml(path: Path) -> Any:
    if not path.exists():
        raise HookError(f"File not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except yaml.YAMLError as exc:
        raise HookError(f"Failed to parse YAML at {path}: {exc}") from exc


def require_string(mapping: dict[str, Any], key: str, source: Path) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise HookError(f"{key} must be a non-empty string in {source}")
    return value.strip()


def normalize_string_list(value: Any, field_name: str, source: Path) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise HookError(f"{field_name} must be a list in {source}")

    items: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise HookError(f"{field_name}[{index}] must be a non-empty string in {source}")
        items.append(item.strip())
    return items


def load_project_snapshot(config_path: Path) -> dict[str, Any]:
    config = load_yaml(config_path)
    if not isinstance(config, dict):
        raise HookError(f"Config must be a mapping: {config_path}")

    active_project = require_string(config, "active_project", config_path)
    projects_dir = require_string(config, "projects_dir", config_path)
    if not is_relative_path(projects_dir):
        raise HookError(f"projects_dir must be relative to the agent-harness root: {projects_dir}")

    project_profile_path = resolve_repo_path(projects_dir) / f"{active_project}.yaml"
    project = load_yaml(project_profile_path)
    if not isinstance(project, dict):
        raise HookError(f"Project profile must be a mapping: {project_profile_path}")

    openspec_root = require_string(project, "openspec_root", project_profile_path)
    if not is_relative_path(openspec_root):
        raise HookError(f"openspec_root must be relative in {project_profile_path}")

    primary_repo = require_string(project, "primary_repo", project_profile_path)
    summary = require_string(project, "summary", project_profile_path)
    repos_value = project.get("repos")
    if not isinstance(repos_value, list) or not repos_value:
        raise HookError(f"repos must be a non-empty list in {project_profile_path}")

    repos: list[dict[str, Any]] = []
    repo_ids: set[str] = set()
    for index, repo_value in enumerate(repos_value):
        if not isinstance(repo_value, dict):
            raise HookError(f"repos[{index}] must be a mapping in {project_profile_path}")

        repo_id = require_string(repo_value, "id", project_profile_path)
        repo_root = require_string(repo_value, "root", project_profile_path)
        if not is_relative_path(repo_root):
            raise HookError(f"repos[{index}].root must be relative in {project_profile_path}")
        if repo_id in repo_ids:
            raise HookError(f"repos[{index}].id is duplicated in {project_profile_path}: {repo_id}")

        repo_ids.add(repo_id)
        repos.append(
            {
                "id": repo_id,
                "root": repo_root,
                "root_absolute": str(resolve_repo_path(repo_root)),
                "follow_files": normalize_string_list(
                    repo_value.get("follow_files"),
                    f"repos[{index}].follow_files",
                    project_profile_path,
                ),
                "default_checks": normalize_string_list(
                    repo_value.get("default_checks"),
                    f"repos[{index}].default_checks",
                    project_profile_path,
                ),
            }
        )

    if primary_repo not in repo_ids:
        raise HookError(f"primary_repo must match a repo id in {project_profile_path}")

    return {
        "active_project": active_project,
        "agent_harness_root": str(REPO_ROOT),
        "project_profile_path": repo_relative_string(project_profile_path),
        "openspec_root": openspec_root,
        "openspec_root_absolute": str(resolve_repo_path(openspec_root)),
        "primary_repo": primary_repo,
        "summary": re.sub(r"\s+", " ", summary).strip(),
        "repos": repos,
    }


def write_runtime_snapshot(output_path: Path, snapshot: dict[str, Any]) -> None:
    runtime_snapshot = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "generated_by": "SessionStart hook",
        **snapshot,
    }

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(runtime_snapshot, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise HookError(f"Failed to write runtime snapshot at {output_path}: {exc}") from exc


def build_system_message(snapshot: dict[str, Any], snapshot_path: Path) -> str:
    primary_repo_id = snapshot["primary_repo"]
    primary_repo = next(
        (repo for repo in snapshot["repos"] if repo["id"] == primary_repo_id),
        None,
    )
    default_checks = "None"
    primary_repo_root = "Unknown"
    if primary_repo is not None:
        primary_repo_root = primary_repo["root"]
        if primary_repo["default_checks"]:
            default_checks = "; ".join(primary_repo["default_checks"])

    lines = [
        "agent-harness active project context resolved at SessionStart.",
        "",
        f"- Active project: {snapshot['active_project']}",
        f"- Project profile: {snapshot['project_profile_path']}",
        f"- OpenSpec root: {snapshot['openspec_root']}",
        f"- Primary repo: {primary_repo_id}",
        f"- Primary repo root: {primary_repo_root}",
        f"- Default checks: {default_checks}",
        f"- Runtime snapshot: {repo_relative_string(snapshot_path)}",
        "",
        "Prefer this injected context over re-reading config unless the user asks or the injected context is insufficient.",
    ]
    return "\n".join(lines)


def hook_response(system_message: str | None = None) -> str:
    payload: dict[str, Any] = {"continue": True}
    if system_message:
        payload["systemMessage"] = system_message
    return json.dumps(payload, ensure_ascii=False)


def main() -> int:
    try:
        read_hook_input()
        snapshot = load_project_snapshot(DEFAULT_CONFIG_PATH)
        write_runtime_snapshot(DEFAULT_SNAPSHOT_PATH, snapshot)
    except HookError as exc:
        sys.stdout.write(hook_response(f"agent-harness SessionStart hook failed: {exc}"))
        return 0

    sys.stdout.write(hook_response(build_system_message(snapshot, DEFAULT_SNAPSHOT_PATH)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())