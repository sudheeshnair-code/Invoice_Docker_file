import re


def normalize_ocr_text(text):

    # =========================================================
    # Basic cleanup
    # =========================================================

    text = text.replace("\xa0", " ")

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )


    # =========================================================
    # Invoice Number
    # =========================================================

    text = re.sub(
        r"\bInvoice\s*(?:No|Number)\s*[:#.\-]+\s*",
        "INVOICE_NUMBER:",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\bInvoice\s*#\s*[:#.\-]*\s*",
        "INVOICE_NUMBER:",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\bInv\.?\s*(?:No|Number)\s*[:#.\-]*\s*",
        "INVOICE_NUMBER:",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\bBill\s*(?:No|Number)\s*[:#.\-]*\s*",
        "INVOICE_NUMBER:",
        text,
        flags=re.IGNORECASE
    )


    # =========================================================
    # Invoice Date
    # =========================================================

    text = re.sub(
        r"\bInvoice\s*Date\s*[:#.\-]+\s*",
        "INVOICE_DATE:",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\bDate\s+of\s+Invoice\s*[:#.\-]+\s*",
        "INVOICE_DATE:",
        text,
        flags=re.IGNORECASE
    )

    # IMPORTANT:
    # Only normalize "Date:" when it starts a line.
    #
    # This prevents text such as:
    # "Payment is due within 30 days from date"
    # from being treated as invoice date.

    text = re.sub(
        r"(?mi)^\s*Date\s*[:#.\-]+\s*",
        "INVOICE_DATE:",
        text
    )


    # =========================================================
    # GSTIN
    # =========================================================

    text = re.sub(
        r"\bGSTIN\s*(?:No|Number)?\s*[:.\-]+\s*",
        "GSTIN:",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\bGST\s*(?:No|Number)\s*[:.\-]+\s*",
        "GSTIN:",
        text,
        flags=re.IGNORECASE
    )


    # =========================================================
    # Clean duplicate separators
    # =========================================================

    text = re.sub(
        r"INVOICE_NUMBER:\s*[:]+\s*",
        "INVOICE_NUMBER:",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"INVOICE_DATE:\s*[:]+\s*",
        "INVOICE_DATE:",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"GSTIN:\s*[:]+\s*",
        "GSTIN:",
        text,
        flags=re.IGNORECASE
    )


    return text.strip()
