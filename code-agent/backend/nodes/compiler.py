"""Compilation node that validates generated LaTeX."""

from __future__ import annotations

import logging

from ..config import AgentConfig
from ..state import AgentState
from ..mcp.session import MCPRegistry


logger = logging.getLogger("resume_agent.compiler")


async def compile_document(
    state: AgentState, agent_config: AgentConfig, registry: MCPRegistry
) -> AgentState:
    latex_to_compile = (
        state.get("generated_code") or state.get("current_document") or ""
    )

    await registry.ensure_initialized()
    logger.info(
        "Running latex_compiler tool | content_len=%d",
        len(latex_to_compile),
    )
    payload = await registry.call_tool(
        "latex_compiler",
        {
            "document": latex_to_compile,
        },
    )

    status = payload.get("status", "error")
    errors = payload.get("errors") or []

    logger.info(
        "Compilation result | status=%s errors=%d",
        status,
        len(errors),
    )

    result: AgentState = {
        "compilation_result": payload,
    }

    if status == "error":
        error_lines = errors or ["Compilation failed"]
        result["agent_response"] = "\n".join(error_lines)
        result["generated_code"] = latex_to_compile
        result["current_document"] = latex_to_compile
        logger.warning("Compilation failed | first_error=%s", error_lines[0])
    else:
        result["generated_code"] = latex_to_compile
        result["current_document"] = latex_to_compile
        logger.info("Compilation succeeded | pdf_path=%s", payload.get("pdf_path"))

    return result
