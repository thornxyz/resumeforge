"""
LaTeX Resume Building Tools for the Agent
"""

import re
import json
import requests
import tempfile
import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class BaseTool:
    """Base class for tools"""

    name = "base_tool"
    description = "Base tool class"

    def _run(self, *args, **kwargs):
        raise NotImplementedError

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)


class LatexCompilerTool(BaseTool):
    """Tool for compiling LaTeX code using the Docker container"""

    name = "latex_compiler"
    description = "Compile LaTeX code to PDF using the Docker container. Returns compilation status and any errors."

    def _run(self, latex_content: str) -> str:
        """Compile LaTeX content to PDF"""
        try:
            response = requests.post(
                "http://localhost:8000/compile",
                files={"file": ("resume.tex", latex_content, "text/plain")},
                timeout=30,
            )

            if response.status_code == 200:
                return "✅ LaTeX compiled successfully! PDF generated without errors."
            else:
                error_info = (
                    response.json()
                    if response.headers.get("content-type") == "application/json"
                    else {"error": response.text}
                )
                return (
                    f"❌ Compilation failed: {error_info.get('error', 'Unknown error')}"
                )

        except requests.exceptions.RequestException as e:
            return f"❌ Failed to connect to LaTeX compiler: {str(e)}"

    async def _arun(self, latex_content: str) -> str:
        return self._run(latex_content)


class LatexValidatorTool(BaseTool):
    """Tool for validating LaTeX syntax"""

    name = "latex_validator"
    description = (
        "Validate LaTeX syntax and check for common errors before compilation."
    )

    def _run(self, latex_content: str) -> str:
        """Validate LaTeX syntax"""
        errors = []
        warnings = []

        # Check for basic LaTeX structure
        if not re.search(r"\\documentclass", latex_content):
            errors.append("Missing \\documentclass declaration")

        if not re.search(r"\\begin\{document\}", latex_content):
            errors.append("Missing \\begin{document}")

        if not re.search(r"\\end\{document\}", latex_content):
            errors.append("Missing \\end{document}")

        # Check for balanced braces
        open_braces = latex_content.count("{")
        close_braces = latex_content.count("}")
        if open_braces != close_braces:
            errors.append(
                f"Unbalanced braces: {open_braces} opening, {close_braces} closing"
            )

        # Check for common LaTeX environments
        environments = re.findall(r"\\begin\{(\w+)\}", latex_content)
        for env in environments:
            if not re.search(rf"\\end\{{{env}\}}", latex_content):
                errors.append(f"Unclosed environment: {env}")

        # Check for common packages that might be missing
        if re.search(r"\\textcolor|\\color", latex_content) and not re.search(
            r"\\usepackage.*xcolor", latex_content
        ):
            warnings.append("Using color commands without xcolor package")

        if re.search(r"\\href|\\url", latex_content) and not re.search(
            r"\\usepackage.*hyperref", latex_content
        ):
            warnings.append("Using hyperlinks without hyperref package")

        result = []
        if errors:
            result.append("🔴 Errors found:")
            for error in errors:
                result.append(f"  - {error}")

        if warnings:
            result.append("🟡 Warnings:")
            for warning in warnings:
                result.append(f"  - {warning}")

        if not errors and not warnings:
            result.append("✅ LaTeX syntax looks good!")

        return "\n".join(result)

    async def _arun(self, latex_content: str) -> str:
        return self._run(latex_content)


class LatexSectionExtractorTool(BaseTool):
    """Tool for extracting specific sections from LaTeX resume"""

    name = "latex_section_extractor"
    description = "Extract specific sections (like experience, education, skills) from LaTeX resume code."

    def _run(self, latex_content: str, section_name: str = "") -> str:
        """Extract a specific section from LaTeX content"""
        if not section_name:
            # Return available sections
            sections = re.findall(r"\\section\*?\{([^}]+)\}", latex_content)
            if sections:
                return f"Available sections: {', '.join(sections)}"
            else:
                return "No sections found in the LaTeX content."

        # Extract specific section
        pattern = rf"\\section\*?\{{{re.escape(section_name)}\}}(.*?)(?=\\section|\Z)"
        match = re.search(pattern, latex_content, re.DOTALL | re.IGNORECASE)

        if match:
            return f"Section '{section_name}':\n{match.group(1).strip()}"
        else:
            return f"Section '{section_name}' not found."

    async def _arun(self, latex_content: str, section_name: str = "") -> str:
        return self._run(latex_content, section_name)


class LatexTemplateGeneratorTool(BaseTool):
    """Tool for generating LaTeX resume templates"""

    name = "latex_template_generator"
    description = "Generate LaTeX resume templates with different styles (modern, classic, creative, academic)."

    def _run(
        self,
        style: str = "modern",
        name: str = "[Your Name]",
        email: str = "[your.email@example.com]",
    ) -> str:
        """Generate a LaTeX template based on style"""

        templates = {
            "modern": self._modern_template(name, email),
            "classic": self._classic_template(name, email),
            "creative": self._creative_template(name, email),
            "academic": self._academic_template(name, email),
        }

        if style.lower() in templates:
            return templates[style.lower()]
        else:
            return f"Unknown style '{style}'. Available styles: {', '.join(templates.keys())}"

    def _modern_template(self, name: str, email: str) -> str:
        return f"""\\documentclass[11pt,a4paper,sans]{{moderncv}}
\\moderncvstyle{{banking}}
\\moderncvcolor{{blue}}
\\usepackage[scale=0.75]{{geometry}}

\\name{{{name}}}{{}}
\\email{{{email}}}
\\phone{{+1 (555) 123-4567}}
\\social[linkedin]{{your-linkedin}}
\\social[github]{{your-github}}

\\begin{{document}}
\\makecvtitle

\\section{{Experience}}
\\cventry{{2024--Present}}{{Software Developer}}{{Tech Company}}{{City, State}}{{}}{{
\\begin{{itemize}}
\\item Developed and maintained web applications using modern frameworks
\\item Collaborated with cross-functional teams to deliver high-quality software
\\item Improved application performance by 30\\% through optimization
\\end{{itemize}}}}

\\section{{Education}}
\\cventry{{2020--2024}}{{Bachelor of Science in Computer Science}}{{University Name}}{{City, State}}{{GPA: 3.8/4.0}}{{}}

\\section{{Skills}}
\\cvitem{{Programming}}{{Python, JavaScript, TypeScript, Java}}
\\cvitem{{Frameworks}}{{React, Node.js, FastAPI, Django}}
\\cvitem{{Tools}}{{Git, Docker, AWS, PostgreSQL}}

\\end{{document}}"""

    def _classic_template(self, name: str, email: str) -> str:
        return f"""\\documentclass[letterpaper,11pt]{{article}}
\\usepackage[left=0.75in,top=0.6in,right=0.75in,bottom=0.6in]{{geometry}}
\\usepackage{{enumitem}}
\\usepackage{{hyperref}}

\\pagestyle{{empty}}

\\begin{{document}}

\\begin{{center}}
{{\\LARGE \\bf {name}}} \\\\
\\vspace{{0.1in}}
{email} $\\cdot$ +1 (555) 123-4567 $\\cdot$ linkedin.com/in/yourprofile
\\end{{center}}

\\vspace{{0.2in}}

\\noindent{{\\bf EXPERIENCE}}
\\hrule
\\vspace{{0.1in}}

\\noindent{{\\bf Software Developer}} \\hfill {{\\em 2024 -- Present}} \\\\
{{\\em Tech Company, City, State}}
\\begin{{itemize}}[leftmargin=*]
\\item Developed and maintained web applications using modern frameworks
\\item Collaborated with cross-functional teams to deliver high-quality software
\\item Improved application performance by 30\\% through optimization
\\end{{itemize}}

\\vspace{{0.1in}}
\\noindent{{\\bf EDUCATION}}
\\hrule
\\vspace{{0.1in}}

\\noindent{{\\bf Bachelor of Science in Computer Science}} \\hfill {{\\em 2020 -- 2024}} \\\\
{{\\em University Name, City, State}} \\hfill {{\\em GPA: 3.8/4.0}}

\\vspace{{0.1in}}
\\noindent{{\\bf SKILLS}}
\\hrule
\\vspace{{0.1in}}

\\noindent{{\\bf Programming:}} Python, JavaScript, TypeScript, Java \\\\
{{\\bf Frameworks:}} React, Node.js, FastAPI, Django \\\\
{{\\bf Tools:}} Git, Docker, AWS, PostgreSQL

\\end{{document}}"""

    def _creative_template(self, name: str, email: str) -> str:
        return f"""\\documentclass[11pt,a4paper]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{xcolor}}
\\usepackage{{tikz}}
\\usepackage[left=0.7in,top=0.5in,right=0.7in,bottom=0.5in]{{geometry}}
\\usepackage{{fontawesome5}}
\\usepackage{{hyperref}}

\\definecolor{{primary}}{{RGB}}{{52, 152, 219}}
\\definecolor{{secondary}}{{RGB}}{{149, 165, 166}}

\\pagestyle{{empty}}

\\begin{{document}}

\\begin{{tikzpicture}}[remember picture,overlay]
\\fill[primary] (current page.north west) rectangle ([yshift=-3cm]current page.north east);
\\end{{tikzpicture}}

\\vspace{{1cm}}
\\begin{{center}}
{{\\Huge\\color{{white}}\\bf {name}}} \\\\
\\vspace{{0.3cm}}
{{\\Large\\color{{white}} Software Developer}}
\\end{{center}}

\\vspace{{1cm}}

\\noindent\\begin{{minipage}}{{0.3\\textwidth}}
\\raggedright
\\section*{{\\color{{primary}}Contact}}
\\faEnvelope \\, {email} \\\\
\\faPhone \\, +1 (555) 123-4567 \\\\
\\faLinkedin \\, linkedin.com/in/you \\\\
\\faGithub \\, github.com/you

\\vspace{{0.5cm}}
\\section*{{\\color{{primary}}Skills}}
\\textbf{{Languages:}} \\\\
Python, JavaScript, TypeScript

\\textbf{{Frameworks:}} \\\\
React, Node.js, FastAPI

\\textbf{{Tools:}} \\\\
Git, Docker, AWS
\\end{{minipage}}%
\\hfill
\\begin{{minipage}}{{0.65\\textwidth}}
\\section*{{\\color{{primary}}Experience}}
\\textbf{{Software Developer}} \\hfill \\textit{{2024 -- Present}} \\\\
\\textit{{Tech Company, City, State}}
\\begin{{itemize}}
\\item Developed web applications using modern frameworks
\\item Improved performance by 30\\% through optimization
\\item Collaborated with cross-functional teams
\\end{{itemize}}

\\vspace{{0.3cm}}
\\section*{{\\color{{primary}}Education}}
\\textbf{{Bachelor of Science in Computer Science}} \\hfill \\textit{{2020 -- 2024}} \\\\
\\textit{{University Name, City, State}} \\\\
GPA: 3.8/4.0
\\end{{minipage}}

\\end{{document}}"""

    def _academic_template(self, name: str, email: str) -> str:
        return f"""\\documentclass[11pt]{{article}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage{{enumitem}}
\\usepackage{{hyperref}}
\\usepackage{{bibentry}}

\\pagestyle{{empty}}

\\begin{{document}}

\\begin{{center}}
{{\\Large \\textbf{{{name}}}}} \\\\
\\vspace{{0.1in}}
{email} $\\bullet$ +1 (555) 123-4567 $\\bullet$ Department of Computer Science \\\\
University Name, City, State
\\end{{center}}

\\section*{{Research Interests}}
Artificial Intelligence, Machine Learning, Natural Language Processing

\\section*{{Education}}
\\textbf{{Ph.D. in Computer Science}} \\hfill 2024 -- Present \\\\
University Name, City, State \\\\
Advisor: Dr. John Smith \\\\
Dissertation: "Advanced Techniques in Machine Learning"

\\textbf{{Master of Science in Computer Science}} \\hfill 2022 -- 2024 \\\\
University Name, City, State \\\\
GPA: 3.9/4.0 \\\\
Thesis: "Deep Learning Applications in Natural Language Processing"

\\section*{{Publications}}
\\begin{{enumerate}}
\\item Smith, J., \\textbf{{{name[1:-1]}}}. "A Novel Approach to Machine Learning." \\textit{{Journal of AI Research}}, 2024.
\\item \\textbf{{{name[1:-1]}}}, Brown, A. "Advances in Neural Networks." \\textit{{Conference on Machine Learning}}, 2023.
\\end{{enumerate}}

\\section*{{Research Experience}}
\\textbf{{Research Assistant}} \\hfill 2024 -- Present \\\\
AI Research Lab, University Name
\\begin{{itemize}}
\\item Developed novel machine learning algorithms
\\item Published research in top-tier conferences
\\item Mentored undergraduate research students
\\end{{itemize}}

\\section*{{Awards and Honors}}
\\begin{{itemize}}
\\item Outstanding Graduate Student Award, 2024
\\item Best Paper Award, Conference on Machine Learning, 2023
\\item Graduate Fellowship, 2022-2024
\\end{{itemize}}

\\end{{document}}"""

    async def _arun(
        self,
        style: str = "modern",
        name: str = "[Your Name]",
        email: str = "[your.email@example.com]",
    ) -> str:
        return self._run(style, name, email)


class LatexEnhancerTool(BaseTool):
    """Tool for enhancing LaTeX resumes with better formatting and content suggestions"""

    name = "latex_enhancer"
    description = "Enhance LaTeX resume with better formatting, professional language, and content suggestions."

    def _run(self, latex_content: str, enhancement_type: str = "all") -> str:
        """Enhance LaTeX content"""
        suggestions = []

        if enhancement_type in ["all", "formatting"]:
            suggestions.extend(self._analyze_formatting(latex_content))

        if enhancement_type in ["all", "content"]:
            suggestions.extend(self._analyze_content(latex_content))

        if enhancement_type in ["all", "structure"]:
            suggestions.extend(self._analyze_structure(latex_content))

        if not suggestions:
            return "✅ Your resume looks great! No immediate enhancements needed."

        return "💡 Enhancement suggestions:\n" + "\n".join(
            f"• {suggestion}" for suggestion in suggestions
        )

    def _analyze_formatting(self, content: str) -> List[str]:
        suggestions = []

        # Check for consistent spacing
        if re.search(r"\\\\\\\\", content):
            suggestions.append(
                "Remove excessive line breaks (\\\\\\\\) for cleaner formatting"
            )

        # Check for proper sectioning
        if not re.search(r"\\section", content):
            suggestions.append("Add section headers to organize your resume better")

        # Check for bullet points
        if "itemize" not in content and "enumerate" not in content:
            suggestions.append(
                "Consider using bullet points (itemize) for better readability"
            )

        return suggestions

    def _analyze_content(self, content: str) -> List[str]:
        suggestions = []

        # Check for action verbs
        weak_verbs = ["did", "made", "worked on", "helped with", "responsible for"]
        for verb in weak_verbs:
            if verb.lower() in content.lower():
                suggestions.append(
                    f"Replace weak verb '{verb}' with stronger action verbs"
                )

        # Check for quantifiable achievements
        if not re.search(r"\d+%|\d+\+|\$\d+", content):
            suggestions.append(
                "Add quantifiable achievements (percentages, numbers, metrics)"
            )

        return suggestions

    def _analyze_structure(self, content: str) -> List[str]:
        suggestions = []

        # Check section order
        sections = re.findall(r"\\section\*?\{([^}]+)\}", content)
        if sections:
            if "experience" not in " ".join(sections).lower():
                suggestions.append("Consider adding an Experience section")
            if "education" not in " ".join(sections).lower():
                suggestions.append("Consider adding an Education section")
            if "skills" not in " ".join(sections).lower():
                suggestions.append("Consider adding a Skills section")

        return suggestions

    async def _arun(self, latex_content: str, enhancement_type: str = "all") -> str:
        return self._run(latex_content, enhancement_type)


class LatexFormatterTool(BaseTool):
    """Tool for formatting and cleaning up LaTeX code"""

    name = "latex_formatter"
    description = (
        "Format and clean up LaTeX code for better readability and consistency."
    )

    def _run(self, latex_content: str) -> str:
        """Format LaTeX content"""
        # Remove excessive whitespace
        formatted = re.sub(r"\n\s*\n\s*\n", "\n\n", latex_content)

        # Ensure proper indentation for environments
        lines = formatted.split("\n")
        formatted_lines = []
        indent_level = 0

        for line in lines:
            stripped = line.strip()

            # Decrease indent for end commands
            if re.match(r"\\end\{", stripped):
                indent_level = max(0, indent_level - 1)

            # Add indentation
            if stripped:
                formatted_lines.append("  " * indent_level + stripped)
            else:
                formatted_lines.append("")

            # Increase indent for begin commands
            if re.match(r"\\begin\{", stripped):
                indent_level += 1

        return "\n".join(formatted_lines)

    async def _arun(self, latex_content: str) -> str:
        return self._run(latex_content)
