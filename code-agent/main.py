import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.agent import LangGraphResumeAgent
from backend.config import AgentConfig, load_config
from backend.tools.compiler import compile_latex
from backend.tools.formatter import format_latex


log_level = os.getenv("AGENT_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=log_level,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("resume_agent.main")

# Load environment variables
load_dotenv()

app = FastAPI(title="ResumeForge AI Agent", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://frontend:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")


class Message(BaseModel):
    id: str
    content: str
    role: str
    timestamp: str


class ChatRequest(BaseModel):
    message: str
    conversationHistory: List[Message]
    latexContent: Optional[str] = None
    mode: str = "ask"
    cursorPosition: Optional[Dict[str, int]] = None
    filesToModify: Optional[List[str]] = None
    userProfile: Optional[Dict[str, Any]] = None
    threadId: Optional[str] = None


class ChatResponse(BaseModel):
    mode: str
    response: Optional[str] = None
    edits: Optional[List[Dict[str, Any]]] = None
    compilation_result: Optional[Dict[str, Any]] = None
    preview_url: Optional[str] = None
    success: bool = True
    explanation: Optional[str] = None
    modifiedLatex: Optional[str] = None
    error: Optional[str] = None
    toolsUsed: Optional[List[str]] = None
    threadId: Optional[str] = None


# Initialize the LangGraph ResumeForge Agent
AGENT_CONFIG = load_config()
logger.info(
    "Agent configuration loaded | model=%s latex_api_url=%s",
    AGENT_CONFIG.gemini_model,
    AGENT_CONFIG.latex_api_url,
)
resume_agent = LangGraphResumeAgent(AGENT_CONFIG)


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Validate request
        if not request.message or not isinstance(request.message, str):
            raise HTTPException(
                status_code=400, detail="Message is required and must be a string"
            )

        logger.info(
            "Received chat request | mode=%s thread=%s message_len=%d",
            request.mode,
            request.threadId,
            len(request.message),
        )

        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.conversationHistory
        ]

        state = await resume_agent.process(
            user_request=request.message,
            messages=conversation_history,
            current_document=request.latexContent or "",
            mode=request.mode,
            cursor_position=request.cursorPosition,
            files_to_modify=request.filesToModify or [],
            thread_id=request.threadId,
        )

        logger.info(
            "Agent process complete | thread=%s mode=%s tools=%s compilation_status=%s",
            state.get("thread_id"),
            state.get("mode"),
            ",".join(state.get("tools_used") or []),
            (state.get("compilation_result") or {}).get("status"),
        )

        compilation = state.get("compilation_result")
        pdf_path = None
        if compilation and isinstance(compilation, dict):
            pdf_path = compilation.get("pdf_path")

        success = (compilation or {}).get("status") != "error" if compilation else True
        tools_used = state.get("tools_used") or []
        modified_latex = state.get("generated_code") if success else None

        return ChatResponse(
            mode=state.get("mode", request.mode),
            response=state.get("agent_response"),
            edits=state.get("file_diffs"),
            compilation_result=compilation,
            preview_url=pdf_path,
            success=success,
            explanation=state.get("agent_response"),
            modifiedLatex=modified_latex,
            toolsUsed=tools_used,
            threadId=state.get("thread_id"),
        )

    except HTTPException:
        logger.exception("HTTP error while processing chat request")
        raise
    except Exception as e:
        logger.exception("Unexpected error during chat request handling")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "ResumeForge AI Agent is running"}


@app.post("/reset-session")
async def reset_session():
    """Reset the conversation and session state"""
    try:
        # The LangGraph agent is stateless between runs, so no action needed.
        return {"success": True, "message": "Session reset successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to reset session: {str(e)}"
        )


@app.post("/compile-latex")
async def compile_latex_endpoint(request: dict):
    """Direct endpoint for LaTeX compilation using the shared tooling."""
    latex_content = request.get("latexContent")
    if not latex_content:
        raise HTTPException(status_code=400, detail="latexContent is required")

    outcome = compile_latex(latex_content, AGENT_CONFIG)
    success = outcome.status == "success"
    return {
        "success": success,
        "log": outcome.log,
        "errors": outcome.errors,
        "pdfPath": str(outcome.pdf_path) if outcome.pdf_path else None,
    }


@app.post("/format-latex")
async def format_latex_endpoint(request: dict):
    """Apply deterministic formatting to provided LaTeX content."""
    latex_content = request.get("latexContent")
    if latex_content is None:
        raise HTTPException(status_code=400, detail="latexContent is required")

    return {
        "success": True,
        "formatted": format_latex(latex_content),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
