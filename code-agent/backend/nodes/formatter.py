"""Formatter node applies consistent whitespace to LaTeX output."""

from __future__ import annotations

import logging

from ..state import AgentState
from ..mcp.session import MCPRegistry


logger = logging.getLogger("resume_agent.formatter")


async def format_document(state: AgentState, registry: MCPRegistry) -> AgentState:
    content = state.get("generated_code") or state.get("current_document") or ""
    await registry.ensure_initialized()
    logger.info("Running latex_formatter tool | content_len=%d", len(content))
    payload = await registry.call_tool("latex_formatter", {"document": content})
    formatted = payload.get("formatted") or payload.get("text") or content
    logger.info("Formatter complete | changed=%s", formatted != content)
    return {
        "generated_code": formatted,
    }
