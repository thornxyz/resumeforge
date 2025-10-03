"""LaTeX tools for resume building"""

import re
import requests
from typing import List


class LatexCompilerTool:
    """Compile LaTeX to PDF via local service"""
    
    name = "latex_compiler"
    description = "Compile LaTeX to PDF via local service"

    def _run(self, latex_content: str) -> str:
        """Compile LaTeX content to PDF"""
        if "\\documentclass" not in latex_content:
            return "❌ Compilation failed: Missing \\documentclass"
        
        try:
            r = requests.post(
                "http://localhost:8000/compile",
                files={"file": ("resume.tex", latex_content, "text/plain")},
                timeout=35,
            )
        except requests.exceptions.RequestException as e:
            return f"❌ Failed to connect to LaTeX compiler: {e}"
        
        if r.status_code == 200:
            return "✅ LaTeX compiled successfully! PDF generated."
        
        try:
            err = r.json().get("error")
        except Exception:
            err = r.text[:500]
        return f"❌ Compilation failed: {err}"


class LatexValidatorTool:
    """Validate LaTeX and report issues"""
    
    name = "latex_validator"
    description = "Validate LaTeX and report issues + JSON tail"

    def _run(self, latex_content: str) -> str:
        """Validate LaTeX content and return report"""
        errors: List[str] = []
        warnings: List[str] = []
        fixes: List[str] = []
        
        # Check for document structure
        if not re.search(r"\\documentclass", latex_content):
            errors.append("Missing \\documentclass")
            fixes.append("Add minimal preamble")
        
        if not re.search(r"\\begin{document}", latex_content):
            errors.append("Missing \\begin{document}")
            fixes.append("Add \\begin{document}")
        
        if not re.search(r"\\end{document}", latex_content):
            errors.append("Missing \\end{document}")
            fixes.append("Add \\end{document}")
        
        # Check for balanced braces
        if latex_content.count("{") != latex_content.count("}"):
            errors.append("Unbalanced braces")
            fixes.append("Balance braces")
        
        # Check for unclosed environments
        for env in re.findall(r"\\begin{(\w+)}", latex_content):
            if not re.search(rf"\\end{{{env}}}", latex_content):
                errors.append(f"Unclosed environment: {env}")
                fixes.append(f"Add \\end{{{env}}}")
        
        # Check for missing packages
        if re.search(r"\\(?:textcolor|color)\b", latex_content) and not re.search(
            r"\\usepackage{.*?xcolor.*?}", latex_content
        ):
            warnings.append("Color commands without xcolor")
            fixes.append("Add \\usepackage{xcolor}")
        
        if re.search(r"\\(?:href|url)\b", latex_content) and not re.search(
            r"\\usepackage{.*?hyperref.*?}", latex_content
        ):
            warnings.append("Hyperlink commands without hyperref")
            fixes.append("Add \\usepackage{hyperref}")
        
        # Check for resume sections
        sections = [
            s.lower() 
            for s in re.findall(r"\\section\*?{([^}]+)}", latex_content)
        ]
        if not any(s in sections for s in ["experience", "education", "skills"]):
            warnings.append("No standard resume sections")
            fixes.append("Add Experience/Education/Skills")
        
        # Build output
        out: List[str] = []
        if errors:
            out.append("🔴 Errors:")
            out.extend("  - " + e for e in errors)
        
        if warnings:
            out.append("🟡 Warnings:")
            out.extend("  - " + w for w in warnings)
        
        if fixes:
            out.append("🛠 Suggested fixes:")
            out.extend("  - " + f for f in fixes)
        
        if not errors and not warnings:
            out.append("✅ LaTeX syntax looks good!")
        
        # Add JSON validation result
        out.append(
            "__VALIDATION_JSON__"
            + str(
                {
                    "errors": errors,
                    "warnings": warnings,
                    "fixes": fixes,
                    "is_valid": not errors,
                }
            )
        )
        
        return "\n".join(out)


class LatexSectionExtractorTool:
    """Extract sections from LaTeX documents"""
    
    name = "latex_section_extractor"
    description = "Extract a named section"

    def _run(self, latex_content: str, section_name: str = "") -> str:
        """Extract a specific section or list all sections"""
        if not section_name:
            secs = re.findall(r"\\section\*?{([^}]+)}", latex_content)
            return (
                f"Available sections: {', '.join(secs)}"
                if secs
                else "No sections found."
            )
        
        pattern = rf"\\section\*?{{{re.escape(section_name)}}}(.*?)(?=\\section|\\end{{document}}|\Z)"
        m = re.search(pattern, latex_content, re.DOTALL | re.IGNORECASE)
        
        return (
            f"Section '{section_name}':\n{m.group(1).strip()}"
            if m
            else f"Section '{section_name}' not found."
        )


class LatexTemplateGeneratorTool:
    """Generate resume templates in various styles"""
    
    name = "latex_template_generator"
    description = "Generate resume template"

    def _run(self, style: str = "modern") -> str:
        """Generate a resume template based on the specified style"""
        style = style.lower().strip()
        
        templates = {
            "modern": self._modern_template,
            "classic": self._classic_template,
            "creative": self._creative_template,
            "academic": self._academic_template,
        }
        
        template_func = templates.get(style, self._modern_template)
        return template_func()

    def _common_preamble(self) -> str:
        """Return common LaTeX preamble used by all templates"""
        return (
            "\\documentclass[11pt]{article}\n"
            "\\usepackage[margin=0.8in]{geometry}\n"
            "\\usepackage[hidelinks]{hyperref}\n"
            "\\usepackage{xcolor}\n"
            "\\usepackage{enumitem}\n"
            "\\setlist[itemize]{leftmargin=*,itemsep=2pt,topsep=2pt}\n"
            "\\usepackage[T1]{fontenc}\n"
            "\\usepackage[utf8]{inputenc}\n"
            "\\usepackage{titlesec}\n"
            "\\titleformat{\\section}{\\large\\bfseries}{}{0pt}{}\\titlerule[0.5pt]\n"
            "\\pagestyle{empty}\n"
        )

    def _modern_template(self) -> str:
        """Generate modern template"""
        return f"""{self._common_preamble()}\\begin{{document}}
\\begin{{center}}
{{\\LARGE [Your Name]}}\\\\
{{\\normalsize [your.email@example.com] • LinkedIn • GitHub}}\\\\
\\end{{center}}

\\section{{Summary}}
Results-oriented engineer focused on scalable web applications.

\\section{{Experience}}
\\textbf{{Software Engineer}}, Tech Company (2024--Present)\\\\
\\begin{{itemize}}
  \\item Built full-stack features (TypeScript/Python).
  \\item Reduced API latency 30\\%.
  \\item Shipped UX improvements cross-team.
\\end{{itemize}}

\\section{{Education}}
B.S. Computer Science, University (2020--2024) -- GPA 3.8/4.0

\\section{{Skills}}
Languages: Python, JS, TS, SQL\\\\
Frameworks: React, Next.js, FastAPI\\\\
Tools: Git, Docker, PostgreSQL, AWS

\\end{{document}}"""

    def _classic_template(self) -> str:
        """Generate classic template"""
        return f"""{self._common_preamble()}\\begin{{document}}
\\begin{{center}}
{{\\Large [Your Name]}}\\\\
{{[your.email@example.com] • Location • +1 (555) 123-4567}}\\\\
\\end{{center}}

\\section{{Objective}}
Seeking a software engineering role contributing reliable systems.

\\section{{Experience}}
\\textbf{{Junior Developer}}, Company A (2023--2024)\\\\
\\begin{{itemize}}
  \\item Built internal productivity tools.
  \\item Raised test coverage to 85\\%.
\\end{{itemize}}

\\section{{Education}}
University — B.S. CS (2020--2024)\\\\
Coursework: Data Structures, Algorithms, DBs

\\section{{Skills}}
Programming: Python, JS, SQL\\\\
Other: Git, Docker, Linux

\\end{{document}}"""

    def _creative_template(self) -> str:
        """Generate creative template"""
        return f"""{self._common_preamble()}\\definecolor{{accent}}{{HTML}}{{005F99}}

\\begin{{document}}
\\begin{{center}}
{{\\fontsize{{24}}{{26}}\\selectfont\\textcolor{{accent}}{{[Your Name]}}}}\\\\
{{\\small [your.email@example.com] • Portfolio • @handle}}\\\\
\\end{{center}}

\\section{{Profile}}
Creative full-stack engineer blending design + engineering.

\\section{{Projects}}
\\textbf{{Project Alpha}} Dashboard analytics\\\\
\\begin{{itemize}}
  \\item Modular React component system.
  \\item Real-time websocket updates.
\\end{{itemize}}

\\textbf{{Project Beta}} Automation scripts reduced ops 40\\%.

\\section{{Skills}}
Frontend: React, Next.js, Tailwind\\\\
Backend: FastAPI, Node.js, PostgreSQL\\\\
Other: Docker, CI/CD, Testing

\\section{{Experience}}
Freelance Developer (2022--Present)\\\\
\\begin{{itemize}}
  \\item Delivered accessible performant web apps.
\\end{{itemize}}

\\end{{document}}"""

    def _academic_template(self) -> str:
        """Generate academic template"""
        return f"""{self._common_preamble()}\\begin{{document}}
\\begin{{center}}
{{\\Large [Your Name]}}\\\\
{{[your.email@example.com] • Google Scholar}}\\\\
\\end{{center}}

\\section{{Research Interests}}
Distributed systems, applied ML, performance.

\\section{{Publications}}
\\begin{{itemize}}
  \\item Author et al. "Paper Title", Conf 2024.
  \\item Author et al. "Another Publication", Journal 2023.
\\end{{itemize}}

\\section{{Education}}
B.S. CS, University, 2024

\\section{{Experience}}
Research Assistant (2023--2024)\\\\
\\begin{{itemize}}
  \\item Built evaluation framework for schedulers.
\\end{{itemize}}

\\section{{Skills}}
Languages: Python, C++, Go\\\\
Tools: Git, Docker, Linux, LaTeX

\\end{{document}}"""


class LatexEnhancerTool:
    """Enhance LaTeX content"""
    
    name = "latex_enhancer"
    description = "Enhance LaTeX content"

    def _run(self, latex_content: str) -> str:
        """Enhance LaTeX content by converting plain lists to itemize"""
        if not latex_content.strip():
            return "No LaTeX content supplied."
        
        suggestions: List[str] = []
        lines = latex_content.splitlines()
        out: List[str] = []
        inside = False
        
        for line in lines:
            s = line.strip()
            
            # Detect start of plain list
            if re.match(r"^- ", s) and not inside:
                out.append("\\begin{itemize}")
                inside = True
            
            # Detect end of plain list
            if inside and s == "":
                out.append("\\end{itemize}")
                inside = False
            
            # Convert list item
            if inside and re.match(r"^- ", s):
                bullet = re.sub(r"^- ", "", s)
                bullet = re.sub(r"^(\w)", lambda m: m.group(1).upper(), bullet)
                suggestions.append(f"Converted list item: {bullet[:40]}")
                out.append(f"  \\item {bullet}")
            else:
                out.append(line)
        
        # Close any remaining itemize
        if inside:
            out.append("\\end{itemize}")
        
        improved = "\n".join(out)
        
        # Check for quantifiable metrics
        if re.search(r"\\item", improved) and not re.search(r"\d+%", improved):
            suggestions.append("Add quantifiable impact numbers to bullets.")
        
        # Build report
        report = ["Enhancements:"] + [
            "  - " + s for s in (suggestions or ["Already structured."])
        ]
        report.append("\nImproved LaTeX:\n" + improved)
        
        return "\n".join(report)


class LatexFormatterTool:
    """Format and normalize LaTeX"""
    
    name = "latex_formatter"
    description = "Format / normalize LaTeX"

    def _run(self, latex_content: str) -> str:
        """Format and normalize LaTeX content"""
        if not latex_content.strip():
            return "No LaTeX content to format."
        
        # Normalize line endings
        c = latex_content.replace("\r\n", "\n").replace("\r", "\n")
        
        # Remove trailing whitespace
        c = "\n".join(l.rstrip() for l in c.splitlines())
        
        # Normalize blank lines
        c = re.sub(r"\n{3,}", "\n\n", c)
        
        # Add spacing before sections
        c = re.sub(r"([^\n])\n(\\section)", r"\1\n\n\\section", c)

        # Indent environments
        def indent_env(m):
            body = m.group(2)
            body_i = "\n".join(
                ("  " + l) if l.strip() else l for l in body.splitlines()
            )
            return f"\\begin{{{m.group(1)}}}\n{body_i}\n\\end{{{m.group(1)}}}"

        c = re.sub(
            r"\\begin{(itemize|enumerate)}(.*?)\\end{\1}",
            indent_env,
            c,
            flags=re.DOTALL,
        )
        
        return "✅ Formatting applied.\n" + c
