import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.agent import LangGraphResumeAgent
from backend.config import AgentConfig
from backend.tools.compiler import compile_latex
from backend.tools.formatter import format_latex

# Load environment variables
load_dotenv()

app = FastAPI(title="ResumeForge AI Agent", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
AGENT_CONFIG = AgentConfig(gemini_api_key=GEMINI_API_KEY)
resume_agent = LangGraphResumeAgent(AGENT_CONFIG)


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Validate request
        if not request.message or not isinstance(request.message, str):
            raise HTTPException(
                status_code=400, detail="Message is required and must be a string"
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

        compilation = state.get("compilation_result")
        pdf_path = None
        if compilation and isinstance(compilation, dict):
            pdf_path = compilation.get("pdf_path")

        success = (compilation or {}).get("status") != "error" if compilation else True
        tools_used = state.get("tools_used") or []

        return ChatResponse(
            mode=state.get("mode", request.mode),
            response=state.get("agent_response"),
            edits=state.get("file_diffs"),
            compilation_result=compilation,
            preview_url=pdf_path,
            success=success,
            explanation=state.get("agent_response"),
            modifiedLatex=state.get("generated_code"),
            toolsUsed=tools_used,
            threadId=state.get("thread_id"),
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
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
