from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import subprocess, uuid, os

app = FastAPI()

@app.post("/compile")
async def compile_latex(file: UploadFile = File(...)):
    uid = str(uuid.uuid4())
    tex_file = f"{uid}.tex"
    pdf_file = f"{uid}.pdf"

    with open(tex_file, "wb") as f:
        f.write(await file.read())

    subprocess.run(["pdflatex", tex_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    return FileResponse(pdf_file, media_type="application/pdf", filename="compiled.pdf")
