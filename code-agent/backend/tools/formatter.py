"""Simple LaTeX formatter for edit mode output."""

from __future__ import annotations

import re


def format_latex(content: str) -> str:
    if not content.strip():
        return content

    text = content.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.splitlines())
    text = re.sub(r"\n{3,}", "\n\n", text)

    def indent_env(match: re.Match[str]) -> str:
        env = match.group(1)
        body = match.group(2)
        indented = "\n".join(
            ("  " + line) if line.strip() else line for line in body.splitlines()
        )
        return f"\\begin{{{env}}}\n{indented}\n\\end{{{env}}}"

    text = re.sub(
        r"\\begin{(itemize|enumerate)}(.*?)\\end{\1}",
        indent_env,
        text,
        flags=re.DOTALL,
    )

    text = re.sub(r"([^\n])\n(\\section)", r"\1\n\n\\section", text)
    return text
