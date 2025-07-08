import os
import json
import re
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
from agent import ResumeForgeAgent, VibeManager

# Load environment variables
load_dotenv()

app = FastAPI(title="ResumeForge AI Agent", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

genai.configure(api_key=GEMINI_API_KEY)


class Message(BaseModel):
    id: str
    content: str
    role: str
    timestamp: str


class ChatRequest(BaseModel):
    message: str
    conversationHistory: List[Message]
    latexContent: Optional[str] = None
    mode: str = "agent"
    userProfile: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    success: bool
    explanation: Optional[str] = None
    modifiedLatex: Optional[str] = None
    response: Optional[str] = None
    error: Optional[str] = None
    toolsUsed: Optional[List[str]] = None
    vibeMessage: Optional[str] = None
    sessionStats: Optional[Dict[str, Any]] = None


# Initialize the ResumeForge Agent and Vibe Manager
resume_agent = ResumeForgeAgent(GEMINI_API_KEY)
vibe_manager = VibeManager()


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Validate request
        if not request.message or not isinstance(request.message, str):
            raise HTTPException(
                status_code=400, detail="Message is required and must be a string"
            )

        # Set user profile if provided
        if request.userProfile:
            resume_agent.set_user_profile(request.userProfile)

        # Set current LaTeX content if provided
        if request.latexContent:
            resume_agent.set_current_latex(request.latexContent)

        # Convert conversation history to the format expected by the agent
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.conversationHistory
        ]

        # Process the message using the LangChain agent
        result = await resume_agent.process_message(
            request.message, conversation_history
        )

        # Determine vibe message based on tools used and success
        vibe_message = None
        if result.get("success"):
            tools_used = result.get("toolsUsed", [])
            if "latex_compiler" in tools_used:
                vibe_message = vibe_manager.get_encouragement("successful_compile")
                vibe_manager.update_stats("compilation", True)
            elif "latex_enhancer" in tools_used:
                vibe_message = vibe_manager.get_encouragement("enhancement")
                vibe_manager.update_stats("enhancement")
            elif "latex_template_generator" in tools_used:
                vibe_message = vibe_manager.get_encouragement("first_template")
            elif result.get("modifiedLatex"):
                vibe_message = vibe_manager.get_encouragement("formatting")
                vibe_manager.update_stats("section_modification")

        return ChatResponse(
            success=result.get("success", True),
            response=result.get("response"),
            explanation=result.get("explanation"),
            modifiedLatex=result.get("modifiedLatex"),
            error=result.get("error"),
            toolsUsed=result.get("toolsUsed"),
            vibeMessage=vibe_message,
            sessionStats=vibe_manager.session_stats,
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
        resume_agent.reset_conversation()
        global vibe_manager
        vibe_manager = VibeManager()
        return {"success": True, "message": "Session reset successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to reset session: {str(e)}"
        )


@app.get("/session-stats")
async def get_session_stats():
    """Get current session statistics"""
    return {
        "stats": vibe_manager.session_stats,
        "summary": vibe_manager.get_session_summary(),
    }


@app.post("/compile-latex")
async def compile_latex_endpoint(request: dict):
    """Direct endpoint for LaTeX compilation"""
    try:
        latex_content = request.get("latexContent")
        if not latex_content:
            raise HTTPException(status_code=400, detail="latexContent is required")

        from tools import LatexCompilerTool

        compiler = LatexCompilerTool()
        result = compiler._run(latex_content)

        success = "compiled successfully" in result.lower()
        if success:
            vibe_manager.update_stats("compilation", True)

        return {
            "success": success,
            "message": result,
            "vibeMessage": vibe_manager.get_encouragement(
                "successful_compile" if success else "error_fix"
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compilation failed: {str(e)}")


@app.post("/validate-latex")
async def validate_latex_endpoint(request: dict):
    """Direct endpoint for LaTeX validation"""
    try:
        latex_content = request.get("latexContent")
        if not latex_content:
            raise HTTPException(status_code=400, detail="latexContent is required")

        from tools import LatexValidatorTool

        validator = LatexValidatorTool()
        result = validator._run(latex_content)

        return {
            "success": True,
            "validation": result,
            "isValid": "looks good" in result.lower(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@app.post("/generate-template")
async def generate_template_endpoint(request: dict):
    """Direct endpoint for template generation"""
    try:
        style = request.get("style", "modern")
        name = request.get("name", "[Your Name]")
        email = request.get("email", "[your.email@example.com]")

        from tools import LatexTemplateGeneratorTool

        generator = LatexTemplateGeneratorTool()
        result = generator._run(style, name, email)

        return {
            "success": True,
            "template": result,
            "style": style,
            "vibeMessage": vibe_manager.get_encouragement("first_template"),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Template generation failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
