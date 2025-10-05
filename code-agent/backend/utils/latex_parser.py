"""Utility helpers for lightweight LaTeX parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple


SECTION_PATTERN = re.compile(
    r"^\s*\\(?:section|resumeSection)\*?{([^}]+)}", re.MULTILINE
)
PACKAGE_PATTERN = re.compile(r"\\usepackage(?:\[[^\]]*\])?{([^}]+)}")


@dataclass
class DocumentInsights:
    """Summarised view of a LaTeX document."""

    packages: List[str]
    sections: List[str]
    current_section: Optional[str]
    context_snippet: str


def _clean_packages(raw_packages: Iterable[str]) -> List[str]:
    packages: List[str] = []
    for item in raw_packages:
        packages.extend([pkg.strip() for pkg in item.split(",") if pkg.strip()])
    return packages


def find_current_section(
    section_entries: List[Tuple[int, str]], cursor_line: int | None
) -> Optional[str]:
    if cursor_line is None:
        return section_entries[0][1] if section_entries else None
    active = None
    for line_no, name in section_entries:
        if line_no <= cursor_line:
            active = name
        else:
            break
    return active


def extract_context(
    document: str,
    cursor_position: Optional[dict],
    radius: int = 20,
) -> str:
    lines = document.splitlines()
    if not lines:
        return ""
    if cursor_position and "line" in cursor_position:
        line_index = max(0, min(len(lines) - 1, cursor_position["line"]))
    else:
        line_index = 0
    start = max(0, line_index - radius)
    end = min(len(lines), line_index + radius + 1)
    excerpt = lines[start:end]
    return "\n".join(excerpt)


def analyse_document(
    document: str, cursor_position: Optional[dict]
) -> DocumentInsights:
    packages = _clean_packages(PACKAGE_PATTERN.findall(document))
    section_entries: List[tuple[int, str]] = []
    for match in SECTION_PATTERN.finditer(document):
        start_idx = match.start()
        line_no = document.count("\n", 0, start_idx)
        section_entries.append((line_no, match.group(1)))

    cursor_line = cursor_position.get("line") if cursor_position else None
    current_section = find_current_section(section_entries, cursor_line)
    sections = [name for (_, name) in section_entries]
    snippet = extract_context(document, cursor_position)
    return DocumentInsights(
        packages=packages,
        sections=sections,
        current_section=current_section,
        context_snippet=snippet,
    )
