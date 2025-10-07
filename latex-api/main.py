import logging
import os
import subprocess
import tempfile
import time
from uuid import uuid4

from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import JSONResponse, Response

app = FastAPI()


LOG_LEVEL = os.getenv("LATEX_API_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("latex_api")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/compile")
async def compile_latex(
    file: UploadFile = File(...),
    return_json: bool = Query(False, alias="json"),
):
    # Use a temp directory to isolate LaTeX build artifacts
    request_id = uuid4().hex
    start_time = time.perf_counter()

    logger.info(
        "[%s] Received compile request: filename=%s return_json=%s",
        request_id,
        file.filename,
        return_json,
    )

    with tempfile.TemporaryDirectory(prefix="latexbuild_") as tmpdir:
        tex_path = os.path.join(tmpdir, "input.tex")
        pdf_path = os.path.join(tmpdir, "input.pdf")

        content = await file.read()
        logger.info("[%s] Read %d bytes of LaTeX source", request_id, len(content))
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
        try:
            proc = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
        except Exception:
            logger.exception("[%s] Failed to invoke pdflatex", request_id)
            return JSONResponse(
                {
                    "success": False,
                    "error": "Internal compiler error",
                },
                status_code=500,
            )

        log = proc.stdout or ""
        success = proc.returncode == 0 and os.path.exists(pdf_path)
        duration = time.perf_counter() - start_time

        if success:
            pdf_size = os.path.getsize(pdf_path)
            logger.info(
                "[%s] Compilation succeeded in %.2fs (exit_code=%d, pdf_size=%d bytes)",
                request_id,
                duration,
                proc.returncode,
                pdf_size,
            )
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
        logger.error(
            "[%s] Compilation failed in %.2fs (exit_code=%d): %s",
            request_id,
            duration,
            proc.returncode,
            summary,
        )
        if lines:
            logger.debug(
                "[%s] Log tail:\n%s",
                request_id,
                "\n".join(lines[-80:]),
            )
        return JSONResponse(
            {
                "success": False,
                "error": summary,
                "logTail": "\n".join(lines[-80:]),
            },
            status_code=400,
        )
