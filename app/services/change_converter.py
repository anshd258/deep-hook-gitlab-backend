"""Convert GitLab MR changes API response into deep_hook GitLabChange list.

Filters and truncates changes so only review-relevant files are passed to the agent.
"""

from __future__ import annotations

import logging
from typing import Any

from deep_hook_review import GitLabChange

logger = logging.getLogger(__name__)

# File path patterns to skip (images, assets, lock files, build artifacts)
# Covers Spring/Java, Flutter, Node/Express, FastAPI and similar stacks.
_SKIP_EXTENSIONS = frozenset(
    {
        "png", "jpg", "jpeg", "gif", "svg", "webp", "ico", "avif",
        "woff", "woff2", "ttf", "eot", "otf",
        "mp4", "webm", "mov", "pdf", "mp3", "wav",
        "pyc", "class", "jar", "so", "dylib", "dll", "o", "a",
    }
)
_SKIP_FILENAMES = frozenset(
    {
        "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lock",
        "Gemfile.lock", "Pipfile.lock", "poetry.lock", "Cargo.lock", "go.sum",
        "Podfile.lock", "composer.lock",
    }
)
_SKIP_PATH_SEGMENTS = (
    "node_modules", "__pycache__", ".gradle", "target", ".dart_tool",
    "Pods", "dist", "build", ".next", ".nuxt", "venv", ".venv",
    ".git", ".idea", ".vscode",
)

DEFAULT_MAX_DIFF_LINES = 3000


def _should_skip_path(path: str) -> bool:
    if not path or not path.strip():
        return True
    p = path.strip().lower()
    if p.split("/")[-1] in _SKIP_FILENAMES:
        return True
    if "." in p:
        ext = p.rsplit(".", 1)[-1]
        if ext in _SKIP_EXTENSIONS:
            return True
    if p.endswith(".min.js") or p.endswith(".min.css"):
        return True
    for seg in _SKIP_PATH_SEGMENTS:
        if f"/{seg}/" in f"/{p}/" or p.startswith(seg + "/") or p == seg:
            return True
    return False


def gitlab_changes_to_deep_hook(
    raw_response: dict[str, Any],
    *,
    max_diff_lines: int = DEFAULT_MAX_DIFF_LINES,
) -> list[GitLabChange]:
    """
    Convert GitLab MR changes API response into a list of GitLabChange for deep_hook.

    Filters out images, assets, lock files, Pod files, and non-essential build/dep
    paths (Spring/Java, Flutter, Node/Express, FastAPI, etc.). Truncates large diffs.
    """
    raw_changes = raw_response.get("changes") or []
    out: list[GitLabChange] = []

    for c in raw_changes:
        if not isinstance(c, dict):
            continue
        new_path = (c.get("new_path") or c.get("old_path") or "").strip()
        old_path = (c.get("old_path") or new_path or "").strip()
        if _should_skip_path(new_path) and _should_skip_path(old_path):
            logger.debug("Skipping non-essential path: %s", new_path or old_path)
            continue

        diff = (c.get("diff") or "").strip()
        if diff:
            lines = diff.split("\n")
            if len(lines) > max_diff_lines:
                diff = "\n".join(lines[:max_diff_lines]) + "\n\n... [truncated]\n"

        out.append(
            GitLabChange(
                old_path=old_path,
                new_path=new_path,
                a_mode=str(c.get("a_mode") or "100644"),
                b_mode=str(c.get("b_mode") or "100644"),
                diff=diff,
                new_file=bool(c.get("new_file")),
                renamed_file=bool(c.get("renamed_file")),
                deleted_file=bool(c.get("deleted_file")),
            )
        )
    return out
