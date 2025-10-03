"""LaTeX processing utilities"""

import re
from typing import Optional, List, Dict, Any


class LatexExtractor:
    """Extract LaTeX code from messages and responses"""

    @staticmethod
    def from_message(message: str) -> Optional[str]:
        """Extract LaTeX from a user message"""
        pattern = r"```(?:latex|tex)?\s*\n(.*?)\n```"
        m = re.search(pattern, message, re.DOTALL)
        if m:
            return m.group(1).strip()
        if "\\documentclass" in message and "\\begin{document}" in message:
            return message.strip()
        return None

    @staticmethod
    def from_response(response: str) -> Optional[str]:
        """
        Extract LaTeX from AI response, ensuring it's a complete document

        Returns None if the extracted LaTeX appears to be just a snippet
        """
        pattern = r"```(?:latex|tex)?\s*\n(.*?)\n```"
        m = re.search(pattern, response, re.DOTALL)
        extracted = m.group(1).strip() if m else None

        if extracted:
            has_docclass = "\\documentclass" in extracted
            has_begin_doc = "\\begin{document}" in extracted
            has_end_doc = "\\end{document}" in extracted

            # If it looks like a snippet (missing key components), reject it
            if not (has_docclass and has_begin_doc and has_end_doc):
                # Check if it's just a section that should be merged
                if re.search(r"\\section", extracted):
                    # This appears to be a partial section edit - don't use it
                    return None

        return extracted

    @staticmethod
    def extract_explanation(response: str) -> Optional[str]:
        """Extract explanation text from response (before code blocks)"""
        lines = []
        for line in response.split("\n"):
            if "```" in line:
                break
            if line.strip():
                lines.append(line.strip())
        return " ".join(lines) if lines else None


class LatexValidator:
    """Validate and repair LaTeX code"""

    @staticmethod
    def ensure_minimal_wrapper(latex: str) -> str:
        """Ensure LaTeX has minimal document structure"""
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

    @staticmethod
    def auto_repair(latex: str, validation_report: str) -> tuple[str, List[str]]:
        """
        Attempt to automatically repair common LaTeX issues

        Returns:
            tuple of (repaired_latex, list_of_fixes_applied)
        """
        fixes: List[str] = []
        original = latex

        # Ensure wrapper
        latex = LatexValidator.ensure_minimal_wrapper(latex)
        if latex != original:
            fixes.append("Added minimal wrapper")

        # Balance braces
        if latex.count("{") > latex.count("}"):
            diff = latex.count("{") - latex.count("}")
            latex += "}" * diff
            fixes.append(f"Balanced {diff} brace(s)")

        # Add missing xcolor
        if "xcolor" in validation_report and "\\usepackage{xcolor}" not in latex:
            latex = re.sub(
                r"(\\documentclass.*?\n)",
                r"\1\\usepackage{xcolor}\n",
                latex,
                1,
                flags=re.DOTALL,
            )
            fixes.append("Added xcolor")

        # Add missing hyperref
        if (
            "hyperref" in validation_report
            and "\\usepackage{hyperref}" not in latex
            and "\\usepackage[hidelinks]{hyperref}" not in latex
        ):
            latex = re.sub(
                r"(\\documentclass.*?\n)",
                r"\1\\usepackage[hidelinks]{hyperref}\n",
                latex,
                1,
                flags=re.DOTALL,
            )
            fixes.append("Added hyperref")

        # Close unclosed itemize environments
        opens = len(re.findall(r"\\begin{itemize}", latex))
        closes = len(re.findall(r"\\end{itemize}", latex))
        if opens > closes:
            latex += "\n" + "\n".join(["\\end{itemize}"] * (opens - closes)) + "\n"
            fixes.append("Closed itemize")

        return latex, fixes


class LatexProcessor:
    """Main LaTeX processing coordinator"""

    def __init__(self, validator_tool, compiler_tool, max_repair_attempts: int = 2):
        self.validator_tool = validator_tool
        self.compiler_tool = compiler_tool
        self.max_repair_attempts = max_repair_attempts

    def validate_and_compile(self, latex: str) -> Dict[str, Any]:
        """
        Validate and compile LaTeX, attempting repairs if needed

        Returns:
            dict with validation and compilation results
        """
        if not latex:
            return {
                "latex": None,
                "valid": False,
                "repairs": [],
                "compiled": False,
                "validation": None,
                "compile_result": None,
            }

        repairs: List[str] = []
        attempt = 0
        validation = self.validator_tool._run(latex)

        # Attempt repairs
        while attempt < self.max_repair_attempts:
            attempt += 1

            # Check if valid
            m = re.search(r"__VALIDATION_JSON__(\{.*\})", validation, re.DOTALL)
            valid_flag = False
            if m:
                try:
                    valid_flag = eval(m.group(1)).get("is_valid", False)
                except Exception:
                    pass

            if valid_flag:
                break

            # Try to repair
            new_latex, fix = LatexValidator.auto_repair(latex, validation)
            if not fix:
                break

            repairs.extend(fix)
            latex = new_latex
            validation = self.validator_tool._run(latex)

        # Final validation check
        m2 = re.search(r"__VALIDATION_JSON__(\{.*\})", validation, re.DOTALL)
        final_valid = False
        if m2:
            try:
                final_valid = eval(m2.group(1)).get("is_valid", False)
            except Exception:
                pass

        # Compile if valid
        compile_result = None
        compiled = False
        if final_valid:
            compile_result = self.compiler_tool._run(latex)
            compiled = "compiled successfully" in compile_result.lower()

        return {
            "latex": latex,
            "valid": final_valid,
            "repairs": repairs,
            "compiled": compiled,
            "validation": validation,
            "compile_result": compile_result,
        }
