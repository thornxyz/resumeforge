"""
Simplified ResumeForge AI Agent
"""

from typing import List, Dict, Any, Optional
import google.generativeai as genai
from tools import (
    LatexCompilerTool,
    LatexValidatorTool,
    LatexSectionExtractorTool,
    LatexTemplateGeneratorTool,
    LatexEnhancerTool,
    LatexFormatterTool,
)
from prompts import get_system_prompt, get_modification_instruction
from intent_detector import IntentDetector
from latex_processor import LatexExtractor, LatexProcessor


class ResumeForgeAgent:
    """Main AI agent for resume building"""

    def __init__(self, gemini_api_key: str):
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        genai.configure(api_key=gemini_api_key)
        
        # Initialize tools
        self.tools = {
            "compiler": LatexCompilerTool(),
            "validator": LatexValidatorTool(),
            "extractor": LatexSectionExtractorTool(),
            "template_generator": LatexTemplateGeneratorTool(),
            "enhancer": LatexEnhancerTool(),
            "formatter": LatexFormatterTool(),
        }
        
        # Initialize processors
        self.intent_detector = IntentDetector()
        self.latex_processor = LatexProcessor(
            self.tools["validator"],
            self.tools["compiler"],
            max_repair_attempts=2
        )
        
        # State
        self.current_latex = None
        self.conversation_history = []

    def _execute_tools(
        self, tools_needed: List[str], message: str, latex_content: str = None
    ) -> Dict[str, str]:
        """Execute the specified tools and return results"""
        results: Dict[str, str] = {}
        
        for tool_name in tools_needed:
            if tool_name not in self.tools:
                continue
                
            tool = self.tools[tool_name]
            
            try:
                if tool_name == "template_generator":
                    # Detect style from message
                    style = "modern"
                    if "classic" in message.lower():
                        style = "classic"
                    elif "creative" in message.lower():
                        style = "creative"
                    elif "academic" in message.lower():
                        style = "academic"
                    results[tool_name] = tool._run(style)
                    
                elif tool_name == "extractor":
                    # Detect section name from message
                    section_name = ""
                    for s in ["experience", "education", "skills", "projects"]:
                        if s in message.lower():
                            section_name = s
                            break
                    results[tool_name] = tool._run(
                        latex_content or self.current_latex or "", section_name
                    )
                    
                else:
                    lt = latex_content or self.current_latex or ""
                    results[tool_name] = (
                        tool._run(lt)
                        if lt
                        else "No LaTeX content available for analysis."
                    )
                    
            except Exception as e:
                results[tool_name] = f"Tool error: {e}"
                
        return results

    def _build_prompt(
        self, message: str, tool_results: Dict[str, str], intent_action: str = "chat"
    ) -> str:
        """Build the complete prompt for the AI model"""
        prompt_parts = [get_system_prompt(), "\n\n"]
        
        # Add current LaTeX if available
        if self.current_latex:
            prompt_parts.append(
                f"CURRENT LATEX CONTENT:\n```latex\n{self.current_latex}\n```\n\n"
            )
        
        # Add tool results
        if tool_results:
            prompt_parts.append("TOOL ANALYSIS RESULTS:\n")
            for name, result in tool_results.items():
                prompt_parts.append(f"\n{name.upper()} RESULT:\n{result}\n")
            prompt_parts.append("\n")
        
        # Add recent conversation history
        if self.conversation_history:
            prompt_parts.append("RECENT CONVERSATION:\n")
            for msg in self.conversation_history[-6:]:
                role = "User" if msg["role"] == "user" else "Assistant"
                prompt_parts.append(f"{role}: {msg['content']}\n")
            prompt_parts.append("\n")
        
        # Add modification instruction if needed
        if intent_action in ["modify", "enhance", "format"] and self.current_latex:
            prompt_parts.append(get_modification_instruction())
        
        # Add user message
        prompt_parts.append(
            f"USER MESSAGE: {message}\n\n"
            "Please respond with helpful guidance. Include LaTeX in a ```latex block if changed."
        )
        
        return "".join(prompt_parts)

    async def process_message(
        self, message: str, conversation_history: List[Dict]
    ) -> Dict[str, Any]:
        """Process a user message and return response"""
        try:
            self.conversation_history = conversation_history
            
            # Extract LaTeX from message if present
            latex_content = LatexExtractor.from_message(message)
            if latex_content:
                self.current_latex = latex_content
            
            # Detect intent
            intent = self.intent_detector.detect(message)
            
            # Execute tools if needed
            tool_results: Dict[str, str] = {}
            tools_used: List[str] = []
            if intent["tools_needed"]:
                tool_results = self._execute_tools(
                    intent["tools_needed"], message, latex_content
                )
                tools_used = [
                    self.tools[key].name 
                    for key in intent["tools_needed"] 
                    if key in self.tools
                ]
            
            # Build prompt and get AI response
            prompt = self._build_prompt(message, tool_results, intent["action"])
            
            try:
                response = self.model.generate_content(prompt)
                response_text = getattr(response, "text", str(response))
            except Exception as e:
                return {"success": False, "error": f"Model generation failed: {e}"}
            
            # Extract and validate LaTeX from response
            modified_latex = LatexExtractor.from_response(response_text)
            reliability = {}
            
            if modified_latex:
                reliability = self.latex_processor.validate_and_compile(modified_latex)
                repaired = reliability.get("latex")
                
                # Update response with repair info
                if repaired and repaired != modified_latex:
                    repairs = reliability.get("repairs", [])
                    if repairs:
                        response_text += "\n\n(Repairs: " + "; ".join(repairs) + ")"
                    modified_latex = repaired
                
                # Add compilation feedback
                if reliability.get("compile_result"):
                    if reliability.get("compiled"):
                        response_text += "\n\nCompiled successfully."
                    else:
                        response_text += (
                            "\n\nCompile feedback: " + 
                            reliability.get("compile_result", "")
                        )
                    if "latex_compiler" not in tools_used:
                        tools_used.append("latex_compiler")
                
                if reliability.get("validation") and "latex_validator" not in tools_used:
                    tools_used.append("latex_validator")
                
                self.current_latex = modified_latex
            
            return {
                "success": True,
                "response": response_text,
                "modifiedLatex": modified_latex,
                "explanation": LatexExtractor.extract_explanation(response_text),
                "toolsUsed": tools_used,
                "intent": intent["action"],
                "reliability": reliability,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Agent processing failed: {e}",
                "response": f"Error: {e}",
            }

    def reset_conversation(self):
        """Reset conversation state"""
        self.conversation_history = []
        self.current_latex = None

    def get_current_latex(self) -> Optional[str]:
        """Get current LaTeX content"""
        return self.current_latex

    def set_current_latex(self, latex_content: str):
        """Set current LaTeX content"""
        self.current_latex = latex_content
