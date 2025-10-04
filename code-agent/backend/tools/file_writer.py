"""Utilities for applying generated LaTeX edits to disk."""

from __future__ import annotations

import difflib
from pathlib import Path
from typing import Dict, List

from ..config import AgentConfig


class FileWriteError(RuntimeError):
    """Raised when a file modification fails validation."""


def _validate_path(path: Path, config: AgentConfig) -> None:
    if not path.suffix.lower() in config.allowed_file_extensions:
        raise FileWriteError(f"Modification of '{path}' is not permitted")
    if not path.exists():
        raise FileWriteError(f"File '{path}' does not exist")


def apply_changes(
    file_paths: List[str], new_content: str, config: AgentConfig
) -> List[Dict[str, str]]:
    diffs: List[Dict[str, str]] = []
    if not file_paths:
        return diffs

    for file_path in file_paths:
        path = Path(file_path).resolve()
        _validate_path(path, config)

        original_text = path.read_text(encoding="utf-8")
        if original_text == new_content:
            continue

        diff = "".join(
            difflib.unified_diff(
                original_text.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=str(path),
                tofile=str(path),
            )
        )
        path.write_text(new_content, encoding="utf-8")
        diffs.append({"file": str(path), "diff": diff})

    return diffs
