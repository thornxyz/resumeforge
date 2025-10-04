"""Helpers for parsing LLM responses into explanation + LaTeX code."""

from __future__ import annotations

import re
from typing import Optional, Tuple

CODE_BLOCK_PATTERN = re.compile(
    r"```(?:latex|tex)?\s*\n(.*?)\n```",
    re.DOTALL,
)


def split_explanation_and_code(response: str) -> Tuple[str, Optional[str]]:
    """Split plain text explanation and LaTeX code block from an LLM response."""
    if not response:
        return "", None

    match = CODE_BLOCK_PATTERN.search(response)
    if not match:
        return response.strip(), None

    latex = match.group(1).strip()
    explanation = (response[: match.start()] + response[match.end() :]).strip()
    return explanation, latex if latex else None


def ensure_complete_document(latex: Optional[str]) -> Optional[str]:
    if not latex:
        return None
    required_tokens = ["\\documentclass", "\\begin{document}", "\\end{document}"]
    if all(token in latex for token in required_tokens):
        return latex
    return None
