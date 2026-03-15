from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


DEFAULT_REGISTRY_PATH = "configs/projects.yml"


class DeepConfigError(RuntimeError):
    pass


def _read_yaml_file(path: str) -> Any:
    p = Path(path)
    try:
        raw = p.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise DeepConfigError(f"YAML file not found: {path}") from e
    except OSError as e:
        raise DeepConfigError(f"Failed to read YAML file {path}: {e}") from e

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        raise DeepConfigError(f"Invalid YAML in {path}: {e}") from e

    if data is None:
        raise DeepConfigError(f"Empty YAML file: {path}")

    return data


def _ensure_mapping(value: Any, *, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DeepConfigError(f"Expected a mapping at {where}, got {type(value).__name__}")
    return value


def load_project_registry(path: str = DEFAULT_REGISTRY_PATH) -> dict[int, str]:
    """
    Load the project registry YAML.

    Expected shape:
      {"projects": {<project_id>: {"config_path": <path>}}}
    """
    data = _read_yaml_file(path)
    root = _ensure_mapping(data, where=f"{path} (root)")

    projects_any = root.get("projects")
    projects = _ensure_mapping(projects_any, where=f"{path}.projects")

    out: dict[int, str] = {}
    for project_id_raw, entry_raw in projects.items():
        try:
            project_id = int(project_id_raw)
        except (TypeError, ValueError) as e:
            raise DeepConfigError(
                f"Invalid project id key in {path}.projects: {project_id_raw!r} (must be int-like)"
            ) from e

        entry = _ensure_mapping(entry_raw, where=f"{path}.projects[{project_id_raw!r}]")
        config_path = entry.get("config_path")
        if not isinstance(config_path, str) or not config_path.strip():
            raise DeepConfigError(
                f"Missing/invalid config_path for project {project_id} in {path} (must be non-empty string)"
            )
        out[project_id] = config_path

    return out


def load_project_deep_config(config_path: str) -> dict[str, Any]:
    data = _read_yaml_file(config_path)
    return _ensure_mapping(data, where=f"{config_path} (root)")
