import re
from datetime import datetime


# ============================================================
# GSTIN
# ============================================================

def extract_gstins(text):

    pattern = (
        r"\b"
        r"[0-9]{2}"
        r"[A-Z]{5}"
        r"[0-9]{4}"
        r"[A-Z]"
        r"[0-9A-Z]"
        r"Z"
        r"[0-9A-Z]"
        r"\b"
    )

    gstins = re.findall(
        pattern,
        text.upper()
    )

    return list(dict.fromkeys(gstins))


# ============================================================
# Invoice Number
# ============================================================

def extract_invoice_number(text):

    patterns = [

        # Normalized field
        r"INVOICE_NUMBER\s*:\s*([A-Z0-9./_-]+)",

        # Invoice No: INV-3337
        r"Invoice\s*(?:No|Number)\s*[:#.\-]?\s*([A-Z0-9./_-]+)",

        # Invoice No.
        # INV-3337
        r"Invoice\s*(?:No|Number)\.?\s*\n+\s*([A-Z0-9./_-]+)",

        # Invoice No. Dated
        # 2026-27/198 14-Jul-26
        r"Invoice\s*(?:No|Number)\.?\s+Dated\s*\n+\s*([A-Z0-9./_-]+)",

        r"Inv\.?\s*(?:No|Number)\s*[:#.\-]?\s*([A-Z0-9./_-]+)",

        r"Bill\s*(?:No|Number)\s*[:#.\-]?\s*([A-Z0-9./_-]+)",

        r"Tax\s+Invoice\s*(?:No|Number)\s*[:#.\-]?\s*([A-Z0-9./_-]+)"
    ]

    invalid_words = {
        "invoice",
        "number",
        "no",
        "date",
        "dated",
        "gst",
        "gstin",
        "bill"
    }

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if not match:
            continue

        value = match.group(1).strip(" .:-#")

        if value.lower() in invalid_words:
            continue

        # Invoice number should contain at least one digit
        if not re.search(r"\d", value):
            continue

        return value

    return None


# ============================================================
# Date conversion
# ============================================================

def normalize_date(date_string):

    date_string = date_string.strip()

    formats = [

        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",

        "%d/%m/%y",
        "%d-%m-%y",

        "%d-%b-%y",
        "%d-%b-%Y",

        "%m/%d/%Y",
        "%m-%d-%Y",

        "%Y-%m-%d",
        "%Y/%m/%d",

        "%B %d, %Y",
        "%b %d, %Y",

        "%d %B %Y",
        "%d %b %Y"
    ]

    for fmt in formats:

        try:

            date = datetime.strptime(
                date_string,
                fmt
            )

            return date.strftime("%Y-%m-%d")

        except ValueError:
            continue

    return date_string


# ============================================================
# Invoice Date
# ============================================================

def extract_invoice_date(text):

    date_pattern = (
        r"("
        r"[0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4}"
        r"|"
        r"[0-9]{1,2}-[A-Za-z]{3}-[0-9]{2,4}"
        r"|"
        r"[A-Za-z]+\s+[0-9]{1,2},\s*[0-9]{4}"
        r"|"
        r"[0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4}"
        r")"
    )

    patterns = [

        rf"INVOICE_DATE\s*:\s*{date_pattern}",

        rf"Invoice\s*Date\s*[:#.\-]?\s*{date_pattern}",

        rf"Date\s+of\s+Invoice\s*[:#.\-]?\s*{date_pattern}",

        rf"Bill\s*Date\s*[:#.\-]?\s*{date_pattern}",

        rf"Invoice\s*Dt\.?\s*[:#.\-]?\s*{date_pattern}",

        rf"Dated\s*[:#.\-]?\s*{date_pattern}",

        rf"Date\s*[:#.\-]?\s*{date_pattern}",

        # Invoice No. Dated
        # 2026-27/198 14-Jul-26
        rf"Dated\s*\n+\s*[A-Z0-9./_-]+\s+{date_pattern}",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            return normalize_date(
                match.group(1)
            )

    return None


# ============================================================
# Extract everything
# ============================================================

def extract_invoice_data(text):

    invoice_number = extract_invoice_number(text)

    invoice_date = extract_invoice_date(text)

    gstins = extract_gstins(text)

    return {

        "invoice_number": invoice_number,

        "invoice_date": invoice_date,

        "gstins": gstins
    }
