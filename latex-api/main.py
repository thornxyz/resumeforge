from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import JSONResponse, Response
import subprocess, tempfile, os

app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/compile")
async def compile_latex(
    file: UploadFile = File(...),
    return_json: bool = Query(False, alias="json"),
):
    # Use a temp directory to isolate LaTeX build artifacts
    with tempfile.TemporaryDirectory(prefix="latexbuild_") as tmpdir:
        tex_path = os.path.join(tmpdir, "input.tex")
        pdf_path = os.path.join(tmpdir, "input.pdf")

        content = await file.read()
        with open(tex_path, "wb") as f:
            f.write(content)

        # Run pdflatex in nonstop mode and halt on error for reliable exit code
        cmd = [
            "pdflatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-file-line-error",
            f"-output-directory={tmpdir}",
            tex_path,
        ]
        proc = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        log = proc.stdout or ""
        success = proc.returncode == 0 and os.path.exists(pdf_path)

        if success:
            if return_json:
                return JSONResponse(
                    {
                        "success": True,
                        "message": "LaTeX compiled successfully.",
                        "logTail": "\n".join(log.splitlines()[-40:]),
                    }
                )
            # Default: return the compiled PDF bytes directly
            with open(pdf_path, "rb") as f:
                data = f.read()
            return Response(
                content=data,
                media_type="application/pdf",
                headers={"Content-Disposition": "inline; filename=compiled.pdf"},
            )

        # Extract a concise error summary from the log
        lines = log.splitlines()
        err_lines = [l for l in lines if l.startswith("!") or "LaTeX Error" in l]
        # Include context around first error if available
        summary = err_lines[0] if err_lines else "Compilation failed. Check log."
        return JSONResponse(
            {
                "success": False,
                "error": summary,
                "logTail": "\n".join(lines[-80:]),
            },
            status_code=400,
        )
