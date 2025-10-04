"""Parser node for extracting LaTeX document insights."""

from __future__ import annotations

from ..state import AgentState
from ..utils.latex_parser import analyse_document


def parse_context(state: AgentState) -> AgentState:
    document = state.get("current_document", "") or ""
    cursor = state.get("cursor_position")

    insights = analyse_document(document, cursor)

    summary_lines = [
        f"Current section: {insights.current_section or 'Unknown'}",
        f"Detected packages: {', '.join(insights.packages) if insights.packages else 'None'}",
        f"Sections: {', '.join(insights.sections) if insights.sections else 'None'}",
        "Context snippet:\n" + insights.context_snippet,
    ]

    return {
        "context": "\n".join(summary_lines).strip(),
    }
