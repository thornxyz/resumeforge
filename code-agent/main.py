import os
import json
import re
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

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


class ChatResponse(BaseModel):
    success: bool
    explanation: Optional[str] = None
    modifiedLatex: Optional[str] = None
    response: Optional[str] = None
    error: Optional[str] = None


class AIAgent:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    def build_conversation_context(self, conversation_history: List[Message]) -> str:
        if not conversation_history:
            return ""

        return "\n".join(
            [
                f"{'User' if msg.role == 'user' else 'Assistant'}: {msg.content}"
                for msg in conversation_history[-10:]  # Last 10 messages
            ]
        )

    def create_agent_prompt(self, message: str, latex_content: str) -> str:
        return f"""You are a LaTeX code assistant that helps users modify their resume code based on natural language instructions.

CURRENT LATEX CODE:
```latex
{latex_content}
```

USER INSTRUCTION: {message}

CRITICAL REQUIREMENTS:
1. You MUST actually modify the LaTeX code based on the user's request
2. You MUST respond with ONLY a valid JSON object in this EXACT format
3. Do NOT include any explanatory text before or after the JSON
4. Do NOT just explain what you would do - actually DO the modifications
5. ALWAYS include the complete modified LaTeX in the "modifiedLatex" field

REQUIRED JSON FORMAT:
{{
  "explanation": "Brief explanation of what you changed",
  "modifiedLatex": "The complete modified LaTeX code with actual changes applied",
  "hasChanges": true
}}

IMPORTANT: When you make ANY change (even small ones like changing a name), you MUST:
- Set "hasChanges": true
- Include the COMPLETE modified LaTeX code in "modifiedLatex"
- Do NOT set "hasChanges": false unless you truly cannot fulfill the request

EXAMPLES:
- If user says "make the font bigger", actually change \\fontsize or add \\large commands
- If user says "add a phone number", actually insert the phone number in the contact section
- If user says "change the color to blue", actually modify color commands like \\textcolor{{blue}}
- If user says "remove education section", actually delete those lines from the code

STRICT GUIDELINES:
- ALWAYS make the actual requested changes to the LaTeX code
- Set hasChanges to true when you make modifications
- Set hasChanges to false ONLY if the request cannot be fulfilled or no changes are truly needed
- Return the COMPLETE modified LaTeX document, not just snippets
- Ensure all LaTeX syntax remains valid after modifications
- Keep explanations brief but specific about what was actually changed

YOU MUST RESPOND WITH ONLY THE JSON OBJECT - NO OTHER TEXT:"""

    def create_chat_prompt(self, message: str, conversation_context: str) -> str:
        prompt = "You are an AI assistant specialized in helping with LaTeX resume writing, formatting, and career advice. You should be helpful, professional, and provide practical guidance.\n\n"

        if conversation_context:
            prompt += f"Previous conversation:\n{conversation_context}\n\n"

        prompt += (
            f"Current user message: {message}\n\nPlease provide a helpful response:"
        )
        return prompt

    def clean_and_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            # Clean the response text
            cleaned_text = text.strip()

            # Remove any markdown code block formatting
            cleaned_text = re.sub(r"```json\s*", "", cleaned_text)
            cleaned_text = re.sub(r"```\s*$", "", cleaned_text)

            # Try to extract the first valid JSON object
            json_start = cleaned_text.find("{")
            json_end = cleaned_text.rfind("}")

            if json_start != -1 and json_end != -1 and json_end > json_start:
                json_string = cleaned_text[json_start : json_end + 1]

                try:
                    # Try parsing directly first
                    return json.loads(json_string)
                except json.JSONDecodeError:
                    # Try to fix common issues: unescaped backslashes
                    safe_json = re.sub(r'\\(?![\\"\'/bfnrt])', r"\\\\", json_string)
                    return json.loads(safe_json)

            # If no braces found, try parsing the whole cleaned text
            return json.loads(cleaned_text)

        except (json.JSONDecodeError, Exception) as e:
            print(f"JSON parsing error: {e}")
            return None

    def detect_actual_changes(self, original_latex: str, modified_latex: str) -> bool:
        if not modified_latex:
            return False
        return modified_latex.strip() != original_latex.strip()

    async def process_agent_request(
        self, message: str, latex_content: str, conversation_history: List[Message]
    ) -> ChatResponse:
        try:
            prompt = self.create_agent_prompt(message, latex_content)

            # Generate response
            response = self.model.generate_content(prompt)
            text = response.text

            # Parse JSON response
            parsed_response = self.clean_and_parse_json(text)

            if parsed_response and "explanation" in parsed_response:
                # Check if AI actually provided modified code
                has_actual_changes = self.detect_actual_changes(
                    latex_content, parsed_response.get("modifiedLatex", "")
                )

                print(
                    f"Change detection: AI says {parsed_response.get('hasChanges')}, "
                    f"Actually has changes: {has_actual_changes}"
                )

                # Override AI's hasChanges if we detect actual changes
                final_has_changes = has_actual_changes or parsed_response.get(
                    "hasChanges", False
                )

                return ChatResponse(
                    success=True,
                    explanation=parsed_response["explanation"],
                    modifiedLatex=(
                        parsed_response["modifiedLatex"] if final_has_changes else None
                    ),
                    response=parsed_response["explanation"],
                )
            else:
                # Fallback if JSON parsing fails
                return ChatResponse(
                    success=True,
                    response=text,
                    explanation="I couldn't process that request properly. Please try rephrasing.",
                )

        except Exception as e:
            print(f"Agent processing error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to process agent request: {str(e)}"
            )

    async def process_chat_request(
        self, message: str, conversation_history: List[Message]
    ) -> ChatResponse:
        try:
            conversation_context = self.build_conversation_context(conversation_history)
            prompt = self.create_chat_prompt(message, conversation_context)

            # Generate response
            response = self.model.generate_content(prompt)
            text = response.text

            return ChatResponse(success=True, response=text)

        except Exception as e:
            print(f"Chat processing error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to process chat request: {str(e)}"
            )


# Initialize the AI agent
ai_agent = AIAgent()


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Validate request
        if not request.message or not isinstance(request.message, str):
            raise HTTPException(
                status_code=400, detail="Message is required and must be a string"
            )

        # Process based on mode
        if request.mode == "agent" and request.latexContent:
            return await ai_agent.process_agent_request(
                request.message, request.latexContent, request.conversationHistory
            )
        else:
            return await ai_agent.process_chat_request(
                request.message, request.conversationHistory
            )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "ResumeForge AI Agent is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
