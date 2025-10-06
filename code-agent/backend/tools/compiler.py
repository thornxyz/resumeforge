"""LaTeX compilation tooling."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from uuid import uuid4

import requests
from requests import RequestException

from ..config import AgentConfig


logger = logging.getLogger("resume_agent.tools.compiler")


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
        logger.warning("compile_latex called with empty document")
        return CompilationOutcome(
            status="error",
            log="Empty document provided",
            pdf_path=None,
            errors=["Empty document"],
        )

    document_bytes = document.encode("utf-8")
    url = config.latex_api_url.rstrip("/") + "/compile"

    try:
        logger.info("Posting document to latex-api | url=%s", url)
        response = requests.post(
            url,
            files={
                "file": ("document.tex", document_bytes, "application/x-tex"),
            },
            timeout=config.latex_api_timeout,
        )
    except RequestException as exc:
        logger.exception("latex-api request failed | url=%s", url)
        return CompilationOutcome(
            status="error",
            log=str(exc),
            pdf_path=None,
            errors=["Failed to reach latex-api service"],
        )

    content_type = response.headers.get("content-type", "")
    if response.status_code == 200 and "application/pdf" in content_type:
        logger.info("latex-api compilation succeeded | status=%s", response.status_code)
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

    logger.error(
        "latex-api compilation failed | status=%s errors=%s",
        response.status_code,
        errors,
    )

    return CompilationOutcome(
        status="error",
        log=log_tail,
        pdf_path=None,
        errors=errors,
    )
