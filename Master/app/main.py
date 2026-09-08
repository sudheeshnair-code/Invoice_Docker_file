from fastapi import FastAPI, UploadFile, File
import shutil
import os

from app.ocr import process_invoice

app = FastAPI()

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/upload")
async def upload(file: UploadFile = File(...)):

    pdf_file = os.path.join(
        UPLOAD_DIR,
        file.filename
    )

    with open(pdf_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    data = process_invoice(pdf_file)

    return data
