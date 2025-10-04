"""LaTeX compilation tooling."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from uuid import uuid4

import requests
from requests import RequestException

from ..config import AgentConfig


@dataclass
class CompilationOutcome:
    status: str
    log: str
    pdf_path: Optional[Path]
    errors: list[str]

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "log": self.log,
            "pdf_path": str(self.pdf_path) if self.pdf_path else None,
            "errors": self.errors,
        }


def compile_latex(document: str, config: AgentConfig) -> CompilationOutcome:
    """Compile LaTeX by delegating to the external latex-api service."""
    if not document.strip():
        return CompilationOutcome(
            status="error",
            log="Empty document provided",
            pdf_path=None,
            errors=["Empty document"],
        )

    document_bytes = document.encode("utf-8")
    url = config.latex_api_url.rstrip("/") + "/compile"

    try:
        response = requests.post(
            url,
            files={
                "file": ("document.tex", document_bytes, "application/x-tex"),
            },
            timeout=config.latex_api_timeout,
        )
    except RequestException as exc:
        return CompilationOutcome(
            status="error",
            log=str(exc),
            pdf_path=None,
            errors=["Failed to reach latex-api service"],
        )

    content_type = response.headers.get("content-type", "")
    if response.status_code == 200 and "application/pdf" in content_type:
        Path(config.temp_dir).mkdir(parents=True, exist_ok=True)
        pdf_path = Path(config.temp_dir) / f"latex_api_{uuid4().hex}.pdf"
        pdf_path.write_bytes(response.content)
        return CompilationOutcome(
            status="success",
            log="Compiled successfully via latex-api service.",
            pdf_path=pdf_path,
            errors=[],
        )

    try:
        payload = response.json()
    except ValueError:
        payload = {}

    errors = []
    if isinstance(payload, dict):
        error_summary = payload.get("error") or payload.get("message")
        if error_summary:
            errors.append(str(error_summary))
        log_tail = payload.get("logTail") or payload.get("log") or response.text
    else:
        log_tail = response.text

    if not errors:
        errors = [f"latex-api responded with status {response.status_code}".strip()]

    return CompilationOutcome(
        status="error",
        log=log_tail,
        pdf_path=None,
        errors=errors,
    )
