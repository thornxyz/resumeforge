"""Central configuration for the LangGraph-based LaTeX agent."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import List


@dataclass(frozen=True)
class AgentConfig:
    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash-exp"
    temperature: float = 0.2
    max_iterations: int = 3
    latex_compiler: str = "pdflatex"
    temp_dir: str = "/tmp/latex_compile"
    allowed_file_extensions: List[str] = (".tex", ".bib", ".cls", ".sty")
    latex_api_url: str = "http://localhost:8000"
    latex_api_timeout: float = 30.0


@lru_cache(maxsize=1)
def load_config() -> AgentConfig:
    """Load configuration from environment variables."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is required")

    model = os.getenv(
        "GEMINI_MODEL",
        AgentConfig.__dataclass_fields__["gemini_model"].default,
    )
    try:
        temperature = float(os.getenv("GEMINI_TEMPERATURE", AgentConfig.temperature))
    except ValueError as exc:
        raise RuntimeError("GEMINI_TEMPERATURE must be numeric") from exc

    max_iter_raw = os.getenv("AGENT_MAX_ITERATIONS")
    max_iterations = AgentConfig.max_iterations
    if max_iter_raw:
        try:
            max_iterations = int(max_iter_raw)
        except ValueError as exc:
            raise RuntimeError("AGENT_MAX_ITERATIONS must be an integer") from exc

    compiler = os.getenv("LATEX_COMPILER", AgentConfig.latex_compiler)
    temp_dir = os.getenv("LATEX_TEMP_DIR", AgentConfig.temp_dir)
    ext_raw = os.getenv("LATEX_ALLOWED_EXTENSIONS")
    allowed_extensions = (
        tuple(ext.strip() for ext in ext_raw.split(",") if ext.strip())
        if ext_raw
        else AgentConfig.allowed_file_extensions
    )

    latex_api_url = os.getenv("LATEX_API_URL", AgentConfig.latex_api_url)
    try:
        latex_api_timeout = float(
            os.getenv("LATEX_API_TIMEOUT", AgentConfig.latex_api_timeout)
        )
    except ValueError as exc:
        raise RuntimeError("LATEX_API_TIMEOUT must be numeric") from exc

    return AgentConfig(
        gemini_api_key=api_key,
        gemini_model=model,
        temperature=temperature,
        max_iterations=max_iterations,
        latex_compiler=compiler,
        temp_dir=temp_dir,
        allowed_file_extensions=list(allowed_extensions),
        latex_api_url=latex_api_url,
        latex_api_timeout=latex_api_timeout,
    )
