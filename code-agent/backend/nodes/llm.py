"""LLM nodes backed by Gemini via LangChain."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Iterable, List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ..config import AgentConfig
from ..state import AgentState
from ..utils.llm_output import split_explanation_and_code, ensure_complete_document


logger = logging.getLogger("resume_agent.llm")

ASK_SYSTEM_PROMPT = (
    "You are a helpful LaTeX assistant in 'Ask Mode'. Your role is to answer "
    "questions, explain concepts, and provide guidance conversationally. You "
    "must not generate a full, modified LaTeX document. You can include "
    "small, illustrative ```latex code snippets if necessary, but your "
    "primary output should be explanatory text."
)

EDIT_SYSTEM_PROMPT = (
    "You are a specialized LaTeX code generation assistant in 'Edit Mode'. "
    "Your task is to produce precise LaTeX code modifications. You must "
    "follow these rules strictly:\n"
    "1. Start your response with a single, concise sentence describing the "
    "change (e.g., 'Added a new Education section.').\n"
    "2. After the description, provide only the complete, updated LaTeX "
    "document inside a ```latex code block.\n"
    "3. Do NOT include any other explanations, questions, or alternative "
    "suggestions. Your response must contain only the one-line description "
    "and the code block."
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
        message_sequence.append(SystemMessage(content=f"Document context:\n{context}"))
    if document:
        message_sequence.append(
            SystemMessage(content=f"Current document:\n```latex\n{document}\n```")
        )

    message_sequence.extend(_build_history(state.get("messages", [])))
    message_sequence.append(HumanMessage(content=user_request))

    logger.info(
        "Invoking ASK LLM | context_len=%d doc_len=%d history=%d",
        len(context),
        len(document),
        len(state.get("messages", [])),
    )

    result = llm.invoke(message_sequence)
    text = getattr(result, "content", None) or getattr(result, "text", "")
    explanation, _ = split_explanation_and_code(text)

    logger.info(
        "ASK LLM completed | explanation_len=%d",
        len(explanation or text),
    )

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
        "Follow the rules for 'Edit Mode' precisely. Your entire response "
        "should consist of a single descriptive sentence followed by the full "
        "updated LaTeX document in a code block."
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

    logger.info(
        "Invoking EDIT LLM | doc_len=%d diagnostics=%s history=%d",
        len(document),
        compilation_status,
        len(state.get("messages", [])),
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
        logger.warning(
            "EDIT LLM returned incomplete document | using fallback len=%d",
            len(fallback),
        )
    else:
        logger.info(
            "EDIT LLM completed | explanation_len=%d latex_len=%d",
            len(explanation or text),
            len(latex_document),
        )

    return {
        "agent_response": explanation or text,
        "generated_code": latex_document,
        "raw_llm_output": text,
        "iteration_count": state.get("iteration_count", 0) + 1,
    }
