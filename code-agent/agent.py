"""
Comprehensive LangChain Agent for Resume Building
"""

import json
import re
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


class ResumeForgeAgent:
    """Comprehensive agent for resume building with vibe coding experience"""

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

        # Store current LaTeX content for context
        self.current_latex = None
        self.user_profile = {}
        self.conversation_history = []

    def _get_system_prompt(self) -> str:
        return """You are ResumeForge AI, a sophisticated LaTeX resume building assistant that provides a "vibe coding" experience. You help users create, modify, and perfect their resumes using LaTeX.

YOUR PERSONALITY:
- Enthusiastic and encouraging, like a skilled coding mentor
- Use emojis appropriately to make interactions feel alive
- Be conversational but professional
- Show genuine excitement when users make progress
- Provide specific, actionable feedback

YOUR CAPABILITIES:
You have access to powerful tools for:
1. 🔧 Compile LaTeX to PDF using Docker container
2. ✅ Validate LaTeX syntax and catch errors
3. 📄 Extract and analyze resume sections
4. 🎨 Generate different resume templates
5. ✨ Suggest improvements and enhancements
6. 🎯 Clean up and format LaTeX code

INTERACTION STYLE:
- Always acknowledge what the user is trying to achieve
- Provide step-by-step guidance when needed
- Use tools proactively to validate, enhance, and compile code
- Give specific examples and suggestions
- Celebrate successes and guide through errors
- Make the experience feel like pair programming

WORKFLOW APPROACH:
1. Understand the user's intent and current state
2. Use appropriate tools to analyze, modify, or create content
3. Always validate changes before presenting them
4. Compile when major changes are made
5. Provide enhancement suggestions
6. Keep the conversation flowing naturally

Remember: You're not just processing requests - you're providing a collaborative, engaging experience that makes resume building feel like an exciting coding session!"""

    def _extract_latex_from_message(self, message: str) -> Optional[str]:
        """Extract LaTeX code from user message"""
        # Look for LaTeX code blocks
        latex_pattern = r"```(?:latex|tex)?\s*\n(.*?)\n```"
        match = re.search(latex_pattern, message, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Look for LaTeX document structure
        if "\\documentclass" in message and "\\begin{document}" in message:
            return message.strip()

        return None

    def _determine_intent_and_tools(self, message: str) -> Dict[str, Any]:
        """Analyze user message to determine intent and required tools"""
        message_lower = message.lower()

        intent = {"action": "chat", "tools_needed": [], "confidence": 0.5}

        # Template generation
        if any(
            word in message_lower
            for word in ["template", "start", "create resume", "new resume"]
        ):
            intent.update(
                {
                    "action": "generate_template",
                    "tools_needed": ["template_generator"],
                    "confidence": 0.9,
                }
            )

        # Compilation requests
        elif any(
            word in message_lower
            for word in ["compile", "build", "pdf", "generate pdf"]
        ):
            intent.update(
                {
                    "action": "compile",
                    "tools_needed": ["validator", "compiler"],
                    "confidence": 0.9,
                }
            )

        # Validation requests
        elif any(
            word in message_lower for word in ["validate", "check", "errors", "syntax"]
        ):
            intent.update(
                {"action": "validate", "tools_needed": ["validator"], "confidence": 0.8}
            )

        # Enhancement requests
        elif any(
            word in message_lower
            for word in ["improve", "enhance", "better", "suggestions"]
        ):
            intent.update(
                {"action": "enhance", "tools_needed": ["enhancer"], "confidence": 0.8}
            )

        # Formatting requests
        elif any(word in message_lower for word in ["format", "clean", "organize"]):
            intent.update(
                {"action": "format", "tools_needed": ["formatter"], "confidence": 0.8}
            )

        # Section extraction
        elif any(word in message_lower for word in ["section", "extract", "show me"]):
            intent.update(
                {"action": "extract", "tools_needed": ["extractor"], "confidence": 0.7}
            )

        # Modification requests (use multiple tools)
        elif any(
            word in message_lower
            for word in ["change", "modify", "update", "add", "remove"]
        ):
            intent.update(
                {
                    "action": "modify",
                    "tools_needed": ["validator", "enhancer"],
                    "confidence": 0.7,
                }
            )

        return intent

    def _execute_tools(
        self, tools_needed: List[str], message: str, latex_content: str = None
    ) -> Dict[str, str]:
        """Execute the specified tools and return results"""
        results = {}

        for tool_name in tools_needed:
            if tool_name not in self.tools:
                continue

            tool = self.tools[tool_name]

            try:
                if tool_name == "template_generator":
                    # Extract style from message
                    style = "modern"
                    if "classic" in message.lower():
                        style = "classic"
                    elif "creative" in message.lower():
                        style = "creative"
                    elif "academic" in message.lower():
                        style = "academic"

                    result = tool._run(style)
                    results[tool_name] = result

                elif tool_name == "extractor":
                    # Extract section name from message
                    section_name = ""
                    for section in ["experience", "education", "skills", "projects"]:
                        if section in message.lower():
                            section_name = section
                            break

                    result = tool._run(
                        latex_content or self.current_latex or "", section_name
                    )
                    results[tool_name] = result

                else:
                    # Standard tool execution
                    latex_to_use = latex_content or self.current_latex or ""
                    if latex_to_use:
                        result = tool._run(latex_to_use)
                        results[tool_name] = result
                    else:
                        results[tool_name] = "No LaTeX content available for analysis."

            except Exception as e:
                results[tool_name] = f"Tool error: {str(e)}"

        return results

    def _create_comprehensive_prompt(
        self, message: str, tool_results: Dict[str, str]
    ) -> str:
        """Create a comprehensive prompt including tool results"""
        prompt = f"{self._get_system_prompt()}\n\n"

        if self.current_latex:
            prompt += f"CURRENT LATEX CONTENT:\n```latex\n{self.current_latex}\n```\n\n"

        if tool_results:
            prompt += "TOOL ANALYSIS RESULTS:\n"
            for tool_name, result in tool_results.items():
                prompt += f"\n{tool_name.upper()} RESULT:\n{result}\n"
            prompt += "\n"

        if self.conversation_history:
            prompt += "RECENT CONVERSATION:\n"
            for msg in self.conversation_history[-6:]:  # Last 3 exchanges
                role = "User" if msg["role"] == "user" else "Assistant"
                prompt += f"{role}: {msg['content']}\n"
            prompt += "\n"

        prompt += f"USER MESSAGE: {message}\n\n"
        prompt += """Please respond as ResumeForge AI with:
1. An enthusiastic, helpful response acknowledging the user's request
2. If you generated or modified LaTeX code, include it in a ```latex code block
3. Specific actionable advice based on the tool analysis
4. Encouragement and next steps

Keep the vibe coding experience alive with enthusiasm and practical guidance!"""

        return prompt

    async def process_message(
        self, message: str, conversation_history: List[Dict]
    ) -> Dict[str, Any]:
        """Process user message and return response with enhanced context"""
        try:
            # Update conversation history
            self.conversation_history = conversation_history

            # Update context with any LaTeX content
            latex_content = self._extract_latex_from_message(message)
            if latex_content:
                self.current_latex = latex_content

            # Determine intent and required tools
            intent = self._determine_intent_and_tools(message)

            # Execute tools if needed
            tool_results = {}
            if intent["tools_needed"]:
                tool_results = self._execute_tools(
                    intent["tools_needed"], message, latex_content
                )

            # Create comprehensive prompt
            prompt = self._create_comprehensive_prompt(message, tool_results)

            # Generate response using Gemini
            response = self.model.generate_content(prompt)
            response_text = response.text

            # Extract LaTeX code from response
            modified_latex = self._extract_latex_from_response(response_text)
            if modified_latex:
                self.current_latex = modified_latex

            return {
                "success": True,
                "response": response_text,
                "modifiedLatex": modified_latex,
                "explanation": self._extract_explanation(response_text),
                "toolsUsed": intent["tools_needed"],
                "intent": intent["action"],
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Agent processing failed: {str(e)}",
                "response": f"I encountered an error while processing your request: {str(e)}. Let me try a different approach! 🔧",
            }

    def _extract_latex_from_response(self, response: str) -> Optional[str]:
        """Extract LaTeX code from agent response"""
        # Look for LaTeX code blocks in response
        latex_pattern = r"```(?:latex|tex)?\s*\n(.*?)\n```"
        match = re.search(latex_pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def _extract_explanation(self, response: str) -> Optional[str]:
        """Extract explanation from response"""
        # Simple heuristic: first paragraph that doesn't contain code
        lines = response.split("\n")
        explanation_lines = []

        for line in lines:
            if "```" in line:
                break
            if line.strip():
                explanation_lines.append(line.strip())

        if explanation_lines:
            return " ".join(explanation_lines)
        return None

    def _extract_tools_used(self, intermediate_steps: List) -> List[str]:
        """Extract names of tools that were used"""
        tools_used = []
        for step in intermediate_steps:
            if hasattr(step[0], "tool"):
                tools_used.append(step[0].tool)
        return tools_used

    def reset_conversation(self):
        """Reset conversation memory"""
        self.memory.clear()
        self.current_latex = None
        self.user_profile = {}

    def set_user_profile(self, profile: Dict[str, Any]):
        """Set user profile information for personalized assistance"""
        self.user_profile = profile

    def get_current_latex(self) -> Optional[str]:
        """Get current LaTeX content"""
        return self.current_latex

    def set_current_latex(self, latex_content: str):
        """Set current LaTeX content"""
        self.current_latex = latex_content


class VibeManager:
    """Manages the 'vibe' of the coding experience with encouragement and feedback"""

    def __init__(self):
        self.session_stats = {
            "compilations": 0,
            "successful_compilations": 0,
            "enhancements_applied": 0,
            "sections_modified": 0,
        }

    def get_encouragement(self, context: str) -> str:
        """Get contextual encouragement based on user action"""
        encouragements = {
            "first_template": "🎉 Great start! You've got your first LaTeX template. Let's make it uniquely yours!",
            "successful_compile": "✨ Beautiful! Your LaTeX compiled perfectly. The PDF looks professional!",
            "error_fix": "🔧 Nice debugging! You're getting the hang of LaTeX. Every error makes you stronger!",
            "enhancement": "🚀 Excellent improvement! Your resume is looking more polished with each change.",
            "new_section": "📝 Smart addition! That new section really strengthens your resume.",
            "formatting": "🎨 Love the formatting! Clean, readable LaTeX makes for a stunning resume.",
        }

        return encouragements.get(
            context, "💪 Keep up the great work! You're building something amazing!"
        )

    def update_stats(self, action: str, success: bool = True):
        """Update session statistics"""
        if action == "compilation":
            self.session_stats["compilations"] += 1
            if success:
                self.session_stats["successful_compilations"] += 1
        elif action == "enhancement":
            self.session_stats["enhancements_applied"] += 1
        elif action == "section_modification":
            self.session_stats["sections_modified"] += 1

    def get_session_summary(self) -> str:
        """Get session summary with achievements"""
        stats = self.session_stats
        summary = f"🏆 Session Summary:\n"
        summary += f"   📊 {stats['successful_compilations']}/{stats['compilations']} successful compilations\n"
        summary += f"   ✨ {stats['enhancements_applied']} enhancements applied\n"
        summary += f"   📝 {stats['sections_modified']} sections modified\n"

        if stats["successful_compilations"] >= 3:
            summary += "   🌟 LaTeX Master - You're on fire!"
        elif stats["enhancements_applied"] >= 2:
            summary += "   🎯 Enhancement Expert - Great attention to detail!"
        else:
            summary += "   🚀 Keep building - You're making great progress!"

        return summary
