import os
import io
import csv
import uuid

import pymupdf
import pytesseract

from PIL import Image

from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import Annotated
from fastapi.responses import FileResponse
from fastapi.openapi.utils import get_openapi

from app.extract import extract_invoice_data
from app.normalizer import normalize_ocr_text


# ============================================================
# FastAPI Application
# ============================================================

app = FastAPI(
    title="Invoice OCR API",
    description="Extract invoice number, invoice date and GSTIN from PDF invoices",
    version="1.0"
)


def custom_openapi():

    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        openapi_version="3.0.3"
    )

    # --------------------------------------------------------
    # Fix multiple file upload schema for Swagger UI
    # --------------------------------------------------------

    try:

        schema = (
            openapi_schema["components"]["schemas"]
            ["Body_extract_invoice_extract_invoice_post"]
        )

        files_schema = schema["properties"]["files"]

        files_schema["items"] = {
            "type": "string",
            "format": "binary"
        }

    except KeyError:
        pass

    app.openapi_schema = openapi_schema

    return app.openapi_schema


app.openapi = custom_openapi


# ============================================================
# Health Check
# ============================================================

@app.get("/health")
async def health():
    return {
        "status": "UP",
        "service": "OCR API"
    }


# ============================================================
# Directories
# ============================================================

UPLOAD_DIR = "/home/ansible/ocr/uploads"
OUTPUT_DIR = "/home/ansible/ocr/output"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# PDF Text Extraction
# ============================================================

def extract_pdf_text(pdf_path):

    pdf = pymupdf.open(pdf_path)

    all_text = ""

    for page in pdf:

        # ----------------------------------------------------
        # First try extracting embedded PDF text
        # ----------------------------------------------------

        text = page.get_text()

        if text.strip():

            all_text += "\n" + text

        else:

            # ------------------------------------------------
            # If no text exists, use OCR
            # ------------------------------------------------

            pix = page.get_pixmap(dpi=300)

            image = Image.open(
                io.BytesIO(
                    pix.tobytes("png")
                )
            )

            ocr_text = pytesseract.image_to_string(
                image
            )

            all_text += "\n" + ocr_text

    pdf.close()

    return all_text


# ============================================================
# Root Endpoint
# ============================================================

@app.get("/")
def root():

    return {
        "message": "Invoice OCR API is running"
    }


# ============================================================
# Multiple Invoice Extraction Endpoint
# ============================================================

@app.post("/extract-invoice")
async def extract_invoice(
    files: Annotated[list[UploadFile], File(...)]
):

    # ========================================================
    # Validate files
    # ========================================================

    if not files:

        raise HTTPException(
            status_code=400,
            detail="Please upload at least one PDF file"
        )

    # ========================================================
    # Validate all uploaded files
    # ========================================================

    for file in files:

        if not file.filename:

            raise HTTPException(
                status_code=400,
                detail="Uploaded file has no filename"
            )

        if not file.filename.lower().endswith(".pdf"):

            raise HTTPException(
                status_code=400,
                detail=f"Only PDF files are supported: {file.filename}"
            )

    # ========================================================
    # Generate one CSV for this batch
    # ========================================================

    unique_id = uuid.uuid4().hex

    output_filename = (
        f"invoice_data_{unique_id}.csv"
    )

    csv_path = os.path.join(
        OUTPUT_DIR,
        output_filename
    )

    # ========================================================
    # Create CSV
    # ========================================================

    with open(
        csv_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)

        # ----------------------------------------------------
        # CSV Header
        # ----------------------------------------------------

        writer.writerow([
            "Invoice Number",
            "Invoice Date",
            "GSTIN 1",
            "GSTIN 2",
            "GSTIN 3",
            "GSTIN 4",
            "GSTIN 5"
        ])

        # ====================================================
        # Process every uploaded PDF
        # ====================================================

        results = []

        for file in files:

            # ------------------------------------------------
            # Generate unique input filename
            # ------------------------------------------------

            input_filename = (
                f"{uuid.uuid4().hex}_{file.filename}"
            )

            pdf_path = os.path.join(
                UPLOAD_DIR,
                input_filename
            )

            # ------------------------------------------------
            # Save uploaded PDF
            # ------------------------------------------------

            with open(
                pdf_path,
                "wb"
            ) as buffer:

                while True:

                    chunk = await file.read(
                        1024 * 1024
                    )

                    if not chunk:
                        break

                    buffer.write(chunk)

            # =================================================
            # Extract PDF text / OCR
            # =================================================

            try:

                all_text = extract_pdf_text(
                    pdf_path
                )

            except Exception as e:

                raise HTTPException(
                    status_code=500,
                    detail=(
                        f"PDF/OCR extraction failed "
                        f"for {file.filename}: {str(e)}"
                    )
                )

            # =================================================
            # Normalize OCR text
            # =================================================

            try:

                normalized_text = normalize_ocr_text(
                    all_text
                )

            except Exception as e:

                raise HTTPException(
                    status_code=500,
                    detail=(
                        f"OCR normalization failed "
                        f"for {file.filename}: {str(e)}"
                    )
                )

            # =================================================
            # Extract invoice fields
            # =================================================

            try:

                data = extract_invoice_data(
                    normalized_text
                )

            except Exception as e:

                raise HTTPException(
                    status_code=500,
                    detail=(
                        f"Invoice extraction failed "
                        f"for {file.filename}: {str(e)}"
                    )
                )

            # =================================================
            # Get GSTINs
            # =================================================

            gstins = data.get(
                "gstins",
                []
            )

            # =================================================
            # Create CSV row
            # =================================================

            row = [
                data.get(
                    "invoice_number"
                ),
                data.get(
                    "invoice_date"
                )
            ]

            # ------------------------------------------------
            # Store GSTINs in separate columns
            # ------------------------------------------------

            for i in range(5):

                if i < len(gstins):

                    row.append(
                        gstins[i]
                    )

                else:

                    row.append("")

            # ------------------------------------------------
            # Write invoice data to CSV
            # ------------------------------------------------

            writer.writerow(row)

            # =================================================
            # Store result for API response
            # =================================================

            results.append({

                "file": file.filename,

                "invoice_number": data.get(
                    "invoice_number"
                ),

                "invoice_date": data.get(
                    "invoice_date"
                ),

                "gstins": gstins
            })

            # ------------------------------------------------
            # Close uploaded file
            # ------------------------------------------------

            await file.close()

    # ========================================================
    # Return JSON response
    # ========================================================

    return {

        "message": (
            f"{len(files)} invoice(s) processed successfully"
        ),

        "total_files": len(files),

        "results": results,

        "csv_file": output_filename,

        "download_endpoint": (
            f"/download-invoice-data/{output_filename}"
        )
    }


# ============================================================
# Download Latest CSV
# ============================================================

@app.get("/download-invoice-data")
def download_invoice_data():

    # --------------------------------------------------------
    # Find CSV files in output directory
    # --------------------------------------------------------

    csv_files = []

    for filename in os.listdir(OUTPUT_DIR):

        if (
            filename.startswith("invoice_data_")
            and filename.endswith(".csv")
        ):

            csv_files.append(
                filename
            )

    # --------------------------------------------------------
    # No CSV found
    # --------------------------------------------------------

    if not csv_files:

        raise HTTPException(
            status_code=404,
            detail="No invoice CSV file found"
        )

    # --------------------------------------------------------
    # Find latest CSV
    # --------------------------------------------------------

    latest_file = max(
        csv_files,
        key=lambda filename: os.path.getmtime(
            os.path.join(
                OUTPUT_DIR,
                filename
            )
        )
    )

    csv_path = os.path.join(
        OUTPUT_DIR,
        latest_file
    )

    # --------------------------------------------------------
    # Return CSV file
    # --------------------------------------------------------

    return FileResponse(
        path=csv_path,
        filename="invoice_data.csv",
        media_type="text/csv"
    )
