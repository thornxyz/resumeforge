"""Parser node for extracting LaTeX document insights."""

from __future__ import annotations

import logging

from ..state import AgentState
from ..utils.latex_parser import analyse_document


logger = logging.getLogger("resume_agent.parser")


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

    logger.info(
        "Parsed document context | packages=%d sections=%d current_section=%s",
        len(insights.packages),
        len(insights.sections),
        insights.current_section,
    )

    return {
        "context": "\n".join(summary_lines).strip(),
    }
