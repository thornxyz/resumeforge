"""
Comprehensive LangChain Agent for Resume Building
"""

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
    def __init__(self, gemini_api_key: str):
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        genai.configure(api_key=gemini_api_key)
        self.tools = {
            "compiler": LatexCompilerTool(),
            "validator": LatexValidatorTool(),
            "extractor": LatexSectionExtractorTool(),
            "template_generator": LatexTemplateGeneratorTool(),
            "enhancer": LatexEnhancerTool(),
            "formatter": LatexFormatterTool(),
        }
        self.current_latex = None
        self.user_profile = {}
        self.conversation_history = []
        self.repair_max_attempts = 2

    def _get_system_prompt(self) -> str:
        return """You are **ResumeForge AI** — an expert LaTeX resume crafting assistant that blends technical precision with creative flair.  
    You deliver a “vibe coding” experience: users feel like they’re collaborating with an enthusiastic mentor who’s deeply invested in making their resume shine.

    ## PERSONALITY
    - Warm, encouraging, and confident — a mix of skilled coding mentor and supportive career coach.
    - Use emojis sparingly but meaningfully 🎯✨🔥 to add energy and celebration to progress.
    - Keep a conversational, human tone while staying professional and focused on the goal.
    - Show excitement for user wins and progress (“Yes! That section looks so much cleaner now 🚀”).
    - Give constructive, actionable feedback without being overwhelming.

    ## CAPABILITIES
    You can:
    - Analyze and understand LaTeX resume code.
    - Suggest formatting, layout, and content improvements.
    - Write and modify LaTeX with clean, consistent styling.
    - Validate, debug, and repair broken or misaligned code.
    - Compile and preview LaTeX to verify results.
    - Generate tailored resume templates and section snippets.
    - Enhance typography, alignment, and whitespace for visual polish.

    ## WORKFLOW
    1. **Understand Intent** — Identify exactly what the user wants to change, fix, or improve.
    2. **Plan & Explain** — Outline the approach so the user understands your reasoning.
    3. **Use Tools** — Apply compilation, validation, extraction, or template generation as needed.
    4. **Validate & Repair** — Ensure code is error-free and logically structured.
    5. **Compile if Appropriate** — Confirm that the final output is visually correct.
    6. **Deliver Improvements** — Present clean, functional LaTeX code plus clear explanations.
    7. **Encourage & Guide** — Celebrate progress, suggest next steps, and keep morale high.

    Always return LaTeX code in a **complete, working form** unless the user specifically asks for only a snippet.
    """

    def _extract_latex_from_message(self, message: str) -> Optional[str]:
        pattern = r"```(?:latex|tex)?\s*\n(.*?)\n```"
        m = re.search(pattern, message, re.DOTALL)
        if m:
            return m.group(1).strip()
        if "\\documentclass" in message and "\\begin{document}" in message:
            return message.strip()
        return None

    def _determine_intent_and_tools(self, message: str) -> Dict[str, Any]:
        ml = message.lower()
        intent = {"action": "chat", "tools_needed": [], "confidence": 0.5}
        if any(w in ml for w in ["template", "start", "create resume", "new resume"]):
            intent.update(
                {
                    "action": "generate_template",
                    "tools_needed": ["template_generator"],
                    "confidence": 0.9,
                }
            )
        elif any(w in ml for w in ["compile", "build", "pdf", "generate pdf"]):
            intent.update(
                {
                    "action": "compile",
                    "tools_needed": ["validator", "compiler"],
                    "confidence": 0.9,
                }
            )
        elif any(w in ml for w in ["validate", "check", "errors", "syntax"]):
            intent.update(
                {"action": "validate", "tools_needed": ["validator"], "confidence": 0.8}
            )
        elif any(w in ml for w in ["improve", "enhance", "better", "suggestions"]):
            intent.update(
                {"action": "enhance", "tools_needed": ["enhancer"], "confidence": 0.8}
            )
        elif any(w in ml for w in ["format", "clean", "organize"]):
            intent.update(
                {"action": "format", "tools_needed": ["formatter"], "confidence": 0.8}
            )
        elif any(w in ml for w in ["section", "extract", "show me"]):
            intent.update(
                {"action": "extract", "tools_needed": ["extractor"], "confidence": 0.7}
            )
        elif any(w in ml for w in ["change", "modify", "update", "add", "remove"]):
            intent.update(
                {
                    "action": "modify",
                    "tools_needed": ["validator", "enhancer"],
                    "confidence": 0.7,
                }
            )
        return intent

    def _ensure_minimal_wrapper(self, latex: str) -> str:
        has_docclass = re.search(r"\\documentclass", latex)
        has_begin = "\\begin{document}" in latex
        has_end = "\\end{document}" in latex
        if not has_docclass:
            preamble = (
                "\\documentclass[11pt]{article}\n"
                "\\usepackage[margin=0.8in]{geometry}\n"
                "\\usepackage[hidelinks]{hyperref}\n"
                "\\usepackage{xcolor}\n"
                "\\usepackage{enumitem}\n"
                "\\setlist[itemize]{leftmargin=*,itemsep=2pt,topsep=2pt}\n"
                "\\pagestyle{empty}\n"
            )
            latex = preamble + ("\n" if not latex.startswith("\n") else "") + latex
        if has_docclass and not has_begin and not has_end:
            latex += "\n\\begin{document}\n\n\\end{document}\n"
        else:
            if not has_begin:
                insert_pos = 0
                matches = list(
                    re.finditer(
                        r"^(?:\\documentclass|\\usepackage).*?$", latex, re.MULTILINE
                    )
                )
                if matches:
                    insert_pos = matches[-1].end()
                latex = (
                    latex[:insert_pos] + "\n\\begin{document}\n" + latex[insert_pos:]
                )
            if not has_end:
                latex += "\n\\end{document}\n"
        return latex

    def _auto_repair_latex(
        self, latex: str, validation_report: str
    ) -> tuple[str, List[str]]:
        fixes: List[str] = []
        m = re.search(r"__VALIDATION_JSON__(\{.*\})", validation_report, re.DOTALL)
        if m:
            try:
                eval(m.group(1))
            except Exception:
                pass
        original = latex
        latex = self._ensure_minimal_wrapper(latex)
        if latex != original:
            fixes.append("Added minimal wrapper")
        if latex.count("{") > latex.count("}"):
            diff = latex.count("{") - latex.count("}")
            latex += "}" * diff
            fixes.append(f"Balanced {diff} brace(s)")
        if "xcolor" in validation_report and "\\usepackage{xcolor}" not in latex:
            latex = re.sub(
                r"(\\documentclass.*?\n)",
                r"\\1\\usepackage{xcolor}\n",
                latex,
                1,
                flags=re.DOTALL,
            )
            fixes.append("Added xcolor")
        if (
            "hyperref" in validation_report
            and "\\usepackage{hyperref}" not in latex
            and "\\usepackage[hidelinks]{hyperref}" not in latex
        ):
            latex = re.sub(
                r"(\\documentclass.*?\n)",
                r"\\1\\usepackage[hidelinks]{hyperref}\n",
                latex,
                1,
                flags=re.DOTALL,
            )
            fixes.append("Added hyperref")
        opens = len(re.findall(r"\\begin{itemize}", latex))
        closes = len(re.findall(r"\\end{itemize}", latex))
        if opens > closes:
            latex += "\n" + "\n".join(["\\end{itemize}"] * (opens - closes)) + "\n"
            fixes.append("Closed itemize")
        return latex, fixes

    def _post_generate_validate_cycle(self, latex: str) -> Dict[str, Any]:
        if not latex:
            return {
                "latex": None,
                "valid": False,
                "repairs": [],
                "compiled": False,
                "validation": None,
                "compile_result": None,
            }
        validator: LatexValidatorTool = self.tools["validator"]
        compiler: LatexCompilerTool = self.tools["compiler"]
        repairs: List[str] = []
        attempt = 0
        validation = validator._run(latex)
        while attempt < self.repair_max_attempts:
            attempt += 1
            m = re.search(r"__VALIDATION_JSON__(\{.*\})", validation, re.DOTALL)
            valid_flag = False
            if m:
                try:
                    valid_flag = eval(m.group(1)).get("is_valid", False)
                except Exception:
                    pass
            if valid_flag:
                break
            new_latex, fix = self._auto_repair_latex(latex, validation)
            if not fix:
                break
            repairs.extend(fix)
            latex = new_latex
            validation = validator._run(latex)
        m2 = re.search(r"__VALIDATION_JSON__(\{.*\})", validation, re.DOTALL)
        final_valid = False
        if m2:
            try:
                final_valid = eval(m2.group(1)).get("is_valid", False)
            except Exception:
                pass
        compile_result = None
        compiled = False
        if final_valid:
            compile_result = compiler._run(latex)
            compiled = "compiled successfully" in compile_result.lower()
        return {
            "latex": latex,
            "valid": final_valid,
            "repairs": repairs,
            "compiled": compiled,
            "validation": validation,
            "compile_result": compile_result,
        }

    def _execute_tools(
        self, tools_needed: List[str], message: str, latex_content: str = None
    ) -> Dict[str, str]:
        results: Dict[str, str] = {}
        for tool_name in tools_needed:
            if tool_name not in self.tools:
                continue
            tool = self.tools[tool_name]
            try:
                if tool_name == "template_generator":
                    style = "modern"
                    if "classic" in message.lower():
                        style = "classic"
                    elif "creative" in message.lower():
                        style = "creative"
                    elif "academic" in message.lower():
                        style = "academic"
                    results[tool_name] = tool._run(style)
                elif tool_name == "extractor":
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

    def _create_comprehensive_prompt(
        self, message: str, tool_results: Dict[str, str]
    ) -> str:
        prompt = f"{self._get_system_prompt()}\n\n"
        if self.current_latex:
            prompt += f"CURRENT LATEX CONTENT:\n```latex\n{self.current_latex}\n```\n\n"
        if tool_results:
            prompt += "TOOL ANALYSIS RESULTS:\n"
            for n, r in tool_results.items():
                prompt += f"\n{n.upper()} RESULT:\n{r}\n"
            prompt += "\n"
        if self.conversation_history:
            prompt += "RECENT CONVERSATION:\n"
            for msg in self.conversation_history[-6:]:
                role = "User" if msg["role"] == "user" else "Assistant"
                prompt += f"{role}: {msg['content']}\n"
            prompt += "\n"
        prompt += (
            f"USER MESSAGE: {message}\n\n"
            "Please respond with helpful guidance. Include LaTeX in a ```latex block if changed."
        )
        return prompt

    async def process_message(
        self, message: str, conversation_history: List[Dict]
    ) -> Dict[str, Any]:
        try:
            self.conversation_history = conversation_history
            latex_content = self._extract_latex_from_message(message)
            if latex_content:
                self.current_latex = latex_content
            intent = self._determine_intent_and_tools(message)
            tool_results: Dict[str, str] = {}
            tools_used: List[str] = []
            if intent["tools_needed"]:
                tool_results = self._execute_tools(
                    intent["tools_needed"], message, latex_content
                )
                for key in intent["tools_needed"]:
                    if key in self.tools:
                        tools_used.append(self.tools[key].name)
            prompt = self._create_comprehensive_prompt(message, tool_results)
            try:
                response = self.model.generate_content(prompt)
                response_text = getattr(response, "text", str(response))
            except Exception as e:
                return {"success": False, "error": f"Model generation failed: {e}"}
            modified_latex = self._extract_latex_from_response(response_text)
            reliability = {}
            if modified_latex:
                reliability = self._post_generate_validate_cycle(modified_latex)
                repaired = reliability.get("latex")
                if repaired and repaired != modified_latex:
                    repairs = reliability.get("repairs", [])
                    if repairs:
                        response_text += "\n\n(Repairs: " + "; ".join(repairs) + ")"
                    modified_latex = repaired
                if reliability.get("compile_result"):
                    if reliability.get("compiled"):
                        response_text += "\n\nCompiled successfully."
                    else:
                        response_text += "\n\nCompile feedback: " + reliability.get(
                            "compile_result", ""
                        )
                    if "latex_compiler" not in tools_used:
                        tools_used.append("latex_compiler")
                if (
                    reliability.get("validation")
                    and "latex_validator" not in tools_used
                ):
                    tools_used.append("latex_validator")
                self.current_latex = modified_latex
            return {
                "success": True,
                "response": response_text,
                "modifiedLatex": modified_latex,
                "explanation": self._extract_explanation(response_text),
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

    def _extract_latex_from_response(self, response: str) -> Optional[str]:
        pattern = r"```(?:latex|tex)?\s*\n(.*?)\n```"
        m = re.search(pattern, response, re.DOTALL)
        return m.group(1).strip() if m else None

    def _extract_explanation(self, response: str) -> Optional[str]:
        lines = []
        for line in response.split("\n"):
            if "```" in line:
                break
            if line.strip():
                lines.append(line.strip())
        return " ".join(lines) if lines else None

    def reset_conversation(self):
        self.conversation_history = []
        self.current_latex = None
        self.user_profile = {}

    def set_user_profile(self, profile: Dict[str, Any]):
        self.user_profile = profile

    def get_current_latex(self) -> Optional[str]:
        return self.current_latex

    def set_current_latex(self, latex_content: str):
        self.current_latex = latex_content


class VibeManager:
    def __init__(self):
        self.session_stats = {
            "compilations": 0,
            "successful_compilations": 0,
            "enhancements_applied": 0,
            "sections_modified": 0,
        }

    def get_encouragement(self, context: str) -> str:
        messages = {
            "first_template": "Great start!",
            "successful_compile": "Compiled perfectly!",
            "error_fix": "Nice debugging!",
            "enhancement": "Improvement applied!",
            "new_section": "Section added!",
            "formatting": "Formatting polished!",
        }
        return messages.get(context, "Keep going!")

    def update_stats(self, action: str, success: bool = True):
        if action == "compilation":
            self.session_stats["compilations"] += 1
            if success:
                self.session_stats["successful_compilations"] += 1
        elif action == "enhancement":
            self.session_stats["enhancements_applied"] += 1
        elif action == "section_modification":
            self.session_stats["sections_modified"] += 1

    def get_session_summary(self) -> str:
        s = self.session_stats
        summary = (
            "Session Summary:\n"
            f"  {s['successful_compilations']}/{s['compilations']} successful compilations\n"
            f"  {s['enhancements_applied']} enhancements applied\n"
            f"  {s['sections_modified']} sections modified\n"
        )
        return summary
