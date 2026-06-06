#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[4]
HARNESS_HOME = REPO_ROOT / ".agents" / "harness"
DEFAULT_CONFIG_PATH = HARNESS_HOME / "config" / "agent-harness.yaml"
DEFAULT_PROJECTS_DIR = HARNESS_HOME / "projects"
SESSION_CONFIG_VERSION = 2
ALLOWED_PROFILE_KEYS = {"id", "openspec_root", "repos", "summary"}
ALLOWED_REPO_KEYS = {"id", "root", "follow_files", "default_checks"}


class ProfileError(Exception):
    pass


def fail(message: str) -> "NoReturn":
    print(message, file=sys.stderr)
    raise SystemExit(1)


def resolve_repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (REPO_ROOT / path).resolve()


def repo_relative_string(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def is_relative_path(value: str) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    if value.startswith("~"):
        return False
    return not PurePosixPath(value).is_absolute() and not PureWindowsPath(value).is_absolute()


def load_yaml(path: Path) -> Any:
    if not path.exists():
        fail(f"File not found: {path}")
    try:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except yaml.YAMLError as exc:
        fail(f"Failed to parse YAML at {path}: {exc}")


def config_path_from_arg(value: str) -> Path:
    return resolve_repo_path(value)


def profile_path_for_project(project_id: str) -> Path:
    return DEFAULT_PROJECTS_DIR / f"{project_id}.yaml"


def normalize_string_list(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ProfileError(f"{field_name} must be a list of strings")
    items: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ProfileError(f"{field_name}[{index}] must be a non-empty string")
        items.append(item.strip())
    return items


def normalize_optional_summary(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ProfileError("summary must be a string")
    return value.rstrip()


def normalize_project_ids(values: list[str]) -> list[str]:
    project_ids: list[str] = []
    seen_ids: set[str] = set()
    for index, value in enumerate(values):
        if not isinstance(value, str) or not value.strip():
            raise ProfileError(f"project_id[{index}] must be a non-empty string")
        project_id = value.strip()
        if project_id in seen_ids:
            raise ProfileError(f"project_id is duplicated: {project_id}")
        seen_ids.add(project_id)
        project_ids.append(project_id)
    return project_ids


def resolve_openspec_config(
    active_projects: list[str],
    openspec_mode: str | None,
    openspec_project_id: str | None,
) -> dict[str, str]:
    mode = openspec_mode or "project"
    if mode not in {"project", "harness"}:
        raise ProfileError("openspec_mode must be 'project' or 'harness'")

    if mode == "harness":
        if openspec_project_id is not None:
            raise ProfileError("openspec_project_id cannot be used when openspec_mode is 'harness'")
        return {"mode": "harness"}

    project_id = (openspec_project_id or active_projects[0]).strip()
    if project_id not in active_projects:
        raise ProfileError("openspec_project_id must match one active project")
    return {"mode": "project", "project_id": project_id}


def render_session_config(active_projects: list[str], openspec: dict[str, str]) -> str:
    lines = [
        f"version: {SESSION_CONFIG_VERSION}",
        "",
        "# Project ids to include in the active session context.",
        "active_projects:",
    ]
    lines.extend(f"  - {render_scalar(project_id)}" for project_id in active_projects)
    lines.extend(
        [
            "",
            "# OpenSpec source to use for the current session.",
            "# mode: project -> use the selected active project's openspec/ directory.",
            "#   project_id is required and must be listed in active_projects.",
            "# mode: harness -> use agent-harness/openspec.",
            "#   omit project_id when using harness mode.",
            "openspec:",
            f"  mode: {render_scalar(openspec['mode'])}",
        ]
    )
    if openspec["mode"] == "project":
        lines.append(f"  project_id: {render_scalar(openspec['project_id'])}")
    return "\n".join(lines) + "\n"


def normalize_repo(repo: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(repo, dict):
        raise ProfileError(f"{field_name} must be a mapping")
    extra_keys = sorted(set(repo) - ALLOWED_REPO_KEYS)
    if extra_keys:
        raise ProfileError(f"{field_name} has unsupported keys: {', '.join(extra_keys)}")

    repo_id = repo.get("id")
    root = repo.get("root")
    if not isinstance(repo_id, str) or not repo_id.strip():
        raise ProfileError(f"{field_name}.id must be a non-empty string")
    if not isinstance(root, str) or not root.strip():
        raise ProfileError(f"{field_name}.root must be a non-empty string")

    return {
        "id": repo_id.strip(),
        "root": root.strip(),
        "follow_files": normalize_string_list(repo.get("follow_files"), f"{field_name}.follow_files"),
        "default_checks": normalize_string_list(repo.get("default_checks"), f"{field_name}.default_checks"),
    }


def normalize_profile(profile: Any) -> dict[str, Any]:
    if not isinstance(profile, dict):
        raise ProfileError("Profile must be a mapping")

    extra_keys = sorted(set(profile) - ALLOWED_PROFILE_KEYS)
    if extra_keys:
        raise ProfileError(f"Profile has unsupported keys: {', '.join(extra_keys)}")

    project_id = profile.get("id")
    openspec_root = profile.get("openspec_root")
    summary = profile.get("summary")
    repos_value = profile.get("repos")

    if not isinstance(project_id, str) or not project_id.strip():
        raise ProfileError("id must be a non-empty string")
    if not isinstance(openspec_root, str) or not openspec_root.strip():
        raise ProfileError("openspec_root must be a non-empty string")
    if not isinstance(repos_value, list) or not repos_value:
        raise ProfileError("repos must be a non-empty list")

    repos = [normalize_repo(repo, f"repos[{index}]") for index, repo in enumerate(repos_value)]

    return {
        "id": project_id.strip(),
        "openspec_root": openspec_root.strip(),
        "repos": repos,
        "summary": normalize_optional_summary(summary),
    }


def validate_profile(profile: Any, allow_missing_paths: bool) -> tuple[dict[str, Any], list[str]]:
    normalized = normalize_profile(profile)
    warnings: list[str] = []

    if not is_relative_path(normalized["openspec_root"]):
        raise ProfileError("openspec_root must be relative to the agent-harness root")

    openspec_root = resolve_repo_path(normalized["openspec_root"])
    if not allow_missing_paths and not openspec_root.exists():
        raise ProfileError(f"openspec_root does not exist: {normalized['openspec_root']}")
    if openspec_root.exists() and not (openspec_root / "openspec").exists():
        warnings.append(f"openspec directory not found under {normalized['openspec_root']}")

    seen_repo_ids: set[str] = set()
    for index, repo in enumerate(normalized["repos"]):
        repo_id = repo["id"]
        if repo_id in seen_repo_ids:
            raise ProfileError(f"repos[{index}].id is duplicated: {repo_id}")
        seen_repo_ids.add(repo_id)

        if not is_relative_path(repo["root"]):
            raise ProfileError(f"repos[{index}].root must be relative to the agent-harness root")

        repo_root = resolve_repo_path(repo["root"])
        if not allow_missing_paths and not repo_root.exists():
            raise ProfileError(f"repos[{index}].root does not exist: {repo['root']}")

        for follow_index, follow_file in enumerate(repo["follow_files"]):
            if not is_relative_path(follow_file):
                raise ProfileError(
                    f"repos[{index}].follow_files[{follow_index}] must be relative to the agent-harness root"
                )
            follow_path = resolve_repo_path(follow_file)
            if not allow_missing_paths and not follow_path.exists():
                warnings.append(f"follow_file not found: {follow_file}")

    return normalized, warnings


def render_scalar(value: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_./ -]+", value):
        return value
    return json.dumps(value, ensure_ascii=False)


def render_list(key: str, items: list[str], indent: str) -> list[str]:
    if not items:
        return [f"{indent}{key}: []"]
    lines = [f"{indent}{key}:"]
    lines.extend(f"{indent}  - {render_scalar(item)}" for item in items)
    return lines


def render_profile(profile: dict[str, Any]) -> str:
    lines = [
        f"id: {render_scalar(profile['id'])}",
        "",
        "# Root path, relative to the agent-harness root, whose openspec/ directory stores",
        "# the change artifacts for this work unit.",
        f"openspec_root: {render_scalar(profile['openspec_root'])}",
        "",
        "# Repositories that participate in this work unit.",
        "repos:",
    ]

    for repo in profile["repos"]:
        lines.extend(
            [
                f"  - id: {render_scalar(repo['id'])}",
                f"    root: {render_scalar(repo['root'])}",
                "",
                "    # Optional files to read after opening the repository.",
            ]
        )
        lines.extend(render_list("follow_files", repo["follow_files"], "    "))
        lines.extend(
            [
                "",
                "    # Optional repository-specific validation commands.",
            ]
        )
        lines.extend(render_list("default_checks", repo["default_checks"], "    "))
        lines.append("")

    if profile["summary"]:
        lines.extend(["summary: |"])
        for summary_line in profile["summary"].splitlines():
            lines.append(f"  {summary_line}")
    else:
        lines.append('summary: ""')
    return "\n".join(lines) + "\n"


def parse_repo_json(values: list[str]) -> list[dict[str, Any]]:
    repos: list[dict[str, Any]] = []
    for index, value in enumerate(values):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ProfileError(f"repo-json[{index}] is not valid JSON: {exc}") from exc
        repos.append(normalize_repo(parsed, f"repo-json[{index}]"))
    return repos


def write_profile_file(path: Path, profile: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_profile(profile), encoding="utf-8")


def print_result(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def command_set_active(args: argparse.Namespace) -> None:
    config_path = config_path_from_arg(args.config_path)
    try:
        active_projects = normalize_project_ids(args.project_id)
    except ProfileError as exc:
        fail(str(exc))

    warnings: list[str] = []
    profile_paths: list[str] = []
    for project_id in active_projects:
        profile_path = profile_path_for_project(project_id)
        if not profile_path.exists():
            fail(f"Project profile does not exist: {repo_relative_string(profile_path)}")
        profile_paths.append(repo_relative_string(profile_path))

        profile_data = load_yaml(profile_path)
        try:
            _, profile_warnings = validate_profile(profile_data, args.allow_missing_paths)
        except ProfileError as exc:
            fail(str(exc))
        warnings.extend(f"{project_id}: {warning}" for warning in profile_warnings)

    try:
        openspec = resolve_openspec_config(active_projects, args.openspec_mode, args.openspec_project_id)
    except ProfileError as exc:
        fail(str(exc))

    config_path.write_text(render_session_config(active_projects, openspec), encoding="utf-8")
    print_result(
        {
            "status": "ok",
            "command": "set-active",
            "active_projects": active_projects,
            "openspec": openspec,
            "config_path": repo_relative_string(config_path),
            "profile_paths": profile_paths,
            "warnings": warnings,
        }
    )


def command_create_profile(args: argparse.Namespace) -> None:
    config_path = config_path_from_arg(args.config_path)
    profile_path = profile_path_for_project(args.project_id)
    if profile_path.exists() and not args.force:
        fail(f"Profile already exists: {repo_relative_string(profile_path)}")

    try:
        profile, warnings = validate_profile(
            {
                "id": args.project_id,
                "openspec_root": args.openspec_root,
                "repos": parse_repo_json(args.repo_json),
                "summary": args.summary,
            },
            args.allow_missing_paths,
        )
    except ProfileError as exc:
        fail(str(exc))

    write_profile_file(profile_path, profile)
    print_result(
        {
            "status": "ok",
            "command": "create-profile",
            "project_id": profile["id"],
            "profile_path": repo_relative_string(profile_path),
            "warnings": warnings,
        }
    )


def command_update_profile(args: argparse.Namespace) -> None:
    config_path = config_path_from_arg(args.config_path)
    profile_path = profile_path_for_project(args.project_id)
    if not profile_path.exists():
        fail(f"Profile does not exist: {repo_relative_string(profile_path)}")

    try:
        profile = normalize_profile(load_yaml(profile_path))
    except ProfileError as exc:
        fail(str(exc))

    changed = False
    if args.openspec_root is not None:
        profile["openspec_root"] = args.openspec_root
        changed = True
    if args.summary is not None:
        profile["summary"] = args.summary
        changed = True

    repos = list(profile["repos"])
    if args.replace_repos:
        repos = []
        changed = True

    if args.remove_repo:
        remove_ids = set(args.remove_repo)
        existing_ids = {repo["id"] for repo in repos}
        missing_ids = sorted(remove_ids - existing_ids)
        if missing_ids:
            fail(f"Cannot remove unknown repo ids: {', '.join(missing_ids)}")
        repos = [repo for repo in repos if repo["id"] not in remove_ids]
        changed = True

    try:
        repo_updates = parse_repo_json(args.repo_json)
    except ProfileError as exc:
        fail(str(exc))

    if repo_updates:
        changed = True
        by_id = {repo["id"]: index for index, repo in enumerate(repos)}
        for repo in repo_updates:
            if repo["id"] in by_id:
                repos[by_id[repo["id"]]] = repo
            else:
                by_id[repo["id"]] = len(repos)
                repos.append(repo)

    if not changed:
        fail("No changes requested. Provide at least one update option.")

    profile["repos"] = repos

    try:
        normalized, warnings = validate_profile(profile, args.allow_missing_paths)
    except ProfileError as exc:
        fail(str(exc))

    write_profile_file(profile_path, normalized)
    print_result(
        {
            "status": "ok",
            "command": "update-profile",
            "project_id": normalized["id"],
            "profile_path": repo_relative_string(profile_path),
            "warnings": warnings,
        }
    )


def command_validate_profile(args: argparse.Namespace) -> None:
    if args.project_id:
        profile_path = profile_path_for_project(args.project_id)
    else:
        profile_path = resolve_repo_path(args.profile_path)

    data = load_yaml(profile_path)
    try:
        normalized, warnings = validate_profile(data, args.allow_missing_paths)
    except ProfileError as exc:
        fail(str(exc))

    print_result(
        {
            "status": "ok",
            "command": "validate-profile",
            "project_id": normalized["id"],
            "profile_path": repo_relative_string(profile_path),
            "warnings": warnings,
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage agent-harness project configuration.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    set_active = subparsers.add_parser(
        "set-active",
        help="Update active_projects and openspec in .agents/harness/config/agent-harness.yaml",
    )
    set_active.add_argument("--project-id", action="append", required=True)
    set_active.add_argument("--openspec-mode", choices=["project", "harness"])
    set_active.add_argument("--openspec-project-id")
    set_active.add_argument("--config-path", default=repo_relative_string(DEFAULT_CONFIG_PATH))
    set_active.add_argument("--allow-missing-paths", action="store_true")
    set_active.set_defaults(func=command_set_active)

    create_profile = subparsers.add_parser(
        "create-profile",
        help="Create a profile under .agents/harness/projects/",
    )
    create_profile.add_argument("--project-id", required=True)
    create_profile.add_argument("--openspec-root", required=True)
    create_profile.add_argument("--summary", default="")
    create_profile.add_argument("--repo-json", action="append", default=[], required=True)
    create_profile.add_argument("--config-path", default=repo_relative_string(DEFAULT_CONFIG_PATH))
    create_profile.add_argument("--force", action="store_true")
    create_profile.add_argument("--allow-missing-paths", action="store_true")
    create_profile.set_defaults(func=command_create_profile)

    update_profile = subparsers.add_parser("update-profile", help="Update an existing profile")
    update_profile.add_argument("--project-id", required=True)
    update_profile.add_argument("--openspec-root")
    update_profile.add_argument("--summary")
    update_profile.add_argument("--repo-json", action="append", default=[])
    update_profile.add_argument("--remove-repo", action="append", default=[])
    update_profile.add_argument("--replace-repos", action="store_true")
    update_profile.add_argument("--config-path", default=repo_relative_string(DEFAULT_CONFIG_PATH))
    update_profile.add_argument("--allow-missing-paths", action="store_true")
    update_profile.set_defaults(func=command_update_profile)

    validate_profile_parser = subparsers.add_parser("validate-profile", help="Validate a profile")
    target_group = validate_profile_parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--project-id")
    target_group.add_argument("--profile-path")
    validate_profile_parser.add_argument("--config-path", default=repo_relative_string(DEFAULT_CONFIG_PATH))
    validate_profile_parser.add_argument("--allow-missing-paths", action="store_true")
    validate_profile_parser.set_defaults(func=command_validate_profile)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()