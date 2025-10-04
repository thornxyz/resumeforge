"""Node that writes generated edits back to disk."""

from __future__ import annotations

from ..config import AgentConfig
from ..state import AgentState
from ..tools.file_writer import FileWriteError, apply_changes


def apply_file_changes(state: AgentState, agent_config: AgentConfig) -> AgentState:
    files = state.get("files_to_modify", []) or []
    content = state.get("generated_code") or ""

    if not files or not content:
        return {
            "file_diffs": [],
            "agent_response": state.get("agent_response", ""),
        }

    try:
        diffs = apply_changes(files, content, agent_config)
        response = state.get("agent_response") or "Changes applied successfully."
        return {
            "file_diffs": diffs,
            "agent_response": response,
            "current_document": content,
            "iteration_count": 0,
        }
    except FileWriteError as exc:
        return {
            "agent_response": f"File write failed: {exc}",
            "file_diffs": [],
        }
