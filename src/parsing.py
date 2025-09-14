from io import BytesIO
from typing import Optional
from pdfminer.high_level import extract_text as pdf_extract_text
import docx2txt

def _read_pdf_bytes(b: bytes) -> str:
    try:
        with BytesIO(b) as buff:
            return pdf_extract_text(buff) or ""
    except Exception:
        return ""

def _read_docx_bytes(b: bytes) -> str:
    try:
        with BytesIO(b) as buff:
            return docx2txt.process(buff) or ""
    except Exception:
        return ""

def extract_text_from_upload(uploaded_file) -> str:
    """
    Accepts Streamlit UploadedFile (pdf/docx/txt).
    Tries robust extraction and returns plain text.
    """
    filename = (uploaded_file.name or "").lower()
    data = uploaded_file.read()
    if filename.endswith(".pdf"):
        return _read_pdf_bytes(data)
    elif filename.endswith(".docx"):
        return _read_docx_bytes(data)
    elif filename.endswith(".txt") or filename.endswith(".md"):
        try:
            return data.decode("utf-8", errors="ignore")
        except Exception:
            return data.decode("latin-1", errors="ignore")
    else:
        # last resort: try utf-8 decode
        try:
            return data.decode("utf-8", errors="ignore")
        except Exception:
            return ""
