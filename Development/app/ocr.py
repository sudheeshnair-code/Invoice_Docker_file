import fitz
import pytesseract
from PIL import Image
import io
import json
import csv
import os

from app.normalizer import normalize_ocr_text
from app.extract import extract_invoice_data

OUTPUT_DIR = "output"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def process_invoice(pdf_file):

    # ============================================================
    # Open PDF
    # ============================================================

    pdf = fitz.open(pdf_file)

    all_text = ""

    # ============================================================
    # Extract text / OCR
    # ============================================================

    for page in pdf:

        text = page.get_text()

        if text.strip():
            all_text += text

        else:

            pix = page.get_pixmap(dpi=300)

            image = Image.open(
                io.BytesIO(
                    pix.tobytes("png")
                )
            )

            ocr_text = pytesseract.image_to_string(image)

            all_text += ocr_text

    # ============================================================
    # Save raw OCR/text
    # ============================================================

    raw_file = os.path.join(
        OUTPUT_DIR,
        "raw_invoice_text.txt"
    )

    with open(raw_file, "w", encoding="utf-8") as f:
        f.write(all_text)

    # ============================================================
    # Normalize text
    # ============================================================

    normalized_text = normalize_ocr_text(all_text)

    # ============================================================
    # Save normalized text
    # ============================================================

    normalized_file = os.path.join(
        OUTPUT_DIR,
        "normalized_invoice.txt"
    )

    with open(normalized_file, "w", encoding="utf-8") as f:
        f.write(normalized_text)

    # ============================================================
    # Extract invoice data
    # ============================================================

    data = extract_invoice_data(normalized_text)

    csv_file = os.path.join(
        OUTPUT_DIR,
        "invoice_data.csv"
    )

    file_exists = os.path.isfile(csv_file)

    with open(csv_file, "a", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "Invoice Number",
                "Invoice Date",
                "GSTIN 1",
                "GSTIN 2",
                "GSTIN 3",
                "GSTIN 4",
                "GSTIN 5"
            ])

        gstins = data.get("gstins", [])

        row = [
            data.get("invoice_number"),
            data.get("invoice_date")
        ]

        for i in range(5):
            if i < len(gstins):
                row.append(gstins[i])
            else:
                row.append("")

        writer.writerow(row)

    print(json.dumps(data, indent=4))

    print(f"\nData saved to {csv_file}")

    return data
