"""Formatter node applies consistent whitespace to LaTeX output."""

from __future__ import annotations

from ..state import AgentState
from ..mcp.session import MCPRegistry


async def format_document(state: AgentState, registry: MCPRegistry) -> AgentState:
    content = state.get("generated_code") or state.get("current_document") or ""
    await registry.ensure_initialized()
    payload = await registry.call_tool("latex_formatter", {"document": content})
    formatted = payload.get("formatted") or payload.get("text") or content
    return {
        "generated_code": formatted,
    }
