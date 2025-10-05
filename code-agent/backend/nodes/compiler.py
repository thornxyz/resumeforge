"""Compilation node that validates generated LaTeX."""

from __future__ import annotations

from ..config import AgentConfig
from ..state import AgentState
from ..mcp.session import MCPRegistry


async def compile_document(
    state: AgentState, agent_config: AgentConfig, registry: MCPRegistry
) -> AgentState:
    latex_to_compile = (
        state.get("generated_code") or state.get("current_document") or ""
    )

    await registry.ensure_initialized()
    payload = await registry.call_tool(
        "latex_compiler",
        {
            "document": latex_to_compile,
        },
    )

    status = payload.get("status", "error")
    errors = payload.get("errors") or []

    result: AgentState = {
        "compilation_result": payload,
    }

    if status == "error":
        error_lines = errors or ["Compilation failed"]
        result["agent_response"] = "\n".join(error_lines)
        result["generated_code"] = latex_to_compile
    else:
        result["generated_code"] = latex_to_compile
        result["current_document"] = latex_to_compile

    return result
