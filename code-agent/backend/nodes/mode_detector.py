"""Mode detection node."""

from __future__ import annotations

import logging
from typing import Dict, List

from ..state import AgentState


logger = logging.getLogger("resume_agent.mode_detector")

ASK_KEYWORDS: List[str] = [
    "explain",
    "what is",
    "how does",
    "why",
    "tell me",
    "document",
]

EDIT_KEYWORDS: List[str] = [
    "add",
    "fix",
    "change",
    "update",
    "create",
    "modify",
    "replace",
    "insert",
]


def _contains_keyword(text: str, keywords: List[str]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def detect_mode(state: AgentState) -> AgentState:
    """Determine whether the incoming request is ASK or EDIT mode."""
    request = state.get("user_request") or ""
    explicit_mode = state.get("mode")

    mode = "ask"
    if explicit_mode and explicit_mode.lower() in {"ask", "edit"}:
        mode = explicit_mode.lower()
    elif _contains_keyword(request, EDIT_KEYWORDS):
        mode = "edit"
    elif _contains_keyword(request, ASK_KEYWORDS):
        mode = "ask"

    logger.info(
        "Mode detector results | explicit=%s detected=%s request_preview=%s",
        explicit_mode,
        mode,
        request[:80].replace("\n", " "),
    )

    next_state: AgentState = {
        "mode": mode,
    }

    if mode == "edit":
        next_state["iteration_count"] = state.get("iteration_count", 0)
    else:
        next_state["iteration_count"] = 0

    return next_state
