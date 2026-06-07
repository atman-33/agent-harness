#!/usr/bin/env python3

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import re
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any
from xml.sax.saxutils import escape

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


REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS_HOME = REPO_ROOT / ".agents" / "harness"
DEFAULT_CONFIG_PATH = HARNESS_HOME / "config" / "agent-harness.yaml"
DEFAULT_PROJECTS_DIR = HARNESS_HOME / "projects"
DEFAULT_RUNTIME_DIR = HARNESS_HOME / "runtime"
DEFAULT_SNAPSHOT_PATH = DEFAULT_RUNTIME_DIR / "active-project-context.json"
FOLLOW_FILES_INSTRUCTION = "Read these files before acting in this repo unless they are clearly irrelevant to the task."


class HookError(Exception):
    pass


def is_relative_path(value: str) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    if value.startswith("~"):
        return False
    return (
        not PurePosixPath(value).is_absolute()
        and not PureWindowsPath(value).is_absolute()
    )


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
            raise HookError(
                f"{field_name}[{index}] must be a non-empty string in {source}"
            )
        items.append(item.strip())
    return items


def require_mapping(mapping: dict[str, Any], key: str, source: Path) -> dict[str, Any]:
    value = mapping.get(key)
    if not isinstance(value, dict):
        raise HookError(f"{key} must be a mapping in {source}")
    return value


def require_unique_strings(value: Any, field_name: str, source: Path) -> list[str]:
    items = normalize_string_list(value, field_name, source)
    duplicates = sorted({item for item in items if items.count(item) > 1})
    if duplicates:
        raise HookError(
            f"{field_name} contains duplicates in {source}: {', '.join(duplicates)}"
        )
    return items


def normalize_optional_summary(value: Any, source: Path) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise HookError(f"summary must be a string in {source}")
    return re.sub(r"\s+", " ", value).strip()


def load_session_config(config_path: Path) -> dict[str, Any]:
    config = load_yaml(config_path)
    if not isinstance(config, dict):
        raise HookError(f"Config must be a mapping: {config_path}")

    version = config.get("version")
    if version != 2:
        raise HookError(f"version must be 2 in {config_path}")

    active_projects = require_unique_strings(
        config.get("active_projects"), "active_projects", config_path
    )
    openspec = require_mapping(config, "openspec", config_path)
    mode = require_string(openspec, "mode", config_path)
    if mode not in {"project", "harness"}:
        raise HookError(
            f"openspec.mode must be 'project' or 'harness' in {config_path}"
        )

    project_id = None
    if mode == "project":
        project_id = require_string(openspec, "project_id", config_path)
        if active_projects and project_id not in active_projects:
            raise HookError(
                f"openspec.project_id must be listed in active_projects in {config_path}"
            )
    elif openspec.get("project_id") not in (None, ""):
        raise HookError(
            f"openspec.project_id must be omitted when openspec.mode is 'harness' in {config_path}"
        )

    return {
        "active_projects": active_projects,
        "openspec": {
            "mode": mode,
            "project_id": project_id,
        },
    }


def load_project_definition(project_id: str) -> dict[str, Any]:
    project_profile_path = DEFAULT_PROJECTS_DIR / f"{project_id}.yaml"
    project = load_yaml(project_profile_path)
    if not isinstance(project, dict):
        raise HookError(f"Project profile must be a mapping: {project_profile_path}")

    profile_id = require_string(project, "id", project_profile_path)
    if profile_id != project_id:
        raise HookError(
            f"Project profile id does not match filename in {project_profile_path}: expected {project_id}, got {profile_id}"
        )

    openspec_root = require_string(project, "openspec_root", project_profile_path)
    if not is_relative_path(openspec_root):
        raise HookError(f"openspec_root must be relative in {project_profile_path}")

    summary = normalize_optional_summary(project.get("summary"), project_profile_path)
    repos_value = project.get("repos")
    if not isinstance(repos_value, list) or not repos_value:
        raise HookError(f"repos must be a non-empty list in {project_profile_path}")

    repos: list[dict[str, Any]] = []
    repo_ids: set[str] = set()
    for index, repo_value in enumerate(repos_value):
        if not isinstance(repo_value, dict):
            raise HookError(
                f"repos[{index}] must be a mapping in {project_profile_path}"
            )

        repo_id = require_string(repo_value, "id", project_profile_path)
        repo_root = require_string(repo_value, "root", project_profile_path)
        if not is_relative_path(repo_root):
            raise HookError(
                f"repos[{index}].root must be relative in {project_profile_path}"
            )
        if repo_id in repo_ids:
            raise HookError(
                f"repos[{index}].id is duplicated in {project_profile_path}: {repo_id}"
            )

        repo_ids.add(repo_id)
        repos.append(
            {
                "id": repo_id,
                "qualified_id": f"{project_id}/{repo_id}",
                "root": repo_root,
                "root_absolute": str(resolve_repo_path(repo_root)).replace("\\", "/"),
                "follow_files": normalize_string_list(
                    repo_value.get("follow_files"),
                    f"repos[{index}].follow_files",
                    project_profile_path,
                ),
                "follow_files_absolute": [
                    str(resolve_repo_path(path)).replace("\\", "/")
                    for path in normalize_string_list(
                        repo_value.get("follow_files"),
                        f"repos[{index}].follow_files",
                        project_profile_path,
                    )
                ],
                "default_checks": normalize_string_list(
                    repo_value.get("default_checks"),
                    f"repos[{index}].default_checks",
                    project_profile_path,
                ),
            }
        )

    return {
        "id": project_id,
        "project_profile_path": repo_relative_string(project_profile_path),
        "project_profile_path_absolute": str(project_profile_path.resolve()).replace(
            "\\", "/"
        ),
        "openspec_root": openspec_root,
        "openspec_root_absolute": str(resolve_repo_path(openspec_root)).replace(
            "\\", "/"
        ),
        "openspec_path_absolute": str(
            (resolve_repo_path(openspec_root) / "openspec").resolve()
        ).replace("\\", "/"),
        "summary": summary,
        "repos": repos,
    }


def load_active_context(config_path: Path) -> dict[str, Any]:
    session_config = load_session_config(config_path)
    projects = [
        load_project_definition(project_id)
        for project_id in session_config["active_projects"]
    ]
    projects_by_id = {project["id"]: project for project in projects}

    openspec_mode = session_config["openspec"]["mode"]
    if openspec_mode == "harness":
        openspec_path = (REPO_ROOT / "openspec").resolve()
    else:
        openspec_path = Path(
            projects_by_id[session_config["openspec"]["project_id"]][
                "openspec_path_absolute"
            ]
        )

    return {
        "agent_harness_root": str(REPO_ROOT.resolve()).replace("\\", "/"),
        "active_projects": projects,
        "openspec": {
            "mode": openspec_mode,
            "path": str(openspec_path).replace("\\", "/"),
        },
    }


def write_runtime_snapshot(output_path: Path, snapshot: dict[str, Any]) -> None:
    runtime_snapshot = {
        "schema_version": 2,
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
        raise HookError(
            f"Failed to write runtime snapshot at {output_path}: {exc}"
        ) from exc


def xml_attribute(value: str) -> str:
    return escape(value, {'"': "&quot;"})


def xml_text(value: str) -> str:
    return escape(value)


def build_system_message(snapshot: dict[str, Any], snapshot_path: Path) -> str:
    lines: list[str] = ["<tooling-context>"]
    lines.append(
        f'  <agent-harness root-path="{xml_attribute(snapshot["agent_harness_root"])}" runtime-snapshot="{xml_attribute(str(snapshot_path.resolve()).replace("\\", "/"))}" />'
    )
    lines.append(f'  <openspec path="{xml_attribute(snapshot["openspec"]["path"])}" />')
    lines.append("  <active-projects>")

    for project in snapshot["active_projects"]:
        lines.append(
            f'    <project id="{xml_attribute(project["id"])}" profile-path="{xml_attribute(project["project_profile_path_absolute"])}">'
        )
        if project["summary"]:
            lines.append(f"      <summary>{xml_text(project['summary'])}</summary>")
        lines.append("      <repos>")
        for repo in project["repos"]:
            lines.append(
                f'        <repo id="{xml_attribute(repo["id"])}" qualified-id="{xml_attribute(repo["qualified_id"])}" root-path="{xml_attribute(repo["root_absolute"])}">'
            )
            if repo["follow_files_absolute"]:
                lines.append(
                    f'          <follow-files instruction="{xml_attribute(FOLLOW_FILES_INSTRUCTION)}">'
                )
                for follow_file in repo["follow_files_absolute"]:
                    lines.append(
                        f'            <file path="{xml_attribute(follow_file)}" />'
                    )
                lines.append("          </follow-files>")
            if repo["default_checks"]:
                lines.append("          <default-checks>")
                for check in repo["default_checks"]:
                    lines.append(f"            <check>{xml_text(check)}</check>")
                lines.append("          </default-checks>")
            lines.append("        </repo>")
        lines.append("      </repos>")
        lines.append("    </project>")

    lines.append("  </active-projects>")
    lines.append("  <instructions>")
    lines.append(
        "    <instruction>Prefer this injected context, including the openspec path above, over re-reading harness config unless it is insufficient or User explicitly asks.</instruction>"
    )
    lines.append(
        "    <instruction>Before acting in a repo, read its follow-files unless they are clearly irrelevant, and run its default-checks when validation is needed.</instruction>"
    )
    lines.append("  </instructions>")
    lines.append("</tooling-context>")
    return "\n".join(lines)


def build_error_system_message(error_message: str, config_path: Path) -> str:
    lines: list[str] = ["<tooling-context>"]
    lines.append(
        f'  <agent-harness root-path="{xml_attribute(str(REPO_ROOT.resolve()).replace(chr(92), "/"))}" />'
    )
    lines.append("  <error>")
    lines.append(f"    <message>{xml_text(error_message)}</message>")
    lines.append(
        f'    <instruction>Please fix `{xml_text(repo_relative_string(config_path))}`.</instruction>'
    )
    lines.append("  </error>")
    lines.append("  <instructions>")
    lines.append(
        "    <instruction>agent-harness configuration has an error. Please review and fix the configuration file.</instruction>"
    )
    lines.append("  </instructions>")
    lines.append("</tooling-context>")
    return "\n".join(lines)


def hook_response(system_message: str | None = None) -> str:
    payload: dict[str, Any] = {"continue": True}
    if system_message:
        payload["systemMessage"] = system_message
    return json.dumps(payload, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inject active project context into agent system prompt."
    )
    parser.add_argument(
        "--output-system-message",
        action="store_true",
        help=(
            "Output only the system message XML text (no JSON wrapper, no stdin read). "
            "Useful for OpenCode plugin integration."
        ),
    )
    args = parser.parse_args()

    try:
        if not args.output_system_message:
            read_hook_input()
        snapshot = load_active_context(DEFAULT_CONFIG_PATH)
        write_runtime_snapshot(DEFAULT_SNAPSHOT_PATH, snapshot)
    except HookError as exc:
        if args.output_system_message:
            # Output the error details as a system message so the agent can prompt the user to fix it.
            print(build_error_system_message(str(exc), DEFAULT_CONFIG_PATH))
            return 0
        sys.stdout.write(
            hook_response(f"agent-harness SessionStart hook failed: {exc}")
        )
        return 0

    if args.output_system_message:
        print(build_system_message(snapshot, DEFAULT_SNAPSHOT_PATH))
    else:
        sys.stdout.write(
            hook_response(build_system_message(snapshot, DEFAULT_SNAPSHOT_PATH))
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
