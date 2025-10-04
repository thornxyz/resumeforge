"""LLM nodes backed by Gemini via LangChain."""

from __future__ import annotations

from functools import lru_cache
from typing import Iterable, List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ..config import AgentConfig
from ..state import AgentState
from ..utils.llm_output import split_explanation_and_code, ensure_complete_document

ASK_SYSTEM_PROMPT = (
    "You are a LaTeX expert mentor. Explain concepts clearly, reference the "
    "provided document context when helpful, and include short code examples "
    "inside ```latex blocks when relevant."
)

EDIT_SYSTEM_PROMPT = (
    "You are a LaTeX code editor. Produce updated LaTeX that fully replaces "
    "the existing document. Maintain required packages and structure."
)


@lru_cache(maxsize=4)
def _make_llm(api_key: str, model: str, temperature: float) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=temperature,
    )


def _build_history(messages: Iterable[dict]) -> List[HumanMessage | AIMessage]:
    history: List[HumanMessage | AIMessage] = []
    for item in messages:
        role = item.get("role", "user")
        content = item.get("content", "")
        if not content:
            continue
        if role == "assistant":
            history.append(AIMessage(content=content))
        else:
            history.append(HumanMessage(content=content))
    return history


def ask_with_gemini(state: AgentState, agent_config: AgentConfig) -> AgentState:
    llm = _make_llm(
        agent_config.gemini_api_key,
        agent_config.gemini_model,
        agent_config.temperature,
    )

    context = state.get("context", "")
    document = state.get("current_document", "")
    user_request = state.get("user_request", "")

    message_sequence: List = [SystemMessage(content=ASK_SYSTEM_PROMPT)]
    if context:
        message_sequence.append(
            SystemMessage(
                content=f"Document context:\n{context}\n---\nCurrent document snippet:\n```latex\n{document[:4000]}\n```"
            )
        )

    message_sequence.extend(_build_history(state.get("messages", [])))
    message_sequence.append(HumanMessage(content=user_request))

    result = llm.invoke(message_sequence)
    text = getattr(result, "content", None) or getattr(result, "text", "")
    explanation, _ = split_explanation_and_code(text)

    return {
        "agent_response": explanation or text,
        "generated_code": None,
        "raw_llm_output": text,
    }


def edit_with_gemini(state: AgentState, agent_config: AgentConfig) -> AgentState:
    llm = _make_llm(
        agent_config.gemini_api_key,
        agent_config.gemini_model,
        agent_config.temperature,
    )

    document = state.get("current_document", "")
    context = state.get("context", "")
    user_request = state.get("user_request", "")
    compilation = state.get("compilation_result") or {}
    compilation_status = compilation.get("status")
    compilation_errors = compilation.get("errors") or []
    compilation_log = compilation.get("log")

    system_message = SystemMessage(content=EDIT_SYSTEM_PROMPT)
    instructions = (
        "Always return the full LaTeX document between ```latex fences."
        "\nRespond with explanation first, then the code block."
    )

    message_sequence: List = [system_message]
    if context:
        message_sequence.append(SystemMessage(content=f"Context summary:\n{context}"))
    if compilation_status == "error":
        error_lines = (
            "\n".join(compilation_errors)
            if compilation_errors
            else "Compilation failed."
        )
        diagnostic = error_lines
        if compilation_log and isinstance(compilation_log, str):
            tail = "\n".join(compilation_log.splitlines()[-10:])
            diagnostic = f"{diagnostic}\n\nLog tail:\n{tail}"
        message_sequence.append(
            SystemMessage(
                content=(
                    "Previous compilation failed. Use these diagnostics to fix the LaTeX before returning.\n"
                    f"{diagnostic}"
                )
            )
        )
    message_sequence.extend(_build_history(state.get("messages", [])))
    message_sequence.append(
        HumanMessage(
            content=(
                f"Current document:\n```latex\n{document}\n```\n\n"
                f"Instructions: {user_request}\n\n{instructions}"
            )
        )
    )

    result = llm.invoke(message_sequence)
    text = getattr(result, "content", None) or getattr(result, "text", "")
    explanation, latex = split_explanation_and_code(text)
    latex_document = ensure_complete_document(latex)

    if latex_document is None:
        fallback = state.get("current_document") or ""
        if explanation:
            explanation += "\n\n(LLM response did not include a full LaTeX document; using existing document.)"
        else:
            explanation = "LLM response missing a complete LaTeX document; using existing content."
        latex_document = fallback

    return {
        "agent_response": explanation or text,
        "generated_code": latex_document,
        "raw_llm_output": text,
        "iteration_count": state.get("iteration_count", 0) + 1,
    }
