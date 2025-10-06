"""Node that writes generated edits back to disk."""

from __future__ import annotations

import logging

from ..config import AgentConfig
from ..state import AgentState
from ..tools.file_writer import FileWriteError, apply_changes


logger = logging.getLogger("resume_agent.file_writer")


def apply_file_changes(state: AgentState, agent_config: AgentConfig) -> AgentState:
    files = state.get("files_to_modify", []) or []
    content = state.get("generated_code") or ""

    if not files or not content:
        logger.info(
            "No file changes requested | files=%d content_len=%d",
            len(files),
            len(content),
        )
        return {
            "file_diffs": [],
            "agent_response": state.get("agent_response", ""),
        }

    try:
        diffs = apply_changes(files, content, agent_config)
        response = state.get("agent_response") or "Changes applied successfully."
        logger.info("File writes applied | files=%s", ",".join(files))
        return {
            "file_diffs": diffs,
            "agent_response": response,
            "current_document": content,
            "iteration_count": 0,
        }
    except FileWriteError as exc:
        logger.exception("File write failed | files=%s", ",".join(files))
        return {
            "agent_response": f"File write failed: {exc}",
            "file_diffs": [],
        }
