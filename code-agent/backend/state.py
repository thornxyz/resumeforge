"""Agent state schema for LangGraph workflow."""

from __future__ import annotations

from typing import List, Optional, TypedDict, Dict, Any


class AgentState(TypedDict, total=False):
    """Shared graph state passed between nodes.

    Attributes mirror the architectural design doc supplied in the migration
    requirements. Optional keys are marked so nodes can fill them incrementally
    without forcing defaults that might overwrite downstream work.
    """

    mode: str  # "ask" or "edit"
    current_document: str
    cursor_position: Optional[Dict[str, int]]
    context: str
    messages: List[Dict[str, Any]]
    user_request: str
    generated_code: Optional[str]
    compilation_result: Optional[Dict[str, Any]]
    iteration_count: int
    files_to_modify: List[str]
    agent_response: Optional[str]
    file_diffs: Optional[List[Dict[str, str]]]
    raw_llm_output: Optional[str]
    tools_used: Optional[List[str]]
    thread_id: Optional[str]


INITIAL_STATE: AgentState = {
    "mode": "ask",
    "current_document": "",
    "cursor_position": None,
    "context": "",
    "messages": [],
    "user_request": "",
    "generated_code": None,
    "compilation_result": None,
    "iteration_count": 0,
    "files_to_modify": [],
    "agent_response": None,
    "file_diffs": [],
    "raw_llm_output": None,
    "tools_used": [],
    "thread_id": None,
}
"""Default state bootstrap for new LangGraph sessions."""
