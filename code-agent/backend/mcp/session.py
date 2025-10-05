"""In-process MCP session exposing compiler and formatter tools."""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Dict

from langchain_mcp import MCPToolkit
from mcp import ClientSession
from mcp.types import CallToolResult, ListToolsResult, TextContent, Tool

from ..config import AgentConfig
from ..tools.compiler import compile_latex
from ..tools.formatter import format_latex

ToolFunction = Callable[[dict[str, Any]], Awaitable[dict[str, Any]] | dict[str, Any]]


TOOL_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "latex_compiler": {
        "description": "Compile LaTeX content into PDF and capture diagnostics.",
        "input_schema": {
            "type": "object",
            "properties": {
                "document": {"type": "string"},
            },
            "required": ["document"],
        },
    },
    "latex_formatter": {
        "description": "Format LaTeX content with consistent whitespace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "document": {"type": "string"},
            },
            "required": ["document"],
        },
    },
}


class InProcessMCPSession(ClientSession):
    """Minimal asynchronous session satisfying the MCPToolkit contract."""

    def __init__(self, tools: Dict[str, ToolFunction]):
        # Avoid calling super().__init__ to sidestep transport requirements.
        self._tools = tools
        self._tool_list: ListToolsResult | None = None

    async def initialize(self) -> None:
        if self._tool_list is None:
            tools = []
            for name, definition in TOOL_DEFINITIONS.items():
                tools.append(
                    Tool(
                        name=name,
                        description=definition.get("description", ""),
                        inputSchema=definition.get("input_schema", {"type": "object"}),
                        outputSchema=None,
                    )
                )
            self._tool_list = ListToolsResult(tools=tools)

    async def list_tools(self) -> ListToolsResult:
        if self._tool_list is None:
            await self.initialize()
        return self._tool_list

    async def call_tool(
        self, name: str, arguments: dict[str, Any] | None = None
    ) -> CallToolResult:
        if name not in self._tools:
            raise ValueError(f"Unknown MCP tool: {name}")
        arguments = arguments or {}
        result = self._tools[name](arguments)
        if asyncio.iscoroutine(result):
            result = await result  # type: ignore[assignment]
        text = TextContent(type="text", text=result.get("text", ""))
        return CallToolResult(content=[text], structuredContent=result, isError=False)


class MCPRegistry:
    """Provides MCP-backed tools available to nodes."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self._session = InProcessMCPSession(
            tools={
                "latex_compiler": self._compile_wrapper,
                "latex_formatter": self._format_wrapper,
            }
        )
        self._toolkit = MCPToolkit(session=self._session)
        self._tool_cache: dict[str, Any] | None = None
        self._invocations: list[str] = []

    async def initialize(self) -> None:
        await self._toolkit.initialize()
        tools = self._toolkit.get_tools()
        self._tool_cache = {tool.name: tool for tool in tools}

    async def ensure_initialized(self) -> None:
        if self._tool_cache is None:
            await self.initialize()

    async def call_tool(
        self, name: str, arguments: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        await self.ensure_initialized()
        result = await self._session.call_tool(name, arguments or {})
        self._invocations.append(name)
        payload: dict[str, Any] = {}
        if isinstance(result.structuredContent, dict):
            payload.update(result.structuredContent)
        text_blocks = [
            block.text for block in result.content if isinstance(block, TextContent)
        ]
        if text_blocks:
            payload.setdefault("text", "\n".join(text_blocks))
        payload.setdefault("is_error", result.isError)
        return payload

    def get_tool(self, name: str):
        if self._tool_cache is None:
            raise RuntimeError("MCP toolkit not initialized")
        return self._tool_cache[name]

    def drain_invocations(self) -> list[str]:
        names = list(self._invocations)
        self._invocations.clear()
        return names

    def _compile_wrapper(self, arguments: dict[str, Any]) -> dict[str, Any]:
        document = arguments.get("document", "")
        outcome = compile_latex(document, self.config)
        payload = outcome.to_dict()
        payload["text"] = (
            "Compilation succeeded"
            if outcome.status == "success"
            else "Compilation failed"
        )
        return payload

    def _format_wrapper(self, arguments: dict[str, Any]) -> dict[str, Any]:
        document = arguments.get("document", "")
        formatted = format_latex(document)
        return {"text": formatted, "formatted": formatted}
