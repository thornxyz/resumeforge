"""LaTeX tools"""

import re
import requests
from typing import List


class BaseTool:
    name = "base_tool"
    description = "Base tool"

    def _run(self, *args, **kwargs):
        raise NotImplementedError

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)


class LatexCompilerTool(BaseTool):
    name = "latex_compiler"
    description = "Compile LaTeX to PDF via local service"

    def _run(self, latex_content: str) -> str:
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

    async def _arun(self, latex_content: str) -> str:
        return self._run(latex_content)


class LatexValidatorTool(BaseTool):
    name = "latex_validator"
    description = "Validate LaTeX and report issues + JSON tail"

    def _run(self, latex_content: str) -> str:
        errors: List[str] = []
        warnings: List[str] = []
        fixes: List[str] = []
        if not re.search(r"\\\\\s*documentclass", latex_content):
            errors.append("Missing \\documentclass")
            fixes.append("Add minimal preamble")
        if not re.search(r"\\begin{document}", latex_content):
            errors.append("Missing \\begin{document}")
            fixes.append("Add \\begin{document}")
        if not re.search(r"\\end{document}", latex_content):
            errors.append("Missing \\end{document}")
            fixes.append("Add \\end{document}")
        if latex_content.count("{") != latex_content.count("}"):
            errors.append("Unbalanced braces")
            fixes.append("Balance braces")
        for env in re.findall(r"\\begin{(\w+)}", latex_content):
            if not re.search(rf"\\end{{{env}}}", latex_content):
                errors.append(f"Unclosed environment: {env}")
                fixes.append(f"Add \\end{{{env}}}")
        if re.search(r"\\(?:textcolor|color)\\b", latex_content) and not re.search(
            r"\\usepackage{.*?xcolor.*?}", latex_content
        ):
            warnings.append("Color commands without xcolor")
            fixes.append("Add \\usepackage{xcolor}")
        if re.search(r"\\(?:href|url)\\b", latex_content) and not re.search(
            r"\\usepackage{.*?hyperref.*?}", latex_content
        ):
            warnings.append("Hyperlink commands without hyperref")
            fixes.append("Add \\usepackage{hyperref}")
        if not any(
            s
            in [
                s2.lower() for s2 in re.findall(r"\\section\*?{([^}]+)}", latex_content)
            ]
            for s in ["experience", "education", "skills"]
        ):
            warnings.append("No standard resume sections")
            fixes.append("Add Experience/Education/Skills")
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

    async def _arun(self, latex_content: str) -> str:
        return self._run(latex_content)


class LatexSectionExtractorTool(BaseTool):
    name = "latex_section_extractor"
    description = "Extract a named section"

    def _run(self, latex_content: str, section_name: str = "") -> str:
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

    async def _arun(self, latex_content: str, section_name: str = "") -> str:
        return self._run(latex_content, section_name)


class LatexTemplateGeneratorTool(BaseTool):
    name = "latex_template_generator"
    description = "Generate resume template"

    def _run(
        self,
        style: str = "modern",
        name: str = "[Your Name]",
        email: str = "[your.email@example.com]",
    ) -> str:
        style = style.lower().strip()
        t = {
            "modern": self._modern_template,
            "classic": self._classic_template,
            "creative": self._creative_template,
            "academic": self._academic_template,
        }
        return (t.get(style) or self._modern_template)(name, email)

    def _common_preamble(self) -> str:
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

    def _modern_template(self, name: str, email: str) -> str:
        return f"""{self._common_preamble()}\\begin{{document}}\n\\begin{{center}}\n{{\\LARGE {name}}}\\\\\n{{\\normalsize {email} • LinkedIn • GitHub}}\\\\\n\\end{{center}}\n\\section{{Summary}}\nResults-oriented engineer focused on scalable web applications.\n\\section{{Experience}}\\textbf{{Software Engineer}}, Tech Company (2024--Present)\\\\\n\\begin{{itemize}}\n  \\item Built full-stack features (TypeScript/Python).\n  \\item Reduced API latency 30\\%.\n  \\item Shipped UX improvements cross-team.\n\\end{{itemize}}\n\\section{{Education}}B.S. Computer Science, University (2020--2024) -- GPA 3.8/4.0\n\\section{{Skills}}Languages: Python, JS, TS, SQL\\\\Frameworks: React, Next.js, FastAPI\\\\Tools: Git, Docker, PostgreSQL, AWS\n\\end{{document}}"""

    def _classic_template(self, name: str, email: str) -> str:
        return f"""{self._common_preamble()}\\begin{{document}}\n\\begin{{center}}\n{{\\Large {name}}}\\\\\n{{{email} • Location • +1 (555) 123-4567}}\\\\\n\\end{{center}}\n\\section{{Objective}}Seeking a software engineering role contributing reliable systems.\n\\section{{Experience}}\\textbf{{Junior Developer}}, Company A (2023--2024)\\\\\n\\begin{{itemize}}\n  \\item Built internal productivity tools.\n  \\item Raised test coverage to 85\\%.\n\\end{{itemize}}\n\\section{{Education}}University — B.S. CS (2020--2024)\\\\Coursework: Data Structures, Algorithms, DBs\n\\section{{Skills}}Programming: Python, JS, SQL\\\\Other: Git, Docker, Linux\n\\end{{document}}"""

    def _creative_template(self, name: str, email: str) -> str:
        return f"""{self._common_preamble()}\\definecolor{{accent}}{{HTML}}{{005F99}}\n\\begin{{document}}\n\\begin{{center}}\n{{\\fontsize{{24}}{{26}}\\selectfont\\textcolor{{accent}}{{{name}}}}}\\\\\n{{\\small {email} • Portfolio • @handle}}\\\\\n\\end{{center}}\n\\section{{Profile}}Creative full-stack engineer blending design + engineering.\n\\section{{Projects}}\\textbf{{Project Alpha}} Dashboard analytics\\\\\\n\\begin{{itemize}}\n  \\item Modular React component system.\n  \\item Real-time websocket updates.\n\\end{{itemize}}\\textbf{{Project Beta}} Automation scripts reduced ops 40\\%.\n\\section{{Skills}}Frontend: React, Next.js, Tailwind\\\\Backend: FastAPI, Node.js, PostgreSQL\\\\Other: Docker, CI/CD, Testing\n\\section{{Experience}}Freelance Developer (2022--Present)\\\\\\n\\begin{{itemize}}\n  \\item Delivered accessible performant web apps.\n\\end{{itemize}}\n\\end{{document}}"""

    def _academic_template(self, name: str, email: str) -> str:
        return f"""{self._common_preamble()}\\begin{{document}}\n\\begin{{center}}\n{{\\Large {name}}}\\\\\n{{{email} • Google Scholar}}\\\\\n\\end{{center}}\n\\section{{Research Interests}}Distributed systems, applied ML, performance.\n\\section{{Publications}}\\begin{{itemize}}\n  \\item Author et al. "Paper Title", Conf 2024.\n  \\item Author et al. "Another Publication", Journal 2023.\n\\end{{itemize}}\n\\section{{Education}}B.S. CS, University, 2024\n\\section{{Experience}}Research Assistant (2023--2024)\\\\\\n\\begin{{itemize}}\n  \\item Built evaluation framework for schedulers.\n\\end{{itemize}}\n\\section{{Skills}}Languages: Python, C++, Go\\\\Tools: Git, Docker, Linux, LaTeX\n\\end{{document}}"""

    async def _arun(
        self,
        style: str = "modern",
        name: str = "[Your Name]",
        email: str = "[your.email@example.com]",
    ) -> str:
        return self._run(style, name, email)


class LatexEnhancerTool(BaseTool):
    name = "latex_enhancer"
    description = "Enhance LaTeX content"

    def _run(self, latex_content: str, enhancement_type: str = "all") -> str:
        if not latex_content.strip():
            return "No LaTeX content supplied."
        suggestions: List[str] = []
        lines = latex_content.splitlines()
        out: List[str] = []
        inside = False
        for line in lines:
            s = line.strip()
            if re.match(r"^- ", s) and not inside:
                out.append("\\begin{itemize}")
                inside = True
            if inside and s == "":
                out.append("\\end{itemize}")
                inside = False
            if inside and re.match(r"^- ", s):
                bullet = re.sub(r"^(- )", "", s)
                bullet = re.sub(r"^(\w)", lambda m: m.group(1).upper(), bullet)
                suggestions.append(f"Converted list item: {bullet[:40]}")
                out.append(f"  \\item {bullet}")
            else:
                out.append(line)
        if inside:
            out.append("\\end{itemize}")
        improved = "\n".join(out)
        if re.search(r"\\item", improved) and "%" not in improved:
            suggestions.append("Add quantifiable impact numbers to bullets.")
        report = ["Enhancements:"] + [
            "  - " + s for s in suggestions or ["Already structured."]
        ]
        report.append("\nImproved LaTeX:\n" + improved)
        return "\n".join(report)

    async def _arun(self, latex_content: str, enhancement_type: str = "all") -> str:
        return self._run(latex_content, enhancement_type)


class LatexFormatterTool(BaseTool):
    name = "latex_formatter"
    description = "Format / normalize LaTeX"

    def _run(self, latex_content: str) -> str:
        if not latex_content.strip():
            return "No LaTeX content to format."
        c = latex_content.replace("\r\n", "\n").replace("\r", "\n")
        c = "\n".join(l.rstrip() for l in c.splitlines())
        c = re.sub(r"\n{3,}", "\n\n", c)
        c = re.sub(r"([^\n])\n(\\section)", r"\1\n\n\\section", c)

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

    async def _arun(self, latex_content: str) -> str:
        return self._run(latex_content)
