"""LangGraph-powered LaTeX coding agent."""

from __future__ import annotations

from functools import partial
from typing import Any, Dict
from uuid import uuid4

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .config import AgentConfig, load_config
from .state import AgentState, INITIAL_STATE
from .mcp.session import MCPRegistry
from .nodes.mode_detector import detect_mode
from .nodes.parser import parse_context
from .nodes.llm import (
    ask_with_gemini,
    edit_with_gemini,
)
from .nodes.compiler import compile_document
from .nodes.formatter import format_document
from .nodes.file_writer import apply_file_changes


def _route_mode(state: AgentState) -> str:
    """Decide which branch to follow after mode detection."""
    mode = state.get("mode", "ask").lower()
    return "ask" if mode != "edit" else "edit"


def _route_compilation(state: AgentState, agent_config: AgentConfig) -> str:
    """Route based on compilation results and iteration limit."""
    result = state.get("compilation_result") or {}
    status = result.get("status")
    if (
        status == "error"
        and state.get("iteration_count", 0) < agent_config.max_iterations
    ):
        return "retry"
    return "success"


class LangGraphResumeAgent:
    """Coordinator that wires together the LangGraph workflow and exposes a simple API."""

    def __init__(self, config: AgentConfig | None = None):
        self.config = config or load_config()
        self._registry = MCPRegistry(self.config)
        self._graph = self._build_graph(self.config, self._registry)

    @staticmethod
    def _build_graph(config: AgentConfig, registry: MCPRegistry):
        graph = StateGraph(AgentState)
        memory = MemorySaver()

        graph.add_node("mode_detector", detect_mode)
        graph.add_node("parser", parse_context)
        graph.add_node("gemini_ask", partial(ask_with_gemini, agent_config=config))
        graph.add_node("gemini_edit", partial(edit_with_gemini, agent_config=config))
        graph.add_node(
            "compiler",
            partial(compile_document, agent_config=config, registry=registry),
        )
        graph.add_node(
            "formatter",
            partial(format_document, registry=registry),
        )
        graph.add_node("file_writer", partial(apply_file_changes, agent_config=config))

        graph.set_entry_point("mode_detector")

        graph.add_edge("mode_detector", "parser")
        graph.add_conditional_edges(
            "parser",
            _route_mode,
            {
                "ask": "gemini_ask",
                "edit": "gemini_edit",
            },
        )

        graph.add_edge("gemini_ask", END)
        graph.add_edge("gemini_edit", "compiler")
        graph.add_conditional_edges(
            "compiler",
            partial(_route_compilation, agent_config=config),
            {
                "retry": "gemini_edit",
                "success": "formatter",
            },
        )
        graph.add_edge("formatter", "file_writer")
        graph.add_edge("file_writer", END)

        return graph.compile(checkpointer=memory)

    async def ainvoke(self, state: AgentState | None = None) -> AgentState:
        """Run the graph asynchronously with the provided state."""
        initial_state: AgentState = dict(INITIAL_STATE)
        if state:
            initial_state.update({k: v for k, v in state.items() if v is not None})
        thread_id = initial_state.get("thread_id") or str(uuid4())
        initial_state["thread_id"] = thread_id

        await self._registry.ensure_initialized()
        result: AgentState = await self._graph.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": thread_id}},
        )
        result["thread_id"] = thread_id
        tools_used = self._registry.drain_invocations()
        if tools_used:
            result["tools_used"] = tools_used
        return result

    async def process(
        self,
        *,
        user_request: str,
        messages: list[Dict[str, Any]],
        current_document: str,
        mode: str | None = None,
        cursor_position: Dict[str, int] | None = None,
        files_to_modify: list[str] | None = None,
        thread_id: str | None = None,
    ) -> AgentState:
        """Convenience wrapper used by the FastAPI route."""
        state: AgentState = {
            "user_request": user_request,
            "messages": messages,
            "current_document": current_document,
            "cursor_position": cursor_position,
            "mode": mode or "ask",
            "files_to_modify": files_to_modify or [],
        }
        if thread_id:
            state["thread_id"] = thread_id
        return await self.ainvoke(state)
